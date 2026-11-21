# v0.11.1 — Bilingual scheduling structure reconstruction (experimental)

## Scope and safety

This version expands the offline v0.11 geometry layer with conservative **structural candidates** for mixed Hebrew/English lines, borderless process tables, and time-labeled Gantt charts. It also checks explicitly printed average waiting-time arithmetic.

It **does not overwrite original PDF files, alter existing SQLite page bodies or FTS, or claim verified correctness**. A coordinate-based word order is not a confirmed grammatical sentence, and a process label between two times is not proof of the actual segment boundaries. Model findings are hypotheses only.

## Using the seven-page v0.11 report

From the repository checkout:

```powershell
git fetch origin
git switch --track origin/feature/v0.11.1-structural-reconstruction
.\.venv\Scripts\python.exe -m pip install -e ".[inspect,dev]"
.\.venv\Scripts\python.exe -m pytest -q

.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course-v041.sqlite3" reconstruct-structures "C:\Users\amita\Documents\University\OperatingSystems" "data\structural-v011\STRUCTURAL_RECOVERY.json" "data\structural-v0111" --limit 7
```

If the branch already exists locally, switch to it and run `git pull --ff-only` instead.

Outputs:
- `data\structural-v0111\STRUCTURAL_RECONSTRUCTION.json`: per-page candidate RTL lines with bounding boxes, borderless tables, scheduling time rows, source arithmetic checks, and candidate consistency results.
- `data\structural-v0111\STRUCTURAL_RECONSTRUCTION.html`: summary with explicit unverified status.

The command uses **no Gemini calls** and requires no API key. It rejects a changed PDF SHA or changed stored extraction hash relative to the v0.11 report.

## What is established

- RTL candidates are ordered by source-word X coordinates and retain the native word order, so suspicious bidi/Latin and punctuation can be inspected independently.
- Borderless tables require a visible `תהליך` heading, two or more process rows vertically aligned to it, and multiple numbers in stable numeric columns. Runtime/arrival semantics are proposed only when visible `זמן ריצה` or `הגעה` headings align.
- Gantt text candidates require at least three strictly ordered timestamps and at least two nearby process labels. The labels are tentatively associated with neighboring tick intervals; **this does not verify the drawn segment edges**. Vector-supported interval candidates remain available in v0.11's separate report.
- Formula checks parse explicit `average = (...)/N = M` expressions in original PDF text and test the arithmetic independently. For example: `(0+24+27)/3=17` and `(3+16+9+0)/4=7`.

## Known limitations / exit criteria

1. A slide that renders Gantt blocks visually but not as text/vector geometry may still have no reliable intervals; a targeted vision extraction with bounding boxes is needed.
2. Multi-line RTL paragraphs, punctuation and LTR runs are not fully semantically resolved; this implementation makes suggestions rather than rewriting text.
3. Borderless tables may contain candidate columns with unknown headers; do not assume such numbers are runtimes.
4. To claim a measurable fidelity gain, score corrected output against independently verified references on held-out pages and rerun source-grounded Q&A.
5. Numerical accuracy checks validate the printed expression, **not whether the scheduling explanation or the formula inputs are correct**.

PR is a draft until real-page results and reliable recovery can be evaluated. No manual labeling is required to run this diagnostic.
