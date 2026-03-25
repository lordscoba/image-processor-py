from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.image_dpi_service import image_dpi_checker_service, image_dpi_service
from app.utils.file_validators import validate_file_extension, validate_file_size, validate_real_image
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger

ALLOWED_EXTENSIONS = [
    "jpg", "jpeg",
    "png",
    "webp",
    "heic", "heif",
    "tiff", "tif",
    "bmp",
    "ico",
    "gif",
    "avif",
]


# ─────────────────────────────────────────────
# 🔥 SHARED PREPROCESSOR (VERY IMPORTANT)
# ─────────────────────────────────────────────
async def _prepare_file(file: UploadFile):

    # Validate extension FIRST (cheap)
    validate_file_extension(file.filename, ALLOWED_EXTENSIONS)

    # Read ONCE
    await file.seek(0)
    image_bytes = await file.read()

    # Validate size using bytes (no re-read)
    validate_file_size(image_bytes)

    # Validate real file
    validate_real_image(file.filename, image_bytes)

    return image_bytes

async def image_dpi_controller(
    file: UploadFile,
    dpi: int,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Changing DPI to {dpi} for: {file.filename}")

        image_bytes = await _prepare_file(file)

        result_data = await image_dpi_service(
            image_bytes=image_bytes,   # 🔥 pass bytes
            filename=file.filename,
            dpi=dpi,
        )

        logger.info("Image DPI changed successfully")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_DPI_CHANGER,
            request=request,
            success=True,
            status_code=200,
            file_size=None,
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
            action_type=ActionType.IMAGE_DPI_CHANGER,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image DPI change error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_DPI_CHANGER,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image DPI change failed."
        )


async def image_dpi_checker_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Checking DPI for: {file.filename}")

        image_bytes = await _prepare_file(file)

        result_data = await image_dpi_checker_service(
            image_bytes=image_bytes  # 🔥 pass bytes
        )

        logger.info("Image DPI checked successfully")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_DPI_CHECKER,
            request=request,
            success=True,
            status_code=200,
            file_size=None,
            original_format=file.filename.split(".")[-1].lower(),
            target_format=None,
            width=None,
            height=None,
            processing_time_ms=None,
        )

        return result_data

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_DPI_CHECKER,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image DPI checker error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_DPI_CHECKER,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image DPI check failed."
        )