from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.file_validators import validate_file_size, validate_file_extension
from app.services.pdf_compressor import compress_pdf_file, compress_pdf_pro_service
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType

async def compress_pdf_controller(
    file: UploadFile,
    compression_level: str,
    request: Request,
    db: AsyncSession,
):
    try:
        logger.info(f"Incoming PDF: {file.filename}")

        validate_file_extension(file.filename, allowed_extensions=["pdf"])
        await validate_file_size(file)

        result_data = await compress_pdf_file(file.file, compression_level)

        logger.info("PDF compressed successfully")

        await log_action(
            db=db,
            action_type=ActionType.PDF_COMPRESS,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format="pdf",
            target_format="pdf",
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:
        await log_action(
            db=db,
            action_type=ActionType.PDF_COMPRESS,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )
        raise e

    except Exception as e:
        logger.error(f"Compression error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.PDF_COMPRESS,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Internal server error")


async def compress_pdf_pro_controller(
    file: UploadFile,
    quality: int,
    dpi: int,
    request: Request,
    db: AsyncSession,
):
    try:
        logger.info(f"Incoming PRO PDF: {file.filename}")

        validate_file_extension(file.filename, allowed_extensions=["pdf"])
        await validate_file_size(file)

        result_data = await compress_pdf_pro_service(
            file=file.file,
            quality=quality,
            dpi=dpi
        )

        await log_action(
            db=db,
            action_type=ActionType.PDF_COMPRESS_PRO,
            request=request,
            success=True,
            status_code=200,
            file_size=result_data["original_size"],
            original_format="pdf",
            target_format="pdf",
            processing_time_ms=result_data["processing_time_ms"],
        )

        return result_data["response"]

    except HTTPException as e:
        await log_action(
            db=db,
            action_type=ActionType.PDF_COMPRESS_PRO,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )
        raise e

    except Exception as e:
        logger.error(f"Compression error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.PDF_COMPRESS_PRO,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )
        logger.error(f"PRO Compression error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")