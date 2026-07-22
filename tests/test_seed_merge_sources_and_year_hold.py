"""Re-seed preservation of curator-added sources and per-entry year narrowing.

Guards the danish_realm drift caught 2026-07-23: a merge-aware re-run of
`build_numista_seed` reverted three Christian IV English-model gold coins
(numista 426503 / 426815 / 426842) from the curator's source-backed window
`1606-1608` (verified:false) to Numista's bare full-reign placeholder
`1588-1648`, AND dropped the curator-added danskmoent.dk Hede c4h21 citation
from `sources`.

Two independent defects were fixed in `merge_one`:

  1. `sources` fell through to «fresh wins» → the curator-added primary-source
     citation was REPLACED by the Numista-only fresh list. §9a mandates
     «Reconciliation NEVER replaces `sources` — always UNION». Now unioned via
     `_union_source_lists`.

  2. year fields (`year_first/last/ranges/label` + `year_verified`) are neither
     globally curated nor source-derived-immutable; the curator's per-entry
     narrowing is preserved with a `_curation_holds` on the entry. This test
     confirms the hold mechanism freezes them across a re-merge and that the
     accompanying `year_verified` existing-only key is not dropped.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import _union_source_lists, merge_one  # noqa: E402
from ruamel.yaml.comments import CommentedMap  # noqa: E402


def _src(url, ref, type_="literature"):
    return CommentedMap({"type": type_, "url": url, "ref": ref})


NUMISTA_SRC = _src("https://en.numista.com/426503", "Numista N#426503")
DANSK_SRC = _src("https://www.danskmoent.dk/chr/c4h21.htm", "danskmoent.dk (Hede c4h21)")


class TestUnionSourceLists(unittest.TestCase):
    def test_curator_added_source_preserved(self):
        existing = [NUMISTA_SRC, DANSK_SRC]
        fresh = [NUMISTA_SRC]  # builder re-emits only the Numista source
        out = _union_source_lists(existing, fresh)
        self.assertEqual(out, [NUMISTA_SRC, DANSK_SRC])

    def test_union_is_idempotent(self):
        out1 = _union_source_lists([NUMISTA_SRC, DANSK_SRC], [NUMISTA_SRC])
        out2 = _union_source_lists(out1, [NUMISTA_SRC])
        self.assertEqual(out1, out2)

    def test_dedup_is_key_order_insensitive(self):
        reordered = CommentedMap({"ref": "Numista N#426503", "url": "https://en.numista.com/426503", "type": "literature"})
        out = _union_source_lists([NUMISTA_SRC], [reordered])
        self.assertEqual(len(out), 1)  # same content, one copy

    def test_fresh_only_source_appended(self):
        out = _union_source_lists([NUMISTA_SRC], [DANSK_SRC])
        self.assertEqual(out, [NUMISTA_SRC, DANSK_SRC])

    def test_existing_leads_order(self):
        out = _union_source_lists([DANSK_SRC], [NUMISTA_SRC])
        self.assertEqual(out[0], DANSK_SRC)


class TestMergeOnePreservesCuratorEdits(unittest.TestCase):
    def _curated_entry(self):
        return CommentedMap({
            "id": "dk-numista-426503",
            "year_label": "1606-1608",
            "year_first": 1606,
            "year_last": 1608,
            "year_ranges": [[1606, 1608]],
            "year_verified": False,
            "sources": [NUMISTA_SRC, DANSK_SRC],
            "_curation_holds": CommentedMap({
                "year_label": "narrowed per danskmoent Hede c4h21",
                "year_first": None,
                "year_last": None,
                "year_ranges": None,
                "year_verified": None,
            }),
        })

    def _fresh_from_numista(self):
        # What the builder re-emits from the immutable Numista cache:
        # the bare full-reign placeholder + only the Numista source, no
        # year_verified key.
        return CommentedMap({
            "id": "dk-numista-426503",
            "year_label": "1588-1648",
            "year_first": 1588,
            "year_last": 1648,
            "year_ranges": [[1588, 1648]],
            "sources": [NUMISTA_SRC],
        })

    def test_year_narrowing_survives_regen(self):
        existing = self._curated_entry()
        merge_one(existing, self._fresh_from_numista())
        self.assertEqual(existing["year_label"], "1606-1608")
        self.assertEqual(existing["year_first"], 1606)
        self.assertEqual(existing["year_last"], 1608)
        self.assertEqual(list(existing["year_ranges"][0]), [1606, 1608])

    def test_year_verified_existing_only_key_not_dropped(self):
        existing = self._curated_entry()
        merge_one(existing, self._fresh_from_numista())
        self.assertIn("year_verified", existing)
        self.assertIs(existing["year_verified"], False)

    def test_danskmoent_source_survives_regen(self):
        existing = self._curated_entry()
        merge_one(existing, self._fresh_from_numista())
        urls = {s["url"] for s in existing["sources"]}
        self.assertIn("https://www.danskmoent.dk/chr/c4h21.htm", urls)
        self.assertIn("https://en.numista.com/426503", urls)

    def test_double_merge_idempotent(self):
        existing = self._curated_entry()
        merge_one(existing, self._fresh_from_numista())
        snap1 = (existing["year_label"], [dict(s) for s in existing["sources"]])
        merge_one(existing, self._fresh_from_numista())
        snap2 = (existing["year_label"], [dict(s) for s in existing["sources"]])
        self.assertEqual(snap1, snap2)

    def test_source_union_without_hold_still_preserves_citation(self):
        # Even with NO year hold, a curator-added source must survive — the
        # sources-union fix is independent of the year-hold mechanism.
        existing = self._curated_entry()
        del existing["_curation_holds"]
        merge_one(existing, self._fresh_from_numista())
        urls = {s["url"] for s in existing["sources"]}
        self.assertIn("https://www.danskmoent.dk/chr/c4h21.htm", urls)


if __name__ == "__main__":
    unittest.main()
