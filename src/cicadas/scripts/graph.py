# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import sys
import time

from graph_build import run_graph_build
from graph_doctor import render_doctor_report
from graph_observe import render_progress_tail, watch_progress
from graph_usage import append_usage_entry, render_usage_report
from graph_query import dispatch_query
from utils import format_graph_status


def _safe_append_usage(**kwargs: object) -> None:
    try:
        append_usage_entry(**kwargs)
    except Exception:
        # Usage logging is best-effort and must never break the user-visible graph command.
        return


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cicadas.py graph", description="Build and inspect the optional Code Graph subsystem.")
    subparsers = parser.add_subparsers(dest="graph_command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the local graph artifacts")
    build_parser.add_argument("--languages", default="auto", help="Comma-separated language filter or 'auto'")
    build_parser.add_argument("--force", action="store_true", help="Rebuild even if graph artifacts already exist")
    tail_parser = subparsers.add_parser("tail", help="Show the latest graph build progress and recent events")
    tail_parser.add_argument("--lines", type=int, default=10, help="Number of recent progress events to show")
    watch_parser = subparsers.add_parser("watch", help="Watch graph build progress until completion")
    watch_parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    watch_parser.add_argument("--max-updates", type=int, default=None, help="Stop after this many progress refreshes")

    subparsers.add_parser("status", help="Show graph availability and freshness")
    subparsers.add_parser("doctor", help="Diagnose graph tooling and analyzer readiness")
    usage_parser = subparsers.add_parser("usage", help="Summarize graph command usage")
    usage_parser.add_argument("--initiative", default=None, help="Filter by initiative")
    usage_parser.add_argument("--since", default=None, help="Filter entries since the given ISO8601 timestamp")
    usage_parser.add_argument("--view", choices=("table", "json", "html"), default="table", help="Report format")
    for command in ("area", "neighbors", "tests", "callers", "callees", "signature-impact", "route", "search"):
        query_parser = subparsers.add_parser(command, help=f"Run the graph {command} query")
        query_parser.add_argument("target", help="Path, symbol, or description to analyze")
        query_parser.add_argument("--exclude-tests", action="store_true", help="Filter test artifacts from result sets when applicable")
        if command == "search":
            query_parser.add_argument("--kind", action="append", choices=("entrypoint", "file", "symbol", "test"), help="Limit search to one or more node kinds")
            query_parser.add_argument("--limit", type=int, default=10, help="Maximum number of search results to return")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    start = time.perf_counter()

    if args.graph_command == "build":
        code = run_graph_build(language_filter=args.languages, force=args.force)
        _safe_append_usage(
            command="cicadas.py graph build",
            query_kind="build",
            target_type="repo",
            operation_name="graph.build",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            result_count=1 if code == 0 else 0,
            usefulness_tags=["graph-built"] if code == 0 else [],
        )
        return code

    if args.graph_command == "status":
        output = format_graph_status()
        print(output)
        _safe_append_usage(
            command="cicadas.py graph status",
            query_kind="status",
            target_type="repo",
            operation_name="graph.status",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            result_count=1,
        )
        return 0

    if args.graph_command == "tail":
        output = render_progress_tail(lines=args.lines)
        print(output)
        _safe_append_usage(
            command="cicadas.py graph tail",
            query_kind="tail",
            target_type="graph-build",
            operation_name="graph.tail",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            result_count=1,
            usefulness_tags=["graph-observability"],
            metadata={"lines": args.lines},
        )
        return 0

    if args.graph_command == "watch":
        code = watch_progress(interval_seconds=args.interval, max_updates=args.max_updates)
        _safe_append_usage(
            command="cicadas.py graph watch",
            query_kind="watch",
            target_type="graph-build",
            operation_name="graph.watch",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            result_count=1 if code == 0 else 0,
            usefulness_tags=["graph-observability"],
            metadata={"interval_seconds": args.interval, "max_updates": args.max_updates},
        )
        return code

    if args.graph_command == "doctor":
        output = render_doctor_report()
        print(output)
        _safe_append_usage(
            command="cicadas.py graph doctor",
            query_kind="doctor",
            target_type="repo",
            operation_name="graph.doctor",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            result_count=1,
        )
        return 0

    if args.graph_command == "usage":
        output = render_usage_report(initiative=args.initiative, since=args.since, view=args.view)
        print(output)
        _safe_append_usage(
            command="cicadas.py graph usage",
            query_kind="usage",
            target_type="report",
            operation_name="graph.usage",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            result_count=1,
            usefulness_tags=["graph-report"],
            metadata={"initiative_filter": args.initiative, "since": args.since, "view": args.view},
        )
        return 0

    if args.graph_command in {"area", "neighbors", "tests", "callers", "callees", "signature-impact", "route", "search"}:
        code, output, meta = dispatch_query(
            args.graph_command,
            args.target,
            exclude_tests=args.exclude_tests,
            kinds=getattr(args, "kind", None),
            limit=getattr(args, "limit", 10),
        )
        print(output)
        command_text = f"cicadas.py graph {args.graph_command} {args.target}"
        if args.exclude_tests:
            command_text += " --exclude-tests"
        if args.graph_command == "search":
            for kind in getattr(args, "kind", None) or []:
                command_text += f" --kind {kind}"
            command_text += f" --limit {getattr(args, 'limit', 10)}"
        _safe_append_usage(
            command=command_text,
            query_kind=args.graph_command,
            target_type="description" if args.graph_command == "route" else "artifact",
            operation_name=f"graph.query.{args.graph_command}",
            end_to_end_ms=round((time.perf_counter() - start) * 1000),
            graph_query_ms=meta.get("graph_query_ms"),
            result_count=meta.get("result_count", 0),
            usefulness_tags=meta.get("usefulness_tags", []),
            metadata=meta.get("metadata", {}),
        )
        return code

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
