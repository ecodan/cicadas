---
summary: "Two partitions: P1 (tracing-core) creates tracing.py, pyproject.toml optional deps, init.py config stub, and unit tests; P2 (tracing-instrumentation) adds spans to kickoff.py, branch.py, archive.py, emit_event.py, and command_registry.py. Single initiative PR at the end."
phase: "tasks"
when_to_load:
  - "When selecting the next implementation task or reviewing completion state."
  - "When checking partition progress or execution sequencing."
depends_on:
  - "technical-brief.md"
  - "tech-design.md"
  - "approach.md"
modules:
  - "src/cicadas/scripts/tracing.py"
  - "src/cicadas/scripts/kickoff.py"
  - "src/cicadas/scripts/branch.py"
  - "src/cicadas/scripts/archive.py"
  - "src/cicadas/scripts/emit_event.py"
  - "src/cicadas/scripts/command_registry.py"
  - "src/cicadas/scripts/init.py"
  - "pyproject.toml"
  - "tests/test_tracing.py"
index:
  partition_one: "## Partition: feat/tracing-core"
  partition_two: "## Partition: feat/tracing-instrumentation"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/tracing-core"
---

# Tasks: otel-instrumentation

## Partition: feat/tracing-core

- [x] Create `src/cicadas/scripts/tracing.py` with `_NullSpan` (no-op context manager with `set_attribute`, `record_exception`, `set_status`, `__enter__`, `__exit__`), `_NullTracer` (returns `_NullSpan` from `start_as_current_span` and `start_span`), and module-level `_PROVIDER = None`, `_TRACER = None` cache <!-- id: 1 -->
- [x] Implement `init_tracer(config: dict)` in `tracing.py`: read `config.get("tracing", {})`, return cached `_TRACER` if already set, return `_NullTracer` if `enabled` is falsy; otherwise lazy-import OTel SDK, build `Resource`, `TracerProvider` with `SimpleSpanProcessor` + `OTLPSpanExporter(endpoint=..., headers=...)`, cache in `_PROVIDER`/`_TRACER`, return tracer; catch all import/runtime errors and return `_NullTracer` <!-- id: 2 -->
- [x] Implement `flush()`, `get_trace_context(initiative)`, `store_trace_context(initiative, trace_id_hex, span_id_hex)`, `parent_context_for_initiative(initiative)`, `span_context_hex(span)` in `tracing.py` per tech-design interface spec; all exceptions in `store_trace_context` and `parent_context_for_initiative` must be swallowed <!-- id: 3 -->
- [x] Add `[project.optional-dependencies]` `tracing` group to `pyproject.toml` with `opentelemetry-api>=1.20`, `opentelemetry-sdk>=1.20`, `opentelemetry-exporter-otlp-proto-http>=1.20` <!-- id: 4 -->
- [x] Update `init.py` config.json template to include `"tracing": {"enabled": false, "endpoint": "http://localhost:4318/v1/traces", "service_name": "cicadas", "headers": {}}` <!-- id: 5 -->
- [x] Create `tests/test_tracing.py`: test `_NullTracer`/`_NullSpan` no-op behavior; test `init_tracer` returns `_NullTracer` when disabled or tracing key absent; test `_NullTracer.start_as_current_span` is a valid context manager; test `flush()` no-ops when no provider; test `store_trace_context` is non-fatal with bad initiative name; test `span_context_hex(_NullSpan())` returns `None` <!-- id: 6 -->
- [x] Run full test suite (`PYTHONPATH=src/cicadas/scripts:tests python3 -m unittest discover -s tests/`) and confirm all existing tests still pass <!-- id: 7 -->

## Partition: feat/tracing-instrumentation

- [x] Instrument `kickoff.py`: add `import tracing` at top; in `kickoff()`, call `tracing.init_tracer(load_config())` before existing logic; wrap the full function body in `with tracer.start_as_current_span("cicadas.initiative.kickoff") as span:`; set `cicadas.initiative`, `cicadas.intent`, `cicadas.owner` attributes; call `tracing.store_trace_context(name, *ctx)` after registry save while span is still active; call `tracing.flush()` after the `with` block <!-- id: 10 -->
- [x] Instrument `branch.py`: add `import tracing`; call `init_tracer(load_config())`; resolve `parent_ctx = tracing.parent_context_for_initiative(initiative) if initiative else None`; wrap main body in `with tracer.start_as_current_span("cicadas.branch.create", context=parent_ctx) as span:`; set `cicadas.branch`, `cicadas.initiative`, `cicadas.modules`; call `tracing.flush()` <!-- id: 11 -->
- [x] Instrument `archive.py`: add `import tracing`; resolve parent ctx from initiative name; use span name `"cicadas.initiative.archive"` when `type_ == "initiative"` else `"cicadas.branch.archive"`; set `cicadas.name`, `cicadas.type`; call `tracing.flush()` <!-- id: 12 -->
- [x] Instrument `emit_event.py`: add `_emit_otel_span(initiative, event_type, data)` function that wraps all OTel calls in `try/except Exception: pass`; call it at the end of `emit_event()` after the JSONL write; set `cicadas.initiative`, `cicadas.event.type`, and `cicadas.event.{k}` for each scalar field in `data` <!-- id: 13 -->
- [x] Add `_detect_initiative(command_name: str, forwarded_args: list[str]) -> str | None` to `command_registry.py`: check `--initiative` flag first; fall back to first positional for `POSITIONAL_COMMANDS = {"kickoff", "branch", "archive", "prune", "unarchive", "register-existing"}` <!-- id: 14 -->
- [x] Wrap `_run_script` call in `_handle_script_command` with command span: detect initiative, resolve parent ctx, emit `cicadas.command.{spec.name}` span with `cicadas.command`, optional `cicadas.initiative`, `cicadas.exit_code`; wrap entire tracing block in `try/except Exception` so `_run_script` always executes <!-- id: 15 -->
- [x] Add LLM span in `_handle_tokens` after `append_entry` call: only when `tokens_args.input_tokens or tokens_args.output_tokens`; emit `cicadas.llm.call` span with `cicadas.initiative`, `llm.phase`, `llm.model` (if set), `llm.input_tokens`, `llm.output_tokens`, `llm.cached_tokens`; wrap in `try/except Exception: pass` <!-- id: 16 -->
- [x] Run full test suite and confirm all 52+ existing tests pass unchanged with tracing disabled (default) <!-- id: 17 -->
- [x] Verify scripts run without `ImportError` when `opentelemetry` is not installed: remove/rename the package from the test env temporarily (or use `sys.modules` manipulation in a test), confirm `cicadas.py status` exits cleanly <!-- id: 18 -->

## Initiative Boundary

- [ ] Open PR: initiative/otel-instrumentation -> master and await merge approval before continuing <!-- id: 100 -->
