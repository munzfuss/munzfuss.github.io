"""A catalogue mark names the CatalogRefs field; the seed may hold the alias key.

The Bruun builder writes the Davenport number under `davenport`, the render
and the merger know it as `dav`. A mark `{register: dav}` must take the
number out of a seed whose catalog still says `davenport` — otherwise the
marked number keeps justifying matches while also showing as «(!)».
First case: Bruun Part III prints its own collection number in the Dav slot
on lots 11193, 11231 and 12046 (curator 2026-11-10).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib.seed_merge import apply_catalog_marks  # noqa: E402


def mark(reg, val):
    return {"register": reg, "value": val, "kind": "erroneous", "reason": {"en": "x"}}


class RegisterAlias(unittest.TestCase):
    def test_dav_mark_removes_davenport_key(self):
        e = {"catalog": {"davenport": "6505", "hede": "112A"},
             "catalog_marks": [mark("dav", "6505")]}
        apply_catalog_marks(e)
        self.assertEqual(e["catalog"], {"hede": "112A"})

    def test_canonical_key_still_preferred(self):
        e = {"catalog": {"dav": ["3580", "6505"], "davenport": "6505"},
             "catalog_marks": [mark("dav", "6505")]}
        apply_catalog_marks(e)
        self.assertEqual(e["catalog"]["dav"], "3580")
        self.assertEqual(e["catalog"]["davenport"], "6505")

    def test_other_value_under_alias_untouched(self):
        e = {"catalog": {"davenport": "3580"}, "catalog_marks": [mark("dav", "6505")]}
        apply_catalog_marks(e)
        self.assertEqual(e["catalog"], {"davenport": "3580"})


if __name__ == "__main__":
    unittest.main()
