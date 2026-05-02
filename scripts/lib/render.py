"""
Layer C → HTML: render categorized tree to HTML via Jinja2.
"""
from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import i18n
from . import styles
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
    env.filters["ruler"] = ruler_for_lang
    env.filters["nominal_nbsp"] = nominal_nbsp

    return env


def nominal_nbsp(s: str | None) -> str:
    """Glue the nominal's leading number to its first word with NBSP so
    the «1 Rigsbankdaler» line never wraps between the count and the
    denomination. Subsequent spaces stay normal — the rest of the
    denomination phrase wraps naturally on narrow viewports.

    Marked safe: returned with raw `&nbsp;` entity, applied via |safe in
    the template. Other characters are NOT escaped because the upstream
    template still owns autoescape control — callers must apply this
    only to trusted nominal strings (which they always are; nominals
    come from the YAML, never user input).
    """
    if not s:
        return ""
    # HTML-escape first (callers will pass through |safe), then replace
    # ONLY the first whitespace run with a single NBSP entity.
    import html
    import re
    escaped = html.escape(s)
    return re.sub(r"\s+", "&nbsp;", escaped, count=1)


def ruler_for_lang(name: str | None, lang: str) -> str:
    """Render a ruler name appropriate to the target language.

    The YAML stores rulers in canonical German form, where Roman-numeral
    ordinals carry a trailing period (Christian IV. = "Christian der IV.").
    English and Ukrainian don't use this convention — strip the period
    from Roman numerals for non-DE rendering.
    """
    if not name:
        return "—"
    if lang == "de":
        return name
    import re
    # Match a space + Roman numeral + literal period; drop the period.
    # Roman numerals: combinations of I, V, X (for 1..30 — sufficient for monarchs).
    return re.sub(r"(\s[IVX]+)\.", r"\1", name)


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
    """Build the redesigned three-theme stylesheet (Atlas / Codex / Noir).

    Implementation lives in `styles.py` to keep this module focused on
    template rendering. Theme.yml provides the dark-theme palette and
    timeline-bar gradients; the light Atlas/Codex palettes are baked in
    so users can switch themes without re-editing config.
    """
    return styles.build_css(theme, lang)
