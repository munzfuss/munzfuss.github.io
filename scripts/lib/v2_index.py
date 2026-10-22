"""The one correct traversal of the three V2 id layers.

WHY THIS FILE EXISTS. The layers do not link the way they look like they do:

    seed id        ikmk-18297645, dk-hede-c4h2      stable (§9b)
    unified id     unified-<top-authority seed id>  renames on a merge decision
                   (D49: a NAME, kept as `label`; the stable handle is
                   `class_id` from data/v2/class_registry/, stage 2+)
    final id       follows the unified (until D49 stage 3: the head class id)

    seed_unified[].composed_of  →  SEED ids
    final[].composed_of         →  UNIFIED ids, and sometimes seed ids directly

The same field name means a different layer at each level. Every ad-hoc probe
that walks it by hand has to rediscover that, and the ones that get it wrong do
not fail — they return a confident, plausible, empty answer. Five such probes
in one session (2026-08-25) reported, in turn: «0 of 14 077 kmk seeds reach
final» and «0 of 166 coins relocated, 166 dead». Both were pure key mismatch;
the true answers were «nearly all» and «165 of 166».

`trace_coin.py` had the correct traversal all along, and CLAUDE.md §9b already
says to use it. It stayed unused because it lived inside a CLI script behind
five canned subcommands, so any question they did not answer was cheaper to
hand-roll than to reach — and 55 files across scripts/ now walk `composed_of`
themselves. This module makes the correct thing the cheap thing: one import,
and a lookup on the wrong layer RAISES instead of quietly missing.

    from lib.v2_index import V2Index
    idx = V2Index.load()
    idx.seed("ikmk-18297645")          # → placement, or KeyError
    idx.seed("unified-ikmk-18297645")  # → LayerError, naming the mistake
    idx.resolve(any_id)                # → ("seed"|"unified"|"final", record)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml

V2 = Path(__file__).resolve().parents[2] / "data" / "v2"


class LayerError(LookupError):
    """An id was looked up in a map keyed by a DIFFERENT layer.

    Raised instead of returning nothing, because the silent miss is the whole
    failure mode this module exists to stop: a probe that asks the wrong map
    gets an empty answer that looks like a finding.
    """


# libyaml when present: the whole V2 tree is ~100 MB of YAML, 96 s through the
# pure-Python loader and a fraction of that through the C one (same objects).
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _load(path: Path) -> dict:
    return yaml.load(path.read_text(), Loader=_LOADER) or {}


@dataclass
class Placement:
    """Where one seed sits across the three layers."""
    seed: str
    source: str
    seed_entity: str
    unified: str | None = None
    label: str | None = None      # the class's readable name (D49)
    final: str | None = None
    final_entity: str | None = None
    fuss: str | None = None
    phase: str | None = None
    sources: int | None = None

    @property
    def in_final(self) -> bool:
        return self.final is not None


@dataclass
class V2Index:
    """Seed-keyed placement index, plus reverse maps for the other two layers."""
    by_seed: dict[str, Placement] = field(default_factory=dict)
    unified_members: dict[str, set[str]] = field(default_factory=dict)
    final_members: dict[str, set[str]] = field(default_factory=dict)

    # ── construction ──────────────────────────────────────────────────────
    @classmethod
    def load(cls, root: Path | None = None) -> "V2Index":
        v2 = root or V2
        idx = cls()
        for src_dir in sorted((v2 / "seed").iterdir()):
            if not src_dir.is_dir():
                continue
            for p in sorted(src_dir.glob("*.yml")):
                for c in _load(p).get("coins") or []:
                    if c.get("id"):
                        idx.by_seed[c["id"]] = Placement(
                            seed=c["id"], source=src_dir.name, seed_entity=p.stem)

        for p in sorted((v2 / "seed_unified").glob("*.yml")):
            for c in _load(p).get("coins") or []:
                uid = c.get("id")
                if not uid:
                    continue
                members = set(c.get("composed_of") or [])
                idx.unified_members[uid] = members
                for m in members:
                    if m in idx.by_seed:
                        idx.by_seed[m].unified = uid
                        idx.by_seed[m].label = c.get("label")

        # `final[].composed_of` holds UNIFIED ids — and, for older entries,
        # sometimes a seed id directly. Both shapes are resolved here so no
        # caller has to know which it got.
        for p in sorted((v2 / "final").glob("*.yml")):
            for c in _load(p).get("coins") or []:
                fid = c.get("id")
                if not fid:
                    continue
                reached: set[str] = set()
                for ref in c.get("composed_of") or []:
                    if ref in idx.unified_members:
                        reached |= idx.unified_members[ref]
                    elif ref in idx.by_seed:
                        reached.add(ref)
                idx.final_members[fid] = reached
                for s in reached:
                    pl = idx.by_seed[s]
                    pl.final, pl.final_entity = fid, p.stem
                    pl.fuss, pl.phase = c.get("fuss"), c.get("phase")
                    pl.sources = len(c.get("sources") or [])
        return idx

    # ── lookups that refuse the wrong layer ───────────────────────────────
    def seed(self, seed_id: str) -> Placement:
        """Placement of a SEED id. Raises rather than missing quietly."""
        if seed_id not in self.by_seed:
            if seed_id in self.unified_members or seed_id in self.final_members:
                raise LayerError(
                    f"{seed_id!r} is a unified/final id, not a seed id — "
                    f"use .by_unified()/.by_final(), or .resolve() if unsure. "
                    f"(This is the mismatch that returns an empty answer when "
                    f"hand-rolled; see the module docstring.)")
            raise KeyError(f"{seed_id!r} is in no seed file")
        return self.by_seed[seed_id]

    def by_unified(self, unified_id: str) -> list[Placement]:
        """Every seed composing a UNIFIED class."""
        if unified_id not in self.unified_members:
            if unified_id in self.by_seed:
                raise LayerError(
                    f"{unified_id!r} is a seed id, not a unified id — use .seed()")
            raise KeyError(f"{unified_id!r} is in no seed_unified file")
        return [self.by_seed[m] for m in sorted(self.unified_members[unified_id])
                if m in self.by_seed]

    def by_final(self, final_id: str) -> list[Placement]:
        """Every seed reaching a FINAL entry, through unified or directly."""
        if final_id not in self.final_members:
            raise KeyError(f"{final_id!r} is in no final file")
        return [self.by_seed[m] for m in sorted(self.final_members[final_id])
                if m in self.by_seed]

    def resolve(self, any_id: str) -> tuple[str, Any]:
        """(layer, record) for an id of unknown layer. The safe entry point."""
        if any_id in self.by_seed:
            return "seed", self.by_seed[any_id]
        if any_id in self.unified_members:
            return "unified", self.by_unified(any_id)
        if any_id in self.final_members:
            return "final", self.by_final(any_id)
        raise KeyError(f"{any_id!r} appears in no V2 layer")

    # ── convenience ───────────────────────────────────────────────────────
    def seeds(self, *, source: str | None = None,
              entity: str | None = None) -> Iterator[Placement]:
        for pl in self.by_seed.values():
            if source and pl.source != source:
                continue
            if entity and pl.seed_entity != entity:
                continue
            yield pl

    def __len__(self) -> int:
        return len(self.by_seed)
