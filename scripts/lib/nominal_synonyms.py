"""Danish ↔ English/German denomination synonym table for nominal-
based matching across cross-source pipeline stages.

Hede / Galster / Bruun / our project YAML use Danish / period German
forms («Nobel», «Dukat», «Daler», «Skilling»). Numista / NumisMaster
use English forms («Noble», «Ducat», «Thaler», «Schilling»).
Without normalisation, code that performs substring or equality
checks on coin nominals fragments identical types across sources.

Direction is English/German → Danish (canonical Hede form), applied
AFTER lowercasing. Compound forms come FIRST so single-word patterns
don't partially substitute (e.g. «Rose Noble» → «rosenobel» before
bare «Noble» → «nobel»). Word-boundary anchored to preserve
sub-variant qualifiers (e.g. «Skilling Lybsk» stays whole).

Consumers:
  * `scripts/maintenance/merge_seeds_cross_source.py::_normalise_nominal`
    — cross-source coin matcher (primary signal comparison).
  * `scripts/maintenance/auto_classify_seed_unsorted.py::_normalise_nominal_for_anchor`
    — denomination-anchor classifier rule patterns.

Keep additions to this list narrow + verified by survey before
adding new synonyms — false-fold risk is real (e.g. don't conflate
«Krone» with «Crown» unless every source uses identical-meaning,
which isn't the case for our scope).
"""
from __future__ import annotations

import re
from functools import lru_cache

# ---------------------------------------------------------------------------
# Pre-substitution normalisation (format noise, not denomination synonyms).
# Applied in `normalise_nominal` BEFORE the NOMINAL_SYNONYMS table. These were
# mined from same-coin nominal divergences (entries sharing a globally-unique
# bruun_collection_id) — they are pure spelling/format variants of the SAME
# denomination, safe for the matcher. Genuine denomination DIFFERENCES (Ungersk
# vs Rhinsk Gylden, Krone≡4 Mark accounting equivalence, Klippe sub-variants)
# are deliberately NOT folded here — they stay distinct.
# ---------------------------------------------------------------------------

# Unicode vulgar fractions + the U+2044 fraction slash → ASCII «n/m» so
# «½ Daler» ≡ «1/2 Daler» and «1⁄16 Daler» ≡ «1/16 Daler».
_UNICODE_FRACTIONS = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5", "⅙": "1/6",
    "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
    "⁄": "/",
}

# Danish diacritics → ASCII (matching only — «Portugaløser» ≡ «Portugaloser»).
_DIACRITIC_FOLD = {"ø": "o", "æ": "ae", "å": "a", "ö": "o", "ä": "ae", "ü": "u"}

# Bruun-catalogue region/issuer prefixes («Lübeck. Daler», «Oldenburg. Taler»).
# Stripped leading-segment-wise; the region is not a coin-identity discriminator
# (and the per-entity matcher never compares across regions anyway). Includes a
# known OCR typo variant («s chleswig…»).
_REGION_PREFIXES = frozenset({
    "lübeck", "lubeck", "oldenburg", "bremen", "bremen & verden", "lower saxony",
    "osnabrück", "osnabruck", "hesse-kassel", "lauenburg", "wismar", "rantzau",
    "copenhagen", "danish east india company",
    "schleswig-holstein-schaumburg-pinneberg", "s chleswig-holstein-schaumburg-pinneberg",
    "lübeck (bishopric)", "lubeck (bishopric)",
})


def _strip_region_prefixes(s: str) -> str:
    """Drop leading «Region. » segments (one or more) from a «. »-delimited
    nominal, keeping from the first non-region segment onward."""
    if ". " not in s:
        return s
    parts = s.split(". ")
    i = 0
    while i < len(parts) - 1 and parts[i].strip() in _REGION_PREFIXES:
        i += 1
    return ". ".join(parts[i:])


def _normalise_dor(s: str) -> str:
    """Unify «d'or» spellings: curly/straight apostrophe, stray space, and a
    missing space before «d'or» («Frederikd'or» → «frederik d'or»)."""
    s = s.replace("’", "'").replace("`", "'")
    s = re.sub(r"d'\s+or\b", "d'or", s)          # «d' or» → «d'or»
    s = re.sub(r"([a-zäöü])d'or\b", r"\1 d'or", s)  # «frederikd'or» → «frederik d'or»
    return s


def _preprocess(s: str) -> str:
    """Format-noise normalisation applied before the synonym table."""
    # Separate a mixed-number quantity from a following vulgar fraction so
    # «1½» → «1 ½» → «1 1/2» (not the garbled «11/2»). Covers EVERY unicode
    # fraction, any whole part («2½», «1¼», «1¾», …). The space lets the
    # leading-«1 » strip below correctly skip a «1 1/2» mixed number.
    s = re.sub(r"(?<=\d)(?=[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])", " ", s)
    for u, a in _UNICODE_FRACTIONS.items():
        s = s.replace(u, a)
    s = _normalise_dor(s)
    s = re.sub(r"\s*\([^)]*\)", "", s)   # drop parenthetical glosses «X (Y)» → «X»
    s = re.sub(r"\s+", " ", s).strip()
    s = _strip_region_prefixes(s)
    for d, a in _DIACRITIC_FOLD.items():
        s = s.replace(d, a)
    return s


# (regex pattern, replacement) — applied in order. Compound patterns
# FIRST so single-word substitutions don't corrupt them.
NOMINAL_SYNONYMS: list[tuple[str, str]] = [
    # Multi-word compounds (must precede single-word patterns below).
    # English-plural forms «Rose Nobles» / «Specie Thalers» handled by
    # the optional `s?` in the last token of each pattern.
    (r"\brose\s+nobles?\b", "rosenobel"),
    (r"\bspecie\s+thalers?\b", "speciedaler"),
    (r"\bspecie\s+dalers?\b", "speciedaler"),
    (r"\bsilver\s+guldens?\b", "sølvgylden"),
    (r"\bsilver\s+guilders?\b", "sølvgylden"),
    # «Rhinsk Gylden» / «Rhinsk Gulden» — Danish/Norwegian per-source
    # variants of the Rhenish Gulden (18½-karat gold). Normalise the
    # spelling variant to the canonical Hede form.
    (r"\brhinsk\s+gulden\b", "rhinsk gylden"),
    # «Rigsdaler Courant» / «Courant Rigsdaler» ≡ «Kurantdaler» — the same
    # 1-courant-rigsdaler coin (Numista/NumisMaster vs Danish / project
    # form). Compound, so precede the single-word `taler` rule below.
    (r"\brigsdaler\s+courant\b", "kurantdaler"),
    (r"\bcourant\s+rigsdaler\b", "kurantdaler"),
    # Genitive-s before «D'or»: NumisMaster «Frederiks D'or» vs project
    # «Frederik D'or» (same coin). Drop ONLY the genitive s, keep the king,
    # so «Frederik» vs «Christian» D'or stay DISTINCT (different coins).
    (r"\b(frederik|christian)s\s+d'or\b", r"\1 d'or"),
    # Single-word denomination synonyms — handle English «-s» plural
    # («2 Nobles», «3 Ducats», «Thalers», «Schillings»). Danish forms
    # don't take English-style «s» pluralisation, so a trailing «s»
    # (when present) signals an English-form variant safely.
    (r"\bnobles?\b", "nobel"),
    (r"\bducats?\b", "dukat"),
    (r"\bducaten\b", "dukat"),
    (r"\bthalers?\b", "daler"),
    # «Reichsthaler» (one word) ≡ the standard «Daler»/Thaler in our scope —
    # the existing `\bthalers?\b` rule can't reach it (no word boundary
    # before the mid-word «thaler»). «Taler» is just the modern spelling of
    # period «Thaler» (CLAUDE.md §2); fold both to «daler». Qualifiers
    # (Specie-/Kurant-/Rigs-daler) are already distinct one-word forms.
    (r"\breichsthalers?\b", "daler"),
    (r"\btalers?\b", "daler"),
    # «Marck» = the period-German spelling of «Mark» (CLAUDE.md §2). Fold
    # for matching so «4 Marck» ≡ «4 Mark», «Marck Banco» ≡ «Mark Banco».
    (r"\bmarcks?\b", "mark"),
    (r"\bschillings?\b", "skilling"),
    # «Guilder» (English) ≡ «Gulden» (German) ≡ «Gylden» (Danish).
    # NumisMaster uses «Guilder» for Rhenish/Danish gold guldens; Hede
    # uses «Gylden». Both refer to the same gold-coin family — normalise
    # to «gylden» as canonical (matches Hede / project YAML).
    (r"\bguilders?\b", "gylden"),
    (r"\bguldens?\b", "gylden"),
    # --- format/spelling equivalences mined from same-bruun-id divergences ---
    # (run AFTER the thaler→daler / schilling→skilling rules above so the
    #  post-substitution forms are what these match).
    (r"\bkroner\b", "krone"),                              # Danish plural «2 Kroner»≡«2 Krone»
    (r"\breichsbank[ -]?skilling\b", "rigsbankskilling"),  # «Reichsbank Schilling»≡«Rigsbankskilling»
    (r"\bspecies[ -]?(?:thaler|taler|daler)s?\b", "speciedaler"),
    (r"\bdaler species\b", "speciedaler"),                 # «1 Thaler Species»→«speciedaler»
    (r"\bdouble daler\b", "2 daler"),                      # «Double Taler»→«2 daler»
    (r"\bguldnobel\b", "nobel"),                           # Guldnobel («gold noble») ≡ the Nobel (gold by definition)
    (r"\bguldkrone\b", "gold krone"),                      # Guldkrone≡Gold Krone
    (r"\bgold (\d+|\d+/\d+) krone\b", r"\1 gold krone"),   # «gold 2 krone»→«2 gold krone»
    # --- Danish «Dobbelt» (double) + «Specie» equivalences (nominal-
    #     discriminator synonym table, 2026-06-08) ---
    # «Dobbelt X» (Danish «double») ≡ «2 X». Folded ONLY when «dobbelt»
    # HEADS the nominal (optionally behind a spurious implicit-one «1 »),
    # so the multiplied form «4 Dobbelt Groschen» (a 4-fold coin, NOT
    # 2×) is left intact. Covers «Dobbelt dukat / speciedaler / krone /
    # skilling / hvid / royalin / mariengroschen / groschen / ungarsk
    # gylden / guldkrone», one-word («Dobbeltkrone») or spaced. The «t» is
    # optional — both «Dobbelt-» and «Dobbel-» (Dobbeldukat) spellings occur.
    (r"^(?:1\s+)?dobbelt?[- ]?", "2 "),
    # «Specie(s)-Dukat» / «Ducat Specie» = a Speciedukat (specie-grade
    # GOLD ducat), NOT a Speciedaler — guard BEFORE the bare specie fold
    # so the «specie» adjective isn't mis-read as the daler denomination.
    (r"\bspecies?[- ]?dukat\b", "speciedukat"),
    (r"\bdukat[- ]?species?\b", "speciedukat"),
    # «Specie» / «Species» (standalone) and the «Rigsdaler Specie» /
    # «Specie norsk» / «Speciemønt» forms ≡ «Speciedaler» (the bare
    # specie IS the Rigsdaler-Species / Speciedaler). Compound guards
    # FIRST so the daler isn't doubled («Rigsdaler Specie» → speciedaler,
    # NOT «rigsdaler speciedaler»). «Speciedaler» / «Speciedukat» are
    # untouched — there's no word boundary inside «specie­daler/dukat».
    (r"\brigsdaler\s+species?\b", "speciedaler"),
    (r"\bspecie[- ]?norsk\b", "speciedaler"),
    (r"\bspeciem[øo]nt\b", "speciedaler"),
    (r"\bspecies?\b", "speciedaler"),
    # --- label-variance folds that surfaced as FALSE splits when the
    #     nominal discriminator was first dry-run (2026-06-08) ---
    # Value-gloss tail «X, N <unit>» — «1 Krone, 4 Mark» / «1 Sovereign,
    # 3 Guilder»: the «, N …» is a worth-annotation, not part of the
    # denomination → strip it. MUST precede the comma-normaliser below so
    # the comma is still present to anchor on. (A bare «, <word>» without a
    # leading digit — «1 Skilling, norsk» — is a qualifier, NOT stripped.)
    (r",\s*\d[\d/]*\s+\w.*$", ""),
    (r",\s+", " "),                                  # remaining «X, qualifier» comma → space
    # «dansk» / «danske» is the DEFAULT (Danish) qualifier — «6 Skilling
    # dansk» ≡ «6 Skilling». Stripped as a standalone word. «lybsk» (Lübeck)
    # and «norsk» (Norwegian) are GENUINELY distinguishing and are kept.
    (r"\s*\bdanske?\b", ""),
    # «Halv-X» (Danish «half») ≡ «½ X»: «Halvkrone»→«1/2 krone»,
    # «Halvdaler», «Halvskilling», «Halv ørtug», «halv dukat», …. The
    # leading form CONSUMES the implicit-one («1 Halvkrone» = one half-
    # krone = ½ krone, NOT «1 1/2 krone») — otherwise it would collide with
    # the genuine mixed number «1½ Krone» after the «1½»→«1 1/2» fraction
    # split. Anchored rule first, then a general one for a non-leading
    # «halv» («½ Halvdaler»).
    (r"^(?:1\s+)?halv[ -]?", "1/2 "),
    (r"\bhalv[ -]?", "1/2 "),
    # «Lion Daler / Taler / Dalar» (EN/spelling variants) ≡ «Løvedaler»
    # (DA «lion daler»); fold to the diacritic-folded «lovedaler».
    (r"\blion\s+(?:dal[ae]r|taler)\b", "lovedaler"),
    # Genitive-s spelling typos: «Rigsbanksdaler»→«Rigsbankdaler»,
    # «Rigsbanksskilling»→«Rigsbankskilling» (explicit full words so the
    # CORRECT «Rigsbankskilling» is never corrupted).
    (r"\brigsbanksdaler\b", "rigsbankdaler"),
    (r"\brigsbanksskilling\b", "rigsbankskilling"),
    # «Courant» (EN/FR period spelling) ≡ «Kurant» (DE) — fold for matching
    # only (display keeps the period «Courant» per CLAUDE.md §2). Then the
    # spaced «Kurant Dukat» collapses to the one-word «Kurantdukat».
    (r"\bcourant\b", "kurant"),
    (r"\bkurant\s+dukat\b", "kurantdukat"),
]


@lru_cache(maxsize=None)
def normalise_nominal(nominal: str | None) -> str:
    """Lowercase the nominal, normalise dashes/whitespace, then apply
    the canonical synonym substitutions. Returns empty string on
    None / empty input.

    A leading «1 » prefix is stripped at the end — different sources
    write the same denomination with or without the implicit «one of»
    quantifier:

      Numista:  «1 Noble»     → «1 nobel» → «nobel»
      Bruun:    «Noble»                   → «nobel»
      Hede:     «Speciedaler»             → «speciedaler»
      ucoin:    «1 Speciedaler»           → «speciedaler»

    Only a bare integer «1 » followed by whitespace is stripped —
    fractions «½ Ducat» / «¼ Speciedaler» and other quantities «2 Nobles»
    stay distinct (those genuinely differ in denomination weight).
    """
    if not nominal:
        return ""
    s = str(nominal).lower().strip()
    s = s.replace("müntze", "münze")
    s = re.sub(r"[‒–—]+", "-", s)
    s = re.sub(r"\s+", " ", s)
    s = _preprocess(s)   # fractions, d'or, parenthetical glosses, region prefix, diacritics
    for pattern, replacement in NOMINAL_SYNONYMS:
        s = re.sub(pattern, replacement, s)
    # Strip leading «1 » (implicit-one quantifier). Applied AFTER synonyms
    # so «1 Rose Noble» → «1 rosenobel» → «rosenobel» works correctly.
    # `^1\s+` won't touch «1/2», «1.5», «10», «1A», «2 Nobles». The
    # negative-lookahead `(?!\d)` protects a «1 1/2» mixed number (the
    # leading «1» is the whole part, NOT the implicit-one quantifier) —
    # otherwise «1½ Daler» would collapse to «1/2 daler».
    s = re.sub(r"^1\s+(?!\d)", "", s)
    return s
