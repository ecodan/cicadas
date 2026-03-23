
---
next_section: 'complete'
---

# Tech Design: auto-cicadas

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
- [x] Architecture Decisions (ADRs)
## Project / Module Structure

`cicadas-chorus` is a standalone Python package in its own repo. The structure below shows only what this initiative creates — the Cicadas workspace (separate repo) is unchanged except for one addition to `SKILL.md`.

```
cicadas-chorus/                          # separate repo / pip package
├── pyproject.toml                       # package metadata; entry point: chorus = chorus.cli:main
├── README.md
├── src/
│   └── chorus/
│       ├── __init__.py
│       ├── cli.py                       # entry point: `chorus run`, `chorus start`, `chorus config`
│       ├── supervisor.py                # core loop: iterate → route → resolve → log
│       ├── resolver.py                  # classify → shallow path / deep path (party mode)
│       ├── party.py                     # Phase 1 reviewers, Phase 2 synthesis, Phase 3 consensus
│       ├── context.py                   # workspace reader: spec bundle, intent summary, handoff write
│       ├── authority.py                 # authority policy: load, evaluate, annotate
│       ├── session.py                   # session file: create, append decision, write terminal condition
│       ├── escalation.py                # escalation transport interface + terminal implementation
│       ├── token_log.py                 # mirrors tokens.py API; writes supervisor/tokens.json
│       ├── eval_log.py                  # JSONL append; writes supervisor/eval-samples/{session_id}.jsonl
│       ├── config.py                    # load ~/.config/chorus/config.json + workspace override
│       ├── plugins.py                   # entry-point discovery + explicit module-path loader
│       ├── models.py                    # dataclasses: Interrupt, Decision, AgentResult, Session, etc.
│       └── agents/
│           ├── base.py                  # CodingAgentInterface ABC + PermissionDecision
│           └── claude_code.py           # ClaudeCodeAdapter: claude_agent_sdk wiring
└── tests/
    ├── base.py                          # CicadasChorusTest: temp workspace, mock agent, mock LiteLLM
    ├── test_supervisor.py               # core loop: routing, terminal conditions, max_iterations
    ├── test_resolver.py                 # shallow path, deep path, confidence threshold, skip
    ├── test_party.py                    # phase 1/2/3, consensus, retry, no-consensus escalate
    ├── test_context.py                  # workspace reads, handoff write, supervisor_dir resolution
    ├── test_authority.py                # pre-flight gate, tier classification, annotation load
    ├── test_session.py                  # append durability, crash recovery, KeyboardInterrupt flush
    ├── test_eval_log.py                 # JSONL append, --no-eval-log suppression, write failure tolerance
    └── test_claude_code_adapter.py      # AskUserQuestion → on_interrupt, PreToolUse → on_tool_gate
```

**In the Cicadas repo** (one change only):

```
src/cicadas/
└── SKILL.md    # [MODIFIED] add "Implement hands-free" Builder command:
                #   "implement hands-free" → requires chorus installed;
                #   runs: chorus run --workspace {cwd}
```

**Workspace state** (written by chorus at runtime — neither repo):

```
.cicadas/{drafts|active}/{initiative}/supervisor/
    ├── chorus-handoff.md          # written by chorus before each query(); read by agent at start
    ├── session-{timestamp}.json   # append-per-decision log
    ├── escalations.md             # human-readable escalation history
    ├── authority.md               # decision authority policy (generated + annotatable)
    └── tokens.json                # per-session token usage log
```

**Key structural decisions:**
- `agents/` is a subpackage, not a flat module — future adapters (`cursor.py`, `rovo_dev.py`) drop in without touching any other file.
- `supervisor.py` imports only `models`, `session`, `escalation`, and `agents.base` — it never imports `resolver`, `party`, or `claude_code` directly. Those are injected at construction. This makes the core loop testable with mocks.
- `context.py` owns all filesystem reads from the workspace. No other module reads `.cicadas/` directly — single point of coupling to the Cicadas schema.
- `cli.py` is thin: parse args → load config → instantiate Supervisor → call `run()`. No business logic.

---

## Architecture Decisions (ADRs)
- [x] Data Models
- [x] API & Interface Design
- [x] Implementation Patterns & Conventions
- [x] Security & Performance
- [x] Implementation Sequence

---

## Architecture Decisions (ADRs)

### ADR-1: Separate Package (`cicadas-chorus`) Rather Than Cicadas Script

**Decision:** `cicadas-chorus` is a standalone pip package in its own repository, not a script inside the Cicadas skill directory. It is installed independently and points at workspaces where Cicadas is already installed.

**Rationale:** The supervisor has its own dependency graph (`litellm`, `claude_agent_sdk`), its own configuration namespace, and its own release cadence. Embedding it in Cicadas would bloat the skill installation for the majority of users who don't need autonomous supervision, and would couple the supervisor's dependency updates to Cicadas's distribution model (bash `install.sh` + `requirements.txt`). A separate package can be versioned, published to PyPI, and upgraded independently. Cicadas remains a lightweight, zero-dependency skill.

**Affects:** `pyproject.toml`, `install.sh` (unchanged — Cicadas install is unaffected), `SKILL.md` addition (`implement hands-free` command), all chorus module imports.

---

### ADR-2: LiteLLM for All Supervisor LLM Calls

**Decision:** All supervisor LLM calls (classifier, party reviewers, synthesis, consensus) go through `litellm.completion()`. No direct `anthropic` SDK import anywhere in chorus core.

**Rationale:** The supervisor must work with whichever provider the user has configured — Anthropic, OpenAI, Gemini, Ollama, or a custom endpoint like Atlassian AIGateway. LiteLLM provides a single unified `completion()` call across all of these with a model-string prefix convention (`anthropic/`, `openai/`, `ollama/`, custom). It also provides `usage` data (input/output/cached tokens) on every response, which feeds directly into token logging. Direct Anthropic SDK would create a hard provider lock and require chorus to add conditionals for every future provider. LiteLLM's `CustomLLM` extension point covers providers not natively supported (AIGateway, enterprise proxies) without changing chorus core.

**Affects:** `supervisor.py`, `resolver.py`, `party.py`, `config.py`, `plugins.py`, `token_log.py`, `pyproject.toml`.

---

### ADR-3: `CodingAgentInterface` ABC with `on_interrupt` Callback

**Decision:** The coding agent is abstracted behind a `CodingAgentInterface` ABC with two methods: `run()` and `resume()`. Both accept an `on_interrupt: Callable[[Interrupt], Awaitable[str]]` callback. The interrupt signal mechanism — how an agent signals it needs supervisor input — is the responsibility of each adapter, not the core loop.

**Rationale:** `AskUserQuestion` (the natural Claude Code interrupt signal) is a Claude-specific tool. If it were wired directly into the supervisor loop, every other agent adapter would need to emulate or wrap it. By pushing interrupt detection into each adapter, chorus core only knows about `Interrupt(question, context)` — a provider-neutral dataclass. `ClaudeCodeAdapter` maps `AskUserQuestion` → `on_interrupt`; a future `CursorAdapter` could map a different event. The core loop is unaffected. This also means `claude_agent_sdk` is never imported outside `ClaudeCodeAdapter`, which keeps it an optional dep that only activates when the Claude Code adapter is in use.

**Affects:** `agents/base.py` (ABC definition), `agents/claude_code.py` (adapter), `supervisor.py` (only uses ABC), `models.py` (Interrupt, AgentResult dataclasses).

---

### ADR-4: `chorus-handoff.md` as the Context Bridge

**Decision:** Before each `query()` call, chorus writes a `chorus-handoff.md` to the supervisor namespace. The file contains: the synthesized intent summary, recent decisions, authority policy summary, current task focus, and protocol instruction (`"Use AskUserQuestion for ALL questions — never print questions to stdout"`). The agent reads it at session start via the prompt. Agent → chorus context flows via natural workspace artifacts (checked `tasks.md` items, `git log`, `ResultMessage` metadata).

**Rationale:** The agent's context window is reset on each `query()` call. Without an injection mechanism, the agent would have no awareness of prior decisions, authority constraints, or the supervisor protocol. `chorus-handoff.md` is the minimal, filesystem-native solution: it requires no new agent-side coupling, works identically for every adapter, and is human-readable for debugging. The reverse flow (agent → chorus) is intentionally zero-coupling: chorus reads standard workspace artifacts that the agent would produce anyway. No chorus-specific writes are required from the agent.

**Affects:** `context.py` (write), `agents/base.py` (prompt prepends path), `session.py` (decision log feeds handoff content).

---

### ADR-5: `supervisor_dir()` Resolution Mirrors Cicadas Precedence

**Decision:** Chorus writes all supervisor artifacts to `.cicadas/{drafts|active}/{initiative}/supervisor/*`, where `active/` takes precedence over `drafts/`. This is encapsulated in a single `supervisor_dir(workspace, initiative) → Path` function in `context.py`.

**Rationale:** Cicadas uses the same `active/`-over-`drafts/` precedence everywhere. Chorus doesn't know — and shouldn't have to know — what lifecycle stage an initiative is in. By mirroring Cicadas's own resolution rule, supervisor artifacts always land in the right place: in `drafts/` during emergence (before kickoff), in `active/` during execution (after kickoff). A single function encapsulates this rule; all other chorus modules call `supervisor_dir()` without caring about lifecycle stage. This also means session logs, escalations, authority policy, and tokens always travel with the initiative as Cicadas promotes it from `drafts/` to `active/`.

**Affects:** `context.py` (owns `supervisor_dir()`), all modules that write to supervisor namespace import it from `context.py`.

---

### ADR-6: Party Mode via `ThreadPoolExecutor` — No Orchestration Framework

**Decision:** Party mode (deep resolution path) is implemented as three parallel `litellm.completion()` calls via `ThreadPoolExecutor`, followed by a synthesis call, followed by a consensus vote. No LangGraph, CrewAI, asyncio, or other multi-agent framework is used.

**Rationale:** `litellm.completion()` is a synchronous blocking HTTP call — running three of them in a thread pool is exactly the right tool for I/O-bound parallelism. `ThreadPoolExecutor` is stdlib, produces readable synchronous-style code, and generates normal stack traces. `asyncio.gather` would require wrapping sync calls in an event loop for no benefit. LangGraph/CrewAI would add hundreds of transitive dependencies over what is a three-call fan-out/fan-in. The main supervisor loop stays synchronous end-to-end; asyncio is confined to the agent SDK adapter layer where it is genuinely required.

**Affects:** `party.py` (all of it), `pyproject.toml` (explicitly no langchain/crewai/langgraph deps).

---

### ADR-7: Two-Layer Plugin Discovery

**Decision:** Plugin discovery uses two layers: (1) `importlib.metadata.entry_points(group="cicadas.plugins")` for pip-installed packages, and (2) an explicit `plugins` array in `supervisor-config.json` for local/non-pip modules. Both layers are merged at startup. Each plugin exposes a `register(registry: CicadasPluginRegistry)` function that can push LLM providers into LiteLLM and coding agent types into the factory map.

**Rationale:** Enterprise users (e.g., Atlassian) need to distribute proprietary LLM adapters that cannot be published to public PyPI. Local module paths in config cover this case without requiring a private registry or pip install. Public plugins (community agent adapters, LLM integrations) use the standard `entry_points` mechanism for zero-configuration discovery. The two-layer design covers both without privileging either. The `CicadasPluginRegistry` protocol is the single extension point — plugins don't call LiteLLM or the factory map directly, which keeps chorus in control of when and how plugins are loaded.

**Affects:** `plugins.py` (all of it), `config.py` (loads plugin paths), `agents/base.py` (factory map), `pyproject.toml` (entry_points group definition).

---

### ADR-8: Cicadas as a Hard Prerequisite; Skill Invocation as the Primary Execution Model

**Decision:** Cicadas must be installed and initialized in the target workspace before chorus can run. `chorus run` performs a pre-flight check for `.cicadas/registry.json`; if absent, it exits with a clear error. Nearly every task chorus hands to the agent is framed as a Cicadas skill command — `kickoff`, `branch`, `reflect`, `archive`, etc. Chorus does not prompt agents to perform ad-hoc file mutations; it prompts them to drive the Cicadas lifecycle.

**Rationale:** Chorus is a supervisor for Cicadas-driven development, not a general-purpose coding agent driver. The entire decision model (interrupt classification, authority policy, party mode reviewers) is grounded in Cicadas concepts — initiatives, specs, tasks, emergence, lifecycle stages. Without Cicadas in the workspace, chorus has no state to read and no lifecycle to supervise. Making this a hard pre-flight check (rather than a soft warning) prevents silent failures where chorus runs against an uninitialized workspace and produces nonsensical decisions. Framing agent prompts as Cicadas skill invocations also constrains the agent's action space — it reduces ambiguity about what the agent should do next and aligns the agent's output with the structured state that chorus reads back.

**Affects:** `cli.py` (pre-flight check), `context.py` (registry read as first operation), `supervisor.py` (handoff prompts reference Cicadas commands), all test fixtures (require `.cicadas/` setup).

---

## Data Models

All models live in `models.py` as stdlib `dataclasses`. JSON serialisation is manual (`asdict()` + `json.dump`). No Pydantic.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Agent ↔ Chorus boundary
# ---------------------------------------------------------------------------

@dataclass
class Interrupt:
    """An agent-initiated question that requires supervisor resolution."""
    question: str          # the question text the agent wants answered
    context: str           # raw tool input or surrounding context (for classifiers)


@dataclass
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None


@dataclass
class AgentResult:
    """Terminal result returned by CodingAgentInterface.run() / resume()."""
    status: Literal["completed", "error", "max_turns"]
    session_id: str | None = None        # stored for resume(); from claude_agent_sdk ResultMessage
    cost_usd: float | None = None
    usage: TokenUsage | None = None
    error_message: str | None = None     # populated on status="error"


# ---------------------------------------------------------------------------
# Supervisor resolution
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    """A single resolved interrupt, appended to the session file."""
    timestamp: str                        # ISO-8601 UTC
    question: str
    answer: str
    resolution_path: Literal["shallow", "deep", "escalated", "pre-flight-blocked"]
    confidence: float | None = None       # classifier confidence score (shallow path)
    reviewers_used: list[str] = field(default_factory=list)   # party mode only
    authority_tier: str | None = None     # "always_escalate" | "chorus_decides" | "agent_decides"
    notes: str | None = None


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@dataclass
class Session:
    """Represents one chorus run against one initiative."""
    session_id: str                       # chorus-generated UUID (distinct from agent session_id)
    initiative: str
    workspace: str                        # absolute path, stringified
    started_at: str                       # ISO-8601 UTC
    intent_summary: str                   # synthesised once at session start; frozen
    decisions: list[Decision] = field(default_factory=list)
    agent_session_id: str | None = None   # from AgentResult.session_id; populated after first run()
    terminal_condition: Literal[
        "completed", "requires_human_input", "unrecoverable_error"
    ] | None = None
    terminal_reason: str | None = None    # human-readable explanation
    ended_at: str | None = None


# ---------------------------------------------------------------------------
# Authority policy
# ---------------------------------------------------------------------------

@dataclass
class AuthorityRule:
    """One entry in the authority policy."""
    pattern: str                          # glob or keyword pattern matched against question text
    tier: Literal["always_escalate", "chorus_decides", "agent_decides"]
    rationale: str | None = None


@dataclass
class AuthorityPolicy:
    """Loaded from supervisor/authority.md front-matter + rule list."""
    rules: list[AuthorityRule] = field(default_factory=list)
    default_tier: Literal["chorus_decides", "always_escalate"] = "chorus_decides"
```

**Key field decisions:**

- `Decision.resolution_path` — four values cover all paths: shallow (classifier confident), deep (party mode), escalated (human), pre-flight-blocked (authority policy intercepted before classification). Stored so sessions can be audited for escalation rate and party-mode frequency.
- `Session.intent_summary` is frozen at session start and stored in the session file. It is passed verbatim to every LLM call. Never re-synthesised mid-session — prevents intent drift across interrupts.
- `Session.agent_session_id` vs `Session.session_id` — chorus generates its own UUID for the chorus session; `agent_session_id` is whatever the coding agent SDK returns (used for agent-level resume, not chorus-level resume).
- `TokenUsage` is a standalone dataclass, not inlined into `AgentResult`, because it is also used by `token_log.py` when appending supervisor LLM call entries.
- `AuthorityPolicy.default_tier` defaults to `"chorus_decides"` — unmatched questions fall to chorus resolution, not automatic escalation. This keeps the supervisor useful without requiring an exhaustive authority policy.

### Eval Sample Model

```python
@dataclass
class PartyOutputs:
    reviewers: list[str]       # one string per reviewer (analyst, ux, architect)
    synthesis: str
    consensus: Literal["agree", "disagree", "retry"]


@dataclass
class EvalSample:
    """Captured after every resolved interrupt. label=None until human-annotated."""
    sample_id: str                        # UUID, chorus-generated
    captured_at: str                      # ISO-8601 UTC
    initiative: str
    question: str
    context: str
    resolution_path: Literal["shallow", "deep", "escalated", "pre-flight-blocked"]
    classifier_output: dict               # {"confidence": float, "tier": str}
    party_outputs: PartyOutputs | None    # None on shallow/escalated/pre-flight paths
    final_answer: str
    label: str | None = None              # null at capture; filled by human annotator
```

Written as JSONL to `supervisor/eval-samples/{session_id}.jsonl` by `eval_log.py`.

### Modified Models

No existing Cicadas models are modified. Chorus is a separate package; it reads Cicadas filesystem schema directly (JSON files, markdown) without importing any Cicadas Python classes.

---

## API & Interface Design

### CLI Commands

```
chorus run [--workspace PATH] [--initiative NAME] [--agent TYPE]
```
Primary entry point. Detects workspace state and does the right thing:
- If an open session exists → resumes it (agent-level resume via stored `agent_session_id`)
- If initiative is in `drafts/` → starts emergence supervision
- If initiative is in `active/` → starts execution supervision
- `--workspace` defaults to `cwd`; `--initiative` defaults to the single active initiative (errors if 0 or >1)
- `--agent` overrides the agent type from config (e.g. `claude-code`)

```
chorus start --initiative NAME [--workspace PATH] [--agent TYPE] [--force]
```
Always starts a new session. Errors if an open session already exists unless `--force`.

```
chorus config [--global] [show | set KEY VALUE | edit]
```
View or modify `agents.json`. `--global` targets `~/.config/chorus/agents.json`; default targets `.cicadas/agents.json` in the current workspace. `edit` opens in `$EDITOR`.

```
chorus status [--workspace PATH]
```
Prints current session state (open/closed, terminal condition, decision count, last interrupt).

---

### `CodingAgentInterface` ABC (`agents/base.py`)

```python
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from pathlib import Path
from models import AgentResult, Interrupt


class CodingAgentInterface(ABC):

    @abstractmethod
    async def run(
        self,
        prompt: str,
        workspace: Path,
        on_interrupt: Callable[[Interrupt], Awaitable[str]],
        on_tool_gate: Callable[[str, dict], Awaitable[bool]] | None = None,
    ) -> AgentResult:
        """Start a new agent session. Returns when agent reaches a terminal state."""

    @abstractmethod
    async def resume(
        self,
        session_id: str,
        context: str,
        on_interrupt: Callable[[Interrupt], Awaitable[str]],
        on_tool_gate: Callable[[str, dict], Awaitable[bool]] | None = None,
    ) -> AgentResult:
        """Resume an existing agent session by SDK session_id."""
```

**Callback contracts:**
- `on_interrupt(interrupt) → str` — supervisor resolves the question and returns the answer string. The adapter injects this answer back into the agent (e.g., as the `AskUserQuestion` response).
- `on_tool_gate(tool_name, input_data) → bool` — returns `True` to allow, `False` to deny. Called for every tool use when authority policy restricts the agent's action space. Optional; pass `None` to allow all tools.

---

### `EscalationTransport` Interface (`escalation.py`)

```python
from abc import ABC, abstractmethod
from models import Session


class EscalationTransport(ABC):

    @abstractmethod
    async def send(self, question: str, context: str, session: Session) -> str:
        """Send escalation to a human and return their answer."""


class TerminalEscalation(EscalationTransport):
    """Default implementation: blocks on input() in the terminal."""

    async def send(self, question: str, context: str, session: Session) -> str:
        print(f"\n[ESCALATION] {question}\nContext: {context}\n")
        return input("Your answer: ").strip()
```

Future implementations (Slack, email, webhook) implement `EscalationTransport` and register via the plugin system.

---

### Configuration Schema

#### `agents.json` (global or workspace)

```json
{
  "_models": {
    "<model_id>": {
      "model_provider": "anthropic | openai | vertex_ai | ollama | <custom>",
      "model_family": "claude | gpt | gemini | qwen | <other>",
      "model_version": "<litellm-compatible model string>",
      "model_parameters": {
        "temperature": 0.3,
        "max_tokens": 4096
      },
      "provider_auth": {
        "api_key": "<key>"
      }
    }
  },
  "<agent_name>": {
    "model_id": "<model_id>",
    "prompt": "<prompt_name>:<version>",
    "model_parameters": {
      "temperature": 0.2
    },
    "custom_configs": {
      "logging": {
        "enabled": true,
        "mode": "jsonl_file",
        "file_path": "./logs/chorus.jsonl",
        "level": "standard"
      }
    }
  },
  "_coding_agents": {
    "<agent_id>": {
      "type": "claude_code | cursor | <plugin-registered>",
      "options": {}
    }
  }
}
```

**Named agents chorus defines** (each references a `model_id`):

| Agent name | Role |
|------------|------|
| `intent_synthesizer` | Synthesises the frozen intent summary at session start |
| `classifier` | Classifies interrupts: shallow confidence score + tier |
| `reviewer_analyst` | Party mode Phase 1 — PRD/acceptance-criteria perspective |
| `reviewer_ux` | Party mode Phase 1 — UX/workflow perspective |
| `reviewer_architect` | Party mode Phase 1 — architecture/risk perspective |
| `synthesizer` | Party mode Phase 2 — merges reviewer outputs into a single answer |
| `consensus` | Party mode Phase 3 — votes on synthesised answer; triggers retry or escalate |

#### `supervisor-config.json` (workspace, chorus-specific overrides)

```json
{
  "max_iterations": 50,
  "confidence_threshold": 0.85,
  "plugins": [
    "path/to/local_plugin.py"
  ]
}
```

#### Prompt files (`prompts/<name>.toml`)

```toml
[v2]
system_prompt = '''You are a chorus supervisor classifier...'''
user_prompt = '''
Initiative intent: {intent_summary}
Question: {question}
Context: {context}

Classify the above interrupt...
'''

[v1]
system_prompt = '''...'''
user_prompt = '''...'''
```

`{placeholder}` substitution is applied by `PromptLoader` before the prompt is passed to `litellm.completion()`.

---

### `ConfigManager` and `PromptLoader`

```python
class ConfigManager:
    def __init__(self, workspace: Path) -> None: ...

    def load_agent(self, agent_name: str) -> dict:
        """Merge global + workspace agents.json; resolve model_id ref; return merged agent config."""

    def load_model(self, model_id: str) -> dict:
        """Return base model config dict for model_id."""

    def load_coding_agent(self, agent_id: str) -> dict:
        """Return _coding_agents entry for agent_id."""


class PromptLoader:
    def __init__(self, prompts_dir: Path) -> None: ...

    def load_prompt(self, prompt_name: str, version: str = "latest") -> dict:
        """
        Load prompt by name and version from prompts/<name>.toml.
        Returns dict with 'system_prompt' and/or 'user_prompt' keys.
        'latest' resolves to the highest [vN] section in the file.
        """

    def render(self, prompt: dict, **kwargs: str) -> dict:
        """Apply {placeholder} substitution to system_prompt and user_prompt."""
```

Both classes are instantiated once in `cli.py` and injected into modules that need them. No global singletons.

---

### Backward Compatibility

Chorus is a new package with no existing API consumers. No migration concerns.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|------------|---------|
| Functions / methods | `snake_case` | `resolve_interrupt()` |
| Classes | `PascalCase` | `ClaudeCodeAdapter` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_CONFIDENCE_THRESHOLD` |
| Files / modules | `snake_case.py` | `token_log.py` |
| CLI flags | `--kebab-case` | `--workspace`, `--initiative` |
| Config keys | `snake_case` | `max_iterations`, `model_provider` |
| Prompt files | `snake_case.toml` | `classifier.toml`, `reviewer_analyst.toml` |

---

### Logging Pattern

All modules import a shared logger from `log_config.py`. No module creates its own logger independently.

```python
# log_config.py
import logging
import sys

LOG_FORMAT = "%(asctime)s [%(levelname)s] <%(filename)s:%(lineno)s> %(message)s"
LOGGER_NAME = "chorus"


def create_logger(level: int = logging.INFO, log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger  # already initialised; idempotent
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    if log_file:
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)
    logger.setLevel(level)
    return logger


# In every module:
import logging
logger = logging.getLogger("chorus")
```

`create_logger()` is called once in `cli.py` at startup. All other modules call `logging.getLogger("chorus")` — they get the already-configured instance.

---

### Error Handling Pattern

```python
# Supervisor loop — let known exception types surface with context
try:
    result = await agent.run(prompt, workspace, on_interrupt=resolve)
except SomeAgentError as e:
    logger.error("Agent error during run: %s", e)
    session.write_terminal("unrecoverable_error", reason=str(e))
    raise SystemExit(1)

# I/O helpers — absorb OSError, log warning, never raise
def _atomic_write(path: Path, data: str) -> None:
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(data)
        tmp.replace(path)   # atomic on POSIX
    except OSError as e:
        logger.warning("Could not write %s: %s", path, e)
```

**Rules:**
- Never swallow exceptions silently in the supervisor loop — log at `ERROR` and write a terminal condition.
- I/O helpers (session append, token log, handoff write) absorb `OSError` with a `WARNING` log — a failed log write must not kill the supervisor.
- `KeyboardInterrupt` is caught at the top of `supervisor.run()`, writes terminal condition `requires_human_input` / reason `"interrupted"`, flushes session, then re-raises cleanly.
- All imports at top of file unless there is a strong reason for deferred import (e.g., optional plugin module loaded by path).

---

### Atomic File Write Pattern

Used by `session.py` and `token_log.py` for every append operation.

```python
import json
from pathlib import Path


def _atomic_json_append(path: Path, new_entry: dict) -> None:
    """Read → extend → write-then-rename. Crash-safe append."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing: list[dict] = json.loads(path.read_text()) if path.exists() else []
    except (json.JSONDecodeError, OSError):
        existing = []
    existing.append(new_entry)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(existing, indent=2))
    tmp.replace(path)
```

---

### LiteLLM Call Pattern

Every supervisor LLM call follows this structure. Token counts are always captured for `token_log.py`.

```python
import litellm
from dataclasses import asdict


def _call_llm(
    agent_cfg: dict,
    prompt: dict,           # rendered dict with system_prompt / user_prompt
    *,
    extra_kwargs: dict | None = None,
) -> tuple[str, dict]:      # (content, usage dict)
    messages: list[dict] = []
    if system := prompt.get("system_prompt"):
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt["user_prompt"]})

    response = litellm.completion(
        model=agent_cfg["model_version"],
        messages=messages,
        temperature=agent_cfg["model_parameters"].get("temperature", 0.3),
        max_tokens=agent_cfg["model_parameters"].get("max_tokens", 4096),
        **(extra_kwargs or {}),
    )
    content: str = response.choices[0].message.content
    usage: dict = {
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "cached_tokens": getattr(response.usage, "cache_read_input_tokens", None),
    }
    return content, usage
```

---

### Concurrency Pattern

The main supervisor loop is **synchronous throughout**. Two concurrency mechanisms are used, each scoped to where it's actually needed:

**Party mode — `ThreadPoolExecutor`**

`litellm.completion()` is a synchronous blocking HTTP call. Three of them in a thread pool is the right tool — no event loop involved.

```python
# party.py
from concurrent.futures import ThreadPoolExecutor


def run_reviewers(prompts: list[dict], agent_cfgs: list[dict]) -> list[str]:
    """Fan-out: call all reviewers in parallel, return their outputs."""
    with ThreadPoolExecutor(max_workers=len(prompts)) as ex:
        return list(ex.map(_call_llm, agent_cfgs, prompts))
```

**Agent SDK — `asyncio` confined to adapter + `cli.py`**

`claude_agent_sdk` is async — not our choice. `CodingAgentInterface.run()` and `resume()` are declared `async` to match. `cli.py` drives them with a single `asyncio.run()` call. Nothing outside `agents/` and `cli.py` is async.

```python
# cli.py
import asyncio
result: AgentResult = asyncio.run(agent.run(prompt, workspace, on_interrupt=resolve))
```

**Rules:**
- `asyncio` is confined to `agents/claude_code.py` and the single `asyncio.run()` call in `cli.py`. No other module imports or uses asyncio.
- Party mode uses `ThreadPoolExecutor` — never `asyncio.gather`.
- No `async def` outside `agents/` — keeps terminal I/O, session writes, and escalation `input()` straightforward.

---

### Testing Pattern

```python
# tests/base.py — all test classes inherit from CicadasChorusTest
import unittest
import tempfile
import subprocess
from pathlib import Path


class CicadasChorusTest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmpdir.name)
        # Minimal .cicadas/ structure
        (self.workspace / ".cicadas").mkdir()
        (self.workspace / ".cicadas" / "registry.json").write_text('{"initiatives": {}}')

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def init_git(self) -> None:
        subprocess.run(["git", "init"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"],
                       cwd=self.workspace, check=True, capture_output=True)
```

**Coverage expectations:** 80%+ on non-trivial logic; 100% on session durability and authority pre-flight paths.

**Mocking strategy:**
- Mock `litellm.completion` at the module boundary — never reach the network in tests.
- Mock `CodingAgentInterface` with a `MockAgent` that returns a preset `AgentResult` and calls `on_interrupt` for a preset list of questions.
- Real filesystem for all session, token log, context, and authority tests — no mocking of file I/O.

---

## Overview & Context

`cicadas-chorus` (`chorus` CLI) is a **standalone Python package** — separate from the Cicadas skill — that wraps the Cicadas inner loop with an autonomous supervisor. It is installed independently (`pip install cicadas-chorus`), points at a workspace where Cicadas is already installed, and drives a coding agent against that workspace. It never calls Cicadas scripts directly; all Cicadas lifecycle operations are performed by the agent.

The design follows four architectural principles:

1. **Read-only Cicadas consumer** — chorus reads `.cicadas/` state (registry, specs, config) directly from the workspace filesystem. It writes only to its own supervisor namespace: `.cicadas/{drafts|active}/{initiative}/supervisor/*`. All state mutations (kickoff, branch, archive, etc.) go through the agent. This eliminates interface contract fragility — Cicadas schema changes don't break chorus; only the filesystem read schema is the contract.
2. **Agent-mediated execution** — the coding agent (Claude Code, Cursor, etc.) is the only thing that mutates workspace state or runs Cicadas scripts. Chorus sends prompts; the agent does the work.
3. **Append-per-decision durability** — session state is written to disk after every resolved interrupt. Crash = lose at most one in-flight LLM call, not a session's worth of decisions.
4. **Abstracted interfaces at every external boundary** — LLM calls (via LiteLLM), agent execution, and escalation transport are each behind a single Python ABC/protocol. Implementations are swappable without touching the core loop.

### Supervisor Namespace Resolution

Chorus needs to write session artifacts before an initiative is kicked off (emergence stage) as well as after (execution stage). It mirrors the same resolution Cicadas uses: **`active/` takes precedence; `drafts/` is the fallback.**

```python
def supervisor_dir(workspace: Path, initiative: str) -> Path:
    active = workspace / ".cicadas" / "active" / initiative / "supervisor"
    drafts = workspace / ".cicadas" / "drafts" / initiative / "supervisor"
    if (workspace / ".cicadas" / "active" / initiative).exists():
        return active
    return drafts
```

This means session logs, escalations, and authority policy always land in the right place regardless of lifecycle stage.

### Cross-Cutting Concerns

1. **Session durability** — decision appends and terminal condition writes use write-then-rename for atomicity. The session file is a JSON array; appends re-read, extend, and rewrite atomically.
2. **Intent anchoring** — intent summary synthesized once at session start, passed as a frozen constant to every LLM call (classifier, reviewers, synthesis, consensus). Never re-synthesized mid-session unless explicitly requested.
3. **Authority policy as pre-flight gate** — "always escalate" category checked before classification or resolution. Not a post-hoc filter.
4. **Token tracking** — all LiteLLM calls log token counts via the workspace's `tokens.py` (if present) or chorus's own token log. Source: `"agent-reported"` for supervisor calls; `"unavailable"` for agent subprocess calls.
5. **`KeyboardInterrupt` handling** — main loop catches `KeyboardInterrupt`, writes terminal condition `requires_human_input` with reason `"interrupted"`, flushes session file, then re-raises cleanly.

### Workspace Coupling

Chorus depends on the Cicadas workspace at exactly one interface: **the `.cicadas/` filesystem schema**. The read contract:

| Path | Purpose |
|------|---------|
| `.cicadas/registry.json` | Initiative/branch detection |
| `.cicadas/{drafts\|active}/{initiative}/*.md` | Spec bundle assembly |
| `.cicadas/{drafts\|active}/{initiative}/emergence-config.json` | Pace, building_on_ai, eval_status |
| `.cicadas/canon/summary.md` | Canon context (if present) |

Chorus does **not** import or call any file from the Cicadas scripts directory. No `utils.py`, no `kickoff.py`, no `tokens.py` from the workspace. If the Cicadas schema changes, the only update needed in chorus is the filesystem reader — not any script interface.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| **API key exposure** | Keys live in `agents.json` on disk (user-managed). Chorus never logs model config or provider auth fields. `ConfigManager` strips auth fields before passing config to LiteLLM response logging. |
| **Prompt injection via workspace files** | Spec bundle content (from `.cicadas/`) is included in LLM prompts. Chorus does not sanitise it — the LLM is the consumer, not a security boundary. Risk is confined to the user's own workspace files influencing supervisor decisions, which is the intended behaviour. |
| **Agent tool-gate bypass** | `on_tool_gate` is the authority policy enforcement point. If `on_tool_gate` returns `False`, `ClaudeCodeAdapter` returns `PermissionResultDeny` to the SDK — the tool is not executed. The gate is always invoked before tool execution, not after. |
| **Session file integrity** | Session files are JSON arrays written atomically (write-to-`.tmp` → `replace()`). A corrupt or truncated session file is detected at load time; chorus falls back to an empty decision list and logs a warning rather than crashing. |
| **Workspace path traversal** | `supervisor_dir()` resolves paths relative to the `workspace` argument, which is validated as an existing directory at CLI startup. No user-supplied strings are passed to `open()` without going through `Path` resolution first. |
| **Secrets in prompts** | `chorus-handoff.md` contains intent summary, decisions, and authority policy — no model config, API keys, or environment variables are written to it. |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| **Supervisor loop latency** | Minimal added overhead beyond LLM call time | Filesystem reads (spec bundle, session) happen once per iteration; no polling. `context.py` caches the spec bundle for the session lifetime. |
| **Party mode latency** | ≤ max(reviewer latency) + synthesis + consensus | Three reviewer calls run in parallel via `ThreadPoolExecutor`. Sequential only when one reviewer fails and retry is needed. |
| **Token cost** | Proportional to interrupt volume | Intent summary synthesised once and reused. `chorus-handoff.md` is compact — decisions are summarised, not fully reproduced. Classifier runs before party mode to avoid deep resolution on simple questions. |
| **Session file growth** | Negligible for any realistic session | Decisions are small JSON objects. A 500-decision session is ~100KB. No rotation needed. |
| **LiteLLM cold start** | One-time per process | LiteLLM initialises provider clients on first call. No pre-warming needed; first call bears the initialisation cost. |

### Observability

- **Logs:** Every interrupt received, every decision written, every escalation sent, and every terminal condition — logged at `INFO`. LLM call failures logged at `ERROR` with model name and truncated prompt. Token counts logged at `DEBUG`.
- **Token log:** `supervisor/tokens.json` records every LiteLLM call (classifier, reviewers, synthesis, consensus, intent) with `initiative`, `phase`, `subphase`, `model`, `source: "agent-reported"`, input/output/cached counts. Agent subprocess tokens logged as `source: "unavailable"`.
- **Session file:** Human-readable audit trail of every decision, resolution path, and confidence score. Sufficient to reconstruct what chorus decided and why.
- **Escalations log:** `supervisor/escalations.md` — append-only human-readable record of every escalated question and its answer. Useful for post-session review.

---

## Implementation Sequence

### Build Order

1. **Foundation** *(blocking — everything depends on these)*
   - `models.py` — all dataclasses (`Interrupt`, `AgentResult`, `Decision`, `Session`, `AuthorityPolicy`)
   - `log_config.py` — central logger; imported by every module
   - `agents/base.py` — `CodingAgentInterface` ABC, `EscalationTransport` ABC, `PermissionDecision` types
   - `pyproject.toml` — package metadata, entry point, deps (`litellm`, `claude_agent_sdk`)

2. **Infrastructure** *(depends on 1; build in parallel with each other)*
   - `token_log.py` — atomic append, mirrors Cicadas `tokens.py` API
   - `eval_log.py` — JSONL append, best-effort write, `--no-eval-log` suppression
   - `session.py` — create, append decision, write terminal condition, crash recovery
   - `context.py` — `supervisor_dir()`, spec bundle reader, handoff writer, workspace coupling
   - `authority.py` — load `authority.md`, evaluate rule patterns, pre-flight gate
   - `config.py` + `ConfigManager` — load/merge `agents.json` global + workspace
   - `PromptLoader` — TOML load, version resolution, `{placeholder}` render

3. **Agent adapter** *(depends on 1; parallel with 2)*
   - `agents/claude_code.py` — `ClaudeCodeAdapter`: `claude_agent_sdk` wiring, `AskUserQuestion` → `on_interrupt`, `PreToolUse` → `on_tool_gate`, `ResultMessage` → `AgentResult`

4. **Resolution engine** *(depends on 1, 2; build in parallel with each other)*
   - `resolver.py` — LiteLLM classifier call, confidence threshold, shallow/deep routing
   - `party.py` — `ThreadPoolExecutor` reviewer fan-out (Phase 1), synthesis (Phase 2), consensus vote + retry (Phase 3)
   - `escalation.py` — `TerminalEscalation` implementation

5. **Supervisor loop** *(depends on 2, 3, 4)*
   - `supervisor.py` — iterate → authority pre-flight → route → resolve → log → terminal condition detection
   - Interfaces injected at construction: `CodingAgentInterface`, `Resolver`, `EscalationTransport`

6. **Plugin system** *(depends on 1, 2)*
   - `plugins.py` — `entry_points` discovery + explicit module path loader, `CicadasPluginRegistry`

7. **CLI** *(depends on 5, 6; thin layer)*
   - `cli.py` — arg parse → pre-flight workspace check → `ConfigManager` + `PromptLoader` → instantiate `Supervisor` → `asyncio.run(agent.run(...))`

8. **Prompts** *(parallel with 4–7)*
   - `prompts/classifier.toml`, `prompts/reviewer_analyst.toml`, `prompts/reviewer_ux.toml`, `prompts/reviewer_architect.toml`, `prompts/synthesizer.toml`, `prompts/consensus.toml`, `prompts/intent_synthesizer.toml`

9. **Tests** *(parallel with 2–7; write alongside each module)*
   - `tests/base.py` first (blocks all other tests)
   - Then per-module tests in build order: session → context → authority → resolver → party → supervisor → claude_code_adapter

10. **Cicadas integration** *(depends on 7; last step)*
    - Add `implement hands-free` command to `src/cicadas/SKILL.md`

---

### Parallel Work Opportunities

The following can be built concurrently by separate developers or agents once Step 1 is complete:

| Track A | Track B | Track C |
|---------|---------|---------|
| `session.py` + `token_log.py` | `context.py` + `authority.py` | `agents/claude_code.py` |
| `resolver.py` | `party.py` | `escalation.py` |
| Tests for Track A | Tests for Track B | Tests for Track C |

`supervisor.py` is the integration point — built after all three tracks converge.

---

### Known Implementation Risks

- **`claude_agent_sdk` API stability** — MVP dep at `>=0.1`; the SDK is early-stage. `AskUserQuestion` callback signature and `ResultMessage` structure may change. Mitigation: all SDK interaction is isolated inside `ClaudeCodeAdapter`; a breaking SDK change requires updating one file only.
- **`AskUserQuestion` availability** — the interrupt mechanism depends on Claude Code exposing `AskUserQuestion` as a tool interceptable via `can_use_tool`. Validate this works in a spike before committing to `ClaudeCodeAdapter` implementation.
- **Party mode consensus termination** — the retry loop (Phase 3 → Phase 1 on no-consensus) needs a hard `max_retries` cap to prevent infinite loops on genuinely ambiguous questions. Default: 2 retries before escalating.
- **LiteLLM structured output support** — classifier returns a confidence score; if the configured model doesn't support structured output reliably, the classifier must parse free-text JSON from the response. Implement a fallback JSON extractor for models that wrap JSON in markdown fences.
- **Prompt token budget** — spec bundles for large initiatives can be large. If `chorus-handoff.md` + spec bundle exceeds the model's context window, context assembly must truncate gracefully (most recent decisions first, oldest dropped). Add a token-count pre-check in `context.py` before assembling the final prompt.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Matches Cicadas requirement; `match` used for resolution routing; `asyncio.gather` for parallel reviewer calls |
| **Supervisor LLM calls** | `litellm` | Single unified `completion()` call across all providers (Anthropic, OpenAI, Gemini, Ollama, custom). Model string prefix (`anthropic/`, `openai/`) routes to the right provider. Supports extended thinking, structured output, and per-call token counts via `usage` field. |
| **Agent execution** | `claude_agent_sdk` (MVP) | Structured SDK events replace stdout parsing entirely. `can_use_tool` callback intercepts `AskUserQuestion` as the interrupt signal; `PreToolUse` hook enforces authority policy; `ResultMessage` gives clean terminal condition + `session_id` for resume. Wrapped behind `CodingAgentInterface` ABC — never imported outside `ClaudeCodeAdapter`. |
| **Agent abstraction** | `CodingAgentInterface` ABC | Decouples chorus core from agent implementation. `ClaudeCodeAdapter` ships in MVP; future adapters (Cursor, Rovo Dev) implement same `run()` / `resume()` / `on_interrupt` contract. Registered via plugin system. |
| **Concurrency** | `ThreadPoolExecutor` (stdlib) + `asyncio` (confined) | Party mode reviewer fan-out uses `ThreadPoolExecutor` — `litellm.completion()` is sync/blocking, threads are the right tool. `asyncio` is confined to `agents/claude_code.py` (SDK requirement) and a single `asyncio.run()` in `cli.py`. No other module is async. |
| **Data models** | `dataclasses` (stdlib) | `Session`, `Decision`, `Interrupt`, `AgentResult` — lightweight, JSON-serialisable, no ORM needed. |
| **Config** | `agents.json` format + `.cicadas/supervisor-config.json` | `agents.json` defines `_models` (base model definitions keyed by `model_id`) and named agents (each referencing a `model_id` + `prompt` + optional `model_parameters`/`custom_configs`). Loaded via `ConfigManager.load_agent(agent_name)` / `load_model(model_id)`. Global defaults in `~/.config/chorus/agents.json`; workspace override in `.cicadas/agents.json`. `_coding_agents` section is chorus-specific and not part of the base Cicadas schema. |
| **Prompts** | TOML files (`prompts/<name>.toml`) | Each file contains versioned `[v1]`, `[v2]`, … sections with `system_prompt` and/or `user_prompt` string fields. Both fields support `{placeholder}` substitution. Loaded via `PromptLoader.load_prompt(name, version="latest")` which returns a dict with `system_prompt`/`user_prompt` keys. `latest` resolves to the highest version number in the file. |
| **Plugin discovery** | `importlib.metadata` entry points + explicit module paths | `entry_points(group="cicadas.plugins")` auto-discovers pip-installed plugins. `supervisor-config.json` `plugins` array covers local/non-pip modules. Both layers merged at startup. |
| **Token logging** | chorus-internal `token_log.py` | Chorus is a separate package — cannot depend on workspace's `tokens.py`. Mirrors the same append-only API (`init_log`, `append_entry`). Writes to `supervisor/tokens.json`. |
| **Testing** | `unittest` (stdlib) | Matches Cicadas convention. `ClaudeCodeAdapter` and LiteLLM calls are mocked at the interface boundary (`CodingAgentInterface`, `litellm.completion`). |

**New dependencies (cicadas-chorus package):**
- `litellm>=1.0` — provider-agnostic LLM calls. Chosen over direct `anthropic` SDK: supports every provider the user might configure, including Atlassian AIGateway via `CustomLLM` extension, without code changes. Transitive dep on `anthropic` SDK is pulled in by LiteLLM automatically.
- `claude_agent_sdk>=0.1` — Claude Code agent integration. MVP only. Wrapped entirely inside `ClaudeCodeAdapter`; chorus core has no direct import.

**Dependencies explicitly rejected:**
- `anthropic` (direct) — LiteLLM wraps it. Direct import would create a hard Anthropic dependency in chorus core, defeating the provider-abstraction goal.
- `pydantic` — stdlib `dataclasses` + manual JSON serialisation sufficient; avoids a heavy validation dep.
- `langchain` / `crewai` / `langgraph` — party mode is three parallel `litellm.completion()` calls + synthesis; no orchestration framework needed. These add hundreds of transitive deps for no gain here.
- `asyncio` as the outer shell — main loop stays synchronous; `asyncio.run()` is scoped to parallel reviewer batches only. Keeps terminal I/O (`input()`) straightforward.

---
