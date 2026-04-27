#!/usr/bin/env python3
"""Add ~30 new Gottorp Duchy coins to schleswig.yml from Numista metadata.

Reads scripts/new_coins_meta.json and produces YAML coin entries appended
to data/locations/schleswig.yml. Each entry gets:
- A stable id derived from KM# + ruler + year
- fuss = 9_25_thaler (with phase A or B based on year)
- fraction parsed from Numista's denomination
- kind from meta (kurant/scheide)
- catalog refs from Numista
- Concise note in 3 languages
- Numista source URL

Run once:
    .venv/bin/python scripts/add_new_coins.py
"""
from __future__ import annotations
import json, pathlib, re
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)

META = pathlib.Path("scripts/new_coins_meta.json")
YML = pathlib.Path("data/locations/schleswig.yml")

REF_FIELD = {"KM#": "km", "Fr#": "fr", "Lange#": "lange", "Hede#": "hede",
             "Sieg#": "sieg", "Schou#": "schou", "Bruun#": "bruun_lot", "Dav#": "dav"}

RULER_NORMALIZE = {
    "John Adolphus": "Johann Adolf von Gottorp",
    "Frederick III": "Frederik III. von Gottorp",
    "Christian Albert": "Christian Albrecht von Gottorp",
    "Charles Frederick": "Karl Friedrich von Gottorp",
    "Karl Peter Ulrich": "Karl Peter Ulrich von Gottorp (späterer Peter III. v. Russland)",
    "Christian IV": "Christian IV. (Kgr. Dänemark, Glückstadt)",
    "Christian V": "Christian V. (Kgr. Dänemark, Glückstadt)",
    "Christian VII": "Christian VII. (Kgr. Dänemark)",
    "Frederik III": "Frederik III. (Kgr. Dänemark, Glückstadt)",
    "Frederik VI": "Frederik VI. (Kgr. Dänemark)",
    "Otto IV": "Otto IV. von Schaumburg-Pinneberg",
    "Adolphus XIV": "Adolph XIV. von Schaumburg-Pinneberg",
    "Ernest": "Ernst von Schaumburg-Pinneberg",
    "Justus Herman": "Just Herman von Schaumburg-Pinneberg",
    "Otto V": "Otto V. von Schaumburg-Pinneberg",
    "John Adolphus I": "Johann Adolph I. von Holstein-Norburg-Plön",
    "Frederick Charles": "Friedrich Karl von Holstein-Plön",
    "John": "Johann (Hans d. J.) von Schleswig-Holstein-Sonderburg",
    "Alexander": "Alexander von Schleswig-Holstein-Sonderburg",
}

RULER_SLUG = {
    "John Adolphus": "ja",
    "Frederick III": "fr-iii",
    "Frederik III": "fr-iii-dk",
    "Christian Albert": "chr-a",
    "Charles Frederick": "karl-fr",
    "Karl Peter Ulrich": "kpu",
    "Christian IV": "chr-iv",
    "Christian V": "chr-v",
    "Christian VII": "chr-vii",
    "Frederik VI": "fr-vi",
    "Otto IV": "otto-iv",
    "Adolphus XIV": "adolph-xiv",
    "Ernest": "ernst",
    "Justus Herman": "just-herman",
    "Otto V": "otto-v",
    "John Adolphus I": "ja-i-plon",
    "Frederick Charles": "fr-karl-plon",
    "John": "hans-jr-sonderb",
    "Alexander": "alex-sonderb",
}

RULER_UK = {
    "John Adolphus": "Йоганн Адольф (Гольштейн-Ґотторп)",
    "Frederick III": "Фредерік III (Гольштейн-Ґотторп)",
    "Frederik III": "Фредерік III (король Данії, Глюкштадт)",
    "Christian Albert": "Крістіан Альбрехт (Гольштейн-Ґотторп)",
    "Charles Frederick": "Карл Фрідріх (Гольштейн-Ґотторп)",
    "Karl Peter Ulrich": "Карл Петер Ульріх (Гольштейн-Ґотторп; пізніше Петро III)",
    "Christian IV": "Кристіан IV (король Данії, Глюкштадт)",
    "Christian V": "Кристіан V (король Данії, Глюкштадт)",
    "Christian VII": "Кристіан VII (король Данії)",
    "Frederik VI": "Фредерік VI (король Данії)",
    "Otto IV": "Отто IV Шаумбург-Піннеберг",
    "Adolphus XIV": "Адольф XIV Шаумбург-Піннеберг",
    "Ernest": "Ернст Шаумбург-Піннеберг",
    "Justus Herman": "Юст Герман Шаумбург-Піннеберг",
    "Otto V": "Отто V Шаумбург-Піннеберг",
    "John Adolphus I": "Йоганн Адольф I (Гольштейн-Норбург-Плен)",
    "Frederick Charles": "Фрідріх Карл (Гольштейн-Плен)",
    "John": "Йоганн (Ганс Молодший) Гольштейн-Зондербург",
    "Alexander": "Александр Гольштейн-Зондербург",
}

RULER_EN = {
    "John Adolphus": "John Adolphus, Duke of Schleswig-Holstein-Gottorp",
    "Frederick III": "Frederick III, Duke of Schleswig-Holstein-Gottorp",
    "Frederik III": "Frederik III of Denmark (Glückstadt mint)",
    "Christian Albert": "Christian Albert, Duke of Schleswig-Holstein-Gottorp",
    "Charles Frederick": "Charles Frederick, Duke of Schleswig-Holstein-Gottorp",
    "Karl Peter Ulrich": "Karl Peter Ulrich (later Peter III of Russia)",
    "Christian IV": "Christian IV of Denmark (Glückstadt mint)",
    "Christian V": "Christian V of Denmark (Glückstadt mint)",
    "Christian VII": "Christian VII of Denmark",
    "Frederik VI": "Frederik VI of Denmark",
    "Otto IV": "Otto IV, Count of Schaumburg-Pinneberg",
    "Adolphus XIV": "Adolph XIV, Count of Schaumburg-Pinneberg",
    "Ernest": "Ernst, Count of Schaumburg-Pinneberg",
    "Justus Herman": "Just Herman, Count of Schaumburg-Pinneberg",
    "Otto V": "Otto V, Count of Schaumburg-Pinneberg",
    "John Adolphus I": "Johann Adolph I, Duke of Holstein-Norburg-Plön",
    "Frederick Charles": "Friedrich Karl, Duke of Holstein-Plön",
    "John": "Johann (Hans the Younger), Duke of Schleswig-Holstein-Sonderburg",
    "Alexander": "Alexander, Duke of Schleswig-Holstein-Sonderburg",
}


def parse_fineness(c: str):
    """'Silver (.812)' → 0.812; 'Silver' → None; 'Billon' → None; 'Copper' → 0 sentinel."""
    m = re.search(r"\.(\d{3})", c or "")
    if m:
        return float("0." + m.group(1))
    return None


def make_id(km: str, ruler: str, year_first: int) -> str:
    """e.g. 'km-118-chr-a-1673'"""
    km_slug = re.sub(r"[^a-z0-9]+", "-", (km or "x").lower()).strip("-")
    rs = RULER_SLUG.get(ruler, "x")
    return f"km-{km_slug}-{rs}-{year_first}"


def build_catalog(refs: list[str], extra_km_from_id: str | None = None):
    cat: dict = {}
    if extra_km_from_id:
        cat["km"] = extra_km_from_id
    for r in refs or []:
        parts = r.split(" ", 1)
        if len(parts) != 2: continue
        prefix = parts[0] if parts[0].endswith("#") else parts[0] + "#"
        field = REF_FIELD.get(prefix)
        if not field: continue
        cat.setdefault(field, parts[1])
    return cat


def make_note(meta: dict, ruler: str) -> dict:
    """Concise 3-language note from Numista metadata."""
    nominal = meta["v"]
    yr = meta["y"]
    km_str = next((r.split(" ",1)[1] for r in (meta.get("refs") or []) if r.startswith("KM#")), None)
    src = f"Numista N#{meta_id_from_pid(meta)}"
    km_part = f" KM# {km_str}" if km_str else ""
    return {
        "de": f"{ruler}, {yr}: {nominal}.{km_part} · Quelle: {src}",
        "en": f"{ruler}, {yr}: {nominal}.{km_part} · Source: {src}",
        "uk": f"{RULER_UK.get(ruler, ruler)}, {yr}: {nominal}.{km_part} · Джерело: {src}",
    }


def meta_id_from_pid(meta: dict) -> str:
    return meta.get("_pid", "?")


def main():
    raw = json.loads(META.read_text())
    pieces = raw["pieces"]
    data = yaml.load(YML.read_text())

    existing_ids = {coin.get("id") for coin in (data.get("coins") or [])}

    new_entries = []
    for pid, meta in pieces.items():
        meta["_pid"] = pid
        ruler = meta["ru"]
        km_match = next((r.split(" ",1)[1] for r in (meta.get("refs") or []) if r.startswith("KM#")), None)
        cid = make_id(km_match or pid, ruler, meta["yf"])
        # Avoid id clash: if already exists, append piece-id
        suffix = ""
        n = 1
        while (cid + suffix) in existing_ids:
            suffix = f"-v{n}"
            n += 1
        cid = cid + suffix
        existing_ids.add(cid)

        c_text = meta.get("c") or ""
        if "Copper" in c_text or "Bronze" in c_text or "Brass" in c_text:
            metal = "copper" if "Copper" in c_text else ("bronze" if "Bronze" in c_text else "brass")
            fineness = None
        elif "Billon" in c_text:
            metal = "billon"
            fineness = parse_fineness(c_text)
        else:
            metal = "silver"
            fineness = parse_fineness(c_text)

        entry = CommentedMap()
        entry["id"] = cid
        entry["fuss"] = meta.get("fuss", "9_25_thaler")
        entry["phase"] = meta.get("phase", "A")
        entry["kind"] = meta.get("kind", "kurant")
        if meta.get("frac"):
            entry["fraction"] = meta["frac"]
        entry["nominal"] = meta["v"]
        entry["year_label"] = str(meta["y"])
        entry["year_first"] = meta["yf"]
        if meta.get("yt") and meta["yt"] != meta["yf"]:
            entry["year_last"] = meta["yt"]
        entry["ruler"] = RULER_NORMALIZE.get(ruler, ruler)
        cat = build_catalog(meta.get("refs"), extra_km_from_id=km_match)
        if cat:
            entry["catalog"] = cat
        entry["metal"] = metal
        if fineness is not None:
            entry["fineness"] = fineness
            entry["fineness_verified"] = False
        if meta.get("w"):
            entry["weight_rough_g"] = meta["w"]
        if meta.get("d"):
            entry["diameter_mm"] = meta["d"]
        if meta.get("entity"):
            entry["issuing_entity"] = meta["entity"]
        # Note
        nominal = meta["v"]
        yr = meta["y"]
        entry["note"] = {
            "de": f"{nominal} · {RULER_NORMALIZE.get(ruler, ruler)}, {yr} · Numista N#{pid}",
            "en": f"{nominal} · {RULER_EN.get(ruler, ruler)}, {yr} · Numista N#{pid}",
            "uk": f"{nominal} · {RULER_UK.get(ruler, ruler)}, {yr} · Numista N#{pid}",
        }
        entry["sources"] = [{
            "type": "numista",
            "url": f"https://en.numista.com/catalogue/pieces{pid}.html",
            "ref": "Numista"
        }]
        new_entries.append(entry)

    # Append all
    coins = data.get("coins") or []
    for e in new_entries:
        coins.append(e)
    data["coins"] = coins

    with open(YML, "w") as f:
        yaml.dump(data, f)

    print(f"Added {len(new_entries)} new coins:")
    for e in new_entries:
        print(f"  {e['id']:42s} ({e.get('catalog',{}).get('km','—')})")


if __name__ == "__main__":
    main()
