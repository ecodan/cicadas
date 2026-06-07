# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import runpy
import stat
import unittest
from unittest.mock import patch

import init
from base import CicadasTest
from utils import load_json, save_json


class TestInit(CicadasTest):
    def test_init_cicadas(self):
        # CicadasTest.setUp already creates some of this, but let's test the script's logic
        # We'll use a fresh sub-directory for this specific test
        new_root = self.root / "new_project"
        new_root.mkdir()

        init.init_cicadas(new_root)

        cicadas_dir = new_root / ".cicadas"
        self.assertTrue(cicadas_dir.exists())
        self.assertTrue((cicadas_dir / "canon").exists())
        self.assertFalse((cicadas_dir / "canon/modules").exists())
        self.assertTrue((cicadas_dir / "active").exists())
        self.assertTrue((cicadas_dir / "drafts").exists())
        self.assertTrue((cicadas_dir / "archive").exists())

        registry = load_json(cicadas_dir / "registry.json")
        self.assertEqual(registry["schema_version"], "2.0")

        index = load_json(cicadas_dir / "index.json")
        self.assertEqual(index["schema_version"], "2.0")

        config = load_json(cicadas_dir / "config.json")
        self.assertEqual(config["project_name"], "new_project")
        self.assertEqual(config["tracing"]["enabled"], False)
        self.assertEqual(config["tracing"]["endpoint"], "http://localhost:4318/v1/traces")
        self.assertEqual(config["tracing"]["service_name"], "cicadas")
        self.assertEqual(config["tracing"]["headers"], {})

    def test_init_cicadas_preserves_existing_json_on_rerun(self):
        new_root = self.root / "existing_project"
        new_root.mkdir()

        init.init_cicadas(new_root)

        cicadas_dir = new_root / ".cicadas"
        registry_data = {
            "schema_version": "2.0",
            "initiatives": {"keep-me": {"branch": "initiative/keep-me"}},
            "branches": {"feat/keep-me": {"initiative": "keep-me"}},
        }
        index_data = {
            "schema_version": "2.0",
            "entries": [{"id": "existing-entry", "type": "manual"}],
        }
        config_data = {
            "project_name": "custom-name",
            "auto_worktrees": {
                "initiatives": True,
                "lightweight": True,
                "parallel_features": False,
            },
            "extra": "preserved",
        }
        save_json(cicadas_dir / "registry.json", registry_data)
        save_json(cicadas_dir / "index.json", index_data)
        save_json(cicadas_dir / "config.json", config_data)

        init.init_cicadas(new_root)

        self.assertEqual(load_json(cicadas_dir / "registry.json"), registry_data)
        self.assertEqual(load_json(cicadas_dir / "index.json"), index_data)
        self.assertEqual(load_json(cicadas_dir / "config.json"), config_data)

    def test_init_cicadas_creates_missing_json_on_rerun(self):
        new_root = self.root / "partial_project"
        new_root.mkdir()

        init.init_cicadas(new_root)
        cicadas_dir = new_root / ".cicadas"
        registry_path = cicadas_dir / "registry.json"
        index_path = cicadas_dir / "index.json"
        config_path = cicadas_dir / "config.json"
        registry_path.unlink()
        index_path.unlink()
        config_path.unlink()

        init.init_cicadas(new_root)

        registry = load_json(registry_path)
        self.assertEqual(registry["schema_version"], "2.0")
        self.assertEqual(registry["initiatives"], {})
        self.assertEqual(registry["branches"], {})

        index = load_json(index_path)
        self.assertEqual(index["schema_version"], "2.0")
        self.assertEqual(index["entries"], [])

        config = load_json(config_path)
        self.assertEqual(config["project_name"], "partial_project")
        self.assertFalse(config["auto_worktrees"]["initiatives"])

    def test_install_hooks_with_git_dir(self):
        """Hook installation loop runs when .git/hooks/ exists."""
        new_root = self.root / "hooked_project"
        new_root.mkdir()
        git_hooks_dir = new_root / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True)

        init.init_cicadas(new_root)

        hook_dst = git_hooks_dir / "pre-commit"
        self.assertTrue(hook_dst.exists())
        # Verify executable bits were set
        mode = hook_dst.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR)

    def test_main_block(self):
        """__main__ entry point calls init_cicadas with the project root."""
        new_root = self.root / "main_project"
        new_root.mkdir()

        # Patch utils.get_project_root so the re-executed import picks it up
        with patch("utils.get_project_root", return_value=new_root):
            with patch("sys.argv", ["init.py"]):
                runpy.run_module("init", run_name="__main__", alter_sys=True)

        self.assertTrue((new_root / ".cicadas").exists())

    def test_init_hint_present_when_run_as_main(self):
        """When run as __main__ with TTY, init prints hint."""
        import io
        from unittest.mock import patch
        
        new_root = self.root / "hint_project"
        new_root.mkdir()
        
        buf = io.StringIO()
        test_args = ["init.py"]
        
        with patch("sys.argv", test_args):
            with patch("utils.hints_enabled", return_value=True):
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    with patch("utils.get_project_root", return_value=new_root):
                        try:
                            runpy.run_module("init", run_name="__main__", alter_sys=True)
                        except SystemExit:
                            pass
        
        output = buf.getvalue()
        self.assertIn("Welcome to Cicadas! Start your first initiative.", output)

    def test_init_hint_suppressed_with_no_hints_flag(self):
        """When run as __main__ with --no-hints, init suppresses hint."""
        import io
        from unittest.mock import patch
        
        new_root = self.root / "no_hint_project"
        new_root.mkdir()
        
        buf = io.StringIO()
        test_args = ["init.py", "--no-hints"]
        
        with patch("sys.argv", test_args):
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    with patch("utils.get_project_root", return_value=new_root):
                        try:
                            runpy.run_module("init", run_name="__main__", alter_sys=True)
                        except SystemExit:
                            pass
        
        output = buf.getvalue()
        self.assertNotIn("Welcome to Cicadas! Start your first initiative.", output)


if __name__ == "__main__":
    unittest.main()
