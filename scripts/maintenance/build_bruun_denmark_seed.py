#!/usr/bin/env python3
"""build_bruun_denmark_seed.py — generate Bruun V2 seed entries
from parsed Bruun-corpus lots.

Scope: the FULL project window for Danish-realm + Norway-under-Danish-
rule coins (1514-1914). Bruun's L. E. Bruun Collection (Stack's Bowers
2024-2026, 4 parts) is one of the canonical specimen attestations
for Danish numismatics — every period from Christian II's Lovkompleks
through Christian X's Krone-era. Pre-1541 was the original §BI anchor
scope; expanded to the full window 2026-05-20 (rationale: V2 needs
cross-source attestation parity with V1, which carried Bruun citations
on Christian IV-era + later Speciedaler / Krone / Rigsbankdaler issues
that the pre-1541 window excluded — leading to 62 Bruun-citation
losses on stale-foundation purge).

This transforms the already-parsed Bruun lot JSON
(`scripts/cache/bruun/lots/part{1-4}.json`) into project-shaped seed
entries that the cross-source merger consolidates with parallel
Hede / Numista / NumisMaster / ucoin attestations.

Scope filter: 1514 ≤ year ≤ 1914 AND region ∈ {DENMARK, NORW AY,
DENMARK-NORWAY}. Excludes:
  - Pre-1514 (Hans + Erik VII outside Christian II Lovkompleks anchor)
  - Post-1914 (post-precious-metal-anchor era per CLAUDE.md mission scope)
  - Sweden / other non-realm regions (Kalmar Union political residue
    treated as out-of-realm; Christian II 1535 Stockholm IS kept since
    he claimed Sweden)

Output schema mirrors the other V2 seed sources for cross-source
merger compatibility:
  - id: `dk-bruun-<bruun-coll-id>` (or `dk-bruun-pt<N>-<lot-no>` if no coll-id)
  - catalog: dict of all attested cross-refs from lot.refs
  - sources: Bruun-lot citation block + Stack's Bowers auction reference
  - bruun_collection_id / bruun_part / bruun_lot_no for fast lookup
  - verified: false on all per §AF/§4 (specimens are auction-grade, not
    project-verified)
  - fineness_verified / weight_rough_verified per attestation status

Run:
    .venv/bin/python scripts/maintenance/build_bruun_denmark_seed.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ruamel.yaml

# Boilerplate ----------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "scripts" / "cache" / "bruun" / "lots"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from lib.catalog_codes import catalog_from_ref_dict  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib.v2_seed_writer import normalise_nominal_display  # noqa: E402


def _classify_entity(mint, is_norway: bool, meta_line: str | None = None,
                       year: int | None = None):
    """Bruun lot → V2 issuing_entity. Three-tier fallback:

    1. **Meta_line subnational token** (`_classify_via_meta_line`) —
       Bruun's meta line carries the EXPLICIT issuer attribution from
       Krause's catalogue convention («Schleswig-Holstein-Norburg-Plön. Ducat»,
       «Lübeck (Bishopric). 2 Mark», «Lauenburg. 2/3 Taler»). When
       present, this is the most precise signal — it tells us which
       political body Bruun assigns the coin to, regardless of which
       physical mint struck it. The matcher uses longest-token-first
       so «schleswig-holstein-gottorp» beats the generic «schleswig-
       holstein» fallback. Returns None when no subnational token
       matches (e.g. meta_line just says «DENMARK. <denom>. <mint>
       Mint. ...» — no SH-prefix qualifier).
    2. **Mint-based** (`classify_mint_to_entity`) — fallback when
       meta_line gives no issuer signal. `year` forwarded so the
       central classifier applies year-aware overrides (e.g. Altona
       pre/post-1640 → Schauenburg-Pinneberg vs Royal-Holstein per
       `mint_registry.py::year_overrides`).
    3. **Norway flag / `danish_realm` default** — bottom of the fallback
       chain. Lots that fail all three end up in `danish_realm` and
       surface as orphan unifieds for curator review.

    Order rationale (2026-05-26): meta_line-first preserves Krause's
    issuer attribution for cases where multiple issuers used the same
    physical mint at the same time. Example: Glückstadt royal mint
    struck Royal-Holstein coinage AND, under contract, Lübeck-Bishopric
    coinage (Christian August 1723) AND Lauenburg-territorial coinage
    (Frederik VI 1830). Mint alone says royal_holstein for all three;
    meta_line correctly distinguishes them via «Lübeck (Bishopric)»,
    «Lauenburg», or no-subnational-token (= royal coinage).

    Year-awareness wired 2026-05-26: when meta_line has no subnational
    token (e.g. pre-1640 Altona with Bruun-14912 typo «Schaumberg»
    that misses META_SUBNATIONAL alias OR generic «DENMARK. <denom>.
    <mint>» meta), mint-classifier-with-year correctly returns
    `schauenburg_pinneberg` for Altona+year<1640.
    """
    if meta_line:
        result = _classify_via_meta_line(meta_line)
        if result:
            return result
    if mint:
        result = classify_mint_to_entity(mint, year=year)
        if result:
            return result
    if is_norway:
        return "danish_norway"
    return "danish_realm"

# Region filter — Bruun parser produced "NORW AY" with internal space.
# GERMANY + SWEDEN added 2026-05-25 to cover SH-duchy / Bremen-Verden /
# Plön coinage in Bruun catalogue (audit found 57 Bruun lots tagged as
# GERMANY/SWEDEN but legitimately in project scope — Schleswig-Holstein-
# Norburg-Plön under DENMARK crown, Holstein-Gottorp-Bremen, Bremen-Verden
# under SWEDISH crown 1648-1715). The downstream `_classify_entity` /
# `_classify_via_meta_line` routes such lots to the correct project
# entity (norburg_plon_duchy, gottorp_duchy, erzbisthum_bremen_verden,
# holstein_schauenburg_county, etc.); lots that don't classify land in
# `_unclassified.yml` for curator review.
REALM_REGIONS = {
    "DENMARK", "NORW AY", "NORWAY", "DENMARK-NORWAY",
    "GERMANY", "SWEDEN",
}

# Meta_line subnational-token → project entity mapping. Bruun's meta_line
# carries «Schleswig-Holstein-Norburg-Plön. Ducat, 1760...» — the second
# clause names the issuing political body. When the mint-based classifier
# returns nothing (mint missing or generic), we fall back to these tokens.
META_SUBNATIONAL_TO_ENTITY: dict[str, str] = {
    "schleswig-holstein-norburg-plön": "norburg_plon_duchy",
    "schleswig-holstein-norburg-plon": "norburg_plon_duchy",
    "schleswig-holstein-sonderburg": "sonderburg_duchy",
    "schleswig-holstein-sønderborg": "sonderburg_duchy",
    "schleswig-holstein-sonderburg-glücksburg": "glucksburg_duchy",
    "schleswig-holstein-sonderburg-glucksburg": "glucksburg_duchy",
    "schleswig-holstein-glücksburg": "glucksburg_duchy",
    "schleswig-holstein-gottorp": "gottorp_duchy",
    "schleswig-holstein": "royal_holstein",  # fallback for unqualified SH
    "holstein-schauenburg": "schauenburg_pinneberg",
    "schauenburg-pinneberg": "schauenburg_pinneberg",
    "lübeck (bishopric)": "fuerstbisthum_luebeck",
    "luebeck (bishopric)": "fuerstbisthum_luebeck",
    "lübeck-bishopric": "fuerstbisthum_luebeck",
    "fürstbisthum lübeck": "fuerstbisthum_luebeck",
    "fuerstbisthum luebeck": "fuerstbisthum_luebeck",
    "bremen (bishopric)": "erzbisthum_bremen_verden",
    "bremen-verden": "erzbisthum_bremen_verden",
    "bremen & verden": "erzbisthum_bremen_verden",
    "hesse-kassel": "landgrafschaft_hessen_kassel",
    "hessen-kassel": "landgrafschaft_hessen_kassel",
    "oldenburg": "grafschaft_oldenburg",
    "osnabrück (bishopric)": "hochstift_osnabrueck",
    "osnabrueck (bishopric)": "hochstift_osnabrueck",
    "osnabrück": "hochstift_osnabrueck",
    "osnabrueck": "hochstift_osnabrueck",
    "schaumburg-pinneberg": "schauenburg_pinneberg",
    "schleswig-holstein-schaumburg-pinneberg": "schauenburg_pinneberg",
    "s chleswig-holstein-schaumburg-pinneberg": "schauenburg_pinneberg",
    # Bruun catalogue typo observed on Bruun-14912 («Schaumberg» without
    # the «u»). Defense-in-depth alias so meta_line classification
    # survives without the mint+year fallback path. Same for the leading-
    # space parser artefact.
    "schaumberg-pinneberg": "schauenburg_pinneberg",
    "schleswig-holstein-schaumberg-pinneberg": "schauenburg_pinneberg",
    "s chleswig-holstein-schaumberg-pinneberg": "schauenburg_pinneberg",
    "lübeck. taler": "hanseatic_lubeck",
    "luebeck. taler": "hanseatic_lubeck",
    "rantzau": "rantzau_county",
    "brunswick-lüneburg": "herzogtum_braunschweig_lueneburg",
    "brunswick-luneburg": "herzogtum_braunschweig_lueneburg",
    "saxe-lauenburg": "herzogtum_sachsen_lauenburg",
    "sachsen-lauenburg": "herzogtum_sachsen_lauenburg",
    "lauenburg": "herzogtum_sachsen_lauenburg",
}


def _classify_via_meta_line(meta: str | None) -> str | None:
    """Walk META_SUBNATIONAL_TO_ENTITY tokens against the lot's meta_line
    text. Longest-match wins (multi-word tokens like
    `schleswig-holstein-norburg-plön` outrank the generic
    `schleswig-holstein`). Case-insensitive substring."""
    if not meta:
        return None
    meta_lc = meta.lower()
    # Sort by token length descending so longest-match wins
    for token in sorted(META_SUBNATIONAL_TO_ENTITY, key=len, reverse=True):
        if token in meta_lc:
            return META_SUBNATIONAL_TO_ENTITY[token]
    return None

# Year window — full project scope (was 1514-1541 pre-2026-05-20 per the
# original §BI anchor; expanded to 1514-1914 to recover the 62 lost
# Bruun citations on Christian IV-era Speciedaler / 17-18th c Krone /
# Rigsbankdaler / Krone-era entries from V1).
YEAR_FROM = 1481
YEAR_TO = 1914
# Lower bound 1481 = Hans's earliest documented coinage (Hans Goldgulden
# Numista N#355730 «de facto 1481»). The project's mission-scope anchor
# is 1514 (Christian II Lovkompleks), but the Nobelfod and reichsdukatenfuss
# Phase pre-I genuinely extend back to 1481 — Hans Nobel 1496, Hans
# Goldgulden 1481-1513 et al. are documented Hans-era types kept in
# V2 nobel_fod / reichsdukatenfuss. Bruun catalogue carries authoritative
# specimen attestations for these (Bruun-3831 Hans Nobel, Bruun-3840
# Hans Goldgulden) — must enter seed for cross-source attestation parity.
# Earlier than 1481 (Erik VII, Christopher III, true medieval) remains OOS.

# Map Bruun ref-key to project catalog field. Keys NOT present in
# `CatalogRefs` schema (lott, delzanno, sm, hagander, appelgren,
# mb_swedish, hauberg, malmer) route to `catalog.others` as
# «{prefix}# {value}» tokens — see _route_unknown_ref below.
REF_FIELDS = {
    "Bruun": "bruun_collection_id",
    "Sieg": "sieg",
    "Schou": "schou",
    "Galster": "galster",
    "Fr": "friedberg",
    "Lange": "lange",
    "Dav": "davenport",
    "KM": "km",
    "Hede": "hede",
    "Schive": "schive",
    "NMD": "nmd",
    "FP": "fp",  # Friberg-Pedersen «Skillingen, Specien og Kronen 1761-1813»
    "Skjoldager": "jensen_skjoldager",  # parser key for «Jensen & Skjoldager»
    "Llt": "lott",
    "Delzanno": "delzanno",
    "SM": "sm",
    "Hagander": "hagander",
    "Appelgren": "appelgren",
    "MB": "mb_swedish",  # confirmed Swedish-specific per §BJ survey
    "Hauberg": "hauberg",
    "Malmer": "malmer",
}


# Canonical PDF URL per Bruun Part. Stack's Bowers Galleries published the
# L. E. Bruun collection across four sales (Sept 2024, March 2025, October 2025,
# March 2026); Part II's PDF is hosted by danskmoent.dk, the rest by
# stacksbowers.com. These URLs anchor every emitted Bruun source so a
# reader can land on the exact catalog PDF for the cited lot/page.
_BRUUN_PART_PDF_URL: dict[int, str] = {
    1: "https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Sept2024_LEBruun_Collection_Part_I_Catalog.pdf",
    2: "https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf",
    3: "https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Oct2025_LE_Bruun_Coins_Part_III.pdf",
    4: "https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Mar2026_BruunIV_Coins_Catalog.pdf",
}
_BRUUN_PART_ROMAN: tuple[str, ...] = ("I", "II", "III", "IV")


def _build_bruun_source(part: int, lot: dict) -> dict:
    """Canonical Bruun source entry — `Bruun Part {N}, lot {lot_no}, p. {page}`.

    Schema-conformant: `type: auction`, with the part-specific PDF URL
    and a `ref` text giving Part roman numeral + lot number + page. This
    format is the project's single canonical form for Bruun citations
    (curator-stated 2026-05-27): readers want a direct, dense locator
    that points at a specific page of the auction catalog. Older builder
    output of «Bruun-{coll_id} · Stack's Bowers Bruun Collection Part
    {N}, lot {lot_no}» (no page, no URL, redundant collection-id-in-text)
    is replaced; existing entries get rewritten by
    `scripts/maintenance/normalise_bruun_sources.py`.

    Page numbers come from the Bruun parser's `page_span` (single page when
    the lot fits on one page; min(page_span) when it spans two — page
    numbers in auction catalogs traditionally cite the lot's first page).
    """
    page_span = lot.get("page_span") or []
    page = page_span[0] if page_span else lot.get("page")
    romnum = _BRUUN_PART_ROMAN[part - 1]
    lot_no = lot.get("lot_no")
    page_str = f", p. {page}" if page else ""
    return {
        "type": "auction",
        "url": _BRUUN_PART_PDF_URL[part],
        "ref": f"Bruun Part {romnum}, lot {lot_no}{page_str}",
    }


def parse_year(lot: dict) -> int | None:
    """Try lot.year first, then regex on meta_line / body_excerpt.

    The upstream Bruun parser (`scripts/bruun_parser/02_parse_lots.py`) was
    fixed 2026-05-24 to cover pre-1500 coinage and prioritise meta_line over
    body refs (Beskrivelsen 1791 / Bruun-1898 catalog-ref traps). This
    builder-side helper mirrors that fix so a fresh build against an unpatched
    cache (or partial regen) still picks up the right year for in-scope coins
    spanning the 1514 anchor (Hans Goldgulden 1481-1497 Phase pre-I etc.).

    Order of precedence:
      1. ND-range gate — reject medieval-Penny lots whose meta starts with
         «ND (1xxx)» where xxx is <= 299 (pre-1300 horizon). Builder scope
         filter further restricts to 1514-1914, but this gate avoids spending
         cycles on clearly OOS medieval lots.
      2. lot.year (upstream parser's verdict) — trusted when present.
      3. Fallback regex on meta_line / body — first 4-digit year in
         1300-1980 range (matches every Bruun coin from medieval up to
         modern catalogue edition years; builder scope filter discards OOS).
    """
    meta = lot.get("meta_line") or ""
    body = lot.get("body_excerpt") or ""
    # Reject ND-ranges that explicitly mark a pre-1300 medieval lot
    # («ND (1100)» / «ND (1234)» / «ND (1289)»). The previous regex
    # `[01]?[01]\d\d` was greedy: «[01]?» + «[01]» backtrack-matched
    # ANY 1-prefixed 4-digit token, so «ND (1440)», «ND (1496)»,
    # «ND (1396)» etc. all got silently rejected. Tightened to
    # `1[012]\d{2}` so only true 10xx/11xx/12xx ranges trip the gate.
    NDMED = r"ND\s*\(1[012]\d{2}"
    if re.search(NDMED, meta) or re.search(NDMED, body[:200]):
        return None
    y = lot.get("year")
    if y is not None:
        try:
            return int(str(y)[:4])
        except (ValueError, TypeError):
            pass
    # Fallback: meta first, then body — match parser's priority order.
    # Pattern covers 1300-1980 (Hans pre-1500 coinage + standard project
    # horizon + catalog edition years up to 1980). Lower bound 1300 instead
    # of 1100 (parser's bound) because by the time we're here, lot.year was
    # already missing — extra strictness is acceptable to dodge body-prose
    # noise (e.g. battle-of-1238 mentions in long lot descriptions).
    for src in (meta, body):
        if not src:
            continue
        m = re.search(r"\b(1[3-9]\d{2})\b", src)
        if m:
            return int(m.group(1))
    return None


def parse_year_span(lot: dict) -> tuple[int, int, bool] | None:
    """Capture an «ND (…)» *attributed* year-range, distinct from a dated strike.

    Bruun marks undated coins «ND (<year(s)>)» — the year there is the
    cataloguer's attribution, NOT an inscription on the coin. Both the upstream
    parser and `parse_year` flatten such lots to a single lower-bound year
    (`lot.year`), discarding three things: (a) the range, (b) an abbreviated
    upper bound («ND (1607-11)» = 1607–1611, «ND (ca. 1496-97)» = 1496–1497),
    and (c) the very fact the coin is undated / approximate. The result was an
    «ND (ca. 1496-1497)» Goldgulden rendered as a confident single-year «1496»
    strike (quirk logged 2026-06-16, `docs/SOURCES.md` §13.3).

    Returns `(year_first, year_last, year_verified=False)` when the meta_line
    carries an in-scope «ND (…)» attribution, else `None` (caller then uses the
    plain single-year `parse_year` path for genuinely dated strikes). «ca.» is
    honoured but does not change the result shape — every ND attribution is
    unverified, so the renderer emits the «(?)» marker on the year column
    (CLAUDE.md §4 / §3a: the year_label stays a clean decimal year/range, the
    uncertainty lives in the per-field verified flag).
    """
    meta = lot.get("meta_line") or ""
    # «ND (» + optional «ca.» + a 4-digit lower year + optional «-<upper>», where
    # the upper bound may be abbreviated (1607-11 → 1611, 1496-97 → 1497).
    # Medieval «ND (900-950)» / «ND (1100…)» never match: the lower-year class
    # is 1[3-9]\d{2} (1300-1999), so pre-1300 lots fall through to None and are
    # handled by parse_year's NDMED gate + the 1481-1914 scope filter.
    m = re.search(r"\bND\s*\(\s*(?:ca\.?\s*)?(1[3-9]\d{2})(?:\s*[-–]\s*(\d{2,4}))?", meta)
    if not m:
        return None
    yf = int(m.group(1))
    if m.group(2):
        frag = m.group(2)
        yl = int(frag) if len(frag) == 4 else int(str(yf)[: 4 - len(frag)] + frag)
    else:
        yl = yf
    if yl < yf:
        yf, yl = yl, yf
    return (yf, yl, False)


def parse_ruler_from_meta(meta_line: str | None, body: str | None, ruler_hint: str | None) -> str | None:
    """Bruun parser sometimes mis-attributes a mintmaster name as `ruler`
    (e.g. "Hans Seyer" → ruler="Hans"). The meta_line carries the actual
    ruler after the period name + mint. Pattern: `<Country>. <Type>, <year>. <Mint> Mint. <RULER>. NGC ...`

    Meta and body may have line-break splits ("Christian \nII"). We
    normalise whitespace before matching."""
    text = " ".join((meta_line or "", body or ""))
    text = re.sub(r"\s+", " ", text)
    # Check "Hans Mule" — a real ruler-equivalent (archbishop) for Oslo 1523-24
    if re.search(r"\bHans\s+Mule\b", text):
        return "Hans Mule"
    # Christian III / II / I — III must be checked first to win match (III contains II)
    for r in ["Christian III", "Christian II", "Frederik I", "Frederick I"]:
        if re.search(rf"\b{re.escape(r)}\b", text):
            return r
    return ruler_hint


def parse_mint(lot: dict) -> str | None:
    """Extract mint from meta_line: pattern `<Mint> Mint.` typically.

    Also supports the «<Modern> (<Period>) Mint.» / «<Period> (<Modern>) Mint.»
    bilingual form (Bruun PDF uses for Nidaros/Trondheim etc.). Returns
    the period-canonical name when both are present.
    """
    meta = lot.get("meta_line") or ""
    # Bilingual «Nidaros (Trondheim) Mint» / «Trondheim (Nidaros) Mint»
    m = re.search(
        r"\b(Nidaros|Trondheim)\s*\([^)]+\)\s+Mint\b",
        meta,
    )
    if m:
        # Canonical: use the period name. «Nidaros» is the period name,
        # «Trondheim» is modern. When matched first capture is one of
        # them, return as-is — both forms are widely understood.
        return m.group(1)
    # Direct ".Malmö Mint." or "Copenhagen Mint." patterns
    m = re.search(
        r"\b(Copenhagen|København|Malmö|Malmø|Malmo|Husum|Gottorp|Roskilde|"
        r"Aarhus|Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|"
        r"Helsingør|Helsingor|Lund|Nidaros|Trondheim|Lübeck|Hamburg|"
        r"Altona|Glückstadt|Gluckstadt|Rendsburg|Schwerin)\s+Mint\b",
        meta,
    )
    if m:
        return m.group(1)
    # Without "Mint" suffix
    m = re.search(
        r"\b(Copenhagen|København|Malmö|Husum|Gottorp|Roskilde|Aarhus|Ribe|"
        r"Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|Helsingør|Lund|"
        r"Nidaros|Trondheim)\b",
        meta,
    )
    if m:
        return m.group(1)
    return lot.get("mint")


# Leading region word of a «. »-delimited TERRITORY segment. Used to strip
# country/territory prefixes off the denomination WITHOUT mistaking a
# denom-first lot («Skilling. Mint Error …») for a territory. Derived from
# the META_SUBNATIONAL_TO_ENTITY token set.
_TERRITORY_LEAD = re.compile(
    r"^(?:schleswig|holstein|l[üu]beck|bremen|oldenburg|hesse|gotland|"
    r"f[üu]rstbisthum|fuerstbisthum|erzbisthum|gottorp|sonderburg|s[øo]nderborg|"
    r"norburg|gl[üu]cksburg|schauenburg|pinneberg|rantzau|lauenburg|"
    r"osnabr[üu]ck|wismar|verden|"
    # Foreign / Baltic secondary realms that prefix the denom on
    # Swedish-section lots («SWEDEN. Swedish Livonia. Riga. 5 Ducats»).
    r"swedish|livonia|riga|reval|pomerania|stralsund|stade)\b",
    re.IGNORECASE,
)


def _denom_from_text(text: str) -> str | None:
    """Pull the denomination from one «<COUNTRY>[. <TERRITORY>…]. <denom>,
    <year>.» string. The year after the comma may be Arabic (1589), Roman
    (MDCIII), or «ND[ (year)]»."""
    # PDF line-wrap repair: de-hyphenate split words («Bishop-\nric» →
    # «Bishopric») then collapse ALL whitespace (incl. the newline that wraps a
    # truncated «… Pinneberg.» territory from its «Taler, 1589» denom onto the
    # next line — without this the «.»-class regex can't cross the newline).
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Year lookahead accepts: «(» / digit / «ND…» / a Roman-numeral run
    # (≥2 uppercase Roman chars — «MDCIII», «MDCXCII»). The {2,} guard keeps a
    # stray capitalised word («Mint», «Mule») from being read as a year. An
    # optional leading quote («5 Ducats, "1645"») is skipped — Bruun
    # occasionally quotes a coin's stated (non-actual) date.
    m = re.match(
        r"^[^.]+\.\s+(.+?),\s*[“”\"'‘’]?\s*"
        r"(?:ND(?:\s*[.\(]|\b)|[\(\d]|[MDCLXVI]{2,}\b)",
        text,
    )
    if not m:
        return None
    d = m.group(1).strip()
    # Strip leading COUNTRY/TERRITORY «. »-segments: the denom is the first
    # segment that is NOT a known territory. Handles «Schleswig-Holstein-
    # Schaumburg-Pinneberg. Taler» → «Taler» and «Lübeck (Bishopric). Taler»
    # → «Taler», while keeping a denom-FIRST lot intact («Skilling. Mint
    # Error — …» → «Skilling», not the trailing error annotation).
    while ". " in d:
        head, rest = d.split(". ", 1)
        if _TERRITORY_LEAD.match(head):
            d = rest.strip()
        else:
            d = head.strip()
            break
    # Source-gap guards (no denomination actually printed):
    #   • «DENMARK. , 1572» → empty / digit-only residue
    #   • «… Lübeck (Bishopric), 1608-IG» → year directly after territory, so
    #     the residue IS the trailing territory (still matches _TERRITORY_LEAD)
    # Both must yield None, not a junk «denom».
    if not d or not re.search(r"[A-Za-zÀ-ÿ]", d):
        return None
    if _TERRITORY_LEAD.match(d):
        return None
    return d


def parse_denomination(meta: str | None, body: str | None) -> str | None:
    """Extract a denomination string from the lot's meta_line, falling back
    to the body_excerpt when the meta_line is truncated.

    Patterns supported:
      A. «<COUNTRY>. <denom>, <year>.»          — standard dated form
      B. «<COUNTRY>. <denom>, ND.»              — undated (ND with period)
      C. «<COUNTRY>. <denom>, ND (year).»       — undated with attribution
      D. «<COUNTRY> . <TERRITORY>. <denom>, …»  — German-states territory prefix
      E. Roman-numeral dated «… <denom>, MDCIII (1603).»

    BODY FALLBACK (2026-06-09): the PDF line-wrap routinely truncates the
    meta_line of German-states lots to «GERMANY . Schleswig-Holstein-
    Schaumburg-Pinneberg.» — the denom + year wrap onto the body's first
    line. The body_excerpt always carries the full «COUNTRY. TERRITORY.
    <denom>, <year>. Mint…» header, so when the meta_line yields nothing we
    re-run the same extraction on the body. (Fixes 18 nominal-less Bruun
    seeds — German Schauenburg/Sonderburg Taler + Roman-dated Speciedaler.)
    """
    for text in (meta, body):
        if not text:
            continue
        d = _denom_from_text(text)
        if d:
            return d
    return None


_FRACTION_GLYPHS = {
    "1/2": "½", "1/3": "⅓", "2/3": "⅔", "1/4": "¼", "3/4": "¾",
    "1/8": "⅛", "3/8": "⅜",
}


def _bruun_display_nominal(raw: str | None) -> str | None:
    """Reader-facing display normalisation for a raw Bruun denomination.

    The seed's nominals were normalised once by a now-removed pass; the live
    parser emits the raw catalogue string. This reproduces that normalisation so
    fresh / new entries render cleanly AND a regen of existing entries is a
    no-op (existing nominals are additionally soft-preserved via the builder's
    `extra_curated_fields={'nominal'}`, which covers the ~24 curated/special
    cases — Portugaløser-canonical, inconsistent value-parens, editorial
    prefixes — that aren't algorithmically reproducible).

    Steps (reproduces 1075/1099 of the committed seed exactly):
      • strip a trailing «Klippe» / «, Klippe» form-qualifier (→ note territory);
      • strip a NAME-only parenthetical «(Rhinsk Gulden)» but KEEP a VALUE
        parenthetical «(3 Mark)» (leading digit) — a value equivalence;
      • ASCII fractions → unicode glyphs, incl. mixed «2 1/2»/«1-1/2» → «2½»/«1½»;
      • ø-spelling of the Danish denomination words;
      • then the shared `normalise_nominal_display` (Noble→Nobel, Halv→½,
        roman→arabic, implicit «1 », location/editorial strip)."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = re.sub(r",?\s+Klippe\b", "", s)
    s = re.sub(r"\s*\((?!\s*\d)[^)]*\)", "", s).strip()   # drop NAME-paren, keep VALUE-paren
    s = re.sub(
        r"(\d)[\s-]+(1/2|1/3|2/3|1/4|3/4|1/8|3/8)\b",
        lambda m: m.group(1) + _FRACTION_GLYPHS[m.group(2)], s)
    for ascii_frac, glyph in sorted(_FRACTION_GLYPHS.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(r"(?<!\d)" + re.escape(ascii_frac) + r"(?!\d)", glyph, s)
    s = (s.replace("Portugaloser", "Portugaløser")
          .replace("Sosling", "Søsling")
          .replace("Lovedaler", "Løvedaler"))
    return normalise_nominal_display(s)


# NGC/PCGS grade-colour suffix — applied ONLY to copper/bronze coins (silver
# and gold get a bare numeric grade). Anchored to the «NGC/PCGS <grade> <colour>»
# shape so a stray «brown patina» in prose never false-matches. Matches e.g.
# «NGC MS-64 Brown», «NGC MS-64+ Red Brown», «NGC PROOF-63 BN».
_NGC_GRADE_COLOUR_RE = re.compile(
    r"(?:NGC|PCGS)\s+[A-Z]{2,8}[\s\-]*\d{0,2}\+?\s+(?:RED\s+BROWN|BROWN|BN|RB|RD)\b",
    re.IGNORECASE,
)


def parse_metal(denom: str | None, refs: dict, body: str | None = None) -> tuple[str, bool]:
    """Best-effort metal classification from denomination.

    Returns (metal, verified) tuple. **Bruun does not state the metal
    directly** — it is inferred. So `verified=True` is reserved for the two
    cases where the signal is genuinely RELIABLE, not a denomination-name guess:

      1. **Friedberg ref** present → gold (Friedberg indexes gold coins ONLY by
         catalogue definition — see §BJ source survey). External authority.
      2. **Explicit metal WORD in the nominal** — «Silver Gulden», «Sølvgylden»,
         «Gold Krone», «Goldgulden», «Guldkrone» — the catalogue literally names
         the metal.

    EVERYTHING ELSE is a denomination-NAME heuristic (Ducat→gold, Mark→silver,
    Skilling→billon, Krone→silver/gold-by-value, …) and returns
    `verified=False` — a WEAK signal. Rationale (curator decision 2026-06-03):
    «Krone» is genuinely ambiguous (silver 1–2 Kroner vs gold 10/20 Kroner /
    Guldkrone) and the old code listed bare «krone»/«crown» as a gold token,
    mis-classifying ~79 silver Krone/Mark coins as gold AND marking them
    verified=True — which (per §4) BLOCKED their cross-source merge with the
    silver Hede/Numista foundations, manufacturing silver-vs-gold split-clusters.

    Making the heuristic `verified=False` fixes this at the root: §4 says a
    `*_verified: false` value cannot DISPROVE a merge and is overridden by any
    source-attested metal. So an inferred metal no longer blocks a merge, and
    a real source (Hede/Numista/Friedberg) corrects it in the unified output.
    The heuristic still makes its best GUESS (so orphan-only entries render a
    sensible, `(?)`-marked metal) — it just doesn't claim certainty.

    Bug-fix history: 2026-05-22 the `"fr"` ref check was case-sensitive and
    silently never fired (Bruun uses key «Fr»); fixed to lowercase. 2026-06-03
    the krone→gold token + verified=True over-claim was fixed per the above.
    """
    refs_lc = {k.lower() for k in (refs or {})}
    # (1) Friedberg ref — reliable external gold signal, regardless of denom.
    if "fr" in refs_lc or "friedberg" in refs_lc:
        return ("gold", True)
    d = (denom or "").lower()
    # (2) Explicit metal WORD in the nominal — the catalogue names the metal.
    # SILVER takes precedence and is matched broadly («silver»/«sølv») so that
    # «Sølvgylden», «Halv Sølvgylden», «Silver Gulden», «Sølvafslag …» never
    # fall through to a gold heuristic. Safe: no gold coin carries «silver»/«sølv».
    if "silver" in d or "sølv" in d or "joachimstaler" in d or "joachimsdaler" in d:
        return ("silver", True)
    # GOLD word: «gold» (English, unambiguous) or a SPECIFIC guld-gold compound.
    # NOT bare «guld» — that would mis-catch «Guldengroschen» (a SILVER Guldiner)
    # and the metal-ambiguous «gulden» family.
    if "gold" in d or "guldkrone" in d or "guldgylden" in d or "guldreal" in d:
        return ("gold", True)
    # (3) NGC/PCGS grade-COLOUR suffix → copper. NGC applies a colour code
    # (Red «RD» / Red-Brown «RB» / Brown «BN», or spelled-out «Brown» / «Red
    # Brown») ONLY to copper/bronze coins; silver and gold get a bare numeric
    # grade. So «NGC MS-64 Brown» in the lot body is a strong physical metal
    # signal that overrides the weak denomination-NAME heuristics below
    # (Skilling→billon, klippe→silver, Øre→default-silver). It is INDIRECT
    # (names surface colour, not assayed fineness) → verified=False, so per §4
    # it cannot block a cross-source merge and a source that assays the metal
    # still overrides it. Placed AFTER the explicit metal-WORD checks so a
    # «Sølv…»-named piece is never overridden. Caught 2026-06-10: siege klippe
    # (dk-bruun-7277) + the Øre / Rigsbanktegn / small-Rigsbankskilling copper
    # series were mis-rendered silver/billon.
    if body and _NGC_GRADE_COLOUR_RE.search(body):
        return ("copper", False)
    # --- denomination-NAME heuristics below: weak guess → verified=False ---
    if not d:
        return ("silver", False)  # safest default — no source signal
    if "10 kroner" in d or "20 kroner" in d:  # Danish gold-standard gold coins
        return ("gold", False)
    if any(t in d for t in [
        "nobel", "goldgulden", "rhinsk gylden", "ungersk gylden", "ungarsk gylden",
        "ducat", "dukat", "guldreal", "portugaløser", "portugaloser",
        "sovereign",  # Christian IV 1608 Sovereign (Hede 19) — gold prestige
        "d'or", "d’or", "dor",  # Pistolen-family (Christian/Frederik d'Or)
        "pistol",  # Pistole, Half Pistole etc.
    ]):
        return ("gold", False)
    if "klipping" in d or "klippe" in d:
        return ("silver", False)
    if "hvid" in d or "penning" in d or "blaffert" in d:
        return ("billon", False)
    if "skilling" in d or "søsling" in d or "sosling" in d:
        return ("billon", False)  # most pre-1541 skillinge are debased
    if "mark" in d:
        return ("silver", False)
    return ("silver", False)


def parse_mintmaster(body: str | None) -> str | None:
    """Pull `Mintmaster: <Name>` from body_excerpt."""
    if not body:
        return None
    m = re.search(r"Mintmaster:\s*([A-ZÆØÅa-zæøå .,()\-]+?)(?:\.|$|\sAn |\sExcept)", body)
    if m:
        return m.group(1).strip(" .,")
    return None


def parse_rarity(rarity: str | None) -> str | None:
    if not rarity:
        return None
    r = rarity.strip().upper()
    if "EXTREMELY" in r:
        return "RRR"
    if "VERY RARE" in r or "VRARE" in r:
        return "RR"
    if "RARE" in r:
        return "R"
    return None


def lot_id(part: int, lot: dict) -> str:
    refs = lot.get("refs") or {}
    bruun_id = refs.get("Bruun")
    if bruun_id:
        return f"dk-bruun-{bruun_id}"
    return f"dk-bruun-pt{part}-{lot.get('lot_no')}"


# Build coin entry ----------------------------------------------------


def build_coin_entry(part: int, lot: dict) -> dict | None:
    year = parse_year(lot)
    if year is None or not (YEAR_FROM <= year <= YEAR_TO):
        return None
    region = (lot.get("region") or "").strip()
    if region not in REALM_REGIONS:
        return None

    # CLAUDE.md §9.1 — patterns / trial strikes / off-metal strikes never
    # reach the seed. The Phase 2 parser (`scripts/bruun_parser/02_parse_lots.py`)
    # sets `is_pattern: true` on lots whose meta/body matches the trial-strike
    # regex (Pattern / Probe / Essai / Pn-ref / Piefort / Piedfort / Sølvafslag
    # / Guldafslag / off-metal strike); the seed builder consumes that flag —
    # per the linear-pipeline principle, Phase 3 reads only Phase 2 output, no
    # re-parsing of body text here.
    if lot.get("is_pattern"):
        return None

    meta = lot.get("meta_line") or ""
    body = lot.get("body_excerpt") or ""
    refs = lot.get("refs") or {}
    ruler = parse_ruler_from_meta(meta, body, lot.get("ruler"))
    mint = parse_mint(lot)
    # parse_metal MUST see the RAW denomination (descriptive parens intact):
    # «12 Mark (Courant Ducat)» → the «Ducat» token drives the gold heuristic,
    # «8 Skilling (klippe)» → the «klippe» token drives the silver heuristic.
    # _bruun_display_nominal strips those name-parens for the rendered nominal,
    # so it must run AFTER metal classification — otherwise the metal signal is
    # lost (regression caught 2026-06-10: 7661 gold→silver, 4156/7277 →billon).
    raw_denom = parse_denomination(meta, body)
    metal, metal_verified = parse_metal(raw_denom, refs, body=body)
    denom = _bruun_display_nominal(raw_denom)
    mintmaster = parse_mintmaster(body)

    # GENERIC catalogue mapping (§CJ): schema-field keys → typed; every other
    # key — Bruun's Swedish-specific cats (lott/delzanno/sm/hagander/appelgren/
    # mb_swedish/hauberg/malmer, mapped to non-schema names in REF_FIELDS) AND
    # any code our schema doesn't type (Aagaard, Pn, future catalogues) →
    # `others` as «Label# value». Nothing dropped, nothing breaks validation.
    catalog: dict[str, Any] = catalog_from_ref_dict(refs, REF_FIELDS)
    # Special: Jensen-Skjoldager key in Bruun refs (cited as "Jensen & Skjoldager-...")
    if "Jensen & Skjoldager" in body:
        m = re.search(r"Jensen\s*&?\s*Skjoldager-?\s*([A-Z0-9/\-,. ]+?)(?:[;.]|\sschou|\sweight)", body, re.IGNORECASE)
        if m:
            catalog["jensen_skjoldager"] = m.group(1).strip().rstrip(",;")

    # Norwegian region marker
    is_norway = "NORW" in region

    # Scope-gate for GERMANY / SWEDEN regions (added 2026-05-25 alongside
    # REALM_REGIONS expansion). Bruun catalogue carries ~100 GERMANY +
    # ~180 SWEDEN lots; only those tagging a known project entity
    # (SH-duchy, Bremen-Verden, Hesse-Kassel, Plön, Holstein-Schauenburg,
    # bishopric Lübeck/Osnabrück) belong in-scope. The mint→entity
    # classifier handles cases where the lot's mint pins down an entity
    # (Steinbeck Mint → gottorp_duchy); _classify_via_meta_line handles
    # cases where the subnational annotation is only in meta_line. Lots
    # that fall through to the `danish_realm` default — pure Swedish
    # coinage (Stockholm Mint), Pomerania, Livonia, Mainz, Erfurt — are
    # genuinely out of project scope and MUST NOT enter the seed.
    if region in {"GERMANY", "SWEDEN"}:
        entity_check = _classify_entity(mint, is_norway, meta_line=meta, year=year)
        if entity_check in {"danish_realm", "danish_norway"}:
            return None

    cid = lot_id(part, lot)
    # Year fields: an «ND (…)» attribution carries a range + the undated flag
    # (year_verified=False → «(?)» marker); a dated strike keeps the plain
    # single year. See parse_year_span / SOURCES.md §13.3.
    span = parse_year_span(lot)
    if span:
        yf, yl, yv = span
        year_fields: dict[str, Any] = {
            "year_label": str(yf) if yf == yl else f"{yf}-{yl}",
            "year_first": yf,
            "year_last": yl,
            "year_ranges": [[yf, yl]],
            "year_verified": yv,
        }
    else:
        year_fields = {
            "year_label": str(year),
            "year_first": year,
            "year_last": year,
            "year_ranges": [[year, year]],
        }
    entry: dict[str, Any] = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "bruun",
        "kind": "kurant",
        "nominal": denom,
        **year_fields,
        "ruler": ruler,
        "mint": mint,
        "catalog": catalog,
        "metal": metal,
        "metal_verified": metal_verified,
        "fineness": None,  # not in Bruun lot data; comes from spec tables (Wilcke)
        "weight_rough_g": lot.get("weight_g"),
        "issuing_entity": _classify_entity(mint, is_norway, meta_line=meta, year=year),
        "verified": False,
        "fineness_verified": False,
        "weight_rough_verified": bool(lot.get("weight_g")),
        "mint_verified": bool(mint),
        "sources": [_build_bruun_source(part, lot)],
        "verification_note": {
            "de": (
                "Bruun-Seed: spezifikische Münzfuß- und Phase-Zuordnung sowie "
                "Per-Münze-Verifikation stehen noch aus; Daten direkt aus dem "
                "Bruun-Auktionskatalog (Stack's Bowers L. E. Bruun Collection 2024-2026) "
                "übernommen. Brutto-Gewicht ist ein per-Specimen-Wert; Feingehalt "
                "fehlt in Bruun-Daten und folgt aus dem Wilcke 1950-Ordonnance-"
                "Spezifikations-Tabel (s. docs/research/moentordning_1541.md)."
            ),
            "en": (
                "Bruun seed: Müntzfuß and phase assignment plus per-coin "
                "verification are still outstanding; data taken directly from "
                "the Bruun auction catalogue (Stack's Bowers L. E. Bruun "
                "Collection 2024-2026). Brutto weight is a per-specimen value; "
                "fineness is not in Bruun data and follows from the Wilcke 1950 "
                "ordinance specification table (see docs/research/moentordning_1541.md)."
            ),
            "uk": (
                "Bruun-seed: призначення Müntzfuß і фази та покоінна верифікація "
                "ще очікуються; дані взято безпосередньо з аукціонного каталогу "
                "Bruun (Stack's Bowers L. E. Bruun Collection 2024-2026). "
                "Brutto-вага це per-specimen значення; проба відсутня в Bruun-"
                "даних і випливає з таблиці специфікацій ордонансів Wilcke 1950 "
                "(див. docs/research/moentordning_1541.md)."
            ),
        },
    }

    # Carry mintmaster as a note field (project schema doesn't have dedicated)
    if mintmaster:
        entry["mintmaster"] = mintmaster

    # Per-specimen quality flags (rarity, NGC grade) are NOT in the
    # Coin schema top-level — they describe individual specimens not
    # the coin type. They appear in the Bruun citation `sources[*].ref`
    # text already (Stack's Bowers prints rarity inline) and don't
    # need separate fields.
    # bruun_collection_id / bruun_part / bruun_lot_no / bruun_page
    # belong in catalog (already populated above via REF_FIELDS map);
    # don't duplicate at coin top-level. Schema-strict validation
    # would reject them otherwise.

    return entry


# Main pipeline -------------------------------------------------------


def collect_entries() -> list[dict]:
    entries: list[dict] = []
    trial_skipped: list[tuple[int, int, str]] = []  # (part, lot_no, denomination)
    for part in (1, 2, 3, 4):
        path = CACHE_DIR / f"part{part}.json"
        if not path.exists():
            print(f"  warning: {path} missing — skipping", file=sys.stderr)
            continue
        data = json.loads(path.read_text())
        added = 0
        for lot in data:
            # Diagnostic — count §9.1 trial-strike suppressions for IN-SCOPE
            # lots only (out-of-scope-anyway trials make for thousands of
            # uninteresting noise; we only care about the ones the seed
            # would otherwise have admitted).
            if lot.get("is_pattern"):
                year = parse_year(lot)
                region = (lot.get("region") or "").strip()
                if year is not None and YEAR_FROM <= year <= YEAR_TO and region in REALM_REGIONS:
                    denom_hint = (lot.get("meta_line") or "")[:70]
                    trial_skipped.append((part, lot.get("lot_no", 0), denom_hint))
            entry = build_coin_entry(part, lot)
            if entry:
                entries.append(entry)
                added += 1
        print(f"  part{part}: {added} entries added (from {len(data)} total lots)")
    if trial_skipped:
        print(f"\n  Trial-strike filter (§9.1) suppressed {len(trial_skipped)} in-scope lot(s):")
        for part, lot_no, hint in trial_skipped[:10]:
            print(f"    part{part} lot {lot_no} — {hint}")
        if len(trial_skipped) > 10:
            print(f"    … and {len(trial_skipped) - 10} more")
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="Print summary; do not write file")
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

    print(f"Collecting Bruun pre-1541 realm entries ({YEAR_FROM}-{YEAR_TO})...")
    entries = collect_entries()
    print(f"\nTotal entries: {len(entries)}\n")

    # Sort by year, then by Bruun-id
    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("bruun_collection_id", "")))

    # Summary
    from collections import Counter
    by_ruler = Counter(e.get("ruler") or "?" for e in entries)
    by_mint = Counter(e.get("mint") or "?" for e in entries)
    by_metal = Counter(e.get("metal") or "?" for e in entries)
    print(f"By ruler: {dict(by_ruler.most_common())}")
    print(f"By mint: {dict(by_mint.most_common())}")
    print(f"By metal: {dict(by_metal.most_common())}")

    write_v2_seed(
        entries,
        source_name="bruun",
        source_label="Stack's Bowers L. E. Bruun Collection (parts I-IV, 2024-2026)",
        scope_note=(
            "§AZ Tier 1 — Bruun corpus pre-1541 realm lots, covers the gap "
            "Hede 1971 doesn't catalogue (Christian II + Frederik I + "
            "Christian III pre-1541 Møntordning). NOT a substitute for the "
            "Hede seed at v2/seed/hede/; parallel source."
        ),
        dry_run=args.dry_run,
        no_merge=args.no_merge,
        # `nominal` is soft-preserved across regen: the live parser emits the
        # raw catalogue string and `_bruun_display_nominal` reproduces the
        # algorithmic normalisation for 1075/1099, but ~24 curated/special
        # nominals (Portugaløser-canonical, inconsistent value-parens, editorial
        # prefixes, parser-None → curated) aren't algorithmically reproducible —
        # preserving `nominal` keeps those (and any future curator edit) intact
        # so a regen never degrades a stored nominal.
        extra_curated_fields=frozenset({"nominal"}),
        extra_top_level={
            "scope_year_from": YEAR_FROM,
            "scope_year_to": YEAR_TO,
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
