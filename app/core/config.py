import os
from dotenv import load_dotenv

load_dotenv()

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5242880))
RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# Expanded allowed extensions for validation
ALLOWED_EXTENSIONS = {
    "jpeg", "jpg", "png", "webp", "bmp", "tiff", "tif", 
    "gif", "ico", "heic", "heif", "avif"
}

MAX_IMAGE_PIXELS = 20_000_000