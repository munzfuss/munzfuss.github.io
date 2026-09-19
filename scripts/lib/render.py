"""
Layer C → HTML: render categorized tree to HTML via Jinja2.
"""
from __future__ import annotations

import re
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
    env.filters["nb_dashes"] = nb_dashes
    env.filters["fin_unit"] = fin_unit
    env.filters["strip_phase_marker"] = strip_phase_marker

    return env


# Nearest-simple-fraction table: fractional value → glyph. "CARRY" means the
# fraction rounds up to a whole unit (carry into the integer part).
_FIN_FRACTIONS = [
    (0.0, ""),
    (1 / 8, "⅛"),
    (1 / 4, "¼"),
    (1 / 3, "⅓"),
    (3 / 8, "⅜"),
    (1 / 2, "½"),
    (5 / 8, "⅝"),
    (2 / 3, "⅔"),
    (3 / 4, "¾"),
    (7 / 8, "⅞"),
    (1.0, "CARRY"),
]

# gold → Cölln Mark ÷ 24 Karat; silver/billon → ÷ 16 Lot. Unit nouns are
# period numismatic terms (don't translate for DE/EN per the i18n policy);
# UK uses the established Cyrillic forms, DA the Danish ones (`lod`, not the
# German `Lot`), lowercase as Danish writes unit nouns.
_FIN_UNITS = {
    "gold": (24, {"de": "Karat", "en": "Karat", "uk": "карат", "da": "karat"}),
    "silver": (16, {"de": "Lot", "en": "Lot", "uk": "лот", "da": "lod"}),
    "billon": (16, {"de": "Lot", "en": "Lot", "uk": "лот", "da": "lod"}),
}


def fin_unit(value, metal: str | None, lang: str):
    """Re-express a stored fineness fraction (e.g. 0.986) in its period unit
    as an inline `<span class="fin-unit">` carrying `(23⅔&nbsp;Karat)` for gold,
    `(14&nbsp;Lot)` for silver/billon. The template wraps this span together
    with the fineness `(?)` marker in a block `.fin-eq` line, so the whole
    equivalent (unit + marker) drops onto its own left-aligned line under the
    `.xxx` value. Returns "" when not applicable
    (no value, or a metal without a fineness-unit convention).

    Pure computation — a unit re-expression of the same number the `.xxx`
    column already shows (like Feingewicht), so it needs no separate source.
    """
    import math
    from markupsafe import Markup

    if value is None or metal not in _FIN_UNITS:
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return ""

    factor, labels = _FIN_UNITS[metal]
    unit = labels.get(lang, labels["en"])

    raw = v * factor
    whole = math.floor(raw)
    frac = raw - whole
    # nearest simple fraction
    _, glyph = min(_FIN_FRACTIONS, key=lambda pair: abs(frac - pair[0]))
    if glyph == "CARRY":
        whole += 1
        glyph = ""

    # "0⅝" reads oddly for very low finenesses — show the bare fraction "⅝".
    if whole == 0 and glyph:
        num = glyph
    else:
        num = f"{whole}{glyph}"
    return Markup(f'<span class="fin-unit">({num}&nbsp;{unit})</span>')


def nominal_nbsp(s: str | None) -> str:
    """Glue the nominal's leading number to its first word with NBSP so
    the «1 Rigsbankdaler» line never wraps between the count and the
    denomination. Subsequent spaces stay normal — the rest of the
    denomination phrase wraps naturally on narrow viewports.

    Dual-denomination nominals (two face values on one coin, separated
    by ` = ` in the YAML — e.g. «8 Rigsbankskilling = 2½ Schilling
    Courant») render with each denomination on its own line: the « = »
    becomes the line-break point, and each side gets its own NBSP-
    glued leading number. This gives a stable two-row visual layout
    in narrow nominal columns instead of letting the natural wrap
    break wherever it lands.

    Marked safe: returned with raw `&nbsp;` entity, applied via |safe in
    the template. Other characters are NOT escaped because the upstream
    template still owns autoescape control — callers must apply this
    only to trusted nominal strings (which they always are; nominals
    come from the YAML, never user input).
    """
    if not s:
        return ""
    import html
    import re
    escaped = html.escape(s)
    if " = " in escaped:
        left, right = escaped.split(" = ", 1)
        left = re.sub(r"\s+", "&nbsp;", left, count=1)
        right = re.sub(r"\s+", "&nbsp;", right, count=1)
        return f"{left} =<br>{right}"
    return re.sub(r"\s+", "&nbsp;", escaped, count=1)


_NB_DASH_RE = None  # lazy-compiled — see nb_dashes()


def nb_dashes(s: str | None) -> str:
    """Insert U+2060 WORD JOINER on both sides of any «-», «–» or «—»
    that sits between two non-space characters. The browser then refuses
    to break the line at that position, so compound year ranges
    («1644—1696»), compound place names («Шлезвіг-Гольштейн») and
    similar tight punctuation never break across two lines mid-token.

    Plain prose dashes that ARE surrounded by spaces are not touched —
    those are valid soft-break opportunities.

    Use as a Jinja filter on `data-tooltip` attribute values:
        data-tooltip="{{ '...' | nb_dashes }}"
    """
    if not s:
        return s
    global _NB_DASH_RE
    if _NB_DASH_RE is None:
        import re
        _NB_DASH_RE = re.compile(r"(\S)([\-‐‑‒–—―])(\S)")
    return _NB_DASH_RE.sub("\\1⁠\\2⁠\\3", s)


def ruler_for_lang(name: str | None, lang: str) -> str:
    """Render a ruler name appropriate to the target language.

    The YAML stores rulers in canonical German form, where Roman-numeral
    ordinals carry a trailing period (Christian IV. = "Christian der IV.").
    English, Ukrainian and Danish don't use this convention — strip the
    period from Roman numerals for non-DE rendering. (Danish numismatic
    literature writes «Christian IV», and danskmoent.dk does the same.)
    """
    if not name:
        return "—"
    import re
    # NBSP-glue the space before a Roman-numeral ordinal (Christian III,
    # Friedrich III. von Gottorp) so the numeral never wraps onto its own line
    # away from the name in the narrow Ruler column.   is a literal NBSP
    # char — the ruler cell renders WITHOUT |safe, so an &nbsp; entity would be
    # escaped, but the char is not. Roman numerals: I, V, X combos (1..30 —
    # sufficient for monarchs); trailing period optional, token-boundary anchored.
    name = re.sub(r"\s+([IVX]+\.?)(?=\s|$)", " \\1", name)
    if lang == "de":
        return name
    # en/uk/da: Roman-numeral ordinals don't carry the German trailing period.
    return re.sub(r"( [IVX]+)\.", r"\1", name)


# Every language's word for a phase, so the marker can be stripped off a
# title no matter which language that title came from. Kept here rather than
# read from ui.yml at call time because the filter runs once per phase per
# page and the set is four words long.
_PHASE_WORDS = ("Phase", "Fase", "Фаза")
_PHASE_MARKER_RE = re.compile(
    r"^(?:%s)\s+(\S+)\s+·\s+" % "|".join(_PHASE_WORDS)
)


def strip_phase_marker(title: str | None, phase_id: str) -> str:
    """Drop a leading «Phase I · » from a phase title.

    The template emits the marker itself, so a title that repeats it would
    show it twice. The catch is that the title and the marker need not be in
    the same LANGUAGE: a page renders the marker in its own language but
    falls back to another for an untranslated title, which is how the Danish
    page came to read «Fase I · 1514 → 1532 · Phase I · …». So the match is on
    any language's word for a phase, and on the phase id, which must agree —
    a descriptive title that merely opens with a word and a dot is left alone.
    """
    if not title:
        return title or ""
    m = _PHASE_MARKER_RE.match(title)
    if m and m.group(1) == str(phase_id):
        return title[m.end():]
    return title


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


def generate_css(theme: dict, languages: list[str] | None = None) -> str:
    """Build the three-theme stylesheet (Atlas / Codex / Noir).

    Returns `prefix + styles.base.css` — the prefix is generated from
    `theme.yml` (Noir palette tokens, per-`html[lang]` body line-height,
    timeline-bar palette); the body lives as a static .css file alongside
    `styles.py`. Atlas and Codex palettes are hardcoded inside the static
    base — those themes don't read from theme.yml.

    One stylesheet serves every language of one site; the per-language
    line-height is selected via `html[lang="…"] { --body-line-height: … }`
    rules in the prefix, emitted only for the languages `languages` names.
    """
    return styles.build_css(theme, languages)
