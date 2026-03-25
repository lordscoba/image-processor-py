import io
import math
import time
from PIL import Image
from pillow_heif import register_heif_opener
import pillow_avif  # registers AVIF

from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger

register_heif_opener()

# 🔒 Protect against image bombs
Image.MAX_IMAGE_PIXELS = 50_000_000


# ─────────────────────────────────────────────
# FORMAT HANDLER MAP (CLEAN + FAST)
# ─────────────────────────────────────────────
FORMAT_MAP = {
    "JPEG": ("JPEG", "jpg", "image/jpeg"),
    "PNG": ("PNG", "png", "image/png"),
    "WEBP": ("WEBP", "webp", "image/webp"),
    "HEIC": ("HEIF", "heic", "image/heic"),
    "HEIF": ("HEIF", "heic", "image/heic"),
    "TIFF": ("TIFF", "tiff", "image/tiff"),
    "TIF": ("TIFF", "tiff", "image/tiff"),
    "BMP": ("BMP", "bmp", "image/bmp"),
    "GIF": ("GIF", "gif", "image/gif"),
    "ICO": ("ICO", "ico", "image/x-icon"),
    "AVIF": ("AVIF", "avif", "image/avif"),
}


# ─────────────────────────────────────────────
# DPI CHANGE (SYNC CORE)
# ─────────────────────────────────────────────
def _sync_change_dpi(image_bytes: bytes, dpi: int, filename: str):

    start_time = time.perf_counter()

    try:
        img = Image.open(io.BytesIO(image_bytes))
        format = (img.format or "JPEG").upper()

        if format not in FORMAT_MAP:
            raise ValueError(f"Unsupported format: {format}")

        save_format, ext, media_type = FORMAT_MAP[format]

        output_buffer = io.BytesIO()

        # ─── Format-specific optimizations ───

        if save_format == "JPEG":
            img = img.convert("RGB")
            img.save(
                output_buffer,
                format="JPEG",
                dpi=(dpi, dpi),
                quality=90,              # 🔥 reduced from 95 (better perf)
                optimize=True,
                progressive=True,
            )

        elif save_format == "PNG":
            img.save(
                output_buffer,
                format="PNG",
                dpi=(dpi, dpi),
                optimize=True,
                compress_level=6        # 🔥 balanced compression
            )

        elif save_format == "WEBP":
            img.save(
                output_buffer,
                format="WEBP",
                quality=90,
                method=5               # 🔥 faster than 6
            )

        elif save_format in ["HEIF", "AVIF"]:
            # 1. Manually set the info dictionary so Pillow/HEIF-plugin sees it
            img.info["dpi"] = (dpi, dpi)
            
            # 2. Pass the dpi parameter (some plugins use this)
            img.save(
                output_buffer,
                format=save_format,
                quality=85,
                dpi=(dpi, dpi) 
            )
            ext = "heic" if save_format == "HEIF" else "avif"
            media_type = f"image/{ext}"

        elif save_format == "TIFF":
            img.save(
                output_buffer,
                format="TIFF",
                dpi=(dpi, dpi)
            )

        elif save_format == "BMP":
            img.save(output_buffer, format="BMP")

        elif save_format == "GIF":
            img.save(output_buffer, format="GIF")

        elif save_format == "ICO":
            img.save(output_buffer, format="ICO")

        else:
            raise ValueError("Unsupported image format")

        img.close()  # 🔥 free memory early

        output_buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, ext, media_type, processing_time_ms

    except Exception as e:
        logger.error(f"DPI sync processing error: {str(e)}")
        raise


# ─────────────────────────────────────────────
# ASYNC WRAPPER (NO FILE READ)
# ─────────────────────────────────────────────
async def image_dpi_service(image_bytes: bytes, filename: str, dpi: int):

    try:
        output_buffer, ext, media_type, processing_time_ms = await run_in_threadpool(
            _sync_change_dpi,
            image_bytes,
            dpi,
            filename
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename.split('.')[0]}_{dpi}dpi.{ext}"
                }
            ),
            "processing_time_ms": processing_time_ms,
            "ext": ext,
        }

    except Exception as e:
        logger.error(f"DPI wrapper error: {str(e)}")
        raise HTTPException(500, "Error changing image DPI.")

def _convert_rational(value):
    try:
        # Handles IFDRational or tuple
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            return float(value.numerator) / float(value.denominator)

        if isinstance(value, tuple) and len(value) == 2:
            return float(value[0]) / float(value[1])

        return float(value)
    except:
        return None

# ─────────────────────────────────────────────
# DPI CHECK (SYNC)
# ─────────────────────────────────────────────
def _sync_check_dpi(image_bytes: bytes):

    start_time = time.perf_counter()

    try:
        img = Image.open(io.BytesIO(image_bytes))

        format = (img.format or "").upper()

        dpi_x, dpi_y = None, None

        # ─────────────────────────────────────────
        # STANDARD FORMATS (JPEG, PNG)
        # ─────────────────────────────────────────
        dpi_x, dpi_y = None, None

        if "dpi" in img.info:
            dpi = img.info.get("dpi")

            if isinstance(dpi, tuple) and len(dpi) == 2:
                dpi_x, dpi_y = float(dpi[0]), float(dpi[1])

        elif format in ["TIFF", "TIF"]:
             try:
                tags = getattr(img, "tag_v2", {})

                x_res = tags.get(282)
                y_res = tags.get(283)

                dpi_x = _convert_rational(x_res) if x_res else None
                dpi_y = _convert_rational(y_res) if y_res else None


             except Exception as e:
                logger.warning(f"TIFF DPI read failed: {str(e)}")

        # ─────────────────────────────────────────
        # OTHER FORMATS (WEBP, AVIF, GIF)
        # ─────────────────────────────────────────
        else:
            # These formats usually don't support DPI properly
            dpi_x, dpi_y = None, None

        width, height = img.size

        img.close()

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "dpi_x": math.ceil(dpi_x) if dpi_x is not None else None,
            "dpi_y": math.ceil(dpi_y) if dpi_y is not None else None,
            "width": width,
            "height": height,
            "format": format,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"DPI check sync error: {str(e)}")
        raise


# ─────────────────────────────────────────────
# ASYNC CHECK WRAPPER
# ─────────────────────────────────────────────
async def image_dpi_checker_service(image_bytes: bytes):

    try:
        return await run_in_threadpool(
            _sync_check_dpi,
            image_bytes
        )

    except Exception as e:
        logger.error(f"DPI checker wrapper error: {str(e)}")
        raise HTTPException(500, "Error checking image DPI.")