# v0.4.3 evidence-review infrastructure

- `visual-evidence` CLI: original PDF images, primary vs hybrid extraction, native-only number candidates, HTML review gallery and JSON queue.
- `benchmark-official-config` CLI: checks ground-truth and prediction ID coverage, rejects failed/missing outputs, pins official scorer source revision and writes upstream YAML.
- Both operations explicitly preserve `unreviewed` / `prepared_not_scored` status.
- Automated regression tests for source integrity, review queue, scorer pinning and missing prediction rejection.
- Critical scheduling pages 12/13/14/18/20/28/30 identified for manual or visual-model review.

No result here implies that mathematical reasoning, RTL ordering or chart geometry has been verified.
