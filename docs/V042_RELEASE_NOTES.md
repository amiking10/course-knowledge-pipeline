# v0.4.2 — Benchmark harness (development)

- Introduced `benchmark-public` with version-pinned dataset manifests and SHA-256 provenance.
- Deterministic round-robin stratified selection; user-supplied `--sample` and `--seed`.
- Backend-specific predictions compatible with page-stem Markdown handoff.
- Timings, parser failure records and nonzero exit on failed cases.
- Safety validation on relative paths, duplicate identifiers, unsupported datasets and one-page PDF boundaries.
- Synthetic PDF regression tests and separate non-official token-overlap diagnostics.
- No bundled copyrighted benchmark documents and no fabricated official benchmark scores.

**Next:** Acquire official datasets and run official evaluators for OmniDocBench and olmOCR-Bench. Then integrate review-gated vision extraction.
