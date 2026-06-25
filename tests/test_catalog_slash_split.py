"""Regression: a «/» in a catalogue index reads as «and» — split into numbers.

A «/» between catalogue NUMBERS is a multi-value «and» delimiter (curator
decision 2026-06-25 — «сприймемо це як 'та'»):

  * both parts complete — ucoin/Numista sub-variants «683.1 / 683.2», «125A /
    125B», «3679 / 3679A» → split as-is;
  * shared prefix abbreviated on the second — Jensen-Skjoldager «T-91/96»
    (danskmoent writes the «T-» once) = «T-91» AND «T-96»; the leading alpha
    prefix is RE-ATTACHED so the bare «96» becomes «T-96», never a prefix-less
    garbage token.

A «/» that is NOT separating numbers — a publisher abbreviation «Divo/S» (pure-
alpha first part) or a «Catalogue# n» label («#») — is left whole by the
number-list guard. A DASH range «T-81 - T-88» / «021-061» is a different
notation (not a slash) and never enters here.

Two surfaces, both must apply the same rule:

* WRITE/DISPLAY — `lib/catalog_codes.py :: split_multi_ref` (+ the `normalise_catalog`
  block 1b that consumes it).
* MATCHING — `merge_seeds_cross_source.py :: _split_multi` (delegates to the same
  helper so a not-yet-renormalised seed still matches correctly).

Run via:
    .venv/bin/python -m unittest tests.test_catalog_slash_split -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.catalog_codes import split_multi_ref, normalise_catalog  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"),
)
_merger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_merger)
_split_multi = _merger._split_multi
_catalog_refs = _merger._catalog_refs


class TestSplitMultiRefHelper(unittest.TestCase):
    def test_shared_prefix_reattached(self):
        # «96» is a prefix-abbreviated continuation of «T-91» → reattach «T-».
        self.assertEqual(split_multi_ref("T-91/96"), ["T-91", "T-96"])
        self.assertEqual(split_multi_ref("T-31/35"), ["T-31", "T-35"])
        self.assertEqual(split_multi_ref("T-41/45"), ["T-41", "T-45"])

    def test_both_parts_complete_split_as_is(self):
        self.assertEqual(split_multi_ref("683.1 / 683.2"), ["683.1", "683.2"])
        self.assertEqual(split_multi_ref("125A / 125B"), ["125A", "125B"])
        self.assertEqual(split_multi_ref("3679 / 3679A"), ["3679", "3679A"])

    def test_one_sided_space_still_splits(self):
        self.assertEqual(split_multi_ref("125A /125B"), ["125A", "125B"])
        self.assertEqual(split_multi_ref("125A/ 125B"), ["125A", "125B"])

    def test_publisher_abbrev_kept_whole(self):
        # «#»-labelled token → one citation, not a number list.
        self.assertEqual(split_multi_ref("Divo/S# 123"), ["Divo/S# 123"])

    def test_pure_alpha_first_kept_whole(self):
        # first part «Divo» has no digit → not a number list.
        self.assertEqual(split_multi_ref("Divo/S"), ["Divo/S"])

    def test_dash_range_not_a_slash(self):
        self.assertEqual(split_multi_ref("XIV.32-33"), ["XIV.32-33"])
        self.assertEqual(split_multi_ref("T-81 - T-88"), ["T-81 - T-88"])

    def test_blank_yields_empty(self):
        self.assertEqual(split_multi_ref("   "), [])


class TestNormaliseCatalogWriteSide(unittest.TestCase):
    """`normalise_catalog` expands «/» to a number list in a typed field."""

    def test_jensen_skjoldager_and_split_with_reattach(self):
        cat = {"jensen_skjoldager": "T-91/96"}
        normalise_catalog(cat)
        self.assertEqual(sorted(cat["jensen_skjoldager"]), ["T-91", "T-96"])

    def test_schive_dash_range_preserved(self):
        cat = {"schive": "XIV.32-33"}
        normalise_catalog(cat)
        self.assertEqual(cat["schive"], "XIV.32-33")

    def test_spaced_subvariant_explodes(self):
        cat = {"sieg": "683.1 / 683.2"}
        normalise_catalog(cat)
        self.assertEqual(sorted(cat["sieg"]), ["683.1", "683.2"])


class TestMergerMatchingSide(unittest.TestCase):
    """`_catalog_refs` (matcher) sees both numbers (prefix reattached)."""

    def test_jensen_skjoldager_and_split(self):
        refs = _catalog_refs({"catalog": {"jensen_skjoldager": "T-91/96"}},
                             entity_id="danish_realm")
        self.assertEqual(refs.get("jensen_skjoldager"), "T-91|T-96")

    def test_spaced_subvariant_split_for_overlap(self):
        # no ruler → sieg key is bare «sieg» (reign-scope empty)
        refs = _catalog_refs({"catalog": {"sieg": "125A / 125B"}},
                             entity_id="danish_realm")
        self.assertEqual(refs.get("sieg"), "125A|125B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
