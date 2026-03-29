# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import sys

from command_registry import alias_map, register_subcommands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cicadas.py",
        description="Cicadas CLI: one entrypoint for deterministic lifecycle operations.",
    )
    subparsers = parser.add_subparsers(dest="command")
    register_subcommands(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    aliases = alias_map()
    if argv and argv[0] in aliases:
        argv = [aliases[argv[0]], *argv[1:]]

    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    handler = getattr(args, "handler")
    spec = getattr(args, "spec", None)
    if spec is not None:
        return handler(spec, args)
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
