from fastapi import APIRouter, UploadFile, File, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.image_transform_controller import crop_image_controller

router = APIRouter(prefix="/images", tags=["Image Cropper"])


@router.post("/crop")
@limiter.limit(RATE_LIMIT)
async def crop_image(
    request: Request,
    file: UploadFile = File(...),
    left: int = Query(..., ge=0),
    top: int = Query(..., ge=0),
    right: int = Query(..., gt=0),
    bottom: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    return await crop_image_controller(
        file=file,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        request=request,
        db=db
    )