# course-knowledge-pipeline

A local, source-traceable pipeline for preparing engineering lectures for ChatGPT Projects.

**Status:** Complete *offline diagnostic prototype*; not production validated for Docling, Hebrew RTL, or vision-heavy documents. See [validation](docs/VALIDATION.md) and [phase gates](docs/PHASES.md).

## Windows setup

```powershell
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
git switch feature/docling-to-chatgpt-pipeline
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

Keep the PDF originals outside this repository, e.g. `C:\Courses\OS046209`.

To run scan → parse → export in one PowerShell command:

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Courses\OS046209" -Backend docling
```

### Optional automatic daily updates on Windows

To register a Windows Task Scheduler job that re-scans for changed/new lectures and updates Project exports every day at 19:00, run **explicitly**:

```powershell
.\scripts\register_daily_update.ps1 -SourceDir "C:\Courses\OS046209" -At "19:00" -WithVisualPDF
```

This only schedules a **local** job. It does not upload files to ChatGPT or notify you automatically. View or remove it in Windows Task Scheduler. It requires Docling to be installed and the PC to be on when the task runs (subject to Windows task settings).

## Scan, parse, search, export

```powershell
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 scan "C:\Courses\OS046209"
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 parse "C:\Courses\OS046209" --backend docling
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 search "interrupt"
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 hybrid-search "interrupt IDT"
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 export "data\chatgpt-export"
```

Use `--backend pymupdf-diagnostic` only for wiring tests and preflight. It may reorder Hebrew and omit image information. **Do not treat its Markdown output as a faithful replacement for the PDFs.**

Add exported `course_sources_*.md` files and `INDEX.md` to your ChatGPT Project. The `manifest.json` is for auditing; preserve the original PDFs for checking diagrams. Export does not connect a searchable database to ChatGPT.

## Preserve all original diagrams with a PDF archive

```powershell
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 export-pdf "C:\Courses\OS046209" "data\chatgpt-export\course_original_visuals.pdf"
```

This generates a single **bookmarked, loss-minimizing visual PDF** preserving source pages and a `.manifest.json` mapping source pages to merged page numbers. On the six-file sample, this produced 214 pages and six bookmarks; a sampled rendered slide matched the original pixel-for-pixel. This does not magically fix OCR or the model's internal retrieval, but preserves visual content. For mixed PPTX/DOCX inputs, this command only includes PDFs and reports skips; convert other source types separately before bundling.

For ChatGPT Projects, upload the visual archive alongside the Markdown bundles and index. Copy `docs/CHATGPT_PROJECT_INSTRUCTIONS.md` into the Project instruction settings (also provided with the results bundle).

## Review figures

```powershell
.\.venv\Scripts\course-pipeline.exe render-review "C:\Courses\OS046209\lecture.pdf" data\review --pages 3 12
```

Page renders can be inspected manually or passed into optional `draft_visual_note()` using a configured OpenAI vision model/API key. Generated descriptions default to **unreviewed**, not authoritative. Reviewable annotation records are defined in `enrichment.py`.

## Optional neural multilingual retrieval

Install `.[semantic]` and run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[semantic]"
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 semantic-search "How do processes handle interrupts?" --model intfloat/multilingual-e5-small
```

The model may be downloaded on first use and may require substantial memory/time. Embeddings are cached by source hash, page text and model name. The adapter passed tests with a fake encoder, but its real multilingual retrieval quality has not yet been benchmarked on this course. The offline TF-IDF search remains available without neural models.

## Include reviewed figure notes

Use `export data\chatgpt-export --annotations data\reviewed_notes.json`. Only annotations with `reviewed: true` are exported, with their source and page identifiers; unreviewed AI drafts are excluded. The optional vision adapter requires a model and API key and was not executed here.

## Evaluate retrieval

```powershell
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 benchmark benchmarks\os_retrieval_candidates.json --k 5
```

The supplied Operating Systems benchmark cases are **unreviewed candidates**, not verified gold truth. The diagnostic baseline is 54.5% hit@5 across 22 questions. Results measure retrieval of specified pages, not answer quality.

## Scope and future work

See [architecture](docs/ARCHITECTURE.md) for the trust boundaries. OCR of scans, robust diagrams/formulas, full bilingual neural embeddings, ChatGPT end-to-end question answering and continuous folder monitoring remain gated features. Unit tests and source audit reports are not substitutes for verified parsing fidelity.


## v0.4 hybrid extraction and audit (candidate release)

The recommended Windows processing command now uses hybrid PDF parsing (Docling + PyMuPDF) with separately labeled source evidence:

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\OperatingSystems" -Backend hybrid -WithVisualPDF
```

New commands:

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course.sqlite3 build-index data\chatgpt-export
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course.sqlite3 quality-report data\chatgpt-export
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course.sqlite3 review-queue "C:\Users\amita\Documents\University\OperatingSystems" data\chatgpt-export\review --render
```

The optional `--render` option renders only flagged pages for manual inspection. The normal pipeline emits the JSON review list without images.

ChatGPT Project uploads: `COURSE_INDEX.md`, `INDEX.md`, `course_sources_*.md`, and `course_original_visuals.pdf`. Check `QUALITY_REPORT.html` locally before studying. The topic index is **keyword evidence matching**, not an AI-generated semantic graph.

**Not production-certified:** review flagged pages and verify Hebrew RTL, equations and diagrams in the original PDF. See [v0.4 validation](docs/V04_VALIDATION.md).


### Upgrade an existing v0.3 Docling export without re-parsing

If Docling already succeeded and the previous export contains \`manifest.json\` and \`course_sources_*.md\`, reuse it:

\`\`\`powershell
.\scripts\upgrade_v03_export.ps1 \`
  -SourceDir "C:\Users\amita\Documents\University\OperatingSystems" \`
  -PriorExportDir ".\data\chatgpt-export"
\`\`\`

The new output goes to \`data\chatgpt-export-v04\`, preserving the previous export. The script validates hashes and original page headings before reconciling text and generating a new source package. For new courses, run \`scripts/run_pipeline.ps1\` instead.


### Regression gate: 12 previously omitted slides

\`\`\`powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v04.sqlite3 validate-recovery benchmarks\v04_recovery_targets.json
\`\`\`

The command exits nonzero if any of the 12 known omission targets lacks secondary extraction text. It does **not** certify mathematical or visual correctness.


## v0.4.1 — Token-level extraction QA

Work on branch `feature/v0.4.1-disagreement-triage`. This version compares Unicode-normalized word counts (rather than only total character lengths) and prioritizes missing numeric evidence and other discrepancies. The output includes severity-ranked `QUALITY_REPORT.json`, `QUALITY_REPORT.html` and `review/review_queue.json`.

To upgrade from the original **v0.3** export (not from a modified v0.4 export):

```powershell
git fetch origin
git switch feature/v0.4.1-disagreement-triage
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\upgrade_v03_export.ps1 -SourceDir "C:\Users\amita\Documents\University\OperatingSystems" -PriorExportDir ".\data\chatgpt-export" -DatabasePath "data\course-v041.sqlite3" -Output "data\chatgpt-export-v041"
```

The original PDFs remain authoritative. Read [v0.4.1 validation](docs/V041_VALIDATION.md) before relying on the output: 86/214 pages are flagged, including 7 critical by a heuristic rule. Flag counts should not be interpreted as extraction accuracy or confidence scores.


## v0.4.2 — Reproducible public benchmark runner

Run a version-pinned, single-page PDF manifest through Docling, hybrid or native PyMuPDF and produce **per-page Markdown**, latency, source SHA-256, and error accounting. This does **not** compute official benchmark scores: run the dataset owner's evaluator separately.

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-public benchmarks\public\manifest.json data\benchmarks\omni200 --backend hybrid --sample 200 --seed 42
```

The example manifest is a schema template, not downloaded benchmark data. See [benchmark methodology](docs/V042_BENCHMARKS.md).


### Verified 6-page OmniDocBench integration run (2026-11-20)

Docling, PyMuPDF native text, and hybrid were executed in GitHub Actions against identical image-derived PDFs (6 pages, 0 parser failures). The explicitly **unofficial** prose token diagnostic measured 80.81% micro recall for Docling and hybrid, versus 0% for native-text extraction on raster-only PDFs. This is **not an official OmniDocBench accuracy score**, and is too small to generalize. See [measured results and raw artifact](docs/V042_REAL_MICRO_RESULTS.md). Official upstream evaluation and a larger stratified sample remain pending.


## v0.4.3 — Visual evidence and official-scoring preflight

The `visual-evidence` CLI generates a local HTML gallery of the **original rendered PDF pages**, the saved hybrid extraction, a native text reference and suggested numeric discrepancies. Every page stays **unreviewed** until checked. The `benchmark-official-config` CLI rejects missing or failed page predictions and writes an official upstream scorer config; it does *not* compute metrics itself. See [v0.4.3 phase report](docs/V043_PHASE_REPORT.md).


## v0.5 evidence-backed topic map

The `build-knowledge` CLI produces `COURSE_KNOWLEDGE.json` and `COURSE_KNOWLEDGE.md` with exact source SHA-256, page number, extractor segment, evidence excerpt and unresolved review flags. Concept links mean **co-mentioned on the same page**; they are not AI-certified prerequisite relationships. See [v0.5 validation](docs/V05_VALIDATION.md).


## v0.6 — Efficient, source-qualified retrieval

`grounded-search` returns cited **candidate pages**, original source SHA-256 and unresolved extraction flags without generating answers or inventing citations. `benchmark` now constructs one reusable char-ngram index for all its test questions. See [v0.6 validation](docs/V06_VALIDATION.md) for measured timings and current unreviewed retrieval accuracy limitations.


## v0.7 — Table and diagram preservation

Fresh Docling parsing now includes detected table Markdown and visible placeholders for original figures. Failed table export and multi-page figures are flagged instead of silently disappearing. The parser cache version changed: **to test this improvement, rerun Docling using a new database**, not the earlier v0.3 export importer. See [v0.7 validation](docs/V07_VALIDATION.md).


## v0.8 — Review the extraction against original PDFs

Create a stratified 30-page **human-review** package with rendered originals and expandable extraction output:

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v041.sqlite3 review-gold-sample "C:\Users\amita\Documents\University\OperatingSystems" data\gold-review-30 --seed 42
```

Open `data\gold-review-30\REVIEW.html`, label the original versus extracted information, and download `REVIEW_LABELS_COMPLETED.json`. Use `evaluate-review-labels` to compute sample precision/recall **only after independent review**. See [v0.8 validation](docs/V08_VALIDATION.md).

This workflow does not require an AI API key. It does require genuine review to convert proposed pages into gold evidence.


## v0.9 — Optional formula enrichment

The pinned official six-page OmniDocBench evaluation gave a text edit distance of 0.0213 but **zero formula CDM and zero table TEDS**, yielding a 32.62/100 composite. See [official evidence and scoring limitations](docs/V09_VALIDATION.md).

Try `--backend docling-formula` or `--backend hybrid-formula` to enable Docling's additional formula recognition and LaTeX-style output. This may require model downloads and more processing time. It is an experimental, opt-in backend, **not a certified improvement** until the matched official re-evaluation passes.
