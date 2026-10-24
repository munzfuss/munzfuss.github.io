#!/usr/bin/env python3
"""Helper for the `fuss-rebuild-review` skill — compare one Müntzfuß between a
BASE revision (default `main`) and the working tree, at the data layer and on
the rendered page. READ-ONLY for the repository: it writes only under
`output/fuss_compare/` (gitignored).

Why one script: reviewing Nobelfod, Guldgyldenfod and Lybsk møntfod
(2026-10-24) the comparison was rewritten by hand three times, and each
hand-written version missed something the next one caught — a citation
whose LABEL changed under the same URL (record-diff-table compares sources
by URL only), and a ruler change visible only on the DE page (the renderer
strips the ordinal period on da/en/uk). The two subcommands below are the
checks that caught them.

Subcommands:
  fuss_compare.py data  <fuss> [--base main] [--location denmark]
      Every final of <fuss> on the location's entities, base vs working tree:
        * finals present on one side only;
        * per final: the SEEDS it composes (by seed id — the only stable
          handle, CLAUDE.md §9b), every field that differs (flattened,
          order-only list changes ignored), `sources` by URL plus every key
          (`ref`, `display`, `type`) that differs on a shared URL;
          `verification_note` reported as one line;
        * seeds that joined or left the Fuß.
  fuss_compare.py build-base [--base main] [--site danskmoent]
      Archive <base> into output/fuss_compare/<base>/ and build the site
      there (a few minutes; run it in the background).
  fuss_compare.py page  <fuss> [--base main] [--site danskmoent]
      Row-by-row diff of every rendered `t/<fuss>.html` (all languages; on
      munzfuss every location), base build vs the working tree's build
      (`site-<site>/`, or `site/` for munzfuss — build it first). Tooltip
      indices (`data-tt`) are resolved to their text through the page's
      `window.__TT`, and each row is compared as a multiset of lines, so a
      renumbered tooltip table or a reordered source list is not a
      difference.
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.v2_index import V2Index  # noqa: E402

WORK = ROOT / "output" / "fuss_compare"


# ── base revision ───────────────────────────────────────────────────────────
def base_tree(base: str) -> Path:
    """data/v2 (and, for build-base, the whole tree) of <base>, archived once
    per base SHA under output/fuss_compare/."""
    sha = subprocess.run(["git", "rev-parse", "--short", base], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.strip()
    d = WORK / sha
    if not (d / "data" / "v2").exists():
        d.mkdir(parents=True, exist_ok=True)
        tar = WORK / f"{sha}.tar"
        subprocess.run(["git", "archive", base, "-o", str(tar)], cwd=ROOT, check=True)
        subprocess.run(["tar", "-xf", str(tar), "-C", str(d)], check=True)
        tar.unlink()
    return d


def location_entities(loc: str) -> list[str]:
    ce = yaml.safe_load((ROOT / "data/v2/locations" / f"{loc}.yml").read_text())["consumes_entities"]
    return [e["entity"] if isinstance(e, dict) else e for e in ce]


# ── data ────────────────────────────────────────────────────────────────────
def _flat(d, pre=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{pre}.{k}" if pre else k))
    else:
        out[pre] = d
    return out


def _bag(lst: list) -> list[str]:
    """Order-free identity of a list (order carries no meaning in a final)."""
    return sorted(json.dumps(v, sort_keys=True, default=str) for v in lst)


def _finals(v2: Path, ents: list[str], fuss: str) -> dict[str, tuple[str, dict]]:
    out = {}
    for e in ents:
        p = v2 / "final" / f"{e}.yml"
        if p.exists():
            for c in (yaml.safe_load(p.read_text()) or {}).get("coins") or []:
                if c.get("fuss") == fuss:
                    out[c["id"]] = (e, c)
    return out


def _short(v, n=140):
    s = str(v)
    return s if len(s) <= n else s[:n] + "…"


def cmd_data(a) -> int:
    ents = location_entities(a.location)
    bv2 = base_tree(a.base) / "data" / "v2"
    wv2 = ROOT / "data" / "v2"
    bi, wi = V2Index.load(root=bv2), V2Index.load(root=wv2)
    B, W = _finals(bv2, ents, a.fuss), _finals(wv2, ents, a.fuss)
    print(f"# {a.fuss}: {len(B)} finals on {a.base}, {len(W)} in the working tree "
          f"(entities of {a.location})")
    for tag, only in ((f"only on {a.base}", set(B) - set(W)), ("only in the working tree", set(W) - set(B))):
        if only:
            print(f"{tag}: {sorted(only)}")
    totals = collections.Counter()
    for fid in sorted(set(B) | set(W)):
        eb, b = B.get(fid, (None, {}))
        ew, w = W.get(fid, (None, {}))
        lines = []
        if not (b and w):
            here, other = (wi, bi) if w else (bi, wi)
            seeds = sorted({p.seed for p in here.by_final(fid)}) if fid in here.final_members else []
            now = sorted({other.by_seed[s].final for s in seeds if s in other.by_seed} - {None})
            side = "working tree" if w else a.base
            print(f"\n== {eb or ew} {fid} | {(b or w).get('nominal')} | {(b or w).get('year_label')}"
                  f" | ONLY in {side}; seeds {seeds}; on the other side in {now or 'no final'}")
            totals[f"finals only in {side}"] += 1
            continue
        if eb and ew and eb != ew:
            lines.append(f"entity {eb} -> {ew}")
        sb = {p.seed for p in bi.by_final(fid)} if fid in bi.final_members else set()
        sw = {p.seed for p in wi.by_final(fid)} if fid in wi.final_members else set()
        if sb != sw:
            lines.append(f"SEEDS only on base {sorted(sb - sw)}; only in tree {sorted(sw - sb)}")
            totals["seeds"] += 1
        ub = {s.get("url"): s for s in b.get("sources") or []}
        uw = {s.get("url"): s for s in w.get("sources") or []}
        for tag, only in (("base", set(ub) - set(uw)), ("tree", set(uw) - set(ub))):
            if only:
                lines.append(f"sources only in {tag}: {len(only)} — {sorted(only)[:4]}")
                totals[f"sources only in {tag}"] += len(only)
        for u in sorted(set(ub) & set(uw), key=str):
            for k in sorted(set(ub[u]) | set(uw[u])):
                if ub[u].get(k) != uw[u].get(k):
                    lines.append(f"source {u}: {k} {_short(ub[u].get(k), 80)!r} -> {_short(uw[u].get(k), 80)!r}")
                    totals[f"source {k}"] += 1
        fb = _flat({k: v for k, v in b.items() if k != "sources"})
        fw = _flat({k: v for k, v in w.items() if k != "sources"})
        vnote = False
        for k in sorted(set(fb) | set(fw)):
            x, y = fb.get(k), fw.get(k)
            if x == y:
                continue
            if k.startswith("verification_note"):
                vnote = True
                continue
            if isinstance(x, list) and isinstance(y, list) and _bag(x) == _bag(y):
                continue
            lines.append(f"{k}: {_short(x)} -> {_short(y)}")
            totals[k] += 1
        if vnote:
            lines.append("verification_note differs (all languages)")
            totals["verification_note"] += 1
        head = b or w
        print(f"\n== {eb or ew} {fid} | {head.get('nominal')} | {head.get('year_label')} | {head.get('ruler')}"
              f" | seeds {len(sb)}→{len(sw)}")
        for ln in lines or ["no difference"]:
            print("    " + ln)
    fb_seeds = {p.seed for p in bi.by_seed.values() if p.fuss == a.fuss}
    fw_seeds = {p.seed for p in wi.by_seed.values() if p.fuss == a.fuss}
    print(f"\n# seeds in {a.fuss}: base {len(fb_seeds)}, tree {len(fw_seeds)}")
    for s in sorted(fb_seeds - fw_seeds):
        p = wi.by_seed.get(s)
        print(f"  LEFT   {s} -> {p.final if p else None} ({p.fuss if p else 'no seed'})")
    for s in sorted(fw_seeds - fb_seeds):
        p = bi.by_seed.get(s)
        print(f"  JOINED {s} <- {p.final if p else None} ({p.fuss if p else 'new seed'})")
    print(f"\n# totals: {dict(totals)}")
    return 0


# ── page ────────────────────────────────────────────────────────────────────
def _site_dir(root: Path, site: str) -> Path:
    return root / ("site" if site == "munzfuss" else f"site-{site}")


def cmd_build_base(a) -> int:
    d = base_tree(a.base)
    venv = d / ".venv"
    if not venv.exists():
        os.symlink(ROOT / ".venv" if (ROOT / ".venv").exists() else Path(os.path.realpath(ROOT / ".venv")), venv)
    args = [str(venv / "bin" / "python"), "scripts/build.py"] + ([] if a.site == "munzfuss" else ["--site", a.site])
    print("building", a.site, "in", d)
    return subprocess.run(args, cwd=d).returncode


def _rows(path: Path) -> list[tuple[str, collections.Counter]]:
    t = path.read_text(encoding="utf-8")
    idx = path.parent.parent / "index.html"
    m = re.search(r"window\.__TT=(\[.*?\]);</script>", idx.read_text(encoding="utf-8"), flags=re.S)
    tt = json.loads(m.group(1)) if m else []
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    t = re.sub(r'data-tt="(\d+)"',
               lambda x: 'data-tooltip="' + html.escape(tt[int(x.group(1))] if int(x.group(1)) < len(tt) else "?") + '"', t)
    out = []
    for r in re.findall(r"<tr[^>]*>.*?</tr>", t, flags=re.S):
        lines = [html.unescape(l.strip()) for l in re.sub(r">\s*<", ">\n<", r).split("\n") if l.strip()]
        lines = [l for l in lines if l not in ("<br>", "</span>", '<span class="ref-line">')]
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", r))).strip()
        out.append((text[:110], collections.Counter(lines)))
    return out


def cmd_page(a) -> int:
    base_site = _site_dir(base_tree(a.base), a.site)
    cur_site = _site_dir(ROOT, a.site)
    if not base_site.exists():
        raise SystemExit(f"no base build at {base_site} — run build-base first")
    pages = sorted(p.relative_to(cur_site) for p in cur_site.rglob(f"t/{a.fuss}.html"))
    if not pages:
        raise SystemExit(f"no t/{a.fuss}.html under {cur_site} — build the site first")
    changed = 0
    for rel in pages:
        bp = base_site / rel
        if not bp.exists():
            print(f"===== {rel}: NEW (no such page on base)")
            continue
        A, Bw = _rows(bp), _rows(cur_site / rel)
        out, used = [], set()
        for ta, ca in A:
            best, bi = None, None
            for j, (_, cb) in enumerate(Bw):
                if j not in used:
                    score = sum((ca & cb).values())
                    if best is None or score > best:
                        best, bi = score, j
            if bi is None:
                out.append(f"   ROW GONE: {ta}")
                continue
            used.add(bi)
            cb = Bw[bi][1]
            if ca != cb:
                out.append(f"   ROW {ta}")
                out += [f"      - {l[:240]}" for l in sorted((ca - cb).elements())]
                out += [f"      + {l[:240]}" for l in sorted((cb - ca).elements())]
        out += [f"   ROW NEW: {tb}" for j, (tb, _) in enumerate(Bw) if j not in used]
        print(f"===== {rel}: rows {len(A)} vs {len(Bw)}" + ("" if out else " — identical"))
        print("\n".join(out)) if out else None
        changed += bool(out)
    for rel in sorted(p.relative_to(base_site) for p in base_site.rglob(f"t/{a.fuss}.html")):
        if not (cur_site / rel).exists():
            print(f"===== {rel}: GONE (page exists on base only)")
    print(f"\n# {len(pages)} pages, {changed} with differences")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("data"); d.add_argument("fuss"); d.add_argument("--base", default="main"); d.add_argument("--location", default="denmark")
    b = sub.add_parser("build-base"); b.add_argument("--base", default="main"); b.add_argument("--site", default="danskmoent")
    p = sub.add_parser("page"); p.add_argument("fuss"); p.add_argument("--base", default="main"); p.add_argument("--site", default="danskmoent")
    a = ap.parse_args()
    return {"data": cmd_data, "build-base": cmd_build_base, "page": cmd_page}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
