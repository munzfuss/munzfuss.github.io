"""Group the IKMK Berlin cache by issuer (title prefix) and emit an index.

Reads every JSON file under ``scripts/cache/ikmk/``, buckets by the
title-prefix string IKMK uses to denote the issuing entity (the part
before the first ``:`` in ``title``), and writes:

* ``scripts/cache/ikmk/_index_by_issuer.json`` — machine-readable
  index. Each issuer entry carries record IDs split into in-scope /
  out-of-scope buckets, year bounds, material/mint distributions, a
  handful of sample titles, and a coarse mapping to the project's
  location files when one exists.
* ``scripts/cache/ikmk/_index_summary.md`` — human-readable digest
  of the same data, useful for picking which issuers to research
  next.

The script is idempotent: re-run after expanding the cache to refresh
both files. No network access; reads existing cache only.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "cache" / "ikmk"
INDEX_JSON = CACHE_DIR / "_index_by_issuer.json"
INDEX_MD = CACHE_DIR / "_index_summary.md"

# Project window. Records with any year overlap into this window are
# "in scope".
SCOPE_YEAR_MIN = 1566
SCOPE_YEAR_MAX = 1914

# Hand-curated mapping issuer-prefix → project-location id.
# Multiple prefixes may map to the same location (e.g. all
# Schleswig-Holstein-* sub-duchies → schleswig_holstein.yml).
PROJECT_LOCATION_MAP: dict[str, str] = {
    # schleswig_holstein.yml — all the Schleswig-Holstein duchies
    "Schleswig-Holstein": "schleswig_holstein",
    "Schleswig-Holstein-Sonderburg": "schleswig_holstein",
    "Schleswig-Holstein-Gottorf": "schleswig_holstein",
    "Schleswig-Holstein-Glücksburg": "schleswig_holstein",
    "Schleswig-Holstein-Plön": "schleswig_holstein",
    "Schleswig-Holstein-Augustenburg": "schleswig_holstein",
    # lauenburg.yml — Sachsen-Lauenburg duchy
    "Sachsen-Lauenburg": "lauenburg",
    "Lauenburg": "lauenburg",
    # lubeck.yml — Hanseatic city of Lübeck
    "Lübeck": "lubeck",
    # lubeck_bishopric.yml — Lübeck-Bistum / Hochstift
    "Bistum Lübeck": "lubeck_bishopric",
    "Hochstift Lübeck": "lubeck_bishopric",
    # denmark.yml — Danish & Danish-Norwegian crown + Danish-
    # controlled territories of other states. Norwegian mints route
    # to denmark.yml only for the Danish-Norwegian-union era
    # (≤ 1814); IKMK records dated 1815+ under the «Norwegen»
    # prefix are Sweden-Norway-union or independent-Norway issues
    # and won't year-overlap any coin in our denmark.yml — the
    # matcher's per-coin year-overlap check naturally filters
    # them out without an extra gate here. Out-of-scope by year
    # is already enforced by `_in_scope` against [1566, 1914].
    "Dänemark": "denmark",
    "Norwegen": "denmark",
    # Iceland / Faroe / Greenland — Danish dependencies
    "Island": "denmark",
    "Färöer": "denmark",
    "Faroe Islands": "denmark",
    "Grönland": "denmark",
    # Danish overseas trading colonies — coins struck for the
    # Danish crown's territorial possessions outside the Helstaten
    # core.
    "Tranquebar": "denmark",
    "Dänisch-Indien": "denmark",
    "Dänisch-Westindien": "denmark",
    "Dänisch Guinea": "denmark",
    "Dänische Goldküste": "denmark",
    # Medieval Norwegian Trondheim mints (under Danish-Norwegian
    # crown 1397+); IKMK groups them under their own city prefix
    # rather than the «Norwegen» country prefix.
    "Trondheim": "denmark",
    # bremen_verden.yml + future bremen-archbishopric (TODO C)
    "Bremen": "bremen_verden",
    "Erzbistum Bremen": "bremen_verden",
    "Bistum Bremen": "bremen_verden",
    "Bremen-Verden": "bremen_verden",
    # hamburg.yml
    "Hamburg": "hamburg",
    # osnabrueck.yml
    "Osnabrück": "osnabrueck",
    # Holstein-Schauenburg — bulk-seed stub for the dynasty as a whole
    # (commit 0b14f71). Pinneberg-branch (Kreis Pinneberg, modern SH)
    # and Schaumburg-proper (Stadthagen / Bückeburg, modern Niedersachsen)
    # both ruled by Ernst III in 1616-1622 — IKMK groups them under one
    # dynastic prefix without mint-city distinction, so they live in
    # holstein_schauenburg.yml until per-coin research splits them.
    "Holstein-Schauenburg": "holstein_schauenburg",
}


def _yr(rec: dict, key: str) -> int | None:
    v = rec.get(key)
    try:
        return int(v) if v else None
    except (TypeError, ValueError):
        return None


def _load_records() -> list[dict]:
    out = []
    for f in sorted(os.listdir(CACHE_DIR)):
        if not f.endswith(".json") or f.startswith("_"):
            continue
        try:
            data = json.loads((CACHE_DIR / f).read_text(encoding="utf-8"))
            data["_file"] = f
            out.append(data)
        except Exception as exc:
            print(f"  parse error {f}: {exc}", file=sys.stderr)
    return out


def _issuer_prefix(rec: dict) -> str:
    title = rec.get("title") or ""
    return title.split(":", 1)[0].strip() or "(no title)"


def _in_scope(rec: dict) -> bool:
    ys = _yr(rec, "year_start")
    ye = _yr(rec, "year_end") or ys
    if ys is None:
        return False
    return not (ye < SCOPE_YEAR_MIN or ys > SCOPE_YEAR_MAX)


def _material_name(rec: dict) -> str:
    m = rec.get("material") or {}
    return m.get("material_name_en") or m.get("material_name_de") or "—"


def _mint_place(rec: dict) -> str:
    mint = rec.get("mint") or []
    # IKMK occasionally nests mint as list-of-list; flatten and pick the
    # first dict-shaped entry.
    if isinstance(mint, list):
        for m in mint:
            if isinstance(m, dict):
                return (
                    m.get("place_name_de")
                    or m.get("place_name_en")
                    or m.get("country_name_de")
                    or "—"
                )
            if isinstance(m, list) and m and isinstance(m[0], dict):
                inner = m[0]
                return (
                    inner.get("place_name_de")
                    or inner.get("place_name_en")
                    or inner.get("country_name_de")
                    or "—"
                )
    return "—"


def _nominal_de(rec: dict) -> str:
    n = rec.get("nominal") or {}
    return n.get("nominal_de") or "—"


def build_index(records: list[dict]) -> dict:
    issuers: dict[str, dict] = {}
    for rec in records:
        prefix = _issuer_prefix(rec)
        bucket = issuers.setdefault(prefix, {
            "count": 0,
            "in_scope": 0,
            "year_min": None,
            "year_max": None,
            "materials": Counter(),
            "mints": Counter(),
            "nominals": Counter(),
            "ids_in_scope": [],
            "ids_out_of_scope": [],
            "sample_titles": [],
        })
        bucket["count"] += 1
        ys = _yr(rec, "year_start")
        ye = _yr(rec, "year_end") or ys
        if ys is not None:
            if bucket["year_min"] is None or ys < bucket["year_min"]:
                bucket["year_min"] = ys
            if bucket["year_max"] is None or (ye or ys) > bucket["year_max"]:
                bucket["year_max"] = ye or ys
        bucket["materials"][_material_name(rec)] += 1
        bucket["mints"][_mint_place(rec)] += 1
        bucket["nominals"][_nominal_de(rec)] += 1
        nid = rec.get("ikmk_mds_id") or rec["_file"].replace(".json", "")
        if _in_scope(rec):
            bucket["in_scope"] += 1
            bucket["ids_in_scope"].append(nid)
        else:
            bucket["ids_out_of_scope"].append(nid)
        if len(bucket["sample_titles"]) < 6:
            t = rec.get("title") or ""
            after_colon = t.split(":", 1)[1].strip() if ":" in t else t
            bucket["sample_titles"].append(after_colon[:60])

    # Finalize counters → dicts (top-N for compactness)
    finalized: dict[str, dict] = {}
    for prefix, b in issuers.items():
        finalized[prefix] = {
            "count": b["count"],
            "in_scope": b["in_scope"],
            "year_min": b["year_min"],
            "year_max": b["year_max"],
            "project_location": PROJECT_LOCATION_MAP.get(prefix),
            "materials": dict(b["materials"].most_common()),
            "mints_top10": dict(b["mints"].most_common(10)),
            "nominals_top10": dict(b["nominals"].most_common(10)),
            "ids_in_scope": sorted(b["ids_in_scope"], key=int),
            "ids_out_of_scope": sorted(b["ids_out_of_scope"], key=int),
            "sample_titles": b["sample_titles"],
        }

    # Build the by-project-location reverse index
    by_location: dict[str, list[str]] = {}
    unmapped: list[str] = []
    for prefix, info in finalized.items():
        loc = info["project_location"]
        if loc:
            by_location.setdefault(loc, []).append(prefix)
        else:
            unmapped.append(prefix)
    for loc, prefixes in by_location.items():
        prefixes.sort(key=lambda p: -finalized[p]["in_scope"])
    unmapped.sort(key=lambda p: -finalized[p]["in_scope"])

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_cache": str(CACHE_DIR.relative_to(CACHE_DIR.parents[2])),
        "total_records": sum(b["count"] for b in finalized.values()),
        "scope_window": [SCOPE_YEAR_MIN, SCOPE_YEAR_MAX],
        "by_project_location": by_location,
        "unmapped_issuers_top": unmapped[:50],
        "issuers": finalized,
    }


def write_summary_md(index: dict) -> None:
    issuers = index["issuers"]
    lines: list[str] = []
    lines.append(f"# IKMK Berlin cache — issuer index\n")
    lines.append(f"Generated {index['generated_at']} from `{index['source_cache']}`. ")
    lines.append(f"Window {SCOPE_YEAR_MIN}–{SCOPE_YEAR_MAX}.\n")
    lines.append(f"Total records: **{index['total_records']}**.\n")

    # Project-location section: clearly mapped issuers first
    lines.append("\n## Mapped to project locations\n")
    for loc, prefixes in sorted(index["by_project_location"].items()):
        total = sum(issuers[p]["count"] for p in prefixes)
        scope = sum(issuers[p]["in_scope"] for p in prefixes)
        lines.append(f"\n### `{loc}` — {scope} in scope / {total} total\n")
        lines.append("| issuer | total | in scope | year_min | year_max | top mint | top nominal |")
        lines.append("|---|---:|---:|---:|---:|---|---|")
        for p in prefixes:
            b = issuers[p]
            top_mint = next(iter(b["mints_top10"].keys()), "—")
            top_nom = next(iter(b["nominals_top10"].keys()), "—")
            lines.append(
                f"| {p} | {b['count']} | {b['in_scope']} | {b['year_min'] or '—'} "
                f"| {b['year_max'] or '—'} | {top_mint} | {top_nom} |",
            )

    # Unmapped issuers — sorted by in-scope count descending, top-50
    lines.append("\n## Unmapped issuers (top 50 by in-scope count)\n")
    lines.append("These don't currently map to a project location — useful as ")
    lines.append("a shortlist when considering new locations or extending scope.\n")
    lines.append("\n| issuer | total | in scope | year_min | year_max | top mint |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for p in index["unmapped_issuers_top"]:
        b = issuers[p]
        if b["in_scope"] == 0:
            continue
        top_mint = next(iter(b["mints_top10"].keys()), "—")
        lines.append(
            f"| {p} | {b['count']} | {b['in_scope']} | {b['year_min'] or '—'} "
            f"| {b['year_max'] or '—'} | {top_mint} |",
        )

    lines.append("\n## How to use\n")
    lines.append("\n* Pick an issuer of interest from the tables above.")
    lines.append("\n* Look up its `ids_in_scope` array in `_index_by_issuer.json` ")
    lines.append("to get the IKMK IDs to work with.")
    lines.append("\n* Each ID resolves to `scripts/cache/ikmk/<id>.json` ")
    lines.append("(IKMK record, CC BY-SA 4.0 / PDM 1.0).")
    lines.append("\n")
    INDEX_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not CACHE_DIR.exists():
        print(f"cache dir missing: {CACHE_DIR}", file=sys.stderr)
        return 1
    records = _load_records()
    print(f"Loaded {len(records)} records.")
    index = build_index(records)
    INDEX_JSON.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary_md(index)
    print(
        f"Wrote {INDEX_JSON.relative_to(Path.cwd())} "
        f"({len(index['issuers'])} issuers, "
        f"{sum(b['in_scope'] for b in index['issuers'].values())} in-scope records).",
    )
    print(f"Wrote {INDEX_MD.relative_to(Path.cwd())}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
