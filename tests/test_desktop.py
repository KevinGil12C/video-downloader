"""Tests for the Eel desktop shell (app.desktop.main).

``eel.start`` is monkeypatched so no browser window is ever opened, and the
API is booted on ephemeral ports only.
"""

import json
import socket
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import eel
import pytest
import uvicorn

from app.backend.config import APP_VERSION
from app.desktop.main import (
    UvicornThread,
    _browser_mode,
    get_app_info,
    main,
)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _http_json(port: int, path: str) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as resp:
        return resp.status, json.loads(resp.read())


def _wait_health_ok(port: int, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if _http_json(port, "/api/health")[0] == 200:
                return
        except Exception:
            pass
        time.sleep(0.05)
    raise AssertionError("API health check never returned 200")


def _wait_down(port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            _http_json(port, "/api/health")
        except Exception:
            return
        time.sleep(0.05)
    raise AssertionError("API server did not stop")


def test_get_app_info_reports_version_and_api_url() -> None:
    info = get_app_info()
    assert info["version"] == APP_VERSION
    assert info["api_url"].startswith("http://127.0.0.1:")
    assert info["platform"] == "Windows"


def test_browser_mode_defaults_to_edge() -> None:
    assert _browser_mode() == "edge"


def test_browser_mode_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for raw in ("false", "0", "none", "FALSE"):
        monkeypatch.setenv("VD_BROWSER", raw)
        assert _browser_mode() is False


def test_browser_mode_custom_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VD_BROWSER", "chrome")
    assert _browser_mode() == "chrome"


def test_uvicorn_thread_starts_and_stops() -> None:
    port = _free_port()
    api = UvicornThread(host="127.0.0.1", port=port)
    api.start()
    try:
        _wait_health_ok(port)
        status, body = _http_json(port, "/api/health")
        assert status == 200
        assert body["status"] == "ok"
    finally:
        api.stop()
    _wait_down(port)


def test_main_boots_api_and_closes_window(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.backend import config

    port = _free_port()
    monkeypatch.setenv("VD_PORT", str(port))
    config.get_settings.cache_clear()

    window_open = threading.Event()
    window_closed = threading.Event()
    start_kwargs: dict[str, Any] = {}

    def fake_start(*args: Any, **kwargs: Any) -> None:
        start_kwargs["mode"] = kwargs.get("mode")
        start_kwargs["port"] = kwargs.get("port")
        window_open.set()
        window_closed.wait(timeout=15)

    monkeypatch.setattr(eel, "start", fake_start)

    result: dict[str, int] = {}

    def run() -> None:
        result["code"] = main()

    thread = threading.Thread(target=run)
    thread.start()

    try:
        assert window_open.wait(timeout=15), "eel.start was never called"
        _wait_health_ok(port)
        assert start_kwargs["mode"] == "edge"
        assert start_kwargs["port"] == port + 1
    finally:
        window_closed.set()
        thread.join(timeout=15)
        config.get_settings.cache_clear()

    assert result["code"] == 0
    _wait_down(port)


def test_uvicorn_thread_raises_when_server_never_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.desktop.main as desktop

    class NeverServer:
        started = False
        should_exit = False

        def __init__(self, config: Any) -> None:
            pass

        def run(self) -> None:
            return None

    monkeypatch.setattr(uvicorn, "Server", NeverServer)
    monkeypatch.setattr(desktop.time, "sleep", lambda _seconds: None)

    counter = iter([1.0, 100.0])
    monkeypatch.setattr(desktop.time, "monotonic", lambda: next(counter))

    api = desktop.UvicornThread(host="127.0.0.1", port=_free_port())
    with pytest.raises(RuntimeError, match="failed to start"):
        api.start()
    api.stop()


def test_main_returns_error_when_web_dir_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.desktop.main as desktop

    calls: list[str] = []

    class NoopThread:
        def __init__(self, host: str, port: int) -> None:
            pass

        def start(self) -> None:
            calls.append("start")

        def stop(self) -> None:
            calls.append("stop")

    monkeypatch.setattr(desktop, "UvicornThread", NoopThread)
    monkeypatch.setattr(desktop, "WEB_DIR", Path("/does/not/exist"))

    assert desktop.main() == 1
    assert calls == ["start", "stop"]
