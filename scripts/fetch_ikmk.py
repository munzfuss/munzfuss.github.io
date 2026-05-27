"""Discover and cache IKMK Berlin records for SH + Denmark scope.

Two phases driven from CLI:

* ``discover`` — runs the configured search queries against
  ``ikmk.smb.museum/quick_search``, collects the union of result IDs,
  writes ``scripts/cache/ikmk/_manifest.json``.
* ``fetch`` — reads the manifest and downloads
  ``object?id=<id>&download=json_ext`` for every ID, caching as
  ``scripts/cache/ikmk/<id>.json``. Skips IDs already cached.

No-arg invocation runs both phases in order.

Why this exists, scope, and the polite-rate / licensing posture are
documented in ``docs/IKMK_HARVEST.md``. Read that first.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import IKMK_CACHE as CACHE_DIR  # noqa: E402

MANIFEST = CACHE_DIR / "_manifest.json"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; serhii)"
SLEEP_SECS = 0.5

# Mission scope per CLAUDE.md §«Mission temporal scope»: 1514 (Christian II
# Lovkompleks, Danish realm) to 1914 (end of precious-metal anchor). German
# lands start 1559 but the wider union is used here as a single filter — a
# German coin from 1530 is rare-but-not-impossible context material; the year-
# overlap rule keeps anything plausibly relevant to the wider 1514-1914 window.
MISSION_YEAR_MIN = 1514
MISSION_YEAR_MAX = 1914


def _is_in_mission_scope(record: dict) -> bool:
    """Return True iff the record's year range overlaps the mission window.

    IKMK records carry integer `year_start` / `year_end` fields (BCE encoded
    as negatives; e.g. -380 = 380 BC). The check is overlap, not containment:
    a record dated 1500-1530 is in scope (touches mission window), as is one
    dated 1900-1920.

    Conservative on missing/unparseable years — return True so we cache the
    record and the curator can decide. Better to harvest a few OOS records
    than to silently drop in-scope ones because of a field-format edge case.
    """
    try:
        y_start = int(record.get("year_start"))
        y_end = int(record.get("year_end"))
    except (TypeError, ValueError):
        return True  # missing/malformed → keep, conservative
    if y_end == 0:
        # Defensive: some records carry year_end=0 as "unset" placeholder;
        # collapse to single-year.
        y_end = y_start
    return y_start <= MISSION_YEAR_MAX and y_end >= MISSION_YEAR_MIN

QUERIES = [
    # Schleswig-Holstein and territorial duchies
    "Schleswig-Holstein", "Holstein", "Schleswig",
    "Holstein-Sonderburg", "Holstein-Sonderburg-Glücksburg",
    "Sonderburg", "Augustenburg", "Plön", "Glücksburg", "Norburg",
    "Schaumburg",
    # SH mints / cities — Royal-Holstein + Gottorp + sub-duchies
    "Glückstadt", "Altona", "Reinfeld", "Eutin", "Kiel", "Flensburg",
    "Itzehoe", "Pinneberg", "Husum", "Haderslev", "Rendsburg",
    "Tönning", "Gottorp", "Barmstedt", "Rantzau",
    # holstein_schauenburg_county ancestral mints (Lower-Saxon
    # Reichsmünzordnung Imperial-circle coinage, distinct from SH-
    # Pinneberg numismatic tradition — see CLAUDE.md analysis
    # 2026-05-26 + docs/research/mint_year_transitions.md).
    "Stadthagen", "Bückeburg", "Rinteln", "Hessisch Oldendorf",
    "Oldendorf",
    # Lauenburg territory + residences (project scope)
    "Lauenburg", "Ratzeburg", "Mölln",
    # Lübeck-Bishopric (Eutin-residenced prince-bishopric)
    "Lübeck Bistum",
    # Hanseatic cities — Hamburg + Lübeck-as-city (separate from
    # Lübeck Bistum bishopric)
    "Hamburg", "Lübeck",
    # Bremen-Verden / Bremen archbishopric
    "Bistum Bremen", "Bremen-Verden", "Stade", "Bremervörde",
    # Hessen-Kassel landgraviate (post-1640 Schaumburg-Hessen-Anteil)
    "Hessen-Kassel", "Hesse-Cassel", "Kassel",
    # Hochstift Osnabrück (prince-bishopric)
    "Osnabrück", "Iburg",
    # Grafschaft Oldenburg (county in Lower Saxony, Danish-king-as-
    # count 1667-1773 personal union)
    "Oldenburg",
    # Brunswick-Lüneburg (project-scope brunswick_lueneburg location)
    "Braunschweig-Lüneburg", "Brunswick-Lüneburg",
    "Braunschweig", "Wolfenbüttel",

    # ============================================================
    # Denmark proper, Danish-Norwegian crown, and Danish-controlled
    # territories outside the Helstaten core (TODO L.2a).
    #
    # Discovery-budget discipline: IKMK quick_search does loose
    # substring matching, so generic given-names («Hans», «Erik»)
    # and short common toponyms («Island») return thousands of
    # unrelated hits. Generic ruler ordinals («Friedrich I.»,
    # «Friedrich II.» etc.) hit the 4000-result cap because every
    # German prince ever called Friedrich shows up. We therefore
    # restrict ruler-axis queries to the Danish kings whose reigns
    # actually overlap our denmark.yml + sh.yml coin range — and
    # skip pure given-name queries entirely.
    # ============================================================

    # Country / region — narrow umbrella
    "Dänemark", "Denmark", "Norwegen", "Norge",
    # Denmark proper mints (Kopenhagen pulls broadly; the rest are
    # narrowly scoped or return 0 — fine to keep as canaries.)
    "Kopenhagen", "Helsingør", "Roskilde", "Aalborg", "Viborg",
    "Ribe", "Odense", "Malmö",
    # Norway under the Danish crown (1397–1814)
    "Christiania", "Kongsberg", "Bergen", "Trondheim", "Trondhjem",
    # Faroe Islands (Danish since 1380)
    "Färöer", "Færøerne",
    # Greenland (Danish until 1953)
    "Grönland", "Grønland",
    # Danish India (Tranquebar trading colony, 1620–1845)
    "Tranquebar", "Trankebar", "Dänisch-Indien",
    # Danish West Indies (1672–1917, modern US Virgin Islands)
    "Dänisch-Westindien", "Dansk Vestindien",
    # Danish Gold Coast / Guinea (1659–1850, modern Ghana)
    "Dänisch Guinea", "Goldküste",
    # Danish kings whose reigns intersect our 1566-1914 window AND
    # who don't share a given+ordinal with prolific German princes.
    # Christian IV-X and Friedrich III/IV are the productive Danish
    # ones; Friedrich I/II/V hit the 4000-cap because they collide
    # with Pfalz/Prussia/HRE Friedrichs and aren't worth the noise.
    "Christian IV.", "Christian V.", "Christian VI.",
    "Christian VII.", "Christian VIII.", "Christian IX.", "Christian X.",
    "Friedrich III.", "Friedrich IV.",
    "Friedrich VI.", "Friedrich VII.",
]


def _make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
    )
    opener.addheaders = [("User-Agent", USER_AGENT)]
    opener.open("https://ikmk.smb.museum/home?lang=en").read()
    return opener


def _search_ids(opener, query: str, range_: int = 4000) -> list[str]:
    data = urllib.parse.urlencode({
        "quick_search_value": query,
        "search_type": "quick_search",
    }).encode()
    req = urllib.request.Request(
        "https://ikmk.smb.museum/quick_search?lang=en",
        data=data,
        headers={"Referer": "https://ikmk.smb.museum/home?lang=en"},
    )
    opener.open(req).read()
    url = f"https://ikmk.smb.museum/tray?lang=en&view=list&range={range_}"
    html = opener.open(url).read().decode("utf-8", "replace")
    return list(dict.fromkeys(
        re.findall(r"\?(?:lang=[a-z]+&)?id=(\d{7,9})(?:&|\"|'|>)", html),
    ))


def discover() -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    per_query: dict[str, list[str]] = {}
    union: list[str] = []
    seen = set()
    for q in QUERIES:
        opener = _make_session()
        try:
            ids = _search_ids(opener, q)
        except urllib.error.HTTPError as exc:
            print(f"  [{q}] HTTP {exc.code}", file=sys.stderr)
            ids = []
        per_query[q] = ids
        new = [i for i in ids if i not in seen]
        seen.update(new)
        union.extend(new)
        print(f"  {q:35s}  hits={len(ids):4d}  cum_union={len(union)}")
        time.sleep(SLEEP_SECS)
    manifest = {
        "queries": per_query,
        "ids": sorted(set(union), key=int),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"\nUnion: {len(manifest['ids'])} IDs → {MANIFEST}")
    return manifest


def _load_oos_set() -> set[str]:
    """Read the manifest's oos_excluded_mds_ids slot (empty set on fresh repo)."""
    if not MANIFEST.exists():
        return set()
    m = json.loads(MANIFEST.read_text())
    return set(str(i) for i in m.get("oos_excluded_mds_ids") or [])


def _record_oos(nid: str, year_start, year_end, title: str = "") -> None:
    """Append nid to manifest's oos_excluded_mds_ids slot (idempotent, sorted)."""
    if not MANIFEST.exists():
        return
    m = json.loads(MANIFEST.read_text())
    oos = set(str(i) for i in m.get("oos_excluded_mds_ids") or [])
    if str(nid) in oos:
        return
    oos.add(str(nid))
    m["oos_excluded_mds_ids"] = sorted(oos, key=int)
    # Lightweight side log for forensics (why each id is OOS)
    detail_log = m.setdefault("oos_excluded_details", {})
    detail_log[str(nid)] = {
        "year_start": year_start,
        "year_end": year_end,
        "title": title[:140],
        "filtered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2))


def _fetch_one(opener_holder: list, nid: str) -> str:
    """Fetch a single record, with retries + backoff for throttle/network errors.

    `opener_holder` is a one-element list holding the current opener so we
    can rebuild the session (fresh cookies, fresh socket) after a backoff.

    Returns:
      "fetched"     — new record downloaded + in mission scope, cached.
      "skipped"     — already cached on disk.
      "oos"         — fetched but year-range outside mission scope; NOT cached,
                      id appended to manifest's oos_excluded_mds_ids slot.
    """
    path = CACHE_DIR / f"{nid}.json"
    if path.exists():
        return "skipped"
    url = f"https://ikmk.smb.museum/object?id={nid}&download=json_ext"
    last_err: Exception | None = None
    backoffs = (2.0, 5.0, 15.0, 60.0)
    for attempt, wait_after in enumerate(backoffs):
        try:
            body = opener_holder[0].open(url, timeout=60).read()
            # Mission-scope filter — applied at-fetch-time, BEFORE writing to
            # cache. Out-of-scope records (ancient, medieval, post-1914 commem,
            # non-project entities) get logged to manifest's
            # oos_excluded_mds_ids slot so future runs skip them without
            # re-fetching.
            try:
                record = json.loads(body)
            except json.JSONDecodeError:
                # Malformed JSON — pass through as-is (legacy behaviour);
                # downstream parser will surface.
                path.write_bytes(body)
                return "fetched"
            if not _is_in_mission_scope(record):
                _record_oos(
                    nid,
                    record.get("year_start"),
                    record.get("year_end"),
                    record.get("title", ""),
                )
                return "oos"
            path.write_bytes(body)
            return "fetched"
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc
            print(
                f"  [{nid}] attempt {attempt + 1}/{len(backoffs)}: "
                f"{type(exc).__name__} — backoff {wait_after}s",
                file=sys.stderr,
            )
            time.sleep(wait_after)
            opener_holder[0] = _make_session()
    raise last_err  # type: ignore[misc]


def fetch(limit: int | None = None) -> None:
    """Fetch JSON for every ID in the manifest (skipping cached + known-OOS).

    Parameters
    ----------
    limit
        When set, stop after that many NEW fetches (cache writes). IDs
        already cached or already-known-OOS are skipped without counting
        against the limit. OOS records discovered during this run (filter
        triggered at-fetch-time) also don't count toward the limit — they
        return "oos", contribute to the oos counter, and the loop continues
        looking for in-scope records to count.
    """
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    ids: list[str] = manifest["ids"]
    oos_known = set(str(i) for i in manifest.get("oos_excluded_mds_ids") or [])
    opener_holder = [_make_session()]
    fetched = 0
    skipped = 0
    oos_skipped_known = 0   # already in oos_excluded_mds_ids
    oos_skipped_fresh = 0   # filtered just now this run
    errors = 0
    t0 = time.time()
    for i, nid in enumerate(ids, start=1):
        # Pre-skip already-known OOS — saves the HTTP fetch
        if nid in oos_known:
            oos_skipped_known += 1
            continue
        try:
            outcome = _fetch_one(opener_holder, nid)
        except urllib.error.HTTPError as exc:
            errors += 1
            print(f"  [{nid}] gave up: HTTP {exc.code}", file=sys.stderr)
            continue
        except Exception as exc:
            errors += 1
            print(f"  [{nid}] gave up: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        if outcome == "fetched":
            fetched += 1
            time.sleep(SLEEP_SECS)
            if limit is not None and fetched >= limit:
                print(
                    f"  reached --limit {limit}; stopping. "
                    f"fetched={fetched} skipped={skipped} "
                    f"oos_known={oos_skipped_known} oos_fresh={oos_skipped_fresh} "
                    f"errors={errors} ({int(time.time() - t0)}s).",
                )
                return
        elif outcome == "oos":
            oos_skipped_fresh += 1
            time.sleep(SLEEP_SECS)  # we still hit the API, pace politely
        else:  # "skipped" — already in cache
            skipped += 1
        if i % 50 == 0:
            elapsed = int(time.time() - t0)
            remaining = len(ids) - i
            print(
                f"  progress {i}/{len(ids)}  fetched={fetched}  skipped={skipped}  "
                f"oos_known={oos_skipped_known} oos_fresh={oos_skipped_fresh}  "
                f"errors={errors}  elapsed={elapsed}s  remaining≈{int(remaining * SLEEP_SECS)}s",
            )
    print(
        f"\nDone. fetched={fetched} skipped={skipped} "
        f"oos_known={oos_skipped_known} oos_fresh={oos_skipped_fresh} "
        f"errors={errors} out of {len(ids)} ({int(time.time() - t0)}s).",
    )


def scan_cache() -> None:
    """Walk already-cached records, apply mission-scope filter, populate
    manifest's oos_excluded_mds_ids slot.

    One-shot cleanup for IDs cached before the at-fetch-time filter existed.
    Does NOT delete cache files — only marks them OOS so downstream
    consumers (seed builders, coverage tables) can skip them. Preserves
    cache as audit trail.
    """
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    cache_files = sorted(CACHE_DIR.glob("[0-9]*.json"))
    print(f"scanning {len(cache_files)} cached records against mission scope "
          f"[{MISSION_YEAR_MIN}, {MISSION_YEAR_MAX}]...")
    in_scope = 0
    oos = 0
    no_year = 0
    newly_oos: list[tuple[str, dict]] = []
    for p in cache_files:
        try:
            record = json.loads(p.read_text())
        except json.JSONDecodeError:
            print(f"  [{p.stem}] malformed JSON — skip", file=sys.stderr)
            continue
        ys, ye = record.get("year_start"), record.get("year_end")
        if ys is None or ye is None or ys == "" or ye == "":
            no_year += 1
            continue
        if _is_in_mission_scope(record):
            in_scope += 1
        else:
            oos += 1
            newly_oos.append((p.stem, record))
    # Bulk-write all newly-found OOS ids
    if newly_oos:
        manifest = json.loads(MANIFEST.read_text())
        existing = set(str(i) for i in manifest.get("oos_excluded_mds_ids") or [])
        added = 0
        details = manifest.setdefault("oos_excluded_details", {})
        for nid, record in newly_oos:
            if nid in existing:
                continue
            existing.add(nid)
            added += 1
            details[nid] = {
                "year_start": record.get("year_start"),
                "year_end": record.get("year_end"),
                "title": (record.get("title") or "")[:140],
                "filtered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "scan_cache",
            }
        manifest["oos_excluded_mds_ids"] = sorted(existing, key=int)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"  added {added} ids to manifest.oos_excluded_mds_ids "
              f"(was {len(existing) - added}, now {len(existing)})")
    print(f"\nDone. in_scope={in_scope}  oos={oos}  no_year={no_year}  "
          f"total={len(cache_files)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "phase",
        nargs="?",
        choices=["discover", "fetch", "both", "scan-cache"],
        default="both",
        help="discover=rebuild manifest from QUERIES, fetch=download per "
             "manifest, both=discover then fetch, scan-cache=walk already-"
             "cached records + mark OOS per mission scope filter.",
    )
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Cap on new fetches per run (cache writes). Used by the "
             "hourly harvest routine for small per-run batches. "
             "Applies to `fetch` and `both` phases.",
    )
    args = ap.parse_args()
    if args.phase == "scan-cache":
        scan_cache()
        return 0
    if args.phase in ("discover", "both"):
        discover()
    if args.phase in ("fetch", "both"):
        fetch(limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
