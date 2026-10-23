"""A Danish king's name is written one way, and the seed writer writes it.

Sources spell the same king «Christian 4» (KMM, IKMK, ucoin), «Christian IV»
(Numista, Bruun), «Christian 4.» (Galster), «Frederick III» (Numista). The
canonical display form «Name Roman.» (Hede's) was applied in June 2026 to
data/v2/final/* only (7e95732, 917b7a6, a777b9a), so every seed kept its
source's spelling — measured 2026-10-23: «Frederik 3» 1 074× in the KMM seed of
danish_norway, 410× in seed_unified, 60× in final — and a final rebuilt from its
members lost the form. `lib.ruler_reigns.canonical_ruler_display` is the rule;
the merger applies it (`_canonical_ruler_out`, curator 2026-10-23: a seed keeps
the source's spelling, the merger knows the entity). The scope is the
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
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import merge_seeds_cross_source as M  # noqa: E402
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


class Merger(unittest.TestCase):
    """The merger writes the form into seed_unified, by the file's entity
    (curator 2026-10-23); the seed keeps the source's spelling."""

    def _out(self, ruler, entity, **member):
        out = {"ruler": ruler}
        M._canonical_ruler_out(out, [dict(member, ruler=ruler)], entity)
        return out

    def test_applies_by_entity(self):
        self.assertEqual(self._out("Frederik 3", "danish_realm"), {"ruler": "Frederik III."})
        self.assertEqual(self._out("Frederik 3", "gottorp_duchy"), {"ruler": "Frederik 3"})

    def test_christian_ii_entities(self):
        for e in ("christian_ii_reconquest", "christian_ii_supporters"):
            self.assertEqual(self._out("Christian 2", e)["ruler"], "Christian II.", e)
            self.assertEqual(self._out("Christian II", e)["ruler"], "Christian II.", e)

    def test_doubt_flips_the_flag_unless_held(self):
        self.assertEqual(self._out("Christian 3?", "danish_norway"),
                         {"ruler": "Christian III.", "ruler_verified": False})
        held = self._out("Christian 3?", "danish_norway",
                         _curation_holds={"ruler_verified": "curator"})
        self.assertEqual(held, {"ruler": "Christian III."})

    def test_years_settle_a_doubted_king(self):
        # «Christian 3?» on a coin dated 1541 — the years are Christian III's.
        out = {"ruler": "Christian 3?", "year_first": 1541, "year_last": 1541}
        M._canonical_ruler_out(out, [{"ruler": "Christian 3?"}], "danish_realm")
        self.assertEqual(out, {"ruler": "Christian III.", "year_first": 1541, "year_last": 1541})
        # the years name ANOTHER king than the source guessed: the years win
        out = {"ruler": "Christian 3?", "year_first": 1600, "year_last": 1602}
        M._canonical_ruler_out(out, [{"ruler": "Christian 3?"}], "danish_realm")
        self.assertEqual(out["ruler"], "Christian IV.")
        self.assertNotIn("ruler_verified", out)

    def test_years_that_prove_nothing_keep_the_doubt(self):
        # an undated coin whose span is the guessed king's own reign
        out = {"ruler": "Hans?", "year_first": 1483, "year_last": 1513}
        M._canonical_ruler_out(out, [{"ruler": "Hans?"}], "danish_realm")
        self.assertEqual((out["ruler"], out["ruler_verified"]), ("Hans", False))
        # a span that crosses two reigns
        out = {"ruler": "Frederik 3?", "year_first": 1645, "year_last": 1652}
        M._canonical_ruler_out(out, [{"ruler": "Frederik 3?"}], "danish_realm")
        self.assertEqual((out["ruler"], out["ruler_verified"]), ("Frederik III.", False))
        # unverified years
        out = {"ruler": "Christian 3?", "year_first": 1541, "year_last": 1541}
        M._canonical_ruler_out(out, [{"ruler": "Christian 3?", "year_verified": False}], "danish_realm")
        self.assertEqual(out["ruler_verified"], False)

    def test_ruler_hold_freezes_the_spelling(self):
        self.assertEqual(self._out("Frederik 3", "danish_realm", _curation_holds=["ruler"]),
                         {"ruler": "Frederik 3"})


class WriterKeepsSourceForm(unittest.TestCase):
    def test_hygiene_pass_leaves_the_ruler(self):
        kept, stats = W._apply_pre_write_hygiene([
            {"id": "a", "issuing_entity": "danish_realm", "ruler": "Christian 5",
             "nominal": "1 Krone", "metal": "silver"}])
        self.assertEqual(kept[0]["ruler"], "Christian 5")
        self.assertNotIn("ruler_canonicalised", stats)


class ReignRulesUnchanged(unittest.TestCase):
    def test_christian_ii_entities_stay_out_of_reign_rules(self):
        from lib.ruler_reigns import DANISH_CROWN_ENTITIES, DISPLAY_NAME_ENTITIES
        self.assertNotIn("christian_ii_reconquest", DANISH_CROWN_ENTITIES)
        self.assertIn("christian_ii_reconquest", DISPLAY_NAME_ENTITIES)


if __name__ == "__main__":
    unittest.main()
