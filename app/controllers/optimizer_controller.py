import io

from fastapi import UploadFile
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.image_optimizer import (
    optimize_for_twitter,
    optimize_for_whatsapp,
    optimize_for_web,
    optimize_custom,
    optimize_for_instagram,
    optimize_for_youtube,
    optimize_for_seo,
)
from app.core.logging import logger

async def optimize_twitter_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)
    logger.info("Optimizing for Twitter")
    return optimize_for_twitter(file.file)

async def optimize_whatsapp_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)
    logger.info("Optimizing for WhatsApp")
    return optimize_for_whatsapp(file.file)

async def optimize_web_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)
    logger.info("Optimizing for Web")
    return optimize_for_web(file.file)

async def optimize_custom_controller(file, target_kb, quality, resize_percent):
    # Validation remains
    validate_file_extension(file.filename)
    await validate_file_size(file)
    
    # Use 'with' to ensure the file is closed after processing to free memory
    try:
        contents = await file.read()
        image_data = io.BytesIO(contents)
        return optimize_custom(image_data, target_kb, quality, resize_percent)
    finally:
        await file.close()
    
async def optimize_instagram_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)
    logger.info("Optimizing for Instagram")
    return optimize_for_instagram(file.file)

async def optimize_youtube_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)
    logger.info("Optimizing for YouTube Thumbnail")
    return optimize_for_youtube(file.file)

async def optimize_seo_controller(file: UploadFile):
    validate_file_extension(file.filename)
    await validate_file_size(file)
    logger.info("Optimizing for SEO Responsive")
    return optimize_for_seo(file.file)