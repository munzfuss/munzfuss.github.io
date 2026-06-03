"""Regression guard for build_bruun_denmark_seed.parse_metal.

Bruun does NOT state the metal directly — parse_metal infers it. The contract
(curator decision 2026-06-03):

  * verified=True ONLY for RELIABLE signals — a Friedberg ref (gold by catalogue
    definition) or an explicit metal WORD in the nominal («silver»/«sølv» →
    silver; «gold»/«guldkrone»/«guldgylden»/«guldreal» → gold).
  * EVERY denomination-name heuristic (Ducat→gold, Mark→silver, Krone→…,
    Skilling→billon, 10/20 Kroner→gold) → verified=False, a WEAK signal that
    per CLAUDE.md §4 cannot block a cross-source merge and is overridden by a
    source-attested metal.

Two traps this pins down:
  * «Sølvgylden» / «Silver Gulden» MUST be silver (silver-precedence, matched
    broadly) — never fall through to a gold heuristic.
  * «Guldengroschen» (a SILVER Guldiner) MUST NOT be read as gold — so the gold
    word-match is «gold» + specific guld-compounds, never bare «guld».

Run:  .venv/bin/python -m unittest tests.test_parse_metal -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "build_bruun_denmark_seed", ROOT / "scripts" / "maintenance" / "build_bruun_denmark_seed.py")
_bbd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bbd)
parse_metal = _bbd.parse_metal


class TestReliableSignalsVerified(unittest.TestCase):
    """Friedberg ref + explicit metal word → verified=True."""

    def test_friedberg_ref_is_gold_verified(self):
        self.assertEqual(parse_metal("Krone", {"friedberg": "94"}), ("gold", True))
        self.assertEqual(parse_metal("1 Portugaløser", {"friedberg": "66"}), ("gold", True))

    def test_explicit_silver_word_verified(self):
        for nom in ("1 Sølvgylden", "Halv Sølvgylden", "1½ Sølvgylden",
                    "1 Silver Gulden", "½ Silver Gulden", "sølvafslag af 10 Dukat"):
            self.assertEqual(parse_metal(nom, {}), ("silver", True), nom)

    def test_explicit_gold_word_verified(self):
        for nom in ("1 Goldgulden", "1 Gold Gulden", "Gold Krone", "Guldkrone",
                    "Guldgylden", "1 Rhinsk gylden-guldkrone"):
            self.assertEqual(parse_metal(nom, {}), ("gold", True), nom)


class TestSilverPrecedenceTraps(unittest.TestCase):
    """The «Sølvgylden» caution + the «Guldengroschen» (silver Guldiner) trap."""

    def test_solvgylden_never_gold(self):
        # contains «gylden» but is SILVER — silver word must win
        self.assertEqual(parse_metal("1 Sølvgylden", {})[0], "silver")
        self.assertEqual(parse_metal("halv sølvgylden", {})[0], "silver")

    def test_guldengroschen_is_silver_not_gold(self):
        # «Guldengroschen» = the large SILVER Guldiner; bare «guld» must NOT
        # trigger gold.
        self.assertEqual(parse_metal("1 Guldengroschen", {})[0], "silver")
        self.assertEqual(parse_metal("½ Guldengroschen", {})[0], "silver")


class TestHeuristicsAreWeak(unittest.TestCase):
    """Denomination-name inferences → verified=False (the §4 weak signal that
    unblocks silver/gold split-cluster merges)."""

    def test_silver_krone_mark_unverified(self):
        for nom in ("1 Krone", "2 Krone", "2 Kroner", "3 Krone", "4 Mark", "½ Krone"):
            metal, verified = parse_metal(nom, {})
            self.assertEqual(metal, "silver", nom)
            self.assertFalse(verified, f"{nom}: heuristic metal must be verified=False")

    def test_gold_standard_kroner_unverified_gold(self):
        for nom in ("10 Kroner", "20 Kroner"):
            self.assertEqual(parse_metal(nom, {}), ("gold", False), nom)

    def test_gold_denomination_names_unverified(self):
        for nom in ("1 Ducat", "2 Dukat", "1 Frederik d'Or", "1 Portugaløser",
                    "1 Ungersk Gylden", "1 Ungarsk gylden", "1 Pistole"):
            metal, verified = parse_metal(nom, {})
            self.assertEqual(metal, "gold", nom)
            self.assertFalse(verified, f"{nom}: heuristic gold must be verified=False")

    def test_skilling_billon_unverified(self):
        metal, verified = parse_metal("8 Skilling", {})
        self.assertEqual(metal, "billon")
        self.assertFalse(verified)


class TestEdgeCases(unittest.TestCase):
    def test_no_denom_no_ref_silver_unverified(self):
        self.assertEqual(parse_metal(None, {}), ("silver", False))
        self.assertEqual(parse_metal("", {}), ("silver", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
