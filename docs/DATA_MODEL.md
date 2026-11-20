# Data model

SQLite `sources`: `source_id` (UUID), `relative_path` (unique relative POSIX path), `sha256` (source-content hash), `byte_size`, `ext`, `state` (`active`/`missing`), `last_backend`, `last_parsed_hash`, `last_parser_version`.

SQLite `pages`: composite key (`source_id`, `page_no`); `body` (extracted text, **not verified**), `figure_notes` (reserved list), `flags` (reserved list), `backend`.

FTS5 `pages_fts`: searchable copy of text per source/page; not a vector index and not a semantic concept graph.

Source files remain authoritative. Project exports contain exact filenames and page numbers, but do not reproduce page graphics. They must be manually checked on sensitive/visual material.
