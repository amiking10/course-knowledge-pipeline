# v0.9 — Opt-in formula enrichment

- Added separate `docling-formula` and `hybrid-formula` backends.
- Explicitly enables Docling PDF formula enrichment and table recognition when chosen.
- Labeled formulas receive display-math delimiters for downstream Markdown/evaluator recognition.
- Empty formula items are flagged instead of silently omitted.
- New regression tests and versioned parser cache.
- Formula-enriched public six-page benchmark workflow uses the same source revision and pinned official evaluator image digest as the baseline.

The v0.9 experiment must be evaluated before asserting fidelity gains.
