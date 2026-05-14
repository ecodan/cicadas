# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import io
import json
import unittest
from contextlib import redirect_stdout

import archive
import status
from base import CicadasTest


class TestArchiveStatus(CicadasTest):
    def test_archive_branch(self):
        name = "feat-to-archive"
        # Setup branch in registry and active spec
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"][name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "spec.md").write_text("# Spec")

        # Run archive
        archive.archive(name, type_="branch")

        # Verify removed from registry
        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertNotIn(name, reg["branches"])

        # Verify moved to archive
        # Archive dir contains ts-name
        arch_roots = [r.name for r in (self.cicadas_dir / "archive").iterdir()]
        self.assertTrue(any(name in r for r in arch_roots))

        # Verify active dir removed
        self.assertFalse(active_dir.exists())

    def test_archive_includes_lifecycle_json(self):
        """When active contains lifecycle.json, archive moves it with the rest of active."""
        name = "init-with-lifecycle"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "prd.md").write_text("# PRD")
        (active_dir / "lifecycle.json").write_text('{"initiative": "init-with-lifecycle", "steps": []}')

        archive.archive(name, type_="initiative")

        arch_dirs = list((self.cicadas_dir / "archive").iterdir())
        self.assertEqual(len(arch_dirs), 1)
        husk = arch_dirs[0]
        self.assertTrue((husk / "lifecycle.json").exists())
        self.assertEqual((husk / "lifecycle.json").read_text(), '{"initiative": "init-with-lifecycle", "steps": []}')

    def test_archive_significance_check(self):
        name = "fix/my-bug"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"][name] = {"intent": "bug"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        # Significance check alert only prints if active dir exists
        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)

        f = io.StringIO()
        with redirect_stdout(f):
            archive.archive(name, type_="branch")

        output = f.getvalue()
        self.assertIn("!!! LIGHTWEIGHT PATH SIGNIFICANCE CHECK !!!", output)
        # Archive must still complete despite the warning
        with open(self.cicadas_dir / "registry.json") as f2:
            reg = json.load(f2)
        self.assertNotIn(name, reg["branches"])
        # Verify something was written to the archive directory
        self.assertTrue(any((self.cicadas_dir / "archive").iterdir()))

    def test_archive_registered_lightweight_branch_uses_initiative_active_dir(self):
        init_name = "my-bug"
        branch_name = "fix/my-bug"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "bug"}
            reg["branches"][branch_name] = {"intent": "bug", "initiative": init_name}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / init_name
        active_dir.mkdir(parents=True)
        (active_dir / "buglet.md").write_text("# Bug")

        archive.archive(branch_name, type_="branch")

        self.assertFalse(active_dir.exists())
        archived_files = list((self.cicadas_dir / "archive").glob("*-my-bug/buglet.md"))
        self.assertEqual(len(archived_files), 1)
        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertNotIn(branch_name, reg["branches"])

    def test_archive_initiative_deregisters_associated_branches(self):
        """Archiving an initiative must also remove its linked branches from the registry."""
        init_name = "my-initiative"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test initiative"}
            reg["branches"]["feat/part-1"] = {"intent": "part 1", "initiative": init_name}
            reg["branches"]["tweak/side-fix"] = {"intent": "side fix", "initiative": init_name}
            reg["branches"]["feat/other"] = {"intent": "unrelated", "initiative": "other-initiative"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        (self.cicadas_dir / "active" / init_name).mkdir(parents=True)

        archive.archive(init_name, type_="initiative")

        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)

        # Initiative and its branches deregistered
        self.assertNotIn(init_name, reg["initiatives"])
        self.assertNotIn("feat/part-1", reg["branches"])
        self.assertNotIn("tweak/side-fix", reg["branches"])
        # Unrelated branch untouched
        self.assertIn("feat/other", reg["branches"])

    def test_status_categorization(self):
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"]["feat/f1"] = {"intent": "feat", "modules": []}
            reg["branches"]["fix/b1"] = {"intent": "bug", "modules": []}
            reg["branches"]["tweak/t1"] = {"intent": "tweak", "modules": []}
            reg["branches"]["skill/s1"] = {"intent": "skill", "modules": []}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()

        output = f.getvalue()
        self.assertIn("Active Feature Branches (1):", output)
        self.assertIn("Active Bugs (1):", output)
        self.assertIn("Active Tweaks (1):", output)
        self.assertIn("Active Skills (1):", output)
        self.assertIn("feat/f1", output)
        self.assertIn("fix/b1", output)
        self.assertIn("tweak/t1", output)
        self.assertIn("skill/s1", output)

    def test_skill_branch_not_counted_as_feature(self):
        """skill/ branches must not appear in the Active Feature Branches section."""
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"]["skill/my-tool"] = {"intent": "build tool skill", "modules": []}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()

        output = f.getvalue()
        self.assertIn("Active Skills (1):", output)
        self.assertNotIn("Active Feature Branches (1):", output)

    def test_archive_skill_initiative(self):
        """Archiving a skill-prefixed initiative works correctly."""
        init_name = "skill-pdf"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "pdf skill"}
            reg["branches"]["skill/pdf"] = {"intent": "pdf skill branch", "initiative": init_name}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        (self.cicadas_dir / "active" / init_name).mkdir(parents=True)
        (self.cicadas_dir / "active" / init_name / "SKILL.md").write_text("# Skill")

        archive.archive(init_name, type_="initiative")

        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertNotIn(init_name, reg["initiatives"])
        self.assertNotIn("skill/pdf", reg["branches"])

        arch_dirs = [d.name for d in (self.cicadas_dir / "archive").iterdir()]
        self.assertTrue(any(init_name in d for d in arch_dirs))

    def test_status_lifecycle_section_when_lifecycle_exists(self):
        """When an initiative has active lifecycle.json, status prints a Lifecycle section with Next step."""
        init_name = "with-lifecycle"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test initiative"}
            reg["branches"]["feat/part1"] = {"intent": "part 1", "initiative": init_name, "modules": []}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        (self.cicadas_dir / "active" / init_name).mkdir(parents=True)
        (self.cicadas_dir / "active" / init_name / "lifecycle.json").write_text(
            '{"initiative": "with-lifecycle", "steps": [{"id": "complete_feature", "name": "Complete each feature"}]}'
        )

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()

        output = f.getvalue()
        self.assertIn("Lifecycle (with-lifecycle):", output)
        self.assertIn("Next:", output)


class TestArchiveWorktree(CicadasTest):
    """Worktree teardown tests for archive.py."""

    def setUp(self):
        super().setUp()
        self.init_git()
        import subprocess
        subprocess.run(["git", "checkout", "-b", "feat/wt-branch"], cwd=self.root, check=True, capture_output=True)
        import utils
        from utils import worktree_path
        self.wt_dir = worktree_path(self.root, "feat/wt-branch")
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        # Create the worktree
        utils.create_worktree(self.root, "feat/wt-branch", self.wt_dir)
        # Register in registry
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["branches"]["feat/wt-branch"] = {"intent": "test", "worktree_path": str(self.wt_dir)}
        utils.save_json(self.cicadas_dir / "registry.json", reg)

    def tearDown(self):
        import subprocess
        if self.wt_dir.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(self.wt_dir)], cwd=self.root, capture_output=True)
        super().tearDown()

    def test_archive_cleans_worktree(self):
        import utils
        archive.archive("feat/wt-branch", type_="branch")
        # Worktree should be removed
        self.assertFalse(self.wt_dir.exists())
        # worktree_path should be absent from registry (branch deregistered)
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertNotIn("feat/wt-branch", reg["branches"])

    def test_archive_dirty_worktree_exits_without_force(self):
        import sys
        (self.wt_dir / "dirty.txt").write_text("uncommitted")
        with self.assertRaises(SystemExit) as cm:
            archive.archive("feat/wt-branch", type_="branch", force=False)
        self.assertEqual(cm.exception.code, 1)
        # Worktree should still exist
        self.assertTrue(self.wt_dir.exists())

    def test_archive_dirty_worktree_force_removes(self):
        (self.wt_dir / "dirty.txt").write_text("uncommitted")
        archive.archive("feat/wt-branch", type_="branch", force=True)
        self.assertFalse(self.wt_dir.exists())

    def test_archive_missing_worktree_dir_warns_and_continues(self):
        """If worktree dir was already deleted, archive should still proceed and clear registry."""
        import shutil, utils
        shutil.rmtree(self.wt_dir)
        # Prune the worktree from git's list
        import subprocess
        subprocess.run(["git", "worktree", "prune"], cwd=self.root, capture_output=True)
        f = io.StringIO()
        with redirect_stdout(f):
            archive.archive("feat/wt-branch", type_="branch")
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        self.assertNotIn("feat/wt-branch", reg["branches"])


class TestStatusWorktrees(CicadasTest):
    """Worktrees section in status.py output."""

    def test_no_worktrees_section_when_none(self):
        """If no branches have worktree_path, the Worktrees section must not appear."""
        import utils
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["branches"]["feat/normal"] = {"intent": "normal", "modules": []}
        utils.save_json(self.cicadas_dir / "registry.json", reg)
        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        self.assertNotIn("Worktrees", f.getvalue())

    def test_worktrees_section_shows_missing(self):
        """A branch with a nonexistent worktree_path is shown as [MISSING]."""
        import utils
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["branches"]["feat/gone"] = {"intent": "gone", "modules": [], "worktree_path": "/nonexistent/wt/path"}
        utils.save_json(self.cicadas_dir / "registry.json", reg)
        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()
        self.assertIn("Worktrees", out)
        self.assertIn("[MISSING]", out)
        self.assertIn("feat/gone", out)

    def test_worktrees_section_shows_clean(self):
        """A branch with a real clean worktree shows [clean] and HEAD."""
        self.init_git()
        import subprocess
        import utils
        subprocess.run(["git", "checkout", "-b", "feat/wt-clean"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        wt = utils.worktree_path(self.root, "feat/wt-clean")
        utils.create_worktree(self.root, "feat/wt-clean", wt)
        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["branches"]["feat/wt-clean"] = {"intent": "clean", "modules": [], "worktree_path": str(wt)}
        utils.save_json(self.cicadas_dir / "registry.json", reg)
        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=self.root, capture_output=True)
        out = f.getvalue()
        self.assertIn("[clean]", out)
        self.assertIn("feat/wt-clean", out)

    def test_worktrees_section_includes_initiatives(self):
        import utils

        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["initiatives"]["wt-init"] = {"intent": "initiative", "worktree_path": "/tmp/wt-init"}
        utils.save_json(self.cicadas_dir / "registry.json", reg)

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()

        out = f.getvalue()
        self.assertIn("Worktrees", out)
        self.assertIn("initiative/wt-init", out)

    def test_check_warns_for_stale_initiative_worktree(self):
        import check
        import utils

        reg = utils.load_json(self.cicadas_dir / "registry.json")
        reg["initiatives"]["stale-init"] = {"intent": "initiative", "worktree_path": "/nonexistent/init/wt"}
        utils.save_json(self.cicadas_dir / "registry.json", reg)

        f = io.StringIO()
        with redirect_stdout(f):
            check.check_conflicts()

        self.assertIn("initiative: stale-init", f.getvalue())


class TestStatusLifecycleMerge(CicadasTest):
    """Tests for _is_merged_into, _ref_exists, and _lifecycle_merge_status via real git repos."""

    def setUp(self):
        super().setUp()
        self.init_git()

    def _register_initiative_with_lifecycle(self, init_name: str, feat_branches: list[str], steps: list[dict] | None = None):
        if steps is None:
            steps = [
                {"id": "complete_feature", "name": "Complete each feature"},
                {"id": "complete_initiative", "name": "Complete the initiative"},
            ]
        reg = json.loads((self.cicadas_dir / "registry.json").read_text())
        reg["initiatives"][init_name] = {"intent": "test"}
        for fb in feat_branches:
            reg["branches"][fb] = {"intent": "test feat", "initiative": init_name, "modules": []}
        (self.cicadas_dir / "registry.json").write_text(json.dumps(reg))

        (self.cicadas_dir / "active" / init_name).mkdir(parents=True)
        (self.cicadas_dir / "active" / init_name / "lifecycle.json").write_text(
            json.dumps({"initiative": init_name, "steps": steps})
        )

    def test_ref_exists_for_real_branch(self):
        import subprocess
        subprocess.run(["git", "checkout", "-b", "feat/real"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        self.assertTrue(status._ref_exists(self.root, "feat/real"))

    def test_ref_exists_false_for_nonexistent(self):
        self.assertFalse(status._ref_exists(self.root, "feat/ghost-branch-xyz"))

    def test_is_merged_into_true_after_merge(self):
        import subprocess
        subprocess.run(["git", "checkout", "-b", "feat/merged"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "merge", "feat/merged", "--no-ff", "-m", "merge"], cwd=self.root, check=True, capture_output=True)
        self.assertTrue(status._is_merged_into(self.root, "feat/merged", "master"))

    def test_is_merged_into_false_before_merge(self):
        import subprocess
        subprocess.run(["git", "checkout", "-b", "feat/unmerged"], cwd=self.root, check=True, capture_output=True)
        (self.root / "new.txt").write_text("new")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "new commit"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        self.assertFalse(status._is_merged_into(self.root, "feat/unmerged", "master"))

    def _make_commit(self, filename: str):
        """Write and commit a file so branches have diverging histories."""
        import subprocess
        (self.root / filename).write_text(f"content of {filename}")
        subprocess.run(["git", "add", filename], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"add {filename}"], cwd=self.root, check=True, capture_output=True)

    def test_next_step_is_complete_feature_when_feats_open(self):
        """When feature branches exist but are not merged, Next should be 'Complete each feature'."""
        import subprocess
        subprocess.run(["git", "checkout", "-b", "initiative/my-init"], cwd=self.root, check=True, capture_output=True)
        # Commit on initiative so it's ahead of master (not trivially merged into master)
        self._make_commit("init1.txt")
        subprocess.run(["git", "checkout", "-b", "feat/part1"], cwd=self.root, check=True, capture_output=True)
        # Add a commit on feat/part1 so it's ahead of initiative/my-init and not trivially merged
        self._make_commit("feat1.txt")
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        self._register_initiative_with_lifecycle("my-init", ["feat/part1"])

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()
        self.assertIn("Complete each feature", out)

    def test_next_step_is_complete_initiative_when_all_feats_merged(self):
        """When all feat branches are merged into initiative, Next should be 'Complete the initiative'."""
        import subprocess
        subprocess.run(["git", "checkout", "-b", "initiative/my-init2"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "feat/part1"], cwd=self.root, check=True, capture_output=True)
        self._make_commit("feat2.txt")
        subprocess.run(["git", "checkout", "initiative/my-init2"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "merge", "feat/part1", "--no-ff", "-m", "merge feat"], cwd=self.root, check=True, capture_output=True)
        # Do NOT merge initiative into master — initiative still open
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        self._register_initiative_with_lifecycle("my-init2", ["feat/part1"])

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()
        self.assertIn("Complete the initiative", out)

    def test_next_step_is_done_when_initiative_merged_to_default(self):
        """When initiative branch is merged to master, status shows 'Initiative complete'."""
        import subprocess
        subprocess.run(["git", "checkout", "-b", "initiative/my-init3"], cwd=self.root, check=True, capture_output=True)
        self._make_commit("init3.txt")
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "merge", "initiative/my-init3", "--no-ff", "-m", "merge init"], cwd=self.root, check=True, capture_output=True)
        self._register_initiative_with_lifecycle("my-init3", [])

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()
        self.assertIn("Initiative complete", out)

    def test_merged_pair_reported_when_feat_merged_into_initiative(self):
        """A merged feat→initiative pair must appear in the Merged: lines."""
        import subprocess
        subprocess.run(["git", "checkout", "-b", "initiative/my-init4"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "feat/part1"], cwd=self.root, check=True, capture_output=True)
        self._make_commit("feat4.txt")
        subprocess.run(["git", "checkout", "initiative/my-init4"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "merge", "feat/part1", "--no-ff", "-m", "merge"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=self.root, capture_output=True)
        self._register_initiative_with_lifecycle("my-init4", ["feat/part1"])

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()
        self.assertIn("Merged:", out)
        self.assertIn("feat/part1", out)


    def test_archive_emits_specs_archived_event(self):
        """archive() writes a specs.archived event to events.jsonl before moving the active dir."""
        name = "event-archive-test"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "prd.md").write_text("# Spec")

        archive.archive(name, type_="initiative")

        # events.jsonl must have been moved into the archive along with the spec
        arch_dir = next(d for d in (self.cicadas_dir / "archive").iterdir() if name in d.name)
        events_path = arch_dir / "events.jsonl"
        self.assertTrue(events_path.exists(), "events.jsonl should be in the archive after move")

        events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["type"], "specs.archived")
        self.assertEqual(ev["initiative"], name)
        self.assertEqual(ev["data"]["type"], "initiative")

    def test_status_shows_recent_events(self):
        """show_status() includes a 'Recent events' block for an initiative with events."""
        name = "status-event-test"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][name] = {"intent": "test", "signals": []}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        # Write two events directly to events.jsonl
        from datetime import datetime, timezone
        events_path = self.cicadas_dir / "active" / name / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        events_path.write_text(
            '{"timestamp":"' + ts + '","type":"initiative.kicked_off","initiative":"' + name + '","branch":"master","data":{}}\n'
            '{"timestamp":"' + ts + '","type":"branch.created","initiative":"' + name + '","branch":"feat/x","data":{}}\n'
        )

        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()

        self.assertIn("Recent events", out)
        self.assertIn("initiative.kicked_off", out)
        self.assertIn("branch.created", out)


class TestStatusNextStepHints(CicadasTest):
    """Tests for _infer_next_step() and status hint printing."""

    def test_no_cicadas_dir_shows_init_hint(self):
        """When .cicadas/ does not exist, status shows friendly message and init hint."""
        import shutil
        from unittest.mock import patch
        # Remove .cicadas directory
        shutil.rmtree(self.cicadas_dir)
        
        f = io.StringIO()
        with redirect_stdout(f), patch("sys.stdout.isatty", return_value=True):
            status.show_status()
        out = f.getvalue()
        
        self.assertIn("No Cicadas project initialized", out)
        self.assertIn("No Cicadas project found", out)
        self.assertIn("Initialize cicadas", out)

    def test_no_initiatives_shows_start_initiative_hint(self):
        """When .cicadas/ exists but no initiatives, show start initiative hint."""
        from unittest.mock import patch
        # Registry exists but is empty
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump({"initiatives": {}, "branches": {}}, f)
        
        f = io.StringIO()
        with redirect_stdout(f), patch("sys.stdout.isatty", return_value=True):
            status.show_status()
        out = f.getvalue()
        
        self.assertIn("Start your first initiative", out)
        self.assertIn("Start an initiative called", out)

    def test_initiative_no_branches_shows_build_partition_hint(self):
        """When initiative exists but no feature branches, show build partition hint."""
        from unittest.mock import patch
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump({
                "initiatives": {"my-init": {"intent": "test"}},
                "branches": {}
            }, f)
        
        f = io.StringIO()
        with redirect_stdout(f), patch("sys.stdout.isatty", return_value=True):
            status.show_status()
        out = f.getvalue()
        
        self.assertIn("Next: build your first partition", out)
        self.assertIn("Implement partition", out)

    def test_branches_no_lifecycle_shows_complete_partition_hint(self):
        """When feature branches exist but no lifecycle.json, show complete partition hint."""
        from unittest.mock import patch
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump({
                "initiatives": {"my-init": {"intent": "test"}},
                "branches": {"feat/test": {"intent": "test", "initiative": "my-init"}}
            }, f)
        
        f = io.StringIO()
        with redirect_stdout(f), patch("sys.stdout.isatty", return_value=True):
            status.show_status()
        out = f.getvalue()
        
        self.assertIn("Next: complete the current partition", out)
        self.assertIn("Code review and complete partition", out)

    def test_lifecycle_json_suppresses_infer_hint(self):
        """When lifecycle.json exists, _infer_next_step returns None (lifecycle handles it)."""
        init_name = "my-init"
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump({
                "initiatives": {init_name: {"intent": "test"}},
                "branches": {"feat/test": {"intent": "test", "initiative": init_name}}
            }, f)
        
        # Create lifecycle.json
        active_dir = self.cicadas_dir / "active" / init_name
        active_dir.mkdir(parents=True, exist_ok=True)
        (active_dir / "lifecycle.json").write_text('{"steps": []}')
        
        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status()
        out = f.getvalue()
        
        # Should not see the inferred hint (lifecycle takes over)
        self.assertNotIn("Next: complete the current partition", out)

    def test_no_hints_flag_suppresses_hint_output(self):
        """When --no-hints is passed, hint box should not appear."""
        import argparse
        import sys
        
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump({
                "initiatives": {"my-init": {"intent": "test"}},
                "branches": {}
            }, f)
        
        # Simulate --no-hints argument
        args = argparse.Namespace(no_hints=True)
        
        f = io.StringIO()
        with redirect_stdout(f):
            status.show_status(args)
        out = f.getvalue()
        
        # Should see the status but NOT the hint box
        self.assertIn("Active Initiatives", out)
        self.assertNotIn("Start your first initiative", out)

    def test_archive_hint_present_when_run_as_main(self):
        """When run as __main__ with TTY, archive prints hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        name = "feat-to-archive"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"][name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "spec.md").write_text("# Spec")
        
        buf = io.StringIO()
        test_args = ["archive.py", name]
        
        with patch("sys.argv", test_args):
            with patch("utils.hints_enabled", return_value=True):
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("archive", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertIn("You're done! Start your next initiative any time.", output)

    def test_archive_hint_suppressed_with_no_hints_flag(self):
        """When run as __main__ with --no-hints, archive suppresses hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        name = "feat-no-hint"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"][name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "spec.md").write_text("# Spec")
        
        buf = io.StringIO()
        test_args = ["archive.py", name, "--no-hints"]
        
        with patch("sys.argv", test_args):
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                try:
                    runpy.run_module("archive", run_name="__main__", alter_sys=True)
                except SystemExit:
                    pass
        
        output = buf.getvalue()
        self.assertNotIn("You're done! Start your next initiative any time.", output)



if __name__ == "__main__":
    unittest.main()
