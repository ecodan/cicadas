
# Emergence: Tasks

**Goal**: Break the approach into a checklist of small, testable tasks, grouped by partition.

**Role**: You are a Project Manager / Tech Lead. Your job is to create a clear plan of action for the developer.

## Process

FOLLOW THIS PROCESS EXACTLY. DO NOT SKIP STEPS UNLESS INSTRUCTED.

0. **Pace Check**: Read `.cicadas/drafts/{initiative}/emergence-config.json`. If absent, treat pace as `"doc"`. State the active rule before proceeding:
    - `section` — pause after each section (use the Balanced Elicitation Menu per section as normal)
    - `doc` — complete the full doc, then hard stop for Builder review before proceeding to kickoff
    - `all` — complete the full doc and present to Builder (this is the final doc — always present at the end regardless of pace)

1.  **Ingest**: Read all previous docs in `.cicadas/drafts/{initiative}/`.
2.  **Select Mode**: Choose **Foundation Mode** for greenfield projects or new standalone modules with no existing codebase to extend. Choose **Feature Mode** when adding vertical slices of functionality to an existing system.
    -   **Foundation Mode** (New Project/Module):
        -   **Decompose**: Atomic, file-level tasks.
        -   **Order**: Strict dependency phases (Models → Engine → UI).
        -   **Parallelism**: Independent *Work Groups* within a phase.
    -   **Feature Mode** (Vertical Slice):
        -   **Decompose**: Functional deliverables (e.g., "Add Inventory").
        -   **Order**: Group by feature or user story.
        -   **Parallelism**: Features are parallel; tasks within a feature are sequential.

3.  **Group by Partition**: Tasks MUST be organized under the partitions defined in `approach.md`. Each partition's tasks map to a Feature Branch.
4.  **Draft**: Create `.cicadas/drafts/{initiative}/tasks.md`.
    -   Use the format `- [ ] Task Description <!-- id: N -->`
5.  **Refine**: **Always present to the Builder for review.** Tasks is the final spec doc — it is always presented regardless of pace setting.
6.  **Consistency Check**: Once the Builder approves `tasks.md`, run the
    `emergence/consistency-check` instruction module. It reads all five draft docs and surfaces any
    cross-phase contradictions as questions for the Builder. Resolve any flagged issues before
    proceeding to kickoff.
7.  **Inject PR tasks from `lifecycle.json`**: Read `lifecycle.json` from `.cicadas/drafts/{initiative}/`. For each step with `opens_pr: true`, append a PR task at the relevant boundary:
    -   If `pr_boundaries.features: true` → add at the end of **each partition's** task list:
        `- [ ] Open PR: feat/{branch} → initiative/{name} and await merge approval before continuing <!-- id: PR-feature -->`
    -   If `pr_boundaries.initiatives: true` → add at the very end of `tasks.md`:
        `- [ ] Open PR: initiative/{name} → master and await merge approval before continuing <!-- id: PR-initiative -->`
    -   If `lifecycle.json` is absent or `pr_boundaries` all false: skip this step silently.
    -   **Why**: These tasks make PR boundaries explicit and pauseable. The implementation agent will stop at these tasks and wait for Builder approval before merging.

## Output Artifact: `tasks.md`

Use the template at `{cicadas-dir}/templates/tasks.md`.

## Key Considerations

-   **Granularity**: Tasks should be small enough to complete in one sitting.
-   **Verify-ability**: Each task should have a clear "done" state.
-   **Dependencies**: Identify blockers.
-   **Acceptance Criteria**: Each task should include criteria for what "done" looks like.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
