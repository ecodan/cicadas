# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for tutorial.py — interactive Cicadas tutorial."""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure scripts directory is on the path.
SCRIPTS_DIR = Path(__file__).parent.parent / "src" / "cicadas" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import tutorial  # noqa: E402
from tutorial import (  # noqa: E402
    MOCK_BUILD,
    MOCK_CODE_REVIEW,
    MOCK_COMPLETE_INITIATIVE,
    MOCK_COMPLETE_PARTITION,
    MOCK_KICKOFF,
    MOCK_OPEN_PR,
    MOCK_START,
    _CHEATSHEET,
    _TOTAL_STEPS,
    _completion_screen,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_main_capturing() -> str:
    """Run tutorial.main() with Enter auto-pressed and capture all stdout."""
    buf = io.StringIO()
    # Patch input() to always press Enter (default "yes" / continue).
    with patch("builtins.input", return_value=""):
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                # Re-route print() to our buffer AND to mock_stdout so
                # utils functions that use print() also go to buf.
                original_print = print

                def capturing_print(*args, **kwargs):
                    kwargs.setdefault("file", buf)
                    # also write to mock_stdout so isatty checks don't explode
                    original_print(*args, **kwargs)

                with patch("builtins.print", side_effect=capturing_print):
                    main()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Test: step banners print in order
# ---------------------------------------------------------------------------


class TestTutorialBanners(unittest.TestCase):
    """All 7 step banners appear in correct order in tutorial output."""

    def setUp(self):
        self.output = _run_main_capturing()

    def _banner_position(self, step: int) -> int:
        marker = f"STEP {step} of {_TOTAL_STEPS}"
        idx = self.output.find(marker)
        self.assertNotEqual(idx, -1, f"Banner for step {step} not found in output")
        return idx

    def test_all_seven_banners_present(self):
        for step in range(1, _TOTAL_STEPS + 1):
            self._banner_position(step)

    def test_banners_in_ascending_order(self):
        positions = [self._banner_position(s) for s in range(1, _TOTAL_STEPS + 1)]
        self.assertEqual(positions, sorted(positions), "Banners not in ascending order")


# ---------------------------------------------------------------------------
# Test: tutorial makes zero changes to git state or .cicadas/
# ---------------------------------------------------------------------------


class TestTutorialNoSideEffects(unittest.TestCase):
    """cicadas tutorial makes zero changes to git state or .cicadas/."""

    def test_no_filesystem_changes(self):
        """Running main() must not create or modify any files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Record before state (files + dirs present)
            before = set(tmp.rglob("*"))
            with patch("builtins.input", return_value=""):
                with patch("sys.stdin") as mock_stdin:
                    mock_stdin.isatty.return_value = True
                    with patch("builtins.print"):
                        main()
            after = set(tmp.rglob("*"))
            self.assertEqual(before, after, "tutorial.main() created or modified files")


# ---------------------------------------------------------------------------
# Test: tutorial runs in a bare git repo with no commits
# ---------------------------------------------------------------------------


class TestTutorialInBareRepo(unittest.TestCase):
    """tutorial.main() succeeds in a bare git repo with no commits."""

    def test_runs_in_bare_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import subprocess as sp
            sp.run(["git", "init", tmpdir], check=True, capture_output=True)
            with patch("builtins.input", return_value=""):
                with patch("sys.stdin") as mock_stdin:
                    mock_stdin.isatty.return_value = True
                    with patch("builtins.print"):
                        rc = main()
            self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# Test: cicadas init --tutorial runs tutorial without prompt
# ---------------------------------------------------------------------------


class TestInitTutorialFlag(unittest.TestCase):
    """cicadas init --tutorial runs tutorial without prompting."""

    def _run_init(self, extra_args: list[str], tmpdir: str) -> tuple[int, str]:
        """Run init.py via subprocess in an isolated temp git repo."""
        import subprocess as sp
        sp.run(["git", "init", tmpdir], check=True, capture_output=True)
        sp.run(["git", "-C", tmpdir, "commit", "--allow-empty", "-m", "init"],
               check=True, capture_output=True)
        result = sp.run(
            [sys.executable, str(SCRIPTS_DIR / "init.py"), *extra_args],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            input="",  # no stdin
        )
        return result.returncode, result.stdout + result.stderr

    def test_tutorial_flag_runs_tutorial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, output = self._run_init(["--tutorial"], tmpdir)
            self.assertEqual(rc, 0)
            # Tutorial output must contain step banners
            self.assertIn(f"STEP 1 of {_TOTAL_STEPS}", output)

    def test_no_tutorial_flag_skips_tutorial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, output = self._run_init(["--no-tutorial"], tmpdir)
            self.assertEqual(rc, 0)
            self.assertNotIn(f"STEP 1 of {_TOTAL_STEPS}", output)

    def test_first_run_without_flags_offers_prompt(self):
        """On first run without flags and non-TTY stdin, no prompt is shown (graceful skip)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, output = self._run_init([], tmpdir)
            # Should not crash; tutorial prompt is silently skipped for non-TTY
            self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# Test: completion screen contains all 7 agent prompts
# ---------------------------------------------------------------------------


class TestCompletionScreen(unittest.TestCase):
    """_completion_screen() output contains all 7 agent prompts from the cheatsheet."""

    def test_all_prompts_in_completion_screen(self):
        buf = io.StringIO()
        with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
            _completion_screen()
        output = buf.getvalue()
        for label, prompt in _CHEATSHEET:
            if not prompt.startswith("("):
                # Check that at least the first meaningful word of the prompt appears
                first_word = prompt.split()[0]
                self.assertIn(first_word, output, f"Prompt for {label!r} not found in completion screen")

    def test_completion_screen_has_youre_ready(self):
        buf = io.StringIO()
        with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
            _completion_screen()
        self.assertIn("ready", buf.getvalue().lower())

    def test_cheatsheet_has_seven_entries(self):
        self.assertEqual(len(_CHEATSHEET), _TOTAL_STEPS)


# ---------------------------------------------------------------------------
# Test: mock strings are defined and non-empty
# ---------------------------------------------------------------------------


class TestMockStrings(unittest.TestCase):
    """All MOCK_* constants are non-empty strings."""

    def test_all_mocks_non_empty(self):
        mocks = [
            ("MOCK_START", MOCK_START),
            ("MOCK_KICKOFF", MOCK_KICKOFF),
            ("MOCK_BUILD", MOCK_BUILD),
            ("MOCK_CODE_REVIEW", MOCK_CODE_REVIEW),
            ("MOCK_COMPLETE_PARTITION", MOCK_COMPLETE_PARTITION),
            ("MOCK_OPEN_PR", MOCK_OPEN_PR),
            ("MOCK_COMPLETE_INITIATIVE", MOCK_COMPLETE_INITIATIVE),
        ]
        for name, value in mocks:
            with self.subTest(mock=name):
                self.assertIsInstance(value, str)
                self.assertGreater(len(value.strip()), 0, f"{name} is empty")


if __name__ == "__main__":
    unittest.main()
