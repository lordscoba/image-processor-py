import time

from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.exif_scrubber_service import exif_scrubber_service
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def exif_scrubber_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
):

    try:
        logger.info(f"Scrubbing EXIF metadata from: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "heif"]
        )

        await validate_file_size(file)

        # read file once for logging
        await file.seek(0)
        file_bytes = await file.read()

        # reset pointer before sending to service
        await file.seek(0)

        result_data = await exif_scrubber_service(file)

        logger.info("EXIF metadata removed successfully")

        await log_action(
            db=db,
            action_type=ActionType.EXIF_SCRUBBER,
            request=request,
            success=True,
            status_code=200,
            file_size=len(file_bytes),
            original_format=file.filename.split(".")[-1].lower(),
            target_format=file.filename.split(".")[-1].lower(),
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.EXIF_SCRUBBER,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"EXIF scrub error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.EXIF_SCRUBBER,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="EXIF metadata removal failed."
        )