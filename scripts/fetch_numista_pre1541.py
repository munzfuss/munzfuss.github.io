"""§AZ Tier 3 — fetch Numista per-coin HTML pages for the 1514-1541
Danish-Norwegian realm sub-window.

Polite HTML scraping (NOT the Numista v3 API — the «Numista API budget»
rule per CLAUDE.md targets api.numista.com quota; this script hits the
public HTML catalog at en.numista.com which has no per-coin request
budget). Long pauses between fetches (default 30s) per user direction
2026-05-16. Each page is saved as raw HTML to
scripts/cache/numista/denmark_pre_1541/n<N#>.html.

N# list compiled from:
  - User-provided Numista catalog inventory snapshot 2026-05-16 (in
    §BJ TODO entry, since closed)
  - 4 Norwegian entries surfaced during Chrome MCP browse 2026-05-16

Run:
    .venv/bin/python scripts/fetch_numista_pre1541.py [--sleep N]
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "cache" / "numista" / "denmark_pre_1541"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) "
    "Gecko/20100101 Firefox/121.0"
)
BASE = "https://en.numista.com"

# Denmark pre-1541 — Christian II + Frederik I + Christian III pre-1541
# Currency «Gulden (1513-1572)». 1541 boundary issues included for
# Hede cross-validation (Hede-3A/4A/5A/7/8 coverage check).
DENMARK_NUMS = [
    # Christian II 1513-1523 (7 entries)
    264676,  # Blaffert C2/C3 ND 1513-1559
    153125,  # 1 Skilling Malmo type 1 1514-1515
    297656,  # 18 Penning Klippingar 1518-1522
    108782,  # 1 Sølvgylden Malmo 1518-1523
    428876,  # 1 Noble 1516-1518
    # Frederik I 1523-1533 (16 entries)
    301237,  # 2 Schillings Husum portrait first 1514-1522
    301239,  # 2 Schillings Husum portrait second 1514-1522
    152267,  # Lejrskilling 10 Hvid 1523-1524
    153173,  # 8 Skilling/Halvmark Malmo 1523-1532
    153257,  # 2 Schillings Gottorp 1523-1533
    301177,  # 1 Søsling type 3 date-in-legend 1524
    301174,  # 1 Søsling type 3 date-over-shield 1524
    433743,  # 1 Goldgulden Malmö 1527
    476713,  # 1 Mark 1529
    476705,  # 1/2 Sølvgylden 1531
    428864,  # 1 Goldgulden 1531
    152639,  # 8 Skilling/Halvmark Copenhagen 1532
    476708,  # 1/4 Sølvgylden 1532
    476697,  # 1/2 Sølvgylden 1532 Pillars
    476698,  # 1/2 Sølvgylden 1532 Statues
    476687,  # 1 Sølvgylden 1532
    476691,  # 1 1/2 Sølvgylden 1532
    428544,  # 1 Noble 1532
    # Christian III 1534-1541 (24 entries)
    461448,  # 1 Ducat Gottorp ND 1534
    153825,  # 2 Schillings Gottorp 1534-1537
    476671,  # 4 Skilling Klipping 1535
    476674,  # 4 Skilling Aarhus heavy 1535
    301375,  # 4 Skilling Aarhus light 1535
    474591,  # 4 Skilling Copenhagen 1535
    476659,  # 4 Skilling Ribe 1535
    152059,  # 4 Skilling Roskilde 1535
    476670,  # 8 Skilling Klipping 1535
    476681,  # 1 Mark Roskilde 1535
    476668,  # 2 Mark Klipping 1535
    476678,  # 2 Mark 1535
    84844,   # 1 Skilling Copenhagen 1536
    474604,  # 1 Skilling Ribe 1536
    476676,  # 2 Skilling Aarhus 1536
    152060,  # 2 Skilling Copenhagen 1536
    476662,  # 2 Skilling Ribe 1536
    476684,  # 2 Skilling Roskilde 1536
    474581,  # 1/2 Joachimstaler 1537
    474577,  # 1 Joachimstaler 1537 (28.75g)
    474583,  # 1 Joachimstaler 1537 (36.31g)
    474250,  # 4 Skilling 1541 (Hede-5A boundary)
    474248,  # 8 Skilling 1541 (Hede-4A boundary)
    474245,  # 1 Mark 1541 (Hede-3A boundary)
    386681,  # 2 Ducats 1541 (no Hede)
    # Norway sub-realm 1514-1541 (8 entries, added 2026-05-16)
    110323,  # 1 Skilling Christian II Oslo 1513-1523
    124914,  # 1 Skilling Christian II ND 1513-1523
    120175,  # 1 Skilling Frederik I Bergen 1524-1533
    121754,  # 1 Skilling Frederik I Oslo 1524-1533
    477551,  # 1 Skilling Frederik I Oslo 1525
    444429,  # 1 Skilling Frederik I Oslo 1531
    444496,  # 1 Skilling Christian III Oslo 1535
    121758,  # 1 Skilling Christian III Bergen 1533-1537
]


def _make_session():
    """Build urllib opener with cookie support + polite UA."""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ("User-Agent", USER_AGENT),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "en-US,en;q=0.5"),
        ("Accept-Encoding", "identity"),  # no compression — keep parse simple
    ]
    return opener


def fetch_one(opener, nid: int) -> str | None:
    url = f"{BASE}/{nid}"
    try:
        with opener.open(url, timeout=20) as r:
            body = r.read()
            try:
                return body.decode("utf-8", "replace")
            except Exception:
                return body.decode("iso-8859-1", "replace")
    except urllib.error.HTTPError as exc:
        print(f"  [{nid}] HTTP {exc.code}", file=sys.stderr)
        if exc.code == 403:
            print(f"  [{nid}] Cloudflare 403 — anti-bot likely. Stopping.", file=sys.stderr)
            return "STOP"
        return None
    except Exception as exc:
        print(f"  [{nid}] {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleep", type=int, default=30, help="Pause between fetches (seconds)")
    ap.add_argument("--limit", type=int, default=None, help="Stop after N pages")
    ap.add_argument("--start", type=int, default=0, help="Start at index N in the list")
    args = ap.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    opener = _make_session()

    nums = DENMARK_NUMS[args.start :]
    if args.limit:
        nums = nums[: args.limit]

    fetched = 0
    skipped = 0
    failed = 0
    stopped = False
    t0 = time.time()

    for i, nid in enumerate(nums, 1):
        out_path = CACHE_DIR / f"n{nid}.html"
        if out_path.exists():
            skipped += 1
            print(f"  [{i:3d}/{len(nums)}] n{nid} — cached (skip)")
            continue
        html = fetch_one(opener, nid)
        if html == "STOP":
            stopped = True
            print(f"  Cloudflare anti-bot triggered. Resume conditions in docs/SOURCES.md §13.1.")
            break
        if html is None:
            failed += 1
            continue
        out_path.write_text(html, encoding="utf-8")
        fetched += 1
        elapsed = time.time() - t0
        print(
            f"  [{i:3d}/{len(nums)}] n{nid} — fetched {len(html)} bytes "
            f"(cum: fetched={fetched} skipped={skipped} failed={failed}; "
            f"elapsed={elapsed:.0f}s)"
        )
        if i < len(nums):
            time.sleep(args.sleep)

    elapsed = time.time() - t0
    print(
        f"\nDone in {elapsed:.0f}s: fetched={fetched}, skipped={skipped}, "
        f"failed={failed}{', STOPPED' if stopped else ''}"
    )
    return 1 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
