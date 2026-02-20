"""LaTeX rendering for magazine-style article output."""

from __future__ import annotations

import re
from dataclasses import dataclass
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

_CODE_FENCE_RE = re.compile(r"```(?P<lang>[A-Za-z0-9_+-]*)\n(?P<code>[\s\S]*?)```", re.MULTILINE)
_ULIST_RE = re.compile(r"^[-*]\s+")
_OLIST_RE = re.compile(r"^\d+[.)]\s+")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
_COMMAND_LINE_RE = re.compile(
    r"^(?:\$|npm\s+|pnpm\s+|yarn\s+|uv\s+|python\s+|pip\s+|git\s+|npx\s+|node\s+|curl\s+|bash\s+|sh\s+|export\s+|set\s+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RenderBlock:
    """Intermediate content block before LaTeX serialization."""

    kind: str
    body: str
    language: str | None = None


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


def _parse_plain_text_segment(segment: str) -> list[RenderBlock]:
    blocks: list[RenderBlock] = []
    paragraph_chunks = [chunk.strip("\n") for chunk in re.split(r"\n{2,}", segment) if chunk.strip()]

    for chunk in paragraph_chunks:
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue

        if len(lines) == 1:
            heading_match = _HEADING_RE.match(lines[0])
            if heading_match and heading_match.group(2).strip():
                level = len(heading_match.group(1))
                blocks.append(
                    RenderBlock(kind="heading", body=heading_match.group(2).strip(), language=str(level))
                )
                continue

        command_like_count = sum(1 for line in lines if _COMMAND_LINE_RE.match(line))
        if command_like_count >= 2:
            blocks.append(RenderBlock(kind="code", body="\n".join(lines), language=None))
            continue

        if all(_ULIST_RE.match(line) for line in lines):
            items = [re.sub(_ULIST_RE, "", line, count=1).strip() for line in lines]
            blocks.append(RenderBlock(kind="ulist", body="\n".join(items)))
            continue

        if all(_OLIST_RE.match(line) for line in lines):
            items = [re.sub(_OLIST_RE, "", line, count=1).strip() for line in lines]
            blocks.append(RenderBlock(kind="olist", body="\n".join(items)))
            continue

        blocks.append(RenderBlock(kind="text", body="\n".join(lines)))

    return blocks


def _parse_content_blocks(text: str) -> list[RenderBlock]:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    blocks: list[RenderBlock] = []
    cursor = 0

    for match in _CODE_FENCE_RE.finditer(normalized):
        leading_text = normalized[cursor : match.start()]
        blocks.extend(_parse_plain_text_segment(leading_text))

        language = match.group("lang").strip() or None
        code = match.group("code").strip("\n")
        if code:
            blocks.append(RenderBlock(kind="code", body=code, language=language))

        cursor = match.end()

    trailing_text = normalized[cursor:]
    blocks.extend(_parse_plain_text_segment(trailing_text))

    if not blocks:
        blocks.append(RenderBlock(kind="text", body=normalized))

    return blocks


def _render_text_block(block: RenderBlock) -> str:
    raw_lines = [line.strip() for line in block.body.splitlines() if line.strip()]
    escaped_lines = [latex_escape(line) for line in raw_lines]
    if not escaped_lines:
        return ""

    command_like_count = sum(1 for line in raw_lines if _COMMAND_LINE_RE.match(line))
    if command_like_count >= 2:
        joined = " \\\\\n".join(escaped_lines)
        return f"{joined}\\par"

    joined = latex_escape(" ".join(raw_lines))
    return f"{joined}\\par"


def _render_list_block(block: RenderBlock) -> str:
    environment = "itemize" if block.kind == "ulist" else "enumerate"
    lines = [line.strip() for line in block.body.splitlines() if line.strip()]
    items = [rf"\item {latex_escape(line)}" for line in lines]

    return "\n".join(
        [
            rf"\begin{{{environment}}}",
            *items,
            rf"\end{{{environment}}}",
        ]
    )


def _render_heading_block(block: RenderBlock) -> str:
    level = int(block.language) if block.language and block.language.isdigit() else 2
    escaped = latex_escape(block.body.strip())
    if level <= 1:
        return rf"\noindent\textbf{{\large {escaped}}}\par"
    if level == 2:
        return rf"\noindent\textbf{{{escaped}}}\par"
    return rf"\noindent\textit{{{escaped}}}\par"


def _listings_language(language: str | None) -> str:
    if language is None:
        return ""

    normalized = language.strip().lower()
    mapping = {
        "py": "Python",
        "python": "Python",
        "js": "Java",
        "javascript": "Java",
        "ts": "Java",
        "typescript": "Java",
        "json": "",
        "bash": "",
        "sh": "",
    }
    mapped = mapping.get(normalized, "")
    if not mapped:
        return ""
    return f"[language={mapped}]"


def _render_code_block(block: RenderBlock) -> str:
    begin = rf"\begin{{lstlisting}}{_listings_language(block.language)}"
    # Avoid accidentally terminating the listing environment from user input.
    safe_code = block.body.replace(r"\end{lstlisting}", r"\\end{lstlisting}")
    return "\n".join([begin, safe_code, r"\end{lstlisting}"])


def _render_content_blocks(text: str) -> list[str]:
    rendered: list[str] = []

    for block in _parse_content_blocks(text):
        if block.kind == "text":
            rendered_block = _render_text_block(block)
        elif block.kind in {"ulist", "olist"}:
            rendered_block = _render_list_block(block)
        elif block.kind == "heading":
            rendered_block = _render_heading_block(block)
        else:
            rendered_block = _render_code_block(block)

        if rendered_block:
            rendered.append(rendered_block)

    return rendered


def _render_article_header(article: ArticleContent, article_index: int, total_articles: int) -> str:
    return "\n".join(
        [
            r"\vspace{1.8mm}",
            r"\noindent\color{black!45}\rule{\linewidth}{0.55pt}",
            r"\vspace{1.2mm}",
            rf"\noindent\textbf{{\large Article {article_index}/{total_articles}}}\hfill\texttt{{{article.status_id}}}\\",
            rf"\textbf{{{latex_escape(article.author_name)}}} {latex_escape(article.author_handle)}\\",
            rf"\textit{{Published:}} {latex_escape(_date_display(article.published_at))}\\",
            rf"\textit{{Source:}} \url{{{article.url}}}",
            r"\vspace{1.6mm}",
        ]
    )


def _render_single_inline_image(image: LocalMedia) -> str:
    return "\n".join(
        [
            r"\begin{center}",
            rf"\includegraphics[width=0.84\columnwidth]{{\detokenize{{{_latex_path(image.local_path)}}}}}",
            r"\end{center}",
            r"\vspace{1.5mm}",
        ]
    )


def _render_single_span_image(image: LocalMedia) -> str:
    return "\n".join(
        [
            r"\begin{center}",
            rf"\includegraphics[width=0.72\textwidth]{{\detokenize{{{_latex_path(image.local_path)}}}}}",
            r"\end{center}",
            r"\vspace{2.4mm}",
        ]
    )


def _render_inline_flow(content_blocks: list[str], images: list[LocalMedia]) -> str:
    parts: list[str] = []
    image_index = 0

    for block_index, block in enumerate(content_blocks, start=1):
        parts.append(block)

        should_insert_image = block_index == 1 or block_index % 2 == 0
        if should_insert_image and image_index < len(images):
            parts.append(_render_single_inline_image(images[image_index]))
            image_index += 1

    while image_index < len(images):
        parts.append(_render_single_inline_image(images[image_index]))
        image_index += 1

    return "\n\n".join(parts)


def _article_block(
    article: ArticleContent,
    images: list[LocalMedia],
    config: LayoutConfig,
    *,
    article_index: int,
    total_articles: int,
) -> tuple[str, list[LocalMedia]]:
    header = _render_article_header(article, article_index, total_articles)
    content_blocks = _render_content_blocks(article.text)

    if config.image_layout == ImageLayoutMode.INLINE:
        body = "\n".join(
            [
                rf"\begin{{multicols*}}{{{config.columns}}}",
                header,
                _render_inline_flow(content_blocks, images),
                r"\end{multicols*}",
            ]
        )
        return body, []

    if config.image_layout == ImageLayoutMode.SPAN:
        body = "\n".join(
            [
                rf"\begin{{multicols*}}{{{config.columns}}}",
                header,
                "\n\n".join(content_blocks),
                r"\end{multicols*}",
                "\n".join(_render_single_span_image(image) for image in images),
            ]
        )
        return body, []

    body = "\n".join(
        [
            rf"\begin{{multicols*}}{{{config.columns}}}",
            header,
            "\n\n".join(content_blocks),
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

    for index, article in enumerate(contents, start=1):
        body_block, appendix = _article_block(
            article,
            media_map.get(article.status_id, []),
            config,
            article_index=index,
            total_articles=len(contents),
        )
        blocks.append(body_block)
        appendix_images.extend(appendix)

        if config.pagination == PaginationMode.NEWPAGE and index < len(contents):
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
