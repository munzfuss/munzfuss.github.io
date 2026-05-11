"""Apply the IKMK → schleswig_holstein.yml strict-enrichment batch.

This is the *first* enrichment pass: the user-resolved subset of the
strict matches produced by ``scripts/match_ikmk_schleswig_holstein.py``.
The matcher's auto-classification has been hand-corrected for the
Lange-65 conflict (a pre-existing data error in our YAML).

Per session 2026-05-08, the batch is:

* ``km-51-fr-iii-1664`` — IKMK 18206321 (re-routed from km-56; the
  Lange # 65 reference in IKMK is to *Lange I* 65 = Speciedaler 1664,
  identified by Davenport 3673; not the Dukat 1666 KM 56). Adds Hede
  148 + Aagaard 63 (T 11.1) to catalog.
* ``km-9-hans-jr-sonderb-1619`` — 7 IKMK specimens (Lange II 533a).
  Two die-variants of the legend; canonical = the longer form, with
  a one-liner note about the abbreviated variant.
* ``km-11-hans-jr-sonderb-1620`` — IKMK 18284714 (Lange II 542c).
  Standard merge.
* ``bruun-14681-christian-glb-1672`` — IKMK 18206117 (Lange II 737).
  Standard merge, only the reverse legend new.

Policy (matches the dry-run plan agreed with the user):

* ``inscription_obv`` / ``inscription_rev`` filled only when currently
  empty; never overwritten. ``*_verified: true`` set in same step.
* ``diameter_mm`` filled only when null/0; ``diameter_mm_verified: true``
  in same step.
* ``weight_rough_g`` always appended (§9a — never collapse), one
  ``{value, source}`` entry per IKMK specimen. Source string carries
  the IKMK Inv. number for traceability. ``weight_rough_verified``
  flipped ``false → true`` in same transaction.
* ``coin.sources[]`` extended with a museum-typed entry per IKMK
  record. URL points to the human-facing
  ``/object?id=<id>`` page (same as JSON-export endpoint minus the
  ``download=json_ext`` query). Idempotent: skip if URL already
  present.
* ``catalog.hede`` / ``catalog.others`` extended only via explicit
  per-coin override (km-51 in this batch).

Idempotent: re-running won't double-add sources or weights.
"""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import IKMK_CACHE as IKMK, PROJECT_ROOT as REPO  # noqa: E402

YML = REPO / "data" / "locations" / "schleswig_holstein.yml"

# ---------- The hand-resolved batch -----------------------------------

BATCH: list[dict] = [
    {
        "our_coin": "km-51-fr-iii-1664",
        "ikmk_ids": ["18206321"],
        "extra_catalog": {"hede": "148"},
        "extra_others": ["Aagaard# 63 (T 11.1)"],
        "match_basis": "Davenport 3673 cross-cited (IKMK + km-51); IKMK Lange-65 ignored — see comment",
    },
    {
        "our_coin": "km-9-hans-jr-sonderb-1619",
        "ikmk_ids": ["18284402", "18284403", "18284692", "18284693",
                     "18284694", "18284695", "18284696"],
        # Use the longer die-variant as canonical; record the abbreviated
        # variant in note (i18n).
        "obv_canonical": "IOHA D G - HAE NOR",
        "rev_canonical": "DVX SL HOL CO OL ET D 619",
        "stempel_note_de": (
            "Stempelvariante mit verkürzter Legende belegt: "
            "«IO D G - H NO / DVX SL HOL CO O E D 619» (IKMK Berlin)."
        ),
        "stempel_note_en": (
            "Variant die with abbreviated legend documented: "
            "«IO D G - H NO / DVX SL HOL CO O E D 619» (IKMK Berlin)."
        ),
        "stempel_note_uk": (
            "Задокументований штемпель зі скороченою легендою: "
            "«IO D G - H NO / DVX SL HOL CO O E D 619» (IKMK Berlin)."
        ),
        "match_basis": "strict by Lange II 533a (matcher)",
    },
    {
        "our_coin": "km-11-hans-jr-sonderb-1620",
        "ikmk_ids": ["18284714"],
        "match_basis": "strict by Lange II 542c (matcher); user-confirmed merge despite weight gap",
    },
    {
        "our_coin": "bruun-14681-christian-glb-1672",
        "ikmk_ids": ["18206117"],
        "match_basis": "strict by Lange II 737 (matcher)",
    },
]


# ---------- Helpers ---------------------------------------------------


def parse_weight(s: str | None) -> float | None:
    if not s:
        return None
    m = re.match(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_diameter(s: str | None) -> float | None:
    if not s:
        return None
    m = re.match(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def url_for(ikmk_id: str) -> str:
    return f"https://ikmk.smb.museum/object?id={ikmk_id}"


def load_ikmk(ikmk_id: str) -> dict:
    return json.loads((IKMK / f"{ikmk_id}.json").read_text(encoding="utf-8"))


def existing_ikmk_urls(coin: dict) -> set[str]:
    found = set()
    for s in coin.get("sources") or []:
        if isinstance(s, dict):
            url = s.get("url") or ""
            if "ikmk.smb.museum/object" in url:
                found.add(url)
    return found


def existing_ikmk_weight_sources(coin: dict) -> set[str]:
    """Return the set of IKMK Inv. numbers already present in
    weight_rough_g[].source values."""
    out = set()
    w = coin.get("weight_rough_g")
    if isinstance(w, list):
        for entry in w:
            if isinstance(entry, dict):
                src = str(entry.get("source") or "")
                m = re.search(r"IKMK Berlin,\s*Inv\.\s*(\d+)", src)
                if m:
                    out.add(m.group(1))
    return out


def ensure_weight_list(coin: dict) -> list:
    """Convert scalar weight to list shape if needed; return the list."""
    w = coin.get("weight_rough_g")
    if w is None:
        coin["weight_rough_g"] = []
        return coin["weight_rough_g"]
    if isinstance(w, list):
        return w
    if isinstance(w, (int, float)):
        # Convert scalar to list. Source unknown — tag the legacy value
        # explicitly so the provenance gap is visible. The new list
        # entry has the original numeric preserved as-is.
        coin["weight_rough_g"] = [{"value": w, "source": "(unspecified — legacy scalar)"}]
        return coin["weight_rough_g"]
    raise TypeError(f"Unexpected weight_rough_g shape: {type(w)}")


def i18n_get(d, key: str) -> str:
    if d is None:
        return ""
    if isinstance(d, dict):
        return str(d.get(key) or "")
    return ""


def i18n_set(coin: dict, field: str, lang: str, value: str) -> None:
    cur = coin.get(field)
    if cur is None:
        coin[field] = {"de": "", "en": "", "uk": ""}
        cur = coin[field]
    cur[lang] = value


def append_note_paragraph(coin: dict, de: str, en: str, uk: str, marker: str) -> bool:
    """Append a note paragraph in all three languages if the marker is
    not already present in the de note. Returns True if appended."""
    note = coin.get("note")
    if not isinstance(note, dict):
        coin["note"] = {"de": "", "en": "", "uk": ""}
        note = coin["note"]
    if marker in (note.get("de") or ""):
        return False
    sep = "\n\n" if (note.get("de") or "").strip() else ""
    note["de"] = (note.get("de") or "") + sep + de
    note["en"] = (note.get("en") or "") + sep + en
    note["uk"] = (note.get("uk") or "") + sep + uk
    return True


# ---------- Per-coin enrichment ---------------------------------------


def enrich_coin(coin: dict, item: dict, ikmk_records: list[dict]) -> dict:
    """Apply the enrichment to one coin entry. Returns a summary of
    actions performed (what changed)."""
    actions: dict[str, int | str] = {
        "sources_added": 0,
        "weights_added": 0,
        "filled_obv": False,
        "filled_rev": False,
        "filled_diameter": False,
        "appended_note": False,
        "added_catalog_hede": False,
        "added_others": 0,
    }

    # ---- 1. Sources (one per IKMK record, idempotent by URL) ----
    have_urls = existing_ikmk_urls(coin)
    sources = coin.setdefault("sources", [])
    for rec in ikmk_records:
        url = url_for(str(rec["ikmk_mds_id"]))
        if url in have_urls:
            continue
        photographer = ((rec.get("avers") or {}).get("photographer") or {}).get("photographer_name")
        img_right = (rec.get("image_right") or {}).get("short") or "—"
        ref_str = f"IKMK Berlin, Inv. {rec['ikmk_mds_id']} (Münzkabinett der Staatlichen Museen zu Berlin)"
        note_parts = [f"Bild: {img_right}", "Text: CC BY-SA 4.0"]
        if photographer:
            note_parts.append(f"Aufnahme: {photographer}")
        sources.append({
            "type": "museum",
            "url": url,
            "ref": ref_str,
            "note": "; ".join(note_parts),
        })
        actions["sources_added"] += 1

    # ---- 2. inscription_obv / _rev ----
    cur_obv = (coin.get("inscription_obv") or "").strip()
    cur_rev = (coin.get("inscription_rev") or "").strip()
    obv_canonical = item.get("obv_canonical")
    rev_canonical = item.get("rev_canonical")
    if not obv_canonical:
        # Pull from first IKMK record if all specimens agree;
        # otherwise leave empty (defensive — caller should have set
        # obv_canonical explicitly when there are die-variants).
        legs = {(r.get("avers") or {}).get("leg_text", "").strip()
                for r in ikmk_records}
        legs.discard("")
        obv_canonical = legs.pop() if len(legs) == 1 else None
    if not rev_canonical:
        legs = {(r.get("revers") or {}).get("leg_text", "").strip()
                for r in ikmk_records}
        legs.discard("")
        rev_canonical = legs.pop() if len(legs) == 1 else None

    # Inscription fields don't have per-field _verified flags in the
    # schema (only mint/fineness/weight_rough/diameter_mm do). The
    # citation lives in coin.sources[] (the IKMK museum entry).
    if not cur_obv and obv_canonical:
        coin["inscription_obv"] = obv_canonical
        actions["filled_obv"] = True
    if not cur_rev and rev_canonical:
        coin["inscription_rev"] = rev_canonical
        actions["filled_rev"] = True

    # ---- 3. diameter ----
    cur_d = coin.get("diameter_mm")
    if cur_d in (None, 0):
        ds = sorted(d for d in (parse_diameter(r.get("diameter")) for r in ikmk_records) if d)
        if ds:
            coin["diameter_mm"] = ds[len(ds) // 2]  # median
            coin["diameter_mm_verified"] = True
            actions["filled_diameter"] = True

    # ---- 4. weight (multi-specimen append, §9a) ----
    have_inv = existing_ikmk_weight_sources(coin)
    wlist = ensure_weight_list(coin)
    for rec in ikmk_records:
        w = parse_weight(rec.get("weight"))
        inv = str(rec["ikmk_mds_id"])
        if not w or inv in have_inv:
            continue
        wlist.append({
            "value": w,
            "source": f"IKMK Berlin, Inv. {inv}",
        })
        actions["weights_added"] += 1
    if actions["weights_added"]:
        coin["weight_rough_verified"] = True

    # ---- 5. note paragraph (Stempel-variant) ----
    if all(item.get(k) for k in ("stempel_note_de", "stempel_note_en", "stempel_note_uk")):
        appended = append_note_paragraph(
            coin,
            item["stempel_note_de"], item["stempel_note_en"], item["stempel_note_uk"],
            marker="(IKMK Berlin).",
        )
        actions["appended_note"] = appended

    # ---- 6. extra catalog refs ----
    cat = coin.setdefault("catalog", {})
    extra_cat = item.get("extra_catalog") or {}
    for k, v in extra_cat.items():
        if not cat.get(k):
            cat[k] = v
            actions[f"added_catalog_{k}"] = True
    extra_others = item.get("extra_others") or []
    if extra_others:
        others = cat.setdefault("others", [])
        for ref in extra_others:
            if ref not in others:
                others.append(ref)
                actions["added_others"] += 1

    return actions


def main() -> int:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    with YML.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    coins = data["coins"]
    by_id = {c["id"]: c for c in coins}

    summary: list[tuple[str, dict]] = []
    for item in BATCH:
        cid = item["our_coin"]
        coin = by_id.get(cid)
        if coin is None:
            print(f"[!] coin {cid} not in YAML — skipped", file=sys.stderr)
            continue
        ikmk_records = [load_ikmk(nid) for nid in item["ikmk_ids"]]
        actions = enrich_coin(coin, item, ikmk_records)
        summary.append((cid, actions))

    with YML.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print("Enrichment summary:")
    for cid, a in summary:
        flags = ", ".join(f"{k}={v}" for k, v in a.items() if v)
        print(f"  {cid:42s}  {flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
