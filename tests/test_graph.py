# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import sqlite3
import subprocess
import sys

from base import CicadasTest, SCRIPTS_DIR


CLI_PATH = SCRIPTS_DIR / "cicadas.py"


class TestGraphCli(CicadasTest):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            cwd=self.root,
            text=True,
            capture_output=True,
        )

    def test_graph_status_reports_not_initialized(self):
        result = self._run_cli("graph", "status")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph: not initialized", result.stdout)

    def test_graph_build_creates_sqlite_and_metadata(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        graph_dir = self.cicadas_dir / "graph"
        self.assertTrue((graph_dir / "codegraph.sqlite").exists())
        self.assertTrue((graph_dir / "metadata.json").exists())
        payload = json.loads((graph_dir / "metadata.json").read_text())
        self.assertEqual(payload["freshness"], "fresh")
        with sqlite3.connect(graph_dir / "codegraph.sqlite") as conn:
            row = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()
        self.assertGreater(row[0], 0)
        self.assertTrue((self.cicadas_dir / "canon" / "repo.json").exists())

    def test_graph_build_seeds_areas_from_repo_metadata(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        (self.cicadas_dir / "canon").mkdir(exist_ok=True)
        (self.cicadas_dir / "canon" / "repo.json").write_text(
            json.dumps(
                {
                    "candidate_slices": [
                        {"name": "payments", "paths": ["src"], "status": "seeded"},
                    ]
                }
            )
        )
        (self.cicadas_dir / "canon" / "repo-tree.jsonl").write_text(
            json.dumps({"path": "src/demo.py", "kind": "file", "language": "python", "extension": ".py", "summary": "demo"}) + "\n"
        )

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        payload = json.loads((self.cicadas_dir / "graph" / "metadata.json").read_text())
        self.assertEqual(payload["seeded_areas"][0]["name"], "payments")

    def test_graph_area_reports_area_for_file(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        (self.cicadas_dir / "canon").mkdir(exist_ok=True)
        (self.cicadas_dir / "canon" / "repo.json").write_text(
            json.dumps({"candidate_slices": [{"name": "payments", "paths": ["src"], "status": "seeded"}]})
        )
        (self.cicadas_dir / "canon" / "repo-tree.jsonl").write_text(
            json.dumps({"path": "src/demo.py", "kind": "file", "language": "python", "extension": ".py", "summary": "demo"}) + "\n"
        )
        self._run_cli("graph", "build")

        result = self._run_cli("graph", "area", "src/demo.py")

        self.assertEqual(result.returncode, 0)
        self.assertIn("payments", result.stdout)

    def test_graph_neighbors_reports_other_seeded_areas(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        (self.cicadas_dir / "canon").mkdir(exist_ok=True)
        (self.cicadas_dir / "canon" / "repo.json").write_text(
            json.dumps(
                {
                    "candidate_slices": [
                        {"name": "payments", "paths": ["src"], "status": "seeded"},
                        {"name": "accounts", "paths": ["lib"], "status": "seeded"},
                    ]
                }
            )
        )
        (self.cicadas_dir / "canon" / "repo-tree.jsonl").write_text(
            json.dumps({"path": "src/demo.py", "kind": "file", "language": "python", "extension": ".py", "summary": "demo"}) + "\n"
        )
        self._run_cli("graph", "build")

        result = self._run_cli("graph", "neighbors", "src/demo.py")

        self.assertEqual(result.returncode, 0)
        self.assertIn("accounts", result.stdout)

    def test_graph_signature_impact_reports_callers_and_tests_for_python(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "helpers.py").write_text(
            "def helper():\n    return 1\n\n"
            "def consumer():\n    return helper()\n"
        )
        (self.root / "tests" / "test_helpers.py").write_text(
            "from src.helpers import helper\n\n"
            "def test_helper():\n    assert helper() == 1\n"
        )

        self._run_cli("graph", "build")
        result = self._run_cli("graph", "signature-impact", "helper")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Direct callers: 2", result.stdout)
        self.assertIn("consumer", result.stdout)
        self.assertIn("test_helper", result.stdout)
