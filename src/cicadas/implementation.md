
This document defines the rules for an **Implementation Agent**. These rules prevent agents from "running amok" and ensure changes are made within the correct safety boundaries.

## 1. The Hard Stop
An agent MUST stop and wait for human review after the **Emergence** phase (generating `tasks.md`).
- **Rule**: Do not start implementing code until the user explicitly says "Kickoff" or "Start a Feature".
- **Why**: The `tasks.md` file often needs human correction for granularity and parallelism.

## 2. Identity Check (Branch Safety)
Before touching any project source code, an agent MUST verify its environment.
- **Rule**: You must only write code if you are on a **registered feature branch** or a **task branch** forked from one. Check `.cicadas/registry.json`.
- **Constraint**: No direct code changes to `main`, `master`, or initiative branches are permitted.

## 3. Execution Scope
When working on a branch:
- **Rule**: Only implement the tasks assigned to your current feature branch partition.
- **Rule**: If you discover that a task requires changing files outside your declared modules, STOP and notify the user.

## 4. Pause Before Committing (Reflect + Tasks + Code Review for Features)
Before **committing** on a feature branch (`feat/`) or task branch (`task/`):
- **Rule**: Do not commit without running Reflect and updating active specs. Treat "about to commit" as a trigger for Reflect.
- **Rule**: As part of Reflect, update `.cicadas/active/{initiative}/tasks.md`: mark completed tasks with `- [x]`, add or adjust tasks if the implementation diverged from the plan.
- **Rule (feature branches only)**: Before committing on a **feature branch** (`feat/`), also run the **Code Review** operation (after Reflect). Resolve or acknowledge Blocking findings before committing. This applies when completing feature-level work, not necessarily every single commit — but before any commit that would be considered "feature complete" or before opening a PR from the feature branch.
- **Rule**: Only then commit. This keeps specs and code in sync at every commit, not only at PR time.

Before opening a PR for a task branch, in addition to the above:
- **Rule**: Include Reflect findings in the PR description.

## 4b. Pause at `Open PR` Tasks (Hard Stop)
When executing a `tasks.md` checklist and the next unchecked task matches the pattern `- [ ] Open PR: ...`:
- **Rule**: STOP. Do NOT mark it complete. Do NOT merge. Do NOT proceed to the next task.
- **Rule**: Run `open_pr.py` to open the PR, then surface the PR URL to the Builder and explicitly state: *"Waiting for merge approval before continuing."*
- **Rule**: Only after the Builder explicitly confirms the PR has been merged should the agent mark the task `- [x]` and continue with subsequent tasks.
- **Why**: `Open PR` tasks are human-gated checkpoints, not automatic steps. The implementation agent has no authority to merge — that is always a Builder decision.

## 5. No Canon on Branches
- **Rule**: Never write to `.cicadas/canon/` on any branch.
- **Why**: Canon is only synthesized on `main` at initiative completion. Writing canon on branches creates merge conflicts.

## 6. Synthesis
When an initiative is complete:
- **Rule**: Merge the initiative branch to `main` first, then synthesize canon on `main`.
- **Rule**: Do not archive active specs until the Builder reviews the synthesized canon.

## 7. Registry Integrity
- **Rule**: NEVER manually edit `registry.json`.
- **Constraint**: ALWAYS use the provided CLI scripts (e.g., `branch.py`, `kickoff.py`, `status.py`) to manage system state.

## 8. Always Push to Remote
- **Rule**: Every branch creation and every merge to a long-lived branch MUST be followed by a `git push`.
  - New initiative branch (via `kickoff.py`): script handles `git push -u origin initiative/{name}`.
  - New feature branch (via `branch.py`): script handles `git push -u origin {name}`.
  - After merging a feature branch into the initiative branch: `git push origin initiative/{name}`.
  - After merging the initiative branch into `main` and after the final canon commit: `git push origin main`.
- **Why**: Collaborators and CI/CD systems depend on the remote. Local-only branches and merges are invisible to the team.

## 9. Emit Task Completion Events
After marking a task checkbox `- [x]` in `tasks.md`, emit a `task.complete` event:
```
python {cicadas-dir}/scripts/emit_event.py \
  --initiative {name} --type task.complete \
  --data '{"task_id": "<id>", "summary": "<one-line summary>"}'
```
- **Rule**: Use `check=False` (or the equivalent try/except wrapper) — emit failure must never abort the primary operation.
- **Why**: Allows automated drivers (e.g., Chorus) to observe task-level progress without polling spec files.

## 10. Emit Partition Completion Events
When all tasks in a partition are marked `- [x]` and before opening the partition PR, emit a `partition.complete` event:
```
python {cicadas-dir}/scripts/emit_event.py \
  --initiative {name} --type partition.complete \
  --data '{"partition": "<branch-name>", "summary": "<what was built>", "canon_entry": "<suggested canon update>", "notes_for_evaluator": "<acceptance criteria notes>"}'
```
- **Rule**: `summary` is required. `canon_entry` and `notes_for_evaluator` are optional but strongly encouraged for automated evaluation.
- **Rule**: Emit before opening the PR so the event is captured in the same active spec window as the implementation.
- **Why**: Provides structured, machine-readable signal that a partition is ready for review — distinct from the PR itself.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
