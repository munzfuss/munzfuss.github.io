"""Centralised filesystem paths for the project.

The single source of truth for **harvest-cache** locations. Every fetcher,
parser, audit and maintenance script imports its per-source cache directory
from this module instead of declaring its own ``Path(...)``. That gives:

* One canonical concept of «cache root» (``HARVEST_ROOT``) — the directory
  mounted as the ``munzfuss-harvest`` git submodule at ``scripts/cache/``.
* Mobility: the cache root can be relocated by setting
  ``MUNZFUSS_HARVEST_DIR`` in ``local.env`` (or the process environment).
  Useful for putting the 124 MB cache on an external SSD without forking
  ~30 scripts.
* Pattern-B fix: previously many scripts declared
  ``CACHE_DIR = Path("scripts/cache/<src>")`` (relative to CWD). Those
  scripts silently mis-resolved when invoked from any directory other
  than the repo root. Importing from ``lib.paths`` bypasses CWD entirely.

``HARVEST_ROOT`` resolves in this order:

1. ``$MUNZFUSS_HARVEST_DIR`` from the environment (set in shell or via
   ``local.env`` after ``load_local_env()`` has run).
2. ``<repo>/scripts/cache`` — the default submodule mount point.

Note: ``local.env`` is loaded lazily by individual scripts (not at module-
import time here), so callers that rely on the override must call
``load_local_env()`` BEFORE reading constants from this module. In
practice, scripts that hit ``HARVEST_ROOT`` already call
``load_local_env()`` near the top of their ``main()``.

Import pattern:

    from lib.paths import HEDE_CACHE, IKMK_CACHE  # noqa: E402
"""
from __future__ import annotations
import os
from pathlib import Path

# Project root (the repo containing this file's grandparent).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]


def _resolve_harvest_root() -> Path:
    """Resolve harvest cache root, honouring the env override.

    Called lazily on each constant lookup so a ``load_local_env()`` call
    that happens after ``lib.paths`` is first imported still takes effect.
    """
    override = os.environ.get("MUNZFUSS_HARVEST_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return PROJECT_ROOT / "scripts" / "cache"


# Eagerly compute the default at import-time AND expose a refresh hook
# for callers that load local.env after first import.
HARVEST_ROOT: Path = _resolve_harvest_root()

# Per-source cache directories. Stay in sync with the directory structure
# in the munzfuss-harvest submodule.
HEDE_CACHE: Path = HARVEST_ROOT / "hede"
IKMK_CACHE: Path = HARVEST_ROOT / "ikmk"
NUMISTA_CACHE: Path = HARVEST_ROOT / "numista"
UCOIN_CACHE: Path = HARVEST_ROOT / "ucoin"
BRUUN_CACHE: Path = HARVEST_ROOT / "bruun"
# danskmoent.dk Galster page series — added 2026-05-16 per §AZ Tier 2.
# Hosts Galster-numbered per-coin pages for pre-Christian-III rulers
# (Hede 1957 doesn't catalogue Christian II / Frederik I / Christian III
# pre-1541). URL patterns: chr/c2g<N>.htm, fr/f1g<N>.htm, norge/n<r>g<N>.htm.
GALSTER_CACHE: Path = HARVEST_ROOT / "danskmoent" / "galster"


def refresh() -> None:
    """Re-read MUNZFUSS_HARVEST_DIR from env and update all constants.

    Call this from scripts that invoke ``load_local_env()`` AFTER
    importing ``lib.paths``. Most scripts won't need this — they either
    set the env var in the shell before launch, or they load local.env
    before doing any actual cache I/O so the eager resolution at import-
    time is already correct.
    """
    global HARVEST_ROOT, HEDE_CACHE, IKMK_CACHE, NUMISTA_CACHE, UCOIN_CACHE, BRUUN_CACHE, GALSTER_CACHE
    HARVEST_ROOT = _resolve_harvest_root()
    HEDE_CACHE = HARVEST_ROOT / "hede"
    IKMK_CACHE = HARVEST_ROOT / "ikmk"
    NUMISTA_CACHE = HARVEST_ROOT / "numista"
    UCOIN_CACHE = HARVEST_ROOT / "ucoin"
    BRUUN_CACHE = HARVEST_ROOT / "bruun"
    GALSTER_CACHE = HARVEST_ROOT / "danskmoent" / "galster"
