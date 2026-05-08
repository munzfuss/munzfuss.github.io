"""Shared YAML load/save helpers for one-off data scripts.

Most edit-scripts under `scripts/oneoff/` and `scripts/maintenance/` boil
down to: «open a location YAML, find one or more coins by id, mutate, write
back, preserving formatting and comments». This module factors out the
boilerplate so each script only carries its task-specific predicate /
transformation.

For trivial single-string substitutions (one or two lines) the Edit tool is
still simpler than spinning up a script — use this module when the change
needs structural logic (filter by predicate, insert at position, rebuild a
mapping in conventional key order, etc.).

Conventions (match the rest of the project):
  - `preserve_quotes=True`, `width=4096`, `indent(mapping=2, sequence=4,
    offset=2)` — same settings used by every existing one-off so output
    diffs stay minimal.
  - Per CLAUDE.md «Atomic commits at task boundaries», each script that
    uses these helpers is expected to result in one logical commit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[2]
LOCATIONS_DIR = REPO / "data" / "locations"
SHARED_DIR = REPO / "data" / "shared"
I18N_DIR = REPO / "data" / "i18n"


def make_yaml() -> YAML:
    """Return a ruamel YAML instance configured with the project's
    canonical formatting (matches every existing data file)."""
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def load(path: Path) -> tuple[YAML, Any]:
    """Load any YAML file, returning the configured loader and the parsed
    document. Pass both to `save()` to round-trip the change."""
    y = make_yaml()
    with open(path) as f:
        return y, y.load(f)


def save(y: YAML, path: Path, doc: Any) -> None:
    """Write `doc` back to `path` using the project's YAML conventions."""
    with open(path, "w") as f:
        y.dump(doc, f)


def load_location(name: str) -> tuple[YAML, Path, Any]:
    """Load `data/locations/<name>.yml`. Returns (yaml-instance, path, doc).

    The path is returned so the caller can pass it straight to `save()`
    without rebuilding it from `name`."""
    path = LOCATIONS_DIR / f"{name}.yml"
    y, doc = load(path)
    return y, path, doc


def load_shared(name: str) -> tuple[YAML, Path, Any]:
    """Load `data/shared/<name>.yml`."""
    path = SHARED_DIR / f"{name}.yml"
    y, doc = load(path)
    return y, path, doc


def find_coin(doc: Any, coin_id: str) -> Any | None:
    """Return the coin dict with the matching `id`, or None."""
    for c in doc.get("coins") or []:
        if c.get("id") == coin_id:
            return c
    return None


def coin_index(doc: Any, coin_id: str) -> int | None:
    """Return the list-index of the coin with the matching `id`, or None.

    Useful for `doc['coins'].insert(idx + 1, new_coin)` when adding a
    sister entry right after an existing one."""
    for i, c in enumerate(doc.get("coins") or []):
        if c.get("id") == coin_id:
            return i
    return None
