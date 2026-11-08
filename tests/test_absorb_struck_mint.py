"""A mint a live member marks «erroneous» leaves the final.

The seed's `mint_mark` (kind erroneous) clears the seed's own mint and shows
the printed value in `mint_alts`, but the final's stored copy is its own
first member in the self-union, so the struck value came back on every run
(Hede 13, ucoin 70717 «Copenhagen (FF)», 2026-11-08). The final now drops a
struck mint that no live member attests, and — when that leaves every live
member on one scalar issuing_entity inside the stored joint — follows it.
"""
from __future__ import annotations

import contextlib
import copy
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

with contextlib.redirect_stdout(io.StringIO()):
    from maintenance import absorb_seeds_into_final_v2 as ab  # noqa: E402

STRUCK = {"value": "Kopenhagen", "source": "ucoin", "kind": "erroneous",
          "reason": {"en": "Wrong mint."}}

FINAL = {"id": "c-f", "label": "unified-s1", "composed_of": ["c-cls"],
         "fuss": "18_5_thaler", "phase": "II", "kind": "scheide",
         "nominal": "1/5 Rigsbankskilling", "ruler": "Christian VIII",
         "issuing_entity": ["danish_realm", "royal_holstein"],
         "mint": ["Altona", "Kopenhagen"], "mint_verified": True,
         "sources": [{"url": "https://en.ucoin.net/x?tid=70717", "ref": "ucoin",
                      "type": "ucoin"}]}

CLS = {"id": "c-cls", "label": "unified-s1", "composed_of": ["s1", "s2"],
       "nominal": "1/5 Rigsbankskilling", "ruler": "Christian VIII",
       "issuing_entity": "royal_holstein", "mint": "Altona",
       "mint_verified": True, "mint_alts": [STRUCK],
       "sources": [{"url": "https://en.ucoin.net/x?tid=70717", "ref": "ucoin",
                    "type": "ucoin"}]}


def _run(final, cls):
    with contextlib.redirect_stdout(io.StringIO()):
        out, _ = ab._enrich_final_entry(copy.deepcopy(final),
                                        [copy.deepcopy(final), copy.deepcopy(cls)],
                                        "royal_holstein")
    return out


class StruckMint(unittest.TestCase):
    def test_struck_mint_leaves_final(self):
        out = _run(FINAL, CLS)
        self.assertEqual(out["mint"], "Altona")
        self.assertEqual(out["issuing_entity"], "royal_holstein")
        self.assertEqual([a["value"] for a in out["mint_alts"]], ["Kopenhagen"])

    def test_struck_mint_another_member_attests_stays(self):
        cls = dict(CLS, mint=["Altona", "Kopenhagen"],
                   issuing_entity=["danish_realm", "royal_holstein"])
        out = _run(FINAL, cls)
        self.assertEqual(sorted(out["mint"]), ["Altona", "Kopenhagen"])
        self.assertEqual(out["issuing_entity"], ["danish_realm", "royal_holstein"])

    def test_suspect_mark_changes_nothing(self):
        cls = dict(CLS, mint_alts=[dict(STRUCK, kind="suspect")])
        out = _run(FINAL, cls)
        self.assertEqual(sorted(out["mint"]), ["Altona", "Kopenhagen"])

    def test_issuing_hold_opts_out(self):
        final = dict(FINAL, _curation_holds={"issuing_entity": "joint by decision"})
        out = _run(final, CLS)
        self.assertEqual(out["mint"], "Altona")
        self.assertEqual(out["issuing_entity"], ["danish_realm", "royal_holstein"])


ALT = {"kind": "hedged", "how": "alternatives", "source": "hede",
       "as_printed": "København eller Christiania"}


class HedgedAlternativeMint(unittest.TestCase):
    """«København eller Christiania»: the alternative the verified members do
    not give leaves the final (Frederik III Hede 39, 2026-11-08)."""

    def _final(self):
        return dict(FINAL, mint=["Christiania", "Kopenhagen"],
                    issuing_entity="danish_norway")

    def test_alternative_leaves_final(self):
        cls = dict(CLS, mint="Christiania", issuing_entity="danish_norway",
                   mint_alts=None, uncertainty={"mint": [ALT]})
        out = _run(self._final(), cls)
        self.assertEqual(out["mint"], "Christiania")

    def test_no_verified_member_keeps_both(self):
        cls = dict(CLS, mint=["Christiania", "Kopenhagen"], mint_verified=False,
                   issuing_entity="danish_norway", mint_alts=None,
                   uncertainty={"mint": [ALT]})
        out = _run(self._final(), cls)
        self.assertEqual(sorted(out["mint"]), ["Christiania", "Kopenhagen"])

    def test_render_lists_the_alternative(self):
        from lib.render import mint_hedged_alts
        self.assertEqual(mint_hedged_alts({"mint": "Christiania",
                                           "uncertainty": {"mint": [ALT]}}),
                         ["Kopenhagen"])


if __name__ == "__main__":
    unittest.main()
