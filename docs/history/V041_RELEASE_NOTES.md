# v0.4.1 candidate release

- Added token-level comparison using NFKC and Unicode bidirectional-control stripping.
- Prevented mere token order reversals from being classified as content omissions.
- Added detection of missing technical tokens even when character counts are similar.
- Preserved both extraction versions on substantial or ambiguous discrepancies.
- Added severity levels to review entries: critical, major, minor, informational.
- Prioritized visual review by severity, without automatically asserting any page is correct.
- Tests and parser cache version updated.

**QA conclusion:** The v0.4.1 tool is usable as a development candidate, but 86/214 pages are flagged on the six-PDF sample and no high-fidelity certification is claimed.
