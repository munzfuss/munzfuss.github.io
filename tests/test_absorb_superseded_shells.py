"""A final whose seed moved into a bigger class must not keep rendering its old row.

A standalone-promoted final is keyed `unified-<seed>`. When that seed later
joins a larger class, the stale purge empties the final's composed_of, the
stale-foundation purge drops it — and the monotonic guard re-promotes it
verbatim on the same run, because its seed is still alive somewhere. 159 such
shells were found 2026-09-28, most in `_unclassified` after the 2026-08 IKMK
re-routing, and 122 of them looked «curated» only because they carried the
seed's own IKMK description as `note`. The rule: a shell is superseded when
its id is `unified-<seed>`, it has no live member, and `<seed>` sits in a
class with another id; it is dropped unless it carries a curator decision.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import absorb_seeds_into_final_v2 as ab  # noqa: E402


class SupersededShells(unittest.TestCase):
    def setUp(self):
        self._saved = (ab._SEED_CLASS_INDEX, dict(ab._CLASS_NOTES))
        ab._SEED_CLASS_INDEX = {"ikmk-1": "unified-dk-numista-9", "ikmk-2": "unified-ikmk-2"}
        ab._CLASS_NOTES.clear()
        ab._CLASS_NOTES["unified-dk-numista-9"] = "IKMK description"

    def tearDown(self):
        ab._SEED_CLASS_INDEX = self._saved[0]
        ab._CLASS_NOTES.clear()
        ab._CLASS_NOTES.update(self._saved[1])

    def test_shell_detected(self):
        fe = {"id": "unified-ikmk-1", "composed_of": []}
        self.assertEqual(ab._superseding_class(fe, set()), "unified-dk-numista-9")

    def test_live_member_is_not_a_shell(self):
        fe = {"id": "unified-ikmk-1", "composed_of": ["unified-ikmk-1"]}
        self.assertIsNone(ab._superseding_class(fe, {"unified-ikmk-1"}))

    def test_own_class_is_not_a_shell(self):
        self.assertIsNone(ab._superseding_class({"id": "unified-ikmk-2"}, set()))

    def test_curator_id_is_never_a_shell(self):
        self.assertIsNone(ab._superseding_class({"id": "km-17-ja-1690"}, set()))

    def test_copied_note_is_not_curation(self):
        fe = {"id": "unified-ikmk-1", "fuss": "seed_unsorted", "phase": "ikmk",
              "note": "IKMK description"}
        self.assertFalse(ab._shell_is_curated(fe, "unified-dk-numista-9"))

    def test_own_note_and_real_fuss_are_curation(self):
        base = {"id": "unified-ikmk-1", "phase": "ikmk"}
        self.assertTrue(ab._shell_is_curated(dict(base, fuss="seed_unsorted", note="curator text"),
                                             "unified-dk-numista-9"))
        self.assertTrue(ab._shell_is_curated(dict(base, fuss="18_5_thaler", note="IKMK description"),
                                             "unified-dk-numista-9"))


class CuratedShellSettled(unittest.TestCase):
    """A Hede page split into sub-letters (202a5c1) left the CLASSIFIED final
    `unified-dk-hede-nc5h30` with no member beside a new seed_unsorted class
    `nc5h30a` holding all of them — the type rendered twice, its fuss on the
    empty row. 2026-10-09: the sub-letter class is recognised as the
    successor and takes the curation; siblings split across classes stay a
    curator question."""

    def setUp(self):
        self._saved = (ab._SEED_CLASS_INDEX, ab._SUB_LETTER_INDEX,
                       set(ab._SPLIT_SUB_LETTER_SHELLS))
        ab._SEED_CLASS_INDEX = {
            "dk-hede-nc5h30a": "unified-dk-hede-nc5h30a",
            "dk-hede-nc5h30b": "unified-dk-hede-nc5h30a",
            "dk-hede-nc5h56a": "unified-dk-hede-nc5h56a",
            "dk-hede-nc5h56b": "unified-dk-hede-nc5h56b",
        }
        ab._SUB_LETTER_INDEX = None

    def tearDown(self):
        ab._SEED_CLASS_INDEX, ab._SUB_LETTER_INDEX = self._saved[0], self._saved[1]
        ab._SPLIT_SUB_LETTER_SHELLS.clear()
        ab._SPLIT_SUB_LETTER_SHELLS.update(self._saved[2])

    SHELL = {"id": "unified-dk-hede-nc5h30", "composed_of": ["unified-dk-hede-nc5h30"],
             "fuss": "9_25_thaler", "phase": "I", "kind": "kurant", "fraction": "2",
             "note": {"en": "Obverse: portrait"}}

    def test_sub_letter_successor_found(self):
        self.assertEqual(ab._superseding_class(dict(self.SHELL), set()),
                         "unified-dk-hede-nc5h30a")

    def test_split_siblings_are_not_a_successor(self):
        fe = dict(self.SHELL, id="unified-dk-hede-nc5h56")
        self.assertIsNone(ab._superseding_class(fe, set()))
        self.assertIn("unified-dk-hede-nc5h56", ab._SPLIT_SUB_LETTER_SHELLS)

    def test_unsorted_successor_takes_the_curation(self):
        succ = {"id": "unified-dk-hede-nc5h30a", "fuss": "seed_unsorted", "phase": "hede"}
        self.assertTrue(ab._settle_curated_shell(dict(self.SHELL), succ))
        self.assertEqual((succ["fuss"], succ["phase"], succ["kind"], succ["fraction"]),
                         ("9_25_thaler", "I", "kurant", "2"))
        self.assertEqual(succ["note"], {"en": "Obverse: portrait"})

    def test_differently_classified_successor_keeps_the_shell(self):
        succ = {"id": "x", "fuss": "9_thaler", "phase": "I"}
        self.assertFalse(ab._settle_curated_shell(dict(self.SHELL), succ))
        self.assertEqual(succ["fuss"], "9_thaler")

    def test_unsorted_shell_hands_over_only_its_note(self):
        shell = dict(self.SHELL, fuss="seed_unsorted", phase="hede")
        succ = {"id": "y", "fuss": "seed_unsorted", "phase": "kmk"}
        self.assertTrue(ab._settle_curated_shell(shell, succ))
        self.assertEqual(succ["phase"], "kmk")
        self.assertEqual(succ["note"], {"en": "Obverse: portrait"})


if __name__ == "__main__":
    unittest.main()
