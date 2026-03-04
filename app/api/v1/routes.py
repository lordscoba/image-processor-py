from fastapi import APIRouter
from app.api.v1.sticker_router import router as sticker_router
from app.api.v1.video_gif_router import router as video_gif_router
from app.api.v1.password_generator_router import router as password_generator_router
from app.api.v1.image_dpi_router import router as image_dpi_router
from app.api.v1.exif_scrubber_router import router as exif_scrubber_router
from app.api.v1.watermark import  router as watermark
from app.api.v1.image_to_pdf_router import router as image_to_pdf_router
from app.api.v1.converter_router import router as converter_router
from app.api.v1.optimizer_router import router as optimizer_router
from app.api.v1.analyzer_router import router as analyzer_router
from app.api.v1.svg_optimizer_route import router as svg_optimizer_router
from app.api.v1.crop_router import router as crop_router
from app.api.v1.resize_router import router as resize_router
from app.api.v1.image_base64_routes import router as image_base64_routes
from app.api.v1.favicon_routes import router as favicon_router
from app.api.v1.pdf_compression_router import router as pdf_compression_router
from app.api.v1.heic_convert import router as heic_convert
from app.api.v1.pdf_extraction import router as pdf_extraction
from app.api.v1.image_color_effect_router import router as image_color_effect_router
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
api_router.include_router(pdf_compression_router, tags=["PDF Compressor"])
api_router.include_router(image_to_pdf_router, tags=["Image to PDF Converter"])
api_router.include_router(heic_convert, tags=["HEIC Converter"])
api_router.include_router(pdf_extraction, tags=["PDF Extractor"])
api_router.include_router(watermark, tags=["Watermark"])
api_router.include_router(image_color_effect_router, tags=["Image Color Effect"])
api_router.include_router(exif_scrubber_router, tags=["Exif Scrubber"])
api_router.include_router(image_dpi_router, tags=["Image DPI Changer"])
api_router.include_router(password_generator_router, tags=["Password Generator"])
api_router.include_router(video_gif_router, tags=["Video to GIF Converter"])
api_router.include_router(sticker_router, tags=["Sticker Generator"])

# api_router.include_router(background_router, tags=["Background Removal"])
