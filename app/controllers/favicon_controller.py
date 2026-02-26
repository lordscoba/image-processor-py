from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.favicon_service import generate_favicon_service
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType
import time

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


async def generate_favicon_controller(
    file: UploadFile,
    extension: str,
    background: str,
    padding: int,
    request: Request,
    db: AsyncSession
):
    start_time = time.perf_counter()

    try:
        logger.info(f"Favicon generation request: {file.filename}")

        validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
        await validate_file_size(file)

        file_bytes = await file.read()

        response = await generate_favicon_service(
            file.file,
            extension,
            background,
            padding
        )

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=ActionType.FAVICON_GENERATE,
            request=request,
            success=True,
            status_code=200,
            file_size=len(file_bytes),
            original_format=file.filename.split(".")[-1].lower(),
            target_format=extension,
            width=None,
            height=None,
            processing_time_ms=processing_time_ms,
        )

        return response

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.FAVICON_GENERATE,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Favicon error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.FAVICON_GENERATE,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Favicon generation failed.")