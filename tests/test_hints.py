# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for the hint subsystem added to utils.py."""

from __future__ import annotations

import argparse
import io
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "src" / "cicadas" / "scripts"))

from utils import (  # noqa: E402
    _HINT_BOX_WIDTH,
    hints_enabled,
    print_hint,
    print_tutorial_banner,
    print_tutorial_checkmark,
)


def _make_args(no_hints: bool = False) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.no_hints = no_hints
    return ns


class TestHintsEnabled(unittest.TestCase):
    """hints_enabled() priority: --no-hints > config > TTY > True."""

    def test_no_hints_flag_returns_false(self):
        """--no-hints arg suppresses hints regardless of config or TTY."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            self.assertFalse(hints_enabled(args=_make_args(no_hints=True), config={}))

    def test_config_hints_false_returns_false(self):
        """config['hints'] == False suppresses hints when no --no-hints flag."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            self.assertFalse(hints_enabled(args=_make_args(no_hints=False), config={"hints": False}))

    def test_non_tty_returns_false(self):
        """Non-TTY stdout suppresses hints even without flag or config."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            self.assertFalse(hints_enabled(args=_make_args(no_hints=False), config={}))

    def test_tty_no_suppression_returns_true(self):
        """Returns True when TTY, no --no-hints, no config suppression."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            self.assertTrue(hints_enabled(args=_make_args(no_hints=False), config={}))

    def test_config_hints_true_returns_true(self):
        """Explicit config['hints'] == True does not suppress."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            self.assertTrue(hints_enabled(args=_make_args(no_hints=False), config={"hints": True}))

    def test_no_args_no_config_non_tty_returns_false(self):
        """Called with no args and no config, non-TTY → False."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            self.assertFalse(hints_enabled())

    def test_no_args_no_config_tty_returns_true(self):
        """Called with no args and no config, TTY → True."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            self.assertTrue(hints_enabled())

    def test_no_hints_flag_beats_tty(self):
        """--no-hints takes priority even over a TTY stdout."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            self.assertFalse(hints_enabled(args=_make_args(no_hints=True)))


class TestPrintHint(unittest.TestCase):
    """print_hint() output format and suppression."""

    def _capture_hint(self, lines, *, no_hints=False, config=None, is_tty=False):
        """Run print_hint() capturing stdout, with configurable TTY simulation."""
        buf = io.StringIO()
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = is_tty
            # Route actual print() calls to our buffer.
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                print_hint(lines, args=_make_args(no_hints=no_hints), config=config or {})
        return buf.getvalue()

    def test_no_output_when_hints_disabled_via_flag(self):
        """print_hint() produces zero output when --no-hints is set."""
        output = self._capture_hint(["Next: do something"], no_hints=True, is_tty=True)
        self.assertEqual(output, "")

    def test_no_output_when_hints_disabled_via_config(self):
        """print_hint() produces zero output when config hints=False."""
        output = self._capture_hint(["Next: do something"], config={"hints": False}, is_tty=True)
        self.assertEqual(output, "")

    def test_no_output_when_not_tty(self):
        """print_hint() produces zero output when stdout is not a TTY."""
        output = self._capture_hint(["Next: do something"], is_tty=False)
        self.assertEqual(output, "")

    def test_box_width_when_hints_enabled(self):
        """Each printed line of the hint box is exactly _HINT_BOX_WIDTH chars wide (ignoring ANSI)."""
        import re
        ansi_escape = re.compile(r"\033\[[0-9;]*m")

        buf = io.StringIO()
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                print_hint(["Next: start your first feature branch"], args=_make_args(no_hints=False), config={})

        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        self.assertGreater(len(lines), 0, "Expected hint output but got none")
        for line in lines:
            clean = ansi_escape.sub("", line)
            self.assertEqual(
                len(clean),
                _HINT_BOX_WIDTH,
                f"Line width {len(clean)} != {_HINT_BOX_WIDTH}: {repr(clean)}",
            )

    def test_multiple_lines_rendered(self):
        """All provided lines appear in the output."""
        buf = io.StringIO()
        test_lines = ["Next: implement partition 1", '  💬 "Implement partition 1"']
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                print_hint(test_lines, args=_make_args(no_hints=False), config={})
        output = buf.getvalue()
        for line in test_lines:
            self.assertIn(line[:20], output)

    def test_long_line_truncated_to_fit(self):
        """Lines longer than inner width are truncated, not wrapped."""
        inner_width = _HINT_BOX_WIDTH - 4
        long_line = "X" * (inner_width + 50)
        buf = io.StringIO()
        import re
        ansi_escape = re.compile(r"\033\[[0-9;]*m")
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                print_hint([long_line], args=_make_args(no_hints=False), config={})
        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        for line in lines:
            clean = ansi_escape.sub("", line)
            self.assertLessEqual(len(clean), _HINT_BOX_WIDTH)


class TestPrintTutorialBanner(unittest.TestCase):
    def test_banner_contains_step_info(self):
        buf = io.StringIO()
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                print_tutorial_banner(3, 7, "Kickoff the initiative")
        output = buf.getvalue()
        self.assertIn("3", output)
        self.assertIn("7", output)
        self.assertIn("Kickoff the initiative", output)


class TestPrintTutorialCheckmark(unittest.TestCase):
    def test_checkmark_contains_message(self):
        buf = io.StringIO()
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
                print_tutorial_checkmark("Draft folder ready")
        self.assertIn("Draft folder ready", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
