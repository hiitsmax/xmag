"""Main build orchestration for xmag."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

from xmag.compiler import compile_tex_with_tectonic
from xmag.config import LayoutConfig, PaginationMode
from xmag.extractor import ArticleExtractionError, extract_article
from xmag.input import load_url_file
from xmag.media import download_media
from xmag.models import ArticleContent, BuildReport
from xmag.renderer import render_issue_tex


@contextmanager
def _build_workspace(output: Path, keep_tex: bool):
    if keep_tex:
        workspace = output.parent / f"{output.stem}_build"
        workspace.mkdir(parents=True, exist_ok=True)
        yield workspace
        return

    with tempfile.TemporaryDirectory(prefix="xmag-") as tmp:
        yield Path(tmp)


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


def _split_output_path(output: Path, index: int, status_id: str) -> Path:
    stem = output.stem if output.suffix.lower() == ".pdf" else output.name
    return output.parent / f"{stem}-{index:03d}-{status_id}.pdf"


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
    """Build one or more PDFs from a list of X status URLs."""

    contents, failures, total = _extract_contents(
        url_file=url_file,
        headless=headless,
        storage_state=storage_state,
        timeout_seconds=timeout_seconds,
        continue_on_error=continue_on_error,
    )

    if not contents:
        raise RuntimeError("No extractable articles were found")

    output = output if output.suffix.lower() == ".pdf" else output.with_suffix(".pdf")
    output.parent.mkdir(parents=True, exist_ok=True)

    report = BuildReport(total=total, succeeded=len(contents), failed=len(failures), failures=failures)

    with _build_workspace(output, keep_tex=keep_tex) as workspace:
        media_map: dict[str, list] = {}
        media_root = workspace / "media"
        for article in contents:
            media_map[article.status_id] = download_media(
                article.media_urls,
                media_root / article.status_id,
            )

        if config.pagination == PaginationMode.SPLIT:
            for index, article in enumerate(contents, start=1):
                single_tex = render_issue_tex([article], media_map, config.model_copy())
                tex_path = workspace / f"article-{index:03d}-{article.status_id}.tex"
                tex_path.write_text(single_tex, encoding="utf-8")

                article_output = _split_output_path(output, index, article.status_id)
                compile_tex_with_tectonic(tex_path, article_output)
                report.outputs.append(article_output)
        else:
            tex = render_issue_tex(contents, media_map, config)
            tex_path = workspace / "issue.tex"
            tex_path.write_text(tex, encoding="utf-8")

            compile_tex_with_tectonic(tex_path, output)
            report.outputs.append(output)

    return report
