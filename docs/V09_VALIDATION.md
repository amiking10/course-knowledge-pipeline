# v0.9 — Formula enrichment experiment

## Real motivation: official OmniDocBench score

The official OmniDocBench scorer was run on the *same pinned six-page image-only PDF subset* as the earlier diagnostic. 

- Run: https://github.com/amiking10/course-knowledge-pipeline/actions/runs/44737045204
- Raw official result artifact: https://github.com/amiking10/course-knowledge-pipeline/actions/runs/44737045204/artifacts/14628264298
- Evaluator image: `ghcr.io/zeng-weijun/omnidocbench-eval@sha256:6116ad72172e763b5c43e963d5efebf2093f2362b975f58156ce4f6c9142e617`.
- Dataset revision: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec`.

| Official metric | Six-page baseline Docling |
|---|---:|
| Text normalized edit distance (lower better) | 0.021273413 |
| Formula CDM (higher better) | 0.0 |
| Table TEDS (higher better) | 0.0 |
| Reading-order edit distance (lower better) | 0.261778746 |
| Overall notebook composite / 100 (higher better) | 32.6242 |

Formula samples: two relevant pages. Table samples: one relevant page. These numbers are **too few for an overall accuracy claim**; the low formula/table scores provide a development signal.

## Hypothesis

Docling's `do_formula_enrichment` is disabled by default. This version adds optional `docling-formula` and `hybrid-formula` backends that enable the official formula enrichment pipeline and retain LaTeX-style display-math boundaries when an item is labeled a formula. This requires additional local models and processing resources.

Detected empty formula items remain visible and are flagged. Ordinary Docling and hybrid backends remain unchanged by default.

## Commands

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli benchmark-public data\benchmarks\omni200\manifest.json data\benchmarks\omni200\formula --backend docling-formula --sample 6 --seed 42
```

The end-to-end study pipeline can use `-Backend hybrid-formula` in the Windows script, but expect additional models to download during the first run. Use a distinct source database and export directory.

## Release gates

- Complete a same-page official formula-enriched run with the same scorer image digest and dataset hash.
- Verify formula/CDM and table/TEDS actually improve; do not claim success from plain-text token overlap.
- Review the original PDF for any new spurious LaTeX or repeated cell content.
- Full 214-page OS reparse and bilingual/RTL accuracy evaluation still require the reviewed gold reference set.

The baseline 32.62 composite is a real official *six-page* score, not a benchmark leaderboard score.


## Human-reviewed OS gold sample — manual dependency

A source-hash checked stratified review set was generated from the user's six PDFs and the v0.4.1 extraction database: **30 pages** across all six sources, comprising 7 critical, 7 major, 5 minor, 5 informational and 6 unflagged examples. The artifact `os_gold_review_30.zip` contains `REVIEW.html`, `REVIEW_LABELS_TEMPLATE.json` and original rendered source-page PNGs.

- Each review entry retains `source_id`, `source_sha256`, source filename, PDF page, original severity flags, and extracted text.
- All six correctness dimensions initially have null labels, with `status=unreviewed`.
- The standalone HTML supports saving and reopening partially completed reviews using JSON, with no external transmission.
- User must actually inspect the original slide against extraction and return `REVIEW_LABELS_COMPLETED.json`. The pipeline cannot legitimately self-certify this sample.
- The `evaluate-review-labels` CLI checks original source hashes and unchanged QA flags before reporting sample precision, recall, FP and FN. Unreviewed entries are excluded.
- Working with the first seven critical pages is enough to begin the next fidelity correction, though ≥30 independently reviewed examples are needed for the proposed validation milestone.

**This is an independent human reference gate, not a coding task to be automated away.**
