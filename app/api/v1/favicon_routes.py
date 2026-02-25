from fastapi import APIRouter, UploadFile, File, Query, Request
from app.controllers.favicon_controller import generate_favicon_controller
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter(prefix="/images", tags=["Favicon Generator"])


@router.post("/favicon")
@limiter.limit(RATE_LIMIT)
async def generate_favicon(
    request: Request,
    file: UploadFile = File(...),
    extension: str = Query("ico"),
    background: str = Query("transparent"), #transparent , white , black , light , dark ,auto , contrast
    padding: int = Query(0, ge=0, le=200)
):
    return await generate_favicon_controller(
        file,
        extension,
        background,
        padding
    )