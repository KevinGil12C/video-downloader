"""Download orchestration built on top of yt-dlp.

The service is deliberately thin and testable: every production call goes
through an injectable ``dl_builder`` (default ``yt_dlp.YoutubeDL``) so
tests can substitute a fake and never touch the network.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp  # type: ignore[import-untyped]

from app.backend.config import get_settings
from app.backend.security import is_safe_url

KIND_VIDEO = "video"
KIND_AUDIO = "audio"
ALLOWED_KINDS = {KIND_VIDEO, KIND_AUDIO}
ALLOWED_QUALITIES = {"best", "2160", "1440", "1080", "720", "480", "360", "240"}

ProgressHook = Callable[[dict[str, Any]], None]
DLBuilder = Callable[[dict[str, Any]], Any]


class DownloaderError(Exception):
    """Base error raised by the download service."""


class UnsupportedURLError(DownloaderError):
    """The given URL failed security validation."""


class InvalidRequestError(DownloaderError):
    """Requested kind/quality values are not allowed."""


class ExtractionError(DownloaderError):
    """yt-dlp could not extract information about the URL."""


class DownloadError(DownloaderError):
    """The actual download failed."""


def format_selector(kind: str, quality: str) -> str:
    """Return the yt-dlp ``format`` selector for the requested combo."""
    if kind == KIND_AUDIO:
        return "bestaudio/best"
    if quality == "best":
        return "bestvideo*+bestaudio/best"
    return (
        f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
        f"/best[height<={quality}]"
    )


def validate_request(kind: str, quality: str) -> None:
    """Reject unsupported kind/quality values before a download starts."""
    if kind not in ALLOWED_KINDS:
        raise InvalidRequestError(f"Unknown kind: {kind!r}")
    if quality not in ALLOWED_QUALITIES:
        raise InvalidRequestError(f"Unknown quality: {quality!r}")


class DownloadService:
    """High-level operations over yt-dlp."""

    def __init__(
        self,
        downloads_dir: Path | None = None,
        dl_builder: DLBuilder = yt_dlp.YoutubeDL,
        ffmpeg_location: str | None = None,
    ) -> None:
        self.downloads_dir = downloads_dir or get_settings().downloads_dir
        self._dl_builder = dl_builder
        self.ffmpeg_location = ffmpeg_location

    def _base_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "outtmpl": "%(title)s [%(id)s].%(ext)s",
            "paths": {"home": str(self.downloads_dir)},
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "windowsfilenames": True,
        }
        if self.ffmpeg_location:
            options["ffmpeg_location"] = self.ffmpeg_location
        return options

    def _build(self, options: dict[str, Any]) -> Any:
        return self._dl_builder(options)

    def extract_metadata(self, url: str) -> dict[str, Any]:
        """Resolve metadata for ``url`` without downloading anything."""
        if not is_safe_url(url):
            raise UnsupportedURLError("URL rejected by security validation")
        options = self._base_options()
        options.update({"skip_download": True, "simulate": True})
        dl = self._build(options)
        try:
            info = dl.extract_info(url, download=False)
        except Exception as exc:
            raise ExtractionError(f"Failed to extract info: {exc}") from exc
        if not info:
            raise ExtractionError("yt-dlp returned no information")
        return {
            "id": info.get("id"),
            "title": info.get("title") or info.get("id"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "webpage_url": info.get("webpage_url") or url,
        }

    def download(
        self,
        url: str,
        *,
        kind: str = KIND_VIDEO,
        quality: str = "best",
        output_dir: Path | None = None,
        progress_hook: ProgressHook | None = None,
    ) -> Path:
        """Download the media at ``url`` and return the output file path."""
        if not is_safe_url(url):
            raise UnsupportedURLError("URL rejected by security validation")
        validate_request(kind, quality)

        output_dir = Path(output_dir) if output_dir else self.downloads_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        options = self._base_options()
        options["format"] = format_selector(kind, quality)
        if progress_hook is not None:
            options["progress_hooks"] = [progress_hook]
        if kind == KIND_AUDIO:
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        dl = self._build(options)
        try:
            info = dl.extract_info(url, download=True)
        except Exception as exc:
            raise DownloadError(f"Download failed: {exc}") from exc

        file_path = self._output_path(dl, info)
        if not file_path.exists():
            raise DownloadError(f"Output file not found: {file_path}")
        return file_path

    def _output_path(self, dl: Any, info: dict[str, Any]) -> Path:
        requested = info.get("requested_downloads")
        if requested:
            raw = requested[0].get("filepath")
            if raw:
                return Path(str(raw))
        return Path(dl.prepare_filename(info))
