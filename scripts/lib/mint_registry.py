"""Unified mint-canonicalisation registry — single source of truth.

Catalogues spell the same mint many different ways: «Glückstadt» (German
period spelling), «Gluckstadt» (English-language auction catalogues like
Bruun PDF — no umlaut), «Glikstadt» (legacy V1 seeds, some Hede pages),
plus mojibake variants from iso-8859 → utf-8 round-tripping. This module
holds ONE registry that drives BOTH:

  * Mint-string canonicalisation (output spelling) — used by
    `scripts/lib/v2_seed_writer.py::_canonicalise_mint`. Maps any alias
    to the project-canonical display form per CLAUDE.md i18n policy
    (German period spelling: Kopenhagen / Christiania / Glückstadt /
    Altona / Lübeck etc.).

  * Mint → political entity lookup — used by
    `scripts/lib/v2_entity_classify.py::classify_mint_to_entity`. Maps
    any alias to the issuing-entity tag (must exist in
    `data/i18n/issuing_entities.yml`).

Before this module existed (split between `_MINT_CANONICAL` in
v2_seed_writer + `_MINT_ALIASES` in v2_entity_classify), the two tables
could disagree on which alias forms were recognised. Concretely the
ASCII alias `gluckstadt` was in `_MINT_CANONICAL` (so the output got
proper «Glückstadt») but NOT in `_MINT_ALIASES` (so entity lookup
returned None, falling through to a default like `danish_realm`). A
Bruun-parsed Christian IV Glückstadt 1640 Ducat ended up with
`mint: Glückstadt` + `issuing_entity: danish_realm` — internally
inconsistent, broke cross-source merging with the matching ucoin entry
in `royal_holstein.yml`. (2026-05-26 audit found 87 such cases in
project-wide scan of 4812 seed entries.)

Year-aware classification (e.g. Altona pre-1640 = Schauenburg vs
post-1640 = Royal Holstein) is NOT modelled here — this registry gives
the LATE / project-default mapping. Source-specific builders that have
year-aware logic (NumisMaster classifies by issuer-name, not mint) may
override the mint-based default with their own classifier; this is by
design.

Adding a new mint — 5 steps:
  1. Pick a canonical key (ASCII, hyphen-free, lower-case).
  2. Set `aliases` including BOTH ASCII and Unicode spellings every
     parser might produce + period name + modern name + mojibake
     variant. ALL must be lower-case.
  3. Set `display` to the project-canonical form per CLAUDE.md i18n.
  4. Set `entity` to the mint-driven primary entity (None for foreign
     / out-of-scope mints — caller routes to `_unclassified`).
  5. Add a one-line comment with the historical period the entity tag
     reflects (when ambiguity exists).
"""
from __future__ import annotations


# Per-canonical-key registry entry.
#   - aliases: set of LOWERCASE alternate spellings the parsers actually
#              produce. Verified against the seed inventory + cache JSON.
#   - display: project-canonical display form (CLAUDE.md §2a German
#              period spelling for German lands; Danish/Latin period
#              form for Danish-Norwegian lands when distinct).
#   - entity: political-entity tag (must exist in issuing_entities.yml).
#              `None` means «foreign / out-of-scope» — caller routes to
#              `_unclassified`.
_MINT_REGISTRY: dict[str, dict] = {
    # ──────────────────────────── Danish realm ─────────────────────────
    "kopenhagen": {
        # Copenhagen aka København aka Kjøbenhavn (pre-1948 Danish)
        # aka Hafnia (Latin — Christian IV legends). Includes the U+FFFD
        # mojibake form «k�benhavn» (iso-8859 → utf-8 round-trip, distinct
        # from the «?»-mojibake «k?benhavn»), the «Kbh.» abbreviation, and
        # the OCR/typo variants surveyed in the seed inventory (all map to
        # the one canonical «Kopenhagen»). Also «Royal Danish Mint» (Den
        # Kongelige Mønt) — Numista's mint name for the Copenhagen royal
        # mint; the API field reads «Royal Danish Mint», which the seed
        # writer's « Mint»-strip reduces to «Royal Danish» before this
        # lookup, so both forms are listed (mint_text on the page:
        # «Royal Danish Mint (Den Kongelige Mønt), Copenhagen, Denmark»).
        "aliases": {
            "kopenhagen", "copenhagen", "københavn", "kobenhavn",
            "kjøbenhavn", "kjobenhavn", "k?benhavn", "k�benhavn",
            "hafnia", "kbh", "kbh.",
            "royal danish", "royal danish mint",
            # OCR/typo variants (low-count, from seed survey 2026-06-09)
            "københavb", "københanv", "københavhn", "københavnh",
            "københavbn", "købehavn", "københavn.",
        },
        "display": "Kopenhagen",
        "entity": "danish_realm",
    },
    "frederiksborg": {
        "aliases": {"frederiksborg"},
        "display": "Frederiksborg",
        "entity": "danish_realm",
    },
    "roskilde": {
        "aliases": {"roskilde"},
        "display": "Roskilde",
        "entity": "danish_realm",
    },
    "ribe": {
        "aliases": {"ribe"},
        "display": "Ribe",
        "entity": "danish_realm",
    },
    "aarhus": {
        "aliases": {"aarhus", "århus", "?rhus"},
        "display": "Århus",
        "entity": "danish_realm",
    },
    "malmoe": {
        # Danish until Treaty of Roskilde 1658, then Swedish.
        # Project anchors as Danish-era (medieval coinage subject).
        "aliases": {"malmö", "malmø", "malmo", "malmoe", "malm?"},
        "display": "Malmø",
        "entity": "danish_realm",
    },
    "helsingor": {
        # Elsinore (English), Elseneur (French — old auction catalogues).
        "aliases": {
            "helsingør", "helsingor", "helsingoer", "helsing?r",
            "elsinore", "elseneur",
        },
        "display": "Helsingør",
        "entity": "danish_realm",
    },
    "visby": {
        # Medieval Danish Gotland (then Swedish 1645+).
        "aliases": {"visby"},
        "display": "Visby",
        "entity": "danish_realm",
    },
    "landskrona": {
        # Danish until 1658, then Swedish.
        "aliases": {"landskrona"},
        "display": "Landskrona",
        "entity": "danish_realm",
    },
    "stockholm": {
        # Appears as historical anchor on some Hans-era pages
        # (Sweden under Kalmar Union pre-1521).
        "aliases": {"stockholm"},
        "display": "Stockholm",
        "entity": "danish_realm",
    },
    "lund": {
        "aliases": {"lund"},
        "display": "Lund",
        "entity": "danish_realm",
    },
    "aalborg": {
        # Aalborg / Ålborg — Danish royal mint. In-scope Hans / Christian II
        # coinage 1481-1525 (22 KMM / Numista types) classifies danish_realm
        # via nation; the mint entry keeps mint-driven classification aligned.
        "aliases": {"aalborg", "ålborg", "?lborg"},
        "display": "Aalborg",
        "entity": "danish_realm",
    },

    # ────────────────────────── Royal Holstein ─────────────────────────
    "altona": {
        # Pre-1640 Altona under Holstein-Pinneberg (House of Schaumburg
        # rule, Adolf XIII / Ernst III / Otto V). Otto V died childless
        # 1640 — House of Schaumburg extinct; Holstein-Pinneberg merged
        # with the Duchy of Holstein under Christian IV's Royal-Danish
        # administration (Holstein-Glückstadt portion). Per Wikipedia
        # EN «Altona, Hamburg»: «In 1640, Altona was part of Holstein-
        # Glückstadt.» Cross-check Wikipedia EN «House of Schauenburg»:
        # «After the death in 1640 of Count Otto V without children,
        # the House of Schaumburg became extinct. The County of Holstein-
        # Pinneberg was merged with the Duchy of Holstein.»
        # See `docs/research/mint_year_transitions.md` for full sources.
        "aliases": {"altona"},
        "display": "Altona",
        "entity": "royal_holstein",  # default = post-1640
        "year_overrides": [
            # Exclusive cutoff per 2026-05-26 user direction:
            # year < 1640 → Schauenburg-Pinneberg; year ≥ 1640 →
            # default Royal Holstein.
            {"year_to": 1640, "entity": "schauenburg_pinneberg"},
        ],
    },
    "glueckstadt": {
        # Christian IV founded the Glückstadt mint 1640. ASCII form
        # «gluckstadt» comes from Bruun PDF; «glikstadt» from some
        # legacy V1 seeds. WAS the bug source — ASCII form previously
        # missing from this alias set caused 18+ Bruun-Glückstadt
        # entries to misclassify as `danish_realm`.
        "aliases": {
            "glückstadt", "glueckstadt", "gluckstadt", "glikstadt",
            "gl?ckstadt",
        },
        "display": "Glückstadt",
        "entity": "royal_holstein",
    },
    "poppenbuettel": {
        "aliases": {"poppenbüttel", "poppenbuettel", "poppenbuttel"},
        "display": "Poppenbüttel",
        "entity": "royal_holstein",
    },
    "husum": {
        # Royal Schleswig portion (Danish king's direct rule).
        "aliases": {"husum"},
        "display": "Husum",
        "entity": "royal_holstein",
    },
    "haderslev": {
        # Hadersleben (German) — pre-1660 split crown; project follows
        # V1 author's tagging convention (royal_holstein default).
        "aliases": {"haderslev", "hadersleben"},
        "display": "Haderslev",
        "entity": "royal_holstein",
    },
    "flensburg": {
        # Flensborg (Danish) — Royal-Danish-Schleswig pre-1864.
        "aliases": {"flensburg", "flensborg"},
        "display": "Flensburg",
        "entity": "royal_holstein",
    },
    "rendsburg": {
        # Rendsborg (Danish).
        "aliases": {"rendsburg", "rendsborg"},
        "display": "Rendsburg",
        "entity": "royal_holstein",
    },
    "rethwisch": {
        # Rethwisch was a Holstein-Plön mint until the Plön line died out in
        # 1761, when castle + mint passed to the Danish crown by treaty; it then
        # ran as a BRANCH of the Copenhagen mint 1769-70 (Christian VII
        # Speciedaler). So the flat `royal_holstein` default reflects only the
        # POST-1761 crown coinage; the 1761 Plön issue (Friedrich Karl) seeds by
        # ITS issuer → norburg_plon_duchy and never relies on this mint entity.
        # (Corrected 2026-07-08 — was wrongly «royal Holstein after 1640».)
        # Source: de.wikipedia.org/wiki/Münze_zu_Rethwisch.
        "aliases": {"rethwisch"},
        "display": "Rethwisch",
        "entity": "royal_holstein",
    },

    # ───────────────────────── Gottorp duchy ───────────────────────────
    "schleswig": {
        # Schleswig city was primarily Gottorp through the period.
        "aliases": {"schleswig"},
        "display": "Schleswig",
        "entity": "gottorp_duchy",
    },
    "gottorp": {
        "aliases": {"gottorp"},
        "display": "Gottorp",
        "entity": "gottorp_duchy",
    },
    "toenning": {
        "aliases": {"tönning", "toenning", "tonning", "t?nning"},
        "display": "Tönning",
        "entity": "gottorp_duchy",
    },
    "kiel": {
        "aliases": {"kiel"},
        "display": "Kiel",
        "entity": "gottorp_duchy",
    },
    "steinbeck": {
        # Steinbeck (Steinbek nr. Reinbek) — Johann Adolf von Holstein-Gottorp's
        # ducal mint (Reichstaler 1606-07, MP/IG). Territory = Gottorp. Johann
        # Adolf was ALSO administrator of the Bishopric of Lübeck (1586-1607),
        # so his 1606 «Lübeck (Bishopric)» issue struck here seeds to
        # fuerstbisthum_luebeck by its ISSUER annotation — the mint entity is a
        # Gottorp-territory fallback, not the issuer of every Steinbeck coin.
        "aliases": {"steinbeck", "steinbek"},
        "display": "Steinbeck",
        "entity": "gottorp_duchy",
    },

    # ───────────────────────── Danish-Norway ───────────────────────────
    "christiania": {
        # Christiania pre-1924, Oslo post-1925. Project window ends 1914
        # so canonical = Christiania.
        "aliases": {"christiania", "kristiania", "oslo"},
        "display": "Christiania",
        "entity": "danish_norway",
    },
    "kongsberg": {
        # Norge silver mint. «Konsberg» = legacy spelling.
        "aliases": {"kongsberg", "konsberg"},
        "display": "Kongsberg",
        "entity": "danish_norway",
    },
    "bergen": {
        "aliases": {"bergen"},
        "display": "Bergen",
        "entity": "danish_norway",
    },
    "gimsoe": {
        # Gimsø / Gimsøy — the Christian III Norwegian mint (1545-46). Bruun
        # writes «Gimsøy Mint»; the trailing «-y» form was missing here.
        "aliases": {"gimsø", "gimsoe", "gimsøy", "gims?"},
        "display": "Gimsø",
        "entity": "danish_norway",
    },
    "nidaros": {
        # Trondheim (modern) — period name «Nidaros» preserved in
        # Bruun + Galster catalogues for medieval coinage.
        "aliases": {"nidaros", "trondheim"},
        "display": "Nidaros",
        "entity": "danish_norway",
    },

    # ────────── Grafschaft Schaumburg (Niedersachsen / Lower Saxon side) ──
    # The Schauenburg dynasty's ancestral Lower-Saxon county (Landkreis
    # Schaumburg) struck in the Niedersächsisch 36-Mariengroschen tradition;
    # its mints route to grafschaft_schaumburg. The Holstein side (Altona,
    # Pinneberg) routes to schauenburg_pinneberg. (Refactor 2026-06-10:
    # the holstein_schauenburg_county umbrella was split into these two.)
    "oldendorf": {
        "aliases": {"oldendorf"},
        "display": "Oldendorf",
        "entity": "grafschaft_schaumburg",
    },
    "rinteln": {
        "aliases": {"rinteln"},
        "display": "Rinteln",
        "entity": "grafschaft_schaumburg",
    },
    "stadthagen": {
        "aliases": {"stadthagen"},
        "display": "Stadthagen",
        "entity": "grafschaft_schaumburg",
    },
    "bueckeburg": {
        "aliases": {"bückeburg", "bueckeburg", "buckeburg", "b?ckeburg"},
        "display": "Bückeburg",
        "entity": "grafschaft_schaumburg",
    },

    # ───────────────────────── Hanseatic ───────────────────────────────
    "hamburg": {
        "aliases": {"hamburg"},
        "display": "Hamburg",
        "entity": "hanseatic_hamburg",
    },
    "lubeck": {
        "aliases": {"lübeck", "luebeck", "lubeck", "l?beck"},
        "display": "Lübeck",
        "entity": "hanseatic_lubeck",
    },

    # ───────────────────── Fürstbistum Lübeck ──────────────────────────
    "eutin": {
        "aliases": {"eutin"},
        "display": "Eutin",
        "entity": "fuerstbisthum_luebeck",
    },
    "kaltenhof": {
        "aliases": {"kaltenhof"},
        "display": "Kaltenhof",
        "entity": "fuerstbisthum_luebeck",
    },

    # ─────────────────── Erzbistum Bremen-Verden ───────────────────────
    "bremervoerde": {
        "aliases": {"bremervörde", "bremervoerde", "bremervorde", "bremerv?rde"},
        "display": "Bremervörde",
        "entity": "erzbisthum_bremen_verden",
    },
    "stade": {
        "aliases": {"stade"},
        "display": "Stade",
        "entity": "erzbisthum_bremen_verden",
    },

    # ─────────────── Landgrafschaft Hessen-Kassel ──────────────────────
    "kassel": {
        "aliases": {"kassel", "cassel"},
        "display": "Kassel",
        "entity": "landgrafschaft_hessen_kassel",
    },

    # ─────────────────────── Rantzau county ────────────────────────────
    "barmstedt": {
        "aliases": {"barmstedt"},
        "display": "Barmstedt",
        "entity": "rantzau_county",
    },
    "rantzau": {
        "aliases": {"rantzau"},
        "display": "Rantzau",
        "entity": "rantzau_county",
    },

    # ──────────────────── Sønderborg / Nørborg-Plön ────────────────────
    "sonderburg": {
        "aliases": {
            "sønderborg", "sonderburg", "soenderborg", "sønderburg",
            "s?nderborg", "s?nderburg",
        },
        "display": "Sønderborg",
        "entity": "sonderburg_duchy",
    },
    "reinfeld": {
        # Reinfeld — Johann d.J. von Schleswig-Holstein-Sonderburg's mint
        # (Taler 1622). Reinfeld Abbey lay in the Sonderburg possessions.
        "aliases": {"reinfeld"},
        "display": "Reinfeld",
        "entity": "sonderburg_duchy",
    },
    "ploen": {
        "aliases": {"plön", "ploen", "plon", "pl?n"},
        "display": "Plön",
        "entity": "norburg_plon_duchy",
    },

    # ─────────────────────── Grafschaft Oldenburg ──────────────────────
    "jever": {
        # Jever — Anton Günther von Oldenburg held the Lordship of Jever and
        # struck his Taler/Ducat coinage there (1614-1667).
        "aliases": {"jever"},
        "display": "Jever",
        "entity": "grafschaft_oldenburg",
    },

    # ─────────────────────── Hochstift Osnabrück ───────────────────────
    "osnabrueck": {
        # Osnabrück — the Prince-Bishopric's mint (Franz Wilhelm von
        # Wartenberg, Taler Klippe 1633).
        "aliases": {"osnabrück", "osnabrueck", "osnabruck", "osnabr?ck"},
        "display": "Osnabrück",
        "entity": "hochstift_osnabrueck",
    },

    # ──────────────── Out-of-scope (foreign mints) ─────────────────────
    "mannheim": {
        "aliases": {"mannheim"},
        "display": "Mannheim",
        "entity": None,
    },
}


# ────────────────────────── Derived lookup maps ────────────────────────
# Built once at module import time so consumers do a single dict.get()
# rather than walking the registry each call.

# alias (lower-case) → canonical key
ALIAS_TO_CANON: dict[str, str] = {}
for _canon, _spec in _MINT_REGISTRY.items():
    ALIAS_TO_CANON[_canon] = _canon  # canonical key matches itself
    for _alias in _spec["aliases"]:
        ALIAS_TO_CANON[_alias.lower()] = _canon
    # Display form (lower-case) also routes back to its canon — covers
    # the case where the canonical display string itself is fed in as
    # input (e.g. ucoin re-emits «Glückstadt» which already-canonical).
    ALIAS_TO_CANON[_spec["display"].lower()] = _canon

# canonical key → display string (project-canonical YAML form)
CANON_TO_DISPLAY: dict[str, str] = {
    canon: spec["display"] for canon, spec in _MINT_REGISTRY.items()
}

# canonical key → political entity tag (or None for out-of-scope)
CANON_TO_ENTITY: dict[str, str | None] = {
    canon: spec["entity"] for canon, spec in _MINT_REGISTRY.items()
}

# canonical key → list of year-overrides, each a dict
#   {"year_from": int | None, "year_to": int | None, "entity": str}.
# year_from inclusive, year_to EXCLUSIVE (locked 2026-05-26).
# Missing bound = open-ended on that side. Walk in order;
# first match wins. Mints without overrides have an empty list.
CANON_TO_YEAR_OVERRIDES: dict[str, list[dict]] = {
    canon: (spec.get("year_overrides") or [])
    for canon, spec in _MINT_REGISTRY.items()
}


# ─────────────────────── Crown-owned mints (render layer) ──────────────
# Single source of truth for build.py `_derive_issuing_entity` — the render-
# time realm widening of Danish-crown coinage. A mint is «crown-owned» when the
# Danish crown owned it and struck REALM coinage there: Kopenhagen (Denmark),
# Kongsberg (Norway), and the royal-Holstein mints (Altona / Glückstadt from
# 1617/1640; Husum / Haderslev / Flensburg / Rendsburg royal-Schleswig;
# Poppenbüttel by Altona; Rethwisch a Copenhagen branch 1769-70). This is a
# DIFFERENT concept from a mint's territory `entity` (used at SEED time to
# classify a coin BY its mint) — hence an explicit crown set rather than
# «every royal_holstein mint». build.py scopes the widening to
# `issuing_entity == danish_realm`, so commission strikes of OTHER issuers
# (Plön / Lübeck-bishopric / Lauenburg) struck at a crown mint are NOT widened
# — they keep their commissioning entity. Derived maps below key on the
# project-canonical DISPLAY form (mint fields are canonicalised to it).
_CROWN_OWNED: frozenset[str] = frozenset({
    "kopenhagen", "kongsberg",
    "altona", "glueckstadt", "poppenbuettel", "husum",
    "haderslev", "flensburg", "rendsburg", "rethwisch",
})

# display form → realm entity (for a crown coin struck there)
CROWN_MINT_REALM: dict[str, str] = {
    _MINT_REGISTRY[c]["display"]: _MINT_REGISTRY[c]["entity"] for c in _CROWN_OWNED
}
# the royal-Holstein subset — the gate: widening only fires when a crown coin
# is struck at one of these (a Holstein mint).
HOLSTEIN_CROWN_MINTS: frozenset[str] = frozenset(
    _MINT_REGISTRY[c]["display"] for c in _CROWN_OWNED
    if _MINT_REGISTRY[c]["entity"] == "royal_holstein"
)


def entity_for_canon_year(canon: str, year: int | None) -> str | None:
    """Resolve canonical mint key + optional year → entity tag.

    When `year is None` OR the mint has no year_overrides OR no override
    matches the given year, return the registry's default entity for
    that canon. Otherwise return the matching override's entity.

    Match rule per override:
      year_from inclusive, year_to EXCLUSIVE.
      year_from=None → -∞ (open lower bound).
      year_to=None   → +∞ (open upper bound).
    """
    if canon not in CANON_TO_ENTITY:
        return None
    default = CANON_TO_ENTITY[canon]
    if year is None:
        return default
    overrides = CANON_TO_YEAR_OVERRIDES.get(canon) or []
    for ov in overrides:
        yf = ov.get("year_from")
        yt = ov.get("year_to")
        if yf is not None and year < yf:
            continue
        if yt is not None and year >= yt:
            continue
        return ov["entity"]
    return default


def canon_for_alias(raw: str) -> str | None:
    """Look up the canonical key for an alias. Case-insensitive.
    Returns None when the alias is not registered."""
    if not isinstance(raw, str):
        return None
    return ALIAS_TO_CANON.get(raw.strip().lower())


def display_for_alias(raw: str) -> str | None:
    """Convenience: alias → canonical display form. None when unknown."""
    canon = canon_for_alias(raw)
    return CANON_TO_DISPLAY.get(canon) if canon else None


def entity_for_alias(raw: str) -> str | None:
    """Convenience: alias → political entity tag. None when unknown OR
    when the registered entity is None (out-of-scope mint)."""
    canon = canon_for_alias(raw)
    return CANON_TO_ENTITY.get(canon) if canon else None


# ───────────────────────── Issuer-text → entity registry ───────────────
#
# Parallel to the mint→entity map above. Used by parsers whose primary
# source labels coins by ISSUER STRING rather than mint (Numista does
# this — `issuer.name` / `issuer_text` / `country` field carries the
# emitting jurisdiction, mint is often not catalogued).
#
# Two real-world Numista cache shapes feed this table:
#   * API v3 (`fetch_numista_api.py`):   `issuer: {code, name}`
#   * chrome v1 (older HARVEST_ROUTINE): `issuer_text: <name>`
#   * chrome v2 (newer HARVEST_ROUTINE): `country: <name>`
# Same noun used three ways — registry is keyed by the lowercase string
# (whichever route surfaces it) plus any obvious variants Numista emits.
#
# Coverage (locked 2026-05-27 after full enumeration of 1717 cache files):
#   - All ~22 issuer strings present in cache map to one of 11 V2 entities
#   - One OOS issuer (`Mauritius`) maps to None (out-of-scope by project scope)
#   - One ambiguous issuer (`Schleswig and Holstein, Danish duchies of`)
#     spans 1514-1851 across multiple V2 entities (gottorp_duchy in early
#     period, royal_holstein in king-as-duke period, provisional_govt
#     for 1850-1851 rebels). Returns None here so mint-driven classifier
#     gets first crack via `classify_mint_to_entity`; only when mint is
#     also absent does the caller fall back to `_unclassified`.
#
# When Numista publishes a NEW issuer string the cache will surface a
# `None` from `classify_issuer_to_entity()`. The seed builder logs that
# as an unclassified entry; curator adds the new mapping here.
_ISSUER_REGISTRY: dict[str, str | None] = {
    # ───────────────────────── Denmark / Norway ────────────────────────
    "denmark": "danish_realm",
    "norway": "danish_norway",

    # API v3 code prefixes (issuer.code values verbatim, lower-case)
    "danemark": "danish_realm",
    "norvege": "danish_norway",

    # ────────────── Schleswig-Holstein duchies ────────────────────────
    "schleswig-holstein-gottorp, duchy of": "gottorp_duchy",
    "duchy of schleswig-holstein-gottorp (german states)": "gottorp_duchy",
    "schleswig_holstein_gottorp_duchy": "gottorp_duchy",  # API code

    "holstein-schaumburg-pinneberg, county of": "schauenburg_pinneberg",
    "county of holstein-schaumburg-pinneberg (german states)": "schauenburg_pinneberg",
    "holstein_schauenburg_county": "schauenburg_pinneberg",  # API code

    "schleswig-holstein-norburg-plön, duchy of": "norburg_plon_duchy",
    "schleswig-holstein-norburg-plon, duchy of": "norburg_plon_duchy",
    "schleswig_holstein_norbourg_plon_duchy": "norburg_plon_duchy",  # API code

    "schleswig-holstein-sonderburg, duchy of": "sonderburg_duchy",
    "schleswig_holstein_sonderburg_duchy": "sonderburg_duchy",  # API code

    # ──────────── Royal Holstein / Glückstadt mint ──────────────────────
    "glückstadt, city of": "royal_holstein",
    "gluckstadt, city of": "royal_holstein",
    "city of glückstadt (denmark)": "royal_holstein",
    "city of gluckstadt (denmark)": "royal_holstein",
    "gluckstadt_city": "royal_holstein",  # API code

    # ───────────────── Fürstbistum Lübeck ───────────────────────────────
    "bishopric of lübeck (german states)": "fuerstbisthum_luebeck",
    "bishopric of lubeck (german states)": "fuerstbisthum_luebeck",

    # ──────────────── Brunswick-Lüneburg cluster ────────────────────────
    "duchy of brunswick (german states)": "herzogtum_braunschweig_lueneburg",
    "duchy of brunswick": "herzogtum_braunschweig_lueneburg",
    "brunswick-lüneburg-celle (german states)": "herzogtum_braunschweig_lueneburg",
    "brunswick-lüneburg-celle": "herzogtum_braunschweig_lueneburg",
    "brunswick-luneburg-celle (german states)": "herzogtum_braunschweig_lueneburg",
    "brunswick-luneburg-celle": "herzogtum_braunschweig_lueneburg",
    "principality of brunswick-grubenhagen (german states)": "herzogtum_braunschweig_lueneburg",
    "principality of brunswick-calenberg (german states)": "herzogtum_braunschweig_lueneburg",

    # ──────────────────────── Oldenburg ─────────────────────────────────
    "county of oldenburg (german states)": "grafschaft_oldenburg",
    "county of oldenburg": "grafschaft_oldenburg",
    "grand duchy of oldenburg (german states)": "grafschaft_oldenburg",

    # ───────────────────── Osnabrück / Bremen-Verden ───────────────────
    "bishopric of osnabrück (german states)": "hochstift_osnabrueck",
    "bishopric of osnabruck (german states)": "hochstift_osnabrueck",
    "archbishopric of bremen (german states)": "erzbisthum_bremen_verden",
    "duchy under swedish possession of bremen-verden (german states)": "erzbisthum_bremen_verden",
    "bremen-verden (swedish)": "erzbisthum_bremen_verden",

    # ──────────────────── Saxe-Lauenburg ────────────────────────────────
    "duchy of saxe-lauenburg (german states)": "herzogtum_sachsen_lauenburg",

    # ──────────── Danish-ruled Schleswig-Holstein duchies ──────────────
    # Numista's «Schleswig and Holstein, Danish duchies of» (+ German-
    # states-suffix + API-code variants) is the coinage struck by the
    # Danish KING in his capacity as Duke of (his portion of) Schleswig-
    # Holstein — the royal Holstein portion. This is DISTINCT from:
    #   * «Schleswig-Holstein-Gottorp, Duchy of» → gottorp_duchy (the
    #     independent Gottorp dukes' own sovereign coinage, 1544-1773)
    #   * «Holstein-Schaumburg-Pinneberg, County of» → schauenburg
    #     (the Schauenburg comital dynasty)
    # Numista distinguishes all three issuer strings, so this one is
    # unambiguously the royal/Danish line.
    #
    # Maps flat to royal_holstein — NOT year-varying. Control-based
    # classification per the project entity scheme (issuing_entities.yml):
    # Schleswig-Holstein territory under Danish control = royal_holstein,
    # across the whole period. The three historical eras all collapse to
    # royal_holstein in this scheme:
    #   * pre-1544 (joint, senior-duke = royal line): royal_holstein
    #   * 1544-1773 (King's portion alongside sovereign Gottorp): royal_holstein
    #   * post-1773 (Gottorp ceded to DK → unified SH duchy, Altona-struck):
    #     royal_holstein (the deprecated `gesamtstaat` term retired; coins
    #     classify by territorial control, and unified SH = royal Holstein)
    #
    # Twin-evidence (2026-05-27, §CB): every «Danish duchies» coin with a
    # findable same-type V2 twin lands in royal_holstein —
    #   km-82-chr-iv-1640 (2 Schilling Reuterpfennig 1640),
    #   hede-c7h45 (2 Sechsling 1787), hede-c5h121+sieg-137 (4 Marck /
    #   1 Krone 1671), numismaster mb-48 (1 Thaler Christian III 1545),
    #   numismaster mb-62 (1 Pfennig Schüsselpfennig Friedrich II 1559).
    "schleswig and holstein, danish duchies of": "royal_holstein",
    "danish duchies of schleswig and holstein (german states)": "royal_holstein",
    "schleswig_holstein_danish_duchies": "royal_holstein",  # API code

    # ────────────────────── Out-of-scope ────────────────────────────────
    # Project scope is German lands + Danish-Norwegian realm 1514-1914.
    # Mauritius / other tropical / colonial issues are explicitly OOS.
    "mauritius": None,
    "maurice": None,  # API code
}


def classify_issuer_to_entity(issuer: str | None) -> str | None:
    """Map a Numista `issuer` / `issuer_text` / `country` string to a V2
    political entity tag.

    Returns:
      * scalar entity tag when the issuer is registered and not OOS
      * None when:
          - issuer is None / empty
          - issuer is registered as None (ambiguous OR OOS — caller
            distinguishes via `issuer in _ISSUER_REGISTRY`)
          - issuer is unknown (not in registry)

    Case-insensitive. Strips surrounding whitespace.

    The newer chrome_mcp_html shape uses `country` instead of `issuer_text`
    but the strings themselves are identical (e.g. `Norway`, `Denmark`,
    `Duchy of Brunswick (German States)`) — callers can pass either route.
    """
    if not issuer or not isinstance(issuer, str):
        return None
    return _ISSUER_REGISTRY.get(issuer.strip().lower())


def is_known_issuer(issuer: str | None) -> bool:
    """True if the issuer string is in our registry (regardless of whether
    it maps to a real entity or to None/OOS). Distinguishes «known
    ambiguous / OOS» from «unrecognised — needs curator review»."""
    if not issuer or not isinstance(issuer, str):
        return False
    return issuer.strip().lower() in _ISSUER_REGISTRY


# ───────────────────── KMM `nation` → entity classifier ────────────────
#
# The Royal Coin Cabinet Copenhagen (KMM, harvested via api.natmus.dk —
# see docs/KMK_HARVEST.md) labels every coin with a DANISH-LANGUAGE
# `nation` realm string, and only ~27 % carry a `place` (mint). For the
# ~73 % without a mint, `nation` is the fallback entity signal. KMM's
# nation strings are dirty (case / whitespace / a «Tysk, » prefix /
# «?» uncertainty marks / spelling variants): «Danmark» / « Danmark» /
# «danmark» / «Danmark?» / «Tysk, Hamburg» / «Slesvig-Holsten» /
# «Holsten-Gottorp». So we normalise then match ORDERED substring rules
# (specific entities before the Danmark/Norge realm fallback).
#
# This is the nation-string analogue of `classify_issuer_to_entity`
# (which handles Numista's English jurisdiction strings). Builders that
# use it MUST record the lower-confidence provenance — the
# `entity_classified_via` field on Coin — because nation routing is
# coarser than mint routing (e.g. bare «Slesvig-Holsten» could be royal
# OR Gottorp; we default to royal_holstein per the issuer-registry
# convention «Danish duchies of Schleswig and Holstein → royal_holstein»,
# and a mint reading, when present, overrides it).
import re as _re  # noqa: E402

_NATION_RULES: list[tuple] = [
    # ── Schleswig-Holstein sub-duchies (specific BEFORE the bare
    #    Slesvig/Holsten → royal_holstein catch) ──
    (_re.compile(r"gottorp"), "gottorp_duchy"),
    (_re.compile(r"s[øo]nderb[ou]rg"), "sonderburg_duchy"),
    (_re.compile(r"gl[üu]cksb[ou]rg"), "glucksburg_duchy"),
    (_re.compile(r"\bpl[öo]n\b|ploen"), "norburg_plon_duchy"),
    (_re.compile(r"rantzau"), "rantzau_county"),
    # ── Schleswig / Holstein under the Danish crown (king-as-duke
    #    default; flat to royal_holstein per the issuer-registry
    #    convention). Gottorp/Sønderborg/Plön/Glücksborg already won above. ──
    (_re.compile(r"slesvig|holsten|holstein"), "royal_holstein"),
    # ── Hanseatic + German territories ──
    (_re.compile(r"hamburg"), "hanseatic_hamburg"),
    (_re.compile(r"l[üu]neburg|lueneburg|brunswick|braunschweig"),
     "herzogtum_braunschweig_lueneburg"),
    (_re.compile(r"l[üu]beck|luebeck"), "hanseatic_lubeck"),
    (_re.compile(r"bremen|verden"), "erzbisthum_bremen_verden"),
    (_re.compile(r"oldenburg"), "grafschaft_oldenburg"),
    (_re.compile(r"lauenburg"), "herzogtum_sachsen_lauenburg"),
    (_re.compile(r"osnabr[üu]ck|osnabruck"), "hochstift_osnabrueck"),
    (_re.compile(r"hessen|hesse|kassel|cassel"),
     "landgrafschaft_hessen_kassel"),
    # Schauenburg issuer-name fallback → Holstein-Pinneberg by default;
    # the schauenburg_niedersaechsisch_denoms routing rule re-routes the
    # Niedersächsisch (Mariengroschen / Oldendorf-mint) pieces to
    # grafschaft_schaumburg (the holstein_schauenburg_county umbrella was
    # split into these two, 2026-06-10).
    (_re.compile(r"scha[ou]?[ue]nburg|schaumburg"),
     "schauenburg_pinneberg"),
    # ── Danish-Norwegian realm fallback. Danmark BEFORE Norge so
    #    «Danmark-Norge» / «Danmark; Norge» (dual monarchy) anchor to the
    #    realm, while bare «Norge» routes to danish_norway. ──
    (_re.compile(r"danmark"), "danish_realm"),
    (_re.compile(r"\bnorge\b|\bnorway\b"), "danish_norway"),
]


def _normalise_nation(nation: str) -> str:
    """Lower-case, strip, drop a leading «Tysk, » / «Tysk » prefix, and
    strip trailing «?» / «(?)» uncertainty marks. Returns «» on junk."""
    s = nation.strip().lower()
    s = _re.sub(r"^tysk[,\s]+", "", s)        # «Tysk, Hamburg» → «hamburg»
    s = _re.sub(r"\(\?\)|\?+\s*$", "", s).strip()  # «danmark?» → «danmark»
    return s


def classify_nation_to_entity(nation: str | None,
                              year: int | None = None) -> str | None:
    """Map a KMM `nation` realm string → V2 political entity tag, or None.

    Ordered substring match against `_NATION_RULES` after normalising the
    dirty nation string. `year` is accepted for signature parity with
    `classify_mint_to_entity` but is currently unused (no nation-level
    year overrides modelled yet). Returns None for unknown / OOS / generic
    («Tyskland», «Tysk», ancient/world realms) → caller routes to
    `_unclassified`.

    COARSER than mint classification — callers should prefer
    `classify_mint_to_entity(place)` first and only fall back to this when
    no mint is present, recording `entity_classified_via="nation"`.
    """
    if not nation or not isinstance(nation, str):
        return None
    norm = _normalise_nation(nation)
    if not norm:
        return None
    for rx, entity in _NATION_RULES:
        if rx.search(norm):
            return entity
    return None


def is_known_nation(nation: str | None) -> bool:
    """True if the nation string resolves to an in-scope entity."""
    return classify_nation_to_entity(nation) is not None
