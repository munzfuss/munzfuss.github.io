#!/usr/bin/env python3
"""§AZ Tier 4 seed builder — NumisMaster MC_NNNNN parsed JSON →
data/seed/numismaster/denmark_pre_1541.yml.

NumisMaster's distinctive contribution:
  - Krause-Mishler KM# numbering (when applicable)
  - Madai-Bach «MB#» for pre-Krause Schleswig-Holstein duchy coins
  - Obverse + Reverse legends (Latin)
  - General-note style cross-references (Sch# / L# / Fr#)
  - Polit-economic period attribution («Duchy», «Trade Coinage» tags)

§BJ source survey predicted sparse pre-1541 coverage (KM# starts ~1604);
confirmed via Chrome MCP browse 2026-05-16: id=-10012282 (Holstein-
Gottorp-Rendsborg search) surfaces 3 MB_-numbered entries in scope.
Future enrichment can extend by walking other Schleswig-Holstein-*
sub-territories.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import NUMISMASTER_CACHE, PROJECT_ROOT  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

# §AZ pre-1541 subdir under the canonical NumisMaster cache root.
# See lib/paths.py for the full layout planned at Phase-1b/2 completion.
CACHE_DIR = NUMISMASTER_CACHE / "denmark_pre_1541"
OUT_PATH = PROJECT_ROOT / "data" / "seed" / "numismaster" / "denmark_pre_1541.yml"

YEAR_FROM = 1514
YEAR_TO = 1541


def detect_metal(comp: str | None, denom: str | None) -> str:
    if comp:
        c = comp.lower()
        if "gold" in c: return "gold"
        if "billon" in c: return "billon"
        if "silver" in c: return "silver"
        if "copper" in c: return "copper"
    if denom:
        d = denom.lower()
        if any(t in d for t in ["goldgulden", "ducat", "noble", "krone"]):
            return "gold"
        if "pfennig" in d or "hvid" in d:
            return "billon"
    return "silver"


def build_entry(data: dict) -> dict | None:
    yf = data.get("year_first")
    yl = data.get("year_last")
    if yf is None:
        return None
    # Include if range overlaps 1514-1541
    if (yl or yf) < YEAR_FROM or yf > YEAR_TO:
        return None

    mc = data.get("numismaster_id")
    cid = f"dk-numismaster-{mc}"

    composition = data.get("composition") or ""
    metal = detect_metal(composition, data.get("denomination"))

    catalog: dict = {"numismaster_mc": str(mc)}
    if data.get("catalog_number"):
        # «MB# 33» → mb=33; «KM# 7» → km=7
        cat = data["catalog_number"]
        m = cat.split("#", 1)
        if len(m) == 2:
            prefix = m[0].strip().lower()
            value = m[1].strip()
            if prefix in ("mb",):
                catalog["mb"] = value  # Madai-Bach (pre-Krause SH duchy numbering)
            elif prefix == "km":
                catalog["km"] = value
            else:
                catalog[prefix] = value
    catalog.update(data.get("catalog_refs") or {})

    # Canonical V2 issuing_entity from NumisMaster `country` (D38, 2026-05-19).
    # Pre-1541 mission scope is mostly Christian II / Frederik I Danish royal
    # coinage; the Schleswig-Holstein cadet lines didn't yet exist (formed
    # 1544+ with Christian III's split). Map the few SH attestations to
    # `royal_holstein` (the Danish king's Holstein duchy era).
    issuing = "danish_realm"
    country = (data.get("country") or "").upper()
    if "NORWAY" in country:
        issuing = "danish_norway"
    elif "SCHLESWIG-HOLSTEIN" in country or "HOLSTEIN" in country:
        # Pre-1544 → no Holstein cadet lines yet. SH-tagged pre-1541
        # entries are Danish-royal-Holstein coinage → royal_holstein.
        issuing = "royal_holstein"

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "numismaster",
        "kind": "kurant",
        "nominal": data.get("denomination"),
        "year_label": data.get("date_raw"),
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": [[yf, yl if yl is not None else yf]],
        "ruler": data.get("ruler"),
        "mint": data.get("mint"),
        "catalog": catalog,
        "metal": metal,
        "fineness": data.get("fineness"),
        "weight_rough_g": data.get("mass_g"),
        "issuing_entity": issuing,
        "verified": False,
        "fineness_verified": data.get("fineness") is not None,
        "weight_rough_verified": data.get("mass_g") is not None,
        "mint_verified": bool(data.get("mint")),
        "sources": [
            {
                "type": "literature",
                "url": data.get("url"),
                "ref": (
                    f"NumisMaster MC_{mc} — "
                    f"{data.get('country', '?')} {data.get('catalog_number', '')} "
                    f"{data.get('denomination', '')} {data.get('date_raw', '')}".strip()
                ),
            }
        ],
        "verification_note": {
            "de": (
                "NumisMaster-Seed (§AZ Tier 4): Krause-Mishler-basiertes "
                "kommerzielles Katalog. Pre-1604 KM-Nummerierung sparse — "
                "die meisten Pre-1541 Schleswig-Holstein-Herzogthum-Münzen "
                "kommen mit «MB#»-Nummerierung (Madai-Bach, vor-Krause). "
                "Per-Münze-Verifikation gegen Primärquellen vor §BF-Promotion."
            ),
            "en": (
                "NumisMaster seed (§AZ Tier 4): Krause-Mishler-based commercial "
                "catalogue. Pre-1604 KM numbering sparse — most pre-1541 "
                "Schleswig-Holstein duchy coins come with «MB#» numbering "
                "(Madai-Bach, pre-Krause). Per-coin verification against primary "
                "sources before §BF promotion."
            ),
            "uk": (
                "NumisMaster-seed (§AZ Tier 4): Krause-Mishler-базований "
                "комерційний каталог. Pre-1604 KM-нумерація розріджена — "
                "більшість pre-1541 Schleswig-Holstein-герцогських монет мають "
                "«MB#»-нумерацію (Madai-Bach, до-Krause). Покоінна верифікація "
                "проти первинних джерел перед §BF-промоцією."
            ),
        },
    }
    if data.get("political_period"):
        entry["political_period"] = data["political_period"]
    if data.get("coinage_entity"):
        entry["coinage_entity"] = data["coinage_entity"]
    if data.get("obverse"):
        entry["obverse"] = data["obverse"]
    if data.get("reverse"):
        entry["reverse"] = data["reverse"]
    if data.get("general_note"):
        entry["general_note"] = data["general_note"]
    if data.get("actual_weight_fein"):
        entry["actual_weight_fein_g"] = data["actual_weight_fein"]

    return entry


def collect() -> list[dict]:
    entries: list[dict] = []
    for json_path in sorted(CACHE_DIR.glob("MC_*.json")):
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError as e:
            print(f"  [{json_path.name}] parse error: {e}", file=sys.stderr)
            continue
        entry = build_entry(data)
        if entry:
            entries.append(entry)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
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
    entries = collect()
    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("id", "")))
    print(f"Total entries: {len(entries)}")
    if args.dry_run:
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Merge fresh-generated entries against existing on-disk seed, preserving
    # curated decisions (CURATED_FIELDS) + dict deep-merges (catalog) +
    # verified-wins (measurements) + per-entry holds. See scripts/lib/seed_merge.py.
    if not args.no_merge:
        entries, merge_stats = merge_seed(entries, OUT_PATH)
        print(
            f"Merge against existing {OUT_PATH.name}: "
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
        "source": "NumisMaster (numismaster.com per-coin HTML MC_NNNNN pages)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope_year_from": YEAR_FROM,
        "scope_year_to": YEAR_TO,
        "scope_note": (
            "§AZ Tier 4 — NumisMaster HTML-scrape. Krause-Mishler-based "
            "commercial catalog. Pre-1604 KM coverage sparse, but pre-1541 "
            "Schleswig-Holstein-duchy coins are catalogued under «MB#» (pre-"
            "Krause Madai-Bach numbering). Initial harvest captures 3 in-scope "
            "entries surfaced from id=-10012282 (Holstein-Gottorp-Rendsborg "
            "search). Full Schleswig-Holstein sub-territory walk for additional "
            "MB_ entries deferred to future enrichment session."
        ),
        "coins": entries,
    }
    with OUT_PATH.open("w") as f:
        yaml.dump(out, f)
    print(f"Wrote {OUT_PATH.relative_to(PROJECT_ROOT)} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
