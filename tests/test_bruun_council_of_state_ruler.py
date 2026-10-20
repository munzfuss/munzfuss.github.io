"""The interregnum 2 Skilling 1533 (Galster 81) was seeded as «Christian III».

Bruun Part II lot 13056 has no ruler slot in its catalogue line («DENMARK. 2
Skilling, 1533. Malmö Mint. NGC MS-62.»), so the builder fell back to the
catalogue SECTION the lot sits in — Christian III — while the lot text says
«Struck by the Council of State (SENATUS REGNI DANIE) between the death of
Frederik I … and the outbreak of the so-called Count's Feud». The section is
where the cataloguer filed the coin, not a statement of its issuer (curator
2026-10-20: «bruun не стверджує Christian III»).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from build_bruun_denmark_seed import parse_ruler_from_meta  # noqa: E402


class CouncilOfState(unittest.TestCase):
    META = "DENMARK. 2 Skilling, 1533. Malmö Mint. NGC MS-62."

    def test_lot_text_names_the_council(self):
        body = (self.META + " Gal- ster-81; Sieg-1. Struck by the Council of State "
                "(SENATUS REGNI DANIE) be - tween the death of Frederik I")
        self.assertEqual(parse_ruler_from_meta(self.META, body, "Christian III"),
                         "Rigsrådet")

    def test_without_it_the_section_hint_stands(self):
        self.assertEqual(parse_ruler_from_meta(self.META, self.META, "Christian III"),
                         "Christian III")


if __name__ == "__main__":
    unittest.main()
