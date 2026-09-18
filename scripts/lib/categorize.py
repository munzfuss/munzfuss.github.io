"""
Layer B → C: group computed coins into the render-ready tree.

Produces nested structure: location → fuss → phase → kind → coins (sorted).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .compute import ComputedCoin
from .fraction_infer import _parse_nominal_head
from .schema import Location, Phase, Fuss, FussPeriod, Grundwerte


def _fraction_value(fraction: str | None) -> float | None:
    """`fraction` as a number: «4» → 4.0, «1/2» → 0.5, «3/2» → 1.5.

    This is the coin's size in the FUSS's own unit, which is why it is the
    right key for ordering a table: it compares a ½ Speciedaler against a
    4 Skilling correctly, where the bare quantities («½» vs «4») do not.
    """
    if not fraction:
        return None
    s = str(fraction).strip()
    if "/" in s:
        num, _, den = s.partition("/")
        if num.isdigit() and den.isdigit() and int(den):
            return int(num) / int(den)
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _nominal_magnitude(nominal: str | None) -> float | None:
    """The quantity a nominal names — «4 Daler» → 4.0, «½ Dukat» → 0.5.

    Fallback only, for coins whose `fraction` is not filled in yet. It reads
    the number a row displays, so rows of one denomination still come out in
    order; it cannot compare ACROSS denominations, which is what `fraction`
    is for.
    """
    if not nominal:
        return None
    frac, count, _rest = _parse_nominal_head(nominal)
    if count is not None:
        return float(count)
    if frac and "/" in frac:
        num, _, den = frac.partition("/")
        if num.isdigit() and den.isdigit() and int(den):
            return int(num) / int(den)
    return None


def _resolve_fuss_with_overrides(base: Fuss, override: FussPeriod | None) -> Fuss:
    """Apply per-location overrides from FussPeriod onto the shared Fuss
    definition. Returns the SAME instance when no overrides exist; else
    returns a model-copy with overlaid fields.

    Per-location-override design 2026-05-22 (Variant A):

      - `override.name`, `override.historical_name`, `override.description` —
        whole-field replacement when present in the location's
        `fuss_periods.<fuss>` block.
      - `override.grundwerte` — partial-replace at the top-level sub-key
        granularity (heading/subheading/badge/rechnungsfraktionen_label/
        rechnungsfraktionen replace independently; `rows` is a list and
        replaces fully when provided, while `rows_patch` edits individual
        shared rows in place).

    Use case: «Reichsdukatenfuß» (German imperial standard 1559+) is
    surfaced on the Danish page as «Rigsdukatfod» (Danish-syntax form,
    structurally parallel to Riksdaler ↔ Reichstaler) with a Hungarian-
    Goldgulden-tradition narrative 1481-1876. Same physical Fuß ID, same
    coin classification, distinct page-level framing.
    """
    if override is None:
        return base
    updates: dict[str, Any] = {}
    if override.name is not None:
        updates['name'] = override.name
    if override.historical_name is not None:
        updates['historical_name'] = override.historical_name
    if override.description is not None:
        updates['description'] = override.description
    if override.grundwerte is not None:
        updates['grundwerte'] = _merge_grundwerte(base.grundwerte, override.grundwerte)
    if override.fractions is not None:
        updates['fractions'] = _merge_fractions(base.fractions, override.fractions)
    if not updates:
        return base
    return base.model_copy(update=updates)


def _merge_fractions(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Per-KEY replace on `Fuss.fractions`. A fraction named in the override
    replaces that fraction wholly; fractions it does not name are inherited
    untouched.

    Per-key (not per-field) because a `Fraction` is small and self-consistent —
    `soll_rau_g`, `soll_fein_g` and `soll_fein_by_phase` describe one
    denomination together, and half-overriding them would produce a target no
    ordinance ever set. Unlike `Grundwerte.rows` (a list with no stable key,
    which is why that one replaces wholesale) the fraction string IS a stable
    key, so a partial override is well-defined here."""
    merged = dict(base)
    merged.update(override)
    return merged


def _merge_grundwerte(base: Grundwerte | None, override: Grundwerte) -> Grundwerte:
    """Top-level partial-replace on Grundwerte. Each Grundwerte sub-key
    that's explicitly set in the override (via `model_fields_set`)
    replaces the corresponding base value. Sub-keys absent from the
    override fall back to base.

    `rows` still replaces the base list in FULL when set — two pages rely on
    that (denmark/reichsdukatenfuss supplies 7 rows against 3 shared,
    schleswig_holstein/rhinsk_gylden_fod 4 against 6), so the two lists are
    genuinely different cards rather than edits of one.

    `rows_patch` is the other case: edit ONE shared row and inherit the rest.
    It is applied after `rows`, so a page may replace the list and then patch
    the result. See `Grundwerte.rows_patch` for why the German key text is the
    identity."""
    if base is None:
        return override
    base_dict = base.model_dump()
    override_dict = override.model_dump()
    # Only fields the override caller explicitly set should replace
    explicit_keys = override.model_fields_set
    merged = dict(base_dict)
    for k in explicit_keys:
        if k in override_dict:
            merged[k] = override_dict[k]
    patch = merged.pop('rows_patch', None)
    if patch:
        merged['rows'] = _patch_rows(merged.get('rows') or [], patch)
    else:
        merged.pop('rows_patch', None)
    return Grundwerte(**merged)


def _patch_rows(rows: list[dict], patch: dict[str, dict]) -> list[dict]:
    """Apply `rows_patch` onto a Grundwerte row list, keyed by German key text.

    Each patch entry names the languages it changes; everything else in the
    row is inherited. A key that matches no row — or more than one — raises,
    because the alternative is a page that quietly keeps showing the shared
    wording the patch existed to change.
    """
    out = [dict(r) for r in rows]
    for de_key, fields in patch.items():
        hits = [i for i, r in enumerate(out)
                if ((r.get('key') or {}).get('de')) == de_key]
        if len(hits) != 1:
            raise ValueError(
                f"grundwerte.rows_patch: German row key {de_key!r} matched "
                f"{len(hits)} rows (expected exactly 1). Available: "
                + ', '.join(repr((r.get('key') or {}).get('de')) for r in out)
            )
        row = out[hits[0]]
        for field_name, langs in (fields or {}).items():
            if not langs:
                continue
            merged_field = dict(row.get(field_name) or {})
            merged_field.update({k: v for k, v in langs.items() if v is not None})
            row[field_name] = merged_field
    return out


@dataclass
class PhaseGroup:
    """A phase within a fuss, with its categorized coins."""
    phase: Phase
    kurant_coins: list[ComputedCoin] = field(default_factory=list)
    scheide_coins: list[ComputedCoin] = field(default_factory=list)   # silver/billon scheidemünzen (have computable Δ)
    copper_coins: list[ComputedCoin] = field(default_factory=list)    # pure copper tokens (no silver, Δ undefined)
    tarif_coins: list[ComputedCoin] = field(default_factory=list)     # standard tariff coins (fineness ≈ fuss standard)
    tarif_deviant_coins: list[ComputedCoin] = field(default_factory=list)
    # ↑ Tariff coins whose fineness is materially below the fuss standard
    # (Hebræermønt 1645 .593 vs Kronemønt-Standard .671) — a "Scheidemünze
    # within the Tarifmünze": same nominal tariff, additional silver debasement
    # on top. Rendered in its own sub-block analogous to Scheidemünze.
    tarif_subunit_coins: list[ComputedCoin] = field(default_factory=list)
    # ↑ Tariff subdivision coins under the same tariff regime — same fineness
    # as the parent Tarifmünze, but per-piece silver content systematically
    # exceeds the strict subdivision proportion (e.g. Kroneskilling 1619-1621
    # at .859 carry up to ~2× the silver of strict 1/96-Krone). Rendered as
    # its own sub-block, contrasting with the at-tariff main coins.
    gedenk_coins: list[ComputedCoin] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (len(self.kurant_coins) + len(self.scheide_coins) + len(self.copper_coins)
                + len(self.tarif_coins) + len(self.tarif_deviant_coins)
                + len(self.tarif_subunit_coins) + len(self.gedenk_coins))

    @property
    def nonempty(self) -> bool:
        return self.total > 0

    @property
    def is_mixed(self) -> bool:
        """True when more than one category group has coins (needs subcat dividers)."""
        groups = [bool(self.kurant_coins), bool(self.scheide_coins), bool(self.copper_coins),
                  bool(self.tarif_coins), bool(self.tarif_deviant_coins),
                  bool(self.tarif_subunit_coins)]
        return sum(groups) > 1


@dataclass
class FussGroup:
    """A fuss with its phases and coins."""
    fuss: Fuss
    phases: list[PhaseGroup] = field(default_factory=list)

    @property
    def nonempty_phases(self) -> list[PhaseGroup]:
        return [p for p in self.phases if p.nonempty]

    @property
    def has_any_coin(self) -> bool:
        """True when at least one phase carries a coin. Used by the
        empty-catch-all filter — see `categorize()` below."""
        return any(p.nonempty for p in self.phases)

    @property
    def unique_nominals(self) -> int:
        """Count of distinct `nominal` strings across every coin in every
        phase of this Fuss. Used by the per-fuss collapsible stat-bar
        as a quick «how many denomination types belong to this Müntzfuß
        on this page» summary.

        Compares raw `coin.raw.nominal` strings — two coins with the
        same inscription (e.g. two KM variants of «1 Thaler Species»
        struck under different mintmasters) collapse to one nominal.
        Coins with no nominal string (defensive null check) are skipped.
        """
        seen: set[str] = set()
        for pg in self.phases:
            for coin_list in (
                pg.kurant_coins, pg.scheide_coins, pg.copper_coins,
                pg.tarif_coins, pg.tarif_deviant_coins,
                pg.tarif_subunit_coins, pg.gedenk_coins,
            ):
                for cc in coin_list:
                    nom = getattr(cc.raw, "nominal", None)
                    if nom:
                        seen.add(nom)
        return len(seen)


@dataclass
class LocationTree:
    """Full categorized tree for a location."""
    location: Location
    fuesse: list[FussGroup] = field(default_factory=list)



def categorize(
    location: Location,
    computed_coins: list[ComputedCoin],
    fuesse: dict[str, Fuss],
) -> LocationTree:
    """Group computed coins by (fuss, phase, kind) respecting the location's preferred ordering.

    The post-timeline fuss list is rendered in the order of `location.fuss_order`,
    re-sorted so it follows the (already-sorted) `location.timeline.bars` order.
    Fuss-ids that have a timeline bar are placed in bar-position; ids without a
    bar fall back to their `fuss_order` position (after the bar-tagged ones).
    Result: the optional `order` field on TimelineBar drives both the timeline
    and this list with a single source of truth — no need to keep `fuss_order`
    and `bars` manually synchronised.
    """

    # Index coins by (fuss, phase)
    from collections import defaultdict
    idx: dict[tuple[str, str], list[ComputedCoin]] = defaultdict(list)
    for cc in computed_coins:
        idx[(cc.raw.fuss, cc.raw.phase)].append(cc)

    tree = LocationTree(location=location)

    # Effective fuss order: sort `location.fuss_order` by timeline-bar
    # position (bars are already sorted by their `order` field via the
    # Timeline pydantic validator). Fuss without a corresponding bar
    # keep their `fuss_order` position relative to each other and are
    # placed AFTER the bar-tagged ones.
    bar_position = {}
    if location.timeline and location.timeline.bars:
        bar_position = {b.id: i for i, b in enumerate(location.timeline.bars)}

    def _fuss_sort_key(item):
        original_idx, fuss_id = item
        bar_idx = bar_position.get(fuss_id)
        if bar_idx is not None:
            return (0, bar_idx, original_idx)
        return (1, original_idx, 0)

    fuss_order_sorted = [fid for _, fid in sorted(enumerate(location.fuss_order), key=_fuss_sort_key)]

    for fuss_id in fuss_order_sorted:
        if fuss_id not in fuesse:
            continue
        if fuss_id not in location.phases:
            continue

        # Per-location overrides (Variant A 2026-05-22): look up the
        # location's `fuss_periods.<fuss>` entry — if it carries any
        # override field (name / historical_name / description /
        # grundwerte), build a merged Fuss for THIS page only.
        location_override = (location.fuss_periods or {}).get(fuss_id)
        resolved_fuss = _resolve_fuss_with_overrides(
            fuesse[fuss_id], location_override
        )
        sg = FussGroup(fuss=resolved_fuss)
        
        for phase in location.phases[fuss_id]:
            pg = PhaseGroup(phase=phase)
            coins_in_phase = idx.get((fuss_id, phase.id), [])
            # None-safe: undated coins (year_first=None, e.g. ND kmk/bruun
            # seed pieces — Vildmandsdaler, Portrætdaler) are legitimate and
            # sort AFTER all dated coins, then by id. A bare `(year_first, id)`
            # key raises «'<' not supported between NoneType and int» the moment
            # a phase group mixes dated + undated coins (surfaced when the
            # Brunswick page gained the kmk bulk phase, 2026-07-24).
            # Within one year, order by `fraction` ascending — the coin's size
            # in the fuss's own unit. Falling through to the id (a provenance
            # string) is what rendered the 1604 Klippen as 4 · 6 · 8 · 3 and
            # made the table read as unsorted.
            #
            # `fraction` is filled in as each standard is worked through, so
            # coins that do not carry one yet sort after those that do, ordered
            # among themselves by the quantity their nominal displays. That
            # keeps an unprocessed group readable without letting its numbers —
            # which mean «4 Skilling», not «4 units of the fuss» — interleave
            # with the processed ones, where they would compare against a
            # different scale entirely.
            def _row_order(c):
                frac = _fraction_value(getattr(c.raw, "fraction", None))
                mag = _nominal_magnitude(c.raw.nominal)
                return (c.raw.year_first is None,
                        c.raw.year_first or 0,
                        frac is None,
                        frac if frac is not None else 0.0,
                        mag is None,
                        mag if mag is not None else 0.0,
                        c.raw.id)

            coins_in_phase.sort(key=_row_order)
            
            for cc in coins_in_phase:
                if cc.raw.kind == "kurant":
                    pg.kurant_coins.append(cc)
                elif cc.raw.kind == "scheide":
                    # Pure copper tokens (no precious metal content) get their own sub-group
                    # since Δ is undefined and the economic logic differs from billon scheidemünzen.
                    if cc.raw.metal in ("copper", "bronze", "brass"):
                        pg.copper_coins.append(cc)
                    else:
                        pg.scheide_coins.append(cc)
                elif cc.raw.kind == "tarif":
                    # Split tariff coins by whether the fineness materially
                    # undercuts the fuss standard. Threshold of 1 % keeps
                    # rounding noise out of the «deviant» bucket; only real
                    # debasement (e.g. Hebræermønt .593 vs .671 = 11.6 % gap)
                    # is broken out into its own sub-table.
                    fuss_std = cc.fuss.fineness_standard
                    if (cc.primary_fineness is not None and fuss_std
                            and cc.primary_fineness < fuss_std - 0.01):
                        pg.tarif_deviant_coins.append(cc)
                    else:
                        pg.tarif_coins.append(cc)
                elif cc.raw.kind == "tarif_subunit":
                    pg.tarif_subunit_coins.append(cc)
                elif cc.raw.kind == "gedenk":
                    # Commemoratives are no longer a separate sub-table; they
                    # fold into the main (kurant) table, interleaved by year
                    # (the phase was already year-sorted above), and are marked
                    # per-row in the template via `raw.kind == "gedenk"`.
                    pg.kurant_coins.append(cc)
            
            sg.phases.append(pg)

        # Hide the `seed_unsorted` catch-all placeholder when it's
        # empty — once a location's Bulk-seed has been fully
        # classified, the placeholder section is just noise. The
        # phase / fuss definitions themselves stay in
        # `data/locations/<loc>.yml` as a safety-net for future
        # seed imports that bring in unclassified coins (the block
        # then re-appears automatically next build).
        #
        # Real Müntzfüße that were legally in force on the territory
        # but where nothing was minted in this period stay visible —
        # the absence of mintage is itself meaningful historical
        # signal (e.g. a Müntzfuß formally adopted at a location
        # but never struck there), not a reason to hide.
        if fuss_id == "seed_unsorted" and not sg.has_any_coin:
            continue
        tree.fuesse.append(sg)

    return tree
