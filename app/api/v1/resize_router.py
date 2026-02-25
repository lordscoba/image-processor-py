from fastapi import APIRouter, UploadFile, File, Query, Request
from app.controllers.image_transform_controller import (
    resize_image_controller,
)
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter(prefix="/images", tags=["Image Resizer"])


@router.post("/resize")
@limiter.limit(RATE_LIMIT)
async def resize_image(
    request: Request,
    file: UploadFile = File(...),
    width: int = Query(..., gt=0),
    height: int = Query(..., gt=0),
    keep_aspect: bool = Query(True)
):
    return await resize_image_controller(file, width, height, keep_aspect)