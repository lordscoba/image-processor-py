from PIL import Image, ImageOps, UnidentifiedImageError
import io
import time
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety

SUPPORTED_FORMATS = {
    "jpeg": "JPEG",
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
    "gif": "GIF",
    "ico": "ICO",
}


def convert_image(file, target_format: str):
    start_time = time.perf_counter()

    try:
        logger.info(f"Starting conversion process to {target_format}")

        image = Image.open(file)
        validate_image_safety(image)

        original_format = image.format.lower() if image.format else None
        width, height = image.size

        target_format = target_format.lower()
        if target_format not in SUPPORTED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Target format '{target_format}' not supported")

        if target_format in ["jpeg", "jpg", "bmp"]:
            if image.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            else:
                image = image.convert("RGB")

        elif target_format in ["png", "webp", "gif"]:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")

        image = ImageOps.exif_transpose(image)

        buffer = io.BytesIO()
        image.save(
            buffer,
            format=SUPPORTED_FORMATS[target_format],
            optimize=True,
            quality=90
        )
        buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        response = StreamingResponse(
            buffer,
            media_type=f"image/{target_format}",
            headers={"Content-Disposition": f"attachment; filename=converted.{target_format}"}
        )

        return {
            "response": response,
            "original_format": original_format,
            "target_format": target_format,
            "width": width,
            "height": height,
            "processing_time_ms": processing_time_ms,
        }

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as e:
        logger.error(f"Conversion Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during image processing.")