"""Harvest the Royal Coin Cabinet Copenhagen (KMM) via the Nationalmuseet API.

Phase 1 (HARVEST) for the 8th source. The KMM collection
(Den Kgl. Mønt- og Medaillesamling, held by the Danish Nationalmuseet) is
exposed through an open, no-auth Elasticsearch endpoint at
`api.natmus.dk/search/public/raw`. Strategy, field anatomy, scope rationale
and the polite-rate posture are documented in `docs/KMK_HARVEST.md` — read
that first.

Two phases driven from CLI:

* ``discover`` — pulls the full `nation.keyword` terms aggregation, runs each
  bucket through `classify_nation_to_entity`, and freezes the IN-SCOPE nation
  strings (those that resolve to a project entity) into the manifest
  (`scripts/cache/kmk/_manifest.json`). This is the scope filter the fetch
  phase enumerates. Resets the search_after cursor when the scope changes.
* ``fetch`` — enumerates every KMM `type=object` record whose `nation` is in
  the frozen scope list, via `search_after` paging (sort `_id` asc — bypasses
  the ES 10 000-doc `from+size` ceiling). Writes each record's WHOLE `_source`
  JSON to `scripts/cache/kmk/<id>.json` (id = numeric `_source.id`). Skips
  ids already cached. Resumable via the manifest cursor; `--limit` caps new
  cache writes per run (rounded up to the page boundary) for the hourly
  harvest routine's per-run batch.

No-arg invocation runs both phases in order.

The harvest is scoped by NATION + a TASK temporal gate (year 1480-1914 when
dated, OR undated with an in-scope ruler — see `_harvest_query`), and keeps the
whole record (no field pruning, no exonumia drop). The temporal gate cuts KMM's
huge medieval Danish bulk (221k → ~42.6k); per-track era refinement (DK 1514 /
German 1559) and §9 exonumia exclusion happen later at SEED time
(`build_kmk_seed.py`).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import KMK_CACHE as CACHE_DIR  # noqa: E402
from lib.mint_registry import classify_nation_to_entity  # noqa: E402

MANIFEST = CACHE_DIR / "_manifest.json"
API_URL = "https://api.natmus.dk/search/public/raw"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; serhii)"
PAGE_SIZE = 500
SLEEP_SECS = 0.4
# Base scope: the KMM coin/medal objects (excludes `still` image-asset records).
_BASE_FILTER = [
    {"term": {"collection.keyword": "KMM"}},
    {"term": {"type.keyword": "object"}},
]

# ── Task-scope temporal gate (curator 2026-06-01) ────────────────────────────
# The bare nation scope is ~221k records, dominated by KMM's huge MEDIEVAL
# Danish holding (62% are undated bracteates/pennings; the dated bulk is pre-
# 1480). The task scope is «Denmark 1480-1914 (wide)», so we gate at HARVEST:
#
#   KEEP a record iff EITHER
#     (a) it is DATED with creationEvents.yearFrom in [1480, 1914]  — OR —
#     (b) it is UNDATED but attributed to an IN-SCOPE ruler (authority present
#         and NOT a medieval pre-Hans Danish monarch).
#
# (b) is essential: ~7.3k undated records carry a ruler + a Hede number
# («H. 71» Frederik III, Christian IV/V skillings etc.) — the project's core
# coins, just lacking a precise creationEvents date. Dropping all undated would
# lose them. The medieval EXCLUDE-list (a closed, distinctive set of Danish
# pre-1481 royal names) is safer than an in-scope INCLUDE-list and never
# collides with in-scope German/SH ruler names (Friedrich, Johan Adolf, …).
#
# Net: 221k → ~42.6k (35.3k dated-in-range + 7.3k undated-in-scope-ruler).
# Year is a STRING field; a 4-digit regexp guard removes the tiny 3-digit
# («181») lexicographic-range leak. Era refinement to the per-track mission
# anchors (DK 1514 / German 1559) stays a SEED/Phase-4 concern.
YEAR_MIN, YEAR_MAX = "1480", "1914"
_MEDIEVAL_AUTHORITY = [
    "Erik", "Svend", "Valdemar", "Knud", "Niels", "Abel", "Christoffer",
    "Margrete", "Oluf", "Harald", "Gorm", "Hardeknud", "Magnus",
    "ubestemmelig", "ubestemt",
]


def _harvest_query(kept_nations: list[str]) -> dict:
    """Full ES query: base + nation scope + the year/ruler task-scope gate."""
    dated_in_range = {"bool": {"filter": [
        {"exists": {"field": "creationEvents"}},
        {"range": {"creationEvents.yearFrom": {"gte": YEAR_MIN, "lte": YEAR_MAX}}},
        {"regexp": {"creationEvents.yearFrom": "[1-9][0-9]{3}"}},  # drop 3-digit leak
    ]}}
    undated_in_scope_ruler = {"bool": {
        "filter": [{"exists": {"field": "authority"}}],
        "must_not": [{"exists": {"field": "creationEvents"}}]
        + [{"match_phrase": {"authority": n}} for n in _MEDIEVAL_AUTHORITY],
    }}
    return {"bool": {
        "filter": _BASE_FILTER + [{"terms": {"nation.keyword": kept_nations}}],
        "must": [{"bool": {"should": [dated_in_range, undated_in_scope_ruler],
                           "minimum_should_match": 1}}],
    }}


def _api_post(body: dict, *, retries: int = 4) -> dict:
    """POST an ES query body to the public/raw endpoint, with backoff."""
    data = json.dumps(body).encode("utf-8")
    backoffs = (2.0, 5.0, 15.0, 60.0)
    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(
            API_URL, data=data,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_err = exc
            wait = backoffs[min(attempt, len(backoffs) - 1)]
            print(f"  API POST attempt {attempt + 1}/{retries}: "
                  f"{type(exc).__name__} — backoff {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise last_err  # type: ignore[misc]


# ── discover ────────────────────────────────────────────────────────────────

def discover() -> dict:
    """Refresh the in-scope nation list from the live aggregation.

    Pulls every `nation.keyword` bucket, classifies it, and freezes the
    strings that resolve to a project entity into the manifest. Preserves the
    fetch cursor when the scope is unchanged; resets it when the scope set
    changed (so a widened scope re-enumerates from the start).
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    agg = _api_post({
        "size": 0,
        "query": {"bool": {"filter": _BASE_FILTER}},
        "aggs": {"n": {"terms": {"field": "nation.keyword", "size": 400}}},
    })
    buckets = agg.get("aggregations", {}).get("n", {}).get("buckets", [])
    kept: dict[str, dict] = {}   # nation string → {count, entity}
    dropped: list[list] = []     # [nation, count] for OOS buckets
    for b in buckets:
        nation, cnt = b["key"], b["doc_count"]
        ent = classify_nation_to_entity(nation)
        if ent is not None:
            kept[nation] = {"count": cnt, "entity": ent}
        else:
            dropped.append([nation, cnt])

    kept_nations = sorted(kept)
    nation_scope_total = sum(v["count"] for v in kept.values())
    # Filtered harvest target = nation scope ∩ (dated-in-range ∨ undated-ruler).
    filt = _api_post({"size": 0, "query": _harvest_query(kept_nations)})
    t = filt.get("hits", {}).get("total")
    in_scope_total = t.get("value") if isinstance(t, dict) else t

    prior = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    scope_changed = sorted(prior.get("kept_nations", [])) != kept_nations

    manifest = {
        "source": "kmk",
        "endpoint": API_URL,
        "base_filter": "collection.keyword=KMM + type.keyword=object",
        "task_scope": (f"year {YEAR_MIN}-{YEAR_MAX} (dated) OR undated with "
                       f"in-scope ruler (medieval-excluded)"),
        "kept_nations": kept_nations,
        "kept_detail": kept,
        "dropped_nations": sorted(dropped, key=lambda x: -x[1]),
        "nation_scope_total": nation_scope_total,
        "in_scope_total": in_scope_total,
        # Reset cursor on scope change so a widened scope re-enumerates; else
        # keep the prior cursor so `fetch` resumes where it left off.
        "cursor": None if scope_changed else prior.get("cursor"),
        "cached_count": prior.get("cached_count", 0),
        "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"  discover: {len(kept_nations)} in-scope nation strings; "
          f"nation-scope {nation_scope_total} → task-scope (1480-1914) "
          f"{in_scope_total} records; {len(dropped)} OOS buckets dropped. "
          f"cursor={'reset' if scope_changed else 'kept'} → {MANIFEST}")
    # Show the kept entities for a quick eyeball (nation-level, pre-temporal-gate).
    by_entity: dict[str, int] = {}
    for v in kept.values():
        by_entity[v["entity"]] = by_entity.get(v["entity"], 0) + v["count"]
    print("    [nation-scope per entity, BEFORE the 1480-1914 temporal gate]")
    for ent, n in sorted(by_entity.items(), key=lambda x: -x[1]):
        print(f"    {ent:35s} {n:>7d}")
    return manifest


# ── fetch ─────────────────────────────────────────────────────────────────--

def _record_id(src: dict) -> str | None:
    """Numeric record id for the cache filename. Prefer `_source.id`; else
    parse it out of the `_id` ("KMM-<n>")."""
    rid = src.get("id")
    if isinstance(rid, int) or (isinstance(rid, str) and rid.isdigit()):
        return str(rid)
    return None


def fetch(limit: int | None = None) -> None:
    """Enumerate in-scope records via search_after and cache whole `_source`.

    Resumes from the manifest cursor. `limit` caps NEW cache writes this run
    (rounded up to the page boundary — a page already fetched is written whole
    rather than discarded). The cursor + cached_count are persisted to the
    manifest after every page so an interrupted run resumes cleanly.
    """
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    kept_nations = manifest.get("kept_nations") or []
    if not kept_nations:
        print("no in-scope nations in manifest — run `discover`", file=sys.stderr)
        sys.exit(1)
    query = _harvest_query(kept_nations)

    cursor = manifest.get("cursor")  # last search_after value, or None
    fetched = skipped = pages = no_id = 0
    t0 = time.time()
    while True:
        body = {"size": PAGE_SIZE, "sort": [{"_id": "asc"}], "query": query}
        if cursor:
            body["search_after"] = cursor
        resp = _api_post(body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            print("  enumeration exhausted (no more hits).")
            cursor = None  # fully walked → reset so next run re-checks from top
            break
        pages += 1
        for h in hits:
            src = h.get("_source", {})
            rid = _record_id(src)
            if rid is None:
                no_id += 1
                continue
            path = CACHE_DIR / f"{rid}.json"
            if path.exists():
                skipped += 1
                continue
            path.write_text(json.dumps(src, ensure_ascii=False, indent=1))
            fetched += 1
        cursor = hits[-1].get("sort")  # advance
        # Persist progress every page (resume-safe).
        manifest["cursor"] = cursor
        manifest["cached_count"] = len(list(CACHE_DIR.glob("[0-9]*.json")))
        manifest["last_fetch_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        if pages % 10 == 0:
            print(f"  page {pages}  fetched={fetched}  skipped={skipped}  "
                  f"elapsed={int(time.time() - t0)}s  cursor={cursor}")
        if limit is not None and fetched >= limit:
            print(f"  reached --limit {limit} (page boundary); stopping.")
            break
        time.sleep(SLEEP_SECS)
    # Final manifest write (cursor may have been reset on exhaustion).
    manifest["cursor"] = cursor
    manifest["cached_count"] = len(list(CACHE_DIR.glob("[0-9]*.json")))
    manifest["last_fetch_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"\nDone. fetched={fetched} skipped={skipped} no_id={no_id} "
          f"pages={pages} cached_total={manifest['cached_count']} "
          f"({int(time.time() - t0)}s).")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", nargs="?", choices=["discover", "fetch", "both"],
                    default="both",
                    help="discover=refresh in-scope nation list, "
                         "fetch=enumerate+cache per manifest, both=discover then fetch.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap on new cache writes per run (rounded up to the "
                         "500-record page boundary). Used by the harvest routine.")
    args = ap.parse_args()
    if args.phase in ("discover", "both"):
        discover()
    if args.phase in ("fetch", "both"):
        fetch(limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
