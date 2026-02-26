from fastapi import APIRouter, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.analyzer_controller import analyze_controller

router = APIRouter(prefix="/analyze")

@router.post("/")
@limiter.limit(RATE_LIMIT)
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await analyze_controller(
        file=file,
        request=request,
        db=db
    )