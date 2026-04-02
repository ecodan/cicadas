# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import sys

from graph_build import run_graph_build
from graph_query import dispatch_query
from utils import format_graph_status


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cicadas.py graph", description="Build and inspect the optional Code Graph subsystem.")
    subparsers = parser.add_subparsers(dest="graph_command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the local graph artifacts")
    build_parser.add_argument("--languages", default="auto", help="Comma-separated language filter or 'auto'")
    build_parser.add_argument("--force", action="store_true", help="Rebuild even if graph artifacts already exist")

    subparsers.add_parser("status", help="Show graph availability and freshness")
    for command in ("area", "neighbors", "tests", "callers", "callees", "signature-impact", "route"):
        query_parser = subparsers.add_parser(command, help=f"Run the graph {command} query")
        query_parser.add_argument("target", help="Path, symbol, or description to analyze")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.graph_command == "build":
        return run_graph_build(language_filter=args.languages, force=args.force)

    if args.graph_command == "status":
        print(format_graph_status())
        return 0

    if args.graph_command in {"area", "neighbors", "tests", "callers", "callees", "signature-impact", "route"}:
        code, output = dispatch_query(args.graph_command, args.target)
        print(output)
        return code

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
