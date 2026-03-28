# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import sys
import time
import unittest
from pathlib import Path

from base import CicadasTest

SCRIPTS_DIR = Path(__file__).parent.parent / "src" / "cicadas" / "scripts"
EMIT_SCRIPT = SCRIPTS_DIR / "emit_event.py"
GET_SCRIPT = SCRIPTS_DIR / "get_events.py"


def _run_emit(initiative: str, event_type: str, data: dict | None = None) -> None:
    import subprocess
    cmd = [sys.executable, str(EMIT_SCRIPT), "--initiative", initiative, "--type", event_type]
    if data is not None:
        cmd += ["--data", json.dumps(data)]
    subprocess.run(cmd, check=True, capture_output=True)


def _run_get(initiative: str, **kwargs) -> "subprocess.CompletedProcess":
    import subprocess
    cmd = [sys.executable, str(GET_SCRIPT), "--initiative", initiative]
    if "event_type" in kwargs and kwargs["event_type"] is not None:
        cmd += ["--type", kwargs["event_type"]]
    if "since" in kwargs and kwargs["since"] is not None:
        cmd += ["--since", kwargs["since"]]
    if "last" in kwargs and kwargs["last"] is not None:
        cmd += ["--last", str(kwargs["last"])]
    return subprocess.run(cmd, capture_output=True, text=True)


def _parse_output(result) -> list[dict]:
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


class TestGetEvents(CicadasTest):

    def test_missing_file_returns_empty(self):
        """get_events on initiative with no events.jsonl exits 0 with empty output."""
        self.init_git()
        result = _run_get("nonexistent-initiative")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_returns_all_events(self):
        """get_events with no filters returns all emitted events."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        for t in ["a.event", "b.event", "c.event"]:
            _run_emit("test-init", t)

        result = _run_get("test-init")
        self.assertEqual(result.returncode, 0)
        events = _parse_output(result)
        self.assertEqual(len(events), 3)

    def test_filter_by_type_exact(self):
        """--type filters to exact type matches only."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        _run_emit("test-init", "task.complete")
        _run_emit("test-init", "branch.created")
        _run_emit("test-init", "task.complete")

        result = _run_get("test-init", event_type="task.complete")
        events = _parse_output(result)
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e["type"] == "task.complete" for e in events))

    def test_filter_by_type_prefix(self):
        """--type prefix matches child event types."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        _run_emit("test-init", "partition.complete")
        _run_emit("test-init", "branch.created")

        result = _run_get("test-init", event_type="partition")
        events = _parse_output(result)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "partition.complete")

    def test_filter_by_since(self):
        """--since filters to events at or after the given timestamp."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        _run_emit("test-init", "early.event")
        time.sleep(0.05)

        # Capture a middle timestamp
        from datetime import datetime, timezone
        mid_ts = datetime.now(timezone.utc).isoformat()
        time.sleep(0.05)

        _run_emit("test-init", "late.event")

        result = _run_get("test-init", since=mid_ts)
        events = _parse_output(result)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "late.event")

    def test_last_n(self):
        """--last N returns only the N most recent events."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        for i in range(5):
            _run_emit("test-init", "seq.event", {"i": i})

        result = _run_get("test-init", last=3)
        events = _parse_output(result)
        self.assertEqual(len(events), 3)
        # Should be the last 3 (indices 2, 3, 4)
        indices = [e["data"]["i"] for e in events]
        self.assertEqual(indices, [2, 3, 4])

    def test_chronological_order(self):
        """Events are returned in ascending timestamp order."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        for label in ["first", "second", "third"]:
            _run_emit("test-init", "seq.event", {"label": label})
            time.sleep(0.02)

        result = _run_get("test-init")
        events = _parse_output(result)
        labels = [e["data"]["label"] for e in events]
        self.assertEqual(labels, ["first", "second", "third"])

    def test_combined_filters(self):
        """Combining --type and --last returns correct subset."""
        self.init_git()
        (self.root / ".cicadas" / "active" / "test-init").mkdir(parents=True, exist_ok=True)
        for i in range(4):
            _run_emit("test-init", "task.complete", {"i": i})
            _run_emit("test-init", "branch.created")

        result = _run_get("test-init", event_type="task.complete", last=2)
        events = _parse_output(result)
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e["type"] == "task.complete" for e in events))
        indices = [e["data"]["i"] for e in events]
        self.assertEqual(indices, [2, 3])


if __name__ == "__main__":
    unittest.main()
