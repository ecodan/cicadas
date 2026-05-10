# Cicadas: The Definitive Guide (v2.1)

Welcome to the Cicadas methodology. This guide explains how to install Cicadas, initialize your project, and follow the Cicadas workflow for both new and existing codebases.

---

## 🚀 Installation & Setup

### 1. Install Cicadas

**One-liner** (requires Python 3.11+, `curl`, `unzip`, and a `git` repo):

```bash
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash
```

This will:
1. Check for Python 3.11+ (and print OS-specific guidance if missing)
2. Download and extract Cicadas into `.cicadas-skill/cicadas/` (configurable with `--dir`)
3. Initialize the `.cicadas/` workspace
4. Optionally set up your AI coding agent integration

**With agent integration** (skips interactive prompt):
```bash
# Claude Code
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent claude-code

# Cursor
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent cursor

# Rovodev
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --agent rovodev
```

**All flags:**
```
--dir <path>     Install location (default: .cicadas-skill/cicadas/)
--agent <list>   Agent integrations: claude-code, antigravity, cursor, rovodev, none (comma-separated)
--update         Re-download skill files only; never touches .cicadas/
```

**Supported agent integrations:**

| Agent | What gets created |
|-------|------------------|
| `claude-code` | `.claude/skills/cicadas` → symlink to install dir |
| `antigravity` | `.agents/skills/cicadas` → symlink to install dir |
| `cursor` | `.cursor/rules/cicadas.mdc` (copy of `SKILL.md`) |
| `rovodev` | `.rovodev/skills/cicadas` → symlink to install dir |

**Where implementation guardrails come from:** `CLAUDE.md` is used only by **Claude Code** (it lists commands, architecture, and points to `implementation.md` in the skill dir). **Cursor** and other environments do not use `CLAUDE.md`; they get lifecycle and implementation rules from the **skill file** (`SKILL.md` / `cicadas.mdc`) alone. The skill includes an "Implementation agent rules" section so the same guardrails apply in every environment.

### 2. Update Cicadas

To refresh the Cicadas skill files without touching your `.cicadas/` workspace:

```bash
bash install.sh --update
```

Or re-run the one-liner with `--update`:
```bash
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --update
```

---

## 🧠 Core Concepts & Hierarchy

### Branching Model

Cicadas uses a two-layer branching hierarchy to manage concurrent work and ensure documentation integrity:

1.  **Initiative Branch (`initiative/{name}`)**: A long-lived branch created at **Kickoff**. It serves as the integration point for all code in a release. No documentation is synthesized here.
2.  **Feature Branch (`feat/{name}`)**: A registered branch for a specific **Partition** (defined in the Approach). It forks from the Initiative branch and merges back when the partition is complete.
3.  **Task Branch (`task/{feat}/{name}`)**: (Optional) Ephemeral, unregistered branches for individual PRs into a feature branch.

### Terminology

| Term | Definition |
| :--- | :--- |
| **Canon** | Authoritative documentation reverse-engineered from code + rationale. Lives in `.cicadas/canon/`. |
| **Drafts** | Staging area for new requirements before work starts (`.cicadas/drafts/`). |
| **Active Specs** | The living requirements driving current work (`.cicadas/active/`). |
| **Approach** | The strategy doc where you define the **Initiative** and its **Partitions**. |
| **Reflect** | Keeping active specs in sync with code *during* development. |
| **Code Review** | Optional agent operation run after Reflect, before opening a PR or merging. Evaluates the diff against active specs, security patterns, correctness bugs, and code quality. Writes a structured `review.md` to `.cicadas/active/{initiative}/` with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict. `python src/cicadas/scripts/cicadas.py open-pr ...` reads this verdict and blocks on `BLOCK`. |
| **Signal** | Broadcasting breaking changes to other peer branches. |
| **Synthesis** | Updating Canon on `main` at the end of an initiative. Full for normal repos; targeted reconcile for large/mega repos. |
| **Lifecycle** | Per-initiative `lifecycle.json` (in drafts/active) defines PR boundaries (specs, initiatives, features, tasks) and an ordered step list. Created during Approach (for example, `python src/cicadas/scripts/cicadas.py create-lifecycle {name}`). |
| **Status (Merged/Next)** | When lifecycle exists, `python src/cicadas/scripts/cicadas.py status` reports which branches are merged and suggests the next step (git-based; no host API). |
| **Open PR** | `python src/cicadas/scripts/cicadas.py open-pr` opens a PR from the current branch (uses `gh` or `glab` if installed; else Bitbucket URL or fallback message). |

---

## 📁 Directory Structure (`.cicadas/`)

```text
.cicadas/
├── config.json        # Local configuration.
├── registry.json      # Global state of active initiatives and feature branches.
├── index.json         # Append-only history of all completed feature branches.
├── canon/             # Authoritative snapshots of the system.
├── drafts/            # Staging area for upcoming initiatives.
├── active/            # Living specs for in-flight work.
└── archive/           # Expired specs from completed initiatives.
```

---

## Starting any initiative, tweak, or bug

Whenever you ask to **start an initiative**, **start a tweak**, or **start a bug**, the agent runs a **standard start flow** first: name (confirmed even if you already said it) → create draft folder → **Building on AI?** (yes/no; if yes, eval status: already have / will do) → requirements source and pace (initiatives only) → PR preference → then collect requirements or draft the spec. This keeps the "start" experience repeatable. For work that builds on AI, the agent may later offer an **eval spec** (initiatives) or an **eval/benchmark reminder** in the tweaklet/buglet; Cicadas does not run evals. The flow is defined in the skill at `emergence/start-flow.md` and is embedded in the Clarify, Tweak, and Bug Fix instruction modules. A deprecated legacy skill-authoring path remains documented there for compatibility.

## Compact Context Contract

To keep long-running agent work from bloating context, the five core initiative specs now use a shared machine-readable front matter contract:

- `summary`: compact approved summary of the document
- `modules`: code areas most likely to be touched
- `depends_on`: upstream specs or artifacts this document relies on
- `index`: stable section labels pointing to the detailed headings inside the file

This lets the agent restart from approved file state instead of dragging full drafting conversations forward. Clarify refreshes this front matter as sections are approved, and Reflect refreshes it again when implementation changes the plan.

## Reset Boundaries

Cicadas now treats three moments as context-reset boundaries:

- `Branch Reset`: at branch start, reload `canon/summary.md`, the active spec front matter, and only the indexed sections needed for the current task
- `Phase Reset`: after each approved spec phase, treat the detailed drafting conversation as stale and carry forward only the approved file-backed summaries and indexed sections
- `Partition Reset`: when starting a partition, default to the current partition's approach/tasks sections and avoid loading unrelated partitions unless ambiguity forces it

If the host agent/runtime supports context clearing or compaction, the skill asks it to do that at these boundaries. If not, Cicadas still works because file-backed state remains authoritative.

---

## 🎓 Interactive Tutorial

Cicadas ships with an interactive 7-step walkthrough that shows the complete workflow using mock output — no real code required. It takes about 5 minutes.

### Running the tutorial

**On first `cicadas init`**: Cicadas detects that `.cicadas/` was just created and prompts:

```
Would you like to run the tutorial now? [Y/n]:
```

Type `Y` (or just press Enter) to start immediately.

**Any time after that**, tell your agent:

> 💬 *"Run the Cicadas tutorial"*

Or pass a flag directly to init:

```bash
# Run tutorial without the interactive prompt:
cicadas init --tutorial

# Skip the tutorial prompt entirely:
cicadas init --no-tutorial
```

### What the tutorial covers

The tutorial walks through all 7 steps of the Cicadas workflow with realistic mock CLI output at each step:

| Step | Title | 💬 Agent prompt shown |
| :--- | :--- | :--- |
| 1 | Start an initiative | *"Start an initiative called my-project"* |
| 2 | Define specs (agent-guided) | *(agent-guided — no prompt needed)* |
| 3 | Kickoff the initiative | *"Kickoff the initiative"* |
| 4 | Implement a partition | *"Implement partition 1"* |
| 5 | Code review and complete partition | *"Code review and complete partition"* |
| 6 | Create a PR | *"Create a PR"* |
| 7 | Complete the initiative | *"Complete the initiative"* |

At the end, the tutorial prints the full 7-prompt cheatsheet so you have it handy.

> **Note**: The tutorial is purely informational — it makes no changes to your git state or `.cicadas/` workspace.

---

## ⚙️ Hint Toggling

Cicadas prints contextual next-step hints after key lifecycle commands (kickoff, branch, archive, open-pr, status, etc.). Each hint shows the natural-language agent prompt to use next, formatted in a bordered box.

### Disabling hints globally

Add `"hints": false` to `.cicadas/config.json`:

```json
{
  "hints": false
}
```

Hints are shown by default (no key needed). To re-enable, set `"hints": true` or remove the key entirely.

### Disabling hints for a single command

Pass `--no-hints` to any lifecycle command:

```bash
python src/cicadas/scripts/cicadas.py kickoff my-project --intent "..." --no-hints
python src/cicadas/scripts/cicadas.py status --no-hints
```

### When hints are suppressed automatically

Hints are automatically suppressed when stdout is not a TTY (e.g., piped output, CI environments, script capture). This means CI logs stay clean without any extra configuration.

---

## 🟢 Greenfield: Starting a New Project

1.  **Initialize**: *"Initialize cicadas for this project."*
    - On first run, Cicadas offers the interactive tutorial. Type `Y` to run it.
2.  **Clarify**: *"I want to build [Product Name]. Help me clarify the requirements."* You can provide requirements via **Q&A** (interactive), a **doc** (`.cicadas/drafts/{initiative}/requirements.md`), or a **Loom transcript** (`.cicadas/drafts/{initiative}/loom.md`); the agent fills the PRD from the doc or transcript.
3.  **Draft Appearance**: Use prompts like *"Draft the UX"* and *"Draft the tech design"*.
4.  **Define Strategy (Approach)**: *"Draft the approach."*
    - **Note**: This is where you define the **Partitions** (future Feature Branches).
5.  **Draft Tasks**: *"Draft the tasks."*
6.  **Kickoff**: *"Kickoff [initiative-name]."*
    - Agent promotes drafts to active and creates the **Initiative Branch**.
    - By default work continues in the current workspace. To create a linked initiative worktree, enable it in `.cicadas/config.json` or use `--worktree`.
7.  **Implementation Loop**:
    - **Start Feature**: *"Implement partition [partition-name]."* (Forks from Initiative Branch).
      - Parallel `feat/` partitions still create linked worktrees by default.
      - Lightweight `fix/`, `tweak/`, and `skill/` branches now stay in the current workspace unless config or `--worktree` opts into a worktree.
    - **Reflect**: The Agent keeps specs current as you build, including refreshing spec front matter so compact context stays accurate.
    - **Code Review** (optional): *"Code review"* — the Agent evaluates the diff against specs, security, correctness, and code quality and writes `review.md` with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict.
    - **Complete Feature**: *"Code review and complete partition"* — merges back to the Initiative Branch.
8.  **Complete Initiative**: *"Complete the initiative."*
    - Merges Initiative Branch to `main`, updates Canon on `main`, and **Archives** the specs.
    - `normal-repo` initiatives run the traditional broad synthesis pass.
    - `large-repo` and `mega-repo` initiatives run targeted canon reconcile: touched slices first, neighboring slices only when the work changed interfaces, boundaries, or invariants, and global orientation docs only when repo-wide truth changed.

---

## 🔵 Bootstrap: Migrating a Legacy Project

If you are starting with an existing codebase that lacks Cicadas documentation, use the Bootstrap workflow to bring it into the methodology.

1.  **Initialize**: *"Initialize cicadas for this project."*
2.  **Bootstrap**: *"Bootstrap the baseline Canon."*
    - The Agent autonomously performs code discovery, classifies the repo, writes orientation docs, and seeds only the canon structure appropriate for that scale.
    - `normal-repo`: stays flat and module-oriented.
    - `large-repo` / `mega-repo`: writes `repo.json`, `repo-tree.jsonl`, `repo-context.md`, and a small set of lazy starter `slices/` packs meant to deepen on first real use rather than upfront.
3.  **Reference**: See the **Bootstrap** instruction module in `{cicadas root}/emergence/bootstrap.md` for a deep-dive on legacy migration.

---

## 🟠 Brownfield: New Features (Canon-Aware)

1.  **Read Canon**: The Agent uses existing `.cicadas/canon/` as context automatically.
2.  **Draft Delta**: *"I want to add [Feature X]."* (Agent authors specs aware of the existing system).
3.  **Standard Cycle**: Follow the Approach -> Kickoff -> Feature loop.
4.  **Update Canon**: Synthesis on `main` **updates** the existing Canon with the new reality.
    - `normal-repo`: broad/full canon refresh.
    - `large-repo` / `mega-repo`: targeted reconcile of touched slices, neighboring slices only when interfaces or boundaries changed, and top-level orientation only when durable repo-wide truth changed.

---

## 🧭 Optional Code Graph

Large and mega repos can opt into a local code graph to improve first-hop routing without changing the default Cicadas workflow:

```bash
python src/cicadas/scripts/cicadas.py graph build
```

The graph is optional. If `.cicadas/graph/` is absent, Cicadas continues to route from canon and targeted code reads.

When enabled, graph build now writes progressive artifacts while it runs:

- `codegraph.sqlite` — the staged/promoted SQLite graph
- `metadata.json` — build freshness, analyzer coverage, symbol counts, seeded areas
- `area-plan.json` — the deterministic routing areas selected for the repo
- `progress.json` and `progress-log.jsonl` — current progress snapshot plus append-only history
- `spool/` — streamed JSONL node/edge batches written during ingestion
- `tools/` — extractor-side artifacts such as Java semantic batch logs and manifests

Useful graph commands:

- `python src/cicadas/scripts/cicadas.py graph area <file-or-symbol>`
- `python src/cicadas/scripts/cicadas.py graph neighbors <file>`
- `python src/cicadas/scripts/cicadas.py graph callers <symbol> --exclude-tests`
- `python src/cicadas/scripts/cicadas.py graph signature-impact <symbol> --exclude-tests`
- `python src/cicadas/scripts/cicadas.py graph search <query> --kind file --exclude-tests`
- `python src/cicadas/scripts/cicadas.py graph tail`
- `python src/cicadas/scripts/cicadas.py graph watch`
- `python src/cicadas/scripts/cicadas.py graph usage --view table`

Coverage today:

- Python: semantic where available
- JavaScript/TypeScript: structural indexing for imports, exports, top-level symbols, and likely entrypoints
- Java: structural baseline plus semantic enrichment. Large repos may report `semantic` or `hybrid` Java coverage depending on how many semantic batches succeed locally.

The Java semantic harness now keeps successful work when a few files are problematic: failed batches are bisected recursively, poisonous files are quarantined, and the rest of the semantic output is retained.

---

## 🟡 Lightweight Paths (Fixes & Tweaks)

For trivial changes, Cicadas supports a "fast path" that reduces documentation overhead.

-   **Fix**: An isolated defect with no architectural impact.
-   **Tweak**: A small enhancement requiring < 100 lines of code.

**Workflow**:
1.  **Draft**: *"Draft the buglet"* or *"Draft the tweaklet"*.
2.  **Kickoff**: Promotes the single spec to active.
3.  **Branch**: Forks directly from `main`.
    - Default behavior is to keep work in the current workspace.
    - Pass `--worktree` or enable lightweight worktrees in `.cicadas/config.json` to opt into a linked worktree.
4.  **Complete**: Merge to `main`, optionally update Canon, and Archive.
    - **Note**: You can run `archive` and include the spec move in your PR to `main`. Use `unarchive` if you need to revert and make further changes.

**Aborting a Lightweight Path**: Say *"Abort"* at any point. The agent rolls back the branch and registry entry, and prompts whether to move the promoted spec back to drafts or delete it entirely.

---

## 🤖 Agents & Skills

- **Emergence Agent**: Authors specs (PRD, UX, Tech, Approach, Tasks).
- **Implementation Agent**: Focuses on `tasks.md` and writing code.
- **Synthesis Agent**: Operates on `main` to update the authoritative Canon.

### Authoring Agent Skills (Deprecated)

Cicadas no longer treats Agent Skill authoring as a first-class workflow. The
legacy docs and templates remain in the repo for compatibility, but new skill
work should use dedicated skill-authoring tooling instead.

**Legacy create flow**: `src/cicadas/emergence/skill-create.md`
The deprecated path still documents the old start flow (name, Building on AI?, publish destination, PR preference), then a dialogue-driven authoring session: 4 clarifying questions → complete `SKILL.md` + optional bundled `scripts/`, `references/`, or `assets/` → `eval_queries.json` draft → kickoff + branch (`skill/{name}`) + validate.

**Legacy edit flow**: `src/cicadas/emergence/skill-edit.md`
The deprecated path still documents the old edit loop: one diagnostic question (under-triggering / over-triggering / wrong output), a minimum targeted before/after diff, and validation after applying.

**Validate a skill**: *"Validate skill \<name\>"*

**Publish a skill** (after merging `skill/{name}` to `main`): *"Publish skill \<name\>"*
Reads `publish_dir` from `emergence-config.json`, runs validation before copying.

### Registering Cicadas as a Claude Code Skill

To use Cicadas as a native Claude Code skill (enabling auto-invocation and the `/cicadas` slash command), register it by symlinking the skill directory into `.claude/skills/`:

```bash
mkdir -p .claude/skills
ln -s ../../{cicadas-dir} .claude/skills/cicadas
```

Where `{cicadas-dir}` is the relative path from `.claude/skills/` to wherever you installed the Cicadas scripts (e.g., `../../.cicadas-skill/cicadas`).

Alternatively, copy or symlink the directory directly:

```bash
# If installed at the default location:
mkdir -p .claude/skills
ln -s ../../.cicadas-skill/cicadas .claude/skills/cicadas
```

Once registered, Claude Code will automatically load the skill and recognize Cicadas lifecycle commands like "kickoff", "start feature", and "check status".

> [!IMPORTANT]
> The **Code is the single source of truth**. Specs are active inputs that expire once implemented, while Canon is the permanent record synthesized from reality.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
