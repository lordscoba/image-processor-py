import io
import time
from PIL import Image
from pillow_heif import register_heif_opener
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger

register_heif_opener()


def _sync_change_dpi(image_bytes: bytes, dpi: int, filename: str):

    start_time = time.perf_counter()

    try:
        img = Image.open(io.BytesIO(image_bytes))

        format = img.format if img.format else "JPEG"

        output_buffer = io.BytesIO()

        if format.upper() in ["JPEG", "JPG"]:

            img = img.convert("RGB")

            img.save(
                output_buffer,
                format="JPEG",
                dpi=(dpi, dpi),
                quality=95,
                optimize=True,
                progressive=True
            )

            ext = "jpg"
            media_type = "image/jpeg"

        elif format.upper() == "PNG":

            img.save(
                output_buffer,
                format="PNG",
                dpi=(dpi, dpi),
                optimize=True
            )

            ext = "png"
            media_type = "image/png"

        elif format.upper() == "WEBP":

            img.save(
                output_buffer,
                format="WEBP",
                quality=95,
                method=6
            )

            ext = "webp"
            media_type = "image/webp"

        elif format.upper() in ["HEIC", "HEIF"]:

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
        logger.error(f"DPI sync processing error: {str(e)}")
        raise e


async def image_dpi_service(file, dpi: int):

    try:

        await file.seek(0)
        image_bytes = await file.read()

        output_buffer, ext, media_type, processing_time_ms = await run_in_threadpool(
            _sync_change_dpi,
            image_bytes,
            dpi,
            file.filename
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}_{dpi}dpi.{ext}"
                }
            ),
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"DPI wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error changing image DPI.")
    


def _sync_check_dpi(image_bytes: bytes):

    start_time = time.perf_counter()

    try:
        img = Image.open(io.BytesIO(image_bytes))

        dpi = img.info.get("dpi")

        if dpi:
            dpi_x, dpi_y = dpi
        else:
            dpi_x, dpi_y = None, None

        width, height = img.size
        format = img.format

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "dpi_x": dpi_x,
            "dpi_y": dpi_y,
            "width": width,
            "height": height,
            "format": format,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"DPI check sync error: {str(e)}")
        raise e


async def image_dpi_checker_service(file):

    try:
        await file.seek(0)
        image_bytes = await file.read()

        result = await run_in_threadpool(
            _sync_check_dpi,
            image_bytes
        )

        return result

    except Exception as e:
        logger.error(f"DPI checker wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking image DPI.")