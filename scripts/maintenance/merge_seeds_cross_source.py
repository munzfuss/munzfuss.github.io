#!/usr/bin/env python3
"""V2 Phase 3.2 — cross-source merge of per-resource seeds into one
unified seed entry per physical coin.

Input  : data/v2/seed/<source>/<entity>.yml         (per-resource seeds)
Output : data/v2/seed_unified/<entity>.yml          (cross-source merged)
         data/v2/match_uncertainty/<entity>.yml     (gitignored — low-confidence)

Per docs/V2_PIPELINE.md §5.2, the matcher applies a strict-primary +
loose-fallback signal hierarchy:

  PRIMARY (all must match for confident auto-merge):
    1. Metal — with billon/silver normalisation when fineness < 0.5
    2. Nominal — verbatim string equality after period-spelling normalise
    3. Catalog index chain — refs cross-checked respecting scopes:
         KM restarts per Krause volume (use entity context)
         Hede restarts per ruler (use catalog.hede_volume)
         Sieg, Schou, Lange, Galster, MB also per-author/per-volume
    4. Ruler — canonical-form equality

  FALLBACK (loose — break ties, never sole signal):
    5. Year-range overlap (≥1 year)
    6. Fineness within ±5 %
    7. Mint overlap

Decisions:
  - All 4 primary match + ≥1 fallback consistent + 0 fallback inconsistent
      → confident auto-merge
  - All primary match + fallback disagrees (e.g. weights inconsistent)
      → low-confidence (surface for curator)
  - ≥3 primary match + remaining primary missing-not-disagreeing
      → low-confidence candidate
  - Primary mismatch → no_match

Curator decision surfaces:
  - data/v2/merge_decisions/<entity>.yml   (committed; authoritative)
      merges: list of {members: [seed_ids], reason: "..."}
      no_merges: list of {members: [seed_a, seed_b], reason: "..."}
  - data/v2/match_uncertainty/<entity>.yml (gitignored; diagnostic only)

Idempotent — fresh re-runs on unchanged input produce zero file changes
(deterministic id ordering + sorted output).

Unified entry id rule (V2_PIPELINE.md §5.2 authority-based):
  Priority order for source-id prefixes: dk-hede- > dk-bruun- >
  dk-numismaster- > dk-numista- > dk-galster-. The unified entry's id
  is `unified-<top-authority-member-id>`. Prefix prevents collision
  with the seed-side id; remains readable for debugging.

Usage:
  scripts/maintenance/merge_seeds_cross_source.py --dry-run    # report only
  scripts/maintenance/merge_seeds_cross_source.py --apply      # write outputs
  scripts/maintenance/merge_seeds_cross_source.py --entity X   # one entity
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2_SEED = ROOT / "data" / "v2" / "seed"
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_MERGE_DECISIONS = ROOT / "data" / "v2" / "merge_decisions"
V2_MATCH_UNCERTAINTY = ROOT / "data" / "v2" / "match_uncertainty"


# ---------------------------------------------------------------------------
# cf-form + unlisted detection — user policy 2026-05-18
# ---------------------------------------------------------------------------
# «cf. X» refs point at a similar OTHER coin, not at this entry's own
# catalogue index. «X-unlisted» is a negative claim («this coin is NOT
# in catalogue X»). Neither belongs in catalog columns. Filter at
# ingest in _deep_merge_catalog so future seeds carrying either shape
# (e.g. Bruun harvester reading Stack's-Bowers «Fr-cf. 3089» / Lange's
# «KM-unlisted») don't re-introduce them.
_SCALAR_CF_RE = re.compile(r"^\s*(?:cf\.?\s*\S|unlisted\s*$)", re.IGNORECASE)
_OTHERS_CF_RE = re.compile(
    r"^\s*[A-Za-zÄÖÜäöüß][\w./\- ]*?(?:[-\s]+cf\.?(?:\s|\d)|[-\s]+unlisted\b)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Authority order — V2_PIPELINE.md §5.2 choice (a) confirmed by user
# ---------------------------------------------------------------------------

_ID_AUTHORITY_ORDER = [
    "dk-hede-",          # Hede 1971 (primary scholarly DK)
    "dk-bruun-",         # Stack's Bowers Bruun auction
    "dk-numismaster-",   # Krause-Mishler canonical
    "dk-numista-",       # community Numista
    "dk-galster-",       # Galster pre-1541
]


def _authority_score(coin_id: str) -> int:
    """Higher = more authority. Used to choose unified id."""
    if not coin_id:
        return -1
    for i, prefix in enumerate(_ID_AUTHORITY_ORDER):
        if coin_id.startswith(prefix):
            return len(_ID_AUTHORITY_ORDER) - i
    return 0


# ---------------------------------------------------------------------------
# Catalog-ref scoping
# ---------------------------------------------------------------------------
#
# User-confirmed (chat 2026-05-18):
#   «KM різних локацій стартують з 1 (Ш-Г vs данія, наприклад) і тому може
#    бути клеш, внутрішньо треба розрізняти це КМ данії чи КМ Ш-Г.
#    Хеде теж клешить але per ruler — Хеде#1 рулера_1 і Хеде#1 рулера_2
#    це різні монети, як і KM-DK# 1 ≠ KM-SH# 1.»
#
# Within-entity matching: per-entity loop isolates KM volumes naturally
# (danish_realm coins compare only among themselves; royal_holstein
# coins likewise). But two failure modes survive within ONE entity:
#
#   1. Mixing bare-form `catalog.km: '75'` with dict-form
#      `catalog.km: {dk: '75'}` inside one entity. Same physical KM but
#      different dict-keys (`km` vs `km/dk`) → false no_overlap.
#      FIX: entity-aware register inference — translate bare KM to
#      `km/<inferred_register>` based on entity's natural Krause volume.
#
#   2. Bare-form `catalog.hede: '156'` (no `hede_volume`) within one
#      entity that spans multiple rulers. Christian IV's Hede-156 and
#      Frederik III's Hede-156 would false-match on bare key.
#      FIX: ruler-aware scoping — when `hede_volume` is absent, derive
#      scope from the coin's `ruler` field (normalised). Always present
#      from any non-trivial source; if both sides lack ruler too, fall
#      back to bare `hede` key (still risky but rare in practice).

_ENTITY_TO_KM_REGISTER: dict[str, str] = {
    # Danish-realm tracks Krause's «Denmark» volume
    "danish_realm": "dk",
    "danish_norway": "no",       # Krause has separate Norway volume
    # SH territory — Krause «German States — Schleswig-Holstein»
    "royal_holstein": "sh",
    "gottorp_duchy": "sh",
    "schauenburg_pinneberg": "sh",
    "sonderburg_duchy": "sh",
    "norburg_plon_duchy": "sh",
    "glucksburg_duchy": "sh",
    "rantzau_county": "sh",
    "provisional_govt": "sh",
    "holstein_schauenburg_county": "sh",
    # Other German entities — each has its own Krause volume, keep
    # registers explicit so cross-entity bleed (rare) doesn't false-match
    "fuerstbisthum_luebeck": "de-fbl",
    "hanseatic_hamburg": "de-hh",
    "hanseatic_lubeck": "de-hl",
    "erzbisthum_bremen_verden": "de-bv",
    "herzogtum_braunschweig_lueneburg": "de-bl",
    "herzogtum_sachsen_lauenburg": "de-sl",
    "grafschaft_oldenburg": "de-old",
    "hochstift_osnabrueck": "de-osnabr",
    "landgrafschaft_hessen_kassel": "de-hk",
    # No register — bare KM remains ambiguous within these synthetic buckets
    # "_unclassified": None,
    # "_deprecated_gesamtstaat": None,
}


# ---------------------------------------------------------------------------
# Field normalisation
# ---------------------------------------------------------------------------


def _normalise_metal(metal, fineness):
    """billon/silver collapse when fineness < 0.5 (per §5.2 primary rule 1)."""
    if metal is None:
        return None
    m = str(metal).lower()
    # Pull a representative fineness value
    f_val = None
    if isinstance(fineness, (int, float)):
        f_val = float(fineness)
    elif isinstance(fineness, list):
        vals = [
            e.get("value") for e in fineness
            if isinstance(e, dict) and isinstance(e.get("value"), (int, float))
        ]
        if vals:
            f_val = min(vals)
    if m == "silver" and f_val is not None and f_val < 0.5:
        return "billon"
    return m


def _normalise_nominal(nominal):
    if not nominal:
        return ""
    s = str(nominal).lower().strip()
    s = s.replace("müntze", "münze")
    s = re.sub(r"[‒–—]+", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _normalise_ruler(ruler):
    """Canonicalise a ruler string for cross-source comparison.

    Variants normalised to the same form (so reign-index queries +
    cross-source matcher hits don't fragment over spelling artefacts):

      «Christian IV.»     →  «christian iv»
      «Christian IV»      →  «christian iv»
      «Christian IV. (1588-1648)»  →  «christian iv»
      «Christian VII, der …»  →  «christian vii»
      «Frederik IV 1699 - 1730»  →  «frederik iv»  (NumisMaster reign-bleed)
      «Christian VII 1766 - 1808 Issuer: Danish …»  →  «christian vii»  (NumisMaster Issuer-bleed)
      «Friedrich III. von Schleswig-Holstein-Gottorp»  →  «friedrich iii»

    Returns lowercased, trailing-period-stripped, single-spaced.
    """
    if not ruler:
        return ""
    s = str(ruler)
    # Drop parenthetical reign annotations, e.g. «(1588-1648)»
    s = s.split("(")[0]
    # Drop comma-tail descriptive epithets, e.g. «Christian VII, der …»
    s = s.split(",")[0]
    # Drop «Issuer:» bleed-through from NumisMaster pages
    s = re.split(r"\s+Issuer\s*:", s, maxsplit=1)[0]
    # Drop trailing «1699 - 1730» reign-year tail (NumisMaster mass-pollution
    # already handled by parse_numismaster._clean_ruler, but defensive here
    # so older seeds + future sources stay normalised)
    s = re.sub(r"\s+\d{4}\s*-\s*\d{0,4}\s*$", "", s)
    # Drop «von <house>» / «af <kingdom>» trailing peerage
    s = re.split(r"\s+(?:von|af|of|zu)\s+", s, maxsplit=1)[0]
    # Strip trailing dots, normalise whitespace
    s = re.sub(r"\.+$", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    # English / parser-artefact spelling normalisations. The Danish
    # form is «Frederik» (no `c` before `k`); some sources / parsers
    # render it «Frederick» which fragments index attestation. Same
    # for «Christian» (no variant) — kept for symmetry future-proof.
    s = re.sub(r"\bfrederick\b", "frederik", s)
    return s


def _coin_years(coin: dict) -> set[int]:
    """All years this coin's type was attested for, expanded from either
    `year_ranges: [[lo, hi], ...]` or `year_first`..`year_last`.

    Used by `_build_reign_index` (which years does this coin's ruler
    cover?) and by `_infer_ruler` (which years does this coin claim,
    so we can look up the unambiguous ruler?).
    """
    years: set[int] = set()
    yr = coin.get("year_ranges")
    if isinstance(yr, list) and yr:
        for r in yr:
            if isinstance(r, (list, tuple)) and len(r) == 2:
                try:
                    lo, hi = int(r[0]), int(r[1])
                    if hi < lo:
                        lo, hi = hi, lo
                    years.update(range(lo, hi + 1))
                except (TypeError, ValueError):
                    continue
    else:
        yf, yl = coin.get("year_first"), coin.get("year_last")
        if isinstance(yf, int):
            yl_int = yl if isinstance(yl, int) else yf
            if yl_int < yf:
                yf, yl_int = yl_int, yf
            years.update(range(yf, yl_int + 1))
    return years


# ---------------------------------------------------------------------------
# Hede-volume reign windows — per-volume parser-anomaly filter for D33
# ---------------------------------------------------------------------------
# danskmoent.dk Hede catalog is organised by ruler-volumes: `c4h*` is the
# Christian IV volume, `f3h*` is Frederik III, etc. The volume code is
# the parser's canonical attribution of WHICH ruler a Hede entry
# documents — it's encoded in the URL path and never ambiguous. The
# `year_first` / `year_last` fields, by contrast, occasionally suffer
# parser-anomalies (an OCR-or-regex glitch reads 1746 as 1646, or a
# type-continuity range overshoots the issuing ruler's death-year by
# decades — captured 2026-05-18 audit found 11 such cases).
#
# When building the D33 reign index, we use this table to drop
# (year, ruler) attestations whose year falls OUTSIDE the volume's
# documented reign window — the bad year never poisons the index,
# while genuinely-attested in-window years contribute as normal. The
# seed itself stays untouched (parser-fix is a separate task; this is
# a defensive filter at the merger layer).
#
# Window endpoints are inclusive on both sides. Transition years (king
# A dies + king B crowned same calendar year) appear in BOTH adjacent
# windows by design — both rulers can legitimately have struck coins
# in that year, so multi-ruler attestation is the correct outcome.
#
# Source: Wilcke 1950 / Hede 1957 (Danish royal reign chronology) — a
# well-established historical record, not invented; per CLAUDE.md §0
# this category of attested historical knowledge is a valid source.
# Hede volume codes (`c4h`, `f3h`, …) carry both the ruler attribution
# (encoded in the volume letter + roman-numeral integer) AND the reign
# window. Together they let the D33 reign-index construction:
#   (a) OVERRIDE the seed's `ruler` field with the volume-canonical
#       label when they disagree (real cases captured 2026-05-18:
#       `dk-hede-c9h1a` has ruler="Christian VIII." but volume=`c9h`
#       means Christian IX — the page's catalog scope is authoritative);
#   (b) FILTER per-year attestations to the ruler's actual reign window
#       (real cases captured 2026-05-18: `dk-hede-f5h3ab` parsed year
#       1646 for a Frederik V coin — FR V reigned 1746-1766; the
#       attestation is dropped so it doesn't poison the index).
#
# The reign window is also exposed by ruler-name (`_DK_RULER_REIGNS`)
# so non-Hede sources (NumisMaster, Numista, Bruun, Galster) can use
# the SAME filter when their seed's `ruler` field attests a king for
# a year outside that king's reign (captured 2026-05-18:
# `denmark-numismaster-165534` attests Frederik III for year 1633 —
# FR III reigned 1648-1670, that 1633 attestation is wrong).
#
# Source: Wilcke 1950 / Hede 1957 (Danish royal reign chronology) — a
# well-established historical record, not invented; per CLAUDE.md §0
# this category of attested historical knowledge is a valid source.
# (Reign windows scoped to the Danish realm. Other entities like
# `gottorp_duchy`, `schauenburg_pinneberg` use entirely different
# ruler timelines and would need their own tables when D33 fires for
# those — currently they have ≤3 cross-source low-confidence pairs,
# so the Danish table covers the 99 %+ case.)
_HEDE_VOLUME_TO_RULER: dict[str, str] = {
    "c2h": "christian ii",
    "f1h": "frederik i",
    "c3h": "christian iii",
    "f2h": "frederik ii",
    "c4h": "christian iv",
    "f3h": "frederik iii",
    "c5h": "christian v",
    "f4h": "frederik iv",
    "c6h": "christian vi",
    "f5h": "frederik v",
    "c7h": "christian vii",
    "f6h": "frederik vi",
    "c8h": "christian viii",
    "f7h": "frederik vii",
    "c9h": "christian ix",
    "f8h": "frederik viii",
    "c10h": "christian x",
}

_DK_RULER_REIGNS: dict[str, tuple[int, int]] = {
    "christian ii": (1513, 1523),
    "frederik i": (1523, 1533),
    "christian iii": (1534, 1559),
    "frederik ii": (1559, 1588),
    "christian iv": (1588, 1648),
    "frederik iii": (1648, 1670),
    "christian v": (1670, 1699),
    "frederik iv": (1699, 1730),
    "christian vi": (1730, 1746),
    "frederik v": (1746, 1766),
    "christian vii": (1766, 1808),
    "frederik vi": (1808, 1839),
    "christian viii": (1839, 1848),
    "frederik vii": (1848, 1863),
    "christian ix": (1863, 1906),
    "frederik viii": (1906, 1912),
    "christian x": (1912, 1947),
}


def _hede_volume_to_ruler(coin: dict) -> str | None:
    """Map the coin's Hede volume code to its canonical normalised
    ruler label. The `n` prefix (Norge sub-catalogue) is stripped first
    since the same monarch ruled both kingdoms in personal union.
    Returns None for non-Hede entries or Hede entries lacking a parsed
    volume code.
    """
    vol = ((coin.get("catalog") or {}).get("hede_volume") or "").strip().lstrip("n")
    if not vol:
        return None
    return _HEDE_VOLUME_TO_RULER.get(vol)


def _attestation_ruler(coin: dict) -> str | None:
    """Pick the authoritative normalised-ruler attestation for an
    index-building pass:
      • Hede sources → derive from `hede_volume` code (parser-canonical,
        immune to ruler-field mislabels);
      • Non-Hede sources → fall back to `_normalise_ruler(coin.ruler)`.
    Returns None when neither path yields a ruler.
    """
    rn = _hede_volume_to_ruler(coin)
    if rn:
        return rn
    return _normalise_ruler(coin.get("ruler")) or None


# Entities where the ruler is unambiguously a Danish-monarchy king
# (Danish-Norwegian personal union 1380-1814, plus Holstein-Glückstadt
# under Danish sovereignty 1544+). For these we apply STRICT reign
# filtering: an attestation whose normalised ruler isn't in
# `_DK_RULER_REIGNS` is dropped entirely (treated as parser-anomaly
# bad data). Real example caught 2026-05-18: NumisMaster MC pages
# for Danish 1809-1810 coins of Frederik VI rendered as «Frederick IX»
# (FR IX reigned 1947-1972, never could have signed 1809 coins) —
# visual VI / IX confusion in their data entry.
_DK_REALM_ENTITIES = frozenset({"danish_realm", "danish_norway", "royal_holstein"})


def _build_reign_index(coins: list[dict], entity_id: str | None = None) -> dict[int, set[str]]:
    """Build `{year → set(normalised_rulers)}` index from coins of ONE
    entity that DO carry an attested ruler. Per CLAUDE.md §0 / D33 the
    inference downstream is conservative: it ONLY fires when a year
    maps to a singleton ruler set in this index.

    The index is built in two passes:

    1. **Raw attestation pass** — each coin's `(year, ruler)` pair
       contributes to the raw index. Years where multiple distinct
       rulers are attested across the corpus (real transition years
       like 1648 / 1670 / 1808 + data anomalies where some source
       mislabelled a ruler) end up with a multi-element set.

    2. **Contiguous-reign gap-fill pass** — for any year `y` between
       the min and max attested years that is NOT covered by step 1,
       look at the closest preceding attested year `p` and closest
       following attested year `n`. When BOTH `index[p]` and
       `index[n]` are the SAME singleton set `{R}`, fill `y` with
       `{R}`. Rationale: if the reign-corpus says CHR IV alone in
       1605 and CHR IV alone in 1612, the gap years 1606-1611 are
       unambiguously also CHR IV — no seed coin happens to be dated
       to those in-between years, but the bracket guarantees no king
       changed in the interval. The two-sided bracket ensures the
       fill never extends past either end of a reign.

    Transition years (king-A dies + king-B crowned in same calendar
    year), separatist / co-regent windows, and any year where two
    different ruler labels were attested across the corpus end up with
    a multi-element set — `_infer_ruler` returns None for those and
    leaves the ruler null. Better null than a false attribution per
    user direction 2026-05-18.
    """
    raw: dict[int, set[str]] = {}
    strict_dk = entity_id in _DK_REALM_ENTITIES
    for c in coins:
        # Pick the authoritative ruler for this attestation: Hede →
        # volume-canonical (immune to seed-field mislabels); other
        # sources → seed's `ruler` field. See `_attestation_ruler`.
        rn = _attestation_ruler(c)
        if not rn:
            continue
        reign_window = _DK_RULER_REIGNS.get(rn)
        if strict_dk and reign_window is None:
            # Strict DK-realm filter: a ruler-name not in the Danish
            # royal chronology (e.g. NumisMaster's «Frederick IX» on
            # an 1809 coin) is parser-anomaly bad data. Drop the
            # entire attestation rather than letting it poison the
            # year's ruler-set.
            continue
        for y in _coin_years(c):
            if reign_window is not None:
                lo, hi = reign_window
                if y < lo or y > hi:
                    continue
            raw.setdefault(y, set()).add(rn)

    if not raw:
        return raw

    extended = dict(raw)
    known = sorted(raw)
    min_y, max_y = known[0], known[-1]
    # Build a sparse lookup for prev/next attested year per gap year.
    # Walk forward through the year range once, tracking the most-recent
    # singleton-attested year on the left; for each gap year, look ahead
    # to the next singleton-attested year on the right.
    last_singleton: tuple[int, str] | None = None
    next_singleton_after: dict[int, tuple[int, str]] = {}
    next_known: tuple[int, str] | None = None
    for y in range(max_y, min_y - 1, -1):
        if y in raw and len(raw[y]) == 1:
            next_known = (y, next(iter(raw[y])))
        if next_known is not None:
            next_singleton_after[y] = next_known
    for y in range(min_y, max_y + 1):
        if y in raw and len(raw[y]) == 1:
            last_singleton = (y, next(iter(raw[y])))
            continue
        if y in raw:
            # multi-attest year — never gap-fill, never advance singleton
            continue
        next_pair = next_singleton_after.get(y + 1)
        if last_singleton is None or next_pair is None:
            continue
        # Both bracket years attest the same single ruler with no
        # multi-attest year in between (we'd have hit `continue` above
        # before reaching this y).
        if last_singleton[1] == next_pair[1]:
            extended[y] = {last_singleton[1]}
    return extended


def _infer_ruler(coin: dict, reign_index: dict[int, set[str]]) -> str | None:
    """Look up the coin's year(s) in the entity-scoped reign index.

    Resolves to a single inferred ruler under the «singleton-anchored
    + transition-tolerant» rule:

    1. Walk every year in the coin's covered span. Each year contributes
       its ruler-set from the index (singleton, multi-element, or
       missing).
    2. Years where the index is missing the year entirely → return None
       (genuine ignorance — better null than guess).
    3. Collect the set of SINGLETON rulers across the coin's years
       (`singletons`) and the list of MULTI-ELEMENT ruler-sets
       (`multi_sets`).
    4. Require ≥1 singleton anchor — if every year touches a transition
       year only, the coin is genuinely ambiguous and the inference
       returns None. This handles real single-year-on-transition coins
       (e.g. a 1648 1/4 Speciedaler can be CHR IV's or FR III's; we
       refuse to pick).
    5. All singletons must agree on one ruler R. If two years attest
       different singletons, the coin crosses reigns → None.
    6. Every multi-ruler year's set must CONTAIN R. This allows a
       coin whose span includes a transition year (e.g. 1667-1670
       with all of 1667-1669 attesting FR III alone and 1670
       attesting both CHR V + FR III) to confidently infer FR III —
       the transition year's set is a superset of the singleton.
       But disallows inferring R when a multi-set excludes R
       (meaning we're conflating two reigns).
    7. With all checks passed, return R.

    Per user direction 2026-05-18 «краще мати null і продовжити
    шукати правду ніж поставити неправдивий nonull value».
    """
    years = _coin_years(coin)
    if not years:
        return None

    singletons: set[str] = set()
    multi_sets: list[set[str]] = []
    for y in years:
        rulers = reign_index.get(y)
        if not rulers:
            return None
        if len(rulers) == 1:
            singletons.add(next(iter(rulers)))
        else:
            multi_sets.append(set(rulers))

    if not singletons:
        # All covered years are multi-ruler (transition-only span) —
        # genuinely ambiguous, stay null.
        return None
    if len(singletons) > 1:
        # Span crosses two distinct reigns — can't pick one.
        return None

    R = next(iter(singletons))
    for s in multi_sets:
        if R not in s:
            # A multi-set in the span excludes our singleton ruler —
            # the coin's coverage doesn't cohere around a single
            # reign; stay null.
            return None
    return R


def _catalog_refs(coin: dict, entity_id: str | None = None) -> dict[str, str]:
    """Return dict of {scope_key: ref_value} for every catalog ref.
    Keys encode scope so cross-volume / cross-ruler collisions don't
    false-match (per user reminder: KM-DK#1 ≠ KM-SH#1; Hede#1 of
    Christian IV ≠ Hede#1 of Christian VII).

    Scope-key shape:
      'km/{register}' — for KM. Dict-form contributes one key per
                        register. Bare-form maps to the entity's
                        default register (`_ENTITY_TO_KM_REGISTER`)
                        OR drops to bare `'km'` when entity has no
                        mapping.
      'hede/{ruler}'  — for Hede. Derived from coin's `ruler` field
                        (normalised) when present, else from
                        `catalog.hede_volume` lookup. Falls back to
                        bare `'hede'` only when both unavailable.
      Single-source refs (sieg/schou/lange/galster_volume/fr/dav/mb/
        jensen_skjoldager/schive/skaare/friedberg/davenport) — verbatim
        field name (publication-stable scope, no ruler clash).
    """
    cat = coin.get("catalog") or {}
    refs: dict[str, str] = {}

    km = cat.get("km")
    if km is not None:
        if isinstance(km, dict):
            for reg, v in km.items():
                refs[f"km/{reg.lower()}"] = str(v).strip()
        else:
            # Bare KM — infer register from entity context.
            register = _ENTITY_TO_KM_REGISTER.get(entity_id or "")
            if register:
                refs[f"km/{register}"] = str(km).strip()
            else:
                refs["km"] = str(km).strip()

    hede = cat.get("hede")
    if hede is not None:
        # Scope = ruler-canonical first (preferred since ruler field is
        # the authoritative «which king's Hede catalog» signal); fall
        # back to hede_volume code from URL; finally bare-key.
        ruler_norm = _normalise_ruler(coin.get("ruler"))
        vol = (cat.get("hede_volume") or "").strip()
        if ruler_norm:
            scope = ruler_norm
        elif vol:
            scope = vol
        else:
            scope = ""
        key = f"hede/{scope}" if scope else "hede"
        if isinstance(hede, list):
            refs[key] = "|".join(sorted(str(h).strip() for h in hede))
        else:
            refs[key] = str(hede).strip()

    # Per-publication catalog identifiers — each is unique within its own
    # scope. Disagreement on any of these = different physical coins.
    # `numista` + `bruun_collection_id` included: same physical coin
    # generally has one Numista N# and one Bruun collection-id; two
    # records with different IDs = different specimens (Bruun) or sub-
    # variants (Numista) and should NOT auto-merge without curator
    # decision via merge_decisions/<entity>.yml.
    #
    # Bruun_part / bruun_lot_no / bruun_page are SPECIMEN-level — two
    # lots can be the same type; excluded from match comparison.
    for field in ("sieg", "schou", "lange", "fr", "dav", "mb",
                  "jensen_skjoldager", "schive", "skaare", "friedberg",
                  "davenport", "numista", "bruun_collection_id"):
        val = cat.get(field)
        if val is None:
            continue
        if isinstance(val, list):
            refs[field] = "|".join(sorted(str(v).strip() for v in val))
        else:
            refs[field] = str(val).strip()

    galster = cat.get("galster")
    if galster is not None:
        vol = (cat.get("galster_volume") or "").strip()
        key = f"galster/{vol}" if vol else "galster"
        refs[key] = str(galster).strip()

    return refs


def _catalog_chain_consistent(refs_a: dict, refs_b: dict):
    """Returns (state, has_overlap):
      state ∈ {'agree', 'disagree', 'no_overlap'}
      has_overlap: True if any shared key
    """
    shared = set(refs_a) & set(refs_b)
    if not shared:
        return ("no_overlap", False)
    for k in shared:
        # For list-encoded refs (separated by "|"), match if sets overlap
        va, vb = refs_a[k], refs_b[k]
        sa = set(va.split("|"))
        sb = set(vb.split("|"))
        if not (sa & sb):
            return ("disagree", True)
    return ("agree", True)


def _year_first(coin):
    return coin.get("year_first")


def _year_last(coin):
    return coin.get("year_last") or coin.get("year_first")


def _years_overlap(a, b):
    af, al = _year_first(a), _year_last(a)
    bf, bl = _year_first(b), _year_last(b)
    if af is None or bf is None:
        return None
    return max(af, bf) <= min(al, bl)


def _fineness_repr(coin) -> float | None:
    f = coin.get("fineness")
    if isinstance(f, (int, float)):
        return float(f)
    if isinstance(f, list):
        vals = [
            e.get("value") for e in f
            if isinstance(e, dict) and isinstance(e.get("value"), (int, float))
        ]
        if vals:
            return sum(vals) / len(vals)
    return None


def _fineness_within(a, b, tol=0.05):
    fa = _fineness_repr(a)
    fb = _fineness_repr(b)
    if fa is None or fb is None:
        return None
    return abs(fa - fb) <= tol


# Mint spelling aliases — map source-specific variants to a single
# project-canonical lowercased form so cross-source mint comparison
# doesn't false-fail on language / orthography. Each entry: source
# spelling (lowercase) → canonical spelling (lowercase).
#
# Discovered 2026-05-19 during D40 H-case categorisation: 27 of 33
# residual pending entries were «Copenhagen» (NumisMaster English) vs
# «Kopenhagen» (project-canonical Danish/German). 1 case was
# «Rendsborg» (Danish) vs «Rendsburg» (project-canonical German for SH
# towns). Pure normaliser gap, not actual mint divergence.
#
# When extending: keep map-keys lowercase. Match is applied after
# `lower()` + paren-suffix stripping in `_normalise_mints`. Add
# variants ONLY when they refer to the SAME historical mint town —
# never collapse functionally-distinct mints into one canonical form.
_MINT_SPELLING_ALIASES = {
    # Copenhagen — English / historical Danish / Latin → project canonical
    # (German-Danish «Kopenhagen» is the convention per CLAUDE.md §2 / §i18n
    # «mint names use standard academic spellings, identical across languages»;
    # the «Kopenhagen» form is what V1 foundation entries carry).
    "copenhagen": "kopenhagen",
    "københavn": "kopenhagen",
    "kjøbenhavn": "kopenhagen",       # historical Danish (pre-1948 spelling)
    "hafnia": "kopenhagen",            # Latin (Christian IV / Frederik III legends)
    # Rendsburg — Danish vs German for the Schleswig-Holstein town.
    # Project convention: German spelling for SH mints (consistent with
    # other SH towns like Flensburg, Eckernförde, Husum).
    "rendsborg": "rendsburg",
    # Helsingør — English «Elsinore» variant
    "elsinore": "helsingør",
    "elseneur": "helsingør",           # French (rare, appears in old auction catalogues)
}


# Country / region prefix tokens that ucoin and similar sources
# sometimes prepend to mint strings — e.g. ucoin's «Denmark, Copenhagen»,
# «Norway, Christiania», «Sweden, Stockholm». These prefixes carry no
# information beyond what the issuing_entity already encodes; stripping
# them lets the city token reach the alias map.
_MINT_COUNTRY_PREFIXES = frozenset({
    "denmark", "norway", "sweden", "germany", "holstein", "schleswig",
    "schleswig-holstein", "lübeck", "hamburg",
})


def _normalise_mints(mint) -> set[str]:
    if mint is None:
        return set()
    mints = mint if isinstance(mint, list) else [mint]
    out = set()
    for m in mints:
        if not isinstance(m, str):
            continue
        # Strip trailing paren tail «Altona (FK VS)» → «Altona», then
        # split on comma so multi-token shapes like «Denmark, Copenhagen»
        # or «Altona, Kopenhagen» (V1 list-style joined into a string)
        # decompose into individual mint tokens.
        base = re.sub(r"\s*\([^)]*\)\s*$", "", m).strip()
        if not base:
            continue
        tokens = [t.strip().lower() for t in base.split(",") if t.strip()]
        for t in tokens:
            # Skip pure country-prefix tokens (they're scope qualifiers,
            # not mint towns). Keeps the city token for comparison.
            if t in _MINT_COUNTRY_PREFIXES:
                continue
            # Apply spelling-alias canonicalisation so cross-source
            # comparison doesn't false-fail on English/Danish/German
            # variants of the same mint town.
            canonical = _MINT_SPELLING_ALIASES.get(t, t)
            out.add(canonical)
    return out


def _mints_overlap(a, b):
    ma = _normalise_mints(a.get("mint"))
    mb = _normalise_mints(b.get("mint"))
    if not (ma and mb):
        return None
    if ma & mb:
        return True
    # No overlap — check whether either side's mint is curator-attested
    # (`mint_verified: True`). An UNVERIFIED mint is a V1-bootstrap
    # fallback (typically «Kopenhagen» as default for Danish coins) or
    # a parser guess — it cannot DISPROVE a merge against a verified
    # authority like Hede 1971's page header. When one side is verified
    # and the other isn't, return None (unknown) instead of False.
    #
    # When BOTH sides are unverified, the mint signal is fully advisory;
    # also return None to let other signals drive the decision.
    av = bool(a.get("mint_verified"))
    bv = bool(b.get("mint_verified"))
    if av != bv or (not av and not bv):
        return None
    # Both verified, no overlap — real divergence
    return False


# ---------------------------------------------------------------------------
# Match algorithm
# ---------------------------------------------------------------------------


def match_pair(coin_a: dict, coin_b: dict, entity_id: str | None = None,
               reign_index: dict[int, set[str]] | None = None) -> dict:
    """Apply §5.2 hierarchy. Returns:
        {'decision': 'confident' | 'low_confidence' | 'no_match',
         'primary': {metal, nominal, catalog, ruler},
         'fallback': {years, fineness, mint},
         'why': [str, ...]}
    Primary booleans: True (match), False (mismatch), None (cannot evaluate).

    `entity_id` is used to scope bare-form catalog refs (KM register
    inference per `_ENTITY_TO_KM_REGISTER`) — both coins are assumed
    to belong to the same entity (matcher is per-entity).

    `reign_index` (D33) is an optional `{year → set(rulers)}` map for
    THIS entity, built from members that DO have an attested ruler.
    When either coin's `ruler` is null, the matcher falls back to
    looking up its year(s) in the index — but ONLY adopts the inferred
    value when the union of rulers across every covered year is
    exactly one (transition / co-regent years leave the ruler null per
    user direction). The inference is reported in `why` as
    «ruler inferred: <name> (year(s) X)» so a curator audit can trace
    the chain.
    """
    primary = {}
    fallback = {}
    why = []

    # Metal
    ma = _normalise_metal(coin_a.get("metal"), coin_a.get("fineness"))
    mb = _normalise_metal(coin_b.get("metal"), coin_b.get("fineness"))
    if ma and mb:
        primary["metal"] = (ma == mb)
        if not primary["metal"]:
            why.append(f"metal: {ma} ≠ {mb}")
            return {"decision": "no_match", "primary": primary,
                    "fallback": fallback, "why": why}
    else:
        primary["metal"] = None

    # Nominal
    na = _normalise_nominal(coin_a.get("nominal"))
    nb = _normalise_nominal(coin_b.get("nominal"))
    if na and nb:
        primary["nominal"] = (na == nb)
        if not primary["nominal"]:
            why.append(f"nominal: {coin_a.get('nominal')!r} ≠ {coin_b.get('nominal')!r}")
            return {"decision": "no_match", "primary": primary,
                    "fallback": fallback, "why": why}
    else:
        primary["nominal"] = None

    # Catalog chain (entity-aware scoping for bare KM + ruler-aware for Hede)
    refs_a = _catalog_refs(coin_a, entity_id)
    refs_b = _catalog_refs(coin_b, entity_id)
    chain_state, has_overlap = _catalog_chain_consistent(refs_a, refs_b)
    if chain_state == "disagree":
        why.append(f"catalog disagree: {refs_a} vs {refs_b}")
        primary["catalog"] = False
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why}
    if chain_state == "agree":
        primary["catalog"] = True
    else:
        # no_overlap: one or both sides lack catalog refs that intersect.
        # NOT a mismatch — can't be evaluated. Tri-state primary signal.
        primary["catalog"] = None

    # Ruler — direct values first; reign-index inference (D33) when null.
    ra = _normalise_ruler(coin_a.get("ruler"))
    rb = _normalise_ruler(coin_b.get("ruler"))
    if reign_index:
        if not ra:
            inferred_a = _infer_ruler(coin_a, reign_index)
            if inferred_a:
                ra = inferred_a
                why.append(f"ruler_a inferred: {inferred_a!r} from year(s) {sorted(_coin_years(coin_a))}")
        if not rb:
            inferred_b = _infer_ruler(coin_b, reign_index)
            if inferred_b:
                rb = inferred_b
                why.append(f"ruler_b inferred: {inferred_b!r} from year(s) {sorted(_coin_years(coin_b))}")
    if ra and rb:
        primary["ruler"] = (ra == rb)
        if not primary["ruler"]:
            why.append(f"ruler: {ra!r} ≠ {rb!r}")
    else:
        primary["ruler"] = None

    # Fallback signals
    fallback["years"] = _years_overlap(coin_a, coin_b)
    fallback["fineness"] = _fineness_within(coin_a, coin_b)
    fallback["mint"] = _mints_overlap(coin_a, coin_b)

    # Confidence calc
    primary_true = sum(1 for v in primary.values() if v is True)
    primary_unknown = sum(1 for v in primary.values() if v is None)
    primary_false = sum(1 for v in primary.values() if v is False)

    fallback_true = sum(1 for v in fallback.values() if v is True)
    fallback_false = sum(1 for v in fallback.values() if v is False)

    if primary_false:
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why or ["primary signal disagreed"]}

    # All available primary signals agree (no False); some may be None
    # (not evaluable — e.g. catalog no_overlap when refs come from
    # different cataloguing systems, or metal not stated). Decision:
    #
    #   CONFIDENT  — primary_true ≥ 3 AND fallback_true ≥ 1 AND no fallback_false
    #   LOW_CONF   — primary_true == 4 AND fallback_false > 0
    #                (catalog/ruler/nominal/metal all match but specimen
    #                 weight or year disagrees — curator inspect)
    #   LOW_CONF   — primary_true ≥ 2 AND fallback_true ≥ 1 AND no fallback_false
    #   NO_MATCH   — everything else
    if primary_true == 4 and fallback_false > 0:
        why.append(f"all 4 primary match but fallback disagrees: {fallback}")
        return {"decision": "low_confidence", "primary": primary,
                "fallback": fallback, "why": why}

    if fallback_false > 0:
        why.append(f"fallback disagrees ({fallback}), primary_true={primary_true}")
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why}

    if primary_true >= 3 and fallback_true >= 1:
        return {"decision": "confident", "primary": primary,
                "fallback": fallback, "why": [f"primary_true={primary_true}/4, fallback_true={fallback_true}"]}

    if primary_true >= 2 and fallback_true >= 1:
        why.append(f"primary_true={primary_true} (<3) — review")
        return {"decision": "low_confidence", "primary": primary,
                "fallback": fallback, "why": why}

    return {"decision": "no_match", "primary": primary,
            "fallback": fallback, "why": why or [f"insufficient signals (primary_true={primary_true}, fallback_true={fallback_true})"]}


# ---------------------------------------------------------------------------
# Union-Find with explicit no-merge support
# ---------------------------------------------------------------------------


class UnionFind:
    """Union-Find with explicit no-merge that respects TRANSITIVITY:
    when A↔B and A↔C are confident merges but B↔C is no_match, the
    transitive union {A, B, C} would silently override B↔C's no_match.
    To prevent this, union(x, y) checks every cross-class member pair
    for a registered no_merge constraint; if any pair conflicts, the
    union is refused.

    This means processing order matters: register all no_merges FIRST
    (matcher pass for no_match decisions), then process confident
    unions. A confident union that violates a no_merge stays separate
    + surfaces in match_uncertainty via the unmerged pair.
    """

    def __init__(self):
        self.parent: dict[str, str] = {}
        self.no_merge: set[frozenset] = set()

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def can_union(self, x, y) -> bool:
        return frozenset({x, y}) not in self.no_merge

    def _class_members(self, root: str) -> list[str]:
        return [k for k in self.parent if self.find(k) == root]

    def union(self, x, y) -> tuple[bool, frozenset | None]:
        """Returns (succeeded, conflicting_pair_or_None).
        On no_merge violation, returns (False, frozenset({a, b}))
        so caller can log which pair blocked the transitive union."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return (False, None)
        # Direct pair check
        if not self.can_union(x, y):
            return (False, frozenset({x, y}))
        # Cross-class check: any member of rx's class has a no_merge
        # with any member of ry's class?
        if self.no_merge:
            members_x = self._class_members(rx)
            members_y = self._class_members(ry)
            for mx in members_x:
                for my in members_y:
                    if frozenset({mx, my}) in self.no_merge:
                        return (False, frozenset({mx, my}))
        # Stable root choice: lexicographically smaller wins
        if rx < ry:
            self.parent[ry] = rx
        else:
            self.parent[rx] = ry
        return (True, None)

    def add_no_merge(self, x, y):
        self.no_merge.add(frozenset({x, y}))
        # Touch both ids so they appear as singleton classes if not
        # subsequently merged with anything else.
        self.find(x)
        self.find(y)

    def classes(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for k in self.parent:
            groups[self.find(k)].append(k)
        return dict(groups)


# ---------------------------------------------------------------------------
# Unified entry construction
# ---------------------------------------------------------------------------


def _collect_field_list(members: list[dict], field: str) -> list[dict]:
    """For weight_rough_g / fineness / diameter_mm — collect ALL readings
    from every member as multi-source list entries. Dedupe by (value, source)
    so re-runs are deterministic."""
    seen: set[tuple] = set()
    out: list[dict] = []
    for m in members:
        val = m.get(field)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            # bare-number form — synthesise source from member id
            entry = {"value": float(val), "source": _source_label_from_id(m.get("id"))}
            key = (entry["value"], entry["source"])
            if key not in seen:
                seen.add(key)
                out.append(entry)
        elif isinstance(val, list):
            for item in val:
                if not isinstance(item, dict):
                    continue
                v = item.get("value")
                if not isinstance(v, (int, float)):
                    continue
                entry = {"value": float(v), "source": item.get("source", "?")}
                key = (entry["value"], entry["source"])
                if key not in seen:
                    seen.add(key)
                    out.append(entry)
    # Deterministic order: by value, then source
    out.sort(key=lambda e: (e["value"], e["source"]))
    return out


def _source_label_from_id(coin_id: str | None) -> str:
    if not coin_id:
        return "?"
    if coin_id.startswith("dk-hede-"):
        return "hede"
    if coin_id.startswith("dk-bruun-"):
        return "bruun"
    if coin_id.startswith("dk-numismaster-"):
        return "numismaster"
    if coin_id.startswith("dk-numista-"):
        return "numista"
    if coin_id.startswith("dk-galster-"):
        return "galster"
    return coin_id.split("-")[1] if "-" in coin_id else "?"


def _collect_sources(members: list[dict]) -> list[dict]:
    """Union members' source lists with smart de-duplication.

    Two regimes by URL shape:

    * **Single-page sources** (each URL == one cited record): URL is
      the primary identity; multiple entries with the same URL but
      different `ref` / `type` labels are RE-LABELS of the same
      citation, NOT distinct references. Dedupe by URL alone, keep
      the first occurrence. Covers `danskmoent.dk/*.htm`,
      `en.numista.com/<id>`, `en.ucoin.net/coin/.../?tid=<n>`,
      `numismaster.com/MC_<n>`, `numista.com/`, IKMK `ikmk.smb.museum/`.
    * **Multi-record sources** (one URL hosts many citations, with
      `ref` carrying the per-citation discriminator — page / lot / etc.):
      dedupe by (URL, ref, type) — keep distinct refs even when URL
      collides. Covers Bruun PDFs (Stack's Bowers catalogues — one
      PDF, hundreds of lots), institutional library PDFs.

    Triggers for the «single-page» regime: known host substrings.
    Anything else falls through to the strict (url, ref, type) key.
    """
    _SINGLE_PAGE_HOSTS = (
        "danskmoent.dk",
        "en.numista.com",
        "en.ucoin.net",
        "numismaster.com",
        "ikmk.smb.museum",
    )
    seen_keys: set[tuple] = set()
    out: list[dict] = []
    for m in members:
        for s in m.get("sources") or []:
            if not isinstance(s, dict):
                continue
            url = s.get("url", "")
            ref = s.get("ref", "")
            stype = s.get("type", "")
            if any(host in url for host in _SINGLE_PAGE_HOSTS):
                key = ("url", url)
            else:
                key = ("trip", url, ref, stype)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            out.append(s)
    return out


def _collect_mints(members: list[dict]) -> str | list[str] | None:
    """Collect mint(s) from unified members per verified-wins precedence.

    Per CLAUDE.md §4 «verified-wins-over-unverified» principle applied
    to mint specifically (user-confirmed 2026-05-19): a `mint_verified:
    False` value is a curator GUESS (typically V1 bootstrap default
    «Kopenhagen» for Danish coins, or a parser heuristic). It cannot
    OVERRIDE a `mint_verified: True` authoritative attestation, and
    when no verified attestation exists, the lower-authority guess
    must yield to the higher-authority source's mint.

    Precedence:
      Tier 1: ANY member has `mint_verified: True`
              → use ONLY those members' mints (drop unverified guesses)
      Tier 2: All members unverified
              → use only the HIGHEST-_authority_score source's mints
              (e.g. Hede outranks ucoin even when neither flips the
              verified flag; the ucoin curator's «Kopenhagen» default
              is dropped in favour of Hede's parser-extracted mint)
      Tier 3: All members at authority score 0
              → fall back to UNION of all mints (legitimate joint-mint
              coins like Altona+Kopenhagen where both attest the same
              physical issue)
    """
    # Tier 1: verified mints, when any exist
    source_members = [m for m in members if bool(m.get("mint_verified"))]
    if not source_members:
        # Tier 2: keep only the highest-authority members
        scored = [(m, _authority_score(m.get("id", ""))) for m in members]
        max_score = max((s for _, s in scored), default=0)
        if max_score > 0:
            source_members = [m for m, s in scored if s == max_score]
        else:
            # Tier 3: nothing to rank by — keep everyone
            source_members = members
    mints_set: list[str] = []
    seen: set[str] = set()
    for m in source_members:
        mint = m.get("mint")
        if mint is None:
            continue
        mints = mint if isinstance(mint, list) else [mint]
        for mt in mints:
            if isinstance(mt, str) and mt not in seen:
                seen.add(mt)
                mints_set.append(mt)
    if not mints_set:
        return None
    if len(mints_set) == 1:
        return mints_set[0]
    return sorted(mints_set)


def _merge_km_field(members: list[dict], entity_id: str | None) -> tuple[
    str | dict | None, list[tuple[str, str, str]]
]:
    """Merge `catalog.km` across members into MAXIMAL representation:
    every distinct register-value pair is preserved. Handles bare-form
    + dict-form mixture across sources without losing cross-volume info.

    Example: hede.km = "75" (bare, danish_realm entity → infer dk),
             numismaster.km = {dk: "75", sh: "29"}
    Output:  km = {dk: "75", sh: "29"}   ← cross-volume sh="29" preserved
    (was being silently lost before this fix — see commit message).

    Returns (merged_km, conflicts). conflicts is a list of
    (scope_key, top_auth_value, conflicting_value) — items where two
    members disagreed on the same register's KM. Top-auth wins for the
    merged output; conflicts are surfaced for diagnostic logging.
    """
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    by_register: dict[str, str] = {}
    bare_value: str | None = None
    conflicts: list[tuple[str, str, str]] = []

    for m in sorted_members:
        km = (m.get("catalog") or {}).get("km")
        if km is None:
            continue
        if isinstance(km, dict):
            for reg, val in km.items():
                reg_norm = reg.lower()
                val_str = str(val).strip()
                if reg_norm in by_register and by_register[reg_norm] != val_str:
                    conflicts.append((f"km/{reg_norm}", by_register[reg_norm], val_str))
                    continue
                by_register.setdefault(reg_norm, val_str)
        else:
            val_str = str(km).strip()
            register = _ENTITY_TO_KM_REGISTER.get(entity_id or "")
            if register:
                if register in by_register and by_register[register] != val_str:
                    conflicts.append((f"km/{register}", by_register[register], val_str))
                    continue
                by_register.setdefault(register, val_str)
            elif bare_value is None:
                bare_value = val_str
            elif bare_value != val_str:
                conflicts.append(("km", bare_value, val_str))

    # Output shape — preserve maximal info:
    #   - cross-volume known → dict-form
    #   - single register known + no other inputs → bare-form (compact, V1-compat)
    #   - only bare-without-register input → bare-form
    if by_register:
        if len(by_register) == 1:
            # Single register — emit bare to stay V1-compat. The
            # entity-aware scoping rebuilds the register at match time.
            return next(iter(by_register.values())), conflicts
        return dict(by_register), conflicts
    return bare_value, conflicts


def _deep_merge_catalog(members: list[dict], entity_id: str | None = None
                        ) -> tuple[dict, list]:
    """Catalog refs accumulated across members per CLAUDE.md
    «Data-accumulation principle». Special-cases KM via `_merge_km_field`
    (cross-volume preservation). For other refs that schema declares as
    `str | list[str]`, accumulates distinct values into list-form when
    members disagree — no silent data loss.

    Top-authority value comes FIRST in the list (preserves display
    preference); distinct lower-auth values append in authority order.

    Returns (merged_catalog, conflicts). `conflicts` only logs cases
    where two members disagreed on a STRICTLY single-value field (e.g.
    bruun_part Literal — can't list-form).
    """
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    out: dict = {}
    all_conflicts: list[tuple[str, str, str]] = []

    # KM — special-case cross-volume merge
    km, km_conflicts = _merge_km_field(members, entity_id)
    if km is not None:
        out["km"] = km
    all_conflicts.extend(km_conflicts)

    # Fields that schema lets us accumulate to list-form
    # (per CatalogRefs `str | list[str]` declaration). Distinct values
    # across members are PRESERVED.
    _LIST_FORM_FIELDS = {
        "hede", "hede_volume", "sieg", "schou", "fr", "dav",
        "galster", "galster_volume", "jensen_skjoldager",
        "schive", "skaare", "friedberg", "davenport",
        "mb", "bruun_collection_id", "bruun_lot", "numista", "lange",
    }
    # Fields that stay single-value (specimen-level or strict literal).
    # Conflict = log; top-auth wins for output.
    _SINGLE_VALUE_FIELDS = {
        "bruun_part", "bruun_lot_no", "bruun_page",
        "sieg_hede1971", "schou_hede1971",
    }
    # `others` is already list-form; just union.

    # Defensive filter — drop cf-form values (user policy 2026-05-18):
    # «cf. X» references point at a similar OTHER coin, not at this entry's
    # own catalogue index, so they don't belong in catalog columns. Skip at
    # ingest time so future seeds carrying cf don't leak through.
    def _is_cf(value: str) -> bool:
        v = value.strip()
        if _SCALAR_CF_RE.match(v):
            return True
        if _OTHERS_CF_RE.match(v):
            return True
        return False

    # Collect distinct values per field across members
    per_field_values: dict[str, list[str]] = defaultdict(list)
    for m in sorted_members:
        cat = m.get("catalog") or {}
        for k, v in cat.items():
            if k == "km" or v is None:
                continue
            # Normalise to list of string values for comparison + accumulation
            if isinstance(v, list):
                value_list = [str(x).strip() for x in v if x is not None and str(x).strip()]
            else:
                value_list = [str(v).strip()] if str(v).strip() else []
            for val in value_list:
                if _is_cf(val):
                    continue
                if val not in per_field_values[k]:
                    per_field_values[k].append(val)

    # Emit per-field output
    for k, values in per_field_values.items():
        if not values:
            continue
        if k in _LIST_FORM_FIELDS:
            # str when single value (V1-compatible compact form);
            # list[str] when ≥2 distinct (data accumulation).
            out[k] = values[0] if len(values) == 1 else values
        elif k == "others":
            # `others: list[str]` — always list, union deduped
            out[k] = values
        elif k in _SINGLE_VALUE_FIELDS:
            # Single-value forced (schema constraint). Top-auth wins.
            out[k] = values[0]
            if len(values) > 1:
                for extra in values[1:]:
                    all_conflicts.append((f"catalog.{k}", values[0], extra))
        else:
            # Unknown field — defensive: keep first non-None
            out[k] = values[0]
            if len(values) > 1:
                for extra in values[1:]:
                    all_conflicts.append((f"catalog.{k}", values[0], extra))

    # `bruun_lot_no` is int in schema, `bruun_page` is int — re-cast when
    # values are numeric strings (pydantic would accept str→int coercion
    # but writing the YAML cleanly is nicer)
    for k in ("bruun_lot_no", "bruun_page"):
        if k in out and isinstance(out[k], str) and out[k].isdigit():
            out[k] = int(out[k])

    return out, all_conflicts


def _take_first_non_none(members: list[dict], field: str):
    """Return the first non-None / non-empty value across members
    (already sorted top-authority first). Gap-fills from lower-authority
    sources when top-authority lacks the field — no data loss when
    upper has None and lower has a real value."""
    for m in members:
        v = m.get(field)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def _union_year_ranges(members: list[dict]) -> list[list[int]] | None:
    """UNION year_ranges across members per data-accumulation principle.
    Combines all `year_ranges` entries (and also synthesised entries
    from each member's `year_first..year_last` when explicit ranges
    are absent), de-overlaps, returns sorted non-overlapping list.

    Example:
      Member A: year_ranges = [[1591, 1593]]
      Member B: year_ranges = [[1591,1591], [1595,1595]]
      Result:   [[1591, 1593], [1595, 1595]]
                (1591-1593 absorbs B's 1591; 1595 stands alone)

    Returns None when no member has any year info.
    """
    pairs: list[tuple[int, int]] = []
    for m in members:
        yr = m.get("year_ranges")
        if isinstance(yr, list) and yr:
            for r in yr:
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    try:
                        pairs.append((int(r[0]), int(r[1])))
                    except (TypeError, ValueError):
                        continue
        else:
            yf, yl = m.get("year_first"), m.get("year_last")
            if isinstance(yf, int):
                pairs.append((yf, int(yl) if isinstance(yl, int) else yf))

    if not pairs:
        return None

    # De-overlap / merge adjacent or overlapping pairs
    pairs.sort()
    merged: list[list[int]] = []
    for first, last in pairs:
        if merged and first <= merged[-1][1] + 1:
            # Overlap or adjacent — extend
            merged[-1][1] = max(merged[-1][1], last)
        else:
            merged.append([first, last])
    return merged


def _or_merge_verified(members: list[dict], field: str) -> bool | None:
    """OR-merge for verification flags: if ANY source attests (True),
    the unified entry is `True`. False otherwise (no source confirmed)."""
    seen_any_attestation = False
    seen_any_value = False
    for m in members:
        if field in m:
            seen_any_value = True
            if bool(m[field]):
                seen_any_attestation = True
                break
    if not seen_any_value:
        return None
    return seen_any_attestation


def build_unified(members: list[dict], unified_id: str,
                  entity_id: str | None = None
                  ) -> tuple[dict, list]:
    """Construct one unified entry from N member seed entries.

    Returns (unified_coin_dict, conflicts).
    `conflicts` lists scalar / catalog conflicts where members disagreed
    on a non-list field's value (top-auth wins for the output value but
    caller can log for visibility).

    Data-preservation rules per user direction («жодні дані не повинні
    бути перетерті, лише змерджені»):

      - Multi-source measurements (weight_rough_g, fineness, diameter_mm)
        → multi-source list with every reading preserved (`_collect_field_list`).
      - Sources → union, deduped by (url, ref, type).
      - Mint → union (list-form if multi-mint across members).
      - Catalog refs → max representation via `_deep_merge_catalog` —
        cross-volume KM preserved as dict-form, other refs gap-filled
        top-authority first.
      - Scalar text fields (nominal, ruler, year_label, year_first,
        year_last, year_ranges, mintmaster, fraction, kind, note,
        verification_note, inscription_obv, inscription_rev, metal):
        → `_take_first_non_none` walks members top-authority first;
        lower-authority's value fills gap when top-authority has None.
        On real conflict (both have non-None DIFFERENT values), top-auth
        wins; conflict logged.
      - Verification flags (metal_verified, fineness_verified,
        weight_rough_verified, diameter_mm_verified, mint_verified):
        → `_or_merge_verified` — any source attests → True. (A source's
        confirmation is never lost when its peer says False.)
    """
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    composed_of = sorted(set(m["id"] for m in members if m.get("id")))
    conflicts: list[tuple[str, str, str]] = []

    out: dict = {"id": unified_id}

    # Required schema fields (must have a value)
    out["fuss"] = _take_first_non_none(sorted_members, "fuss") or "seed_unsorted"
    out["phase"] = _take_first_non_none(sorted_members, "phase") or "unified"
    out["kind"] = _take_first_non_none(sorted_members, "kind") or "kurant"
    # `nominal` is schema-required. Some Galster pre-1541 seed entries
    # come with empty-string nominal (parser couldn't extract) — gap-fill
    # to '(?)' placeholder so schema validates; curator inspects pending
    # list and fills in real nominal via classification_decisions or by
    # fixing the parser.
    out["nominal"] = _take_first_non_none(sorted_members, "nominal") or "(?)"
    # `year_label` similar — synthesise from year_first/_last below if absent.

    # year_ranges + year_first/_last — UNION across members per
    # data-accumulation principle. The widest combined range envelope
    # drives year_first/_last; year_ranges keeps the de-overlapped
    # detail so per-year specimen markers in the timeline reflect every
    # source's recorded minting year.
    union_yr = _union_year_ranges(members)
    if union_yr is not None:
        if len(union_yr) == 1 and union_yr[0][0] == union_yr[0][1]:
            # Single-year — drop year_ranges (V1-compat: omit when trivial)
            out["year_first"] = union_yr[0][0]
            out["year_last"] = union_yr[0][1]
        else:
            out["year_first"] = min(r[0] for r in union_yr)
            out["year_last"] = max(r[1] for r in union_yr)
            out["year_ranges"] = union_yr
    # year_label — top-auth wins for display (synthesise if missing
    # but year info exists)
    year_label = _take_first_non_none(sorted_members, "year_label")
    if year_label is not None:
        out["year_label"] = year_label
    elif "year_first" in out and "year_last" in out:
        if out["year_first"] == out["year_last"]:
            out["year_label"] = str(out["year_first"])
        else:
            out["year_label"] = f"{out['year_first']}-{out['year_last']}"

    # Other scalar text fields — gap-fill across members (log conflicts).
    # `ruler` uses _normalise_ruler equivalence to suppress pure-punctuation
    # variants («Frederik IV.» vs «Frederik IV») from the conflict log:
    # those are NOT real disagreements about who the ruler was, just
    # different spelling conventions across sources. The merger preserves
    # the top-authority spelling verbatim in `out[field]` — only the
    # conflict log is normalised.
    for field in ("fraction", "nominal", "ruler", "mintmaster",
                  "inscription_obv", "inscription_rev"):
        v = _take_first_non_none(sorted_members, field)
        if v is not None:
            out[field] = v
            # Log conflicts when ≥2 distinct values exist across members
            def _conflict_key(val):
                s = val if isinstance(val, str) else str(val)
                if field == "ruler":
                    return _normalise_ruler(s)
                return s
            seen: list[str] = [v if isinstance(v, str) else str(v)]
            seen_keys: set[str] = {_conflict_key(seen[0])}
            for m in sorted_members[1:]:
                mv = m.get(field)
                if mv is None:
                    continue
                mv_repr = mv if isinstance(mv, str) else str(mv)
                mv_key = _conflict_key(mv_repr)
                if mv_key not in seen_keys:
                    seen.append(mv_repr)
                    seen_keys.add(mv_key)
                    conflicts.append((field, seen[0], mv_repr))

    # Multi-mint union
    mint = _collect_mints(members)
    if mint is not None:
        out["mint"] = mint

    # Catalog deep-merge (entity-aware KM)
    cat, cat_conflicts = _deep_merge_catalog(members, entity_id)
    if cat:
        out["catalog"] = cat
    conflicts.extend(cat_conflicts)

    # Metal — gap-fill
    metal = _take_first_non_none(sorted_members, "metal")
    if metal:
        out["metal"] = metal

    # Verification flags — OR-merge (any source attests counts)
    for field in ("metal_verified", "fineness_verified", "weight_rough_verified",
                  "diameter_mm_verified", "mint_verified", "verified",
                  "year_verified"):
        v = _or_merge_verified(sorted_members, field)
        if v is not None:
            out[field] = v

    # Multi-source measurement lists (every reading preserved)
    fine = _collect_field_list(members, "fineness")
    if fine:
        out["fineness"] = fine
    weights = _collect_field_list(members, "weight_rough_g")
    if weights:
        out["weight_rough_g"] = weights
    diameters = _collect_field_list(members, "diameter_mm")
    if diameters:
        out["diameter_mm"] = diameters

    # Sources union
    sources = _collect_sources(members)
    if sources:
        out["sources"] = sources

    # Notes — gap-fill (next non-None from lower authority if primary lacks)
    note = _take_first_non_none(sorted_members, "note")
    if note is not None:
        out["note"] = note
    vnote = _take_first_non_none(sorted_members, "verification_note")
    if vnote is not None:
        out["verification_note"] = vnote

    # issuing_entity — gap-fill (regroup classifier already set on every member)
    ie = _take_first_non_none(sorted_members, "issuing_entity")
    if ie is not None:
        out["issuing_entity"] = ie

    # Hede-attested Müntzfuß ratio (per-page «Marken fin udbragt til N
    # speciedaler/rd.kr/...» quote). Only ONE source publishes this —
    # the Hede 1971 catalogue via danskmoent.dk pages — so authority-
    # ordering doesn't apply; take whichever member carries it. Pass-
    # through the dict verbatim.
    yld = _take_first_non_none(sorted_members, "hede_muentzfuss_yield")
    if yld is not None:
        out["hede_muentzfuss_yield"] = yld

    # Audit trail
    out["composed_of"] = composed_of

    return out, conflicts


def _unified_id_for_class(members: list[dict]) -> str:
    """Pick the unified id per §5.2 authority rule: top-authority member's id
    with `unified-` prefix."""
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    primary = sorted_members[0]
    return f"unified-{primary['id']}"


# ---------------------------------------------------------------------------
# Decision file I/O
# ---------------------------------------------------------------------------


def _load_decisions(entity_id: str) -> dict:
    """Load explicit merge_decisions/<entity>.yml if present.
    Returns {merges: [{members, reason}], no_merges: [...]}"""
    path = V2_MERGE_DECISIONS / f"{entity_id}.yml"
    if not path.exists():
        return {"merges": [], "no_merges": []}
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "merges": doc.get("merges", []) or [],
        "no_merges": doc.get("no_merges", []) or [],
    }


# ---------------------------------------------------------------------------
# Per-entity processing
# ---------------------------------------------------------------------------


def _load_seeds_for_entity(entity_id: str) -> list[dict]:
    """Walk data/v2/seed/<source>/<entity>.yml across all sources.
    Returns flat list of coin dicts; each dict has its `id` for identification."""
    coins: list[dict] = []
    if not V2_SEED.exists():
        return coins
    for src_dir in sorted(V2_SEED.iterdir()):
        if not src_dir.is_dir():
            continue
        path = src_dir / f"{entity_id}.yml"
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for c in doc.get("coins") or []:
            if isinstance(c, dict) and c.get("id"):
                coins.append(c)
    return coins


def process_entity(entity_id: str) -> dict:
    """Returns:
      {
        'entity_id': str,
        'seeds_count': int,
        'unified_entries': [unified_coin_dict, ...],
        'unified_count': int,
        'confident_merges': [{members, score}, ...],
        'low_confidence_pairs': [{members, why, signals}, ...],
        'forced_merges': [{members, reason}, ...],
        'forced_no_merges': [{members, reason}, ...],
      }
    """
    seeds = _load_seeds_for_entity(entity_id)
    # Drop synthetic «catalog-overview» entries the parser sometimes
    # emits when a catalog index page (rather than a coin page) gets
    # processed as if it were a real entry. Their `nominal` field
    # carries page-title fragments like «- oversigt efter Galster» /
    # «overview of Y» — clearly not a numismatic denomination. The
    # seed file itself is left untouched (fix belongs in the parser,
    # tracked separately); we just skip them here so they don't
    # generate spurious low-confidence pairs against real coins.
    def _is_overview_page(c: dict) -> bool:
        nom = (c.get("nominal") or "").strip()
        if not nom:
            return False
        nom_lower = nom.lower()
        return (
            nom_lower.startswith("-")  # catalog-overview title prefix
            or "oversigt" in nom_lower
            or "overview" in nom_lower
        )
    pre_filter_count = len(seeds)
    seeds = [c for c in seeds if not _is_overview_page(c)]
    overview_dropped = pre_filter_count - len(seeds)

    decisions = _load_decisions(entity_id)

    # D33 reign index — built ONCE per entity from members that DO
    # carry an attested ruler. Used by `match_pair` to fill ruler=null
    # gaps when (and ONLY when) a coin's covered year(s) attest a
    # single ruler. Transition / co-regent years carry multi-element
    # sets and stay null per user direction («краще null ніж
    # неправдивий nonull»).
    reign_index = _build_reign_index(seeds, entity_id)

    seeds_by_id: dict[str, dict] = {c["id"]: c for c in seeds}
    uf = UnionFind()
    # Ensure all ids are in uf so singleton classes show up.
    for cid in seeds_by_id:
        uf.find(cid)

    # 1. Apply explicit no_merges first (curator decisions take precedence
    #    over any auto-rule).
    forced_no_merges: list[dict] = []
    for entry in decisions["no_merges"]:
        members = entry.get("members") or []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                uf.add_no_merge(members[i], members[j])
        forced_no_merges.append(entry)

    # 2. PRE-PASS: run matcher on every pair, register no_match pairs in
    #    union-find BEFORE attempting any union. This guarantees that
    #    transitive merges (A↔B, A↔C both confident, B↔C no_match) DO
    #    NOT silently override the B↔C no_match — union() refuses any
    #    cross-class merge that would put a no_merge pair in the same
    #    class.
    confident_pairs: list[dict] = []
    low_confidence: list[dict] = []
    ids = sorted(seeds_by_id)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a_id, b_id = ids[i], ids[j]
            if not uf.can_union(a_id, b_id):
                continue
            result = match_pair(seeds_by_id[a_id], seeds_by_id[b_id], entity_id,
                                reign_index=reign_index)
            if result["decision"] == "no_match":
                uf.add_no_merge(a_id, b_id)
            elif result["decision"] == "confident":
                confident_pairs.append({
                    "a": a_id, "b": b_id,
                    "primary": result["primary"],
                    "fallback": result["fallback"],
                })
            elif result["decision"] == "low_confidence":
                low_confidence.append({
                    "members": [a_id, b_id],
                    "primary": result["primary"],
                    "fallback": result["fallback"],
                    "why": result["why"],
                })

    # 2b. POST-PRE-PASS: Single-candidate promotion for null primary
    # signals (`ruler`, `nominal`).
    #
    # When a coin's `ruler` is null AND its D33 reign-index inference
    # also returns None (single-year-on-transition like 1648 or 1670),
    # OR its `nominal` is null (parser-gap on Galster / Bruun / etc.),
    # `match_pair` leaves the pair as low_confidence even though the
    # other side carries an attested value — primary_true stalls at 2.
    # To recover safely without inviting cross-reign / cross-type
    # mismerges, scan the low_confidence pairs FOR EACH null-attribute
    # coin and check whether every cross-source candidate attests THE
    # SAME value for that field. When the candidate set's union is
    # exactly one, promote ALL of that coin's low_confidence pairs to
    # confident — the other side has uniquely identified the missing
    # attribute. When the union has >1 distinct values (e.g. a 1648
    # 1/4 Speciedaler with both CHR IV and FR III Hede candidates),
    # it's genuinely ambiguous and stays low_confidence for curator
    # review.
    def _attested_value(coin: dict, field: str) -> str | None:
        if field == "ruler":
            return _attestation_ruler(coin)
        if field == "nominal":
            return _normalise_nominal(coin.get("nominal")) or None
        return None

    def _coin_self_value(coin: dict, field: str) -> str | None:
        if field == "ruler":
            return _normalise_ruler(coin.get("ruler")) or None
        if field == "nominal":
            return _normalise_nominal(coin.get("nominal")) or None
        return None

    pairs_to_promote: dict[tuple[str, str], dict] = {}
    null_attribute_coins: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for lcp in low_confidence:
        a_id, b_id = lcp["members"]
        for field in ("ruler", "nominal"):
            # The pair must be at the «one null one attested» pattern
            # for this specific field — primary[field] is None in the
            # matcher's output.
            if lcp["primary"].get(field) is not False and lcp["primary"].get(field) is not True:
                # field is None (or absent) on the pair
                for null_side, attested_side in [(a_id, b_id), (b_id, a_id)]:
                    if _coin_self_value(seeds_by_id[null_side], field):
                        continue
                    # For ruler: skip if the index would have inferred it
                    # (those would already be confident). For nominal:
                    # no inference path, all genuine nulls qualify.
                    if field == "ruler" and _infer_ruler(seeds_by_id[null_side], reign_index):
                        continue
                    attested = _attested_value(seeds_by_id[attested_side], field)
                    if not attested:
                        continue
                    null_attribute_coins[(null_side, field)].append({
                        "pair": lcp,
                        "attested_value": attested,
                    })
                    break

    def _coin_weight(coin: dict) -> float | None:
        w = coin.get("weight_rough_g")
        if isinstance(w, (int, float)):
            return float(w)
        if isinstance(w, list):
            for item in w:
                if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
                    return float(item["value"])
        return None

    for (null_id, field), candidates in null_attribute_coins.items():
        values_attested = {c["attested_value"] for c in candidates}
        winning_candidates = candidates
        winning_value = None

        if len(values_attested) == 1:
            # Unique attested value across all candidates — promote all.
            winning_value = next(iter(values_attested))
        else:
            # Multiple distinct attested values for this null field.
            # Weight tie-breaker: if the null-coin has a recorded weight
            # AND exactly ONE candidate's weight matches within ±2%, the
            # weight uniquely identifies the matching type — promote ONLY
            # that pair, leave the others as low_confidence. Same-weight
            # across different nominals is essentially impossible in
            # numismatic practice (1 Gulden ≈ 30g, ½ Gulden ≈ 15g — the
            # weight IS the denomination signature).
            null_coin = seeds_by_id.get(null_id)
            if null_coin is None:
                continue
            null_weight = _coin_weight(null_coin)
            if null_weight is None or null_weight <= 0:
                continue
            weight_matched = []
            for c in candidates:
                other_id = next(
                    iid for iid in c["pair"]["members"] if iid != null_id
                )
                other_coin = seeds_by_id.get(other_id)
                if other_coin is None:
                    continue
                ow = _coin_weight(other_coin)
                if ow is None or ow <= 0:
                    continue
                if abs(ow - null_weight) / null_weight < 0.02:
                    weight_matched.append(c)
            if len(weight_matched) != 1:
                continue
            winning_candidates = weight_matched
            winning_value = weight_matched[0]["attested_value"]

        for c in winning_candidates:
            a_id, b_id = c["pair"]["members"]
            key = (a_id, b_id)
            if key not in pairs_to_promote:
                primary = dict(c["pair"]["primary"])
                primary[field] = True
                why_lines = list(c["pair"]["why"])
                if len(values_attested) == 1:
                    why_lines.append(
                        f"promoted: single cross-source candidate's {field} attestation is consistent ({winning_value!r})"
                    )
                else:
                    why_lines.append(
                        f"promoted: weight tie-breaker uniquely selects {field}={winning_value!r} (weight {null_weight} ± 2 %)"
                    )
                pairs_to_promote[key] = {
                    "a": a_id, "b": b_id,
                    "primary": primary,
                    "fallback": c["pair"]["fallback"],
                    "why": why_lines,
                }
            else:
                pairs_to_promote[key]["primary"][field] = True
                if len(values_attested) == 1:
                    pairs_to_promote[key]["why"].append(
                        f"promoted: single cross-source candidate's {field} attestation is consistent ({winning_value!r})"
                    )
                else:
                    pairs_to_promote[key]["why"].append(
                        f"promoted: weight tie-breaker uniquely selects {field}={winning_value!r} (weight {null_weight} ± 2 %)"
                    )

    if pairs_to_promote:
        promoted_keys = set(pairs_to_promote.keys())
        confident_pairs.extend(pairs_to_promote.values())
        low_confidence = [
            lcp for lcp in low_confidence
            if tuple(lcp["members"]) not in promoted_keys
        ]

    # 3. Apply explicit merges (curator wins over auto-rules, but still
    #    respects already-recorded no_match — curator must explicitly
    #    add the conflicting pair to `merges:` to override, in which case
    #    they must ALSO remove the implicit no_match by their reasoning).
    forced_merges: list[dict] = []
    for entry in decisions["merges"]:
        members = entry.get("members") or []
        for i in range(1, len(members)):
            uf.union(members[0], members[i])
        forced_merges.append(entry)

    # 4. Apply confident auto-merges. union() now refuses any merge
    #    that would create a class containing a no_match pair.
    confident_merges: list[dict] = []
    transitivity_blocks: list[dict] = []
    for cp in confident_pairs:
        ok, blocking = uf.union(cp["a"], cp["b"])
        if ok:
            confident_merges.append({
                "members": [cp["a"], cp["b"]],
                "primary": cp["primary"],
                "fallback": cp["fallback"],
            })
        elif blocking:
            transitivity_blocks.append({
                "would_merge": [cp["a"], cp["b"]],
                "blocked_by_no_match": sorted(blocking),
            })

    # 4. Build unified entries from equivalence classes
    classes = uf.classes()
    unified_entries: list[dict] = []
    merge_conflicts: list[dict] = []  # data-loss visibility: per-unified conflicts
    for class_root, member_ids in sorted(classes.items()):
        member_coins = [seeds_by_id[mid] for mid in sorted(member_ids)]
        unified_id = _unified_id_for_class(member_coins)
        unified, conflicts = build_unified(member_coins, unified_id, entity_id)
        unified_entries.append(unified)
        if conflicts and len(member_coins) > 1:
            merge_conflicts.append({
                "unified_id": unified_id,
                "members": sorted(member_ids),
                # Convert tuples → dicts so yaml.safe_load can read them back
                "field_conflicts": [
                    {"field": f, "top_authority_value": t, "other_value": o}
                    for (f, t, o) in conflicts
                ],
            })

    # Deterministic order
    unified_entries.sort(key=lambda u: u["id"])

    return {
        "entity_id": entity_id,
        "seeds_count": len(seeds),
        "unified_entries": unified_entries,
        "unified_count": len(unified_entries),
        "confident_merges": confident_merges,
        "low_confidence_pairs": low_confidence,
        "forced_merges": forced_merges,
        "forced_no_merges": forced_no_merges,
        "merge_conflicts": merge_conflicts,
        "transitivity_blocks": transitivity_blocks,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _emit_unified_yaml(entity_id: str, unified_entries: list[dict],
                       seeds_count: int) -> str:
    today = date.today().isoformat()
    header = (
        f"# V2 seed_unified for political entity `{entity_id}`.\n"
        f"# Generated {today} by scripts/maintenance/merge_seeds_cross_source.py\n"
        f"# from data/v2/seed/<source>/{entity_id}.yml across all sources.\n"
        f"#\n"
        f"# Input: {seeds_count} per-source seed entries.\n"
        f"# Output: {len(unified_entries)} unified entries (one per physical coin).\n"
        f"#\n"
        f"# Each unified entry's `composed_of` lists the per-source seeds\n"
        f"# it absorbed via the §5.2 match hierarchy. `weight_rough_g[]`,\n"
        f"# `fineness[]`, `diameter_mm[]` are multi-source lists preserving\n"
        f"# every reading per CLAUDE.md §9a. `sources[]` is the union.\n\n"
    )
    payload = {
        "id": entity_id,
        "generated_at": today,
        "coins": unified_entries,
    }
    return header + yaml.dump(payload, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=120)


def _emit_match_uncertainty(entity_id: str, low_conf: list[dict],
                             merge_conflicts: list[dict] | None = None,
                             transitivity_blocks: list[dict] | None = None) -> str:
    today = date.today().isoformat()
    header = (
        f"# Match uncertainty for entity `{entity_id}` — gitignored diagnostic.\n"
        f"# Regenerated {today} by merge_seeds_cross_source.py.\n"
        f"#\n"
        f"# Two sections (both surface data the auto-merger couldn't handle\n"
        f"# without losing information):\n"
        f"#\n"
        f"# 1. low_confidence_pairs — seed-pairs that look LIKE same coin\n"
        f"#    but matcher's primary signals were insufficient to confirm.\n"
        f"#    Resolution: add to merge_decisions/{entity_id}.yml::merges\n"
        f"#    OR extend matcher rules.\n"
        f"#\n"
        f"# 2. merge_conflicts — successful merges where scalar fields\n"
        f"#    DISAGREED across members (top-authority value kept in\n"
        f"#    unified entry; lower-authority value would be lost without\n"
        f"#    this log). Resolution: either accept top-auth, OR widen\n"
        f"#    the unified schema to preserve both, OR fix the parser\n"
        f"#    that emitted the wrong value.\n"
        f"#\n"
        f"# DO NOT edit this file — it's overwritten on every run.\n"
        f"# Curator decisions go into data/v2/merge_decisions/{entity_id}.yml.\n\n"
    )
    payload = {
        "entity_id": entity_id,
        "generated_at": today,
        "low_confidence_pairs": low_conf,
        "merge_conflicts": merge_conflicts or [],
        "transitivity_blocks": transitivity_blocks or [],
    }
    return header + yaml.dump(payload, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=120)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _all_entities() -> list[str]:
    """All entity ids that have at least one seed yaml."""
    seen: set[str] = set()
    if not V2_SEED.exists():
        return []
    for src_dir in V2_SEED.iterdir():
        if not src_dir.is_dir():
            continue
        for p in src_dir.glob("*.yml"):
            seen.add(p.stem)
    return sorted(seen)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write outputs (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Write data/v2/seed_unified/ + data/v2/match_uncertainty/")
    parser.add_argument("--entity", help="Process only this entity")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all low-confidence pairs (default: top 10 per entity)")
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False

    entities = [args.entity] if args.entity else _all_entities()
    if not entities:
        print("No V2 seed files found under data/v2/seed/.")
        return 0

    print(f"Processing {len(entities)} entit(y/ies)...\n")

    totals = Counter()
    for ent in entities:
        result = process_entity(ent)
        totals["seeds"] += result["seeds_count"]
        totals["unified"] += result["unified_count"]
        totals["confident_merges"] += len(result["confident_merges"])
        totals["low_confidence"] += len(result["low_confidence_pairs"])
        totals["forced_merges"] += len(result["forced_merges"])
        totals["forced_no_merges"] += len(result["forced_no_merges"])
        totals["merge_conflicts"] += len(result.get("merge_conflicts", []))

        reduction = result["seeds_count"] - result["unified_count"]
        line = (f"{ent:36s}  "
                f"seeds:{result['seeds_count']:4d}  → "
                f"unified:{result['unified_count']:4d}  "
                f"(−{reduction:3d})  "
                f"conf:{len(result['confident_merges']):3d}  "
                f"lowconf:{len(result['low_confidence_pairs']):3d}  "
                f"conflicts:{len(result.get('merge_conflicts', [])):3d}")
        if result["forced_merges"] or result["forced_no_merges"]:
            line += (f"  forced:{len(result['forced_merges'])}/"
                     f"{len(result['forced_no_merges'])}")
        print(line)

        if args.verbose and result["low_confidence_pairs"]:
            for pair in result["low_confidence_pairs"][:5]:
                print(f"    ? {pair['members']}: {pair['why']}")
            if len(result["low_confidence_pairs"]) > 5:
                print(f"    ? ... and {len(result['low_confidence_pairs']) - 5} more")

        if args.apply:
            V2_SEED_UNIFIED.mkdir(parents=True, exist_ok=True)
            (V2_SEED_UNIFIED / f"{ent}.yml").write_text(
                _emit_unified_yaml(ent, result["unified_entries"],
                                   result["seeds_count"]),
                encoding="utf-8",
            )
            if (result["low_confidence_pairs"] or result.get("merge_conflicts")
                    or result.get("transitivity_blocks")):
                V2_MATCH_UNCERTAINTY.mkdir(parents=True, exist_ok=True)
                (V2_MATCH_UNCERTAINTY / f"{ent}.yml").write_text(
                    _emit_match_uncertainty(
                        ent,
                        result["low_confidence_pairs"],
                        result.get("merge_conflicts"),
                        result.get("transitivity_blocks"),
                    ),
                    encoding="utf-8",
                )
            else:
                stale = V2_MATCH_UNCERTAINTY / f"{ent}.yml"
                if stale.exists():
                    stale.unlink()

    print()
    print(f"=== Totals ===")
    print(f"  Per-source seeds total:     {totals['seeds']:>5d}")
    print(f"  Unified entries total:      {totals['unified']:>5d}")
    print(f"  Reduction (merges):         {totals['seeds'] - totals['unified']:>5d}")
    print(f"  Confident auto-merges:      {totals['confident_merges']:>5d}")
    print(f"  Low-confidence pairs:       {totals['low_confidence']:>5d}")
    print(f"  Merge conflicts (logged):   {totals['merge_conflicts']:>5d}")
    print(f"  Forced merges (decisions):  {totals['forced_merges']:>5d}")
    print(f"  Forced no_merges (decisions): {totals['forced_no_merges']:>3d}")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
    else:
        print(f"\n✓ Wrote unified yamls to {V2_SEED_UNIFIED}/")
        print(f"  Match uncertainty diagnostics to {V2_MATCH_UNCERTAINTY}/ "
              f"(gitignored)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
