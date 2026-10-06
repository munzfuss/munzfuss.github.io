"""A mint string can carry the mintmaster too, in either order — and the seed
writer used to keep the wrong half of the second order.

`_canonicalise_mint` strips a bracket unconditionally. That is right for
«Altona (FF)» (mint, then mintmaster) and wrong for ucoin's «HCH (Heinrich
Christoph Hille, Zellerfeld)» / «J (Hamburg)» (initials or a mint letter, then
the town): the town was lost and «HCH» / «J» rendered as the mint. Bare initials
with no town at all («OHK», «CvC (Carl von Cramm)») rendered the same way.
CLAUDE.md anti-pattern 6: initials belong in `mintmaster`.

`;` was the same defect one character over: KMM's «Clausthal; Henning
Schreiber» became a two-mint list, while «København; Malmø» really is two mints.

Every input below is a verbatim cache value.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib import v2_seed_writer as w  # noqa: E402


def split(raw):
    m, mm = w._split_mint_mintmaster(raw)
    return w._canonicalise_mint(m), mm


class TownInTheBracket(unittest.TestCase):
    def test_initials_then_name_and_town(self):
        self.assertEqual(split("HCH (Heinrich Christoph Hille, Zellerfeld)"), ("Zellerfeld", "HCH"))

    def test_mint_letter_is_not_a_mintmaster(self):
        self.assertEqual(split("J (Hamburg)"), ("Hamburg", None))
        self.assertEqual(split("B (Hannover)"), ("Hannover", None))


class MintThenMintmaster(unittest.TestCase):
    def test_initials_kept_as_mintmaster(self):
        self.assertEqual(split("Copenhagen (FK VS)"), ("Kopenhagen", "FK VS"))
        self.assertEqual(split("Braunschweig (CvC, Carl von Cramm)"), ("Braunschweig", "CvC"))

    def test_non_initials_gloss_is_not_a_mintmaster(self):
        self.assertEqual(split("Celle (Germany)"), ("Celle", None))
        self.assertEqual(split("Hamburg (J)"), ("Hamburg", None))
        self.assertEqual(split("Kassel (37,000 mintage)"), ("Kassel", None))


class NoTownAtAll(unittest.TestCase):
    def test_bare_initials(self):
        self.assertEqual(split("OHK"), (None, "OHK"))
        self.assertEqual(split("CvC (Carl von Cramm)"), (None, "CvC"))
        self.assertEqual(split("LW/HS/IPE/RB (mintmasters across years)"), (None, "LW/HS/IPE/RB"))
        # hb-tid-81961, spaced slash.
        self.assertEqual(split("IHL / OHK"), (None, "IHL / OHK"))
        # tid 92007, comma-separated.
        self.assertEqual(split("CPS, IWS"), (None, "CPS, IWS"))
        # A real joint mint is not initials.
        self.assertEqual(split("Kopenhagen, Altona"), (["Altona", "Kopenhagen"], None))

    def test_lone_letter_is_dropped_not_kept(self):
        self.assertEqual(split("D"), (None, None))

    def test_unregistered_town_passes_through(self):
        # Unregistered is not dropped.
        self.assertEqual(split("Clausthal-Zellerfeld"), ("Clausthal-Zellerfeld", None))
        self.assertEqual(split("Eversburg"), ("Eversburg", None))


class Semicolon(unittest.TestCase):
    def test_mint_then_mintmaster(self):
        self.assertEqual(split("Clausthal; Henning Schreiber"), ("Clausthal", "Henning Schreiber"))

    def test_negation_names_nobody(self):
        self.assertEqual(split("Goslar; ikke Andreas Khüne)"), ("Goslar", None))

    def test_two_mints_stay_two_mints(self):
        self.assertEqual(split("København; Malmø"), (["Kopenhagen", "Malmø"], None))
        self.assertEqual(split("Clausthal-Zellerfeld; Zellerfeld"),
                         (["Clausthal-Zellerfeld", "Zellerfeld"], None))


class ApplyToCoin(unittest.TestCase):
    def test_existing_mintmaster_wins(self):
        c = {"mint": "Altona (FF)", "mintmaster": "IFF", "mint_verified": True}
        w._apply_mint_mintmaster_split(c, None)
        self.assertEqual(c["mintmaster"], "IFF")

    def test_no_mint_left_means_not_verified(self):
        c = {"mint": "OHK", "mint_verified": True}
        w._apply_mint_mintmaster_split(c, None)
        self.assertNotIn("mint", c)
        self.assertFalse(c["mint_verified"])
        self.assertEqual(c["mintmaster"], "OHK")


if __name__ == "__main__":
    unittest.main()


class NominalDoesNotOverrideMint(unittest.TestCase):
    """«søsling, 1/96 thaler» is one coin under two names; the left part is a
    denomination, not a mint, and must not replace the builder's mint."""

    def test_two_denominations_keep_source_mint(self):
        self.assertEqual(w._extract_mint_from_nominal("søsling, 1/96 thaler", "Gottorp"),
                         ("1/96 thaler", "Gottorp"))


class DanishSpellingOfTrondheim(unittest.TestCase):
    def test_trondhjem_is_the_mint_not_its_bracket(self):
        self.assertEqual(split("Trondhjem (Nidaros)"), ("Nidaros", None))
        from lib.mint_registry import canon_for_alias
        self.assertEqual(canon_for_alias("Trondhjem"), "nidaros")
