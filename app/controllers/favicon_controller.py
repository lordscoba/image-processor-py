from fastapi import UploadFile
from app.services.favicon_service import generate_favicon_service
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.core.logging import logger

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


async def generate_favicon_controller(
    file: UploadFile,
    extension: str,
    background: str,
    padding: int
):
    logger.info(f"Favicon generation request: {file.filename}")

    validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
    await validate_file_size(file)

    return await generate_favicon_service(
        file.file,
        extension,
        background,
        padding
    )