from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.action_type import ActionType
from app.services.image_color_effect_service import image_color_effect_service
from app.services.log_service import log_action
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.core.logging import logger



async def image_color_effect_controller(
    file: UploadFile,
    brightness: float,
    contrast: float,
    saturation: float,
    hue: float,
    temperature: float,
    exposure: float,
    vibrance: float,
    tint_color: str,
    preset: str,
    intensity: float,
    lut_filter: str,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Applying color effects to: {file.filename}")

        validate_file_extension(
            file.filename,
            allowed_extensions=["jpg", "jpeg", "png", "webp"]
        )

        await validate_file_size(file)

        result = await image_color_effect_service(
            file=file,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            hue=hue,
            temperature=temperature,
            exposure=exposure,
            vibrance=vibrance,
            tint_color=tint_color,
            preset=preset,
            intensity=intensity,
            lut_filter=lut_filter
        )

        logger.info("Color effects applied successfully")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_COLOR_EFFECTS,
            request=request,
            success=True,
            status_code=200,
            file_size=None,  # service does not return size
            original_format=file.filename.split(".")[-1].lower(),
            target_format="jpg",
            width=None,
            height=None,
            processing_time_ms=result["processing_time_ms"],
        )

        return result["response"]

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_COLOR_EFFECTS,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Image color effect error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.IMAGE_COLOR_EFFECTS,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Image color effect processing failed."
        )