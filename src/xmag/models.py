"""Domain models used by xmag."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    """A user-provided X/Twitter status URL and its parsed status id."""

    url: str
    status_id: str


class ArticleContent(BaseModel):
    """Normalized article data extracted from X."""

    status_id: str
    url: str
    author_name: str
    author_handle: str
    published_at: datetime | None
    text: str
    media_urls: list[str] = Field(default_factory=list)


class LocalMedia(BaseModel):
    """Downloaded media file information used by LaTeX rendering."""

    source_url: str
    local_path: Path
    width: int | None = None
    height: int | None = None


class BuildReport(BaseModel):
    """Final build summary returned by build_issue."""

    total: int
    succeeded: int
    failed: int
    outputs: list[Path] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
