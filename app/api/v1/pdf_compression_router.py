from fastapi import APIRouter, Query, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.pdf_compression_controller import compress_pdf_controller, compress_pdf_pro_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()

@router.post("/compress-pdf")
@limiter.limit(RATE_LIMIT)
async def compress_pdf(
    request: Request,
    file: UploadFile = File(...),
    compression_level: str = Query("medium"),
    db: AsyncSession = Depends(get_db)
):
    return await compress_pdf_controller(
        file=file,
        compression_level=compression_level,
        request=request,
        db=db
    )

@router.post("/compress-pdf/pro")
@limiter.limit(RATE_LIMIT)
async def compress_pdf_pro(
    request: Request,
    file: UploadFile = File(...),
    quality: int = Query(70),  # JPEG quality
    dpi: int = Query(150),     # target DPI
    db: AsyncSession = Depends(get_db)
):
    return await compress_pdf_pro_controller(
        file=file,
        quality=quality,
        dpi=dpi,
        request=request,
        db=db
    )