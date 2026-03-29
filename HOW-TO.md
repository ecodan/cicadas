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
| **Synthesis** | Overwriting Canon on `main` at the end of an initiative. |
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

## Starting any initiative, tweak, bug, or skill

Whenever you ask to **start an initiative**, **start a tweak**, **start a bug**, or **create a skill**, the agent runs a **standard start flow** first: name (confirmed even if you already said it) → create draft folder → **Building on AI?** (yes/no; if yes, eval status: already have / will do — skipped for skills) → requirements source and pace (initiatives only) → publish destination (skills only) → PR preference → then collect requirements or draft the spec. This keeps the "start" experience repeatable. For work that builds on AI, the agent may later offer an **eval spec** (initiatives) or an **eval/benchmark reminder** in the tweaklet/buglet; Cicadas does not run evals. The flow is defined in the skill at `emergence/start-flow.md` and is embedded in the Clarify, Tweak, Bug Fix, and Skill Create instruction modules.

---

## 🟢 Greenfield: Starting a New Project

1.  **Initialize**: *"Initialize cicadas for this project."*
2.  **Clarify**: *"I want to build [Product Name]. Help me clarify the requirements."* You can provide requirements via **Q&A** (interactive), a **doc** (`.cicadas/drafts/{initiative}/requirements.md`), or a **Loom transcript** (`.cicadas/drafts/{initiative}/loom.md`); the agent fills the PRD from the doc or transcript.
3.  **Draft Appearance**: Use prompts like *"Draft the UX"* and *"Draft the tech design"*.
4.  **Define Strategy (Approach)**: *"Draft the approach."*
    - **Note**: This is where you define the **Partitions** (future Feature Branches).
5.  **Draft Tasks**: *"Draft the tasks."*
6.  **Kickoff**: *"Kickoff [initiative-name]."*
    - Agent promotes drafts to active and creates the **Initiative Branch**.
7.  **Implementation Loop**:
    - **Start Feature**: *"Start feature [partition-name]."* (Forks from Initiative Branch).
    - **Reflect**: The Agent keeps specs current as you build.
    - **Code Review** (optional): *"Code review"* — the Agent evaluates the diff against specs, security, correctness, and code quality and writes `review.md` with a `PASS` / `PASS WITH NOTES` / `BLOCK` verdict. `python src/cicadas/scripts/cicadas.py open-pr ...` blocks on `BLOCK`.
    - **Complete Feature**: Merges back to the Initiative Branch.
8.  **Complete Initiative**: *"Complete initiative [initiative-name]."*
    - Merges Initiative Branch to `main`, **Synthesizes** the Canon on `main`, and **Archives** the specs.

---

## 🔵 Bootstrap: Migrating a Legacy Project

If you are starting with an existing codebase that lacks Cicadas documentation, use the Bootstrap workflow to bring it into the methodology.

1.  **Initialize**: *"Initialize cicadas for this project."*
2.  **Bootstrap**: *"Bootstrap the baseline Canon."*
    - The Agent autonomously performs code discovery, synthesizes a full suite of docs (PRD, UX, Tech, Modules) using templates, and validates them against the code.
3.  **Reference**: See the **Bootstrap** instruction module in `{cicadas root}/emergence/bootstrap.md` for a deep-dive on legacy migration.

---

## 🟠 Brownfield: New Features (Canon-Aware)

1.  **Read Canon**: The Agent uses existing `.cicadas/canon/` as context automatically.
2.  **Draft Delta**: *"I want to add [Feature X]."* (Agent authors specs aware of the existing system).
3.  **Standard Cycle**: Follow the Approach -> Kickoff -> Feature loop.
4.  **Update Canon**: Synthesis on `main` **updates** the existing Canon with the new reality.

---

## 🟡 Lightweight Paths (Fixes & Tweaks)

For trivial changes, Cicadas supports a "fast path" that reduces documentation overhead.

-   **Fix**: An isolated defect with no architectural impact.
-   **Tweak**: A small enhancement requiring < 100 lines of code.

**Workflow**:
1.  **Draft**: *"Draft the buglet"* or *"Draft the tweaklet"*.
2.  **Kickoff**: Promotes the single spec to active.
3.  **Branch**: Forks directly from `main`.
4.  **Complete**: Merge to `main`, optionally update Canon, and Archive.
    - **Note**: You can run `archive` and include the spec move in your PR to `main`. Use `unarchive` if you need to revert and make further changes.

**Aborting a Lightweight Path**: Say *"Abort"* at any point. The agent runs `python src/cicadas/scripts/cicadas.py abort` from the current branch, rolls back the branch and registry entry, and prompts whether to move the promoted spec back to drafts or delete it entirely.

---

## 🤖 Agents & Skills

- **Emergence Agent**: Authors specs (PRD, UX, Tech, Approach, Tasks).
- **Implementation Agent**: Focuses on `tasks.md` and writing code.
- **Synthesis Agent**: Operates on `main` to update the authoritative Canon.

### Authoring Agent Skills

Cicadas manages the full lifecycle of **Agent Skills** — portable instruction modules you can ship alongside your project to teach agents new capabilities.

**Create a new skill**: *"Create a skill that handles our database migration runbook."*
The agent runs the start flow (name, Building on AI?, publish destination, PR preference), then a dialogue-driven authoring session: 4 clarifying questions → complete `SKILL.md` + optional bundled `scripts/`, `references/`, or `assets/` → `eval_queries.json` draft → kickoff + branch (`skill/{name}`) + validate.

**Edit an existing skill**: *"The skill isn't triggering reliably."* or *"Edit skill db-migrations."*
The agent asks one diagnostic question (under-triggering / over-triggering / wrong output), proposes a minimum targeted change as a before/after diff, and validates after applying.

**Validate a skill**: `python src/cicadas/scripts/cicadas.py validate-skill {slug}`

**Publish a skill** (after merging `skill/{name}` to `main`): `python src/cicadas/scripts/cicadas.py skill-publish {slug}`
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
