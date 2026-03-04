from fastapi import APIRouter, Query, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.image_dpi_controller import image_dpi_checker_controller, image_dpi_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()


@router.post("/image-dpi-changer")
@limiter.limit(RATE_LIMIT)
async def image_dpi_changer(
    request: Request,
    file: UploadFile = File(...),
    dpi: int = Query(300, ge=72, le=1200, description="Target DPI"),
    db: AsyncSession = Depends(get_db)
):
    return await image_dpi_controller(
        file=file,
        dpi=dpi,
        request=request,
        db=db
    )


@router.post("/image-dpi-checker")
@limiter.limit(RATE_LIMIT)
async def image_dpi_checker(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await image_dpi_checker_controller(
        file=file,
        request=request,
        db=db
    )