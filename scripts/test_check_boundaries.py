#!/usr/bin/env python3
"""Unit tests for scripts/check_boundaries.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import check_boundaries

sys.dont_write_bytecode = True


class BoundaryTests(unittest.TestCase):
    def _write(self, root: Path, rel: str, content: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_valid_layout_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "guard/guard.py", "import json\nimport os\n")
            self._write(
                root,
                "adapters/opencode/index.ts",
                'import { evaluate } from "../../guard/core.mjs";\n',
            )
            self._write(root, "scripts/a.py", "import json\n")
            self._write(root, "skills/engineering/demo/scripts/a.py", "import sys\n")
            self.assertEqual(check_boundaries.check_boundaries(root), [])

    def test_guard_importing_scripts_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "guard/bad.py", "import scripts.check_skills\n")
            errs = check_boundaries.check_boundaries(root)
            self.assertEqual(len(errs), 1)
            self.assertIn("guard/", errs[0])

    def test_skill_importing_other_skill_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "skills/engineering/alpha/scripts/run.mjs",
                'import x from "../../beta/scripts/util.mjs";\n',
            )
            errs = check_boundaries.check_boundaries(root)
            self.assertEqual(len(errs), 1)
            self.assertIn("skills/engineering/alpha/", errs[0])

    def test_adapter_importing_other_adapter_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "adapters/pi/index.ts",
                'import x from "../opencode/index.ts";\n',
            )
            errs = check_boundaries.check_boundaries(root)
            self.assertEqual(len(errs), 1)
            self.assertIn("adapters/pi/", errs[0])

    def test_scripts_importing_guard_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "scripts/bad.py", "from guard import guard\n")
            errs = check_boundaries.check_boundaries(root)
            self.assertEqual(len(errs), 1)
            self.assertIn("scripts/", errs[0])

    def test_escape_hatch_pragma_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "guard/bad.py", "import os  # noqa: F401\n")
            self._write(root, "adapters/pi/bad.ts", "// @ts-ignore\nexport const x = 1;\n")
            errs = check_boundaries.check_escape_hatches(root)
            self.assertEqual(len(errs), 2)
            self.assertIn("@ts-ignore", errs[0])
            self.assertIn("noqa", errs[1])


if __name__ == "__main__":
    unittest.main()
