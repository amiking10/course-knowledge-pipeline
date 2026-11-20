# Architecture and trust boundaries

- **Input:** Original PDFs, PPTX, DOCX, kept outside git and retained as primary evidence.
- **Phase 1:** SHA-256 registry and stable per-path UUIDs, missing/changed detection.
- **Phase 2:** Docling backend. A separate explicit `pymupdf-diagnostic` backend is only suitable for evaluating pipeline wiring, *not* visual or RTL fidelity.
- **Phase 3:** Page completeness, low-text, replacement-character and image-review warnings. No heuristic guarantees correct understanding.
- **Phase 4:** Manual and optional AI vision notes with required source/page/evidence/review-state. Draft AI notes are never silently substituted for lecture text.
- **Phase 5:** SQLite FTS5 and offline character n-gram TF-IDF hybrid retrieval. TF-IDF is **not** an embedding model; accuracy on Hebrew/English cross-language queries can be weak.
- **Phase 6:** Page-anchored Markdown + JSON manifest + bookmarked merged visual PDF to add manually to a ChatGPT Project. The SQLite index is **not transferred** into ChatGPT's internal retriever.
- **Phase 7:** Ground-truth exact-source-page retrieval benchmark; gold set must be human reviewed, not just automatically generated.
- **Phase 8:** Changes to source SHA-256 or parser-version invalidate stale pages. Stale content is excluded from search/export until reparsed.

## Integrity requirements

1. The source bytes and original page number always take priority over AI inferences.
2. Never export a source if its last parsed SHA differs from its active file SHA.
3. Never call a document complete solely because it has text on every page.
4. Never upload copyrighted/private lecture originals to a public GitHub repository.
5. Query results from the diagnostic backend require manual verification against the source page.
6. The system cannot claim a full Docling validation until that dependency is installed and run.
