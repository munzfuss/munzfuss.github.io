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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import NUMISMASTER_CACHE, PROJECT_ROOT  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

# §AZ pre-1541 subdir under the canonical NumisMaster cache root.
# See lib/paths.py for the full layout planned at Phase-1b/2 completion.
CACHE_DIR = NUMISMASTER_CACHE / "denmark_pre_1541"

YEAR_FROM = 1514
YEAR_TO = 1541


def _group_consecutive_years(years: list[int]) -> list[tuple[int, int]]:
    """Collapse a sorted year list into consecutive-run [first, last] ranges.
    Mirrors `build_numismaster_seed.py::_group_consecutive_years`."""
    if not years:
        return []
    sorted_ys = sorted(set(years))
    out: list[tuple[int, int]] = []
    cur_start = cur_end = sorted_ys[0]
    for y in sorted_ys[1:]:
        if y == cur_end + 1:
            cur_end = y
            continue
        out.append((cur_start, cur_end))
        cur_start = cur_end = y
    out.append((cur_start, cur_end))
    return out


def _format_year_label(ranges: list[tuple[int, int]]) -> str:
    """Canonical year_label string per CLAUDE.md §3a: en-dash inside ranges,
    comma-space between range entries."""
    parts: list[str] = []
    for a, b in ranges:
        parts.append(str(a) if a == b else f"{a}–{b}")
    return ", ".join(parts)


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

    # `numismaster_mc` is a non-schema audit anchor. Carry it as
    # underscore-prefixed top-level field so `_merge_seeds_into_raw`
    # strips it at validation time; not inside `catalog` (schema strict).
    catalog: dict = {}
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

    # Prefer per-year breakdown from the «Value information» table when
    # available — Mirror of the main builder's preference order. Otherwise
    # fall back to the broader date_raw range as a single year_ranges entry.
    dates_explicit = data.get("dates_explicit") or []
    if dates_explicit:
        grouped = _group_consecutive_years(dates_explicit)
        year_label = _format_year_label(grouped)
        year_ranges = [[a, b] for a, b in grouped]
        yf = grouped[0][0]
        yl = grouped[-1][1]
    else:
        # Single-year collapse: «1628 - 1628» → «1628»
        if yl is None or yl == yf:
            year_label = str(yf)
            year_ranges = [[yf, yf]]
            yl = yf
        else:
            year_label = f"{yf}–{yl}"
            year_ranges = [[yf, yl]]

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "numismaster",
        "kind": "kurant",
        "nominal": data.get("denomination"),
        "year_label": year_label,
        "year_first": yf,
        "year_last": yl,
        "year_ranges": year_ranges,
        "ruler": data.get("ruler"),
        "mint": data.get("mint"),
        "catalog": catalog,
        "_numismaster_mc": str(mc),
        "metal": metal,
        "fineness": data.get("fineness"),
        "weight_rough_g": data.get("mass_g"),
        "issuing_entity": issuing,
        "verified": False,
        # metal_verified: true when NumisMaster's «Composition» field is
        # explicitly attested («Silver», «Billon», «Copper», …) — mirrors
        # the same flag the main builder sets. Skipped when composition
        # is None (detect_metal then guessed from denomination tokens).
        "metal_verified": bool(data.get("composition")),
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
    # Read parser output ONLY — `.parsed.json`. The bare `MC_*.json` glob
    # would also match stale `.json` files left over from an earlier parser
    # version that wrote to the bare suffix; reading those re-injects the
    # old parser's bugs (e.g. truncated `lange: "23, 2"` for L#23, 23AB).
    for json_path in sorted(CACHE_DIR.glob("MC_*.parsed.json")):
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
    write_v2_seed(
        entries,
        source_name="numismaster",
        source_label="NumisMaster (numismaster.com per-coin HTML MC_NNNNN pages)",
        scope_note=(
            "§AZ Tier 4 — NumisMaster HTML-scrape. Krause-Mishler-based "
            "commercial catalog. Pre-1604 KM coverage sparse, but pre-1541 "
            "Schleswig-Holstein-duchy coins are catalogued under «MB#» (pre-"
            "Krause Madai-Bach numbering). Initial harvest captures 3 in-scope "
            "entries surfaced from id=-10012282 (Holstein-Gottorp-Rendsborg "
            "search). Full Schleswig-Holstein sub-territory walk for additional "
            "MB_ entries deferred to future enrichment session."
        ),
        dry_run=args.dry_run,
        no_merge=args.no_merge,
        extra_top_level={
            "scope_year_from": YEAR_FROM,
            "scope_year_to": YEAR_TO,
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
