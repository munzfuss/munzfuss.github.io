"""Unit tests for the year-hold guard on the pure-absorbed fast-path in the
absorb step (`_enrich_final_entry`, 2026-07-15).

A "pure-absorbed" foundation is a `unified-*` final whose `composed_of` is a
single member with its own id — i.e. just a pulled-through seed_unified copy
with no curator-composed additions. For those the absorb trusts the seed
member's `year_ranges` directly (the seed accumulates all current source
attestations). BUT when the curator has hand-corrected the year and frozen it
via `_curation_holds: {year_ranges|year_first}`, that fast-path silently
reverted the correction — e.g. sonderburg `unified-schleswig_holstein-
numismaster-120994`, curator-corrected to 1622 (Numista N#151529) while the
NumisMaster seed carries «ND(1618-22)» whose range-start is 1618. The guard
makes the pure-absorbed branch honour a year hold, mirroring the `else` branch.

Run via:
    .venv/bin/python -m unittest tests.test_absorb_year_hold_pure_absorbed -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from absorb_seeds_into_final_v2 import _enrich_final_entry  # noqa: E402


def _yr(final, members):
    out, _ = _enrich_final_entry(final, members, "sonderburg_duchy")
    return out.get("year_first"), out.get("year_last")


def _foundation(cid, extra=None):
    f = {"id": cid, "composed_of": [cid],
         "year_first": 1622, "year_last": 1622, "year_ranges": [[1622, 1622]]}
    if extra:
        f.update(extra)
    return f


def _seed(cid):
    return {"id": cid, "year_first": 1618, "year_last": 1618,
            "year_ranges": [[1618, 1618]]}


class YearHoldPureAbsorbed(unittest.TestCase):
    def test_year_ranges_hold_honoured(self):
        # sonderburg 120994: curator 1622, seed «ND(1618-22)» → 1618. hold wins.
        f = _foundation("unified-a",
                        {"_curation_holds": {"year_ranges": "curator 1622"}})
        self.assertEqual(_yr(f, [f, _seed("unified-a")]), (1622, 1622))

    def test_year_first_hold_also_honoured(self):
        f = _foundation("unified-b",
                        {"_curation_holds": {"year_first": "curator 1622"}})
        self.assertEqual(_yr(f, [f, _seed("unified-b")]), (1622, 1622))

    def test_list_form_hold_honoured(self):
        f = _foundation("unified-c", {"_curation_holds": ["year_ranges"]})
        self.assertEqual(_yr(f, [f, _seed("unified-c")]), (1622, 1622))

    def test_no_hold_seed_year_wins(self):
        # control: without a year hold the pure-absorbed fast-path trusts seed.
        f = _foundation("unified-d")
        self.assertEqual(_yr(f, [f, _seed("unified-d")]), (1618, 1618))

    def test_unrelated_hold_does_not_freeze_year(self):
        # a hold on a DIFFERENT field must not freeze the year.
        f = _foundation("unified-e", {"_curation_holds": {"fineness": "x"}})
        self.assertEqual(_yr(f, [f, _seed("unified-e")]), (1618, 1618))


if __name__ == "__main__":
    unittest.main()
