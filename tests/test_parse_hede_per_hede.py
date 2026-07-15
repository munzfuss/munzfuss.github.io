"""Unit tests for the per-sub-variant Hede extraction added to parse_hede.

The multi-nominal Hede page bug: a page documenting «4 Mark (Hede 100AB)» +
«8 Mark (Hede 101)» from the same dies used to give BOTH sub-entries the
page-level year (1559) + the merged catalog (both variants' Schou/Sieg). The
fix teaches `_extract_specs` to attach each `by_hede` entry its OWN year(s) +
catalog refs from the descriptive «(Hede N, Schou …, Sieg …)» groups, matching
sub-letter tags («100A»/«100B») to the combined spec-table key («100AB»).

Run:  .venv/bin/python -m unittest tests.test_parse_hede_per_hede -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import parse_hede as ph  # noqa: E402


class SplitHedeKey(unittest.TestCase):
    def test_split(self):
        self.assertEqual(ph._split_hede_key("100AB"), ("100", "AB"))
        self.assertEqual(ph._split_hede_key("101"), ("101", ""))
        self.assertEqual(ph._split_hede_key("84A"), ("84", "A"))
        self.assertEqual(ph._split_hede_key("39"), ("39", ""))


class DescHedeGroups(unittest.TestCase):
    def test_multi_nominal_f3h100_shape(self):
        """f3h100: «4 Mark» A)/B) → Hede 100A/100B; «8 Mark» → Hede 101."""
        desc = (
            "4 Mark\n"
            "A) 1559; stenen bryder ringen (Hede 100A, Schou 33-35, Sieg 53)\n"
            "B) 1559 (S), 1660 (RR); stenen bryder ikke ringen (Hede 100B, Schou 36 og 23, Sieg 53)\n"
            "8 Mark (2 Krone)\n"
            "1659; (Hede 101, Schou 31, Sieg 54)\n"
        )
        g = ph._extract_desc_hede_groups(desc)
        # Hede 101 (the 8 Mark) is dated 1659, carries ONLY Schou 31 / Sieg 54
        self.assertEqual({y["year"] for y in g["101"]["years"]}, {1659})
        self.assertEqual(g["101"]["catalog_refs"].get("Schou"), ["31"])
        self.assertEqual(g["101"]["catalog_refs"].get("Sieg"), ["54"])
        # Hede 100A carries Schou 33-35 / Sieg 53, NOT the 8 Mark's 31/54
        self.assertEqual(g["100A"]["catalog_refs"].get("Sieg"), ["53"])
        self.assertNotIn("31", g["100A"]["catalog_refs"].get("Schou", []))

    def test_year_isolation(self):
        """Each sub-variant's years come from its own block, not the union."""
        desc = (
            "3 Speciedaler\n"
            "1624 (R), 1627 (Unik), 1628 (Unik).\n"
            "(Hede 57, Schou hhv. 3-4, 4 og 9, Sieg 125)\n"
            "1624, 1627 (Unik).\n"
            "(Hede 58, Schou hhv. 1-2 og 3, Sieg 126)\n"
        )
        g = ph._extract_desc_hede_groups(desc)
        self.assertEqual({y["year"] for y in g["57"]["years"]}, {1624, 1627, 1628})
        self.assertEqual({y["year"] for y in g["58"]["years"]}, {1624, 1627})
        self.assertEqual(g["57"]["catalog_refs"]["Sieg"], ["125"])
        self.assertEqual(g["58"]["catalog_refs"]["Sieg"], ["126"])

    def test_cross_ref_not_a_group(self):
        """«Som Hede 84A» is a cross-reference, not a catalog group — the real
        group «(Hede 85, Schou 12-14, Sieg 43)» must win for tag 85."""
        desc = (
            "4 Mark\n"
            "A) 1651, 1652; Valgsprog (Hede 84A, Schou hhv. 15-33 og 12-18, Sieg 42.2)\n"
            "1651, (R); Som Hede 84A (Hede 85, Schou 12-14, Sieg 43)\n"
        )
        g = ph._extract_desc_hede_groups(desc)
        self.assertIn("85", g)
        self.assertEqual(g["85"]["catalog_refs"]["Schou"], ["12-14"])
        self.assertEqual(g["85"]["catalog_refs"]["Sieg"], ["43"])

    def test_schou_mangler(self):
        """«Schou mgl.» (Schou missing) yields no Schou ref for that Hede."""
        desc = (
            "3 Speciedaler\n"
            "1661 (Unik); Som Hede 57B (Hede 59, Schou mgl., Sieg 77)\n"
        )
        g = ph._extract_desc_hede_groups(desc)
        self.assertEqual(g["59"]["catalog_refs"].get("Sieg"), ["77"])
        self.assertFalse(g["59"]["catalog_refs"].get("Schou"))


class LooksLikeDenom(unittest.TestCase):
    def test_accept_real_denoms(self):
        self.assertTrue(ph._looks_like_denom("2 speciedaler"))
        self.assertTrue(ph._looks_like_denom("4 mark"))
        self.assertTrue(ph._looks_like_denom("1 reichsthaler courant"))
        self.assertTrue(ph._looks_like_denom("2 dukat 1687"))  # trailing year stripped

    def test_reject_prose(self):
        # DENOM_LABEL_RE over-captures «2 Dukaten findes i to varianter» on f5h1
        self.assertFalse(ph._looks_like_denom("2 dukaten findes i to varianter"))
        self.assertFalse(ph._looks_like_denom(""))
        self.assertFalse(ph._looks_like_denom("speciedaler"))  # no leading number


_CACHE = Path(__file__).resolve().parents[1] / "scripts" / "cache" / "hede"


@unittest.skipUnless((_CACHE / "f3h62.htm").exists(),
                     "hede cache submodule not present")
class ByHedeNominalIntegration(unittest.TestCase):
    """Regression guards for the off-strike (Guldafslag/Sølvafslag) + combined-
    key nominal handling — validated against the real danskmoent cache."""

    def _noms(self, pid):
        html = (_CACHE / f"{pid}.htm").read_text(encoding="utf-8", errors="replace")
        bh = (ph.parse_one(html, pid).get("specs") or {}).get("by_hede") or {}
        return {k: v.get("nominal") for k, v in bh.items()}

    def test_f3h62_multidenom_guldafslag_between_sections(self):
        # «1/2/3/4 Speciedaler» with a Guldafslag block between each section —
        # the aside must not swallow the next «N Speciedaler» header.
        n = self._noms("f3h62")
        self.assertEqual(n.get("62AB"), "2 speciedaler")
        self.assertEqual(n.get("63"), "3 speciedaler")
        self.assertEqual(n.get("64"), "4 speciedaler")

    def test_c5h15_solvafslag_before_dukat_maindenom(self):
        # «Sølvafslag Schou 1a (RRR).» precedes the real «2 Dukat» header on a
        # page whose OWN denomination is the Dukat — must not be suppressed.
        self.assertEqual(self._noms("c5h15").get("15"), "2 dukat 1687")

    def test_f5h1_prose_not_a_nominal(self):
        # «2 Dukaten findes i to varianter» is prose, not a combined nominal.
        self.assertIsNone(self._noms("f5h1").get("2AB"))

    def test_f3h100_ebenezer_8mark(self):
        n = self._noms("f3h100")
        self.assertEqual(n.get("100AB"), "4 mark")
        self.assertEqual(n.get("101"), "8 mark")


if __name__ == "__main__":
    unittest.main()
