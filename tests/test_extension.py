"""Tests for the Manifest V3 browser extension (static structure validation)."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.backend.server import app

EXTENSION_DIR = Path(__file__).resolve().parents[1] / "extension"

client = TestClient(app)


def _manifest() -> dict:
    with (EXTENSION_DIR / "manifest.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def test_manifest_is_valid_mv3() -> None:
    manifest = _manifest()
    assert manifest["manifest_version"] == 3
    assert manifest["background"]["service_worker"] == "background.js"
    assert manifest["action"]["default_popup"] == "popup/popup.html"
    assert manifest["options_page"] == "options/options.html"
    assert set(manifest["permissions"]) == {
        "activeTab",
        "tabs",
        "scripting",
        "storage",
    }


def test_host_permissions_are_local_only() -> None:
    manifest = _manifest()
    assert manifest["host_permissions"]
    for host in manifest["host_permissions"]:
        assert host.startswith(("http://127.0.0.1:", "http://localhost:"))


def test_all_referenced_files_exist() -> None:
    manifest = _manifest()
    referenced = [
        manifest["background"]["service_worker"],
        manifest["action"]["default_popup"],
        manifest["options_page"],
        *manifest["icons"].values(),
        *manifest["action"]["default_icon"].values(),
    ]
    for relative in referenced:
        assert (EXTENSION_DIR / relative).is_file(), f"missing {relative}"


def test_background_only_uses_backend_endpoints() -> None:
    text = (EXTENSION_DIR / "background.js").read_text(encoding="utf-8")
    for endpoint in ("/api/health", "/api/downloads", "/api/downloads/"):
        assert endpoint in text
    assert text.count("/api/downloads") >= 4


def test_content_script_targets_page_video_sources() -> None:
    text = (EXTENSION_DIR / "content.js").read_text(encoding="utf-8")
    for selector in ("video", 'meta[property="og:video"]', "source[src]"):
        assert selector in text


def test_extension_origin_is_allowed_for_local_api() -> None:
    response = client.options(
        "/api/downloads",
        headers={
            "Origin": "chrome-extension://deadbeefdeadbeefdeadbeefdeadbeef",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "chrome-extension://deadbeefdeadbeefdeadbeefdeadbeef"
    )
