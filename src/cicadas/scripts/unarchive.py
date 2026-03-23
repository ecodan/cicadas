# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import shutil
import sys
from pathlib import Path

from utils import get_project_root, load_json, save_json


def unarchive(name):
    root = get_project_root()
    cicadas = root / ".cicadas"
    archive_dir = cicadas / "archive"
    registry = load_json(cicadas / "registry.json")

    # 1. Find the most recent archive for this name
    # Archives are named TIMESTAMP-name
    matches = list(archive_dir.glob(f"*-{name}"))
    if not matches:
        print(f"[ERR]  No archive found for '{name}'.")
        return 1

    # Sort by name (which starts with timestamp) and pick last
    husk = sorted(matches)[-1]
    print(f"[INFO] Restoring from {husk.name}...")

    # 2. Read metadata
    metadata_path = husk / ".cicadas_metadata.json"
    if not metadata_path.exists():
        print(f"[ERR]  No metadata found in archive {husk.name}. Cannot restore registry state.")
        return 1

    metadata = load_json(metadata_path)
    type_ = metadata.get("type", "branch")
    registry_key = "initiatives" if type_ == "initiative" else "branches"

    # 3. Restore registry entry
    if name in registry.get(registry_key, {}):
        print(f"[WARN] {type_.capitalize()} '{name}' is already in registry. Skipping registry restore.")
    else:
        registry.setdefault(registry_key, {})[name] = metadata["registry_entry"]
        print(f"[OK]   Restored {type_} to registry.")

    # 4. Restore associated branches if any
    if type_ == "initiative" and "associated_branches" in metadata:
        for b, info in metadata["associated_branches"].items():
            if b not in registry.get("branches", {}):
                registry.setdefault("branches", {})[b] = info
                print(f"[OK]   Restored associated branch to registry: {b}")

    save_json(cicadas / "registry.json", registry)

    # 5. Move files back to active/
    active_dir = cicadas / "active" / name
    if active_dir.exists():
        print(f"[ERR]  Active directory already exists: {active_dir}. Remove it or rename it first.")
        return 1

    # Remove the metadata file before moving back
    metadata_path.unlink()
    
    shutil.move(str(husk), str(active_dir))
    print(f"[OK]   Restored files to {active_dir}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore an archived initiative or branch from its metadata snapshot")
    parser.add_argument("name", help="Name of the initiative or branch to unarchive")
    args = parser.parse_args()
    sys.exit(unarchive(args.name))
