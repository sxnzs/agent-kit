#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_listings import summary_of, sync, yaml_scalar


def _kit(root: Path) -> Path:
    skill = root / "skills" / "engineering" / "probe"
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: probe\ndescription: UI probe for tests. Use when testing.\n---\n\n# Probe\n", encoding="utf-8"
    )
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n  display_name: Probe\n  short_description: stale\n", encoding="utf-8"
    )
    (root / "skills" / "engineering" / "README.md").write_text("* [probe](probe/SKILL.md): stale\n", encoding="utf-8")
    (root / "README.md").write_text(
        "- **9 skills** here\n<summary>Model-invoked skills (9)</summary>\n"
        "| [probe](./skills/wrong/probe/SKILL.md) | wrong | stale |\n",
        encoding="utf-8",
    )
    return root


class SyncListingsTests(unittest.TestCase):
    def test_summary_stops_before_use_when(self) -> None:
        self.assertEqual(summary_of("Do a thing. Use when asked. Not for b."), "Do a thing.")
        self.assertEqual(summary_of("One sentence only."), "One sentence only.")
        self.assertEqual(
            summary_of("Pick the tool to use when deploying. Use when shipping."), "Pick the tool to use when deploying."
        )

    def test_yaml_scalar_quotes_only_when_needed(self) -> None:
        self.assertEqual(yaml_scalar("Plain text."), "Plain text.")
        self.assertEqual(yaml_scalar("Key: value"), '"Key: value"')
        self.assertEqual(yaml_scalar("Ends with colon:"), '"Ends with colon:"')

    def test_check_reports_drift_and_write_repairs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kit = _kit(Path(tmp))
            self.assertEqual(len(sync(kit, write=False)), 5)
            self.assertIn("stale", (kit / "README.md").read_text(encoding="utf-8"))
            sync(kit, write=True)
            self.assertEqual(sync(kit, write=False), [])
            top = (kit / "README.md").read_text(encoding="utf-8")
            self.assertIn("**1 skills**", top)
            self.assertIn("Model-invoked skills (1)", top)
            self.assertIn("| engineering | UI probe for tests. |", top)
            twin = (kit / "skills/engineering/probe/agents/openai.yaml").read_text(encoding="utf-8")
            self.assertIn("short_description: UI probe for tests.", twin)
            bucket = (kit / "skills/engineering/README.md").read_text(encoding="utf-8")
            self.assertIn("): UI probe for tests.", bucket)

    def test_missing_malformed_and_unknown_rows_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kit = _kit(Path(tmp))
            sync(kit, write=True)
            readme = kit / "README.md"
            text = readme.read_text(encoding="utf-8")
            readme.write_text(text.replace("| UI probe for tests. |", "| stale | "), encoding="utf-8")
            (kit / "skills/engineering/README.md").write_text("* [ghost](ghost/SKILL.md): gone\n", encoding="utf-8")
            drift = sync(kit, write=True)
            self.assertEqual(len(drift), 3, drift)
            self.assertIn("no listing row for skill 'probe'", drift[0])
            self.assertIn("no listing row for skill 'probe'", drift[1])
            self.assertIn("'ghost', which has no skill folder", drift[2])

    def test_row_in_wrong_kind_table_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kit = _kit(Path(tmp))
            sync(kit, write=True)
            readme = kit / "README.md"
            text = readme.read_text(encoding="utf-8")
            readme.write_text(text.replace("Model-invoked skills (1)", "User-invoked skills (0)"), encoding="utf-8")
            drift = sync(kit, write=True)
            self.assertTrue(any("belongs in the Model-invoked table" in line for line in drift), drift)


if __name__ == "__main__":
    unittest.main()
