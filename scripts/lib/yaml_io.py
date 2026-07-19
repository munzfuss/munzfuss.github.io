"""Shared YAML I/O for programmatic data-file edits — family-aware.

WHY THIS MODULE EXISTS (the recurring trap it prevents)
--------------------------------------------------------
The project's data YAMLs are written by TWO different serializers, each with
family-specific settings. Round-tripping a file through the WRONG serializer
or the wrong settings silently reformats the ENTIRE file — a 24k-line spurious
diff from a one-field edit. This has bitten multiple sessions. This module is
the single sanctioned entry point so the correct config is always used; never
instantiate a bare `ruamel.yaml.YAML()` / `yaml.dump(...)` with guessed
settings for an ad-hoc edit again.

The families (auto-detected from the path), empirically verified zero/near-zero
round-trip diff (see scripts/maintenance/test_yaml_io_roundtrip.py). There are
THREE axes that all have to match or the whole file reformats: serializer,
line width, and — for ruamel — the sequence indent/offset (block-list dash
flush with the parent key vs. indented):

  | path prefix                                        | serializer | width | seq/offset       |
  |----------------------------------------------------|------------|-------|------------------|
  | data/v2/final/, seed_unified/, classification_dec. | ruamel rt  | 200   | seq=4, offset=2  |
  | data/v2/seed/                                       | ruamel rt  | 200   | seq=4, offset=2  |
  | data/locations/                                     | ruamel rt  | 4096  | seq=2, offset=0  |
  | data/shared/, data/i18n/                            | ruamel rt  | 4096  | seq=4, offset=2  |

  UNIFICATION (2026-07-19, curator decision B). Previously final/,
  seed_unified/ and classification_decisions/ were written by
  absorb_seeds_into_final_v2.py / merge_seeds_cross_source.py with PyYAML
  (width=120, offset=0). A human editing one of those files with ruamel (the
  natural tool for YAML-with-comments) reflowed the WHOLE file — the
  offset0↔offset2 churn trap (the 2026-07-19 danish_realm incident, +216k/-219k
  from a hand edit). PyYAML and ruamel cannot be made byte-identical even at
  matched offset+width (quote policy + fold-point differ), so all three
  machine-emitted-AND-hand-editable file types were unified onto ruamel
  width=200/offset=2 (the `ruamel_seed` profile) — the yamllint/prettier
  industry-standard indented-sequence style, matching what a ruamel hand-edit
  produces. The emitters now call `dump_v2_canonical()` below.

  match_uncertainty/* stays on PyYAML — it is GITIGNORED (never tracked, never
  in a diff) and machine-only, so unifying it would only cost a multi-MB
  reflow for zero benefit. The v2/seed family is written by lib/seed_merge.py
  + lib/v2_seed_writer.py; the V1-era locations family uses offset=0 dash-flush
  block lists, while data/shared uses offset=2 — these two LOOK alike but
  reformat each other.

  Even the matching config leaves a small residual on some files (internal
  formatting drift accumulated over many sessions): seed ~18 lines, shared
  fuesse.yml ~46, schleswig_holstein.yml ~6. final/seed_unified round-trip to
  exactly 0. The self-test pins these baselines so a wrong-serializer regression
  (thousands of lines) is caught loudly.

PREFER `edit_coin_field()` FOR SINGLE-FIELD SURGICAL EDITS
----------------------------------------------------------
`edit_coin_field()` is LINE-BASED — it locates a coin block by id and rewrites
only the target field's line(s). It does NO serialization round-trip, so it is
immune to the reformat trap entirely, regardless of family. Use it whenever the
change is "set / clear / list-edit one field on N coins by id" (the bulk of
one-off data fixes). Reach for `load()`/`save()` only for genuinely structural
edits (insert/remove/reorder coins, rebuild a mapping).

Per CLAUDE.md «Atomic commits at task boundaries», each script that uses these
helpers is expected to result in one logical commit.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import yaml as _pyyaml
from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[2]
LOCATIONS_DIR = REPO / "data" / "locations"
SHARED_DIR = REPO / "data" / "shared"
I18N_DIR = REPO / "data" / "i18n"

# ---------------------------------------------------------------------------
# Family detection + per-family serializer config
# ---------------------------------------------------------------------------

_PYYAML_WIDTH = 120

# ruamel per-family (width, sequence, offset). The mapping indent is always 2.
_RUAMEL_CFG = {
    "ruamel_seed":   (200, 4, 2),   # data/v2/seed/
    "ruamel_loc":    (4096, 2, 0),  # data/locations/ (dash-flush block lists)
    "ruamel_shared": (4096, 4, 2),  # data/shared/, data/i18n/, default
}


def family_of(path) -> str:
    """Return the serializer-family key for `path`:
    'pyyaml120' | 'ruamel_seed' | 'ruamel_loc' | 'ruamel_shared'."""
    # Match path substrings WITHOUT a leading slash so both relative
    # ("data/v2/final/x.yml") and absolute ("/repo/data/v2/final/x.yml")
    # paths classify correctly. "data/v2/seed/" is not a substring of
    # "data/v2/seed_unified/" (the latter has no slash after "seed"), and
    # the final/seed_unified test runs first anyway.
    p = str(path).replace("\\", "/")
    # final/, seed_unified/ and classification_decisions/ were unified onto the
    # ruamel_seed profile (width=200/offset=2) in 2026-07 — see module docstring.
    if (
        "data/v2/final/" in p
        or "data/v2/seed_unified/" in p
        or "data/v2/classification_decisions/" in p
    ):
        return "ruamel_seed"
    if "data/v2/seed/" in p:
        return "ruamel_seed"
    if "data/locations/" in p:
        return "ruamel_loc"
    return "ruamel_shared"  # shared / i18n / anything else


def _make_ruamel(family: str) -> YAML:
    width, seq, off = _RUAMEL_CFG.get(family, _RUAMEL_CFG["ruamel_shared"])
    y = YAML()
    y.preserve_quotes = True
    y.width = width
    y.indent(mapping=2, sequence=seq, offset=off)
    return y


def dump_v2_canonical(payload) -> str:
    """Serialize a plain dict/list payload to the canonical V2 string
    (ruamel width=200, seq=4/offset=2). This is the single serializer for the
    machine-emitted-AND-hand-editable V2 files — final/, seed_unified/,
    classification_decisions/. The absorb/merger emitters call this instead of
    the old PyYAML width=120 dump, so a subsequent ruamel hand-edit is a no-op
    (no more offset0↔offset2 churn). Callers needing a header-comment banner
    prepend it to the returned string. NOT for match_uncertainty/ (PyYAML,
    gitignored)."""
    import io
    buf = io.StringIO()
    _make_ruamel("ruamel_seed").dump(payload, buf)
    return buf.getvalue()


def make_yaml(path=None) -> YAML:
    """Return a ruamel YAML instance configured for `path`'s family.

    With no path (or a PyYAML family), defaults to the data/shared profile
    (width=4096, offset=2). For PyYAML families callers wanting structural
    round-trips should use `load()`/`save()`, which pick the serializer
    automatically."""
    fam = family_of(path) if path is not None else "ruamel_shared"
    if fam == "pyyaml120":
        fam = "ruamel_shared"
    return _make_ruamel(fam)


# ---------------------------------------------------------------------------
# Structural load/save (family-aware). load() -> (ctx, doc); save(ctx, path, doc)
# `ctx` is opaque — pass it straight back to save(). This keeps the historical
# 2-tuple convention (`y, doc = load(path)`; `save(y, path, doc)`).
# ---------------------------------------------------------------------------

def _split_comment_header(raw: str) -> tuple[str, str]:
    """Split leading `#`-comment / blank lines (the writer's banner that
    PyYAML's safe_load would drop) from the YAML body."""
    lines = raw.split("\n")
    i = 0
    while i < len(lines) and (lines[i].lstrip().startswith("#") or lines[i].strip() == ""):
        i += 1
    header = "\n".join(lines[:i])
    if header:
        header += "\n"
    return header, "\n".join(lines[i:])


def load(path) -> tuple[Any, Any]:
    """Load any project YAML, returning (ctx, doc). Pass ctx + doc back to
    `save()` to round-trip with the file's own serializer + settings."""
    path = Path(path)
    fam = family_of(path)
    raw = path.read_text()
    if fam == "pyyaml120":
        header, body = _split_comment_header(raw)
        doc = _pyyaml.safe_load(body)
        return {"kind": "pyyaml", "header": header}, doc
    y = make_yaml(path)
    return y, y.load(raw)


def save(ctx: Any, path, doc: Any) -> None:
    """Write `doc` back to `path` using the serializer carried in `ctx`
    (the value returned by `load()`)."""
    path = Path(path)
    if isinstance(ctx, dict) and ctx.get("kind") == "pyyaml":
        body = _pyyaml.dump(
            doc, sort_keys=False, allow_unicode=True,
            default_flow_style=False, width=_PYYAML_WIDTH,
        )
        path.write_text(ctx.get("header", "") + body)
        return
    # ruamel instance
    with open(path, "w") as f:
        ctx.dump(doc, f)


def load_location(name: str) -> tuple[Any, Path, Any]:
    """Load `data/locations/<name>.yml`. Returns (ctx, path, doc)."""
    path = LOCATIONS_DIR / f"{name}.yml"
    ctx, doc = load(path)
    return ctx, path, doc


def load_shared(name: str) -> tuple[Any, Path, Any]:
    """Load `data/shared/<name>.yml`. Returns (ctx, path, doc)."""
    path = SHARED_DIR / f"{name}.yml"
    ctx, doc = load(path)
    return ctx, path, doc


def find_coin(doc: Any, coin_id: str) -> Any | None:
    """Return the coin dict with the matching `id`, or None."""
    for c in doc.get("coins") or []:
        if c.get("id") == coin_id:
            return c
    return None


def coin_index(doc: Any, coin_id: str) -> int | None:
    """Return the list-index of the coin with the matching `id`, or None."""
    for i, c in enumerate(doc.get("coins") or []):
        if c.get("id") == coin_id:
            return i
    return None


# ---------------------------------------------------------------------------
# Line-based surgical editor (NO round-trip — immune to the reformat trap)
# ---------------------------------------------------------------------------

_ID_RE = re.compile(r"^\s*(?:-\s+)?id:\s+(\S+)\s*$")


def _coin_block_bounds(lines: list[str], coin_id: str) -> tuple[int, int] | None:
    """Return [start, end) line indices of the coin whose id == coin_id.
    A coin block runs from its `id:` line to the next coin's `id:` line."""
    start = None
    for i, l in enumerate(lines):
        m = _ID_RE.match(l)
        if m and m.group(1) == coin_id:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _ID_RE.match(lines[j]):
            end = j
            break
    return start, end


def _render_field(indent: str, field: str, value) -> list[str]:
    """Render a scalar or list-valued field at the given indent. Strings are
    single-quoted to match the project's catalog-ref convention."""
    def q(v):
        return f"'{v}'" if isinstance(v, str) else str(v)
    if isinstance(value, (list, tuple)):
        out = [f"{indent}{field}:"]
        out += [f"{indent}- {q(v)}" for v in value]
        return out
    return [f"{indent}{field}: {q(value)}"]


def edit_coin_field(
    path,
    coin_id: str,
    field: str,
    new_value,
    *,
    expect_contains: str | None = None,
    must_exist: bool = True,
) -> bool:
    """Surgically set/clear/replace one `field` on the coin `coin_id`, by
    line-based block-scoped editing — NO serialization round-trip, so the rest
    of the file is byte-for-byte untouched (immune to the reformat trap).

    `field` is matched as the first `<indent><field>:` line inside the coin's
    block, so nested catalog sub-fields (e.g. 'bruun_collection_id', 'km') work
    as long as the bare name is unique within the block (the usual case).

    new_value:
      * str / number  -> scalar  (`field: 'x'`)
      * list/tuple     -> block list (`field:` + `- 'x'` items); a 1-element
                          list is written as a scalar for cleanliness
      * None           -> remove the field (and its list items) entirely

    expect_contains: if given, assert the existing field text contains this
      substring before editing (guards against editing the wrong occurrence).
    must_exist: if False, a missing field is a no-op returning False instead of
      raising.

    Returns True if a change was written, False on no-op. Raises on a genuinely
    unexpected state (block/field not found when required, expect mismatch).
    """
    path = Path(path)
    fam = family_of(path)
    if fam == "pyyaml120":
        # PyYAML files have no comments/quote-state to preserve, so a line-based
        # edit is still the safest; but warn callers via the docstring. We still
        # operate line-based here (works regardless of serializer).
        pass
    text = path.read_text()
    nl = "\n"
    lines = text.split(nl)
    b = _coin_block_bounds(lines, coin_id)
    if b is None:
        raise KeyError(f"{path.name}: coin id {coin_id!r} not found")
    s, e = b
    fi = None
    field_re = re.compile(rf"^(\s*){re.escape(field)}:(\s|$)")
    for i in range(s, e):
        if field_re.match(lines[i]):
            fi = i
            break
    if fi is None:
        if must_exist:
            raise KeyError(f"{path.name}:{coin_id}: field {field!r} not found in block")
        return False
    indent = re.match(r"^(\s*)", lines[fi]).group(1)
    rest = lines[fi].split(":", 1)[1].strip()
    if rest:  # scalar field — single line
        span_end = fi + 1
    else:     # list field — header + following same-indent '- ' items
        span_end = fi + 1
        item_re = re.compile(rf"^{re.escape(indent)}-\s")
        while span_end < e and item_re.match(lines[span_end]):
            span_end += 1
    if expect_contains is not None:
        block_txt = nl.join(lines[fi:span_end])
        if expect_contains not in block_txt:
            raise ValueError(
                f"{path.name}:{coin_id}: expected {expect_contains!r} in "
                f"{field!r} block, got {block_txt!r}")
    if new_value is None:
        new_lines: list[str] = []
    elif isinstance(new_value, (list, tuple)) and len(new_value) == 1:
        new_lines = _render_field(indent, field, new_value[0])
    else:
        new_lines = _render_field(indent, field, new_value)
    old_lines = lines[fi:span_end]
    if old_lines == new_lines:
        return False
    lines[fi:span_end] = new_lines
    path.write_text(nl.join(lines))
    return True
