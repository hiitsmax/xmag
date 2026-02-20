# ExecPlan: Playwright-First X Article to Three-Column LaTeX PDF (A4 Tight Magazine)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `~/.agents/PLANS.md`.

## Purpose / Big Picture

Build a Python CLI that reads a list of X article URLs and generates a LaTeX-style PDF with a three-column magazine layout and a very narrow outer margin.

## Progress

- [x] (2026-02-20 21:00Z) Confirmed workspace state and local tooling.
- [x] (2026-02-20 21:05Z) Gathered user intent and locked key behavior choices.
- [x] (2026-02-20 21:10Z) Verified current X access/policy context via official sources.
- [x] (2026-02-20 21:30Z) Implemented scaffold, CLI defaults, and typed config/models.
- [x] (2026-02-20 21:40Z) Implemented Playwright extraction with retry and fallback selection.
- [x] (2026-02-20 21:50Z) Implemented media staging, LaTeX rendering, and Tectonic compilation.
- [x] (2026-02-20 22:00Z) Added tests for parsing, rendering, extraction fixture, and compile smoke.
- [x] (2026-02-20 22:10Z) Completed final validation (`ruff`, `mypy`, `pytest`, CLI help).

## Surprises & Discoveries

- Observation: Local machine had `tectonic` installed but not `pdflatex`.
  Evidence: `command -v tectonic` returned `/opt/homebrew/bin/tectonic`; `command -v pdflatex` returned not found.
- Observation: Workspace started completely empty and not version-controlled.
  Evidence: `ls -la` had no files and `git rev-parse --is-inside-work-tree` failed.
- Observation: Jinja template parsing is sensitive to LaTeX brace escaping and failed initially when using `{{` around raw LaTeX braces.
  Evidence: `TemplateSyntaxError: unexpected char '\\'` in initial test run.

## Decision Log

- Decision: Use Playwright as sole extraction backend.
  Rationale: Explicit user direction to avoid API-first path.
  Date/Author: 2026-02-20 / Codex + User
- Decision: Keep defaults at A4 three-column tight-mag while exposing all layout knobs through CLI.
  Rationale: Matches required output style with operational flexibility.
  Date/Author: 2026-02-20 / Codex + User
- Decision: Implement all pagination modes and all image layout modes as CLI enums.
  Rationale: User explicitly requested selectable modes.
  Date/Author: 2026-02-20 / Codex + User
- Decision: Add strict typing validation (`mypy`) and dateutil stubs before finalizing.
  Rationale: Prevent regressions in strict static checks required by repo tooling.
  Date/Author: 2026-02-20 / Codex

## Outcomes & Retrospective

Completed deliverable:

- `xmag` CLI now builds three-column LaTeX-style PDFs from URL lists.
- Extraction, rendering, media download, and Tectonic compile are integrated.
- All planned pagination and image layout modes are implemented.
- Full test suite is present and passing.

Remaining risks:

- X selector drift can break extraction over time.
- Non-public content depends on valid browser storage state.

Lessons learned:

- Keep LaTeX/Jinja boundary simple and avoid mixed brace syntax.
- Include strict type checks early to avoid late-stage cleanup.

## Context and Orientation

Project files are under `src/xmag`:

- `cli.py`: Typer command surface.
- `input.py`: URL parsing and file ingestion.
- `extractor.py`: Playwright extraction logic.
- `media.py`: image normalization/download.
- `renderer.py` + `templates/issue.tex.j2`: LaTeX generation.
- `compiler.py`: Tectonic invocation.
- `builder.py`: end-to-end orchestration.

Tests are under `tests/` and codex learning artifacts are under `docs/codex/`.

## Plan Revision Note

2026-02-20: Converted chat-level plan into a tracked repository ExecPlan and updated progress to reflect implemented milestones.
2026-02-20: Updated final validation status, discoveries, and retrospective after implementation completion.
