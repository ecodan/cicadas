---
summary: "Add opt-in OpenTelemetry distributed tracing to the Cicadas CLI so each initiative produces a single trace spanning kickoff through archive. Spans are exported via OTLP HTTP to any configurable backend. A new tracing.py module provides a _NullTracer fallback when the OTel SDK is absent or tracing is disabled, so zero existing functionality changes."
phase: "clarify"
when_to_load:
  - "When defining or reviewing tracing instrumentation goals, module scope, acceptance criteria, risks, rollback, observability, and tests."
  - "When downstream Tech Design, Approach, or Tasks need the approved technical problem statement."
depends_on: []
modules:
  - "src/cicadas/scripts/tracing.py"
  - "src/cicadas/scripts/kickoff.py"
  - "src/cicadas/scripts/branch.py"
  - "src/cicadas/scripts/archive.py"
  - "src/cicadas/scripts/emit_event.py"
  - "src/cicadas/scripts/command_registry.py"
  - "src/cicadas/scripts/init.py"
  - "pyproject.toml"
index:
  problem: "## Problem Statement"
  goals_non_goals: "## Goals and Non-Goals"
  affected_modules: "## Affected Modules"
  users_operators: "## Users and Operators Affected"
  success_criteria: "## Success Criteria"
  requirements: "## Functional Requirements and Acceptance Criteria"
  risks_rollback: "## Risks and Rollback"
  observability_testing: "## Observability and Testing Expectations"
  open_questions: "## Open Questions"
next_section: null
---

# Technical Brief: otel-instrumentation

## Progress

- [x] Problem Statement
- [x] Goals and Non-Goals
- [x] Affected Modules
- [x] Users and Operators Affected
- [x] Success Criteria
- [x] Functional Requirements and Acceptance Criteria
- [x] Risks and Rollback
- [x] Observability and Testing Expectations
- [x] Open Questions

## Problem Statement

Cicadas manages complex multi-phase development workflows (kickoff → feature branches → tasks → archive) but currently produces no machine-readable observability signal. Teams using Cicadas alongside LLM agents cannot correlate slow phases, identify which initiatives consume the most tokens, or inspect execution timelines in their existing observability stacks (Arize, Phoenix, Jaeger, etc.). Each CLI invocation is a short-lived subprocess with no connection to the broader initiative context, making distributed tracing architecturally non-trivial. The gap is: no way to ask "how long did phase X take for initiative Y, and which LLM calls happened in it?"

## Goals and Non-Goals

### Goals

- Instrument every significant lifecycle event (kickoff, branch create, event emit, archive, every CLI command) as an OTel span.
- Link all spans for a single initiative under one root trace via a persisted `trace_context` in `registry.json`.
- Export spans synchronously via OTLP HTTP to any compatible backend.
- Keep tracing entirely opt-in: disabled by default; degrades to a no-op when the OTel SDK is not installed.
- Zero change to observable CLI behavior for users who do not enable tracing.
- Emit a `cicadas.llm.call` span for every `tokens append` call that includes token counts.

### Non-Goals

- Spans for graph subsystem commands (`graph build`, `graph search`, etc.).
- Running or hosting any observability backend — operators bring their own.
- Windows support for the `fcntl`-based event log (pre-existing limitation).
- Async or batched span export — synchronous `SimpleSpanProcessor` only.

## Affected Modules

| Module / Path | Expected Change | Notes |
|---------------|-----------------|-------|
| `src/cicadas/scripts/tracing.py` | **Create** | New core module: `_NullTracer`, `_NullSpan`, `init_tracer()`, `flush()`, `get_trace_context()`, `store_trace_context()`, `parent_context_for_initiative()`, `span_context_hex()` |
| `src/cicadas/scripts/kickoff.py` | Modify | Wrap main logic in `cicadas.initiative.kickoff` span; store trace context in registry after span starts |
| `src/cicadas/scripts/branch.py` | Modify | Wrap main logic in `cicadas.branch.create` span; resolve parent from initiative trace context |
| `src/cicadas/scripts/archive.py` | Modify | Wrap main logic in `cicadas.initiative.archive` or `cicadas.branch.archive` span |
| `src/cicadas/scripts/emit_event.py` | Modify | After JSONL write, emit a child OTel span named `cicadas.{event_type}`; all exceptions swallowed |
| `src/cicadas/scripts/command_registry.py` | Modify | Wrap `_run_script` in `cicadas.command.{name}` span; add `_detect_initiative()` helper; emit `cicadas.llm.call` span in `_handle_tokens` for `append` with token counts |
| `src/cicadas/scripts/init.py` | Modify | Add `tracing` stub (disabled by default) to the generated `config.json` template |
| `pyproject.toml` | Modify | Add `[project.optional-dependencies] tracing = [opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-http]` (all >=1.20) |

## Users and Operators Affected

| Operator / User | Impact |
|-----------------|--------|
| Cicadas maintainer / developer | Can now enable tracing and inspect initiative timelines in Arize/Phoenix/Jaeger with no code changes |
| CI / automated pipelines | No impact — tracing is disabled by default; `_NullTracer` ensures zero runtime errors |
| LLM implementation agents | No change — `tokens append` CLI surface is unchanged; spans are emitted as a side effect |
| New project adopters running `cicadas init` | `config.json` template now includes a commented-out `tracing` stub for discoverability |

## Success Criteria

- `cicadas.initiative.kickoff` span appears in the backend with `cicadas.initiative` and `cicadas.intent` attributes after enabling tracing and running kickoff.
- Subsequent `branch`, `emit-event`, and `archive` spans are children of the kickoff span (same `trace_id`).
- `cicadas.llm.call` spans carry `llm.input_tokens`, `llm.output_tokens`, `llm.model` when those args are passed to `tokens append`.
- All 52+ existing tests pass without modification when tracing is disabled (default).
- All scripts run without errors or ImportErrors when `opentelemetry-sdk` is not installed.
- Tracing can be enabled and disabled purely via `config.json` with no code changes.

## Functional Requirements and Acceptance Criteria

### FR-1: Core Tracing Module (`tracing.py`)

- **Requirement:** A new `tracing.py` module must provide `init_tracer(config)`, `flush()`, `get_trace_context()`, `store_trace_context()`, `parent_context_for_initiative()`, and `span_context_hex()`. The module must be importable and functional with or without the OTel SDK installed.
- **Acceptance criteria:**
  - `init_tracer({})` returns a `_NullTracer` when `tracing.enabled` is absent or false.
  - `init_tracer({"tracing": {"enabled": true, ...}})` returns a real OTel tracer when the SDK is installed.
  - `init_tracer` is idempotent (repeated calls return the cached tracer).
  - `flush()` calls `force_flush(5000)` on the provider if one exists; otherwise is a no-op.
  - `_NullSpan.set_attribute`, `record_exception`, `set_status` are all no-ops.
  - `store_trace_context` swallows all exceptions (non-fatal).

### FR-2: Cross-Process Trace Continuity

- **Requirement:** `kickoff.py` must generate the root span and persist its `trace_id` + `span_id` to `registry.json["initiatives"][name]["trace_context"]`. All subsequent commands for that initiative must reconstruct the parent `SpanContext` from those stored hex strings.
- **Acceptance criteria:**
  - After `kickoff`, `registry.json` contains `trace_context.trace_id` and `trace_context.span_id` for that initiative.
  - A span started by `branch.py` for the same initiative has the same `trace_id` as the kickoff span.
  - If `trace_context` is absent or invalid, subsequent spans are emitted as root spans (no crash).

### FR-3: Broad Command Coverage (`command_registry.py`)

- **Requirement:** Every command dispatched via `_run_script` must be wrapped in a `cicadas.command.{name}` span. A `_detect_initiative()` helper extracts the initiative name from `--initiative` flag or first positional for lifecycle commands.
- **Acceptance criteria:**
  - `cicadas.command.status` span is emitted when `cicadas.py status` is run with tracing enabled.
  - `cicadas.command.kickoff` span has `cicadas.initiative` attribute set.
  - If tracing raises any exception, `_run_script` still executes normally (exception is caught).

### FR-4: Event Spans (`emit_event.py`)

- **Requirement:** After every successful JSONL write in `emit_event()`, a child OTel span named `cicadas.{event_type}` must be emitted. All scalar event data fields must be set as span attributes. All tracing code in `emit_event.py` must be wrapped in a top-level `try/except` (non-fatal).
- **Acceptance criteria:**
  - Running `cicadas emit-event --initiative X --type partition.complete --data '{"partition":"p1"}'` produces a `cicadas.partition.complete` span with `cicadas.event.partition = "p1"`.
  - A tracing failure does not affect the JSONL write or process exit code.

### FR-5: LLM Span (`command_registry.py` `_handle_tokens`)

- **Requirement:** When `tokens append` is called with `--input-tokens` or `--output-tokens`, a `cicadas.llm.call` span must be emitted as a child of the initiative's trace context.
- **Acceptance criteria:**
  - Span carries `llm.input_tokens`, `llm.output_tokens`, `llm.model`, `llm.phase`, `cicadas.initiative`.
  - `--cached-tokens` maps to `llm.cached_tokens` when present.
  - Span is not emitted for `tokens append` calls with neither `--input-tokens` nor `--output-tokens`.

### FR-6: Optional Dependency

- **Requirement:** `pyproject.toml` must declare a `tracing` optional dependency group containing `opentelemetry-api>=1.20`, `opentelemetry-sdk>=1.20`, and `opentelemetry-exporter-otlp-proto-http>=1.20`.
- **Acceptance criteria:**
  - `pip install -e ".[tracing]"` succeeds and installs the OTel packages.
  - The base install (`pip install -e .`) does not pull in OTel packages.

### FR-7: Config Stub in `init.py`

- **Requirement:** The `config.json` template generated by `init.py` must include a `tracing` section with `enabled: false`, `endpoint`, `service_name`, and `headers` keys.
- **Acceptance criteria:**
  - Running `cicadas init` on a fresh directory produces a `config.json` with `tracing.enabled == false` and `tracing.endpoint == "http://localhost:4318/v1/traces"`.

## Risks and Rollback

| Risk | Likelihood | Impact | Mitigation | Rollback |
|------|------------|--------|------------|----------|
| OTel SDK import failure crashes scripts | Low | High | All OTel imports are inside `try/except`; `_NullTracer` returned on any import error | Remove `import tracing` lines; no registry.json schema break |
| `store_trace_context` corrupts `registry.json` | Low | High | Swallow all exceptions in `store_trace_context`; unit-test the write path | Drop `trace_context` key from affected initiative entry manually |
| `force_flush()` blocks process exit on slow backends | Low | Medium | 5-second timeout on `force_flush`; `SimpleSpanProcessor` not `BatchSpanProcessor` | Set `tracing.enabled: false` in `config.json` |
| Adding `trace_context` to `registry.json` breaks status.py or check.py | Low | Medium | `trace_context` is an optional additive key; parsers use `.get()` patterns | Remove `trace_context` key; schema is backward-compatible |
| Test suite breaks due to tracing imports | Low | High | All tests run with tracing disabled by default; `_NullTracer` ensures no I/O side effects | Guard `import tracing` with `try/except` in test helpers if needed |

## Observability and Testing Expectations

- **Observability:** The tracing initiative is itself the observability feature. Manual verification against a local Phoenix or Jaeger instance is the primary confirmation path. `init.py` adds a config stub for discoverability.
- **Tests:** 
  - Unit tests for `tracing.py`: `_NullTracer`/`_NullSpan` no-op behavior; `init_tracer` returns `_NullTracer` when disabled; `store_trace_context` is non-fatal; `span_context_hex` returns correct hex strings.
  - Integration tests: `kickoff` → `branch` round-trip with mocked tracer verifying `store_trace_context` is called and `parent_context_for_initiative` returns a non-None context.
  - Regression: all 52+ existing tests pass unchanged.
  - Negative test: all scripts run without `ImportError` when `opentelemetry` is not installed (simulate by temporarily removing from sys.modules).
- **Manual verification:** Run the 10-step verification sequence from the requirements doc against a local Phoenix instance after installing `.[tracing]`.

## Open Questions

- None blocking. The requirements doc fully specifies architecture decisions (SimpleSpanProcessor, span_id persistence, `_detect_initiative` positional heuristic). These are adopted as-is.
