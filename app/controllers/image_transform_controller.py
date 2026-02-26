from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import ALLOWED_EXTENSIONS
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.image_transform_service import (
    resize_image_service,
    crop_image_service,
)
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType
import time


# --------------------------
# RESIZE CONTROLLER
# --------------------------

async def resize_image_controller(
    file: UploadFile,
    width: int,
    height: int,
    keep_aspect: bool,
    request: Request,
    db: AsyncSession,
):
    start_time = time.perf_counter()

    try:
        logger.info(f"Resize request: {file.filename}")

        validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
        await validate_file_size(file)

        file_bytes = await file.read()

        response, metadata = resize_image_service(
            file_bytes,
            width,
            height,
            keep_aspect
        )

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=ActionType.RESIZE,
            request=request,
            success=True,
            status_code=200,
            file_size=len(file_bytes),
            original_format=metadata["format"],
            target_format=None,
            width=metadata["width"],
            height=metadata["height"],
            processing_time_ms=processing_time_ms,
        )

        return response

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.RESIZE,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Resize error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.RESIZE,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Resize operation failed.")


# --------------------------
# CROP CONTROLLER
# --------------------------

async def crop_image_controller(
    file: UploadFile,
    left: int,
    top: int,
    right: int,
    bottom: int,
    request: Request,
    db: AsyncSession,
):
    start_time = time.perf_counter()

    try:
        logger.info(f"Crop request: {file.filename}")

        validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
        await validate_file_size(file)

        file_bytes = await file.read()

        response, metadata = crop_image_service(
            file_bytes,
            left,
            top,
            right,
            bottom
        )

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=ActionType.CROP,
            request=request,
            success=True,
            status_code=200,
            file_size=len(file_bytes),
            original_format=metadata["format"],
            target_format=None,
            width=metadata["width"],
            height=metadata["height"],
            processing_time_ms=processing_time_ms,
        )

        return response

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.CROP,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Crop error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.CROP,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Crop operation failed.")