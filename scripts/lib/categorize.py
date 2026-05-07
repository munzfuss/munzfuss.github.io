"""
Layer B → C: group computed coins into the render-ready tree.

Produces nested structure: location → fuss → phase → kind → coins (sorted).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from .compute import ComputedCoin
from .schema import Location, Phase, Fuss


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


@dataclass
class LocationTree:
    """Full categorized tree for a location."""
    location: Location
    fuesse: list[FussGroup] = field(default_factory=list)


def compute_coin_year_runs(
    bars: list,
    computed_coins: list,
    tl_year_from: int,
    tl_year_to: int,
) -> dict[str, list[dict]]:
    """For each timeline bar, collect the set of years when at least one
    coin was minted under that stope (per the location's coin entries),
    collapse consecutive years into runs, and pre-compute left% / width%
    for the timeline track.

    A run has shape `{"first": int, "last": int, "coin_count": int,
    "state": str, "left_pct": float, "width_pct": float}`. Each year a
    `Coin` covers (year_first through year_last inclusive, or just
    year_first if year_last is None) counts as one minting year for its
    `fuss`.

    Runs collapse consecutive years OF THE SAME `state` — where state is
    either the year's single distinct issuing entity (`"royal_holstein"`,
    `"gottorp_duchy"`, …) or the sentinel `"shared"` for years where
    coins from more than one entity were minted (or where some coin
    lacks an `issuing_entity` so the year cannot be cleanly attributed
    to a single authority). A change of state breaks a run.

    This split lets the renderer paint each year-marker in its issuing
    entity's colour and merges multi-entity years into a neutral band,
    while still merging consecutive same-state years to keep the DOM
    small.
    """
    SHARED = "shared"
    out: dict[str, list[dict]] = {}
    tl_span = tl_year_to - tl_year_from
    if tl_span <= 0:
        return out

    # Map fuss_id → year → entity_id (or None) → set of coin IDs.
    # The full mapping per (fuss, year) lets us derive the year's state
    # (single entity vs shared) AND count distinct coins per run, all
    # without ever leaving the source `Coin` records.
    by_fuss_year_ent: dict[str, dict[int, dict[str | None, set[str]]]] = {}
    for cc in computed_coins:
        c = cc.raw
        # If the coin specifies sparse `year_ranges`, iterate only those
        # sub-spans (so a 1625-1657 cataloged coin actually struck only
        # 1625-1626, 1635-1636, 1656-1657 leaves the gap years bare).
        # Otherwise fall back to a single [year_first, year_last] span.
        if c.year_ranges:
            ranges_iter = [(int(r[0]), int(r[1])) for r in c.year_ranges]
        else:
            yl = c.year_last if c.year_last is not None else c.year_first
            f, l = (c.year_first, yl) if yl >= c.year_first else (yl, c.year_first)
            ranges_iter = [(f, l)]
        years_ent = by_fuss_year_ent.setdefault(c.fuss, {})
        ent = c.issuing_entity  # may be None
        for first, last in ranges_iter:
            for y in range(first, last + 1):
                if tl_year_from <= y <= tl_year_to:
                    ent_map = years_ent.setdefault(y, {})
                    ent_map.setdefault(ent, set()).add(c.id)

    def _state_for(ent_map: dict) -> str:
        """A year is `entity_id` if it has exactly one distinct entity
        and no `None`-entity coin (an unattributed coin still poisons the
        year into `shared`); otherwise it's `shared`. The latter covers:
        - 2+ distinct entities in the same year
        - 1+ entity plus an unattributed coin
        - all coins unattributed (no clean entity → use neutral colour).
        """
        if len(ent_map) == 1:
            only = next(iter(ent_map.keys()))
            return only if only is not None else SHARED
        return SHARED

    def _collect_coins(ent_map: dict) -> set[str]:
        s: set[str] = set()
        for v in ent_map.values():
            s |= v
        return s

    def _accumulate(target: dict, source: dict) -> None:
        """Merge source `{entity_id_or_None → coin_id_set}` into target."""
        for ent, ids in source.items():
            target.setdefault(ent, set()).update(ids)

    def _close_run(start: int, end: int, state: str,
                   ent_sets: dict) -> dict:
        """Build a run dict from accumulated per-entity coin sets.

        For a run whose original entities are O = {e1, e2, …}, generate
        a list of `variants` — one per non-empty subset of O (so 2^|O|−1
        variants). At render time each variant becomes its own DOM div
        sharing the same `[left_pct, width_pct]`; JS toggles visibility
        per the «highest-match» rule: variant V is shown iff
        `V == checked ∩ O` (and at least one of O is checked).

        Single-entity runs: |O| = 1 → exactly one variant.
        Shared runs:        |O| > 1 → 2^|O|−1 variants, allowing any
                                       subset of selected filters to
                                       address the rect precisely.
        """
        sorted_counts = sorted(
            ((ent, len(s)) for ent, s in ent_sets.items()),
            key=lambda x: (-x[1], x[0] or ""),
        )
        counts_map = {ent: cnt for ent, cnt in sorted_counts}
        # Sorted alphabetically — same canonical order used by the JS
        # `data-ents` / `data-orig` comparison (sorted-comma-join).
        non_none_ents = sorted(e for e in counts_map if e is not None)

        variants: list[dict] = []
        for r in range(1, len(non_none_ents) + 1):
            for subset in combinations(non_none_ents, r):
                variants.append({
                    "entities": list(subset),
                    "entity_counts": [(e, counts_map[e]) for e in subset],
                })

        return {
            "first": start,
            "last": end,
            "state": state,
            "entity_counts": sorted_counts,
            "coin_count": sum(len(s) for s in ent_sets.values()),
            "orig_entities": non_none_ents,
            "variants": variants,
        }

    for bar in bars:
        years_ent = by_fuss_year_ent.get(bar.id, {})
        if not years_ent:
            out[bar.id] = []
            continue

        years = sorted(years_ent.keys())
        runs: list[dict] = []
        start = prev = years[0]
        cur_state = _state_for(years_ent[start])
        ent_sets: dict[str | None, set[str]] = {}
        _accumulate(ent_sets, years_ent[start])

        for y in years[1:]:
            y_state = _state_for(years_ent[y])
            if y == prev + 1 and y_state == cur_state:
                prev = y
                _accumulate(ent_sets, years_ent[y])
            else:
                runs.append(_close_run(start, prev, cur_state, ent_sets))
                start = prev = y
                cur_state = y_state
                ent_sets = {}
                _accumulate(ent_sets, years_ent[y])
        runs.append(_close_run(start, prev, cur_state, ent_sets))

        # The rect for year Y spans [Y, Y+1) on the timeline so that
        # a single year reads as a 1-year-wide tick, and a run of
        # N consecutive years reads as an N-year-wide band with no
        # gap between adjacent runs.
        for r in runs:
            raw_left  = (r["first"] - tl_year_from) / tl_span * 100
            raw_right = (r["last"]  - tl_year_from + 1) / tl_span * 100
            cl = max(raw_left, 0.0)
            cr = min(raw_right, 100.0)
            r["left_pct"]  = round(cl, 3)
            r["width_pct"] = round(cr - cl, 3)

        out[bar.id] = runs

    return out


# --- Holstein-scope label ---
#
# Schleswig and Holstein operated as a single monetary unit throughout the
# 1559–1914 period this project documents: royal-Danish issues 1544–1864
# from any of the joint mints (Glückstadt, Altona, Tönning, Schleswig,
# Rendsburg) were legal tender in BOTH duchies under joint administration
# (Deutsche Kanzlei → Schleswig-Holsteinische Regierung); Reich /
# Vereinsthaler / Goldmark standards 1559–1914 covered both as members of
# HRR / Deutscher Bund / Province Schleswig-Holstein. The physical mint
# city is a topographic detail, not the coinage's territorial scope.
#
# We therefore label every holstein-scope layer as `tl.scope.schleswig_holstein`
# («Шлезвіг-Гольштейн»). The earlier mint-city classifier conflated mint
# topology with coinage scope; this default is the historically correct
# unit of abstraction. Per-bar overrides can be added later via a TimelineBar
# field if a future bar genuinely covers a narrower scope (e.g. Sonderburg-
# Plön ducal coinage), but no such bars exist today.


def derive_holstein_mint_overrides(loc: Location, fuesse: dict) -> dict:
    """Auto-sync `events.first_mint.holstein` / `last_mint.holstein` per
    Fuß to the actual coin span on a Holstein-scope page.

    Returns a NEW dict `{fuss_id -> Fuss-with-overridden-events}` — only
    Fuß systems whose synced span differs from the existing event range
    appear in the result; the rest of the global `fuesse` dict is left
    untouched. Callers should merge this dict over the original before
    handing it to `compute_bar_layers`.

    Rules
      * Only locations whose mint scope coincides with the events'
        `holstein` axis run through this — currently only
        `schleswig_holstein` (Schleswig + Holstein operated as one
        monetary unit; the schema's `holstein` scope means this).
      * **Full sync** — the data is authoritative. If our YAML's earliest
        SH-coin under a Fuß is 1645 but `events.first_mint.holstein` was
        set to 1644 (the patent year, before any physical strike), we
        sync down to 1645. Curator-set values that conceptually predate
        the first strike (decree / adoption year) belong in
        `first_adoption.holstein`, not `first_mint.holstein`.
      * Existing `None`s stay `None`. A Fuß whose curator explicitly
        marked `holstein = None` ("never minted in Holstein") is
        respected; we don't promote `None` to the data-derived range,
        even if a coin slipped into the SH yaml. That keeps the curated
        narrative authoritative. Stray cases surface elsewhere
        (audit_year_ranges etc.).
      * `approx_holstein` clears when we override — the data is
        empirical, not approximate.
    """
    if loc.id != "schleswig_holstein":
        return {}

    spans: dict[str, list[int | None]] = {}
    for c in loc.coins:
        if c.year_first is None:
            continue
        yl = c.year_last if c.year_last is not None else c.year_first
        cur = spans.setdefault(c.fuss, [c.year_first, yl])
        if c.year_first < cur[0]:
            cur[0] = c.year_first
        if yl > cur[1]:
            cur[1] = yl

    overrides: dict = {}
    for fid, (cmin, cmax) in spans.items():
        f = fuesse.get(fid)
        if f is None or f.events is None:
            continue
        ev = f.events
        fm = ev.first_mint
        lm = ev.last_mint
        # Skip Fuß systems whose Holstein-mint axis is curator-set None
        # (e.g. Copenhagen-only kronemont_chr_iv / kronemont_fine).
        if fm is None or fm.holstein is None or lm is None or lm.holstein is None:
            continue
        # Data is authoritative for both endpoints — sync, don't merge.
        new_fm_h = cmin
        new_lm_h = cmax
        if new_fm_h == fm.holstein and new_lm_h == lm.holstein:
            continue  # already in sync
        # Pydantic v2: model_copy(deep=True) on the whole Fuss is the
        # cleanest way to avoid mutating the global registry.
        new_f = f.model_copy(deep=True)
        if new_f.events.first_mint.holstein != new_fm_h:
            new_f.events.first_mint.holstein = new_fm_h
            new_f.events.first_mint.approx_holstein = False
        if new_f.events.last_mint.holstein != new_lm_h:
            new_f.events.last_mint.holstein = new_lm_h
            new_f.events.last_mint.approx_holstein = False
        overrides[fid] = new_f
    return overrides


def compute_bar_layers(
    bars: list,
    fuesse: dict,
    tl_year_from: int,
    tl_year_to: int,
    scope_mode: str = "dual",
) -> dict[str, list[dict]]:
    """For each timeline bar, derive the up-to-six period × scope layers
    (mint × {anywhere, holstein}, status × {anywhere, holstein},
    circulation × {anywhere, holstein}) from its `events` block, falling
    back to the matching Fuss in `fuesse` when the bar itself doesn't carry
    events. Returns a dict `bar_id → [layer, ...]` sorted by length DESC
    (longest first → bottom of the visual stack), with `left_pct` /
    `width_pct` pre-computed for the timeline track.

    A layer has shape:
      {
        "kind":      "mint" | "status" | "circulation",
        "scope":     "anywhere" | "holstein",
        "first":     int,
        "last":      int,
        "length":    int,                 # last - first
        "left_pct":  float (0..100),
        "width_pct": float (0..100),
        "scope_label_key": "tl.scope.schleswig_holstein",
      }

    Holstein-scope layers are always labelled «Schleswig-Holstein» — see
    the module-level comment above this function for the historical
    rationale (Schleswig + Holstein operated as a joint monetary unit
    throughout 1559–1914; mint topology ≠ coinage scope).

    Layers with first/last == None (e.g. holstein-side of a Copenhagen-only
    standard, or no-local-mint stopes like Vereinsthaler in H) are skipped
    — the result only contains layers that have a real year range.
    """
    out: dict[str, list[dict]] = {}
    tl_span = tl_year_to - tl_year_from
    if tl_span <= 0:
        return out

    for bar in bars:
        events = getattr(bar, "events", None)
        if events is None and bar.id in fuesse:
            events = getattr(fuesse[bar.id], "events", None)
        if events is None:
            out[bar.id] = []
            continue

        # Holstein-scope label: see the module-level comment above
        # `compute_bar_layers`. Schleswig + Holstein operated as a single
        # monetary unit throughout 1559–1914 — the holstein-scope is
        # always labelled «Schleswig-Holstein» on this page.
        scope_label_key = "tl.scope.schleswig_holstein"

        layers: list[dict] = []
        anywhere_label = getattr(events, "anywhere_label", None)

        # Per-bar `truncate_anywhere_after` (e.g. 1866 for Danish-Helstaten
        # stopes on the Holstein page) — sharply caps the anywhere-scope's
        # `last` year and drops layers whose `first` is already past it.
        # Holstein-scope layers are unaffected (they already terminate in
        # their own `events`). When None, no truncation is applied.
        trunc_any = getattr(bar, "truncate_anywhere_after", None)
        # Per-kind override: a dict {kind: int} that supersedes the bar-
        # wide `truncate_anywhere_after` for specific layer kinds. Lets
        # mint/status/circulation/sole each have its own cutoff year on
        # the same bar (e.g. 9-Fuß: mint+status=1667, circulation=1700).
        trunc_any_by_kind = getattr(bar, "truncate_anywhere_after_by_kind", None) or {}

        # `scope_mode` = "denmark_only": iterate only the anywhere scope and
        # suppress holstein-scope layers entirely (Denmark page where
        # Holstein is not a separate sub-track). Default "dual": both scopes.
        active_scopes = ("anywhere",) if scope_mode == "denmark_only" else ("anywhere", "holstein")

        # Per-bar `hide_anywhere`: drop the anywhere scope from this bar
        # only (e.g. on the Holstein page, the 9-Thaler-Fuß bar — its
        # anywhere extent is Reich-/Hanseatic-wide and distracts from
        # the Holstein-narrative). Underlying events in fuesse.yml stay
        # intact; this is a per-page visibility flag.
        if getattr(bar, "hide_anywhere", False):
            active_scopes = tuple(s for s in active_scopes if s != "anywhere")

        # Per-bar `hide_layers`: granular (scope, kind) suppression.
        # Finer-grained than `hide_anywhere` — used e.g. on Krone bars
        # to drop just the anywhere-circulation layer while keeping
        # anywhere-mint and anywhere-status visible.
        hidden_pairs = {
            (h.scope, h.kind) for h in (getattr(bar, "hide_layers", None) or [])
        }

        def _add(kind, scope, start_event, end_event):
            """Pull (year, approx) for one scope from a (start, end) event pair."""
            if (scope, kind) in hidden_pairs:
                return  # explicitly suppressed by hide_layers
            if start_event is None or end_event is None:
                return
            first = getattr(start_event, scope)
            last = getattr(end_event, scope)
            if first is None or last is None:
                return
            first_approx = getattr(start_event, f"approx_{scope}", False)
            last_approx = getattr(end_event, f"approx_{scope}", False)
            # Per-bar anywhere-scope truncation (sharp cutoff, not approx).
            # Per-kind override beats the bar-wide value; otherwise fall back.
            effective_trunc = trunc_any_by_kind.get(kind, trunc_any)
            if scope == "anywhere" and effective_trunc is not None:
                if first > effective_trunc:
                    return  # layer entirely past the cutoff — drop
                if last > effective_trunc:
                    last = effective_trunc
                    last_approx = False
            layers.append({
                "kind": kind,
                "scope": scope,
                "first": first,
                "last": last,
                "length": last - first,
                "first_approx": first_approx,
                "last_approx": last_approx,
                "anywhere_label": anywhere_label,  # I18nText | None — per-stope label
                "scope_label_key": scope_label_key,
            })

        # mint = [first_mint, last_mint]
        fm, lm = events.first_mint, events.last_mint
        for scope in active_scopes:
            _add("mint", scope, fm, lm)

        # status = [first_adoption, std_end]
        fa, se = events.first_adoption, events.std_end
        for scope in active_scopes:
            _add("status", scope, fa, se)

        # circulation = [first_adoption, demonetisation]
        de_ = events.demonetisation
        for scope in active_scopes:
            _add("circulation", scope, fa, de_)

        # sole = [sole_start, sole_end] — OPTIONAL. Always emit when both
        # endpoints are defined; the layer-merge step below will combine
        # any layers whose (scope, first, last) coincide so a sole-period
        # identical to status doesn't render as two overlapping bars but
        # as a single bar with combined tooltip («Чинний стандарт + Єдиний
        # стандарт · …»).
        ss, se_sole = events.sole_start, events.sole_end
        if ss is not None and se_sole is not None:
            for scope in active_scopes:
                _add("sole", scope, ss, se_sole)

        # Layer merging: bars with identical (scope, first, last) span
        # would render as visual duplicates that overlap perfectly,
        # showing only one tooltip on hover. Common case: when std_end
        # equals demonetisation, status and circulation layers fully
        # coincide (e.g. reichsdukatenfuss anywhere 1559-1876 — both
        # status and circulation share that span). Merge such groups
        # into a single layer carrying all coinciding kinds in `kinds`,
        # which the template joins with « + » in the tooltip («Чинний
        # стандарт + В обігу · … · 1559—1876»).
        _SCOPE_PRIORITY = {"anywhere": 0, "holstein": 1}
        _KIND_PRIORITY = {"circulation": 0, "status": 1, "mint": 2, "sole": 3}

        groups: dict[tuple, list[dict]] = {}
        for layer in layers:
            key = (layer["scope"], layer["first"], layer["last"])
            groups.setdefault(key, []).append(layer)
        merged_layers: list[dict] = []
        for grp in groups.values():
            if len(grp) == 1:
                grp[0]["kinds"] = [grp[0]["kind"]]
                merged_layers.append(grp[0])
                continue
            # Multiple layers at the same span — merge. Use the highest-
            # priority kind for CSS class & sort key (so the merged bar
            # behaves identically to the most-specific layer it absorbs).
            grp.sort(key=lambda l: -_KIND_PRIORITY[l["kind"]])
            base = dict(grp[0])
            base["kinds"] = [l["kind"] for l in grp]
            # Preserve the intent-preserving order: render kinds in
            # priority order so the most specific reads first in the
            # tooltip («Єдиний стандарт + Чинний стандарт + В обігу»).
            merged_layers.append(base)
        layers = merged_layers

        # Sort layers so the rendered DOM order = bottom-to-top stacking,
        # with the topmost layer winning hover at any overlap point.
        #
        # Primary key: length DESC — the longest layer goes to the bottom,
        #   the shortest to the top. (Shorter usually = more specific
        #   to the position the user hovered.)
        # Secondary key: scope (holstein > anywhere) — for equal-length
        #   layers, the project-focused Holstein scope wins.
        # Tertiary key: kind (mint > status > circulation) — for equal
        #   length AND equal scope, the most concrete fact (mint) is
        #   what the user wants to see; status and circulation are
        #   semantically subordinate. After merging, kind = highest-
        #   priority of the merged set.
        layers.sort(key=lambda l: (
            -l["length"],
            _SCOPE_PRIORITY[l["scope"]],
            _KIND_PRIORITY[l["kind"]],
        ))

        for l in layers:
            # `last + 1` because a year is a 1-year-wide block, not a
            # point on the axis: a layer running through year 1696 must
            # cover [1696, 1697) so its right edge lines up with the
            # right edge of a year-mintage marker for the same year
            # (which uses the same `+1` convention in compute_coin_year_runs).
            raw_left  = (l["first"]    - tl_year_from) / tl_span * 100
            raw_right = (l["last"] + 1 - tl_year_from) / tl_span * 100
            cl = max(raw_left, 0.0)
            cr = min(raw_right, 100.0)
            l["left_pct"]  = round(cl, 2)
            l["width_pct"] = round(cr - cl, 2)

        out[bar.id] = layers

    return out


def compute_hover_zones(
    bar_layers: dict[str, list[dict]],
    tl_year_from: int,
    tl_year_to: int,
) -> dict[str, list[dict]]:
    """For each bar, segment its timeline span into 'hover zones' — year
    ranges across which the active layer set stays constant. The
    template renders one transparent overlay div per zone with a static
    `data-tooltip` aggregating every active layer's text. Browser-native
    `:hover::after` then renders the joined tooltip without any
    JavaScript coordination — eliminating the rapid-mousemove flicker
    that arose when a single tooltip was being live-rebuilt on every
    cursor pixel.

    Algorithm:
      1. Collect breakpoints from each layer's `first` and `last + 1`.
      2. For each consecutive pair (bp[i], bp[i+1]-1), derive the active
         layer indices = layers whose [first, last] interval contains
         that whole sub-range.
      3. Drop zones with no active layers (dead space inside the bar).
      4. Compute % positions identical to compute_bar_layers (`last + 1`
         for the right edge — a year is a 1-year-wide block).

    Returned dict shape: `bar_id → [zone, ...]`, each zone:
      {
        "first":         int,
        "last":          int,
        "layer_indices": [int, ...],   # indices into bar_layers[bar_id]
        "left_pct":      float (0..100),
        "width_pct":     float (0..100),
      }
    """
    out: dict[str, list[dict]] = {}
    tl_span = tl_year_to - tl_year_from
    if tl_span <= 0:
        return out

    for bar_id, layers in bar_layers.items():
        if not layers:
            out[bar_id] = []
            continue
        bps: set[int] = set()
        for l in layers:
            bps.add(l["first"])
            bps.add(l["last"] + 1)
        sorted_bps = sorted(bps)

        # Cumulative band of all layers in this bar (the visual envelope —
        # min left to max right across all layers). The tooltip is anchored
        # at the centre of this band so it sits at one stable x-position
        # regardless of which sub-zone the cursor is currently inside —
        # the «cumulative layer» the user sees as a single continuous
        # multi-coloured strip.
        cum_left = min(l["left_pct"] for l in layers)
        cum_right = max(l["left_pct"] + l["width_pct"] for l in layers)
        cum_center_pct = (cum_left + cum_right) / 2.0

        zones: list[dict] = []
        for i in range(len(sorted_bps) - 1):
            zfirst = sorted_bps[i]
            zlast = sorted_bps[i + 1] - 1
            if zlast < zfirst:
                continue
            active_idx = [
                j for j, l in enumerate(layers)
                if l["first"] <= zfirst and l["last"] >= zlast
            ]
            if not active_idx:
                continue
            raw_left = (zfirst - tl_year_from) / tl_span * 100
            raw_right = (zlast + 1 - tl_year_from) / tl_span * 100
            cl = max(raw_left, 0.0)
            cr = min(raw_right, 100.0)
            zone_w = cr - cl
            # tt_offset_pct = where the cumulative-band centre falls inside
            # this zone, expressed as a % of the zone's own width (the unit
            # that ::after's `left:` interprets relative to its trigger).
            # Negative or >100 values are valid — they mean the tooltip
            # centre sits outside the current zone's rect (CSS happily
            # positions absolutely-placed children outside their parent).
            if zone_w > 0:
                tt_offset_pct = (cum_center_pct - cl) / zone_w * 100.0
            else:
                tt_offset_pct = 50.0
            zones.append({
                "first": zfirst,
                "last": zlast,
                "layer_indices": active_idx,
                "left_pct": round(cl, 2),
                "width_pct": round(zone_w, 2),
                "tt_offset_pct": round(tt_offset_pct, 2),
            })
        out[bar_id] = zones

    return out


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
        
        sg = FussGroup(fuss=fuesse[fuss_id])
        
        for phase in location.phases[fuss_id]:
            pg = PhaseGroup(phase=phase)
            coins_in_phase = idx.get((fuss_id, phase.id), [])
            coins_in_phase.sort(key=lambda c: (c.raw.year_first, c.raw.id))
            
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
                    pg.gedenk_coins.append(cc)
            
            sg.phases.append(pg)
        
        tree.fuesse.append(sg)

    return tree
