"""TDD test for `_catalog_refs` synonym normalisation.

Function under test:
    scripts/maintenance/merge_seeds_cross_source.py :: _catalog_refs(coin)

Different parsers emit different short tokens for the same catalogue:

  - Numista API: `cat.fr` (Friedberg «Gold Coins of the World»)
  - Bruun PDF parser: `cat.friedberg` (same Friedberg)
  - Numista API: `cat.dav` (Davenport «European Crowns Since 1484»)
  - Some sources: `cat.davenport` (same Davenport)

Pre-fix `_catalog_refs` carried both keys verbatim in its output dict, so
`_catalog_chain_consistent` saw {fr:3} vs {friedberg:3} as having zero
shared keys → primary["catalog"] = None → matching downgraded to fallback
signals → merge typically failed.

The fix introduces a CATALOG_KEY_SYNONYMS map: {friedberg → fr,
davenport → dav}. Both shapes now end up under the canonical key.

Run via:
    .venv/bin/python -m unittest tests.test_catalog_refs_normalisation -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"),
)
_merger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_merger)
_catalog_refs = _merger._catalog_refs


def coin(catalog):
    """Build a minimal coin dict with given catalog dict."""
    return {"catalog": catalog}


class TestFriedbergSynonym(unittest.TestCase):
    """`friedberg` (Bruun parser) ↔ `fr` (Numista API) canonicalised to `fr`."""

    def test_friedberg_only_maps_to_fr(self):
        """Bruun-side: only `friedberg` in catalog → output key is `fr`."""
        refs = _catalog_refs(coin({"friedberg": "3"}), entity_id="danish_realm")
        self.assertEqual(refs.get("fr"), "3")
        self.assertNotIn("friedberg", refs)

    def test_fr_only_unchanged(self):
        """Numista-side: only `fr` → output key is `fr` (unchanged)."""
        refs = _catalog_refs(coin({"fr": "3"}), entity_id="danish_realm")
        self.assertEqual(refs.get("fr"), "3")

    def test_bruun_friedberg_3_matches_numista_fr_3(self):
        """Cross-source: both surfaces of Fr-3 collapse to same canonical key
        with same value — overlap exists for `_catalog_chain_consistent`."""
        bruun = _catalog_refs(coin({"friedberg": "3", "bruun_collection_id": "3831"}),
                               entity_id="danish_realm")
        numista = _catalog_refs(coin({"fr": "3", "numista": "420401"}),
                                 entity_id="danish_realm")
        # The fr keys must match
        self.assertEqual(bruun["fr"], numista["fr"])
        # And they intersect on `fr`
        shared = set(bruun) & set(numista)
        self.assertIn("fr", shared)

    def test_fr_4_friedberg_4_real_hans_goldgulden(self):
        """Hans Goldgulden type — Numista 355730 (fr:4) vs Bruun-3840 (friedberg:4).
        Same Friedberg-4 → must collapse."""
        numista = _catalog_refs(coin({"fr": "4", "numista": "355730"}),
                                 entity_id="danish_realm")
        bruun = _catalog_refs(coin({"friedberg": "4", "bruun_collection_id": "3840"}),
                               entity_id="danish_realm")
        self.assertEqual(bruun["fr"], "4")
        self.assertEqual(numista["fr"], "4")


class TestDavenportSynonym(unittest.TestCase):
    """`davenport` ↔ `dav` canonicalised to `dav`. Symmetric to friedberg/fr."""

    def test_davenport_maps_to_dav(self):
        refs = _catalog_refs(coin({"davenport": "3512"}), entity_id="danish_realm")
        self.assertEqual(refs.get("dav"), "3512")
        self.assertNotIn("davenport", refs)

    def test_dav_unchanged(self):
        refs = _catalog_refs(coin({"dav": "3512"}), entity_id="danish_realm")
        self.assertEqual(refs.get("dav"), "3512")


class TestSynonymCoexistence(unittest.TestCase):
    """When a coin happens to carry BOTH synonyms (rare — curator edit, manual
    merge), values are unioned rather than one overwriting the other."""

    def test_fr_and_friedberg_same_value(self):
        """{fr:3, friedberg:3} → {fr:3} (idempotent)."""
        refs = _catalog_refs(coin({"fr": "3", "friedberg": "3"}),
                              entity_id="danish_realm")
        self.assertEqual(refs.get("fr"), "3")

    def test_fr_and_friedberg_different_values_unioned(self):
        """{fr:3, friedberg:5} → {fr:'3|5'} (union, sorted)."""
        refs = _catalog_refs(coin({"fr": "3", "friedberg": "5"}),
                              entity_id="danish_realm")
        # Order-independent: both refs must appear in output
        parts = set(refs["fr"].split("|"))
        self.assertEqual(parts, {"3", "5"})


class TestPreservedFields(unittest.TestCase):
    """Non-synonym fields stay verbatim (regression guards)."""

    def test_sieg_unchanged(self):
        refs = _catalog_refs(coin({"sieg": "12"}), entity_id="danish_realm")
        self.assertEqual(refs.get("sieg"), "12")

    def test_schou_unchanged(self):
        refs = _catalog_refs(coin({"schou": "2"}), entity_id="danish_realm")
        self.assertEqual(refs.get("schou"), "2")

    def test_numista_unchanged(self):
        refs = _catalog_refs(coin({"numista": "420401"}), entity_id="danish_realm")
        self.assertEqual(refs.get("numista"), "420401")

    def test_bruun_collection_id_unchanged(self):
        refs = _catalog_refs(coin({"bruun_collection_id": "3831"}),
                              entity_id="danish_realm")
        self.assertEqual(refs.get("bruun_collection_id"), "3831")

    def test_jensen_skjoldager_and_split(self):
        # «/» reads as «and»: «T-91/96» = «T-91» + «T-96» (shared prefix re-
        # attached to the bare «96»). See tests/test_catalog_slash_split.py.
        refs = _catalog_refs(coin({"jensen_skjoldager": "T-91/96"}),
                              entity_id="danish_realm")
        self.assertEqual(refs.get("jensen_skjoldager"), "T-91|T-96")

    def test_list_value_joined_and_sorted(self):
        """List-valued catalog refs join on `|`, sorted."""
        refs = _catalog_refs(coin({"sieg": ["12", "12A", "12B"]}),
                              entity_id="danish_realm")
        self.assertEqual(refs.get("sieg"), "12|12A|12B")


class TestE2EBruunNobelMergeFinallyWorks(unittest.TestCase):
    """End-to-end smoke test: Bruun-3831 (Hans Nobel) and Numista-420401
    (Hans Nobel) refs must overlap on `fr`. Combined with the parser fix
    (year 1496 vs 1791), this should let match_pair declare confident merge."""

    def test_bruun_3831_numista_420401_share_fr_3(self):
        bruun = _catalog_refs(coin({
            "bruun_collection_id": "3831", "sieg": "12", "schou": "2",
            "friedberg": "3", "galster": "24",
        }), entity_id="danish_realm")
        numista = _catalog_refs(coin({
            "fr": "3", "numista": "420401",
        }), entity_id="danish_realm")
        shared_keys = set(bruun) & set(numista)
        self.assertIn("fr", shared_keys, "fr↔friedberg synonym must unify the keys")
        self.assertEqual(bruun["fr"], numista["fr"], "Both must carry Fr-3")


if __name__ == "__main__":
    unittest.main(verbosity=2)
