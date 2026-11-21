# UNI-VERSE architecture

The current repository is a **local data-preparation and evidence pipeline**, not a hosted AI study platform.

## Why this architecture

The design separates **source-of-truth documents**, **machine extraction**, **retrieval**, and **AI consumption**. This prevents a lossy text converter or a model-generated figure description from silently replacing a lecturer's original slide.

~~~mermaid
flowchart TD
  A["Local source directory<br/>PDF, PPTX, DOCX"] --> B["SHA-256 scan / stable IDs"]
  B --> C[("SQLite: sources")]
  B --> D["Docling / hybrid parser"]
  D --> E["Per-page text + QA flags"]
  E --> F[("SQLite: pages")]
  F --> G[("SQLite FTS5")]
  F --> H["Optional TF-IDF / embedding retrieval"]
  F --> I["Topic and knowledge evidence"]
  F --> J["Page-labeled Markdown files + JSON manifests"]
  A --> K["Bookmarked original visual PDF"]
  I --> L["Package integrity checker"]
  J --> L
  K --> L
  L --> M["Manual upload to ChatGPT Project"]
  M --> N["ChatGPT-managed retrieval and answer generation"]
  G --> O["Local CLI search"]
  H --> O
~~~

## Key modules and data contracts

| Boundary | Code | Data / responsibility |
|---|---|---|
| Source registry | core.py | Stable source_id, path, SHA-256, active/missing state, parser version |
| Parsing | parsers.py, hybrid.py | Page objects; primary text, optional secondary PDF evidence, warnings |
| Quality | quality.py, triage.py, quality_report.py | Flags and prioritization. A clean flag list is NOT verified accuracy |
| Local search | core.py, retrieval.py, prepared_retrieval.py | FTS5, lexical/TF-IDF evidence candidates; original page provenance |
| Neural search | semantic.py | Optional multilingual model with content-sensitive local cache |
| Knowledge | topic_index.py, knowledge.py | Alias hits and same-page co-mentions, never semantic/prerequisite claims |
| Export | exporter.py, pdf_bundle.py | Static Markdown bundles, source inventory, original visual pages, page map |
| Export gate | release_validation.py | Structural consistency before manual upload; no accuracy certification |
| CLI / orchestration | cli.py, scripts/setup_windows.ps1, scripts/run_pipeline.ps1 | First-time Windows setup and reproducible local scan → parse → export → review |\n| ChatGPT instructions | project_instructions.py | One course-specific `INTERNAL/PROJECT_INSTRUCTIONS.md` to paste into the Project Instructions field; never bundled as source text |\n| Optional AI recovery | ai_recovery.py | Explicitly authorized model-generated proposals with separate provenance; does not overwrite source extraction |
| Experimental research | structural_recovery.py, structural_reconstruction.py, cross_block_gantt.py, timeline_validation.py | Unverified RTL, table and Gantt hypotheses stored separately; never overwrite canonical text |

## SQLite layout

- **sources:** source_id, relative_path, sha256, byte_size, ext, state, last_backend, last_parsed_hash, last_parser_version.
- **pages:** source_id, original page_no, body, figure_notes, flags, backend.
- **pages_fts:** SQLite FTS5 searchable representation of page text. This is **not** a vector database.

A scan detects modified/missing files. Searches and exports exclude source rows where the parsed hash no longer matches the registered file hash. The parse backend/version determine which sources are pending reprocessing.

The database should remain local and out of Git; it is not directly attached to ChatGPT Projects.

## Source/answer trust boundaries

1. **Authoritative:** original PDF bytes, original page and document name.
2. **Derived, unverified:** PDF text extraction, output layout, tables/formulas, warnings and keyword evidence.
3. **Hypothetical:** vision-model observations, reconstructed RTL/Gantt candidates, inferred relations.
4. **External service:** ChatGPT Projects receive uploaded files, perform their own retrieval and generate answers. UNI-VERSE cannot guarantee the assistant consulted each uploaded source.

**Rule:** A plausible numeric schedule is not visual proof. Source arithmetic consistency verifies sums, not that the schedule was correctly read from the diagram.

## Security and privacy

This architecture is **local-first**. SQLite and raw PDFs are not published automatically. The Gemini audit has an explicit live opt-in; if enabled, rendered pages and extracted text may be sent to an external provider. Never place private course material, API keys or user database snapshots in public GitHub. No multi-user access control, hosted persistence, customer billing or data deletion workflow exists.

## Runtime workflows

### One-pass course preparation

Run Windows script with source directory outside repo, hybrid backend, and original visual PDF. Each stage exits on a failure. The export contains static files; use the new integrity gate before uploading.

### Incremental update

Rerun the same script after replacing or adding a lecture. Scanning updates source hashes; changed sources are reparsed. Upload the newly generated files to the AI Project, replacing prior versions manually. There is no automatic Project sync.

### AI-backed study

Static exported files are the integration boundary. The ChatGPT Project can be instructed to ground answers in original pages and visual PDFs, but actual citation/answer quality must be evaluated independently.

### Developer-mode local evidence retrieval

Local FTS/TF-IDF/optional embedding search returns source/page evidence without an AI-generated response. Exposing this to a hosted UI requires a separate authenticated retrieval service.

## Failure and regression policy

- A failed parser must not overwrite last-good pages.
- Changed or missing source files must not be searchable/exported as current.
- An incomplete package must fail verification.
- QA output must not claim an unflagged page is correct.
- Reconstructed figures must never silently enter authoritative text.
- CI tests cover modules, but **passing CI is not a user-product acceptance test**.

See [Data model](DATA_MODEL.md), [AI integration](AI_INTEGRATION.md), [Release checklist](RELEASE_CHECKLIST.md) and [Validation history](VALIDATION.md).
