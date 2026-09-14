"""Environment information endpoint."""
from __future__ import annotations

import shutil
import sys
from importlib import metadata

from fastapi import APIRouter

from app.backend.config import APP_VERSION, get_settings
from app.backend.models import InfoResponse

router = APIRouter(prefix="/api/info", tags=["info"])


def yt_dlp_version() -> str | None:
    """Return the installed yt-dlp version, if available."""
    try:
        return metadata.version("yt-dlp")
    except metadata.PackageNotFoundError:
        return None


@router.get("", response_model=InfoResponse, summary="Environment information")
async def info() -> InfoResponse:
    settings = get_settings()
    return InfoResponse(
        version=APP_VERSION,
        yt_dlp_version=yt_dlp_version(),
        ffmpeg_available=shutil.which("ffmpeg") is not None,
        downloads_dir=str(settings.downloads_dir),
        platform=sys.platform,
    )