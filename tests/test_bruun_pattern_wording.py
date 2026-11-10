"""Bruun parser: «pattern» / «trial» wording alone does not exclude a lot
(curator 2026-11-08); an off-metal or off-nominal piece still goes."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots", ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py")
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def excluded(meta, desc):
    return bool(P.PATTERN_RE.search(desc)) or bool(P.OFF_METAL_TITLE_RE.search(meta)) or (
        bool(P.PATTERN_WORD_RE.search(desc))
        and P._pattern_off_metal_or_nominal(meta, desc))


class PatternWording(unittest.TestCase):
    def test_roman_attire_krone_kept(self):
        meta = "DENMARK. 4 Mark (Krone), 1666. Copenhagen Mint."
        desc = meta + " KM-271; Hede-105B. This exquisite type ... is considered a pattern and today"
        self.assertFalse(excluded(meta, desc))

    def test_decorative_pattern_not_a_marker(self):
        meta = "DENMARK. Ducat, 1709. Copenhagen Mint. Frederik IV . NGC MS-62."
        desc = meta + " this Ducat featuring an alternating pattern of crowned arms"
        self.assertFalse(excluded(meta, desc))

    def test_copper_skilling_pattern_kept(self):
        meta = "DENMARK. Copper Pattern 4 Skilling, 1812. Copenhagen Mint. Frederik VI. NGC PROOF-63"
        self.assertFalse(excluded(meta, meta))

    def test_base_metal_and_off_metal_excluded(self):
        for meta in ("DENMARK. Pewter Pattern 2 Frederik d’ or, 1825. Altona",
                     "NORW AY . Gold Mark Pattern, 1684. Christiania Mint.",
                     "DENMARK. Copper Trial  Strike 1/2 Rigsdaler, 1855. Copen-",
                     "DENMARK. Silver Pattern (without denomination), ND (1809-12)."):
            self.assertTrue(excluded(meta, meta), meta)

    def test_gold_under_silver_nominal_with_weight_paren(self):
        meta = "DENMARK. Gold 4 Mark (of 10 Ducats Weight), 1689. Copenhagen Mint. Christian V ."
        desc = meta + " this must be considered a trial for a new but never realized silver Krone"
        self.assertTrue(excluded(meta, desc))

    def test_catalogue_flags_other_metal(self):
        meta = "DENMARK. Silver Pattern 6 Skilling, 1812. Copenhagen"
        self.assertTrue(excluded(meta, meta + " Hede-12; Sieg-40 (copper); Schou-4a"))

    def test_off_metal_strike_still_excluded_without_pattern_word(self):
        meta = "DENMARK. Gold Off-Metal 2 Skilling, 1711."
        self.assertTrue(excluded(meta, meta + " off-metal strike"))


class OffMetalHeadline(unittest.TestCase):
    """«Off-Metal» in the headline excludes; in the description alone it does
    not (curator 2026-11-10)."""

    def test_headline_without_strike_excluded(self):
        meta = "DENMARK. Gold Off-Metal. 2 Skilling, 1711. Frederik IV . NGC Unc Details—Obverse Scratched."
        self.assertTrue(excluded(meta, meta + " Fr-unlisted; KM-502 (silver); Hede-44A"))

    def test_description_mention_kept(self):
        meta = "NORW AY . 1/8 Speciedaler, 1660. Christiania Mint. Frederik III. NGC EF-45."
        desc = meta + (" The weight is consistent with a 1/8 Speciedaler, and was likely produced"
                       " as such instead of being an off-metal striking of a Ducat.")
        self.assertFalse(excluded(meta, desc))


if __name__ == "__main__":
    unittest.main()
