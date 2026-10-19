"""Two KMM defects that put the wrong catalogue numbers on a coin, found 2026-10-17.

Both surfaced while dating the ruler-less pennies of the Denmark page by their
Mansfeld-Bûllner numbers. `kmk-138263` (KMM FP 8349.1, typeNumber «MB 285,
287; 319-320») carried `mb: [285, 500, 566-567]` — Erik Menved of Lund and
Christoffer II of Roskilde on one record — and had lost its own 287.

1. Seed thinning (`lib.seed_thin`) grouped records by a key that named only
   km / hede / sieg / schou / lange / galster. A bucket of weightless ruler-
   less pennies with DIFFERENT MB numbers was one bucket, and
   `_salvage_unique` pinned the dropped records' numbers onto the keeper.
   19 KMM keepers carried another record's index that way; nothing flagged
   it, because a salvaged index looks exactly like a source's own.
2. `build_kmk_seed._catalog` split typeNumber on [;,] and dropped every
   segment without a catalogue prefix — the «287» of «MB 285, 287» — on 224
   records. Its sibling: «Lange 1, 503-04» / «Lange 2, 542c» name the VOLUME
   of the two-volume Lange 1908/12 first, and the volume was stored as the
   index (`lange: '1'`), which fused Lange 2 540 / 541 / 542 / 542c into one
   final class.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.seed_thin import thin_safe  # noqa: E402
from build_kmk_seed import _catalog  # noqa: E402


def penny(cid, **cat):
    return {"id": cid, "nominal": "1 Penning", "metal": None,
            "catalog": dict(cat)}


def cat(tn):
    return _catalog({"typeNumber": tn, "id": 1})


class ThinningKeepsDifferentIndicesApart(unittest.TestCase):
    def test_weightless_records_of_different_mb_numbers_stay(self):
        recs = [penny(f"kmk-{i}", mb=n) for i, n in
                enumerate(["285"] * 4 + ["566-567"] * 4)]
        kept, _ = thin_safe(recs)
        by_mb = {}
        for c in kept:
            by_mb.setdefault(c["catalog"]["mb"], []).append(c)
        self.assertEqual({"285", "566-567"}, set(by_mb))
        for c in kept:   # no keeper got another bucket's number
            self.assertIsInstance(c["catalog"]["mb"], str)

    def test_record_without_the_register_is_not_given_one(self):
        recs = [penny(f"kmk-{i}") for i in range(4)] + \
               [penny(f"kmk-{i}", mb="500") for i in range(4, 8)]
        kept, _ = thin_safe(recs)
        self.assertEqual(
            {(c["catalog"] or {}).get("mb") for c in kept}, {None, "500"})
        self.assertTrue(any(not c["catalog"] for c in kept))

    def test_same_index_still_thins(self):
        recs = [penny(f"kmk-{i}", mb="285") for i in range(6)]
        kept, stats = thin_safe(recs)
        self.assertEqual(3, len(kept))
        self.assertEqual(3, stats["dropped"])

    def test_others_labels_are_part_of_the_key(self):
        recs = [penny(f"kmk-{i}", others=[f"JSJ# {n}"]) for i, n in
                enumerate(["267"] * 4 + ["268"] * 4)]
        kept, _ = thin_safe(recs)
        for c in kept:
            self.assertEqual(1, len(c["catalog"]["others"]))


class TypeNumberContinuation(unittest.TestCase):
    def test_comma_continues_the_catalogue(self):
        self.assertEqual({"lange": ["541", "542"]}, cat("Lange 541, 542"))
        self.assertEqual({"schou": ["85", "88-89", "93"]},
                         cat("Schou 85, 88-89, 93"))
        self.assertEqual({"hede": "140A", "schou": ["59", "60"]},
                         cat("H:140A; Sch:59, 60"))

    def test_the_mb_case(self):
        self.assertEqual({"mb": ["285", "287", "319-320"]},
                         cat("MB 285, 287;  319-320"))

    def test_prefixed_segment_is_its_own_catalogue(self):
        self.assertEqual({"hauberg": "4", "mb": "558"}, cat("Hbg. 4, MB 558"))

    def test_non_numbers_are_not_continued(self):
        self.assertEqual({"schou": "12"}, cat("Schou 12, 2var."))
        self.assertEqual({"schou": "22"}, cat("sch 22; 4 mark!"))
        self.assertEqual({"lange": "948c"}, cat("Lange 2, 948c, var. 1"))

    def test_nothing_continues_a_segment_that_wrote_nothing(self):
        self.assertEqual({}, cat("Lange conf., 547"))
        self.assertEqual({}, cat("Jvf. Lange I, 325"))
        self.assertEqual({"dav": "5366"}, cat("Dav 5366; Gaedechens II, 479"))

    def test_alternatives_are_not_indices(self):
        self.assertEqual({"hede": "86"}, cat("H. 86, 101, 102 eller 137?"))
        self.assertEqual({"hede": "101"}, cat("H. 101, 102 ell. 137"))


class SpacedSubVariantLetter(unittest.TestCase):
    """«H 3 B» lost its B on ~250 records: the number match stopped at the
    digits. A lone letter is part of the index; alternatives are not."""

    def test_lone_letter_is_kept(self):
        self.assertEqual({"hede": "3B"}, cat("H 3 B"))
        self.assertEqual({"hede": "71c"}, cat("H. 71 c"))
        self.assertEqual({"galster": "57B"}, cat("Galster 57 B"))
        self.assertEqual({"lange": "504A"}, cat("Lange 1, 504 A"))

    def test_alternatives_keep_only_the_base(self):
        self.assertEqual({"hede": "151"}, cat("H: 151 A el. B"))
        self.assertEqual({"hede": "119"}, cat("H. 119 B-C"))
        self.assertEqual({"hede": "119"}, cat("H. 119 B?"))
        self.assertEqual({"hede": "80"}, cat("Hede 80 e/g"))


class AuctionCatalogueNumber(unittest.TestCase):
    def test_nr_form_reads_the_number(self):
        from build_kmk_seed import _raadata_catalog
        self.assertEqual({"others": ["Auk.Kat.# 1573", "Auk.Kat.# 4003"]},
                         _raadata_catalog(["auk. Kat. Nr. 1573",
                                           "Auk. Kat. no. 4003"]))
        self.assertEqual({}, _raadata_catalog(["Auk. Kat. Nr"]))


class LangeVolumeIsNotTheIndex(unittest.TestCase):
    def test_volume_before_number(self):
        self.assertEqual({"lange": "503-04"}, cat("Lange 1, 503-04"))
        self.assertEqual({"lange": "504A"}, cat("Lange 1, 504 A"))
        self.assertEqual({"lange": "542c"}, cat("Lange 2, 542c"))
        self.assertEqual({"lange": "324"}, cat("Lange I, 324"))
        self.assertEqual({"lange": "359"}, cat("Lange 1, nr. 359"))

    def test_plain_lange_one_untouched(self):
        self.assertEqual({"lange": "1"}, cat("Lange 1"))


if __name__ == "__main__":
    unittest.main()
