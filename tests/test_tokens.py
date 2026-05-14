# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import multiprocessing
import unittest
from pathlib import Path
from queue import Empty

from base import CicadasTest
from tokens import VALID_SOURCES, append_entry, init_log, load_log


def _append_token_entries(log_path: Path, worker_id: int, count: int, errors) -> None:
    try:
        for i in range(count):
            append_entry(
                log_path,
                initiative=f"worker-{worker_id}",
                phase=f"phase-{worker_id}-{i}",
                source="unavailable",
            )
    except Exception as e:
        errors.put(f"{type(e).__name__}: {e}")


class TestInitLog(CicadasTest):
    def test_creates_file_with_empty_entries(self):
        log = self.root / "tokens.json"
        init_log(log)
        self.assertTrue(log.exists())
        data = json.loads(log.read_text())
        self.assertEqual(data, {"entries": []})

    def test_does_not_overwrite_existing_file(self):
        log = self.root / "tokens.json"
        log.write_text(json.dumps({"entries": [{"phase": "existing"}]}))
        init_log(log)
        data = json.loads(log.read_text())
        self.assertEqual(len(data["entries"]), 1)

    def test_creates_parent_dirs(self):
        log = self.root / "nested" / "dir" / "tokens.json"
        init_log(log)
        self.assertTrue(log.exists())


class TestLoadLog(CicadasTest):
    def test_returns_empty_list_when_file_absent(self):
        log = self.root / "nonexistent.json"
        self.assertEqual(load_log(log), [])

    def test_returns_empty_list_on_invalid_json(self):
        log = self.root / "tokens.json"
        log.write_text("not valid json {{{")
        self.assertEqual(load_log(log), [])

    def test_returns_empty_list_when_entries_key_missing(self):
        log = self.root / "tokens.json"
        log.write_text(json.dumps({"other": "data"}))
        self.assertEqual(load_log(log), [])

    def test_returns_entries(self):
        log = self.root / "tokens.json"
        log.write_text(json.dumps({"entries": [{"phase": "lifecycle"}]}))
        entries = load_log(log)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["phase"], "lifecycle")


class TestAppendEntry(CicadasTest):
    def _log(self) -> Path:
        return self.root / "tokens.json"

    def test_creates_file_on_first_write(self):
        append_entry(self._log(), initiative="test", phase="lifecycle", source="unavailable")
        self.assertTrue(self._log().exists())

    def test_entry_has_required_fields(self):
        append_entry(self._log(), initiative="test", phase="lifecycle", source="unavailable")
        entries = load_log(self._log())
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["initiative"], "test")
        self.assertEqual(e["phase"], "lifecycle")
        self.assertEqual(e["source"], "unavailable")
        self.assertIn("timestamp", e)

    def test_multiple_appends_grow_list(self):
        for i in range(3):
            append_entry(self._log(), initiative="test", phase=f"phase-{i}", source="unavailable")
        self.assertEqual(len(load_log(self._log())), 3)

    def test_optional_fields_default_to_none(self):
        append_entry(self._log(), initiative="test", phase="lifecycle", source="unavailable")
        e = load_log(self._log())[0]
        self.assertIsNone(e["subphase"])
        self.assertIsNone(e["input_tokens"])
        self.assertIsNone(e["output_tokens"])
        self.assertIsNone(e["cached_tokens"])
        self.assertIsNone(e["model"])
        self.assertIsNone(e["notes"])

    def test_optional_fields_stored_when_provided(self):
        append_entry(
            self._log(),
            initiative="test",
            phase="emergence",
            source="agent-reported",
            subphase="clarify",
            input_tokens=1200,
            output_tokens=400,
            cached_tokens=800,
            model="claude-sonnet-4-6",
            notes="two rounds",
        )
        e = load_log(self._log())[0]
        self.assertEqual(e["subphase"], "clarify")
        self.assertEqual(e["input_tokens"], 1200)
        self.assertEqual(e["output_tokens"], 400)
        self.assertEqual(e["cached_tokens"], 800)
        self.assertEqual(e["model"], "claude-sonnet-4-6")
        self.assertEqual(e["notes"], "two rounds")

    def test_raises_on_invalid_source(self):
        with self.assertRaises(ValueError):
            append_entry(self._log(), initiative="test", phase="lifecycle", source="bad-source")

    def test_raises_on_empty_initiative(self):
        with self.assertRaises(ValueError):
            append_entry(self._log(), initiative="", phase="lifecycle", source="unavailable")

    def test_raises_on_empty_phase(self):
        with self.assertRaises(ValueError):
            append_entry(self._log(), initiative="test", phase="", source="unavailable")

    def test_all_valid_sources_accepted(self):
        for source in VALID_SOURCES:
            log = self.root / f"tokens-{source}.json"
            append_entry(log, initiative="test", phase="lifecycle", source=source)
            self.assertEqual(load_log(log)[0]["source"], source)

    def test_timestamp_is_iso8601_utc(self):
        append_entry(self._log(), initiative="test", phase="lifecycle", source="unavailable")
        ts = load_log(self._log())[0]["timestamp"]
        # Must end with Z and contain T
        self.assertTrue(ts.endswith("Z"))
        self.assertIn("T", ts)

    def test_creates_parent_dirs(self):
        log = self.root / "nested" / "tokens.json"
        append_entry(log, initiative="test", phase="lifecycle", source="unavailable")
        self.assertTrue(log.exists())

    def test_concurrent_process_appends_preserve_all_entries(self):
        log = self._log()
        process_count = 8
        entries_per_process = 25
        ctx = multiprocessing.get_context("fork")
        errors = ctx.Queue()
        processes = [
            ctx.Process(
                target=_append_token_entries,
                args=(log, worker_id, entries_per_process, errors),
            )
            for worker_id in range(process_count)
        ]

        for process in processes:
            process.start()
        for process in processes:
            process.join(10)

        failures = []
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
                failures.append(f"process {process.pid} did not finish")
        while True:
            try:
                failures.append(errors.get_nowait())
            except Empty:
                break
        self.assertEqual(failures, [])
        self.assertTrue(all(process.exitcode == 0 for process in processes))

        data = json.loads(log.read_text())
        entries = data["entries"]
        self.assertEqual(len(entries), process_count * entries_per_process)
        phases = {entry["phase"] for entry in entries}
        self.assertEqual(len(phases), process_count * entries_per_process)


class TestKickoffTokenIntegration(CicadasTest):
    def test_kickoff_writes_token_entry(self):
        import kickoff

        name = "test-kickoff-tokens"
        draft_dir = self.cicadas_dir / "drafts" / name
        draft_dir.mkdir(parents=True)
        (draft_dir / "prd.md").write_text("# Test PRD")
        self.init_git()

        kickoff.kickoff(name, "test intent")

        log_path = self.cicadas_dir / "active" / name / "tokens.json"
        self.assertTrue(log_path.exists())
        entries = load_log(log_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["phase"], "lifecycle")
        self.assertEqual(entries[0]["subphase"], "kickoff")
        self.assertEqual(entries[0]["source"], "unavailable")
        self.assertEqual(entries[0]["initiative"], name)


class TestBranchTokenIntegration(CicadasTest):
    def test_branch_writes_token_entry(self):
        import branch
        import kickoff

        name = "test-branch-tokens"
        draft_dir = self.cicadas_dir / "drafts" / name
        draft_dir.mkdir(parents=True)
        (draft_dir / "prd.md").write_text("# Test PRD")
        self.init_git()

        kickoff.kickoff(name, "test intent")

        branch_name = f"feat/partition-a"
        branch.create_branch(branch_name, "partition a", "scripts/utils.py", initiative=name, no_worktree=True)

        log_path = self.cicadas_dir / "active" / name / "tokens.json"
        entries = load_log(log_path)
        # One from kickoff, one from branch
        impl_entries = [e for e in entries if e["phase"] == "implementation"]
        self.assertEqual(len(impl_entries), 1)
        self.assertEqual(impl_entries[0]["subphase"], branch_name)
        self.assertEqual(impl_entries[0]["source"], "unavailable")


class TestLoadTokenSummary(CicadasTest):
    def test_returns_none_when_file_absent(self):
        from history import load_token_summary

        self.assertIsNone(load_token_summary(self.root / "nonexistent"))

    def test_returns_none_when_all_counts_null(self):
        from history import load_token_summary

        folder = self.root / "archive" / "test"
        folder.mkdir(parents=True)
        append_entry(folder / "tokens.json", initiative="test", phase="lifecycle", source="unavailable")

        self.assertIsNone(load_token_summary(folder))

    def test_returns_summary_with_real_counts(self):
        from history import load_token_summary

        folder = self.root / "archive" / "test"
        folder.mkdir(parents=True)
        append_entry(folder / "tokens.json", initiative="test", phase="emergence", source="agent-reported",
                     input_tokens=1000, output_tokens=300, cached_tokens=500)
        append_entry(folder / "tokens.json", initiative="test", phase="emergence", source="agent-reported",
                     input_tokens=200, output_tokens=100, cached_tokens=0)

        summary = load_token_summary(folder)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["total_input"], 1200)
        self.assertEqual(summary["total_output"], 400)
        self.assertEqual(summary["total_cached"], 500)
        self.assertIn("emergence", summary["by_phase"])

    def test_render_html_no_crash_without_tokens(self):
        from history import render_html

        entries = [{"name": "test", "kind": "initiative", "date": "Jan 1, 2026",
                    "summary": "", "ledger_summary": "", "total_tasks": 0,
                    "done_tasks": 0, "token_summary": None}]
        html = render_html(entries)
        self.assertIn("test", html)

    def test_render_html_includes_token_block_when_present(self):
        from history import render_html

        entries = [{"name": "test", "kind": "initiative", "date": "Jan 1, 2026",
                    "summary": "", "ledger_summary": "", "total_tasks": 0,
                    "done_tasks": 0, "token_summary": {
                        "total_input": 1000, "total_output": 300, "total_cached": 500,
                        "by_phase": {"emergence": {"input": 1000, "output": 300, "cached": 500}}
                    }}]
        html = render_html(entries)
        self.assertIn("Tokens", html)
        self.assertIn("1,000", html)
        self.assertIn("emergence", html)


if __name__ == "__main__":
    unittest.main()
