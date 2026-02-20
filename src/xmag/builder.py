"""Main build orchestration for xmag."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from xmag.config import LayoutConfig
from xmag.extractor import ArticleExtractionError, extract_article
from xmag.input import load_url_file
from xmag.models import ArticleContent, BuildReport


def _extract_contents(
    *,
    url_file: Path,
    headless: bool,
    storage_state: Path | None,
    timeout_seconds: int,
    continue_on_error: bool,
) -> tuple[list[ArticleContent], list[str], int]:
    inputs = load_url_file(url_file)

    contents: list[ArticleContent] = []
    failures: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        if storage_state is not None:
            context = browser.new_context(storage_state=str(storage_state))
        else:
            context = browser.new_context()

        page = context.new_page()
        for item in inputs:
            try:
                content = extract_article(page, item, timeout_seconds)
                contents.append(content)
            except ArticleExtractionError as exc:
                message = f"{item.url}: {exc}"
                if continue_on_error:
                    failures.append(message)
                    continue
                raise RuntimeError(message) from exc

        context.close()
        browser.close()

    return contents, failures, len(inputs)


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

    del output
    del config
    del keep_tex

    contents, failures, total = _extract_contents(
        url_file=url_file,
        headless=headless,
        storage_state=storage_state,
        timeout_seconds=timeout_seconds,
        continue_on_error=continue_on_error,
    )

    if not contents:
        raise RuntimeError("No extractable articles were found")

    raise NotImplementedError(
        "Extraction is implemented. Rendering and PDF compilation are implemented in the next step."
    )
