"""Playwright-based extraction of X article content."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from dateutil.parser import isoparse
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from xmag.models import ArticleContent, ArticleInput

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class ArticleExtractionError(RuntimeError):
    """Base extraction error for X article parsing failures."""


class ArticleTimeoutError(ArticleExtractionError):
    """Raised when article extraction times out."""


class ArticleNotFoundError(ArticleExtractionError):
    """Raised when article content cannot be found on the page."""


def _to_datetime(raw_timestamp: str | None) -> datetime | None:
    if not raw_timestamp:
        return None
    try:
        return isoparse(raw_timestamp)
    except ValueError:
        return None


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _extract_author(raw_author: str) -> tuple[str, str]:
    lines = [line.strip() for line in raw_author.splitlines() if line.strip()]

    match = re.search(r"@[A-Za-z0-9_]+", raw_author)
    author_handle = match.group(0) if match else "@unknown"

    candidate_name = lines[0] if lines else "Unknown"
    candidate_name = re.sub(r"@[A-Za-z0-9_]+", "", candidate_name).strip(" -|·")
    author_name = candidate_name if candidate_name else "Unknown"
    return author_name, author_handle


def _extract_text_from_locator(article_locator: "Locator") -> str:
    text_nodes = article_locator.locator('[data-testid="tweetText"]')
    texts: list[str] = []

    for index in range(text_nodes.count()):
        text = text_nodes.nth(index).inner_text().strip()
        if text:
            texts.append(text)

    if not texts:
        fallback_text = article_locator.inner_text().strip()
        if fallback_text:
            texts.append(fallback_text)

    joined = "\n\n".join(_dedupe_preserve(texts)).strip()
    if not joined:
        raise ArticleExtractionError("Extracted article text is empty")
    return joined


def _find_article_locator(page: "Page", status_id: str, timeout_ms: int) -> "Locator":
    page.wait_for_selector("article", timeout=timeout_ms)

    anchored = page.locator(f'article:has(a[href*="/status/{status_id}"])')
    if anchored.count() > 0:
        return anchored.first

    fallback = page.locator("article")
    if fallback.count() > 0:
        return fallback.first

    raise ArticleNotFoundError(f"Could not locate article for status id {status_id}")


def _extract_media_urls(article_locator: "Locator") -> list[str]:
    urls = article_locator.locator('img[src*="twimg.com/media"]').evaluate_all(
        "els => els.map(el => el.getAttribute('src')).filter(Boolean)"
    )
    cleaned = [url for url in urls if isinstance(url, str) and url.startswith("http")]
    return _dedupe_preserve(cleaned)


def extract_article(
    page: "Page",
    article: ArticleInput,
    timeout_s: int,
    *,
    _attempt: int = 1,
) -> ArticleContent:
    """Load and extract one article from a status URL."""

    timeout_ms = timeout_s * 1000

    try:
        page.goto(article.url, wait_until="domcontentloaded", timeout=timeout_ms)
        article_locator = _find_article_locator(page, article.status_id, timeout_ms)

        raw_author = ""
        author_nodes = article_locator.locator('[data-testid="User-Name"]')
        if author_nodes.count() > 0:
            raw_author = author_nodes.first.inner_text().strip()
        author_name, author_handle = _extract_author(raw_author)

        raw_timestamp = None
        time_nodes = article_locator.locator("time")
        if time_nodes.count() > 0:
            raw_timestamp = time_nodes.first.get_attribute("datetime")

        text = _extract_text_from_locator(article_locator)
        media_urls = _extract_media_urls(article_locator)

        return ArticleContent(
            status_id=article.status_id,
            url=article.url,
            author_name=author_name,
            author_handle=author_handle,
            published_at=_to_datetime(raw_timestamp),
            text=text,
            media_urls=media_urls,
        )
    except PlaywrightTimeoutError as exc:
        if _attempt == 1:
            return extract_article(page, article, timeout_s * 2, _attempt=2)
        raise ArticleTimeoutError(
            f"Timed out extracting status id {article.status_id} from {article.url}"
        ) from exc
    except ArticleExtractionError:
        raise
    except Exception as exc:  # pragma: no cover - defensive normalization
        raise ArticleExtractionError(
            f"Unexpected extraction failure for status id {article.status_id}: {exc}"
        ) from exc
