"""Tests for app.backend.security input validation helpers."""

from app.backend.security import allowed_cors_origins, is_safe_url


def test_is_safe_url_accepts_http_https() -> None:
    assert is_safe_url("https://example.com/watch?v=1")
    assert is_safe_url("http://127.0.0.1:8000/video")


def test_is_safe_url_rejects_bad_urls() -> None:
    for url in (
        "",
        "ftp://example.com/video",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "http://u:p@example.com/video",
        "http://",
        "http://[::1",
    ):
        assert is_safe_url(url) is False


def test_is_safe_url_rejects_oversized_urls() -> None:
    assert is_safe_url("https://" + "a" * 3000) is False


def test_allowed_cors_origins_return_sorted_local_origins() -> None:
    origins = allowed_cors_origins()
    assert origins == sorted(origins)
    for origin in origins:
        assert origin.startswith(("http://localhost:", "http://127.0.0.1:"))
