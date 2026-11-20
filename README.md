# course-knowledge-pipeline

A local, source-traceable pipeline for preparing engineering lectures for ChatGPT Projects.

**Status:** Complete *offline diagnostic prototype*; not production validated for Docling, Hebrew RTL, or vision-heavy documents. See [validation](docs/VALIDATION.md) and [phase gates](docs/PHASES.md).

## Windows setup

```powershell
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

Keep the PDF originals outside this repository, e.g. `C:\Courses\OS046209`.

To run scan → parse → export in one PowerShell command:

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Courses\OS046209" -Backend docling
```

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

For ChatGPT Projects, upload the visual archive alongside the Markdown bundles and index.

## Review figures

```powershell
.\.venv\Scripts\course-pipeline.exe render-review "C:\Courses\OS046209\lecture.pdf" data\review --pages 3 12
```

Page renders can be inspected manually or passed into optional `draft_visual_note()` using a configured OpenAI vision model/API key. Generated descriptions default to **unreviewed**, not authoritative. Reviewable annotation records are defined in `enrichment.py`.

## Evaluate retrieval

```powershell
.\.venv\Scripts\course-pipeline.exe --db data\os.sqlite3 benchmark benchmarks\os_retrieval_candidates.json --k 5
```

The supplied Operating Systems benchmark cases are **unreviewed candidates**, not verified gold truth. The diagnostic baseline is 54.5% hit@5 across 22 questions. Results measure retrieval of specified pages, not answer quality.

## Scope and future work

See [architecture](docs/ARCHITECTURE.md) for the trust boundaries. OCR of scans, robust diagrams/formulas, full bilingual neural embeddings, ChatGPT end-to-end question answering and continuous folder monitoring remain gated features. Unit tests and source audit reports are not substitutes for verified parsing fidelity.
