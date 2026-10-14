"""A Grundwerte row may refer to an act (a `kind: decree` row of the same card)
from inside its value HTML: `<span class='gw-act' data-act='slug'>…</span>`.
The page script shows that decree row as a hover card and, when the decree
row itself only says «per the 1514 Møntordning», follows the reference to
the figures.

Three things the schema guards so the hover never dangles:

  * every `data-act` names a decree row of THIS card (a reworded or removed
    act row must fail validation, not silently lose its hover);
  * `act` sits on decree rows only, once per card;
  * decree→decree references form no cycle (the resolver follows them).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.schema import Grundwerte  # noqa: E402


def _row(key, value, **kw):
    t = {"de": key, "en": key, "uk": key}
    v = {"de": value, "en": value, "uk": value}
    return {"key": t, "value": v, **kw}


REF = "<span class='gw-phase'><span class='gw-phase-label'>P</span>per <span class='gw-act' data-act='{}'>X</span></span>"
FIG = "<span class='gw-phase'><span class='gw-phase-label'>P</span><b>72</b></span>"


class ActRefs(unittest.TestCase):
    def test_resolving_card_passes(self):
        gw = Grundwerte(rows=[
            _row("Worms 1495", FIG, kind="decree", act="worms-1495"),
            _row("Kongebrev 1524", REF.format("worms-1495"), kind="decree", act="kongebrev-1524"),
            _row("Period I", REF.format("kongebrev-1524")),
        ])
        self.assertEqual([r.act for r in gw.rows], ["worms-1495", "kongebrev-1524", None])

    def test_dangling_reference_raises(self):
        with self.assertRaisesRegex(ValueError, "names no decree row"):
            Grundwerte(rows=[_row("Period I", REF.format("nope-1514"))])

    def test_act_on_non_decree_row_rejected(self):
        with self.assertRaisesRegex(ValueError, "kind: decree rows only"):
            Grundwerte(rows=[_row("Period I", FIG, act="period-i")])

    def test_duplicate_act_rejected(self):
        with self.assertRaisesRegex(ValueError, "used by rows"):
            Grundwerte(rows=[_row("A", FIG, kind="decree", act="a"),
                             _row("B", FIG, kind="decree", act="a")])

    def test_cycle_raises(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            Grundwerte(rows=[
                _row("A", REF.format("b"), kind="decree", act="a"),
                _row("B", REF.format("a"), kind="decree", act="b"),
            ])

    def test_slug_shape(self):
        with self.assertRaises(ValueError):
            Grundwerte(rows=[_row("A", FIG, kind="decree", act="Not A Slug")])


if __name__ == "__main__":
    unittest.main()
