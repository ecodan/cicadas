
# Tweaklet: context-handoff

## Intent
Reduce per-session token costs when running Cicadas by (1) converting the existing soft "if the host supports it, ask for context clearing" reset guidance into directive checkpoints at four concrete execution-driven workflow boundaries, and (2) introducing a lightweight, reusable "handoff" artifact + resume rule — with subagent delegation and a code-review gate where the host supports it — so important state survives a context reset, and autonomous runs don't have to stall on a human-triggered `/clear`.

Background: a token-usage analysis of a real initiative session showed prompt tokens growing from ~918K to ~1.97M across just three turns (a ~77:1 prompt:completion ratio), strongly suggesting that nearly the full accumulated context was being re-sent each turn rather than the agent working from compact, file-backed state — exactly the failure mode the existing (but conditionally-worded) Context Reset Rules were meant to prevent. Separately: the agent has no way to self-trigger a host-level `/clear`/`/compact` — the only fully agent-controlled equivalent is delegating to a fresh subagent with an isolated context.

**Note — PRD/UX/Tech-design phase intentionally excluded**: This is the Builder-sparring loop the Emergence Hard Stop Rule protects (one spec at a time, approval between each). Adding a directive reset checkpoint there would either interrupt that dialogue with reset prompts or hand drafting to a subagent and flatten the sparring into one-shot generation — both undesirable. That phase keeps its existing (softer) Phase Reset guidance untouched; this tweak does not touch it.

## Proposed Change

1. **`SKILL.md` — Context Reset Rules** (currently ~lines 195-215): Replace the conditional "if the host supports it, ask for context clearing/compaction" phrasing in Branch/Partition Reset with directive instructions tied to four concrete, execution-driven boundaries (the Phase Reset rule for spec-drafting is left as-is — see note above):

   | Boundary | Why it's execution-driven (subagent-eligible) |
   |---|---|
   | After drafting & approving Approach + Tasks | Structured/derivable once PRD/UX/Tech are approved — no Builder sparring required to execute it |
   | After Kickoff | Mechanical, script-driven; light context either way |
   | After each partition (feature branch) completion | Natural isolation boundary already (separate `feat/` branch / optional worktree) |
   | After Initiative completion | Canon synthesis is heavy lifting a subagent can absorb; final commit/review stays with the Builder per the existing autonomy table |

   At every boundary the agent MUST: (a) refresh front matter per the existing Phase/Partition Reset steps, and (b) write a `handoff.md` (per the new template below). Then the path forks on host capability:
   - **Host supports spawning isolated subagents** → delegate the next chunk of work to a fresh subagent, passing `handoff.md`'s contents as its self-contained briefing, so the orchestrator's own context stays flat across the boundary (no human pause required — enables long autonomous runs). Before accepting the subagent's output, run a **code-review gate**: review the subagent's draft/diff/synthesis against the relevant specs (reusing the existing autonomous Code Review operation/criteria — task completeness, conformance, security/correctness/quality scan) and surface tiered findings before proceeding or handing back to the Builder. This compensates for the lost continuous human dialogue during delegated execution.
   - **Host lacks subagent support** → write the handoff, explicitly recommend the Builder run `/clear` (or the host's equivalent reset) stating the exact reload list, then resume from the handoff per the new Resume rule.

2. **New template — `templates/handoff.md`**: A compact, agent-authored artifact written immediately before each reset/handoff (regardless of which fork is taken). One reusable shape across all four boundaries. Front matter + sections:
   - `boundary`: one of `approach-tasks | kickoff | partition-complete | initiative-complete`
   - `initiative`: the initiative/tweak name
   - **Just completed** — one-line description of what just finished
   - **Approved/authoritative state** — pointers to files + sections/headings (not prose copies of content)
   - **Next action** — the single concrete next step to take on resume
   - **Reload list** — the exact files/sections to read on resume, nothing more
   - **Carry forward** — anything not yet captured in files (open decisions, deviations, signals to recheck)

3. **`SKILL.md` — Resume rule**: Add a short rule near "Resuming Mid-Initiative" (~line 286): if a handoff file exists, read it first as the authoritative pointer, consume its reload list before opening anything else, then delete/archive the file so it can't linger as stale state someone trusts later. This applies whether the resume is a Builder picking the conversation back up after `/clear` or a freshly spawned subagent starting from the handoff as its prompt.

4. **Storage convention**: `.cicadas/active/{initiative}/handoff.md` for the in-initiative boundary (approach-tasks, partition-complete); `.cicadas/handoff.md` for boundaries that span initiative lifecycles (kickoff, initiative-complete), since `active/{name}/` may not yet exist (pre-kickoff) or may already be archived (post-completion).

5. **Templates list**: Mention `handoff.md` alongside the other templates in `SKILL.md`'s templates section / CLI quick reference so it's discoverable.

This is a documentation/prompt-only change (`SKILL.md` + one new template) — no script or code changes, well under the 100-line tweak threshold.

## Tasks
- [x] Draft `templates/handoff.md` with the front matter + section shape described above <!-- id: 10 -->
- [x] Update `SKILL.md` Context Reset Rules to name the 4 execution-driven boundaries and define the fork resolution (subagent-with-code-review-gate vs. human `/clear`+handoff); leave the spec-drafting Phase Reset guidance untouched <!-- id: 11 -->
- [x] Add a "Resume from handoff" rule near "Resuming Mid-Initiative" directing the agent (human-resumed or freshly spawned subagent) to read, consume, then delete/archive `handoff.md` <!-- id: 12 -->
- [x] Add `handoff.md` to the templates list / CLI quick reference in `SKILL.md` <!-- id: 13 -->
- [x] Verify functionality: trace through each of the 4 boundaries (both forks where applicable) against the new wording (dry run / manual walkthrough) <!-- id: 14 -->
- [x] Significance Check: Does this warrant a Canon update? <!-- id: 15 -->

## Notes
Implemented as a new "Directive Handoff Checkpoints" subsection in `SKILL.md` (after Partition Reset, before Kickoff), rather than rewriting Branch/Phase/Partition Reset in place — this kept the PRD/UX/Tech-design Phase Reset guidance completely untouched while layering directive behavior on top at the four named boundaries (one of which, Approach+Tasks, narrows the otherwise-conditional Phase Reset specifically at that boundary). Walkthrough of all 4 boundaries × both forks traced cleanly against the new wording; no inconsistencies found.

**Significance check — no Canon update warranted**: This is a documentation/prompt-only change to `SKILL.md` plus one new template file. `canon/product-overview.md` references key templates only in passing (e.g. `buglet.md`, `tweaklet.md` as part of describing the Lightweight Paths feature) and does not enumerate the full template set or the Context Reset Rules' internal wording — neither of which represents a durable architectural truth that canon needs to track. No code/script changes, no new modules, no shift in branching model or lifecycle.
