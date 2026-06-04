#!/usr/bin/env python3
"""Reclassify out-of-scope (banknote / exonumia / pattern) NIDs in the BO.7
Numista audit manifest into an ``oos_excluded_nids`` slot.

Why: BO.7 enumeration pulled full Numista issuer listings; ``ct=coin`` still
leaks Patterns (a coin-category subtype) and a few medal/banknote rows. Those
are OOS for the project's coin tables (CLAUDE.md §9.1 patterns / §9.2 exonumia).

Two sources of OOS NIDs:
  1. CACHED records — classified directly via ``classify_numista_scope`` from
     the Numista ``type`` field + title + metal + denomination.
  2. UNCACHED records — sampled via §7.5 during a run (page seen, never saved),
     so the cache classifier can't see them. The run logs an
     ``audit_manifest_scope_drift`` anomaly carrying the affected NID + the OOS
     kind in its summary. ``--from-anomalies`` folds those into
     ``oos_excluded_nids`` and resolves the anomaly — so the routine NEVER needs
     a hand-maintained NID list (the old ``KNOWN_UNCACHED_OOS`` whack-a-mole).

Durability: once a NID is in ``oos_excluded_nids``, ``refresh_audit_cached_counts``
prunes it from ``in_scope_nids`` on every run — even if a re-enumeration re-adds
it. So the manifest slot is the source of truth; no code-side NID list is kept.

Usage:
    python scripts/maintenance/reclassify_bo7_oos.py                    # dry-run: cache sweep
    python scripts/maintenance/reclassify_bo7_oos.py --write            # persist cache sweep
    python scripts/maintenance/reclassify_bo7_oos.py --from-anomalies --write
        # also fold open audit_manifest_scope_drift OOS anomalies + resolve them
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from lib.numista_canonical import classify_numista_scope  # noqa: E402

MANIFEST = ROOT / "scripts/cache/numista/_BO7_audit_2026-05-24.json"
NUMISTA_DIR = ROOT / "scripts/cache/numista"

# Bucketing-drift markers — anomalies about bucket OVERLAP (not OOS content)
# must NOT be folded as exclusions (their affected NIDs are real coins).
_BUCKETING_MARKERS = ("overlap", "superset", "double-count", "double count")


def _type_of(d: dict) -> str:
    return d.get("type") or (d.get("_raw_rows") or {}).get("Type") or ""


def _recompute(info: dict) -> None:
    keep = list(info.get("in_scope_nids") or [])
    cached = [n for n in keep if (NUMISTA_DIR / f"{n}.json").exists()]
    info["in_scope_total"] = len(keep)
    info["cached_count"] = len(cached)
    info["gap_nids"] = [n for n in keep if n not in set(cached)]


def _exclude_nid(buckets: dict, nid: int, reason: str) -> str | None:
    """Move ``nid`` from whatever bucket holds it in_scope into that bucket's
    oos_excluded_nids. Returns the bucket name if moved, None if it was not
    in any in_scope list (already excluded / absent)."""
    for bk, info in buckets.items():
        if nid in (info.get("in_scope_nids") or []):
            info["in_scope_nids"] = [x for x in info["in_scope_nids"] if x != nid]
            if "in_scope_year_meta" in info:
                info["in_scope_year_meta"] = [
                    m for m in info["in_scope_year_meta"] if m.get("nid") != nid]
            info.setdefault("oos_excluded_nids", {})[str(nid)] = reason
            _recompute(info)
            return bk
    return None


def _anomaly_oos_kind(summary: str) -> str | None:
    s = (summary or "").lower()
    if any(m in s for m in _BUCKETING_MARKERS):
        return None  # bucketing drift, not OOS content
    if "banknote" in s:
        return "banknote"
    if re.search(r"\bmedal|token|jeton|exonumia|rechenpfennig", s):
        return "exonumia"
    if "pattern" in s:
        return "pattern"
    return None


def cache_sweep(buckets: dict) -> tuple[int, list[str]]:
    total, report = 0, []
    for bk, info in buckets.items():
        nids = list(info.get("in_scope_nids") or [])
        oos: dict[int, str] = {}
        for n in nids:
            p = NUMISTA_DIR / f"{n}.json"
            if not p.exists():
                continue  # uncached → handled via --from-anomalies, not here
            try:
                d = json.loads(p.read_text())
            except Exception:
                continue
            in_scope, kind, reason = classify_numista_scope(
                _type_of(d), d.get("title"), d.get("metal"), d.get("denomination"))
            if not in_scope:
                oos[n] = f"{kind} — {reason}"
        if not oos:
            continue
        info["in_scope_nids"] = [n for n in nids if n not in oos]
        if "in_scope_year_meta" in info:
            info["in_scope_year_meta"] = [
                m for m in info["in_scope_year_meta"] if m.get("nid") not in oos]
        slot = info.setdefault("oos_excluded_nids", {})
        for n, r in oos.items():
            slot[str(n)] = r
        _recompute(info)
        total += len(oos)
        report.append(f"  [cache] {bk:<33} -{len(oos):>2} OOS → in_scope {info['in_scope_total']}")
        for n, r in sorted(oos.items()):
            report.append(f"            N#{n:<8} {r[:78]}")
    return total, report


def anomaly_fold(buckets: dict, write: bool) -> tuple[int, list[str]]:
    from scripts.lib import anomaly_log as al
    total, report = 0, []
    for e in al.open_anomalies("audit_manifest_scope_drift"):
        kind = _anomaly_oos_kind(e.get("summary") or "")
        if kind is None:
            continue  # bucketing drift or unrecognised — leave open for a human
        nids = (e.get("affected_ids") or {}).get("numista") or []
        if not nids:
            continue
        moved, already = [], []
        for n in nids:
            bk = _exclude_nid(buckets, int(n), f"{kind} — per anomaly {e['id']}: "
                              f"{(e.get('summary') or '')[:90]}")
            (moved if bk else already).append((int(n), bk))
            if bk:
                total += 1
        report.append(f"  [anomaly] {e['id']}")
        for n, bk in moved:
            report.append(f"            N#{n} → {bk} oos_excluded")
        for n, _ in already:
            report.append(f"            N#{n} already excluded / absent")
        if write:
            al.mark_resolved(
                e["id"],
                resolution=("Affected NIDs folded into oos_excluded_nids via "
                            "reclassify_bo7_oos.py --from-anomalies; refresh prunes them from in_scope."),
                resolved_by="reclassify_bo7_oos --from-anomalies")
            report.append("            → anomaly RESOLVED")
    return total, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="persist changes")
    ap.add_argument("--from-anomalies", action="store_true",
                    help="also fold open audit_manifest_scope_drift OOS anomalies + resolve")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    buckets = manifest["in_scope_buckets"]

    ct, creport = cache_sweep(buckets)
    at, areport = (anomaly_fold(buckets, args.write) if args.from_anomalies else (0, []))

    print(f"=== BO.7 OOS reclassification: {ct} cached + {at} anomaly-folded ===")
    print("\n".join(creport + areport) or "  (nothing to do)")
    if args.write:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"\nWROTE {MANIFEST}")
    else:
        print("\n(dry-run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
