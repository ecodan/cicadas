# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import unittest

import prune
from base import CicadasTest


class TestPrune(CicadasTest):
    def test_prune_branch(self):
        self.init_git()
        name = "feat/to-prune"
        subprocess.run(["git", "checkout", "-b", name], cwd=self.root, check=True)

        # Register and create active specs
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["branches"][name] = {"modules": []}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        (self.cicadas_dir / "active" / name).mkdir(parents=True)
        (self.cicadas_dir / "active" / name / "task.md").write_text("todo")

        prune.prune(name, "branch")

        # Verify specs restored to drafts
        self.assertTrue((self.cicadas_dir / "drafts" / name).exists())
        self.assertTrue((self.cicadas_dir / "drafts" / name / "task.md").exists())
        self.assertFalse((self.cicadas_dir / "active" / name).exists())

        # Verify removed from registry
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertNotIn(name, registry["branches"])

        # Verify git branch deleted (might fail if checkout fails, but here we are on the default branch)
        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn(name, branches)

    def test_prune_registered_lightweight_branch_uses_initiative_active_dir(self):
        self.init_git()
        init_name = "my-bug"
        branch_name = "fix/my-bug"
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.root, check=True)
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["initiatives"][init_name] = {"intent": "bug"}
        registry["branches"][branch_name] = {"modules": [], "initiative": init_name}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        active_dir = self.cicadas_dir / "active" / init_name
        active_dir.mkdir(parents=True)
        (active_dir / "buglet.md").write_text("todo")

        prune.prune(branch_name, "branch")

        self.assertFalse(active_dir.exists())
        self.assertTrue((self.cicadas_dir / "drafts" / init_name / "buglet.md").exists())

    def test_prune_initiative(self):
        self.init_git()
        name = "init-to-prune"
        branch_name = f"initiative/{name}"
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.root, check=True)

        # Register
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["initiatives"][name] = {"intent": "test"}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        (self.cicadas_dir / "active" / name).mkdir(parents=True)

        prune.prune(name, "initiative")

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertNotIn(name, registry["initiatives"])

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn(branch_name, branches)

    def test_prune_non_existent(self):
        prune.prune("ghost", "branch")
        prune.prune("ghost", "initiative")
        # Should just print error messages

    def test_prune_skill_initiative(self):
        """Pruning a skill-prefixed initiative deregisters it and restores specs to drafts."""
        self.init_git()
        name = "skill-pdf"
        branch_name = f"initiative/{name}"
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.root, check=True)

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["initiatives"][name] = {"intent": "pdf skill"}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "SKILL.md").write_text("# Skill")

        prune.prune(name, "initiative")

        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        self.assertNotIn(name, registry["initiatives"])
        self.assertTrue((self.cicadas_dir / "drafts" / name).exists())

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn(branch_name, branches)


if __name__ == "__main__":
    unittest.main()
