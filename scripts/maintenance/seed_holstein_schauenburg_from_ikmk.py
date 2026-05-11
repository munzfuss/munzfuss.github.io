"""Seed `data/locations/holstein_schauenburg.yml` from the IKMK cache.

Builds the location file (and its references sidecar) for the
Schauenburg county / county-of-Holstein-Schauenburg dynasty (1567-1640
in our project window — IKMK coverage is concentrated 1616-1622, the
Ernst III phase). The file is created as a Bruun-style stub: every
coin gets ``fuss: seed_unsorted`` and ``verified: false`` until per-
coin classification + mint-city research moves entries into proper
Müntzfüße.

Why a separate location: the Schauenburg dynasty ruled two
geographically disjunct territories simultaneously:

* **Grafschaft Pinneberg** (county exclave; Kreis Pinneberg in modern
  Schleswig-Holstein) — within our SH project's territorial scope.
* **Schaumburg proper** (capitals Stadthagen / Bückeburg; modern
  Niedersachsen) — outside our SH territorial scope.

IKMK groups all 104 records under the dynastic title
«Holstein-Schauenburg» without exposing the mint city, so the
Pinneberg-vs-Stadthagen split cannot be done automatically. Per
session 2026-05-08 analysis, ~50 % of records (Doppelschilling /
Fürstengroschen / Taler) fit our 9-Taler-Fuß rough-weight expectation
while ~50 % (1/24 Taler Kipper-debased / Arendschilling /
non-Reichsfuß denominations) do not. Without mint-city
disambiguation, a clean assignment to either SH (Pinneberg) or future
Schaumburg-proper isn't possible — they live in this stub until
manual research resolves them.

Run once to seed; idempotent on re-run (writes deterministically).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from ruamel.yaml import YAML

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import IKMK_CACHE, PROJECT_ROOT as REPO  # noqa: E402

INDEX = IKMK_CACHE / "_index_by_issuer.json"
LOC = REPO / "data" / "locations" / "holstein_schauenburg.yml"
REF = REPO / "data" / "locations" / "holstein_schauenburg-references.yml"

# IKMK material name → our schema enum (silver / gold / billon / copper).
METAL_MAP = {
    "Silver": "silver",
    "Gold": "gold",
    "Billon": "billon",
    "Copper": "copper",
    "Bronze": "copper",  # bronze is a copper alloy; closest in our enum
}

# Heuristic: kind = scheide for fractional-Pfennig denominations,
# kurant for Taler / Doppelschilling / Fürstengroschen / Halbtaler.
SCHEIDE_PATTERNS = re.compile(r"\bPfennig\b|\bGroschen\b|1/24 Taler|1/48 Taler", re.IGNORECASE)


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


# ---------- Catalogue-ref extraction from IKMK literatur -------------

# Lange (vol I 1908 SH, vol II 1912 Sonderburg/Gottorf) — used for some
# Schauenburg cross-references.
RE_LANGE = re.compile(
    r"(?P<cf>Vgl\.\s+)?Chr\.?\s*Lange'?s\s*,?\s*Sammlung[^()]*\((?P<year>1908|1912)\)"
    r"[\s\S]*?Nr\.?\s*(?P<num>\d+)\s*(?P<q>[A-Za-z](?:\.\d+)?)?",
    re.IGNORECASE,
)
# Davenport (German Secular Talers / European Crowns)
RE_DAV = re.compile(
    r"Davenport[\s\S]*?Nr\.?\s*(?P<num>\d+)(?P<q>[A-Za-z]?)\b",
    re.IGNORECASE,
)
# Weinmeister (the canonical Schauenburg catalogue, ZfN 26 1908)
RE_WEIN = re.compile(
    r"Weinmeister[\s\S]*?Nr\.?\s*(?P<num>\d+)\s*(?P<q>[A-Za-z](?:\.\d+)?)?",
    re.IGNORECASE,
)


def extract_refs(literatur: str) -> dict:
    refs = {}
    for m in RE_LANGE.finditer(literatur):
        if m.group("cf"):
            continue
        refs.setdefault("lange", []).append(
            f"{m.group('num')}{(m.group('q') or '').strip().lower()}",
        )
    for m in RE_DAV.finditer(literatur):
        refs.setdefault("dav", []).append(
            f"{m.group('num')}{(m.group('q') or '').strip()}",
        )
    for m in RE_WEIN.finditer(literatur):
        refs.setdefault("weinmeister", []).append(
            f"{m.group('num')}{(m.group('q') or '').strip().lower()}",
        )
    return refs


def kind_for_nominal(nominal: str) -> str:
    if SCHEIDE_PATTERNS.search(nominal):
        return "scheide"
    return "kurant"


def build_coin_entry(rec: dict) -> dict:
    nid = rec["ikmk_mds_id"]
    nominal_full = (rec.get("nominal") or {}).get("nominal_de", "") or ""
    nominal_short = nominal_full.split(" (")[0].strip() or "Münze"
    year_start = rec.get("year_start")
    year_end = rec.get("year_end") or year_start
    try:
        ys = int(year_start) if year_start else None
        ye = int(year_end) if year_end else ys
    except (TypeError, ValueError):
        ys = ye = None

    # Ruler — Ernst III for all 104 records
    ruler = ""
    pers = rec.get("linked_persons_corporations") or {}
    if isinstance(pers, dict):
        for v in pers.values():
            if not isinstance(v, dict):
                continue
            if v.get("type_name_de") in ("Münzherr", "Autorität", "Dargestellte/r"):
                items = v.get("items") or {}
                for it in items.values():
                    last_de = it.get("last_name_de") or ""
                    if last_de:
                        ruler = last_de
                        break
                if ruler:
                    break

    material = (rec.get("material") or {}).get("material_name_en", "Silver")
    metal = METAL_MAP.get(material, "silver")

    weight = parse_weight(rec.get("weight"))
    diameter = parse_diameter(rec.get("diameter"))
    avers_leg = ((rec.get("avers") or {}).get("leg_text") or "").strip()
    revers_leg = ((rec.get("revers") or {}).get("leg_text") or "").strip()

    refs = extract_refs(rec.get("literatur") or "")
    catalog: dict = {}
    others: list[str] = []
    if refs.get("dav"):
        catalog["dav"] = refs["dav"][0]
    if refs.get("lange"):
        catalog["lange"] = refs["lange"][0]
    if refs.get("weinmeister"):
        # Weinmeister isn't a top-level catalog field in our schema; use `others`.
        for w in refs["weinmeister"]:
            others.append(f"Weinmeister-ZfN26# {w}")
    if others:
        catalog["others"] = others

    sources = []
    photographer = ((rec.get("avers") or {}).get("photographer") or {}).get("photographer_name")
    img_right = (rec.get("image_right") or {}).get("short") or "—"
    note_parts = [f"Bild: {img_right}", "Text: CC BY-SA 4.0"]
    if photographer:
        note_parts.append(f"Aufnahme: {photographer}")
    sources.append({
        "type": "museum",
        "url": f"https://ikmk.smb.museum/object?id={nid}",
        "ref": f"IKMK Berlin, Inv. {nid} (Münzkabinett der Staatlichen Museen zu Berlin)",
        "note": "; ".join(note_parts),
    })

    coin: dict = {
        "id": f"hs-ikmk-{nid}",
        "fuss": "seed_unsorted",
        "phase": "I",
        "kind": kind_for_nominal(nominal_full),
        "nominal": nominal_short,
        "year_label": str(ys) if ys == ye else f"{ys}-{ye}",
        "year_first": ys,
        "year_last": ye,
        "ruler": ruler,
        "mint": None,
        "catalog": catalog,
        "metal": metal,
        "fineness": None,
        "fineness_verified": False,
    }
    if weight is not None:
        coin["weight_rough_g"] = [{"value": weight, "source": f"IKMK Berlin, Inv. {nid}"}]
    else:
        coin["weight_rough_verified"] = False
    if diameter is not None:
        coin["diameter_mm"] = diameter
    else:
        coin["diameter_mm_verified"] = False
    if avers_leg:
        coin["inscription_obv"] = avers_leg
    if revers_leg:
        coin["inscription_rev"] = revers_leg
    coin["sources"] = sources
    coin["issuing_entity"] = "holstein_schauenburg_county"
    coin["verified"] = False
    coin["mint_verified"] = False
    coin["verification_note"] = {
        "de": (
            "Bulk-Seed aus IKMK Berlin (Holstein-Schauenburg, Ernst III.). "
            "Müntzstadt — Pinneberg (modernes SH) oder Stadthagen / Bückeburg "
            "(Niedersachsen) — und Müntzfuß-Zuordnung sind ungeklärt; "
            "Per-Münze-Recherche via Weinmeister 1908 + Bei der Wieden 1961 ausstehend."
        ),
        "en": (
            "Bulk seed from IKMK Berlin (Holstein-Schauenburg, Ernst III). "
            "Mint city — Pinneberg (modern SH) vs. Stadthagen / Bückeburg "
            "(Lower Saxony) — and Müntzfuß assignment are unresolved; "
            "per-coin research via Weinmeister 1908 + Bei der Wieden 1961 pending."
        ),
        "uk": (
            "Bulk-сід з IKMK Berlin (Holstein-Schauenburg, Ernст III). "
            "Місто карбування — Піннеберг (сучасний SH) чи Stadthagen / Bückeburg "
            "(Нижня Саксонія) — і призначення Müntzfuß не визначені; "
            "покоінне дослідження через Weinmeister 1908 + Bei der Wieden 1961 очікується."
        ),
    }
    return coin


def main() -> int:
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    schau_ids = idx["issuers"]["Holstein-Schauenburg"]["ids_in_scope"]
    coins = []
    for nid in schau_ids:
        rec = json.loads((IKMK_CACHE / f"{nid}.json").read_text(encoding="utf-8"))
        coins.append(build_coin_entry(rec))
    coins.sort(key=lambda c: (c.get("year_first") or 9999, c["id"]))

    location = {
        "id": "holstein_schauenburg",
        "name": {
            "de": "Grafschaft Holstein-Schauenburg",
            "en": "County of Holstein-Schauenburg",
            "uk": "Графство Гольштейн-Шауенбург",
        },
        "summary": {
            "de": (
                "Reichslehen der Schauenburger Linie unter Ernst III. (1601-1622), "
                "geographisch geteilt zwischen der Grafschaft Pinneberg (heute Kreis "
                "Pinneberg im Schleswig-Holstein) und der Stammgrafschaft Schaumburg "
                "(Stadthagen / Bückeburg, heute Niedersachsen). IKMK Berlin trennt "
                "diese beiden Territorien nicht — der vorliegende Bestand ist "
                "Bulk-Seed (104 Stücke 1616-1622), bis Müntzort und Müntzfuß durch "
                "Weinmeister 1908 + Bei der Wieden 1961 für jeden Eintrag geklärt sind."
            ),
            "en": (
                "Imperial fief of the Schauenburg dynasty under Ernst III (1601-1622), "
                "geographically split between the County of Pinneberg (today Kreis "
                "Pinneberg in Schleswig-Holstein) and the ancestral County of "
                "Schaumburg (Stadthagen / Bückeburg, today Lower Saxony). IKMK "
                "Berlin doesn't distinguish the two territories — this holding is a "
                "bulk seed (104 pieces 1616-1622) pending mint-city and Müntzfuß "
                "resolution via Weinmeister 1908 + Bei der Wieden 1961 per coin."
            ),
            "uk": (
                "Імперський лен династії Шауенбург під Ернстом III (1601-1622), "
                "географічно розділений між графством Піннеберг (сучасний Кreis "
                "Піннеберг у Шлезвіг-Гольштейні) та родовим графством Шаумбург "
                "(Stadthagen / Bückeburg, сучасна Нижня Саксонія). IKMK Berlin не "
                "розрізняє ці дві території — цей фонд є bulk-сід (104 монети "
                "1616-1622) до встановлення міста карбування та Müntzfuß через "
                "Weinmeister 1908 + Bei der Wieden 1961 для кожного запису."
            ),
        },
        "fuss_order": ["seed_unsorted"],
        "phases": {
            "seed_unsorted": [
                {
                    "id": "A",
                    "year_from": 1616,
                    "year_to": 1622,
                    "from_label": "1616",
                    "to_label": "1622",
                    "title": {
                        "de": "Ernst III., Bulk-Seed (Holstein-Schauenburg)",
                        "en": "Ernst III, bulk seed (Holstein-Schauenburg)",
                        "uk": "Ернст III, bulk-сід (Holstein-Schauenburg)",
                    },
                },
            ],
        },
        "coins": coins,
    }

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    with LOC.open("w", encoding="utf-8") as f:
        yaml.dump(location, f)

    # ---- references sidecar ----
    references = {
        "references": [
            {
                "id": "ref1",
                "content": {
                    "de": (
                        "<b>Weinmeister, Paul</b>: <i>Münzgeschichte der Grafschaft "
                        "Holstein-Schauenburg</i>, Zeitschrift für Numismatik 26 (1908) "
                        "348-481. Standardkatalog der Schauenburger Prägungen Ernst III."
                    ),
                    "en": (
                        "<b>Weinmeister, Paul</b>: <i>Münzgeschichte der Grafschaft "
                        "Holstein-Schauenburg</i>, Zeitschrift für Numismatik 26 (1908) "
                        "348-481. Standard catalogue of the Schauenburg coinage of Ernst III."
                    ),
                    "uk": (
                        "<b>Weinmeister, Paul</b>: <i>Münzgeschichte der Grafschaft "
                        "Holstein-Schauenburg</i>, Zeitschrift für Numismatik 26 (1908) "
                        "348-481. Стандартний каталог карбування Ернста III "
                        "(Holstein-Schauenburg)."
                    ),
                },
            },
            {
                "id": "ref2",
                "content": {
                    "de": (
                        "<b>Bei der Wieden, Helge</b>: <i>Fürst Ernst Graf von "
                        "Holstein-Schaumburg und seine Wirtschaftspolitik</i> "
                        "(Rinteln 1961). Wirtschafts- und Müntzpolitik Ernsts III. zwischen "
                        "Pinneberg und Stadthagen — primäre Quelle für Müntzortung."
                    ),
                    "en": (
                        "<b>Bei der Wieden, Helge</b>: <i>Fürst Ernst Graf von "
                        "Holstein-Schaumburg und seine Wirtschaftspolitik</i> "
                        "(Rinteln 1961). Ernst III's economic and minting policy between "
                        "Pinneberg and Stadthagen — primary source for mint-city attribution."
                    ),
                    "uk": (
                        "<b>Bei der Wieden, Helge</b>: <i>Fürst Ernst Graf von "
                        "Holstein-Schaumburg und seine Wirtschaftspolitik</i> "
                        "(Rinteln 1961). Економічна та монетна політика Ернста III між "
                        "Піннебергом та Stadthagen — первинне джерело для атрибуції "
                        "монетного двору."
                    ),
                },
            },
            {
                "id": "ref3",
                "content": {
                    "de": (
                        "<b>IKMK Berlin</b>: <i>Interaktiver Katalog des Münzkabinetts "
                        "Berlin</i> — <a href=\"https://ikmk.smb.museum/\">ikmk.smb.museum</a>. "
                        "104 Stücke unter dem Dynastie-Präfix «Holstein-Schauenburg»; "
                        "Texte CC BY-SA 4.0, Bilder grosso modo PDM 1.0."
                    ),
                    "en": (
                        "<b>IKMK Berlin</b>: <i>Interactive Catalogue of the Münzkabinett "
                        "Berlin</i> — <a href=\"https://ikmk.smb.museum/\">ikmk.smb.museum</a>. "
                        "104 pieces under the dynastic prefix «Holstein-Schauenburg»; "
                        "texts CC BY-SA 4.0, images mostly PDM 1.0."
                    ),
                    "uk": (
                        "<b>IKMK Berlin</b>: <i>Інтерактивний каталог Münzkabinett "
                        "Berlin</i> — <a href=\"https://ikmk.smb.museum/\">ikmk.smb.museum</a>. "
                        "104 записи під династичним префіксом «Holstein-Schauenburg»; "
                        "тексти CC BY-SA 4.0, зображення переважно PDM 1.0."
                    ),
                },
            },
            {
                "id": "ref4",
                "content": {
                    "de": (
                        "<b>Davenport, John S.</b>: <i>German Secular Talers 1600-1700</i> "
                        "(Krause 1976). Zweite Standardreferenz für die Taler der Schauenburger."
                    ),
                    "en": (
                        "<b>Davenport, John S.</b>: <i>German Secular Talers 1600-1700</i> "
                        "(Krause 1976). Secondary standard reference for Schauenburg Talers."
                    ),
                    "uk": (
                        "<b>Davenport, John S.</b>: <i>German Secular Talers 1600-1700</i> "
                        "(Krause 1976). Другий стандартний довідник для талерів Schauenburger."
                    ),
                },
            },
        ],
    }

    with REF.open("w", encoding="utf-8") as f:
        yaml.dump(references, f)

    # Summary
    nominals = Counter(c["nominal"] for c in coins)
    print(f"Wrote {LOC.relative_to(REPO)}: {len(coins)} coins")
    for n, cnt in nominals.most_common():
        print(f"  {cnt:3d}× {n}")
    print(f"Wrote {REF.relative_to(REPO)}: 4 references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
