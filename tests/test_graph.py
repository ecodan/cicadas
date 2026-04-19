# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from base import CicadasTest, SCRIPTS_DIR
import graph_extract.java as graph_java
import graph_store
from graph_ir import GraphEdge, GraphNode


CLI_PATH = SCRIPTS_DIR / "cicadas.py"


class TestGraphCli(CicadasTest):
    FIXTURES_DIR = Path(__file__).parent / "fixtures"

    def _run_cli(self, *args: str, graph_enabled: bool = True) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if graph_enabled:
            env["CICADAS_GRAPH_EXPERIMENTAL"] = "1"
        else:
            env.pop("CICADAS_GRAPH_EXPERIMENTAL", None)
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            env=env,
        )

    def _copy_fixture(self, name: str) -> None:
        fixture_root = self.FIXTURES_DIR / name
        for path in fixture_root.rglob("*"):
            if not path.is_file():
                continue
            rel_path = path.relative_to(fixture_root)
            target = self.root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    def test_graph_status_reports_not_initialized(self):
        result = self._run_cli("graph", "status")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph: not initialized", result.stdout)

    def test_graph_status_reports_experimental_disabled_by_default(self):
        result = self._run_cli("graph", "status", graph_enabled=False)

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph: experimental disabled", result.stdout)
        self.assertIn("CICADAS_GRAPH_EXPERIMENTAL=1", result.stdout)

    def test_graph_build_requires_experimental_opt_in(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")

        result = self._run_cli("graph", "build", graph_enabled=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn("Graph support is experimental and disabled by default", result.stdout)
        self.assertFalse((self.cicadas_dir / "graph" / "codegraph.sqlite").exists())

    def test_graph_doctor_reports_experimental_gate_state(self):
        result = self._run_cli("graph", "doctor", graph_enabled=False)

        self.assertEqual(result.returncode, 0)
        self.assertIn("Experimental gate: disabled", result.stdout)

    def test_graph_build_creates_sqlite_and_metadata(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        graph_dir = self.cicadas_dir / "graph"
        self.assertTrue((graph_dir / "codegraph.sqlite").exists())
        self.assertTrue((graph_dir / "metadata.json").exists())
        self.assertTrue((graph_dir / "area-plan.json").exists())
        self.assertTrue((graph_dir / "progress.json").exists())
        self.assertTrue((graph_dir / "progress-log.jsonl").exists())
        self.assertTrue((graph_dir / "spool" / "nodes.jsonl").exists())
        self.assertTrue((graph_dir / "spool" / "edges.jsonl").exists())
        payload = json.loads((graph_dir / "metadata.json").read_text())
        progress = json.loads((graph_dir / "progress.json").read_text())
        self.assertEqual(payload["freshness"], "fresh")
        self.assertEqual(progress["status"], "complete")
        self.assertEqual(progress["percent_complete"], 100)
        self.assertEqual(progress["phase"], "complete")
        self.assertGreaterEqual(progress["structural_files_processed"], 1)
        self.assertGreater(progress["stage_nodes_written"], 0)
        self.assertGreaterEqual(progress["stage_edges_written"], 0)
        self.assertGreaterEqual(progress["elapsed_seconds"], 0)
        self.assertEqual(progress["eta_seconds"], 0)
        area_plan = json.loads((graph_dir / "area-plan.json").read_text())
        self.assertIn("areas", area_plan)
        with sqlite3.connect(graph_dir / "codegraph.sqlite") as conn:
            row = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()
            stage_row = conn.execute("SELECT COUNT(*) FROM graph_nodes_stage").fetchone()
        self.assertGreater(row[0], 0)
        self.assertGreater(stage_row[0], 0)
        self.assertTrue((self.cicadas_dir / "canon" / "repo.json").exists())
        self.assertIn("Graph build started", result.stdout)
        self.assertIn("Area planning complete", result.stdout)
        self.assertIn("Writing graph data to SQLite stage tables", result.stdout)
        self.assertIn("SQLite stage write complete", result.stdout)
        self.assertIn("Promoting stage graph into active tables", result.stdout)
        self.assertIn("SQLite active graph write complete", result.stdout)

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

    def test_graph_build_refreshes_stale_large_repo_scan_when_candidate_slices_are_missing(self):
        self.init_git()
        for module_name in ["jira-components", "jira-domains", "jira-devops"]:
            module_src = self.root / module_name / "src" / "main" / "java" / "com" / "acme"
            module_src.mkdir(parents=True)
            (module_src / "Demo.java").write_text("class Demo {}\n")
        (self.root / "pom.xml").write_text(
            "<project><modules>"
            "<module>jira-components</module>"
            "<module>jira-domains</module>"
            "<module>jira-devops</module>"
            "</modules></project>"
        )
        (self.root / "package.json").write_text(json.dumps({"name": "jira"}))
        (self.cicadas_dir / "canon").mkdir(exist_ok=True)
        (self.cicadas_dir / "canon" / "repo.json").write_text(
            json.dumps(
                {
                    "repo_mode": "mega-repo",
                    "scan": {
                        "declared_modules": ["jira-components", "jira-domains", "jira-devops"],
                        "ownership_zone_candidates": [],
                    },
                    "candidate_slices": [],
                }
            )
        )
        (self.cicadas_dir / "canon" / "repo-tree.jsonl").write_text(
            json.dumps({"path": "pom.xml", "kind": "file", "language": "xml", "extension": ".xml", "summary": "pom"}) + "\n"
        )

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        self.assertIn("area seeds are insufficient", result.stdout)
        payload = json.loads((self.cicadas_dir / "graph" / "metadata.json").read_text())
        area_names = {area["name"] for area in payload["seeded_areas"]}
        self.assertIn("jira-components", area_names)
        self.assertIn("jira-domains", area_names)

    def test_graph_build_refines_large_seeded_area_into_child_areas(self):
        self.init_git()
        for idx in range(10):
            target = self.root / "src" / "payments" / f"payment_{idx}.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"def payment_{idx}():\n    return {idx}\n")
        for idx in range(10):
            target = self.root / "src" / "accounts" / f"account_{idx}.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"def account_{idx}():\n    return {idx}\n")
        (self.cicadas_dir / "canon").mkdir(exist_ok=True)
        (self.cicadas_dir / "canon" / "repo.json").write_text(
            json.dumps({"candidate_slices": [{"name": "app", "paths": ["src"], "status": "seeded"}]})
        )
        entries = []
        for path in sorted((self.root / "src").rglob("*.py")):
            rel_path = path.relative_to(self.root).as_posix()
            entries.append(json.dumps({"path": rel_path, "kind": "file", "language": "python", "extension": ".py", "summary": rel_path}))
        (self.cicadas_dir / "canon" / "repo-tree.jsonl").write_text("\n".join(entries) + "\n")

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        payload = json.loads((self.cicadas_dir / "graph" / "metadata.json").read_text())
        area_names = {area["name"] for area in payload["seeded_areas"]}
        self.assertIn("app", area_names)
        self.assertIn("src-payments", area_names)
        self.assertIn("src-accounts", area_names)
        payments_area = next(area for area in payload["seeded_areas"] if area["name"] == "src-payments")
        self.assertIn(payments_area["routing_confidence"], {"low", "medium", "high"})
        self.assertEqual(payments_area["parent_area"], "app")

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
        self.assertIn("Confidence:", result.stdout)

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
        self.assertIn("confidence:", result.stdout)

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

    def test_graph_signature_impact_can_exclude_tests(self):
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
        result = self._run_cli("graph", "signature-impact", "helper", "--exclude-tests")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Direct callers: 1", result.stdout)
        self.assertIn("consumer", result.stdout)
        self.assertNotIn("test_helper", result.stdout)
        self.assertIn("Linked tests: 0", result.stdout)
        self.assertIn("excluded", result.stdout)

    def test_graph_signature_impact_reports_callers_and_tests_for_java(self):
        self.init_git()
        self._copy_fixture("java_calculator")

        self._run_cli("scan-repo")
        self._run_cli("graph", "build")
        result = self._run_cli("graph", "signature-impact", "com.acme.Calculator#add")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Direct callers: 1", result.stdout)
        self.assertIn("com.acme.CalculatorTest#testAdd", result.stdout)
        self.assertIn("Linked tests: 1", result.stdout)
        self.assertIn("com.acme.CalculatorTest#testAdd()", result.stdout)

    def test_graph_doctor_reports_java_harness_readiness(self):
        result = self._run_cli("graph", "doctor")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph doctor", result.stdout)
        self.assertIn("Java mode:", result.stdout)
        self.assertIn("Java toolchain:", result.stdout)
        self.assertIn("Java semantic source:", result.stdout)

    def test_java_semantic_batches_split_large_source_roots(self):
        java_paths = [f"jira-domains/platform/foo/src/main/java/com/acme/File{idx}.java" for idx in range(4500)]

        batches = graph_java._semantic_batches(self.root, java_paths, max_files_per_batch=2000)

        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0][0]), 2000)
        self.assertEqual(len(batches[1][0]), 2000)
        self.assertEqual(len(batches[2][0]), 500)

    def test_stage_upsert_allows_semantic_rows_to_replace_structural_duplicates(self):
        graph_db = self.root / ".cicadas" / "graph" / "codegraph.sqlite"
        conn = graph_store.connect_graph(graph_db)
        try:
            graph_store.initialize_schema(conn)
            graph_store.reset_stage_graph(conn, "build-1")
            symbol = GraphNode(
                node_id="symbol:1",
                kind="symbol",
                name="com.acme.Calculator#add",
                language="java",
                path="src/main/java/com/acme/Calculator.java",
                build_id="build-1",
                metadata={"extraction_source": "structural"},
            )
            edge = GraphEdge(
                edge_id="calls:1",
                kind="calls",
                src_id="symbol:caller",
                dst_id="symbol:1",
                build_id="build-1",
                metadata={"extraction_source": "structural"},
            )
            graph_store.insert_stage_nodes(conn, [symbol], "build-1")
            graph_store.insert_stage_edges(conn, [edge], "build-1")

            semantic_symbol = GraphNode(
                node_id="symbol:1",
                kind="symbol",
                name="com.acme.Calculator#add",
                language="java",
                path="src/main/java/com/acme/Calculator.java",
                build_id="build-1",
                metadata={"extraction_source": "semantic", "full_name": "com.acme.Calculator#add()"},
            )
            semantic_edge = GraphEdge(
                edge_id="calls:1",
                kind="calls",
                src_id="symbol:caller",
                dst_id="symbol:1",
                build_id="build-1",
                metadata={"extraction_source": "semantic", "resolved": True},
            )
            graph_store.insert_stage_nodes(conn, [semantic_symbol], "build-1")
            graph_store.insert_stage_edges(conn, [semantic_edge], "build-1")

            stored_node = conn.execute("SELECT metadata_json FROM graph_nodes_stage WHERE node_id = 'symbol:1'").fetchone()
            stored_edge = conn.execute("SELECT metadata_json FROM graph_edges_stage WHERE edge_id = 'calls:1'").fetchone()
        finally:
            conn.close()

        self.assertEqual(json.loads(stored_node[0])["extraction_source"], "semantic")
        self.assertEqual(json.loads(stored_edge[0])["extraction_source"], "semantic")
        self.assertTrue(json.loads(stored_edge[0])["resolved"])

    def test_graph_query_writes_usage_log_with_end_to_end_timing(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        self._run_cli("graph", "build")

        result = self._run_cli("graph", "area", "src/demo.py")

        self.assertEqual(result.returncode, 0)
        usage_path = self.cicadas_dir / "graph" / "usage.jsonl"
        self.assertTrue(usage_path.exists())
        entries = [json.loads(line) for line in usage_path.read_text().splitlines() if line.strip()]
        self.assertTrue(any(entry["query_kind"] == "area" for entry in entries))
        area_entry = next(entry for entry in entries if entry["query_kind"] == "area")
        self.assertIn("call_duration_ms", area_entry)
        self.assertGreaterEqual(area_entry["call_duration_ms"], 0)
        self.assertIn("end_to_end_ms", area_entry)
        self.assertGreaterEqual(area_entry["end_to_end_ms"], 0)
        self.assertIn("graph_query_ms", area_entry)
        self.assertGreaterEqual(area_entry["graph_query_ms"], 0)
        self.assertEqual(area_entry["operation_name"], "graph.query.area")

    def test_graph_usage_reports_summary(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        self._run_cli("graph", "build")
        self._run_cli("graph", "area", "src/demo.py")

        result = self._run_cli("graph", "usage")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph usage summary", result.stdout)
        self.assertIn("area", result.stdout)
        self.assertIn("avg_call_duration_ms", result.stdout)
        self.assertIn("avg_end_to_end_ms", result.stdout)

    def test_graph_search_finds_operational_symbols(self):
        self.init_git()
        (self.root / "src" / "ui").mkdir(parents=True)
        (self.root / "src" / "support").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / "src" / "ui" / "IssueView.tsx").write_text(
            "export function IssueView() {\n  return null;\n}\n"
        )
        (self.root / "src" / "support" / "IssueViewSerializer.py").write_text(
            "def serialize_issue_view():\n    return {}\n"
        )
        (self.root / "tests" / "test_issue_view.py").write_text(
            "def test_issue_view():\n    assert True\n"
        )

        self._run_cli("graph", "build")
        result = self._run_cli("graph", "search", "IssueView", "--exclude-tests", "--limit", "5")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Search results for `IssueView`", result.stdout)
        self.assertIn("IssueView.tsx", result.stdout)
        self.assertNotIn("test_issue_view", result.stdout)

    def test_graph_build_indexes_javascript_structurally(self):
        self.init_git()
        (self.root / "frontend" / "issue").mkdir(parents=True)
        (self.root / "frontend" / "issue" / "IssueView.tsx").write_text(
            "import React from 'react';\n"
            "export function IssueView() {\n"
            "  return null;\n"
            "}\n"
            "export default IssueView;\n"
        )

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        metadata = json.loads((self.cicadas_dir / "graph" / "metadata.json").read_text())
        self.assertEqual(metadata["analyzers"]["javascript"], "structural")
        self.assertGreater(metadata["javascript_symbols_indexed"], 0)

        search_result = self._run_cli("graph", "search", "IssueView", "--kind", "entrypoint", "--limit", "5")
        self.assertEqual(search_result.returncode, 0)
        self.assertIn("entrypoint:", search_result.stdout)
        self.assertIn("IssueView.tsx", search_result.stdout)

    def test_graph_build_tolerates_non_utf8_javascript_sources(self):
        self.init_git()
        (self.root / "frontend").mkdir(parents=True)
        with open(self.root / "frontend" / "legacy.js", "wb") as handle:
            handle.write(b"export function legacyView() { return '\\xe2'; }\n")

        result = self._run_cli("graph", "build")

        self.assertEqual(result.returncode, 0)
        metadata = json.loads((self.cicadas_dir / "graph" / "metadata.json").read_text())
        self.assertEqual(metadata["analyzers"]["javascript"], "structural")

    def test_graph_search_supports_kind_filter(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def issue_helper():\n    return 1\n")

        self._run_cli("graph", "build")
        result = self._run_cli("graph", "search", "issue", "--kind", "symbol", "--limit", "5")

        self.assertEqual(result.returncode, 0)
        self.assertIn("symbol:", result.stdout)

    def test_graph_usage_log_records_exclude_tests_flag(self):
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

        result = self._run_cli("graph", "signature-impact", "helper", "--exclude-tests")

        self.assertEqual(result.returncode, 0)
        usage_path = self.cicadas_dir / "graph" / "usage.jsonl"
        entries = [json.loads(line) for line in usage_path.read_text().splitlines() if line.strip()]
        impact_entry = next(entry for entry in reversed(entries) if entry["query_kind"] == "signature-impact")
        self.assertTrue(impact_entry["metadata"]["exclude_tests"])
        self.assertIn("--exclude-tests", impact_entry["command"])

    def test_graph_usage_supports_initiative_and_since_filters(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        self._run_cli("graph", "build")
        self._run_cli("graph", "area", "src/demo.py")

        result = self._run_cli("graph", "usage", "--initiative", "unknown-initiative", "--since", "2999-01-01T00:00:00Z")

        self.assertEqual(result.returncode, 0)
        self.assertIn("No graph usage recorded yet.", result.stdout)

    def test_graph_usage_json_and_corrupt_log_resilience(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        self._run_cli("graph", "build")
        self._run_cli("graph", "area", "src/demo.py")
        usage_path = self.cicadas_dir / "graph" / "usage.jsonl"
        with open(usage_path, "a", encoding="utf-8") as f:
            f.write("{this is not valid json}\n")

        table_result = self._run_cli("graph", "usage")
        json_result = self._run_cli("graph", "usage", "--view", "json")
        html_result = self._run_cli("graph", "usage", "--view", "html")

        self.assertEqual(table_result.returncode, 0)
        self.assertIn("Corrupt entries ignored: 1", table_result.stdout)
        self.assertEqual(json_result.returncode, 0)
        payload = json.loads(json_result.stdout)
        self.assertEqual(payload["corrupt_entries"], 1)
        self.assertTrue(any(entry["query_kind"] == "area" for entry in payload["entries"]))
        self.assertEqual(html_result.returncode, 0)
        self.assertIn("<html>", html_result.stdout)
        self.assertIn("Avg call duration ms", html_result.stdout)
        self.assertIn("Avg end-to-end ms", html_result.stdout)

    def test_graph_tail_reports_recent_progress(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        self._run_cli("graph", "build")

        result = self._run_cli("graph", "tail", "--lines", "3")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph build tail", result.stdout)
        self.assertIn("Stage rows:", result.stdout)
        self.assertIn("Recent events:", result.stdout)

    def test_graph_watch_reports_progress_snapshot(self):
        self.init_git()
        (self.root / "src").mkdir()
        (self.root / "src" / "demo.py").write_text("def demo():\n    return 1\n")
        self._run_cli("graph", "build")

        result = self._run_cli("graph", "watch", "--interval", "0.2", "--max-updates", "1")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Graph build tail", result.stdout)
        self.assertIn("Percent:", result.stdout)
