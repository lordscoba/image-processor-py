from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from app.core.limiter import limiter
from app.api.v1.routes import api_router
from app.core.logging import setup_logging
from app.core.monitoring import router as monitoring_router

setup_logging()

app = FastAPI(title="Image Format Converter API")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router)
app.include_router(monitoring_router)