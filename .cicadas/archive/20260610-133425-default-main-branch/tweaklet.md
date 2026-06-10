# Tweaklet: Default Main Branch

## Intent
Default Cicadas greenfield git branch behavior to `main` instead of `master`. New temporary or newly initialized repositories should use `main` when Cicadas creates or assumes the initial branch, while existing repositories that already use `master` or another configured default branch should continue to work.

## Proposed Change
- Update default branch detection fallback behavior in `src/cicadas/scripts/utils.py` so a repo with no remote HEAD and no local `main` branch falls back to `main` rather than `master`.
- Update greenfield test fixtures and expectations that explicitly initialize temporary repositories with `--initial-branch=master` only where the test is not specifically exercising legacy `master` compatibility.
- Preserve compatibility paths that detect an existing `master` branch or an explicit remote default branch.
- Keep documentation wording aligned where it describes lightweight or initiative merges to the default branch.

## Tasks
- [x] Update `get_default_branch()` fallback behavior for greenfield repositories <!-- id: 10 -->
- [x] Update affected greenfield test setup and assertions to expect `main` by default <!-- id: 11 -->
- [x] Add or preserve coverage proving existing `master` repositories are still detected correctly <!-- id: 12 -->
- [x] Verify with focused tests for branch/default-branch behavior <!-- id: 13 -->
- [x] Significance Check: Does this warrant a Canon update? No; this is a default-value and test-fixture tweak with no durable Canon change. <!-- id: 14 -->
