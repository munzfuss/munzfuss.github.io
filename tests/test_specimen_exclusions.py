"""A curator-excluded KMM specimen leaves the coin; the seed and the class stay.

A KMM seed folds several specimens of one find (one `sources` entry each). The
`specimens:` block of `data/v2/exclusions/<entity>.yml` names single KMM
objects; absorb strips exactly their citations (curator 2026-10-20), never one
with a weight or a photo, and never the coin's last source.

Run:
    .venv/bin/python -m unittest tests.test_specimen_exclusions -v
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.specimen_exclusions import load_excluded_specimens, strip_excluded_specimens  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "verify_reflow_specimens", ROOT / "scripts" / "maintenance" / "verify_reflow.py")
VR = importlib.util.module_from_spec(_spec)
sys.modules["verify_reflow_specimens"] = VR
_spec.loader.exec_module(VR)


def _k(n):
    return {"type": "museum", "url": f"https://samlinger.natmus.dk/KMM/object/{n}",
            "ref": f"KMM {n}"}


class Strip(unittest.TestCase):
    def test_only_named_specimens_go(self):
        coin = {"sources": [_k(1), _k(2), _k(3)]}
        self.assertEqual(strip_excluded_specimens(coin, {"2": {}}), ["2"])
        self.assertEqual([s["ref"] for s in coin["sources"]], ["KMM 1", "KMM 3"])

    def test_guard_keeps_weight_or_photo(self):
        coin = {"sources": [_k(1), _k(2)]}
        self.assertEqual(strip_excluded_specimens(coin, {"2": {}}, keeps=lambda n: n == "2"), [])
        self.assertEqual(len(coin["sources"]), 2)

    def test_never_leaves_a_coin_without_source(self):
        coin = {"sources": [_k(1), _k(2)]}
        self.assertEqual(strip_excluded_specimens(coin, {"1": {}, "2": {}}), [])
        self.assertEqual(len(coin["sources"]), 2)

    def test_other_resources_untouched(self):
        lit = {"type": "literature", "url": "https://www.danskmoent.dk/hansg31.htm"}
        coin = {"sources": [lit, _k(5)]}
        strip_excluded_specimens(coin, {"5": {}})
        self.assertEqual(coin["sources"], [lit])


class LoadAndVerify(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data/v2/exclusions").mkdir(parents=True)
        (self.root / "data/v2/exclusions/ent.yml").write_text(yaml.safe_dump({
            "exclusions": [{"id": "kmk-9", "category": "off_strike"}],
            "specimens": [{"kmm": 395811, "category": "undocumented_stub"}]}))
        self._root, VR.ROOT = VR.ROOT, self.root
        VR._MEMBER_KMM_CACHE.clear()

    def tearDown(self):
        VR.ROOT = self._root
        VR._MEMBER_KMM_CACHE.clear()
        self.tmp.cleanup()

    def test_loader_reads_only_the_specimens_block(self):
        got = load_excluded_specimens(self.root / "data/v2/exclusions")
        self.assertEqual(set(got), {"395811"})

    def test_verify_reflow_excuses_the_specimen_citation(self):
        self.assertIn("395811", VR._member_excluded_kmm("ent"))
        self.assertNotIn("9", VR._member_excluded_kmm("ent"))


if __name__ == "__main__":
    unittest.main()
