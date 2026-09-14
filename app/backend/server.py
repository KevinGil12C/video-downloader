"""FastAPI application factory used by the desktop UI and the browser extension.

Run it with::

    python -m uvicorn app.backend.server:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.backend.api import downloads, health, info, ws
from app.backend.config import APP_VERSION, PROJECT_ROOT, get_settings
from app.backend.security import (
    RejectDisallowedOrigin,
    allowed_cors_origin_regex,
    allowed_cors_origins,
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    settings.ensure_dirs()

    application = FastAPI(
        title="Video Downloader Local API",
        description="Local video downloader backend for the desktop UI "
        "and the browser extension.",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url=None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_cors_origins(),
        allow_origin_regex=allowed_cors_origin_regex(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.add_middleware(
        RejectDisallowedOrigin,
        allowed_origins=allowed_cors_origins(),
    )

    application.include_router(health.router)
    application.include_router(info.router)
    application.include_router(downloads.router)
    application.include_router(ws.router)

    web_dir = PROJECT_ROOT / "web"
    if web_dir.is_dir():
        application.mount(
            "/",
            StaticFiles(directory=str(web_dir), html=True),
            name="web",
        )

    return application


app = create_app()
