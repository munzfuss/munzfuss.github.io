#!/usr/bin/env python3
"""build_galster_denmark_seed.py — generate `data/seed/galster/denmark_pre_1541.yml`
from parsed Galster page sidecars at `scripts/cache/danskmoent/galster/*.json`.

§AZ Tier 2 (per `docs/research/denmark_pre_1541_source_survey.md`). The
parsed Galster JSON sidecars carry per-page data (ruler, denomination,
year, mint, catalog refs, Bruttovægt + Finhed + Finvægt where attested,
inscription, Litteratur). This script walks those sidecars and emits a
project-shaped seed YAML for the 1514-1541 sub-window.

Parallel to `data/seed/bruun/denmark_pre_1541.yml` (Tier 1) +
`data/seed/hede/denmark.yml` (existing main seed). §BF promotes entries
from any of the three into curated `data/locations/denmark.yml` entries
during its data-population phase.

Scope filter: 1514 ≤ year ≤ 1541. Norway sub-pages (norge_*.json) and
Schleswig-Holstein lots are INCLUDED (per §BI «realm» scope).

Run:
    .venv/bin/python scripts/maintenance/build_galster_denmark_seed.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from lib.paths import GALSTER_CACHE  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

OUT_PATH = PROJECT_ROOT / "data" / "seed" / "galster" / "denmark_pre_1541.yml"

YEAR_FROM = 1514
YEAR_TO = 1541


def parse_year_range(year_label: str | None) -> tuple[int | None, int | None]:
    """Extract (year_first, year_last) from a Galster page year_label.

    Examples:
      «1531» → (1531, 1531)
      «1516, 1518» → (1516, 1518)
      «1535-1540» → (1535, 1540)
      «u.år» → (None, None) — falls back to «pre-1540» heuristic
    """
    if not year_label:
        return None, None
    years = [int(m) for m in re.findall(r"\b(1[5-6]\d{2})\b", year_label)]
    if not years:
        return None, None
    return min(years), max(years)


def detect_metal(denom: str | None) -> str:
    if not denom:
        return "silver"
    d = denom.lower()
    if any(t in d for t in ["nobel", "goldgulden", "ungersk gylden", "rhinsk gylden", "ducat", "guldreal", "krone", "goldreal"]):
        return "gold"
    if any(t in d for t in ["hvid", "penning", "blaffert"]):
        return "billon"
    if any(t in d for t in ["sølvgylden", "solvgylden", "joachimstaler", "joachimsdaler"]):
        return "silver"
    if "skilling" in d or "søsling" in d or "sosling" in d:
        return "billon"
    if "mark" in d:
        return "silver"
    return "silver"


def detect_issuing_entity(sub_realm: str | None, mint: str | None) -> str:
    if sub_realm == "norway":
        return "norwegian_realm"
    return "danish_realm"


def coin_id(galster_number: str | None, ruler_volume: str | None, source_file: str) -> str:
    """Stable ID: dk-galster-<ruler_volume>-<number>.

    Falls back to dk-galster-<source_filename> if metadata is missing.
    """
    if galster_number and ruler_volume:
        return f"dk-galster-{ruler_volume}-{galster_number.lower()}"
    return f"dk-galster-{source_file.replace('.htm', '').replace('.json', '')}"


def build_entry(data: dict) -> dict | None:
    year_first, year_last = parse_year_range(data.get("year_label"))
    if year_first is None or year_last is None:
        return None
    if not (YEAR_FROM <= year_first <= YEAR_TO):
        return None

    catalog: dict = dict(data.get("catalog_refs") or {})
    if data.get("galster_number") and "galster" not in catalog:
        catalog["galster"] = data["galster_number"]
    if data.get("ruler_volume"):
        catalog["galster_volume"] = data["ruler_volume"]

    specs = data.get("specs") or {}
    sub_realm = data.get("sub_realm")
    metal = detect_metal(data.get("denomination"))

    cid = coin_id(data.get("galster_number"), data.get("ruler_volume"), data.get("source_file", ""))

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "galster",
        "kind": "kurant",
        "nominal": data.get("denomination"),
        "year_label": data.get("year_label"),
        "year_first": year_first,
        "year_last": year_last,
        "year_ranges": [[year_first, year_last]] if year_first == year_last else [[year_first, year_last]],
        "ruler": data.get("ruler"),
        "mint": data.get("mint"),
        "catalog": catalog,
        "metal": metal,
        "fineness": specs.get("finhed"),
        "weight_rough_g": specs.get("bruttovaegt_g"),
        "issuing_entity": detect_issuing_entity(sub_realm, data.get("mint")),
        "verified": False,
        "fineness_verified": bool(specs.get("finhed")),
        "weight_rough_verified": bool(specs.get("bruttovaegt_g")),
        "mint_verified": bool(data.get("mint")),
        "sources": [
            {
                "type": "literature",
                "url": data.get("source_url_hint"),
                "ref": (
                    f"Galster {data.get('galster_number', '?')} "
                    f"({data.get('ruler_volume', '?')}) — "
                    f"danskmoent.dk {data.get('source_file', '?')}"
                ),
            }
        ],
        "verification_note": {
            "de": (
                "Galster-Seed: spezifikische Münzfuß- und Phase-Zuordnung sowie "
                "Per-Münze-Verifikation stehen noch aus; Daten direkt aus den "
                "danskmoent.dk-Galster-Seiten (Hosting der Galster-Numismatik) "
                "übernommen. Cross-references aus dem H1 + Beschreibungsblock "
                "automatisch extrahiert (Schou, Sieg, Jensen-Skjoldager, Schive, etc.)."
            ),
            "en": (
                "Galster seed: Müntzfuß and phase assignment plus per-coin "
                "verification are still outstanding; data taken directly from "
                "the danskmoent.dk Galster-page series (hosting Galster numismatic "
                "catalog). Cross-references from H1 + description block "
                "extracted automatically (Schou, Sieg, Jensen-Skjoldager, Schive, etc.)."
            ),
            "uk": (
                "Galster-seed: призначення Müntzfuß і фази та покоінна верифікація "
                "ще очікуються; дані взято безпосередньо зі сторінок Galster на "
                "danskmoent.dk (хостинг каталога Galster). Cross-references з "
                "H1 + блоку опису витягнуто автоматично (Schou, Sieg, Jensen-"
                "Skjoldager, Schive, тощо)."
            ),
        },
    }

    # Inscription as literary attachment
    if data.get("inscription"):
        entry["inscription"] = data["inscription"]
    if data.get("litteratur"):
        entry["additional_litteratur"] = data["litteratur"]
    if sub_realm:
        entry["sub_realm"] = sub_realm
    if specs.get("finvaegt_g"):
        entry["finvaegt_g"] = specs["finvaegt_g"]
    if specs.get("mintage"):
        entry["mintage"] = specs["mintage"]

    return entry


def collect_entries() -> list[dict]:
    entries: list[dict] = []
    for json_path in sorted(GALSTER_CACHE.glob("*.json")):
        if json_path.name.startswith("_"):
            continue
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError as e:
            print(f"  [{json_path.name}] JSON parse error: {e}", file=sys.stderr)
            continue
        entry = build_entry(data)
        if entry:
            entries.append(entry)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--no-merge",
        action="store_true",
        help=(
            "Skip the curation-preserving merge against the existing on-disk "
            "seed and overwrite wholesale with fresh output. Destructive — only "
            "use for verification / dry-run paths."
        ),
    )
    args = ap.parse_args()

    print(f"Collecting Galster pre-1541 entries from {GALSTER_CACHE}...")
    entries = collect_entries()
    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("id", "")))

    from collections import Counter
    by_ruler = Counter(e.get("ruler") or "?" for e in entries)
    by_mint = Counter(e.get("mint") or "?" for e in entries)
    by_realm = Counter(e.get("issuing_entity") for e in entries)
    by_metal = Counter(e.get("metal") for e in entries)
    print(f"\nTotal entries: {len(entries)}")
    print(f"By ruler:  {dict(by_ruler.most_common())}")
    print(f"By mint:   {dict(by_mint.most_common(15))}")
    print(f"By realm:  {dict(by_realm.most_common())}")
    print(f"By metal:  {dict(by_metal.most_common())}")

    if args.dry_run:
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Merge fresh-generated entries against existing on-disk seed, preserving
    # curated decisions (CURATED_FIELDS) + dict deep-merges (catalog) +
    # verified-wins (measurements) + per-entry holds. See scripts/lib/seed_merge.py.
    if not args.no_merge:
        entries, merge_stats = merge_seed(entries, OUT_PATH)
        print(
            f"\nMerge against existing {OUT_PATH.name}: "
            f"merged_existing={merge_stats['merged_existing']}, "
            f"added_new={merge_stats['added_new']}, "
            f"orphan_curated={merge_stats['orphan_curated']}"
        )

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.width = 200
    yaml.indent(mapping=2, sequence=4, offset=2)
    out = {
        "status": "seed",
        "source": "danskmoent.dk Galster-page series (Christian II + Frederik I indexes + Christian III pre-1541)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope_year_from": YEAR_FROM,
        "scope_year_to": YEAR_TO,
        "scope_note": (
            "§AZ Tier 2 — danskmoent.dk Galster-page harvest. Covers Christian "
            "II + Frederik I + Christian III pre-1541 (Hede 1957 doesn't "
            "catalogue these). Parallel source to data/seed/bruun/ (Tier 1) "
            "and data/seed/hede/ (existing main). §BF promotion uses all three."
        ),
        "coins": entries,
    }
    with OUT_PATH.open("w") as f:
        yaml.dump(out, f)
    print(f"\nWrote {OUT_PATH.relative_to(PROJECT_ROOT)} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
