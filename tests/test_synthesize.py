# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

import synthesize
from base import CicadasTest
from utils import REPO_CONTEXT_FILENAME, REPO_METADATA_FILENAME, REPO_TREE_FILENAME


class TestSynthesize(CicadasTest):
    def setUp(self):
        super().setUp()
        # Initialize git so get_project_root() works without mocks
        self.init_git()
        # Note: synthesize.py uses Path(__file__) to find templates,
        # which will resolve to the actual src directory.
        # This is fine for "real" tests as long as the templates exist.

    def test_gather_context_basic(self):
        # Create a branch and some files
        name = "feat/test"
        (self.cicadas_dir / "active" / name).mkdir(parents=True)
        (self.cicadas_dir / "active" / name / "prd.md").write_text("Active PRD")

        # Add to registry
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["branches"][name] = {"modules": ["my_mod"]}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        # Create code file
        # synthesize.py looks in src/mod/ or mod/
        mod_dir = self.root / "src" / "my_mod"
        mod_dir.mkdir(parents=True)
        (mod_dir / "logic.py").write_text("print('hello')")

        # Create canon
        (self.cicadas_dir / "canon/modules").mkdir(parents=True, exist_ok=True)
        (self.cicadas_dir / "canon/overview.md").write_text("Canon Overview")

        # We need to ensure we are in the root so get_project_root works
        context = synthesize.gather_context(name)

        self.assertIn("prd.md", context["active_docs"])
        self.assertEqual(context["active_docs"]["prd.md"], "Active PRD")
        self.assertIn("src/my_mod/logic.py", context["code_context"])
        self.assertIn("overview.md", context["canon_docs"])
        self.assertTrue((self.cicadas_dir / "canon" / REPO_METADATA_FILENAME).exists())
        self.assertTrue((self.cicadas_dir / "canon" / REPO_TREE_FILENAME).exists())
        self.assertTrue((self.cicadas_dir / "canon" / REPO_CONTEXT_FILENAME).exists())

    def test_generate_prompt(self):
        context = {
            "canon_docs": {"overview.md": "Canon"},
            "active_docs": {"prd.md": "Active"},
            "code_context": {"src/main.py": "print(1)"},
            "index": {"entries": []},
            "repo_context": "# Repo Context\n",
        }
        prompt = synthesize.generate_prompt(context)
        # Check for real template content identifiers instead of mocked one
        self.assertIn("### Step 1: Determine Mode", prompt)
        self.assertIn("Canon", prompt)
        self.assertIn("Active", prompt)
        self.assertIn("print(1)", prompt)
        self.assertIn("#### REPO CONTEXT ####", prompt)

    def test_gather_context_empty_active_dir(self):
        """gather_context returns empty active_docs when active dir has no files."""
        name = "feat/empty"
        (self.cicadas_dir / "active" / name).mkdir(parents=True)
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["branches"][name] = {"modules": []}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        context = synthesize.gather_context(name)
        self.assertEqual(context["active_docs"], {})

    def test_gather_context_no_src_dir(self):
        """gather_context returns empty code_context when no src/ directory exists."""
        name = "feat/nosrc"
        (self.cicadas_dir / "active" / name).mkdir(parents=True)
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["branches"][name] = {"modules": ["nonexistent_mod"]}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        context = synthesize.gather_context(name)
        self.assertEqual(context["code_context"], {})

    def test_gather_context_backfills_repo_metadata_when_missing(self):
        context = synthesize.gather_context("initiative/demo", is_initiative=True)
        self.assertIsInstance(context["repo_metadata"], dict)
        self.assertTrue((self.cicadas_dir / "canon" / REPO_METADATA_FILENAME).exists())
        self.assertTrue((self.cicadas_dir / "canon" / REPO_TREE_FILENAME).exists())
        self.assertTrue((self.cicadas_dir / "canon" / REPO_CONTEXT_FILENAME).exists())

    def test_apply_response_multiple_file_blocks(self):
        """apply_response writes all files when response contains multiple File: blocks."""
        response = """
File: canon/doc1.md
```markdown
Content one
```

File: canon/doc2.md
```markdown
Content two
```
"""
        synthesize.apply_response(response)
        self.assertEqual((self.cicadas_dir / "canon/doc1.md").read_text().strip(), "Content one")
        self.assertEqual((self.cicadas_dir / "canon/doc2.md").read_text().strip(), "Content two")

    def test_apply_response_empty_string_writes_nothing(self):
        """apply_response with an empty string must not create any files."""
        synthesize.apply_response("")
        self.assertFalse(any((self.cicadas_dir / "canon").iterdir()))

    def test_apply_response(self):
        # Create a temp response file
        response = """
File: canon/new_doc.md
```markdown
Updated content
```
"""
        response_file = self.root / "response.txt"
        response_file.write_text(response)

        synthesize.apply_response(response)  # Can call directly with text

        target = self.cicadas_dir / "canon/new_doc.md"
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text().strip(), "Updated content")

    def test_apply_response_writes_new_canon_families(self):
        response = """
File: canon/routing-guide.md
```markdown
Routing content
```

File: canon/areas/core.md
```markdown
Area content
```
"""
        synthesize.apply_response(response)
        self.assertEqual((self.cicadas_dir / "canon/routing-guide.md").read_text().strip(), "Routing content")
        self.assertEqual((self.cicadas_dir / "canon/areas/core.md").read_text().strip(), "Area content")


if __name__ == "__main__":
    unittest.main()
