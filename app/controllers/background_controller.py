from fastapi import UploadFile
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.background_removal import remove_background
from app.core.logging import logger
import io

async def remove_background_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)

    logger.info("Removing image background")

    contents = await file.read()
    image_data = io.BytesIO(contents)

    result = remove_background(image_data)

    await file.close()
    return result