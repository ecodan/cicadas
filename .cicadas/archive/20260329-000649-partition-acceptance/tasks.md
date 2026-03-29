
# Tasks: Partition Acceptance

## Partition 1: Templates (`feat/partition-spec-templates`)

- [x] Edit `src/cicadas/templates/approach.md`: add `#### Artifact Type`, `#### How to Run`, `#### Acceptance Criteria` subsections to each partition example block (before `#### Implementation Steps`) <!-- id: 1 -->
- [x] Edit `src/cicadas/emergence/approach.md`: add Step 4b — Per-Partition Evaluator Sections (artifact type inference, AC generation by artifact type, How to Run from tooling detection, `<!-- NEEDS MANUAL REVIEW -->` flagging) <!-- id: 2 -->
- [ ] Open PR: feat/partition-spec-templates → initiative/partition-acceptance <!-- id: 3 -->

## Partition 2: Event Log Infrastructure (`feat/event-log-infrastructure`)

- [x] Create `src/cicadas/scripts/emit_event.py`: append typed event to `events.jsonl` with `flock`; accept `--initiative`, `--type`, `--data`; validate initiative name; create file/dir if absent <!-- id: 10 -->
- [x] Create `src/cicadas/scripts/get_events.py`: read and filter `events.jsonl`; accept `--initiative`, `--type`, `--since`, `--last`; output JSONL to stdout; handle missing file gracefully <!-- id: 11 -->
- [x] Create `tests/test_emit_event.py`: test file creation, valid event structure, concurrent writes (threading), initiative name validation <!-- id: 12 -->
- [x] Create `tests/test_get_events.py`: test all filters, empty output for missing file, chronological sort <!-- id: 13 -->
- [ ] Open PR: feat/event-log-infrastructure → initiative/partition-acceptance <!-- id: 14 -->

## Partition 3: Event Integration & Documentation (`feat/event-integration`)

- [x] Edit `kickoff.py`: emit `initiative.kicked_off` after successful registration (`check=False`) <!-- id: 20 -->
- [x] Edit `branch.py`: emit `branch.created` after registration; emit `worktree.created` when worktree is created (`check=False` for both) <!-- id: 21 -->
- [x] Edit `archive.py`: emit `specs.archived` after archive move (`check=False`) <!-- id: 22 -->
- [x] Edit `open_pr.py`: emit `pr.opened` on success, `pr.blocked` on BLOCK verdict (`check=False`) <!-- id: 23 -->
- [x] Edit `status.py`: call `get_events --last 5` per active initiative and append to status output; handle missing `events.jsonl` gracefully <!-- id: 24 -->
- [x] Edit `src/cicadas/implementation.md`: add Rule 9 (emit `task.complete` after each task checkbox) and Rule 10 (emit `partition.complete` with `summary`, `canon_entry`, `notes_for_evaluator` when all partition tasks done) <!-- id: 25 -->
- [x] Edit `src/cicadas/SKILL.md`: add Event Log subsection to Operations (event log path, `get_events` interface, `task.complete`/`partition.complete` schemas) <!-- id: 26 -->
- [x] Run full test suite; update any assertions broken by new event emission side effects <!-- id: 27 -->
- [x] Open PR: feat/event-integration → initiative/partition-acceptance <!-- id: 28 -->
