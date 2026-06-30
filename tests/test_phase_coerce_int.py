"""Regression: `Coin.phase` coerces a bare YAML integer to `str`.

A curator who writes `phase: 0` (no quotes) in a YAML produces a Python int,
which used to fail the `phase: str | dict[str, str]` type — the c3g-131 case
(audit_v2 I4 «phase.str», caught 2026-06-30). A `field_validator(mode="before")`
now coerces int → str so `0` becomes '0', and coerces int values inside the
per-location dict form. `bool` (an int subclass) is deliberately NOT coerced —
`phase: true` is not a valid phase and must still fail.

Run:
    .venv/bin/python -m unittest tests.test_phase_coerce_int -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.schema import Coin  # noqa: E402

_BASE = dict(id="t", fuss="9_thaler", kind="kurant", nominal="4 Mark",
             year_label="1659", year_first=1659)


def _phase(p):
    return Coin(phase=p, **_BASE).phase


class TestPhaseCoerceInt(unittest.TestCase):
    def test_int_zero_coerced(self):
        # the literal c3g-131 case: `phase: 0` (unquoted YAML int)
        self.assertEqual(_phase(0), "0")

    def test_int_nonzero_coerced(self):
        self.assertEqual(_phase(5), "5")

    def test_str_unchanged(self):
        for s in ("A", "II", "A1", "hede", "0"):
            self.assertEqual(_phase(s), s)

    def test_dict_int_value_coerced(self):
        # per-location dict form with a stray int value
        self.assertEqual(
            _phase({"denmark": 0, "schleswig_holstein": "A"}),
            {"denmark": "0", "schleswig_holstein": "A"},
        )

    def test_bool_still_rejected(self):
        # bool is an int subclass but is NOT a valid phase — must still fail
        with self.assertRaises(Exception):
            _phase(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
