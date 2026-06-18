"""Tests for `derive_mint_overrides` — auto-syncs each Fuß's
`events.first_mint.<scope>` / `last_mint.<scope>` to the actual coin span
on the page, where <scope> is the scope the page's own coins represent:
`anywhere` on a denmark_only-scope page (Denmark), `holstein` on the SH page.

Function under test:
    scripts/lib/timeline.py :: derive_mint_overrides

Behavioural rules (mirrors the prior holstein-only mechanism, generalised):
  - denmark_only page → sync the `anywhere` scope from loc.coins.
  - schleswig_holstein → sync the `holstein` scope (unchanged behaviour);
    the `anywhere` (Reich-wide curated) scope is left untouched.
  - Data is authoritative — full sync of both endpoints to min/max coin year.
  - A scope endpoint that is curator-`None` ("never minted here") stays None
    and the fuss is skipped, even if a coin exists.
  - `approx_<scope>` clears when an endpoint is overridden.
  - Already-in-sync fusses do not appear in the overlay.
  - Other locations → empty overlay.

Run via:
    .venv/bin/python -m unittest tests.test_derive_mint_overrides -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pydantic import BaseModel  # noqa: E402

from lib.schema import FussEvent, FussEvents  # noqa: E402
from lib.timeline import derive_mint_overrides  # noqa: E402


class FakeFuss(BaseModel):
    """Minimal stand-in for a Fuss carrying real `events` — enough for
    `derive_mint_overrides`, which only reads `.events` and calls
    `.model_copy(deep=True)` (a pydantic BaseModel method)."""
    events: FussEvents | None = None


def fuss(fm_any=None, lm_any=None, fm_hol=None, lm_hol=None,
         approx_any=False, approx_hol=False) -> FakeFuss:
    return FakeFuss(events=FussEvents(
        first_mint=FussEvent(anywhere=fm_any, holstein=fm_hol,
                             approx_anywhere=approx_any, approx_holstein=approx_hol),
        last_mint=FussEvent(anywhere=lm_any, holstein=lm_hol),
    ))


def coin(fid, year_first, year_last=None):
    return NS(fuss=fid, year_first=year_first, year_last=year_last)


def denmark(coins):
    return NS(id="denmark",
              timeline=NS(scope_mode="denmark_only", year_from=1514, year_to=1914),
              coins=coins)


def sh(coins):
    return NS(id="schleswig_holstein",
              timeline=NS(scope_mode="dual", year_from=1559, year_to=1914),
              coins=coins)


class TestDenmarkAnywhereSync(unittest.TestCase):
    def test_anywhere_synced_to_coin_span(self):
        """denmark_only page: anywhere mint events follow the coin min/max."""
        loc = denmark([
            coin("rhinsk", 1591, 1632),
            coin("rhinsk", 1671),          # single-year → last == first
            coin("rhinsk", 1600, 1605),
        ])
        fuesse = {"rhinsk": fuss(fm_any=1536, lm_any=1632)}
        ov = derive_mint_overrides(loc, fuesse)
        self.assertIn("rhinsk", ov)
        self.assertEqual(ov["rhinsk"].events.first_mint.anywhere, 1591)
        self.assertEqual(ov["rhinsk"].events.last_mint.anywhere, 1671)

    def test_approx_cleared_on_override(self):
        loc = denmark([coin("k", 1644, 1732)])
        fuesse = {"k": fuss(fm_any=1640, lm_any=1732, approx_any=True)}
        ov = derive_mint_overrides(loc, fuesse)
        self.assertEqual(ov["k"].events.first_mint.anywhere, 1644)
        self.assertFalse(ov["k"].events.first_mint.approx_anywhere)

    def test_none_anywhere_stays_none(self):
        """A curator-None anywhere mint endpoint is not promoted."""
        loc = denmark([coin("x", 1600, 1650)])
        fuesse = {"x": fuss(fm_any=None, lm_any=None)}
        self.assertEqual(derive_mint_overrides(loc, fuesse), {})

    def test_already_in_sync_no_override(self):
        loc = denmark([coin("y", 1618, 1668)])
        fuesse = {"y": fuss(fm_any=1618, lm_any=1668)}
        self.assertEqual(derive_mint_overrides(loc, fuesse), {})

    def test_does_not_touch_holstein_scope(self):
        loc = denmark([coin("z", 1591, 1671)])
        fuesse = {"z": fuss(fm_any=1536, lm_any=1632, fm_hol=1600, lm_hol=1620)}
        ov = derive_mint_overrides(loc, fuesse)
        # anywhere synced, holstein left exactly as curated
        self.assertEqual(ov["z"].events.first_mint.anywhere, 1591)
        self.assertEqual(ov["z"].events.first_mint.holstein, 1600)
        self.assertEqual(ov["z"].events.last_mint.holstein, 1620)


class TestSchleswigHolsteinHolsteinSync(unittest.TestCase):
    def test_holstein_synced_anywhere_untouched(self):
        """SH page still syncs the holstein scope (unchanged behaviour);
        anywhere (Reich-wide curated) is left alone."""
        loc = sh([coin("rdf", 1640, 1802), coin("rdf", 1657)])
        fuesse = {"rdf": fuss(fm_any=1481, lm_any=1871, fm_hol=1644, lm_hol=1800)}
        ov = derive_mint_overrides(loc, fuesse)
        self.assertIn("rdf", ov)
        self.assertEqual(ov["rdf"].events.first_mint.holstein, 1640)
        self.assertEqual(ov["rdf"].events.last_mint.holstein, 1802)
        # anywhere is NOT touched on the SH page
        self.assertEqual(ov["rdf"].events.first_mint.anywhere, 1481)
        self.assertEqual(ov["rdf"].events.last_mint.anywhere, 1871)

    def test_none_holstein_stays_none(self):
        loc = sh([coin("cph_only", 1644, 1696)])
        fuesse = {"cph_only": fuss(fm_any=1644, lm_any=1696, fm_hol=None, lm_hol=None)}
        self.assertEqual(derive_mint_overrides(loc, fuesse), {})


class TestTimelineWindowClamp(unittest.TestCase):
    def test_last_clamped_to_timeline_year_to(self):
        """A straddle type (1913-1931) clamps its mint last to year_to=1914."""
        loc = denmark([coin("k", 1873, 1931)])
        fuesse = {"k": fuss(fm_any=1873, lm_any=1875)}
        ov = derive_mint_overrides(loc, fuesse)
        self.assertEqual(ov["k"].events.first_mint.anywhere, 1873)
        self.assertEqual(ov["k"].events.last_mint.anywhere, 1914)  # clamped from 1931

    def test_reign_placeholder_clamped_not_1947(self):
        """A reign-window placeholder (1912-1947) clamps to 1914, not 1947."""
        loc = denmark([coin("k", 1873, 1914), coin("k", 1912, 1947)])
        fuesse = {"k": fuss(fm_any=1873, lm_any=1914)}
        ov = derive_mint_overrides(loc, fuesse)
        # last clamps to 1914 — already in sync with the event, so no override
        self.assertNotIn("k", ov)

    def test_coin_entirely_past_window_skipped(self):
        """A fuss whose only coin is past year_to contributes no override."""
        loc = denmark([coin("z", 2005, 2008)])
        fuesse = {"z": fuss(fm_any=1873, lm_any=1900)}
        self.assertEqual(derive_mint_overrides(loc, fuesse), {})


class TestOtherLocations(unittest.TestCase):
    def test_non_denmark_non_sh_is_noop(self):
        loc = NS(id="lubeck", timeline=NS(scope_mode="dual"), coins=[coin("a", 1600)])
        fuesse = {"a": fuss(fm_any=1500, lm_any=1700)}
        self.assertEqual(derive_mint_overrides(loc, fuesse), {})

    def test_no_timeline_is_noop(self):
        loc = NS(id="denmark", timeline=None, coins=[coin("a", 1600)])
        self.assertEqual(derive_mint_overrides(loc, {"a": fuss(fm_any=1500, lm_any=1700)}), {})


if __name__ == "__main__":
    unittest.main()
