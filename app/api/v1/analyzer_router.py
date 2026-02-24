from fastapi import APIRouter, UploadFile, File, Request
from app.controllers.analyzer_controller import analyze_controller
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter(prefix="/analyze")

@router.post("/")
@limiter.limit(RATE_LIMIT)
async def analyze_image(request: Request, file: UploadFile = File(...)):
    return await analyze_controller(file)