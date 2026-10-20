"""Per-specimen exclusions — one KMM object inside a seed, not the seed.

A KMM seed folds several specimens of one find into one coin record, one
`sources` entry each (`build_kmk_seed`'s grouping). A seed-level exclusion
(`exclusions:` in `data/v2/exclusions/<entity>.yml`) removes the whole record,
so it cannot drop the 39 bare specimens of a seed whose 40th has a photo.

The curator-approved specimen exclusions sit beside them, under a separate key
the seed-level code never reads:

    specimens:
      - kmm: 395811                 # KMM object number
        category: undocumented_stub
        reason: >- …
        curator: Serhii
        date: 2026-10-20

Effect: the specimen's citation is taken out of every coin in the merger (seed
load) and in absorb (after the sources union, which would otherwise carry it
over from the old final). The seed file keeps it (provenance). Guards, applied
by the callers: a specimen with a weight or a photo is never stripped, and a
coin is never left without a source. Curator direction 2026-10-20.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
EXCLUSIONS_DIR = _ROOT / "data" / "v2" / "exclusions"
_KMM_URL_RE = re.compile(r"/KMM/object/(\d+)\s*$")
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

_CACHE: dict[str, dict] | None = None


def load_excluded_specimens(directory: Path | None = None) -> dict[str, dict]:
    """{KMM object number: entry} over every `specimens:` block. Cached per
    process when read from the default directory."""
    global _CACHE
    if directory is None and _CACHE is not None:
        return _CACHE
    d = directory or EXCLUSIONS_DIR
    out: dict[str, dict] = {}
    if d.exists():
        for f in sorted(d.glob("*.yml")):
            doc = yaml.load(f.read_text(encoding="utf-8"), Loader=_LOADER) or {}
            for e in doc.get("specimens") or []:
                if isinstance(e, dict) and e.get("kmm") is not None:
                    out[str(e["kmm"]).strip()] = dict(e, _file=f.name)
    if directory is None:
        _CACHE = out
    return out


def kmm_number(source: dict) -> str | None:
    if not isinstance(source, dict):
        return None
    m = _KMM_URL_RE.search(str(source.get("url") or ""))
    return m.group(1) if m else None


def strip_excluded_specimens(coin: dict, excluded: dict | set,
                             keeps=lambda nid: False) -> list[str]:
    """Remove from `coin["sources"]` every KMM citation whose object number is
    excluded, unless `keeps(nid)` (the caller's weight / photo guard) says
    otherwise. Never empties a coin's sources: when every remaining citation
    would go, nothing is removed. Returns the object numbers removed."""
    srcs = coin.get("sources")
    if not isinstance(srcs, list) or not excluded:
        return []
    drop = [s for s in srcs
            if (n := kmm_number(s)) is not None and n in excluded and not keeps(n)]
    if not drop or len(drop) == len(srcs):
        return []
    ids = {id(s) for s in drop}
    coin["sources"] = [s for s in srcs if id(s) not in ids]
    return [kmm_number(s) for s in drop]
