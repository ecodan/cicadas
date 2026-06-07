---
summary: "A new tracing.py module encapsulates all OTel SDK interaction behind a _NullTracer fallback. Lifecycle scripts (kickoff, branch, archive, emit_event) and command_registry wrap their work in named spans; kickoff stores the root trace_id/span_id in registry.json so all subsequent per-process spans reconstruct the same parent context. SimpleSpanProcessor + force_flush() handles synchronous export from short-lived CLI processes."
phase: "tech"
when_to_load:
  - "When implementing or reviewing tracing module design, span instrumentation, trace continuity, or test structure."
  - "When checking whether changes still conform to the agreed technical approach."
depends_on:
  - "technical-brief.md"
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
  overview: "## Overview & Context"
  stack: "## Tech Stack & Dependencies"
  structure: "## Project / Module Structure"
  adrs: "## Architecture Decisions (ADRs)"
  data_models: "## Data Models"
  interfaces: "## API & Interface Design"
  conventions: "## Implementation Patterns & Conventions"
  security_performance: "## Security & Performance"
  implementation_sequence: "## Implementation Sequence"
next_section: null
---

# Tech Design: otel-instrumentation

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
- [x] Architecture Decisions (ADRs)
- [x] Data Models
- [x] API & Interface Design
- [x] Implementation Patterns & Conventions
- [x] Security & Performance
- [x] Implementation Sequence

---

## Overview & Context

**Summary:** The tracing initiative threads OpenTelemetry distributed tracing through the Cicadas CLI without adding a required runtime dependency or changing any existing CLI behavior. A single new module (`tracing.py`) owns all OTel SDK interaction and exposes a minimal surface: initialize a tracer, flush before process exit, resolve/store cross-process context, and convert a live span to storable hex strings. Every other module imports only `tracing` — they never import `opentelemetry` directly.

Because each Cicadas command runs as a short-lived subprocess (spawned by `command_registry.py` via `subprocess.run`), OTel contexts cannot propagate in-band across invocations. Cross-process trace continuity is solved by persisting `{trace_id, span_id}` from the kickoff span into `registry.json`. Every subsequent subprocess reads this stored context and reconstructs the parent `SpanContext` before starting its own span, producing a consistent trace in the backend.

### Cross-Cutting Concerns

1. **Non-fatal everywhere** — All tracing code must be wrapped in `try/except Exception: pass`. A broken backend, missing SDK, or corrupt trace_context must never affect CLI exit codes or JSONL writes.
2. **Synchronous flush** — `force_flush(5000)` is called at the end of every invocation. `SimpleSpanProcessor` (not Batch) is used so spans are exported before flush.
3. **Lazy SDK import** — The OTel packages are only imported inside `init_tracer()`. This keeps the module importable even when the SDK is not installed.

### Brownfield Notes

- `command_registry.py` currently calls `_run_script(spec.script_name, forwarded_args)` as a bare subprocess call — this call site is where the command span wrapper goes.
- `emit_event.py::emit_event()` already does an `fcntl.flock`-guarded JSONL append. OTel emission goes after the write completes.
- `kickoff.py` and `branch.py` already call `utils.emit()` which routes to `emit_event.py`. The dedicated lifecycle spans (e.g., `cicadas.initiative.kickoff`) are in addition to, not instead of, those event spans.
- `init.py` already generates a `config.json` template; only the `tracing` stub needs to be added.
- The `tokens.py` module must remain clean of OTel imports — the LLM span is emitted in `command_registry.py::_handle_tokens`, not in `tokens.py`.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Existing project requirement |
| **OTel API** | `opentelemetry-api>=1.20` | Stable; provides `SpanContext`, `NonRecordingSpan` |
| **OTel SDK** | `opentelemetry-sdk>=1.20` | `TracerProvider`, `SimpleSpanProcessor`, `Resource` |
| **OTLP Exporter** | `opentelemetry-exporter-otlp-proto-http>=1.20` | HTTP/protobuf; works with Arize, Phoenix, Jaeger |
| **Testing** | stdlib `unittest` + real filesystem | Project convention |

**New dependencies introduced:**

- `opentelemetry-api>=1.20`, `opentelemetry-sdk>=1.20`, `opentelemetry-exporter-otlp-proto-http>=1.20` — optional group `tracing` in `pyproject.toml`

**Dependencies explicitly rejected:**

- `opentelemetry-exporter-otlp-proto-grpc` — HTTP is sufficient and has fewer transitive dependencies
- `BatchSpanProcessor` — batch introduces background threads; bad for short-lived CLI processes where `atexit` may not fire
- Any tracing facade library (e.g., `opentelemetry-instrument-*` auto-instrumentors) — too broad for targeted CLI instrumentation

---

## Project / Module Structure

```
src/cicadas/scripts/
├── tracing.py                # NEW: core OTel module (_NullTracer, _NullSpan, init_tracer, flush, context helpers)
├── kickoff.py                # [MODIFIED] wrap kickoff() in cicadas.initiative.kickoff span; store trace context
├── branch.py                 # [MODIFIED] wrap create_branch() in cicadas.branch.create span; resolve parent
├── archive.py                # [MODIFIED] wrap archive() in cicadas.{type}.archive span; resolve parent
├── emit_event.py             # [MODIFIED] emit child span after JSONL write in emit_event()
├── command_registry.py       # [MODIFIED] wrap _run_script in cicadas.command.{name} span; add _detect_initiative(); emit LLM span in _handle_tokens
└── init.py                   # [MODIFIED] add tracing stub to config.json template
pyproject.toml                # [MODIFIED] add [project.optional-dependencies] tracing group
```

**Key structural decisions:**

- All OTel knowledge lives in `tracing.py` — other modules never import `opentelemetry` directly.
- `_NullTracer` and `_NullSpan` are defined in `tracing.py`, not in a separate file, to keep the module self-contained.

---

## Architecture Decisions (ADRs)

### ADR-1: Null Object Pattern for Optional SDK

**Decision:** `tracing.py` defines `_NullTracer` (returns `_NullSpan` from `start_as_current_span`/`start_span`) and `_NullSpan` (no-op `set_attribute`, `record_exception`, `set_status`, context manager). `init_tracer()` returns `_NullTracer` when tracing is disabled or the SDK is absent.

**Rationale:** Instrumented call sites write `with tracer.start_as_current_span(...) as span:` unconditionally. The null object makes the call sites identical regardless of SDK availability — no `if tracing_enabled:` guards scattered through lifecycle scripts.

**Affects:** `kickoff.py`, `branch.py`, `archive.py`, `emit_event.py`, `command_registry.py`

---

### ADR-2: SimpleSpanProcessor Over BatchSpanProcessor

**Decision:** Use `SimpleSpanProcessor` with `force_flush(5000ms)` at process exit.

**Rationale:** Cicadas CLI processes are short-lived (< 1 second for most commands). `BatchSpanProcessor` relies on a background thread and an `atexit` hook to flush; in short-lived processes this frequently results in dropped spans. `SimpleSpanProcessor` exports synchronously on `on_end()`, so `force_flush()` is just a safety net, not the primary export path.

**Affects:** `tracing.py::init_tracer()`

---

### ADR-3: Persist trace_context in registry.json

**Decision:** After the kickoff span starts, `span_context_hex(span)` extracts `(trace_id_hex, span_id_hex)` and `store_trace_context()` writes them to `registry.json["initiatives"][name]["trace_context"]`. Subsequent processes call `parent_context_for_initiative()` to reconstruct the `SpanContext`.

**Rationale:** Python subprocesses do not inherit OTel context from parent processes. Environment variable propagation (W3C `traceparent`) was considered but rejected: it would require modifying `subprocess.run()` calls and passing env overrides through command_registry, adding complexity. Storing in `registry.json` is consistent with how Cicadas already propagates state across process boundaries.

**Affects:** `tracing.py`, `kickoff.py`, `registry.json` schema

---

### ADR-4: Command Wrapper in command_registry, Not Each Script

**Decision:** The `cicadas.command.{name}` span wrapping `_run_script` is added to `command_registry.py::_handle_script_command()`, not duplicated in each script.

**Rationale:** `_handle_script_command` is the single dispatch point for every script command. Wrapping it once covers all commands including those not explicitly instrumented (e.g., `status`, `check`, `signal`). This is the DRY choice.

**Affects:** `command_registry.py`

---

### ADR-5: Kickoff Span Linkage Limitation

**Decision:** Accept that the `cicadas.command.kickoff` span emitted by `command_registry.py` and the `cicadas.initiative.kickoff` span emitted by `kickoff.py` will have different trace IDs for the first kickoff of a new initiative.

**Rationale:** When `command_registry.py` calls `parent_context_for_initiative("X")` before `kickoff.py` runs, the initiative doesn't exist in registry yet, so both spans are emitted as roots. Environment variable propagation was considered (see ADR-3) but rejected. For post-kickoff commands (branch, archive, emit-event), both the command span and the inner span correctly share the same trace ID stored in registry, so the linkage limitation only affects the single kickoff invocation.

**Affects:** `command_registry.py`, `tracing.py`

---

## Data Models

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `registry.json["initiatives"][name]` | Add optional `trace_context: {trace_id: str, span_id: str}` | No — additive; all readers use `.get()` |

```json
{
  "initiatives": {
    "my-feature": {
      "intent": "...",
      "created_at": "...",
      "trace_context": {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7"
      }
    }
  }
}
```

**Key field decisions:**

- `trace_id` / `span_id` stored as lowercase hex strings (32 and 16 hex chars respectively) — matches OTel wire format directly; no encoding/decoding needed.
- `trace_context` is absent for initiatives kicked off before this initiative ships — `parent_context_for_initiative()` returns `None` gracefully.

### Schema / Migration Notes

No migration needed. Existing `registry.json` files without `trace_context` continue to work. `store_trace_context` swallows all exceptions so a write failure doesn't leave the registry in a partial state.

---

## API & Interface Design

### `tracing.py` Public Surface

```python
def init_tracer(config: dict) -> Any:
    """Return real OTel tracer or _NullTracer. Idempotent."""

def flush() -> None:
    """Call force_flush(5000) on cached provider, if any."""

def get_trace_context(initiative: str) -> dict | None:
    """Read registry.json, return initiatives[name].get('trace_context')."""

def store_trace_context(initiative: str, trace_id_hex: str, span_id_hex: str) -> None:
    """Write trace_context to registry.json. Swallows all exceptions."""

def parent_context_for_initiative(initiative: str) -> Any | None:
    """Reconstruct OTel context from stored hex strings. Returns None on any failure."""

def span_context_hex(span: Any) -> tuple[str, str] | None:
    """Return (trace_id_hex, span_id_hex) from a live span. Returns None for NullSpan."""
```

### config.json tracing block (added by `init.py`)

```json
"tracing": {
    "enabled": false,
    "endpoint": "http://localhost:4318/v1/traces",
    "service_name": "cicadas",
    "headers": {}
}
```

### Span Catalog

| Span name | Emitted from | Key attributes |
|-----------|-------------|----------------|
| `cicadas.initiative.kickoff` | `kickoff.py` | `cicadas.initiative`, `cicadas.intent`, `cicadas.owner` |
| `cicadas.branch.create` | `branch.py` | `cicadas.branch`, `cicadas.initiative`, `cicadas.modules` |
| `cicadas.initiative.archive` | `archive.py` | `cicadas.name`, `cicadas.type` |
| `cicadas.branch.archive` | `archive.py` | `cicadas.name`, `cicadas.type` |
| `cicadas.{event.type}` | `emit_event.py` | `cicadas.initiative`, `cicadas.event.type`, `cicadas.event.*` (scalar data fields) |
| `cicadas.command.{name}` | `command_registry.py` | `cicadas.command`, `cicadas.initiative` (if detected), `cicadas.exit_code` |
| `cicadas.llm.call` | `command_registry.py` | `cicadas.initiative`, `llm.phase`, `llm.model`, `llm.input_tokens`, `llm.output_tokens`, `llm.cached_tokens` |

### Backward Compatibility

No existing CLI interface changes. All new behavior is opt-in via `config.json["tracing"]["enabled"]`.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Span names | `cicadas.{noun}.{verb}` | `cicadas.initiative.kickoff`, `cicadas.llm.call` |
| Span attributes | `cicadas.{field}` or `llm.{field}` | `cicadas.initiative`, `llm.input_tokens` |
| Private classes | underscore prefix | `_NullTracer`, `_NullSpan`, `_PROVIDER` |

### Error Handling Pattern

All tracing call sites in existing scripts use this pattern:

```python
try:
    import tracing
    from utils import load_config
    config = load_config()
    tracer = tracing.init_tracer(config)
    parent_ctx = tracing.parent_context_for_initiative(initiative)
    with tracer.start_as_current_span("cicadas.X.Y", context=parent_ctx) as span:
        span.set_attribute("cicadas.initiative", initiative)
        # ... existing logic unchanged ...
    tracing.flush()
except Exception:
    pass  # non-fatal — re-run existing logic outside the try
```

For `kickoff.py`, `branch.py`, and `archive.py` where the span wraps the main logic, use:

```python
config = load_config()
tracer = tracing.init_tracer(config)  # returns _NullTracer on any failure — safe
with tracer.start_as_current_span("cicadas.X.Y") as span:
    span.set_attribute(...)
    # ... full existing logic ...
tracing.flush()
```

The `_NullTracer` return from `init_tracer` on SDK absence means the second pattern is safe without an outer `try/except` — but `_emit_otel_span` in `emit_event.py` and the LLM span in `_handle_tokens` should still use an outer `try/except` because they involve registry reads.

### Testing Pattern

```python
class TestTracingModule(CicadasTest):
    def test_null_tracer_returned_when_disabled(self):
        tracer = tracing.init_tracer({})
        self.assertIsInstance(tracer, tracing._NullTracer)

    def test_null_span_set_attribute_noop(self):
        span = tracing._NullSpan()
        span.set_attribute("key", "value")  # must not raise

    def test_store_trace_context_nonfatal(self):
        # Should not raise even with corrupt registry
        tracing.store_trace_context("nonexistent-initiative", "abc", "def")
```

**Coverage expectations:** 80%+ on `tracing.py`; regression suite (all 52+ existing tests) must pass unchanged.

**Mocking strategy:** For integration tests verifying `store_trace_context` is called from `kickoff.py`, patch `tracing.store_trace_context` with `unittest.mock.patch`. Do not mock the filesystem — use real temp dirs per project convention.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| `headers` in config (e.g., API keys) | Config file lives in `.cicadas/config.json` — already gitignored by convention. No special handling needed beyond existing config security posture. |
| OTLP endpoint SSRF | Endpoint is operator-configured; Cicadas is a dev tool, not a server. No additional SSRF protection warranted. |
| Sensitive span attributes | Span attributes are limited to initiative names, command names, token counts, and model IDs — no secrets or user content. |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| CLI latency with tracing enabled | < 100ms added | `SimpleSpanProcessor` is synchronous but fast; `force_flush(5000)` has a timeout |
| CLI latency with tracing disabled | 0ms added | `_NullTracer` and `_NullSpan` are pure Python no-ops; no I/O |
| Import time | Negligible | OTel SDK is lazy-imported inside `init_tracer()` |

### Observability

- **Logs:** No new log lines; tracing failures are silently swallowed per design.
- **Metrics:** None added.
- **Traces:** This initiative *is* the observability feature. See Span Catalog above.

---

## Implementation Sequence

1. **`tracing.py` + `pyproject.toml` + `init.py` stub** *(blocking)* — All other changes import `tracing`. Must ship first.
2. **Lifecycle script instrumentation** *(depends on 1)* — `kickoff.py`, `branch.py`, `archive.py`, `emit_event.py`
3. **Command registry instrumentation** *(depends on 1, parallel with 2)* — `command_registry.py` command wrapper + `_handle_tokens` LLM span
4. **Tests** *(parallel with 2–3)* — `tests/test_tracing.py` unit tests; regression run

**Parallel work opportunities:** Steps 2 and 3 touch disjoint files and can be developed in parallel feature branches once step 1 is merged.

**Known implementation risks:**

- `_NullTracer.start_as_current_span` must behave as a valid context manager or `with tracer.start_as_current_span(...) as span:` call sites in lifecycle scripts will raise. Test this explicitly.
- `span_context_hex()` must handle `_NullSpan` gracefully (return `None`) so `kickoff.py` doesn't attempt to store a null trace_context.
