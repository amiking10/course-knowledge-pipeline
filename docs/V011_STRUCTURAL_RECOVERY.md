# v0.11 — Structural recovery evidence (development)

## Objective

Resolve recurring document-structure problems identified in the seven critical Operating Systems lecture slides. The first implementation is **conservative evidence recovery**, not automatic overwriting: it extracts original PDF word coordinates and candidate visual orders, native PDF table cells when available, and geometrically associated process labels and time ticks as candidate scheduling timelines. It cross-references the existing Gemini audit as **unverified hypotheses**. This preserves original pages and avoids inventing a Gantt schedule from disconnected labels.

## What the implementation does

- Collects per-token PDF bounding boxes with both left-to-right and right-to-left ordering candidates for Hebrew-dominant lines. Does **not** blindly reverse stored text. Mixed Hebrew/English and reversed glyph encodings require subsequent semantic validation.
- Extracts native vector table rectangles and cell contents where PyMuPDF `find_tables` succeeds. Retains unknown column orientation and never manufactures cells.
- Detects candidate vector-drawn Gantt process intervals only when a rectangle contains exactly one process label and both time ticks align with its left/right boundaries. These are geometrically supported but **still not semantically verified**; raster slides may yield no vector intervals.\n- Identifies geometrically nearby process labels (`p1`, `p2`, `T1`, etc.) and monotonically ordered time-tick rows. **No time-to-process intervals are assigned** unless reliable subsequent evidence is available.
- Joins issue hypotheses from `GEMINI_QA_REPORT.json` only after verifying the exact source PDF SHA-256. Unrelated audit source hashes are rejected.
- Saves `STRUCTURAL_RECOVERY.json` and `STRUCTURAL_RECOVERY.html`. Keeps existing SQLite parser text, FTS, PDF originals and exports untouched.
- Escapes untrusted model text in HTML, rejects modified source PDF hashes and excludes stale parses.

## Windows execution

Use the existing source PDFs, v0.4.1 SQLite database and the seven-page Gemini report on the same machine:

```powershell
cd "C:\Users\amita\Documents\course-knowledge-pipeline"
git fetch origin
git switch --track origin/feature/v0.11-structural-recovery
.\.venv\Scripts\python.exe -m pip install -e ".[inspect,dev]"
.\.venv\Scripts\python.exe -m pytest -q

.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course-v041.sqlite3" structural-recovery "C:\Users\amita\Documents\University\OperatingSystems" "data\structural-v011" --audit-report "data\gemini-audit-v010\GEMINI_QA_REPORT.json" --severity critical --limit 7
```

If the branch already exists locally, use `git switch feature/v0.11-structural-recovery` and `git pull --ff-only`.

Inspect `data\structural-v011\STRUCTURAL_RECOVERY.html` and share the JSON for measured next-step prioritization. The command is **fully offline** and makes no Gemini API calls.

For a broader diagnostic across all PDFs, select `--severity all --limit 214`, but the seven-page pilot should be inspected first. No structural proposal may be presented as a confirmed correction unless independently supported by original source evidence.

## Acceptance limits

- This release **does not claim improved Hebrew semantic accuracy** just because tokens were reordered.
- This release does **not claim universal or validated Gantt reconstruction**. It proposes process intervals only when vector rectangles and two boundary ticks align; other timeline candidates retain unknown segment mappings. No intervals are accepted as ground truth.
- This release **does not auto-merge Gemini findings** into study content. A model may incorrectly flag a header for appearing first in reading order or refer to a secondary extractor not actually supplied.
- Native vector tables may be absent when tables are rasterized or not drawn with detectable rules.
- Completion of v0.11's *full structural recovery* will require independently checked reconstruction (RTL, table relationships, Gantt intervals) and a before/after benchmark. This branch supplies the provenance-preserving geometric groundwork and regression tests.

## Regression tests

`tests/test_structural_recovery.py` verifies:
- no PDF or SQLite mutation;
- extraction hashes and source PDF integrity;
- rejecting mismatched Gemini audit hashes;
- no promotion of failed AI audits;
- HTML escaping;
- geometric word orders, conservative timeline detection, and vector-block interval assignment conditions.

Passing synthetic tests is not a claim of improvement on the real seven slides.
