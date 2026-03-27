# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
from datetime import UTC, datetime

from utils import get_registry_dir, load_json, save_json


def update_index(branch, summary, decisions="", modules=""):
    index_path = get_registry_dir() / "index.json"
    index = load_json(index_path)

    if isinstance(modules, str):
        mod_list = [m.strip() for m in modules.split(",") if m.strip()]
    else:
        mod_list = modules or []

    entry = {"timestamp": datetime.now(UTC).isoformat(), "branch": branch, "summary": summary, "decisions": decisions, "modules": mod_list}

    index.setdefault("entries", []).append(entry)
    save_json(index_path, index)
    print(f"Added entry {len(index['entries'])} to artifact index.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--decisions", default="")
    parser.add_argument("--modules", default="")
    args = parser.parse_args()
    update_index(args.branch, args.summary, args.decisions, args.modules)
