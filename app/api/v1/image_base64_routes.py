from fastapi import APIRouter, UploadFile, File, Request, Body
from app.controllers.image_base64_controller import (
    image_to_base64_controller,
    base64_to_image_controller,
)
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter(prefix="/images", tags=["Image Base64 Tools"])


@router.post("/to-base64")
@limiter.limit(RATE_LIMIT)
async def image_to_base64(
    request: Request,
    file: UploadFile = File(...)
):
    return await image_to_base64_controller(file)


@router.post("/from-base64")
@limiter.limit(RATE_LIMIT)
async def base64_to_image(
    request: Request,
    base64_string: str = Body(...)
):
    return await base64_to_image_controller(base64_string)