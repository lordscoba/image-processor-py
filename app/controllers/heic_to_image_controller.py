from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.heic_to_image_service import heic_to_image_service, image_to_heic_service
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def heic_to_image_controller(
    file: UploadFile,
    format: str,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting HEIC to {format.upper()}: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["heic", "heif"]
        )

        await validate_file_size(file)

        result_data = await heic_to_image_service(
            file=file,
            target_format=format
        )

        logger.info("HEIC converted successfully")

        # await log_action(
        #     db=db,
        #     action_type=ActionType.HEIC_TO_IMAGE,
        #     request=request,
        #     success=True,
        #     status_code=200,
        #     file_size=result_data["original_size"],
        #     original_format=file.filename.split(".")[-1].lower(),
        #     target_format=format.lower(),
        #     width=None,
        #     height=None,
        #     processing_time_ms=result_data["processing_time_ms"],
        # )

        return result_data["response"]

    except HTTPException as e:

        # await log_action(
        #     db=db,
        #     action_type=ActionType.HEIC_TO_IMAGE,
        #     request=request,
        #     success=False,
        #     status_code=e.status_code,
        #     error_type="http_exception",
        #     error_message=str(e.detail),
        # )

        raise e

    except Exception as e:

        logger.error(f"HEIC to image error: {str(e)}")

        # await log_action(
        #     db=db,
        #     action_type=ActionType.HEIC_TO_IMAGE,
        #     request=request,
        #     success=False,
        #     status_code=500,
        #     error_type="internal_error",
        #     error_message=str(e),
        # )

        raise HTTPException(
            status_code=500,
            detail="HEIC conversion failed."
        )


async def image_to_heic_controller(
    file: UploadFile,
    quality: int,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting Image to HEIC: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["jpg", "jpeg", "png"]
        )

        await validate_file_size(file)

        result_data = await image_to_heic_service(
            file=file,
            quality=quality
        )

        logger.info("Image converted to HEIC successfully")

        # await log_action(
        #     db=db,
        #     action_type=ActionType.IMAGE_TO_HEIC,
        #     request=request,
        #     success=True,
        #     status_code=200,
        #     file_size=result_data["original_size"],
        #     original_format=file.filename.split(".")[-1].lower(),
        #     target_format="heic",
        #     width=None,
        #     height=None,
        #     processing_time_ms=result_data["processing_time_ms"],
        # )

        return result_data["response"]

    except HTTPException as e:

        # await log_action(
        #     db=db,
        #     action_type=ActionType.IMAGE_TO_HEIC,
        #     request=request,
        #     success=False,
        #     status_code=e.status_code,
        #     error_type="http_exception",
        #     error_message=str(e.detail),
        # )

        raise e

    except Exception as e:

        logger.error(f"Image to HEIC error: {str(e)}")

        # await log_action(
        #     db=db,
        #     action_type=ActionType.IMAGE_TO_HEIC,
        #     request=request,
        #     success=False,
        #     status_code=500,
        #     error_type="internal_error",
        #     error_message=str(e),
        # )

        raise HTTPException(
            status_code=500,
            detail="Image to HEIC conversion failed."
        )