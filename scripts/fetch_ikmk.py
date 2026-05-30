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

# Scope note (curator 2026-05-29). The keep-scope is multi-level:
#   • Broad (future): German lands + Scandinavia + territories under their
#     rule (HRE / Denmark / Norway / dependencies), in ANY era — pre-1514 and
#     post-1914 included as future-useful context.
#   • Narrow (current research): Schleswig-Holstein 1559(1566)-1914 +
#     Denmark 1514-1914 (+ 1480+ examples for standards predating 1514).
#   • Active harvest concentration: 1480-1914 — but that governs which
#     discovery buckets we prioritise, NOT what we reject on fetch.
# The fetch / scan scope gate is therefore ENTITY-based (country + object-
# type), NOT year: see `_is_in_entity_scope`. Anything German/Scandinavian
# that surfaces is kept regardless of year; only other-country coins and
# exonumia are filtered out.


# Entity-scope filter (added 2026-05-29 after the IKMK cache scope-purge —
# see docs/SOURCES.md §13.8). This is the SOLE fetch/scan gate (it replaced an
# earlier year-only filter). The full-text quick_search discovery pulls records
# from other countries (ancient/oriental/foreign) and non-coin objects (medals,
# dies, jetons); without this gate the cache re-accumulates ~90 % out-of-scope.
# The keep-rule mirrors the purge classification exactly.
_KEEP_COUNTRIES = {
    "Germany", "Deutschland", "Denmark", "Dänemark", "Norway", "Norwegen",
    "Sweden", "Schweden", "Iceland", "Island", "Finland", "Finnland",
}
# Borderline modern states that hold historical German / HRE territories
# (Silesia, Pomerania, Neuchâtel, Bohemia, Austrian HRE lands). IKMK tags mint
# country by modern geography, so these must be kept per curator verdict
# 2026-05-29 — a naïve "country != Germany" drop would lose German-lands material.
_BORDERLINE_COUNTRIES = {
    "Poland", "Polen", "Switzerland", "Schweiz", "Czech Republic",
    "Tschechische Republik", "Austria", "Österreich", "Netherlands",
    "Niederlande", "Belgium", "Belgien", "Luxembourg", "Luxemburg",
}
# Danish-colonial coins are in scope even under a foreign mint country.
_COLONIAL_RE = re.compile(
    r"(Tranquebar|Trankebar|Vestindien|Westindien|Virgin|Guinea|"
    r"Goldküste|Dänisch|Grönland|Grønland|Färöer|Færøerne)", re.I)
# None-country records: drop only clearly ancient/oriental polities; keep the
# rest (German issuers occasionally carry no mint country, e.g. "Preußen …").
_NONE_ORIENTAL_RE = re.compile(
    r"^(Abbasiden|Umayyaden|Sasaniden|Südarabien|Arabo-Sasaniden|"
    r"Persischer Großkönig|Persis|Makedonien|Honorius|Früh-islamische|"
    r"Umayyaden oder Abbasiden)")


def _first(x):
    """First dict in a list-or-dict field (IKMK mint/item/division shapes vary)."""
    while isinstance(x, list):
        x = x[0] if x else {}
    return x if isinstance(x, dict) else {}


def _is_in_entity_scope(record: dict) -> tuple[bool, str]:
    """Return (in_scope, reason).

    Keep coins of German lands + Scandinavia (+ borderline HRE states +
    Danish colonies); drop other-country coins and all exonumia. Uses the
    museum's own `item.item_en` / `division` typology (authoritative) and the
    `mint[].country_name` geocoding. Conservative on missing fields — keep.
    """
    item_en = _first(record.get("item")).get("item_en")
    div_en = _first(record.get("division")).get("division_name_en")
    title = str(record.get("title") or "")
    # Exonumia (medal / minting tool / model / token / paper money / seal / …).
    if div_en == "Medals" or (item_en is not None and item_en != "Coin"):
        return False, f"exonumia:{item_en or div_en}"
    if _COLONIAL_RE.search(title):
        return True, "colonial"
    mint = _first(record.get("mint"))
    country = mint.get("country_name_en") or mint.get("country_name_de")
    if country in _KEEP_COUNTRIES or country in _BORDERLINE_COUNTRIES:
        return True, "keep"
    if country is None:
        if _NONE_ORIENTAL_RE.match(title):
            return False, "none-oriental"
        return True, "none-keep"  # conservative: keep ambiguous None-country
    return False, f"other-country:{country}"

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


def _record_oos(nid: str, year_start, year_end, title: str = "",
                reason: str = "entity") -> None:
    """Append nid to manifest's oos_excluded_mds_ids slot (idempotent, sorted).

    `reason` records WHY the record is out of scope — an entity reason from
    `_is_in_entity_scope` ("exonumia:…", "other-country:…", "none-oriental").
    """
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
        "reason": reason,
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
            # Scope gate is ENTITY-based (country + object-type), NOT year.
            # Per curator scope 2026-05-29: the broad keep-scope is German
            # lands + Scandinavia + territories under their rule, in ANY era
            # (HRE / Denmark / Norway, pre-1514 and post-1914 included as
            # future-useful context). Year is therefore NOT a drop criterion —
            # only other-country coins and exonumia are filtered out. (The
            # active harvest CONCENTRATION is 1480-1914, but that governs which
            # discovery buckets we prioritise, not what we reject on fetch:
            # anything German/Scandinavian that surfaces is kept.)
            in_scope, reason = _is_in_entity_scope(record)
            if not in_scope:
                _record_oos(
                    nid,
                    record.get("year_start"),
                    record.get("year_end"),
                    record.get("title", ""),
                    reason=reason,
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
    """Walk already-cached records, apply the ENTITY-scope filter, populate
    manifest's oos_excluded_mds_ids slot.

    One-shot cleanup for IDs cached before the at-fetch-time filter existed.
    Does NOT delete cache files — only marks them OOS so downstream
    consumers (seed builders, coverage tables) can skip them. Preserves
    cache as audit trail.

    Scope is ENTITY-based (country + object-type), NOT year — German /
    Scandinavian coins of any era are in the broad keep-scope (see
    `_is_in_entity_scope` + docs/SOURCES.md §13.8). Only other-country coins
    and exonumia are marked OOS.
    """
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    cache_files = sorted(CACHE_DIR.glob("[0-9]*.json"))
    print(f"scanning {len(cache_files)} cached records against entity scope "
          f"(German lands + Scandinavia + borderline-HRE, any era)...")
    in_scope = 0
    oos = 0
    newly_oos: list[tuple[str, dict, str]] = []
    for p in cache_files:
        try:
            record = json.loads(p.read_text())
        except json.JSONDecodeError:
            print(f"  [{p.stem}] malformed JSON — skip", file=sys.stderr)
            continue
        ok, reason = _is_in_entity_scope(record)
        if ok:
            in_scope += 1
        else:
            oos += 1
            newly_oos.append((p.stem, record, reason))
    # Bulk-write all newly-found OOS ids
    if newly_oos:
        manifest = json.loads(MANIFEST.read_text())
        existing = set(str(i) for i in manifest.get("oos_excluded_mds_ids") or [])
        added = 0
        details = manifest.setdefault("oos_excluded_details", {})
        for nid, record, reason in newly_oos:
            if nid in existing:
                continue
            existing.add(nid)
            added += 1
            details[nid] = {
                "year_start": record.get("year_start"),
                "year_end": record.get("year_end"),
                "title": (record.get("title") or "")[:140],
                "reason": reason,
                "filtered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "scan_cache",
            }
        manifest["oos_excluded_mds_ids"] = sorted(existing, key=int)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"  added {added} ids to manifest.oos_excluded_mds_ids "
              f"(was {len(existing) - added}, now {len(existing)})")
    print(f"\nDone. in_scope={in_scope}  oos={oos}  total={len(cache_files)}")


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
