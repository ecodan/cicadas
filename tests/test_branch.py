# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import io
import shutil
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path

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
        subprocess.run(["git", "branch", f"initiative/{init_name}"], cwd=self.root, check=True, capture_output=True)

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

        # Main worktree switches to the branch by default (no worktree unless explicitly enabled)
        curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=self.root).decode().strip()
        self.assertEqual(curr, branch_name)

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

        # Main worktree switches to the branch by default (no worktree unless explicitly enabled)
        curr = subprocess.check_output(["git", "branch", "--show-current"], cwd=self.root).decode().strip()
        self.assertEqual(curr, branch_name)

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

    def test_lightweight_branch_does_not_get_worktree_by_default(self):
        import utils
        branch.create_branch("tweak/plain-lightweight", "plain tweak", "", initiative=self.init_name)
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertNotIn("worktree_path", reg["branches"]["tweak/plain-lightweight"])

    def test_lightweight_branch_can_force_worktree(self):
        import utils
        expected_wt = utils.worktree_path(self.root, "tweak/forced-lightweight")
        self._worktree_dirs.append(expected_wt)

        branch.create_branch("tweak/forced-lightweight", "forced tweak", "", initiative=self.init_name, force_worktree=True)

        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertEqual(
            reg["branches"]["tweak/forced-lightweight"]["worktree_path"],
            str(expected_wt.resolve()),
        )

    def test_lightweight_branch_uses_config_to_create_worktree(self):
        import utils
        expected_wt = utils.worktree_path(self.root, "tweak/config-lightweight")
        self._worktree_dirs.append(expected_wt)
        (self.cicadas_dir / "config.json").write_text(
            json.dumps({"project_name": self.root.name, "auto_worktrees": {"lightweight": True}})
        )

        branch.create_branch("tweak/config-lightweight", "config tweak", "", initiative=self.init_name)

        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertEqual(
            reg["branches"]["tweak/config-lightweight"]["worktree_path"],
            str(expected_wt.resolve()),
        )

    def test_parallel_partition_respects_config_disable(self):
        import utils
        (self.cicadas_dir / "config.json").write_text(
            json.dumps({"project_name": self.root.name, "auto_worktrees": {"parallel_features": False}})
        )

        branch.create_branch("feat/parallel-branch", "parallel intent", "src/foo", initiative=self.init_name)

        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertNotIn("worktree_path", reg["branches"]["feat/parallel-branch"])

    def test_force_worktree_warns_when_creation_fails(self):
        import utils
        expected_wt = utils.worktree_path(self.root, "tweak/conflict-lightweight")
        expected_wt.mkdir()

        buf = io.StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(buf):
                branch.create_branch(
                    "tweak/conflict-lightweight",
                    "conflict tweak",
                    "",
                    initiative=self.init_name,
                    force_worktree=True,
                )

        self.assertIn("git worktree add failed", buf.getvalue())

    def test_create_branch_uses_parent_ref_directly(self):
        subprocess.run(["git", "checkout", "-b", "feat/base-parent"], cwd=self.root, check=True, capture_output=True)
        (self.root / "parent.txt").write_text("parent")
        subprocess.run(["git", "add", "parent.txt"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "parent commit"], cwd=self.root, check=True, capture_output=True)
        parent_hash = subprocess.check_output(["git", "rev-parse", "feat/base-parent"], cwd=self.root).decode().strip()
        subprocess.run(["git", "checkout", self.default_branch], cwd=self.root, check=True, capture_output=True)

        branch.create_branch("feat/from-parent", "from explicit parent", "src/foo", from_branch="feat/base-parent", no_worktree=True)

        branch_hash = subprocess.check_output(["git", "rev-parse", "feat/from-parent"], cwd=self.root).decode().strip()
        self.assertEqual(branch_hash, parent_hash)

    def test_create_branch_uses_remote_only_initiative_parent(self):
        remote_dir = Path(self.test_dir) / "origin.git"
        subprocess.run(["git", "init", "--bare", str(remote_dir)], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote_dir)], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", self.default_branch], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", f"initiative/{self.init_name}"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "branch", "-D", f"initiative/{self.init_name}"], cwd=self.root, check=True, capture_output=True)

        branch.create_branch("feat/from-remote-parent", "remote parent", "src/foo", initiative=self.init_name, no_worktree=True)

        branch_hash = subprocess.check_output(["git", "rev-parse", "feat/from-remote-parent"], cwd=self.root).decode().strip()
        remote_parent_hash = subprocess.check_output(
            ["git", "rev-parse", f"origin/initiative/{self.init_name}"], cwd=self.root
        ).decode().strip()
        self.assertEqual(branch_hash, remote_parent_hash)

    def test_create_branch_emits_branch_created_event(self):
        """create_branch writes a branch.created event to events.jsonl."""
        branch.create_branch("feat/event-branch", "event intent", "src/foo.py", initiative=self.init_name)

        events_path = self.cicadas_dir / "active" / self.init_name / "events.jsonl"
        self.assertTrue(events_path.exists(), "events.jsonl should be created by create_branch")

        events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        branch_events = [e for e in events if e["type"] == "branch.created"]
        self.assertEqual(len(branch_events), 1)
        ev = branch_events[0]
        self.assertEqual(ev["initiative"], self.init_name)
        self.assertEqual(ev["data"]["branch"], "feat/event-branch")
        self.assertEqual(ev["data"]["intent"], "event intent")


if __name__ == "__main__":
    unittest.main()
