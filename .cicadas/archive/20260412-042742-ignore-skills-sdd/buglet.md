---
summary: "scan_repository traverses SDD installs and skill dirs at arbitrary paths, inflating scale/complexity metrics and polluting slice candidates"
phase: "bug"
modules:
  - "src/cicadas/scripts/scan_repo.py"
  - "src/cicadas/scripts/utils.py"
---

# Buglet: ignore-skills-sdd

## Problem Description

When `scan_repository` (called by `graph build`, `scan`, and bootstrap) traverses the project tree, it fully descends into SDD (spec-driven development) installs and agent skill directories that are not in the hard-coded `SKIP_DIRS` set. Such directories — e.g. a Cicadas install at `tools/cicadas/` or a skill bundle at `src/skills/foo/` — contain many `.md` files (`emergence/`, `templates/`, `SKILL.md`) that are not project code. These files inflate `meaningful_file_count` and `estimated_loc`, potentially bumping a `normal-repo` to `large-repo` or `mega-repo`, and they surface as top-level code zones or slice candidates that have no relevance to the host project.

Currently excluded: `.cicadas/`, `.cicadas-skill/`, `.agents/`, `.claude/` (via `SKIP_DIRS` and `EXCLUDED_COMPLEXITY_PREFIXES`).  
Not excluded: SDD installs or skill bundles at any other path.

## Reproduction Steps

1. Create a project with Cicadas (or any SDD toolset) installed at a non-standard path, e.g. `tools/cicadas/`, containing `SKILL.md`, `emergence/`, and `templates/`.
2. Run `python src/cicadas/scripts/cicadas.py graph build` (or trigger a scan directly via `scan_repo.py`).
3. Observe that `meaningful_file_count` includes `.md` files from `tools/cicadas/emergence/` and `tools/cicadas/templates/`, inflating the scale classification and/or adding `tools/cicadas` as a slice candidate.

## Proposed Fix

Three mechanisms, all in `scan_repo.py` and `utils.py`:

### 1 — SKILL.md detection (SDD installs + agent skill bundles)

In `scan_repository`'s `os.walk` loop, skip any subdirectory containing a `SKILL.md` file:

```python
dirnames[:] = sorted(
    name for name in dirnames
    if name not in SKIP_DIRS
    and not (Path(current_root) / name / "SKILL.md").exists()
    and not _is_sdd_state_dir(name, is_root_child=(Path(current_root) == root))
)
```

### 2 — Known SDD state dir detection (working/output dirs)

Add a helper `_is_sdd_state_dir(name, is_root_child)` in `scan_repo.py`:

- If `is_root_child` and `name` starts with `.` or `_`: check if the lowercased name contains any known SDD tool substring.
- Known substrings: `{"bmad", "cicadas", "gsd", "openspec"}`.
- The root-child + `.`/`_` prefix guard prevents false positives in source trees (e.g. a package named `gsd-parser/` deep in `src/` is left alone).

```python
_SDD_SUBSTRINGS = frozenset({"bmad", "cicadas", "gsd", "openspec"})

def _is_sdd_state_dir(name: str, is_root_child: bool) -> bool:
    if not is_root_child:
        return False
    if not (name.startswith(".") or name.startswith("_")):
        return False
    lower = name.lower()
    return any(sub in lower for sub in _SDD_SUBSTRINGS)
```

`.cicadas` is already in `SKIP_DIRS`, so it never reaches this helper — the substring check is strictly additive coverage.

### 3 — Config-based exclusions (long tail)

Read `scan_exclude_paths` from `.cicadas/config.json` (string list, default `[]`) in `scan_repository` and add those paths to the effective skip set. Paths are relative to the project root and matched as prefixes. Document the key in `utils.py`'s `load_config` comment.

```json
{
  "scan_exclude_paths": ["_bmad-output", "vendor/some-sdd-tool"]
}
```

No changes needed to `scale_exclusion_reason` or `entry_counts_toward_complexity` — skipped directories are never enumerated, so those functions are never called for their contents.

## Tasks
- [x] Add tests: (a) scan with a fake SDD install dir (`SKILL.md` present) — assert files excluded; (b) scan with a root-level `_bmad-output/` dir — assert excluded; (c) scan with a deep `src/gsd-parser/` dir — assert NOT excluded <!-- id: 0 -->
- [x] Add `_SDD_SUBSTRINGS` constant and `_is_sdd_state_dir()` helper to `scan_repo.py` <!-- id: 1 -->
- [x] Extend `dirnames` filter in `scan_repository` with SKILL.md check + `_is_sdd_state_dir` check <!-- id: 2 -->
- [x] Read `scan_exclude_paths` from config in `scan_repository` and apply as additional skip prefixes <!-- id: 3 -->
- [x] Verify all tests pass, no regressions <!-- id: 4 -->
- [x] Significance Check: Does not warrant a Canon update (additive exclusion only, no API surface change) <!-- id: 5 -->
