---
summary: "Execute Code Graph in four partitions: the graph foundation, query CLI, and observability are complete, including optional SQLite-backed graph builds, graph queries, and local usage logging/reporting with end-to-end timing. The remaining work is workflow integration and the initiative-level PR review."
phase: "tasks"
when_to_load:
  - "When selecting the next implementation task or reviewing partition completion for Code Graph."
  - "When checking initiative-only PR boundaries and execution sequencing across graph foundation, queries, observability, and integration."
depends_on:
  - "prd.md"
  - "ux.md"
  - "tech-design.md"
  - "approach.md"
modules:
  - "src/cicadas/scripts"
  - "src/cicadas/emergence"
  - "src/cicadas/templates"
  - ".cicadas/graph"
index:
  partition_foundation: "## Partition: feat/graph-foundation"
  partition_query: "## Partition: feat/graph-query-cli"
  partition_observability: "## Partition: feat/graph-observability"
  partition_integration: "## Partition: feat/graph-workflow-integration"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/graph-workflow-integration"
---

# Tasks: Code Graph

## Partition: feat/graph-foundation

- [x] Add graph artifact path helpers and metadata loading/saving for `.cicadas/graph/` in shared script utilities <!-- id: 1 -->
- [x] Define the normalized graph IR and SQLite schema for nodes, edges, build metadata, and seeded-area relationships <!-- id: 2 -->
- [x] Implement the graph build command scaffold and create `.cicadas/graph/codegraph.sqlite` plus `metadata.json` on successful builds <!-- id: 3 -->
- [x] Implement shared extraction plumbing for file walking, language detection, and fallback structural graph facts <!-- id: 4 -->
- [x] Seed area nodes from canon slices or existing routing artifacts when present, with documented fallback heuristics when absent <!-- id: 5 -->
- [x] Implement `graph status` to report availability, freshness, build ID, and indexed language coverage <!-- id: 6 -->
- [x] Add temp-repo tests for build success, absent graph handling, metadata persistence, and seeded-area behavior <!-- id: 7 -->

## Partition: feat/graph-query-cli

- [x] Register the `graph` command namespace in the common CLI and wire subcommands for area, neighbors, tests, callers, callees, signature-impact, and route <!-- id: 20 -->
- [x] Implement ranked query result formatting that includes freshness and coverage context instead of raw backend rows <!-- id: 21 -->
- [x] Add artifact-led query behavior for `graph area`, `graph neighbors`, and `graph tests` against the SQLite store <!-- id: 22 -->
- [x] Add symbol-led query behavior for `graph callers`, `graph callees`, and `graph signature-impact` with explicit partial-coverage reporting <!-- id: 23 -->
- [x] Add best-effort language enrichment hooks for Python, JS/TS, Java, and Rust and surface analyzer availability in results <!-- id: 24 -->
- [x] Implement `graph route "<description>"` as a secondary routing helper after artifact-led queries are stable <!-- id: 25 -->
- [x] Add integration tests for routing, caller/callee, and signature-impact flows on representative temp repos <!-- id: 26 -->

## Partition: feat/graph-observability

- [x] Add append-only graph usage logging under `.cicadas/graph/usage.jsonl` with the agreed JSONL schema <!-- id: 40 -->
- [x] Capture `operation_name` and required `end_to_end_ms` for every graph-backed command invocation, with optional narrower graph timing where isolatable <!-- id: 41 -->
- [x] Record initiative/work type, branch, query kind, freshness, coverage, and usefulness tags in each usage entry <!-- id: 42 -->
- [x] Add graph usage aggregation and filtering for initiative/time-scope reporting <!-- id: 43 -->
- [x] Implement `graph usage` output modes for table and JSON, plus HTML report generation if practical in the same partition <!-- id: 44 -->
- [x] Add tests for usage logging, timing fields, filtered summaries, and corrupt-log resilience <!-- id: 45 -->

## Partition: feat/graph-workflow-integration

- [ ] Update Cicadas skill and emergence guidance to prefer graph-backed routing when work begins from a symptom, symbol, or failing test and graph artifacts are available <!-- id: 60 -->
- [ ] Update README, internal docs, and routing templates to describe the optional graph subsystem, build flow, and fallback behavior <!-- id: 61 -->
- [ ] Update routing/area guidance to align graph area naming with canon slices and existing routing artifacts <!-- id: 62 -->
- [ ] Add regression tests that verify graph guidance remains conditional and non-graph workflows still function cleanly when graph artifacts are absent <!-- id: 63 -->
- [ ] Review command names, output terms, and observability field names across docs and tests for consistency with the agreed contracts <!-- id: 64 -->

## Initiative Boundary

- [ ] Open PR: initiative/code-graph -> master and await merge approval before continuing <!-- id: 100 -->
