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
    

def resize_image_service(file, width: int, height: int, keep_aspect: bool):

    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise HTTPException(status_code=400, detail="Requested dimensions too large.")

    image = _prepare_image(file)

    try:
        if keep_aspect:
            # High-quality resizing
            image.thumbnail((width, height), Image.LANCZOS)
        else:
            image = image.resize((width, height), Image.LANCZOS)

        return _stream_image(image)

    except Exception as e:
        logger.error(f"Resize error: {str(e)}")
        raise HTTPException(status_code=500, detail="Resize operation failed.")
    


def crop_image_service(file, left: int, top: int, right: int, bottom: int):

    image = _prepare_image(file)

    width, height = image.size

    # Validate crop box
    if right <= left or bottom <= top:
        raise HTTPException(status_code=400, detail="Invalid crop dimensions.")

    if right > width or bottom > height:
        raise HTTPException(
            status_code=400,
            detail="Crop box exceeds image boundaries."
        )

    try:
        cropped = image.crop((left, top, right, bottom))
        return _stream_image(cropped)

    except Exception as e:
        logger.error(f"Crop error: {str(e)}")
        raise HTTPException(status_code=500, detail="Crop operation failed.")
    

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