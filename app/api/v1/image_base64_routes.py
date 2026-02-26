from fastapi import APIRouter, UploadFile, File, Request, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.image_base64_controller import (
    image_to_base64_controller,
    base64_to_image_controller,
)

router = APIRouter(prefix="/images", tags=["Image Base64"])


@router.post("/to-base64")
@limiter.limit(RATE_LIMIT)
async def image_to_base64(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await image_to_base64_controller(
        file=file,
        request=request,
        db=db
    )


@router.post("/from-base64")
@limiter.limit(RATE_LIMIT)
async def base64_to_image(
    request: Request,
    base64_string: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    return await base64_to_image_controller(
        base64_string=base64_string,
        request=request,
        db=db
    )