"""Real-time progress broadcasting over WebSockets.

The :class:`ProgressHub` keeps the set of live WebSocket connections and
forwards :class:`ProgressEvent` snapshots whenever the ``DownloadManager``
updates a record. It registers itself as an ``on_update`` listener, so it stays
decoupled from the download lifecycle itself.

Because progress hooks run in worker threads, the hub hands every event to the
event loop with :meth:`asyncio.loop.call_soon_threadsafe` before sending it.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket

from app.services.manager import DownloadManager, DownloadRecord


@dataclass(frozen=True)
class ProgressEvent:
    """A JSON-serialisable progress snapshot for one download."""

    download_id: str
    status: str
    progress: float
    speed: str | None = None
    eta: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "download_id": self.download_id,
            "status": self.status,
            "progress": self.progress,
            "speed": self.speed,
            "eta": self.eta,
        }


def progress_event(record: DownloadRecord) -> ProgressEvent:
    """Build a snapshot from the current state of a download record."""
    return ProgressEvent(
        download_id=record.id,
        status=record.status,
        progress=record.progress,
        speed=record.speed,
        eta=record.eta,
    )


class ProgressHub:
    """Fans out download state changes to subscribed WebSocket clients."""

    def __init__(self, manager: DownloadManager) -> None:
        self._manager = manager
        self._sockets: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._manager.set_update_listener(self.notify)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a client and send it the current state of every download."""
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        self._sockets.add(websocket)
        for record in self._manager.list():
            await self._safe_send(websocket, progress_event(record))

    def disconnect(self, websocket: WebSocket) -> None:
        """Forget a client (called on disconnect or failed send)."""
        self._sockets.discard(websocket)

    def notify(self, record: DownloadRecord) -> None:
        """Queue a broadcast for ``record``; safe to call from any thread."""
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        event = progress_event(record)
        loop.call_soon_threadsafe(self._schedule_broadcast, event)

    def _schedule_broadcast(self, event: ProgressEvent) -> None:
        for socket in list(self._sockets):
            asyncio.create_task(self._safe_send(socket, event))

    async def _safe_send(self, websocket: WebSocket, event: ProgressEvent) -> None:
        try:
            await websocket.send_json(event.to_dict())
        except Exception:
            self.disconnect(websocket)
