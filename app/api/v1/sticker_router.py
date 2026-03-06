from fastapi import APIRouter, Query, UploadFile, File, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.sticker_controller import image_to_sticker_controller, video_to_sticker_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()


@router.post("/video-to-sticker")
@limiter.limit(RATE_LIMIT)
async def video_to_sticker(
    request: Request,

    file: UploadFile = File(...),

    fps: int = Query(
        12,
        ge=1,
        le=20,
        description="Frames per second for animated sticker"
    ),

    start_time: float = Query(
        0,
        ge=0,
        description="Start time in seconds for trimming"
    ),

    end_time: float = Query(
        5,
        gt=0,
        description="End time in seconds"
    ),

    quality: str = Query(
        "medium",
        pattern="^(hd|high|medium|low)$",
        description="Sticker quality preset"
    ),

    reverse: bool = Query(
        False,
        description="Reverse sticker animation"
    ),

    db: AsyncSession = Depends(get_db)

):
    if end_time - start_time > 6:
        raise HTTPException(
            status_code=400,
            detail="Maximum sticker duration is 6 seconds"
        )

    return await video_to_sticker_controller(
        file=file,
        fps=fps,
        start_time=start_time,
        end_time=end_time,
        quality=quality,
        reverse=reverse,
        request=request,
        db=db
    )


@router.post("/image-to-sticker")
@limiter.limit(RATE_LIMIT)
async def image_to_sticker(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await image_to_sticker_controller(
        file=file,
        request=request,
        db=db
    )