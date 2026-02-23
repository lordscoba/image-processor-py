from PIL import Image, ImageOps, UnidentifiedImageError
import io
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety

# Mapping for Pillow's save format
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
    try:
        logger.info(f"Starting conversion process to {target_format}")
        
        # 1. Open and Validate
        image = Image.open(file)
        validate_image_safety(image)
        
        target_format = target_format.lower()
        if target_format not in SUPPORTED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Target format '{target_format}' not supported")

        # 2. Handle Transparency & Color Modes
        # If converting to JPEG/BMP (which don't support alpha), we must remove transparency
        if target_format in ["jpeg", "jpg", "bmp"]:
            if image.mode in ("RGBA", "P", "LA"):
                # Create a white background and paste the image over it
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            else:
                image = image.convert("RGB")
        
        # Keep transparency for supported formats
        elif target_format in ["png", "webp", "gif"]:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")

        # 3. Auto-orient (Fixes images that appear sideways from phone cameras)
        image = ImageOps.exif_transpose(image)

        # 4. Save to Buffer
        buffer = io.BytesIO()
        image.save(
            buffer, 
            format=SUPPORTED_FORMATS[target_format], 
            optimize=True, # Compresses the file slightly without quality loss
            quality=90     # Good balance for JPEGs
        )
        buffer.seek(0)

        # 5. Return Stream
        return StreamingResponse(
            buffer,
            media_type=f"image/{target_format}",
            headers={"Content-Disposition": f"attachment; filename=converted.{target_format}"}
        )

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as e:
        logger.error(f"Conversion Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during image processing.")