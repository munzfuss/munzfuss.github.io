"""Where a research original (PDF, scan, ALTO XML) is read from.

Originals live in the research library (``LIBRARY_ROOT``, outside git; see
``scripts/library/library.py`` and docs/plans/research_library_split.md),
under the same relative path they had in the harvest cache
(``fogtman/d1/…pdf``). Until the cache copies are removed (plan step 7) a
file is also accepted from ``HARVEST_ROOT`` — the library wins when both
exist.

A missing original is not a bare FileNotFoundError: the message says how to
restore it (``library.py fetch``), because after step 7 a fresh checkout or
a new machine has the manifest but not the bytes.

Derived text (extracts, ``pages/*.txt``, layout text) is NOT an original and
is never written to the library; ``TEXT_ROOT`` is where it goes — the
harvest cache, which keeps coin data and corpus text alike.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from lib import paths

TEXT_ROOT: Path = paths.HARVEST_ROOT


class MissingOriginal(FileNotFoundError):
    pass


def _roots() -> list[Path]:
    return [paths.LIBRARY_ROOT, paths.HARVEST_ROOT]


def rel_of(p: str | Path) -> str:
    """Library-relative form of ``p`` (relative path, or absolute under a root)."""
    q = Path(p)
    if q.is_absolute():
        for r in _roots():
            try:
                return q.resolve().relative_to(r.resolve()).as_posix()
            except ValueError:
                continue
        return q.as_posix()
    # the older repo-relative spelling «scripts/cache/<rel>» still works
    return q.as_posix().removeprefix("./").removeprefix(paths.LEGACY_CACHE_PREFIX)


def original(p: str | Path) -> Path:
    """The readable file for library path ``p``; absolute paths that exist are
    returned as they are."""
    q = Path(p)
    if q.is_absolute() and q.exists():
        return q
    rel = rel_of(q)
    for r in _roots():
        cand = r / rel
        if cand.exists():
            return cand
    raise MissingOriginal(
        f"original not present: {rel} — restore it with "
        f"`.venv/bin/python scripts/library/library.py fetch {rel}` "
        f"(library root {paths.LIBRARY_ROOT})")


def iter_originals(suffix: str = ".pdf", under: str = "") -> Iterator[tuple[str, Path]]:
    """(relative path, readable file) of every original with ``suffix``,
    library first, then cache files the library does not hold."""
    seen: set[str] = set()
    for r in _roots():
        base = r / under if under else r
        if not base.exists():
            continue
        for f in sorted(base.rglob(f"*{suffix}")):
            rel = f.relative_to(r).as_posix()
            if rel in seen or rel.startswith(("_derived/", ".git/")) or "/.git/" in rel:
                continue
            seen.add(rel)
            yield rel, f
