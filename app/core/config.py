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

MAX_DIMENSION = 8000  # Prevent massive memory abuse
MAX_BASE64_SIZE = 15 * 1024 * 1024  # 15MB decoded protection
# Standardized allowed output formats
ALLOWED_OUTPUT_FORMATS = {"png": "PNG", "jpeg": "JPEG", "webp": "WEBP"}