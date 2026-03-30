# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
from pathlib import Path

from base import CicadasTest, SCRIPTS_DIR


CLI_PATH = SCRIPTS_DIR / "cicadas.py"


class TestCicadasCli(CicadasTest):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            cwd=self.root,
            text=True,
            capture_output=True,
        )

    def test_top_level_help_lists_known_commands(self):
        result = self._run_cli("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("status", result.stdout)
        self.assertIn("check", result.stdout)
        self.assertIn("kickoff", result.stdout)
        self.assertIn("create-lifecycle", result.stdout)
        self.assertIn("tokens", result.stdout)
        self.assertNotIn("create_lifecycle", result.stdout)
        self.assertNotIn("open_pr", result.stdout)

    def test_status_dispatches_to_existing_script(self):
        self.init_git()

        result = self._run_cli("status")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Project:", result.stdout)
        self.assertIn("Active Initiatives", result.stdout)

    def test_unknown_subcommand_returns_non_zero(self):
        result = self._run_cli("does-not-exist")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", result.stderr)

    def test_advanced_subcommand_help_is_available(self):
        for command in ("create-lifecycle", "validate-skill", "get-events"):
            result = self._run_cli(command, "--help")
            self.assertEqual(result.returncode, 0, msg=f"{command} help should succeed")
            self.assertIn("usage:", result.stdout)

    def test_create_lifecycle_mutation_path_works_via_cli(self):
        self.init_git()
        draft_dir = self.cicadas_dir / "drafts" / "demo-cli"
        draft_dir.mkdir(parents=True)

        result = self._run_cli("create-lifecycle", "demo-cli", "--no-pr-features")

        self.assertEqual(result.returncode, 0)
        lifecycle_path = draft_dir / "lifecycle.json"
        self.assertTrue(lifecycle_path.exists())
        payload = json.loads(lifecycle_path.read_text())
        self.assertFalse(payload["pr_boundaries"]["features"])

    def test_tokens_init_show_and_append(self):
        log_path = self.root / "tokens.json"

        init_result = self._run_cli("tokens", "init", str(log_path))
        self.assertEqual(init_result.returncode, 0)
        self.assertTrue(log_path.exists())

        append_result = self._run_cli(
            "tokens",
            "append",
            str(log_path),
            "--initiative",
            "demo",
            "--phase",
            "implementation",
            "--source",
            "estimated",
            "--input-tokens",
            "12",
        )
        self.assertEqual(append_result.returncode, 0)

        show_result = self._run_cli("tokens", "show", str(log_path))
        self.assertEqual(show_result.returncode, 0)
        payload = json.loads(show_result.stdout)
        self.assertEqual(len(payload["entries"]), 1)
        self.assertEqual(payload["entries"][0]["initiative"], "demo")

    def test_tokens_show_full_returns_error_on_invalid_json(self):
        log_path = self.root / "broken-tokens.json"
        log_path.write_text("{not-json")

        result = self._run_cli("tokens", "show", str(log_path), "--full")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error reading tokens file", result.stderr)

    def test_update_index_forwards_option_style_args_via_cli(self):
        result = self._run_cli(
            "update-index",
            "--branch",
            "feat/cli",
            "--summary",
            "cli message",
            "--modules",
            "cli_mod",
        )

        self.assertEqual(result.returncode, 0)
        index_path = self.cicadas_dir / "index.json"
        payload = json.loads(index_path.read_text())
        self.assertEqual(payload["entries"][-1]["branch"], "feat/cli")
        self.assertEqual(payload["entries"][-1]["summary"], "cli message")
        self.assertEqual(payload["entries"][-1]["modules"], ["cli_mod"])
