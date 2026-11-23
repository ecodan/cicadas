# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import skill_publish
from base import CicadasTest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_skill(cicadas: Path, slug: str) -> Path:
    """Create a minimal valid skill in active/skill-{slug}/."""
    d = cicadas / "active" / f"skill-{slug}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {slug}\ndescription: A valid description.\n---\n\n# Body\n"
    )
    config = {"publish_dir": None}
    (d / "emergence-config.json").write_text(json.dumps(config))
    return d


def _set_publish_dir(skill_dir: Path, publish_dir: str) -> None:
    config_path = skill_dir / "emergence-config.json"
    config = json.loads(config_path.read_text())
    config["publish_dir"] = publish_dir
    config_path.write_text(json.dumps(config))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSkillPublish(CicadasTest):

    def setUp(self):
        super().setUp()
        # All publish destinations go inside the temp project root
        self.pub_base = self.root / "published-skills"

    def test_copy_default(self):
        """Default behaviour: copies skill dir to publish_dir/slug/."""
        d = _make_valid_skill(self.cicadas_dir, "pdf-utils")
        _set_publish_dir(d, str(self.pub_base))

        skill_publish.publish("pdf-utils", cicadas_dir=self.cicadas_dir)

        dest = self.pub_base / "pdf-utils"
        self.assertTrue(dest.is_dir())
        self.assertTrue((dest / "SKILL.md").exists())
        self.assertFalse(dest.is_symlink())

    def test_symlink_flag(self):
        """--symlink creates a symlink instead of a copy."""
        d = _make_valid_skill(self.cicadas_dir, "sym-skill")
        _set_publish_dir(d, str(self.pub_base))

        skill_publish.publish("sym-skill", symlink=True, cicadas_dir=self.cicadas_dir)

        dest = self.pub_base / "sym-skill"
        self.assertTrue(dest.exists())
        self.assertTrue(dest.is_symlink())

    def test_destination_exists_without_force_exits_1(self):
        """If destination already exists, exit 1 without --force."""
        d = _make_valid_skill(self.cicadas_dir, "clash-skill")
        _set_publish_dir(d, str(self.pub_base))
        # Pre-create destination
        (self.pub_base / "clash-skill").mkdir(parents=True)

        with self.assertRaises(SystemExit) as cm:
            skill_publish.publish("clash-skill", cicadas_dir=self.cicadas_dir)
        self.assertEqual(cm.exception.code, 1)

    def test_destination_exists_with_force_succeeds(self):
        """--force overwrites existing destination."""
        d = _make_valid_skill(self.cicadas_dir, "force-skill")
        _set_publish_dir(d, str(self.pub_base))
        old_dest = self.pub_base / "force-skill"
        old_dest.mkdir(parents=True)
        (old_dest / "old.txt").write_text("old content")

        skill_publish.publish("force-skill", force=True, cicadas_dir=self.cicadas_dir)

        dest = self.pub_base / "force-skill"
        self.assertTrue((dest / "SKILL.md").exists())
        self.assertFalse((dest / "old.txt").exists())

    def test_publish_dir_null_in_config_exits_1(self):
        """publish_dir: null in config without --publish-dir override → exit 1."""
        _make_valid_skill(self.cicadas_dir, "null-dir")
        # publish_dir stays null (default from _make_valid_skill)

        with self.assertRaises(SystemExit) as cm:
            skill_publish.publish("null-dir", cicadas_dir=self.cicadas_dir)
        self.assertEqual(cm.exception.code, 1)

    def test_publish_dir_cli_override(self):
        """--publish-dir overrides emergence-config.json."""
        _make_valid_skill(self.cicadas_dir, "override-skill")
        # Don't set publish_dir in config; provide via CLI override
        override_dir = str(self.root / "cli-dest")

        skill_publish.publish(
            "override-skill", publish_dir=override_dir, cicadas_dir=self.cicadas_dir
        )

        self.assertTrue((self.root / "cli-dest" / "override-skill" / "SKILL.md").exists())

    def test_invalid_skill_fails_pre_publish_validate_exits_1_without_writing(self):
        """Invalid SKILL.md: pre-publish validation fails, nothing written to destination."""
        d = _make_valid_skill(self.cicadas_dir, "bad-skill")
        # Corrupt the SKILL.md (name mismatch)
        (d / "SKILL.md").write_text(
            "---\nname: wrong-name\ndescription: A description.\n---\n\n# Body\n"
        )
        _set_publish_dir(d, str(self.pub_base))

        with self.assertRaises(SystemExit) as cm:
            skill_publish.publish("bad-skill", cicadas_dir=self.cicadas_dir)
        self.assertEqual(cm.exception.code, 1)
        # Destination must not exist
        self.assertFalse((self.pub_base / "bad-skill").exists())

    def test_skill_dir_not_found_exits_1(self):
        """Slug with no matching active dir → exit 1."""
        with self.assertRaises(SystemExit) as cm:
            skill_publish.publish("ghost-skill", cicadas_dir=self.cicadas_dir)
        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
