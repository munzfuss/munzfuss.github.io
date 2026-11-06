"""Hede-base rule: nominal equivalences come from the sources themselves
(curator 2026-11-05). A raw nominal «A = B» / «A (B)» / «A / B» declares one
value under two names; the declaration is used only inside the Hede-base group
check, pair by pair, never chained. Off-strikes and forgeries never match.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "maintenance")]

import merge_seeds_cross_source as m  # noqa: E402


class DeclaredPairs(unittest.TestCase):
    def test_gloss_forms(self):
        self.assertEqual(m._declared_nominal_pairs("⅛ Speciedaler (12 Skilling)"),
                         [("1/8 speciedaler", "12 skilling")])
        self.assertEqual(m._declared_nominal_pairs("12 Mark = 3 Kroner"),
                         [("12 mark", "3 krone")])
        self.assertEqual(m._declared_nominal_pairs("4 Mark / Krone"), [("4 mark", "krone")])
        self.assertIn(("16 skilling", "mark"),
                      m._declared_nominal_pairs("16 Skilling = 1 Mark (1/6 Speciedaler)"))

    def test_fraction_is_not_a_gloss(self):
        self.assertEqual(m._declared_nominal_pairs("½ Skilling"), [])
        self.assertEqual(m._declared_nominal_pairs("1/4 Speciedaler"), [])


class Equivalence(unittest.TestCase):
    def setUp(self):
        self._saved = dict(m._DECLARED_NOMINAL_EQUIV)
        m._DECLARED_NOMINAL_EQUIV.clear()
        m._collect_declared_nominal_equiv([
            {"id": "a", "nominal": "16 Skilling = 1 Mark"},
            {"id": "b", "nominal": "1 Dukat (12 Mark)"},
            {"id": "c", "nominal": "1 Dukat (14 Mark)"},
        ])

    def tearDown(self):
        m._DECLARED_NOMINAL_EQUIV.clear()
        m._DECLARED_NOMINAL_EQUIV.update(self._saved)

    def test_declared(self):
        self.assertTrue(m._hede_base_nominal_equiv("16 skilling", "mark").startswith("source a"))

    def test_declared_through_bare_unit(self):
        self.assertIsNotNone(m._hede_base_nominal_equiv("kurantdukat", "12 mark"))

    def test_no_chaining(self):
        self.assertIsNone(m._hede_base_nominal_equiv("12 mark", "14 mark"))

    def test_undeclared_stays_apart(self):
        self.assertIsNone(m._hede_base_nominal_equiv("2 skilling", "skilling"))

    def test_off_strike_never_matches(self):
        self.assertIsNone(m._hede_base_nominal_equiv("skilling", "guldafslag af skilling"))

    def test_dual_name(self):
        self.assertEqual(m._hede_base_nominal_equiv("speciedaler / 3 mark", "3 mark"), "dual name")


class Spelling(unittest.TestCase):
    """Spelling noise folded for the comparison only (curator 2026-11-05)."""

    def eq(self, a, b):
        return m._hede_base_nominal_equiv(a, b)

    def test_number_words(self):
        self.assertEqual(self.eq("toskilling", "2 skilling"), "spelling")
        self.assertIsNone(self.eq("toskilling", "4 skilling"))

    def test_word_forms(self):
        self.assertEqual(self.eq("gold krone", "goldkrone"), "spelling")
        self.assertEqual(self.eq("gold krone", "krone"), "spelling")
        self.assertEqual(self.eq("penning", "penny"), "spelling")
        self.assertEqual(self.eq("2 christian d'or", "2 christiandor"), "spelling")
        self.assertEqual(self.eq("dukat", "dukat kobenhavn"), "spelling")

    def test_qualifiers(self):
        self.assertEqual(self.eq("lybsk blaffert", "blaffert lybsk"), "spelling")
        self.assertEqual(self.eq("sosling", "sosling lybsk"), "spelling")
        self.assertIsNone(self.eq("2 skilling norsk", "2 skilling lybsk"))

    def test_rigsbanktegn_forms(self):
        self.assertEqual(self.eq("rigsbanktegn for 4 skilling", "4 rigsbankskilling rigsbanktegn"),
                         "spelling")
        self.assertEqual(self.eq("4 skilling rigbanktegn", "rigsbanktegn 4 skilling"), "spelling")

    def test_doubt_and_empty_names(self):
        self.assertEqual(self.eq("2 skilling?", "2 skilling"), "uncertain")
        self.assertIsNone(self.eq("2 speciedaler", "1"))

    def test_sechsling_is_sosling(self):
        self.assertEqual(self.eq("sechsling", "sosling lybsk"), "spelling")
        self.assertEqual(self.eq("sechling", "sosling"), "spelling")
        self.assertEqual(self.eq("secholing", "sechsling"), "spelling")

    def test_other_strikes_stay_apart(self):
        self.assertIsNone(self.eq("16 skilling", "gold 16 skilling"))
        self.assertIsNone(self.eq("2 skilling; samtidig forfalskning?", "2 skilling"))

    def test_declared_pair_in_source_spelling(self):
        saved = dict(m._DECLARED_NOMINAL_EQUIV)
        try:
            m._DECLARED_NOMINAL_EQUIV.clear()
            m._collect_declared_nominal_equiv([
                {"id": "a", "nominal": "⅛ Reichsdaler (6 Skilling Lybsk)"},
                {"id": "b", "nominal": "1 Sechsling = 6 Pfennig"},
                {"id": "c", "nominal": "1/6 Speciedaler/10 Schilling Schleswig-holsteinischer Courant"},
            ])
            self.assertTrue(self.eq("1/8 reichsdaler", "6 skilling lybsk").startswith("source a"))
            self.assertTrue(self.eq("sosling lybsk", "6 pfennig").startswith("source b"))
            self.assertTrue(self.eq("1/6 speciedaler", "10 skilling").startswith("source c"))
            m._collect_declared_nominal_equiv([
                {"id": "d", "nominal": "2 Skilling Lybsk = 4 Skilling Dansk"}])
            self.assertTrue(self.eq("2 skilling lybsk", "4 skilling dansk").startswith("source d"))
            self.assertIsNone(self.eq("4 skilling", "2 skilling"))
        finally:
            m._DECLARED_NOMINAL_EQUIV.clear()
            m._DECLARED_NOMINAL_EQUIV.update(saved)

    def test_real_differences_stay(self):
        self.assertIsNone(self.eq("skilling", "2 skilling"))
        self.assertIsNone(self.eq("1/2 skilling", "2 skilling"))


if __name__ == "__main__":
    unittest.main()
