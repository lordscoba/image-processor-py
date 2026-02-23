from PIL import Image
from fastapi import HTTPException
from app.core.config import MAX_IMAGE_PIXELS

def validate_image_safety(image: Image.Image):
    width, height = image.size
    if width * height > MAX_IMAGE_PIXELS:
        raise HTTPException(status_code=400, detail="Image too large in dimensions")