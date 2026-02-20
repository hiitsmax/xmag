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


_METRIC_LINE_RE = re.compile(r"^[\d,.]+(?:[KMBT]|[KMBT]\+)?$", re.IGNORECASE)
_STOP_AT_LINE_RE = re.compile(
    r"^(Want to publish your own Article\?|Upgrade to Premium|Read\s+\d+\s+replies)$",
    re.IGNORECASE,
)
_TIMESTAMP_LINE_RE = re.compile(r"^\d{1,2}:\d{2}\s?(AM|PM)\s*·", re.IGNORECASE)
_ARTIFACT_PATTERNS = [
    re.compile(r"if\s*\(!alreadyRequested\)\s*\{[\s\S]*?\}", re.IGNORECASE),
    re.compile(r"postComment\s*\([\s\S]*?\)", re.IGNORECASE),
    re.compile(r"@review-harness:[^\s]+", re.IGNORECASE),
    re.compile(r"\$\{trigger\}", re.IGNORECASE),
]


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


def _sanitize_text(raw_text: str, author_name: str, author_handle: str) -> str:
    sanitized_source = raw_text
    for pattern in _ARTIFACT_PATTERNS:
        sanitized_source = pattern.sub(" ", sanitized_source)

    author_prefix = re.compile(
        rf"^\s*{re.escape(author_name)}\s+{re.escape(author_handle)}(?:\s+[\d.,]+(?:[KMBT])?)*\s+",
        re.IGNORECASE,
    )
    sanitized_source = author_prefix.sub("", sanitized_source)

    lines = [line.rstrip() for line in sanitized_source.splitlines()]
    cleaned: list[str] = []

    author_name_norm = author_name.strip().lower()
    author_handle_norm = author_handle.strip().lower()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue

        if _STOP_AT_LINE_RE.match(stripped) or _TIMESTAMP_LINE_RE.match(stripped):
            break

        if stripped == "Views" or stripped == "·":
            break

        lower = stripped.lower()
        if (
            lower == author_name_norm
            or lower == author_handle_norm
            or lower == f"{author_name_norm} {author_handle_norm}".strip()
        ):
            continue

        if _METRIC_LINE_RE.fullmatch(stripped):
            continue

        cleaned.append(stripped)

    # Collapse repeated blank lines but preserve paragraph intent.
    collapsed: list[str] = []
    previous_blank = False
    for line in cleaned:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank

    return "\n".join(collapsed).strip()


def _extract_text_from_locator(article_locator: "Locator", author_name: str, author_handle: str) -> str:
    selector_candidates = [
        '[data-testid="tweetText"]',
        "div[lang]",
        'div[dir="auto"]',
    ]

    best_sanitized = ""

    for selector in selector_candidates:
        nodes = article_locator.locator(selector)
        if nodes.count() == 0:
            continue

        collected: list[str] = []
        for index in range(min(nodes.count(), 20)):
            candidate = nodes.nth(index).inner_text().strip()
            if candidate and len(candidate) >= 12:
                collected.append(candidate)

        if not collected:
            continue

        if selector == '[data-testid="tweetText"]':
            candidate_text = "\n\n".join(_dedupe_preserve(collected))
        else:
            candidate_text = max(collected, key=len)

        sanitized = _sanitize_text(candidate_text, author_name, author_handle)
        if sanitized:
            if selector == '[data-testid="tweetText"]' and len(sanitized) >= 40:
                return sanitized
            if len(sanitized) > len(best_sanitized):
                best_sanitized = sanitized

    try:
        fallback_inner_text = article_locator.inner_text().strip()
    except Exception:
        fallback_inner_text = ""

    if fallback_inner_text:
        sanitized_inner = _sanitize_text(fallback_inner_text, author_name, author_handle)
        if len(sanitized_inner) > len(best_sanitized):
            best_sanitized = sanitized_inner

    if best_sanitized:
        return best_sanitized
    raise ArticleExtractionError("Could not find usable text nodes in article")


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

        text = _extract_text_from_locator(article_locator, author_name, author_handle)
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
