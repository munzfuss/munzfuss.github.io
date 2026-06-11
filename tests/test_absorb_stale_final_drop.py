"""Tests for the stale-final drop in absorb_seeds_into_final_v2.

Functions under test (module-level helpers):
    scripts/maintenance/absorb_seeds_into_final_v2.py ::
        _final_is_curated
        _final_has_live_backing
        _is_vanished_stale_final

Context — the bug these guard against (2026-06-09 KMM-exonumia suppress):
absorb is additive/sticky. When a unified entry vanishes from
data/v2/seed_unified/ (its seed source deleted or filtered), the absorb
pass left the corresponding final entry behind — only dead composed_of
REFS were trimmed, never the whole now-unbacked final. 622 stale exonumia
finals had to be removed by hand. The drop logic now removes a final iff:
  (a) it is pipeline-promoted (id form `unified-*`) — a V1 foundation
      (real id) is the coin's own data and is never dropped here;
  (b) it has no live backing — neither its id nor any composed_of member
      resolves to a current seed_unified head/seed;
  (c) it carries no curation (real fuss / note / _curation_holds /
      promoted_to / curator-assigned phase).
A curated entry whose backing vanished is KEPT (curator work is never lost).

Run via:
    .venv/bin/python -m unittest tests.test_absorb_stale_final_drop -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "absorb_seeds_into_final_v2",
    str(PROJECT_ROOT / "scripts" / "maintenance"
        / "absorb_seeds_into_final_v2.py"),
)
_absorb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_absorb)

_is_vanished_stale_final = _absorb._is_vanished_stale_final
_final_is_curated = _absorb._final_is_curated
_final_has_live_backing = _absorb._final_has_live_backing

# Synthetic seed_unified state shared by the backing tests.
#   live heads: unified-A (still produced by a seed), unified-B
#   live seed ids inside heads' composed_of: denmark-kmk-1, denmark-hede-2
LIVE_UNIFIED = {"unified-A", "unified-B"}
LIVE_IDS = LIVE_UNIFIED | {"denmark-kmk-1", "denmark-hede-2"}


class TestLiveBacking(unittest.TestCase):
    def test_own_id_is_live_head(self):
        # bulk-promoted self-link whose head still exists
        fe = {"id": "unified-A", "composed_of": ["unified-A"]}
        self.assertTrue(_final_has_live_backing(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_composed_member_is_live_head(self):
        # V1 foundation enriched by a still-live unified head
        fe = {"id": "dk-tid-1", "composed_of": ["unified-B"]}
        self.assertTrue(_final_has_live_backing(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_composed_member_is_live_seed_id(self):
        fe = {"id": "dk-tid-2", "composed_of": ["denmark-kmk-1"]}
        self.assertTrue(_final_has_live_backing(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_no_backing_when_all_members_gone(self):
        fe = {"id": "unified-GONE", "composed_of": ["unified-GONE"]}
        self.assertFalse(_final_has_live_backing(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_no_backing_empty_composed(self):
        fe = {"id": "unified-GONE", "composed_of": []}
        self.assertFalse(_final_has_live_backing(fe, LIVE_UNIFIED, LIVE_IDS))


class TestCurationGuard(unittest.TestCase):
    def test_seed_unsorted_is_not_curated(self):
        self.assertFalse(_final_is_curated(
            {"fuss": "seed_unsorted", "phase": "kmk"}))

    def test_none_fuss_is_not_curated(self):
        self.assertFalse(_final_is_curated({"fuss": None}))

    def test_real_fuss_is_curated(self):
        self.assertTrue(_final_is_curated(
            {"fuss": "reichsdukatenfuss", "phase": "II"}))

    def test_note_is_curation(self):
        self.assertTrue(_final_is_curated(
            {"fuss": "seed_unsorted", "note": "curator remark"}))

    def test_curation_holds_is_curation(self):
        self.assertTrue(_final_is_curated(
            {"fuss": "seed_unsorted", "_curation_holds": {"fineness": "why"}}))

    def test_promoted_to_is_curation(self):
        self.assertTrue(_final_is_curated(
            {"fuss": "seed_unsorted", "promoted_to": "dk-tid-99"}))

    def test_seed_source_phase_tag_is_not_curation(self):
        # a bare seed-source phase tag must NOT protect an uncurated entry
        for tag in ("bruun", "hede", "kmk", "numismaster", "ucoin"):
            with self.subTest(tag=tag):
                self.assertFalse(_final_is_curated(
                    {"fuss": "seed_unsorted", "phase": tag}))

    def test_curator_phase_is_curation(self):
        # a real curator phase (not a seed tag) counts even if fuss slipped
        self.assertTrue(_final_is_curated(
            {"fuss": "seed_unsorted", "phase": "A"}))


class TestVanishedStaleFinal(unittest.TestCase):
    """The composite predicate that drives the drop."""

    def test_uncurated_promoted_vanished_is_dropped(self):
        # the exact 622-exonumia shape: bulk-promoted self-link, backing gone
        fe = {"id": "unified-GONE", "composed_of": ["unified-GONE"],
              "fuss": "seed_unsorted", "phase": "kmk"}
        self.assertTrue(
            _is_vanished_stale_final(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_promoted_still_backed_is_kept(self):
        fe = {"id": "unified-A", "composed_of": ["unified-A"],
              "fuss": "seed_unsorted", "phase": "kmk"}
        self.assertFalse(
            _is_vanished_stale_final(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_curated_vanished_is_kept(self):
        # curator classified a promoted entry; backing vanished → KEEP
        fe = {"id": "unified-GONE", "composed_of": ["unified-GONE"],
              "fuss": "9_25_thaler", "phase": "II"}
        self.assertFalse(
            _is_vanished_stale_final(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_v1_foundation_vanished_is_kept(self):
        # real (non-unified) id → V1 data, never dropped even if backing gone
        fe = {"id": "dk-tid-7", "composed_of": ["unified-GONE"],
              "fuss": "seed_unsorted"}
        self.assertFalse(
            _is_vanished_stale_final(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_v1_foundation_with_note_vanished_is_kept(self):
        fe = {"id": "dk-c4h97", "composed_of": [],
              "fuss": "seed_unsorted", "note": "x"}
        self.assertFalse(
            _is_vanished_stale_final(fe, LIVE_UNIFIED, LIVE_IDS))

    def test_uncurated_promoted_partial_backing_is_kept(self):
        # one of two composed members still live → still backed → KEEP
        fe = {"id": "unified-GONE", "composed_of": ["unified-GONE", "unified-B"],
              "fuss": "seed_unsorted", "phase": "kmk"}
        self.assertFalse(
            _is_vanished_stale_final(fe, LIVE_UNIFIED, LIVE_IDS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
