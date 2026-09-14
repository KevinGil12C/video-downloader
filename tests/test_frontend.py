"""Tests for the web frontend served by FastAPI and its CORS allowlist."""

from fastapi.testclient import TestClient

from app.backend.server import app

client = TestClient(app)


def test_index_page_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Video Downloader Local</title>" in response.text


def test_css_and_js_assets_are_served() -> None:
    css = client.get("/css/style.css")
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")

    js = client.get("/js/app.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]


def test_api_routes_take_priority_over_static() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


def test_missing_static_file_returns_404() -> None:
    response = client.get("/does-not-exist.txt")
    assert response.status_code == 404


def test_cors_allows_eel_desktop_origin() -> None:
    response = client.get(
        "/api/health",
        headers={"Origin": "http://127.0.0.1:8001"},
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://127.0.0.1:8001"
    )


def test_cors_preflight_from_eel_origin() -> None:
    response = client.options(
        "/api/downloads",
        headers={
            "Origin": "http://localhost:8001",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:8001"
    )
