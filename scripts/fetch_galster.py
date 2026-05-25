"""Discover and cache Galster catalog pages from danskmoent.dk.

The danskmoent.dk site hosts a Galster-numbered series of per-coin
pages for pre-Christian-III rulers (the gap §BI's 1514 anchor opened
+ §BJ source-survey confirmed: Hede 1957 monograph starts at Christian
III 1541, so Galster is the primary structured-data source for the
1514-1540 sub-window). URL patterns confirmed in §BJ survey:

  * Reign-level indexes: /c2galst.htm (Christian II), /f1galst.htm
    (Frederik I). /c3galst.htm does NOT exist (HTTP 404) — Christian
    III pre-1541 pages are enumerated via /chr/c3g<N>.htm directly.
  * Per-coin pages: /chr/c<N>g<NUM>.htm (Christian rulers) +
    /fr/f<N>g<NUM>.htm (Frederik rulers) + /norge/n<r>g<NUM>.htm
    (Norway sub-series under each ruler).
  * Page data shape (per /fr/f1g46.htm sample):
      <ruler>, <denomination> <year> <mint>
      Forside: ... Bagside: ... (Galster N, Schou N, Jensen/Skjoldager X)
      Bruttovægt: X g
      Finhed: X
      Finvægt: X g
      Inscription + translation
      Litteratur: ... refs ...

Three phases:

* ``discover`` — fetches /c2galst.htm + /f1galst.htm, extracts all
  per-coin Galster page URLs from their tables, writes
  ``scripts/cache/danskmoent/galster/_manifest.json``.
* ``fetch`` — reads the manifest and downloads each unique URL,
  caching the raw page as ``scripts/cache/danskmoent/galster/<basename>.htm``.
  Skips URLs already cached.
* ``overviews`` — fetches /type.htm (the Pålydende master index of
  denomination overviews) + each root-level overview page it lists
  (1nobel.htm, guldgyld.htm, 2skill.htm, …), then extracts cross-refs
  from each overview to per-coin pages. Writes
  ``_overview_cross_refs.json`` keyed by coin_path with the list of
  overview URLs that mention it. Consumed by
  ``build_galster_denmark_seed.py`` to enrich each per-coin entry's
  ``sources[]`` with denomination-overview attestations.

Run all phases::

    .venv/bin/python scripts/fetch_galster.py
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import GALSTER_CACHE as CACHE_DIR  # noqa: E402

MANIFEST = CACHE_DIR / "_manifest.json"
OVERVIEW_MANIFEST = CACHE_DIR / "_overview_cross_refs.json"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; non-commercial scholarly register)"
SLEEP_SECS = 0.4
BASE = "https://www.danskmoent.dk"

# Reign-level Galster index pages. Christian II + Frederik I are
# confirmed (§BJ); Christian III index does NOT exist, so we walk
# c3g* per-coin pages via probe pattern in `discover`.
INDEX_PAGES = [
    "/c2galst.htm",
    "/f1galst.htm",
]

# Denomination-overview master index page. Each entry links to a
# root-level overview page (1nobel.htm, guldgyld.htm, 2skill.htm, …)
# that documents one denomination across multiple rulers, with hyper-
# links back to specific per-coin pages. The harvester walks this
# master index, fetches each overview, and extracts cross-refs from
# each overview to per-coin pages. The result populates a
# `coin_path → [overview_paths]` map used by the Galster builder to
# enrich per-coin entries' `sources[]` with denomination-overview
# attestations. (Surfaced 2026-05-25 — danskmoent.dk/1nobel.htm
# overview was not previously visited, so Frederik I Ribe Nobel
# entries lacked the overview cross-ref despite being listed there.)
TYPE_INDEX = "/type.htm"

# Per-coin URL patterns to extract from index pages. The Galster
# series uses single-letter «g» (vs Hede's «h»). Mirroring fetch_hede.py.
PERCOIN_PATTERNS = [
    # Standard: chr/c2g37.htm, fr/f1g46.htm
    r"((?:chr|fr)/(?:c|f)\d+g[\w\-]*\.htm)",
    # Norway sub-folder: norge/nc2g164.htm, norge/nf1g166.htm
    r"(norge/n(?:c|f)\d+g[\w\-]*\.htm)",
    # Some pages live at root or in artikler/ or galster/ subfolders
    r"((?:artikler|galster|ernst)/[\w\-]+\.htm)",
]


def _make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", USER_AGENT)]
    return opener


def _try_fetch(opener, url: str, timeout: int = 30) -> str | None:
    """Fetch URL; return text on 200, None on 404 / errors."""
    try:
        body = opener.open(url, timeout=timeout).read()
        try:
            return body.decode("utf-8", "replace")
        except Exception:
            return body.decode("iso-8859-1", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        print(f"  [{url}] HTTP {exc.code}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  [{url}] {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def _extract_links(html: str) -> set[str]:
    """Extract per-coin URL paths from a Galster index page.

    Index pages use <A HREF="chr/c2g37.htm">37</A> style. Per-coin
    pages may also link to companion artikler/* pages (Ernst, Moesgaard
    pdfs etc.) that we want to track for harvest.
    """
    out: set[str] = set()
    for pat in PERCOIN_PATTERNS:
        for m in re.finditer(pat, html, re.IGNORECASE):
            path = m.group(1)
            # Normalise leading slash
            if not path.startswith("/"):
                path = "/" + path
            out.add(path)
    return out


def _filename_for(url_path: str) -> str:
    """Cache filename: subfolder + basename joined by underscore so
    that chr/c2g37.htm + norge/nc2g37.htm don't collide on basename."""
    path = url_path.lstrip("/")
    return path.replace("/", "_")


# Hyperlink + visible-text extractor for the /type.htm master index.
# Each row links a denomination overview page (root-level, e.g.
# `1nobel.htm`) with a human-readable title («1 Nobel»). The harvester
# uses this to (a) enumerate the overview-page URL set, (b) attach
# a human-readable title to each overview for the source-ref text.
_TYPE_INDEX_LINK_RE = re.compile(
    r'<a\s+href="([^"]+\.htm)"[^>]*>([^<]+)</a>',
    re.IGNORECASE,
)


def _extract_overview_index(html: str) -> list[tuple[str, str]]:
    """Parse /type.htm master index into [(path, title), …].

    Filters to ROOT-LEVEL overview pages only (single .htm at root —
    e.g. `1nobel.htm`, `guldgyld.htm`). Sub-directory links
    (`fr/f1g68.htm`, `chr/c2g37.htm`, `norge/nc2g165.htm`, `falske/*`)
    are NOT overviews — they're individual coin pages that some
    denominations co-list (typically for rare one-off coins where
    no overview exists). Self-link to /type.htm and the navigation
    /index.htm are excluded.
    """
    excluded_basenames = {"type.htm", "index.htm"}
    seen_paths: set[str] = set()
    out: list[tuple[str, str]] = []
    for href, text in _TYPE_INDEX_LINK_RE.findall(html):
        href = href.strip()
        text = text.strip()
        # Strip any leading slash and skip subdirectory links
        norm = href.lstrip("/")
        if "/" in norm:
            continue
        if norm in excluded_basenames:
            continue
        path = "/" + norm
        if path in seen_paths:
            # Same path linked from multiple rows (e.g. 1mark.htm
            # appears as both «1 Mark/16 Skilling» and «16 Skilling/1 Mark»).
            # Keep the first-seen title (alphabetical-order in /type.htm
            # tends to favour the canonical denomination form).
            continue
        seen_paths.add(path)
        out.append((path, text))
    return out


def discover_overviews() -> dict:
    """Fetch /type.htm master index, enumerate denomination-overview
    pages, fetch each one, and extract cross-refs from each overview
    to per-coin pages.

    Writes `_overview_cross_refs.json` with:
      {
        "overviews": [{"path": ..., "title": ..., "cache_file": ...}],
        "cross_refs": {coin_path: [overview_path, …], …},
        "fetched_at": "..."
      }

    The cross_refs map is read by `build_galster_denmark_seed.py`
    (and any sibling builder) to add denomination-overview URLs to
    each per-coin entry's `sources[]`.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    opener = _make_session()

    # Phase 1 — fetch /type.htm master index
    type_url = BASE + TYPE_INDEX
    type_html = _try_fetch(opener, type_url)
    time.sleep(SLEEP_SECS)
    if type_html is None:
        print(f"  {TYPE_INDEX} — not found; cannot enumerate overviews", file=sys.stderr)
        return {}
    type_cache = CACHE_DIR / _filename_for(TYPE_INDEX)
    type_cache.write_text(type_html, encoding="utf-8")

    overview_entries = _extract_overview_index(type_html)
    print(f"  /type.htm: enumerated {len(overview_entries)} denomination-overview page(s)")

    # Phase 2 — fetch each overview page + extract its cross-refs
    overviews_meta: list[dict] = []
    cross_refs: dict[str, list[str]] = {}  # coin_path → [overview_paths]
    fetched_now = 0
    cached_already = 0
    failed = 0
    for path, title in overview_entries:
        cache_file = CACHE_DIR / _filename_for(path)
        if cache_file.exists():
            html = cache_file.read_text(encoding="utf-8")
            cached_already += 1
        else:
            url = BASE + path
            html = _try_fetch(opener, url)
            time.sleep(SLEEP_SECS)
            if html is None:
                failed += 1
                continue
            cache_file.write_text(html, encoding="utf-8")
            fetched_now += 1
        overviews_meta.append({
            "path": path,
            "title": title,
            "cache_file": _filename_for(path),
        })
        # Extract cross-refs from this overview's body. _extract_links
        # captures per-coin paths under chr/, fr/, norge/, artikler/,
        # galster/, ernst/ — i.e. exactly the per-coin URL shapes the
        # rest of this harvester already knows. Self-links (an overview
        # linking to itself or to another overview) are filtered by
        # the existing patterns since overviews live at root level.
        for coin_path in _extract_links(html):
            cross_refs.setdefault(coin_path, []).append(path)

    # Deduplicate + sort each cross-ref list (an overview may appear
    # twice on a coin page via duplicate links).
    cross_refs_sorted = {cp: sorted(set(ops)) for cp, ops in cross_refs.items()}

    manifest = {
        "overviews": overviews_meta,
        "cross_refs": cross_refs_sorted,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OVERVIEW_MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Overviews fetched: {fetched_now} new + {cached_already} cached "
          f"+ {failed} failed = {len(overviews_meta)}/{len(overview_entries)}")
    print(f"  Cross-refs: {len(cross_refs_sorted)} per-coin pages have "
          f"≥1 overview backref")
    print(f"  Manifest written: {OVERVIEW_MANIFEST.name}")
    return manifest


def discover() -> dict:
    """Walk index pages, extract per-coin URL list, plus probe for
    Christian III pre-1541 g-pages that aren't in any index."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    opener = _make_session()

    indexes_found: list[str] = []
    links: set[str] = set()
    index_links_per: dict[str, list[str]] = {}

    # Phase 1: walk known index pages
    for path in INDEX_PAGES:
        url = BASE + path
        html = _try_fetch(opener, url)
        time.sleep(SLEEP_SECS)
        if html is None:
            print(f"  {path} — not found", file=sys.stderr)
            continue
        # Save raw index page
        (CACHE_DIR / _filename_for(path)).write_text(html, encoding="utf-8")
        indexes_found.append(path)
        new_links = _extract_links(html)
        # Filter: drop links to other ruler indexes themselves
        new_links = {ln for ln in new_links if "galst" not in ln.lower()}
        index_links_per[path] = sorted(new_links)
        new_only = new_links - links
        links.update(new_links)
        print(f"  {path}  hits={len(new_links):4d}  new={len(new_only):4d}  cum={len(links)}")

    # Phase 2: probe Christian III pre-Møntordning Galster pages directly
    # (no index page exists for Christian III pre-1541; per the survey,
    # Galster numbers 92-130 cover Grevens Fejde 1534-36 + 1537
    # Joachimsdaler + pre-1541 issues). Probe range 92-135 to be safe.
    print("\n  Probing Christian III pre-1541 Galster pages (92-135)...")
    c3_hits = 0
    for n in range(92, 136):
        path = f"/chr/c3g{n}.htm"
        # Skip if already known
        if path in links:
            continue
        url = BASE + path
        html = _try_fetch(opener, url)
        time.sleep(SLEEP_SECS)
        if html is None:
            continue
        links.add(path)
        c3_hits += 1
    print(f"  Christian III probe — {c3_hits} new pages found")

    manifest = {
        "indexes": indexes_found,
        "index_files": {p: _filename_for(p) for p in indexes_found},
        "index_links_per": index_links_per,
        "links": sorted(links),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\n  Manifest written: {len(links)} per-coin URLs across {len(indexes_found)} index pages.")
    return manifest


def fetch_all(force: bool = False) -> None:
    """Read manifest, fetch all per-coin pages not yet cached."""
    if not MANIFEST.exists():
        print("Manifest missing — run `discover` first.", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    opener = _make_session()
    total = len(manifest["links"])
    fetched = 0
    skipped = 0
    failed = 0
    for i, path in enumerate(manifest["links"], 1):
        fname = _filename_for(path)
        out_path = CACHE_DIR / fname
        if out_path.exists() and not force:
            skipped += 1
            continue
        url = BASE + path
        html = _try_fetch(opener, url)
        time.sleep(SLEEP_SECS)
        if html is None:
            failed += 1
            continue
        out_path.write_text(html, encoding="utf-8")
        fetched += 1
        if i % 25 == 0 or i == total:
            print(f"  [{i:4d}/{total}] fetched={fetched} skipped={skipped} failed={failed}")
    print(f"\n  Done: fetched={fetched}, skipped={skipped}, failed={failed}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("phase", nargs="?", default="all",
                    choices=["discover", "fetch", "overviews", "all"])
    ap.add_argument("--force", action="store_true", help="Re-fetch already-cached pages")
    args = ap.parse_args()

    if args.phase in ("discover", "all"):
        print(f"Discovering Galster pages in {CACHE_DIR}...")
        discover()
    if args.phase in ("fetch", "all"):
        print(f"\nFetching per-coin pages...")
        fetch_all(force=args.force)
    if args.phase in ("overviews", "all"):
        print(f"\nDiscovering denomination-overview pages...")
        discover_overviews()


if __name__ == "__main__":
    main()
