"""KMM `place` naming ALTERNATIVE mints («A eller B», «A/B») attests neither.

`_split_place` kept only the first segment, so «Malmø eller København» became
mint «Malmø» with `mint_verified: true`; the verified single town then won the
merger's tiered mint collection over the other town Galster gives (kmk-156727,
2026-11-05; SOURCES §13.30). And `merge_one` let an existing verified value
survive a fresh source-hedged one, so the fix would not have reached the seed.

Pinned: alternatives between two different registered mints pass through
verbatim (the writer splits them, unverified, with `as_printed`); a name-variant
pair stays one mint; a non-mint segment keeps the old reading; and a fresh
source-hedged mint beats an existing verified one in `merge_one`.
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
    "build_kmk_seed_for_alt_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)

from lib.seed_merge import merge_one  # noqa: E402
from lib.v2_seed_writer import _apply_pre_write_hygiene  # noqa: E402
from ruamel.yaml.comments import CommentedMap  # noqa: E402


def split(place):
    return bk._split_place({"id": 0, "place": place})


def written(place):
    coin = {"id": "kmk-0", "mint": split(place)[0],
            "mint_verified": not bool(bk._ALT_PLACE_RE.search(place)),
            "sources": [{"url": "https://samlinger.natmus.dk/KMM/object/0"}]}
    kept, _ = _apply_pre_write_hygiene([coin], "kmk")
    return kept[0]


class Alternatives(unittest.TestCase):
    def test_eller_passes_verbatim(self):
        self.assertEqual(split("Malmø eller København"), ("Malmø eller København", None))

    def test_slash_passes_verbatim(self):
        self.assertEqual(split("Goslar/Zellerfeld")[0], "Goslar/Zellerfeld")

    def test_writer_splits_unverified_with_as_printed(self):
        c = written("Malmø eller København")
        self.assertEqual(c["mint"], ["Kopenhagen", "Malmø"])
        self.assertFalse(c["mint_verified"])
        self.assertEqual(c["uncertainty"]["mint"][0]["as_printed"], "Malmø eller København")

    def test_name_variant_pair_is_one_mint(self):
        self.assertEqual(split("Christiania / Oslo"), ("Christiania", None))

    def test_non_mint_segment_keeps_first(self):
        self.assertEqual(split("København/Schwabe")[0], "Kopenhagen")


class HedgedFreshWins(unittest.TestCase):
    def test_fresh_alternatives_beat_stale_verified(self):
        existing = CommentedMap({"id": "kmk-156727", "mint": "Malmø", "mint_verified": True})
        fresh = CommentedMap({
            "id": "kmk-156727", "mint": ["Kopenhagen", "Malmø"], "mint_verified": False,
            "uncertainty": {"mint": [{"kind": "hedged", "how": "alternatives",
                                      "source": "kmk", "as_printed": "Malmø eller København"}]}})
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], ["Kopenhagen", "Malmø"])
        self.assertFalse(existing["mint_verified"])

    def test_same_list_stale_flag_follows_fresh(self):
        existing = CommentedMap({"id": "g", "mint": ["Kopenhagen", "Malmø"], "mint_verified": True})
        fresh = CommentedMap({
            "id": "g", "mint": ["Kopenhagen", "Malmø"], "mint_verified": False,
            "uncertainty": {"mint": [{"kind": "hedged", "how": "alternatives", "source": "galster"}]}})
        merge_one(existing, fresh)
        self.assertFalse(existing["mint_verified"])

    def test_unhedged_fresh_still_loses_to_verified(self):
        existing = CommentedMap({"id": "x", "mint": "Ribe", "mint_verified": True})
        fresh = CommentedMap({"id": "x", "mint": "Kopenhagen", "mint_verified": False})
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], "Ribe")
        self.assertTrue(existing["mint_verified"])

    def test_hold_still_wins(self):
        existing = CommentedMap({"id": "x", "mint": "Malmø", "mint_verified": True,
                                 "_curation_holds": {"mint": "r", "mint_verified": "r"}})
        fresh = CommentedMap({
            "id": "x", "mint": ["Kopenhagen", "Malmø"], "mint_verified": False,
            "uncertainty": {"mint": [{"kind": "hedged", "how": "alternatives", "source": "kmk"}]}})
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], "Malmø")
        self.assertTrue(existing["mint_verified"])


if __name__ == "__main__":
    unittest.main()
