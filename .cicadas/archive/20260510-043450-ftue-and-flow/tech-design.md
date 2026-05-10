---
summary: "ftue-and-flow adds three additive layers to the Cicadas CLI: a centralized hints utility (hints_enabled() + print_hint()) in utils.py, a standalone tutorial.py script, and next-step inference in status.py. All changes are stdlib-only. Hints are ANSI-colored, TTY-gated, and suppressed by --no-hints flag or hints:false in config.json. No existing output is modified."
phase: "tech"
when_to_load:
  - "When implementing or reviewing hint output, tutorial flow, status improvements, or config changes."
  - "When adding --no-hints flag to any lifecycle command."
depends_on:
  - "prd.md"
  - "ux.md"
modules:
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/tutorial.py"
  - "src/cicadas/scripts/status.py"
  - "src/cicadas/scripts/init.py"
  - "src/cicadas/scripts/cicadas.py"
  - "src/cicadas/scripts/kickoff.py"
  - "src/cicadas/scripts/branch.py"
  - "src/cicadas/scripts/archive.py"
  - "src/cicadas/scripts/update_index.py"
  - "src/cicadas/scripts/open_pr.py"
  - "README.md"
  - "HOW-TO.md"
index:
  overview: "## Overview & Context"
  stack: "## Tech Stack & Dependencies"
  structure: "## Project / Module Structure"
  adrs: "## Architecture Decisions (ADRs)"
  data_models: "## Data Models"
  api: "## API & Interface Design"
  patterns: "## Implementation Patterns & Conventions"
  security: "## Security & Performance"
  sequence: "## Implementation Sequence"
next_section: "Overview & Context"
---

# Tech Design: ftue-and-flow

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
- [x] Architecture Decisions (ADRs)
- [x] Data Models
- [x] API & Interface Design
- [x] Implementation Patterns & Conventions
- [x] Security & Performance
- [x] Implementation Sequence

---

## Overview & Context

This initiative adds three additive layers to the existing Cicadas CLI:

1. **Hints subsystem** — a centralized utility that appends ANSI-colored "Next:" hint blocks after lifecycle commands. Hooks into existing scripts via a single function call at the end of each command's `main()`.
2. **Tutorial script** — a standalone `tutorial.py` that orchestrates a guided walkthrough by calling real Cicadas scripts in sequence with inline explanations. Invoked from `init.py` when `--tutorial` is passed or offered interactively.
3. **Status next-step inference** — extends `status.py` to emit a "Next:" suggestion even when no `lifecycle.json` is present, by inspecting registry state.

**Cross-cutting concerns:**
- **Additive only**: No existing script output is modified. Hints are appended after existing output, never interleaved.
- **TTY gating**: All ANSI and hint output is gated on `sys.stdout.isatty()`. Piped/CI output is unaffected.
- **Centralized suppression**: A single `hints_enabled(args, config)` function in `utils.py` is the sole authority on whether hints print. Scripts never inline this logic.
- **No new dependencies**: Pure Python stdlib. No `rich`, `click`, `colorama`, or other packages.

---

## Tech Stack & Dependencies

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Existing constraint — no change |
| Color output | ANSI escape codes (stdlib) | No new deps; degrades on non-TTY; 16-color only for broad compatibility |
| Config I/O | Existing `load_config()` / `save_json()` in utils.py | Consistent with all other scripts |
| Tutorial orchestration | Direct Python function calls to existing script modules | Keeps tutorial as real Cicadas execution, not simulation |
| Testing | `unittest` + real temp git repos (existing pattern) | Consistent with project conventions |

**Rejected alternatives:**
- `rich` library — would add a dependency and break the zero-dependency constraint.
- Separate color module — unnecessary; ANSI codes are simple enough to centralize in utils.py.
- Subprocess calls in tutorial — brittle; direct module imports keep tutorial in-process and testable.

---

## Project / Module Structure

Only files touched by this initiative:

```
src/cicadas/scripts/
├── utils.py              # ADD: hints_enabled(), print_hint(), print_tutorial_step(), ANSI constants
├── init.py               # MODIFY: add --tutorial/--no-tutorial flags; offer tutorial on first run
├── tutorial.py           # NEW: standalone tutorial orchestrator
├── status.py             # MODIFY: add inferred next-step block when lifecycle absent
├── cicadas.py            # MODIFY: register tutorial subcommand; add --no-hints to all lifecycle commands
├── kickoff.py            # MODIFY: call print_hint() at end of main()
├── branch.py             # MODIFY: call print_hint() at end of main()
├── archive.py            # MODIFY: call print_hint() at end of main()
├── update_index.py       # MODIFY: call print_hint() at end of main()
└── open_pr.py            # MODIFY: call print_hint() at end of main()

README.md                 # REWRITE: getting-started narrative
HOW-TO.md                 # UPDATE: tutorial mode + hint toggle docs

tests/
├── test_hints.py         # NEW: hint suppression, TTY gating, config toggle
├── test_tutorial.py      # NEW: tutorial flow, real artifact creation, idempotency
└── test_status.py        # MODIFY: add inferred next-step cases
```

---

## Architecture Decisions (ADRs)

### ADR-1: Centralize hint logic in utils.py, not per-script

**Decision:** All hint-related functions (`hints_enabled()`, `print_hint()`, ANSI constants) live in `utils.py`. Individual lifecycle scripts call these functions; they do not implement hint logic themselves.

**Alternatives considered:**
- Per-script hint strings — rejected because hint copy would drift across scripts with no central update point.
- Separate `hints.py` module — reasonable, but adds a module for ~30 lines of code; `utils.py` already serves as the shared stdlib, and the existing pattern is to keep shared utilities there.

**Consequences:** Any hint copy change requires touching only `utils.py`. New scripts that need hints import one function. The test surface for hint behavior is a single module.

---

### ADR-2: Tutorial as a standalone script (tutorial.py), not integrated into init.py

**Decision:** Tutorial logic lives in `tutorial.py`. `init.py` calls `tutorial.main()` after standard init completes. The `cicadas.py` CLI also registers `tutorial` as a direct subcommand.

**Alternatives considered:**
- Inline in init.py — rejected because init.py is already responsible for `.cicadas/` structure; mixing tutorial orchestration makes it harder to maintain and test each concern independently.
- Subagent/separate process — rejected; tutorial must call real Cicadas functions in-process to remain testable and to guarantee it reflects the current state of the scripts.

**Consequences:** Tutorial can be run standalone (`cicadas tutorial`) or via init. Each is independently testable. Tutorial stays current automatically because it imports and calls the real scripts.

---

### ADR-3: Hints are TTY-gated and suppressed on non-TTY stdout

**Decision:** `hints_enabled()` returns `False` when `sys.stdout.isatty()` is `False`, regardless of config. ANSI codes are never written to pipes, files, or CI environments.

**Alternatives considered:**
- Always write hints, strip ANSI in non-TTY — rejected because hint text in piped output would still pollute machine-readable output (e.g., scripts parsing `cicadas status`).
- Separate stderr for hints — considered; rejected because stderr is typically captured/suppressed in CI and mixed with error output, making it harder to distinguish. TTY gating is simpler and more predictable.

**Consequences:** Hints are invisible in CI, scripts, and pipes. This is the correct behavior — hints are human orientation, not machine output. Tutorial concept text (non-ANSI) still prints in non-TTY for documentation purposes.

---

### ADR-4: `hints` boolean in `.cicadas/config.json`, not a per-initiative flag

**Decision:** Hint suppression is stored as `hints: false` in `.cicadas/config.json` (the project-level config). This is per-project, not per-initiative or per-user.

**Rationale from Builder:** "allow toggling off at any time for a given initiative" — interpreted as per-project config, since config.json is the existing per-project store. A per-user global config would require a new `~/.cicadas/config.json` mechanism (out of scope).

**Alternatives considered:**
- Per-user `~/.cicadasrc` — post-MVP; would require new config discovery logic.
- Sentinel file `.cicadas/.no-hints` — rejected; JSON config is cleaner and already exists.
- Per-command `--no-hints` only (no persistent config) — insufficient; users want persistent suppression.

**Consequences:** `load_config()` already reads config.json; `hints_enabled()` just reads the `hints` key from the loaded config dict. Default when key is absent: `True`.

---

### ADR-5: Tutorial uses deterministic mock output (no real git artifacts)

**Decision:** Tutorial does not create real git branches, registry entries, or `.cicadas/` state. Each step prints pre-scripted output that exactly mirrors what real Cicadas commands produce, driven by a defined step sequence. Zero cleanup burden, zero state pollution.

**Alternatives considered:**
- Real artifacts with manual cleanup — rejected; leaves tutorial branches/registry entries indefinitely if user forgets to clean up; `status` shows tutorial noise.
- Real artifacts with auto-cleanup — considered; cleaner than manual but still touches git during the tutorial, which can fail in edge-case repo states (detached HEAD, dirty worktree, etc.).
- Ephemeral git worktree — over-engineered for a tutorial; worktrees have their own failure modes.

**Consequences:** Tutorial output is always consistent, correct, and current (mock strings are maintained alongside the real scripts). No git operations = no failure modes from repo state. Tutorial can run in any repo state, including a brand-new empty repo. Mock strings must be kept in sync with real script output — this is the primary maintenance cost; mitigated by co-locating mock strings with the scripts they mirror and by having a test that diffs mock vs. real output on a known input.

**Tutorial step sequence (7 steps matching canonical flow):**
1. **Start** — 💬 "Start an initiative called my-project"; mock: draft folder created
2. **Define specs** — explain agent-guided spec phase; no prompt needed; mock: spec summary
3. **Kickoff** — 💬 "Kickoff the initiative"; mock: `MOCK_KICKOFF`
4. **Build** — 💬 "Implement partition 1"; mock: `MOCK_BUILD`
5. **Complete partition** — 💬 "Code review and complete partition"; mock: `MOCK_CODE_REVIEW` + `MOCK_COMPLETE_PARTITION`
6. **PR** — 💬 "Create a PR"; mock: `MOCK_OPEN_PR`
7. **Complete** — 💬 "Complete the initiative"; mock: `MOCK_COMPLETE_INITIATIVE` → `_completion_screen()`

---

### ADR-6: Status next-step inference from registry state (no new state file)

**Decision:** `status.py` infers the next step by inspecting the existing `registry.json` state. No new state file or database is needed. Inference logic:

| Registry State | Inferred Next Step |
|---------------|-------------------|
| No `.cicadas/` | "Initialize Cicadas — tell your agent: 💬 'Initialize cicadas'" |
| `.cicadas/` exists, no initiatives | "Start your first initiative — tell your agent: 💬 'Start a new initiative called <name>'" |
| Initiative exists, no branches | "Create a feature branch — tell your agent: 💬 'Start a feature branch for <partition>'" |
| Branches exist, lifecycle present | Existing lifecycle-based "Next" (already implemented) |
| Branches exist, no lifecycle | "Implement on your feature branch — tell your agent: 💬 'Implement task 1'" |

**Alternatives considered:**
- New `state.json` tracking current lifecycle position — overkill; registry already has enough signal.
- Always require lifecycle.json for Next — rejected per FR-3.1; users without lifecycle.json are currently left without guidance.

**Consequences:** No new files. Status becomes self-orienting for users at any stage. Existing lifecycle-based Next is unchanged.

---

## Data Models

### Modified: `.cicadas/config.json`

**Existing structure:**
```json
{
  "project_name": "cicadas",
  "auto_worktrees": { ... }
}
```

**Additive change — new optional key:**
```json
{
  "project_name": "cicadas",
  "auto_worktrees": { ... },
  "hints": true
}
```

- `hints` (bool, optional): When `false`, suppresses all hint output. Default when absent: `true`.
- This is a purely additive change. Existing configs without the key behave as `hints: true`.
- `load_config()` already handles missing keys gracefully — no migration needed.

No other data model changes. Tutorial creates real `.cicadas/` artifacts using existing schemas (registry.json, active/, etc.) — no new schemas.

---

## API & Interface Design

### New: `utils.py` — Hint Subsystem

```python
# ANSI constants (only applied when TTY)
CYAN  = "\033[36m"
GREEN = "\033[32m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"

def hints_enabled(args: argparse.Namespace | None, config: dict) -> bool:
    """Return True if hint output should be printed.

    Priority:
    1. --no-hints flag on args → False
    2. config['hints'] == False → False
    3. not sys.stdout.isatty() → False
    4. Otherwise → True
    """

def print_hint(lines: list[str], args: argparse.Namespace | None = None, config: dict | None = None) -> None:
    """Print a formatted hint block if hints are enabled.

    Box format (66 chars wide):
    ╔══════════════════════════════════════════════════════════════╗
    ║  <line 1>                                                    ║
    ║  <line 2>                                                    ║
    ╚══════════════════════════════════════════════════════════════╝

    Lines are truncated to fit. Max 3 content lines enforced.
    Colors applied only when TTY.
    """

def print_tutorial_banner(step: int, total: int, title: str) -> None:
    """Print a tutorial step banner."""

def print_tutorial_checkmark(message: str) -> None:
    """Print a green checkmark confirmation line."""
```

---

### New: `tutorial.py`

```python
def main(args: argparse.Namespace) -> None:
    """Entry point for tutorial mode. Called by init.py and cicadas.py."""

def _run_step(step_num: int, total: int, title: str, concept: str,
              agent_prompt: str, mock_output: str) -> None:
    """Print banner + concept + agent prompt + deterministic mock output + checkmark, wait for Enter.
    
    No real scripts are called. mock_output is a pre-scripted string that mirrors
    real command output exactly. No git operations or filesystem changes occur.
    """

def _completion_screen() -> None:
    """Print the 'You're ready!' completion screen with next-step agent prompts."""

# Mock output strings — co-located with tutorial steps for easy maintenance
MOCK_KICKOFF = """[INFO] Promoting drafts for initiative: my-project...
[OK]   Created initiative branch: initiative/my-project
[INFO] Pushed initiative/my-project to remote."""

MOCK_BRANCH = """[OK]   Registered branch: feat/my-partition
[OK]   Created and pushed branch: feat/my-partition"""

MOCK_CODE_REVIEW = """Code Review — feat/my-partition
Verdict: PASS (Advisory)
  [OK] All tasks complete
  [OK] Acceptance criteria met
  [OK] No security issues detected"""

MOCK_COMPLETE_PARTITION = """[OK]   Recorded: feat/my-partition → index.json"""

MOCK_COMPLETE_INITIATIVE = """[INFO] Archiving initiative: my-project...
[OK]   Moved .cicadas/active/my-project → .cicadas/archive/20260509-my-project/
[OK]   Canon synthesized and committed."""
```

**The canonical 7-step flow — tutorial mirrors this exactly:**

| Step | Name | Agent Prompt | Mock String |
|------|------|-------------|-------------|
| 1 | **Start** | 💬 "Start an initiative called my-project" | `MOCK_START` |
| 2 | **Define specs** | *(Cicadas guides — no prompt; tutorial summarizes the spec phase)* | `MOCK_SPECS` |
| 3 | **Kickoff** | 💬 "Kickoff the initiative" | `MOCK_KICKOFF` |
| 4 | **Build** | 💬 "Implement partition 1" | `MOCK_BUILD` |
| 5 | **Complete partition** | 💬 "Code review and complete partition" | `MOCK_CODE_REVIEW` + `MOCK_COMPLETE_PARTITION` |
| 4-5 | *(note: repeat for each partition)* | | |
| 6 | **PR** | 💬 "Create a PR" | `MOCK_OPEN_PR` |
| 7 | **Complete** | 💬 "Complete the initiative" | `MOCK_COMPLETE_INITIATIVE` → `_completion_screen()` |

---

### Modified: `init.py`

```python
# New CLI flags:
# --tutorial        Run tutorial after init
# --no-tutorial     Skip tutorial prompt (standard init only)

def init_cicadas(root: Path, offer_tutorial: bool = True) -> None:
    # ... existing init logic unchanged ...
    if offer_tutorial and _is_first_run(root):
        _offer_tutorial(root)

def _is_first_run(root: Path) -> bool:
    """True if .cicadas/ was just created (not pre-existing)."""

def _offer_tutorial(root: Path) -> None:
    """Prompt user; if yes, call tutorial.main()."""
```

---

### Modified: `status.py`

```python
def _infer_next_step(registry: dict, cicadas_exists: bool) -> str | None:
    """Return a next-step hint string based on registry state, or None if lifecycle handles it."""
```

---

### Modified: Lifecycle scripts (kickoff.py, branch.py, archive.py, update_index.py, open_pr.py)

Each script's `main()` gains:
1. `--no-hints` argument added to its argparse parser.
2. A `print_hint(HINT_LINES, args, config)` call at the end of successful execution.

Hint content per command, aligned to the canonical 7-step flow:

| Command | Step it completes | Hint "Next:" line | Agent prompt shown |
|---------|------------------|------------------|-------------------|
| `init` (no tutorial) | — | "Start the initiative" | 💬 "Start an initiative called \<name\>" |
| `kickoff` | Step 3 | "Build your first partition" | 💬 "Implement partition \<name\>" |
| `branch` | Step 4 (start) | "Implement, then complete the partition" | 💬 "Code review and complete partition" |
| `update-index` | Step 5 | "Create a PR when all partitions are done" | 💬 "Create a PR" |
| `open-pr` | Step 6 | "Merge the PR, then complete the initiative" | 💬 "Complete the initiative" |
| `archive` | Step 7 | "You're done! Start your next initiative" | 💬 "Start an initiative called \<name\>" |

---

## Implementation Patterns & Conventions

### Hint call pattern (all lifecycle scripts)
```python
# At the end of main(), after all existing output:
config = load_config()
print_hint(
    [
        "Next: start your first feature branch",
        "Tell your agent:",
        '  💬 "Start a feature branch for <partition name>"',
    ],
    args=args,
    config=config,
)
```

### ANSI application pattern
```python
def _colorize(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text
```

Never apply ANSI codes outside `utils.py`. All scripts use `print_hint()` and `print_tutorial_banner()` — never raw escape codes.

### Tutorial step pattern
```python
_run_step(
    step_num=1, total=5,
    title="Draft & Kickoff",
    concept=(
        "Before any code is written, Cicadas requires a spec.\n"
        "Specs live in .cicadas/drafts/ until they're approved.\n"
        "Your agent creates and kicks off the initiative when you say:"
    ),
    agent_prompt='"Start a new initiative called hello-cicadas"',
    fn=kickoff.kickoff,
    "hello-cicadas",
    intent="My first tutorial initiative",
)
```

### Testing pattern
- All hint tests use `--no-hints` to verify suppression produces zero diff against baseline.
- Tutorial tests use `tempfile.mkdtemp()` + `git init` (existing base class pattern).
- TTY gating tested by patching `sys.stdout.isatty` to return `False`.
- No mocks for filesystem or git operations (existing project convention).

---

## Security & Performance

### Security
- **No new attack surface.** Hint strings are hardcoded in scripts, not read from user input or files.
- **Tutorial does not push to remote** (ADR-5). No network calls in tutorial path.
- Tutorial `hello-cicadas` draft stubs are pre-written strings — not read from any user-supplied file.

### Performance
- **Hint output overhead:** < 5ms (a few `print()` calls). Well within the < 50ms NFR.
- **Tutorial:** Interactive (user-paced). No latency constraint beyond normal `git branch` operations (~100ms).
- **`hints_enabled()`:** Pure in-memory dict lookup + `sys.stdout.isatty()` syscall. Negligible.
- **`_infer_next_step()`:** Pure dict inspection of already-loaded registry. Zero additional I/O.

---

## Implementation Sequence

### Phase 1 — Hint subsystem (foundation, no user-visible changes yet)
1. Add ANSI constants and `hints_enabled()` to `utils.py`
2. Add `print_hint()` and `print_tutorial_banner()` / `print_tutorial_checkmark()` to `utils.py`
3. Write `test_hints.py` — verify suppression via `--no-hints`, config, and TTY mock
4. Add `--no-hints` to `cicadas.py` common argument parser (or per-command)

*Unblocks: all other phases*

### Phase 2 — Lifecycle command hints (parallel with Phase 3)
5. Add `print_hint()` call to `kickoff.py`, `branch.py`, `archive.py`, `update_index.py`, `open_pr.py`
6. Add `--no-hints` to each script's argparse
7. Extend existing tests to assert hint output appears / is suppressed correctly

*Depends on: Phase 1*

### Phase 3 — Status next-step inference (parallel with Phase 2)
8. Add `_infer_next_step()` to `status.py`
9. Extend `test_status.py` with inferred next-step cases (no lifecycle, no branches, no .cicadas/)

*Depends on: Phase 1*

### Phase 4 — Tutorial script
10. Implement `tutorial.py` with all 5 steps
11. Modify `init.py` to add `--tutorial`/`--no-tutorial` flags and `_offer_tutorial()` prompt
12. Register `tutorial` subcommand in `cicadas.py`
13. Write `test_tutorial.py` — real artifact creation, idempotency check, completion screen

*Depends on: Phase 1, Phase 2 (for tutorial to show real hints)*

### Phase 5 — Documentation
14. Rewrite `README.md` getting-started section (full first cycle narrative)
15. Update `HOW-TO.md` with tutorial mode and hint toggle docs

*Depends on: Phase 4 (tutorial UX must be final before documenting it)*
