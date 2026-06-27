# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import io
import subprocess
import unittest
from contextlib import redirect_stdout

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

    def test_kickoff_creates_worktree(self):
        """kickoff creates a linked worktree when explicitly requested and stays on the original branch."""
        self.init_git()
        original_branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=self.root
        ).decode().strip()

        kickoff.kickoff("wt-test", "worktree test", force_worktree=True)

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

    def test_kickoff_does_not_create_worktree_by_default(self):
        self.init_git()

        kickoff.kickoff("no-wt-test", "default kickoff")

        expected_wt = self.root.parent / f"{self.root.name}-initiative-no-wt-test"
        self.assertFalse(expected_wt.exists())

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertNotIn("worktree_path", registry["initiatives"]["no-wt-test"])

    def test_kickoff_uses_config_to_create_worktree(self):
        self.init_git()
        config = {"project_name": self.root.name, "auto_worktrees": {"initiatives": True}}
        (self.cicadas_dir / "config.json").write_text(json.dumps(config))

        kickoff.kickoff("config-wt-test", "config kickoff")

        expected_wt = self.root.parent / f"{self.root.name}-initiative-config-wt-test"
        self.assertTrue(expected_wt.exists())

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertIn("worktree_path", registry["initiatives"]["config-wt-test"])

    def test_kickoff_warns_when_worktree_creation_fails(self):
        self.init_git()
        conflicting_path = self.root.parent / f"{self.root.name}-initiative-wt-conflict"
        conflicting_path.mkdir()

        buf = io.StringIO()
        with redirect_stdout(buf):
            kickoff.kickoff("wt-conflict", "conflict kickoff", force_worktree=True)

        output = buf.getvalue()
        self.assertIn("Could not create worktree", output)

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertNotIn("worktree_path", registry["initiatives"]["wt-conflict"])

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


    def test_kickoff_emits_initiative_kicked_off_event(self):
        """kickoff writes an initiative.kicked_off event to events.jsonl."""
        name = "event-init"
        self.init_git()
        kickoff.kickoff(name, "event test intent")

        events_path = self.cicadas_dir / "active" / name / "events.jsonl"
        self.assertTrue(events_path.exists(), "events.jsonl should be created by kickoff")

        lines = [l for l in events_path.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["type"], "initiative.kicked_off")
        self.assertEqual(event["initiative"], name)
        self.assertEqual(event["data"]["intent"], "event test intent")

    def test_kickoff_hint_present_when_run_as_main(self):
        """When run as __main__ with TTY, kickoff prints hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        name = "hint-init"
        self.init_git()
        
        buf = io.StringIO()
        test_args = ["kickoff.py", name, "--intent", "hint test intent"]
        
        with patch("sys.argv", test_args):
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                # Redirect actual print calls to buffer to capture output
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("kickoff", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertIn("Next: build your first partition", output)

    def test_kickoff_hint_suppressed_with_no_hints_flag(self):
        """When run as __main__ with --no-hints, kickoff suppresses hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        name = "no-hint-init"
        self.init_git()
        
        buf = io.StringIO()
        test_args = ["kickoff.py", name, "--intent", "no hint test", "--no-hints"]
        
        with patch("sys.argv", test_args):
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("kickoff", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertNotIn("Next: build your first partition", output)


if __name__ == "__main__":
    unittest.main()
