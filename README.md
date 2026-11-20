# Course Knowledge Pipeline

Prepare large collections of engineering lecture materials for ChatGPT Projects with traceable page citations. Windows + Python 3.11+.

**Development status:** Source ingestion, page-based extraction interface, heuristic QA, FTS5 keyword search, incremental parser cache, and Markdown Project exports are implemented. **The Docling path is not yet runtime validated.** AI visual enrichment and semantic embeddings are not implemented.

## Setup on Windows

```powershell
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
git switch feature/docling-to-chatgpt-pipeline
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[parse,diagnostic,dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

Place course PDFs outside Git (for example `C:\Courses\OperatingSystems`).

## Process lectures

```powershell
.\.venv\Scripts\course-pipeline.exe "C:\Courses\OperatingSystems" --db "data\registry.sqlite3"
.\.venv\Scripts\course-stages.exe --registry "data\registry.sqlite3" --parsed "data\parsed.sqlite3" parse "C:\Courses\OperatingSystems" --backend docling
.\.venv\Scripts\course-stages.exe --parsed "data\parsed.sqlite3" search "interrupt"
.\.venv\Scripts\course-stages.exe --registry "data\registry.sqlite3" --parsed "data\parsed.sqlite3" export "outputs\chatgpt-project"
```

For diagnostics without Docling, replace `--backend docling` with `--backend pymupdf-diagnostic`. This is **not** a production-quality replacement: native PDF text can reverse Hebrew or lose formulas and figures.

## Outputs and limitations

- `outputs/chatgpt-project/INDEX.md`: source **inventory**, not a semantic index.
- `course_sources_###.md`: page-anchored source text (not graphics).
- `manifest.json`: source IDs, original filenames, hashes, counts.
- Upload these to ChatGPT Projects, retaining original PDFs for graphs, equations and circuit diagrams.
- ChatGPT Projects do not automatically connect to the local SQLite index.
- Parsed content is evidence only when checked against the source; AI-generated enrichments must not replace it.
- File rename creates a new source ID in this version.

### Status and validation

See [docs/PIPELINE_STATUS.md](docs/PIPELINE_STATUS.md). Local diagnostic smoke test used six Operating Systems PDFs totaling 214 pages. That test does not establish Docling accuracy. GitHub Actions runs source-free automated tests. Don't upload copyrighted lecture PDFs to the public repository.

## Future milestones

1. Run and benchmark Docling on the Windows test corpus (Hebrew RTL, tables, math and images).
2. Add source-linked vision descriptions and review queue.
3. Add semantic/vector retrieval and hybrid ranking.
4. Evaluate at least 30 gold questions across raw and transformed files.
5. Add robust monitoring, logging and end-to-end scheduled updates.
