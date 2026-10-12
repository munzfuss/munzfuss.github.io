#!/usr/bin/env python3
"""Read-only: find KMM records whose cached web page (scripts/cache/kmk/web/<id>.json)
is a different object than the API record (scripts/cache/kmk/<id>.json).

Background: docs/SOURCES.md §13.19. `build_kmk_seed._enrich_from_raadata` fills
API gaps from the web page keyed only by the numeric id. Three classes exist:

  A  notation only — same inventory once a repeated base and leading zeros
     are removed (`_inv_key`). Harmless.
  B  same prefix + base number, different suffix (the FP 1780 off-by-one).
     Page content usually still follows the id; the builder enriches. A
     record is flagged INCOHERENT when the API and page content disagree
     (nominal, or «norsk» vs a non-Christiania place). Those need a curator
     call and, if confirmed, an entry in `_RAADATA_INCOHERENT_IDS`.
  C  different prefix or base number — another object; the builder skips
     enrichment automatically (`_raadata_other_object`).

Run after every KMM re-harvest. Prints the counts per class and lists every
B-INCOHERENT record not yet in `_RAADATA_INCOHERENT_IDS`. Exit 1 if any.

    .venv/bin/python scripts/maintenance/audit_kmk_raadata_mismatch.py [--all]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_kmk_seed import (  # noqa: E402
    _RAADATA_INCOHERENT_IDS, _inv_key, _raadata_other_object,
)

CACHE = ROOT / "scripts" / "cache" / "kmk"


def _words(s: str | None) -> list[str]:
    s = (s or "").lower().split(",")[0]
    return re.sub(r"[^a-zæøå0-9 ]", "", s).split()


def _incoherent(api: dict, web: dict) -> str | None:
    """Reason string when API and page content disagree, else None."""
    besk = [b for b in (web.get("beskrivelser") or [])
            if isinstance(b, str) and b.strip() and b.strip() != "Ikonografi"]
    if besk and api.get("nominal") and _words(api["nominal"]) != _words(besk[0]):
        # søsling = sechsling is the same nominal in two languages
        pair = {" ".join(_words(api["nominal"])), " ".join(_words(besk[0]))}
        if pair != {"søsling", "sechsling"}:
            return f"nominal «{api['nominal']}» ↔ page «{besk[0].strip()}»"
    loc = " ".join(((h.get("lokalitet") or {}).get("angivelser") or "")
                   for h in web.get("haendelser") or []
                   if h.get("titel") == "Fremstilling")
    if "norsk" in (api.get("nominal") or "") and loc and "Christiania" not in loc \
            and "Norge" not in loc:
        return f"«{api['nominal']}» ↔ page place «{loc}»"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="also list B-INCOHERENT records already handled")
    args = ap.parse_args()
    counts = {"A": 0, "B": 0, "B-incoherent": 0, "C": 0}
    new = []
    for wf in sorted((CACHE / "web").glob("*.json")):
        af = CACHE / wf.name
        if not af.exists():
            continue
        api = json.loads(af.read_text("utf-8"))
        web = json.loads(wf.read_text("utf-8"))
        a = (api.get("objectIdentification") or "").strip()
        w = (web.get("identifikation") or "").strip()
        if not a or not w or a == w:
            continue
        if _inv_key(a) == _inv_key(w):
            counts["A"] += 1
            continue
        if str(api.get("id")) not in _RAADATA_INCOHERENT_IDS and \
                _raadata_other_object(api, web):
            counts["C"] += 1
            continue
        why = _incoherent(api, web)
        if why is None:
            counts["B"] += 1
            continue
        counts["B-incoherent"] += 1
        handled = str(api.get("id")) in _RAADATA_INCOHERENT_IDS
        if not handled or args.all:
            new.append((api.get("id"), a, w, why, handled))
    print("KMM API ↔ web-page inventory mismatches:",
          ", ".join(f"{k} {v}" for k, v in counts.items()))
    for rid, a, w, why, handled in new:
        mark = "handled" if handled else "NEW"
        print(f"  [{mark}] {rid}  API {a} ↔ page {w}: {why}")
    unhandled = [x for x in new if not x[4]]
    if unhandled:
        print(f"\n{len(unhandled)} B-incoherent record(s) not in "
              "_RAADATA_INCOHERENT_IDS — curator call (SOURCES §13.19).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
