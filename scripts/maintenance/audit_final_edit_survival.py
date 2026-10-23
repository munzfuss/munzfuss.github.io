#!/usr/bin/env python3
"""READ-ONLY: which hand edits on the finals does a rebuild undo?

A commit that changed `data/v2/final/*` without a seed or `seed_unified`
change is an edit the pipeline did not make, and cannot re-make. For every
such commit this lists, per coin and field:

    added     a value the commit put on the final that HEAD still holds, and
              the finals on disk (the rebuild) do NOT — the edit is undone
    deleted   a value the commit took off the final, absent at HEAD, that the
              finals on disk hold again — the deletion is undone

The commit subject tells a curator decision («Galster 68 narrowed to 1524
after Ernst») from a pipeline output («absorb re-merged …»); nothing here
decides that. Values are compared as `lib.final_derivation.items` does; a
coin renamed since (D49) is followed by `label` / `legacy_id`.

    .venv/bin/python scripts/maintenance/audit_final_edit_survival.py [--since 2026-06-01] [--json out.json]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib.final_derivation import items  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
IGN = {"id", "composed_of", "label", "legacy_id", "origin", "class_id", "__order__",
       "_migration_note", "v1_home_location", "generated_at"}
PIPELINE_RE = re.compile(r"absorb|re-flow|reflow|re-absorb|re-merge|fixed.point|regenerate|D49|legacy_id|"
                         r"re-sync|serializ|field-order|bootstrap|rename curated|restore-v1|propagat", re.I)


def _git(args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def _coins(text):
    return {c["id"]: c for c in (yaml.load(text, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")}


def _resolve(m, cid):
    c = m.get(cid)
    if c is None:
        for x in m.values():
            if cid in (x.get("label"), x.get("legacy_id")):
                return x
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default="2026-05-18")
    ap.add_argument("--json")
    ap.add_argument("--show", type=int, default=40)
    a = ap.parse_args()

    # final-only commits
    log = _git(["log", "--format=%x00%h|%ad|%s", "--date=short", "--name-only", f"--since={a.since}"])
    commits = []
    for chunk in log.split("\x00")[1:]:
        head, _, files = chunk.partition("\n")
        h, d, s = head.split("|", 2)
        fs = [f for f in files.split("\n") if f.strip()]
        finals = [f for f in fs if f.startswith("data/v2/final/") and f.endswith(".yml")]
        seeds = [f for f in fs if f.startswith(("data/v2/seed/", "data/v2/seed_unified/"))]
        if finals and not seeds:
            commits.append((h, d, s, finals))

    now, headf = {}, {}
    for p in sorted((ROOT / "data/v2/final").glob("*.yml")):
        now[p.stem] = _coins(p.read_text())
        headf[p.stem] = _coins(_git(["show", f"HEAD:data/v2/final/{p.stem}.yml"]))

    out = []
    tot = collections.Counter()
    for h, d, s, finals in commits:
        undone_add, undone_del, kept = [], [], 0
        for f in finals:
            ent = Path(f).stem
            before = _coins(_git(["show", f"{h}~1:{f}"]))
            after = _coins(_git(["show", f"{h}:{f}"]))
            cur, hd = now.get(ent, {}), headf.get(ent, {})
            for cid in set(before) | set(after):
                b, af = before.get(cid, {}), after.get(cid, {})
                c, hc = _resolve(cur, cid), _resolve(hd, cid)
                if hc is None:
                    continue  # not at HEAD any more — later history, not the rebuild
                for fld in set(b) | set(af):
                    if fld in IGN:
                        continue
                    ib, ia = items(fld, b.get(fld)), items(fld, af.get(fld))
                    ih, ic = items(fld, hc.get(fld)), items(fld, c.get(fld)) if c else set()
                    for x in (ia - ib) & ih:          # added, HEAD still holds
                        if x in ic:
                            kept += 1
                        else:
                            undone_add.append((cid, fld, str(x)[:90]))
                    for x in (ib - ia) - ih:          # deleted, absent at HEAD
                        if x in ic:
                            undone_del.append((cid, fld, str(x)[:90]))
        if undone_add or undone_del:
            out.append({"h": h, "d": d, "s": s, "kind": "pipeline" if PIPELINE_RE.search(s) else "edit",
                        "kept": kept, "undone_added": undone_add, "undone_deleted": undone_del})
        tot["kept"] += kept
        tot["undone_added"] += len(undone_add)
        tot["undone_deleted"] += len(undone_del)

    print(f"final-only commits since {a.since}: {len(commits)}; with something undone: {len(out)}; "
          f"values kept {tot['kept']}, undone added {tot['undone_added']}, undone deleted {tot['undone_deleted']}")
    for kind in ("edit", "pipeline"):
        rows = [o for o in out if o["kind"] == kind]
        print(f"\n== {kind} commits ({len(rows)})")
        for o in sorted(rows, key=lambda o: -(len(o["undone_added"]) + len(o["undone_deleted"])))[:a.show]:
            print(f"{o['h']} {o['d']} kept={o['kept']:5} undone: +{len(o['undone_added']):4} -{len(o['undone_deleted']):4}  {o['s'][:85]}")
            for e in (o["undone_added"][:2] + o["undone_deleted"][:2]):
                print("      ", e)
    if a.json:
        Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
