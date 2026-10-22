"""The stage-3 id migration renames every final; the gate must still see a loss.

D49 stage 3 turns every final `id` into its head class id and keeps the old
id in `legacy_id`. `verify_reflow` pairs HEAD ↔ current by final id, so on
the migration commit every HEAD coin would read as vanished (14 of them
carry no URL and would be COIN GONE) and, worse, no field-level comparison
would run at all — a real reclassification could ride the migration unseen.
`_translate` re-keys the HEAD side into class-id space through the registry
labels and the finals' `legacy_id`, so a renamed coin that also lost a value
is still reported.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import verify_reflow as vr  # noqa: E402


class LegacyPairing(unittest.TestCase):
    def setUp(self):
        self._saved = vr._LEGACY
        vr._LEGACY = {"unified-dk-hede-c4h2": "c-aaaa0001",
                      "unified-kmk-1": "c-aaaa0002"}

    def tearDown(self):
        vr._LEGACY = self._saved

    def test_translate_rekeys_id_and_composed_of(self):
        head = {"unified-dk-hede-c4h2": {"id": "unified-dk-hede-c4h2",
                                         "composed_of": ["unified-dk-hede-c4h2", "unified-kmk-1"],
                                         "fuss": "x"}}
        out = vr._translate(head)
        self.assertEqual(list(out), ["c-aaaa0001"])
        self.assertEqual(out["c-aaaa0001"]["composed_of"], ["c-aaaa0001", "c-aaaa0002"])
        self.assertEqual(out["c-aaaa0001"]["fuss"], "x")

    def test_renamed_coin_with_a_real_loss_is_still_reported(self):
        head = {"unified-dk-hede-c4h2": {"id": "unified-dk-hede-c4h2", "fuss": "nobel_fod",
                                         "phase": "I", "kind": "kurant", "nominal": "1 Nobel",
                                         "composed_of": ["unified-dk-hede-c4h2"],
                                         "sources": [{"url": "https://x/1"}]}}
        cur = {"c-aaaa0001": {"id": "c-aaaa0001", "legacy_id": "unified-dk-hede-c4h2",
                              "fuss": "nobel_fod", "phase": "I", "kind": "kurant",
                              "nominal": None, "composed_of": ["c-aaaa0001"],
                              "sources": [{"url": "https://x/1"}]}}
        r = vr.compare_coins("danish_realm", vr._translate(head), cur,
                             excluded=set(), retracted={}, elsewhere={}, head_members={})
        self.assertTrue(any("nominal" in ln for ln in r["losses"]), r)
        self.assertFalse(any("COIN GONE" in ln for ln in r["losses"]), r)


if __name__ == "__main__":
    unittest.main()
