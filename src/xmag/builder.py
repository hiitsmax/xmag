"""Main build orchestration for xmag."""

from __future__ import annotations

from pathlib import Path

from xmag.config import LayoutConfig
from xmag.models import BuildReport


def build_issue(
    url_file: Path,
    output: Path,
    config: LayoutConfig,
    *,
    headless: bool = True,
    storage_state: Path | None = None,
    timeout_seconds: int = 30,
    continue_on_error: bool = False,
    keep_tex: bool = False,
) -> BuildReport:
    """Build a PDF issue from a list of X URLs."""

    raise NotImplementedError(
        "build_issue is not implemented yet. Complete extractor, renderer, and compiler modules first."
    )
