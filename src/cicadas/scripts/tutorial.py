# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

"""Interactive Cicadas tutorial — 7-step walkthrough of the methodology."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# When run as a subprocess by the CLI dispatcher, the scripts directory is
# already on sys.path. When imported directly in tests or called from init.py
# in-process, we may need to add it. Guard so we only insert when necessary.
_SCRIPTS_DIR = str(Path(__file__).parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from utils import print_tutorial_banner, print_tutorial_checkmark  # noqa: E402

# ---------------------------------------------------------------------------
# Mock output strings — match real Cicadas CLI output format exactly.
# ---------------------------------------------------------------------------

MOCK_START = """\
Your agent will ask you a few questions about the project — for example,
at what granularity you'd like to progress through the specs and where
you want PRs — and then create the initiative.

(Note: Initiatives are full-sized projects with PRD, UXD and Tech Designs.
Tweak, Bug and Tech Initiatives are also available.)"""

MOCK_SPECS = """\
The agent will guide you through the process. Depending on whether you
chose Section, Doc or All granularity, the agent will pause after each
doc section, each doc, or at the end of all docs for you to ask
questions and make corrections.

Once you're happy with the specs, tell the agent to create an approach
and task list. The approach defines the large-grained partitions — the
logical work that belongs together — and includes a DAG showing how to
sequence the work. The task list contains the individual work items the
implementing agent will complete."""

MOCK_KICKOFF = """\
[OK]   Promoted specs: .cicadas/drafts/my-project → .cicadas/active/my-project
[OK]   Registered initiative: my-project
[OK]   Created branch: initiative/my-project
[OK]   Pushed initiative/my-project to remote"""

MOCK_BUILD = """\
Switched to a new branch 'feat/partition-1'
[OK]   Branch registered: feat/partition-1
[INFO] Implementing tasks for partition 1...
[task.complete] id=1 — Add core data model
[task.complete] id=2 — Implement service layer
[task.complete] id=3 — Write unit tests"""

MOCK_CODE_REVIEW = """\
── Code Review: feat/partition-1 ──────────────────────────────────────
Scope: Full (feat/ branch)
Tasks complete: 3 / 3  ✓
Acceptance criteria met: yes  ✓
Security scan: no issues  ✓
Correctness: no issues  ✓

Verdict: APPROVED — ready to merge"""

MOCK_COMPLETE_PARTITION = """\
[OK]   Logged feat/partition-1 → index.json
[OK]   Merged feat/partition-1 → initiative/my-project
[OK]   Pushed initiative/my-project"""

MOCK_OPEN_PR = """\
[OK]   Opening PR: feat/partition-1 → initiative/my-project
       https://github.com/your-org/your-repo/pull/42
[INFO] Waiting for Builder merge confirmation..."""

MOCK_COMPLETE_INITIATIVE = """\
[OK]   Merged initiative/my-project → main
[OK]   Canon synthesized and committed
[OK]   Archived: my-project → .cicadas/archive/20260101-000000-my-project
[OK]   Index updated"""

# ---------------------------------------------------------------------------
# Total tutorial steps
# ---------------------------------------------------------------------------

_TOTAL_STEPS = 7


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _pause() -> None:
    """Wait for Enter unless stdin is not a TTY (automated / piped)."""
    if sys.stdin.isatty():
        try:
            input("\n  Press Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            print()


def _print_concept(lines: list[str]) -> None:
    """Print indented concept lines."""
    for line in lines:
        print(f"  {line}")


def _print_prompt(prompt: str) -> None:
    """Print the 💬 agent prompt in a visually distinct style."""
    print()
    print(f'  💬 Tell your agent: "{prompt}"')
    print()


def _print_mock(output: str) -> None:
    """Print mock CLI output, indented."""
    print()
    for line in output.splitlines():
        print(f"  {line}")
    print()


def _run_step(
    step_num: int,
    title: str,
    concept: list[str],
    agent_prompt: str | None,
    mock_output: str,
    checkmark_msg: str,
) -> None:
    """Print a single tutorial step: banner → concept → prompt → mock → checkmark → pause."""
    print()
    print_tutorial_banner(step_num, _TOTAL_STEPS, title)
    print()
    _print_concept(concept)
    if agent_prompt is not None:
        _print_prompt(agent_prompt)
    _print_mock(mock_output)
    print_tutorial_checkmark(checkmark_msg)
    _pause()


# ---------------------------------------------------------------------------
# Completion screen
# ---------------------------------------------------------------------------

_CHEATSHEET = [
    ("1 — Start",             'Start an initiative called <name>'),
    ("2 — Spec",              "(agent-guided — no prompt needed)"),
    ("3 — Kickoff",           'Kickoff the initiative'),
    ("4 — Build",             'Implement partition <name>'),
    ("5 — Complete partition", 'Code review and complete partition'),
    ("6 — PR",                'Create a PR'),
    ("7 — Complete",          'Complete the initiative'),
]


def _completion_screen() -> None:
    """Print the final "You're ready!" screen with the full cheatsheet."""
    print()
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   🎉  You're ready to use Cicadas!")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("  Quick Reference — 7 agent prompts:")
    print()
    for label, prompt in _CHEATSHEET:
        if prompt.startswith("("):
            print(f"    Step {label}")
            print(f"      {prompt}")
        else:
            print(f"    Step {label}")
            print(f'      💬 "{prompt}"')
        print()
    print("  Tip: run `cicadas status` anytime to see what's next.")
    print()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(args: argparse.Namespace | None = None) -> int:  # noqa: ARG001
    """Run the interactive 7-step Cicadas tutorial."""

    print()
    print("  Welcome to the Cicadas interactive tutorial!")
    print("  You'll learn the 7-step workflow in about 5 minutes.")

    # ── Step 1: Start ──────────────────────────────────────────────────────
    _run_step(
        step_num=1,
        title="Start an initiative",
        concept=[
            "Every piece of work in Cicadas begins by telling your AI agent",
            "what you want to build. The agent creates a draft folder and",
            "begins the spec authoring process.",
        ],
        agent_prompt="Start an initiative called my-project",
        mock_output=MOCK_START,
        checkmark_msg="Draft folder created: .cicadas/drafts/my-project/",
    )

    # ── Step 2: Define specs ───────────────────────────────────────────────
    _run_step(
        step_num=2,
        title="Define specs (agent-guided)",
        concept=[
            "Your agent will guide you through five spec documents:",
            "  PRD → UX → Tech Design → Approach → Tasks",
            "",
            "You review and approve each one before the agent proceeds.",
        ],
        agent_prompt=None,
        mock_output=MOCK_SPECS,
        checkmark_msg="Specs approved: prd.md, ux.md, tech-design.md, approach.md, tasks.md",
    )

    # ── Step 3: Kickoff ────────────────────────────────────────────────────
    _run_step(
        step_num=3,
        title="Kickoff the initiative",
        concept=[
            "Once specs are approved, kickoff promotes them from drafts to",
            "active, registers the initiative, and creates the initiative branch.",
        ],
        agent_prompt="Kickoff the initiative",
        mock_output=MOCK_KICKOFF,
        checkmark_msg="Initiative branch created: initiative/my-project",
    )

    # ── Step 4: Build ──────────────────────────────────────────────────────
    _run_step(
        step_num=4,
        title="Implement a partition",
        concept=[
            "Your agent implements one partition (feature branch) at a time.",
            "It creates task branches, writes code, runs Reflect to keep specs",
            "current, and marks tasks complete as it goes.",
        ],
        agent_prompt="Implement partition 1",
        mock_output=MOCK_BUILD,
        checkmark_msg="Partition tasks implemented and specs updated",
    )

    # ── Step 5a: Code review ───────────────────────────────────────────────
    _run_step(
        step_num=5,
        title="Code review and complete partition",
        concept=[
            "Before merging, the agent runs a structured code review:",
            "task completeness, acceptance criteria, security, correctness.",
            "Then it merges the feature branch into the initiative branch.",
        ],
        agent_prompt="Code review and complete partition",
        mock_output=MOCK_CODE_REVIEW + "\n\n" + MOCK_COMPLETE_PARTITION,
        checkmark_msg="Partition merged into initiative/my-project",
    )

    # ── Step 6: PR ────────────────────────────────────────────────────────
    _run_step(
        step_num=6,
        title="Create a PR",
        concept=[
            "When all partitions are done, the agent opens a Pull Request",
            "from the initiative branch to main. You review and merge it.",
        ],
        agent_prompt="Create a PR",
        mock_output=MOCK_OPEN_PR,
        checkmark_msg="PR opened — awaiting your review and merge",
    )

    # ── Step 7: Complete ──────────────────────────────────────────────────
    _run_step(
        step_num=7,
        title="Complete the initiative",
        concept=[
            "After the PR is merged, the agent synthesizes Canon (authoritative",
            "docs from code), archives the specs, and records the change.",
            "Your project history grows with every initiative.",
        ],
        agent_prompt="Complete the initiative",
        mock_output=MOCK_COMPLETE_INITIATIVE,
        checkmark_msg="Initiative complete! Canon updated and specs archived.",
    )

    _completion_screen()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the interactive Cicadas tutorial")
    args = parser.parse_args()
    raise SystemExit(main(args))
