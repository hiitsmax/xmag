# xmag

Convert a list of X article URLs into a three-column LaTeX-style PDF.

## Features

- Playwright-first extraction for X/Twitter status URLs.
- Three-column magazine layout with tight outer margin defaults.
- Selectable pagination modes: `continuous`, `newpage`, `split`.
- Selectable image layout modes: `span`, `inline`, `appendix`.
- Tectonic-based LaTeX compilation for deterministic PDF output.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

Create a URL file (`urls.txt`) with one status URL per line:

```text
https://x.com/user/status/1234567890
https://twitter.com/another/status/9876543210
```

Generate a PDF:

```bash
xmag build --url-file /absolute/path/urls.txt --output /absolute/path/magazine.pdf
```

## CLI Examples

```bash
# Force page break between articles
xmag build --url-file urls.txt --output issue.pdf --pagination newpage

# Split mode: one PDF per article
xmag build --url-file urls.txt --output issue.pdf --pagination split

# Inline images inside columns
xmag build --url-file urls.txt --output issue.pdf --image-layout inline

# Use authenticated browser state for restricted content
xmag build --url-file urls.txt --output issue.pdf --storage-state /absolute/path/state.json
```

## Defaults

- Paper: `a4`
- Columns: `3`
- Outer margin: `4mm`
- Inner margin: `9mm`
- Top/bottom margins: `10mm`
- Column gap: `4mm`
- Pagination: `continuous`
- Image layout: `span`

## Development

```bash
ruff check .
mypy src
pytest -q
```

## Notes

- Extraction targets public content by default.
- DOM selectors may drift as X changes its frontend.
- See `docs/codex/` for autolearning notes, selector strategy, and test autonomy guidance.
