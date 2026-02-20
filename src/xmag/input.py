"""URL parsing and URL-file ingestion utilities."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from xmag.models import ArticleInput

_ALLOWED_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}


def parse_status_id(url: str) -> str:
    """Extract a numeric status id from an X/Twitter URL."""

    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme in '{url}'")
    if parsed.netloc.lower() not in _ALLOWED_HOSTS:
        raise ValueError(f"Unsupported host in '{url}'. Expected x.com or twitter.com")

    parts = [part for part in parsed.path.split("/") if part]
    for index, part in enumerate(parts):
        if part == "status" and index + 1 < len(parts):
            status_id = parts[index + 1]
            if status_id.isdigit():
                return status_id
            raise ValueError(f"Status id is not numeric in '{url}'")

    raise ValueError(f"Could not find '/status/<id>' in '{url}'")


def load_url_file(path: Path) -> list[ArticleInput]:
    """Load and validate article URLs from a text file (one URL per line)."""

    if not path.exists() or not path.is_file():
        raise ValueError(f"URL file not found: {path}")

    seen: set[str] = set()
    items: list[ArticleInput] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            status_id = parse_status_id(line)
        except ValueError as exc:
            raise ValueError(f"Invalid URL at line {line_number}: {exc}") from exc

        if status_id in seen:
            continue

        seen.add(status_id)
        items.append(ArticleInput(url=line, status_id=status_id))

    if not items:
        raise ValueError("No valid URLs found in URL file")

    return items
