"""A seed that leaves a coin must take its own data with it — and only its own.

KMM 439647 printed the 3-Dukat type number on a 4-Dukat specimen; once a
`_source_errata` corrected it (2026-09-28) the seed merged into the 4 Dukat,
and its old class `unified-kmk-439647` vanished from seed_unified. absorb's
stale purge dropped the dangling id from the 3 Dukat's composed_of but left
what that seed had baked onto the host: the KMM source and «B# 5a». Absorb
unions sources and catalogue indices and never removes them, so they would
have stayed forever. `_surgical_decontaminate` already knew how to strip a
departed member's EXCLUSIVE contributions — but only two eviction paths called
it, and it did not touch the catalogue.

The curator's constraint: remove only what the departed source alone supplied.
A value a remaining member also attests is shared and must stay.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from absorb_seeds_into_final_v2 import _surgical_decontaminate  # noqa: E402

KMM = {"type": "museum", "url": "https://samlinger.natmus.dk/KMM/object/439647",
       "ref": "KMM 439647 (Inv. RP 1098.1)"}
DANSK = {"type": "literature", "url": "https://www.danskmoent.dk/fr/f4h2.htm",
         "ref": "danskmoent.dk (Hede f4h4)"}


def host():
    return {"id": "unified-dk-hede-f4h4",
            "catalog": {"hede": "4", "schou": ["3", "3a"], "others": ["B# 5", "B# 5a"]},
            "sources": [DANSK, KMM],
            "weight_rough_g": [{"value": 10.471, "source": "hede"},
                               {"value": 13.7, "source": "kmk"}]}


DEPARTED = {"id": "kmk-439647", "catalog": {"hede": "4", "schou": "3", "others": ["B# 5a"]},
            "sources": [KMM], "weight_rough_g": [{"value": 13.7, "source": "kmk"}]}
REMAINING = {"id": "unified-dk-hede-f4h4",
             "catalog": {"hede": "4", "schou": ["3", "3a"], "others": ["B# 5"]},
             "sources": [DANSK], "weight_rough_g": [{"value": 10.471, "source": "hede"}]}


class DepartedSeedTakesOnlyItsOwn(unittest.TestCase):
    def setUp(self):
        self.fc = host()
        _surgical_decontaminate(self.fc, [DEPARTED], [REMAINING])

    def test_exclusive_source_leaves(self):
        self.assertEqual(self.fc["sources"], [DANSK])

    def test_exclusive_index_leaves(self):
        self.assertEqual(self.fc["catalog"]["others"], ["B# 5"])

    def test_shared_indices_stay(self):
        """hede 4 / schou 3 are also attested by the remaining member."""
        self.assertEqual(self.fc["catalog"]["hede"], "4")
        self.assertEqual(self.fc["catalog"]["schou"], ["3", "3a"])

    def test_exclusive_weight_leaves(self):
        self.assertEqual([w["value"] for w in self.fc["weight_rough_g"]], [10.471])

    def test_held_catalog_is_untouched(self):
        fc = host()
        fc["_curation_holds"] = {"catalog": "curator froze the indices"}
        _surgical_decontaminate(fc, [DEPARTED], [REMAINING])
        self.assertEqual(fc["catalog"]["others"], ["B# 5", "B# 5a"])

    def test_source_shared_with_a_remaining_member_stays(self):
        fc = host()
        _surgical_decontaminate(fc, [DEPARTED], [dict(REMAINING, sources=[DANSK, KMM])])
        self.assertIn(KMM, fc["sources"])


class DepartedYears(unittest.TestCase):
    """The 1/16 Speciedaler case: 1645-1647 came only from the departed tid 163623."""
    def test_exclusive_years_leave_shared_stay(self):
        fc = {"id": "unified-dk-tid-163623", "year_first": 1640, "year_last": 1647,
              "year_ranges": [[1640, 1643], [1645, 1647]]}
        departed = {"id": "dk-tid-163623", "year_ranges": [[1641, 1646]]}
        remaining = {"id": "unified-dk-tid-163618", "year_ranges": [[1640, 1641]]}
        _surgical_decontaminate(fc, [departed], [remaining])
        # 1642-1643 and 1645-1646 were the departed seed's alone; 1640-1641 are
        # shared; 1647 was attested by no evicted member and stays.
        self.assertEqual(fc["year_ranges"], [[1640, 1641], [1647, 1647]])
        self.assertEqual((fc["year_first"], fc["year_last"]), (1640, 1647))

    def test_year_hold_freezes(self):
        fc = {"id": "x", "year_first": 1640, "year_last": 1646,
              "year_ranges": [[1640, 1646]], "_curation_holds": {"year_ranges": "curated"}}
        _surgical_decontaminate(fc, [{"year_ranges": [[1642, 1646]]}],
                                [{"year_ranges": [[1640, 1641]]}])
        self.assertEqual(fc["year_ranges"], [[1640, 1646]])


if __name__ == "__main__":
    unittest.main()
