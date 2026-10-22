"""A Danish king's name is written one way, and the seed writer writes it.

Sources spell the same king «Christian 4» (KMM, IKMK, ucoin), «Christian IV»
(Numista, Bruun), «Christian 4.» (Galster), «Frederick III» (Numista). The
canonical display form «Name Roman.» (Hede's) was applied in June 2026 to
data/v2/final/* only (7e95732, 917b7a6, a777b9a), so every seed kept its
source's spelling — measured 2026-10-23: «Frederik 3» 1 074× in the KMM seed of
danish_norway, 410× in seed_unified, 60× in final — and a final rebuilt from its
members lost the form. `lib.ruler_reigns.canonical_ruler_display` is the rule,
`v2_seed_writer._canonicalise_ruler` applies it at the writer. The scope is the
June one: Danish-crown entities only, bare king forms only; «Friedrich» and
«Johann» stay (curator 2026-10-23).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib import v2_seed_writer as W  # noqa: E402
from lib.ruler_reigns import canonical_ruler_display as cd  # noqa: E402


class Rule(unittest.TestCase):
    def test_arabic_roman_period_english_forms(self):
        for raw in ("Christian 4", "Christian IV", "Christian 4.", "Christian iv", "Christian  4"):
            self.assertEqual(cd(raw, "danish_realm"), ("Christian IV.", False), raw)
        self.assertEqual(cd("Frederick III", "danish_norway"), ("Frederik III.", False))
        self.assertEqual(cd("Christian 10", "danish_realm"), ("Christian X.", False))
        self.assertEqual(cd("Frederik4", "royal_holstein"), ("Frederik IV.", False))
        self.assertEqual(cd("Eric VII", "danish_realm"), ("Erik VII.", False))

    def test_uncertain_marker(self):
        self.assertEqual(cd("Frederik 3?", "danish_realm"), ("Frederik III.", True))
        self.assertEqual(cd("Hans?", "danish_realm"), ("Hans", True))

    def test_hans_forms(self):
        for raw in ("Hans", "John I", "Johan", "Hans I"):
            self.assertEqual(cd(raw, "danish_realm"), ("Hans", False), raw)
        self.assertEqual(cd("Hans II", "danish_realm"), ("Hans II", False))

    def test_untouched(self):
        for raw in ("Friedrich I", "Johann", "Karl Frederik",
                    "Frederik 3 af Slesvig-Holsten-Gottorp",
                    "Frederick III (Frederik III)", "Christian I/Hans",
                    "Christian", "Rigsrådet", "?"):
            self.assertEqual(cd(raw, "danish_realm"), (raw, False), raw)
        self.assertEqual(cd("Frederik 3", "gottorp_duchy"), ("Frederik 3", False))
        self.assertEqual(cd("Frederik 3", "norway"), ("Frederik 3", False))
        self.assertEqual(cd(None, "danish_realm"), (None, False))

    def test_already_canonical_is_a_fixed_point(self):
        self.assertEqual(cd("Christian IV.", "danish_realm"), ("Christian IV.", False))


class Writer(unittest.TestCase):
    def test_applies_by_home_entity(self):
        c = {"id": "x", "issuing_entity": "danish_realm", "ruler": "Frederik 3"}
        self.assertTrue(W._canonicalise_ruler(c))
        self.assertEqual(c["ruler"], "Frederik III.")
        self.assertNotIn("ruler_verified", c)
        g = {"id": "y", "issuing_entity": "gottorp_duchy", "ruler": "Frederik 3"}
        self.assertFalse(W._canonicalise_ruler(g))
        self.assertEqual(g["ruler"], "Frederik 3")

    def test_doubt_flips_the_flag_unless_held(self):
        c = {"id": "x", "issuing_entity": "danish_norway", "ruler": "Christian 3?",
             "ruler_verified": True}
        self.assertTrue(W._canonicalise_ruler(c))
        self.assertEqual((c["ruler"], c["ruler_verified"]), ("Christian III.", False))
        h = {"id": "x", "issuing_entity": "danish_norway", "ruler": "Christian 3?",
             "ruler_verified": True, "_curation_holds": {"ruler_verified": "curator"}}
        W._canonicalise_ruler(h)
        self.assertEqual((h["ruler"], h["ruler_verified"]), ("Christian III.", True))

    def test_ruler_hold_freezes_the_spelling(self):
        c = {"id": "x", "issuing_entity": "danish_realm", "ruler": "Frederik 3",
             "_curation_holds": ["ruler"]}
        self.assertFalse(W._canonicalise_ruler(c))
        self.assertEqual(c["ruler"], "Frederik 3")

    def test_hygiene_pass_counts_it(self):
        kept, stats = W._apply_pre_write_hygiene([
            {"id": "a", "issuing_entity": "danish_realm", "ruler": "Christian 5",
             "nominal": "1 Krone", "metal": "silver"}])
        self.assertEqual(kept[0]["ruler"], "Christian V.")
        self.assertEqual(stats.get("ruler_canonicalised"), 1)


if __name__ == "__main__":
    unittest.main()
