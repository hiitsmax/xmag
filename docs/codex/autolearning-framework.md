# Autolearning Framework for xmag

## Goal

Keep extraction and rendering quality improving over time by capturing failures, selector drift, and layout regressions in a repeatable loop.

## Loop

1. Run deterministic checks:
   - `pytest -q`
   - `python -m xmag.cli build ...` on a known URL fixture list.
2. Record failures in `docs/codex/playwright-selector-notes.md` or test notes.
3. Add or update:
   - Extraction selectors.
   - Unit/integration tests for the new breakage pattern.
   - LaTeX rendering snapshots when output format changes.
4. Re-run tests and keep the record of what changed.

## Project Learning Artifacts

- `docs/codex/research-x-access-and-playwright.md`: access policy and implementation rationale.
- `docs/codex/playwright-selector-notes.md`: selector strategy and drift handling.
- `docs/codex/test-autonomy.md`: reproducible autonomous test flows.
- `docs/codex/execplan-playwright-xmag.md`: living execution plan and decisions.

## Maintenance Cadence

- Per feature or bugfix: update at least one learning artifact.
- Per selector drift incident: add a failing fixture and fixed selector note.
- Per rendering change: add coverage in `tests/test_tex_generation.py`.
