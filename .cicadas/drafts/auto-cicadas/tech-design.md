
---
next_section: 'Overview & Context'
---

# Tech Design: auto-cicadas

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
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
- [ ] Data Models
- [ ] API & Interface Design
- [ ] Implementation Patterns & Conventions
- [ ] Security & Performance
- [ ] Implementation Sequence

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

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Matches Cicadas requirement; `match` used for resolution routing; `asyncio.gather` for parallel reviewer calls |
| **Supervisor LLM calls** | `litellm` | Single unified `completion()` call across all providers (Anthropic, OpenAI, Gemini, Ollama, custom). Model string prefix (`anthropic/`, `openai/`) routes to the right provider. Supports extended thinking, structured output, and per-call token counts via `usage` field. |
| **Agent execution** | `claude_agent_sdk` (MVP) | Structured SDK events replace stdout parsing entirely. `can_use_tool` callback intercepts `AskUserQuestion` as the interrupt signal; `PreToolUse` hook enforces authority policy; `ResultMessage` gives clean terminal condition + `session_id` for resume. Wrapped behind `CodingAgentInterface` ABC — never imported outside `ClaudeCodeAdapter`. |
| **Agent abstraction** | `CodingAgentInterface` ABC | Decouples chorus core from agent implementation. `ClaudeCodeAdapter` ships in MVP; future adapters (Cursor, Rovo Dev) implement same `run()` / `resume()` / `on_interrupt` contract. Registered via plugin system. |
| **Async** | `asyncio` (stdlib) | Party mode Phase 1 and Phase 3 run reviewer calls in parallel via `asyncio.gather`. Main supervisor loop is synchronous; `asyncio.run()` invoked only for parallel batches. Keeps `input()` escalation and terminal I/O simple. |
| **Data models** | `dataclasses` (stdlib) | `Session`, `Decision`, `Interrupt`, `AgentResult` — lightweight, JSON-serialisable, no ORM needed. |
| **Config** | `~/.config/chorus/config.json` + `.cicadas/supervisor-config.json` | Global defaults + workspace override. Model definitions follow existing Cicadas `_models` / `agents.json` format — LiteLLM model strings are compatible. Coding agent config (`_coding_agents`) is chorus-specific. |
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
