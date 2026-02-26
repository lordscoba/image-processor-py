from fastapi import HTTPException, UploadFile, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.svg_optimizer import optimize_svg_service
from app.utils.svg_validators import validate_svg_safety
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger
import time


async def optimize_svg_controller(
    file: UploadFile,
    request: Request,
    db: AsyncSession
):
    start_time = time.perf_counter()

    try:
        if not file.filename.lower().endswith(".svg"):
            raise HTTPException(status_code=400, detail="Only .svg files allowed")

        content = await file.read()

        if len(content) > 2_000_000:
            raise HTTPException(status_code=413, detail="File too large")

        svg_text = content.decode("utf-8")

        validate_svg_safety(svg_text)

        optimized_buffer = await optimize_svg_service(svg_text)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        await log_action(
            db=db,
            action_type=ActionType.SVG_OPTIMIZE,
            request=request,
            success=True,
            status_code=200,
            file_size=len(content),
            original_format="svg",
            target_format="svg",
            width=None,
            height=None,
            processing_time_ms=processing_time_ms,
        )

        return StreamingResponse(
            optimized_buffer,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=min-{file.filename}"
            }
        )

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.SVG_OPTIMIZE,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"SVG optimization error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.SVG_OPTIMIZE,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail="SVG optimization failed.")