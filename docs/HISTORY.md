# Historical documentation (reference only)

UNI-VERSE is being prepared for a frozen **local Windows CLI + ChatGPT Projects export** release.

**For installation and first use, read only [README.md](../README.md).** Current Project instructions come from the generated `INTERNAL/PROJECT_INSTRUCTIONS.md`, not a static template in `docs/`. For sign-off, use [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

The following versioned documents are kept deliberately as engineering history (not required reading and not guaranteed to reflect the current CLI):

- `V04*`, `V041*`, `V042*`, `V043*`: earlier parsing, benchmarking, corpus and visual-quality experiments.
- `V05*`, `V06*`, `V07*`, `V08*`, `V09*`: historical incremental releases and validations.
- `V010*`, `V011*`, `V0111*`, `V0112*`, `V0113*`: AI auditing, structure reconstruction and timeline research.
- `PHASES.md`, `PRODUCT_ACCEPTANCE_REVIEW.md`, `VALIDATION.md`, and the dated `REPOSITORY_REVIEW_2026-11-20.md`: prior plans, evaluation and known limitations.

These files are **not installation instructions**. Their local CLI paths, test counts, providers and historical constraints may be outdated. Avoid linking beginners directly to them.

**Cleanup decisions:**
- The old `docs/CHATGPT_PROJECT_INSTRUCTIONS.md` template was removed to prevent conflicting instructions. The single source of truth is `src/course_pipeline/project_instructions.py`, which generates `INTERNAL/PROJECT_INSTRUCTIONS.md` during each course run.
- Historical research and validation evidence stays version-controlled rather than being destructively dropped during pre-freeze cleanup.
- `scripts/upgrade_v03_export.ps1` remains a legacy migration utility only; do not use it for new courses.
