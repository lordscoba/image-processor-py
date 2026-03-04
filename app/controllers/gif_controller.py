import time
from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.enums.action_type import ActionType
from app.services.gif_service import video_to_gif_service, image_to_gif_service
from app.services.log_service import log_action
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.core.logging import logger


async def video_to_gif_controller(
    file: UploadFile,
    fps: int,
    width: int,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting video to GIF: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["mp4", "mov", "avi", "webm"]
        )

        await validate_file_size(file)

        if width > 600:
            raise HTTPException(
                status_code=400,
                detail="Maximum GIF width is 600px"
            )

        result_data = await video_to_gif_service(
            file=file,
            fps=fps,
            width=width
        )

        logger.info("Video converted to GIF successfully")

        await log_action(
            db=db,
            action_type=ActionType.VIDEO_TO_GIF,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format=file.filename.split(".")[-1].lower(),
            target_format="gif",
            width=width,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.VIDEO_TO_GIF,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Video to GIF error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.VIDEO_TO_GIF,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Video to GIF conversion failed."
        )


async def image_to_gif_controller(
    file: UploadFile,
    duration: int,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting image to GIF: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["jpg", "jpeg", "png", "webp"]
        )

        await validate_file_size(file)

        result_data = await image_to_gif_service(
            file=file,
            duration=duration
        )

        logger.info("Image converted to GIF successfully")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_GIF,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format=file.filename.split(".")[-1].lower(),
            target_format="gif",
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_GIF,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image to GIF error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_GIF,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image to GIF conversion failed."
        )