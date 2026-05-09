"""
Layer A → B: compute derived fields for each coin.

Pure functions over the input data. No template concerns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Coin, Fuss, Location, FieldValue


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
        return [(fv.value, fv.source) for fv in v]
    # FieldValue object (shouldn't happen at this layer but defensive)
    if hasattr(v, "value"):
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


def make_display_groups(
    pairs: list[tuple[float, str | None]],
    precision: int,
) -> list[DisplayGroup]:
    """Group (value, source) pairs by their display-precision rounded
    value. Each unique display value → one DisplayGroup whose `sources`
    list combines every contributing source label. When all pairs round
    to the same display value, the single returned group has
    `is_unanimous=True` so the renderer can drop tooltip+styling
    (consensus = plain text)."""
    if not pairs:
        return []
    groups: dict[float, list[tuple[float, str | None]]] = {}
    order: list[float] = []
    for v, src in pairs:
        if v is None:
            continue
        key = round(v, precision)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((v, src))

    is_unanimous = len(order) == 1
    out: list[DisplayGroup] = []
    for key in order:
        members = groups[key]
        canonical = members[0][0]
        srcs: list[str] = []
        for _, src in members:
            if not src:
                continue
            for tok in src.split("\n"):
                tok = tok.strip()
                if tok and tok not in srcs:
                    srcs.append(tok)
        out.append(DisplayGroup(value=canonical, sources=srcs,
                                is_unanimous=is_unanimous))
    return out


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
    # Catalog refs grouped by prefix; each group is (label, [values]).
    # Rendered in template, one group per line: "KM# 77, 77.1, 77.2".
    catalog_groups: list[tuple[str, list[str]]] = field(default_factory=list)
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

    def __getattr__(self, name):
        """Proxy to raw for convenience."""
        return getattr(self.raw, name)


# ---------------------------------------------------------------------
# Catalog grouping — collects named fields + parses cat.others into a
# stable, prefix-grouped, deduplicated list. Used by the renderer to lay
# out the «Каталог» column with one prefix per row.
# ---------------------------------------------------------------------

import re  # noqa: E402

# Display label for each named catalog field
_NAMED_FIELDS: list[tuple[str, str]] = [
    ("km", "KM"),
    ("hede", "Hede"),
    ("sieg", "Sieg"),
    ("schou", "Schou"),
    ("lange", "Lange"),
    ("fr", "Fr"),
    ("dav", "Dav"),
    ("bruun_lot", "Bruun"),
]

# Render priority: lower = earlier. Unknown prefixes get a mid-rank.
_PREFIX_PRIORITY: dict[str, int] = {
    # `KM#` (no suffix) defaults to the territorial Krause-Mishler register
    # for the location being documented (Schleswig-Holstein for our base).
    # `KM-DK#` is the Royal Danish Krause-Mishler register — same publisher,
    # different territorial scope. Several Glückstadt issues appear in BOTH
    # registers under different numbers (e.g. our km-358 = SH-KM# 358 =
    # DK-KM# 71), so the suffix is needed for unambiguous citation.
    "KM": 10, "KM-DK": 11, "Hede": 20, "Sieg": 30, "Schou": 40, "Lange": 50,
    "Fr": 60,
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


def _compute_catalog_groups(coin: Coin) -> list[tuple[str, list[str]]]:
    """Build a list of (prefix, [values]) groups in render priority order.

    - Named fields (cat.km, cat.lange, ...) become groups by canonical label.
    - cat.others entries: 'PREFIX# value' lands in a group keyed by PREFIX.
    - cat.numista becomes the trailing 'N#' group.
    - Within each group, values are deduped (preserving order).
    - Unparseable entries (no '#') become a trailing anonymous group.
    """
    cat = coin.catalog
    groups: dict[str, list[str]] = {}
    order: list[str] = []  # first-seen order for tie-breaking

    def add(prefix: str, value: str):
        if not value:
            return
        if prefix not in groups:
            groups[prefix] = []
            order.append(prefix)
        if value not in groups[prefix]:
            groups[prefix].append(value)

    # Named fields
    for field_name, label in _NAMED_FIELDS:
        v = getattr(cat, field_name, None)
        if v:
            # Some named fields hold composite "77.1, 77.2" or "77.1 / 77.2"
            for part in re.split(r"\s*[,/]\s*", str(v)):
                if part.strip():
                    add(label, part.strip())

    # Others list — parse each
    plain_lines: list[str] = []
    for raw in cat.others or []:
        prefix, value = _parse_ref(raw)
        if prefix is None:
            plain_lines.append(value)
        else:
            add(prefix, value)

    # Numista — always last
    if cat.numista:
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
            try:
                out.append((0, int(t)))
            except (ValueError, TypeError):
                out.append((1, t))
        return out

    for p in groups:
        groups[p] = sorted(set(groups[p]), key=value_key)

    sorted_prefixes = sorted(groups.keys(), key=sort_key)
    out: list[tuple[str, list[str]]] = [(p, groups[p]) for p in sorted_prefixes]

    if plain_lines:
        out.append(("", plain_lines))

    return out


def _compute_coin(coin: Coin, fuss: Fuss) -> ComputedCoin:
    cc = ComputedCoin(raw=coin, fuss=fuss)

    # Catalog groups for the «Каталог» column
    cc.catalog_groups = _compute_catalog_groups(coin)

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

    # Source label for derived primary Feingewicht/delta. Critically,
    # these are COMPUTED values (weight × fineness), NOT directly cited
    # from any source — the source(s) supply the inputs, not the
    # derived number. The label makes that explicit ("обчислено з …")
    # so a reader hovering doesn't think e.g. Numista published .979 ×
    # 3.48 = 3.40692; Numista only published 3.48 g and .979 fineness;
    # the multiplication is ours.
    if cc.primary_weight_source and cc.primary_fineness_source:
        if cc.primary_weight_source == cc.primary_fineness_source:
            cc.primary_derived_source = (f"Обчислено з вагою × пробою з:\n"
                                         f"{cc.primary_weight_source}")
        else:
            cc.primary_derived_source = (f"Обчислено з вагою з:\n"
                                         f"{cc.primary_weight_source}\n"
                                         f"з пробою з:\n"
                                         f"{cc.primary_fineness_source}")
    elif cc.primary_weight_source:
        cc.primary_derived_source = f"Обчислено з вагою з:\n{cc.primary_weight_source}"
    elif cc.primary_fineness_source:
        cc.primary_derived_source = f"Обчислено з пробою з:\n{cc.primary_fineness_source}"

    # Propagate the unverified marker: any derived metric is only as solid as
    # its inputs. If the rough weight or fineness is unverified, mark all
    # downstream computations the same way.
    cc.derived_unverified = (not coin.weight_rough_verified) or (not coin.fineness_verified)

    # weight_fein from primary rough × fineness
    if primary_w is not None and primary_f is not None:
        cc.weight_fein_g = round(primary_w * primary_f, 5)

    # soll values from fuss fractions
    if coin.fraction and coin.fraction in fuss.fractions:
        frac = fuss.fractions[coin.fraction]
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

    # Per-source alt computations: when measurement fields are list-form
    # (multiple sources), each non-primary source gets its own
    # Feingewicht / delta / implied_fuss derived from THAT source's
    # weight + fineness pair. Source labels can be COMBINED (newline-
    # separated, e.g. "ucoin tid X\nNumista N#Y" when one value is
    # confirmed by multiple sources). We pair by checking if any TOKEN
    # of an alt source matches any token of weight/fineness source —
    # so a combined-label fineness entry still pairs cleanly with a
    # specific-label weight entry from the same source. Otherwise a
    # cross-source product (primary-weight × alt-fineness with no
    # token match) would surface as an "extra" derived value the user
    # can't trace to any single coherent source reading.
    def _tokens(src: str) -> list[str]:
        return [t.strip() for t in (src or "").split("\n") if t.strip()]

    def _value_for_source(pairs: list[tuple[float, str | None]],
                          source_tokens: set[str],
                          exclude_primary: bool = True) -> float | None:
        """Find a NON-PRIMARY entry whose source label shares ANY token
        with source_tokens. Primary entry (index 0) excluded by default
        — its value is shown by the primary render path; including it
        here would surface as a duplicate alt."""
        candidates = pairs[1:] if exclude_primary else pairs
        for v, s in candidates:
            if s and source_tokens & set(_tokens(s)):
                return v
        return None

    # Collect all unique INDIVIDUAL source tokens that appear in any
    # non-primary position. NOTE: we do NOT exclude tokens present in
    # primary entries — a token like "ucoin tid X" can be part of a
    # combined-label primary diameter ("Hede X\nucoin tid X") while
    # still being a distinct alt source for weight/fineness. Excluding
    # it would silently drop that source's alt in the other field.
    alt_tokens: list[str] = []
    for pairs in (weight_pairs[1:], fineness_pairs[1:], diameter_pairs[1:]):
        for _, src in pairs:
            for tok in _tokens(src):
                if tok not in alt_tokens:
                    alt_tokens.append(tok)

    for tok in alt_tokens:
        toks = {tok}
        ca = ComputedAlt(source=tok)
        # For each field: pick value whose source label includes this token
        ca.weight_rough_g = _value_for_source(weight_pairs,   toks)
        ca.fineness       = _value_for_source(fineness_pairs, toks)
        ca.diameter_mm    = _value_for_source(diameter_pairs, toks)

        w = ca.weight_rough_g if ca.weight_rough_g is not None else primary_w
        f = ca.fineness       if ca.fineness       is not None else primary_f
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
        cc.alts.append(ca)

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
    fein_pairs: list[tuple[float, str | None]] = []
    delta_pairs: list[tuple[float, str | None]] = []
    impl_pairs: list[tuple[float, str | None, float]] = []  # (value, src, delta_pct)
    if cc.weight_fein_g is not None:
        fein_pairs.append((cc.weight_fein_g, cc.primary_derived_source))
    if cc.delta_g is not None:
        delta_pairs.append((cc.delta_g, cc.primary_derived_source))
    if (cc.implied_fuss is not None and cc.delta_pct is not None
            and abs(cc.delta_pct) > 2):
        impl_pairs.append((cc.implied_fuss, cc.primary_derived_source, cc.delta_pct))
    for ca in cc.alts:
        if not (ca.weight_rough_g or ca.fineness):
            continue
        alt_label = f"Обчислено з вагою × пробою з:\n{ca.source}"
        if ca.weight_fein_g is not None:
            fein_pairs.append((ca.weight_fein_g, alt_label))
        if ca.delta_g is not None:
            delta_pairs.append((ca.delta_g, alt_label))
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
    """Compute derived fields for all coins in a location."""
    computed = []
    for coin in location.coins:
        if coin.fuss not in fuesse:
            # Should have been caught in validation, but guard anyway
            continue
        computed.append(_compute_coin(coin, fuesse[coin.fuss]))
    return computed
