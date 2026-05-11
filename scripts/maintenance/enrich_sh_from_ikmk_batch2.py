"""Apply the IKMK → schleswig_holstein.yml enrichment, batch 2.

Builds on batch 1 (commit a409d31). Resolves the 11 unique
new-Lange-variant candidates from
``scripts/cache/ikmk/_match_schleswig_holstein.json`` per the user-
visual disambiguation pass (session 2026-05-08):

* Lange 535a, 535b   → existing km-5-hans-jr-sonderb-1618 (Lange 535)
* Lange 536a, 536b   → existing km-5-hans-jr-sonderb-1618 (visual confirmed)
* Lange 533           → existing km-9-hans-jr-sonderb-1619 (Lange 533a base form)
* Lange 339b, 339c    → existing km-46-fr-iii-1617 (Doppelschilling 1617-1619)
* Lange 34e           → existing km-15-chr-iv-1623 (1 Speciedaler 1623)
* Lange 532, 532b     → **new YAML entry** (visual: similar obverse to
                         KM#5 but different reverse — separate Krause
                         classification pending)

For all existing-coin enrichments the policy mirrors batch 1:
inscriptions filled only when previously empty, diameter when null,
weight_rough_g always appended (§9a multi-specimen merge),
weight_rough_verified flipped in same transaction, sources[] gains
one museum entry per IKMK record, ``catalog.others`` extended with
the encountered Lange-letter-suffix tags. Idempotent.

For the new Lange-532 entry: created from scratch with the IKMK
specimen data as the only weight/inscription provenance,
``verified: false``, KM unknown, primary catalog ref = Lange 532.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import IKMK_CACHE as IKMK, PROJECT_ROOT as REPO  # noqa: E402

YML = REPO / "data" / "locations" / "schleswig_holstein.yml"


# ---------- The hand-resolved batch ----------------------------------

# (target_coin_id, list-of-(ikmk_id, lange-tag), notes)
ENRICH: list[dict] = [
    {
        "our_coin": "km-5-hans-jr-sonderb-1618",
        "specimens": [
            ("18284698", "535a"),
            ("18284699", "535b"),
            ("18284700", "535b"),
            ("18284701", "535b"),
            ("18284707", "536a"),
            ("18284709", "536a"),
            ("18284710", "536a"),
            ("18284702", "536b"),
            ("18284703", "536b"),
            ("18284704", "536b"),
            ("18284705", "536b"),
            ("18284706", "536b"),
            ("18284708", "536b"),
        ],
        "lange_others": ["Lange# 535a", "Lange# 535b",
                         "Lange# 536a", "Lange# 536b"],
        "stempel_note_de": (
            "Stempelvarianten unter dem KM#5-Typ dokumentiert: "
            "Lange 535a/535b (1618), 536a/536b (1619) — IKMK Berlin."
        ),
        "stempel_note_en": (
            "Die-variants under the KM#5 type documented: "
            "Lange 535a/535b (1618), 536a/536b (1619) — IKMK Berlin."
        ),
        "stempel_note_uk": (
            "Задокументовані штемпелі під типом KM#5: "
            "Lange 535a/535b (1618), 536a/536b (1619) — IKMK Berlin."
        ),
    },
    {
        "our_coin": "km-9-hans-jr-sonderb-1619",
        "specimens": [
            ("18284399", "533"),
            ("18284400", "533"),
            ("18284404", "533"),
        ],
        "lange_others": ["Lange# 533"],
        "stempel_note_de": (
            "Stempelvariante mit Lange-Basisnummer 533 (ohne Suffix) "
            "neben der katalogisierten 533a belegt — IKMK Berlin."
        ),
        "stempel_note_en": (
            "Die-variant with Lange base number 533 (no suffix) "
            "documented alongside the catalogued 533a — IKMK Berlin."
        ),
        "stempel_note_uk": (
            "Задокументований штемпель з базовим Lange-номером 533 "
            "(без суфікса) поряд із каталогізованим 533a — IKMK Berlin."
        ),
    },
    {
        "our_coin": "km-46-fr-iii-1617",
        "specimens": [
            ("18284934", "339b"),
            ("18284940", "339b"),
            ("18285708", "339c"),
            ("18285714", "339c"),
            ("18285715", "339c"),
            ("18285716", "339c"),
            ("18285717", "339c"),
            ("18285718", "339c"),
            ("18285719", "339c"),
            ("18285754", "339c"),
        ],
        "extra_catalog": {"lange": "339"},
        "lange_others": ["Lange# 339b", "Lange# 339c"],
        "stempel_note_de": (
            "Stempelvarianten Lange 339b (1618) und 339c (1619) "
            "unter dem KM#46-Typ dokumentiert — IKMK Berlin."
        ),
        "stempel_note_en": (
            "Die-variants Lange 339b (1618) and 339c (1619) "
            "documented under the KM#46 type — IKMK Berlin."
        ),
        "stempel_note_uk": (
            "Задокументовані штемпелі Lange 339b (1618) та 339c (1619) "
            "під типом KM#46 — IKMK Berlin."
        ),
    },
    {
        "our_coin": "km-15-chr-iv-1623",
        "specimens": [
            ("18202375", "34e"),
        ],
        "extra_catalog": {"lange": "34"},
        "lange_others": ["Lange# 34e", "Lange# 35"],
        "stempel_note_de": (
            "Lange-Klassifikation des KM#15-Typs: Basis Lange 34 "
            "(plus Stempelvarianten 34e und 35) — Numista N#142977, "
            "IKMK Berlin."
        ),
        "stempel_note_en": (
            "Lange classification of the KM#15 type: base Lange 34 "
            "(plus die-variants 34e and 35) — Numista N#142977, "
            "IKMK Berlin."
        ),
        "stempel_note_uk": (
            "Lange-класифікація типу KM#15: базовий Lange 34 "
            "(плюс штемпелі 34e та 35) — Numista N#142977, "
            "IKMK Berlin."
        ),
    },
]

# Specification for the NEW YAML entry (Lange 532 / 532b — separate type).
NEW_ENTRY = {
    "id": "lange-532-hans-jr-sonderb-1618",
    "specimens": [
        ("18284272", "532"),
        ("18284395", "532b"),
        ("18284396", "532b"),
        ("18284397", "532b"),
    ],
    "fields": {
        "fuss": "9_thaler",
        "phase": "A",
        "kind": "kurant",
        "nominal": "2 Schilling",
        "year_label": "1618",
        "year_first": 1618,
        "year_last": 1618,
        "ruler": "Johann (Hans d. J.) von Schleswig-Holstein-Sonderburg",
        "mint": None,
        "metal": "silver",
        "fineness": None,
        "fineness_verified": False,
        "issuing_entity": "sonderburg_duchy",
        "verified": False,
        "mint_verified": False,
    },
    "catalog": {
        "lange": "532",
        "others": ["Lange# 532b"],
    },
    # Canonical inscriptions: take the longer Lange-532b forms.
    "inscription_obv": "IOHAN D G HAERES NORWG",
    "inscription_rev": "D SCHL E HO C I OL E D 1618",
    "note": {
        "de": (
            "2 Schilling 1618 · Johann (Hans d. J.) von Schleswig-Holstein-"
            "Sonderburg · Lange 532 / 532b — gleicher Avers wie KM#5-Typ "
            "(Lange 535), aber abweichender Revers; separate Krause-"
            "Klassifikation steht aus. IKMK Berlin dokumentiert vier "
            "Stücke (1× Lange 532, 3× Lange 532b)."
        ),
        "en": (
            "2 Schilling 1618 · Johann (Hans the Younger) of "
            "Schleswig-Holstein-Sonderburg · Lange 532 / 532b — same "
            "obverse as the KM#5 type (Lange 535) but different reverse; "
            "separate Krause classification pending. IKMK Berlin "
            "documents four specimens (1× Lange 532, 3× Lange 532b)."
        ),
        "uk": (
            "2 Schilling 1618 · Йоганн (Ганс Молодший) "
            "Гольштейн-Зондербург · Lange 532 / 532b — той самий аверс, "
            "що в типу KM#5 (Lange 535), але інший реверс; окрема "
            "Krause-класифікація очікується. IKMK Berlin документує "
            "чотири екземпляри (1× Lange 532, 3× Lange 532b)."
        ),
    },
    "verification_note": {
        "de": (
            "Stempel-/Reverstyp-Variante des Hans-Sonderburg 2-Schilling "
            "1618; im Krause-Verzeichnis nicht separat klassifiziert. "
            "Per-Münze-Verifikation und KM-Zuordnung stehen aus."
        ),
        "en": (
            "Die / reverse-type variant of the Hans-Sonderburg 2-Schilling "
            "1618; not separately classified in Krause. Per-coin "
            "verification and KM assignment outstanding."
        ),
        "uk": (
            "Штемпельний / реверс-варіант 2-Schilling 1618 Hans-Sonderburg; "
            "у Krause-каталозі не виділений окремо. Покоінна верифікація "
            "та призначення KM очікуються."
        ),
    },
}


# ---------- Helpers ---------------------------------------------------


def parse_weight(s):
    if not s: return None
    m = re.match(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_diameter(s):
    if not s: return None
    m = re.match(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def url_for(nid: str) -> str:
    return f"https://ikmk.smb.museum/object?id={nid}"


def load_ikmk(nid: str) -> dict:
    return json.loads((IKMK / f"{nid}.json").read_text(encoding="utf-8"))


def existing_ikmk_urls(coin: dict) -> set[str]:
    out = set()
    for s in coin.get("sources") or []:
        if isinstance(s, dict):
            url = s.get("url") or ""
            if "ikmk.smb.museum/object" in url:
                out.add(url)
    return out


def existing_ikmk_inv_in_weights(coin: dict) -> set[str]:
    out = set()
    w = coin.get("weight_rough_g")
    if isinstance(w, list):
        for entry in w:
            if isinstance(entry, dict):
                m = re.search(r"IKMK Berlin,\s*Inv\.\s*(\d+)", str(entry.get("source") or ""))
                if m:
                    out.add(m.group(1))
    return out


def ensure_weight_list(coin: dict) -> list:
    w = coin.get("weight_rough_g")
    if w is None:
        coin["weight_rough_g"] = []
        return coin["weight_rough_g"]
    if isinstance(w, list):
        return w
    if isinstance(w, (int, float)):
        coin["weight_rough_g"] = [{"value": w, "source": "Numista"}]
        return coin["weight_rough_g"]
    raise TypeError(f"Unexpected weight_rough_g shape: {type(w)}")


def append_note_paragraph(coin: dict, de: str, en: str, uk: str, marker: str) -> bool:
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


# ---------- Per-coin enrichment --------------------------------------


def make_source_entry(rec: dict) -> dict:
    nid = rec["ikmk_mds_id"]
    photographer = ((rec.get("avers") or {}).get("photographer") or {}).get("photographer_name")
    img_right = (rec.get("image_right") or {}).get("short") or "—"
    note_parts = [f"Bild: {img_right}", "Text: CC BY-SA 4.0"]
    if photographer:
        note_parts.append(f"Aufnahme: {photographer}")
    return {
        "type": "museum",
        "url": url_for(str(nid)),
        "ref": f"IKMK Berlin, Inv. {nid} (Münzkabinett der Staatlichen Museen zu Berlin)",
        "note": "; ".join(note_parts),
    }


def enrich_existing(coin: dict, item: dict) -> dict:
    actions = {
        "sources_added": 0, "weights_added": 0,
        "filled_obv": False, "filled_rev": False, "filled_diameter": False,
        "appended_note": False, "added_others": 0,
        "added_catalog_lange": False,
    }

    have_urls = existing_ikmk_urls(coin)
    have_invs = existing_ikmk_inv_in_weights(coin)
    sources = coin.setdefault("sources", [])
    wlist = ensure_weight_list(coin)

    # Load all specimens
    records = []
    for nid, _lange in item["specimens"]:
        records.append(load_ikmk(nid))

    # 1. sources + weights — append per-specimen
    for rec in records:
        nid = str(rec["ikmk_mds_id"])
        if url_for(nid) not in have_urls:
            sources.append(make_source_entry(rec))
            actions["sources_added"] += 1
        if nid not in have_invs:
            w = parse_weight(rec.get("weight"))
            if w is not None:
                wlist.append({
                    "value": w,
                    "source": f"IKMK Berlin, Inv. {nid}",
                })
                actions["weights_added"] += 1
    if actions["weights_added"]:
        coin["weight_rough_verified"] = True

    # 2. inscriptions / diameter (only if empty) — use most-frequent variant
    cur_obv = (coin.get("inscription_obv") or "").strip()
    cur_rev = (coin.get("inscription_rev") or "").strip()
    obv_legs = [(rec.get("avers") or {}).get("leg_text", "").strip() for rec in records]
    rev_legs = [(rec.get("revers") or {}).get("leg_text", "").strip() for rec in records]
    if not cur_obv:
        from collections import Counter
        most = Counter(s for s in obv_legs if s).most_common(1)
        if most:
            coin["inscription_obv"] = most[0][0]
            actions["filled_obv"] = True
    if not cur_rev:
        from collections import Counter
        most = Counter(s for s in rev_legs if s).most_common(1)
        if most:
            coin["inscription_rev"] = most[0][0]
            actions["filled_rev"] = True

    if coin.get("diameter_mm") in (None, 0):
        ds = sorted(d for d in (parse_diameter(rec.get("diameter")) for rec in records) if d)
        if ds:
            coin["diameter_mm"] = ds[len(ds) // 2]
            coin["diameter_mm_verified"] = True
            actions["filled_diameter"] = True

    # 3. catalog.lange (if specified by extra_catalog)
    cat = coin.setdefault("catalog", {})
    extra_cat = item.get("extra_catalog") or {}
    for k, v in extra_cat.items():
        if not cat.get(k):
            cat[k] = v
            actions[f"added_catalog_{k}"] = True
    # 4. catalog.others — Lange-suffix tags
    others = cat.setdefault("others", [])
    for tag in item.get("lange_others") or []:
        if tag not in others:
            others.append(tag)
            actions["added_others"] += 1

    # 5. Stempel note paragraph (idempotent via marker)
    marker = "(IKMK Berlin)."
    if all(item.get(k) for k in ("stempel_note_de", "stempel_note_en", "stempel_note_uk")):
        # Use a tag that's specific to THIS item's Lange variants — so it
        # doesn't conflict with the batch-1 Stempel-note already on km-9.
        unique_marker = item["stempel_note_de"][:60]
        appended = False
        if unique_marker not in (coin.get("note", {}).get("de") or ""):
            note = coin.setdefault("note", {"de": "", "en": "", "uk": ""})
            sep = "\n\n" if (note.get("de") or "").strip() else ""
            note["de"] = (note.get("de") or "") + sep + item["stempel_note_de"]
            note["en"] = (note.get("en") or "") + sep + item["stempel_note_en"]
            note["uk"] = (note.get("uk") or "") + sep + item["stempel_note_uk"]
            appended = True
        actions["appended_note"] = appended

    return actions


def build_new_entry(spec: dict) -> dict:
    """Build the new YAML entry for Lange 532/532b."""
    records = [load_ikmk(nid) for nid, _ in spec["specimens"]]
    coin: dict = dict(spec["fields"])
    coin["id"] = spec["id"]

    # catalog
    coin["catalog"] = dict(spec["catalog"])

    # weight_rough_g — list per-specimen
    coin["weight_rough_g"] = []
    for rec in records:
        nid = str(rec["ikmk_mds_id"])
        w = parse_weight(rec.get("weight"))
        if w is not None:
            coin["weight_rough_g"].append({
                "value": w,
                "source": f"IKMK Berlin, Inv. {nid}",
            })
    coin["weight_rough_verified"] = True

    # diameter from median
    ds = sorted(d for d in (parse_diameter(rec.get("diameter")) for rec in records) if d)
    if ds:
        coin["diameter_mm"] = ds[len(ds) // 2]
        coin["diameter_mm_verified"] = True

    # inscriptions — explicit
    coin["inscription_obv"] = spec["inscription_obv"]
    coin["inscription_rev"] = spec["inscription_rev"]

    # sources
    coin["sources"] = [make_source_entry(rec) for rec in records]
    coin["note"] = spec["note"]
    coin["verification_note"] = spec["verification_note"]
    return coin


def find_insertion_index(coins: list, new_id: str) -> int:
    """Insert near the existing Hans-Sonderburg entries; specifically
    right after km-5-hans-jr-sonderb-1618 to keep related types adjacent."""
    for i, c in enumerate(coins):
        if c.get("id") == "km-5-hans-jr-sonderb-1618":
            return i + 1
    return len(coins)


# ---------- Driver ---------------------------------------------------


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
    for item in ENRICH:
        cid = item["our_coin"]
        coin = by_id.get(cid)
        if coin is None:
            print(f"[!] coin {cid} not in YAML — skipped", file=sys.stderr)
            continue
        actions = enrich_existing(coin, item)
        summary.append((cid, actions))

    # Add new Lange-532 entry if not present
    if NEW_ENTRY["id"] not in by_id:
        new_coin = build_new_entry(NEW_ENTRY)
        idx = find_insertion_index(coins, NEW_ENTRY["id"])
        coins.insert(idx, new_coin)
        summary.append((NEW_ENTRY["id"], {"created": True,
                                           "specimens": len(NEW_ENTRY["specimens"])}))
    else:
        summary.append((NEW_ENTRY["id"], {"already_present": True}))

    with YML.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print("Enrichment summary (batch 2):")
    for cid, a in summary:
        flags = ", ".join(f"{k}={v}" for k, v in a.items() if v)
        print(f"  {cid:42s}  {flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
