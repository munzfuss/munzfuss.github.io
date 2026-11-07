"""A final whose every source is a scope-dropped KMM record leaves with them.

Caught 2026-11-06: after the KMM stub rule (curator 2026-11-05) took 10 440
seeds out of the corpus, 356 finals that existed only through those records
stayed in final — e.g. KMM 150153 / 150155 / 673522 under 8_daler_fod phase 0 —
because the vanished-backing drop spares any final with a real Fuß. Rule: no
live seed reaches it AND every source is a KMM object listed in
`data/v2/_scope_dropped/` → dropped, curated or not. Any other source keeps it.
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

KMM = "https://samlinger.natmus.dk/KMM/object/{}"


def _fe(fid, *urls, fuss="8_daler_fod"):
    return {"id": fid, "fuss": fuss, "phase": "0", "composed_of": [fid],
            "sources": [{"type": "museum", "url": u} for u in urls]}


class ScopeDroppedFinal(unittest.TestCase):
    def setUp(self):
        self._saved = AB._SCOPE_DROPPED_IDS
        AB._SCOPE_DROPPED_IDS = {"kmk-150153", "kmk-150155"}

    def tearDown(self):
        AB._SCOPE_DROPPED_IDS = self._saved

    def test_all_sources_dropped_kmm_is_dropped_even_classified(self):
        fe = _fe("c-x1", KMM.format(150153), KMM.format(150155))
        self.assertTrue(AB._is_scope_dropped_final(fe, set(), set()))

    def test_a_live_kmm_source_keeps_it(self):
        fe = _fe("c-x2", KMM.format(150153), KMM.format(999999))
        self.assertFalse(AB._is_scope_dropped_final(fe, set(), set()))

    def test_a_non_kmm_source_keeps_it(self):
        fe = _fe("c-x3", KMM.format(150153), "https://www.danskmoent.dk/chr/c3h1.htm")
        self.assertFalse(AB._is_scope_dropped_final(fe, set(), set()))

    def test_live_backing_keeps_it(self):
        fe = _fe("c-x4", KMM.format(150153))
        self.assertFalse(AB._is_scope_dropped_final(fe, {"c-x4"}, {"c-x4"}))

    def test_label_only_kmm_citation_counts(self):
        fe = {"id": "c-x6", "fuss": "kronefod", "composed_of": ["c-x6"],
              "sources": [{"type": "museum", "ref": "KMM 150153 (Inv. FP 2711.20)"}]}
        self.assertTrue(AB._is_scope_dropped_final(fe, set(), set()))
        fe["sources"][0]["ref"] = "KMM 999999 (Inv. FP 2711.20)"
        self.assertFalse(AB._is_scope_dropped_final(fe, set(), set()))

    def test_no_sources_is_not_this_rule(self):
        self.assertFalse(AB._is_scope_dropped_final(_fe("c-x5"), set(), set()))


if __name__ == "__main__":
    unittest.main()
