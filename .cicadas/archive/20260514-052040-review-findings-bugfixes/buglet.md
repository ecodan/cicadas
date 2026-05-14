---
summary: "Fix code review findings 1-7: init preservation, synthesis apply path safety, portable git tests, graph test-edge streaming, token log concurrency, active-dir naming consistency, and module path containment."
phase: "bug-fix"
when_to_load:
  - "When implementing or reviewing the review findings bug-fix batch"
depends_on:
  - "Code review findings from May 2026"
modules:
  - "src/cicadas/scripts/init.py"
  - "src/cicadas/scripts/synthesize.py"
  - "src/cicadas/scripts/graph_extract/python.py"
  - "src/cicadas/scripts/graph_extract/java.py"
  - "src/cicadas/scripts/tokens.py"
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/archive.py"
  - "src/cicadas/scripts/prune.py"
  - "tests"
index:
  tasks: "## Tasks"
next_section: "Tasks"
---

# Buglet: Review Findings Bug Fixes

## Problem

The full code review found seven correctness, security, concurrency, and test-portability defects that should be fixed before submitting the current codebase.

## Scope

- Preserve existing Cicadas state when `init` is rerun.
- Prevent path traversal writes from `synthesize --apply`.
- Make git-backed tests deterministic regardless of local default branch configuration.
- Restore graph `tests` edges when extraction streams batches through `emit`.
- Make token log appends concurrency-safe.
- Use one active-spec directory naming rule across branch/archive/prune/synthesis flows.
- Keep module-derived code context reads contained inside the project root.

## Non-Goals

- Broad Ruff cleanup beyond changed files.
- Canon synthesis or archive cleanup.
- Graph feature redesign beyond the missing test-edge bug.

## Tasks

- [x] Preserve existing registry/index/config in `init.py` and cover rerun behavior.
- [x] Harden `synthesize.apply_response()` against canon path traversal and add tests.
- [x] Make git test fixtures deterministic across `main`/`master` defaults.
- [x] Fix streamed Python and Java graph extraction so `tests` edges are emitted.
- [x] Add concurrency-safe token log appends with regression coverage.
- [x] Centralize active directory naming and apply it to archive/prune/synthesis flows.
- [x] Reject out-of-repo module path context collection and add regression coverage.
- [x] Run focused tests and full project tests with plugin autoload disabled.
