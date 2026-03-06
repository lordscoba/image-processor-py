from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sticker_service import image_to_sticker_service, video_to_sticker_service
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def video_to_sticker_controller(
    file: UploadFile,
    fps: int,
    start_time: float,
    end_time: float,
    quality: str,
    reverse: bool,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting video to WhatsApp sticker: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["mp4", "mov", "webm"]
        )

        await validate_file_size(file)

        result_data = await video_to_sticker_service(
            file=file,
            fps=fps,
            start_time=start_time,
            end_time=end_time,
            quality=quality,
            reverse=reverse
        )

        logger.info("Video converted to sticker successfully")

        await log_action(
            db=db,
            action_type=ActionType.VIDEO_TO_STICKER,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format=file.filename.split(".")[-1].lower(),
            target_format="webp",
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.VIDEO_TO_STICKER,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Video to sticker error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.VIDEO_TO_STICKER,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Video to sticker conversion failed."
        )

async def image_to_sticker_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting image to WhatsApp sticker: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["jpg", "jpeg", "png", "webp"]
        )

        await validate_file_size(file)

        result_data = await image_to_sticker_service(file=file)

        logger.info("Image converted to sticker successfully")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_STICKER,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format=file.filename.split(".")[-1].lower(),
            target_format="webp",
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_STICKER,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image to sticker error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_STICKER,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image to sticker conversion failed."
        )