"""Unit tests for entity_routing — safe-mode + hint-always semantics."""
from __future__ import annotations
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.entity_routing import (  # noqa: E402
    route_entity_with_rules,
    load_rules,
)


class TestEntityRouting(unittest.TestCase):
    """Fixture set keyed on the schauenburg_niedersaechsisch_denoms rule
    (the first and currently only routing rule). Tests the two-axis
    matrix: rule-match (yes/no) × mint-authoritative (yes/no)."""

    def setUp(self) -> None:
        # Sanity — rules file is loaded + has the expected entry.
        rules = load_rules(force_reload=True)
        self.assertGreaterEqual(len(rules), 1)
        ids = [r["id"] for r in rules]
        self.assertIn("schauenburg_niedersaechsisch_denoms", ids)

    # ── Case 1: rule matches, mint absent → active re-route ─────────
    def test_mariengroschen_no_mint_active_reroute(self):
        coin = {
            "id": "test-1",
            "ruler": "Jobst Hermann",
            "nominal": "2 Mariengroschen",
            "mint": None,
            "mint_verified": False,
            "year_first": 1624,
            "year_last": 1626,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="schauenburg_pinneberg")
        self.assertEqual(ent, "holstein_schauenburg_county")
        self.assertIsNotNone(hint)
        self.assertTrue(hint["active"])
        self.assertEqual(hint["rule_id"], "schauenburg_niedersaechsisch_denoms")
        self.assertEqual(hint["would_route_to"], "holstein_schauenburg_county")
        self.assertIn("ruler_lineage", hint["matched_on"])
        self.assertIn("denomination", hint["matched_on"])

    # ── Case 2: rule matches, mint Oldendorf (NS-side) verified → hint records agreement ──
    def test_mariengroschen_oldendorf_verified_hint_agrees(self):
        coin = {
            "id": "test-2",
            "ruler": "Just Herman von Schaumburg-Pinneberg",
            "nominal": "4 Mariengroschen",
            "mint": "Oldendorf",
            "mint_verified": True,
            "year_first": 1624,
            "year_last": 1624,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="holstein_schauenburg_county")
        # Mint wins (verified); rule writes hint with agrees_with_active=True.
        self.assertEqual(ent, "holstein_schauenburg_county")
        self.assertIsNotNone(hint)
        self.assertFalse(hint["active"])
        self.assertTrue(hint["agrees_with_active"])

    # ── Case 3: rule matches, mint Altona (SH-side) verified → hint records DISAGREEMENT ─
    def test_24_thaler_altona_verified_hint_disagrees(self):
        coin = {
            "id": "test-3",
            "ruler": "Ernst III von Schaumburg-Pinneberg",
            "nominal": "1/24 Thaler",
            "mint": "Altona",
            "mint_verified": True,
            "year_first": 1611,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="schauenburg_pinneberg")
        # Mint wins (verified); rule writes hint with agrees_with_active=False
        # — this is the edge-case-flag for curator review.
        self.assertEqual(ent, "schauenburg_pinneberg")
        self.assertIsNotNone(hint)
        self.assertFalse(hint["active"])
        self.assertFalse(hint["agrees_with_active"])
        self.assertEqual(hint["would_route_to"], "holstein_schauenburg_county")

    # ── Case 4: no rule matches → passes through unchanged, no hint ──
    def test_reichsthaler_altona_vanilla_passthrough(self):
        coin = {
            "id": "test-4",
            "ruler": "Just Herman von Schaumburg-Pinneberg",
            "nominal": "½ Thaler",            # SH denom, no rule match
            "mint": "Altona",
            "mint_verified": True,
            "year_first": 1624,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="schauenburg_pinneberg")
        self.assertEqual(ent, "schauenburg_pinneberg")
        self.assertIsNone(hint)

    # ── Case 5: rule matches but mint is null AND no ruler match → no rule fires ─
    def test_no_ruler_no_rule(self):
        coin = {
            "id": "test-5",
            "ruler": "Christian IV",          # not Schauenburg lineage
            "nominal": "Mariengroschen",      # denom matches but ruler doesn't
            "mint": None,
            "mint_verified": False,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="danish_realm")
        self.assertEqual(ent, "danish_realm")
        self.assertIsNone(hint)

    # ── Case 6: list-form ruler (joint rulers) — substring still matches ─
    def test_joint_ruler_substring(self):
        coin = {
            "id": "test-6",
            "ruler": ["Ernst III", "Matthias"],   # joint
            "nominal": "1/24 Thaler",
            "mint": None,
            "mint_verified": False,
            "year_first": 1612,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="schauenburg_pinneberg")
        self.assertEqual(ent, "holstein_schauenburg_county")
        self.assertTrue(hint["active"])

    # ── Case 7: issuer-only OR match (ruler empty, issuer carries lineage) ──
    def test_issuer_only_lineage_match(self):
        coin = {
            "id": "test-7",
            "ruler": "",                     # empty ruler text
            "nominal": "1 Groschen = 1/24 Thaler",
            "mint": None,
            "mint_verified": False,
            "_numista_issuer": "County of Holstein-Schaumburg-Pinneberg (German States)",
            "year_first": 1620,
        }
        ent, hint = route_entity_with_rules(coin, default_entity="schauenburg_pinneberg")
        self.assertEqual(ent, "holstein_schauenburg_county")
        self.assertTrue(hint["active"])
        # matched on issuer, not ruler
        self.assertIn("issuer", hint["matched_on"])
        self.assertNotIn("ruler_lineage", hint["matched_on"])

    # ── Case 8: issuer matches but denomination doesn't → no rule fire ──
    def test_issuer_match_but_denom_misses(self):
        coin = {
            "id": "test-8",
            "ruler": "",
            "nominal": "1 Reichsthaler",     # not in NS-tradition list
            "mint": None,
            "mint_verified": False,
            "_numista_issuer": "County of Holstein-Schaumburg-Pinneberg (German States)",
        }
        ent, hint = route_entity_with_rules(coin, default_entity="schauenburg_pinneberg")
        self.assertEqual(ent, "schauenburg_pinneberg")
        self.assertIsNone(hint)

    # ── Case 9: empty rules → noop ────────────────────────────────
    def test_empty_default(self):
        coin = {"id": "test-7"}
        ent, hint = route_entity_with_rules(coin, default_entity=None)
        # No matches; returns the default (which is None).
        self.assertIsNone(ent)
        self.assertIsNone(hint)


if __name__ == "__main__":
    unittest.main(verbosity=2)
