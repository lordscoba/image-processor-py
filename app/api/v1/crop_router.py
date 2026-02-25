from fastapi import APIRouter, UploadFile, File, Query, Request
from app.controllers.image_transform_controller import (
    crop_image_controller,
)
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter(prefix="/images", tags=["Image Cropper"])


@router.post("/crop")
@limiter.limit(RATE_LIMIT)
async def crop_image(
    request: Request,
    file: UploadFile = File(...),
    left: int = Query(..., ge=0),
    top: int = Query(..., ge=0),
    right: int = Query(..., gt=0),
    bottom: int = Query(..., gt=0)
):
    return await crop_image_controller(file, left, top, right, bottom)