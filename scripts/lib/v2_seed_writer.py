"""V2-native seed writer — shared helper for seed builders.

Replaces the V1→V2 indirection that runs every V1 builder through
`seed_v2_regroup.py` to translate location-keyed output into entity-
keyed V2 seed yamls. Each builder calls `write_v2_seed(coins, source)`
directly and the result lands in `data/v2/seed/<source>/<entity>.yml`
ready for the cross-source merger.

Per V2_PIPELINE.md §3.10: when a coin has list-form `issuing_entity`
(joint mint, e.g. `[danish_realm, royal_holstein]` for Altona+Kopenhagen),
the HOME FILE is the alphabetically-first entity. Build assembly's
inverse-index pass surfaces the coin on every consumer page whose
`consumes_entities` intersects with the list.

Per CLAUDE.md «V2 entity-keyed pipeline»: V1 is FROZEN; new builders
write V2 directly. The previous `data/seed/<source>/<location>.yml`
output path is no longer touched by these builders.

Curation preservation: each per-entity write goes through
`lib.seed_merge.merge_seed`, so existing curator-set `fuss`/`phase`/
`issuing_entity`/`note`/`*_verified` flags survive regeneration.
Orphan curated entries (in V2 seed but no longer in the fresh build)
stay verbatim — no silent data loss.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import PROJECT_ROOT  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

V2_SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed"

# ----------------------------------------------------------------------
# Pre-write hygiene: out-of-scope filter + normalisation
# ----------------------------------------------------------------------
import re  # noqa: E402

# Nominal substrings that mark a coin as OUT-OF-SCOPE for the project.
# Per CLAUDE.md «Mission temporal scope» the artifact documents NORTH
# GERMAN + DANISH-NORWEGIAN coinage. Trade coins minted FOR (not BY)
# the Danish Crown — East India Asiatic Piastre etc. — fall outside
# this register even when minted at Kopenhagen. User-confirmed
# 2026-05-20.
_OUT_OF_SCOPE_NOMINAL_TOKENS = (
    "piast",         # Piaster (German singular) + Piastre (English plural)
                     # — Christian VII East India trade
    "rupee",         # East India Tranquebar
    "fanam",         # East India sub-denomination
    "cash",          # East India sub-denomination
)

# Denomination nouns that often appear in source data without a
# leading number (Hede pages: «Penning», «Hvid», «Skilling», bare
# spec-headers). Per CLAUDE.md «mathematically-verified register»:
# every coin row needs an explicit denomination count, default «1»
# when source publishes just the noun. Listed denominations get
# «1 » prefixed when the nominal lacks a leading digit/fraction.
_BARE_DENOMINATION_NOUNS = frozenset({
    # Danish core
    "ducat", "dukat", "thaler", "speciedaler", "specie daler",
    "krone", "skilling", "mark", "søsling", "hvid", "penning",
    "denning", "dobbelthvid", "firehvid", "treskilling",
    "joachimstaler",
    # German + Hanseatic
    "pfennig", "schilling", "sechsling", "dreiling", "groschen",
    "goldgulden", "gulden", "portugaløser", "rosenobel", "nobel",
    "reichsthaler", "kronenthaler", "rhinsk gylden", "sølvgylden",
    # Rigsdaler-era
    "rigsdaler", "rigsbankdaler", "rigsbankskilling",
    # Gold sub-denominations
    "pistole", "friedrichsdor", "rosenoble",
})

# Canonical mint name table — normalises the dozens of orthographic
# variants encountered across sources (English / Danish / Latin
# spellings, country-prefixed ucoin format, modern vs historical
# spellings) to ONE canonical form per physical mint town.
# Project convention per CLAUDE.md i18n policy: German period spelling
# for project canonical (Kopenhagen, Christiania, Glückstadt, Altona).
_MINT_CANONICAL = {
    # Copenhagen variants → Kopenhagen
    "copenhagen": "Kopenhagen",
    "københavn": "Kopenhagen",
    "kjøbenhavn": "Kopenhagen",      # pre-1948 Danish spelling
    "k�benhavn": "Kopenhagen",        # mojibake from iso-8859 source
    "hafnia": "Kopenhagen",           # Latin (Christian IV legends)
    "kopenhagen": "Kopenhagen",
    # Christiania / Oslo (Norge)
    "christiania": "Christiania",
    "oslo": "Christiania",            # pre-1924 Christiania (post 1925 Oslo)
                                       # — project window ends 1914 → Christiania
    # Glückstadt variants
    "glückstadt": "Glückstadt",
    "gluckstadt": "Glückstadt",       # ASCII fallback
    "gl�ckstadt": "Glückstadt",       # mojibake
    # Rendsburg (German canonical for SH)
    "rendsburg": "Rendsburg",
    "rendsborg": "Rendsburg",         # Danish spelling
    # Helsingør
    "helsingør": "Helsingør",
    "helsingor": "Helsingør",
    "helsing�r": "Helsingør",         # mojibake
    "elsinore": "Helsingør",          # English
    "elseneur": "Helsingør",          # French (old auction catalogues)
    # Aarhus / Århus
    "århus": "Århus",
    "aarhus": "Århus",
    # Malmö / Malmø (Scania historical; Swedish for project)
    "malmö": "Malmö",
    "malmø": "Malmö",                 # Danish for the same town
    "malm�": "Malmö",                 # mojibake
    "malmoe": "Malmö",
    # Kongsberg (Norge silver mint)
    "kongsberg": "Kongsberg",
    "konsberg": "Kongsberg",
}

# Country / region prefix tokens that ucoin sometimes prepends
# («Denmark, Copenhagen»). Strip these before canonicalising.
_MINT_COUNTRY_PREFIXES = frozenset({
    "denmark", "norway", "sweden", "germany", "holstein", "schleswig",
    "schleswig-holstein", "lübeck", "hamburg",
})


def _canonicalise_mint(raw):
    """Map an arbitrary mint string (or list) to canonical project
    spelling. Strips country-prefixes, paren tails, applies alias
    map, restores diacritics. Returns scalar (single mint) or sorted
    de-duped list (joint mint). None when input is None / empty."""
    if raw is None:
        return None
    items = raw if isinstance(raw, list) else [raw]
    out_set: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        # Strip paren tail «Altona (FK VS)» → «Altona»
        base = re.sub(r"\s*\([^)]*\)\s*$", "", item).strip()
        if not base:
            continue
        # Split on comma — drop country prefix tokens, canonicalise the
        # rest. «Denmark, Copenhagen» → Kopenhagen.
        for tok in [t.strip() for t in base.split(",") if t.strip()]:
            key = tok.lower()
            if key in _MINT_COUNTRY_PREFIXES:
                continue
            canonical = _MINT_CANONICAL.get(key, tok)
            if canonical not in out_set:
                out_set.append(canonical)
    if not out_set:
        return None
    return out_set[0] if len(out_set) == 1 else sorted(out_set)


# Nominal normalisation table — fixes mojibake + standardises fraction
# typography («1/2» → «½», «1 1/2» → «1½») without altering the
# semantic content. Per CLAUDE.md §i18n the period denomination form
# stays — we only fix encoding artefacts and typographic consistency.
_NOMINAL_MOJIBAKE_FIXES = (
    ("K�benhavn", "København"),
    ("Malm�", "Malmø"),
    ("Gl�ckstadt", "Glückstadt"),
    ("Helsing�r", "Helsingør"),
    ("Sølv�", "Sølv"),
    ("�", ""),  # last-resort drop remaining replacement-char artefacts
)


def _normalise_nominal(raw):
    """Normalise a nominal string: mojibake fix + fraction typography +
    consistent capitalization of the denomination noun. Preserves the
    period-correct numismatic form (no translation), only typographic
    cleanup. Returns None when input is None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # Mojibake repair first — must happen before any case folding so
    # the diacritic-bearing char survives.
    for bad, good in _NOMINAL_MOJIBAKE_FIXES:
        if bad in s:
            s = s.replace(bad, good)
    # Strip trailing year-status markers — «uden år» metadata that
    # accidentally entered the nominal field via parser greed. The
    # year-status belongs in `year_label` (rendered as «u. å.»);
    # nominal should hold ONLY the denomination noun. Patterns
    # observed (Hede pages, mostly Christian IV / Frederik III
    # undated gold strikes):
    #   «1 Portugaløser U.år»     → «1 Portugaløser»
    #   «1/2 Dukat U.år (ca 1648)» → «1/2 Dukat»
    #   «1 Søsling u.år»          → «1 Søsling»
    #   «..., u. år (-32)?»       → «...»  (strip from comma onward)
    # Anchored at end so we don't accidentally strip a denomination
    # named «UR» or similar (none exist in Danish numismatics).
    s = re.sub(
        r"[,\s]+[Uu]\.?\s*[åÅaA]?\.?\s*[Rr]?\.?(?:\s*\((?:[^)]*\)|[^)]*$))?\s*\??$",
        "",
        s,
        flags=re.IGNORECASE,
    ).strip(" ,")
    # Strip trailing year-range fragments like «, -24» / «, 1523-24» —
    # parser artefacts where a sub-year range from the page header bleeds
    # into the captured denomination string. Patterns observed (Galster
    # pre-1541 pages):
    #   «Skilling (10 hvide), -24»  → «Skilling (10 hvide)»
    #   «X, 1523-24» / «X, -1525»   → «X»
    # The trailing fragment is recognised as: comma + optional whitespace
    # + (optional 4-digit-year + dash) + 2-digit-year-tail OR bare dash-
    # prefixed 2/4-digit tail.
    s = re.sub(
        r"\s*,\s*-?\d{2,4}(?:[-–]\d{2,4})?\s*$",
        "",
        s,
    ).strip(" ,")
    # Collapse extra whitespace before comma: «X , Y» → «X, Y»
    s = re.sub(r"\s+,", ",", s)
    # Collapse multiple spaces (e.g. «X,  Y» → «X, Y»)
    s = re.sub(r"\s{2,}", " ", s)
    # Expand parenthesised abbreviation-completion: «Fr(ederiks) D'or»
    # → «Frederiks D'or», «Chr(istians) D'or» → «Christians D'or».
    # The Danish numismatic convention prints the genitive suffix in
    # parens immediately after the abbreviation root («Fr» / «Chr»),
    # with NO space between root and opening paren. The legitimate
    # paren-clarifier case («1 Skilling (Firehvid)», «Ny mønt (1844)»)
    # has a space before «(» AND starts with uppercase / digit inside
    # the parens — distinguishable from the abbreviation form.
    s = re.sub(
        r"\b([A-Z][a-z]*)\(([a-zæøåü]+)\)",
        r"\1\2",
        s,
    )
    # Add leading «1 » when nominal is a bare denomination noun.
    # «Penning» → «1 Penning», «Hvid» → «1 Hvid», «Skilling» → «1 Skilling».
    # Also fires when the nominal has the shape «<noun>, <mint>» or
    # «<noun>, <mint> (?)» — the leading count is implicit. Catches
    # Galster pre-1541 pages where page-title denomination omits «1 »:
    #   «Søsling, Ronneby (?)»  → «1 Søsling, Ronneby (?)»
    #   «Halv Sølvgylden»       → kept as-is (Halv = «½», not bare-noun)
    if s:
        # Split on first comma to get the leading-denomination token;
        # also strip a trailing paren clarifier («Skilling (10 Hvide)»
        # → head = «Skilling») so bare-noun detection still fires.
        head = s.split(",", 1)[0].strip()
        head_noparens = re.sub(r"\s*\([^)]*\)\s*$", "", head).strip()
        if head_noparens.lower() in _BARE_DENOMINATION_NOUNS:
            s = f"1 {s}"
    # Fraction typography: «1 1/2» / «1-1/2» → «1½»; «1/2» → «½»; etc.
    s = re.sub(r"(\d)\s*[\-\s]\s*1/2\b", r"\1½", s)
    s = re.sub(r"(\d)\s*[\-\s]\s*1/4\b", r"\1¼", s)
    s = re.sub(r"(\d)\s*[\-\s]\s*3/4\b", r"\1¾", s)
    s = re.sub(r"\b1/2\b", "½", s)
    s = re.sub(r"\b1/4\b", "¼", s)
    s = re.sub(r"\b3/4\b", "¾", s)
    s = re.sub(r"\b1/3\b", "⅓", s)
    s = re.sub(r"\b2/3\b", "⅔", s)
    s = re.sub(r"\b1/8\b", "⅛", s)
    s = re.sub(r"\b1/16\b", "1/16", s)  # leave higher fractions as-is
    # Capitalize denomination noun after a number. «1 skilling» →
    # «1 Skilling»; «4 mark» → «4 Mark»; «1 dukat» → «1 Dukat».
    # Only first noun, not deep capitalisation.
    s = re.sub(
        r"(\b(?:\d+|½|¼|¾|⅓|⅔|⅛)\s+)([a-zæøåüß])",
        lambda m: m.group(1) + m.group(2).upper(),
        s,
    )
    return s


# Known catalog prefix → schema-field map. Used by `_normalise_catalog`
# to split jammed field values like «hede: "24 Sieg 26.1"» into the
# correct per-prefix fields. Prefixes without a dedicated field fall
# back to `catalog.others` as «Prefix# Value».
_CATALOG_PREFIX_TO_FIELD: dict[str, str] = {
    "Hede": "hede",
    "Sieg": "sieg",
    "Schou": "schou",
    "Lange": "lange",
    "Fr": "fr",
    "Dav": "dav",
    "Galster": "galster",
    "Friedberg": "friedberg",
    "Davenport": "davenport",
    "MB": "mb",
    "Skaare": "skaare",
    "Schive": "schive",
    "Jensen-Skjoldager": "jensen_skjoldager",
}

# Recognise these as «next-catalog-ref» when scanning a jammed value.
# Order matters: longer prefixes first (so «KM-DK» beats «KM», «Dav EC»
# beats «Dav», etc.).
_KNOWN_CATALOG_PREFIXES = tuple(sorted({
    "KM-DK", "KM-SH", "KM-NO", "KM",
    "Hede", "Sieg", "Schou", "Lange", "Fr", "Dav",
    "Bruun", "Galster", "Friedberg", "Davenport", "MB",
    "AKS", "Behr", "Brockmann", "Bahrf", "Bobzin", "Hofmann",
    "Jaeg", "Aagaard", "Saur", "Diakov", "Uzd", "Bit",
    "Brekke", "Hauberg", "Fb", "J", "N", "C", "Weinm",
    "Schön", "Skaare", "Schive", "Jensen-Skjoldager",
    "NWD",
}, key=len, reverse=True))

# Regex to detect a jammed «<value> <NextPrefix> <next_value>» pattern
# inside a scalar catalog-ref field. The next_value can have decimals
# («26.1»), letter suffixes («14a»), slashes («5/6»), or hyphens.
_JAMMED_CATALOG_RE = re.compile(
    r"^(?P<own>\S+(?:\s*[A-Za-z]+\s*)?)\s+"
    r"(?P<next_prefix>" + "|".join(re.escape(p) for p in _KNOWN_CATALOG_PREFIXES) + r")"
    r"\s+(?P<next_value>[\d./\-]+[A-Za-z]?(?:\s*[,/]\s*[\d./\-]+[A-Za-z]?)*)\s*$"
)


def _normalise_catalog(catalog: dict | None) -> tuple[dict | None, int]:
    """Detect and split jammed catalog-ref values.

    V1-foundation entries sometimes packed multiple catalog refs into
    a single field (e.g. `hede: "24 Sieg 26.1"` should be
    `hede: "24"` + `sieg: "26.1"`). This function walks each named
    catalog field, detects the «<own_value> <NextPrefix> <next_value>»
    pattern, peels off the trailing ref, and routes it to the
    appropriate destination (dedicated field if known, else
    `catalog.others`).

    Returns `(normalised_catalog, changes_count)`. When `catalog` is
    None or has no jammed fields, returns the input unchanged with
    count = 0.
    """
    if not isinstance(catalog, dict):
        return catalog, 0
    changes = 0

    def _split_one(val: str, field: str) -> str | None:
        """Process a single scalar value. Returns the cleaned own value,
        OR None when no split fired. Side-effects: route the peeled ref
        to its destination field / others."""
        nonlocal changes
        m = _JAMMED_CATALOG_RE.match(val.strip())
        if not m:
            return None
        own = m.group("own").strip()
        next_prefix = m.group("next_prefix")
        next_value = m.group("next_value").strip()
        dest_field = _CATALOG_PREFIX_TO_FIELD.get(next_prefix)
        if dest_field and dest_field != field:
            existing = catalog.get(dest_field)
            if existing is None or existing == "":
                catalog[dest_field] = next_value
            elif isinstance(existing, str) and existing == next_value:
                pass
            elif isinstance(existing, list) and next_value in existing:
                pass
            else:
                others = catalog.setdefault("others", [])
                if isinstance(others, list):
                    token = f"{next_prefix}# {next_value}"
                    if token not in others:
                        others.append(token)
        else:
            others = catalog.setdefault("others", [])
            if isinstance(others, list):
                token = f"{next_prefix}# {next_value}"
                if token not in others:
                    others.append(token)
        changes += 1
        return own

    # Iterate over CURRENT field list — appending to `others` doesn't
    # need to be re-scanned (its format is already «Prefix# Value»).
    for field in list(_CATALOG_PREFIX_TO_FIELD.values()):
        val = catalog.get(field)
        if isinstance(val, str):
            cleaned = _split_one(val, field)
            if cleaned is not None:
                catalog[field] = cleaned
        elif isinstance(val, list):
            # List-form (data-accumulation per CLAUDE.md): scan each
            # entry; replace jammed ones with the cleaned own value.
            # Dedupe — if cleaning produces duplicates, drop.
            new_list: list = []
            for item in val:
                if isinstance(item, str):
                    cleaned = _split_one(item, field)
                    new_item = cleaned if cleaned is not None else item
                    if new_item not in new_list:
                        new_list.append(new_item)
                else:
                    new_list.append(item)
            if new_list != list(val):
                # Replace; preserve scalar shape if list collapsed to one
                catalog[field] = new_list[0] if len(new_list) == 1 else new_list
    return catalog, changes


# Danish numismatic mints that occasionally bleed into the nominal
# field from source page-title concatenation. Used by
# `_extract_mint_from_nominal` to detect both trailing form («4
# Skilling, København») and leading form («Oslo, Skilling») and route
# the mint to its dedicated field. Includes mojibake variants from
# iso-8859 → utf-8 conversion artefacts in the danskmoent.dk cache.
_NOMINAL_MINT_PATTERN = (
    r"Ålborg|Aalborg|Malmø|Malmoe|Malmö|Malm[?�]|"
    r"Ronneby|Hamar|Bergen|Oslo|Christiania|"
    r"København|Kjøbenhavn|K[?�]benhavn|Kj[?�]benhavn|Copenhagen|"
    r"Roskilde|Aarhus|Århus|[?�]rhus|Ribe|Lund|Visby|"
    r"Husum|Gottorp|Glückstadt|Gluckstadt|Gl[?�]ckstadt|"
    r"Trondheim|Nidaros|Stockholm|Vasteras|"
    r"Lübeck|L[?�]beck|Hamburg|Schwerin|Rendsburg|"
    r"Helsingør|Helsingor|Helsing[?�]r"
)
_NOMINAL_MINT_TRAILING_RE = re.compile(
    r",\s*(" + _NOMINAL_MINT_PATTERN + r")(\s*\(\?\))?\s*$",
    re.IGNORECASE,
)
_NOMINAL_MINT_LEADING_RE = re.compile(
    r"^(" + _NOMINAL_MINT_PATTERN + r")\s*,\s*",
    re.IGNORECASE,
)
_NOMINAL_SHAPE_RE = re.compile(
    r"[,\s]+\(?(klipping|klippe|firkant)\)?\s*$",
    re.IGNORECASE,
)


def _extract_mint_from_nominal(nominal, source_mint
                                ) -> tuple[str | None, str | None]:
    """Split «<denom>, <mint>» / «<mint>, <denom>» — return (clean_nominal,
    mint). Mint extracted from nominal takes precedence over source_mint
    (the in-nominal mint is the page-title-attested authority). Also
    strips coin-shape descriptors («klipping»). When no mint found in
    nominal, returns (nominal, source_mint) unchanged."""
    if not nominal:
        return (nominal, source_mint)
    s = str(nominal).strip()
    # Collapse double-comma artefacts (e.g. «1 Hvid, , Ålborg»)
    s = re.sub(r",\s*,\s*", ", ", s)
    extracted_mint = None
    # Trailing form
    m = _NOMINAL_MINT_TRAILING_RE.search(s)
    if m:
        extracted_mint = m.group(1)
        s = _NOMINAL_MINT_TRAILING_RE.sub("", s).rstrip(" ,")
    # Leading form (only when trailing didn't fire)
    if not extracted_mint:
        m_lead = _NOMINAL_MINT_LEADING_RE.match(s)
        if m_lead:
            extracted_mint = m_lead.group(1)
            s = _NOMINAL_MINT_LEADING_RE.sub("", s).strip()
    # Coin-shape descriptor stripping
    s = _NOMINAL_SHAPE_RE.sub("", s).rstrip(" ,")
    mint_value = extracted_mint or source_mint
    return (s or None, mint_value)


def _is_out_of_scope_nominal(nominal) -> bool:
    """Return True when the nominal indicates an out-of-scope trade coin
    (East India Piastre / Rupee / Fanam / Cash). User-confirmed
    2026-05-20: these coins were minted BY the Danish Crown FOR Asian
    markets, not for the European-realm coinage system the artifact
    documents — exclude from every seed regardless of mint."""
    if not nominal:
        return False
    n = str(nominal).lower()
    return any(tok in n for tok in _OUT_OF_SCOPE_NOMINAL_TOKENS)


# Krause-catalog prefix tokens that mark an entry as exonumia /
# non-circulation per CLAUDE.md §9.1: trial strikes / pattern strikes
# («Pn*», «TS*»), essais («E*»). Tokens («Tn*») are NOT filtered here:
# Krause's Tn prefix covers a range of issues from private merchant
# tokens to crown-issued small-change with full denomination markings
# (e.g. Christian VI / Frederik VI 1814-1815 token coinage — KM# Tn1-Tn6
# in Denmark). When such a Tn-piece carries a denomination + period-
# correct weight/composition attested by an acceptable source (per
# §5), it belongs in the catalogue as a Scheidemünze. Filtering on
# bare Tn prefix would silently drop legitimate circulation-adjacent
# small-change coinage. Per-case classification (which Müntzfuß +
# phase + kind) is the curator's call, not a hard-block at hygiene.
_OUT_OF_SCOPE_KM_PREFIXES: tuple[str, ...] = ("Pn", "TS")


def _is_out_of_scope_catalog(catalog) -> bool:
    """Return True when `catalog.km` carries a Krause non-circulation
    prefix (Pn = Pattern, TS = Trial Strike). Tn = Token deliberately
    NOT filtered — see _OUT_OF_SCOPE_KM_PREFIXES docstring above."""
    if not isinstance(catalog, dict):
        return False
    km = catalog.get("km")
    if km is None:
        return False
    candidates: list[str] = []
    if isinstance(km, str):
        candidates.append(km)
    elif isinstance(km, list):
        for item in km:
            if isinstance(item, str):
                candidates.append(item)
            elif isinstance(item, dict):
                v = item.get("value")
                if isinstance(v, str):
                    candidates.append(v)
    elif isinstance(km, dict):
        # dict-form {register: value} per V2_PIPELINE.md §4
        for v in km.values():
            if isinstance(v, str):
                candidates.append(v)
    for value in candidates:
        v = value.strip()
        for prefix in _OUT_OF_SCOPE_KM_PREFIXES:
            if v.startswith(prefix) and len(v) > len(prefix):
                # Require digit immediately after prefix to avoid
                # matching legitimate KMs whose number starts with these
                # letters (none exist in our scope but defensive check).
                if v[len(prefix)].isdigit():
                    return True
    return False


def _apply_pre_write_hygiene(coins: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Run mint + nominal + catalog normalisation in-place and filter
    out coins whose nominal puts them out-of-scope. Returns
    (kept, stats)."""
    stats = {
        "mint_normalised": 0,
        "nominal_normalised": 0,
        "catalog_split": 0,
        "out_of_scope_filtered": 0,
        "out_of_scope_km_filtered": 0,
        "metal_verified_implied": 0,
    }
    kept: list[dict] = []
    for c in coins:
        if not isinstance(c, dict):
            kept.append(c)
            continue
        nominal = c.get("nominal")
        if _is_out_of_scope_nominal(nominal):
            stats["out_of_scope_filtered"] += 1
            continue
        if _is_out_of_scope_catalog(c.get("catalog")):
            stats["out_of_scope_km_filtered"] += 1
            continue
        # Extract embedded mint from nominal («4 Skilling, København»
        # → nominal=«4 Skilling», mint=«København») BEFORE the string-
        # level normaliser, so the mint goes to its dedicated field
        # instead of staying in the rendered nominal text.
        nom_after_mint, mint_after_split = _extract_mint_from_nominal(
            nominal, c.get("mint"))
        if nom_after_mint != nominal:
            c["nominal"] = nom_after_mint
            nominal = nom_after_mint
        if mint_after_split != c.get("mint"):
            c["mint"] = mint_after_split
        new_nom = _normalise_nominal(nominal)
        if new_nom is not None and new_nom != nominal:
            c["nominal"] = new_nom
            stats["nominal_normalised"] += 1
        mint = c.get("mint")
        new_mint = _canonicalise_mint(mint)
        if new_mint != mint and not (new_mint is None and mint in (None, "")):
            c["mint"] = new_mint
            stats["mint_normalised"] += 1
        catalog = c.get("catalog")
        if isinstance(catalog, dict):
            _, n_split = _normalise_catalog(catalog)
            if n_split:
                stats["catalog_split"] += n_split
        # fineness-implies-metal rule: a source that attests fineness
        # has by definition also attested the metal (you cannot publish
        # «.875» without knowing whether it's silver or gold). When
        # `fineness_verified: true` AND metal is non-null, metal_verified
        # MUST be true. V1-bootstrap entries sometimes have
        # metal_verified=false next to fineness_verified=true — that's
        # an inconsistency, not an intended state.
        if (c.get("metal")
                and bool(c.get("fineness_verified"))
                and not bool(c.get("metal_verified"))):
            c["metal_verified"] = True
            stats["metal_verified_implied"] += 1
        # sources-imply-mint rule: when an entry has at least one
        # external source citation (ucoin / numista / numismaster /
        # hede / bruun / galster URL in `sources[]`) AND mint is
        # populated, the mint value came FROM that source's coin page
        # — every source we use publishes mint metadata. V1-bootstrap
        # default of `mint_verified: false` is an under-claim that
        # incorrectly flags the value as a curator guess.
        sources = c.get("sources") or []
        if (c.get("mint")
                and isinstance(sources, list)
                and any(isinstance(s, dict) and s.get("url") for s in sources)
                and not bool(c.get("mint_verified"))):
            c["mint_verified"] = True
            stats.setdefault("mint_verified_implied", 0)
            stats["mint_verified_implied"] += 1
        kept.append(c)
    return kept, stats


def _home_entity(coin: dict) -> str | None:
    """Return the home-file entity for a coin.

    - Scalar `issuing_entity`: that entity.
    - List-form `issuing_entity` (joint mint): alphabetically-first
      entity, per V2_PIPELINE.md §3.10.
    - Missing / empty: None (caller routes to `_unclassified.yml`).
    """
    ie = coin.get("issuing_entity")
    if isinstance(ie, str) and ie:
        return ie
    if isinstance(ie, list) and ie:
        return sorted(str(e) for e in ie if e)[0]
    return None


def write_v2_seed(
    coins: list[dict],
    source_name: str,
    scope_note: str,
    *,
    source_label: str | None = None,
    dry_run: bool = False,
    no_merge: bool = False,
    extra_top_level: dict | None = None,
) -> dict:
    """Group `coins` by `issuing_entity` → write
    `data/v2/seed/<source_name>/<entity>.yml` per entity.

    Parameters
    ----------
    coins : list of Coin-schema dicts. Each must carry `issuing_entity`
        (scalar or list-form). Coins with missing/empty issuing_entity
        route to `_unclassified.yml` for curator review.
    source_name : subdirectory under `data/v2/seed/` to write into.
        E.g. "hede" → `data/v2/seed/hede/`.
    scope_note : human-readable string describing the source + scope.
        Emitted as the `scope_note` header in every output yaml.
    source_label : optional value for the `source` header (defaults
        to source_name).
    dry_run : if True, only logs stats and skips writes.
    no_merge : if True, wholesale-overwrites existing seed yamls
        without `merge_seed` curation preservation. Destructive — use
        only for verification or fresh-build scenarios.
    extra_top_level : optional dict of extra header keys to merge into
        every output yaml's top level (e.g. {"scope_year_from": 1514}).

    Returns
    -------
    dict with summary stats:
      {
        "entities_written": [...],
        "per_entity": {entity: {merged_existing, added_new, orphan_curated, total}},
        "unclassified_count": N,
      }
    """
    # Pre-write hygiene: normalise mints + nominals, drop out-of-scope
    # trade coins (Piastre / Rupee / Fanam / Cash). Runs in-place so
    # all builders benefit uniformly. Returns the kept list +
    # per-source counts of how many entries were touched.
    coins, hygiene_stats = _apply_pre_write_hygiene(list(coins))
    if any(hygiene_stats.values()):
        print(f"\n[{source_name}] pre-write hygiene: "
              f"out_of_scope_filtered={hygiene_stats['out_of_scope_filtered']}, "
              f"nominal_normalised={hygiene_stats['nominal_normalised']}, "
              f"mint_normalised={hygiene_stats['mint_normalised']}")

    by_entity: dict[str, list[dict]] = defaultdict(list)
    unclassified: list[dict] = []
    for c in coins:
        home = _home_entity(c)
        if home is None:
            unclassified.append(c)
            continue
        by_entity[home].append(c)

    src_dir = V2_SEED_ROOT / source_name
    src_dir.mkdir(parents=True, exist_ok=True)

    # Cross-entity dup-purge: when a fresh build re-classifies a coin
    # from entity A to entity B (e.g. mint reading refined → previously
    # `royal_holstein` now `gottorp_duchy`), the OLD entry in A's seed
    # file must be removed, else the same id appears in two files and
    # the cross-source merger sees a phantom duplicate. Walk every
    # existing seed file under this source, collect ids that this fresh
    # build now places under a DIFFERENT entity, drop them from their
    # stale home.
    fresh_id_to_entity: dict[str, str] = {}
    for entity, ents in by_entity.items():
        for c in ents:
            cid = c.get("id")
            if cid:
                fresh_id_to_entity[cid] = entity
    purged_per_file: dict[str, int] = {}
    out_of_scope_per_file: dict[str, int] = {}
    normalised_per_file: dict[str, int] = {}
    if not dry_run and not no_merge:
        import ruamel.yaml as _ruyaml
        purge_yaml = _ruyaml.YAML(typ="rt")
        purge_yaml.preserve_quotes = True
        purge_yaml.width = 200
        purge_yaml.indent(mapping=2, sequence=4, offset=2)
        for existing_path in sorted(src_dir.glob("*.yml")):
            stale_entity_name = existing_path.stem
            if stale_entity_name == "_unclassified":
                # _unclassified entries that fresh build now classifies
                # to a real entity must also be removed from the bucket.
                pass
            with existing_path.open() as f:
                existing_doc = purge_yaml.load(f)
            if not isinstance(existing_doc, dict):
                continue
            existing_coins = existing_doc.get("coins") or []
            kept = []
            purged = 0
            out_of_scope_dropped = 0
            file_normalised = 0
            for c in existing_coins:
                if not isinstance(c, dict):
                    kept.append(c)
                    continue
                # Out-of-scope purge: when the pre-write filter rules
                # are tightened (e.g. extending Piastre → Piaster), the
                # already-stored entries from prior builds need to be
                # purged from existing seed yamls — otherwise merge_seed's
                # orphan-curated mechanism preserves them indefinitely.
                # Same logic applies to Krause exonumia prefixes
                # (Tn / Pn / TS / E) per CLAUDE.md §9.1-§9.2.
                if _is_out_of_scope_nominal(c.get("nominal")):
                    out_of_scope_dropped += 1
                    continue
                if _is_out_of_scope_catalog(c.get("catalog")):
                    out_of_scope_dropped += 1
                    continue
                cid = c.get("id")
                if cid and cid in fresh_id_to_entity:
                    new_entity = fresh_id_to_entity[cid]
                    if new_entity != stale_entity_name:
                        purged += 1
                        continue
                # Normalise orphan-curated entries' nominal + mint in
                # place. The same hygiene that runs on fresh coins
                # applies retroactively to entries the parser no longer
                # produces (the orphan_curated path through merge_seed).
                # Without this, hygiene rule changes leave a long tail
                # of un-normalised entries from prior builds.
                nominal = c.get("nominal")
                # Mint-from-nominal extraction
                nom_after_mint, mint_after_split = _extract_mint_from_nominal(
                    nominal, c.get("mint"))
                if nom_after_mint != nominal:
                    c["nominal"] = nom_after_mint
                    nominal = nom_after_mint
                    file_normalised += 1
                if mint_after_split != c.get("mint"):
                    c["mint"] = mint_after_split
                new_nom = _normalise_nominal(nominal)
                if new_nom is not None and new_nom != nominal:
                    c["nominal"] = new_nom
                    file_normalised += 1
                mint = c.get("mint")
                new_mint = _canonicalise_mint(mint)
                if (new_mint != mint
                        and not (new_mint is None and mint in (None, ""))):
                    c["mint"] = new_mint
                catalog = c.get("catalog")
                if isinstance(catalog, dict):
                    _, n_cat = _normalise_catalog(catalog)
                    if n_cat:
                        file_normalised += 1
                # fineness-implies-metal rule
                if (c.get("metal")
                        and bool(c.get("fineness_verified"))
                        and not bool(c.get("metal_verified"))):
                    c["metal_verified"] = True
                    file_normalised += 1
                # sources-imply-mint rule
                sources = c.get("sources") or []
                if (c.get("mint")
                        and isinstance(sources, list)
                        and any(isinstance(s, dict) and s.get("url") for s in sources)
                        and not bool(c.get("mint_verified"))):
                    c["mint_verified"] = True
                    file_normalised += 1
                kept.append(c)
            if purged or out_of_scope_dropped or file_normalised:
                existing_doc["coins"] = kept
                with existing_path.open("w") as f:
                    purge_yaml.dump(existing_doc, f)
                if purged:
                    purged_per_file[existing_path.name] = purged
                if out_of_scope_dropped:
                    out_of_scope_per_file[existing_path.name] = out_of_scope_dropped
                if file_normalised:
                    normalised_per_file[existing_path.name] = file_normalised

    stats = {
        "entities_written": [],
        "per_entity": {},
        "unclassified_count": len(unclassified),
        "cross_entity_purged": sum(purged_per_file.values()),
    }

    if purged_per_file:
        print(f"\n[{source_name}] cross-entity dup-purge: "
              f"{sum(purged_per_file.values())} stale entries removed "
              f"from {len(purged_per_file)} file(s)")
        for fname, n in sorted(purged_per_file.items()):
            print(f"  - {fname}: {n} entries dropped (re-classified)")
    if out_of_scope_per_file:
        print(f"\n[{source_name}] out-of-scope purge from existing seeds: "
              f"{sum(out_of_scope_per_file.values())} entries removed "
              f"from {len(out_of_scope_per_file)} file(s)")
        for fname, n in sorted(out_of_scope_per_file.items()):
            print(f"  - {fname}: {n} entries dropped (out-of-scope)")
    if normalised_per_file:
        print(f"\n[{source_name}] orphan-curated normalisation: "
              f"{sum(normalised_per_file.values())} entries with nominal "
              f"renormalised across {len(normalised_per_file)} file(s)")
    print(f"\n[{source_name}] grouping → {len(by_entity)} entities, "
          f"{len(unclassified)} unclassified")
    for entity in sorted(by_entity.keys()):
        ents = by_entity[entity]
        # Sort stable for clean diffs
        ents.sort(key=lambda e: (e.get("year_first") or 9999, e.get("id") or ""))
        out_path = src_dir / f"{entity}.yml"
        merge_stats = {"merged_existing": 0, "added_new": len(ents), "orphan_curated": 0}
        if not dry_run and not no_merge:
            ents, merge_stats = merge_seed(ents, out_path)

        print(f"  [{entity}] {len(ents)} entries  "
              f"(merged={merge_stats['merged_existing']}, "
              f"added={merge_stats['added_new']}, "
              f"orphan_curated={merge_stats['orphan_curated']})")

        if dry_run:
            stats["per_entity"][entity] = {**merge_stats, "total": len(ents)}
            continue

        yaml = ruamel.yaml.YAML(typ="rt")
        yaml.preserve_quotes = True
        yaml.width = 200
        yaml.indent(mapping=2, sequence=4, offset=2)
        out = {
            "status": "seed",
            "source": source_label or source_name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entity": entity,
            "scope_note": scope_note,
        }
        if extra_top_level:
            for k, v in extra_top_level.items():
                if k not in out:
                    out[k] = v
        out["coins"] = ents
        with out_path.open("w") as f:
            yaml.dump(out, f)
        stats["entities_written"].append(entity)
        stats["per_entity"][entity] = {**merge_stats, "total": len(ents)}

    # Unclassified bucket — keep coins that the entity classifier failed
    # to resolve so curators can triage them without losing source data.
    if unclassified:
        unclass_path = src_dir / "_unclassified.yml"
        unclassified.sort(key=lambda e: (e.get("year_first") or 9999, e.get("id") or ""))
        merge_stats = {"merged_existing": 0, "added_new": len(unclassified), "orphan_curated": 0}
        if not dry_run and not no_merge:
            unclassified, merge_stats = merge_seed(unclassified, unclass_path)
        print(f"  [_unclassified] {len(unclassified)} entries")
        if not dry_run:
            yaml = ruamel.yaml.YAML(typ="rt")
            yaml.preserve_quotes = True
            yaml.width = 200
            yaml.indent(mapping=2, sequence=4, offset=2)
            out = {
                "status": "seed",
                "source": source_label or source_name,
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "entity": "_unclassified",
                "scope_note": (
                    f"{scope_note} — entries the mint→entity classifier "
                    "could not resolve. Curator triage required: assign "
                    "`issuing_entity` per coin, then re-run the builder."
                ),
                "coins": unclassified,
            }
            with unclass_path.open("w") as f:
                yaml.dump(out, f)
        stats["per_entity"]["_unclassified"] = {**merge_stats, "total": len(unclassified)}

    # Summary
    by_realm = Counter(e for entity, ents in by_entity.items() for e in [entity] for _ in ents)
    print(f"\n[{source_name}] wrote V2 seed: "
          f"{len(stats['entities_written'])} entity file(s)"
          f"{', 1 unclassified file' if unclassified else ''}")
    return stats
