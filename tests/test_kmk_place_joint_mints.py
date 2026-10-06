"""KMM `place` → mint / mintmaster, for the forms that are not «city,
mintmaster».

`_split_place` read every comma as «city, mintmaster», so a second TOWN after
the comma landed in `mintmaster` — «Zellerfeld, Goslar; Henning Schlüter» gave
mintmaster «Goslar; Henning Schlüter», «København, Altona» gave mintmaster
«Altona». And «&» was not read at all. 15 + 13 records, 2026-10-06.

Pinned: a registered second mint after «,» or «&» makes a joint mint, «;»
introduces the mintmaster; a real «city, mintmaster» is unchanged; the
København/Frederiksborg pair (Hede names København alone) is kept but
unverified; the one place erratum (310429) applies only to its printed value.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_place_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)


def split(place, rid=0):
    return bk._split_place({"id": rid, "place": place})


class JointMints(unittest.TestCase):
    def test_two_towns_then_mintmaster(self):
        self.assertEqual(split("Zellerfeld, Goslar; Henning Schlüter"),
                         (["Zellerfeld", "Goslar"], "Henning Schlüter"))

    def test_two_towns_no_mintmaster(self):
        self.assertEqual(split("København, Altona"), (["Kopenhagen", "Altona"], None))

    def test_ampersand(self):
        self.assertEqual(split("Goslar & Zellerfeld"), (["Goslar", "Zellerfeld"], None))

    def test_city_then_person_unchanged(self):
        self.assertEqual(split("København, Schwabe"), ("Kopenhagen", "Schwabe"))


class DisputedPair(unittest.TestCase):
    def test_frederiksborg_pair_unverified(self):
        src = {"id": 699135, "place": "København & Frederiksborg", "nominal": "skilling"}
        e = bk.build_entry(src) or {}
        self.assertTrue(e)
        self.assertEqual(e.get("mint"), ["Kopenhagen", "Frederiksborg"])
        self.assertFalse(e.get("mint_verified"))

    def test_other_joint_pair_verified(self):
        src = {"id": 298426, "place": "København, Altona", "nominal": "1 skilling rigsmønt"}
        e = bk.build_entry(src) or {}
        self.assertTrue(e)
        self.assertTrue(e.get("mint_verified"))


class PlaceErratum(unittest.TestCase):
    def test_applies_to_its_printed_value_only(self):
        self.assertEqual(split("skilling", rid=310429), ("Malmø", None))
        self.assertEqual(split("Lund", rid=310429)[0], "Lund")


if __name__ == "__main__":
    unittest.main()
