# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import tracing
from utils import load_config


SCRIPTS_DIR = Path(__file__).resolve().parent

POSITIONAL_COMMANDS = {"kickoff", "branch", "archive", "prune", "unarchive", "register-existing"}


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
    CommandSpec("graph", "Build and inspect the experimental Code Graph subsystem", "graph.py"),
    CommandSpec("scan-repo", "Scan the repo and write adaptive canon metadata", "scan_repo.py", aliases=("scan_repo",)),
    CommandSpec("synthesize", "Gather context and generate or apply a synthesis prompt", "synthesize.py"),
    CommandSpec("register-existing", "Register an existing branch in the Cicadas registry", "register_existing.py", aliases=("register_existing",)),
    CommandSpec("validate-skill", "Validate an Agent Skill directory against the spec", "validate_skill.py", aliases=("validate_skill",)),
    CommandSpec("skill-publish", "Publish an active skill to its destination", "skill_publish.py", aliases=("skill_publish",)),
    CommandSpec("emit-event", "Append a typed event to the initiative event log", "emit_event.py", aliases=("emit_event",)),
    CommandSpec("get-events", "Read and filter the initiative event log", "get_events.py", aliases=("get_events",)),
    CommandSpec("unarchive", "Restore an archived initiative or branch", "unarchive.py"),
    CommandSpec("tutorial", "Run the interactive Cicadas tutorial", "tutorial.py", supports_script_help=False),
)

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


def _detect_initiative(command_name: str, forwarded_args: list[str]) -> str | None:
    for i, arg in enumerate(forwarded_args):
        if arg == "--initiative" and i + 1 < len(forwarded_args):
            return forwarded_args[i + 1]
        if arg.startswith("--initiative="):
            return arg.split("=", 1)[1]
    if command_name in POSITIONAL_COMMANDS:
        for arg in forwarded_args:
            if not arg.startswith("-"):
                return arg
    return None


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

    initiative = _detect_initiative(spec.name, forwarded_args)
    try:
        tracer = tracing.init_tracer(load_config())
        parent_ctx = tracing.parent_context_for_initiative(initiative) if initiative else None
    except Exception:
        tracer, parent_ctx = tracing._NullTracer(), None

    # `exit_code` doubles as a "did _run_script already execute?" marker so that
    # a tracing failure (including from the span's __exit__) can never trigger
    # a second invocation of the underlying command.
    exit_code = None
    try:
        with tracer.start_as_current_span(f"cicadas.command.{spec.name}", context=parent_ctx) as span:
            try:
                span.set_attribute("cicadas.command", spec.name)
                if initiative:
                    span.set_attribute("cicadas.initiative", initiative)
            except Exception:
                pass

            exit_code = _run_script(spec.script_name, forwarded_args)

            try:
                span.set_attribute("cicadas.exit_code", exit_code)
            except Exception:
                pass
    except Exception:
        if exit_code is None:
            exit_code = _run_script(spec.script_name, forwarded_args)

    try:
        tracing.flush()
    except Exception:
        pass

    return exit_code


def command_specs() -> tuple[CommandSpec, ...]:
    return SCRIPT_COMMANDS


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


