# Pre-freeze repository cleanup — 2026-11-21

**Target:** reliable first-time Windows onboarding for a local UNI-VERSE CLI + manual ChatGPT Projects export; not a hosted product. Freeze status: pending exact-commit CI and a clean-machine, real-course acceptance test.

- Replaced a sprawling README with a single beginner path from Git/Python installation through cloning, parser setup, source-file placement, package generation, ChatGPT Project instructions and refresh.
- Added `scripts/setup_windows.ps1` to create the virtual environment, install Docling and dependencies, check the import and run a real parser smoke test; it fails visibly on errors.
- Added a guard against using this Git checkout itself as the source folder, preventing accidental inclusion of private course data in the repository.
- Standardized **one** generated per-course `INTERNAL/PROJECT_INSTRUCTIONS.md` as the only supported ChatGPT Project Instructions content, and removed the superseded static `docs/CHATGPT_PROJECT_INSTRUCTIONS.md`.
- Moved 29 historic validation/release/phase files into `docs/history/` without changing their content; see `docs/HISTORY.md`. The current architecture, setup, troubleshooting and release checklist remain at the top of `docs/`.
- Updated the architecture, AI integration guide, Windows CI PowerShell syntax checks and onboarding regression tests.
- Maintained a non-destructive approach to executable experimental modules, migration tools and database formats. The public release remains unapproved pending validation; do not conflate the passing package gate with correctness of PDF formulas/diagrams.

---

# UNI-VERSE v0.12.0 — Local alpha release hardening

**Scope:** Local-first CLI and AI-ready course export. Not a hosted web application or certified AI tutoring product.

- Rewrote README as a product overview, quickstart, real workflow, exported-file upload guide, architecture and honest limitations.
- Added a copy-ready set of ChatGPT Project instructions and expanded AI integration / architecture / data model guides.
- Added a non-mutating **verify-export** CLI gate that checks the local manifest against active parsed SQLite sources, original-page Markdown headings, visual PDF archive and mapping, and reports unresolved QA warnings.
- The end-to-end PowerShell script now runs export validation and exits on an incomplete package.
- Added automated regression coverage for valid packages, missing source-page text, stale sources, corrupted manifests, missing visual archive and incorrect archive page mapping.
- Updated Git ignore rules for course documents, credentials and SQLite journal files.
- Added a P0 demo / P1 private alpha / P2 public launch readiness checklist.

**Validation status:** Synthetic and CI tests verify code behavior. External student UX, ChatGPT Project end-to-end answer accuracy and visual formula/diagram fidelity remain unverified. This release is not production-certified.

**Repository:** The proposed consolidated integration into main is PR #18. The older sections below are archived historical records; they do not describe the current implementation accurately.

---

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
- Optional Windows Task Scheduler registration for a daily local incremental run (requires an explicit user command).

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
