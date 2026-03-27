# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import unittest

import branch
from base import CicadasTest


class TestBranch(CicadasTest):
    def setUp(self):
        super().setUp()
        self.init_git()
        # Mocking and real git operations are mixed here.
        # utils.get_default_branch() will return 'master' or 'main' depending on git init.
        from utils import get_default_branch

        self.default_branch = get_default_branch()

    def test_create_feature_branch(self):
        # Register an initiative first
        init_name = "test-init"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        branch_name = "feat/my-feature"
        branch.create_branch(branch_name, "feat intent", "src/foo.py", initiative=init_name)

        # Verify git branch
        curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=self.root).decode().strip()
        self.assertEqual(curr, branch_name)

        # Verify registry
        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertIn(branch_name, reg["branches"])
        self.assertEqual(reg["branches"][branch_name]["initiative"], init_name)

    def test_create_fix_branch_from_root(self):
        branch_name = "fix/my-bug"
        branch.create_branch(branch_name, "bug intent", "src/bar.py")

        # Main worktree stays on default branch (worktree created instead)
        curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=self.root).decode().strip()
        self.assertEqual(curr, self.default_branch)

        # Branch was created and points to the same commit as default branch
        branch_hash = subprocess.check_output(["git", "rev-parse", branch_name], cwd=self.root).decode().strip()
        default_hash = subprocess.check_output(["git", "rev-parse", self.default_branch], cwd=self.root).decode().strip()
        self.assertEqual(branch_hash, default_hash)

    def test_skill_branch_forks_from_default_branch(self):
        """skill/ branches should fork from default branch, not from an initiative branch."""
        init_name = "my-skill"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test skill"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        branch_name = "skill/my-skill"
        branch.create_branch(branch_name, "skill intent", "", initiative=init_name)

        # Main worktree stays on default branch (worktree created instead)
        curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=self.root).decode().strip()
        self.assertEqual(curr, self.default_branch)

        # Branch was created from default branch
        branch_hash = subprocess.check_output(["git", "rev-parse", branch_name], cwd=self.root).decode().strip()
        default_hash = subprocess.check_output(["git", "rev-parse", self.default_branch], cwd=self.root).decode().strip()
        self.assertEqual(branch_hash, default_hash)

    def test_skill_branch_registered_with_initiative(self):
        """skill/ branch registration records the initiative key."""
        init_name = "skill-pdf"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "pdf skill"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        branch.create_branch("skill/pdf", "build pdf skill", "", initiative=init_name)

        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertIn("skill/pdf", reg["branches"])
        self.assertEqual(reg["branches"]["skill/pdf"]["initiative"], init_name)

    def test_tweak_branch_active_dir_uses_initiative_name(self):
        """Active dir for a tweak branch should be active/{initiative}, not active/tweak/{name}."""
        init_name = "my-tweak"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test tweak"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        branch.create_branch("tweak/my-tweak", "tweak intent", "", initiative=init_name)

        # Active dir must be active/my-tweak, NOT active/tweak/my-tweak
        self.assertTrue((self.cicadas_dir / "active" / init_name).exists())
        self.assertFalse((self.cicadas_dir / "active" / "tweak").exists())

    def test_fix_branch_active_dir_uses_initiative_name(self):
        """Active dir for a fix branch should be active/{initiative}, not active/fix/{name}."""
        init_name = "my-fix"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test fix"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        branch.create_branch("fix/my-fix", "fix intent", "", initiative=init_name)

        self.assertTrue((self.cicadas_dir / "active" / init_name).exists())
        self.assertFalse((self.cicadas_dir / "active" / "fix").exists())

    def test_conflict_detection(self):
        # Register existing branch with same module
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"]["feat/old"] = {"modules": ["src/shared.py"], "intent": "old"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        # Capture output
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            branch.create_branch("feat/new", "new intent", "src/shared.py")

        output = f.getvalue()
        self.assertIn("[WARN]", output)
        self.assertIn("feat/old", output)


class TestBranchWorktree(CicadasTest):
    """Integration tests for worktree creation in branch.py."""

    def setUp(self):
        super().setUp()
        self.init_git()
        from utils import get_default_branch
        self.default_branch = get_default_branch()
        self.init_name = "my-initiative"
        # Register initiative
        import utils
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["initiatives"][self.init_name] = {"intent": "test"}
        utils.save_json(self.cicadas_dir / "registry.json", reg)
        # Create active dir and approach.md with a parallel partition
        active = self.cicadas_dir / "active" / self.init_name
        active.mkdir(parents=True, exist_ok=True)
        (active / "approach.md").write_text(
            "# Approach\n\n## Sequencing\n\n"
            "```yaml partitions\n"
            "- name: feat/parallel-branch\n"
            "  modules: [src/foo]\n"
            "  depends_on: []\n"
            "- name: feat/sequential-branch\n"
            "  modules: [src/bar]\n"
            "  depends_on: [feat/parallel-branch]\n"
            "```\n"
        )
        (active / "tasks.md").write_text("# Tasks\n")
        # Create initiative branch first
        subprocess.run(["git", "checkout", "-b", f"initiative/{self.init_name}"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", self.default_branch], cwd=self.root, check=True, capture_output=True)
        self._worktree_dirs = []

    def tearDown(self):
        for wt in self._worktree_dirs:
            if wt.exists():
                subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=self.root, capture_output=True)
        super().tearDown()

    def test_parallel_partition_gets_worktree(self):
        import utils
        expected_wt = utils.worktree_path(self.root, "feat/parallel-branch")
        self._worktree_dirs.append(expected_wt)

        branch.create_branch("feat/parallel-branch", "parallel intent", "src/foo", initiative=self.init_name)

        # Worktree directory should exist
        self.assertTrue(expected_wt.exists(), f"Worktree dir not found: {expected_wt}")
        # Registry should have worktree_path
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertIn("worktree_path", reg["branches"]["feat/parallel-branch"])
        # context.md should exist in worktree
        self.assertTrue((expected_wt / "context.md").exists())

    def test_sequential_partition_gets_plain_branch(self):
        import utils
        # Register parallel branch first so sequential can reference it
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["branches"]["feat/parallel-branch"] = {"modules": ["src/foo"], "initiative": self.init_name, "intent": "parallel"}
        utils.save_json(self.cicadas_dir / "registry.json", reg)
        # Create initiative branch to branch from
        subprocess.run(["git", "checkout", f"initiative/{self.init_name}"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", self.default_branch], cwd=self.root, check=True, capture_output=True)

        branch.create_branch("feat/sequential-branch", "sequential intent", "src/bar", initiative=self.init_name)

        reg = utils.load_json(self.cicadas_dir / "registry.json")
        # No worktree_path for sequential partition
        self.assertNotIn("worktree_path", reg["branches"]["feat/sequential-branch"])

    def test_no_worktree_flag_forces_plain_branch(self):
        import utils
        branch.create_branch("feat/parallel-branch", "parallel intent", "src/foo", initiative=self.init_name, no_worktree=True)
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertNotIn("worktree_path", reg["branches"]["feat/parallel-branch"])


if __name__ == "__main__":
    unittest.main()
