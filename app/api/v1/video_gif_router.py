from fastapi import APIRouter, UploadFile, File, Request, Depends, Query
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
    fps: int = Query(10, ge=1, le=30),
    width: int = Query(480, ge=100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    return await video_to_gif_controller(
        file=file,
        fps=fps,
        width=width,
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