---
summary: "Execute graph quality work across five sequential partitions: source-aware scan classification, layered extraction with optional Tree-sitter and streamed Python test-link fixes, indexed query/observability improvements, a bounded mega-repo eval harness, and final guidance/regression hardening before the initiative PR."
phase: "tasks"
when_to_load:
  - "When selecting the next implementation task or reviewing graph quality partition progress."
  - "When checking source classification, Tree-sitter optionality, query quality, observability, or guidance completion."
depends_on:
  - "prd.md"
  - "tech-design.md"
  - "approach.md"
modules:
  - "src/cicadas/scripts/scan_repo.py"
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/graph_extract"
  - "src/cicadas/scripts/graph_query.py"
  - "src/cicadas/scripts/graph_usage.py"
  - "src/cicadas/scripts/graph_eval.py"
  - "src/cicadas/SKILL.md"
  - "src/cicadas/emergence"
  - "tests"
index:
  partition_source_scan: "## Partition: feat/source-aware-scan"
  partition_layered_extraction: "## Partition: feat/layered-graph-extraction"
  partition_query_quality: "## Partition: feat/graph-query-quality"
  partition_eval_harness: "## Partition: feat/graph-eval-harness"
  partition_guidance: "## Partition: feat/graph-quality-guidance"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/source-aware-scan"
---

# Tasks: Graph Quality & Optional Tree-sitter Extraction

## Partition: feat/source-aware-scan

- [ ] Add shared source classification helpers for code, test, docs, config, generated/local, and unknown paths <!-- id: 1 -->
- [ ] Extend scan summaries and repo metadata with total, meaningful, code, test, documentation, generated/local, code LOC, and documentation LOC metrics <!-- id: 2 -->
- [ ] Revise repo mode scale floor to use code file count and code LOC, with topology/build/module evidence as the secondary escalation path <!-- id: 3 -->
- [ ] Update repo context output to explain source volume separately from documentation/context volume <!-- id: 4 -->
- [ ] Add markdown-heavy SDD/doc regression tests that remain `normal-repo` when code volume is small <!-- id: 5 -->
- [ ] Run focused scan tests with `uv run pytest tests/test_scan_repo.py` and fix regressions <!-- id: 6 -->

## Partition: feat/layered-graph-extraction

- [ ] Add graph fact metadata helpers for extraction source, confidence, and semantic resolution <!-- id: 20 -->
- [ ] Add optional Tree-sitter adapter with runtime package/grammar capability detection and no network/install behavior <!-- id: 21 -->
- [ ] Fix Python extractor streamed-build state so linked test edges are emitted and `graph tests` works after normal builds <!-- id: 22 -->
- [ ] Update JS/TS extraction to use Tree-sitter structural parsing when available and keep existing fallback behavior when absent <!-- id: 23 -->
- [ ] Implement Rust analyzer status and optional Tree-sitter structural extraction for modules, functions, structs, enums, impl blocks, use statements, and tests <!-- id: 24 -->
- [ ] Update graph build metadata and status output to report Tree-sitter capability and extraction modes per language <!-- id: 25 -->
- [ ] Add graph tests for Tree-sitter-unavailable fallback, Python linked tests, and Rust coverage metadata <!-- id: 26 -->

## Partition: feat/graph-query-quality

- [ ] Add deterministic search candidate generation and optional SQLite FTS setup with basic fallback when FTS is unavailable <!-- id: 40 -->
- [ ] Remove arbitrary pre-ranking `LIMIT 250` behavior from `graph search` and rank a deterministic candidate set <!-- id: 41 -->
- [ ] Add regression test where the intended operational/UI result appears after more than 250 lower-quality matches but still ranks top 5 <!-- id: 42 -->
- [ ] Implement graph-edge-based area adjacency scoring for `graph neighbors` using imports, references, calls, tests, owns/contains, and package/module relations where available <!-- id: 43 -->
- [ ] Update neighbor output to label graph-connected vs metadata-fallback results and include basis/confidence fields <!-- id: 44 -->
- [ ] Add bounded result summaries to graph query metadata and append them to usage entries <!-- id: 45 -->
- [ ] Extend graph usage reports to show result-summary availability and overlap-ready fields while tolerating old log entries <!-- id: 46 -->
- [ ] Run focused graph tests with `uv run pytest tests/test_graph.py` and fix regressions <!-- id: 47 -->

## Partition: feat/graph-eval-harness

- [ ] Define graph eval scenario JSONL schema for search, route, neighbors, tests, callers, callees, and signature-impact checks <!-- id: 50 -->
- [ ] Add `graph eval --repo <path> --scenario-file <jsonl> --output <path>` command or equivalent script entrypoint <!-- id: 51 -->
- [ ] Implement synthetic mega-repo fixture/generator support for doc-heavy scale, search noise, dense adjacency, generated/support noise, and parser-unavailable fallback <!-- id: 52 -->
- [ ] Implement metric aggregation for build coverage, search top-N/rank, route top-N/rank, neighbor hit rate, test discovery, latency, and failure reasons <!-- id: 53 -->
- [ ] Write JSON report output plus concise human-readable summary output <!-- id: 54 -->
- [ ] Document private Jira/Confluence scenario files as local/gitignored inputs outside the public repository <!-- id: 55 -->
- [ ] Add tests for scenario parsing, synthetic fixture execution, metric aggregation, and report compatibility <!-- id: 56 -->

## Partition: feat/graph-quality-guidance

- [ ] Update `src/cicadas/SKILL.md` graph guidance to include `search`, `neighbors`, `callers`, `callees`, `tests`, `signature-impact`, `--exclude-tests`, and fallback behavior <!-- id: 60 -->
- [ ] Update emergence and routing guidance so graph use remains conditional and reflects improved search/neighbor behavior <!-- id: 61 -->
- [ ] Update README and `src/cicadas/README.md` to document source-aware scan metrics, Tree-sitter optionality, analyzer modes, graph eval harness usage, and graph value reporting <!-- id: 62 -->
- [ ] Add or update template/guidance tests for conditional graph guidance and optional Tree-sitter wording <!-- id: 63 -->
- [ ] Run focused regression tests for scan, graph, graph eval, and templates <!-- id: 64 -->
- [ ] Reflect any implementation-driven scope or behavior changes into PRD, tech-design, approach, and tasks before initiative PR <!-- id: 65 -->

## Initiative Boundary

- [ ] Open PR: initiative/graph-quality-treesitter -> master and await merge approval before continuing <!-- id: 100 -->
