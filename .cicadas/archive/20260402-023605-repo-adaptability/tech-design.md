---
summary: "Evolve scan-repo into Bootstrap V3: build-first evidence gathering, scale-floor classification, strategy planning in repo.json, and orientation-plus-seeded-slices canon generation for larger repos."
phase: "tech"
when_to_load:
  - "When implementing or reviewing architecture, interfaces, data models, conventions, and sequencing."
  - "When checking whether changes still conform to the agreed technical approach."
depends_on:
  - "prd.md"
  - "ux.md"
modules:
  - "src/cicadas/emergence/bootstrap.md"
  - "src/cicadas/scripts/synthesize.py"
  - "src/cicadas/templates"
  - ".cicadas/canon"
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
next_section: "Builder review"
---

# Tech Design: Repo Adaptability

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

**Summary:** This initiative evolves Cicadas from a mostly uniform bootstrap flow into Bootstrap V3: a staged brownfield workflow that gathers structural evidence, prefers declared build/workspace structure over directory heuristics, enforces scale floors, chooses a canon strategy explicitly, generates minimal orientation plus seeded slices for larger repos, and validates the output before completion. The design keeps graph-backed routing out of scope for now, but preserves the seam for that follow-on work.

The architectural pattern is “evidence + classification + strategy plan + synthesis + validation.” `scan-repo` becomes the reusable engine for evidence gathering, structure detection, planning, and metadata refresh. `repo.json` becomes the durable machine-readable record for scale findings, detected build systems, candidate slices, chosen canon strategy, generation targets, deferred slices, and validation results. Synthesis then consumes that plan instead of improvising canon shape from a few heuristics.

### Cross-Cutting Concerns

1. **Durable evidence and planning** — Repo mode, build discovery, canon strategy, and validation results must live in stable file-backed metadata so later synthesis and maintenance can rely on them.
2. **Backward compatibility** — Existing flows that expect `product-overview.md`, `tech-overview.md`, and `canon/summary.md` must continue to work even as new artifact families appear.
3. **Human-versus-machine seam** — The design must not overfit prose canon to tasks that a future graph layer should answer mechanically.
4. **Build-first structure discovery** — Build/workspace/module definitions should win over directory-shape inference when present.
5. **Template-driven consistency** — New canon artifact families need templates and naming rules so different agents produce compatible outputs.
6. **Selective depth** — Large and mega repos must not force equal documentation depth across every subtree.
7. **Fast structural discovery** — Bootstrap needs a reusable, high-speed repo inventory for classification and navigation without repeated expensive crawls.

### Repo Classification And Strategy Heuristic

Classification should use explicit scale floors plus structural promotion. The final rule is conceptually:

`repo_mode = max(scale_class, topology_class)`

1. Gather evidence from a fast repo scan:
   - repo file count, meaningful file count, and estimated LoC
   - dominant languages and top-level fanout
   - detected build/workspace systems
   - declared modules/workspaces/subprojects
   - major code zones, test surfaces, and runtime/package surfaces
   - existing docs and easy-to-detect tool/runtime versions
2. Compute scale class floors:
   - `normal-repo` below `1K` meaningful files and below `100K` LoC
   - `large-repo` at `1K+` meaningful files or `100K+` LoC
   - `mega-repo` at `25K+` meaningful files or `2M+` LoC
3. Compute topology/routing promotion signals:
   - build-defined module count
   - number of major code zones
   - test/runtime/package surface count
   - language/build-system diversity
   - routing complexity for brownfield work
4. Build-defined structure wins when present:
   - Maven/Gradle/Bazel definitions outrank folder-name guesses for Java repos
   - npm/pnpm/yarn workspace declarations outrank simple package-folder inference
   - Python and Rust workspace/build declarations should shape routing and strategy when available
5. Choose canon strategy from the resulting mode:
   - `normal-repo` defaults to flat canon with top-level orientation plus module snapshots
   - `large-repo` defaults to locality-first canon with top-level orientation plus a few seeded slice packs
   - `mega-repo` also defaults to locality-first canon, but with stronger slice boundaries and more careful neighboring-slice guidance
6. Record classifier uncertainty, candidate slices, deferred slices, and strategy rationale in `repo.json` rather than pretending certainty.

### Brownfield Notes

This touches the existing bootstrap guidance in [bootstrap.md](/Users/dcripe/dev/code/thirdparty/cicadas/src/cicadas/emergence/bootstrap.md), scan and classification plumbing in [scan_repo.py](/Users/dcripe/dev/code/thirdparty/cicadas/src/cicadas/scripts/scan_repo.py), synthesis plumbing in [synthesize.py](/Users/dcripe/dev/code/thirdparty/cicadas/src/cicadas/scripts/synthesize.py), canon templates under [templates](/Users/dcripe/dev/code/thirdparty/cicadas/src/cicadas/templates), and downstream documentation/canon conventions. It must preserve the compact-context contract around `canon/summary.md`, keep top-level canon docs stable, and avoid breaking current repos while richer strategy-driven canon is added.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Matches the existing Cicadas runtime and script ecosystem. |
| **Framework** | None | Cicadas remains a script-and-markdown orchestrator, not a service. |
| **Database** | None for MVP | Repo classification and canon planning stay file-backed; graph storage is follow-on work. |
| **ORM / Query** | None | No database introduced in this initiative. |
| **Auth** | None | Local filesystem workflow only. |
| **Testing** | `pytest` + `unittest` style real filesystem/git tests | Matches the repo’s current testing bias. |
| **Key Libraries** | Standard library, optional `PyYAML` already used elsewhere | Avoids new infrastructure dependencies for MVP while still supporting concurrent scan workers via `concurrent.futures`. |

**New dependencies introduced:**
- None for MVP. The design intentionally avoids adding a DB or graph library before the follow-on project exists.

**Dependencies explicitly rejected:**
- `networkx` or graph DB clients — rejected for MVP because the PRD makes graph-backed navigation a dependent follow-on, not a core assumption.
- New persistence layers such as SQLite/Postgres for canon planning — rejected because file-backed artifacts are sufficient for classification, review, and synthesis planning at this stage.

---

## Project / Module Structure

```text
/Users/dcripe/dev/code/thirdparty/cicadas/
├── src/cicadas/emergence/
│   ├── bootstrap.md                 # [MODIFIED] Add adaptive classification, canon-mode planning, and parking-lot guidance
│   └── tech-design.md               # [MODIFIED] Document new canon artifacts and data contracts
├── src/cicadas/scripts/
│   ├── scan_repo.py                 # [NEW] Fast multi-threaded repo crawler that writes reusable structure metadata
│   ├── synthesize.py                # [MODIFIED] Gather/apply canon artifact families beyond top-level docs and modules
│   ├── utils.py                     # [MODIFIED] Shared helpers for repo metadata loading, canon-plan loading, path enumeration, and validation
│   └── command_registry.py          # [MODIFIED] Register the new scan command
├── src/cicadas/templates/
│   ├── slice-summary.md             # [NEW] Template for seeded slice orientation
│   ├── slice-boundaries.md          # [NEW] Template for slice ownership/boundaries
│   ├── slice-architecture.md        # [NEW] Template for local implementation model
│   ├── slice-invariants.md          # [NEW] Template for local invariants
│   ├── slice-change-guide.md        # [NEW] Template for practical local change guidance
│   ├── canon-plan.json              # [NEW] Optional schema/example for artifact families by mode
│   ├── synthesis-prompt.md          # [MODIFIED] Teach synthesis to respect canon mode and new artifact families
│   └── canon-summary.md             # [MODIFIED] Add cues for compact orientation plus local slice loading
└── .cicadas/
    └── canon/
        ├── repo.json                # [NEW] Durable repo-scale, scan summary, and canon-plan metadata
        ├── repo-tree.jsonl          # [NEW] Streamable machine inventory for classification and tooling
        ├── repo-context.md          # [NEW] Token-efficient reload artifact derived from repo metadata and scan results
        ├── product-overview.md      # [UPDATED] Hand-edit encouraged for large/mega history and why
        ├── tech-overview.md         # [UPDATED] Hand-edit encouraged for large/mega rationale and constraints
        └── slices/                  # [NEW for large/mega] Seeded local canon packs
```

**Key structural decisions:**
- Keep the mode-selection metadata in `.cicadas/canon/` so synthesis and future maintenance can treat it as durable canon context rather than ephemeral draft state.
- Add new canon artifact families alongside existing top-level docs instead of replacing them, preserving backward compatibility.
- Centralize path enumeration and canon-plan logic in shared Python helpers rather than scattering artifact-family rules across scripts.

---

## Architecture Decisions (ADRs)

### ADR-1: Store adaptive canon metadata as a durable `repo.json`

**Decision:** Introduce `.cicadas/canon/repo.json` as the canonical metadata artifact for repo mode, supporting evidence, selected canon layers, depth classifications, scan summaries, and graph-follow-on status.

**Rationale:** The PRD requires classification evidence to survive beyond a single bootstrap run. Putting it in canon, rather than drafts or a script-local cache, makes it available to synthesis, maintainers, and future initiatives. A JSON artifact is easy for scripts to validate and update without inventing a heavier persistence layer.

**Affects:** Bootstrap guidance, synthesis helpers, validation tests, future branch-context routing helpers.

---

### ADR-2: Keep top-level orientation docs and add seeded slices for larger repos

**Decision:** Preserve `product-overview.md`, `tech-overview.md`, and `canon/summary.md` for all modes, and add `slices/{slice-name}/` as the primary operational canon family for `large-repo` and `mega-repo`.

**Rationale:** Existing Cicadas flows and human expectations already rely on the top-level canon docs. Keeping them stable while moving local working canon into slices minimizes breakage, preserves human-readable history and "why," and better matches how brownfield work actually starts.

**Affects:** Templates, synthesis prompt, `synthesize.py`, branch context guidance, documentation.

---

### ADR-3: Treat canon planning as a first-class intermediate contract

**Decision:** Represent the chosen canon shape as an explicit plan with required artifact families, optional artifact families, and depth annotations, rather than inferring everything ad hoc from the selected mode.

**Rationale:** A plan contract gives bootstrap, synthesis, and future validators a shared vocabulary. It also supports selective depth and ambiguous cases better than a single enum alone.

**Affects:** `repo.json`, helper functions in `utils.py`, bootstrap instructions, tests, and future validation tooling.

---

### ADR-4: Add a fast repo scan as reusable infrastructure, not full graph infrastructure

**Decision:** Add a multi-threaded `scan-repo` CLI utility that walks the repo, records file-tree structure, sizes, kinds, dominant types, and cheap summaries, and writes `.cicadas/canon/repo-tree.jsonl` plus summary fields in `repo.json` and a compact `.cicadas/canon/repo-context.md`.

**Rationale:** Adaptive classification needs better raw evidence than prose discovery alone, and future navigation benefits from a durable structural inventory. A fast scan is much cheaper and lower-risk than full graph extraction, while still providing meaningful input to bootstrap, synthesis, and human review.

**Affects:** `scan_repo.py`, command registry, bootstrap workflow, `repo.json`, future navigation helpers.

---

### ADR-5: Keep graph-backed routing outside MVP and design only the seam

**Decision:** Do not add graph storage, graph extraction, or graph query interfaces in this initiative. Instead, annotate `repo.json` and canon guidance so a future graph layer can own mechanically derivable navigation without invalidating the document model.

**Rationale:** The PRD explicitly makes graph-backed machine navigation dependent follow-on work. Designing only the seam keeps MVP smaller and prevents canon from ossifying around speculative graph infrastructure.

**Affects:** PRD-aligned scope, bootstrap wording, canon artifact content rules, follow-on architecture handoff.

---

### ADR-6: Prefer slice-oriented canon over proliferating module snapshots in large and mega repos

**Decision:** In `large-repo` and `mega-repo` modes, treat seeded slice packs as the primary operational docs and make `modules/*.md` optional or selective.

**Rationale:** The problem statement is about safe routing and operational ownership, not documenting every leaf module uniformly. Slice packs better match the Builder and agent journeys for large repos, while module snapshots remain useful where a subsystem is already a strong local reasoning unit.

**Affects:** Bootstrap guidance, synthesis prompt, template set, branch-start context guidance.

---

## Data Models

### New Models

```json
{
  "schema_version": 1,
  "scan_version": 1,
  "repo_mode": "large-repo",
  "scan": {
    "tree_path": "repo-tree.jsonl",
    "context_path": "repo-context.md",
    "top_level_entries": 18,
    "dominant_languages": ["python", "markdown", "shell"],
    "build_paths": ["install.sh", "src/cicadas/scripts/"],
    "test_paths": ["tests/"],
    "runtime_paths": ["src/cicadas/"],
    "ownership_zone_candidates": ["src/cicadas/emergence", "src/cicadas/scripts", "src/cicadas/templates"]
  },
  "classification": {
    "decision": "large-repo",
    "confidence": "medium",
    "heuristic_scores": {
      "subsystem_breadth": 3,
      "layer_diversity": 4,
      "ownership_zone_count": 3,
      "path_diversity": 3,
      "routing_difficulty": 4
    },
    "evidence": [
      {
        "signal": "multiple_architectural_layers",
        "observation": "UI, service, packaging, and plugin layers all shape brownfield changes",
        "weight": "high"
      }
    ],
    "ambiguous_with": ["mega-repo"],
    "decision_note": "Routing matters, but a few strong local slices should cover common work better than a broad parallel hierarchy."
  },
  "canon_plan": {
    "orientation": ["product-overview.md", "tech-overview.md", "summary.md"],
    "slice_dirs": ["slices/"],
    "seeded_slice_count": 3,
    "minimum_slice_files": ["summary.md", "boundaries.md", "architecture.md", "invariants.md", "change-guide.md"],
    "module_snapshots": "minimal"
  },
  "slice_strategy": {
    "unit": "slice",
    "bootstrap_mode": "seeded-lazy",
    "path_policy": "contiguous-by-default",
    "allow_multi_path_when": "Only when repeated real work shows strong co-change across paths.",
    "deepen_on": ["initiative-start", "tweak-start", "bug-start"]
  },
  "candidate_slices": [
    {"name": "bootstrap", "paths": ["src/cicadas/emergence"], "status": "seeded"},
    {"name": "scripts", "paths": ["src/cicadas/scripts"], "status": "seeded"},
    {"name": "templates", "paths": ["src/cicadas/templates"], "status": "deferred"}
  ],
  "depth_policy": {
    "seeded": ["bootstrap", "scripts"],
    "deferred": ["templates"]
  },
  "graph_follow_on": {
    "status": "not_available",
    "parking_lot_topics": [
      "dependency adjacency traversal",
      "blast-radius queries",
      "inside-out symbol routing"
    ]
  }
}
```

**Key field decisions:**
- `scan` — provides a compact summary of the evidence-gathering pass and points to the durable inventory and context artifacts.
- `repo_mode` — explicit top-level field so downstream readers do not have to inspect nested decision data.
- `classification.scale_class` and `classification.topology_class` — make it obvious how the final mode was chosen.
- `classification.evidence` — structured as signal/observation pairs so scripts and humans can both inspect why a mode was chosen.
- `build_systems` and `declared_modules` — capture build-first structure directly rather than burying it inside weak path heuristics.
- `canon_plan` — records chosen strategy, targets, seeded slices, and validation steps so generation is plan-driven.
- `slice_strategy` and `candidate_slices` — encode the canon unit for larger repos, the lazy-deepening policy, and the initial set of slices bootstrap should seed.
- `validation` — stores best-effort QA results and any autocorrections performed.
- `graph_follow_on` — records the seam and parking-lot status without pretending graph functionality exists.

```jsonl
{"path":"src/cicadas/scripts","kind":"directory","children_count":22,"total_bytes":183245,"dominant_types":["py"],"summary":"Script layer for lifecycle orchestration and canon tooling"}
{"path":"src/cicadas/scripts/synthesize.py","kind":"file","bytes":3894,"extension":".py","language":"python","summary":"Gathers canon, specs, and code context into a synthesis prompt and can apply generated canon files"}
```

`repo-tree.jsonl` is intentionally structural, cheap, streamable, and non-graph. It should capture enough for fast classification and navigation handoffs without pretending to model semantic dependencies yet.

```markdown
# Repo Context

- Repo mode candidate: `large-repo`
- Dominant languages: `python`, `markdown`, `shell`
- Highest-signal areas:
  - `src/cicadas/emergence` — spec-authoring and bootstrap workflow guidance
  - `src/cicadas/scripts` — CLI orchestration and synthesis plumbing
  - `src/cicadas/templates` — canon/spec templates and synthesis prompt contract
- Build/test/runtime paths:
  - Build: `install.sh`, `src/cicadas/scripts/`
  - Test: `tests/`
  - Runtime: `src/cicadas/`
- Routing note: Start in `src/cicadas/scripts` for execution behavior changes, `src/cicadas/emergence` for workflow/design changes, and `src/cicadas/templates` for canon artifact contract changes.
```

`repo-context.md` is the token-efficient reload artifact. Agents should prefer it over raw inventory data unless they need finer-grained structural details.

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `canon/` artifact set | Add `repo.json`, `repo-tree.jsonl`, `repo-context.md`, and for larger repos `slices/` | No code migration; docs/template generation change only |
| Synthesis response format | Expand accepted `File: canon/...` blocks to include `slices/{slice-name}/*.md` and new top-level canon files | No stored data migration; parser update only |
| Bootstrap mental model | Move from fixed module-oriented outputs to mode-aware canon plans | No data migration; documentation and workflow update |

### Schema / Migration Notes

The migration path is additive. Existing repos without `repo.json` should be treated as legacy-uniform canon until the next bootstrap or synthesis refresh creates one. Script helpers should tolerate missing adaptive artifacts and fall back to the current top-level-doc-plus-modules behavior.

---

## API & Interface Design

### New Endpoints / Commands

This initiative should evolve the explicit user-facing `scan-repo` helper command into the Bootstrap V3 engine for evidence gathering, planning, and metadata refresh:

```text
python src/cicadas/scripts/cicadas.py scan-repo [--root PATH] [--output PATH] [--summary-depth N]
Behavior:
  - crawls the repo tree concurrently with streamed inventory output
  - computes meaningful file count, estimated LoC, language distribution, and top-level fanout
  - detects supported build/workspace systems for Java, Node/TS, Python, and Rust
  - records declared modules, major code zones, test surfaces, and runtime/package surfaces
  - chooses `scale_class`, `topology_class`, `repo_mode`, and canon strategy
  - writes `.cicadas/canon/repo-tree.jsonl`
  - updates `.cicadas/canon/repo.json` with evidence, plan, slice strategy, candidate slices, and validation metadata
  - writes `.cicadas/canon/repo-context.md` as the compact reload artifact
  - surfaces progress in phases with throughput/ETA during scanning
Errors:
  - inaccessible paths are skipped and reported
  - output write failures are fatal
```

Synthesis should also consume the new metadata:

```text
python src/cicadas/scripts/cicadas.py synthesize <name> --initiative
Behavior:
  - reads canon/repo.json when present
  - if canon/repo.json is missing, runs a lightweight scan/classification backfill before continuing
  - may read canon/repo-tree.jsonl when present
  - should prefer canon/repo-context.md for prompt-efficient reloads when present
  - generates canon from the explicit strategy plan in repo.json
  - falls back to legacy canon shape when absent
  - accepts and applies new canon artifact families, including seeded slice outputs
Errors:
  - missing repo.json is not fatal
  - invalid repo.json reports actionable schema errors
```

### Interface Contracts

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ClassificationEvidence:
    signal: str
    observation: str
    weight: str  # "low" | "medium" | "high"

@dataclass
class RepoScanSummary:
    meaningful_file_count: int
    estimated_loc: int
    dominant_languages: list[str]
    build_systems: list[str]
    major_code_zones: list[str]

@dataclass
class CanonPlan:
    repo_mode: str
    strategy: str
    required_files: list[str]
    optional_files: list[str]
    slice_dirs: list[str]
    module_dirs: list[str]
    module_snapshot_policy: str  # "full" | "selective" | "minimal"

def load_repo_metadata(canon_dir: Path) -> dict: ...
def load_repo_tree(canon_dir: Path) -> list[dict] | None: ...
def load_repo_context(canon_dir: Path) -> str | None: ...
def infer_repo_mode(repo_tree: list[dict] | None, repo_metadata: dict | None) -> tuple[str, list[ClassificationEvidence]]: ...
def build_canon_plan(repo_metadata: dict | None) -> CanonPlan: ...
def enumerate_canon_targets(plan: CanonPlan) -> list[str]: ...
```

The key contract is that synthesis should no longer hardcode only top-level docs plus `modules/`. Instead, a plan-driven enumerator should decide which canon files are gathered from existing canon and which output paths are valid targets during apply, including seeded `slices/{slice-name}/` layouts for larger repos.

### Backward Compatibility

Existing canon consumers remain supported:
- `canon/summary.md` stays present and remains the compact branch-start artifact.
- `product-overview.md` and `tech-overview.md` remain universal.
- `modules/*.md` remain valid existing artifacts even when not primary for large/mega repos.
- If adaptive artifacts are absent, current synthesis continues to behave as legacy mode.
- If `repo-tree.jsonl` is absent, classification can still proceed from slower discovery and `repo.json` can be populated incrementally later.
- If `repo-context.md` is absent, agents can still fall back to `canon/summary.md` plus targeted inventory reads.
- If `repo.json` is missing on an older repo, Cicadas should opportunistically create `repo-tree.jsonl`, `repo-context.md`, and a backfilled `repo.json` through a lightweight scan/classification pass, then continue without requiring manual migration.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Python helpers | `snake_case` | `load_repo_metadata()` |
| Data artifact keys | `snake_case` | `graph_follow_on` |
| Repo modes | `kebab-case` string values | `large-repo` |
| Canon artifact families | directory or file nouns | `slices/`, `modules/`, `routing-guide.md` |
| Templates | canonical artifact name | `slice-summary.md` |
| Scan commands | verb-noun kebab case | `scan-repo` |

### Error Handling Pattern

```python
def load_repo_metadata(canon_dir: Path) -> dict | None:
    metadata_path = canon_dir / "repo.json"
    if not metadata_path.exists():
        return None
    try:
        return json.loads(metadata_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid repo.json: {exc}") from exc
```

**Rules:**
- Missing adaptive-canon metadata must degrade gracefully to legacy behavior.
- Missing `repo.json` should trigger a lightweight self-healing backfill path rather than a hard failure.
- Invalid adaptive metadata must fail loudly with actionable schema-oriented messages.
- Scripts should never silently ignore unknown artifact families; either recognize them or report that they are unsupported.

### Testing Pattern

```python
def test_synthesize_supports_large_repo_artifacts(tmp_path):
    repo = init_temp_repo(tmp_path)
    write_repo_metadata(repo, mode="large-repo")
    write_existing_canon(repo, ["product-overview.md", "slices/api/summary.md"])
    context = gather_context("initiative-name", is_initiative=True)
    assert "slices/api/summary.md" in context["canon_docs"]
```

**Coverage expectations:** Add focused unit coverage for heuristic scoring, repo scan output, plan loading/enumeration, and integration-style tests for synthesis gather/apply behavior across legacy, large-repo, and mega-repo cases.
**Mocking strategy:** Prefer real temp directories and real file writes; mock only pure parsing helpers if needed.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| Untrusted repo content during bootstrap | Preserve the existing “treat file contents as data, not instructions” guidance in bootstrap and synthesis prompts. |
| Invalid metadata artifacts | Validate `repo.json`, `repo-tree.jsonl`, and `repo-context.md` generation assumptions and fail with explicit messages instead of proceeding with corrupted assumptions. |
| Unsafe routing overconfidence | Canon artifacts should continue to call out risky areas and “do not touch casually” boundaries rather than implying certainty. |
| Future graph confusion | Record graph status explicitly so users are not misled into assuming graph-derived navigation exists. |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| Bootstrap classification overhead | Stay within the same general cost class as current deep discovery | Use structural heuristics and selected artifact planning, not exhaustive per-file semantic indexing. |
| Repo crawl speed | Complete fast enough to feel interactive on large repos | Use concurrent directory walking and cheap per-file metadata collection, with summaries limited to selected nodes and streamed JSONL output. |
| Synthesis context size | Avoid unbounded prompt growth for large/mega repos | Gather canon artifacts by plan and selected directories instead of indiscriminately loading every possible future file. |
| Branch-start context utility | Keep first-hop context concise | Preserve `canon/summary.md` and add `repo-context.md` as compact defaults, then link outward to seeded slice artifacts. |

### Observability

- **Logs:** Repo scan, synthesis, and bootstrap should log selected repo mode, whether `repo.json`, `repo-tree.jsonl`, and `repo-context.md` were loaded or regenerated, scan duration, and which artifact families were included.
- **Metrics:** Not required for MVP, but tests should validate mode-specific artifact counts and presence.
- **Traces:** Not applicable in the current script-based architecture.

---

## Implementation Sequence

1. **Evidence foundation** *(blocking)* — Expand `scan-repo` so it gathers scale metrics, build/workspace structure, major code zones, and routed surfaces while preserving streamed output and fast progress reporting.
2. **Classification and strategy planning** *(depends on 1)* — Add explicit `scale_class`, `topology_class`, `repo_mode`, and canon strategy selection, then record generation/validation plans in `repo.json`.
3. **Synthesis plumbing** *(depends on 1-2)* — Extend `synthesize.py` so canon generation is driven by the recorded plan rather than ad hoc mode logic.
4. **Template and guidance layer** *(depends on 2)* — Update bootstrap guidance, prompts, and templates to explain Bootstrap V3 in clear human language and support seeded slice output.
5. **Validation and autocorrection** *(depends on 3-4)* — Validate generated canon against the selected plan and structural evidence, fixing cheap issues automatically when safe.
6. **Compatibility and docs** *(depends on 1-5)* — Preserve lazy backfill for older repos and update README/canon guidance so the evolved workflow is understandable.
7. **Testing** *(parallel with 2-6 once 1 exists)* — Add real-filesystem tests for build detection, scale floors, strategy planning, seeded-slice generation, best-effort validation, and legacy fallback.
8. **Polish** *(depends on 3-7)* — Refine explanations, completion summaries, and graph-follow-on parking-lot language.

Legacy upgrade behavior should be implemented through the evolved `scan-repo` path: when `repo.json` is absent, run the evidence/classification/strategy pass, write backfilled metadata plus `repo-tree.jsonl` and `repo-context.md`, and proceed with the resulting plan instead of blocking the workflow.

**Parallel work opportunities:** Once the evidence schema and planning contract are settled, synthesis changes and template/guidance updates can proceed in parallel. Tests can also be developed alongside scan and synthesis changes using temp repos.

**Known implementation risks:**
- Build-system detection could underfit real monorepos if supported patterns are too shallow, so the MVP must prioritize strong Java, Node/TS, Python, and Rust detection.
- If `repo.json` under-specifies scale class, topology class, or strategy rationale, agents may diverge in how they classify or plan artifacts.
- A naive repo scanner could become I/O-bound or generate noisy summaries, so JSONL output and context-summary generation must stay cheap and selective.
- There is a risk of making orientation docs and slice docs too similar unless template differences are made explicit.
