# UNI-VERSE
### Your courses. Connected. Understood.

**UNI-VERSE** is a local-first course-material preparation pipeline. It transforms university lecture PDFs and other course documents into searchable, page-attributed text and an **AI-ready study package** while preserving original visual evidence.

**Current status:** Functional developer prototype. This is **not** a deployed student web application or an independently validated AI tutor. Hebrew/English reading order, diagrams, formulas and tables are still quality risks. There is no automatic upload, direct ChatGPT-to-SQLite connection, hosted API, account system or generated-answer chat UI.

## Why we built it

Students study from scattered lecture decks, notes, tutorials, homework and diagrams. Naive PDF extraction breaks context, ignores figures and loses bilingual reading order. AI chat over bad extraction can be confidently wrong.

UNI-VERSE prepares course materials **before** an AI assistant reads them:

- Identifies changed or missing source files using SHA-256.
- Extracts page-level text via Docling or hybrid Docling + PyMuPDF.
- Preserves source filenames and original page numbers.
- Marks suspicious extraction instead of silently accepting it.
- Creates a keyword/topic evidence index and local retrieval database.
- Keeps original figures and equations in a bookmarked visual PDF.
- Exports an uploadable set of Markdown and PDF files for ChatGPT Projects.

**Differentiation is a research hypothesis, not a proven competitor advantage.** Better study outcomes or higher accuracy must be demonstrated by real users and independent evaluation.

## Quick start: Windows PowerShell

Requirements: Git, Python 3.11/3.12. Keep your course PDFs in a local directory **outside this repository**. The first Docling installation is relatively large.

~~~powershell
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
git fetch origin
git switch --track origin/release/uni-verse-readiness
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\.venv\Scripts\python.exe -m pytest -q
~~~

### Run the full workflow

~~~powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Courses\OperatingSystems" -Backend hybrid -WithVisualPDF
~~~

This scans, parses, exports, builds evidence indexes and quality reports, and creates the original visual archive. **It does not automatically upload anything to ChatGPT.**

Check the output before uploading:

~~~powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" verify-export "data\chatgpt-export" --require-visuals --source-dir "C:\Courses\OperatingSystems"
~~~

A successful check means that the **package structure and source/page links are consistent**, not that the extracted content is scientifically or visually correct. Also inspect **data/chatgpt-export/QUALITY_REPORT.html**.

### Manual commands

~~~powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" scan "C:\Courses\OperatingSystems"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" parse "C:\Courses\OperatingSystems" --backend hybrid
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" hybrid-search "What is preemptive scheduling?"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" export "data\chatgpt-export"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" export-pdf "C:\Courses\OperatingSystems" "data\chatgpt-export\course_original_visuals.pdf"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" build-knowledge "data\chatgpt-export"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" build-index "data\chatgpt-export"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" quality-report "data\chatgpt-export"
~~~

For diagnostic use only, the backend named **pymupdf-diagnostic** extracts native text without document-understanding guarantees. The recommended hybrid backend is also **not production-certified** for high-stakes or diagram-heavy material.

## How to study with AI: recommended supported workflow

**Today, UNI-VERSE integrates with ChatGPT Projects through exported files, not a live database connection.**

1. Run the end-to-end command with **-WithVisualPDF** and verify the package.
2. Create a **new ChatGPT Project** for your course.
3. Upload all numbered **course_sources_*.md** files from **data/chatgpt-export/**. Each has original source-file and page information.
4. Upload **INDEX.md**, **COURSE_INDEX.md**, and optionally **COURSE_KNOWLEDGE.md** for navigation.
5. Upload **course_original_visuals.pdf** so the AI has access to the original diagrams, formulas and slide layouts. Optionally include its **course_original_visuals.manifest.json** page mapping.
6. Copy the instructions from [ChatGPT Project instructions](docs/CHATGPT_PROJECT_INSTRUCTIONS.md) into the Project.
7. Ask course questions. Require original source/page citations and visual verification for claims involving diagrams.

Sample prompts:

> In our Operating Systems course, compare FCFS and SJF average waiting time. Cite the lecture name and original page, show the calculations, and explicitly flag any unreadable Gantt chart.

> Find the original slide explaining round-robin time quantum. Explain it using the instructor's notation, and distinguish the lecture from outside knowledge.

> Create five study questions from the course with an answer key and source-page citations. Avoid claims that depend on diagrams you cannot inspect.

**Do not upload SQLite expecting ChatGPT Projects to query it directly.** The file **data/course.sqlite3** is the local source registry, page store and FTS index. ChatGPT Projects receive static Markdown/PDF files, and their own retrieval behavior is external to this repository. When course materials change, rerun the pipeline and replace the uploaded files.

For a **database-connected AI application**, an additional authenticated backend must retrieve passages from SQLite and supply them to an LLM with provenance. No such hosted app/API currently ships in this repository. See [AI integration](docs/AI_INTEGRATION.md).

## Architecture

~~~mermaid
flowchart TD
    A["Course PDFs / PPTX / DOCX<br/>source of truth"] --> B["SHA-256 scan / source registry"]
    B --> C[("SQLite sources")]
    B --> D["Docling or hybrid parsing"]
    D --> E["Page text + provenance + QA flags"]
    E --> F[("SQLite pages + FTS5")]
    F --> G["Local lexical / TF-IDF / optional semantic retrieval"]
    F --> H["Page-anchored Markdown export"]
    F --> I["Topic and knowledge evidence files"]
    A --> J["Bookmarked visual PDF"]
    H --> K["Export integrity check"]
    I --> K
    J --> K
    K --> L["Manual upload to ChatGPT Project"]
    L --> M["ChatGPT answers over uploaded sources"]
    G --> N["Local CLI evidence search<br/>no generated answers"]
~~~

**Source registry:** The scanner records file hash, path, state and parser version. Changed, missing or stale content is not included in normal search/export until reparsed.

**Extraction:** Docling processes source files, with a secondary native-PDF extraction in hybrid mode. Page text and QA flags are stored with source ID and original page. Experimental RTL, table and Gantt reconstruction produces sidecars only; it is not substituted into the trusted course text.

**Retrieval:** Local SQLite FTS5 supports keyword search; optional character-ngram TF-IDF and neural embeddings offer other retrieval modes. They are **not** the same as the ChatGPT Project's own file retrieval.

**Knowledge layer:** COURSE_INDEX and COURSE_KNOWLEDGE link explicitly matched terms to original pages. Same-page mentions do not prove conceptual or prerequisite relations, and these files are **not** a verified semantic knowledge graph.

**Export:** The Markdown bundles, source manifests, original visual PDF and QA reports are generated locally. The new export gate checks file/source coherence. Correctness of formulas, images and answers still requires independent evidence.

**Trust boundary:** Original document bytes and original page numbers are the authoritative sources. Machine parsing, model interpretations and text order are unverified unless independently evaluated.

Read [full architecture](docs/ARCHITECTURE.md), [data model](docs/DATA_MODEL.md), [AI integration](docs/AI_INTEGRATION.md) and [release checklist](docs/RELEASE_CHECKLIST.md).

## Output files

| File | Purpose | Upload to ChatGPT? |
|---|---|---|
| course_sources_001.md etc. | Extracted source text with original page headings | **Yes, all bundles** |
| INDEX.md | Document inventory and checksums | Yes |
| COURSE_INDEX.md | Keyword-linked topic navigation | Yes |
| COURSE_KNOWLEDGE.md | Machine-matched topic evidence, not verified | Optional |
| course_original_visuals.pdf | Preserves page graphics, tables and equations | **Yes** |
| course_original_visuals.manifest.json | Original-to-merged page mapping | Optional |
| QUALITY_REPORT.json / .html | Flagged extraction issues | Review locally |
| data/course.sqlite3 | SQLite source, page, FTS storage | **No; keep local** |

## Validation and readiness

Test locally with:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course.sqlite3" verify-export "data\chatgpt-export" --require-visuals
~~~

Previous work used a **214-page** Operating Systems course sample and a **seven-page** critical-slide pilot. These are not independently labeled accuracy benchmarks. The latest scheduling research had six structurally coherent timeline candidates out of eight, **not six visually verified correct diagrams**. Do not use that figure as an extraction accuracy claim.

The repo has no hosted, secure multi-user application, production authentication, automatic ChatGPT Project synchronization or validated answer-generation layer. See [release checklist](docs/RELEASE_CHECKLIST.md) for concrete gates.

## Repository map

~~~text
src/course_pipeline/
  core.py                    SHA registry, SQLite pages and FTS
  parsers.py / hybrid.py     extraction backends
  quality*.py / triage.py   QA flags and severity
  retrieval.py / semantic.py local candidate evidence search
  topic_index.py / knowledge.py topic evidence files
  exporter.py / pdf_bundle.py Markdown and visual PDF export
  release_validation.py     export integrity gate
  cli.py                    command-line interface
  structural_*.py / timeline_validation.py   experimental research
scripts/
  run_pipeline.ps1          one-command local workflow
docs/                       architecture, integration, validation and history
tests/                      regression suite
~~~

Historical implementation notes remain in docs rather than cluttering onboarding. Keep private or copyrighted PDFs outside public GitHub. Gemini vision auditing is explicitly opt-in and may send rendered pages to an external model.

**Licensing:** The repository does not currently declare a software license. Public access does not automatically grant commercial reuse rights. Choose a license and publish privacy/security terms before external product distribution.
