# Cicadas: Next Evolution — Roadmap Notes

_Discussion notes from March 2026. These are directional proposals, not finalized specs._

---

## 1. Worktrees for Parallel Execution

**What:** Use `git worktree` for parallel feature branch execution; plain branches for sequential work.

**Why:** Worktrees give each agent an isolated filesystem checkout without requiring a separate clone. Agents can build, test, and commit independently without fighting over the working directory. For sequential work, the overhead isn't justified — `git switch` is sufficient.

**Key design decisions:**

- `approach.md` must explicitly encode a dependency DAG between partitions — which can run in parallel, which must wait. The emergence agent is responsible for declaring this during spec authoring.
- `kickoff.py` / `branch.py` read the DAG and decide: parallel → create worktree, sequential → create plain branch.
- `check.py` should run *before* parallel execution starts (not just on-demand) to catch module ownership conflicts early.
- Cleanup is explicit: `archive.py` and `abort.py` must tear down worktrees, not just delete branch references.

**Approach.md addition needed:** A `partitions` block declaring each partition's name, module scope, and dependencies (e.g. `depends_on: [partition-a]`). Empty `depends_on` means it can run immediately.

---

## 2. Spec Development Stays Human-Paced

**What:** No compression of the emergence phase. Each subagent phase (Clarify → UX → Tech → Approach → Tasks) remains a sparring opportunity between human and agent.

**Why:** This is where Cicadas earns its keep. The spec pipeline eliminates ambiguity that would otherwise cause agent failures downstream. Compressing it to save time trades the wrong thing.

**One addition worth considering:** A cross-phase consistency check at the end of emergence — after Tasks is drafted, an agent reviews the full draft set for internal contradictions. Examples: tasks.md implying more scope than approach.md's partitions can contain; tech-design.md dependencies not reflected in the partition DAG; UX flows referencing features not in the PRD. This surfaces as a structured list of questions for the human, not autonomous resolution.

---

## 3. Automated Code Review as Merge Gate

**What:** After each feature branch completes, an independent code review agent runs before any merge proceeds. It produces a structured `review.md` artifact and issues a verdict.

**Why:** Removes a manual review step without removing quality assurance. The agent catches spec drift, test gaps, and code quality issues. Human only intervenes if the agent flags a block.

**Report structure (proposed `review.md`):**

- **Spec conformance** — did the implementation match tasks.md? List any gaps or deviations.
- **Reflect status** — are the active specs current with the code? Flag if Reflect was skipped.
- **Test coverage delta** — coverage before/after. Flag regressions.
- **Lint/format** — ruff clean, any warnings.
- **Merge verdict** — one of: `PASS`, `PASS WITH NOTES` (human should read but can proceed), `BLOCK` (human must resolve before merge).

**Placement:** `review.md` lives alongside `tasks.md` in `.cicadas/active/{initiative}/`. It is generated fresh on each review run — not manually edited.

**Merge gate:** PRs to initiative branch (and initiative to main) should not proceed with a `BLOCK` verdict. `PASS WITH NOTES` can proceed at human discretion.

---

## 4. Context Injection at Branch Start

**What:** When `branch.py` starts a feature branch, automatically inject relevant canon context into the agent's starting context.

**Why:** The research finding that token usage explains 80% of multi-agent performance variance points directly here. Agents that start with the right context make better decisions and deviate less from the plan.

**What gets injected:**

- `canon/summary.md` — a compressed, high-signal overview of the full codebase (a few hundred tokens). This is a new artifact produced during canon synthesis, sitting alongside the full canon docs.
- Full module snapshots (`canon/modules/{module}.md`) for each module declared in the feature branch's scope.
- The feature's own `tasks.md` and the parent initiative's `approach.md`.

**Canon synthesis addition:** The synthesis step (currently producing `product-overview.md`, `tech-overview.md`, etc.) adds one more output: `canon/summary.md`. Concise — think 300-500 tokens. Purpose is branch-start injection, not human reading.

**Implementation:** `branch.py` assembles this context bundle and either writes it to a temp file the agent reads, or passes it as the agent's initial prompt prefix, depending on the agent integration.

---

## 5. Coordination and Collision Prevention (Deferred)

**Status:** Parked for now. The problem is real — parallel agents on separate machines or in separate repos need a remote coordination primitive, not a local filesystem one. Git-native approaches (signals as commits to a shared ref, or a dedicated `cicadas/state` branch) are the most promising direction. Revisit once the above four are in place.

---

## Summary of Script/Skill Changes Required

| Component | Change |
|---|---|
| `approach.md` template | Add `partitions` block with dependency DAG |
| `branch.py` | Read DAG, create worktree vs. plain branch accordingly |
| `kickoff.py` | Run `check.py` before parallel execution starts |
| `archive.py` / `abort.py` | Tear down worktrees on cleanup |
| `check.py` | Support pre-execution conflict validation mode |
| Canon synthesis | Add `summary.md` output |
| `branch.py` | Inject canon summary + module snapshots at branch start |
| New: `review.py` | Code review agent runner, produces `review.md` |
| `open_pr.py` | Check for `BLOCK` verdict in `review.md` before proceeding |
| `emergence/code-review.md` | Update with new report structure and verdict format |
| `templates/review.md` | New template for code review output |
