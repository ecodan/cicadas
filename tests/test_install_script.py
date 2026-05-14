# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = REPO_ROOT / "install.sh"


class TestInstallScript(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.repo_dir = self.test_dir / "repo"
        self.repo_dir.mkdir()
        self.install_dir = self.repo_dir / ".cicadas-skill" / "cicadas"
        self.install_dir.mkdir(parents=True)
        (self.install_dir / "SKILL.md").write_text("---\nname: cicadas\ndescription: Test skill.\n---\n")
        self.home_dir = self.test_dir / "home"
        self.home_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_setup_agents(self, agents: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        if extra_env:
            env.update(extra_env)
        command = (
            f"source {shlex.quote(str(INSTALL_SCRIPT))}; "
            f"setup_agents {shlex.quote(str(self.install_dir))} {shlex.quote(agents)}"
        )
        return subprocess.run(
            ["bash", "-lc", command],
            cwd=self.repo_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_codex_agent_accepted_with_custom_codex_home(self):
        codex_home = self.test_dir / "custom-codex-home"
        result = self._run_setup_agents("codex", {"CODEX_HOME": str(codex_home)})

        self.assertEqual(result.returncode, 0, result.stderr)
        dest = codex_home / "skills" / "cicadas"
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.resolve(), self.install_dir.resolve())
        self.assertIn("Restart Codex to pick up the new skill.", result.stdout)

    def test_codex_uses_home_default_when_codex_home_unset(self):
        result = self._run_setup_agents("codex")

        self.assertEqual(result.returncode, 0, result.stderr)
        dest = self.home_dir / ".codex" / "skills" / "cicadas"
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.resolve(), self.install_dir.resolve())

    def test_codex_symlink_target_is_absolute(self):
        result = self._run_setup_agents("codex")

        self.assertEqual(result.returncode, 0, result.stderr)
        dest = self.home_dir / ".codex" / "skills" / "cicadas"
        self.assertTrue(dest.is_symlink())
        self.assertTrue(os.path.isabs(os.readlink(dest)))

    def test_multiple_agents_keep_existing_integrations_working(self):
        result = self._run_setup_agents("claude-code,codex")

        self.assertEqual(result.returncode, 0, result.stderr)
        claude_dest = self.repo_dir / ".claude" / "skills" / "cicadas"
        codex_dest = self.home_dir / ".codex" / "skills" / "cicadas"
        self.assertTrue(claude_dest.is_symlink())
        self.assertTrue(codex_dest.is_symlink())
        self.assertEqual(codex_dest.resolve(), self.install_dir.resolve())

    def test_installer_runs_from_stdin_with_nounset_enabled(self):
        fake_bin = self.test_dir / "bin"
        fake_bin.mkdir()

        fake_curl = fake_bin / "curl"
        fake_curl.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "output=''\n"
            "while [[ $# -gt 0 ]]; do\n"
            "  case \"$1\" in\n"
            "    -o) output=\"$2\"; shift 2 ;;\n"
            "    *) shift ;;\n"
            "  esac\n"
            "done\n"
            "touch \"$output\"\n"
        )

        fake_unzip = fake_bin / "unzip"
        fake_unzip.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "dest=''\n"
            "while [[ $# -gt 0 ]]; do\n"
            "  case \"$1\" in\n"
            "    -d) dest=\"$2\"; shift 2 ;;\n"
            "    *) shift ;;\n"
            "  esac\n"
            "done\n"
            "mkdir -p \"$dest/cicadas-master/src/cicadas/scripts\"\n"
            "printf '%s\\n' '---' 'name: cicadas' 'description: Test skill.' '---' > \"$dest/cicadas-master/src/cicadas/SKILL.md\"\n"
            "printf '%s\\n' 'print(\"initialized\")' > \"$dest/cicadas-master/src/cicadas/scripts/init.py\"\n"
        )

        fake_curl.chmod(0o755)
        fake_unzip.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

        subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, capture_output=True, text=True)
        result = subprocess.run(
            ["bash", "-s", "--", "--agent", "codex"],
            input=INSTALL_SCRIPT.read_text(),
            cwd=self.repo_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Installation complete", result.stdout)
        self.assertTrue((self.home_dir / ".codex" / "skills" / "cicadas").is_symlink())


if __name__ == "__main__":
    unittest.main()
