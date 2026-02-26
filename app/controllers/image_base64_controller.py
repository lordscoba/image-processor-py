from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import ALLOWED_EXTENSIONS
from app.services.image_base64_service import (
    image_to_base64_service,
    base64_to_image_service,
)
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType
import time


# --------------------------------------------------
# Image → Base64
# --------------------------------------------------

async def image_to_base64_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession
):
    start_time = time.perf_counter()

    try:
        logger.info(f"Image to Base64 request: {file.filename}")

        validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
        await validate_file_size(file)

        file_bytes = await file.read()

        result = await image_to_base64_service(file.file)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=ActionType.TO_BASE64,
            request=request,
            success=True,
            status_code=200,
            file_size=len(file_bytes),
            original_format=result.get("format"),
            target_format="base64",
            width=None,
            height=None,
            processing_time_ms=processing_time_ms,
        )

        return result

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.TO_BASE64,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image to Base64 error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.TO_BASE64,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Conversion failed.")


# --------------------------------------------------
# Base64 → Image
# --------------------------------------------------

async def base64_to_image_controller(
    base64_string: str,
    request: Request,
    db: AsyncSession
):
    start_time = time.perf_counter()

    try:
        logger.info("Base64 to Image request")

        result = await base64_to_image_service(base64_string)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=ActionType.FROM_BASE64,
            request=request,
            success=True,
            status_code=200,
            file_size=len(base64_string),
            original_format="base64",
            target_format="image",
            width=None,
            height=None,
            processing_time_ms=processing_time_ms,
        )

        return result

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.FROM_BASE64,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Base64 to Image error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.FROM_BASE64,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Conversion failed.")