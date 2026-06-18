#!/usr/bin/env python3
"""V2 Phase 4 — absorb seed_unified entries into existing V2 final foundation.

Input  : data/v2/seed_unified/<entity>.yml  (cross-source merged per coin)
         data/v2/final/<entity>.yml          (V1-bootstrap foundation, frozen
                                              per D3 except for additive
                                              enrichment from this script)
Output : updated data/v2/final/<entity>.yml
         data/v2/classification_decisions/<entity>.yml  (pending genuinely-new
                                                         coins for curator)

For each entry in seed_unified, find a matching entry in final via the
§5.2 match hierarchy (D10). When matched, ENRICH the final entry:
  - Add unified.id to final.composed_of (D9)
  - UNION year_ranges across final + all composed_of members (D19)
  - Multi-source merge of weight_rough_g / fineness / diameter_mm (D17, §9a)
  - Union sources / mint
  - Accumulate catalog refs to list-form on conflict (D18)
  - OR-merge verification flags (D20)
  - Gap-fill scalar fields when final lacks (D21)

Foundation-immutable fields per DF1 (current default — strict):
  fuss, phase, kind, fraction, nominal, ruler, mintmaster, issuing_entity

If no match found → genuinely new physical coin. Two paths:
  1. Auto-classify via CLAUDE.md §8a (Müntzfuß-disambiguation pipeline) —
     to-be-built; for MVP, surface to classification_decisions/<entity>.yml
     pending list.
  2. Curator declares in classification_decisions/<entity>.yml::assignments
     {coin_id: {fuss, phase, kind}}; on next run, absorb adds the entry
     to final with the declared classification.

The script is IDEMPOTENT (D25):
  - already-absorbed unified entries (in some final.composed_of) skipped
  - re-derived enrichment fields stable across runs given stable input
  - merge_seed write preserves curator edits on final entries

Usage:
  scripts/maintenance/absorb_seeds_into_final_v2.py --dry-run    # report
  scripts/maintenance/absorb_seeds_into_final_v2.py --apply      # write
  scripts/maintenance/absorb_seeds_into_final_v2.py --entity X   # one entity
"""

from __future__ import annotations

import argparse
import copy
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_SEED = ROOT / "data" / "v2" / "seed"
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_CLASSIFICATION_DECISIONS = ROOT / "data" / "v2" / "classification_decisions"
V2_MERGE_DECISIONS = ROOT / "data" / "v2" / "merge_decisions"
V2_OVERMERGE_PURGE = ROOT / "data" / "v2" / "overmerge_purge_allowlist.yml"

sys.path.insert(0, str(ROOT / "scripts"))
from lib.fraction_infer import infer_fraction, load_fuss_fractions  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402
from lib.v2_seed_writer import (  # noqa: E402
    _is_out_of_scope_nominal,
    _is_out_of_scope_catalog,
    _is_out_of_scope_year,
    _normalise_nominal,
    _canonicalise_mint,
    _normalise_catalog,
    _extract_mint_from_nominal,
)

# Reuse match-strategy + enrichment helpers from Phase 3.2.
# Both files share the same data-accumulation conventions (D17-D21).
from maintenance.merge_seeds_cross_source import (  # noqa: E402
    match_pair,
    _build_reign_index,
    _collect_field_list,
    _collect_sources,
    _collect_mints,
    _collect_metal,
    _deep_merge_catalog,
    _union_year_ranges,
    _format_year_label,
    _take_first_non_none,
    _or_merge_verified,
    _catalog_refs,
    _shares_unique_id_ref,
    _shares_type_level_catalog,
    _nominal_wildcard_match,
    _is_forgery_nominal,
    # The merge module's nominal normaliser applies the FULL synonym table
    # (Ducat→dukat, Dobbelt X→2 X, Guldkrone→gold krone, «(?)»→empty); the
    # v2_seed_writer `_normalise_nominal` imported above does NOT. The
    # re-validate identity check MUST use the same normaliser as match_pair's
    # nominal discriminator, else synonym pairs («1 Ducat» vs «1 Dukat») read
    # as genuine mismatches and get false-evicted.
    _normalise_nominal as _mg_normalise_nominal,
)
from lib.catalog_codes import normalise_catalog as _fold_catalog_indices  # noqa: E402


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _load_yaml(p: Path) -> dict:
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _ruamel_to_dict(c):
    """Delegate to lib.v2_resolver.ruamel_to_plain."""
    from lib.v2_resolver import ruamel_to_plain
    return ruamel_to_plain(c)


def _entities_with_seed_unified() -> list[str]:
    if not V2_SEED_UNIFIED.exists():
        return []
    return sorted(p.stem for p in V2_SEED_UNIFIED.glob("*.yml"))


def _km_bases(coin: dict) -> set:
    """SET of base KM tokens of a coin — handles scalar, list-form
    (multi-source / curator-merged KM accumulation, e.g. ['21','21.1']), and
    dict-form (register-keyed). Each token: leading optional-letter + integer
    part, dropping dot-subvariant + trailing letters ('A110'→'A110', '70.1'→
    '70', '11a'→'11', '156,3'→'156'). Empty set when KM is absent.

    Two coins SHARE a KM type iff their base-sets intersect; they are GENUINELY
    KM-divergent (different Krause type per CLAUDE.md §9.4) iff both base-sets
    are non-empty AND DISJOINT. Sub-variants tolerated ('11'≡'11a','70'≡'70.1');
    the A-prefix is PRESERVED (KM A110 ≠ KM 110). List-form KM must NOT be
    str()'d whole (that yields garbage like "['21','21.1']" → false divergence
    — the 44-false-positive bug, 2026-05-31)."""
    km = (coin.get("catalog") or {}).get("km")
    if km in (None, "", []):
        return set()
    if isinstance(km, dict):
        vals = [v for v in km.values() if v not in (None, "", [])]
    elif isinstance(km, list):
        vals = [v for v in km if v not in (None, "", [])]
    else:
        vals = [km]
    out = set()
    for v in vals:
        m = re.match(r"^([A-Za-z]*)(\d+)", str(v).strip())
        out.add((m.group(1).upper() + m.group(2)) if m else str(v).strip())
    return out


# ---------------------------------------------------------------------------
# Weightless-museum specimen suppression (§9a fallback — thin by HIDING, not
# deleting). The §9a weight-sort thinning keeps min/middle/max of a weight
# cluster; it can't fire when the specimens carry NO weight (KMM rarely
# weighs small billon coins). For those over-collections we SUPPRESS the
# surplus citations — keep them in the data, hide them from the render —
# per the data-accumulation principle (nothing is lost). Keep ~3 visible:
# imaged-first (the KMM record has a still photo), then lowest object-id.
# User decision 2026-06-04.
# ---------------------------------------------------------------------------
import json as _json  # noqa: E402

_KMK_CACHE_DIR = ROOT / "scripts" / "cache" / "kmk"
_KMM_IMAGE_MEMO: dict[str, bool] = {}
_KMM_WEIGHT_MEMO: dict[str, bool] = {}


def _kmm_nid_from_url(url):
    if not url:
        return None
    m = re.search(r"/KMM/object/(\d+)", str(url))
    return m.group(1) if m else None


def _kmm_specimen_has_image(nid: str) -> bool:
    """True when the KMM (Nationalmuseet) record has a still-photo asset.
    Memoised cache read — maintenance-side only; the build never reads cache.
    Verified equivalent to the natmus page state: records with a still asset
    show photo(s); records without show «Genstanden er endnu ikke
    affotograferet» (2026-06-08 live spot-check, KMM 290904 vs 123284)."""
    if nid in _KMM_IMAGE_MEMO:
        return _KMM_IMAGE_MEMO[nid]
    has = False
    try:
        d = _json.loads((_KMK_CACHE_DIR / f"{nid}.json").read_text())
        rel = d.get("related") or {}
        assets = rel.get("assets") or [] if isinstance(rel, dict) else []
        has = any(isinstance(a, dict) and a.get("type") == "still" for a in assets)
    except (FileNotFoundError, ValueError):
        has = False
    _KMM_IMAGE_MEMO[nid] = has
    return has


_KMM_WEIGHT_VALUE_MEMO: dict[str, float | None] = {}


def _kmm_specimen_weight(nid: str) -> float | None:
    """The KMM record's Vægt (weight, g) value, or None when absent.
    Memoised cache read — maintenance-side only."""
    if nid in _KMM_WEIGHT_VALUE_MEMO:
        return _KMM_WEIGHT_VALUE_MEMO[nid]
    val = None
    try:
        d = _json.loads((_KMK_CACHE_DIR / f"{nid}.json").read_text())
        ms = d.get("measurements") or []
        for m in ms:
            if (isinstance(m, dict) and m.get("dimension") == "Vægt"
                    and isinstance(m.get("data"), (int, float))):
                val = float(m["data"])
                break
    except (FileNotFoundError, ValueError):
        val = None
    _KMM_WEIGHT_VALUE_MEMO[nid] = val
    return val


def _kmm_specimen_has_weight(nid: str) -> bool:
    """True when the KMM record carries a Vægt (weight) measurement.
    Memoised cache read — maintenance-side only."""
    if nid in _KMM_WEIGHT_MEMO:
        return _KMM_WEIGHT_MEMO[nid]
    has = _kmm_specimen_weight(nid) is not None
    _KMM_WEIGHT_MEMO[nid] = has
    return has


_KEEP_KMM_IMAGE_ONLY = 3   # image but no weight → keep 3
_KEEP_KMM_PURE = 1         # neither weight nor image → keep 1
# §9a weight-specimen thinning: when one resource (KMM) over-collects
# weight-giving specimens of the same coin, keep only min / middle / max
# by weight — the intermediates add no variance-envelope information.
_KMM_WEIGHT_THIN_THRESHOLD = 5   # thin only when ≥5 weight-giving KMM specimens


def _suppress_weightless_museum_overcollection(coin: dict) -> int:
    """Hide surplus low-information KMM specimen citations via `display: false`
    (data kept — §9a accumulation — just not rendered on the page). Three
    categories, keyed by what the KMM record carries (user direction
    2026-06-08):

      • WEIGHT (with or without an image) — §9a weight-specimen thinning:
        when ≥5 weight-giving KMM specimens of the same coin pile up, keep
        only min / middle / max by weight (the intermediates add no
        variance-envelope info — all KMM specimens share absent fineness,
        so the bucket is uniform per §9a). The dropped specimens' CITATIONS
        are hidden here AND their matching `weight_rough_g` readings are
        hidden (by value) so the weight column collapses to 3 spans. Catalog
        refs are NOT touched — they're accumulated on the merged entry, so
        unique Schou/sub-variant indices survive (user direction).
      • IMAGE only (no weight) — keep 3 (lowest object-id), hide the rest.
      • NEITHER weight nor image (natmus «Genstanden er endnu ikke
        affotograferet»; 79 % of all KMM cites — bare «museum holds a
        specimen») — keep 1, hide the rest.

    Fires regardless of whether the coin has weight from other sources.
    Idempotent + deterministic. Returns the count newly hidden."""
    srcs = coin.get("sources") or []
    kmm = [s for s in srcs
           if isinstance(s, dict) and _kmm_nid_from_url(s.get("url"))]
    if not kmm:
        return 0
    weight_giving, image_only, pure = [], [], []
    for s in kmm:
        nid = _kmm_nid_from_url(s["url"])
        w = _kmm_specimen_weight(nid)
        if w is not None:
            weight_giving.append((s, nid, w))
        elif _kmm_specimen_has_image(nid):
            image_only.append(s)
        else:
            pure.append(s)
    n = 0

    def _cap(group, keep):
        nonlocal n
        ordered = sorted(group, key=lambda s: int(_kmm_nid_from_url(s["url"])))
        for i, s in enumerate(ordered):
            if i < keep:
                s.pop("display", None)
            else:
                if s.get("display") is not False:
                    n += 1
                s["display"] = False

    # --- §9a weight-specimen thinning over the weight-giving KMM bucket ---
    kept_weights: set[float] | None = None  # None = no thinning (keep all)
    if len(weight_giving) >= _KMM_WEIGHT_THIN_THRESHOLD:
        # deterministic sort: by weight, tie-break by object-id
        wg = sorted(weight_giving, key=lambda t: (t[2], int(t[1])))
        keep_idx = {0, len(wg) // 2, len(wg) - 1}
        kept_weights = set()
        for i, (s, nid, w) in enumerate(wg):
            if i in keep_idx:
                s.pop("display", None)
                kept_weights.add(round(w, 5))
            else:
                if s.get("display") is not False:
                    n += 1
                s["display"] = False
    else:
        for s, nid, w in weight_giving:
            s.pop("display", None)

    _cap(image_only, _KEEP_KMM_IMAGE_ONLY)
    _cap(pure, _KEEP_KMM_PURE)

    # Hide the weight_rough_g readings of the dropped KMM specimens. The
    # KMM weight entries carry source label "kmk" with no nid, so we match
    # by value: keep only entries whose rounded value is one of the kept
    # min/middle/max weights; flag the rest display:false (data kept).
    if kept_weights is not None:
        wfield = coin.get("weight_rough_g")
        if isinstance(wfield, list):
            for fv in wfield:
                if not isinstance(fv, dict):
                    continue
                if str(fv.get("source", "")).strip().lower() != "kmk":
                    continue
                val = fv.get("value")
                if not isinstance(val, (int, float)):
                    continue
                if round(float(val), 5) in kept_weights:
                    fv.pop("display", None)
                else:
                    fv["display"] = False
    return n


# ---------------------------------------------------------------------------
# Foundation-immutable rule (per DF1, current default)
# ---------------------------------------------------------------------------

# Fields that NEVER change on an existing final entry. V1 bootstrap set
# these via curator decisions baked into V1; V2 doesn't second-guess
# until DF1 is resolved.
_FOUNDATION_IMMUTABLE_FIELDS = frozenset({
    "fuss", "phase", "kind", "fraction", "nominal",
    "ruler", "mintmaster", "issuing_entity",
})

# Foundation-immutable fields that may be GAP-FILLED (never overridden) from a
# composed_of member when the foundation value is None — the «non-None wins
# over None» rule. The V1 bootstrap dropped descriptive attributes (ruler:
# 67 entries, mintmaster: 258) that the V2 merger has since resolved on the
# seed_unified bridge; without gap-fill the absorb step copies the None
# verbatim and the resolved value never reaches the rendered final.
#
# fuss / phase / kind are DELIBERATELY excluded: a composed_of member carries
# the seed-pass placeholder («seed_unsorted»), not the curated classification,
# so its "non-None" is not an authoritative value — gap-filling them would
# pull a placeholder into a curated slot. A NON-None foundation value is
# never overridden for any field (V1 curation stays intact).
_FOUNDATION_GAPFILL_FIELDS = _FOUNDATION_IMMUTABLE_FIELDS - {"fuss", "phase", "kind"}


def _enrich_final_entry(final_entry: dict, members: list[dict],
                        entity_id: str | None) -> tuple[dict, list]:
    """Re-derive enrichment fields on a final entry from itself + members
    listed in composed_of. Foundation-immutable fields stay untouched.

    `members` includes the final entry itself FIRST (highest authority —
    foundation wins on scalar gap-fill) and every composed_of member
    after (from seed_unified). Authority sort within members preserves
    foundation-first ordering.
    """
    conflicts: list = []
    # Foundation-immutable fields: copy from final_entry verbatim
    out = {k: v for k, v in final_entry.items()
           if k in _FOUNDATION_IMMUTABLE_FIELDS}
    out["id"] = final_entry["id"]

    # «non-None wins over None» gap-fill: when a foundation descriptive field
    # is None, adopt the first composed_of member's non-None value. Members are
    # authority-sorted (foundation first), so members[1:] are the seed_unified
    # entries whose values the merger already resolved (incl. its transition-
    # year ruler-null rule). Never overrides a non-None foundation value;
    # never touches fuss/phase/kind (see _FOUNDATION_GAPFILL_FIELDS).
    for _fld in _FOUNDATION_GAPFILL_FIELDS:
        if out.get(_fld) is None:
            for _m in members[1:]:
                _mv = _m.get(_fld)
                if _mv not in (None, []):
                    out[_fld] = _mv
                    break

    # year_ranges UNION across members (D19), with a refresh path for
    # pure-absorbed foundations:
    # When `final_entry` is itself a `unified-*` foundation whose
    # composed_of references a SINGLE seed_unified member with the same
    # id (i.e. the foundation IS just a pulled-through seed_unified copy
    # from a previous absorb run, no curator additions), trust the
    # seed_unified member's year_ranges directly. Otherwise — curator-
    # composed foundation with N>=2 members or a foreign id — union
    # across all members so curator-attested years and seed-attested
    # years both survive.
    final_id = final_entry.get("id") or ""
    composed = final_entry.get("composed_of") or []
    pure_absorbed = (
        final_id.startswith("unified-")
        and len(composed) == 1
        and composed[0] == final_id
    )
    seed_member = None
    if pure_absorbed and len(members) >= 2:
        # `members` is [final_entry, seed_unified_member]. Pick the
        # seed_unified one (member with the matching id, NOT the final
        # entry itself) and use its year_ranges as authoritative.
        seed_member = next(
            (m for m in members[1:] if m.get("id") == final_id),
            None,
        )
        if seed_member is not None:
            authoritative_yr = _union_year_ranges([seed_member])
        else:
            authoritative_yr = _union_year_ranges(members)
    else:
        # Curator foundation with seed_unified composed_of members.
        # The foundation's stored `year_first/year_last/year_ranges`
        # are themselves OUTPUTS of prior absorb-run unions, so they
        # can carry years from a stale seed_unified state (e.g.
        # parser-bug years that have since been removed). Re-derive
        # cleanly: when seed_unified members exist, use ONLY them
        # for the year-ranges union — they accumulate everything
        # attested across all current sources. Curator intent that
        # genuinely needs to override (rare) is expressible via
        # `_curation_holds: {year_ranges: "reason"}` on the V1 entry.
        # When no seed_unified members exist (pure-curator entry,
        # composed_of empty), preserve foundation's own year info.
        seed_unified_members = members[1:]
        if seed_unified_members:
            holds = final_entry.get("_curation_holds")
            holds_keys = set(holds.keys() if isinstance(holds, dict)
                             else (holds or []))
            if "year_ranges" in holds_keys or "year_first" in holds_keys:
                # Curator explicitly froze year data — OVERRIDE: the frozen
                # foundation year is authoritative; member year-ranges
                # (including loose reign-window placeholders) must NOT widen
                # it. Was union-preserve until 2026-06-15 — the union let a
                # galster reign-window member (1481-1513, year_verified=false)
                # widen the curated 1497 on unified-dk-bruun-3839, so the hold
                # only froze the display label while year_first/last still
                # leaked to the reign window (and year_first drives §8.2 phase
                # placement). Override blast radius: 0 existing coins — that
                # entry is the only one carrying a year-hold.
                authoritative_yr = _union_year_ranges([final_entry])
            else:
                authoritative_yr = _union_year_ranges(seed_unified_members)
        else:
            authoritative_yr = _union_year_ranges(members)
    if authoritative_yr is not None:
        if len(authoritative_yr) == 1 and authoritative_yr[0][0] == authoritative_yr[0][1]:
            out["year_first"] = authoritative_yr[0][0]
            out["year_last"] = authoritative_yr[0][1]
        else:
            out["year_first"] = min(r[0] for r in authoritative_yr)
            out["year_last"] = max(r[1] for r in authoritative_yr)
            out["year_ranges"] = authoritative_yr
    # year_label — ALWAYS synthesise from the resolved year_ranges
    # (via `_format_year_label`). This guarantees the display label
    # reflects the merged truth «1611, 1613-1614, 1618-1620» rather
    # than a single source's loose «1611-1619» that may have been
    # supplanted by discrete attestations during cross-source merge.
    #
    # The curator-foundation case is the exception: when a V1-curator
    # entry has frozen year info via `_curation_holds: {year_label}`,
    # the curator's hand-written label survives regen unchanged.
    holds = final_entry.get("_curation_holds")
    holds_keys = set(holds.keys() if isinstance(holds, dict)
                     else (holds or []))
    if "year_label" in holds_keys and final_entry.get("year_label"):
        out["year_label"] = final_entry["year_label"]
    elif authoritative_yr is not None:
        out["year_label"] = _format_year_label(authoritative_yr)
    elif "year_first" in out and "year_last" in out:
        out["year_label"] = (str(out["year_first"]) if out["year_first"] == out["year_last"]
                              else f"{out['year_first']}-{out['year_last']}")

    # year_verified OR-merge (any source attests counts)
    yv = _or_merge_verified(members, "year_verified")
    if yv is not None:
        out["year_verified"] = yv

    # Ambiguity-split sweep across members: any member with a scalar
    # mint containing «eller / oder / or / /» indicators (Hede/Galster
    # cataloguer-documented uncertainty) is split in-place to list-form
    # AND its mint_verified forced to False. This matches the seed-writer
    # hygiene step and ensures stale foundation entries from pre-2026-05-25
    # absorb runs don't bleed legacy «X eller Y» scalars into the union.
    _AMBIG_MINT_RE = re.compile(
        r"\s*(?:\beller\b|\boder\b|\bor\b|/)\s*", re.IGNORECASE)

    def _split_ambig(value):
        """Return (new_value, split_happened) — splits scalar AND list-form
        cases (legacy data may have «eller»-scalar embedded as a list item)."""
        if isinstance(value, str) and _AMBIG_MINT_RE.search(value):
            tokens = [t.strip() for t in _AMBIG_MINT_RE.split(value) if t.strip()]
            if len(tokens) >= 2:
                return tokens, True
        if isinstance(value, list):
            out_list = []
            did_split = False
            for item in value:
                if isinstance(item, str) and _AMBIG_MINT_RE.search(item):
                    tokens = [t.strip() for t in _AMBIG_MINT_RE.split(item) if t.strip()]
                    if len(tokens) >= 2:
                        out_list.extend(tokens)
                        did_split = True
                        continue
                out_list.append(item)
            if did_split:
                # De-dupe while preserving order
                seen = set()
                dedup = []
                for x in out_list:
                    if isinstance(x, str) and x not in seen:
                        seen.add(x)
                        dedup.append(x)
                return dedup, True
        return value, False

    for m in members:
        new_v, did = _split_ambig(m.get("mint"))
        if did:
            # Canonicalise each token after split so «København» and
            # «Kopenhagen» both fold to project-canonical «Kopenhagen».
            canonical = _canonicalise_mint(new_v)
            m["mint"] = canonical if canonical is not None else new_v
            m["mint_verified"] = False
    # Foundation-verified-override-cleanup: when a seed_unified member
    # explicitly publishes mint_verified=False AND its mint is multi-mint
    # list-form, the foundation's mint_verified=True is residue from
    # pre-ambiguity-split absorb runs. Force foundation to False so the
    # OR-merge below produces the correct unverified verdict. (OR-merge
    # alone cannot regress True → False; this explicit cleanup closes
    # that gap.)
    if len(members) >= 2 and members[0].get("mint_verified") is True:
        fc_mint = members[0].get("mint")
        if isinstance(fc_mint, list) and len(fc_mint) >= 2:
            for m in members[1:]:
                if (m.get("mint_verified") is False
                        and isinstance(m.get("mint"), list)
                        and set(m.get("mint", [])) == set(fc_mint)):
                    members[0]["mint_verified"] = False
                    break
    # mint UNION across members (D17 list-form when multi-mint)
    mint = _collect_mints(members)
    if mint is not None:
        out["mint"] = mint

    # Catalog: accumulate list-form on conflict (D18). Foundation entries
    # come first → their values take authority position in the list.
    cat, cat_conflicts = _deep_merge_catalog(members, entity_id)
    if cat:
        out["catalog"] = cat
    conflicts.extend(cat_conflicts)

    # Metal — verified-wins (CLAUDE.md §4): when foundation carries an
    # unverified builder-inferred metal (e.g. ucoin's billon-by-
    # Müntzfuß-default) and a composed_of member attests verified
    # copper/silver/gold, the verified value wins. Without this rule
    # foundation's wrong inference outranks a real source attestation.
    metal = _collect_metal(members)
    if metal:
        out["metal"] = metal

    # Verification flags: OR-merge (D20)
    for field in ("metal_verified", "fineness_verified", "weight_rough_verified",
                  "diameter_mm_verified", "mint_verified", "verified"):
        v = _or_merge_verified(members, field)
        if v is not None:
            out[field] = v

    # Multi-source measurement lists (D17 / §9a).
    # `skip_first_list=True` — the first member is the foundation (fc),
    # and its list-form values are absorb-cached from prior runs. The
    # cache may carry phantom readings from composed_of sources that
    # have since been split off (e.g. Galster ruler-scope split). Re-
    # derive from composed_of unified members only; foundation's scalar
    # (when present) still counts via the same call.
    #
    # Exception — bulk-promote path (`members = [unified_self]`,
    # `len(members) == 1`). Here `members[0]` IS the freshly-merged
    # unified entry, not a stale-cached foundation; its list-form
    # values came from the current seed/merger and should pass
    # through verbatim. Skipping them would silently drop every
    # per-source weight/fineness/diameter reading on every bulk-
    # promoted entry — observed cooccurrence with the catalog bug
    # (see comment above), same root cause.
    _skip_first = len(members) > 1
    fine = _collect_field_list(members, "fineness", skip_first_list=_skip_first)
    if fine:
        out["fineness"] = fine
    weights = _collect_field_list(members, "weight_rough_g", skip_first_list=_skip_first)
    if weights:
        out["weight_rough_g"] = weights
    diameters = _collect_field_list(members, "diameter_mm", skip_first_list=_skip_first)
    if diameters:
        out["diameter_mm"] = diameters

    # Honor `_curation_holds` for measurement fields, reconciling the two
    # rules that govern measurement merges:
    #   • §9a «preserve-all»: every distinct source reading of a list-form
    #     measurement (fineness / weight_rough_g / diameter_mm) is kept.
    #   • §4 «verified-wins»: a SOURCE-VERIFIED reading displaces an
    #     UNVERIFIED curator placeholder (which must NOT propagate).
    #
    # `skip_first_list=True` drops the foundation-self's readings on regen,
    # so a curator-set value that no source attests (e.g. the canonical
    # 23½-Karat .979 Nobel-fineness anchor) would otherwise vanish. Freezing
    # it via `_curation_holds: {fineness: "…"}` brings it back — but the way
    # it re-enters depends on what the sources now say:
    #
    #   (a) a source member attests the field VERIFIED while the hold is
    #       UNVERIFIED → §4: the source displaces the hold. `out[_hf]`
    #       (collected source readings) + the OR-merged `*_verified` flag
    #       already carry the source value; the held value is dropped.
    #   (b) otherwise (no verified source, OR the hold is itself verified)
    #       → §9a: UNION the held value with the collected source readings.
    #       A source's UNVERIFIED reading does NOT suppress the curator
    #       anchor and vice-versa — both survive as distinct list entries.
    for _hf, _vf in (("fineness", "fineness_verified"),
                     ("weight_rough_g", "weight_rough_verified"),
                     ("diameter_mm", "diameter_mm_verified")):
        if _hf not in holds_keys or final_entry.get(_hf) is None:
            continue
        held_verified = bool(final_entry.get(_vf))
        src_verified = (_or_merge_verified(members[1:], _vf)
                        if len(members) > 1 else None)
        if (not held_verified) and src_verified:
            # (a) §4 verified-wins: let the collected source readings +
            #     OR-merged verified flag stand; drop the unverified hold.
            continue
        # (b) §9a preserve-all: union held value(s) with source readings.
        held_val = final_entry[_hf]
        merged = list(held_val) if isinstance(held_val, list) else [held_val]
        collected = out.get(_hf)
        if isinstance(collected, list):
            def _k(e):
                return (e.get("value"), e.get("source")) if isinstance(e, dict) else (e, None)
            seen = {_k(e) for e in merged}
            for e in collected:
                if _k(e) not in seen:
                    merged.append(e)
                    seen.add(_k(e))
        out[_hf] = merged
        # `out[_vf]` already holds the OR-merge over all members (foundation
        # + sources), which is the correct «any verified ⇒ verified» status.

    # Catalog rebuild: same principle as measurements — drop foundation's
    # absorb-cached list-form catalog values for cross-source fields
    # before re-deriving. Foundation's SCALAR catalog entries are V1-
    # bootstrap and stay (DF1-immutable for some — see schema notes).
    # The merger's `_deep_merge_catalog` already runs above; we just
    # need to scrub fc's list-form for cross-source accumulation
    # fields before that. Done in-place on the `out` catalog after
    # merge by intersecting with members[1:]'s actual values.
    _CROSS_SOURCE_CATALOG_FIELDS = {
        "hede", "sieg", "schou", "galster", "galster_volume",
        "jensen_skjoldager", "schive", "skaare", "friedberg",
        "davenport", "lange", "fr", "dav", "nmd",
    }
    # Skip the cross-source intersect entirely for bulk-promote entries
    # (where the foundation IS the unified entry and `composed_members`
    # is empty). In that case there's no «prior absorb-cached list-form»
    # to clean up — the catalog values came directly from the current
    # seed and are trustworthy as-is. Running the intersect would
    # incorrectly drop every cross-source field because the composed-set
    # is empty by definition. Observed 2026-05-26 — Hans Galster entries
    # bulk-promoted in their first absorb run lost their entire
    # catalog dict (galster, schou, sieg, schive, galster_volume).
    if isinstance(out.get("catalog"), dict) and len(members) > 1:
        # Build the union of cross-source catalog values from composed_of
        # members (excluding fc which is members[0]).
        composed_members = members[1:]
        composed_values: dict[str, set[str]] = {}
        for k in _CROSS_SOURCE_CATALOG_FIELDS:
            for cm in composed_members:
                cat = cm.get("catalog") or {}
                v = cat.get(k)
                if v is None:
                    continue
                vals = v if isinstance(v, list) else [v]
                composed_values.setdefault(k, set()).update(
                    str(x).strip() for x in vals if x is not None)
        # For each cross-source catalog field in out, intersect with
        # composed_values — drop any value that no current member attests.
        for k in _CROSS_SOURCE_CATALOG_FIELDS:
            if k not in out["catalog"]:
                continue
            current = out["catalog"][k]
            current_list = current if isinstance(current, list) else [current]
            keep = composed_values.get(k, set())
            filtered = [v for v in current_list if str(v).strip() in keep]
            if not filtered:
                # No composed_of member attests this field → drop entirely
                del out["catalog"][k]
            elif len(filtered) == 1:
                out["catalog"][k] = filtered[0]
            else:
                out["catalog"][k] = filtered

    # §9.4 index hygiene on the assembled catalog: fold any `others:
    # <code># N` overflow into its typed list-field (case-insensitive
    # code) and de-dup list-form values case-insensitively («Hede 55C»
    # + «55c» → one «55C»). Runs whenever the entry has a catalog dict
    # (including the bulk-promote / single-member path skipped above).
    if isinstance(out.get("catalog"), dict):
        _fold_catalog_indices(out["catalog"])

    # Sources union — preserve curator-added entries on the foundation
    # alongside fresh seed-source citations, deduplicated by URL (single-
    # page hosts) or by (url, ref, type) (multi-record sources like the
    # Bruun PDF catalogues). The earlier `skip_first_list=True` dropped
    # the foundation's entire sources list to avoid phantom citations
    # from prior absorb runs — but it also dropped V1-curator-added
    # Numista / ucoin / auction refs that have no seed equivalent.
    # Phantom-citation persistence is a smaller issue than curator data
    # loss; dedup ensures legitimate duplicates collapse anyway.
    #
    # NB — a blanket `members[1:]` skip for `unified-*` foundations was
    # tried and reverted: even pure-absorbed-looking foundations (final
    # composed_of == [self]) can carry V1-curator sources merged in by a
    # prior absorb (e.g. a `km-*` V1 member's Bruun / Numista / Heritage
    # citations) that live ONLY on the foundation-self and are absent from
    # the seed_unified member's own sources list. Skipping the foundation-
    # self dropped 471 such legitimate citations across 224 entries.
    # True phantoms (a museum citation the merger has since re-homed to a
    # sibling entry — the f1g-68 / KMM 156725 case) are cleaned surgically
    # at the data layer instead.
    sources = _collect_sources(members)
    if sources:
        out["sources"] = sources
        # Hide (not delete) surplus weightless KMM specimen citations.
        _suppress_weightless_museum_overcollection(out)

    # Inscriptions — gap-fill (foundation primary)
    for field in ("inscription_obv", "inscription_rev", "weight_rough_label"):
        v = _take_first_non_none(members, field)
        if v is not None:
            out[field] = v

    # Note / verification_note — gap-fill from foundation
    for field in ("note", "verification_note"):
        v = _take_first_non_none(members, field)
        if v is not None:
            out[field] = v

    # Hede-attested Müntzfuß ratio — pass-through dict from whichever
    # member carries it (only Hede sources publish it; no conflict
    # resolution needed across multiple sources).
    yld = _take_first_non_none(members, "hede_muentzfuss_yield")
    if yld is not None:
        out["hede_muentzfuss_yield"] = yld

    # composed_of: union of final's existing + new members (deterministic
    # order). When a member has the SAME id as the final entry, it's the
    # «promoted unified entry» case — a final entry whose id is the
    # unified id (created by the bulk-promote path or absorbed via direct
    # match by self-id). In that case the SELF-REFERENCE is meaningful: it
    # marks the final as «this is the absorbed projection of the unified
    # cluster». Without self-reference, `already_absorbed` index on next
    # absorb run can't recognise this entry → it gets re-processed forever
    # and stays as an orphan (composed_of=[]).
    #
    # Heuristic: include self-id when the final-id matches a unified id
    # (starts with `unified-` AND the member with same id IS the unified
    # cluster representation of this final). Otherwise (foundation entry
    # with curator-set id that happens to also be a unified-id collision
    # — rare), exclude.
    existing_composed = list(final_entry.get("composed_of") or [])
    final_id = final_entry.get("id") or ""
    member_ids = []
    for m in members:
        mid = m.get("id")
        if not mid:
            continue
        if mid != final_id:
            member_ids.append(mid)
            continue
        # Self-reference: only meaningful if final-id is a unified-shape
        # id (the promoted-unified pattern). For other foundation entries
        # with a name-collision risk, stay safe and exclude.
        if final_id.startswith("unified-"):
            member_ids.append(mid)
    composed = sorted(set(existing_composed) | set(member_ids))
    out["composed_of"] = composed

    # Preserve other V2 bookkeeping fields from foundation
    for k in ("v1_home_location", "_migration_note", "_migration_dup_origin_id",
              "promoted_to", "_curation_holds", "_entity_routing_hint"):
        if k in final_entry:
            out[k] = final_entry[k]

    # When the foundation didn't already carry an `_entity_routing_hint`,
    # promote one from a composed_of member if any of them carries one.
    # The hint is metadata-class — last-writer-wins is acceptable;
    # foundation precedence handled above.
    if "_entity_routing_hint" not in out:
        for m in members:
            if isinstance(m, dict) and m.get("_entity_routing_hint"):
                out["_entity_routing_hint"] = m["_entity_routing_hint"]
                break

    return out, conflicts


# ---------------------------------------------------------------------------
# Per-entity processing
# ---------------------------------------------------------------------------


def _bulk_promote_mode(entity_id: str) -> str | None:
    """Curator-decision flag — returns the promote mode or None.

    Four accepted shapes of `bulk_promote_pending` in
    `data/v2/classification_decisions/<entity>.yml`:

      bulk_promote_pending: true                          → "all"  (D37)
      bulk_promote_pending: all                           → "all"
      bulk_promote_pending: no_basic_peer_only            → "no_basic_peer_only"  (D39)
      bulk_promote_pending: no_match_primary_disagrees    → "no_match_primary_disagrees"  (D40)
      (absent or false)                                   → None  (no auto-promote)

    Mode "all" (D37): promote EVERY unmatched unified entry. Use when
    the entity has no V1 foundation at all — no conflict is possible
    because there's nothing to conflict with.

    Mode "no_basic_peer_only" (D39): promote ONLY unified entries
    whose metal+nominal combination has NO peer in the existing
    foundation. The most conservative mode — keeps every «matcher-
    recoverable» case (D/E/H/C categories) in pending for review.

    Mode "no_match_primary_disagrees" (D40): superset of D39. Promotes
    a unified entry when EITHER (a) no basic peer exists OR (b) every
    basic peer's match_pair returned `decision: no_match` with an
    explicit primary-signal disagreement (`catalog: False` ≡ different
    KM/Hede/Sieg number → genuinely different sub-variant, OR `ruler:
    False` ≡ different reign attribution → genuinely different type).
    Keeps `low_confidence` cases (almost-match) AND `no_match` cases
    where only fallback signals disagreed (suspicious — primary is
    True/None for all peers) in pending for curator review.

    Promoting D + E cases is safe because the matcher's explicit
    primary disagreement is itself a confident signal of «different
    coin» — the same numismatic catalog logic that distinguishes KM-
    DK#92 from KM-DK#107 as separate 1625 16-Skilling sub-variants.
    """
    # Default mode = "no_basic_peer_only" (post-2026-05-20 D43).
    # V1 is frozen, V2 is the canonical pipeline going forward — new
    # coins flowing through harvest → seed → seed_unified MUST land in
    # V2 final automatically, otherwise they're invisible to the
    # rendered page. The old default (None = «stuck in pending») was a
    # bootstrap-era safety that doesn't apply to steady-state V2.
    # `no_basic_peer_only` is the safe choice: promotes only when NO
    # existing peer at all (no metal+nominal collision) — the
    # «genuinely new coin» case. Cases where the matcher found peers
    # but couldn't decide (D/E/H/C ambiguities) still land in pending
    # for curator review.
    DEFAULT_MODE = "no_basic_peer_only"
    path = V2_CLASSIFICATION_DECISIONS / f"{entity_id}.yml"
    if not path.exists():
        return DEFAULT_MODE
    doc = _load_yaml(path)
    val = doc.get("bulk_promote_pending")
    if val is True or val == "all":
        return "all"
    if val == "no_basic_peer_only":
        return "no_basic_peer_only"
    if val == "no_match_primary_disagrees":
        return "no_match_primary_disagrees"
    # Explicit `false` / `none` keeps None (curator opts out); absence
    # falls through to the new default.
    if val in (False, "false", "none"):
        return None
    return DEFAULT_MODE


def _has_basic_peer(unified: dict, finals: list[dict], entity_id: str | None,
                    reign_index: dict | None = None) -> bool:
    """Return True if any final entry shares the unified's
    metal AND nominal (the strict «basic peer» check per
    `_compute_coin`'s match-pair primary signals). Used by
    bulk_promote mode «no_basic_peer_only» to safely promote
    only the «genuinely new type» subset of pending entries.

    `reign_index` (D33 / D41) is forwarded to `match_pair` so that
    coins with `ruler: None` get year→reign inference applied
    consistently with the merger's pre-pass behaviour.
    """
    for f in finals:
        result = match_pair(unified, f, entity_id, reign_index=reign_index)
        pri = result.get("primary") or {}
        if pri.get("metal") is True and pri.get("nominal") is True:
            return True
    return False


def _all_basic_peers_no_match_primary(unified: dict, finals: list[dict],
                                       entity_id: str | None,
                                       reign_index: dict | None = None) -> bool | None:
    """Return True if EVERY basic-peer (metal+nominal match) returns
    `decision: no_match` AND at least one peer's no_match was caused
    by an EXPLICIT primary-signal disagreement (`catalog: False` or
    `ruler: False`). Returns False if any peer returned `confident`
    or `low_confidence`, OR if every peer's no_match was caused by
    fallback-only disagreement (H-category — primary all True/None
    but secondary signals diverged).

    Returns None when there are no basic peers at all — the caller
    falls back to the `no_basic_peer_only` check.

    Used by bulk_promote mode «no_match_primary_disagrees» (D40) to
    safely promote D + E category pending entries (different sub-
    variant by explicit catalog/ruler signal) while keeping H + C
    category entries in pending for curator review.

    `reign_index` (D33 / D41) is forwarded to `match_pair`.
    """
    saw_basic_peer = False
    saw_primary_disagreement = False
    for f in finals:
        result = match_pair(unified, f, entity_id, reign_index=reign_index)
        pri = result.get("primary") or {}
        # Skip non-basic-peers (metal/nominal not both True)
        if not (pri.get("metal") is True and pri.get("nominal") is True):
            continue
        saw_basic_peer = True
        decision = result.get("decision")
        if decision != "no_match":
            # confident OR low_confidence — NOT safe to promote
            return False
        # decision == "no_match" — check primary disagreement
        if pri.get("catalog") is False or pri.get("ruler") is False:
            saw_primary_disagreement = True
    if not saw_basic_peer:
        return None  # caller falls back to no_basic_peer_only
    # All basic peers said no_match. Safe iff at least one had primary
    # disagreement (D/E category). Pure fallback-only disagreement
    # (H category) is NOT promotable — keep pending for review.
    return saw_primary_disagreement


# Module-level cache for `fuesse.yml::<fuss>.fractions` keys. Built once
# on first call to process_entity, reused across every entity. Reading
# fuesse.yml on every fraction-inference invocation would be wasteful.
_FUSS_FRACTIONS_CACHE: dict[str, set] | None = None

# Re-validate composed_of membership each run (evict identity-mismatched
# members per `_revalidate_composed_of`). Default on; `--no-revalidate`
# disables for a one-off debug run that must not mutate existing membership.
REVALIDATE_ENABLED: bool = True


def _get_fuss_fractions_cache() -> dict[str, set]:
    global _FUSS_FRACTIONS_CACHE
    if _FUSS_FRACTIONS_CACHE is None:
        _FUSS_FRACTIONS_CACHE = load_fuss_fractions()
    return _FUSS_FRACTIONS_CACHE


def _nominal_genuinely_differs(a, b) -> bool:
    """True iff two nominals are a GENUINE identity mismatch.

    Mirrors the merger's nominal discriminator (merge_seeds_cross_source,
    shipped 2026-06-08): normalise both via `_normalise_nominal`, treat
    them as the same coin when equal OR when the bare-unit / same-unit-
    compound wildcard (`_nominal_wildcard_match`) holds. Anything else is
    a genuine difference («8 Skilling» vs «1 Denning», «2 Guldkrone» vs
    «2 Dukat»). Empty / unparseable nominals are NOT a genuine difference
    (can't assert a mismatch from missing data).
    """
    na, nb = _mg_normalise_nominal(a), _mg_normalise_nominal(b)
    if not na or not nb or na == nb:
        return False
    if _nominal_wildcard_match(na, nb):
        return False
    return True


def _revalidate_composed_of(
    final_by_id: dict, unified_by_id: dict, entity_id: str
) -> dict[str, set]:
    """Re-validate existing composed_of membership; return per-host evict set.

    The ABSORB stage is additive + STICKY: once a unified entry lands in a
    foundation's `composed_of`, no later run re-checks whether it still
    belongs. Earlier-pipeline mis-groupings (and V1-bootstrap composed_of
    carried forward) therefore persist forever — e.g. the «1 Denning»
    (unified-kmk-137199) + «4 Skilling lybsk» (unified-kmk-294714) members
    fused into the KM 42 «8 Skilling» foundation, dragging a 0.44 g weight
    onto an 8-Skilling row (caught 2026-06-08).

    SAFE criterion — IDENTITY mismatch only, never specimen variance:
    a member is evicted iff its normalised nominal GENUINELY differs from
    the foundation's (`_nominal_genuinely_differs`) AND the two share NO
    agreeing type-level catalogue (`_shares_type_level_catalog` — km / hede
    / galster / dav / lange / numista / bruun_collection_id, NOT weak per-
    reign Schou/Sieg). This is exactly the merger's nominal discriminator,
    applied to existing membership. The weight-tier-1 disambiguator is
    DELIBERATELY NOT used here: a same-nominal member whose weight diverges
    >5 % is legitimate specimen variance (a worn / off-standard piece),
    not a different coin — re-validating on weight would false-drop real
    specimens (verified 2026-06-08: 24 of 38 weight-tier drops were
    same-nominal). Once a member is evicted it re-enters the unabsorbed
    pool and re-homes via the standard force-promote path; the shipped
    nominal discriminator then prevents it re-absorbing into the same
    foundation (no type-level tie → match_pair no_match).

    Returns `{host_id: {evict_member_id, ...}}` for every foundation with
    at least one identity-mismatched member.
    """
    evictions: dict[str, set] = {}
    for fid, fc in final_by_id.items():
        comp = fc.get("composed_of") or []
        if len(comp) < 2:
            continue
        fa = _catalog_refs(fc, entity_id)
        host_nom = fc.get("nominal")
        for mid in comp:
            if mid == fid:
                continue  # self-link foundation contribution — never evict
            m = unified_by_id.get(mid)
            if m is None:
                continue  # raw-seed / unknown member — not a unified entry
            # Forgery-asymmetry: a contemporary forgery / imitation is never
            # the same object as the genuine coin it copies, even sharing its
            # catalogue (it's catalogued BY what it imitates). Evict REGARDLESS
            # of a type-level tie — the shared Hede/KM is exactly why it stuck
            # (caught 2026-06-09: «1 Skilling samtidig forfalskning» bouncing
            # between genuine Hede 119B hosts).
            if _is_forgery_nominal(host_nom) != _is_forgery_nominal(m.get("nominal")):
                evictions.setdefault(fid, set()).add(mid)
                continue
            if not _nominal_genuinely_differs(host_nom, m.get("nominal")):
                continue
            if _shares_type_level_catalog(fa, _catalog_refs(m, entity_id)):
                continue  # type-level catalogue tie overrides nominal diff
            evictions.setdefault(fid, set()).add(mid)
    return evictions


def _wkey(v):
    """Round-to-5 numeric key for weight/fineness/diameter value matching."""
    try:
        return round(float(v), 5)
    except (TypeError, ValueError):
        return None


def _surgical_decontaminate(
    fc: dict, evicted_members: list[dict], remaining_members: list[dict]
) -> None:
    """Strip ONLY the evicted members' EXCLUSIVE accumulated contributions.

    Prior enrichment runs bake every member's measurements + sources onto
    the foundation entry itself (members[0] == fc in `_enrich_final_entry`),
    so dropping a member from composed_of is not enough — its 0.44 g weight,
    its source URLs etc. survive on fc and re-pollute the next re-enrichment.

    Twin-INDEPENDENT removal (no clean-foundation snapshot needed): for each
    list-form measurement field (weight_rough_g / fineness / diameter_mm) and
    for `sources`, drop a value from fc iff it is contributed by SOME evicted
    member AND by NO remaining member. Values that no evicted member carries
    (genuine foundation-own data, or orphan baked data with no current backer
    — e.g. km-74's 4 Bruun/KMM source URLs) are PRESERVED untouched, honouring
    §9a «preserve all data, never collapse». Mutates `fc` in place.

    Year fields are intentionally left alone: an over-wide year range is the
    safe direction per §0 («year_last overshooting acceptable, never clip»),
    and re-enrichment unions years from the surviving member set anyway.
    """
    def _val_source_keys(members, field):
        keys = set()
        for m in members:
            v = m.get(field)
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, dict) and _wkey(x.get("value")) is not None:
                        keys.add((_wkey(x["value"]), x.get("source")))
        return keys

    def _source_keys(members):
        keys = set()
        for m in members:
            for s in (m.get("sources") or []):
                if isinstance(s, dict):
                    keys.add((s.get("url"), s.get("ref"), s.get("type")))
        return keys

    for field in ("weight_rough_g", "fineness", "diameter_mm"):
        cur = fc.get(field)
        if not isinstance(cur, list):
            continue  # scalar (curator / canonical Müntzfuß value) — leave it
        ev_keys = _val_source_keys(evicted_members, field)
        if not ev_keys:
            continue
        keep_keys = _val_source_keys(remaining_members, field)
        kept = [
            x for x in cur
            if not (
                isinstance(x, dict)
                and (_wkey(x.get("value")), x.get("source")) in ev_keys
                and (_wkey(x.get("value")), x.get("source")) not in keep_keys
            )
        ]
        if kept:
            fc[field] = kept
        else:
            fc.pop(field, None)

    cur_sources = fc.get("sources")
    if isinstance(cur_sources, list):
        ev_src = _source_keys(evicted_members)
        if ev_src:
            keep_src = _source_keys(remaining_members)
            kept = [
                s for s in cur_sources
                if not (
                    isinstance(s, dict)
                    and (s.get("url"), s.get("ref"), s.get("type")) in ev_src
                    and (s.get("url"), s.get("ref"), s.get("type")) not in keep_src
                )
            ]
            if kept:
                fc["sources"] = kept
            else:
                fc.pop("sources", None)


# ---------------------------------------------------------------------------
# Stale-final detection (2026-06-10) — module-level so it is unit-testable.
# See the STALE-FINAL DROP block in process_entity() for the full rationale.
# ---------------------------------------------------------------------------

# Seed-source phase tags. A bare phase like "kmk"/"bruun" on a final is the
# SEED's source tag, not a curator decision — so it does NOT count as curation.
_SEED_TAG_PHASES = frozenset({
    "bruun", "hede", "kmk", "galster", "ikmk",
    "numista", "numismaster", "ucoin", "seed_unsorted",
})


def _final_is_curated(fe: dict) -> bool:
    """True if a final entry carries a curator decision that must survive an
    automated drop: a real Müntzfuß (`fuss` not seed_unsorted/None), a `note`,
    `_curation_holds`, `promoted_to`, or a curator-assigned `phase` (a bare
    seed-source phase tag is NOT curation)."""
    if fe.get("fuss") not in (None, "seed_unsorted"):
        return True
    if fe.get("note") or fe.get("_curation_holds") or fe.get("promoted_to"):
        return True
    ph = fe.get("phase")
    if ph and ph not in _SEED_TAG_PHASES:
        return True
    return False


def _final_has_live_backing(fe: dict, live_unified_ids: set, live_ids: set) -> bool:
    """True if the final's own id is a current seed_unified head OR any of its
    composed_of members resolves to a current seed_unified head / seed id."""
    if fe.get("id") in live_unified_ids:
        return True
    return any(c in live_ids for c in (fe.get("composed_of") or []))


def _is_vanished_stale_final(fe: dict, live_unified_ids: set, live_ids: set) -> bool:
    """A PIPELINE-PROMOTED (`unified-*`) final whose backing seed_unified entry
    has vanished and which carries no curation — safe to drop.

    The `unified-*` id gate is the primary guard: a V1-bootstrap foundation
    (real id, e.g. `dk-tid-…`) is the coin's OWN data, never seed-derived, so it
    is never dropped here regardless of backing. The curation guard is the
    second line of defence (keeps a bulk-promoted entry a curator has since
    classified)."""
    return (
        str(fe.get("id") or "").startswith("unified-")
        and not _final_has_live_backing(fe, live_unified_ids, live_ids)
        and not _final_is_curated(fe)
    )


def process_entity(entity_id: str) -> dict:
    """Returns:
      {
        'entity_id': str,
        'unified_total': int,
        'final_total_before': int,
        'final_total_after': int,
        'already_absorbed': int,
        'newly_absorbed': int,
        'genuinely_new': int,
        'bulk_promoted': int,           # entries auto-promoted to final under D37
        'unmatched_unified_ids': [...],
        'multi_match_warnings': [{unified_id, candidates}, ...],
        'enrichment_conflicts': [{final_id, members, conflicts}, ...],
        'enriched_final_entries': [...] (dicts ready to write),
      }
    """
    unified_doc = _load_yaml(V2_SEED_UNIFIED / f"{entity_id}.yml")
    unified_entries: list[dict] = unified_doc.get("coins") or []
    unified_by_id = {u["id"]: u for u in unified_entries if u.get("id")}

    final_path = V2_FINAL / f"{entity_id}.yml"
    final_doc = _load_yaml(final_path)
    final_entries: list[dict] = final_doc.get("coins") or []

    # Monotonic-absorb snapshot: the coins currently in `final` (references —
    # in-place normalisation below mutates these same dicts). A post-pass
    # before return re-promotes any of these that a re-run DROPS for a
    # NON-legitimate reason (stale-foundation-purge regroup churn / D40
    # bulk-promote peer-check shift when a new source like IKMK is merged
    # in) — so adding a new source can never silently DE-PROMOTE a coin
    # that was already on the page. It re-adds the prior entry VERBATIM
    # (never a new merge — that stays the merger's job, surfaced for curator
    # review). Legitimate drops (out-of-scope, article-page, genuinely
    # consolidated-into-a-peer) are excluded in the post-pass. See TODO §CH.
    _prior_final_for_monotonic: list[dict] = [
        fc for fc in final_entries if isinstance(fc, dict) and fc.get("id")
    ]

    # Out-of-scope purge: when the pre-write hygiene filter rules are
    # tightened (broader Piaster filter, etc.) entries previously absorbed
    # into final survive because absorb iterates `final_by_id` from the
    # existing file. Drop them here before they re-enter the enrichment
    # cycle — keeps final in sync with the current scope policy.
    # Apply nominal + mint normalisation in-place too — the V1-foundation
    # entries were seeded with raw values; data quality rules
    # (U.År strip, bare-noun prefix, mojibake fix, canonical mint
    # spelling) apply retroactively across the whole pipeline.
    out_of_scope_final_dropped = 0
    kept_finals: list[dict] = []
    for fe in final_entries:
        if isinstance(fe, dict) and (
            _is_out_of_scope_nominal(fe.get("nominal"))
            or _is_out_of_scope_catalog(fe.get("catalog"))
            or _is_out_of_scope_year(fe.get("year_first"))
        ):
            out_of_scope_final_dropped += 1
            continue
        if isinstance(fe, dict):
            raw_nom = fe.get("nominal")
            # Placeholder-nominal adoption: when foundation carries a
            # literal «(?)» (or empty) nominal AND the matching unified
            # entry now publishes a real nominal (e.g. after a builder
            # fix supplied title-derived value), adopt that nominal.
            # Foundation-immutable per DF1 normally — but a placeholder
            # is by definition unset; replacing it isn't a curator
            # override, it's a gap-fill.
            # Same rule extended: foundation nominal with the
            # «X og Y» Danish-conjunction pattern is an obsolete
            # multi-coin merged form from before the Hede multi-Hede
            # parser fix. The unified entry now publishes the clean
            # single-coin nominal — adopt it. Concrete case:
            # `unified-dk-hede-nf3h39` foundation had «1 Og 2
            # Speciedaler» (merged Hede 39 + Hede 40); fresh Hede
            # parser splits into `nf3h39` (1 Speciedaler) +
            # `nf3h40` (2 Speciedaler) — foundation adopts the
            # clean Hede 39's «1 Speciedaler».
            fid = fe.get("id")
            needs_adoption = False
            if raw_nom in ("(?)", "", None):
                needs_adoption = True
            elif isinstance(raw_nom, str) and re.search(
                    r"\b[Oo]g\b", raw_nom):
                needs_adoption = True
            if (needs_adoption
                    and fid and fid in unified_by_id):
                ue = unified_by_id[fid]
                ue_nom = ue.get("nominal")
                if ue_nom and ue_nom not in ("(?)", "") and ue_nom != raw_nom:
                    fe["nominal"] = ue_nom
                    raw_nom = ue_nom
            # Mint-from-nominal extraction first (so the string-level
            # normaliser sees the clean nominal).
            nom_after_mint, mint_after_split = _extract_mint_from_nominal(
                raw_nom, fe.get("mint"))
            if nom_after_mint != raw_nom:
                fe["nominal"] = nom_after_mint
                raw_nom = nom_after_mint
            if mint_after_split != fe.get("mint"):
                fe["mint"] = mint_after_split
            new_nom = _normalise_nominal(raw_nom)
            if new_nom is not None and new_nom != raw_nom:
                fe["nominal"] = new_nom
            raw_mint = fe.get("mint")
            new_mint = _canonicalise_mint(raw_mint)
            if (new_mint != raw_mint
                    and not (new_mint is None and raw_mint in (None, ""))):
                fe["mint"] = new_mint
            cat = fe.get("catalog")
            if isinstance(cat, dict):
                _normalise_catalog(cat)
            # fineness-implies-metal rule (parallel to seed-writer hygiene)
            if (fe.get("metal")
                    and bool(fe.get("fineness_verified"))
                    and not bool(fe.get("metal_verified"))):
                fe["metal_verified"] = True
            # sources-imply-mint rule
            sources_fe = fe.get("sources") or []
            if (fe.get("mint")
                    and isinstance(sources_fe, list)
                    and any(isinstance(s, dict) and s.get("url") for s in sources_fe)
                    and not bool(fe.get("mint_verified"))):
                fe["mint_verified"] = True
        kept_finals.append(fe)
    final_entries = kept_finals

    # Stale-foundation purge: when a V1-bootstrap foundation entry has
    # been merged AWAY by the cross-source merger (its source seed id
    # now belongs to a different unified entry's composed_of), the
    # foundation copy is a stale duplicate. Three shapes:
    #   A. `unified-X` foundation where the cross-source merger has
    #      consolidated `X` into a different unified entry.
    #   B. `X` foundation (V1-direct bootstrap, e.g. `dk-tid-70722`)
    #      where `X` now appears as a source-seed in some unified's
    #      composed_of, but `X` itself is not a unified entry id.
    #   C. Article-page foundations (`*-ernst_*`, `*-artikler_*` —
    #      danskmoent.dk narrative articles ABOUT coins, not coin-
    #      catalog pages themselves). The cache parser correctly
    #      marks these `skip: true`; historical V2 final foundations
    #      from before the skip rule landed persist as phantoms. The
    #      coins these articles describe are already covered by the
    #      canonical Galster pages (f1g-71 Ribe / f1g-74 Ålborg cover
    #      ernst_14p1524's two coins; f1g-50 covers ernst_f1g50ern).
    # All three shapes need purging — the consolidated unified entry's
    # final wrapper subsumes the original V1-foundation data via its
    # composed_of seed-id membership; leaving the orphan foundation
    # results in DUPLICATE coin rows (caught 2026-05-20 audit on
    # KM# 688 / 696 / Tn6 — V1 ucoin foundation + NumisMaster unified
    # appearing as two rows in seed_unsorted).
    stale_foundation_dropped = 0
    article_page_dropped = 0
    # Build: source seed id → its current unified host
    seed_to_unified: dict[str, str] = {}
    for uid, ue in unified_by_id.items():
        for sid in ue.get("composed_of") or []:
            seed_to_unified[sid] = uid
    # When a stale foundation is purged because the merger has consolidated
    # its source seed id into a different unified host, the V1-bootstrap
    # foundation's curator-attested classification (fuss / phase / kind /
    # ruler-spelling / mintmaster, etc.) must MIGRATE to the new host —
    # otherwise the absorb's bulk-promote path would emit the new unified
    # entry with the source's raw `fuss: seed_unsorted` default, silently
    # losing months of curator work.
    #
    # Build a migration table `{new_host_fid: classification_dict}` so the
    # later bulk-promote step can look it up and apply the curator override
    # to the freshly-promoted final entry. Observed 2026-05-26: relocation
    # of Bruun `dk-bruun-5631` from `danish_realm` to `royal_holstein`
    # caused the merger to compose 3 sources (Bruun + V1 `km-29-chr-iv-1640`
    # + NumisMaster) into a new unified id `unified-dk-bruun-5631`. The
    # stale-foundation purge then dropped the V1 entry, taking with it
    # the `fuss: reichsdukatenfuss, phase: I` classification — the merged
    # entry rendered into the seed_unsorted bucket instead of Reichsdukatenfuß.
    curator_migrations: dict[str, dict] = {}

    # Fields migrated from a dropped V1-bootstrap foundation onto its
    # new unified host. Superset of `_FOUNDATION_IMMUTABLE_FIELDS` plus
    # curator-prose fields that hold V1's hand-written description text
    # (Stempelschneider initials, mint-master attribution, Reichsdukatenfuß
    # standard recap — content that's not derivable from any source seed
    # and would otherwise vanish into the void).
    _MIGRATION_PRESERVED_FIELDS = _FOUNDATION_IMMUTABLE_FIELDS | {
        "note",
        # Curator-set year metadata is irreplaceable: V1 entry «1791-1792,
        # 1794, 1802» (4 discrete years) is more accurate than the
        # merger's «1791-1802» wide-span derived from year_first/year_last
        # of the source seeds. Per CLAUDE.md «Source years are immutable
        # — never truncate to fit our taxonomy». Caught 2026-05-27 on
        # KM-650 Christian VII Species-Dukat.
        "year_first", "year_last", "year_ranges", "year_label",
        # Curator-set diameter (V1 scalar, manually verified against
        # specimen catalogues) is dropped by the merger when no cache
        # source provides diameter — preserve it as a fallback.
        "diameter_mm", "diameter_mm_verified",
        # Verification flags travel with the curator's intent.
        "weight_rough_verified", "fineness_verified", "metal_verified",
        "mint_verified",
    }
    # Fields that MERGE rather than replace. `sources` from V1
    # foundations carry curator-handpicked URLs (NGC price guides,
    # Smithsonian collection links, museum pages, Wikipedia analyses)
    # that NO source seed produces. The merger's unified entry has
    # cache-derived sources (Bruun PDFs, ucoin tids, NumisMaster); we
    # want BOTH sets on the final entry, deduplicated by URL.
    _MIGRATION_MERGE_FIELDS = frozenset({"sources"})

    def _migrate_classification(fe: dict, new_host_fid: str) -> None:
        """Snapshot curator-set fields for migration to new host.

        Includes foundation-immutable (fuss/phase/kind/etc.) AND
        curator-prose `note` field — the V1 entry's hand-written
        description that captures mint-master initials, engraver names,
        and other context not encoded in any source seed's structured
        fields. ALSO year-metadata fields when the V1 curator set
        discrete years that merger's range-derivation would lose.
        """
        snapshot = {
            field: fe[field]
            for field in _MIGRATION_PRESERVED_FIELDS
            if field in fe and fe[field] not in (None, "", [], {})
        }
        # Merge-fields: collect curator-added entries (sources list)
        # under a separate key so the bulk-promote applier knows to
        # MERGE not REPLACE.
        merge_snapshot = {}
        for field in _MIGRATION_MERGE_FIELDS:
            v = fe.get(field)
            if v not in (None, "", [], {}):
                merge_snapshot[field] = v
        if not snapshot and not merge_snapshot:
            return
        existing = curator_migrations.get(new_host_fid) or {}
        existing.update(snapshot)
        # Accumulate merge-field entries across multiple stale-foundations
        # pointing at the same new host.
        for k, vlist in merge_snapshot.items():
            mkey = f"__merge__{k}"
            ex_merge = existing.get(mkey) or []
            if isinstance(vlist, list):
                ex_merge.extend(vlist)
            else:
                ex_merge.append(vlist)
            existing[mkey] = ex_merge
        curator_migrations[new_host_fid] = existing

    surviving_finals: list[dict] = []
    for fe in final_entries:
        fid = fe.get("id") if isinstance(fe, dict) else None
        if not fid:
            surviving_finals.append(fe)
            continue
        composed = fe.get("composed_of") or []
        # «Effectively empty» composed_of: either truly empty OR a
        # self-link (foundation points only to itself, which is a
        # V1-bootstrap artefact, not a real cross-source composition).
        composed_real = [c for c in composed if c != fid]
        # Shape C: article-page foundation. Check sources[] for known
        # article-page URL paths (danskmoent.dk /ernst/ / /artikler/).
        # The cache parser marks these `skip: true`; the canonical
        # Galster catalog pages cover their coins. Pure narrative
        # foundations have empty composed_of (no source seed entry)
        # or a self-link only.
        if not composed_real:
            srcs = fe.get("sources") or []
            is_article = False
            for s in srcs:
                if not isinstance(s, dict):
                    continue
                url = str(s.get("url") or "")
                if "/ernst/" in url or "/artikler/" in url:
                    is_article = True
                    break
            if is_article:
                article_page_dropped += 1
                continue
        # Shape A: `unified-X` foundation
        if (fid.startswith("unified-")
                and fid not in unified_by_id):
            source_id = fid[len("unified-"):]
            new_host = seed_to_unified.get(source_id)
            if new_host and new_host != fid:
                _migrate_classification(fe, new_host)
                stale_foundation_dropped += 1
                continue
            # Shape D: orphan unified-X foundation where X is gone from
            # EVERY unified entry's composed_of (no `new_host` lookup
            # hit). The source seed id was removed from seed entirely
            # (e.g. phantom-cleanup after the parser learned to skip
            # the page that originally produced it). The final entry
            # is now a true orphan with no live data feed and would
            # otherwise persist indefinitely. Only fire when the
            # foundation is a bulk-promoted self-link (composed_of
            # == [fid]) — a curator-composed unified entry with N>=2
            # different composed_of members is a different shape that
            # needs explicit curator decision before dropping.
            if (new_host is None
                    and source_id not in seed_to_unified
                    and composed == [fid]):
                stale_foundation_dropped += 1
                continue
        # Shape B: V1-direct bootstrap foundation whose id is now a
        # source-seed in some unified's composed_of. Detection requires
        # both: (a) fid is composed BY a unified, (b) fid itself is not
        # a unified entry id, (c) foundation has empty composed_of (not
        # the host of any seed itself — pure leaf foundation).
        elif (fid in seed_to_unified
                and fid not in unified_by_id
                and not composed):
            new_host = seed_to_unified[fid]
            if new_host != fid:
                _migrate_classification(fe, new_host)
                stale_foundation_dropped += 1
                continue
        surviving_finals.append(fe)
    if stale_foundation_dropped:
        print(f"  [{entity_id}] stale-foundation purge: "
              f"{stale_foundation_dropped} entries dropped (merged into peers)")
    if article_page_dropped:
        print(f"  [{entity_id}] article-page purge: "
              f"{article_page_dropped} entries dropped (narrative articles)")

    # Shape E: self-foundation reconciliation. When a unified entry was
    # bulk-promoted as `composed_of: [self]` in a previous run AND a
    # V1-bootstrap foundation peer now `confident`-matches it (4/4
    # primary signals), the self-foundation is a duplicate. Drop it from
    # final; the iteration loop below will pick up the unified entry
    # from seed_unified/ and absorb it into the V1-foundation peer's
    # composed_of via the standard match_pair path. Caught 2026-05-26
    # on KM-94 1642 1 Ducat: V1-bootstrap `km-94-fr-iii-1642` (carrying
    # mintmaster HG + Bruun catalog refs + curator note prose) and
    # self-promoted `unified-schleswig_holstein-numismaster-99481`
    # (carrying NumisMaster fineness+weight) sat side-by-side as two
    # separate rows even though match_pair returned confident for the
    # pair.
    #
    # Trigger conditions (ALL must hold):
    #   - fid.startswith("unified-")
    #   - fid in unified_by_id (the underlying unified still exists)
    #   - composed_of == [fid] (pure self-link, not a curator-composed
    #     entry with multiple members)
    #   - exactly ONE non-`unified-`-prefixed peer in `surviving_finals`
    #     returns `decision: confident` from match_pair
    #   - classification fields (fuss/phase/kind/issuing_entity) either
    #     agree exactly OR the self-foundation carries the default
    #     `seed_unsorted` fuss (i.e. no curator decision has fired yet
    #     on the self-foundation, so V1's classification is authoritative)
    #
    # Strict 1-peer requirement: if multiple V1 peers match confidently,
    # fold direction is ambiguous and needs curator review. If zero V1
    # peers match, the self-foundation stays as its only home.
    #
    # Classification-disagreement guard: when both sides carry curator-
    # set fuss/phase/kind that DIFFER, don't silently lose either —
    # surface as a skip and let the curator resolve.
    v1_foundations_for_fold = [
        fe for fe in surviving_finals
        if isinstance(fe, dict) and fe.get("id")
        and not fe["id"].startswith("unified-")
    ]
    _CLASSIFICATION_FIELDS = ("fuss", "phase", "kind", "issuing_entity")

    def _classifications_compatible(self_fe: dict, v1_fe: dict) -> bool:
        """Self-foundation may fold into V1-foundation iff classifications
        agree exactly OR self has the default `seed_unsorted` fuss.
        Returns False if there's a curator-set disagreement on any field."""
        sf_fuss = self_fe.get("fuss")
        if sf_fuss in (None, "seed_unsorted"):
            # No curator decision on self yet → V1 is authoritative.
            return True
        for field in _CLASSIFICATION_FIELDS:
            sv = self_fe.get(field)
            vv = v1_fe.get(field)
            if sv in (None, "", "seed_unsorted"):
                continue
            if vv in (None, "", "seed_unsorted"):
                continue
            if sv != vv:
                return False
        return True

    self_foundation_folded = 0
    self_foundation_fold_skipped_multi: list[str] = []
    self_foundation_fold_skipped_clash: list[str] = []
    final_after_fold: list[dict] = []
    for fe in surviving_finals:
        if not isinstance(fe, dict):
            final_after_fold.append(fe)
            continue
        fid = fe.get("id")
        composed = fe.get("composed_of") or []
        if not (fid and fid.startswith("unified-")
                and fid in unified_by_id
                and composed == [fid]):
            final_after_fold.append(fe)
            continue
        # Self-foundation candidate. Find V1-peer matches via match_pair.
        matches = []
        for vf in v1_foundations_for_fold:
            result = match_pair(fe, vf, entity_id)
            if result.get("decision") == "confident":
                matches.append(vf)
        if len(matches) == 1:
            if _classifications_compatible(fe, matches[0]):
                # Safe to fold. Drop self-foundation; loop below will
                # absorb the unified into V1 via the normal match_pair path.
                self_foundation_folded += 1
                continue
            # Classification disagreement — needs curator review.
            self_foundation_fold_skipped_clash.append(fid)
        elif len(matches) > 1:
            self_foundation_fold_skipped_multi.append(fid)
        final_after_fold.append(fe)
    if self_foundation_folded:
        print(f"  [{entity_id}] self-foundation fold: "
              f"{self_foundation_folded} entries dropped "
              f"(re-absorb into V1 peers via match_pair)")
    if self_foundation_fold_skipped_multi:
        print(f"  [{entity_id}] self-foundation fold: "
              f"skipped {len(self_foundation_fold_skipped_multi)} "
              f"(multiple V1 peers match): "
              f"{self_foundation_fold_skipped_multi[:3]}")
    if self_foundation_fold_skipped_clash:
        print(f"  [{entity_id}] self-foundation fold: "
              f"skipped {len(self_foundation_fold_skipped_clash)} "
              f"(curator classification clash): "
              f"{self_foundation_fold_skipped_clash[:3]}")
    surviving_finals = final_after_fold

    final_entries = surviving_finals
    final_by_id = {f["id"]: f for f in final_entries if f.get("id")}

    bulk_promote_mode = _bulk_promote_mode(entity_id)

    # D41 — reign-index ruler inference, extended from Phase 3.2 to
    # Phase 4 absorb. The merger pre-pass (`merge_seeds_cross_source.py`)
    # builds a `{year → set(rulers)}` index from members that DO carry
    # an attested ruler and uses it to infer ruler on null-ruler coins
    # via singleton-year lookup (D33). Until D41 the absorb script did
    # NOT forward that index into its `match_pair` calls, so the H-case
    # pending entries that the merger's pre-pass had inferred ruler on
    # were still treated as ruler=None in absorb's match — losing the
    # inference at the Phase 3.2 → Phase 4 boundary. Building the index
    # here from BOTH unified + foundation entries (both carry attested
    # rulers) and forwarding to every match_pair / _has_basic_peer /
    # _all_basic_peers_no_match_primary call restores the inference.
    reign_index = _build_reign_index(
        list(unified_entries) + list(final_entries), entity_id
    )

    # PURGE stale composed_of entries — when the cross-source merger
    # consolidates two previously-separate unified entries into one
    # (e.g. unified-denmark-numismaster-65046 + unified-dk-hede-c4h134
    # → unified-dk-hede-c4h134 after D33 ruler-inference unlocks the
    # merge), the old unified id no longer exists in seed_unified.
    # Without this purge those stale ids linger in final.composed_of
    # and trip audit_v2 I2 «composed_of references unknown id». The
    # replacement unified id gets added by the normal match-pair pass
    # below, so we don't lose information — just drop dangling refs.
    purged_count = 0
    for fid, fc in final_by_id.items():
        original_composed = fc.get("composed_of") or []
        kept = [cid for cid in original_composed if cid in unified_by_id]
        if len(kept) != len(original_composed):
            fc["composed_of"] = kept
            purged_count += len(original_composed) - len(kept)

    # PURGE over-merge composed_of members (CLAUDE.md §9.4 base-KM split).
    # Older pipeline code fused entries of DIFFERENT base KM into one final
    # (e.g. dk-tid-97364 km=248 absorbing unified-dk-hede-f3h61 km=240 +
    # f3h82 km=169 → three Krause types in one row). The current matcher
    # returns no_match on these, but the additive absorb never re-validated
    # existing composed_of, so the stale fusion persisted across runs. The
    # curator-reviewed SAFE allowlist (data/v2/overmerge_purge_allowlist.yml)
    # lists, per host, the members to evict: each carries a different base KM
    # than the host AND self-attributes (own KM, no orphan no-KM member
    # entangled, no two evicted members sharing a KM).
    #
    # CRITICAL: simply dropping the member from composed_of is NOT enough —
    # the host's accumulated fields (catalog, weights, sources, year) were
    # BAKED INTO the foundation entry by prior enrichment runs (_deep_merge_
    # catalog merges members[0]=fc's own catalog, so an evicted member's
    # km/hede survives in fc even after it leaves composed_of). That stale
    # km then lets the matcher RE-ABSORB the evicted member this very run
    # (48==48). So we RESET each host's accumulated fields to its clean
    # foundation twin (the seed_unified or raw-seed entry of the same id),
    # then drop evicted members + re-enrich from the remaining members only.
    # Curator-immutable fields (fuss/phase/kind/nominal/ruler/…) + composed_of
    # are preserved on fc. Evicted members are force-promoted standalone (or
    # re-matched into an existing same-KM home) below. COMPLEX cases (no-KM
    # member / A-prefix / same-km-multi / no clean twin) are NOT in the
    # allowlist — they await curator image verification.
    forced_evict_promote: set[str] = set()
    _purge_allow = _load_yaml(V2_OVERMERGE_PURGE)
    if isinstance(_purge_allow, dict) and any(
            h in final_by_id for h in _purge_allow):
        # Clean-foundation twin lookup: seed_unified (this entity) ∪ raw seeds.
        _twin: dict[str, dict] = dict(unified_by_id)
        for _sf in V2_SEED.rglob(f"*/{entity_id}.yml"):
            _sdoc = _load_yaml(_sf)
            for _sc in (_sdoc.get("coins") or []):
                if isinstance(_sc, dict) and _sc.get("id"):
                    _twin.setdefault(_sc["id"], _sc)
        # Fields the over-merge accumulated onto the foundation — reset from
        # the twin so they re-derive cleanly from the post-purge member set.
        _ACCUM = ("catalog", "weight_rough_g", "fineness", "diameter_mm",
                  "sources", "year_first", "year_last", "year_ranges",
                  "year_label", "year_verified")
        for host_id, evict_ids in _purge_allow.items():
            fc = final_by_id.get(host_id)
            if not fc or not isinstance(evict_ids, list):
                continue
            comp = fc.get("composed_of") or []
            evict_set = {e for e in evict_ids if e in comp}
            if not evict_set:
                continue
            twin = _twin.get(host_id)
            if twin is None:
                # No clean twin → cannot safely un-bake; leave merged (the
                # allowlist generator already filtered these to COMPLEX, so
                # this branch is a defensive no-op).
                continue
            for fld in _ACCUM:
                if fld in twin:
                    fc[fld] = copy.deepcopy(twin[fld])
                else:
                    fc.pop(fld, None)
            fc["composed_of"] = [c for c in comp if c not in evict_set]
            forced_evict_promote |= evict_set
    if forced_evict_promote:
        print(f"  over-merge purge: evicted {len(forced_evict_promote)} "
              f"different-KM member(s) + reset host(s) to clean twin "
              f"→ re-match + force-promote standalone")

    # RE-VALIDATE composed_of membership (IDENTITY mismatch eviction).
    # The over-merge purge above only handles the curator-reviewed base-KM
    # allowlist; this pass is criterion-driven and catches the broader
    # «wrong-nominal member fused into a foundation» class (e.g. KM 42
    # «8 Skilling» dragging in «1 Denning» + «4 Skilling lybsk»). Criterion
    # = genuine nominal differ + no type-level catalogue tie (= the shipped
    # merger nominal discriminator, applied to existing membership). Each
    # evicted member is surgically decontaminated off the host (its weight /
    # source contributions removed, orphan + remaining-member data kept),
    # dropped from composed_of, and force-promoted standalone so it re-homes
    # — the discriminator then blocks it re-absorbing (no type-level tie).
    if REVALIDATE_ENABLED:
        revalid = _revalidate_composed_of(final_by_id, unified_by_id, entity_id)
        revalid_evicted = 0
        for host_id, evict_set in revalid.items():
            fc = final_by_id.get(host_id)
            if not fc:
                continue
            comp = list(fc.get("composed_of") or [])
            evict_now = {e for e in evict_set if e in comp}
            if not evict_now:
                continue
            evicted_members = [unified_by_id[e] for e in evict_now
                               if e in unified_by_id]
            remaining_members = [unified_by_id[c] for c in comp
                                 if c not in evict_now and c in unified_by_id]
            _surgical_decontaminate(fc, evicted_members, remaining_members)
            fc["composed_of"] = [c for c in comp if c not in evict_now]
            forced_evict_promote |= evict_now
            revalid_evicted += len(evict_now)
            for e in sorted(evict_now):
                m = unified_by_id.get(e, {})
                print(f"  re-validate: {host_id} ({fc.get('nominal')!r}) "
                      f"✗ evict {e} ({m.get('nominal')!r}) — identity mismatch")
        if revalid_evicted:
            print(f"  re-validate: evicted {revalid_evicted} identity-"
                  f"mismatched member(s) across {len(revalid)} host(s) "
                  f"→ decontaminated + force-promote standalone")

    # Build: already-absorbed unified ids (across all final composed_of lists)
    already_absorbed: dict[str, str] = {}
    for fid, fc in final_by_id.items():
        for cid in fc.get("composed_of") or []:
            already_absorbed[cid] = fid

    # Curator no_merges (merge_decisions::no_merges) are authoritative over
    # the absorb matcher too: a member the curator declared a DIFFERENT coin
    # from a foundation must NOT be absorbed into it — even when match_pair
    # says confident on nominal+ruler+year. The §9.4 base-KM guard cannot
    # catch the no-KM case (e.g. dk-tid-94338 KM 564 vs Hede 9 f5h9: f5h9 has
    # no KM, so it would re-fuse on nominal+year confidence). Resolve each
    # entry to its underlying SEED set (a final foundation's composed_of holds
    # unified ids → expand via unified_by_id to their seeds; its own id is a
    # seed for raw-seed foundations) and refuse any absorb that would unite a
    # registered no_merge seed pair.
    _nm_doc = _load_yaml(V2_MERGE_DECISIONS / f"{entity_id}.yml")
    _no_merge_pairs: set = set()
    for nm in (_nm_doc.get("no_merges") or []):
        mem = [x for x in (nm.get("members") or []) if x]
        for i in range(len(mem)):
            for j in range(i + 1, len(mem)):
                _no_merge_pairs.add(frozenset({mem[i], mem[j]}))

    def _seeds_of_entry(e: dict) -> set:
        out: set = set()
        eid = e.get("id")
        if eid:
            out.add(eid)
        for m in (e.get("composed_of") or []):
            if m == eid:
                continue
            out.add(m)
            um = unified_by_id.get(m)
            if um is not None:
                out |= {s for s in (um.get("composed_of") or []) if s}
        return {x for x in out if x}

    def _curator_no_merged(a: dict, b: dict) -> bool:
        if not _no_merge_pairs:
            return False
        sa, sb = _seeds_of_entry(a), _seeds_of_entry(b)
        for x in sa:
            for y in sb:
                if frozenset({x, y}) in _no_merge_pairs:
                    return True
        return False

    # Iterate unified entries, find matches in final
    new_links: dict[str, list[str]] = defaultdict(list)
    unmatched: list[str] = []
    multi_match: list[dict] = []
    already_in = 0

    for unified in unified_entries:
        uid = unified.get("id")
        if not uid:
            continue
        if uid in already_absorbed:
            already_in += 1
            continue
        # Find match against final entries (per §5.2 hierarchy)
        candidates = []
        for fid, fc in final_by_id.items():
            if _curator_no_merged(unified, fc):
                continue  # curator no_merge: different coin — never absorb
            result = match_pair(unified, fc, entity_id, reign_index=reign_index)
            if result["decision"] == "confident":
                candidates.append(fid)
        # Globally-unique-ID absorb fallback (§dup-audit T1 residual,
        # 2026-05-30). When no confident match_pair candidate exists, a
        # unified entry STILL absorbs into a foundation that shares an
        # AGREEING globally-unique ref (numista N# / bruun coll-id) —
        # PROVIDED exactly one foundation qualifies AND match_pair's
        # failure was not on a hard physical signal (metal / nominal).
        # This catches the «same Numista type, divergent Lange sub-number»
        # case (e.g. unified-dk-numista-301095 vs km-132-chr-a-1681 —
        # both cite N#301095 + km=132, but lange «405» vs «404A,405» makes
        # the catalog chain «disagree» → match_pair no_match). The shared
        # N# is identity-proof; the Lange divergence is cross-source noise.
        #
        # Scoped to ABSORB only (not the merger's union-find) so it can't
        # trigger transitive over-merge across seeds. The exactly-one
        # guard rejects the year-variant false-positive (Numista groups
        # multiple struck years under one N#; OUR data splits them into
        # several foundations → multiple share the N# → ambiguous → skip).
        if not candidates:
            u_refs = _catalog_refs(unified, entity_id)
            id_fallback = []
            for fid, fc in final_by_id.items():
                if _curator_no_merged(unified, fc):
                    continue  # curator no_merge: different coin — never absorb
                f_refs = _catalog_refs(fc, entity_id)
                if not _shares_unique_id_ref(u_refs, f_refs):
                    continue
                r = match_pair(unified, fc, entity_id, reign_index=reign_index)
                # Don't override a hard physical-signal disagreement.
                if r["primary"].get("metal") is False:
                    continue
                if r["primary"].get("nominal") is False:
                    continue
                # §9.4 guard: never absorb across genuinely different BASE KM,
                # even on a shared globally-unique ref. Numista groups multiple
                # Krause KM under one N#, so a shared N# must NOT fuse KM 40
                # with KM 48 (this fallback was the over-merge root cause —
                # 2026-05-31 audit). Bare-vs-subvariant (KM 70 ≡ 70.1) and
                # absent-KM still pass: divergent ONLY when both base-sets are
                # non-empty AND disjoint (list-form KM that shares a base, e.g.
                # 21.2 vs ['21','21.1'], is the SAME coin).
                ub, fb = _km_bases(unified), _km_bases(fc)
                if ub and fb and ub.isdisjoint(fb):
                    continue
                id_fallback.append(fid)
            if len(id_fallback) == 1:
                candidates = id_fallback
        if not candidates:
            unmatched.append(uid)
        elif len(candidates) == 1:
            new_links[candidates[0]].append(uid)
        else:
            # Multi-match — ambiguous; flag for review, link to first
            new_links[candidates[0]].append(uid)
            multi_match.append({"unified_id": uid, "candidates": candidates})

    # Re-derive enrichment on each final entry whose composed_of CHANGED
    # OR re-derive on all (idempotent — same output for stable input).
    # We choose «re-derive on all» so the data-accumulation invariant is
    # always enforced fresh: every final's multi-source lists reflect
    # the current composed_of state without growing or shrinking
    # accidentally.
    enriched_entries: list[dict] = []
    enrichment_conflicts: list[dict] = []
    for fid, fc in final_by_id.items():
        # Compose member list: final itself (foundation, top priority) +
        # any unified entries in composed_of (after new links applied)
        full_composed = sorted(set(fc.get("composed_of") or []) | set(new_links.get(fid, [])))
        members = [fc]
        for mid in full_composed:
            if mid in unified_by_id:
                members.append(unified_by_id[mid])
        enriched, conflicts = _enrich_final_entry(fc, members, entity_id)
        enriched_entries.append(enriched)
        if conflicts:
            enrichment_conflicts.append({
                "final_id": fid,
                "members": full_composed,
                "conflicts": [
                    {"field": f, "foundation_value": t, "absorbed_value": o}
                    for f, t, o in conflicts
                ],
            })

    # D37 BULK-PROMOTE PENDING: when the curator-decision flag is set,
    # the unmatched unified entries (= no V1-foundation conflict possible
    # because there IS no V1 foundation, by assertion) become the
    # entity's INITIAL foundation. Each unified entry's data is written
    # into final verbatim, with the `composed_of` audit-trail listing
    # the unified id itself (a self-promote — distinguishes a bulk-
    # promoted entry from a V1-bootstrap-foundation entry that has
    # `composed_of: []`).
    # Pre-load curator assignments so the bulk-promote loop can force-
    # promote any pending unified entry that the curator has explicitly
    # classified. Without this, an assignment on a pending entry whose
    # bulk_promote mode would otherwise skip it (e.g.
    # `no_basic_peer_only` when a basic peer exists) goes unapplied —
    # the assignment is the curator's explicit «yes, add this row»
    # decision, so the policy gate should be bypassed for it.
    _decisions_pre = _load_yaml(V2_CLASSIFICATION_DECISIONS / f"{entity_id}.yml")
    _assignment_ids: set[str] = set()
    for a in _decisions_pre.get("assignments") or []:
        if isinstance(a, dict) and a.get("coin_id"):
            _assignment_ids.add(a["coin_id"])

    bulk_promoted: list[str] = []
    bulk_skipped: list[str] = []  # mode="no_basic_peer_only" — peer-exists cases stay pending
    if bulk_promote_mode is not None:
        existing_finals_for_peer_check = list(final_by_id.values())
        for uid in unmatched:
            unified = unified_by_id.get(uid)
            if not unified:
                continue
            # Curator-assignment force-promote: if this unified id has
            # an explicit fuss/phase assignment, promote regardless of
            # the bulk_promote_mode gate. Curator decided — the gate
            # exists to keep ambiguous cases parked in pending, not
            # to override decisions.
            force_promote = uid in _assignment_ids or uid in forced_evict_promote
            # Mode «no_basic_peer_only» (D39): only promote when the
            # unified entry has NO metal+nominal peer in foundation.
            # Skips D/E/H/C-category cases where promoting would
            # silently duplicate an existing foundation entry whose
            # auto-match was blocked by a fixable signal disagreement.
            if bulk_promote_mode == "no_basic_peer_only" and not force_promote:
                if _has_basic_peer(unified, existing_finals_for_peer_check,
                                   entity_id, reign_index=reign_index):
                    bulk_skipped.append(uid)
                    continue
            # Mode «no_match_primary_disagrees» (D40): superset of D39.
            # Promote when EITHER no basic peer exists OR every basic
            # peer's match_pair returned `no_match` with explicit
            # primary-signal disagreement (catalog False ≡ different
            # KM/Hede sub-variant, ruler False ≡ different reign).
            # Keeps `low_confidence` AND fallback-only-disagreement
            # cases in pending for curator review.
            elif bulk_promote_mode == "no_match_primary_disagrees" and not force_promote:
                primary_disagreement = _all_basic_peers_no_match_primary(
                    unified, existing_finals_for_peer_check,
                    entity_id, reign_index=reign_index,
                )
                if primary_disagreement is False:
                    # Basic peer exists but matcher didn't say
                    # «definitively different by primary signal»
                    # (H or C category) — skip for curator review.
                    bulk_skipped.append(uid)
                    continue
                # primary_disagreement is True (D/E case — safe promote)
                # OR None (no basic peer — falls through to promote,
                # same path as D39 «no_basic_peer_only»).
            # Bake the promoted entry's `composed_of` to include the
            # self-id so subsequent runs recognise it as already-
            # absorbed (via the `already_absorbed` index built from
            # final.composed_of at the top of process_entity). Then
            # route through `_enrich_final_entry` so the output has
            # the SAME canonical field layout as V1-foundation entries
            # — guarantees idempotency on re-runs.
            promoted_stub = dict(unified)
            promoted_stub["composed_of"] = [uid]
            # Apply curator-classification migration from any V1-bootstrap
            # foundation(s) that the merger consolidated into this unified
            # host (see `curator_migrations` build above). This ensures the
            # bulk-promoted entry inherits the V1 curator's fuss / phase /
            # kind / mintmaster / etc. instead of falling back to the
            # source seed's raw defaults («fuss: seed_unsorted»).
            migrated = curator_migrations.get(uid)
            if migrated:
                for field, value in migrated.items():
                    # Merge-form keys carry «__merge__<field>» prefix —
                    # union with existing list under the bare field name,
                    # deduped by URL (or full repr for non-URL entries).
                    if field.startswith("__merge__"):
                        bare = field[len("__merge__"):]
                        existing_list = promoted_stub.get(bare) or []
                        if not isinstance(existing_list, list):
                            existing_list = [existing_list]
                        seen_urls: set[str] = set()
                        for e in existing_list:
                            if isinstance(e, dict) and e.get("url"):
                                seen_urls.add(e["url"])
                        for v_entry in value:
                            url = v_entry.get("url") if isinstance(v_entry, dict) else None
                            if url and url in seen_urls:
                                continue
                            if url:
                                seen_urls.add(url)
                            existing_list.append(v_entry)
                        promoted_stub[bare] = existing_list
                        continue
                    # Don't overwrite a non-trivial value the seed already
                    # carries — but DO overwrite when the seed has the
                    # default placeholder («seed_unsorted» for fuss, the
                    # source's raw phase name like «bruun» / «ucoin»).
                    seed_val = promoted_stub.get(field)
                    if field == "fuss" and seed_val == "seed_unsorted":
                        promoted_stub[field] = value
                    elif field == "phase" and seed_val in (
                            None, "bruun", "ucoin", "numismaster",
                            "numista", "hede", "galster"):
                        promoted_stub[field] = value
                    elif seed_val in (None, "", [], {}):
                        promoted_stub[field] = value
                    # else: seed already has a curator-set value; keep it.
            enriched, _ = _enrich_final_entry(
                promoted_stub, [promoted_stub], entity_id
            )
            enriched_entries.append(enriched)
            bulk_promoted.append(uid)
        # Update pending lists. Skipped entries (mode "no_basic_peer_only"
        # with a matchable peer) stay in unmatched for curator review.
        unmatched = bulk_skipped
        if bulk_promote_mode == "all":
            multi_match = []  # mode «all» subsumes multi-match decisions

    # CURATOR ASSIGNMENTS — apply explicit fuss/phase/kind overrides
    # declared in `data/v2/classification_decisions/<entity>.yml::assignments`.
    # The docstring at top of file states: «Curator declares ... {coin_id:
    # {fuss, phase, kind}}; on next run, absorb adds the entry to final
    # with the declared classification.» Without this block the file's
    # assignments were merely PRESERVED on writeback but never APPLIED,
    # leaving curator-classified entries stuck at `fuss=seed_unsorted`
    # after they had been bulk-promoted. (Observed 2026-05-25 for the
    # Galster f1g-68/f1g-69 Frederik I Nobel u.år Ribe pair: assignments
    # to nobel_fod/I/kurant were declared and preserved, but the final
    # entries kept fuss=seed_unsorted/phase=galster.)
    #
    # Matching: assignment.coin_id is looked up against (a) each enriched
    # entry's `id` directly, and (b) each enriched entry's `composed_of`
    # member ids. Direct id match wins when both apply. Override touches
    # only the three classification fields (fuss/phase/kind); all other
    # data on the entry stays intact.
    decisions_doc = _load_yaml(V2_CLASSIFICATION_DECISIONS / f"{entity_id}.yml")
    raw_assignments = decisions_doc.get("assignments") or []
    assignment_by_coin_id: dict[str, dict] = {}
    for a in raw_assignments:
        if not isinstance(a, dict):
            continue
        cid = a.get("coin_id")
        if cid:
            assignment_by_coin_id[cid] = a
    applied_assignments: list[str] = []
    unapplied_assignments: list[str] = []
    if assignment_by_coin_id:
        for entry in enriched_entries:
            eid = entry.get("id")
            assignment: dict | None = None
            if eid and eid in assignment_by_coin_id:
                assignment = assignment_by_coin_id[eid]
                applied_assignments.append(eid)
            else:
                for cid in entry.get("composed_of") or []:
                    if cid in assignment_by_coin_id:
                        assignment = assignment_by_coin_id[cid]
                        applied_assignments.append(cid)
                        break
            if assignment is None:
                continue
            for field in ("fuss", "phase", "kind"):
                if assignment.get(field):
                    entry[field] = assignment[field]
        # Diagnostic: assignments whose coin_id matched nothing.
        all_known_ids: set[str] = set()
        for e in enriched_entries:
            if e.get("id"):
                all_known_ids.add(e["id"])
            for cid in e.get("composed_of") or []:
                all_known_ids.add(cid)
        for coin_id in assignment_by_coin_id:
            if coin_id not in all_known_ids:
                unapplied_assignments.append(coin_id)

    # FRACTION INFERENCE — when a final entry has fuss != seed_unsorted +
    # a parseable nominal but NO fraction, derive it from the fuss+nominal
    # rules in `lib.fraction_infer`. Without `fraction` set, the build's
    # `_compute_coin` (scripts/lib/compute.py:558) can't look up
    # `fuss.fractions[fraction]` and the Soll-Feingewicht + Δ columns
    # render blank — hiding analysis that could be done from data the
    # entry already carries (weight + fineness). User direction
    # 2026-05-27: «ці дані мають прораховуватись як тільки коін отримує
    # своє місце в стопі».
    #
    # Two paths:
    #   (a) FILL — fraction is currently None → inferred value emitted.
    #   (b) CORRECT — fraction was set by a PRIOR (buggy) inference run
    #       AND the fresh inference returns a different value. The
    #       common bug-pattern: «½ Skilling» under 9_25_thaler used to
    #       infer `1/2` (leading_frac applied as-if head was the base
    #       unit) when the correct answer is `1/192` (½ × 1/96 sub-unit
    #       fraction). The fix at the lib level (sub-unit-aware path 1)
    #       only kicks in for new None values; we ALSO replace existing
    #       values that match the buggy shape so the data converges on
    #       the fresh logic without manual cleanup.
    #
    # Curator overrides via `_curation_holds: [fraction, ...]` always
    # win — neither path touches `fraction` when it's in holds. This is
    # the lever the curator uses to pin a value across regens (e.g.
    # «½ Krone» of a Kipper-period coin that doesn't follow the textbook
    # ratio).
    fuss_fractions_cache = _get_fuss_fractions_cache()
    inferred_fractions_count = 0
    corrected_fractions_count = 0
    for entry in enriched_entries:
        holds = set(entry.get("_curation_holds") or [])
        if "fraction" in holds:
            continue  # curator-pinned, never touch
        existing = entry.get("fraction")
        cand = infer_fraction(entry, fuss_fractions_cache)
        if not cand:
            continue
        if not existing:
            entry["fraction"] = cand
            inferred_fractions_count += 1
            continue
        # existing is set; consider replacement only when the prior value
        # matches the LEGACY buggy-path output AND fresh inference gives
        # a different (correct) value. The legacy path returned the bare
        # leading_frac of the nominal regardless of whether the head was
        # a sub-unit; that's exactly the shape to overwrite.
        if str(existing) == str(cand):
            continue
        # Reproduce the legacy path-1 output: if nominal has a leading
        # unicode/text fraction AND that fraction is the current value,
        # this entry was likely set by the buggy code. Overwrite.
        nom = entry.get("nominal") or ""
        from lib.fraction_infer import _parse_nominal_head as _pnh
        leading_frac, _count, _rest = _pnh(nom)
        if leading_frac and str(existing) == leading_frac:
            entry["fraction"] = cand
            corrected_fractions_count += 1
    if inferred_fractions_count:
        print(f"  [{entity_id}] fraction-inference: "
              f"set on {inferred_fractions_count} entries from nominal+fuss")
    if corrected_fractions_count:
        print(f"  [{entity_id}] fraction-inference: "
              f"corrected {corrected_fractions_count} entries "
              f"(prior buggy leading-frac path output)")

    # STALE-FINAL DROP (2026-06-10). Absorb is otherwise additive/sticky: a
    # final entry persists across runs even when the seed_unified entry that
    # backed it disappears (its seed source was deleted or filtered out). The
    # "stale composed_of refs purged" step above only trims dead REFS inside a
    # surviving final — it never drops a WHOLE final whose every backing member
    # has vanished. That left 622 stale exonumia finals behind during the
    # 2026-06-09 KMM-exonumia suppress; they had to be removed by hand. This
    # closes the loop: parallel to the out-of-scope and stale-foundation purges
    # above, drop a final iff ALL of:
    #   (a) it is a PIPELINE-PROMOTED entry (id form `unified-*`). A
    #       V1-bootstrap foundation (real id, e.g. `dk-tid-…`) is the coin's
    #       OWN data and is never seed-derived — it is NEVER dropped here, even
    #       if its seed enrichment vanished (the curation guard (c) is a second
    #       line of defence, but the id-form gate is the primary one);
    #   (b) it has NO live backing — neither its own id nor any composed_of
    #       member resolves to a CURRENT seed_unified head. Assessed HERE, after
    #       enrichment has refreshed composed_of via `new_links`, so a unified
    #       that was merely RE-KEYED (not deleted) is re-linked and still counts
    #       as backed → no false drop;
    #   (c) it carries NO curation — fuss is seed_unsorted/None, no `note`, no
    #       `_curation_holds`, no `promoted_to`, and no curator-assigned phase
    #       (a bare seed-source phase tag like `kmk`/`bruun` is not curation).
    # A CURATED entry whose backing vanished is KEPT (surfaced, not silently
    # dropped) — same spirit as §4 / the D-series "curated/verified wins": never
    # lose curator work to an automated pass. The dropped ids are excluded from
    # the monotonic guard below so it cannot re-promote them.
    _live_unified_ids = set(unified_by_id)
    _live_seed_ids = {
        s for u in unified_entries for s in (u.get("composed_of") or [])
    }
    _live_ids = _live_unified_ids | _live_seed_ids

    stale_dropped_ids: set[str] = set()
    _kept_after_stale: list[dict] = []
    for e in enriched_entries:
        if _is_vanished_stale_final(e, _live_unified_ids, _live_ids):
            stale_dropped_ids.add(str(e.get("id")))
            continue
        _kept_after_stale.append(e)
    enriched_entries = _kept_after_stale
    if stale_dropped_ids:
        print(f"  [{entity_id}] stale finals dropped: "
              f"{len(stale_dropped_ids)} entries (backing seed_unified gone, "
              f"no curation): {sorted(stale_dropped_ids)[:8]}")

    # MONOTONIC-ABSORB GUARD (TODO §CH). A coin already on the page must
    # not silently vanish from final just because a new source (IKMK, …)
    # was merged in and shifted the stale-foundation-purge / bulk-promote
    # decisions. Re-promote any prior-final coin that is NOT represented in
    # the new final, EXCEPT the legitimately-dropped kinds:
    #   • out-of-scope (nominal / catalog) — correctly purged;
    #   • article-page narrative foundation (Shape C) — not a real coin;
    #   • genuinely consolidated — its id / source-ids appear in some new
    #     entry's id or composed_of (the merger merged it into a peer).
    # The re-add is VERBATIM (the prior standalone entry) — it never fuses
    # two coins; genuine cross-source merges stay the merger's job and are
    # surfaced for curator image-review, never auto-decided here.
    new_repr_ids: set[str] = set()
    for e in enriched_entries:
        if e.get("id"):
            new_repr_ids.add(e["id"])
        for m in e.get("composed_of") or []:
            new_repr_ids.add(m)
            # Resolve a unified composed_of member → its underlying seeds, so
            # a prior STANDALONE final (id form `unified-<seed>`) that a
            # curator merge_decision has since consolidated into this entry
            # (its seed now sits in the host unified's composed_of) is
            # recognised as consolidated and NOT spuriously re-promoted by
            # the monotonic guard. Add both the bare seed id and its
            # `unified-`-prefixed standalone-promote form.
            um = unified_by_id.get(m)
            if um:
                for s in um.get("composed_of") or []:
                    new_repr_ids.add(s)
                    if not s.startswith("unified-"):
                        new_repr_ids.add("unified-" + s)
    monotonic_restored: list[str] = []
    for fc in _prior_final_for_monotonic:
        fid = fc.get("id")
        if not fid or fid in new_repr_ids:
            continue
        # Vanished-backing stale final — do NOT resurrect. Checked directly on
        # the prior-final entry (not via `stale_dropped_ids`) because such an
        # entry may have been removed by an EARLIER purge (stale-foundation /
        # self-fold) before the explicit stale-final filter above could see it;
        # without this the monotonic guard re-promotes it verbatim and the
        # whole point is defeated. Only fires for entries ABSENT from the new
        # final (guarded by the `fid in new_repr_ids` check above), so a merely
        # re-keyed unified — which would be present, re-linked via new_links —
        # never reaches here. Same id-form + no-backing + no-curation gate as
        # the explicit filter; both feed `stale_dropped_ids` for the stat.
        if _is_vanished_stale_final(fc, _live_unified_ids, _live_ids):
            stale_dropped_ids.add(str(fid))
            continue
        if (_is_out_of_scope_nominal(fc.get("nominal"))
                or _is_out_of_scope_catalog(fc.get("catalog"))
                or _is_out_of_scope_year(fc.get("year_first"))):
            continue  # OOS — correctly dropped
        src_ids = {fid} | set(fc.get("composed_of") or [])
        if src_ids & new_repr_ids:
            continue  # consolidated into a peer — its data is in final
        composed_real = [c for c in (fc.get("composed_of") or []) if c != fid]
        if not composed_real:
            srcs = fc.get("sources") or []
            if any(isinstance(s, dict)
                   and ("/ernst/" in str(s.get("url") or "")
                        or "/artikler/" in str(s.get("url") or ""))
                   for s in srcs):
                continue  # article-page narrative foundation (Shape C)
        enriched_entries.append(fc)
        new_repr_ids.add(fid)
        monotonic_restored.append(fid)
    if monotonic_restored:
        print(f"  [{entity_id}] monotonic guard: re-promoted "
              f"{len(monotonic_restored)} prior-final coin(s) a re-merge "
              f"would have de-promoted (verbatim, no merge): "
              f"{monotonic_restored[:8]}")

    return {
        "entity_id": entity_id,
        "unified_total": len(unified_entries),
        "final_total_before": len(final_entries),
        "final_total_after": len(enriched_entries),
        "already_absorbed": already_in,
        "newly_absorbed": sum(len(v) for v in new_links.values()),
        "genuinely_new": len(unmatched),
        "bulk_promoted": len(bulk_promoted),
        "stale_purged": purged_count,
        "out_of_scope_dropped": out_of_scope_final_dropped,
        "stale_finals_dropped": len(stale_dropped_ids),
        "unmatched_unified_ids": unmatched,
        "multi_match_warnings": multi_match,
        "enrichment_conflicts": enrichment_conflicts,
        "enriched_final_entries": enriched_entries,
        "applied_assignments": applied_assignments,
        "unapplied_assignments": unapplied_assignments,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _emit_final_yaml(entity_id: str, coins: list[dict],
                     prior_doc: dict | None) -> str:
    """Render `data/v2/final/<entity>.yml`. Preserve prior doc-level
    metadata (id, source_locations, migrated_from_v1, …) while replacing
    the coins[] list with the re-derived enriched entries."""
    payload = {
        "id": entity_id,
        "source_locations": (prior_doc or {}).get("source_locations") or [],
        "migrated_from_v1": (prior_doc or {}).get("migrated_from_v1") or "",
        "coins": coins,
    }
    return yaml.dump(payload, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=120)


def _emit_classification_decisions(entity_id: str, unmatched_ids: list[str],
                                    multi_match: list[dict]) -> str:
    today = date.today().isoformat()
    header = (
        f"# Classification decisions for entity `{entity_id}` (Phase 4).\n"
        f"# Curator-authoritative file (committed). Two sections:\n"
        f"#\n"
        f"# 1. `assignments:` — explicit fuss/phase for ambiguous coins.\n"
        f"#    Each entry adds a NEW final entry on next absorb run.\n"
        f"#    Example:\n"
        f"#      assignments:\n"
        f"#        - coin_id: unified-dk-numismaster-12345\n"
        f"#          fuss: 9_25_thaler\n"
        f"#          phase: A\n"
        f"#          kind: kurant\n"
        f"#          reason: 'specimen Δ ambiguous; per Hede assignment'\n"
        f"#\n"
        f"# 2. `pending:` — auto-populated diagnostic list of unified\n"
        f"#    entries with no match in current final. Curator either:\n"
        f"#    moves an entry to `assignments:` with classification,\n"
        f"#    OR fixes the matcher rules so the coin gets absorbed,\n"
        f"#    OR confirms it's a genuinely new coin needing addition\n"
        f"#    (will be auto-routed by §8a once that's built).\n"
        f"#\n"
        f"# This file is REGENERATED on every absorb run for the\n"
        f"# `pending:` section; existing `assignments:` entries are\n"
        f"# preserved.\n\n"
    )
    # Try to preserve existing assignments + the bulk_promote_pending flag.
    # Critical: PRESERVE the original value verbatim — D37 carries
    # `bulk_promote_pending: true` (mode "all"), D39 carries
    # `bulk_promote_pending: no_basic_peer_only` (mode "no_basic_peer_only").
    # Collapsing to `bool(...)` silently downgrades D39 → D37 on the
    # next run because `True` round-trips as YAML `true`, which the
    # `_bulk_promote_mode` reader maps to mode "all" (bug observed
    # 2026-05-19, see V2_DECISIONS D39 note).
    existing = _load_yaml(V2_CLASSIFICATION_DECISIONS / f"{entity_id}.yml")
    existing_assignments = existing.get("assignments") or []
    bulk_value = existing.get("bulk_promote_pending")
    payload: dict = {
        "entity_id": entity_id,
        "generated_at": today,
    }
    if bulk_value:
        payload["bulk_promote_pending"] = bulk_value
    payload["assignments"] = existing_assignments
    payload["pending"] = [{"unified_id": uid, "status": "no_match_in_final"}
                          for uid in unmatched_ids]
    payload["multi_match_warnings"] = multi_match
    return header + yaml.dump(payload, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=120)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write outputs (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Write data/v2/final/ + data/v2/classification_decisions/")
    parser.add_argument("--entity", help="Process only this entity")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--no-revalidate", action="store_true",
                        help="Skip composed_of re-validation (identity-"
                             "mismatch eviction) for this run")
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False
    if args.no_revalidate:
        global REVALIDATE_ENABLED
        REVALIDATE_ENABLED = False

    entities = [args.entity] if args.entity else _entities_with_seed_unified()
    if not entities:
        print("No V2 seed_unified files found.")
        return 0

    print(f"Processing {len(entities)} entit(y/ies)...\n")

    totals = Counter()
    for ent in entities:
        result = process_entity(ent)
        totals["unified_total"] += result["unified_total"]
        totals["final_total_after"] += result["final_total_after"]
        totals["already_absorbed"] += result["already_absorbed"]
        totals["newly_absorbed"] += result["newly_absorbed"]
        totals["genuinely_new"] += result["genuinely_new"]
        totals["bulk_promoted"] += result.get("bulk_promoted", 0)
        totals["stale_purged"] += result.get("stale_purged", 0)
        totals["out_of_scope_dropped"] += result.get("out_of_scope_dropped", 0)
        totals["stale_finals_dropped"] += result.get("stale_finals_dropped", 0)
        totals["multi_match"] += len(result["multi_match_warnings"])
        totals["enrichment_conflicts"] += len(result["enrichment_conflicts"])
        totals["applied_assignments"] += len(result.get("applied_assignments") or [])
        totals["unapplied_assignments"] += len(result.get("unapplied_assignments") or [])

        line = (
            f"{ent:36s}  "
            f"unified:{result['unified_total']:4d}  "
            f"final:{result['final_total_before']:>4d}→{result['final_total_after']:>4d}  "
            f"abs(prev):{result['already_absorbed']:3d}  "
            f"abs(new):{result['newly_absorbed']:3d}  "
            f"new_coins:{result['genuinely_new']:3d}"
        )
        if result.get("bulk_promoted"):
            line += f"  bulk_promote:{result['bulk_promoted']}"
        if result.get("applied_assignments"):
            line += f"  assigned:{len(result['applied_assignments'])}"
        if result.get("unapplied_assignments"):
            line += f"  ASSIGN-MISS:{len(result['unapplied_assignments'])}"
        if result["multi_match_warnings"]:
            line += f"  multi:{len(result['multi_match_warnings'])}"
        if result["enrichment_conflicts"]:
            line += f"  conflicts:{len(result['enrichment_conflicts'])}"
        print(line)

        if args.verbose and result.get("unapplied_assignments"):
            print(f"    assignments with unknown coin_id (skipped):")
            for cid in result["unapplied_assignments"]:
                print(f"      • {cid}")

        if args.verbose and result["unmatched_unified_ids"]:
            print(f"    pending (no match in final):")
            for uid in result["unmatched_unified_ids"][:5]:
                print(f"      • {uid}")
            if len(result["unmatched_unified_ids"]) > 5:
                print(f"      • ... and {len(result['unmatched_unified_ids']) - 5} more")

        if args.apply:
            # Write enriched final yaml directly (not via merge_seed):
            # `_enrich_final_entry` already preserves V1-foundation
            # immutable fields verbatim from each existing final entry,
            # so the enriched list IS the canonical state. Going through
            # merge_seed would re-trigger CURATED_FIELDS preservation —
            # which would block composed_of updates (existing empty list
            # is treated as «present» and wins over the fresh non-empty
            # list per the «existing wins when present» rule). Direct
            # write is correct here because we read+enrich every existing
            # entry — no orphan curator data possible.
            V2_FINAL.mkdir(parents=True, exist_ok=True)
            final_path = V2_FINAL / f"{ent}.yml"
            prior_doc = _load_yaml(final_path)
            # §9.4 blanket index hygiene: fold `others: <code># N` → typed
            # list-field + case-insensitive value de-dup on EVERY final
            # entry — including V1-carryover / prior-absorb foundations that
            # were not re-enriched this run (no current seed_unified member),
            # whose stale overflow would otherwise survive. Skips entries
            # that froze `catalog` via `_curation_holds`.
            for _fc in result["enriched_final_entries"]:
                if not isinstance(_fc, dict):
                    continue
                if isinstance(_fc.get("catalog"), dict):
                    _h = _fc.get("_curation_holds")
                    _hk = set(_h.keys() if isinstance(_h, dict)
                              else (_h or []))
                    if "catalog" not in _hk:
                        _fold_catalog_indices(_fc["catalog"])
                # Uninformative-KMM thinning on EVERY final entry (incl.
                # V1-carryover foundations not re-enriched this run).
                _suppress_weightless_museum_overcollection(_fc)
            final_path.write_text(
                _emit_final_yaml(ent, result["enriched_final_entries"],
                                  prior_doc),
                encoding="utf-8",
            )

            # Write classification_decisions pending list (always — regenerated).
            # Also rewrite when the file ALREADY EXISTS even if pending is
            # now empty — bulk-promote (D37) clears the pending list and
            # we need to drop stale entries from the previous run. The
            # existing-assignments + bulk_promote_pending flag are preserved
            # by `_emit_classification_decisions` reading the prior file.
            existing_decisions_path = V2_CLASSIFICATION_DECISIONS / f"{ent}.yml"
            if (
                result["unmatched_unified_ids"]
                or result["multi_match_warnings"]
                or existing_decisions_path.exists()
            ):
                V2_CLASSIFICATION_DECISIONS.mkdir(parents=True, exist_ok=True)
                existing_decisions_path.write_text(
                    _emit_classification_decisions(
                        ent,
                        result["unmatched_unified_ids"],
                        result["multi_match_warnings"],
                    ),
                    encoding="utf-8",
                )

    print()
    print(f"=== Totals ===")
    print(f"  Unified entries total:           {totals['unified_total']:>5d}")
    print(f"  Final entries after run:         {totals['final_total_after']:>5d}")
    print(f"  Already absorbed (prev runs):    {totals['already_absorbed']:>5d}")
    print(f"  Newly absorbed this run:         {totals['newly_absorbed']:>5d}")
    print(f"  Bulk-promoted (D37):             {totals['bulk_promoted']:>5d}")
    print(f"  Genuinely new (pending):         {totals['genuinely_new']:>5d}")
    print(f"  Stale composed_of refs purged:   {totals['stale_purged']:>5d}")
    print(f"  Out-of-scope finals dropped:     {totals['out_of_scope_dropped']:>5d}")
    print(f"  Stale finals dropped (no backing):{totals['stale_finals_dropped']:>5d}")
    print(f"  Multi-match warnings:            {totals['multi_match']:>5d}")
    print(f"  Enrichment conflicts (logged):   {totals['enrichment_conflicts']:>5d}")
    print(f"  Curator assignments applied:     {totals['applied_assignments']:>5d}")
    if totals['unapplied_assignments']:
        print(f"  Curator assignments unmatched:   {totals['unapplied_assignments']:>5d}  (coin_id not in unified/final)")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
    else:
        print(f"\n✓ Wrote enriched final yamls to {V2_FINAL}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
