#!/usr/bin/env python3
"""Helper for the `v2-merge-coins` skill — resolve ids, build the §9.4 index
graph, and audit merge-decision member resolution.

The skill (SKILL.md) orchestrates the full merge/split flow; this script
provides the three mechanical checks that the two recurring failure modes
need:

  * RESOLVE   — map any id form (final/foundation id, seed_unified id, bare
                Hede/catalog code) to canonical SEED ids, so a merge_decision
                never references a non-seed id (the orphan root cause).
  * GRAPH     — collect every catalogue index (KM/Hede/Sieg/Lange/Dav/Schou/Fr)
                across the candidate seeds, so the §9.4 over-merge gate can see
                whether a SHARED base index unifies them or the merge rests on
                ruler+nominal+year alone (the gottorp over-merge trap).
  * AUDIT     — list all merge/no_merge members that do NOT resolve to a current
                seed id (the standing orphan detector; also the pre-commit guard).

  * SCAN      — read-only §9.4 over-merge detector: flag existing seed_unified
                entries whose members carry catalogue indices but share NO base
                (the gottorp class) — surfaces over-merges proactively instead
                of by chance.

Subcommands:
  merge_helper.py resolve <entity> <id> [<id> ...]
  merge_helper.py graph   <entity> <id> [<id> ...]      # ids resolved first
  merge_helper.py audit   [<entity>]                    # all entities if omitted; exit 1 if orphans
  merge_helper.py scan    <entity>                      # §9.4 over-merge candidates; exit 1 if any
"""
from __future__ import annotations
import sys, glob, os, re
import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "v2")
ROOT = os.path.normpath(ROOT)

CAT_KEYS = ["km", "hede", "sieg", "schou", "lange", "dav", "fr", "galster",
            "numista", "bruun_collection_id"]


def _load(path):
    try:
        d = yaml.safe_load(open(path)) or {}
    except FileNotFoundError:
        return []
    return (d.get("coins") if isinstance(d, dict) else d) or []


def load_seeds(entity):
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "seed", "*", f"{entity}.yml"))):
        for c in _load(f):
            if c.get("id"):
                out[c["id"]] = c
    return out


def load_layer(entity, layer):
    out = {}
    for c in _load(os.path.join(ROOT, layer, f"{entity}.yml")):
        if c.get("id"):
            out[c["id"]] = c
    return out


def resolve(entity, idstr, seeds=None, unified=None, final=None):
    """Return (list_of_seed_ids, kind). kind in
    {seed, seed_unified, final, catalog-prefix, UNRESOLVED}."""
    seeds = seeds if seeds is not None else load_seeds(entity)
    if idstr in seeds:
        return [idstr], "seed"
    unified = unified if unified is not None else load_layer(entity, "seed_unified")
    if idstr in unified:
        return list(unified[idstr].get("composed_of") or []), "seed_unified"
    final = final if final is not None else load_layer(entity, "final")
    if idstr in final:
        out = []
        for uid in final[idstr].get("composed_of") or []:
            if uid in unified:
                out.extend(unified[uid].get("composed_of") or [])
            elif uid in seeds:
                out.append(uid)
            else:
                out.append(uid)  # keep for visibility; caller flags non-seeds
        return out, "final"
    # bare base code: dk-hede-c4h112 -> dk-hede-c4h112a / c4h112b / c4h112ab
    pat = re.compile("^" + re.escape(idstr) + r"[a-z]+$")
    pref = sorted(sid for sid in seeds if pat.match(sid))
    if pref:
        return pref, "catalog-prefix"
    return [], "UNRESOLVED"


def cmd_resolve(entity, ids):
    seeds = load_seeds(entity)
    unified = load_layer(entity, "seed_unified")
    final = load_layer(entity, "final")
    bad = 0
    for i in ids:
        out, kind = resolve(entity, i, seeds, unified, final)
        # flag any resolved id that is itself not a current seed
        nonseed = [x for x in out if x not in seeds]
        tag = "✓" if (kind != "UNRESOLVED" and not nonseed) else "⚠"
        if tag == "⚠":
            bad += 1
        print(f"  {tag} {i}  [{kind}] -> {out or 'NOTHING'}"
              + (f"   (non-seed members: {nonseed})" if nonseed else ""))
    if bad:
        print(f"\n  {bad} input(s) did not resolve cleanly to seed ids — "
              "use the seed id(s) above in the merge_decision.")
    return 1 if bad else 0


def cmd_graph(entity, ids):
    seeds = load_seeds(entity)
    unified = load_layer(entity, "seed_unified")
    final = load_layer(entity, "final")
    # resolve every input to seeds first
    seed_ids = []
    for i in ids:
        out, _ = resolve(entity, i, seeds, unified, final)
        seed_ids.extend(out)
    seed_ids = list(dict.fromkeys(seed_ids))  # de-dup, keep order
    # collect indices
    print(f"  candidate seeds: {seed_ids}\n")
    index_owners = {}  # (key, value) -> [seed]
    for sid in seed_ids:
        c = seeds.get(sid)
        if not c:
            print(f"  ⚠ {sid} not a seed in {entity}")
            continue
        cat = c.get("catalog", {}) or {}
        rl = c.get("ruler"); nm = c.get("nominal"); yr = c.get("year_label")
        cells = []
        for k in CAT_KEYS:
            v = cat.get(k)
            if v in (None, "", []):
                continue
            vs = v if isinstance(v, list) else [v]
            for x in vs:
                cells.append(f"{k}={x}")
                index_owners.setdefault((k, str(x)), []).append(sid)
        print(f"  {sid}: {nm} · {rl} · {yr}")
        print(f"      {'  '.join(cells) or '(no catalogue index)'}")
    # §9.4 verdict hint: is there a base index shared by >1 candidate?
    print("\n  §9.4 shared-index check:")
    def base(k, v):
        # strip trailing sub-letters/sub-decimals: 121A->121, 305.2->305, 271d->271
        m = re.match(r"^([A-Za-z ]*?\d+)", v)
        return (k, m.group(1)) if m else (k, v)
    base_owners = {}
    for (k, v), owners in index_owners.items():
        bk = base(k, v)
        base_owners.setdefault(bk, set()).update(owners)
    shared = {bk: o for bk, o in base_owners.items() if len(o) > 1}
    if shared:
        print("    SHARED base index links candidates (merge plausible per §9.4):")
        for (k, b), o in sorted(shared.items()):
            print(f"      {k} base {b}  <- {sorted(o)}")
    else:
        print("    ⚠ NO shared base index across candidates.")
        print("    If the only commonality is ruler+nominal+year, this is the")
        print("    OVER-MERGE trap (gottorp/99444 class) — STOP and surface to the")
        print("    user before merging.")
    return 0


def _merger_resolves(mid, sids):
    """Mirror merge_seeds_cross_source._expand_member_against: a member resolves
    if it IS a seed id OR is a bare Hede code expanding to sub-letter seeds
    (dk-hede-c4h112 -> c4h112a/c4h112b — the intended curator shorthand the
    merger expands + groups). Final/V1 ids that expand to nothing (km-305-2-…)
    are real orphans. Keeping this identical to the merger stops audit drift."""
    if mid in sids:
        return True
    if re.search(r"\d$", mid):
        return any(k.startswith(mid) and k[len(mid):].isalpha() for k in sids)
    return False


def cmd_audit(entity):
    seeds_by_entity = {}
    entities = [entity] if entity else None
    files = sorted(glob.glob(os.path.join(ROOT, "merge_decisions", "*.yml")))
    orphans = []
    for f in files:
        ent = os.path.basename(f).replace(".yml", "")
        if ent.startswith("_"):
            continue  # _cross_entity handled separately
        if entities and ent not in entities:
            continue
        if ent not in seeds_by_entity:
            seeds_by_entity[ent] = set(load_seeds(ent))
        sids = seeds_by_entity[ent]
        doc = yaml.safe_load(open(f)) or {}
        for key in ("merges", "no_merges"):
            for blk in (doc.get(key) or []):
                for m in (blk.get("members") or []):
                    if not _merger_resolves(m, sids):
                        orphans.append((ent, key, m))
    if orphans:
        print(f"  ⚠ {len(orphans)} non-resolving merge-decision member(s):")
        for ent, key, m in orphans:
            print(f"      [{ent}] {key}: {m}")
        print("\n  Each MUST resolve to a current seed id. For a no_merges member"
              " this is\n  critical — a non-resolving block is INACTIVE (silent"
              " over-merge gap).\n  Re-point to the seed id (see `resolve`), or"
              " drop if redundant.")
        return 1
    print(f"  ✓ all merge-decision members resolve to seed ids"
          + (f" ({entity})" if entity else ""))
    return 0


def _base(k, v):
    """Catalogue base: strip sub-letters/sub-decimals — 121A->121, 305.2->305,
    271d->271, 'EC II 3690'->'EC II 3690' (kept; Dav has no sub-form here)."""
    s = str(v)
    m = re.match(r"^([A-Za-z ]*?\d+)", s)
    return m.group(1) if m else s


def cmd_scan(entity):
    """§9.4 over-merge scan: flag every multi-member seed_unified entry where
    >=2 members EACH carry a catalogue index but NO (catalogue, base) pair is
    shared by >=2 members — i.e. the merge rests on ruler+nominal+year alone
    (the gottorp KM33/KM35/Lange274b class). Distinct from a legit merge where
    one catalogue gives a shared base (Hede 121A+121B, or numista+numismaster
    both KM 305). Read-only; surfaces candidates for curator + the v2-merge-coins
    split flow. Exit 1 if any flagged."""
    from collections import Counter
    seeds = load_seeds(entity)
    unified = load_layer(entity, "seed_unified")
    # Curator force-`merges` declare a vetted identity (e.g. KM 41 ≡ Lange 274b);
    # those are intentional no-shared-base merges, not over-merges — skip an entry
    # whose members are fully covered by one force-merge group (expand bare Hede).
    force_groups = []
    decp = os.path.join(ROOT, "merge_decisions", f"{entity}.yml")
    if os.path.exists(decp):
        ddoc = yaml.safe_load(open(decp)) or {}
        for blk in (ddoc.get("merges") or []):
            grp = set()
            for m in (blk.get("members") or []):
                if m in seeds:
                    grp.add(m)
                elif re.search(r"\d$", m):
                    grp.update(k for k in seeds
                               if k.startswith(m) and k[len(m):].isalpha())
            if grp:
                force_groups.append(grp)
    flagged = []
    for uid, c in unified.items():
        members = c.get("composed_of") or []
        if len(members) < 2:
            continue
        mset = set(members)
        if any(mset <= g for g in force_groups):
            continue  # curator-vetted identity, not an over-merge
        per_key = {}  # key -> {member: set(bases)}
        for mid in members:
            cat = (seeds.get(mid, {}) or {}).get("catalog", {}) or {}
            for k in ("km", "hede", "sieg", "lange", "dav"):
                v = cat.get(k)
                if v in (None, "", []):
                    continue
                vs = v if isinstance(v, list) else [v]
                per_key.setdefault(k, {}).setdefault(mid, set()).update(
                    _base(k, x) for x in vs)
        indexed_members = {m for perm in per_key.values() for m in perm}
        if len(indexed_members) < 2:
            continue  # not enough indexed members to judge — leave it
        unifier = None
        for k, perm in per_key.items():
            cnt = Counter()
            for s in perm.values():
                cnt.update(s)
            if any(n >= 2 for n in cnt.values()):
                unifier = k
                break
        if unifier is None:
            detail = {k: {m: sorted(b) for m, b in perm.items()}
                      for k, perm in per_key.items()}
            flagged.append((uid, c.get("nominal"), c.get("ruler"), detail))
    if flagged:
        print(f"  ⚠ {len(flagged)} possible over-merge(s) in {entity} "
              "(no shared catalogue base across members):")
        for uid, nom, rul, detail in flagged:
            print(f"    {uid}  ({nom} · {rul})")
            for k, perm in detail.items():
                print(f"        {k}: " + "  ".join(
                    f"{m.split('-')[-1]}={'/'.join(b)}" for m, b in perm.items()))
        print("\n  Review each: if §9.4 confirms distinct coins, split via the "
              "v2-merge-coins skill.\n  False positives (legit no-index museum "
              "specimens merged in) are possible — judge per case.")
        return 1
    print(f"  ✓ no no-shared-base over-merges in {entity}")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    cmd = sys.argv[1]
    if cmd == "resolve":
        return cmd_resolve(sys.argv[2], sys.argv[3:])
    if cmd == "graph":
        return cmd_graph(sys.argv[2], sys.argv[3:])
    if cmd == "audit":
        return cmd_audit(sys.argv[2] if len(sys.argv) > 2 else None)
    if cmd == "scan":
        return cmd_scan(sys.argv[2])
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
