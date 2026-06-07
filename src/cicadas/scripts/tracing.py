# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

"""Optional OpenTelemetry tracing for the Cicadas CLI.

All OTel SDK interaction is encapsulated here behind a null-object fallback
(`_NullTracer` / `_NullSpan`) so call sites can be written unconditionally —
`with tracer.start_as_current_span(...) as span:` works whether or not the
SDK is installed or tracing is enabled.
"""

from utils import get_registry_dir, load_json, save_json

_PROVIDER = None
_TRACER = None


class _NullSpan:
    """No-op span; satisfies the context manager and span protocol."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def set_attribute(self, key, value):
        pass

    def record_exception(self, exception):
        pass

    def set_status(self, status):
        pass


class _NullTracer:
    """No-op tracer returned when tracing is disabled or the SDK is absent."""

    def start_as_current_span(self, name, context=None, **kwargs):
        return _NullSpan()

    def start_span(self, name, context=None, **kwargs):
        return _NullSpan()


def init_tracer(config: dict):
    """Return a real OTel tracer or a `_NullTracer`. Idempotent (cached)."""
    global _PROVIDER, _TRACER

    if _TRACER is not None:
        return _TRACER

    tracing_config = (config or {}).get("tracing") or {}
    if not tracing_config.get("enabled"):
        _TRACER = _NullTracer()
        return _TRACER

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        service_name = tracing_config.get("service_name", "cicadas")
        endpoint = tracing_config.get("endpoint", "http://localhost:4318/v1/traces")
        headers = tracing_config.get("headers") or {}

        resource = Resource(attributes={"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        _PROVIDER = provider
        _TRACER = trace.get_tracer(service_name, tracer_provider=provider)
        return _TRACER
    except Exception:
        _TRACER = _NullTracer()
        return _TRACER


def flush() -> None:
    """Force-flush the cached provider, if one exists. Non-fatal."""
    if _PROVIDER is None:
        return
    try:
        _PROVIDER.force_flush(5000)
    except Exception:
        pass


def get_trace_context(initiative: str) -> dict | None:
    """Return the stored `trace_context` for an initiative, or None."""
    try:
        registry = load_json(get_registry_dir() / "registry.json")
        return registry.get("initiatives", {}).get(initiative, {}).get("trace_context")
    except Exception:
        return None


def store_trace_context(initiative: str, trace_id_hex: str, span_id_hex: str) -> None:
    """Persist `{trace_id, span_id}` for an initiative. Swallows all exceptions."""
    try:
        registry_path = get_registry_dir() / "registry.json"
        registry = load_json(registry_path)
        if initiative not in registry.get("initiatives", {}):
            return
        registry["initiatives"][initiative]["trace_context"] = {
            "trace_id": trace_id_hex,
            "span_id": span_id_hex,
        }
        save_json(registry_path, registry)
    except Exception:
        pass


def parent_context_for_initiative(initiative: str):
    """Reconstruct an OTel parent context from stored trace context, or None."""
    try:
        ctx = get_trace_context(initiative)
        if not ctx or not ctx.get("trace_id") or not ctx.get("span_id"):
            return None

        from opentelemetry import context as otel_context
        from opentelemetry import trace
        from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

        span_context = SpanContext(
            trace_id=int(ctx["trace_id"], 16),
            span_id=int(ctx["span_id"], 16),
            is_remote=True,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
        )
        return trace.set_span_in_context(NonRecordingSpan(span_context), otel_context.get_current())
    except Exception:
        return None


def span_context_hex(span) -> tuple[str, str] | None:
    """Return `(trace_id_hex, span_id_hex)` for a live span, or None."""
    try:
        span_context = span.get_span_context()
        if span_context is None or span_context.trace_id == 0:
            return None
        return (
            format(span_context.trace_id, "032x"),
            format(span_context.span_id, "016x"),
        )
    except Exception:
        return None
