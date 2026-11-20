# v0.7 — Docling structure-preserving extraction

## Motivation

The previous per-page Docling adapter copied only `item.text`. Some `TableItem` objects store their grid separately and were **silently omitted**. Figures also lacked placeholders, so users could mistake an extracted page for complete content.

## Changes

- `TableItem.export_to_markdown(doc=doc)` now preserves detected table grids as Markdown per original page.
- Failed/empty table serialization leaves an explicit marker and `table_structure_review_required` flag.
- Picture/figure objects leave visible `FIGURE DETECTED` markers and `figure_content_review_required` flags; no textual interpretation is invented.
- Items spanning multiple pages are retained and marked `multi_page_item_review_required` for manual layout verification.
- Source hashes and page-level provenance remain unchanged.
- Parser version bumped so old cached exports are not silently used as new v0.7 results.

## Tests

Synthetic Docling-document tests cover successful table serialization, exceptions, picture markers, and multi-page structures. Real Docling smoke test and Windows/Linux CI must pass.

## Limitations

This does not visually recover handwritten calculations, diagram coordinates, chart logic or missing content Docling never detected. Markdown tables may not preserve merged-cell semantics; preserve original PDF images for structure-sensitive questions. <https://docling-project.github.io/docling/concepts/serialization/>

## Run a fresh reparse

```powershell
git fetch origin
git switch feature/v0.7-table-figure-fidelity
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,retrieval,dev]"
.\scripts\run_pipeline.ps1 -SourceDir "C:\Users\amita\Documents\University\OperatingSystems" -Backend hybrid -WithVisualPDF -DatabasePath "data\course-v07.sqlite3" -Output "data\chatgpt-export-v07"
```

Important: **do not use** the `upgrade_v03_export.ps1` path to test this parser improvement, because it reuses previously extracted Docling text and would not re-run the improved table serializer.

## Release gates

A fresh full six-document parse and visual spot-check are still needed before claiming that mathematical/table fidelity improved in the user's actual files. Quantify genuine new table cells and false-positive figure flags.
