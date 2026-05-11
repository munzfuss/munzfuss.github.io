"""Helpers for the ucoin-composition harvest pipeline.

The actual page-fetching runs through Chrome MCP (see Claude session
2026-05-11 «ucoin composition expansion») — ucoin blocks WebFetch /
Apify / curl with 403, only a real-browser session goes through.

**Harvest halted 2026-05-11**: ucoin's URL slug routing changed and our
``_url_index.json`` (slug-generated heuristically from period TSVs) no
longer resolves correctly. Pages built like ``/coin/<slug>/?tid=<tid>``
return UNRELATED coins (typically modern Euro-area pieces) with HTTP
200, instead of 404. Symptoms:

  * ``denmark-1-dukat-1753-1756/?tid=101037`` → «50 euro cent, Ireland»
  * ``denmark-1-ore-1874-1904/?tid=49544``    → «1 euro 2002-2007, Italy»
  * ``denmark-1-hvid-1602/?tid=162977``       → «1 euro 2002-2008, Portugal»

The bare ``/coin/?tid=<tid>`` form returns 404 (no fallback to tid
lookup). The ``/catalog/`` and ``/table/`` listing pages no longer
expose ``?tid=`` query links — ucoin's URL scheme has been restructured.

The 98 entries currently in ``_composition.json`` (committed
2026-05-11 16:54Z) were harvested when the old slug routing was still
working and are internally consistent with the expected per-coin
specs. They are TREATED AS RELIABLE. No further entries are added by
this pipeline until either: (a) ucoin's slug routing is restored, or
(b) a new URL discovery strategy (e.g. site-search, sitemap, JSON
API) is identified.

Cross-validation primitive that catches future regressions: compare
the page's ``<link rel="canonical">`` href to the requested tid before
trusting any extracted data (see the canonical-tid check inside
``MEGA_FETCH_TEMPLATE``). Currently this check rejects 100 % of slug
look-ups, confirming the breakage above.

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

# Compact-key map used by the same-origin fetch / mega-batch JS extractor
# (one-letter keys keep the cross-page JSON small so 50 records fit
# comfortably in a localStorage round-trip).
COMPACT_KEY_MAP = {
    "c": "composition",
    "w": "weight_g",
    "d": "diameter_mm",
    "th": "thickness_mm",
    "e": "edge_type",
    "s": "shape",
    "a": "alignment",
}

# Mega-batch JS: fetches N URLs through same-origin fetch(), parses the
# specification table from each page's HTML, stores the resulting array
# as a JSON string under ``localStorage.uc_results`` so the caller can
# read it back in chunks via ``slice()``. The JS body returns a tiny
# {n, total_bytes} summary so the immediate tool-call return stays small.
MEGA_FETCH_TEMPLATE = """
(async () => {
  const todo = __TODO__;
  const labels = {Composition:'c','Weight (g)':'w','Diameter (mm)':'d','Thickness (mm)':'th','Edge type':'e',Shape:'s',Alignment:'a'};
  const fetchOne = async ([tid, url]) => {
    try {
      const r = await fetch(url, {credentials: 'same-origin'});
      const html = await r.text();
      // Validate that the page's canonical tid matches what we requested.
      // ucoin's slug routing serves UNRELATED coins for bad slugs while
      // returning HTTP 200, so structural data on the page is for a
      // different tid. Reject when canonical tid disagrees.
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const canon = doc.querySelector('link[rel=canonical]');
      let canonTid = null;
      if (canon) {
        const m = canon.href.match(/[?&]tid=(\\d+)/);
        if (m) canonTid = m[1];
      }
      if (!r.ok) return {tid, err: 'HTTP ' + r.status};
      if (canonTid && canonTid !== String(tid)) {
        return {tid, err: 'slug_mismatch'};
      }
      if (!canonTid) {
        // No canonical link found — likely redirected to home / 404 soft-page
        return {tid, err: 'no_canonical'};
      }
      const rec = {tid};
      for (const tr of doc.querySelectorAll('tr')) {
        const th = tr.querySelector('th'); const td = tr.querySelector('td');
        if (!th || !td) continue;
        const k = th.textContent.trim();
        if (k in labels) rec[labels[k]] = td.textContent.trim();
      }
      return rec;
    } catch (e) { return {tid, err: String(e)}; }
  };
  // Fire in parallel waves of CONCURRENCY to keep request count manageable
  const CONCURRENCY = 10;
  const out = [];
  for (let i = 0; i < todo.length; i += CONCURRENCY) {
    const slice = todo.slice(i, i + CONCURRENCY);
    const results = await Promise.all(slice.map(fetchOne));
    out.push(...results);
  }
  const s = JSON.stringify(out);
  localStorage.uc_results = s;
  return {n: out.length, total_bytes: s.length};
})()
"""


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
    into the sidecar. Tolerates both the original full-label keys
    (``"Composition"``, ``"Weight (g)"``, …) AND the compact one-letter
    keys (``c``, ``w``, ``d``, ``th``, …) emitted by the mega-batch
    same-origin fetch extractor. Records carrying an ``err`` field are
    persisted with ``status_404: True`` so future runs skip them."""
    data = json.load(stream)
    if not isinstance(data, list):
        raise SystemExit("Expected a JSON list of per-tid dicts")
    sidecar = _load_sidecar()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    added = 0
    skipped_err = 0
    for rec in data:
        tid = rec.get("tid")
        if not tid:
            continue
        tid = str(tid)
        if rec.get("err"):
            sidecar[tid] = {"fetched_at": now, "status_404": True, "err": rec["err"]}
            skipped_err += 1
            continue
        entry = {"fetched_at": now}
        # Build a unified iterable: try full-label keys first, then compact
        items = []
        for src, dst in KEY_MAP.items():
            if src in rec:
                items.append((dst, rec[src]))
        for src, dst in COMPACT_KEY_MAP.items():
            if src in rec and dst not in (k for k, _ in items):
                items.append((dst, rec[src]))
        if not items:
            # Page loaded but the spec table was empty / page-shape changed
            sidecar[tid] = {"fetched_at": now, "status_404": True, "err": "empty_spec"}
            skipped_err += 1
            continue
        for dst, v in items:
            if not v or "Unknown" in str(v):
                continue
            if dst in ("weight_g", "diameter_mm", "thickness_mm"):
                num = _parse_num(v)
                if num is not None:
                    entry[dst] = num
            else:
                entry[dst] = str(v)
        sidecar[tid] = entry
        added += 1
    _save_sidecar(sidecar)
    print(f"Ingested {added} ok, {skipped_err} marked status_404/empty; sidecar now has {len(sidecar)} entries")


def cmd_mega_batch(n: int) -> None:
    """Emit a single javascript_tool snippet that fetches n URLs via
    same-origin fetch() and persists the result in localStorage.

    Output format: ``{"text": "(async ...)", "tids": [...], "remaining": K}``
    The caller pastes ``text`` into ``javascript_tool`` once and then
    reads back ``localStorage.uc_results`` in chunks via ``slice()``.
    """
    url_index = json.loads(URL_INDEX.read_text())
    sidecar = _load_sidecar()
    todo = [(tid, url_index[tid]["url"]) for tid in sorted(url_index) if tid not in sidecar]
    batch = todo[:n]
    todo_pairs = [[tid, url] for tid, url in batch]
    text = MEGA_FETCH_TEMPLATE.replace("__TODO__", json.dumps(todo_pairs))
    out = {
        "text": text,
        "tids": [t for t, _ in batch],
        "remaining": len(todo) - len(batch),
    }
    print(json.dumps(out))


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
    p_mb = sub.add_parser("mega-batch", help="Emit single same-origin fetch JS for next n tids")
    p_mb.add_argument("n", type=int, help="Batch size (typically 50)")
    sub.add_parser("ingest", help="Parse extractor output JSON from stdin into sidecar")
    sub.add_parser("status", help="Print fetch progress")
    args = ap.parse_args()
    if args.cmd == "next-batch":
        cmd_next_batch(args.n, args.tab_id)
    elif args.cmd == "mega-batch":
        cmd_mega_batch(args.n)
    elif args.cmd == "ingest":
        cmd_ingest(sys.stdin)
    elif args.cmd == "status":
        cmd_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
