"""The merger's year «(?)» decision (`_year_attestation`, curator 2026-10-29).

Before the fix, one undated member or one member with no year at all put
«(?)» on a year that other sources print plainly, because an absent
`year_verified` (the attested case) counted as «no information».
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


def m(sid, yf, yl=None, **kw):
    yl = yl if yl is not None else yf
    d = {"id": sid, "year_first": yf, "year_last": yl,
         "year_label": str(yf) if yf == yl else f"{yf}-{yl}"}
    d.update(kw)
    return d


class YearAttestation(unittest.TestCase):
    def test_reign_placeholder_does_not_beat_dated_sources(self):
        # Christian V 1671: Hede «u. år» (reign, demoted) vs four dated sources.
        ms = [m("dk-hede-nc5h1", 1670, 1699, year_verified=False, _year_demoted=True),
              m("dk-numista-117111", 1671), m("dk-tid-145788", 1671),
              m("ngc-1098155", 1671), m("denmark-numismaster-110810", 1671)]
        self.assertEqual(M._year_attestation(ms), (True, None))

    def test_member_without_year_does_not_poison(self):
        # Frederik III 1669: NGC record with no year carries year_verified False.
        ms = [{"id": "ngc-1095650", "year_verified": False},
              m("dk-hede-nf3h7", 1669), m("dk-numista-111175", 1669)]
        self.assertEqual(M._year_attestation(ms), (True, None))

    def test_unflagged_source_span_is_not_an_attestation(self):
        # Hans 1505-1510: Numista span vs Galster u.år reign placeholder.
        ms = [m("dk-galster-hg-gej", 1483, 1513, year_verified=False, _year_demoted=True),
              m("dk-numista-444264", 1505, 1510)]
        self.assertEqual(M._year_attestation(ms), (False, None))

    def test_hedged_source_against_plain_one_is_a_conflict(self):
        ms = [m("dk-bruun-1", 1661, year_verified=False), m("dk-hede-nf3h1", 1661)]
        yv, conflict = M._year_attestation(ms)
        self.assertIs(yv, False)
        self.assertEqual([r["source"] for r in conflict["confident"]], ["hede"])
        self.assertEqual([r["source"] for r in conflict["uncertain"]], ["bruun"])

    def test_kmm_plain_year_does_not_override_uncertain_sources(self):
        ms = [m("dk-hede-x", 1588, 1648, year_verified=False, _year_demoted=True),
              m("kmk-1", 1620)]
        self.assertEqual(M._year_attestation(ms)[0], False)
        # …but KMM with only plain company still attests (no False member →
        # the plain OR-merge, default True).
        self.assertIsNone(M._year_attestation([m("kmk-1", 1620), m("dk-hede-y", 1620)])[0])

    def test_kmm_is_listed_in_a_conflict_but_does_not_settle_it(self):
        ms = [m("ngc-1", 1611, year_verified=False), m("kmk-2", 1611)]
        yv, conflict = M._year_attestation(ms)
        self.assertIs(yv, False)
        self.assertEqual([r["source"] for r in conflict["confident"]], ["kmk"])

    def test_no_false_member_keeps_or_merge(self):
        self.assertIsNone(M._year_attestation([m("dk-hede-a", 1600)])[0])


if __name__ == "__main__":
    unittest.main()
