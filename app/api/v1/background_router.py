# from fastapi import APIRouter, UploadFile, File, Request
# from app.controllers.background_controller import remove_background_controller
# from app.core.limiter import limiter
# from app.core.config import RATE_LIMIT

# router = APIRouter(prefix="/background")

# @router.post("/remove")
# @limiter.limit(RATE_LIMIT)
# async def remove_background(request: Request, file: UploadFile = File(...)):
#     return await remove_background_controller(file)