from fastapi import UploadFile
from app.utils.file_validators import validate_file_size, validate_file_extension
from app.services.image_converter import convert_image
from app.core.logging import logger

async def convert_controller(file: UploadFile, target_format: str):

    logger.info(f"Incoming file: {file.filename}")

    validate_file_extension(file.filename)
    await validate_file_size(file)

    result = convert_image(file.file, target_format)

    logger.info(f"Successfully converted to {target_format}")

    return result