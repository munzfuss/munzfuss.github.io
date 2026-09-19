#!/usr/bin/env python3
"""NGC World Coin Price Guide — Phase 3 SEED.

Reads the Phase-2 sidecars (`scripts/cache/ngc/<scope>/cuid_<N>.parsed.json`,
written by `scripts/parse_ngc.py`) and emits entity-keyed seed yamls at
`data/v2/seed/ngc/<entity>.yml`, with every entry marked
`fuss: seed_unsorted` / `phase: ngc`.

**This builder does not classify.** Müntzfuß, phase and kind are curator
decisions taken later against `merge_decisions/` + `classification_decisions/`;
everything here lands as an unsorted seed. Nor does it filter for scope: the
shared pre-write hygiene in `lib/v2_seed_writer` already drops Krause `Pn*`/`TS*`
pattern and trial strikes (§9.1), coins starting after 1914, and out-of-scope
Asian trade nominals — duplicating that here would risk the two disagreeing.

Curation survives regeneration for free: `write_v2_seed` routes every per-entity
write through `lib.seed_merge.merge_seed`, so curator-set `fuss` / `phase` /
`issuing_entity` / `*_verified` flags are preserved and entries the parser no
longer produces stay as orphan-curated rather than vanishing.

Usage::

    python scripts/maintenance/build_ngc_seed.py [--dry-run] [--scope luebeck]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.entity_routing import route_entity_with_rules  # noqa: E402
from lib.paths import NGC_CACHE  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

# NGC region -> default issuing_entity. The region IS the polity: NGC splits
# Schleswig-Holstein politically, with zero overlap between the cadet lines
# (SOURCES.md §13.13(e)), so the scope name is a real provenance signal rather
# than a geographic bucket. `route_entity_with_rules` then refines this the same
# way it does for the NumisMaster / Numista builders.
#
# `luebeck` deliberately defaults to the CITY. NGC does not separate the Free
# City from the Prince-Bishopric — both sit in one region — and while bishopric
# issues do tend to carry a `Ruler`, splitting on that alone would be a guess
# dressed as a rule (§0b). The scope is recorded on every entry as
# `_ngc_scope`, so a curator (or a later routing rule) can make the call on
# evidence rather than on this builder's hunch.
SCOPE_ENTITY: dict[str, str] = {
    "denmark": "danish_realm",
    "norway": "danish_norway",
    "luebeck": "hanseatic_lubeck",
    "schleswig_holstein": "royal_holstein",
    "schleswig_holstein_gottorp": "gottorp_duchy",
    "schleswig_holstein_sonderburg": "sonderburg_duchy",
    "schleswig_holstein_ploen": "norburg_plon_duchy",
    "schleswig_holstein_norburg": "norburg_plon_duchy",
    "schleswig_holstein_glucksburg": "glucksburg_duchy",
    "schaumburg_pinneberg": "schauenburg_pinneberg",
    "rantzau": "rantzau_county",
}

# NGC's `Composition` is a plain metal word, so this is a mapping and not a
# heuristic — an unrecognised value leaves metal unset with the flag false
# rather than being guessed into the nearest bucket (§4).
_METAL = {
    "silver": "silver", "gold": "gold", "copper": "copper", "billon": "billon",
    "bronze": "bronze", "brass": "brass", "tin": "tin", "zinc": "zinc",
    "lead": "lead", "iron": "iron", "aluminum": "aluminium",
    "aluminium": "aluminium", "nickel": "nickel", "pewter": "pewter",
    "platinum": "platinum", "silver plated": "silver", "gold plated": "gold",
}

_DIAM_SINGLE = re.compile(r"^\s*([\d.]+)\s*mm\s*$", re.I)


def _metal(composition: str | None) -> tuple[str | None, bool]:
    if not composition:
        return None, False
    key = composition.strip().lower()
    if key in _METAL:
        return _METAL[key], True
    # e.g. "Copper-Nickel", "Silver, .875" — take the leading metal word but do
    # NOT claim it as attested, since the string says more than we captured.
    head = re.split(r"[,\-/(]", key)[0].strip()
    return (_METAL.get(head), False) if head in _METAL else (None, False)


def _diameter(raw: str | None) -> tuple[float | None, str | None]:
    """Single measurement -> float; a RANGE ('39-40mm') stays unparsed.

    Picking a value out of a published range would invent a precision the
    source does not give (§3). The raw string is kept so nothing is lost.
    """
    if not raw:
        return None, None
    m = _DIAM_SINGLE.match(raw)
    if m:
        try:
            return float(m.group(1)), None
        except ValueError:
            pass
    return None, raw.strip()


def _year_ranges(years: list[int] | None, yf: int | None, yl: int | None):
    if years:
        out: list[list[int]] = []
        for y in sorted(set(years)):
            if out and y == out[-1][1] + 1:
                out[-1][1] = y
            else:
                out.append([y, y])
        return out
    if yf is None:
        return None
    return [[yf, yl if yl is not None else yf]]


def _year_label(ranges) -> str | None:
    if not ranges:
        return None
    return ", ".join(str(a) if a == b else f"{a}–{b}" for a, b in ranges)


def _nominal(heading: str | None) -> str | None:
    """Denomination out of 'German States LÜBECK 1/128 Thaler KM# A9'.

    Strip the leading country/region words and the trailing catalogue token;
    what remains is the denomination as NGC states it.
    """
    if not heading:
        return None
    s = re.sub(r"\s*\b(?:KM|MB|FR|C)#\s*[\w.]+\s*$", "", heading).strip()
    s = re.sub(r"^German States\s+", "", s, flags=re.I)
    s = re.sub(r"^(Denmark|Norway)\s+", "", s, flags=re.I)
    # a remaining ALL-CAPS region word (LÜBECK, GLÜCKSTADT) is not part of the
    # denomination
    s = re.sub(r"^[A-ZÄÖÜÆØÅ][A-ZÄÖÜÆØÅ\-\s]{2,}?\s+(?=[\d½¼¾]|[A-Z][a-z])", "", s)
    return s.strip() or None


def _catalog(rec: dict) -> dict:
    cat: dict = {}
    own = rec.get("catalog_own") or {}
    for scheme, val in own.items():
        if scheme in ("km", "mb", "fr"):
            cat[scheme] = val
        else:                       # 'c' (Christensen) has no schema field
            cat.setdefault("others", []).append(f"{scheme.upper()} {val}")
    refs = rec.get("catalog_refs") or {}
    for src_key, dst in (("behrens", "behrens"), ("dav", "dav"), ("fr", "fr")):
        vals = [v.lstrip("#") for v in (refs.get(src_key) or [])]
        if not vals:
            continue
        if dst in cat:              # own index already occupies the field
            cat.setdefault("others", []).extend(f"{dst.upper()} {v}" for v in vals)
        else:
            cat[dst] = vals[0] if len(vals) == 1 else vals
    return cat


def build_entry(rec: dict, scope: str) -> dict | None:
    cuid = rec.get("cuid")
    if not cuid:
        return None
    nominal = _nominal(rec.get("heading"))
    if not nominal:
        return None
    metal, metal_ok = _metal(rec.get("composition"))
    diam, diam_raw = _diameter(rec.get("diameter_raw"))
    yf, yl = rec.get("year_first"), rec.get("year_last")
    ranges = _year_ranges(rec.get("years_all"), yf, yl)
    fineness = rec.get("fineness")
    weight = rec.get("weight_g")
    flags = rec.get("flags") or {}
    mint = flags.get("struck_at") or rec.get("mint")

    entry: dict = {
        "id": f"ngc-{cuid}",
        "fuss": "seed_unsorted",
        "phase": "ngc",
        "kind": "kurant",
        "nominal": nominal,
        "year_label": _year_label(ranges),
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": ranges,
        "ruler": rec.get("ruler"),
        "mint": mint,
        "catalog": _catalog(rec),
        "metal": metal,
        "fineness": fineness,
        "weight_rough_g": weight,
        "diameter_mm": diam,
        "issuing_entity": SCOPE_ENTITY.get(scope, ""),
        "verified": False,
        "metal_verified": metal_ok,
        "fineness_verified": fineness is not None,
        "weight_rough_verified": weight is not None,
        "diameter_mm_verified": diam is not None,
        "mint_verified": bool(mint),
        "sources": [{
            "type": "literature",
            "url": rec.get("url"),
            "ref": "NGC World Coin Price Guide (powered by NumisMaster)",
        }],
        "verification_note": {
            "de": ("NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, "
                   "Nachfolger des eingestellten NumisMaster. Per-Münze-"
                   "Verifikation gegen Primärquellen vor der Promotion."),
            "en": ("NGC seed: World Coin Price Guide, Krause-Mishler-based, "
                   "successor to the discontinued NumisMaster. Per-coin "
                   "verification against primary sources before promotion."),
            "uk": ("NGC-seed: World Coin Price Guide, на основі Krause-Mishler, "
                   "наступник закритого NumisMaster. Покоінна верифікація "
                   "проти первинних джерел перед промоцією."),
            "da": ("NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, "
                   "efterfølger til det nedlagte NumisMaster. Verifikation af "
                   "den enkelte mønt mod primærkilder før optagelse."),
        },
        "_ngc_scope": scope,
        "_ngc_cuid": str(cuid),
    }

    # §4: an unreadable date digit ('16z4') is NOT resolved into a year, and a
    # coin with no year at all cannot claim one — both render '(?)'.
    if rec.get("year_partially_illegible") or yf is None:
        entry["year_verified"] = False

    for key, dst in (("obverse", "_obverse"), ("reverse", "_reverse"),
                     ("obverse_legend", "_obverse_legend"),
                     ("reverse_legend", "_reverse_legend"),
                     ("note_raw", "_ngc_note"),
                     ("date_line", "_ngc_date_line")):
        if rec.get(key):
            entry[dst] = rec[key]
    if diam_raw:
        entry["_ngc_diameter_raw"] = diam_raw
    # The renumbering trail is the coin's FORMER index, not its current one, so
    # it must not sit in `catalog` (anti-pattern 5). Kept alongside for the §9.4
    # index-graph work.
    prev = (rec.get("catalog_refs") or {}).get("previous_km")
    if prev:
        entry["_ngc_previous_km"] = prev
    if flags:
        keep = {k: v for k, v in flags.items() if k != "struck_at"}
        if keep:
            entry["_ngc_flags"] = keep

    routed, hint = route_entity_with_rules(
        dict(entry), default_entity=entry["issuing_entity"])
    entry["issuing_entity"] = routed
    if hint is not None:
        entry["_entity_routing_hint"] = hint
    return entry


def collect(scopes: list[str] | None) -> list[dict]:
    coins: list[dict] = []
    for d in sorted(p for p in NGC_CACHE.iterdir() if p.is_dir()):
        scope = d.name
        if scopes and scope not in scopes:
            continue
        if scope not in SCOPE_ENTITY:
            print(f"  [skip] {scope}: no entity mapping")
            continue
        files = sorted(d.glob("cuid_*.parsed.json"))
        n = 0
        for f in files:
            e = build_entry(json.loads(f.read_text(encoding="utf-8")), scope)
            if e:
                coins.append(e)
                n += 1
        if files:
            print(f"  {scope:<32} {n}/{len(files)} entries")
    return coins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scope", help="comma-separated cache scopes to build")
    args = ap.parse_args()

    scopes = args.scope.split(",") if args.scope else None
    print("Collecting NGC parsed sidecars…")
    coins = collect(scopes)
    print(f"\ntotal entries built: {len(coins)}")
    if not coins:
        return 1
    stats = write_v2_seed(
        coins, "ngc",
        "NGC World Coin Price Guide (powered by NumisMaster) — Danish realm, "
        "Norway under the Danish crown, Lübeck and the Schleswig-Holstein "
        "polities; harvested 1480-1914 (Norway to 1814).",
        source_label="ngc",
        dry_run=args.dry_run,
        extra_curated_fields=frozenset({"_ngc_previous_km", "_ngc_flags"}),
    )
    print(f"\nentities written: {len(stats['entities_written'])}")
    for ent, s in sorted(stats["per_entity"].items()):
        print(f"  {ent:<38} total={s['total']:<5} new={s['added_new']:<5} "
              f"merged={s['merged_existing']:<5} orphan={s['orphan_curated']}")
    if stats.get("unclassified_count"):
        print(f"  _unclassified: {stats['unclassified_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
