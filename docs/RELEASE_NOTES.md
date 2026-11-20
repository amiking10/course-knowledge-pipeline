# v0.3 local diagnostic release

## Functionality
- Register and track PDF/PPTX/DOCX originals locally, detect changes with SHA-256.
- Parse with Docling when installed; PyMuPDF is an explicitly labelled PDF-only diagnostic fallback.
- Flag potential extraction issues, render visual pages for review.
- Create manually reviewable page-linked enrichment records and optional vision drafts; only reviewed notes can enter exports.
- Find text using FTS5, character n-gram TF-IDF ranking, or optional cached multilingual embeddings.
- Export compact Markdown bundles and a source manifest for ChatGPT Projects.
- Benchmark page retrieval using an independently curated expected-source/page dataset.
- Incrementally reparse new/modified/changed-backend files, exclude stale pages from exports.

## Validated results on six uploaded PDFs
- Six PDF documents, 214 total pages (diagnostic parser only).
- Seven heuristically flagged events; their presence is not a measured error rate.
- 18 tests passed, one real-Docling smoke test skipped locally including the actual six-PDF integration test.
- 22 unreviewed retrieval candidates: hit@5 12/22, MRR 0.333 on final test.
- Two Markdown bundles plus an inventory, JSON manifest and 214-page bookmarked original PDF archive.

## Unresolved production blockers
- Docling installation/execution unavailable in current runtime.
- Hebrew RTL extraction from the diagnostic backend demonstrably mishandles ordering.
- Visual understanding, equation transcription and semantic grounding require human validation.
- Vision calls not run; only the validated adapter and manual review schema are shipped.
- Real ChatGPT Project Q&A not evaluated, only the export format.
- GitHub branch currently contains earlier scaffolding; this local release archive must be synchronized to complete the PR.

## Remote validation
GitHub CI matrix runs on Windows/Linux with Python 3.11/3.12; a dedicated Docling smoke job checks synthetic page provenance. Do not equate synthetic parser validation with the six real lecture PDFs.
