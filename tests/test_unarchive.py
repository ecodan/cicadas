# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from pathlib import Path

import archive
import unarchive
from base import CicadasTest
from utils import load_json


class TestUnarchive(CicadasTest):
    def test_archive_creates_metadata(self):
        name = "test-init-metadata"
        # Setup initiative in registry and active spec
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][name] = {"intent": "test metadata snapshot", "owner": "test-user"}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "spec.md").write_text("# Spec")

        # Run archive
        archive.archive(name, type_="initiative")

        # Verify moved to archive
        arch_dirs = list((self.cicadas_dir / "archive").iterdir())
        self.assertEqual(len(arch_dirs), 1)
        husk = arch_dirs[0]
        
        # Verify metadata snapshot exists
        metadata_path = husk / ".cicadas_metadata.json"
        self.assertTrue(metadata_path.exists())
        metadata = load_json(metadata_path)
        self.assertEqual(metadata["name"], name)
        self.assertEqual(metadata["registry_entry"]["intent"], "test metadata snapshot")

    def test_unarchive_restores_state(self):
        name = "test-restore"
        # 1. Setup and Archive
        with open(self.cicadas_dir / "registry.json", "r+") as f:
            reg = json.load(f)
            reg["initiatives"][name] = {"intent": "to be restored", "owner": "rebuilder"}
            reg["branches"]["feat/r1"] = {"intent": "associated", "initiative": name}
            f.seek(0)
            json.dump(reg, f)
            f.truncate()

        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        (active_dir / "doc.md").write_text("content")

        archive.archive(name, type_="initiative")
        
        # Verify it's gone
        reg = load_json(self.cicadas_dir / "registry.json")
        self.assertNotIn(name, reg["initiatives"])
        self.assertNotIn("feat/r1", reg["branches"])
        self.assertFalse(active_dir.exists())

        # 2. Run unarchive
        unarchive.unarchive(name)

        # 3. Verify restored
        reg = load_json(self.cicadas_dir / "registry.json")
        self.assertIn(name, reg["initiatives"])
        self.assertEqual(reg["initiatives"][name]["intent"], "to be restored")
        self.assertIn("feat/r1", reg["branches"])
        self.assertTrue(active_dir.exists())
        self.assertTrue((active_dir / "doc.md").exists())
        
        # Verify metadata file is cleaned up
        self.assertFalse((active_dir / ".cicadas_metadata.json").exists())

    def test_unarchive_fails_if_active_exists(self):
        name = "conflict-test"
        # Setup an archive
        (self.cicadas_dir / "archive" / "20260101-000000-conflict-test").mkdir(parents=True)
        (self.cicadas_dir / "archive" / "20260101-000000-conflict-test" / ".cicadas_metadata.json").write_text(
            json.dumps({"name": name, "type": "initiative", "registry_entry": {}})
        )
        
        # Setup an existing active dir
        active_dir = self.cicadas_dir / "active" / name
        active_dir.mkdir(parents=True)
        
        # Should fail
        result = unarchive.unarchive(name)
        self.assertEqual(result, 1)

if __name__ == "__main__":
    unittest.main()
