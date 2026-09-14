"""Tests for app.services.progress and the manager's update listener.

No real downloads or network access: yt-dlp is replaced with a fake.
"""

import asyncio
from pathlib import Path

from app.services.manager import (
    DownloadManager,
    DownloadRecord,
    _format_eta,
    _format_speed,
)
from app.services.progress import ProgressEvent, progress_event

SAFE_URL = "https://example.com/watch?v=abc123"


def completed_info(file_path: Path) -> dict:
    return {
        "id": "x1",
        "title": "T",
        "ext": "mp4",
        "requested_downloads": [{"filepath": str(file_path)}],
    }


def make_fake(dl):
    def builder(options: dict):
        dl.options = options
        return dl

    return builder


class ProgressDL:
    """Fake that reports progress, speed and ETA through the hooks."""

    def __init__(self, info: dict | None = None) -> None:
        self.options: dict = {}
        self.info = info

    def extract_info(self, url: str, download: bool = False) -> dict:
        for hook in self.options.get("progress_hooks", []):
            hook(
                {
                    "_percent_str": "42.0%",
                    "speed": 1.5 * 1024 * 1024,
                    "eta": 90,
                }
            )
        return self.info

    def prepare_filename(self, info: dict) -> str:
        return str(Path("downloads") / "T.mp4")


def test_format_speed_prefers_string_value() -> None:
    assert _format_speed("1.2 MiB/s", 99999999) == "1.2 MiB/s"


def test_format_speed_from_raw_bytes() -> None:
    assert _format_speed(None, 1.5 * 1024 * 1024) == "1.5 MiB/s"


def test_format_speed_missing_or_invalid() -> None:
    assert _format_speed(None, None) is None
    assert _format_speed(None, -1) is None
    assert _format_speed(None, "not-a-number") is None


def test_format_eta_prefers_string_value() -> None:
    assert _format_eta("00:01:30", 999999) == "00:01:30"


def test_format_eta_from_raw_seconds() -> None:
    assert _format_eta(None, 90) == "00:01:30"
    assert _format_eta(None, 3661) == "01:01:01"


def test_format_eta_missing_or_invalid() -> None:
    assert _format_eta(None, None) is None
    assert _format_eta(None, -5) is None
    assert _format_eta(None, "soon") is None


def test_progress_event_maps_record_fields() -> None:
    record = DownloadRecord(
        id="abc",
        url=SAFE_URL,
        kind="video",
        quality="best",
        status="downloading",
        progress=42.0,
        speed="1.5 MiB/s",
        eta="00:01:30",
    )
    event = progress_event(record)
    assert isinstance(event, ProgressEvent)
    assert event.download_id == "abc"
    assert event.status == "downloading"
    assert event.progress == 42.0
    assert event.speed == "1.5 MiB/s"
    assert event.eta == "00:01:30"


def test_progress_event_to_dict() -> None:
    event = ProgressEvent(download_id="abc", status="completed", progress=100.0)
    payload = event.to_dict()
    assert payload == {
        "download_id": "abc",
        "status": "completed",
        "progress": 100.0,
        "speed": None,
        "eta": None,
    }


def test_manager_listener_receives_lifecycle_events(tmp_path: Path) -> None:
    out_file = tmp_path / "T.mp4"
    out_file.write_bytes(b"data")
    events: list[tuple[str, float, str | None, str | None]] = []
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(ProgressDL(info=completed_info(out_file))),
        on_update=lambda record: events.append(
            (record.status, record.progress, record.speed, record.eta)
        ),
    )

    async def run() -> DownloadRecord:
        record = await manager.create(SAFE_URL)
        await manager.wait_all()
        return record

    record = asyncio.run(run())

    statuses = [event[0] for event in events]
    assert statuses[0] == "downloading"
    assert statuses[-1] == "completed"
    assert record.status == "completed"

    middle = next(event for event in events if event[1] == 42.0)
    assert middle[2] == "1.5 MiB/s"
    assert middle[3] == "00:01:30"


def test_set_update_listener_replaces_listener(tmp_path: Path) -> None:
    manager = DownloadManager(
        downloads_dir=tmp_path, dl_builder=make_fake(ProgressDL())
    )
    manager.set_update_listener(lambda record: None)
    assert manager._on_update is not None  # noqa: SLF001
