# v0.4.1 — Token-aware extraction comparison and review triage

## Test corpus and measured results
Input: six supplied Operating Systems PDFs (214 pages), using the previously generated Docling v0.3 Markdown and an independent native PDF text extraction. This is NOT a fresh full Docling run.

| Measure | v0.4 baseline | v0.4.1 |
|---|---:|---:|
| Pages represented | 214 | 214 |
| Flagged pages | 75 | 86 |
| Critical | Not available | 7 |
| Major | Not available | 54 |
| Minor | Not available | 14 |
| Informational | Not available | 11 |
| Known recovery pages with native text | 12/12 | 12/12 |

A higher count of flags is not automatically worse: v0.4.1 detects potential missing tokens even when character lengths are similar. All flags are unverified and some are false positives.

## Implemented
- Unicode NFKC and bidirectional-control normalization for Hebrew and Latin text.
- Token-multiset comparison insensitive to word order.
- Secondary evidence retained when likely missing or ambiguous; originals remain authoritative.
- Numeric-expression review heuristic for criticality; no mathematical correctness guarantee.
- Severity-ordered JSON/HTML QA report and visual review queue.
- Parser cache version bump to avoid silently reusing stale classifications.
- Additional unit tests (including RTL controls, word order, numeric omission, priority sorting).

## Remaining gates
- Manually label false-positive/true-positive status on a representative stratified sample of pages.
- Verify Hebrew RTL reading order, formulas, tables, diagrams and full Docling on all sources.
- Benchmark ≥30 verified gold questions, including diagrams and questions absent from files.
- No direct ChatGPT Projects retrieval accuracy has been demonstrated.

## How to test
Use a **new database/output** so v0.4 remains available for comparison:

```powershell
git fetch origin
git switch feature/v0.4.1-disagreement-triage
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\upgrade_v03_export.ps1 -SourceDir "C:\Users\amita\Documents\University\OperatingSystems" -PriorExportDir ".\data\chatgpt-export" -DatabasePath "data\course-v041.sqlite3" -Output "data\chatgpt-export-v041"
```
