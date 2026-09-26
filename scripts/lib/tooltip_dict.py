"""Deduplicate repeated `data-tooltip` values in a rendered page.

A location page repeats the same tooltip text thousands of times (the
issuing-entity badge text on every coin row, the «computed from weight ×
fineness» source lines, the bare source labels). This post-render pass
moves every value that occurs more than once into a single JSON table
(`window.__TT`) and replaces the attribute with `data-tt="<index>"`.
`assets/app.js` restores `data-tooltip` on the element (and its
`[data-tt]` ancestors) on first mouseover / focus, so the CSS
`attr(data-tooltip)` rule and the portal tooltip keep working unchanged.

Timeline elements (any class containing `tl-`) are left alone: app.js
reads sibling timeline tooltips eagerly (`unifyZoneWidths`), before
they would have been hovered.
"""
from __future__ import annotations

import html as _html
import json
import re
from collections import Counter

_TAG_RE = re.compile(r'<[a-zA-Z][^<>]*?\sdata-tooltip="([^"]*)"[^<>]*>')
_MIN_LEN = 6


def _eligible(tag: str) -> bool:
    return "tl-" not in tag


def process_html(html: str) -> str:
    counts: Counter[str] = Counter(
        m.group(1) for m in _TAG_RE.finditer(html) if _eligible(m.group(0)))
    keep = [v for v, n in counts.items() if n > 1 and len(v) >= _MIN_LEN]
    if not keep:
        return html
    keep.sort(key=lambda v: -counts[v] * len(v))
    index = {v: i for i, v in enumerate(keep)}

    def _sub(m: re.Match) -> str:
        tag, val = m.group(0), m.group(1)
        i = index.get(val)
        if i is None or not _eligible(tag):
            return tag
        return tag.replace(f'data-tooltip="{val}"', f'data-tt="{i}"', 1)

    html = _TAG_RE.sub(_sub, html)
    table = json.dumps([_html.unescape(v) for v in keep],
                       ensure_ascii=False, separators=(",", ":"))
    table = table.replace("</", "<\\/")
    script = f"<script>window.__TT={table};</script>\n"
    pos = html.rfind("</body>")
    return html[:pos] + script + html[pos:] if pos >= 0 else html + script
