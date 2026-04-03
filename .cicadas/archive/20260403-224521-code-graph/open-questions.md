# Code Graph Open Questions

This log captures implementation questions and assumptions that came up during execution.

## Open

- None currently.

## Resolved / Assumed

- 2026-04-01: Execute partitions sequentially even though the first partition remains machine-readable as the root of the DAG.
- 2026-04-01: Ship Python-backed semantic query support first and report other language analyzers as unavailable until their extractors are implemented.
- 2026-04-01: Treat graph usage logging as best-effort so observability failures never break user-visible graph commands.
- 2026-04-01: Support time-scoped usage reporting with an optional ISO8601 `--since` filter and keep report generation local-only.
- 2026-04-01: Keep graph guidance conditional in skills, emergence, and routing docs so repos without `.cicadas/graph/` continue to follow the canon-first workflow unchanged.
