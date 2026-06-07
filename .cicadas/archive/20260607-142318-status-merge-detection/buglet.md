---
summary: "status.py reports a freshly-kicked-off branch as 'Merged' because _is_merged_into() only checks ancestor reachability, which is trivially true for branches that have never diverged from their target."
modules:
  - "src/cicadas/scripts/status.py"
depends_on: []
---

# Buglet: status-merge-detection

## Problem Description
`cicadas status` reports lifecycle pairs like `initiative/{name} → master` as **Merged** (and suggests "Next: Initiative complete") even when the branch was *just created* and contains zero commits beyond what `master` already has.

Root cause: `_is_merged_into()` (`src/cicadas/scripts/status.py:34`) decides "merged" purely via:
```
git merge-base --is-ancestor <source> <target>
```
This returns `true` whenever `<source>`'s tip is reachable from `<target>`'s tip — which is **trivially true** for a brand-new branch whose tip is identical to its target's tip (zero commits in either direction). The detector cannot distinguish:
- "branch did work, and that work has been merged into target", from
- "branch was created and has never diverged from target".

Observed concretely: `initiative/feat-autotune` and `master` point to the exact same commit (`6336cc2`), with empty `git log master..initiative/feat-autotune` and `git log initiative/feat-autotune..master`. The branch was created at kickoff (per the event log) but no work has landed yet — `status` nonetheless reports it "Merged" with "Next: Initiative complete."

## Reproduction Steps
1. Kick off a fresh initiative (or otherwise create a branch that forks from `master` with zero commits since).
2. Run `python src/cicadas/scripts/cicadas.py status`.
3. Observe the lifecycle section reports `initiative/{name} → master` (or `feat/{x} → initiative/{name}`) as **Merged**, with a "Next" hint suggesting the initiative/feature is complete — even though no work has been done.
4. Confirm via git that the two refs are identical: `git rev-parse {source}` and `git rev-parse {target}` return the same SHA, and both `git log {target}..{source}` and `git log {source}..{target}` are empty.

## Proposed Fix
In `_is_merged_into()` (`src/cicadas/scripts/status.py:34`), require that the source and target tips are not identical before reporting "merged" — a branch can only be considered "merged" if it actually diverged from its target and that divergence is now reachable from the target. Concretely: keep the existing `git merge-base --is-ancestor <source> <target>` check, but additionally require `git rev-parse <source> != git rev-parse <target>`. Only report "merged" when both conditions hold (ancestor-reachable **and** the refs differ), so a never-diverged branch is reported as not-yet-merged instead of a false positive.

## Implementation Notes
Implemented exactly as proposed: `_is_merged_into()` now compares `git rev-parse <source>` and `git rev-parse <target>` and short-circuits to `False` when the tips are identical, before running the existing `merge-base --is-ancestor` check. New regression test `test_is_merged_into_false_when_branch_never_diverged` covers the never-diverged case directly.

One related discovery: the existing `test_is_merged_into_true_after_merge` test was itself constructing a "never diverged" scenario (it merged a feature branch into master with zero commits between them, so git treated it as a no-op merge and the tips stayed identical) — meaning it was incidentally asserting on the very false-positive this bug describes, rather than a genuine merge. Updated it to add a real commit on the feature branch before merging, so it now exercises a true "diverged, then merged" scenario.

## Tasks
- [x] Reproduce bug with a test case <!-- id: 0 -->
- [x] Implement fix: add a tip-equality guard to `_is_merged_into()` in `status.py` so identical source/target refs are never reported as "merged" <!-- id: 1 -->
- [x] Verify fix with the test case (covering both the never-diverged false-positive case and the genuine merged case) <!-- id: 2 -->
- [x] Significance Check: Does this warrant a Canon update? <!-- id: 3 --> — No. Canon describes merge detection only at a high level ("git-based merge detection"); that description stays accurate. This is an internal correctness fix to one helper with no interface/architecture change.
