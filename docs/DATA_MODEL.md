# Data model

SQLite `sources`: `source_id` (UUID), `relative_path` (unique relative POSIX path), `sha256` (source-content hash), `byte_size`, `ext`, `state` (`active`/`missing`), `last_backend`, `last_parsed_hash`, `last_parser_version`.

SQLite `pages`: composite key (`source_id`, `page_no`); `body` (extracted text, **not verified**), `figure_notes` (reserved list), `flags` (reserved list), `backend`.

FTS5 `pages_fts`: searchable copy of text per source/page; not a vector index and not a semantic concept graph.

Source files remain authoritative. Project exports contain exact filenames and page numbers, but do not reproduce page graphics. They must be manually checked on sensitive/visual material.


## Additional artifacts

- `semantic.py`: optional multilingual embeddings cached as `.npz` under a chosen local data directory; cache fingerprint includes the model and all active parsed source content.
- `enrichment.py`: JSON array with source ID, page, evidence, review flag and annotation type; only reviewed records may enter exports.
- `pdf_bundle.py`: bookmarked original PDF archive plus `.manifest.json` mapping original source pages to combined visual pages.
- Source registry excludes stale parsed content from lookup and exports when SHA-256 no longer matches.