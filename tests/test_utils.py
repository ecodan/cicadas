# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import unittest
from pathlib import Path

import utils
from base import CicadasTest


class TestUtils(CicadasTest):
    def test_get_project_root(self):
        self.assertEqual(utils.get_project_root().resolve(), self.root.resolve())

        sub = self.root / "src" / "foo"
        sub.mkdir(parents=True)
        os.chdir(sub)
        self.assertEqual(utils.get_project_root().resolve(), self.root.resolve())

    def test_load_save_json(self):
        path = self.root / "test.json"
        data = {"foo": "bar", "baz": 123}
        utils.save_json(path, data)
        loaded = utils.load_json(path)
        self.assertEqual(loaded, data)
        self.assertEqual(utils.load_json(self.root / "missing.json"), {})

    def test_get_default_branch(self):
        self.init_git()
        expected = subprocess.check_output(["git", "branch", "--show-current"], cwd=self.root).decode().strip()
        self.assertEqual(utils.get_default_branch(), expected)


class TestGetRegistryRoot(CicadasTest):
    def test_primary_worktree_returns_self(self):
        self.init_git()
        self.assertEqual(utils.get_registry_root().resolve(), self.root.resolve())

    def test_linked_worktree_returns_primary(self):
        self.init_git()
        subprocess.run(["git", "checkout", "-b", "feat/rr-branch"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, check=True, capture_output=True)
        wt_dir = self.root.parent / f"{self.root.name}-feat-rr-branch"
        subprocess.run(["git", "worktree", "add", str(wt_dir), "feat/rr-branch"], cwd=self.root, check=True, capture_output=True)
        try:
            os.chdir(wt_dir)
            result = utils.get_registry_root()
            self.assertEqual(result.resolve(), self.root.resolve())
        finally:
            os.chdir(self.root)

    def test_get_registry_dir_returns_cicadas_subdir(self):
        self.init_git()
        result = utils.get_registry_dir()
        self.assertEqual(result.resolve(), (self.root / ".cicadas").resolve())


class TestGitVersionCheck(unittest.TestCase):
    def test_passes_on_current_git(self):
        # Should not raise on any modern git installation
        utils.git_version_check()  # no assertion needed — just must not raise


class TestWorktreePath(unittest.TestCase):
    def test_basic_slug(self):
        root = Path("/home/dan/cicadas")
        result = utils.worktree_path(root, "feat/api")
        self.assertEqual(result, Path("/home/dan/cicadas-feat-api"))

    def test_nested_slug(self):
        root = Path("/home/dan/myrepo")
        result = utils.worktree_path(root, "feat/auth/core")
        self.assertEqual(result, Path("/home/dan/myrepo-feat-auth-core"))

    def test_underscore_replaced(self):
        root = Path("/home/dan/myrepo")
        result = utils.worktree_path(root, "feat/some_feature")
        self.assertEqual(result, Path("/home/dan/myrepo-feat-some-feature"))


class TestParsePartitionsDag(CicadasTest):
    def _write_approach(self, content: str) -> Path:
        p = self.root / "approach.md"
        p.write_text(content)
        return p

    def test_valid_block(self):
        approach = self._write_approach(
            "# Approach\n\n"
            "```yaml partitions\n"
            "- name: feat/api\n"
            "  modules: [api, gateway]\n"
            "  depends_on: []\n"
            "- name: feat/integration\n"
            "  modules: [integration]\n"
            "  depends_on: [feat/api]\n"
            "```\n"
        )
        result = utils.parse_partitions_dag(approach)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "feat/api")
        self.assertEqual(result[0]["depends_on"], [])
        self.assertEqual(result[1]["name"], "feat/integration")
        self.assertEqual(result[1]["depends_on"], ["feat/api"])

    def test_missing_file_returns_empty(self):
        result = utils.parse_partitions_dag(self.root / "nonexistent.md")
        self.assertEqual(result, [])

    def test_missing_block_returns_empty(self):
        approach = self._write_approach("# Approach\n\nNo partitions block here.\n")
        result = utils.parse_partitions_dag(approach)
        self.assertEqual(result, [])

    def test_invalid_yaml_returns_empty(self):
        approach = self._write_approach(
            "```yaml partitions\n"
            "not: valid: yaml: [[\n"
            "```\n"
        )
        result = utils.parse_partitions_dag(approach)
        self.assertEqual(result, [])

    def test_real_approach_md_fixture(self):
        """Use this initiative's own approach.md as a live fixture."""
        fixture = Path(__file__).parent.parent / ".cicadas" / "active" / "worktrees-parallel-execution" / "approach.md"
        if not fixture.exists():
            self.skipTest("Initiative approach.md not found — run after kickoff")
        result = utils.parse_partitions_dag(fixture)
        self.assertIsInstance(result, list)
        # Expect 4 partitions from the worktrees initiative
        self.assertEqual(len(result), 4)
        names = [p["name"] for p in result]
        self.assertIn("feat/worktree-utils", names)
        self.assertIn("feat/worktree-templates", names)
        # These two have no dependencies
        parallel = [p for p in result if p["depends_on"] == []]
        self.assertGreaterEqual(len(parallel), 2)


class TestCreateWorktree(CicadasTest):
    def setUp(self):
        super().setUp()
        self.init_git()
        # Create a test branch to attach the worktree to
        subprocess.run(["git", "checkout", "-b", "feat/test-branch"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, check=True, capture_output=True)
        self.wt_dir = self.root.parent / f"{self.root.name}-feat-test-branch"

    def tearDown(self):
        # Clean up worktree if it exists
        if self.wt_dir.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(self.wt_dir)], cwd=self.root, capture_output=True)
        super().tearDown()

    def test_creates_worktree(self):
        result = utils.create_worktree(self.root, "feat/test-branch", self.wt_dir)
        self.assertEqual(result, self.wt_dir.resolve())
        self.assertTrue(self.wt_dir.exists())

    def test_idempotent_on_existing_worktree(self):
        utils.create_worktree(self.root, "feat/test-branch", self.wt_dir)
        # Second call should return path without error
        result = utils.create_worktree(self.root, "feat/test-branch", self.wt_dir)
        self.assertTrue(result.exists())

    def test_raises_on_invalid_branch(self):
        with self.assertRaises(subprocess.CalledProcessError):
            utils.create_worktree(self.root, "feat/nonexistent", self.wt_dir)


class TestRemoveWorktree(CicadasTest):
    def setUp(self):
        super().setUp()
        self.init_git()
        subprocess.run(["git", "checkout", "-b", "feat/rm-branch"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, check=True, capture_output=True)
        self.wt_dir = self.root.parent / f"{self.root.name}-feat-rm-branch"
        utils.create_worktree(self.root, "feat/rm-branch", self.wt_dir)

    def tearDown(self):
        if self.wt_dir.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(self.wt_dir)], cwd=self.root, capture_output=True)
        super().tearDown()

    def test_removes_clean_worktree(self):
        utils.remove_worktree(self.root, self.wt_dir)
        self.assertFalse(self.wt_dir.exists())

    def test_raises_on_dirty_without_force(self):
        # Create an uncommitted file in the worktree
        (self.wt_dir / "dirty_file.txt").write_text("uncommitted")
        with self.assertRaises(utils.WorktreeDirtyError):
            utils.remove_worktree(self.root, self.wt_dir, force=False)
        # Worktree should still exist
        self.assertTrue(self.wt_dir.exists())

    def test_removes_dirty_with_force(self):
        (self.wt_dir / "dirty_file.txt").write_text("uncommitted")
        utils.remove_worktree(self.root, self.wt_dir, force=True)
        self.assertFalse(self.wt_dir.exists())

    def test_warns_and_returns_on_missing_dir(self):
        import shutil
        shutil.rmtree(self.wt_dir)
        # Should not raise — just warn
        utils.remove_worktree(self.root, self.wt_dir)


if __name__ == "__main__":
    unittest.main()
