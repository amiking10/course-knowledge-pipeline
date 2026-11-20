# Multi-phase implementation status

The earlier Phase 1 branch is the base. This branch adds parsing, extraction QA,
keyword retrieval and ChatGPT Project export. All source materials stay local.

| Phase | Implementation | Validation |
|---|---|---|
| 1. Ingestion | Phase 1 scanner / SQLite manifest | Existing unit tests |
| 2. Docling parsing | Docling adapter and page provenance | **Not runtime-validated**: Docling cannot be installed in current environment |
| 3. Extraction QA | Page completeness and low-text warnings | Synthetic tests and six-file diagnostic run |
| 4. AI enrichment | Not implemented | Blocked pending vision model integration and human-reviewed examples |
| 5. Index | SQLite FTS5 BM25 lexical retrieval | Diagnostic retrieval demonstrated; semantic search not implemented |
| 6. Project export | Page-referenced Markdown bundles + manifest | Exported six PDFs into two bundles |
| 7. Evaluation | Unit and ingestion smoke tests | Full benchmark (answer/citation accuracy) outstanding |
| 8. Incremental updates | SHA-256/backend-version checks | Logic added; full Docling regression outstanding |

## Test corpus
Six supplied Operating Systems PDFs (046209): 214 PDF pages in total. A PyMuPDF
diagnostic backend extracted text from all pages and produced seven heuristic
review warnings. **This is not a Docling benchmark**, and text may be incorrect
in Hebrew RTL layout, formulas, and diagrams.

## Required acceptance gates before promoting to production
1. Install and run Docling locally with all six samples.
2. Check exactly 214 pages and review every zero-text page against rendered originals.
3. Validate source-specific terms, equations, RTL reading order, and diagram coverage.
4. Add provenance-linked vision descriptions (separated from source facts).
5. Test hybrid semantic retrieval and source ranking, including negative questions.
6. Benchmark ≥30 instructor-grounded questions and cite correct original page locations.
7. Run automated lint/tests on Windows and prevent source materials from entering Git.

## Example on Windows
Install Docling and PyMuPDF: `py -m pip install docling pymupdf pytest`.
Then run an ingestion scan using the Phase 1 CLI and invoke the new phase API in Python.
The normal integrated CLI remains future work.
