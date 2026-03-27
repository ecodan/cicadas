# Cicadas 
**Version 0.6.1**

**Sustainable, Spec-Driven Development (SDD) for human-AI teams.**

Cicadas reverses the traditional relationship between code and documentation. Instead of fighting to keep specifications in sync with code, **Cicadas treats forward-looking docs (PRDs, plans) as disposable inputs** that drive implementation and then expire. Authoritative system documentation is then **reverse-engineered from the code itself** into canonical snapshots.

---

## The Core Concept

1.  **Active Specs are Disposable**: PRDs, designs, and task lists drive implementation but expire when the initiative completes.
2.  **Code is Truth**: The codebase is the only source of truth.
3.  **Work is Coordinated**: Parallel initiatives and features are registered in a registry, allowing parallel work efforts to minimize overlap and clashes.
4.  **Canon is Synthesized**: Authoritative documentation (`canon/`) is generated from the code + the intent of expired specs. It is never manually maintained.
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

# Cursor
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent cursor

# Rovodev
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent rovodev

# Multiple agents
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent claude-code,cursor
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
| `none` | Skip; configure manually |

**Requirements:** Python 3.11+, `curl`, `unzip`, `git`

---

## The Workflow

### Phase 1: Emergence (Drafting)
When you start an initiative, tweak, bug, or skill, the agent runs a **standard start flow** first (name → draft folder → **Building on AI?** (yes/no; if yes, eval status) → requirements source/pace for initiatives → publish destination for skills → PR preference), then drafts specs. For work that builds on AI, the agent may later offer an **eval spec** (initiatives) or an **eval/benchmark reminder** (tweaks/bugs); Cicadas does not run evals. We draft specifications in `.cicadas/drafts/` using specialized instruction modules (Clarify, UX, Tech, Approach, Tasks, Skill Create). **Clarify** can be driven by Q&A, a requirements doc (`drafts/{initiative}/requirements.md`), or a Loom transcript (`drafts/{initiative}/loom.md`).
*   **Key Artifact**: `approach.md` defines the partitions (feature branches).

### Phase 2: Kickoff
We promote drafts to **Active Specs** and register the initiative.
*   **Command**: `python src/cicadas/scripts/kickoff.py {name} --intent "..."`
*   **Result**: Creates `initiative/{name}` branch and `.cicadas/active/{name}/`. A linked git worktree is created at `../{repo}-initiative-{name}` so the main worktree stays on its current branch — multiple workstreams can run in parallel.

### Phase 3: Execution (The Dual Loop)
Work happens in **Feature Branches** (registered) and **Task Branches** (ephemeral).

*   **Start Feature**: `python src/cicadas/scripts/branch.py {feature} --intent "..."`
*   **Reflect**: When code implementation diverges from the plan, we update the active specs *immediately* (and before every commit on feat/task branches).
*   **Code Review** (optional): After Reflect; before committing on feature branches; before opening a PR or merging. The agent evaluates the diff against specs, security, correctness, and quality — producing a structured `review.md` artifact with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict. `open_pr.py` checks this verdict and blocks on `BLOCK`.
*   **Signal**: If a change affects other branches, we broadcast it: `python src/cicadas/scripts/signal.py "..."`

### Phase 4: Completion (Synthesis)
When all features are merged into the initiative branch, we merge to `main` and then:
1.  **Synthesize Canon**: An AI agent reads the code on `main` + the active specs and generates fresh documentation in `.cicadas/canon/` (including `canon/summary.md` — a 300–500 token snapshot used to inject context at branch start).
2.  **Archive**: Active specs are moved to `.cicadas/archive/`.
    - **1-PR Flow**: You can include the `archive` move and registry cleanup in your main PR for a single-commit finalization. If rework is needed, use `unarchive` to restore the state instantly.


### Quick Command Reference
All scripts are in `src/cicadas/scripts/`.

| Action | Command |
| :--- | :--- |
| **Kickoff Initiative** | `python src/cicadas/scripts/kickoff.py {name} --intent "..."` |
| **Start Feature** | `python src/cicadas/scripts/branch.py {name} --intent "..."` |
| **Check Status** | `python src/cicadas/scripts/status.py` (shows Merged/Next when lifecycle exists) |
| **Check Conflicts** | `python src/cicadas/scripts/check.py` |
| **Send Signal** | `python src/cicadas/scripts/signal.py "Message..."` |
| **Log Work** | `python src/cicadas/scripts/update_index.py --branch {name} ...` |
| **Lifecycle** | `python src/cicadas/scripts/create_lifecycle.py {name}` (PR boundaries + steps in drafts/active) |
| **Open PR** | `python src/cicadas/scripts/open_pr.py [--base branch]` (gh/glab/Bitbucket/fallback; blocks on BLOCK verdict) |
| **Check Review** | `python src/cicadas/scripts/review.py [--initiative name]` (read verdict from review.md) |
| **Archive** | `python src/cicadas/scripts/archive.py {name} [--type initiative]` (now snapshots metadata) |
| **Unarchive** | `python src/cicadas/scripts/unarchive.py {name}` |
| **Abort** | `python src/cicadas/scripts/abort.py` |
| **Project History** | `python src/cicadas/scripts/history.py` |
| **Validate Skill** | `python src/cicadas/scripts/validate_skill.py {slug}` |
| **Publish Skill** | `python src/cicadas/scripts/skill_publish.py {slug} [--publish-dir DIR] [--symlink] [--force]` |

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
    │   └── modules/            # Module-level snapshots
    ├── active/                 # Live specs for in-flight initiatives
    ├── drafts/                 # Staging area for new initiatives
    ├── archive/                # Expired specs (historical record)
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
