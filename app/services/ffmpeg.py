"""FFmpeg discovery, verification and version reporting.

FFmpeg is an external binary (not a pip dependency). It is searched in the
project's ``bin/ffmpeg/`` folder first, then in ``PATH``. The service also
reports its version for the info endpoint and feeds the ``ffmpeg_location``
of yt-dlp, which needs it to merge and convert media.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from app.backend.config import PROJECT_ROOT

_EXPECTED_BINARIES = ("ffmpeg.exe", "ffmpeg")


def find_ffmpeg(extra_paths: Iterable[Path] = ()) -> Path | None:
    """Locate the ffmpeg binary, if any.

    Search order:

    1. ``bin/ffmpeg/`` inside the project.
    2. Folders provided in ``extra_paths``.
    3. The ``ffmpeg`` command resolvable through ``PATH``.
    """
    folders = [PROJECT_ROOT / "bin" / "ffmpeg"]
    folders.extend(Path(folder) for folder in extra_paths)

    for folder in folders:
        for name in _EXPECTED_BINARIES:
            candidate = folder / name
            if candidate.is_file():
                return candidate

    found = shutil.which("ffmpeg")
    return Path(found) if found else None


def ffmpeg_version(binary: Path | str) -> str | None:
    """Return the first line of ``ffmpeg -version``, or ``None``.

    The first line looks like: ``ffmpeg version 6.1.1-full_build ...``.
    """
    try:
        proc = subprocess.run(
            [str(binary), "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if proc.returncode != 0:
        return None

    first_line = proc.stdout.splitlines()[0].strip() if proc.stdout else ""
    return first_line or None


class FFmpegService:
    """Locates ffmpeg and reports its availability and version."""

    def __init__(
        self,
        location: Path | str | None = None,
        extra_paths: Iterable[Path] = (),
    ) -> None:
        self._fixed_location = Path(location) if location is not None else None
        self._extra_paths = tuple(extra_paths)
        self._binary: Path | None = None

    def _resolve(self) -> Path | None:
        if self._fixed_location is not None:
            return self._fixed_location if self._fixed_location.is_file() else None
        if self._binary is None:
            self._binary = find_ffmpeg(self._extra_paths)
        return self._binary

    def executable(self) -> str | None:
        """Path suitable for yt-dlp's ``ffmpeg_location`` option."""
        binary = self._resolve()
        return str(binary) if binary is not None else None

    def available(self) -> bool:
        return self._resolve() is not None

    def version(self) -> str | None:
        binary = self._resolve()
        if binary is None:
            return None
        return ffmpeg_version(binary)


@lru_cache(maxsize=1)
def get_ffmpeg_service() -> FFmpegService:
    """Cached default ffmpeg service."""
    return FFmpegService()
