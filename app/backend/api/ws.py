"""WebSocket endpoint streaming live download progress.

The hub is created lazily and wired to the default download manager, so the
existing ``GET /api/downloads`` polling contract remains available as a
fallback when WebSockets are unavailable.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.services.progress import ProgressHub

router = APIRouter()

_hub: ProgressHub | None = None


def get_progress_hub() -> ProgressHub:
    """Return the process-wide hub wired to the default download manager."""
    global _hub
    if _hub is None:
        from app.services.manager import default_manager

        _hub = ProgressHub(manager=default_manager())
    return _hub


ProgressHubDependency = Annotated[ProgressHub, Depends(get_progress_hub)]


@router.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket, hub: ProgressHubDependency) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
