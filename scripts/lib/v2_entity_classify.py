"""V2 entity classifier — maps a coin's mint(s) to its political entity tag(s).

Used by Phase 3 seed re-grouping (`scripts/maintenance/seed_v2_regroup.py`)
to take V1 location-keyed seed yamls and re-group their coins under
`data/v2/seed/<source>/<entity>.yml` per V2_PIPELINE.md §2/§3.

The mapping is mint-driven, matching the §3.1 migration decision tree
for `gesamtstaat` resolution. When a coin has multiple mints across
different entities, the result is a list-form tag (alphabetical) per
V2_PIPELINE.md §3.10. Unknown mints return `None` (callers route those
to a `_unclassified` bucket the curator reviews).

The mapping is intentionally generous on V2_PIPELINE.md §3.1's strict
table — it covers historical Danish-realm mints (Roskilde, Ribe, Aarhus,
medieval Malmø, etc.) and Norwegian-realm mints (Bergen, Oslo, Gimsø)
that don't appear in §3.1 because the migration only had to resolve
post-1773 `gesamtstaat` cases. Phase 3 sees all historical mints in
the harvested catalogues, so the table is broader.

Year-aware overrides (e.g. Haderslev pre-1660 vs post-1660) are NOT
modelled here. If they prove necessary the helper will grow a
`(mint, year, ruler)` triple signature; for now mint alone suffices
for ~99 % of seed entries.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Mint name normalisation. Catalogues spell the same mint differently —
# Kopenhagen / Copenhagen / København all denote the same place. We collapse
# variants to a stable canonical key BEFORE entity lookup. Match is
# case-insensitive AND parenthesised mintmaster suffixes are stripped.
# ---------------------------------------------------------------------------

# Per-canonical-key set of alternate spellings the parsers / V1 seeds
# actually use (verified against the seed inventory).
_MINT_ALIASES: dict[str, set[str]] = {
    "kopenhagen": {"kopenhagen", "copenhagen", "københavn", "kobenhavn"},
    "altona": {"altona"},
    "glueckstadt": {"glückstadt", "glueckstadt", "glikstadt"},
    "poppenbuettel": {"poppenbüttel", "poppenbuettel"},
    "husum": {"husum"},
    "haderslev": {"haderslev", "hadersleben"},
    "flensburg": {"flensburg", "flensborg"},
    "rendsburg": {"rendsburg", "rendsborg"},
    "schleswig": {"schleswig"},
    "gottorp": {"gottorp"},
    "toenning": {"tönning", "toenning"},
    "kiel": {"kiel"},
    "frederiksborg": {"frederiksborg"},
    "roskilde": {"roskilde"},
    "ribe": {"ribe"},
    "aarhus": {"aarhus", "århus"},
    "malmoe": {"malmø", "malmoe", "malmö", "malmo"},
    "helsingor": {"helsingør", "helsingoer"},
    "visby": {"visby"},
    "landskrona": {"landskrona"},
    "stockholm": {"stockholm"},
    "christiania": {"christiania", "kristiania"},
    "oslo": {"oslo"},
    "kongsberg": {"kongsberg"},
    "bergen": {"bergen"},
    "gimsoe": {"gimsø", "gimsoe"},
    "oldendorf": {"oldendorf"},
    "rinteln": {"rinteln"},
    "rethwisch": {"rethwisch"},
    "mannheim": {"mannheim"},
    "stadthagen": {"stadthagen"},
    "bueckeburg": {"bückeburg", "bueckeburg"},
    "lubeck": {"lübeck", "luebeck", "lubeck"},
    "hamburg": {"hamburg"},
    "eutin": {"eutin"},
    "kaltenhof": {"kaltenhof"},
    "bremervoerde": {"bremervörde", "bremervoerde"},
    "stade": {"stade"},
    "kassel": {"kassel"},
    "barmstedt": {"barmstedt"},
    "sonderburg": {"sønderborg", "sonderburg", "soenderborg"},
    "ploen": {"plön", "ploen"},
    "rantzau": {"rantzau"},
}

# Build reverse-lookup (alias → canonical) once.
_ALIAS_TO_CANON: dict[str, str] = {}
for canon, aliases in _MINT_ALIASES.items():
    for a in aliases:
        _ALIAS_TO_CANON[a.lower()] = canon


# ---------------------------------------------------------------------------
# Canonical mint → political entity mapping. Entity tags must exist in
# `data/i18n/issuing_entities.yml`. Multi-entity / contested cases are
# defaulted to the most common usage in this project's curated V1 data.
# ---------------------------------------------------------------------------

_MINT_TO_ENTITY: dict[str, str] = {
    # Danish realm — Copenhagen + medieval / post-medieval royal Danish mints.
    "kopenhagen": "danish_realm",
    "frederiksborg": "danish_realm",
    "roskilde": "danish_realm",
    "ribe": "danish_realm",
    "aarhus": "danish_realm",
    "malmoe": "danish_realm",        # Danish until Treaty of Roskilde 1658
    "helsingor": "danish_realm",
    "visby": "danish_realm",         # medieval Danish Gotland
    "landskrona": "danish_realm",    # Danish until 1658
    "stockholm": "danish_realm",     # appears in some seeds as historical anchor

    # Royal Holstein — Holstein mints under the Danish king's authority
    "altona": "royal_holstein",
    "glueckstadt": "royal_holstein",
    "poppenbuettel": "royal_holstein",
    "husum": "royal_holstein",       # Royal Schleswig portion
    "haderslev": "royal_holstein",   # follows V1 author's tagging convention
    "flensburg": "royal_holstein",   # Royal-Danish-Schleswig portion (pre-1864)
    "rendsburg": "royal_holstein",

    # Gottorp duchy — Schleswig-Holstein-Gottorp mints
    "gottorp": "gottorp_duchy",
    "toenning": "gottorp_duchy",
    "schleswig": "gottorp_duchy",    # Schleswig city was primarily Gottorp
    "kiel": "gottorp_duchy",

    # Danish-Norway — Norwegian mints under Danish crown
    "christiania": "danish_norway",
    "oslo": "danish_norway",
    "kongsberg": "danish_norway",
    "bergen": "danish_norway",
    "gimsoe": "danish_norway",

    # Holstein-Schauenburg county (Stadthagen + Bückeburg + Pinneberg territory)
    "oldendorf": "holstein_schauenburg_county",
    "rinteln": "holstein_schauenburg_county",
    "stadthagen": "holstein_schauenburg_county",
    "bueckeburg": "holstein_schauenburg_county",

    # Hansa cities + sub-duchies + church state entities
    "hamburg": "hanseatic_hamburg",
    "lubeck": "hanseatic_lubeck",
    "eutin": "fuerstbisthum_luebeck",
    "kaltenhof": "fuerstbisthum_luebeck",
    "bremervoerde": "erzbisthum_bremen_verden",
    "stade": "erzbisthum_bremen_verden",
    "kassel": "landgrafschaft_hessen_kassel",
    "barmstedt": "rantzau_county",
    "rantzau": "rantzau_county",
    "sonderburg": "sonderburg_duchy",
    "ploen": "norburg_plon_duchy",
    "rethwisch": "royal_holstein",   # Rethwisch lay in royal Holstein after 1640

    # Out-of-scope (foreign mint appearing in catalogue cross-references).
    # Setting to None ⇒ coin goes to `_unclassified` bucket for curator review.
    "mannheim": None,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _strip_mintmark_suffix(mint: str) -> str:
    """`Altona (FK VS)` → `Altona`; `Kopenhagen (683.1 M)` → `Kopenhagen`."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", mint).strip()


def _normalise_one_mint(raw: str) -> str | None:
    """Returns the canonical mint key (e.g. `kopenhagen`) or None when no
    alias matches. Strips any parenthesised mintmaster suffix first."""
    stripped = _strip_mintmark_suffix(raw)
    # Direct lookup against alias table (case-insensitive).
    return _ALIAS_TO_CANON.get(stripped.lower())


def classify_mint_to_entity(mint) -> str | list[str] | None:
    """Map a coin's `mint` field (scalar, list, or None) to its political
    entity tag(s).

      * None / unknown / unparseable → returns None (caller routes to
        `_unclassified`).
      * Scalar → str.
      * Multi-mint resolving to ONE entity → str (same entity).
      * Multi-mint resolving to ≥2 distinct entities → sorted list[str].

    The list-form ordering matches V2_PIPELINE.md §3.10 (alphabetical),
    so the alphabetically-first element is the home-file entity.
    """
    if mint is None:
        return None

    raws = mint if isinstance(mint, list) else [mint]
    resolved: set[str] = set()
    any_unknown = False

    for m in raws:
        if not isinstance(m, str):
            any_unknown = True
            continue
        # Handle compound mint strings:
        #   - "København eller Malmø" — 'eller' = 'or' = enumerate alternatives
        #   - "Kopenhagen,Altona" — comma-joined multi-mint (parser sometimes
        #     emits a list as a single comma-string)
        segments = re.split(r"\s+(?:eller|or)\s+|\s*,\s*", m, flags=re.IGNORECASE)
        for seg in segments:
            seg = seg.strip().strip(",")
            if not seg:
                continue
            canon = _normalise_one_mint(seg)
            if canon is None:
                any_unknown = True
                continue
            ent = _MINT_TO_ENTITY.get(canon)
            if ent is None:
                # Known mint, deliberately mapped to None (out-of-scope).
                # We don't add it to resolved, but it's not "unknown" either.
                continue
            resolved.add(ent)

    if not resolved:
        # All mints were unknown or out-of-scope → unclassified.
        return None
    if len(resolved) == 1:
        return next(iter(resolved))
    return sorted(resolved)


def classify_mint_diagnostics(mint) -> dict:
    """Return a structured breakdown of mint→entity for one coin, useful
    for the regroup script's diagnostic report."""
    out: dict = {
        "raw": mint,
        "canon": [],
        "unknown_raw": [],
        "resolved_entities": [],
        "out_of_scope_canon": [],
    }
    if mint is None:
        return out
    raws = mint if isinstance(mint, list) else [mint]
    for m in raws:
        if not isinstance(m, str):
            out["unknown_raw"].append(m)
            continue
        segments = re.split(r"\s+(?:eller|or)\s+|\s*,\s*", m, flags=re.IGNORECASE)
        for seg in segments:
            seg = seg.strip().strip(",")
            if not seg:
                continue
            canon = _normalise_one_mint(seg)
            if canon is None:
                out["unknown_raw"].append(seg)
                continue
            out["canon"].append(canon)
            ent = _MINT_TO_ENTITY.get(canon)
            if ent is None:
                out["out_of_scope_canon"].append(canon)
            else:
                out["resolved_entities"].append(ent)
    return out
