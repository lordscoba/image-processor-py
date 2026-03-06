from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.gif_controller import video_to_gif_controller, image_to_gif_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()


@router.post("/video-to-gif")
@limiter.limit(RATE_LIMIT)
async def video_to_gif(
    request: Request,

    file: UploadFile = File(...),

    fps: int = Query(
        10,
        ge=1,
        le=30,
        description="Frames per second of the output GIF"
    ),

    width: int = Query(
        480,
        ge=100,
        le=1000,
        description="Output width of the GIF"
    ),

    start_time: float = Query(
        0,
        ge=0,
        description="Start time in seconds for trimming the video"
    ),

    end_time: float = Query(
        5,
        gt=0,
        description="End time in seconds for trimming the video"
    ),

    quality: str = Query(
        "medium",
        pattern="^(hd|high|medium|low)$",
        description="GIF quality preset"
    ),

    reverse: bool = Query(
        False,
        description="Reverse the video before converting to GIF"
    ),

    db: AsyncSession = Depends(get_db)

):
    if end_time - start_time > 15:
        raise HTTPException(
            status_code=400,
            detail="Maximum GIF duration is 15 seconds"
        )

    return await video_to_gif_controller(
        file=file,
        fps=fps,
        width=width,
        start_time=start_time,
        end_time=end_time,
        quality=quality,
        reverse=reverse,
        request=request,
        db=db
    )


@router.post("/image-to-gif")
@limiter.limit(RATE_LIMIT)
async def image_to_gif(
    request: Request,
    file: UploadFile = File(...),
    duration: int = Query(500, ge=100, le=3000),
    db: AsyncSession = Depends(get_db)
):
    return await image_to_gif_controller(
        file=file,
        duration=duration,
        request=request,
        db=db
    )