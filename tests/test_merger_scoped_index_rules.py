"""Records that share a scoped catalogue index must merge — and the arguments
against a merge must still be heard.

Found 2026-10-17 (docs/undated_coins_denmark.md row 4): KMM specimens carrying
the same Hede/Schou index as a classified coin stayed in separate classes —
Christian IV Hede 139A came out in eleven classes, Hede 134 in twenty-six.
Four causes, each fixed here with the curator's rule:

  * «Schou 32» against a Hede page's «Schou 29-32» counted as disagreement
    (number inside a range of the same sub-variant catalogue = match; but
    a museum's «Hede 21-23» is «one of three types», not a range);
  * catalogue + nominal + ruler agreeing with year and metal unknown was
    left undecided (now enough — nothing disagreed);
  * billon against silver, both attested, vetoed (not an obstacle);
  * PASS 2 turned every `no_match` inside a component into a transitive veto,
    so a WEAK contradiction between two thin records (different Schou only,
    a different year, a worn weight) split a type whose Hede page lists both.

And the curator's counterweight: an argument for a merge must not override a
stronger one against. A different nominal or a different type-level index is
never overruled, and a match resting only on a Schou number that two Hede types
list (Christian IV 2 Guldkrone: Schou 2 in Hede 25 and in Hede 28) is not
evidence — Schou restarts per type.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import merge_seeds_cross_source as M  # noqa: E402

ENT = "danish_realm"


def coin(cid, nominal="6 Skilling", **kw):
    c = {"id": cid, "nominal": nominal, "ruler": "Christian IV",
         "issuing_entity": ENT, "catalog": kw.pop("catalog", {})}
    c.update(kw)
    return c


class TestRanges(unittest.TestCase):
    def test_schou_number_inside_range(self):
        self.assertEqual(M._catalog_chain_consistent(
            {"schou/christian iv": "32"}, {"schou/christian iv": "29-32"})[0], "agree")

    def test_type_level_range_is_not_a_range_of_variants(self):
        self.assertEqual(M._catalog_chain_consistent(
            {"hede/frederik vi": "22"}, {"hede/frederik vi": "21-23"})[0], "disagree")


class TestPairRules(unittest.TestCase):
    def setUp(self):
        M._SUBVAR_CLAIMS = {}

    def test_index_nominal_ruler_without_year_or_metal(self):
        a = coin("a", catalog={"hede": "134"})
        b = coin("b", catalog={"hede": "134A"})
        self.assertEqual(M.match_pair(a, b, ENT)["decision"], "confident")

    def test_billon_silver_is_not_a_veto(self):
        a = coin("a", catalog={"hede": "134"}, metal="silver", metal_verified=True)
        b = coin("b", catalog={"hede": "134"}, metal="billon", metal_verified=True)
        self.assertNotEqual(M.match_pair(a, b, ENT)["decision"], "no_match")

    def test_ambiguous_schou_number_is_not_evidence(self):
        a = coin("a", "2 Guldkrone", catalog={"schou": "2"})
        b = coin("b", "2 Guldkrone", catalog={"schou": "1-4"})
        self.assertEqual(M.match_pair(a, b, ENT)["decision"], "confident")
        nom = M._normalise_nominal("2 Guldkrone")
        M._SUBVAR_CLAIMS = {("schou/christian iv", "2", nom):
                            {"hede/christian iv=25", "hede/christian iv=28"}}
        r = M.match_pair(a, b, ENT)
        self.assertIsNone(r["primary"]["catalog"])
        self.assertNotEqual(r["decision"], "confident")

    def test_weight_gate_widens_to_ten_percent_with_index(self):
        # A shared Hede already lifts the 5 % gate (older rule); the new one
        # covers an index that is not «authoritative», e.g. Schou alone. The
        # catalogues differ in shape so the «identical but for weight»
        # exemption does not apply either.
        a = coin("a", catalog={"schou": "50"}, weight_rough_g=1.771)
        b = coin("b", catalog={"schou": "50", "sieg": "57"}, weight_rough_g=1.650)
        self.assertNotEqual(M.match_pair(a, b, ENT)["decision"], "no_match")
        c = coin("c", catalog={"schou": "50", "sieg": "57"}, weight_rough_g=1.40)
        self.assertEqual(M.match_pair(a, c, ENT)["decision"], "no_match")


class TestKroneIsFourMark(unittest.TestCase):
    """Hede writes «4 Mark», NumisMaster / NGC / KMM «1 Krone» for one coin:
    not a contradiction — and not evidence for a merge either."""

    def test_equivalent_names(self):
        n = M._normalise_nominal
        self.assertTrue(M._nominal_equivalent(n("4 Mark"), n("1 Krone")))
        self.assertTrue(M._nominal_equivalent(n("8 Mark"), n("2 Krone")))
        self.assertFalse(M._nominal_equivalent(n("4 Mark"), n("2 Krone")))

    def test_neutral_in_a_pair(self):
        a = coin("a", "4 Mark", catalog={"hede": "104"})
        b = coin("b", "1 Krone", catalog={"km": "428.2"})
        self.assertIsNone(M.match_pair(a, b, ENT)["primary"]["nominal"])


class TestWeakVetoes(unittest.TestCase):
    """A Hede page listing «Schou 41-54» unifies a KMM «Schou 50» and a KMM
    «Schou 41» record; the veto between those two must not split the type."""

    def setUp(self):
        M._SUBVAR_CLAIMS = {}
        self.seeds = {
            "z": coin("z", catalog={"hede": "139A", "schou": ["41-54"]}),
            "x": coin("x", catalog={"schou": "50"}),
            "y": coin("y", catalog={"schou": "41"}),
            "w": coin("w", "8 Skilling", catalog={"schou": "41"}),
        }
        self.idx = M._WeakVetoIndex(sorted(self.seeds), self.seeds, ENT)

    def veto(self, a, b):
        r = M.match_pair(self.seeds[a], self.seeds[b], ENT)
        self.assertEqual(r["decision"], "no_match")
        return r

    def test_subvariant_veto_overruled_by_unifier(self):
        self.assertTrue(self.idx.overruled(self.veto("x", "y"), "x", "y"))

    def test_different_nominal_is_never_overruled(self):
        self.assertFalse(self.idx.overruled(self.veto("x", "w"), "x", "w"))

    def test_type_level_conflict_is_never_overruled(self):
        seeds = dict(self.seeds,
                     p=coin("p", catalog={"hede": "93A"}),
                     q=coin("q", catalog={"hede": "96"}))
        idx = M._WeakVetoIndex(sorted(seeds), seeds, ENT)
        r = M.match_pair(seeds["p"], seeds["q"], ENT)
        self.assertFalse(idx.overruled(r, "p", "q"))

    def test_weight_gap_hiding_a_different_index(self):
        # Christian V Ducats: Hede 29 (KM 414) at 3.71 g vs Hede 57 (KM 455)
        # at 3.49 g — match_pair names the weight first, the index differs too.
        seeds = {"x": coin("x", "1 Ducat", catalog={"hede": "29", "km": "414"}, weight_rough_g=3.71),
                 "y": coin("y", "1 Dukat", catalog={"hede": "57"}, weight_rough_g=3.49),
                 "z": coin("z", "1 Ducat", catalog={"hede": "57", "km": "414"})}
        idx = M._WeakVetoIndex(sorted(seeds), seeds, ENT)
        r = M.match_pair(seeds["x"], seeds["y"], ENT)
        self.assertEqual(r["decision"], "no_match")
        self.assertFalse(idx.overruled(r, "x", "y"))

    def test_weight_band_must_be_continuous(self):
        def build(extra):
            seeds = {"z": coin("z", catalog={"hede": "134A"}, weight_rough_g=1.30),
                     "x": coin("x", catalog={"schou": "65"}, weight_rough_g=1.0)}
            seeds.update(extra)
            return seeds, M._WeakVetoIndex(sorted(seeds), seeds, ENT)
        res = {"why": ["weight: 1.000g vs 1.300g — Δ > 5% AND catalog not strongly-agreeing"]}
        band = {f"s{i}": coin(f"s{i}", catalog={"hede": "134A"}, weight_rough_g=w)
                for i, w in enumerate((1.04, 1.08, 1.13, 1.18, 1.24))}
        seeds, idx = build(band)
        self.assertTrue(idx._continuous(idx.nom["x"], 1.0, 1.30))
        seeds, idx = build({})
        self.assertFalse(idx._continuous(idx.nom["x"], 1.0, 1.30))
        self.assertFalse(idx.overruled(res, "x", "z"))


if __name__ == "__main__":
    unittest.main()
