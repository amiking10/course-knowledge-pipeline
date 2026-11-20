# v0.4.3 — Evidence before automatic verification

## Goals

1. Prepare official OmniDocBench end-to-end evaluation inputs on a pinned evaluator revision.
2. Generate an auditable visual-evidence pack for the seven critically flagged scheduling slides.
3. Keep the original page and both extraction outputs side by side. No automated process can claim that a page has been human-verified.

## Actual course sample

Using the original six uploaded PDF lecture files, v0.4.1 database and QA report, a separate HTML/image comparison pack was generated locally for **seven critical pages** of `OS02-procs-sched (1).pdf`: 12, 13, 14, 18, 20, 28 and 30. Each contains original page artwork, the native text layer, extracted Docling text, retained hybrid text and a machine-suggested set of missing numeric strings.

At least page 28 visibly contains two Round Robin timelines with different time quanta and arrival constraints; an extracted title alone omits substantial worked-example material. The fallback adds the native text layer but does not encode all diagram geometry. Verification status remains **unreviewed**.

## New commands

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v041.sqlite3 visual-evidence "C:\Users\amita\Documents\University\OperatingSystems" data\critical-review --severity critical --limit 7
```

The resulting `data/critical-review/INDEX.html` opens without an AI account or paid API key. It contains original-page PNGs plus per-page extracted evidence.

After generating OmniDocBench predictions and preparing the subset JSON:

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-official-config data\benchmarks\omni200\OmniDocBench_subset.json data\benchmarks\omni200\docling\run.json data\benchmarks\omni200\official-docling --evaluator-commit FULL_40_CHARACTER_GITHUB_COMMIT_SHA
```

The `--evaluator-commit` must be the exact commit of the checked-out upstream scorer; the command only prepares and validates the configuration and does not fabricate a score.

## Next gates

- Run actual upstream scorer (text edit distance, TEDS, CDM and reading order) in its documented container/runtime, pinned to the same revision.
- Review and label at least 30 varied pages to quantify false negatives and false positives on the bilingual lecture corpus.
- Extract technical diagram relationships into structured, provenance-linked fields with separate machine-generated and human-approved statuses.
- Expand to representative public benchmark subset with confidence intervals.

**Do not merge to main as a quality-certified parser merely because CI passes.**
