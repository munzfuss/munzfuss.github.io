"""Mint-registry cleanup (curator 2026-10-19).

Functions under test:
    scripts/lib/v2_seed_writer.py :: _apply_pre_write_hygiene, _canonicalise_mint
    scripts/lib/seed_merge.py     :: merge_one (verified-wins vs a stale «X?»)
    scripts/maintenance/build_kmk_seed.py :: _split_place

  * misspellings normalise («Cristiania», «Hafnens», «Rønneby» …);
  * a source's «?» moves from the name into `mint_verified: false`;
  * «el.» / «ell.» split as alternatives, «+» as a joint pair;
  * a denomination in the mint field is not a mint;
  * KMM non-mint places / mintmaster notes leave the mint field.

Run:

    .venv/bin/python -m unittest tests.test_mint_cleanup_2026_10_19 -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.seed_merge import merge_one  # noqa: E402
from lib.v2_seed_writer import _apply_pre_write_hygiene, _canonicalise_mint  # noqa: E402
import build_kmk_seed as kmk  # noqa: E402


def _hyg(mint):
    coins, _ = _apply_pre_write_hygiene(
        [{"id": "t", "mint": mint, "mint_verified": True,
          "nominal": "1 Skilling", "year_first": 1600,
          "sources": [{"url": "https://example.org/x"}]}])
    return coins[0]


class MintCleanupTest(unittest.TestCase):
    def test_misspellings(self):
        for raw, canon in (("Cristiania", "Christiania"), ("Christinia", "Christiania"),
                           ("Christania", "Christiania"), ("Hafnens", "Kopenhagen"),
                           ("Rønneby", "Ronneby"), ("Romeby", "Ronneby"),
                           ("Alborg", "Aalborg"), ("Mamø", "Malmø"),
                           ("Landskrone", "Landskrona"), ("Rensborg", "Rendsburg"),
                           ("Fensborg", "Flensburg"), ("Gulland", "Visby")):
            self.assertEqual(_canonicalise_mint(raw), canon, raw)

    def test_uncertain_mint_to_flag(self):
        c = _hyg("Malmø?")
        self.assertEqual(c["mint"], "Malmø")
        self.assertIs(c["mint_verified"], False)
        self.assertTrue(c["_mint_uncertain"])
        c = _hyg("Niduras?")
        self.assertEqual(c["mint"], "Nidaros")
        self.assertIs(c["mint_verified"], False)

    def test_alternatives_and_joint(self):
        c = _hyg("Kbh. el. Malmø")
        self.assertEqual(c["mint"], ["Kopenhagen", "Malmø"])
        self.assertIs(c["mint_verified"], False)
        c = _hyg("Kbh.+ Frederiksborg")
        self.assertEqual(c["mint"], ["Frederiksborg", "Kopenhagen"])

    def test_denomination_is_not_a_mint(self):
        for raw in ("Thaler", "Portugaloser", "6 Pfennig", "2 Portugaloser"):
            self.assertIsNone(_canonicalise_mint(raw), raw)

    def test_stale_uncertain_value_loses(self):
        existing = {"id": "k", "mint": "Christiania?", "mint_verified": True}
        fresh = {"id": "k", "mint": "Christiania", "mint_verified": False,
                 "_mint_uncertain": True}
        out = merge_one(dict(existing), fresh)
        self.assertEqual(out["mint"], "Christiania")
        self.assertIs(out["mint_verified"], False)

    def test_kmk_non_mint_places(self):
        self.assertEqual(kmk._split_place({"place": "Ubestemt", "id": 0}), (None, None))
        self.assertEqual(kmk._split_place({"place": "Store-Magleby-skatten", "id": 0}), (None, None))
        self.assertEqual(kmk._split_place({"place": "Møntmester: Gotfr. Krüger", "id": 0}),
                         (None, "Gotfr. Krüger"))
        self.assertEqual(kmk._split_place({"place": "Hafnens", "id": 0}), ("Kopenhagen", None))



class HedeUnknownMintReviewTest(unittest.TestCase):
    def test_unknown_mint_candidates(self):
        import parse_hede as ph
        txt = "A) Sæby; 1596 (Hede 5A)\nB) Kongsberg, 1597\nC) Forsideomskrift: x"
        self.assertEqual(ph.unknown_mint_candidates(txt), ["Sæby"])

    def test_no_ruler_header(self):
        import parse_hede as ph
        html = "<H1>2 Skilling klipping, Christiansstad</H1>"
        d = ph.parse_one(html, "c5h131")
        self.assertEqual(d["ruler"], "Christian 5.")
        self.assertEqual(d["nominal"], "2 Skilling klipping")
        self.assertEqual(d["mint"], "Christiansstad")


if __name__ == "__main__":
    unittest.main()
