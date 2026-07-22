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
import html as _html
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


def fetch_raadata(obj_id: int | str, *, force: bool = False,
                  sleep_secs: float = SLEEP_SECS) -> dict | None:
    """Bulk-mode fetch (§DB Phase-1, variant «б»): fetch the object page,
    extract its embedded rådata JSON, and persist ONLY that verbatim record as
    `web/<id>.json` (~3 KB vs ~28 KB HTML — the rådata IS the museum's source
    record; the surrounding HTML is site chrome). Full HTML is stored as
    `web/<id>.html` ONLY when the rådata parse fails (fallback «а», so the raw
    page survives for a later parser fix). Skip-if-cached on either artefact.
    Returns the rådata dict, or None (no rådata found / fetch error)."""
    WEB_CACHE.mkdir(parents=True, exist_ok=True)
    jdest = WEB_CACHE / f"{obj_id}.json"
    hdest = WEB_CACHE / f"{obj_id}.html"
    if not force:
        if jdest.exists() and jdest.stat().st_size > 2:
            try:
                return json.loads(jdest.read_text("utf-8"))
            except json.JSONDecodeError:
                pass  # corrupt sidecar → refetch
        if hdest.exists() and hdest.stat().st_size > 1000:
            return parse_raadata(hdest.read_text("utf-8"))
    req = urllib.request.Request(OBJECT_URL.format(id=obj_id), headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    rd = parse_raadata(html)
    if rd is not None:
        jdest.write_text(json.dumps(rd, ensure_ascii=False, indent=1), "utf-8")
    else:
        hdest.write_text(html, "utf-8")   # fallback «а»: keep the raw page
    time.sleep(sleep_secs)
    return rd


def extract_description(html: str) -> str:
    """Return the plain-text content of the page's <div id="description">
    (nominal + catalogue refs, `  |  `-joined across the source's <br/>s)."""
    m = _DESC_RE.search(html)
    if not m:
        return ""
    txt = re.sub(r"<br\s*/?>", "  |  ", m.group(1))
    txt = re.sub(r"<[^>]+>", "", txt)
    return txt.strip()


def parse_raadata(html: str) -> dict | None:
    """Extract the object's embedded rådata JSON from the page.

    The KMM object page renders a full structured record (Danish-keyed:
    `beskrivelser` / `maalinger` / `haendelser` / `materialer` /
    `identifikation` …) into the «Rådata» section as HTML-escaped JSON. This
    is a strictly richer source than `extract_description()` (which only sees
    `beskrivelser`), so the seed builder consults it for weight / year / mint /
    catalogue at once. Returns the parsed dict, or None if not found /
    unparseable."""
    i = html.find("Rådata")
    if i < 0:
        return None
    seg = html[i:i + 20000]
    j = seg.find("{")
    if j < 0:
        return None
    depth = 0
    in_str = esc = False
    end = None
    for k in range(j, len(seg)):
        ch = seg[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = k + 1
                break
    if end is None:
        return None
    try:
        return json.loads(_html.unescape(seg[j:end]))
    except (json.JSONDecodeError, ValueError):
        return None


def load_raadata(obj_id: int | str) -> dict | None:
    """Return the rådata dict for a cached object (None if nothing cached or
    no parseable rådata). Read-only — never fetches. Prefers the `<id>.json`
    verbatim sidecar (bulk variant «б»); falls back to parsing `<id>.html`."""
    jdest = WEB_CACHE / f"{obj_id}.json"
    if jdest.exists():
        try:
            return json.loads(jdest.read_text("utf-8"))
        except json.JSONDecodeError:
            pass
    dest = WEB_CACHE / f"{obj_id}.html"
    if not dest.exists():
        return None
    return parse_raadata(dest.read_text("utf-8"))


def _bulk_fetch(ids: list[str], workers: int, sleep_secs: float,
                force: bool) -> int:
    """§DB Phase-1 bulk mode: fetch rådata JSON sidecars for `ids` with a
    small thread pool. Prints a progress line every 200 objects and a final
    yield summary; failed ids land in `web/_failed_ids.json` for a re-run."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ok = empty = err = 0
    failed: list[str] = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fetch_raadata, i, force=force,
                            sleep_secs=sleep_secs): i for i in ids}
        for fut in as_completed(futs):
            i = futs[fut]
            done += 1
            try:
                rd = fut.result()
                if rd is None:
                    empty += 1     # page fetched, no rådata → HTML fallback saved
                else:
                    ok += 1
            except Exception as e:  # noqa: BLE001
                err += 1
                failed.append(i)
                print(f"  ERR {i}: {e}", file=sys.stderr)
            if done % 200 == 0:
                print(f"  {done}/{len(ids)}  (raadata={ok} no-raadata={empty} err={err})",
                      flush=True)
    (WEB_CACHE / "_failed_ids.json").write_text(json.dumps(failed))
    print(f"DONE {len(ids)}: raadata={ok}  no-raadata(html-fallback)={empty}  "
          f"errors={err} (ids in web/_failed_ids.json)")
    return 0 if err == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids", nargs="*", help="numeric KMM object ids")
    ap.add_argument("--file", help="JSON file holding a list of ids")
    ap.add_argument("--force", action="store_true", help="refetch even if cached")
    ap.add_argument("--preview", action="store_true", help="print each description div")
    ap.add_argument("--bulk", action="store_true",
                    help="§DB Phase-1 bulk mode: store verbatim raadata JSON "
                         "sidecars (HTML only as parse-failure fallback)")
    ap.add_argument("--workers", type=int, default=3,
                    help="bulk-mode thread pool size (default 3)")
    ap.add_argument("--sleep", type=float, default=SLEEP_SECS,
                    help=f"per-worker sleep after each fetch (default {SLEEP_SECS}s)")
    args = ap.parse_args()

    ids = list(args.ids)
    if args.file:
        ids += [str(x) for x in json.load(open(args.file))]
    if not ids:
        ap.error("no ids given (positional or --file)")

    if args.bulk:
        return _bulk_fetch(ids, workers=args.workers,
                           sleep_secs=args.sleep, force=args.force)

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
