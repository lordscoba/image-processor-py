from fastapi.responses import JSONResponse
from fastapi import Request

async def http_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )