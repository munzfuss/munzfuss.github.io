"""Anomaly-log API — persistent record of harvest / build / curation anomalies.

Companion: `docs/ANOMALY_LOG.md` (schema + lifecycle), `docs/anomaly_log.yml`
(the log itself). Reader/writer for the harvest routine (`docs/HARVEST_ROUTINE.md`
§1.5) and any other pipeline component that surfaces a non-fatal anomaly worth
preserving across sessions.

The log lives in the MAIN repo (`docs/`), not the `scripts/cache/` submodule.
Rationale: anomaly triage is a curator workflow (open → acknowledged →
in_progress → resolved), with normal git-review semantics. Submodule's
push-by-routine / never-read-by-build lifecycle would let entries drift.

## Stable-id derivation

Each anomaly carries a deterministic `id` of the form
`<type>:<k1>=<v1>:<k2>=<v2>` (kebab-case keys + values). Gran granularity is
intentionally FINE — different queries / buckets / boundaries get distinct ids,
even when classified under the same `type`. This avoids collapsing distinct
problems into one entry. Per-tid / per-batch-label dimensions ARE included
where they distinguish the issue; per-run timestamps are NOT (they're occurrence
metadata, not identity).

Examples:
  audit_manifest_scope_drift:ikmk:query=hamburg
  audit_manifest_scope_drift:ucoin:bucket=osnabruck_p3057
  audit_manifest_label_mismatch:ucoin:bucket=osnabruck_p2988
  audit_manifest_period_boundary:ucoin:bucket=osnabruck_p2988:tid=172175

## Reopen-after-resolved rule

`record()` looks up the LATEST entry with the matching stable id:
  - If status ∈ {open, acknowledged, in_progress}: update in place
    (bump last_seen + occurrence_count, append occurrence, merge affected_ids).
  - If status ∈ {resolved, wontfix} OR no entry exists: CREATE A NEW entry
    (fresh instance_first_seen, status=open, occurrence_count=1). The previous
    resolved entry stays in the file as archive.

So multiple entries with the same `id` are valid — at most one is active at any
time. `mark_resolved(id, ...)` targets the latest active one.

## Transient anomalies are NOT logged

Anything that auto-resolved within the SAME run (Cloudflare interstitial that
cleared after 90s, single fetch that retried OK) belongs in
`scripts/cache/_harvest_handoff.json::runs[].anomalies[]` as per-run snapshot.
Only anomalies that survive the run unresolved escalate to this persistent log.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Iterable

import yaml

# ---------------------------------------------------------------------------
# Constants

SCHEMA_VERSION = 1

ACTIVE_STATUSES = {"open", "acknowledged", "in_progress"}
TERMINAL_STATUSES = {"resolved", "wontfix"}
ALL_STATUSES = ACTIVE_STATUSES | TERMINAL_STATUSES

LOG_RELATIVE_PATH = "docs/anomaly_log.yml"


# ---------------------------------------------------------------------------
# Path resolution


def _repo_root() -> pathlib.Path:
    """Resolve main-repo root, working from any cwd (including submodule).

    `git rev-parse --show-toplevel` returns the SUBMODULE root when cwd is
    inside the submodule. The main-repo marker is the presence of `docs/` and
    `data/`; walk up until found.
    """
    p = pathlib.Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=pathlib.Path.cwd()
        )
        .decode()
        .strip()
    )
    while p != p.parent:
        if (p / "docs").is_dir() and (p / "data").is_dir():
            return p
        p = p.parent
    raise RuntimeError("could not locate main-repo root from cwd")


def log_path() -> pathlib.Path:
    """Canonical path to docs/anomaly_log.yml in the main repo."""
    return _repo_root() / LOG_RELATIVE_PATH


# ---------------------------------------------------------------------------
# Stable-id derivation


_KEBAB_RE = re.compile(r"[^a-z0-9]+")


def _kebab(s: str) -> str:
    return _KEBAB_RE.sub("_", str(s).lower()).strip("_")


def derive_id(type_: str, key_dims: dict[str, Any]) -> str:
    """Build stable id `<type>:<k1>=<v1>:<k2>=<v2>` (sorted keys for determinism)."""
    type_slug = _kebab(type_)
    parts = [type_slug]
    for k in sorted(key_dims):
        parts.append(f"{_kebab(k)}={_kebab(key_dims[k])}")
    return ":".join(parts)


# ---------------------------------------------------------------------------
# Load / save


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _empty_log() -> dict:
    return {
        "_metadata": {
            "schema_version": SCHEMA_VERSION,
            "last_updated_utc": _now(),
        },
        "anomalies": [],
    }


def load() -> dict:
    """Read the log; return empty scaffold if file missing."""
    p = log_path()
    if not p.exists():
        return _empty_log()
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict) or "anomalies" not in raw:
        raise RuntimeError(
            f"{p}: malformed anomaly log (expected top-level dict with 'anomalies' list)"
        )
    raw.setdefault("_metadata", {"schema_version": SCHEMA_VERSION})
    raw.setdefault("anomalies", [])
    return raw


def save(log: dict) -> None:
    """Write the log atomically (write+rename) with deterministic ordering."""
    p = log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    log["_metadata"]["last_updated_utc"] = _now()
    log["_metadata"]["schema_version"] = SCHEMA_VERSION

    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(
        yaml.safe_dump(
            log,
            sort_keys=False,
            allow_unicode=True,
            width=100,
            default_flow_style=False,
        )
    )
    tmp.replace(p)


# ---------------------------------------------------------------------------
# Helpers


def _merge_affected_ids(
    existing: dict[str, list], new: dict[str, list] | None
) -> dict[str, list]:
    """Union per-source id lists, preserving insertion order, dedup'd."""
    if not new:
        return existing
    out = {k: list(v) for k, v in (existing or {}).items()}
    for src, ids in new.items():
        bucket = out.setdefault(src, [])
        seen = set(bucket)
        for i in ids:
            if i not in seen:
                bucket.append(i)
                seen.add(i)
    return out


def _find_latest_by_id(log: dict, stable_id: str) -> tuple[int, dict] | None:
    """Return (index, entry) of latest entry matching stable_id, or None.

    «Latest» = highest `instance_first_seen` timestamp. Ties broken by list
    position (last wins).
    """
    candidates = [
        (i, e) for i, e in enumerate(log["anomalies"]) if e.get("id") == stable_id
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda ie: ie[1].get("instance_first_seen", ""))
    return candidates[-1]


# ---------------------------------------------------------------------------
# Writer


def record(
    type_: str,
    key_dims: dict[str, Any],
    summary: str,
    detail: str,
    affected_ids: dict[str, list] | None = None,
    proposed_fix: str | None = None,
    batch_label: str | None = None,
    run_utc: str | None = None,
    full_context: dict | None = None,
) -> str:
    """Record an anomaly. Returns the stable id.

    Behaviour:
      - Latest entry with this id is ACTIVE (open/acknowledged/in_progress):
        update in place — bump last_seen + occurrence_count, append to
        occurrences, merge affected_ids, refresh proposed_fix if newer text
        passed.
      - Latest entry is TERMINAL (resolved/wontfix) OR no entry: create a NEW
        entry with status=open, instance_first_seen=now, occurrence_count=1.
        Previous resolved entry stays in log as archive.
    """
    if not isinstance(key_dims, dict) or not key_dims:
        raise ValueError("record() requires non-empty key_dims dict for stable-id derivation")

    stable_id = derive_id(type_, key_dims)
    log = load()

    now = run_utc or _now()
    occurrence = {
        "run_utc": now,
        "batch_label": batch_label,
        "detail": detail,
    }
    if full_context:
        occurrence["full_context"] = full_context
    # Strip None values for cleaner YAML
    occurrence = {k: v for k, v in occurrence.items() if v is not None}

    found = _find_latest_by_id(log, stable_id)
    if found is not None and found[1].get("status") in ACTIVE_STATUSES:
        _, entry = found
        entry["last_seen"] = now
        entry["occurrence_count"] = int(entry.get("occurrence_count", 0)) + 1
        entry.setdefault("occurrences", []).append(occurrence)
        entry["affected_ids"] = _merge_affected_ids(
            entry.get("affected_ids", {}), affected_ids
        )
        # Refresh proposed_fix if caller supplied an updated one (don't clear
        # existing on absence — keeps triager-edited text).
        if proposed_fix:
            entry["proposed_fix"] = proposed_fix
        # Refresh summary similarly.
        if summary:
            entry["summary"] = summary
    else:
        entry = {
            "id": stable_id,
            "type": type_,
            "key_dims": dict(key_dims),
            "summary": summary,
            "status": "open",
            "instance_first_seen": now,
            "last_seen": now,
            "occurrence_count": 1,
            "affected_ids": _merge_affected_ids({}, affected_ids),
            "occurrences": [occurrence],
            "proposed_fix": proposed_fix,
            "resolution": None,
            "resolved_at": None,
            "resolved_by": None,
        }
        log["anomalies"].append(entry)

    save(log)
    return stable_id


# ---------------------------------------------------------------------------
# Reader


def open_anomalies(filter_type: str | None = None) -> list[dict]:
    """Return all entries with status in ACTIVE_STATUSES (sorted oldest-first).

    `filter_type` (optional) restricts to a specific `type` slug.
    """
    log = load()
    out = [
        e
        for e in log["anomalies"]
        if e.get("status") in ACTIVE_STATUSES
        and (filter_type is None or e.get("type") == filter_type)
    ]
    out.sort(key=lambda e: e.get("instance_first_seen", ""))
    return out


def get_by_id(stable_id: str, include_archived: bool = False) -> list[dict]:
    """Return entries matching stable_id (oldest first). If !include_archived,
    only active entries are returned."""
    log = load()
    out = [e for e in log["anomalies"] if e.get("id") == stable_id]
    if not include_archived:
        out = [e for e in out if e.get("status") in ACTIVE_STATUSES]
    out.sort(key=lambda e: e.get("instance_first_seen", ""))
    return out


def summary_counts() -> dict[str, int]:
    """{status: count} across all entries (active + archived) — for §8 reports."""
    log = load()
    counts = {s: 0 for s in ALL_STATUSES}
    for e in log["anomalies"]:
        s = e.get("status")
        if s in counts:
            counts[s] += 1
    return counts


# ---------------------------------------------------------------------------
# State transitions (manual triage)


def _set_status(stable_id: str, new_status: str, **fields) -> dict:
    if new_status not in ALL_STATUSES:
        raise ValueError(f"unknown status: {new_status!r} (allowed: {sorted(ALL_STATUSES)})")
    log = load()
    found = _find_latest_by_id(log, stable_id)
    if found is None:
        raise KeyError(f"anomaly id not found: {stable_id!r}")
    _, entry = found
    if entry.get("status") not in ACTIVE_STATUSES:
        raise RuntimeError(
            f"latest entry for {stable_id!r} already terminal "
            f"(status={entry.get('status')!r}); cannot transition. "
            f"To re-open, let record() create a fresh instance on next occurrence."
        )
    entry["status"] = new_status
    for k, v in fields.items():
        entry[k] = v
    save(log)
    return entry


def mark_acknowledged(stable_id: str, note: str | None = None) -> dict:
    """Mark active anomaly as acknowledged (triager has seen, not yet fixing)."""
    fields = {"acknowledged_at": _now()}
    if note:
        fields["acknowledgement_note"] = note
    return _set_status(stable_id, "acknowledged", **fields)


def mark_in_progress(stable_id: str, note: str | None = None) -> dict:
    """Mark active anomaly as in_progress (triager actively working on it)."""
    fields = {"in_progress_at": _now()}
    if note:
        fields["in_progress_note"] = note
    return _set_status(stable_id, "in_progress", **fields)


def mark_resolved(
    stable_id: str, resolution: str, resolved_by: str = "manual"
) -> dict:
    """Mark active anomaly as resolved with a short resolution text.

    `resolved_in_commit` deliberately NOT recorded — git log on
    `docs/anomaly_log.yml` provides the commit trail via `resolved_at` timestamp.
    """
    return _set_status(
        stable_id,
        "resolved",
        resolution=resolution,
        resolved_at=_now(),
        resolved_by=resolved_by,
    )


def mark_wontfix(stable_id: str, resolution: str, resolved_by: str = "manual") -> dict:
    """Mark active anomaly as wontfix (acknowledged but no fix planned).

    Semantically same shape as resolved; different status to make the
    «documented decision not to fix» case greppable.
    """
    return _set_status(
        stable_id,
        "wontfix",
        resolution=resolution,
        resolved_at=_now(),
        resolved_by=resolved_by,
    )
