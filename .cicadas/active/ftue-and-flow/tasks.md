---
summary: "ftue-and-flow tasks are organized across 4 sequential partitions: P1 (hints subsystem foundation), P2a (lifecycle command hints) + P2b (status inference) in parallel, P3 (tutorial script), P4 (docs rewrite). Single initiative PR at completion. Feature Mode on existing Cicadas CLI codebase."
phase: "tasks"
when_to_load:
  - "When selecting the next implementation task or reviewing completion state."
  - "When checking partition progress, PR boundaries, or execution sequencing."
depends_on:
  - "prd.md"
  - "ux.md"
  - "tech-design.md"
  - "approach.md"
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
  partition_p1: "## Partition: feat/hints-subsystem"
  partition_p2a: "## Partition: feat/lifecycle-hints"
  partition_p2b: "## Partition: feat/status-next-step"
  partition_p3: "## Partition: feat/tutorial"
  partition_p4: "## Partition: feat/docs-rewrite"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/hints-subsystem"
---

# Tasks: ftue-and-flow

<!-- P1 must land before P2a and P2b. P2a and P2b are parallel. P3 depends on both P2s. P4 depends on P3. -->
<!-- No feature PRs (lifecycle.json features: false). Single initiative PR at the end. -->

---

## Partition: feat/hints-subsystem

> **Foundation layer.** All other partitions depend on this one.

- [x] Add ANSI color constants (`CYAN`, `GREEN`, `BOLD`, `DIM`, `RESET`) to `utils.py` <!-- id: 1 -->
- [x] Implement `_colorize(text, code)` helper in `utils.py` — applies code only when `sys.stdout.isatty()` <!-- id: 2 -->
- [x] Implement `hints_enabled(args, config)` in `utils.py` — priority: `--no-hints` flag → `config['hints'] == False` → not TTY → True <!-- id: 3 -->
- [x] Implement `print_hint(lines, args, config)` in `utils.py` — 66-char box with `╔══╗` / `║` / `╚══╝` border, cyan when TTY, no output when hints disabled <!-- id: 4 -->
- [x] Implement `print_tutorial_banner(step, total, title)` in `utils.py` — bold white `━━━` divider, step number in cyan <!-- id: 5 -->
- [x] Implement `print_tutorial_checkmark(message)` in `utils.py` — green `✓` prefix <!-- id: 6 -->
- [x] Add `--no-hints` global argument to the common argparse setup in `cicadas.py` <!-- id: 7 --> [Note: --no-hints handled per-script, not in cicadas.py, due to subprocess forwarding architecture]
- [x] Write `tests/test_hints.py`: <!-- id: 8 -->
  - `hints_enabled()` returns False for `--no-hints` flag
  - `hints_enabled()` returns False for `config['hints'] == False`
  - `hints_enabled()` returns False when `sys.stdout.isatty()` patched to False
  - `hints_enabled()` returns True when TTY and no suppression
  - `print_hint()` produces zero output when hints disabled
  - `print_hint()` box is exactly 66 chars wide when hints enabled (patch isatty=True)
  - `print_hint()` strips ANSI when not TTY (patch isatty=False, hints=True via config — no output)
- [x] Verify all existing tests pass unchanged <!-- id: 9 --> [338 passed, 1 skipped]

---

## Partition: feat/lifecycle-hints

> **Parallel with feat/status-next-step.** Depends on feat/hints-subsystem.

- [ ] Add `--no-hints` arg and `print_hint()` call to `kickoff.py` — hint points to Step 4: 💬 "Implement partition \<name\>" <!-- id: 20 -->
- [ ] Add `--no-hints` arg and `print_hint()` call to `branch.py` — hint points to Step 5: 💬 "Code review and complete partition" <!-- id: 21 -->
- [ ] Add `--no-hints` arg and `print_hint()` call to `update_index.py` — hint points to Step 6: 💬 "Create a PR" <!-- id: 22 -->
- [ ] Add `--no-hints` arg and `print_hint()` call to `open_pr.py` — hint points to Step 7: 💬 "Complete the initiative" <!-- id: 23 -->
- [ ] Add `--no-hints` arg and `print_hint()` call to `archive.py` — hint points to starting next initiative: 💬 "Start an initiative called \<name\>" <!-- id: 24 -->
- [ ] Add `--no-hints` arg and `print_hint()` call to `init.py` (non-tutorial path) — hint points to Step 1: 💬 "Start an initiative called \<name\>" <!-- id: 25 -->
- [ ] Extend `tests/test_kickoff.py`: assert hint block present in TTY-patched output; assert zero hint output with `--no-hints` <!-- id: 26 -->
- [ ] Extend `tests/test_branch.py`: assert hint block present; assert suppressed with `--no-hints` <!-- id: 27 -->
- [ ] Extend existing tests for `archive`, `update_index`, `open_pr`, `init`: assert hint present / suppressed <!-- id: 28 -->
- [ ] Verify all existing tests for modified scripts pass unchanged (non-TTY env suppresses hints automatically) <!-- id: 29 -->

---

## Partition: feat/status-next-step

> **Parallel with feat/lifecycle-hints.** Depends on feat/hints-subsystem.

- [ ] Add `_infer_next_step(registry, cicadas_exists)` to `status.py` — returns hint lines based on registry state: <!-- id: 40 -->
  - No `.cicadas/`: "Initialize Cicadas" → 💬 "Initialize cicadas"
  - `.cicadas/` exists, no initiatives: "Start your first initiative" → 💬 "Start an initiative called \<name\>"
  - Initiative exists, no branches: "Build your first partition" → 💬 "Implement partition \<name\>"
  - Branches exist, no lifecycle: "Complete the partition" → 💬 "Code review and complete partition"
  - Lifecycle present: existing Next step (unchanged)
- [ ] Wire `_infer_next_step()` into `status.py` output — call `print_hint()` with inferred lines after existing status output <!-- id: 41 -->
- [ ] Handle the no-`.cicadas/` case gracefully in `status.py` — currently may error; should print friendly message + hint <!-- id: 42 -->
- [ ] Add `--no-hints` arg to `status.py` <!-- id: 43 -->
- [ ] Write new test cases in `tests/test_status.py` for each inference scenario: <!-- id: 44 -->
  - No `.cicadas/` → friendly message + hint
  - No initiatives → hint to start initiative
  - Initiative, no branches → hint to implement partition
  - Branches, no lifecycle → hint to complete partition
  - `--no-hints` → zero hint output in all cases
- [ ] Verify all existing `test_status.py` tests pass unchanged <!-- id: 45 -->

---

## Partition: feat/tutorial

> **Depends on feat/lifecycle-hints and feat/status-next-step.**

- [ ] Create `src/cicadas/scripts/tutorial.py` with `main(args)` entry point <!-- id: 60 -->
- [ ] Implement `_run_step(step_num, total, title, concept, agent_prompt, mock_output)` — prints banner + concept + 💬 prompt + mock output + checkmark + "Press Enter to continue" <!-- id: 61 -->
- [ ] Implement `_completion_screen()` — prints "You're ready!" + full 7-step cheatsheet with agent prompts <!-- id: 62 -->
- [ ] Write all 8 `MOCK_*` strings matching exact real Cicadas output format (8 strings for 7 steps — step 5 uses two): `MOCK_START`, `MOCK_SPECS`, `MOCK_KICKOFF`, `MOCK_BUILD`, `MOCK_CODE_REVIEW`, `MOCK_COMPLETE_PARTITION`, `MOCK_OPEN_PR`, `MOCK_COMPLETE_INITIATIVE` <!-- id: 63 -->
- [ ] Implement all 7 tutorial steps in `main()` using `_run_step()`: <!-- id: 64 -->
  - Step 1 — Start: 💬 "Start an initiative called my-project"
  - Step 2 — Define specs: explain agent-guided spec phase (no prompt needed)
  - Step 3 — Kickoff: 💬 "Kickoff the initiative"
  - Step 4 — Build: 💬 "Implement partition 1"
  - Step 5 — Complete partition: 💬 "Code review and complete partition"
  - Step 6 — PR: 💬 "Create a PR"
  - Step 7 — Complete: 💬 "Complete the initiative" → `_completion_screen()`
- [ ] Modify `init.py`: add `_is_first_run(root)` helper (True if `.cicadas/` was just created) <!-- id: 65 -->
- [ ] Modify `init.py`: add `_offer_tutorial(root)` — prompts "Would you like to run the tutorial now? [Y/n]:" and calls `tutorial.main()` if yes <!-- id: 66 -->
- [ ] Modify `init.py`: add `--tutorial` flag (skip prompt, run tutorial) and `--no-tutorial` flag (skip prompt, standard init only) <!-- id: 67 -->
- [ ] Register `tutorial` as a subcommand in `cicadas.py` pointing to `tutorial.main()` <!-- id: 68 -->
- [ ] Write `tests/test_tutorial.py`: <!-- id: 69 -->
  - All 7 step banners print in order (capture stdout)
  - `cicadas tutorial` makes zero changes to git state or `.cicadas/` (assert before/after state identical)
  - `cicadas tutorial` runs successfully in a bare git repo with no commits
  - `cicadas init --tutorial` runs tutorial without prompt
  - `cicadas init --no-tutorial` skips prompt, no tutorial output
  - `cicadas init` on first run (no existing `.cicadas/`) outputs tutorial prompt
  - Completion screen contains all 7 agent prompts
- [ ] Verify all existing `test_init.py` tests pass unchanged <!-- id: 70 -->

---

## Partition: feat/docs-rewrite

> **Depends on feat/tutorial.** Tutorial UX must be finalized before documenting it.

- [ ] Rewrite the "Getting Started" section of `README.md` as a narrative covering the full 7-step Cicadas flow with 💬 agent prompts at each step (no raw CLI commands exposed to users) <!-- id: 80 -->
- [ ] Add a "Quick Reference" cheatsheet to `README.md` with the 7 agent prompts in a copyable table <!-- id: 81 -->
- [ ] Update `HOW-TO.md`: add section documenting the interactive tutorial (how to run: 💬 "Run the Cicadas tutorial" or `cicadas init --tutorial`) <!-- id: 82 -->
- [ ] Update `HOW-TO.md`: add section documenting hint toggling (`hints: false` in `.cicadas/config.json` to disable; `hints: true` or remove key to re-enable) <!-- id: 83 -->
- [ ] Review all existing `HOW-TO.md` sections for consistency with the 7-step flow — update any references to raw CLI commands to use agent prompts <!-- id: 84 -->
- [ ] Review `README.md` for any remaining references to raw CLI commands in user-facing sections — replace with 💬 agent prompts <!-- id: 85 -->

---

## Initiative Boundary

- [ ] Open PR: initiative/ftue-and-flow → main and await merge approval before continuing <!-- id: 100 -->
