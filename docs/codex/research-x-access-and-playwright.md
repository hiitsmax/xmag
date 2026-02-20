# Research: X Access Conditions and Playwright Fallback

## Date

2026-02-20

## Summary

Implementation is Playwright-first and excludes X API calls by decision. The main reasons were uncertain free-tier availability and explicit preference to avoid paid API flow.

## Sources Reviewed

- X API pricing: https://docs.x.com/x-api/fundamentals/pricing
- X legacy support tiers: https://developer.x.com/en/support/x-api/v2
- X automation policy: https://help.x.com/en/rules-and-policies/x-automation

## Practical Outcome for this Repo

- No API tokens are required.
- Content extraction is implemented with Playwright selectors.
- Docs keep a note that automation policy may change and selector updates are expected.

## Risk Notes

- Frontend DOM and data-testid attributes can change.
- Some posts may require authenticated sessions.
- Policy constraints can affect allowed scraping behavior; usage should remain compliant.
