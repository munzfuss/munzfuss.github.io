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
# danskmoent.dk concordance page (konkord.htm) — added 2026-07-30. A
# concordance is a list equating the catalogue numbers of two different
# catalogues, or of two editions of the same one. Two blocks: Hauberg /
# Mansfeld-Bullner for 1241-1375 (outside our 1514+ scope, harvested for
# completeness) and the Sieg 2001 renumbering of Christian VII, which IS
# in scope and is why we harvest the page at all — our `sieg` citations
# do not record which edition they came from.
KONKORDANS_CACHE: Path = HARVEST_ROOT / "danskmoent" / "konkordans"
# danskmoent.dk per-coin pages of Mansfeld-Bûllner (mb/mbNNN.htm), 1241-1375 —
# added 2026-10-17. Each page lines up one MB number with Hauberg, Kaaber,
# Sømod and Grinder-Hansen (ruler / mint / dating), which the concordance
# page gives only as Hauberg↔MB ranges.
MB_CACHE: Path = HARVEST_ROOT / "danskmoent" / "mb"
# danskmoent.dk «Forordninger m.v. vedr. Møntvæsenet under Enevælden» —
# added 2026-10-13 for the coinage-instruments register. Mordhorst, Dansk
# Pengehistorie III (Bilag), pp. 159-264, transcribed per reign:
# artikler/mord.htm (index) + f3mord … f7mord.htm (1661-1849).
MORD_CACHE: Path = HARVEST_ROOT / "danskmoent" / "mord"
# Secher, Corpus constitutionum Daniæ (1558-1660, 6 Bd.) — the printed
# Danish ordinances; KB digitisation served by kildeskriftselskabet.dk.
SECHER_CACHE: Path = HARVEST_ROOT / "secher"
# Schou, Chronologisk Register over de Kongelige Forordninger (from 1670);
# nb.no digibok, per-page ALTO OCR.
SCHOU_CACHE: Path = HARVEST_ROOT / "schou"
# NumisMaster (Librios) commercial catalogue — added 2026-05-16 per §AZ
# Tier 3 + Phase 1b full inventory walk. Layout under HARVEST_ROOT/numismaster:
#   denmark_pre_1541/MC_<N>.html + .json  — legacy §AZ subdir (3 entries)
#   <sub_scope>/MC_<N>.html + .meta.json  — future Phase 4 urllib fetch output
#       (sub_scope ∈ {schleswig_holstein, denmark, norway})
#   mc_index.json                          — consolidated MC_NNNNN inventory
#                                            per country_filter (Phase 1b output)
#   _walks/                                — raw Chrome-MCP-walked page-text
#                                            dumps per filtered search-result
#                                            page; provenance for mc_index +
#                                            input for downstream MC_ID
#                                            extraction not yet anchored
NUMISMASTER_CACHE: Path = HARVEST_ROOT / "numismaster"
# KMK / KMM — Royal Coin Cabinet Copenhagen (Den Kgl. Mønt- og
# Medaillesamling), harvested via the Nationalmuseet open API
# (api.natmus.dk). Whole-record `_source` JSON per file: kmk/<id>.json.
# Strategy + field mapping: docs/KMK_HARVEST.md. Added 2026-06-01.
KMK_CACHE: Path = HARVEST_ROOT / "kmk"
# NGC World Coin Price Guide — the LIVE successor to NumisMaster (which went
# offline; see docs/SOURCES.md §1.4). Same Active Interest Media catalogue
# under new custody, so authority sits at-or-below NumisMaster, never above.
#
# Cloudflare gates every non-browser client: urllib, requests and Playwright
# (7 configs, all blocked — §13.13(c2)) cannot reach it. Harvest therefore
# runs as an in-page fetch() loop in a real browser session, and the records
# arrive here as already-extracted JSON. Layout:
#   _regions.json               — region taxonomy per country (captured once)
#   <region>/_listing.json      — cuid → detail-href map from the pager walk
#   <region>/cuid_<N>.json      — one extracted record per coin TYPE
#   <region>/cuid_<N>.txt       — page innertext, provenance for the record
NGC_CACHE: Path = HARVEST_ROOT / "ngc"


def refresh() -> None:
    """Re-read MUNZFUSS_HARVEST_DIR from env and update all constants.

    Call this from scripts that invoke ``load_local_env()`` AFTER
    importing ``lib.paths``. Most scripts won't need this — they either
    set the env var in the shell before launch, or they load local.env
    before doing any actual cache I/O so the eager resolution at import-
    time is already correct.
    """
    global HARVEST_ROOT, HEDE_CACHE, IKMK_CACHE, NUMISTA_CACHE, UCOIN_CACHE, BRUUN_CACHE, GALSTER_CACHE, KONKORDANS_CACHE, NUMISMASTER_CACHE, KMK_CACHE, NGC_CACHE
    global MORD_CACHE, SECHER_CACHE, SCHOU_CACHE, MB_CACHE
    HARVEST_ROOT = _resolve_harvest_root()
    MORD_CACHE = HARVEST_ROOT / "danskmoent" / "mord"
    SECHER_CACHE = HARVEST_ROOT / "secher"
    SCHOU_CACHE = HARVEST_ROOT / "schou"
    HEDE_CACHE = HARVEST_ROOT / "hede"
    IKMK_CACHE = HARVEST_ROOT / "ikmk"
    NUMISTA_CACHE = HARVEST_ROOT / "numista"
    UCOIN_CACHE = HARVEST_ROOT / "ucoin"
    BRUUN_CACHE = HARVEST_ROOT / "bruun"
    GALSTER_CACHE = HARVEST_ROOT / "danskmoent" / "galster"
    KONKORDANS_CACHE = HARVEST_ROOT / "danskmoent" / "konkordans"
    MB_CACHE = HARVEST_ROOT / "danskmoent" / "mb"
    NUMISMASTER_CACHE = HARVEST_ROOT / "numismaster"
    KMK_CACHE = HARVEST_ROOT / "kmk"
    NGC_CACHE = HARVEST_ROOT / "ngc"
