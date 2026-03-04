from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.file_validators import validate_file_size, validate_file_extension
from app.services.image_to_pdf_service import image_to_pdf_service, pdf_to_image_service
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def image_to_pdf_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting image to PDF: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["jpg", "jpeg", "png"]
        )

        await validate_file_size(file)

        result_data = await image_to_pdf_service(file)

        logger.info("Image converted to PDF successfully")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_PDF,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format=file.filename.split(".")[-1].lower(),
            target_format="pdf",
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_PDF,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image to PDF error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_TO_PDF,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image to PDF conversion failed."
        )


async def pdf_to_image_controller(
    file: UploadFile,
    format: str,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Converting PDF to {format.upper()}: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["pdf"]
        )

        await validate_file_size(file)

        result_data = await pdf_to_image_service(file, format)

        logger.info("PDF converted to images successfully")

        await log_action(
            db=db,
            action_type=ActionType.PDF_TO_IMAGE,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format="pdf",
            target_format=format.lower(),
            width=None,
            height=None,
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.PDF_TO_IMAGE,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"PDF to image error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.PDF_TO_IMAGE,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="PDF to image conversion failed."
        )