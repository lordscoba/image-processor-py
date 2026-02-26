from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
import io
from app.core.config import MAX_DIMENSION
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety



def _prepare_image(file):
    try:
        image = Image.open(file)

        # Auto-orient (fix sideways camera photos)
        image = ImageOps.exif_transpose(image)

        validate_image_safety(image)

        return image

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    except Exception as e:
        logger.error(f"Image preparation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Image processing failed.")
    

def resize_image_service(file_bytes, width: int, height: int, keep_aspect: bool):

    image = _prepare_image(io.BytesIO(file_bytes))
    original_format = image.format if image.format else "PNG"

    if keep_aspect:
        image.thumbnail((width, height), Image.LANCZOS)
    else:
        image = image.resize((width, height), Image.LANCZOS)

    response = _stream_image(image)

    metadata = {
        "width": image.size[0],
        "height": image.size[1],
        "format": original_format,
    }

    return response, metadata
    

def crop_image_service(file_bytes, left: int, top: int, right: int, bottom: int):

    image = _prepare_image(io.BytesIO(file_bytes))
    original_format = image.format if image.format else "PNG"

    cropped = image.crop((left, top, right, bottom))

    response = _stream_image(cropped)

    metadata = {
        "width": cropped.size[0],
        "height": cropped.size[1],
        "format": original_format,
    }

    return response, metadata
    

def _stream_image(image: Image.Image):

    buffer = io.BytesIO()

    # Preserve original format safely
    format = image.format if image.format else "PNG"

    if format.upper() == "JPEG":
        image = image.convert("RGB")

    image.save(buffer, format=format, optimize=True, quality=90)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type=f"image/{format.lower()}",
        headers={
            "Content-Disposition": f"attachment; filename=processed.{format.lower()}"
        }
    )