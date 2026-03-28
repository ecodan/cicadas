# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from utils import WorktreeDirtyError, emit, get_project_root, get_registry_dir, load_json, remove_worktree, save_json


def archive(name, type_="branch", force=False):
    root = get_project_root()
    cicadas = root / ".cicadas"
    registry = load_json(get_registry_dir() / "registry.json")

    registry_key = "initiatives" if type_ == "initiative" else "branches"

    if name not in registry.get(registry_key, {}):
        print(f"[ERR]  {type_.capitalize()} {name} not found in registry.")
        return

    # Worktree teardown
    if type_ == "initiative":
        wt = registry[registry_key][name].get("worktree_path")
        if wt:
            try:
                remove_worktree(root, Path(wt), force=force)
                print(f"[OK]   Worktree removed: {wt}")
                registry[registry_key][name].pop("worktree_path", None)
            except WorktreeDirtyError:
                print(f"[WARN] Worktree has uncommitted changes: {wt}")
                print("[WARN] Use --force to remove anyway, or commit/stash changes first.")
                sys.exit(1)

    if type_ == "branch":
        wt = registry[registry_key][name].get("worktree_path")
        if wt:
            try:
                remove_worktree(root, Path(wt), force=force)
                print(f"[OK]   Worktree removed: {wt}")
                # Clear worktree_path from registry entry
                registry[registry_key][name].pop("worktree_path", None)
            except WorktreeDirtyError:
                print(f"[WARN] Worktree has uncommitted changes: {wt}")
                print("[WARN] Use --force to remove anyway, or commit/stash changes first.")
                sys.exit(1)

    # Move active specs to archive
    active = cicadas / "active" / name
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    husk = cicadas / "archive" / f"{ts}-{name}"

    if active.exists():
        # Save metadata snapshot for unarchive
        metadata = {
            "name": name,
            "type": type_,
            "registry_entry": registry[registry_key][name],
            "timestamp": ts,
        }
        # If initiative, also snapshot associated branches that are about to be deregistered
        if type_ == "initiative":
            orphaned_branches = {
                b: info for b, info in registry.get("branches", {}).items() 
                if info.get("initiative") == name
            }
            if orphaned_branches:
                metadata["associated_branches"] = orphaned_branches

        save_json(active / ".cicadas_metadata.json", metadata)

        if name.startswith("fix/") or name.startswith("tweak/") or name.startswith("skill/"):
            print("!!! LIGHTWEIGHT PATH SIGNIFICANCE CHECK !!!")
            print(f"Agent: Before archiving {name}, have you verified if this change warrants a Canon update?")
            print("If yes, perform a 'Reflect' operation to update .cicadas/canon/ before proceeding.")
            print("-" * 40)

        emit(name, "specs.archived", {"archive_name": husk.name, "type": type_})
        shutil.move(str(active), str(husk))
        print(f"[OK]   Archived active specs to {husk.name}")

    # Remove from registry
    del registry[registry_key][name]

    # When archiving an initiative, also deregister any associated branches (and their worktrees)
    if type_ == "initiative":
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
            print(f"[OK]   Deregistered associated branch: {b}")

    save_json(get_registry_dir() / "registry.json", registry)
    print(f"[OK]   Deregistered {type_}: {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Archive active specs and deregister from registry")
    parser.add_argument("name")
    parser.add_argument("--type", default="branch", choices=["branch", "initiative"], help="Type to archive: branch or initiative")
    parser.add_argument("--force", action="store_true", help="Force worktree removal even if dirty")
    args = parser.parse_args()
    archive(args.name, args.type, force=args.force)
