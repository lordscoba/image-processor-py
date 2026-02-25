import base64
import io
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from app.core.config import ALLOWED_OUTPUT_FORMATS, MAX_BASE64_SIZE
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety


# Prevent decompression bombs
Image.MAX_IMAGE_PIXELS = 50_000_000  # 50MP limit




# --------------------------------------------------
# Image → Base64 (Thread-safe + Memory-aware)
# --------------------------------------------------

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


# --------------------------------------------------
# Base64 → Image (Memory-Safe + No Heavy Regex)
# --------------------------------------------------

async def base64_to_image_service(base64_string: str):

    try:

        # Remove data URI safely (no heavy regex)
        if base64_string.startswith("data:image"):
            base64_string = base64_string.split(",", 1)[1]

        # Prevent oversized base64 payload
        if len(base64_string) > MAX_BASE64_SIZE * 1.4:
            raise HTTPException(
                status_code=400,
                detail="Base64 payload too large."
            )

        # Decode safely
        try:
            decoded_bytes = base64.b64decode(base64_string, validate=True)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid Base64 string."
            )

        if len(decoded_bytes) > MAX_BASE64_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Decoded image exceeds allowed size."
            )

        async def process():

            def inner():
                with Image.open(io.BytesIO(decoded_bytes)) as image:

                    image = ImageOps.exif_transpose(image)
                    validate_image_safety(image)

                    # Standardize output format
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

                        buffer.seek(0)

                        return StreamingResponse(
                            io.BytesIO(buffer.getvalue()),
                            media_type=f"image/{output_format}",
                            headers={
                                "Content-Disposition":
                                f"attachment; filename=converted.{output_format}"
                            }
                        )

            return await run_in_threadpool(inner)

        return await process()

    except DecompressionBombError:
        raise HTTPException(
            status_code=400,
            detail="Image resolution too large (possible decompression bomb)."
        )
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Decoded data is not a valid image."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Base64 to Image error: {str(e)}")
        raise HTTPException(status_code=500, detail="Conversion failed.")