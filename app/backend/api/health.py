"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.backend.config import APP_VERSION
from app.backend.models import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Service liveness check")
async def health() -> HealthResponse:
    return HealthResponse(version=APP_VERSION)
