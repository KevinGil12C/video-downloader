"""Security helpers: CORS allowlist and input validation.

The CORS origins are intentionally local-only. They cover the API port, the
Eel desktop window (API port + 1) and any extra origins passed through the
``VD_ALLOWED_ORIGINS`` environment variable. Browser-extension origins are
appended by the browser-extension phase.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.backend.config import get_settings

_ALLOWED_URL_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048


def allowed_cors_origins() -> list[str]:
    """Local-only origins the API is willing to answer to."""
    settings = get_settings()
    origins = {
        f"http://localhost:{settings.port}",
        f"http://127.0.0.1:{settings.port}",
        f"http://localhost:{settings.port + 1}",
        f"http://127.0.0.1:{settings.port + 1}",
    }
    origins.update(settings.allowed_origins)
    return sorted(origins)


def is_safe_url(url: str) -> bool:
    """Return ``True`` when ``url`` looks like a reasonable http(s) URL.

    Used before scheduling a download. Rejects non-http schemes,
    credentials embedded in the URL, and empty URLs.
    """
    if not url or len(url) > _MAX_URL_LENGTH:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    return bool(parsed.netloc)
