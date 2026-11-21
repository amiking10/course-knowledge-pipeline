# v0.8 — Human gold annotation and reproducible research workflow

## Why this step matters

Official public PDF benchmarks provide extraction comparisons, but they cannot certify the user's mixed Hebrew/English Operating Systems slides or the accuracy of our own omission-warning detector. **Human-reviewed labels are required** to estimate its false-positive and false-negative behavior.

## A reproducible 30-page review pack

The local source corpus has 6 PDFs and 214 pages; a deterministic review set (`seed=42`) is divided into:

| Stratum | Pages |
|---|---:|
| Critical extraction flags | 7 |
| Major flags | 7 |
| Minor flags | 5 |
| Informational flags | 5 |
| Unflagged comparison cases | 6 |
| **Total** | **30** |

All six original sources are represented. This is a **stratified QA sample, not a representative population survey**. Do not interpret its raw flag proportions as real failure prevalence.

Open `REVIEW.html`, compare original slide artwork against the expandable extracted text, label six dimensions or mark not applicable, and choose **Download review labels JSON**. No data is sent to an external server. All page statuses start as `unreviewed`.

## Generation and evaluation

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v041.sqlite3 review-gold-sample "C:\Users\amita\Documents\University\OperatingSystems" data\gold-review-30 --seed 42
```

After independent review and export of `REVIEW_LABELS_COMPLETED.json`:

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v041.sqlite3 evaluate-review-labels "data\gold-review-30\REVIEW_LABELS_COMPLETED.json" "data\gold-review-30\EVALUATION.json"
```

The evaluator rejects stale source hashes, changed review flags and duplicate page records. Unreviewed labels do **not** count as negative examples. It computes an exploratory confusion matrix (TP, FP, FN, TN), precision and recall **on labeled sample pages only**.

## Public benchmark stage — expanded pilot

GitHub Actions: https://github.com/amiking10/course-knowledge-pipeline/actions/runs/44733832766

The stratified **24-page OmniDocBench image-derived PDF** pilot completed all 72 parser executions with no failures and identical input hashes.

| Metric | Native-text PyMuPDF | Docling | Hybrid |
|---|---:|---:|---:|
| Successful cases | 24 | 24 | 24 |
| Median seconds/page | 0.001 | 16.370 | 16.248 |
| Unofficial prose-token micro recall | 0.0% | 79.13% | 79.13% |
| Unofficial prose-token macro recall | 0.0% | 69.93% | 69.93% |

These are **not official OmniDocBench accuracy scores**. Raster pages have no embedded PDF text, making native PyMuPDF empty by design; the hybrid's native-text fallback is likewise unable to help.

## What remains before a quality-certified v1.0

1. Independently review the initial 30-page local course sample; pay special attention to numerical timelines and Hebrew RTL ordering.
2. Use resulting labels to measure warning-detector precision, recall and false negatives; tune only on a training split and hold out later examples.
3. Complete upstream official OmniDocBench text/formula/table/reading-order scoring, with pinned evaluator environment.
4. Benchmark 200 stratified public pages and a separately labeled born-digital PDF sample.
5. Evaluate actual course Q&A accuracy and unsupported citation/abstention behavior.

The pipeline should remain a *development candidate* until those gates pass.
