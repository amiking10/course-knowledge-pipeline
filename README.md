# UNI-VERSE
### Your courses. Connected. Understood.

**UNI-VERSE** is a local-first course-material preparation pipeline. It transforms university lecture PDFs and other course documents into searchable, page-attributed text and an **AI-ready study package** while preserving original visual evidence.

**Current status:** Functional developer prototype; improvements are under review on a feature branch. This is **not** a deployed student web application or an independently validated AI tutor. Hebrew/English reading order, diagrams, formulas and tables are still quality risks. There is no automatic upload, direct ChatGPT-to-SQLite connection, hosted API, account system or generated-answer chat UI.

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

## For students: the three-step workflow

1. Keep each course's lecture files in its own source folder (for example `University/RX_TX`). Do not put exported files back in that source folder.
2. Run `run_pipeline.ps1 -SourceDir "PATH_TO_COURSE" -Backend hybrid -WithVisualPDF` from the repository directory. The script prepares only that course, reports progress, and verifies that upload contents match its course database.
3. Review `data/courses/COURSE_NAME/INTERNAL/QUALITY_REPORT.html`. Then open `UPLOAD_TO_CHATGPT` and upload **only the files inside** to the matching ChatGPT Project. On updates, replace the old Project files; they are not automatically synchronized.

The output's `COURSE_INDEX.md` is an automatically matched **keyword index**, not a teacher-reviewed syllabus or proven semantic graph. Missing, formula-heavy, and diagram-heavy material requires a check against the original visual PDF. If verification fails, do not upload the package.

## Quick start: Windows PowerShell

Requirements: Git, Python 3.11/3.12. Keep your course PDFs in a local directory **outside this repository**. The first Docling installation is relatively large.

~~~powershell
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
git fetch origin
git switch --track origin/feature/uni-verse-course-workflow
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\.venv\Scripts\python.exe -m pytest -q
~~~

### Run the full workflow

~~~powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Courses\OperatingSystems" -Backend hybrid -WithVisualPDF
~~~

This scans, parses, exports, builds evidence indexes and quality reports, and creates the original visual archive. **It does not automatically upload anything to ChatGPT.**

Check the output before uploading (the full script already performs this check):

~~~powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\courses\OperatingSystems\INTERNAL\course.sqlite3" verify-export "data\courses\OperatingSystems\UPLOAD_TO_CHATGPT" --require-visuals --source-dir "C:\Courses\OperatingSystems" --quality-report "data\courses\OperatingSystems\INTERNAL\QUALITY_REPORT.json" --strict-indexes
~~~

A successful check means that the **package structure and source/page links are consistent**, not that the extracted content is scientifically or visually correct. Also inspect **data/courses/OperatingSystems/INTERNAL/QUALITY_REPORT.html**.

### One course folder, two clearly separated subfolders

The script automatically creates an **upload-only folder** and a **private internal folder** for every course:

```text
data/
  courses/
    RX_TX/
      UPLOAD_TO_CHATGPT/                 ← select files here for Project Sources
        course_sources_001.md            # all numbered bundles
        INDEX.md
        COURSE_INDEX.md
        COURSE_KNOWLEDGE.md
        manifest.json                    # source/provenance metadata
        course_original_visuals.pdf      # when -WithVisualPDF is set
        course_original_visuals.manifest.json
      INTERNAL/                          ← never upload this entire folder
        course.sqlite3                   # local database
        QUALITY_REPORT.html
        QUALITY_REPORT.json
        COURSE_INDEX.json
        COURSE_KNOWLEDGE.json
        COURSE_WORKFLOW.md               # update and upload instructions
        review/                          # quality review queue
    OperatingSystems/
      UPLOAD_TO_CHATGPT/
      INTERNAL/
```

The upload folder contains **no SQLite database, quality reports, or review queue**. The full workflow also validates that both course indexes exactly match the current source-derived database evidence; manually copied or stale indexes fail verification. The source manifest JSON is intentionally retained there for provenance. The percentage shown in PowerShell represents completed pipeline stages and documents, not a time estimate.

**RX_TX example:**

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\RX_TX" -Backend hybrid -WithVisualPDF
```

Upload location: **`data\courses\RX_TX\UPLOAD_TO_CHATGPT\`**. Private diagnostics: **`data\courses\RX_TX\INTERNAL\`**. The default course name is the original source directory name; advanced options `-OutputRoot`, `-CourseName`, `-Output` (course root) and `-DatabasePath` remain available.

### RapidOCR messages: when they matter

A message such as `RapidOCR returned empty result!` means the OCR recognizer found no text in an attempted image/region; **it does not by itself mean that the lecture failed to parse**. Check the final `failures` array and `INTERNAL/QUALITY_REPORT.html`. An export integrity pass proves file coherence, not OCR correctness.

For PDFs verified to contain **selectable native text**, an explicit troubleshooting option turns off Docling OCR and retains the hybrid native-text comparison:

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\RX_TX" -Backend hybrid-no-ocr -WithVisualPDF
```

**Do not use `hybrid-no-ocr` on scanned PDFs or slides where labels exist only within images.** Disabling OCR can silently drop that information, especially diagrams and screenshots. This is an opt-in troubleshooting alternative, *not* the new default. Changing the backend intentionally triggers a fresh parse; unchanged runs with the same backend remain incremental. The `fitz` deprecation warning is separate from OCR. Review extracted formulas/diagrams against the original visual archive either way.

### Optional AI-assisted formula recovery (external knowledge clearly labeled)

The `ai-recovery` command selects source-linked PDF pages where formulas, numeric evidence or tables are missing; it uses the original page image plus existing extracted text and lets a vision model use **outside technical knowledge** to propose reconstructions.

AI recovery is **OFF by default**. It does not rewrite SQLite pages, lecture exports, topic evidence or original PDFs. Every suggestion is labeled `visually_supported`, `externally_inferred`, or `uncertain`, with a separate description of what was visible, what outside knowledge was used, and remaining uncertainty. Even `visually_supported` is a model's judgment, **not independently verified**.

To enable live calls, install the optional provider and set your own API key in your current Windows PowerShell session:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[gemini]"
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\RX_TX" -Backend hybrid -WithVisualPDF -WithAIRecovery -AIRecoveryLimit 19 -AIRecoveryMaxRequests 19
```

**Privacy/cost:** `-WithAIRecovery` is explicit consent to send up to the specified number of rendered original PDF pages and parser text snippets to Gemini. These provider requests may be billed. Request count is capped; one request per selected page; automatic retries are disabled. Results are cached using the source hash, original page image, model, prompt and extracted text. The default model is `gemini-2.5-flash` (replace with `-AIRecoveryModel <model-id>` if required). Avoid passing sensitive or restricted course files to an external provider.

Outputs:
- `INTERNAL/ai_recovery/AI_RECOVERY.json`: detailed status, provenance and model responses.
- `INTERNAL/ai_recovery/AI_RECOVERY.md`: proposed study text, always marked unverified.
- `UPLOAD_TO_CHATGPT/AI_RECOVERY.md`: an **additional labeled source layer** produced only when opt-in is enabled; the raw extracted source bundles remain unchanged.

Running the pipeline without `-WithAIRecovery` removes any previously published AI reconstruction from the new upload package. A package-integrity pass does not certify any recovered equation. **Check the original PDF** for important formulas and lecturer-specific conventions.

You may inspect candidates without sending anything:

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\courses\RX_TX\INTERNAL\course.sqlite3" ai-recovery "C:\Users\amita\Documents\University\RX_TX" "data\courses\RX_TX\INTERNAL\ai_recovery" --limit 19
```

### Quality report, topic navigation and content review

Every completed run now leaves three tools under the **course-specific** `INTERNAL` directory:

- `QUALITY_REPORT.html`: critical/major diagnostics appear first; ordinary figure and informational flags are collapsed. A flag means **review needed**, not proven incorrect text. Use the exact `by_flag` counts in `QUALITY_REPORT.json` to understand why a course with many diagrams may have warnings on every page.
- `content_audit/REVIEW.html`: a deterministic, stratified sample of PDF pages displayed beside the extracted text. Inspect numbers, formulas, tables, figures and Hebrew/English reading order. Mark the review fields and download the review-label JSON to track human validation. This sample **does not automatically certify** the other pages.
- `stage_reports/*.json`: full stage outputs are recorded locally, while the terminal prints short readable summaries and live parsing progress. The parser's own OCR warning messages may still appear.

The `COURSE_INDEX.md` and `COURSE_KNOWLEDGE.md` in `UPLOAD_TO_CHATGPT` use **course-specific evidence**: repeated terms and 2–3-word phrases from parsed pages. They are lexical indexes, **not** AI-verified concepts, a semantic graph or the lecturer's syllabus.

```powershell
# Refresh RX_TX without reparsing unchanged documents:
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\RX_TX" -Backend hybrid -WithVisualPDF

# Optional: skip regeneration of the visual audit on later runs:
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\RX_TX" -Backend hybrid -WithVisualPDF -SkipContentAudit
```

**Do not upload `INTERNAL` to ChatGPT Projects.** Replace the old project source bundles and indexes rather than accumulating old and new copies. Only a human can confirm that OCR, diagrams, equations and notation match the original PDFs.

### Add new lectures / refresh your existing ChatGPT Project

1. Copy a new PDF/PPTX/DOCX into the **existing original course directory** (subfolders are supported).
2. Rerun the **same** pipeline command for that course. The local database detects changes and only new/modified/stale documents are reparsed.
3. Follow PowerShell's stage percentages and completed-document progress.
4. Inspect **`INTERNAL\QUALITY_REPORT.html`**, especially for charts, formulas and diagrams.
5. In your ChatGPT Project, remove the previous UNI-VERSE export files and upload the updated files from **`UPLOAD_TO_CHATGPT`**. Uploading is manual, not automatically synchronized. Bundle numbering and visual page mapping may change.

See **`INTERNAL\COURSE_WORKFLOW.md`** for a generated reminder of this workflow.

**Existing users:** previous exports and databases are not automatically migrated or erased. If your earlier database is in `data\courses\RX_TX\course.sqlite3` (or `data\rx_tx.sqlite3`), the new default is `data\courses\RX_TX\INTERNAL\course.sqlite3`. The first run without migrating the old database may reparse once. To retain the cache, copy a matching, closed SQLite database to the new path before running. Never mix databases from different courses.

### Manual commands (always pass the course-specific database)

Run the full `run_pipeline.ps1` workflow unless diagnosing a specific stage. For example:

~~~powershell
$courseDb = "data\courses\RX_TX\INTERNAL\course.sqlite3"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db $courseDb hybrid-search "carrier modulation"
.\.venv\Scripts\python.exe -m course_pipeline.cli --db $courseDb verify-export "data\courses\RX_TX\UPLOAD_TO_CHATGPT" --source-dir "C:\Users\amita\Documents\University\RX_TX" --quality-report "data\courses\RX_TX\INTERNAL\QUALITY_REPORT.json" --require-visuals --strict-indexes
~~~

Avoid the legacy shared `data/course.sqlite3` database for multiple courses. The database now records its original source directory and rejects reuse with a different directory. Older unbound databases are checked against their source file hashes before being claimed for a course. For safest migration from a contaminated database, regenerate the affected course's `INTERNAL/course.sqlite3` from its original lecture files instead of copying the old database.

The course topic index is **source-derived keyword navigation**, not semantic topic extraction or a validated knowledge graph. Search does not automatically expand RX_TX queries with Operating Systems synonyms. Visual archiving currently merges **PDF originals only**; PPTX/DOCX source visuals are not automatically included in the bookmarked PDF.


For diagnostic use only, the backend named **pymupdf-diagnostic** extracts native text without document-understanding guarantees. The recommended hybrid backend is also **not production-certified** for high-stakes or diagram-heavy material.

## How to study with AI: recommended supported workflow

**Today, UNI-VERSE integrates with ChatGPT Projects through exported files, not a live database connection.**

1. Run the end-to-end command with **-WithVisualPDF** and verify the package.
2. Create a **new ChatGPT Project** for your course.
3. Upload all numbered **course_sources_*.md** files from the course's **UPLOAD_TO_CHATGPT** directory (normally **data/courses/COURSE_NAME/UPLOAD_TO_CHATGPT/**). Each has original source-file and page information.
4. Upload **INDEX.md**, **COURSE_INDEX.md**, and optionally **COURSE_KNOWLEDGE.md** for navigation.
5. Upload **course_original_visuals.pdf** so the AI has access to the original diagrams, formulas and slide layouts. Optionally include its **course_original_visuals.manifest.json** page mapping.
6. Copy the instructions from [ChatGPT Project instructions](docs/CHATGPT_PROJECT_INSTRUCTIONS.md) into the Project.
7. Ask course questions. Require original source/page citations and visual verification for claims involving diagrams.

Sample prompts:

> In our Operating Systems course, compare FCFS and SJF average waiting time. Cite the lecture name and original page, show the calculations, and explicitly flag any unreadable Gantt chart.

> Find the original slide explaining round-robin time quantum. Explain it using the instructor's notation, and distinguish the lecture from outside knowledge.

> Create five study questions from the course with an answer key and source-page citations. Avoid claims that depend on diagrams you cannot inspect.

**Do not upload SQLite expecting ChatGPT Projects to query it directly.** Each course's **INTERNAL/course.sqlite3** is the local source registry, page store and FTS index. ChatGPT Projects receive static Markdown/PDF files, and their own retrieval behavior is external to this repository. When course materials change, rerun the pipeline and replace the uploaded files.

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

See [repository review and remaining risks](docs/REPOSITORY_REVIEW_2026-11-20.md). Read [full architecture](docs/ARCHITECTURE.md), [data model](docs/DATA_MODEL.md), [AI integration](docs/AI_INTEGRATION.md) and [release checklist](docs/RELEASE_CHECKLIST.md).

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

## Troubleshooting

If Windows reports that an Application Control policy blocks a pandas/Docling DLL during import, see [Windows Docling troubleshooting](docs/WINDOWS_DOCLING_TROUBLESHOOTING.md). This requires an approved dependency runtime, not a silent parser fallback.

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
