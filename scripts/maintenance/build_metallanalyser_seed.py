#!/usr/bin/env python3
"""«Metallanalyser av mynt» appendices — Phase 3 SEED.

Reads the Phase-2 sidecars written by `scripts/parse_su_metallanalyser.py`
(per-coin XRF assays, Numismatiska forskningsgruppen, Stockholm University)
and emits `data/v2/seed/metallanalyser/<entity>.yml`: one entry per Galster
type, every assayed coin a paired reading (`weight_rough_g` + `fineness` under
the same source label, so the build pairs each weight with its own Ag) and its
own `sources` line (§9a). Analysis and decisions: docs/research/eriksson_2017_assays.md.

**Scope (curator 2026-10-21).**
- 2017:1 (Eriksson, Denmark 1448–1523), all rows except those listed in
  `_SKIP_2017_1` with the reason for each.
- 2017:3 (Lindblad, Gotland): only rows whose Lagerqvist (LL) number has a
  printed Galster concordance — `_LL_TO_GALSTER`. danskmoent's Galster pages
  give three (LL 1 = G 139, LL 5 = G 140, LL 7b = G 142); LL 1 and LL 5 are held
  back because danskmoent names those types «Gote» while Lindblad lists the
  coins as «Hvid» (note §8). Other LL numbers wait for a concordance.
- 2016:1 (Heljeback, 1400–1448): not seeded — no type of ours to attach to.

**No catalogue or mint is corrected here** (curator: no index / mint errata for
now). The appendix's Galster number, mint and date go in as printed; rows where
the mint and the Galster number contradict each other are skipped instead.

Usage::

    python scripts/maintenance/build_metallanalyser_seed.py [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.paths import HARVEST_ROOT  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

CACHE = HARVEST_ROOT / "danskmoent" / "hans_1481_1513"
SOURCE = "metallanalyser"

_ISSUE = {
    "2017_1": {
        "parsed": "eriksson_2017_metallanalyser_appendix.parsed.json",
        "cite": "Eriksson 2017 (Metallanalyser av mynt 2017:1)",
        "url": ("https://www.su.se/download/18.7e388b91199a31e65d247cb/1759930031611/"
                "Metallanalyser%20av%20mynt%202017:1_APPENDIXMetallanalyser%20av%20mynt_2017_1_APPENDIX.pdf"),
    },
    "2017_3": {
        "parsed": "lindblad_2017_metallanalyser_gotland_appendix.parsed.json",
        "cite": "Lindblad 2017 (Metallanalyser av mynt 2017:3)",
        "url": ("https://www.su.se/download/18.7e388b91199a31e65d247c7/1759930030292/"
                "Metallanalyser%20av%20mynt%202017:3_APPENDIXMetallanalyser%20av%20mynt_2017_3_APPENDIX.pdf"),
    },
}

# Rows of 2017:1 left out, with the reason (note §3, §7, §7a).
_SKIP_2017_1: dict[int, str] = {
    # Contemporary forgeries (curator 2026-10-21: «фальшивки відфільтруй»).
    22: "forgery: Eriksson s. 7, confused legends, 13,25 % Ag",
    23: "forgery: Eriksson s. 7, near-copper (3 % Ag), illegible legends",
    81: "forgery: 3,10 % Ag; Eriksson s. 4 on low-silver Hvide as forgeries",
    # ¼ Sølvgylden printed as Galster 38 — G 38 is the whole Sølvgylden.
    84: "1/4 gyllen printed with the whole Sølvgylden's Galster 38",
}
# Mint column and Galster number contradict (G 32 / 35 / 33 are not Malmø
# types); the curator's tentative photo reading favours the mint column, but no
# erratum is made for now — the rows wait (note §7a).
for _n in (28, 30, 32, 35, 36, 41, 45, 46, 47, 49, 55, 56):
    _SKIP_2017_1[_n] = "mint column and Galster number contradict (note §7a)"

# Types held back until the curator decides the merge (note §9): the matcher
# keeps them apart from our existing class — G 39 by the tier-1 weight gate
# (the 1515 pieces weigh 1,11-2,16 g), G 42 by the nominal («Skilling (kl)» vs
# Galster's «18 Penning»). Seeding them unmerged would add duplicate rows.
_HOLD_BASES_2017_1 = {"39", "42"}

_LL_TO_GALSTER = {"7b": "142"}           # danskmoent gotlg142: «Lagerqvist 7b»

_RULER = {"KI": "Christian I", "RR": "Rigsrådet", "H": "Hans", "KII": "Christian II"}
_VOLUME = {"H": "hg", "KII": "c2g"}      # as the Galster seeds carry it
_MINT = {"Malmö": "Malmø", "Köpenhamn": "Kopenhagen", "Ålborg": "Aalborg",
         "Gotland": "Visby"}
_NOMINAL = {"hvid": "1 Hvid", "skilling": "1 Skilling",
            "½ skilling": "1 Søsling", "silvergyllen": "1 Sølvgylden",
            "skilling (kl)": "1 Skilling"}

_NOTE = {
    "de": ("Röntgenfluoreszenzanalyse (XRF) der Oberfläche, Stücke aus dem Königlichen "
           "Münzkabinett Stockholm; kalibriert ist nur das Silber (Fehlergrenze ±0,8 %). "
           "Gewicht und Feingehalt jedes Stücks stammen aus dem Anhang der Veröffentlichung."),
    "en": ("Surface X-ray fluorescence (XRF) of pieces in the Royal Coin Cabinet, "
           "Stockholm; only silver is calibrated (error margin ±0.8 %). Weight and "
           "fineness of each piece come from the publication's appendix."),
    "uk": ("Рентгенофлуоресцентний аналіз (XRF) поверхні, монети з Королівського "
           "монетного кабінету в Стокгольмі; калібровано лише срібло (похибка ±0,8 %). "
           "Вага і проба кожної монети взяті з додатка до публікації."),
    "da": ("Røntgenfluorescensanalyse (XRF) af overfladen, stykker fra Kungliga "
           "Myntkabinettet i Stockholm; kun sølvet er kalibreret (fejlmargin ±0,8 %). "
           "Vægt og finhed for hvert stykke stammer fra publikationens appendiks."),
}

# «ks» = «kantskada» (edge damage, the appendix's own abbreviation list); «f»
# is not explained in that list. Both readings stay visible, marked (*).
_SUSPECT = {
    "ks": {
        "de": "Randbeschädigtes Stück (Anhang: «ks kantskada»). Das Gewicht kann daher unter dem eines unbeschädigten Stücks liegen; ob und wie viel, ist nicht angegeben.",
        "en": "A piece with a damaged edge (appendix: «ks kantskada»). Its weight may therefore lie below that of an undamaged piece; whether and by how much is not stated.",
        "uk": "Монета з пошкодженим краєм (додаток: «ks kantskada»). Тому її вага може бути нижчою за вагу непошкодженої монети; чи так і наскільки, не вказано.",
        "da": "Et stykke med beskadiget rand (appendiks: «ks kantskada»). Vægten kan derfor ligge under et ubeskadiget stykkes; om og hvor meget, er ikke angivet.",
    },
    "f": {
        "de": "Das Gewicht trägt im Anhang die Marke «f», die in dessen Abkürzungsliste nicht erklärt ist; nach der Redaktionsregel werden Gewichte fragmentarischer Stücke gesondert gekennzeichnet. Ob das Stück unvollständig ist, ist nicht angegeben.",
        "en": "The weight carries the mark «f» in the appendix, which its list of abbreviations does not explain; by the editorial rule, weights of fragmentary pieces are marked separately. Whether the piece is incomplete is not stated.",
        "uk": "Вага в додатку має позначку «f», яку його список скорочень не пояснює; за редакційним правилом вагу фрагментованих монет позначають окремо. Чи монета неповна, не вказано.",
        "da": "Vægten bærer i appendikset mærket «f», som dets forkortelsesliste ikke forklarer; efter redaktionens regel mærkes vægten af fragmentariske stykker særskilt. Om stykket er ufuldstændigt, er ikke angivet.",
    },
}


def _years(rows: list[dict]) -> list[int]:
    """Only years printed as a plain year («1512»). «u.å.» and «u.å. (1518)»
    are undated pieces: the bracket is the author's attribution, not a date on
    the coin, and is not turned into a year (it would widen the type's range)."""
    return sorted({int(r["year"]) for r in rows if re.fullmatch(r"\d{4}", r["year"] or "")})


def _ranges(years: list[int]) -> list[list[int]] | None:
    out: list[list[int]] = []
    for y in years:
        if out and y == out[-1][1] + 1:
            out[-1][1] = y
        else:
            out.append([y, y])
    return out or None


def _label(ranges) -> str | None:
    if not ranges:
        return None
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in ranges)


def _galster_value(raw: str) -> str:
    """«23c» → «23C» (the case our Galster sub-letters are kept in)."""
    return re.sub(r"[a-d]$", lambda m: m.group(0).upper(), raw)


def collect() -> tuple[list[dict], list[str]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    skipped: list[str] = []
    for issue, meta in _ISSUE.items():
        rows = json.loads((CACHE / meta["parsed"]).read_text(encoding="utf-8"))["rows"]
        for r in rows:
            if issue == "2017_1":
                if r["nr"] in _SKIP_2017_1:
                    skipped.append(f"{issue} nr {r['nr']}: {_SKIP_2017_1[r['nr']]}")
                    continue
                gal = r["cat"]
                base = re.match(r"\d+", gal).group(0)
                if base in _HOLD_BASES_2017_1:
                    skipped.append(f"{issue} nr {r['nr']}: G {base} held (merge undecided)")
                    continue
                ruler_code = r["ruler"]
            else:
                ll = (r.get("cat") or "").strip()
                if r["mint"] != "Gotland" or ll not in _LL_TO_GALSTER:
                    continue
                gal = base = _LL_TO_GALSTER[ll]
                ruler_code = None
            if r["ag_pct"] is None:
                skipped.append(f"{issue} nr {r['nr']}: no assay")
                continue
            r = dict(r, _gal=gal, _base=base, _ruler=ruler_code)
            groups[(issue, base, ruler_code, r["mint"],
                    r["denom"].lower())].append(r)

    coins: list[dict] = []
    for (issue, base, ruler_code, mint, denom), rows in sorted(groups.items()):
        meta = _ISSUE[issue]
        gal_values = sorted({_galster_value(r["_gal"]) for r in rows
                             if "/" not in r["_gal"]} | {base},
                            key=lambda v: (len(v), v))
        weights, finenesses, sources = [], [], []
        for r in rows:
            label = f"{meta['cite']}, Nr {r['nr']}"
            w = {"value": r["weight_g"], "source": label}
            if r["weight_flag"]:
                # a copy per reading: a shared dict becomes a YAML anchor and
                # renumbers every anchor after it in the final file
                w["suspect"] = copy.deepcopy(_SUSPECT[r["weight_flag"]])
            weights.append(w)
            finenesses.append({"value": round(r["ag_pct"] / 100, 6), "source": label})
            sources.append({
                "type": "literature", "url": meta["url"],
                # the locator only: the values themselves are the readings
                # above (a number here would bypass the page's decimal format)
                "ref": (f"{label}, Appendix (XRF)"
                        + (f"; Galster {r['_gal']} as printed" if "/" in r["_gal"] else "")),
            })
        ranges = _ranges(_years(rows))
        undated = any(not re.fullmatch(r"\d{4}", r["year"] or "") for r in rows)
        entry = {
            "id": f"{SOURCE}-{issue.replace('_', '-')}-g{base}"
                  + ("" if ruler_code else "-gotland"),
            "fuss": "seed_unsorted",
            "phase": SOURCE,
            "kind": "kurant",
            "nominal": _NOMINAL[denom],
            "year_label": _label(ranges),
            "year_first": ranges[0][0] if ranges else None,
            "year_last": ranges[-1][1] if ranges else None,
            "year_ranges": ranges,
            "ruler": _RULER.get(ruler_code),
            "mint": _MINT[mint],
            "catalog": {"galster": gal_values[0] if len(gal_values) == 1 else gal_values,
                        **({"galster_volume": _VOLUME[ruler_code]}
                           if ruler_code in _VOLUME else
                           {"galster_volume": "hg"} if not ruler_code else {})},
            "fineness": finenesses,
            "weight_rough_g": weights,
            "issuing_entity": "danish_realm",
            "verified": False,
            "fineness_verified": True,
            "weight_rough_verified": True,
            "mint_verified": True,
            "sources": sources,
            "verification_note": copy.deepcopy(_NOTE),
            "_metallanalyser_rows": [f"{issue}:{r['nr']}" for r in rows],
        }
        if ranges and undated:
            # the year range covers the dated pieces only; undated ones exist
            entry["_metallanalyser_undated_rows"] = [
                f"{issue}:{r['nr']}" for r in rows
                if not re.fullmatch(r"\d{4}", r["year"] or "")]
        coins.append(entry)
    return coins, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    coins, skipped = collect()
    print(f"entries: {len(coins)}  (readings: {sum(len(c['fineness']) for c in coins)})")
    for c in coins:
        print(f"  {c['id']:<36} {c['nominal']:<12} {c['mint']:<11} "
              f"G {c['catalog']['galster']}  n={len(c['fineness'])}  {c['year_label']}")
    print(f"skipped rows: {len(skipped)}")
    for s in skipped:
        print("  " + s)
    stats = write_v2_seed(
        coins, SOURCE,
        "Metallanalyser av mynt (Numismatiska forskningsgruppen, Stockholm "
        "University) — per-coin XRF assays from the appendices of 2017:1 "
        "(Eriksson, Denmark 1448-1523) and 2017:3 (Lindblad, Gotland).",
        source_label=SOURCE,
        dry_run=args.dry_run,
        extra_curated_fields=frozenset({"_metallanalyser_rows",
                                        "_metallanalyser_undated_rows"}),
    )
    for ent, s in sorted(stats["per_entity"].items()):
        print(f"  {ent:<20} total={s['total']} new={s['added_new']} "
              f"merged={s['merged_existing']} orphan={s['orphan_curated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
