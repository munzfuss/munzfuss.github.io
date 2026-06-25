#!/usr/bin/env python3
"""build_galster_denmark_seed.py — V2-native Galster seed builder.

Walks parsed Galster page sidecars at `scripts/cache/danskmoent/galster/*.json`
and writes entity-keyed V2 seed yamls directly to
`data/v2/seed/galster/<entity>.yml`.

§AZ Tier 2 (per `docs/research/denmark_pre_1541_source_survey.md`). The
parsed Galster JSON sidecars carry per-page data (ruler, denomination,
year, mint, catalog refs, Bruttovægt + Finhed + Finvægt where attested,
inscription, Litteratur). The 1514-1541 sub-window is the project's
pre-Hede gap (Hede 1971 starts Christian III 1541).

V2-native (per CLAUDE.md «V2 entity-keyed pipeline» — V1 frozen):
output goes directly to `data/v2/seed/galster/<entity>.yml`, NOT through
the V1→V2 `seed_v2_regroup.py` indirection. Each coin's `issuing_entity`
(scalar or list-form) determines its home file via `lib.v2_seed_writer`.

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
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from lib.catalog_codes import catalog_from_ref_dict  # noqa: E402
from lib.paths import GALSTER_CACHE  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

_OVERVIEW_MANIFEST = GALSTER_CACHE / "_overview_cross_refs.json"
_DANSKMOENT_BASE = "https://www.danskmoent.dk"


def _load_overview_cross_refs() -> tuple[dict[str, list[str]], dict[str, str]]:
    """Load `_overview_cross_refs.json` produced by `fetch_galster.py overviews`.

    Returns:
      (cross_refs, overview_titles) where
        cross_refs[coin_path] = [overview_path, ...]
        overview_titles[overview_path] = "1 Nobel" (etc.)

    Both maps are empty if the manifest doesn't exist (older clones
    that haven't run the overviews phase). Builder propagation is
    a no-op in that case.
    """
    if not _OVERVIEW_MANIFEST.exists():
        return {}, {}
    try:
        data = json.loads(_OVERVIEW_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    cross_refs = data.get("cross_refs") or {}
    overviews = data.get("overviews") or []
    titles = {ov.get("path"): ov.get("title", "")
              for ov in overviews if ov.get("path")}
    return cross_refs, titles


YEAR_FROM = 1481
YEAR_TO = 1541
# Lower bound 1481 matches Bruun builder + project Phase-pre-I scope
# anchor (Hans's reign start = 1481). Galster catalogue covers Hans
# 1481-1513 + Christian II 1513-1523 + Frederik I 1523-1533, so the
# previous 1514 floor was over-restrictive and rejected ~9 Hans
# coins (Galster 1-24, Nobel 1496-1502 + Goldgulden 1481-1513
# + Sølvgylden + Hvid varieties). Surface harvest gap: the Hans
# Galster index `/hgalst.htm` is not yet in `fetch_galster.py::INDEX_PAGES`
# so even with this lower YEAR_FROM, Hans pages remain uncached;
# tracked as a separate harvest task.

# Reign-end anchor per ruler — used as fallback year_first/year_last
# for undated («u.år») Galster entries. Keys match `ruler_volume`
# from the per-coin JSON (`hg` Hans / `c2g` Christian II / `f1g`
# Frederik I) or fallback by ruler-name. Per CLAUDE.md §3a:
# undated entries get bare year-range as year_label + set
# `year_verified: false` so the renderer emits `(?)`.
_RULER_REIGN = {
    "hg":  (1481, 1513),   # Hans
    "c2g": (1513, 1523),   # Christian II
    "f1g": (1523, 1533),   # Frederik I
    "c3g": (1534, 1559),   # Christian III (pre-1541 portion only — YEAR_TO=1541 cuts later)
}


def parse_year_range(year_label: str | None) -> tuple[int | None, int | None]:
    """Extract (year_first, year_last) from a Galster page year_label.

    Examples:
      «1531» → (1531, 1531)
      «1516, 1518» → (1516, 1518)
      «1535-1540» → (1535, 1540)
      «u.år» → (None, None) — caller anchors to reign window
    """
    if not year_label:
        return None, None
    years = [int(m) for m in re.findall(r"\b(1[4-6]\d{2})\b", year_label)]
    if not years:
        return None, None
    return min(years), max(years)


def parse_year_ranges(year_label: str | None) -> list[list[int]]:
    """Parse a Galster page year_label into DISCRETE [start, end] ranges.

    Each comma/semicolon-separated token is a single year «1516» → [1516,
    1516] or a dash range «1535-1540» → [1535, 1540]. A discrete-year list
    is kept as SEPARATE ranges so «1516, 1518» → [[1516, 1516], [1518,
    1518]] — NOT [[1516, 1518]], which would falsely assert a 1517
    striking. Per CLAUDE.md «source years immutable — never collapse a
    discrete list into a continuous span». Reuses parse_year_range's year
    token regex, so min/max stay consistent with year_first/year_last.

    Returns [] when no year token is present (caller falls back to the
    reign-window single span).
    """
    if not year_label:
        return []
    ranges: list[list[int]] = []
    for token in re.split(r"[,;]", year_label):
        yrs = [int(m) for m in re.findall(r"\b(1[4-6]\d{2})\b", token)]
        if not yrs:
            continue
        ranges.append([min(yrs), max(yrs)])
    return ranges


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


def detect_issuing_entity(sub_realm: str | None, mint: str | None):
    """Returns V2 issuing_entity (scalar or list-form for joint mints).

    Uses the centralised `classify_mint_to_entity` (lib/v2_entity_classify.py)
    so the mapping table is single-source-of-truth across all V2 builders.
    Falls back by `sub_realm` when the mint is missing or unclassified —
    keeps Norway-realm coins under `danish_norway` even when the page
    doesn't name a specific Norge mint."""
    if mint:
        result = classify_mint_to_entity(mint)
        if result:
            return result
    if sub_realm == "norway":
        return "danish_norway"
    return "danish_realm"


def coin_id(galster_number: str | None, ruler_volume: str | None, source_file: str) -> str:
    """Stable ID: dk-galster-<ruler_volume>-<number>.

    Falls back to dk-galster-<source_filename> if metadata is missing.
    """
    if galster_number and ruler_volume:
        return f"dk-galster-{ruler_volume}-{galster_number.lower()}"
    return f"dk-galster-{source_file.replace('.htm', '').replace('.json', '')}"


_GALSTER_MINTS_RE = re.compile(
    r",\s*("
    # Danish mints (incl. mojibake variants K�benhavn / Malm� /
    # Gl�ckstadt / Helsing�r / �rhus from iso-8859 → utf-8 conversion)
    r"Ålborg|Aalborg|Malmø|Malmoe|Malmö|Malm[?�]|"
    r"Ronneby|Hamar|Bergen|Oslo|Christiania|"
    r"København|Kjøbenhavn|K[?�]benhavn|Kj[?�]benhavn|Copenhagen|"
    r"Roskilde|Aarhus|Århus|[?�]rhus|Ribe|Lund|Visby|"
    r"Husum|Gottorp|Glückstadt|Gluckstadt|Gl[?�]ckstadt|"
    r"Trondheim|Nidaros|Stockholm|Vasteras|"
    r"Lübeck|L[?�]beck|Hamburg|Schwerin|Rendsburg|"
    r"Helsingør|Helsingor|Helsing[?�]r"
    r")(\s*\(\?\))?\s*$",
    re.IGNORECASE,
)
# Coin-shape descriptors that occasionally bleed into the denomination
# field from Galster page titles. «klipping» / «klippe» = clipped /
# emergency-issue square-cut coin shape, not a denomination. Stripped
# from nominal; preserved in note via `shape_hint` (curator may move
# to `shape` field).
_SHAPE_DESCRIPTORS_RE = re.compile(
    r"[,\s]+\(?(klipping|klippe|firkant)\)?\s*$",
    re.IGNORECASE,
)


_GALSTER_MINT_PREFIX_RE = re.compile(
    r"^("
    # Same set as _GALSTER_MINTS_RE for reversed «<Mint>, <denom>» order
    r"Ålborg|Aalborg|Malmø|Malmoe|Malmö|Malm[?�]|"
    r"Ronneby|Hamar|Bergen|Oslo|Christiania|"
    r"København|Kjøbenhavn|K[?�]benhavn|Kj[?�]benhavn|Copenhagen|"
    r"Roskilde|Aarhus|Århus|[?�]rhus|Ribe|Lund|Visby|"
    r"Husum|Gottorp|Glückstadt|Gluckstadt|Gl[?�]ckstadt|"
    r"Trondheim|Nidaros|Stockholm|Vasteras|"
    r"Lübeck|L[?�]beck|Hamburg|Schwerin|Rendsburg|"
    r"Helsingør|Helsingor|Helsing[?�]r"
    r")\s*,\s*",
    re.IGNORECASE,
)


def _split_nominal_mint(nominal: str | None, source_mint: str | None
                        ) -> tuple[str | None, str | None, str | None]:
    """Detect mint embedded in the nominal field and split it out.

    Two patterns recognised:
      A. Trailing form  «<denom>, <mint>[ (?)]»  (most common)
      B. Leading form   «<mint>, <denom>»          (rarer; Galster
         occasionally orders mint first when the mint is the page's
         primary identifier)

    Returns (clean_nominal, mint, shape_hint). When the nominal carries
    a mint, the in-nominal mint is treated as the page-title-attested
    authority and overrides source_mint (which is parser-heuristic-
    derived and sometimes wrong). Also strips coin-shape descriptors
    («klipping») from nominal.
    """
    if not nominal:
        return (nominal, source_mint, None)
    s = str(nominal).strip()
    # Collapse double-comma artefacts: «1 Hvid, , Ålborg» → «1 Hvid, Ålborg»
    s = re.sub(r",\s*,\s*", ", ", s)
    extracted_mint = None
    # A. Trailing form
    m = _GALSTER_MINTS_RE.search(s)
    if m:
        extracted_mint = m.group(1)
        s = _GALSTER_MINTS_RE.sub("", s).rstrip(" ,")
    # B. Leading form (only when trailing pattern didn't fire)
    if not extracted_mint:
        m_lead = _GALSTER_MINT_PREFIX_RE.match(s)
        if m_lead:
            extracted_mint = m_lead.group(1)
            s = _GALSTER_MINT_PREFIX_RE.sub("", s).strip()
    shape_hint = None
    sm = _SHAPE_DESCRIPTORS_RE.search(s)
    if sm:
        shape_hint = sm.group(1).lower()
        s = _SHAPE_DESCRIPTORS_RE.sub("", s).rstrip(" ,")
    # Prefer the title-attested mint over the parser-heuristic source_mint
    mint_value = extracted_mint or source_mint
    return (s or None, mint_value, shape_hint)


# Module-level overview-cross-refs cache, loaded once per build.
# Maps coin_path (e.g. "/fr/f1g68.htm") → [overview_path, …]
# and overview_path → overview title for ref-text emission.
_OVERVIEW_CROSS_REFS, _OVERVIEW_TITLES = _load_overview_cross_refs()


def _build_sources(data: dict) -> list[dict]:
    """Construct the per-coin `sources[]` list.

    Emits ONLY the primary Galster page citation — the specific per-coin
    danskmoent.dk page (e.g. /fr/hg24.htm), which is where the coin's data
    actually came from.

    The former behaviour ALSO appended the denomination-OVERVIEW page
    (/1nobel.htm, /guldgyld.htm, /2skill.htm, …) as a secondary
    «(Wertstufen-Übersicht)» citation. Removed (curator decision 2026-06-03):
    a denomination-overview is a table-of-contents of ALL coins of that
    denomination, not a per-coin source — it does not attest THIS coin's
    specific data. Per §5a sources must be specific + per-claim; the specific
    page is the source, the overview is navigation. (The overview-cross-ref
    manifest is still loaded for any future use, but is no longer emitted as a
    coin source.)
    """
    # Galster number: filename-derived on per-coin pages (chr_/fr_/hansg…),
    # but single-coin overview pages (2nobel.htm) carry it only in the
    # parsed catalog_refs — fall back to that. The ruler_volume parenthetical
    # is filename-derived too and absent on those pages; omit it cleanly
    # rather than print «(?)».
    galster_num = (
        data.get("galster_number")
        or (data.get("catalog_refs") or {}).get("galster")
        or "?"
    )
    volume = data.get("ruler_volume")
    volume_part = f" ({volume})" if volume else ""
    return [
        {
            "type": "literature",
            "url": data.get("source_url_hint"),
            "ref": (
                f"Galster {galster_num}{volume_part} — "
                f"danskmoent.dk {data.get('source_file', '?')}"
            ),
        }
    ]


# Foreign-catalogue NAMES that danskmoent lists as cross-references on a Galster
# coin page (Hildebrand/Lagerqvist/Rasmusson = Swedish/Scanian medieval-coin
# catalogues; Hauberg = Danish medieval; Ernst = Axel Ernst's Norwegian-coin
# studies, e.g. «Ernst 1940 21»). The page parser sometimes captures these INTO a
# Danish register (galster/sieg/schive — e.g. galster ['233','Hildebrand 715',
# 'Lagerqvist 4'] or schive ['Ernst 1940 21','XIV.32-33']). They are NOT
# Galster/Sieg/Schive numbers — reroute to `others`. Tight NAME whitelist: a real
# Danish index never starts with a catalogue name.
_FOREIGN_CATALOGUE_RE = re.compile(
    r"^(hildebrand|lagerqvist|rasmusson|hauberg|ernst)\b", re.I)

# Danish PROSE / negative markers danskmoent appends inside a catalogue cell —
# never a real index: «mangler [hos X]» (absent from catalogue X), «adskillige
# katalognumre» (several numbers), «se side N» (see page N), «unik» (unique —
# a rarity note). Dropped, not routed.
_PROSE_NOISE_RE = re.compile(
    r"\b(mangler|adskillige|katalognumre|se\s+side|unik)\b", re.I)
# «hhv. X og mangler» = "respectively X (year 1) and missing (year 2)" — a
# two-year Galster row where only the first year is catalogued. Keep X.
_HHV_RE = re.compile(r"^hhv\.\s*(.+?)\s+og\s+mangler", re.I)


def _clean_catalogue_refs(catalog: dict) -> None:
    """Clean danskmoent catalogue cells in the Danish registers, in place
    (idempotent). The cache packs cross-refs, prose and rarity notes into one
    cell, comma- or «;»-joined; a real Galster/Sieg/Schive/Schou/J-S index never
    contains a comma, a semicolon, or a Danish word. So split first, then:
      * «hhv. X og mangler» → X (keep the catalogued variant);
      * foreign cross-refs (Hildebrand/Lagerqvist/Rasmusson/Hauberg/Ernst) → `others`;
      * Danish prose / negative markers («mangler hos», «adskillige katalognumre,
        se side …», «; unik») → dropped;
      * a register left with no real index is removed."""
    for reg in ("galster", "sieg", "schive", "schou", "jensen_skjoldager"):
        val = catalog.get(reg)
        if val is None:
            continue
        vals = val if isinstance(val, list) else [val]
        parts: list[str] = []
        for v in vals:
            for p in re.split(r"[,;]", str(v)):
                p = p.strip()
                if not p:
                    continue
                m = _HHV_RE.match(p)
                if m:
                    p = m.group(1).strip()
                parts.append(p)
        kept: list[str] = []
        moved: list[str] = []
        for p in parts:
            if _FOREIGN_CATALOGUE_RE.match(p):
                moved.append(p)
            elif _PROSE_NOISE_RE.search(p):
                continue                      # drop prose / negative marker
            else:
                kept.append(p)
        if moved:
            others = catalog.setdefault("others", [])
            for m in moved:
                if m not in others:
                    others.append(m)
        if kept:
            catalog[reg] = kept[0] if len(kept) == 1 else kept
        else:
            catalog.pop(reg, None)


def build_entry(data: dict) -> dict | None:
    year_first, year_last = parse_year_range(data.get("year_label"))
    year_verified = True
    if year_first is None or year_last is None:
        # Undated «u.år» entry — anchor to ruler reign window per
        # CLAUDE.md §3a (renderer adds `(?)` via year_verified=false).
        reign = _RULER_REIGN.get(data.get("ruler_volume") or "")
        if reign is None:
            return None
        year_first, year_last = reign
        year_verified = False
    if not (YEAR_FROM <= year_first <= YEAR_TO):
        return None

    # GENERIC catalogue mapping (§CJ): Galster's catalog_refs keys are already
    # schema-field names (galster/schou/schive/sieg/jensen_skjoldager); the
    # generic mapper passes those through typed and routes any future
    # non-schema key to `others` rather than copying it verbatim (which would
    # fail validation).
    catalog: dict = catalog_from_ref_dict(data.get("catalog_refs") or {})
    if data.get("galster_number") and "galster" not in catalog:
        catalog["galster"] = data["galster_number"]
    if data.get("ruler_volume"):
        catalog["galster_volume"] = data["ruler_volume"]
    _clean_catalogue_refs(catalog)

    specs = data.get("specs") or {}
    sub_realm = data.get("sub_realm")
    metal = detect_metal(data.get("denomination"))

    cid = coin_id(data.get("galster_number"), data.get("ruler_volume"), data.get("source_file", ""))

    # Split mint from denomination string («14 Penning, Ålborg» →
    # nominal=«14 Penning», mint=«Ålborg»). Also strips coin-shape
    # descriptors like «klipping» that leak from page titles.
    nominal_clean, mint_value, shape_hint = _split_nominal_mint(
        data.get("denomination"), data.get("mint"))

    # Render year_label per CLAUDE.md §3a: bare decimal years/range,
    # no «u.år» prefix. For undated entries we use the reign-window
    # range as year_label and set year_verified=false (renderer
    # emits `(?)`).
    if not year_verified:
        if year_first == year_last:
            year_label_out = str(year_first)
        else:
            year_label_out = f"{year_first}-{year_last}"
    else:
        year_label_out = data.get("year_label")

    # year_ranges: parse the source year_label into DISCRETE ranges so a
    # comma-list «1516, 1518» yields [[1516,1516],[1518,1518]] (not a
    # continuous [[1516,1518]] that would falsely assert a 1517 striking,
    # CLAUDE.md «source years immutable»). The cross-source merger's
    # span-comparison then keeps the discrete form over a looser Numista
    # min/max range. Undated (reign-window) entries have no per-year source
    # detail → single span.
    if year_verified:
        yr_ranges = parse_year_ranges(data.get("year_label")) or [[year_first, year_last]]
    else:
        yr_ranges = [[year_first, year_last]]

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "galster",
        "kind": "kurant",
        "nominal": nominal_clean,
        "year_label": year_label_out,
        "year_first": year_first,
        "year_last": year_last,
        "year_ranges": yr_ranges,
        "year_verified": year_verified,
        "ruler": data.get("ruler"),
        "mint": mint_value,
        "catalog": catalog,
        "metal": metal,
        "fineness": specs.get("finhed"),
        "weight_rough_g": specs.get("bruttovaegt_g"),
        "issuing_entity": detect_issuing_entity(sub_realm, mint_value),
        "verified": False,
        "fineness_verified": bool(specs.get("finhed")),
        "weight_rough_verified": bool(specs.get("bruttovaegt_g")),
        "mint_verified": bool(mint_value) and not (
            isinstance(mint_value, str)
            and re.search(r"\s*(?:\beller\b|\boder\b|\bor\b|/)\s*",
                          mint_value, re.IGNORECASE)
        ),
        "sources": _build_sources(data),
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
    if sub_realm:
        entry["sub_realm"] = sub_realm
    if specs.get("mintage"):
        entry["mintage"] = specs["mintage"]
    # Note: `additional_litteratur` + `finvaegt_g` are deliberately
    # NOT emitted into the seed — they are dead-end metadata fields
    # never read downstream (cache JSON retains the litteratur block;
    # finvægt is bruttovægt × finhed and gets re-derived where needed)
    # and the Coin pydantic model rejects them (`_StrictBase` extra=forbid).
    # Schema-rejection was previously masked because most galster seed
    # entries were absorbed into unified foundation entries (build.py
    # `absorbed_seed_ids`); new sub-variant entries surface the issue.

    return entry


def collect_entries() -> list[dict]:
    entries: list[dict] = []
    skipped_shape = 0
    for json_path in sorted(GALSTER_CACHE.glob("*.json")):
        if json_path.name.startswith("_"):
            continue
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError as e:
            print(f"  [{json_path.name}] JSON parse error: {e}", file=sys.stderr)
            continue
        # Skip non-coin pages flagged by the per-shape parser
        # (`scripts/lib/galster_parsers/{reign_index,article}.py`).
        # These carry `skip: True` + `skip_reason` and are not coin
        # data — they exist as JSON sidecars purely for cache audit.
        if data.get("skip"):
            skipped_shape += 1
            continue
        # Additional safety filter: filenames prefixed with `ernst_` /
        # `artikler_` are danskmoent.dk narrative ARTICLE pages, not
        # coin-catalog pages. The cache parser sometimes mis-classifies
        # these as `page_shape: standard` when the article happens to
        # parse cleanly (e.g. ernst_f1g50ern reads as a single-coin
        # description). They describe specific specimens of coins that
        # are already represented in their canonical Galster pages
        # (f1g-50 covers ernst_f1g50ern; f1g-71 + f1g-74 cover
        # ernst_14p1524's two coins). Filtering them at the builder
        # level prevents phantom unified entries.
        source_file = data.get("source_file") or json_path.name
        if source_file.startswith(("ernst_", "artikler_")):
            skipped_shape += 1
            continue
        # Sub-variant pages (chr_c3g92 → 92/92A/92B; chr_c3g95 → 95A/95B;
        # parser-emitted `variants: [...]`): emit one entry per variant.
        # Each variant overlays its galster suffix + per-row specs onto
        # the page-level data; catalog_refs gets variant-specific
        # schou/sieg when the variant carries them.
        variants = data.get("variants") or []
        if variants:
            for var in variants:
                var_data = dict(data)
                if var.get("galster"):
                    var_data["galster_number"] = var["galster"]
                var_data["specs"] = {
                    **(data.get("specs") or {}),
                    **{k: v for k, v in {
                        "bruttovaegt_g": var.get("bruttovaegt_g"),
                        "finhed": var.get("finhed"),
                        "finvaegt_g": var.get("finvaegt_g"),
                    }.items() if v is not None},
                }
                # Variant-specific schou / sieg refs override the
                # page-level catalog_refs (which mix all variants).
                var_data["catalog_refs"] = dict(data.get("catalog_refs") or {})
                if var.get("schou"):
                    var_data["catalog_refs"]["schou"] = var["schou"]
                if var.get("sieg"):
                    var_data["catalog_refs"]["sieg"] = var["sieg"]
                entry = build_entry(var_data)
                if entry:
                    if var.get("note"):
                        # «Kendes ikke mere» style annotation from the
                        # variant table — folded into the schema-allowed
                        # `note` field as DE/EN/UK prose (single-language
                        # caveat; downstream curator can refine).
                        caveat = var["note"]
                        entry["note"] = {
                            "de": f"Galster-Variantentabelle: {caveat}",
                            "en": f"Galster variant table: {caveat}",
                            "uk": f"Galster-таблиця варіантів: {caveat}",
                        }
                    entries.append(entry)
            continue
        entry = build_entry(data)
        if entry:
            entries.append(entry)
    if skipped_shape:
        print(f"  Skipped {skipped_shape} non-coin page(s) (article / reign_index)")
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

    scope_note = (
        "§AZ Tier 2 — danskmoent.dk Galster-page harvest. Covers Christian "
        "II + Frederik I + Christian III pre-1541 (Hede 1971 doesn't "
        "catalogue these). Parallel source to v2/seed/bruun/ (Tier 1) "
        "and v2/seed/hede/ (existing main). §BF promotion uses all three."
    )
    write_v2_seed(
        entries,
        source_name="galster",
        source_label=(
            "danskmoent.dk Galster-page series (Christian II + Frederik I "
            "indexes + Christian III pre-1541)"
        ),
        scope_note=scope_note,
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
