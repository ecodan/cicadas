# Tech Overview

> Canon document. Updated by the Synthesis agent at the close of each initiative.

## Architecture Summary

Cicadas is a filesystem-based state machine that orchestrates development via Git and JSON-based registries. It separates logic (the "Skill") from state (the `.cicadas/` directory). Distribution and installation is managed by a standalone bash script (`install.sh`) that requires only `bash`, `curl`, and `unzip`.

### Key Decisions

- **Expiring Specs** — Active specs live in `.cicadas/active/` and are moved to `.cicadas/archive/` upon completion. This prevents developers from relying on outdated documents.
- **Hierarchical Branching** — Complex work uses `initiative/{name}` and `feat/{name}` branches. Lightweight work forks directly from `master` using `fix/` or `tweak/`.
- **Registry Source of Truth** — `registry.json` is the definitive map of all in-flight work and cross-branch signals.
- **Distribution-First Design** — `install.sh` is the primary entry point; uses GitHub archive URL for zero-friction distribution without requiring a release pipeline.
- **Universal Installation** — Installer works on any project stack (Go, Java, React, etc.); only requires Python 3.11+ and `git` at runtime.
- **Lifecycle & PR Boundaries** — Per-initiative `lifecycle.json` (in drafts/active) defines at which boundaries to open PRs (specs, initiatives, features, tasks) and an ordered step list; completion is detected via git only (no host API).
- **Token Usage Logging** — Each initiative carries an append-only `tokens.json` (drafts → active → archive) that captures input/output/cached token counts per phase and subphase. Scripts write null phase-boundary entries (`source: unavailable`); agents self-append real counts when the runtime exposes them (`source: agent-reported`). `history.py` rolls up per-initiative token summaries into the HTML timeline.
- **Emergence Pace** — At the start of Clarify, the Builder chooses a review cadence (`section` / `doc` / `all`) stored in `emergence-config.json`. Every subsequent emergence agent reads this file and enforces the stop rule, preventing agents from silently drafting all specs without review gates.
- **Clarify Intake** — At Clarify start, the Builder can provide requirements via **Q&A** (interactive), **Doc** (place a file at `.cicadas/drafts/{initiative}/requirements.md`), or **Loom** (save the video transcript to `.cicadas/drafts/{initiative}/loom.md`). The agent fills the PRD from the doc or transcript. All intake logic lives in `emergence/clarify.md`; no scripts read these files. `EMERGENCE.md` documents the convention for discoverability.
- **Building on AI** — Start flow (all entry points) includes a **Building on AI?** step after draft folder: ask yes/no; if yes, ask eval status (already have / will do). Both stored in `emergence-config.json` (merge with existing keys e.g. `pace`). Initiatives with "will do" evals: after PRD/UX/Tech the agent may offer eval-spec authoring (`emergence/eval-spec.md`, template `templates/eval-spec.md`, six-step LLMOps playbook); during Approach, agent asks eval placement (before build / in parallel) and writes `eval_placement`; adds explicit Eval step to approach.md. Tweaks/bugs with "will do": agent offers to add one eval/benchmark reminder task or section to tweaklet/buglet. Cicadas does not execute or host evals. `parse_partitions_dag()` in `utils.py` uses PyYAML when available and a regex fallback when not, so partition parsing works in environments without PyYAML.
- **Code Review Merge Gate** — Code review produces a persistent `review.md` artifact (not an ephemeral console report) with a three-way verdict: `PASS`, `PASS WITH NOTES`, or `BLOCK`. `open_pr.py` reads this file and refuses to open a PR on `BLOCK`. The verdict is always advisory; the Builder retains merge authority.
- **Context Injection at Branch Start** — `branch.py` writes a `context.md` bundle to the branch's working directory on creation (worktree root for parallel branches; project root for sequential branches). Bundle contains: `canon/summary.md` (if present), full module snapshots for the branch's declared scope, and the initiative's `approach.md` + `tasks.md`. Provides agents with the right context immediately without requiring manual file reads. `context.md` is gitignored.
- **Event Log** — Each initiative carries an append-only `events.jsonl` at `.cicadas/active/{initiative}/events.jsonl` (moves to archive with specs). `emit_event.py` is the sole write path; uses `fcntl.flock` for concurrent-write safety. `get_events.py` is the sole read interface; exits 0 + empty output if the file is absent (design invariant: consumers never read `events.jsonl` directly, ensuring future storage refactors don't break callers). All lifecycle scripts emit typed events automatically via `utils.emit()` (non-fatal; failure never crashes a script). Implementation agents emit `task.complete` and `partition.complete` per Rules 9–10 in `implementation.md`.
- **Machine-Testable Partition Specs** — `approach.md` template includes **Artifact Type**, **How to Run**, and **Acceptance Criteria** subsections per partition block. `emergence/approach.md` Step 4b guides automated generation of these subsections by artifact type (unit tests, integration tests, visual output, CLI output, etc.). Together these fields provide enough information for an evaluator agent to verify partition completion without reading the full spec.

---

## Directory Schema

```
.cicadas/
├── registry.json                 # Global state (initiatives + feature branches)
├── index.json                    # Change ledger (append-only)
├── canon/                        # Authoritative documentation (synthesized)
├── drafts/                       # Pre-kickoff staging area (may include lifecycle.json, tokens.json, emergence-config.json)
├── active/                       # Live specs for in-flight work (may include lifecycle.json, tokens.json)
└── archive/                      # Expired spec trail
```

---

## Branching Model

| Prefix | Source | registered? | Purpose |
|--------|--------|-------------|---------|
| `initiative/` | `master` | Yes | Parent branch for multi-partition work. |
| `feat/` | `initiative/` | Yes | Vertical slice of an initiative. |
| `fix/` | `master` | Yes | Lightweight bug fix. |
| `tweak/` | `master` | Yes | Lightweight enhancement. |
| `task/` | `feat/` | No | Ephemeral implementation branch. |

---

## Installation & Distribution

### `install.sh` — Entry Point

A portable bash script in the project root that handles installation, setup, and updates. Requires only `bash`, `curl`, `unzip`, and `git`.

**Key features:**
- **Python 3.11+ Check**: Validates version; prints OS-specific install guidance if missing.
- **GitHub Archive Distribution**: Downloads `master.zip`, extracts to `.cicadas-skill/cicadas/` (configurable via `--dir`).
- **Workspace Initialization**: Calls `init.py` to initialize the `.cicadas/` directory structure.
- **Agent Integration Setup**: Optionally creates symlinks/configs for `claude-code` (`.claude/skills/cicadas`), `antigravity` (`.agents/skills/cicadas`), `cursor` (`.cursor/rules/cicadas.mdc`), and `rovodev` (`.rovodev/skills/cicadas`).
- **Update Workflow**: `--update` flag re-downloads skill files without touching `.cicadas/` state or re-running init.

```bash
curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash
bash install.sh --dir tools/cicadas --agent claude-code,cursor
bash install.sh --update
```

---

## CLI Orchestration

The system uses a set of Python scripts in `src/cicadas/scripts/`:
- `init.py`: Initializes `.cicadas/` directory on fresh install (idempotent; called by `install.sh`).
- `kickoff.py`: Promotes drafts (including `lifecycle.json` when present) and registers initiatives.
- `branch.py`: Creates and registers feature/fix/tweak branches. Writes `context.md` (canon summary + scoped module snapshots + approach.md + tasks.md) to the branch's working directory on creation for all branch types.
- `status.py`: Reports global project state; when `lifecycle.json` exists for an initiative, reports Merged (branch pairs) and Next (suggested step) via git-based merge detection.
- `create_lifecycle.py`: Creates `lifecycle.json` in drafts or active with PR boundaries and default steps.
- `open_pr.py`: Opens a PR from current branch (tries `gh` → `glab` → Bitbucket URL → fallback); host-agnostic. Pre-flight checks `review.md` verdict: blocks on `BLOCK`, warns on `PASS WITH NOTES`.
- `review.py`: Reads `.cicadas/active/{initiative}/review.md`, parses the verdict (`PASS`, `PASS WITH NOTES`, `BLOCK`), and exits with 0 (safe to merge), 1 (BLOCK), or 2 (no review.md found). Imported by `open_pr.py`.
- `update_index.py`: Logs changes to the ledger.
- `archive.py`: Concludes work, deregisters branches, and expires specs (includes `lifecycle.json` when present).
- `abort.py`: Context-aware rollback for any branch type.
- `signal.py`: Broadcasts breaking changes across peer branches.
- `tokens.py`: Append-only token usage log API (`init_log`, `append_entry`, `load_log`); called by `kickoff.py` and `branch.py` at phase boundaries.
- `history.py`: Generates HTML timeline of completed initiatives; includes per-initiative token summary when `tokens.json` is present.
- `check.py`: Validates for module conflicts across active branches.
- `emit_event.py`: Appends a typed event to `.cicadas/active/{initiative}/events.jsonl` with `fcntl.flock` concurrent-write safety. Called by lifecycle scripts via `utils.emit()` and directly by agents.
- `get_events.py`: Reads and filters `events.jsonl`; exits 0 + empty output if file absent. Supports `--type` prefix filter, `--since` ISO timestamp, and `--last N` tail.

---

## Implementation Conventions

- **Module-Awareness**: Feature branches declare their module scope in the registry to prevent silent merge conflicts.
- **Reflect Operation**: Agents MUST update active specs before merging any code change.
- **Code Review Operation**: Optional agent operation invoked after Reflect, before opening a PR or merging. Runs a structured algorithm (task completeness, acceptance criteria, arch conformance, module scope, Reflect completeness, security scan, correctness scan, code quality) against the branch diff and active specs. Writes a structured `review.md` to `.cicadas/active/{initiative}/` with verdict `PASS`, `PASS WITH NOTES`, or `BLOCK`. `open_pr.py` enforces this as a merge gate (blocks on `BLOCK`). Defined in `emergence/code-review.md`; checked via `scripts/review.py`.
- **Significance Check**: Lightweight paths must be evaluated for Canon updates before archiving.
- **Relative Symlinks**: Agent integrations use relative symlinks for portability across machines with different mount paths.
- **Non-Interactive Pipe Support**: Installer detects `curl | bash` context (`[ -t 0 ]`) and skips interactive prompts, printing manual setup guidance instead.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
