"""TDD test for `_union_year_ranges` — the cross-source year merge function.

Function under test:
    scripts/maintenance/merge_seeds_cross_source.py :: _union_year_ranges

Behavioural rule the function MUST implement (user direction,
2026-05-23 + 2026-05-26 refinement):

- Year-range entries from N seed sources come in two CLASSIFIED shapes:
  • LOOSE source = a member whose `year_ranges` is a SINGLE non-
                   singleton range `[[lo, hi]]` with lo < hi.
                   Typical: Numista / ucoin's «1640-1646» single field.
  • DISCRETE source = anything else: multi-entry year_ranges, a single
                   singleton `[[y, y]]`, or multiple singletons.
                   Typical: NumisMaster / Hede / Bruun per-year breakdown.

- A DISCRETE source's `year_ranges` is exploded into its full year SET:
  each range `[lo, hi]` contributes years lo..hi inclusive. A range
  like `[[1618, 1619]]` inside a multi-entry list contributes
  {1618, 1619} as DISCRETE attestations (NOT a loose span).

- Cross-source merge rule:

  1. discrete_years = union of attested years from ALL discrete members.
  2. loose_ranges  = list of (lo, hi) tuples from loose members.
  3. SPAN COMPARISON: when discrete_years is non-empty, compute
     discrete_min / discrete_max. For each loose range (lo, hi):
       * If discrete_min ≤ lo AND discrete_max ≥ hi → the discrete
         attestations form a same-or-wider window than the loose source.
         The loose range is DROPPED — discrete wins.
       * Otherwise (discrete forms a NARROWER window) → loose KEPT;
         final compression absorbs the discrete singletons into the
         loose envelope.
  4. Final result = (discrete years as `[y, y]` singletons) + surviving
     loose ranges, sorted and compressed (adjacent / overlapping ranges
     merge).

- Rationale (user direction): when discrete sources together span the
  same window as a loose source, the loose source is by definition
  imprecise about the same period and is supplanted. When discrete
  sources span a NARROWER window than the loose source, the loose
  source carries information about years the discrete attestations
  don't reach, so the loose envelope is retained.

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
    """CORE RULE: discrete years displace a loose range ONLY when the
    discrete attestations span same-or-wider than the loose range.
    """

    def test_163665_case_singletons_cover_span_endpoints(self):
        """KM-29 canonical case: ucoin span + NumisMaster discretes.

        ucoin: «1640-1646» (loose). NumisMaster: «1640, 1642, 1646»
        (discrete). Discrete span 1640-1646 = loose span 1640-1646.
        Per rule: discrete spans same as loose → discrete wins, loose
        discarded.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[
                    [1640, 1640], [1642, 1642], [1646, 1646],
                ]),
            ]),
            [[1640, 1640], [1642, 1642], [1646, 1646]],
        )

    def test_singletons_strictly_inside_span_loose_wins(self):
        """Discrete singletons strictly INSIDE a wider loose range — discrete
        narrower than loose, so loose stays. Final compression absorbs the
        singletons into the loose envelope.

        Previously this case displaced the span; per the refined rule
        (2026-05-26), discrete only wins when it spans same-or-wider.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1650]]),
                _member(year_ranges=[[1643, 1643], [1647, 1647]]),
            ]),
            [[1640, 1650]],
        )

    def test_single_singleton_inside_span_loose_wins(self):
        """One discrete singleton inside wider loose range → discrete
        narrower → loose stays."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1642, 1642]]),
            ]),
            [[1640, 1646]],
        )

    def test_singleton_at_span_endpoint_loose_wins(self):
        """Singleton at span's start endpoint → discrete span (1 year) is
        narrower than loose (7 years) → loose stays."""
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1646]]),
                _member(year_ranges=[[1640, 1640]]),
            ]),
            [[1640, 1646]],
        )

    def test_discrete_span_wider_than_loose_wins(self):
        """Discrete singletons {1591, 1595} span 1591-1595 (5 years).
        Loose [1591, 1593] (3 years). Discrete wider → covers loose
        endpoints → drop loose.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1591, 1593]]),
                _member(year_ranges=[[1591, 1591], [1595, 1595]]),
            ]),
            [[1591, 1591], [1595, 1595]],
        )

    def test_multiple_discrete_sources_unite_to_cover_loose(self):
        """Three sources example:
          A: loose [1640, 1650]
          B: discrete {1640, 1645}
          C: discrete {1645, 1648}

        Combined discrete: {1640, 1645, 1648}, span 1640-1648 (9 years).
        Loose [1640, 1650] span = 11 years. Discrete NARROWER → loose
        stays. Final compress: discrete + loose → [[1640, 1650]].
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1650]]),
                _member(year_ranges=[[1640, 1640], [1645, 1645]]),
                _member(year_ranges=[[1645, 1645], [1648, 1648]]),
            ]),
            [[1640, 1650]],
        )

    def test_multiple_discrete_sources_collectively_wider_loose_dropped(self):
        """Three sources where combined discrete is WIDER than loose:
          A: discrete {1640, 1642}
          B: discrete {1646, 1648}
          C: loose [1641, 1647]

        Combined discrete: {1640, 1642, 1646, 1648}, span 1640-1648.
        Loose 1641-1647. Discrete WIDER (1640 ≤ 1641 AND 1648 ≥ 1647)
        → drop loose.
        Result: [[1640, 1640], [1642, 1642], [1646, 1646], [1648, 1648]].
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1640], [1642, 1642]]),
                _member(year_ranges=[[1646, 1646], [1648, 1648]]),
                _member(year_ranges=[[1641, 1647]]),
            ]),
            [[1640, 1640], [1642, 1642], [1646, 1646], [1648, 1648]],
        )


class TestUnionYearRangesUserDirectionExample(unittest.TestCase):
    """2026-05-26 user direction: cross-source merge example.

    «джерело А дає роки 1611 1613 1618-1619, а джерело Б дає 1613 1614
    1619 1620, а джерело 3 дає 1611-1619, то повинно перемогти
    результуюче "1611, 1613-1614, 1618-1620"»

    This is the canonical case for the refined rule: A and B are both
    multi-entry (DISCRETE) sources; C is a single-range (LOOSE) source
    spanning a narrower window than A∪B. Discrete wins, loose dropped,
    final compression collapses adjacent singletons.
    """

    def test_user_example_three_sources_discrete_wins(self):
        """A: 1611, 1613, 1618-1619 (multi-entry, DISCRETE).
        B: 1613, 1614, 1619, 1620 (multi-entry, DISCRETE).
        C: 1611-1619 (single range, LOOSE).

        Combined discrete: {1611, 1613, 1614, 1618, 1619, 1620}.
        Discrete span 1611-1620 (10 years) ⊃ loose 1611-1619 (9 years)
        → drop loose. Compress discrete: [[1611,1611], [1613,1614],
        [1618,1620]].
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1611, 1611], [1613, 1613], [1618, 1619]]),
                _member(year_ranges=[[1613, 1613], [1614, 1614],
                                     [1619, 1619], [1620, 1620]]),
                _member(year_ranges=[[1611, 1619]]),
            ]),
            [[1611, 1611], [1613, 1614], [1618, 1620]],
        )

    def test_narrow_range_in_multi_entry_member_treated_as_discrete(self):
        """A `[1618, 1619]` range INSIDE a multi-entry year_ranges list
        is DISCRETE attestation of both 1618 AND 1619, NOT a span that
        gets displaced by another source's singleton on 1619.

        Old buggy behaviour: range [1618,1619] gets displaced wholesale
        by singleton 1619 → year 1618 silently lost.
        Correct behaviour: both 1618 and 1619 contribute to discrete_years
        and survive into output.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1611, 1611], [1618, 1619]]),
                _member(year_ranges=[[1619, 1619]]),
            ]),
            [[1611, 1611], [1618, 1619]],
        )

    def test_pair_of_narrow_ranges_no_loose(self):
        """Two members each with a narrow range (multi-year, no singletons,
        no separate loose source). Both treated as discrete-flavoured;
        result is the year-set union compressed.

        A: [[1614, 1617]] (single entry but multi-year — DEFAULT loose
           when alone, but no other discrete source to compete).
        B: [[1616, 1619]] (same shape).

        Both are LOOSE (single non-singleton). No discrete_years.
        → just union loose ranges, compressed: [[1614, 1619]].
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1614, 1617]]),
                _member(year_ranges=[[1616, 1619]]),
            ]),
            [[1614, 1619]],
        )

    def test_reign_window_fallback_loose_keeps_when_discrete_narrower(self):
        """Hans Nobel-style: Bruun attests {1496}, Galster attests {1502},
        reign-window fallback gives [1481, 1513].

        Discrete: {1496, 1502}, span 1496-1502 (7 years).
        Loose [1481, 1513] (33 years). Discrete NARROWER.
        → loose stays. Final compress: loose absorbs discrete singletons.
        Result: [[1481, 1513]].
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1496, 1496]]),
                _member(year_ranges=[[1502, 1502]]),
                _member(year_ranges=[[1481, 1513]]),
            ]),
            [[1481, 1513]],
        )

    def test_two_discrete_sources_no_loose_compress_adjacent(self):
        """A: {1640, 1641}, B: {1641, 1642}. Combined: {1640, 1641, 1642}.
        No loose source. Compression merges adjacent: [[1640, 1642]].
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1640], [1641, 1641]]),
                _member(year_ranges=[[1641, 1641], [1642, 1642]]),
            ]),
            [[1640, 1642]],
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

    def test_singleton_inside_one_of_multiple_spans_loose_wins(self):
        """One discrete singleton inside one of two loose spans → discrete
        span (1 year) narrower than ANY loose span → both loose ranges
        stay. The singleton is absorbed by the loose envelope it falls
        within during compression.

        Per refined rule (2026-05-26): only DISCRETE that spans
        same-or-wider than each loose range displaces. Here {1645}
        spans 1 year << 11 years per loose range → no displacement.
        """
        self.assertEqual(
            _union_year_ranges([
                _member(year_ranges=[[1640, 1650]]),
                _member(year_ranges=[[1700, 1710]]),
                _member(year_ranges=[[1645, 1645]]),
            ]),
            [[1640, 1650], [1700, 1710]],
        )


_format_year_label = _merger._format_year_label


class TestFormatYearLabel(unittest.TestCase):
    """Compact display rendering of year_ranges.

    The function takes the cross-source merged year_ranges output and
    formats it for the `year_label` display field. Singletons render as
    bare year strings; multi-year ranges render with an en-dash; entries
    are joined with «, ».

    Output examples:
      [[1640, 1640]] → "1640"
      [[1640, 1646]] → "1640-1646"
      [[1611, 1611], [1613, 1614], [1618, 1620]] → "1611, 1613-1614, 1618-1620"
    """

    def test_none_input(self):
        """None → None (no year info)."""
        self.assertIsNone(_format_year_label(None))

    def test_empty_list(self):
        """Empty list → None."""
        self.assertIsNone(_format_year_label([]))

    def test_single_singleton(self):
        """[[1640, 1640]] → '1640'."""
        self.assertEqual(_format_year_label([[1640, 1640]]), "1640")

    def test_single_range(self):
        """[[1640, 1646]] → '1640-1646'."""
        self.assertEqual(_format_year_label([[1640, 1646]]), "1640-1646")

    def test_user_example_compact(self):
        """User direction example (2026-05-26):
        [[1611,1611], [1613,1614], [1618,1620]] → '1611, 1613-1614, 1618-1620'.
        """
        self.assertEqual(
            _format_year_label([[1611, 1611], [1613, 1614], [1618, 1620]]),
            "1611, 1613-1614, 1618-1620",
        )

    def test_three_discrete_singletons(self):
        """[[1640,1640], [1642,1642], [1646,1646]] → '1640, 1642, 1646'."""
        self.assertEqual(
            _format_year_label([[1640, 1640], [1642, 1642], [1646, 1646]]),
            "1640, 1642, 1646",
        )

    def test_mixed_singletons_and_ranges(self):
        """Singletons + ranges mixed → comma-separated mix."""
        self.assertEqual(
            _format_year_label([[1481, 1513], [1532, 1532]]),
            "1481-1513, 1532",
        )


class TestYearDemoteMute(unittest.TestCase):
    """§CU curator-mute: a `_year_demoted` member is held to a last-resort pass.

    It contributes years ONLY when no non-muted member does (its years are
    demoted, never deleted). Priority below a normal member, above no-data.
    """

    @staticmethod
    def _muted(year_ranges):
        m = _member(year_ranges=year_ranges)
        m["_year_demoted"] = True
        return m

    def test_muted_reign_window_ignored_when_others_present(self):
        """bruun-3839: bruun 1496-1497 (loose) + muted galster/numista reign
        window 1481-1513 → muted ignored, union is the real strike window."""
        members = [
            _member(year_ranges=[[1496, 1497]]),       # bruun (non-muted)
            self._muted([[1481, 1513]]),               # galster reign-window
            self._muted([[1481, 1513]]),               # numista-355730 reign-window
        ]
        self.assertEqual(_union_year_ranges(members), [[1496, 1497]])

    def test_muted_reign_window_ignored_discrete_case(self):
        """km-795: discrete 1874-1905 attestations + muted kmk-279179 full reign
        1863-1906 → muted ignored, union is the discrete envelope (no 1863/1906)."""
        members = [
            _member(year_ranges=[[1874, 1875], [1882, 1882], [1891, 1891]]),
            _member(year_ranges=[[1894, 1894], [1903, 1905]]),
            self._muted([[1863, 1906]]),               # kmk-279179 reign-window
        ]
        u = _union_year_ranges(members)
        flat = [y for lo, hi in u for y in (lo, hi)]
        self.assertEqual(min(flat), 1874)
        self.assertEqual(max(flat), 1905)
        self.assertNotIn(1863, [lo for lo, hi in u])

    def test_muted_used_as_fallback_when_sole_source(self):
        """A muted member is NOT deleted: if it is the only source of any year,
        its years are used (last-resort fallback)."""
        members = [self._muted([[1481, 1513]])]
        self.assertEqual(_union_year_ranges(members), [[1481, 1513]])

    def test_muted_fallback_when_non_muted_have_no_years(self):
        """Non-muted members present but year-less → fall back to the muted one."""
        members = [
            {"id": "x"},                               # no year fields
            self._muted([[1670, 1699]]),
        ]
        self.assertEqual(_union_year_ranges(members), [[1670, 1699]])

    def test_no_demote_flag_behaves_as_before(self):
        """Without `_year_demoted`, the reign span is KEPT (pre-mute behaviour):
        discrete 1496-1497 does NOT span the loose 1481-1513 → loose retained."""
        members = [
            _member(year_ranges=[[1496, 1497]]),
            _member(year_ranges=[[1481, 1513]]),       # NOT muted
        ]
        self.assertEqual(_union_year_ranges(members), [[1481, 1513]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
