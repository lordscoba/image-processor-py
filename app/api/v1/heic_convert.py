
from fastapi import APIRouter, Query, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.heic_to_image_controller import heic_to_image_controller, image_to_heic_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()

@router.post("/heic-to-image")
@limiter.limit(RATE_LIMIT)
async def heic_to_image(
    request: Request,
    file: UploadFile = File(...),
    format: str = Query("jpg", enum=["jpg", "png"]),
    db: AsyncSession = Depends(get_db)
):
    return await heic_to_image_controller(
        file=file,
        format=format,
        request=request,
        db=db
    )

@router.post("/image-to-heic")
@limiter.limit(RATE_LIMIT)
async def image_to_heic(
    request: Request,
    file: UploadFile = File(...),
    quality: int = Query(80, ge=10, le=100, description="HEIC quality level"),
    db: AsyncSession = Depends(get_db)
):
    return await image_to_heic_controller(
        file=file,
        quality=quality,
        request=request,
        db=db
    )