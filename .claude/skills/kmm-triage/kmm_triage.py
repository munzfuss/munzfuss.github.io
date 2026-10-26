#!/usr/bin/env python3
"""Usefulness triage of the KMM (kmk-*) records inside one Müntzfuß.

READ-ONLY. For every kmk seed that is a member of a final of the Fuß it reads
three signals and sorts the record into the curator's categories
(2026-10-26):

  1    useless        no catalogue index, no weight, no image
  2    a little use   exactly one of the three
       2.1  index only, and another SOURCE in the same class gives that index
            too (a range such as «Schou 10-50» covers 23) — not critical
       2.2  index only, and no other source in the class gives it — unique
       2-w / 2-img  weight only / image only
  3    useful         two of the three
  4    very useful    image + index + weight

Signals:
  index   the seed's normalised `catalog` (numista / bruun / galster_volume
          ignored). A KMM `typeNumber` the builder could not parse is listed
          separately — it may hide an index.
  weight  the seed's `weight_rough_g`.
  image   scripts/cache/kmk/web/<id>.json `billeder` non-empty, else the
          <id>.html page carrying an ImageObject / «/asset/». Neither cached
          → «?» (fetch with scripts/fetch_kmk_web.py <ids> and re-run).

Usage:
  .venv/bin/python .claude/skills/kmm-triage/kmm_triage.py --fuss luebischer_muenzfuss
  … --md report.md --json rows.json      # write the full table
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

import yaml  # noqa: E402
from lib.v2_index import V2Index  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_SKIP = {"galster_volume", "bruun_collection_id", "numista"}
_WEB = ROOT / "scripts" / "cache" / "kmk" / "web"
_API = ROOT / "scripts" / "cache" / "kmk"


def _registers(cat) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for k, v in (cat or {}).items():
        if k in _SKIP or v in (None, "", []):
            continue
        if k == "others":
            for t in (v if isinstance(v, list) else [v]):
                m = re.match(r"^(.*?)#\s*(.+)$", str(t))
                if m:
                    out[m.group(1).strip().lower()].add(m.group(2).strip())
            continue
        if isinstance(v, dict):          # volume-keyed KM
            for vv in v.values():
                for x in (vv if isinstance(vv, list) else [vv]):
                    out[k].add(str(x))
            continue
        for x in (v if isinstance(v, list) else [v]):
            out[k].add(str(x))
    return out


def _covers(other: str, mine: str) -> bool:
    o, v = other.strip().casefold(), mine.strip().casefold()
    if o == v:
        return True
    rng, num = re.match(r"^(\d+)\s*-\s*(\d+)$", o), re.match(r"^(\d+)$", v)
    return bool(rng and num and int(rng.group(1)) <= int(num.group(1)) <= int(rng.group(2)))


def _has_weight(c: dict) -> bool:
    w = c.get("weight_rough_g")
    if isinstance(w, list):
        return any((e.get("value") if isinstance(e, dict) else e) for e in w)
    return bool(w)


def _has_image(oid: str):
    j = _WEB / f"{oid}.json"
    if j.exists():
        return bool(json.loads(j.read_text()).get("billeder"))
    h = _WEB / f"{oid}.html"
    if h.exists():
        t = h.read_text(errors="ignore")
        return "ImageObject" in t or "/asset/" in t
    return None


def _api(oid: str) -> dict:
    p = _API / f"{oid}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def triage(fuss: str) -> list[dict]:
    ix = V2Index.load()
    seeds = {c["id"]: c for p in glob.glob("data/v2/seed/*/*.yml")
             for c in (yaml.load(open(p), Loader=_L) or {}).get("coins") or []}
    finals = {c["id"]: c for p in glob.glob("data/v2/final/*.yml")
              for c in (yaml.load(open(p), Loader=_L) or {}).get("coins") or []}
    rows = []
    for fid, fc in finals.items():
        if fc.get("fuss") != fuss:
            continue
        mem = ix.final_members.get(fid, set())
        others: dict[str, set[str]] = collections.defaultdict(set)
        for o in mem:
            if not o.startswith("kmk-"):
                for k, vs in _registers((seeds.get(o) or {}).get("catalog")).items():
                    others[k] |= vs
        for sid in sorted(m for m in mem if m.startswith("kmk-")):
            s, oid = seeds.get(sid) or {}, sid.split("-", 1)[1]
            mine = _registers(s.get("catalog"))
            api = _api(oid)
            idx, w, img = bool(mine), _has_weight(s), _has_image(oid)
            uniq = [f"{k} {v}" for k, vs in mine.items() for v in sorted(vs)
                    if not any(_covers(o, v) for o in others.get(k, ()))]
            n = sum([idx, w, bool(img)])
            cat = {0: "1", 1: "2", 2: "3", 3: "4"}[n]
            if cat == "2":
                cat = ("2.2" if uniq else "2.1") if idx else ("2-w" if w else "2-img")
            rows.append({
                "seed": sid, "inv": api.get("objectIdentification"), "final": fid,
                "nominal": fc.get("nominal"), "ruler": fc.get("ruler"),
                "index": "; ".join(f"{k} {', '.join(sorted(v))}" for k, v in mine.items()),
                "unique": ", ".join(uniq), "weight": w, "image": img, "cat": cat,
                "typeNumber_unparsed": api.get("typeNumber") if api.get("typeNumber") and not idx else None,
                "kmm_only_class": all(m.startswith("kmk-") for m in mem),
                "class_members": len(mem),
            })
    return rows


_ORDER = ["1", "2.1", "2.2", "2-w", "2-img", "3", "4"]
_TITLE = {"1": "1 — без індексу, ваги й зображення", "2.1": "2.1 — лише індекс, неунікальний",
          "2.2": "2.2 — лише індекс, унікальний", "2-w": "2 — лише вага",
          "2-img": "2 — лише зображення", "3": "3 — два з трьох", "4": "4 — індекс, вага й зображення"}


def to_md(rows: list[dict], fuss: str) -> str:
    yn = lambda v: "?" if v is None else ("так" if v else "—")  # noqa: E731
    out = [f"# KMM triage — {fuss}", "",
           " · ".join(f"{c}: {sum(r['cat'] == c for r in rows)}" for c in _ORDER), ""]
    for c in _ORDER:
        rs = [r for r in rows if r["cat"] == c]
        if not rs:
            continue
        out += [f"## {_TITLE[c]} ({len(rs)})", "",
                "| seed | інв. | клас | номінал · правитель | індекс | унікальне | вага | фото | лише KMM у класі |",
                "|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: (r["final"], r["seed"])):
            idx = r["index"] or (f"(typeNumber «{r['typeNumber_unparsed']}» не розібрано)"
                                 if r["typeNumber_unparsed"] else "—")
            out.append(f"| {r['seed']} | {r['inv'] or ''} | {r['final']} ({r['class_members']}) | "
                       f"{r['nominal']} · {r['ruler']} | {idx} | {r['unique'] or '—'} | "
                       f"{yn(r['weight'])} | {yn(r['image'])} | {'так' if r['kmm_only_class'] else '—'} |")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuss", required=True)
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    rows = triage(a.fuss)
    print(f"{a.fuss}: {len(rows)} KMM records — "
          + ", ".join(f"{c}: {sum(r['cat'] == c for r in rows)}" for c in _ORDER))
    unk = [r["seed"] for r in rows if r["image"] is None]
    if unk:
        print(f"image unknown ({len(unk)}) — fetch: scripts/fetch_kmk_web.py "
              + " ".join(s.split('-', 1)[1] for s in unk))
    tn = [(r["seed"], r["typeNumber_unparsed"]) for r in rows if r["typeNumber_unparsed"]]
    if tn:
        print("typeNumber not parsed into catalog:", tn)
    if a.md:
        Path(a.md).write_text(to_md(rows, a.fuss), encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
