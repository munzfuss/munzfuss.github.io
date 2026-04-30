"""
Layer B → C: group computed coins into the render-ready tree.

Produces nested structure: location → fuss → phase → kind → coins (sorted).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .compute import ComputedCoin
from .schema import Location, Phase, Fuss


@dataclass
class PhaseGroup:
    """A phase within a fuss, with its categorized coins."""
    phase: Phase
    kurant_coins: list[ComputedCoin] = field(default_factory=list)
    scheide_coins: list[ComputedCoin] = field(default_factory=list)   # silver/billon scheidemünzen (have computable Δ)
    copper_coins: list[ComputedCoin] = field(default_factory=list)    # pure copper tokens (no silver, Δ undefined)
    tarif_coins: list[ComputedCoin] = field(default_factory=list)     # standard tariff coins (fineness ≈ fuss standard)
    tarif_deviant_coins: list[ComputedCoin] = field(default_factory=list)
    # ↑ Tariff coins whose fineness is materially below the fuss standard
    # (Hebræermønt 1645 .593 vs Kronemønt-Standard .671) — a "Scheidemünze
    # within the Tarifmünze": same nominal tariff, additional silver debasement
    # on top. Rendered in its own sub-block analogous to Scheidemünze.
    tarif_subunit_coins: list[ComputedCoin] = field(default_factory=list)
    # ↑ Tariff subdivision coins under the same tariff regime — same fineness
    # as the parent Tarifmünze, but per-piece silver content systematically
    # exceeds the strict subdivision proportion (e.g. Kroneskilling 1619-1621
    # at .859 carry up to ~2× the silver of strict 1/96-Krone). Rendered as
    # its own sub-block, contrasting with the at-tariff main coins.
    gedenk_coins: list[ComputedCoin] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (len(self.kurant_coins) + len(self.scheide_coins) + len(self.copper_coins)
                + len(self.tarif_coins) + len(self.tarif_deviant_coins)
                + len(self.tarif_subunit_coins) + len(self.gedenk_coins))

    @property
    def nonempty(self) -> bool:
        return self.total > 0

    @property
    def is_mixed(self) -> bool:
        """True when more than one category group has coins (needs subcat dividers)."""
        groups = [bool(self.kurant_coins), bool(self.scheide_coins), bool(self.copper_coins),
                  bool(self.tarif_coins), bool(self.tarif_deviant_coins),
                  bool(self.tarif_subunit_coins)]
        return sum(groups) > 1


@dataclass
class FussGroup:
    """A fuss with its phases and coins."""
    fuss: Fuss
    phases: list[PhaseGroup] = field(default_factory=list)

    @property
    def nonempty_phases(self) -> list[PhaseGroup]:
        return [p for p in self.phases if p.nonempty]


@dataclass
class LocationTree:
    """Full categorized tree for a location."""
    location: Location
    fuesse: list[FussGroup] = field(default_factory=list)


def compute_bar_layers(
    bars: list,
    fuesse: dict,
    tl_year_from: int,
    tl_year_to: int,
) -> dict[str, list[dict]]:
    """For each timeline bar, derive the up-to-six period × scope layers
    (mint × {anywhere, holstein}, status × {anywhere, holstein},
    circulation × {anywhere, holstein}) from its `events` block, falling
    back to the matching Fuss in `fuesse` when the bar itself doesn't carry
    events. Returns a dict `bar_id → [layer, ...]` sorted by length DESC
    (longest first → bottom of the visual stack), with `left_pct` /
    `width_pct` pre-computed for the timeline track.

    A layer has shape:
      {
        "kind":      "mint" | "status" | "circulation",
        "scope":     "anywhere" | "holstein",
        "first":     int,
        "last":      int,
        "length":    int,                 # last - first
        "left_pct":  float (0..100),
        "width_pct": float (0..100),
      }

    Layers with first/last == None (e.g. holstein-side of a Copenhagen-only
    standard, or no-local-mint stopes like Vereinsthaler in H) are skipped
    — the result only contains layers that have a real year range.
    """
    out: dict[str, list[dict]] = {}
    tl_span = tl_year_to - tl_year_from
    if tl_span <= 0:
        return out

    for bar in bars:
        events = getattr(bar, "events", None)
        if events is None and bar.id in fuesse:
            events = getattr(fuesse[bar.id], "events", None)
        if events is None:
            out[bar.id] = []
            continue

        layers: list[dict] = []
        anywhere_label = getattr(events, "anywhere_label", None)

        def _add(kind, scope, start_event, end_event):
            """Pull (year, approx) for one scope from a (start, end) event pair."""
            if start_event is None or end_event is None:
                return
            first = getattr(start_event, scope)
            last = getattr(end_event, scope)
            if first is None or last is None:
                return
            first_approx = getattr(start_event, f"approx_{scope}", False)
            last_approx = getattr(end_event, f"approx_{scope}", False)
            layers.append({
                "kind": kind,
                "scope": scope,
                "first": first,
                "last": last,
                "length": last - first,
                "first_approx": first_approx,
                "last_approx": last_approx,
                "anywhere_label": anywhere_label,  # I18nText | None — per-stope label
            })

        # mint = [first_mint, last_mint]
        fm, lm = events.first_mint, events.last_mint
        for scope in ("anywhere", "holstein"):
            _add("mint", scope, fm, lm)

        # status = [first_adoption, std_end]
        fa, se = events.first_adoption, events.std_end
        for scope in ("anywhere", "holstein"):
            _add("status", scope, fa, se)

        # circulation = [first_adoption, demonetisation]
        de_ = events.demonetisation
        for scope in ("anywhere", "holstein"):
            _add("circulation", scope, fa, de_)

        # Sort by length DESC so the longest layer is rendered first
        # (DOM order = bottom of stack); the shortest paints last (= on top).
        layers.sort(key=lambda l: l["length"], reverse=True)

        for l in layers:
            raw_left  = (l["first"] - tl_year_from) / tl_span * 100
            raw_right = (l["last"]  - tl_year_from) / tl_span * 100
            cl = max(raw_left, 0.0)
            cr = min(raw_right, 100.0)
            l["left_pct"]  = round(cl, 2)
            l["width_pct"] = round(cr - cl, 2)

        out[bar.id] = layers

    return out


def categorize(
    location: Location,
    computed_coins: list[ComputedCoin],
    fuesse: dict[str, Fuss],
) -> LocationTree:
    """Group computed coins by (fuss, phase, kind) respecting the location's preferred ordering."""
    
    # Index coins by (fuss, phase)
    from collections import defaultdict
    idx: dict[tuple[str, str], list[ComputedCoin]] = defaultdict(list)
    for cc in computed_coins:
        idx[(cc.raw.fuss, cc.raw.phase)].append(cc)

    tree = LocationTree(location=location)

    for fuss_id in location.fuss_order:
        if fuss_id not in fuesse:
            continue
        if fuss_id not in location.phases:
            continue
        
        sg = FussGroup(fuss=fuesse[fuss_id])
        
        for phase in location.phases[fuss_id]:
            pg = PhaseGroup(phase=phase)
            coins_in_phase = idx.get((fuss_id, phase.id), [])
            coins_in_phase.sort(key=lambda c: (c.raw.year_first, c.raw.id))
            
            for cc in coins_in_phase:
                if cc.raw.kind == "kurant":
                    pg.kurant_coins.append(cc)
                elif cc.raw.kind == "scheide":
                    # Pure copper tokens (no precious metal content) get their own sub-group
                    # since Δ is undefined and the economic logic differs from billon scheidemünzen.
                    if cc.raw.metal in ("copper", "bronze", "brass"):
                        pg.copper_coins.append(cc)
                    else:
                        pg.scheide_coins.append(cc)
                elif cc.raw.kind == "tarif":
                    # Split tariff coins by whether the fineness materially
                    # undercuts the fuss standard. Threshold of 1 % keeps
                    # rounding noise out of the «deviant» bucket; only real
                    # debasement (e.g. Hebræermønt .593 vs .671 = 11.6 % gap)
                    # is broken out into its own sub-table.
                    fuss_std = cc.fuss.fineness_standard
                    if (cc.raw.fineness is not None and fuss_std
                            and cc.raw.fineness < fuss_std - 0.01):
                        pg.tarif_deviant_coins.append(cc)
                    else:
                        pg.tarif_coins.append(cc)
                elif cc.raw.kind == "tarif_subunit":
                    pg.tarif_subunit_coins.append(cc)
                elif cc.raw.kind == "gedenk":
                    pg.gedenk_coins.append(cc)
            
            sg.phases.append(pg)
        
        tree.fuesse.append(sg)

    return tree
