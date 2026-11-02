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
  Galster concordance — `_LL_TO_GALSTER` (LL 7b = G 142 printed by danskmoent;
  the Norby, ca-1530 and 1535-1537 coins = G 143-147 from Lindblad's text,
  curator 2026-10-28) — plus the hvide 1450-1520 as their own LL rows
  (`_LL_HVID_WINDOWS`), joined to Galster 139 / 140 / 142 by merge decisions.
  The 1554 Copenhagen coins (LL 9-11) have no Galster number and stay out.
- 2016:1 (Heljeback, Denmark 1396–1448), all 145 rows (curator 2026-10-21:
  «їх всі теж додавай в seed»). Galster 1972 numbers there run per ruler, so
  they get explicit scopes (`_VOLUME`); our Numista types of the period carry
  Sieg numbers only, so these mostly stand as their own seed_unsorted rows.

**Metal from the assay (curator 2026-10-26).** A coin with ≥ 50 % Ag is silver,
below that billon; a type whose assayed coins fall on both sides is
`silver_billon`. The appendices give the full composition of every coin, so
the metal is source-attested (`metal_verified`); a weight-only row votes for
nothing. `_assay_metal`.

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
from lib import uncertainty as unc  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
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
    "2016_1": {
        "parsed": "heljeback_2016_metallanalyser_1400_1448_appendix.parsed.json",
        "cite": "Heljeback 2016 (Metallanalyser av mynt 2016:1)",
        "url": ("https://www.su.se/download/18.7e388b91199a31e65d247cd/1759930032121/"
                "Metallanalyser%20av%20mynt%202016:1%20APPENDIXMetallanalyser%20av%20mynt_2016_1_APPENDIX.pdf"),
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
# Mint column and Galster number contradict: the appendix prints «Malmö» on
# pieces whose Galster number (32 / 33 København, 35 Ålborg) is not a Malmø
# type. No erratum (curator 2026-10-21): the pieces go in under the printed
# Galster number, and the printed mint stays visible, marked suspect (*)
# (curator 2026-10-21: «не фільтруй їх, познач двір як (*)»). Note §7a.
_MINT_CONFLICT_2017_1 = {28, 30, 32, 35, 36, 41, 45, 46, 47, 49, 55, 56}
_GALSTER_MINT = {"32": "København", "33": "København", "35": "Ålborg"}


def _mint_suspect(galster: str, nrs: list[int]) -> dict:
    home = _GALSTER_MINT[galster]
    home_de = {"København": "Kopenhagen", "Ålborg": "Aalborg"}[home]
    home_en = {"København": "Copenhagen", "Ålborg": "Aalborg"}[home]
    n = ", ".join(str(x) for x in nrs)
    return {"kind": "suspect", "reason": {
        "de": (f"Der Anhang bei Eriksson 2017 druckt für Nr. {n} die Münzstätte «Malmö», "
               f"die Galster-Nummer {galster} gehört aber zur Münzstätte {home_de} (Eriksson, Tab. 1, "
               f"nach Galster 1972). Welche der beiden Angaben falsch ist, ist aus der Quelle nicht bekannt."),
        "en": (f"The appendix of Eriksson 2017 prints the mint «Malmö» for no. {n}, while Galster "
               f"number {galster} belongs to the {home_en} mint (Eriksson, tab. 1, after Galster 1972). "
               f"Which of the two is wrong is not known from the source."),
        "uk": (f"Додаток Eriksson 2017 друкує для № {n} двір «Malmö», тоді як номер Galster "
               f"{galster} належить двору {home} (Eriksson, табл. 1, за Galster 1972). Котре з двох "
               f"значень хибне, з джерела невідомо."),
        "da": (f"Appendikset hos Eriksson 2017 trykker møntstedet «Malmö» for nr. {n}, mens Galster "
               f"nummer {galster} hører til møntstedet {home} (Eriksson, tab. 1, efter Galster 1972). "
               f"Hvilken af de to angivelser der er forkert, vides ikke ud fra kilden."),
    }}


# Types held back until the curator decides a merge. G 39 and G 42 were held
# (the matcher keeps them apart: G 39 by the tier-1 weight gate — the 1515
# pieces weigh 1,11-2,16 g — and G 42 by the nominal, «Skilling (kl)» vs
# Galster's «18 Penning»); the curator approved both merges 2026-10-22 and they
# are joined by merge_decisions/danish_realm.yml. Note §9b.
_HOLD_BASES_2017_1: set[str] = set()

# Lagerqvist (LL) → Galster, keyed by (appendix denomination, LL): LL numbers
# restart per period, so «2», «4a», «4b» and «7» stand for a hvid of 1455-1520
# AND for a Norby or 1530s coin. Only 7b has a printed concordance (danskmoent
# gotlg142: «Lagerqvist 7b»). The post-1520 rows (curator 2026-10-28) follow
# from Lindblad's own text, which names the issuer, the year and the reverse,
# against danskmoent gotlg143-147 (each of which lists Lindblad 2017:3 under
# «Litteratur»); Galster has one type per issuer and denomination there:
#   tab. 12  Norby skilling u.å. (LL 1, 1a, 1b), agnus dei   → G 144
#   tab. 12  Norby skilling 1524 / 1525 (LL 2, 3)            → G 143
#   tab. 13  Norby hvid u.å. (LL 4a, 4b, «4?»)               → G 145
#   tab. 14  hvid ca 1530 (LL 5a, Hauberg 1891 s. 69)        → G 146
#   tab. 15  skilling 1535 / 1536 / 1537 (LL 6a, 7, 8)       → G 147
# The 1554 Copenhagen coins (LL 9-11) have no Galster number and stay out.
# docs/research/gotland_gote.md §«Lindblad LL and Galster».
_LL_TO_GALSTER = {
    ("hvid", "7b"): "142",
    ("skilling sören norby", "1"): "144", ("skilling sören norby", "1a"): "144",
    ("skilling sören norby", "1b"): "144",
    ("skilling sören norby", "2"): "143", ("skilling sören norby", "3"): "143",
    ("hvid sören norby", "4a"): "145", ("hvid sören norby", "4b"): "145",
    ("hvid sören norby", "4?"): "145",
    ("hvid", "5a"): "146",
    ("skilling", "6a"): "147", ("skilling", "7"): "147", ("skilling", "8"): "147",
}

# 2017:3 Gotland hvide with no printed Galster concordance (curator
# 2026-10-25: «хіба що ті що вписуються в lybsk møntfod»). Lindblad s. 4:
# «Omkring 1450 infördes dansk mynträkning på Gotland … den nya valören hvid
# introducerades och ersatte gotarna … En hvid motsvarade fyra penningar» —
# the hvid belongs to the Danish (Lybsk) set; the gote (ørtug) and the
# W-brakteat penning before it to the Gotlandic reckoning, and stay out.
# Windows as Lindblad dates the groups (tab. 8-11), Lybsk card window (to
# 1520); each LL number its own row, no Galster number asserted.
_LL_HVID_WINDOWS = {"1450": (1450, 1450), "1455-1480": (1455, 1480),
                    "1480-1500": (1480, 1500), "1500-1520": (1500, 1520)}

_RULER = {"KI": "Christian I", "RR": "Rigsrådet", "H": "Hans", "KII": "Christian II",
          # 2016:1 (Heljeback): Erik of Pomerania, Christopher of Bavaria,
          # the Rigsråd's 1448 Skilling
          "EaP": "Erik VII", "EAP": "Erik VII", "KaB": "Christoffer III",
          "RR1448": "Rigsrådet"}
_VOLUME = {"H": "hg", "KII": "c2g",     # as the Galster seeds carry it
           # Galster 1972 numbers Erik's and Christopher's coins in their own
           # runs; an explicit scope keeps «Christoffer III» from deriving the
           # «c3g» scope the merger uses for Christian III's Galster numbers.
           "EaP": "galster1972-erik7", "EAP": "galster1972-erik7",
           "KaB": "galster1972-christoffer3", "RR1448": "galster1972-rigsraad1448"}
_MINT = {"Malmö": "Malmø", "Köpenhamn": "Kopenhagen", "Ålborg": "Aalborg",
         "Gotland": "Visby", "Lund": "Lund", "Gurre": "Gurre",
         "Næstved": "Næstved", "Naestved": "Næstved",
         "Maestved": "Næstved",                 # 2016:1 nr 41, a typo for Næstved
         "Odense": "Odense", "Randers": "Randers"}
_NOMINAL = {"hvid": "1 Hvid", "skilling": "1 Skilling",
            "hvid sören norby": "1 Hvid", "skilling sören norby": "1 Skilling",
            "½ skilling": "1 Søsling", "silvergyllen": "1 Sølvgylden",
            "skilling (kl)": "1 Skilling",
            "sterling": "1 Sterling", "gros": "1 Gros", "sösling": "1 Søsling",
            "lebard": "1 Lebard", "penning": "1 Penning",
            "kopparsterling": "1 Kobbersterling"}

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

# Weight flags of the appendices, all rendered as the fragment mark «(f)»
# (curator 2026-10-26). 2016:1 explains «f» in its own list of abbreviations
# («f fragment»); 2017:1 does not, but by the editorial rule it marks the
# weights of fragmentary pieces separately. «ks» = «kantskada» (edge damage,
# both appendices' abbreviation lists): the weight is not that of a whole
# coin. The tooltip's headline already says «Fragment.», so the reason gives
# only the evidence.
_FRAGMENT_BY_ISSUE = {
    ("2016_1", "f"): {
        "de": "Anhang, Abkürzungsliste: «f fragment». Das Gewicht ist das des Fragments, nicht einer ganzen Münze.",
        "en": "Appendix, list of abbreviations: «f fragment». The weight is that of the fragment, not of a whole coin.",
        "uk": "Додаток, список скорочень: «f fragment». Вага належить фрагменту, а не цілій монеті.",
        "da": "Appendiks, forkortelsesliste: «f fragment». Vægten er fragmentets, ikke en hel mønts.",
    },
    ("2017_1", "f"): {
        "de": "Das Gewicht trägt im Anhang die Marke «f», die dessen Abkürzungsliste nicht erklärt; nach der Redaktionsregel werden Gewichte fragmentarischer Stücke gesondert gekennzeichnet. Das Gewicht ist daher nicht das einer ganzen Münze.",
        "en": "The weight carries the mark «f» in the appendix, which its list of abbreviations does not explain; by the editorial rule, weights of fragmentary pieces are marked separately. The weight is therefore not that of a whole coin.",
        "uk": "Вага в додатку має позначку «f», яку його список скорочень не пояснює; за редакційним правилом вагу фрагментованих монет позначають окремо. Тому це вага не цілої монети.",
        "da": "Vægten bærer i appendikset mærket «f», som dets forkortelsesliste ikke forklarer; efter redaktionens regel mærkes vægten af fragmentariske stykker særskilt. Vægten er derfor ikke en hel mønts.",
    },
}
_FRAGMENT_KS = {
    "de": "Randbeschädigtes Stück (Anhang: «ks kantskada»). Das Gewicht ist daher nicht das einer ganzen Münze.",
    "en": "A piece with a damaged edge (appendix: «ks kantskada»). Its weight is therefore not that of a whole coin.",
    "uk": "Монета з пошкодженим краєм (додаток: «ks kantskada»). Тому це вага не цілої монети.",
    "da": "Et stykke med beskadiget rand (appendiks: «ks kantskada»). Vægten er derfor ikke en hel mønts.",
}


def _years(rows: list[dict]) -> list[int]:
    """Only years printed as a plain year («1512»). «u.å.» and «u.å. (1518)»
    are undated pieces: the bracket is the author's attribution, not a date on
    the coin, and is not turned into a year (it would widen the type's range)."""
    return sorted({int(r["year"]) for r in rows
                   if re.fullmatch(r"\d{4}", r.get("year") or "")})


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower().translate(
        str.maketrans("æøåäö", "aoaao"))).strip("-")


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


def _assay_metal(rows: list[dict]) -> str | None:
    """silver (≥ 50 % Ag) / billon (< 50 %) per assayed coin; both → silver_billon."""
    kinds = {"silver" if r["ag_pct"] >= 50 else "billon"
             for r in rows if r["ag_pct"] is not None}
    if len(kinds) > 1:
        return "silver_billon"
    return kinds.pop() if kinds else None


def _copper_type(rows: list[dict], cite: str) -> dict:
    """A Kobbersterling is a copper coin (curator 2026-10-26: «Кобберстерлінги
    мідні, вистав всім мідь як метал, попри те що там знайдена проба»): metal
    copper whatever the assay. The assayed silver stays in the fineness
    column like any reading (curator 2026-10-31: the «?» there read as
    «unknown from the sources», which it is not)."""
    return {"metal": "copper", "metal_verified": True}


def _row_key(issue: str, row: dict) -> str:
    """«2016:1 nr 38» — the issue as the series prints it plus the row number.
    Not «2016_1:38»: YAML 1.1 readers (PyYAML) resolve that as a base-60
    integer whenever the row number is below 60."""
    return f"{issue.replace('_', ':')} nr {row['nr']}"


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
            elif issue == "2016_1":
                gal = re.sub(r"\s+", "", r["cat"])           # «7 /10/14/15» → «7/10/14/15»
                base = gal.replace("/", "-")
                ruler_code = "RR1448" if r["ruler"] == "RR" else r["ruler"]
            else:
                ll = (r.get("cat") or "").strip()
                if r["mint"] != "Gotland":
                    continue
                if (r["denom"].lower(), ll) in _LL_TO_GALSTER:
                    gal = base = _LL_TO_GALSTER[(r["denom"].lower(), ll)]
                    r = dict(r, _ll_printed=ll)
                else:
                    window = (r.get("year") or "").replace("\u2010", "-")
                    if r["denom"] != "Hvid" or window not in _LL_HVID_WINDOWS:
                        continue
                    # «4 a?» / «4 a??» (Lindblad's own doubt) stay apart from «4a»
                    gal, base = None, "ll" + re.sub(r"\s+", "", ll).replace("?", "q").lower()
                    r = dict(r, _ll=ll, _window=_LL_HVID_WINDOWS[window])
                ruler_code = None
            r = dict(r, _gal=gal, _base=base, _ruler=ruler_code)
            # group by the NORMALISED mint: «Naestved» / «Næstved» (and the
            # «Maestved» typo) are one mint, not three groups
            mint_key = "/".join(_MINT[m] for m in r["mint"].split("/"))
            groups[(issue, base, ruler_code, mint_key,
                    r["denom"].lower())].append(r)

    coins: list[dict] = []
    for (issue, base, ruler_code, mint, denom), rows in sorted(groups.items()):
        meta = _ISSUE[issue]
        lagerqvist = rows[0].get("_ll")
        if lagerqvist is not None:
            gal_values = []
        elif issue == "2016_1":
            gal_values = sorted({g for r in rows for g in r["_gal"].split("/")},
                                key=lambda v: (len(v), v))
        else:
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
                frag = (_FRAGMENT_KS if r["weight_flag"] == "ks"
                        else _FRAGMENT_BY_ISSUE[(issue, r["weight_flag"])])
                w["fragment"] = copy.deepcopy(frag)
            weights.append(w)
            if r["ag_pct"] is not None:            # 2016:1 nr 1: weight only
                finenesses.append({"value": round(r["ag_pct"] / 100, 6), "source": label})
            sources.append({
                "type": "literature", "url": meta["url"],
                # the locator only: the values themselves are the readings
                # above (a number here would bypass the page's decimal format)
                "ref": (f"{label}, Appendix (XRF)"
                        + (f"; Galster {r['_gal']} as printed"
                           if r["_gal"] and "/" in r["_gal"] and issue != "2016_1" else "")
                        + (f"; Lagerqvist {r['_ll_printed']}" if r.get("_ll_printed") else "")
                        + (f"; {r['var']}" if r.get("var") else "")),
            })
        conflict = issue == "2017_1" and all(r["nr"] in _MINT_CONFLICT_2017_1 for r in rows)
        if (issue == "2017_1" and not conflict
                and any(r["nr"] in _MINT_CONFLICT_2017_1 for r in rows)):
            raise SystemExit(f"mixed mint-conflict group {issue} G {base} {mint}")
        ranges = _ranges(_years(rows))
        undated = any(not re.fullmatch(r"\d{4}", r.get("year") or "") for r in rows)
        # Lindblad dates the Gotland hvid groups by period («Hvider ca 1450»,
        # tab. 8-11) — an attribution, never a year on the coin.
        window_dated = lagerqvist is not None
        if lagerqvist is not None and not ranges:
            # Lindblad's dating window for the group (tab. 9-11), not a year
            # on the coin: written as the year, unverified.
            lo, hi = rows[0]["_window"]
            ranges, undated = [[lo, hi]], False
        mints = mint.split("/")
        entry = {
            "id": f"{SOURCE}-{issue.replace('_', '-')}-"
                  + (base if lagerqvist is not None else f"g{base}")
                  + ("" if ruler_code else "-gotland")
                  + (f"-{_slug(mint)}-{_slug(denom)}" if issue == "2016_1" else ""),
            "fuss": "seed_unsorted",
            "phase": SOURCE,
            "kind": "kurant",
            "nominal": _NOMINAL[denom],
            "year_label": _label(ranges),
            "year_first": ranges[0][0] if ranges else None,
            "year_last": ranges[-1][1] if ranges else None,
            "year_ranges": ranges,
            "ruler": _RULER.get(ruler_code),
            "mint": mints[0] if len(mints) == 1 else mints,
            # The catalogue value drops Lindblad's «?» / «??» and the space
            # before the sub-letter («4 a??» → «4a», as other catalogues write
            # it; curator 2026-10-30); the source citation keeps the print.
            "catalog": ({"others": [f"Lagerqvist# {re.sub(r'[?\s]+', '', lagerqvist)}"]}
                        if lagerqvist is not None else
                        {"galster": gal_values[0] if len(gal_values) == 1 else gal_values,
                         **({"galster_volume": _VOLUME[ruler_code]}
                            if ruler_code in _VOLUME else
                            {"galster_volume": "hg"} if not ruler_code else {})}),
            "metal": _assay_metal(rows),
            "fineness": finenesses or None,
            "weight_rough_g": weights,
            # by mint: Visby is Gotlandic coin (`gotland`, mint registry);
            # Danish mints and no mint fall back to the realm
            "issuing_entity": classify_mint_to_entity(mints) or "danish_realm",
            "verified": False,
            "fineness_verified": bool(finenesses),
            "metal_verified": bool(finenesses),
            **(_copper_type(rows, meta["cite"]) if denom.lower() == "kopparsterling" else {}),
            "weight_rough_verified": True,
            "mint_verified": not conflict,
            "sources": sources,
            "verification_note": copy.deepcopy(_NOTE),
            "_metallanalyser_rows": [_row_key(issue, r) for r in rows],
        }
        if window_dated:
            entry["year_verified"] = False
            # Lindblad's period for the hvid group (tab. 8-11), not a year on
            # the coin.
            unc.add(entry, "year", "window", "metallanalyser",
                    value=unc.year_value(entry.get("year_first"), entry.get("year_last")))
        if ranges and undated:
            # the year range covers the dated pieces only; undated ones exist
            entry["_metallanalyser_undated_rows"] = [
                _row_key(issue, r) for r in rows
                if not re.fullmatch(r"\d{4}", r.get("year") or "")]
        if conflict:
            entry["id"] += "-malmoe-printed"
            entry["mint_mark"] = _mint_suspect(base, [r["nr"] for r in rows])
            # keeps the shared writer's sources-imply-mint rule from promoting
            # the printed mint back to verified (lib/v2_seed_writer)
            entry["_mint_uncertain"] = True
        coins.append(entry)
    return coins, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    coins, skipped = collect()
    print(f"entries: {len(coins)}  (weights: {sum(len(c['weight_rough_g']) for c in coins)}, finenesses: {sum(len(c['fineness'] or []) for c in coins)})")
    for c in coins:
        print(f"  {c['id']:<36} {c['nominal']:<12} {str(c['mint']):<11} "
              f"G {c['catalog'].get('galster') or c['catalog'].get('others')}  n={len(c['weight_rough_g'])}  {c['year_label']}")
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
