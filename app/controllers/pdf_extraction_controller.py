from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pdf_extraction_service import extract_pdf_images_service
from app.utils.file_validators import validate_file_size, validate_file_extension
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def extract_pdf_images_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Extracting images from PDF: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["pdf"]
        )

        await validate_file_size(file)

        result_data = await extract_pdf_images_service(file)

        logger.info(f"Successfully extracted images from {file.filename}")

        await log_action(
            db=db,
            action_type=ActionType.EXTRACT_PDF_IMAGES,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format="pdf",
            target_format="zip",
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.EXTRACT_PDF_IMAGES,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"PDF image extraction error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.EXTRACT_PDF_IMAGES,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to extract images from PDF."
        )