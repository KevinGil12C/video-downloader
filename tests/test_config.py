"""Tests for app.backend.config settings loading and host validation."""

import os
from pathlib import Path
from unittest import mock

import pytest

from app.backend.config import Settings, load_settings, validate_host


def test_load_settings_defaults() -> None:
    for key in (
        "VD_HOST",
        "VD_PORT",
        "VD_DEBUG",
        "VD_DOWNLOADS_DIR",
        "VD_LOGS_DIR",
        "VD_ALLOWED_ORIGINS",
    ):
        os.environ.pop(key, None)
    settings = load_settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.debug is False
    assert settings.downloads_dir.name == "downloads"


def test_invalid_port_falls_back_to_default() -> None:
    with mock.patch.dict(os.environ, {"VD_PORT": "not-a-number"}):
        assert load_settings().port == 8000


def test_debug_environments_are_parsed() -> None:
    with mock.patch.dict(os.environ, {"VD_DEBUG": "1"}):
        assert load_settings().debug is True
    with mock.patch.dict(os.environ, {"VD_DEBUG": "off"}):
        assert load_settings().debug is False


def test_extra_allowed_origins_are_parsed() -> None:
    with mock.patch.dict(
        os.environ,
        {"VD_ALLOWED_ORIGINS": "http://localhost:5173, http://127.0.0.1:9000"},
    ):
        origins = load_settings().allowed_origins
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:9000" in origins


def test_downloads_and_logs_directories_from_env(tmp_path: Path) -> None:
    with mock.patch.dict(
        os.environ,
        {
            "VD_DOWNLOADS_DIR": str(tmp_path / "d"),
            "VD_LOGS_DIR": str(tmp_path / "l"),
        },
    ):
        settings = load_settings()
    assert settings.downloads_dir == tmp_path / "d"
    assert settings.logs_dir == tmp_path / "l"


def test_ensure_dirs_creates_folders(tmp_path: Path) -> None:
    settings = Settings(
        downloads_dir=tmp_path / "downloads",
        logs_dir=tmp_path / "logs",
    )
    settings.ensure_dirs()
    assert (tmp_path / "downloads").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_validate_host_accepts_loopback_only() -> None:
    for host in ("127.0.0.1", "localhost", "::1"):
        validate_host(host)
    for host in ("0.0.0.0", "::", "192.168.1.10", "my-desktop.home"):
        with pytest.raises(ValueError, match="loopback"):
            validate_host(host)
