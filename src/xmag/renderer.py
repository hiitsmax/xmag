"""LaTeX rendering for magazine-style article output."""

from __future__ import annotations

import re
from datetime import datetime
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment

from xmag.config import ImageLayoutMode, LayoutConfig, PaperSize, PaginationMode
from xmag.models import ArticleContent, LocalMedia

_LATEX_ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def latex_escape(value: str) -> str:
    """Escape LaTeX special characters in user/content text."""

    return "".join(_LATEX_ESCAPE_MAP.get(char, char) for char in value)


def _paper_option(paper: PaperSize) -> str:
    if paper == PaperSize.A4:
        return "a4paper"
    return "letterpaper"


def _date_display(value: datetime | None) -> str:
    if value is None:
        return "Unknown"
    return value.strftime("%Y-%m-%d %H:%M:%S %Z").strip()


def _latex_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _render_paragraphs(text: str) -> str:
    raw_paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    paragraphs = [re.sub(r"\s*\n\s*", " ", part) for part in raw_paragraphs]
    return "\n\n".join(f"{latex_escape(paragraph)}\\par" for paragraph in paragraphs)


def _render_article_header(article: ArticleContent) -> str:
    return "\n".join(
        [
            rf"\section*{{{latex_escape(article.author_name)} {latex_escape(article.author_handle)}}}",
            rf"\noindent\textbf{{Published:}} {latex_escape(_date_display(article.published_at))}\\",
            rf"\textbf{{Source:}} \url{{{article.url}}}",
            "\\vspace{2mm}",
        ]
    )


def _render_inline_images(images: list[LocalMedia]) -> str:
    snippets = []
    for image in images:
        snippets.append(
            "\n".join(
                [
                    r"\begin{center}",
                    rf"\includegraphics[width=0.98\columnwidth]{{\detokenize{{{_latex_path(image.local_path)}}}}}",
                    r"\end{center}",
                    r"\vspace{2mm}",
                ]
            )
        )
    return "\n".join(snippets)


def _render_span_images(images: list[LocalMedia]) -> str:
    snippets = []
    for image in images:
        snippets.append(
            "\n".join(
                [
                    r"\begin{center}",
                    rf"\includegraphics[width=0.98\textwidth]{{\detokenize{{{_latex_path(image.local_path)}}}}}",
                    r"\end{center}",
                    r"\vspace{3mm}",
                ]
            )
        )
    return "\n".join(snippets)


def _article_block(
    article: ArticleContent,
    images: list[LocalMedia],
    config: LayoutConfig,
) -> tuple[str, list[LocalMedia]]:
    header = _render_article_header(article)
    paragraphs = _render_paragraphs(article.text)

    if config.image_layout == ImageLayoutMode.INLINE:
        body = "\n".join(
            [
                rf"\begin{{multicols*}}{{{config.columns}}}",
                header,
                paragraphs,
                _render_inline_images(images),
                r"\end{multicols*}",
            ]
        )
        return body, []

    if config.image_layout == ImageLayoutMode.SPAN:
        body = "\n".join(
            [
                rf"\begin{{multicols*}}{{{config.columns}}}",
                header,
                paragraphs,
                r"\end{multicols*}",
                _render_span_images(images),
            ]
        )
        return body, []

    body = "\n".join(
        [
            rf"\begin{{multicols*}}{{{config.columns}}}",
            header,
            paragraphs,
            r"\end{multicols*}",
        ]
    )
    return body, images


def render_issue_tex(
    contents: list[ArticleContent],
    media_map: dict[str, list[LocalMedia]],
    config: LayoutConfig,
) -> str:
    """Render full issue LaTeX for one or more extracted articles."""

    blocks: list[str] = []
    appendix_images: list[LocalMedia] = []

    for index, article in enumerate(contents):
        body_block, appendix = _article_block(article, media_map.get(article.status_id, []), config)
        blocks.append(body_block)
        appendix_images.extend(appendix)

        if config.pagination == PaginationMode.NEWPAGE and index < len(contents) - 1:
            blocks.append(r"\newpage")

    template_source = files("xmag.templates").joinpath("issue.tex.j2").read_text(encoding="utf-8")
    environment = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
    template = environment.from_string(template_source)

    return template.render(
        paper_option=_paper_option(config.paper),
        inner_margin_mm=config.inner_margin_mm,
        outer_margin_mm=config.outer_margin_mm,
        top_margin_mm=config.top_margin_mm,
        bottom_margin_mm=config.bottom_margin_mm,
        column_gap_mm=config.column_gap_mm,
        body_blocks=blocks,
        appendix_images=appendix_images,
        include_appendix=config.image_layout == ImageLayoutMode.APPENDIX,
    )
