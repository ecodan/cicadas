# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys

from base import CicadasTest, SCRIPTS_DIR
from graph_eval import create_synthetic_repo, load_scenarios, run_eval


CLI_PATH = SCRIPTS_DIR / "cicadas.py"


class TestGraphEval(CicadasTest):
    def test_load_scenarios_validates_supported_queries(self):
        scenario_path = self.root / "scenarios.jsonl"
        scenario_path.write_text(
            json.dumps({"id": "search", "query": "search", "target": "IssueView", "expect": {"paths": ["src/ui/IssueView.tsx"]}})
            + "\n"
        )

        scenarios = load_scenarios(scenario_path)

        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].query, "search")
        self.assertEqual(scenarios[0].target, "IssueView")

    def test_load_scenarios_rejects_unknown_query(self):
        scenario_path = self.root / "bad-scenarios.jsonl"
        scenario_path.write_text(json.dumps({"query": "unknown", "target": "x"}) + "\n")

        with self.assertRaises(ValueError):
            load_scenarios(scenario_path)

    def test_synthetic_eval_writes_report_and_summary(self):
        repo = self.root / "synthetic"
        scenario_file = self.root / "synthetic-scenarios.jsonl"
        output = self.root / "reports" / "graph-eval.json"
        create_synthetic_repo(repo, scenario_file)

        report, summary = run_eval(repo, scenario_file, output)

        self.assertTrue(output.exists())
        payload = json.loads(output.read_text())
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["metrics"]["scenario_count"], 7)
        self.assertGreaterEqual(payload["metrics"]["hits"], 5)
        self.assertIn("search", payload["metrics"]["by_query"])
        self.assertIn("neighbors", payload["metrics"]["by_query"])
        self.assertIn("Graph eval summary", summary)
        self.assertIn("Coverage:", summary)

    def test_graph_eval_cli_runs_against_local_repo(self):
        repo = self.root / "cli-synthetic"
        scenario_file = self.root / "cli-scenarios.jsonl"
        output = self.root / "cli-report.json"

        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "graph",
                "eval",
                "--repo",
                str(repo),
                "--scenario-file",
                str(scenario_file),
                "--output",
                str(output),
                "--generate-synthetic",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output.exists())
        payload = json.loads(output.read_text())
        self.assertEqual(payload["metrics"]["scenario_count"], 7)
        self.assertIn("Graph eval summary", result.stdout)
