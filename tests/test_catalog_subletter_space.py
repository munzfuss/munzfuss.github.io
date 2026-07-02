"""normalise_numeric_index closes a spurious space between a catalogue number
and its terminal sub-letter — «39 C» → «39C» (ucoin's tab-split DOM occasionally
detaches the sub-letter; SOURCES.md §13.2, km-138-3-chr-vii-1787).

Applied per-token inside `normalise_numeric_index`, so it reaches the render
chokepoint (compute.py) AND the merger/absorb/seed-writer normalise_catalog pass.
Only a token that is ENTIRELY number+space+letters collapses; a value with
further structure — Lange's reign-disambiguated «358 C IV» (two spaces), a range
«39 A-39 D», a roman «XV.5» — is left intact. dav/davenport volume codes
(«EC II 3547») are not numeric-index fields, so they never reach this path.

Run via:
    .venv/bin/python -m unittest tests.test_catalog_subletter_space -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.catalog_codes import (  # noqa: E402
    normalise_catalog,
    normalise_numeric_index,
    _strip_subletter_space,
)


class TestStripHelper(unittest.TestCase):
    def test_collapses_terminal_subletter(self):
        self.assertEqual(_strip_subletter_space("39 C"), "39C")
        self.assertEqual(_strip_subletter_space("62 AB"), "62AB")
        self.assertEqual(_strip_subletter_space("264 a"), "264a")

    def test_keeps_reign_disambiguation(self):
        # «358 C IV» = Lange 358, Christian IV — a SECOND space; must stay intact.
        self.assertEqual(_strip_subletter_space("358 C IV"), "358 C IV")

    def test_keeps_clean_and_structured(self):
        self.assertEqual(_strip_subletter_space("39C"), "39C")
        self.assertEqual(_strip_subletter_space("108-110"), "108-110")
        self.assertEqual(_strip_subletter_space("39 A-39 D"), "39 A-39 D")
        self.assertEqual(_strip_subletter_space("XV.5"), "XV.5")
        self.assertEqual(_strip_subletter_space("RP 22.1"), "RP 22.1")


class TestNormaliseNumericIndex(unittest.TestCase):
    def test_scalar(self):
        self.assertEqual(normalise_numeric_index("39 C"), "39C")

    def test_list(self):
        self.assertEqual(normalise_numeric_index(["39 C", "62 AB"]), ["39C", "62AB"])

    def test_comma_joined(self):
        self.assertEqual(normalise_numeric_index("39 C, 62 A"), ["39C", "62A"])

    def test_idempotent(self):
        self.assertEqual(normalise_numeric_index(normalise_numeric_index("39 C")), "39C")


class TestNormaliseCatalog(unittest.TestCase):
    def test_hede_collapsed(self):
        cat = {"hede": "39 C", "hede_volume": "f3h", "sieg": "80.1"}
        normalise_catalog(cat)
        self.assertEqual(cat["hede"], "39C")

    def test_lange_reign_disamb_kept(self):
        cat = {"lange": "358 C IV"}
        normalise_catalog(cat)
        self.assertEqual(cat["lange"], "358 C IV")

    def test_dav_volume_code_untouched(self):
        cat = {"dav": "EC II 3547"}
        normalise_catalog(cat)
        self.assertEqual(cat["dav"], "EC II 3547")


if __name__ == "__main__":
    unittest.main()
