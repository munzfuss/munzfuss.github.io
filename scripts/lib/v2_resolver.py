"""V2 build-assembly resolvers — pick the right per-location field value
for coins that carry V2's dict-form indirection.

Per V2_PIPELINE.md §4-§5:

  - `coin.phase: str | dict[str, str]`
    Scalar applies everywhere. Dict `{loc_id: phase_id}` overrides per
    display page. Used when the same coin sits in different local
    periodisations across the pages of a multi-consumer entity file.

  - `coin.catalog.km: str | dict[str, str] | list[...]`
    Scalar / list shapes pre-V2 (unchanged). Dict form (V2) names KM
    register explicitly — `{'dk': '722', 'sh': '155'}` — so the same
    Krause-volume-twin lives in ONE curated entry.

These functions live in their own module (not `compute.py`) because the
V1 build path doesn't need them — V1 coins always have scalar phase and
str/list-form km. Phase 4 assembly imports from here only when reading
V2 yamls.

A separate `resolve_mint_for_location()` is deferred per V2_PIPELINE.md
§3.5 — current state renders the same mint list on every consumer page.
"""

from __future__ import annotations


def resolve_phase_for_location(phase, loc_id: str, coin_id: str | None = None) -> str:
    """Pick the phase id matching `loc_id` from a scalar-or-dict phase field.

    Scalar phase → returns as-is.
    Dict phase → returns `phase[loc_id]`, raising ValueError if the key is
                 missing (V2 audit catches this in Phase 7).
    """
    if isinstance(phase, dict):
        if loc_id not in phase:
            raise ValueError(
                f"coin {coin_id!r}: phase dict {phase!r} has no entry for "
                f"location {loc_id!r}"
            )
        return phase[loc_id]
    if not isinstance(phase, str):
        raise ValueError(
            f"coin {coin_id!r}: phase must be str or dict, got {type(phase).__name__}"
        )
    return phase


def resolve_km_for_location(km, km_register: str, coin_id: str | None = None):
    """Pick the KM value matching the current location's `km_register`.

    Scalar / list shapes → returned as-is (legacy V1 path, no register
        resolution; the existing KMRef machinery handles cross-volume
        cases for list-form).
    Dict shape (V2) → case-insensitive lookup by register key. Returns
        the resolved scalar KM; missing key raises ValueError.
    """
    if isinstance(km, dict):
        key_lc = (km_register or "").lower()
        for k, v in km.items():
            if k.lower() == key_lc:
                return v
        raise ValueError(
            f"coin {coin_id!r}: km dict {km!r} has no entry for register "
            f"{km_register!r}"
        )
    return km


# Migration breadcrumb keys produced by `migrate_curated_to_v2.py`. The
# Phase 4 build assembly strips these from each coin dict before
# instantiating the pydantic Coin model.
V2_MIGRATION_BREADCRUMB_KEYS = (
    "v1_home_location",
    "_migration_note",
    "_migration_dup_origin_id",
)


def strip_v2_breadcrumbs(coin: dict) -> dict:
    """Return a shallow copy of `coin` with the V2 migration breadcrumb
    keys removed (so the dict passes `Coin._StrictBase` extra='forbid').
    Operates non-destructively on the input dict."""
    out = {k: v for k, v in coin.items() if k not in V2_MIGRATION_BREADCRUMB_KEYS}
    return out
