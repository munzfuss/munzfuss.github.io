"""
Layer C → HTML: render categorized tree to HTML via Jinja2.
"""
from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import i18n
from .categorize import LocationTree


def build_env(template_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    # Register filters
    env.filters["t"] = i18n.t
    env.filters["fmt_num"] = i18n.fmt_num
    env.filters["fmt_pct"] = i18n.fmt_pct
    env.filters["fmt_delta"] = i18n.fmt_delta
    env.filters["group_bars"] = group_timeline_bars
    env.filters["first_sentence"] = first_sentence

    return env


def first_sentence(html_text: str) -> str:
    """Extract the first sentence from a (possibly HTML) string for the
    title-block teaser. Strips tags, then truncates after the first
    period/question/exclamation followed by whitespace or end of string.
    Used by location.html.j2 to render the short summary in each Müntzfuß
    title from the long `hintergrund` text without requiring a separate
    `tldr` field per phase."""
    import re
    if not html_text:
        return ""
    # Strip all HTML tags
    text = re.sub(r"<[^>]+>", "", str(html_text))
    # Decode common entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Find first sentence terminator (. ? !) followed by whitespace + capital,
    # or end of string. Skip abbreviations like "ca." or "Chr." or "1½."
    # by requiring the next char after the terminator to be uppercase or end.
    # Start search after the first 30 chars to skip leading "1618 (Corona...)" type stuff.
    m = re.search(r"([.!?])\s+(?=[A-ZА-ЯÄÖÜ])", text[30:])
    if m:
        return text[:30 + m.end(1)].strip()
    return text


def group_timeline_bars(bars):
    """
    Fold consecutive overlay-bars into the preceding non-overlay bar.
    Returns list of dicts: {"primary": TimelineBar, "overlays": [TimelineBar...]}
    Used by location.html.j2 to render Schilling-Theilung etc. inside their parent track.
    """
    groups = []
    for bar in bars:
        if bar.overlay and groups:
            groups[-1]["overlays"].append(bar)
        else:
            groups.append({"primary": bar, "overlays": []})
    return groups


def render_location(
    tree: LocationTree,
    ui: dict,
    theme: dict,
    lang: str,
    template_dir: str,
    languages_available: list[str],
) -> str:
    env = build_env(template_dir)
    tmpl = env.get_template("location.html.j2")
    
    return tmpl.render(
        tree=tree,
        ui=ui,
        theme=theme,
        lang=lang,
        languages=languages_available,
        ui_get=lambda k, l=lang: i18n.ui_get(ui, k, l),
        t=lambda v, l=lang: i18n.t(v, l),
        fmt_num=lambda v, **kw: i18n.fmt_num(v, lang, **kw),
        fmt_delta=lambda g, p: i18n.fmt_delta(g, p, lang),
    )


def render_landing(
    locations: list,
    ui: dict,
    theme: dict,
    lang: str,
    languages_available: list[str],
    template_dir: str,
) -> str:
    env = build_env(template_dir)
    tmpl = env.get_template("landing.html.j2")
    
    return tmpl.render(
        locations=locations,
        ui=ui,
        theme=theme,
        lang=lang,
        languages=languages_available,
        ui_get=lambda k, l=lang: i18n.ui_get(ui, k, l),
        t=lambda v, l=lang: i18n.t(v, l),
    )


def generate_css(theme: dict, lang: str = "de") -> str:
    """Generate theme CSS from theme.yml."""
    c = theme["colors"]
    t = theme["typography"]
    l = theme["layout"]
    a = theme["accents"]
    bars = theme.get("timeline_bars", {})

    # Apply language overrides
    line_height = t["line_height"]
    if lang in theme.get("language_overrides", {}):
        line_height = theme["language_overrides"][lang].get("line_height", line_height)

    # Generate per-bar gradients from timeline_bars map
    bar_css = []
    for bar_id, conf in bars.items():
        extras = []
        if conf.get("fg"):
            extras.append(f"color: {conf['fg']};")
        if conf.get("weight"):
            extras.append(f"font-weight: {conf['weight']};")
        extras_str = " " + " ".join(extras) if extras else ""
        bar_css.append(
            f".tl-bar.{bar_id} {{ background: linear-gradient(90deg, {conf['from']}, {conf['to']});{extras_str} }}"
        )
    bar_css_block = "\n".join(bar_css)

    return f"""
:root {{
  --bg-page: {c['bg_page']};
  --bg-card: {c['bg_card']};
  --bg-subcard: {c['bg_subcard']};
  --text-primary: {c['text_primary']};
  --text-secondary: {c['text_secondary']};
  --text-muted: {c['text_muted']};
  --text-dim: {c['text_dim']};
  --border: {c['border']};
  --border-subtle: {c['border_subtle']};
  --border-light: {c['border_light']};
  --accent-purple: {c['accent_purple']};
  --cite-color: {c['cite_color']};

  /* Accent palette (from theme.yml -> accents:) */
  --acc-gold-deep: {a['gold_deep']};
  --acc-gold-light: {a['gold_light']};
  --acc-gold-muted: {a['gold_muted']};
  --acc-gold-border: {a['gold_border']};
  --acc-gold-border-active: {a['gold_border_active']};
  --acc-gold-bullet: {a['gold_bullet']};
  --acc-purple-text: {a['purple_text']};
  --acc-purple-bullet: {a['purple_bullet']};
  --acc-blue-text: {a['blue_text']};
  --acc-blue-bullet: {a['blue_bullet']};
  --acc-phase-head-from: {a['phase_head_from']};
  --acc-phase-head-to: {a['phase_head_to']};
  --acc-pill-fg: {a['pill_fg']};
  --acc-pill-active-bg: {a['pill_active_bg']};
  --acc-phd-fg: {a['phd_fg']};
  --acc-table-header-bg: {a['table_header_bg']};
  --acc-table-row-hover-bg: {a['table_row_hover_bg']};
  --acc-table-scroll-border: {a['table_scroll_border']};
}}

* {{ box-sizing: border-box; }}

body {{
  font-size: {t['size_body']};
  color: var(--text-primary);
  font-family: {t['family_body']};
  background: var(--bg-page);
  padding: 1rem 1.5rem;
  margin: 0;
  line-height: {line_height};
}}

a {{ color: var(--accent-purple); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

.h1 {{
  font-size: {t['size_xsmall']};
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: {t['letter_spacing_cap']};
  color: var(--text-muted);
  margin: 0 0 10px;
}}

.nav {{
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
  border-bottom: {l['border_width']} solid var(--border);
  margin-bottom: 16px;
  font-size: {t['size_small']};
}}

.lang-switch {{
  display: flex;
  gap: 6px;
  margin-left: auto;
}}

.lang-switch a {{
  padding: 2px 8px;
  border: {l['border_width']} solid var(--border);
  border-radius: {l['radius_pill']};
  font-size: {t['size_xsmall']};
  text-transform: uppercase;
}}

.lang-switch a.active {{
  background: var(--accent-purple);
  color: var(--bg-page);
  border-color: var(--accent-purple);
}}

/* Cards */
.card {{
  background: var(--bg-card);
  border: {l['border_width']} solid var(--border);
  border-radius: {l['radius_card']};
  margin-bottom: {l['gap_cards']};
  overflow: hidden;
}}

.ch {{
  padding: 8px 12px;
  display: flex;
  gap: 8px;
  border-bottom: {l['border_width']} solid var(--border);
}}

.ct {{ font-size: 14px; font-weight: 600; flex: 1; color: var(--text-primary); }}
.cs {{ font-size: {t['size_xsmall']}; color: var(--text-secondary); margin-top: 2px; }}

.bx {{
  font-size: {t['size_tiny']};
  padding: 1px 6px;
  border-radius: {l['radius_pill']};
  flex-shrink: 0;
  margin-top: 2px;
}}
.bx.silver {{ background: {c['badge_silver_bg']}; color: {c['badge_silver_fg']}; }}
.bx.gold {{ background: {c['badge_gold_bg']}; color: {c['badge_gold_fg']}; }}
.bx.giro {{ background: {c['badge_giro_bg']}; color: {c['badge_giro_fg']}; }}
.bx.tarif {{ background: {c['badge_tarif_bg']}; color: {c['badge_tarif_fg']}; }}

.cb {{ padding: 8px 12px; }}

/* Fuss block — subtle wash that visually unifies header + grundwerte + phases + closing.
   Existing colored backgrounds (phase-header, gw, mt-subcat) sit on top unchanged. */
.fuss-block {{
  background: rgba(255, 255, 255, 0.018);
  padding: 14px 14px 18px;
  margin: 28px 0 0;
  border-radius: 8px;
  border: .5px solid rgba(255, 255, 255, 0.04);
}}
.fuss-block + .fuss-block {{ margin-top: 36px; }}
.fuss-block > .phase-header:first-child {{ margin-top: 0; }}
.fuss-block > .terr:last-child {{ margin-bottom: 0; }}

/* Müntzfuß header (was: outer .card) — dark gradient band with name, validity, background */
.phase-header {{
  background: linear-gradient(90deg, var(--acc-phase-head-from), var(--acc-phase-head-to) 80%);
  border-left: 4px solid var(--acc-gold-deep);
  padding: 13px 16px;
  margin: 28px 0 14px 0;
  border-radius: 0 8px 8px 0;
}}
.phase-header .pname {{
  display: block;
  font-size: 16.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--acc-gold-light);
  margin-bottom: 7px;
}}
.phase-header .pdate {{
  display: block;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  background: var(--bg-page);
  border: .5px solid var(--acc-gold-border);
  border-radius: 4px;
  padding: 5px 9px;
  margin: 6px 0 8px;
  letter-spacing: .02em;
}}
.phase-header .pdate b {{ color: var(--acc-gold-deep); font-weight: 700; }}
.phase-header .psub {{
  display: block;
  font-size: 13px;
  font-weight: 400;
  color: #b5b0aa;
  margin-top: 6px;
  line-height: 1.6;
  font-style: italic;
}}
.phase-header details {{ margin-top: 6px; }}
.phase-header details > summary,
.phc details > summary {{
  cursor: pointer;
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  color: var(--acc-pill-fg);
  padding: 2px 8px;
  border: .5px solid var(--acc-gold-border);
  border-radius: 12px;
  background: var(--bg-page);
  list-style: none;
  user-select: none;
}}
.phase-header details > summary::-webkit-details-marker,
.phc details > summary::-webkit-details-marker {{ display: none; }}
.phase-header details > summary::before,
.phc details > summary::before {{ content: "ℹ "; font-style: normal; }}
.phase-header details[open] > summary,
.phc details[open] > summary {{
  color: var(--acc-gold-deep);
  background: var(--bg-card);
  border-color: var(--acc-gold-border-active);
}}

/* Phase header (inside a Müntzfuß) */
.ph {{
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--text-muted);
  margin: 16px 0 4px;
  padding-left: 5px;
  border-left: 2px solid var(--acc-gold-border);
}}
.ph em {{
  color: var(--text-muted);
  font-style: italic;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
}}

.phd {{
  font-size: 12.5px;
  color: var(--acc-phd-fg);
  margin: 0 0 4px 7px;
  line-height: 1.5;
}}

/* Phase content container */
.phc {{
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.65;
  padding: 6px 0 4px 15px;
  border-left: .5px solid var(--border-subtle);
  margin: 2px 0 8px 7px;
}}
.phc b {{ color: var(--text-primary); font-weight: 500; }}
.phc em {{ color: var(--text-muted); font-style: italic; font-size: 12.5px; }}

/* Phase.context block — inside the opened phc-toggle */
.phc-context {{
  margin: 4px 0 12px;
  padding: 8px 12px;
  background: var(--bg-card);
  border-left: 2px solid var(--acc-gold-border);
  border-radius: 0 4px 4px 0;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--text-primary);
}}
.phc-context b {{ color: var(--acc-gold-light); }}
.phc-context em {{ color: var(--text-muted); font-style: italic; }}

/* Phase collapse toggle — hides everything except .ph and .phd behind a summary click */
.phc-toggle {{
  margin: 4px 0 12px 7px;
}}
/* Explicit hide/show — some layouts override the UA default for <details> */
.phc-toggle:not([open]) > .phc {{ display: none; }}
.phc-toggle[open] > .phc {{ display: block; }}
.phc-toggle > summary {{
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 12.5px;
  font-weight: 500;
  font-family: {t['family_body']};
  color: var(--acc-pill-fg);
  background: var(--bg-page);
  border: .5px solid var(--acc-gold-border);
  border-radius: {l['radius_pill']};
  list-style: none;
  user-select: none;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}}
.phc-toggle > summary::-webkit-details-marker {{ display: none; }}
.phc-toggle > summary::before {{
  content: "▾";
  font-style: normal;
  font-size: 11px;
  line-height: 1;
}}
.phc-toggle[open] > summary::before {{ content: "▴"; }}
.phc-toggle > summary:hover {{
  background: var(--acc-pill-active-bg);
  color: var(--acc-gold-deep);
  border-color: var(--acc-gold-border-active);
}}
.phc-toggle[open] > summary {{
  color: var(--acc-gold-deep);
  background: var(--acc-pill-active-bg);
  border-color: var(--acc-gold-border-active);
}}
.phc-toggle .phc-toggle-count {{
  color: var(--text-muted);
  font-weight: 400;
  font-size: 11.5px;
}}
.phc-toggle[open] .phc-toggle-count {{ color: var(--acc-gold-muted); }}
/* Show/hide labels flip with the [open] state */
.phc-toggle > summary .phc-toggle-label-hide {{ display: none; }}
.phc-toggle[open] > summary .phc-toggle-label-show {{ display: none; }}
.phc-toggle[open] > summary .phc-toggle-label-hide {{ display: inline; }}
/* When opened — nested phc has no extra margin-top; we already paid for spacing */
.phc-toggle[open] > .phc {{ margin-top: 6px; }}
/* Print: everything open */
@media print {{
  .phc-toggle {{ display: block; }}
  .phc-toggle > summary {{ display: none; }}
  .phc-toggle > .phc {{ display: block !important; }}
}}

/* Fuss-level details toggle — wraps the long historical context AND all
   phase blocks (with their tables already expanded). Replaces the previous
   per-phase .phc-toggle. */
.fuss-details {{
  margin: 10px 0 14px;
}}
.fuss-details:not([open]) > .fuss-details-body {{ display: none; }}
.fuss-details[open] > .fuss-details-body {{ display: block; }}
.fuss-details > summary {{
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 600;
  font-family: {t['family_body']};
  color: var(--acc-pill-fg);
  background: var(--bg-page);
  border: .5px solid var(--acc-gold-border);
  border-radius: {l['radius_pill']};
  list-style: none;
  user-select: none;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}}
.fuss-details > summary::-webkit-details-marker {{ display: none; }}
.fuss-details > summary::before {{
  content: "▾";
  font-style: normal;
  font-size: 12px;
  line-height: 1;
}}
.fuss-details[open] > summary::before {{ content: "▴"; }}
.fuss-details > summary:hover {{
  background: var(--acc-pill-active-bg);
  color: var(--acc-gold-deep);
  border-color: var(--acc-gold-border-active);
}}
.fuss-details[open] > summary {{
  color: var(--acc-gold-deep);
  background: var(--acc-pill-active-bg);
  border-color: var(--acc-gold-border-active);
}}
.fuss-details .fd-count {{
  color: var(--text-muted);
  font-weight: 400;
  font-size: 12px;
}}
.fuss-details[open] .fd-count {{ color: var(--acc-gold-muted); }}
.fuss-details > summary .fd-label-hide {{ display: none; }}
.fuss-details[open] > summary .fd-label-show {{ display: none; }}
.fuss-details[open] > summary .fd-label-hide {{ display: inline; }}
.fuss-details[open] > .fuss-details-body {{ margin-top: 12px; }}

/* Long historical detail block at the top of the fuss-details body */
.fuss-hintergrund {{
  font-size: 13.5px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 18px;
  padding: 10px 14px;
  background: var(--bg-subcard);
  border-left: 2px solid var(--acc-gold-border);
  border-radius: 0 {l['radius_card']} {l['radius_card']} 0;
}}
.fuss-hintergrund p {{ margin: 0 0 10px; }}
.fuss-hintergrund p:last-child {{ margin-bottom: 0; }}
.fuss-hintergrund b {{ color: var(--text-primary); font-weight: 600; }}
.fuss-hintergrund i, .fuss-hintergrund em {{ font-style: italic; color: var(--text-muted); }}

/* Bottom close-button mirror inside .fuss-details */
.fd-foot {{
  margin-top: 16px;
  text-align: right;
}}
.fd-close {{
  background: var(--bg-page);
  border: .5px solid var(--acc-gold-border);
  border-radius: {l['radius_pill']};
  padding: 4px 12px;
  font-size: 12.5px;
  color: var(--acc-pill-fg);
  cursor: pointer;
  font-family: {t['family_body']};
  display: inline-flex;
  align-items: center;
  gap: 6px;
}}
.fd-close:hover {{
  background: var(--acc-pill-active-bg);
  color: var(--acc-gold-deep);
}}

@media print {{
  .fuss-details {{ display: block; }}
  .fuss-details > summary {{ display: none; }}
  .fuss-details > .fuss-details-body {{ display: block !important; }}
}}

/* Closing summary (.terr) */
.terr {{
  background: var(--bg-subcard);
  border-top: .5px solid var(--border-subtle);
  padding: 6px 11px;
  font-size: 12.5px;
  color: var(--text-secondary);
  line-height: 1.65;
  margin: 8px 0 22px;
  border-radius: 0 0 {l['radius_card']} {l['radius_card']};
}}
.terr .tlb {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--text-muted);
  display: block;
  margin-bottom: 3px;
}}
.terr b {{ color: var(--text-primary); font-weight: 500; }}
.terr i {{ font-style: italic; }}

/* Coin table caption */
.mt-caption {{
  font-size: 12px;
  color: var(--acc-gold-muted);
  margin: 10px 0 3px;
  font-weight: 500;
  line-height: 1.5;
}}
.mt-caption b {{ color: var(--text-primary); font-weight: 600; }}
.mt-caption i {{ font-style: italic; color: var(--text-muted); }}

/* Subcat dividers (Kurant / Scheide) */
.mt-subcat {{
  margin: 10px 0 4px;
  padding: 5px 10px;
  border-radius: {l['radius_block']};
  font-size: {t['size_small']};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: {t['letter_spacing_small']};
  color: var(--text-primary);
}}

.mt-subcat.kurant {{
  background: {c['subcat_kurant_bg']};
  border-left: 3px solid {c['subcat_kurant_border']};
  color: {c['subcat_kurant_fg']};
}}

.mt-subcat.scheide {{
  background: {c['subcat_scheide_bg']};
  border-left: 3px solid {c['subcat_scheide_border']};
  color: {c['subcat_scheide_fg']};
}}

.mt-subcat.copper {{
  background: {c['subcat_copper_bg']};
  border-left: 3px solid {c['subcat_copper_border']};
  color: {c['subcat_copper_fg']};
}}

.mt-subcat .sc-desc {{
  display: block;
  font-size: {t['size_tiny']};
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
  margin-top: 2px;
  opacity: 0.85;
}}

/* Table */
.mt-scroll {{
  overflow-x: auto;
  overflow-y: hidden;
  margin: 6px 0 4px;
  border: {l['border_width']} solid var(--acc-table-scroll-border);
  border-radius: 4px;
  background: var(--bg-page);
  -webkit-overflow-scrolling: touch;
}}
.mt-scroll::-webkit-scrollbar        {{ height: 8px; }}
.mt-scroll::-webkit-scrollbar-track  {{ background: var(--bg-page); }}
.mt-scroll::-webkit-scrollbar-thumb  {{ background: var(--acc-gold-border); border-radius: 4px; }}
.mt-scroll::-webkit-scrollbar-thumb:hover {{ background: var(--acc-gold-border-active); }}

.mt {{
  width: 100%;
  /* min-width keeps the note column readable (~400 px) on narrower viewports;
     parent .mt-scroll already provides overflow-x: auto so users can scroll
     horizontally on phones / split windows. */
  min-width: {l['max_width']};
  border-collapse: collapse;
  font-size: {t['size_small']};
  background: var(--bg-page);
  margin: 0;
}}

.mt thead th {{
  background: var(--acc-table-header-bg);
  color: var(--acc-gold-deep);
  padding: 6px 6px;
  border-bottom: {l['border_width']} solid var(--acc-gold-border);
  font-weight: 700;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: {t['letter_spacing_small']};
  font-size: {t['size_tiny']};
  white-space: nowrap;
  vertical-align: bottom;
}}

.mt tbody td {{
  padding: 4px 6px;
  border-bottom: {l['border_width']} solid var(--bg-card);
  vertical-align: top;
}}
.mt tbody tr:last-child td {{ border-bottom: none; }}
.mt tbody tr:hover       {{ background: var(--acc-table-row-hover-bg); }}
.mt tbody tr.rw-sch      {{ background: rgba(194, 139, 75, 0.04); }}
.mt tbody tr.rw-sch:hover{{ background: var(--acc-table-row-hover-bg); }}

.c-nom {{ font-weight: 500; }}
.c-year {{ color: var(--text-secondary); white-space: nowrap; }}
.c-km {{ font-size: {t['size_xsmall']}; color: var(--text-secondary); line-height: 1.4; }}
.c-km .cat-group {{ display: inline-block; }}
.c-km .cat-prefix {{ color: var(--text-muted); font-weight: 500; }}
.c-km .cat-plain {{ color: var(--text-muted); font-style: italic; }}
.c-metal {{ font-size: {t['size_xsmall']}; color: var(--text-secondary); }}
.c-w {{ font-family: {t['family_mono']}; font-size: {t['size_xsmall']}; white-space: nowrap; }}
.c-d {{ font-family: {t['family_mono']}; font-size: {t['size_xsmall']}; color: var(--text-muted); }}
.c-mint {{ font-size: {t['size_xsmall']}; color: var(--text-secondary); }}
.c-note {{
  font-size: {t['size_xsmall']};
  color: var(--text-secondary);
  line-height: 1.45;
  /* The note column must be wide enough for prose, otherwise long Bemerkungen
     wrap into 12-15 lines. min-width forces the browser's auto layout to give
     this column ≥380 px even on a wide table; combined with .mt min-width:1200
     the column is always readable. The table will overflow horizontally inside
     .mt-scroll if the window is too narrow to fit everything. */
  min-width: 380px;
}}
.c-note b, .c-note strong {{ color: var(--text-primary); font-weight: 600; }}
.c-note i, .c-note em {{ font-style: italic; color: var(--text-secondary); }}
.c-note u {{ text-decoration: underline; }}
.c-note a {{ color: var(--accent-purple); }}
.c-note sup a {{ font-size: 0.85em; }}

.c-soll {{
  font-family: {t['family_mono']};
  font-size: {t['size_xsmall']};
  color: var(--text-secondary);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}}

.c-delta {{
  font-family: {t['family_mono']};
  font-size: {t['size_xsmall']};
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}}
/* Δ 4-state spectrum: yellow-brown (under) / green (over),
   with «mild» (within remedium ±1%) and «deep»/«strong» (beyond) variants. */
.c-delta .sd.under-deep  {{ color: {c['under_deep']};  background: {c['under_deep_bg']};  padding: 0 4px; border-radius: 2px; }}
.c-delta .sd.under-mild  {{ color: {c['under_mild']};  background: {c['under_mild_bg']};  padding: 0 4px; border-radius: 2px; }}
.c-delta .sd.over-mild   {{ color: {c['over_mild']};   background: {c['over_mild_bg']};   padding: 0 4px; border-radius: 2px; }}
.c-delta .sd.over-strong {{ color: {c['over_strong']}; background: {c['over_strong_bg']}; padding: 0 4px; border-radius: 2px; }}
/* Legacy class aliases — for any pages still rendered with the old class names */
.c-delta .sd.ok          {{ color: {c['over_mild']};   background: {c['over_mild_bg']};   padding: 0 4px; border-radius: 2px; }}
.c-delta .sd.dev         {{ color: {c['under_deep']};  background: {c['under_deep_bg']};  padding: 0 4px; border-radius: 2px; }}
.c-delta .sd.dev-pos     {{ color: {c['over_strong']}; background: {c['over_strong_bg']}; padding: 0 4px; border-radius: 2px; }}
.c-delta .sd-na          {{ color: var(--text-muted); font-style: italic; cursor: help; }}

.c-fuss {{
  font-size: {t['size_xsmall']};
  color: var(--text-secondary);
  line-height: 1.4;
}}
.c-fuss .fuss-nominal {{ display: block; color: var(--text-primary); }}
.c-fuss .fuss-implied {{ color: var(--dev, #d49968); font-style: italic; }}
.c-fuss .sf-line {{
  display: block;
  font-size: 10.5px;
  font-style: italic;
  line-height: 1.35;
  margin-top: 2px;
}}
.c-fuss .sf-line.plain       {{ color: var(--text-muted); font-style: normal; }}
.c-fuss .sf-line.primary     {{ color: var(--acc-gold-muted); }}
.c-fuss .sf-line.primary::before   {{ content: "▸ Primär: ";   color: var(--acc-gold-bullet); font-weight: 600; font-style: normal; }}
.c-fuss .sf-line.secondary   {{ color: var(--acc-purple-text); }}
.c-fuss .sf-line.secondary::before {{ content: "▸ Sekundär: "; color: var(--acc-purple-bullet); font-weight: 600; font-style: normal; }}
.c-fuss .sf-line.tertiary    {{ color: var(--acc-blue-text); }}
.c-fuss .sf-line.tertiary::before  {{ content: "▸ Tertiär: ";  color: var(--acc-blue-bullet); font-weight: 600; font-style: normal; }}
.c-fuss .sf-line.implied     {{ color: var(--dev, #d49968); font-style: italic; opacity: .85; }}

.c-ref {{ font-size: {t['size_xsmall']}; }}
.c-ref a {{ color: var(--accent-purple); }}

/* Issuing-entity badge — small pill in c-entity column */
.c-entity {{ text-align: center; vertical-align: middle; padding: 4px 6px; }}
.ent-badge {{
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: .04em;
  font-family: {t['family_body']};
  cursor: help;
  border: .5px solid transparent;
}}
.ent-badge.ent-royal_holstein    {{ background: #3a1a1a; color: #e89090; border-color: #6e2d2d; }}
.ent-badge.ent-gottorp_duchy     {{ background: #1a2d1a; color: #a8d490; border-color: #4d6e35; }}
.ent-badge.ent-danish_realm      {{ background: #1a2438; color: #8aaef0; border-color: #355088; }}
.ent-badge.ent-gesamtstaat       {{ background: #281a36; color: #c8a8e8; border-color: #5a3a85; }}
.ent-badge.ent-provisional_govt  {{ background: #38301a; color: #ead890; border-color: #8a7038; }}
.ent-badge.ent-prussian_province {{ background: #1f1f1f; color: #b8b8b8; border-color: #4a4a4a; }}
.ent-badge.ent-schauenburg_pinneberg {{ background: #2a2532; color: #c8b8d8; border-color: #5a4a72; }}
.ent-badge.ent-norburg_plon_duchy {{ background: #1f2a35; color: #98c0e0; border-color: #3d6080; }}
.ent-badge.ent-sonderburg_duchy {{ background: #1a3030; color: #88c8c0; border-color: #3a6868; }}

.mt-caption {{
  font-size: {t['size_xsmall']};
  color: var(--text-secondary);
  margin: 8px 0 4px;
  padding: 4px 10px;
  font-style: italic;
}}

/* Verification marker */
.unverified {{
  color: {c['dev']};
  cursor: help;
  font-weight: 600;
}}

.untranslated {{
  background: rgba(255, 220, 0, 0.08);
  border-bottom: 1px dashed rgba(255, 220, 0, 0.3);
}}

/* Landing cards */
.loc-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}}

a.loc-card {{
  display: block;
  background: var(--bg-card);
  border: {l['border_width']} solid var(--border);
  border-radius: {l['radius_card']};
  padding: 16px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
}}
a.loc-card:hover {{
  background: var(--acc-pill-active-bg);
  border-color: var(--acc-gold-border-active);
  transform: translateY(-1px);
  text-decoration: none;
}}

.loc-card h3 {{ margin: 0 0 8px; font-size: 16px; color: var(--acc-gold-deep); }}
.loc-card p  {{ margin: 0; font-size: 13px; color: var(--text-secondary); }}

footer {{
  margin-top: 32px;
  padding-top: 16px;
  border-top: {l['border_width']} solid var(--border);
  font-size: {t['size_xsmall']};
  color: var(--text-muted);
  text-align: center;
}}

/* Grundwerte card */
.gw {{
  background: var(--bg-card);
  border: {l['border_width']} solid var(--border);
  border-radius: {l['radius_card']};
  margin: 0 0 12px;
  overflow: hidden;
}}
.gw-head {{
  padding: 7px 11px 6px;
  display: flex;
  gap: 6px;
  border-bottom: {l['border_width']} solid var(--border);
}}
.gw-head-text {{ flex: 1; }}
.gw-heading {{
  font-size: 15.5px;
  font-weight: 600;
  color: var(--text-primary);
}}
.gw-subheading {{
  font-size: {t['size_xsmall']};
  color: var(--text-muted);
  margin-top: 2px;
  line-height: 1.5;
}}
.gw-body {{
  padding: 8px 11px 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 14px;
}}
@media(max-width: 720px) {{
  .gw-body {{ grid-template-columns: 1fr; }}
}}
.gw-rows {{
  display: table;
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
}}
.gw-row {{ display: table-row; }}
.gw-k {{
  display: table-cell;
  color: var(--text-muted);
  min-width: 110px;
  padding: 3px 6px 3px 0;
  border-bottom: .5px solid var(--border-subtle);
  font-size: 13px;
  vertical-align: top;
}}
.gw-v {{
  display: table-cell;
  padding: 3px 0;
  border-bottom: .5px solid var(--border-subtle);
  font-size: 13.5px;
  vertical-align: top;
  color: var(--text-primary);
}}
.gw-v b {{ color: var(--text-primary); font-weight: 600; }}
.gw-v em {{ color: var(--text-muted); font-style: normal; font-size: 12.5px; }}

.gw-fr {{
  background: var(--bg-page);
  border: {l['border_width']} solid var(--border);
  border-radius: 6px;
  padding: 5px 9px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-secondary);
  margin-top: 5px;
}}
.gw-fr b {{ color: var(--text-primary); font-weight: 500; }}
.gw-fr em {{ color: var(--text-muted); font-style: normal; font-size: 12.5px; }}
.gw-fr i {{ color: var(--text-muted); font-style: italic; }}
.gw-fr .gw-fr-label {{
  display: block;
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--text-muted);
  margin-bottom: 3px;
}}

/* Timeline */
.tl {{
  background: var(--bg-card);
  border: {l['border_width']} solid var(--border);
  border-radius: {l['radius_card']};
  padding: 14px 14px 16px;
  margin: 0 0 22px;
}}
.tl-title {{
  font-size: {t['size_xsmall']};
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: {t['letter_spacing_cap']};
  color: var(--text-muted);
  margin: 0 0 12px;
}}
.tl-grid {{
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 0 10px;
  align-items: center;
  font-size: 13px;
}}
@media(max-width: 720px) {{
  .tl-grid {{ grid-template-columns: 140px 1fr; font-size: 12px; }}
}}
.tl-label {{
  color: var(--text-primary);
  font-weight: 500;
  text-align: right;
  padding: 9px 4px 9px 2px;
  line-height: 1.3;
}}
.tl-label-sub {{
  padding-left: 18px;
  color: var(--text-secondary);
}}
.tl-label small {{
  display: block;
  color: var(--text-muted);
  font-size: 11.5px;
  font-weight: 400;
  margin-top: 2px;
}}
.tl-grid > div:nth-child(n+3) {{ border-top: .5px dashed var(--border-subtle); }}
.tl-grid > div:nth-child(4n+1),
.tl-grid > div:nth-child(4n+2) {{ background: rgba(255, 255, 255, 0.015); }}

.tl-track {{
  position: relative;
  height: 46px;                           /* whole height now belongs to the bar
                                             since the phase strip was removed
                                             from the timeline (103debf) */
  background: rgba(0, 0, 0, 0.25);
  border-radius: 3px;
  border: .5px solid var(--border-subtle);
  margin: 9px 0;
}}
.tl-track-compact {{ height: 32px; margin: 12px 0; }}

.tl-bar {{
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 2px;
  display: flex;
  align-items: center;
  padding: 0 5px;
  font-size: 11.5px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  box-shadow: inset 0 0 0 .5px rgba(0, 0, 0, 0.3);
}}
.tl-bar-dashed {{
  border: .5px dashed var(--accent-purple);
  opacity: 0.7;
  font-size: 10.5px;
}}
/* Bars whose true range extends past the timeline edges — show a torn edge */
.tl-bar-cut-left  {{ border-top-left-radius: 0; border-bottom-left-radius: 0;
                     border-left: 1.5px dotted rgba(255,255,255,0.45); }}
.tl-bar-cut-right {{ border-top-right-radius: 0; border-bottom-right-radius: 0;
                     border-right: 1.5px dotted rgba(255,255,255,0.45); }}
/* Narrow bars (<8% of the timeline) cannot fit their bar_label inside the
   bar itself. We keep the label vertically centred (same as wide bars) but
   allow horizontal overflow — the text spills past the bar edges with a
   text-shadow halo for legibility over neighbouring bars / track background. */
.tl-bar-narrow {{
  overflow: visible;
  padding: 0;
}}
.tl-bar-narrow .tl-bar-label-float {{
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 10.5px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  pointer-events: none;
  text-shadow:
    -1px -1px 0 var(--bg-page),
     1px -1px 0 var(--bg-page),
    -1px  1px 0 var(--bg-page),
     1px  1px 0 var(--bg-page);  /* outline halo for readability over any bg */
}}
/* Overlay bar — laid INTO the parent track, sits as a thinner stripe over it */
.tl-bar-overlay {{
  top: 21px;                              /* parent bar top is 14, leave 7px inset */
  bottom: 7px;
  border: .5px dashed rgba(255,255,255,0.6);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.4);
  z-index: 2;
}}
/* Phase strip — top 14px of the track, above the bar; never overlaps bar_label */
.tl-phase {{
  position: absolute;
  top: 0;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px dashed rgba(255, 255, 255, 0.35);
  cursor: help;
  pointer-events: auto;
  z-index: 3;
}}
/* Outer edges: left dash on first phase, right dash on last */
.tl-phase.tl-phase-first {{ border-left:  1px dashed rgba(255, 255, 255, 0.35); }}
.tl-phase.tl-phase-last  {{ border-right: 1px dashed rgba(255, 255, 255, 0.35); }}
.tl-phase-label {{
  font-size: 10.5px;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}}
/* Pause-segment marker — diagonal stripes signal a documented production gap
   («no coins here», distinct from «missing data»). The "—" label is supplied
   by the regular .tl-phase-label span; ::before is intentionally not used. */
.tl-phase.tl-phase-pause {{
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(255, 255, 255, 0.08) 0,
    rgba(255, 255, 255, 0.08) 4px,
    rgba(0, 0, 0, 0.18) 4px,
    rgba(0, 0, 0, 0.18) 8px
  );
}}
.tl-phase.tl-phase-pause .tl-phase-label {{
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  letter-spacing: 0;
}}
/* ---------------------------------------------------------------------
   Instant CSS tooltip — applies to ANY element with data-tooltip="..."
   (phase bars, (?)-markers, ent-badges, table headers etc.). Replaces
   the native HTML title= attribute, which has a ~700-1500ms browser
   delay before appearing. Hover here → tooltip is instant.

   :not(.tl-phase) — timeline phase markers are already position:absolute
   (anchored to a year-derived X coordinate); forcing them to relative
   collapses the layout. Their ::after still positions correctly because
   the absolutely-positioned parent itself acts as the containing block.
   --------------------------------------------------------------------- */
[data-tooltip]:not(.tl-phase) {{
  position: relative;
}}
[data-tooltip]:hover::after {{
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  border: .5px solid var(--acc-gold-border-active);
  color: var(--text-primary);
  padding: 5px 9px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: 1.45;
  white-space: normal;
  width: max-content;
  max-width: 320px;
  z-index: 100;
  pointer-events: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
}}
/* Sub-label folded under the parent's label */
.tl-sublabel {{
  margin-top: 4px;
  padding-left: 12px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1.3;
}}
.tl-sublabel small {{
  display: block;
  color: var(--text-muted);
  font-size: 10.5px;
  font-weight: 400;
  margin-top: 1px;
}}
{bar_css_block}

.tl-axis {{
  position: relative;
  height: 20px;
  border-top: .5px solid var(--border-subtle);
  margin-top: 8px;
}}
.tl-axis span {{
  position: absolute;
  top: 4px;
  font-size: 11.5px;
  color: var(--text-muted);
  transform: translateX(-50%);
  white-space: nowrap;
}}
.tl-axis span::before {{
  content: "";
  position: absolute;
  top: -8px;
  left: 50%;
  width: .5px;
  height: 5px;
  background: var(--border-subtle);
}}

/* Phase-close button at the bottom of an open phase — mirrors the top summary pill */
.phc-foot {{
  margin: 10px 0 4px;
  display: flex;
  justify-content: flex-start;
}}
.phc-close {{
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 12.5px;
  font-weight: 500;
  font-family: {t['family_body']};
  color: var(--acc-gold-deep);
  background: var(--acc-pill-active-bg);
  border: .5px solid var(--acc-gold-border-active);
  border-radius: {l['radius_pill']};
  user-select: none;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}}
.phc-close:hover {{
  background: var(--bg-page);
  color: var(--acc-pill-fg);
  border-color: var(--acc-gold-border);
}}
.phc-close-icon {{
  font-style: normal;
  font-size: 11px;
  line-height: 1;
}}
@media print {{
  .phc-foot {{ display: none; }}
}}

/* Methodological notes block */
.methodology {{
  background: var(--bg-card);
  border: {l['border_width']} solid var(--border);
  border-radius: {l['radius_card']};
  padding: 14px 18px;
  font-size: {t['size_small']};
  color: var(--text-secondary);
  line-height: 1.65;
  margin: 0 0 22px;
}}
.methodology b {{ color: var(--text-primary); font-weight: 500; }}
.methodology em, .methodology i {{ color: var(--accent-purple); font-style: italic; }}
.methodology br + br {{ content: ""; display: block; margin-top: 4px; }}

/* References block */
.rsep {{
  border: 0;
  border-top: {l['border_width']} solid var(--border);
  margin: 32px 0 16px;
}}

.refs-title {{
  font-size: {t['size_xsmall']};
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: {t['letter_spacing_cap']};
  color: var(--text-muted);
  margin: 16px 0 12px;
}}

.refs {{
  padding-left: 24px;
  font-size: {t['size_small']};
  line-height: 1.55;
  color: var(--text-secondary);
}}

.refs li {{
  margin-bottom: 8px;
  padding-left: 4px;
}}

.refs li b {{ color: var(--text-primary); font-weight: 600; }}
.refs li i {{ color: var(--cite-color); font-style: italic; }}

.refs a {{
  color: var(--accent-purple);
  word-break: break-word;
}}
.refs a:hover {{ text-decoration: underline; }}
"""
