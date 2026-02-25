from fastapi import UploadFile
from app.core.config import ALLOWED_EXTENSIONS
from app.services.image_base64_service import (
    image_to_base64_service,
    base64_to_image_service,
)
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.core.logging import logger



async def image_to_base64_controller(file: UploadFile):
    logger.info(f"Image to Base64 request: {file.filename}")

    validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
    await validate_file_size(file)

    return await image_to_base64_service(file.file)


async def base64_to_image_controller(base64_string: str):
    logger.info("Base64 to Image request")

    return await base64_to_image_service(base64_string)