from fastapi import APIRouter, UploadFile, File, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.image_color_effect_controller import image_color_effect_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.enums.lut_filter_enum import LUTFilter

router = APIRouter()


@router.post("/image-color-effect")
@limiter.limit(RATE_LIMIT)
async def image_color_effect(
    request: Request,
    file: UploadFile = File(...),

    brightness: float = Query(1.0, ge=0.0, le=3.0),
    contrast: float = Query(1.0, ge=0.0, le=3.0),
    saturation: float = Query(1.0, ge=0.0, le=3.0),

    hue: float = Query(0.0, ge=-180, le=180),

    temperature: float = Query(0.0, ge=-100, le=100),
    exposure: float = Query(0.0, ge=-5, le=5),
    vibrance: float = Query(0.0, ge=-100, le=100),

    tint_color: str = Query(None),

    preset: str = Query(None),
    intensity: float = Query(1.0, ge=0.0, le=1.0),

    lut_filter: LUTFilter = Query(None),

    db: AsyncSession = Depends(get_db)
):
    return await image_color_effect_controller(
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
        lut_filter=lut_filter,
        request=request,
        db=db,
    )