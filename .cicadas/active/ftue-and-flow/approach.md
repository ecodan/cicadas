---
summary: "ftue-and-flow is implemented in 4 sequential partitions: (1) hints subsystem foundation in utils.py, (2) lifecycle command hints + status inference in parallel, (3) tutorial script, (4) documentation rewrite. P1 is the critical unblocking dependency; P2a and P2b can run in parallel; P3 and P4 depend on P2."
phase: "approach"
when_to_load:
  - "When starting registered feature branches or reviewing partition scope, sequencing, and dependencies."
  - "When deciding what work can proceed in parallel and what must wait."
depends_on:
  - "prd.md"
  - "ux.md"
  - "tech-design.md"
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
  strategy: "## Strategy"
  partitions: "## Partitions (Feature Branches)"
  sequencing: "## Sequencing"
  migrations_compat: "## Migrations & Compat"
  risks: "## Risks & Mitigations"
  alternatives: "## Alternatives Considered"
next_section: "Strategy"
---

# Approach: ftue-and-flow

## Strategy

Sequential-then-parallel. The hints subsystem (P1) is the foundational layer that all other partitions depend on — it must land first. Once P1 is merged, lifecycle hints (P2a) and status inference (P2b) can proceed in parallel since they touch disjoint modules. The tutorial (P3) depends on both P2 partitions being complete so it can show realistic hint output in its mock steps. Documentation (P4) is the final partition and depends on tutorial UX being finalized.

The initiative uses a single PR at completion (initiative PR only), per lifecycle.json.

---

## Partitions (Feature Branches)

### Partition 1: Hints Subsystem → `feat/hints-subsystem`

**Modules**: `src/cicadas/scripts/utils.py`, `src/cicadas/scripts/cicadas.py`, `tests/test_hints.py`
**Scope**: Add all hint infrastructure to `utils.py`: ANSI constants, `hints_enabled()`, `print_hint()`, `print_tutorial_banner()`, `print_tutorial_checkmark()`. Add `--no-hints` to the common argparse setup in `cicadas.py`. Write `test_hints.py`.
**Dependencies**: None — first partition.

#### Artifact Type
`cli`

#### How to Run
- No persistent process. Run tests: `pytest tests/test_hints.py -v`

#### Acceptance Criteria
- [ ] `hints_enabled(args_with_no_hints, {})` returns `False`
- [ ] `hints_enabled(None, {"hints": False})` returns `False`
- [ ] `hints_enabled(None, {})` returns `False` when `sys.stdout.isatty()` is patched to return `False`
- [ ] `hints_enabled(None, {})` returns `True` when `sys.stdout.isatty()` returns `True` and config has no `hints` key
- [ ] `print_hint(["Next: do X", "Tell your agent: ..."], args=no_hints_args)` prints nothing
- [ ] `print_hint(["Next: do X"], args=None, config={})` prints nothing when not TTY (isatty patched False)
- [ ] `print_hint(["Next: do X"], args=None, config={"hints": True})` prints the box when TTY
- [ ] Box output is exactly 66 chars wide (including border chars)
- [ ] All existing tests pass unchanged

#### Implementation Steps
1. Add ANSI constants to `utils.py`
2. Implement `hints_enabled()` in `utils.py`
3. Implement `print_hint()` in `utils.py` with 66-char box format
4. Implement `print_tutorial_banner()` and `print_tutorial_checkmark()` in `utils.py`
5. Add `--no-hints` to common argparse in `cicadas.py`
6. Write `tests/test_hints.py` covering all acceptance criteria above

---

### Partition 2a: Lifecycle Command Hints → `feat/lifecycle-hints`

**Modules**: `src/cicadas/scripts/kickoff.py`, `src/cicadas/scripts/branch.py`, `src/cicadas/scripts/archive.py`, `src/cicadas/scripts/update_index.py`, `src/cicadas/scripts/open_pr.py`, `src/cicadas/scripts/init.py`
**Scope**: Add `print_hint()` call at end of each lifecycle command's `main()`. Add `--no-hints` to each script's argparse. Extend existing tests to assert hint output appears / is suppressed.
**Dependencies**: Requires `feat/hints-subsystem` (P1).

#### Artifact Type
`cli`

#### How to Run
- No persistent process. Run tests: `pytest tests/ -v -k "kickoff or branch or archive or update_index or open_pr or init"`

#### Acceptance Criteria
- [ ] `cicadas kickoff <name>` prints a hint block ending with a 💬 agent prompt after existing output
- [ ] `cicadas kickoff <name> --no-hints` prints zero hint output (existing output unchanged)
- [ ] `cicadas branch <name>` prints a hint block with implement + PR agent prompts
- [ ] `cicadas branch <name> --no-hints` prints zero hint output
- [ ] `cicadas archive <name>` prints a hint block pointing to canon synthesis
- [ ] `cicadas update-index` prints a hint block pointing to PR or merge
- [ ] `cicadas open-pr` prints a hint block pointing to PR review
- [ ] `cicadas init` (no tutorial) prints a hint block pointing to first initiative
- [ ] With `hints: false` in config.json, all commands print zero hint output
- [ ] All existing tests for these commands pass unchanged (hint suppressed by default in test harness via `--no-hints` or non-TTY environment)

#### Implementation Steps
1. Add `print_hint()` call + `--no-hints` arg to `kickoff.py`
2. Add `print_hint()` call + `--no-hints` arg to `branch.py`
3. Add `print_hint()` call + `--no-hints` arg to `archive.py`
4. Add `print_hint()` call + `--no-hints` arg to `update_index.py`
5. Add `print_hint()` call + `--no-hints` arg to `open_pr.py`
6. Add `print_hint()` call + `--no-hints` arg to `init.py`
7. Update existing tests to verify hint presence/absence

---

### Partition 2b: Status Next-Step Inference → `feat/status-next-step`

**Modules**: `src/cicadas/scripts/status.py`, `tests/test_status.py` (or new `tests/test_status_next_step.py`)
**Scope**: Add `_infer_next_step()` to `status.py`. Emit a `print_hint()` block in all status output paths, including when no `.cicadas/` exists and when no initiatives are registered.
**Dependencies**: Requires `feat/hints-subsystem` (P1). Independent of P2a.

#### Artifact Type
`cli`

#### How to Run
- No persistent process. Run tests: `pytest tests/test_status.py -v`

#### Acceptance Criteria
- [ ] `cicadas status` with no `.cicadas/` prints a hint: "Initialize Cicadas" + 💬 "Initialize cicadas"
- [ ] `cicadas status` with `.cicadas/` but no initiatives prints a hint: "Start your first initiative" + 💬 "Start a new initiative called <name>"
- [ ] `cicadas status` with initiative but no branches prints a hint: "Create a feature branch" + 💬 "Start a feature branch for <partition>"
- [ ] `cicadas status` with branches but no lifecycle prints a hint: "Implement on your feature branch" + 💬 "Implement task 1"
- [ ] `cicadas status` with lifecycle present uses existing lifecycle Next (unchanged)
- [ ] `cicadas status --no-hints` prints zero hint output in all cases
- [ ] All existing `test_status.py` tests pass unchanged

#### Implementation Steps
1. Add `_infer_next_step(registry, cicadas_exists)` to `status.py`
2. Wire `_infer_next_step()` into the status output paths
3. Add `print_hint()` call using inferred step
4. Handle the no-`.cicadas/` case (currently likely an error or empty output)
5. Add new test cases to `test_status.py` for each inference scenario

---

### Partition 3: Tutorial Script → `feat/tutorial`

**Modules**: `src/cicadas/scripts/tutorial.py` (new), `src/cicadas/scripts/init.py`, `src/cicadas/scripts/cicadas.py`, `tests/test_tutorial.py` (new)
**Scope**: Implement `tutorial.py` with 6 deterministic mock steps (Clarify → Kickoff → Implement partition → Code review → Complete partition → Complete initiative). Add `--tutorial`/`--no-tutorial` to `init.py`. Register `tutorial` subcommand in `cicadas.py`. Write `test_tutorial.py`.
**Dependencies**: Requires `feat/hints-subsystem` (P1) and `feat/lifecycle-hints` (P2a) — tutorial must show the same hint format as real commands.

#### Artifact Type
`cli`

#### How to Run
- No persistent process. Run tests: `pytest tests/test_tutorial.py -v`
- Manual run: `python src/cicadas/scripts/cicadas.py tutorial` (or `cicadas init --tutorial`)

#### Acceptance Criteria
- [ ] `cicadas tutorial` prints all 6 step banners in order
- [ ] Each step shows: banner → concept text → 💬 agent prompt → mock output → checkmark → "Press Enter"
- [ ] Mock output for each step matches the exact format of real Cicadas commands (verified by snapshot test)
- [ ] `cicadas init` on a new repo (no existing `.cicadas/`) offers the tutorial prompt
- [ ] `cicadas init --tutorial` skips the prompt and runs tutorial directly
- [ ] `cicadas init --no-tutorial` skips the prompt and runs standard init only
- [ ] Running `cicadas tutorial` makes zero changes to git state or `.cicadas/` (no branches, no registry changes)
- [ ] `cicadas tutorial` completes successfully in a bare git repo with no commits
- [ ] Completion screen shows "You're ready!" + correct next-step agent prompts
- [ ] All existing `test_init.py` tests pass unchanged

#### Implementation Steps
1. Create `tutorial.py` with `main()`, `_run_step()`, `_completion_screen()`, and all 6 MOCK_* strings
2. Implement each of the 6 tutorial steps with concept text and agent prompts
3. Modify `init.py`: add `--tutorial`/`--no-tutorial` flags, `_is_first_run()`, `_offer_tutorial()`
4. Register `tutorial` subcommand in `cicadas.py`
5. Write `test_tutorial.py`: step sequence, no-state-change assertion, first-run prompt, flag behavior

---

### Partition 4: Documentation → `feat/docs-rewrite`

**Modules**: `README.md`, `HOW-TO.md`
**Scope**: Rewrite `README.md` getting-started section with full first-cycle narrative and copy-paste commands (as agent prompts). Update `HOW-TO.md` to document tutorial mode and hint toggle.
**Dependencies**: Requires `feat/tutorial` (P3) — tutorial UX must be final before documenting it.

#### Artifact Type
`library` <!-- documentation only, no runnable artifact -->

#### How to Run
- No runnable artifact. Review by reading the updated files.

#### Acceptance Criteria
- [ ] `README.md` contains a "Getting Started" section covering: install → init → first initiative → kickoff → branch → implement → PR → merge <!-- NEEDS MANUAL REVIEW -->
- [ ] Every step in the getting-started section uses a 💬 agent prompt, not a raw CLI command <!-- NEEDS MANUAL REVIEW -->
- [ ] `HOW-TO.md` documents how to run the tutorial (`cicadas init --tutorial` or 💬 "Run the tutorial") <!-- NEEDS MANUAL REVIEW -->
- [ ] `HOW-TO.md` documents how to disable hints (`hints: false` in `.cicadas/config.json`) <!-- NEEDS MANUAL REVIEW -->
- [ ] No existing HOW-TO sections are removed or broken <!-- NEEDS MANUAL REVIEW -->

#### Implementation Steps
1. Rewrite `README.md` getting-started section (full first cycle, agent prompts throughout)
2. Add tutorial and hint toggle documentation to `HOW-TO.md`
3. Review for consistency with actual tutorial step content from P3

---

## Sequencing

P1 must land first. P2a and P2b are independent of each other and can run in parallel. P3 depends on both P2 partitions. P4 depends on P3.

```
P1: hints-subsystem
    ├── P2a: lifecycle-hints  ─┐
    └── P2b: status-next-step ─┤
                               ├── P3: tutorial
                                       └── P4: docs-rewrite
```

### Partitions DAG

```yaml partitions
- name: feat/hints-subsystem
  modules: [src/cicadas/scripts/utils.py, src/cicadas/scripts/cicadas.py, tests/test_hints.py]
  depends_on: []

- name: feat/lifecycle-hints
  modules: [src/cicadas/scripts/kickoff.py, src/cicadas/scripts/branch.py, src/cicadas/scripts/archive.py, src/cicadas/scripts/update_index.py, src/cicadas/scripts/open_pr.py, src/cicadas/scripts/init.py]
  depends_on: [feat/hints-subsystem]

- name: feat/status-next-step
  modules: [src/cicadas/scripts/status.py, tests/test_status.py]
  depends_on: [feat/hints-subsystem]

- name: feat/tutorial
  modules: [src/cicadas/scripts/tutorial.py, src/cicadas/scripts/init.py, src/cicadas/scripts/cicadas.py, tests/test_tutorial.py]
  depends_on: [feat/lifecycle-hints, feat/status-next-step]

- name: feat/docs-rewrite
  modules: [README.md, HOW-TO.md]
  depends_on: [feat/tutorial]
```

---

## Migrations & Compat

- **`config.json`**: Adding optional `hints` boolean key. No migration — absence defaults to `true`. Existing configs are unaffected.
- **Existing CLI output**: All changes are strictly additive. No existing output is removed or reformatted. All existing tests remain valid; hint output is suppressed in test environments (non-TTY) without any test changes.
- **Existing scripts**: All modified scripts remain backward-compatible. `--no-hints` is an optional flag; omitting it preserves current behavior.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Existing tests break due to unexpected hint output | Hints are TTY-gated; test environments are non-TTY by default. Verify in test_hints.py with explicit isatty patch. |
| Mock tutorial output drifts from real command output | Co-locate MOCK_* strings with tutorial steps; write a snapshot test that diffs mock vs. real output on a known invocation. |
| `init.py` tutorial prompt interferes with automated `cicadas init` usage in scripts | `--no-tutorial` flag; tutorial prompt only shown when `_is_first_run()` is True (first time `.cicadas/` is created). |
| P2a and P2b merge conflicts on shared files | No shared files: P2a touches lifecycle scripts, P2b touches only `status.py`. Zero overlap. |
| `print_hint()` adds latency to CI pipelines | Hints are TTY-gated and never run in non-TTY environments. Zero CI impact. |

---

## Alternatives Considered

- **Single monolithic partition** — rejected; the hints subsystem, lifecycle changes, tutorial, and docs are independently testable and have a natural dependency graph. Splitting allows P2a and P2b to run in parallel and isolates risk.
- **Tutorial as a separate CLI tool** — rejected; keeping it as a `cicadas tutorial` subcommand is more discoverable and consistent with the existing CLI surface.
- **Docs-first approach** — rejected; documentation should reflect the final implemented behavior, not lead it. P4 correctly depends on P3.
