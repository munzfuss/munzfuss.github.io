"""The reign-span flag must come off when the year stops being a reign window.

`year_is_reign_span` marks one narrow thing: the coin's year range is EXACTLY
its ruler's reign, i.e. the cataloguer tagged the piece with a reign because the
mint year is unknown. The absorb override sets it and forces `year_verified:
false`, so the renderer shows «(?)» and the coin never drives phase expansion.

It could only ever set. The flag is also foundation-immutable, copied verbatim
across regens, so a coin that LATER acquires a real year keeps claiming to be a
reign placeholder. Not hypothetical: `unified-dk-hede-f3h81` carried
«1648-1670» (Frederik III's reign) until a parser fix gave its row the year
danskmoent actually prints, 1669 — and it still rendered «(?)» afterwards.

The subtle half is `year_verified`. The obvious repair — «recompute the
OR-merge» — does nothing, because `members[0]` IS the foundation, so the stale
False this rule wrote last run re-elects itself. The clear therefore asks the
OTHER members only, and falls back to the schema default when none of them has
an opinion.

The clear is narrow on purpose: it fires only when a reign window EXISTS for the
ruler and the range no longer equals it. A curator's hand-set flag on a ruler
`_reign_window` cannot resolve (the German dukes and counts) never reaches the
branch — `_rw is None` leaves the whole override alone.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "absorb_seeds_into_final_v2",
    ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
AB = importlib.util.module_from_spec(_spec)
sys.modules["absorb_seeds_into_final_v2"] = AB
_spec.loader.exec_module(AB)

REIGN = AB._reign_window(AB._norm_ruler("Frederik III."))


def enrich(first, last, *, flag=True, member_extra=None, ruler="Frederik III."):
    """Absorb one foundation that arrives carrying the reign-span flag."""
    rng = [[first, last]]
    coin = {"id": "t", "ruler": ruler, "nominal": "2 Speciedaler",
            "composed_of": ["m"], "year_first": first, "year_last": last,
            "year_ranges": rng, "year_verified": False}
    if flag:
        coin["year_is_reign_span"] = True
    member = {"id": "m", "ruler": ruler, "year_first": first,
              "year_last": last, "year_ranges": rng}
    member.update(member_extra or {})
    out, _ = AB._enrich_final_entry(coin, [coin, member], "danish_realm")
    return out


class TestTheWindowResolves(unittest.TestCase):
    def test_frederik_iii(self):
        # The whole rule depends on this lookup; if it ever returns None the
        # override silently stops firing in BOTH directions.
        self.assertEqual(list(REIGN), [1648, 1670])


class TestTheFlagClears(unittest.TestCase):
    def test_an_attested_year_drops_the_flag(self):
        self.assertNotIn("year_is_reign_span", enrich(1669, 1669))

    def test_and_takes_the_question_mark_with_it(self):
        # Absent means the schema default (verified) — no «(?)» on the page.
        self.assertNotIn("year_verified", enrich(1669, 1669))

    def test_a_year_inside_the_reign_still_counts_as_attested(self):
        # 1669 lies inside 1648-1670. Equality is the test, not containment.
        out = enrich(1669, 1669)
        self.assertEqual(out["year_first"], 1669)
        self.assertNotIn("year_is_reign_span", out)


class TestTheFlagStays(unittest.TestCase):
    def test_a_range_equal_to_the_reign_keeps_both(self):
        out = enrich(1648, 1670)
        self.assertIs(out.get("year_is_reign_span"), True)
        self.assertIs(out.get("year_verified"), False)

    def test_another_member_saying_unverified_is_respected(self):
        # The flag goes (the range isn't the reign) but the «(?)» stays,
        # because something other than the stale self-assertion asks for it.
        out = enrich(1669, 1669, member_extra={"year_verified": False})
        self.assertNotIn("year_is_reign_span", out)
        self.assertIs(out.get("year_verified"), False)

    def test_a_duke_whose_name_resolves_to_the_wrong_king_is_left_alone(self):
        # «Frederik III. von Gottorp» normalises to the DANISH Frederik III, so
        # the window that comes back (1648-1670) is someone else's reign; the
        # duke's own is 1616-1659. Clearing on that basis would strip the
        # curator's flag from km-44, whose range is right and whose lookup is
        # wrong. The guard is what stops it.
        out = enrich(1616, 1659, ruler="Frederik III. von Gottorp")
        self.assertIs(out.get("year_is_reign_span"), True)

    def test_the_numeral_form_is_not_a_qualifier(self):
        # «Christian 4» is the same man as «Christian IV» — the guard must look
        # through the numeral, or half the KMM-sourced coins never clear.
        self.assertTrue(AB._reign_lookup_is_exact("Christian 4"))
        self.assertTrue(AB._reign_lookup_is_exact("Frederik III."))
        self.assertFalse(AB._reign_lookup_is_exact("Frederik 3 af Holstein-Gottorp"))

    def test_a_coin_that_never_had_the_flag_is_untouched(self):
        out = enrich(1669, 1669, flag=False)
        self.assertNotIn("year_is_reign_span", out)
        self.assertIs(out.get("year_verified"), False)


class TestTheLiveDataAgrees(unittest.TestCase):
    def test_f3h81_has_a_real_year_and_no_reign_flag(self):
        import yaml
        with open(ROOT / "data" / "v2" / "final" / "danish_realm.yml") as fh:
            d = yaml.safe_load(fh)
        coin = next(c for c in d["coins"]
                    if (c.get("label") or c.get("id")) == "unified-dk-hede-f3h81")
        self.assertEqual(coin.get("year_first"), 1669)
        self.assertEqual(coin.get("year_last"), 1669)
        self.assertNotIn("year_is_reign_span", coin)


if __name__ == "__main__":
    unittest.main()
