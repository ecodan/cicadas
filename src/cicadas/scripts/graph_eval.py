# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from graph_build import run_graph_build
from graph_query import dispatch_query
from utils import load_graph_metadata, save_json


SUPPORTED_QUERY_KINDS = {"search", "route", "neighbors", "tests", "callers", "callees", "signature-impact"}


@dataclass(frozen=True)
class GraphEvalScenario:
    scenario_id: str
    query: str
    target: str
    expect: dict
    limit: int = 10
    exclude_tests: bool = False
    kinds: list[str] | None = None


@contextmanager
def _pushd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def load_scenarios(path: Path) -> list[GraphEvalScenario]:
    scenarios: list[GraphEvalScenario] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid scenario JSONL line {lineno}: {exc}") from exc
        query = payload.get("query")
        if query not in SUPPORTED_QUERY_KINDS:
            raise ValueError(f"Invalid scenario line {lineno}: unsupported query `{query}`")
        target = payload.get("target")
        if not isinstance(target, str) or not target:
            raise ValueError(f"Invalid scenario line {lineno}: target is required")
        expect = payload.get("expect") or {}
        if not isinstance(expect, dict):
            raise ValueError(f"Invalid scenario line {lineno}: expect must be an object")
        scenarios.append(
            GraphEvalScenario(
                scenario_id=str(payload.get("id") or f"scenario-{lineno}"),
                query=query,
                target=target,
                expect=expect,
                limit=int(payload.get("limit") or expect.get("top_n") or 10),
                exclude_tests=bool(payload.get("exclude_tests", False)),
                kinds=list(payload.get("kinds") or []) or None,
            )
        )
    return scenarios


def _result_lines(output: str) -> list[str]:
    return [
        line
        for line in output.splitlines()
        if line.startswith("- ")
        and "Candidate generation:" not in line
        and not line.startswith("- Note:")
        and "excluded" not in line.lower()
    ]


def _expected_tokens(expect: dict) -> list[str]:
    tokens: list[str] = []
    for key in ("paths", "areas", "symbols", "tests", "callers", "callees"):
        value = expect.get(key) or []
        if isinstance(value, str):
            tokens.append(value)
        elif isinstance(value, list):
            tokens.extend(str(item) for item in value)
    return [token for token in tokens if token]


def _rank_for_output(output: str, expect: dict) -> int | None:
    tokens = _expected_tokens(expect)
    if not tokens:
        return None
    lines = _result_lines(output)
    for idx, line in enumerate(lines, start=1):
        if any(token in line for token in tokens):
            return idx
    return None


def _evaluate_scenario(scenario: GraphEvalScenario) -> dict:
    started = time.perf_counter()
    code, output, meta = dispatch_query(
        scenario.query,
        scenario.target,
        exclude_tests=scenario.exclude_tests,
        kinds=scenario.kinds,
        limit=scenario.limit,
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    top_n = int(scenario.expect.get("top_n") or scenario.limit or 10)
    rank = _rank_for_output(output, scenario.expect)
    hit = bool(code == 0 and rank is not None and rank <= top_n)
    failure_reason = None
    if code != 0:
        failure_reason = "query_failed"
    elif rank is None and _expected_tokens(scenario.expect):
        failure_reason = "expected_result_missing"
    elif rank is not None and rank > top_n:
        failure_reason = "expected_result_below_top_n"
    return {
        "id": scenario.scenario_id,
        "query": scenario.query,
        "target": scenario.target,
        "top_n": top_n,
        "hit": hit,
        "rank": rank,
        "latency_ms": latency_ms,
        "graph_query_ms": meta.get("graph_query_ms"),
        "result_count": meta.get("result_count", 0),
        "failure_reason": failure_reason,
        "metadata": meta.get("metadata", {}),
    }


def _avg(values: Iterable[int | float | None]) -> int:
    numbers = [value for value in values if isinstance(value, int | float)]
    if not numbers:
        return 0
    return round(sum(numbers) / len(numbers))


def _aggregate(results: list[dict]) -> dict:
    by_query: dict[str, list[dict]] = {}
    for result in results:
        by_query.setdefault(result["query"], []).append(result)
    query_metrics = {}
    for query, items in sorted(by_query.items()):
        ranks = [item["rank"] for item in items if item.get("rank") is not None]
        query_metrics[query] = {
            "count": len(items),
            "hits": sum(1 for item in items if item.get("hit")),
            "hit_rate": round(sum(1 for item in items if item.get("hit")) / len(items), 3) if items else 0,
            "avg_rank": _avg(ranks),
            "avg_latency_ms": _avg(item.get("latency_ms") for item in items),
            "failure_reasons": sorted({item["failure_reason"] for item in items if item.get("failure_reason")}),
        }
    return {
        "scenario_count": len(results),
        "hits": sum(1 for result in results if result.get("hit")),
        "hit_rate": round(sum(1 for result in results if result.get("hit")) / len(results), 3) if results else 0,
        "avg_latency_ms": _avg(result.get("latency_ms") for result in results),
        "by_query": query_metrics,
    }


def render_summary(report: dict) -> str:
    metrics = report.get("metrics", {})
    lines = [
        "Graph eval summary",
        f"Repo: {report.get('repo')}",
        f"Scenarios: {metrics.get('scenario_count', 0)}",
        f"Hits: {metrics.get('hits', 0)}",
        f"Hit rate: {metrics.get('hit_rate', 0)}",
        f"Avg latency ms: {metrics.get('avg_latency_ms', 0)}",
        f"Coverage: {json.dumps(report.get('coverage', {}), sort_keys=True)}",
    ]
    for query, data in sorted((metrics.get("by_query") or {}).items()):
        reasons = ", ".join(data.get("failure_reasons") or []) or "none"
        lines.append(
            f"- {query}: count={data.get('count', 0)}, hits={data.get('hits', 0)}, "
            f"hit_rate={data.get('hit_rate', 0)}, avg_rank={data.get('avg_rank', 0)}, "
            f"avg_latency_ms={data.get('avg_latency_ms', 0)}, failures={reasons}"
        )
    return "\n".join(lines)


def run_eval(repo: Path, scenario_file: Path, output: Path, *, build: bool = True) -> tuple[dict, str]:
    repo = repo.resolve()
    scenario_file = scenario_file.resolve()
    output = output.resolve()
    scenarios = load_scenarios(scenario_file)
    with _pushd(repo):
        build_started = time.perf_counter()
        build_code = run_graph_build(force=True) if build else 0
        build_latency_ms = round((time.perf_counter() - build_started) * 1000)
        results = [_evaluate_scenario(scenario) for scenario in scenarios]
        metadata = load_graph_metadata() or {}
    report = {
        "schema_version": 1,
        "repo": str(repo),
        "scenario_file": str(scenario_file),
        "build": {
            "enabled": build,
            "exit_code": build_code,
            "latency_ms": build_latency_ms,
        },
        "coverage": metadata.get("analyzers", {}),
        "indexed_languages": metadata.get("indexed_languages", []),
        "metrics": _aggregate(results),
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    save_json(output, report)
    return report, render_summary(report)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_synthetic_repo(repo: Path, scenario_file: Path) -> None:
    """Create a public synthetic mega-repo-style fixture.

    Private Jira/Confluence scenarios should be passed as local JSONL files via
    --scenario-file and kept outside this public repository, or in gitignored
    local paths.
    """
    repo.mkdir(parents=True, exist_ok=True)
    for idx in range(60):
        _write(repo / "requirements" / f"story_{idx}.md", f"# Story {idx}\n\nSynthetic planning context.\n")
    for idx in range(320):
        _write(repo / "src" / "support" / f"IssueViewFixture{idx}.py", f"def issue_view_fixture_{idx}():\n    return {{}}\n")
    _write(repo / "src" / "ui" / "IssueView.tsx", "export function IssueView() {\n  return null;\n}\n")
    _write(repo / "src" / "payments" / "pay.py", "from src.accounts.ledger import ledger\n\ndef checkout():\n    return ledger()\n")
    _write(repo / "src" / "accounts" / "ledger.py", "def ledger():\n    return 1\n")
    _write(repo / "tests" / "test_ledger.py", "from src.accounts.ledger import ledger\n\ndef test_ledger():\n    assert ledger() == 1\n")
    _write(repo / "crates" / "core" / "src" / "lib.rs", "pub struct Issue;\n#[test]\nfn test_issue() {}\n")
    _write(repo / ".gitignore", "dist/\n")
    _write(repo / "dist" / "bundle.js", "export function generated() {}\n")

    canon = repo / ".cicadas" / "canon"
    canon.mkdir(parents=True, exist_ok=True)
    file_entries = []
    language_by_suffix = {".py": "python", ".tsx": "typescript", ".rs": "rust", ".md": "markdown", ".js": "javascript"}
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or ".cicadas" in path.parts:
            continue
        rel = path.relative_to(repo).as_posix()
        suffix = path.suffix.lower()
        file_entries.append(
            {
                "path": rel,
                "kind": "file",
                "language": language_by_suffix.get(suffix),
                "extension": suffix,
                "summary": rel,
                "source_class": "documentation" if suffix == ".md" else "code",
            }
        )
    (canon / "repo-tree.jsonl").write_text("\n".join(json.dumps(entry, sort_keys=True) for entry in file_entries) + "\n", encoding="utf-8")
    save_json(
        canon / "repo.json",
        {
            "repo_mode": "mega-repo",
            "candidate_slices": [
                {"name": "ui", "paths": ["src/ui"], "status": "seeded"},
                {"name": "payments", "paths": ["src/payments"], "status": "seeded"},
                {"name": "accounts", "paths": ["src/accounts"], "status": "seeded"},
                {"name": "support", "paths": ["src/support"], "status": "deferred"},
            ],
            "scan": {"dominant_languages": ["python", "typescript", "rust"]},
        },
    )
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    scenarios = [
        {"id": "search-ui", "query": "search", "target": "IssueView", "limit": 5, "expect": {"paths": ["src/ui/IssueView.tsx"], "top_n": 5}},
        {"id": "route-payments", "query": "route", "target": "payments checkout flow", "expect": {"areas": ["payments"], "top_n": 3}},
        {"id": "neighbors-payments", "query": "neighbors", "target": "src/payments/pay.py", "expect": {"areas": ["accounts"], "top_n": 3}},
        {"id": "tests-ledger", "query": "tests", "target": "ledger", "expect": {"tests": ["test_ledger"], "top_n": 5}},
        {"id": "callers-ledger", "query": "callers", "target": "ledger", "expect": {"callers": ["checkout"], "top_n": 5}},
        {"id": "callees-checkout", "query": "callees", "target": "checkout", "expect": {"callees": ["ledger"], "top_n": 5}},
        {"id": "impact-ledger", "query": "signature-impact", "target": "ledger", "expect": {"callers": ["checkout"], "tests": ["test_ledger"], "top_n": 10}},
    ]
    scenario_file.write_text("\n".join(json.dumps(scenario, sort_keys=True) for scenario in scenarios) + "\n", encoding="utf-8")
