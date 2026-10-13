"""Cache danskmoent.dk's «Forordninger m.v. vedr. Møntvæsenet under
Enevælden» — Mordhorst, *Dansk Pengehistorie* III (Bilag), pp. 159-264,
transcribed one page per reign.

Source of the coinage-instrument TEXTS for 1661-1849 (the register in
docs/research/ordinances_register.md needs the act, not a retelling):

    artikler/mord.htm     index (what is transcribed, update notes)
    artikler/f3mord.htm   Frederik 3.   1661-1670
    artikler/c5mord.htm   Christian 5.  1670-1699
    artikler/f4mord.htm   Frederik 4.   1699-1730
    artikler/c6mord.htm   Christian 6.  1730-1746
    artikler/f5mord.htm   Frederik 5.   1746-1766
    artikler/c7mord.htm   Christian 7.  1766-1808
    artikler/f6mord.htm   Frederik 6.   1808-1839
    artikler/c8mord.htm   Christian 8.  1839-1848
    artikler/f7mord.htm   Frederik 7.   1848-1849

Cached raw as ``scripts/cache/danskmoent/mord/<basename>.htm``; a page the
site has not transcribed yet (HTTP 404) is recorded in ``_manifest.json``
so the next run knows it was tried. Re-runnable; ``--force`` re-downloads.

    .venv/bin/python scripts/fetch_danskmoent_mord.py [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import MORD_CACHE as CACHE_DIR  # noqa: E402

BASE = "https://www.danskmoent.dk/artikler/"
PAGES = ["mord", "f3mord", "c5mord", "f4mord", "c6mord",
         "f5mord", "c7mord", "f6mord", "c8mord", "f7mord"]
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; non-commercial scholarly register)"
SLEEP_SECS = 0.5


def _fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        body = urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    # Same decode discipline as fetch_galster._try_fetch: strict UTF-8 first,
    # Latin-1 on failure, never errors="replace" (it destroys æ/ø/å bytes).
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("iso-8859-1")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = CACHE_DIR / "_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name in PAGES:
        out = CACHE_DIR / f"{name}.htm"
        if out.exists() and not args.force:
            print(f"  cached  {name}.htm")
            continue
        html = _fetch(BASE + f"{name}.htm")
        if html is None:
            manifest[name] = {"status": 404, "tried": date.today().isoformat()}
            print(f"  404     {name}.htm")
        else:
            out.write_text(html, encoding="utf-8")
            manifest[name] = {"status": 200, "fetched": date.today().isoformat(),
                              "bytes": len(html.encode("utf-8"))}
            print(f"  fetched {name}.htm ({len(html)} chars)")
        time.sleep(SLEEP_SECS)
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
