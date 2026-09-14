"""Endpoints to create, inspect, cancel and forget downloads.

All endpoints bind to ``127.0.0.1`` only and never require authentication.
The manager dependency is injectable so tests can swap in a fake manager.
"""

from __future__ import annotations

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException

from app.backend.models import (
    DownloadCreateRequest,
    DownloadListResponse,
    DownloadResponse,
    DownloadStatus,
)
from app.services.downloader import DownloaderError
from app.services.manager import (
    DownloadManager,
    DownloadNotCancellableError,
    DownloadNotDeletableError,
    DownloadNotFoundError,
    DownloadRecord,
    default_manager,
)

router = APIRouter(prefix="/api/downloads", tags=["downloads"])

Manager = Annotated[DownloadManager, Depends(default_manager)]


def _to_response(record: DownloadRecord) -> DownloadResponse:
    return DownloadResponse(
        id=record.id,
        url=record.url,
        format=cast(Literal["video", "audio"], record.kind),
        container=getattr(record, "container", "mp4"),
        quality=record.quality,
        status=cast(DownloadStatus, record.status),
        progress=record.progress,
        file=record.file,
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post("", response_model=DownloadResponse, status_code=201)
async def create_download(
    payload: DownloadCreateRequest,
    manager: Manager,
) -> DownloadResponse:
    try:
        arguments = {
            "kind": payload.format,
            "quality": payload.quality,
            "directory": payload.directory,
        }
        if payload.container is not None:
            arguments["container"] = payload.container
        record = await manager.create(payload.url, **arguments)
    except DownloaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(record)


@router.get("", response_model=DownloadListResponse)
async def list_downloads(manager: Manager) -> DownloadListResponse:
    items = [_to_response(record) for record in manager.list()]
    return DownloadListResponse(items=items)


@router.get("/{download_id}", response_model=DownloadResponse)
async def get_download(download_id: str, manager: Manager) -> DownloadResponse:
    record = manager.get(download_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Download not found")
    return _to_response(record)


@router.post("/{download_id}/cancel", response_model=DownloadResponse)
async def cancel_download(download_id: str, manager: Manager) -> DownloadResponse:
    try:
        record = manager.cancel(download_id)
    except DownloadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Download not found") from exc
    except DownloadNotCancellableError as exc:
        raise HTTPException(
            status_code=400, detail="Cannot cancel finished download"
        ) from exc
    return _to_response(record)


@router.delete("/{download_id}", status_code=204)
async def delete_download(download_id: str, manager: Manager) -> None:
    try:
        manager.delete(download_id)
    except DownloadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Download not found") from exc
    except DownloadNotDeletableError as exc:
        raise HTTPException(
            status_code=409, detail="Download is still in progress"
        ) from exc
    return None
