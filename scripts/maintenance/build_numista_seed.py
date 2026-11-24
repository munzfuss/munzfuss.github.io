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
from lib.note_extract import source_note  # noqa: E402

from lib.paths import NUMISTA_CACHE  # noqa: E402

PARSED_DIR = NUMISTA_CACHE / "parsed"

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
        "bruun_collection_id", "bruun_lot",
    }


# Numista labels Danish kings with their English exonyms; the project uses
# the Danish form (e.g. «Hans», 217× canonical). Map the King-Hans exonyms
# to the Danish canonical. (The systemic «Frederick» → «Frederik» divergence
# is a broader, separate ruler-canonicalisation pass — not handled here yet.)
_NUMISTA_RULER_CANON = {
    "John I (Hans I)": "Hans",
    "John I": "Hans",
    # The two Holstein dukes Numista ALSO files under a «John …» name. Folded
    # to the canonical the project settled 2026-06-03 (`f5374d0` + `1e15579`,
    # ~413 coins): the Gottorp duke is «Johann Adolf»; the Norburg-Plön one
    # keeps his numeral so the two never collapse into each other.
    "John Adolphus": "Johann Adolf",
    "John Adolphus (Johann Adolf)": "Johann Adolf",
    "John Adolphus I": "Johann Adolf I",
    # Johann Friedrich von Holstein-Gottorp, archbishop of Bremen 1596-1634.
    # Where Numista supplies its own German gloss we take it; the bare English
    # «John Frederick» is left as published — it names the right MAN either
    # way, and turning every English exonym into its period form is a separate
    # pass across all sources, not a side effect of this fix.
    "John Frederick (Johann Friedrich)": "Johann Friedrich",
    "John Frederick of Holstein-Gottorp (Johann Friedrich von Holstein-Gottorp)":
        "Johann Friedrich von Holstein-Gottorp",
}

# «John» ALONE is the Danish-Norwegian Hans — either King Hans (John I,
# r. 1481-1513) or Hans den Yngre of Sonderburg, whom Numista files as the
# bare «John» (ruler id 8940). Numista writes that man four ways, all still
# him: «John», «John I», «John (Hans)», «John I (Hans I)».
#
# So what FOLLOWS «John» decides: nothing, a regnal numeral, or a parenthetical
# means Hans; another given name means another man entirely. The previous rule
# `^\s*John\b` matched the given-name case too and rewrote «John Adolphus»
# (Johan Adolf of Gottorp, r. 1590-1616), «John Adolphus I» (Norburg-Plön),
# «John Frederick» and «John George» all to «Hans» — destroying the name before
# the merger could apply its own carefully guarded folds for these very people.
# Danish sources call the Gottorp duke «Johan Adolf» and never «Hans».
# Parenthetical groups repeat (`*`, not `?`): Numista appends reign dates
# as a SECOND group on some routes — «John (Hans) (1483-1513)». The single
# optional group this pattern first shipped with (00fbfdc) rejected that
# shape and sent King Hans through unchanged as «John (Hans) (1483-1513)».
# No live cache record carries the double-paren form today, so nothing was
# mis-seeded, but tests/test_numista_ruler_canon.py covers it because the
# source does produce it — the regression went unnoticed for a session
# because that commit's verification ran only its own new test file.
_KING_HANS_RE = re.compile(r"^\s*John(?:\s+[IVXLC]+)?(?:\s*\([^)]*\))*\s*$")

# Numista ruler RECORDS that carry a wrong name string, keyed by Numista's own
# ruler id. Keyed on the id, not the name, because the defect is in ONE ruler
# record and the name is the broken part — every coin linking that id inherits
# it, including ones we have not cached yet.
#
#   4713 — Numista's record reads «Frederick IX» but is Frederik VI. Numista
#          itself says so three ways, verified 2026-07-30:
#            · its own coin titles for every affected type read «… - Frederik
#              VI» (N#19531, 61491, 142102, 152374);
#            · the same Ruler field prints the reign «1808-1839», which is
#              Frederik VI's (Frederik IX reigned 1947-1972);
#            · the record's `wikidata_id` is Q155002, whose Wikidata label is
#              «Frederick VI of Denmark», king 13 Mar 1808 - 3 Dec 1839.
#          All four affected types are dated 1809-1839, inside that reign and a
#          century before Frederik IX. The substituted spelling is Numista's
#          OWN title form, so this corrects the source from the source rather
#          than imposing a project convention.
_NUMISTA_RULER_ID_ERRATA: dict[int, str] = {
    4713: "Frederik VI",
}


def _canon_numista_ruler(nm: str) -> str:
    """Canonicalise a Numista king name to the project's Danish form.

    Numista writes the Danish-Norwegian king Hans (John I, r. 1481-1513) with
    the English exonym «John» — in several shapes: «John», «John I»,
    «John (Hans)», «John I (Hans I)», any optionally trailed by a
    « (reign-dates)». Hans is the ONLY Danish-Norwegian «John», so ANY leading
    «John» token canonicalises to «Hans». Exact-map hits (`_NUMISTA_RULER_CANON`)
    win first; the regex is the robust fallback that the hardcoded map missed
    (e.g. «John (Hans)» → «Hans», the Norway Bergen Goldgulden N#444264, 2026-07-13).
    """
    if nm in _NUMISTA_RULER_CANON:
        return _NUMISTA_RULER_CANON[nm]
    if _KING_HANS_RE.match(nm):
        return "Hans"
    return nm


def _resolve_ruler(kings: list[dict] | None) -> str | None:
    """Pick the most informative ruler name. Multi-ruler entries get
    joined with « / » per pre_1541 builder convention. Danish exonyms are
    mapped to the project's canonical Danish form via `_canon_numista_ruler`."""
    if not kings:
        return None
    names = []
    for k in kings:
        if isinstance(k, dict) and k.get("name"):
            # A known-wrong ruler RECORD is corrected by its Numista id before
            # any name-based handling — the name is the broken part, so
            # matching on it would be matching on the defect.
            fix = _NUMISTA_RULER_ID_ERRATA.get(k.get("id"))
            if fix:
                names.append(fix)
                continue
            nm = str(k["name"])
            names.append(_canon_numista_ruler(nm))
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
    issuer = canonical.get("issuer")
    # A state that had its coin struck at another state's mint is the issuer;
    # the mint city is only where it was struck (curator 2026-11-24). Numista's
    # issuer decides for these issuers, the mint stays the coin's mint.
    iss_ent = classify_issuer_to_entity(issuer) if issuer else None
    if iss_ent in _ISSUER_OVER_MINT:
        return iss_ent
    if mint:
        ent = classify_mint_to_entity(mint, year=year)
        if ent is not None:
            return ent
    if issuer:
        ent = classify_issuer_to_entity(issuer)
        if ent is not None:
            return ent
    # A generic country («German States», «Germany»): Numista names the
    # issuer again in the title, after the denomination («16 Schilling -
    # Free Hanseatic city of Lübeck – Numista», «12 Grote - City of Bremen»).
    if (issuer or "").strip().lower() in _GENERIC_COUNTRIES:
        for seg in re.split(r"\s+[-–—]\s+", canonical.get("title") or "")[1:]:
            ent = classify_issuer_to_entity(seg)
            if ent is not None:
                return ent
    return None


_GENERIC_COUNTRIES = frozenset({"german states", "germany"})

# Issuers whose coins Numista files under a mint of ANOTHER state: the issuer
# decides the entity, not the mint (the rule the ucoin builder already
# follows — «mint city is not issuer», build_ucoin_seed._resolve_target_entity).
# Measured 2026-11-24 over the whole Numista cache, every case a coin of the
# issuer struck elsewhere: Plön Thaler 1761 at Rethwisch (Plön's own mint
# until the line died out that year; N#41864 = KM 28) and Ducat 1760 at
# Hamburg (N#222051 = KM 27); Gottorp Thaler 1673-1674 at Hamburg (N#313829 =
# KM 118, Bruun lot 14417 the same); Bremen 2 Mark 1904 at Hamburg (N#20410,
# KM 250, mint J); Lauenburg ⅔ Thaler 1830 at Altona (N#31393). NOT for the
# issuers of one sovereign's several territories — «Denmark», «Norway»,
# «Danish duchies of Schleswig and Holstein», «Holstein-Schaumburg-Pinneberg»:
# there the mint and the currency system decide between danish_realm /
# royal_holstein / royal_slesvig / danish_norway (or Pinneberg / Schaumburg),
# which is no commission at another state's mint.
_ISSUER_OVER_MINT = frozenset({
    "norburg_plon_duchy",
    "gottorp_duchy",
    "hanseatic_bremen",
    "herzogtum_sachsen_lauenburg",
})


_SPACED_DASH = re.compile(r"\s+-\s+")


def _split_dash_list(value):
    """Numista sometimes prints several numbers of one catalogue as one
    reference joined by spaced dashes — «Lange 69 - 70a - 71a - 73a» (Numista
    129062). Split those into a list. One spaced dash is a RANGE («Jungk# 366 -
    371», «Lange 21 - 22») and stays a string; only two or more separators make
    a list, since a range has exactly one."""
    if isinstance(value, list):
        out: list = []
        for v in value:
            r = _split_dash_list(v)
            out.extend(r if isinstance(r, list) else [r])
        return out
    if isinstance(value, str) and len(_SPACED_DASH.findall(value)) >= 2:
        return [p.strip() for p in _SPACED_DASH.split(value) if p.strip()]
    return value


# Numista prints some Hede references with the ruler volume in front and a dot
# before the sub-letter: «C4 80.C» = Christian IV, Hede 80C (N#307035). The
# merger already scopes a bare Hede number by the record's ruler, so only the
# number is kept, in the form every other source gives («80C»). The prefix must
# name the record's own ruler (C = Christian, F = Frederik, H = Hans, + regnal
# number); a prefix naming another king is left as printed. A bare «80.C» (no
# prefix) is the same number.
_HEDE_RULER_PREFIX_RE = re.compile(
    r"^(?:(?P<k>[CFH])(?P<n>\d{1,2})?\s+)?(?P<num>\d+)\.(?P<sub>[A-Za-z]{1,2})$")
_HEDE_PREFIX_KING = {"C": "Christian", "F": "Frederik", "H": "Hans"}
_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII",
          8: "VIII", 9: "IX", 10: "X"}


def _normalise_hede_value(value, ruler: str | None = None):
    """«C4 80.C» → «80C» when the prefix names `ruler`; «80.C» → «80C».
    Anything else (and a list's other members) is returned unchanged."""
    if isinstance(value, list):
        out: list = []
        for v in value:
            n = _normalise_hede_value(v, ruler)
            if n not in out:
                out.append(n)
        return out
    if not isinstance(value, str):
        return value
    m = _HEDE_RULER_PREFIX_RE.match(value.strip())
    if not m:
        return value
    if m.group("k"):
        king = _HEDE_PREFIX_KING[m.group("k")]
        if m.group("n"):
            king = f"{king} {_ROMAN.get(int(m.group('n')), m.group('n'))}"
        if (ruler or "").strip() != king:
            return value
    return f"{m.group('num')}{m.group('sub').upper()}"


def _filter_catalog(refs: dict[str, str] | None,
                    ruler: str | None = None) -> dict[str, str]:
    """Drop keys not in our schema (strict-extra), split spaced-dash lists and
    take the ruler prefix off a Hede number (`_normalise_hede_value`)."""
    if not refs:
        return {}
    out = {k: _split_dash_list(v) for k, v in refs.items() if k in _ALLOWED_CATALOG}
    if "hede" in out:
        out["hede"] = _normalise_hede_value(out["hede"], ruler)
    return out


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


# Numista issuer → the Krause section its KM numbers belong to, where that
# section has its own numbering (lib.km_registers). «Glückstadt, City of» is
# Krause's Glückstadt section (Numista 154260: KM 26 = 1/16 Reichsthaler
# 1640; Denmark KM 26 is the 6 Speciedaler 1604); «Schleswig and Holstein,
# Danish duchies of» the S-H section (Numista 301630: KM 105 for the
# Speciedaler 1683 that is Glückstadt KM 73).
# The other Schleswig-Holstein houses follow Krause's sections the same way
# (lib.km_registers.KRAUSE_SECTIONS, curator 2026-11-23). Checked 2026-11-23
# against NumisMaster / NGC records of the named section: of 240 Numista KMs
# under these issuers, 233 are the same number in that section with
# overlapping years, the other 7 the same denomination a year or two apart.
# «Schleswig-Holstein-Norburg-Plön, Duchy of» is NOT mapped: Numista files
# Plön and Norburg, two Krause sections, under one issuer.
_ISSUER_TO_KM_REGISTER = {
    "glückstadt, city of": "glu",
    "city of glückstadt (denmark)": "glu",
    "schleswig and holstein, danish duchies of": "sh",
    "danish duchies of schleswig and holstein (german states)": "sh",
    "schleswig-holstein-gottorp, duchy of": "gott",
    "duchy of schleswig-holstein-gottorp (german states)": "gott",
    "schleswig-holstein-sonderburg, duchy of": "sond",
    "county of holstein-schaumburg-pinneberg (german states)": "schpin",
    "holstein-schaumburg-pinneberg, county of": "schpin",
}

# Numista's country sections «Denmark» / «Norway» follow Krause's Denmark /
# Norway volumes. Unlike the sections above they are the ORDINARY volume of
# most coins filed there, so they only decide when the coin routes to an entity
# read in the other volume: N#100478, Christian VI 1 Reisedaler 1732-1733 under
# «Norway», routes to danish_realm by its Copenhagen mint, and its bare «KM 230»
# is Norway KM 230 (NumisMaster MC_92262; Bruun «KM-539 (Denmark); KM-230
# (Norway)»), while Denmark KM 230 is the 3 Speciedaler 1661.
# Two limits, both from the measurement over the whole cache (2026-11-23):
#   * only between the Denmark and Norway volumes — an S-H entity (royal_holstein)
#     filed under «Denmark» has its own rule below (_DENMARK_ISSUER);
#   * only a SINGLE bare KM — Numista lists cross-volume numbers bare side by side
#     (N#119248 under «Norway»: «260» is Norway, «645» is Denmark KM 645), so the
#     section does not name the volume of each member of a list.
_COUNTRY_ISSUER_TO_KM_REGISTER = {
    "denmark": "dk",
    "norway": "nor",
}
_COUNTRY_VOLUMES = frozenset(_COUNTRY_ISSUER_TO_KM_REGISTER.values())

# Numista issuer «Denmark» on a coin that routes to a Schleswig-Holstein entity
# (royal_holstein, by its Altona / Rethwisch / Rendsburg mint): the bare KM is a
# Krause Denmark-volume number, not an S-H-section one. Checked 2026-11-23
# against NumisMaster / NGC «DENMARK» records by KM and years: 66 of 68 such
# records match the Denmark volume. The two exceptions are the Rendsburg pieces
# (N#88660 KM 6, N#89702 KM 5), which are Krause HOLSTEIN-GOTTORP-RENDSBORG
# numbers (NumisMaster MC_66626 / MC_66636; Denmark KM 5 / 6 are the Penning
# 1602) — hence mint Rendsburg → «hgr». A list is folded only when all its
# numbers share one base («640», «640.1»); a list of different bases may mix
# volumes (the N#119248 case) and stays as printed.
_DENMARK_ISSUER = "denmark"
_RENDSBURG_KM_REGISTER = "hgr"
_KM_BASE_RE = re.compile(r"([A-Za-z]*\d+)")


def _km_single_base(vals) -> bool:
    bases = set()
    for v in vals:
        m = _KM_BASE_RE.match(str(v).strip())
        if not m:
            return False
        bases.add(m.group(1).upper())
    return len(bases) == 1


def _mint_is_rendsburg(mint) -> bool:
    ms = mint if isinstance(mint, list) else [mint]
    return any("rendsburg" in str(m or "").lower() for m in ms)


def _apply_km_country_register(catalog: dict, entity, issuer: str | None = None,
                                mint=None) -> None:
    """Fold Numista's «<km> (<Country>)» volume tags into the register-keyed dict
    form ``{register: km}`` the schema uses for cross-volume KMs (KMRef). A bare
    (untagged) value takes the Krause section of the Numista issuer when it has
    one (`_ISSUER_TO_KM_REGISTER`), or the country volume of the issuer when that
    differs from the entity's own volume (`_COUNTRY_ISSUER_TO_KM_REGISTER`, a
    single bare value between the Denmark and Norway volumes only), or — issuer
    «Denmark» on an S-H-group entity — the Denmark volume («hgr» for mint
    Rendsburg; `_DENMARK_ISSUER`), else the coin's own entity register. In place; a no-op when every value is
    bare and in the entity's own volume, and left untouched entirely if any tag
    names a country we don't map (e.g. «(OM)») or a bare value has no
    resolvable register."""
    km = catalog.get("km")
    if km is None:
        return
    vals = km if isinstance(km, list) else [km]
    iss = (issuer or "").strip().lower()
    issuer_reg = _ISSUER_TO_KM_REGISTER.get(iss)
    # _ENTITY_TO_KM_REGISTER is the single source of truth for entity→volume.
    from lib.km_registers import ENTITY_TO_KM_REGISTER as _ENTITY_TO_KM_REGISTER
    reg_entity = entity[0] if isinstance(entity, list) else entity
    own_reg = _ENTITY_TO_KM_REGISTER.get(reg_entity)
    country_reg = _COUNTRY_ISSUER_TO_KM_REGISTER.get(iss)
    if (issuer_reg is None and country_reg and own_reg in _COUNTRY_VOLUMES
            and country_reg != own_reg and isinstance(km, str)
            and "(" not in km):
        issuer_reg = country_reg
    from lib.km_registers import match_group as _match_group
    if (issuer_reg is None and iss == _DENMARK_ISSUER
            and any(_match_group(_ENTITY_TO_KM_REGISTER.get(e)) == "sh"
                    for e in (entity if isinstance(entity, list) else [entity]))
            and not isinstance(km, dict)
            and not any("(" in str(v) for v in vals) and _km_single_base(vals)):
        issuer_reg = (_RENDSBURG_KM_REGISTER if _mint_is_rendsburg(mint)
                      else _COUNTRY_ISSUER_TO_KM_REGISTER[_DENMARK_ISSUER])
    if not any("(" in str(v) for v in vals):
        if issuer_reg and not isinstance(km, dict):
            catalog["km"] = {issuer_reg: km}
        return
    entity_reg = issuer_reg or own_reg
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


# §9.1 trial/pattern strikes + §9.3 off-metal/off-strikes — never struck for
# circulation; CLAUDE.md §9 excludes them from the coin table. build_hede_denmark_seed
# filters these structurally; the Numista builder had no such filter, so a Bremen
# «½ Groten (Gold pattern strike)» and a Frederik IV «16 Skilling (Gold, 2 ducat
# equivalent)» off-metal strike (KM «505 (OM)») slipped into the seed — caught
# 2026-06-25.
#
# We trigger on the Numista TITLE («(Gold pattern strike)», «trial strike»,
# «(Pattern)», «off-metal», «…afslag») and the off-metal «(OM)» KM marker — NOT on
# the bare Krause «Pn» catalogue number. Curator decision 2026-06-25: «Pn» is an
# UNRELIABLE exclusion signal — Krause numbers BOTH genuine die-trials AND unique
# FULL-VALUE pieces «Pn» (e.g. Frederik III Portugaløser «PnD20», 5 Ducats «PnJ16»).
# The latter are not off-metal and not trial strikes — unique gold coins that could
# have circulated at face value — so they stay (user: «нехай будуть у нас»). The
# title is the reliable discriminator; every genuine trial in the cache says so in
# its title.
_KM_OFFMETAL_RE = re.compile(r"\(OM\)", re.I)             # KM «505 (OM)»
_TITLE_PATTERN_RE = re.compile(
    r"pattern strike|trial strike|\(pattern\)|\bprobe\b|\bessai\b|prøvemønt", re.I)
_TITLE_OFFSTRIKE_RE = re.compile(
    r"off[- ]metal|guldafslag|sølvafslag|\bafslag\b", re.I)
# §9.5 OFF-NOMINAL presentation strikes (curator decision 2026-06-25; CLAUDE.md
# §9 item 5): a piece whose stamped nominal is MUCH SMALLER than the intrinsic
# value of its metal weight — e.g. a «1 Krone» struck on a 5-ducat gold planchet
# (Numista titles it «5 Ducats», value.raw «1 Krone», KM PnJ16). Same metal as the
# nominal (so NOT off-metal), but it would never circulate at its stamped face
# value — a presentation piece, out of scope. Implemented as the detectable proxy
# of that concept: title leading segment is exactly «N Ducat(s)/Dukat» (Numista
# titles these by the bullion WEIGHT) AND value.raw is a non-bullion nominal AND
# the KM index carries «Pn» (the necessary Krause pattern/presentation marker —
# user: «сигнал це Pn в КМ індексі»). The «Pn» gate keeps the rule conservative:
# a merely overweight specimen, a tariff coin or a bad source weight is NOT
# off-nominal. KEPT (not off-nominal): full-value show coins whose nominal IS the
# bullion denomination (Portugaløser, genuine Ducat — value.raw bullion); dual-
# denomination / value-equivalent coins («¼ Ducat / 3 Mark» — the «/» is an
# equivalence); Scheidemünze (the OPPOSITE — nominal > metal value, §6).
_TITLE_SEG_DUCAT_RE = re.compile(r"^[\d¼½¾⅓⅔\s]+(ducats?|dukat)\s*$", re.I)
_VALUE_BULLION_RE = re.compile(r"ducat|dukat|portugal", re.I)
_KM_PN_RE = re.compile(r"^\s*Pn", re.I)                   # Krause pattern/presentation prefix

# §9 OFF-SCOPE by metal — banknotes (paper) and white-metal / tin / pewter
# exonumia (medals, jetons, tokens) are not precious/base-metal circulation
# coinage. The Coin schema metal enum is {silver, gold, billon, copper, lead,
# bronze}; anything in this set is off-scope and dropped at seed time. (A Bremen
# exhibition «Medal» white-metal piece (N#422716) and a «Braunschweigische Bank»
# paper banknote (N#342834) had slipped into the seed — caught 2026-06-30.)
_OFFSCOPE_METALS = {"paper", "white-metal", "white metal", "tin", "pewter"}

# §9.2 exonumia — medals, tokens, jetons, plaquettes carry no circulating
# denomination and are not coinage. Numista titles them «Medal - …»,
# «Token - …», «Jeton - …» and gives value.raw «Medal». (N#422716 Bremen
# exhibition Medal, N#391426 Oldenburg Gustav-Adolf-Festspiele Medal,
# N#400480 Bremen Token — caught 2026-06-30.)
_TITLE_EXONUMIA_RE = re.compile(
    r"^\s*(medal|m[ée]daille|token|jeton|jetton|plaquette)\b", re.I)


def _excluded_strike_reason(title, references, value_raw=None, metal=None) -> str | None:
    """Return a §9 exclusion reason when this Numista type is a trial/pattern
    (§9.1), off-metal (§9.3) or off-nominal presentation strike (§9.5; not struck
    for circulation), off-scope by metal (banknote/exonumia — see _OFFSCOPE_METALS),
    or §9.2 exonumia (medal/token/jeton — see _TITLE_EXONUMIA_RE), else None. Keyed
    on the title + off-metal «(OM)» KM marker + composition metal + value nominal.
    The bare Krause «Pn» number is NOT a standalone trigger (it conflates die-trials
    with full-value pieces); for §9.5 off-nominal it is a NECESSARY gate combined
    with the ducat-weight title + non-bullion nominal."""
    if str(metal or "").strip().lower() in _OFFSCOPE_METALS:
        return f"§9 off-scope metal ({str(metal).strip().lower()}): banknote/exonumia"
    if _TITLE_EXONUMIA_RE.match(title or "") or str(value_raw or "").strip().lower() == "medal":
        return "§9.2 exonumia (medal/token/jeton — no circulating denomination)"
    km = (references or {}).get("km")
    km_vals: list = []
    if isinstance(km, dict):
        for v in km.values():
            km_vals.extend(v if isinstance(v, list) else [v])
    elif isinstance(km, list):
        km_vals = km
    elif km is not None:
        km_vals = [km]
    if any(_KM_OFFMETAL_RE.search(str(v)) for v in km_vals):
        return "§9.3 off-metal strike (KM OM)"
    t = title or ""
    if _TITLE_PATTERN_RE.search(t):
        return "§9.1 pattern (title)"
    if _TITLE_OFFSTRIKE_RE.search(t):
        return "§9.3 off-metal strike (title)"
    seg = t.split(" - ")[0].strip()
    if (_TITLE_SEG_DUCAT_RE.match(seg) and value_raw
            and not _VALUE_BULLION_RE.search(str(value_raw))
            and any(_KM_PN_RE.match(str(v)) for v in km_vals)):
        return "§9.5 off-nominal strike (Pn, titled by ducat weight)"
    return None


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
    catalog.update(_filter_catalog(canonical.get("references"),
                                   _resolve_ruler(canonical.get("kings"))))

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
    _apply_km_country_register(entry["catalog"], routed_ent, canonical.get("issuer"),
                               canonical.get("mint"))
    # _source_note candidate (Phase-1, commit 80a1b62): «obverse / reverse»
    # descriptions joined, cleaned + language-tagged (en) for the later note-
    # selector. Non-schema (underscore) → stripped before the strict Coin schema
    # at final/render. Wiring here (the deferred follow-up) makes a re-seed
    # reproduce it durably instead of dropping the one-off population.
    _obv = ((canonical.get("obverse") or {}).get("description") or "").strip()
    _rev = ((canonical.get("reverse") or {}).get("description") or "").strip()
    _combined = " / ".join(x for x in (_obv, _rev) if x)
    _sn = source_note(_combined or None, "en")
    if _sn:
        entry["_source_note"] = _sn
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
        excl = _excluded_strike_reason(canonical.get("title"),
                                       canonical.get("references"),
                                       (canonical.get("value") or {}).get("raw"),
                                       (canonical.get("composition") or {}).get("metal"))
        if excl is not None:
            by_shape["skipped_strike"] += 1
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
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
