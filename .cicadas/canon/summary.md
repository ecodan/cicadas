
# Canon Summary

> Auto-generated during canon synthesis. Consumed by agents at branch start.

## Purpose

Cicadas is a spec-driven development orchestrator for human-AI teams that treats forward-looking specs as disposable inputs and synthesizes authoritative documentation from code at initiative completion.

## Architecture

- Filesystem state machine: all state lives in `.cicadas/` (registry.json, active/, archive/, canon/); no database or server.
- Logic/state separation: the Skill (`src/cicadas/`) is portable and installable; the state (`.cicadas/`) stays in the project.
- Scripts are pure Python stdlib — no external dependencies at runtime; only `git` and Python 3.11+ required.
- Agent operations (Reflect, Code Review, Synthesis) are LLM tasks defined in `emergence/` markdown prompts, not scripts. Clarify supports intake via Q&A, doc, or Loom. Start flow includes Building on AI? (yes/no) and eval status; stored in emergence-config.json. Initiatives: optional eval spec (eval-spec.md + template); Approach asks eval placement. Tweaks/bugs: optional eval/benchmark reminder. Cicadas does not run evals.
- Context injection: `branch.py` writes `context.md` at branch creation time (canon summary + scoped module snapshots + specs); gitignored.

## Modules

scripts/init.py: bootstrap `.cicadas/` directory structure (idempotent)
scripts/kickoff.py: promote drafts → active, register initiative, create initiative branch
scripts/branch.py: create and register feature/fix/tweak branches; write context.md bundle
scripts/status.py: report active initiatives/branches; Merged/Next when lifecycle.json present
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
scripts/utils.py: shared utilities (root detection, git helpers, JSON I/O, worktree ops, emit() non-fatal event emitter)
scripts/emit_event.py: append typed event to events.jsonl with fcntl.flock; CLI: --initiative, --type, --data
scripts/get_events.py: read/filter events.jsonl; CLI: --initiative, --type, --since, --last; exits 0+empty if absent
emergence/: markdown prompts for Clarify, UX, Tech, Approach (incl. Step 4b: Artifact Type, How to Run, AC generation per partition), Tasks, Bootstrap, Bug-fix, Tweak, Eval Spec (Building on AI), Code Review; start-flow includes Building on AI? and eval status
templates/approach.md: partition blocks include Artifact Type, How to Run, and Acceptance Criteria subsections
templates/: spec templates (prd, ux, tech-design, approach, tasks, buglet, tweaklet, eval-spec, review), canon templates, synthesis prompt

## Conventions

- Never manually edit `registry.json` — always use scripts.
- Never write to `.cicadas/canon/` on any branch — canon only on master after merge.
- Reflect (update active specs to match code) before every commit on feat/task branches.
- Code Review (writes review.md) after Reflect on feat branches; open_pr.py enforces BLOCK.
- Tests use real temp filesystems + real git repos (no mocks for I/O); base class in `tests/base.py`.
- PYTHONPATH=src/cicadas/scripts:tests for all test runs; system python3 (not .venv) for tests.
- Ruff for lint/format; pre-commit hooks enforced.
