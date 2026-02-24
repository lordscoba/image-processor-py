from fastapi import APIRouter, UploadFile, File, Request, Query
from app.controllers.optimizer_controller import (
    optimize_instagram_controller,
    optimize_seo_controller,
    optimize_twitter_controller,
    optimize_whatsapp_controller,
    optimize_web_controller,
    optimize_custom_controller,
    optimize_youtube_controller,
)
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter(prefix="/optimize")

@router.post("/twitter")
@limiter.limit(RATE_LIMIT)
async def optimize_twitter(request: Request, file: UploadFile = File(...)):
    return await optimize_twitter_controller(file)

@router.post("/whatsapp")
@limiter.limit(RATE_LIMIT)
async def optimize_whatsapp(request: Request, file: UploadFile = File(...)):
    return await optimize_whatsapp_controller(file)

@router.post("/web")
@limiter.limit(RATE_LIMIT)
async def optimize_web(request: Request, file: UploadFile = File(...)):
    return await optimize_web_controller(file)

@router.post("/custom")
@limiter.limit(RATE_LIMIT)
async def optimize_custom(
    request: Request,
    file: UploadFile = File(...),
    target_kb: int = Query(None),
    quality: int = Query(85),
    resize_percent: int = Query(None),
):
    return await optimize_custom_controller(file, target_kb, quality, resize_percent)

@router.post("/instagram")
@limiter.limit(RATE_LIMIT)
async def optimize_instagram(request: Request, file: UploadFile = File(...)):
    return await optimize_instagram_controller(file)

@router.post("/youtube-thumbnail")
@limiter.limit(RATE_LIMIT)
async def optimize_youtube(request: Request, file: UploadFile = File(...)):
    return await optimize_youtube_controller(file)

@router.post("/seo-responsive")
@limiter.limit(RATE_LIMIT)
async def optimize_seo(request: Request, file: UploadFile = File(...)):
    return await optimize_seo_controller(file)