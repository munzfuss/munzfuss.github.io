"""TDD test for `attach_visual_pieces` — derives per-layer rendering
segments from hover-zone segmentation so the fade-end gradient applies
ONLY where the layer is solo (the only active member of its scope in
that zone), not across the full layer width.

Function under test:
    scripts/lib/timeline.py :: attach_visual_pieces

Behavioural rule (user direction 2026-05-23):

  - For each layer L in `bar_layers[bar_id]` that carries `first_approx`
    OR `last_approx`, derive `visual_pieces` from the existing
    `hover_zones[bar_id]` segmentation.
  - Each visual piece corresponds to one zone where L is active.
  - `show_fade_start` = `L.first_approx` AND L is the only active layer
    OF ITS SCOPE in this zone AND the zone touches L's left edge.
  - `show_fade_end`   = `L.last_approx`  AND L is the only active layer
    OF ITS SCOPE in this zone AND the zone touches L's right edge.
  - Adjacent pieces with identical fade flags are merged.
  - Layers with neither approx flag get no `visual_pieces` (default
    single-piece rendering applies in the template).

Effect: layers whose end-uncertainty falls inside a sibling-shadowed
overlap zone get NO fade (drop the bad CSS class). Layers with a
genuine solo tail get the fade only on the tail. Layers fully solo
keep current full-layer fade.

Run via:
    .venv/bin/python -m unittest tests.test_attach_visual_pieces -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Import the function under test. `timeline.py` lives inside the `lib`
# package and uses relative imports (`from .schema import ...`) — must
# be imported via the package path, not loaded standalone.
from lib.timeline import attach_visual_pieces  # noqa: E402


def _layer(**kw) -> dict:
    """Build a minimal layer dict with sensible defaults."""
    return {
        "kind": kw.get("kind", "circulation"),
        "kinds": kw.get("kinds", [kw.get("kind", "circulation")]),
        "scope": kw.get("scope", "anywhere"),
        "first": kw["first"],
        "last": kw["last"],
        "first_approx": kw.get("fa", False),
        "last_approx":  kw.get("la", False),
        "left_pct":     kw["left_pct"],
        "width_pct":    kw["width_pct"],
    }


def _zone(first: int, last: int, layer_indices: list[int],
          left_pct: float, width_pct: float) -> dict:
    """Build a minimal hover-zone dict."""
    return {
        "first": first,
        "last": last,
        "layer_indices": layer_indices,
        "left_pct": left_pct,
        "width_pct": width_pct,
    }


class TestAttachVisualPiecesNoFade(unittest.TestCase):
    """Layers without approx flags don't get visual_pieces."""

    def test_no_approx_no_visual_pieces(self):
        layers = [_layer(kind="mint", first=1500, last=1600,
                          left_pct=0.0, width_pct=25.0)]
        zones  = [_zone(1500, 1600, [0], 0.0, 25.0)]
        bar_layers = {"b": layers}
        hover_zones = {"b": zones}
        attach_visual_pieces(bar_layers, hover_zones)
        self.assertNotIn("visual_pieces", layers[0])

    def test_empty_zones_no_change(self):
        layers = [_layer(first=1500, last=1600, la=True,
                          left_pct=0.0, width_pct=25.0)]
        bar_layers = {"b": layers}
        attach_visual_pieces(bar_layers, {"b": []})
        self.assertNotIn("visual_pieces", layers[0])


class TestAttachVisualPiecesSoloDetection(unittest.TestCase):
    """The core solo-vs-overlap rule, including the canonical KM-29 case."""

    def test_lone_layer_la_full_solo(self):
        """A single layer alone with la=True is solo throughout, touches
        the right edge → one piece with fade_end=True."""
        layers = [_layer(first=1500, last=1600, la=True,
                          left_pct=0.0, width_pct=25.0)]
        zones  = [_zone(1500, 1600, [0], 0.0, 25.0)]
        attach_visual_pieces({"b": layers}, {"b": zones})
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0, "width_pct": 25.0,
             "show_fade_start": False, "show_fade_end": True},
        ])

    def test_nobel_fod_circulation_split(self):
        """Canonical 163665 case for circulation: split at sibling-max-last.

        mint [1496-1532, la=F], status [1496-1533, la=T],
        circulation [1496-1600, la=T] — circulation has solo region
        1534-1600 → split into [1496-1533 solid] + [1534-1600 faded]."""
        layers = [
            _layer(kind="mint",        first=1496, last=1532,
                   left_pct=0.0, width_pct=4.75),
            _layer(kind="status",      first=1496, last=1533, la=True,
                   left_pct=0.0, width_pct=5.0),
            _layer(kind="circulation", first=1496, last=1600, la=True,
                   left_pct=0.0, width_pct=21.75),
        ]
        zones = [
            _zone(1496, 1532, [0, 1, 2], 0.0,  4.75),    # all 3 active
            _zone(1533, 1533, [1, 2],    4.75, 0.25),    # status + circ
            _zone(1534, 1600, [2],       5.0,  16.75),   # circ solo
        ]
        attach_visual_pieces({"b": layers}, {"b": zones})

        # mint: no approx → no visual_pieces
        self.assertNotIn("visual_pieces", layers[0])

        # status: la=T but sibling (circulation) extends past it →
        # NEVER solo → all pieces fade_end=False. After merge-adjacent,
        # the two pieces collapse to one.
        self.assertEqual(layers[1]["visual_pieces"], [
            {"left_pct": 0.0, "width_pct": 5.0,
             "show_fade_start": False, "show_fade_end": False},
        ])

        # circulation: solo in zone 1534-1600 only. After merge, 2 pieces.
        self.assertEqual(layers[2]["visual_pieces"], [
            {"left_pct": 0.0, "width_pct": 5.0,
             "show_fade_start": False, "show_fade_end": False},
            {"left_pct": 5.0, "width_pct": 16.75,
             "show_fade_start": False, "show_fade_end": True},
        ])

    def test_fragmented_solo_middle_no_fade(self):
        """Solo zone in middle (not touching layer edges) → no fade
        applied even if layer has approx flag."""
        layers = [
            _layer(kind="circulation", first=1500, last=1600, la=True,
                   left_pct=0.0, width_pct=25.0),
            _layer(kind="mint",        first=1510, last=1540,
                   left_pct=2.5, width_pct=7.75),
            _layer(kind="status",      first=1560, last=1590,
                   left_pct=15.0, width_pct=7.75),
        ]
        zones = [
            _zone(1500, 1509, [0],       0.0,   2.5),
            _zone(1510, 1540, [0, 1],    2.5,   7.75),
            _zone(1541, 1559, [0],       10.25, 4.75),
            _zone(1560, 1590, [0, 2],    15.0,  7.75),
            _zone(1591, 1600, [0],       22.75, 2.5),
        ]
        attach_visual_pieces({"b": layers}, {"b": zones})
        # L0 (circulation) pieces, post-merge:
        #   [1500-1590 mixed solo/overlap, all flags False after merge]
        #   [1591-1600 solo at right, fade_end=True]
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0,   "width_pct": 22.75,
             "show_fade_start": False, "show_fade_end": False},
            {"left_pct": 22.75, "width_pct": 2.5,
             "show_fade_start": False, "show_fade_end": True},
        ])

    def test_both_approx_with_edge_solo(self):
        """Layer with BOTH fa=T and la=T, siblings overlap middle only
        → 3-way split: faded-left + solid-middle + faded-right."""
        layers = [
            _layer(first=1500, last=1600, fa=True, la=True,
                   left_pct=0.0, width_pct=25.0),
            _layer(first=1510, last=1590,
                   left_pct=2.5, width_pct=20.25),
        ]
        zones = [
            _zone(1500, 1509, [0],    0.0,   2.5),     # solo at left
            _zone(1510, 1590, [0, 1], 2.5,   20.25),   # overlap
            _zone(1591, 1600, [0],    22.75, 2.5),     # solo at right
        ]
        attach_visual_pieces({"b": layers}, {"b": zones})
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0,   "width_pct": 2.5,
             "show_fade_start": True,  "show_fade_end": False},
            {"left_pct": 2.5,   "width_pct": 20.25,
             "show_fade_start": False, "show_fade_end": False},
            {"left_pct": 22.75, "width_pct": 2.5,
             "show_fade_start": False, "show_fade_end": True},
        ])

    def test_fa_only_with_left_solo(self):
        """Layer with fa=T (no la), siblings extend past on right
        → split: faded-left + solid-right (no right-fade)."""
        layers = [
            _layer(first=1500, last=1600, fa=True,
                   left_pct=0.0, width_pct=25.0),
            _layer(first=1510, last=1600,
                   left_pct=2.5, width_pct=22.5),
        ]
        zones = [
            _zone(1500, 1509, [0],    0.0,   2.5),
            _zone(1510, 1600, [0, 1], 2.5,   22.75),
        ]
        attach_visual_pieces({"b": layers}, {"b": zones})
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0, "width_pct": 2.5,
             "show_fade_start": True,  "show_fade_end": False},
            {"left_pct": 2.5, "width_pct": 22.75,
             "show_fade_start": False, "show_fade_end": False},
        ])


class TestAttachVisualPiecesScopeIsolation(unittest.TestCase):
    """Solo detection is per-scope: anywhere and holstein scopes don't
    cross-shadow each other."""

    def test_anywhere_solo_despite_holstein_overlap(self):
        """An anywhere layer can be solo even when a holstein layer is
        active in the same zone — they're independent scopes."""
        layers = [
            _layer(kind="circulation", scope="anywhere",
                   first=1500, last=1600, la=True,
                   left_pct=0.0, width_pct=25.0),
            _layer(kind="circulation", scope="holstein",
                   first=1500, last=1600,
                   left_pct=0.0, width_pct=25.0),
        ]
        zones = [
            _zone(1500, 1600, [0, 1], 0.0, 25.0),
        ]
        attach_visual_pieces({"b": layers}, {"b": zones})
        # L0 is alone in its scope → solo=True → fade_end=True
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0, "width_pct": 25.0,
             "show_fade_start": False, "show_fade_end": True},
        ])


class TestAttachVisualPiecesMergeAdjacent(unittest.TestCase):
    """Adjacent pieces with identical fade flags are merged."""

    def test_three_pieces_first_two_merge(self):
        """3 active zones for one layer: first two have no fade, third
        has fade_end. Merge collapses first two into one."""
        layers = [_layer(first=1500, last=1600, la=True,
                          left_pct=0.0, width_pct=25.0)]
        zones = [
            _zone(1500, 1519, [0], 0.0,  5.0),
            _zone(1520, 1579, [0, 1], 5.0,  15.0),  # this zone is non-solo
            _zone(1580, 1600, [0], 20.0, 5.25),
        ]
        # Add a sibling that overlaps middle zone only
        layers.append(_layer(first=1520, last=1579, la=False,
                              left_pct=5.0, width_pct=15.0))
        attach_visual_pieces({"b": layers}, {"b": zones})
        # L0 visual_pieces: [solo-left, overlap-middle, solo-right]
        #   solo-left: fade_start=F (fa=F), fade_end=F (touches_hi=F)
        #   overlap: fade_end=F (solo=F)
        #   solo-right: fade_end=T (solo=T, touches_hi=T, la=T)
        # First two have identical flags → merge into one [0.0, 20.0, F, F].
        # Then [20.0, 5.25, F, T] stays.
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0,  "width_pct": 20.0,
             "show_fade_start": False, "show_fade_end": False},
            {"left_pct": 20.0, "width_pct": 5.25,
             "show_fade_start": False, "show_fade_end": True},
        ])

    def test_all_same_flags_merge_to_one(self):
        """All zones produce the same flags → merge to single full-extent
        piece."""
        layers = [
            _layer(kind="status", first=1496, last=1533, la=True,
                   left_pct=0.0, width_pct=5.0),
            _layer(kind="circulation", first=1496, last=1600, la=True,
                   left_pct=0.0, width_pct=21.75),
        ]
        zones = [
            _zone(1496, 1532, [0, 1], 0.0,  4.75),
            _zone(1533, 1533, [0, 1], 4.75, 0.25),
            _zone(1534, 1600, [1],    5.0,  16.75),
        ]
        attach_visual_pieces({"b": layers}, {"b": zones})
        # status has la=T but sibling (circulation) overlaps both its
        # active zones → no solo → all pieces fade_end=F → merge into one.
        self.assertEqual(layers[0]["visual_pieces"], [
            {"left_pct": 0.0, "width_pct": 5.0,
             "show_fade_start": False, "show_fade_end": False},
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
