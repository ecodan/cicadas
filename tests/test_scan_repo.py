# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

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
        self.assertEqual(metadata["scan"]["code_file_count"], 1)
        self.assertEqual(metadata["scan"]["test_file_count"], 1)
        self.assertEqual(metadata["scan"]["source_file_count"], 2)
        self.assertGreaterEqual(metadata["scan"]["estimated_code_loc"], 3)

        lines = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        self.assertTrue(any(line["kind"] == "directory" for line in lines))
        self.assertTrue(any(line["kind"] == "file" for line in lines))
        self.assertTrue(any(line["path"] == "src/pkg/mod.py" for line in lines))
        self.assertTrue(any(line["path"] == "src/pkg/mod.py" and line["source_class"] == "code" for line in lines))
        self.assertTrue(any(line["path"] == "tests/test_mod.py" and line["source_class"] == "test" for line in lines))
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

    def test_scan_skips_cicadas_skill_workspace(self):
        (self.root / ".cicadas-skill" / "cicadas" / "scripts").mkdir(parents=True)
        (self.root / ".cicadas-skill" / "cicadas" / "scripts" / "helper.py").write_text("print('tooling')\n")
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.root / "src" / "pkg" / "mod.py").write_text("print('real')\n")

        tree_path, metadata_path, context_path = scan_repo.run_scan()
        entries = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        paths = {entry["path"] for entry in entries}
        metadata = json.loads(metadata_path.read_text())

        self.assertIn("src/pkg/mod.py", paths)
        self.assertNotIn(".cicadas-skill", paths)
        self.assertFalse(any(path.startswith(".cicadas-skill/") for path in paths))
        self.assertNotIn(".cicadas-skill", metadata["scan"]["ownership_zone_candidates"])
        self.assertNotIn(".cicadas-skill", context_path.read_text())

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

    def test_scan_seeds_slices_from_declared_modules_when_major_code_zones_are_empty(self):
        for module_name in ["jira-components", "jira-domains", "jira-devops"]:
            module_src = self.root / module_name / "src" / "main" / "java" / "com" / "acme"
            module_src.mkdir(parents=True)
            for idx in range(400):
                (module_src / f"{module_name.replace('-', '_')}_{idx}.java").write_text("class Demo {}\n")
        (self.root / "pom.xml").write_text(
            "<project><modules>"
            "<module>jira-components</module>"
            "<module>jira-domains</module>"
            "<module>jira-devops</module>"
            "</modules></project>"
        )
        (self.root / "package.json").write_text(json.dumps({"name": "jira"}))

        _tree_path, metadata_path, context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())

        self.assertEqual(metadata["repo_mode"], "large-repo")
        self.assertEqual(metadata["scan"]["major_code_zones"], [])
        self.assertEqual(
            set(metadata["scan"]["ownership_zone_candidates"][:3]),
            {"jira-components", "jira-domains", "jira-devops"},
        )
        candidate_names = [slice_info["name"] for slice_info in metadata["candidate_slices"]]
        self.assertIn("jira-components", candidate_names)
        self.assertIn("jira-domains", candidate_names)
        self.assertIn("jira-devops", candidate_names)
        context = context_path.read_text()
        self.assertIn("Seeded slices:", context)
        self.assertIn("jira-components", context)

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

    def test_markdown_heavy_repo_stays_normal_when_code_volume_is_small(self):
        requirements_dir = self.root / "requirements"
        requirements_dir.mkdir()
        for idx in range(5000):
            (requirements_dir / f"story_{idx}.md").write_text(f"# Story {idx}\n\nAcceptance criteria.\n")
        src_dir = self.root / "src" / "app"
        src_dir.mkdir(parents=True)
        for idx in range(10):
            (src_dir / f"mod_{idx}.py").write_text("print('small')\n")

        tree_path, metadata_path, context_path = scan_repo.run_scan()
        metadata = json.loads(metadata_path.read_text())
        entries = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        doc_entries = [entry for entry in entries if entry.get("source_class") == "documentation"]

        self.assertEqual(metadata["classification"]["scale_class"], "normal-repo")
        self.assertEqual(metadata["repo_mode"], "normal-repo")
        self.assertEqual(metadata["scan"]["code_file_count"], 10)
        self.assertEqual(metadata["scan"]["test_file_count"], 0)
        self.assertEqual(metadata["scan"]["source_file_count"], 10)
        self.assertGreaterEqual(metadata["scan"]["documentation_file_count"], 5000)
        self.assertGreaterEqual(metadata["scan"]["estimated_documentation_loc"], 10000)
        self.assertGreaterEqual(len(doc_entries), 5000)
        self.assertIn("Source volume:", context_path.read_text())
        self.assertIn("Documentation/context volume:", context_path.read_text())

    def test_scan_spools_tree_to_disk_during_inventory_build(self):
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        for idx in range(3):
            (src_dir / f"mod_{idx}.py").write_text(f"print({idx})\n")

        tree_path = self.root / ".cicadas" / "canon" / REPO_TREE_FILENAME
        observed_previous_entries = False

        class FakeExecutor:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def map(self, fn, items):
                for item in items:
                    yield fn(item)

        original_summarize = scan_repo._summarize_file

        def summarize_with_probe(path: Path, root: Path, gitignored_paths: set[str]) -> dict:
            nonlocal observed_previous_entries
            if path.name == "mod_1.py" and tree_path.exists():
                existing_lines = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
                observed_previous_entries = any(line["path"] == "src/pkg/mod_0.py" for line in existing_lines)
            return original_summarize(path, root, gitignored_paths)

        with mock.patch.object(scan_repo, "ThreadPoolExecutor", FakeExecutor):
            with mock.patch.object(scan_repo, "_summarize_file", side_effect=summarize_with_probe):
                summary = scan_repo.scan_repository(self.root, tree_path=tree_path)

        self.assertTrue(tree_path.exists())
        self.assertTrue(observed_previous_entries)
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


    def test_scan_skips_sdd_install_dirs_with_skill_md(self):
        # An SDD install at a non-standard path (e.g. tools/cicadas/) should be fully excluded.
        sdd_dir = self.root / "tools" / "cicadas"
        sdd_dir.mkdir(parents=True)
        (sdd_dir / "SKILL.md").write_text("# Skill")
        (sdd_dir / "emergence").mkdir()
        (sdd_dir / "emergence" / "clarify.md").write_text("# Clarify")
        (sdd_dir / "templates").mkdir()
        (sdd_dir / "templates" / "prd.md").write_text("# PRD")
        src_dir = self.root / "src" / "pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "mod.py").write_text("print('real')\n")

        tree_path, metadata_path, _context_path = scan_repo.run_scan()
        entries = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        paths = {entry["path"] for entry in entries}
        metadata = json.loads(metadata_path.read_text())

        self.assertIn("src/pkg/mod.py", paths)
        # SDD install dir and its contents must not appear in the tree
        self.assertFalse(any(p.startswith("tools/cicadas") for p in paths))
        # Must not appear as a slice candidate or code zone
        all_candidates = [s["paths"][0] for s in metadata.get("candidate_slices", [])]
        self.assertFalse(any("cicadas" in c for c in all_candidates))

    def test_scan_skips_sdd_state_dirs_by_substring(self):
        # Root-level dirs starting with _ or . whose names contain known SDD substrings
        # (bmad, gsd, openspec) should be excluded from traversal.
        bmad_dir = self.root / "_bmad-output"
        bmad_dir.mkdir()
        for i in range(5):
            (bmad_dir / f"story-{i}.md").write_text(f"# Story {i}")
        gsd_dir = self.root / ".gsd-work"
        gsd_dir.mkdir()
        (gsd_dir / "epic.md").write_text("# Epic")
        src_dir = self.root / "src" / "app"
        src_dir.mkdir(parents=True)
        (src_dir / "main.py").write_text("print('app')\n")

        tree_path, metadata_path, _context_path = scan_repo.run_scan()
        entries = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        paths = {entry["path"] for entry in entries}
        metadata = json.loads(metadata_path.read_text())

        self.assertIn("src/app/main.py", paths)
        self.assertFalse(any(p.startswith("_bmad-output") for p in paths))
        self.assertFalse(any(p.startswith(".gsd-work") for p in paths))
        self.assertNotIn("_bmad-output", metadata["scan"]["major_code_zones"])
        self.assertNotIn(".gsd-work", metadata["scan"]["major_code_zones"])

    def test_scan_does_not_skip_deep_source_dirs_matching_sdd_substrings(self):
        # A source package named e.g. src/gsd-parser/ must NOT be excluded — the
        # substring heuristic only applies at the project root level.
        gsd_pkg = self.root / "src" / "gsd-parser"
        gsd_pkg.mkdir(parents=True)
        (gsd_pkg / "parser.py").write_text("def parse(): pass\n")

        tree_path, _metadata_path, _context_path = scan_repo.run_scan()
        entries = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        paths = {entry["path"] for entry in entries}

        self.assertIn("src/gsd-parser/parser.py", paths)

    def test_scan_respects_scan_exclude_paths_from_config(self):
        # Paths listed in config.json scan_exclude_paths are skipped entirely.
        vendor_sdd = self.root / "vendor" / "my-sdd-tool"
        vendor_sdd.mkdir(parents=True)
        (vendor_sdd / "spec.md").write_text("# Spec")
        (vendor_sdd / "task.md").write_text("# Task")
        src_dir = self.root / "src" / "app"
        src_dir.mkdir(parents=True)
        (src_dir / "main.py").write_text("print('app')\n")
        config_path = self.cicadas_dir / "config.json"
        config_path.write_text(json.dumps({"scan_exclude_paths": ["vendor/my-sdd-tool"]}))

        tree_path, _metadata_path, _context_path = scan_repo.run_scan()
        entries = [json.loads(line) for line in tree_path.read_text().splitlines() if line.strip()]
        paths = {entry["path"] for entry in entries}

        self.assertIn("src/app/main.py", paths)
        self.assertFalse(any(p.startswith("vendor/my-sdd-tool") for p in paths))


if __name__ == "__main__":
    unittest.main()
