# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from utils import WorktreeDirtyError, get_default_branch, get_project_root, get_registry_dir, load_json, remove_worktree, save_json


def prune(name, type_, force=False):
    root = get_project_root()
    cicadas = root / ".cicadas"
    registry = load_json(get_registry_dir() / "registry.json")
    default_branch = get_default_branch()

    if type_ == "branch":
        if name not in registry.get("branches", {}):
            print(f"[ERR]  Branch {name} not found.")
            return

        # Worktree teardown before deregistering
        wt = registry["branches"][name].get("worktree_path")
        if wt:
            try:
                remove_worktree(root, Path(wt), force=force)
                print(f"[OK]   Worktree removed: {wt}")
                registry["branches"][name].pop("worktree_path", None)
            except WorktreeDirtyError:
                print(f"[WARN] Worktree has uncommitted changes: {wt}")
                print("[WARN] Use --force to remove anyway, or commit/stash changes first.")
                sys.exit(1)

        # Restore active specs to drafts
        active = cicadas / "active" / name
        drafts = cicadas / "drafts" / name
        if active.exists():
            shutil.move(str(active), str(drafts))
            print(f"[OK]   Restored specs to drafts/{name}")

        # Delete git branch
        try:
            subprocess.run(["git", "checkout", default_branch], check=True, cwd=root)
            subprocess.run(["git", "branch", "-D", name], check=True, cwd=root)
        except Exception:
            print(f"[WARN] Could not delete git branch {name}")

        del registry["branches"][name]
        save_json(get_registry_dir() / "registry.json", registry)
        print(f"[OK]   Pruned branch: {name}")

    elif type_ == "initiative":
        if name not in registry.get("initiatives", {}):
            print(f"[ERR]  Initiative {name} not found.")
            return

        # Teardown worktrees for all associated branches
        orphaned = [b for b, info in registry.get("branches", {}).items() if info.get("initiative") == name]
        for b in orphaned:
            wt = registry["branches"][b].get("worktree_path")
            if wt:
                try:
                    remove_worktree(root, Path(wt), force=force)
                    print(f"[OK]   Worktree removed: {wt}")
                except (WorktreeDirtyError, Exception) as e:
                    print(f"[WARN] Could not remove worktree for {b}: {e}")
            del registry["branches"][b]

        # Restore specs
        active = cicadas / "active" / name
        drafts = cicadas / "drafts" / name
        if active.exists():
            shutil.move(str(active), str(drafts))
            print(f"[OK]   Restored specs to drafts/{name}")

        # Delete initiative branch
        branch_name = f"initiative/{name}"
        try:
            subprocess.run(["git", "checkout", default_branch], check=True, cwd=root)
            subprocess.run(["git", "branch", "-D", branch_name], check=True, cwd=root)
        except Exception:
            print(f"[WARN] Could not delete git branch {branch_name}")

        del registry["initiatives"][name]
        save_json(get_registry_dir() / "registry.json", registry)
        print(f"[OK]   Pruned initiative: {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rollback and restore specs to drafts")
    parser.add_argument("name")
    parser.add_argument("--type", required=True, choices=["branch", "initiative"])
    parser.add_argument("--force", action="store_true", help="Force worktree removal even if dirty")
    args = parser.parse_args()
    prune(args.name, args.type, force=args.force)
