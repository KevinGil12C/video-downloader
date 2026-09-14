"""In-memory download manager orchestrating the download service.

Downloads are tracked as :class:`DownloadRecord` entries, run as background
asyncio tasks with a concurrency limit, and can be cancelled or removed from
history. All state is kept in memory (no persistence) so a restart clears the
queue, which is acceptable for a local single-user tool.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yt_dlp  # type: ignore[import-untyped]

from app.backend.security import is_safe_url
from app.services.downloader import (
    KIND_VIDEO,
    DLBuilder,
    DownloaderError,
    DownloadService,
    InvalidRequestError,
    UnsupportedURLError,
    validate_request,
)

CANCELLABLE_STATUSES = {"pending", "downloading", "processing"}


class DownloadManagerError(Exception):
    """Base error raised by the download manager."""


class DownloadNotFoundError(DownloadManagerError):
    """No record exists for the requested ID."""


class DownloadNotCancellableError(DownloadManagerError):
    """The download already finished and can no longer be cancelled."""


class DownloadNotDeletableError(DownloadManagerError):
    """The download is still active and cannot be removed from history."""


@dataclass
class DownloadRecord:
    """Mutable in-memory state for a single download."""

    id: str
    url: str
    kind: str
    quality: str
    status: str = "pending"
    progress: float = 0.0
    file: str | None = None
    speed: str | None = None
    eta: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    target_filepath: Path | None = None


class DownloadManager:
    """Creates, runs, cancels and forgets downloads."""

    def __init__(
        self,
        downloads_dir: Path | None = None,
        dl_builder: DLBuilder | None = None,
        ffmpeg_location: str | None = None,
        max_concurrent: int = 3,
        on_update: Callable[[DownloadRecord], None] | None = None,
    ) -> None:
        from app.backend.config import get_settings

        self._downloads_dir = downloads_dir or get_settings().downloads_dir
        self._ffmpeg_location = ffmpeg_location
        self._dl_builder = dl_builder or yt_dlp.YoutubeDL
        self._on_update = on_update
        self._downloads: dict[str, DownloadRecord] = {}
        self._tasks: set[asyncio.Task[None]] = set()
        self._semaphore = asyncio.Semaphore(max_concurrent)

    # -- Public query API -------------------------------------------------

    def list(self) -> list[DownloadRecord]:
        """Return all records, oldest first."""
        return sorted(self._downloads.values(), key=lambda r: r.created_at)

    def get(self, download_id: str) -> DownloadRecord | None:
        return self._downloads.get(download_id)

    # -- Lifecycle ---------------------------------------------------------

    async def create(
        self,
        url: str,
        *,
        kind: str = KIND_VIDEO,
        quality: str = "best",
        directory: str | None = None,
    ) -> DownloadRecord:
        """Validate a request, register it and start it in the background."""
        if not is_safe_url(url):
            raise UnsupportedURLError("URL rejected by security validation")
        validate_request(kind, quality)
        _reject_unsafe_directory(directory)

        record = DownloadRecord(
            id=uuid.uuid4().hex,
            url=url,
            kind=kind,
            quality=quality,
        )
        self._downloads[record.id] = record

        task = asyncio.create_task(self._run(record, directory=directory))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return record

    def cancel(self, download_id: str) -> DownloadRecord:
        """Signal a running download to stop and mark it cancelled."""
        record = self._get_or_raise(download_id)
        if record.status in CANCELLABLE_STATUSES:
            record.cancel_event.set()
            self._set_status(record, "cancelled")
            return record
        if record.status in {"completed", "error"}:
            raise DownloadNotCancellableError(download_id)
        return record

    def delete(self, download_id: str) -> None:
        """Forget a finished download (best-effort removes its file)."""
        record = self._get_or_raise(download_id)
        if record.status in CANCELLABLE_STATUSES:
            raise DownloadNotDeletableError(download_id)
        if record.target_filepath is not None:
            _unlink_if_exists(record.target_filepath)
        del self._downloads[download_id]

    # -- Internal ----------------------------------------------------------

    def _get_or_raise(self, download_id: str) -> DownloadRecord:
        record = self._downloads.get(download_id)
        if record is None:
            raise DownloadNotFoundError(download_id)
        return record

    async def _run(self, record: DownloadRecord, directory: str | None) -> None:
        async with self._semaphore:
            if record.cancel_event.is_set():
                self._set_status(record, "cancelled")
                return
            self._set_status(record, "downloading")

            downloads_dir = Path(directory) if directory else self._downloads_dir
            service = DownloadService(
                downloads_dir=downloads_dir,
                dl_builder=self._dl_builder,
                ffmpeg_location=self._ffmpeg_location,
            )

            def progress_hook(data: dict[str, Any]) -> None:
                if record.cancel_event.is_set():
                    raise RuntimeError("Cancelled by user")
                percent = _parse_percent(data.get("_percent_str"))
                if percent is not None:
                    record.progress = percent
                record.speed = _format_speed(data.get("_speed_str"), data.get("speed"))
                record.eta = _format_eta(data.get("_eta_str"), data.get("eta"))
                record.updated_at = datetime.now(timezone.utc)
                self._emit(record)

            try:
                file_path = await asyncio.to_thread(
                    service.download,
                    record.url,
                    kind=record.kind,
                    quality=record.quality,
                    output_dir=downloads_dir,
                    progress_hook=progress_hook,
                )
            except DownloaderError as exc:
                self._on_failure(record, exc)
                return
            except Exception as exc:
                self._on_failure(record, exc)
                return

            record.target_filepath = Path(file_path)
            record.file = Path(file_path).name
            record.progress = 100.0
            self._set_status(record, "completed")

    def _on_failure(self, record: DownloadRecord, exc: Exception) -> None:
        if record.cancel_event.is_set():
            self._set_status(record, "cancelled")
        else:
            record.error_message = str(exc)
            self._set_status(record, "error")

    def _set_status(self, record: DownloadRecord, status: str) -> None:
        record.status = status
        record.updated_at = datetime.now(timezone.utc)
        self._emit(record)

    def _emit(self, record: DownloadRecord) -> None:
        if self._on_update is not None:
            self._on_update(record)

    def set_update_listener(
        self, on_update: Callable[[DownloadRecord], None] | None
    ) -> None:
        """Replace the listener notified on every record change."""
        self._on_update = on_update

    async def wait_all(self) -> None:
        """Block until all scheduled downloads finish (used by tests)."""
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)


def _parse_percent(raw: Any) -> float | None:
    try:
        return float(str(raw).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None


_SPEED_UNITS = ("B/s", "KiB/s", "MiB/s", "GiB/s", "TiB/s")


def _format_speed(string_value: Any, raw_value: Any) -> str | None:
    """Return a human read speed string, preferring yt-dlp's own formatter."""
    if string_value:
        return str(string_value).strip()
    try:
        speed = float(raw_value)
    except (TypeError, ValueError):
        return None
    if speed < 0:
        return None
    size = speed
    for unit in _SPEED_UNITS:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PiB/s"


def _format_eta(string_value: Any, raw_value: Any) -> str | None:
    """Return an ``HH:MM:SS`` ETA string from a yt-dlp hook payload."""
    if string_value:
        return str(string_value).strip()
    try:
        seconds = int(raw_value)
    except (TypeError, ValueError):
        return None
    if seconds < 0:
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _reject_unsafe_directory(directory: str | None) -> None:
    if not directory:
        return
    path = Path(directory)
    if path.is_absolute() or ".." in path.parts:
        raise InvalidRequestError("Unsafe directory path")


def _unlink_if_exists(filepath: Path) -> None:
    with suppress(OSError):
        filepath.unlink()


_manager_memo: DownloadManager | None = None


def default_manager() -> DownloadManager:
    """Lazily built process-wide manager wired with the FFmpeg service."""
    global _manager_memo
    if _manager_memo is None:
        from app.services.ffmpeg import get_ffmpeg_service

        _manager_memo = DownloadManager(
            ffmpeg_location=get_ffmpeg_service().executable(),
        )
    return _manager_memo


async def wait_for_tasks() -> None:
    """Convenience used by CLI/test helpers to drain the default manager."""
    await default_manager().wait_all()
