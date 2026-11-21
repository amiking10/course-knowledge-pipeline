# UNI-VERSE

**Prepare course PDFs for a source-grounded ChatGPT Project.** UNI-VERSE is a local Windows/Python document extraction and packaging tool, **not** a hosted website or a chatbot. You keep course originals on your computer; UNI-VERSE prepares searchable, page-attributed Markdown plus a visual archive for manual upload into ChatGPT Projects.

**Status:** pre-freeze developer prototype. Parsing mathematics, complex figures, tables and Hebrew/English layout is not guaranteed correct. Upload only materials you have permission to share. Nothing uploads itself.

## Start here — Windows, first time

**You need:** Windows 10/11, PowerShell, Git, **64-bit Python 3.11 or 3.12** (with the `py` launcher), internet access for first-time Python dependencies, and access to ChatGPT Projects for the later study step. The first installation may download large AI/Docling model packages. No API key is required for normal use.

### 1. Install Git and Python

Install [Git for Windows](https://git-scm.com/download/win) and [Python for Windows](https://www.python.org/downloads/windows/). Choose Python **3.11** when possible; ensure the Python launcher is installed. Close and reopen PowerShell after installation.

Check they work:

```powershell
git --version
py -3.11 --version
```

If you installed Python 3.12, use `py -3.12 --version` instead. If the `py` command is missing, fix the Python installation before continuing.

### 2. Clone UNI-VERSE — one time

Open **PowerShell** and run:

```powershell
cd "$HOME\Documents"
git clone https://github.com/amiking10/course-knowledge-pipeline.git
cd course-knowledge-pipeline
git fetch origin
git switch --track origin/feature/uni-verse-course-workflow
```

If this branch is already checked out (existing users), run `git switch feature/uni-verse-course-workflow` followed by `git pull --ff-only` instead. **Until the freeze release is merged into main, the feature branch is the version documented here.** Do not download only individual `.py` files; clone the complete repository.

### 3. Install UNI-VERSE — one time

From inside the cloned repository:

```powershell
.\scripts\setup_windows.ps1
```

The setup script creates `.venv`, installs the supported parser and test dependencies, checks the Docling import, and executes a real PDF parsing smoke test. It stops on installation or validation errors rather than silently switching to a weaker parser.

If PowerShell refuses to execute the script because of an organization-managed policy, follow your organization's approved procedure. Do not bypass managed security controls. For Docling DLL/import failures, consult [Windows troubleshooting](docs/WINDOWS_DOCLING_TROUBLESHOOTING.md).

### 4. Put your courses in folders **outside the Git repository**

Example (change the name to your actual course):

```text
C:\Users\YOUR_USERNAME\Documents\University\
  RX_TX\
    Lecture_1.pdf
    Lecture_2.pdf
    Tutorial_1.pdf
  OperatingSystems\
    Week1.pdf
    Week2.pdf
```

You may use nested folders inside each course. Supported source types: **PDF, PPTX, DOCX**. For the most reliable visual preservation, use PDFs. The original PDFs must **not** go inside `course-knowledge-pipeline`, `.venv`, `data`, or the generated `UPLOAD_TO_CHATGPT` folder. Do not upload your private lectures to GitHub. The script does not need any special filenames.

For a new course, simply create a new folder outside the repository and place its PDFs inside. You do **not** need to edit Python code, create a database or copy a template.

### 5. Generate your course package

While PowerShell is in `course-knowledge-pipeline`, run this command, replacing the path with your real course location:

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "$HOME\Documents\University\RX_TX" -Backend hybrid -WithVisualPDF
```

If your files are elsewhere, use an absolute path:

```powershell
.\scripts\run_pipeline.ps1 -SourceDir "D:\University\Signals" -Backend hybrid -WithVisualPDF
```

The recommended `hybrid` backend compares Docling extraction with native PDF text when available. The script shows stage progress and document completion, creates course-scoped files, and runs a strict **package integrity** check. On a repeat run, unchanged documents are usually reused. **Do not confuse completed stage percentages with elapsed time or extraction accuracy.**

If parsing fails, read the terminal error and the troubleshooting section below. Do not upload an incomplete package.

### 6. Locate the two output folders

For a course directory named `RX_TX`:

```text
course-knowledge-pipeline/
  data/
    courses/
      RX_TX/
        UPLOAD_TO_CHATGPT/
          course_sources_001.md
          course_sources_002.md         (if needed)
          INDEX.md
          COURSE_INDEX.md
          COURSE_KNOWLEDGE.md
          manifest.json
          course_original_visuals.pdf   (with -WithVisualPDF)
          course_original_visuals.manifest.json
        INTERNAL/
          PROJECT_INSTRUCTIONS.md       <-- COPY its text to ChatGPT instructions
          QUALITY_REPORT.html           <-- CHECK this before uploading
          course.sqlite3                <-- KEEP LOCAL
          content_audit/
            REVIEW.html
            CONTENT_AUDIT.zip
          stage_reports/
```

**The folder names are deliberate:**

- `UPLOAD_TO_CHATGPT` contains **Project source files**. Upload the generated bundles, indexes and the original visual PDF. The manifest files preserve provenance.
- `INTERNAL/PROJECT_INSTRUCTIONS.md` is **one copy-ready instruction document**. Open it with Notepad, copy the full text and paste it into the ChatGPT Project's **Instructions** field. **Do not upload it as another source file.**
- `INTERNAL/QUALITY_REPORT.html` identifies suspicious pages. Review formula/diagram issues with the original PDFs before relying on them. `INTERNAL` also holds private caches, the database and logs; never upload the entire folder.

### 7. Create or update your ChatGPT Project

1. In ChatGPT, create a **Project** for your course (e.g., “RX_TX”).
2. Open the Project's **Instructions** setting. Paste the entire content of `INTERNAL/PROJECT_INSTRUCTIONS.md`; replace older instructions rather than appending duplicates.
3. Under Project **Sources/Files**, upload the generated files from `UPLOAD_TO_CHATGPT` (especially **every** `course_sources_*.md` and `course_original_visuals.pdf`). Use the upload limits shown in your account; if you hit a limit, prioritize source bundles and visual PDF, and split/adjust your package if needed.
4. Ask course questions normally, e.g. “Explain Friis noise factor from Lecture 2 and show which terms come from the lecture versus outside knowledge.”

**Important:** ChatGPT may not be able to inspect every visual page automatically. The instructions tell it to distinguish source evidence from AI-reconstructed explanations rather than pretending to have read a missing equation.

### 8. Add a lecture or refresh a course

Copy the new PDF into the **same original course folder** and rerun the **same** `run_pipeline.ps1` command. Review the new quality report, then **replace the previous UNI-VERSE-generated files in that ChatGPT Project**; uploads do not synchronize automatically. Re-copy the updated `PROJECT_INSTRUCTIONS.md` if needed. Keep different courses in different Projects and input folders.

## Quick checks and common problems

| Symptom | What to do |
|---|---|
| `git` or `py` is not recognized | Install Git/Python as in step 1; reopen PowerShell |
| `run_pipeline.ps1` or `.venv` missing | `cd` into the cloned `course-knowledge-pipeline` directory and run setup |
| The course source folder cannot be found | Use its real absolute Windows path, surrounded by quotes |
| Docling import / Windows Application Control error | See [Windows Docling troubleshooting](docs/WINDOWS_DOCLING_TROUBLESHOOTING.md); do not bypass policies |
| `RapidOCR returned empty result!` | Not necessarily fatal: check final parse failures and the quality report |
| Lots of QA warnings on formulas and figures | Open original pages; warnings are review requests, not measured error counts |
| Text-based AI misses a diagram or formula | Supply/check the original PDF page; source evidence outranks a guessed formula |
| ChatGPT still sees older lectures | Remove previous Project uploads and replace them with the refreshed package |
| Course topics or pages appear from another course | Verify each course uses its own input folder, output folder and SQLite database |
| CI passes but a lecture looks wrong | CI tests code and package integrity; it cannot certify extraction accuracy on your lectures |

For optional diagnosis, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Your local full course build and a real ChatGPT Project test are **additional** acceptance gates. CI alone is not a release certificate.

## Advanced options — not required for beginners

- **Troubleshoot OCR:** `-Backend hybrid-no-ocr` is an explicit diagnostic choice only for PDFs with selectable text; it can lose text inside pictures or scans. Normal users should keep `-Backend hybrid`.
- **Skip the human-review sample on refresh:** `-SkipContentAudit` reduces optional review rendering, but it does not improve extraction.
- **Optional AI formula recovery:** `-WithAIRecovery` separately sends selected original PDF pages to a Gemini API and needs `GEMINI_API_KEY`; it can incur charges. **Not needed** when you want GPT to reconstruct missing formulas interactively in your ChatGPT Project. [Technical integration details](docs/AI_INTEGRATION.md).
- **Advanced CLI:** `python -m course_pipeline.cli --help` describes search, benchmarks and experimental recovery tools. They are not part of the standard student workflow.

## For maintainers and release reviewers

- [Architecture and trust boundaries](docs/ARCHITECTURE.md)
- [Data model](docs/DATA_MODEL.md)
- [AI integration and optional recovery](docs/AI_INTEGRATION.md)
- [Windows troubleshooting](docs/WINDOWS_DOCLING_TROUBLESHOOTING.md)
- [Release checklist and remaining gates](docs/RELEASE_CHECKLIST.md)
- [Release notes](docs/RELEASE_NOTES.md)
- [Historical experimental documentation](docs/HISTORY.md)
- [Repository audit](docs/REPOSITORY_REVIEW_2026-11-20.md)

The public repository does not include private course PDFs, trained models, licensing grants for uploaded materials, or an independently validated accuracy benchmark. It does not currently provide a hosted multi-user app, automatic ChatGPT synchronization, user authentication or guaranteed visual extraction accuracy. Research and historic validation documents are intentionally separated from this onboarding guide; do not treat their old metrics as current release claims.
