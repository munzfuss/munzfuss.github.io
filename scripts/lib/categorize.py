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

    @property
    def nonempty(self) -> bool:
        """True when at least one phase carries a coin. Catch-all
        Müntzfüße (e.g. `seed_unsorted`) that finish a classification
        pass empty are filtered out of the rendered tree on this
        signal — saves a confusing empty «Bulk-Seed (unsortiert)»
        section appearing on the page."""
        return any(p.nonempty for p in self.phases)

    @property
    def unique_nominals(self) -> int:
        """Count of distinct `nominal` strings across every coin in every
        phase of this Fuss. Used by the per-fuss collapsible stat-bar
        as a quick «how many denomination types belong to this Müntzfuß
        on this page» summary.

        Compares raw `coin.raw.nominal` strings — two coins with the
        same inscription (e.g. two KM variants of «1 Thaler Species»
        struck under different mintmasters) collapse to one nominal.
        Coins with no nominal string (defensive null check) are skipped.
        """
        seen: set[str] = set()
        for pg in self.phases:
            for coin_list in (
                pg.kurant_coins, pg.scheide_coins, pg.copper_coins,
                pg.tarif_coins, pg.tarif_deviant_coins,
                pg.tarif_subunit_coins, pg.gedenk_coins,
            ):
                for cc in coin_list:
                    nom = getattr(cc.raw, "nominal", None)
                    if nom:
                        seen.add(nom)
        return len(seen)


@dataclass
class LocationTree:
    """Full categorized tree for a location."""
    location: Location
    fuesse: list[FussGroup] = field(default_factory=list)



def categorize(
    location: Location,
    computed_coins: list[ComputedCoin],
    fuesse: dict[str, Fuss],
) -> LocationTree:
    """Group computed coins by (fuss, phase, kind) respecting the location's preferred ordering.

    The post-timeline fuss list is rendered in the order of `location.fuss_order`,
    re-sorted so it follows the (already-sorted) `location.timeline.bars` order.
    Fuss-ids that have a timeline bar are placed in bar-position; ids without a
    bar fall back to their `fuss_order` position (after the bar-tagged ones).
    Result: the optional `order` field on TimelineBar drives both the timeline
    and this list with a single source of truth — no need to keep `fuss_order`
    and `bars` manually synchronised.
    """

    # Index coins by (fuss, phase)
    from collections import defaultdict
    idx: dict[tuple[str, str], list[ComputedCoin]] = defaultdict(list)
    for cc in computed_coins:
        idx[(cc.raw.fuss, cc.raw.phase)].append(cc)

    tree = LocationTree(location=location)

    # Effective fuss order: sort `location.fuss_order` by timeline-bar
    # position (bars are already sorted by their `order` field via the
    # Timeline pydantic validator). Fuss without a corresponding bar
    # keep their `fuss_order` position relative to each other and are
    # placed AFTER the bar-tagged ones.
    bar_position = {}
    if location.timeline and location.timeline.bars:
        bar_position = {b.id: i for i, b in enumerate(location.timeline.bars)}

    def _fuss_sort_key(item):
        original_idx, fuss_id = item
        bar_idx = bar_position.get(fuss_id)
        if bar_idx is not None:
            return (0, bar_idx, original_idx)
        return (1, original_idx, 0)

    fuss_order_sorted = [fid for _, fid in sorted(enumerate(location.fuss_order), key=_fuss_sort_key)]

    for fuss_id in fuss_order_sorted:
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
                    if (cc.primary_fineness is not None and fuss_std
                            and cc.primary_fineness < fuss_std - 0.01):
                        pg.tarif_deviant_coins.append(cc)
                    else:
                        pg.tarif_coins.append(cc)
                elif cc.raw.kind == "tarif_subunit":
                    pg.tarif_subunit_coins.append(cc)
                elif cc.raw.kind == "gedenk":
                    pg.gedenk_coins.append(cc)
            
            sg.phases.append(pg)

        # Skip Müntzfüße that finish the classification pass with
        # zero coins anywhere (catch-all `seed_unsorted` after a
        # full reclassification, or any other Fuß that holds no
        # data on this page). Keeps stale empty sections out of
        # the rendered HTML; the phase definitions themselves stay
        # in `location.phases` as a safety-net for future imports.
        if not sg.nonempty:
            continue
        tree.fuesse.append(sg)

    return tree
