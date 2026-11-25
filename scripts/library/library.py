#!/usr/bin/env python3
"""Research library: originals (PDF, scans, ALTO XML) kept OUTSIDE git.

Plan and rationale: docs/plans/research_library_split.md.

Three copies, in the order ``fetch`` tries them:

1. the local library, ``LIBRARY_ROOT`` (default ``~/munzfuss-library``);
2. a release asset in the private repo ``munzfuss/munzfuss-library``
   (one release per top-level directory, asset = path below it with
   ``/`` → ``--``);
3. the origin URL, when one is known. A missing URL is normal, never an
   error — ``status`` only reports which files have a single copy.

The manifest (``HARVEST_ROOT/_library_manifest.yml``, versioned in the
munzfuss-harvest repo next to ``_corpus.yml``) holds one
record per file, or per BUNDLE — a directory of many small files (ALTO XML)
that is backed up as one ``.tar.gz`` because a release takes at most 1000
assets. A bundle's ``sha256`` is a tree hash over its files' relative paths
and hashes, so it does not depend on how the tar was packed; the tar's own
hash is kept as ``backup.asset_sha256``.

Commands::

    library.py add <path>… [--url U] [--fetched YYYY-MM-DD] [--bundle]
    library.py backup [<path>…] [--dry-run]
    library.py fetch  <path>… | --all [--dest DIR]
    library.py verify [<path>…]
    library.py status [--list]

Paths are relative to LIBRARY_ROOT (an absolute path inside it is accepted).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

DEFAULT_REPO = "munzfuss/munzfuss-library"
MANIFEST_NAME = "_library_manifest.yml"
CHUNK = 1 << 20


# ── hashing ──────────────────────────────────────────────────────────────

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest()


def bundle_files(d: Path) -> list[Path]:
    return sorted(p for p in d.rglob("*") if p.is_file())


def tree_hash(d: Path) -> tuple[str, int, int]:
    """(sha256, total bytes, file count) of a directory, independent of
    mtimes and of any tar packing."""
    h = hashlib.sha256()
    total = n = 0
    for p in bundle_files(d):
        rel = p.relative_to(d).as_posix()
        h.update(f"{rel}\0{sha256_file(p)}\n".encode())
        total += p.stat().st_size
        n += 1
    return h.hexdigest(), total, n


def make_tar(d: Path, out: Path) -> None:
    """Deterministic tar.gz of ``d`` (sorted entries, zeroed metadata)."""
    import gzip
    with open(out, "wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tar:
                for p in bundle_files(d):
                    ti = tarfile.TarInfo(p.relative_to(d).as_posix())
                    ti.size = p.stat().st_size
                    ti.mtime = 0
                    ti.mode = 0o644
                    with open(p, "rb") as f:
                        tar.addfile(ti, f)


# ── manifest ─────────────────────────────────────────────────────────────

@dataclass
class Library:
    root: Path
    manifest_path: Path

    def load(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        data = yaml.safe_load(self.manifest_path.read_text()) or {}
        return list(data.get("files") or [])

    def save(self, recs: list[dict]) -> None:
        recs = sorted(recs, key=lambda r: r["path"])
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.manifest_path.with_suffix(".tmp")
        tmp.write_text(
            "# Research library manifest — see scripts/library/library.py.\n"
            + yaml.safe_dump({"files": recs}, allow_unicode=True,
                             sort_keys=False, width=1000))
        tmp.replace(self.manifest_path)

    def rel(self, p: str | Path) -> str:
        pp = Path(p)
        if pp.is_absolute():
            try:
                pp = pp.resolve().relative_to(self.root.resolve())
            except ValueError:
                raise SystemExit(f"✗ {p} is not inside {self.root}")
        s = pp.as_posix().strip("/")
        if not s or s.startswith(".."):
            raise SystemExit(f"✗ bad library path: {p}")
        return s


def asset_location(rec: dict) -> tuple[str, str]:
    """(release tag, asset name) for a record."""
    parts = rec["path"].split("/")
    if len(parts) < 2:
        raise SystemExit(f"✗ {rec['path']}: a library file must sit in a "
                         "top-level directory (that directory is the release)")
    # GitHub rewrites asset names (a space becomes «.»), so the name is made
    # safe here, deterministically: anything outside [A-Za-z0-9._-] → «_».
    name = re.sub(r"[^A-Za-z0-9._-]", "_", "--".join(parts[1:]))
    if rec.get("kind") == "bundle":
        name += ".tar.gz"
    return parts[0], name


# ── backends ─────────────────────────────────────────────────────────────

class GhBackend:
    """Release assets through the ``gh`` CLI."""

    def __init__(self, repo: str):
        self.repo = repo
        self._assets: dict[str, dict[str, str]] = {}

    def _gh(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(["gh", *args, "-R", self.repo] if args[0] == "release"
                              else ["gh", *args], capture_output=True, text=True,
                              check=check)

    def assets(self, tag: str) -> dict[str, str] | None:
        """{asset name: sha256 hex} for a release, None if it does not exist."""
        if tag in self._assets:
            return self._assets[tag]
        r = self._gh("api", f"repos/{self.repo}/releases/tags/{tag}", check=False)
        if r.returncode != 0:
            return None
        out = {}
        for a in json.loads(r.stdout).get("assets") or []:
            dg = a.get("digest") or ""
            out[a["name"]] = dg.split(":", 1)[1] if dg.startswith("sha256:") else ""
        self._assets[tag] = out
        return out

    def ensure_release(self, tag: str) -> None:
        if self.assets(tag) is not None:
            return
        self._gh("release", "create", tag, "--title", tag, "--notes",
                 f"Originals for library path {tag}/. Asset name = path below "
                 f"{tag}/ with '/' -> '--'. Manifest: _library_manifest.yml in "
                 "munzfuss-harvest.")
        self._assets[tag] = {}

    def upload(self, tag: str, asset: str, src: Path) -> str:
        with tempfile.TemporaryDirectory() as td:
            link = Path(td) / asset
            os.symlink(src.resolve(), link)
            self._gh("release", "upload", tag, str(link))
        # GitHub computes the digest asynchronously: right after an upload it
        # can still be empty (seen on a 42 MB PDF, 2026-11-25). Poll briefly.
        import time
        for wait in (0, 2, 4, 8, 16):
            time.sleep(wait)
            self._assets.pop(tag, None)
            got = (self.assets(tag) or {}).get(asset, "")
            if got:
                return got
        return ""

    def download(self, tag: str, asset: str, dest: Path) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._gh("release", "download", tag, "-p", asset, "-D", td)
            shutil.move(str(Path(td) / asset), dest)


def download_url(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f, CHUNK)


# ── commands ─────────────────────────────────────────────────────────────

def cmd_add(lib: Library, paths_: list[str], url: str | None,
            fetched: str | None, bundle: bool, force: bool) -> int:
    recs = {r["path"]: r for r in lib.load()}
    rc = 0
    for raw in paths_:
        rel = lib.rel(raw)
        p = lib.root / rel
        if bundle:
            if not p.is_dir():
                print(f"✗ {rel}: --bundle needs a directory"); rc = 1; continue
            digest, size, n = tree_hash(p)
            new = {"path": rel, "kind": "bundle", "sha256": digest,
                   "bytes": size, "files": n}
        else:
            if not p.is_file():
                print(f"✗ {rel}: no such file under {lib.root}"); rc = 1; continue
            new = {"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size}
        old = recs.get(rel)
        if old and old["sha256"] != new["sha256"] and not force:
            print(f"✗ {rel}: content differs from the manifest record "
                  "(--force to replace the record)"); rc = 1; continue
        rec = dict(old or {})
        if old and old["sha256"] != new["sha256"]:
            rec.pop("backup", None)
        rec.update(new)
        if url:
            rec["source_url"] = url
        if fetched:
            rec["fetched"] = fetched
        recs[rel] = rec
        print(f"{'~' if old else '+'} {rel}  {rec['bytes']} B"
              f"  url: {rec.get('source_url') or 'unknown'}")
    lib.save(list(recs.values()))
    return rc


def cmd_backup(lib: Library, be, only: list[str], dry: bool) -> int:
    recs = lib.load()
    sel = {lib.rel(x) for x in only}
    rc = 0
    for rec in recs:
        if sel and rec["path"] not in sel:
            continue
        if rec.get("backup"):
            continue
        tag, asset = asset_location(rec)
        p = lib.root / rec["path"]
        if not p.exists():
            print(f"✗ {rec['path']}: missing locally, cannot back up"); rc = 1; continue
        if dry:
            print(f"would upload {rec['path']} → {tag}/{asset}"); continue
        with tempfile.TemporaryDirectory() as td:
            if rec.get("kind") == "bundle":
                digest, _, _ = tree_hash(p)
                if digest != rec["sha256"]:
                    print(f"✗ {rec['path']}: bundle changed since add"); rc = 1; continue
                src = Path(td) / asset
                make_tar(p, src)
                want = sha256_file(src)
            else:
                src, want = p, rec["sha256"]
                if sha256_file(p) != want:
                    print(f"✗ {rec['path']}: file changed since add"); rc = 1; continue
            existing = be.assets(tag)
            if existing is not None and asset in existing:
                got = existing[asset]
            else:
                be.ensure_release(tag)
                got = be.upload(tag, asset, src)
        if got != want:
            print(f"✗ {rec['path']}: asset digest {got or '∅'} ≠ {want}"); rc = 1; continue
        rec["backup"] = {"release": tag, "asset": asset}
        if rec.get("kind") == "bundle":
            rec["backup"]["asset_sha256"] = want
        lib.save(recs)
        print(f"✓ {rec['path']} → {tag}/{asset}")
    return rc


def _place_bundle(tar_path: Path, dest: Path, want: str) -> bool:
    with tempfile.TemporaryDirectory(dir=dest.parent) as td:
        out = Path(td) / "x"
        out.mkdir()
        with tarfile.open(tar_path, "r:gz") as t:
            t.extractall(out, filter="data")
        if tree_hash(out)[0] != want:
            return False
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(out), dest)
    return True


def cmd_fetch(lib: Library, be, only: list[str], all_: bool,
              dest_root: Path | None, fetch_url=download_url) -> int:
    recs = lib.load()
    sel = {lib.rel(x) for x in only}
    if not all_ and not sel:
        print("✗ name paths or pass --all"); return 2
    root = dest_root or lib.root
    known = {r["path"] for r in recs}
    rc = 0
    for missing in sorted(sel - known):
        print(f"✗ {missing}: not in the manifest"); rc = 1
    for rec in recs:
        if sel and rec["path"] not in sel:
            continue
        dest = root / rec["path"]
        bundle = rec.get("kind") == "bundle"
        if dest.exists() and (tree_hash(dest)[0] if bundle else sha256_file(dest)) == rec["sha256"]:
            print(f"= {rec['path']} (local)"); continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        done = False
        b = rec.get("backup")
        if b:
            with tempfile.TemporaryDirectory(dir=dest.parent) as td:
                tmp = Path(td) / "dl"
                try:
                    be.download(b["release"], b["asset"], tmp)
                except Exception as e:  # noqa: BLE001 — try the next copy
                    print(f"  {rec['path']}: release download failed ({e})")
                else:
                    if bundle:
                        done = _place_bundle(tmp, dest, rec["sha256"])
                    elif sha256_file(tmp) == rec["sha256"]:
                        shutil.move(str(tmp), dest); done = True
                    if not done:
                        print(f"  {rec['path']}: release copy fails sha256")
            if done:
                print(f"✓ {rec['path']} (release)"); continue
        url = rec.get("source_url")
        if url and not bundle:
            with tempfile.TemporaryDirectory(dir=dest.parent) as td:
                tmp = Path(td) / "dl"
                try:
                    fetch_url(url, tmp)
                except Exception as e:  # noqa: BLE001
                    print(f"✗ {rec['path']}: origin download failed ({e})"); rc = 1; continue
                if sha256_file(tmp) == rec["sha256"]:
                    shutil.move(str(tmp), dest)
                    print(f"✓ {rec['path']} (origin)"); continue
                side = dest.with_name(dest.name + ".origin-mismatch")
                shutil.move(str(tmp), side)
                print(f"⚠ {rec['path']}: the origin now serves different bytes; "
                      f"saved as {side.name}, record unchanged"); rc = 1; continue
        print(f"✗ {rec['path']}: no copy could be fetched"); rc = 1
    return rc


def cmd_verify(lib: Library, only: list[str]) -> int:
    sel = {lib.rel(x) for x in only}
    bad = missing = ok = 0
    for rec in lib.load():
        if sel and rec["path"] not in sel:
            continue
        p = lib.root / rec["path"]
        if not p.exists():
            missing += 1; print(f"– {rec['path']}: missing locally"); continue
        got = tree_hash(p)[0] if rec.get("kind") == "bundle" else sha256_file(p)
        if got != rec["sha256"]:
            bad += 1; print(f"✗ {rec['path']}: sha256 differs from the manifest")
        else:
            ok += 1
    print(f"verify: {ok} ok, {bad} differ, {missing} missing locally")
    return 1 if bad else 0


def cmd_status(lib: Library, listing: bool) -> int:
    recs = lib.load()
    single, missing, nourl = [], [], []
    covered: set[Path] = set()
    for r in recs:
        p = lib.root / r["path"]
        if not p.exists():
            missing.append(r["path"])
        if not r.get("source_url"):
            nourl.append(r["path"])
        if not r.get("backup") and not r.get("source_url"):
            single.append(r["path"])
        covered.add(p)
    unrecorded = []
    if lib.root.exists():
        for p in sorted(lib.root.rglob("*")):
            if not p.is_file() or p.name.startswith("."):
                continue
            if p in covered or any(a in covered for a in p.parents):
                continue
            unrecorded.append(p.relative_to(lib.root).as_posix())
    size = sum(r.get("bytes", 0) for r in recs)
    print(f"library: {lib.root}\nmanifest: {lib.manifest_path}")
    print(f"{len(recs)} records, {size / 1e9:.2f} GB; "
          f"{sum(1 for r in recs if r.get('backup'))} backed up, "
          f"{len(recs) - len(nourl)} with origin URL")
    for label, items in (("single copy (no backup, no URL)", single),
                         ("missing locally", missing),
                         ("unrecorded files", unrecorded)):
        print(f"{label}: {len(items)}")
        if listing:
            for it in items:
                print(f"    {it}")
    return 0


def default_library() -> Library:
    return Library(paths.LIBRARY_ROOT, paths.HARVEST_ROOT / MANIFEST_NAME)


def register(rel: str, *, url: str | None = None, fetched: str | None = None,
             bundle: bool = False) -> None:
    """For fetchers: record a just-written original (or ALTO tree) in the
    manifest. A changed file/tree replaces its record (a re-fetch or a tree
    that grew); the old backup entry is dropped so ``backup`` uploads anew."""
    cmd_add(default_library(), [rel], url, fetched, bundle, force=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=None, help="library root")
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--repo", default=os.environ.get("MUNZFUSS_LIBRARY_REPO", DEFAULT_REPO))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("paths", nargs="+")
    a.add_argument("--url"); a.add_argument("--fetched")
    a.add_argument("--bundle", action="store_true"); a.add_argument("--force", action="store_true")
    b = sub.add_parser("backup"); b.add_argument("paths", nargs="*")
    b.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("fetch"); f.add_argument("paths", nargs="*")
    f.add_argument("--all", action="store_true"); f.add_argument("--dest", type=Path)
    v = sub.add_parser("verify"); v.add_argument("paths", nargs="*")
    s = sub.add_parser("status"); s.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    root = (args.root or paths.LIBRARY_ROOT).expanduser()
    lib = Library(root, (args.manifest or paths.HARVEST_ROOT / MANIFEST_NAME).expanduser())
    if args.cmd == "add":
        return cmd_add(lib, args.paths, args.url, args.fetched, args.bundle, args.force)
    if args.cmd == "backup":
        return cmd_backup(lib, GhBackend(args.repo), args.paths, args.dry_run)
    if args.cmd == "fetch":
        return cmd_fetch(lib, GhBackend(args.repo), args.paths, args.all, args.dest)
    if args.cmd == "verify":
        return cmd_verify(lib, args.paths)
    return cmd_status(lib, args.list)


if __name__ == "__main__":
    sys.exit(main())
