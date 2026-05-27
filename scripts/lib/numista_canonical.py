"""Shared helpers for normalising Numista cache shapes (API v3 / chrome v1 /
chrome v2 / HTML pre_1541) into the project's canonical sidecar schema.

Canonical schema (matches `scripts/cache/numista/denmark_pre_1541/n*.json`
fields produced by the original `parse_numista_pre1541.py`):

  numista_id       int
  url              str
  title            str
  issuer           str               — primary jurisdiction string
  kings            list[{id?, name, reign?, wikidata_id?}]
  type_            str               — "Standard circulation coins" etc.
  year_first       int               — numerically resolved
  year_last        int               — numerically resolved
  years_raw        str               — original display ("1591-1593" or "1591, 1593")
  year_list        list[int] | None  — discrete years when comma-form
  value            {raw: str}
  currency         str               — currency.name or currency.full_name
  composition      {raw, metal, fineness}
  weight_g         float | None
  diameter_mm      float | None
  shape            str | None
  technique        str | None
  orientation      str | None
  demonetized      str | None        — "Yes"/"No"
  rarity_index     int | None
  references       dict[str, str]    — canonical-key → ref number/code
  obverse          {description, script, lettering, translation}
  reverse          {description, script, lettering, translation}
  mint             str | list[str] | None
  photo_credit     str | None
  _source_shape    str               — 'api' | 'chrome' | 'html_pre1541'

Two stages share this module:
  Phase 2 sub-parsers (parse_numista_api / parse_numista_chrome)
  produce these sidecars.
  Phase 3 seed builder (build_numista_seed) consumes them.
"""
from __future__ import annotations

import re
from typing import Any


# ──────────────────────────────────────────────────────────────────────
# Reference normalisation
# ──────────────────────────────────────────────────────────────────────
#
# Numista API v3 publishes refs as `{catalogue: {id, code}, number}` with
# stable codes; the chrome scrapes emit free-text «KM# 62» / «Hede# 23»
# strings. Both shapes funnel through `_NUMISTA_REF_CODE_MAP` below to
# our project-canonical YAML keys (per `scripts/lib/schema.py::CatalogRefs`).

# Catalogue-code (lower-case) → our schema field name
_NUMISTA_REF_CODE_MAP: dict[str, str] = {
    # Krause family
    "km": "km",
    # Danish standards
    "hede": "hede",
    "sieg": "sieg",
    "schou": "schou",
    "galster": "galster",
    "fr": "fr",         # Friedberg (gold reference)
    "friedberg": "fr",
    "dav": "dav",       # Davenport
    "davenport": "dav",
    "mb": "mb",         # Mansfeld-Bullner
    # Holstein / regional
    "lange": "lange",
    # Bruun (auction-collection id)
    "bruun": "bruun_collection_id",
    # Norwegian-Krause sub-volume tags Numista emits inline — these
    # carry useful coverage data but our schema doesn't model them;
    # quietly drop. Builder logs as informational only when seen.
}

# Refs Numista catalogues that our schema does not currently model.
# Listed here so the parser skips them silently rather than raising on
# unknown keys.
_UNMODELLED_REFS: set[str] = {
    "brekke",      # Norway-specific (Brekke 1965)
    "thesen",      # Norway-specific (Thesen 1969)
    "rønning",     # Norway-specific (Rønning 1984)
    "skaare",      # Norway-specific (Skaare 1995)
    "weinm",       # Weinmeister (Schauenburg)
    "ahs",         # AKS
    "aks",
    "n",           # Numista's own self-ref («N# 12345»)
    "y",
    "c",
    "uc",          # UC# — Numista user-coin id
    "aagaard",
    "ngm",
    "tornberg",
    "jensen",
    "skjoldager",
    "krohn",
    "stahnsdorf",
}


def parse_references_from_api_list(refs: list[dict[str, Any]] | None) -> dict[str, str]:
    """Convert API v3 `references: [{catalogue: {code}, number}, ...]`
    into the canonical dict. Unknown / unmodelled codes are dropped."""
    out: dict[str, str] = {}
    if not refs:
        return out
    for r in refs:
        if not isinstance(r, dict):
            continue
        cat = r.get("catalogue") or {}
        code = (cat.get("code") or "").strip().lower()
        number = r.get("number")
        if number is None:
            continue
        number_str = str(number).strip()
        if not number_str:
            continue
        mapped = _NUMISTA_REF_CODE_MAP.get(code)
        if not mapped:
            # silently skip unknown / unmodelled
            continue
        # First occurrence wins; multi-volume refs (different KM in
        # different Krause editions) get list-form later in the
        # seed builder where merge logic applies.
        out.setdefault(mapped, number_str)
    return out


def parse_references_from_strings(items: list[str] | None) -> dict[str, str]:
    """Convert chrome-scrape `references_list: ["KM# 62", "Hede# 23"]`
    into the canonical dict. Tolerant of varied whitespace, comma /
    semicolon separators inside a single string.
    """
    out: dict[str, str] = {}
    if not items:
        return out
    for raw in items:
        if not isinstance(raw, str):
            continue
        # A single list element may contain multiple refs separated by
        # commas («KM# 12, Hede# 5») or semicolons.
        for chunk in re.split(r"[,;]+", raw):
            chunk = chunk.strip()
            if not chunk:
                continue
            m = re.match(r"^([A-Za-zÆØÅæøåöü]+(?:[\-\.][A-Za-zÆØÅæøåöü]+)?)\s*#?\s*(.+)$", chunk)
            if not m:
                continue
            code = m.group(1).strip().lower()
            number = m.group(2).strip()
            if not number:
                continue
            mapped = _NUMISTA_REF_CODE_MAP.get(code)
            if not mapped:
                continue
            out.setdefault(mapped, number)
    return out


# ──────────────────────────────────────────────────────────────────────
# Composition parsing
# ──────────────────────────────────────────────────────────────────────

# composition.text shape variants observed in Numista cache:
#   "Silver"
#   "Silver (.875)"
#   "Silver (.500)"
#   "Billon (.500)"
#   "Gold (.917)"
#   "Copper"
#   "Bronze"
#   "Brass"
#   "Nickel-silver"
#   "Iron"
# Plus chrome's `composition_text` carrying the same forms.

# Map Numista metal vocabulary → our Pydantic-allowed metal set
# (silver / gold / billon / copper / lead / bronze per schema.py).
# Numista emits a wider vocabulary («Gilding metal plated», «Brass»,
# «Cupronickel», «Aluminum-bronze», …) — these compound / alloy forms
# get folded onto the nearest schema-allowed metal, or None when no
# reasonable mapping exists (caller then falls back to denomination
# heuristic via `infer_metal_from_denomination`).
_METAL_TOKEN_TO_CANON: dict[str, str | None] = {
    # Schema-direct
    "silver": "silver",
    "gold": "gold",
    "billon": "billon",
    "copper": "copper",
    "lead": "lead",
    "bronze": "bronze",
    # Compounds Numista emits, folded onto schema-allowed:
    "brass": "bronze",                      # copper-zinc, closest schema match
    "gilding": "bronze",                    # «Gilding metal plated» — copper-zinc alloy
    "gilt": "bronze",
    "cupronickel": "copper",                # copper-nickel, project treats as copper-tier
    "aluminum-bronze": "bronze",
    "aluminium-bronze": "bronze",
    "nickel-silver": "billon",              # German silver alloy — closest schema is billon
    "nickel": "copper",                     # base-metal nickel, treat as copper-tier
    # OOS (foreign tropical / fantasy / contemporary commemoratives)
    "iron": None,
    "aluminum": None,
    "aluminium": None,
    "tin": None,
    "zinc": None,
}


def parse_composition(raw: str | None) -> dict[str, Any]:
    """Parse a Numista composition string («Silver (.875)») into
    `{raw, metal, fineness}`. Returns `{raw: None, metal: None,
    fineness: None}` when input is None / unparseable.

    Fineness handling:
      * «(.875)» / «(.5625)» — leading-dot decimal form: parsed as
        direct decimal, e.g. .5625 → 0.5625 (no rescaling).
      * «(0.875)» — explicit zero-dot decimal: parsed as direct decimal.
      * «(875)» — bare integer: per-mille form, divided by 1000.
      * «(875/1000)» — explicit ratio: parsed as fraction.
    """
    out: dict[str, Any] = {"raw": raw, "metal": None, "fineness": None}
    if not raw or not isinstance(raw, str):
        return out
    s = raw.strip()
    # Extract leading metal token (everything up to '(' or whitespace).
    m_metal = re.match(r"^\s*([A-Za-z\-]+)", s)
    if m_metal:
        token = m_metal.group(1).strip().lower()
        # Look up token in canonical map; if absent, pass through
        # lowercase token so a downstream consumer can decide whether
        # to fold or report. None entries in the map are explicit OOS
        # (iron / aluminum / tin / zinc) — treat as «metal unknown».
        if token in _METAL_TOKEN_TO_CANON:
            out["metal"] = _METAL_TOKEN_TO_CANON[token]
        else:
            out["metal"] = token
    # Fineness: capture the dot character explicitly to distinguish
    # decimal form (.875) from per-mille form (875). Both forms map
    # to the same fraction; the regex preserves the dot when present
    # so the conversion logic is unambiguous.
    m_fin = re.search(r"\(\s*(\.?\d+(?:\.\d+)?)\s*\)", s)
    if m_fin:
        token = m_fin.group(1)
        if token.startswith("."):
            # Direct leading-dot decimal: «.5625» → 0.5625
            v = float("0" + token)
        else:
            v_raw = float(token)
            if "." in token:
                # Explicit decimal form: «0.875» → 0.875 directly
                v = v_raw
            elif v_raw >= 1.0:
                # Per-mille bare integer: «875» → 0.875
                v = v_raw / 1000.0
            else:
                v = v_raw
        out["fineness"] = round(v, 6)
    else:
        # «X/1000» form
        m_frac = re.search(r"\(\s*(\d+)\s*/\s*1000\s*\)", s)
        if m_frac:
            out["fineness"] = int(m_frac.group(1)) / 1000.0
    return out


def infer_metal_from_denomination(value_raw: str | None) -> str | None:
    """Last-resort metal inference from denomination noun. Mirrors the
    pre_1541 builder's `detect_metal()` heuristic so a coin lacking an
    explicit composition still gets a reasonable metal classification."""
    if not value_raw:
        return None
    v = value_raw.lower()
    if any(k in v for k in ("ducat", "dukat", "gulden", "noble", "krone",
                            "pistole", "louisdor", "friedrichsdor", "rosenoble",
                            "portugaloser", "goldgulden")):
        return "gold"
    if any(k in v for k in ("skilling", "hvid", "penning", "sechsling",
                            "dreiling", "søsling", "sosling")):
        return "billon"
    return "silver"


# ──────────────────────────────────────────────────────────────────────
# Year-range serialisation
# ──────────────────────────────────────────────────────────────────────

def render_years_raw(year_first: int | None, year_last: int | None,
                     year_list: list[int] | None) -> str | None:
    """Render canonical `years_raw` from numeric values.

    - When `year_list` is given (discrete years), comma-join.
    - Otherwise dash-join, or single year when first==last.
    - None when year_first is None.
    """
    if year_list:
        return ", ".join(str(y) for y in year_list)
    if year_first is None:
        return None
    if year_last is None or year_last == year_first:
        return str(year_first)
    return f"{year_first}-{year_last}"


# ──────────────────────────────────────────────────────────────────────
# Mint extraction
# ──────────────────────────────────────────────────────────────────────

def extract_mint(api_mints: list[dict[str, Any]] | None,
                 chrome_mint: str | None) -> str | list[str] | None:
    """Pick the best mint signal.

    Preference: explicit chrome `mint` string (often more precise — has
    period spelling, mintmark variants) → API v3 `mints[].name` (when
    chrome unavailable).

    Returns scalar for single mint, list for multi-mint, None for empty.
    """
    if chrome_mint and isinstance(chrome_mint, str) and chrome_mint.strip():
        return chrome_mint.strip()
    if api_mints:
        names = [m.get("name") for m in api_mints if isinstance(m, dict) and m.get("name")]
        names = [n.strip() for n in names if n and n.strip()]
        if len(names) == 1:
            return names[0]
        if names:
            return names
    return None


# ──────────────────────────────────────────────────────────────────────
# Title nominal extraction (when value is missing)
# ──────────────────────────────────────────────────────────────────────

_TITLE_DENOM_RE = re.compile(r"^\s*(.+?)\s+-\s+", re.UNICODE)


def extract_nominal_from_title(title: str | None) -> str | None:
    """Numista title shape: «<denomination> - <ruler/era>». When
    `value.text` is empty fall back to the title's denomination prefix."""
    if not title or not isinstance(title, str):
        return None
    m = _TITLE_DENOM_RE.match(title)
    if not m:
        return None
    nominal = m.group(1).strip()
    # Strip trailing Daler-fraction suffix per CLAUDE.md §1
    nominal = re.sub(
        r"\s+\(([⅓⅔¼½¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+\s*[⁄/]\s*\d+)\)\s*$",
        "",
        nominal,
    ).strip()
    return nominal or None
