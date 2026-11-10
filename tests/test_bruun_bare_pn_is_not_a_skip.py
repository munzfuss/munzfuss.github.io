"""A bare Krause `Pn` number must NOT suppress a Bruun lot (§9 item 1).

CLAUDE.md §9 item 1 is explicit:

    Caveat — the bare Krause `Pn*` catalogue number alone is NOT sufficient to
    skip: Krause numbers unique FULL-VALUE show coins (Portugaløser, multi-Ducat
    gold) `Pn` too, and those stay. Rely on the title wording, not the `Pn`
    number.

`PATTERN_RE` nevertheless carried `Pn\\d+` as an alternative until 2026-08-01, so
the parser did exactly what the rule forbids. Five lots were suppressed by that
alternative and by nothing else — every one a full-weight gold coin, 3.39-3.47 g
per stamped ducat against a canonical 3.490, each catalogued in three or more
independent registers:

    Bruun-6083  lot  1062  ½ Portugaloser (5 Ducats) 1653  17.18 g  Fr 98
    Bruun-6084  lot 11215  5 Ducats 1653                   17.30 g  Fr 98
    Bruun-6082  lot 17066  5 Ducat (½ Portugaloser) 1653   17.31 g  Fr 106
    Bruun-6174  lot  1066  ½ Portugaloser (5 Ducats) 1655  17.35 g  Fr 106
    Bruun-7296  lot 13201  10 Ducats 1699                  33.93 g  Fr 213

Their nominal equals their bullion value, so §9.5 does not exclude them either.
They are coins; the curator decides in the normal triage.

Two things this test pins down, because both were got wrong on the way here:

  * the `Pn` alternative stays OUT of the suppression pattern;
  * every OTHER suppression is untouched — those rest on Bruun's own wording
    («off-metal strike», «Piefort», «Guldafslag», and the plain-prose «gold
    planchet» phrasing added the same day). «Pattern» / «Trial» were here too
    until 2026-11-08, when the curator made the wording alone insufficient
    (see test_bruun_pattern_wording).

The measurement that produced the five is worth remembering too: it must run
against the FULL lot body, not the cached `body_excerpt`, which is `body[:600]`.
A first pass keyed on the excerpt reported 25 candidates and a table of 17 that
included ordinary silver Speciedaler — every one of them an artefact of reading
a truncated field.

Run:
    .venv/bin/python -m unittest tests.test_bruun_bare_pn_is_not_a_skip -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots_pn", PROJECT_ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["bruun_parse_lots_pn"] = _mod
_spec.loader.exec_module(_mod)

PATTERN_RE = _mod.PATTERN_RE


class TestBarePnDoesNotSuppress(unittest.TestCase):
    def test_the_five_real_bodies(self):
        # Verbatim openings of the five lots the old alternative suppressed.
        for body in (
            "DENMARK. 1/2 Portugaloser (5 Ducats), 1653. Copenhagen Mint; Privy "
            "Mark: Poker. Frederik III. NGC AU-55. Fr-98; KM-Pn10; Hede-12; "
            "Sieg-113; Schou-4; Aagaard-13.1 (53-1/53.1); Bruun-6083.",
            "DENMARK. 5 Ducats, 1653. Copenhagen Mint. Frederik III. NGC MS-61. "
            "Fr-98; KM-Pn10; Hede-12; Sieg-113; Schou-5; Bruun-6084.",
            "DENMARK. 5 Ducat (1/2 Portugaloser), 1653. Copenhagen Mint. "
            "Frederik III. NGC MS-62. Fr-106; KM-Pn10; Hede-52A; Bruun-6082.",
            "DENMARK. 1/2 Portugaloser (5 Ducats), 1655. Copenhagen Mint. "
            "Frederik III. NGC AU-58. Fr-106; KM- Pn13; Hede-54A; Bruun-6174.",
            "DENMARK. 10 Ducats, 1699. Copenhagen Mint; mm: heart. Frederik IV. "
            "NGC MS-60. Fr-213; KM-Pn39; Hede-36; Sieg-17; Kold-149a; Bruun-7296.",
        ):
            with self.subTest(body=body[:44]):
                self.assertIsNone(PATTERN_RE.search(body))

    def test_bare_pn_alone_never_fires(self):
        for text in ("KM-Pn10;", "KM-Pn39;", "KM- Pn13;", "KM-PnA16;"):
            with self.subTest(text=text):
                self.assertIsNone(PATTERN_RE.search(text))


class TestEveryOtherSuppressionSurvives(unittest.TestCase):
    def test_bruun_own_wording_still_suppresses(self):
        # «Pattern» / «Trial» left PATTERN_RE on 2026-11-08 (curator, e135675):
        # the wording alone no longer excludes a lot, only together with an
        # off-metal or off-nominal sign — pinned in test_bruun_pattern_wording.
        for text, marker in (
            ("DENMARK. Gold Off-Metal Strike 2 Skilling, 1778-CHL.", "off-metal"),
            ("DENMARK. Speciedaler Piefort, 1624.", "Piefort"),
            ("… Guldafslag af 1 Speciedaler …", "Guldafslag"),
            ("… a gold planchet struck to a Double Ducat weight standard …",
             "gold planchet"),
        ):
            with self.subTest(marker=marker):
                self.assertIsNotNone(PATTERN_RE.search(text))

    def test_a_plain_coin_is_not_suppressed(self):
        for text in (
            "DENMARK. Speciedaler, 1663. Copenhagen Mint. KM-248; Dav-3549;",
            "NORWAY. 2 Speciedaler, 1634. Christiania Mint. KM-13; Dav-3532;",
            "DENMARK. 32 Skilling, 1818. Altona Mint. KM-690.1; Hede-29A;",
        ):
            with self.subTest(text=text[:40]):
                self.assertIsNone(PATTERN_RE.search(text))


if __name__ == "__main__":
    unittest.main()
