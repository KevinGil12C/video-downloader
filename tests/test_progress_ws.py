"""End-to-end test of the /ws/progress WebSocket stream.

The default manager and hub are replaced with fakes, so no media is ever
downloaded over the network.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.backend.api.ws import get_progress_hub
from app.backend.server import app
from app.services.manager import DownloadManager, default_manager
from app.services.progress import ProgressHub

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


class HangingProgressDL:
    """Fake that pauses mid-download so the stream can be observed."""

    def __init__(self, info: dict) -> None:
        self.options: dict = {}
        self.proceed = threading.Event()
        self._info = info

    def extract_info(self, url: str, download: bool = False) -> dict:
        for hook in self.options.get("progress_hooks", []):
            hook(
                {
                    "_percent_str": "0.0%",
                    "speed": 1.5 * 1024 * 1024,
                    "eta": 90,
                }
            )
        self.proceed.wait(timeout=5)
        for hook in self.options.get("progress_hooks", []):
            hook(
                {
                    "_percent_str": "100.0%",
                    "speed": 1.5 * 1024 * 1024,
                    "eta": 0,
                }
            )
        return self._info

    def prepare_filename(self, info: dict) -> str:
        return str(Path("downloads") / "T.mp4")


@pytest.fixture
def setup(tmp_path: Path):
    out_file = tmp_path / "T.mp4"
    out_file.write_bytes(b"data")
    dl = HangingProgressDL(info=completed_info(out_file))
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(dl),
        max_concurrent=1,
    )
    hub = ProgressHub(manager=manager)
    app.dependency_overrides[default_manager] = lambda: manager
    app.dependency_overrides[get_progress_hub] = lambda: hub
    yield manager, hub, dl
    app.dependency_overrides.pop(default_manager, None)
    app.dependency_overrides.pop(get_progress_hub, None)


def test_progress_ws_streams_lifecycle(setup, tmp_path: Path) -> None:
    manager, hub, dl = setup
    with TestClient(app) as client:
        create = client.post(
            "/api/downloads",
            json={"url": SAFE_URL, "format": "video", "quality": "best"},
        )
        assert create.status_code == 201
        download_id = create.json()["id"]

        with client.websocket_connect("/ws/progress") as websocket:
            dl.proceed.set()
            statuses: list[str] = []
            while "completed" not in statuses:
                event = websocket.receive_json()
                statuses.append(event["status"])
                assert event["download_id"] == download_id

        assert "downloading" in statuses
        assert "completed" in statuses
        assert hub._sockets == set()  # noqa: SLF001
        assert manager.get(download_id).status == "completed"
