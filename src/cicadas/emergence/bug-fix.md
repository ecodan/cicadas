
# Instruction Module: Bug Fix (Clarify Bug)

## Role
You are the **Bug Fix instruction module**. Your goal is to help the Builder clarify a bug and draft a concise `buglet.md` specification.

## Process

FOLLOW THIS PROCESS EXACTLY. DO NOT SKIP STEPS UNLESS INSTRUCTED.

**Run the [Standard Start Flow](./start-flow.md) first.** For bug fixes, that means in order:

0.  **Standard Start Flow** (see [start-flow.md](./start-flow.md)):
    0a. **Process Preview**: Before starting, show the Builder the spec phase steps:
        ```
        Spec phase:   Clarify bug → Analyze codebase → Draft buglet.md → [Your review]
        Then:         Kickoff → Branch → Implement → Significance check → Merge → Archive
        ```
    0b. **Name**: Get or confirm the bug-fix name. If the user already gave a name, still ask: *"What is the name of this fix? 1. {name}, 2. Other (enter the name)"*.
    0c. **Create draft folder**: Ensure `.cicadas/drafts/{name}/` exists (create it if needed).
    0d. **LLMs and Evals?**: Ask *"Will this feature or change be powered by LLMs and may require ML evals to ensure quality? (yes / no)"*. If **yes**, ask *"This change involves LLMs. Experimentation and evals may be required. Does this project already have completed evals, or will you be doing evals? (already have / will do)"*. Write `building_on_ai` and `eval_status` to `.cicadas/drafts/{name}/emergence-config.json` (merge with existing keys). If **no**, write `building_on_ai: false` and continue.
    0e. **PR preference**: Ask *"Do you want to open a PR when merging this fix to master? (yes / no)"*, then run `create_lifecycle.py`:
        - **Yes** (default): `python {cicadas-dir}/scripts/cicadas.py create-lifecycle {name} --no-pr-features`
        - **No**: `python {cicadas-dir}/scripts/cicadas.py create-lifecycle {name} --no-pr-initiatives --no-pr-features`

1.  **Understand the Bug**: Ask the Builder for the observed behavior and reproduction steps if not already clear.
2.  **Analyze**: Quickly scan the codebase to identify the likely cause. Do not perform a deep refactor or redesign.
    - If optional graph artifacts are present, prefer graph-assisted routing for symptom-led bugs: use `graph area`, `graph tests`, `graph callers`, or `graph signature-impact` to find the likely owning area, nearby tests, and stale callsites.
    - If graph support is absent, continue with existing routing artifacts (`canon/summary.md`, `canon/repo-context.md`, routing guides, targeted reads) without treating that as a blocker.
3.  **Draft Buglet**: Fill out the `buglet.md` template.
    - Keep descriptions punchy.
    - Ensure reproduction steps are actionable.
    - Define a simple, direct fix strategy.
    - Ensure the bug fix has coverage from automated tests.
    - **LLM and Eval reminder**: If `emergence-config.json` has `building_on_ai: true` and `eval_status: "will_do"`, before finalizing the buglet ask: *"This work involves LLMs and you said you'll run evals/benchmarks. I can add a reminder to your buglet — e.g. a task 'Run regression benchmark before merging.' Add it? (yes / no)"*. If yes, add one checklist task or a short "Benchmark / eval" section. Do **not** offer the full eval-spec authoring flow (that is for initiatives only).
4.  **Review**: Present the `buglet.md` to the Builder for approval. Once approved, show the implementation path:
    ```
    Next steps:   Kickoff → Branch (fix/{name}) → Implement → Significance check → Merge to master → Archive → Branch cleanup
    ```

## Artifacts
- **Output**: `.cicadas/drafts/{name}/buglet.md`

## Escalation
If you discover that the fix requires architectural changes, database migrations, or touches more than 2-3 modules, **inform the Builder** and suggest upgrading to a full `Clarify` (Initiative) path.

---
_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
