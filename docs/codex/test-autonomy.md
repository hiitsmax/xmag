# Autonomous Testing Notes

## Local Deterministic Loop

Run from repository root:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    python -m playwright install chromium
    pytest -q

## End-to-End Build Smoke

Use a URL list file (`urls.txt`, one URL per line):

    xmag build --url-file /absolute/path/urls.txt --output /absolute/path/magazine.pdf --pagination continuous --image-layout span

## MCP/Playwright Automation Suggestions

- Script a recurring browser extraction smoke that checks one known public URL and validates non-empty text extraction.
- Capture generated PDF size and checksum to detect regressions in output production.
- Add a periodic selector health check that opens X, verifies expected nodes, and reports drift.

## CI Recommendations

- Install Chromium via Playwright in CI before tests.
- Keep `tests/test_compile_smoke.py` enabled where `tectonic` is present.
- Store failed `.tex` artifacts when compile fails to debug layout regressions.
