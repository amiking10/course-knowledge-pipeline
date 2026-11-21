# v0.5 Evidence-linked course knowledge

## Scope

The canonical evidence-based topic index is generated from already extracted course pages. It does not claim LLM-based semantic interpretation or independently verified accuracy.

`COURSE_KNOWLEDGE.json` and `COURSE_KNOWLEDGE.md` include:
- Topic names and explicit matched aliases
- Original source file, source ID, original PDF page and SHA-256
- Exact local text excerpt and extractor segment (primary vs native text fallback)
- Diagnostic flags and `machine_extracted_unverified` status
- Cross-topic **co-mention on the same page** only; no fabricated prerequisites, synonym relationships, causal links or definitions.

This makes evidence audit practical before adding semantic relationships.

## Commands

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v041.sqlite3 build-knowledge data\chatgpt-export-v05
```

The normal Windows scripts now also generate these exports.

## Validation gates
- Synthetic unit tests ensure SHA-256 and original page metadata on every occurrence and no unsupported semantic claims.
- Empty pages produce no fabricated evidence.
- Extraction flags are preserved rather than silently approving a machine-created concept.
- Full accuracy evaluation for concept selection, tables, equations and bilingual glossary mappings remains pending.
- Do not use these co-mention links as a recommendation of conceptual prerequisites or textbook equivalence.

## Roadmap

Next: collect structured equation and worked-example candidates, create a 30-page human-reviewed bilingual gold set, and evaluate retrieval against independently checked source references.
