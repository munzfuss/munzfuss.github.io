"""Tests for source-precision-preserving display decimals.

`make_display_groups` must never render a source reading at fewer decimals
than the value itself carries (CLAUDE.md §3 — "store / show the source's
literal value, never round"). A Hede weight of 3.249 g must display as
«3.249», not «3.25», even though 3.25 is distinct from its neighbours at
the field-default 2-decimal precision.

Functions under test:
    scripts/lib/compute.py :: _natural_decimals, make_display_groups

Run via:
    .venv/bin/python -m unittest tests.test_display_decimals -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.compute import _natural_decimals, make_display_groups  # noqa: E402


def _render(value: float, decimals: int) -> str:
    """Mirror lib.i18n.fmt_num's strip-trailing-zeros / min-2-places logic
    (decimal-separator + unit stripped) so the test asserts on the exact
    rendered token."""
    s = f"{value:.{decimals}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
        if "." in s:
            i, d = s.split(".")
            if len(d) < 2:
                s = f"{i}.{d.ljust(2, '0')}"
        else:
            s = s + ".00"
    return s


def _texts(groups, default_precision):
    return [_render(g.value, g.display_decimals if g.display_decimals is not None
                    else default_precision) for g in groups]


class TestNaturalDecimals(unittest.TestCase):
    def test_three_decimal_value(self):
        self.assertEqual(_natural_decimals(3.249, 2, 4), 3)

    def test_two_decimal_value(self):
        self.assertEqual(_natural_decimals(3.16, 2, 4), 2)

    def test_floor_respected(self):
        # 3.2 is exact at 1 decimal but the weight floor is 2
        self.assertEqual(_natural_decimals(3.2, 2, 4), 2)

    def test_four_decimal_fineness(self):
        self.assertEqual(_natural_decimals(0.9792, 3, 5), 4)

    def test_cap_at_hi(self):
        # needs >3 decimals but diameter caps at 3
        self.assertEqual(_natural_decimals(28.5559, 1, 3), 3)


class TestDisplayDecimals(unittest.TestCase):
    def test_rhinsk_gylden_preserves_three_decimals(self):
        """The real case: Bruun 3.16/3.18/3.22 + Hede/NM/Numista 3.249 g.
        The 3.249 group must render «3.249», never «3.25»."""
        pairs = [(3.16, "bruun"), (3.18, "bruun"), (3.22, "bruun"),
                 (3.249, "hede"), (3.249, "numismaster"), (3.249, "numista")]
        groups = make_display_groups(pairs, 2)
        texts = _texts(groups, 2)
        self.assertIn("3.249", texts)
        self.assertNotIn("3.25", texts)
        self.assertEqual(set(texts), {"3.16", "3.18", "3.22", "3.249"})
        # the three 3.249 readings collapse into ONE group, sources accumulated
        g249 = [g for g in groups if abs(g.value - 3.249) < 1e-9][0]
        self.assertEqual(g249.sources, ["hede", "numismaster", "numista"])

    def test_unanimous_three_decimal_not_rounded(self):
        """A lone 3-decimal reading must keep its precision (the old adaptive
        rule skipped the unanimous case → would have rounded to 3.25)."""
        groups = make_display_groups([(3.249, "hede")], 2)
        self.assertEqual(_texts(groups, 2), ["3.249"])

    def test_sub_precision_distinct_groups_stay_distinct(self):
        """2.386 and 2.390 both round to «2.39» at 2 decimals — must remain
        visually distinct (2.386 carries a 3rd decimal)."""
        groups = make_display_groups([(2.386, "hede"), (2.390, "nm")], 2)
        texts = _texts(groups, 2)
        self.assertEqual(len(set(texts)), 2)
        self.assertIn("2.386", texts)
        self.assertIn("2.39", texts)

    def test_plain_two_decimal_pair_not_bumped(self):
        """Values exact at the field precision keep display_decimals=None
        (template uses its default) — no needless padding."""
        groups = make_display_groups([(3.16, "a"), (3.22, "b")], 2)
        self.assertTrue(all(g.display_decimals is None for g in groups))

    def test_fineness_four_decimal_reading(self):
        """Fineness precision is 3; a 4-decimal source reading shows 4."""
        groups = make_display_groups([(0.9792, "hede")], 3)
        self.assertEqual(_texts(groups, 3), ["0.9792"])


if __name__ == "__main__":
    unittest.main()
