# Tweaklet: worktree-support

## Intent

Make `kickoff.py` create a git worktree for every initiative/tweak/fix/skill branch, so multiple Cicadas work streams can run simultaneously without shell sessions stomping on each other's checked-out branch.

## Proposed Change

### 1. `utils.py` — add `get_registry_root()`

Add a function that detects whether the current working directory is a linked worktree (`.git` is a file, not a directory) and, if so, walks up to find the primary worktree (where `.git` is a real directory). All registry reads/writes (`registry.json`, `index.json`) must go through this root so the primary worktree's copy stays authoritative.

### 2. All scripts — route registry I/O through `get_registry_dir()`

Added `get_registry_dir()` convenience helper to utils.py. Updated `registry.json` and `index.json` load/save calls in: `kickoff.py`, `archive.py`, `branch.py`, `prune.py`, `abort.py`, `signalboard.py`, `update_index.py`, `status.py`, `check.py`. Spec file paths (active/, drafts/, archive/) continue to use `get_project_root()` — they live on the branch and are intentionally per-branch.

### 3. `kickoff.py` — create worktree, stay on current branch

Changed `git checkout -b initiative/{name}` to `git branch initiative/{name}` (no checkout). After branch creation, calls `create_worktree()` at `../{repo}-initiative-{name}`. Stores the worktree path in the registry entry under `"worktree_path"`.

### 4. `archive.py` — added initiative worktree removal

Branch worktree removal was already correct. Added initiative-level worktree removal (using `"worktree_path"` from registry entry) since kickoff now creates worktrees for initiatives too.

### Worktree naming convention

`../{repo-name}-{branch-type}-{name}` — e.g. for repo `cicadas` and branch `tweak/worktree-support`: `../cicadas-tweak-worktree-support`.

### 5. `branch.py` — worktrees for fix/tweak/skill branches

Extended the worktree condition in `branch.py`: fix/, tweak/, and skill/ branches now always use worktrees (previously only parallel feat/ partitions with `depends_on: []` did). Main worktree stays on parent branch.

### Divergence from plan

`branch.py` change was added (not in original tweaklet) — required to complete the use case: if only kickoff created worktrees but `branch.py` still did checkout for fix/tweak/skill, the main worktree would still switch. Also: `base.py` tearDown updated to clean up worktrees created during tests.

### Out of scope (unchanged)

- `status.py` already displays worktree paths from the registry — no structural changes.
- No changes to emergence modules, templates, or spec lifecycle.

## Tasks
- [x] Add `get_registry_root()` to `utils.py` <!-- id: 10 -->
- [x] Update registry I/O in all scripts to use `get_registry_dir()` for `registry.json` and `index.json` <!-- id: 11 -->
- [x] Update `kickoff.py` to create a worktree after branch creation and store path in registry <!-- id: 12 -->
- [x] Verify `archive.py` reads worktree path from registry entry (added initiative worktree removal) <!-- id: 13 -->
- [x] Add/update tests for `get_registry_root()` and the kickoff worktree flow <!-- id: 14 -->
- [ ] Significance Check: Does this warrant a Canon update? <!-- id: 15 -->
