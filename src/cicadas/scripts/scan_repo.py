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

from utils import (
    REPO_CONTEXT_FILENAME,
    REPO_METADATA_FILENAME,
    REPO_TREE_FILENAME,
    _meaningful_runtime_areas,
    _meaningful_test_roots,
    canon_dir,
    entry_counts_toward_complexity,
    generate_repo_context,
    get_project_root,
    infer_repo_mode_from_signals,
    save_repo_context,
    save_repo_metadata,
    scale_exclusion_reason,
)


SKIP_DIRS = {".git"}
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
}

BUILD_PATHS = {"pyproject.toml", "package.json", "Makefile", "Dockerfile", "install.sh"}


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
    build_paths: list[str]
    test_paths: list[str]
    runtime_paths: list[str]
    ownership_zone_candidates: list[str]
    mode: str
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
    return {
        "path": rel,
        "kind": "file",
        "bytes": stat.st_size,
        "extension": extension,
        "language": language,
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
    build_paths: set[str] = set()
    test_paths: set[str] = set()

    file_entries: list[dict] = []
    reporter.phase(f"Scanning {len(file_paths)} files into {tree_path.name}")
    scan_started_at = time.monotonic()
    with ThreadPoolExecutor(max_workers=min(32, (os.cpu_count() or 4) * 2)) as pool:
        for idx, result in enumerate(pool.map(lambda path: _summarize_file(path, root, gitignored_paths), file_paths), start=1):
            if result:
                file_entries.append(result)
            reporter.progress("File scan", idx, len(file_paths), scan_started_at)

    reporter.phase("Writing directory summaries")
    with tree_path.open("w") as tree_file:
        for entry in file_entries:
            tree_file.write(json.dumps(entry, sort_keys=True))
            tree_file.write("\n")

            language = entry.get("language")
            if language:
                dominant_languages[language] += 1

            rel = entry["path"]
            if rel in BUILD_PATHS:
                build_paths.add(rel)
            if rel.startswith("tests"):
                test_paths.add(rel.split("/", 1)[0])

            parent_rel = _parent_rel(rel)
            parent_stats = dir_stats.setdefault(parent_rel, DirectoryStats(path=parent_rel))
            parent_stats.file_count += 1
            ext = entry.get("extension") or "unknown"
            type_name = ext.lstrip(".") or "unknown"
            parent_stats.direct_type_counts[type_name] = parent_stats.direct_type_counts.get(type_name, 0) + 1
            for ancestor_rel in _ancestor_chain(rel):
                dir_stats.setdefault(ancestor_rel, DirectoryStats(path=ancestor_rel)).total_bytes += entry.get("bytes", 0)

        directory_entries = [
            _summarize_directory_from_stats(rel_path, stats, gitignored_paths)
            for rel_path, stats in sorted(dir_stats.items())
        ]
        for entry in directory_entries:
            tree_file.write(json.dumps(entry, sort_keys=True))
            tree_file.write("\n")

    top_level_entries = [
        entry["path"]
        for entry in directory_entries
        if entry.get("path") != "." and "/" not in entry.get("path", "").strip(".") and entry_counts_toward_complexity(entry)
    ]
    runtime_paths = _meaningful_runtime_areas(directory_entries)[:8]
    ownership_zone_candidates = runtime_paths[:8]
    mode, evidence, heuristic_scores = infer_repo_mode_from_signals(
        top_level_dirs=top_level_entries,
        build_paths=sorted(build_paths),
        test_paths=sorted(test_paths),
        runtime_paths=runtime_paths,
    )
    reporter.done(f"Inventory complete: {len(file_paths)} files, {len(directory_entries)} directories")
    return ScanSummary(
        tree_path=tree_path,
        directory_entries=directory_entries,
        top_level_entries=top_level_entries,
        dominant_languages=dict(dominant_languages),
        build_paths=sorted(build_paths),
        test_paths=sorted(test_paths),
        runtime_paths=runtime_paths,
        ownership_zone_candidates=ownership_zone_candidates,
        mode=mode,
        evidence=evidence,
        heuristic_scores=heuristic_scores,
    )


def build_repo_metadata(root: Path, summary: ScanSummary) -> dict:
    canon_plan = {
        "orientation": ["product-overview.md", "tech-overview.md", "summary.md"],
        "routing": ["routing-guide.md"] if summary.mode in {"large-repo", "mega-repo"} else [],
        "area": ["areas/"] if summary.mode in {"large-repo", "mega-repo"} else [],
        "playbooks": ["playbooks/"] if summary.mode == "mega-repo" else [],
        "module_snapshots": "selective" if summary.mode in {"large-repo", "mega-repo"} else "full",
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
            "top_level_entries": len(summary.top_level_entries),
            "dominant_languages": top_languages,
            "build_paths": summary.build_paths,
            "test_paths": summary.test_paths[:8],
            "runtime_paths": summary.runtime_paths,
            "ownership_zone_candidates": summary.ownership_zone_candidates,
        },
        "classification": {
            "decision": summary.mode,
            "confidence": "medium",
            "heuristic_scores": summary.heuristic_scores,
            "evidence": summary.evidence,
            "ambiguous_with": ["mega-repo"] if summary.mode == "large-repo" else (["large-repo"] if summary.mode == "normal-repo" else []),
            "decision_note": f"Auto-classified from structural scan of {root.name}.",
        },
        "canon_plan": canon_plan,
        "depth_policy": {
            "deep": summary.ownership_zone_candidates[:3],
            "shallow": summary.ownership_zone_candidates[3:5],
            "deferred": summary.ownership_zone_candidates[5:8],
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
