# UNI-VERSE local data model

UNI-VERSE stores its **local source registry, extracted pages and full-text index** in SQLite. This is an implementation database, **not a hosted service or direct ChatGPT-connected database**.

## Tables

### sources

| Column | Role |
|---|---|
| source_id | UUID identifying a source across changes to its content at a stable path |
| relative_path | POSIX-style path relative to the scanned course directory; unique |
| sha256 | Current bytes of the original file |
| byte_size, ext | Source metadata |
| state | active or missing |
| last_backend | Backend used for last successful extraction |
| last_parsed_hash | Input source hash used for last successful parse |
| last_parser_version | Last parser revision used |

**Freshness invariant:** Search and normal text export require an active source and last_parsed_hash equal to current sha256. A changed file is reparsed before a new export. The parser version and backend also determine whether an extraction is pending.

### pages

| Column | Role |
|---|---|
| source_id, page_no | Composite key; original document page number is 1-based |
| body | Machine-extracted text; not guaranteed visually correct |
| figure_notes | JSON list of figure-review descriptions |
| flags | JSON list of quality warnings |
| backend | Parser used for this page |

### pages_fts

SQLite FTS5 index of source_id, page_no and body. Used for local lexical retrieval. It is not an embedding index, not a relational knowledge graph, and does not automatically transfer to ChatGPT Projects.

## Derived data

- **Hybrid extraction:** A page body may preserve separately marked Docling and secondary PyMuPDF evidence when extractors disagree.
- **Optional semantic retrieval:** Embeddings cache is stored locally, keyed to source content and model identity. It is not populated by the basic installation.
- **COURSE_INDEX:** Keyword/alias matches pointing to source pages.
- **COURSE_KNOWLEDGE:** Explicit topic occurrences and co-mentions on the same page; not a verified semantic knowledge graph.
- **Export package:** Numbered Markdown bundles, INDEX.md, manifest.json, optionally a visual PDF archive with its own page-map manifest, and QA/knowledge files.
- **Experimental reconstruction sidecars:** RTL, table and Gantt proposals remain outside canonical SQLite content until independently verified.

## Provenance and integrity

- Keep the **original PDF and original page number** as the source of truth.
- Preserve source SHA-256 through the export manifests.
- Do not mix unverified model-generated figure notes with primary lecture text.
- Do not assume mathematical agreement between extracted values proves visual correctness.
- Use **verify-export** before uploading an AI-ready package.

## Security

The database belongs in the local data directory and is ignored by Git. It may contain proprietary course text and should not be pushed to a public repository or uploaded to ChatGPT Projects as if it were a supported live connector.

See [Architecture](ARCHITECTURE.md) and [AI integration](AI_INTEGRATION.md).
