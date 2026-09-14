"""Tests for app.services.ffmpeg.

Subprocess calls are mocked, so no external binary is executed unless a
machine actually has ffmpeg installed (integration test skipped otherwise).
"""

import subprocess
from pathlib import Path

import pytest

from app.services import ffmpeg
from app.services.ffmpeg import FFmpegService, ffmpeg_version, find_ffmpeg

FAKE_VERSION_LINE = (
    "ffmpeg version 6.1.1-full_build-www.gyan.dev"
    " Copyright (c) 2000-2024 the FFmpeg developers"
)


def fake_run(monkeypatch, *, returncode=0, stdout="", error=None):
    def _run(args, **kwargs):
        if error is not None:
            raise error
        return subprocess.CompletedProcess(
            args=args, returncode=returncode, stdout=stdout, stderr=""
        )

    monkeypatch.setattr(ffmpeg.subprocess, "run", _run)


def test_find_ffmpeg_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(ffmpeg.shutil, "which", lambda _name: None)
    assert find_ffmpeg() is None


def test_find_ffmpeg_finds_extra_path(monkeypatch, tmp_path):
    monkeypatch.setattr(ffmpeg.shutil, "which", lambda _name: None)
    binary_dir = tmp_path / "tools"
    binary_dir.mkdir()
    binary = binary_dir / "ffmpeg.exe"
    binary.write_bytes(b"MZ")

    result = find_ffmpeg([binary_dir])

    assert result == binary


def test_find_ffmpeg_falls_back_to_path(monkeypatch):
    fake_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    monkeypatch.setattr(ffmpeg.shutil, "which", lambda _name: fake_path)
    found = find_ffmpeg()
    assert str(found) == fake_path


def test_ffmpeg_version_parses_first_line(monkeypatch):
    fake_run(monkeypatch, stdout=FAKE_VERSION_LINE + "\n...")

    result = ffmpeg_version("ffmpeg")

    assert result == FAKE_VERSION_LINE


def test_ffmpeg_version_none_on_nonzero_exit(monkeypatch):
    fake_run(monkeypatch, returncode=1, stdout=FAKE_VERSION_LINE)

    assert ffmpeg_version("ffmpeg") is None


def test_ffmpeg_version_none_on_missing_binary(monkeypatch):
    fake_run(monkeypatch, error=FileNotFoundError("no binary"))

    assert ffmpeg_version(Path("missing/ffmpeg")) is None


def test_ffmpeg_version_none_on_timeout(monkeypatch):
    fake_run(monkeypatch, error=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=10))

    assert ffmpeg_version("ffmpeg") is None


def test_service_reports_unavailable_when_no_binary(monkeypatch):
    monkeypatch.setattr(ffmpeg, "find_ffmpeg", lambda *a, **k: None)
    service = FFmpegService()

    assert service.available() is False
    assert service.executable() is None
    assert service.version() is None


def test_service_reports_available_with_version(monkeypatch, tmp_path):
    binary = tmp_path / "ffmpeg.exe"
    binary.write_bytes(b"MZ")
    fake_run(monkeypatch, stdout=FAKE_VERSION_LINE + "\n...")
    service = FFmpegService(location=binary)

    assert service.available() is True
    assert service.executable() == str(binary)
    assert service.version() == FAKE_VERSION_LINE


@pytest.mark.skipif(
    not FFmpegService().available(),
    reason="ffmpeg not installed on this machine",
)
def test_integration_with_installed_ffmpeg():
    service = FFmpegService()
    version = service.version()
    assert version is not None
    assert version.startswith("ffmpeg version")
