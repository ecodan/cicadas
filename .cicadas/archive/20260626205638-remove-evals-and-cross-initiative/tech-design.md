---
summary: "Pure deletion initiative. Two independent clusters: (1) scrub all LLMs-and-evals content from emergence markdown and SKILL.md, deleting eval-spec files; (2) remove get_registry_root() from utils.py, simplify get_registry_dir() to a one-liner, fix emit_event.py, drop two test cases, and update all project docs + bump to v1.0.0. No new abstractions. No data migration. No runtime behavior change for single-worktree users."
phase: "tech"
when_to_load:
  - "When implementing file edits or verifying scope during this initiative."
depends_on:
  - "technical-brief.md"
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
  - "pyproject.toml"
  - "release-notes.md"
index:
  overview: "## Overview & Context"
  stack: "## Tech Stack & Dependencies"
  structure: "## Project / Module Structure"
  adrs: "## Architecture Decisions (ADRs)"
  data_models: "## Data Models"
  interfaces: "## API & Interface Design"
  conventions: "## Implementation Patterns & Conventions"
  security_performance: "## Security & Performance"
  implementation_sequence: "## Implementation Sequence"
next_section: "Implementation Sequence"
---

# Tech Design: remove-evals-and-cross-initiative

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

This is a **deletion initiative** — no new code, no new abstractions. Two independent cleanup clusters:

**Cluster A — Evals removal**: The LLMs-and-evals question chain lives entirely in emergence markdown files and SKILL.md. No Python scripts read `building_on_ai` or `eval_status`, so this is a pure text-editing pass with file deletions. The `emergence-config.json` schema no longer needs those keys (existing files with them are inert — we don't need a migration, just stop writing them).

**Cluster B — `get_registry_root()` removal**: This function (28 lines in `utils.py`) navigates from a linked worktree back to the primary worktree so that `registry.json` and `events.jsonl` are read/written to the main-branch `.cicadas/`. It's called in two places: `get_registry_dir()` (one-liner in `utils.py`) and `emit_event.py` (one import + one path construction). Removing it means `get_registry_dir()` returns `get_project_root() / ".cicadas"` — i.e., the local `.cicadas/` of wherever you are. For single-worktree usage (the overwhelming common case) this is identical to today's behavior.

### Cross-Cutting Concerns

1. **No silent behavioral regression** — The `get_registry_dir()` simplification must produce exactly the same path as today for single-worktree repos. The test at `test_get_registry_dir_returns_cicadas_subdir` already covers this.
2. **No orphaned references** — Every file that mentions `get_registry_root`, `building_on_ai`, `eval_status`, or `eval-spec` must be updated or deleted. A grep gate in the acceptance criteria enforces this.
3. **Docs stay consistent with code** — `agents.md`, `docs/cicadas-method-general.md`, `README.md`, and `SKILL.md` describe the same system. All four must be updated in the same commit scope as the code changes.

### Brownfield Notes

- `utils.py` is imported by every Cicadas script. Removing a public function is a breaking change to any external caller. The major version bump (0.3.1 → 1.0.0) documents this.
- `test_utils.py` has a three-test class `TestGetRegistryRoot`. Two tests exercise `get_registry_root()` directly and must be deleted. The third (`test_get_registry_dir_returns_cicadas_subdir`) tests `get_registry_dir()` which we're keeping — rename the class to `TestGetRegistryDir` and keep that test.
- `emit_event.py` imports `get_registry_root` from utils. After removal, it must import `get_registry_dir` instead (already available; no new export needed).

---

## Tech Stack & Dependencies

| Category | Selection | Notes |
|---|---|---|
| Language | Python 3.11+ stdlib | No change |
| Markup | Markdown | Emergence/SKILL/doc files |
| Config | TOML (`pyproject.toml`) | Version bump only |
| Testing | `unittest` + real temp dirs | Existing pattern; no new dependencies |

**New dependencies introduced:** None.

**Dependencies removed:** None (eval-spec files are Markdown, not code).

---

## Project / Module Structure

Files deleted:

```
src/cicadas/emergence/eval-spec.md        # DELETED
src/cicadas/templates/eval-spec.md        # DELETED
```

Files modified (Cluster A — evals):

```
src/cicadas/emergence/start-flow.md       # [MODIFIED] Remove step 3; renumber steps 4–7 → 3–6; update scoping table + descriptions
src/cicadas/emergence/clarify.md          # [MODIFIED] Remove "LLMs and Evals?" from step 0 start-flow summary
src/cicadas/emergence/tweak.md            # [MODIFIED] Remove step 0d (LLMs and Evals) and LLM/Eval reminder block
src/cicadas/emergence/bug-fix.md          # [MODIFIED] Remove step 0d (LLMs and Evals) and LLM/Eval reminder block
src/cicadas/emergence/approach.md         # [MODIFIED] Remove step 3 eval-spec offer and eval placement question
src/cicadas/SKILL.md                      # [MODIFIED] Remove "LLMs and Evals" section; update start-flow description; remove get_registry_root/worktree-routing docs
```

Files modified (Cluster B — registry root + docs + version):

```
src/cicadas/scripts/utils.py              # [MODIFIED] Delete get_registry_root(); simplify get_registry_dir()
src/cicadas/scripts/emit_event.py         # [MODIFIED] Replace get_registry_root import+call with get_registry_dir
tests/test_utils.py                       # [MODIFIED] Delete TestGetRegistryRoot class; keep test_get_registry_dir_returns_cicadas_subdir in a renamed class TestGetRegistryDir
README.md                                 # [MODIFIED] Remove evals and cross-initiative registry mentions
agents.md                                 # [MODIFIED] Remove "Building on AI" / evals mention in src/cicadas/ description
docs/cicadas-method-general.md            # [MODIFIED] Remove Building on AI sentence (line ~162), eval status from emergence-config comment (line ~116), cross-initiative registry gap entry (line ~502)
release-notes.md                          # [MODIFIED] Add v1.0.0 section
pyproject.toml                            # [MODIFIED] version = "0.3.1" → "1.0.0"
```

**Key structural decisions:**
- Cluster A and Cluster B are independent — no ordering dependency between them. They can be implemented and reviewed as two separate feature branches or sequentially in one.
- `emergence-config.json` files on disk that contain `building_on_ai` or `eval_status` are **not touched** — those fields are simply ignored going forward. No migration script needed.

---

## Architecture Decisions (ADRs)

### ADR-1: Simplify `get_registry_dir()` to call `get_project_root()` directly

**Decision:** Replace `get_registry_dir()` body from `return get_registry_root() / ".cicadas"` to `return get_project_root() / ".cicadas"`. Delete `get_registry_root()` entirely.

**Rationale:** The primary-worktree routing was the only reason `get_registry_root()` existed. With that feature gone, the indirection adds no value. A direct call to `get_project_root()` is simpler, easier to test, and eliminates the silent fallback behavior.

**Affects:** `utils.py` (definition), `emit_event.py` (only other direct caller of `get_registry_root`).

---

### ADR-2: Fix `emit_event.py` by switching to `get_registry_dir()`

**Decision:** In `emit_event.py`, replace `from utils import get_registry_root, load_config` with `from utils import get_registry_dir, load_config`, and change the path construction from `get_registry_root() / ".cicadas" / "active" / ...` to `get_registry_dir() / "active" / ...`.

**Rationale:** `get_registry_dir()` is already the canonical way to get the `.cicadas/` path. Using it directly removes the duplicated `.cicadas` path segment and makes `emit_event.py` consistent with every other script.

**Affects:** `emit_event.py` only.

---

### ADR-3: Keep `test_get_registry_dir_returns_cicadas_subdir`, drop the two `get_registry_root` tests

**Decision:** Delete `TestGetRegistryRoot.test_primary_worktree_returns_self` and `TestGetRegistryRoot.test_linked_worktree_returns_primary`. Rename the class `TestGetRegistryRoot` → `TestGetRegistryDir` and keep `test_get_registry_dir_returns_cicadas_subdir`.

**Rationale:** The two deleted tests exercise a function that no longer exists. The kept test verifies the behavior of `get_registry_dir()`, which is still public API and worth covering. The rename removes the misleading class name.

**Affects:** `tests/test_utils.py`.

---

### ADR-4: Step-renumbering in `start-flow.md` — renumber, don't restructure

**Decision:** Remove step 3 ("LLMs and Evals?") and renumber the remaining steps in place: old steps 4–7 become new steps 3–6. Update the scoping table and the narrative descriptions (e.g., "then continue to step 4" → "then continue to step 3").

**Rationale:** The simplest and least error-prone edit. Renumbering is mechanical and reviewable line-by-line.

**Affects:** `start-flow.md` only; callers in `clarify.md`, `tweak.md`, `bug-fix.md` reference the step by name ("PR preference"), not by number, so they are unaffected by renumbering.

---

### ADR-5: Remove cross-initiative gap entry from `docs/cicadas-method-general.md`

**Decision:** Remove the gap table row at line ~502 (`X1: Signals are intra-initiative only: No formal mechanism for cross-initiative notifications`) and the future-vision paragraph at line ~533 referencing cross-initiative signal awareness. Leave the migration ordering gap (`B3`) as-is since it is about database migrations, not the Cicadas registry.

**Rationale:** The cross-initiative registry was the proposed mitigation for `X1`. We are not fixing it — we are deliberately removing the broken attempt. Keeping the gap entry would imply work is still planned; removing it reflects the decision that cross-initiative coordination is out of scope.

**Affects:** `docs/cicadas-method-general.md`.

---

## Data Models

**No new models.** No schema changes to `registry.json` or `index.json`.

**`emergence-config.json`**: `building_on_ai` and `eval_status` keys are no longer written by the start flow. Existing files containing them are not touched — they are inert. No migration.

---

## API & Interface Design

**Public API change (breaking):** `get_registry_root()` is removed from `utils.py`. This is the reason for the major version bump.

**`get_registry_dir()` signature is unchanged:**

```python
def get_registry_dir() -> Path:
    return get_project_root() / ".cicadas"
```

Callers that use `get_registry_dir()` (which is every script except `emit_event.py`) require no changes.

**No CLI command changes.** All `cicadas.py` subcommands remain identical.

---

## Implementation Patterns & Conventions

**Editing markdown files**: Make surgical edits — remove only the identified lines/sections. Do not reformat surrounding content or reflow paragraphs that don't change. This keeps diffs readable and review fast.

**Grep gate before closing each file**: After each edit, run `grep -n "eval_status\|building_on_ai\|eval.spec\|eval-spec\|get_registry_root" <file>` and confirm zero hits before moving on.

**Test run after Cluster B**: After removing `get_registry_root()` and updating `emit_event.py`, run the full test suite:
```bash
PYTHONPATH=src/cicadas/scripts:tests python3 -m unittest discover -s tests/
```
All tests must pass.

**No reformatting**: Do not run `ruff format` across files that only have content deletions — it introduces noise. Only run format if a Python edit produces a lint error.

---

## Security & Performance

No new attack surfaces. No performance-sensitive paths changed. The `get_registry_dir()` simplification is a pure performance improvement (one fewer function call and no filesystem I/O to detect the `.git` type).

---

## Implementation Sequence

These two clusters are **fully independent** — either order works.

### Cluster A: Evals removal (markdown only)

1. Delete `src/cicadas/emergence/eval-spec.md`
2. Delete `src/cicadas/templates/eval-spec.md`
3. Edit `start-flow.md` — remove step 3, renumber 4–7 → 3–6, update scoping table and descriptions
4. Edit `clarify.md` — update step 0 start-flow summary line (remove "LLMs and Evals?")
5. Edit `tweak.md` — remove step 0d and the LLM/Eval reminder block
6. Edit `bug-fix.md` — remove step 0d and the LLM/Eval reminder block
7. Edit `approach.md` — remove step 3 (eval-spec offer + eval placement)
8. Edit `SKILL.md` — remove "LLMs and Evals" section; update start-flow description in Emergence table and process description; remove `get_registry_root`/worktree-routing mentions

Grep gate after all of Cluster A:
```bash
grep -rn "eval_status\|building_on_ai\|eval.spec\|get_registry_root" src/cicadas/
```
Must return zero hits.

### Cluster B: Registry root removal + docs + version bump

1. Edit `utils.py` — delete `get_registry_root()` (lines 22–49); change `get_registry_dir()` body to `return get_project_root() / ".cicadas"`
2. Edit `emit_event.py` — update import; change `get_registry_root() / ".cicadas" / "active"` → `get_registry_dir() / "active"`
3. Edit `tests/test_utils.py` — rename class `TestGetRegistryRoot` → `TestGetRegistryDir`; delete `test_primary_worktree_returns_self` and `test_linked_worktree_returns_primary`; keep `test_get_registry_dir_returns_cicadas_subdir`
4. Run full test suite — all must pass
5. Edit `agents.md` — remove "Building on AI — gate and eval status in start flow, optional eval spec for initiatives, eval/benchmark reminder for tweaks/bugs" from the `src/cicadas/` description
6. Edit `docs/cicadas-method-general.md` — remove eval status from emergence-config.json comment (~line 116); remove Building on AI sentence (~line 162); remove gap entry X1 (~line 502) and cross-initiative future-vision paragraph (~line 533)
7. Edit `README.md` — remove any evals/cross-initiative registry mentions (audit by grep)
8. Edit `pyproject.toml` — bump `version = "0.3.1"` → `version = "1.0.0"`
9. Edit `release-notes.md` — prepend a `## v1.0.0` section

**Parallel work opportunities:** Cluster A and Cluster B can be worked simultaneously by separate agents/branches.

**Known risks:** None — all changes are additive deletes with no runtime branching or migration logic.
