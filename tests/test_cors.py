"""CORS hardening and localhost-only binding tests."""

import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from app.backend import config
from app.backend.config import validate_host
from app.backend.security import allowed_cors_origins
from app.backend.server import app

client = TestClient(app)

ALLOWED_ORIGIN = "http://127.0.0.1:8000"
EEL_ORIGIN = "http://127.0.0.1:8001"
DISALLOWED_ORIGIN = "http://evil.example"


def test_cors_reflects_allowed_origin() -> None:
    response = client.get("/api/health", headers={"Origin": ALLOWED_ORIGIN})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_cors_reflects_eel_desktop_origin() -> None:
    response = client.get("/api/health", headers={"Origin": EEL_ORIGIN})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == EEL_ORIGIN


def test_disallowed_origin_is_rejected_before_routers() -> None:
    response = client.get("/api/health", headers={"Origin": DISALLOWED_ORIGIN})
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_null_origin_is_rejected() -> None:
    response = client.get("/api/health", headers={"Origin": "null"})
    assert response.status_code == 403


def test_requests_without_origin_header_are_served() -> None:
    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 200


def test_allowed_preflight_returns_cors_headers() -> None:
    response = client.options(
        "/api/downloads",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    methods = set(response.headers["access-control-allow-methods"].split(", "))
    assert {"GET", "POST", "DELETE", "OPTIONS"} <= methods


def test_disallowed_preflight_is_rejected() -> None:
    response = client.options(
        "/api/downloads",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_credentials_are_never_allowed_across_origins() -> None:
    response = client.get("/api/health", headers={"Origin": ALLOWED_ORIGIN})
    assert "access-control-allow-credentials" not in response.headers


def test_websocket_upgrade_is_not_blocked_by_origin_guard() -> None:
    with client.websocket_connect(
        "/ws/progress",
        headers={"Origin": DISALLOWED_ORIGIN},
    ) as websocket:
        websocket.close()


def test_extra_origins_from_environment_are_allowed() -> None:
    with mock.patch.dict(os.environ, {"VD_ALLOWED_ORIGINS": "http://localhost:5173"}):
        config.get_settings.cache_clear()
        try:
            assert "http://localhost:5173" in allowed_cors_origins()
        finally:
            config.get_settings.cache_clear()


def test_validate_host_accepts_loopback_only() -> None:
    for host in ("127.0.0.1", "localhost", "::1"):
        validate_host(host)


def test_load_settings_rejects_external_bind() -> None:
    with (
        mock.patch.dict(os.environ, {"VD_HOST": "0.0.0.0"}),
        pytest.raises(ValueError, match="loopback"),
    ):
        config.load_settings()
