# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import unittest

import synthesize
from utils import save_repo_metadata
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

    def test_gather_context_registered_branch_uses_initiative_active_dir(self):
        branch_name = "fix/my-bug"
        initiative = "my-bug"
        active_dir = self.cicadas_dir / "active" / initiative
        active_dir.mkdir(parents=True)
        (active_dir / "buglet.md").write_text("Active buglet")
        with open(self.cicadas_dir / "registry.json") as f:
            registry = json.load(f)
        registry["initiatives"][initiative] = {"intent": "fix bug"}
        registry["branches"][branch_name] = {"initiative": initiative, "modules": []}
        with open(self.cicadas_dir / "registry.json", "w") as f:
            json.dump(registry, f)

        context = synthesize.gather_context(branch_name)

        self.assertEqual(context["active_docs"]["buglet.md"], "Active buglet")

    def test_generate_prompt(self):
        context = {
            "canon_docs": {"overview.md": "Canon"},
            "active_docs": {"prd.md": "Active"},
            "code_context": {"src/main.py": "print(1)"},
            "index": {"entries": []},
            "repo_context": "# Repo Context\n",
            "reconcile_scope": {"mode": "full"},
        }
        prompt = synthesize.generate_prompt(context)
        # Check for real template content identifiers instead of mocked one
        self.assertIn("### Step 1: Determine Mode", prompt)
        self.assertIn("Canon", prompt)
        self.assertIn("Active", prompt)
        self.assertIn("print(1)", prompt)
        self.assertIn("#### REPO CONTEXT ####", prompt)
        self.assertIn("#### RECONCILE SCOPE ####", prompt)

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
        self.assertIn("reconcile_scope", context)

    def test_initiative_gather_context_keeps_full_scope_for_normal_repo(self):
        initiative = "demo"
        active_dir = self.cicadas_dir / "active" / initiative
        active_dir.mkdir(parents=True)
        (active_dir / "prd.md").write_text(
            "---\nmodules:\n  - src/cicadas/scripts\n---\n\nNormal initiative\n"
        )
        (self.cicadas_dir / "canon" / "product-overview.md").write_text("Product")
        (self.cicadas_dir / "canon" / "tech-overview.md").write_text("Tech")
        (self.cicadas_dir / "canon" / "summary.md").write_text("Summary")

        context = synthesize.gather_context(initiative, is_initiative=True)

        self.assertEqual(context["reconcile_scope"]["mode"], "full")
        self.assertIn("product-overview.md", context["canon_docs"])
        self.assertIn("tech-overview.md", context["canon_docs"])
        self.assertIn("summary.md", context["canon_docs"])

    def test_initiative_gather_context_targets_touched_slice_for_large_repo(self):
        initiative = "demo"
        active_dir = self.cicadas_dir / "active" / initiative
        active_dir.mkdir(parents=True)
        (active_dir / "tech-design.md").write_text(
            "---\nmodules:\n  - src/payments\n---\n\nLocal slice change\n"
        )
        repo_metadata = {
            "repo_mode": "large-repo",
            "canon_plan": {
                "strategy": "locality-first",
                "orientation": ["product-overview.md", "tech-overview.md", "summary.md"],
                "slice_dirs": ["slices/"],
                "minimum_slice_files": ["summary.md", "boundaries.md", "architecture.md", "invariants.md", "change-guide.md"],
            },
            "candidate_slices": [
                {"name": "payments", "paths": ["src/payments"], "status": "seeded"},
                {"name": "accounts", "paths": ["src/accounts"], "status": "seeded"},
            ],
        }
        save_repo_metadata(repo_metadata, self.cicadas_dir / "canon")
        (self.cicadas_dir / "canon" / "product-overview.md").write_text("Product")
        (self.cicadas_dir / "canon" / "tech-overview.md").write_text("Tech")
        (self.cicadas_dir / "canon" / "summary.md").write_text("Summary")
        (self.cicadas_dir / "canon" / "slices" / "payments").mkdir(parents=True)
        (self.cicadas_dir / "canon" / "slices" / "payments" / "summary.md").write_text("Payments slice")
        (self.cicadas_dir / "canon" / "slices" / "payments" / "boundaries.md").write_text("Payments boundaries")
        (self.root / "src" / "payments").mkdir(parents=True)
        (self.root / "src" / "payments" / "logic.py").write_text("print('payments')\n")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "payments change"], check=True)

        context = synthesize.gather_context(initiative, is_initiative=True)

        self.assertEqual(context["reconcile_scope"]["mode"], "targeted")
        self.assertEqual(context["reconcile_scope"]["touched_slices"], ["payments"])
        self.assertEqual(context["reconcile_scope"]["neighbor_slices"], [])
        self.assertIn("summary.md", context["canon_docs"])
        self.assertIn("slices/payments/summary.md", context["canon_docs"])
        self.assertNotIn("product-overview.md", context["canon_docs"])
        self.assertNotIn("tech-overview.md", context["canon_docs"])
        self.assertIn("src/payments/logic.py", context["code_context"])

    def test_initiative_gather_context_expands_to_neighboring_slice_on_boundary_shift(self):
        initiative = "demo"
        active_dir = self.cicadas_dir / "active" / initiative
        active_dir.mkdir(parents=True)
        (active_dir / "tech-design.md").write_text(
            "---\nmodules:\n  - src/payments\n---\n\nBoundary and interface update across slices.\n"
        )
        repo_metadata = {
            "repo_mode": "mega-repo",
            "canon_plan": {
                "strategy": "locality-first",
                "orientation": ["product-overview.md", "tech-overview.md", "summary.md"],
                "slice_dirs": ["slices/"],
                "minimum_slice_files": ["summary.md", "boundaries.md", "architecture.md", "invariants.md", "change-guide.md"],
            },
            "candidate_slices": [
                {"name": "payments", "paths": ["src/payments"], "status": "seeded"},
                {"name": "accounts", "paths": ["src/accounts"], "status": "seeded"},
            ],
        }
        save_repo_metadata(repo_metadata, self.cicadas_dir / "canon")
        (self.cicadas_dir / "canon" / "summary.md").write_text("Summary")
        for slice_name in ["payments", "accounts"]:
            slice_dir = self.cicadas_dir / "canon" / "slices" / slice_name
            slice_dir.mkdir(parents=True)
            for doc_name in ["summary.md", "boundaries.md", "architecture.md", "invariants.md", "change-guide.md"]:
                (slice_dir / doc_name).write_text(f"{slice_name} {doc_name}")
        (self.root / "src" / "payments").mkdir(parents=True)
        (self.root / "src" / "payments" / "logic.py").write_text("print('payments')\n")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "boundary change"], check=True)

        context = synthesize.gather_context(initiative, is_initiative=True)

        self.assertEqual(context["reconcile_scope"]["touched_slices"], ["payments"])
        self.assertEqual(context["reconcile_scope"]["neighbor_slices"], ["accounts"])
        self.assertIn("slices/accounts/boundaries.md", context["canon_docs"])

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

    def test_apply_response_writes_slice_canon_files(self):
        response = """
File: canon/slices/core/summary.md
```markdown
Slice summary
```

File: canon/slices/core/change-guide.md
```markdown
Change guide
```
"""
        synthesize.apply_response(response)
        self.assertEqual((self.cicadas_dir / "canon/slices/core/summary.md").read_text().strip(), "Slice summary")
        self.assertEqual((self.cicadas_dir / "canon/slices/core/change-guide.md").read_text().strip(), "Change guide")

    def test_apply_response_skips_path_traversal(self):
        response = """
File: canon/../../outside.md
```markdown
Do not write
```

File: canon/safe.md
```markdown
Safe
```
"""
        synthesize.apply_response(response)

        self.assertFalse((self.root / "outside.md").exists())
        self.assertEqual((self.cicadas_dir / "canon/safe.md").read_text().strip(), "Safe")


if __name__ == "__main__":
    unittest.main()
