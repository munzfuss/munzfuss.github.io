"""A curator's ruler correction reaches a coin that already has its final.

2026-10-18: KMM writes «Frederik 3» on coins of Frederik I, Frederik II, the
Gottorp duke Frederik III and the future king Frederik III as archbishop of
Bremen. The correction is a `_source_errata` on the KMM seed, carried up by the
merger as the class's `_errata_applied`. `ruler` is foundation-immutable in
absorb, so a coin that kept its final kept the old ruler. The curator decided
(2026-10-18) that his correction outranks the frozen value; a `_curation_holds`
on ruler still wins.
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
    "absorb_seeds_into_final_v2",
    ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
AB = importlib.util.module_from_spec(_spec)
sys.modules["absorb_seeds_into_final_v2"] = AB
_spec.loader.exec_module(AB)


def enrich(holds=None, corrections=("Frederik I.",)):
    final = {"id": "unified-kmk-747724", "ruler": "Frederik III.", "nominal": "1 Søsling",
             "issuing_entity": "danish_realm", "composed_of": ["unified-kmk-747724"]}
    if holds:
        final["_curation_holds"] = holds
    member = {"id": "unified-kmk-747724", "ruler": "Frederik I.", "nominal": "1 Søsling",
              "issuing_entity": "danish_realm",
              "_errata_applied": [{"source": "kmk-747724", "field": "ruler",
                                   "printed": "Frederik 3", "correct": c} for c in corrections]}
    out, _ = AB._enrich_final_entry(final, [final, member], "danish_realm")
    return out


class TestRulerErrataWins(unittest.TestCase):
    def test_correction_replaces_frozen_ruler(self):
        self.assertEqual(enrich()["ruler"], "Frederik I.")

    def test_ruler_hold_wins(self):
        self.assertEqual(enrich(holds={"ruler": "kept"})["ruler"], "Frederik III.")

    def test_two_corrections_leave_it(self):
        self.assertEqual(enrich(corrections=("Frederik I.", "Frederik II."))["ruler"], "Frederik III.")


class TestPromotedKeepsMark(unittest.TestCase):
    """A class promoted to a new final (bulk-promote, or a relocation into
    another entity) is enriched with itself as the only member; its KMM
    «(!)» ruler alt must survive."""

    def test_single_member_alt_kept(self):
        alt = {"value": "Frederik 3", "source": "kmk", "kind": "erroneous",
               "reason": {"de": "x", "en": "x", "uk": "x", "da": "x"}}
        stub = {"id": "unified-kmk-149360", "ruler": "Erzbischof Friedrich",
                "nominal": "1/16 Thaler", "issuing_entity": "erzbisthum_bremen_verden",
                "composed_of": ["unified-kmk-149360"], "ruler_alts": [alt]}
        out, _ = AB._enrich_final_entry(stub, [stub], "erzbisthum_bremen_verden")
        self.assertEqual([a["value"] for a in out.get("ruler_alts") or []], ["Frederik 3"])


if __name__ == "__main__":
    unittest.main()
