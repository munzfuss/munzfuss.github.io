#!/usr/bin/env python3
"""READ-ONLY: sort the values a `--no-self-union` absorb removed from the
finals into stale / legitimate / review, by evidence — stage C of
docs/plans/rebuild_final_from_members.md.

Input: the rows `final_diff_candidates.py --json` wrote (finals on disk vs
the finals at `--base`, the committed state the switch ran from). Evidence
per removed value:

    attest   who attests it at the base: a class of this final (then the
             switch should not have removed it — flagged), a class of ANOTHER
             final (moved / twin), an unfinaled class (orphan), nobody
             (unseeded)   — lib.class_attestation and the base seed_unified
    route    the commit after which THIS final first carried the value
             (pickaxe on the entity's final file, checked in the final's
             block), and the commit's kind: v1 (the bootstrap / restore
             commits), pipeline (absorb / re-flow / promote), edit
    why      a curator layer naming the field on one of the final's seeds:
             _source_errata, _curation_holds, _recorded_removals,
             _retracted_refs, exclusions

Buckets: S stale · L legitimate · H head-departed final · D diverged scalar
(the policy decides, by origin) · R review.

    .venv/bin/python scripts/maintenance/classify_self_union_diff.py CANDIDATES.json --json OUT.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib.class_attestation import READING_FIELDS, AttestationIndex, reading_key, source_key  # noqa: E402
from lib.final_derivation import items  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"

V1_ROUTE = {"214f991", "e210ed6", "e851d3f", "10850ab", "4831c21", "f1a9a4d",
            "1391cc9", "fb795a7", "e07029d", "7b10ca7", "c31c860", "66efdae",
            "9cb33bd", "b9e45f7"}
PIPELINE_RE = re.compile(r"absorb|re-flow|reflow|re-absorb|promote|re-merge|re-seed|"
                         r"fixed.point|regenerate|propagat|D49|legacy_id", re.I)
SCALARS = {"nominal", "ruler", "mintmaster", "issuing_entity", "fraction", "metal",
           "note", "verification_note", "inscription_obv", "inscription_rev",
           "year_first", "year_last", "year_label", "fuss", "phase", "kind"}
FLAGS = {"ruler_verified", "metal_verified", "fineness_verified", "weight_rough_verified",
         "diameter_mm_verified", "mint_verified", "verified", "year_verified"}


def _git(args: list[str]) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return r.stdout


def _coins(text: str) -> list[dict]:
    return [c for c in (yaml.load(text, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")]


def _blocks(commit: str, ent: str) -> dict[str, str]:
    t = _git(["show", f"{commit}:data/v2/final/{ent}.yml"])
    m = re.search(r"\ncoins:\n( *)- ", t)
    if not m:
        return {}
    pre = "\n" + m.group(1) + "- "
    out = {}
    for ch in t[m.start():].split(pre)[1:]:
        mm = re.search(r"^\s*id: (\S+)$", ch, re.M)
        if mm:
            out[mm.group(1)] = ch
    return out


def _load_decisions(seed_ids: set, thinned: dict) -> tuple[dict, set]:
    """Every curator merge / no_merge decision, members expanded as the merger
    expands them (bare Hede code → sub-letters, thinned specimen → its
    representative). Returns ({seed: forced-group id}, {frozenset(pair)}).
    A no_merge binds every pair across its members (the merger forbids the
    class from holding both, directly or transitively)."""
    from maintenance.merge_seeds_cross_source import _expand_member_against
    parent: dict[str, str] = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    no_merge: set = set()
    for p in sorted((V2 / "merge_decisions").glob("*.yml")):
        doc = yaml.load(p.read_text(), Loader=_L) or {}
        for m in doc.get("merges") or []:
            ids = [x for mid in (m.get("members") or []) for x in _expand_member_against(str(mid), seed_ids, thinned)]
            for x in ids[1:]:
                ra, rb = find(ids[0]), find(x)
                if ra != rb:
                    parent[rb] = ra
        for m in doc.get("no_merges") or []:
            ids = [x for mid in (m.get("members") or []) for x in _expand_member_against(str(mid), seed_ids, thinned)]
            for i, x in enumerate(ids):
                for y in ids[i + 1:]:
                    no_merge.add(frozenset((x, y)))
    groups = {s: find(s) for s in list(parent)}
    return groups, no_merge


def _num_core(v: str) -> str:
    m = re.match(r"^\s*([A-Za-z]{0,2}\d+)", str(v))
    return m.group(1).lower() if m else str(v).strip().lower()


def _loosely_covered(f: str, v: str, classes: list[dict]) -> bool:
    """Does a class of the final carry the value in ANOTHER form — the same
    url under another ref, the same catalogue number in another register
    form or sub-variant, the same reading under another label, the same
    year inside a range, any inscription / metal at all?"""
    if not classes:
        return False
    if f == "sources":
        m = re.match(r"\('([^']*)',", v)
        url = m.group(1) if m else ""
        return bool(url) and any(str(s.get("url") or "") == url
                                 for c in classes for s in (c.get("sources") or []) if isinstance(s, dict))
    if f in READING_FIELDS:
        m = re.match(r"\(([-\d.]+),", v)
        if not m:
            return False
        x = float(m.group(1))
        for c in classes:
            for r in (c.get(f) or []) if isinstance(c.get(f), list) else [c.get(f)]:
                val = r.get("value") if isinstance(r, dict) else r
                try:
                    if abs(float(val) - x) < 0.0051:
                        return True
                except (TypeError, ValueError):
                    pass
        return False
    if f == "catalog":
        m = re.match(r"\('([^']*)', '(.*)'\)$", v)
        if not m:
            return False
        reg, val = m.group(1), m.group(2).split(":")[-1]
        core = _num_core(val)
        for c in classes:
            cv = (c.get("catalog") or {}).get(reg)
            vals = list(cv.values()) if isinstance(cv, dict) else (cv if isinstance(cv, list) else [cv])
            flat = [y for x in vals for y in (x if isinstance(x, list) else [x])]
            if any(_num_core(str(y)) == core for y in flat if y not in (None, "")):
                return True
        return False
    if f == "year_ranges":
        try:
            y = int(v)
        except ValueError:
            return False
        for c in classes:
            a, b = c.get("year_first"), c.get("year_last")
            if isinstance(a, int) and isinstance(b, int) and a <= y <= b:
                return True
        return False
    if f in ("metal", "inscription_obv", "inscription_rev", "mint", "nominal", "ruler", "mintmaster"):
        return any(c.get(f) not in (None, "", []) for c in classes)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--json")
    ap.add_argument("--no-history", action="store_true", help="skip the git route (fast)")
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()
    rows = json.load(open(a.candidates))

    ents = sorted({r["entity"] for r in rows})
    base_final: dict[str, dict] = {}
    base_uni: dict[str, dict] = {}
    names: dict[str, set] = {}
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _coins(_git(["show", f"{a.base}:data/v2/final/{p.stem}.yml"])):
            base_final[c["id"]] = c
            names[c["id"]] = {c["id"], c.get("label"), c.get("legacy_id")} - {None}
    for p in sorted((V2 / "seed_unified").glob("*.yml")):
        for c in _coins(_git(["show", f"{a.base}:data/v2/seed_unified/{p.stem}.yml"])):
            base_uni[c["id"]] = c
    idx = AttestationIndex.build(list(base_uni.values()), list(base_final.values()))
    cur_final: dict[str, dict] = {}
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _coins(p.read_text()):
            cur_final[c["id"]] = c
    # seed id -> the final that holds its class (for the stale-V1-twin test)
    class_home: dict[str, str] = {}
    for fid, fc in base_final.items():
        for cid in fc.get("composed_of") or []:
            class_home.setdefault(cid, fid)
    seed_home: dict[str, str] = {}
    for u in base_uni.values():
        for s in u.get("composed_of") or []:
            if u["id"] in class_home:
                seed_home[s] = class_home[u["id"]]

    # Seed records (working tree is fine: seeds are not what the switch changes).
    seeds: dict[str, dict] = {}
    for p in sorted((V2 / "seed").glob("*/*.yml")):
        for c in _coins(p.read_text()):
            seeds[c["id"]] = c
    removals = yaml.load((V2 / "_recorded_removals.yml").read_text(), Loader=_L) if (V2 / "_recorded_removals.yml").exists() else []
    retracted = yaml.load((V2 / "_retracted_refs.yml").read_text(), Loader=_L) if (V2 / "_retracted_refs.yml").exists() else []
    removal_text = json.dumps(removals, ensure_ascii=False, default=str) + json.dumps(retracted, ensure_ascii=False, default=str)
    excluded: set[str] = set()
    for p in (V2 / "exclusions").glob("*.yml"):
        d = yaml.load(p.read_text(), Loader=_L) or {}
        for e in d.get("coins") or d.get("exclusions") or []:
            if isinstance(e, dict) and e.get("id"):
                excluded.add(e["id"])
            elif isinstance(e, str):
                excluded.add(e)

    # Head-departed finals (group H).
    thinned: dict[str, set] = defaultdict(set)
    for s in seeds.values():
        for t in s.get("_thinned_from") or []:
            thinned[s["id"]].add(t)
    # Curator decisions, expanded as the merger expands them.
    thinned_idx = {t: [rep] for rep, ts in thinned.items() for t in ts}
    forced_group, no_merge_pairs = _load_decisions(set(seeds), thinned_idx)

    def _seeds_of_final(fid: str) -> set:
        out = set()
        for cid in (base_final.get(fid) or {}).get("composed_of") or []:
            u = base_uni.get(cid)
            if u:
                for s in u.get("composed_of") or []:
                    out.add(s)
                    out |= thinned.get(s, set())
        if fid in seeds:
            out.add(fid)
        return out

    def _decision_between(fid_a: str, fid_b: str) -> str | None:
        sa, sb = _seeds_of_final(fid_a), _seeds_of_final(fid_b)
        if any(frozenset((x, y)) in no_merge_pairs for x in sa for y in sb):
            return "no_merge"
        ga = {forced_group[x] for x in sa if x in forced_group}
        gb = {forced_group[y] for y in sb if y in forced_group}
        if ga & gb:
            return "merge"
        return None
    head_departed: set[str] = set()
    for fid, fc in base_final.items():
        if fc.get("origin") != "promoted":
            continue
        head = str(fc.get("label") or "")[len("unified-"):]
        spec = set()
        for cid in fc.get("composed_of") or []:
            u = base_uni.get(cid)
            if u:
                for s in u.get("composed_of") or []:
                    spec.add(s)
                    spec |= thinned.get(s, set())
        if head and head not in spec:
            head_departed.add(fid)

    # Class-level value sets at the base, for the fields class_attestation does not cover.
    def _vals(c: dict, f: str) -> set:
        return items(f, c.get(f))

    other_class_vals: dict[tuple, set] = defaultdict(set)   # (field, value) -> finals whose class carries it
    for fid, fc in base_final.items():
        for cid in fc.get("composed_of") or []:
            u = base_uni.get(cid)
            if not u:
                continue
            for f in ("catalog", "mint", "year_ranges", "nominal", "ruler", "mintmaster",
                      "issuing_entity", "metal", "inscription_obv", "inscription_rev"):
                for v in _vals(u, f):
                    other_class_vals[(f, str(v))].add(fid)

    # Pair removed/added per (final, field) for relabel and scalar change detection.
    by_ff: dict[tuple, dict] = defaultdict(lambda: {"removed": [], "added": []})
    for r in rows:
        if r["field"] != "*coin*":
            by_ff[(r["entity"], r["final"], r["field"])][r["direction"]].append(r)

    # Git route: pickaxe per distinct (entity, value) for list-form fields only.
    route: dict[tuple, str | None] = {}
    if not a.no_history:
        keys = sorted({(r["entity"], r["final"], r["field"], r["value"]) for r in rows
                       if r["direction"] == "removed" and r["field"] in ("sources", *READING_FIELDS, "catalog")})

        def _needle(field: str, value: str) -> str:
            if field == "sources":
                m = re.match(r"\('([^']*)', '(.*)'\)$", value)
                return (m.group(1) or m.group(2)) if m else value
            if field in READING_FIELDS:
                m = re.match(r"\(([^,]*), '(.*)'\)$", value)
                return m.group(2) if m and m.group(2) else value
            m = re.match(r"\('([^']*)', '(.*)'\)$", value)
            return m.group(2) if m else value

        def _pick(k):
            ent, fid, field, value = k
            n = _needle(field, value)
            if not n:
                return k, []
            out = _git(["log", "--format=%H", "--reverse", "-S", n, "--", f"data/v2/final/{ent}.yml"]).split()
            return k, out

        with ThreadPoolExecutor(8) as ex:
            hits = dict(ex.map(_pick, keys))
        need: dict[tuple, set] = defaultdict(set)
        for (ent, fid, field, value), cs in hits.items():
            for c in cs:
                need[(c, ent)].add(fid)
        blk: dict[tuple, str | None] = {}
        for (c, ent) in sorted(need):
            b = _blocks(c, ent)
            for fid in need[(c, ent)]:
                blk[(c, fid)] = next((b[n] for n in names.get(fid, {fid}) if n in b), None)
        subj: dict[str, str] = {}
        for (ent, fid, field, value), cs in hits.items():
            n = _needle(field, value)
            first = next((c for c in cs if (t := blk.get((c, fid))) is not None and n in t), None)
            if first and first not in subj:
                subj[first] = _git(["log", "-1", "--format=%h %s", first]).strip()
            route[(ent, fid, field, value)] = subj.get(first) if first else None

    def _route_kind(s: str | None) -> str:
        if not s:
            return "unknown"
        h = s.split()[0]
        if any(h.startswith(v) or v.startswith(h) for v in V1_ROUTE):
            return "v1"
        return "pipeline" if PIPELINE_RE.search(s) else "edit"

    out_rows = []
    buckets: Counter = Counter()
    ex_by: dict[tuple, list] = defaultdict(list)
    for r in rows:
        if r["field"] == "*coin*":
            buckets[(r["direction"], "*coin*", r.get("origin") or "?")] += 1
            continue
        if r["direction"] != "removed":
            continue
        ent, fid, f, v = r["entity"], r["final"], r["field"], r["value"]
        fc = base_final.get(fid) or {}
        org = r.get("origin") or "?"
        ev: dict = {}
        # attest
        own_classes = [c for c in (fc.get("composed_of") or []) if c in base_uni]
        home = None
        if f == "sources" or f in READING_FIELDS:
            cl = idx.classify(fc, f)
            # a final with no live class attests nothing itself
            cause = "own" if own_classes else "unseeded"
            for c_name, vals in cl.items():
                for x in vals:
                    val = x[0] if isinstance(x, tuple) else x
                    k = source_key(val) if f == "sources" else reading_key(val)
                    if k is not None and str(k) == v:
                        cause = c_name
                        if isinstance(x, tuple) and isinstance(x[1], str):
                            home = x[1]
            ev["attest"] = cause
        elif f in ("catalog", "mint", "year_ranges", "nominal", "ruler", "mintmaster",
                   "issuing_entity", "metal", "inscription_obv", "inscription_rev"):
            holders = other_class_vals.get((f, v), set())
            ev["attest"] = "own" if fid in holders else ("moved" if holders else "unseeded")
            if holders and fid not in holders:
                home = sorted(holders)[0]
        else:
            ev["attest"] = "n/a"
        if home:
            ev["home"] = home
            d = _decision_between(fid, home)
            if d:
                ev["decision"] = d
        # loose coverage: the harvests carry the value in another form
        base_classes = [base_uni[c] for c in own_classes]
        ev["covered"] = _loosely_covered(f, v, base_classes)
        ev["memberless"] = not own_classes
        # relabel (sources): the same url still cited on the rebuilt final
        # under another ref text (added back, or already there)
        if f == "sources":
            m = re.match(r"\('([^']*)', '(.*)'\)$", v)
            url = m.group(1) if m else ""
            cur_urls = {str(s.get("url") or "") for s in ((cur_final.get(fid) or {}).get("sources") or [])
                        if isinstance(s, dict)}
            if url and url in cur_urls:
                ev["relabel"] = True
        # a memberless V1 foundation whose own id is a seed now living in a
        # class homed on ANOTHER final: a stale V1 twin of that coin
        if not own_classes:
            twin_seed = next((s for s in (fid, *(fid[len(p):] for p in ("hs-", "dk-", "hb-", "lu-") if fid.startswith(p)))
                              if s in seed_home), None)
            if twin_seed and seed_home[twin_seed] != fid:
                ev["twin_of"] = seed_home[twin_seed]
        # why
        why = []
        for sid in r.get("seeds") or []:
            s = seeds.get(sid)
            if not s:
                why.append(f"seed {sid} gone" + (" (excluded)" if sid in excluded else ""))
                continue
            for e in s.get("_source_errata") or []:
                if isinstance(e, dict) and e.get("field") in (f, f.rstrip("s")):
                    why.append(f"errata {sid}.{e.get('field')}")
            h = s.get("_curation_holds")
            hk = set(h.keys() if isinstance(h, dict) else (h or []))
            if f in hk:
                why.append(f"hold {sid}.{f}")
        fh = fc.get("_curation_holds")
        if f in set(fh.keys() if isinstance(fh, dict) else (fh or [])):
            why.append(f"hold {fid}.{f}")
        needle = v.split("'")[1] if v.startswith("('") and "'" in v[2:] else v
        if needle and len(needle) > 6 and needle in removal_text:
            why.append("recorded removal / retraction")
        ev["why"] = why
        ev["route"] = route.get((ent, fid, f, v))
        rk = _route_kind(ev["route"]) if (ent, fid, f, v) in route else "n/a"
        ev["route_kind"] = rk
        # bucket
        changed_scalar = f in SCALARS | FLAGS and by_ff[(ent, fid, f)]["added"]
        if fid in head_departed:
            b = "H"
        elif ev.get("twin_of"):
            b = "H-stale-v1-twin"
        elif ev["attest"] == "own":
            b = "FLAG-own-attested-but-removed"
        elif f in SCALARS | FLAGS:
            b = "D-promoted-class-wins" if org == "promoted" else ("D-foundation" if changed_scalar else "R")
        elif ev.get("relabel"):
            b = "S-relabel"
        elif any(w.startswith("recorded") for w in why):
            b = "S-recorded"
        elif ev.get("decision") == "merge":
            b = "R-merge-decision-not-applied"
        elif ev["attest"] in ("moved", "twin") and ev.get("decision") == "no_merge":
            b = "S-moved-no_merge"
        elif ev["attest"] == "moved" and rk in ("pipeline", "n/a", "unknown"):
            b = "S-moved"
        elif ev["attest"] == "moved" and rk == "v1":
            b = "R-v1-but-moved"
        elif ev["attest"] == "unseeded" and any(w.startswith(("hold", "errata")) for w in why):
            b = "L-curated"
        elif ev["attest"] == "twin":
            b = "R-twin"
        elif ev["attest"] == "orphan":
            b = "R-orphan"
        elif ev["attest"] == "unseeded" and org == "foundation":
            b = ("R-v1-memberless" if ev["memberless"]
                 else ("S-v1-covered" if ev["covered"] else "R-v1-uncovered"))
        elif ev["attest"] == "unseeded" and rk == "v1":
            b = "L-v1"
        elif ev["attest"] == "unseeded" and rk == "edit":
            b = "L-edit"
        elif ev["attest"] == "unseeded" and ev["covered"]:
            b = "S-covered"
        else:
            b = "R"
        buckets[(b, f, org)] += 1
        row = dict(r, **ev, bucket=b)
        out_rows.append(row)
        if len(ex_by[(b, f, org)]) < a.examples:
            ex_by[(b, f, org)].append(row)

    print(f"{'bucket':34} {'field':22} {'origin':10} {'n':>6}")
    for (b, f, org), n in sorted(buckets.items()):
        print(f"{b:34} {f:22} {org:10} {n:6}")
    print()
    for k in sorted(ex_by):
        for row in ex_by[k]:
            print(f"  {k[0]}/{k[1]}/{k[2]}: {row['final']} [{row['entity']}] {row['value'][:90]}"
                  f"  attest={row['attest']} route={row.get('route_kind')} why={row['why'][:2]}")
    if a.json:
        Path(a.json).write_text(json.dumps(out_rows, ensure_ascii=False, indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
