from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from app.core.limiter import limiter
from app.api.v1.routes import api_router
from app.core.logging import setup_logging
from app.core.monitoring import router as monitoring_router
from app.core.cors import setup_cors

setup_logging()

app = FastAPI(title="Image Format Converter API")

# -----------------------------
# MIDDLEWARES
# -----------------------------

setup_cors(app) 

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# -----------------------------
# ROUTERS
# -----------------------------

app.include_router(api_router)
app.include_router(monitoring_router)