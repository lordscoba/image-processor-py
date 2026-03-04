from fastapi import APIRouter, Query, UploadFile, File, Form, Depends, Request
from typing import Optional

from app.controllers.watermark_controller import watermark_controller
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/watermark-image")
@limiter.limit(RATE_LIMIT)
async def watermark_image(
    request: Request,
    file: UploadFile = File(...),
    disposition: str = Query("inline", enum=["inline", "attachment"]),
    watermark_type: str = Form(..., enum=["text", "image"]),
    text: Optional[str] = Form(None),
    font_size: int = Form(48),
    color: str = Form("#ffffff"),
    watermark_file: Optional[UploadFile] = File(None),
    scale: float = Form(0.3),
    position: str = Form("bottom-right", enum=["top-left","top-right","bottom-left","bottom-right","center"]),
    opacity: int = Form(60),
    rotation: int = Form(0),
    compression: str = Form("medium"),
    db: AsyncSession = Depends(get_db)
):
    return await watermark_controller(
        request=request,
        file=file,
        watermark_type=watermark_type,
        watermark_file=watermark_file,
        disposition=disposition,
        text=text,
        font_size=font_size,
        color=color,
        scale=scale,
        position=position,
        opacity=opacity,
        rotation=rotation,
        compression=compression,
        db=db
    )