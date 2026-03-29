
# Emergence: Approach

**Goal**: Define the implementation strategy, including logical partitions that become feature branches.

**Role**: You are a Lead Developer. Your job is to figure out *how* to build the design, step-by-step, and how to *partition* the work for parallel execution.

## Process

FOLLOW THIS PROCESS EXACTLY. DO NOT SKIP STEPS UNLESS INSTRUCTED.

0. **Pace Check**: Read `.cicadas/drafts/{initiative}/emergence-config.json`. If absent, treat pace as `"doc"`. State the active rule before proceeding:
    - `section` — pause after each section (use the Balanced Elicitation Menu per section as normal)
    - `doc` — complete the full doc, then hard stop for Builder review before moving to Tasks
    - `all` — complete the full doc and continue to Tasks without stopping

1.  **Lifecycle Check**: Check if `.cicadas/drafts/{initiative}/lifecycle.json` already exists. If so, skip this step — PR preference was already set during Clarify. Otherwise, ask the Builder:

    > *"How do you want to handle PRs for this initiative?"*
    > 1. **No PRs** — merge directly at every boundary (fastest, solo work)
    > 2. **Final merge only** — one PR when the initiative merges to master
    > 3. **Full PR flow** — PR at every feature boundary + the initiative merge (default, team workflow)

    Then immediately run the common CLI `create-lifecycle` command with the matching flags:
    - Option 1 (no PRs): `python {cicadas-dir}/scripts/cicadas.py create-lifecycle {initiative} --no-pr-initiatives --no-pr-features`
    - Option 2 (final only): `python {cicadas-dir}/scripts/cicadas.py create-lifecycle {initiative} --no-pr-features`
    - Option 3 (full, default): `python {cicadas-dir}/scripts/cicadas.py create-lifecycle {initiative}`

2.  **Ingest**: Read `prd.md`, `ux.md`, and `tech-design.md` from `.cicadas/drafts/{initiative}/` (or `.cicadas/active/{initiative}/` if the initiative was already kicked off).
3.  **LLMs and Evals — Eval spec offer and placement** (initiatives only): Read `emergence-config.json` from `.cicadas/drafts/{initiative}/` or `.cicadas/active/{initiative}/`. If `building_on_ai` is true and `eval_status` is `"will_do"`:
    - **Eval spec offer**: If `eval-spec.md` does not yet exist in drafts or active for this initiative, ask: *"Would you like help creating the eval spec now? I'll walk you through the template using the LLMOps Experimentation playbook (define success, dataset, rubrics, harness, experiment, wrap-up). (yes / no)"* If yes, run the **[Eval Spec](./eval-spec.md)** instruction module, then continue with the placement question below. If no or if eval-spec.md already exists, skip to the placement question.
    - **Eval placement**: Ask the Builder: *"Do you want to insert the (manual) eval step before starting the build, or run evals in parallel with the build? (before / parallel)"*.
    - If the user chooses **parallel**, show: *"Heads up: if evals run in parallel, their results may materially affect requirements and design. We suggest waiting for eval results before locking the build plan. You can still proceed now if you prefer."*
    - Write `eval_placement: "before_build"` or `eval_placement: "parallel"` to `emergence-config.json` (merge with existing keys). When you draft `approach.md` in step 5, add an explicit **Eval** step in the Strategy or Sequencing section: if before_build, e.g. *"Run evals per eval spec before implementation; proceed when gates are met."*; if parallel, e.g. *"Evals run in parallel; be prepared to update requirements/design if results change."* If `building_on_ai` is false or `eval_status` is not `"will_do"`, skip this step and do not add an Eval step to the approach.
4.  **Plan**:
    -   **Define Partitions**: Identify logical partitions of work. Each partition becomes a **Feature Branch**. For each partition, declare:
        - A name (e.g., `feat/data-and-auth`, `feat/frontend-shell`)
        - The modules it touches (e.g., `db`, `auth`, `frontend/core`)
        - Its scope and boundaries
    -   **Sequence**: Determine ordering and dependencies between partitions. Which must go first? Which can run in parallel?
    -   **Author the Partitions DAG**: In the `## Sequencing` section, add a `yaml partitions` fenced block (see template). For every partition:
        - Set `depends_on: []` if it can run in parallel (no prerequisites). This partition **will get its own git worktree** when `branch.py` is run.
        - Set `depends_on: [feat/other-partition]` if it must wait for another partition to merge first. This partition will be a plain branch.
        - If no partition is parallel (all have non-empty `depends_on`), the block is still valid — all branches will be plain. Omit the block entirely only if the concept of parallelism is irrelevant to the initiative.
    -   **Identify Risks**: Module overlaps between partitions, migration concerns, shared component boundaries.
    -   **Plan for backward compatibility and migration** (brownfield).
    -   **Other requirements or prohibitions**
        - Do NOT include estimated effort or timeframes for phases or tasks.

4b. **Per-Partition Evaluator Sections**: For each partition defined in step 4, generate three additional subsections — `#### Artifact Type`, `#### How to Run`, and `#### Acceptance Criteria` — placed before `#### Implementation Steps`. These make the partition spec machine-testable by an automated evaluator.

    -   **Infer Artifact Type**: Determine which type best describes what the partition produces:
        - `web-ui` — browser-rendered interface
        - `rest-api` — HTTP API endpoints
        - `cli` — command-line tool
        - `library` — importable module with no persistent process
        - `background-service` — daemon or worker process
        - `full-stack` — both server and client (evaluator will start both and test via browser)

        Use the partition description, module names, and tech-design.md to infer the type. **When ambiguous, ask the Builder before proceeding.**

    -   **Generate `#### How to Run`**: Inspect the project root for `package.json`, `pyproject.toml`, `Makefile`, and `Dockerfile` to determine the build system and derive exact commands:
        - `start` — the exact command to launch the artifact (e.g. `npm run dev -- --port 3000`, `uvicorn app:main --port 8000`). **Omit for `library` and `cli` when there is no persistent process.**
        - `ready-check` — an endpoint or condition the evaluator polls before beginning tests (e.g. `GET http://localhost:3000/health returns 200`). **Required for any artifact that starts a server.**
        - `teardown` — how to stop the process (e.g. `Ctrl+C` / process group kill).
        If tooling cannot be detected, write a placeholder and add `<!-- NEEDS MANUAL REVIEW -->`.

    -   **Generate `#### Acceptance Criteria`**: Write a checklist of falsifiable, independently verifiable pass/fail statements matched to the artifact type:
        - `rest-api`: endpoint criteria — HTTP method, path, status code, response shape (e.g. `POST /api/items returns 201 with {id, name, createdAt}`)
        - `web-ui`: interaction criteria — user action → observable UI state, with timing where relevant (e.g. `submitting empty form displays inline error without page reload`)
        - `cli`: stdout/stderr/exit-code criteria (e.g. `running with --help exits 0 and prints usage`)
        - `library`: function call → return value or side effect (e.g. `parse_config("valid.toml") returns dict with expected keys`)
        - `background-service`: observable side effects — files written, messages queued, state changed
        - `full-stack`: combination of API and UI criteria

        Each criterion must be:
        - **Falsifiable** — has a single expected outcome that is either true or false
        - **Observable** — checkable by an automated agent without human judgement
        - **Specific** — includes exact endpoints, fields, status codes, commands, or UI states

        Flag any criterion that cannot be made machine-verifiable with `<!-- NEEDS MANUAL REVIEW -->` so the Builder can revise before execution. Do NOT omit the criterion — losing the intent is worse than flagging it.

5.  **Draft**: Create `.cicadas/drafts/{initiative}/approach.md` (or update `.cicadas/active/{initiative}/approach.md` if post-kickoff). Include the Eval step from step 3 when applicable.
6.  **Refine**:
    - **If pace is `"doc"` or `"section"`**: STOP and present the complete approach for Builder review.
    - **If pace is `"all"`**: Continue directly to the next module (Tasks) without stopping.

## Output Artifacts

- **lifecycle.json** (after step 1): In `.cicadas/drafts/{initiative}/lifecycle.json`; created by the common CLI `create-lifecycle` command with the Builder's PR boundary choices. Promoted to active at kickoff.
- **approach.md**: Use the template at `{cicadas-dir}/templates/approach.md`.

**The approach document is the single most important artifact in Emergence.** Every downstream decision — branch names, module scopes, conflict detection, registry entries — flows from the partitions defined here.

## Key Considerations

-   **Partitions are mandatory**: The approach MUST define named partitions with declared module scopes. Without partitions, feature branches cannot be created.
-   **Author the Partitions DAG**: Every approach.md MUST include the `yaml partitions` fenced block in `## Sequencing`. This block is machine-read by `branch.py` to decide whether to create a git worktree (parallel) or a plain branch (sequential). Use the exact format from the template.
-   **`depends_on` semantics**:
    - `depends_on: []` → parallel partition — gets its own isolated git worktree directory so agents can work on it simultaneously.
    - `depends_on: [feat/x]` → sequential — plain branch created from the initiative branch, waits for `feat/x` to merge first.
-   **Module boundary clarity**: If two partitions touch the same module, tighten the boundaries (e.g., `frontend/core/` vs. `frontend/social/`).
-   **Testability**: How will we test this?
-   **Incremental Delivery**: Can we ship this in pieces?
-   **Risks**: What could go wrong?

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
