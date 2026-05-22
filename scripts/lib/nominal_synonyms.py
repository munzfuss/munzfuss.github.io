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
    # Single-word denomination synonyms — handle English «-s» plural
    # («2 Nobles», «3 Ducats», «Thalers», «Schillings»). Danish forms
    # don't take English-style «s» pluralisation, so a trailing «s»
    # (when present) signals an English-form variant safely.
    (r"\bnobles?\b", "nobel"),
    (r"\bducats?\b", "dukat"),
    (r"\bducaten\b", "dukat"),
    (r"\bthalers?\b", "daler"),
    (r"\bschillings?\b", "skilling"),
]


def normalise_nominal(nominal: str | None) -> str:
    """Lowercase the nominal, normalise dashes/whitespace, then apply
    the canonical synonym substitutions. Returns empty string on
    None / empty input.
    """
    if not nominal:
        return ""
    s = str(nominal).lower().strip()
    s = s.replace("müntze", "münze")
    s = re.sub(r"[‒–—]+", "-", s)
    s = re.sub(r"\s+", " ", s)
    for pattern, replacement in NOMINAL_SYNONYMS:
        s = re.sub(pattern, replacement, s)
    return s
