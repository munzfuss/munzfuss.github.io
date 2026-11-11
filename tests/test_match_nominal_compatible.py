"""Two names of one denomination lift the pair matcher's nominal veto
(curator 2026-11-11): source-declared dual names, a simplification of the
same name, a spelling. «lybsk» stays out for now. The names give no vote:
`primary["nominal"]` is None, not True.

Run:
    .venv/bin/python -m unittest tests.test_match_nominal_compatible -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402

N = M._normalise_nominal


def ok(a, b):
    return M._match_nominal_compatible.__wrapped__(N(a), N(b), a.lower(), b.lower())


class Compatible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        M._collect_declared_nominal_equiv([
            {"id": "dk-hede-c7h42", "nominal": "1/6 Speciedaler/10 Schilling Schleswig-holsteinischer Courant"},
            {"id": "dk-bruun-6485", "nominal": "⅛ Reichsdaler (6 Skilling Lybsk)"},
        ])

    def test_simplifications(self):
        for a, b in (("8 skilling", "8 krone-skilling"), ("4 skilling rigsmont", "4 skilling"),
                     ("speciedaler", "daler"), ("skilling", "kurantskilling"),
                     ("2 rigsbankskilling", "rigsbanktegn for 2 skilling")):
            self.assertTrue(ok(a, b), (a, b))

    def test_spellings(self):
        self.assertTrue(ok("2 christian d'or", "2 christiandor"))
        self.assertTrue(ok("2 skilling", "toskilling"))

    def test_source_declared_pair(self):
        self.assertTrue(ok("1/6 speciedaler", "10 skilling"))
        self.assertTrue(ok("1/24 speciedaler",
                           "1/24 speciedaler/2 1/2 skilling schleswig-holsteinischer kurant"))

    def test_lybsk_left_out_of_cross_unit_pairs(self):
        self.assertFalse(ok("1/8 reichsdaler", "6 skilling lybsk"))

    def test_bare_name_against_its_lybsk_form(self):
        for a, b in (("sosling lybsk", "sosling"), ("skilling lybsk", "skilling"),
                     ("blaffert", "lybsk blaffert"), ("lybsk blaffert", "blaffert lybsk"),
                     ("sosling lybsk", "sechsling"), ("3 skilling lybsk", "3 skilling")):
            self.assertTrue(ok(a, b), (a, b))

    def test_lybsk_against_dansk_or_another_count_stays_apart(self):
        for a, b in (("2 skilling lybsk", "2 skilling dansk"), ("2 skilling lybsk", "4 skilling"),
                     ("1 skilling lybsk", "1 skilling norsk")):
            self.assertFalse(ok(a, b), (a, b))

    def test_real_differences_stay(self):
        for a, b in (("2 skilling", "4 skilling"), ("1 dukat", "2 dukat"),
                     ("speciedaler", "1/2 speciedaler"), ("16 skilling", "gold 16 skilling"),
                     ("1 krone", "1 skilling")):
            self.assertFalse(ok(a, b), (a, b))

    def test_no_vote_in_match_pair(self):
        a = {"id": "a", "nominal": "4 Skilling Rigsmont", "metal": "silver", "metal_verified": True,
             "ruler": "Christian VII", "year_first": 1770, "year_last": 1770}
        b = {"id": "b", "nominal": "4 Skilling", "metal": "silver", "metal_verified": True,
             "ruler": "Christian VII", "year_first": 1770, "year_last": 1770}
        r = M.match_pair(a, b, "danish_realm")
        self.assertIsNone(r["primary"]["nominal"])
        self.assertNotEqual(r["decision"], "no_match")


class DanskeForm(unittest.TestCase):
    def test_one_spelling(self):
        for n in ("8 Skilling dansk", "8 Skilling Dansk", "8 Skilling danske", "8 Skilling, dansk"):
            self.assertEqual(M._danske_form(n), "8 Skilling Danske", n)
        self.assertEqual(M._danske_form("4 Marck dansk"), "4 Marck Danske")
        self.assertEqual(M._danske_form("2 Skilling Lybsk"), "2 Skilling Lybsk")
        self.assertEqual(M._danske_form("1 Denning = ½ Skilling Dansk"), "1 Denning = ½ Skilling Danske")


if __name__ == "__main__":
    unittest.main()
