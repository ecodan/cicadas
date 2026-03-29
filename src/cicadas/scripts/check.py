# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path

from utils import get_default_branch, get_project_root, get_registry_dir, load_json


def check_conflicts(initiative_name: str | None = None) -> bool:
    """
    Check for module conflicts and stale worktrees.

    Args:
        initiative_name: If provided, scope the module-overlap check to all branches
                         registered under this initiative (pre-execution mode for kickoff.py).
                         If None, check only the current git branch (legacy behavior).

    Returns:
        True if any conflicts were found, False otherwise.
    """
    root = get_project_root()
    cicadas = root / ".cicadas"
    registry = load_json(get_registry_dir() / "registry.json")
    default_branch = get_default_branch()
    has_conflicts = False

    if initiative_name:
        # Pre-execution initiative-scoped mode: check all branches for this initiative
        initiative_branches = {
            name: info
            for name, info in registry.get("branches", {}).items()
            if info.get("initiative") == initiative_name
        }

        # Check all pairs for module overlap
        branch_list = list(initiative_branches.items())
        for i, (name_a, info_a) in enumerate(branch_list):
            mods_a = set(info_a.get("modules", []))
            for name_b, info_b in branch_list[i + 1 :]:
                mods_b = set(info_b.get("modules", []))
                overlap = mods_a & mods_b
                if overlap:
                    print(f"[WARN] Module conflict: {name_a} and {name_b} both declare ownership of '{', '.join(overlap)}'")
                    has_conflicts = True

        if not has_conflicts and initiative_branches:
            # No conflicts found — don't print here, kickoff.py prints [OK]
            pass
    else:
        # Legacy mode: check current branch against all registered branches
        try:
            curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=root).decode().strip()
        except Exception:
            curr = "unknown"

        print(f"Checking status for branch: {curr}")

        curr_info = registry.get("branches", {}).get(curr)
        if curr_info:
            my_mods = set(curr_info.get("modules", []))
            for name, info in registry.get("branches", {}).items():
                if name == curr:
                    continue
                overlap = my_mods.intersection(set(info.get("modules", [])))
                if overlap:
                    print(f"⚠️  CONFLICT: Branch '{name}' overlaps on modules: {', '.join(overlap)}")
                    has_conflicts = True

            # Check for signals in linked initiative
            initiative = curr_info.get("initiative")
            if initiative:
                init_info = registry.get("initiatives", {}).get(initiative, {})
                signals = init_info.get("signals", [])
                if signals:
                    print(f"\n📡 Signals from initiative '{initiative}':")
                    for s in signals[-3:]:
                        print(f"  [{s['timestamp']}] ({s.get('from_branch', '?')}): {s['message']}")
        else:
            print(f"ℹ️  Current branch '{curr}' is not registered.")

        # Check for branch updates
        try:
            log = subprocess.check_output(["git", "log", f"{curr}..{default_branch}", "--oneline"], cwd=root).decode()
            if log:
                count = len(log.strip().split("\n"))
                print(f"\n📥 {count} new commits on {default_branch} since you branched.")
        except Exception:
            pass

    # Stale worktree detection — always run regardless of mode
    for initiative_name, info in registry.get("initiatives", {}).items():
        wt = info.get("worktree_path")
        if wt and not Path(wt).exists():
            print(f"[WARN] Stale worktree: {wt} (initiative: {initiative_name}). Run 'git worktree repair' or re-run kickoff.py with --worktree.")
    for branch_name, info in registry.get("branches", {}).items():
        wt = info.get("worktree_path")
        if wt and not Path(wt).exists():
            print(f"[WARN] Stale worktree: {wt} (branch: {branch_name}). Run 'git worktree repair' or re-run branch.py.")

    return has_conflicts


if __name__ == "__main__":
    check_conflicts()
