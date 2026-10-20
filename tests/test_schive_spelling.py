"""Schive's «section.number» has two spellings in our sources.

danskmoent prints «XIV.2», Bruun and Numista «XIV:2» — the same reference.
Merged, a class carried both and rendered «Schive# XIV.2, XIV:2» (Galster
149 / Bruun 9223, caught by the curator 2026-10-20). The catalogue
normaliser folds the colon into the dot; the renderer shows the section in
the label, «Schive XIV# 2», as the curator asked the same day.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.catalog_codes import normalise_catalog  # noqa: E402
from lib.compute import _SCHIVE_SECTION_RE, _PREFIX_PRIORITY  # noqa: E402


class SchiveSpelling(unittest.TestCase):
    def test_colon_folds_into_dot(self):
        c = {"schive": ["XIV.2", "XIV:2"]}
        normalise_catalog(c)
        self.assertEqual(c, {"schive": "XIV.2"})

    def test_scalar_range(self):
        c = {"schive": "XVIII:10-12"}
        normalise_catalog(c)
        self.assertEqual(c, {"schive": "XVIII.10-12"})

    def test_render_split(self):
        m = _SCHIVE_SECTION_RE.match("XIV.32-33")
        self.assertEqual(m.groups(), ("XIV", "32-33"))


class CatalogueOrder(unittest.TestCase):
    """Galster before Schive, NMD and Sieg; Schou before Schive and NMD;
    Schive before NMD (curator 2026-10-20)."""

    def test_order(self):
        p = _PREFIX_PRIORITY
        for later in ("Schive", "NMD", "Sieg"):
            self.assertLess(p["Galster"], p[later])
        for later in ("Schive", "NMD"):
            self.assertLess(p["Schou"], p[later])
        self.assertLess(p["Schive"], p["NMD"])


if __name__ == "__main__":
    unittest.main()
