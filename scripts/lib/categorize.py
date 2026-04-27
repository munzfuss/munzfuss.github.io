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
    gedenk_coins: list[ComputedCoin] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (len(self.kurant_coins) + len(self.scheide_coins) + len(self.copper_coins)
                + len(self.tarif_coins) + len(self.tarif_deviant_coins)
                + len(self.gedenk_coins))

    @property
    def nonempty(self) -> bool:
        return self.total > 0

    @property
    def is_mixed(self) -> bool:
        """True when more than one category group has coins (needs subcat dividers)."""
        groups = [bool(self.kurant_coins), bool(self.scheide_coins), bool(self.copper_coins),
                  bool(self.tarif_coins), bool(self.tarif_deviant_coins)]
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
                elif cc.raw.kind == "gedenk":
                    pg.gedenk_coins.append(cc)
            
            sg.phases.append(pg)
        
        tree.fuesse.append(sg)

    return tree
