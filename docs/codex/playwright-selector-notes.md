# Playwright Selector Notes

## Primary Selectors

- Article container: `article`
- Anchored article match: `article:has(a[href*="/status/<id>"])`
- Text: `[data-testid="tweetText"]`
- Author: `[data-testid="User-Name"]`
- Timestamp: `time[datetime]`
- Media: `img[src*="twimg.com/media"]`

## Fallback Strategy

1. Wait for any `article`.
2. Prefer article containing anchor with target status id.
3. Fall back to first article if exact anchor is not found.

## Drift Response

When selectors break:

1. Capture failing HTML or screenshot.
2. Add/update fixture under `tests/fixtures/`.
3. Update parser and test in `tests/test_extractor_with_fixture_html.py`.
4. Document the change in this file.

## Authenticated Context

Use `--storage-state <path>` if a public page is inaccessible.
