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
    display_decimals: int | None = None  # adaptive decimals when default rounding
                                          # would collapse distinct groups into
                                          # identical-looking text (None → use
                                          # template-default precision)


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
    groups: dict[float, list[tuple[float, str | None]]] = {}
    order: list[float] = []
    for v, src in pairs:
        if v is None:
            continue
        key = round(v, group_precision)
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

    # Adaptive display-decimals: when groups are SEMANTICALLY distinct
    # at the finer grouping precision but would collapse to identical
    # text at the template's default decimals (e.g. 2.386 and 2.390
    # both → «2.39» at decimals=2), bump per-group `display_decimals`
    # to the lowest precision that distinguishes them. Otherwise the
    # user sees two visually-identical spans and the source-divergence
    # signal is lost on the rendered table (only the tooltip would
    # carry the info, and tooltips are mouse-only).
    if not is_unanimous and len(out) >= 2:
        canonicals = [g.value for g in out]
        # Find the smallest decimals p >= `precision` such that
        # rounding all canonicals to p yields the same number of
        # distinct values as the group count itself.
        for p in range(precision, group_precision + 1):
            rounded = [round(v, p) for v in canonicals]
            if len(set(rounded)) == len(out):
                if p > precision:
                    for g in out:
                        g.display_decimals = p
                break
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
        # Mirror the primary-derived-source prefix logic: pick the
        # prefix that reflects WHICH input(s) this alt actually
        # overrides (weight only / fineness only / both). Without this
        # alignment, alts that supply only a different weight reading
        # (with fineness inherited from the scalar primary) would
        # render under the «× пробою» prefix and visually duplicate
        # the primary's «з вагою з:» prefix in the same tooltip after
        # multi-source weight entries are split per source.
        if ca.weight_rough_g is not None and ca.fineness is not None:
            alt_label = f"Обчислено з вагою × пробою з:\n{ca.source}"
        elif ca.weight_rough_g is not None:
            alt_label = f"Обчислено з вагою з:\n{ca.source}"
        elif ca.fineness is not None:
            alt_label = f"Обчислено з пробою з:\n{ca.source}"
        else:
            # both inherited from primary — alt only overrides diameter
            # or another non-derivation field; nothing to label here.
            continue
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
