"""Detect which Galster page-shape parser to dispatch to.

The classifier is intentionally narrow — each rule fires on one
specific signal (filename pattern or H1 content) and the first match
wins. New shapes get added as a new rule at the appropriate priority,
NOT by extending an existing rule.

See ``scripts/lib/galster_parsers/__init__.py`` for the shape catalogue.
"""
from __future__ import annotations

import re
from pathlib import Path

# Reign-overview pages: explicit filename pattern.
# Names look like:
#   - `c2galst.htm` (Christian 2)
#   - `f1galst.htm` (Frederik 1)
#   - `hans.htm`    (Hans — uses the ruler's name directly rather than
#                   the `<letter><digit>galst` convention, since Hans
#                   is the only Danish-Norwegian Hans and needs no
#                   reign-number disambiguator)
# The `galst` token is the reign-overview marker for Christian/Frederik
# (vs. coin-page `g37`, `g46` etc. which use single-letter `g`). Hans
# requires an explicit filename match.
_REIGN_INDEX_FILENAME_RE = re.compile(r"^(c|f)\d+galst\.htm$|^hans\.htm$")

# Article-folder filename prefixes. `artikler_*` (danskmoent.dk blog
# articles) always skip. `ernst_*` is more nuanced — Ernst-Hede sometimes
# publishes a per-coin variant page that DOES carry a Galster-number
# component (e.g. `ernst_f1g50ern.htm` = Galster 50 variant per Ernst);
# those are legitimate coin pages and pass through.
_ARTICLE_FILENAME_RE = re.compile(r"^artikler_")
_ERNST_FILENAME_RE = re.compile(r"^ernst_")
# A `g\d+` token anywhere in the ernst-* filename signals a coin-variant
# rather than a generic article.
_ERNST_COIN_NUM_RE = re.compile(r"g\d+")

# Possessive-H1 pattern: «Christian 2.s tilhængere…», «Frederik 1.s …».
# The trailing `.s` (period-then-s, no apostrophe — Danish possessive
# form) is the distinguishing feature: a standard coin-page H1 has
# `Christian 2., 1 Nobel, …` (period-then-comma) instead.
_POSSESSIVE_H1_RE = re.compile(
    r"^(Christian|Frederik|Hans|Margrethe|Erik|Olav|Olaf)\s+\d+\.s\s+",
)

# Coin-page filename signatures. A filename matching ANY of these is
# a per-coin page (Christian II / Frederik I / Hans / Christian III
# under their respective subfolder + Hans's root-level Hvid + Gotland-
# Hans + Norway-Hans variants). A filename matching NONE of these
# AND none of the article / reign-index patterns is an overview page
# (1nobel.htm, 2skill.htm, guldgyld.htm, …) — fetched into the cache
# by `fetch_galster.py overviews` for cross-ref extraction but NOT
# itself a coin page; should be skipped by the parser.
_COIN_PAGE_PREFIXES = ("chr_", "fr_", "norge_")
_COIN_PAGE_ROOT_RE = re.compile(r"^(?:hansg|gotlg)\d+[\w\-]*\.htm$")


def _extract_first_h1(text: str) -> str | None:
    """Return the first non-empty `## ` header line, or None.

    The Galster pages flatten <H1>/<H2>/<H3> all into `## ` lines via
    ``parse_galster._normalise_text``. The «H1» here is the first such
    line in the body — typically carrying the ruler + denomination on
    standard pages, or the thematic header on Grevens-Fejde pages.
    """
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("## "):
            content = line[3:].strip()
            if content:
                return content
    return None


def detect_page_shape(html_path: Path, text: str) -> str:
    """Classify a Galster cache page into a shape tag.

    Priority order — first match wins:
      1. Reign-overview filename → ``reign_index``
      2. Article filename (with ernst-coin-variant carve-out) → ``article``
      3. Non-coin-page filename (overview pages from /type.htm) → ``reign_index``
      4. Possessive-H1 content → ``grevenfejde``
      5. Default → ``standard``

    Returns one of: ``"standard"``, ``"grevenfejde"``, ``"reign_index"``,
    ``"article"``.
    """
    name = html_path.name

    # 1. Reign-overview tables — explicit filename match
    if _REIGN_INDEX_FILENAME_RE.match(name):
        return "reign_index"

    # 2. Article folders — `artikler_*` always; `ernst_*` only when
    # there's no `g\d+` coin-variant token in the filename.
    if _ARTICLE_FILENAME_RE.match(name):
        return "article"
    if _ERNST_FILENAME_RE.match(name) and not _ERNST_COIN_NUM_RE.search(name):
        return "article"

    # 3. Filename doesn't match any per-coin URL signature → overview
    # page (1nobel.htm, guldgyld.htm, 2skill.htm, …) fetched into
    # the cache by the `overviews` phase for cross-ref extraction.
    # Routed to the reign_index skip-parser. Type.htm itself + any
    # future root-level non-coin filename also lands here.
    is_coin_page = (
        name.startswith(_COIN_PAGE_PREFIXES)
        or _COIN_PAGE_ROOT_RE.match(name)
    )
    if not is_coin_page:
        return "reign_index"

    # 4. Possessive-H1 pages (Grevens Fejde series). Check H1 content
    # only AFTER filename rules so we don't false-positive on a
    # hypothetical article whose H1 happens to use possessive form.
    h1 = _extract_first_h1(text)
    if h1 and _POSSESSIVE_H1_RE.match(h1):
        return "grevenfejde"

    # 5. Default coin-page shape
    return "standard"
