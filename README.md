# Cicadas 
**Version 1.0.0**

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

This downloads Cicadas into `.cicadas-skill/cicadas/`, initializes the `.cicadas/` workspace, and optionally sets up agent integrations. Re-running initialization is idempotent: existing registry, index, config, and active state are preserved.

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
- or - 
```bash
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash -s -- --update
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

### Your First Time: Run the Tutorial

After installing, run the interactive tutorial to see the full Cicadas workflow in about 5 minutes:

> 💬 **Tell your agent:** *"Run the Cicadas tutorial"*

Or, if you initialized Cicadas yourself and skipped the prompt:

> 💬 **Tell your agent:** *"cicadas tutorial"*

The tutorial walks you through all 7 steps with mock output so you know exactly what to expect before touching real code.

---

## The Workflow

Cicadas is designed to be driven entirely through natural-language agent prompts — you rarely need to type a CLI command yourself. Here is the full 7-step flow.

### Step 1 — Start an initiative

Tell your agent what you want to build. Cicadas creates a draft folder and begins an agent-guided spec authoring session.

> 💬 **Tell your agent:** *"Start an initiative called \<name\>"*

The agent runs a brief start flow (confirms the name, sets up your PR preference) and then moves into spec drafting.

#### What type of initiative?

Not all work needs the full spec suite. Choose the path that matches the scope of the change:

| Type | When to use | Specs required | Prompt                                      |
| :--- | :--- | :--- |:--------------------------------------------|
| **Full Initiative** | A meaningful new feature, significant refactor, or cross-cutting change | Full suite: PRD → UX → Tech → Approach → Tasks | *"Start an initiative called \<name\>"*     |
| **Tech Initiative** | A technical change with no user-facing UX (e.g. infra, migration, performance) | PRD → Tech → Approach → Tasks (UX skipped) | *"Start a tech initiative called \<name\>"* |
| **Tweak** | A small improvement, < ~100 lines | Single compact tweaklet doc | *"Start a tweak called \<name\>"*           |
| **Bug** | An isolated defect fix | Single compact buglet doc | *"Start a bug fix called \<name\>"*         |

Tweaks and bugs bypass the full Emergence phase — the agent drafts a single lightweight doc and moves straight to implementation. They also fork directly from `main` rather than creating a dedicated initiative branch.

### Step 2 — Define specs (agent-guided)

Your agent guides you through five spec documents, one at a time — each approved before the next begins:

- **PRD** — What and why (problem, users, success criteria)
- **UX** — Experience and interaction flow
- **Tech Design** — Architecture, components, data flow
- **Approach** — Partitions (the feature branches you will implement)
- **Tasks** — Ordered, testable checklist grouped by partition

You review and approve each document. No raw CLI commands needed at this step — the agent handles everything.

### Step 3 — Kickoff the initiative

Once specs are approved, kickoff promotes them from drafts to active, registers the initiative, and creates the initiative branch.

> 💬 **Tell your agent:** *"Kickoff the initiative"*

### Step 4 — Implement a partition

Your agent implements one partition (feature branch) at a time: creates task branches, writes code, keeps specs current via Reflect, and marks tasks complete as it goes.

> 💬 **Tell your agent:** *"Implement partition \<name\>"*

Repeat for each partition defined in your Approach. Partitions that don't depend on each other can run in parallel.

### Step 5 — Code review and complete the partition

Before merging, the agent runs a structured code review against specs, security patterns, and code quality, then merges the partition into the initiative branch.

> 💬 **Tell your agent:** *"Code review and complete partition"*

Repeat Steps 4–5 for each partition.

### Step 6 — Create a PR

When all partitions are complete, the agent opens a pull request from the initiative branch to `main`.

> 💬 **Tell your agent:** *"Create a PR"*

Review and merge the PR in your usual code review tool.

### Step 7 — Complete the initiative

After the PR is merged, the agent synthesizes updated Canon documentation on `main` and archives the active specs.

> 💬 **Tell your agent:** *"Complete the initiative"*

---

### Context Reset Discipline

Cicadas treats branch starts, approved spec boundaries, and partition handoffs as **reset points**. The skill tells the agent to:

- Prefer approved file-backed state over prior chat history.
- Reload from `canon/summary.md`, then `canon/repo-context.md` when present, plus spec front matter and indexed sections first.
- Opportunistically clear or compact conversational context when the host supports it, without relying on that behavior for correctness.

---

### Quick Reference — 7 Agent Prompts

| Step | What happens | 💬 Tell your agent |
| :--- | :--- | :--- |
| **1 — Start** | Creates draft folder, runs start flow | *"Start an initiative called \<name\>"* |
| **2 — Spec** | Agent-guided PRD → UX → Tech → Approach → Tasks | *(agent-guided — no prompt needed)* |
| **3 — Kickoff** | Promotes specs, creates initiative branch | *"Kickoff the initiative"* |
| **4 — Build** | Implements partition on a feature branch | *"Implement partition \<name\>"* |
| **5 — Complete partition** | Code review + merge to initiative branch | *"Code review and complete partition"* |
| **6 — PR** | Opens pull request to `main` | *"Create a PR"* |
| **7 — Complete** | Synthesizes Canon, archives specs | *"Complete the initiative"* |

> **Tip**: run 💬 *"Check status"* at any time to see what Cicadas suggests as the next step.

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
    └── registry.json           # Active initiatives & branch registry
```

### Additional Resources

For the full practitioner reference (all commands, flags, brownfield/bootstrap flows, and advanced configuration), see:

📘 **[Cicadas User Guide](docs/cicadas-user-manual.md)**

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
