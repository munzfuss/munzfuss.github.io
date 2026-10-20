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

# Reign-level Galster index pages. Hans + Christian II + Frederik I
# are confirmed (Hans index is `/hans.htm`, NOT `/hgalst.htm`).
# Christian III pre-1541 index does NOT exist, so we walk c3g*
# per-coin pages via probe pattern in `discover`.
INDEX_PAGES = [
    "/hans.htm",
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

# Per-coin URL patterns, matched against the WHOLE href path (leading slash
# stripped). The Galster series uses single-letter «g» (vs Hede's «h»). Hans
# (1481-1513) uses several conventions: `fr/hg<N>.htm` is most common,
# `hansg<N>.htm` for the Hvid-Malmø series at root, `gotlg<N>.htm` for the
# Gotland (Visby) series, `norge/hansg<N>.htm` + `norge/nha_g<N>.htm` for
# Norway. Christian II / III + Frederik I use `(?:c|f)<digit>g<N>` under chr/ +
# fr/ + norge/ — and occasionally at the site ROOT (`c2g39.htm`, linked
# root-relative from /c2galst.htm). `rigsraad.htm` is the Rigsrådet page
# (Galster 21, 22, 81 on one page).
#
# Matched with `fullmatch` on each href, never with `finditer` over the raw
# HTML: a substring search turned `norge/hansg151.htm` into a phantom root
# `/hansg151.htm` (404) and could not tell `c2g39.htm` from `chr/c2g39.htm`.
PERCOIN_PATTERNS = [
    # chr/c2g37.htm (Christian II), fr/f1g46.htm (Frederik I), fr/hg24.htm (Hans)
    r"(?:chr|fr)/(?:c\d+|f\d+|h)g[\w\-]*\.htm",
    # norge/nc2g164.htm, norge/nc3g176.htm, norge/nf1g166.htm,
    # norge/nha_g149.htm, norge/hansg151.htm, norge/hansGej.htm
    r"norge/(?:n(?:c\d+|f\d+|ha_)g[\w\-]*|hansg\w+|hansGej)\.htm",
    # Root-level Hans Hvid (hansg31.htm) + Gotland series (gotlg143.htm)
    r"(?:hansg|gotlg)\d+[\w\-]*\.htm",
    # Root-level reign-prefixed page: c2g39.htm (Christian II, Skilling Malmø)
    r"(?:c|f)\d+g\d+[\w\-]*\.htm",
    # Rigsrådet (interregnum coinage, Galster 21 / 22 / 81)
    r"rigsraad\.htm",
    # Companion pages in artikler/ or galster/ or ernst/ subfolders
    r"(?:artikler|galster|ernst)/[\w\-]+\.htm",
]
_PERCOIN_RES = [re.compile(p, re.IGNORECASE) for p in PERCOIN_PATTERNS]

# Scope floor: Hans's accession, 1481 (same as the seed builder's YEAR_FROM).
# Galster's catalogue and danskmoent's overviews also cover the earlier
# Union kings; their per-coin pages are dropped at discovery so they never
# enter the cache:
#   * Christian I (1448-1481)        c1g<N>, chr/c1g<N>, sc1g<N> (Stockholm)
#   * Christoffer af Bayern          bajg / sbajg / fbajg<N>
#   * Erik af Pommern, Margrethe I   epomg / spomg<N>, m1g<N>
#   * Gotland gote before the Oldenburg kings: gotlg134-138 (Galster 134-138,
#     1361 - c. 1448, per the pages themselves)
# Christian I's own Gotland gote (gotlg139, gotlg140) are KEPT: Schou assigns
# Galster 140 to Christian II (gotlg140.htm), so the page is evidence for the
# 1481+ window; the seed builder dates each page by its ruler.
_PRE_1481_BASENAME_RE = re.compile(
    r"^(?:s?c1g|[sf]?bajg|[se]pomg|m1g)\d", re.IGNORECASE)
_PRE_1481_GOTLAND_MAX = 138

# Pages that match a per-coin pattern but document no real coin.
_NOT_A_COIN = {
    # Hans «1 Sølvgylden - støbt fantasimønt»: «Disse mønter, der aldrig har
    # eksisteret, men er senere fantasifostre» (fr/hg253.htm).
    "/fr/hg253.htm",
}


def _normalise_href(href: str) -> str | None:
    """Site-relative path («/chr/c2g37.htm») for a danskmoent href, or None
    for an off-site / anchor-only link."""
    href = href.strip().split("#", 1)[0].split("?", 1)[0]
    if not href:
        return None
    m = re.match(r"^https?://(?:www\.)?danskmoent\.dk/(.*)$", href, re.IGNORECASE)
    if m:
        href = m.group(1)
    elif re.match(r"^[a-z]+:", href, re.IGNORECASE):
        return None
    while href.startswith("../"):
        href = href[3:]
    return "/" + href.lstrip("/")


def _is_percoin_path(path: str) -> bool:
    rel = path.lstrip("/")
    return any(rx.fullmatch(rel) for rx in _PERCOIN_RES)


def _is_out_of_scope(path: str) -> bool:
    """True for a per-coin page before 1481 or a page that is no coin."""
    if path in _NOT_A_COIN:
        return True
    base = path.rsplit("/", 1)[-1]
    if _PRE_1481_BASENAME_RE.match(base):
        return True
    m = re.match(r"^gotlg(\d+)", base, re.IGNORECASE)
    return bool(m and int(m.group(1)) <= _PRE_1481_GOTLAND_MAX)


_HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def _make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", USER_AGENT)]
    return opener


def _try_fetch(opener, url: str, timeout: int = 30) -> str | None:
    """Fetch URL; return text on 200, None on 404 / errors."""
    try:
        body = opener.open(url, timeout=timeout).read()
        # danskmoent.dk serves ISO-8859-1 with no declared charset. Decode
        # strict UTF-8 first (a genuinely-UTF-8 page round-trips cleanly); on
        # the first non-UTF-8 byte fall back to Latin-1. NEVER decode with
        # errors="replace" before saving — "replace" silently bakes U+FFFD
        # over every raw æ/ø/å byte (0xE6/0xF8/0xE5) and destroys it, so the
        # cached .htm can no longer be re-parsed back to the correct letter.
        # (Regression fixed 2026-09-06 — mirrors fetch_hede.py._try_fetch.)
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            return body.decode("iso-8859-1")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        print(f"  [{url}] HTTP {exc.code}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  [{url}] {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def _extract_links(html: str) -> set[str]:
    """Per-coin page paths linked from a danskmoent page (index or overview).

    Index pages use <A HREF="chr/c2g37.htm">37</A> style; overviews link the
    same way. Per-coin pages may also link companion artikler/* pages that we
    track for harvest. Out-of-scope pages (pre-1481, non-coins) are NOT
    filtered here — the overview cross-ref map keeps every link it sees —
    but by the callers that decide what to fetch.
    """
    out: set[str] = set()
    for href in _HREF_RE.findall(html):
        path = _normalise_href(href)
        if path and _is_percoin_path(path):
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


def _overview_pages(opener) -> tuple[list[tuple[str, str, str]], dict]:
    """[(path, title, html), …] for every denomination overview /type.htm
    lists, read from the cache or fetched (and cached) when missing.
    Returns the list plus counters {fetched, cached, failed, listed}."""
    stats = {"fetched": 0, "cached": 0, "failed": 0, "listed": 0}
    type_cache = CACHE_DIR / _filename_for(TYPE_INDEX)
    type_html = _try_fetch(opener, BASE + TYPE_INDEX)
    time.sleep(SLEEP_SECS)
    if type_html is None:
        if not type_cache.exists():
            print(f"  {TYPE_INDEX} — not found; cannot enumerate overviews",
                  file=sys.stderr)
            return [], stats
        type_html = type_cache.read_text(encoding="utf-8")
    else:
        type_cache.write_text(type_html, encoding="utf-8")
    entries = _extract_overview_index(type_html)
    stats["listed"] = len(entries)
    out: list[tuple[str, str, str]] = []
    for path, title in entries:
        cache_file = CACHE_DIR / _filename_for(path)
        if cache_file.exists():
            html = cache_file.read_text(encoding="utf-8")
            stats["cached"] += 1
        else:
            html = _try_fetch(opener, BASE + path)
            time.sleep(SLEEP_SECS)
            if html is None:
                stats["failed"] += 1
                continue
            cache_file.write_text(html, encoding="utf-8")
            stats["fetched"] += 1
        out.append((path, title, html))
    return out, stats


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
    pages, stats = _overview_pages(opener)
    if not stats["listed"]:
        return {}
    print(f"  /type.htm: enumerated {stats['listed']} denomination-overview page(s)")

    overviews_meta: list[dict] = []
    cross_refs: dict[str, list[str]] = {}  # coin_path → [overview_paths]
    for path, title, html in pages:
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
    print(f"  Overviews fetched: {stats['fetched']} new + {stats['cached']} cached "
          f"+ {stats['failed']} failed = {len(overviews_meta)}/{stats['listed']}")
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

    # Phase 1b: per-coin links from the denomination overviews (/type.htm).
    # Several in-scope pages are linked ONLY from an overview, never from a
    # reign index — rigsraad.htm (Galster 22) from hvid.htm, the Gotland
    # pages gotlg139-147 from hvid.htm / skilling.htm, norge/nc3g176.htm
    # (no Christian III index exists), norge/nc2g173.htm from 2mark.htm.
    pages, _stats = _overview_pages(opener)
    ov_links: set[str] = set()
    for _path, _title, html in pages:
        ov_links |= _extract_links(html)
    # Only coin pages from the overviews: their artikler/ galster/ ernst/
    # links are articles (the reign-index walk keeps its own as before).
    ov_links = {ln for ln in ov_links
                if not ln.startswith(("/artikler/", "/galster/", "/ernst/"))}
    new_only = ov_links - links
    links.update(ov_links)
    index_links_per["/type.htm (overviews)"] = sorted(ov_links)
    print(f"  overviews ({len(pages)})  hits={len(ov_links):4d}  "
          f"new={len(new_only):4d}  cum={len(links)}")

    # Scope: drop pre-1481 pages and non-coins (see _is_out_of_scope).
    dropped = sorted(ln for ln in links if _is_out_of_scope(ln))
    links.difference_update(dropped)
    if dropped:
        print(f"  dropped {len(dropped)} out-of-scope page(s): {', '.join(dropped)}")

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
        "out_of_scope": dropped,
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


NARRATIVE_PAGES = ("galkult", "galtysk")   # Galster, «Danmarks Mønter» (da) + German version


def fetch_narrative(force: bool = False) -> None:
    """Cache Galster's running text (galster/galkult.htm, galtysk.htm) and a
    plain-text extract next to each, so quotes in refs_pool can be verified
    offline. These are NOT per-coin pages, so ``fetch`` never sees them."""
    import html as _html
    opener = _make_session()
    for name in NARRATIVE_PAGES:
        dst = CACHE_DIR / f"galster_{name}.htm"
        if dst.exists() and not force:
            print(f"  cached: {dst.name}")
            continue
        page = _try_fetch(opener, f"{BASE}/galster/{name}.htm")
        if not page or "Security Incident" in page[:400]:
            print(f"  ✗ {name}: not fetched", file=sys.stderr)
            continue
        dst.write_text(page, encoding="utf-8")
        txt = re.sub(r"(?is)<(script|style).*?</\1>", "", page)
        txt = re.sub(r"(?i)<br\s*/?>|</p>|</tr>|</h\d>", "\n", txt)
        txt = _html.unescape(re.sub(r"<[^>]+>", "", txt))
        txt = re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t\xa0]+", " ", txt))
        (CACHE_DIR / f"galster_{name}.extract.txt").write_text(txt, encoding="utf-8")
        print(f"  ✓ {name}: {len(page)} bytes")
        time.sleep(SLEEP_SECS)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("phase", nargs="?", default="all",
                    choices=["discover", "fetch", "overviews", "narrative", "all"])
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
    if args.phase in ("narrative", "all"):
        print("\nFetching Galster running text...")
        fetch_narrative(force=args.force)


if __name__ == "__main__":
    main()
