# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import shutil
import subprocess
from datetime import UTC, datetime

from tokens import append_entry
from utils import create_worktree, emit, get_project_root, get_registry_dir, load_json, parse_partitions_dag, save_json, worktree_path


def kickoff(name, intent, owner="unknown"):
    root = get_project_root()
    cicadas = root / ".cicadas"
    registry = load_json(get_registry_dir() / "registry.json")

    if name in registry.get("initiatives", {}):
        print(f"[ERR]  Initiative {name} already exists.")
        return

    active_dir = cicadas / "active" / name
    active_dir.mkdir(parents=True, exist_ok=True)

    # Promote drafts
    drafts_dir = cicadas / "drafts" / name
    if drafts_dir.exists():
        print(f"[INFO] Promoting drafts for initiative: {name}...")
        for item in drafts_dir.iterdir():
            if item.name.startswith("."):
                continue
            shutil.move(str(item), str(active_dir / item.name))
        try:
            drafts_dir.rmdir()
        except OSError:
            pass
    else:
        print(f"[WARN] No drafts found for {name}. Creating empty initiative.")

    # Register
    registry.setdefault("initiatives", {})[name] = {"intent": intent, "owner": owner, "signals": [], "created_at": datetime.now(UTC).isoformat()}
    save_json(get_registry_dir() / "registry.json", registry)
    emit(name, "initiative.kicked_off", {"intent": intent})

    # Write lifecycle/kickoff token boundary entry
    append_entry(active_dir / "tokens.json", initiative=name, phase="lifecycle", subphase="kickoff", source="unavailable")

    # Detect parallel partitions and run pre-execution conflict check
    approach_path = active_dir / "approach.md"
    partitions = parse_partitions_dag(approach_path)
    parallel = [p["name"] for p in partitions if p.get("depends_on") == []]
    if parallel:
        print(f"[INFO] Parallel partitions detected: {', '.join(parallel)}")
        print(f"[INFO] Running conflict check before parallel execution...")
        from check import check_conflicts
        has_conflicts = check_conflicts(initiative_name=name)
        if has_conflicts:
            print(f"[WARN] Resolve module conflicts in approach.md before starting parallel branches.")
        else:
            print(f"[OK]   No module conflicts detected.")

    # Create initiative branch without switching (stay on current branch)
    branch_name = f"initiative/{name}"
    try:
        subprocess.run(["git", "branch", branch_name], check=True, cwd=root)
        print(f"[OK]   Created initiative branch: {branch_name}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not create git branch {branch_name}")

    try:
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True, cwd=root)
        print(f"[INFO] Pushed {branch_name} to remote.")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not push {branch_name} to remote. Push manually: git push -u origin {branch_name}")

    # Create a linked worktree so this and other work streams stay independent
    wt_dir = worktree_path(root, branch_name)
    try:
        created = create_worktree(root, branch_name, wt_dir)
        registry["initiatives"][name]["worktree_path"] = str(created)
        save_json(get_registry_dir() / "registry.json", registry)
        print(f"[OK]   Worktree created: {created}")
        print(f"[INFO] Work on this initiative in: {created}")
    except Exception as e:
        print(f"[WARN] Could not create worktree: {e}")

    print(f"[OK]   Initiative kicked off: {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kickoff an initiative: promote drafts to active, register, create branch")
    parser.add_argument("name")
    parser.add_argument("--intent", required=True)
    args = parser.parse_args()
    kickoff(args.name, args.intent)
