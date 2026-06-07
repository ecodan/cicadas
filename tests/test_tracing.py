# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import sys
from unittest.mock import patch

import tracing
from base import CicadasTest
from utils import load_json, save_json

_BLOCKED_OTEL_MODULES = {
    "opentelemetry": None,
    "opentelemetry.exporter": None,
    "opentelemetry.exporter.otlp": None,
    "opentelemetry.exporter.otlp.proto": None,
    "opentelemetry.exporter.otlp.proto.http": None,
    "opentelemetry.exporter.otlp.proto.http.trace_exporter": None,
    "opentelemetry.sdk": None,
    "opentelemetry.sdk.resources": None,
    "opentelemetry.sdk.trace": None,
    "opentelemetry.sdk.trace.export": None,
}


class TestNullSpan(CicadasTest):
    def test_context_manager_protocol(self):
        span = tracing._NullSpan()
        with span as s:
            self.assertIs(s, span)

    def test_set_attribute_is_noop(self):
        span = tracing._NullSpan()
        span.set_attribute("key", "value")  # must not raise

    def test_record_exception_is_noop(self):
        span = tracing._NullSpan()
        span.record_exception(ValueError("boom"))  # must not raise

    def test_set_status_is_noop(self):
        span = tracing._NullSpan()
        span.set_status("ERROR")  # must not raise


class TestNullTracer(CicadasTest):
    def test_start_as_current_span_is_context_manager(self):
        tracer = tracing._NullTracer()
        with tracer.start_as_current_span("cicadas.test") as span:
            self.assertIsInstance(span, tracing._NullSpan)

    def test_start_span_returns_null_span(self):
        tracer = tracing._NullTracer()
        span = tracer.start_span("cicadas.test")
        self.assertIsInstance(span, tracing._NullSpan)

    def test_accepts_context_kwarg(self):
        tracer = tracing._NullTracer()
        with tracer.start_as_current_span("cicadas.test", context=object()) as span:
            self.assertIsInstance(span, tracing._NullSpan)


class TestInitTracer(CicadasTest):
    def setUp(self):
        super().setUp()
        tracing._PROVIDER = None
        tracing._TRACER = None

    def tearDown(self):
        tracing._PROVIDER = None
        tracing._TRACER = None
        super().tearDown()

    def test_returns_null_tracer_when_config_empty(self):
        tracer = tracing.init_tracer({})
        self.assertIsInstance(tracer, tracing._NullTracer)

    def test_returns_null_tracer_when_disabled(self):
        tracer = tracing.init_tracer({"tracing": {"enabled": False}})
        self.assertIsInstance(tracer, tracing._NullTracer)

    def test_returns_null_tracer_when_tracing_key_absent(self):
        tracer = tracing.init_tracer({"hints": True})
        self.assertIsInstance(tracer, tracing._NullTracer)

    def test_idempotent_returns_cached_tracer(self):
        first = tracing.init_tracer({})
        second = tracing.init_tracer({"tracing": {"enabled": True}})
        self.assertIs(first, second)


class TestFlush(CicadasTest):
    def setUp(self):
        super().setUp()
        tracing._PROVIDER = None
        tracing._TRACER = None

    def tearDown(self):
        tracing._PROVIDER = None
        tracing._TRACER = None
        super().tearDown()

    def test_flush_noop_when_no_provider(self):
        tracing.flush()  # must not raise

    def test_flush_swallows_provider_errors(self):
        class _BoomProvider:
            def force_flush(self, timeout):
                raise RuntimeError("boom")

        tracing._PROVIDER = _BoomProvider()
        tracing.flush()  # must not raise


class TestTraceContextStorage(CicadasTest):
    def _seed_initiative(self, name="my-initiative"):
        registry = load_json(self.cicadas_dir / "registry.json")
        registry.setdefault("initiatives", {})[name] = {"intent": "test", "signals": []}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)
        return name

    def test_get_trace_context_returns_none_when_absent(self):
        name = self._seed_initiative()
        self.assertIsNone(tracing.get_trace_context(name))

    def test_get_trace_context_returns_none_for_unknown_initiative(self):
        self.assertIsNone(tracing.get_trace_context("nonexistent"))

    def test_store_then_get_round_trip(self):
        name = self._seed_initiative()
        tracing.store_trace_context(name, "a" * 32, "b" * 16)
        ctx = tracing.get_trace_context(name)
        self.assertEqual(ctx, {"trace_id": "a" * 32, "span_id": "b" * 16})

    def test_store_trace_context_nonfatal_for_unknown_initiative(self):
        tracing.store_trace_context("nonexistent-initiative", "aa", "bb")  # must not raise
        self.assertIsNone(tracing.get_trace_context("nonexistent-initiative"))

    def test_store_trace_context_nonfatal_on_corrupt_registry(self):
        (self.cicadas_dir / "registry.json").write_text("not json")
        tracing.store_trace_context("whatever", "aa", "bb")  # must not raise


class TestParentContextForInitiative(CicadasTest):
    def test_returns_none_when_no_trace_context(self):
        registry = load_json(self.cicadas_dir / "registry.json")
        registry.setdefault("initiatives", {})["my-initiative"] = {"intent": "test", "signals": []}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)
        self.assertIsNone(tracing.parent_context_for_initiative("my-initiative"))

    def test_returns_none_for_unknown_initiative(self):
        self.assertIsNone(tracing.parent_context_for_initiative("nonexistent"))

    def test_returns_none_on_malformed_hex(self):
        registry = load_json(self.cicadas_dir / "registry.json")
        registry.setdefault("initiatives", {})["my-initiative"] = {
            "intent": "test",
            "signals": [],
            "trace_context": {"trace_id": "not-hex", "span_id": "also-not-hex"},
        }
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)
        self.assertIsNone(tracing.parent_context_for_initiative("my-initiative"))


class TestSpanContextHex(CicadasTest):
    def test_returns_none_for_null_span(self):
        self.assertIsNone(tracing.span_context_hex(tracing._NullSpan()))

    def test_returns_none_for_span_without_get_span_context(self):
        self.assertIsNone(tracing.span_context_hex(object()))


class TestImportErrorFallback(CicadasTest):
    """Verify graceful fallback when the opentelemetry SDK is not installed."""

    def setUp(self):
        super().setUp()
        tracing._PROVIDER = None
        tracing._TRACER = None

    def tearDown(self):
        tracing._PROVIDER = None
        tracing._TRACER = None
        super().tearDown()

    def test_init_tracer_falls_back_to_null_tracer_when_sdk_absent(self):
        config = {"tracing": {"enabled": True, "endpoint": "http://localhost:4318/v1/traces"}}
        with patch.dict(sys.modules, _BLOCKED_OTEL_MODULES):
            tracer = tracing.init_tracer(config)
        self.assertIsInstance(tracer, tracing._NullTracer)

    def test_status_command_exits_cleanly_when_sdk_absent(self):
        import command_registry

        self.init_git()
        save_json(self.cicadas_dir / "config.json", {"tracing": {"enabled": True, "endpoint": "http://localhost:4318/v1/traces"}})

        spec = next(s for s in command_registry.SCRIPT_COMMANDS if s.name == "status")
        args = argparse.Namespace(script_args=[], show_help=False)

        with patch.dict(sys.modules, _BLOCKED_OTEL_MODULES):
            exit_code = command_registry._handle_script_command(spec, args)

        self.assertEqual(exit_code, 0)


class TestCommandSpanFailureDoesNotDoubleExecute(CicadasTest):
    """A tracing failure after the script runs must not re-run the underlying command."""

    def setUp(self):
        super().setUp()
        tracing._PROVIDER = None
        tracing._TRACER = None

    def tearDown(self):
        tracing._PROVIDER = None
        tracing._TRACER = None
        super().tearDown()

    def test_run_script_invoked_exactly_once_when_span_exit_raises(self):
        import command_registry

        class _BoomSpan(tracing._NullSpan):
            def __exit__(self, exc_type, exc_val, exc_tb):
                raise RuntimeError("exporter exploded")

        class _BoomTracer(tracing._NullTracer):
            def start_as_current_span(self, name, context=None, **kwargs):
                return _BoomSpan()

        spec = next(s for s in command_registry.SCRIPT_COMMANDS if s.name == "status")
        args = argparse.Namespace(script_args=[], show_help=False)

        with patch.object(command_registry.tracing, "init_tracer", return_value=_BoomTracer()), \
                patch.object(command_registry, "_run_script", return_value=0) as mock_run_script:
            exit_code = command_registry._handle_script_command(spec, args)

        self.assertEqual(mock_run_script.call_count, 1)
        self.assertEqual(exit_code, 0)
