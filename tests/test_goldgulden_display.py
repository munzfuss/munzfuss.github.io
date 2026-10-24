"""The gold gulden's display nominal on a Denmark-page class is «Goldgulden»
(curator 2026-10-24). Seeds keep the source's spelling; the merger writes
this form on the unified entry.

    .venv/bin/python -m unittest tests.test_goldgulden_display -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.nominal_synonyms import canonical_nominal_display  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "maintenance"))
from merge_seeds_cross_source import _canonical_nominal_out  # noqa: E402


class Display(unittest.TestCase):
    def test_source_forms_fold(self):
        for raw, want in [("1 Rhinsk Gylden", "1 Goldgulden"), ("1 Gold Gulden", "1 Goldgulden"),
                          ("2 Guldens", "2 Goldgulden"), ("½ Gulden", "½ Goldgulden"),
                          ("1 Guilder", "1 Goldgulden"), ("2 Rhinsk Gylden", "2 Goldgulden"),
                          ("1 Goldgulden", "1 Goldgulden")]:
            self.assertEqual(canonical_nominal_display(raw, "gold", "danish_realm"), want, raw)

    def test_left_alone(self):
        for raw, metal, ent in [("1 Ungersk Gylden", "gold", "danish_realm"),
                                ("1 Guilder, Hungarian Guilder", "gold", "danish_realm"),
                                ("1 Gulden", "silver", "danish_realm"),
                                ("1 Goldgulden (3.25)", "gold", "danish_realm"),
                                ("1 Gulden", "gold", "herzogtum_braunschweig_lueneburg")]:
            self.assertEqual(canonical_nominal_display(raw, metal, ent), raw, raw)


class MergerHook(unittest.TestCase):
    def test_gold_class_folds(self):
        out = {"nominal": "1 Rhinsk Gylden"}
        _canonical_nominal_out(out, [{"metal": "gold"}, {"metal": None}], "danish_realm")
        self.assertEqual(out["nominal"], "1 Goldgulden")

    def test_mixed_metal_class_untouched(self):
        out = {"nominal": "1 Gulden"}
        _canonical_nominal_out(out, [{"metal": "gold"}, {"metal": "silver"}], "danish_realm")
        self.assertEqual(out["nominal"], "1 Gulden")

    def test_member_hold_freezes(self):
        out = {"nominal": "1 Rhinsk Gylden"}
        _canonical_nominal_out(out, [{"metal": "gold", "_curation_holds": {"nominal": "x"}}],
                               "danish_realm")
        self.assertEqual(out["nominal"], "1 Rhinsk Gylden")


if __name__ == "__main__":
    unittest.main()
