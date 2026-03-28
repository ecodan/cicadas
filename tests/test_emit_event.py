# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import sys
import threading
import unittest
from pathlib import Path

from base import CicadasTest

SCRIPTS_DIR = Path(__file__).parent.parent / "src" / "cicadas" / "scripts"
EMIT_SCRIPT = SCRIPTS_DIR / "emit_event.py"


def _run_emit(initiative: str, event_type: str, data: dict | None = None) -> "subprocess.CompletedProcess":
    import subprocess
    cmd = [sys.executable, str(EMIT_SCRIPT), "--initiative", initiative, "--type", event_type]
    if data is not None:
        cmd += ["--data", json.dumps(data)]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestEmitEvent(CicadasTest):

    def _events_path(self, initiative: str) -> Path:
        return self.root / ".cicadas" / "active" / initiative / "events.jsonl"

    def test_creates_events_file(self):
        """Emitting an event creates events.jsonl in the expected path."""
        self.init_git()
        (self.cicadas_dir / "active" / "my-initiative").mkdir(parents=True, exist_ok=True)
        result = _run_emit("my-initiative", "test.event")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self._events_path("my-initiative").exists())

    def test_event_structure(self):
        """Emitted event contains all required fields with correct types."""
        self.init_git()
        (self.cicadas_dir / "active" / "my-initiative").mkdir(parents=True, exist_ok=True)
        _run_emit("my-initiative", "initiative.kicked_off", {"intent": "test"})

        line = self._events_path("my-initiative").read_text().strip()
        event = json.loads(line)

        self.assertIn("timestamp", event)
        self.assertIn("type", event)
        self.assertIn("initiative", event)
        self.assertIn("branch", event)
        self.assertIn("data", event)
        self.assertEqual(event["type"], "initiative.kicked_off")
        self.assertEqual(event["initiative"], "my-initiative")
        self.assertIsInstance(event["data"], dict)
        self.assertEqual(event["data"].get("intent"), "test")

    def test_appends_multiple_events(self):
        """Multiple emits produce multiple valid JSONL lines."""
        self.init_git()
        (self.cicadas_dir / "active" / "my-initiative").mkdir(parents=True, exist_ok=True)
        for i in range(3):
            _run_emit("my-initiative", f"test.event.{i}")

        lines = [l for l in self._events_path("my-initiative").read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertIsInstance(json.loads(line), dict)

    def test_creates_parent_directory(self):
        """emit_event creates events.jsonl even if the active dir doesn't exist yet."""
        self.init_git()
        # Do NOT pre-create the active/initiative directory
        result = _run_emit("new-initiative", "test.event")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self._events_path("new-initiative").exists())

    def test_invalid_initiative_name(self):
        """Invalid initiative name returns exit code 1."""
        self.init_git()
        result = _run_emit("Invalid Name!", "test.event")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid", result.stderr)

    def test_invalid_initiative_uppercase(self):
        """Uppercase initiative name returns exit code 1."""
        self.init_git()
        result = _run_emit("MyInitiative", "test.event")
        self.assertEqual(result.returncode, 1)

    def test_concurrent_writes(self):
        """20 concurrent emit calls all produce valid, non-corrupted JSONL lines."""
        self.init_git()
        (self.cicadas_dir / "active" / "concurrent-test").mkdir(parents=True, exist_ok=True)

        import subprocess
        errors: list[str] = []

        def emit_one(index: int) -> None:
            result = subprocess.run(
                [sys.executable, str(EMIT_SCRIPT),
                 "--initiative", "concurrent-test",
                 "--type", "test.concurrent",
                 "--data", json.dumps({"index": index})],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                errors.append(f"thread {index}: {result.stderr}")

        threads = [threading.Thread(target=emit_one, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Some emits failed: {errors}")

        lines = [l for l in self._events_path("concurrent-test").read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 20)
        for line in lines:
            event = json.loads(line)  # raises if corrupted/interleaved
            self.assertEqual(event["type"], "test.concurrent")

    def test_default_data(self):
        """Emitting without --data results in data == {}."""
        self.init_git()
        (self.cicadas_dir / "active" / "my-initiative").mkdir(parents=True, exist_ok=True)
        _run_emit("my-initiative", "test.event")  # no data arg

        line = self._events_path("my-initiative").read_text().strip()
        event = json.loads(line)
        self.assertEqual(event["data"], {})


if __name__ == "__main__":
    unittest.main()
