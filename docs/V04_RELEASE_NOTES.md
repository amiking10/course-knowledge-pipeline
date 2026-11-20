# v0.4 candidate release

- Non-destructive hybrid extraction: preserve primary Docling text and independently recovered native PDF text, with explicit review labels.
- New `COURSE_INDEX.md`/`COURSE_INDEX.json` evidence-matched topic navigation.
- New `QUALITY_REPORT.html`/`QUALITY_REPORT.json` and `review/review_queue.json`.
- `scripts/run_pipeline.ps1` defaults to hybrid backend and no longer conflicts with PowerShell's `-Debug` alias.
- Parser cache invalidated to recompute after v0.3 -> v0.4 upgrade.
- Regression tests for dual-source extraction, source preservation, HTML escaping, review queue and topic mapping.

**Not production-certified:** 73 pages flagged on the supplied corpus, and measured candidate retrieval performance below the 95% target. See `docs/V04_VALIDATION.md`.
