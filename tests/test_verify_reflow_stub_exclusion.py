"""An undocumented-stub exclusion excuses every KMM citation its seed carries.

The merger and absorb isolate a `category: undocumented_stub` exclusion just
like a `scope: member` one: the record leaves its class, and its citations
leave with it. A KMM seed can fold several specimens of one find (one
`sources` entry each), so all of them leave — 2026-10-20: 191 stub seeds held
987 specimen citations. `verify_reflow` must excuse exactly those citations and
nothing else.

Run:
    .venv/bin/python -m unittest tests.test_verify_reflow_stub_exclusion -v
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "verify_reflow", PROJECT_ROOT / "scripts" / "maintenance" / "verify_reflow.py")
VR = importlib.util.module_from_spec(_spec)
sys.modules["verify_reflow"] = VR
_spec.loader.exec_module(VR)


def _src(n):
    return {"ref": f"KMM {n}", "type": "museum",
            "url": f"https://samlinger.natmus.dk/KMM/object/{n}"}


class TestStubExclusionCitations(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "data/v2/exclusions").mkdir(parents=True)
        (root / "data/v2/seed/kmk").mkdir(parents=True)
        (root / "data/v2/exclusions/ent.yml").write_text(yaml.safe_dump({"exclusions": [
            {"id": "kmk-1", "category": "undocumented_stub"},
            {"id": "kmk-5", "category": "off_strike"},
            {"id": "kmk-7", "category": "undocumented_stub", "scope": "member"},
        ]}))
        (root / "data/v2/seed/kmk/ent.yml").write_text(yaml.safe_dump({"coins": [
            {"id": "kmk-1", "sources": [_src(1), _src(2), _src(3)]},
            {"id": "kmk-4", "sources": [_src(4)]},
            {"id": "kmk-5", "sources": [_src(5), _src(6)]},
            {"id": "kmk-7", "sources": [_src(7)]},
        ]}))
        self._root, VR.ROOT = VR.ROOT, root
        VR._MEMBER_KMM_CACHE.clear()

    def tearDown(self):
        VR.ROOT = self._root
        VR._MEMBER_KMM_CACHE.clear()
        self.tmp.cleanup()

    def test_folded_specimens_of_a_stub_are_excused(self):
        self.assertEqual(VR._member_excluded_kmm("ent"), {"1", "2", "3", "7"})

    def test_plain_exclusion_and_other_seeds_are_not(self):
        got = VR._member_excluded_kmm("ent")
        self.assertNotIn("4", got)   # not excluded at all
        self.assertNotIn("5", got)   # whole-coin exclusion, handled elsewhere
        self.assertNotIn("6", got)


class TestStubExclusionAnySource(unittest.TestCase):
    """The same decision for a record of another source (ucoin stubs,
    2026-11-20): its own citation and its own readings leave the class."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "data/v2/exclusions").mkdir(parents=True)
        (root / "data/v2/seed/ucoin").mkdir(parents=True)
        (root / "data/v2/exclusions/ent.yml").write_text(yaml.safe_dump({"exclusions": [
            {"id": "dk-tid-1", "category": "undocumented_stub", "scope": "member"},
            {"id": "dk-tid-9", "category": "exonumia"},
        ]}))
        u = lambda n: {"type": "ucoin", "url": f"https://en.ucoin.net/coin/x/?tid={n}"}
        (root / "data/v2/seed/ucoin/ent.yml").write_text(yaml.safe_dump({"coins": [
            {"id": "dk-tid-1", "sources": [u(1)], "weight_rough_g": 5.57, "fineness": 0.672},
            {"id": "dk-tid-2", "sources": [u(2)], "weight_rough_g": 4.5},
            {"id": "dk-tid-9", "sources": [u(9)], "weight_rough_g": 9.9},
        ]}))
        self._root, VR.ROOT = VR.ROOT, root
        VR._MEMBER_RECORDS_CACHE = None

    def tearDown(self):
        VR.ROOT = self._root
        VR._MEMBER_RECORDS_CACHE = None
        self.tmp.cleanup()

    def test_member_stub_citation_and_readings(self):
        r = VR._member_excluded_records()
        self.assertEqual(r["seeds"], {"dk-tid-1"})
        self.assertEqual(r["urls"], {"https://en.ucoin.net/coin/x/?tid=1"})
        self.assertIn(("weight_rough_g", "ucoin", 5.57), r["readings"])
        self.assertIn(("fineness", "ucoin", 0.672), r["readings"])

    def test_other_records_and_plain_exclusions_are_not(self):
        r = VR._member_excluded_records()
        self.assertNotIn(("weight_rough_g", "ucoin", 4.5), r["readings"])
        self.assertNotIn(("weight_rough_g", "ucoin", 9.9), r["readings"])


if __name__ == "__main__":
    unittest.main()
