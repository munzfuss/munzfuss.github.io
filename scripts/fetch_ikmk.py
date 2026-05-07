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

CACHE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "cache" / "ikmk"
MANIFEST = CACHE_DIR / "_manifest.json"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; serhii)"
SLEEP_SECS = 0.5

QUERIES = [
    # Schleswig-Holstein and territorial duchies
    "Schleswig-Holstein", "Holstein", "Schleswig",
    "Holstein-Sonderburg", "Holstein-Sonderburg-Glücksburg",
    "Sonderburg", "Augustenburg", "Plön", "Glücksburg", "Norburg",
    # SH mints / cities
    "Glückstadt", "Altona", "Reinfeld", "Eutin", "Kiel", "Flensburg",
    # Lübeck-bishopric (project scope)
    "Lübeck Bistum",
    # Denmark + Norway (Danish-Norwegian crown)
    "Dänemark", "Denmark", "Norwegen", "Norge",
    "Kopenhagen", "Christiania", "Kongsberg",
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


def _fetch_one(opener, nid: str) -> bool:
    path = CACHE_DIR / f"{nid}.json"
    if path.exists():
        return False
    url = f"https://ikmk.smb.museum/object?id={nid}&download=json_ext"
    body = opener.open(url, timeout=30).read()
    path.write_bytes(body)
    return True


def fetch() -> None:
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    ids: list[str] = manifest["ids"]
    opener = _make_session()
    fetched = 0
    skipped = 0
    errors = 0
    t0 = time.time()
    for i, nid in enumerate(ids, start=1):
        try:
            new = _fetch_one(opener, nid)
        except urllib.error.HTTPError as exc:
            errors += 1
            print(f"  [{nid}] HTTP {exc.code}", file=sys.stderr)
            time.sleep(2.0)
            continue
        except Exception as exc:
            errors += 1
            print(f"  [{nid}] {type(exc).__name__}: {exc}", file=sys.stderr)
            time.sleep(2.0)
            continue
        if new:
            fetched += 1
            time.sleep(SLEEP_SECS)
        else:
            skipped += 1
        if i % 50 == 0:
            elapsed = int(time.time() - t0)
            remaining = len(ids) - i
            print(
                f"  progress {i}/{len(ids)}  fetched={fetched}  skipped={skipped}  "
                f"errors={errors}  elapsed={elapsed}s  remaining≈{int(remaining * SLEEP_SECS)}s",
            )
    print(
        f"\nDone. fetched={fetched} skipped={skipped} errors={errors} "
        f"out of {len(ids)} ({int(time.time() - t0)}s).",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "phase",
        nargs="?",
        choices=["discover", "fetch", "both"],
        default="both",
    )
    args = ap.parse_args()
    if args.phase in ("discover", "both"):
        discover()
    if args.phase in ("fetch", "both"):
        fetch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
