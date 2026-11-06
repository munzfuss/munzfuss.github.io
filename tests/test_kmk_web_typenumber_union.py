"""The object page's Typenummer is UNIONed with the ES typeNumber.

The web term was read only when the ES typeNumber was empty, so a newer museum
classification on the object page was lost whenever the ES snapshot carried
anything at all: kmk-417187 ES «4ᵦ men som B. 33» vs web «Galster 85;Schou
28(?)» had no catalogue, kmk-148192 ES «Schou 6» vs web «H 33; Schou 6» no
Hede (78 objects, 2026-11-06). Both sides are kept: a register only the web
gives is added, a disagreement keeps both values, a base number beside its
own sub-letter collapses to the sub-letter.

Run:
    .venv/bin/python -m unittest tests.test_kmk_web_typenumber_union -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_web_union", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bks)


def cat(es, web):
    return bks._catalog({"typeNumber": es, "_raadata_typenumber": web})


class WebTypenumberUnion(unittest.TestCase):
    def test_web_adds_a_register(self):
        self.assertEqual(cat("4ᵦ men som B. 33", "Galster 85;Schou 28(?)"),
                         {"galster": "85", "schou": "28"})

    def test_web_adds_hede_beside_schou(self):
        self.assertEqual(cat("Schou 6", "H 33; Schou 6"), {"schou": "6", "hede": "33"})

    def test_disagreement_keeps_both(self):
        self.assertEqual(cat("H. 131", "Hede 125").get("hede"), ["131", "125"])

    def test_base_beside_its_sub_letter_collapses(self):
        self.assertEqual(cat("H 71A", "Hede 71").get("hede"), "71A")
        self.assertEqual(cat("H 21", "H 21A; Sch 16"), {"hede": "21A", "schou": "16"})

    def test_no_web_term_unchanged(self):
        self.assertEqual(bks._catalog({"typeNumber": "Sch 6"}), {"schou": "6"})


if __name__ == "__main__":
    unittest.main()
