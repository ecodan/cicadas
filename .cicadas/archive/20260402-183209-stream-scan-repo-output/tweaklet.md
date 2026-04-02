# Tweaklet: stream-scan-repo-output

## Intent
Reduce `scan-repo` peak memory usage on large and mega repositories by writing file inventory entries to `repo-tree.jsonl` as scanning progresses instead of accumulating the full file-entry list in memory first.

## Proposed Change
Refactor `src/cicadas/scripts/scan_repo.py` so `scan_repository()` opens `repo-tree.jsonl` before the file-summary phase and appends each summarized file entry as soon as it is produced. Keep only bounded aggregate state in memory for downstream classification and context generation, such as directory stats, dominant languages, test surfaces, build/runtime path hints, and counters needed for repo-mode detection. Preserve the existing output schema, directory-summary emission, and progress reporting behavior.

The implementation now streams each file entry directly to the JSONL inventory using a line-buffered file handle and updates aggregate counters in the same loop, rather than retaining a `file_entries` list. Build-structure detection and runtime/package surface detection now read from the discovered relative file-path set instead of requiring fully materialized file summaries.

`tests/test_scan_repo.py` now verifies that earlier file entries are already present on disk while later files are still being summarized, in addition to preserving the existing artifact-shape coverage.

## Tasks
- [x] Implement streaming `repo-tree.jsonl` writes in `scan_repository()` while preserving summary accuracy <!-- id: 10 -->
- [x] Verify scan output and regression coverage for the spool-to-disk path <!-- id: 11 -->
- [x] Significance Check: No Canon update needed because the change only affects scan-time memory behavior and preserves the existing artifacts and workflow contract <!-- id: 12 -->
