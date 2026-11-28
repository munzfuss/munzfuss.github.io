"""A source's AVERAGE weight takes its finenesses; its range bounds take none.

Curator 2026-11-28 (Galster 4): Galster and Lindahl print a type's weight
range AND its average («0,50-1,00g, gennemsnitligt 0,70g», «gn. 0,70 g»)
together with a fineness range. The average is carried as a weight reading
marked approximate «(~)»; the source's finenesses pair with it, while the
range bounds stay on the page as weights without a fineness, instead of every
bound pairing with every fineness bound.

Run via:
    .venv/bin/python -m unittest tests.test_average_weight_pairing -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib import compute  # noqa: E402
from lib.schema import Coin, Fuss  # noqa: E402
from lib.weight_range import average_reason  # noqa: E402

SRC = "danskmoent.dk (Galster 4)"


def _fuss():
    return Fuss.model_validate({
        "name": {"de": "T", "en": "T", "uk": "T"},
        "metal": "silver", "grid_unit_g": 233.856, "grid_stops": 72,
        "fineness_standard": 0.75, "fractions": {},
    })


def _coin(weights, finenesses, ranges):
    return Coin.model_validate({
        "id": "t", "fuss": "t", "phase": "A", "kind": "kurant",
        "nominal": "1 Sterling", "year_label": "1405", "year_first": 1405,
        "weight_rough_g": weights, "fineness": finenesses,
        "weight_range_g": ranges,
    })


def _fine(cc):
    return sorted(round(g.value, 5) for g in cc.weight_fein_groups)


class AveragePairing(unittest.TestCase):
    FINS = [{"value": 0.606, "source": SRC}, {"value": 0.857, "source": SRC}]
    RNG = [{"min": 0.5, "max": 1.0, "source": SRC}]

    def test_average_takes_both_finenesses_bounds_none(self):
        avg = [{"value": 0.7, "source": SRC,
                "approximate": average_reason(SRC, "gennemsnitligt 0,70g", 0.7)}]
        cc = compute._compute_coin(_coin(avg, self.FINS, self.RNG), _fuss())
        self.assertEqual(_fine(cc), [round(0.7 * 0.606, 5), round(0.7 * 0.857, 5)])
        # the bounds are still shown as weights
        ws = sorted(round(g.value, 5) for g in cc.weight_groups)
        self.assertIn(0.5, ws)
        self.assertIn(1.0, ws)

    def test_without_average_bounds_keep_the_2026_11_05_rule(self):
        cc = compute._compute_coin(_coin(None, self.FINS, self.RNG), _fuss())
        self.assertEqual(_fine(cc), sorted({round(w * f, 5) for w in (0.5, 1.0)
                                            for f in (0.606, 0.857)}))

    def test_average_reason_quotes_and_translates(self):
        why = average_reason("Lindahl 1955 (NNÅ 1955), s. 78", "gn. 0,70 g", 0.7)
        self.assertEqual(why["da"], "[b]Lindahl 1955 (NNÅ 1955), s. 78[/b] angiver "
                                    "typens gennemsnitsvægt: [i]«gn. 0,70 g»[/i].")
        self.assertIn("у середньому 0,70 г", why["uk"])
        self.assertIn("on average 0.70 g", why["en"])
        self.assertIn("durchschnittlich 0,70 g", why["de"])


if __name__ == "__main__":
    unittest.main()
