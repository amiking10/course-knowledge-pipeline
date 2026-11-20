# Engineering phase gates — current implementation

| Phase | Implemented | Validated in this environment | Remaining gate |
|---|---|---|---|
| 1. Ingestion | Yes | Scan/rename/modified/missing unit tests; six original PDFs | Windows filesystem behavior |
| 2. Docling | Adapter | **No** (dependency unavailable) | Install Docling, run entire sample and compare | 
| 3. QA | Page-level flags, count checks, visual exports | Yes, diagnostics only | Hebrew layout/figure fidelity human review |
| 4. AI enrichment | Source-linked records, optional vision draft adapter | Schema tested; external model **not run** | Configure API model and human-review notes |
| 5. Retrieval | FTS5 + character TF-IDF hybrid + optional cached multilingual neural embeddings | Local sample + mocked neural-cache tests | Real multilingual model quality unmeasured |
| 6. ChatGPT Project export | Markdown bundles, bookmark-preserving original PDF archive, manifest, stale protection | Yes, six PDFs exported | Test ChatGPT's answer accuracy with uploaded bundles |
| 7. Evaluation | Dataset runner, hit@k and MRR | Yes, 22 **candidate** questions | Curate 30+ human-reviewed gold items |
| 8. Incremental | SHA/version/backend invalidation, no stale export | Unit tests passed | Folder watch or scheduled execution |

**A working offline diagnostic release is not the same as a production-validated academic parser.**
