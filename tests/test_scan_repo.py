# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import scan_repo
from base import CicadasTest
from utils import REPO_CONTEXT_FILENAME, REPO_METADATA_FILENAME, REPO_TREE_FILENAME


class TestScanRepo(CicadasTest):
    def setUp(self):
        super().setUp()
        self.init_git()

    def test_run_scan_writes_expected_artifacts(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "mod.py").write_text("print('hello')\n")
        (self.root / "tests" / "test_mod.py").parent.mkdir(parents=True)
        (self.root / "tests" / "test_mod.py").write_text("def test_ok():\n    assert True\n")
        (self.root / "pyproject.toml").write_text("[project]\nname='demo'\n")

        tree_path, metadata_path, context_path = scan_repo.run_scan()

        self.assertEqual(tree_path.name, REPO_TREE_FILENAME)
        self.assertEqual(metadata_path.name, REPO_METADATA_FILENAME)
        self.assertEqual(context_path.name, REPO_CONTEXT_FILENAME)
        self.assertTrue(tree_path.exists())
        self.assertTrue(metadata_path.exists())
        self.assertTrue(context_path.exists())

        metadata = json.loads(metadata_path.read_text())
        self.assertIn(metadata["repo_mode"], {"normal-repo", "large-repo", "mega-repo"})
        self.assertIn("heuristic_scores", metadata["classification"])
        self.assertEqual(metadata["scan"]["tree_path"], REPO_TREE_FILENAME)
        self.assertEqual(metadata["scan"]["context_path"], REPO_CONTEXT_FILENAME)

        lines = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        self.assertTrue(any(line["kind"] == "directory" for line in lines))
        self.assertTrue(any(line["kind"] == "file" for line in lines))
        self.assertTrue(any(line["path"] == "src/pkg/mod.py" for line in lines))
        self.assertIn("# Repo Context", context_path.read_text())

    def test_scan_excludes_agentic_and_archive_paths_from_complexity_scoring(self):
        (self.root / ".agents" / "skills").mkdir(parents=True)
        (self.root / ".agents" / "skills" / "skill.md").write_text("skill")
        (self.root / ".claude" / "skills").mkdir(parents=True)
        (self.root / ".claude" / "skills" / "skill.md").write_text("skill")
        (self.root / ".idea" / "inspectionProfiles").mkdir(parents=True)
        (self.root / ".idea" / "inspectionProfiles" / "profile.xml").write_text("<xml/>")
        (self.root / ".venv" / "bin").mkdir(parents=True)
        (self.root / ".venv" / "bin" / "python").write_text("python")
        (self.cicadas_dir / "archive" / "old").mkdir(parents=True)
        (self.cicadas_dir / "archive" / "old" / "spec.md").write_text("archived")
        src_dir = self.root / "src" / "smallpkg"
        src_dir.mkdir(parents=True)
        (src_dir / "mod.py").write_text("print('small')\n")

        _tree_path, metadata_path, context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())
        ownership = metadata["scan"]["ownership_zone_candidates"]

        self.assertNotIn(".agents", ownership)
        self.assertNotIn(".claude", ownership)
        self.assertNotIn(".idea", ownership)
        self.assertNotIn(".venv", ownership)
        self.assertNotIn(".cicadas/archive", ownership)
        self.assertIn("src", metadata["scan"]["runtime_paths"])
        self.assertNotIn(".agents", context_path.read_text())
        self.assertNotIn(".idea", context_path.read_text())

    def test_scan_marks_gitignored_and_generated_paths_without_counting_them(self):
        (self.root / ".gitignore").write_text("tmp/\n")
        (self.root / "tmp").mkdir()
        (self.root / "tmp" / "generated.py").write_text("print('tmp')\n")
        (self.root / "build").mkdir()
        (self.root / "build" / "bundle.js").write_text("console.log('bundle')\n")
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.root / "src" / "pkg" / "mod.py").write_text("print('real')\n")

        tree_path, metadata_path, _context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())
        entries = {
            entry["path"]: entry
            for entry in [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        }

        self.assertIn("tmp", entries)
        self.assertIn("tmp/generated.py", entries)
        self.assertFalse(entries["tmp"]["counts_toward_scale"])
        self.assertEqual(entries["tmp"]["scale_exclusion_reason"], "gitignored")
        self.assertFalse(entries["tmp/generated.py"]["counts_toward_scale"])
        self.assertEqual(entries["tmp/generated.py"]["scale_exclusion_reason"], "gitignored")

        self.assertIn("build", entries)
        self.assertFalse(entries["build"]["counts_toward_scale"])
        self.assertEqual(entries["build"]["scale_exclusion_reason"], "generated-or-local")

        self.assertIn("src", metadata["scan"]["runtime_paths"])
        self.assertEqual(metadata["scan"]["ownership_zone_candidates"], ["src", "src/pkg"])

    def test_scan_spools_tree_to_disk_during_inventory_build(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        for idx in range(5):
            (src_dir / f"mod_{idx}.py").write_text(f"print({idx})\n")

        tree_path = self.root / ".cicadas" / "canon" / REPO_TREE_FILENAME
        summary = scan_repo.scan_repository(self.root, tree_path=tree_path)

        self.assertTrue(tree_path.exists())
        lines = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        self.assertTrue(any(line["path"] == "src/pkg/mod_0.py" for line in lines))
        self.assertTrue(any(line["kind"] == "directory" and line["path"] == "src/pkg" for line in lines))
        self.assertEqual(summary.tree_path, tree_path)

    def test_scan_can_emit_progress_and_eta(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        for idx in range(3):
            (src_dir / f"mod_{idx}.py").write_text(f"print({idx})\n")

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            scan_repo.run_scan(progress_mode="on")

        output = stderr.getvalue()
        self.assertIn("[scan-repo] Discovering repository paths", output)
        self.assertIn("[scan-repo] File scan:", output)
        self.assertIn("ETA", output)
        self.assertIn("[scan-repo] Inventory complete:", output)

    def test_scan_repo_help(self):
        script = Path(scan_repo.__file__).resolve()
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("Scan the repository", completed.stdout)


if __name__ == "__main__":
    unittest.main()
