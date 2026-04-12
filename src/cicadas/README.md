# Cicadas Orchestrator

Cicadas is a sustainable **spec-driven development** methodology designed for high-velocity, high-quality engineering. It treats specifications as disposable inputs and the codebase as the single source of truth.

## The Cicadas Philosophy

1.  **Disposable Active Specs**: PRDs, Tech Designs, and Task lists are "active" only during development. Once code is merged, they expire.
2.  **Code is Truth**: Documentation is reverse-engineered (synthesized) from the code, not maintained manually in parallel.
3.  **Partitioned Work**: Complex initiatives are sliced into independent, registered feature branches to minimize conflicts.
4.  **Continuous Reflection**: "Reflect" operations keep specs in sync with code reality during the inner loop of development.

---

## Directory Architecture

The system is split between the **Skill** (logic) and the **Institutional Memory** (data).

### 0. The Installer (`install.sh` — project root)
A portable bash script for zero-friction setup. Run once to download Cicadas, check Python 3.11+, initialize `.cicadas/`, and optionally wire up agent integrations (`claude-code`, `antigravity`, `cursor`, `rovodev`).

```bash
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash
bash install.sh --update   # refresh skill files without touching .cicadas/
```

### 1. The Skill Directory (`src/cicadas/`)
This is the orchestrator itself. It contains:
- `SKILL.md`: The agent manual and technical definition (includes "Implementation agent rules" so the same guardrails apply in Cursor, Claude Code, and other envs).
- `implementation.md`: Guardrails for implementation agents (pause before commit, Reflect, tasks, Code Review on feat/).
- `scripts/`: The repo-local CLI entrypoint `cicadas.py`, its command registry, and the underlying deterministic tools for project lifecycle operations (kickoff, branch, status, create_lifecycle, open_pr, review, tokens, emit_event, get_events, validate_skill, skill_publish, unarchive, etc.). The optional code-graph subsystem also lives here: `graph.py` dispatches graph commands, `graph_build.py` and `graph_store.py` manage staged SQLite-backed graph artifacts under `.cicadas/graph/`, `graph_query.py` handles routed lookups, `graph_observe.py` renders progress/watch output, and `graph_usage.py` records local usage with end-to-end timing. Java graph extraction now uses a structural baseline plus resumable semantic enrichment batches, while JavaScript/TypeScript indexing is currently structural. `utils.py` includes `emit()` — a shared non-fatal event emitter (lazy-imports `emit_event`) used by kickoff, branch, archive, and open_pr.
- `emergence/`: Instruction modules for the drafting phase. Includes `start-flow.md` — the mandatory sequence (name, draft folder, **LLMs and Evals?** and eval status, requirements source/pace, publish destination for skills, PR preference) run first for initiative, tweak, bug, and skill. `skill-create.md` — dialogue-driven Agent Skill authoring (clarifying dialogue, SKILL.md generation, bundled files, `eval_queries.json` draft, kickoff + validate). `skill-edit.md` — one-question diagnostic, minimum-change proposal, validate. When work involves LLMs, `eval-spec.md` guides creation of an eval spec (initiatives only); Approach asks eval placement. Tweaks/bugs get an optional eval/benchmark reminder. Choices stored in `emergence-config.json`. Cicadas does not run evals. `clarify.md` now refreshes approved front matter fields rather than older `steps_completed` metadata.
- `templates/`: Standardized markdown templates for specs (including `eval-spec.md` for LLMs and Evals, `skill-SKILL.md` scaffold for Agent Skills), canon, and per-initiative lifecycle (`lifecycle-default.json`, `lifecycle-schema.md`). The five core initiative templates now share machine-readable front matter (`summary`, `modules`, `depends_on`, `index`) to support compact context reloads. `canon-summary.md` is the template for the 300–500 token agent-optimized codebase snapshot produced during synthesis and now includes an explicit branch-start routing cue. Large and mega repos also use slice canon templates (`slice-summary.md`, `slice-boundaries.md`, `slice-architecture.md`, `slice-invariants.md`, `slice-change-guide.md`) for seeded local canon packs. Routing templates now also mention the optional graph path so graph results and canon slices use the same area language.

### 2. The `.cicadas/` Directory
Located at your project root, this folder stores all project-specific state:
- `canon/`: The authoritative, synthesized documentation (Product, UX, and Tech overviews, plus adaptive repo metadata like `repo.json`, `repo-tree.jsonl`, `repo-context.md`, and seeded `slices/` packs for larger repos).
- `graph/`: Optional local graph artifacts. `codegraph.sqlite`, `metadata.json`, `area-plan.json`, `progress.json`, and `progress-log.jsonl` appear after `python src/cicadas/scripts/cicadas.py graph build`; `spool/` contains streamed node/edge JSONL, `tools/` contains extractor-side artifacts such as Java semantic batch manifests/logs, and `usage.jsonl` captures local graph usage/value events and end-to-end timings.
- `drafts/`: Staging area for new initiatives before they are officially "kicked off".
- `active/`: Live specs for work currently in progress.
- `archive/`: Evidence trail of expired specs from completed initiatives.
- `registry.json`: Global state tracking all active initiatives and branches.
- `index.json`: An append-only ledger of every significant change.

---

## The End-to-End Process

### 1. Emergence (Planning)
When starting an initiative, tweak, bug, or skill, the agent runs the **standard start flow** first (see `emergence/start-flow.md`): name, draft folder, **LLMs and Evals?** (yes/no; if yes, eval status for non-skills), then (for initiatives) requirements source and pace, then (for skills) publish destination, then PR preference. For work involving LLMs, the agent may later offer an eval spec (initiatives) or an eval/benchmark reminder (tweaks/bugs). Vague ideas are refined into structured drafts in `.cicadas/drafts/{initiative}/`.
- **Clarify**: Define the "What & Why" (PRD). At Clarify start, the Builder can choose **Q&A** (interactive), **Doc** (place a file at `drafts/{initiative}/requirements.md`), or **Loom** (save transcript to `drafts/{initiative}/loom.md`); the agent fills the PRD from the doc or transcript.
- **UX**: Map the interaction and UI.
- **Tech**: Design the architecture.
- **Approach**: Slice the work into logical partitions (Feature Branches).
- **Tasks**: Create a testable checklist.
- **Lifecycle** (optional): Run `python {cicadas-dir}/scripts/cicadas.py create-lifecycle ...` to add `lifecycle.json` with PR boundaries and steps; promoted to active at kickoff.

The skill now defines explicit `Branch Reset`, `Phase Reset`, and `Partition Reset` rules. These rules tell the agent to prefer approved file-backed state over prior conversation, reload front matter and indexed sections first, and opportunistically clear or compact conversational context when the host supports it.

### 2. Kickoff
Promote drafts to `active`, register the initiative, and create the `initiative/{name}` branch without switching the main worktree. By default Cicadas now continues in the current workspace; create a linked worktree only when `.cicadas/config.json` enables initiative worktrees or when kickoff is run with `--worktree`.

### 3. Execution (The Inner Loop)
- **Start Feature**: Create a registered feature branch for a partition.
- **Implement Task**: Work on ephemeral task branches.
- **Optional Code Graph**: When repo owners build `.cicadas/graph/`, agents can use graph queries to route from symptoms, failing tests, files, descriptions, and symbols without loading large swaths of the repo. `graph search`, `graph route`, `graph neighbors`, `graph callers`, `graph tests`, `graph signature-impact`, `graph tail`, `graph watch`, and `graph usage` now share the same local graph workspace. Builds stage SQLite rows progressively, emit UTC progress logs with ETA, and keep area planning inspectable through `area-plan.json`. When the graph is absent, Cicadas falls back to canon-first routing with no workflow penalty.
- **Reflect**: Periodically update active specs to match code changes, including refreshing front matter metadata so the compact context entrypoints stay authoritative.
- **Code Review** (optional): After Reflect, run *"Code review"* to evaluate the diff against specs, security, correctness, and quality. Writes `review.md` to `.cicadas/active/{initiative}/` with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict. `python {cicadas-dir}/scripts/cicadas.py open-pr ...` reads the verdict and blocks on `BLOCK`. Check verdict anytime via `python {cicadas-dir}/scripts/cicadas.py review ...`.
- **Signal**: Broadcast breaking changes to other active branches.

### 4. Completion & Synthesis
Merge back to `main`. The agent then updates Canon from the code and active specs (including `canon/summary.md` — a 300–500 token agent-optimized snapshot used for context injection at branch start), then archives the specs. `normal-repo` keeps the broad synthesis flow; `large-repo` and `mega-repo` use targeted reconcile over touched slices plus selective orientation refresh.

## Verification

`tests/test_templates.py` provides lightweight regression coverage for the context contract: it checks the shared front matter structure in the core templates, the branch-start cue in `canon-summary.md`, and the Clarify instructions that keep the new metadata current.

`tests/test_graph.py` covers the optional code graph CLI, including build/status behavior, routed queries, local observability output such as `usage.jsonl` entries and `graph usage` summaries, Java semantic batching, and staged graph persistence behavior. `tests/test_scan_repo.py` covers repo inventory, scale classification, slice seeding, and scan exclusion logic — including that local Cicadas workspaces (`.cicadas-skill/`), SDD installs at arbitrary paths (SKILL.md detection), known SDD tool state dirs (substring matching on root-level `./` and `_` dirs), and `scan_exclude_paths` config entries all stay out of file counts and routing signals.

---

## Operational Formulas

### Greenfield Formula (New Feature)
**Flow**: `Idea -> Clarify -> Tech -> Approach -> Tasks -> Kickoff`
> **Prompt**: "Initialize a new initiative for [IDEA]. Run the Emergence instruction modules to draft the PRD and Tech Design."

### Brownfield Formula (Legacy/Existing Code)
**Flow**: `Code -> Bootstrap -> Clarify -> Approach -> Tasks -> Kickoff`
> **Prompt**: "Bootstrap cicadas for this project. Reverse-engineer the current architecture into Canon, then draft an initiative to [CHANGE]."

---

## Builder Command Quick Reference

| Action | Builder Command |
| :--- | :--- |
| **Setup** | "Initialize cicadas" |
| **Start Initiative** | "Kickoff {initiative-name}" |
| **Start Work** | "Start feature {partition-name}" |
| **Do Coding** | "Implement task {X}" |
| **Code Review** | "Code review" / "Review feature" / "Review fix" / "Review tweak" |
| **Review** | "Check status" |
| **Broadcast** | "Signal: {your message}" |
| **Finish Feature** | "Complete feature {name}" |
| **Finish Initiative** | "Complete initiative {name}" |
| **Abort** | "Abort" |
| **Project History** | "Project history" or "Generate history" |
| **Create Skill** | "Create skill {name}" or "Build a skill for X" |
| **Edit Skill** | "Edit skill {name}" |
| **Validate Skill** | "Validate skill {name}" |
| **Publish Skill** | "Complete skill {name}" or "Publish skill {name}" |

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
