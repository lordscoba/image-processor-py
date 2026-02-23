from fastapi import APIRouter, UploadFile, File, Query, Request
from app.controllers.converter_controller import convert_controller
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()

@router.post("/convert")
@limiter.limit(RATE_LIMIT)
async def convert(
    request: Request,
    file: UploadFile = File(...),
    target_format: str = Query(...)
):
    return await convert_controller(file, target_format)