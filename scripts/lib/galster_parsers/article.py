"""Skip-parser for danskmoent.dk article pages.

The Galster cache mirrors some danskmoent.dk article pages from
`/artikler/` and `/ernst/` folders. These are blog articles ABOUT
coins (provenance studies, find-reports, attribution debates), not
catalog entries for individual coins. Filtering them at parse time
keeps the seed from accumulating article-fragments-as-coins.

Known affected files:
  artikler_ro997999.htm        — provenance article
  artikler_flenobbe.htm        — Flensborgske Blafferte article
  artikler_f1suaa31.htm        — Fund i Forum article
  artikler_kghklipp.htm        — Klippinge article
  ernst_ribeaxe1.htm           — Ribe-Axe study
  ernst_14p1524.htm            — 14-Penning 1524 article

Note: `ernst_f1g50ern.htm` is NOT routed here — it carries a Galster-
number filename token (`g50ern`) which signals a per-coin Ernst-variant
page, not an article. The classifier handles that carve-out.
"""
from __future__ import annotations

from pathlib import Path


def parse_page(html_path: Path, text: str) -> dict:
    return {
        "source_file": html_path.name,
        "source_url_hint": (
            "https://www.danskmoent.dk/" + html_path.name.replace("_", "/")
        ),
        "page_shape": "article",
        "skip": True,
        "skip_reason": (
            "danskmoent.dk article page (not a coin-catalog entry — "
            "filename prefix `artikler_` or `ernst_` without `g\\d+` token)"
        ),
        "raw_text_excerpt": text[:2000],
    }
