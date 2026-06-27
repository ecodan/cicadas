---
summary: "Remove the LLMs-and-evals question chain from the Cicadas start flow and all related emergence modules, templates, and SKILL.md documentation; remove get_registry_root() — the primary-worktree routing function that was supposed to share registry.json across linked worktrees but never worked reliably — simplifying all registry I/O to use get_project_root() / .cicadas instead; update all project documentation (README, agents.md, docs/, SKILL.md) to reflect these removals; and bump the major version."
phase: "clarify"
when_to_load:
  - "When defining scope, affected modules, or acceptance criteria for this removal initiative."
depends_on: []
modules:
  - "src/cicadas/emergence/"
  - "src/cicadas/templates/eval-spec.md"
  - "src/cicadas/SKILL.md"
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/emit_event.py"
  - "tests/test_utils.py"
  - "README.md"
  - "agents.md"
  - "docs/"
  - "release-notes.md"
  - "pyproject.toml"
index:
  problem: "## Problem Statement"
  goals_non_goals: "## Goals and Non-Goals"
  affected_modules: "## Affected Modules"
  users_operators: "## Users and Operators Affected"
  success_criteria: "## Success Criteria"
  requirements: "## Functional Requirements and Acceptance Criteria"
  risks_rollback: "## Risks and Rollback"
  observability_testing: "## Observability and Testing Expectations"
  open_questions: "## Open Questions"
next_section: "Open Questions"
---

# Technical Brief: remove-evals-and-cross-initiative

## Progress

- [x] Problem Statement
- [x] Goals and Non-Goals
- [x] Affected Modules
- [x] Users and Operators Affected
- [x] Success Criteria
- [x] Functional Requirements and Acceptance Criteria
- [x] Risks and Rollback
- [x] Observability and Testing Expectations
- [x] Open Questions

## Problem Statement

Cicadas has two mechanisms that are dead weight:

1. **Evals question chain**: Every initiative, tweak, and bug start flow asks "Will this be powered by LLMs and may require ML evals?" and optionally follows up with eval status. This produces `building_on_ai` and `eval_status` fields in `emergence-config.json`. In practice no Python scripts read these fields — they exist only to gate emergence prompt behavior that almost never fires. The eval-spec module (`eval-spec.md`) and its template add further complexity for a workflow nobody uses. The overhead of the question adds friction to every single kickoff with no payoff.

2. **Cross-initiative registry routing (`get_registry_root()`)**: `get_registry_root()` navigates from a linked worktree back to the primary worktree so that `registry.json` and `index.json` are always read/written from the main-branch `.cicadas/` directory — theoretically allowing parallel worktrees to share a live registry without committing. In practice this doesn't work: the primary worktree path is filesystem-specific, breaks across machines, and the in-place shared-file approach is not a reliable cross-initiative coordination mechanism. The function adds complexity and a silent failure mode (falls back to `get_project_root()` on any error, so callers can't tell whether routing succeeded).

## Goals and Non-Goals

### Goals

- Remove the LLMs-and-evals question (step 3) from `start-flow.md` entirely, including all follow-up (eval status, `building_on_ai`/`eval_status` writes to `emergence-config.json`).
- Remove evals-related content from `clarify.md`, `tweak.md`, `bug-fix.md`, `approach.md`, and `SKILL.md`.
- Delete `src/cicadas/emergence/eval-spec.md` and `src/cicadas/templates/eval-spec.md`.
- Remove `get_registry_root()` from `utils.py` and simplify `get_registry_dir()` to `return get_project_root() / ".cicadas"`.
- Fix `emit_event.py` to stop calling `get_registry_root()` directly.
- Delete the two tests in `test_utils.py` that cover `get_registry_root()`.
- Remove all documentation of `get_registry_root()` and the evals workflow from `SKILL.md` and `canon/summary.md`.

### Non-Goals

- Changing any other aspect of the start flow or emergence process.
- Removing `registry.json`, `index.json`, or the scripts that use them — the registry itself stays; only the primary-worktree routing is removed.
- Removing the signals mechanism inside `registry.json` per initiative (this is intra-initiative, not cross-initiative).
- Removing `building_on_ai` from `skill_publish.py` test fixture — that test is testing something unrelated (the key happens to appear in a mock config).

## Affected Modules

| Module / Path | Expected Change | Notes |
|---|---|---|
| `src/cicadas/emergence/start-flow.md` | Remove step 3 (LLMs & Evals) and update step numbering/scoping table | Core change |
| `src/cicadas/emergence/clarify.md` | Remove evals references in step 0 and initiative-specific additions | |
| `src/cicadas/emergence/tweak.md` | Remove evals references | |
| `src/cicadas/emergence/bug-fix.md` | Remove evals references | |
| `src/cicadas/emergence/approach.md` | Remove eval placement question (before build / in parallel) | |
| `src/cicadas/emergence/eval-spec.md` | Delete file | |
| `src/cicadas/templates/eval-spec.md` | Delete file | |
| `src/cicadas/SKILL.md` | Remove "LLMs and Evals" section; remove `get_registry_root` / worktree-routing documentation; update CLI quick ref to remove `get_registry_root`-related notes | |
| `src/cicadas/scripts/utils.py` | Remove `get_registry_root()`; simplify `get_registry_dir()` | Two callers: `get_registry_dir()` itself and `emit_event.py` |
| `src/cicadas/scripts/emit_event.py` | Replace `get_registry_root()` call with `get_registry_dir()` | Already imports from utils |
| `tests/test_utils.py` | Remove two `get_registry_root` tests | Lines ~159 and ~169 |
| `README.md` | Remove evals and cross-initiative registry mentions | |
| `agents.md` | Remove evals and cross-initiative registry mentions | |
| `docs/cicadas-method-general.md` | Remove evals and cross-initiative registry mentions | |
| `docs/sdd-comparison.md` | Remove evals and cross-initiative registry mentions if present | |
| `release-notes.md` | Add entry for v1.0.0 | |
| `pyproject.toml` | Bump version `0.3.1` → `1.0.0` | Major version — breaking removal of public API (get_registry_root) and user-facing evals flow |

## Users and Operators Affected

| Operator / User | Impact |
|---|---|
| Builder starting an initiative/tweak/bug | No longer asked the LLMs & Evals question — one fewer interruption per kickoff |
| Agent running start-flow | Simpler flow; no `building_on_ai`/`eval_status` writes |
| Agent using `get_registry_dir()` | Gets `get_project_root() / .cicadas` directly; no hidden worktree routing |
| Linked-worktree users | Existing behavior was unreliable; now it's explicit: each worktree reads its local `.cicadas/` |

## Success Criteria

- `start-flow.md` has no mention of LLMs, evals, `building_on_ai`, or `eval_status`.
- `eval-spec.md` (emergence module and template) no longer exist.
- `get_registry_root()` does not exist in `utils.py`; `get_registry_dir()` calls `get_project_root()` directly.
- `emit_event.py` does not import or call `get_registry_root()`.
- All tests pass with no references to `get_registry_root` in test files.
- `SKILL.md` contains no mention of `get_registry_root`, worktree-routing, or the evals question chain.
- `README.md`, `agents.md`, and `docs/` contain no references to the removed evals flow or `get_registry_root`.
- `pyproject.toml` version is `1.0.0`.
- `release-notes.md` has a `## v1.0.0` entry.

## Functional Requirements and Acceptance Criteria

### FR-1: Remove evals question from start flow

- **Requirement:** `start-flow.md` must not include the LLMs-and-evals step (currently step 3). The draft folder creation step and requirements/pace/PR-preference steps remain. Step numbering must be updated.
- **Acceptance criteria:**
  - `start-flow.md` contains no text matching `building_on_ai`, `eval_status`, `LLMs and Evals`, or `eval`.
  - The scoping table no longer has an "LLMs and Evals?" row.

### FR-2: Remove evals from emergence modules and SKILL.md

- **Requirement:** All emergence modules and SKILL.md must be free of eval-spec references and the evals workflow description.
- **Acceptance criteria:**
  - `clarify.md`, `tweak.md`, `bug-fix.md`, `approach.md` contain no references to `eval_status`, `building_on_ai`, eval-spec, or eval placement.
  - `SKILL.md` "LLMs and Evals" section is removed; the process table and start-flow description no longer mention the evals question.

### FR-3: Delete eval-spec files

- **Requirement:** Remove `src/cicadas/emergence/eval-spec.md` and `src/cicadas/templates/eval-spec.md`.
- **Acceptance criteria:**
  - Neither file exists on the branch after this change.
  - No other file imports or references either path (beyond a mention in a "removed" git commit message).

### FR-4: Remove get_registry_root() and simplify get_registry_dir()

- **Requirement:** `get_registry_root()` must be deleted. `get_registry_dir()` must return `get_project_root() / ".cicadas"` directly.
- **Acceptance criteria:**
  - `grep -rn "get_registry_root" src/` returns no results.
  - `get_registry_dir()` is a one-liner calling `get_project_root()`.

### FR-5: Fix emit_event.py

- **Requirement:** `emit_event.py` must not import or call `get_registry_root()`.
- **Acceptance criteria:**
  - `grep "get_registry_root" src/cicadas/scripts/emit_event.py` returns no results.
  - `cicadas emit-event` still writes to the correct `events.jsonl` path.

### FR-6: Remove get_registry_root tests

- **Requirement:** The two `get_registry_root` tests in `test_utils.py` (~lines 159, 169) must be deleted.
- **Acceptance criteria:**
  - `grep "get_registry_root" tests/` returns no results.
  - Full test suite passes.

### FR-7: Update project documentation

- **Requirement:** `README.md`, `agents.md`, `docs/cicadas-method-general.md`, and any other docs files must not reference the evals question flow or `get_registry_root` / cross-initiative registry routing. `release-notes.md` must have a v1.0.0 entry summarizing the removals.
- **Acceptance criteria:**
  - `grep -rn "eval_status\|building_on_ai\|get_registry_root\|cross-initiative registry\|LLMs and Evals" README.md agents.md docs/` returns no results.
  - `release-notes.md` contains a `## v1.0.0` section.

### FR-8: Major version bump

- **Requirement:** `pyproject.toml` version must be updated from `0.3.1` to `1.0.0`.
- **Acceptance criteria:**
  - `grep "^version" pyproject.toml` returns `version = "1.0.0"`.

## Risks and Rollback

| Risk | Likelihood | Impact | Mitigation | Rollback |
|---|---|---|---|---|
| Linked-worktree users relied on primary-worktree routing for registry sharing | Low | Medium | The routing was already unreliable (silent fallback); removing it makes local-only behavior explicit | `git revert` the commit |
| Missed evals reference in an emergence file | Low | Low | Grep all `src/cicadas/emergence/` and `SKILL.md` for `eval` before closing | Fix as a follow-up tweak |
| `emit_event.py` path change breaks event log path | Low | High | Use `get_registry_dir()` (already equivalent in non-worktree case) and add/update test | Revert the emit_event.py change |

## Observability and Testing Expectations

- **Observability:** No runtime metrics; correctness is verified by grep (no forbidden symbols remain) and the test suite.
- **Tests:** Delete `get_registry_root` tests in `test_utils.py`. Verify remaining test suite passes clean. If `emit_event.py` path change needs coverage, add a test that `get_events` reads what `emit_event` writes.
- **Manual verification:** Run `cicadas status` and `cicadas signal "test"` from a non-worktree checkout to confirm registry I/O still works.

## Open Questions

- None.
