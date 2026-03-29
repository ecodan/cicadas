# Tweaklet: worktree-ergonomics

## Intent
Reduce the friction introduced by automatic git worktrees without giving up the isolation benefits that helped parallel Cicadas streams. This tweak should keep worktrees where they clearly help, fix incorrect branch-parent selection when worktree setup falls back awkwardly, and make the active workspace location visible enough for builders, IDEs, and agents to follow.

## Proposed Change
### 1. Keep automatic worktrees for clearly parallel work
Preserve the current behavior for parallel `feat/` partitions discovered from `approach.md` with `depends_on: []`. This is now represented explicitly in `.cicadas/config.json` under `auto_worktrees.parallel_features`, which defaults to `true`.

### 2. Make initiative and lightweight worktrees explicit instead of unconditional
Kickoff and lightweight `fix/`, `tweak/`, and `skill/` branches no longer silently create sibling worktrees by default. Shared config now supports:
- `auto_worktrees.initiatives`
- `auto_worktrees.lightweight`
- `auto_worktrees.parallel_features`

`kickoff.py` and `branch.py` also accept `--worktree` to opt in explicitly for a given operation.

### 3. Fix branch creation to base directly on the intended parent ref
`branch.py` now creates branches directly from the intended parent ref (`git branch <name> <parent>` for worktree flows, `git checkout -b <name> <parent>` for plain flows) instead of relying on a prior checkout side effect in the main workspace.

### 4. Improve worktree discoverability in status and command output
`status.py` now reports initiative worktrees as well as branch worktrees. `check.py` warns on stale initiative worktrees, and worktree-creating flows now print a clearer “open this worktree” path for the builder or agent.

### 5. Cover the behavior with integration tests
Add tests for:
- kickoff without auto-worktree by default
- lightweight branches without auto-worktree by default
- explicit worktree-enabled flows
- direct parent-ref branch creation
- status output for initiative worktrees

### Scope guard
If this requires redesigning Cicadas lifecycle semantics or introducing a broad workspace-management subsystem, stop and upgrade this to a full initiative.

## Tasks
- [x] Change kickoff and lightweight branch defaults so worktree creation is opt-in or config-driven, while preserving auto-worktrees for parallel feature partitions <!-- id: 10 -->
- [x] Fix branch creation to use the intended parent ref directly instead of relying on checkout side effects <!-- id: 11 -->
- [x] Update status and related UX so initiative worktrees are discoverable and worktree paths are clearly surfaced to builders and agents <!-- id: 12 -->
- [x] Add integration tests covering the new defaults, explicit worktree flows, and initiative worktree visibility <!-- id: 13 -->
- [x] Verify the revised behavior still supports parallel work without regressing registry consistency <!-- id: 14 -->
- [x] Significance Check: Does this warrant a Canon update? No. This changes Cicadas workflow ergonomics and script defaults, but it does not change the core methodology or product canon. <!-- id: 15 -->
