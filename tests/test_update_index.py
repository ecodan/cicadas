# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import runpy
import sys
import unittest
from unittest.mock import patch

import update_index
from base import CicadasTest


class TestUpdateIndex(CicadasTest):
    def test_update_index_basic(self):
        branch = "feat/test"
        summary = "logged work"
        modules = "mod1, mod2"

        update_index.update_index(branch, summary, modules=modules)

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)

        self.assertEqual(len(index["entries"]), 1)
        self.assertEqual(index["entries"][0]["branch"], branch)
        self.assertEqual(index["entries"][0]["summary"], summary)
        self.assertEqual(index["entries"][0]["modules"], ["mod1", "mod2"])

    def test_update_index_appends_multiple_entries(self):
        update_index.update_index("feat/first", "first summary")
        update_index.update_index("feat/second", "second summary")

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)

        self.assertEqual(len(index["entries"]), 2)
        self.assertEqual(index["entries"][0]["branch"], "feat/first")
        self.assertEqual(index["entries"][1]["branch"], "feat/second")

    def test_update_index_stores_decisions_field(self):
        update_index.update_index("feat/test", "summary", decisions="key decision here")

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)

        self.assertEqual(index["entries"][0]["decisions"], "key decision here")

    def test_update_index_modules_whitespace_normalized(self):
        update_index.update_index("feat/test", "summary", modules="  mod1  ,  mod2  ")

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)

        self.assertEqual(index["entries"][0]["modules"], ["mod1", "mod2"])

    def test_update_index_modules_empty_string_produces_empty_list(self):
        update_index.update_index("feat/test", "summary", modules="")

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)

        self.assertEqual(index["entries"][0]["modules"], [])

    def test_update_index_cli(self):
        # Use runpy to cover the if __name__ == "__main__" block
        # We need to mock sys.argv
        test_args = ["update_index.py", "--branch", "feat/cli", "--summary", "cli message", "--modules", "cli_mod"]
        with patch.object(sys, "argv", test_args):
            runpy.run_module("update_index", run_name="__main__")

        with open(self.cicadas_dir / "index.json") as f:
            index = json.load(f)
        # Check if any entry matches the CLI call
        found = any(e["branch"] == "feat/cli" for e in index["entries"])
        self.assertTrue(found)

    def test_update_index_hint_present_when_run_as_main(self):
        """When run as __main__ with TTY, update_index prints hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        buf = io.StringIO()
        test_args = ["update_index.py", "--branch", "feat/test", "--summary", "test summary"]
        
        with patch("sys.argv", test_args):
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("update_index", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertIn("Next: create a PR when all partitions are done", output)

    def test_update_index_hint_suppressed_with_no_hints_flag(self):
        """When run as __main__ with --no-hints, update_index suppresses hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        buf = io.StringIO()
        test_args = ["update_index.py", "--branch", "feat/test", "--summary", "test summary", "--no-hints"]
        
        with patch("sys.argv", test_args):
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("update_index", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertNotIn("Next: create a PR when all partitions are done", output)


if __name__ == "__main__":
    unittest.main()
