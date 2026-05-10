# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import io
import os
import subprocess
import unittest
from contextlib import redirect_stdout

import open_pr
from base import CicadasTest


class TestOpenPr(CicadasTest):
    def test_open_pr_not_git_prints_message(self):
        """Without git repo, open_pr prints message and returns 1."""
        f = io.StringIO()
        with redirect_stdout(f):
            code = open_pr.open_pr(base_branch="main")
        self.assertEqual(code, 1)
        self.assertIn("Not a git repository", f.getvalue())

    def test_open_pr_fallback_no_cli(self):
        """In a git repo with no gh/glab on PATH and no Bitbucket remote, prints fallback."""
        self.init_git()
        subprocess.run(["git", "checkout", "-b", "feat/my-feat"], cwd=self.root, check=True, capture_output=True)

        # Restrict PATH to system dirs so neither gh nor glab is found — tests real shutil.which
        # detection logic without patching the function itself.
        old_path = os.environ.get("PATH", "")
        try:
            os.environ["PATH"] = "/usr/bin:/bin"
            f = io.StringIO()
            with redirect_stdout(f):
                code = open_pr.open_pr(base_branch="master")
        finally:
            os.environ["PATH"] = old_path

        self.assertEqual(code, 0)
        self.assertIn("No PR CLI found", f.getvalue())

    def test_bitbucket_pr_url_parsing(self):
        """_bitbucket_pr_url builds URL from HTTPS and SSH remote formats."""
        url = open_pr._bitbucket_pr_url("https://bitbucket.org/ws/proj", "feat/foo", "main")
        self.assertEqual(url, "https://bitbucket.org/ws/proj/pull-requests/new?source=feat/foo&dest=main")
        url = open_pr._bitbucket_pr_url("git@bitbucket.org:ws/proj.git", "feat/bar", "master")
        self.assertEqual(url, "https://bitbucket.org/ws/proj/pull-requests/new?source=feat/bar&dest=master")

    def test_bitbucket_pr_url_non_bitbucket_returns_none(self):
        """_bitbucket_pr_url returns None for non-Bitbucket remotes."""
        self.assertIsNone(open_pr._bitbucket_pr_url("https://github.com/u/r", "feat/x", "main"))
        self.assertIsNone(open_pr._bitbucket_pr_url("", "feat/x", "main"))

    def test_open_pr_hint_present_when_run_as_main(self):
        """When run as __main__ with TTY, open_pr prints hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        self.init_git()
        subprocess.run(["git", "checkout", "-b", "feat/test"], cwd=self.root, check=True, capture_output=True)
        
        buf = io.StringIO()
        test_args = ["open_pr.py", "--base", "master"]
        
        with patch("sys.argv", test_args):
            with patch("utils.hints_enabled", return_value=True):
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("open_pr", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertIn("Next: merge the PR, then complete the initiative", output)

    def test_open_pr_hint_suppressed_with_no_hints_flag(self):
        """When run as __main__ with --no-hints, open_pr suppresses hint."""
        import io
        import runpy
        from unittest.mock import patch
        
        self.init_git()
        subprocess.run(["git", "checkout", "-b", "feat/test"], cwd=self.root, check=True, capture_output=True)
        
        buf = io.StringIO()
        test_args = ["open_pr.py", "--base", "master", "--no-hints"]
        
        with patch("sys.argv", test_args):
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                    try:
                        runpy.run_module("open_pr", run_name="__main__", alter_sys=True)
                    except SystemExit:
                        pass
        
        output = buf.getvalue()
        self.assertNotIn("Next: merge the PR, then complete the initiative", output)


if __name__ == "__main__":
    unittest.main()
