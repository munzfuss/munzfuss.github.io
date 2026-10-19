"""A renamed class must go back to its classified final, not to a stale shell.

2026-10-17: once the NGC parser read «16Z4» as 1624, NGC 1050065 joined the
class that backed the classified final `dk-tid-163042` (24 Skilling KM 93,
9_25_thaler). The class took the NGC record's name, `unified-ngc-1050065` —
the id of the NGC record's own standalone seed_unsorted final. Absorb found
that id already in a final's composed_of, counted the class as absorbed into
the shell, purged the classified final's dead member ids as departed, and the
classified coin dropped out; verify_reflow saw it only as SEED DECLASSIFIED.
Eight classes went this way and were rescued three times by deleting the
shells by hand before absorb.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import absorb_seeds_into_final_v2 as ab  # noqa: E402

NEW = "unified-ngc-1050065"


class RenamedClassHandover(unittest.TestCase):
    def setUp(self):
        self._saved = (ab._SEED_CLASS_INDEX, dict(ab._CLASS_NOTES))
        ab._SEED_CLASS_INDEX = {"dk-tid-163042": NEW, "ngc-1050065": NEW,
                                "kmk-139735": NEW}
        ab._CLASS_NOTES.clear()

    def tearDown(self):
        ab._SEED_CLASS_INDEX = self._saved[0]
        ab._CLASS_NOTES.clear()
        ab._CLASS_NOTES.update(self._saved[1])

    def _finals(self, **shell_extra):
        return {
            "dk-tid-163042": {"id": "dk-tid-163042", "fuss": "9_25_thaler",
                              "composed_of": ["unified-dk-tid-163042",
                                              "unified-kmk-139735"]},
            NEW: dict({"id": NEW, "fuss": "seed_unsorted", "phase": "ngc",
                       "composed_of": [NEW]}, **shell_extra),
        }

    def test_class_returns_to_classified_final(self):
        finals = self._finals()
        done = ab._hand_over_renamed_classes(finals, {NEW: {}}, {})
        self.assertEqual(done, [f"{NEW} → dk-tid-163042"])
        self.assertNotIn(NEW, finals)
        self.assertIn(NEW, finals["dk-tid-163042"]["composed_of"])

    def test_curated_shell_is_left_alone(self):
        finals = self._finals(note="curator text")
        self.assertEqual(ab._hand_over_renamed_classes(finals, {NEW: {}}, {}), [])
        self.assertIn(NEW, finals)

    def test_two_claimants_are_left_alone(self):
        finals = self._finals()
        finals["km-93-chr-iv"] = {"id": "km-93-chr-iv", "fuss": "9_25_thaler",
                                  "composed_of": ["unified-ngc-1050065-old"]}
        ab._SEED_CLASS_INDEX["ngc-1050065-old"] = NEW
        self.assertEqual(ab._hand_over_renamed_classes(finals, {NEW: {}}, {}), [])

    def test_shell_with_other_members_is_left_alone(self):
        finals = self._finals()
        finals[NEW]["composed_of"] = [NEW, "unified-ikmk-9"]
        self.assertEqual(ab._hand_over_renamed_classes(finals, {NEW: {}}, {}), [])

    def test_live_member_is_no_claim(self):
        """A classified final whose members are all live claims nothing."""
        finals = self._finals()
        unified = {NEW: {}, "unified-dk-tid-163042": {}, "unified-kmk-139735": {}}
        self.assertEqual(ab._hand_over_renamed_classes(finals, unified, {}), [])


if __name__ == "__main__":
    unittest.main()
