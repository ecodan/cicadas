---
summary: "Improve Cicadas repo-scale classification and optional code graph quality so large and mega repositories are routed by real source structure instead of documentation volume, while adding an optional Tree-sitter structural extraction layer that enriches graph facts when available and cleanly falls back when it is not."
phase: "clarify"
when_to_load:
  - "When defining or reviewing goals, scope, success criteria, and risks for graph quality and Tree-sitter-backed extraction improvements."
  - "When validating that repository scale classification and optional graph behavior remain accurate, local, and dependency-light."
depends_on:
  - ".cicadas/archive/20260403-224521-code-graph/prd.md"
  - ".cicadas/archive/20260403-224521-code-graph/tech-design.md"
  - ".cicadas/canon/summary.md"
  - ".cicadas/canon/repo-context.md"
modules:
  - "src/cicadas/scripts/scan_repo.py"
  - "src/cicadas/scripts/graph_build.py"
  - "src/cicadas/scripts/graph_query.py"
  - "src/cicadas/scripts/graph_eval.py"
  - "src/cicadas/scripts/graph_extract"
  - "src/cicadas/SKILL.md"
  - "src/cicadas/emergence"
  - "tests"
index:
  executive_summary: "## Executive Summary"
  project_classification: "## Project Classification"
  success_criteria: "## Success Criteria"
  user_journeys: "## User Journeys"
  scope: "## Scope"
  functional_requirements: "## Functional Requirements"
  non_functional_requirements: "## Non-Functional Requirements"
  open_questions: "## Open Questions"
  risk_mitigation: "## Risk Mitigation"
next_section: "Tech Design"
---

# PRD: Graph Quality & Optional Tree-sitter Extraction

## Progress

- [x] Executive Summary
- [x] Project Classification
- [x] Success Criteria
- [x] User Journeys
- [x] Scope & Phasing
- [x] Functional Requirements
- [x] Non-Functional Requirements
- [x] Open Questions
- [x] Risk Mitigation

## Executive Summary

Graph Quality & Optional Tree-sitter Extraction improves Cicadas' optional code graph so it is more trustworthy in large and mega repositories. The initiative fixes source-vs-documentation discrimination in repo scale classification, upgrades graph search and neighbor routing to use richer graph facts, and adds Tree-sitter as an optional structural parsing layer that broadens symbol/import/test extraction without making Tree-sitter or language toolchains mandatory.

### What Makes This Special

- **Source-first scale decisions** — Cicadas classifies repository size from real code volume and topology instead of being inflated by markdown-heavy SDD artifacts.
- **Layered graph creation** — inventory, structural parsing, resolver, optional semantic enrichment, and query/ranking concerns become explicit layers with clear confidence metadata.
- **Optional Tree-sitter, not required Tree-sitter** — repos with Tree-sitter available gain richer structural facts, while repos without it keep the current stdlib/fallback graph behavior.
- **Graph usefulness over graph existence** — search, neighbors, tests, and observability are improved so maintainers can see whether graph results overlap with real work.

## Project Classification

**Technical Type:** Developer Tool  
**Domain:** Infrastructure / Software Engineering  
**Complexity:** High — the work changes repo classification, graph ingestion, query ranking, optional parser integration, tests, and agent guidance while preserving the lightweight Cicadas runtime contract.  
**Project Context:** Brownfield — this initiative improves the existing optional code graph introduced by the archived `code-graph` initiative and must preserve non-graph Cicadas workflows.

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Trust repo size classification in doc-heavy projects** — a repository with many markdown/spec/SDD files but limited code is no longer incorrectly pushed into large or mega mode solely because of non-source files.
2. **Use graph search in mega repos without silent misses** — graph search ranks across a deterministic, sufficiently broad candidate set so likely operational entrypoints are not dropped before ranking.
3. **Route through real adjacency** — graph neighbors reflects imports, references, calls, ownership, and package/module relationships where available instead of only listing sibling metadata areas.
4. **Benefit from Tree-sitter when present** — JS/TS and Rust repositories with Tree-sitter support get richer structural symbol/import/test facts, while environments without Tree-sitter get clear fallback coverage.

### Technical Success

The system is successful when:

1. Repo scan metadata separates total files, meaningful repository files, code files, code LOC, documentation files, and generated/local exclusions.
2. Graph ingestion records extraction source and confidence for facts, distinguishing fallback, stdlib AST, Tree-sitter structural, resolver-derived, and semantic-enriched facts.
3. Graph queries operate from indexed SQLite data without arbitrary pre-ranking truncation that hides better results.
4. Optional Tree-sitter integration is capability-detected, local-only, and never required for normal Cicadas commands.

### Measurable Outcomes

- Markdown-heavy fixtures with at least 5,000 `.md` files and fewer than 100 code files classify as `normal-repo` unless build/module topology independently indicates larger scale.
- Graph search fixtures with more than 250 low-quality matches still return the intended operational/UI symbol in the top 5.
- Neighbor query fixtures rank areas connected by imports/references/calls above unrelated sibling areas.
- Python `graph tests` and `graph signature-impact` return linked tests from streamed graph builds.
- Rust fixtures index at least modules/functions/structs/enums/use statements/tests when Tree-sitter Rust support is available, and report explicit fallback/unavailable coverage otherwise.

---

## User Journeys

### Journey 1: Builder in an SDD-Heavy Repo — Correct Scale Before Canon

A Builder runs Cicadas in a repository that contains a modest application plus thousands of markdown files produced by SDD tools, archived specs, or local planning workflows. Today, scale classification can interpret those markdown files as meaningful code and choose large/mega repo workflows that are too heavy for the actual codebase. With this initiative, the scan reports total repository context separately from code-bearing scale signals, so the Builder gets a workflow proportional to the source tree. Success looks like Cicadas preserving awareness of docs without letting documentation volume distort branch-start routing or canon strategy.

**Requirements Revealed:** source discrimination, code-vs-doc metrics, scale classification, scan transparency, regression fixtures

---

### Journey 2: Implementation Agent in a Mega Repo — Search and Route Without Early Blind Spots

An implementation agent starts from a symptom, component name, failing test, or signature change in a mega repository. The current graph may contain useful facts but `graph search` can rank only an arbitrary first slice of matching rows, and `graph neighbors` may list metadata siblings rather than actual dependency adjacency. After this initiative, the agent can search deterministic indexed candidates, route through graph edges, inspect confidence, and choose an initial code area with fewer wrong starts. Success looks like graph commands narrowing the search space based on real source relationships rather than broad path coincidence.

**Requirements Revealed:** indexed search, graph-edge neighbors, ranking, confidence metadata, call/import/reference traversal

---

### Journey 3: Cicadas Maintainer — Add Richer Extraction Without Heavy Runtime Requirements

A Cicadas maintainer wants better graph coverage across JS/TS and Rust, but cannot make Tree-sitter or language-specific toolchains mandatory for every Cicadas install. They need a layered extractor design where Tree-sitter is detected and used opportunistically, fallback extractors remain available, and output clearly states what kind of facts were produced. They also need tests that prove optional parser availability changes graph richness without changing the basic CLI contract. Success looks like a maintainable graph ingestion pipeline that can add language depth incrementally without violating Cicadas' portable stdlib-first posture.

**Requirements Revealed:** optional dependency detection, Tree-sitter structural extraction, fallback behavior, extraction confidence, maintainable adapters

---

### Journey 4: Maintainer Evaluating Graph Value — Measure Overlap With Actual Work

A maintainer reviews graph usage after several initiatives and wants to know whether graph output helped, not just whether commands ran. The current usage log records timing and tags, but it does not retain enough structured result metadata to compare predicted areas, files, callers, or tests against files ultimately touched. After this initiative, graph query results and later work context can be correlated locally, giving maintainers evidence about which commands and extractors create value. Success looks like usage reports that identify where graph predictions overlap with real implementation and test activity.

**Requirements Revealed:** result capture, local value proxies, overlap reporting, usage summaries, privacy-preserving local logs

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Builder in SDD-heavy repo** | source discrimination, code-vs-doc metrics, proportional repo mode |
| **Implementation agent in mega repo** | indexed search, edge-based neighbors, better test/caller routing |
| **Cicadas maintainer** | optional Tree-sitter layer, fallback extractors, confidence metadata |
| **Graph value evaluator** | structured result logging, overlap proxies, usage reports |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- Source-aware repo scan metrics that distinguish code files/LOC from docs, specs, generated output, and total repository files.
- Revised scale classification that uses code volume as the scale floor and uses build/module/topology signals as explicit secondary evidence.
- Layered graph ingestion architecture with explicit extraction source and confidence metadata.
- Optional Tree-sitter capability detection and structural extraction path, initially focused on JS/TS and Rust where it closes the largest current gaps.
- Fixed Python streamed-build test-link emission so graph tests and signature-impact can report direct linked tests.
- Search candidate generation that avoids arbitrary first-250-row truncation and can rank large result sets deterministically.
- Neighbor routing that uses graph edges and area connectivity before falling back to seeded area metadata.
- Usage/value logging additions that capture structured graph result summaries sufficient for local overlap analysis.
- A bounded mega-repo graph evaluation harness that can run synthetic scale scenarios and private Jira/Confluence scenario suites from local repo paths without packaging proprietary repos.
- Skill, emergence, README, and routing guidance updates for `graph search`, `neighbors`, `callers`, `callees`, `--exclude-tests`, and Tree-sitter optionality.

**Quality Gates:**
- Tree-sitter absence must not fail graph build, graph query, scan-repo, or non-graph Cicadas workflows.
- Query output must explicitly state coverage and confidence when results are fallback-only, Tree-sitter structural, or semantic-enriched.
- Tests must include doc-heavy repo classification, search truncation regression, edge-based neighbor ranking, Python test links, Tree-sitter-present behavior where locally testable, and Tree-sitter-absent fallback.
- Evaluation reports must compare graph output against explicit scenario expectations and surface search/routing/test-discovery metrics without requiring Jira or Confluence code in the public test suite.

### Growth Features (Post-MVP)

**v2: Broader Language Queries**
- Add Tree-sitter query definitions for Java, Kotlin, Go, Ruby, and additional frontend framework patterns where useful.
- Add configurable repo-specific query overlays for monorepo conventions, generated-code markers, and ownership systems.

**v3: Stronger Resolution**
- Add resolver modules for TS path aliases, package exports, Bazel/Gradle/Maven module boundaries, Rust modules, and workspace-level dependency metadata.
- Expand optional semantic enrichers for TypeScript and Rust where toolchains are available.

### Vision (Future)

- Cicadas graph builds become an evidence-rich local navigation layer where inventory, syntax, module resolution, semantics, and observed work overlap continuously improve routing accuracy without requiring a remote service.

---

## Functional Requirements

### 1. Source-Aware Repo Classification

**FR-1.1:** `scan-repo` must report separate counts for total files, meaningful repository files, source code files, documentation/spec files, generated/local files, code LOC, and documentation LOC.
- Markdown and other documentation files may remain visible in repo context, but must not contribute to the code-volume scale floor.

**FR-1.2:** Repo mode classification must use code-file count and code LOC as the primary scale floor.
- Build systems, declared modules, ownership zones, test surfaces, and language diversity may raise classification through topology evidence.
- Documentation volume alone must not raise a repository to `large-repo` or `mega-repo`.

**FR-1.3:** Scan metadata and repo context must explain classification evidence clearly.
- Evidence should show which signals came from source volume, topology, documentation volume, and exclusions.

### 2. Layered Graph Ingestion

**FR-2.1:** Graph build must separate inventory, structural extraction, resolution, semantic enrichment, storage, and metadata assembly concerns.
- Each layer should have clear inputs, outputs, stats, and failure/fallback behavior.

**FR-2.2:** Graph nodes and edges must record extraction source and confidence.
- Supported sources should include at least `inventory`, `fallback-structural`, `python-ast`, `tree-sitter`, `resolver`, and `semantic`.
- Query output should surface coverage limitations without overstating completeness.

**FR-2.3:** Existing graph artifacts must remain derived and rebuildable.
- Schema evolution may use rebuild-over-migrate when practical, but metadata should expose schema/build version clearly.

### 3. Optional Tree-sitter Extraction

**FR-3.1:** Tree-sitter support must be optional and capability-detected.
- If Tree-sitter libraries or grammars are unavailable, graph build must continue with fallback extractors and report Tree-sitter as unavailable.
- No command may silently install Tree-sitter or external grammars.

**FR-3.2:** When Tree-sitter is available, JS/TS extraction must index imports, exports, top-level symbols, components/entrypoints, tests, and relevant structural relationships more accurately than regex extraction.
- Fallback regex/structural extraction must remain available.

**FR-3.3:** When Tree-sitter Rust support is available, Rust extraction must index modules, functions, structs, enums, impl blocks, use statements, and test functions.
- When unavailable, Rust coverage must be reported as fallback/unavailable rather than advertised as supported.

### 4. Query Quality

**FR-4.1:** `graph search` must rank across a deterministic indexed candidate set and avoid arbitrary pre-ranking truncation.
- Candidate generation should use SQLite indexes or FTS where appropriate.
- Result ranking must demote tests/support/generated artifacts and promote operational/UI entrypoints using source facts and area confidence.

**FR-4.2:** `graph neighbors` must use actual graph connectivity before metadata fallback.
- Imports, references, calls, test links, owns/contains relationships, package/module relations, and derived area adjacency should influence ranking.
- Output must identify whether neighbors are graph-connected or metadata fallback.

**FR-4.3:** `graph tests`, `graph callers`, `graph callees`, and `graph signature-impact` must work with streamed builds.
- Python linked-test edges must be emitted correctly when graph build writes nodes and edges incrementally.

### 5. Observability and Value Proxies

**FR-5.1:** Graph usage logs must capture structured result summaries for query commands.
- Result summaries should include top areas, files, symbols, callers, callees, and tests where applicable, bounded to avoid large logs.

**FR-5.2:** Usage reports must support local overlap/value summaries.
- Reports should estimate overlap between graph-predicted artifacts and later touched files or test paths when that data is available locally.
- Missing overlap data must be reported as unknown, not failure.

### 6. Workflow and Documentation

**FR-6.1:** Cicadas skill and emergence guidance must include the full current graph workflow.
- Guidance should mention `graph search`, `neighbors`, `callers`, `callees`, `tests`, `signature-impact`, `--exclude-tests`, and fallback behavior.

**FR-6.2:** Documentation must state Tree-sitter is optional.
- Docs must explain what improves when Tree-sitter is present and what fallback behavior users should expect when it is absent.

### 7. Mega-Repo Evaluation Harness

**FR-7.1:** Cicadas must provide a local graph evaluation harness for large and mega repo scenarios.
- The harness must accept a local repo path, a scenario JSONL file, and an output path.
- The harness must not require Jira or Confluence source code to be packaged with Cicadas.

**FR-7.2:** Evaluation scenarios must support graph search, route, neighbors, tests, callers, callees, and signature-impact checks.
- Scenarios should allow expected paths, areas, symbols, callers, callees, and tests.
- Scenario results should report top-N hit status, rank, latency, coverage, and failure reason where applicable.

**FR-7.3:** Cicadas must include synthetic scale evaluation fixtures or generators.
- Synthetic repos should exercise doc-heavy scale, search candidate truncation, dense area adjacency, generated/support noise, and Tree-sitter-unavailable fallback.

**FR-7.4:** Evaluation reports must be suitable for iterative comparison.
- Reports should include JSON output and a concise human-readable summary with build coverage, search quality, routing quality, neighbor quality, test discovery, and performance metrics.

---

## Non-Functional Requirements

- **Performance:** `scan-repo` must remain practical on large local repositories; graph search should avoid O(total matches) Python ranking where SQLite/FTS can narrow candidates. Graph build may remain explicit and longer-running, but progress reporting must stay accurate.
- **Reliability:** Missing Tree-sitter packages, missing grammars, parse failures, and partial language support must degrade gracefully with clear analyzer metadata.
- **Security:** Extraction remains local-only. No remote parser downloads, toolchain installs, or telemetry are allowed during normal graph build/query.
- **Maintainability:** Extractors should share a common structural fact interface so languages can be added without duplicating storage/query plumbing. Tests should use real temp repositories and avoid mocks for filesystem/git behavior except pure helper logic.

---

## Open Questions

- Which Tree-sitter Python package is acceptable for optional support: `tree-sitter`, `tree-sitter-language-pack`, language-specific grammar packages, or a small adapter that supports multiple layouts?
- Should FTS tables be part of the graph schema immediately, or should search first use deterministic SQL ordering plus candidate expansion?
- What local signal should define "eventual work" for overlap reporting: git diff since query timestamp, active initiative event logs, explicit graph usage annotations, or a combination?
- Should Java eventually use Tree-sitter as a faster structural fallback before the current semantic harness, or should Java remain on the existing structural plus semantic path for MVP?
- Should private Jira/Confluence scenario files live in a local gitignored `.cicadas/evals/` directory, a developer-specific config path, or both?

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tree-sitter packaging differs across environments | High | Medium | Add a small capability adapter, test unavailable paths, and keep fallback extractors as first-class behavior. |
| Source classification undercounts important non-code repo complexity | Medium | Medium | Report documentation/context metrics separately and let topology/build evidence raise repo mode when warranted. |
| Query ranking becomes complex and hard to reason about | Medium | High | Keep ranking deterministic, expose confidence/source metadata, and add targeted regression fixtures for known failure modes. |
| Tree-sitter creates a false sense of semantic completeness | Medium | High | Label Tree-sitter facts as structural and keep semantic resolution metadata separate. |
| Usage overlap logging becomes noisy or too large | Medium | Medium | Store bounded top-result summaries and calculate overlap only when local touched-file data is available. |
| Schema changes break existing graph artifacts | Low | Medium | Treat graph state as derived and prefer explicit rebuild with clear schema/build metadata. |
