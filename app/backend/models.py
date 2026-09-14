"""Pydantic models for the HTTP API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DownloadStatus = Literal[
    "pending", "downloading", "processing", "completed", "error", "cancelled"
]


class HealthResponse(BaseModel):
    """Service liveness check."""

    status: Literal["ok"] = "ok"
    version: str


class InfoResponse(BaseModel):
    """Environment details surfaced by ``GET /api/info``."""

    version: str
    yt_dlp_version: str | None
    ffmpeg_available: bool
    ffmpeg_version: str | None = None
    downloads_dir: str
    platform: str


class DownloadCreateRequest(BaseModel):
    """Payload for ``POST /api/downloads``."""

    url: str
    format: Literal["video", "audio"] = "video"
    quality: str = "best"
    directory: str | None = None


class DownloadResponse(BaseModel):
    """A download record exposed by the API."""

    id: str
    url: str
    format: Literal["video", "audio"]
    quality: str
    status: DownloadStatus = "pending"
    progress: float = Field(default=0.0, ge=0, le=100)
    file: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DownloadListResponse(BaseModel):
    """Currently tracked downloads, oldest first."""

    items: list[DownloadResponse]
