"""Helpers for the ucoin-composition harvest pipeline.

The actual page-fetching runs through Chrome MCP (see Claude session
2026-05-11 «ucoin composition expansion») — ucoin blocks WebFetch /
Apify / curl with 403, only a real-browser session goes through.

This file contains the two helpers that bracket the Chrome-MCP step:

  1. ``next_batch(n)`` — pop n tids from the URL index that aren't
     yet in the sidecar, and emit a JSON action list ready to paste
     into one ``browser_batch`` call.
  2. ``ingest_results(results_json)`` — parse the per-tid JSON
     strings returned by the JS-extractor and merge into
     ``scripts/cache/ucoin/_composition.json``.

Sidecar format:

    { "<tid>": { "composition": "Bronze" | "Silver 0.800" | "Gold 0.917" | ...,
                  "weight_g": float | null,
                  "diameter_mm": float | null,
                  "thickness_mm": float | null,
                  "edge_type": str | null,
                  "shape": str | null,
                  "alignment": str | null,
                  "fetched_at": ISO8601 } }

JS extractor (paste into browser_batch ``javascript_tool.text``,
one call per tid, with ``__TID__`` replaced by the actual tid):

    const labels=['Composition','Weight (g)','Diameter (mm)','Thickness (mm)','Edge type','Shape','Alignment'];
    const out={tid:'__TID__'};
    const text=document.body.innerText||'';
    for(const lbl of labels){
        const re=new RegExp('^'+lbl.replace(/[.()]/g,m=>'\\\\'+m)+'\\\\s*\\\\n?\\\\s*([^\\\\n]+)','m');
        const m=text.match(re);
        if(m)out[lbl]=m[1].trim();
    }
    JSON.stringify(out)

Usage in a Chrome-MCP-enabled Claude session:

    .venv/bin/python scripts/maintenance/ucoin_fetch_composition.py \\
        next-batch 15 --tab-id 1234567890

    # paste the returned actions list into browser_batch, then:

    .venv/bin/python scripts/maintenance/ucoin_fetch_composition.py \\
        ingest <<'EOF'
    [{"tid":"...","Composition":"...",...}, ...]
    EOF
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import UCOIN_CACHE  # noqa: E402

URL_INDEX = UCOIN_CACHE / "_url_index.json"
SIDECAR = UCOIN_CACHE / "_composition.json"

JS_EXTRACTOR = (
    "const labels=['Composition','Weight (g)','Diameter (mm)',"
    "'Thickness (mm)','Edge type','Shape','Alignment'];"
    "const out={tid:'__TID__'};"
    "const text=document.body.innerText||'';"
    "for(const lbl of labels){"
    "const re=new RegExp('^'+lbl.replace(/[.()]/g,m=>'\\\\'+m)+"
    "'\\\\s*\\\\n?\\\\s*([^\\\\n]+)','m');"
    "const m=text.match(re);if(m)out[lbl]=m[1].trim();}"
    "JSON.stringify(out)"
)

KEY_MAP = {
    "Composition": "composition",
    "Weight (g)": "weight_g",
    "Diameter (mm)": "diameter_mm",
    "Thickness (mm)": "thickness_mm",
    "Edge type": "edge_type",
    "Shape": "shape",
    "Alignment": "alignment",
}


def _load_sidecar() -> dict:
    if SIDECAR.exists():
        return json.loads(SIDECAR.read_text())
    return {}


def _save_sidecar(sidecar: dict) -> None:
    SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    SIDECAR.write_text(json.dumps(sidecar, indent=2, sort_keys=True))


def cmd_next_batch(n: int, tab_id: int) -> None:
    """Emit a JSON actions list for browser_batch covering n unfetched tids."""
    url_index = json.loads(URL_INDEX.read_text())
    sidecar = _load_sidecar()
    todo = [(tid, url_index[tid]["url"]) for tid in sorted(url_index) if tid not in sidecar]
    batch = todo[:n]
    actions = []
    for tid, url in batch:
        actions.append({"name": "navigate", "input": {"url": url, "tabId": tab_id}})
        actions.append({
            "name": "javascript_tool",
            "input": {
                "action": "javascript_exec",
                "tabId": tab_id,
                "text": JS_EXTRACTOR.replace("__TID__", tid),
            },
        })
    out = {"actions": actions, "tids": [t for t, _ in batch], "remaining": len(todo) - len(batch)}
    print(json.dumps(out))


def _parse_num(s: str | None) -> float | None:
    if not s:
        return None
    s = str(s)
    if "Unknown" in s:
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def cmd_ingest(stream) -> None:
    """Read a JSON list of per-tid extractor outputs from stdin and merge
    into the sidecar."""
    data = json.load(stream)
    if not isinstance(data, list):
        raise SystemExit("Expected a JSON list of per-tid dicts")
    sidecar = _load_sidecar()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    added = 0
    for rec in data:
        tid = rec.get("tid")
        if not tid:
            continue
        entry = {"fetched_at": now}
        for src, dst in KEY_MAP.items():
            v = rec.get(src)
            if not v or "Unknown" in str(v):
                continue
            if dst in ("weight_g", "diameter_mm", "thickness_mm"):
                num = _parse_num(v)
                if num is not None:
                    entry[dst] = num
            else:
                entry[dst] = v
        sidecar[tid] = entry
        added += 1
    _save_sidecar(sidecar)
    print(f"Ingested {added}; sidecar now has {len(sidecar)} entries")


def cmd_status() -> None:
    url_index = json.loads(URL_INDEX.read_text())
    sidecar = _load_sidecar()
    todo = [t for t in url_index if t not in sidecar]
    print(f"URL index: {len(url_index)} tids")
    print(f"Sidecar:   {len(sidecar)} fetched")
    print(f"Pending:   {len(todo)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_nb = sub.add_parser("next-batch", help="Emit JSON actions list for next n unfetched tids")
    p_nb.add_argument("n", type=int, help="Batch size")
    p_nb.add_argument("--tab-id", type=int, required=True, help="Chrome MCP tab id")
    sub.add_parser("ingest", help="Parse extractor output JSON from stdin into sidecar")
    sub.add_parser("status", help="Print fetch progress")
    args = ap.parse_args()
    if args.cmd == "next-batch":
        cmd_next_batch(args.n, args.tab_id)
    elif args.cmd == "ingest":
        cmd_ingest(sys.stdin)
    elif args.cmd == "status":
        cmd_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
