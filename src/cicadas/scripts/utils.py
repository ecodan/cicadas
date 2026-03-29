# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
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
