#!/usr/bin/env python3
"""Build the V2 entity-keyed IKMK seed from the harvest cache.

Phase 3 (SEED) for IKMK Berlin — the 7th harvested source, and the last one
without a seed builder. Consumes the scope-purged + title-filtered cache
(`scripts/cache/ikmk/<mds_id>.json`, museum json_ext) and writes
`data/v2/seed/ikmk/<entity>.yml` — Coin-schema stubs (`fuss=seed_unsorted`,
verified flags reflecting IKMK attestation) that flow through the existing
cross-source merger (`merge_seeds_cross_source.py`) + Phase-4 classifier like
every other source.

No separate `parse_ikmk.py`: the cache IS typed JSON (json_ext), so this
builder reads it directly. Field mapping follows `docs/IKMK_HARVEST.md`.

Entity routing — each record's mint city (`mint[].mint_name_de`) →
`classify_mint_to_entity(mint, year)`; records whose mint is missing or not in
the registry route to `data/v2/seed/ikmk/_unclassified.yml` for curator review
(same convention as every other V2 builder). ~76 % of in-scope coins carry a
mint city.

§9 exclusions — only `item == 'Coin'` records enter; Medals / Minting Tools /
Models / Tokens / Paper Money are skipped (exonumia per §9.2, already largely
dropped at harvest by the entity-scope filter).

Verified flags — IKMK is a museum catalogue (§5 tier 2): when it populates a
field, that field IS source-attested, so `metal_verified` / `weight_rough_verified`
/ `diameter_mm_verified` / `mint_verified` are true when the value is present
(same pattern as the NumisMaster builder). `fineness` is not exposed by IKMK
(qualitative `material` only) → left absent.

Idempotent + merge-aware (`write_v2_seed` → `merge_seed`): re-runs preserve
curator edits and produce zero churn on unchanged input.

Usage:
    python scripts/maintenance/build_ikmk_seed.py                 # dry-run report
    python scripts/maintenance/build_ikmk_seed.py --write
    python scripts/maintenance/build_ikmk_seed.py --write --limit 50   # subset
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import IKMK_CACHE  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib.note_extract import source_note  # noqa: E402

# IKMK `material.material_name_de` → Coin.metal enum. Materials outside the enum
# (Zinn / Messing / Kupfer-Nickel / Aluminium / Weißmetall / Zinklegierung —
# all rare, ≤2 each, mostly post-1914 or token-ish) map to None → metal absent.
_METAL = {
    "Silber": "silver",
    "Gold": "gold",
    "Kupfer": "copper",
    "Billon": "billon",
    "Bronze": "bronze",
    "Blei": "lead",
}

# literatur catalogue authors → CatalogRefs typed key. Per-segment (split on
# ';'), the first matching author wins; the number is taken from "Nr. N" if
# present, else the segment's trailing number.
_CAT_AUTHORS = [
    (re.compile(r"\bHede\b", re.I), "hede"),
    (re.compile(r"\bDavenport\b", re.I), "dav"),
    (re.compile(r"\bLange\b", re.I), "lange"),
    (re.compile(r"\bSieg\b", re.I), "sieg"),
    (re.compile(r"\bSchou\b", re.I), "schou"),
    (re.compile(r"\bFriedberg\b", re.I), "fr"),
]

# §CJ-IKMK: extra catalogue authors our schema doesn't TYPE but which IKMK's
# prose `literatur` cites for the German entities — routed to `catalog.others`
# as «Label# Nr». CURATED + author↔catalogue verified against the literatur
# titles (2026-06-01): each surname here resolves to exactly ONE standard
# catalogue. Deliberately EXCLUDED (and why):
#   • Kluge, Bahrfeldt — each authored/edited MANY different works
#     (surname ≠ a single catalogue) → ambiguous, would mis-attribute;
#   • Schnee / Keilitz (Saxon Taler), Dannenberg (medieval), Noss (Jülich) —
#     out-of-mission-scope territories;
#   • Steguweit («Suum Cuique») — medals = exonumia (§9.2), not coin indices.
# Ambiguity-of-surname is the bar: only one-catalogue-per-surname authors map.
_EXTRA_CAT_AUTHORS = [
    (re.compile(r"\bBehrens\b"), "Behrens"),      # Münzen u. Medaillen Lübecks (1905)
    (re.compile(r"\bWelter\b"), "Welter"),        # Die Münzen der Welfen
    (re.compile(r"\bFiala\b"), "Fiala"),          # Münzen/Medaillen Welfische Lande
    (re.compile(r"\bDuve\b"), "Duve"),            # Braunschweig-Lüneburg Löser-Taler
    (re.compile(r"\bJesse\b"), "Jesse"),          # Münzen der Stadt Braunschweig
    (re.compile(r"\bDorfmann\b"), "Dorfmann"),    # Münzwesen Hzm. Lauenburg
    (re.compile(r"\bSchön\b"), "Schön"),          # Weltmünzkatalog 19. Jahrhundert
    (re.compile(r"\bJaeger\b"), "Jaeger"),        # Die deutschen Münzen seit 1871
    (re.compile(r"\bDivo\b"), "Divo"),            # Deutsche Goldmünzen 1800-1930
    (re.compile(r"\bArnold\b"), "AKS"),           # Arnold-Küthmann-Steinhilber (1800+)
    (re.compile(r"\bSchrötter\b"), "Schrötter"),  # Das preußische Münzwesen
    (re.compile(r"\bOlding\b"), "Olding"),        # Die Münzen Friedrichs des Großen
]

# «Nr. N» extractor for the extra authors — handles plain («471»), letter-suffix
# sub-variants («90 a», «552 A»), and Olding's K-numbers («K 16.2/3746»). The
# trailing-letter group requires a word boundary (negative lookahead) so it
# captures the sub-variant «a» in «90 a» but NOT the «u» of «90 und 91».
_EXTRA_NR_RE = re.compile(
    r"\bNr\.\s*([A-Za-z]{0,2}\s?\d[\d.\-/]*(?:\s?[A-Za-z](?![A-Za-z]))?)"
)


def _first(x):
    """First dict in a list-or-dict field (IKMK shapes vary)."""
    while isinstance(x, list):
        x = x[0] if x else {}
    return x if isinstance(x, dict) else {}


def _num(s):
    """'3.43 g' / '23 mm' → float; None otherwise."""
    if not isinstance(s, str):
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    return float(m.group(1).replace(",", ".")) if m else None


def _is_coin(rec) -> bool:
    item = _first(rec.get("item")).get("item_en")
    div = _first(rec.get("division")).get("division_name_en")
    return item == "Coin" and div != "Medals"


def _mint_city(rec):
    mn = (_first(rec.get("mint")).get("mint_name_de")
          or _first(rec.get("mint")).get("mint_name") or "").strip()
    # Strip "(modern name)" parentheticals + trailing uncertainty mark:
    # "Neuenburg (Neuchâtel)" → "Neuenburg"; "Annaberg?" → "Annaberg".
    mn = re.sub(r"\s*\([^)]*\)\s*$", "", mn).strip().rstrip("?").strip()
    return mn or None


def _person(rec, rel):
    block = (rec.get("linked_persons_corporations") or {}).get(rel)
    if not isinstance(block, dict):
        return None
    items = block.get("items") or {}
    pid = next(iter(items), None)
    if not pid:
        return None
    p = items[pid]
    return (p.get("last_name_de") or "").strip(), (p.get("first_name_de") or "").strip()


def _ruler(rec):
    pr = _person(rec, "57") or _person(rec, "54")  # Authority, then Sitter
    if not pr:
        return None
    last, _f = pr
    # "Frederik III. (1648-1670), König von …" → "Frederik III."
    name = re.split(r"\s*[(,]", last)[0].strip()
    return name or None


def _mintmaster(rec):
    pr = _person(rec, "55")
    if not pr:
        return None
    last, first = pr
    return (f"{first} {last}".strip() if first else last) or None


def _inscriptions(rec):
    obv = (_first(rec.get("avers")).get("leg_text") or "").strip() or None
    rev = (_first(rec.get("revers")).get("leg_text") or "").strip() or None
    return obv, rev


def _catalog(rec) -> dict:
    lit = rec.get("literatur")
    if not isinstance(lit, str) or not lit.strip():
        return {}
    out: dict = {}
    others: list = []
    for seg in lit.split(";"):
        # «Vgl. …» introduces a cf-reference (a SIMILAR other coin), never this
        # coin's own catalogue index — drop everything from the first «Vgl.»
        # onward (anti-pattern 5). It can sit mid-segment («… Nr. 471. Vgl. F.
        # v. Schrötter …»), not only at the start, so truncate rather than skip
        # — otherwise the cf author/number leaks into the wrong field.
        seg = re.split(r"\bvgl\.", seg, maxsplit=1, flags=re.I)[0].strip()
        if not seg:
            continue
        # Typed schema catalogues (first-occurrence wins per key) — unchanged.
        for rx, key in _CAT_AUTHORS:
            if key in out or not rx.search(seg):
                continue
            m = re.search(r"\bNr\.\s*(\d+[A-Za-z]?)", seg)
            if not m:
                m = re.search(r"(\d+[A-Za-z]?)\s*\.?\s*$", seg)
            if m:
                out[key] = m.group(1)
        # §CJ-IKMK: extra German-states catalogues → others «Label# Nr».
        for rx, label in _EXTRA_CAT_AUTHORS:
            if not rx.search(seg):
                continue
            m = _EXTRA_NR_RE.search(seg)
            if m:
                val = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".,;").strip()
                tok = f"{label}# {val}"
                if tok and tok not in others:
                    others.append(tok)
            break  # one extra catalogue per segment
    if others:
        out["others"] = others
    return out


_VNOTE = {
    "de": ("IKMK-Seed: Datensatz aus dem Interaktiven Katalog des Münzkabinetts "
           "Berlin (ikmk.smb.museum, CC BY-SA 4.0). Felder museumsbelegt; "
           "Müntzfuß/Phase noch unklassifiziert (seed_unsorted) bis zur "
           "Phase-4-Zuordnung."),
    "en": ("IKMK seed: record from the Berlin Münzkabinett online catalogue "
           "(ikmk.smb.museum, CC BY-SA 4.0). Fields museum-attested; Münzfuß/"
           "phase unclassified (seed_unsorted) pending Phase-4 assignment."),
    "uk": ("IKMK-сід: запис з онлайн-каталогу Münzkabinett Berlin "
           "(ikmk.smb.museum, CC BY-SA 4.0). Поля музейно-засвідчені; "
           "Müntzfuß/фаза некласифіковані (seed_unsorted) до Phase-4."),
}


def build_entry(rec) -> dict | None:
    if not _is_coin(rec):
        return None
    mds = rec.get("ikmk_mds_id")
    if not mds:
        return None
    try:
        yf = int(rec.get("year_start"))
    except (TypeError, ValueError):
        yf = None
    try:
        yl = int(rec.get("year_end")) or yf
    except (TypeError, ValueError):
        yl = yf

    # Era scope gate (CLAUDE.md mission lower-bound 1481 / upper 1914). IKMK
    # full-text queries pull in medieval (Denar / Örtug «MA», Gotland) +
    # post-1914 modern records; drop the clearly out-of-scope ones. Undated
    # (yf is None) is KEPT — it may be an in-scope coin the parser couldn't
    # date; the finer dual-anchor (DK 1514 / German 1559) is left to Phase-4
    # classification since these are seed_unsorted.
    if yf is not None and (yf < 1481 or yf > 1914):
        return None

    mint = _mint_city(rec)
    entity = classify_mint_to_entity(mint, year=yf) if mint else None
    metal = _METAL.get(_first(rec.get("material")).get("material_name_de"))
    w = _num(rec.get("weight"))
    d = _num(rec.get("diameter"))
    obv, rev = _inscriptions(rec)
    catalog = _catalog(rec)

    if yf is not None and yl is not None and yf == yl:
        year_label = str(yf)
    elif yf is not None:
        year_label = f"{yf}-{yl}"
    else:
        year_label = None

    entry: dict = {
        "id": f"ikmk-{mds}",
        "fuss": "seed_unsorted",
        "phase": "ikmk",
        "kind": "kurant",
        "issuing_entity": entity,           # None → _unclassified.yml
        "nominal": _first(rec.get("nominal")).get("nominal_de"),
        "metal": metal,
        "metal_verified": metal is not None,
        "mint": mint,
        "mint_verified": mint is not None,
        "ruler": _ruler(rec),
        "mintmaster": _mintmaster(rec),
        "year_first": yf,
        "year_last": yl,
        "year_label": year_label,
        "year_ranges": [[yf, yl]] if yf is not None else None,
        "inscription_obv": obv,
        "inscription_rev": rev,
        "weight_rough_g": w,
        "weight_rough_verified": w is not None,
        "diameter_mm": d,
        "diameter_mm_verified": d is not None,
        "catalog": catalog or None,
        "verified": False,
        "sources": [{
            "type": "museum",
            "url": rec.get("permalink") or f"https://ikmk.smb.museum/object?id={mds}",
            "ref": "IKMK Berlin " + str(mds) + (
                f" (Inv. {rec['inventory_number'].strip()})"
                if (rec.get("inventory_number") or "").strip() else ""),
        }],
        "verification_note": _VNOTE,
    }
    # _source_note candidate (Phase-1, commit 80a1b62): IKMK's `comment`
    # (German), cleaned + language-tagged for the later note-selector. Non-schema
    # (underscore) → stripped before the strict Coin schema at final/render.
    # Wiring here (the deferred follow-up) makes a re-seed reproduce it durably
    # instead of dropping the one-off population. None → filtered out below.
    entry["_source_note"] = source_note(rec.get("comment"), "de")
    # Drop None-valued keys (writer + merge tolerate absence; keeps seed clean).
    return {k: v for k, v in entry.items() if v is not None}


def build_seed(dry_run: bool, no_merge: bool, limit: int | None,
               no_thin: bool = False) -> int:
    files = sorted(p for p in IKMK_CACHE.glob("*.json") if not p.stem.startswith("_"))
    entries: list[dict] = []
    scanned = skipped_noncoin = 0
    for p in files:
        if limit is not None and scanned >= limit:
            break
        scanned += 1
        try:
            rec = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        e = build_entry(rec)
        if e is None:
            skipped_noncoin += 1
            continue
        entries.append(e)

    classified = sum(1 for e in entries if e.get("issuing_entity"))
    print(f"  scanned {scanned} cache files → {len(entries)} coin entries "
          f"({skipped_noncoin} non-coin skipped); "
          f"{classified} entity-classified, {len(entries) - classified} → _unclassified")

    scope_note = (
        "IKMK Berlin seed — records from the Interaktiver Katalog des "
        "Münzkabinetts Berlin (ikmk.smb.museum, CC BY-SA 4.0), built directly "
        "from the museum json_ext cache (scope-purged + title-filtered at "
        "harvest). Coin-only (§9.2 exonumia excluded). Mint city → issuing "
        "entity via classify_mint_to_entity; museum-attested fields carry "
        "verified=true. Phase-4 assigns Müntzfuß/phase; cross-source merger "
        "deduplicates against Hede/Bruun/Numista/etc."
    )
    write_v2_seed(
        entries,
        source_name="ikmk",
        source_label="IKMK Berlin (ikmk.smb.museum, json_ext)",
        scope_note=scope_note,
        dry_run=dry_run,
        no_merge=no_merge,
    )
    # §9a thinning of over-sampled IKMK sub-variants. IKMK over-samples common
    # types (one «1/24 Taler» 1619 sub-variant had 734 specimens). Thin ALL
    # ≥5-specimen buckets to the min/middle/max envelope (catalogued_only=False
    # per curator direction 2026-06-24): an uncatalogued museum record carries
    # no distinguishing signal beyond the sub-variant key + weight, so dropping
    # the redundant specimens loses nothing our data model can tell apart.
    # Integrated here so a single --write is self-filtering + idempotent.
    if not dry_run and not no_thin:
        print("\n🪶 Thinning over-sampled sub-variants to §9a envelope...")
        from lib.seed_thin import thin_seed_dir
        seed_dir = Path(__file__).resolve().parents[2] / "data" / "v2" / "seed" / "ikmk"
        thin_seed_dir(seed_dir, catalogued_only=False, dry_run=False)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="persist (default: dry-run)")
    ap.add_argument("--no-merge", action="store_true",
                    help="wholesale overwrite (skip merge_seed curation preservation)")
    ap.add_argument("--limit", type=int, default=None, help="process only N cache files (subset test)")
    ap.add_argument("--no-thin", action="store_true",
                    help="skip the §9a over-sample thinning post-pass "
                         "(emit the raw per-specimen seed)")
    args = ap.parse_args()
    return build_seed(dry_run=not args.write, no_merge=args.no_merge,
                      limit=args.limit, no_thin=args.no_thin)


if __name__ == "__main__":
    raise SystemExit(main())
