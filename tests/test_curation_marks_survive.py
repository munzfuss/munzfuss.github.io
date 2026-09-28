"""The (§) marks on the Nobel went missing from the page, and nothing complained.

A curation mark — `erroneous` «(!)», `suspect` «(*)», `template` «(§)» — sits
on the SEED reading of the source that published it. The merger copied the
marks by a hard-coded ("erroneous", "suspect"), written before `template`
existed, so every seed_unified dropped the (§) marks and every absorb then
stripped them from final. The thinner had the same two-kind list and would
have deleted a (§) reading on a coin with ≥5 readings from one source. Found
2026-09-28 after an unrelated absorb erased the Nobel 14,375 g / .979 marks;
both sites now read `seed_merge._CURATION_MARK_KEYS`. The corpus-level guard is
pre-commit Check 10 (`audit_curation_marks.py`); these are the unit halves.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.seed_merge import _CURATION_MARK_KEYS  # noqa: E402
from merge_seeds_cross_source import _collect_field_list  # noqa: E402
from thin_final_weight_lists import thin_coin  # noqa: E402

REASON = {"de": "x", "en": "x", "uk": "x", "da": "x"}


class MergerCarriesEveryMark(unittest.TestCase):
    def test_each_kind_reaches_the_merged_list(self):
        for kind in _CURATION_MARK_KEYS:
            with self.subTest(kind=kind):
                members = [{"id": "dk-galster-f1g-45",
                            "weight_rough_g": [{"value": 14.375, "source": "galster",
                                                kind: REASON}]}]
                out = _collect_field_list(members, "weight_rough_g")
                self.assertEqual(len(out), 1)
                self.assertEqual(out[0].get(kind), REASON)

    def test_mark_wins_over_unmarked_duplicate(self):
        for kind in _CURATION_MARK_KEYS:
            with self.subTest(kind=kind):
                members = [
                    {"id": "dk-galster-f1g-45",
                     "weight_rough_g": [{"value": 14.375, "source": "galster"}]},
                    {"id": "dk-galster-f1g-69",
                     "weight_rough_g": [{"value": 14.375, "source": "galster",
                                         kind: REASON}]},
                ]
                out = _collect_field_list(members, "weight_rough_g")
                self.assertEqual(len(out), 1)
                self.assertEqual(out[0].get(kind), REASON)


class ThinnerKeepsEveryMark(unittest.TestCase):
    def test_marked_middle_reading_is_never_dropped(self):
        for kind in _CURATION_MARK_KEYS:
            with self.subTest(kind=kind):
                ws = [{"value": v, "source": "kmk"} for v in (13.0, 13.1, 13.2, 13.3, 13.4, 13.5)]
                ws[2][kind] = REASON          # a middle reading the envelope would drop
                coin = {"id": "t", "weight_rough_g": ws}
                thin_coin(coin)
                kept = [e for e in coin["weight_rough_g"] if e.get(kind)]
                self.assertEqual(len(kept), 1, f"{kind} reading was thinned away")

    def test_thinning_is_a_fixed_point(self):
        ws = [{"value": 13.0 + i / 10, "source": "kmk"} for i in range(7)]
        coin = {"id": "t", "weight_rough_g": ws}
        self.assertGreater(thin_coin(coin), 0)
        self.assertEqual(thin_coin(coin), 0)


if __name__ == "__main__":
    unittest.main()
