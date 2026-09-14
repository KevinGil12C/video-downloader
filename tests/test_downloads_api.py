"""HTTP contract tests for the /api/downloads endpoints.

The default manager dependency is swapped for a scripted stub, so nothing is
ever downloaded over the network.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.backend.security import is_safe_url
from app.backend.server import app
from app.services.downloader import UnsupportedURLError, validate_request
from app.services.manager import (
    DownloadNotCancellableError,
    DownloadNotDeletableError,
    DownloadNotFoundError,
    DownloadRecord,
    default_manager,
)

SAFE_URL = "https://example.com/watch?v=abc123"


class StubManager:
    """In-memory stand-in mirroring DownloadManager's public surface."""

    def __init__(self) -> None:
        self._records: dict[str, DownloadRecord] = {}
        self._counter = 0

    async def create(
        self,
        url: str,
        *,
        kind: str = "video",
        quality: str = "best",
        directory: str | None = None,
    ) -> DownloadRecord:
        if not is_safe_url(url):
            raise UnsupportedURLError("URL rejected by security validation")
        validate_request(kind, quality)
        self._counter += 1
        record = DownloadRecord(
            id=f"dl-{self._counter}",
            url=url,
            kind=kind,
            quality=quality,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        record.status = "completed"
        record.progress = 100.0
        record.file = "sample.mp4"
        self._records[record.id] = record
        return record

    def list(self) -> list[DownloadRecord]:
        return sorted(self._records.values(), key=lambda r: r.created_at)

    def get(self, download_id: str) -> DownloadRecord | None:
        return self._records.get(download_id)

    def cancel(self, download_id: str) -> DownloadRecord:
        record = self._get_or_raise(download_id)
        if record.status in {"completed", "error"}:
            raise DownloadNotCancellableError(download_id)
        record.status = "cancelled"
        return record

    def delete(self, download_id: str) -> None:
        record = self._get_or_raise(download_id)
        if record.status in {"pending", "downloading", "processing"}:
            raise DownloadNotDeletableError(download_id)
        del self._records[download_id]

    def _get_or_raise(self, download_id: str) -> DownloadRecord:
        record = self._records.get(download_id)
        if record is None:
            raise DownloadNotFoundError(download_id)
        return record


def make_record(download_id: str, status: str = "completed") -> DownloadRecord:
    return DownloadRecord(
        id=download_id,
        url=SAFE_URL,
        kind="video",
        quality="best",
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def client() -> None:
    stub = StubManager()
    app.dependency_overrides[default_manager] = lambda: stub
    with TestClient(app) as test_client:
        test_client.stub = stub  # type: ignore[attr-defined]
        yield test_client
    app.dependency_overrides.pop(default_manager, None)


def test_create_download_201(client) -> None:
    response = client.post(
        "/api/downloads",
        json={"url": SAFE_URL, "format": "video", "quality": "best"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("dl-")
    assert body["status"] == "completed"
    assert body["format"] == "video"
    assert body["progress"] == 100.0
    assert body["file"] == "sample.mp4"


def test_create_download_invalid_url_400(client) -> None:
    response = client.post(
        "/api/downloads",
        json={"url": "ftp://example.com/video"},
    )
    assert response.status_code == 400
    assert "security validation" in response.json()["detail"]


def test_create_download_invalid_kind_400(client) -> None:
    response = client.post(
        "/api/downloads",
        json={"url": SAFE_URL, "format": "app"},
    )
    assert response.status_code == 422


def test_list_downloads_empty(client) -> None:
    response = client.get("/api/downloads")
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_downloads_returns_items(client) -> None:
    client.stub._records["d1"] = make_record("d1")
    response = client.get("/api/downloads")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == ["d1"]
    assert items[0]["url"] == SAFE_URL


def test_get_download(client) -> None:
    client.stub._records["d1"] = make_record("d1")
    response = client.get("/api/downloads/d1")
    assert response.status_code == 200
    assert response.json()["id"] == "d1"


def test_get_download_not_found(client) -> None:
    response = client.get("/api/downloads/missing")
    assert response.status_code == 404


def test_cancel_download(client) -> None:
    client.stub._records["d1"] = make_record("d1", status="downloading")
    response = client.post("/api/downloads/d1/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_finished_download_400(client) -> None:
    client.stub._records["d1"] = make_record("d1", status="completed")
    response = client.post("/api/downloads/d1/cancel")
    assert response.status_code == 400


def test_cancel_download_not_found(client) -> None:
    response = client.post("/api/downloads/missing/cancel")
    assert response.status_code == 404


def test_delete_download_204(client) -> None:
    client.stub._records["d1"] = make_record("d1")
    response = client.delete("/api/downloads/d1")
    assert response.status_code == 204
    assert client.stub.get("d1") is None


def test_delete_active_download_409(client) -> None:
    client.stub._records["d1"] = make_record("d1", status="downloading")
    response = client.delete("/api/downloads/d1")
    assert response.status_code == 409


def test_delete_download_not_found(client) -> None:
    response = client.delete("/api/downloads/missing")
    assert response.status_code == 404
