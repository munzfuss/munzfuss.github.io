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
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_CLASSIFICATION_DECISIONS = ROOT / "data" / "v2" / "classification_decisions"

sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import merge_seed  # noqa: E402
from lib.v2_seed_writer import (  # noqa: E402
    _is_out_of_scope_nominal,
    _is_out_of_scope_catalog,
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
)


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
                # Curator explicitly froze year data — preserve via union
                authoritative_yr = _union_year_ranges(members)
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

    # Sources union — preserve curator-added entries on the foundation
    # alongside fresh seed-source citations, deduplicated by URL (single-
    # page hosts) or by (url, ref, type) (multi-record sources like the
    # Bruun PDF catalogues). The earlier `skip_first_list=True` dropped
    # the foundation's entire sources list to avoid phantom citations
    # from prior absorb runs — but it also dropped V1-curator-added
    # Numista / ucoin / auction refs that have no seed equivalent.
    # Phantom-citation persistence is a smaller issue than curator data
    # loss; dedup ensures legitimate duplicates collapse anyway.
    sources = _collect_sources(members)
    if sources:
        out["sources"] = sources

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
              "promoted_to", "_curation_holds"):
        if k in final_entry:
            out[k] = final_entry[k]

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
    _MIGRATION_PRESERVED_FIELDS = _FOUNDATION_IMMUTABLE_FIELDS | {"note"}

    def _migrate_classification(fe: dict, new_host_fid: str) -> None:
        """Snapshot curator-set fields for migration to new host.

        Includes foundation-immutable (fuss/phase/kind/etc.) AND
        curator-prose `note` field — the V1 entry's hand-written
        description that captures mint-master initials, engraver names,
        and other context not encoded in any source seed's structured
        fields.
        """
        snapshot = {
            field: fe[field]
            for field in _MIGRATION_PRESERVED_FIELDS
            if field in fe and fe[field] not in (None, "", [], {})
        }
        if not snapshot:
            return
        existing = curator_migrations.get(new_host_fid) or {}
        # Multiple stale foundations might both point at the same new host
        # (rare — only if 2+ V1 entries got merged into 1 unified by the
        # cross-source merger). Last-writer-wins is acceptable here: both
        # would carry the same curator classification by construction
        # (they ARE the same coin per the merger's confident match).
        existing.update(snapshot)
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

    # Build: already-absorbed unified ids (across all final composed_of lists)
    already_absorbed: dict[str, str] = {}
    for fid, fc in final_by_id.items():
        for cid in fc.get("composed_of") or []:
            already_absorbed[cid] = fid

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
            result = match_pair(unified, fc, entity_id, reign_index=reign_index)
            if result["decision"] == "confident":
                candidates.append(fid)
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
    bulk_promoted: list[str] = []
    bulk_skipped: list[str] = []  # mode="no_basic_peer_only" — peer-exists cases stay pending
    if bulk_promote_mode is not None:
        existing_finals_for_peer_check = list(final_by_id.values())
        for uid in unmatched:
            unified = unified_by_id.get(uid)
            if not unified:
                continue
            # Mode «no_basic_peer_only» (D39): only promote when the
            # unified entry has NO metal+nominal peer in foundation.
            # Skips D/E/H/C-category cases where promoting would
            # silently duplicate an existing foundation entry whose
            # auto-match was blocked by a fixable signal disagreement.
            if bulk_promote_mode == "no_basic_peer_only":
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
            elif bulk_promote_mode == "no_match_primary_disagrees":
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
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False

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
