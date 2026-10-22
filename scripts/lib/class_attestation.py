"""Which of a final's citations and readings its own classes still attest.

WHY. Absorb rebuilds a final by UNIONING its stored values with its class(es)
in `data/v2/seed_unified/` (§9a: a final may hold citations no class re-attests
— dedup folds, curator additions, V1 carry-ins — and those must never be
dropped). The union has no inverse: when a seed LEAVES a class (a relocation
in `merge_decisions/_cross_entity.yml`, a split, a no_merge, a §9a re-fold),
everything it brought stays on the old final for good. Found 2026-10-22 on
`c-afd707d6` (Galster 155): 163 citations of Galster 36 — Numista 152921,
danskmoent fr/hg36.htm, 161 KMM korshvid specimens — that came in with KMM
533276 when 14ef43a relocated it from the G36 class.

THE RULE. A value on final F that no class of F attests is classified by who
DOES attest it:

    moved     a class held by ANOTHER final G attests it, and G carries it →
              the value lives on G; on F it is a stale leftover. Safe to drop
              from F: nothing leaves the render.
    orphan    only classes that reach no final attest it (excluded head seed,
              class never promoted). Dropping would remove it from the render
              entirely → kept, reported.
    unseeded  no class attests it at all: a curator citation, a fold, a V1
              carry-in, a thinned-away specimen. The §9a case → kept.

Only `moved` is ever dropped automatically. A final that holds `sources` in
`_curation_holds` keeps them all.

Identity of a source: (url, ref) — absorb's `_surgical_decontaminate` key
minus `type`. Not the url alone: one Bruun PDF or NGC price-guide url serves
many lots / coins. Identity of a reading (weight_rough_g / fineness /
diameter_mm): (value, source label), and only when the label names one record
(«KMM 642975»); a reading labelled with a bare source name («ucoin») is never
classified, because equal values under one generic label recur across
unrelated coins.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

V2 = Path(__file__).resolve().parents[2] / "data" / "v2"
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

READING_FIELDS = ("weight_rough_g", "fineness", "diameter_mm")


def source_key(s) -> tuple | None:
    """(url, ref). Not the url alone: one Bruun auction PDF, one NGC price
    guide, one danskmoent survey page is the url of many different lots /
    coins, told apart only by `ref`."""
    if not isinstance(s, dict):
        return None
    url, ref = s.get("url"), s.get("ref")
    if not (url or ref):
        return None
    return (str(url or ""), str(ref or ""))


def _specific(label) -> bool:
    """A reading label that names ONE record («KMM 642975», «Bruun Part II,
    lot 13145»), not a whole source («ucoin», «numista», «v1_curator»). Only
    such a reading can be traced to a seed: two coins can both weigh 28.893 g
    «ucoin» without either reading having moved."""
    return bool(label) and any(ch.isdigit() for ch in str(label))


def reading_key(x) -> tuple | None:
    if not isinstance(x, dict) or x.get("value") is None:
        return None
    if not _specific(x.get("source")):
        return None
    try:
        v = round(float(x["value"]), 4)
    except (TypeError, ValueError):
        v = str(x["value"])
    return (v, x.get("source"))


def _keys(coin: dict, fld: str) -> set:
    vals = coin.get(fld)
    if fld == "sources":
        return {k for s in (vals or []) if (k := source_key(s))}
    if not isinstance(vals, list):
        return set()
    return {k for x in vals if (k := reading_key(x))}


@dataclass
class AttestationIndex:
    """Class-level attestation over the whole tree."""
    class_keys: dict[str, dict[str, set]] = field(default_factory=dict)
    # {field: {key: {class ids attesting it}}}
    holders: dict[str, dict] = field(default_factory=dict)
    # class id → final id reaching it (one final per class)
    class_final: dict[str, str] = field(default_factory=dict)
    # final id → class ids it reaches
    final_classes: dict[str, set[str]] = field(default_factory=dict)
    # {field: {key: {final ids that carry it now}}}
    carriers: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def build(cls, unified_coins, final_coins) -> "AttestationIndex":
        """`unified_coins` / `final_coins`: iterables of coin dicts (all
        entities). Pure — no file access, so it is unit-testable."""
        idx = cls()
        fields = ("sources",) + READING_FIELDS
        idx.holders = {f: {} for f in fields}
        seed_class: dict[str, str] = {}
        for u in unified_coins:
            cid = u.get("id")
            if not cid:
                continue
            idx.class_keys[cid] = {f: _keys(u, f) for f in fields}
            for f in fields:
                for k in idx.class_keys[cid][f]:
                    idx.holders[f].setdefault(k, set()).add(cid)
            for m in u.get("composed_of") or []:
                seed_class[m] = cid
        idx.carriers = {f: {} for f in fields}
        for fc in final_coins:
            fid = fc.get("id")
            if not fid:
                continue
            for f in fields:
                for k in _keys(fc, f):
                    idx.carriers[f].setdefault(k, set()).add(fid)
            reached = set()
            for ref in fc.get("composed_of") or [fid]:
                if ref in idx.class_keys:
                    reached.add(ref)
                elif ref in seed_class:
                    reached.add(seed_class[ref])
            if fid in idx.class_keys:
                reached.add(fid)
            idx.final_classes[fid] = reached
            for c in reached:
                idx.class_final.setdefault(c, fid)
        return idx

    @classmethod
    def load(cls, root: Path | None = None) -> "AttestationIndex":
        v2 = root or V2

        def coins(sub):
            for p in sorted((v2 / sub).glob("*.yml")):
                doc = yaml.load(p.read_text(encoding="utf-8"), Loader=_LOADER) or {}
                for c in doc.get("coins") or []:
                    if isinstance(c, dict):
                        yield c
        return cls.build(list(coins("seed_unified")), list(coins("final")))

    def classify(self, fc: dict, fld: str) -> dict[str, list]:
        """{'moved': [(value, other final id)], 'orphan': [(value, class ids)],
        'unseeded': [value]} for the values of `fld` on final `fc` that none
        of its own classes attests."""
        out = {"moved": [], "orphan": [], "unseeded": []}
        fid = fc.get("id")
        own = self.final_classes.get(fid, set())
        attested = set()
        for c in own:
            attested |= self.class_keys.get(c, {}).get(fld, set())
        vals = fc.get(fld)
        if not isinstance(vals, list):
            return out
        keyf = source_key if fld == "sources" else reading_key
        for v in vals:
            k = keyf(v)
            if k is None or k in attested:
                continue
            others = self.holders.get(fld, {}).get(k, set()) - own
            homes = self.homes(fld, k, fid)
            if homes:
                out["moved"].append((v, homes[0]))
            elif others:
                out["orphan"].append((v, sorted(others)))
            else:
                out["unseeded"].append(v)
        return out


    def homes(self, fld: str, key, fid: str | None) -> list[str]:
        """Finals other than `fid` whose own class attests `key` AND that carry
        it now — where a value dropped from `fid` still lives."""
        carried = self.carriers.get(fld, {}).get(key, set())
        return sorted({self.class_final[c]
                       for c in self.holders.get(fld, {}).get(key, set())
                       if self.class_final.get(c) not in (None, fid)
                       and self.class_final[c] in carried})


def _held(fc: dict, fld: str) -> bool:
    h = fc.get("_curation_holds")
    return fld in (h.keys() if isinstance(h, dict) else (h or []))


def prune_moved(fc: dict, idx: AttestationIndex) -> dict[str, list]:
    """Drop from final `fc` (in place) every source / reading a class of
    ANOTHER final attests and none of its own does. Returns {field: [dropped
    (value, home final id)]}. Fields held in `_curation_holds` are untouched;
    `orphan` and `unseeded` values always stay (see module docstring)."""
    dropped: dict[str, list] = {}
    for fld in ("sources",) + READING_FIELDS:
        if _held(fc, fld):
            continue
        moved = idx.classify(fc, fld)["moved"]
        if not moved:
            continue
        gone = {id(v) for v, _ in moved}
        kept = [v for v in fc[fld] if id(v) not in gone]
        if kept:
            fc[fld] = kept
        else:
            fc.pop(fld, None)
        dropped[fld] = moved
    return dropped
