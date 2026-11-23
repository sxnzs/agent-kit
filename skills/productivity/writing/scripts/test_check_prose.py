#!/usr/bin/env python3
"""Unit tests for check_prose.py."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_prose  # noqa: E402


class CheckProseTests(unittest.TestCase):
    def test_clean_latam_spanish_passes(self) -> None:
        text = (
            "---\n"
            "title: Prueba — con guion en frontmatter\n"
            "---\n\n"
            "# Cómo funciona el harness\n\n"
            "El modelo solo predice texto. No toca tu computadora ni corre comandos por su cuenta.\n"
            "Vale la pena separar el archivo de configuración antes de correr las pruebas.\n\n"
            "- Primer paso con `git status -s` y `foo — bar`\n"
            "- Segundo paso: [ver enlace](https://example.com/a-b-c)\n\n"
            "```python\n"
            "# código con — em dash y fichero y hace sentido\n"
            "x = 1 - 2\n"
            "```\n"
        )
        findings = check_prose.check_text(text, path="clean.md", lang="auto")
        self.assertEqual(findings, [])

    def test_catches_spanish_calques_spain_lexicon_and_dashes(self) -> None:
        text = (
            "Claro, con gusto.\n"
            "En esencia, este ordenador no es rápido, sino lento — y hace sentido revisar el fichero.\n"
        )
        findings = check_prose.check_text(text, path="bad.md", lang="es")
        codes = {f.code for f in findings}
        self.assertIn("throat-clearing", codes)
        self.assertIn("es-ai-filler", codes)
        self.assertIn("es-spain-lexicon", codes)
        self.assertIn("contrast-template", codes)
        self.assertIn("dash-in-prose", codes)
        self.assertIn("es-calque", codes)
        line_map = {f.code: f.line for f in findings}
        self.assertEqual(line_map["throat-clearing"], 1)
        self.assertEqual(line_map["es-calque"], 2)

    def test_vale_la_pena_allowed_but_bare_vale_flagged(self) -> None:
        ok = check_prose.check_text("Vale la pena probar esto.", path="ok.md", lang="es")
        self.assertEqual(ok, [])
        bad = check_prose.check_text("Vale, entonces probamos esto.", path="bad.md", lang="es")
        self.assertEqual([f.code for f in bad], ["es-spain-soft"])

    def test_catches_english_tells_and_long_sentence(self) -> None:
        long_line = " ".join(["word"] * 42) + "."
        text = (
            "Great question!\n"
            "It's not a bug, it's a feature, and it's worth noting we should delve into it.\n"
            + long_line
            + "\n"
        )
        findings = check_prose.check_text(text, path="en.md", lang="en")
        codes = {f.code for f in findings}
        self.assertIn("throat-clearing", codes)
        self.assertIn("contrast-template", codes)
        self.assertIn("en-ai-tell", codes)
        self.assertIn("long-sentence", codes)


if __name__ == "__main__":
    unittest.main()
