"""A curator's `_curation_holds` died whenever a re-seed moved the coin to a
different issuing entity — including a hold placed on `issuing_entity` itself,
the very field that decides the move.

Found 2026-09-12 while re-running all nine seed builders: project-wide holds
went 55 -> 49. Six coins lost theirs, five of them Husum / Lybæk / Witten
attribution calls a curator had written out at length. Three were reverted to
the exact stale entity the hold existed to argue against.

It did not announce itself because `issuing_entity` IS in
`seed_merge.CURATED_FIELDS`, so the protection looked present. It was
unreachable: `write_v2_seed` groups fresh coins into per-entity files BEFORE
`merge_seed` runs, so a fresh entry carrying a different entity lands in a
file where no existing entry shares its id -> `added_new`, `merge_one` never
runs, and the cross-entity purge then drops the curated entry from its old
file. Nothing errored; the counts just quietly fell.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.v2_seed_writer import _existing_curated_entries  # noqa: E402

SEED = """\
source: test
scope_note: fixture
coins:
  - id: t-1
    nominal: 1 Mark
    mint: Husum
    issuing_entity: royal_slesvig
    mint_verified: false
    _curation_holds:
      issuing_entity: Husum is a royal-Schleswig mint; the royal_holstein tag is stale.
  - id: t-2
    nominal: 4 Pfennig
    mint:
    issuing_entity: royal_slesvig
    mint_verified: false
    _curation_holds:
      mint: "Witten is the DENOMINATION, not a mint."
  - id: t-3
    nominal: 2 Skilling
    issuing_entity: royal_slesvig
"""


class TestCuratedEntryScan(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "royal_slesvig.yml").write_text(SEED)

    def test_finds_only_entries_carrying_curator_input(self) -> None:
        found = _existing_curated_entries(self.dir)
        self.assertEqual({"t-1", "t-2"}, set(found))
        self.assertNotIn("t-3", found, "an un-curated entry must stay freely movable")

    def test_reports_the_file_the_curated_entry_lives_in(self) -> None:
        stem, entry = _existing_curated_entries(self.dir)["t-1"]
        self.assertEqual("royal_slesvig", stem)
        self.assertEqual("royal_slesvig", entry["issuing_entity"])

    def test_a_missing_source_dir_is_not_an_error(self) -> None:
        self.assertEqual({}, _existing_curated_entries(self.dir / "nope"))


class TestHoldSemantics(unittest.TestCase):
    """The two mechanisms `write_v2_seed` drives off that scan."""

    def setUp(self) -> None:
        import tempfile
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "royal_slesvig.yml").write_text(SEED)
        self.found = _existing_curated_entries(self.dir)

    def test_held_entity_is_the_one_that_reroutes(self) -> None:
        _, entry = self.found["t-1"]
        self.assertIn("issuing_entity", set(entry.get("_curation_holds") or ()))

    def test_a_hold_on_another_field_does_not_pin_the_entity(self) -> None:
        """t-2 pins `mint`, not the file. Its entity may still change -- the
        hold has to TRAVEL with the coin instead of blocking the move."""
        _, entry = self.found["t-2"]
        holds = set(entry.get("_curation_holds") or ())
        self.assertIn("mint", holds)
        self.assertNotIn("issuing_entity", holds)

    def test_merge_one_carries_the_hold_into_the_relocated_entry(self) -> None:
        from lib.seed_merge import merge_one
        _, existing = self.found["t-2"]
        fresh = {"id": "t-2", "nominal": "4 Pfennig", "mint": "Witten",
                 "mint_verified": True, "issuing_entity": "royal_holstein"}
        merged = merge_one(existing, fresh)
        merged["issuing_entity"] = fresh["issuing_entity"]  # relocation stands
        self.assertIn("mint", set(merged.get("_curation_holds") or ()),
                      "the hold must survive the move")
        self.assertFalse(merged.get("mint"), "held mint=None must not regain «Witten»")
        self.assertEqual("royal_holstein", merged["issuing_entity"])


if __name__ == "__main__":
    unittest.main()
