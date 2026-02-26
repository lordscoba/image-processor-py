from fastapi import APIRouter, UploadFile, File, Request, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT
from app.controllers.optimizer_controller import (
    optimize_instagram_controller,
    optimize_seo_controller,
    optimize_twitter_controller,
    optimize_whatsapp_controller,
    optimize_web_controller,
    optimize_custom_controller,
    optimize_youtube_controller,
)

router = APIRouter(prefix="/optimize")


@router.post("/twitter")
@limiter.limit(RATE_LIMIT)
async def optimize_twitter(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_twitter_controller(file, request, db)


@router.post("/whatsapp")
@limiter.limit(RATE_LIMIT)
async def optimize_whatsapp(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_whatsapp_controller(file, request, db)


@router.post("/web")
@limiter.limit(RATE_LIMIT)
async def optimize_web(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_web_controller(file, request, db)


@router.post("/custom")
@limiter.limit(RATE_LIMIT)
async def optimize_custom(
    request: Request,
    file: UploadFile = File(...),
    target_kb: int = Query(None),
    quality: int = Query(85),
    resize_percent: int = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_custom_controller(
        file,
        target_kb,
        quality,
        resize_percent,
        request,
        db
    )


@router.post("/instagram")
@limiter.limit(RATE_LIMIT)
async def optimize_instagram(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_instagram_controller(file, request, db)


@router.post("/youtube-thumbnail")
@limiter.limit(RATE_LIMIT)
async def optimize_youtube(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_youtube_controller(file, request, db)


@router.post("/seo-responsive")
@limiter.limit(RATE_LIMIT)
async def optimize_seo(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await optimize_seo_controller(file, request, db)