"""Harvest KMM object pages from the natmus.dk WEB rådata surface — §DB.

Background (docs/TODO.md §DB): the old ES endpoint
`api.natmus.dk/search/public/raw` that `fetch_kmk.py` used returned HTTP 403
«Site Disabled» (natmus.dk took the public raw ES down), AND a large subset of
our cached ES `_source` records carry `typeNumber: None` + `descriptions: []`
— no catalogue index. The public WEB object page
(`samlinger.natmus.dk/KMM/object/<id>`) is still live and — crucially —
SERVER-RENDERS the catalogue into a plain `<div id="description">` element
(no JS needed), e.g.

    <div id="description">to mark<br/><br/>Bech nr. 876; B 783.a; Sch 3a</div>

so a coin whose ES cache has no catalogue can still be recovered from the web
page. This script is the Phase-1 harvest half of the §DB workaround: given a
list of numeric object ids, it fetches each object's web page to
`scripts/cache/kmk/web/<id>.html` (skip-if-cached, polite rate). The catalogue
extraction (parse the `<div id="description">` → schou / others[]) lives in the
seed-builder half; `extract_description()` here is the shared parser so a
caller can preview the yield without re-fetching.

Usage:
    python scripts/fetch_kmk_web.py 86272 290909 137178      # explicit ids
    python scripts/fetch_kmk_web.py --file ids.json          # JSON list of ids
    python scripts/fetch_kmk_web.py --preview 86272          # fetch + print desc

The full §DB migration (scope re-discovery off the dead ES manifest, wiring
`beskrivelser` into build_kmk_seed._catalog for a bulk re-seed) is still open;
this script is the reusable fetch + description-parser those steps build on.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import KMK_CACHE  # noqa: E402

WEB_CACHE = KMK_CACHE / "web"
OBJECT_URL = "https://samlinger.natmus.dk/KMM/object/{id}"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; serhii)"
SLEEP_SECS = 0.4

_DESC_RE = re.compile(r'<div id="description">(.*?)</div>', re.S)


def fetch_page(obj_id: int | str, *, force: bool = False) -> str:
    """Fetch (or read from cache) the KMM object web page HTML."""
    WEB_CACHE.mkdir(parents=True, exist_ok=True)
    dest = WEB_CACHE / f"{obj_id}.html"
    if dest.exists() and dest.stat().st_size > 1000 and not force:
        return dest.read_text("utf-8")
    req = urllib.request.Request(OBJECT_URL.format(id=obj_id), headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    dest.write_text(html, "utf-8")
    time.sleep(SLEEP_SECS)
    return html


def extract_description(html: str) -> str:
    """Return the plain-text content of the page's <div id="description">
    (nominal + catalogue refs, `  |  `-joined across the source's <br/>s)."""
    m = _DESC_RE.search(html)
    if not m:
        return ""
    txt = re.sub(r"<br\s*/?>", "  |  ", m.group(1))
    txt = re.sub(r"<[^>]+>", "", txt)
    return txt.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids", nargs="*", help="numeric KMM object ids")
    ap.add_argument("--file", help="JSON file holding a list of ids")
    ap.add_argument("--force", action="store_true", help="refetch even if cached")
    ap.add_argument("--preview", action="store_true", help="print each description div")
    args = ap.parse_args()

    ids = list(args.ids)
    if args.file:
        ids += [str(x) for x in json.load(open(args.file))]
    if not ids:
        ap.error("no ids given (positional or --file)")

    for n, i in enumerate(ids, 1):
        try:
            html = fetch_page(i, force=args.force)
            if args.preview:
                print(f"{i:8} {extract_description(html)[:120]!r}")
        except Exception as e:  # noqa: BLE001
            print(f"{i:8} ERR {e}", file=sys.stderr)
        if not args.preview and n % 25 == 0:
            print(f"  fetched {n}/{len(ids)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
