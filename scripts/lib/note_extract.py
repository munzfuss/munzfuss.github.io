"""Shared helper for Phase-1 source-note population.

Each per-source seed builder (numismaster, numista, ikmk, kmk, hede, …)
lifts its richest descriptive cache field into a coin-level
`_source_note` field so the Phase-2 note-selector can later choose the
best note across a coin's merged source-members (per the curator rule:
an existing curator `note` > 5 words wins, else the longest source note
wins) and translate it.

`_source_note` is deliberately underscore-prefixed: per the project's
seed convention (`v2_seed_writer`) an underscore field survives into the
`data/v2/seed/<src>/<entity>.yml` YAML for human review but is stripped
before the strict `Coin` schema at final/render time. That keeps Phase 1
(seed population) fully decoupled from the schema / render-fallback /
translation work that Phase 2 will add — nothing new reaches the
rendered page until the selector promotes a chosen, translated note into
the real `note` field.

Shape: `_source_note = {<lang>: <cleaned text>}` where `<lang>` is the
source's own language (`da` / `de` / `en`), NOT necessarily a currently
render-supported slot. The language key records the source language so
Phase-2 translation knows what it is looking at.
"""

from __future__ import annotations

import re

# Auction / marketplace boilerplate that must never enter a reader note
# (§7a: prices are project-wide out of scope; §2a: no sensationalism).
# Bruun is excluded from Phase 1 entirely, but keep these guards so the
# helper is safe to reuse on any source.
_PRICE_RE = re.compile(
    r"(?:€|£|\$|USD|EUR|DKK|SEK)\s?[\d.,]+(?:\s?[-–—]\s?(?:€|£|\$)?[\d.,]+)?",
    re.IGNORECASE,
)
_BOILERPLATE_RE = re.compile(
    r"(?:From the L\.\s?E\.\s?Bruun Collection|Photo Enlarged|Estimate[:\s]|"
    r"Starting bid|Hammer price|ex[.:]\s|Provenance:)",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_note_text(raw: str | None, max_chars: int = 600) -> str | None:
    """Normalise a raw descriptive cache string into a reader-safe note.

    Strips HTML tags, auction prices and marketplace boilerplate,
    collapses whitespace, and truncates at a word boundary to
    `max_chars`. Returns ``None`` when nothing usable remains (so the
    caller can simply skip the field).

    The text is NOT translated and NOT register-polished here — that is
    Phase-2 work. This only guarantees the stored candidate is free of
    markup and price data.
    """
    if not raw:
        return None
    txt = str(raw)
    txt = _TAG_RE.sub(" ", txt)
    txt = _PRICE_RE.sub("", txt)
    txt = _BOILERPLATE_RE.sub("", txt)
    txt = _WS_RE.sub(" ", txt).strip(" ;·—–-,.")
    txt = txt.strip()
    if not txt:
        return None
    if len(txt) > max_chars:
        cut = txt[:max_chars]
        # back up to the last word boundary so we never split a token
        sp = cut.rfind(" ")
        if sp > max_chars * 0.6:
            cut = cut[:sp]
        txt = cut.rstrip(" ;·—–-,.") + "…"
    # Guard: a single short token (e.g. a bare metal code "AR", a nominal
    # restatement) is not a note — leave it to the structured fields.
    if len(txt.split()) < 2:
        return None
    return txt


def source_note(raw: str | None, lang: str, max_chars: int = 600) -> dict | None:
    """Return a `{lang: cleaned}` `_source_note` dict, or None if empty."""
    cleaned = clean_note_text(raw, max_chars=max_chars)
    if cleaned is None:
        return None
    return {lang: cleaned}
