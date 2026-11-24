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
from lib import uncertainty as unc  # noqa: E402
from lib.paths import NGC_CACHE  # noqa: E402
from lib.ruler_reigns import reign_window  # noqa: E402
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
    # Alloys named in full — matched BEFORE the leading-word fallback, which
    # would read «Aluminum-Bronze» as aluminium (2026-10-22: two Margrethe II
    # 10 / 20 Kroner prøvemønter came through as `aluminium`). Aluminium
    # bronze is a copper alloy: the nearest schema bucket is bronze, flagged
    # unverified because the string says more than the bucket.
    "aluminum-bronze": "bronze", "aluminium-bronze": "bronze",
    "aluminum bronze": "bronze", "aluminium bronze": "bronze",
}
_ALLOY_UNVERIFIED = {"aluminum-bronze", "aluminium-bronze", "aluminum bronze", "aluminium bronze"}

_DIAM_SINGLE = re.compile(r"^\s*([\d.]+)\s*mm\s*$", re.I)


def _metal(composition: str | None) -> tuple[str | None, bool]:
    if not composition:
        return None, False
    key = composition.strip().lower()
    if key in _METAL:
        return _METAL[key], key not in _ALLOY_UNVERIFIED
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
    for src_key, dst in (("behrens", "behrens"), ("dav", "dav"), ("fr", "fr"),
                         ("lange", "lange")):
        vals = [v.lstrip("#") for v in (refs.get(src_key) or [])]
        if not vals:
            continue
        if dst in cat:              # own index already occupies the field
            cat.setdefault("others", []).extend(f"{dst.upper()} {v}" for v in vals)
        else:
            cat[dst] = vals[0] if len(vals) == 1 else vals
    # Catalogues without a schema field, written as NGC prints them («Sch#»,
    # «S#» uninterpreted; curator 2026-10-30).
    for src_key, label in (("weinmeister", "Weinmeister"), ("sch", "Sch"), ("s", "S"),
                           ("meyer", "Meyer"), ("schoen", "Schön"), ("roeper", "Roeper")):
        for v in refs.get(src_key) or []:
            tok = f"{label}# {v}"
            if tok not in cat.setdefault("others", []):
                cat["others"].append(tok)
    return cat


# NGC scope (its Krause section, in the URL: /world/denmark-…, /world/norway-…)
# → the Krause volume it names. Only these two: the German-states sections are
# not mapped one-to-one onto our volume codes.
_KM_VOLUME_BY_SCOPE = {"denmark": "dk", "norway": "nor"}

# NGC's «Denmark» region also holds Krause sections that number on their own:
# the heading names them after the country word («Denmark GLÜCKSTADT 1/16
# Speciedaler KM# 26»). Their KM is NOT in the Denmark volume — Denmark KM 26
# is the 6 Speciedaler 1604 (NGC 1050248, NumisMaster 65594). GLÜCKSTADT has
# its own register (lib.km_registers «glu»), and so does every Krause section
# of a Schleswig-Holstein house, whether NGC files it under «Denmark»
# («Denmark HOLSTEIN-GOTTORP-RENDSBORG», KM 5-8 colliding with Glückstadt 5-8)
# or under «German States» («German States SCHLESWIG-HOLSTEIN-GOTTORP»)
# (lib.km_registers.KRAUSE_SECTIONS, curator 2026-11-23). Any other
# sub-section keeps a bare KM.
_SUBSECTION_RE = re.compile(
    r"^(?:Denmark|Norway|German States)\s+([A-ZÄÖÜÆØÅ][A-ZÄÖÜÆØÅ\-]{2,})\s")
from lib.km_registers import KRAUSE_SECTIONS as _KM_VOLUME_BY_SUBSECTION  # noqa: E402
# …and its issuer: the royal Holstein coinage struck at Glückstadt, as
# NumisMaster's country GLÜCKSTADT is routed (build_numismaster_seed).
# HOLSTEIN-GOTTORP-RENDSBORG: Frederik IV's coinage at Rendsburg 1716-1720
# (Hede 60-63), royal_holstein by the curator's 2026-07-29 ruling.
_ENTITY_BY_SUBSECTION = {"GLÜCKSTADT": "royal_holstein",
                         "HOLSTEIN-GOTTORP-RENDSBORG": "royal_holstein"}


def _subsection(heading: str | None) -> str | None:
    m = _SUBSECTION_RE.match(heading or "")
    return m.group(1) if m else None


def _km_volume(cat: dict, scope: str, heading: str | None = None) -> dict:
    """Write the KM register-keyed when the NGC section names the volume, so a
    record pulled into another entity keeps its own volume (lib.km_registers)."""
    sub = _subsection(heading)
    vol = (_KM_VOLUME_BY_SUBSECTION.get(sub) if sub
           else _KM_VOLUME_BY_SCOPE.get(scope))
    if vol and cat.get("km"):
        cat["km"] = {vol: cat["km"]}
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
    years_all = rec.get("years_all")
    after = rec.get("year_after")
    if after is not None:
        # «(after 1620)»: closed on the ruler's reign end when the reign table
        # knows the ruler for this house; otherwise the bound itself stands,
        # marked '(?)' below (curator, 2026-10-17).
        reign = reign_window(rec.get("ruler"),
                             house=SCOPE_ENTITY.get(scope, ""))
        if reign and reign[1] > after and reign[0] <= after + 1:
            yf, yl = after + 1, reign[1]
            years_all = list(range(yf, yl + 1))
    ranges = _year_ranges(years_all, yf, yl)
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
        "catalog": _km_volume(_catalog(rec), scope, rec.get("heading")),
        "metal": metal,
        "fineness": fineness,
        "weight_rough_g": weight,
        "diameter_mm": diam,
        "issuing_entity": (_ENTITY_BY_SUBSECTION.get(_subsection(rec.get("heading")))
                           or SCOPE_ENTITY.get(scope, "")),
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
        "_ngc_scope": scope,
        "_ngc_cuid": str(cuid),
    }

    # §4: an unread date digit ('166z') is NOT resolved into a year, and a coin
    # with no year at all cannot claim one — both render '(?)'. A Z-shaped 2
    # ('16Z4') IS read (parse_ngc._Z_YEAR); the cells as NGC printed them are
    # kept in `_ngc_dates_as_printed` so the reading stays auditable (§3a: the
    # year fields themselves carry plain digits only). An undated coin the
    # catalogue attributes to a span («(1618-22)») keeps the span; it takes
    # '(?)' only when NGC hedges it («(ca1611)»), not for a plain span.
    if (rec.get("year_partially_illegible") or rec.get("year_attributed")
            or yf is None):
        entry["year_verified"] = False
        # How NGC prints it, verbatim (Coin.uncertainty). A coin with no year
        # at all shows none, so it records nothing.
        printed = ("; ".join(rec.get("dates_as_printed") or [])
                   or "; ".join(d.get("year_mint") for d in rec.get("dates") or []
                                if isinstance(d, dict) and d.get("year_mint"))
                   or rec.get("date_line") or None)
        if yf is not None:
            if after is not None:
                how = "after"
            elif rec.get("year_partially_illegible"):
                how = "illegible"
            elif printed and re.search(r"\(\s*c(?:a)?\.?\s*\d", printed):
                how = "circa"
            else:
                how = "attributed"
            if how == "attributed" and (unc.plain_dating(printed)
                                        or unc.roman_dated(printed)):
                # «(1616-59)» / «ND (1747)»: NGC dates the undated coin without
                # a reservation of its own — a known year, no «(?)» (curator
                # 2026-11-19; a reign-equal range is caught by absorb's
                # reign-span rule). «MDCCLX (1760) G» is a dated coin whose
                # Roman date the cache (parsed before parse_ngc learnt
                # `roman_dated`) still flags as attributed.
                entry.pop("year_verified", None)
            else:
                unc.add(entry, "year", how, "ngc", as_printed=printed,
                        value=unc.year_value(yf, entry.get("year_last")))

    for key, dst in (("obverse", "_obverse"), ("reverse", "_reverse"),
                     ("obverse_legend", "_obverse_legend"),
                     ("reverse_legend", "_reverse_legend"),
                     ("note_raw", "_ngc_note"),
                     ("date_line", "_ngc_date_line"),
                     ("dates_as_printed", "_ngc_dates_as_printed")):
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
