#!/usr/bin/env python3
"""Lindahl, «Danmarks mønter 1377-1448» (NNÅ 1955, s. 73-93) — Phase 3 SEED.

One entry per coin type of the Danish-crown sections (Ribe, Erik af Pommern,
Christopher af Bajern): the weight range Lindahl prints for the type (with
the average, «gn.»), a single weight where only one piece is given, and the
fineness of the assays she publishes (statsguardein Johs. Siggaard; for Erik's
Lund gros and Christopher's skilling and søsling after N. L. Rasmusson, s. 73).
The Flensborg section (s. 74-76: wittens, viertelwitten, dreling, struck by
the town as «moneta holsacie» in the Danish fief of Schleswig, under the
Sønderjylland dukes and, after 1375, the Holstein counts) goes to its own
entity, `flensborg_medieval` (curator 2026-11-02); its coins name no ruler.
The Ribe witten, the town's own coinage, goes to `ribe_medieval` (curator
2026-11-03).

**No Galster number is assigned** (curator 2026-10-26: «зроби сідами, а там
побачимо чи мерджер сам впорається»): Lindahl cites Jesse numbers and numbers
the legend variants herself («FL»); the merger matches on those, nominal,
ruler, mint and years. FL numbers restart in every ruler's section, so they
are written for the Erik af Pommern section only — the register our Galster
seeds already cite («Fritze Lindahl# 34-41»).

Years are Lindahl's: a range where she gives one («1397—ca. 1405», «efter
ca. 1405, før 1424», «1430-erne»), the lower bound alone where she gives only
that («efter ca. 1405», «efter 1444»), the figure caption for the crowned
Næstved witten («ca 1400»), the reign for Christopher's skilling, whose date
she leaves open; all `year_verified: false`.

The table below is transcribed from scripts/cache/danskmoent/hans_1481_1513/
lindahl_1955_nnaa_1377_1448.extract.txt; page = the printed page.

Usage::

    python scripts/maintenance/build_lindahl_1955_seed.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib import uncertainty as unc  # noqa: E402

SOURCE = "lindahl"
URL = "https://www.danskmoent.dk/pdf2/NNA_1955_Lindahl.pdf"
CITE = "Lindahl 1955 (NNÅ 1955)"

_TRACES = {
    "de": "Lindahl 1955 (S. 80): «Finhed: spor af sølv» (Feingehalt: Spuren von Silber).",
    "en": "Lindahl 1955 (p. 80): «Finhed: spor af sølv» (fineness: traces of silver).",
    "uk": "Lindahl 1955 (с. 80): «Finhed: spor af sølv» (проба: сліди срібла).",
    "da": "Lindahl 1955 (s. 80): «Finhed: spor af sølv».",
}

# key, nominal, ruler, mint, (year_first, year_last), page, Jesse, FL,
# weight range (min, max, avg) or None, single weight or None,
# finenesses (‰), fineness note (assayer) or None, mint certain?, note
TYPES = [
    ("flensborg-witten-leoparder", "1 Witten", None, "Flensborg", (1350, 1381), 74, ["339"], None,
     (0.98, 1.33, 1.29), None, [779], None, True, None),
    ("flensborg-viertelwitten", "1 Viertelwitten", None, "Flensborg", (1350, 1381), 75, ["340"], None,
     (0.28, 0.37, 0.34), None, [530], None, True, None),
    ("flensborg-witten-naeldeblad", "1 Witten", None, "Flensborg", (1379, 1379), 75, ["371"], None,
     (1.14, 1.27, 1.22), None, [], None, True, None),
    ("flensborg-dreling", "1 Dreling", None, "Flensborg", (1392, 1392), 76, ["427"], None,
     (0.73, 1.04, 0.90), None, [675, 759], None, True, None),
    ("ribe-witten", "1 Witten", None, "Ribe", (1373, 1396), 76, ["692"], None,
     (1.09, 1.30, 1.19), None, [800], None, True, None),
    ("naestved-witten-krumstav", "1 Witten", "Erik VII", "Næstved", (1397, 1405), 77, ["693"], "1",
     None, 1.15, [], None, True, None),
    ("naestved-witten-krone", "1 Witten", "Erik VII", "Næstved", (1400, 1400), 78, ["694"], "2",
     None, None, [], None, True, None),
    ("lund-sterling", "1 Sterling", "Erik VII", "Lund", (1405, 1405), 78, ["695"], "3-15",
     (0.50, 1.00, 0.70), None, [532], None, True, None),
    ("naestved-sterling", "1 Sterling", "Erik VII", "Næstved", (1405, 1405), 78, ["695"], "16-31",
     (0.50, 1.00, 0.70), None, [629, 857], None, True, None),
    ("hulpenning", "1 Hulpenning", "Erik VII", ["Næstved", "Lund"], (1405, 1424), 79, ["696"], "33",
     (0.21, 0.37, 0.29), None, [0, 212], None, False, None),
    ("halvpenning", "½ Penning", "Erik VII", None, (1405, 1424), 79, [], "33a",
     None, 0.12, [], None, True, None),
    ("lund-kobbersterling", "1 Kobbersterling", "Erik VII", "Lund", (1422, 1422), 80, ["697", "698"], "34-41",
     (0.75, 1.33, 1.01), None, [], None, True, _TRACES),
    ("naestved-kobbersterling", "1 Kobbersterling", "Erik VII", "Næstved", (1422, 1422), 80, ["697", "698"], "42-49",
     (0.75, 1.33, 1.01), None, [], None, True, _TRACES),
    ("odense-kobbersterling", "1 Kobbersterling", "Erik VII", "Odense", (1422, 1422), 80, ["697", "698"], "50-53",
     (0.75, 1.33, 1.01), None, [], None, True, _TRACES),
    ("randers-kobbersterling", "1 Kobbersterling", "Erik VII", "Randers", (1422, 1422), 80, ["697", "698"], "54-58",
     (0.75, 1.33, 1.01), None, [], None, True, _TRACES),
    ("lund-soesling", "1 Søsling", "Erik VII", "Lund", (1424, 1424), 82, ["484"], "59-62",
     (1.00, 1.34, None), None, [703], None, True, None),
    ("lebard", "1 Lebard", "Erik VII", ["Lund", "Næstved"], (1424, 1424), 82, ["485"], None,
     (0.20, 0.39, 0.27), None, [453], None, True, None),
    ("lund-gros", "1 Gros", "Erik VII", "Lund", (1430, 1439), 83, ["699"], "64-74",
     (0.93, 1.75, 1.27), None, [232], "Rasmusson", True, None),
    ("gurre-gros", "1 Gros", "Erik VII", "Gurre", (1430, 1439), 83, ["699"], "75-99",
     (0.93, 1.75, 1.27), None, [415], None, True, None),
    ("lund-soesling-christopher", "1 Søsling", "Christoffer III", "Lund", (1440, 1440), 84, [], None,
     None, 1.04, [750], "Rasmusson", True, None),
    ("skilling-christopher", "1 Skilling", "Christoffer III", ["Lund", "Malmø"], (1440, 1448), 85, ["705"], None,
     (1.87, 2.38, 2.11), None, [500], "Rasmusson", False, None),
    ("malmoe-sterling", "1 Sterling", "Christoffer III", "Malmø", (1444, 1444), 85, ["704"], None,
     (0.61, 0.73, 0.67), None, [], None, True, None),
    ("malmoe-hvid", "1 Hvid", "Christoffer III", "Malmø", (1444, 1444), 86, ["703"], None,
     (0.48, 1.06, 0.79), None, [370, 400], None, True, None),
]


# Lindahl's own dating of each type, verbatim from the extract (the heading in
# parentheses, or the figure caption where the heading gives none) — for
# Coin.uncertainty (curator 2026-10-29). Christopher's skilling has none: its
# year is his reign.
_DATING_PRINTED = {
    "flensborg-witten-leoparder": ("circa", "ca. 1350 til reces 1379/81"),
    "flensborg-viertelwitten": ("circa", "ca. 1350 til reces 1379/81"),
    "flensborg-witten-naeldeblad": ("after", "efter reces 1379/81"),
    "flensborg-dreling": ("after", "efter reces 1392"),
    "ribe-witten": ("attributed", "1373/77—96"),
    "naestved-witten-krumstav": ("circa", "1397—ca. 1405"),
    "naestved-witten-krone": ("circa", "Witten ca 1400"),
    "lund-sterling": ("after", "efter ca. 1405"),
    "naestved-sterling": ("after", "efter ca. 1405"),
    "hulpenning": ("after", "efter ca. 1405, før 1424"),
    "halvpenning": ("after", "efter ca. 1405, før 1424"),
    "lund-kobbersterling": ("circa", "ca. 1422"),
    "naestved-kobbersterling": ("circa", "ca. 1422"),
    "odense-kobbersterling": ("circa", "ca. 1422"),
    "randers-kobbersterling": ("circa", "ca. 1422"),
    "lund-soesling": ("after", "efter reces 1424"),
    "lebard": ("after", "efter reces 1424"),
    "lund-gros": ("decade", "Gros 1430-erne"),
    "gurre-gros": ("decade", "Gros 1430-erne"),
    "lund-soesling-christopher": ("circa", "ca. 1440"),
    "skilling-christopher": ("reign", None),
    "malmoe-sterling": ("circa", "ca. 1444"),
    "malmoe-hvid": ("after", "efter 1444"),
}


def _metal(fins: list[int], note) -> str | None:
    """Metal from Lindahl's assays by the curator's 50 % line (2026-10-26, as
    for the Metallanalyser assays): ≥ 500 ‰ silver, below billon, both
    silver_billon; the Kobbersterling («spor af sølv») copper; no assay, none."""
    if note is _TRACES:
        return "copper"
    kinds = {"silver" if f >= 500 else "billon" for f in fins}
    if len(kinds) > 1:
        return "silver_billon"
    return kinds.pop() if kinds else None


def _label(page: int) -> str:
    return f"{CITE}, s. {page}"


def collect() -> list[dict]:
    coins = []
    for (key, nominal, ruler, mint, (y0, y1), page, jesse, fl, rng, single,
         fins, assayer, mint_sure, note) in TYPES:
        label = _label(page)
        # Jesse in the named register, as Bruun writes it; Lindahl's legend
        # numbers in `others` under the name the Galster seeds use.
        others = [f"Fritze Lindahl# {fl}"] if fl else []
        fin_label = f"{label} (after Rasmusson)" if assayer == "Rasmusson" else label
        entry = {
            "id": f"{SOURCE}-1955-{key}",
            "fuss": "seed_unsorted",
            "phase": SOURCE,
            "kind": "kurant",
            "nominal": nominal,
            "year_label": f"{y0}" if y0 == y1 else f"{y0}-{y1}",
            "year_first": y0,
            "year_last": y1,
            "year_ranges": [[y0, y1]],
            "year_verified": False,
            "ruler": ruler,
            "mint": mint,
            "mint_verified": mint_sure,
            "catalog": ({**({"jesse": jesse[0] if len(jesse) == 1 else jesse} if jesse else {}),
                         **({"others": others} if others else {})}),
            "metal": _metal(fins, note),
            "metal_verified": _metal(fins, note) is not None,
            "fineness": [{"value": f / 1000, "source": fin_label} for f in fins] or None,
            "fineness_verified": bool(fins),
            "weight_rough_g": ([{"value": single, "source": label}] if single else None),
            "weight_rough_verified": bool(single or rng),
            "issuing_entity": ("flensborg_medieval" if key.startswith("flensborg-")
                               else "ribe_medieval" if key.startswith("ribe-")
                               else "danish_realm"),
            "verified": False,
            "sources": [{"type": "literature", "url": URL,
                         "ref": label + (f"; FL {fl}" if fl else "")}],
        }
        if rng:
            entry["weight_range_g"] = [{"min": rng[0], "max": rng[1], "source": label}]
        if note is _TRACES:
            # an assay without a figure: the fineness column shows it
            # (curator 2026-10-31), so no note repeating it
            entry["fineness_trace"] = [{"source": label,
                                        "as_printed": "Finhed: spor af sølv"}]
        elif note:
            entry["note"] = dict(note)
        if (entry["metal"] is None and key.startswith("flensborg-")
                and nominal.endswith(" Witten")):
            # The unassayed Flensborg Witten: silver read from the
            # denomination name (curator 2026-11-03); Lindahl's other
            # Flensborg Witten assays 779 ‰. Not the Næstved Wittens, whose
            # Galster classes read billon from «Hvid».
            entry["metal"] = "silver"
            unc.add(entry, "metal", "from_name", SOURCE, as_printed=nominal,
                    value="silver")
        how, printed = _DATING_PRINTED[key]
        unc.add(entry, "year", how, SOURCE, as_printed=printed,
                value=unc.year_value(y0, y1))
        coins.append(entry)
    return coins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    coins = collect()
    for c in coins:
        print(f"  {c['id']:<44} {c['nominal']:<16} {str(c['mint']):<20} {c['year_label']}")
    stats = write_v2_seed(
        coins, SOURCE,
        "Lindahl, Fritze: Danmarks mønter 1377-1448, Nordisk Numismatisk "
        "Årsskrift 1955, s. 73-93 — weight ranges and assays per coin type "
        "(danskmoent.dk pdf2/NNA_1955_Lindahl.pdf).",
        source_label=SOURCE,
        dry_run=args.dry_run,
    )
    for ent, s in sorted(stats["per_entity"].items()):
        print(f"  {ent:<20} {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
