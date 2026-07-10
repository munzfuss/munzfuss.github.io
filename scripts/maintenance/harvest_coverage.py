#!/usr/bin/env python3
"""Harvest coverage report — full location/specimen coverage across ALL
sources, past harvests AND planned.

The harvest routine's §6 tables track per-BATCH / per-BUCKET progress for
the active fronts (ucoin periods, Numista buckets, IKMK query buckets) —
i.e. enumeration-target-vs-cached for what a routine is currently working.
They do NOT show, per political entity, how many specimens are actually
cached across every source ever harvested. This script fills that gap.

Three sections:

  A. ENTITY × SOURCE matrix — for the sources that have a V2 seed builder
     (bruun / galster / hede / numismaster / numista / ucoin), the
     `data/v2/seed/<source>/<entity>.yml` coin counts ARE the classified,
     in-scope, per-entity specimen coverage. This is the canonical
     "which locations + how many specimens" view.

  B. PER-SOURCE cache footprint — for EVERY cache source: how many record
     files are cached, how many specimens flow into V2 seeds, and (where a
     discovery manifest exists) how many were enumerated. Surfaces sources
     that are cached but NOT enumerated by entity (no seed builder) — IKMK
     today.

  C. IKMK detail — IKMK has no generic seed builder, so its cache is
     invisible to section A. Break it down by manifest-enumerated /
     actually-cached / gap, plus a rough by-country + by-era view (the
     IKMK record exposes mint COUNTRY, not city, so a precise per-entity
     split isn't possible without a real builder — see TODO).

Read-only. No writes. Run standalone or from the routine's §6.

Usage:
  .venv/bin/python scripts/maintenance/harvest_coverage.py
  .venv/bin/python scripts/maintenance/harvest_coverage.py --json
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import PROJECT_ROOT  # noqa: E402
from lib import yaml_io  # noqa: E402

CACHE = PROJECT_ROOT / "scripts" / "cache"
V2_SEED = PROJECT_ROOT / "data" / "v2" / "seed"

# Sources that have a V2 seed builder → their seed coin counts ARE the
# classified per-entity coverage.
SEED_SOURCES = ["bruun", "galster", "hede", "numismaster", "numista", "ucoin"]


# ----------------------------------------------------------------------
# Section A — entity × source classified matrix (from V2 seeds)
# ----------------------------------------------------------------------
def seed_matrix() -> tuple[dict, list, list]:
    mat: dict = defaultdict(lambda: defaultdict(int))
    ents: set = set()
    srcs: set = set()
    for f in V2_SEED.glob("*/*.yml"):
        src = f.parent.name
        ent = f.stem
        try:
            _, doc = yaml_io.load(f)
        except Exception:
            continue
        n = len((doc or {}).get("coins") or [])
        mat[ent][src] += n
        ents.add(ent)
        srcs.add(src)
    return mat, sorted(ents), sorted(srcs)


# ----------------------------------------------------------------------
# Section B — per-source cache record-file footprint
# ----------------------------------------------------------------------
def _count_numeric_json(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for p in d.glob("*.json") if p.stem[:1].isdigit())


def cache_footprint() -> dict:
    fp: dict = {}

    # ikmk — mds_id json files at top level
    fp["ikmk"] = {"cached": _count_numeric_json(CACHE / "ikmk")}

    # numista — top-level nid json + denmark_pre_1541 subdir
    fp["numista"] = {
        "cached": _count_numeric_json(CACHE / "numista")
        + _count_numeric_json(CACHE / "numista" / "denmark_pre_1541")
    }

    # ucoin — tid json files
    fp["ucoin"] = {"cached": _count_numeric_json(CACHE / "ucoin")}

    # numismaster — per-country subdirs of MC record files
    nm = 0
    for sub in ("denmark", "norway", "schleswig_holstein"):
        d = CACHE / "numismaster" / sub
        if d.exists():
            nm += sum(1 for p in d.glob("*.json") if p.name != "mc_index.json")
    fp["numismaster"] = {"cached": nm}

    # bruun — each lots/part*.json is a list (or {lots:[...]}) of lot dicts
    br = 0
    for p in (CACHE / "bruun" / "lots").glob("part*.json") if (CACHE / "bruun" / "lots").exists() else []:
        try:
            doc = json.loads(p.read_text())
            lots = doc if isinstance(doc, list) else (doc.get("lots") or [])
            br += len(lots)
        except Exception:
            pass
    fp["bruun"] = {"cached": br}

    # hede — htm pages (one per Hede catalogue page)
    fp["hede"] = {"cached": len(list((CACHE / "hede").glob("*.htm")))}

    # galster (under danskmoent/galster) — htm pages
    fp["galster"] = {"cached": len(list((CACHE / "danskmoent" / "galster").glob("*.htm")))}

    # reference / research caches (not per-specimen coin sources)
    for src, sub in (("rigsarkivet", "tk_160_diverse_moentsager"),
                     ("wilcke", "renaessancens_moent_1950")):
        d = CACHE / src / sub
        fp[src] = {"cached": len(list(d.rglob("*"))) if d.exists() else 0, "reference": True}

    return fp


# ----------------------------------------------------------------------
# Section C — IKMK detail (no seed builder → invisible to section A)
# ----------------------------------------------------------------------
def ikmk_detail() -> dict:
    man_path = CACHE / "ikmk" / "_manifest.json"
    if not man_path.exists():
        return {}
    man = json.loads(man_path.read_text())
    enumerated = set(str(x) for x in man.get("ids", []))
    oos = len(man.get("oos_excluded_mds_ids", []))
    country = Counter()
    era = Counter()
    cached = 0
    inscope = oos_modern = 0
    for mid in enumerated:
        p = CACHE / "ikmk" / f"{mid}.json"
        if not p.exists():
            continue
        cached += 1
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        mt = d.get("mint")
        c = mt[0].get("country_name_en") if isinstance(mt, list) and mt else None
        country[c or "(none)"] += 1
        pr = (d.get("period") or {}).get("name_en")
        era[pr or "(none)"] += 1
        try:
            ye = int(d.get("year_end") or d.get("year_start") or 0)
        except (TypeError, ValueError):
            ye = 0
        if 1481 <= ye <= 1914:
            inscope += 1
        elif ye > 1914:
            oos_modern += 1
    return {
        "enumerated": len(enumerated),
        "cached": cached,
        "gap_unfetched": len(enumerated) - cached,
        "oos_excluded": oos,
        "cached_inscope_1481_1914": inscope,
        "cached_oos_modern": oos_modern,
        "by_country": country.most_common(),
        "by_era": era.most_common(10),
    }


# ----------------------------------------------------------------------
def render(as_json: bool = False) -> None:
    mat, ents, msrcs = seed_matrix()
    fp = cache_footprint()
    ik = ikmk_detail()

    if as_json:
        print(json.dumps({
            "entity_source_matrix": {e: dict(mat[e]) for e in ents},
            "cache_footprint": fp,
            "ikmk_detail": ik,
        }, ensure_ascii=False, indent=2))
        return

    # ---- Section A ----
    print("### A. Entity × source — classified in-scope specimens (V2 seeds)\n")
    hdr = "| entity | " + " | ".join(msrcs) + " | TOTAL |"
    print(hdr)
    print("|" + "---|" * (len(msrcs) + 2))
    col_tot = Counter()
    grand = 0
    for e in sorted(ents, key=lambda x: -sum(mat[x].values())):
        cells = [mat[e][s] for s in msrcs]
        tot = sum(cells)
        grand += tot
        for s in msrcs:
            col_tot[s] += mat[e][s]
        print(f"| {e} | " + " | ".join(str(c) if c else "·" for c in cells) + f" | **{tot}** |")
    print(f"| **TOTAL** | " + " | ".join(f"**{col_tot[s]}**" for s in msrcs) + f" | **{grand}** |")
    print(f"\n_{len(ents)} entities · {grand} classified specimens across {len(msrcs)} seed-builder sources._\n")

    # ---- Section B ----
    print("### B. Per-source cache footprint (cached records vs seeded specimens)\n")
    print("| source | cached records | → seeded (V2) | status |")
    print("|---|---:|---:|---|")
    seeded_per_src = {s: sum(mat[e][s] for e in ents) for s in msrcs}
    for src in sorted(fp, key=lambda s: -fp[s]["cached"]):
        cached = fp[src]["cached"]
        if fp[src].get("reference"):
            status = "reference (not coin-specimen)"
            seeded = "—"
        elif src in seeded_per_src:
            seeded = seeded_per_src[src]
            status = "seed builder ✓"
        else:
            seeded = 0
            status = "**NO seed builder — uncovered by entity**"
        print(f"| {src} | {cached} | {seeded} | {status} |")
    print()

    # ---- Section C ----
    if ik:
        print("### C. IKMK detail (no seed builder — cache invisible to §A)\n")
        print(f"- **enumerated** (manifest in-scope ids): {ik['enumerated']}")
        print(f"- **actually cached** (record file present): {ik['cached']}  "
              f"→ **{ik['gap_unfetched']} enumerated-but-unfetched**")
        print(f"- cached in temporal scope (1481–1914): {ik['cached_inscope_1481_1914']}  ·  "
              f"cached OOS-modern (>1914): {ik['cached_oos_modern']}  ·  oos-excluded ids: {ik['oos_excluded']}")
        print("- by mint **country** (IKMK exposes country, not city — no per-entity split possible without a builder):")
        for c, n in ik["by_country"][:10]:
            print(f"    {c}: {n}")
        print("- by **era**:")
        for c, n in ik["by_era"]:
            print(f"    {c}: {n}")
        print()


if __name__ == "__main__":
    render(as_json="--json" in sys.argv)
