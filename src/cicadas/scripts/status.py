# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path

from utils import get_default_branch, get_project_root, get_registry_dir, load_json


def _worktree_rows(registry: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for name, info in registry.get("initiatives", {}).items():
        wt = info.get("worktree_path")
        if wt:
            rows.append((f"initiative/{name}", wt))
    for name, info in registry.get("branches", {}).items():
        wt = info.get("worktree_path")
        if wt:
            rows.append((name, wt))
    return rows


def _recent_events(initiative: str, n: int = 5) -> list[dict]:
    """Return up to n most recent events for an initiative; empty list if unavailable."""
    try:
        from get_events import get_events  # lazy import — get_events.py may not always be in sys.path
        return get_events(initiative, last=n)
    except Exception:
        return []


def _is_merged_into(root: Path, source_ref: str, target_ref: str) -> bool:
    """Return True if source is merged into target (source's tip is ancestor of target's tip)."""
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_ref, target_ref],
            cwd=root,
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _ref_exists(root: Path, ref: str) -> bool:
    """Return True if ref or branch name exists."""
    try:
        subprocess.run(["git", "rev-parse", "--verify", ref], cwd=root, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def _lifecycle_merge_status(
    root: Path,
    cicadas: Path,
    registry: dict,
    initiative_name: str,
    default_branch: str,
) -> tuple[list[tuple[str, str]], str | None]:
    """For one initiative with active lifecycle, return (merged_pairs, next_step_name)."""
    active_dir: Path = cicadas / "active" / initiative_name
    lifecycle_path: Path = active_dir / "lifecycle.json"
    if not lifecycle_path.exists():
        return [], None
    lifecycle: dict = load_json(lifecycle_path)
    steps: list[dict] = lifecycle.get("steps", [])
    if not steps:
        return [], None

    initiative_branch: str = f"initiative/{initiative_name}"
    branches: dict = registry.get("branches", {})
    feat_branches: list[str] = [
        n for n, i in branches.items()
        if i.get("initiative") == initiative_name and not (n.startswith("fix/") or n.startswith("tweak/"))
    ]

    merged: list[tuple[str, str]] = []
    # Check each feature -> initiative (use refs/heads/ for local)
    for fb in feat_branches:
        if _ref_exists(root, fb) and _ref_exists(root, initiative_branch):
            if _is_merged_into(root, fb, initiative_branch):
                merged.append((fb, initiative_branch))
    # Check initiative -> default
    if _ref_exists(root, initiative_branch) and _ref_exists(root, default_branch):
        if _is_merged_into(root, initiative_branch, default_branch):
            merged.append((initiative_branch, default_branch))

    # Next step: if initiative merged to default -> done; elif all features merged -> complete initiative; else complete feature
    next_step: str | None = None
    if _ref_exists(root, initiative_branch) and _is_merged_into(root, initiative_branch, default_branch):
        next_step = "Initiative complete (merge to default done)."
    elif feat_branches and all(_ref_exists(root, fb) and _is_merged_into(root, fb, initiative_branch) for fb in feat_branches):
        next_step = next((s.get("name") for s in steps if s.get("id") == "complete_initiative"), steps[-1].get("name") if steps else None)
    else:
        next_step = next((s.get("name") for s in steps if s.get("id") == "complete_feature"), "Complete each feature")

    return merged, next_step


def show_status() -> None:
    root: Path = get_project_root()
    cicadas: Path = root / ".cicadas"
    registry: dict = load_json(get_registry_dir() / "registry.json")

    print(f"Project: {root.name}\n")

    initiatives: dict = registry.get("initiatives", {})
    print(f"Active Initiatives ({len(initiatives)}):")
    for name, info in initiatives.items():
        signals: list = info.get("signals", [])
        print(f"  - {name}: {info['intent']}")
        if signals:
            print(f"    Signals ({len(signals)}):")
            for s in signals[-3:]:  # Show last 3
                print(f"      [{s['timestamp']}] ({s.get('from_branch', '?')}): {s['message']}")
        recent: list[dict] = _recent_events(name)
        if recent:
            print(f"    Recent events ({len(recent)}):")
            for ev in recent:
                ts: str = ev.get("timestamp", "")[:19].replace("T", " ")
                print(f"      [{ts}] {ev.get('type', '?')} (branch: {ev.get('branch', '?')})")

    branches: dict = registry.get("branches", {})
    features: dict = {n: i for n, i in branches.items() if not (n.startswith("fix/") or n.startswith("tweak/") or n.startswith("skill/"))}
    fixes: dict = {n: i for n, i in branches.items() if n.startswith("fix/")}
    tweaks: dict = {n: i for n, i in branches.items() if n.startswith("tweak/")}
    skills: dict = {n: i for n, i in branches.items() if n.startswith("skill/")}

    if features:
        print(f"\nActive Feature Branches ({len(features)}):")
        for name, info in features.items():
            initiative = info.get("initiative", "standalone")
            print(f"  - {name}: {info['intent']} (Initiative: {initiative}, Modules: {', '.join(info.get('modules', []))})")

    if fixes:
        print(f"\nActive Bugs ({len(fixes)}):")
        for name, info in fixes.items():
            print(f"  - {name}: {info['intent']} (Modules: {', '.join(info.get('modules', []))})")

    if tweaks:
        print(f"\nActive Tweaks ({len(tweaks)}):")
        for name, info in tweaks.items():
            print(f"  - {name}: {info['intent']} (Modules: {', '.join(info.get('modules', []))})")

    if skills:
        print(f"\nActive Skills ({len(skills)}):")
        for name, info in skills.items():
            print(f"  - {name}: {info['intent']}")

    # Worktrees section — only shown if any branches have worktree_path recorded
    worktree_rows = _worktree_rows(registry)
    if worktree_rows:
        print(f"\nWorktrees ({len(worktree_rows)}):")
        for name, wt in worktree_rows:
            from pathlib import Path as _Path
            wt_path = _Path(wt)
            if not wt_path.exists():
                print(f"  {name}  →  {wt}  [MISSING]")
            else:
                try:
                    status_out = subprocess.check_output(
                        ["git", "-C", wt, "status", "--porcelain"],
                        stderr=subprocess.DEVNULL,
                    ).decode().strip()
                    state = "[dirty]" if status_out else "[clean]"
                except subprocess.CalledProcessError:
                    state = "[unknown]"
                try:
                    head = subprocess.check_output(
                        ["git", "-C", wt, "log", "-1", "--oneline"],
                        stderr=subprocess.DEVNULL,
                    ).decode().strip()
                except subprocess.CalledProcessError:
                    head = ""
                print(f"  {name}  →  {wt}  {state}  {head}")

    # Lifecycle and merge status (git-based, local refs only; run 'git fetch' first for remote state)
    try:
        default_branch: str = get_default_branch()
        for init_name in initiatives:
            merged_pairs, next_step = _lifecycle_merge_status(root, cicadas, registry, init_name, default_branch)
            if merged_pairs or next_step:
                print(f"\nLifecycle ({init_name}):")
                for src, tgt in merged_pairs:
                    print(f"  Merged: {src} → {tgt}")
                if next_step:
                    print(f"  Next: {next_step}")
                print("  (Tip: run 'git fetch' first for up-to-date remote merge state)")
    except (KeyError, TypeError, ValueError):
        pass


if __name__ == "__main__":
    show_status()
