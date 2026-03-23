
# Tasks: cicadas-chorus

## Partition 1: Foundation → `feat/chorus-foundation`

- [ ] Scaffold repo: `cicadas-chorus/pyproject.toml` with entry point `chorus = chorus.cli:main`, deps `litellm>=1.0` and `claude_agent_sdk>=0.1`, Python 3.11+ constraint <!-- id: 100 -->
- [ ] Create `src/chorus/__init__.py`, `src/chorus/agents/__init__.py`, `tests/__init__.py` <!-- id: 101 -->
- [ ] Create `src/chorus/log_config.py`: `LOGGER_NAME = "chorus"`, `LOG_FORMAT`, `create_logger(level, log_file=None)` with stdout + optional `RotatingFileHandler` <!-- id: 102 -->
- [ ] Create `src/chorus/models.py`: `TokenUsage`, `Interrupt`, `AgentResult`, `Decision`, `Session`, `AuthorityRule`, `AuthorityPolicy`, `PartyOutputs`, `EvalSample` dataclasses with type hints <!-- id: 103 -->
- [ ] Create `src/chorus/agents/base.py`: `CodingAgentInterface` ABC (`run`, `resume`), `EscalationTransport` ABC (`send`), `PermissionDecision` union type <!-- id: 104 -->
- [ ] Create `tests/base.py`: `CicadasChorusTest(unittest.TestCase)` with temp workspace, minimal `.cicadas/registry.json`, `init_git()` helper <!-- id: 105 -->
- [ ] Write `tests/test_models.py`: JSON round-trips for all dataclasses; `EvalSample.label` is `None` at construction; `Session.terminal_condition` is `None` at construction <!-- id: 106 -->
- [ ] Reflect + Code Review <!-- id: 107 -->
- [ ] Open PR: feat/chorus-foundation → initiative/auto-cicadas <!-- id: 108 -->

---

## Partition 2: Workspace & Config → `feat/chorus-workspace-config`

- [ ] Create `src/chorus/token_log.py`: `init_log(path)`, `append_entry(path, initiative, phase, source, ...)`, `load_log(path)` — mirrors Cicadas `tokens.py` API, writes to `supervisor/tokens.json` <!-- id: 200 -->
- [ ] Create `src/chorus/eval_log.py`: `append_sample(path, sample, enabled=True)` JSONL append; `OSError` → WARNING + return (never raises); `EvalSample` serialised via `dataclasses.asdict()` <!-- id: 201 -->
- [ ] Create `src/chorus/context.py`: `supervisor_dir(workspace, initiative) → Path`; `read_spec_bundle(workspace, initiative) → dict` (registry, specs, emergence-config, canon summary); `write_handoff(supervisor_dir, intent, decisions, authority_summary, task_focus)`; spec bundle cached on instance <!-- id: 202 -->
- [ ] Create `src/chorus/authority.py`: `load_policy(supervisor_dir) → AuthorityPolicy` from `authority.md` front-matter; `evaluate(question, policy) → AuthorityRule | None`; `is_pre_flight_blocked(question, policy) → bool` <!-- id: 203 -->
- [ ] Create `src/chorus/config.py` + `ConfigManager`: `load_agent(name)`, `load_model(id)`, `load_coding_agent(id)`; merge global `~/.config/chorus/agents.json` + workspace `.cicadas/agents.json`; strip `provider_auth` from any logging output <!-- id: 204 -->
- [ ] Create `PromptLoader` (in `config.py` or standalone): TOML parse, `latest` version resolution, `render(prompt, **kwargs)` `{placeholder}` substitution <!-- id: 205 -->
- [ ] Create `src/chorus/plugins.py`: `CicadasPluginRegistry` protocol; `discover_plugins(config) → CicadasPluginRegistry` merging `entry_points(group="cicadas.plugins")` + explicit paths from config <!-- id: 206 -->
- [ ] Create `prompts/` directory with stub TOML files (placeholder content): `classifier.toml`, `reviewer_analyst.toml`, `reviewer_ux.toml`, `reviewer_architect.toml`, `synthesizer.toml`, `consensus.toml`, `intent_synthesizer.toml` <!-- id: 207 -->
- [ ] Write `tests/test_token_log.py`: init creates file; append round-trip; corrupt file returns `[]`; `OSError` on write logs warning <!-- id: 208 -->
- [ ] Write `tests/test_eval_log.py`: JSONL append round-trip; `enabled=False` writes nothing; `OSError` logs warning and does not raise <!-- id: 209 -->
- [ ] Write `tests/test_context.py`: `supervisor_dir` prefers `active/` over `drafts/`; spec bundle reads registry + specs; handoff file written to correct path <!-- id: 210 -->
- [ ] Write `tests/test_authority.py`: pre-flight gate blocks `always_escalate` patterns; `chorus_decides` passes; unmatched question uses `default_tier` <!-- id: 211 -->
- [ ] Write `tests/test_config.py`: global + workspace merge; workspace overrides global; missing global handled gracefully; auth fields not present in logged output <!-- id: 212 -->
- [ ] Reflect + Code Review <!-- id: 213 -->
- [ ] Open PR: feat/chorus-workspace-config → initiative/auto-cicadas <!-- id: 214 -->

---

## Partition 3: Resolution Engine → `feat/chorus-resolution`

- [ ] Create `src/chorus/escalation.py`: `TerminalEscalation(EscalationTransport)` — print question + context, block on `input()`, return stripped answer <!-- id: 300 -->
- [ ] Create `src/chorus/resolver.py`: `_call_llm(agent_cfg, prompt, extra_kwargs) → (content, usage)` helper; `classify(question, context, intent_summary, config, prompt_loader) → (resolution_path, confidence, tier)`; confidence threshold routing; token log append after each call <!-- id: 301 -->
- [ ] Create `src/chorus/party.py`: `run_reviewers(prompts, agent_cfgs) → list[str]` via `ThreadPoolExecutor(max_workers=3)`; `synthesize(reviewer_outputs, ...) → str`; `consensus(...) → Literal["agree","disagree","retry"]`; retry loop with `max_retries: int = 2` hard cap <!-- id: 302 -->
- [ ] Finalise prompt TOML content — replace stubs with real prompts for all seven agents; all `{placeholder}` fields match call sites in resolver/party <!-- id: 303 -->
- [ ] Write `tests/test_resolver.py`: mock `litellm.completion`; shallow path (high confidence); deep path (low confidence); pre-flight block; confidence exactly at threshold (boundary) <!-- id: 304 -->
- [ ] Write `tests/test_party.py`: mock `litellm.completion`; Phase 1 fan-out (3 calls); Phase 2 synthesis; Phase 3 consensus agree; consensus retry once then agree; no-consensus after max_retries → escalate path returned <!-- id: 305 -->
- [ ] Reflect + Code Review <!-- id: 306 -->
- [ ] Open PR: feat/chorus-resolution → initiative/auto-cicadas <!-- id: 307 -->

---

## Partition 4: Agent Adapter → `feat/chorus-agent-adapter`

- [ ] **Spike**: manually verify `AskUserQuestion` is interceptable via `can_use_tool` callback in `claude_agent_sdk`; document result in `spike-notes.md` in supervisor namespace; if blocked identify fallback approach before proceeding <!-- id: 400 -->
- [ ] Create `src/chorus/agents/claude_code.py`: `ClaudeCodeAdapter(CodingAgentInterface)`; `run()` and `resume()` using `claude_agent_sdk.query()`; `can_use_tool` maps `AskUserQuestion` → `on_interrupt(Interrupt(question, context))`; `PreToolUse` → `on_tool_gate`; `ResultMessage` subtype → `AgentResult.status`; `session_id` and `usage` extracted <!-- id: 401 -->
- [ ] Register `ClaudeCodeAdapter` in plugin factory map keyed `"claude_code"` <!-- id: 402 -->
- [ ] Write `tests/test_claude_code_adapter.py`: mock `claude_agent_sdk.query`; `AskUserQuestion` tool call invokes `on_interrupt` with correct `Interrupt`; `PreToolUse` invokes `on_tool_gate`; `ResultMessage` success → `AgentResult(status="completed")`; error subtypes → correct statuses <!-- id: 403 -->
- [ ] Reflect + Code Review <!-- id: 404 -->
- [ ] Open PR: feat/chorus-agent-adapter → initiative/auto-cicadas <!-- id: 405 -->

---

## Partition 5: Supervisor & CLI → `feat/chorus-supervisor-cli`

- [ ] Create `src/chorus/supervisor.py`: main loop (`authority pre-flight → classify → route → resolve → log`); `write_handoff` called before each agent run; `eval_log.append_sample` after each decision; `token_log.append_entry` after each LLM call; `KeyboardInterrupt` → write terminal condition `requires_human_input` + flush session + re-raise; `max_iterations` guard → terminal condition `unrecoverable_error` <!-- id: 500 -->
- [ ] Create `src/chorus/cli.py`: `chorus run`, `chorus start`, `chorus status`, `chorus config` subcommands; pre-flight check for `.cicadas/registry.json`; `create_logger()` called once at startup; `asyncio.run()` wrapping agent calls; `--no-eval-log` flag propagated to `eval_log` module <!-- id: 501 -->
- [ ] Update `src/cicadas/SKILL.md`: add `implement hands-free` row to Builder Commands table; command calls `chorus run --workspace {cwd}`; note Cicadas prereq and `pip install cicadas-chorus` <!-- id: 502 -->
- [ ] Write `tests/test_supervisor.py`: mock `CodingAgentInterface` + `litellm.completion`; shallow routing end-to-end; deep routing end-to-end; max_iterations terminal condition; `KeyboardInterrupt` writes terminal condition and flushes session; `eval_log.append_sample` called once per decision <!-- id: 503 -->
- [ ] Smoke test: run `chorus run` against a real local workspace with a live agent; verify session file, eval samples, and token log written correctly <!-- id: 504 -->
- [ ] Reflect + Code Review <!-- id: 505 -->
- [ ] Open PR: feat/chorus-supervisor-cli → initiative/auto-cicadas <!-- id: 506 -->
