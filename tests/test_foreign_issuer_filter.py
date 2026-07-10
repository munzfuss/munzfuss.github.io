"""Unit test for the Pass-1 foreign-issuer intersection filter in
`_assemble_v2_location` (scripts/build.py).

A coin filed in an entity file it doesn't belong to — the Romanian 20-Lei
struck on contract (Auftragsprägung) in Hamburg, `issuing_entity: romania`,
sitting in `hanseatic_hamburg.yml` by mint — must NOT render on a page that
consumes `hanseatic_hamburg`. Pass 1 applies the same
`issuing_entity ∩ consumes_set` rule that Pass 2 + the seed pass already
enforce, using the RAW issuing_entity (a joint coin sharing ONE consumed
entity is still kept).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build  # noqa: E402


_PHASES = {"seed_unsorted": [{"id": "ikmk", "year_from": 1559, "year_to": 1914}]}


def _coin(cid, ie, nominal="10 Mark"):
    return {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "ikmk",
        "kind": "kurant",
        "nominal": nominal,
        "metal": "gold",
        "issuing_entity": ie,
        "year_first": 1883,
        "year_last": 1883,
        "year_label": "1883",
    }


class TestForeignIssuerFilter(unittest.TestCase):
    def setUp(self):
        self._by_entity = {
            "hanseatic_hamburg": [
                _coin("norm-hh", "hanseatic_hamburg"),
                _coin("foreign-ro", "romania", nominal="20 Lei"),
            ],
        }
        # Monkeypatch the three disk loaders + the timeline-span expander so the
        # test exercises only the assembly/filter logic against the fixture.
        self._saved = {
            "_load_v2_curated": build._load_v2_curated,
            "_load_v2_seed_entries": build._load_v2_seed_entries,
            "_compute_absorbed_seed_ids": build._compute_absorbed_seed_ids,
            "_expand_outer_phase_span": build._expand_outer_phase_span,
        }
        build._load_v2_curated = lambda: self._by_entity
        build._load_v2_seed_entries = lambda: []
        build._compute_absorbed_seed_ids = lambda: set()
        build._expand_outer_phase_span = lambda *a, **k: None

    def tearDown(self):
        for name, fn in self._saved.items():
            setattr(build, name, fn)

    def test_foreign_issuer_dropped_own_coin_kept(self):
        """The Romanian coin (issuing_entity ∉ consumes) is dropped; the
        Hamburg coin (issuing_entity ∈ consumes) is kept."""
        raw = {"consumes_entities": ["hanseatic_hamburg"], "phases": _PHASES}
        n = build._assemble_v2_location("german_empire", raw)
        ids = {c["id"] for c in raw["coins"]}
        self.assertIn("norm-hh", ids)
        self.assertNotIn("foreign-ro", ids)
        self.assertEqual(n, 1)

    def test_joint_coin_kept_when_one_entity_consumed(self):
        """A joint coin whose list contains at least one consumed entity is
        kept — the filter requires intersection, not subset."""
        self._by_entity["hanseatic_hamburg"].append(
            _coin("joint-hh-ro", ["hanseatic_hamburg", "romania"])
        )
        raw = {"consumes_entities": ["hanseatic_hamburg"], "phases": _PHASES}
        build._assemble_v2_location("german_empire", raw)
        ids = {c["id"] for c in raw["coins"]}
        self.assertIn("joint-hh-ro", ids)

    def test_no_issuing_entity_kept(self):
        """A coin with no issuing_entity cannot be decided against, so it is
        kept (current behaviour — filter guards on a non-empty raw set)."""
        self._by_entity["hanseatic_hamburg"].append(_coin("no-ie", None))
        raw = {"consumes_entities": ["hanseatic_hamburg"], "phases": _PHASES}
        build._assemble_v2_location("german_empire", raw)
        ids = {c["id"] for c in raw["coins"]}
        self.assertIn("no-ie", ids)


if __name__ == "__main__":
    unittest.main()
