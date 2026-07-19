"""
Layer A → B: compute derived fields for each coin.

Pure functions over the input data. No template concerns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Coin, Fuss, Location, FieldValue
from .catalog_codes import normalise_numeric_index, _NUMERIC_INDEX_FIELDS

import functools


@functools.lru_cache(maxsize=1)
def _fin_authority_map() -> dict[str, int]:
    """Load the fineness-source authority ranking from
    `data/shared/source_authority.yml` (curator-editable). Higher = more
    authoritative; used ONLY to pick which fineness a weight-only source
    borrows (never rewrites a source's own reading).

    Missing / unreadable / empty file → {} so every source scores 0 (tie) and
    the old first-listed fallback behaviour is reproduced exactly (no regression
    for callers without the data file, e.g. isolated unit tests)."""
    import pathlib, yaml
    try:
        p = pathlib.Path(__file__).resolve().parents[2] / "data/shared/source_authority.yml"
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return {str(k).lower(): int(v)
                for k, v in (raw.get("fineness_authority") or {}).items()}
    except Exception:
        return {}


def normalise_field(v) -> list[tuple[float, str | None]]:
    """Normalise a measurement field (scalar | list[FieldValue] | None)
    into a uniform list of (value, source) pairs. Scalar form means
    a single reading with no explicit source label; list form carries
    one entry per source.

    Returns: [] for None, [(value, None)] for scalar, [(v.value, v.source), ...] for list.
    """
    if v is None:
        return []
    if isinstance(v, (int, float)):
        return [(float(v), None)]
    if isinstance(v, list):
        # Skip readings flagged display:false (§9a weight-specimen
        # thinning hides over-collected single-resource intermediates;
        # the data stays in YAML but is excluded from the rendered
        # column AND from the derived Feingewicht).
        return [
            (fv.value, fv.source)
            for fv in v
            if getattr(fv, "display", True) is not False
        ]
    # FieldValue object (shouldn't happen at this layer but defensive)
    if hasattr(v, "value"):
        if getattr(v, "display", True) is False:
            return []
        return [(v.value, getattr(v, "source", None))]
    return []


def primary_value(field) -> float | None:
    """The first value in a measurement field. For scalar form it's the
    only value; for list form it's the first list entry (treated as the
    primary reading). None if the field is empty/None."""
    pairs = normalise_field(field)
    return pairs[0][0] if pairs else None


@dataclass
class DisplayGroup:
    """A renderable group of source readings that all round to the same
    display value. Used to collapse `[(14.447, "Hede"), (14.45, "ucoin")]`
    (which both display as "14,45" at 2 decimals) into ONE rendered
    span with a combined tooltip — and, when this is the ONLY group
    in a field, drop the alt-source styling entirely (single-value
    consensus, just plain text).

    `delta_pct` is populated only for derived-value groups (delta,
    implied_fuss) and carries the percent-deviation context that the
    template needs for colour-class selection (Δ badges) and for the
    > 2 % gate that filters informative implied-Fuß lines.
    """
    value: float                # canonical numeric value (first member)
    sources: list[str]          # ordered, deduped source labels
    is_unanimous: bool = False  # True when this is the SOLE group in its field
    delta_pct: float | None = None  # context for derived-value groups
    display_decimals: int | None = None  # decimals to render this group's value
                                          # at — set when the source reading
                                          # carries more precision than the field
                                          # default (e.g. 3.249 g at weight
                                          # precision 2) or when distinct groups
                                          # would otherwise collapse to identical
                                          # text (None → use template-default
                                          # precision)
    anchor_key: str | None = None  # GROUNDWORK (not yet rendered): a stable
                                   # per-specimen join key = the WEIGHT source(s)
                                   # this reading is anchored to. For the weight
                                   # column it is the weight source itself; for
                                   # the DERIVED columns (weight_fein, delta) it
                                   # is the SAME weight source the value was
                                   # computed from — NOT the combined
                                   # «weight×fineness» derived_source label — so
                                   # a future renderer can align weight ↔ chiста
                                   # ↔ Δ into correlated sub-rows by matching
                                   # anchor_key instead of relying on list
                                   # position. «|»-joined + sorted when a group
                                   # merges several deduped readings.


def _natural_decimals(value: float, lo: int, hi: int) -> int:
    """Smallest decimals `d` in [lo, hi] for which `round(value, d) == value`
    (within float tolerance); `hi` if none qualifies.

    Lets a source reading display at its OWN precision instead of being
    rounded down to the field default — e.g. a Hede weight of 3.249 g returns
    3 (so it renders «3.249», not «3.25»), while 3.16 g returns 2. §3 «store /
    show the source's literal value, never round»."""
    for d in range(lo, hi + 1):
        if abs(round(value, d) - value) < 1e-9:
            return d
    return hi


def make_display_groups(
    pairs: list[tuple[float, str | None]],
    precision: int,
) -> list[DisplayGroup]:
    """Group (value, source) pairs by their semantically-distinct value.

    Two-level grouping precision: source values are grouped at the
    FINER precision `precision + 2` so cross-source attestations that
    differ at the source-publish level (e.g. Hede 2,386 g vs
    NumisMaster 2,39 g — both round to 2.39 at 2 decimals but are
    distinct readings) get separate groups. The `precision` argument
    drives downstream DISPLAY rounding; grouping is finer so
    distinguishable readings aren't collapsed into one tooltip.

    When all pairs collapse to the same finer-precision key, the
    single returned group has `is_unanimous=True` and the renderer
    can drop tooltip+styling (consensus = plain text).

    Each DisplayGroup carries the canonical raw value (first member);
    the template applies its own `decimals=<precision>` formatting.
    When two groups display the same rounded value (e.g. 2.39 and
    2.39 — both ≤2-decimal projections of 2.386 and 2.390), the
    template's adaptive-decimals helper can still distinguish via
    tooltip + alt-source styling.
    """
    if not pairs:
        return []
    # Finer-precision key so distinguishable source readings don't
    # collapse: weight (precision=2) → grouped at 4 decimals;
    # fineness (precision=3) → grouped at 5; diameter (precision=1)
    # → grouped at 3.
    group_precision = precision + 2
    # Members carry (value, source, anchor). `pairs` may be 2-tuples
    # (value, source) — then the anchor defaults to the reading's own
    # source — or 3-tuples (value, source, anchor) where the caller
    # supplies a distinct join anchor (the DERIVED columns pass the
    # WEIGHT source here so weight ↔ derived columns share one key).
    groups: dict[float, list[tuple[float, str | None, str | None]]] = {}
    order: list[float] = []
    for p in pairs:
        v, src = p[0], p[1]
        anchor = p[2] if len(p) > 2 else src
        if v is None:
            continue
        key = round(v, group_precision)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((v, src, anchor))

    is_unanimous = len(order) == 1
    out: list[DisplayGroup] = []
    for key in order:
        members = groups[key]
        canonical = members[0][0]
        srcs: list[str] = []
        anchors: list[str] = []
        for _, src, anch in members:
            if src:
                for tok in src.split("\n"):
                    tok = tok.strip()
                    if tok and tok not in srcs:
                        srcs.append(tok)
            if anch:
                for tok in anch.split("\n"):
                    tok = tok.strip()
                    if tok and tok not in anchors:
                        anchors.append(tok)
        out.append(DisplayGroup(value=canonical, sources=srcs,
                                is_unanimous=is_unanimous,
                                anchor_key=("|".join(sorted(anchors)) or None)))

    # Display-decimals (§3 — never round a source reading below its own
    # precision). Show every value at the MAX natural precision across the
    # groups: `fmt_num` strips trailing zeros per value, so a uniform
    # `decimals = needed` renders each source value exactly (3.16 → «3.16»,
    # 3.249 → «3.249») without padding noise, and floors at the field
    # default `precision`. This also subsumes the old anti-collapse rule:
    # two readings that round to identical text at `precision` (e.g. 2.386
    # and 2.390 both → «2.39» at decimals=2) must differ in a sub-`precision`
    # digit, so at least one has a higher natural precision → `needed` rises
    # and the groups stay visually distinct. Applies to the unanimous case
    # too (a lone 3.249 reading no longer rounds to 3.25).
    needed = max((_natural_decimals(g.value, precision, group_precision)
                  for g in out), default=precision)
    if needed > precision:
        for g in out:
            g.display_decimals = needed
    return out


def _seg_rle(rows: list[dict], field: str, ndigits: int, base_dec: int = 0,
             src_field: str = "sources", group_field: str | None = None) -> list[dict]:
    """Run-length-encode `rows` by the rounded value of `field`.

    Consecutive rows whose `field` value rounds equal collapse into ONE
    segment `{value, span, sources, delta_pct, decimals}` — the segment then
    renders as a single cell that visually spans `span` sub-rows. Sources are
    unioned across the merged rows (read from `src_field` — повна uses the raw
    WEIGHT source, while the DERIVED columns чиста/Δ read a «weight × fineness»
    derived-source label so their tooltip shows what each value was computed
    from); delta_pct is carried from the first contributing row (used only by
    the Δ column for its colour class); `decimals` is each value's own natural
    precision floored at `base_dec` (§3 — never round below the source's).

    `group_field` (optional) confines merges to WITHIN a group: two consecutive
    rows merge only when both their `field` value AND their `group_field` value
    are equal. повна / чиста / Δ pass group_field="fineness" so a value is NEVER
    merged across a проба boundary — two specimens that happen to share a weight
    but sit under different fineness readings (e.g. 3.49 g at .986 and 3.49 g at
    .972) each keep their own sub-row instead of collapsing into one span.
    """
    segs: list[dict] = []
    for r in rows:
        v = r.get(field)
        key = round(v, ndigits) if v is not None else None
        gkey = None
        if group_field is not None:
            gv = r.get(group_field)
            gkey = round(gv, 5) if gv is not None else None
        if segs and segs[-1]["_key"] == key and segs[-1]["_gkey"] == gkey:
            segs[-1]["span"] += 1
            for s in r.get(src_field) or []:
                if s and s not in segs[-1]["sources"]:
                    segs[-1]["sources"].append(s)
            if segs[-1].get("delta_pct") is None and r.get("delta_pct") is not None:
                segs[-1]["delta_pct"] = r.get("delta_pct")
        else:
            dec = _natural_decimals(v, base_dec, base_dec + 3) if v is not None else base_dec
            segs.append({"_key": key, "_gkey": gkey, "value": v, "span": 1,
                         "sources": [s for s in (r.get(src_field) or []) if s],
                         "delta_pct": r.get("delta_pct"), "decimals": dec})
    return segs


def _build_measurement_rows(cc, fineness_pairs) -> None:
    """Populate cc.msr_* — per-specimen measurement sub-rows + per-column
    run-length segments. Only meaningful (and rendered) when msr_n > 1.

    Diameter is deliberately NOT a sub-row axis: specimen-to-specimen
    diameter spread is wear / handling noise, not a standard difference, so
    it neither splits sub-rows nor renders as a merged sub-column. It keeps
    its own deduped column via `diameter_groups`.

    The проба (fineness) column IS aligned with the sub-rows: each row's
    fineness is derived from its own fein / rough and SNAPPED to the nearest
    canonical reading in fineness_pairs, so the проба value on a row matches the
    fineness that produced that row's чиста. A coin with two fineness readings
    (e.g. .750 hede on three specimens, .764 galster on one) shows .750 spanning
    the first three sub-rows and .764 on the fourth — exactly aligned with чиста.
    Per-value source attribution comes from fineness_groups (the fineness field's
    OWN sources), NEVER the per-specimen weight sources."""
    pf = fineness_pairs[0][0] if fineness_pairs else None
    # Canonical fineness readings (deduped values) to snap each row's derived
    # fineness onto — keeps the displayed value clean (.750, not .74999 float
    # noise) and maps it to the right catalogue reading.
    _fin_vals = sorted({round(v, 5) for v, _ in fineness_pairs if v is not None})

    def _rowfin(rough, fine, fallback):
        if rough and fine and rough > 0 and _fin_vals:
            raw = fine / rough
            return min(_fin_vals, key=lambda fv: abs(fv - raw))
        return fallback

    # Per-row source attribution differs by column: повна (rough) → the raw
    # WEIGHT source; чиста / Δ → the «weight × fineness» DERIVED-source label
    # (so their tooltip shows what the value was computed from, not just the
    # weight source). проба sources are overridden below from fineness_groups.
    rows: list[dict] = [{
        "rough": cc.primary_weight_rough_g, "fine": cc.weight_fein_g,
        "delta": cc.delta_g, "delta_pct": cc.delta_pct,
        "fineness": _rowfin(cc.primary_weight_rough_g, cc.weight_fein_g, pf),
        "sources": [cc.primary_weight_source] if cc.primary_weight_source else [],
        "fine_src": [cc.primary_derived_source] if cc.primary_derived_source else [],
        "delta_src": [cc.primary_derived_source] if cc.primary_derived_source else [],
    }]
    for ca in cc.alts:
        r_rough = ca.weight_rough_g if ca.weight_rough_g is not None else cc.primary_weight_rough_g
        rows.append({
            "rough": r_rough, "fine": ca.weight_fein_g,
            "delta": ca.delta_g, "delta_pct": ca.delta_pct,
            "fineness": _rowfin(r_rough, ca.weight_fein_g,
                                ca.fineness if ca.fineness is not None else pf),
            "sources": [ca.source] if ca.source else [],
            "fine_src": [ca.derived_source] if ca.derived_source else [],
            "delta_src": [ca.derived_source] if ca.derived_source else [],
        })
    # Dedup TRUE duplicates (identical across all four fields) — union every
    # per-column source list so a merged sub-row keeps all its provenance.
    deduped: list[dict] = []
    for r in rows:
        k = tuple(round(r[f], 5) if r[f] is not None else None
                  for f in ("rough", "fine", "delta", "fineness"))
        for d in deduped:
            if d["_k"] == k:
                for sf in ("sources", "fine_src", "delta_src"):
                    for s in r.get(sf) or []:
                        if s not in d[sf]:
                            d[sf].append(s)
                break
        else:
            r["_k"] = k
            deduped.append(r)
    # Sort by fineness FIRST, then weight — проба is the primary grouping axis
    # (curator: «сортування проб пріоритетніше за сортування ваг»). Rows sharing
    # a fineness stay CONTIGUOUS so the проба run-length merges into ONE spanning
    # cell even when that fineness sits on a lighter specimen than another
    # reading — e.g. c3h2: .986 on both 6.981 and 6.98, .968 on a 6.981 that
    # would otherwise split the two .986 rows apart. Higher fineness first;
    # heaviest weight first within a fineness group.
    deduped.sort(key=lambda r: (-(r["fineness"] or 0.0), -(r["rough"] or 0.0)))
    cc.msr_n = len(deduped)
    # повна / чиста / Δ merge only WITHIN a проба group (group_field="fineness")
    # — a weight shared by two specimens under different fineness readings is
    # NOT collapsed into one span. проба itself IS the grouping axis (no
    # group_field) and keeps its spanning merge.
    cc.msr_weight_segs   = _seg_rle(deduped, "rough", 4, base_dec=2, group_field="fineness")
    cc.msr_fein_segs     = _seg_rle(deduped, "fine", 7, base_dec=5, src_field="fine_src", group_field="fineness")
    cc.msr_delta_segs    = _seg_rle(deduped, "delta", 7, base_dec=5, src_field="delta_src", group_field="fineness")
    cc.msr_fineness_segs = _seg_rle(deduped, "fineness", 5, base_dec=3)
    # проба source attribution: the fineness's OWN sources (fineness_groups),
    # keyed by value — NEVER the per-specimen weight sources. A single reading
    # (curator-inferred or single-sourced) still carries its source so the
    # tooltip shows provenance; the template colours it normal vs orange by the
    # NUMBER of distinct fineness segments (1 → normal .fin-src, ≥2 → .fin-alt).
    fin_src = {round(g.value, 5): list(g.sources) for g in cc.fineness_groups}
    for seg in cc.msr_fineness_segs:
        v = seg.get("value")
        seg["sources"] = fin_src.get(round(v, 5), []) if v is not None else []


@dataclass
class ComputedAlt:
    """Per-source alternative measurement set with derived values
    computed coherently from THAT source's reading. Inputs come from a
    matching list-form entry on the coin; missing fields fall
    back to the primary so derived calculations always have a complete
    (weight, fineness) pair from the same logical reading.

    Display fields (`weight_rough_g`, `fineness`, `diameter_mm`) only
    carry a value when the alt explicitly differs from primary — so
    the template can decide whether to render an alt annotation in
    each cell."""
    source: str = ""
    # Display values — non-None only when alt explicitly overrides primary
    weight_rough_g: float | None = None
    fineness: float | None = None
    diameter_mm: float | None = None
    # Derived (always computed when inputs allow)
    weight_fein_g: float | None = None
    delta_g: float | None = None
    delta_pct: float | None = None
    within_remedium: bool | None = None
    implied_fuss: float | None = None
    # Tooltip label naming BOTH sources used for the derived Feingewicht
    # (weight source + the fineness source actually used, own or fallback).
    derived_source: str | None = None


@dataclass
class ComputedCoin:
    """A coin with its computed numerical fields added."""
    raw: Coin                              # original input
    fuss: Fuss                           # resolved fuss reference
    # Primary measurement readings — first entry of each list-form field
    # (or the bare scalar). Always available as a float for templates that
    # don't know about list-form. Source is None when scalar form is used.
    primary_weight_rough_g: float | None = None
    primary_weight_source: str | None = None
    primary_fineness: float | None = None
    primary_fineness_source: str | None = None
    primary_diameter_mm: float | None = None
    primary_diameter_source: str | None = None
    # Source label for derived weight_fein_g / delta. When the same source
    # supplied both primary weight and primary fineness, it's that source's
    # name. When they differ, it's a combined "weight from X, fineness from
    # Y" label so the rendered tooltip still shows full provenance.
    primary_derived_source: str | None = None
    weight_fein_g: float | None = None     # primary rough × primary fineness
    soll_fein_g: float | None = None       # from fuss.fractions[fraction]
    soll_rau_g: float | None = None        # for gold
    delta_g: float | None = None           # actual − target
    delta_pct: float | None = None         # delta / target × 100
    within_remedium: bool | None = None    # |delta_pct| ≤ 1.0
    implied_fuss: float | None = None     # actual Münzfuß back-computed from metal content
    has_manual_implied: bool = False      # true if fuss_refs already documents an "Ist-Wert" note
    # Catalog refs grouped by prefix; each group is (label, [values], tooltip).
    # Rendered in template, one group per line: "KM# 77, 77.1, 77.2".
    # `tooltip` is set on register-qualified KM prefixes («KM-DK#»,
    # «KM-SH#») to explain which Krause register volume the number
    # belongs to. None for bare prefixes.
    catalog_groups: list[tuple[str, list[str], str | None]] = field(default_factory=list)
    # True if any input (weight_rough or fineness) is unverified, in which case
    # ALL derived values (weight_fein, delta, implied_fuss) inherit the (?)
    # marker — they sit on a non-primary base.
    derived_unverified: bool = False
    # Per-source alternative measurements with derived values computed
    # for each (Feingewicht, delta) — preserves provenance when sources
    # disagree on weight/fineness/diameter. Populated from non-primary
    # entries in list-form measurement fields.
    alts: list[ComputedAlt] = field(default_factory=list)
    # Display-level grouping of all readings (primary + alts) by rounded
    # value. Each group → one rendered span: when sources agree on value,
    # they collapse into one entry with combined tooltip; when ALL
    # sources agree (single group), template renders plain text without
    # alt-source styling. See make_display_groups() above.
    weight_groups: list[DisplayGroup] = field(default_factory=list)
    fineness_groups: list[DisplayGroup] = field(default_factory=list)
    diameter_groups: list[DisplayGroup] = field(default_factory=list)
    weight_fein_groups: list[DisplayGroup] = field(default_factory=list)
    # Per-source Δ values, collapsed by rounded delta_g. Each group carries
    # delta_pct on it (computed from the canonical value ÷ soll_fein) so
    # the template can pick the colour class without re-deriving.
    delta_groups: list[DisplayGroup] = field(default_factory=list)
    # Per-source implied Fuß values, filtered to entries where |delta_pct|
    # > 2 (small deviations make the implied Fuß ≈ declared Fuß and add no
    # information). Group key = rounded implied_fuss; sources combined.
    # Empty when no source's reading meaningfully deviates from the standard.
    implied_fuss_groups: list[DisplayGroup] = field(default_factory=list)
    # --- Measurement sub-rows (rendered only when msr_n > 1) ---
    # One row per distinct specimen/reading (primary + alts, deduped by the
    # full rough/fein/delta/fineness/diameter tuple). Each per-column list is
    # run-length-encoded, so consecutive rows with an equal value merge into
    # ONE segment that visually spans `span` sub-rows (the «sub-column» look —
    # e.g. one проба value for three weight rows). Rows are sorted to cluster
    # equal fineness so the vertical merges come out contiguous. Each segment
    # dict: {value, span, sources, delta_pct, decimals}. Diameter is NOT a
    # sub-row axis (see _build_measurement_rows) — it keeps diameter_groups.
    msr_n: int = 0
    msr_weight_segs: list[dict] = field(default_factory=list)
    msr_fein_segs: list[dict] = field(default_factory=list)
    msr_delta_segs: list[dict] = field(default_factory=list)
    msr_fineness_segs: list[dict] = field(default_factory=list)

    def __getattr__(self, name):
        """Proxy to raw for convenience."""
        return getattr(self.raw, name)


# ---------------------------------------------------------------------
# Catalog grouping — collects named fields + parses cat.others into a
# stable, prefix-grouped, deduplicated list. Used by the renderer to lay
# out the «Каталог» column with one prefix per row.
# ---------------------------------------------------------------------

import re  # noqa: E402

# Display label for each named catalog field. Ordering doesn't matter
# for output (the render order is driven by `_PREFIX_PRIORITY` below).
# The field must exist on the `CatalogRefs` schema in
# `scripts/lib/schema.py` — adding an entry here without the schema
# field is a no-op (the lookup returns None).
_NAMED_FIELDS: list[tuple[str, str]] = [
    ("km", "KM"),
    ("hede", "Hede"),
    ("sieg", "Sieg"),
    ("schou", "Schou"),
    ("lange", "Lange"),
    ("fr", "Fr"),
    ("dav", "Dav"),
    # Bruun catalogue references — both schema field names map to the same
    # «Bruun#» display prefix:
    #   * `bruun_collection_id` — canonical V2 schema field (populated by
    #     `build_bruun_denmark_seed.py`); the Niels Lassen Bruun 1928
    #     «Beskrivelse over Danske og Norske Mønter» collection number.
    #     One-per-Krause-sub-variant for typical Christian-IV..Christian-X
    #     coinage; list-form when CLAUDE.md §9a multi-specimen merges
    #     several Bruun cabinet entries into a single coin row.
    #   * `bruun_lot` — legacy V1 ucoin-builder field name carrying the
    #     same Bruun-XXXX collection number under a different key. Values
    #     are aliases when both are set; the cat-group dedupe collapses
    #     them automatically (`add()` skips duplicates within a prefix).
    # `_PREFIX_PRIORITY["Bruun"] = 80` slots both after FP (65) and Dav
    # (70), matching the order Bruun PDFs print: «… Fr, KM, Hede, Sieg,
    # Schou, FP, Bruun-XXXX».
    ("bruun_collection_id", "Bruun"),
    ("bruun_lot", "Bruun"),
    # Galster — Danish-Norwegian numismatic catalogue (Georg Galster
    # series via danskmoent.dk). Routinely populated on coins seeded
    # from `scripts/cache/danskmoent/galster/` via the V1+V2 galster
    # builders. Was missing from this list pre-2026-05-22 — coins
    # whose only catalog ref was Galster (e.g. Christian II Nobel
    # 1516/1518 via c2g37, Hans/Frederik I Galster series) had an
    # empty catalog column despite the source URL being a Galster
    # page. `_PREFIX_PRIORITY` already had a slot for it (270),
    # confirming this is a missing-field bug rather than a missing-
    # priority bug. 120 final entries carry catalog.galster; 54 of
    # those have NO other rendered catalog field.
    ("galster", "Galster"),
    # FP — Friberg-Pedersen «Skillingen, Specien og Kronen 1761-1813»
    # (Christian VII-specific Danish-Norwegian catalogue). Routinely cited
    # alongside Hede/Sieg/Schou in the Bruun PDFs on Christian VII issues.
    # `_PREFIX_PRIORITY` slot 65 places it between Fr (60) and Dav (70) —
    # both are gold-trade-coin / world-crowns adjacencies that pair well
    # with FP's Danish gold + speciedaler Christian-VII focus.
    ("fp", "FP"),
    # MB — Madai / Bach «Vollständiges Thaler-Cabinet» (18th-c. German-states
    # + Schleswig-Holstein thaler/gold catalogue), surfaced by NumisMaster as
    # its «MB#» catalog-number field. Was missing from this list although
    # `_PREFIX_PRIORITY["MB"] = 100` already reserved a slot AND the schema has
    # a `mb` field — the same missing-field (not missing-priority) bug the
    # galster note above describes: coins whose source index was MB# (e.g. the
    # Christian III Goldgulden 1547, MB# 57 / Schou 1352, numismaster MC_167747)
    # rendered an empty catalog cell. Adding the mapping surfaces every
    # catalog.mb value.
    ("mb", "MB"),
]

# Register tooltip text per Krause register code. Used by
# _compute_catalog_groups when emitting register-prefixed KM tokens.
# Mirrors the Numista «issuer» semantics for the major Scandinavian
# / German-states Krause volumes our project touches.
_KM_REGISTER_TOOLTIP: dict[str, str] = {
    "DK": "Krause-Mishler — Denmark volume",
    "SH": "Krause-Mishler — Schleswig-Holstein volume",
    "NO": "Krause-Mishler — Norway volume",
}


# Render priority: lower = earlier. Unknown prefixes get a mid-rank.
_PREFIX_PRIORITY: dict[str, int] = {
    # `KM#` (no suffix) defaults to the territorial Krause-Mishler register
    # for the location being documented (Schleswig-Holstein for our base).
    # `KM-DK#` / `KM-SH#` / etc. are per-volume Krause-Mishler registers —
    # same publisher, different territorial scope. Several Glückstadt
    # issues appear in BOTH registers under different numbers (e.g. our
    # km-25 = DK-KM# 25 = SH-KM# 87), so the suffix is needed for
    # unambiguous citation. See KMRef in schema.py for the per-entry
    # register tagging.
    "KM": 10, "KM-DK": 11, "KM-SH": 12, "KM-NO": 13,
    "Hede": 20, "Sieg": 30, "Schou": 40, "Lange": 50,
    "Fr": 60, "FP": 65,
    "Dav": 70,
    "Dav EC II": 71, "Dav EC III": 72, "Dav EC IV": 73, "Dav ECT": 74,
    "Dav Lg": 75, "Dav SG": 76, "Dav GT I": 77, "Dav CCT": 78,
    "Dav.": 75,
    "Bruun": 80,
    "MB": 100, "Weinm": 110, "AKS": 120, "C": 130,
    "Schön": 140, "Schön DM": 141, "Kahnt/Schön": 142,
    "Behr": 150, "Behr.": 150, "Brockmann": 160,
    "Bahrf": 170, "Bobzin": 180, "Hofmann": 190,
    "Jaeg": 200, "Jaeg 6 NWD": 201,
    "Aagaard": 210, "Aagaard-1": 211, "Aagaard-2": 212, "Aagaard-5": 213,
    "Saur": 220, "Diakov": 230, "Uzd": 240, "Bit": 250,
    "Brekke": 260, "Galster": 270, "Hauberg": 280,
    "Fb": 290, "J": 300,
    "N": 9999,  # Numista's own ID — always last
}

_REF_PATTERN = re.compile(r"^([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9./\- ]*?)#\s*(.+)$")


def _parse_ref(s: str) -> tuple[str | None, str]:
    """'KM# 77.1' → ('KM', '77.1'); 'foo bar' → (None, 'foo bar')."""
    m = _REF_PATTERN.match(s.strip())
    if not m:
        return None, s.strip()
    return m.group(1).strip(), m.group(2).strip()


def _compute_catalog_groups(
    coin: Coin, location_km_register: str | None = None,
) -> list[tuple[str, list[str], str | None]]:
    """Build a list of (prefix, [values], tooltip) groups in render priority order.

    - Named fields (cat.km, cat.lange, ...) become groups by canonical label.
    - `catalog.km` carries optional register tags (per-list-entry KMRef or
      scalar default). When a KM entry's register equals
      `location_km_register` (or is unset and that's the default), it emits
      under the bare «KM» prefix. When the register differs, it emits under
      a register-qualified prefix («KM-DK», «KM-SH») with a tooltip. A
      multi-entry KM list always uses qualified prefixes to keep the
      individual numbers unambiguous.
    - cat.others entries: 'PREFIX# value' lands in a group keyed by PREFIX.
    - cat.numista becomes the trailing 'N#' group.
    - Within each group, values are deduped (preserving order).
    - Unparseable entries (no '#') become a trailing anonymous group.
    """
    cat = coin.catalog
    groups: dict[str, list[str]] = {}
    group_tooltip: dict[str, str | None] = {}
    order: list[str] = []  # first-seen order for tie-breaking

    def add(prefix: str, value: str, tooltip: str | None = None):
        if not value:
            return
        if prefix not in groups:
            groups[prefix] = []
            order.append(prefix)
            group_tooltip[prefix] = tooltip
        if value not in groups[prefix]:
            groups[prefix].append(value)

    # KM field: register-aware. Bare «KM» prefix when entry's register
    # matches the page's default (or is unset); register-qualified
    # «KM-<REG>» with tooltip when it doesn't. Multi-entry lists always
    # render qualified so every number is unambiguous.
    km_raw = getattr(cat, "km", None)
    if km_raw is not None:
        # Normalise to list of (value, register-or-None) tuples
        from .schema import KMRef  # avoid circular at module load
        if isinstance(km_raw, list):
            km_items: list[tuple[str, str | None]] = []
            for item in km_raw:
                if isinstance(item, KMRef):
                    km_items.append((item.value, item.register))
                else:
                    km_items.append((str(item), None))
        else:
            # Scalar: split on composite "77.1 / 77.2" / "77.1, 77.2"
            km_items = [
                (p.strip(), None)
                for p in re.split(r"\s*[,/]\s*", str(km_raw))
                if p.strip()
            ]
        # Multi-entry list → all qualified; single-entry uses register
        # only if it differs from page default.
        force_qualified = len(km_items) > 1
        for value, register in km_items:
            effective_register = register or location_km_register
            qualify = force_qualified or (
                register is not None
                and location_km_register is not None
                and register != location_km_register
            )
            if qualify and effective_register:
                prefix = f"KM-{effective_register}"
                tooltip = _KM_REGISTER_TOOLTIP.get(effective_register)
                add(prefix, value, tooltip)
            else:
                add("KM", value)

    # Named fields (km handled above with register logic)
    for field_name, label in _NAMED_FIELDS:
        if field_name == "km":
            continue
        v = getattr(cat, field_name, None)
        # Render-time numeric-index normalisation: flatten comma/slash-joined
        # multi-source values, dedup, range-subsume, numeric sort. Idempotent,
        # so already-normalised final entries are unaffected; this catches
        # seed-pass coins rendered straight from data/v2/seed/ (which the
        # data-level migration never touched) — same rule as the merger/absorb
        # normalise_catalog, applied at the single render chokepoint.
        if v is not None and field_name in _NUMERIC_INDEX_FIELDS:
            v = normalise_numeric_index(v)
        if v:
            # Companion *_hede1971 field: if set AND differs from the
            # primary value, append "(Hede-1971: X)" to the rendered
            # token so the reader sees both the modern Sieg/Schou ref
            # and the older one printed in Hede 1971 (via danskmoent.dk).
            alt_attr = f"{field_name}_hede1971"
            alt = getattr(cat, alt_attr, None)
            # Schema allows scalar OR list form for hede/sieg/schou
            # (list = multi-sub-letter Krause-canonical entries; see
            # CatalogRefs.hede docstring). For list form, iterate items
            # directly. For scalar form, fall back to the legacy
            # composite-string split ("77.1, 77.2" / "77.1 / 77.2")
            # which serves entries that pack multiple Sieg or Dav refs
            # into one string field. Schou values can contain internal
            # commas (Hede prints "Schou 136-165, 59-61" for one sub-
            # letter), so the comma-split is only safe on scalar legacy
            # strings — list form is the structured replacement when
            # multiple sub-letters need to be represented.
            if isinstance(v, list):
                parts = [str(p).strip() for p in v if p]
            else:
                parts = [
                    p.strip()
                    for p in re.split(r"\s*[,/]\s*", str(v))
                    if p.strip()
                ]
            for part in parts:
                if not part:
                    continue
                # Append the Hede-1971 annotation on the FIRST sub-part only
                # (avoids polluting every comma-split fragment with the same
                # annotation). The annotation suppresses itself if alt ==
                # primary (i.e. both editions agree on the number).
                if alt and str(alt).strip() and str(alt).strip() != part:
                    rendered = f"{part} (Hede-1971: {str(alt).strip()})"
                    add(label, rendered)
                    alt = None  # consumed; subsequent parts plain
                else:
                    add(label, part)

    # Others list — parse each
    plain_lines: list[str] = []
    for raw in cat.others or []:
        prefix, value = _parse_ref(raw)
        if prefix is None:
            plain_lines.append(value)
        else:
            add(prefix, value)

    # Numista — always last. Schema allows scalar `str` or list[str]
    # form (per CLAUDE.md §9a multi-source attestation: same physical
    # coin can have multiple Numista N#s when curators register different
    # sub-variants under separate N#s). Iterate list-form so each N#
    # gets its own value entry in the «N#» group.
    if cat.numista:
        if isinstance(cat.numista, list):
            for n in cat.numista:
                if n:
                    add("N", str(n))
        else:
            add("N", str(cat.numista))

    def sort_key(prefix: str) -> tuple[int, int]:
        prio = _PREFIX_PRIORITY.get(prefix, 500)
        return (prio, order.index(prefix))

    # Drop generic "Dav" group if any specific "Dav <subprefix>" carries the
    # same values — the named field is just a less-precise duplicate of the
    # API-derived sub-catalog (e.g. cat.dav="3679 / 3679A" + others has
    # "Dav EC II# 3679" and "Dav EC II# 3679A" → keep only the EC II group).
    if "Dav" in groups:
        dav_vals = set(groups["Dav"])
        for p in list(groups.keys()):
            if p.startswith("Dav ") and dav_vals.issubset(set(groups[p])):
                del groups["Dav"]
                if "Dav" in order:
                    order.remove("Dav")
                break

    # Within each group, sort values naturally so parent types precede their
    # sub-variants (KM# 77 before 77.1, 77.2). Treat each value as a
    # tuple of numeric/string segments split by '.'/'/' so '77' sorts before '77.1'.
    def value_key(v: str):
        out = []
        for tok in re.split(r"[./\-]", v):
            t = tok.strip()
            # A leading integer with an optional letter sub-variant suffix
            # («1a», «93A», «2») sorts by that integer FIRST, then the suffix —
            # so «1a» precedes «2» (not after every plain int, the bug that
            # rendered «Schou# 2, 7, 1a» instead of «1a, 2, 7»). Pure non-numeric
            # tokens (volume codes «EC II», «Tn6») rank last, as before.
            m = re.match(r"^(\d+)([A-Za-z]*)$", t)
            if m:
                out.append((0, int(m.group(1)), m.group(2).lower()))
            else:
                try:
                    out.append((0, int(t), ""))
                except (ValueError, TypeError):
                    out.append((1, 0, t.lower()))
        return out

    def collapse_runs(values: list[str]) -> list[str]:
        """Sort an index-value list and collapse runs of ≥3 consecutive
        bare integers into 'min-max' ranges. Every value is first expanded
        to its integer members — so existing ranges ('23-24') and
        overlapping/adjacent inputs ('25-26', '26') merge correctly
        ('23-26') instead of rendering as a messy unsorted overlap. Runs
        of 1-2 consecutive integers stay individual numbers (the ≥3
        threshold). Non-integer tokens (sub-variant letters '93A', dotted
        '77.1', register-qualified values) never collapse — they sort
        naturally via value_key and parent types still precede their
        sub-variants."""
        ints: set[int] = set()
        complex_toks: list[str] = []
        for raw in values:
            v = str(raw).strip()
            if not v:
                continue
            m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", v)
            if m and int(m.group(1)) <= int(m.group(2)):
                ints.update(range(int(m.group(1)), int(m.group(2)) + 1))
            elif re.fullmatch(r"\d+", v):
                ints.add(int(v))
            else:
                complex_toks.append(v)
        tokens: list[str] = []
        si = sorted(ints)
        i = 0
        while i < len(si):
            j = i
            while j + 1 < len(si) and si[j + 1] == si[j] + 1:
                j += 1
            run = si[i:j + 1]
            if len(run) >= 3:
                tokens.append(f"{run[0]}-{run[-1]}")
            else:
                tokens.extend(str(n) for n in run)
            i = j + 1
        tokens.extend(complex_toks)
        return sorted(dict.fromkeys(tokens), key=value_key)

    for p in groups:
        groups[p] = collapse_runs(groups[p])

    sorted_prefixes = sorted(groups.keys(), key=sort_key)
    out: list[tuple[str, list[str], str | None]] = [
        (p, groups[p], group_tooltip.get(p)) for p in sorted_prefixes
    ]

    if plain_lines:
        out.append(("", plain_lines, None))

    return out


def _compute_coin(coin: Coin, fuss: Fuss, location_km_register: str | None = None) -> ComputedCoin:
    cc = ComputedCoin(raw=coin, fuss=fuss)

    # Catalog groups for the «Каталог» column
    cc.catalog_groups = _compute_catalog_groups(coin, location_km_register)

    # Normalise measurement fields to (value, source) lists. Scalar form
    # → single (value, None) reading; list form → one entry per source.
    weight_pairs   = normalise_field(coin.weight_rough_g)
    fineness_pairs = normalise_field(coin.fineness)
    diameter_pairs = normalise_field(coin.diameter_mm)

    # Primary values (first list entry) drive the table's main display
    # and the "primary" Feingewicht/delta computation.
    primary_w = weight_pairs[0][0]   if weight_pairs   else None
    primary_f = fineness_pairs[0][0] if fineness_pairs else None
    primary_d = diameter_pairs[0][0] if diameter_pairs else None

    # Expose primary readings on ComputedCoin for template access.
    cc.primary_weight_rough_g  = primary_w
    cc.primary_weight_source   = weight_pairs[0][1]   if weight_pairs   else None
    cc.primary_fineness        = primary_f
    cc.primary_fineness_source = fineness_pairs[0][1] if fineness_pairs else None
    cc.primary_diameter_mm     = primary_d
    cc.primary_diameter_source = diameter_pairs[0][1] if diameter_pairs else None

    # --- Source-coherent (weight, fineness) pairing -------------------
    # A source publishing BOTH a weight and a fineness is one coherent
    # reading: its weight pairs with ITS OWN fineness, never another
    # source's (FieldValue docstring: "never mixing weight from one
    # source with fineness from another"). A weight source with NO
    # fineness of its own falls back to the first-listed fineness as a
    # representative (Phase-2 will make this year-aware / all-variants).
    # This removes the spurious cross-source Feingewicht that the naive
    # weight[0]×fineness[0] primary produced when weight[0]'s source had
    # its own fineness (e.g. galster-weight wrongly × hede-fineness).
    def _toks(src):
        return {t.strip() for t in (src or "").split("\n") if t.strip()}

    def _fineness_for(w_src):
        wt = _toks(w_src)
        if wt:
            for fv, fsrc in fineness_pairs:
                if fsrc and wt & _toks(fsrc):
                    return fv, fsrc
        return None, None

    def _weight_for(f_src):
        ft = _toks(f_src)
        if ft:
            for wv, wsrc in weight_pairs:
                if wsrc and ft & _toks(wsrc):
                    return wv, wsrc
        return None, None

    def _fin_authority(src):
        """Authority score of a fineness reading's source (higher = better).
        Exact-token match first, then substring (so «Møntordning 1514 (23½
        Karat)» still resolves via «møntordning»). Unlisted → 0."""
        amap = _fin_authority_map()
        if not amap:
            return 0
        best = 0
        for t in _toks(src):
            tl = t.lower()
            if tl in amap:
                score = amap[tl]
            else:
                score = max((v for k, v in amap.items() if k in tl), default=0)
            if score > best:
                best = score
        return best

    # Fallback fineness for a weight-only source (one that published a weight
    # but no fineness of its own): borrow the HIGHEST-authority reading, not the
    # arbitrary first-listed one — so a weight-only specimen never latches onto a
    # lower-authority (possibly erroneous) fineness. max() keeps list order on
    # ties, so an empty authority map reproduces the old first-listed behaviour.
    if fineness_pairs:
        _fb = max(fineness_pairs, key=lambda p: _fin_authority(p[1]))
        fallback_f, fallback_f_src = _fb[0], _fb[1]
    else:
        fallback_f, fallback_f_src = None, None
    _own_pf, _own_pf_src = _fineness_for(cc.primary_weight_source)
    if _own_pf is not None:
        primary_f_used, primary_f_used_src = _own_pf, _own_pf_src
    else:
        primary_f_used, primary_f_used_src = fallback_f, fallback_f_src

    # Source label for a derived Feingewicht/delta. These are COMPUTED
    # values (weight × fineness), NOT cited from a source — the label
    # says «обчислено з …» and names BOTH inputs' sources. When one
    # source supplied both (own-pair) it collapses to a single «вагою ×
    # пробою з: X»; when the weight source published no fineness of its
    # own, the fallback fineness source is STILL named so the reader can
    # trace which fineness the multiplication actually used (e.g. weight
    # from bruun, fineness from hede).
    def _derived_label(w_src, f_src):
        if w_src and f_src:
            if _toks(w_src) & _toks(f_src):
                return f"Обчислено з вагою × пробою з:\n{w_src}"
            return (f"Обчислено з вагою з:\n{w_src}\n"
                    f"з пробою з:\n{f_src}")
        if w_src:
            return f"Обчислено з вагою з:\n{w_src}"
        if f_src:
            return f"Обчислено з пробою з:\n{f_src}"
        return None

    cc.primary_derived_source = _derived_label(cc.primary_weight_source,
                                               primary_f_used_src)

    # Propagate the unverified marker: any derived metric is only as solid as
    # its inputs. If the rough weight or fineness is unverified, mark all
    # downstream computations the same way.
    cc.derived_unverified = (not coin.weight_rough_verified) or (not coin.fineness_verified)

    # weight_fein from primary rough × its source-coherent fineness
    if primary_w is not None and primary_f_used is not None:
        cc.weight_fein_g = round(primary_w * primary_f_used, 5)

    # soll values from fuss fractions — per-phase override of the delta
    # target when the fuss's de-jure fineness varies by phase
    # (rhinsk_gylden_fod), else the single fuss-wide soll_fein_g.
    if coin.fraction and coin.fraction in fuss.fractions:
        frac = fuss.fractions[coin.fraction]
        if frac.soll_fein_by_phase and coin.phase in frac.soll_fein_by_phase:
            cc.soll_fein_g = frac.soll_fein_by_phase[coin.phase]
        else:
            cc.soll_fein_g = frac.soll_fein_g
        cc.soll_rau_g = frac.soll_rau_g

    # delta
    if cc.weight_fein_g is not None and cc.soll_fein_g is not None:
        cc.delta_g = round(cc.weight_fein_g - cc.soll_fein_g, 5)
        cc.delta_pct = round(cc.delta_g / cc.soll_fein_g * 100, 3)
        cc.within_remedium = abs(cc.delta_pct) <= 1.0

    # implied fuss: back-compute the standard from the coin's actual silver/gold.
    if coin.fraction:
        try:
            num, _, den = coin.fraction.partition("/")
            k = float(num) / float(den) if den else float(num)
        except (ValueError, ZeroDivisionError):
            k = None
        metal_g = None
        if fuss.metal == "silver" and cc.weight_fein_g:
            metal_g = cc.weight_fein_g
        elif fuss.metal == "gold" and primary_w:
            metal_g = primary_w
        if k and metal_g and k > 0 and metal_g > 0:
            full_unit = metal_g / k
            if full_unit > 0:
                cc.implied_fuss = round(fuss.grid_unit_g / full_unit, 2)

    # Detect whether fuss_refs already documents an implied Fuß — if so,
    # templates should skip the auto-computed line to avoid duplication.
    MARKERS = ("Ist-Wert", "Ist ≈", "actual value", "фактичне значення", "Факт ")
    for ref in coin.fuss_refs or []:
        lbl = ref.label
        texts = []
        for lang in ("de", "en", "uk"):
            v = getattr(lbl, lang, None)
            if v: texts.append(str(v))
        joined = " ".join(texts)
        if any(m in joined for m in MARKERS):
            cc.has_manual_implied = True
            break

    # Per-source alt computations, built source-coherently. Each
    # NON-primary weight reading pairs with the fineness FROM ITS OWN
    # SOURCE (own-pair) — or the representative fallback fineness when
    # its source published none (Phase-2 will make the weight-only case
    # year-aware / all-variants). A source that published ONLY a fineness
    # (no weight of its own) pairs with the primary weight; a diameter-
    # only source carries its diameter alone. `seen_f_srcs` guards a
    # source with both weight and fineness from surfacing twice — once as
    # its own-pair, once as a phantom fineness-only alt. Combined labels
    # ("hede\nnumista") still match via token overlap in the helpers.
    def _diameter_for(src):
        st = _toks(src)
        if st:
            for dv, dsrc in diameter_pairs[1:]:
                if dsrc and st & _toks(dsrc):
                    return dv
        return None

    def _fill_alt_derived(ca, w, f):
        if w is not None and f is not None:
            ca.weight_fein_g = round(w * f, 5)
        if ca.weight_fein_g is not None and cc.soll_fein_g is not None:
            ca.delta_g = round(ca.weight_fein_g - cc.soll_fein_g, 5)
            ca.delta_pct = round(ca.delta_g / cc.soll_fein_g * 100, 3)
            ca.within_remedium = abs(ca.delta_pct) <= 1.0
        if coin.fraction:
            try:
                num, _, den = coin.fraction.partition("/")
                k = float(num) / float(den) if den else float(num)
            except (ValueError, ZeroDivisionError):
                k = None
            metal_g = None
            if fuss.metal == "silver" and ca.weight_fein_g:
                metal_g = ca.weight_fein_g
            elif fuss.metal == "gold" and w:
                metal_g = w
            if k and metal_g and k > 0 and metal_g > 0:
                full_unit = metal_g / k
                if full_unit > 0:
                    ca.implied_fuss = round(fuss.grid_unit_g / full_unit, 2)

    seen_f_srcs: set[str] = set()
    if primary_f_used_src:
        seen_f_srcs.add(primary_f_used_src)
    seen_alt_srcs: set[str] = set()

    # (a) non-primary weight readings — own-source fineness or fallback
    for w, w_src in weight_pairs[1:]:
        ca = ComputedAlt(source=w_src or "")
        ca.weight_rough_g = w
        own_f, own_f_src = _fineness_for(w_src)
        if own_f is not None:
            ca.fineness = own_f
            f_used, f_used_src = own_f, own_f_src
            if own_f_src:
                seen_f_srcs.add(own_f_src)
        else:
            f_used, f_used_src = fallback_f, fallback_f_src
        ca.diameter_mm = _diameter_for(w_src)
        _fill_alt_derived(ca, w, f_used)
        ca.derived_source = _derived_label(w_src, f_used_src)
        cc.alts.append(ca)
        if w_src:
            seen_alt_srcs.add(w_src)

    # (b) fineness-only sources — published a fineness but NO weight of
    #     their own, and not already consumed by an own-pair above →
    #     pair with the primary weight (a genuine cross-source reading).
    for fv, f_src in fineness_pairs:
        if not f_src or f_src in seen_f_srcs:
            continue
        if _weight_for(f_src)[0] is not None:
            continue
        ca = ComputedAlt(source=f_src)
        ca.fineness = fv
        ca.diameter_mm = _diameter_for(f_src)
        _fill_alt_derived(ca, primary_w, fv)
        ca.derived_source = _derived_label(cc.primary_weight_source, f_src)
        cc.alts.append(ca)
        seen_alt_srcs.add(f_src)

    # (c) diameter-only sources — carry the diameter for debug/audit
    #     parity; they contribute no Feingewicht (skipped in fein_pairs).
    for dv, d_src in diameter_pairs[1:]:
        if not d_src or d_src in seen_alt_srcs:
            continue
        if _weight_for(d_src)[0] is not None or _fineness_for(d_src)[0] is not None:
            continue
        ca = ComputedAlt(source=d_src)
        ca.diameter_mm = dv
        cc.alts.append(ca)
        seen_alt_srcs.add(d_src)

    # ---- Display-level grouping by rounded value ----
    # For each measurement field, build "groups" the renderer iterates.
    # Each group ≈ one rendered span. When all readings for a field
    # round to the same value → single group with is_unanimous=True →
    # plain text (no tooltip, no alt-source styling).
    cc.weight_groups   = make_display_groups(weight_pairs,   precision=2)
    cc.fineness_groups = make_display_groups(fineness_pairs, precision=3)
    cc.diameter_groups = make_display_groups(diameter_pairs, precision=1)

    # Derived Feingewicht groups: build (value, source) pairs from
    # primary + per-source alts, then group at 5-decimal precision.
    # (value, derived_source_label, anchor_weight_source) — the 3rd element is
    # the WEIGHT source the derived value is anchored to (== the join key that
    # matches the weight column's own source), NOT the combined derived label.
    fein_pairs: list[tuple[float, str | None, str | None]] = []
    delta_pairs: list[tuple[float, str | None, str | None]] = []
    impl_pairs: list[tuple[float, str | None, float]] = []  # (value, src, delta_pct)
    if cc.weight_fein_g is not None:
        fein_pairs.append((cc.weight_fein_g, cc.primary_derived_source, cc.primary_weight_source))
    if cc.delta_g is not None:
        delta_pairs.append((cc.delta_g, cc.primary_derived_source, cc.primary_weight_source))
    if (cc.implied_fuss is not None and cc.delta_pct is not None
            and abs(cc.delta_pct) > 2):
        impl_pairs.append((cc.implied_fuss, cc.primary_derived_source, cc.delta_pct))
    for ca in cc.alts:
        if not (ca.weight_rough_g or ca.fineness):
            continue
        # The alt's derived-source label was built at computation time
        # and names BOTH inputs' sources — the weight source AND the
        # fineness source actually used (own-pair collapses to one; a
        # weight-only source names its fallback fineness source too, so
        # «weight from bruun × fineness from hede» is fully traceable).
        alt_label = ca.derived_source
        if not alt_label:
            continue
        # Anchor = the WEIGHT source behind this derived value: a weight-alt
        # (own reading, ca.weight_rough_g set) anchors to its own source; a
        # fineness-only alt derives from the PRIMARY weight, so it anchors to
        # the primary weight source.
        alt_anchor = ca.source if ca.weight_rough_g is not None else cc.primary_weight_source
        if ca.weight_fein_g is not None:
            fein_pairs.append((ca.weight_fein_g, alt_label, alt_anchor))
        if ca.delta_g is not None:
            delta_pairs.append((ca.delta_g, alt_label, alt_anchor))
        if (ca.implied_fuss is not None and ca.delta_pct is not None
                and abs(ca.delta_pct) > 2):
            impl_pairs.append((ca.implied_fuss, alt_label, ca.delta_pct))

    cc.weight_fein_groups = make_display_groups(fein_pairs, precision=5)
    cc.delta_groups = make_display_groups(delta_pairs, precision=5)
    # Annotate delta groups with delta_pct (from canonical value ÷ soll_fein)
    # so the template colour-classes the Δ badge without recomputing.
    if cc.soll_fein_g:
        for g in cc.delta_groups:
            g.delta_pct = round(g.value / cc.soll_fein_g * 100, 3)

    # Render order: when a row carries multiple readings, sort the three
    # parallel columns (weight, weight_fein, delta) descending by value
    # so the heaviest specimen sits on top. Δ inherits the same order
    # since it is monotonic in fein-weight, which is monotonic in
    # gross-weight when fineness is constant — the typical case. When
    # fineness varies across alts the orders may differ; tooltips still
    # carry the per-source provenance, so visual parallelism remains
    # informative even when rows don't line up exactly.
    cc.weight_groups.sort(key=lambda g: g.value, reverse=True)
    cc.weight_fein_groups.sort(key=lambda g: g.value, reverse=True)
    cc.delta_groups.sort(key=lambda g: g.value, reverse=True)

    # Per-specimen measurement sub-rows (rendered by the template only when
    # msr_n > 1; single-reading coins keep the compact *_groups rendering).
    _build_measurement_rows(cc, fineness_pairs)

    # implied_fuss_groups: only entries where the corresponding source's
    # |delta_pct| > 2 — small deviations make implied ≈ declared and add no
    # information. Pre-filtered above; here we only need to group by the
    # rounded implied_fuss value.
    cc.implied_fuss_groups = make_display_groups(
        [(v, s) for v, s, _ in impl_pairs], precision=2
    )
    # Carry the maximum |delta_pct| from each group's contributing readings
    # so the template can keep the existing > 2 threshold semantics if it
    # ever needs to apply per-group filtering downstream.
    if impl_pairs:
        # Build group_key → max_abs_delta_pct
        max_dp: dict[float, float] = {}
        for v, _, dp in impl_pairs:
            key = round(v, 2)
            cur = max_dp.get(key, 0.0)
            if abs(dp) > cur:
                max_dp[key] = abs(dp)
        for g in cc.implied_fuss_groups:
            g.delta_pct = max_dp.get(round(g.value, 2))

    return cc


def compute_location(
    location: Location,
    fuesse: dict[str, Fuss],
) -> list[ComputedCoin]:
    """Compute derived fields for all coins in a location.

    Per-location Fuß overrides (Variant A, 2026-05-22): when the location's
    `fuss_periods.<fuss>` block carries name / historical_name / description /
    grundwerte fields, we apply those overrides BEFORE binding the Fuss to
    the per-coin ComputedCoin — so the coin-row Fuß-name column shows the
    overridden form (Rigsdukatfod on the Denmark page) instead of the global
    form (Reichsdukatenfuß). Without this resolution, only the FussGroup
    section heading saw the override; per-coin fuss.name calls still
    rendered the global label.
    """
    # Local import to avoid circular dependency (categorize imports compute).
    from .categorize import _resolve_fuss_with_overrides
    fuess_by_id_resolved: dict[str, Fuss] = {}
    location_overrides = location.fuss_periods or {}
    for fid, base in fuesse.items():
        fuess_by_id_resolved[fid] = _resolve_fuss_with_overrides(
            base, location_overrides.get(fid)
        )
    computed = []
    for coin in location.coins:
        if coin.fuss not in fuess_by_id_resolved:
            # Should have been caught in validation, but guard anyway
            continue
        computed.append(_compute_coin(
            coin, fuess_by_id_resolved[coin.fuss],
            location_km_register=location.km_register,
        ))
    return computed
