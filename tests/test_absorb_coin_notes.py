"""Coin Notes come from data/v2/notes/<entity>.yml, keyed by seed id.

Found 2026-11-05 while trimming the period-0 Notes of the Lübeck standard on
the Denmark page: the Notes had been written on the Lindahl seeds, but absorb
carries `note` as curator prose of the final itself (`_SKELETON_CARRY`) and a
member's Note only gap-filled. A shortened seed Note therefore never replaced
the long one already on the final; the build showed the old text and the run
reported no loss, because nothing was lost — the edit simply did not travel.
The fix gives Notes their own surface keyed by seed id; these tests pin that
the file wins over a stored Note, that a final without an entry keeps its own,
and that two Notes on one coin stop the run instead of one silently winning.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import absorb_seeds_into_final_v2 as ab  # noqa: E402

NOTE = {"de": "D", "en": "E", "uk": "У", "da": "Da"}


def _write(tmp: Path, entity: str, body: str) -> None:
    (tmp / f"{entity}.yml").write_text(body, encoding="utf-8")


class CoinNotesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._p = mock.patch.object(ab, "V2_NOTES", self.tmp)
        self._p.start()

    def tearDown(self):
        self._p.stop()
        self._tmp.cleanup()

    def test_file_note_replaces_stored_note(self):
        _write(self.tmp, "ent", "entity: ent\nnotes:\n  - seed: s-1\n    note: {de: D, en: E, uk: У, da: Da}\n")
        unified = {"unified-s-1": {"id": "unified-s-1", "composed_of": ["s-1"]}}
        fe = {"id": "c-x", "composed_of": ["unified-s-1"], "note": {"de": "old", "en": "old", "uk": "old", "da": "old"}}
        keep = {"id": "c-y", "composed_of": [], "note": {"de": "mine"}}
        ab._apply_coin_notes("ent", [fe, keep], unified)
        self.assertEqual(fe["note"], NOTE)
        self.assertEqual(keep["note"], {"de": "mine"})

    def test_two_notes_on_one_final_stop_the_run(self):
        _write(self.tmp, "ent", "entity: ent\nnotes:\n"
               "  - seed: s-1\n    note: {de: D, en: E, uk: У, da: Da}\n"
               "  - seed: s-2\n    note: {de: D, en: E, uk: У, da: Da}\n")
        unified = {"u": {"id": "u", "composed_of": ["s-1", "s-2"]}}
        with self.assertRaises(SystemExit):
            ab._apply_coin_notes("ent", [{"id": "c-x", "composed_of": ["u"]}], unified)

    def test_note_missing_a_language_is_rejected(self):
        _write(self.tmp, "ent", "entity: ent\nnotes:\n  - seed: s-1\n    note: {de: D, en: E, uk: У}\n")
        with self.assertRaises(SystemExit):
            ab._load_coin_notes("ent")

    def test_no_file_changes_nothing(self):
        fe = {"id": "c-x", "note": {"de": "mine"}}
        ab._apply_coin_notes("absent", [fe], {})
        self.assertEqual(fe["note"], {"de": "mine"})


if __name__ == "__main__":
    unittest.main()
