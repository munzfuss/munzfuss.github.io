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

import re

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
        value = (str(value) if value is not None else "").strip().rstrip(",;")
        if not value:
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
    #     A scalar «A / B» in any list-capable catalogue field is two values
    #     (ucoin / Numista pack sub-variants this way: «125A / 125B», «138.1 /
    #     138.2», «3679 / 3679A»). Left unsplit, the value matches NEITHER half
    #     — an unsplit «125A / 125B» equals neither «125A» nor «125B», silently
    #     blocking a cross-source merge of the same coin AND rendering an ugly
    #     joined string. km keeps its own decimal-comma-aware split below; this
    #     handles every other list-capable field. For `dav`, also strip the
    #     stray volume «#» («EC II# 3679» → «EC II 3679») on every value.
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
                for part in v.split("/"):
                    part = part.strip()
                    if field == "dav":
                        part = _clean_dav_value(part)
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

    # 3. KM hygiene (km is the KMRef-union field, not in list_fields, so
    #    handled explicitly): expand a slash-list scalar («683.1 / 683.2»)
    #    into members, normalise a European decimal-comma sub-variant
    #    («404,1» → «404.1») so it matches the dotted form Numista uses
    #    elsewhere, and de-dup case-insensitively. A bare comma-decimal is
    #    ONE value — only «/» separates a multi-KM list. Dict-form
    #    (register-keyed) km is left untouched.
    km = catalog.get("km")
    if km is not None and not isinstance(km, dict):
        raw: list = []
        if isinstance(km, str):
            for part in km.split("/"):
                part = part.strip()
                if part:
                    raw.append(part)
        elif isinstance(km, list):
            raw = list(km)
        else:
            raw = [km]
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
