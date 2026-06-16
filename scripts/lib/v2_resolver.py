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
    Dict shape (V2) → case-insensitive lookup by register key. Returns the
        resolved KM. When the page's register key is ABSENT, the coin's KM
        exists only in another Krause volume (a legitimate single-register
        coin shown on the other consumer page — e.g. an SH-only KM rendered on
        the Denmark page when `denmark` consumes a royal_holstein coin); fall
        back to the union of the available values rather than crashing.
    """
    if isinstance(km, dict):
        key_lc = (km_register or "").lower()
        for k, v in km.items():
            if k.lower() == key_lc:
                return v
        # Missing register → union of available values (graceful; the coin
        # has a catalogue number, just not in this register).
        vals: list = []
        for v in km.values():
            for x in (v if isinstance(v, list) else [v]):
                if x not in (None, "", []) and x not in vals:
                    vals.append(x)
        if not vals:
            return None
        return vals[0] if len(vals) == 1 else vals
    return km


# Migration breadcrumb keys produced by `bootstrap_v2_final_from_v1.py` and
# `seed_v2_regroup.py`. The Phase 4 build assembly strips these from
# each coin dict before instantiating the pydantic Coin model.
V2_MIGRATION_BREADCRUMB_KEYS = (
    "v1_home_location",       # bootstrap_v2_final_from_v1.py — curated coin's source location yaml
    "v1_seed_location",       # seed_v2_regroup.py — seed coin's source V1 location-yaml
    "_migration_note",
    "_migration_dup_origin_id",
)


def ruamel_to_plain(c):
    """ruamel.yaml round-trip types → plain Python equivalents (recursive).
    Handles CommentedMap / CommentedSeq / Scalar* wrappers across str /
    int / float / bool. Used by all V2 maintenance scripts after
    `seed_merge.merge_seed()` returns CommentedMap entries that pyyaml's
    dumper can't serialise without `!!python/object/...` tag pollution.
    """
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    if isinstance(c, CommentedMap):
        return {str(k): ruamel_to_plain(v) for k, v in c.items()}
    if isinstance(c, CommentedSeq):
        return [ruamel_to_plain(v) for v in c]
    # ruamel-wrapped scalars (ScalarString / ScalarFloat / ScalarInt /
    # ScalarBoolean) inherit from str / float / int / bool respectively.
    # Detect by module name + downcast to primitive.
    if (hasattr(c, "__class__")
            and getattr(c.__class__, "__module__", "").startswith("ruamel.")):
        if isinstance(c, bool):
            return bool(c)
        if isinstance(c, int):
            return int(c)
        if isinstance(c, float):
            return float(c)
        if isinstance(c, str):
            return str(c)
    if isinstance(c, dict):
        return {k: ruamel_to_plain(v) for k, v in c.items()}
    if isinstance(c, list):
        return [ruamel_to_plain(v) for v in c]
    return c


def strip_v2_breadcrumbs(coin: dict) -> dict:
    """Return a shallow copy of `coin` with the V2 migration breadcrumb
    keys removed (so the dict passes `Coin._StrictBase` extra='forbid').
    Operates non-destructively on the input dict."""
    out = {k: v for k, v in coin.items() if k not in V2_MIGRATION_BREADCRUMB_KEYS}
    return out
