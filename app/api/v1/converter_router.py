from fastapi import APIRouter, UploadFile, File, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.converter_controller import convert_controller

router = APIRouter()


@router.post("/convert")
@limiter.limit(RATE_LIMIT)
async def convert(
    request: Request,
    file: UploadFile = File(...),
    target_format: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    return await convert_controller(
        file=file,
        target_format=target_format,
        request=request,
        db=db
    )