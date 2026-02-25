from fastapi import APIRouter, UploadFile, File, Request
from app.controllers.svg_optimizer_controller import optimize_svg_controller
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()

@router.post("/optimize-svg")
@limiter.limit(RATE_LIMIT)
async def optimize_svg(
    request: Request,
    file: UploadFile = File(...)
):
    return await optimize_svg_controller(file)