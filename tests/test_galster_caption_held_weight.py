"""build_galster_denmark_seed.apply_caption_ranges — a curator-held weight wins.

A caption weight fills `weight_range_g` only where the page gives no weight.
The fresh parse never carries a weight the curator entered by hand: merge_seed
restores it from `_curation_holds` after the builder runs. Without looking at
the held fields the filler added the same caption a second time
(dk-galster-halvrhin: 1,639 g held, plus a `weight_range_g` 1,639 g from the
same hg28.gif caption — one reading shown twice in the tooltip, 2026-10-30).

Run via:
    .venv/bin/python -m unittest tests.test_galster_caption_held_weight -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "build_galster_denmark_seed",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "build_galster_denmark_seed.py"),
)
_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bg)

CAP = {"page": "halvrhin.htm", "image": "gif/hg28.gif", "metal": "Au",
       "weight_min": 1.639, "weight_max": None, "approx": False}


class CaptionHeldWeightTest(unittest.TestCase):
    def _entry(self):
        return {"id": "dk-galster-halvrhin", "metal": "gold",
                "catalog": {"galster": "28"}}

    def test_no_hold_fills_range(self):
        e = self._entry()
        _bg._captions_for = lambda entry, caps: [CAP]
        self.assertEqual(_bg.apply_caption_ranges([e], {}), 1)
        self.assertEqual(e["weight_range_g"][0]["min"], 1.639)

    def test_held_weight_skips_range(self):
        e = self._entry()
        _bg._captions_for = lambda entry, caps: [CAP]
        held = {"dk-galster-halvrhin": {"weight_rough_g", "nominal"}}
        self.assertEqual(_bg.apply_caption_ranges([e], {}, held), 0)
        self.assertNotIn("weight_range_g", e)

    def test_other_hold_does_not_skip(self):
        e = self._entry()
        _bg._captions_for = lambda entry, caps: [CAP]
        held = {"dk-galster-halvrhin": {"nominal"}}
        self.assertEqual(_bg.apply_caption_ranges([e], {}, held), 1)


if __name__ == "__main__":
    unittest.main()
