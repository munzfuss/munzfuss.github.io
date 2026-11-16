"""The fused «Reichsbankschilling» is the Rigsbankskilling, like the spaced form.

The Altona Rigsbankskilling carries the German legend «Reichsbank Schilling».
The synonym rule matched it only with a space or hyphen, so Bruun 8084
(«16 Reichsbankschilling», Hede 30C) normalised to a different name and the
Hede-base review reported the Hede 30 group as two nominals (2026-11-16).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.nominal_synonyms import normalise_nominal  # noqa: E402


class Reichsbankschilling(unittest.TestCase):
    def test_fused_spaced_and_danish_forms_meet(self):
        want = normalise_nominal("16 Rigsbankskilling")
        for raw in ("16 Reichsbankschilling", "16 Reichsbank Schilling",
                    "16 Reichsbank Schillings", "16 Reichsbank-Schilling"):
            self.assertEqual(normalise_nominal(raw), want, raw)


if __name__ == "__main__":
    unittest.main()
