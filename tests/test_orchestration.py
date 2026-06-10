# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

# Import signalboard.py using importlib to avoid conflict with builtin 'signal' module (though renamed, it's safer)
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

import prune
import update_index
from base import CicadasTest

SCRIPTS_DIR = Path(__file__).parent.parent / "src" / "cicadas" / "scripts"
spec = importlib.util.spec_from_file_location("cicadas_signal", SCRIPTS_DIR / "signalboard.py")
cicadas_signal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cicadas_signal)


class TestOrchestration(CicadasTest):
    def setUp(self):
        super().setUp()
        self.init_git()
        import utils
        self.default_branch = utils.get_default_branch()

    def test_end_to_end_kickoff_branch_archive_index(self):
        """Full lifecycle: kickoff → register branch → archive branch → log to index."""
        import kickoff as kickoff_mod
        import archive as archive_mod

        init_name = "e2e-init"
        feat_name = "feat/e2e-part1"

        # 1. Kickoff: draft → active, initiative branch created
        draft_dir = self.cicadas_dir / "drafts" / init_name
        draft_dir.mkdir(parents=True)
        (draft_dir / "prd.md").write_text("# PRD")
        kickoff_mod.kickoff(init_name, "end-to-end test initiative")

        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertIn(init_name, reg["initiatives"])
        self.assertTrue((self.cicadas_dir / "active" / init_name / "prd.md").exists())

        # 2. Register a feature branch.
        subprocess.run(["git", "checkout", "-b", feat_name], cwd=self.root, check=True, capture_output=True)
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"][feat_name] = {"intent": "part 1", "initiative": init_name, "modules": ["core"]}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()
        (self.cicadas_dir / "active" / feat_name).mkdir(parents=True)
        (self.cicadas_dir / "active" / feat_name / "tasks.md").write_text("- [x] task1\n")

        # 3. Archive the feature branch
        subprocess.run(["git", "checkout", self.default_branch], cwd=self.root, capture_output=True)
        archive_mod.archive(feat_name, type_="branch")

        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertNotIn(feat_name, reg["branches"])
        self.assertIn(init_name, reg["initiatives"])  # initiative still active

        # 4. Log to index
        update_index.update_index(feat_name, "completed e2e part 1", modules="core")

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)
        self.assertEqual(len(index["entries"]), 1)
        self.assertEqual(index["entries"][0]["branch"], feat_name)
        self.assertEqual(index["entries"][0]["modules"], ["core"])

    def test_prune_branch(self):
        name = "feat/to-prune"
        subprocess.run(["git", "checkout", "-b", name], cwd=self.root, check=True)
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["branches"][name] = {"intent": "test"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "draft-spec.md").write_text("# Spec")

        prune.prune(name, type_="branch")

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn(name, branches)
        self.assertTrue((self.cicadas_dir / "drafts" / name / "draft-spec.md").exists())
        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        self.assertNotIn(name, reg["branches"])

    def test_signal_basic(self):
        init_name = "test-init"
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][init_name] = {"intent": "test", "signals": []}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        cicadas_signal.send_signal("test message", initiative=init_name)

        with open(self.cicadas_dir / "registry.json") as f:
            reg = json.load(f)
        signals = reg["initiatives"][init_name]["signals"]
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["message"], "test message")


if __name__ == "__main__":
    unittest.main()
