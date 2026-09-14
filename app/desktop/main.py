"""Desktop entry point: boots the local API and opens the Eel window.

Run with ``python -m app.desktop.main`` from the project root (this is what
``scripts\\start.bat`` does in desktop mode). The Eel window loads the UI from
``web/`` and talks to the FastAPI backend over the localhost HTTP/WebSocket
API.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Literal

import eel
import uvicorn

from app.backend.config import APP_VERSION, PROJECT_ROOT, get_settings
from app.backend.server import app as backend_app

logger = logging.getLogger("app.desktop")

WEB_DIR = PROJECT_ROOT / "web"
WINDOW_SIZE = (1200, 760)


class UvicornThread:
    """Runs the FastAPI application in a background daemon thread."""

    def __init__(self, host: str, port: int) -> None:
        self._server = uvicorn.Server(
            uvicorn.Config(backend_app, host=host, port=port, log_level="warning")
        )
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self) -> None:
        """Start serving and wait until the socket actually binds."""
        self._thread.start()
        deadline = time.monotonic() + 10
        while not self._server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if not self._server.started:
            raise RuntimeError("API server failed to start")

    def stop(self) -> None:
        """Ask uvicorn to exit and join the thread."""
        self._server.should_exit = True
        self._thread.join(timeout=5)


@eel.expose
def get_app_info() -> dict[str, Any]:
    """Info the UI can request from Python: version, API URL, platform."""
    settings = get_settings()
    return {
        "version": APP_VERSION,
        "api_url": f"http://127.0.0.1:{settings.port}",
        "platform": "Windows",
    }


def _browser_mode() -> str | Literal[False]:
    """Eel browser mode, overridable with ``VD_BROWSER`` (default Edge)."""
    raw = os.getenv("VD_BROWSER", "edge").strip().lower()
    if raw in {"false", "0", "none"}:
        return False
    return raw


def main() -> int:
    """Start the backend API and then open the Eel desktop window."""
    settings = get_settings()
    settings.ensure_dirs()

    logging.basicConfig(level=logging.INFO)

    api = UvicornThread(host=settings.host, port=settings.port)
    api.start()

    if not WEB_DIR.is_dir():
        api.stop()
        logger.error("Missing web UI folder: %s", WEB_DIR)
        return 1

    eel.init(str(WEB_DIR))
    try:
        eel.start(
            "index.html",
            mode=_browser_mode(),
            host=settings.host,
            port=settings.port + 1,
            size=WINDOW_SIZE,
            block=True,
        )
    finally:
        api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
