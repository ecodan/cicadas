# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import subprocess
from datetime import UTC, datetime

from utils import get_project_root, get_registry_dir, load_json, save_json


def send_signal(message, initiative=None):
    root = get_project_root()
    cicadas = root / ".cicadas"
    registry = load_json(get_registry_dir() / "registry.json")

    # Auto-detect initiative from current branch
    if not initiative:
        try:
            curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=root).decode().strip()
            branch_info = registry.get("branches", {}).get(curr, {})
            initiative = branch_info.get("initiative")
        except Exception:
            pass

    if not initiative or initiative not in registry.get("initiatives", {}):
        print("Error: Could not determine initiative. Use --initiative flag.")
        return

    signal = {
        "timestamp": datetime.now(UTC).isoformat(),
        "message": message,
        "from_branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=root).decode().strip(),
    }
    registry["initiatives"][initiative].setdefault("signals", []).append(signal)
    save_json(get_registry_dir() / "registry.json", registry)
    print(f"Signal sent to initiative '{initiative}': {message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Broadcast a signal to the initiative's signal board")
    parser.add_argument("message")
    parser.add_argument("--initiative", help="Target initiative (auto-detected if omitted)")
    args = parser.parse_args()
    send_signal(args.message, args.initiative)
