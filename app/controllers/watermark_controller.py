from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.watermark_service import watermark_service
from app.utils.file_validators import validate_file_size, validate_file_extension
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def watermark_controller(
    file: UploadFile,
    watermark_type: str,
    watermark_file: UploadFile | None,
    request: Request,
    db: AsyncSession,
    **kwargs
):
    try:

        logger.info(f"Applying watermark to image: {file.filename}")

        validate_file_extension(
            file.filename,
            ["jpg", "jpeg", "png"]
        )

        await validate_file_size(file)

        if watermark_type == "image":

            if not watermark_file:
                raise HTTPException(
                    status_code=400,
                    detail="watermark_file required for image watermark"
                )

            validate_file_extension(
                watermark_file.filename,
                ["png", "jpg", "jpeg"]
            )

        result = await watermark_service(
            file=file,
            watermark_type=watermark_type,
            watermark_file=watermark_file,
            **kwargs
        )

        logger.info("Watermark applied successfully")

        await log_action(
            db=db,
            action_type=ActionType.WATERMARK_IMAGES,
            request=request,
            success=True,
            status_code=200,
            file_size=None,
            original_format=file.filename.split(".")[-1].lower(),
            target_format="jpg",
            width=None,
            height=None,
            processing_time_ms=None,
        )

        return result

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.WATERMARK_IMAGES,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Watermark error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.WATERMARK_IMAGES,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image watermarking failed."
        )