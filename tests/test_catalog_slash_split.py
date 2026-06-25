"""Regression: a TIGHT slash «X/Y» in a catalogue index is ONE value, not two.

A slash separates a multi-value sub-variant pack ONLY when it carries
surrounding whitespace — «683.1 / 683.2», «125A / 125B», «3679 / 3679A» (how
ucoin/Numista pack sub-variants). A TIGHT «X/Y» belongs to ONE citation token:
the part after the slash is a prefix-abbreviated continuation that is
meaningless on its own — Jensen-Skjoldager «T-91/96» (danskmoent writes the «T-»
once; «96» is not a standalone index — whether «/» reads as a range or an «and»
of T-91 + T-96 is unsettled, but danskmoent uses a SPACED « - » for explicit
ranges, e.g. «T-81 - T-88»), a publisher abbreviation («Divo/S»), or a
hierarchical number («10.4.1/17»). The pre-fix code split on every «/», so
«T-91/96» became «96|T-91» (a fabricated prefix-less token «96»).

Two surfaces, both must respect the spaced-only rule:

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
    def test_tight_prefix_abbreviated_kept_whole(self):
        # «96» is a prefix-abbreviated continuation of «T-91», not a standalone
        # index — keep the source literal whole rather than fabricate «96».
        self.assertEqual(split_multi_ref("T-91/96"), ["T-91/96"])

    def test_publisher_abbrev_kept_whole(self):
        self.assertEqual(split_multi_ref("Divo/S# 123"), ["Divo/S# 123"])

    def test_hierarchical_number_kept_whole(self):
        self.assertEqual(split_multi_ref("10.4.1/17"), ["10.4.1/17"])

    def test_spaced_subvariant_split(self):
        self.assertEqual(split_multi_ref("683.1 / 683.2"), ["683.1", "683.2"])
        self.assertEqual(split_multi_ref("125A / 125B"), ["125A", "125B"])
        self.assertEqual(split_multi_ref("3679 / 3679A"), ["3679", "3679A"])

    def test_one_sided_space_still_splits(self):
        self.assertEqual(split_multi_ref("125A /125B"), ["125A", "125B"])
        self.assertEqual(split_multi_ref("125A/ 125B"), ["125A", "125B"])

    def test_no_slash_passthrough(self):
        self.assertEqual(split_multi_ref("XIV.32-33"), ["XIV.32-33"])

    def test_blank_yields_empty(self):
        self.assertEqual(split_multi_ref("   "), [])


class TestNormaliseCatalogWriteSide(unittest.TestCase):
    """`normalise_catalog` must keep a tight-slash token whole in a typed field."""

    def test_jensen_skjoldager_tight_slash_preserved(self):
        cat = {"jensen_skjoldager": "T-91/96"}
        normalise_catalog(cat)
        self.assertEqual(cat["jensen_skjoldager"], "T-91/96")

    def test_schive_dash_range_preserved(self):
        cat = {"schive": "XIV.32-33"}
        normalise_catalog(cat)
        self.assertEqual(cat["schive"], "XIV.32-33")

    def test_spaced_subvariant_still_explodes(self):
        cat = {"sieg": "683.1 / 683.2"}
        normalise_catalog(cat)
        self.assertEqual(sorted(cat["sieg"]), ["683.1", "683.2"])


class TestMergerMatchingSide(unittest.TestCase):
    """`_catalog_refs` (matcher) must not fabricate «96» from «T-91/96»."""

    def test_jensen_skjoldager_unchanged(self):
        refs = _catalog_refs({"catalog": {"jensen_skjoldager": "T-91/96"}},
                             entity_id="danish_realm")
        self.assertEqual(refs.get("jensen_skjoldager"), "T-91/96")

    def test_spaced_subvariant_split_for_overlap(self):
        # the original purpose still works: «125A / 125B» must split so a
        # peer citing just «125A» overlaps in the matcher.
        # no ruler → sieg key is bare «sieg» (reign-scope empty)
        refs = _catalog_refs({"catalog": {"sieg": "125A / 125B"}},
                             entity_id="danish_realm")
        self.assertEqual(refs.get("sieg"), "125A|125B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
