#!/usr/bin/env python3
"""Build the V2 entity-keyed KMK seed from the harvest cache.

Phase 3 (SEED) for KMM Copenhagen — the 8th harvested source. Consumes the
nation-scoped whole-record cache (`scripts/cache/kmk/<id>.json`, the museum
`_source` JSON) and writes `data/v2/seed/kmk/<entity>.yml` — Coin-schema
stubs (`fuss=seed_unsorted`) that flow through the existing cross-source
merger + Phase-4 classifier like every other source.

No separate `parse_kmk.py`: the cache IS typed JSON, so this builder reads it
directly. Field mapping follows `docs/KMK_HARVEST.md`.

Entity routing — mint city (`place`) → `classify_mint_to_entity` (precise);
when no mint, the Danish-language realm (`nation`) → `classify_nation_to_entity`
(coarse fallback, ~73% of records). Provenance recorded in
`entity_classified_via` ("mint" | "nation"). Records that resolve to no entity
route to `data/v2/seed/kmk/_unclassified.yml` for curator review.

§9 exclusions — `workDescription` of `Medalje` (medal) / `Regnepenning`
(reckoning jeton) are dropped (§9.2 exonumia). Era gate (mission lower bound
1481 / upper 1914) drops clearly out-of-scope records; undated kept.

Verified flags — KMM is a museum catalogue (§5 tier 2): when it populates a
field that field IS source-attested → `metal_verified` / `weight_rough_verified`
/ `mint_verified` true when present. KMM records NO diameter and NO fineness
(qualitative `materials` only) → both left absent.

Idempotent + merge-aware (`write_v2_seed` → `merge_seed`).

Usage:
    python scripts/maintenance/build_kmk_seed.py                 # dry-run report
    python scripts/maintenance/build_kmk_seed.py --write
    python scripts/maintenance/build_kmk_seed.py --write --limit 200
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import KMK_CACHE  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
from lib.mint_registry import (  # noqa: E402
    classify_nation_to_entity, display_for_alias,
)
from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib.ruler_reigns import reign_window  # noqa: E402

# Non-coin / exonumia object types (§9.2 medals · jetons · tokens; §9.3
# off-strikes; plus banknotes · dies · tools · misc). KMM's `workDescription`
# is a controlled vocab — a genuine coin LEADS with «Mønt» («Mønt», «Mønt,
# medalje», «Møntimitation», «Mønt, falsk» stay). Anything that leads with one
# of these object types — or contains «afslag» (off-strike) anywhere, incl.
# «Mønt, afslag» — is excluded from the coin table. (Verified 2026-06-09: ~637
# such records were rendering as phantom coin rows, ~332 of them nominal-less
# «(?)» rows — the KMM source has no denomination for non-coins.)
_EXONUMIA_WORKDESC_LEAD = (
    "medalje", "medaljør", "medaille", "jeton", "regnepenning", "andet",
    "seddel", "polet", "stempel", "plakette", "emblem", "relief",
)


def _is_exonumia_workdesc(wd: str | None) -> bool:
    w = (wd or "").strip().lower()
    if not w:
        return False
    if "afslag" in w:          # off-strike (§9.3) — also «Mønt, afslag»
        return True
    return any(w.startswith(lead) for lead in _EXONUMIA_WORKDESC_LEAD)

# Catalogue-author prefix in `typeNumber` → CatalogRefs key. KMM writes these
# heavily ABBREVIATED («H. 71» = Hede, «G. 23b» = Galster, «Sch 54» = Schou),
# often in a multi-field colon form («H: 134B; Sch: -», the «-» = not listed),
# and only sometimes spelled out. The prefix matcher therefore accepts both
# the abbreviation and the full name. Single-letter abbreviations are mapped
# only where unambiguous in the Danish-cabinet convention (H=Hede, G=Galster,
# L=Lange); ambiguous «S»/«B» are NOT mapped (Sieg/Schou, Behrens/Bergsøe).
# «Hbg» (Hauberg, medieval) + Welter/Behrens/Jesse/Fiala/Th(omsen) have no
# CatalogRefs slot → intentionally unmapped.
_CAT_PREFIX = [
    (re.compile(r"^(?:hede|he|h)$", re.I), "hede"),
    (re.compile(r"^(?:schou|sch)$", re.I), "schou"),
    (re.compile(r"^(?:galster|gal|g)$", re.I), "galster"),
    (re.compile(r"^(?:lange|l)$", re.I), "lange"),
    (re.compile(r"^(?:davenport|dav)$", re.I), "dav"),
    (re.compile(r"^sieg$", re.I), "sieg"),
    (re.compile(r"^(?:friedberg|fr)$", re.I), "fr"),
    (re.compile(r"^mb$", re.I), "mb"),
    # Regional catalogues surfaced by KMM (abbrev → schema key).
    (re.compile(r"^(?:thomsen|th)$", re.I), "thomsen"),
    (re.compile(r"^(?:bergsøe|bergsoe|bgs)$", re.I), "bergsoe"),
    (re.compile(r"^(?:hauberg|hbg)$", re.I), "hauberg"),
    (re.compile(r"^aagaard$", re.I), "aagaard"),
    (re.compile(r"^welter$", re.I), "welter"),
    (re.compile(r"^fiala$", re.I), "fiala"),
    (re.compile(r"^behrens$", re.I), "behrens"),
    (re.compile(r"^gaedechens$", re.I), "gaedechens"),
    (re.compile(r"^jesse$", re.I), "jesse"),
    (re.compile(r"^kreber$", re.I), "kreber"),
]


def _int(s):
    """First integer in a string/number, else None. KMM years are strings."""
    if isinstance(s, int):
        return s
    if not isinstance(s, str):
        return None
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else None


def _metal(src):
    """First `materials[].material` string → Coin.metal enum (dirty-string
    normaliser per docs/KMK_HARVEST.md). Compound silver-copper → billon."""
    mats = src.get("materials") or []
    raw = ""
    if mats and isinstance(mats[0], dict):
        raw = (mats[0].get("material") or "")
    s = raw.strip().lower().replace("(?)", "").replace("?", "").strip()
    if not s:
        return None
    if ("sølv" in s and "kobber" in s) or "kobberholdigt" in s or "billon" in s:
        return "billon"
    tok = re.split(r"[\s,/–-]+", s)[0]
    return {
        "sølv": "silver", "guld": "gold", "kobber": "copper",
        "bronze": "bronze", "bly": "lead", "ar": "silver", "æ": "bronze",
    }.get(tok)


def _ruler(src):
    a = (src.get("authority") or "").strip()
    if not a:
        return None
    # Strip a trailing "(1648-1670)" / ", konge …" tail if present.
    return re.split(r"\s*[(,]", a)[0].strip() or None


def _split_place(src):
    """`place` → (mint_city_or_None, mintmaster_or_None).

    KMM `place` is `City[, mintmaster]` (e.g. "Lund, Bosi") OR a bare region
    ("Holsten", "Danmark"). A region is NOT a mint — detected by the nation
    classifier recognising it — so it yields mint=None (routing falls back to
    `nation`). A known mint city is canonicalised; an unknown city is kept
    verbatim.
    """
    place = (src.get("place") or "").strip()
    if not place:
        return None, None
    head, _, tail = place.partition(",")
    head, tail = head.strip(), tail.strip()
    mintmaster = tail or None
    # A place may be a name-variant pair («Christiania / Oslo» = one mint, two
    # names) or an «A eller B» alternative — take the first mint-name segment so
    # both the mint field and the entity routing use a single canonical city.
    first = re.split(r"\s*/\s*|\s+(?:eller|or)\s+", head, flags=re.IGNORECASE)[0].strip()
    if not first:
        return None, mintmaster
    # Region (not a mint city) → drop from mint field; routing falls to nation.
    if classify_mint_to_entity(first) is None and classify_nation_to_entity(first):
        return None, mintmaster
    canon = display_for_alias(first)
    return (canon or first or None), mintmaster


# KMM data-quality: 25 cache records carry a creationEvent whose
# `yearFrom` is LATER than `yearTo` (raw inversion). Two sub-patterns,
# cleanly separated by the implied span:
#   - ordering slip — both years plausible, just swapped (span ≤ ~10y:
#     «1692/1682» → 1682-1692). Recover by swapping.
#   - typo / impossible value — one year is garbage (span ≥ ~27y:
#     Hans hvid «1581/1513» = 68y, since Hans †1513; truncated
#     «1518/152» = 1366y). Swapping keeps the bad value, so DROP the
#     event's year instead of propagating it (the specimen still merges
#     and contributes weight/source per §9a; an undated specimen no
#     longer widens a foundation's reign window — e.g. galster-hg-31).
# Threshold 20 sits in the empty gap between the two clusters (max
# ordering-slip span 10, min typo span 27).
_INVERTED_EVENT_SWAP_MAX_SPAN = 20

# KMM data-quality #2: a creationEvent year is occasionally a typo with an
# extra (or missing) digit — «1613»→«16113», «1689»→«16890», «1813»→«11813»,
# «1708»→«17089». The bad value is an impossible year; left in place it
# widens the coin's span to e.g. 1613-16113, which the timeline clamps to
# its right edge (1914), painting a spurious minting period across centuries
# (caught 2026-06-12 on Denmark 9-/9¼-/18½-Thaler bars). Any endpoint
# outside this window is treated as a typo and DROPPED (the plausible
# endpoint still anchors the coin). The broad century estimates KMM uses for
# undated coins — «1500-1750», «1600-1799», «1536-1869» — sit inside the
# window AND always carry an empty/absent `authority`, so they are NOT
# affected; they remain legitimate wide datings.
_MIN_PLAUSIBLE_YEAR = 900
_MAX_PLAUSIBLE_YEAR = 2025


def _year(src):
    """creationEvents[].yearFrom/yearTo (strings) → (yf, yl, year_verified).

    When a malformed event's year is dropped and NO usable year remains,
    fall back to the named ruler's reign window (year_verified=False)
    rather than leaving the coin year-less: the merger needs a year as a
    fallback signal to attach a museum specimen to its type (two same-Hede
    specimens lacking any other fallback else fail to merge — caught
    2026-06-11 on Christian-IV Hede-67 2-Skilling specimens). The reign
    window is plausible-but-estimated, so it does not propagate the
    garbage value while still letting §9a multi-specimen merges fire."""
    evs = src.get("creationEvents") or []
    yfs, yls = [], []
    malformed = False
    for e in evs:
        if not isinstance(e, dict):
            continue
        a, b = _int(e.get("yearFrom")), _int(e.get("yearTo"))
        # Magnitude sanity: an endpoint outside [_MIN, _MAX] is a digit-typo
        # («1613»→«16113»). Drop it so it cannot widen the coin's span to an
        # impossible year; the plausible endpoint still anchors the coin.
        if a is not None and not (_MIN_PLAUSIBLE_YEAR <= a <= _MAX_PLAUSIBLE_YEAR):
            a, malformed = None, True
        if b is not None and not (_MIN_PLAUSIBLE_YEAR <= b <= _MAX_PLAUSIBLE_YEAR):
            b, malformed = None, True
        # Per-event raw inversion (yearFrom > yearTo) is a KMM data error.
        if a is not None and b is not None and a > b:
            if a - b <= _INVERTED_EVENT_SWAP_MAX_SPAN:
                a, b = b, a            # ordering slip → swap
            else:
                malformed = True
                continue               # typo / impossible value → drop event
        if a is not None:
            yfs.append(a)
        if b is not None:
            yls.append(b)
    yf = min(yfs) if yfs else None
    yl = max(yls) if yls else (yf if yf is not None else None)
    if yf is not None and yl is not None and yl < yf:
        yf, yl = yl, yf
    if yf is None and malformed:
        reign = reign_window(src.get("authority"))
        if reign:
            return reign[0], reign[1], False   # reign-window estimate
    return yf, yl, True


def _weight(src):
    """First measurement with dimension Vægt (Gram) → float. KMM has only
    weight (no diameter)."""
    for m in (src.get("measurements") or []):
        if isinstance(m, dict) and m.get("dimension") == "Vægt":
            d = m.get("data")
            if isinstance(d, (int, float)):
                return float(d)
            return _int(d)
    return None


# Catalogues whose ref is NOT a bare leading number — store the full text
# after the prefix («Aagaard 1996 T 43b» → «1996 T 43b», not the year «1996»;
# «Fiala 4 nr. 325» → «4 nr. 325», not the volume «4»).
_CAT_FULL_REMAINDER = {"aagaard", "fiala"}


def _catalog(src):
    """Parse `typeNumber` → {catalog_key: ref}. Handles multi-field colon/comma
    form («H: 134B; Sch: -», «Hbg. 4, MB 558») + abbreviations; first per key."""
    tn = src.get("typeNumber")
    if not isinstance(tn, str) or not tn.strip():
        return {}
    out: dict = {}
    for seg in re.split(r"[;,]", tn):
        seg = seg.strip()
        m = re.match(r"^([A-Za-zÆØÅæøå]+)[\s:.]*(.+)$", seg)
        if not m:
            continue
        prefix, rest = m.group(1), m.group(2).strip()
        key = next((k for rx, k in _CAT_PREFIX if rx.match(prefix)), None)
        if key is None or key in out:
            continue
        if key in _CAT_FULL_REMAINDER:
            val = rest.rstrip(" .-")
        else:
            nm = re.match(r"\d+[A-Za-z]?", rest)  # «Sch: -» → no number → skip
            val = nm.group(0) if nm else None
        if val:
            out[key] = val
    return out


def _inventory(src):
    inv = (src.get("objectIdentification") or "").strip()
    if inv:
        return inv
    pre = src.get("numberPrefix") or ""
    num = src.get("numberData")
    suf = src.get("numberSuffix") or ""
    joined = f"{pre} {num}{('.' + str(suf)) if suf else ''}".strip()
    return joined or None


_VNOTE = {
    "de": ("KMK-Seed: Datensatz aus der Kgl. Münz- und Medaillensammlung "
           "(Nationalmuseet Kopenhagen, api.natmus.dk). Felder museumsbelegt; "
           "Müntzfuß/Phase noch unklassifiziert (seed_unsorted) bis zur "
           "Phase-4-Zuordnung."),
    "en": ("KMK seed: record from the Royal Coin Cabinet (Nationalmuseet "
           "Copenhagen, api.natmus.dk). Fields museum-attested; Münzfuß/phase "
           "unclassified (seed_unsorted) pending Phase-4 assignment."),
    "uk": ("KMK-сід: запис із Королівського мюнцкабінету (Nationalmuseet "
           "Копенгаген, api.natmus.dk). Поля музейно-засвідчені; Müntzfuß/фаза "
           "некласифіковані (seed_unsorted) до Phase-4."),
}


def build_entry(src) -> dict | None:
    if _is_exonumia_workdesc(src.get("workDescription")):
        return None
    rid = src.get("id")
    if not (isinstance(rid, int) or (isinstance(rid, str) and str(rid).isdigit())):
        return None
    rid = int(rid)

    yf, yl, year_verified = _year(src)
    # Era scope gate (mission lower bound 1481 / upper 1914). Undated kept —
    # finer dual-anchor (DK 1514 / German 1559) left to Phase 4.
    if yf is not None and (yf < 1481 or yf > 1914):
        return None

    mint, mintmaster = _split_place(src)
    nation = src.get("nation")
    # Entity routing: mint first (precise), nation fallback (coarse).
    entity = classify_mint_to_entity(mint, year=yf) if mint else None
    via = "mint" if entity else None
    if entity is None:
        entity = classify_nation_to_entity(nation, year=yf)
        via = "nation" if entity else None

    metal = _metal(src)
    w = _weight(src)
    catalog = _catalog(src)

    if yf is not None and yl is not None and yf == yl:
        year_label = str(yf)
    elif yf is not None:
        year_label = f"{yf}-{yl}"
    else:
        year_label = None

    entry = {
        "id": f"kmk-{rid}",
        "fuss": "seed_unsorted",
        "phase": "kmk",
        "kind": "kurant",
        "issuing_entity": entity,             # None → _unclassified.yml
        "entity_classified_via": via,
        "nominal": (src.get("nominal") or None),
        "metal": metal,
        "metal_verified": metal is not None,
        "mint": mint,
        "mint_verified": mint is not None,
        "ruler": _ruler(src),
        "mintmaster": mintmaster,
        "year_first": yf,
        "year_last": yl,
        "year_label": year_label,
        "year_ranges": [[yf, yl]] if yf is not None else None,
        # Only emitted when False (reign-window estimate); renderer
        # defaults to verified=true, so a normal dated coin stays clean.
        "year_verified": False if not year_verified else None,
        "weight_rough_g": w,
        "weight_rough_verified": w is not None,
        "catalog": catalog or None,
        "verified": False,
        "sources": [{
            "type": "museum",
            "url": f"https://samlinger.natmus.dk/KMM/object/{rid}",
            "ref": "KMM " + str(rid) + (
                f" (Inv. {_inventory(src)})" if _inventory(src) else ""),
        }],
        "verification_note": _VNOTE,
    }
    return {k: v for k, v in entry.items() if v is not None}


def build_seed(dry_run: bool, no_merge: bool, limit: int | None) -> int:
    files = sorted(p for p in KMK_CACHE.glob("[0-9]*.json"))
    entries: list[dict] = []
    scanned = skipped = 0
    for p in files:
        if limit is not None and scanned >= limit:
            break
        scanned += 1
        try:
            src = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        e = build_entry(src)
        if e is None:
            skipped += 1
            continue
        entries.append(e)

    classified = sum(1 for e in entries if e.get("issuing_entity"))
    via_mint = sum(1 for e in entries if e.get("entity_classified_via") == "mint")
    via_nation = sum(1 for e in entries if e.get("entity_classified_via") == "nation")
    print(f"  scanned {scanned} cache files → {len(entries)} coin entries "
          f"({skipped} skipped: exonumia/era/no-id); "
          f"{classified} entity-classified (mint={via_mint}, nation={via_nation}), "
          f"{len(entries) - classified} → _unclassified")

    scope_note = (
        "KMK Copenhagen seed — records from the Royal Coin Cabinet "
        "(Den Kgl. Mønt- og Medaillesamling, Nationalmuseet; api.natmus.dk), "
        "built directly from the whole-record _source cache (nation-scoped at "
        "harvest). Coin-only (§9.2 exonumia excluded; era 1481-1914, undated "
        "kept). Mint city → entity via classify_mint_to_entity; realm fallback "
        "via classify_nation_to_entity (entity_classified_via records which). "
        "Museum-attested fields carry verified=true (weight only — no diameter/"
        "fineness). Phase-4 assigns Müntzfuß/phase; cross-source merger "
        "deduplicates against Hede/Bruun/Numista/IKMK/etc."
    )
    write_v2_seed(
        entries,
        source_name="kmk",
        source_label="KMK Copenhagen (Nationalmuseet, api.natmus.dk)",
        scope_note=scope_note,
        dry_run=dry_run,
        no_merge=no_merge,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="persist (default: dry-run)")
    ap.add_argument("--no-merge", action="store_true",
                    help="wholesale overwrite (skip merge_seed curation preservation)")
    ap.add_argument("--limit", type=int, default=None,
                    help="process only N cache files (subset test)")
    args = ap.parse_args()
    return build_seed(dry_run=not args.write, no_merge=args.no_merge, limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
