# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
import re
import tomllib

from utils import (
    REPO_CONTEXT_FILENAME,
    REPO_METADATA_FILENAME,
    REPO_TREE_FILENAME,
    _meaningful_runtime_areas,
    canon_dir,
    entry_counts_toward_complexity,
    generate_repo_context,
    get_project_root,
    save_repo_context,
    save_repo_metadata,
    scale_exclusion_reason,
)


SKIP_DIRS = {".git", ".cicadas", ".cicadas-skill"}
LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".md": "markdown",
    ".sh": "shell",
    ".toml": "toml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".rs": "rust",
    ".xml": "xml",
}

LOC_EXTENSIONS = {
    ".py", ".md", ".sh", ".toml", ".json", ".yaml", ".yml", ".js", ".ts", ".tsx", ".java", ".kt", ".kts", ".rs", ".xml",
    ".gradle", ".bazel",
}


@dataclass
class DirectoryStats:
    path: str
    child_dir_count: int = 0
    file_count: int = 0
    total_bytes: int = 0
    direct_type_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class ScanSummary:
    tree_path: Path
    directory_entries: list[dict]
    top_level_entries: list[str]
    dominant_languages: dict[str, int]
    meaningful_file_count: int
    estimated_loc: int
    total_file_count: int
    build_paths: list[str]
    test_paths: list[str]
    runtime_package_surfaces: list[str]
    major_code_zones: list[str]
    build_systems: list[str]
    declared_modules: list[str]
    mode: str
    scale_class: str
    topology_class: str
    canon_strategy: str
    evidence: list[dict]
    heuristic_scores: dict


class ProgressReporter:
    def __init__(self, mode: str = "auto", stream=None):
        self.stream = stream or sys.stderr
        self.enabled = mode == "on" or (mode == "auto" and hasattr(self.stream, "isatty") and self.stream.isatty())
        self._interactive = bool(self.enabled and hasattr(self.stream, "isatty") and self.stream.isatty())
        self._last_update = 0.0

    def phase(self, message: str) -> None:
        if not self.enabled:
            return
        self._write(message, ephemeral=self._interactive)

    def progress(self, label: str, completed: int, total: int, start_time: float) -> None:
        if not self.enabled or total <= 0:
            return
        now = time.monotonic()
        if completed < total and completed != 1 and completed % 250 != 0 and (now - self._last_update) < 1.0:
            return
        elapsed = max(now - start_time, 0.001)
        rate = completed / elapsed
        remaining = max(total - completed, 0)
        eta = remaining / rate if rate > 0 else None
        percent = (completed / total) * 100
        eta_str = _format_duration(eta) if eta is not None else "unknown"
        self._write(
            f"{label}: {completed}/{total} ({percent:.1f}%) at {rate:.0f}/s, ETA {eta_str}",
            ephemeral=completed < total and self._interactive,
        )
        self._last_update = now

    def done(self, message: str) -> None:
        if not self.enabled:
            return
        self._write(message, ephemeral=False)

    def _write(self, message: str, ephemeral: bool) -> None:
        if ephemeral:
            self.stream.write(f"\r[scan-repo] {message:<100}")
        else:
            if self._interactive:
                self.stream.write("\r")
            self.stream.write(f"[scan-repo] {message}\n")
        self.stream.flush()


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    rounded = max(0, int(round(seconds)))
    minutes, secs = divmod(rounded, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _safe_stat(path: Path) -> os.stat_result | None:
    try:
        return path.stat()
    except OSError:
        return None


def _is_gitignored_path(rel_path: str, gitignored_paths: set[str]) -> bool:
    normalized = rel_path.strip("/")
    if not normalized:
        return False
    parts = normalized.split("/")
    for idx in range(len(parts), 0, -1):
        candidate = "/".join(parts[:idx])
        if candidate in gitignored_paths:
            return True
    return False


def _scale_metadata(rel_path: str, gitignored_paths: set[str]) -> dict:
    reason = "gitignored" if _is_gitignored_path(rel_path, gitignored_paths) else scale_exclusion_reason(rel_path)
    metadata = {"counts_toward_scale": reason is None}
    if reason is not None:
        metadata["scale_exclusion_reason"] = reason
    return metadata


def _list_gitignored_paths(root: Path, relative_paths: list[str]) -> set[str]:
    if not relative_paths:
        return set()
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            cwd=root,
            input="\n".join(relative_paths) + "\n",
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return set()
    if proc.returncode not in {0, 1}:
        return set()
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def _parent_rel(rel_path: str) -> str:
    if rel_path in {"", "."} or "/" not in rel_path:
        return "."
    return rel_path.rsplit("/", 1)[0]


def _ancestor_chain(rel_path: str) -> list[str]:
    normalized = rel_path.strip("/")
    if not normalized:
        return ["."]
    parts = normalized.split("/")
    return ["." if idx == 0 else "/".join(parts[:idx]) for idx in range(0, len(parts))]


def _summarize_file(path: Path, root: Path, gitignored_paths: set[str]) -> dict | None:
    stat = _safe_stat(path)
    if stat is None:
        return None
    rel = path.relative_to(root).as_posix()
    extension = path.suffix.lower()
    language = LANGUAGE_BY_EXTENSION.get(extension)
    summary = f"{path.name} in {path.parent.relative_to(root).as_posix() or '.'}"
    estimated_loc = _estimate_loc(path, extension)
    return {
        "path": rel,
        "kind": "file",
        "bytes": stat.st_size,
        "extension": extension,
        "language": language,
        "estimated_loc": estimated_loc,
        "summary": summary,
        **_scale_metadata(rel, gitignored_paths),
    }


def _summarize_directory(path: Path, root: Path, children: list[dict], gitignored_paths: set[str]) -> dict:
    rel = path.relative_to(root).as_posix() if path != root else "."
    child_files = [child for child in children if child.get("kind") == "file"]
    child_dirs = [child for child in children if child.get("kind") == "directory"]
    total_bytes = sum(child.get("bytes", 0) for child in child_files) + sum(child.get("total_bytes", 0) for child in child_dirs)
    dominant_types: dict[str, int] = {}
    for child in child_files:
        ext = child.get("extension") or "unknown"
        dominant_types[ext.lstrip(".") or "unknown"] = dominant_types.get(ext.lstrip(".") or "unknown", 0) + 1
    top_types = [name for name, _count in sorted(dominant_types.items(), key=lambda item: (-item[1], item[0]))[:3]]
    summary = f"{len(child_dirs)} directories and {len(child_files)} files"
    return {
        "path": rel,
        "kind": "directory",
        "children_count": len(children),
        "total_bytes": total_bytes,
        "dominant_types": top_types,
        "summary": summary,
        **_scale_metadata(rel, gitignored_paths),
    }


def _summarize_directory_from_stats(rel_path: str, stats: DirectoryStats, gitignored_paths: set[str]) -> dict:
    top_types = [
        name
        for name, _count in sorted(stats.direct_type_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    ]
    summary = f"{stats.child_dir_count} directories and {stats.file_count} files"
    return {
        "path": rel_path,
        "kind": "directory",
        "children_count": stats.child_dir_count + stats.file_count,
        "total_bytes": stats.total_bytes,
        "dominant_types": top_types,
        "summary": summary,
        **_scale_metadata(rel_path, gitignored_paths),
    }


def _estimate_loc(path: Path, extension: str) -> int:
    if extension not in LOC_EXTENSIONS and path.name not in {"BUILD", "WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel"}:
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def _parse_package_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _parse_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _detect_build_structure(root: Path, file_paths: set[str]) -> tuple[list[str], list[str], list[str]]:
    build_systems: set[str] = set()
    declared_modules: set[str] = set()
    build_paths: set[str] = set()

    if "pom.xml" in file_paths:
        build_systems.add("maven")
        build_paths.add("pom.xml")
        content = (root / "pom.xml").read_text(errors="ignore")
        declared_modules.update(match.strip() for match in re.findall(r"<module>\s*([^<]+?)\s*</module>", content))

    gradle_files = [path for path in file_paths if Path(path).name in {"settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"}]
    if gradle_files:
        build_systems.add("gradle")
        build_paths.update(sorted(gradle_files))
        for rel_path in gradle_files:
            if Path(rel_path).name.startswith("settings.gradle"):
                content = (root / rel_path).read_text(errors="ignore")
                declared_modules.update(match.strip().replace(":", "/") for match in re.findall(r"['\"]:?(.*?)['\"]", content) if match.strip())

    bazel_files = [path for path in file_paths if Path(path).name in {"WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel"} or Path(path).suffix == ".bazel" or Path(path).name == "BUILD"]
    if bazel_files:
        build_systems.add("bazel")
        build_paths.update(sorted(bazel_files))
        declared_modules.update(sorted({str(Path(path).parent) for path in file_paths if Path(path).name in {"BUILD", "BUILD.bazel"}} - {"."}))

    if "package.json" in file_paths:
        package_data = _parse_package_json(root / "package.json")
        build_systems.add("node")
        build_paths.add("package.json")
        workspaces = package_data.get("workspaces", [])
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("packages", [])
        declared_modules.update(workspaces if isinstance(workspaces, list) else [])
    if "pnpm-workspace.yaml" in file_paths:
        build_systems.add("pnpm")
        build_paths.add("pnpm-workspace.yaml")
        content = (root / "pnpm-workspace.yaml").read_text(errors="ignore")
        declared_modules.update(match.strip().strip("'\"") for match in re.findall(r"^\s*-\s+(.+?)\s*$", content, re.MULTILINE))
    if any(path in file_paths for path in {"yarn.lock", ".yarnrc.yml"}):
        build_systems.add("yarn")
        build_paths.update(path for path in {"yarn.lock", ".yarnrc.yml"} if path in file_paths)

    if "pyproject.toml" in file_paths:
        build_systems.add("python")
        build_paths.add("pyproject.toml")
        pyproject = _parse_toml(root / "pyproject.toml")
        tool_data = pyproject.get("tool", {})
        if "uv" in tool_data:
            build_systems.add("uv")
        if "hatch" in tool_data:
            build_systems.add("hatch")
        if "poetry" in tool_data:
            build_systems.add("poetry")
        if "project" in pyproject and pyproject["project"].get("name"):
            declared_modules.add(pyproject["project"]["name"])

    if "Cargo.toml" in file_paths:
        build_systems.add("cargo")
        build_paths.add("Cargo.toml")
        cargo_toml = _parse_toml(root / "Cargo.toml")
        workspace = cargo_toml.get("workspace", {})
        if isinstance(workspace.get("members"), list):
            declared_modules.update(str(item) for item in workspace["members"])
        package = cargo_toml.get("package", {})
        if package.get("name"):
            declared_modules.add(package["name"])

    return sorted(build_systems), sorted(module for module in declared_modules if module and module != "."), sorted(build_paths)


def _major_code_zones(directory_entries: list[dict]) -> list[str]:
    zones = _meaningful_runtime_areas(directory_entries)[:8]
    if zones:
        return zones
    fallback_prefixes = ("src", "app", "packages", "services", "libs")
    inferred = [
        entry.get("path", "")
        for entry in directory_entries
        if entry.get("path") != "."
        and "/" not in entry.get("path", "").strip("/")
        and entry_counts_toward_complexity(entry)
        and entry.get("path", "").split("/", 1)[0] in fallback_prefixes
    ]
    return inferred[:8]


def _code_directory_like(path: str) -> bool:
    normalized = path.strip("/")
    if not normalized or normalized == ".":
        return False
    excluded_prefixes = (
        ".",
        ".cicadas",
        ".cicadas-skill",
        "build",
        "dist",
        "docs",
        "node_modules",
        "target",
        "tmp",
        "vendor",
        "venv",
    )
    first_segment = normalized.split("/", 1)[0]
    if first_segment in excluded_prefixes or normalized.startswith(excluded_prefixes):
        return False
    return True


def _normalize_module_candidate(module: str) -> str | None:
    normalized = module.strip().strip("/")
    if not normalized:
        return None
    if normalized.startswith(":"):
        normalized = normalized.lstrip(":").replace(":", "/")
    if "*" in normalized:
        normalized = normalized.split("*", 1)[0].rstrip("/")
    if normalized in {".", ""}:
        return None
    return normalized


def _top_level_code_roots(directory_entries: list[dict]) -> list[str]:
    roots: list[str] = []
    for entry in directory_entries:
        path = entry.get("path", "")
        if path == "." or "/" in path.strip("/"):
            continue
        if not entry_counts_toward_complexity(entry):
            continue
        if not _code_directory_like(path):
            continue
        child_count = int(entry.get("children_count", 0) or 0)
        if child_count <= 0:
            continue
        roots.append(path)
    return sorted(dict.fromkeys(roots))


def _plan_candidate_slices(
    *,
    declared_modules: list[str],
    major_code_zones: list[str],
    directory_entries: list[dict],
    max_seeded: int = 3,
    max_total: int = 8,
) -> list[dict]:
    directory_paths = {entry.get("path", "") for entry in directory_entries if entry.get("kind") == "directory"}
    planned_paths: list[tuple[str, str]] = []

    for module in declared_modules:
        normalized = _normalize_module_candidate(module)
        if not normalized or not _code_directory_like(normalized):
            continue
        if normalized in directory_paths:
            planned_paths.append((normalized, "declared-module"))
            continue
        top_level = normalized.split("/", 1)[0]
        if top_level in directory_paths and _code_directory_like(top_level):
            planned_paths.append((top_level, "declared-module-root"))

    for zone in major_code_zones:
        normalized = _normalize_module_candidate(zone)
        if normalized and normalized in directory_paths and _code_directory_like(normalized):
            planned_paths.append((normalized, "major-code-zone"))

    for root in _top_level_code_roots(directory_entries):
        planned_paths.append((root, "top-level-code-root"))

    deduped: list[dict] = []
    seen_paths: set[str] = set()
    for idx, (path, reason) in enumerate(planned_paths):
        if path in seen_paths:
            continue
        deduped.append(
            {
                "name": path.replace("/", "-"),
                "paths": [path],
                "status": "seeded" if len(deduped) < max_seeded else "deferred",
                "reason": reason,
            }
        )
        seen_paths.add(path)
        if len(deduped) >= max_total:
            break
    return deduped


def _runtime_package_surfaces(file_paths: set[str], directory_entries: list[dict]) -> list[str]:
    surfaces: set[str] = set()
    for path in file_paths:
        if path in {"Dockerfile", "package.json", "pyproject.toml", "Cargo.toml", "pom.xml"}:
            surfaces.add(path)
    surfaces.update(_major_code_zones(directory_entries))
    return sorted(surfaces)[:8]


def _scale_class(meaningful_file_count: int, estimated_loc: int) -> str:
    if meaningful_file_count >= 25_000 or estimated_loc >= 2_000_000:
        return "mega-repo"
    if meaningful_file_count >= 1_000 or estimated_loc >= 100_000:
        return "large-repo"
    return "normal-repo"


def _class_rank(mode: str) -> int:
    return {"normal-repo": 1, "large-repo": 2, "mega-repo": 3}[mode]


def _canon_strategy_for_mode(mode: str, declared_modules: list[str], build_systems: list[str]) -> str:
    if mode in {"large-repo", "mega-repo"}:
        return "locality-first"
    return "flat"


def _classify_repo(
    meaningful_file_count: int,
    estimated_loc: int,
    build_systems: list[str],
    declared_modules: list[str],
    major_code_zones: list[str],
    test_paths: list[str],
    runtime_package_surfaces: list[str],
    dominant_languages: dict[str, int],
) -> tuple[str, str, str, str, list[dict], dict]:
    scale_class = _scale_class(meaningful_file_count, estimated_loc)
    topology_score = 0
    topology_score += 2 if len(declared_modules) >= 20 else 1 if len(declared_modules) >= 5 else 0
    topology_score += 1 if len(build_systems) >= 2 else 0
    topology_score += 1 if len(major_code_zones) >= 4 else 0
    topology_score += 1 if len(test_paths) >= 3 else 0
    topology_score += 1 if len(runtime_package_surfaces) >= 4 else 0
    topology_score += 1 if len(dominant_languages) >= 3 else 0

    topology_class = "mega-repo" if topology_score >= 5 else "large-repo" if topology_score >= 2 else "normal-repo"
    repo_mode = scale_class if _class_rank(scale_class) >= _class_rank(topology_class) else topology_class
    canon_strategy = _canon_strategy_for_mode(repo_mode, declared_modules, build_systems)
    heuristic_scores = {
        "meaningful_file_count": meaningful_file_count,
        "estimated_loc": estimated_loc,
        "declared_module_count": len(declared_modules),
        "major_code_zone_count": len(major_code_zones),
        "test_surface_count": len(test_paths),
        "runtime_surface_count": len(runtime_package_surfaces),
        "build_system_count": len(build_systems),
        "language_count": len(dominant_languages),
        "topology_score": topology_score,
    }
    evidence = [
        {
            "signal": "scale_floor",
            "observation": f"Detected {meaningful_file_count} meaningful files and {estimated_loc} estimated LoC, giving a scale floor of `{scale_class}`.",
            "weight": "high",
        },
        {
            "signal": "build_structure",
            "observation": f"Detected build systems {', '.join(build_systems) if build_systems else 'none'} and {len(declared_modules)} declared modules.",
            "weight": "high" if build_systems else "medium",
        },
        {
            "signal": "routing_surfaces",
            "observation": f"Observed {len(major_code_zones)} major code zones, {len(test_paths)} test surfaces, and {len(runtime_package_surfaces)} runtime/package surfaces.",
            "weight": "medium",
        },
    ]
    return scale_class, topology_class, repo_mode, canon_strategy, evidence, heuristic_scores


def scan_repository(root: Path, tree_path: Path, summary_depth: int = 2, progress: ProgressReporter | None = None) -> ScanSummary:
    root = root.resolve()
    tree_path.parent.mkdir(parents=True, exist_ok=True)
    file_paths: list[Path] = []
    dir_paths: list[Path] = [root]
    reporter = progress or ProgressReporter(mode="off")
    reporter.phase("Discovering repository paths")

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        filenames = sorted(filenames)
        current_path = Path(current_root)
        if current_path != root:
            dir_paths.append(current_path)
        for filename in filenames:
            file_paths.append(current_path / filename)
    reporter.phase(f"Discovered {len(file_paths)} files across {len(dir_paths)} directories")

    relative_file_paths = {
        path.relative_to(root).as_posix()
        for path in file_paths
    }
    relative_paths = [
        path.relative_to(root).as_posix()
        for path in sorted(file_paths + [path for path in dir_paths if path != root])
    ]
    reporter.phase("Resolving gitignored paths")
    gitignored_paths = _list_gitignored_paths(root, relative_paths)

    dir_stats: dict[str, DirectoryStats] = {".": DirectoryStats(path=".")}
    for dir_path in sorted(dir_paths, key=lambda path: path.relative_to(root).as_posix()):
        rel = dir_path.relative_to(root).as_posix() if dir_path != root else "."
        if rel not in dir_stats:
            dir_stats[rel] = DirectoryStats(path=rel)
        if rel != ".":
            parent_rel = _parent_rel(rel)
            dir_stats.setdefault(parent_rel, DirectoryStats(path=parent_rel)).child_dir_count += 1

    dominant_languages: dict[str, int] = defaultdict(int)
    test_paths: set[str] = set()
    meaningful_file_count = 0
    estimated_loc = 0

    reporter.phase(f"Scanning {len(file_paths)} files into {tree_path.name}")
    scan_started_at = time.monotonic()
    with tree_path.open("w", buffering=1) as tree_file:
        with ThreadPoolExecutor(max_workers=min(32, (os.cpu_count() or 4) * 2)) as pool:
            for idx, result in enumerate(pool.map(lambda path: _summarize_file(path, root, gitignored_paths), file_paths), start=1):
                if result:
                    tree_file.write(f"{json.dumps(result, sort_keys=True)}\n")

                    language = result.get("language")
                    if language:
                        dominant_languages[language] += 1

                    rel = result["path"]
                    if rel.startswith("tests"):
                        test_paths.add(rel.split("/", 1)[0])
                    if entry_counts_toward_complexity(result):
                        meaningful_file_count += 1
                        estimated_loc += int(result.get("estimated_loc", 0) or 0)

                    parent_rel = _parent_rel(rel)
                    parent_stats = dir_stats.setdefault(parent_rel, DirectoryStats(path=parent_rel))
                    parent_stats.file_count += 1
                    ext = result.get("extension") or "unknown"
                    type_name = ext.lstrip(".") or "unknown"
                    parent_stats.direct_type_counts[type_name] = parent_stats.direct_type_counts.get(type_name, 0) + 1
                    for ancestor_rel in _ancestor_chain(rel):
                        dir_stats.setdefault(ancestor_rel, DirectoryStats(path=ancestor_rel)).total_bytes += result.get("bytes", 0)

                reporter.progress("File scan", idx, len(file_paths), scan_started_at)

        reporter.phase("Writing directory summaries")

        directory_entries = [
            _summarize_directory_from_stats(rel_path, stats, gitignored_paths)
            for rel_path, stats in sorted(dir_stats.items())
        ]
        for entry in directory_entries:
            tree_file.write(f"{json.dumps(entry, sort_keys=True)}\n")

    top_level_entries = [
        entry["path"]
        for entry in directory_entries
        if entry.get("path") != "." and "/" not in entry.get("path", "").strip(".") and entry_counts_toward_complexity(entry)
    ]
    build_systems, declared_modules, build_paths = _detect_build_structure(root, relative_file_paths)
    major_code_zones = _major_code_zones(directory_entries)
    runtime_package_surfaces = _runtime_package_surfaces(relative_file_paths, directory_entries)
    scale_class, topology_class, mode, canon_strategy, evidence, heuristic_scores = _classify_repo(
        meaningful_file_count=meaningful_file_count,
        estimated_loc=estimated_loc,
        build_systems=build_systems,
        declared_modules=declared_modules,
        major_code_zones=major_code_zones,
        test_paths=sorted(test_paths),
        runtime_package_surfaces=runtime_package_surfaces,
        dominant_languages=dict(dominant_languages),
    )
    reporter.done(f"Inventory complete: {len(file_paths)} files, {len(directory_entries)} directories")
    return ScanSummary(
        tree_path=tree_path,
        directory_entries=directory_entries,
        top_level_entries=top_level_entries,
        dominant_languages=dict(dominant_languages),
        meaningful_file_count=meaningful_file_count,
        estimated_loc=estimated_loc,
        total_file_count=len(file_paths),
        build_paths=sorted(build_paths),
        test_paths=sorted(test_paths),
        runtime_package_surfaces=runtime_package_surfaces,
        major_code_zones=major_code_zones,
        build_systems=build_systems,
        declared_modules=declared_modules,
        mode=mode,
        scale_class=scale_class,
        topology_class=topology_class,
        canon_strategy=canon_strategy,
        evidence=evidence,
        heuristic_scores=heuristic_scores,
    )


def build_repo_metadata(root: Path, summary: ScanSummary) -> dict:
    module_snapshot_policy = "minimal" if summary.mode in {"large-repo", "mega-repo"} else "full"
    candidate_slices = (
        _plan_candidate_slices(
            declared_modules=summary.declared_modules,
            major_code_zones=summary.major_code_zones,
            directory_entries=summary.directory_entries,
        )
        if summary.mode in {"large-repo", "mega-repo"}
        else []
    )
    canon_plan = {
        "strategy": summary.canon_strategy,
        "orientation": ["product-overview.md", "tech-overview.md", "summary.md"],
        "historical_context": {
            "hand_edit_recommended": summary.mode in {"large-repo", "mega-repo"},
            "why": "Preserve repo history, intent, and local rationale that scan evidence cannot infer safely.",
        },
        "slice_dirs": ["slices/"] if summary.mode in {"large-repo", "mega-repo"} else [],
        "seeded_slice_count": len([slice_info for slice_info in candidate_slices if slice_info["status"] == "seeded"]),
        "minimum_slice_files": [
            "summary.md",
            "boundaries.md",
            "architecture.md",
            "invariants.md",
            "change-guide.md",
        ] if summary.mode in {"large-repo", "mega-repo"} else [],
        "module_dirs": ["modules/"] if summary.mode == "normal-repo" else [],
        "module_snapshots": module_snapshot_policy,
        "generated_targets": ["product-overview.md", "tech-overview.md", "summary.md"]
        + (["slices/"] if summary.mode in {"large-repo", "mega-repo"} else []),
    }
    top_languages = [lang for lang, _ in sorted(summary.dominant_languages.items(), key=lambda item: (-item[1], item[0]))[:3]]
    return {
        "schema_version": 1,
        "scan_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_mode": summary.mode,
        "scan": {
            "tree_path": REPO_TREE_FILENAME,
            "context_path": REPO_CONTEXT_FILENAME,
            "repo_file_count": summary.total_file_count,
            "meaningful_file_count": summary.meaningful_file_count,
            "estimated_loc": summary.estimated_loc,
            "top_level_entries": len(summary.top_level_entries),
            "dominant_languages": top_languages,
            "build_systems": summary.build_systems,
            "declared_modules": summary.declared_modules[:50],
            "major_code_zones": summary.major_code_zones,
            "build_paths": summary.build_paths,
            "test_paths": summary.test_paths[:8],
            "runtime_package_surfaces": summary.runtime_package_surfaces,
            "runtime_paths": summary.runtime_package_surfaces,
            "ownership_zone_candidates": [slice_info["paths"][0] for slice_info in candidate_slices[:8]],
        },
        "classification": {
            "decision": summary.mode,
            "scale_class": summary.scale_class,
            "topology_class": summary.topology_class,
            "confidence": "medium",
            "heuristic_scores": summary.heuristic_scores,
            "evidence": summary.evidence,
            "ambiguous_with": ["mega-repo"] if summary.mode == "large-repo" and summary.topology_class == "mega-repo" else [],
            "decision_note": f"Auto-classified from build-first structural scan of {root.name}.",
        },
        "canon_plan": canon_plan,
        "slice_strategy": (
            {
                "unit": "slice",
                "bootstrap_mode": "seeded-lazy",
                "path_policy": "contiguous-by-default",
                "allow_multi_path_when": "Only when repeated real work shows strong co-change across paths.",
                "deepen_on": ["initiative-start", "tweak-start", "bug-start"],
            }
            if summary.mode in {"large-repo", "mega-repo"}
            else {
                "unit": "module",
                "bootstrap_mode": "fuller-bootstrap",
                "deepen_on": [],
            }
        ),
        "candidate_slices": candidate_slices,
        "depth_policy": {
            "seeded": [slice_info["name"] for slice_info in candidate_slices if slice_info["status"] == "seeded"],
            "deferred": [slice_info["name"] for slice_info in candidate_slices if slice_info["status"] == "deferred"],
        },
        "validation": {
            "status": "pending",
            "checks": (
                [
                    "planned docs exist",
                    "seeded slices point to real code paths",
                    "orientation docs reflect real repo history and boundaries",
                ]
                if summary.mode in {"large-repo", "mega-repo"}
                else [
                    "planned docs exist",
                    "orientation docs reflect real repo history and boundaries",
                    "module snapshots are generated only when needed",
                ]
            ),
            "autocorrections": [],
        },
        "graph_follow_on": {
            "status": "not_available",
            "parking_lot_topics": [
                "dependency adjacency traversal",
                "blast-radius queries",
                "inside-out symbol routing",
            ],
        },
    }


def run_scan(root: Path | None = None, output: Path | None = None, summary_depth: int = 2, progress_mode: str = "auto") -> tuple[Path, Path, Path]:
    root = (root or get_project_root()).resolve()
    out_dir = output.resolve() if output else canon_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    tree_path = out_dir / REPO_TREE_FILENAME
    reporter = ProgressReporter(mode=progress_mode)

    summary = scan_repository(root, tree_path=tree_path, summary_depth=summary_depth, progress=reporter)
    metadata = build_repo_metadata(root, summary)
    context = generate_repo_context(metadata, summary.directory_entries)

    metadata_path = save_repo_metadata(metadata, out_dir)
    context_path = save_repo_context(context, out_dir)

    print(f"[OK]   wrote {tree_path}")
    print(f"[OK]   wrote {metadata_path}")
    print(f"[OK]   wrote {context_path}")
    return tree_path, metadata_path, context_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the repository and generate adaptive canon metadata")
    parser.add_argument("--root", type=Path, default=None, help="Repository root to scan (defaults to detected project root)")
    parser.add_argument("--output", type=Path, default=None, help="Directory to write canon scan artifacts (defaults to .cicadas/canon)")
    parser.add_argument("--summary-depth", type=int, default=2, help="Reserved summary depth setting for future tuning")
    parser.add_argument("--progress", choices=["auto", "on", "off"], default="auto", help="Show scan progress and ETA")
    args = parser.parse_args()

    run_scan(root=args.root, output=args.output, summary_depth=args.summary_depth, progress_mode=args.progress)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
