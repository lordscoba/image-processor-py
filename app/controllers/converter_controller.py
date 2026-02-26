from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.file_validators import validate_file_size, validate_file_extension
from app.services.image_converter import convert_image
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType


async def convert_controller(
    file: UploadFile,
    target_format: str,
    request: Request,
    db: AsyncSession,
):
    try:
        logger.info(f"Incoming file: {file.filename}")

        validate_file_extension(file.filename)
        await validate_file_size(file)

        result_data = convert_image(file.file, target_format)

        logger.info(f"Successfully converted to {target_format}")

        # ✅ Log Success
        await log_action(
            db=db,
            action_type=ActionType.CONVERT,
            request=request,
            success=True,
            status_code=200,
            file_size=file.size if hasattr(file, "size") else None,
            original_format=result_data["original_format"],
            target_format=result_data["target_format"],
            width=result_data["width"],
            height=result_data["height"],
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.CONVERT,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
            file_size=file.size if hasattr(file, "size") else None,
        )

        raise e

    except Exception as e:

        logger.error(f"Conversion error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.CONVERT,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
            file_size=file.size if hasattr(file, "size") else None,
        )

        raise HTTPException(status_code=500, detail="Internal server error")