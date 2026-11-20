# v0.6 — Fast, source-grounded retrieval

## Implementation

- A prepared TF-IDF character-ngram index is constructed once per benchmark run instead of once per question.
- Retrieval candidates retain original file, stable source ID, SHA-256, page number and extraction QA flags.
- No generated answer is labeled as verified. The new `grounded-search` command outputs candidate evidence pages only.
- The original `hybrid-search` command and ranking remain available unchanged.

## Performance measurement on the user's 214-page Operating Systems corpus

Using a locally reconstructed v0.4.1 SQLite export and 22 **unreviewed candidate** retrieval questions:
- Prepared index build: approximately **1.45 seconds** on the test container.
- 132 searches (22 questions × six lexical weights): approximately **0.86 seconds after index build**.
- Default lexical weight of 0.65 retrieved the candidate expected page within top five on **10/22 (45.5%)** questions. This is not a vetted gold benchmark or validated answer accuracy.
- Changing lexical weight alone did not show a robust improvement. We must not overfit to these unreviewed candidates.

The previous API was much slower for repeated benchmark evaluations because it refit the same TF-IDF vocabulary for every query. The prepared index preserves the original default score ordering, verified by synthetic unit tests.

## Example

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db data\course-v041.sqlite3 grounded-search "Round Robin average waiting time" --limit 5
```

Outputs include `has_supporting_pages`, `answer_generated=false`, source hash and unresolved flags. This is a retrieval API, not a generative tutor.

## Remaining gates

- Human-reviewed multilingual Q&A set of 30+ questions with exact page attribution, answerability labels and negative questions.
- Proper held-out retrieval evaluation, false citation and abstention rates.
- Verified original figure evidence for scheduling timelines, process states and signal tables.
- Optional multilingual neural embeddings with pinned models and explicit download consent.
