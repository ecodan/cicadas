# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from pathlib import Path

import history
from base import CicadasTest


def _make_archive_folder(parent: Path, name: str, timestamp: str = "20260101120000") -> Path:
    folder = parent / f"{timestamp}-{name}"
    folder.mkdir(parents=True)
    return folder


class TestClassify(unittest.TestCase):
    def test_fix_slash(self):
        self.assertEqual(history.classify("fix/my-bug"), "fix")

    def test_fix_dash(self):
        self.assertEqual(history.classify("fix-some-bug"), "fix")

    def test_tweak_slash(self):
        self.assertEqual(history.classify("tweak/ui-polish"), "tweak")

    def test_tweak_dash(self):
        self.assertEqual(history.classify("tweak-small"), "tweak")

    def test_initiative(self):
        self.assertEqual(history.classify("my-initiative"), "initiative")

    def test_feat_prefix_is_initiative(self):
        self.assertEqual(history.classify("feat/some-work"), "initiative")


class TestExtractSummary(unittest.TestCase):
    def setUp(self):
        import tempfile, os
        self.test_dir = tempfile.mkdtemp()
        self.folder = Path(self.test_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_tweaklet_intent_section(self):
        (self.folder / "tweaklet.md").write_text(
            "# Tweaklet\n\n## Intent\n\nImprove button color.\n\n## Tasks\n- [ ] do it\n"
        )
        self.assertEqual(history.extract_summary(self.folder), "Improve button color.")

    def test_buglet_intent_section(self):
        (self.folder / "buglet.md").write_text(
            "# Buglet\n\n## Intent\n\nFix null pointer.\n\n## Tasks\n- [ ] fix\n"
        )
        self.assertEqual(history.extract_summary(self.folder), "Fix null pointer.")

    def test_prd_executive_summary(self):
        (self.folder / "prd.md").write_text(
            "# PRD\n\n## Executive Summary\n\nThis product does X.\n\n## Goals\n- goal\n"
        )
        self.assertEqual(history.extract_summary(self.folder), "This product does X.")

    def test_tweaklet_takes_priority_over_prd(self):
        (self.folder / "tweaklet.md").write_text("# T\n\n## Intent\n\nTweak wins.\n")
        (self.folder / "prd.md").write_text("# P\n\n## Executive Summary\n\nPRD loses.\n")
        self.assertEqual(history.extract_summary(self.folder), "Tweak wins.")

    def test_no_matching_file_returns_empty(self):
        self.assertEqual(history.extract_summary(self.folder), "")

    def test_file_with_no_matching_section_returns_empty(self):
        (self.folder / "prd.md").write_text("# PRD\n\nNo summary section here.\n")
        self.assertEqual(history.extract_summary(self.folder), "")


class TestCountTasks(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.test_dir = tempfile.mkdtemp()
        self.folder = Path(self.test_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_mixed_checked_and_unchecked(self):
        (self.folder / "tasks.md").write_text(
            "- [x] done one\n- [ ] pending\n- [X] done two\n"
        )
        total, done = history.count_tasks(self.folder)
        self.assertEqual(total, 3)
        self.assertEqual(done, 2)

    def test_all_complete(self):
        (self.folder / "tasks.md").write_text("- [x] a\n- [x] b\n")
        total, done = history.count_tasks(self.folder)
        self.assertEqual(total, 2)
        self.assertEqual(done, 2)

    def test_none_complete(self):
        (self.folder / "tasks.md").write_text("- [ ] a\n- [ ] b\n- [ ] c\n")
        total, done = history.count_tasks(self.folder)
        self.assertEqual(total, 3)
        self.assertEqual(done, 0)

    def test_no_tasks_file_returns_zeros(self):
        total, done = history.count_tasks(self.folder)
        self.assertEqual(total, 0)
        self.assertEqual(done, 0)

    def test_tweaklet_tasks_used_when_no_tasks_md(self):
        (self.folder / "tweaklet.md").write_text("- [x] done\n- [ ] pending\n")
        total, done = history.count_tasks(self.folder)
        self.assertEqual(total, 2)
        self.assertEqual(done, 1)


class TestRenderHtml(unittest.TestCase):
    def test_empty_entries_shows_fallback_message(self):
        html = history.render_html([])
        self.assertIn("No archived entries found", html)
        self.assertIn("<!DOCTYPE html>", html)

    def test_entry_renders_name_and_date(self):
        entries = [{"name": "my-init", "kind": "initiative", "date": "Jan 01, 2026",
                    "summary": "Test summary", "ledger_summary": "", "total_tasks": 2,
                    "done_tasks": 1}]
        html = history.render_html(entries)
        self.assertIn("my-init", html)
        self.assertIn("Jan 01, 2026", html)
        self.assertIn("1/2 tasks completed", html)
        self.assertIn("Test summary", html)

    def test_fix_kind_renders_bug_fix_badge(self):
        entries = [{"name": "fix-foo", "kind": "fix", "date": "Jan 01, 2026",
                    "summary": "", "ledger_summary": "", "total_tasks": 0,
                    "done_tasks": 0}]
        html = history.render_html(entries)
        self.assertIn("Bug Fix", html)

    def test_ledger_summary_rendered(self):
        entries = [{"name": "init", "kind": "initiative", "date": "Jan 01, 2026",
                    "summary": "", "ledger_summary": "ledger note", "total_tasks": 0,
                    "done_tasks": 0}]
        html = history.render_html(entries)
        self.assertIn("ledger note", html)


class TestGenerate(CicadasTest):
    def test_generate_empty_archive(self):
        out = history.generate(output_path=self.root / "out.html")
        self.assertTrue(out.exists())
        content = out.read_text()
        self.assertIn("No archived entries found", content)

    def test_generate_with_archive_entry(self):
        folder = _make_archive_folder(self.cicadas_dir / "archive", "my-init")
        (folder / "prd.md").write_text("# PRD\n\n## Executive Summary\n\nDoes X.\n")
        (folder / "tasks.md").write_text("- [x] task1\n- [ ] task2\n")

        out = history.generate(output_path=self.root / "out.html")
        content = out.read_text()
        self.assertIn("my-init", content)
        self.assertIn("Does X.", content)
        self.assertIn("1/2 tasks completed", content)

    def test_generate_default_output_path(self):
        out = history.generate()
        expected = self.root / ".cicadas" / "canon" / "history.html"
        self.assertEqual(out.resolve(), expected.resolve())
        self.assertTrue(out.exists())

    def test_generate_uses_index_for_ledger_summary(self):
        folder = _make_archive_folder(self.cicadas_dir / "archive", "indexed-init")
        (self.cicadas_dir / "index.json").write_text(json.dumps({
            "entries": [{"branch": "indexed-init", "summary": "Ledger entry text"}]
        }))
        out = history.generate(output_path=self.root / "out.html")
        self.assertIn("Ledger entry text", out.read_text())


if __name__ == "__main__":
    unittest.main()
