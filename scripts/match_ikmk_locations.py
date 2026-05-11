"""Match IKMK Berlin records against project location YAMLs.

Generic per-location matcher. For each location whose IKMK title-prefix
mapping is recorded in ``scripts/cache/ikmk/_index_by_issuer.json``
(i.e. populated by ``scripts/audit_ikmk_index.py``), walk every IKMK
record under those prefixes and bucket it against the location's
``data/locations/<loc>.yml`` content.

CLI::

    python scripts/match_ikmk_locations.py                     # all mapped locations
    python scripts/match_ikmk_locations.py schleswig_holstein  # one location
    python scripts/match_ikmk_locations.py denmark lauenburg   # several

Buckets per IKMK record (ordered by signal strength):

* **strict_match** — shared catalogue ref (Lange / Hede / Davenport /
  Sieg / Schou). Most reliable.
* **fuzzy_match** — high-confidence ``year + ruler-first-name +
  nominal-token + weight ±3 %`` match without a catalogue overlap
  (score ≥ 7).
* **new_lange_variant** — IKMK has a Lange # we don't catalogue, but
  ruler / year align with one of our coins. Likely a new sub-variant
  worth adding to YAML.
* **weak_candidate** — partial signal (year + one of ruler / nominal
  / weight) without a catalogue overlap, score 4-6. Usually means we
  have the coin under a different KM# variant we never linked
  Lange # to, or it's a new specimen of an existing type.
* **no_match** — neither catalogue overlap nor year-window candidate.

Outputs (per location L)::

    scripts/cache/ikmk/_match_<L>.json   machine record
    scripts/cache/ikmk/_match_<L>.md     human digest

Idempotent. Re-runs after extending IKMK cache or the YAMLs refresh
both files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import IKMK_CACHE as CACHE, PROJECT_ROOT as REPO  # noqa: E402

LOCATIONS = REPO / "data" / "locations"
INDEX_PATH = CACHE / "_index_by_issuer.json"


# ---------- Catalogue-ref extraction from IKMK literatur -------------

# Sub-variant tail captures multi-letter + slash forms common in Lange /
# Hede / Bruun catalogues — e.g. «533 A/b» (a die-mule), «430 AA»,
# «99 Aa», «3746 var». The original regex captured only a single
# trailing letter, silently truncating «A/b» → «A» and collapsing
# distinct sub-variants under one key. The truncation was symmetric
# with YAML normalisation so routing usually survived — but the
# source-label fidelity needed for §9a sub-variant bucket discrimination
# was lost. Mirrors the closed TODO J fix in scripts/bruun_parser.
#
# Each compiled regex gets its own copy of the named group `q`, which
# is fine because they are separate compiled patterns (no group-name
# collision across regexes).
_TAIL = r"(?P<q>[A-Za-z]+(?:\s*/\s*[A-Za-z]+)*(?:\.\d+)?)?"

RE_LANGE = re.compile(
    r"(?P<cf>Vgl\.\s+)?Chr\.?\s*Lange'?s\s*,?\s*Sammlung[^()]*\((?P<year>1908|1912)\)"
    r"[\s\S]*?Nr\.?\s*(?P<num>\d+)\s*" + _TAIL,
    re.IGNORECASE,
)
RE_HEDE = re.compile(
    r"(?:H\.\s*)?Hede[^A-Za-z0-9]+(?:[\s\S]*?Nr\.?\s*)?(?P<num>\d+)\s*"
    + _TAIL + r"\b",
    re.IGNORECASE,
)
RE_DAV = re.compile(
    r"Davenport[\s\S]*?Nr\.?\s*(?P<num>\d+)\s*" + _TAIL + r"\b",
    re.IGNORECASE,
)
RE_SIEG = re.compile(
    r"\bSieg[^A-Za-z0-9]+(?:[\s\S]*?Nr\.?\s*)?(?P<num>\d+(?:\.\d+)?)\s*"
    + _TAIL + r"\b",
    re.IGNORECASE,
)
RE_SCHOU = re.compile(
    r"\bSchou[^A-Za-z0-9]+(?:[\s\S]*?Nr\.?\s*)?(?P<num>\d+)\s*" + _TAIL + r"\b",
    re.IGNORECASE,
)


def _norm(num: str, q: str | None) -> str:
    """Normalise a catalogue ref to a lookup key.

    Strips whitespace, lowercases. Preserves slash separators so multi-
    letter sub-variant tails like «A/b» stay distinct from plain «A».
    The strict-ref lookup path falls back to the root («533a/b» →
    «533a») when an exact match misses, so YAML coins still resolve
    from IKMK records carrying the fuller tag.
    """
    tail = re.sub(r"\s+", "", (q or "")).lower()
    return f"{num}{tail}"


def extract_refs(literatur: str) -> dict[str, list[dict]]:
    refs: dict[str, list[dict]] = {}
    if not literatur:
        return refs
    for m in RE_LANGE.finditer(literatur):
        refs.setdefault("lange", []).append({
            "vol": "I" if m.group("year") == "1908" else "II",
            "num": m.group("num"),
            "q": (m.group("q") or "").strip(),
            "cf": bool(m.group("cf")),
            "norm": _norm(m.group("num"), m.group("q")),
        })
    for m in RE_HEDE.finditer(literatur):
        refs.setdefault("hede", []).append({
            "norm": _norm(m.group("num"), m.group("q")),
        })
    for m in RE_DAV.finditer(literatur):
        refs.setdefault("dav", []).append({
            "norm": _norm(m.group("num"), m.group("q")),
        })
    for m in RE_SIEG.finditer(literatur):
        refs.setdefault("sieg", []).append({
            "norm": _norm(m.group("num"), m.group("q")),
        })
    for m in RE_SCHOU.finditer(literatur):
        refs.setdefault("schou", []).append({
            "norm": _norm(m.group("num"), m.group("q")),
        })
    return refs


# ---------- Our YAML extraction --------------------------------------


def _norm_ref(value) -> str:
    return re.sub(r"\s+", "", str(value)).lower()


# Hede 1971 publishes a separate catalogue volume per Danish king;
# danskmoent.dk hosts entries under URLs keyed by ruler-prefix +
# Hede number (c4h28 ≠ c5h28 ≠ f3h28). The bare Hede number is
# therefore ambiguous across rulers, so the matcher's strict-by-hede
# path uses a COMPOSITE key («c4h28») on both sides:
#   * coin index: composed from `catalog.hede_volume + catalog.hede`.
#   * IKMK record: derived from the record's title prefix
#     («Dänemark: Christian IV.» → c4h) combined with the Hede
#     number parsed from `literatur`.
# Without this gate, the strict path collapses cross-ruler Hede
# collisions (e.g. IKMK 18204859 = Christian VIII 1842 «Hede 1»
# was wrongly strict-matched to our hede-1-chr-iv-1591 = Christian
# IV 1591 «Hede 1» before the gate landed).
_RULER_TO_VOLUME = [
    ("Christian X", "c10h"), ("Christian IX", "c9h"),
    ("Christian VIII", "c8h"), ("Christian VII", "c7h"),
    ("Christian VI", "c6h"), ("Christian V", "c5h"),
    ("Christian IV", "c4h"), ("Christian III", "c3h"),
    ("Christian II", "c2h"), ("Christian I", "c1h"),
    ("Frederik IX", "f9h"), ("Frederik VIII", "f8h"),
    ("Frederik VII", "f7h"), ("Frederik VI", "f6h"),
    ("Frederik V", "f5h"), ("Frederik IV", "f4h"),
    ("Frederik III", "f3h"), ("Frederik II", "f2h"),
    ("Frederik I", "f1h"),
    ("Friedrich IX", "f9h"), ("Friedrich VIII", "f8h"),
    ("Friedrich VII", "f7h"), ("Friedrich VI", "f6h"),
    ("Friedrich V", "f5h"), ("Friedrich IV", "f4h"),
    ("Friedrich III", "f3h"), ("Friedrich II", "f2h"),
    ("Friedrich I", "f1h"),
]


def _ruler_to_hede_volume(text: str) -> str | None:
    if not text:
        return None
    for needle, code in _RULER_TO_VOLUME:
        if needle in text:
            return code
    return None


def _ikmk_hede_volume(summary: dict) -> str | None:
    """Derive the ruler-volume code from an IKMK record summary.

    Tries (in order):
      1. The summary's `ruler` field (extracted from
         `linked_persons_corporations` Autorität / Münzherr).
      2. The summary's `title` after the colon
         («Dänemark: Christian IV.» → c4h).

    Returns None when no Danish-king ruler can be identified — in
    which case the strict-by-hede path skips the record (Hede
    catalogue is per-ruler; without a ruler-volume on the IKMK
    side we can't safely strict-match against our composite-key
    index).

    Also returns None for IKMK records whose country prefix is
    «Norwegen»: Hede 1971 numbers Denmark and Norway sections
    INDEPENDENTLY (page 30 «Hede 8» = FrIII Danish ½ Dukat;
    page 115 «Hede 8 b» = FrIII Norwegian Taler — completely
    different coins). Our denmark.yml indexes Danish-section
    Hede; matching a Norwegian-section Hede to it would be a
    cross-section false-positive of the same shape this fix
    is designed to prevent."""
    if not isinstance(summary, dict):
        return None
    title = summary.get("title") or ""
    # Country prefix gate — Norwegen records have their own Hede
    # numbering and must not match Danish-section index entries.
    country_prefix = title.split(":", 1)[0].strip() if ":" in title else ""
    if country_prefix.lower() in ("norwegen", "norge", "norway"):
        return None
    after_colon = title.split(":", 1)[1] if ":" in title else title
    v = _ruler_to_hede_volume(after_colon)
    if v:
        return v
    # Fallback: bare ruler name (rarely sufficient — accept only if
    # the after-colon content is wholly a ruler ordinal expression
    # we can resolve).
    ruler = summary.get("ruler") or ""
    if ruler:
        v = _ruler_to_hede_volume(ruler)
        if v:
            return v
    return None


def index_our_coins(coins: list[dict]) -> dict[str, dict[str, list[dict]]]:
    index = {k: {} for k in ("lange", "hede", "dav", "sieg", "schou", "km")}
    for c in coins:
        cat = c.get("catalog") or {}
        for code in index:
            if code == "hede":
                # Composite key: «c4h28» = «{hede_volume}{hede_number}».
                # When `hede_volume` is missing on the coin, fall back
                # to bare number so the existing index doesn't drop
                # entries that haven't been backfilled yet.
                v = cat.get("hede")
                if v:
                    norm = _norm_ref(v)
                    vol = cat.get("hede_volume")
                    key = f"{_norm_ref(vol)}{norm}" if vol else norm
                    index["hede"].setdefault(key, []).append(c)
                continue
            v = cat.get(code)
            if v:
                index[code].setdefault(_norm_ref(v), []).append(c)
        for o in cat.get("others") or []:
            mo = re.match(r"\s*Lange[#\s]*(\d+\s*[a-z]?)", str(o), re.IGNORECASE)
            if mo:
                index["lange"].setdefault(_norm_ref(mo.group(1)), []).append(c)
    return index


# ---------- Ruler-token matching (lightweight, location-agnostic) ----

# Common monarchic / dynastic first names across the project's German /
# Danish / Norwegian rulers.
RULER_FIRST_NAMES = {
    "johann", "hans", "christian", "friedrich", "frederick", "frederik",
    "ernst", "adolf", "adolph", "philipp", "peter", "georg", "albrecht",
    "carl", "karl", "joachim", "ferdinand", "rudolph", "rudolf", "magnus",
    "otto", "heinrich", "herman", "hermann", "leopold", "wilhelm",
    "wilhelmine", "marie", "anna", "maria", "elisabeth", "sophie", "sophia",
    "alexander", "ulrich", "augustenburg", "just", "justus", "jobst",
}

# Dynastic / territorial-line tokens — pulled together for fuzzy
# matching across all SH+DK+Lauenburg+Bremen-Verden+Lübeck contexts.
DYNASTIC_LINES = {
    "sonderburg": "sonderburg",
    "gottorf": "gottorf", "gottorp": "gottorf",
    "glücksburg": "glücksburg", "glucksburg": "glücksburg",
    "plön": "plön", "ploen": "plön",
    "augustenburg": "augustenburg",
    "schaumburg": "schaumburg", "schauenburg": "schaumburg",
    "pinneberg": "schaumburg",
    "norburg": "norburg",
    "lauenburg": "lauenburg",
    "dänemark": "dänemark", "denmark": "dänemark",
    "norwegen": "dänemark", "norway": "dänemark",
    "lübeck": "lübeck", "luebeck": "lübeck",
    "bremen": "bremen",
    "holstein": "holstein",
    "schleswig": "schleswig",
}


def _ruler_tokens(text: str) -> tuple[set[str], set[str]]:
    text_l = text.lower()
    first_names = set()
    lines = set()
    for tok in re.findall(r"[a-zäöü]{3,}", text_l):
        if tok in RULER_FIRST_NAMES:
            first_names.add(tok)
        if tok in DYNASTIC_LINES:
            lines.add(DYNASTIC_LINES[tok])
    return first_names, lines


# ---------- Per-record extraction + diff -----------------------------


def _ikmk_summary(rec: dict) -> dict:
    pers = rec.get("linked_persons_corporations") or {}
    ruler = ""
    if isinstance(pers, dict):
        for v in pers.values():
            if not isinstance(v, dict):
                continue
            if v.get("type_name_de") in ("Münzherr", "Autorität", "Dargestellte/r"):
                items = v.get("items") or {}
                for it in items.values():
                    ruler = it.get("last_name_de") or ""
                    if ruler:
                        break
                if ruler:
                    break
    nominal = (rec.get("nominal") or {}).get("nominal_de") or ""
    mint_place = ""
    for m in (rec.get("mint") or []):
        if isinstance(m, dict):
            mint_place = m.get("place_name_de") or ""
            break
    return {
        "id": rec.get("ikmk_mds_id"),
        "title": rec.get("title"),
        "year_start": rec.get("year_start"),
        "year_end": rec.get("year_end"),
        "ruler": ruler,
        "nominal": nominal,
        "mint": mint_place,
        "weight": rec.get("weight") or "",
        "diameter": rec.get("diameter") or "",
        "avers_leg": (rec.get("avers") or {}).get("leg_text") or "",
        "revers_leg": (rec.get("revers") or {}).get("leg_text") or "",
        "literatur": rec.get("literatur") or "",
        "refs": extract_refs(rec.get("literatur") or ""),
        "permalink": rec.get("permalink"),
        "image_right": (rec.get("image_right") or {}).get("short"),
    }


# Mass-sanity gate threshold for fuzzy/cf-only candidate routing.
# When IKMK and host both publish a weight, the ratio (IKMK / host_median)
# must fall within [1/_WEIGHT_GATE, _WEIGHT_GATE]. 1.5 gives ±50%
# headroom — comfortably covers normal specimen variance (±10-15%) and
# Kipper-period debasement (up to ±25-30%) — while correctly rejecting
# adjacent-fraction confusion: a 1/2 vs 1 or 1/16 vs 1/8 pairing has
# ratio exactly 2.0, and those are distinct types deserving separate
# YAML entries, not a cf-only merge. Discovered when a fuzzy cf-only
# «Vgl. Lange 339 B» Doppelschilling cluster routed to km-49-fr-iii-1618
# (Reichsthaler, ratio ~14×) because km-49's ruler spelling happened to
# share more tokens with IKMK than the correct host km-46-fr-iii-1617
# — see TODO L.1 audit, May 2026.
_WEIGHT_GATE = 1.5


def _ikmk_weight_g(ikmk: dict) -> float | None:
    """Parse a leading numeric gram-value from an IKMK weight string."""
    raw = ikmk.get("weight") or ""
    m = re.match(r"\s*([\d.]+)", raw)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _host_weights_g(ours: dict) -> list[float]:
    """Collect numeric gram-values from a YAML coin's weight_rough_g."""
    raw = ours.get("weight_rough_g")
    if isinstance(raw, list):
        out: list[float] = []
        for entry in raw:
            if isinstance(entry, dict):
                v = entry.get("value")
                if isinstance(v, (int, float)) and v > 0:
                    out.append(float(v))
        return out
    if isinstance(raw, (int, float)) and raw > 0:
        return [float(raw)]
    return []


def _weight_compatible(ikmk: dict, ours: dict) -> bool:
    """Reject pairings where IKMK and host weights differ by > _WEIGHT_GATE×.

    Returns True (allow) when either side lacks a numeric weight — the
    gate only fires when both observations exist.
    """
    wi = _ikmk_weight_g(ikmk)
    if wi is None:
        return True
    weights = _host_weights_g(ours)
    if not weights:
        return True
    weights.sort()
    median = weights[len(weights) // 2]
    if median <= 0:
        return True
    ratio = wi / median
    return (1.0 / _WEIGHT_GATE) <= ratio <= _WEIGHT_GATE


def _diff_fields(ikmk: dict, ours: dict) -> dict:
    diff: dict = {}
    if ikmk["avers_leg"] and not (ours.get("inscription_obv") or "").strip():
        diff["inscription_obv"] = ikmk["avers_leg"]
    if ikmk["revers_leg"] and not (ours.get("inscription_rev") or "").strip():
        diff["inscription_rev"] = ikmk["revers_leg"]
    if ikmk["diameter"] and ours.get("diameter_mm") in (None, 0):
        diff["diameter_mm"] = ikmk["diameter"]
    cat = ours.get("catalog") or {}
    for code in ("lange", "hede", "dav", "sieg", "schou"):
        entries = ikmk["refs"].get(code, [])
        if entries and not cat.get(code):
            for r in entries:
                if not r.get("cf"):
                    diff[f"catalog.{code}"] = r["norm"]
                    break
    return diff


def _fuzzy_score(ikmk: dict, ours: dict) -> tuple[int, list[str]]:
    score = 0
    why = []
    try:
        iy = int(ikmk.get("year_start") or 0) or None
    except (TypeError, ValueError):
        iy = None
    try:
        oy = int(ours.get("year_first") or 0) or None
    except (TypeError, ValueError):
        oy = None
    if iy and oy and abs(iy - oy) <= 1:
        score += 2
        why.append(f"year {iy}≈{oy}")
    elif iy and oy and abs(iy - oy) <= 3:
        score += 1
        why.append(f"year {iy}~{oy}")
    i_first, i_line = _ruler_tokens(ikmk.get("ruler") or "")
    o_first, o_line = _ruler_tokens(ours.get("ruler") or "")
    shared_first = i_first & o_first
    shared_line = i_line & o_line
    if shared_first and shared_line:
        score += 4
        why.append(f"ruler {sorted(shared_first)[0]}/{sorted(shared_line)[0]}")
    elif shared_first:
        score += 2
        why.append(f"ruler-first {sorted(shared_first)[0]}")
    elif shared_line:
        score += 1
        why.append(f"ruler-line {sorted(shared_line)[0]}")
    ours_nom = (ours.get("nominal") or "").lower()
    ikmk_nom = (ikmk.get("nominal") or "").lower()
    for tok in re.findall(r"[a-zäöüß]{5,}", ikmk_nom):
        if tok in ours_nom:
            score += 1
            why.append(f"nominal '{tok}'")
            break
    try:
        wi = float(re.match(r"([\d.]+)", ikmk["weight"] or "").group(1))
        ow_raw = ours.get("weight_rough_g")
        if isinstance(ow_raw, list):
            for entry in ow_raw:
                if isinstance(entry, dict):
                    wo = entry.get("value")
                    if wo and abs(wi - wo) / wo < 0.03:
                        score += 2
                        why.append(f"weight {wi:.2f}≈{wo:.2f}")
                        break
        elif isinstance(ow_raw, (int, float)):
            if abs(wi - ow_raw) / ow_raw < 0.03:
                score += 2
                why.append(f"weight {wi:.2f}≈{ow_raw:.2f}")
    except Exception:
        pass
    return score, why


# ---------- Per-location driver --------------------------------------


def match_one_location(loc_id: str, index: dict) -> dict | None:
    by_loc = index["by_project_location"].get(loc_id) or []
    if not by_loc:
        print(f"[!] {loc_id}: no IKMK prefixes mapped (skipping)")
        return None
    yaml_path = LOCATIONS / f"{loc_id}.yml"
    if not yaml_path.exists():
        print(f"[!] {loc_id}: yaml missing: {yaml_path}")
        return None
    yml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    our_coins = yml.get("coins", []) or []
    our_idx = index_our_coins(our_coins)

    ikmk_ids: list[str] = []
    for p in by_loc:
        ikmk_ids.extend(index["issuers"][p]["ids_in_scope"])

    print(f"\n=== {loc_id} ===")
    print(f"  prefixes: {by_loc}")
    print(f"  IKMK records: {len(ikmk_ids)}  | YAML coins: {len(our_coins)}  "
          f"(lange={len(our_idx['lange'])} hede={len(our_idx['hede'])} "
          f"dav={len(our_idx['dav'])} sieg={len(our_idx['sieg'])})")

    matches: list[dict] = []
    for nid in ikmk_ids:
        rec = json.loads((CACHE / f"{nid}.json").read_text(encoding="utf-8"))
        s = _ikmk_summary(rec)

        # 1. Strict catalogue-ref match — Lange/Hede/Dav/Sieg/Schou.
        # Tries the exact normalised key first, then a slash-stripped
        # root («533a/b» → «533a»), then a trailing-letter root
        # («3a» → «3», «339c» → «339») so YAML coins catalogued at the
        # parent-tag level still resolve from IKMK records that publish
        # a fuller sub-variant. The `match_reason` keeps the IKMK form
        # so the reader sees which sub-variant the IKMK actually attests.
        #
        # Special-case Hede: lookup key is composite («c4h28») built
        # from the ruler-volume on each side. IKMK volume comes from
        # the record's title prefix; our coin's volume from the
        # filled `catalog.hede_volume` field. When the IKMK record
        # has no recoverable Danish-king ruler, the Hede strict path
        # is skipped — the bare-number lookup that the previous
        # version did was the source of cross-ruler false-positives
        # (Christian VIII «Hede 1» wrongly hitting Christian IV
        # «Hede 1»; see fill_hede_volume.py + audit_ikmk_index.py).
        ours_match = None
        match_reason = None
        ikmk_hede_vol = _ikmk_hede_volume(s)
        for code in ("lange", "hede", "dav", "sieg", "schou"):
            for ref in s["refs"].get(code, []):
                if ref.get("cf"):
                    continue
                if code == "hede":
                    if not ikmk_hede_vol:
                        continue  # can't disambiguate — skip
                    composite = f"{ikmk_hede_vol}{ref['norm']}"
                    lookup = our_idx[code].get(composite)
                    if not lookup and "/" in ref["norm"]:
                        lookup = our_idx[code].get(
                            f"{ikmk_hede_vol}{ref['norm'].split('/', 1)[0]}"
                        )
                    if not lookup:
                        parent = re.match(r"^(\d+(?:\.\d+)?)", ref["norm"])
                        if parent and parent.group(1) != ref["norm"]:
                            lookup = our_idx[code].get(
                                f"{ikmk_hede_vol}{parent.group(1)}"
                            )
                    if lookup:
                        ours_match = lookup[0]
                        match_reason = f"strict by hede {ikmk_hede_vol}{ref['norm']}"
                        break
                    continue
                lookup = our_idx[code].get(ref["norm"])
                if not lookup and "/" in ref["norm"]:
                    lookup = our_idx[code].get(ref["norm"].split("/", 1)[0])
                if not lookup:
                    parent = re.match(r"^(\d+(?:\.\d+)?)", ref["norm"])
                    if parent and parent.group(1) != ref["norm"]:
                        lookup = our_idx[code].get(parent.group(1))
                if lookup:
                    ours_match = lookup[0]
                    match_reason = f"strict by {code} {ref['norm']}"
                    break
            if ours_match:
                break

        # 2. Fuzzy fallback. Mass-sanity gate (_WEIGHT_GATE) rejects
        # candidates whose host weight differs from the IKMK specimen
        # by more than the threshold, which prevents cross-denomination
        # cf-tag pollution (Doppelschilling ~2 g routing to Reichsthaler
        # ~29 g via shared ruler / year tokens).
        ikmk_has_lange = bool(s["refs"].get("lange"))
        if not ours_match:
            try:
                iy = int(s.get("year_start") or 0)
            except (TypeError, ValueError):
                iy = 0
            cands: list[tuple[int, dict, list[str]]] = []
            for c in our_coins:
                try:
                    cy = int(c.get("year_first") or 0)
                except (TypeError, ValueError):
                    cy = 0
                if iy and cy and abs(iy - cy) > 5:
                    continue
                if not _weight_compatible(s, c):
                    continue
                score, why = _fuzzy_score(s, c)
                if score >= 4:
                    cands.append((score, c, why))
            cands.sort(key=lambda x: -x[0])
            if cands:
                top_score = cands[0][0]
                ours_match = cands[0][1]
                if ikmk_has_lange:
                    tag = "new_lange_variant"
                elif top_score >= 7:
                    tag = "fuzzy"
                else:
                    tag = "weak"
                match_reason = (
                    f"{tag} score={top_score} "
                    f"({', '.join(cands[0][2])})"
                )

        if ours_match:
            entry = {
                "ikmk_id": nid,
                "ikmk_title": s["title"],
                "ikmk_year": f"{s['year_start']}-{s['year_end']}",
                "ikmk_nominal": s["nominal"],
                "ikmk_ruler": s["ruler"],
                "ikmk_weight": s["weight"],
                "ikmk_diameter": s["diameter"],
                "ikmk_refs": s["refs"],
                "our_coin_id": ours_match.get("id"),
                "our_year_label": ours_match.get("year_label"),
                "our_nominal": ours_match.get("nominal"),
                "match_reason": match_reason,
                "ikmk_adds": _diff_fields(s, ours_match),
                "permalink": s["permalink"],
                "image_right": s["image_right"],
            }
            matches.append(entry)
        else:
            entry = {
                "ikmk_id": nid,
                "ikmk_title": s["title"],
                "ikmk_year": f"{s['year_start']}-{s['year_end']}",
                "ikmk_nominal": s["nominal"],
                "ikmk_ruler": s["ruler"],
                "ikmk_weight": s["weight"],
                "ikmk_diameter": s["diameter"],
                "ikmk_refs": s["refs"],
                "ikmk_avers_leg": s["avers_leg"],
                "ikmk_revers_leg": s["revers_leg"],
                "match_reason": "no_match",
                "permalink": s["permalink"],
                "image_right": s["image_right"],
            }
            matches.append(entry)

    strict = [m for m in matches if m.get("match_reason", "").startswith("strict")]
    fuzzy = [m for m in matches if m.get("match_reason", "").startswith("fuzzy")]
    new_var = [m for m in matches if m.get("match_reason", "").startswith("new_lange_variant")]
    weak = [m for m in matches if m.get("match_reason", "").startswith("weak")]
    unmatched = [m for m in matches if m["match_reason"] == "no_match"]

    lange_groups: dict[str, list[dict]] = defaultdict(list)
    for m in new_var:
        for r in m.get("ikmk_refs", {}).get("lange", []):
            if not r.get("cf"):
                lange_groups[r["norm"]].append(m)
                break
        else:
            lange_groups["(cf-only)"].append(m)

    out = {
        loc_id: {
            "totals": {
                "ikmk_records": len(matches),
                "strict_match": len(strict),
                "fuzzy_match": len(fuzzy),
                "new_lange_variant": len(new_var),
                "unique_new_lange_numbers": len(lange_groups),
                "weak_candidate": len(weak),
                "no_match": len(unmatched),
            },
            "strict_matches": strict,
            "fuzzy_matches": fuzzy,
            "new_lange_variants_by_lange": {
                lange: [{
                    "ikmk_id": m["ikmk_id"],
                    "year": m["ikmk_year"],
                    "ruler": m.get("ikmk_ruler"),
                    "weight": m.get("ikmk_weight"),
                    "diameter": m.get("ikmk_diameter"),
                    "best_our_coin": m.get("our_coin_id"),
                    "permalink": m.get("permalink"),
                } for m in records]
                for lange, records in sorted(lange_groups.items())
            },
            "weak_candidates": weak,
            "unmatched_records": unmatched,
        },
    }
    out_json = CACHE / f"_match_{loc_id}.json"
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown digest
    md: list[str] = []
    md.append(f"# IKMK ↔ {loc_id}.yml — match report\n")
    md.append(
        f"\n{len(matches)} IKMK records (prefixes: {', '.join(by_loc)}, "
        f"in-scope 1566–1914) matched against `data/locations/{loc_id}.yml`.\n",
    )
    md.append(
        f"\n* **Strict match (catalogue-ref overlap)**: {len(strict)}\n"
        f"* **Fuzzy match (high-confidence same coin, score≥7)**: {len(fuzzy)}\n"
        f"* **New Lange-# variant (IKMK has Lange # we don't catalogue)**: "
        f"{len(new_var)} specimens across **{len(lange_groups)} unique Lange #**\n"
        f"* **Weak candidate (partial signal, score 4-6, no Lange#)**: {len(weak)}\n"
        f"* **No match**: {len(unmatched)}\n",
    )
    if strict:
        md.append("\n## Strict matches — enrichment candidates\n")
        md.append("\n| IKMK | year | our coin | reason | IKMK adds |")
        md.append("|---|---|---|---|---|")
        for m in strict:
            adds = ", ".join(m["ikmk_adds"].keys()) or "—"
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| `{m['our_coin_id']}` | {m['match_reason']} | {adds} |",
            )
    if fuzzy:
        md.append("\n## Fuzzy matches (score≥7) — likely correct, spot-check\n")
        md.append("\n| IKMK | year | our coin | reason | IKMK adds |")
        md.append("|---|---|---|---|---|")
        for m in fuzzy:
            adds = ", ".join(m["ikmk_adds"].keys()) or "—"
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| `{m['our_coin_id']}` | {m['match_reason']} | {adds} |",
            )
    if new_var:
        md.append("\n## New Lange-# variants (potential YAML additions)\n")
        md.append(
            f"\nGrouped by Lange # — {len(lange_groups)} unique #s, "
            f"{len(new_var)} total specimens.\n",
        )
        md.append("\n| Lange # | specimens | year(s) | sample IKMK |")
        md.append("|---|---:|---|---|")
        for lange, recs in sorted(lange_groups.items()):
            years = sorted({r["ikmk_year"].split("-")[0] for r in [
                {"ikmk_year": rr["ikmk_year"]} for rr in recs
            ] if r["ikmk_year"]})
            sample_ids = [r["ikmk_id"] for r in recs[:3]]
            sample_links = ", ".join(
                f"[{nid}](https://ikmk.smb.museum/object?id={nid})"
                for nid in sample_ids
            )
            md.append(
                f"| `Lange {lange}` | {len(recs)} | {','.join(years)} "
                f"| {sample_links} |",
            )
    if weak:
        md.append("\n## Weak candidates (score 4-6, no Lange #)\n")
        md.append("\n| IKMK | year | nominal | best our coin | reason |")
        md.append("|---|---|---|---|---|")
        for m in weak:
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| {m.get('ikmk_nominal','')[:25]} | `{m['our_coin_id']}` | "
                f"{m['match_reason']} |",
            )
    if unmatched:
        md.append("\n## No match — potential new entries or out-of-coverage\n")
        md.append("\n| IKMK | year | nominal | ruler | weight | refs |")
        md.append("|---|---|---|---|---|---|")
        for m in unmatched:
            r = m.get("ikmk_refs", {})
            ref_str = " ".join(
                f"{c}:{v[0]['norm']}"
                for c, v in r.items() if v
            ) or "—"
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| {m.get('ikmk_nominal','')[:20]} "
                f"| {m.get('ikmk_ruler','')[:35]} "
                f"| {m.get('ikmk_weight','')} | {ref_str[:60]} |",
            )

    out_md = CACHE / f"_match_{loc_id}.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(
        f"  → strict={len(strict)} fuzzy={len(fuzzy)} "
        f"new_lange={len(new_var)} ({len(lange_groups)} unique) "
        f"weak={len(weak)} no_match={len(unmatched)}",
    )
    return out[loc_id]["totals"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "locations", nargs="*",
        help="Location IDs to match (default: all mapped in index)",
    )
    args = ap.parse_args()

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    by_loc = index["by_project_location"]
    locations = args.locations or sorted(by_loc.keys())
    summaries = {}
    for loc in locations:
        s = match_one_location(loc, index)
        if s is not None:
            summaries[loc] = s

    if summaries:
        print("\n=== Coverage summary ===")
        cols = ["records", "strict", "fuzzy", "new_lange (uniq)", "weak", "no_match"]
        print(f"  {'location':25s} " + " ".join(f"{c:>15s}" for c in cols))
        for loc, t in summaries.items():
            print(
                f"  {loc:25s} "
                f"{t['ikmk_records']:>15d} "
                f"{t['strict_match']:>15d} "
                f"{t['fuzzy_match']:>15d} "
                f"{t['new_lange_variant']:>10d} ({t['unique_new_lange_numbers']:>2d}) "
                f"{t['weak_candidate']:>15d} "
                f"{t['no_match']:>15d}",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
