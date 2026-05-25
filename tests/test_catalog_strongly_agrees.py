"""TDD test for `_catalog_strongly_agrees` — weight-tier-1 gate logic.

Function under test:
    scripts/maintenance/merge_seeds_cross_source.py :: _catalog_strongly_agrees

Background
----------
The weight tier-1 disambiguator blocks merges when weight Δ > 5% UNLESS
catalog evidence «strongly agrees». Pre-2026-05-25 the «strongly agrees»
rule required ≥2 shared+agreeing catalog refs.

Real failure case (user audit 2026-05-25): «1 Rhinsk gylden 1536
Christian III» appeared as two separate entries on the Denmark page:
  - Bruun-14770 (3.37g): catalog {bruun_collection_id:14770, sieg:23,
    schou:4, friedberg:18, lange:18, galster:131}
  - Galster-c3g-131 (3.19g): catalog {galster:131, galster_volume:c3g}
Both reference the SAME Galster-131 type. Weight Δ = 5.6% (>5% threshold);
shared refs after `_catalog_refs` canonicalisation = {galster/c3g:131} = 1
ref → tier-1 disambiguator fired → no_match.

Fix: relax `_catalog_strongly_agrees` to accept a single shared+agreeing
ref when that ref is from an AUTHORITATIVE TYPE-DEFINING catalog —
catalogs that publish one number per coin type within their scope:
  - km (Krause-Mishler, scoped per region — see merger D27)
  - numista (N# is type-unique)
  - bruun_collection_id (specimen-equivalent for sales lot)
  - galster/<vol> (Danish per-ruler-volume — one num per type)
  - hede/<vol> (Danish per-ruler-volume — one num per type)

Sub-variant refs (sieg, schou, lange) often distinguish DIE variants
WITHIN a type — they don't qualify as type-defining standalone.

Run via:
    .venv/bin/python -m unittest tests.test_catalog_strongly_agrees -v
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
_catalog_strongly_agrees = _merger._catalog_strongly_agrees


class TestSingleAuthoritativeRefPath(unittest.TestCase):
    """A single shared+agreeing ref from a type-defining catalog
    qualifies as strong agreement (single-source carry path)."""

    def test_galster_volume_single_ref(self):
        """Galster-c3g-131 ↔ Bruun-Galster-131 — real Rhinsk Gylden case."""
        a = {"galster/c3g": "131"}
        b = {"bruun_collection_id": "14770", "sieg": "23", "schou": "4",
             "lange": "18", "fr": "18", "galster/c3g": "131"}
        self.assertTrue(_catalog_strongly_agrees(a, b))

    def test_km_single_ref(self):
        """KM single shared ref is type-defining (one num per region)."""
        a = {"km": "55"}
        b = {"km": "55", "sieg": "152", "schou": "52"}
        self.assertTrue(_catalog_strongly_agrees(a, b))

    def test_numista_single_ref(self):
        """Numista N# — one per type, single ref is enough."""
        a = {"numista": "420401"}
        b = {"numista": "420401", "fr": "3"}
        self.assertTrue(_catalog_strongly_agrees(a, b))

    def test_hede_volume_single_ref(self):
        a = {"hede/c4h": "120"}
        b = {"hede/c4h": "120", "schou": "1"}
        self.assertTrue(_catalog_strongly_agrees(a, b))

    def test_bruun_collection_id_single_ref(self):
        """bruun_collection_id is a stable type pointer once parser captures it."""
        a = {"bruun_collection_id": "3831"}
        b = {"bruun_collection_id": "3831", "galster/c4g": "24"}
        self.assertTrue(_catalog_strongly_agrees(a, b))


class TestSubVariantRefsAlone(unittest.TestCase):
    """Sub-variant refs (Sieg, Schou, Lange) alone are NOT enough — they
    distinguish die-variants within a type and one match isn't type-evidence."""

    def test_sieg_alone_not_enough(self):
        a = {"sieg": "12"}
        b = {"sieg": "12", "galster/c4g": "999"}  # different galster vol-num pair
        # Only sieg agrees; sub-variant ref alone falls back to min_shared count
        self.assertFalse(_catalog_strongly_agrees(a, b))

    def test_schou_alone_not_enough(self):
        a = {"schou": "5"}
        b = {"schou": "5"}
        # Even mutual agreement on schou alone — only 1 shared ref AND no
        # type-defining catalog → not strongly-agreeing
        self.assertFalse(_catalog_strongly_agrees(a, b))

    def test_lange_alone_not_enough(self):
        a = {"lange": "100"}
        b = {"lange": "100"}
        self.assertFalse(_catalog_strongly_agrees(a, b))


class TestMultipleRefsClassicPath(unittest.TestCase):
    """Original ≥2-shared rule still works — multi-catalog cross-source overlap."""

    def test_two_subvariant_refs(self):
        """Two sub-variant refs agreeing → strongly-agrees via classic path."""
        a = {"sieg": "12", "schou": "2"}
        b = {"sieg": "12", "schou": "2"}
        self.assertTrue(_catalog_strongly_agrees(a, b))

    def test_three_refs_agree(self):
        a = {"sieg": "12", "schou": "2", "lange": "100"}
        b = {"sieg": "12", "schou": "2", "lange": "100"}
        self.assertTrue(_catalog_strongly_agrees(a, b))


class TestDisagreementDisqualifies(unittest.TestCase):
    """Any disagreement on a shared key voids strong agreement, even if
    authoritative ref agrees."""

    def test_sieg_disagrees_galster_agrees_still_fails(self):
        """92B Galster (sieg=4) vs 92B Bruun (sieg=16) — same galster #,
        but sieg disagrees → not strong (per the «zero disagreements» rule)."""
        a = {"galster/c4g": "92B", "sieg": "4"}
        b = {"galster/c4g": "92B", "sieg": "16"}
        self.assertFalse(_catalog_strongly_agrees(a, b))

    def test_km_disagrees(self):
        a = {"km": "55"}
        b = {"km": "56"}
        # Same key, different values → disagree → False
        self.assertFalse(_catalog_strongly_agrees(a, b))

    def test_no_shared_keys(self):
        a = {"km": "55"}
        b = {"galster/c4g": "131"}
        self.assertFalse(_catalog_strongly_agrees(a, b))


class TestE2ERhinskGyldenMerge(unittest.TestCase):
    """End-to-end: the real Rhinsk Gylden 1536 case must merge."""

    def test_bruun_galster_rhinsk_gylden_strongly_agrees(self):
        bruun = {"bruun_collection_id": "14770", "sieg": "23", "schou": "4",
                 "lange": "18", "fr": "18", "galster/c3g": "131"}
        galster = {"galster/c3g": "131"}
        self.assertTrue(_catalog_strongly_agrees(bruun, galster))


if __name__ == "__main__":
    unittest.main(verbosity=2)
