from fastapi import UploadFile
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.image_analyzer import analyze_image
from app.core.logging import logger

async def analyze_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)

    logger.info("Analyzing image")

    contents = await file.read()
    result = analyze_image(contents)

    await file.close()
    return result