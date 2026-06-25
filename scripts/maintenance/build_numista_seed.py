#!/usr/bin/env python3
"""build_numista_seed.py — Generic, year-agnostic Numista Phase 3 builder.

Reads canonical Phase 2 sidecars from
`scripts/cache/numista/parsed/<NID>.json` (emitted by
`scripts/parse_numista.py`) and writes per-entity seeds to
`data/v2/seed/numista/<entity>.yml` via the shared
`scripts/lib/v2_seed_writer.write_v2_seed`.

Replaces `build_numista_pre1541_seed.py` which was hard-scoped to the
1514-1541 Denmark sub-window via a separate cache subdir. This generic
builder is **agnostic to year**, ingests every parsed sidecar, and
delegates per-entity routing to the shared writer (same path that
Hede + Bruun builders use).

Entity classification — two-tier:
  1. Mint-driven via `classify_mint_to_entity(coin.mint)` — wins when
     mint is present in our registry (Altona / Kopenhagen / Glückstadt
     / Schleswig / Tönning / Christiania / etc.).
  2. Issuer-driven via `classify_issuer_to_entity(canonical.issuer)`
     — fallback when mint is absent. Numista's issuer string carries
     the jurisdiction even when mint is uncatalogued
     (`Schleswig-Holstein-Gottorp, Duchy of` → `gottorp_duchy`).
  3. Both None → coin routes to `_unclassified.yml` per write_v2_seed.

Curation-preserving merge applies per the seed_merge module — existing
curated `fuss` / `phase` / `kind` / `fraction` / `note` / verification
flags survive regeneration.

Run:
    .venv/bin/python scripts/maintenance/build_numista_seed.py
    .venv/bin/python scripts/maintenance/build_numista_seed.py --dry-run
    .venv/bin/python scripts/maintenance/build_numista_seed.py --no-merge
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.entity_routing import route_entity_with_rules  # noqa: E402
from lib.v2_entity_classify import (  # noqa: E402
    classify_issuer_to_entity,
    classify_mint_to_entity,
    is_known_issuer,
)
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

PARSED_DIR = PROJECT_ROOT / "scripts" / "cache" / "numista" / "parsed"

# Catalog fields the canonical sidecar emits as a flat string-keyed
# dict (per parse_references_from_*). Pydantic CatalogRefs strict-extra
# rejects unknown keys, so we filter to the subset our schema accepts.
# Derive the allowed-key set FROM the schema (CatalogRefs.model_fields) rather
# than a hand-maintained white-list — so the builder accepts EXACTLY what the
# typer models, including the `others` catch-all + every typed ref field. The
# Numista parser routes any unmodelled catalogue code into `others` (generic,
# open to ANY index), keeping the chain lossless: a new/unknown catalogue
# Numista emits flows parser → others → builder → schema → render with no
# white-list to drift out of sync.
try:
    from lib.schema import CatalogRefs as _CatalogRefs  # noqa: E402
    _ALLOWED_CATALOG = set(_CatalogRefs.model_fields.keys())
except Exception:  # pragma: no cover — defensive
    _ALLOWED_CATALOG = {
        "km", "lange", "hede", "sieg", "sieg_hede1971", "schou",
        "schou_hede1971", "fr", "dav", "davenport", "mb", "galster",
        "galster_volume", "friedberg", "jensen_skjoldager", "schive",
        "skaare", "nmd", "fp", "hede_volume", "numista", "others",
        "bruun_collection_id", "bruun_part", "bruun_lot_no", "bruun_page",
        "bruun_lot",
    }


# Numista labels Danish kings with their English exonyms; the project uses
# the Danish form (e.g. «Hans», 217× canonical). Map the King-Hans exonyms
# to the Danish canonical. (The systemic «Frederick» → «Frederik» divergence
# is a broader, separate ruler-canonicalisation pass — not handled here yet.)
_NUMISTA_RULER_CANON = {
    "John I (Hans I)": "Hans",
    "John I": "Hans",
}


def _resolve_ruler(kings: list[dict] | None) -> str | None:
    """Pick the most informative ruler name. Multi-ruler entries get
    joined with « / » per pre_1541 builder convention. Danish exonyms are
    mapped to the project's canonical Danish form via `_NUMISTA_RULER_CANON`."""
    if not kings:
        return None
    names = []
    for k in kings:
        if isinstance(k, dict) and k.get("name"):
            nm = str(k["name"])
            names.append(_NUMISTA_RULER_CANON.get(nm, nm))
    if not names:
        return None
    if len(names) == 1:
        return names[0]
    return " / ".join(names)


def _resolve_default_entity(canonical: dict[str, Any]) -> str | list[str] | None:
    """Two-tier entity resolution: mint first, issuer fallback.

    Mint-driven classification is preferred because:
      * Mint is concrete (a physical place); issuer is jurisdictional.
      * Mint registry has year-aware overrides (Altona pre-1640 vs
        post-1640), which the issuer string can't disambiguate.
      * Hede + Bruun + NumisMaster builders all classify by mint; this
        keeps Numista consistent across sources.

    Issuer fallback fires when:
      * mint is None / not in mint registry, AND
      * issuer string is in our `_ISSUER_REGISTRY` table with a
        non-None entity.

    The result is the «default» entity — `route_entity_with_rules` then
    applies the tradition-driven rules layer on top, potentially
    re-routing the coin when mint is absent / unverified.
    """
    year = canonical.get("year_first")
    mint = canonical.get("mint")
    if mint:
        ent = classify_mint_to_entity(mint, year=year)
        if ent is not None:
            return ent
    issuer = canonical.get("issuer")
    if issuer:
        ent = classify_issuer_to_entity(issuer)
        if ent is not None:
            return ent
    return None


def _filter_catalog(refs: dict[str, str] | None) -> dict[str, str]:
    """Drop keys not in our schema. Schema validates strict-extra."""
    if not refs:
        return {}
    return {k: v for k, v in refs.items() if k in _ALLOWED_CATALOG}


# Country-volume tag Numista appends to a KM when a coin is cross-listed across
# Krause country volumes (§9.4): «479 (Denmark)» = Denmark-volume KM 479. Map
# the country name → the project's short register code (must match
# _ENTITY_TO_KM_REGISTER; «nor» NOT «no» — «no» is a YAML boolean). An UNKNOWN
# parenthetical («505 (OM)» — OM is not a country) aborts the transform.
_COUNTRY_TO_KM_REGISTER = {
    "denmark": "dk",
    "norway": "nor",
    "sweden": "se",
}


def _apply_km_country_register(catalog: dict, entity) -> None:
    """Fold Numista's «<km> (<Country>)» volume tags into the register-keyed dict
    form ``{register: km}`` the schema uses for cross-volume KMs (KMRef). A bare
    (untagged) value takes the coin's own entity register. In place; a no-op
    unless some km value carries a parenthetical tag, and left untouched entirely
    if any tag names a country we don't map (e.g. «(OM)») or a bare value has no
    resolvable register."""
    km = catalog.get("km")
    if km is None:
        return
    vals = km if isinstance(km, list) else [km]
    if not any("(" in str(v) for v in vals):
        return
    # _ENTITY_TO_KM_REGISTER is the single source of truth for entity→volume —
    # imported lazily (only fires for the rare cross-listed coin).
    import sys as _sys
    _md = str(Path(__file__).resolve().parent)
    if _md not in _sys.path:
        _sys.path.insert(0, _md)
    from merge_seeds_cross_source import _ENTITY_TO_KM_REGISTER
    reg_entity = entity[0] if isinstance(entity, list) else entity
    entity_reg = _ENTITY_TO_KM_REGISTER.get(reg_entity)
    reg_dict: dict[str, list] = {}
    for v in vals:
        s = str(v).strip()
        m = re.fullmatch(r"([\w.\-/]+)\s*\(([A-Za-z][\w ]*)\)", s)
        if m:
            num = m.group(1)
            reg = _COUNTRY_TO_KM_REGISTER.get(m.group(2).strip().lower())
            if reg is None:
                return  # unknown parenthetical — not a volume tag, leave raw
        else:
            num, reg = s, entity_reg
        if not reg:
            return  # no register for a bare value → leave km untouched
        reg_dict.setdefault(reg, [])
        if num not in reg_dict[reg]:
            reg_dict[reg].append(num)
    catalog["km"] = {r: (vs[0] if len(vs) == 1 else vs) for r, vs in reg_dict.items()}


def _strip_nominal(nominal: str | None) -> str | None:
    """Canonical-nominal hygiene — collapse whitespace + strip trailing
    Daler-fraction parenthetical (already done by canonical helpers but
    re-applied here for belt-and-braces)."""
    if not nominal or not isinstance(nominal, str):
        return None
    s = re.sub(r"\s+", " ", nominal).strip()
    s = re.sub(
        r"\s+\(([⅓⅔¼½¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+\s*[⁄/]\s*\d+)\)\s*$",
        "",
        s,
    ).strip()
    return s or None


def build_coin_entry(canonical: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one canonical Phase 2 sidecar into a Coin-schema dict
    suitable for the seed builder.

    Returns None when the entry is too incomplete to land in a seed
    (missing year_first or missing nominal)."""
    nid = canonical.get("numista_id")
    if nid is None:
        return None

    yf = canonical.get("year_first")
    if yf is None:
        return None
    yl = canonical.get("year_last") if canonical.get("year_last") is not None else yf

    nominal = _strip_nominal((canonical.get("value") or {}).get("raw")
                              if isinstance(canonical.get("value"), dict) else None)
    if not nominal:
        # Pre-1541 builder skips entries without a nominal — same here.
        return None

    composition = canonical.get("composition") or {}
    metal = composition.get("metal")
    fineness = composition.get("fineness")

    catalog: dict[str, Any] = {"numista": str(nid)}
    catalog.update(_filter_catalog(canonical.get("references")))

    cid = f"dk-numista-{nid}"

    # year_ranges: dash-form → single contiguous range; comma-form
    # (year_list) → per-year. Matches pre_1541 builder shape exactly.
    year_list = canonical.get("year_list") or None
    if year_list:
        year_ranges = [[y, y] for y in year_list]
        year_label = ", ".join(str(y) for y in year_list)
        year_first_out = year_list[0]
        year_last_out = year_list[-1]
    else:
        year_ranges = [[yf, yl]]
        year_label = canonical.get("years_raw") or (str(yf) if yl == yf else f"{yf}-{yl}")
        year_first_out = yf
        year_last_out = yl

    entry: dict[str, Any] = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "numista",
        "kind": "kurant",
        "nominal": nominal,
        "year_label": year_label,
        "year_first": year_first_out,
        "year_last": year_last_out,
        "year_ranges": year_ranges,
        "ruler": _resolve_ruler(canonical.get("kings")),
        "mint": canonical.get("mint"),
        "catalog": catalog,
        "metal": metal,
        "fineness": fineness,
        "weight_rough_g": canonical.get("weight_g"),
        "diameter_mm": canonical.get("diameter_mm"),
        "issuing_entity": None,           # populated by routing layer below
        "verified": False,
        "metal_verified": bool(metal) and metal != "unknown",
        "fineness_verified": fineness is not None,
        "weight_rough_verified": canonical.get("weight_g") is not None,
        "diameter_mm_verified": canonical.get("diameter_mm") is not None,
        "mint_verified": canonical.get("mint") is not None,
        "sources": [
            {
                "type": "literature",
                "url": canonical.get("url"),
                "ref": f"Numista N#{nid} — {canonical.get('title') or '?'}",
            }
        ],
        "verification_note": {
            "de": (
                "Numista-Seed: spezifikische Müntzfuß- und Phase-Zuordnung "
                "sowie Per-Münze-Verifikation stehen noch aus; Daten direkt "
                "aus der HTML-Katalogseite (en.numista.com) übernommen. "
                "Numista ist Benutzer-editiert; Cross-references (SIEG, "
                "Galster, Schou, Fr) müssen gegen Primärquellen geprüft "
                "werden bevor in kuratierte Einträge promotet."
            ),
            "en": (
                "Numista seed: Müntzfuß and phase assignment plus per-coin "
                "verification are still outstanding; data taken directly "
                "from the HTML catalog page (en.numista.com). Numista is "
                "user-edited; cross-references (SIEG, Galster, Schou, Fr) "
                "must be checked against primary sources before promotion "
                "into curated entries."
            ),
            "uk": (
                "Numista-seed: призначення Müntzfuß і фази та покоінна "
                "верифікація ще очікуються; дані взято безпосередньо з "
                "HTML-каталог-сторінки (en.numista.com). Numista редагується "
                "користувачами; cross-references (SIEG, Galster, Schou, Fr) "
                "треба перевірити проти первинних джерел перед промоцією у "
                "кур'єйтед-записи."
            ),
        },
    }

    # Apply entity routing — two-step process:
    #   1. Compute default entity via mint → issuer chain
    #   2. Layer the tradition-driven rules from
    #      `data/v2/entity_routing_rules.yml` on top. The rules layer
    #      is safe-mode: actively re-routes only when the coin's mint
    #      is None or `mint_verified: false`; otherwise records a hint
    #      noting whether rule agrees with mint-driven verdict. The
    #      hint persists on the entry so curators debugging non-obvious
    #      placements see the rule's analysis trace.
    default_ent = _resolve_default_entity(canonical)
    # `route_entity_with_rules` reads `ruler`, `nominal`, `mint`,
    # `mint_verified`, `year_first`, and optional `_numista_issuer` /
    # `_issuer` / `issuer` slots from the entry dict. The Numista
    # issuer chip is the most authoritative lineage signal when the
    # parser failed to extract a ruler string — pass it via the
    # `_numista_issuer` slot. Stripped before Coin() instantiation by
    # the build's underscore-field filter.
    routing_input = dict(entry)
    routing_input["_numista_issuer"] = canonical.get("issuer")
    routed_ent, hint = route_entity_with_rules(routing_input, default_entity=default_ent)
    entry["issuing_entity"] = routed_ent
    if hint is not None:
        entry["_entity_routing_hint"] = hint
    # Fold any «<km> (<Country>)» Krause-volume tag into the register-keyed km
    # form now that the entity (→ default register for bare values) is known.
    _apply_km_country_register(entry["catalog"], routed_ent)
    return entry


def collect_entries() -> tuple[list[dict[str, Any]], Counter]:
    """Walk all parsed sidecars, build Coin entries, return (entries,
    per-shape counter)."""
    entries: list[dict[str, Any]] = []
    by_shape: Counter = Counter()
    for path in sorted(PARSED_DIR.glob("*.json")):
        try:
            canonical = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(canonical, dict):
            continue
        entry = build_coin_entry(canonical)
        if entry is None:
            by_shape["skipped_incomplete"] += 1
            continue
        entries.append(entry)
        by_shape[canonical.get("_source_shape", "?")] += 1
    return entries, by_shape


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-merge", action="store_true",
                    help="Wholesale overwrite — destructive, verification only")
    args = ap.parse_args()

    if not PARSED_DIR.exists():
        print(f"ERROR: {PARSED_DIR} does not exist — run scripts/parse_numista.py first",
              file=sys.stderr)
        return 2

    entries, by_shape = collect_entries()
    print(f"Collected {len(entries)} entries from {PARSED_DIR}")
    print(f"By source-shape:")
    for k, v in by_shape.most_common():
        print(f"  {k}: {v}")

    by_entity: Counter = Counter()
    unclassified_samples: list[dict[str, Any]] = []
    for e in entries:
        ie = e.get("issuing_entity")
        if ie is None:
            by_entity["_unclassified"] += 1
            if len(unclassified_samples) < 12:
                unclassified_samples.append({
                    "id": e.get("id"),
                    "nominal": e.get("nominal"),
                    "year_first": e.get("year_first"),
                    "ruler": e.get("ruler"),
                    "mint": e.get("mint"),
                    "issuer_known": is_known_issuer(
                        # cant read canonical.issuer from here without re-parsing
                        # — sources URL carries N# so it's traceable to cache
                        e.get("ruler") or ""
                    ),
                })
        elif isinstance(ie, list):
            by_entity["_joint_" + "_".join(ie)] += 1
        else:
            by_entity[ie] += 1
    print(f"\nBy resolved entity:")
    for k, v in by_entity.most_common():
        print(f"  {k}: {v}")

    if unclassified_samples:
        print(f"\n_unclassified samples (first 12):")
        for s in unclassified_samples:
            print(f"  {s['id']}  {s['year_first']}  {s['nominal']!r}  ruler={s['ruler']!r}  mint={s['mint']!r}")

    write_v2_seed(
        entries,
        source_name="numista",
        source_label="Numista en.numista.com per-coin catalogue (API v3 + chrome scrape)",
        scope_note=(
            "Generic Numista Phase 3 seed — consumes canonical Phase 2 "
            "sidecars at scripts/cache/numista/parsed/. Mint-driven entity "
            "classification with issuer-string fallback when mint is "
            "absent. Numista is user-edited; cross-references (SIEG, "
            "Galster, Schou, Fr, MB, Lange, Dav) require primary-source "
            "verification before §BF promotion. Phase-2 driver: "
            "scripts/parse_numista.py."
        ),
        dry_run=args.dry_run,
        no_merge=args.no_merge,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
