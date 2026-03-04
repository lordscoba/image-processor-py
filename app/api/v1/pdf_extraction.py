
from fastapi import APIRouter, Query, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.pdf_extraction_controller import extract_pdf_images_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()

@router.post("/extract-pdf-images")
@limiter.limit(RATE_LIMIT)
async def extract_pdf_images(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await extract_pdf_images_controller(
        file=file,
        request=request,
        db=db
    )