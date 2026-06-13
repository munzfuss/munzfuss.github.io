"""Fuss cross-reference system (introduced 2026-06-11).

Prose anywhere in the project — `fuesse.yml::<fuss>.description`,
`<loc>.yml::fuss_periods.<fuss>.{hintergrund,closing,…}`, grundwerte
rows, rechnungsfraktionen, etc. — can reference another Müntzfuß by its
STABLE ID instead of hand-writing its display name:

    … nicht verwandt mit der [fuss:rosenobel_fod]-Linie …

At build time (after the Jinja template render, alongside the
`refs_pool` pass) this module:

1. Scans the rendered HTML for `[fuss:KEY]` markers.
2. Substitutes the EFFECTIVE display name for KEY on THIS page+language
   (the caller passes a pre-resolved `name_map` that already honours
   per-location `fuss_periods[KEY].name` overrides — e.g. the global
   `reichsdukatenfuss` card renders as «Reichsdukatenfuß», but on the
   Denmark page its override displays «Rigsdukatfod»).
3. Wraps the name in a clickable link to the card anchor `#fuss-KEY`
   WHEN that anchor is present on the page (the card is rendered here);
   otherwise renders plain `<code>name</code>` with no dead link.

Why this exists — prose used to hard-code the display name inside a
`<code>…</code>` span. Three problems: (a) renaming a standard meant
hunting every occurrence by hand; (b) the same standard renders under
different names per jurisdiction (fod / -fuß), but the prose is shared;
(c) the raw snake_case key leaked to the reader (§0z role-3 violation).
Authoring by id fixes all three: rename once, resolve per page.

Design + decisions: docs/fuss_cross_refs_design.md. Mirrors the
`refs_pool` (§5b) post-render architecture; the card anchors
(`id="fuss-<id>"`) are emitted by templates/location.html.j2.
"""

from __future__ import annotations

import re


# `[fuss:KEY]` — KEY is a fuss id from fuesse.yml. Ids use digits,
# letters and underscores (`rosenobel_fod`, `9_25_thaler`,
# `11_333_thaler`, `royal_holstein`); `-` included for future-proofing.
FUSS_REF_RE = re.compile(r"\[fuss:([0-9A-Za-z_-]+)\]")

# Card anchors rendered by templates/location.html.j2:760 —
# `<section … id="fuss-<id>">`. Used to decide whether an in-page link
# target exists for a given KEY on THIS page.
ANCHOR_ID_RE = re.compile(r'id="fuss-([0-9A-Za-z_-]+)"')


def present_anchors(html: str) -> set[str]:
    """Set of fuss ids whose card anchor is rendered on this page."""
    return set(ANCHOR_ID_RE.findall(html))


def process_html(html: str, lang: str, name_map: dict[str, str]) -> str:
    """Resolve `[fuss:KEY]` markers in already-rendered HTML.

    Args:
      html:     rendered page HTML (post-Jinja).
      lang:     current language — informational; `name_map` values are
                already resolved for this language by the caller.
      name_map: {fuss_key: effective_display_name} for THIS page+lang,
                with per-location overrides already applied. Keys absent
                from the map resolve to a visible placeholder (never
                silently dropped — §0).

    Returns the HTML with every `[fuss:KEY]` replaced by:
      - `<a class="fuss-xref" href="#fuss-KEY">name</a>` when the
        `#fuss-KEY` anchor is present on this page (an ordinary text link
        — NOT code-styled; the fuss name is a proper noun, not an
        identifier), or
      - the bare `name` when it is not (no dead in-page link; cross-page
        linking is a deferred enhancement — see design doc), or
      - a red `[UNKNOWN FUSS: KEY]` placeholder when KEY is not in name_map.
    """
    anchors = present_anchors(html)

    def replace(m: "re.Match[str]") -> str:
        key = m.group(1)
        name = name_map.get(key)
        if name is None:
            # §0 — surface the gap, never silently vanish. The raw key is
            # an identifier here, so it keeps its <code> monospace.
            return (
                f'<b style="color:#c00">[UNKNOWN FUSS: '
                f'<code>{key}</code>]</b>'
            )
        if key in anchors:
            return f'<a class="fuss-xref" href="#fuss-{key}">{name}</a>'
        return name

    return FUSS_REF_RE.sub(replace, html)
