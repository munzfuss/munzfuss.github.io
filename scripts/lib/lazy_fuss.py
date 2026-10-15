"""Cut each Müntzfuß block's phase tables out of a rendered page.

95 % of a location page is the phase tables inside the collapsed
`<details class="fuss-details">` blocks; the browser parses all of it on
every load although none is visible until a block is opened. The
template brackets the tables of each fuss with
`<!--fd-lazy-begin:ID--> … <!--fd-lazy-end-->`; this pass moves that
HTML into a fragment file (`t/<ID>.html` next to the page) and leaves
`data-src` on the `.fd-lazy` wrapper. `assets/app.js` fetches the
fragment when the block is first opened.

Runs after every other post-render pass, so citation numbers and the
tooltip table (`window.__TT`, which stays on the page) are already
final inside the fragments.
"""
from __future__ import annotations

import re

_RE = re.compile(
    r'<div class="fd-lazy"><!--fd-lazy-begin:([A-Za-z0-9_\-]+)-->(.*?)<!--fd-lazy-end--></div>',
    re.S)


def split(html: str, url_dir: str) -> tuple[str, dict[str, str]]:
    """Return (page_html, {fuss_id: fragment_html}).

    `url_dir` is the page's URL directory (ending in «/»); fragment URLs
    are absolute so the root copy of a root-mounted page resolves them
    to the same files as its language copy.
    """
    frags: dict[str, str] = {}

    def _sub(m: re.Match) -> str:
        fid, body = m.group(1), m.group(2)
        frags[fid] = body
        return f'<div class="fd-lazy" data-src="{url_dir}t/{fid}.html"></div>'

    return _RE.sub(_sub, html), frags


# ── Bibliography («Джерела») ─────────────────────────────────────────────
# The final `<h2 class="refs-title">…</h2><ol class="refs">…</ol>` (legacy
# entries + the pool entries refs_pool.py appended) becomes a closed
# `<details class="refs-box">`; the list itself moves to `t/_refs.html` and
# app.js fetches it on first open, or when a citation `#ref…` is followed.
# The leading «_» keeps the file name clear of every fuss id.
REFS_FRAGMENT = "_refs"

_REFS_RE = re.compile(
    r'<h2 class="refs-title">(.*?)</h2>\s*(<ol class="refs">.*?</ol>)', re.S)


def split_refs(html: str, url_dir: str) -> tuple[str, str | None]:
    """Return (page_html, refs_fragment_html | None)."""
    m = None
    for m in _REFS_RE.finditer(html):
        pass                       # the bibliography is the LAST such block
    if m is None:
        return html, None
    heading, ol = m.group(1), m.group(2)
    n = ol.count("<li ")
    box = (
        '<details class="refs-box">'
        '<summary class="refs-sum"><h2 class="refs-title">'
        f'<span class="refs-sum-icon" aria-hidden="true">+</span>{heading}'
        f' <span class="refs-n">({n})</span></h2></summary>'
        f'<div class="refs-lazy" data-src="{url_dir}t/{REFS_FRAGMENT}.html"></div>'
        '</details>'
    )
    return html[:m.start()] + box + html[m.end():], ol
