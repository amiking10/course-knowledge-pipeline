# v0.6 candidate — evidence-linked retrieval

- Prepared reusable char TF-IDF index eliminates redundant fitting in repeated retrieval benchmarks.
- New `grounded-search` CLI returns page-level evidence with exact file, source ID, source SHA-256, QA flags and machine-extracted provenance.
- No ungrounded generated answers or unsupported confidence claims.
- Baseline 22 candidate questions: 10/22 hit@5 using the default unchanged ranking; **candidates are not independent gold truth**.
- Unit tests assert ranking parity and exactly one index build per evaluation.
