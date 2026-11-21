# v0.10 — Cloud vision audit (development)

- Gemini opt-in cloud audit validates original rendered PDF pages against stored extraction with a structured JSON discrepancy schema.
- Default zero-request dry run; `--live` required; hard API attempt cap (default seven), no automatic retries or model fallback.
- SHA-256 based cache, privacy-preserving output, source-change detection and explicit uncertainty and human-verification disclaimers.
- Original-PDF and SQLite data never overwritten.
- Automated cross-platform mock regression tests.
- Local API key required for live evaluation; API charges and free-tier access must be confirmed separately.
