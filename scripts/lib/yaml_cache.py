"""Parse a YAML text once, across processes and runs.

The merger, absorb and the build each parse the same ~70 MB of
`data/v2/{seed,seed_unified,final}` — libyaml takes 3-7 s for each of the big
files — and most of those files are unchanged between two runs (an
experiment changes a decision, not the seeds). `load(text)` keys the parsed
document by the SHA-1 of the text and keeps it as a pickle under
`output/yaml_cache/` (gitignored); a later call with the same text unpickles
it (~0.2 s for a 10 MB file) instead of parsing.

Same objects as `yaml.load(text, CSafeLoader)`: the cached value IS that
parse, and the data files hold only plain YAML scalars, lists and dicts
(pickle keeps a document's aliased nodes shared). The key includes the
Python and PyYAML versions. Every call returns a fresh object. A corrupt
or unreadable cache entry is ignored and re-parsed. `MUNZFUSS_YAML_CACHE=0`
turns the cache off; the directory can be deleted at any time.
"""
from __future__ import annotations

import hashlib
import os
import pickle
import sys
from pathlib import Path

import yaml

_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_DIR = Path(__file__).resolve().parents[2] / "output" / "yaml_cache"
_SALT = (f"{sys.version_info[:3]}|{yaml.__version__}|{_LOADER.__name__}|1"
         ).encode()
# Keep the directory bounded: past this size the oldest entries go.
_MAX_BYTES = 3 * 1024 ** 3


def enabled() -> bool:
    return os.environ.get("MUNZFUSS_YAML_CACHE", "1") != "0"


def load(text: str):
    """`yaml.load(text, CSafeLoader)`, from the cache when this text was
    parsed before."""
    return memo("load", text, lambda: yaml.load(text, Loader=_LOADER))


def memo(namespace: str, text: str, compute):
    """`compute()` — a pure function of `text` — cached under (namespace,
    text). Used for the parse itself and for results derived only from a
    file's text (the duplicate-key scan)."""
    if not enabled():
        return compute()
    key = hashlib.sha1(_SALT + namespace.encode() + b"\0"
                       + text.encode("utf-8")).hexdigest()
    path = _DIR / f"{key}.pickle"
    try:
        blob = path.read_bytes()
    except OSError:
        blob = None
    if blob is not None:
        try:
            value = pickle.loads(blob)
            try:
                os.utime(path)          # recently used: kept by _prune
            except OSError:
                pass
            return value
        except Exception:
            pass
    value = compute()
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_bytes(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        os.replace(tmp, path)
        _prune()
    except OSError:
        pass
    return value


def load_path(path: Path):
    """`load` of a file's text (read as `Path.read_text(encoding="utf-8")`)."""
    return load(Path(path).read_text(encoding="utf-8"))


def _prune() -> None:
    try:
        entries = [(p.stat().st_mtime, p.stat().st_size, p)
                   for p in _DIR.glob("*.pickle")]
    except OSError:
        return
    total = sum(e[1] for e in entries)
    if total <= _MAX_BYTES:
        return
    for _mt, size, p in sorted(entries):
        try:
            p.unlink()
        except OSError:
            pass
        total -= size
        if total <= _MAX_BYTES * 0.8:
            break
