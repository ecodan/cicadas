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
        self.assertIn("meaningful_file_count", metadata["scan"])
        self.assertIn("estimated_loc", metadata["scan"])

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
        zones = metadata["scan"]["major_code_zones"]

        self.assertNotIn(".agents", zones)
        self.assertNotIn(".claude", zones)
        self.assertNotIn(".idea", zones)
        self.assertNotIn(".venv", zones)
        self.assertNotIn(".cicadas/archive", zones)
        self.assertIn("src", metadata["scan"]["major_code_zones"])
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

        self.assertIn("src", metadata["scan"]["major_code_zones"])
        self.assertEqual(metadata["scan"]["major_code_zones"], ["src", "src/pkg"])

    def test_scan_detects_supported_build_systems_and_declared_modules(self):
        (self.root / "pom.xml").write_text("<project><modules><module>services/api</module></modules></project>")
        (self.root / "package.json").write_text(json.dumps({"workspaces": ["packages/*"]}))
        (self.root / "pyproject.toml").write_text("[project]\nname='demo-py'\n[tool.uv]\n")
        (self.root / "Cargo.toml").write_text("[workspace]\nmembers = ['crates/core']\n")
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.root / "src" / "pkg" / "mod.py").write_text("print('demo')\n")

        _tree_path, metadata_path, context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())

        self.assertIn("maven", metadata["scan"]["build_systems"])
        self.assertIn("node", metadata["scan"]["build_systems"])
        self.assertIn("python", metadata["scan"]["build_systems"])
        self.assertIn("cargo", metadata["scan"]["build_systems"])
        self.assertIn("services/api", metadata["scan"]["declared_modules"])
        self.assertIn("packages/*", metadata["scan"]["declared_modules"])
        self.assertIn("demo-py", metadata["scan"]["declared_modules"])
        self.assertIn("crates/core", metadata["scan"]["declared_modules"])
        self.assertIn("Build systems:", context_path.read_text())

    def test_scan_uses_scale_floor_to_force_mega_repo(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        for idx in range(1005):
            (src_dir / f"file_{idx}.py").write_text("print('x')\n" * 2500)

        _tree_path, metadata_path, _context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())

        self.assertEqual(metadata["classification"]["scale_class"], "mega-repo")
        self.assertEqual(metadata["repo_mode"], "mega-repo")
        self.assertEqual(metadata["canon_plan"]["strategy"], "locality-first")
        self.assertEqual(metadata["slice_strategy"]["unit"], "slice")
        self.assertTrue(metadata["candidate_slices"])

    def test_scan_seeds_slices_for_large_repo_modes(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        for idx in range(1005):
            (src_dir / f"file_{idx}.py").write_text("print('x')\n")

        _tree_path, metadata_path, context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())

        self.assertEqual(metadata["repo_mode"], "large-repo")
        self.assertEqual(metadata["canon_plan"]["strategy"], "locality-first")
        self.assertEqual(metadata["canon_plan"]["slice_dirs"], ["slices/"])
        self.assertEqual(
            metadata["canon_plan"]["minimum_slice_files"],
            ["summary.md", "boundaries.md", "architecture.md", "invariants.md", "change-guide.md"],
        )
        self.assertIn("Seeded slices:", context_path.read_text())

    def test_normal_repo_does_not_seed_slices(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "mod.py").write_text("print('hello')\n")

        _tree_path, metadata_path, context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())

        self.assertEqual(metadata["repo_mode"], "normal-repo")
        self.assertEqual(metadata["candidate_slices"], [])
        self.assertEqual(metadata["slice_strategy"]["unit"], "module")
        self.assertNotIn("Seeded slices:", context_path.read_text())

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
