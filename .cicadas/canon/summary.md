
# Canon Summary

> Auto-generated during canon synthesis. Consumed by agents at branch start.

## Purpose

Cicadas is a spec-driven development orchestrator for human-AI teams that treats forward-looking specs as disposable inputs and synthesizes authoritative documentation from code at initiative completion.

## Architecture

- Filesystem state machine: all state lives in `.cicadas/` (registry.json, active/, archive/, canon/); no database or server.
- Logic/state separation: the Skill (`src/cicadas/`) is portable and installable; the state (`.cicadas/`) stays in the project.
- Scripts are pure Python stdlib — no required external dependencies at runtime; only `git` and Python 3.11+ required. Optional `tracing` extras group (`opentelemetry-api/sdk/exporter-otlp-proto-http`) adds opt-in OTel distributed tracing (off by default; null-object fallback when absent or disabled).
- Agent operations (Reflect, Code Review, Synthesis) are LLM tasks defined in `emergence/` markdown prompts, not scripts. Clarify supports intake via Q&A, doc, or Loom. Start flow includes Building on AI? (yes/no) and eval status; stored in emergence-config.json. Initiatives: optional eval spec (eval-spec.md + template); Approach asks eval placement. Tweaks/bugs: optional eval/benchmark reminder. Cicadas does not run evals.
- Context injection: `branch.py` writes `context.md` at branch creation time (canon summary + scoped module snapshots + specs); gitignored.
- Hint subsystem: `utils.py` provides `hints_enabled(args, config)` (priority: `--no-hints` flag → `config['hints'] == False` → not TTY → True) and `print_hint(lines, args, config)` (66-char cyan box). Every lifecycle script (kickoff, branch, archive, update_index, open_pr, init) prints a next-step hint after its main output. `status.py` infers and prints a hint from registry state. Hints auto-suppress in non-TTY environments (CI/pipes).
- Compact context contract: core initiative specs now carry machine-readable front matter (`summary`, `modules`, `depends_on`, `index`) so agents can reload approved context from the specs themselves.
- Reset workflow: `SKILL.md` defines Branch Reset, Phase Reset, and Partition Reset rules. They prefer `canon/summary.md`, spec front matter, and indexed sections before full-doc loading, and only use host-supported clear/compact behavior opportunistically.

## Modules

scripts/init.py: bootstrap `.cicadas/` directory structure (idempotent); on first run prompts "Would you like to run the Cicadas tutorial now? [Y/n]"; supports --tutorial (auto-run) and --no-tutorial (skip prompt) flags
scripts/kickoff.py: promote drafts → active, register initiative, create initiative branch
scripts/branch.py: create and register feature/fix/tweak branches; write context.md bundle
scripts/status.py: report active initiatives/branches; Merged/Next when lifecycle.json present; _infer_next_step() emits next-step hint based on registry state (no .cicadas → init; no initiatives → start; no branches → implement; no lifecycle → complete partition)
scripts/check.py: detect module overlap conflicts across active branches
scripts/create_lifecycle.py: create lifecycle.json with PR boundaries and step list
scripts/open_pr.py: open PR via gh/glab/Bitbucket/fallback; blocks on BLOCK verdict
scripts/review.py: read review.md verdict, return exit codes (0=PASS, 1=BLOCK, 2=missing)
scripts/signal.py: broadcast breaking change to peer branches
scripts/update_index.py: append completed-work entry to index.json
scripts/archive.py: deregister and expire active specs on initiative completion
scripts/abort.py: context-aware rollback for any branch type
scripts/history.py: generate HTML timeline from archive + index; includes token summaries
scripts/tokens.py: append-only token usage log API (init_log, append_entry, load_log)
scripts/utils.py: shared utilities (root detection, git helpers, JSON I/O, worktree ops, emit() non-fatal event emitter, ANSI color constants, hints_enabled(), print_hint() 66-char box, print_tutorial_banner(), print_tutorial_checkmark())
scripts/tutorial.py: interactive 7-step tutorial; invoked by `cicadas tutorial` or `init.py --tutorial`; each step prints banner + concept + agent prompt + explanatory text + checkmark + pause; completion screen shows Quick Reference cheatsheet
scripts/emit_event.py: append typed event to events.jsonl with fcntl.flock; CLI: --initiative, --type, --data
scripts/get_events.py: read/filter events.jsonl; CLI: --initiative, --type, --since, --last; exits 0+empty if absent
scripts/tracing.py: optional OTel tracing facade (init_tracer, flush, get/store_trace_context, parent_context_for_initiative, span_context_hex); _NullTracer/_NullSpan fallback when disabled or SDK absent; persists {trace_id, span_id} in registry.json for cross-process trace continuity (each cicadas command is its own subprocess)
emergence/: markdown prompts for Clarify, UX, Tech, Approach (incl. Step 4b: Artifact Type, How to Run, AC generation per partition), Tasks, Bootstrap, Bug-fix, Tweak, Eval Spec (Building on AI), Code Review; start-flow includes Building on AI? and eval status
emergence/clarify.md: refreshes approved front matter fields as sections are completed; no longer relies on `steps_completed`
templates/approach.md: partition blocks include Artifact Type, How to Run, and Acceptance Criteria subsections
templates/: spec templates (prd, ux, tech-design, approach, tasks, buglet, tweaklet, eval-spec, review), canon templates, synthesis prompt; core initiative templates share the front matter contract
tests/test_templates.py: regression checks for the front matter contract and compact context routing hints

## Conventions

- Never manually edit `registry.json` — always use scripts.
- Never write to `.cicadas/canon/` on any branch — canon only on master after merge.
- Reflect (update active specs to match code) before every commit on feat/task branches.
- Refresh front matter during Reflect when the meaning of a spec changes.
- Code Review (writes review.md) after Reflect on feat branches; open_pr.py enforces BLOCK.
- Hints are on by default; disable globally via `hints: false` in `.cicadas/config.json`, or per-command via `--no-hints` flag.
- Tracing is opt-in via `tracing.enabled: true` in `.cicadas/config.json`; all `tracing.*` calls must be wrapped in `try/except Exception` and must never duplicate or gate the wrapped operation — only `_run_script`-style work runs; tracing failures are swallowed.
- Tests use real temp filesystems + real git repos (no mocks for I/O); base class in `tests/base.py`.
- PYTHONPATH=src/cicadas/scripts:tests for all test runs; system python3 (not .venv) for tests.
- Ruff for lint/format; pre-commit hooks enforced.
