from fastapi import APIRouter
from app.api.v1.converter_router import router as converter_router
from app.api.v1.optimizer_router import router as optimizer_router
from app.api.v1.analyzer_router import router as analyzer_router
from app.api.v1.background_router import router as background_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(converter_router, tags=["Image Converter"])
api_router.include_router(optimizer_router, tags=["Image Optimizer"])
api_router.include_router(analyzer_router, tags=["Image Analyzer"])
api_router.include_router(background_router, tags=["Background Removal"])
