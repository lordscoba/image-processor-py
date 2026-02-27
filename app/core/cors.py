import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    """

    # Read allowed origins from environment variable
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,https://www.snappy-fix.com,https://snappy-fix.com",
    )

    origins = [origin.strip() for origin in allowed_origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["Content-Disposition"],  # Important for file downloads
    )