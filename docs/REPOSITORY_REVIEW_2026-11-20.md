# UNI-VERSE repository review — 2026-11-20

## Scope and verification level

Reviewed the course source registry, CLI/PowerShell workflow, parsers, hybrid reconciliation, source-index/knowledge generation, retrieval, export, validation, tests, CI, package metadata and user documentation. This is a targeted engineering audit and set of corrections, **not** a certification of every algorithm or an end-to-end test on the user's local PDFs. Continuous integration and a Windows RX_TX run are separate validation gates.

## Corrected in feature/uni-verse-course-workflow

| Concern | Severity | Change |
|---|---|---|
| OS topic headings appearing in RX_TX indexes | High | Replaced hardcoded OS index defaults with words evidenced in *this course's* currently active pages. Explicit legacy `COURSE_TERMS` remains for opt-in callers. |
| OS query synonyms applied to all courses | High | Synonym expansion is now opt-in; general retrieval uses the query as supplied. |
| Accidental shared SQLite database | High | `source_root` binding rejects scanning a different course through the same DB. Legacy unbound DBs must match original source bytes before binding. |
| Stale/copied upload indexes could pass presence-only verification | High | `--strict-indexes` regenerates both indexes from the DB in a temporary directory and compares exact Markdown contents. The PowerShell workflow enables this by default. |
| Incorrect Unicode topic-token regex in initial isolation patch | High | Corrected letter-only matching for Hebrew/English and excluded parser boilerplate terms. |
| Rapid iterative commits creating redundant CI jobs | Medium | Added workflow concurrency cancellation for superseded push / PR executions. |
| Unclear shared-database instructions | Medium | Updated README to use a per-course database and strict validation. |

## Current contract

- One original lecture source root corresponds to one SQLite course database.
- Each course exports into `data/courses/<course>/UPLOAD_TO_CHATGPT` and `INTERNAL`.
- The script scans source file hashes and reparses only changed/missing-stale content.
- Indexes are generated from current active course source pages; their terms are *lexical*, not validated conceptual or hierarchical topics.
- A strict export integrity check fails on stale indexes, mismatched source hashes, missing page citations or missing required PDF archive.
- Manual ChatGPT Project upload remains required; it is not a live SQLite connection.

## Remaining important work, ordered by impact

1. **Independent extraction quality:** Evaluate Hebrew right-to-left text, tables, formulas and diagrams on a human-reviewed sample, and expand official benchmarks beyond six pages. Integrity checks cannot prove semantic correctness.
2. **True content-aware topics:** Current topic selection ranks repeated unigrams, not coherent course concepts. Add section/heading-aware extraction plus explicit concept evaluation before describing indexes as semantic.
3. **Visual completeness:** The bookmarked visual archive includes PDF originals only. PPTX and DOCX originals need separate conversion or explicit required uploads, with provenance.
4. **Incremental performance:** Page hashes avoid re-parsing unchanged files, but source scans still rehash all inputs and most topic/index outputs are rebuilt. Profile cold/warm runs and consider cached corpus fingerprints before optimizing further.
5. **Retrieval benchmarks:** Test cross-course questions, Hebrew/English equivalence and measured hit@k, MRR, latency and token usage. Current CLI retrieval is separate from ChatGPT Projects' internal retrieval.
6. **Operational packaging:** The CLI contains many experimental/research commands; modularize by domain and document stable vs experimental commands only after the CI regression suite is green.
7. **Distribution and security:** No declared project license, release/privacy terms, application authentication, or hosted multi-user security boundary. Gemini vision remains explicitly opt-in; review external sharing consent before any production distribution.
8. **End-to-end Windows acceptance:** Run the PowerShell script separately on real OS and RX_TX directories, verify different indexes and hashes, add a lecture to RX_TX, and verify unchanged PDFs skip parsing without altering OS outputs.

## Acceptance commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\RX_TX" -Backend hybrid -WithVisualPDF
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\courses\RX_TX\INTERNAL\course.sqlite3" verify-export "data\courses\RX_TX\UPLOAD_TO_CHATGPT" --source-dir "C:\Users\amita\Documents\University\RX_TX" --quality-report "data\courses\RX_TX\INTERNAL\QUALITY_REPORT.json" --strict-indexes --require-visuals
```

A successful verification ensures structural consistency and **course-specific index freshness**, not accurate OCR/formulas or better AI answers. Keep the old and new exports out of the same ChatGPT Project until obsolete files have been removed.
