"""
Layer C → HTML: render categorized tree to HTML via Jinja2.
"""
from __future__ import annotations

import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import i18n
from . import styles


# City names follow the power that ruled the city at the time (CLAUDE.md i18n
# policy). The mint registry stores one canonical name per mint town, which for
# Oslo is «Christiania» (the town's name 1624-1924). Until the refoundation as
# Christiania in 1624 the Danish crown's name for the town was «Oslo» (danskmoent
# / Wilcke / Galster: «mints in Bergen, Oslo», «1 skilling 1531, Oslo»), so the
# render shows that name for a coin first struck before 1624. Display only: the
# data keeps the canonical value, on which merging and entity routing depend.
_MINT_RENAMES_BEFORE = (
    ("Christiania", 1624, "Oslo"),
)


def mint_label(mint, year_first=None) -> str:
    """Mint name(s) of one coin for display — a list is joined with «, »."""
    names = mint if isinstance(mint, list) else [mint]
    out = []
    for n in names:
        if isinstance(n, str) and isinstance(year_first, int):
            for canon, until, old in _MINT_RENAMES_BEFORE:
                if n == canon and year_first < until:
                    n = old
                    break
        out.append(n)
    return ", ".join(str(n) for n in out if n)


def build_env(template_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register filters
    env.filters["t"] = i18n.t
    from .sites import sister_site_url
    env.globals["sister_site_url"] = sister_site_url
    env.globals["rebuild_scope"] = _rebuild_scope()
    env.filters["fmt_num"] = i18n.fmt_num
    env.filters["fmt_pct"] = i18n.fmt_pct
    env.filters["fmt_delta"] = i18n.fmt_delta
    env.filters["group_bars"] = group_timeline_bars
    env.filters["first_sentence"] = first_sentence
    env.filters["ruler"] = ruler_for_lang
    env.filters["nominal_nbsp"] = nominal_nbsp
    env.filters["mint_label"] = mint_label
    env.filters["nb_dashes"] = nb_dashes
    env.filters["fin_unit"] = fin_unit
    env.filters["fin_txt"] = fin_txt
    env.filters["fuss_spec"] = fuss_spec
    env.filters["phase_spec"] = phase_spec
    env.filters["strip_phase_marker"] = strip_phase_marker
    env.filters["gw_grouped"] = gw_grouped
    env.filters["phase_parent"] = phase_parent
    env.filters["phase_sub_span"] = phase_sub_span

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
    "silver_billon": (16, {"de": "Lot", "en": "Lot", "uk": "лот", "da": "lod"}),
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


def fin_txt(value, decimals: int = 3) -> str:
    """A fineness fraction as the table prints it: «.986», «.2378», and a
    sub-per-cent assay with its leading zeros, «.0054» (0.54 % Ag). Rounding
    the scaled value to an integer dropped those zeros, so 0.0054 read «.54»."""
    d = max(int(decimals), 1)
    v = float(value)
    if v >= 1:
        return f"{v:.{d}f}"
    return f"{v:.{d}f}"[1:]


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


# A Danish king written exactly as `canonical_ruler_display` writes him,
# «Christian IV» — the DE page adds the period. Compound and annotated forms
# («Christian I/Hans», «Christian V / Frederick III») keep their stored form.
_DE_KING_ORDINAL_RE = re.compile(r"^((?:Christian|Frederik|Erik)[ \u00a0][IVX]+)$")


_REBUILD_SCOPE: frozenset[str] | None = None


def _rebuild_scope() -> frozenset[str]:
    """The Fuß of data/v2/_rebuild_scope.yml — the finals rebuilt from their
    members, which carry the period-less king's name."""
    global _REBUILD_SCOPE
    if _REBUILD_SCOPE is None:
        import yaml
        p = Path(__file__).resolve().parents[2] / "data" / "v2" / "_rebuild_scope.yml"
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
        _REBUILD_SCOPE = frozenset((doc or {}).get("fuss") or [])
    return _REBUILD_SCOPE


def ruler_for_lang(name: str | None, lang: str, fuss: str | None = None) -> str:
    """Render a ruler name appropriate to the target language.

    A Roman-numeral ordinal carries a trailing period in German only
    («Christian IV.» = «Christian der IV.»); English, Ukrainian and Danish
    write «Christian IV». The data stores the period-less form for the
    Danish kings (curator 2026-10-24, `lib.ruler_reigns.canonical_ruler_display`;
    finals not yet rebuilt still carry the older «Christian IV.»), so the
    period is the renderer's: added on DE for a Danish king written without
    it, stripped everywhere else. Other rulers keep their stored form on DE.
    The DE period is added only to a coin of a Fuß in data/v2/_rebuild_scope.yml
    (curator 2026-10-24: the change applies to the listed Fuß only); outside
    it a DE row shows what the final stores, as before.
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
        if fuss in _rebuild_scope():
            return _DE_KING_ORDINAL_RE.sub(r"\1.", name)
        return name
    # en/uk/da: Roman-numeral ordinals don't carry the German trailing period.
    return re.sub(r"( [IVX]+)\.", r"\1", name)


# Every language's word for a period (formerly «phase» — renamed 2026-10-11;
# the old words stay matched for untranslated or not-yet-renamed titles), so the marker can be stripped off a
# title no matter which language that title came from. Kept here rather than
# read from ui.yml at call time because the filter runs once per phase per
# page and the set is four words long.
_PHASE_WORDS = ("Periode", "Period", "Період", "Phase", "Fase", "Фаза")
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


# A reading with no label of its own is labelled by the merger with its
# pipeline source id (`_source_label_from_id`). Those ids are internal; the
# tooltip names the source as the reader knows it (curator 2026-10-26). «kmk»
# is the Copenhagen KMM, not the Berlin Münzkabinett our prose calls «KMK».
_SOURCE_DISPLAY = {
    "kmk": "KMM",
    "ikmk": "IKMK Berlin",
    "numista": "Numista",
    "numismaster": "NumisMaster",
    "ngc": "NGC",
    "hede": "Hede",
    "bruun": "Bruun",
    "galster": "Galster",
}


def resolve_tips(items, ui: dict, lang: str) -> str:
    """Join a tooltip's lines, resolving any that are a localisation KEY.

    A tooltip line is normally a source label — free text, passed through
    untouched. But a DERIVED measurement's label is written by
    `lib/compute.py::_derived_label`, which runs once per location for every
    language the site publishes and therefore cannot spell a sentence. It
    emits `marker.<key>\x1f<arg>…` instead, and this resolves it against
    data/i18n/ui.yml, substituting `{w}` (weight source) and `{f}` (fineness
    source).

    An unknown key is left as the raw label rather than rendered as `[key]`:
    a tooltip is an aid, and showing a bracketed key in its place would be
    worse than showing the untranslated text.
    """
    from .compute import DERIVED_SEP

    out: list[str] = []
    for item in items or []:
        if not isinstance(item, str) or DERIVED_SEP not in item:
            out.append(_SOURCE_DISPLAY.get(item, item) if isinstance(item, str) else item)
            continue
        key, *args = item.split(DERIVED_SEP)
        args = [_SOURCE_DISPLAY.get(a, a) for a in args]
        text = i18n.ui_get(ui, key, lang)
        if text.startswith("["):          # ui_get's not-found form
            out.append(DERIVED_SEP.join(args))
            continue
        names = dict(zip(("w", "f"), args))
        # `.format` would choke on a source label containing a brace.
        for slot, value in names.items():
            text = text.replace("{" + slot + "}", value)
        out.append(text)
    # Localisation keys embedded in a source label (lib/weight_range.ui_key),
    # also when nested inside a derived label above.
    from .weight_range import UI_KEY_MARK
    if any(UI_KEY_MARK in o for o in out):
        pat = re.compile(re.escape(UI_KEY_MARK) + r"([\w.]+)" + re.escape(UI_KEY_MARK))
        out = [pat.sub(lambda m: i18n.ui_get(ui, m.group(1), lang), o) for o in out]
    return "\n".join(out)


def generate_css(theme: dict, languages: list[str] | None = None) -> str:
    """Build the two-theme stylesheet (v3 dark / v1 light).

    Returns `prefix + styles.base.css` — the prefix is generated from
    `theme.yml` (Noir palette tokens, per-`html[lang]` body line-height,
    timeline-bar palette); the body lives as a static .css file alongside
    `styles.py`. The v1 light palette is hardcoded inside the static
    base — those themes don't read from theme.yml.

    One stylesheet serves every language of one site; the per-language
    line-height is selected via `html[lang="…"] { --body-line-height: … }`
    rules in the prefix, emitted only for the languages `languages` names.
    """
    return styles.build_css(theme, languages)


# `.pspec` — the parameter line under a fuss title. Unit nouns follow the
# `_FIN_UNITS` convention above: period terms kept in DE/EN, Cyrillic forms in
# UK, Danish forms in DA. The coin name is never translated (§2 tier 2).
_SPEC_UNIT = {
    "cologne_mark": {"de": "Cöllnische Marck", "en": "Cologne mark", "uk": "кельнська марка", "da": "Cöllnische Marck"},
    "troy_mark": {"de": "Troy-Marck", "en": "troy mark", "uk": "тройська марка", "da": "troisk mark"},
    "troy_pound": {"de": "Troy-Pfund", "en": "troy pound", "uk": "тройський фунт", "da": "troypund"},
    "kilogram": {"de": "Kilogramm", "en": "kilogram", "uk": "кілограм", "da": "kilogram"},
}
# (rauh, fein) and whether the word precedes the unit
_SPEC_BASIS = {
    "de": ({"rauh": "rauh", "fein": "fein"}, False),
    "en": ({"rauh": "rough", "fein": "fine"}, True),
    "uk": ({"rauh": "повна", "fein": "чиста"}, True),
    "da": ({"rauh": "rå", "fein": "fin"}, False),
}
_SPEC_UK_BASIS_M = {"rauh": "повний", "fein": "чистий"}   # masculine nouns (фунт, кілограм)
_SPEC_WORDS = {
    "Karat": {"uk": "карат", "da": "karat"},
    "Lod": {"uk": "лот", "da": "lod"},
    "Loth": {"uk": "лот", "da": "lod"},
    "Grän": {"uk": "гран", "da": "gren"},
}


def _spec_words(text: str, lang: str) -> str:
    # Ukrainian takes the genitive singular after a fractional number:
    # «17¾ карата», «23½ карата», but «18 карат».
    if lang == "uk":
        text = re.sub(r"(?<=[½⅓⅔¼¾⅛⅜⅝⅞]) Karat\b", " карата", text)
    for w, tr in _SPEC_WORDS.items():
        if lang in tr:
            text = re.sub(rf"\b{w}\b", tr[lang], text)
    return text


# Sub-phases: a phase id «I.a» is sub-phase «a» of phase «I». Detected from
# the id alone, so every fuss gets the grouping without extra data.
_SUB_ID_RE = re.compile(r"^(0|[IVX]+)\.([a-z])$")
# A label / key that names a sub-phase: «Фаза I.a (1514-1533) · …».
_SUB_LABEL_RE = re.compile(r"^(?P<pre>\S+ )(?P<par>0|[IVX]+)\.(?P<sub>[a-z])\b(?P<rest>.*)$", re.S)
_YEARS_RE = re.compile(r"\((\d{4})(?:\s*[-–]\s*(\d{4}))?\)")


def phase_parent(phase_id) -> str:
    """«I.a» → «I»; any other id is its own parent."""
    m = _SUB_ID_RE.match(str(phase_id))
    return m.group(1) if m else str(phase_id)


def phase_sub_span(phase_id: str):
    """For a sub-phase id «I.a» → «I.<span class="ph-subl">a</span>», so an
    uppercase header does not turn the letter into «I.A»."""
    from markupsafe import Markup, escape
    m = _SUB_ID_RE.match(str(phase_id))
    if not m:
        return escape(phase_id)
    return escape(m.group(1)) + Markup('.<span class="ph-subl">') + escape(m.group(2)) + Markup("</span>")


def gw_grouped(rows, lang: str) -> list[dict]:
    """Grundwerte rows with sub-phase rows («Phase I.a …») gathered under a
    group header «Phase I (first-last)». Returns items
    {kind: 'row'|'group'|'sub', key: Markup, row}."""
    from markupsafe import Markup, escape
    items: list[dict] = []
    for row in rows or []:
        key = i18n.t(row.key, lang) or ""
        m = _SUB_LABEL_RE.match(key or "")
        if not m:
            items.append({"kind": "row", "key": escape(key), "row": row})
            continue
        par = m.group("par")
        last_group = next((i for i in reversed(items) if i["kind"] == "group"), None)
        if not (items and items[-1]["kind"] == "sub" and last_group and last_group["par"] == par):
            prev = items[-1] if items else None
            # A plain «Phase I (…) · …» row right before «Phase I.a» is the group
            # header itself, carrying the values the sub-phases share.
            if prev and prev["kind"] == "row" and re.match(
                    rf"^\S+ {re.escape(par)}(?![.\w])", str(prev["key"])):
                last_group = {"kind": "group", "par": par, "row": prev["row"], "key": prev["key"]}
                items[-1] = last_group
            else:
                last_group = {"kind": "group", "par": par, "pre": m.group("pre"), "years": []}
                items.append(last_group)
        y = _YEARS_RE.search(m.group("rest"))
        if y and "years" in last_group:
            last_group["years"] += [int(y.group(1)), int(y.group(2) or y.group(1))]
        items.append({"kind": "sub", "row": row,
                      "key": escape(par) + Markup('.<span class="ph-subl">') + escape(m.group("sub"))
                             + Markup("</span>") + escape(m.group("rest"))})
    for g in items:
        if g["kind"] == "group" and "years" in g:
            yrs = g.pop("years")
            span = f" ({min(yrs)}-{max(yrs)})" if yrs else ""
            g["key"] = escape(f"{g['pre']}{g['par']}{span}")
    return items


def fuss_spec(spec, lang: str):
    """Render a FussSpec — or a list of them, one line per successive
    standard — as «count coin / unit basis / fineness» HTML."""
    from markupsafe import Markup, escape
    if not spec:
        return ""
    if isinstance(spec, (list, tuple)):
        out = Markup("")
        parent = None
        for s in spec:
            g = s if isinstance(s, dict) else s.model_dump()
            label = (g.get("label") or {})
            text = label.get(lang) or label.get("en") or ""
            m = _SUB_LABEL_RE.match(text)
            if m and m.group("rest") == "":
                if parent != m.group("par"):
                    parent = m.group("par")
                    out += (Markup('<span class="pspec-line pspec-group"><span class="pspec-label">')
                            + escape(m.group("pre") + parent) + Markup("</span></span>"))
                g = dict(g, label={lang: m.group("sub")})
                out += Markup('<span class="pspec-line pspec-sub">') + _fuss_spec_line(g, lang) + Markup("</span>")
            else:
                parent = None
                out += Markup('<span class="pspec-line">') + _fuss_spec_line(s, lang) + Markup("</span>")
        return out
    return _fuss_spec_line(spec, lang)


def phase_spec(spec, phase_id, lang: str):
    """The formula of the spec entry that lists `phase_id` in its `phases`,
    without the phase label, as a line to put under that phase's header."""
    from markupsafe import Markup
    if not spec or not isinstance(spec, (list, tuple)):
        return ""
    for s in spec:
        g = s if isinstance(s, dict) else s.model_dump()
        if str(phase_id) in [str(x) for x in (g.get("phases") or [])]:
            return _fuss_spec_line(dict(g, label=None), lang)
    return ""


def _fuss_spec_line(spec, lang: str):
    from markupsafe import Markup, escape
    g = spec if isinstance(spec, dict) else spec.model_dump()
    count = g["count"]
    if lang == "en":
        count = re.sub(r"(?<=\d),(?=\d)", ".", count)
    unit = _SPEC_UNIT[g.get("unit") or "cologne_mark"][lang]
    words, before = _SPEC_BASIS[lang]
    basis = words[g["basis"]]
    if lang == "uk" and g.get("unit") in ("troy_pound", "kilogram"):
        basis = _SPEC_UK_BASIS_M[g["basis"]]
    mark = f"{basis} {unit}" if before else f"{unit} {basis}"
    sep = " · " if g.get("fineness_join") == "per_denomination" else " → "
    fin = sep.join(g["fineness"])
    if g.get("fineness_unit"):
        fin = f"{fin} {g['fineness_unit']}"
    fin = _spec_words(fin, lang)
    slash = Markup('<span class="pspec-sep"> / </span>')
    note = g.get("fineness_note") or {}
    note = note.get(lang) or note.get("en") or ""
    if note:
        q = Markup('&nbsp;<span class="pspec-q" data-tooltip="') + escape(note) + Markup('">(?)</span>')
    else:
        q = Markup('&nbsp;<span class="pspec-q">(?)</span>')
    out = Markup("")
    label = g.get("label")
    if label:
        text = label.get(lang) or label.get("en") or ""
        out += Markup('<span class="pspec-label">') + escape(text) + Markup("</span> ")
    out += escape(f"{count} {g['coin']}") + slash + escape(mark) + slash + escape(fin)
    if g.get("fineness_unverified") or g.get("unverified"):
        out += q
    return Markup(out)


_UNC_SOURCE = {
    **_SOURCE_DISPLAY,
    "galster": "Galster (danskmoent.dk)",
    "lindahl": "Lindahl 1955",
    "metallanalyser": "Lindblad, Metallanalyser",
    "ucoin": "ucoin",
}


def uncertainty_mark(raw: dict, field: str, ui: dict, lang: str) -> dict | None:
    """How the page marks an unverified value from Coin.uncertainty
    (docs/plans/uncertainty_markers.md, curator 2026-10-29).

    Returns None when the coin records nothing for `field` (the caller keeps
    the generic «(?)»). Otherwise `{"kind": "hedged" | "inferred", "tip": …}`:
    hedged when any source prints the value uncertainly — the value is the
    source's, so «(?)»; inferred when every entry is the pipeline's own basis
    — «[ … ]». The tooltip lists every entry: each source with its own text,
    then each basis with its value; for a year in conflict, the sources that
    print it plainly as well."""
    def _get(obj, key):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    def _plain(obj):
        return obj.model_dump(exclude_none=True) if hasattr(obj, "model_dump") else obj

    entries = [_plain(e) for e in (_get(raw, "uncertainty") or {}).get(field) or []]
    if not entries:
        return None

    def src(e):
        return _UNC_SOURCE.get(e.get("source"), e.get("source") or "")

    def how(e):
        t = i18n.ui_get(ui, f"uncertainty.how.{e.get('how')}", lang)
        return "" if t.startswith("[") else t

    if field in ("metal", "mint"):
        # Only an entry about the value the cell shows decides its mark: a
        # member that inferred «billon» from the name says nothing about the
        # «silver» another source gave the class.
        shown = _get(raw, field)
        shown = ", ".join(map(str, shown)) if isinstance(shown, list) else str(shown or "")
        entries = [e for e in entries if e.get("value") in (None, shown)
                   or (field == "mint" and e.get("value") and set(
                       str(e["value"]).split(", ")) & set(shown.split(", ")))]
        if not entries:
            return None
    if field == "metal":
        # The value is a metal key («billon»); show it as the column does.
        for e in entries:
            t = i18n.ui_get(ui, f"metal.{e.get('value')}", lang)
            if e.get("value") and not t.startswith("["):
                e["value"] = t
    if field == "year":
        # An inference explains the cell only when the cell shows it: a reign
        # placeholder set aside for a source's own year («Numista 1505-1510»
        # over Galster's «u. år» → 1483-1513) is not the shown value's basis
        # (curator 2026-10-29). A source's own reservation is always listed.
        shown_year = str(_get(raw, "year_label") or "")
        entries = [e for e in entries if e.get("kind") != "inferred"
                   or str(e.get("value") or "") == shown_year]
        # A year shown beside the label as a marked alternative («1501-1510
        # (*)») carries its own tooltip; its entry does not explain the label
        # (curator 2026-10-30).
        alt_years = {str(_get(a, "value") or "") for a in (_get(raw, "year_alts") or [])}
        entries = [e for e in entries
                   if not (e.get("value") and str(e["value"]) in alt_years
                           and str(e["value"]) != shown_year)]
        if not entries:
            return None
    hedged = [e for e in entries if e.get("kind") == "hedged"]
    inferred = [e for e in entries if e.get("kind") == "inferred"]
    lines: list[str] = []
    seen: set[str] = set()

    def push(line: str):
        if line and line not in seen:
            seen.add(line)
            lines.append(line)

    def tr(e):
        # A translation of a quoted work, in the page language; a Danish page
        # reads the Danish quote as it stands.
        t = e.get("translation") or {}
        if not t or lang == "da":
            return ""
        txt = t.get(lang) or t.get("en") or t.get("de")
        return f" («{txt}»)" if txt else ""

    # Tooltip markup read by assets/app.js: [b]…[/b] bold (the work or
    # source), [i]…[/i] italic (its quote). One entry: the source on its own
    # line, the quote and its translation on the next (curator 2026-10-29).
    quoted: set[str] = set()

    def entry(e, prefix: str = ""):
        q = e.get("as_printed")
        if q and any(q in x or x in q for x in quoted):
            return                      # the same passage reached twice
        if q:
            quoted.add(q)
            lines.append(f"{prefix}[b]{src(e)}[/b]")
            lines.append(f"[i]«{q}»[/i]{tr(e)}")
        else:
            # The same source and value reached from several members (nine
            # Lindblad rows of one Gote) is one line.
            push(f"{prefix}[b]{src(e)}[/b]: {e.get('value') or ''}"
                 + (f" ({how(e)})" if how(e) else ""))

    for e in hedged:
        entry(e)
    if inferred and hedged:
        push(i18n.ui_get(ui, "uncertainty.inferred_also", lang))
    compiled_head = False
    for e in inferred:
        if e.get("how") == "compiled" and e.get("as_printed"):
            # An attribution compiled from works: the basis once, then each
            # work with its quote.
            if not compiled_head:
                lines.append(f"{how(e)}: {e.get('value') or ''}")
                compiled_head = True
            entry(e)
            continue
        basis = how(e)
        val = e.get("value") or ""
        line = f"{basis}: {val}" if val else basis
        own = e.get("source") not in ("ruler_reigns", "merge_decisions", "standard")
        if e.get("as_printed") and own:
            line += f" — [b]{src(e)}[/b]: [i]«{e['as_printed']}»[/i]{tr(e)}"
        elif own:
            line += f" — [b]{src(e)}[/b]"
        push(line)
    if field == "year":
        yc = _plain(_get(raw, "year_conflict")) or {}
        conf = yc.get("confident") or []
        if conf:
            push(i18n.ui_get(ui, "uncertainty.confident", lang))
            for r in conf:
                push(f"[b]{_UNC_SOURCE.get(r.get('source'), r.get('source'))}[/b]: {r.get('years') or ''}")
    return {"kind": "hedged" if hedged else "inferred", "tip": "\n".join(lines)}


def derived_mark(raw, ui: dict, lang: str) -> dict | None:
    """How a DERIVED value (fine weight, Δ, pieces per mark) is marked when an
    input is unverified (curator 2026-10-29). When every unverified input is
    our inference (the standard's fineness, «[ ]»), the derived value carries
    «[?]» and a tooltip naming those inputs; otherwise None — the generic
    «(?)» of `marker.derived_unverified` stays (a source's own reservation, or
    an input without an entry)."""
    def _get(obj, key):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    inputs = [f for f, flag in (("fineness", "fineness_verified"),
                                ("weight", "weight_rough_verified"))
              if _get(raw, flag) is False]
    if not inputs:
        return None
    tips = []
    for f in inputs:
        m = uncertainty_mark(raw, f, ui, lang)
        if not m or m["kind"] != "inferred":
            return None
        tips.append(m["tip"])
    return {"kind": "derived", "tip": "\n".join(tips)}
