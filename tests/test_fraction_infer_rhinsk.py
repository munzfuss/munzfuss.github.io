"""rhinsk_gylden_fod fraction inference — «N Goldgulden» / «N Rhinsk gylden» → N.

The gold Rhinsk-Gyldenfod (Goldgulden / Rhinsk Gylden, .75-.77) had NO entry in
`fraction_infer.RULES`, so `infer_fraction()` returned None for its coins. Without
`fraction` set, the build cannot look up `fuss.fractions[fraction]`, so the
Soll-Feingewicht + Δ columns stay blank (surfaced on the Norway Hans Bergen
Goldgulden unified-dk-numista-444264, 2026-07-13). This test guards the added
rule (mirrors the goldgulden/gylden handling under reichsdukatenfuss — distinct
fuss, so it needs its own RULES entry).

Run: .venv/bin/python -m unittest tests.test_fraction_infer_rhinsk -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.fraction_infer import infer_fraction, load_fuss_fractions  # noqa: E402


class RhinskGyldenFraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cache = load_fuss_fractions()

    def _infer(self, nominal: str):
        return infer_fraction(
            {"nominal": nominal, "fuss": "rhinsk_gylden_fod"}, self.cache
        )

    def test_one_goldgulden(self) -> None:
        self.assertEqual(self._infer("1 Goldgulden"), "1")

    def test_one_rhinsk_gylden(self) -> None:
        self.assertEqual(self._infer("1 Rhinsk gylden"), "1")

    def test_one_guldgylden(self) -> None:
        self.assertEqual(self._infer("1 Guldgylden"), "1")

    def test_two_goldgulden(self) -> None:
        # 2 Goldgulden (doppelt) — the "2" fraction key exists in the fuss.
        self.assertEqual(self._infer("2 Goldgulden"), "2")


if __name__ == "__main__":
    unittest.main()
