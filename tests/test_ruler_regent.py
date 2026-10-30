"""Coins struck in Erik VII's name under Margrete I's regency show
«Erik VII (Margrete I)»; the data keeps «Erik VII» (curator 2026-10-30).

    .venv/bin/python -m unittest tests.test_ruler_regent -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import render  # noqa: E402

NB = " "


def coin(first, last, ruler="Erik VII", entity="danish_realm"):
    return {"ruler": ruler, "year_first": first, "year_last": last,
            "issuing_entity": entity, "fuss": "luebischer_muenzfuss"}


class RulerRegent(unittest.TestCase):
    def test_regency_span(self):
        for first, last in ((1396, 1413), (1403, 1413), (1400, 1400)):
            self.assertEqual(render.ruler_regent(coin(first, last), "uk"),
                             f" (Margrete{NB}I)")

    def test_de_period_in_scope(self):
        saved = render._REBUILD_SCOPE
        render._REBUILD_SCOPE = frozenset({"luebischer_muenzfuss"})
        try:
            self.assertEqual(render.ruler_regent(coin(1396, 1413), "de"),
                             f" (Margrete{NB}I.)")
        finally:
            render._REBUILD_SCOPE = saved

    def test_span_past_regency(self):
        for first, last in ((1400, 1424), (1396, 1439), (1422, 1422)):
            self.assertEqual(render.ruler_regent(coin(first, last), "uk"), "")

    def test_other_ruler_or_entity(self):
        self.assertEqual(render.ruler_regent(coin(1400, 1400, ruler="Hans"), "uk"), "")
        self.assertEqual(render.ruler_regent(coin(1400, 1400, entity="sweden"), "uk"), "")
        self.assertEqual(render.ruler_regent(
            coin(1400, 1400, entity=["danish_realm", "royal_holstein"]), "en"),
            f" (Margrete{NB}I)")


if __name__ == "__main__":
    unittest.main()
