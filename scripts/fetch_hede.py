"""Discover and cache Hede catalogue pages from danskmoent.dk.

Hede 1971 (`Danmarks og Norges mønter 1541-1814`, plus the 19th-c.
extension) publishes a separate catalogue volume per Danish king;
danskmoent.dk hosts each entry under a URL keyed by ruler-prefix +
Hede number (e.g. `chr/c5h120.htm`, `fr/f3h62.htm`). Overview pages
group the per-ruler index (e.g. `c4hede2.htm`, `f3hede1.htm`).

Two phases:

* ``discover`` — probes the known overview-page URL space, walks each
  discovered overview's markdown, extracts the per-coin URL list,
  writes ``scripts/cache/hede/_manifest.json``.
* ``fetch`` — reads the manifest and downloads each unique URL via
  WebFetch / Apify-rag-web-browser fallback, caching the raw page as
  ``scripts/cache/hede/<basename>.md``. Skips URLs already cached.

Why the markdown is stored raw, not parsed: the per-coin pages carry
narrative numismatic data (mintage, mintmaster, edge-legend, fine-
weight notes like «Marken fin udbragt til 9,288 speciedalere») that
encodes information about the period standard but doesn't fit a
single canonical schema. Raw text lets future enrichment passes pull
whichever fields each pass needs without requiring an upfront parser.

Run all phases::

    python scripts/fetch_hede.py
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

CACHE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "cache" / "hede"
MANIFEST = CACHE_DIR / "_manifest.json"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; serhii)"
SLEEP_SECS = 0.4
BASE = "https://www.danskmoent.dk"

# Hede 1971 + extensions cover Danish kings from Christian III (1534+)
# through Christian X (-1947). Each ruler may have multiple overview
# parts (the catalogue is large enough that the per-ruler section
# is split). The probe tries every (ruler-code, part-N) combination
# and keeps the ones that respond 200.
RULER_CODES = [
    f"c{n}" for n in range(1, 11)  # c1 (Christian I) … c10 (Christian X)
] + [
    f"f{n}" for n in range(1, 10)  # f1 (Frederik I) … f9 (Frederik IX)
]
# Overview probe: empty-suffix («c4hede.htm») + parts 1..11
OVERVIEW_PARTS = [""] + [str(n) for n in range(1, 12)]

# Patterns observed live: per-coin pages live either at the root
# (e.g. /c4h115.htm) or under /chr/ (Christian) or /fr/ (Frederik)
# subfolder (e.g. /chr/c5h120.htm, /fr/f3h62.htm). Overviews use
# relative HREFs without leading slash («HREF="chr/c4h101.htm"»),
# so the leading slash is optional in the capture.


def _make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
    )
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
    """Extract per-coin URL paths from a danskmoent.dk overview page.

    Accepts markdown link form (paren after `]`), bare anchor href,
    and relative URLs. Filters to per-coin patterns (cNhM.htm /
    fNhM.htm) under root or /chr/ /fr/ subfolders. Returns paths
    normalised with a leading slash so the manifest is stable.
    """
    out: set[str] = set()
    # Markdown / HTML href patterns. The leading slash is optional in
    # the capture because overview pages use relative HREFs.
    for pat in (
        r'href=["\']((?:https?://(?:www\.)?danskmoent\.dk)?/?((?:chr/|fr/)?(?:c|f)\d+h[\w\-]*\.htm))["\']',
        r'\(((?:https?://(?:www\.)?danskmoent\.dk)?/?((?:chr/|fr/)?(?:c|f)\d+h[\w\-]*\.htm))\)',
    ):
        for m in re.finditer(pat, html, re.IGNORECASE):
            path = m.group(2)
            if not path:
                continue
            # Skip overview-patterns of any shape (cNhede.htm,
            # cNhedeP.htm) — only per-coin entries belong here.
            if re.search(r"hede\d*\.htm$", path, re.IGNORECASE):
                continue
            # Skip references to other catalogues (harck/c4hvide, etc.)
            if "/" in path and not path.startswith(("chr/", "fr/")):
                continue
            out.add("/" + path)
    return out


def _filename_for(url_path: str) -> str:
    """Cache filename: just the basename. cNhM / fNhM stems are
    globally unique across the danskmoent.dk Hede directory, so the
    subfolder («/chr/», «/fr/») can be dropped without collision."""
    return Path(url_path).name


def discover() -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    opener = _make_session()
    overviews_found: list[str] = []
    links: set[str] = set()
    overview_links_per: dict[str, list[str]] = {}

    for code in RULER_CODES:
        misses_in_a_row = 0
        for part in OVERVIEW_PARTS:
            path = f"/{code}hede{part}.htm"
            url = BASE + path
            html = _try_fetch(opener, url)
            time.sleep(SLEEP_SECS)
            if html is None:
                misses_in_a_row += 1
                # After 2 consecutive 404s past part 2 we assume the
                # ruler's overview series ends; move on to the next.
                if misses_in_a_row >= 2 and part not in ("", "1"):
                    break
                continue
            misses_in_a_row = 0
            overviews_found.append(path)
            new_links = _extract_links(html)
            overview_links_per[path] = sorted(new_links)
            new_only = new_links - links
            links.update(new_links)
            print(
                f"  /{code}hede{part or ''}.htm  hits={len(new_links):4d}  "
                f"new={len(new_only):4d}  cum={len(links)}",
            )

    # Also save the overview HTML/markdown contents for record
    overview_cache = {}
    for path in overviews_found:
        url = BASE + path
        html = _try_fetch(opener, url)
        if html:
            (CACHE_DIR / Path(path).name).write_text(html, encoding="utf-8")
            overview_cache[path] = Path(path).name
        time.sleep(SLEEP_SECS)

    manifest = {
        "overviews": overviews_found,
        "overview_files": overview_cache,
        "overview_links_per": overview_links_per,
        "links": sorted(links),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"\nDiscovered: {len(overviews_found)} overviews, {len(links)} per-coin links")
    print(f"Manifest → {MANIFEST}")
    return manifest


def fetch() -> None:
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    links: list[str] = manifest["links"]
    opener = _make_session()
    fetched = 0
    skipped = 0
    errors = 0
    t0 = time.time()
    for i, link in enumerate(links, start=1):
        fname = _filename_for(link)
        target = CACHE_DIR / fname
        if target.exists():
            skipped += 1
            continue
        url = BASE + link if link.startswith("/") else link
        text = _try_fetch(opener, url, timeout=45)
        if text is None:
            errors += 1
            print(f"  [{link}] failed", file=sys.stderr)
            continue
        target.write_text(text, encoding="utf-8")
        fetched += 1
        time.sleep(SLEEP_SECS)
        if i % 50 == 0:
            elapsed = int(time.time() - t0)
            remaining = len(links) - i
            print(
                f"  progress {i}/{len(links)}  fetched={fetched}  skipped={skipped}  "
                f"errors={errors}  elapsed={elapsed}s  remaining≈{int(remaining * SLEEP_SECS)}s",
            )
    print(
        f"\nDone. fetched={fetched} skipped={skipped} errors={errors} "
        f"out of {len(links)} ({int(time.time() - t0)}s).",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", nargs="?",
                    choices=["discover", "fetch", "both"], default="both")
    args = ap.parse_args()
    if args.phase in ("discover", "both"):
        discover()
    if args.phase in ("fetch", "both"):
        fetch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
