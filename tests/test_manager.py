"""Tests for app.services.manager (the download manager).

yt-dlp is replaced with scripted fakes, so these tests never download real
media or touch the network.
"""

import asyncio
import threading
from pathlib import Path

import pytest

from app.services.downloader import InvalidRequestError, UnsupportedURLError
from app.services.manager import (
    DownloadManager,
    DownloadNotCancellableError,
    DownloadNotDeletableError,
    DownloadNotFoundError,
)

SAFE_URL = "https://example.com/watch?v=abc123"


def completed_info(file_path: Path) -> dict:
    """yt-dlp style info dict pointing at an existing output file."""
    return {
        "id": "x1",
        "title": "T",
        "ext": "mp4",
        "requested_downloads": [{"filepath": str(file_path)}],
    }


def make_fake(dl):
    """dl_builder that stores options on the fake and returns it."""

    def builder(options: dict):
        dl.options = options
        return dl

    return builder


class FakeDL:
    """Minimal yt-dlp stand-in that invokes progress hooks synchronously."""

    def __init__(
        self, info: dict | None = None, error: Exception | None = None
    ) -> None:
        self.options: dict = {}
        self.info = info
        self.error = error

    def extract_info(self, url: str, download: bool = False) -> dict:
        for hook in self.options.get("progress_hooks", []):
            hook({"_percent_str": "0.0%"})
        if self.error is not None:
            raise self.error
        return self.info or {"id": "x1", "title": "T", "ext": "mp4"}

    def prepare_filename(self, info: dict) -> str:
        title = info.get("title") or "video"
        return str(Path("downloads") / f"{title}.{info.get('ext', 'mp4')}")


class HangingDL(FakeDL):
    """Fake that blocks mid-download until told to proceed."""

    def __init__(self, info: dict | None = None) -> None:
        super().__init__(info=info)
        self.proceed = threading.Event()

    def extract_info(self, url: str, download: bool = False) -> dict:
        for hook in self.options.get("progress_hooks", []):
            hook({"_percent_str": "0.0%"})
        self.proceed.wait(timeout=5)
        for hook in self.options.get("progress_hooks", []):
            hook({"_percent_str": "100.0%"})
        return self.info


class FileDL:
    """Fake that serves pre-built infos one at a time and tracks overlap."""

    def __init__(self, infos: list[dict]) -> None:
        self.options: dict = {}
        self._infos = list(infos)
        self._active = 0
        self.max_concurrent = 0

    def extract_info(self, url: str, download: bool = False) -> dict:
        self._active += 1
        self.max_concurrent = max(self.max_concurrent, self._active)
        for hook in self.options.get("progress_hooks", []):
            hook({"_percent_str": "0.0%"})
        info = self._infos.pop(0)
        self._active -= 1
        return info

    def prepare_filename(self, info: dict) -> str:
        return "T.mp4"


def test_list_empty() -> None:
    manager = DownloadManager(dl_builder=make_fake(FakeDL()))
    assert manager.list() == []


def test_get_missing_returns_none() -> None:
    manager = DownloadManager(dl_builder=make_fake(FakeDL()))
    assert manager.get("missing") is None


def test_create_and_complete(tmp_path: Path) -> None:
    out_file = tmp_path / "T.mp4"
    out_file.write_bytes(b"data")
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(FakeDL(info=completed_info(out_file))),
    )

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        assert record.status == "pending"
        await manager.wait_all()
        final = manager.get(record.id)
        assert final is not None
        assert final.status == "completed"
        assert final.file == "T.mp4"
        assert final.progress == 100.0
        assert final.error_message is None

    asyncio.run(run())


def test_download_failure_records_error(tmp_path: Path) -> None:
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(FakeDL(error=RuntimeError("boom"))),
    )

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        await manager.wait_all()
        final = manager.get(record.id)
        assert final is not None
        assert final.status == "error"
        assert "boom" in (final.error_message or "")

    asyncio.run(run())


def test_cancel_mid_download(tmp_path: Path) -> None:
    out_file = tmp_path / "T.mp4"
    out_file.write_bytes(b"data")
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(HangingDL(info=completed_info(out_file))),
    )

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        await asyncio.sleep(0.01)
        assert manager.get(record.id).status == "downloading"
        manager.cancel(record.id)
        await manager.wait_all()
        final = manager.get(record.id)
        assert final.status == "cancelled"

    asyncio.run(run())


def test_cancel_immediately_before_task_started(tmp_path: Path) -> None:
    manager = DownloadManager(downloads_dir=tmp_path, dl_builder=make_fake(FakeDL()))

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        manager.cancel(record.id)
        await manager.wait_all()
        assert manager.get(record.id).status == "cancelled"

    asyncio.run(run())


def test_cancel_completed_raises(tmp_path: Path) -> None:
    out_file = tmp_path / "T.mp4"
    out_file.write_bytes(b"data")
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(FakeDL(info=completed_info(out_file))),
    )

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        await manager.wait_all()
        with pytest.raises(DownloadNotCancellableError):
            manager.cancel(record.id)

    asyncio.run(run())


def test_cancel_missing_raises() -> None:
    manager = DownloadManager(dl_builder=make_fake(FakeDL()))
    with pytest.raises(DownloadNotFoundError):
        manager.cancel("missing")


def test_delete_completed_removes_record_and_file(tmp_path: Path) -> None:
    out_file = tmp_path / "T.mp4"
    out_file.write_bytes(b"data")
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(FakeDL(info=completed_info(out_file))),
    )

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        await manager.wait_all()
        manager.delete(record.id)
        assert manager.get(record.id) is None
        assert not out_file.exists()

    asyncio.run(run())


def test_delete_active_raises(tmp_path: Path) -> None:
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(HangingDL(info=completed_info(tmp_path / "T.mp4"))),
    )

    async def run() -> None:
        record = await manager.create(SAFE_URL)
        await asyncio.sleep(0.01)
        with pytest.raises(DownloadNotDeletableError):
            manager.delete(record.id)
        manager.cancel(record.id)
        await manager.wait_all()

    asyncio.run(run())


def test_create_rejects_bad_kind() -> None:
    manager = DownloadManager(dl_builder=make_fake(FakeDL()))

    async def run() -> None:
        with pytest.raises(InvalidRequestError):
            await manager.create(SAFE_URL, kind="app")
        assert manager.list() == []

    asyncio.run(run())


def test_create_rejects_unsafe_url() -> None:
    manager = DownloadManager(dl_builder=make_fake(FakeDL()))

    async def run() -> None:
        with pytest.raises(UnsupportedURLError):
            await manager.create("ftp://example.com/video")
        assert manager.list() == []

    asyncio.run(run())


def test_create_rejects_unsafe_directory() -> None:
    manager = DownloadManager(dl_builder=make_fake(FakeDL()))

    async def run() -> None:
        with pytest.raises(InvalidRequestError):
            await manager.create(SAFE_URL, directory="../../escape")
        assert manager.list() == []

    asyncio.run(run())


def test_list_ordered_oldest_first(tmp_path: Path) -> None:
    infos = [completed_info(tmp_path / f"T{i}.mp4") for i in range(3)]
    for path in (tmp_path / "T0.mp4", tmp_path / "T1.mp4", tmp_path / "T2.mp4"):
        path.write_bytes(b"data")
    manager = DownloadManager(
        downloads_dir=tmp_path, dl_builder=make_fake(FileDL(infos))
    )

    async def run() -> None:
        records = [await manager.create(SAFE_URL) for _ in range(3)]
        await manager.wait_all()
        ids = [record.id for record in manager.list()]
        assert ids == [record.id for record in records]
        assert all(record.status == "completed" for record in manager.list())

    asyncio.run(run())


def test_max_concurrent_limits_parallel_runs(tmp_path: Path) -> None:
    infos = [completed_info(tmp_path / f"T{i}.mp4") for i in range(3)]
    for i in range(3):
        (tmp_path / f"T{i}.mp4").write_bytes(b"data")
    dl = FileDL(infos)
    manager = DownloadManager(
        downloads_dir=tmp_path,
        dl_builder=make_fake(dl),
        max_concurrent=1,
    )

    async def run() -> None:
        records = [await manager.create(SAFE_URL) for _ in range(3)]
        await manager.wait_all()
        assert dl.max_concurrent == 1
        assert all(manager.get(record.id).status == "completed" for record in records)

    asyncio.run(run())
