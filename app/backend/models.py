"""Pydantic response models for the HTTP API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Service liveness check."""

    status: Literal["ok"] = "ok"
    version: str


class InfoResponse(BaseModel):
    """Environment details surfaced by ``GET /api/info``."""

    version: str
    yt_dlp_version: str | None
    ffmpeg_available: bool
    downloads_dir: str
    platform: str