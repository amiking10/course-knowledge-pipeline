# course-knowledge-pipeline

A traceable pipeline for preparing university lecture materials for ChatGPT Projects.

## Roadmap

1. **Phase 1 (this branch):** local source ingestion, SQLite registry, hashing, change detection, tests.
2. Phase 2: Docling parsing and page/slide provenance.
3. Phase 3: extraction quality assurance.
4. Phase 4: AI semantic enrichment and diagram interpretation.
5. Phase 5: structured indexing and retrieval.
6. Phase 6: export to ChatGPT Projects.
7. Phase 7: benchmark against original lecture materials.
8. Phase 8: automated incremental updates.

### Phase 1 — Windows setup

Requires Python 3.11+.

```powershell
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
course-pipeline "C:\path\to\your\course\lectures" --db "data\registry.sqlite3"
```

The folder can include nested directories of PDF, PPTX, or DOCX files.
The command prints added, changed, unchanged, missing and unsupported counts.
SHA-256 detects content changes; the source ID remains stable across content edits.
Renaming or moving a file produces a new source ID and marks the original path missing.

### Phase 1 data contract

SQLite table `sources` contains:
- `source_id`: stable UUID per source path
- `relative_path`: POSIX-style path relative to the input directory
- `extension`: supported file suffix
- `sha256`: fingerprint of current file bytes
- `size_bytes`, `mtime_ns`: filesystem metadata
- `status`: `active` or `missing`
- `first_seen_at`, `last_seen_at`: timestamps

The database and source lectures should remain local, not be committed.
For each course, use a separate registry database; Phase 1 does not namespace a database by course.
This phase **does not parse lecture contents yet** — Docling integration belongs to Phase 2.

### Acceptance tests

Run `pytest -q`. Coverage includes deterministic hashing, first ingestion,
repeat scans, content changes with stable IDs, missing/restored files,
nested course folders, hidden directory exclusion and invalid source roots.
