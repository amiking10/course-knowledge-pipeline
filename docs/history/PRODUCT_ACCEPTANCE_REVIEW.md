# UNI-VERSE product acceptance inspection — 2026-11-21

**Inspected branch:** `feature/uni-verse-course-workflow` (unmerged). This assessment distinguishes confirmed source-code behavior from unverified real-document outcomes.

## Product acceptance matrix

| Criterion | Inspection | Status |
| --- | --- | --- |
| No cross-course content | Each course defaults to its own SQLite database, source-root binding rejects switching source directories, and indexes are built from active parsed sources. Tests cover OS/RX_TX separation. | Guarded; needs real source-file acceptance |
| Correct exported Markdown | Strict verification now regenerates all deterministic source bundles from the course database and byte-compares their content, not merely their headings. | Guarded; OCR fidelity still unverified |
| Correct source citations | Export retains source path, source ID, page number, SHA in manifests. Source PDF archive includes an original-to-merged page manifest. | Structurally guarded |
| No stale output files | Export removes obsolete numbered bundles and strict verification rejects unexpected bundles. | Guarded |
| Safe upload folder | `UPLOAD_TO_CHATGPT` allows only intended source files and metadata; SQLite and QA are in `INTERNAL`. | Guarded |
| Easy first-run and updates | Single PowerShell command, output path, elapsed-time spinner, per-document progress, success summary, simple README workflow. | Implemented; needs real user test |
| Measurable loading indicator | True document counts and elapsed time; Docling internal page percentage is not exposed. | Accurate, no invented percentage |
| Human-friendly contents | Original file/page references and a keyword index. Filenames and technical reports remain developer-oriented. | Partial |
| Course-specific concepts | Automatic unigram keyword selection, not semantic topics or a reviewed syllabus. | Needs improvement |
| Diagrams and math | Original PDFs preserved, but no independent guarantee of formula or figure extraction; PPTX/DOCX are not included in the PDF visual bundle. | Not verified |
| Deployment | Prototype exports static files; no direct ChatGPT Project sync, no independent accuracy validation. | Not production-ready |

## Confirmed code changes from this inspection

- Hardened `--strict-indexes`: both index Markdown files and all source Markdown bundles are regenerated in temporary storage and compared byte-for-byte against the active course database.
- Added tests for modified bundle body under an unchanged page heading and for leftover foreign bundles.
- Made the success message actionable: course name, document and bundle counts, review report path and explicit instruction to replace old ChatGPT Project files.
- Added student-oriented three-step onboarding before the developer setup details.

## High-priority remaining issues

1. **Real-corpus acceptance:** Run on distinct OS and RX_TX originals. Compare output manifest hashes, course terms, page counts and random source-page text against originals. Re-run after adding/deleting files, verify no contamination, no missed pages and no stale ChatGPT files.
2. **Content fidelity:** Label technical slides with formulas/diagrams and verify OCR, ordering, table structures and visual archive. The integrity gate only guarantees fidelity to the parser's *output*, not to lecture truth.
3. **Filename/UX clarity:** Students should receive a concise upload manifest and an understandable warning summary, not have to interpret JSON. Keep private debug files off the upload path.
4. **Topic quality:** Repeated single-word headings are not a conceptual map. Evaluate section headings, technical phrases and course-specific vocabulary against human examples before calling it a knowledge graph.
5. **Failure recovery:** Add a controlled interruption/restart test and an explicit migration diagnostic for legacy shared course databases.
6. **Visual coverage:** PPTX/DOCX page/slide originals need a supported visual path or an explicit warning per missing visual source.
7. **Measured performance:** Profile the entire Windows workflow, including model startup, repeated scanning, document-level parsing and final verification; avoid estimated progress percentages without real callbacks.

## Go/no-go decision

**No-go for declaring the pipeline universally correct or production-grade.** The fixes address verifiable structural contamination and tampering risks. The branch can become a beta course-preparation tool after final CI and real Windows OS/RX_TX acceptance tests pass. It must not claim that passing export verification ensures correctness of lecture text, tables, diagrams or AI answers.

**User-facing acceptance scenario:** Prepare 15 RX_TX documents, inspect `COURSE_INDEX.md` for course-specific terms, inspect sampled exported pages and original PDF diagrams, add one RX_TX PDF and rerun; only that new/changed document should parse, the OS output should not change, and `verify-export --strict-indexes --require-visuals` should pass.
