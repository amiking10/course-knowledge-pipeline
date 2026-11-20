# v0.4.2 — First live OmniDocBench micro-run

Date: 2026-11-20
GitHub Actions: https://github.com/amiking10/course-knowledge-pipeline/actions/runs/44730295849
Raw artifact: https://github.com/amiking10/course-knowledge-pipeline/actions/runs/44730295849/artifacts/14626326879

## Reproducibility
- Dataset: official `opendatalab/OmniDocBench`, pinned Hugging Face commit `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec`.
- 6 stratified pages, seed 42, converted **original page images** to one-page raster PDFs. These are **not native vector-PDF tests**.
- Paired SHA-256 checks confirmed the same page bytes were used for both parser runs.
- Parser: PyMuPDF native-text diagnostic vs Docling. Next run extends this to hybrid.
- Output: predictions, source digest, per-page latency, subset annotations and errors in the downloadable artifact.

## Observed results

| Metric | PyMuPDF (native text layer only) | Docling OCR |
|---|---:|---:|
| Pages run | 6 | 6 |
| Successful executions | 6 | 6 |
| Failed executions | 0 | 0 |
| Median seconds per page | 0.001 | 11.887 |
| Sum of measured page times | 0.064 s | 113.622 s |
| Extracted text on these raster-input pages | Empty on all 6 | Nonempty on all 6 |
| Official OmniDocBench score | Not run | Not run |

Because page PDFs contain raster images only, the native-text-only PyMuPDF backend correctly returns empty text; this is not a fair comparison of their performance on searchable born-digital PDFs.

## Auxiliary prose diagnostic (NOT official scoring)
Using an in-house Unicode-normalized multiset overlap on selected `text_block`, `title`, `equation_explanation`, `figure_caption`, and `table_caption` reference fields, the six Docling predictions had:
- Macro per-page prose token recall: **78.37%**
- Micro token-weighted prose recall: **80.81%**

These numbers are exploratory descriptive statistics from six pages, **not OmniDocBench Edit Distance, TEDS, CDM or an official accuracy score**. They do not establish correctness for formulas, tables, reading order or Hebrew.

## Engineering fixes discovered by actual benchmark
1. Official annotation `image_path` values can omit the `images/` Hugging Face storage prefix. Fixed the fetch path.
2. Official page image stems can contain Chinese characters and other Unicode. Fixed ID/path validation to allow portable Unicode filenames.
3. Instantiating Docling for every page wastes repeated setup; added single-process converter caching.

## Next release gates
- Confirm hybrid extraction and automated diagnostic command using identical 6-page public subset.
- Expand to stratified 200+ pages with resource measurements and failures recorded.
- Run the **matched-version official upstream OmniDocBench evaluator**, producing Edit Distance, TEDS, CDM and reading-order metrics. Never substitute our prose diagnostic.
- Compare against original born-digital PDFs in a separate cohort.
- Independently review at least 30 Operating Systems pages spanning Hebrew/English, formulas and process diagrams.
