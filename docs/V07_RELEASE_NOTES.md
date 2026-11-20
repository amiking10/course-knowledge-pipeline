# v0.7 candidate — structure-preserving Docling adapter

- Docling TableItem now serialized into per-page Markdown, with explicit failure warnings.
- Picture items retained as visual-inspection markers rather than silently dropped.
- Multi-page table/figure flags added.
- Parser cache invalidated so new results cannot be confused with old exports.
- Synthetic adapter tests plus platform CI.

No claim of human-certified technical diagram or table accuracy.
