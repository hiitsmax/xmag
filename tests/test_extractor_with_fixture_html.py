from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from xmag.extractor import extract_article
from xmag.models import ArticleInput


@pytest.mark.skipif(not Path("tests/fixtures/x_article_fixture.html").exists(), reason="fixture missing")
def test_extract_article_with_fixture_html() -> None:
    fixture_path = Path("tests/fixtures/x_article_fixture.html").resolve()
    fixture_url = fixture_path.as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        article = ArticleInput(url=fixture_url, status_id="12345")
        content = extract_article(page, article, timeout_s=15)

        assert content.status_id == "12345"
        assert content.author_name == "Alice Example"
        assert content.author_handle == "@alice"
        assert "fixture article" in content.text
        assert len(content.media_urls) == 2

        context.close()
        browser.close()
