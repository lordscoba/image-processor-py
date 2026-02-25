from fastapi import APIRouter
from app.api.v1.converter_router import router as converter_router
from app.api.v1.optimizer_router import router as optimizer_router
from app.api.v1.analyzer_router import router as analyzer_router
from app.api.v1.svg_optimizer_route import router as svg_optimizer_router
from app.api.v1.crop_router import router as crop_router
from app.api.v1.resize_router import router as resize_router
from app.api.v1.image_base64_routes import router as image_base64_routes
from app.api.v1.favicon_routes import router as favicon_router
# from app.api.v1.background_router import router as background_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(converter_router, tags=["Image Converter"])
api_router.include_router(optimizer_router, tags=["Image Optimizer"])
api_router.include_router(analyzer_router, tags=["Image Analyzer"])
api_router.include_router(svg_optimizer_router, tags=["SVG Optimizer"])
api_router.include_router(crop_router, tags=["Image Cropper"])
api_router.include_router(resize_router, tags=["Image Resizer"])
api_router.include_router(image_base64_routes, tags=["Image Base64"])
api_router.include_router(favicon_router, tags=["Favicon Generator"])
# api_router.include_router(background_router, tags=["Background Removal"])
