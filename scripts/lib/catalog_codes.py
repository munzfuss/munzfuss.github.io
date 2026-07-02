"""Shared catalogue-code → schema-field mapper (generic, open to ANY index).

Single source of truth for «which catalogue code maps to which CatalogRefs
field» across EVERY source parser/builder (numista, ucoin, IKMK, NumisMaster,
Hede, Galster, Bruun). The design is GENERIC, NOT a closed white-list: a known
code lands in its typed field; ANY other real catalogue code is preserved in
the `others` catch-all (full «Code# value» label) — never silently dropped.
Only genuine non-catalogue identifiers (a source's own internal id) are
dropped. This is the §CJ generalisation of the numista fix (§CM-era).

Usage in a source extractor:

    from lib.catalog_codes import map_catalog_token, add_to_catalog
    cat: dict = {}
    for code_raw, number in tokenised_refs:
        add_to_catalog(cat, code_raw, number)   # fills typed field OR others[]

`add_to_catalog` is first-occurrence-wins for typed scalar fields (multi-source
list-form is applied later by the seed merger), and append-dedup for `others`.
"""
from __future__ import annotations

import ast
import re

# ── Multi-value slash split (shared by normalise_catalog + the seed merger) ──
# A «/» inside a catalogue index reads as «and»: it separates two catalogue
# NUMBERS (curator decision 2026-06-25 — «сприймемо це як 'та'»). Two shapes:
#   * BOTH parts complete — ucoin/Numista pack sub-variants «683.1 / 683.2»,
#     «125A / 125B», «3679 / 3679A» → split as-is.
#   * SHARED PREFIX ABBREVIATED on the second — Jensen-Skjoldager «T-91/96»
#     (danskmoent writes the «T-» once) = «T-91» AND «T-96». We RE-ATTACH the
#     leading alpha prefix of the first member so «T-91/96» → [«T-91», «T-96»],
#     never the prefix-less garbage «96».
# A «/» that is NOT separating numbers — a publisher abbreviation «Divo/S»,
# «Kahnt/Schön» (first part is a pure-alpha name) or a «Catalogue# n» label
# carrying «#» — is left whole by the number-list guard. (Those live in `others`,
# which is never routed through this helper, so the guard is belt-and-braces.)
# A DASH range «T-81 - T-88» / «021-061» is a DIFFERENT notation (danskmoent uses
# a dash for ranges) and is NOT a slash — it never enters here and stays whole.
# NB: km is intentionally NOT routed through this helper — KM numbers are bare
# integers where a tight «14/15» is a genuine multi-KM list (per the «one Hede
# type Krause-split across KM 14/15/20» merge_decision), so km keeps its own
# unconditional split below. Regression guard: tests/test_catalog_slash_split.py.
_MULTI_SLASH_RE = re.compile(r"\s*/\s*")
_NUM_PREFIX_RE = re.compile(r"^([A-Za-z]{1,4}-?)\d")


def split_multi_ref(value) -> list[str]:
    """Split a catalogue scalar into its members on «/» (read as «and»).

    Splits ONLY when the «/» separates catalogue NUMBERS: the first member must
    contain a digit and no member may carry a «#» (else it is a publisher
    abbreviation / «Catalogue# n» label and is returned whole). The leading
    alpha prefix of the first member is re-attached to any bare-numeric
    continuation, so «T-91/96» → [«T-91», «T-96»]. Returns the stripped,
    non-empty parts; a value with no qualifying slash returns
    `[str(value).strip()]` (or `[]` when blank)."""
    s = str(value).strip()
    if "/" not in s:
        return [s] if s else []
    parts = [p.strip() for p in _MULTI_SLASH_RE.split(s) if p.strip()]
    if len(parts) < 2:
        return [s] if s else []
    # number-list guard: a name-shaped first part («Divo/S») or a «#»-labelled
    # token («Müseler# 10.4.2 / 31») is one citation, not a number list.
    if not any(ch.isdigit() for ch in parts[0]) or any("#" in p for p in parts):
        return [s]
    m = _NUM_PREFIX_RE.match(parts[0])
    prefix = m.group(1) if m else ""
    out = [parts[0]]
    for p in parts[1:]:
        if prefix and p[:1].isdigit():   # re-attach shared prefix to «96» → «T-96»
            p = prefix + p
        out.append(p)
    return out


# Catalogue code (lower-case, whitespace-stripped) → CatalogRefs field name.
# Covers every typed field the schema models + common code aliases. Extend
# here (one place) when a NEW catalogue earns its own typed field; until then
# any unmapped code flows to `others` automatically (no edit needed to AVOID
# dropping it — that is the whole point).
CATALOG_CODE_MAP: dict[str, str] = {
    "km": "km",
    "hede": "hede",
    "sieg": "sieg",
    "schou": "schou",
    "lange": "lange",
    "l": "lange",                 # NumisMaster «L#»
    "fr": "fr",
    "friedberg": "fr",
    "dav": "dav",
    "davenport": "dav",
    "mb": "mb",
    "madai-bach": "mb",
    "galster": "galster",
    "schive": "schive",
    "skaare": "skaare",
    "nmd": "nmd",
    "fp": "fp",
    "jensen": "jensen_skjoldager",
    "skjoldager": "jensen_skjoldager",
    "jensen-skjoldager": "jensen_skjoldager",
    "bruun": "bruun_collection_id",
}

# Codes that are NOT external catalogues — the ONLY thing dropped. A source's
# own internal record id (already captured by its URL / id), not a numismatic
# catalogue reference.
DROP_CODES: set[str] = {
    "n",     # Numista's own N# type id
    "uc",    # Numista user-coin id
}


def _normalise_dav(code_raw: str, number: str):
    """Davenport volume codes («Dav EC III», «Dav Lg», …) → ('dav',
    '<volume> <number>'), preserving the volume. Else None."""
    parts = code_raw.split()
    if parts and parts[0].lower() == "dav" and len(parts) > 1:
        return "dav", f"{' '.join(parts[1:])} {number}".strip()
    return None


def map_catalog_token(code_raw: str, number: str):
    """Map one (code, number) token to (field, value).

    Returns:
      (typed_field, value)         — a schema-typed catalogue field
      ("others", "Code# value")    — real catalogue our schema doesn't type
      None                         — genuine non-catalogue id (dropped)
    """
    code_raw = (code_raw or "").strip()
    number = (str(number) if number is not None else "").strip()
    if not code_raw or not number:
        return None
    code = code_raw.lower()
    if code in DROP_CODES:
        return None
    mapped = CATALOG_CODE_MAP.get(code)
    if mapped:
        return (mapped, number)
    dav = _normalise_dav(code_raw, number)
    if dav:
        return dav
    return ("others", f"{code_raw}# {number}")


def add_to_catalog(catalog: dict, code_raw: str, number: str) -> None:
    """Apply one token to a catalog dict in place. Typed fields: first-occurrence
    wins (the seed merger applies multi-source list-form later). `others`:
    append-dedup as a list of «Code# value» strings."""
    res = map_catalog_token(code_raw, number)
    if res is None:
        return
    field, value = res
    if field == "others":
        bucket = catalog.setdefault("others", [])
        if value not in bucket:
            bucket.append(value)
    else:
        catalog.setdefault(field, value)


# Generic tokeniser for free-text reference corpora («KM# 75, Hede 39A; Dav EC
# III 1311»). Captures a code (letters + optional volume words) followed by a
# number. Used by sources whose refs are a flat string rather than structured
# tokens. Sources with structured refs (per-catalogue fields) should call
# add_to_catalog directly instead.
_TOKEN_RE = re.compile(
    r"\b([A-Za-zÆØÅæøåöüß][\w.\- ]*?)\s*#?\s*"
    r"(\d[\w./\-]*(?:\s*,\s*\d[\w./\-]*)*)",
)


_SCHEMA_CATALOG_FIELDS: set[str] | None = None


def schema_catalog_fields() -> set[str]:
    """The set of CatalogRefs field names, cached. Lazy import so this module
    has no import-time dependency on the schema (avoids cycles)."""
    global _SCHEMA_CATALOG_FIELDS
    if _SCHEMA_CATALOG_FIELDS is None:
        try:
            from lib.schema import CatalogRefs  # type: ignore
        except Exception:  # pragma: no cover — fallback for odd import paths
            from schema import CatalogRefs  # type: ignore
        _SCHEMA_CATALOG_FIELDS = set(CatalogRefs.model_fields.keys())
    return _SCHEMA_CATALOG_FIELDS


_SCHEMA_LIST_CATALOG_FIELDS: set[str] | None = None


def schema_list_catalog_fields() -> set[str]:
    """The subset of CatalogRefs fields whose schema annotation allows
    list-form (`str | list[str] | None`), cached. A single source that
    attests MULTIPLE distinct values for such a field (e.g. danskmoent's
    Galster 68 → «Schou 3» + «Schou 4» inscription variants) emits a list
    directly, instead of overflowing the extras into `others` as
    «schou# 4». Scalar-only fields (hede_volume, bruun_part, …) are
    excluded so they keep the first-wins behaviour."""
    global _SCHEMA_LIST_CATALOG_FIELDS
    if _SCHEMA_LIST_CATALOG_FIELDS is None:
        try:
            from lib.schema import CatalogRefs  # type: ignore
        except Exception:  # pragma: no cover
            from schema import CatalogRefs  # type: ignore
        out: set[str] = set()
        for fn, fi in CatalogRefs.model_fields.items():
            # `list[str]` appears in the annotation's string form for the
            # `str | list[str] | None` fields; `km`'s richer union and
            # `others` (bare list[str]) are intentionally excluded.
            ann = str(fi.annotation)
            if fn in ("km", "others"):
                continue
            if "list[str]" in ann:
                out.add(fn)
        _SCHEMA_LIST_CATALOG_FIELDS = out
    return _SCHEMA_LIST_CATALOG_FIELDS


def catalog_from_ref_dict(
    refs: dict,
    key_field_map: dict | None = None,
    *,
    drop_keys=frozenset(),
) -> dict:
    """GENERIC source-refs-dict → CatalogRefs-shaped dict.

    The §CJ generalisation: a source parser hands us a raw `{Key: value}`
    refs dict (Bruun «{'Sieg': '80.1', 'Aagaard': '12'}», Galster, Hede …).
    We map each key to a typed CatalogRefs field when one exists, and route
    EVERYTHING ELSE to `others` as «Label# value» — never dropping a real
    catalogue, never failing validation on an unmodelled code.

    - `key_field_map`: source Key → schema field (e.g. Bruun {'Fr': 'friedberg',
      'Dav': 'davenport'}). For a key absent from the map, the lower-cased key
      itself is tried against the schema field set (so a source whose keys are
      already schema-field names needs no map).
    - A key whose resolved field IS a real CatalogRefs field → typed
      (first-occurrence wins; the seed merger applies multi-source list-form
      later).
    - Any other key — unmapped, or mapped to a NON-schema name (Bruun's
      lott/delzanno/sm/hagander/appelgren/mb_swedish/hauberg/malmer), or a code
      our schema simply doesn't type (aagaard, …) — → `others` as
      «<label># <value>», label = mapped name if present else the raw key.
    - `drop_keys`: genuine non-catalogue keys to skip entirely (parser
      false-positives like Hede's «Frederik»).
    - List-valued entries (Hede's `{'Schou': ['136', '170']}`) contribute every
      element; the first goes to the typed scalar field, extras (and any
      non-first list members of an others code) append to `others`.
    """
    schema_fields = schema_catalog_fields()
    list_fields = schema_list_catalog_fields()
    out: dict = {}

    def _emit(field: str | None, label: str, value) -> None:
        value = (str(value) if value is not None else "").strip().rstrip(",;").strip()
        # A dash / placeholder a source prints for «no number in this catalogue»
        # (Bruun lot «Schive: –», Hede «Sieg: -») is NOT a reference — skip it so
        # it never lands in a catalog field as a phantom «–» index. Covers hyphen,
        # en/em-dash, and minus-sign, single or repeated.
        if not value or all(ch in "-–—−" for ch in value):
            return
        if field and field in schema_fields:
            if field not in out:
                out[field] = value
            elif out[field] != value:
                # Second distinct value for an already-set typed field. When the
                # schema allows list-form for this field (str | list[str]), a
                # single source legitimately attesting multiple distinct values
                # (e.g. danskmoent Galster 68 → Schou 3 + Schou 4 inscription
                # variants) accumulates into a list — no `others` overflow, no
                # loss. Scalar-only fields keep first-wins + variant→others.
                if field in list_fields:
                    cur = out[field]
                    cur_list = cur if isinstance(cur, list) else [cur]
                    if value not in cur_list:
                        cur_list.append(value)
                    out[field] = cur_list
                else:
                    # keep the first as typed, preserve the variant in others
                    # so nothing is lost (merger reconciles list-form later).
                    _emit(None, label, value)
        else:
            bucket = out.setdefault("others", [])
            tok = f"{label}# {value}"
            if tok not in bucket:
                bucket.append(tok)

    for k, v in (refs or {}).items():
        if k in drop_keys or v in (None, "", []):
            continue
        mapped = key_field_map.get(k) if key_field_map else None
        if mapped is None:
            mapped = k.lower() if k.lower() in schema_fields else None
        field = mapped if (mapped and mapped in schema_fields) else None
        label = (key_field_map.get(k) if key_field_map else None) or k
        values = v if isinstance(v, list) else [v]
        for elem in values:
            _emit(field, label, elem)
    return out


# ---------------------------------------------------------------------------
# Catalog hygiene — normalise indices before display / comparison
# (CLAUDE.md §9.4, user direction 2026-06-08).
# ---------------------------------------------------------------------------

# An `others` token shaped «<code># <value>». The code is letters (+ volume
# words / hyphen); the value starts with a digit (clean catalogue number).
# Values beginning with a non-digit (e.g. «cf. 16», «unlisted») are NOT
# matched — those stay in `others` per anti-pattern #5 (cf-/unlisted-forms
# never become positive typed catalogue fields).
_OTHERS_TOKEN_RE = re.compile(
    r"^\s*([A-Za-zÆØÅæøåöüß][\w.\- ]*?)\s*#\s*(\d[\w.,/\- ]*?)\s*$"
)
# Sub-variant suffix = trailing run of letters on a catalogue value
# («55C» → «C», «8226A» → «A»). Catalogue convention writes it UPPER-case;
# used to pick the canonical representative among case-variants.
_SUFFIX_RE = re.compile(r"[A-Za-zÆØÅæøåöü]+$")


def _suffix_is_upper(v: str) -> bool:
    m = _SUFFIX_RE.search(v.strip())
    return bool(m) and m.group(0).isupper()


def _clean_dav_value(v: str) -> str:
    """Strip the stray «#» some sources attach to a Davenport volume code
    («EC II# 3679» → «EC II 3679», «EC II#3529» → «EC II 3529»). A catalogue
    number never contains «#», so removing it + collapsing whitespace is safe."""
    if not isinstance(v, str) or "#" not in v:
        return v
    return re.sub(r"\s+", " ", v.replace("#", " ")).strip()


_VARIANT_SUFFIX_RE = re.compile(r"\s+var(?:\.|iant)?\s*$", re.I)


def _strip_variant_qualifier(v: str) -> str:
    """Drop a trailing «var.» / «variant» qualifier from a catalogue index —
    «Lange 16b var.» → «16b», «358 C IV var.» → «358 C IV» (curator decision
    2026-06-25: the «var.» merely flags a variant OF the index; the index itself
    is sufficient). Distinct from cf./unlisted, which DROP the whole value — a
    «cf.» points at a DIFFERENT coin, an «unlisted» is a negative claim, whereas a
    «var.» IS this coin's own index with a redundant qualifier."""
    return _VARIANT_SUFFIX_RE.sub("", str(v)).strip()


# A single token that is JUST «<number><space><sub-letters>» — the space is a
# spurious detachment of the sub-letter and must be closed. Anchored to the whole
# token (post comma/slash-split) so a value with a SECOND space is never touched:
# «358 C IV» (Lange, reign-disambiguated «C IV» = Christian IV) has two spaces →
# no match → kept intact, while «39 C» / «62 AB» / «264 a» collapse.
_SUBLETTER_SPACE_RE = re.compile(r"^(\d+)\s+([A-Za-zÆØÅæøåöü]+)$")


def _strip_subletter_space(v: str) -> str:
    """Close a spurious space between a catalogue number and its terminal
    sub-letter — «39 C» → «39C», «62 AB» → «62AB», «264 a» → «264a». ucoin's
    tab-split DOM occasionally detaches the sub-letter (SOURCES.md §13.2). Only a
    token that is ENTIRELY number+space+letters collapses; anything with further
    structure (a second space like Lange's reign-disambiguated «358 C IV», a range
    «39 A-39 D», a roman «XV.5») is left untouched. Applied per-token inside
    `normalise_numeric_index` (plain-number fields: hede/schou/sieg/lange/galster/
    …); dav/davenport volume codes are NOT numeric-index fields, never seen here."""
    return _SUBLETTER_SPACE_RE.sub(r"\1\2", str(v).strip())


def _dav_volume(v: str) -> str | None:
    """The volume prefix of a Davenport value («EC II 3679» → «EC II»), or
    None for a bare number («3679»). A value is volume-qualified when it has
    >1 whitespace-token and the first token does NOT start with a digit."""
    toks = str(v).split()
    if len(toks) > 1 and not toks[0][:1].isdigit():
        return " ".join(toks[:-1])
    return None


def _promote_bare_dav(dav_list: list) -> list:
    """When a Davenport list carries exactly ONE distinct volume among its
    qualified members, promote every bare number to that volume («[EC II 3679,
    3679A]» → «[EC II 3679, EC II 3679A]»). Davenport numbering is continuous
    within a volume, so a bare number sitting beside a single-volume sibling
    belongs to that same volume. Ambiguous lists (0 or ≥2 volumes) are left
    untouched — the volume of a lone bare number is unknowable."""
    vols = {_dav_volume(v) for v in dav_list}
    vols.discard(None)
    if len(vols) != 1:
        return dav_list
    vol = next(iter(vols))
    return [
        f"{vol} {v}".strip() if _dav_volume(v) is None else v
        for v in dav_list
    ]


def _dedup_values_ci(values: list) -> list:
    """Case-insensitive, order-preserving de-dup of catalogue ref values.

    Among case-variants («55C» / «55c») keep ONE: prefer the variant whose
    alphabetic suffix is UPPER-case (catalogue convention), else first-seen.
    Numeric-only values are unaffected (no case to fold)."""
    chosen: dict[str, str] = {}
    order: list[str] = []
    for v in values:
        s = str(v).strip()
        if not s:
            continue
        k = s.lower()
        if k not in chosen:
            chosen[k] = s
            order.append(k)
        elif _suffix_is_upper(s) and not _suffix_is_upper(chosen[k]):
            chosen[k] = s
    return [chosen[k] for k in order]


def _is_str_repr_list(el) -> bool:
    """True if `el` is a string that is the Python-repr of a list — the
    «form-#2» km corruption, e.g. «['651', '651.1']» (a list-value `str()`'d
    whole by a buggy merge path). Real catalogue tokens («651», «404.1») never
    start with «[» and never literal-eval to a list, so they're untouched."""
    if not isinstance(el, str) or not el.strip().startswith("["):
        return False
    try:
        return isinstance(ast.literal_eval(el), list)
    except (ValueError, SyntaxError):
        return False


def _flatten_str_repr_list(vals: list) -> list:
    """Explode every form-#2 str-repr element of `vals` into its members,
    preserving order. Idempotent; a list with no str-repr element returns a
    shallow copy. Exploded members may be bare strings or KMRef dicts
    ({'value':X,'register':Y}) — both are passed through verbatim for the
    caller to dedup/bucket. (Shared with the one-shot repairer
    scripts/maintenance/fix_corrupted_km_repr.py.)"""
    out: list = []
    for el in vals:
        if _is_str_repr_list(el):
            out.extend(ast.literal_eval(el))
        else:
            out.append(el)
    return out


# Any value that begins with the Aagaard label, in any of the three forms
# producers emit: «Aagaard# 14.1 …», «Aagaard-14.1 …», «Aagaard 14.1».
_AAGAARD_OTHERS_RE = re.compile(r"^\s*Aagaard\b\s*[#\-]?\s*(.+?)\s*$", re.IGNORECASE)
# Leading catalogue number of an Aagaard value («14.1 (53-1/53.1)» → «14.1»,
# truncated «14.1 (53-1» → «14.1»), used to group variant forms of one ref.
_AAGAARD_NUM_RE = re.compile(r"^([\d]+(?:\.[\d]+)*)")


def _canonicalise_aagaard(catalog: dict) -> int:
    """Aagaard die-study refs live ONLY in `others`, as one «Aagaard# <value>»
    token per distinct catalogue number. Idempotent.

    Aagaard cites a die-combination in parens with an internal slash —
    «14.1 (53-1/53.1)», «117.7 (69-GK4/69-GK10)». A typed catalogue field is
    hostile to that shape: `normalise_catalog` step 1b AND the renderer both
    slash-split scalar list-fields, which severs the die-pair («14.1 (53-1»),
    and multiple producers additionally emit the ref both as a typed field AND
    as an `others` token, rendering it twice. So Aagaard is never a typed field.

    This gathers every Aagaard mention — a stray typed `aagaard` field plus
    every `others` form («Aagaard# X» / «Aagaard-X» / «Aagaard X») — groups by
    catalogue number, keeps the FULLEST form per number (balanced parens beat a
    «/»-truncated remnant; then longest), dedups, and rewrites canonical
    «Aagaard# <value>» tokens into `others`. Returns 1 if it mutated, else 0.
    """
    def _is_aagaard(tok) -> "re.Match | None":
        return _AAGAARD_OTHERS_RE.match(str(tok)) if isinstance(tok, str) else None

    raw_vals: list[str] = []

    def _clean_aagaard_value(v) -> "str | None":
        """Normalise one Aagaard value. Returns the cleaned value, or None to
        DROP it. Two operations:
          • drop a slash-truncated REMNANT — a value with more «)» than «(» is
            the orphan tail of «62.1 (68-1/68-2)» severed by an earlier
            «/»-as-«and» split («68-2)», «49.1)»); never a real catalogue ref.
          • canonicalise the die-separator to a HYPHEN inside the parenthetical
            only. «.» and «-» are interchangeable in Aagaard die refs (proven by
            «62.1/63-1» mixing both within one ref); hyphen is the source-dominant
            form. The LEADING catalogue number keeps its dot: «62.1 (68.1/68.1)»
            → «62.1 (68-1/68-1)»."""
        s = str(v).strip()
        if not s or s.count(")") > s.count("("):
            return None
        return re.sub(
            r"\(([^)]*)\)",
            lambda m: "(" + re.sub(r"(\d)\.(\d)", r"\1-\2", m.group(1)) + ")",
            s)

    typed = catalog.pop("aagaard", None)
    typed_present = typed is not None
    if typed_present:
        for v in (typed if isinstance(typed, list) else [typed]):
            cv = _clean_aagaard_value(v)
            if cv:
                raw_vals.append(cv)

    others = catalog.get("others")
    others = others if isinstance(others, list) else []
    found_in_others = False
    for tok in others:
        m = _is_aagaard(tok)
        if m:
            found_in_others = True
            cv = _clean_aagaard_value(m.group(1))
            if cv:
                raw_vals.append(cv)

    # Nothing Aagaard-shaped anywhere → no-op. If Aagaard tokens DID exist but
    # all were slash-truncated remnants (raw_vals now empty), fall through to
    # the rewrite so those remnant tokens are still stripped from `others`
    # (`canonical` is empty → they just disappear).
    if not (typed_present or found_in_others):
        return 0

    # Group by catalogue number; keep the fullest representation per number.
    best: dict[str, str] = {}
    order: list[str] = []

    def _score(v: str) -> tuple[bool, int]:
        return (v.count("(") == v.count(")"), len(v))  # balanced first, then longest

    for v in raw_vals:
        nm = _AAGAARD_NUM_RE.match(v)
        key = nm.group(1) if nm else v.lower()
        if key not in best:
            best[key] = v
            order.append(key)
        elif _score(v) > _score(best[key]):
            best[key] = v

    canonical = [f"Aagaard# {best[k]}" for k in order]

    # Rebuild `others` preserving positions: the canonical Aagaard tokens take
    # the slot of the FIRST Aagaard entry; non-Aagaard tokens stay in place;
    # later Aagaard duplicates drop. When Aagaard came only from the typed
    # field (no others token), append the canonical tokens at the end.
    new_others: list = []
    inserted = False
    for tok in others:
        if _is_aagaard(tok):
            if not inserted:
                new_others.extend(canonical)
                inserted = True
        else:
            new_others.append(tok)
    if not inserted:
        new_others.extend(canonical)

    if new_others:
        catalog["others"] = new_others
    else:
        catalog.pop("others", None)

    return 1 if (typed_present or found_in_others) else 0


# Catalogue fields whose values are plain catalogue NUMBERS (ranges + sub-letter
# suffixes + dotted sub-variants), where a coin's multi-source list should be
# flattened, deduped, range-subsumed and numerically sorted. Excludes fields
# with special value shapes: km (register-aware), dav/davenport (volume codes),
# aagaard (die-pairs → others), numista (N# ordering is curator-set), and the
# *_volume / *_id / bruun_lot helper fields.
_NUMERIC_INDEX_FIELDS: set[str] = {
    "schou", "sieg", "hede", "lange", "galster", "nmd", "fp", "fr", "mb",
    "behrens", "schive", "skaare", "thomsen", "fiala", "gaedechens",
    "hauberg", "jesse", "kreber", "welter", "bergsoe",
}
_PLAIN_RANGE_RE = re.compile(r"^(\d+)-(\d+)$")
_PLAIN_INT_RE = re.compile(r"^(\d+)$")


def _index_sort_key(tok: str) -> tuple:
    """Sort a catalogue token by leading integer, then dotted sub-variant
    («16.1» < «16.2»), then the raw string (so «16» < «16A» < «16.1»)."""
    m = re.match(r"(\d+)", tok)
    lead = int(m.group(1)) if m else 10**9
    m2 = re.match(r"^(\d+)\.(\d+)", tok)
    dec = int(m2.group(2)) if m2 else -1
    return (lead, dec, tok)


def normalise_numeric_index(value):
    """Flatten a catalogue-number field (scalar or list) into one clean, sorted
    list of atomic tokens. Splits comma/slash-joined multi-value strings
    («6,9,7» → 6,9,7), dedups, drops a plain integer subsumed by a plain range
    (9 and 10 inside «8-13» → dropped), and sorts numerically. Sub-letter
    («16A»), dotted («16.1») and suffixed-range («39a-39d») tokens are preserved
    verbatim (never subsumed). Returns a scalar when one token remains.
    Idempotent."""
    raw = value if isinstance(value, list) else [value]
    toks: list[str] = []
    for v in raw:
        if v is None:
            continue
        for part in re.split(r"[,/]", str(v)):
            part = _strip_subletter_space(part.strip())
            if part:
                toks.append(part)
    seen: set[str] = set()
    uniq = [t for t in toks if not (t in seen or seen.add(t))]
    ranges = [(int(m.group(1)), int(m.group(2)))
              for t in uniq if (m := _PLAIN_RANGE_RE.match(t))]

    def _covered(t: str) -> bool:
        m = _PLAIN_INT_RE.match(t)
        return bool(m) and any(lo <= int(m.group(1)) <= hi for lo, hi in ranges)

    kept = sorted((t for t in uniq if not _covered(t)), key=_index_sort_key)
    return kept[0] if len(kept) == 1 else kept


def normalise_catalog(catalog: dict) -> int:
    """In-place catalog hygiene. Idempotent. Returns count of mutations.

    Two operations, both case-insensitive:
      1. FOLD — an `others` entry «<code># <value>» whose <code> (lower-cased)
         maps to a typed, list-capable CatalogRefs field is moved INTO that
         field (list-form when it gains a 2nd distinct value). Folded entries
         leave `others`; the key is dropped when it empties. Codes the schema
         does NOT type (aagaard, lott, mb_swedish, …) stay in `others`.
      2. DEDUP — every list-form catalogue field is de-duplicated case-
         insensitively («Hede 55C» + «55c» → one «55C»); a singleton list
         collapses back to scalar.

    This is the canonical «normalise indices, then compare/display» pass:
    producer-side lower-case overflow («schou# 14») and case-variant
    duplicates («55C» vs «55c») reconcile to one typed, deduped, case-
    canonical form. Safe to re-apply on every seed/merge/absorb run."""
    if not isinstance(catalog, dict):
        return 0
    changes = 0
    schema_fields = schema_catalog_fields()
    list_fields = schema_list_catalog_fields()

    # 0. AAGAARD — consolidate to a single «Aagaard# <value>» others token per
    #    number BEFORE the typed-field passes run. Aagaard die-combinations
    #    («14.1 (53-1/53.1)») are corrupted by the slash-split + rendered twice
    #    when they leak into the typed `aagaard` field; keeping them solely in
    #    `others` sidesteps both. Runs first so the popped typed field can't be
    #    slash-split below.
    changes += _canonicalise_aagaard(catalog)

    # 1. FOLD others → typed list-field
    others = catalog.get("others")
    if isinstance(others, list) and others:
        keep: list = []
        for tok in others:
            field = value = None
            if isinstance(tok, str):
                m = _OTHERS_TOKEN_RE.match(tok)
                if m:
                    # map_catalog_token (not the bare CATALOG_CODE_MAP) so a
                    # volume-qualified Davenport code «Dav EC II# 3679» folds
                    # to dav «EC II 3679» instead of staying a dead others
                    # token next to a redundant dav field.
                    mapped = map_catalog_token(m.group(1).strip(),
                                               m.group(2).strip())
                    if mapped and mapped[0] != "others":
                        field, value = mapped
            if (field and field in schema_fields and field in list_fields
                    and value):
                cur = catalog.get(field)
                if cur is None:
                    catalog[field] = value
                else:
                    cur_list = list(cur) if isinstance(cur, list) else [cur]
                    if value.lower() not in {str(x).lower() for x in cur_list}:
                        cur_list.append(value)
                    catalog[field] = cur_list
                changes += 1
            else:
                keep.append(tok)
        if keep:
            catalog["others"] = keep
        else:
            catalog.pop("others", None)

    # 1b. SLASH-SPLIT multi-value scalars + clean Davenport «#» artefacts.
    #     A «/» in a list-capable catalogue field reads as «and» — two catalogue
    #     numbers (ucoin/Numista pack sub-variants «125A / 125B», «138.1 / 138.2»,
    #     «3679 / 3679A»; Jensen-Skjoldager «T-91/96» = «T-91» AND «T-96»). Left
    #     unsplit the value matches NEITHER half, silently blocking a cross-source
    #     merge AND rendering an ugly joined string. `split_multi_ref` splits on
    #     «/», re-attaching a shared prefix to a bare continuation («T-91/96» →
    #     [«T-91», «T-96»]), and leaves a non-number «/» whole («Divo/S»). km
    #     keeps its own decimal-comma-aware split below; this handles every other
    #     list-capable field. For `dav`, also strip the stray volume «#»
    #     («EC II# 3679» → «EC II 3679»). Finally drop a trailing «var.» / «variant»
    #     qualifier on every value («Lange 16b var.» → «16b») — the index alone
    #     suffices (curator 2026-06-25); see `_strip_variant_qualifier`.
    for field in list_fields:
        if field == "km":
            continue
        val = catalog.get(field)
        if val is None:
            continue
        raw = val if isinstance(val, list) else [val]
        out: list = []
        for v in raw:
            if isinstance(v, str):
                for part in split_multi_ref(v):
                    if field == "dav":
                        part = _clean_dav_value(part)
                    part = _strip_variant_qualifier(part)
                    if part:
                        out.append(part)
            else:
                out.append(v)
        new_val = out[0] if len(out) == 1 else out
        if new_val != val:
            catalog[field] = new_val
            changes += 1

    # 2. DEDUP list-form values case-insensitively + collapse singletons
    for field in list(catalog.keys()):
        if field == "others" or field not in list_fields:
            continue
        val = catalog.get(field)
        if isinstance(val, list):
            deduped = _dedup_values_ci(val)
            collapsed = deduped[0] if len(deduped) == 1 else deduped
            if collapsed != val:
                catalog[field] = collapsed
                changes += 1

    # 2b. NUMERIC INDEX normalisation — plain catalogue-number fields accumulate
    #     multi-source attestations that overlap («Schou 6,7,9» from one source +
    #     «6,9,7» from another, or individuals «9, 10» beside a range «8-13»).
    #     Flatten comma/slash-joined tokens, dedup, drop plain ints subsumed by a
    #     plain range, and sort numerically so the field renders one clean list.
    for field in _NUMERIC_INDEX_FIELDS:
        val = catalog.get(field)
        if val is None:
            continue
        new_val = normalise_numeric_index(val)
        if new_val != val:
            catalog[field] = new_val
            changes += 1

    # 2c. Drop a *_hede1971 old-edition number that leaked into its base list.
    #     `sieg`/`schou` carry the MODERN reference; the `*_hede1971` companion
    #     holds the (systematically differing) Hede-1971-edition number, which
    #     the renderer surfaces as «(Hede-1971: X)». When a source also fed that
    #     old number into the modern list it renders twice — «147, 141
    #     (Hede-1971: 147)» — so strip it, leaving the modern reference only
    #     («141 (Hede-1971: 147)»). Never empties the list (if the old number is
    #     the sole entry, the companion would have nothing to annotate).
    for base in ("sieg", "schou"):
        old = catalog.get(f"{base}_hede1971")
        val = catalog.get(base)
        if old is None or val is None:
            continue
        old_s = str(old).strip()
        vals = val if isinstance(val, list) else [val]
        filtered = [v for v in vals if str(v).strip() != old_s]
        if filtered and len(filtered) != len(vals):
            catalog[base] = filtered[0] if len(filtered) == 1 else filtered
            changes += 1

    # 3. KM hygiene. KM is the KMRef-union field (not in list_fields), handled
    #    explicitly. Two shapes:
    #    (a) DICT-form (register-keyed V2 cross-volume twin, e.g. {'dk':'722',
    #        'sh':'155'}): fold any embedded KMRef ({'value':X,'register':Y})
    #        that a cross-register merge FUSED into the dict — the absorb
    #        km-accumulation can emit a hybrid {'sh':[...], 'value':X,
    #        'register':Y} (register-keyed form spliced with KMRef form). Move
    #        X under its register key Y.lower() (dedup), drop value/register.
    #        Without this the hybrid survives and
    #        v2_resolver.resolve_km_for_location rejects it (no register key for
    #        Y) → build crash on cross-register coins (km-696 / c5h121 / c7h13a).
    #        Then dedup each register value list.
    #    (b) SCALAR / LIST: expand a slash-list scalar («683.1 / 683.2») into
    #        members, normalise a European decimal-comma sub-variant («404,1» →
    #        «404.1»), de-dup case-insensitively. A bare comma-decimal is ONE
    #        value — only «/» separates a multi-KM list.
    km = catalog.get("km")
    if isinstance(km, dict):
        if "value" in km and "register" in km:
            reg = str(km.pop("register") or "").lower()
            val = km.pop("value")
            if reg and val not in (None, "", []):
                cur = km.get(reg)
                if cur is None:
                    km[reg] = val
                else:
                    cur_list = list(cur) if isinstance(cur, list) else [cur]
                    for x in (val if isinstance(val, list) else [val]):
                        if str(x).lower() not in {str(y).lower() for y in cur_list}:
                            cur_list.append(x)
                    km[reg] = cur_list[0] if len(cur_list) == 1 else cur_list
            changes += 1
        for _rk, _rv in list(km.items()):
            if isinstance(_rv, list):
                # form-#2 heal: explode any str-repr element inside a
                # register's list value ({sh: ["['696.1', '696']", …]}) before
                # the dedup, then dedup case-insensitively.
                _dd = _dedup_values_ci(_flatten_str_repr_list(_rv))
                _nv = _dd[0] if len(_dd) == 1 else _dd
                if _nv != _rv:
                    km[_rk] = _nv
                    changes += 1
            elif _is_str_repr_list(_rv):
                # scalar register value that is itself a list-repr
                _dd = _dedup_values_ci(ast.literal_eval(_rv))
                km[_rk] = _dd[0] if len(_dd) == 1 else _dd
                changes += 1
    elif km is not None:
        # form-#2 heal: a scalar that is itself a list-repr, or a list carrying
        # str-repr elements (the c7h13a-type top-level corruption) → explode
        # before normalising. `km` stays the original for the change check.
        work = ast.literal_eval(km) if _is_str_repr_list(km) else km
        raw: list = []
        if isinstance(work, str):
            for part in work.split("/"):
                part = part.strip()
                if part:
                    raw.append(part)
        elif isinstance(work, list):
            raw = _flatten_str_repr_list(list(work))
        else:
            raw = [work]
        norm: list = []
        seen: set = set()
        for v in raw:
            if isinstance(v, str):
                v2 = re.sub(r"^(\d+),(\d+)$", r"\1.\2", v.strip())
                k = v2.lower()
                if k not in seen:
                    seen.add(k)
                    norm.append(v2)
            else:
                norm.append(v)
        new_km = norm[0] if len(norm) == 1 else norm
        if new_km != km:
            catalog["km"] = new_km
            changes += 1

    # 4. Davenport volume normalisation. Davenport publishes in century-tagged
    #    volumes («EC II» = European Crowns 1600-1700, «EC III» = 1700-1800,
    #    «GT III», «SG», «BrSL», …) but the numbering is CONTINUOUS — «Dav
    #    3668» and «EC II 3668» are the SAME reference (volume-implicit vs
    #    volume-explicit).
    #    4a. PROMOTE — when a list has exactly ONE distinct volume, bare
    #        numbers belong to it: «[EC II 3679, 3679A]» → «[EC II 3679,
    #        EC II 3679A]» («3679A» is volume-unknowable alone, but its sole
    #        sibling settles it). This is what unifies a ucoin coin that cites
    #        bare numbers with a Numista one that cites «EC II N» once they
    #        merge under §9a.
    #    4b. FOLD — when ≥2 volumes coexist (promotion can't run), drop a bare
    #        «N» that duplicates a qualified «<VOL> N» (the bare is the
    #        less-precise twin). A bare with no qualified twin is kept.
    #    4c. DEDUP — promotion can mint exact duplicates («[EC II 3679, 3679]»
    #        → «[EC II 3679, EC II 3679]»); collapse them.
    dav = catalog.get("dav")
    if isinstance(dav, list) and len(dav) > 1:
        promoted = _promote_bare_dav(dav)

        def _is_qualified(v: str) -> bool:
            return _dav_volume(v) is not None

        def _trailing_num(v: str) -> str:
            return v.split()[-1].lower() if v.split() else v.lower()

        qualified_nums = {
            _trailing_num(v) for v in promoted
            if isinstance(v, str) and _is_qualified(v)
        }
        folded = [
            v for v in promoted
            if not (
                isinstance(v, str)
                and not _is_qualified(v)
                and v.strip().lower() in qualified_nums
            )
        ]
        new_dav = _dedup_values_ci(folded)
        new_dav = new_dav[0] if len(new_dav) == 1 else new_dav
        if new_dav != dav:
            catalog["dav"] = new_dav
            changes += 1
    return changes
