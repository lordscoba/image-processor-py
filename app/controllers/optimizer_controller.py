import io
import time
from fastapi import UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.file_validators import validate_file_extension, validate_file_size
from app.services.image_optimizer import (
    optimize_for_twitter,
    optimize_for_whatsapp,
    optimize_for_web,
    optimize_custom,
    optimize_for_instagram,
    optimize_for_youtube,
    optimize_for_seo,
)
from app.core.logging import logger
from app.services.log_service import log_action
from app.enums.action_type import ActionType


# -----------------------------
# Shared Logging Wrapper
# -----------------------------

async def _optimize_wrapper(
    file: UploadFile,
    request: Request,
    db: AsyncSession,
    action_type: ActionType,
    optimize_function,
    *args
):
    start_time = time.perf_counter()

    try:
        validate_file_extension(file.filename)
        await validate_file_size(file)

        contents = await file.read()
        image_data = io.BytesIO(contents)

        logger.info(f"Optimizing using {action_type.value}")

        response = optimize_function(image_data, *args)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=action_type,
            request=request,
            success=True,
            status_code=200,
            file_size=len(contents),
            original_format=file.filename.split(".")[-1].lower(),
            target_format="jpeg",  # most outputs are jpeg/webp/zip
            processing_time_ms=processing_time_ms,
        )

        return response

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=action_type,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"{action_type.value} error: {str(e)}")

        await log_action(
            db=db,
            action_type=action_type,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="Optimization failed.")
    

async def optimize_twitter_controller(file, request, db):
    return await _optimize_wrapper(
        file, request, db,
        ActionType.OPTIMIZE_TWITTER,
        optimize_for_twitter
    )


async def optimize_whatsapp_controller(file, request, db):
    return await _optimize_wrapper(
        file, request, db,
        ActionType.OPTIMIZE_WHATSAPP,
        optimize_for_whatsapp
    )


async def optimize_web_controller(file, request, db):
    return await _optimize_wrapper(
        file, request, db,
        ActionType.OPTIMIZE_WEB,
        optimize_for_web
    )


async def optimize_instagram_controller(file, request, db):
    return await _optimize_wrapper(
        file, request, db,
        ActionType.OPTIMIZE_INSTAGRAM,
        optimize_for_instagram
    )


async def optimize_youtube_controller(file, request, db):
    return await _optimize_wrapper(
        file, request, db,
        ActionType.OPTIMIZE_YOUTUBE,
        optimize_for_youtube
    )


async def optimize_seo_controller(file, request, db):
    return await _optimize_wrapper(
        file, request, db,
        ActionType.OPTIMIZE_SEO,
        optimize_for_seo
    )


async def optimize_custom_controller(file, target_kb, quality, resize_percent, request, db):
    return await _optimize_wrapper(
        file,
        request,
        db,
        ActionType.OPTIMIZE_CUSTOM,
        optimize_custom,
        target_kb,
        quality,
        resize_percent
    )