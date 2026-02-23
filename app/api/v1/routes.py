from fastapi import APIRouter
from app.api.v1.converter_router import router as converter_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(converter_router, tags=["Image Converter"])