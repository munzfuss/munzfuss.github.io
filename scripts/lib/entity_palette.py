"""Every issuing entity a page shows needs its colours in the stylesheet.

An entity reaches the page as the coin-table badge (`.ent-badge.ent-<id>`), the
timeline filter chip (`.tl-filter-<id>`) and the timeline year marker
(`.tl-coin-year-<id>`), each in the dark theme and in the light theme
(`[data-theme="v1"]`). A new entity without them renders a bare grey badge and
an uncoloured marker — which happened with every entity added so far (curator
2026-11-03: «щоразу коли створюється новий емітент йому бракує кольору»).
`build.py` refuses to validate until all six rules exist for every entity a
location consumes; add them in `scripts/lib/style.base.css` next to the
others, in the same hue for all six.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "scripts" / "lib" / "style.base.css"
LOCATIONS = ROOT / "data" / "v2" / "locations"

RULES = {
    "badge": r"^\.ent-badge\.ent-{e}\s*\{{",
    "badge (light)": r'^\[data-theme="v1"\] \.ent-badge\.ent-{e}\s*\{{',
    "filter": r"^\.tl-filter-{e}\s*\{{",
    "filter (light)": r'^\[data-theme="v1"\] \.tl-filter-{e}\s*\{{',
    "timeline": r"^\.tl-coin-year-{e}\s*\{{",
    "timeline (light)": r'^\[data-theme="v1"\] \.tl-coin-year-{e}\s*\{{',
}


def consumed_entities(locations_dir: Path = LOCATIONS) -> set[str]:
    """Entity ids any V2 location page consumes."""
    out: set[str] = set()
    for p in sorted(locations_dir.glob("*.yml")):
        for e in (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get(
                "consumes_entities") or []:
            ent = e if isinstance(e, str) else (e or {}).get("entity")
            if ent:
                out.add(ent)
    return out


def missing_palette(css: str | None = None,
                    entities: set[str] | None = None) -> dict[str, list[str]]:
    """{entity: [missing rule names]} for every consumed entity lacking one."""
    css = CSS.read_text(encoding="utf-8") if css is None else css
    entities = consumed_entities() if entities is None else entities
    out: dict[str, list[str]] = {}
    for e in sorted(entities):
        miss = [name for name, pat in RULES.items()
                if not re.search(pat.format(e=re.escape(e)), css, re.M)]
        if miss:
            out[e] = miss
    return out
