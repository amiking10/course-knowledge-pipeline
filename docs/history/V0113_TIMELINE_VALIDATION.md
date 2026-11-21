# v0.11.3 — Strict timeline validation and diagram classification

## Motivation

Seven-page Operating Systems pilot of v0.11.2: FCFS/SJF examples on slides 12–14 had coherent source table runtimes and proposed intervals, while slides 20 and 28 contained ambiguous/overlapping interval assignments. Slide 30 is a comparison of FIFO/RR task grids without a numeric time axis, rather than a straightforward timestamped Gantt chart.

## Implementation

1. Validate each proposed timeline using strictly increasing original PDF time ticks, one process label per adjacent tick interval, full interval coverage, and no label collisions.
2. Check total durations against the independently recovered, header-associated process runtime table where available. Runtime consistency is mathematical only, not visual confirmation.
3. Classify clearly repeated T1–T5 process-label stacks in non-timeline comparison diagrams. Do NOT generate fictional time durations for such grids.
4. Preserve original PDF and SQLite bodies, and keep all timeline outputs explicitly unverified.

## Run from existing v0.11.2 reconstruction JSON

```powershell
cd "C:\Users\amita\Documents\course-knowledge-pipeline"
git fetch origin
git switch --track origin/feature/v0.11.3-timeline-validation
.\.venv\Scripts\python.exe -m pip install -e ".[inspect,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m course_pipeline.cli validate-timelines "data\structural-v0112\STRUCTURAL_RECONSTRUCTION.json" "data\timeline-v0113"
```

The validator is **offline**, does not require a Gemini key, and reads only the existing JSON. Outputs: TIMELINE_VALIDATION.json and TIMELINE_VALIDATION.html. This action does not edit the input report.

## Optional: run source PDF diagram classification

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course-v041.sqlite3" reconstruct-structures "C:\Users\amita\Documents\University\OperatingSystems" "data\structural-v011\STRUCTURAL_RECOVERY.json" "data\structural-v0113" --limit 7
.\.venv\Scripts\python.exe -m course_pipeline.cli validate-timelines "data\structural-v0113\STRUCTURAL_RECONSTRUCTION.json" "data\timeline-v0113-with-grids"
```

New reconstruction JSON includes source-supported process_grid_diagrams on slides that have repeated T1–T5 task stacks but no numeric time axis.

## Interpretation

- `coherent_candidate_for_review`: geometric and numerical invariants have passed; **not verified visually**.
- `ambiguous_or_inconsistent_candidate`: overlapping processes, missing labels/ticks, gaps, or incompatible durations; do not trust the inferred intervals.
- `process_grid_comparison_without_timeline`: diagram likely represents a per-process comparison without source timestamps. Do not invent Gantt intervals.
- The next stage for pages with ambiguous visual boundaries is targeted original-image understanding with explicit uncertainty and independent cross-checks.

Passing CI cannot establish extraction accuracy on a new PDF collection.