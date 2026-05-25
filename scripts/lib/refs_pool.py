"""Inline-refs system (introduced 2026-05-25).

Prose anywhere in the project — `fuesse.yml::<fuss>.description`,
`<loc>.yml::fuss_periods.<fuss>.hintergrund`, grundwerte rows,
rechnungsfraktionen, closing labels, etc. — can cite a source by
writing `<sup>[ref:STABLE-KEY]</sup>` instead of the legacy
`<sup><a href="#refN">[N]</a></sup>` form.

At build time (after Jinja template render), this module:

1. Scans the rendered HTML for `<sup>[ref:KEY]</sup>` markers.
2. Resolves each unique KEY against the pool (`data/shared/refs_pool.yml`).
3. Numbers them in appearance order, starting after the highest legacy
   ref value already present in the page's `<ol class="refs">` block.
4. Replaces the markers with `<sup><a href="#ref-pool-KEY">[N]</a></sup>`.
5. Injects `<li id="ref-pool-KEY" value="N">{content}</li>` items into
   the existing biblio list (or creates one before `</body>` when the
   page has no legacy references file).

Why this exists — the OLD system used numeric `<sup>[N]</sup>` cites
that resolved against per-page `*-references.yml` files. Shared
content in `fuesse.yml` had `<sup>[36]</sup>` cites that resolved
against three DIFFERENT entries depending on which page rendered the
Müntzfuß card (denmark-refs::ref36 vs SH-refs::ref36 vs landing's
german_fuesse-refs::ref36) — silent misattribution under §0. The
inline-refs system pins content to stable keys, so cites resolve to
the same source content regardless of which page renders the prose.

See CLAUDE.md §5 «Source hierarchy» for the conventions.
"""

from __future__ import annotations

import re
from pathlib import Path
import yaml


CITE_RE = re.compile(r'<sup>\[ref:([\w\-]+)\]</sup>')
LEGACY_LI_VALUE_RE = re.compile(r'<li[^>]*value="(\d+)"')
OL_REFS_OPEN_RE = re.compile(r'<ol class="refs">')
OL_REFS_CLOSE_RE = re.compile(r'</ol>')


def load_refs_pool(path: Path) -> dict[str, dict[str, str]]:
    """Load the shared refs pool from YAML. Returns {key: {lang: content}}
    or empty dict if file is missing/empty."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _max_legacy_value(html: str) -> int:
    """Find the highest `value="N"` attribute inside `<ol class="refs">`.

    Pool refs number from max+1 to keep continuous numbering with
    legacy refs. Returns 0 if no legacy <ol class="refs"> or no
    value attributes found.
    """
    ol_match = OL_REFS_OPEN_RE.search(html)
    if not ol_match:
        return 0
    # Scope the value search to the <ol class="refs">...</ol> block
    close_match = OL_REFS_CLOSE_RE.search(html, ol_match.end())
    if not close_match:
        return 0
    block = html[ol_match.end():close_match.start()]
    values = LEGACY_LI_VALUE_RE.findall(block)
    if not values:
        return 0
    return max(int(v) for v in values)


def resolve_pool_cites(
    html: str,
    lang: str,
    pool: dict[str, dict[str, str]],
) -> tuple[str, list[tuple[str, str, int]]]:
    """Scan for `<sup>[ref:KEY]</sup>` markers, renumber, replace.

    Returns:
      rewritten_html: HTML with markers replaced by numbered <a> links.
      resolved: list of (key, content_for_lang, display_number) tuples
                in appearance order — used by the caller to render
                the bibliography section.

    Numbering starts at max(legacy_<li value>) + 1, so pool refs sit
    naturally below legacy refs in the biblio without renumber collisions.

    KEYs not found in the pool are left UNRESOLVED with a visible
    placeholder so the curator sees the gap; missing keys are NOT
    silently dropped (per §0 — silent corruption is forbidden).
    """
    start_num = _max_legacy_value(html) + 1
    seen: dict[str, int] = {}
    counter = [start_num]

    def replacer(m: re.Match) -> str:
        key = m.group(1)
        if key not in seen:
            seen[key] = counter[0]
            counter[0] += 1
        n = seen[key]
        return f'<sup><a href="#ref-pool-{key}">[{n}]</a></sup>'

    rewritten = CITE_RE.sub(replacer, html)

    resolved: list[tuple[str, str, int]] = []
    for key, n in sorted(seen.items(), key=lambda kv: kv[1]):
        entry = pool.get(key)
        if not entry:
            content = (
                f'<b style="color:#c00">[MISSING REF POOL ENTRY: <code>{key}</code>]</b> '
                f'— add to <code>data/shared/refs_pool.yml</code>.'
            )
        else:
            content = entry.get(lang) or entry.get("en") or entry.get("de") or ""
        resolved.append((key, content, n))

    return rewritten, resolved


def inject_pool_refs(html: str, resolved: list[tuple[str, str, int]]) -> str:
    """Insert resolved pool refs as `<li>` items into the page's biblio.

    If the page already has `<ol class="refs">` (rendered from legacy
    `<loc>-references.yml`): append pool refs before `</ol>`.

    If the page has NO legacy biblio: create a new biblio section
    before `</body>` with a default heading.
    """
    if not resolved:
        return html

    items_html = "\n".join(
        f'  <li id="ref-pool-{key}" value="{n}">{content}</li>'
        for key, content, n in resolved
    )

    ol_match = OL_REFS_OPEN_RE.search(html)
    if ol_match:
        # Find the matching </ol> closing tag
        close_match = OL_REFS_CLOSE_RE.search(html, ol_match.end())
        if close_match:
            insert_at = close_match.start()
            return html[:insert_at] + "\n" + items_html + "\n" + html[insert_at:]

    # No legacy biblio — create one before </body>
    biblio = (
        '\n<hr class="rsep">\n'
        '<h2 class="refs-title">References</h2>\n'
        f'<ol class="refs">\n{items_html}\n</ol>\n'
    )
    if "</body>" in html:
        return html.replace("</body>", biblio + "</body>", 1)
    # No </body> either — append at end
    return html + biblio


def process_html(html: str, lang: str, pool: dict[str, dict[str, str]]) -> str:
    """End-to-end: resolve + inject. Returns processed HTML."""
    rewritten, resolved = resolve_pool_cites(html, lang, pool)
    return inject_pool_refs(rewritten, resolved)
