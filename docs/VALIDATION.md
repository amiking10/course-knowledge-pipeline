# Validation record, 2026-11-20

- Source corpus: 6 PDF lecture/tutorial files for Operating Systems 046209; **214 pages**.
- Diagnostic parser: **PyMuPDF**, because Docling was not installed and a network installation was unavailable.
- Extracted: 6 sources, 214 page records, **7 heuristic warning events**. Heuristic events do not equal confirmed extraction errors.
- Search: FTS5 and char TF-IDF hybrid; sample `interrupt IDT` finds tutorial 2 page 9 first.
- Export: 2 Markdown bundles, `INDEX.md`, JSON manifest; original figures are not embedded in these bundles.
- Benchmark: 22 source/page **candidate** queries, unreviewed, hit@5 **12/22 (54.5%)**, MRR approximately **0.333**. This is a deliberately difficult cross-language baseline, **not** an answer-accuracy measurement.
- Unit tests: 16 passing with real-corpus integration (including stale-file exclusion, page split provenance, QA, enrichment schema, retrieval benchmark, and rendering).

## Known blockers for production sign-off

1. Install and run the actual Docling parser on the six original files.
2. Review Hebrew right-to-left ordering on extracted slides. Current diagnostic strings visibly reorder words.
3. Verify all mathematical equations, circuit figures and visual-only slide content against renders.
4. Test optional vision API output with manual review and budget controls.
5. Test real ChatGPT Project ingestion and answer/citation quality; local retrieval results cannot substitute for that test.
6. Run Windows CI and compare Docling behavior across versions.
