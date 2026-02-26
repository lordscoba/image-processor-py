from fastapi import APIRouter, UploadFile, File, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.favicon_controller import generate_favicon_controller

router = APIRouter(prefix="/images", tags=["Favicon Generator"])


@router.post("/favicon")
@limiter.limit(RATE_LIMIT)
async def generate_favicon(
    request: Request,
    file: UploadFile = File(...),
    extension: str = Query("ico"),
    background: str = Query("transparent"),
    padding: int = Query(0, ge=0, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await generate_favicon_controller(
        file=file,
        extension=extension,
        background=background,
        padding=padding,
        request=request,
        db=db
    )