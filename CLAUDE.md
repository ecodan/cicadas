# CLAUDE.md

This file provides guidance to **Claude Code** (claude.ai/code) when working with code in this repository. It is not used by Cursor, Antigravity, Rovodev, or other agents — those environments use the Cicadas skill file (`SKILL.md` / `cicadas.mdc`) alone, which includes the same implementation guardrails.

## Python / Environment

Tests are written in **`unittest` style** and are commonly run with `uv run pytest`. The project currently declares `pytest` and `pytest-cov` in the dev dependency group in `pyproject.toml`, and recent CLI coverage was verified with `uv run pytest`.

## Commands

**Run all tests:**
```bash
uv run pytest
```

**Run a single test file:**
```bash
uv run pytest tests/test_kickoff.py
```

**Run the context-template regression checks:**
```bash
uv run pytest tests/test_templates.py
```

**Run a single test:**
```bash
uv run pytest tests/test_kickoff.py -k test_basic_kickoff
```

**Run with coverage:**
```bash
uv run pytest --cov=src/cicadas/scripts --cov-report=term-missing
```

**Lint:**
```bash
source .venv/bin/activate && ruff check src/ tests/
```

**Format:**
```bash
source .venv/bin/activate && ruff format src/ tests/
```

**CLI scripts**:
```bash
python src/cicadas/scripts/cicadas.py init
python src/cicadas/scripts/cicadas.py status
python src/cicadas/scripts/cicadas.py check
python src/cicadas/scripts/cicadas.py kickoff {name} --intent "..."
python src/cicadas/scripts/cicadas.py kickoff {name} --intent "..." --worktree
python src/cicadas/scripts/cicadas.py branch {name} --intent "..." --modules "mod1,mod2" --initiative {name}
python src/cicadas/scripts/cicadas.py branch {name} --intent "..." --modules "mod1,mod2" --initiative {name} --worktree
python src/cicadas/scripts/cicadas.py signal "message"
python src/cicadas/scripts/cicadas.py archive {name} --type {branch|initiative}
python src/cicadas/scripts/cicadas.py update-index --branch {name} --summary "..."
python src/cicadas/scripts/cicadas.py create-lifecycle {name}  # optional: --pr-specs, --no-pr-initiatives, etc.
python src/cicadas/scripts/cicadas.py open-pr [--base branch]   # open PR from current branch (gh/glab/URL/fallback); blocks on BLOCK verdict
python src/cicadas/scripts/cicadas.py review [--initiative name]  # check review.md verdict (exit 0=PASS, 1=BLOCK, 2=not found)
python src/cicadas/scripts/cicadas.py prune {name} --type {branch|initiative}
python src/cicadas/scripts/cicadas.py abort
python src/cicadas/scripts/cicadas.py history [--output path]
python src/cicadas/scripts/cicadas.py validate-skill {slug-or-path}
python src/cicadas/scripts/cicadas.py skill-publish {slug} [--publish-dir DIR] [--symlink] [--force]
python src/cicadas/scripts/cicadas.py unarchive {name}
python src/cicadas/scripts/cicadas.py emit-event --initiative {name} --type {event.type} [--data '{json}']
python src/cicadas/scripts/cicadas.py get-events --initiative {name} [--type prefix] [--since ISO] [--last N]
python src/cicadas/scripts/cicadas.py tokens --help
python src/cicadas/scripts/cicadas.py graph build
python src/cicadas/scripts/cicadas.py graph search <query>
python src/cicadas/scripts/cicadas.py graph watch
python src/cicadas/scripts/cicadas.py graph usage --view table
python src/cicadas/scripts/cicadas.py tutorial
python src/cicadas/scripts/cicadas.py init --tutorial    # run tutorial automatically
python src/cicadas/scripts/cicadas.py init --no-tutorial # skip tutorial prompt
```

## Architecture

Cicadas is a **spec-driven development methodology toolset** for human-AI teams. It consists of two parts:

1. **The Skill** (`src/cicadas/`) — portable CLI scripts and agent instructions that can be dropped into any project.
2. **The State** (`.cicadas/`) — filesystem-based state managed by the scripts, living in the project root.

### `src/cicadas/` Structure

- `scripts/` — the repo-local common CLI lives at `cicadas.py`, with `command_registry.py` mapping subcommands to the underlying deterministic tools. Those tools share `utils.py` for root detection (`get_project_root()`), worktree-aware registry root detection (`get_registry_root()`, `get_registry_dir()` — always routes `registry.json`/`index.json` I/O to the primary worktree), shared worktree config (`load_config()`, `worktree_policy()`), branch detection (`get_default_branch()`), JSON I/O (`load_json`/`save_json`), worktree helpers (`create_worktree`, `remove_worktree`, `worktree_path`), and `emit()` (non-fatal event emitter, lazy-imports `emit_event`). `scan_repo.py` classifies repo scale and seeds adaptive canon metadata while excluding local Cicadas workspaces (`.cicadas-skill/`), directories containing `SKILL.md` (SDD installs and skill bundles at arbitrary paths), root-level hidden/underscore dirs matching known SDD tool substrings (`bmad`, `cicadas`, `gsd`, `openspec`), and any paths in `config.json`'s `scan_exclude_paths` from routing inputs, while `synthesize.py` supports targeted initiative-end reconcile for large/mega repos. `tokens.py` provides the append-only token usage log API (`init_log`, `append_entry`, `load_log`) used by `kickoff.py` and `branch.py`, while `cicadas.py tokens ...` exposes the token workflow through the common command surface. `emit_event.py` appends typed events to `events.jsonl` with `fcntl.flock` concurrent-write safety; `cicadas.py emit-event` forwards the same flags. `get_events.py` reads and filters `events.jsonl` (exit 0 + empty if absent); `cicadas.py get-events` forwards `--initiative`, `--type`, `--since`, and `--last`. `review.py` reads `review.md` verdict and returns exit codes; imported by `open_pr.py` for the merge gate check. `validate_skill.py` checks an Agent Skill directory against the spec (name charset/length/dir-match, description ≤1024 chars, frontmatter delimiters) using stdlib regex. `skill_publish.py` copies or symlinks an active skill to its `publish_dir` with a pre-publish validation gate. `unarchive.py` restores archived state from metadata snapshots. The optional graph stack now includes staged SQLite persistence, deterministic `area-plan.json` routing output, `graph search`, `graph tail`, `graph watch`, structural JS/TS extraction, and a Java semantic harness that can land `semantic` or `hybrid` coverage with batch bisection/quarantine on problematic files.
- `emergence/` — Markdown instruction modules (Clarify, UX, Tech, Approach, Tasks, Bootstrap, Bug-fix, Tweak, Eval Spec, Code Review, plus deprecated legacy Skill Create and Skill Edit docs) — inline role files read in the current context window; no separate agent process is spawned. **start-flow.md** defines the standard start flow for initiative, tweak, and bug entrypoints, and still documents a deprecated legacy skill path for compatibility. Building on AI and eval status are stored in `emergence-config.json` (skills skip the eval-status follow-up — Post-MVP). **skill-create.md** and **skill-edit.md** remain only as deprecated legacy Agent Skill authoring docs. For initiatives building on AI with "will do" evals, **eval-spec.md** guides creation of `eval-spec.md` in drafts/active after PRD/UX/Tech; Approach asks eval placement (before build / in parallel). For tweaks/bugs, a light-touch reminder can be added to the tweaklet/buglet. Cicadas does not run evals. Clarify supports intake via Q&A, a requirements doc (`drafts/{initiative}/requirements.md`), or a Loom transcript (`drafts/{initiative}/loom.md`), and now refreshes the approved front matter fields rather than the older `steps_completed` metadata. These are **agent prompts**, not code.
- `templates/` — Markdown templates for specs (`prd.md`, `ux.md`, `tech-design.md`, `approach.md`, `tasks.md`, `buglet.md`, `tweaklet.md`, `eval-spec.md`, `review.md`, `skill-SKILL.md`) and Canon docs (`product-overview.md`, `ux-overview.md`, `tech-overview.md`, `module-snapshot.md`, `canon-summary.md`). The five core initiative templates now share a compact front matter contract (`summary`, `modules`, `depends_on`, `index`) for context routing, and `canon-summary.md` includes a branch-start cue for reloading minimal approved state. Large and mega repos also use slice canon templates for seeded local packs.
- `SKILL.md` — The master agent skill definition (read this for full operational detail).
- `implementation.md` — Guardrails for implementation agents.

### `.cicadas/` State Directory

```
.cicadas/
├── registry.json     # Source of truth for all active initiatives + feature branches + signals
├── index.json        # Append-only ledger of completed work
├── canon/            # Authoritative docs synthesized from code (NEVER edited manually; NEVER on feature branches; may include adaptive repo metadata and slices/)
├── drafts/           # Staging area for new initiatives before kickoff
├── active/           # Live specs driving current work
├── graph/            # Optional local graph DB, progress logs, area plan, spool/, tools/
└── archive/          # Timestamped expired specs from completed initiatives
```

### Branching Model

| Prefix | Forks From | Registered | Purpose |
|--------|-----------|------------|---------|
| `initiative/` | default branch (`main` by default) | Yes | Integration branch for a full initiative |
| `feat/` | `initiative/` | Yes | One partition of an initiative |
| `fix/` | default branch (`main` by default) | Yes | Lightweight bug fix |
| `tweak/` | default branch (`main` by default) | Yes | Lightweight enhancement (<100 LOC) |
| `skill/` | default branch (`main` by default) | Yes | Agent Skill authoring |
| `task/` | `feat/` | No | Ephemeral; never registered |

Parallel `feat/` partitions still default to linked worktrees. `fix/`, `tweak/`, and `skill/` branches now stay in the current workspace unless config or `--worktree` opts into a linked worktree.

### Initiative Lifecycle

1. **Emergence** — Draft specs in `.cicadas/drafts/{name}/` using instruction modules in `emergence/`.
2. **Kickoff** — `kickoff.py` promotes drafts → `active/`, registers in `registry.json`, and creates `initiative/{name}` without switching the main worktree. Initiative worktrees are now opt-in through `.cicadas/config.json` or `--worktree`.
3. **Feature Branches** — `branch.py` creates `feat/{name}`, declares module scope to detect overlaps.
4. **Inner Loop** — Task branches → Reflect (update active specs to match code) → PR to feature branch (if lifecycle has PR at tasks).
   Reflect now includes refreshing front matter metadata on the affected specs so compact context entrypoints remain current.
5. **Complete Initiative** — Merge the initiative into the default branch (`main` by default), then update Canon there and archive specs (move to `archive/` and deregister).
   `normal-repo` uses broad synthesis; `large-repo` and `mega-repo` use targeted reconcile over touched slices plus selective global doc refresh.
6. **Lifecycle** — Per-initiative `lifecycle.json` (drafts/active) sets PR boundaries and steps; `cicadas.py status` reports Merged/Next (git-based).

### Key Invariants (Guardrails)

- **Never manually edit `registry.json`** — always use the scripts.
- **Never write to `.cicadas/canon/` on any branch** — Canon is only updated on the default branch (`main` by default) at initiative completion.
- **No code without a reviewed `tasks.md`** — agents must stop after Emergence and wait for Builder approval.
- **Reflect before every PR** — active specs must match code before merging any task branch.
- **Prefer file-backed context resets** — at branch starts and spec/partition boundaries, reload from `canon/summary.md`, spec front matter, and indexed sections before trusting prior conversation. If the host supports context clearing or compaction, use it opportunistically, but do not rely on it for correctness.

### Test Conventions

Tests live in `tests/` and inherit from `CicadasTest` in `tests/base.py`. The base class:
- Creates a temp directory and `chdir`s into it.
- Sets up a minimal `.cicadas/` structure with empty `registry.json` and `index.json`.
- Provides `init_git()` for tests that need a real git repo.
- Cleans up in `tearDown`, including removing any linked worktrees created during the test.

Tests are written in `unittest` style and run cleanly under `pytest`. `tests/conftest.py` keeps `src/cicadas/scripts` importable during collection, and many tests still inherit from `CicadasTest` in `tests/base.py` for real filesystem and git setup.

Graph-heavy changes should keep `tests/test_graph.py` and `tests/test_scan_repo.py` current. Those suites cover staged graph persistence, routing/search behavior, Java semantic batching, exclusion of local Cicadas workspaces from repo inventory, and the SDD install/state-dir exclusion logic (SKILL.md detection, SDD substring matching, and `scan_exclude_paths` config).

**Testing bias — real filesystems over mocks:** Prefer tests that operate on real temporary filesystems and real git repositories over mocks. Cicadas scripts touch the filesystem and git directly; mocking these layers hides the integration bugs that matter. Mocks are acceptable only for pure logic with no I/O side-effects (e.g., string parsing, slug computation).
