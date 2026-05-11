"""Enrich ``weight_rough_g.source`` labels with per-specimen catalog refs.

Background. The rendered weight column shows per-specimen tooltips
keyed off the source label (e.g. ``IKMK Berlin, Inv. 18284698``). When
one coin entry aggregates ≥2 specimens from the same resource, the
plain inv-number / lot-number tooltip leaves the reader unable to tell
which Stempelvariante the specific weight represents — even though the
museum / auction record itself documents the catalog index per
specimen.

Operational rule (formalised 2026-05-09): for any coin whose
``weight_rough_g`` carries ≥2 entries from a single resource, look up
the per-specimen catalog index from the cached source record and
append it to the source label as a parenthetical. The annotation goes
in BEFORE any existing free-text parens (``(mule)``, ``(1620)``) so
the catalog ref is always the first thing the reader sees.

Idempotent: if the source label already contains a recognized catalog
token (``Lange``, ``KM``, ``Hede``, ``Sieg``, ``Dav``, ``Schou`` next
to a number) we leave it alone — re-running the script after a manual
correction is a no-op.

Per-resource extraction:

* **IKMK Berlin** — parse the ``literatur`` field. Recognises the
  Lange-Vol-II citation pattern that covers the whole SH corpus, with
  the ``Vgl.``/``vgl.`` prefix → ``cf Lange ...``.
* **Bruun (Stack's Bowers Zürich 2025 Parts I–IV)** — read the lot's
  ``refs`` dict. Compact display: KM (always if present), then a
  region-specific second ref (Lange for SH, Hede for DK), then any
  remaining recognized ref limited to total 3 to keep tooltips
  readable.
* **ucoin** — pull ``km`` from the ucoin URL-index (``KM# 26.1``-style
  with sub-variant suffix preserved).
* **Numista** — skip; Numista entries are type-level and their refs
  duplicate the row's ``catalog`` block.

Usage::

    python scripts/maintenance/annotate_weight_source_with_refs.py \
        [--dry-run] [--location <loc>]

The script also rewrites matching ``sources[i].ref`` strings (the
``ref`` field on the ``sources`` block typically mirrors the weight
``source`` label, so the two stay in sync after the rewrite).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from ruamel.yaml import YAML

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import HARVEST_ROOT as CACHE, PROJECT_ROOT as PROJECT  # noqa: E402

DATA_DIR = PROJECT / "data" / "locations"

# Tokens that already mark a label as "enriched". We detect any one of
# them adjacent to a number or hash to avoid false-positives on free
# prose. ``\#?`` allows both ``KM 26`` and ``KM#26``.
_ALREADY_ENRICHED = re.compile(
    r"\b(?:Lange|KM|UC|Hede|Sieg|Schou|Dav|Behrens|Gaedechens|Weinmeister|Mayer)\s*\#?\s*\d",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Resource detection
# ---------------------------------------------------------------------------

_IKMK_RE = re.compile(r"\bIKMK\s+Berlin,\s*Inv\.?\s*(\d+)", re.IGNORECASE)
_BRUUN_RE = re.compile(
    r"\bBruun\s+Part\s+([IVX]+),\s+lot\s+(\d+)(?:,\s+p\.\s+(\d+))?",
    re.IGNORECASE,
)
_UCOIN_RE = re.compile(r"\bucoin\s+tid\s+(\d+)", re.IGNORECASE)


def detect_resource(label: str) -> str | None:
    if not label:
        return None
    if _IKMK_RE.search(label):
        return "IKMK"
    if _BRUUN_RE.search(label):
        return "Bruun"
    if _UCOIN_RE.search(label):
        return "ucoin"
    if "Numista" in label or "numista" in label.lower():
        return "Numista"
    return None


# ---------------------------------------------------------------------------
# Cache lookups
# ---------------------------------------------------------------------------


def _ikmk_record(inv: str) -> dict | None:
    p = CACHE / "ikmk" / f"{inv}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _ucoin_index() -> dict:
    p = CACHE / "ucoin" / "_url_index.json"
    return json.loads(p.read_text()) if p.exists() else {}


_BRUUN_PARTS_CACHE: dict[int, dict] = {}


def _bruun_lot(part_roman: str, lot_no: str) -> dict | None:
    """Return the lot dict from cached Bruun parts. Indexed lazily."""
    part_num = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(part_roman.upper())
    if part_num is None:
        return None
    if part_num not in _BRUUN_PARTS_CACHE:
        path = CACHE / "bruun" / "lots" / f"part{part_num}.json"
        if not path.exists():
            return None
        lots = json.loads(path.read_text())
        _BRUUN_PARTS_CACHE[part_num] = {str(l["lot_no"]): l for l in lots}
    return _BRUUN_PARTS_CACHE[part_num].get(str(lot_no))


# ---------------------------------------------------------------------------
# Per-resource ref extraction
# ---------------------------------------------------------------------------


_LANGE_NR = re.compile(r"Nr\.\s*(\d+(?:\s*[A-Za-z](?:/[A-Za-z\-]+)?)?)")


def ikmk_refs_from_literatur(literatur: str | None) -> list[str]:
    """Extract a compact catalog-ref list from the IKMK ``literatur``
    field. Returns the Lange tag for confirmed-match specimens; returns
    an empty list when IKMK marks the entry as ``Vgl.`` (vergleiche /
    «compare to») — those specimens are *unindexed* in Lange and the
    literatur only points to the closest known canonical entry, not a
    catalog index of the specimen itself.
    """
    if not literatur:
        return []
    if re.search(r"\b(?:vgl\.|Vgl\.)\s+", literatur):
        return []  # specimen is unindexed; the source only points at a similar known entry
    m = _LANGE_NR.search(literatur)
    if not m:
        return []
    raw = m.group(1).strip()
    # Normalise spacing: "535 a" → "535a", "542 c" → "542c"
    norm = re.sub(r"(\d+)\s+([A-Za-z])", r"\1\2", raw)
    return ["Lange " + norm]


_REGION_PRIORITY: dict[str, list[str]] = {
    # Location prefix → preferred secondary refs after KM
    "schleswig_holstein": ["Lange", "Hede", "Sieg", "Dav"],
    "holstein_schauenburg": ["Lange", "Weinmeister", "Dav"],
    "denmark": ["Hede", "Sieg", "Dav", "Schou"],
    "lubeck": ["Behrens", "Mayer"],
    "hamburg": ["Gaedechens"],
}


def bruun_compact_refs(refs: dict, location: str) -> list[str]:
    """Pick a compact subset of Bruun lot's catalog refs (≤3 entries).

    Always includes KM if available. Then appends region-priority
    secondary refs (Lange for SH, Hede for Denmark, etc.). Caps at 3
    total to keep the tooltip readable.
    """
    if not refs:
        return []
    out: list[str] = []

    def emit(key: str, label: str | None = None) -> None:
        if key in refs and refs[key]:
            out.append(f"{label or key} {refs[key]}")

    emit("KM")
    secondaries = _REGION_PRIORITY.get(location, [])
    for k in secondaries:
        if len(out) >= 3:
            break
        emit(k)
    # If we still have room, add any remaining recognised ref
    for k in ("Lange", "Hede", "Sieg", "Dav", "Schou"):
        if len(out) >= 3:
            break
        if k in refs and not any(o.startswith(k + " ") for o in out):
            emit(k)
    return out


def ucoin_refs(tid: str, idx: dict) -> list[str]:
    e = idx.get(str(tid))
    if not e:
        return []
    km = (e.get("km") or "").strip()
    if not km:
        return []
    # ucoin format: "KM# 26.1" → "KM 26.1"
    m = re.match(r"KM\s*\#?\s*(\S+)", km)
    if m:
        return [f"KM {m.group(1)}"]
    return [km]


# ---------------------------------------------------------------------------
# Label rewriting
# ---------------------------------------------------------------------------


_CF_LANGE_RE = re.compile(r"\(cf Lange [^);]+;\s*")
_CF_LANGE_PURE_RE = re.compile(r"\s*\(cf Lange [^)]+\)")


def strip_cf_lange(label: str) -> str:
    """Remove ``(cf Lange ...)`` annotations from a previously-enriched
    label. Used to retract incorrect index-style annotations on cf
    specimens (which carry no catalog index of their own — see
    ``ikmk_refs_from_literatur`` docstring).

    Two shapes handled:

    * ``... (cf Lange 339B)`` → ``...``
    * ``... (cf Lange 533A/b; mule)`` → ``... (mule)``
    """
    # Strip "(cf Lange XYZ; " prefix when followed by other tokens
    label = _CF_LANGE_RE.sub("(", label)
    # Strip standalone "(cf Lange XYZ)" parens
    label = _CF_LANGE_PURE_RE.sub("", label)
    return label.rstrip()


def rewrite_label(label: str, location: str, ucoin_idx: dict) -> tuple[str, str | None]:
    """Return (new_label, ref_token_added) for one source-label LINE.

    If the label is already enriched OR no refs are found, returns the
    label (possibly with cf-cleanup applied) and ``ref_token_added=None``.
    """
    label = strip_cf_lange(label)
    if _ALREADY_ENRICHED.search(label):
        return label, None
    refs: list[str] = []
    res = detect_resource(label)
    if res == "IKMK":
        m = _IKMK_RE.search(label)
        if m:
            rec = _ikmk_record(m.group(1))
            if rec:
                refs = ikmk_refs_from_literatur(rec.get("literatur"))
    elif res == "Bruun":
        m = _BRUUN_RE.search(label)
        if m:
            lot = _bruun_lot(m.group(1), m.group(2))
            if lot:
                refs = bruun_compact_refs(lot.get("refs") or {}, location)
    elif res == "ucoin":
        m = _UCOIN_RE.search(label)
        if m:
            refs = ucoin_refs(m.group(1), ucoin_idx)
    # Numista intentionally not annotated — type-level refs duplicate
    # the row's catalog block and add no per-specimen signal.
    if not refs:
        return label, None
    refs_str = "; ".join(refs)
    # Merge into existing parens-tail if present, else append.
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", label)
    if m:
        base, existing = m.group(1), m.group(2)
        new = f"{base} ({refs_str}; {existing})"
    else:
        new = f"{label} ({refs_str})"
    return new, refs_str


def rewrite_multiline(label: str, location: str, ucoin_idx: dict) -> tuple[str, int]:
    """Apply rewrite to each \\n-separated line independently. Returns
    ``(new_label, n_lines_changed)`` — counts both ref-additions AND
    cf-cleanup as changes so retractions also flow to disk."""
    if "\n" not in label:
        new, _ = rewrite_label(label, location, ucoin_idx)
        return new, (1 if new != label else 0)
    lines = label.split("\n")
    n_changed = 0
    out_lines = []
    for ln in lines:
        new_ln, _ = rewrite_label(ln.strip(), location, ucoin_idx)
        if new_ln != ln.strip():
            n_changed += 1
        out_lines.append(new_ln)
    return "\n".join(out_lines), n_changed


# ---------------------------------------------------------------------------
# Per-coin processing
# ---------------------------------------------------------------------------


def process_coin(coin: dict, location: str, ucoin_idx: dict) -> int:
    """In-place enrich weight_rough_g + sources entries. Returns count
    of labels rewritten."""
    wrg = coin.get("weight_rough_g")
    if not isinstance(wrg, list):
        return 0

    # Count entries per resource to decide eligibility
    per_resource: dict[str, list[int]] = defaultdict(list)
    for idx, e in enumerate(wrg):
        if not hasattr(e, "get"):
            continue
        src = e.get("source", "") or ""
        for line in str(src).split("\n"):
            r = detect_resource(line.strip())
            if r:
                per_resource[r].append(idx)

    eligible_resources = {r for r, idxs in per_resource.items() if len(idxs) >= 2}
    if not eligible_resources:
        return 0

    # Collect URLs / refs to mirror onto sources[]
    label_remap: dict[str, str] = {}
    n_rewritten = 0

    for entry in wrg:
        if not hasattr(entry, "get"):
            continue
        old = entry.get("source", "") or ""
        # Only rewrite if THIS label belongs to an eligible resource
        any_eligible = False
        for line in str(old).split("\n"):
            r = detect_resource(line.strip())
            if r in eligible_resources:
                any_eligible = True
                break
        if not any_eligible:
            continue
        new, n = rewrite_multiline(old, location, ucoin_idx)
        if n and new != old:
            entry["source"] = new
            label_remap[old.strip()] = new.strip()
            # Per-line remap too (sources[] ref may match a single line)
            for ol, nl in zip(str(old).split("\n"), str(new).split("\n")):
                if ol.strip() != nl.strip():
                    label_remap[ol.strip()] = nl.strip()
            n_rewritten += n

    # Mirror onto sources[].ref
    if label_remap:
        for src in coin.get("sources", []) or []:
            if not hasattr(src, "get"):
                continue
            r_old = src.get("ref", "") or ""
            r_new = label_remap.get(r_old.strip())
            if r_new and r_new != r_old:
                src["ref"] = r_new

    return n_rewritten


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--location", action="append", default=None)
    args = ap.parse_args()

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    ucoin_idx = _ucoin_index()
    grand_total = 0
    coins_touched = 0

    paths = sorted(DATA_DIR.glob("*.yml"))
    for path in paths:
        if path.name.endswith("-references.yml"):
            continue
        loc = path.stem
        if args.location and loc not in args.location:
            continue
        with path.open() as f:
            doc = yaml.load(f)
        loc_total = 0
        loc_coins = 0
        for coin in doc.get("coins", []) or []:
            n = process_coin(coin, loc, ucoin_idx)
            if n:
                loc_total += n
                loc_coins += 1
        if loc_total:
            print(f"  {loc}: {loc_total} labels rewritten across {loc_coins} coins")
            if not args.dry_run:
                with path.open("w") as f:
                    yaml.dump(doc, f)
        grand_total += loc_total
        coins_touched += loc_coins

    print()
    print(f"Total: {grand_total} labels rewritten across {coins_touched} coins"
          f"{' (dry-run; no files written)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
