from fastapi import APIRouter, Query, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.controllers.image_to_pdf_controller import image_to_pdf_controller, pdf_to_image_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()


@router.post("/image-to-pdf")
@limiter.limit(RATE_LIMIT)
async def image_to_pdf(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await image_to_pdf_controller(
        file=file,
        request=request,
        db=db
    )


@router.post("/pdf-to-image")
@limiter.limit(RATE_LIMIT)
async def pdf_to_image(
    request: Request,
    file: UploadFile = File(...),
    format: str = Query("png", enum=["png", "jpg"]),
    db: AsyncSession = Depends(get_db)
):
    return await pdf_to_image_controller(
        file=file,
        format=format,
        request=request,
        db=db
    )