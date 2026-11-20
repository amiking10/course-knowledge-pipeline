# v0.4.2 — Public PDF benchmark integration

## Status
**Benchmark harness implemented; public dataset evaluation is not yet executed.** No official accuracy result can be claimed until the dataset assets and owner's evaluators are run. The local unit tests use synthetic PDFs and are not evidence of parser accuracy.

## Benchmarks and their proper roles
1. **OmniDocBench v1.6** — page-to-Markdown extraction accuracy for text, tables, formulas and reading order. [Project](https://github.com/opendatalab/OmniDocBench); [dataset](https://huggingface.co/datasets/opendatalab/OmniDocBench). Version-pin the dataset and official scorer. Official metrics must come from official evaluation code. Do not call our token diagnostic an OmniDocBench score.
2. **olmOCR-Bench** — assertions about whether document-to-Markdown conversion preserved specific content. [Project](https://github.com/allenai/olmocr/tree/main/olmocr/bench), [dataset](https://huggingface.co/datasets/allenai/olmOCR-bench). Run its official Python suite on predictions; retain missing-file failures.
3. **DocLayNet** — COCO-style layout-object annotations (not a direct Markdown reconstruction metric). [Project](https://github.com/DS4SD/DocLayNet). Deferred until we implement region coordinates.
4. **Six Operating Systems PDFs** — a separate author-reviewed Hebrew/English regression set; not a public benchmark.

## Manifest
Use `benchmarks/public/manifest.example.json` as a schema sample. Put one single-page PDF per case in `pages/`. `id` must match the official benchmark page stem when handing predictions to official evaluators. Record `revision`, `stratum`, exact PDF bytes (runner reports SHA-256), model and parser versions.

Datasets are **not included or downloaded**. Download them from their owner-controlled sources, verify license and version, and derive the page-level cases. OmniDocBench official distributions may include page images rather than one-page PDFs: generate a single-page PDF wrapper from the benchmark image using a lossless image insertion method and record this preprocessing explicitly. This input modality must be disclosed; it is not necessarily equivalent to processing native PDF text.

## Execution (PowerShell)
```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,dev]"
.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-public benchmarks\public\manifest.json data\benchmarks\omni200 --backend hybrid --sample 200 --seed 42
```
Run the same manifest with `--backend docling` and `--backend pymupdf-diagnostic` using separate output folders. The runner writes `predictions/<id>.md` plus a source-hash, latency and error manifest `run.json`.

**Important:** The new CLI is an extraction runner, *not* the official scoring framework. Feed Markdown predictions into the upstream OmniDocBench evaluation code, matching filenames and preprocessing. Follow the upstream metric configuration exactly to obtain normalized edit distance, TEDS, formula metrics and reading order. For olmOCR, use its official executable against generated Markdown with its test fixtures.

## Quality gates for the next implementation phase
- Public datasets acquired with provenance and pinned revisions.
- A reproducible, documented stratified 200-page sample.
- Real Docling-only / hybrid / vision predictions on identical inputs.
- Official upstream evaluator scores and per-category breakdowns.
- At least 30 independently reviewed Hebrew/technical course pages; false-positive/false-negative warning detection scored separately.
- No silent omissions, unqualified accuracy claims or false citations.
