# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path at the beginning to override builtins like 'signal'
SCRIPTS_DIR = Path(__file__).parent.parent / "src" / "cicadas" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


class CicadasTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the project root
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize .cicadas structure
        self.cicadas_dir = self.root / ".cicadas"
        self.cicadas_dir.mkdir()
        (self.cicadas_dir / "drafts").mkdir()
        (self.cicadas_dir / "active").mkdir()
        (self.cicadas_dir / "archive").mkdir()
        (self.cicadas_dir / "canon").mkdir()

        # Create empty registry and index
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump({"initiatives": {}, "branches": {}}, f)
        with open(self.cicadas_dir / "index.json", "w") as f:
            json.dump({"entries": []}, f)

    def tearDown(self):
        os.chdir(self.old_cwd)
        # Remove any linked worktrees before deleting the repo directory
        git_dir = self.root / ".git"
        if git_dir.is_dir():
            try:
                out = subprocess.check_output(
                    ["git", "worktree", "list", "--porcelain"],
                    cwd=self.root, stderr=subprocess.DEVNULL,
                ).decode()
                for line in out.splitlines():
                    if line.startswith("worktree "):
                        wt_path = Path(line[len("worktree "):].strip())
                        if wt_path != self.root and wt_path.exists():
                            subprocess.run(
                                ["git", "worktree", "remove", "--force", str(wt_path)],
                                cwd=self.root, capture_output=True,
                            )
            except Exception:
                pass
        shutil.rmtree(self.test_dir)

    def init_git(self):
        """Initialize a git repo in the test directory."""
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # Configure local git user for commits
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        # Create an initial commit on master
        (self.root / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
        # Create a second commit so branches have a parent
        (self.root / "README.md").write_text("# Test Project\nModified")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], check=True)
