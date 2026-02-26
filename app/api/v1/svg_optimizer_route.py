from fastapi import APIRouter, UploadFile, File, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.svg_optimizer_controller import optimize_svg_controller

router = APIRouter()


@router.post("/optimize-svg")
@limiter.limit(RATE_LIMIT)
async def optimize_svg(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_svg_controller(
        file=file,
        request=request,
        db=db
    )