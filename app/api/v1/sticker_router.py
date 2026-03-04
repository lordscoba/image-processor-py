from fastapi import APIRouter, Query, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.sticker_controller import video_to_sticker_controller, image_to_sticker_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()

@router.post("/video-to-sticker")
@limiter.limit(RATE_LIMIT)
async def video_to_sticker(
    request: Request,
    file: UploadFile = File(...),
    fps: int = Query(12, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    return await video_to_sticker_controller(
        file=file,
        fps=fps,
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