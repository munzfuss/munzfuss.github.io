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
]


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
    for pattern, replacement in NOMINAL_SYNONYMS:
        s = re.sub(pattern, replacement, s)
    # Strip leading «1 » (implicit-one quantifier). Applied AFTER synonyms
    # so «1 Rose Noble» → «1 rosenobel» → «rosenobel» works correctly.
    # `^1\s+` won't touch «1/2», «1.5», «10», «1A», «2 Nobles».
    s = re.sub(r"^1\s+", "", s)
    return s
