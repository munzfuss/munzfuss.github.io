"""Test the mint-from-nominal RE-EXTRACTION after the annotation splitters
(seed-writer hygiene, 2026-07-15).

Function under test (indirectly):
    scripts/lib/v2_seed_writer.py :: _apply_pre_write_hygiene

The first `_extract_mint_from_nominal` pass runs on the raw parser nominal.
When the mint is followed by a REGION qualifier — «Hvid , Visby (Gotland)» —
the trailing-mint regex can't see the mint (it isn't end-of-string), so the
first pass leaves it in. `_normalise_nominal` + the annotation splitters then
strip «(Gotland)», exposing a bare trailing «, Visby». A SECOND extraction
pass (added 2026-07-15) catches it → clean «1 Hvid» + mint «Visby».

Without the second pass the fresh-build path disagreed with the orphan-
normalisation pass (which runs on already-normalised on-disk data and DID
strip it) — so the galster seed never reached a fixed point and every re-seed
re-added «, Visby» (perpetual churn). Real coins: dk-galster-hg-141 / hg-142 /
hg-146 (Visby Hvid), dk-galster-c2g-174 (Hamar Søsling klipping).

Run via:
    .venv/bin/python -m unittest tests.test_nominal_mint_reextract -v
"""
from __future__ import annotations

import sys
import unittest
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "v2_seed_writer",
    str(PROJECT_ROOT / "scripts" / "lib" / "v2_seed_writer.py"),
)
_w = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w)
_apply_pre_write_hygiene = _w._apply_pre_write_hygiene


def coin(**fields):
    base = {"id": "test", "nominal": "Test", "issuing_entity": "danish_realm",
            "metal": "silver"}
    base.update(fields)
    return base


class RegionSuffixedTrailingMint(unittest.TestCase):
    def test_visby_gotland_stripped_to_clean_nominal(self):
        # the dk-galster-hg-141 case: parser «Hvid , Visby (Gotland)» + Visby
        c = coin(nominal="Hvid , Visby (Gotland)", mint="Visby")
        out, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(out[0]["nominal"], "1 Hvid")
        self.assertEqual(out[0]["mint"], "Visby")

    def test_already_clean_unchanged(self):
        # idempotency: the already-normalised form must survive a re-run
        c = coin(nominal="1 Hvid", mint="Visby")
        out, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(out[0]["nominal"], "1 Hvid")
        self.assertEqual(out[0]["mint"], "Visby")

    def test_idempotent_two_passes(self):
        # running hygiene twice yields the same nominal (fixed point)
        c = coin(nominal="Hvid , Visby (Gotland)", mint="Visby")
        out1, _ = _apply_pre_write_hygiene([c])
        out2, _ = _apply_pre_write_hygiene([dict(out1[0])])
        self.assertEqual(out1[0]["nominal"], out2[0]["nominal"])
        self.assertEqual(out2[0]["nominal"], "1 Hvid")

    def test_no_mint_in_nominal_left_intact(self):
        # a nominal with no embedded mint must not be touched by the re-extract
        c = coin(nominal="1 Speciedaler", mint="Kopenhagen")
        out, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(out[0]["nominal"], "1 Speciedaler")


if __name__ == "__main__":
    unittest.main()
