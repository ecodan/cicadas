"""
supervise.py  —  Cicadas Supervisor Agent

Wraps any Cicadas initiative execution loop with a Builder proxy.
Instead of pausing for human input at every agent interrupt, the supervisor
resolves decisions from the active spec. Only genuinely ambiguous decisions
escalate to the Builder.

Architecture
------------

    [Builder intent] ──► [Active spec] ──► [Supervisor] ──► [Agent loop]
                                                │
                                                ▼
                                        [Builder] (escalation only)

The supervisor is NOT a replacement for the Builder. It is a proxy that
enacts the Builder's pre-declared intent. Scope creep, destructive ops,
and anything outside spec boundaries always escalate.

Usage
-----

    # Run a feature branch loop with supervision:
    python supervise.py --initiative auth-system --branch feat/login

    # Dry-run: show what supervisor would decide without executing:
    python supervise.py --initiative auth-system --branch feat/login --dry-run

    # Replay a previous session's decisions:
    python supervise.py --initiative auth-system --session sessions/2026-03-22.json

File layout (written during a session)
---------------------------------------

    .cicadas/active/{initiative}/
        supervisor/
            session-{timestamp}.json    # full decision log for this run
            escalations.md              # human-readable escalation history
            authority.md                # decision authority policy (auto-generated from spec)

Requires
--------

    anthropic>=0.25  (pip install anthropic)
    Python 3.11+
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CICADAS_DIR = Path(".cicadas")
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024

# How many prior decisions to inject as context (prevents prompt bloat)
DECISION_CONTEXT_WINDOW = 10


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class Resolution(str, Enum):
    ANSWER   = "answer"    # resolved from spec — inject into agent
    ESCALATE = "escalate"  # spec doesn't cover this — block and ask Builder
    SKIP     = "skip"      # noise / rhetorical — agent should proceed as-is
    BLOCK    = "block"     # something is wrong — halt entire session


@dataclass
class Interrupt:
    """An agent pause point surfaced to the supervisor."""
    question: str
    agent_context: str        # what the agent was doing when it paused
    branch: str
    initiative: str
    timestamp: str = field(default_factory=lambda: _now())


@dataclass
class Decision:
    """A supervisor resolution of an Interrupt."""
    interrupt: Interrupt
    resolution: Resolution
    answer: str               # the injected response (empty if ESCALATE/BLOCK)
    reasoning: str            # why the supervisor decided this way
    confidence: float         # 0.0–1.0; below threshold → escalate
    escalation_note: str = "" # populated when resolution == ESCALATE


@dataclass
class Session:
    """Full state for one supervise.py run."""
    initiative: str
    branch: str
    started_at: str = field(default_factory=lambda: _now())
    decisions: list[Decision] = field(default_factory=list)
    escalations: list[Decision] = field(default_factory=list)
    completed: bool = False
    exit_reason: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _active_dir(initiative: str) -> Path:
    return CICADAS_DIR / "active" / initiative


def _supervisor_dir(initiative: str) -> Path:
    d = _active_dir(initiative) / "supervisor"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_spec_bundle(initiative: str, branch: str) -> str:
    """
    Assemble the spec bundle the supervisor uses as grounding.
    Mirrors what branch.py injects via context.md — but reads live
    active specs so the supervisor sees the latest Reflect updates.
    """
    active = _active_dir(initiative)
    parts: list[str] = []

    # 1. Canon summary if present
    canon_summary = CICADAS_DIR / "canon" / "summary.md"
    if canon_summary.exists():
        parts.append(f"# Canon Summary\n\n{canon_summary.read_text()}")

    # 2. PRD / spec files in active initiative dir
    for fname in sorted(active.glob("*.md")):
        if fname.stem in ("review", "escalations"):  # skip runtime artifacts
            continue
        parts.append(f"# {fname.stem}\n\n{fname.read_text()}")

    # 3. approach.md and tasks.md (most relevant for decision authority)
    for extra in ["approach.md", "tasks.md"]:
        p = active / extra
        if p.exists() and p.read_text() not in "\n".join(parts):
            parts.append(f"# {extra}\n\n{p.read_text()}")

    # 4. emergence-config.json (pace, building-on-ai flags, eval_placement)
    cfg = active / "emergence-config.json"
    if not cfg.exists():
        cfg = CICADAS_DIR / "drafts" / initiative / "emergence-config.json"
    if cfg.exists():
        parts.append(f"# emergence-config\n\n```json\n{cfg.read_text()}\n```")

    if not parts:
        raise FileNotFoundError(
            f"No active spec found for initiative '{initiative}'. "
            f"Run kickoff.py first or check .cicadas/active/."
        )

    return "\n\n---\n\n".join(parts)


def _load_authority_policy(initiative: str) -> str:
    """
    Load or generate the decision authority policy for this initiative.
    The policy is a simple markdown doc that classifies decision types.
    On first run it's synthesized from the spec; on subsequent runs it's
    read from disk (Builder can edit it).
    """
    policy_path = _supervisor_dir(initiative) / "authority.md"
    if policy_path.exists():
        return policy_path.read_text()

    # Default policy — conservative, escalates broadly.
    # Supervisor will generate a spec-specific one on first real run.
    return textwrap.dedent("""
        # Decision Authority Policy

        ## Autonomous (supervisor resolves without escalation)
        - File and directory naming within declared module scope
        - Choice of variable / function names
        - Import ordering and code style
        - Test fixture construction
        - Log message wording
        - Inline comment text

        ## Conditional (supervisor resolves if spec is explicit)
        - Choice between two implementation approaches both described in spec
        - Adding a dependency that is already listed in spec
        - Skipping a task marked as optional in tasks.md

        ## Always Escalate (never resolve autonomously)
        - Adding scope not described in spec (scope expansion)
        - Deleting files outside declared module scope
        - Schema or API contract changes
        - External service credentials or secrets
        - Anything involving production data
        - Merge or PR decisions
        - Any action the agent flags as irreversible
    """).strip()


# ---------------------------------------------------------------------------
# Core supervisor logic
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""
    You are the Cicadas Supervisor — an autonomous proxy for the Builder
    (the human developer) during a spec-driven development session.

    Your job is to resolve agent interrupts using the active spec as your
    sole source of authority. You do NOT invent requirements. You do NOT
    expand scope. You enact what the Builder already decided.

    ## Inputs you receive
    - SPEC BUNDLE: all active spec files for this initiative
    - AUTHORITY POLICY: which decision types you can resolve vs. must escalate
    - DECISION HISTORY: your recent decisions (for consistency)
    - INTERRUPT: the agent's question or pause point

    ## Output format (JSON, no markdown fences)
    {
      "resolution": "answer" | "escalate" | "skip" | "block",
      "answer": "<the response to inject into the agent, if resolution=answer>",
      "reasoning": "<one or two sentences explaining your decision>",
      "confidence": <float 0.0–1.0>,
      "escalation_note": "<message for the Builder, if resolution=escalate>"
    }

    ## Resolution rules
    - answer:   Spec clearly covers this. Confidence >= 0.75.
    - escalate: Spec doesn't cover this, or confidence < 0.75, or authority
                policy says always escalate.
    - skip:     The interrupt is rhetorical, a status update, or requires no
                decision (e.g. "I'm going to create file X now").
    - block:    The agent is about to do something dangerous or outside all
                bounds. Halt the session.

    ## Principles
    - When in doubt, escalate. A wrong autonomous decision is worse than
      a short human interruption.
    - Be terse. The answer field is injected directly into the agent context.
    - Never fabricate spec content. If it isn't written, escalate.
    - Preserve consistency with prior decisions in this session.
""").strip()


def _build_user_message(
    spec_bundle: str,
    authority_policy: str,
    decision_history: list[Decision],
    interrupt: Interrupt,
) -> str:
    history_text = ""
    if decision_history:
        recent = decision_history[-DECISION_CONTEXT_WINDOW:]
        lines = []
        for d in recent:
            lines.append(
                f"- Q: {d.interrupt.question[:120]}\n"
                f"  A: [{d.resolution.value}] {d.answer or d.escalation_note}"
            )
        history_text = "## Recent Decisions\n\n" + "\n".join(lines)

    return textwrap.dedent(f"""
        ## Spec Bundle

        {spec_bundle}

        ## Authority Policy

        {authority_policy}

        {history_text}

        ## Interrupt

        **Branch:** {interrupt.branch}
        **Agent context:** {interrupt.agent_context}
        **Question:** {interrupt.question}
    """).strip()


def resolve(
    interrupt: Interrupt,
    spec_bundle: str,
    authority_policy: str,
    session: Session,
    client: "anthropic.Anthropic",
    dry_run: bool = False,
) -> Decision:
    """
    Core resolution call. Returns a Decision.
    In dry_run mode, prints the prompt and returns a mock ESCALATE.
    """
    user_msg = _build_user_message(
        spec_bundle,
        authority_policy,
        session.decisions,
        interrupt,
    )

    if dry_run:
        print("\n[DRY RUN] Would send to supervisor LLM:\n")
        print(textwrap.indent(user_msg[:2000], "  "))
        return Decision(
            interrupt=interrupt,
            resolution=Resolution.ESCALATE,
            answer="",
            reasoning="Dry run — no LLM call made.",
            confidence=0.0,
            escalation_note="[DRY RUN] Manual review required.",
        )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Supervisor returned malformed JSON — safe default is escalate
        return Decision(
            interrupt=interrupt,
            resolution=Resolution.ESCALATE,
            answer="",
            reasoning=f"Supervisor returned malformed JSON: {exc}",
            confidence=0.0,
            escalation_note="Supervisor parse error — please review manually.",
        )

    return Decision(
        interrupt=interrupt,
        resolution=Resolution(data.get("resolution", "escalate")),
        answer=data.get("answer", ""),
        reasoning=data.get("reasoning", ""),
        confidence=float(data.get("confidence", 0.0)),
        escalation_note=data.get("escalation_note", ""),
    )


# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------

def _save_session(session: Session, initiative: str) -> Path:
    d = _supervisor_dir(initiative)
    ts = session.started_at.replace(":", "-").replace("+", "Z")[:19]
    path = d / f"session-{ts}.json"

    # Convert dataclasses to dicts for JSON serialisation
    def _serialise(obj):
        if isinstance(obj, Decision):
            d = asdict(obj)
            d["resolution"] = obj.resolution.value
            d["interrupt"] = asdict(obj.interrupt)
            return d
        raise TypeError(f"Not serialisable: {type(obj)}")

    data = {
        "initiative": session.initiative,
        "branch": session.branch,
        "started_at": session.started_at,
        "completed": session.completed,
        "exit_reason": session.exit_reason,
        "decisions": [_serialise(d) for d in session.decisions],
        "escalations": [_serialise(e) for e in session.escalations],
    }
    path.write_text(json.dumps(data, indent=2))
    return path


def _append_escalation_log(decision: Decision, initiative: str) -> None:
    path = _supervisor_dir(initiative) / "escalations.md"
    entry = textwrap.dedent(f"""
        ## {decision.interrupt.timestamp}

        **Branch:** {decision.interrupt.branch}
        **Question:** {decision.interrupt.question}
        **Context:** {decision.interrupt.agent_context}
        **Note:** {decision.escalation_note}

        ---
    """)
    with path.open("a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Execution loop
# ---------------------------------------------------------------------------

class SupervisorLoop:
    """
    Wraps the agent execution loop.

    In practice you would replace _mock_agent_step() with real Claude API
    calls (or subprocess calls to Claude Code). The interface contract is:

        step_result = {
            "type": "interrupt" | "complete" | "error",
            "question": str,          # if type == interrupt
            "context": str,           # if type == interrupt
            "output": str,            # if type == complete
            "error": str,             # if type == error
        }
    """

    CONFIDENCE_THRESHOLD = 0.75   # below this → escalate regardless

    def __init__(
        self,
        initiative: str,
        branch: str,
        client: "anthropic.Anthropic",
        dry_run: bool = False,
        max_iterations: int = 200,
    ):
        self.initiative = initiative
        self.branch = branch
        self.client = client
        self.dry_run = dry_run
        self.max_iterations = max_iterations

        self.session = Session(initiative=initiative, branch=branch)
        self.spec_bundle = _load_spec_bundle(initiative, branch)
        self.authority_policy = _load_authority_policy(initiative)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, initial_prompt: str) -> Session:
        """
        Main loop. Returns the completed Session.

        Replace _mock_agent_step with your real agent call.
        """
        print(f"\n[supervisor] Starting session: {self.initiative} / {self.branch}")
        print(f"[supervisor] Spec loaded ({len(self.spec_bundle)} chars)")
        print(f"[supervisor] Max iterations: {self.max_iterations}\n")

        agent_message = initial_prompt
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            step = self._agent_step(agent_message)

            if step["type"] == "complete":
                print(f"\n[supervisor] Agent completed after {iteration} steps.")
                self.session.completed = True
                self.session.exit_reason = "agent_complete"
                break

            if step["type"] == "error":
                print(f"\n[supervisor] Agent error: {step['error']}")
                self.session.exit_reason = f"agent_error: {step['error']}"
                break

            if step["type"] == "interrupt":
                interrupt = Interrupt(
                    question=step["question"],
                    agent_context=step.get("context", ""),
                    branch=self.branch,
                    initiative=self.initiative,
                )

                decision = self._handle_interrupt(interrupt)

                if decision.resolution == Resolution.BLOCK:
                    print(f"\n[supervisor] BLOCK — halting session.")
                    print(f"  Reason: {decision.reasoning}")
                    self.session.exit_reason = f"block: {decision.reasoning}"
                    break

                if decision.resolution == Resolution.ESCALATE:
                    # Surface to Builder, wait for response
                    human_answer = self._escalate_to_builder(decision)
                    agent_message = human_answer
                else:
                    agent_message = decision.answer or ""

            if iteration == self.max_iterations:
                print(f"\n[supervisor] Max iterations ({self.max_iterations}) reached.")
                self.session.exit_reason = "max_iterations"

        self._finalise_session()
        return self.session

    # ------------------------------------------------------------------
    # Interrupt handling
    # ------------------------------------------------------------------

    def _handle_interrupt(self, interrupt: Interrupt) -> Decision:
        decision = resolve(
            interrupt=interrupt,
            spec_bundle=self.spec_bundle,
            authority_policy=self.authority_policy,
            session=self.session,
            client=self.client,
            dry_run=self.dry_run,
        )

        # Enforce confidence threshold
        if (
            decision.resolution == Resolution.ANSWER
            and decision.confidence < self.CONFIDENCE_THRESHOLD
        ):
            decision.resolution = Resolution.ESCALATE
            decision.escalation_note = (
                f"Low confidence ({decision.confidence:.2f}) — "
                f"original reasoning: {decision.reasoning}"
            )

        self.session.decisions.append(decision)

        symbol = {
            Resolution.ANSWER:   "✓",
            Resolution.ESCALATE: "↑",
            Resolution.SKIP:     "~",
            Resolution.BLOCK:    "✗",
        }[decision.resolution]

        print(
            f"  [{symbol}] {decision.resolution.value.upper():8s} "
            f"(conf={decision.confidence:.2f})  "
            f"{interrupt.question[:80]}"
        )

        if decision.resolution == Resolution.ESCALATE:
            self.session.escalations.append(decision)
            _append_escalation_log(decision, self.initiative)

        return decision

    def _escalate_to_builder(self, decision: Decision) -> str:
        """
        Pause and ask the Builder. Writes to escalations.md first so
        the Builder has persistent context if they step away.
        """
        print(f"\n{'─'*60}")
        print(f"  ESCALATION — Builder input required")
        print(f"{'─'*60}")
        print(f"  Question:  {decision.interrupt.question}")
        print(f"  Context:   {decision.interrupt.agent_context}")
        if decision.escalation_note:
            print(f"  Note:      {decision.escalation_note}")
        print(f"{'─'*60}")

        if self.dry_run:
            return "[DRY RUN] No input collected."

        try:
            answer = input("  Builder > ").strip()
        except (EOFError, KeyboardInterrupt):
            answer = ""

        # Back-fill the answer into the decision log
        decision.answer = answer
        return answer

    # ------------------------------------------------------------------
    # Agent step (replace with real agent integration)
    # ------------------------------------------------------------------

    def _agent_step(self, message: str) -> dict:
        """
        Stub. Replace this with your real agent call:

        Option A — subprocess Claude Code:
            result = subprocess.run(
                ["claude", "--print", message],
                capture_output=True, text=True
            )
            return self._parse_claude_code_output(result.stdout)

        Option B — Anthropic API with tool use:
            response = self.client.messages.create(...)
            return self._parse_api_response(response)

        Option C — OpenClaw-style loop:
            return openclaw_client.step(message)

        The contract:
            {"type": "complete", "output": str}
            {"type": "interrupt", "question": str, "context": str}
            {"type": "error",     "error": str}
        """
        raise NotImplementedError(
            "Replace _agent_step() with your real agent integration.\n"
            "See docstring for options."
        )

    # ------------------------------------------------------------------
    # Finalisation
    # ------------------------------------------------------------------

    def _finalise_session(self) -> None:
        path = _save_session(self.session, self.initiative)
        total = len(self.session.decisions)
        escalated = len(self.session.escalations)
        autonomous = total - escalated

        print(f"\n[supervisor] Session saved → {path}")
        print(f"[supervisor] Decisions: {total} total, "
              f"{autonomous} autonomous, {escalated} escalated")

        # Append token log entry (null entry — agent self-reports real counts)
        # Matches the tokens.py convention: source=unavailable at boundary
        try:
            from tokens import append_entry  # type: ignore
            append_entry(
                initiative=self.initiative,
                phase="supervise",
                subphase=self.branch,
                input_tokens=None,
                output_tokens=None,
                cached_tokens=None,
                source="unavailable",
            )
        except ImportError:
            pass  # tokens.py not on path — skip silently


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Cicadas Supervisor — autonomous Builder proxy for agent loops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python supervise.py --initiative auth-system --branch feat/login
              python supervise.py --initiative auth-system --branch feat/login --dry-run
              python supervise.py --initiative auth-system --branch feat/login \\
                                  --prompt "Implement all tasks in tasks.md"
        """),
    )
    p.add_argument("--initiative", required=True, help="Initiative name (must exist in .cicadas/active/)")
    p.add_argument("--branch",     required=True, help="Feature branch being executed")
    p.add_argument("--prompt",     default="Implement all incomplete tasks in tasks.md according to the spec.",
                   help="Initial prompt to send to the agent")
    p.add_argument("--dry-run",    action="store_true", help="Show prompts without making LLM calls")
    p.add_argument("--max-iter",   type=int, default=200, help="Hard iteration cap (default 200)")
    p.add_argument("--confidence", type=float, default=0.75,
                   help="Minimum confidence for autonomous resolution (default 0.75)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package not found. Run: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    loop = SupervisorLoop(
        initiative=args.initiative,
        branch=args.branch,
        client=client,
        dry_run=args.dry_run,
        max_iterations=args.max_iter,
    )
    loop.CONFIDENCE_THRESHOLD = args.confidence

    session = loop.run(args.prompt)

    if session.completed:
        print("\n[supervisor] ✓ Initiative branch complete.")
        sys.exit(0)
    else:
        print(f"\n[supervisor] ✗ Session ended: {session.exit_reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()