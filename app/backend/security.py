"""Security helpers: CORS allowlist and input validation.

The CORS origins are intentionally local-only. Browser extension origins
are appended by the browser-extension phase.
"""

from __future__ import annotations

from urllib.parse import urlparse

_ALLOWED_URL_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048


def allowed_cors_origins() -> list[str]:
    """Local-only origins the API is willing to answer to."""
    return ["http://localhost:8000", "http://127.0.0.1:8000"]


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
