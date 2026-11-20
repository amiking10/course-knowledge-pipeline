# v0.8 — Human-reviewed reference workflow

- Stratified, deterministic review-page sampling across critical/major/minor/informational/unflagged categories.
- Locally viewable original-PDF screenshot and extracted text comparison, HTML review controls, JSON export.
- Schema with independently markable missing content, number, table, formula, figure and Hebrew RTL correctness.
- Evaluation validates source SHA-256, source names, page numbers and unchanged parser flags; never silently labels unreviewed pages as correct.
- Exploratory precision/recall on labeled pages only. Stratification means unweighted metrics do not estimate real-world prevalence.
- 24-page actual public OmniDocBench micro-to-pilot transition documented.
