from fastapi import APIRouter, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.exif_scrubber_controller import exif_scrubber_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()


@router.post("/exif-scrubber")
@limiter.limit(RATE_LIMIT)
async def exif_scrubber(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await exif_scrubber_controller(
        file=file,
        request=request,
        db=db
    )