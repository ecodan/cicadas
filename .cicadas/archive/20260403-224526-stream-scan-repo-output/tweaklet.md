# Tweaklet: stream-scan-repo-output

## Intent
Reduce `scan-repo` peak memory usage on large and mega repositories by writing file inventory entries to `repo-tree.jsonl` as scanning progresses instead of accumulating the full file-entry list in memory first.

## Proposed Change
Refactor `src/cicadas/scripts/scan_repo.py` so `scan_repository()` opens `repo-tree.jsonl` before the file-summary phase and appends each summarized file entry as soon as it is produced. Keep only bounded aggregate state in memory for downstream classification and context generation, such as directory stats, dominant languages, test surfaces, build/runtime path hints, and counters needed for repo-mode detection. Preserve the existing output schema, directory-summary emission, and progress reporting behavior.

Add or update tests in `tests/test_scan_repo.py` to verify that scanning still produces the expected artifacts and that `scan_repository()` spools file entries to disk during inventory construction rather than waiting until all file summaries have been accumulated.

## Tasks
- [ ] Implement streaming `repo-tree.jsonl` writes in `scan_repository()` while preserving summary accuracy <!-- id: 10 -->
- [ ] Verify scan output and regression coverage for the spool-to-disk path <!-- id: 11 -->
- [ ] Significance Check: Does this warrant a Canon update? <!-- id: 12 -->
