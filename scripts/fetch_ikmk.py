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


def _fetch_one(opener_holder: list, nid: str) -> bool:
    """Fetch a single record, with retries + backoff for throttle/network errors.

    `opener_holder` is a one-element list holding the current opener so we
    can rebuild the session (fresh cookies, fresh socket) after a backoff.
    """
    path = CACHE_DIR / f"{nid}.json"
    if path.exists():
        return False
    url = f"https://ikmk.smb.museum/object?id={nid}&download=json_ext"
    last_err: Exception | None = None
    backoffs = (2.0, 5.0, 15.0, 60.0)
    for attempt, wait_after in enumerate(backoffs):
        try:
            body = opener_holder[0].open(url, timeout=60).read()
            path.write_bytes(body)
            return True
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
    """Fetch JSON for every ID in the manifest (skipping cached).

    Parameters
    ----------
    limit
        When set, stop after that many NEW fetches (cache writes). IDs
        already cached are still skipped without counting against the
        limit. Used by the hourly harvest routine (`HARVEST_ROUTINE.md`
        §5.5) to pace IKMK harvest into small batches matching the
        Numista/ucoin per-run cadence.
    """
    if not MANIFEST.exists():
        print("manifest missing — run `discover` first", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST.read_text())
    ids: list[str] = manifest["ids"]
    opener_holder = [_make_session()]
    fetched = 0
    skipped = 0
    errors = 0
    t0 = time.time()
    for i, nid in enumerate(ids, start=1):
        try:
            new = _fetch_one(opener_holder, nid)
        except urllib.error.HTTPError as exc:
            errors += 1
            print(f"  [{nid}] gave up: HTTP {exc.code}", file=sys.stderr)
            continue
        except Exception as exc:
            errors += 1
            print(f"  [{nid}] gave up: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        if new:
            fetched += 1
            time.sleep(SLEEP_SECS)
            if limit is not None and fetched >= limit:
                print(
                    f"  reached --limit {limit}; stopping. "
                    f"fetched={fetched} skipped={skipped} errors={errors} "
                    f"({int(time.time() - t0)}s).",
                )
                return
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
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Cap on new fetches per run (cache writes). Used by the "
             "hourly harvest routine for small per-run batches. "
             "Applies to `fetch` and `both` phases.",
    )
    args = ap.parse_args()
    if args.phase in ("discover", "both"):
        discover()
    if args.phase in ("fetch", "both"):
        fetch(limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
