"""Typer CLI entrypoint for xmag."""

from __future__ import annotations

from pathlib import Path

import typer
from pydantic import ValidationError

from xmag.builder import build_issue
from xmag.config import ImageLayoutMode, LayoutConfig, PaginationMode, PaperSize

app = typer.Typer(help="Convert X article URLs into a three-column LaTeX-style PDF.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """xmag command group."""


@app.command()
def build(
    url_file: Path = typer.Option(..., exists=True, readable=True, dir_okay=False),
    output: Path = typer.Option(..., dir_okay=False),
    pagination: PaginationMode = typer.Option(PaginationMode.CONTINUOUS),
    image_layout: ImageLayoutMode = typer.Option(ImageLayoutMode.SPAN),
    paper: PaperSize = typer.Option(PaperSize.A4),
    columns: int = typer.Option(3, min=1, max=6),
    outer_margin_mm: float = typer.Option(4.0),
    inner_margin_mm: float = typer.Option(9.0),
    top_margin_mm: float = typer.Option(10.0),
    bottom_margin_mm: float = typer.Option(10.0),
    column_gap_mm: float = typer.Option(4.0),
    headless: bool = typer.Option(True, "--headless/--no-headless"),
    storage_state: Path | None = typer.Option(None, exists=True, dir_okay=False),
    timeout_seconds: int = typer.Option(30, min=5, max=180),
    continue_on_error: bool = typer.Option(False),
    keep_tex: bool = typer.Option(False),
) -> None:
    """Build one or more magazine-style PDFs from X status URLs."""

    try:
        config = LayoutConfig(
            paper=paper,
            columns=columns,
            outer_margin_mm=outer_margin_mm,
            inner_margin_mm=inner_margin_mm,
            top_margin_mm=top_margin_mm,
            bottom_margin_mm=bottom_margin_mm,
            column_gap_mm=column_gap_mm,
            pagination=pagination,
            image_layout=image_layout,
        )
    except ValidationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    try:
        report = build_issue(
            url_file=url_file,
            output=output,
            config=config,
            headless=headless,
            storage_state=storage_state,
            timeout_seconds=timeout_seconds,
            continue_on_error=continue_on_error,
            keep_tex=keep_tex,
        )
    except Exception as exc:
        typer.echo(f"Build failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Processed {report.total} URL(s): {report.succeeded} succeeded, {report.failed} failed."
    )
    for path in report.outputs:
        typer.echo(f"Output: {path}")

    if report.failures:
        typer.echo("Failures:", err=True)
        for failure in report.failures:
            typer.echo(f"- {failure}", err=True)
