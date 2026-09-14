"""Security helpers: CORS allowlist and input validation.

The CORS origins are intentionally local-only. They cover the API origin
and the Eel desktop window (API port + 1), plus any extra origins passed
through the ``VD_ALLOWED_ORIGINS`` environment variable. The browser
extension does not appear here because MV3 ``host_permissions`` calls are
not subject to CORS.
"""

from __future__ import annotations

from urllib.parse import urlparse

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.backend.config import get_settings

_ALLOWED_URL_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048


class RejectDisallowedOrigin:
    """Reject HTTP requests carrying a non-allowlisted ``Origin`` header.

    Browsers attach ``Origin`` to cross-origin requests (and to same-origin
    ones when they are not simple GETs). Short-circuiting every request whose
    origin is not in the CORS allowlist stops even non-preflighted requests
    (for example navigations from an attacker page) from reaching the
    routers, hardening the local API against DNS-rebinding style attacks.

    WebSocket connections are left to the browser's own cross-origin rules:
    extension builtins may originate from a ``chrome-extension://`` origin.
    """

    def __init__(self, app: ASGIApp, allowed_origins: list[str]) -> None:
        self.app = app
        self.allowed = set(allowed_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        origin = Headers(scope=scope).get("origin")
        if origin is not None and origin not in self.allowed:
            response = PlainTextResponse("Forbidden", status_code=403)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


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
