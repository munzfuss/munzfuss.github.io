"""`verify_reflow` must call a loss a loss, and never call a gain one.

The tool answers the one question no other auditor in this project answers: is
the working tree WORSE than what is committed? Everything else measures inside
the tree — `audit_curation_loss` compares a final against what the next absorb
would recompute, `audit_lost_citations` against its own current members,
`audit_v2` checks invariants within one state, and `trace_coin` diffs two
snapshots that a human took by hand.

That last one is where it kept going wrong. On 2026-08-01 four hand-built
baselines were each wrong differently: a truncated cache field, a resolution
scoped to one entity while cross-entity members live elsewhere, a snapshot of a
half-applied pipeline, and a diff nobody read. A committed baseline removes the
whole class — `git show HEAD:` cannot be half-applied or truncated.

These tests pin the classification, which is the part with judgement in it:

  GAIN, never blocks — a new coin, a new reading, a scalar filling in, a
  catalogue register gaining a value, and a coin removed because a survivor
  absorbed it (that is `dedup_final_foundations`' fold, and it is how six
  duplicate Rigsbanktegn finals were legitimately retired the same day).

  LOSS, always blocks — a coin gone with nothing absorbing it, a scalar
  emptied, a list or catalogue register that shrank, a fuss/phase demoted back
  to seed_unsorted.

Run:
    .venv/bin/python -m unittest tests.test_verify_reflow -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "verify_reflow", PROJECT_ROOT / "scripts" / "maintenance" / "verify_reflow.py")
VR = importlib.util.module_from_spec(_spec)
sys.modules["verify_reflow"] = VR
_spec.loader.exec_module(VR)


class _Base(unittest.TestCase):
    """Drive the classifier directly — no git tree, no filesystem, no stubs."""

    def run_case(self, head, cur, excluded=frozenset(), retracted=None):
        idx = lambda lst: {c["id"]: c for c in lst}
        return VR.compare_coins("stub", idx(head), idx(cur), excluded=excluded,
                                retracted=retracted)


class TestLosses(_Base):
    def test_coin_gone_with_no_absorber(self):
        r = self.run_case([{"id": "a", "nominal": "1 Dukat",
                            "sources": [{"url": "u1"}]}], [])
        self.assertTrue(any("COIN GONE" in m for m in r["losses"]))

    def test_scalar_emptied(self):
        r = self.run_case([{"id": "a", "mint": "Kopenhagen"}],
                          [{"id": "a", "mint": None}])
        self.assertTrue(any("FIELD EMPTIED" in m for m in r["losses"]))

    def test_list_shrank(self):
        r = self.run_case(
            [{"id": "a", "sources": [{"url": "u1"}, {"url": "u2"}]}],
            [{"id": "a", "sources": [{"url": "u1"}]}])
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))

    def test_catalogue_register_shrank(self):
        r = self.run_case([{"id": "a", "catalog": {"km": ["1", "2"]}}],
                          [{"id": "a", "catalog": {"km": ["1"]}}])
        self.assertTrue(any("CATALOG SHRANK" in m for m in r["losses"]))

    def test_demoted_to_seed_unsorted(self):
        r = self.run_case([{"id": "a", "fuss": "reichsdukatenfuss"}],
                          [{"id": "a", "fuss": "seed_unsorted"}])
        self.assertTrue(any("DEMOTED" in m for m in r["losses"]))


class TestGains(_Base):
    def test_new_coin(self):
        r = self.run_case([], [{"id": "a"}])
        self.assertEqual(r["losses"], [])

    def test_scalar_filling_in(self):
        r = self.run_case([{"id": "a", "mint": None}],
                          [{"id": "a", "mint": "Kopenhagen"}])
        self.assertEqual(r["losses"], [])

    def test_list_growing(self):
        r = self.run_case([{"id": "a", "sources": [{"url": "u1"}]}],
                          [{"id": "a", "sources": [{"url": "u1"}, {"url": "u2"}]}])
        self.assertEqual(r["losses"], [])

    def test_fold_recognised_via_composed_of(self):
        # dedup_final_foundations pins the dropped id on the survivor.
        r = self.run_case(
            [{"id": "keep"}, {"id": "drop", "sources": [{"url": "u1"}]}],
            [{"id": "keep", "composed_of": ["drop"]}])
        self.assertEqual(r["losses"], [])
        self.assertTrue(any("folded into keep" in g for g in r["gains"]))

    def test_fold_recognised_via_absorbed_sources(self):
        # The I2 fix strips a pin that no longer resolves, so a real fold can
        # arrive with the survivor merely carrying the dropped coin's URLs —
        # which is exactly how the six Rigsbanktegn pairs ended up on disk.
        r = self.run_case(
            [{"id": "keep", "sources": [{"url": "u1"}]},
             {"id": "drop", "sources": [{"url": "u1"}, {"url": "u2"}]}],
            [{"id": "keep", "sources": [{"url": "u1"}, {"url": "u2"}]}])
        self.assertEqual(r["losses"], [])

    def test_partial_absorption_is_still_a_loss(self):
        # Survivor carries only SOME of the dropped coin's sources → not a fold.
        r = self.run_case(
            [{"id": "keep", "sources": [{"url": "u1"}]},
             {"id": "drop", "sources": [{"url": "u2"}, {"url": "u3"}]}],
            [{"id": "keep", "sources": [{"url": "u1"}, {"url": "u2"}]}])
        self.assertTrue(any("COIN GONE" in m for m in r["losses"]))


class TestRedistribution(_Base):
    """A member changing class is not a loss — the data goes WITH it.

    The unit that carries data through the pipeline is the seed (§9b), and a
    merge decision re-assigns seeds between classes. The old class shrinks, the
    new one grows, nothing is lost. Judged strictly per coin, every such move
    reads as a loss: on 2026-08-02 that produced 56 «losses» for a re-flow whose
    entity-wide census dropped not one citation, not one catalogue index and not
    one attested year.
    """

    def test_dissolved_class_split_across_two_survivors(self):
        # unified-kmk-155180's 13 KMM citations split 6/7 between
        # km-x005-chr-iv-1620 and km-82-chr-iv-1640. No single survivor is a
        # superset, so neither the composed_of pin nor the subset test fires —
        # but between them the survivors carry every URL.
        r = self.run_case(
            [{"id": "drop", "sources": [{"url": "u1"}, {"url": "u2"},
                                        {"url": "u3"}]}],
            [{"id": "keepA", "sources": [{"url": "u1"}]},
             {"id": "keepB", "sources": [{"url": "u2"}, {"url": "u3"}]}])
        self.assertEqual(r["losses"], [])
        self.assertTrue(any("folded into" in g for g in r["gains"]))

    def test_incomplete_redistribution_still_blocks(self):
        # One URL that no survivor carries is a real loss and must still report.
        r = self.run_case(
            [{"id": "drop", "sources": [{"url": "u1"}, {"url": "u2"},
                                        {"url": "gone"}]}],
            [{"id": "keepA", "sources": [{"url": "u1"}]},
             {"id": "keepB", "sources": [{"url": "u2"}]}])
        self.assertTrue(any("COIN GONE" in m for m in r["losses"]))

    def test_reading_moved_to_another_coin_is_not_a_loss(self):
        r = self.run_case(
            [{"id": "a", "weight_rough_g": [{"value": 1.0, "source": "kmk"},
                                            {"value": 2.0, "source": "kmk"}]},
             {"id": "b", "weight_rough_g": []}],
            [{"id": "a", "weight_rough_g": [{"value": 1.0, "source": "kmk"}]},
             {"id": "b", "weight_rough_g": [{"value": 2.0, "source": "kmk"}]}])
        self.assertEqual(r["losses"], [])
        self.assertEqual(r["moved"], 1)

    def test_reading_lost_by_everyone_still_blocks(self):
        r = self.run_case(
            [{"id": "a", "weight_rough_g": [{"value": 1.0, "source": "kmk"},
                                            {"value": 2.0, "source": "kmk"}]}],
            [{"id": "a", "weight_rough_g": [{"value": 1.0, "source": "kmk"}]}])
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))

    def test_catalogue_index_moved_to_another_coin(self):
        # unified-kmk-149618's Hede «134» left with the members that changed
        # class; the destination attests it.
        r = self.run_case(
            [{"id": "a", "catalog": {"hede": ["134", "134A"]}}, {"id": "b"}],
            [{"id": "a", "catalog": {"hede": "134A"}},
             {"id": "b", "catalog": {"hede": "134"}}])
        self.assertEqual(r["losses"], [])

    def test_catalogue_index_moved_to_a_different_register_still_blocks(self):
        # Attestation is keyed per register — a `km: 134` elsewhere does NOT
        # cover a lost `hede: 134`.
        r = self.run_case(
            [{"id": "a", "catalog": {"hede": ["134", "134A"]}}, {"id": "b"}],
            [{"id": "a", "catalog": {"hede": "134A"}},
             {"id": "b", "catalog": {"km": "134"}}])
        self.assertTrue(any("CATALOG SHRANK" in m for m in r["losses"]))


class TestNormalisationsAreNotLosses(_Base):
    """Three shapes where the value is intact and only its spelling moved."""

    def test_display_flag_flip_is_not_a_dropped_citation(self):
        # absorb's `_suppress_weightless_museum_overcollection` HIDES a surplus
        # museum citation; the citation stays in the YAML, one key richer.
        # km-82-chr-iv-1640 was reported as losing KMM 693125 while carrying it.
        r = self.run_case(
            [{"id": "a", "sources": [{"url": "u1", "ref": "KMM 693125"}]}],
            [{"id": "a", "sources": [{"url": "u1", "ref": "KMM 693125",
                                      "display": False}]}])
        self.assertEqual(r["losses"], [])

    def test_catalogue_case_folding_is_not_a_lost_index(self):
        # `_fold_catalog_indices` de-dups case-insensitively: seed kmk-348205's
        # Hede «75a» merging into a class carrying «75A» is the same index.
        r = self.run_case([{"id": "a", "catalog": {"hede": "75a"}}],
                          [{"id": "a", "catalog": {"hede": "75A"}}])
        self.assertEqual(r["losses"], [])

    def test_year_range_deoverlap_is_not_a_lost_year(self):
        # The merger unions and de-overlaps ranges (D19): [1813,1813] folding
        # into [1813,1815] loses the tuple, not the year.
        r = self.run_case([{"id": "a", "year_ranges": [[1813, 1813]]}],
                          [{"id": "a", "year_ranges": [[1813, 1815]]}])
        self.assertEqual(r["losses"], [])

    def test_a_year_nothing_attests_still_blocks(self):
        r = self.run_case([{"id": "a", "year_ranges": [[1813, 1815]]}],
                          [{"id": "a", "year_ranges": [[1814, 1815]]}])
        self.assertTrue(any("year_ranges" in m for m in r["losses"]))


class TestCorrectedValuesAreNotLosses(_Base):
    """A reading whose VALUE changed under an unchanged identity is not lost.

    Keying a list entry on its whole serialisation cannot tell a corrected
    reading from a dropped one — both read as «one key vanished». On 2026-08-02
    that reported km-82-chr-iv-1640 as losing a source and a weight while the
    coin had in fact gained both (sources 7 → 8, weights 6 → 7): one kmk
    specimen's weight had merely been corrected to 0.932.
    """

    def test_corrected_weight_under_same_source_is_not_a_loss(self):
        r = self.run_case(
            [{"id": "a", "weight_rough_g": [{"value": 0.93, "source": "kmk 693125"}]}],
            [{"id": "a", "weight_rough_g": [{"value": 0.932, "source": "kmk 693125"}]}])
        self.assertEqual(r["losses"], [])
        self.assertTrue(any("value changed" in m for m in r["changes"]))

    def test_km_82_shape_list_grew_while_one_value_was_corrected(self):
        head = [{"id": "km-82-chr-iv-1640",
                 "sources": [{"url": f"u{i}", "ref": f"KMM {i}"} for i in range(7)],
                 "weight_rough_g": [{"value": 0.90 + i / 100, "source": f"kmk {i}"}
                                    for i in range(6)]}]
        cur = [{"id": "km-82-chr-iv-1640",
                # one citation's ref text was re-worded, and an eighth added
                "sources": ([{"url": "u0", "ref": "KMM 0 (Kopenhagen)"}]
                            + [{"url": f"u{i}", "ref": f"KMM {i}"} for i in range(1, 8)]),
                # one specimen's weight corrected, and a seventh added
                "weight_rough_g": ([{"value": 0.932, "source": "kmk 0"}]
                                   + [{"value": 0.90 + i / 100, "source": f"kmk {i}"}
                                      for i in range(1, 7)])}]
        r = self.run_case(head, cur)
        self.assertEqual(r["losses"], [])
        self.assertEqual(len(r["changes"]), 2)

    def test_a_dropped_identity_is_still_a_loss(self):
        # Same source label, but the entry is GONE, not corrected.
        r = self.run_case(
            [{"id": "a", "weight_rough_g": [{"value": 0.93, "source": "kmk 1"},
                                            {"value": 1.10, "source": "kmk 2"}]}],
            [{"id": "a", "weight_rough_g": [{"value": 0.93, "source": "kmk 1"}]}])
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))

    def test_source_without_url_falls_back_to_ref_identity(self):
        r = self.run_case(
            [{"id": "a", "sources": [{"ref": "Hede 39A", "type": "catalog"}]}],
            [{"id": "a", "sources": [{"ref": "Hede 39A", "type": "literature"}]}])
        self.assertEqual(r["losses"], [])

    def test_duplicate_identity_losing_one_entry_still_blocks(self):
        # Two readings share the source label; one disappears. Identity is still
        # present — but not in the same NUMBER, so it is a loss.
        r = self.run_case(
            [{"id": "a", "weight_rough_g": [{"value": 1.0, "source": "kmk"},
                                            {"value": 2.0, "source": "kmk"}]}],
            [{"id": "a", "weight_rough_g": [{"value": 1.0, "source": "kmk"}]}])
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))


class TestCuratorExclusions(_Base):
    """A recorded §9 exclusion is a deliberate removal, not data lost."""

    def test_exclusion_naming_the_vanished_id_is_not_a_loss(self):
        r = self.run_case([{"id": "a", "nominal": "5 Dukat",
                            "sources": [{"url": "u1"}]}], [],
                          excluded={"a"})
        self.assertEqual(r["losses"], [])
        self.assertTrue(any("curator exclusion" in m for m in r["dropped"]))

    def test_exclusion_naming_a_member_is_not_a_loss(self):
        # The real shape: exclusions carry SEED ids (§9b), the final that
        # disappears is keyed by its unified id.
        r = self.run_case([{"id": "unified-x", "composed_of": ["dk-numista-1"],
                            "sources": [{"url": "u1"}]}], [],
                          excluded={"dk-numista-1"})
        self.assertEqual(r["losses"], [])
        self.assertEqual(len(r["dropped"]), 1)

    def test_an_unrelated_exclusion_does_not_excuse_a_loss(self):
        r = self.run_case([{"id": "a", "sources": [{"url": "u1"}]}], [],
                          excluded={"some-other-coin"})
        self.assertTrue(any("COIN GONE" in m for m in r["losses"]))
        self.assertEqual(r["dropped"], [])

    def test_an_exclusion_does_not_excuse_a_field_loss_on_a_surviving_coin(self):
        # Being listed must not turn into a blanket amnesty for a coin that is
        # still here and quietly lost a value.
        r = self.run_case([{"id": "a", "mint": "Kopenhagen"}],
                          [{"id": "a", "mint": None}],
                          excluded={"a"})
        self.assertTrue(any("FIELD EMPTIED" in m for m in r["losses"]))


class TestParserRetractionAmnesty(unittest.TestCase):
    """The third recorded-removal case, after curator exclusions and folds.

    `catalog` is deep-merged and accumulates, so a parser that stops emitting a
    wrong value cannot remove it — a heal must, and the heal makes the register
    shrink. data/v2/_retracted_refs.yml is the record that lets the gate tell
    that apart from real loss. The amnesty has to stay NARROW or it becomes a
    hole: these tests pin both edges.
    """

    def _case(self, head, cur, retracted=None):
        idx = lambda lst: {c["id"]: c for c in lst}
        return VR.compare_coins("stub", idx(head), idx(cur),
                                retracted=retracted or {})

    def test_a_retracted_value_is_not_a_loss(self):
        r = self._case(
            [{"id": "a", "catalog": {"schou": ["7", "7a"]}}],
            [{"id": "a", "catalog": {"schou": ["7"]}}],
            retracted={"schou": {"7a"}})
        self.assertEqual(r["losses"], [])
        self.assertEqual(len(r["retractions"]), 1)

    def test_case_folding_matches(self):
        # absorb upper-cases catalogue values; the ledger holds the source form.
        r = self._case(
            [{"id": "a", "catalog": {"schou": ["7", "7A"]}}],
            [{"id": "a", "catalog": {"schou": ["7"]}}],
            retracted={"schou": {"7a"}})
        self.assertEqual(r["losses"], [])

    def test_an_unlisted_value_in_the_same_shrink_still_blocks(self):
        r = self._case(
            [{"id": "a", "catalog": {"schou": ["7", "7a", "9"]}}],
            [{"id": "a", "catalog": {"schou": ["7"]}}],
            retracted={"schou": {"7a"}})
        self.assertTrue(any("CATALOG SHRANK" in m and "9" in m for m in r["losses"]))

    def test_the_amnesty_does_not_cross_registers(self):
        r = self._case(
            [{"id": "a", "catalog": {"sieg": ["7a"], "schou": ["7"]}}],
            [{"id": "a", "catalog": {"schou": ["7"]}}],
            retracted={"schou": {"7a"}})
        self.assertTrue(any("sieg" in m for m in r["losses"]))

    def test_it_does_not_excuse_a_lost_source(self):
        r = self._case(
            [{"id": "a", "sources": [{"url": "u1"}, {"url": "u2"}],
              "catalog": {"schou": ["7"]}}],
            [{"id": "a", "sources": [{"url": "u1"}], "catalog": {"schou": ["7"]}}],
            retracted={"schou": {"7a"}})
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))

    def test_no_ledger_means_business_as_usual(self):
        r = self._case(
            [{"id": "a", "catalog": {"schou": ["7", "7a"]}}],
            [{"id": "a", "catalog": {"schou": ["7"]}}])
        self.assertTrue(any("CATALOG SHRANK" in m for m in r["losses"]))


class CrossEntityRelocation(unittest.TestCase):
    """A coin relocated by _cross_entity.yml leaves its source entity file and
    takes its citations with it. The source-side comparison cannot see the
    destination, so before the `elsewhere` index every such merge read as loss
    and needed --no-verify. Real case: KMM 81473 moving gottorp_duchy ->
    danish_realm with the Galster-131 class, 2026-08-19."""

    @staticmethod
    def _case(head, cur, elsewhere=None):
        idx = {c["id"]: c for c in head}, {c["id"]: c for c in cur}
        return VR.compare_coins("stub", idx[0], idx[1], elsewhere=elsewhere)

    def test_a_citation_alive_in_a_relocation_target_is_not_a_loss(self):
        moved = {"type": "museum", "url": "u2"}
        r = self._case(
            [{"id": "a", "sources": [{"url": "u1"}, moved]}],
            [{"id": "a", "sources": [{"url": "u1"}]}],
            elsewhere={"sources": {VR._key(moved)}})
        self.assertEqual(r["losses"], [])
        self.assertEqual(r["moved"], 1)

    def test_without_the_index_the_same_drop_still_blocks(self):
        r = self._case(
            [{"id": "a", "sources": [{"url": "u1"}, {"url": "u2"}]}],
            [{"id": "a", "sources": [{"url": "u1"}]}])
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))

    def test_it_excuses_only_the_value_that_is_attested_elsewhere(self):
        kept = {"url": "u2"}
        r = self._case(
            [{"id": "a", "sources": [{"url": "u1"}, kept, {"url": "u3"}]}],
            [{"id": "a", "sources": [{"url": "u1"}]}],
            elsewhere={"sources": {VR._key(kept)}})
        self.assertTrue(any("LIST SHRANK" in m and "u3" in m for m in r["losses"]))

    def test_the_target_set_comes_from_the_cross_entity_file(self):
        targets = VR._cross_entity_targets()
        self.assertIn("royal_holstein", targets)
        self.assertNotIn(None, targets)
        # Scoped, not global: a value is excused only where the relocation
        # mechanism could have put it.
        self.assertLess(len(targets), 22)


class TestDemotedInMove(_Base):
    """A coin that moves must not arrive in seed_unsorted with its fuss left
    behind (2026-10-09: fifteen coins lost their classification on the
    royal_slesvig split; the identity checks excused them as «alive elsewhere»)."""

    def tearDown(self):
        VR._ELSEWHERE_COINS = None
        VR._ELSEWHERE_FUSS.clear()

    def test_fold_into_unsorted_class_blocks(self):
        r = self.run_case(
            [{"id": "old", "fuss": "9_thaler", "phase": "I"}],
            [{"id": "new", "fuss": "seed_unsorted", "composed_of": ["old"]}])
        self.assertTrue(any("DEMOTED IN MOVE" in m for m in r["losses"]), r["losses"])

    def test_fold_into_classified_class_is_a_gain(self):
        r = self.run_case(
            [{"id": "old", "fuss": "9_thaler"}],
            [{"id": "new", "fuss": "9_thaler", "composed_of": ["old"]}])
        self.assertEqual(r["losses"], [])

    def test_relocation_to_unsorted_in_other_entity_blocks(self):
        VR._ELSEWHERE_COINS = {"unified-x": ("other", "unified-x")}
        VR._ELSEWHERE_FUSS[("other", "unified-x")] = "seed_unsorted"
        r = self.run_case([{"id": "unified-x", "fuss": "8_daler_lybsk_fod"}], [])
        self.assertTrue(any("DEMOTED IN MOVE" in m for m in r["losses"]), r["losses"])

    def test_relocation_keeping_its_fuss_passes(self):
        VR._ELSEWHERE_COINS = {"unified-x": ("other", "unified-x")}
        VR._ELSEWHERE_FUSS[("other", "unified-x")] = "8_daler_lybsk_fod"
        r = self.run_case([{"id": "unified-x", "fuss": "8_daler_lybsk_fod"}], [])
        self.assertEqual(r["losses"], [])

    def test_unsorted_coin_moving_to_unsorted_passes(self):
        VR._ELSEWHERE_COINS = {"unified-x": ("other", "unified-x")}
        VR._ELSEWHERE_FUSS[("other", "unified-x")] = "seed_unsorted"
        r = self.run_case([{"id": "unified-x", "fuss": "seed_unsorted"}], [])
        self.assertEqual(r["losses"], [])


class TestSeedDeclassified(unittest.TestCase):
    """Seed-keyed demotion (§9b). The 202a5c1 Hede re-seed split nc5h30 into
    sub-letter seeds: the classified final stayed as a shell and a NEW
    seed_unsorted class took every member, which the id-keyed checks read as
    a gain. Keyed by seed it is a loss."""

    WAS = {"s1": ("dn", "unified-dk-hede-nc5h30", "9_25_thaler"),
           "s2": ("dn", "unified-dk-hede-nc5h30", "9_25_thaler")}

    def test_shell_plus_new_unsorted_class_blocks(self):
        now = {"s1": ("dn", "unified-dk-hede-nc5h30a", "seed_unsorted"),
               "s2": ("dn", "unified-dk-hede-nc5h30a", "seed_unsorted")}
        r = VR.declassified(self.WAS, now, set())
        self.assertEqual(len(r), 1)
        self.assertIn("SEED DECLASSIFIED", r[0])

    def test_seed_still_classified_elsewhere_passes(self):
        now = {"s1": ("dn", "x", "9_25_thaler"), "s2": ("rh", "y", "9_25_thaler")}
        self.assertEqual(VR.declassified(self.WAS, now, set()), [])

    def test_recorded_declassify_or_exclusion_excuses(self):
        now = {"s1": ("dn", "z", "seed_unsorted"), "s2": ("dn", "z", "seed_unsorted")}
        self.assertEqual(VR.declassified(self.WAS, now, {"s1", "s2"}), [])

    def test_seed_gone_is_left_to_the_coin_checks(self):
        self.assertEqual(VR.declassified(self.WAS, {}, set()), [])

    def test_unsorted_before_and_after_passes(self):
        was = {"s1": ("dn", "a", "seed_unsorted")}
        now = {"s1": ("dn", "b", "seed_unsorted")}
        self.assertEqual(VR.declassified(was, now, set()), [])


if __name__ == "__main__":
    unittest.main()
