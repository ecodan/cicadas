# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src" / "cicadas" / "templates"


def _frontmatter_block(path: Path) -> str:
    text = path.read_text()
    lines = text.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)

    if len(lines) < 3 or lines[0] != "---":
        raise AssertionError(f"{path.name} is missing opening front matter delimiter")

    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"{path.name} is missing closing front matter delimiter") from exc

    return "\n".join(lines[1:end])


class TestSpecTemplates(unittest.TestCase):
    def test_core_spec_templates_include_context_frontmatter(self):
        expected_keys = [
            "summary:",
            "phase:",
            "when_to_load:",
            "depends_on:",
            "modules:",
            "index:",
            "next_section:",
        ]
        template_names = [
            "prd.md",
            "ux.md",
            "tech-design.md",
            "approach.md",
            "tasks.md",
        ]

        for name in template_names:
            frontmatter = _frontmatter_block(TEMPLATES / name)
            for key in expected_keys:
                self.assertIn(key, frontmatter, msg=f"{name} should include {key}")

    def test_tasks_template_matches_partition_workflow(self):
        text = (TEMPLATES / "tasks.md").read_text()

        self.assertIn("## Partition: feat/{branch-name-1}", text)
        self.assertIn("## Initiative Boundary", text)
        self.assertIn("Open PR: initiative/{initiative-name} -> master", text)
        self.assertNotIn(
            "Open PR: feat/{branch-name-1} -> initiative/{initiative-name}",
            text,
        )

    def test_canon_summary_includes_branch_start_routing_hint(self):
        text = (TEMPLATES / "canon-summary.md").read_text()

        self.assertIn("Branch-start rule:", text)
        self.assertIn("active spec front matter", text)

    def test_clarify_module_uses_current_frontmatter_contract(self):
        text = (ROOT / "src" / "cicadas" / "emergence" / "clarify.md").read_text()

        self.assertNotIn("steps_completed", text)
        self.assertIn("refresh front matter", text)
        self.assertIn("summary", text)
        self.assertIn("next_section", text)


if __name__ == "__main__":
    unittest.main()
