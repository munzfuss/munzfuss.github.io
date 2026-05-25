"""TDD test for §9a multi-specimen merge — fallback-tolerance when
catalog evidence is type-strong.

Function under test:
    scripts/maintenance/merge_seeds_cross_source.py :: match_pair

Real bug case (user audit 2026-05-25):
  «1 Rhinsk Gylden» Christian IV 1625-1632 (KM 108, Hede 29) sat as
  TWO separate final entries on the Denmark page:
  - Bruun-5457 / Bruun-5505 cluster (1625, 1627 specimens, Schou 1, 2)
  - Hede-c4h29 / Bruun-5544 cluster (1625-32, Schou 2, 8)

Both clusters reference SAME KM 108 + Hede 29 + Fr 43 + Sieg 136.1 —
overwhelmingly type-identical. They didn't merge because:
  (1) Each Bruun specimen has its own year_first=year_last (1625 vs
      1628 etc.) — `years` fallback disagrees per-pair.
  (2) Mint orthographic variation «Copenhagen Mint» vs «Kopenhagen» —
      `mint` fallback disagrees per-pair before normalisation.
  (3) Different Schou variants (Schou 1, 2 vs 8) — sub-variant
      disagreement that pre-existing `_catalog_chain_consistent`
      tolerance already handled at primary["catalog"] level, but
      _catalog_strongly_agrees didn't.

§9a explicitly endorses multi-specimen merge of same-type coins with
divergent per-specimen attestations. Match_pair was hard-failing these
on fallback_false despite overwhelming catalog evidence.

Fix: when catalog has TYPE-STRONG agreement (≥2 non-sub-variant agreeing
refs OR ≥1 authoritative type-defining ref) AND ruler + metal primaries
also True, fallback disagreement (years / mint / fineness) is tolerated
and the pair is promoted to confident.

Type-strong is stricter than `chain_state == 'agree'` (which can fire on
a single non-sub-variant ref). It demands either ≥2 type-level refs OR
≥1 authoritative (km/<reg>, hede/<vol>, galster/<vol>, numista).

Run via:
    .venv/bin/python -m unittest tests.test_multispecimen_merge -v
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
match_pair = _merger.match_pair


def coin(**fields):
    """Build a coin dict with sane defaults."""
    base = {
        "metal": "gold",
        "metal_verified": True,
        "kind": "kurant",
    }
    base.update(fields)
    return base


# Real-world KM-108 cluster members (Rhinsk Gylden Christian IV 1625-1632)
BRUUN_5457 = coin(
    id="dk-bruun-5457",
    issuing_entity="danish_realm",
    nominal="Gold Gulden (Rhinsk Gylden)",
    ruler="Christian IV",
    year_first=1625, year_last=1625,
    mint="Copenhagen Mint", mint_verified=True,
    catalog={"bruun_collection_id": "5457", "sieg": "136.1", "schou": "1",
             "friedberg": "43", "km": "108", "hede": "29"},
)
BRUUN_5544 = coin(
    id="dk-bruun-5544",
    issuing_entity="danish_realm",
    nominal="1 Goldgulden (Rhinsk Gulden)",
    ruler="Christian IV",
    year_first=1628, year_last=1628,
    mint="Kopenhagen", mint_verified=True,
    catalog={"bruun_collection_id": "5544", "sieg": "136.1", "schou": "8",
             "friedberg": "43", "km": "108", "hede": "29"},
)
HEDE_C4H29 = coin(
    id="dk-hede-c4h29",
    issuing_entity="danish_realm",
    nominal="1 Rhinsk Gylden",
    ruler="Christian IV.",
    year_first=1625, year_last=1632,
    mint="Kopenhagen",
    catalog={"hede": "29", "hede_volume": "c4h", "schou": "2", "sieg": "142"},
)


class TestRhinskGyldenKM108Cluster(unittest.TestCase):
    """The real-world cluster from user audit. All four Bruun+Hede
    pairs must merge confidently."""

    def test_bruun_5457_bruun_5544_confident(self):
        """Same Bruun source, different years, same catalog: must merge
        per §9a multi-specimen."""
        r = match_pair(BRUUN_5457, BRUUN_5544, entity_id="danish_realm")
        self.assertEqual(r["decision"], "confident",
                         f"Got {r['decision']}; primary={r['primary']}, "
                         f"fallback={r['fallback']}, why={r['why']}")

    def test_bruun_5457_hede_c4h29_confident(self):
        """Cross-source (Bruun + Hede), different mint orthography:
        Copenhagen Mint vs Kopenhagen — should still merge."""
        r = match_pair(BRUUN_5457, HEDE_C4H29, entity_id="danish_realm")
        self.assertEqual(r["decision"], "confident",
                         f"Got {r['decision']}; primary={r['primary']}, "
                         f"why={r['why']}")

    def test_bruun_5544_hede_c4h29_confident(self):
        """Cross-source, year_first 1628 (Bruun specimen) vs 1625
        (Hede multi-year)."""
        r = match_pair(BRUUN_5544, HEDE_C4H29, entity_id="danish_realm")
        self.assertEqual(r["decision"], "confident")


class TestMintOrthographyTolerance(unittest.TestCase):
    """«Copenhagen Mint» (Bruun PDF) ↔ «Kopenhagen» (project canonical)
    must normalise to overlap. Suffix « Mint» strip + spelling alias."""

    def test_copenhagen_mint_normalises_to_kopenhagen(self):
        """Catalog matches; mint differs orthographically — must still
        merge once mint normalisation kicks in."""
        a = coin(
            nominal="Speciedaler", ruler="Christian IV",
            year_first=1672, year_last=1672,
            mint="Copenhagen Mint", mint_verified=True,
            catalog={"km": "108", "hede": "29", "sieg": "136.1"},
        )
        b = coin(
            nominal="1 Speciedaler", ruler="Christian IV",
            year_first=1672, year_last=1672,
            mint="Kopenhagen",
            catalog={"km": "108", "hede": "29", "sieg": "136.1"},
        )
        r = match_pair(a, b, entity_id="danish_realm")
        # Mint should overlap (Copenhagen Mint → kopenhagen)
        self.assertIs(r["fallback"]["mint"], True,
                      f"Expected mint True after «Copenhagen Mint» strip; "
                      f"got {r['fallback']}")
        self.assertEqual(r["decision"], "confident")


class TestSafetyGuards(unittest.TestCase):
    """§9a multi-specimen promotion must NOT fire when type-strong gate
    fails (single sub-variant only, or non-sub-variant disagreement)."""

    def test_single_subvariant_ref_only_not_promoted(self):
        """Only Schou agrees, no type-level refs shared → no_match (was
        the pre-fix behaviour for sub-variant only)."""
        a = coin(
            nominal="X", ruler="Christian IV",
            year_first=1625, year_last=1625,
            mint="Kopenhagen",
            catalog={"schou": "2"},
        )
        b = coin(
            nominal="X", ruler="Christian IV",
            year_first=1628, year_last=1628,
            mint="Kopenhagen",
            catalog={"schou": "2"},
        )
        r = match_pair(a, b, entity_id="danish_realm")
        # Only sub-variant agrees; no type-level evidence → not promoted
        self.assertNotEqual(r["decision"], "confident",
                            f"Got {r['decision']} — sub-variant only must "
                            f"NOT auto-promote per type-strong gate")

    def test_non_subvariant_disagreement_disqualifies(self):
        """Lange agrees but Friedberg disagrees → non-sub-variant
        disagreement disqualifies type-strong gate."""
        a = coin(
            ruler="Christian IV",
            year_first=1625, year_last=1625,
            mint="Kopenhagen",
            catalog={"lange": "100", "fr": "43"},
        )
        b = coin(
            ruler="Christian IV",
            year_first=1628, year_last=1628,
            mint="Kopenhagen",
            catalog={"lange": "100", "fr": "44"},  # different Friedberg!
        )
        r = match_pair(a, b, entity_id="danish_realm")
        # Catalog chain still might say «agree» via tolerance, but §9a
        # type-strong gate disqualifies on non-sub-variant disagreement.
        # Pair should NOT auto-promote despite fallback disagreement.
        if r["fallback"].get("years") is False:
            self.assertNotEqual(r["decision"], "confident",
                                f"Got {r['decision']}; non-sub-variant disagreement "
                                f"must disqualify §9a promotion")

    def test_ruler_disagreement_blocks_promotion(self):
        """Even with type-strong catalog, ruler disagreement must block
        §9a multi-specimen promotion (it's not a multi-specimen case if
        rulers differ — it's an attribution error or catalog reuse)."""
        a = coin(
            ruler="Christian IV", ruler_verified=True,
            year_first=1625, year_last=1625,
            catalog={"km": "108", "hede": "29"},
        )
        b = coin(
            ruler="Frederik III", ruler_verified=True,
            year_first=1648, year_last=1648,
            catalog={"km": "108", "hede": "29"},
        )
        r = match_pair(a, b, entity_id="danish_realm")
        # Ruler primary False → blocks (returns no_match on primary_false)
        self.assertEqual(r["decision"], "no_match")


class TestKMOnlyNoPromotion(unittest.TestCase):
    """Even with KM agreement, a SINGLE shared ref + fallback disagreement
    requires care. Cross-country KM clash is the main risk — the gate
    only allows authoritative scope-prefixed keys (km/dk, km/sh, etc.)."""

    def test_km_scoped_single_ref_promotes_with_ruler_metal(self):
        """km/dk + ruler + metal True, year disagrees → promote via §9a."""
        a = coin(
            ruler="Christian IV", year_first=1625, year_last=1625,
            catalog={"km": "108"},
        )
        b = coin(
            ruler="Christian IV", year_first=1632, year_last=1632,
            catalog={"km": "108"},
        )
        r = match_pair(a, b, entity_id="danish_realm")
        self.assertEqual(r["decision"], "confident",
                         f"Got {r['decision']}; km/dk + ruler + metal True "
                         f"should §9a-promote despite year disagreement")


if __name__ == "__main__":
    unittest.main(verbosity=2)
