import io
import time
from PIL import Image
from pillow_heif import register_heif_opener
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger

register_heif_opener()


def _strip_exif(img: Image.Image) -> Image.Image:
    """Remove EXIF metadata safely."""
    data = list(img.getdata())
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(data)
    return clean_img


def _sync_exif_scrub(image_bytes: bytes, filename: str):
    start_time = time.perf_counter()

    try:
        img = Image.open(io.BytesIO(image_bytes))

        original_format = img.format if img.format else "JPEG"

        # Remove EXIF
        img = _strip_exif(img)

        output_buffer = io.BytesIO()

        if original_format.upper() in ["JPEG", "JPG"]:
            img = img.convert("RGB")

            img.save(
                output_buffer,
                format="JPEG",
                quality=95,
                optimize=True,
                progressive=True
            )

            ext = "jpg"
            media_type = "image/jpeg"

        elif original_format.upper() == "PNG":

            img.save(
                output_buffer,
                format="PNG",
                optimize=True
            )

            ext = "png"
            media_type = "image/png"

        elif original_format.upper() == "WEBP":

            img.save(
                output_buffer,
                format="WEBP",
                quality=95,
                method=6
            )

            ext = "webp"
            media_type = "image/webp"

        elif original_format.upper() in ["HEIF", "HEIC"]:

            img.save(
                output_buffer,
                format="HEIF",
                quality=90
            )

            ext = "heic"
            media_type = "image/heic"

        else:
            raise ValueError("Unsupported image format")

        output_buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, ext, media_type, processing_time_ms

    except Exception as e:
        logger.error(f"Sync EXIF scrub error: {str(e)}")
        raise e


async def exif_scrubber_service(file):

    try:
        await file.seek(0)
        image_bytes = await file.read()

        output_buffer, ext, media_type, processing_time_ms = await run_in_threadpool(
            _sync_exif_scrub,
            image_bytes,
            file.filename
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}_clean.{ext}"
                }
            ),
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"EXIF scrub wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error removing EXIF metadata.")