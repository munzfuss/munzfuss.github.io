"""The status stripe («чинний стандарт») used to start at `first_adoption`.

That field also starts the circulation stripe and anchors the founding-era
mint start, so a standard that was in use long before any act prescribed it —
the Rhenish gulden circulated in Denmark from the 15th century, the Møntordning
of 1514 first prescribed it — could not show both facts: either the status
stripe began with circulation, or `first_adoption` had to lie about when the
gulden came into use. `std_start` (curator 2026-10-11) carries the start of
legal force; the status stripe uses it, and falls back to `first_adoption`
per scope when it is absent.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.schema import FussEvent, FussEvents  # noqa: E402
from lib.timeline import compute_bar_layers  # noqa: E402


def _status(events: FussEvents) -> list[dict]:
    bar = SimpleNamespace(id="x", events=events)
    layers = compute_bar_layers([bar], {}, 1400, 1914)["x"]
    return [l for l in layers if "status" in (l.get("kinds") or [l["kind"]])]


class StatusLayerStart(unittest.TestCase):
    def test_std_start_sets_the_status_start(self):
        ev = FussEvents(first_adoption=FussEvent(anywhere=1424),
                        std_start=FussEvent(anywhere=1514),
                        std_end=FussEvent(anywhere=1602, approx_anywhere=True))
        st = _status(ev)
        self.assertEqual([(l["first"], l["last"]) for l in st], [(1514, 1602)])
        self.assertTrue(st[0]["last_approx"])

    def test_without_std_start_the_status_starts_at_first_adoption(self):
        ev = FussEvents(first_adoption=FussEvent(anywhere=1424),
                        std_end=FussEvent(anywhere=1602))
        self.assertEqual([(l["first"], l["last"]) for l in _status(ev)], [(1424, 1602)])

    def test_scope_without_std_start_falls_back(self):
        ev = FussEvents(first_adoption=FussEvent(anywhere=1424, holstein=1495),
                        std_start=FussEvent(anywhere=1514),
                        std_end=FussEvent(anywhere=1602, holstein=1602))
        got = sorted((l["scope"], l["first"]) for l in _status(ev))
        self.assertEqual(got, [("anywhere", 1514), ("holstein", 1495)])


if __name__ == "__main__":
    unittest.main()
