# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import abort
from base import CicadasTest


class TestAbort(CicadasTest):
    def setUp(self):
        super().setUp()
        self.init_git()
        from utils import get_default_branch

        self.default_branch = get_default_branch()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reg(self):
        with open(self.cicadas_dir / "registry.json") as f:
            return json.load(f)

    def _write_reg(self, reg):
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(reg, f)

    def _register_tweak(self, tweak_name, initiative_name):
        reg = self._reg()
        reg["initiatives"][initiative_name] = {"intent": "tweak intent"}
        reg["branches"][f"tweak/{tweak_name}"] = {
            "intent": "tweak intent",
            "modules": [],
            "initiative": initiative_name,
        }
        self._write_reg(reg)

    def _register_fix(self, fix_name, initiative_name):
        reg = self._reg()
        reg["initiatives"][initiative_name] = {"intent": "fix intent"}
        reg["branches"][f"fix/{fix_name}"] = {
            "intent": "fix intent",
            "modules": [],
            "initiative": initiative_name,
        }
        self._write_reg(reg)

    def _register_feat(self, feat_name, initiative_name):
        reg = self._reg()
        reg["initiatives"][initiative_name] = {"intent": "initiative intent"}
        reg["branches"][f"feat/{feat_name}"] = {
            "intent": "feature intent",
            "modules": [],
            "initiative": initiative_name,
        }
        self._write_reg(reg)

    def _create_active_specs(self, initiative_name):
        active_dir = self.cicadas_dir / "active" / initiative_name
        active_dir.mkdir(parents=True, exist_ok=True)
        (active_dir / "tweaklet.md").write_text("# spec")

    def _git(self, *args):
        subprocess.run(list(args), cwd=self.root, check=True, capture_output=True)

    def _create_paired_branches(self, lightweight_branch, initiative_branch):
        """Create both a tweak/fix branch and its paired initiative branch; end on lightweight_branch."""
        self._git("git", "checkout", "-b", initiative_branch)
        self._git("git", "checkout", self.default_branch)
        self._git("git", "checkout", "-b", lightweight_branch)

    # ------------------------------------------------------------------
    # handle_docs
    # ------------------------------------------------------------------

    def test_handle_docs_no_active_specs_is_noop(self):
        with patch("abort.prompt_choice") as mock_prompt:
            abort.handle_docs("nonexistent", self.cicadas_dir)
            mock_prompt.assert_not_called()

    def test_handle_docs_move_to_drafts(self):
        self._create_active_specs("my-spec")
        with patch("abort.prompt_choice", return_value="D"):
            abort.handle_docs("my-spec", self.cicadas_dir)
        self.assertTrue((self.cicadas_dir / "drafts" / "my-spec").exists())
        self.assertFalse((self.cicadas_dir / "active" / "my-spec").exists())

    def test_handle_docs_delete(self):
        self._create_active_specs("del-spec")
        with patch("abort.prompt_choice", return_value="X"):
            abort.handle_docs("del-spec", self.cicadas_dir)
        self.assertFalse((self.cicadas_dir / "active" / "del-spec").exists())
        self.assertFalse((self.cicadas_dir / "drafts" / "del-spec").exists())

    # ------------------------------------------------------------------
    # delete_branch
    # ------------------------------------------------------------------

    def test_delete_branch_removes_git_branch(self):
        self._git("git", "checkout", "-b", "tweak/to-delete")
        abort.delete_branch("tweak/to-delete", self.root)
        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn("tweak/to-delete", branches)
        curr = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=self.root
        ).decode().strip()
        self.assertEqual(curr, self.default_branch)

    def test_delete_branch_nonexistent_prints_warning(self):
        out = StringIO()
        with redirect_stdout(out):
            abort.delete_branch("nonexistent/xyz", self.root)
        self.assertIn("Warning", out.getvalue())

    # ------------------------------------------------------------------
    # abort_lightweight (tweak/ and fix/)
    # ------------------------------------------------------------------

    def test_abort_tweak_moves_docs_to_drafts(self):
        self._register_tweak("my-tweak", "my-tweak")
        self._create_active_specs("my-tweak")
        self._create_paired_branches("tweak/my-tweak", "initiative/my-tweak")

        from utils import load_json

        registry = load_json(self.cicadas_dir / "registry.json")
        with patch("abort.prompt_choice", return_value="D"):
            abort.abort_lightweight(
                "tweak/my-tweak", "my-tweak", self.root, self.cicadas_dir, registry
            )

        self.assertTrue((self.cicadas_dir / "drafts" / "my-tweak").exists())
        self.assertFalse((self.cicadas_dir / "active" / "my-tweak").exists())
        reg = self._reg()
        self.assertNotIn("tweak/my-tweak", reg["branches"])
        self.assertNotIn("my-tweak", reg["initiatives"])

    def test_abort_tweak_deletes_docs(self):
        self._register_tweak("del-tweak", "del-tweak")
        self._create_active_specs("del-tweak")
        self._create_paired_branches("tweak/del-tweak", "initiative/del-tweak")

        from utils import load_json

        registry = load_json(self.cicadas_dir / "registry.json")
        with patch("abort.prompt_choice", return_value="X"):
            abort.abort_lightweight(
                "tweak/del-tweak", "del-tweak", self.root, self.cicadas_dir, registry
            )

        self.assertFalse((self.cicadas_dir / "active" / "del-tweak").exists())
        self.assertFalse((self.cicadas_dir / "drafts" / "del-tweak").exists())

    def test_abort_tweak_no_active_docs_skips_prompt(self):
        self._register_tweak("quiet-tweak", "quiet-tweak")
        self._create_paired_branches("tweak/quiet-tweak", "initiative/quiet-tweak")

        from utils import load_json

        registry = load_json(self.cicadas_dir / "registry.json")
        with patch("abort.prompt_choice") as mock_prompt:
            abort.abort_lightweight(
                "tweak/quiet-tweak", "quiet-tweak", self.root, self.cicadas_dir, registry
            )
            mock_prompt.assert_not_called()

        reg = self._reg()
        self.assertNotIn("tweak/quiet-tweak", reg["branches"])
        self.assertNotIn("quiet-tweak", reg["initiatives"])

    def test_abort_fix_moves_docs_to_drafts(self):
        self._register_fix("my-fix", "my-fix")
        self._create_active_specs("my-fix")
        self._create_paired_branches("fix/my-fix", "initiative/my-fix")

        from utils import load_json

        registry = load_json(self.cicadas_dir / "registry.json")
        with patch("abort.prompt_choice", return_value="D"):
            abort.abort_lightweight(
                "fix/my-fix", "my-fix", self.root, self.cicadas_dir, registry
            )

        self.assertTrue((self.cicadas_dir / "drafts" / "my-fix").exists())
        reg = self._reg()
        self.assertNotIn("fix/my-fix", reg["branches"])
        self.assertNotIn("my-fix", reg["initiatives"])

    # ------------------------------------------------------------------
    # abort_feature (feat/)
    # ------------------------------------------------------------------

    def test_abort_feature_only_keeps_initiative(self):
        self._register_feat("my-feat", "my-initiative")
        self._create_active_specs("my-initiative")
        self._git("git", "checkout", "-b", "initiative/my-initiative")
        self._git("git", "checkout", "-b", "feat/my-feat")

        from utils import load_json

        registry = load_json(self.cicadas_dir / "registry.json")
        # First prompt: scope (F=feature only); second: handle_docs (D=drafts)
        with patch("abort.prompt_choice", side_effect=["F", "D"]):
            abort.abort_feature(
                "feat/my-feat", "my-initiative", self.root, self.cicadas_dir, registry
            )

        reg = self._reg()
        self.assertNotIn("feat/my-feat", reg["branches"])
        self.assertIn("my-initiative", reg["initiatives"])

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn("feat/my-feat", branches)
        self.assertIn("initiative/my-initiative", branches)

        self.assertTrue((self.cicadas_dir / "drafts" / "my-initiative").exists())

    def test_abort_feature_entire_initiative(self):
        self._register_feat("big-feat", "big-init")
        self._create_active_specs("big-init")
        self._git("git", "checkout", "-b", "initiative/big-init")
        self._git("git", "checkout", "-b", "feat/big-feat")

        from utils import load_json

        registry = load_json(self.cicadas_dir / "registry.json")
        # First prompt: scope (I=initiative); second: handle_docs (X=delete)
        with patch("abort.prompt_choice", side_effect=["I", "X"]):
            abort.abort_feature(
                "feat/big-feat", "big-init", self.root, self.cicadas_dir, registry
            )

        reg = self._reg()
        self.assertNotIn("feat/big-feat", reg["branches"])
        self.assertNotIn("big-init", reg["initiatives"])

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn("feat/big-feat", branches)
        self.assertNotIn("initiative/big-init", branches)

        self.assertFalse((self.cicadas_dir / "active" / "big-init").exists())

    # ------------------------------------------------------------------
    # main() dispatch
    # ------------------------------------------------------------------

    def test_main_on_default_branch_exits_clean(self):
        """On the default branch, nothing to abort — exit 0."""
        with self.assertRaises(SystemExit) as cm:
            abort.main()
        self.assertEqual(cm.exception.code, 0)

    def test_main_dispatches_tweak_branch(self):
        self._register_tweak("dispatch-tweak", "dispatch-tweak")
        self._create_active_specs("dispatch-tweak")
        self._create_paired_branches("tweak/dispatch-tweak", "initiative/dispatch-tweak")

        with patch("abort.prompt_choice", return_value="D"):
            abort.main()

        reg = self._reg()
        self.assertNotIn("tweak/dispatch-tweak", reg["branches"])
        self.assertNotIn("dispatch-tweak", reg["initiatives"])
        self.assertTrue((self.cicadas_dir / "drafts" / "dispatch-tweak").exists())

    def test_main_dispatches_initiative_branch(self):
        reg = self._reg()
        reg["initiatives"]["direct-init"] = {"intent": "test"}
        self._write_reg(reg)
        self._create_active_specs("direct-init")
        self._git("git", "checkout", "-b", "initiative/direct-init")

        with patch("abort.prompt_choice", return_value="D"):
            abort.main()

        reg = self._reg()
        self.assertNotIn("direct-init", reg["initiatives"])
        self.assertTrue((self.cicadas_dir / "drafts" / "direct-init").exists())

        branches = subprocess.check_output(["git", "branch"], cwd=self.root).decode()
        self.assertNotIn("initiative/direct-init", branches)

    def test_abort_skill_treated_as_lightweight(self):
        """skill/ branches are recognised as lightweight and abort cleans up paired initiative."""
        skill_name = "pdf-skill"
        initiative_name = "pdf-skill"
        reg = self._reg()
        reg["initiatives"][initiative_name] = {"intent": "pdf skill"}
        reg["branches"][f"skill/{skill_name}"] = {
            "intent": "pdf skill branch",
            "modules": [],
            "initiative": initiative_name,
        }
        self._write_reg(reg)
        self._create_active_specs(initiative_name)
        self._create_paired_branches(f"skill/{skill_name}", f"initiative/{initiative_name}")

        from utils import load_json
        registry = load_json(self.cicadas_dir / "registry.json")
        with patch("abort.prompt_choice", return_value="D"):
            abort.abort_lightweight(
                f"skill/{skill_name}", initiative_name, self.root, self.cicadas_dir, registry
            )

        reg = self._reg()
        self.assertNotIn(f"skill/{skill_name}", reg["branches"])
        self.assertNotIn(initiative_name, reg["initiatives"])
        self.assertTrue((self.cicadas_dir / "drafts" / initiative_name).exists())

    def test_main_dispatches_skill_branch(self):
        """main() dispatches skill/ to abort_lightweight path."""
        skill_name = "tool-skill"
        reg = self._reg()
        reg["initiatives"][skill_name] = {"intent": "tool skill"}
        reg["branches"][f"skill/{skill_name}"] = {
            "intent": "build tool skill",
            "modules": [],
            "initiative": skill_name,
        }
        self._write_reg(reg)
        self._create_paired_branches(f"skill/{skill_name}", f"initiative/{skill_name}")

        with patch("abort.prompt_choice", return_value="D"):
            abort.main()

        reg = self._reg()
        self.assertNotIn(f"skill/{skill_name}", reg["branches"])
        self.assertNotIn(skill_name, reg["initiatives"])


if __name__ == "__main__":
    unittest.main()
