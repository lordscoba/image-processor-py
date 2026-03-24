import base64
import io
import asyncio
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from app.core.config import ALLOWED_OUTPUT_FORMATS, MAX_BASE64_SIZE
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety
from app.utils.profiler import profile_performance
import urllib.parse


# ───────────────────────────────────────────────────────────
# Global Safety Limits
# ───────────────────────────────────────────────────────────

Image.MAX_IMAGE_PIXELS = 50_000_000  # 50MP hard cap
MAX_PIXELS = 20_000_000              # Soft cap (20MP)
MAX_CONCURRENT_JOBS = 10             # Prevent overload
PROCESS_TIMEOUT = 20                 # seconds

semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)



# --------------------------------------------------
# Image → Base64 (Thread-safe + Memory-aware)
# --------------------------------------------------

@profile_performance
async def image_to_base64_service(file):

    try:

        def process():
            with Image.open(file) as image:

                image = ImageOps.exif_transpose(image)
                validate_image_safety(image)

                output_format = image.format.lower() if image.format else "png"

                if output_format not in ALLOWED_OUTPUT_FORMATS:
                    output_format = "png"

                with io.BytesIO() as buffer:

                    if output_format == "jpeg":
                        image = image.convert("RGB")

                    image.save(
                        buffer,
                        format=ALLOWED_OUTPUT_FORMATS[output_format],
                        optimize=True,
                        quality=90
                    )

                    encoded = base64.b64encode(
                        buffer.getbuffer()
                    ).decode("utf-8")

                return {
                    "success": True,
                    "format": output_format,
                    "base64": encoded
                }

        return await run_in_threadpool(process)

    except DecompressionBombError:
        raise HTTPException(
            status_code=400,
            detail="Image resolution too large (possible decompression bomb)."
        )
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    except Exception as e:
        logger.error(f"Image to Base64 error: {str(e)}")
        raise HTTPException(status_code=500, detail="Conversion failed.")


def clean_base64_input(base64_string: str) -> str:
    if not base64_string or len(base64_string) < 10:
        return base64_string

    # 1. URL decode FIRST
    if "%" in base64_string:
        base64_string = urllib.parse.unquote(base64_string)

    # 2. Trim outer whitespace
    base64_string = base64_string.strip()

    # 3. Remove ALL layers of surrounding quotes
    while (
        len(base64_string) > 1 and
        (
            (base64_string.startswith('"') and base64_string.endswith('"')) or
            (base64_string.startswith("'") and base64_string.endswith("'"))
        )
    ):
        base64_string = base64_string[1:-1].strip()

    # 4. Remove internal whitespace efficiently
    if " " in base64_string:
        base64_string = base64_string.replace(" ", "")
    if "\n" in base64_string or "\r" in base64_string:
        base64_string = base64_string.replace("\n", "").replace("\r", "")

    # 5. Fix missing padding
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += "=" * (4 - missing_padding)

    return base64_string

@profile_performance
async def base64_to_image_service(base64_string: str):

    start_len = len(base64_string or "")

    try:
        # ─── 0. CLEAN INPUT FIRST (CRITICAL) ────────────────
        base64_string = clean_base64_input(base64_string)

        start_len = len(base64_string or "")
        # ─── 1. Early validation ───────────────────────────
        if not base64_string or start_len < 100:
            raise HTTPException(400, "Invalid base64 input.")

        # ─── 2. Safe Data URI stripping ────────────────────
        if base64_string.startswith("data:image"):
            if "," not in base64_string:
                raise HTTPException(400, "Malformed data URI.")
            base64_string = base64_string.split(",", 1)[1]

        # ─── 3. Payload size check (before decode) ─────────
        if len(base64_string) > MAX_BASE64_SIZE * 1.4:
            raise HTTPException(400, "Base64 payload too large.")

        # ─── 4. Processing logic (CPU heavy → threadpool) ──
        async def process():

            def inner():
                # ─── Decode inside threadpool (CPU safe) ───
                try:
                    decoded_bytes = base64.b64decode(base64_string, validate=True)
                except Exception:
                    raise HTTPException(400, "Invalid Base64 string.")

                if len(decoded_bytes) > MAX_BASE64_SIZE:
                    raise HTTPException(400, "Decoded image exceeds allowed size.")

                # ─── Open image safely ─────────────────────
                try:
                    image = Image.open(io.BytesIO(decoded_bytes))
                    image.verify()  # detect corrupt headers early
                except Exception:
                    raise HTTPException(400, "Corrupted or invalid image data.")

                # Re-open after verify (Pillow requirement)
                image = Image.open(io.BytesIO(decoded_bytes))

                # Fix EXIF rotation
                image = ImageOps.exif_transpose(image)

                # ─── Dimension safety check ────────────────
                width, height = image.size
                if width * height > MAX_PIXELS:
                    raise HTTPException(
                        400, "Image resolution too large."
                    )

                validate_image_safety(image)

                # ─── Format detection ─────────────────────
                output_format = image.format.lower() if image.format else "png"

                if output_format not in ALLOWED_OUTPUT_FORMATS:
                    output_format = "png"

                # ─── Optional resize (cost saver) ─────────
                MAX_WIDTH = 1920
                if image.width > MAX_WIDTH:
                    image.thumbnail((MAX_WIDTH, MAX_WIDTH))

                # ─── Output buffer (NO duplicate memory) ──
                buffer = io.BytesIO()

                if output_format == "jpeg":
                    image = image.convert("RGB")

                # Lower CPU cost
                save_kwargs = {
                    "format": ALLOWED_OUTPUT_FORMATS[output_format],
                    "optimize": True,
                    "quality": 85,
                }

                # Special handling for WebP
                if output_format == "webp":
                    save_kwargs["quality"] = 80

                image.save(buffer, **save_kwargs)

                buffer.seek(0)

                return buffer, output_format

            return await run_in_threadpool(inner)

        # ─── 5. Concurrency + timeout protection ───────────
        async with semaphore:
            buffer, output_format = await asyncio.wait_for(
                process(),
                timeout=PROCESS_TIMEOUT
            )

        # ─── 6. Streaming response (NO duplication) ────────
        return StreamingResponse(
            buffer,
            media_type=f"image/{output_format}",
            headers={
                "Content-Disposition":
                    f"attachment; filename=converted.{output_format}",
                "Cache-Control": "public, max-age=31536000",
            },
        )

    except asyncio.TimeoutError:
        raise HTTPException(408, "Processing timeout.")

    except DecompressionBombError:
        raise HTTPException(
            400,
            "Image resolution too large (possible decompression bomb)."
        )

    except UnidentifiedImageError:
        raise HTTPException(
            400,
            "Decoded data is not a valid image."
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Base64 to Image error: {str(e)}")
        raise HTTPException(500, "Conversion failed.")

# # --------------------------------------------------
# # Base64 → Image (Memory-Safe + No Heavy Regex)
# # --------------------------------------------------

# async def base64_to_image_service(base64_string: str):

#     try:

#         # Remove data URI safely (no heavy regex)
#         if base64_string.startswith("data:image"):
#             base64_string = base64_string.split(",", 1)[1]

#         # Prevent oversized base64 payload
#         if len(base64_string) > MAX_BASE64_SIZE * 1.4:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Base64 payload too large."
#             )

#         # Decode safely
#         try:
#             decoded_bytes = base64.b64decode(base64_string, validate=True)
#         except Exception:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid Base64 string."
#             )

#         if len(decoded_bytes) > MAX_BASE64_SIZE:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Decoded image exceeds allowed size."
#             )

#         async def process():

#             def inner():
#                 with Image.open(io.BytesIO(decoded_bytes)) as image:

#                     image = ImageOps.exif_transpose(image)
#                     validate_image_safety(image)

#                     # Standardize output format
#                     output_format = image.format.lower() if image.format else "png"

#                     if output_format not in ALLOWED_OUTPUT_FORMATS:
#                         output_format = "png"

#                     with io.BytesIO() as buffer:

#                         if output_format == "jpeg":
#                             image = image.convert("RGB")

#                         image.save(
#                             buffer,
#                             format=ALLOWED_OUTPUT_FORMATS[output_format],
#                             optimize=True,
#                             quality=90
#                         )

#                         buffer.seek(0)

#                         return StreamingResponse(
#                             io.BytesIO(buffer.getvalue()),
#                             media_type=f"image/{output_format}",
#                             headers={
#                                 "Content-Disposition":
#                                 f"attachment; filename=converted.{output_format}"
#                             }
#                         )

#             return await run_in_threadpool(inner)

#         return await process()

#     except DecompressionBombError:
#         raise HTTPException(
#             status_code=400,
#             detail="Image resolution too large (possible decompression bomb)."
#         )
#     except UnidentifiedImageError:
#         raise HTTPException(
#             status_code=400,
#             detail="Decoded data is not a valid image."
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Base64 to Image error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Conversion failed.")