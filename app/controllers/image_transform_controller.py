from fastapi import UploadFile
from app.core.config import ALLOWED_EXTENSIONS
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.image_transform_service import (
    resize_image_service,
    crop_image_service,
)
from app.core.logging import logger

async def resize_image_controller(file: UploadFile, width: int, height: int, keep_aspect: bool):
    logger.info(f"Resize request: {file.filename}")

    validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
    await validate_file_size(file)

    return resize_image_service(file.file, width, height, keep_aspect)


async def crop_image_controller(file: UploadFile, left: int, top: int, right: int, bottom: int):
    logger.info(f"Crop request: {file.filename}")

    validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
    await validate_file_size(file)

    return crop_image_service(file.file, left, top, right, bottom)