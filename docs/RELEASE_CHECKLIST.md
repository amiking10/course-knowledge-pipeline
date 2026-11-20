# UNI-VERSE: developer release checklist

Use this checklist before a live demo, alpha pilot or investor presentation. **A passing checklist for a demo is not equivalent to production readiness.**

## Release definition

**Current release target:** a repeatable **local desktop CLI + ChatGPT Projects export workflow**. We are NOT releasing a hosted app, a direct AI chatbot connected to SQLite, or a paid self-serve learning service.

## P0 — Must pass for the local-demo release

- [ ] Clone the release branch on clean Windows Python 3.11; install the declared extras successfully.
- [ ] GitHub CI passes unit tests on Windows/Linux Python 3.11 and 3.12.
- [ ] Run the PowerShell pipeline against a **licensed, non-private demonstration course** with **-WithVisualPDF**.
- [ ] Verify that every active parsed document has an export entry and that each page's source heading appears in a Markdown bundle.
- [ ] Run the **verify-export** command with **--require-visuals**; it must exit 0.
- [ ] Check **QUALITY_REPORT.html**, record all unresolved issues, and avoid claiming verified visual accuracy.
- [ ] Create a real ChatGPT Project, manually upload all Markdown bundles/index and visual PDF, paste Project instructions.
- [ ] Ask 10 realistic questions, record answers, original-page citations, abstentions and diagram errors. Mark results as *internal pilot*, not external benchmark.
- [ ] Verify a changed or deleted source cannot still be served from stale SQLite content or export.
- [ ] Do not upload private student data, copyrighted instructor material without authorization, API keys or local SQLite into public GitHub.
- [ ] Rehearse the full demo with locally cached dependencies and a known-good backup set of exports.

## P1 — Needed for a credible private student alpha

- [ ] Independently label a stratified sample including RTL, equations, tables, figures and scans.
- [ ] Compare source-grounded answer/citation accuracy to a baseline ChatGPT/NotebookLM workflow using the same permitted source files.
- [ ] Add telemetry for explicit pilot usage (opt-in, private), error rate, retrieval source hit@k, and task success.
- [ ] Establish real onboarding and support workflow, ownership of demo datasets and deletion guidance.
- [ ] Review dependency and Python package license/security status; pin a reproducible release environment.
- [ ] Resolve or gate critical layout failures in Gantt diagrams (Operating Systems pages 20 and 28).
- [ ] Validate major UI/browser and platform workflows if a UI is introduced.

## P2 — Required before public multi-user launch

- [ ] Product web/app UI with upload, course management, search and tutor chat.
- [ ] Auth, per-user course permissions and tenant isolation.
- [ ] Encrypted private object storage, security review, abuse/rate and token-spend limits.
- [ ] Data retention, deletion and export policy; licensing and privacy/terms.
- [ ] Backend retrieval/LLM orchestration with source-grounded Q&A and visual uncertainty.
- [ ] Production deployment, observability, alerting, backup and incident handling.
- [ ] Robust cost model and subscription/billing if commercialized.

## Metrics we can report today, with limitations

- Synthetic CI results and a sample **214-page** OS corpus demonstrate implementation/integration coverage, not true PDF understanding accuracy.
- Seven difficult scheduling slides drove development of RTL/table/Gantt *candidates*. Six out of eight scheduling timelines passed internal structural consistency, but **none has been independently visually verified**.
- The original course benchmark was an unreviewed, source-page retrieval candidate set, **not answer accuracy**.
- We have no externally validated advantage, retention, revenue, paid users or production uptime to claim.

## Release reporting format

Record demo date, commit SHA, system/Python version, sources and SHA hashes, selected backend, input size, parse duration, current QA warnings, verified export result, comparison baselines and any known missed answer. Do not use a synthetic test pass rate as the product's extraction accuracy.

## Git branching policy

Keep experimental reconstruction and research branches available for development, but make the release branch/README the single source for the first-user workflow. Merge only after CI, review and an export smoke test. No destructive removal of historical experiments in this cleanup.
