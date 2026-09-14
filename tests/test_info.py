"""Tests for the /api/info endpoint with mocked dependencies."""

from importlib import metadata as importlib_metadata

from fastapi.testclient import TestClient

from app.backend.api import info as info_module
from app.backend.server import app

client = TestClient(app)

FAKE_VERSION = "ffmpeg version 7.1.1 Copyright (c) 2000-2024 the FFmpeg developers"


class FakeFFmpegService:
    def __init__(self, available: bool, version: str | None = None) -> None:
        self._available = available
        self._version = version

    def available(self) -> bool:
        return self._available

    def version(self) -> str | None:
        return self._version


def test_info_reports_full_environment(
    monkeypatch,
) -> None:
    monkeypatch.setattr(info_module.metadata, "version", lambda name: "2026.8.19")
    fake_service = FakeFFmpegService(True, FAKE_VERSION)
    monkeypatch.setattr(info_module, "get_ffmpeg_service", lambda: fake_service)

    response = client.get("/api/info")

    assert response.status_code == 200
    body = response.json()
    assert body["yt_dlp_version"] == "2026.8.19"
    assert body["ffmpeg_available"] is True
    assert body["ffmpeg_version"] == FAKE_VERSION
    assert isinstance(body["platform"], str)
    assert body["downloads_dir"].endswith("Downloads\\Video Downloader")


def test_info_reports_missing_ytdlp(monkeypatch) -> None:
    def raise_missing(_name: str) -> str:
        raise importlib_metadata.PackageNotFoundError

    monkeypatch.setattr(info_module.metadata, "version", raise_missing)

    body = client.get("/api/info").json()

    assert body["yt_dlp_version"] is None


def test_info_reports_ffmpeg_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        info_module, "get_ffmpeg_service", lambda: FakeFFmpegService(False)
    )

    body = client.get("/api/info").json()

    assert body["ffmpeg_available"] is False
    assert body["ffmpeg_version"] is None
