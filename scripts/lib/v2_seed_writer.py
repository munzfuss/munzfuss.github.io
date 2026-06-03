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
    "west india",    # Danish WEST India Company colonial issues — OOS
    "vestindien",    #   «наразі такі коіни за межами скоупу» (user 2026-05-30)
)

# Exact KM numbers that are out-of-scope regardless of nominal wording.
# Catches colonial-company issues whose Hede / NumisMaster records label
# them with a plain denomination («2 Dukat») — only the KM identifies them.
#   A488 — Danish West India Company 2 Ducats 1708 (Krause colonial «A»
#          appendix). User-flagged OOS 2026-05-30.
_OUT_OF_SCOPE_KM_EXACT = frozenset({"A488"})

# Danish-realm denomination DISPLAY spelling normalisation. Numista /
# NumisMaster / Friedberg print the English «Noble» / «Rose Noble» for
# the Danish gold Nobel (Hans 1496 → Frederik I 1532) and Christian IV's
# Rosenobel. The Danish numismatic + project-canonical form (Galster,
# danskmoent.dk/1nobel.htm + 1rosenobel.htm, our `nobel_fod` /
# `rosenobel_fod` Müntzfüße) is «Nobel» / «Rosenobel». Unlike the
# cross-source MATCHING synonyms in `nominal_synonyms.py` (lowercased,
# for equality checks), this map is CASE- and COUNT-preserving for
# display: «2 Nobles» → «2 Nobel» (singular Danish noun after the
# count, per the nominal-field convention «<N> <singular>»). Compound
# forms FIRST so «Rose Noble» resolves before bare «Noble». Scope is
# deliberately NARROW (noble family only) — we do NOT fold
# Thaler→Daler / Ducat→Dukat etc. for display, since the project keeps
# the period-correct German/Danish forms per CLAUDE.md §2.
_NOMINAL_DISPLAY_SPELLING: tuple[tuple[str, str], ...] = (
    (r"\bRose[\s\-]+Nobles?\b", "Rosenobel"),
    (r"\bRosenobles?\b", "Rosenobel"),
    (r"\bNobles?\b", "Nobel"),
    # Portugaløser — Danish ø (Hede / danskmoent / Galster form). Numista /
    # NumisMaster print the ASCII «Portugaloser». A named denomination =
    # 10 Dukat (½ = 5 Dukat, ¼ = 2½ Dukat, 2× = 20 Dukat); see V2_DECISIONS
    # D43 + TODO §CG. Spelling-only here; the «(10 Ducats)» value-equivalent
    # tail is handled by the §CG nominal-hygiene pass, not this normaliser.
    (r"\bPortugaloser\b", "Portugaløser"),
)

# Roman-numeral counts that lead a nominal («IIII Skilling», «XV Skilling»).
# Archaic «IIII» (=4) included — sources print it. Maps the literal token
# to its arabic value; only the LEADING run-of-roman-letters-then-space is
# converted (so word-heads «Mark» / «Lion» / «Christian» never match).
_ROMAN_VALUES: dict[str, int] = {
    "I": 1, "II": 2, "III": 3, "IIII": 4, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13,
    "XIV": 14, "XV": 15, "XVI": 16, "XX": 20, "XXIV": 24, "XXXII": 32,
}
_LEADING_ROMAN_TOKEN_RE = re.compile(r"^([IVXLCDM]+)\s+")
# Fractional WORD leading a nominal → numeric ½ («Halv ørtug» → «½ ørtug»).
_LEADING_HALV_RE = re.compile(r"^(?:Halv|Halve|Half|Halb)\s+", re.IGNORECASE)
# Known geographic / territorial prefixes that leaked into the nominal
# field («Oldenburg. Taler», «Lübeck (Bishopric). Ducat»). The place is
# the issuing entity (the coin lives in that entity file), never part of
# the nominal. A CLOSED set — NOT a generic «<Capital>. » match — so
# non-place prefixes that happen to fit the shape («Gold Off-Metal.», an
# off-strike annotation; «Danish West India Company.», an issuer) are
# left for the curated §CG pass instead of being silently dropped.
_NOMINAL_LOCATION_PREFIXES = frozenset({
    "oldenburg", "lübeck", "lübeck (bishopric)", "bremen (bishopric)",
    "bremen & verden", "rantzau", "osnabrück", "wismar", "hesse-kassel",
    "lauenburg", "lower saxony", "copenhagen", "lübeck (bistum)",
    "s chleswig-holstein-schaumburg-pinneberg",
})
# Editorial prefix that is NOT part of the denomination («Commemorative
# 2 Kroner», «Largesse 4 Ducats»). The commemorative / largesse character
# is carried by `kind: gedenk`, not the nominal — strip it.
_LEADING_EDITORIAL_RE = re.compile(r"^(?:Commemorative|Largesse)\s+", re.IGNORECASE)
# Trailing decimal-number paren = the piece weight in grams («1 Ducat (3.5)»,
# «1 Crown (15.75)») — a parser bleed; the weight lives in `weight_rough_g`.
# Decimal-only so it never touches a denomination equivalent like «(8 Mark)»
# or «(= 20)».
_TRAILING_WEIGHT_PAREN_RE = re.compile(r"\s*\(\d+\.\d+\)\s*$")
# Trailing modern-currency / metric equivalence («1 Øre (0.01 DKK)»).
_TRAILING_MODERN_PAREN_RE = re.compile(r"\s*\(\s*=?\s*[\d.,]+\s*DKK\s*\)\s*$", re.IGNORECASE)

# Nominal heads that are NOT real denominations — generic descriptors /
# placeholders that must never receive an implicit «1 » count.
_NON_DENOMINATION_NOMINALS = frozenset({
    "(?)", "gold coin", "gold issue", "gold bracteate", "gold medallic",
    "medal", "silver coin", "coin",
})

# Denomination-noun keyword set — used by `_extract_mint_from_nominal` to
# recognise a «<mint>, <denomination>» split (the post-comma head must be a
# known denomination for the pre-comma part to be treated as the mint).
# (The implicit-«1 » prepend no longer uses this — that switched to the
# guard-based `_should_prepend_one` in §CG-D43 — but mint-extraction still
# needs the keyword list, so it stays.)
_BARE_DENOMINATION_NOUNS = frozenset({
    "ducat", "dukat", "thaler", "speciedaler", "specie daler",
    "krone", "skilling", "mark", "søsling", "hvid", "penning",
    "denning", "dobbelthvid", "firehvid", "treskilling", "joachimstaler",
    "pfennig", "schilling", "sechsling", "dreiling", "groschen",
    "goldgulden", "gulden", "portugaløser", "rosenobel", "nobel",
    "reichsthaler", "kronenthaler", "rhinsk gylden", "sølvgylden",
    "rigsdaler", "rigsbankdaler", "rigsbankskilling",
    "pistole", "friedrichsdor", "rosenoble",
})

# Leading roman-numeral count («IIII Skilling», «XV Skilling»). Archaic
# «IIII» (=4) is intentionally allowed — sources print it. Matched as a
# run of roman letters immediately followed by whitespace, so word-heads
# like «Mark» / «Lion» / «Dukat» (single roman letter then a non-space)
# do not match.
_LEADING_ROMAN_RE = re.compile(r"^[IVXLCDM]+\s")
# Leading place / mint prefix ending in «. » («Oldenburg. Taler»,
# «Lübeck (Bishopric). Taler», «Bremen & Verden. 4 Mark»). The location
# has leaked into the nominal field — a separate data-quality issue, but
# never an implicit count, so we must not prepend «1 » at the front.
_LEADING_PLACE_DOT_RE = re.compile(r"^[A-ZÄÖÜØÅ][^.]*\.\s")
# Leading fractional WORD («Halv ørtug», «Half Portugaloser»).
_LEADING_FRACTION_WORD_RE = re.compile(r"^(?:halv|halve|half|halb)\b", re.IGNORECASE)
# Characters that signal an explicit count is already present.
_QUANTITY_CHARS = "0123456789½¼¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞"

# Canonical mint name table — normalises the dozens of orthographic
# variants encountered across sources (English / Danish / Latin
# spellings, country-prefixed ucoin format, modern vs historical
# spellings) to ONE canonical form per physical mint town.
# Mint canonicalisation is centralised in `mint_registry` (single source
# of truth — same registry drives entity classification in
# v2_entity_classify.py). See `mint_registry.py` module docstring for
# the rationale + the 2026-05-26 ASCII-alias regression that motivated
# unifying the previously-split tables.
#
# Derived `{alias: display}` map for fast _canonicalise_mint lookup.
# Project convention per CLAUDE.md i18n policy: German period spelling
# for project canonical (Kopenhagen, Christiania, Glückstadt, Altona).
from lib.mint_registry import (  # noqa: E402
    ALIAS_TO_CANON as _MINT_ALIAS_TO_CANON,
    CANON_TO_DISPLAY as _MINT_CANON_TO_DISPLAY,
)
from lib.nominal_synonyms import normalise_nominal as _fold_denom  # noqa: E402


def _same_denomination(head_word: str, paren_word: str) -> bool:
    """True when two denomination words are the SAME denomination in a
    different language / spelling / plural («Ducats» / «Dukaten»,
    «Skilling» / «Skillinger», «Krone» / «Kroner»), rather than two
    DIFFERENT denominations («Mark» / «Krone», «Speciedaler» /
    «Reichstaler»). Used to decide whether a trailing single-word paren
    is a translation hint (safe to strip) or a cross-denomination
    equivalence (must NOT be deleted — per CLAUDE.md §1 the equivalent
    belongs in `note`, the nominal carries the inscribed denomination).
    Folds via the cross-source synonym table (so «Ducats»≡«Dukaten»),
    then accepts a shared stem for plural/inflection variants."""
    a, b = _fold_denom(head_word), _fold_denom(paren_word)
    if not a or not b:
        return False
    return a == b or a.startswith(b) or b.startswith(a)
_MINT_CANONICAL: dict[str, str] = {
    alias: _MINT_CANON_TO_DISPLAY[canon]
    for alias, canon in _MINT_ALIAS_TO_CANON.items()
    if canon in _MINT_CANON_TO_DISPLAY
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
        # Strip trailing « Mint» suffix (Bruun PDF convention) so the
        # canonical form matches project-bare-mint spelling. Consistent
        # with merger's `_normalise_mints` strip.
        base = re.sub(r"\s+Mint\s*$", "", base).strip()
        if not base:
            continue
        # Split on comma — drop country prefix tokens, canonicalise the
        # rest. «Denmark, Copenhagen» → Kopenhagen.
        for tok in [t.strip() for t in base.split(",") if t.strip()]:
            # Re-strip « Mint» on each token in case multi-token form
            # like «Denmark, Copenhagen Mint» entered (rare but possible).
            tok = re.sub(r"\s+Mint\s*$", "", tok).strip()
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


def _should_prepend_one(s: str) -> bool:
    """Decide whether a bare nominal needs an implicit «1 » count.

    Per CLAUDE.md (mathematically-verified register) every coin row
    carries an explicit denomination count; sources that publish just
    the denomination noun («Skilling», «Taler», «Nobel») get «1 »
    prefixed. This is GUARD-based (skip-list) rather than an allowlist,
    so qualifier-bearing and future denominations («Skilling Rigsmønt»,
    «Gold Krone», «Silver Gulden (Taler)», «Albertsdaler») are handled
    by default. Returns False (skip) when an implicit «1 » would be
    wrong:

      1. an explicit count is already present — leading OR embedded
         digit / fraction glyph once paren-clarifiers like «(10 Ducats)»
         are removed («Commemorative 2 Kroner», «Speciedaler / 3 Mark»);
      2. a leading roman-numeral count («IIII Skilling»);
      3. a leading fractional word («Halv ørtug», «Half Portugaloser»);
      4. a leading place / mint prefix («Oldenburg. Taler») or an
         uncertain-mint «… eller …» attribution that leaked into the
         nominal field («Hamar (Norge) eller København, Søsling(?)»);
      5. a non-denomination placeholder («(?)», «Gold coin», «Medal»).
    """
    if not s:
        return False
    # Strip paren clarifiers so an embedded equivalence «(10 Ducats)»
    # is not mistaken for the denomination's own count.
    bare = re.sub(r"\([^)]*\)", "", s).strip()
    if not bare:
        return False
    # 1. explicit count already present (leading or embedded).
    if any(ch in _QUANTITY_CHARS for ch in bare):
        return False
    # 2. leading roman-numeral count.
    if _LEADING_ROMAN_RE.match(bare):
        return False
    # 3. leading fractional word.
    if _LEADING_FRACTION_WORD_RE.match(bare):
        return False
    # 4. leading place / mint prefix, or uncertain-mint attribution.
    if _LEADING_PLACE_DOT_RE.match(s):
        return False
    if " eller " in bare.lower():
        return False
    first_token = re.split(r"[\s,;]", bare, maxsplit=1)[0].lower()
    if first_token in _MINT_ALIAS_TO_CANON:
        return False
    # 5. non-denomination placeholder.
    head = bare.split(",")[0].split(";")[0].strip().lower()
    if head in _NON_DENOMINATION_NOMINALS:
        return False
    return True


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
    # Strip bare trailing 4-digit year (no comma): «1 Speciedaler 1597»
    # → «1 Speciedaler». Source page titles often append the year to
    # the denomination header; that year already lives in `year_first` /
    # `year_label`, so duplicating it in the nominal field clutters the
    # rendered text + breaks cross-source nominal-matching when sources
    # differ on year suffix presence.
    s = re.sub(r"\s+\d{4}(?:[-–]\d{4})?\s*$", "", s).strip()
    # Strip Numista value_text trailing decorations:
    #   «(Dukaten)» — German translation hint of the same denomination
    #   «(7)» — Numista category number
    # Both appear in pairs or singly («2 Ducats (Dukaten) (7)»).
    # Word-form parens are stripped ONLY when the word matches a known
    # denomination-translation hint — that preserves legitimate variant
    # markers like «(Firehvid)» / «(Tohvid)» which are period-attested
    # sub-types, not translations.
    _DENOMINATION_TRANSLATION_HINTS = {
        # German-form translations of Danish denominations
        "dukaten", "ducaten", "ducati", "ducates", "ducatos",
        "mark", "marck", "marke", "marken",
        "schillinge", "schillinger",
        "pfennige", "pfennigen",
        "groschen",
        "krone", "kronen", "kroner",
        "daler", "dalere", "dalern",
        "speciedalere", "speciedalern",
        "talern", "thaler", "thaler", "talers",
        "rigsdalere", "rigsbankdalere",
        "skilling", "skillinger",
        "ören", "ören",
        "öre", "ore",
    }
    while True:
        m = re.search(
            r"\s*\(([A-Za-zæøåüÆØÅÜ]+|\d+)\)\s*$",
            s,
        )
        if not m:
            break
        token = m.group(1)
        # Numeric category — strip unconditionally
        if token.isdigit():
            s = s[:m.start()].rstrip()
            continue
        # Word — strip ONLY when it's a same-denomination language/plural
        # variant of the head («2 Ducats (Dukaten)» → «2 Ducats»). A
        # DIFFERENT-denomination token in parens is an equivalence /
        # nickname («4 Mark (Krone)», «1 Speciedaler (Reichstaler)») —
        # per CLAUDE.md §1 the inscribed/source denomination is the
        # nominal and the equivalent belongs in `note`, so this
        # normaliser must NOT silently delete it. Keep it in place; the
        # §1 decision is curation, not a silent strip.
        if token.lower() in _DENOMINATION_TRANSLATION_HINTS:
            head_part = s[:m.start()].rstrip()
            head_words = head_part.split()
            head_denom = head_words[-1] if head_words else ""
            if _same_denomination(head_denom, token):
                s = head_part
                continue
        break  # different-denomination / non-hint paren — keep (variant marker)
    # Collapse extra whitespace before comma: «X , Y» → «X, Y»
    s = re.sub(r"\s+,", ",", s)
    # Collapse multiple spaces (e.g. «X,  Y» → «X, Y»)
    s = re.sub(r"\s{2,}", " ", s)
    # Expand parenthesised abbreviation-completion: «Fr(ederiks) D'or»
    # → «Frederiks D'or», «Chr(istians) D'or» → «Christians D'or»,
    # «Fr(Ederiks) D'or» (NumisMaster's uppercase variant) →
    # «Frederiks D'or». The Danish numismatic convention prints the
    # genitive suffix in parens immediately after the abbreviation
    # root («Fr» / «Chr»), with NO space between root and opening
    # paren. The legitimate paren-clarifier case («1 Skilling
    # (Firehvid)», «Ny mønt (1844)») has a SPACE before «(» —
    # distinguishable from the abbreviation form.
    # NumisMaster sometimes capitalises the first letter inside the
    # parens («Fr(Ederiks)») — normalise to lowercase to match the
    # Schou/Hede convention.
    def _expand_paren_abbrev(m):
        root = m.group(1)  # «Fr» / «Chr»
        suffix = m.group(2).lower()  # «Ederiks» → «ederiks»
        return f"{root}{suffix}"

    s = re.sub(
        r"\b([A-Z][a-z]*)\(([A-Za-zæøåüÆØÅÜ]+)\)",
        _expand_paren_abbrev,
        s,
    )
    # Danish-realm denomination spelling: English «Noble» / «Rose Noble»
    # → canonical Danish «Nobel» / «Rosenobel» (case- + count-preserving).
    # Runs BEFORE the implicit-«1 » step so «Noble» → «Nobel» → «1 Nobel».
    for pattern, replacement in _NOMINAL_DISPLAY_SPELLING:
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)
    # Add an implicit leading «1 » when the nominal is a bare denomination
    # with no explicit count. Guard-based — see `_should_prepend_one`.
    #   «Penning» → «1 Penning», «Skilling Rigsmønt» → «1 Skilling Rigsmønt»,
    #   «Nobel» → «1 Nobel», «Halv Sølvgylden» / «Oldenburg. Taler» kept as-is.
    if _should_prepend_one(s):
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


_FRACNICK_FRACTION = r"1/\d+|\d*[½¼¾⅛⅓⅔⅕⅙⅚⅜⅝⅞]"


def split_nominal_annotations(nominal):
    """Split a nominal into (clean_denomination, [annotations]) per
    CLAUDE.md §1 / TODO §CG: a trailing/embedded **fraction-of-standard**
    paren («1/96 Speciedaler», «⅛ Speciedaler») or **nickname / alternative
    name** paren («Sechsling», «Reisedaler», «Doppeltaler») is editorial and
    belongs in `note` — the leading denomination is the nominal.

    Returns `(nominal, [])` UNCHANGED (caller leaves the coin alone) when the
    nominal carries something this pass must NOT decide:
      * a dual FULL-denomination equivalence — «X = Y» or «(N <denom>)»
        (the §CI legend-verification set: is the second denomination
        inscribed?);
      * a «Portugaløser» tail — the correct nominal there is «Portugaløser»,
        a separate reorder, not a strip-to-note;
      * any paren this classifier doesn't recognise (defensive: leave it).
    """
    if not nominal:
        return nominal, []
    s = str(nominal)
    if re.search(r"=\s", s):          # dual equivalence → §CI, leave
        return s, []
    parens = re.findall(r"\(([^)]*)\)", s)
    if not parens:
        return s, []
    if any("portugal" in p.lower() for p in parens):   # Portugaløser-special
        return s, []
    payloads: list[str] = []
    for p in parens:
        pc = p.strip()
        if re.match(r"^\d+\s+[A-Za-zÆØÅæøå]", pc):     # «8 Mark» whole-denom → §CI
            return s, []
        if re.match(rf"^({_FRACNICK_FRACTION})(\s|$)", pc) or \
           re.match(r"^[A-Za-zÆØÅæøåäöü][A-Za-zÆØÅæøåäöü .'\-]*$", pc):
            payloads.append(pc)
        elif re.match(r"^\d+\.\d+$", pc):              # decimal weight (Stage B) — ignore
            continue
        else:
            return s, []                              # unrecognised → leave
    if not payloads:
        return s, []
    clean = s
    for pc in payloads:
        clean = re.sub(r"\s*\(\s*" + re.escape(pc) + r"\s*\)", "", clean)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean, payloads


def portugaloser_medallic_split(nominal):
    """Portugaløser «(N Ducats)» reorder + «Gold Medallic» prefix strip
    (TODO §CG stage-C tail). Returns (clean_nominal, [payloads]):
      * «Gold Medallic 2 Ducats» → («2 Ducats», []) — strip-only, the
        «Medallic» style already lives in the note; «Gold» is the metal;
      * «1 Portugaløser (10 Ducats)» / «10 Ducats (Portugaløser)» →
        («1 Portugaløser», [«10 Ducats»]) — Portugaløser is the named
        denomination (= 10 Dukat), the ducat/speciedaler equivalent → note;
      * unchanged nominals return (nominal, [])."""
    if not nominal:
        return nominal, []
    s = str(nominal)
    if s.lower().startswith("gold medallic "):
        return s[len("Gold Medallic "):].strip(), []
    if "portugal" in s.lower():
        m = re.search(r"([0-9½¼¾⅛⅓⅔]*)\s*[Pp]ortugal[øo]ser", s)
        qty = (m.group(1).strip() if m and m.group(1).strip() else "1")
        clean = f"{qty} Portugaløser"
        if clean == s:
            return s, []
        other = re.sub(r"\(?\s*[0-9½¼¾⅛⅓⅔]*\s*[Pp]ortugal[øo]ser\s*\)?", "", s)
        other = re.sub(r"[()=]", " ", other)
        other = re.sub(r"\s+", " ", other).strip(" ;")
        return clean, ([other] if other else [])
    return s, []


def normalise_nominal_display(raw):
    """Lightweight DISPLAY normalisation for ALREADY-typed nominals.

    Applies only the two reader-facing rules that must hold on every
    rendered coin row regardless of source path:
      * Danish-realm spelling — «Noble»/«Rose Noble» → «Nobel»/«Rosenobel»
        (case- + count-preserving);
      * implicit «1 » count for a bare denomination (`_should_prepend_one`).

    Unlike `_normalise_nominal` (the full raw-ingest pipeline) it does
    NOT strip years / paren-clarifiers / mojibake / reformat fractions,
    so it is safe to re-apply at render time and on curated data without
    altering intentional content (e.g. it leaves «4 Mark (Krone)» and
    «1/2 Taler» untouched). Idempotent; None passes through unchanged.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # Leading place / mint prefix that leaked into the nominal («Oldenburg.
    # Taler», «Lübeck (Bishopric). Ducat», double «Oldenburg. Lübeck
    # (Bishopric). 5 Taler») — the location is the issuing entity (the coin
    # already lives in that entity file), never part of the nominal. Strip
    # repeatedly for stacked prefixes. Per CLAUDE.md §1 / TODO §CG.
    for _ in range(3):
        if ". " not in s:
            break
        prefix = s.split(". ", 1)[0].strip()
        if prefix.lower() not in _NOMINAL_LOCATION_PREFIXES:
            break
        s = s.split(". ", 1)[1].lstrip()
    # Leading editorial word → strip (character carried by kind=gedenk).
    s = _LEADING_EDITORIAL_RE.sub("", s).strip()
    # Trailing weight-in-grams paren + modern-currency equivalence → drop
    # (weight lives in weight_rough_g; DKK value is derivable, not a nominal).
    s = _TRAILING_WEIGHT_PAREN_RE.sub("", s)
    s = _TRAILING_MODERN_PAREN_RE.sub("", s)
    s = s.strip()
    if not s:
        return None
    # Leading fractional word → ½ («Halv ørtug» → «½ ørtug»). Lossless.
    s = _LEADING_HALV_RE.sub("½ ", s)
    # Leading roman-numeral count → arabic («IIII Skilling» → «4 Skilling»).
    m = _LEADING_ROMAN_TOKEN_RE.match(s)
    if m and m.group(1) in _ROMAN_VALUES:
        s = f"{_ROMAN_VALUES[m.group(1)]} {s[m.end():]}"
    for pattern, replacement in _NOMINAL_DISPLAY_SPELLING:
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)
    if _should_prepend_one(s):
        s = f"1 {s}"
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


# Danish catalogue year-variant prose: «hhv.» = henholdsvis (respectively),
# «og» = and, «mangler»/«ej»/«ingen» = missing/none. danskmoent.dk + Hede note
# a multi-year type's per-variant catalogue numbers as «Schou hhv. A og B»
# (= variants are Schou A and B respectively). That prose is not a catalogue
# index — strip it, keep only the distinct index numbers/ranges (curator rule:
# «keep correct indices, drop the prose»). Applied ONLY to numeric Danish-
# catalogue fields (schou/sieg/hede/galster), never to free-text like `others`
# (museum names contain legitimate «og», e.g. «Mønt- og Medaillesamling»).
_INDEX_PROSE_RE = re.compile(r"hhv\.?|\bog\b|henholdsvis", re.IGNORECASE)
_INDEX_PROSE_DROP_RE = re.compile(r"^(?:mangler|ej|ingen|-+)$", re.IGNORECASE)


def _clean_index_prose(value):
    """«Schou hhv. 1 og 1» → «1»; «2 og 3» → ['2','3']; «hhv. 2 og mangler» → «2».
    Returns scalar when one distinct index remains, list when several, the
    input unchanged when no prose is present, None when nothing survives."""
    def _tokens(s: str) -> list[str]:
        s = str(s)
        if not _INDEX_PROSE_RE.search(s):
            return [s]  # no prose — leave verbatim (e.g. plain «227» / «228-235»)
        s = re.sub(r"hhv\.?|henholdsvis", " ", s, flags=re.IGNORECASE)
        out: list[str] = []
        for t in re.split(r"\bog\b|,", s, flags=re.IGNORECASE):
            t = t.strip(" .")
            if not t or _INDEX_PROSE_DROP_RE.match(t):
                continue
            if t not in out:
                out.append(t)
        return out

    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for v in items:
        for t in _tokens(v):
            if t not in result:
                result.append(t)
    if not result:
        return None
    return result[0] if len(result) == 1 else result


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
    # Strip Danish year-variant prose («hhv. A og B») from the Danish-catalogue
    # index fields, keeping only the distinct catalogue indices.
    for pf in ("schou", "sieg", "hede", "galster"):
        v = catalog.get(pf)
        if v and isinstance(v, (str, list)) and _INDEX_PROSE_RE.search(str(v)):
            cleaned = _clean_index_prose(v)
            if cleaned != v:
                catalog[pf] = cleaned
                changes += 1
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
    # Leading mint, optionally a slash-compound «Hamar/Oslo».
    # Inner mint pattern wrapped in (?:...) — the OUTER capture group
    # spans the full compound («Hamar/Oslo» or just «Hamar»).
    r"^((?:" + _NOMINAL_MINT_PATTERN + r")"
    r"(?:\s*/\s*(?:" + _NOMINAL_MINT_PATTERN + r"))?)"
    r"\s*,\s*",
    re.IGNORECASE,
)
_NOMINAL_SHAPE_RE = re.compile(
    r"[,\s]+\(?(klipping|klippe|firkant)\)?\s*$",
    re.IGNORECASE,
)
# Narrative mint-statement fragments that bleed from Danish page
# titles into denomination strings. «; prægested ukendt» literally
# means «; mint unknown» — a curator statement about provenance, not
# part of the coin's nominal. Strip from nominal tail.
_NOMINAL_NARRATIVE_TAIL_RE = re.compile(
    r"\s*[;,]\s*"
    r"(prægested\s+ukendt|mønt(?:sted)?\s+ukendt|ukendt\s+mønt(?:sted)?)"
    r"\s*$",
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
    # Denomination-keyword detection (complex-mint fallback). When the
    # string has a comma AND the post-comma part starts with a known
    # denomination noun (or fraction + denomination noun), treat the
    # pre-comma part as the mint (even when it's a complex narrative
    # like «Hamar (Norge) eller København»), and the post-comma part
    # as the denomination. Catches forms that the standard trailing
    # and leading patterns miss because the mint is multi-word or
    # contains parens.
    if not extracted_mint and "," in s:
        # Build a regex that matches «<count>?<bare-noun>» as the post-
        # comma denomination head. Use the bare-noun set for the
        # word match.
        denom_pattern = "|".join(
            re.escape(d) for d in _BARE_DENOMINATION_NOUNS
        )
        # Find the LAST comma whose right-hand side starts with a
        # known denomination keyword. Iterate right-to-left so the
        # mint takes everything BEFORE the last comma that
        # introduces a denomination.
        commas = [i for i, ch in enumerate(s) if ch == ","]
        for idx in reversed(commas):
            left, right = s[:idx].strip(), s[idx + 1:].strip()
            # Strip trailing «(?)» / «(klipping)» from the
            # denomination candidate so the head-word check sees
            # the denomination noun unencumbered.
            right_head = re.sub(
                r"\s*\([^)]*\)\s*$", "", right
            ).strip()
            # Allow optional leading count or fraction
            denom_match = re.match(
                r"^(?:\d+(?:[/¼½¾⅓⅔⅛]\d*)?\s+)?"
                r"(?P<noun>(?:" + denom_pattern + r"))"
                r"(?:\([^)]+\))?\s*$",
                right_head,
                flags=re.IGNORECASE,
            )
            if denom_match and left:
                extracted_mint = left
                s = right  # keep the (?) / (klipping) on the
                            # denomination for later stripping passes
                break
    # Narrative mint-statement fragments stripped first («; prægested
    # ukendt» = «; mint unknown» — curator's provenance note, not
    # part of denomination)
    s = _NOMINAL_NARRATIVE_TAIL_RE.sub("", s).rstrip(" ,;")
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
        if v in _OUT_OF_SCOPE_KM_EXACT:
            return True
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
        # §CG-C: editorial content out of `nominal` → `note` (the
        # inscribed/source denomination is the nominal per §1). Two
        # splitters: (1) fraction-of-standard / nickname; (2) Portugaløser
        # «(N Ducats)» reorder + «Gold Medallic» prefix. Dual «X = Y» /
        # «(N denom)» return [] (left for §CI legend verification).
        for _splitter in (split_nominal_annotations, portugaloser_medallic_split):
            cur_nom = c.get("nominal")
            clean_nom, payloads = _splitter(cur_nom)
            if clean_nom == cur_nom:
                continue
            if not payloads:                       # strip-only (e.g. Gold Medallic)
                c["nominal"] = clean_nom
                stats["nominal_annotation_to_note"] = stats.get("nominal_annotation_to_note", 0) + 1
                continue
            note = c.get("note")
            present = False
            if isinstance(note, dict):
                present = all(any(p in str(v) for v in note.values() if v) for p in payloads)
            elif isinstance(note, str):
                present = all(p in note for p in payloads)
            if note is None:
                ps = "; ".join(payloads)
                c["note"] = {"de": ps, "en": ps, "uk": ps}
                c["nominal"] = clean_nom
                stats["nominal_annotation_to_note"] = stats.get("nominal_annotation_to_note", 0) + 1
            elif present:
                c["nominal"] = clean_nom
                stats["nominal_annotation_to_note"] = stats.get("nominal_annotation_to_note", 0) + 1
            # else: note exists but payload absent → leave (avoid mismatched-note append)
        mint = c.get("mint")
        # Detect ambiguity-indicators in the mint string («København eller
        # Malmø», «Copenhagen or Malmø», «København/Malmø», «Hamburg oder
        # Altona»). These come from Hede/Galster source pages where the
        # cataloguer documents uncertainty between candidate mints. Split
        # into list-form and mark mint_verified=false so the (?) marker
        # renders in the table per CLAUDE.md §4 unconfirmed-data convention.
        AMBIG_RE = re.compile(r"\s*(?:\beller\b|\boder\b|\bor\b|/)\s*",
                              re.IGNORECASE)
        if isinstance(mint, str) and AMBIG_RE.search(mint):
            tokens = [t.strip() for t in AMBIG_RE.split(mint) if t.strip()]
            if len(tokens) >= 2:
                mint = tokens
                c["mint"] = mint
                # When the SOURCE itself documents uncertainty, the value
                # is curator-guess-shaped — flag as unverified so (?) renders.
                c["mint_verified"] = False
                stats.setdefault("mint_ambiguity_split", 0)
                stats["mint_ambiguity_split"] += 1
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
        # The sources-imply-mint rule does NOT fire when the mint is
        # list-form: that signals either (a) genuine joint-mint coinage
        # documented by the source, or (b) ambiguity-split (source itself
        # documents uncertainty between candidates). Either way, the
        # auto-promotion to verified is inappropriate — joint mints
        # preserve their original mint_verified, ambiguity-splits stay
        # at False per the explicit hygiene-split above.
        if (c.get("mint")
                and not isinstance(c.get("mint"), list)
                and isinstance(sources, list)
                and any(isinstance(s, dict) and s.get("url") for s in sources)
                and not bool(c.get("mint_verified"))):
            c["mint_verified"] = True
            stats.setdefault("mint_verified_implied", 0)
            stats["mint_verified_implied"] += 1
        kept.append(c)
    return kept, stats


def _check_entity_invariant(
    coins: list[dict],
    source_name: str,
) -> dict:
    """Per-coin invariant check: when `mint` maps unambiguously to ONE
    entity via the unified `mint_registry`, the coin's `issuing_entity`
    SHOULD match that mapping. Disagreements are reported to stdout
    + returned in the stats dict.

    A disagreement is NOT auto-corrected here — some source builders
    legitimately override the mint-based default (NumisMaster classifies
    by Krause-region / issuer-name, which is year-aware for cases like
    Altona pre-1640 = Schauenburg vs post-1640 = Royal-Holstein). The
    invariant check exists so a fresh regression surfaces immediately
    rather than waiting for a project-wide audit run.

    The 2026-05-26 entity-classification refactor (mint_registry
    unification) closed an ASCII-alias gap that had silently routed
    87 royal-Holstein-mint Bruun + NumisMaster + ucoin entries to
    `danish_realm` for several months. Without this invariant the next
    similar regression (new mint alias added to one table but not the
    other; new harvester emitting an un-recognised spelling) would only
    surface via manual user-visible side effects.
    """
    # Lazy import to avoid circular dependency at module load.
    from lib.v2_entity_classify import classify_mint_to_entity  # noqa: PLC0415

    stats = {"entity_mismatch": 0}
    mismatches: list[tuple[str, str, str, str]] = []  # (id, mint, current, expected)
    for c in coins:
        mint = c.get("mint")
        if mint in (None, "", []):
            continue
        expected = classify_mint_to_entity(mint)
        if expected is None:
            continue
        ie = c.get("issuing_entity")
        current = ie if isinstance(ie, str) else (
            sorted(str(e) for e in ie if e)[0] if isinstance(ie, list) and ie else None
        )
        # Normalise expected to scalar (alphabetically-first for list-form
        # — matches `_home_entity` convention).
        expected_scalar = expected if isinstance(expected, str) else (
            sorted(str(e) for e in expected if e)[0] if isinstance(expected, list) else None
        )
        if current is None or expected_scalar is None:
            continue
        if current != expected_scalar:
            # Special case: when BOTH current and expected are in the
            # coin's list-form issuing_entity, treat as agreement (joint
            # mint where multiple entities are legitimately claimed).
            if isinstance(ie, list) and expected_scalar in [str(e) for e in ie]:
                continue
            stats["entity_mismatch"] += 1
            mismatches.append((str(c.get("id", "?")), str(mint),
                               current, expected_scalar))
    if mismatches:
        print(f"\n[{source_name}] ⚠️  ENTITY INVARIANT: "
              f"{len(mismatches)} coins have mint→entity disagreement")
        print(f"  (mint-classifier returns one entity, "
              f"coin's issuing_entity says another)")
        # Print up to first 10 to keep log readable
        for cid, mint, cur, exp in mismatches[:10]:
            print(f"    {cid:42s}  mint={mint:18s}  "
                  f"current={cur}  expected={exp}")
        if len(mismatches) > 10:
            print(f"    ... and {len(mismatches) - 10} more")
        print(f"  Run `scripts/maintenance/audit_entity_misclassifications.py --apply` "
              f"to relocate to expected entity.")
    return stats


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

    # Entity-invariant check (post-hygiene so the normalised mint string
    # is what the classifier sees). Emits warnings to stdout for any
    # coin whose `issuing_entity` disagrees with what the mint-driven
    # classifier returns. Doesn't auto-correct — the C-stage maintenance
    # script is the authorised path to relocate misclassified entries
    # (preserves curator decisions + handles cross-file moves cleanly).
    _check_entity_invariant(coins, source_name)

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
