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

## Pinned OmniDocBench preparation (implemented)

The upstream Hugging Face repository currently provides 1,651 annotated pages in `OmniDocBench.json`, images, and some original page PDFs. The adapter below explicitly wraps individual **image pages** into PDFs. This tests the raster-document modality; native vector PDF parsing must be tested separately.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,benchmark,dev]"
.\.venv\Scripts\python.exe -m course_pipeline.cli prepare-omnidocbench data\benchmarks\omni200 --revision aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec --count 200 --seed 42

.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-public data\benchmarks\omni200\manifest.json data\benchmarks\omni200\docling --backend docling
.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-public data\benchmarks\omni200\manifest.json data\benchmarks\omni200\native --backend pymupdf-diagnostic
.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-public data\benchmarks\omni200\manifest.json data\benchmarks\omni200\hybrid --backend hybrid

.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-compare data\benchmarks\omni200\comparison.json data\benchmarks\omni200\docling\run.json data\benchmarks\omni200\native\run.json data\benchmarks\omni200\hybrid\run.json
```

Outputs: subset `OmniDocBench_subset.json`, generated one-page image PDFs, Markdown predictions, and a paired runtime/error comparison with exact source hashes. The pinned 40-character revision must refer to an available upstream dataset snapshot; an inaccessible revision causes download failure rather than fallback to moving `main`.

**Official scoring remains separate.** From the upstream OmniDocBench checkout, configure `configs/end2end.yaml` with `ground_truth.data_path` = `OmniDocBench_subset.json` and `prediction.data_path` = one backend's `predictions` directory. Execute `python pdf_validation.py --config <your-config.yaml>`. Use the same configuration for each backend and record evaluator Git SHA, dataset revision, metric settings and environment. Formula CDM can require additional system dependencies. Do not interpret local token overlap or speed as an official accuracy score.

**Practical note:** Running Docling over all 200 image pages on CPU can be expensive. Validate on a 5–10 page sample first, then increase to 200 only after checking outputs. The official benchmark data is not checked into the repository.
