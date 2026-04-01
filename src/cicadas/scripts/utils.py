# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import re
import subprocess
from pathlib import Path


def get_project_root():
    """Detect .cicadas folder or .git folder to find root."""
    curr = Path.cwd()
    for parent in [curr] + list(curr.parents):
        if (parent / ".cicadas").exists() or (parent / ".git").exists():
            return parent
    return curr


def get_registry_root() -> Path:
    """Return the primary worktree root for registry I/O.

    In a linked worktree, .git is a file (not a directory) that points to the
    real gitdir at {main_repo}/.git/worktrees/{name}.  Navigate up to the main
    worktree so that registry.json and index.json are always read/written from
    the authoritative copy on the default branch.

    Falls back to get_project_root() when detection fails.
    """
    root = get_project_root()
    git_path = root / ".git"

    if git_path.is_dir():
        return root  # already the primary worktree

    if git_path.is_file():
        try:
            content = git_path.read_text().strip()
            if content.startswith("gitdir:"):
                gitdir = Path(content.split(":", 1)[1].strip())
                # Standard layout: {main}/.git/worktrees/{name}
                if gitdir.parent.name == "worktrees":
                    return gitdir.parent.parent.parent  # main repo root
        except Exception:
            pass

    return root


def get_registry_dir() -> Path:
    """Return the .cicadas directory in the primary worktree."""
    return get_registry_root() / ".cicadas"


def get_default_branch():
    """Detect the default branch (main, master, etc.) from git."""
    root = get_project_root()
    try:
        # Check symbolic-ref for the remote HEAD
        res = subprocess.check_output(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=root, stderr=subprocess.DEVNULL).decode().strip()
        return res.split("/")[-1]
    except Exception:
        # Fallback 1: check if 'main' exists locally
        try:
            subprocess.check_call(["git", "show-ref", "--verify", "--quiet", "refs/heads/main"], cwd=root)
            return "main"
        except Exception:
            # Fallback 2: return 'master'
            return "master"


def load_json(path):
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert Path objects to strings for JSON serialization
    def path_serializer(obj):
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=path_serializer)


def load_config() -> dict:
    """Load shared Cicadas config from the primary worktree."""
    return load_json(get_registry_dir() / "config.json")


REPO_METADATA_FILENAME = "repo.json"
REPO_TREE_FILENAME = "repo-tree.jsonl"
REPO_CONTEXT_FILENAME = "repo-context.md"
EXCLUDED_COMPLEXITY_PREFIXES = (
    ".agents",
    ".claude",
    ".cursor",
    ".direnv",
    ".idea",
    ".next",
    ".nuxt",
    ".tox",
    ".venv",
    ".vscode",
    ".rovodev",
    ".build",
    ".cache",
    ".coverage",
    ".cicadas/active",
    ".cicadas/archive",
    ".cicadas/drafts",
    ".cicadas/canon",
    "build",
    "coverage",
    "dist",
    "docs",
    "node_modules",
    "out",
    "target",
    "venv",
)


def canon_dir(root: Path | None = None) -> Path:
    if root is None:
        root = get_project_root()
    return root / ".cicadas" / "canon"


def repo_metadata_path(root: Path | None = None) -> Path:
    return canon_dir(root) / REPO_METADATA_FILENAME


def repo_tree_path(root: Path | None = None) -> Path:
    return canon_dir(root) / REPO_TREE_FILENAME


def repo_context_path(root: Path | None = None) -> Path:
    return canon_dir(root) / REPO_CONTEXT_FILENAME


def load_repo_metadata(canon_root: Path | None = None) -> dict | None:
    path = repo_metadata_path(canon_root if canon_root is not None else None)
    if canon_root is not None and canon_root.name == "canon":
        path = canon_root / REPO_METADATA_FILENAME
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid {REPO_METADATA_FILENAME}: {exc}") from exc


def save_repo_metadata(data: dict, canon_root: Path | None = None) -> Path:
    path = repo_metadata_path(canon_root if canon_root is not None else None)
    if canon_root is not None and canon_root.name == "canon":
        path = canon_root / REPO_METADATA_FILENAME
    save_json(path, data)
    return path


def load_repo_tree(canon_root: Path | None = None) -> list[dict] | None:
    path = repo_tree_path(canon_root if canon_root is not None else None)
    if canon_root is not None and canon_root.name == "canon":
        path = canon_root / REPO_TREE_FILENAME
    if not path.exists():
        return None

    entries: list[dict] = []
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid {REPO_TREE_FILENAME} line {lineno}: {exc}") from exc
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid {REPO_TREE_FILENAME} line {lineno}: expected object")
        entries.append(entry)
    return entries


def save_repo_tree(entries: list[dict], canon_root: Path | None = None) -> Path:
    path = repo_tree_path(canon_root if canon_root is not None else None)
    if canon_root is not None and canon_root.name == "canon":
        path = canon_root / REPO_TREE_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, sort_keys=True))
            f.write("\n")
    return path


def load_repo_context(canon_root: Path | None = None) -> str | None:
    path = repo_context_path(canon_root if canon_root is not None else None)
    if canon_root is not None and canon_root.name == "canon":
        path = canon_root / REPO_CONTEXT_FILENAME
    if not path.exists():
        return None
    return path.read_text()


def save_repo_context(text: str, canon_root: Path | None = None) -> Path:
    path = repo_context_path(canon_root if canon_root is not None else None)
    if canon_root is not None and canon_root.name == "canon":
        path = canon_root / REPO_CONTEXT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _match_path_prefix(rel_path: str, prefixes: list[str]) -> bool:
    normalized = rel_path.strip("/")
    for prefix in prefixes:
        candidate = prefix.strip("/")
        if normalized == candidate or normalized.startswith(f"{candidate}/"):
            return True
    return False


def scale_exclusion_reason(rel_path: str) -> str | None:
    normalized = rel_path.strip("/")
    if not normalized or normalized in {".git", "__pycache__"}:
        return "internal"
    if normalized.startswith(".cicadas/") and not normalized.startswith(".cicadas/canon/summary.md"):
        return "cicadas-internal"
    for prefix in EXCLUDED_COMPLEXITY_PREFIXES:
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return "generated-or-local"
    return None


def path_counts_toward_complexity(rel_path: str) -> bool:
    return scale_exclusion_reason(rel_path) is None


def entry_counts_toward_complexity(entry: dict) -> bool:
    explicit = entry.get("counts_toward_scale")
    if explicit is not None:
        return bool(explicit)
    return path_counts_toward_complexity(entry.get("path", ""))


def infer_repo_mode_from_signals(
    top_level_dirs: list[str],
    build_paths: list[str],
    test_paths: list[str],
    runtime_paths: list[str],
) -> tuple[str, list[dict], dict]:
    ownership_candidates = runtime_paths[:]

    subsystem_breadth = min(5, max(1, len(top_level_dirs) // 4 + (1 if len(top_level_dirs) >= 3 else 0)))
    layer_diversity = min(5, max(1, sum(bool(paths) for paths in [build_paths, test_paths, runtime_paths]) + (1 if len(runtime_paths) > 2 else 0)))
    ownership_zone_count = min(5, max(1, len(ownership_candidates) // 3 + (1 if len(ownership_candidates) >= 2 else 0)))
    path_diversity = min(5, max(1, int(bool(build_paths)) + int(bool(test_paths)) + (1 if len(runtime_paths) > 1 else 0)))
    routing_difficulty = min(
        5,
        max(
            1,
            ownership_zone_count
            + (1 if len(runtime_paths) > 2 else 0)
            + (1 if path_diversity >= 4 else 0),
        ),
    )

    heuristic_scores = {
        "subsystem_breadth": subsystem_breadth,
        "layer_diversity": layer_diversity,
        "ownership_zone_count": ownership_zone_count,
        "path_diversity": path_diversity,
        "routing_difficulty": routing_difficulty,
    }

    max_score = max(heuristic_scores.values())
    if ownership_zone_count <= 1 and subsystem_breadth <= 2 and len(runtime_paths) <= 2:
        mode = "normal-repo"
    elif routing_difficulty >= 4 and ownership_zone_count >= 3:
        mode = "mega-repo"
    elif max_score >= 3:
        mode = "large-repo"
    else:
        mode = "normal-repo"

    evidence = [
        {
            "signal": "top_level_subsystems",
            "observation": f"Found {len(top_level_dirs)} top-level directories worth scanning.",
            "weight": "medium",
        },
        {
            "signal": "ownership_zone_candidates",
            "observation": f"Found {len(ownership_candidates)} likely ownership zones from directory boundaries.",
            "weight": "high" if ownership_zone_count >= 4 else "medium",
        },
        {
            "signal": "path_diversity",
            "observation": f"Detected build/test/runtime path diversity across {len(build_paths)} build, {len(test_paths)} test, and {len(runtime_paths)} runtime paths.",
            "weight": "high" if path_diversity >= 4 else "medium",
        },
    ]
    return mode, evidence, heuristic_scores


def _meaningful_test_roots(entries: list[dict]) -> list[str]:
    roots = {
        entry.get("path", "").split("/", 1)[0]
        for entry in entries
        if entry.get("path", "").startswith("tests")
    }
    return sorted(root for root in roots if root)


def _meaningful_runtime_areas(dir_entries: list[dict]) -> list[str]:
    runtime_prefixes = ("src", "app", "packages", "services")
    areas: set[str] = set()
    for entry in dir_entries:
        path = entry.get("path", "")
        if not entry_counts_toward_complexity(entry):
            continue
        parts = path.split("/")
        if not parts or parts[0] not in runtime_prefixes:
            continue
        if parts[0] == "src" and len(parts) >= 2:
            areas.add("/".join(parts[:2]))
        else:
            areas.add(parts[0])
    return sorted(areas)


def build_canon_plan(repo_metadata: dict | None) -> dict:
    if not repo_metadata:
        return {
            "repo_mode": "legacy",
            "top_level": ["product-overview.md", "ux-overview.md", "tech-overview.md", "summary.md"],
            "directories": ["modules"],
            "prefer_context": False,
            "module_snapshot_policy": "full",
        }

    canon_plan = repo_metadata.get("canon_plan", {})
    top_level = list(dict.fromkeys((canon_plan.get("orientation") or []) + (canon_plan.get("routing") or [])))
    playbooks = canon_plan.get("playbooks") or []
    directories: list[str] = []
    if canon_plan.get("area"):
        directories.append("areas")
    if playbooks:
        directories.append("playbooks")
    module_policy = canon_plan.get("module_snapshots", "full")
    if module_policy != "minimal":
        directories.append("modules")
    return {
        "repo_mode": repo_metadata.get("repo_mode", "normal-repo"),
        "top_level": top_level or ["product-overview.md", "tech-overview.md", "summary.md"],
        "directories": directories,
        "prefer_context": True,
        "module_snapshot_policy": module_policy,
    }


def enumerate_canon_targets(plan: dict) -> list[str]:
    targets = list(plan.get("top_level", []))
    for directory in plan.get("directories", []):
        targets.append(f"{directory}/")
    return targets


def infer_repo_mode(repo_tree: list[dict] | None, repo_metadata: dict | None = None) -> tuple[str, list[dict], dict]:
    if repo_metadata and repo_metadata.get("repo_mode") and repo_metadata.get("classification", {}).get("heuristic_scores"):
        return (
            repo_metadata["repo_mode"],
            list(repo_metadata.get("classification", {}).get("evidence", [])),
            dict(repo_metadata.get("classification", {}).get("heuristic_scores", {})),
        )

    entries = repo_tree or []
    dir_entries = [entry for entry in entries if entry.get("kind") == "directory"]
    file_entries = [entry for entry in entries if entry.get("kind") == "file"]
    top_level_dirs = [
        entry
        for entry in dir_entries
        if "/" not in entry.get("path", "").strip("/")
        and entry_counts_toward_complexity(entry)
    ]
    build_paths = [entry["path"] for entry in file_entries if entry.get("path") in {"pyproject.toml", "package.json", "Makefile", "Dockerfile", "install.sh"}]
    test_paths = _meaningful_test_roots(entries)
    runtime_paths = _meaningful_runtime_areas(dir_entries)
    return infer_repo_mode_from_signals(
        top_level_dirs=[entry.get("path", "") for entry in top_level_dirs],
        build_paths=build_paths,
        test_paths=test_paths,
        runtime_paths=runtime_paths,
    )


def generate_repo_context(repo_metadata: dict, repo_tree: list[dict] | None = None) -> str:
    repo_mode = repo_metadata.get("repo_mode", "unknown")
    scan = repo_metadata.get("scan", {})
    dominant_languages = scan.get("dominant_languages", [])
    build_paths = scan.get("build_paths", [])
    test_paths = scan.get("test_paths", [])
    runtime_paths = scan.get("runtime_paths", [])
    ownership = scan.get("ownership_zone_candidates", [])
    lines = [
        "# Repo Context",
        "",
        f"- Repo mode candidate: `{repo_mode}`",
        f"- Dominant languages: {', '.join(f'`{lang}`' for lang in dominant_languages) if dominant_languages else '`unknown`'}",
        "- Highest-signal areas:",
    ]
    if ownership:
        for path in ownership[:5]:
            lines.append(f"  - `{path}`")
    else:
        lines.append("  - `unknown`")
    lines.extend(
        [
            "- Build/test/runtime paths:",
            f"  - Build: {', '.join(f'`{path}`' for path in build_paths) if build_paths else '`unknown`'}",
            f"  - Test: {', '.join(f'`{path}`' for path in test_paths) if test_paths else '`unknown`'}",
            f"  - Runtime: {', '.join(f'`{path}`' for path in runtime_paths) if runtime_paths else '`unknown`'}",
        ]
    )
    if ownership:
        lines.append(f"- Routing note: Start with `{ownership[0]}` and expand to neighboring areas only if needed.")
    elif repo_tree:
        first = next(
            (
                entry.get("path")
                for entry in repo_tree
                if entry.get("kind") == "directory" and entry.get("path") and entry_counts_toward_complexity(entry)
            ),
            None,
        )
        lines.append(f"- Routing note: Start with `{first}`." if first else "- Routing note: Start with top-level runtime paths.")
    return "\n".join(lines) + "\n"


def collect_code_context(root: Path, modules: list[str], repo_tree: list[dict] | None = None) -> dict[str, str]:
    code_context: dict[str, str] = {}
    matched_any = False
    normalized_modules = [module.strip() for module in modules if module.strip()]
    for mod in normalized_modules:
        mod_path = root / "src" / mod.replace(".", "/")
        if not mod_path.exists():
            mod_path = root / mod.replace(".", "/")

        if mod_path.exists():
            matched_any = True
            for py_file in mod_path.glob("**/*.py"):
                rel_path = py_file.relative_to(root)
                code_context[str(rel_path)] = py_file.read_text()

    if matched_any or not repo_tree:
        return code_context

    high_signal_files = [
        entry.get("path")
        for entry in repo_tree
        if entry.get("kind") == "file"
        and entry.get("language") == "python"
        and _match_path_prefix(entry.get("path", ""), normalized_modules)
    ]
    for rel_str in high_signal_files[:25]:
        path = root / rel_str
        if path.exists():
            code_context[rel_str] = path.read_text()
    return code_context


def worktree_policy(config: dict | None = None) -> dict:
    """Return normalized worktree defaults with backwards-compatible fallbacks."""
    if config is None:
        config = load_config()
    policy = config.get("auto_worktrees", {})
    return {
        "initiatives": bool(policy.get("initiatives", False)),
        "lightweight": bool(policy.get("lightweight", False)),
        "parallel_features": bool(policy.get("parallel_features", True)),
    }


# ---------------------------------------------------------------------------
# Worktree utilities
# ---------------------------------------------------------------------------


class WorktreeDirtyError(Exception):
    """Raised when remove_worktree finds uncommitted changes without --force."""


def git_version_check() -> None:
    """Raise RuntimeError if git < 2.5 (worktree support requires 2.5+)."""
    try:
        out = subprocess.check_output(["git", "--version"], stderr=subprocess.DEVNULL).decode().strip()
        # e.g. "git version 2.39.2"
        parts = out.split()
        if len(parts) >= 3:
            version_str = parts[2]
            major, minor = int(version_str.split(".")[0]), int(version_str.split(".")[1])
            if (major, minor) < (2, 5):
                raise RuntimeError(f"git worktree requires git >= 2.5, found {version_str}. Please upgrade git.")
    except (IndexError, ValueError) as e:
        raise RuntimeError(f"Could not parse git version: {e}") from e


def worktree_path(repo_root: Path, branch_name: str) -> Path:
    """Compute default worktree path: sibling dir named {repo}-{branch-slug}."""
    slug = branch_name.replace("/", "-").replace("_", "-")
    return repo_root.parent / f"{repo_root.name}-{slug}"


def _parse_partitions_yaml_block(raw: str) -> list[dict]:
    """Parse YAML partitions block: try PyYAML first, fallback to minimal regex parse when yaml not installed."""
    try:
        import yaml

        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, list):
            return []
        result = []
        for item in parsed:
            if not isinstance(item, dict) or "name" not in item:
                continue
            result.append(
                {
                    "name": item["name"],
                    "modules": item.get("modules", []),
                    "depends_on": item.get("depends_on", []),
                }
            )
        return result
    except Exception:
        pass
    # Fallback when PyYAML not installed: parse "- name: ...\n  modules: ...\n  depends_on: ..." blocks
    result = []
    # Split on "- name:" so first block is "- name: value\n  modules: ...", rest are "value\n  modules: ..."
    for block in re.split(r"\n-\s+name:\s*", raw):
        if not block.strip():
            continue
        # Require "modules:" so we don't accept arbitrary invalid YAML as a partition
        mod_match = re.search(r"modules:\s*\[(.*?)\]", block, re.DOTALL)
        if not mod_match:
            continue
        # First block has "name: feat/..."; subsequent blocks start with "feat/..." (name only)
        name_match = re.search(r"name:\s*([^\s\n]+)", block)
        if name_match:
            name = name_match.group(1).strip()
        else:
            first_line = re.match(r"^([^\s\n]+)", block)
            if not first_line:
                continue
            name = first_line.group(1).strip()
        modules = []
        modules = [m.strip() for m in mod_match.group(1).split(",") if m.strip()]
        depends_on = []
        dep_match = re.search(r"depends_on:\s*\[(.*?)\]", block, re.DOTALL)
        if dep_match and dep_match.group(1).strip():
            depends_on = [m.strip() for m in dep_match.group(1).split(",") if m.strip()]
        result.append({"name": name, "modules": modules, "depends_on": depends_on})
    return result


def parse_partitions_dag(approach_path: Path) -> list[dict]:
    """
    Parse the ```yaml partitions block from approach.md.
    Returns list of dicts: [{name, modules, depends_on}, ...].
    Returns [] if block absent, file missing, or parse fails — never raises.
    """
    try:
        if not approach_path.exists():
            return []
        text = approach_path.read_text()
        # Match fenced block: ```yaml partitions ... ```
        pattern = r"```yaml\s+partitions\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return []
        raw = match.group(1)
        return _parse_partitions_yaml_block(raw)
    except Exception:
        return []


def create_worktree(repo_root: Path, branch_name: str, worktree_dir: Path) -> Path:
    """
    Run `git worktree add {worktree_dir} {branch_name}`.
    Idempotent: if worktree_dir is already a registered worktree, returns path.
    Raises subprocess.CalledProcessError on git failure.
    Does NOT write to registry — caller is responsible.
    """
    git_version_check()
    worktree_dir = worktree_dir.resolve()

    # Idempotency: if directory exists and is already a registered worktree, return it
    if worktree_dir.exists():
        try:
            listing = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=repo_root, stderr=subprocess.DEVNULL).decode()
            if str(worktree_dir) in listing:
                return worktree_dir
        except subprocess.CalledProcessError:
            pass
        raise subprocess.CalledProcessError(1, "git worktree add", f"Path {worktree_dir} already exists but is not a registered worktree.")

    subprocess.run(
        ["git", "worktree", "add", str(worktree_dir), branch_name],
        cwd=repo_root,
        check=True,
    )
    return worktree_dir


def remove_worktree(repo_root: Path, worktree_dir: Path, force: bool = False) -> None:
    """
    Run `git worktree remove [--force] {worktree_dir}`.
    - If directory missing: prints [WARN] and returns (does not raise).
    - If uncommitted changes and not force: raises WorktreeDirtyError.
    """
    worktree_dir = worktree_dir.resolve()

    if not worktree_dir.exists():
        print(f"[WARN] Worktree directory not found (already removed): {worktree_dir}")
        # Prune stale entries from git's worktree list
        try:
            subprocess.run(["git", "worktree", "prune"], cwd=repo_root, capture_output=True)
        except Exception:
            pass
        return

    # Check for uncommitted changes before attempting removal
    if not force:
        try:
            status = subprocess.check_output(["git", "-C", str(worktree_dir), "status", "--porcelain"], stderr=subprocess.DEVNULL).decode().strip()
            if status:
                raise WorktreeDirtyError(f"Worktree has uncommitted changes: {worktree_dir}")
        except subprocess.CalledProcessError:
            pass  # If git status fails, proceed with removal attempt

    cmd = ["git", "worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(worktree_dir))

    subprocess.run(cmd, cwd=repo_root, check=True)


def emit(initiative: str, event_type: str, data: dict | None = None) -> None:
    """Emit a typed event to the initiative event log; failure is non-fatal.

    Performs a lazy import of emit_event so utils.py stays importable even in
    environments where emit_event.py's dependencies are unavailable.
    """
    try:
        from emit_event import emit_event
        emit_event(initiative, event_type, data or {})
    except Exception:
        pass
