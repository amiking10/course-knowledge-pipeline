# v0.4 extraction-fidelity validation

Status: **candidate release, not fidelity-certified**.

## Executed checks
- Local pytest: 23 passed, 2 skipped (Python 3.13).
- Six Operating Systems PDF originals: 214 pages. Reconciled the user's Docling v0.3 Markdown export against **independent native PyMuPDF extraction**, not a fresh Docling run.
- All 12 previously reported material-omission pages now contain independently extracted native text, separately labeled for verification.
- Secondary inclusion policy: native text >= 140 characters and Docling/native character length ratio < 0.30 (or when Docling is empty). These are heuristic checks, not claims of perfect recovery.
- Quality report flags 73 of 214 pages for review in the reconstructed test corpus; flags include low text and parser disagreement, not necessarily actual corruption.
- Source-preserving visual PDF archive: 214 pages, 6 bookmarks; a rendered Round Robin slide matched source pixels.
- Topic navigation: 6 evidence-matched categories with 305 source-page references, not an AI semantic knowledge graph.
- The 22 unreviewed baseline retrieval cases scored 50% hit@5 for this reconstructed export, below the desired 95% acceptance target.

## Limitations / required release gates
1. Fresh actual Docling v0.4 processing and end-to-end Windows test across all six user PDFs.
2. Human review of RTL Hebrew, math expressions, timelines, tables and missing visual content.
3. Opt-in vision-based figure interpretation with reviewed provenance, not just renderable review queue.
4. Proper semantic graph, cross-lecture concepts/prerequisites with verified evidence.
5. Thirty or more independently reviewed gold evaluation cases, including negatives and diagrams. Minimum 95% hit@5 remains an *unmet target*.
6. ChatGPT Project end-to-end question/citation testing.

## Source of truth
The original PDFs remain authoritative. Machine-extracted Docling and PyMuPDF text are interpretations and do not supersede the original. Reviewed figure annotations are stored separately.

## Regression pages (original source numbering)
- `02 פסיקות ואיתותים.pdf`: 15, 16, 29, 42
- `OS01-intro-procs (1).pdf`: 46, 63, 65, 72
- `OS02-procs-sched (1).pdf`: 18, 28, 40, 41


## v0.3 upgrade command (validated separately)
The `reconcile-export` command was executed against the user's actual v0.3 export and all six original PDFs. It checked file hashes, reconciled 214 pages, and generated v0.4 output without executing Docling again. The importer flagged 75 pages (including short-text review flags). Three dedicated unit tests cover matching, source hash mismatch, and incomplete exports. The PowerShell wrapper has not been executed on Windows in this environment.
