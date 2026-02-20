# xmag

Convert a list of X/Twitter article URLs into a polished, magazine-style LaTeX PDF.

## Vibecoded Note

This project is **vibecodato** (vibe-coded), meaning it was built with strong AI-assisted iteration and human direction.

## What It Does

- Extracts long-form content from X/Twitter status pages (Playwright-first).
- Renders content in a three-column PDF layout.
- Supports article-level separators, index page, and optional blank cover page.
- Handles images with multiple placement strategies.
- Compiles with Tectonic for reproducible LaTeX output.

## Features

- URL file input (one URL per line).
- Configurable layout: paper, margins, columns, column gap.
- Pagination modes:
  - `continuous`
  - `newpage`
  - `split` (one PDF per article)
- Image layout modes:
  - `inline`
  - `span`
  - `appendix`
- Optional `--blank-first-page`.
- Optional `--index-page` (generated index with clickable article references).
- Optional `--storage-state` for authenticated browser contexts.

## Project Structure

- `src/xmag/cli.py`: CLI entrypoint (`xmag build ...`)
- `src/xmag/input.py`: URL parsing and ingestion
- `src/xmag/extractor.py`: Playwright extraction + sanitization
- `src/xmag/media.py`: image download/normalization
- `src/xmag/renderer.py`: LaTeX content rendering
- `src/xmag/templates/issue.tex.j2`: document template
- `src/xmag/compiler.py`: Tectonic compilation wrapper
- `src/xmag/builder.py`: end-to-end orchestration
- `tests/`: parsing, extraction, rendering, compile tests
- `docs/codex/`: research notes, selector notes, autonomous testing notes
- `docs/USER_GUIDE.md`: complete usage guide

## Requirements

- Python `>= 3.12`
- Tectonic (`tectonic` in `PATH`)
- Chromium (installed via Playwright)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

## Input File Format

Create `urls.txt` with one status URL per line:

```text
https://x.com/user/status/1234567890123456789
https://twitter.com/another/status/9876543210987654321
```

Comments and blank lines are allowed.

## Basic Usage

```bash
xmag build --url-file /absolute/path/urls.txt --output /absolute/path/magazine.pdf
```

## Common Examples

```bash
# Add blank first page + index page
xmag build --url-file urls.txt --output issue.pdf --blank-first-page --index-page

# Keep all articles in one flow
xmag build --url-file urls.txt --output issue.pdf --pagination continuous

# Force each article to a new page
xmag build --url-file urls.txt --output issue.pdf --pagination newpage

# Generate one PDF per article
xmag build --url-file urls.txt --output issue.pdf --pagination split

# Put images inline in columns
xmag build --url-file urls.txt --output issue.pdf --image-layout inline

# Put images between text blocks at page width ratio
xmag build --url-file urls.txt --output issue.pdf --image-layout span

# Put all images in an appendix
xmag build --url-file urls.txt --output issue.pdf --image-layout appendix

# Use authenticated browser session
xmag build --url-file urls.txt --output issue.pdf --storage-state /absolute/path/state.json
```

## Defaults

- Paper: `a4`
- Columns: `3`
- Outer margin: `4mm`
- Inner margin: `9mm`
- Top/bottom margins: `10mm`
- Column gap: `4mm`
- Pagination: `newpage`
- Image layout: `inline`
- Blank first page: `false`
- Index page: `false`

## Development

```bash
ruff check .
mypy src
pytest -q
```

## Troubleshooting

- `Build failed: ... Could not find usable text nodes in article`
  - X frontend structure changed; update selectors in `src/xmag/extractor.py`.
- `Tectonic not found`
  - Install Tectonic and ensure `tectonic` is in your `PATH`.
- Private/restricted posts not accessible
  - Export Playwright storage state and pass `--storage-state`.

## Notes

- Extraction targets publicly accessible content by default.
- X DOM can change over time; maintenance on selectors is expected.
- This tool focuses on readable export workflows, not platform mirroring.

## Full Documentation

See `docs/USER_GUIDE.md` for complete operational docs.
