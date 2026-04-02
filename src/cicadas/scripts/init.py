# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import shutil
import stat
from pathlib import Path

from utils import get_project_root, save_json

_HOOKS_SRC = Path(__file__).parent / "hooks"


def init_cicadas(root: Path) -> None:
    cicadas = root / ".cicadas"
    cicadas.mkdir(exist_ok=True)
    (cicadas / "canon").mkdir(parents=True, exist_ok=True)
    (cicadas / "active").mkdir(exist_ok=True)
    (cicadas / "drafts").mkdir(exist_ok=True)
    (cicadas / "archive").mkdir(exist_ok=True)

    save_json(cicadas / "registry.json", {"schema_version": "2.0", "initiatives": {}, "branches": {}})
    save_json(cicadas / "index.json", {"schema_version": "2.0", "entries": []})
    save_json(
        cicadas / "config.json",
        {
            "project_name": root.name,
            "auto_worktrees": {
                "initiatives": False,
                "lightweight": False,
                "parallel_features": True,
            },
        },
    )

    print(f"Initialized Cicadas in {cicadas}")

    _install_hooks(root)


def _install_hooks(root: Path) -> None:
    git_hooks_dir = root / ".git" / "hooks"
    if not git_hooks_dir.exists():
        print("Skipping hook installation: no .git/hooks directory found.")
        return

    for hook_src in _HOOKS_SRC.iterdir():
        if hook_src.suffix or not hook_src.is_file():
            continue
        hook_dst = git_hooks_dir / hook_src.name
        shutil.copy2(hook_src, hook_dst)
        hook_dst.chmod(hook_dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Installed git hook: .git/hooks/{hook_src.name}")


if __name__ == "__main__":
    init_cicadas(get_project_root())
