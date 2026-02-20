"""Media URL normalization and downloading utilities."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from xmag.models import LocalMedia


class MediaDownloadError(RuntimeError):
    """Raised when media assets fail to download."""


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def normalize_media_url(url: str) -> str:
    """Normalize X media URLs to request original quality image assets."""

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    image_format = query.get("format", [""])[0]
    if not image_format:
        suffix = Path(parsed.path).suffix.lstrip(".")
        image_format = suffix if suffix else "jpg"

    normalized_query = urlencode({"format": image_format, "name": "orig"})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", normalized_query, ""))


def _filename_for_media(url: str, index: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    image_format = query.get("format", [""])[0]
    stem = Path(parsed.path).stem or f"image_{index:03d}"
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)

    extension = image_format if image_format else "jpg"
    return f"{index:03d}_{safe_stem}.{extension}"


def download_media(media_urls: list[str], out_dir: Path) -> list[LocalMedia]:
    """Download media URLs into out_dir and return local media metadata."""

    out_dir.mkdir(parents=True, exist_ok=True)

    normalized_urls = [normalize_media_url(url) for url in _dedupe_preserve(media_urls)]
    local_media: list[LocalMedia] = []

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for index, url in enumerate(normalized_urls, start=1):
            filename = _filename_for_media(url, index)
            file_path = out_dir / filename

            try:
                response = client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise MediaDownloadError(f"Failed to download media '{url}': {exc}") from exc

            file_path.write_bytes(response.content)
            local_media.append(LocalMedia(source_url=url, local_path=file_path))

    return local_media
