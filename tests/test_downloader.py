"""Tests for app.services.downloader.

All yt-dlp calls are replaced by a fake builder, so these tests never
perform real downloads or touch the network.
"""

from pathlib import Path

import pytest

from app.services.downloader import (
    DownloadError,
    DownloadService,
    ExtractionError,
    InvalidRequestError,
    UnsupportedURLError,
    format_selector,
)

SAFE_URL = "https://example.com/watch?v=abc123"


class FakeDL:
    """Minimal stand-in for yt_dlp.YoutubeDL."""

    def __init__(
        self, info: dict | None = None, error: Exception | None = None
    ) -> None:
        self.options: dict = {}
        self.info = info
        self.error = error
        self.extract_info_calls: list[tuple[str, bool]] = []

    def extract_info(self, url: str, download: bool = False) -> dict:
        self.extract_info_calls.append((url, download))
        if self.error is not None:
            raise self.error
        if self.info is None:
            return {"id": "abc123", "title": "Fake Title", "ext": "mp4"}
        return self.info

    def prepare_filename(self, info: dict) -> str:
        title = info.get("title") or "video"
        return str(Path("downloads") / f"{title}.{info.get('ext', 'mp4')}")


def make_service(dl: FakeDL, downloads_dir: Path | None = None) -> DownloadService:
    def builder(options: dict) -> FakeDL:
        dl.options = options
        return dl

    return DownloadService(
        downloads_dir=downloads_dir or Path("downloads"),
        dl_builder=builder,
    )


def completed_info(file_path: Path) -> dict:
    """yt-dlp style info dict pointing at an existing output file."""
    return {
        "id": "x1",
        "title": "T",
        "ext": "mp4",
        "requested_downloads": [{"filepath": str(file_path)}],
    }


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/video",
        "javascript:alert(1)",
        "file:///etc/passwd",
        "",
        "https://user:pass@example.com/video",
        "http://",
        "https://" + "a" * 2100,
    ],
)
def test_rejects_unsafe_urls(url: str) -> None:
    service = make_service(FakeDL())
    with pytest.raises(UnsupportedURLError):
        service.download(url)
    with pytest.raises(UnsupportedURLError):
        service.extract_metadata(url)


def test_extract_metadata_returns_info_and_does_not_download() -> None:
    dl = FakeDL(
        info={
            "id": "x1",
            "title": "My Video",
            "duration": 123,
            "thumbnail": "https://t/img.jpg",
        }
    )
    service = make_service(dl)

    result = service.extract_metadata(SAFE_URL)

    assert result["id"] == "x1"
    assert result["title"] == "My Video"
    assert result["webpage_url"] == SAFE_URL
    assert dl.options["skip_download"] is True
    assert dl.extract_info_calls == [(SAFE_URL, False)]


def test_extract_metadata_wraps_errors() -> None:
    service = make_service(FakeDL(error=RuntimeError("boom")))

    with pytest.raises(ExtractionError):
        service.extract_metadata(SAFE_URL)


def test_download_returns_output_path(tmp_path: Path) -> None:
    out_file = tmp_path / "out.mp4"
    out_file.write_bytes(b"data")
    dl = FakeDL(info=completed_info(out_file))
    service = make_service(dl, downloads_dir=tmp_path)

    result = service.download(SAFE_URL)

    assert result == out_file
    assert dl.options["format"] == "bestvideo*+bestaudio/best"
    assert "progress_hooks" not in dl.options
    assert dl.extract_info_calls == [(SAFE_URL, True)]


def test_download_passes_progress_hook(tmp_path: Path) -> None:
    out_file = tmp_path / "out.mp4"
    out_file.write_bytes(b"data")
    received: list[dict] = []

    def hook(data: dict) -> None:
        received.append(data)

    dl = FakeDL(info=completed_info(out_file))
    service = make_service(dl, downloads_dir=tmp_path)

    service.download(SAFE_URL, progress_hook=hook)

    assert dl.options["progress_hooks"] == [hook]


def test_download_audio_selects_bestaudio_and_postprocessor(tmp_path: Path) -> None:
    out_file = tmp_path / "out.mp3"
    out_file.write_bytes(b"data")
    dl = FakeDL(info=completed_info(out_file))
    service = make_service(dl, downloads_dir=tmp_path)

    result = service.download(SAFE_URL, kind="audio")

    assert result == out_file
    assert dl.options["format"] == "bestaudio/best"
    postprocessor = dl.options["postprocessors"][0]
    assert postprocessor["key"] == "FFmpegExtractAudio"
    assert postprocessor["preferredcodec"] == "mp3"


def test_download_output_missing_raises(tmp_path: Path) -> None:
    dl = FakeDL(info=completed_info(tmp_path / "missing.mp4"))
    service = make_service(dl, downloads_dir=tmp_path)

    with pytest.raises(DownloadError):
        service.download(SAFE_URL)


def test_download_wraps_ytdlp_errors(tmp_path: Path) -> None:
    service = make_service(
        FakeDL(error=RuntimeError("network down")), downloads_dir=tmp_path
    )

    with pytest.raises(DownloadError):
        service.download(SAFE_URL)


def test_invalid_parameters_rejected(tmp_path: Path) -> None:
    service = make_service(FakeDL(), downloads_dir=tmp_path)

    with pytest.raises(InvalidRequestError):
        service.download(SAFE_URL, kind="app")
    with pytest.raises(InvalidRequestError):
        service.download(SAFE_URL, quality="9999")


def test_format_selector_rules() -> None:
    assert format_selector("video", "best") == "bestvideo*+bestaudio/best"
    assert format_selector("audio", "720") == "bestaudio/best"
    assert "height<=720" in format_selector("video", "720")


def test_service_receives_injectable_builder() -> None:
    builder_calls: list[dict] = []

    def builder(options: dict) -> FakeDL:
        builder_calls.append(options)
        return FakeDL()

    service = DownloadService(downloads_dir=Path("downloads"), dl_builder=builder)
    service.extract_metadata(SAFE_URL)

    assert len(builder_calls) == 1
    assert builder_calls[0]["simulate"] is True


def test_ffmpeg_location_is_passed_to_ytdlp_options() -> None:
    dl = FakeDL()
    service = DownloadService(
        downloads_dir=Path("downloads"),
        dl_builder=lambda options: dl.__dict__.update(options=options) or dl,
        ffmpeg_location=r"C:\tools\ffmpeg\bin",
    )

    service.extract_metadata(SAFE_URL)

    assert dl.options["ffmpeg_location"] == r"C:\tools\ffmpeg\bin"


def test_extract_metadata_raises_when_info_is_empty() -> None:
    service = make_service(FakeDL(info={}))

    with pytest.raises(ExtractionError):
        service.extract_metadata(SAFE_URL)


def test_download_falls_back_to_prepare_filename(tmp_path: Path) -> None:
    out_file = tmp_path / "Infer.mp4"
    out_file.write_bytes(b"data")

    class LocalFileDL(FakeDL):
        def prepare_filename(self, info: dict) -> str:
            return str(out_file)

    service = make_service(
        LocalFileDL(info={"id": "i1", "title": "Infer", "ext": "mp4"}),
        downloads_dir=tmp_path,
    )

    result = service.download(SAFE_URL)

    assert result == out_file
