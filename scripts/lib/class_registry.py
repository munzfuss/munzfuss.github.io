"""Class registry — the one immutable id of a cross-source class (D49).

WHY. A seed_unified class is named `unified-<top-authority member>`, i.e. after
its composition, so the name changes whenever a higher-authority member joins,
a §9a fold is re-cut or the class splits; every consumer keyed on it (final
ids, classification decisions, verify_reflow) then loses the coin. The
registry gives each class an OPAQUE id that never changes, and recognises the
merger's freshly computed partition as the classes it already knows.

THE MODEL (V2_DECISIONS D49 + addendum). The merger recomputes the partition
of all seeds on every run; nobody moves members by hand. So the registry does
not hold membership — it RECOGNISES: for each class the merger emits, which
existing record is it?

  1. Membership is counted in SPECIMENS: the class's seed ids plus every id in
     a representative's `_thinned_from`. A fold re-cut is thereby invisible.
  2. Candidates are the active records (any entity) whose specimens intersect
     the class. One candidate inherits. Several (classes merged): the one with
     the LARGEST intersection inherits, ties → the OLDER record (`created`),
     then the smaller id; the others are retired with `merged_into`. One record
     claimed by several classes (a split): the class with the largest
     intersection keeps the id, the others get new ids, the record notes
     `split_into`. No candidate → new record.
  3. A record nobody inherits is retired, never deleted (`merged_into` /
     `split_into` keep resolving; `trace_coin` keeps the lineage).
  4. Idempotent: the same partition twice → no change.

ID FORM: `c-<8 hex>` = sha1 of the sorted founding specimen set. No entity
(a relocated class keeps its id and nothing in it lies), no date
(a bootstrap is reproducible). A collision with ANY existing id, active or
retired, gets a `-2`, `-3` suffix.

STORAGE: one shard per entity, `data/v2/class_registry/<entity>.yml`, written
only by the merger (and the one-off bootstrap). `inherit` runs ONCE per merger
invocation over every processed entity, after the partition loop and before
any shard is written — never per entity inside the loop, which would make the
result depend on entity order.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

V2 = Path(__file__).resolve().parents[2] / "data" / "v2"
REGISTRY_DIR = V2 / "class_registry"

ACTIVE = "active"
RETIRED = "retired"


@dataclass
class Record:
    id: str
    entity: str
    members: list[str]
    created: str
    status: str = ACTIVE
    label: str | None = None
    legacy_id: str | None = None
    merged_into: str | None = None
    split_into: list[str] = field(default_factory=list)
    retired: str | None = None   # date

    def to_yaml(self) -> dict:
        out: dict = {"id": self.id, "status": self.status, "created": self.created}
        if self.label:
            out["label"] = self.label
        if self.legacy_id:
            out["legacy_id"] = self.legacy_id
        if self.merged_into:
            out["merged_into"] = self.merged_into
        if self.split_into:
            out["split_into"] = sorted(self.split_into)
        if self.retired:
            out["retired"] = self.retired
        out["members"] = sorted(self.members)
        return out

    @classmethod
    def from_yaml(cls, entity: str, d: dict) -> "Record":
        return cls(id=str(d["id"]), entity=entity,
                   members=[str(m) for m in (d.get("members") or [])],
                   created=str(d.get("created") or ""), status=d.get("status") or ACTIVE,
                   label=d.get("label"), legacy_id=d.get("legacy_id"),
                   merged_into=d.get("merged_into"),
                   split_into=[str(x) for x in (d.get("split_into") or [])],
                   retired=str(d["retired"]) if d.get("retired") else None)


def make_id(founding: Iterable[str], taken: set[str] | None = None) -> str:
    base = "c-" + hashlib.sha1(",".join(sorted(founding)).encode("utf-8")).hexdigest()[:8]
    if not taken or base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def specimens_of(seed_ids: Iterable[str], rep_to_dead: dict[str, list[str]]) -> frozenset[str]:
    """Seeds ∪ the specimens each representative absorbed by §9a thinning.
    `rep_to_dead` = {representative seed id: [its `_thinned_from`]} — the
    inverse of `merge_seeds_cross_source.build_thinned_index`."""
    out: set[str] = set()
    for s in seed_ids:
        out.add(s)
        out.update(rep_to_dead.get(s, ()))
    return frozenset(out)


def rep_to_dead_index(coins: Iterable[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for c in coins:
        if c.get("id") and c.get("_thinned_from"):
            out[c["id"]] = [str(x) for x in c["_thinned_from"]]
    return out


class Registry:
    def __init__(self) -> None:
        self.records: dict[str, Record] = {}
        self.touched: set[str] = set()      # entities whose shard changed

    # ---- I/O -------------------------------------------------------------
    @classmethod
    def load_all(cls, root: Path = REGISTRY_DIR) -> "Registry":
        import yaml
        reg = cls()
        if root.exists():
            for f in sorted(root.glob("*.yml")):
                d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                for r in d.get("classes") or []:
                    rec = Record.from_yaml(f.stem, r)
                    if rec.id in reg.records:
                        raise ValueError(f"class id {rec.id} appears in two shards "
                                         f"({reg.records[rec.id].entity}, {f.stem})")
                    reg.records[rec.id] = rec
        return reg

    def shard(self, entity: str) -> list[Record]:
        return sorted((r for r in self.records.values() if r.entity == entity),
                      key=lambda r: (r.status != ACTIVE, r.id))

    def emit(self, entity: str) -> str:
        from lib.yaml_io import dump_v2_canonical
        recs = self.shard(entity)
        payload = {"id": entity,
                   "classes": [r.to_yaml() for r in recs]}
        header = (f"# V2 class registry for political entity `{entity}` (D49).\n"
                  f"# Written by scripts/maintenance/merge_seeds_cross_source.py — never by hand.\n"
                  f"# One record per cross-source class: an opaque immutable id, the class's\n"
                  f"# specimens (seed ids incl. those folded by §9a thinning), its lineage\n"
                  f"# (merged_into / split_into) and the mutable `label` (the unified id).\n"
                  f"# {sum(r.status == ACTIVE for r in recs)} active, "
                  f"{sum(r.status != ACTIVE for r in recs)} retired.\n\n")
        return header + dump_v2_canonical(payload)

    def save(self, root: Path = REGISTRY_DIR, entities: Iterable[str] | None = None) -> list[str]:
        root.mkdir(parents=True, exist_ok=True)
        ents = set(entities) if entities is not None else self.touched
        written = []
        for ent in sorted(ents):
            text = self.emit(ent)
            path = root / f"{ent}.yml"
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                path.write_text(text, encoding="utf-8")
                written.append(ent)
        return written

    # ---- queries ---------------------------------------------------------
    def active(self) -> Iterable[Record]:
        return (r for r in self.records.values() if r.status == ACTIVE)

    def holders(self) -> dict[str, list[str]]:
        """{specimen → [active record ids holding it]} (normally one)."""
        out: dict[str, list[str]] = {}
        for r in self.active():
            for m in r.members:
                out.setdefault(m, []).append(r.id)
        return out

    def resolve(self, rid: str) -> Record | None:
        """Follow `merged_into` to the active record."""
        seen = set()
        while rid in self.records and rid not in seen:
            seen.add(rid)
            r = self.records[rid]
            if r.status == ACTIVE or not r.merged_into:
                return r
            rid = r.merged_into
        return None

    # ---- the recognition rule -------------------------------------------
    def inherit(self, partitions: dict[str, list[tuple[frozenset[str], str]]],
                today: str | None = None) -> dict[tuple[str, frozenset[str]], str]:
        """Recognise the merger's partition. `partitions` = {entity: [(specimens,
        label)]} for every entity processed in this run. Returns {(entity,
        specimens): record id}. Mutates the registry; `self.touched` lists the
        entities whose shard changed (a relocation touches two)."""
        today = today or date.today().isoformat()
        holders = self.holders()
        # 1. best candidate per class
        best: dict[tuple[str, frozenset[str]], str | None] = {}
        overlap: dict[tuple[str, frozenset[str]], dict[str, int]] = {}
        for ent, classes in partitions.items():
            for spec, label in classes:
                key = (ent, spec)
                counts: dict[str, int] = {}
                for s in spec:
                    for rid in holders.get(s, ()):
                        counts[rid] = counts.get(rid, 0) + 1
                overlap[key] = counts
                if counts:
                    best[key] = min(counts, key=lambda rid: (
                        -counts[rid], self.records[rid].created, rid))
                else:
                    best[key] = None
        # 2. one record claimed by several classes → the largest keeps it
        claims: dict[str, list[tuple[str, frozenset[str]]]] = {}
        for key, rid in best.items():
            if rid:
                claims.setdefault(rid, []).append(key)
        assigned: dict[tuple[str, frozenset[str]], str] = {}
        taken = set(self.records)
        labels = {key: label for ent, cl in partitions.items() for spec, label in cl
                  for key in [(ent, spec)]}
        for rid, keys in claims.items():
            keys.sort(key=lambda k: (-overlap[k][rid], -len(k[1]), labels[k], k[0]))
            keeper, *others = keys
            assigned[keeper] = rid
            rec = self.records[rid]
            for k in others:
                nid = make_id(k[1], taken)
                taken.add(nid)
                self.records[nid] = Record(id=nid, entity=k[0], members=sorted(k[1]),
                                           created=today, label=labels[k])
                assigned[k] = nid
                rec.split_into = sorted(set(rec.split_into) | {nid})
                self.touched.add(k[0])
        # 3. classes with no candidate → new
        for key, rid in best.items():
            if rid is None:
                nid = make_id(key[1], taken)
                taken.add(nid)
                self.records[nid] = Record(id=nid, entity=key[0], members=sorted(key[1]),
                                           created=today, label=labels[key])
                assigned[key] = nid
                self.touched.add(key[0])
        # 4. update inheriting records; retire the candidates nobody inherited
        inherited = set(assigned.values())
        for key, rid in assigned.items():
            rec = self.records[rid]
            ent, spec = key
            new_members = sorted(spec)
            if (rec.members != new_members or rec.label != labels[key]
                    or rec.entity != ent or rec.status != ACTIVE):
                self.touched.update({rec.entity, ent})
                rec.members, rec.label, rec.status = new_members, labels[key], ACTIVE
                rec.entity = ent
                rec.merged_into, rec.retired = None, None
        processed = set(partitions)
        for key, counts in overlap.items():
            for rid in counts:
                if rid in inherited:
                    continue
                rec = self.records[rid]
                if rec.status != ACTIVE:
                    continue
                # the record's members went to the classes that overlap it;
                # merged_into = the record that took most of them
                share: dict[str, int] = {}
                for k2, c2 in overlap.items():
                    if rid in c2:
                        share[assigned[k2]] = share.get(assigned[k2], 0) + c2[rid]
                rec.status, rec.retired = RETIRED, today
                rec.merged_into = max(share, key=lambda x: (share[x], x))
                self.touched.add(rec.entity)
        # 5. an active record of a PROCESSED entity that no class touched at
        #    all (all its specimens vanished from the seeds) is retired too
        touched_ids = {rid for c in overlap.values() for rid in c} | inherited
        for rec in list(self.active()):
            if rec.entity in processed and rec.id not in touched_ids:
                rec.status, rec.retired = RETIRED, today
                self.touched.add(rec.entity)
        return assigned
