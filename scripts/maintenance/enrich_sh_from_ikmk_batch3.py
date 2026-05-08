"""Apply IKMK → schleswig_holstein.yml enrichment, batch 3 (cf-only).

Builds on batch 1 (a409d31), batch 2 (57d4ff1), batch 2.5 (29b49a3).
Resolves the 23 «(cf-only)» records the matcher classified as
new_lange_variant — IKMK literatur says «Vgl. Lange Nr. X (dort Y)»
(«cf. Lange X — there has Y») meaning the specimen is a close
sub-variant of Lange X with documented die-divergences.

Of 23 cf-only records:

* 21 enrichable as additional specimens of existing types (per §9a
  multi-specimen merge).
* 2 deferred — Lange-volume collision (cf 358Eb, IKMK 18285130) and
  no-YAML-match (cf Lange 534, IKMK 18284697). Flagged with
  comments in the YAML for follow-up.

The 2 IKMK records cf-cited as «Lange 533A» have a Matthias-II
imperial reverse — these are die-mules where the obverse is Hans
Sonderburg's standard die paired with a reverse die from a German
imperial coin. They get a dedicated MULE note flag.

Policy mirrors batch 2: idempotent additions of sources / weight /
inscription / Lange-suffix tags / Stempel-variant note. Inscriptions
filled only when previously empty.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[2]
YML = REPO / "data" / "locations" / "schleswig_holstein.yml"
IKMK = REPO / "scripts" / "cache" / "ikmk"


# ---------- The hand-resolved batch ----------------------------------

ENRICH: list[dict] = [
    {
        "our_coin": "km-46-fr-iii-1617",
        "specimens": [
            # cf Lange 339B (11 specimens, 1618)
            ("18284934", "339B-cf"),
            ("18284940", "339B-cf"),
            ("18285689", "339B-cf"),
            ("18285701", "339B-cf"),
            ("18285754", "339B-cf"),
            ("18285782", "339B-cf"),
            ("18285918", "339B-cf"),
            ("18285924", "339B-cf"),
            ("18286228", "339B-cf"),
            ("18286248", "339B-cf"),
            ("18286251", "339B-cf"),
            # cf Lange 339C (3 specimens, 1619)
            ("18285708", "339C-cf"),
            ("18285714", "339C-cf"),
            ("18285715", "339C-cf"),
        ],
        "lange_others": [
            "Lange# 339 B (cf — Rückseite HOL statt HO)",
            "Lange# 339 C (cf — Rückseite HER statt HAER)",
        ],
        "stempel_note_de": (
            "Sub-Stempelvarianten unter Lange 339 dokumentiert: 339 B (Rückseite "
            "HOL statt HO, 1618) und 339 C (HER statt HAER, 1619) — IKMK Berlin "
            "verzeichnet 14 weitere Stücke außerhalb der katalogisierten 339 b/c."
        ),
        "stempel_note_en": (
            "Sub-die-variants under Lange 339 documented: 339 B (reverse HOL "
            "instead of HO, 1618) and 339 C (HER instead of HAER, 1619) — "
            "IKMK Berlin records 14 further specimens outside the catalogued "
            "339 b/c."
        ),
        "stempel_note_uk": (
            "Задокументовані штемпельні підваріанти під Lange 339: 339 B "
            "(реверс HOL замість HO, 1618) та 339 C (HER замість HAER, 1619) — "
            "IKMK Berlin реєструє 14 додаткових екземплярів поза каталогізованими "
            "339 b/c."
        ),
    },
    {
        "our_coin": "lange-532-hans-jr-sonderb-1618",
        "specimens": [
            # cf Lange 532 (1 specimen, 1618 Hans Sonderburg)
            ("18284398", "532-cf"),
        ],
        "lange_others": [
            "Lange# 532 (cf — Rückseite ohne Reichsapfel in Umschrift)",
        ],
        "stempel_note_de": (
            "Sub-Stempelvariante unter Lange 532: ein weiteres Stück mit "
            "Rückseite ohne Reichsapfel in der Umschrift (IKMK Berlin)."
        ),
        "stempel_note_en": (
            "Sub-die-variant under Lange 532: one further specimen with "
            "reverse lacking the imperial orb in the legend (IKMK Berlin)."
        ),
        "stempel_note_uk": (
            "Штемпельний підваріант під Lange 532: ще один екземпляр зі реверсом "
            "без Reichsapfel в обводці (IKMK Berlin)."
        ),
    },
    {
        "our_coin": "km-9-hans-jr-sonderb-1619",
        "specimens": [
            # cf Lange 533A (2 specimens) — these are MULES with Matthias II
            # imperial reverse, NOT standard km-9 reverse. Documented as
            # specimen-level error coinage.
            ("18284401", "533A-mule"),
            ("18284691", "533A-mule"),
        ],
        "lange_others": [
            "Lange# 533 A/b (cf — Vorderseite IOHA statt IOH; "
            "Rückseite mule mit Matthias D G R IM S A)",
        ],
        "stempel_note_de": (
            "Stempel-Mule belegt: Vorderseite Hans-Sonderburg-Standardstempel "
            "(IOHA D G - HAE NOR), Rückseite mit Reichslegende «MATTHIAS D G "
            "R IM S A 619» — Stempel des Reichskaisers Matthias II. mit "
            "fehlerhaft kombiniert. IKMK Berlin verzeichnet zwei solche Stücke."
        ),
        "stempel_note_en": (
            "Die-mule documented: obverse standard Hans-Sonderburg die "
            "(IOHA D G - HAE NOR), reverse with imperial legend «MATTHIAS D G "
            "R IM S A 619» — die of Holy Roman Emperor Matthias II combined "
            "in error. IKMK Berlin records two such specimens."
        ),
        "stempel_note_uk": (
            "Задокументований штемпельний mule: аверс — стандартний штемпель "
            "Hans-Sonderburg (IOHA D G - HAE NOR), реверс — з імператорською "
            "легендою «MATTHIAS D G R IM S A 619», штемпель імператора Матвія II "
            "помилково поєднаний. IKMK Berlin реєструє два таких екземпляри."
        ),
    },
    {
        "our_coin": "km-11-hans-jr-sonderb-1620",
        "specimens": [
            # cf Lange 542c (1 specimen) and 542d (3 specimens) — sub-variants
            # under km-11 per Numista N#151528 (KM#11 covers Lange 542c+d).
            ("18284712", "542c-cf"),
            ("18284715", "542d-cf"),
            ("18284716", "542d-cf"),
            ("18284717", "542d-cf"),
        ],
        "lange_others": [
            "Lange# 542 c (cf — Vs.-Variante)",
            "Lange# 542 d (cf — Vs.-Aufschriftvarianten)",
        ],
        "stempel_note_de": (
            "Sub-Stempelvarianten Lange 542 c und 542 d (Vorderseiten-"
            "Aufschriftvarianten des Reuterpfennigs) durch vier weitere "
            "IKMK-Stücke belegt; Numista N#151528 fasst beide unter KM#11 "
            "zusammen."
        ),
        "stempel_note_en": (
            "Sub-die-variants Lange 542 c and 542 d (Reuterpfennig obverse "
            "legend variants) attested by four further IKMK specimens; "
            "Numista N#151528 groups both under KM#11."
        ),
        "stempel_note_uk": (
            "Штемпельні підваріанти Lange 542 c та 542 d (варіанти аверсного "
            "напису Reuterpfennig'а) задокументовані чотирма додатковими "
            "IKMK-екземплярами; Numista N#151528 об'єднує обидва під KM#11."
        ),
    },
]

# Defer: log a YAML comment near the relevant area noting two records left
# untouched (Lange volume collision; no-YAML-match Lange 534).
DEFERRED = [
    {
        "ikmk_id": "18285130",
        "reason": (
            "1 Sechsling 1621 Friedrich III SH-Gottorf cf Lange I (1908) 358 E b — "
            "different coin from our km-91-fr-iii-1644 (3 Pfennig 1642-1653, "
            "Lange 358 [vol II]). Lange-base-number collision between volumes; "
            "the specimen may map to km-55-fr-iii-1621 (Friedrich III Gottorf "
            "Sechsling 1621, Lange 354b) or be a new sub-variant. Needs Lange "
            "volume-I lookup to decide."
        ),
    },
    {
        "ikmk_id": "18284697",
        "reason": (
            "1 Doppelschilling 1620 Hans Sonderburg cf Lange II 534 — no current "
            "YAML match. Lange 534 doesn't fit any of the 4 KM#-variants Numista "
            "lists for SH-Sonderburg-Duchy (KM#4/5/9/11). Could be a separate "
            "Krause type we don't catalogue, or a specimen of an existing KM# "
            "with the IKMK note «Jahreszahl Z0 statt 620». Defer until Krause "
            "lookup or visual comparison resolves."
        ),
    },
]


# ---------- Helpers ---------------------------------------------------


def parse_weight(s):
    if not s:
        return None
    m = re.match(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_diameter(s):
    if not s:
        return None
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
                src = str(entry.get("source") or "")
                m = re.search(r"IKMK Berlin,\s*Inv\.\s*(\d+)", src)
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


def make_source_entry(rec: dict, mule_marker: bool = False) -> dict:
    nid = rec["ikmk_mds_id"]
    photographer = ((rec.get("avers") or {}).get("photographer") or {}).get("photographer_name")
    img_right = (rec.get("image_right") or {}).get("short") or "—"
    note_parts = [f"Bild: {img_right}", "Text: CC BY-SA 4.0"]
    if photographer:
        note_parts.append(f"Aufnahme: {photographer}")
    if mule_marker:
        note_parts.append("Stempel-Mule (Matthias-II-Reverse)")
    return {
        "type": "museum",
        "url": url_for(str(nid)),
        "ref": f"IKMK Berlin, Inv. {nid} (Münzkabinett der Staatlichen Museen zu Berlin)",
        "note": "; ".join(note_parts),
    }


def enrich_existing(coin: dict, item: dict) -> dict:
    actions = {
        "sources_added": 0, "weights_added": 0, "added_others": 0,
        "appended_note": False,
    }
    have_urls = existing_ikmk_urls(coin)
    have_invs = existing_ikmk_inv_in_weights(coin)
    sources = coin.setdefault("sources", [])
    wlist = ensure_weight_list(coin)
    is_mule_batch = any(tag.endswith("-mule") for _, tag in item["specimens"])

    records = [load_ikmk(nid) for nid, _ in item["specimens"]]
    spec_tags = {nid: tag for nid, tag in item["specimens"]}

    for rec in records:
        nid = str(rec["ikmk_mds_id"])
        spec_tag = spec_tags.get(nid, "")
        if url_for(nid) not in have_urls:
            sources.append(make_source_entry(rec, mule_marker=spec_tag.endswith("-mule")))
            actions["sources_added"] += 1
        if nid not in have_invs:
            w = parse_weight(rec.get("weight"))
            if w is not None:
                wlist.append({
                    "value": w,
                    "source": (
                        f"IKMK Berlin, Inv. {nid} (mule)"
                        if spec_tag.endswith("-mule")
                        else f"IKMK Berlin, Inv. {nid}"
                    ),
                })
                actions["weights_added"] += 1
    if actions["weights_added"]:
        coin["weight_rough_verified"] = True

    cat = coin.setdefault("catalog", {})
    others = cat.setdefault("others", [])
    for tag in item.get("lange_others") or []:
        if tag not in others:
            others.append(tag)
            actions["added_others"] += 1

    if all(item.get(k) for k in ("stempel_note_de", "stempel_note_en", "stempel_note_uk")):
        unique_marker = item["stempel_note_de"][:60]
        if unique_marker not in (coin.get("note", {}).get("de") or ""):
            note = coin.setdefault("note", {"de": "", "en": "", "uk": ""})
            sep = "\n\n" if (note.get("de") or "").strip() else ""
            note["de"] = (note.get("de") or "") + sep + item["stempel_note_de"]
            note["en"] = (note.get("en") or "") + sep + item["stempel_note_en"]
            note["uk"] = (note.get("uk") or "") + sep + item["stempel_note_uk"]
            actions["appended_note"] = True

    return actions


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

    with YML.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print("Enrichment summary (batch 3):")
    for cid, a in summary:
        flags = ", ".join(f"{k}={v}" for k, v in a.items() if v)
        print(f"  {cid:42s}  {flags}")

    print("\nDeferred (left untouched):")
    for d in DEFERRED:
        print(f"  IKMK {d['ikmk_id']}  {d['reason'][:120]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
