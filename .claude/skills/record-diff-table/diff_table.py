#!/usr/bin/env python3
"""Difference table between two coin records — READ-ONLY.

Four columns: field, record A, record B, comment. One row per field that differs;
equal fields are not shown. `sources` are compared by URL only — the
`ref` label is ignored (curator 2026-10-23), so a relabelled citation is
not a difference and a citation present on one side only is.

Record spec (either side):
    final:<entity>:<id>[@<git-ref>]      an entry of data/v2/final/<entity>.yml
    unified:<entity>:<id>[@<git-ref>]    an entry of data/v2/seed_unified/<entity>.yml
    seed:<seed-id>[@<git-ref>]           a seed entry (searched in data/v2/seed/*/)
Without `@ref` the working tree is read; `@main`, `@HEAD`, `@<sha>` read
that revision via `git show`.

    .venv/bin/python .claude/skills/record-diff-table/diff_table.py \
        final:royal_holstein:km-105-chr-v-1683@main \
        final:royal_holstein:km-105-chr-v-1683

Options:
    --order         also report lists that differ only in order
    --ignore F,G    skip these fields (dotted paths, prefix match: `note`)
    --full          do not shorten long values
    --json          machine-readable rows instead of markdown

The comment column is filled with a mechanical tag (only in A / only in B /
differs / order only). It is a placeholder: the agent replaces it with the
judgment or the proposal (see SKILL.md). A missing record raises.
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
_SKIP_ALWAYS = {"__order__"}


def _read(path: str, ref: str | None) -> str:
    if ref is None:
        return (ROOT / path).read_text()
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git show {ref}:{path} failed: {r.stderr.strip()}")
    return r.stdout


def _entries(text: str) -> list[dict]:
    d = yaml.safe_load(text) or {}
    if isinstance(d, dict):
        return d.get("coins") or d.get("entries") or []
    return d


def _find(entries: list[dict], cid: str, where: str) -> dict:
    hits = [e for e in entries if isinstance(e, dict) and e.get("id") == cid]
    if not hits:
        raise SystemExit(f"record {cid!r} not found in {where}")
    return hits[0]


def load(spec: str) -> tuple[str, dict]:
    body, _, ref = spec.partition("@")
    ref = ref or None
    kind, _, rest = body.partition(":")
    if kind in ("final", "unified"):
        entity, _, cid = rest.partition(":")
        if not cid:
            raise SystemExit(f"bad spec {spec!r}: need {kind}:<entity>:<id>")
        layer = "final" if kind == "final" else "seed_unified"
        path = f"data/v2/{layer}/{entity}.yml"
        return spec, _find(_entries(_read(path, ref)), cid, f"{path}@{ref or 'worktree'}")
    if kind == "seed":
        cid = rest
        needle = f"id: {cid}"
        for p in sorted(glob.glob(str(ROOT / "data/v2/seed/*/*.yml"))):
            rel = str(Path(p).relative_to(ROOT))
            # cheap pre-filter on the working tree; the revision is read only for a hit
            if needle not in Path(p).read_text():
                continue
            text = _read(rel, ref)
            if needle in text:
                return spec, _find(_entries(text), cid, f"{rel}@{ref or 'worktree'}")
        raise SystemExit(f"seed {cid!r} not found under data/v2/seed/")
    raise SystemExit(f"bad spec {spec!r}: kind must be final / unified / seed")


def _canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)


def _flatten(rec: dict, prefix: str = "", other: dict | None = None) -> dict[str, object]:
    """Dicts are walked into dotted paths; lists and scalars are leaves.
    A dict whose counterpart on the other side is NOT a dict stays one leaf,
    so a change of shape (`km: [73, 105]` → `km: {dk: 73, sh: 105}`) is one
    row. `sources` becomes one leaf per URL (`sources[<url>]`)."""
    out: dict[str, object] = {}
    other = other if isinstance(other, dict) else {}
    for k, v in rec.items():
        if k in _SKIP_ALWAYS:
            continue
        path = f"{prefix}{k}"
        o = other.get(k)
        if isinstance(v, dict) and k in other and not isinstance(o, dict):
            out[path] = v
            continue
        if path == "sources" and isinstance(v, list):
            for s in v:
                url = s.get("url") if isinstance(s, dict) else s
                ref = s.get("ref") if isinstance(s, dict) else None
                out[f"sources[{url}]"] = ref if ref is not None else url
            continue
        if isinstance(v, dict):
            out.update(_flatten(v, path + ".", o))
        else:
            out[path] = v
    return out


def _short(v, full: bool) -> str:
    s = v if isinstance(v, str) else _canon(v)
    s = s.replace("|", "\\|").replace("\n", " ")
    return s if full or len(s) <= 90 else s[:87] + "…"


def diff(a: dict, b: dict, order: bool, ignore: list[str]) -> list[dict]:
    fa, fb = _flatten(a, other=b), _flatten(b, other=a)
    rows = []
    for key in sorted(set(fa) | set(fb), key=lambda k: (k.startswith("sources["), k)):
        if any(key == g or key.startswith(g + ".") or key.startswith(g + "[") for g in ignore):
            continue
        ina, inb = key in fa, key in fb
        if key.startswith("sources["):
            if ina and inb:
                continue  # same URL — the label is not compared
            rows.append({"field": key, "a": "✓" if ina else "—", "b": "✓" if inb else "—",
                         "tag": "лише в A" if ina else "лише в B"})
            continue
        va, vb = fa.get(key), fb.get(key)
        if ina and inb and _canon(va) == _canon(vb):
            continue
        if (ina and inb and isinstance(va, list) and isinstance(vb, list)
                and sorted(map(_canon, va)) == sorted(map(_canon, vb))):
            if order:
                rows.append({"field": key, "a": va, "b": vb, "tag": "лише порядок"})
            continue
        tag = "лише в A" if not inb else "лише в B" if not ina else "відрізняється"
        rows.append({"field": key, "a": va if ina else None, "b": vb if inb else None, "tag": tag})
    return rows


def render(sa: str, sb: str, rows: list[dict], full: bool) -> str:
    lines = [f"A = `{sa}`", f"B = `{sb}`", "",
             "| поле | A | B | коментар |", "|---|---|---|---|"]
    for r in rows:
        a = "—" if r["a"] is None else _short(r["a"], full)
        b = "—" if r["b"] is None else _short(r["b"], full)
        field = r["field"]
        if field.startswith("sources["):
            a, b = (field[8:-1] if r["a"] == "✓" else "—"), (field[8:-1] if r["b"] == "✓" else "—")
            field = "sources"
        lines.append(f"| `{field}` | {a} | {b} | {r['tag']} |")
    if not rows:
        lines.append("| — | — | — | відмінностей немає |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--order", action="store_true")
    ap.add_argument("--ignore", default="")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    sa, ra = load(args.a)
    sb, rb = load(args.b)
    ignore = [g for g in args.ignore.split(",") if g]
    rows = diff(ra, rb, args.order, ignore)
    if args.json:
        print(json.dumps({"a": sa, "b": sb, "rows": rows}, ensure_ascii=False, indent=1, default=str))
    else:
        print(render(sa, sb, rows, args.full))
    return 0


if __name__ == "__main__":
    sys.exit(main())
