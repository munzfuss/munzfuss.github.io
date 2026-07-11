"""
Timeline-rendering helpers — derived from coin records and Fuss `events`,
turn each location's timeline-bar list into the geometric / categorised
data that location.html.j2 paints into period × scope layers, per-year
mintage markers, and hover-zone overlays.

Four entry points (called from `scripts/build.py:build_location` —
`categorize.py` no longer touches them):

  * `derive_mint_overrides(loc, fuesse)` — auto-syncs each Fuß's
    `events.first_mint.<scope>` / `last_mint.<scope>` to the actual
    coin span on this page, where `<scope>` is the scope that
    represents the page's own coins: `holstein` on the SH page,
    `anywhere` on a `denmark_only`-scope page (Denmark). Returns a
    `{fuss_id -> Fuss}` overlay; other locations are no-ops.

  * `compute_bar_layers(bars, fuesse, year_from, year_to, scope_mode)` —
    derives the up-to-six (mint × {anywhere, holstein}, status × …,
    circulation × …) layers per bar with their `left%` / `width%`
    pre-computed for the timeline track.

  * `compute_coin_year_runs(bars, computed_coins, year_from, year_to)` —
    per-bar consecutive-year runs marking every year a coin was actually
    minted under that stope (per location YAML). Powers the 1-year-wide
    rectangle markers overlaid on the layered period × scope bar.

  * `compute_hover_zones(bar_layers, year_from, year_to)` — segments each
    bar's span into ranges where the active layer set stays constant,
    each rendered as a transparent overlay div with a static `data-tooltip`
    aggregating all active layers' texts.

Holstein-scope label rule
-------------------------
Schleswig and Holstein operated as a single monetary unit throughout the
1559-1914 period this project documents: royal-Danish issues 1544-1864
from any of the joint mints (Glückstadt, Altona, Tönning, Schleswig,
Rendsburg) were legal tender in BOTH duchies under joint administration
(Deutsche Kanzlei → Schleswig-Holsteinische Regierung); Reich /
Vereinsthaler / Goldmark standards 1559-1914 covered both as members of
HRR / Deutscher Bund / Province Schleswig-Holstein. The physical mint
city is a topographic detail, not the coinage's territorial scope.

We therefore label every holstein-scope layer as
`tl.scope.schleswig_holstein` («Шлезвіг-Гольштейн»). Per-bar overrides
can be added later via a TimelineBar field if a future bar genuinely
covers a narrower scope (e.g. Sonderburg-Plön ducal coinage), but no
such bars exist today.
"""
from __future__ import annotations

from itertools import combinations

from .schema import Location


__all__ = [
    "derive_mint_overrides",
    "compute_bar_layers",
    "compute_coin_year_runs",
    "compute_hover_zones",
]


def _mint_sync_scope(loc: Location) -> str | None:
    """The mint-event scope that this page's own coins represent, or None
    if this location has no data-driven mint axis.

    * `denmark_only`-scope page (Denmark) → `anywhere`: the timeline shows
      only the anywhere scope, scoped to the Kingdom of Denmark, so its
      mint layer = the Denmark coins' span.
    * Schleswig-Holstein → `holstein`: Schleswig + Holstein operated as one
      monetary unit (the schema's `holstein` scope means this); the page's
      `anywhere` layer is the Reich-wide curated span and is NOT data-driven.
    * Any other location → None (no-op).
    """
    tl = getattr(loc, "timeline", None)
    if tl is not None and getattr(tl, "scope_mode", None) in ("denmark_only", "anywhere_only"):
        return "anywhere"
    if loc.id == "schleswig_holstein":
        return "holstein"
    return None


def founding_mint_start(
    reign_min: int | None,
    dated_min: int | None,
    adoption_year: int | None,
    firm: bool,
) -> tuple[int | None, bool]:
    """Founding-era mint/phase START rule (curator direction 2026-07-10).

    A standard whose earliest coin carries a reign-window placeholder year
    (`year_is_reign_span` — exact mint year unknown, only the ruler's reign)
    must not silently start at the nearest DATED coin, ignoring that the reign
    coin was demonstrably struck earlier. Two sub-rules, keyed on whether the
    founding anchor (`first_adoption`) is FIRM:

      * firm (a dated ordinance / Møntordning, or a curator-certain de-facto
        start) → HARD-clip the start to the founding year: the reign coin's
        spill before it is cut off and the edge is sharp (no fade), the
        founding decree giving legal certainty.  → (founding_year, approx=False)
      * not firm (uncertain de-facto estimate) → start from the reign coin's
        OWN earliest year WITH the uncertainty fade: it was struck around then,
        just not exactly when.                    → (reign_year, approx=True)

    Returns `(start_year, approx)`. When no reign-span coin is earlier than the
    earliest dated coin the dated start is returned unchanged (approx=False) —
    the rule is a no-op for the common case. Shared by `derive_mint_overrides`
    (the timeline mint stripe) and `build._expand_outer_phase_span` (the phase
    table) so both surfaces resolve a founding-era start identically.

    Args
      reign_min     earliest `year_is_reign_span` coin year_first (or None)
      dated_min     earliest NON-reign coin year_first (None if all reign-span)
      adoption_year `first_adoption.<scope>` — the founding anchor (or None)
      firm          `first_adoption.firm_<scope>` — True → hard clip, False → fade
    """
    if reign_min is None:
        return dated_min, False
    if dated_min is not None and reign_min >= dated_min:
        return dated_min, False   # a dated coin is at/before the reign coin — no-op
    if firm and adoption_year is not None:
        start = max(reign_min, adoption_year)          # Rule 1 — clip reign spill to founding
        if dated_min is not None:
            start = min(dated_min, start)
        return start, False                            # hard edge
    start = reign_min                                  # Rule 2 — fade from the reign coin
    if dated_min is not None:
        start = min(dated_min, start)
    return start, True


def derive_mint_overrides(loc: Location, fuesse: dict) -> dict:
    """Auto-sync each Fuß's `events.first_mint.<scope>` / `last_mint.<scope>`
    to the actual coin span on this page, where `<scope>` is the scope that
    represents the page's own coins (see `_mint_sync_scope`): `holstein` on
    the SH page, `anywhere` on a `denmark_only`-scope page (Denmark).

    Returns a NEW dict `{fuss_id -> Fuss-with-overridden-events}` — only
    Fuß systems whose synced span differs from the existing event range
    appear in the result; the rest of the global `fuesse` dict is left
    untouched. Callers should merge this dict over the original before
    handing it to `compute_bar_layers`. The override is ephemeral (per
    render) — `data/shared/fuesse.yml` is never written, so the curated
    *global* `anywhere` values other surfaces rely on are unaffected.

    Rules
      * **Full sync** — the data is authoritative. If our YAML's earliest
        coin under a Fuß is 1645 but `events.first_mint.<scope>` was set to
        1644 (the patent year, before any physical strike), we sync down to
        1645. Curator-set values that conceptually predate the first strike
        (decree / adoption year) belong in `first_adoption.<scope>`, not
        `first_mint.<scope>` — so status / circulation layers are untouched.
      * Existing `None`s stay `None`. A Fuß whose curator explicitly marked
        this scope's mint endpoint `None` ("never minted here") is respected;
        we don't promote `None` to the data-derived range, even if a coin
        slipped into the page's yaml. Stray cases surface elsewhere
        (audit_year_ranges etc.).
      * `approx_<scope>` clears when we override — the data is empirical,
        not approximate.
    """
    scope = _mint_sync_scope(loc)
    if scope is None:
        return {}

    spans: dict[str, list[int | None]] = {}   # fuss -> [dated_cmin, cmax]  (non-reign)
    reign_min: dict[str, int] = {}            # fuss -> earliest reign-span coin year_first
    for c in loc.coins:
        if c.year_first is None:
            continue
        # A coin whose year IS a ruler's reign window (year_is_reign_span,
        # «1588-1648» Christian IV — exact mint year unknown) does NOT define a
        # physical-mint END (year_last is a reign bound, not a strike) nor the
        # non-reign start. But its year_first DOES feed the founding-era START
        # rule (founding_mint_start below): so a founding-era standard whose
        # earliest coin is a reign placeholder isn't silently pulled forward to
        # the nearest dated coin (curator direction 2026-07-10). An imprecise-
        # but-narrow year_verified:false estimate («1496-1497 (?)») is NOT a
        # reign span and flows through the normal `spans` path.
        if getattr(c, "year_is_reign_span", False) is True:
            rm = reign_min.get(c.fuss)
            if rm is None or c.year_first < rm:
                reign_min[c.fuss] = c.year_first
            continue
        yl = c.year_last if c.year_last is not None else c.year_first
        cur = spans.setdefault(c.fuss, [c.year_first, yl])
        if c.year_first < cur[0]:
            cur[0] = c.year_first
        if yl > cur[1]:
            cur[1] = yl

    approx_attr = f"approx_{scope}"
    firm_attr = f"firm_{scope}"
    overrides: dict = {}
    for fid, (dated_cmin, cmax) in spans.items():
        f = fuesse.get(fid)
        if f is None or f.events is None:
            continue
        ev = f.events
        fm = ev.first_mint
        lm = ev.last_mint
        fa = ev.first_adoption
        # Skip Fuß systems whose mint axis for this scope is curator-set
        # None (e.g. Copenhagen-only fusses have holstein=None; a fuss
        # with no anywhere mint span would be anywhere=None).
        if (fm is None or getattr(fm, scope) is None
                or lm is None or getattr(lm, scope) is None):
            continue
        # Founding-era reign-span START rule (2026-07-10). When the earliest
        # coin under this fuss is a reign-window placeholder earlier than any
        # dated coin, `founding_mint_start` resolves the start: a FIRM founding
        # hard-clips to the adoption year (no fade), a non-firm de-facto one
        # starts from the reign coin's year WITH the fade. Otherwise it returns
        # `dated_cmin` unchanged.
        adoption_year = getattr(fa, scope) if fa is not None else None
        firm = getattr(fa, firm_attr, True) if fa is not None else True
        cmin, cmin_approx = founding_mint_start(
            reign_min.get(fid), dated_cmin, adoption_year, firm)
        # Clamp only the UPPER bound to the timeline's right edge: a stripe
        # cannot render past year_to, so a tooltip year beyond it — a
        # 1913-1931 straddle type, or a reign-window placeholder masking a
        # post-1914 issue — would be misleading. The LOWER bound is left
        # alone: a coin minted before the window (nobel / rhinsk ~1496 while
        # the Denmark axis starts 1514) must keep its real start year in the
        # tooltip; compute_bar_layers already clamps the visual left edge.
        tl = loc.timeline
        if tl is not None:
            cmax = min(cmax, tl.year_to)
            if cmin is None or cmin > cmax:
                continue  # this fuss's coins fall entirely past the right edge
        # Data is authoritative for both endpoints — sync, don't merge. The
        # start's approx flag (fade) is part of the sync: a founding-era Rule 2
        # start renders faded, Rule 1 / a dated start renders sharp.
        if (cmin == getattr(fm, scope) and cmax == getattr(lm, scope)
                and cmin_approx == getattr(fm, approx_attr)):
            continue  # already in sync
        # Pydantic v2: model_copy(deep=True) on the whole Fuss is the
        # cleanest way to avoid mutating the global registry.
        new_f = f.model_copy(deep=True)
        if (getattr(new_f.events.first_mint, scope) != cmin
                or getattr(new_f.events.first_mint, approx_attr) != cmin_approx):
            setattr(new_f.events.first_mint, scope, cmin)
            setattr(new_f.events.first_mint, approx_attr, cmin_approx)
        if getattr(new_f.events.last_mint, scope) != cmax:
            setattr(new_f.events.last_mint, scope, cmax)
            setattr(new_f.events.last_mint, approx_attr, False)
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
    the module-level docstring for the historical rationale (Schleswig +
    Holstein operated as a joint monetary unit throughout 1559-1914;
    mint topology ≠ coinage scope).

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

        # Holstein-scope label: see module-level docstring for the
        # historical rationale (joint monetary unit 1559-1914).
        scope_label_key = "tl.scope.schleswig_holstein"

        layers: list[dict] = []
        # Per-bar `anywhere_label` override wins over the Fuß's GLOBAL
        # events.anywhere_label — lets a single page re-word the circulation-
        # scope tooltip (e.g. drop a Denmark mention that is out-of-place on
        # the German-Empire timeline) without touching data/shared/fuesse.yml.
        anywhere_label = getattr(bar, "anywhere_label", None) or getattr(events, "anywhere_label", None)

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
        # Per-bar `truncate_anywhere_before` — mirror for the LEFT edge: raise
        # the anywhere-scope's `first` up to this year, dropping layers whose
        # `last` is already before it. Used for context bars of standards whose
        # circulation predates this page's axis (Reichsdukat on the GE timeline).
        trunc_before = getattr(bar, "truncate_anywhere_before", None)
        # Per-kind FADED cap (mirror of trunc_any_by_kind but last_approx=True):
        # cap the anywhere-scope kind's `last` at the year WITH an uncertainty
        # fade instead of the sharp truncate cutoff.
        fade_any_by_kind = getattr(bar, "fade_anywhere_after_by_kind", None) or {}

        # `scope_mode` "denmark_only" / "anywhere_only": iterate only the
        # anywhere scope and suppress holstein-scope layers entirely (a single-
        # jurisdiction page — Denmark, or the German Empire — where Holstein is
        # not a separate sub-track). Default "dual": both scopes.
        active_scopes = ("anywhere",) if scope_mode in ("denmark_only", "anywhere_only") else ("anywhere", "holstein")

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
            if scope == "anywhere" and trunc_before is not None:
                if last < trunc_before:
                    return  # layer entirely before the cutoff — drop
                if first < trunc_before:
                    first = trunc_before
                    first_approx = False
            if scope == "anywhere" and kind in fade_any_by_kind:
                _fade_yr = fade_any_by_kind[kind]
                if first > _fade_yr:
                    return  # layer entirely past the faded cutoff — drop
                if last > _fade_yr:
                    last = _fade_yr
                    last_approx = True   # FADE-out (vs truncate's sharp cutoff)
            # Mission-scope visibility clip: if the actual start year is BEFORE
            # the timeline's left edge, the visible left edge of the layer is
            # the clip line (sharp cutoff), NOT the underlying uncertain year
            # — so the fade-start gradient would be misleading (it would
            # suggest uncertainty at the clip line itself, whereas the
            # uncertainty is hidden off-screen to the left). Symmetrical for
            # the right edge. Clear approx flags when the actual extent
            # extends past the visible window.
            if first < tl_year_from:
                first_approx = False
            if last > tl_year_to:
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
        # V2: `issuing_entity` can be a list (joint-jurisdiction coins
        # per V2_PIPELINE.md §3.10). Each element is recorded as a
        # separate ent-key in the year map so the «shared» rule (≥2
        # distinct entities in one year) fires naturally for joint-
        # mint years. Scalar form (V1 + 90% V2) is recorded once.
        ie = c.issuing_entity  # may be None or str or list[str]
        if isinstance(ie, list):
            ents_for_year = list(ie) if ie else [None]
        else:
            ents_for_year = [ie]
        for first, last in ranges_iter:
            for y in range(first, last + 1):
                if tl_year_from <= y <= tl_year_to:
                    ent_map = years_ent.setdefault(y, {})
                    for ent in ents_for_year:
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


def attach_visual_pieces(bar_layers: dict, hover_zones: dict) -> None:
    """Mutate `bar_layers` in place: for each layer carrying `first_approx`
    or `last_approx`, attach a `visual_pieces` list derived from the
    hover-zone segmentation. Each piece corresponds to one zone where the
    layer is active, with `show_fade_start` / `show_fade_end` flags set
    only when the zone is solo (only layer of its scope active) AND
    touches the layer's matching edge.

    Layers without any approx flag are skipped — they don't need split
    rendering and the template's default-single-piece fallback applies.

    Adjacent pieces with identical fade flags are merged to keep the
    rendered DOM lean.

    Rationale: the `.tl-bar-layer-fade-end::before` CSS mask gradient
    bleeds into the overlap zone when applied to a layer's full width;
    by emitting separate piece divs for the overlap region (no fade
    class) and the solo region (fade class), the mask only acts where
    the layer is actually the bar's visible end-strip.

    Operates symmetrically on `first_approx` (left edge) and
    `last_approx` (right edge).

    Args:
        bar_layers: dict `bar_id → [layer, ...]` from `compute_bar_layers`.
        hover_zones: dict `bar_id → [zone, ...]` from `compute_hover_zones`.
    """
    for bar_id, layers in bar_layers.items():
        zones = hover_zones.get(bar_id) or []
        if not zones:
            continue
        for layer_idx, L in enumerate(layers):
            fa = L.get("first_approx", False)
            la = L.get("last_approx", False)
            if not (fa or la):
                continue  # no fade flag → no visual_pieces needed

            pieces: list[dict] = []
            for z in zones:
                indices = z.get("layer_indices") or []
                if layer_idx not in indices:
                    continue
                # Solo-of-scope: only layer of L's scope active in this
                # zone. Anywhere-scope and holstein-scope layers don't
                # cross-shadow each other.
                same_scope_count = sum(
                    1 for i in indices
                    if 0 <= i < len(layers) and layers[i].get("scope") == L["scope"]
                )
                is_solo = (same_scope_count == 1)
                touches_lo = (z["first"] == L["first"])
                touches_hi = (z["last"]  == L["last"])
                pieces.append({
                    "left_pct":  z["left_pct"],
                    "width_pct": z["width_pct"],
                    "show_fade_start": fa and is_solo and touches_lo,
                    "show_fade_end":   la and is_solo and touches_hi,
                })

            if pieces:
                L["visual_pieces"] = _merge_adjacent_pieces(pieces)


def _merge_adjacent_pieces(pieces: list[dict]) -> list[dict]:
    """Collapse consecutive pieces with identical fade flags into one,
    summing their widths. Pieces are assumed to be in left-to-right order
    (hover_zones returns them sorted).
    """
    if not pieces:
        return pieces
    out: list[dict] = [dict(pieces[0])]
    for p in pieces[1:]:
        prev = out[-1]
        if (prev["show_fade_start"] == p["show_fade_start"]
                and prev["show_fade_end"] == p["show_fade_end"]):
            prev["width_pct"] = round(prev["width_pct"] + p["width_pct"], 2)
        else:
            out.append(dict(p))
    return out
