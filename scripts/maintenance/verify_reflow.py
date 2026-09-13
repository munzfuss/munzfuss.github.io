#!/usr/bin/env python3
"""Field-diff every `data/v2/final/*.yml` against git HEAD, and call the losses.

WHY THIS EXISTS
---------------
Every other auditor in this project measures INSIDE the working tree:

    audit_curation_loss    final  vs  recomputed-from-unified  (what the NEXT apply would change)
    audit_lost_citations   final  vs  its own current members
    audit_v2               invariants within one state
    trace_coin             snapshot vs snapshot — both taken by hand

None of them answers the one question that actually gates a commit: **is the
rendered data worse than what is already committed?** That measurement had no
tool, so it got hand-rolled in a shell heredoc each time — and on 2026-08-01
four such hand-rolled baselines were each wrong in a different way:

  * an inventory keyed on the cached `body_excerpt`, which is `body[:600]` — a
    truncation — reported 25 suppressed lots and a table of 17 that included
    ordinary silver Speciedaler. The real figure, read from the full body, was 5.
  * a dangling-`composed_of` sweep resolved ids against ONE entity's
    seed_unified; cross-entity members live in other files, so it flagged six
    healthy records as dead and was one keystroke from writing that to disk.
  * a `trace_coin` snapshot taken with seeds updated but seed_unified/final
    stale measured a MIXTURE of two changes and reported «16 coins lost their
    final» where a comparison against real HEAD showed none.
  * a one-line merge change that looked obviously right rewrote 872 of 1695
    lines across 23 seed files into a wrong scalar shape, caught only by
    reading the diff.

The pattern is single: the comparison BASELINE was not what the author assumed.
Prose cannot fix that — CLAUDE.md §0b already demands verification from real
data, and all four happened anyway. A committed baseline is the one reference
that cannot be half-applied, mid-flight or silently truncated, so this tool
takes it from `git show HEAD:` and nothing else.

WHAT IT REPORTS
---------------
Per entity and in total: coins added, coins removed, coins changed, and for each
changed coin which fields moved — classified as a GAIN or a LOSS.

A LOSS is any of:
  * a coin present at HEAD that is gone now and was NOT folded into a survivor
    (a fold is recognised by the survivor listing it in `composed_of`, by one
    survivor having absorbed its source URLs, or by the survivors between them
    covering every one of those URLs — see REDISTRIBUTION below);
  * a scalar field that had a value at HEAD and is now empty;
  * a list field (sources / weight_rough_g / fineness / diameter_mm / catalog
    registers) that lost an entry NOTHING in the entity attests any more;
  * a change of `fuss` or `phase` from a real assignment back to `seed_unsorted`.

Everything else — new coins, new readings, a scalar filling in, a catalogue
register gaining a value — is a GAIN and never blocks.

A list entry is matched on its IDENTITY (a source's url, a reading's source
label), not on its whole content, so a CORRECTED value under an unchanged
identity is reported as a change and never as a loss. Keying on content cannot
tell the two apart: on 2026-08-02 that reported km-82-chr-iv-1640 as losing a
source and a weight while the coin had gained both — one kmk specimen's weight
had merely been corrected to 0.932. The gate's errors are safe in direction
(false alarm, never a missed loss), which is exactly why they must stay rare:
a gate that cries loss over a non-loss trains its reader to skim past it.

REDISTRIBUTION — why «gone from this coin» is not «gone»
--------------------------------------------------------
The unit that carries data through the pipeline is the SEED, and a merge
decision re-assigns seeds between classes (CLAUDE.md §9b: seed ids are the only
stable handle). When a seed changes class it takes its citations, weights and
catalogue indices with it: the old class shrinks, the new one grows, and the
project has lost nothing. Judged strictly per coin that reads as a loss on
every such move — which is how this tool first reported 56 «losses» for a
re-flow that, measured across the entity, dropped not one citation, not one
catalogue index (case-folded, as absorb folds them) and not one attested year.

So a dropped value blocks only when NOTHING in the entity attests it any more.
Values that merely changed owner are counted separately as `moved`, kept
visible in the summary rather than silently swallowed. Two normalisations are
likewise not losses: a `display: false` flip (absorb HIDES a surplus museum
citation, the citation stays) and a `year_ranges` de-overlap (the tuple
[1813,1813] folding into [1813,1815] loses the tuple, not the year).

Exit 0 = no losses. Exit 1 = at least one loss (the commit should not go out).

USAGE
-----
    .venv/bin/python scripts/maintenance/verify_reflow.py                # all entities
    .venv/bin/python scripts/maintenance/verify_reflow.py --entity danish_realm
    .venv/bin/python scripts/maintenance/verify_reflow.py --verbose      # list every changed coin
    .venv/bin/python scripts/maintenance/verify_reflow.py --base <ref>   # baseline other than HEAD
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_REL = "data/v2/final"
EXCLUSIONS_REL = "data/v2/exclusions"
UNIFIED_REL = "data/v2/seed_unified"
RETRACTED_REL = "data/v2/_retracted_refs.yml"
# Second ledger of the same shape, and separate for a mechanical reason:
# heal_hede_retracted_refs.py rewrites _retracted_refs.yml WHOLESALE, so a
# second author writing into that file would be silently wiped on the next
# heal run. This one records values a SOURCE-SANITY gate refused at parse.
SANITY_RETRACTED_REL = "data/v2/_source_sanity_retractions.yml"
RECORDED_REMOVALS_REL = "data/v2/_recorded_removals.yml"

# Fields whose disappearance or shrinkage is a real regression. `note` and the
# prose fields are excluded on purpose — they are curator-edited and a rewrite
# legitimately replaces them.
SCALAR_FIELDS = (
    "nominal", "ruler", "year_label", "year_first", "year_last",
    "mint", "metal", "kind", "fuss", "phase", "mintmaster",
)
LIST_FIELDS = ("sources", "weight_rough_g", "fineness", "diameter_mm", "year_ranges")

# Keys on a list entry that carry RENDER VISIBILITY, not data. `display: false`
# is set by absorb's `_suppress_weightless_museum_overcollection` to hide — not
# delete — surplus weightless KMM specimen citations; the citation stays in the
# YAML in full. Keying a list entry on the whole dict therefore reads a pure
# visibility flip as «lost 1, gained 1» and blocks a re-flow that lost nothing.
# (Observed 2026-08-02: km-82-chr-iv-1640 was reported as losing KMM 693125,
# which the very same file demonstrably still carried, one key richer.)
PRESENTATION_KEYS = frozenset({"display"})

# What makes one list entry THE SAME entry across the two sides, independent of
# its value. Keying an entry on its whole serialisation — which is what the
# set-difference below used to do — cannot tell a CORRECTED reading from a
# DROPPED one: both read as «one key vanished». On 2026-08-02 that reported
# km-82-chr-iv-1640 as losing a source and a weight while the coin had in fact
# gained both (sources 7 → 8, weights 6 → 7); one kmk specimen's weight had
# merely been corrected to 0.932. An entry whose IDENTITY is still present is a
# modification, never a loss — reported, but it does not block.
IDENTITY_KEYS: dict[str, tuple[str, ...]] = {
    "sources": ("url", "ref"),              # url; ref when the source has no url
    "weight_rough_g": ("source",),
    "fineness": ("source",),
    "diameter_mm": ("source",),
}


def _ident(field: str, v) -> str:
    """Identity of one list entry — what it IS, not what it says.

    Falls back to the full value key when the entry is not a dict or carries
    none of the field's identity keys: then content is all the identity there
    is, and the old strict behaviour applies.
    """
    if isinstance(v, dict):
        for k in IDENTITY_KEYS.get(field, ()):
            got = v.get(k)
            if got not in (None, ""):
                return f"{k}={got}"
    return _key(v)


def _git_show(ref: str, rel: str) -> dict | None:
    """Parse `<ref>:<rel>` as YAML; None when the path does not exist there."""
    r = subprocess.run(["git", "show", f"{ref}:{rel}"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return None
    return yaml.safe_load(io.StringIO(r.stdout)) or {}


def _coins(doc: dict | None) -> dict[str, dict]:
    return {c["id"]: c for c in (doc or {}).get("coins") or [] if c.get("id")}


def _urls(coin: dict) -> set[str]:
    return {s.get("url") for s in (coin.get("sources") or []) if isinstance(s, dict) and s.get("url")}


def _as_list(v) -> list:
    if v is None:
        return []
    return list(v) if isinstance(v, list) else [v]


def _key(v) -> str:
    """Identity of a value for set-difference purposes.

    Dict entries drop `PRESENTATION_KEYS` first, so a render-visibility flip is
    not mistaken for a dropped reading.
    """
    if isinstance(v, dict):
        v = {k: x for k, x in v.items() if k not in PRESENTATION_KEYS}
    return json.dumps(v, sort_keys=True, default=str)



def _is_span_refinement(old, new) -> bool:
    """One coarse range replaced by a finer enumeration within the SAME envelope.

    `[[1727, 1758]]` → `[[1727,1729],[1733,1733],[1758,1758]]` is a precision
    GAIN: the coarse span merely bounded the issue, the enumeration names the
    years actually struck. Returns False for anything else — in particular for a
    shrink of an already-discrete list, which stays a reportable loss.
    """
    def norm(v):
        out = []
        for r in (v or []):
            if isinstance(r, (list, tuple)) and len(r) == 2:
                try:
                    out.append((int(r[0]), int(r[1])))
                except (TypeError, ValueError):
                    return None
            else:
                return None
        return out
    o, n = norm(old), norm(new)
    if not o or not n or len(o) != 1 or len(n) <= 1:
        return False
    lo, hi = o[0]
    return (min(a for a, _ in n) == lo and max(b for _, b in n) == hi
            and all(lo <= a and b <= hi for a, b in n))

def _covered_years(ranges) -> set[str]:
    """Every individual year a `year_ranges` list attests, as comparable keys."""
    out: set[str] = set()
    for r in _as_list(ranges):
        try:
            lo, hi = int(r[0]), int(r[1])
        except (TypeError, ValueError, IndexError, KeyError):
            out.add(_key(r))
            continue
        if hi < lo:
            lo, hi = hi, lo
        out.update(str(y) for y in range(lo, hi + 1))
    return out


def _catalog_key(v) -> str:
    """Case-folded identity of one catalogue index value.

    Absorb's `_fold_catalog_indices` de-dups list-form catalogue values
    case-insensitively («Hede 55c» + «55C» → one «55C»). A case-sensitive
    comparison therefore reads that normalisation as a lost index: seed
    kmk-348205's Hede «75a» merging into unified-dk-hede-c5h75, which carries
    «75A», is the SAME index in the catalogue's own casing, not a loss.
    """
    return str(v).strip().upper()


def _catalog_registers(coin: dict) -> dict[str, set[str]]:
    """catalog → {register: {values}}, so a register losing a value is visible."""
    out: dict[str, set[str]] = {}
    for reg, val in (coin.get("catalog") or {}).items():
        out[reg] = {_catalog_key(x) for x in _as_list(val)}
    return out


def _relocated_ids(entity: str) -> set[str]:
    """Seed ids a cross-entity decision moves OUT of `entity`.

    `data/v2/merge_decisions/_cross_entity.yml` declares coins whose source
    seeds were bucketed into different entities. The merger pulls every member
    into `target_entity` and EXCLUDES them from their source entity — so from
    this file's per-entity vantage the coin simply vanishes, while globally
    nothing was lost: it is alive, whole, in another final.

    Without this the gate hard-blocks the very commit that records a legitimate
    cross-entity merge — the same failure mode `_excluded_ids` exists to avoid,
    and the same one the module docstring already notes for the dangling-
    `composed_of` sweep («cross-entity members live in other files, so it
    flagged six»).

    Returns the member seed ids of every decision whose `target_entity` is NOT
    `entity`; the caller matches them against the vanished coin's own id and its
    `composed_of`, exactly as it does for exclusions.
    """
    path = ROOT / "data/v2/merge_decisions/_cross_entity.yml"
    if not path.exists():
        return set()
    doc = yaml.safe_load(path.read_text()) or {}
    out: set[str] = set()
    for d in (doc.get("merges") or []):
        if d.get("target_entity") == entity:
            continue
        for m in (d.get("members") or []):
            out.add(m)
            out.add(f"unified-{m}")
    return out


def _excluded_ids(entity: str) -> set[str]:
    """Seed ids the curator has excluded for `entity` (data/v2/exclusions/).

    A curator exclusion is the one REMOVAL this project sanctions that is not a
    fold: the coin is deliberately dropped from the render with a recorded
    reason (§9 + PB-12), and by construction no survivor absorbs it. Without
    this the gate reports every exclusion as data falling on the floor and hard-
    blocks the very commit that records the decision — which is how the check
    would teach people to reach for --no-verify.
    """
    path = ROOT / EXCLUSIONS_REL / f"{entity}.yml"
    if not path.exists():
        return set()
    doc = yaml.safe_load(path.read_text()) or {}
    raw = {e["id"] for e in (doc.get("exclusions") or []) if e.get("id")}
    if not raw:
        return set()

    # An exclusion names a SEED id; a final's `composed_of` names the UNIFIED
    # classes it was built from. Bridge the two through seed_unified, which is
    # the only place that maps a unified class to its member seeds — the
    # `unified-<head member>` naming is a convention, not something to parse.
    seed_ids = set(raw)
    unified_path = ROOT / UNIFIED_REL / f"{entity}.yml"
    if unified_path.exists():
        udoc = yaml.safe_load(unified_path.read_text()) or {}
        for c in udoc.get("coins") or []:
            if c.get("id") and raw & set(c.get("composed_of") or []):
                raw.add(c["id"])

    # A FOUNDATION-only final (a V1-bootstrap coin the V2 merger never re-derived
    # — e.g. a non-coin the merger's scope filter drops) carries NO seed_unified
    # entry to bridge through, so the loop above cannot reach it. But the absorber
    # matches such a coin's exclusion on the `unified-<seed id>` naming directly
    # (see data/v2/exclusions header: «dropped when its own unified id … resolves
    # to a listed id»), and drops it correctly. Mirror that convention here so the
    # deliberate drop is recognised, not hard-blocked as a phantom loss.
    raw |= {f"unified-{sid}" for sid in seed_ids}
    return raw


def _retracted_refs(entity: str) -> dict[str, set[str]]:
    """{field: {value identities}} the parser retracted, for coins of `entity`.

    Covers TWO shapes, because a parser withdraws two kinds of thing:
      * a catalogue register value — «KM 82» — matched case-insensitively;
      * a whole measurement-list entry — «{source: ngc, value: 35.5}» — matched
        on the same identity the list comparison uses, so the excuse is exact.

    Third member of the same family as the curator exclusions above: a removal
    that is deliberate, recorded, and invisible to a gate that only sees a
    register shrink. `catalog` is deep-merged and accumulates, so a parser fix
    that stops emitting a wrong value cannot remove it — only a heal can, and
    the heal is what makes the register shrink.

    Written by heal_hede_retracted_refs.py into data/v2/_retracted_refs.yml.
    Keyed by SEED id there; resolved to the coins that carry it here, the same
    way `_excluded_ids` bridges seed → unified.
    """
    entries = []
    for rel in (RETRACTED_REL, SANITY_RETRACTED_REL, RECORDED_REMOVALS_REL):
        path = ROOT / rel
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text()) or {}
        # `_recorded_removals.yml` keys its list `removals` and marks each entry
        # with a `kind`; only its field removals belong here (a `thinning` entry
        # excuses a whole coin and is handled in the vanished branch). The two
        # machine-written ledgers key theirs `retractions` and carry no `kind`.
        entries += (doc.get("retractions") or [])
        entries += [e for e in (doc.get("removals") or [])
                    if isinstance(e, dict) and e.get("kind") == "field"]
    if not entries:
        return {}
    by_seed: dict[str, dict[str, set[str]]] = {}
    for e in entries:
        if e.get("seed") and e.get("field"):
            # A catalogue register drops bare strings («KM 82»); a measurement
            # list drops whole entries («{source: ngc, value: 35.5}»). Key the
            # dict form through _key so it matches the very identity the
            # list-field comparison below builds, instead of a str() of a dict.
            by_seed.setdefault(e["seed"], {}).setdefault(e["field"], set()).update(
                _key(v) if isinstance(v, dict) else str(v)
                for v in (e.get("dropped") or []))
    if not by_seed:
        return {}
    # Which of those seeds live in THIS entity, and under which class.
    unified_path = ROOT / UNIFIED_REL / f"{entity}.yml"
    if not unified_path.exists():
        return {}
    out: dict[str, set[str]] = {}
    for c in (yaml.safe_load(unified_path.read_text()) or {}).get("coins") or []:
        for m in c.get("composed_of") or []:
            for field, vals in by_seed.get(m, {}).items():
                out.setdefault(field, set()).update(vals)
    return out


_RELOCATION_INDEX: dict[str, set[str]] | None = None


def _cross_entity_targets() -> list[str]:
    """Entities that a cross-entity merge can RELOCATE a coin INTO.

    `data/v2/merge_decisions/_cross_entity.yml` is the only sanctioned way a
    coin — and with it every reading and citation it carries — leaves one
    entity file for another. Its `target_entity` values are therefore the
    complete set of destinations, and today a small one (4 of 22 entities).
    """
    path = ROOT / "data/v2/merge_decisions/_cross_entity.yml"
    if not path.exists():
        return []
    doc = yaml.safe_load(path.read_text()) or {}
    return sorted({m.get("target_entity") for m in (doc.get("merges") or [])
                   if m.get("target_entity")})


def _relocation_attestation_index() -> dict[str, set[str]]:
    """What the cross-entity RELOCATION TARGETS attest, in the working tree.

    `_attestation_index` answers «is this still attested anywhere?» — but it is
    built from ONE entity file, so «anywhere» stops at the entity boundary. A
    cross-entity merge walks a coin straight across that boundary: the value is
    alive and well in the target's final, and the source entity's comparison,
    unable to see it, reports a loss. Every such merge would need --no-verify.

    So the source side additionally consults the destinations. Scoped to the
    declared `target_entity` set rather than every final: a value that vanished
    from one entity is excused only where the relocation mechanism could
    actually have put it, so an unrelated coin in an unrelated entity that
    happens to carry the same reading still cannot launder a real loss.

    Cached — the same handful of files would otherwise be re-read per entity.
    """
    global _RELOCATION_INDEX
    if _RELOCATION_INDEX is None:
        idx: dict[str, set[str]] = {f: set() for f in LIST_FIELDS}
        idx["catalog"] = set()
        for ent in _cross_entity_targets():
            path = ROOT / f"{FINAL_REL}/{ent}.yml"
            if not path.exists():
                continue
            for f, vals in _attestation_index(
                    _coins(yaml.safe_load(path.read_text()))).items():
                idx.setdefault(f, set()).update(vals)
        _RELOCATION_INDEX = idx
    return _RELOCATION_INDEX


def compare_entity(entity: str, base: str) -> dict:
    """Load both sides for `entity` and delegate to `compare_coins`."""
    rel = f"{FINAL_REL}/{entity}.yml"
    head = _coins(_git_show(base, rel))
    path = ROOT / rel
    cur = _coins(yaml.safe_load(path.read_text()) if path.exists() else None)
    return compare_coins(entity, head, cur, excluded=_excluded_ids(entity),
                         retracted=_retracted_refs(entity),
                         elsewhere=_relocation_attestation_index(),
                         head_members=_head_unified_members(base))


_ELSEWHERE_COINS: dict[str, tuple[str, str]] | None = None


_HEAD_UNIFIED: dict[str, dict[str, list[str]]] = {}


_RECORDED_REMOVALS: tuple[set[str], dict[str, set[str]]] | None = None


def _recorded_removals() -> tuple[set[str], dict[str, set[str]]]:
    """(seeds thinned away, {field: seeds whose value was removed}).

    Third member of the family that already holds `data/v2/exclusions/` for
    coins, `_retracted_refs.yml` for catalogue registers and
    `_source_sanity_retractions.yml` for refused readings: a removal that is
    deliberate and recorded, and that the gate would otherwise be unable to
    tell from data falling on the floor.

    Two shapes, because two legitimate operations leave a loss signature:
    §9a thinning drops a redundant museum specimen, taking with it any final
    that specimen alone backed; and a manual field clearance removes a value
    the finals had ACCUMULATED, which no re-flow can undo because
    `_collect_mints` feeds a final's own stored value back in as a member.

    Keyed by SEED id (§9b), resolved to the coins that carry it by the caller,
    exactly as `_excluded_ids` and `_retracted_refs` are.
    """
    global _RECORDED_REMOVALS
    if _RECORDED_REMOVALS is None:
        thinned: set[str] = set()
        fields: dict[str, set[str]] = {}
        path = ROOT / RECORDED_REMOVALS_REL
        if path.exists():
            for e in (yaml.safe_load(path.read_text()) or {}).get("removals") or []:
                seed = e.get("seed")
                if not seed:
                    continue
                if e.get("kind") == "thinning":
                    thinned.add(seed)
                elif e.get("kind") == "field" and e.get("field"):
                    fields.setdefault(e["field"], set()).add(seed)
        _RECORDED_REMOVALS = (thinned, fields)
    return _RECORDED_REMOVALS


def _head_unified_members(base: str) -> dict[str, list[str]]:
    """{unified id → its seed members} as of the BASELINE commit.

    The vanished final is described by the baseline, so its members must be
    resolved against the baseline's seed_unified, not the working tree's —
    the working tree may have renamed or dissolved that very class.
    """
    if base not in _HEAD_UNIFIED:
        out: dict[str, list[str]] = {}
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", base, "data/v2/seed_unified/"],
            capture_output=True, text=True, cwd=ROOT).stdout.split()
        for rel in listing:
            for uid, u in _coins(_git_show(base, rel)).items():
                out[uid] = list(u.get("composed_of") or [])
        _HEAD_UNIFIED[base] = out
    return _HEAD_UNIFIED[base]


def _coin_home_index() -> dict[str, tuple[str, str]]:
    """{id seen in some final → (entity, that final's id)} across EVERY entity.

    `_relocation_attestation_index` answers the same question one layer down —
    "is this VALUE still attested somewhere the relocation mechanism could have
    put it?" — but only for coins moved by a declared `_cross_entity.yml`
    decision. A coin can also cross the boundary without any decision at all:
    `issuing_entity` is derived from the mint, so the moment a mint the
    pipeline could not read becomes readable, the classifier routes the coin to
    a different entity and its final is written to a different file. From this
    file's per-entity vantage the coin simply vanishes — the exact wording the
    `_relocated_ids` docstring already uses — while globally it is alive, whole,
    and better placed than before.

    Observed 2026-08-21: making `Kongsborg` resolve to Kongsberg moved 118
    seeds from danish_realm to danish_norway, where 50 of them stopped being
    `seed_unsorted` and merged into their Hede types. The gate reported 65
    coins gone and hard-blocked the commit that improved them.

    Indexes both a final's own id and every id in its `composed_of`, because
    the vanished side is keyed by a unified id while the survivor may name it
    as a member. This is an IDENTITY test, not a value test: a coin that is
    genuinely gone appears in no final anywhere, so unlike a value-based
    excuse this one cannot launder a real loss.
    """
    global _ELSEWHERE_COINS
    if _ELSEWHERE_COINS is None:
        idx: dict[str, tuple[str, str]] = {}
        # A final's `composed_of` names UNIFIED ids, so the index has to walk
        # one layer further to reach the seed ids — the only stable handle
        # (§9b). Without that step a coin whose seed joined a DIFFERENT class
        # in the new entity is invisible here: the old unified id is gone and
        # the new final never mentions it.
        unified: dict[str, list[str]] = {}
        for path in sorted((ROOT / "data/v2/seed_unified").glob("*.yml")):
            for uid, u in _coins(yaml.safe_load(path.read_text())).items():
                unified[uid] = list(u.get("composed_of") or [])
        for path in sorted((ROOT / FINAL_REL).glob("*.yml")):
            ent = path.stem
            for cid, coin in _coins(yaml.safe_load(path.read_text())).items():
                idx.setdefault(cid, (ent, cid))
                for m in (coin.get("composed_of") or [cid]):
                    idx.setdefault(m, (ent, cid))
                    for seed in unified.get(m, []):
                        idx.setdefault(seed, (ent, cid))
        _ELSEWHERE_COINS = idx
    return _ELSEWHERE_COINS


def _attestation_index(coins: dict[str, dict]) -> dict[str, set[str]]:
    """Every value the entity still attests, per comparison dimension.

    A re-flow moves MEMBERS between classes, and a member takes its readings
    with it: when a seed leaves `unified-kmk-131360` for another class, that
    class's `year_ranges` shrink and the destination's grow. Judged per coin
    that reads as a loss; judged across the entity nothing was lost at all.
    Since the members that move live a layer below `final` (inside a
    seed_unified class that can shrink while the final's own `composed_of` is
    unchanged), the final layer cannot attribute the move to a destination —
    so retention is measured entity-wide, which is the question the gate
    actually asks: is anything no longer attested anywhere?
    """
    idx: dict[str, set[str]] = {f: set() for f in LIST_FIELDS}
    idx["catalog"] = set()
    for coin in coins.values():
        for f in LIST_FIELDS:
            if f == "year_ranges":
                idx[f] |= _covered_years(coin.get(f))
            else:
                idx[f] |= {_key(x) for x in _as_list(coin.get(f))}
        for reg, vals in _catalog_registers(coin).items():
            idx["catalog"] |= {f"{reg}={v}" for v in vals}
    return idx


def compare_coins(entity: str, head: dict[str, dict], cur: dict[str, dict],
                  excluded: set[str] | frozenset = frozenset(),
                  retracted: dict[str, set[str]] | None = None,
                  elsewhere: dict[str, set[str]] | None = None,
                  head_members: dict[str, list[str]] | None = None) -> dict:
    """Classify every difference between two {id: coin} maps as gain or loss.

    Split out from the loading so the classification — the part with judgement
    in it — is directly testable without a git tree or a filesystem.

    `excluded` carries the curator's exclusion ids for this entity; a coin that
    vanished because one of them names it is a recorded decision, not a loss.
    `retracted` carries {register: values} the parser withdrew and a heal then
    removed — same idea, one level down: a recorded removal INSIDE a coin.
    `elsewhere` carries what the cross-entity relocation TARGETS attest, so a
    value that left this entity by the one mechanism that moves coins between
    entity files is not reported as lost (see _relocation_attestation_index).
    """
    retracted = retracted or {}
    losses: list[str] = []
    dropped: list[str] = []
    retractions: list[str] = []
    gains: list[str] = []
    changed: dict[str, dict] = {}
    changes: list[str] = []
    moved_only = 0
    attested = _attestation_index(cur)
    for f, vals in (elsewhere or {}).items():
        attested.setdefault(f, set()).update(vals)

    # --- coins that vanished -------------------------------------------------
    # A vanished coin is fine ONLY if a survivor absorbed it: either it is named
    # in a survivor's composed_of, or a survivor carries all of its source URLs.
    # That is exactly the dedup_final_foundations fold, and exactly what makes a
    # deliberate dedup distinguishable from data quietly falling on the floor.
    for cid in sorted(set(head) - set(cur)):
        was = head[cid]
        # A curator exclusion removes the coin ON PURPOSE, with a recorded
        # reason, and nothing absorbs it. Match on the vanished id itself or on
        # any of its members, since an exclusion names a SEED id (§9b) while the
        # final that disappears is keyed by its unified id.
        hit = ({cid} | set(was.get("composed_of") or [])) & set(excluded)
        if hit:
            dropped.append(f"{cid} ({was.get('nominal')} {was.get('year_label')}) "
                           f"— curator exclusion: {', '.join(sorted(hit))}")
            continue
        # A cross-entity merge moves the coin to another entity's final. It is
        # gone from THIS file and alive in that one; per-entity differencing
        # cannot see the survivor, so consult the decision that moved it.
        moved = ({cid} | set(was.get("composed_of") or [])) & _relocated_ids(entity)
        if moved:
            dropped.append(f"{cid} ({was.get('nominal')} {was.get('year_label')}) "
                           f"— cross-entity merge: {', '.join(sorted(moved))}")
            continue
        # A §9a thinning dropped the seed this final was standing on. Recorded
        # in `_recorded_removals.yml` with the surviving bucket members, since
        # the drop is invisible here: the final simply has nothing left to
        # stand on.
        thinned, _ = _recorded_removals()
        probe_seeds = [cid, *(was.get("composed_of") or [])]
        probe_seeds += [x for m in list(probe_seeds)
                        for x in (head_members or {}).get(m, [])]
        thin_hit = sorted(set(probe_seeds) & thinned)
        if thin_hit:
            dropped.append(f"{cid} ({was.get('nominal')} {was.get('year_label')}) "
                           f"— §9a thinning: {', '.join(thin_hit)}")
            continue
        # Routing-driven relocation: the coin left this entity because its
        # derived `issuing_entity` changed, with no decision file to consult.
        # Same phenomenon as the cross-entity merge above, different trigger.
        home = _coin_home_index()
        probes = [cid, *(was.get("composed_of") or [])]
        probes += [s for m in list(probes)
                   for s in (head_members or {}).get(m, [])]
        elsewhere_hit = next(
            ((m, home[m]) for m in probes
             if m in home and home[m][0] != entity), None)
        if elsewhere_hit is not None:
            member, (ent, host) = elsewhere_hit
            dropped.append(f"{cid} ({was.get('nominal')} {was.get('year_label')}) "
                           f"— relocated to {ent} as {host}"
                           + (f" (via {member})" if member != cid else ""))
            continue
        absorbed_by = None
        for sid, sc in cur.items():
            if cid in (sc.get("composed_of") or []):
                absorbed_by = sid
                break
            u = _urls(was)
            if u and u <= _urls(sc):
                absorbed_by = sid
                break
        if absorbed_by is None:
            # REDISTRIBUTION. A merge decision can DISSOLVE a class rather than
            # fold it whole: when the seeds of a `unified-*` foundation join
            # different new classes, each survivor receives only its share, so
            # no single survivor is a superset and the two tests above both
            # miss. That is not data falling on the floor — every citation is
            # still cited, just by more than one coin. Accept it only when the
            # survivors COVER the URL set completely; any URL that no survivor
            # carries is a real loss and still reports.
            # (Observed 2026-08-02: unified-kmk-155180's 13 KMM citations split
            # 6/7 between km-x005-chr-iv-1620 and km-82-chr-iv-1640 after the
            # abstain fix legitimately unblocked the merges.)
            want = _urls(was)
            if want:
                carriers = sorted(
                    sid for sid, sc in cur.items() if want & _urls(sc)
                )
                covered: set[str] = set()
                for sid in carriers:
                    covered |= _urls(cur[sid]) & want
                if covered == want:
                    absorbed_by = ", ".join(carriers)
        if absorbed_by:
            gains.append(f"{cid} folded into {absorbed_by}")
        else:
            losses.append(f"COIN GONE  {cid} ({was.get('nominal')} {was.get('year_label')}) "
                          f"— no survivor lists it in composed_of and none carries its sources")

    for cid in sorted(set(cur) - set(head)):
        gains.append(f"{cid} new")

    # --- field-level ---------------------------------------------------------
    for cid in sorted(set(head) & set(cur)):
        h, c = head[cid], cur[cid]
        moved: dict[str, tuple] = {}

        for f in SCALAR_FIELDS:
            hv, cv = h.get(f), c.get(f)
            if _key(hv) == _key(cv):
                continue
            moved[f] = (hv, cv)
            if hv not in (None, "", []) and cv in (None, "", []):
                # A recorded field removal is the scalar twin of a parser
                # retraction: the value is gone on purpose and the ledger names
                # exactly which field of which seed it was.
                _, field_removals = _recorded_removals()
                seeds_here = [cid, *(c.get("composed_of") or [])]
                seeds_here += [x for m in list(seeds_here)
                               for x in (head_members or {}).get(m, [])]
                if set(seeds_here) & field_removals.get(f, set()):
                    retractions.append(f"{cid}.{f}: {hv!r} (recorded removal)")
                    continue
                losses.append(f"FIELD EMPTIED  {cid}.{f}: {hv!r} → empty")
            elif f in ("fuss", "phase") and cv == "seed_unsorted":
                losses.append(f"DEMOTED  {cid}.{f}: {hv!r} → seed_unsorted")

        for f in LIST_FIELDS:
            if f == "year_ranges":
                # Compare COVERED YEARS, not range tuples. The merger unions and
                # de-overlaps ranges across members (D19), so [1813,1813] joining
                # a class that also attests 1814-1815 legitimately re-shapes into
                # [1813,1815]: the tuple is gone, the year is not. Only a year
                # that nothing attests any more is a loss.
                hl = _covered_years(h.get(f))
                cl = _covered_years(c.get(f))
            else:
                hl = {_key(x) for x in _as_list(h.get(f))}
                cl = {_key(x) for x in _as_list(c.get(f))}
            if hl == cl:
                continue
            if f == "year_ranges" and _is_span_refinement(h.get(f), c.get(f)):
                # A single COARSE span replaced by a discrete enumeration inside
                # the same envelope is the accumulation principle working as
                # designed («the richer breakdown wins», CLAUDE.md
                # §Data-accumulation): ucoin publishes «1727-1758», NGC's date
                # table publishes the actual 1727/1728/1729/1733/1758. The
                # covered-years set shrinks because the coarse span IMPLIED
                # years nobody ever struck — dropping those is a gain in
                # precision, not a loss of attestation.
                # Deliberately narrow: only fires when the old side was ONE
                # range, the new side has strictly more, every new range sits
                # inside the old one, and the outer envelope is identical. A
                # shrink of an already-discrete list is untouched and still
                # reported.
                continue
            moved[f] = (len(hl), len(cl))
            dropped = hl - cl
            if dropped:
                if f == "year_ranges":
                    modified: set[str] = set()
                else:
                    # An entry whose identity is still here in the same number
                    # only had its VALUE corrected — a modification, not a loss.
                    hi = Counter(_ident(f, x) for x in _as_list(h.get(f)))
                    ci = Counter(_ident(f, x) for x in _as_list(c.get(f)))
                    ident_of = {_key(x): _ident(f, x) for x in _as_list(h.get(f))}
                    modified = {k for k in dropped
                                if ci[ident_of.get(k, k)] >= hi[ident_of.get(k, k)]}
                    for k in sorted(modified):
                        changes.append(
                            f"{cid}.{f}: value changed under {ident_of.get(k, k)[:60]}")
                gone = (dropped - modified) - attested[f]
                # A reading the parser REFUSED is a recorded removal, not a
                # loss. This is the measurement-list twin of the catalog branch
                # below: a source-sanity gate (parse_ngc.sift_fineness) declines
                # a value the source printed but that cannot be what it claims,
                # the ledger records exactly which value of exactly which field
                # on exactly which seed, and only that one is excused. Anything
                # else in the same shrink still blocks — a ledger entry can
                # never become a blanket amnesty for the coin or the field.
                excused = gone & retracted.get(f, set())
                if excused:
                    retractions.extend(
                        f"{cid}.{f}: {v[:70]} (parser retraction)"
                        for v in sorted(excused))
                    gone -= excused
                if gone:
                    losses.append(f"LIST SHRANK  {cid}.{f}: lost {len(gone)} "
                                  f"({sorted(gone)[0][:70]}…)")
                elif dropped - modified:
                    moved_only += 1

        hcat, ccat = _catalog_registers(h), _catalog_registers(c)
        for reg in sorted(set(hcat) | set(ccat)):
            hv, cv = hcat.get(reg, set()), ccat.get(reg, set())
            if hv == cv:
                continue
            moved.setdefault("catalog", []).append(reg)
            dropped = hv - cv
            if dropped:
                # A truncated index replaced by the RANGE the source actually
                # prints is a refinement, not a loss: «MB 569» becomes «MB
                # 569-570», «Lange 759» becomes «759-762». The old value is the
                # head of the new one and is strictly contained in it. Same
                # reasoning as `_is_span_refinement` above for year_ranges — a
                # coarse value replaced by a more exact one inside the same
                # envelope is the accumulation principle working, and it must
                # not read as a shrink.
                #
                # Deliberately narrow: only a value that is the literal head of
                # a NEW value in the SAME register, separated by «-». A value
                # that merely disappears, or is a substring somewhere in the
                # middle, still blocks.
                _refined = {v for v in dropped
                            if any(n.startswith(f"{v}-") for n in (cv - hv))}
                dropped = dropped - _refined
                if _refined:
                    changes.extend(
                        f"{cid}.catalog.{reg}: {v} refined to the printed range"
                        for v in sorted(_refined))
                if not dropped:
                    continue
                gone = {v for v in dropped if f"{reg}={v}" not in attested["catalog"]}
                # A value the parser retracted is a recorded removal, not a
                # loss — but ONLY that value of ONLY that register. Anything
                # else in the same shrink still blocks, so a ledger entry can
                # never turn into a blanket amnesty for the coin.
                excused = {v for v in gone if v.upper() in
                           {x.upper() for x in retracted.get(reg, set())}}
                if excused:
                    retractions.extend(
                        f"{cid}.catalog.{reg}: {v} (parser retraction)"
                        for v in sorted(excused))
                    gone -= excused
                if gone:
                    losses.append(
                        f"CATALOG SHRANK  {cid}.catalog.{reg}: lost {sorted(gone)}")
                else:
                    moved_only += 1

        if moved:
            changed[cid] = moved

    return {
        "entity": entity, "head": len(head), "cur": len(cur),
        "changed": changed, "losses": losses, "gains": gains,
        "moved": moved_only, "changes": changes, "dropped": dropped,
        "retractions": retractions,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entity", help="single entity (default: every final yaml)")
    ap.add_argument("--base", default="HEAD", help="baseline git ref (default: HEAD)")
    ap.add_argument("--verbose", action="store_true", help="list every changed coin")
    args = ap.parse_args()

    final_dir = ROOT / FINAL_REL
    entities = ([args.entity] if args.entity
                else sorted(p.stem for p in final_dir.glob("*.yml")))

    total_loss: list[str] = []
    total_dropped: list[str] = []
    total_retractions: list[str] = []
    total_changed = total_gain = total_moved = 0
    total_changes: list[str] = []
    print(f"===== verify_reflow — working tree vs {args.base} =====\n")

    for ent in entities:
        r = compare_entity(ent, args.base)
        if not (r["changed"] or r["losses"] or r["gains"] or r.get("dropped")):
            continue
        total_changed += len(r["changed"])
        total_gain += len(r["gains"])
        total_loss += [f"[{ent}] {m}" for m in r["losses"]]
        total_dropped += [f"[{ent}] {m}" for m in r.get("dropped") or []]
        total_retractions += [f"[{ent}] {m}" for m in r.get("retractions") or []]
        total_moved += r["moved"]
        total_changes += [f"[{ent}] {m}" for m in r.get("changes") or []]
        flag = "✗" if r["losses"] else "✓"
        print(f"{flag} {ent:38} coins {r['head']} → {r['cur']}   "
              f"changed {len(r['changed'])}   gains {len(r['gains'])}   "
              f"losses {len(r['losses'])}"
              + (f"   excluded {len(r['dropped'])}" if r.get("dropped") else "")
              + (f"   moved {r['moved']}" if r["moved"] else ""))
        if args.verbose:
            for cid, moved in r["changed"].items():
                print(f"      {cid}: {', '.join(sorted(moved))}")
            for g in r["gains"]:
                print(f"      + {g}")

    print(f"\nchanged coins: {total_changed}   gains: {total_gain}   "
          f"losses: {len(total_loss)}   moved: {total_moved}")
    if total_moved:
        print("  (moved = a value that left one coin and is still attested by "
              "another — a member changed class, not a loss)")

    if total_retractions:
        # Deliberate, recorded removals INSIDE a coin — printed so the gate
        # still shows what left, without failing on it.
        print(f"\n----- PARSER RETRACTIONS ({len(total_retractions)}) — not losses -----")
        for m in total_retractions:
            print(f"  {m}")

    if total_dropped:
        # Deliberate removals, printed so the gate still SHOWS what left the
        # render even though it does not block on it.
        print(f"\n----- CURATOR EXCLUSIONS ({len(total_dropped)}) — not losses -----")
        for m in total_dropped:
            print(f"  {m}")

    if total_changes:
        # Not a loss — the entry is still here, its reading was corrected. Worth
        # SEEING all the same: a measurement that silently changed value is the
        # kind of thing a re-flow should be deliberate about.
        print(f"\n----- CHANGED VALUES ({len(total_changes)}) — not losses -----")
        for m in total_changes:
            print(f"  {m}")

    if total_loss:
        print("\n----- LOSSES -----")
        for m in total_loss:
            print(f"  {m}")
        print("\nThe working tree is WORSE than the baseline on the lines above.")
        print("Fix them, or — if a removal is deliberate — make it a recognised")
        print("fold: the survivor must list the removed id in composed_of")
        print("(dedup_final_foundations.py does this).")
        return 1

    print("\n✓ no losses — every change is an addition or a recognised fold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
