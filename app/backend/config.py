"""Central application configuration.

Values are read from environment variables (all optional) over sane
local defaults. The API only ever binds to 127.0.0.1.

Environment variables:

- ``VD_HOST``            host to bind (default ``127.0.0.1``)
- ``VD_PORT``            port to bind (default ``8000``)
- ``VD_DEBUG``           enable debug mode ("1"/"true"/"yes"/"on")
- ``VD_DOWNLOADS_DIR``   folder for downloaded files
- ``VD_LOGS_DIR``        folder for log files
- ``VD_ALLOWED_ORIGINS`` extra comma-separated CORS origins

A documented example lives in ``config.example.json``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_VERSION = "0.1.0"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    downloads_dir: Path = PROJECT_ROOT / "downloads"
    logs_dir: Path = PROJECT_ROOT / "logs"
    debug: bool = False
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS

    def ensure_dirs(self) -> None:
        """Create the folders the application writes to."""
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """Build a :class:`Settings` from environment variables."""
    downloads_dir = Path(os.getenv("VD_DOWNLOADS_DIR", str(PROJECT_ROOT / "downloads")))
    logs_dir = Path(os.getenv("VD_LOGS_DIR", str(PROJECT_ROOT / "logs")))

    allowed_origins = list(DEFAULT_ALLOWED_ORIGINS)
    if raw := os.getenv("VD_ALLOWED_ORIGINS"):
        allowed_origins.extend(
            origin.strip() for origin in raw.split(",") if origin.strip()
        )

    return Settings(
        host=os.getenv("VD_HOST", DEFAULT_HOST),
        port=_env_int("VD_PORT", DEFAULT_PORT),
        downloads_dir=downloads_dir,
        logs_dir=logs_dir,
        debug=_env_bool("VD_DEBUG", False),
        allowed_origins=tuple(allowed_origins),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton used by the application."""
    return load_settings()