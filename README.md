# Cicadas 
**Version 0.8**

**Sustainable, Spec-Driven Development (SDD) for human-AI teams.**

Cicadas reverses the traditional relationship between code and documentation. Instead of fighting to keep specifications in sync with code, **Cicadas treats forward-looking docs (PRDs, plans) as disposable inputs** that drive implementation and then expire. Authoritative system documentation is then **reverse-engineered from the code itself** into canonical snapshots.

---

## The Core Concept

1.  **Active Specs are Disposable**: PRDs, designs, and task lists drive implementation but expire when the initiative completes.
2.  **Code is Truth**: The codebase is the only source of truth.
3.  **Work is Coordinated**: Parallel initiatives and features are registered in a registry, allowing parallel work efforts to minimize overlap and clashes.
4.  **Canon is Synthesized**: Authoritative documentation (`canon/`) is generated from the code + the intent of expired specs. It is never manually maintained, and larger repos use a more selective canon structure than smaller ones.
5.  **Reflect & Signal**: During development, we keep specs honest via **Reflect** (updating active specs to match code reality) and coordinate via **Signal** (broadcasting breaking changes to peer branches).

---

## Getting Started

### Installation

**One-liner** (requires Python 3.11+ and `git`):

```bash
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash
```

This downloads Cicadas into `.cicadas-skill/cicadas/`, initializes the `.cicadas/` workspace, and optionally sets up agent integrations.

**With agent integration:**
```bash
# Claude Code
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent claude-code

# Codex
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent codex

# Cursor
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent cursor

# Rovodev
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent rovodev

# Multiple agents
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent claude-code,codex
```

**Custom install directory:**
```bash
bash install.sh --dir tools/cicadas --agent claude-code
```

**Update Cicadas files** (preserves your `.cicadas/` workspace):
```bash
bash install.sh --update
```

**Supported agents:**

| Agent | Integration |
|-------|------------|
| `claude-code` | `.claude/skills/cicadas` symlink (uses project `CLAUDE.md` if present) |
| `antigravity` | `.agents/skills/cicadas` symlink |
| `cursor` | `.cursor/rules/cicadas.mdc` (copy of `SKILL.md`; guardrails are in the skill) |
| `rovodev` | `.rovodev/skills/cicadas` symlink |
| `codex` | `$CODEX_HOME/skills/cicadas` or `~/.codex/skills/cicadas` symlink (restart Codex after install) |
| `none` | Skip; configure manually |

**Codex note:** Unlike Claude Code's repo-local `.claude/skills/cicadas` integration, Codex installs Cicadas into your Codex skills directory and continues to use the repo's `.cicadas/` workspace per project. Restart Codex after installation so it picks up the new skill.

**Requirements:** Python 3.11+, `curl`, `unzip`, `git`

---

## The Workflow

### Phase 1: Emergence (Drafting)
When you start an initiative, tweak, bug, or skill, the agent runs a **standard start flow** first (name → draft folder → initiative profile for initiatives → **Building on AI?** (yes/no; if yes, eval status) → requirements source/pace for initiatives → publish destination for skills → PR preference), then drafts specs. Initiative profiles are `product`, `technical`, or `mixed`: product keeps the full PRD + UX path, technical uses a Technical Brief plus optional Operator Experience, and mixed chooses the appropriate artifact per surface. For work that builds on AI, the agent may later offer an **eval spec** (initiatives) or an **eval/benchmark reminder** (tweaks/bugs); Cicadas does not run evals. We draft specifications in `.cicadas/drafts/` using specialized instruction modules (Clarify, UX, Tech, Approach, Tasks, Skill Create). **Clarify** can be driven by Q&A, a requirements doc (`drafts/{initiative}/requirements.md`), or a Loom transcript (`drafts/{initiative}/loom.md`).
Every core initiative spec now carries compact machine-readable front matter (`summary`, `modules`, `depends_on`, `index`) so agents can reload approved state without re-reading entire drafting threads. The Technical Brief and Operator Experience templates use the same front matter contract.
*   **Key Artifact**: `approach.md` defines the partitions (feature branches).

### Phase 2: Kickoff
We promote drafts to **Active Specs** and register the initiative.
*   **Command**: `python src/cicadas/scripts/cicadas.py kickoff {name} --intent "..."`
*   **Result**: Creates `initiative/{name}` branch and `.cicadas/active/{name}/`. By default Cicadas continues in the current workspace; a linked git worktree is created only when `.cicadas/config.json` enables initiative worktrees or when kickoff is run with `--worktree`.

### Phase 3: Execution (The Dual Loop)
Work happens in **Feature Branches** (registered) and **Task Branches** (ephemeral).

*   **Start Feature**: `python src/cicadas/scripts/cicadas.py branch {feature} --intent "..."`
    - Parallel `feat/` partitions still auto-create linked worktrees by default.
    - Lightweight `fix/`, `tweak/`, and `skill/` branches now stay in the current workspace unless config or `--worktree` opts in.
*   **Experimental Code Graph**: Graph commands are disabled by default while large-repo efficacy work continues. Repo owners can opt in locally with `CICADAS_GRAPH_EXPERIMENTAL=1 python src/cicadas/scripts/cicadas.py graph build` or `.cicadas/config.json` key `graph_experimental_enabled: true`. Graph artifacts remain under `.cicadas/graph/`, but agents should use canon summaries, slice canon, routing guides, and targeted code reads as the default large-repo workflow.
*   **Reflect**: When code implementation diverges from the plan, we update the active specs *immediately* (and before every commit on feat/task branches).
    - Reflect refreshes the affected specs' front matter as well as their prose content so the compact routing metadata stays accurate.
*   **Code Review** (optional): After Reflect; before committing on feature branches; before opening a PR or merging. The agent evaluates the diff against specs, security, correctness, and quality — producing a structured `review.md` artifact with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict. `python src/cicadas/scripts/cicadas.py open-pr ...` checks this verdict and blocks on `BLOCK`.
*   **Signal**: If a change affects other branches, we broadcast it: `python src/cicadas/scripts/cicadas.py signal "..."`

### Phase 4: Completion (Synthesis)
When all features are merged into the initiative branch, we merge to `main` and then:
1.  **Synthesize Canon**: An AI agent reads the code on `main` + the active specs and generates fresh documentation in `.cicadas/canon/`. `canon/summary.md` remains the universal branch-start snapshot, while adaptive repo scans also maintain `repo.json`, `repo-tree.jsonl`, and `repo-context.md`. `normal-repo` projects keep the canon flat; `large-repo` and `mega-repo` projects seed lightweight `slices/` packs and reconcile only the touched canon at initiative completion.
    2.  **Archive**: Active specs are moved to `.cicadas/archive/`.
    - **1-PR Flow**: You can include the `archive` move and registry cleanup in your main PR for a single-commit finalization. If rework is needed, use `unarchive` to restore the state instantly.

### Context Reset Discipline

Cicadas treats branch starts, approved spec boundaries, and partition handoffs as **reset points**. The skill now tells the agent to:

- Prefer approved file-backed state over prior chat history.
- Reload from `canon/summary.md`, then `canon/repo-context.md` when present, plus spec front matter and indexed sections first.
- Opportunistically clear or compact conversational context when the host supports it, without relying on that behavior for correctness.


### Quick Command Reference
All scripts are in `src/cicadas/scripts/`.

| Action | Command |
| :--- | :--- |
| **Kickoff Initiative** | `python src/cicadas/scripts/cicadas.py kickoff {name} --intent "..."` |
| **Kickoff Initiative in worktree** | `python src/cicadas/scripts/cicadas.py kickoff {name} --intent "..." --worktree` |
| **Start Feature** | `python src/cicadas/scripts/cicadas.py branch {name} --intent "..."` |
| **Start Branch in worktree** | `python src/cicadas/scripts/cicadas.py branch {name} --intent "..." --worktree` |
| **Check Status** | `python src/cicadas/scripts/cicadas.py status` (shows Merged/Next when lifecycle exists) |
| **Check Conflicts** | `python src/cicadas/scripts/cicadas.py check` |
| **Send Signal** | `python src/cicadas/scripts/cicadas.py signal "Message..."` |
| **Log Work** | `python src/cicadas/scripts/cicadas.py update-index --branch {name} ...` |
| **Lifecycle** | `python src/cicadas/scripts/cicadas.py create-lifecycle {name}` (PR boundaries + steps in drafts/active) |
| **Open PR** | `python src/cicadas/scripts/cicadas.py open-pr [--base branch]` (gh/glab/Bitbucket/fallback; blocks on BLOCK verdict) |
| **Check Review** | `python src/cicadas/scripts/cicadas.py review [--initiative name]` (read verdict from review.md) |
| **Archive** | `python src/cicadas/scripts/cicadas.py archive {name} [--type initiative]` (now snapshots metadata) |
| **Unarchive** | `python src/cicadas/scripts/cicadas.py unarchive {name}` |
| **Abort** | `python src/cicadas/scripts/cicadas.py abort` |
| **Project History** | `python src/cicadas/scripts/cicadas.py history` |
| **Graph Build** | `CICADAS_GRAPH_EXPERIMENTAL=1 python src/cicadas/scripts/cicadas.py graph build` |
| **Graph Status** | `python src/cicadas/scripts/cicadas.py graph status` |
| **Graph Query** | `CICADAS_GRAPH_EXPERIMENTAL=1 python src/cicadas/scripts/cicadas.py graph area|neighbors|tests|callers|callees|signature-impact|route|search ...` |
| **Graph Observe** | `CICADAS_GRAPH_EXPERIMENTAL=1 python src/cicadas/scripts/cicadas.py graph tail|watch` |
| **Graph Usage** | `CICADAS_GRAPH_EXPERIMENTAL=1 python src/cicadas/scripts/cicadas.py graph usage [--initiative name] [--since ISO8601] [--view table|json|html]` |
| **Validate Skill** | `python src/cicadas/scripts/cicadas.py validate-skill {slug}` |
| **Publish Skill** | `python src/cicadas/scripts/cicadas.py skill-publish {slug} [--publish-dir DIR] [--symlink] [--force]` |

---

## Project Structure

The **Cicadas** toolset manages the `.cicadas/` directory:

```text
.
├── src/
│   └── cicadas/                # The Cicadas orchestrator (scripts & agents)
└── .cicadas/
    ├── canon/                  # Authoritative, generated checks
    │   ├── product-overview.md
    │   ├── tech-overview.md
    │   ├── summary.md
    │   ├── repo.json           # Adaptive repo metadata when scan/classification is enabled
    │   ├── repo-tree.jsonl     # Streamable machine inventory for deeper structural inspection
    │   ├── repo-context.md     # Compact routing/reload artifact for agents
    │   ├── modules/            # Module-level snapshots for regular repos when needed
    │   └── slices/             # Seeded canon slices for large/mega repos
    ├── active/                 # Live specs for in-flight initiatives
    │   └── {name}/
    │       └── events.jsonl    # Append-only event log (lifecycle + agent events)
    ├── drafts/                 # Staging area for new initiatives
    ├── archive/                # Expired specs (historical record)
    ├── graph/                  # Optional local code graph artifacts + usage log
    │   ├── codegraph.sqlite
    │   ├── metadata.json       # Build freshness, coverage, symbol counts, seeded areas
    │   ├── area-plan.json      # Deterministic routing areas chosen for this repo/build
    │   ├── progress.json       # Current build snapshot with elapsed time and ETA
    │   ├── progress-log.jsonl  # Append-only build progress history
    │   ├── spool/              # Streamed JSONL nodes/edges written during build
    │   └── tools/              # Extractor artifacts such as Java semantic batch logs
    └── registry.json           # Active initiatives & branch registry
```

### Additional Resources

For the full methodology specification, see:

📘 **[Cicadas Method Specification](docs/cicadas-method-general.md)**

For a comparison of the Cicadas Method to other approaches, see:

📘 **[SDD Comparison](docs/sdd-comparison.md)**


---





## License

Cicadas is licensed under the [Apache License 2.0](LICENSE).
Copyright 2026 Cicadas Contributors

This product includes software developed by Dan and contributors.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
