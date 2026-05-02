"""
i18n utilities: translation resolution, number formatting.
"""
from __future__ import annotations

from typing import Any


# Fallback chain: target → en → de
FALLBACK = {
    "de": ["de"],
    "en": ["en", "de"],
    "uk": ["uk", "en", "de"],
}


def t(value: Any, lang: str) -> str | None:
    """Resolve an I18nText / I18nTextOptional / plain string to target language."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    # Pydantic model with .resolve
    if hasattr(value, "resolve"):
        return value.resolve(lang, fallback=FALLBACK.get(lang, ["en", "de"])[1:])
    # Plain dict
    if isinstance(value, dict):
        order = FALLBACK.get(lang, ["en", "de"])
        for l in order:
            if l in value and value[l]:
                return value[l]
    return None


# Month names for fmt_date — kept in this module rather than ui.yml because
# they're a closed set tied to the date formatter, not user-facing translation keys.
_MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni",
           "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "uk": ["січня", "лютого", "березня", "квітня", "травня", "червня",
           "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"],
}


def fmt_date(iso: str, lang: str) -> str:
    """Render an ISO YYYY-MM-DD date in language-appropriate long form.

    de: "27. April 2026"   en: "27 April 2026"   uk: "27 квітня 2026"
    """
    try:
        y, m, d = iso.split("-")
        m_idx = int(m) - 1
        d_int = int(d)
    except (ValueError, IndexError):
        return iso
    months = _MONTHS.get(lang, _MONTHS["de"])
    if not (0 <= m_idx < 12):
        return iso
    if lang == "de":
        return f"{d_int}. {months[m_idx]} {y}"
    if lang == "uk":
        return f"{d_int} {months[m_idx]} {y}"
    return f"{d_int} {months[m_idx]} {y}"


def fmt_num(val: float | None, lang: str, decimals: int = 5, unit: str = "g") -> str:
    """Format a number with language-appropriate decimal separator and optional unit."""
    if val is None:
        return "—"
    
    # Strip trailing zeros after decimal but keep at least 2 places
    formatted = f"{val:.{decimals}f}"
    # Remove trailing zeros after non-zero decimal
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
        # But enforce at least 2 decimal places for values < 100
        if "." in formatted:
            int_part, dec_part = formatted.split(".")
            if len(dec_part) < 2:
                dec_part = dec_part.ljust(2, "0")
                formatted = f"{int_part}.{dec_part}"
    
    # Localize decimal separator
    if lang in ("de", "uk"):
        formatted = formatted.replace(".", ",")
    
    if unit:
        if lang == "uk" and unit == "g":
            return f"{formatted} г"
        return f"{formatted} {unit}"
    return formatted


def fmt_pct(val: float | None, lang: str) -> str:
    """Format a percentage."""
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    s = f"{sign}{val:.2f}%"
    if lang in ("de", "uk"):
        s = s.replace(".", ",")
    return s


def fmt_delta(delta_g: float | None, delta_pct: float | None, lang: str) -> str:
    """Render Δ as two stacked lines: grams first, percentage second.

    Returns inline HTML; the template must pipe through |safe. The two
    line wrappers carry .sd-g and .sd-pct classes so per-line typography
    can be tuned in CSS.
    """
    if delta_g is None:
        return '<span class="sd-g">Δ —</span>'
    g_str = fmt_num(delta_g, lang, decimals=5, unit='')
    if not g_str.startswith("-"):
        g_str = "+" + g_str
    pct_str = fmt_pct(delta_pct, lang) if delta_pct is not None else ""
    parts = [f'<span class="sd-g">Δ {g_str}</span>']
    if pct_str:
        parts.append(f'<span class="sd-pct">{pct_str}</span>')
    return "".join(parts)


def load_ui(path: str) -> dict[str, dict[str, str]]:
    """Load ui.yml and return {key: {lang: text}}."""
    import yaml
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    # Flatten — ui.yml is already {key: {de, en, uk}}
    return raw


def ui_get(ui: dict, key: str, lang: str, default: str = "") -> str:
    """Look up a UI string by key + language."""
    entry = ui.get(key, {})
    if isinstance(entry, dict):
        order = FALLBACK.get(lang, ["en", "de"])
        for l in order:
            if l in entry and entry[l]:
                return entry[l]
    return default or f"[{key}]"
