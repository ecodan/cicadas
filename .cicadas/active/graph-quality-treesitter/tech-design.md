---
summary: "Implement graph quality improvements through a source-aware repo inventory, layered graph extraction pipeline, optional Tree-sitter adapter, deterministic indexed query improvements, edge-based neighbor routing, and richer local usage/value metadata while preserving Cicadas' no-mandatory-dependency runtime contract."
phase: "tech"
when_to_load:
  - "When implementing or reviewing repo classification, graph extraction, graph query, optional Tree-sitter support, and usage/value logging changes."
  - "When checking that Tree-sitter remains optional and fallback behavior remains explicit."
depends_on:
  - "prd.md"
modules:
  - "src/cicadas/scripts/scan_repo.py"
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/graph_ir.py"
  - "src/cicadas/scripts/graph_store.py"
  - "src/cicadas/scripts/graph_build.py"
  - "src/cicadas/scripts/graph_query.py"
  - "src/cicadas/scripts/graph_usage.py"
  - "src/cicadas/scripts/graph_eval.py"
  - "src/cicadas/scripts/graph_extract"
  - "src/cicadas/SKILL.md"
  - "src/cicadas/emergence"
  - "tests"
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
next_section: "Approach"
---

# Tech Design: Graph Quality & Optional Tree-sitter Extraction

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

**Summary:** This initiative upgrades the existing optional Code Graph subsystem by making repository inventory source-aware, separating graph build into explicit layers, and adding an optional Tree-sitter structural parser adapter. The design keeps Cicadas' current local, file-based, Python-stdlib-first model: Tree-sitter is detected at runtime and improves graph coverage when available, but all graph commands continue to work with fallback extractors when it is absent.

The implementation focuses on the observed failure modes from the archived `code-graph` review: markdown-heavy SDD repositories inflate scale classification, graph search can silently miss relevant nodes due to arbitrary pre-ranking truncation, neighbors are metadata listings rather than graph traversal, Python test links are incomplete under streamed builds, Rust support is advertised without extraction, graph usage cannot prove value, and skill guidance omits newer graph workflows.

UX is intentionally skipped for this technical initiative by Builder direction. Operator-facing behavior is captured here through CLI contracts, fallback messages, metadata fields, and testable command output.

### Cross-Cutting Concerns

1. **Optionality** - Tree-sitter and grammar packages must never be required for Cicadas startup, scan, graph build, query, or non-graph workflows.
2. **Source discrimination** - code volume, documentation volume, generated/local files, and total repo context must be tracked separately.
3. **Confidence transparency** - graph facts and query output must state whether they came from inventory, fallback extraction, Tree-sitter structural parsing, resolver heuristics, or semantic enrichment.
4. **Disk-first scale** - graph search and neighbor queries must operate from SQLite indexes and bounded result sets rather than loading the whole graph.
5. **Derived state** - `.cicadas/graph/` remains rebuildable local machine state; schema changes should favor explicit rebuild over complex migrations.

### Brownfield Notes

The existing graph subsystem already has SQLite storage, staged writes, metadata, progress logs, Java semantic enrichment, Python AST extraction, regex JS/TS extraction, query commands, and usage logging. This design preserves those public commands and evolves internals incrementally. Non-graph Cicadas flows, canon generation, lifecycle scripts, and existing branch/start guidance must continue to work when `.cicadas/graph/` is absent.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Matches Cicadas runtime and current scripts. |
| **Framework** | Existing script-based CLI | Keeps graph commands under `cicadas.py graph`. |
| **Database** | SQLite | Existing local graph store; suitable for indexed search and adjacency queries. |
| **Parser Layer** | Optional Tree-sitter adapter plus existing fallback extractors | Improves structural coverage without making parser packages mandatory. |
| **Testing** | pytest/unittest with temp repos | Matches project convention and tests real filesystem/git behavior. |
| **Key Libraries** | Python stdlib required; Tree-sitter packages optional | Preserves lightweight default installation. |

**New dependencies introduced:**
- No mandatory runtime dependency is introduced.
- Optional support may detect packages such as `tree_sitter`, `tree_sitter_language_pack`, `tree_sitter_languages`, or language-specific grammar packages if already installed.

**Dependencies explicitly rejected:**
- Mandatory Tree-sitter dependency - rejected because Cicadas must remain usable in stdlib-only environments.
- Silent grammar downloads or toolchain installs - rejected because graph build must be local-only and explicit.
- Replacing SQLite with an external graph database - rejected because current command contracts need local derived state, not a service dependency.

---

## Project / Module Structure

```
src/cicadas/scripts/
├── scan_repo.py                    # [MODIFIED] source-aware metrics and classification
├── utils.py                        # [MODIFIED] shared source/docs/generated classification helpers
├── graph_ir.py                     # [MODIFIED] extraction source/confidence metadata conventions
├── graph_store.py                  # [MODIFIED] optional FTS/index support and schema metadata
├── graph_build.py                  # [MODIFIED] layered build orchestration and analyzer metadata
├── graph_query.py                  # [MODIFIED] deterministic search and graph-edge neighbor routing
├── graph_usage.py                  # [MODIFIED] bounded result summaries and overlap reporting
├── graph_extract/
│   ├── common.py                   # [MODIFIED] shared layered extraction contracts
│   ├── tree_sitter_adapter.py      # [NEW] optional runtime adapter and grammar capability detection
│   ├── javascript.py               # [MODIFIED] fallback JS/TS structural extraction with Tree-sitter capability reporting
│   ├── rust.py                     # [MODIFIED] Rust structural extraction via Tree-sitter when available
│   ├── python.py                   # [MODIFIED] streamed-build linked-test fix
│   └── java.py                     # [MODIFIED] metadata alignment; semantic harness remains primary
├── graph_extract/queries/          # [NEW] query definitions if adapter package supports raw queries
│   ├── javascript.scm
│   ├── typescript.scm
│   └── rust.scm
└── graph.py                        # [MODIFIED] help/output text for search, filters, coverage

tests/
├── test_scan_repo.py               # [MODIFIED] doc-heavy classification regressions
├── test_graph.py                   # [MODIFIED] query/extraction regressions
└── fixtures/                       # [MODIFIED] JS/TS/Rust/search/neighbor fixtures

src/cicadas/
├── SKILL.md                        # [MODIFIED] graph workflow guidance
├── emergence/                      # [MODIFIED] graph routing guidance where relevant
└── README.md                       # [MODIFIED] optional Tree-sitter and graph quality notes
```

**Key structural decisions:**
- Tree-sitter capability detection lives in a dedicated adapter instead of inside language extractors.
- Shared source classification helpers live in `utils.py` so `scan_repo.py` and graph build use the same meaning of code/docs/generated.
- Query improvements stay behind the existing `graph search` and `graph neighbors` commands.

---

## Architecture Decisions (ADRs)

### ADR-1: Keep Tree-sitter Optional and Runtime-Detected

**Decision:** Tree-sitter is used only when import and grammar capability checks succeed at runtime.

**Rationale:** Cicadas has a lightweight local runtime contract. Optional parser support can improve graph quality, but mandatory parser dependencies would make installation and portability worse.

**Affects:** `graph_extract/tree_sitter_adapter.py`, JS/TS extractor, Rust extractor, graph metadata, docs

---

### ADR-2: Split Source Scale From Repository Context

**Decision:** Repository scan metadata will track code files/LOC separately from documentation/spec files and total repository files, and repo mode scale floors will use code volume rather than all meaningful files.

**Rationale:** Cicadas should still see docs/specs for context, but workflow scale must reflect source complexity. Markdown-heavy SDD directories should not independently force large/mega behavior.

**Affects:** `scan_repo.py`, `utils.py`, repo metadata, repo context, scan tests

---

### ADR-3: Treat Tree-sitter Facts as Structural, Not Semantic

**Decision:** Tree-sitter-extracted nodes and edges are labeled structural and unresolved unless a resolver or semantic enricher upgrades them.

**Rationale:** Tree-sitter parses syntax but does not type-resolve call targets or package semantics. Explicit confidence avoids overstating graph completeness.

**Affects:** graph metadata, query headers, usage result summaries, docs

---

### ADR-4: Use SQLite Candidate Generation for Search

**Decision:** `graph search` will use deterministic SQLite candidate generation, FTS where available, and a bounded post-rank stage rather than `LIMIT 250` before ranking.

**Rationale:** Mega repos can have thousands of partial matches. Arbitrary early truncation hides better results even when graph data exists.

**Affects:** `graph_store.py`, `graph_query.py`, tests

---

### ADR-5: Rank Neighbors From Graph Connectivity First

**Decision:** `graph neighbors` will aggregate area adjacency from graph edges before falling back to seeded area metadata.

**Rationale:** Neighbor output should answer dependency/routing adjacency, not simply list sibling areas. Metadata fallback remains useful only when graph facts are too sparse.

**Affects:** `graph_query.py`, graph edge metadata, tests

---

### ADR-6: Capture Bounded Result Summaries for Value Analysis

**Decision:** Usage entries for graph queries will include bounded top-result summaries and later reports may compare them with locally touched files/tests.

**Rationale:** Command counts and usefulness tags show activity, not efficacy. Bounded result metadata allows local overlap analysis without large logs or external telemetry.

**Affects:** `graph_usage.py`, `graph.py`, query meta payloads, usage reports

---

## Data Models

### New Models

```python
from dataclasses import dataclass, field
from typing import Literal

SourceClass = Literal["code", "test", "docs", "config", "generated", "local", "unknown"]
ExtractionSource = Literal[
    "inventory",
    "fallback-structural",
    "python-ast",
    "tree-sitter",
    "resolver",
    "semantic",
]
Confidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class SourceMetrics:
    total_file_count: int = 0
    meaningful_file_count: int = 0
    code_file_count: int = 0
    test_file_count: int = 0
    documentation_file_count: int = 0
    generated_or_local_file_count: int = 0
    estimated_code_loc: int = 0
    estimated_documentation_loc: int = 0


@dataclass(frozen=True)
class ExtractedFactMetadata:
    extraction_source: ExtractionSource
    confidence: Confidence
    semantic_resolution: Literal["unresolved", "heuristic", "resolved"] = "unresolved"
    analyzer: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TreeSitterCapability:
    available: bool
    package: str | None
    language: str
    grammar_available: bool
    mode: Literal["unavailable", "available"]
    detail: str | None = None
```

**Key field decisions:**
- `code_file_count` and `estimated_code_loc` are separate from `meaningful_file_count` so docs remain visible without driving scale floors.
- `semantic_resolution` is separate from `extraction_source` so Tree-sitter structural facts can later be resolved without changing their origin.
- Capability status is per language because Tree-sitter may be installed for JS/TS but not Rust.

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `ScanSummary` | Add `source_metrics` and code/docs counters | No persistent migration; next scan rewrites metadata |
| `repo.json scan` | Add code/docs/generated count fields and classification evidence | No; scan artifacts are generated |
| `GraphNode.metadata` | Standardize `extraction_source`, `confidence`, `semantic_resolution`, `surface_kind` | No; graph artifacts are rebuilt |
| `GraphEdge.metadata` | Standardize `extraction_source`, `confidence`, `semantic_resolution`, `neighbor_reason` | No; graph artifacts are rebuilt |
| `metadata.json analyzers` | Add Tree-sitter capability detail per supported language | No; graph artifacts are rebuilt |
| `usage.jsonl` entries | Add bounded `result_summary` and optional `overlap` fields | Backward-compatible; reports handle missing fields |

### Schema / Migration Notes

Graph schema changes should prefer rebuild-over-migrate. If FTS is added, `initialize_schema` should create FTS tables only when SQLite supports them; otherwise `metadata.json` should report `search_index=basic` and search should use deterministic SQL fallback.

---

## API & Interface Design

### Commands

Existing commands remain:

```text
python src/cicadas/scripts/cicadas.py scan-repo
python src/cicadas/scripts/cicadas.py graph build [--languages auto]
python src/cicadas/scripts/cicadas.py graph status
python src/cicadas/scripts/cicadas.py graph search <query> [--kind ...] [--exclude-tests] [--limit N]
python src/cicadas/scripts/cicadas.py graph neighbors <artifact> [--exclude-tests]
python src/cicadas/scripts/cicadas.py graph tests|callers|callees|signature-impact <symbol> [--exclude-tests]
python src/cicadas/scripts/cicadas.py graph usage [--initiative name] [--since ISO8601] [--view table|json|html]
```

### Output Contracts

`graph status` should include:

```text
Graph: available
Build ID: ...
Freshness: ...
Indexed Languages: python, javascript, typescript, rust
Analyzers: python=python-ast, javascript=fallback-structural, rust=tree-sitter, java=semantic
Tree-sitter: javascript=available, typescript=available, rust=unavailable
Search Index: fts|basic
```

`graph search` result rows should include at least:

```text
- symbol: IssueView (path; area: web-issue; source: fallback-structural; confidence: medium; surface: ui_surface)
```

`graph neighbors` should identify graph vs fallback basis:

```text
- Neighbor: platform-api (score: 12.5; basis: imports,calls; files: 1200; confidence: medium)
- Note: metadata fallback used for areas without graph-connected edges.
```

### Interface Contracts

```python
class StructuralExtractor:
    language: str

    def analyzer_status(self) -> dict:
        ...

    def extract(self, *, root, file_entries, build_id, area_lookup, progress=None, emit=None):
        """Emit GraphNode/GraphEdge facts and return stats."""
```

```python
class TreeSitterAdapter:
    def capability(self, language: str) -> TreeSitterCapability:
        ...

    def parse(self, *, language: str, path: Path, source: str):
        """Return a parsed tree or raise a local adapter error handled by caller."""
```

### Backward Compatibility

- Existing graph commands and flags remain valid.
- Existing graph DBs may be rebuilt explicitly; missing new metadata fields default to unknown/basic.
- Existing usage logs remain readable; missing result summaries are treated as unavailable.
- Repos without Tree-sitter continue through fallback extraction with explicit analyzer metadata.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|------------|---------|
| Functions | `snake_case` | `classify_source_path()` |
| Dataclasses | `PascalCase` | `SourceMetrics` |
| Constants | `UPPER_SNAKE` | `CODE_EXTENSIONS` |
| Files | existing `snake_case.py` | `tree_sitter_adapter.py` |

### Error Handling Pattern

```python
try:
    capability = adapter.capability("rust")
except Exception as exc:
    capability = TreeSitterCapability(
        available=False,
        package=None,
        language="rust",
        grammar_available=False,
        mode="unavailable",
        detail=str(exc),
    )
```

**Rules:**
- Optional parser failures must become analyzer metadata, not graph build failures.
- Query failures due to absent graph remain clear user-facing errors with fallback guidance.
- Parse failures for individual files should be counted and reported without aborting the build.

### Testing Pattern

```python
def test_scan_does_not_classify_markdown_heavy_repo_as_large(self):
    self.init_git()
    # create many docs and few code files in a temp repo
    _tree, metadata_path, _context = scan_repo.run_scan()
    metadata = json.loads(metadata_path.read_text())
    self.assertEqual(metadata["repo_mode"], "normal-repo")
```

**Coverage expectations:** regression coverage for every review finding and every new fallback path.  
**Mocking strategy:** use real temp repos for scan/build/query; use small monkeypatches only for optional Tree-sitter capability probes where local packages are not installed.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|------------|
| Unexpected parser package behavior | Use only locally installed packages; no network calls or downloads. |
| Untrusted repository files | Read source as text with bounded error handling; do not execute source. |
| Usage log size/privacy | Store bounded result summaries only; keep logs local under `.cicadas/graph/`. |
| Path handling | Normalize repo-relative paths and avoid shelling out with source-controlled arguments. |

### Performance

| Concern | Target | Approach |
|---------|--------|----------|
| Doc-heavy scan | Classification remains O(files) and avoids expensive doc LOC where not needed for code scale | Separate code/docs counters and reuse existing threaded scan. |
| Search in mega repos | No arbitrary first-page truncation before ranking | Use FTS if available, deterministic SQL fallback, and bounded post-rank candidates. |
| Graph build memory | Avoid full graph in memory where current spooler supports streaming | Keep emit/spool pattern and fix extractors that assume local node lists. |
| Tree-sitter parsing | Build remains explicit; parse failures are file-local | Parse only supported source extensions and stream emitted facts. |

### Observability

- **Logs:** graph build progress should include Tree-sitter capability and parse failure counts.
- **Metrics:** metadata should include source metrics, analyzer modes, indexed symbol counts, search index mode, and Tree-sitter availability.
- **Usage:** query usage entries should include bounded `result_summary` and report overlap fields when available.

---

## Implementation Sequence

1. **Source classification foundation** *(blocking)* - add shared source classification and scan metadata changes with doc-heavy regression tests.
2. **Graph metadata and extraction contracts** *(depends on 1)* - standardize extraction source/confidence metadata and fix streamed Python test links.
3. **Optional Tree-sitter adapter and language extraction** *(depends on 2)* - add capability detection, Rust structural extraction, JS/TS fallback metadata, and fallback tests.
4. **Query quality** *(depends on 2 and 3)* - improve search candidate generation, edge-based neighbors, and output confidence.
5. **Mega-repo evaluation harness** *(depends on 4)* - add scenario schema, synthetic scale fixtures, local external-repo eval execution, and JSON/markdown reports.
6. **Usage/value proxies** *(depends on 4 and informed by 5)* - add result summaries and local overlap reporting fields aligned with eval metrics.
7. **Guidance/docs and final regression pass** *(depends on all)* - update skill/emergence/docs and run focused graph/scan/eval tests.

**Parallel work opportunities:** source classification can proceed independently from Tree-sitter adapter exploration after metadata field names are agreed. Documentation updates should wait until command output and metadata names settle.

**Known implementation risks:**
- Tree-sitter package availability may differ locally; tests must include unavailable behavior and make available behavior conditional or adapter-stubbed.
- FTS support may not exist in every SQLite build; search must have a deterministic non-FTS fallback.
- Refactoring graph build layers can destabilize existing Java semantic behavior; keep Java changes minimal in MVP.
- Jira and Confluence mega-repo scenarios cannot be committed publicly; the harness must support private local scenario files and make synthetic scale tests the public regression layer.
