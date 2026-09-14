"""Environment information endpoint."""

from __future__ import annotations

import sys
from importlib import metadata

from fastapi import APIRouter, HTTPException, Query

from app.backend.config import APP_VERSION, get_settings
from app.backend.models import InfoResponse
from app.services.ffmpeg import get_ffmpeg_service
from app.services.downloader import DownloadService, DownloaderError

router = APIRouter(prefix="/api/info", tags=["info"])


def yt_dlp_version() -> str | None:
    """Return the installed yt-dlp version, if available."""
    try:
        return metadata.version("yt-dlp")
    except metadata.PackageNotFoundError:
        return None


@router.get("", response_model=InfoResponse, summary="Environment information")
async def info(url: str | None = Query(default=None)) -> InfoResponse:
    settings = get_settings()
    ffmpeg = get_ffmpeg_service()
    media = None
    if url:
        try:
            media = DownloadService(
                downloads_dir=settings.downloads_dir,
                ffmpeg_location=ffmpeg.executable(),
            ).extract_metadata(url)
        except DownloaderError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return InfoResponse(
        version=APP_VERSION,
        yt_dlp_version=yt_dlp_version(),
        ffmpeg_available=ffmpeg.available(),
        ffmpeg_version=ffmpeg.version(),
        downloads_dir=str(settings.downloads_dir),
        platform=sys.platform,
        media=media,
    )
