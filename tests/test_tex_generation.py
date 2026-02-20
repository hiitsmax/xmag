from datetime import datetime, timezone
from pathlib import Path

from xmag.config import ImageLayoutMode, LayoutConfig, PaginationMode
from xmag.models import ArticleContent, LocalMedia
from xmag.renderer import render_issue_tex


def _sample_contents() -> list[ArticleContent]:
    return [
        ArticleContent(
            status_id="111",
            url="https://x.com/alice/status/111",
            author_name="Alice",
            author_handle="@alice",
            published_at=datetime(2026, 2, 20, 12, 0, tzinfo=timezone.utc),
            text="First paragraph.\n\n```python\nprint('hi')\n```\n\nSecond paragraph.",
            media_urls=["https://pbs.twimg.com/media/abc?format=jpg&name=small"],
        ),
        ArticleContent(
            status_id="222",
            url="https://x.com/bob/status/222",
            author_name="Bob",
            author_handle="@bob",
            published_at=datetime(2026, 2, 20, 13, 0, tzinfo=timezone.utc),
            text="Another article text.",
            media_urls=[],
        ),
    ]


def _media_map(tmp_path: Path) -> dict[str, list[LocalMedia]]:
    image_path = tmp_path / "img.jpg"
    image_path.write_bytes(b"fake")

    return {
        "111": [LocalMedia(source_url="https://pbs.twimg.com/media/abc", local_path=image_path)],
        "222": [],
    }


def test_render_issue_tex_span_mode_contains_multicol_and_reduced_width_image(tmp_path: Path) -> None:
    config = LayoutConfig(image_layout=ImageLayoutMode.SPAN, pagination=PaginationMode.CONTINUOUS)
    tex = render_issue_tex(_sample_contents(), _media_map(tmp_path), config)

    assert r"\begin{multicols*}{3}" in tex
    assert r"\includegraphics[width=0.72\textwidth]" in tex


def test_render_issue_tex_newpage_inserts_break_between_articles(tmp_path: Path) -> None:
    config = LayoutConfig(image_layout=ImageLayoutMode.INLINE, pagination=PaginationMode.NEWPAGE)
    tex = render_issue_tex(_sample_contents(), _media_map(tmp_path), config)

    assert tex.count(r"\newpage") >= 1
    assert r"\includegraphics[width=0.84\columnwidth]" in tex
    assert "Article 1/2" in tex


def test_render_issue_tex_appendix_mode_collects_images(tmp_path: Path) -> None:
    config = LayoutConfig(image_layout=ImageLayoutMode.APPENDIX)
    tex = render_issue_tex(_sample_contents(), _media_map(tmp_path), config)

    assert "Image Appendix" in tex


def test_render_issue_tex_renders_fenced_code_as_lstlisting(tmp_path: Path) -> None:
    config = LayoutConfig(image_layout=ImageLayoutMode.INLINE)
    tex = render_issue_tex(_sample_contents(), _media_map(tmp_path), config)

    assert r"\begin{lstlisting}[language=Python]" in tex
    assert "print('hi')" in tex


def test_render_issue_tex_renders_inline_markdown(tmp_path: Path) -> None:
    contents = [
        ArticleContent(
            status_id="333",
            url="https://x.com/x/status/333",
            author_name="Name",
            author_handle="@name",
            published_at=datetime(2026, 2, 20, 15, 0, tzinfo=timezone.utc),
            text="Read **this** and [source](https://example.com).",
            media_urls=[],
        )
    ]
    tex = render_issue_tex(contents, {"333": []}, LayoutConfig())

    assert r"\textbf{this}" in tex
    assert r"\href{https://example.com}{source}" in tex
