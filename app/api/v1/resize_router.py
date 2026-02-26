from fastapi import APIRouter, UploadFile, File, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.image_transform_controller import resize_image_controller

router = APIRouter(prefix="/images", tags=["Image Resizer"])


@router.post("/resize")
@limiter.limit(RATE_LIMIT)
async def resize_image(
    request: Request,
    file: UploadFile = File(...),
    width: int = Query(..., gt=0),
    height: int = Query(..., gt=0),
    keep_aspect: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    return await resize_image_controller(
        file=file,
        width=width,
        height=height,
        keep_aspect=keep_aspect,
        request=request,
        db=db
    )