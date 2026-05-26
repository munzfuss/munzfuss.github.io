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
        # aka Hafnia (Latin — Christian IV legends).
        "aliases": {
            "kopenhagen", "copenhagen", "københavn", "kobenhavn",
            "kjøbenhavn", "kjobenhavn", "k?benhavn", "hafnia",
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
        "display": "Malmö",
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

    # ────────────────────────── Royal Holstein ─────────────────────────
    "altona": {
        # Pre-1640 = Schauenburg-Pinneberg; post-1640 = Royal Holstein.
        # Project late default = Royal Holstein. NumisMaster handles
        # Schauenburg-era Altona via issuer-tag instead of mint-tag.
        "aliases": {"altona"},
        "display": "Altona",
        "entity": "royal_holstein",
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
        # Rethwisch lay in royal Holstein after 1640.
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
        "aliases": {"gimsø", "gimsoe", "gims?"},
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

    # ────────────── Holstein-Schauenburg county ────────────────────────
    "oldendorf": {
        "aliases": {"oldendorf"},
        "display": "Oldendorf",
        "entity": "holstein_schauenburg_county",
    },
    "rinteln": {
        "aliases": {"rinteln"},
        "display": "Rinteln",
        "entity": "holstein_schauenburg_county",
    },
    "stadthagen": {
        "aliases": {"stadthagen"},
        "display": "Stadthagen",
        "entity": "holstein_schauenburg_county",
    },
    "bueckeburg": {
        "aliases": {"bückeburg", "bueckeburg", "buckeburg", "b?ckeburg"},
        "display": "Bückeburg",
        "entity": "holstein_schauenburg_county",
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
    "ploen": {
        "aliases": {"plön", "ploen", "plon", "pl?n"},
        "display": "Plön",
        "entity": "norburg_plon_duchy",
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
