#!/usr/bin/env python3
"""Fetch coin references from Numista API v3 (replaces browser scraping).

Strategy:
- Reads `data/locations/schleswig_holstein.yml`, collects unique `catalog.numista` IDs.
- For each, looks up cached `scripts/cache/numista/<nid>.json`. If absent,
  fetches from the API and caches the full JSON response.
- Compiles `scripts/numista_refs.json` — the input expected by
  `scripts/enrich_numista_refs.py` — keyed by nid, value = list of strings
  in "Prefix# number" form (e.g. "KM# 12", "Weinm# 39").

Free-tier limit: 200 calls / 24h. We rate-limit to ~1 req/sec to stay polite
even when a future location batch pushes total volume higher.

Usage:
    .venv/bin/python scripts/fetch_numista_api.py
    .venv/bin/python scripts/fetch_numista_api.py --force      # ignore cache
    .venv/bin/python scripts/fetch_numista_api.py --location=schleswig
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib.env import load_local_env, require  # type: ignore  # noqa: E402

from ruamel.yaml import YAML  # noqa: E402

CACHE_DIR = pathlib.Path("scripts/cache/numista")
OUT_REFS = pathlib.Path("scripts/numista_refs.json")
# Per docs at https://en.numista.com/api/doc/index.php the canonical base is /v3
# (the /api/v3 prefix also works but is undocumented).
API_BASE = "https://api.numista.com/v3"
RATE_LIMIT_S = 1.0  # seconds between live fetches


def fetch_type(nid: str, key: str) -> dict:
    """One live API call. Raises on HTTP error."""
    url = f"{API_BASE}/types/{nid}?lang=en"
    req = urllib.request.Request(
        url,
        headers={"Numista-API-Key": key, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def get_or_fetch(nid: str, key: str, force: bool = False) -> tuple[dict, bool]:
    """Return (json, was_live_fetch). Caches to CACHE_DIR/<nid>.json."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{nid}.json"
    if not force and cache_path.exists():
        return json.loads(cache_path.read_text()), False
    data = fetch_type(nid, key)
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data, True


def refs_to_strings(refs: list[dict]) -> list[str]:
    """[{catalogue:{code:'KM'}, number:'12'}] → ['KM# 12']"""
    out = []
    for r in refs or []:
        code = (r.get("catalogue") or {}).get("code") or ""
        num = r.get("number") or ""
        if not code or not num:
            continue
        out.append(f"{code}# {num}")
    return out


def collect_nids(yml_path: pathlib.Path) -> list[str]:
    yaml = YAML()
    data = yaml.load(yml_path.read_text())
    nids: set[str] = set()
    for c in data.get("coins") or []:
        nid = (c.get("catalog") or {}).get("numista")
        if nid:
            nids.add(str(nid))
    return sorted(nids)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="Refetch even if cached (uses up API quota)")
    ap.add_argument("--location", default="schleswig_holstein",
                    help="Location YAML stem (default: schleswig)")
    args = ap.parse_args()

    load_local_env()
    key = require("NUMISTA_API_KEY")

    yml_path = pathlib.Path(f"data/locations/{args.location}.yml")
    nids = collect_nids(yml_path)
    print(f"Collected {len(nids)} unique Numista IDs from {yml_path.name}")

    all_refs: dict[str, list[str]] = {}
    live = 0
    cached = 0
    errors: dict[str, str] = {}

    for i, nid in enumerate(nids, 1):
        try:
            data, was_live = get_or_fetch(nid, key, force=args.force)
            all_refs[nid] = refs_to_strings(data.get("references") or [])
            if was_live:
                live += 1
                time.sleep(RATE_LIMIT_S)
            else:
                cached += 1
            if i % 25 == 0:
                print(f"  [{i}/{len(nids)}] live={live} cached={cached} "
                      f"errors={len(errors)}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            errors[nid] = f"HTTP {e.code}: {body}"
            print(f"  ! N#{nid}: HTTP {e.code} — {body}")
            if e.code == 429:  # rate limited — stop, don't burn more quota
                print("  Hit rate limit; aborting further fetches.")
                break
        except Exception as e:
            errors[nid] = str(e)
            print(f"  ! N#{nid}: {e}")

    OUT_REFS.write_text(json.dumps(all_refs, ensure_ascii=False, indent=2))
    print()
    print(f"Wrote {OUT_REFS} ({len(all_refs)} entries)")
    print(f"  live API calls: {live}")
    print(f"  served from cache: {cached}")
    print(f"  errors: {len(errors)}")


if __name__ == "__main__":
    main()
