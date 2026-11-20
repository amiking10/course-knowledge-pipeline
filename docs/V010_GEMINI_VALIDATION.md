# v0.10 — Gemini image-based PDF audit

## Purpose

Gemini is a **second, fallible visual reviewer** of the original rendered PDF page and the stored Docling+PyMuPDF extraction. It identifies potential missing figures, numbers, formulas, tables, timelines and Hebrew/English RTL order. It **does not** silently replace the extraction or claim human verification.

## Security and spending controls

- API credentials must be available from the user's local PowerShell session as `GEMINI_API_KEY`. Never paste, upload or commit keys. No Gemini key is used in CI.
- The default run is **dry-run** and makes **zero** calls.
- Live calls require the explicit `--live` flag.
- `--max-requests` is a hard cap on **attempted** API calls per invocation (default 7); there are **no automatic retries**. The model may still incur costs on failed requests.
- **The request cap is not a monetary budget or a guarantee of free usage.** Review the project's pricing, billing and model availability in Google AI Studio before running. Gemini Plus/Pro chat subscriptions are separate from the Gemini API billing tiers.
- Original PNGs and extracted PDF text are sent to Google's Gemini service on live runs. Only use this on PDFs you are permitted to send to a cloud provider. If the material is restricted, use an offline method.
- Responses are cached locally by original PDF SHA-256, page, rendered-image hash, extracted text, prompt version, model and structured output schema. Repeated identical pages do not consume requests.
- Cached content and reports may contain course text and model observations; keep them out of Git. Output locations should remain under ignored `data/` paths.

## Installation (local Windows PowerShell)

```powershell
cd "C:\Users\amita\Documents\course-knowledge-pipeline"
git fetch origin
git switch --track origin/feature/v0.10-gemini-vision-audit
.\.venv\Scripts\python.exe -m pip install -e ".[parse,inspect,gemini,dev]"
.\.venv\Scripts\python.exe -m pytest -q
```
If the branch exists locally, use `git switch feature/v0.10-gemini-vision-audit` and `git pull --ff-only`. Keep the same PowerShell window where `GEMINI_API_KEY` is set.

Confirm environment variable **without printing its value**:

```powershell
if ($env:GEMINI_API_KEY) { Write-Host "Key configured" } else { Write-Host "Key not set in this session" }
```

## Seven-page pilot (first safe dry run)

Use the **existing v0.4.1 SQLite DB** and the original source PDF folder; do not run a new 214-page parse for this step.

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course-v041.sqlite3" gemini-audit "C:\Users\amita\Documents\University\OperatingSystems" "data\gemini-audit-v010" --severity critical --limit 7 --max-requests 7
```
Open `data\gemini-audit-v010\GEMINI_QA_REPORT.html`. The seven pages should be `not_run` and `actual_api_attempts=0`. If you see a missing-file or source-SHA mismatch, stop: the DB and source PDFs must correspond.

## Actual Gemini pilot

After checking API pricing and project availability:

```powershell
.\.venv\Scripts\python.exe -m course_pipeline.cli --db "data\course-v041.sqlite3" gemini-audit "C:\Users\amita\Documents\University\OperatingSystems" "data\gemini-audit-v010" --severity critical --limit 7 --max-requests 7 --model gemini-3.8-flash --live
```

Then open `data\gemini-audit-v010\GEMINI_QA_REPORT.html` and share `GEMINI_QA_REPORT.json` for discrepancy analysis (check that it contains no sensitive material). **Do not share the key.** You can redact local paths or course content if needed.

For the first connectivity test only, add `--limit 1 --max-requests 1 --live`. After confirming the result, use `--limit 7 --max-requests 6 --live` to reuse the cached first page and attempt only six additional calls.

## Next stages

1. Determine how many of seven critical pages have concrete evidence-backed discrepancies and which findings remain uncertain.
2. Cross-check numerical discrepancies with PDF native text; never treat consensus of models as independently verified ground truth.
3. Correct parser errors by category, preserving source images and provenance.
4. Run a 30-page AI audit, then optionally all 214 pages using separate opt-in limits. Record model, date, token usage and errors where available.
5. Re-run public benchmarks and held-out question answering. Human ground truth remains necessary for claims of actual precision/recall, even if no manual review is performed.

## Files

- `GEMINI_QA_REPORT.json`: per-page source hashes, model status, potential issues and uncertainty.
- `GEMINI_QA_REPORT.html`: compact locally rendered findings.
- `cache/<sha256>.json`: valid structured responses keyed to source and extraction.
- **No PDF or SQLite rewriting**.

## Current validation level

Unit tests use *mock Gemini responses* to check dry-run, cache reuse, request cap, error handling, SHA invalidation and HTML escaping. They do not prove the API key works on the user's machine or that model observations are correct.


## Model retirement correction (2026-11-20)

The user's first live attempt returned HTTP 404: `gemini-2.5-flash` is no longer available to new users. Google recommended `gemini-3.8-flash`. This release changes the default to `gemini-3.8-flash`; the model still needs a successful live test in this particular API project. Confirm API tier and pricing before retrying. The first request was unsuccessful and did not produce an audit result.
