
# Cicadas Method (v0.5)

## A Methodology for Sustainable Spec-Driven Development

### Implementation Manual

---

## Part 1: Summary of the Approach

### The Problem

Traditional Spec-Driven Development (SDD) works well on the first pass but degrades over time:

1. **Documentation entropy**: Every code change must back-propagate to specs, creating exponential maintenance burden.
2. **Waterfall assumptions**: SDD assumes requirements are known before implementation, but real design is emergent.
3. **Single-threaded model**: SDD doesn't address concurrent work by multiple humans and AI agents.
4. **Stale context**: LLMs confidently generate from outdated specs, producing incorrect code.
5. **Spec drift during implementation**: As engineers discover reality, the specs they were given become stale, but there is no mechanism to keep them current during the inner loop of coding.

### The Cicadas Solution

**Why "Cicadas"?** Cicadas emerge in synchronized broods, do their work, leave their husks behind, and repeat on a cycle. This mirrors the methodology: active specs emerge to drive implementation, then expire (leave husks), while the living system continues. Multiple contributors work in synchronized parallel.

**Core principles:**

1. **Active Specs are disposable inputs** — PRDs, designs, and tasks expire after implementation.
2. **Code is the single source of truth** — always authoritative.
3. **Canon are reverse-engineered** — derived from code + expiring specs, not maintained in parallel.
4. **Work is partitioned** — large initiatives are sliced into independent feature branches via an explicit approach doc.
5. **Concurrent work via intent registry** — feature branch registration with both module-level and semantic intent conflict detection.
6. **Specs stay current during development** — a "Reflect" mechanism keeps active specs in sync with code as implementation progresses.
7. **Teams coordinate asynchronously** — a "Signal" mechanism broadcasts breaking changes to peer branches without blocking.

**Key innovation:** Instead of fighting to keep docs in sync with code, we let active specs expire and synthesize canon from what was actually built. The canon capture both the "what" (from code) and the "why" (from the expiring active specs). During development, the "Reflect" operation keeps specs honest, and "Signal" keeps teams informed.

### Terminology

| Concept | Term | Definition |
| :--- | :--- | :--- |
| **Coordination Unit** | **Initiative** | A set of related features with shared context (PRD, UX, Architecture). |
| **Drafting Area** | **Drafts** | Where specs are authored before work begins (`.cicadas/drafts/`). |
| **Live Requirements** | **Active Specs** | The living requirements driving current work (`.cicadas/active/`). Updated by Reflect during development. |
| **Generated Docs** | **Canon** | Authoritative canon, reverse-engineered from code on `main` (`.cicadas/canon/`). Smaller repos can stay flat; larger repos can use adaptive metadata and localized slice packs. |
| **Activation** | **Kickoff** | Promoting drafts to active status, registering the initiative, and creating the initiative branch. |
| **Outer Integration** | **Initiative Branch** | A long-lived git branch (`initiative/{name}`) that integrates all feature branches. Pure code — never touches canon. Merges to `main` once at initiative completion. |
| **Inner Integration** | **Feature Branch** | A registered git branch for a partition of the initiative. Forks from and merges back to the initiative branch. |
| **Lightweight Change** | **Fix / Tweak Branch** | A registered branch for a single issue/enhancement. Forks directly from main/master. |
| **Work Branch** | **Task Branch** | An ephemeral, private git branch for a single task. Unregistered. Merges to feature branch via PR. |
| **Change Ledger** | **Index** | Append-only history of all completed work (`.cicadas/index.json`). |
| **Expired Specs** | **Archive** | Completed active specs, preserved for archaeology (`.cicadas/archive/`).

### System Components

| Component | Purpose | Lifecycle |
|-----------|---------|-----------|
| Active Specs | Drive implementation (PRD, tasks, tokens, lifecycle) | Created at kickoff → updated by Reflect → archived at completion |
| Canon | Authoritative canon | Synthesized on `main` at initiative completion, never manually edited |
| Optional Graph | Local routing and impact index | Built on demand under `.cicadas/graph/`; safe to rebuild |
| Index | Lightweight change ledger | Append-only, one entry per feature branch |
| Registry | Track concurrent work-in-progress | Entries added/removed with initiatives and feature branches |
| Archive | Historical active specs | Append-only, one entry per initiative |

**Cicadas** is the orchestrator — a set of portable CLI scripts and agent instructions that manages the Cicadas lifecycle: initiative kickoff, branch registration, conflict detection, spec reflection, signaling, synthesis, merging, and queries.

---

## Part 2: Implementation Architecture

### Directory Structure

Cicadas logic resides in `src/cicadas/`, and it manages the `.cicadas/` folder in the project root:

```
project-root/
├── src/                              # Existing source code
├── src/cicadas/                      # Cicadas orchestrator
│   ├── SKILL.md                     # Agent skill definition (entry point)
│   ├── implementation.md            # Guardrails for agent implementation
│   ├── scripts/                     # Repo-local CLI + deterministic orchestration scripts
│   │   ├── cicadas.py               # Common entrypoint for agent-facing commands
│   │   ├── command_registry.py      # Subcommand registry and wrappers
│   │   ├── utils.py                 # Shared utilities (path resolution, JSON I/O)
│   │   ├── kickoff.py               # Promote drafts → active, register initiative
│   │   ├── branch.py                # Register a feature branch, check module overlaps
│   │   ├── graph_build.py           # Optional staged graph build
│   │   ├── graph_query.py           # Graph routing, impact, and search queries
│   │   ├── review.py                # Parses review.md verdict
│   │   ├── tokens.py                # Token usage log API
│   │   └── ...                      # Other deterministic lifecycle scripts
│   ├── templates/                   # Markdown templates
│   └── emergence/                   # Instruction modules for spec authoring
└── .cicadas/                         # Cicadas artifacts (managed by scripts)
    ├── config.json                   # Local configuration
    ├── registry.json                 # Global registry (initiatives + feature branches)
    ├── index.json                    # Change ledger (append-only)
    ├── canon/                        # Canon (authoritative, generated)
    │   ├── product-overview.md       # What the product does, goals, personas
    │   ├── ux-overview.md            # Design principles, patterns, flows
    │   ├── tech-overview.md          # Architecture, components, API, schema
    │   ├── summary.md                # Compact branch-start snapshot
    │   ├── repo.json                 # Repo scale + canon planning metadata when adaptive scan is used
    │   ├── repo-tree.jsonl           # Streamable structural inventory
    │   ├── repo-context.md           # Compact orientation and routing context
    │   ├── modules/                  # Module-level snapshots for regular repos when useful
    │   └── slices/                   # Localized canon packs for large/mega repos
    ├── drafts/                       # Pre-kickoff staging area
    │   └── {initiative-name}/
    │       ├── prd.md
    │       ├── ux.md
    │       ├── tech-design.md
    │       ├── approach.md           # MUST define partitions → feature branches
    │       ├── tasks.md
    │       ├── lifecycle.json        # PR boundaries and step list
    │       ├── emergence-config.json # Review cadence; initiative profile; Building on AI? and eval status
    │       └── tokens.json           # Token usage log
    ├── active/                       # Live specs for in-flight work
    │   └── {initiative-name}/
    │       ├── prd.md
    │       ├── ux.md
    │       ├── tech-design.md
    │       ├── approach.md
    │       └── tasks.md
    ├── graph/                        # Optional local code graph artifacts
    │   ├── codegraph.sqlite          # Active graph DB
    │   ├── metadata.json             # Coverage, freshness, symbol counts
    │   ├── area-plan.json            # Deterministic routing areas
    │   ├── progress.json             # Current build snapshot
    │   ├── progress-log.jsonl        # Append-only build log
    │   ├── spool/                    # Streamed JSONL node/edge staging
    │   └── tools/                    # Extractor diagnostics and semantic logs
    └── archive/                      # Expired specs (timestamped)
        └── {timestamp}-{name}/
```

### Portability Principle

All scripts are platform-agnostic, using standard Python 3 libraries. They avoid hardcoded platform-specific paths and instead rely on the project structure and convention.

---

## Part 3: The Workflow

### Phase 1: Emergence (Drafting)

**Location**: `.cicadas/drafts/{initiative-name}/`

Progressive spec authoring using subagents or manual drafting:

| Step | Artifact | Focus |
|------|----------|-------|
| 0. Intake | `requirements.md` / `loom.md` | **Raw Requirements**. Unstructured input for Clarify subagent via Docs, Loom, or Q&A. |
| 1. Clarify | `prd.md` / `technical-brief.md` | **What & Why**. Product problem, technical problem, users/operators, success criteria. |
| 2. UX | `ux.md` / `operator-experience.md` | **Experience**. Product interaction flow plus an HTML/CSS mock-up for screen-based UI, or operator-facing CLI/log/error/docs/agent workflow. |
| 3. Tech | `tech-design.md` | **Architecture**. Components, data flow, schemas. |
| 4. Approach | `approach.md` | **Strategy & Partitioning**. Implementation plan, sequencing, dependencies, and logical partitions. |
| 5. Tasks | `tasks.md` | **Execution**. Ordered, testable checklist. |

**Critical**: `approach.md` MUST define logical partitions (e.g., "Auth Module", "Frontend Shell", "Data Layer"). These partitions become **Feature Branches**.

**Profile, Pace & Limits**: At the start of Clarify, the Builder chooses an initiative profile (`product` / `technical` / `mixed`) and a review cadence (`section` / `doc` / `all`) stored in `emergence-config.json`. Product initiatives use full PRD and UX artifacts. Technical initiatives use `technical-brief.md` and skip UX only when there is no meaningful human-facing or agent-facing surface; otherwise they use `operator-experience.md`. Mixed initiatives choose the appropriate artifact per surface. For screen-based UX work, the completed `ux.md` must reference at least one editable HTML/CSS mock-up under `.cicadas/drafts/{initiative}/mockups/` before approval; screenshot previews are optional. The standard start flow also records **Building on AI?** (yes/no) and, if yes, eval status (already have / will do); initiatives with "will do" may add an eval spec and placement in Approach. A `tokens.json` log actively captures LLM usage during drafting and updates throughout the initiative.

**Compact Context Contract**: The five core initiative specs (`prd.md`, `ux.md`, `tech-design.md`, `approach.md`, `tasks.md`) now carry machine-readable front matter with:

- `summary`: compact approved summary of the document
- `modules`: likely code areas touched by the work
- `depends_on`: upstream specs or artifacts that inform this document
- `index`: stable section labels pointing to the detailed headings inside the file

This front matter is the low-token re-entry point for later phases and branch starts. Clarify refreshes it as sections are approved, and Reflect refreshes it again when implementation changes the plan.

**Mechanism**: Subagents in `src/cicadas/emergence/` or manual authoring. See `EMERGENCE.md` for details.

### Optional Graph Augmentation

For large and mega repos, Cicadas can optionally build a local code graph with:

`python src/cicadas/scripts/cicadas.py graph build`

This augments canon rather than replacing it. The graph helps with first-hop routing, blast-radius checks, test discovery, and file/symbol search when available.

Current graph characteristics:

- deterministic area planning written to `.cicadas/graph/area-plan.json`
- staged SQLite persistence with progressive progress logs and ETA
- `graph tail` and `graph watch` for long-running build observability
- graph-native search over files, symbols, tests, and likely entrypoints
- structural JavaScript/TypeScript indexing
- structural Java baseline plus semantic enrichment batches, which may land as `semantic` or `hybrid`

If Java semantic enrichment encounters pathological files, Cicadas now bisects failed batches, quarantines the smallest failing file set, and retains successful semantic output for the rest of the repo.

### Phase 2: Kickoff

**Trigger**: Drafts are reviewed and approved.

**Action (Script)**: `python src/cicadas/scripts/cicadas.py kickoff {initiative-name} --intent "description"`

**Effect**:
1. Promotes docs from `.cicadas/drafts/{name}/` to `.cicadas/active/{name}/`.
2. Registers the initiative in `registry.json` under `initiatives`.
3. Creates the **initiative branch** — a long-lived integration point where all feature branches merge.
4. Creates a linked initiative worktree only when local config enables initiative worktrees or kickoff is run with `--worktree`.
5. The shared specs become the "constitution" for all feature branches.

**Branch hierarchy**:
```
main
└── initiative/{name}              ← created at kickoff, merges to main once
    ├── feat/{partition-1}         ← registered, forks from initiative
    │   ├── task/.../task-a        ← ephemeral, unregistered
    │   └── task/.../task-b        ← ephemeral, unregistered
    ├── feat/{partition-2}         ← registered, forks from initiative
    └── feat/{partition-3}         ← registered, forks from initiative
```

**Key**: The initiative branch is a *pure code integration branch*. It never touches canon. Canon is updated on `main` after the initiative branch merges (see Phase 5).

### Phase 3: Execution (The Dual Loop)

#### Outer Loop: Start a Feature Branch (Registered)

**When**: Starting a major partition of work defined in `approach.md`.

**Steps**:
1. **Semantic Check (Agent)**: Read `registry.json`. Analyze the new intent against all active feature intents for logical conflicts. This is an LLM reasoning step — module overlap alone is insufficient.
2. **Resolve parent ref**: ensure the initiative parent exists locally or as `origin/initiative/{name}`.
3. **Module Check (Script)**: `python src/cicadas/scripts/cicadas.py branch {branch-name} --intent "description" --modules "mod1,mod2" --initiative {initiative-name}`
4. Review warnings from both the Agent (intent conflicts) and the Script (module overlaps).

**Script effect**:
- Creates git branch (forking from the initiative branch).
- Registers the branch in `registry.json` under `branches`, linked to the initiative.
- Creates `.cicadas/active/{branch-name}/` for branch-specific specs.
- Parallel `feat/` partitions still default to linked worktrees, while initiative and lightweight worktrees are now opt-in through config or `--worktree`.

**Branch Reset Rule**:

At branch start, the agent should treat prior chat detail as stale and re-anchor on approved file-backed context:

- load `canon/summary.md`
- load front matter from the active specs
- open only the indexed sections needed for the current branch or task
- if the host/runtime supports context clearing or compaction, use it opportunistically before reloading

The reset rule is behavioral guidance, not a hard dependency. Correctness must still come from the files even if the host ignores the clear-context hint.

#### Outer Loop: Complete a Feature Branch

**When**: All task branches for this feature are merged.

**Steps**:
1. **Update index (Script)**: `python src/cicadas/scripts/cicadas.py update-index --branch {name} --summary "..."` — logs to the change ledger.
2. **Merge to initiative**: `git checkout initiative/{name} && git merge {branch-name}` — merges into the initiative branch, **not** `main`.

**Key**: No synthesis, no archiving at this step. Active specs stay active — they're the living document for the rest of the initiative, continuously updated by Reflect. Canon is updated only at initiative completion (Phase 5).

#### Inner Loop: Task Branches (Unregistered)

**When**: Daily coding work. These are ephemeral and do NOT touch the registry.

**Steps**:
1. Checkout from Feature Branch: `git checkout -b task/{feature}/{task-name}`
2. Implement code.
3. **Reflect** (see below): Keep active specs current as code reality diverges from plan.
4. Open a **PR** against the feature branch using `python src/cicadas/scripts/cicadas.py open-pr`. Include in the PR description:
   - What was implemented
   - **Reflect findings**: any spec divergences discovered and updated
   - Test results
5. **Code review Merge Gate**: A Code Review process happens to verify structured algorithm checks (task completeness, tech conformance). Code review outputs a persistent `review.md` artifact with a three-way verdict (`PASS`, `PASS WITH NOTES`, `BLOCK`) before allowing merge checks.
6. Builder reviews and approves the PR.
7. Merge the PR into the feature branch. Delete the task branch.

#### Inner Loop: Reflect (Agent Operation)

**Purpose**: Keep active specs in sync with code *during* development, not just at the end.

**Trigger**: After significant code changes; before merging a Task Branch to the Feature Branch.

**Action (Agent)**:
1. Analyze `git diff` against the active specs.
2. Update the relevant docs in `.cicadas/active/` (e.g., `tech-design.md`, `approach.md`, `tasks.md`) to match code reality.
3. Refresh the affected documents' front matter so the compact summaries, dependencies, modules, and section index remain accurate.
3. If the change is significant enough to impact other feature branches, proceed to **Signal**.

**This is NOT a script** — it is an LLM reasoning + file editing operation performed by the agent.

#### Phase Reset and Partition Reset

Approved spec boundaries and partition starts are also reset points:

- **Phase Reset**: after PRD, UX, Tech, Approach, or Tasks approval, carry forward the approved front matter and the indexed sections needed by the next phase rather than the full drafting dialogue
- **Partition Reset**: when starting a partition, default to that partition's `approach.md` and `tasks.md` sections; do not load unrelated partitions unless ambiguity or conflict requires it

As with Branch Reset, the method may ask the host to clear or compact context when supported, but approved on-disk state remains authoritative either way.

### Phase 4: Coordination (Signals)

**Problem**: Feature A changes an API signature that Feature B depends on. Feature B's developer needs to know.

**Action (Script)**: `python src/cicadas/scripts/cicadas.py signal "Changed Auth API: renamed login() to authenticate()"`

**Effect**:
- Appends a timestamped signal to the Initiative entry in `registry.json`.

**Reception**:
- `python src/cicadas/scripts/cicadas.py status` surfaces unacknowledged signals.
- The Agent should check for signals when performing a **Check Status** operation and assess their relevance.

### Phase 5: Initiative Completion (Outer Loop: Canon Update & Archive)

**Trigger**: All feature branches for the initiative are merged into the initiative branch.

Synthesis and archiving are **outer loop functions** — they happen once, when all inner loops are done. During development, the active specs + Reflect serve as the living document.

#### Step 1: Merge Code to Main

1. `git checkout main && git merge initiative/{name}` — **code merge only**. The initiative branch never touched canon, so there are no documentation conflicts.
2. `git branch -d initiative/{name}` — delete the initiative branch.

**Why merge first, then synthesize**: Canon is meant to *replace*, not *merge*. If synthesis happened on the initiative branch, merging canon files to `main` would use git's 3-way merge — which could conflict with previous canon versions. By synthesizing directly on `main`, canon is a simple file write (overwrite old, create new). No merge strategy needed, ever.

#### Step 2: Update Canon on Main (Agent Operation)

**Inputs**:
- The complete codebase on `main` (now includes all initiative code)
- Active specs from `.cicadas/active/{initiative}/` (continuously updated by Reflect — they reflect the *actual* system, not the original plan)
- Existing canon from `.cicadas/canon/` (may be empty on greenfield)
- Change ledger from `.cicadas/index.json`

**Outputs**:
- `canon/product-overview.md` (Goals, Personas, Metrics)
- `canon/ux-overview.md` (Design Principles, Patterns, Flows)
- `canon/tech-overview.md` (Architecture, Components, API, Schema)
- `canon/summary.md` for compact branch-start context
- For adaptive repos: `canon/repo.json`, `canon/repo-tree.jsonl`, and `canon/repo-context.md`
- Module-level snapshots in `canon/modules/` for regular repos when useful
- Slice packs in `canon/slices/` for large and mega repos

**Protocol**:
1. **Read**: Code on `main`, active specs, existing canon, change ledger.
2. **Synthesize**: Write canon to reflect the *new reality* of the code. On greenfield, create from scratch. On subsequent initiatives, update existing canon.
   - `normal-repo`: broad canon synthesis remains the default.
   - `large-repo` / `mega-repo`: use targeted reconcile. Update touched slices first, expand to neighboring slices only when boundaries, interfaces, or invariants changed, and refresh top-level orientation docs only when durable repo-wide truth changed.
3. **Crucial**: Extract "Key Decisions" from the active specs and embed them in canon. This preserves the "why" before the specs are archived.
4. **Verify**: Ensure the new canon accurately describes the code as it exists *now* on `main`.

Use the prompt in `src/cicadas/templates/synthesis-prompt.md` to guide this process.

**Builder review**: The Builder reviews the synthesized canon before proceeding.

#### Step 3: Archive & Commit

1. Run: `python src/cicadas/scripts/cicadas.py archive {initiative-name}` — moves all active specs to `archive/`.
2. Remove the initiative from `registry.json`.
3. Commit canon + archive as a follow-up commit on `main`.
4. Push to remote.

**Result**: `main` receives two commits — the code merge, then the synthesis/archive commit. Canon is always synthesized *from* main, *on* main.

---

## Part 4: Reference Guides

### Guide 1: Bootstrapping an Existing Project
When starting Cicadas on a codebase that already has code:
1. **Initialize**: Run `python src/cicadas/scripts/cicadas.py init`.
2. **Reverse Engineer**: Follow `src/cicadas/REVERSE_ENGINEERING.md` for disciplined code discovery.
3. **Analyze**: Identify core modules and architectural patterns.
4. **Draft Canon**:
    - Run adaptive scan/bootstrap to classify the repo and seed orientation docs.
    - For `normal-repo`, keep the canon flat and add module snapshots only where they improve local understanding.
    - For `large-repo` / `mega-repo`, seed a small set of lazy `slices/` packs and deepen them later on first real use.
5. **Seed Index**:
    - Run `python src/cicadas/scripts/cicadas.py update-index --branch "bootstrap" --summary "Initial bootstrap"`.

### Guide 2: Canon Synthesis (The LLM's Core Task)
**When to run**: At initiative completion, on `main`, after the code merge. NOT per-feature-branch.
**Goal**: Produce canon that reflects the *complete reality* of the code on `main`.

**Protocol**:
1. **Read**:
    - The codebase on `main` (now includes all initiative code).
    - The active specs in `.cicadas/active/{initiative}/` (updated by Reflect throughout development).
    - The existing canon in `.cicadas/canon/` (may be empty on greenfield).
    - The change ledger in `.cicadas/index.json` (for feature branch summaries).
2. **Synthesize**:
    - On greenfield: create canon from scratch.
    - On subsequent initiatives: update existing canon — overwrite, don't merge.
    - Update `product-overview.md` if product scope changed.
    - Update `tech-overview.md` if architecture changed.
    - For `normal-repo`, update relevant `modules/{name}.md` files when needed.
    - For `large-repo` / `mega-repo`, reconcile touched `slices/{name}/` packs first and expand only when the initiative changed interfaces, boundaries, or invariants.
    - **Crucial**: Extract "Key Decisions" from the active specs and embed them in canon. This preserves the "why" before the specs are archived.
3. **Verify**: Ensure the new canon accurately describes the code as it exists *now* on `main`.
4. **Builder review**: Present canon for review before archiving and committing.

### Guide 3: Conflict Resolution
Run: `python src/cicadas/scripts/cicadas.py check`

**Interpreting Output**:
- **Module Overlap**: Another branch is touching the same modules. *Action*: Check their active specs, coordinate.
- **Signals**: Another branch broadcast a change. *Action*: Assess relevance and update your approach.
- **Main Updates**: New commits on main. *Action*: Rebase your branch.
- **Registry Desync**: Branch not registered. *Action*: Run `python src/cicadas/scripts/cicadas.py branch ...` to register it.

### Guide 4: Agent Guardrails
1. **No Unplanned Work**: Never start writing code until you have a reviewed `tasks.md`.
2. **Branch Only**: Only implement code on a registered feature branch, fix branch, tweak branch, or a task branch off of one.
3. **Hard Stop**: After drafting specs, STOP and wait for the Builder to approve. After synthesis, STOP and wait for the Builder to review canon.
4. **Tool Mandate**: NEVER manually edit `registry.json`. ALWAYS use the scripts.
5. **Merge Boundaries**: A per-initiative `lifecycle.json` defines PR boundaries and step lists, with `python src/cicadas/scripts/cicadas.py open-pr` handling code review validation through `review.md` artifacts.
6. **Reflect Before PR**: Always run the Reflect operation before opening a PR for a task branch. Include Reflect findings in the PR description.
7. **No Canon on Branches**: Never write to `.cicadas/canon/` on any branch. Canon is only updated on `main` at initiative completion.

### Guide 5: Agent Autonomy Boundaries
The Agent handles all ceremony behind natural-language commands from the Builder. Some actions are autonomous; others require Builder confirmation.

| Action | Autonomy | Rationale |
|--------|----------|----------|
| **Reflect** | Autonomous | Keeping specs current is mechanical — the Agent diffs and updates. |
| **Signal** | Autonomous | The Agent assesses cross-branch impact and signals when needed. |
| **Semantic Intent Check** | Autonomous | Conflict detection is informational. |
| **PR creation** | Autonomous | The Agent opens PRs with summaries and Reflect findings. |
| **PR merge** | **Builder approval** | Code review is a human gate. |
| **Synthesis** | Autonomous (execution) | The Agent produces canon, but... |
| **Canon commit** | **Builder approval** | ...canon must be reviewed before committing to `main`. |
| **Archive** | **Builder approval** | Archiving is irreversible — specs move to archive after Builder confirms canon. |

### Guide 6: Builder Commands
The Builder interacts via natural-language commands. The Agent handles all scripts, git operations, and agentic operations behind the scenes.

- **"Initialize cicadas"**: Runs `python src/cicadas/scripts/cicadas.py init`. Sets up `.cicadas/` structure.
- **"Kickoff {name}"**: Runs `python src/cicadas/scripts/cicadas.py kickoff`. Promotes drafts, registers initiative, creates the initiative branch/worktree.
- **"Start feature {name}"**: Semantic check + `python src/cicadas/scripts/cicadas.py branch`. Creates feature branch from initiative branch, registers, checks conflicts.
- **"Implement task {X}"**: Creates task branch, implements, Reflects, opens PR with findings.
- **"Signal {message}"**: Runs `python src/cicadas/scripts/cicadas.py signal`. Broadcasts change to initiative.
- **"Complete feature {name}"**: Runs `python src/cicadas/scripts/cicadas.py update-index`. Merges feature branch into initiative branch.
- **"Complete initiative {name}"**: Merges initiative to `main`, updates canon on `main`, archives specs, commits.

---

## Part 5: Workflow Quick Reference

### Scripts (Deterministic)

| Phase | Command | Action |
|-------|---------|--------|
| **Init** | `python src/cicadas/scripts/cicadas.py init` | Bootstrap project structure |
| **Kickoff** | `python src/cicadas/scripts/cicadas.py kickoff {name} --intent "..."` | Promote drafts, register initiative |
| **Feature** | `python src/cicadas/scripts/cicadas.py branch {name} --intent "..." --modules "..." --initiative {name}` | Register feature branch |
| **Status** | `python src/cicadas/scripts/cicadas.py status` | Show global state & signals |
| **Check** | `python src/cicadas/scripts/cicadas.py check` | Check for conflicts & updates |
| **Signal** | `python src/cicadas/scripts/cicadas.py signal "{message}"` | Broadcast to initiative |
| **PR** | `python src/cicadas/scripts/cicadas.py open-pr` | Reads review target and creates PR |
| **Archive** | `python src/cicadas/scripts/cicadas.py archive {name}` | Expire active specs & initiative |
| **Log** | `python src/cicadas/scripts/cicadas.py update-index --branch {name} --summary "..."` | Record history |
| **Prune** | `python src/cicadas/scripts/cicadas.py prune {name} --type {branch\|initiative}` | Rollback & restore to drafts |

### Agent Operations (LLM)

| Operation | Trigger | Action |
|-----------|---------|--------|
| **Semantic Intent Check** | Before starting a feature branch | Analyze registry intents for logical conflicts |
| **Reflect** | After significant code changes, before PR | Update active specs to match code reality. Include findings in PR. |
| **Signal Assessment** | After Reflect, during status check | Evaluate cross-branch impact. Signal autonomously if needed. |
| **Synthesis** | At initiative completion, on `main` | Update canon from code + active specs. Full for normal repos; targeted reconcile for large/mega repos. Requires Builder review. |

### File Locations
- Orchestrator: `src/cicadas/`
- Artifacts: `.cicadas/`
- Agent Manual: `src/cicadas/SKILL.md`

---

## Part 6: Known Issues & Future Directions

Issues identified through dry-run exercises (greenfield, brownfield, and parallel multi-developer scenarios). These are documented limitations of the current method — not blockers, but areas to improve as real-world usage reveals patterns.

### 8.1 Synthesis

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| S1 | **Greenfield bootstrap mode**: First synthesis creates canon from scratch — different from update synthesis. The synthesis prompt needs to handle both modes. | Medium | Detect empty `canon/` and switch to creation mode automatically. |
| S2 | **Update synthesis fidelity**: On brownfield, the LLM must distinguish "preserve this" from "update this." Risk of accidentally dropping existing canon content. | High | Synthesis should output a change plan (sections added/modified/untouched) before writing. Builder reviews the plan. |
| S3 | **Context window pressure**: Synthesis reads the entire codebase + active specs + existing canon + change ledger. On mature projects, this exceeds context limits. | High | Prioritize by module. Synthesize module-by-module rather than holistically. Use code summaries rather than full source. |
| S4 | **Unchanged module verification**: Synthesis should verify that modules declared "unchanged" truly are — by diffing source code against existing module snapshots. | Medium | Add a verification pass to the synthesis prompt. |
| S5 | **Canon diff review**: Builders review synthesis output as full files. A diff view (old canon → new canon) would be dramatically faster. | Low | Tooling improvement — generate a git diff of `canon/` after synthesis, before commit. |

### 8.2 Canon Lifecycle

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| C1 | **Canon accumulation**: Canon grows each initiative but never shrinks. Key Decisions span all historical initiatives. Over time, canon drifts toward exhaustive reference docs. | Medium | Tag Key Decisions with the initiative that produced them. Add a "prune" pass to synthesis — remove obsolete sections. |
| C2 | **Intermediate spec snapshots lost**: Active specs mutate via Reflect across all feature branches. By initiative completion, they reflect only the final state. | Low | Git history of `.cicadas/active/` provides intermediate states if needed. Acceptable trade-off. |

### 8.3 Coordination & Signals

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| X1 | **Signals are intra-initiative only**: No formal mechanism for cross-initiative notifications. Builder A's Recipe changes can't directly signal Builder B's separate initiative. | Medium | Add a global signal board in `registry.json`, or allow signals to target specific initiatives. |
| X2 | **Stale canon at Emergence for concurrent initiatives**: Builder B drafts specs against current `main` canon, but another initiative may be modifying the same modules. Specs are drafted against outdated context. | Medium | During Emergence, the Agent should read not just canon but also the active specs of in-flight initiatives — surfacing planned changes to shared modules. |
| X3 | **Active specs are initiative-scoped**: At synthesis time, the LLM reads only its own initiative's specs. If Initiative B merges before Initiative A, B's synthesis won't have A's key decisions (since A hasn't synthesized yet). | Low | Synthesis prompt should read active specs from *all* in-flight initiatives, not just its own. |

### 8.4 Branching & Merging

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| B1 | **Rebase timing is undefined**: The method doesn't prescribe when initiative branches should rebase against `main`. | Low | Recommend: rebase before starting each new feature branch within the initiative. Document as a best practice. |
| B2 | **Initiative merge ordering**: When two initiatives finish simultaneously, merge order affects which synthesis sees which canon. | Low | Rule of thumb: merge in completion order. If truly simultaneous, coordinate between builders. |
| B3 | **Migration ordering across initiatives**: Parallel initiatives adding database migrations create migration sequence conflicts at rebase/merge. | Medium | Use timestamp-based migration naming, or add a central sequence counter to `registry.json`. |
| B4 | **Shared `tasks.md` conflict risk**: `tasks.md` at the initiative level. Two parallel branches Reflecting simultaneously could create merge conflicts. | Low | Split tasks into per-partition sections with clear markers, or per-branch task files. |

### 8.5 Scripts & Tooling

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| T2 | **Initiative kickoff depends on git metadata writes**: Environments that can edit the worktree but not `.git` internals can promote specs without creating the initiative branch or worktree. | Medium | Detect git permission failures explicitly and offer a sequential single-worktree fallback or a clear retry path with elevated git access. |
| T3 | **`branch.py` should enforce parent branch**: Forks from current HEAD. A `--from` flag (defaulting to the linked initiative branch) would prevent mistakes. | Low | Add `--from` flag to `branch.py`. |

### 8.6 Process & Ergonomics

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| P1 | **Overhead for solo builders**: Full ceremony (registrations, intent checks, Reflect, PRs) is significant for one person. | Low | Document a "light mode": fewer partitions, combined steps, optional PRs for solo. |
| P2 | **No explicit test phase**: The method doesn't prescribe where testing fits in the lifecycle. | Low | Tasks should include acceptance criteria. Task branches aren't merge-ready until tests pass. Document as convention. |
| P3 | **Module boundary crossings on brownfield**: Existing code has implicit ownership. Modifications to shared components outside a feature's declared modules need special attention. | Low | Reflect already flags these. Formalize as a "boundary crossing" annotation in PRs. |

### Future Direction: Full WIP Awareness

> [!IMPORTANT]
> The most significant gap across all scenarios is that Cicadas operates within a single initiative's context. In future versions, the Agent should be aware of **all work in progress across all initiatives** — reading other initiatives' active specs during Emergence, signaling across initiative boundaries, and incorporating cross-initiative context during synthesis.
>
> This would address issues X1, X2, X3, and S2 simultaneously. The registry already contains the required information; the Agent simply needs to be instructed to use it holistically.
>
> For now, the method works — Reflect catches post-rebase drift, the registry surfaces overlap at branch registration, and serial synthesis on `main` prevents canon merge conflicts. The coordination gaps are manageable with developer communication.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
