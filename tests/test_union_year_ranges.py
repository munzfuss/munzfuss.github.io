"""TDD test for `_union_year_ranges` — the cross-source year merge function.

Function under test:
    scripts/maintenance/merge_seeds_cross_source.py :: _union_year_ranges

Behavioural rule the function SHOULD implement (user direction, 2026-05-23):

- Year-range entries from N seed sources come in two shapes:
  • SPAN     (lo, hi) with lo < hi — a less-precise bounding window
             (typical Numista / ucoin «1640-1646» published year-range).
  • SINGLETON (y, y) where lo == hi — an AUTHORITATIVE per-year strike
             attestation (typical NumisMaster / Hede per-year breakdown).

- When N sources are merged:
  1. UNION all singletons across all members → these are the
     authoritative attested years.
  2. For each span: if ANY singleton year falls inside the span's
     [lo, hi] range, the span is OVERLAP-DISPLACED by the discrete
     attestations — discarded entirely.
  3. Spans with no overlapping singleton SURVIVE and are emitted
     as-is.
  4. Result = (union of singletons) ∪ (surviving spans), sorted.

- Rationale: discrete singletons say «strike happened in THIS year»;
  span says «strikes happened SOMEWHERE in this range». When they
  conflict, the discrete authority wins per «дискретні витісняють
  ширший період коли перекриваються».

Test harness: stdlib unittest (no pytest dep needed). Run via:

    .venv/bin/python -m unittest tests.test_union_year_ranges -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make scripts/ importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Import the function under test
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"),
)
_merger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_merger)
_union_year_ranges = _merger._union_year_ranges


def _member(year_ranges=None, year_first=None, year_last=None):
    """Build a minimal member dict with year fields."""
    m = {}
    if year_ranges is not None:
        m["year_ranges"] = year_ranges
    if year_first is not None:
        m["year_first"] = year_first
    if year_last is not None:
        m["year_last"] = year_last
    return m


class TestUnionYearRangesBasic(unittest.TestCase):
    """Sanity cases — these should already pass under current implementation."""

    def test_empty_members(self):
        """No members → None."""
        self.assertIsNone(_union_year_ranges([]))

    def test_members_with_no_year_info(self):
        """Members without year fields → None."""
        self.assertIsNone(_union_year_ranges([{}, {"nominal": "X"}]))

    def test_single_member_single_span(self):
        """Single span, single member → preserve."""
        self.assertEqual(
            _union_year_ranges([_member(year_ranges=[[1640, 1646]])]),
            [[1640, 1646]],
        )

    def test_single_member_single_singleton(self):
        """Single singleton → preserve."""
        self.assertEqual(
            _union_year_ranges([_member(year_ranges=[[1532, 1532]])]),
            [[1532, 1532]],
        )

    def test_single_member_discrete_singletons(self):
        """Multiple discrete singletons in one member → preserve all."""
        self.assertEqual(
            _union_year_ranges([_member(year_ranges=[
                [1640, 1640], [1642, 1642], [1646, 1646],
            ])]),
            [[1640, 1640], [1642, 1642], [1646, 1646]],
        )

    def test_year_first_year_last_fallback(self):
        """Member without year_ranges but with year_first/year_last."""
        self.assertEqual(
            _union_year_ranges([_member(year_first=1640, year_last=1646)]),
            [[1640, 1646]],
        )

    def test_two_non_overlapping_spans(self):
        """Two members, non-overlapping spans, no singletons → both preserved."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1620, 1625]]),
                _member(year_ranges=[[1640, 1650]]),
            ]),
            [[1620, 1625], [1640, 1650]],
        )


class TestUnionYearRangesDiscreteDisplacement(unittest.TestCase):
    """THE CORE RULE: discrete singletons displace overlapping spans.

    These cases currently FAIL — they're the bug we're fixing.
    """

    def test_163665_case_singletons_cover_span_endpoints(self):
        """Bug 1 canonical case: ucoin span + NumisMaster discretes for KM-29.

        ucoin says «1640-1646» (range), NumisMaster says «1640, 1642, 1646»
        (discrete strike years). The discretes overlap the span at BOTH
        endpoints. Per rule: discretes win, span discarded.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),  # ucoin span
                _member(year_ranges=[
                    [1640, 1640], [1642, 1642], [1646, 1646],
                ]),  # NumisMaster discretes
            ]),
            [[1640, 1640], [1642, 1642], [1646, 1646]],
        )

    def test_singletons_strictly_inside_span(self):
        """Discretes inside span (not on endpoints) — discretes still win."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1650]]),
                _member(year_ranges=[[1643, 1643], [1647, 1647]]),
            ]),
            [[1643, 1643], [1647, 1647]],
        )

    def test_single_singleton_overlaps_span(self):
        """Even one discrete singleton overlapping a span discards the span."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1642, 1642]]),
            ]),
            [[1642, 1642]],
        )

    def test_singleton_at_span_endpoint(self):
        """Singleton matching span's start endpoint → displaces span."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1640, 1640]]),
            ]),
            [[1640, 1640]],
        )

    def test_docstring_example_under_new_rule(self):
        """The current docstring example (which the new rule changes).

        Member A: year_ranges = [[1591, 1593]]    (span)
        Member B: year_ranges = [[1591,1591], [1595,1595]]  (singletons)

        OLD behaviour: [[1591, 1593], [1595, 1595]]
                      (span absorbed singleton 1591, kept singleton 1595)
        NEW rule: singleton 1591 overlaps span → span discarded.
                  Result: [[1591,1591], [1595,1595]]
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1591, 1593]]),
                _member(year_ranges=[[1591, 1591], [1595, 1595]]),
            ]),
            [[1591, 1591], [1595, 1595]],
        )

    def test_multiple_sources_with_discretes_unite_and_displace(self):
        """Per user: «при наявності декількох джерел які дають такі дискрети –
        їхні дискрети перекриваються, і ширший менш точний період все одно
        програє».

        Three sources:
          A: span [1640, 1650]
          B: singletons {1640, 1645}
          C: singletons {1645, 1648}

        Singletons union → {1640, 1645, 1648}. Span overlaps them → discarded.
        Result: [[1640,1640], [1645,1645], [1648,1648]]
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1650]]),
                _member(year_ranges=[[1640, 1640], [1645, 1645]]),
                _member(year_ranges=[[1645, 1645], [1648, 1648]]),
            ]),
            [[1640, 1640], [1645, 1645], [1648, 1648]],
        )


class TestUnionYearRangesNonDisplacement(unittest.TestCase):
    """Cases where the discrete-displaces-span rule does NOT fire."""

    def test_singleton_outside_span_both_preserved(self):
        """Singleton outside span → no overlap → both preserved."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1700, 1700]]),
            ]),
            [[1640, 1646], [1700, 1700]],
        )

    def test_two_spans_no_singletons_preserved(self):
        """No singletons exist → spans preserved (no displacement rule fires)."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1620, 1625]]),
                _member(year_ranges=[[1640, 1650]]),
            ]),
            [[1620, 1625], [1640, 1650]],
        )

    def test_two_singletons_disjoint_no_span(self):
        """Two disjoint singletons, no span → union of singletons preserved."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1640]]),
                _member(year_ranges=[[1700, 1700]]),
            ]),
            [[1640, 1640], [1700, 1700]],
        )

    def test_span_survives_when_singletons_only_outside(self):
        """Multiple spans + singletons that don't overlap ANY span → all kept."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1670, 1675]]),
                _member(year_ranges=[[1700, 1700]]),  # outside both spans
            ]),
            [[1640, 1646], [1670, 1675], [1700, 1700]],
        )


class TestUnionYearRangesEdgeCases(unittest.TestCase):
    """Edge cases that probe rule boundaries."""

    def test_duplicate_span_from_two_sources(self):
        """Same span from two sources → deduplicated."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1640, 1646]]),
            ]),
            [[1640, 1646]],
        )

    def test_duplicate_singleton_from_two_sources(self):
        """Same singleton from two sources → deduplicated."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1640]]),
                _member(year_ranges=[[1640, 1640]]),
            ]),
            [[1640, 1640]],
        )

    def test_mixed_member_span_and_singleton_one_source(self):
        """Single member with both a span and an outside singleton — keep both.

        (No cross-source displacement to apply; same source asserting both.)
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646], [1650, 1650]]),
            ]),
            [[1640, 1646], [1650, 1650]],
        )

    def test_span_partially_overlaps_another_span(self):
        """Two overlapping spans, no singletons → merged into one wider span.

        (No singletons → no displacement; classic envelope union is OK.)
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1644, 1650]]),
            ]),
            [[1640, 1650]],
        )

    def test_singletons_partially_overlap_multiple_spans(self):
        """Singletons displace EACH span they overlap, not all spans globally.

        Singletons {1645} overlap span [1640,1650] but NOT span [1700,1710].
        First span discarded; second preserved alongside singletons.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1650]]),
                _member(year_ranges=[[1700, 1710]]),
                _member(year_ranges=[[1645, 1645]]),
            ]),
            [[1645, 1645], [1700, 1710]],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
