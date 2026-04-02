# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tokens import VALID_SOURCES, append_entry, init_log, load_log


SCRIPTS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class CommandSpec:
    name: str
    help: str
    script_name: str | None = None
    aliases: tuple[str, ...] = ()
    usage: str | None = None
    supports_script_help: bool = True


SCRIPT_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("init", "Bootstrap project structure", "init.py", supports_script_help=False),
    CommandSpec("kickoff", "Promote drafts, register initiative, create branch", "kickoff.py"),
    CommandSpec("branch", "Register a feature branch", "branch.py"),
    CommandSpec("status", "Show state, signals, and lifecycle next steps", "status.py", supports_script_help=False),
    CommandSpec("check", "Check for conflicts and branch updates", "check.py", supports_script_help=False),
    CommandSpec("signal", "Broadcast a signal to the current initiative", "signalboard.py", aliases=("signalboard",)),
    CommandSpec("archive", "Expire active specs and deregister work", "archive.py"),
    CommandSpec("update-index", "Append a summary entry to the change ledger", "update_index.py", aliases=("update_index",)),
    CommandSpec("prune", "Rollback and restore specs to drafts", "prune.py"),
    CommandSpec("abort", "Context-aware escape hatch from the current branch", "abort.py"),
    CommandSpec("history", "Generate the HTML history timeline", "history.py"),
    CommandSpec("create-lifecycle", "Create lifecycle.json in drafts or active", "create_lifecycle.py", aliases=("create_lifecycle",)),
    CommandSpec("open-pr", "Open a PR from the current branch", "open_pr.py", aliases=("open_pr",)),
    CommandSpec("review", "Check code review verdict for the current initiative", "review.py"),
    CommandSpec("graph", "Build and inspect the optional Code Graph subsystem", "graph.py"),
    CommandSpec("scan-repo", "Scan the repo and write adaptive canon metadata", "scan_repo.py", aliases=("scan_repo",)),
    CommandSpec("synthesize", "Gather context and generate or apply a synthesis prompt", "synthesize.py"),
    CommandSpec("register-existing", "Register an existing branch in the Cicadas registry", "register_existing.py", aliases=("register_existing",)),
    CommandSpec("validate-skill", "Validate an Agent Skill directory against the spec", "validate_skill.py", aliases=("validate_skill",)),
    CommandSpec("skill-publish", "Publish an active skill to its destination", "skill_publish.py", aliases=("skill_publish",)),
    CommandSpec("emit-event", "Append a typed event to the initiative event log", "emit_event.py", aliases=("emit_event",)),
    CommandSpec("get-events", "Read and filter the initiative event log", "get_events.py", aliases=("get_events",)),
    CommandSpec("unarchive", "Restore an archived initiative or branch", "unarchive.py"),
)

TOKENS_USAGE = """usage: cicadas.py tokens {init,show,append} ...

Manage tokens.json files used for Cicadas token accounting.

subcommands:
  init    Create a tokens.json file if it does not exist
  show    Print the current entries or full JSON payload
  append  Append a validated token entry
"""

FALLBACK_USAGE: dict[str, str] = {
    "init": "usage: cicadas.py init",
    "status": "usage: cicadas.py status",
    "check": "usage: cicadas.py check",
}


def _script_path(script_name: str) -> Path:
    return SCRIPTS_DIR / script_name


def _run_script(script_name: str, script_args: list[str]) -> int:
    completed = subprocess.run([sys.executable, str(_script_path(script_name)), *script_args], cwd=Path.cwd())
    return completed.returncode


def _print_manual_help(spec: CommandSpec) -> None:
    usage = spec.usage or FALLBACK_USAGE.get(spec.name) or f"usage: cicadas.py {spec.name}"
    print(usage)
    print()
    print(spec.help)
    if spec.aliases:
        print()
        print(f"aliases: {', '.join(spec.aliases)}")


def _handle_script_command(spec: CommandSpec, args: argparse.Namespace) -> int:
    forwarded_args = list(args.script_args or [])
    if getattr(args, "show_help", False):
        if spec.supports_script_help and spec.script_name is not None:
            return _run_script(spec.script_name, ["--help"])
        _print_manual_help(spec)
        return 0
    if spec.script_name is None:
        _print_manual_help(spec)
        return 1
    return _run_script(spec.script_name, forwarded_args)


def _tokens_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cicadas.py tokens", description="Manage Cicadas tokens.json files")
    subparsers = parser.add_subparsers(dest="tokens_command", required=True)

    init_parser = subparsers.add_parser("init", help="Create an empty tokens.json file if missing")
    init_parser.add_argument("path", help="Path to the tokens.json file")

    show_parser = subparsers.add_parser("show", help="Print a tokens.json file")
    show_parser.add_argument("path", help="Path to the tokens.json file")
    show_parser.add_argument("--full", action="store_true", help="Print the full JSON payload instead of just entries")

    append_parser = subparsers.add_parser("append", help="Append a token entry to a tokens.json file")
    append_parser.add_argument("path", help="Path to the tokens.json file")
    append_parser.add_argument("--initiative", required=True, help="Initiative name")
    append_parser.add_argument("--phase", required=True, help="Lifecycle or implementation phase name")
    append_parser.add_argument("--source", required=True, choices=sorted(VALID_SOURCES), help="Token source classification")
    append_parser.add_argument("--subphase", default=None, help="Optional subphase name")
    append_parser.add_argument("--input-tokens", type=int, default=None, help="Input token count")
    append_parser.add_argument("--output-tokens", type=int, default=None, help="Output token count")
    append_parser.add_argument("--cached-tokens", type=int, default=None, help="Cached token count")
    append_parser.add_argument("--model", default=None, help="Model identifier")
    append_parser.add_argument("--notes", default=None, help="Optional note")

    return parser


def _handle_tokens(args: argparse.Namespace) -> int:
    if getattr(args, "show_help", False):
        print(TOKENS_USAGE)
        return 0

    parser = _tokens_parser()
    tokens_args = parser.parse_args(list(args.script_args or []))
    path = Path(tokens_args.path)

    if tokens_args.tokens_command == "init":
        init_log(path)
        print(f"[OK]  initialized {path}")
        return 0

    if tokens_args.tokens_command == "show":
        payload = {"entries": load_log(path)}
        if tokens_args.full and path.exists():
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError as exc:
                print(f"Error reading tokens file: {exc}", file=sys.stderr)
                return 1
        print(json.dumps(payload, indent=2))
        return 0

    append_entry(
        path,
        initiative=tokens_args.initiative,
        phase=tokens_args.phase,
        source=tokens_args.source,
        subphase=tokens_args.subphase,
        input_tokens=tokens_args.input_tokens,
        output_tokens=tokens_args.output_tokens,
        cached_tokens=tokens_args.cached_tokens,
        model=tokens_args.model,
        notes=tokens_args.notes,
    )
    print(f"[OK]  appended entry to {path}")
    return 0


def command_specs() -> tuple[CommandSpec, ...]:
    return SCRIPT_COMMANDS + (CommandSpec("tokens", "Manage Cicadas token logs", supports_script_help=False),)


def alias_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in SCRIPT_COMMANDS:
        for alias in spec.aliases:
            mapping[alias] = spec.name
    return mapping


def _configure_forwarding_parser(parser: argparse.ArgumentParser, *, handler, spec: CommandSpec | None = None) -> None:
    parser.add_argument("-h", "--help", action="store_true", dest="show_help", help="Show help for this command")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    if spec is not None:
        parser.set_defaults(handler=handler, spec=spec)
    else:
        parser.set_defaults(handler=handler)


def register_subcommands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    for spec in SCRIPT_COMMANDS:
        parser = subparsers.add_parser(spec.name, add_help=False, help=spec.help, description=spec.help)
        _configure_forwarding_parser(parser, handler=_handle_script_command, spec=spec)

    tokens_parser = subparsers.add_parser("tokens", add_help=False, help="Manage Cicadas token logs", description="Manage Cicadas token logs")
    _configure_forwarding_parser(tokens_parser, handler=_handle_tokens)
