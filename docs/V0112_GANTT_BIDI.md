# v0.11.2 — Cross-block Gantt and bilingual validation (experimental)

Non-destructive extension of v0.11.1. Uses original PDF word coordinates even where process labels and timestamps live in separate PDF blocks. Proposes Gantt interval candidates and checks their candidate durations against source process tables. Preserves contiguous English word runs such as 'convoy effect' inside Hebrew lines.

## Run on the seven source scheduling pages

```powershell
git fetch origin
git switch --track origin/feature/v0.11.2-gantt-bidi-validation
.\.venv\Scripts\python.exe -m pip install -e ".[inspect,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course-v041.sqlite3" reconstruct-structures "C:\Users\amita\Documents\University\OperatingSystems" "data\structural-v011\STRUCTURAL_RECOVERY.json" "data\structural-v0112" --limit 7
```

The command is offline and does not call Gemini. It emits STRUCTURAL_RECONSTRUCTION.json and STRUCTURAL_RECONSTRUCTION.html. JSON schema_version is 0.11.2 with fields bilingual_rtl_candidates, cross_block_gantt_candidates, cross_block_consistency_checks.

## Accuracy safeguards

- Source PDF hashes and stored SQLite extraction hashes must match the earlier v0.11 report.
- The original PDF files, SQLite pages, search indexes, and published study exports remain unchanged.
- A process label between numeric ticks is only a geometric hypothesis, not a visually verified Gantt block.
- Runtime table agreement is a consistency check on two proposed structures, not independent correctness proof.
- Only contiguous plain Latin word tokens are reordered within Hebrew lines; mixed punctuation and semantic reading order still require validation.
- Rasterized diagrams or multi-track schedules may remain unresolved. The next gate is measuring candidate coverage and false associations on the seven real scheduling pages.
