"""KMM typeNumber: «ff» / «var» written onto the number are not sub-variants.

«sch 141ff» is Schou 141 «og følgende» (and following), «Sch 154var» a variant
of Schou 154; read as a sub-variant letter they became the phantom Schou
numbers 141f / 154v (curator 2026-10-22). A real sub-variant letter stays,
also when more letters follow it («H 106Abeta» → Hede 106A, «Lange 358Ea» →
Lange 358E).

Run: .venv/bin/python -m unittest tests.test_kmk_ff_var_suffix -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

from build_kmk_seed import _catalog  # noqa: E402


class FfVarSuffix(unittest.TestCase):
    def test_ff_and_var_dropped(self) -> None:
        for tn, want in [("sch 141ff", {"schou": "141"}),
                         ("G 31; Sch 154var", {"galster": "31", "schou": "154"}),
                         ("Sch 141 ff.", {"schou": "141"})]:
            self.assertEqual(_catalog({"typeNumber": tn}), want, tn)

    def test_real_sub_variant_letter_kept(self) -> None:
        for tn, want in [("H 106Abeta", {"hede": "106A"}),
                         ("G 39b", {"galster": "39B"})]:
            self.assertEqual(_catalog({"typeNumber": tn}), want, tn)


if __name__ == "__main__":
    unittest.main()
