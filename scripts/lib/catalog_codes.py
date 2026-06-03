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
