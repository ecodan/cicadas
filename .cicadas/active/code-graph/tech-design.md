---
summary: "Implement Code Graph as an optional Cicadas subsystem that builds a routing-oriented graph into SQLite under .cicadas/graph/, exposes deterministic graph CLI commands, seeds area nodes from canon slices when available, and records graph usage/value signals locally. The design favors broad structural coverage across Java, Node/JS/TS, Python, and Rust, with deeper semantic enrichment added opportunistically by language-specific analyzers."
phase: "tech"
when_to_load:
  - "When implementing or reviewing the graph storage, ingestion pipeline, CLI commands, observability, and integration points."
  - "When checking whether graph-backed routing changes still conform to the agreed optional-subsystem design."
depends_on:
  - "prd.md"
  - "canon/tech-overview.md"
  - "canon/repo-context.md"
modules:
  - "src/cicadas/scripts"
  - "src/cicadas/templates"
  - "src/cicadas/emergence"
  - ".cicadas/graph"
index:
  overview: "## Overview & Context"
  stack: "## Tech Stack & Dependencies"
  structure: "## Project / Module Structure"
  adrs: "## Architecture Decisions (ADRs)"
  data_models: "## Data Models"
  interfaces: "## API & Interface Design"
  conventions: "## Implementation Patterns & Conventions"
  security_performance: "## Security & Performance"
  implementation_sequence: "## Implementation Sequence"
next_section: "Implementation Sequence"
---

# Tech Design: Code Graph

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
- [x] Architecture Decisions (ADRs)
- [x] Data Models
- [x] API & Interface Design
- [x] Implementation Patterns & Conventions
- [x] Security & Performance
- [x] Implementation Sequence

---

## Overview & Context

**Summary:** Code Graph adds a new optional graph subsystem to Cicadas that complements existing repo scanning and routing canon with a queryable, local graph index. The implementation is intentionally terminal-first and local-only: repo owners explicitly build the graph, Cicadas writes normalized graph facts into a SQLite database under `.cicadas/graph/`, and graph-aware commands return compact ranked summaries tailored to clarify, implementation, and review workflows.

The design treats canon as the explanation layer and the graph as the navigation layer. Existing `scan-repo`, `repo-context.md`, routing templates, and slice guidance remain authoritative when graph artifacts are absent. When graph artifacts are present, agents can use graph commands to answer inside-out questions such as owning area, neighboring slices, likely callers, likely tests, and signature-change blast radius without exposing the underlying storage or analyzers directly.

### Cross-Cutting Concerns

1. **Optional capability** — The subsystem must never make graph support mandatory for Cicadas or for any repository using Cicadas.
2. **Disk-first efficiency** — Graph data must be written and queried incrementally from disk so local developer machines are not forced into large in-memory graph loads.
3. **Trust through explicit coverage** — Every build and query must surface which languages and analyzers contributed to the results so graph output is interpretable.
4. **Seeded routing model** — Area nodes must reuse canon slices or comparable Cicadas routing artifacts when available so graph routing and canon routing stay aligned.
5. **Observable value** — Graph usage and usefulness must be logged locally from the first release so future investment is guided by evidence.

### Brownfield Notes

This initiative extends existing Cicadas architecture rather than introducing a separate platform. It must fit the current common CLI model, local filesystem state model, and documented branch-start routing behavior. The existing canon/repo scan artifacts must remain valid and useful without graph support, and no graph files should be written into `.cicadas/canon/` because the graph is machine state, not synthesized canon.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Matches current Cicadas runtime and keeps the graph subsystem inside the existing distribution model. |
| **Framework** | Existing script-based CLI | Keeps the new graph commands consistent with the current `cicadas.py` command registry and script structure. |
| **Database** | SQLite | Self-contained, local, disk-backed, query-efficient, and better suited than JSONL-only storage for relationship-heavy traversals on developer machines. |
| **ORM / Query** | `sqlite3` stdlib or thin query helpers | Avoids introducing a heavy ORM for a compact local store while keeping query plans explicit. |
| **Auth** | None | The subsystem is local-only and file-based. |
| **Testing** | `pytest` with temp repos | Matches current repo conventions and supports realistic graph-build/query tests. |
| **Key Libraries** | Python stdlib + selective parser adapters | Preserves Cicadas' lightweight packaging while leaving room for optional analyzer adapters. |

**New dependencies introduced:**
- No mandatory heavyweight runtime dependencies are required for v1 beyond SQLite support already available in Python.
- Optional language adapters may be added behind capability detection if they materially improve JS/TS, Java, or Rust indexing without becoming hard requirements.

**Dependencies explicitly rejected:**
- `neo4j` as a required runtime dependency — rejected for v1 because the product contract is stable Cicadas commands, not open-ended graph querying, and local self-contained packaging is a higher priority.
- Flat-file-only graph storage — rejected because large relationship-heavy graphs would be more expensive to query repeatedly and would push too much indexing work into memory at query time.
- Auto-managed external toolchains — rejected because Cicadas should not silently install Node, Java, or Rust ecosystems just to remain usable.

---

## Project / Module Structure

```
.cicadas/
├── graph/
│   ├── metadata.json              # Build info, freshness, indexed languages, analyzer availability
│   ├── codegraph.sqlite           # SQLite graph store
│   └── usage.jsonl                # Append-only graph usage/value log with end-to-end operation timing
src/cicadas/scripts/
├── graph.py                       # CLI dispatcher for graph subcommands such as build and status
├── graph_build.py                 # Build or rebuild graph artifacts
├── graph_query.py                 # Shared query logic for area/tests/callers/callees/route
├── graph_usage.py                 # Summaries or visualizations for graph usage/value
├── graph_ir.py                    # Normalized graph facts and schema helpers
├── graph_store.py                 # SQLite schema creation and persistence/query helpers
├── graph_extract/                 # Extraction adapters and language-specific collectors
│   ├── common.py                  # Shared file walking, path classification, slice seeding
│   ├── python.py                  # Python extraction
│   ├── javascript.py              # Node/JS/TS extraction
│   ├── java.py                    # Java extraction
│   └── rust.py                    # Rust extraction
└── command_registry.py            # [MODIFIED] register the top-level graph command family
src/cicadas/emergence/
├── clarify.md                     # [MODIFIED] mention graph-backed routing when available
├── bug-fix.md                     # [MODIFIED] mention graph use for symptom-led work
├── tweak.md                       # [MODIFIED] mention graph use when routing is unclear
└── tech-design.md                 # [MODIFIED] mention graph-aware observability and routing conventions
src/cicadas/templates/
├── routing-guide.md               # [MODIFIED] graph-available guidance stays conditional
└── area-map.md                    # [MODIFIED] align area naming with seeded graph areas
```

**Key structural decisions:**
- Graph machine state lives under `.cicadas/graph/`, separate from canon.
- Extraction, storage, and query logic are separated so language-specific ingest can evolve without destabilizing the command surface.
- Shared query helpers return compact ranked summaries, not backend-native rows.

---

## Architecture Decisions (ADRs)

### ADR-1: Make graph support an optional built capability

**Decision:** Graph support is available only after an explicit graph build command produces `.cicadas/graph/` artifacts.

**Rationale:** This preserves Cicadas' current low-friction default, avoids surprising repos that do not want graph state, and keeps graph freshness an explicit repo-owner choice.

**Affects:** graph build/status commands, skill guidance, fallback behavior, docs

---

### ADR-2: Use SQLite as the v1 graph store

**Decision:** Persist the graph in a local SQLite database with sidecar metadata and usage logs rather than storing only JSONL facts or requiring a graph database.

**Rationale:** SQLite satisfies the self-contained local-storage requirement, supports repeated relationship queries better than flat files, and avoids the operational burden of shipping Neo4j as part of v1.

**Affects:** graph store schema, query implementation, build pipeline, performance model

---

### ADR-3: Expose only opinionated Cicadas commands in v1

**Decision:** The public interface is a stable set of graph commands for routing and blast-radius workflows, not raw query language access.

**Rationale:** Cicadas needs deterministic, scriptable operations that are easy for agents to use and benchmark. Open-ended query interfaces would increase scope and user confusion without being necessary for v1 value.

**Affects:** CLI surface, output shaping, skill instructions, test plan

---

### ADR-4: Seed area nodes from canon slices and routing artifacts

**Decision:** Area nodes are seeded from canon slices or equivalent Cicadas routing artifacts when available, with structural heuristics used only as fallback.

**Rationale:** Cicadas already has a routing model for large and mega repos. Reusing it avoids creating a competing area vocabulary and ensures graph routing aligns with canon and future synthesis.

**Affects:** extraction pipeline, data model, routing commands, graph-derived canon integration

---

### ADR-5: Prefer broad structural coverage with selective semantic enrichment

**Decision:** Support Java, Node/JS/TS, Python, and Rust in v1 at a routing-useful structural level, while allowing deeper symbol/call/test links to be stronger in languages where analyzers are readily available.

**Rationale:** The product needs broad routing coverage sooner than it needs perfect semantics everywhere. A routing-first graph is useful before a fully uniform semantic graph exists.

**Affects:** extraction adapters, metadata reporting, command guarantees, benchmark design

---

### ADR-6: Build observability into the graph subsystem from day one

**Decision:** Write graph-local append-only usage logs with initiative/work-type dimensions and support summary/visualization commands plus structured usefulness signals.

**Rationale:** The graph is experimental enough that usage and value must be measurable early. Local observability fits Cicadas' filesystem-first model and avoids centralized telemetry concerns.

**Affects:** query command wrappers, usage logging format, graph usage reporting, skill integration

---

## Data Models

### New Models

```python
from dataclasses import dataclass
from typing import Literal


NodeKind = Literal[
    "repo",
    "area",
    "package",
    "file",
    "symbol",
    "test",
    "build_target",
    "entrypoint",
    "external_dep",
]


EdgeKind = Literal[
    "contains",
    "declares",
    "imports",
    "references",
    "calls",
    "implements",
    "overrides",
    "tests",
    "builds_to",
    "entrys_at",
    "depends_on",
    "neighbors",
    "owns",
]


@dataclass
class GraphNode:
    node_id: str
    kind: NodeKind
    name: str
    language: str | None
    path: str | None
    area: str | None
    build_id: str
    metadata_json: str


@dataclass
class GraphEdge:
    edge_id: str
    kind: EdgeKind
    src_id: str
    dst_id: str
    weight: float | None
    derived: bool
    build_id: str
    metadata_json: str
```

**Key field decisions:**
- `build_id` — allows queries and usage logs to tie results back to a specific graph build and freshness snapshot.
- `area` on nodes — denormalized for routing convenience, but the authoritative area relationship still lives in seeded `owns` and `contains` edges.
- `derived` on edges — distinguishes language-truth edges like `calls` or `declares` from routing products like `neighbors` and `owns`.

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `.cicadas/config.json` | No required schema change in v1 | No |
| `command_registry.py` command surface | Add graph command namespace | No repo-state migration |
| skill/emergence guidance | Add conditional graph usage instructions | No |

### Schema / Migration Notes

The SQLite schema should be versioned in `metadata.json` and rebuilt from scratch when incompatible schema changes occur. Because graph artifacts are optional and derived, v1 should prefer rebuild-over-migrate rather than maintaining complex graph schema migrations.

---

## API & Interface Design

### New Endpoints / Commands

```text
cicadas.py graph build [--languages auto|python,typescript,...] [--force]
Result: builds .cicadas/graph/codegraph.sqlite and metadata.json
Errors: reports unavailable analyzers and partial coverage; non-zero on build failure

cicadas.py graph status
Result: graph availability, build timestamp, schema version, freshness, indexed languages, analyzer coverage

cicadas.py graph area <artifact>
Result: ranked owning-area summary with evidence

cicadas.py graph neighbors <artifact-or-area>
Result: ranked adjacent areas or packages with why they are neighbors

cicadas.py graph tests <artifact>
Result: ranked likely tests and test surfaces

cicadas.py graph callers <symbol>
Result: ranked caller list with path and area context

cicadas.py graph callees <symbol>
Result: ranked callees/dependencies with path and area context

cicadas.py graph signature-impact <symbol>
Result: callers, nearby tests, adjacent areas, and impacted files/packages for a signature change

cicadas.py graph route "<description>"
Result: ranked candidate areas/files/tests for a natural-language task description

cicadas.py graph usage [--initiative NAME] [--since ISO8601] [--view table|json|html]
Result: usage and value summary for graph-backed workflows
```

### Interface Contracts

```python
class GraphQueryResult(TypedDict):
    query_kind: str
    target: str
    graph_available: bool
    freshness: str
    coverage: dict[str, str]
    summary: str
    items: list[dict]


class GraphUsageEntry(TypedDict):
    timestamp: str
    build_id: str
    initiative: str | None
    work_type: str
    branch: str | None
    command: str
    query_kind: str
    target_type: str
    operation_name: str
    end_to_end_ms: int
    graph_query_ms: int | None
    result_count: int
    freshness: str
    coverage: dict[str, str]
    usefulness_tags: list[str]
    metadata: dict
```

### Graph Usage Log Format

`usage.jsonl` is the graph-local append-only observability log. Each line is a single JSON object so the file can be tailed, filtered, summarized, or rendered into HTML without a separate service.

```json
{
  "timestamp": "2026-04-02T04:15:26Z",
  "build_id": "2026-04-02T03:58:10Z-4f3b2d1",
  "initiative": "code-graph",
  "work_type": "initiative",
  "branch": "initiative/code-graph",
  "command": "cicadas.py graph signature-impact src.cicadas.scripts.scan_repo.run_scan",
  "query_kind": "signature-impact",
  "target_type": "symbol",
  "operation_name": "clarify.routing",
  "end_to_end_ms": 842,
  "graph_query_ms": 217,
  "result_count": 9,
  "freshness": "fresh",
  "coverage": {
    "python": "semantic",
    "typescript": "structural",
    "java": "unavailable",
    "rust": "unavailable"
  },
  "usefulness_tags": [
    "helped-route",
    "helped-find-tests"
  ],
  "metadata": {
    "target": "src.cicadas.scripts.scan_repo.run_scan",
    "top_area": "src/cicadas/scripts",
    "top_test": "tests/test_scan_repo.py",
    "result_overlap_pending": true
  }
}
```

**Field rules:**
- `end_to_end_ms` is required and measures the full wall-clock time for the user-visible operation, including command startup, graph access, ranking, and result formatting.
- `graph_query_ms` is optional and measures the narrower graph retrieval/ranking portion when the implementation can isolate it; it must never replace `end_to_end_ms` as the primary performance field.
- `operation_name` identifies the higher-level workflow context such as `clarify.routing`, `implementation.signature-impact`, or `review.test-selection`.
- `initiative` and `work_type` allow filtering usage across initiatives, tweaks, bugs, skills, and ad hoc graph use.
- `coverage` records the language support actually available at query time so usefulness can be interpreted against analyzer limits.

### Backward Compatibility

No existing non-graph Cicadas command should require graph artifacts. Documentation and skill instructions must present graph usage as conditional: prefer graph-backed routing when available, otherwise fall back to `canon/summary.md`, `repo-context.md`, routing guides, slice docs, and targeted code inspection.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Graph scripts | `snake_case` with `graph_` prefix | `graph_build.py` |
| CLI subcommands | `kebab-case` | `signature-impact` |
| SQLite tables | `snake_case` nouns | `graph_nodes` |
| Node kinds / edge kinds | lowercase string enums | `symbol`, `neighbors` |
| Usage tags | dotted or kebab strings | `helped-route`, `helped-find-tests` |

### Error Handling Pattern

```python
def require_graph() -> GraphAvailability:
    availability = load_graph_metadata()
    if not availability.available:
        raise SystemExit("[ERR] Graph not initialized. Run `cicadas.py graph build` or fall back to repo-context and routing docs.")
    return availability
```

**Rules:**
- Never silently pretend graph results are complete when analyzer coverage is partial.
- Graph command failures must explain whether the issue is absence, staleness, unsupported input, or analyzer limits.
- Usage logging is best-effort and must never cause a graph query to fail.

### Testing Pattern

```python
def test_signature_impact_returns_callers_and_tests(tmp_path):
    repo = init_repo_with_python_callers_and_tests(tmp_path)
    build_graph(repo)
    result = run_graph_command(repo, "signature-impact", "pkg.refunds.compute_refund_amount")
    assert "callers" in result.stdout.lower()
    assert "tests" in result.stdout.lower()
```

**Coverage expectations:** Full coverage for absent-graph, stale-graph, and partial-coverage behavior; strong integration coverage for routing and signature-impact flows.  
**Mocking strategy:** Prefer temp repos and real graph builds over mocks for query behavior; mock only clearly isolated adapter-detection branches.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| Local file safety | Graph writes stay under `.cicadas/graph/` and never mutate source files |
| Untrusted repo contents | Treat parsed code and manifests as data only; do not execute repo code during ingestion |
| Analyzer invocation | Detect and invoke optional external tools explicitly; report versions/availability in metadata |
| Output trust | Queries disclose partial coverage and derived routing edges so users understand confidence limits |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| Query latency | Practical local queries on existing graph without rebuild | Use indexed SQLite tables and precomputed routing edges for common traversals |
| Build memory | Avoid full graph residency in memory | Stream extraction results into SQLite in batches |
| Rebuild cost | Explicit and inspectable rather than hidden in everyday commands | Separate `graph build` from normal command flow |
| Report generation | Cheap local summaries | Aggregate from append-only `usage.jsonl` plus graph metadata, not full graph replay |

### Observability

Graph observability is local-first and append-only.
- **Logs:** `usage.jsonl` records each graph command invocation with initiative/work type, branch, target type, workflow operation name, end-to-end wall-clock time, optional graph-only query time, freshness, coverage, and usefulness tags; metadata records build provenance and analyzer availability.
- **Metrics:** command counts by query kind, build frequency, average end-to-end operation time, graph-only query time where available, freshness status distribution, overlap proxies between predicted tests/callers/areas and eventual work.
- **Traces:** v1 does not require distributed tracing; command-level timing and build identifiers are sufficient.

---

## Implementation Sequence

1. **Foundation** *(blocking)* — Define graph IR, SQLite schema, metadata format, and seeded-area loading from canon slices/routing artifacts.
2. **Build pipeline** *(depends on 1)* — Implement file walking, language adapter hooks, normalized node/edge emission, and graph build/status commands.
3. **Core queries** *(depends on 1–2)* — Implement area, neighbors, tests, callers, callees, and signature-impact query paths with ranked summaries.
4. **Route + observability** *(depends on 2–3)* — Add natural-language routing heuristics, usage logging, usefulness tagging hooks, and usage summaries/visualization.
5. **Workflow integration** *(parallel with 3–4)* — Update skill docs, emergence guidance, routing templates, and command registry integration.
6. **Validation & benchmarks** *(parallel with 3–5)* — Add temp-repo integration tests, partial-coverage tests, and benchmark corpus support for routing/value checks.

**Parallel work opportunities:** One stream can own graph storage/build plumbing while another updates docs/skill guidance once the command names and artifact locations are stable. Query output shaping and observability can proceed in parallel after the IR and metadata contracts are set.

**Known implementation risks:**
- Optional analyzers may provide inconsistent semantics across languages; mitigate with explicit coverage reporting and a routing-first contract.
- Seeded areas may be absent in some repos; mitigate with documented fallback heuristics and clear metadata about the source of area assignments.
- Natural-language `graph route` may be noisier than artifact-led queries; mitigate by keeping it secondary to artifact-led commands in both docs and evaluation.
