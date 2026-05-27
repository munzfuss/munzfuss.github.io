"""Seed docs/anomaly_log.yml from historic handoff records.

One-shot: walks `scripts/cache/_harvest_handoff.json::runs[].anomalies[]`,
classifies each historic record by hand-encoded rules into one or more stable
ids, and emits them via `anomaly_log.record()`.

Idempotent — re-running is safe because `record()`'s match-or-create logic
on stable id absorbs repeat calls into the existing active entry's
`occurrences[]` list. (It will inflate `occurrence_count` on re-run, so don't
run twice unless you mean to. The output before-vs-after counts make this
obvious.)

Classification rules (hand-written based on inspection of all 11 records as
of 2026-05-27 batch FO/177/W):

  - IKMK QUERIES false-positives → one entry per query name (Hamburg /
    Kassel / Hessen / Lübeck / Christian V. / Christian VI. / Christian VIII. /
    Friedrich VI. / Iburg). When a historic record mentions multiple queries
    in the same anomaly, that record's occurrence gets RECORDED on each
    relevant query's entry.

  - ucoin BR-4 bucket scope/label issues → per-bucket distinct entries:
      `audit_manifest_scope_drift:ucoin:bucket=osnabruck_p3057` (pre-mission
        gap TIDs)
      `audit_manifest_label_mismatch:ucoin:bucket=osnabruck_p2988` (Hochstift
        vs City label)
      `audit_manifest_period_boundary:ucoin:bucket=osnabruck_p2988:tid=N`
        (per-TID date-bound violation, one entry per TID)

  - Transient anomalies (cloudflare_challenge_persistent) → SKIPPED. Per
    docs/ANOMALY_LOG.md transient rule: auto-resolved-in-same-run incidents
    stay in handoff snapshots, do not promote to persistent log.

  - Mistyped originals (`doc_update_pending` records #4 + #5 were really
    scope-drift cases) → re-classified to `audit_manifest_scope_drift`.

  - `_failed_open_ids.json` walker (separate from handoff walk): for each
    historic entry, check if the source's `<id>.json` cache file exists. If
    YES, skip — the failure was resolved by a subsequent successful fetch.
    If NO, emit `url_open_failed:source=X:id=Y` entry (one per still-broken
    ID; multiple historic occurrences for same ID fold into one log entry's
    `occurrences[]` list).

Run: `python scripts/maintenance/backfill_anomaly_log.py`
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# Allow running as a script from anywhere
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import anomaly_log as al


def _extract_mds_ids(text: str) -> list[int]:
    """Pull 8-digit IKMK mds_ids out of free text."""
    return [int(m) for m in re.findall(r"\b18\d{6}\b", text)]


def _extract_tids(text: str) -> list[int]:
    """Pull 6-digit ucoin TIDs out of free text. Filter to plausible range."""
    found = [int(m) for m in re.findall(r"\b1[67]\d{4}\b", text)]
    return [t for t in found if 160000 <= t < 200000]


# ---------------------------------------------------------------------------
# Hand-classified entries: list of (historic_record_predicate, emit_fn).
#
# Each emit_fn takes the historic record dict (with extra `_run_utc` +
# `_batch_label` fields) and calls al.record(...) one or more times.

CLASSIFIERS: list = []


def _classifier(pred):
    def deco(fn):
        CLASSIFIERS.append((pred, fn))
        return fn
    return deco


# -----------------------------------------------------------
# IKMK QUERIES false-positives — split by query name.

IKMK_QUERY_PATTERNS = [
    ("Hamburg", "hamburg", r"\bHamburg\b"),
    ("Kassel", "kassel", r"\bKassel\b"),
    ("Hessen", "hessen", r"\bHessen\b"),
    ("Lübeck", "lubeck", r"\bL(?:ü|u)beck\b"),
    ("Christian V.", "christian_v", r"\bChristian V\.(?!I)"),
    ("Christian VI.", "christian_vi", r"\bChristian VI\.(?!I)"),
    ("Christian VIII.", "christian_viii", r"\bChristian VIII\.\B"),
    ("Friedrich VI.", "friedrich_vi", r"\bFriedrich VI\."),
    ("Iburg", "iburg", r"\bIburg\b"),
]


@_classifier(lambda r: "IKMK" in r.get("detail", "") and any(
    re.search(pat, r["detail"]) for _, _, pat in IKMK_QUERY_PATTERNS
))
def emit_ikmk_query_drift(record: dict) -> int:
    """Emit one record() call per IKMK query name mentioned in detail."""
    detail = record["detail"]
    mds_ids = _extract_mds_ids(detail)
    follow_up = record.get("follow_up") or ""
    action_taken = record.get("action_taken") or ""
    n_emitted = 0
    for display_name, slug, pat in IKMK_QUERY_PATTERNS:
        if re.search(pat, detail):
            al.record(
                type_="audit_manifest_scope_drift",
                key_dims={"source": "ikmk", "query": slug},
                summary=(
                    f"IKMK discover query «{display_name}» returns OOS records "
                    f"(fuzzy-search false-positives outside mission scope)."
                ),
                detail=detail,
                affected_ids={"ikmk": mds_ids} if mds_ids else None,
                proposed_fix=follow_up,
                batch_label=record.get("_batch_label"),
                run_utc=record.get("_run_utc"),
                full_context={
                    "action_taken": action_taken,
                    "ikmk_batch": record.get("_ikmk_batch"),
                    "numista_batch": record.get("_numista_batch"),
                    "ucoin_batch": record.get("_ucoin_batch"),
                },
            )
            n_emitted += 1
    return n_emitted


# -----------------------------------------------------------
# IKMK manifest sequential-walk OOS (when no specific query named, just
# «broad text queries» or «manifest sequential walk» — generic complaint).

@_classifier(lambda r: "IKMK" in r.get("detail", "") and (
    "broad text queries" in r["detail"].lower()
    or "manifest sequential walk" in r["detail"].lower()
    or "fuzzy-search" in r["detail"].lower()
) and not any(re.search(p, r["detail"]) for _, _, p in IKMK_QUERY_PATTERNS))
def emit_ikmk_generic_drift(record: dict) -> int:
    """Catch-all for IKMK records that complain about scope drift without
    naming a specific QUERIES entry."""
    detail = record["detail"]
    mds_ids = _extract_mds_ids(detail)
    al.record(
        type_="audit_manifest_scope_drift",
        key_dims={"source": "ikmk", "scope": "queries_broad_general"},
        summary=(
            "IKMK broad-text discover queries (multiple) collectively return "
            "OOS records (ancient + medieval + post-1914 commemoratives). "
            "Generic class — see per-query entries for specific cases."
        ),
        detail=detail,
        affected_ids={"ikmk": mds_ids} if mds_ids else None,
        proposed_fix=record.get("follow_up"),
        batch_label=record.get("_batch_label"),
        run_utc=record.get("_run_utc"),
        full_context={"action_taken": record.get("action_taken")},
    )
    return 1


# -----------------------------------------------------------
# ucoin bucket-level scope drift (osnabruck_p3057 pre-mission TIDs).

@_classifier(lambda r: "osnabruck_p3057" in r.get("detail", ""))
def emit_ucoin_p3057_scope_drift(record: dict) -> int:
    detail = record["detail"]
    tids = _extract_tids(detail)
    al.record(
        type_="audit_manifest_scope_drift",
        key_dims={"source": "ucoin", "bucket": "osnabruck_p3057"},
        summary=(
            "ucoin BR-4 bucket osnabruck_p3057 (Bishopric of Osnabrück "
            "1482-1661) spans pre-mission years; first gap TIDs are pre-1559 "
            "and audit-4 did not filter to mission window."
        ),
        detail=detail,
        affected_ids={"ucoin": tids} if tids else None,
        proposed_fix=record.get("follow_up"),
        batch_label=record.get("_batch_label"),
        run_utc=record.get("_run_utc"),
        full_context={"action_taken": record.get("action_taken")},
    )
    return 1


# -----------------------------------------------------------
# ucoin osnabruck_p2988 label mismatch (Hochstift vs City).

@_classifier(lambda r: "osnabruck_p2988" in r.get("detail", "") and (
    "Hochstift" in r["detail"] or "City of Osnabrück" in r["detail"]
) and "label" not in r["detail"].lower() or
    ("osnabruck_p2988" in r.get("detail", "") and "Hochstift" in r.get("detail", "") and "City" in r.get("detail", "")))
def emit_ucoin_p2988_label_mismatch(record: dict) -> int:
    detail = record["detail"]
    al.record(
        type_="audit_manifest_label_mismatch",
        key_dims={"source": "ucoin", "bucket": "osnabruck_p2988"},
        summary=(
            "ucoin BR-4 bucket osnabruck_p2988 carries label «Osnabrück "
            "Hochstift» but ucoin's own period title reads «City of Osnabrück "
            "(1586-1805)»; fetched TIDs are city issues not Hochstift."
        ),
        detail=detail,
        affected_ids=None,
        proposed_fix=record.get("follow_up"),
        batch_label=record.get("_batch_label"),
        run_utc=record.get("_run_utc"),
        full_context={"action_taken": record.get("action_taken")},
    )
    return 1


# -----------------------------------------------------------
# ucoin osnabruck_p2988 per-TID period-boundary violations
# (TID date < period.start). One stable id per TID.

@_classifier(lambda r: re.search(r"TID 17\d{4}.*1570", r.get("detail", "")) or
             re.search(r"TID 17\d{4}.*1566", r.get("detail", "")) or
             re.search(r"TID 17\d{4}.*precedes ucoin", r.get("detail", "")))
def emit_ucoin_p2988_period_boundary(record: dict) -> int:
    detail = record["detail"]
    tids = re.findall(r"TID (17\d{4})", detail)
    if not tids:
        return 0
    for tid in set(tids):
        al.record(
            type_="audit_manifest_period_boundary",
            key_dims={"source": "ucoin", "bucket": "osnabruck_p2988", "tid": tid},
            summary=(
                f"ucoin TID {tid} carries a year predating its bucket's "
                f"period start (osnabruck_p2988 = 1586-1805) — ucoin internal "
                f"label inconsistency, but year still within mission window."
            ),
            detail=detail,
            affected_ids={"ucoin": [int(tid)]},
            proposed_fix=record.get("follow_up"),
            batch_label=record.get("_batch_label"),
            run_utc=record.get("_run_utc"),
            full_context={"action_taken": record.get("action_taken")},
        )
    return len(set(tids))


# -----------------------------------------------------------
# Transient — SKIP per design.

@_classifier(lambda r: r.get("type") == "cloudflare_challenge_persistent")
def emit_transient_skip(record: dict) -> int:
    print(
        f"  [SKIP] cloudflare_challenge_persistent at {record.get('_run_utc')} "
        f"— transient, not logged per docs/ANOMALY_LOG.md."
    )
    return 0


# ---------------------------------------------------------------------------
# Driver


def _backfill_failed_open_ids() -> tuple[int, int, int]:
    """Walk scripts/cache/{numista,ucoin}/_failed_open_ids.json files.

    For each historic failure entry: if the source's `<id>.json` cache file
    NOW exists, the failure was resolved by a later successful fetch → skip
    (per user rule: «ігноруй те що вже було пофікшено згодом»).

    Otherwise emit a `url_open_failed:source=X:id=Y` entry. Multiple historic
    occurrences for same id fold into a single log entry via `al.record()`'s
    upsert-on-active-id behaviour.

    Returns (walked, skipped_resolved, emitted_entries).
    """
    walked = 0
    skipped = 0
    emitted = 0
    seen_ids_emitted: set[tuple[str, str]] = set()  # (source, id_str)

    for source in ("numista", "ucoin"):
        p = _REPO_ROOT / f"scripts/cache/{source}/_failed_open_ids.json"
        if not p.exists():
            continue
        arr = json.loads(p.read_text())
        cache_dir = _REPO_ROOT / f"scripts/cache/{source}"
        for record in arr:
            walked += 1
            id_ = record["id"]
            id_str = str(id_)
            cache_file = cache_dir / f"{id_str}.json"
            if cache_file.exists():
                skipped += 1
                continue
            # Still uncached — escalate to anomaly log
            al.record(
                type_="url_open_failed",
                key_dims={"source": source, "id": id_str},
                summary=(
                    f"{source} id={id_str} persistently fails to fetch "
                    f"(reason last seen: {record.get('reason')!r}). ID remains "
                    f"in audit gap_nids/gap_tids as retry candidate; cache file absent."
                ),
                detail=(
                    f"Batch {record.get('batch_label')!r}: {record.get('reason')!r} — "
                    f"url tried {record.get('url_tried')!r}. "
                    f"{record.get('details') or ''}"
                ).strip(),
                affected_ids={source: [id_]},
                proposed_fix=(
                    "Open the URL in browser to determine status: renamed / merged / "
                    "moved / withdrawn / genuinely-removed. If verified OOS, reclassify "
                    f"the ID into the audit's oos_excluded_{'nids' if source=='numista' else 'tids'} "
                    "slot with audit-trail reason."
                ),
                batch_label=record.get("batch_label"),
                run_utc=record.get("ts", "").replace(".908521Z", "Z").replace(".413418Z", "Z")[:19] + "Z"
                if record.get("ts") else None,
                full_context={
                    "reason": record.get("reason"),
                    "url_tried": record.get("url_tried"),
                    "raw_ts": record.get("ts"),
                },
            )
            key = (source, id_str)
            if key not in seen_ids_emitted:
                seen_ids_emitted.add(key)
                emitted += 1

    return walked, skipped, emitted


def main():
    handoff_path = _REPO_ROOT / "scripts/cache/_harvest_handoff.json"
    if not handoff_path.exists():
        print(f"ERROR: handoff file missing at {handoff_path}", file=sys.stderr)
        sys.exit(1)
    handoff = json.loads(handoff_path.read_text())

    pre_count = al.summary_counts()
    print(f"Pre-backfill counts: {pre_count}")
    print()

    # --- Part 1: handoff runs[].anomalies[] walk ---
    print("=== Part 1: handoff anomalies walk ===")
    walked = 0
    classified = 0
    unclassified = []
    for run in handoff.get("runs", []):
        run_utc = run.get("run_utc")
        nb = (run.get("numista_batch") or {}).get("label")
        ub = (run.get("ucoin_batch") or {}).get("label")
        ib = (run.get("ikmk_batch") or {}).get("label")
        for a in run.get("anomalies") or []:
            walked += 1
            enriched = {
                **a,
                "_run_utc": run_utc,
                "_batch_label": ub or nb or ib,
                "_numista_batch": nb,
                "_ucoin_batch": ub,
                "_ikmk_batch": ib,
            }
            emitted_total = 0
            for pred, emit in CLASSIFIERS:
                if pred(enriched):
                    n = emit(enriched)
                    emitted_total += n
            if emitted_total == 0:
                unclassified.append(enriched)
            else:
                classified += 1
                print(
                    f"  [{run_utc}] type={a.get('type')!r} → "
                    f"{emitted_total} log entries emitted/updated"
                )

    print()
    print(f"Part 1: Walked {walked} handoff anomalies; classified+emitted {classified}; unclassified {len(unclassified)}")
    if unclassified:
        for u in unclassified:
            print(
                f"  unclassified: [{u.get('_run_utc')}] type={u.get('type')!r} detail={u.get('detail','')[:120]!r}"
            )

    # --- Part 2: _failed_open_ids.json walk with cache-existence filter ---
    print()
    print("=== Part 2: _failed_open_ids.json walk (cache-existence filter) ===")
    f_walked, f_skipped, f_emitted = _backfill_failed_open_ids()
    print(
        f"Part 2: Walked {f_walked} historic failure entries; "
        f"skipped {f_skipped} (subsequently cached → resolved post-fail per user rule); "
        f"emitted {f_emitted} new url_open_failed log entries."
    )

    print()
    post_count = al.summary_counts()
    print(f"Post-backfill counts: {post_count}")
    print()

    # Show resulting log shape
    log = al.load()
    print(f"Total log entries: {len(log['anomalies'])}")
    print("Active entries (status ∈ {open, acknowledged, in_progress}):")
    for e in al.open_anomalies():
        print(
            f"  - {e['id']!r}  occ={e['occurrence_count']}  "
            f"first={e['instance_first_seen']}  last={e['last_seen']}"
        )


if __name__ == "__main__":
    main()
