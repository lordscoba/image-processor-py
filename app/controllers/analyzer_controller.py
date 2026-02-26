from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.image_analyzer import analyze_image
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType
import time


async def analyze_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
):
    start_time = time.perf_counter()

    try:
        logger.info(f"Incoming file for analysis: {file.filename}")

        validate_file_extension(file.filename)
        await validate_file_size(file)

        contents = await file.read()
        result = analyze_image(contents)

        await file.close()

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        basic_info = result.get("basic_info", {})

        # ✅ Log Success
        await log_action(
            db=db,
            action_type=ActionType.ANALYZE,
            request=request,
            success=True,
            status_code=200,
            file_size=len(contents),
            original_format=basic_info.get("format"),
            target_format=None,
            width=basic_info.get("width"),
            height=basic_info.get("height"),
            processing_time_ms=processing_time_ms,
        )

        return result

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.ANALYZE,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
            file_size=file.size if hasattr(file, "size") else None,
        )

        raise e

    except Exception as e:

        logger.error(f"Analysis error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.ANALYZE,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
            file_size=file.size if hasattr(file, "size") else None,
        )

        raise HTTPException(status_code=500, detail="Internal server error")