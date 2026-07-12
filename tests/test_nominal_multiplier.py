"""Danish multiplier-prefix normalisation in v2_seed_writer._normalise_nominal.

Sources (esp. KMM / Nationalmuseet) spell a multiple-denomination coin with a
leading Danish multiplier word («dobbelt Portugaløser» = 2 Portugaløser) or an
«N-dobbelt» form («4-dobbelt Groschen» = 4 Groschen) instead of a digit. Before
the fix the count was silently lost — the bare denomination picked up an
implicit «1 » («1 Dobbelt portugaløser» / «1 Portugaløser»), which corrupted the
nominal and blocked cross-source merges (e.g. KMM «dobbelt portugaløser» never
matched the «2 Portugaløser» / Hede-4 type).

Compound single-word coin names («dobbelthvid», «firehvid») are period-attested
denominations, NOT «2 hvid» / «4 hvid», and must stay intact — the fix's
`\\s+`-after-multiplier guard protects them (no trailing space to match).

Run: .venv/bin/python -m unittest tests.test_nominal_multiplier -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.v2_seed_writer import _normalise_nominal


class TestDanishMultiplier(unittest.TestCase):
    def test_dobbelt_word(self):
        self.assertEqual(_normalise_nominal("dobbelt portugaløser"), "2 Portugaløser")
        self.assertEqual(_normalise_nominal("Dobbelt Speciedaler"), "2 Speciedaler")
        self.assertEqual(_normalise_nominal("dobbelt dukat"), "2 Dukat")

    def test_higher_word_multipliers(self):
        self.assertEqual(_normalise_nominal("tredobbelt dukat"), "3 Dukat")
        self.assertEqual(_normalise_nominal("firdobbelt speciedaler"), "4 Speciedaler")

    def test_numeric_dobbelt_form(self):
        self.assertEqual(_normalise_nominal("4-dobbelt portugaløser"), "4 Portugaløser")
        self.assertEqual(_normalise_nominal("3-dobbelt speciedaler"), "3 Speciedaler")

    def test_compound_denomination_preserved(self):
        # single-word compound coin names must NOT split to «2 hvid» / «4 hvid»
        self.assertEqual(_normalise_nominal("dobbelthvid"), "1 Dobbelthvid")
        self.assertEqual(_normalise_nominal("firehvid"), "1 Firehvid")

    def test_plain_denomination_unchanged(self):
        self.assertEqual(_normalise_nominal("portugaløser"), "1 Portugaløser")
        self.assertEqual(_normalise_nominal("1/4 portugaløser"), "¼ Portugaløser")
        self.assertEqual(_normalise_nominal("2 Portugaløser"), "2 Portugaløser")


if __name__ == "__main__":
    unittest.main()
