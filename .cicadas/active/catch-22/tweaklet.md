# Tweak: catch-22

## Intent
Implement a 1-PR flow for archiving initiatives to resolve the "catch-22" where a second PR was needed to finalize canon updates and registry cleanup.

## Changes

### 1. `archive.py` (Metadata Snapshot)
- Modify `archive` to save a `.cicadas_metadata.json` snapshot inside the folder being archived *before* moving it and deleting the registry entry.
- The snapshot will contain the full initiative entry from `registry.json`.
- This ensures the move to `archive/` is final in git history but fully restorable by local tools.

### 2. `unarchive.py` (Restore from Snapshot) [NEW]
- Create a new script to find the most recent archive for a given initiative name.
- Restore the `registry.json` entry from `.cicadas_metadata.json`.
- Move the archived folder back to `.cicadas/active/`.
- Delete the temporary metadata snapshot.

### 3. `open_pr.py` (Process Guard)
- Update to check if an initiative's specs are still in `active/`. 
- Strongly recommend running `archive` (pre-PR) to include finalization in the main PR.

### 4. `lifecycle-default.json` (Methodology Update)
- Update the `complete_initiative` step to recommend:
  `Synthesize Canon → Archive → Open PR → Merge`.

## Tests
### Automated Tests (`tests/test_unarchive.py`)
- **Test Archive-with-Metadata**: Verify `archive.py` creates the `.cicadas_metadata.json` snapshot.
- **Test Unarchive**: Verify `unarchive.py` restores the registry entry and active folder perfectly from a snapshot.

### Manual Verification
1. `init` a test initiative and `archive` it.
2. Verify it is removed from `status` and moved to `archive/` with metadata.
3. Run `unarchive` and verify it's back in `active/` and visible in `status`.
4. Run `archive` again, commit, and verify the PR contains the archive move and registry deletion.