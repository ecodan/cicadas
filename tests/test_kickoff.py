# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import unittest

import kickoff
from base import CicadasTest


class TestKickoff(CicadasTest):
    def test_kickoff_basic(self):
        # Setup draft
        name = "test-init"
        draft_dir = self.cicadas_dir / "drafts" / name
        draft_dir.mkdir(parents=True)
        (draft_dir / "prd.md").write_text("# Test PRD")

        # Initialize git for kickoff to work
        self.init_git()

        # Run kickoff
        kickoff.kickoff(name, "test intent")

        # Verify active spec
        active_spec = self.cicadas_dir / "active" / name / "prd.md"
        self.assertTrue(active_spec.exists())
        self.assertEqual(active_spec.read_text(), "# Test PRD")

        # Verify drafts removed
        self.assertFalse(draft_dir.exists())

        # Verify registry
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertIn(name, registry["initiatives"])
        self.assertEqual(registry["initiatives"][name]["intent"], "test intent")

        # Verify git branch
        import subprocess

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertIn(f"initiative/{name}", branches)

    def test_kickoff_no_drafts(self):
        self.init_git()
        name = "empty-init"
        kickoff.kickoff(name, "no drafts")

        active_dir = self.cicadas_dir / "active" / name
        self.assertTrue(active_dir.exists())

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertIn(name, registry["initiatives"])
        self.assertEqual(registry["initiatives"][name]["signals"], [])

    def test_kickoff_promotes_lifecycle_json(self):
        """When drafts contain lifecycle.json, kickoff promotes it to active."""
        name = "with-lifecycle"
        draft_dir = self.cicadas_dir / "drafts" / name
        draft_dir.mkdir(parents=True)
        (draft_dir / "prd.md").write_text("# Test PRD")
        lifecycle_content = '{"initiative": "with-lifecycle", "pr_boundaries": {"specs": false}, "steps": []}'
        (draft_dir / "lifecycle.json").write_text(lifecycle_content)

        self.init_git()
        kickoff.kickoff(name, "test intent")

        active_lifecycle = self.cicadas_dir / "active" / name / "lifecycle.json"
        self.assertTrue(active_lifecycle.exists())
        self.assertEqual(active_lifecycle.read_text(), lifecycle_content)
        self.assertFalse(draft_dir.exists())

    def test_kickoff_promotes_all_draft_files(self):
        """All files in the draft directory (prd, tech-design, tasks, lifecycle) are promoted."""
        name = "multi-file"
        draft_dir = self.cicadas_dir / "drafts" / name
        draft_dir.mkdir(parents=True)
        (draft_dir / "prd.md").write_text("# PRD")
        (draft_dir / "tech-design.md").write_text("# Tech")
        (draft_dir / "tasks.md").write_text("# Tasks")
        (draft_dir / "lifecycle.json").write_text('{"initiative": "multi-file", "steps": []}')

        self.init_git()
        kickoff.kickoff(name, "multi file test")

        active = self.cicadas_dir / "active" / name
        self.assertTrue((active / "prd.md").exists())
        self.assertTrue((active / "tech-design.md").exists())
        self.assertTrue((active / "tasks.md").exists())
        self.assertTrue((active / "lifecycle.json").exists())
        self.assertFalse(draft_dir.exists())

    def test_kickoff_creates_tokens_json(self):
        """kickoff initializes tokens.json in the active directory."""
        name = "token-init"
        self.init_git()
        kickoff.kickoff(name, "token test")

        tokens_path = self.cicadas_dir / "active" / name / "tokens.json"
        self.assertTrue(tokens_path.exists())
        data = json.loads(tokens_path.read_text())
        self.assertIn("entries", data)

    def test_kickoff_creates_worktree(self):
        """kickoff creates a linked worktree and stays on the original branch."""
        self.init_git()
        original_branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=self.root
        ).decode().strip()

        kickoff.kickoff("wt-test", "worktree test")

        # Main worktree stays on original branch
        current = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=self.root
        ).decode().strip()
        self.assertEqual(current, original_branch)

        # Worktree directory was created
        expected_wt = self.root.parent / f"{self.root.name}-initiative-wt-test"
        self.assertTrue(expected_wt.exists())

        # Registry records the worktree path
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertIn("worktree_path", registry["initiatives"]["wt-test"])

    def test_kickoff_existing(self):
        self.init_git()
        name = "exists"
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["initiatives"][name] = {"intent": "old"}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        # Should just print that it already exists
        kickoff.kickoff(name, "new")

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertEqual(registry["initiatives"][name]["intent"], "old")


if __name__ == "__main__":
    unittest.main()
