#!/usr/bin/env python3
"""Step 2 of docs/plans/research_library_split.md: COPY the research
originals out of the harvest cache into LIBRARY_ROOT and write the manifest.

Originals taken:
  * every *.pdf under the cache (tracked and gitignored);
  * every ``alto/`` directory (ALTO XML from nb.no) — one bundle each;
  * ``rigsarkivet/*/pages/`` scan directories (jpg) — one bundle each;
    loose scans elsewhere under ``rigsarkivet/`` — one record each.

Copies use ``cp -c`` (APFS clone): no extra disk space, and the clone stays
valid after the cache file is later removed. The cache is not touched.

URL fields per record:
  * ``source_url`` — a URL that serves THIS file's bytes. Set only when a
    per-file metadata record names the URL and its sha256 equals the file's
    (Secher ``bd<N>/_index.json``). ``library.py fetch`` uses only this.
  * ``work_url`` — the work's ``source_url`` from ``_corpus.yml`` (matched by
    the longest text-layer directory that contains the file), when it is a
    URL. Informational: a split part or a PDF assembled from page images is
    not re-downloadable byte for byte from it.
  * ``work`` — the ``_corpus.yml`` id.
  * wayback PDFs: ``work_url`` = the original URL from ``wayback/_index.json``.

Usage: import_from_cache.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "library"))
from lib.paths import CORPUS_ROOT, HARVEST_ROOT, LIBRARY_ROOT  # noqa: E402
import library as L  # noqa: E402


def originals(cache: Path) -> tuple[list[str], list[str]]:
    files, bundles = [], []
    for p in cache.rglob("*"):
        if ".git" in p.relative_to(cache).parts:
            continue
        rel = p.relative_to(cache).as_posix()
        if p.is_file() and p.suffix.lower() == ".pdf":
            files.append(rel)
        elif (p.is_file() and rel.startswith("rigsarkivet/") and p.parent.name != "pages"
              and p.suffix.lower() in (".jpg", ".tif", ".png")):
            files.append(rel)
        elif p.is_dir() and p.name == "alto":
            bundles.append(rel)
        elif (p.is_dir() and p.name == "pages" and rel.startswith("rigsarkivet/")
              and any(x.suffix.lower() in (".jpg", ".tif", ".png") for x in p.iterdir())):
            bundles.append(rel)
    return sorted(files), sorted(bundles)


def work_dirs(cache: Path) -> list[tuple[str, dict]]:
    d = yaml.safe_load((cache / "_corpus.yml").read_text())
    out = []
    for w in d["works"]:
        for t in w.get("text_layers") or []:
            g = t["glob"]
            parts = []
            for seg in g.split("/"):
                if any(ch in seg for ch in "*?["):
                    break
                parts.append(seg)
            if parts and parts[-1] == "pages":
                parts.pop()
            if parts and "." in parts[-1]:     # a single-file glob
                parts.pop()
            if parts:
                out.append(("/".join(parts), w))
    return sorted(out, key=lambda x: -len(x[0]))


def per_file_urls(cache: Path) -> dict[str, tuple[str, str, str]]:
    """{library path: (url, sha256, fetched)} from per-file metadata."""
    out = {}
    for idx in cache.glob("secher/bd*/_index.json"):
        j = json.loads(idx.read_text())
        out[f"secher/_pdf/bd{j['volume']}.pdf"] = (
            j["source_url"], j["pdf_sha256"], j.get("fetched", ""))
    return out


def clone(src: Path, dst: Path, dry: bool) -> None:
    if dst.exists():
        return
    if dry:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-c", "-R" if src.is_dir() else "-p", str(src), str(dst)],
                   check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cache, lib_root = HARVEST_ROOT, LIBRARY_ROOT
    files, bundles = originals(cache)
    print(f"{len(files)} PDF, {len(bundles)} bundles → {lib_root}")
    for rel in files + bundles:
        clone(cache / rel, lib_root / rel, a.dry_run)
    if a.dry_run:
        return 0

    if not (CORPUS_ROOT / ".git").exists():
        CORPUS_ROOT.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(CORPUS_ROOT)], check=True)

    lib = L.Library(lib_root, CORPUS_ROOT / L.MANIFEST_NAME)
    recs = {r["path"]: r for r in lib.load()}
    wd = work_dirs(cache)
    pf = per_file_urls(cache)
    wb = {f"wayback/{v['file']}": u for u, v in
          json.loads((cache / "wayback" / "_index.json").read_text()).items()
          if isinstance(v, dict) and v.get("file")}
    for rel in files + bundles:
        p = lib_root / rel
        if rel in bundles:
            h, size, n = L.tree_hash(p)
            new = {"path": rel, "kind": "bundle", "sha256": h, "bytes": size, "files": n}
        else:
            new = {"path": rel, "sha256": L.sha256_file(p), "bytes": p.stat().st_size}
        old = recs.get(rel)
        if old and old["sha256"] != new["sha256"]:
            print(f"✗ {rel}: differs from existing record — left as is")
            continue
        rec = dict(old or {})
        rec.update(new)
        if rel in pf and pf[rel][1] == rec["sha256"]:
            rec["source_url"], _, fetched = pf[rel]
            if fetched:
                rec["fetched"] = fetched
        if rel in wb:
            rec["work_url"] = wb[rel]
        if rel.startswith("secher/_pdf/"):
            rec["work"] = "secher-ccd"
        owner = next((w for d, w in wd if rel == d or rel.startswith(d + "/")), None)
        if owner and not rec.get("work"):
            rec["work"] = owner["id"]
            u = str(owner.get("source_url") or "")
            if u.startswith("http") and " " not in u:
                rec["work_url"] = u
        recs[rel] = rec
    lib.save(list(recs.values()))
    allr = list(recs.values())
    print(f"manifest: {len(allr)} records, "
          f"{sum(r['bytes'] for r in allr) / 1e9:.2f} GB; "
          f"source_url {sum(1 for r in allr if r.get('source_url'))}, "
          f"work_url {sum(1 for r in allr if r.get('work_url'))}, "
          f"no work {sum(1 for r in allr if not r.get('work'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
