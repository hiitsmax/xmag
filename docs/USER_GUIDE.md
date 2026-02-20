# xmag User Guide

## 1. Overview

`xmag` converts X/Twitter status URLs into a LaTeX-generated PDF with a dense editorial layout.

Primary output goals:
- consistent print-ready structure,
- readable multi-column pages,
- deterministic PDF generation,
- configurable pre-content pages (blank cover, index).

## 2. End-to-End Flow

1. Read URL list.
2. Parse/validate status IDs.
3. Extract article content with Playwright.
4. Sanitize noisy UI artifacts.
5. Download media assets.
6. Render LaTeX content.
7. Compile via Tectonic.

## 3. Command Reference

Main command:

```bash
xmag build --url-file <path> --output <path>
```

Important options:
- `--pagination [continuous|newpage|split]`
- `--image-layout [inline|span|appendix]`
- `--blank-first-page`
- `--index-page`
- `--storage-state <path>`
- `--keep-tex`

Layout options:
- `--paper [a4|letter]`
- `--columns <int>`
- `--outer-margin-mm <float>`
- `--inner-margin-mm <float>`
- `--top-margin-mm <float>`
- `--bottom-margin-mm <float>`
- `--column-gap-mm <float>`

## 4. Recommended Preset

For magazine-like output:

```bash
xmag build \
  --url-file urls.txt \
  --output magazine.pdf \
  --blank-first-page \
  --index-page \
  --pagination newpage \
  --image-layout inline
```

## 5. Input Rules

`urls.txt` format:
- one URL per line,
- supports `x.com` and `twitter.com`,
- duplicate status IDs are deduplicated,
- lines beginning with `#` are ignored.

## 6. Private Content

If content requires login:
1. capture Playwright storage state,
2. pass `--storage-state /path/state.json`.

## 7. Output Behavior

- `continuous`: one uninterrupted issue.
- `newpage`: each article starts on a new page.
- `split`: one PDF file per article.

Images:
- `inline`: images interleaved in column flow.
- `span`: larger between text sections.
- `appendix`: moved to final appendix.

## 8. Quality and Stability

To validate changes:

```bash
ruff check .
mypy src
pytest -q
```

Extraction may need periodic selector tuning as X markup changes.

## 9. Known Constraints

- Rendering quality depends on source text structure from X.
- Very long URLs can still create line breaks despite URL handling.
- Source HTML volatility is expected.

## 10. Vibecoded Disclosure

This project is vibecodato: developed through iterative AI-assisted coding with explicit human direction and review.
