---
summary: "Add an optional code-graph capability to Cicadas that repo owners explicitly build and local agents query through stable CLI commands for routing, caller/callee analysis, test discovery, and blast-radius estimation in large and mega repos. The graph supplements canon rather than replacing it, stores machine data under .cicadas/graph/, and includes lightweight observability so Cicadas can measure usage and value."
phase: "clarify"
when_to_load:
  - "When defining or reviewing the goals, scope, success criteria, and risks for optional code-graph support."
  - "When deciding whether graph-backed routing should be used during clarify, implementation, review, or canon work."
depends_on:
  - "background.md"
  - "CodexGraph.md"
  - "canon/product-overview.md"
  - "canon/tech-overview.md"
modules:
  - "src/cicadas/scripts"
  - "src/cicadas/emergence"
  - "src/cicadas/templates"
  - ".cicadas/graph"
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
next_section: "Risk Mitigation"
---

# PRD: Code Graph

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

Code Graph adds an optional, locally built graph-routing capability to Cicadas so agents working in large and mega repos can navigate from a symptom or changed symbol to the right owning area, neighboring areas, impacted callers, and likely tests more quickly. The first release prioritizes stable CLI operations, on-disk local storage, and integration with existing canon and spec workflows over open-ended graph querying or perfect semantic understanding.

### What Makes This Special

- **Canon plus graph, not canon replacement** — Cicadas keeps human-readable canon as the explanation layer while adding a machine-oriented routing substrate for inside-out brownfield work.
- **Optional and self-contained** — Repo owners explicitly build the graph when they want it; Cicadas continues to work without graph artifacts and falls back to existing routing docs.
- **Measured usefulness from day one** — Graph usage and usefulness are observed through local logs and graph-aware summaries instead of being treated as an article of faith.

## Project Classification

**Technical Type:** Developer Tool  
**Domain:** Infrastructure / Software Engineering  
**Complexity:** High — the initiative adds a new local data subsystem, multi-language ingestion strategy, new CLI surface, and observability while preserving Cicadas' low-friction default workflow.  
**Project Context:** Brownfield — this extends existing repo scanning, routing guidance, canon generation, and agent instructions already present in Cicadas.

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Opt into graph support for a repo without changing normal Cicadas usage** — Repo owners can explicitly build the graph, see that it is available, and continue using Cicadas normally when it is not.
2. **Route from a symptom or changed symbol to likely owning code quickly** — An agent can use graph commands to identify an owning area, relevant neighbors, likely callers, and first tests without guessing from directory layout alone.
3. **Use graph results during spec creation and execution** — Builders and agents can reference graph-backed routing when clarifying work, scoping blast radius, selecting tests, and describing affected areas in implementation work.

### Technical Success

The system is successful when:

1. Graph artifacts are stored locally, queried efficiently from disk, and rebuilt explicitly without requiring the entire graph to be loaded into memory.
2. Graph support remains optional, deterministic, and stable behind Cicadas CLI commands even when language-specific analyzers are partially unavailable.

### Measurable Outcomes

- Graph-assisted workflows show a meaningful improvement over canon-only routing on a benchmark corpus, including better top-3 owning-area accuracy and fewer wrong-area starts.
- For graph-assisted runs, Cicadas captures local evidence of value such as overlap between predicted tests/callers and the files or tests ultimately touched.
- `graph status` and usage summaries can report indexed languages, freshness, command frequency, and basic usefulness signals for the local repo.
- Graph usage summaries report end-to-end operation timing for graph-backed workflows so maintainers can weigh routing value against local latency cost.

---

## User Journeys

### Journey 1: Builder in a Mega-Repo — Route Before Spec

A Builder starts from a failing test or a changed API signature in a large codebase where directory structure alone does not reveal the owning area. During Clarify, they use the graph to identify the likely area, neighboring slices, callers, and tests before deciding whether the work is a bug, tweak, or full initiative. They want Cicadas to keep that routing grounded in existing canon so the graph narrows the search while the canon explains the meaning of the areas involved. Success looks like a PRD and later task plan that scope the work correctly on the first try instead of wandering through the wrong parts of the repo.

**Requirements Revealed:** optional graph availability, owning-area routing, neighbor discovery, caller/callee lookup, test discovery, spec-phase integration

---

### Journey 2: Implementation Agent — Signature Blast Radius

An implementation agent is working in a brownfield branch after a function or method signature changes and needs to find the most likely stale callsites and tests. The agent uses graph commands instead of open-ended grepping to inspect direct callers, likely callees, related tests, and nearby impacted areas seeded from canon slices. They need the graph to return ranked, stable summaries that are cheap to consume in a tool-driven workflow and to degrade gracefully when the graph is missing or only partially indexed. Success looks like touching the correct files and tests with fewer wrong turns and a clearer understanding of the likely blast radius.

**Requirements Revealed:** stable CLI commands, ranked summaries, signature-impact analysis, seeded area model, graceful degradation, local efficiency

---

### Journey 3: Cicadas Maintainer — Prove Value, Not Just Availability

A Cicadas maintainer wants to know whether the graph is actually helping and where it is used. They review local graph usage summaries to see which commands are being called, which initiatives or tweak/fix flows rely on them, and whether graph-predicted callers/tests overlap with real work. They do not want to build a cloud telemetry system or central service; local append-only logs and repo-level reports are sufficient for the first version. Success looks like concrete local evidence that graph-backed routing is being used and is adding value, which can then shape future investment in deeper semantics or more language support.

**Requirements Revealed:** graph-local observability, initiative-scoped filters, automatic usage logging, value proxies, usage visualization

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Builder in a Mega-Repo** | optional opt-in, owning-area routing, neighbor discovery, clarify-phase integration, canon alignment |
| **Implementation Agent** | callers/callees, signature-impact, first tests, ranked summaries, partial-language tolerance |
| **Cicadas Maintainer** | usage logging, usefulness signals, initiative filters, local reports, benchmark support |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- Optional graph subsystem under `.cicadas/graph/` with SQLite storage, metadata, and explicit build/status commands
- Stable CLI commands for routing and blast-radius workflows: build, status, area, neighbors, tests, callers, callees, signature-impact, and route
- Broad structural support for Java, Node/JS/TS, Python, and Rust with best-effort deeper symbol and call analysis where available
- Graph schema centered on repo, seeded areas, packages/modules, files, symbols, tests, build targets, entrypoints, and external dependencies
- Integration updates to Cicadas docs, templates, and skill guidance so graph support is used when present and ignored safely when absent
- Graph-local observability with usage logging, initiative/tweak/bug dimensions, and a usage/visualization command

**Quality Gates:**
- Graph support is never required for existing Cicadas flows and missing graph artifacts produce clear fallback guidance
- Queries return ranked summaries rather than raw graph dumps and operate against on-disk graph storage without full-memory preload

### Growth Features (Post-MVP)

**v2: Deeper Semantics**
- Expand richer symbol-level semantics, implementation relationships, and repo-specific operational edges across more languages with stronger guarantees

**v3: Graph-Derived Canon**
- Feed graph-backed routing information into generated routing guides, area docs, and targeted canon reconciliation more directly

### Vision (Future)

- A mature Cicadas navigation layer where canon explains the terrain, the graph traverses it, and local evidence continuously shows which graph-backed workflows provide the most value

---

## Functional Requirements

### 1. Graph Availability & Lifecycle

**FR-1.1:** Repo owners must explicitly opt into graph support by building graph artifacts for the repository.
- Graph support is considered available only after a successful build command produces the required artifacts under `.cicadas/graph/`.
- Existing Cicadas flows must remain unchanged when graph artifacts do not exist.

**FR-1.2:** Cicadas must expose graph readiness and freshness through a deterministic status command.
- The command must report graph schema/build information, indexed languages, analyzer availability, and whether graph data is fresh enough to use.

### 2. Graph Query Surface

**FR-2.1:** Cicadas must provide stable graph-backed CLI operations for routing and local traversal.
- MVP commands include `graph area`, `graph neighbors`, `graph tests`, `graph callers`, `graph callees`, `graph signature-impact`, and `graph route`.
- Outputs must be ranked summaries intended for agents and builders, not low-level query output.

**FR-2.2:** Signature-change analysis must be a first-class operation.
- `graph signature-impact` must help users understand likely stale callsites, impacted tests, and nearby affected areas for a symbol or method.

**FR-2.3:** Graph queries must degrade gracefully when semantic depth is limited.
- Partial language support or missing analyzers may reduce coverage, but commands must report that limitation explicitly rather than silently pretending to be complete.

### 3. Graph Data Model

**FR-3.1:** The graph must include node and edge types sufficient for routing, adjacency, and blast-radius analysis.
- Required node families include repo, area, package/module, file, symbol, test, build target, entrypoint, and external dependency.
- Required edge families include containment, declarations, imports/references, calls, implementation relationships, test coverage links, build/runtime links, and derived routing adjacency.

**FR-3.2:** Area nodes must be seeded from canon slices or equivalent existing routing artifacts when available.
- When explicit slice or routing guidance exists, the graph must reuse it instead of inventing an unrelated area model.
- When no slice data exists, the implementation may derive fallback areas from structural heuristics.

### 4. Ingestion & Language Support

**FR-4.1:** The graph build process must support Java, Node/JS/TS, Python, and Rust in the first release.
- v1 may provide broad structural extraction everywhere and deeper symbol/call analysis only where analyzers are available and reliable.

**FR-4.2:** Graph ingestion must remain local and efficient on developer machines.
- The build process must write normalized graph facts incrementally and avoid requiring the full graph to live in memory.

**FR-4.3:** Cicadas must not require heavyweight non-Python toolchains to be auto-installed in order to function.
- Language-specific analyzers may be detected and used opportunistically, but graph support remains optional and partial coverage is acceptable.

### 5. Workflow Integration

**FR-5.1:** Cicadas skill and emergence guidance must teach agents when to prefer graph-backed routing.
- Clarify, bug-fix, tweak, review, and branch-start guidance must mention graph use when work begins from a symptom, symbol, failing test, or likely signature change.

**FR-5.2:** Graph output must support better spec creation and execution planning.
- Builders and agents must be able to use graph results to scope work, identify adjacent areas, estimate blast radius, and choose first tests.

### 6. Observability & Evaluation

**FR-6.1:** Cicadas must record graph usage in a local append-only log under `.cicadas/graph/`.
- Each entry must include timestamp, command, query kind, work dimension (initiative/tweak/bug/skill/ad hoc), branch, graph build identity, and end-to-end operation timing for the user-visible graph operation.

**FR-6.2:** Observability must include automatic value proxies, not just raw usage counts.
- The system must capture enough structured data to estimate whether graph-returned areas, callers, or tests overlap with eventual work.

**FR-6.3:** Cicadas must provide a usage summary or visualization command.
- The report must support filtering by initiative or work type and show command frequency, latency, and usefulness signals.

---

## Non-Functional Requirements

- **Performance:** Query commands should operate from on-disk graph storage without full reload and remain practical on local developer machines; graph rebuild is explicit rather than hidden in frequent workflows.
- **Reliability:** Missing graph artifacts, stale builds, or partial analyzer availability must be surfaced clearly and must never break non-graph Cicadas workflows.
- **Security:** Graph ingestion and query commands must remain local-only by default and must not require remote services or silent installation of heavyweight external toolchains.
- **Maintainability:** The graph subsystem should use a clear internal IR, stable CLI contracts, and test coverage for both absent-graph fallback paths and graph-backed happy paths.

---

## Open Questions

- What freshness threshold should mark the graph as stale enough to warn or block certain queries? This affects user trust and rebuild guidance.
- How much semantic depth should be guaranteed per language in v1 versus treated as best-effort? This affects benchmark design and user expectations.
- Should graph-derived routing summaries eventually be persisted into canon artifacts during synthesis, or remain purely query-time behavior until v2?

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Graph scope expands into an open-ended platform project | Medium | High | Keep v1 focused on optional SQLite-backed CLI routing, seeded areas, and explicit benchmarkable commands rather than raw graph querying or perfect semantics |
| Multi-language extraction is uneven and undermines trust | High | High | Be explicit about partial coverage, report analyzer availability, and bias v1 guarantees toward routing-first structural value instead of full semantic promises |
| Local builds or queries are too expensive on developer machines | Medium | High | Use on-disk SQLite storage, incremental writes, explicit rebuilds, and ranked summaries rather than loading full graph structures into memory |
| The graph is used but its value is unclear | Medium | Medium | Add graph-local usage logging, usefulness proxies, and summary reports in v1 so investment decisions can be grounded in repo-local evidence |
