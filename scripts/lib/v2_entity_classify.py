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

# Mint canonicalisation is centralised in `mint_registry` (single source
# of truth for both `_canonicalise_mint` in v2_seed_writer AND entity
# lookup here). See `mint_registry.py` module docstring for the
# rationale + the 2026-05-26 ASCII-alias regression that motivated
# unifying the previously-split tables.
from lib.mint_registry import ALIAS_TO_CANON as _ALIAS_TO_CANON  # noqa: E402
from lib.mint_registry import CANON_TO_ENTITY as _MINT_TO_ENTITY  # noqa: E402
from lib.mint_registry import entity_for_canon_year as _entity_for_canon_year  # noqa: E402
# Issuer-string classifier (Numista et al. — sources that label coins by
# emitting jurisdiction rather than by mint). Lives in mint_registry for
# co-location with the mint table; re-exported here as the public
# classifier surface paralleling `classify_mint_to_entity`.
from lib.mint_registry import classify_issuer_to_entity  # noqa: E402,F401
from lib.mint_registry import is_known_issuer  # noqa: E402,F401


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _strip_mintmark_suffix(mint: str) -> str:
    """`Altona (FK VS)` → `Altona`; `Kopenhagen (683.1 M)` → `Kopenhagen`."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", mint).strip()


def _strip_mint_word_suffix(mint: str) -> str:
    """`Altona Mint` → `Altona`; `Glückstadt Mint` → `Glückstadt`.

    Bruun's catalogue body excerpts emit the mint name with a trailing
    « Mint» word (English-language auction convention). The cache parser
    preserves this verbatim in the lot's `mint` field, so when
    `parse_mint(lot)` falls through to the cache value as fallback the
    string carries the suffix. Classifier needs to strip it before
    alias lookup, otherwise «Altona Mint» misses the «altona» alias.
    """
    return re.sub(r"\s+Mint\s*$", "", mint, flags=re.IGNORECASE).strip()


def _normalise_one_mint(raw: str) -> str | None:
    """Returns the canonical mint key (e.g. `kopenhagen`) or None when no
    alias matches. Strips any parenthesised mintmaster suffix and any
    trailing « Mint» word first."""
    stripped = _strip_mintmark_suffix(raw)
    stripped = _strip_mint_word_suffix(stripped)
    # Direct lookup against alias table (case-insensitive).
    return _ALIAS_TO_CANON.get(stripped.lower())


def classify_mint_to_entity(mint, year: int | None = None
                              ) -> str | list[str] | None:
    """Map a coin's `mint` field (scalar, list, or None) + optional
    `year` to its political entity tag(s).

      * None / unknown / unparseable → returns None (caller routes to
        `_unclassified`).
      * Scalar → str.
      * Multi-mint resolving to ONE entity → str (same entity).
      * Multi-mint resolving to ≥2 distinct entities → sorted list[str].

    The list-form ordering matches V2_PIPELINE.md §3.10 (alphabetical),
    so the alphabetically-first element is the home-file entity.

    `year` argument is OPT-IN. When provided, the mint registry's
    `year_overrides` rules are consulted to pick the era-correct entity
    (per locked 2026-05-26 convention: `year_to` exclusive). Mints
    without overrides ignore the year. See
    `docs/research/mint_year_transitions.md` for currently-modeled
    transitions (Altona 1640 only as of MVP-D).
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
            ent = _entity_for_canon_year(canon, year)
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
