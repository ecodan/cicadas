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
- `scripts/`: The repo-local CLI entrypoint `cicadas.py`, its command registry, and the underlying deterministic tools for project lifecycle operations (kickoff, branch, status, create_lifecycle, open_pr, review, tokens, emit_event, get_events, validate_skill, skill_publish, unarchive, etc.). `utils.py` includes `emit()` — a shared non-fatal event emitter (lazy-imports `emit_event`) used by kickoff, branch, archive, and open_pr.
- `emergence/`: Instruction modules for the drafting phase. Includes `start-flow.md` — the mandatory sequence (name, draft folder, **LLMs and Evals?** and eval status, requirements source/pace, publish destination for skills, PR preference) run first for initiative, tweak, bug, and skill. `skill-create.md` — dialogue-driven Agent Skill authoring (clarifying dialogue, SKILL.md generation, bundled files, `eval_queries.json` draft, kickoff + validate). `skill-edit.md` — one-question diagnostic, minimum-change proposal, validate. When work involves LLMs, `eval-spec.md` guides creation of an eval spec (initiatives only); Approach asks eval placement. Tweaks/bugs get an optional eval/benchmark reminder. Choices stored in `emergence-config.json`. Cicadas does not run evals.
- `templates/`: Standardized markdown templates for specs (including `eval-spec.md` for LLMs and Evals, `skill-SKILL.md` scaffold for Agent Skills), canon, and per-initiative lifecycle (`lifecycle-default.json`, `lifecycle-schema.md`). `canon-summary.md` is the template for the 300–500 token agent-optimized codebase snapshot produced during synthesis.

### 2. The `.cicadas/` Directory
Located at your project root, this folder stores all project-specific state:
- `canon/`: The authoritative, synthesized documentation (Product, UX, and Tech overviews).
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

### 2. Kickoff
Promote drafts to `active`, register the initiative, and create the `initiative/{name}` branch without switching the main worktree. By default Cicadas now continues in the current workspace; create a linked worktree only when `.cicadas/config.json` enables initiative worktrees or when kickoff is run with `--worktree`.

### 3. Execution (The Inner Loop)
- **Start Feature**: Create a registered feature branch for a partition.
- **Implement Task**: Work on ephemeral task branches.
- **Reflect**: Periodically update active specs to match code changes.
- **Code Review** (optional): After Reflect, run *"Code review"* to evaluate the diff against specs, security, correctness, and quality. Writes `review.md` to `.cicadas/active/{initiative}/` with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict. `python {cicadas-dir}/scripts/cicadas.py open-pr ...` reads the verdict and blocks on `BLOCK`. Check verdict anytime via `python {cicadas-dir}/scripts/cicadas.py review ...`.
- **Signal**: Broadcast breaking changes to other active branches.

### 4. Completion & Synthesis
Merge back to `main`. The agent then **synthesizes** new Canon docs from the code and active specs (including `canon/summary.md` — a 300–500 token agent-optimized snapshot used for context injection at branch start), then archives the specs.

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
