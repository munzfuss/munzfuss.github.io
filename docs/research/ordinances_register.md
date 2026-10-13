# Register of monetary instruments — Danish-Norwegian and Imperial

> **What this is.** One place to look up a coinage ordinance, edict, recess or
> treaty before searching for it again. The project cites 80-odd dated
> instruments across its dossiers and its `fuesse.yml` prose, and until now the
> only way to find what one of them SAYS was to re-read whichever dossier
> happened to quote it.
>
> **Scope.** Instruments that set or change monetary parameters — piece-count,
> fineness, weight, tariff, legal-tender status. Not coin catalogues, not
> auction records, not literature about them.

## How to use it

1. Look the year up in §1 (Danish-Norwegian) or §2 (Imperial / German).
2. A row with a **refs_pool key** is citable straight from prose:
   `<sup>[ref:KEY]</sup>`. That entry carries the verbatim quote and the URL.
3. A row in §3 is one the project already cites SOMEWHERE but that nobody has
   written up here yet. The «cited in» column says where to read what we
   already know, so the next session starts from our own text rather than from
   a search engine.
4. A row with a **Dossier** link has its full write-up in
   [`instruments/`](instruments/README.md) (one file per act, nine fixed
   sections). §4 lists acts that were examined and found to set no monetary
   parameter — so nobody re-finds them.

## Columns (target shape for §1 and §2 — rows are being migrated to it, 2026-10-13)

`Date · Instrument (the source's own name, its own language) · Issuer ·
Jurisdiction · What it sets · Text seen · refs_pool key · Dossier`

- **Jurisdiction codes:** `DK` Denmark · `NO` Norway under the Danish crown ·
  `SH-d` the ducal (Gottorp / Haderslev / Sønderborg) share of
  Schleswig-Holstein · `SH-k` the royal share · `HRE` Imperial. One row may
  carry several (`DK+NO` for the 1514 pair).
- **What it sets:** the parameters only — coins named · pieces to the mark
  (which mark) · fineness in the act's unit (karat / lod) · tariff / course ·
  mints · mintmaster — in ≤ 3 lines. Everything beyond that is the dossier's.
- **Text seen** is the honesty column: `act` when the row was written from the
  instrument's own text (Secher, Kolderup-Rosenvinge, Paus, Schou, Hirsch,
  Mordhorst's Bilag, a Rigsarkivet scan); `Wilcke` / `Galster` / `Ernst` when
  it was written from that author's retelling. A retelling is NOT the act —
  a figure that only a retelling gives is cited as the retelling's, and the
  dossier says so.
- In scope: an act that fixes pieces/mark, fineness, weight, tariff or
  course, legal-tender status or demonetisation, a mint's location, or a
  mintmaster's appointment WITH parameters. Out of scope (→ §4): acts with
  no monetary parameter.

## Discipline — two rules learned the hard way

**An instrument states a TARGET; an assay states an OUTCOME.** They look alike
in a table and mean opposite things. Wilcke's comparison table of Rhenish
gulden reads as a list of standards and is in fact the output of the Nürnberg
Valvationstag of 1551, where a Wardein from each imperial Kreis assayed
circulating coin. A plan to make a fuss's piece-count phase-variable was built
on mistaking one for the other, and would have replaced decreed targets with
measured outturns. Before entering a figure here, ask which of the two it is —
and say so in the row. See `rhinsk_gylden_fod.md` §7.

**Karat is the primary value; the permille is its conversion.** The ordinances
state «18½ Karat», not «.77». Deriving arithmetic from a rounded decimal moves
the target — 18½ Karat is 0,770833, and at 72 to the mark that is 2,50367 g
fine against the 2,501 a rounded .77 gives. See `rhinsk_gylden_fod.md` §6.

## §1 · Danish-Norwegian

| Date | Instrument | What it sets | refs_pool key | Read it |
|---|---|---|---|---|
| **1497**, 4 Dec | Møntanordning for Sverige (Hans → mintmaster Michel Johansson) | Gylden at 72 pieces to the 18½-carat Cologne mark. Scoped to **Sweden alone** and **never executed** — «*Nogen svensk Guldmønt blev dog aldrig slaaet*». Evidentiary, not normative: it fixes what Hans himself meant by «Rhenska gulden slag», but governs no Danish coinage. | `wilcke6-hans-moentanordning-1497-sverige` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) · cached `danskmoent/wilcke/w6a.htm` |
| Summer **1514** | Møntordning of Christian II (Dienis Blicher Brev, Malmø) | Both metals, both kingdoms. Gold: Nobel 23½ Kt at 16/Mark; **Rhinsk Gylden 18 Kt at 72/Mark**; Skilling subdivisions. The first comprehensive Danish-Norwegian act and the project's Danish scope anchor. | `wilcke-rhinsk-gylden-1514-standard` | Wilcke 7-2 p. 152-153 — [PDF](https://www.danskmoent.dk/pdf2/Wilcke%207-2.pdf) |
| **1524**, 25 Feb | Møntordning of Frederik I | Gold: «*Nobler (… 23½ Karat … 16 Stkr.), Rinske Gylden (18 Karat, 72 Stkr.)*». Restates 1514's gold grid. | `wilcke-rhinsk-gylden-1524-standard` | Wilcke 7-2 p. 184 — [PDF](https://www.danskmoent.dk/pdf2/Wilcke%207-2.pdf) |
| **1540** | Recess | Exchange ceiling: «*oc schall een rhinsk Gylden eller en Jochimsdaler ikke dyrere wedtzles end for III Mark Danske*». Sets the daler-vs-mark ceiling the 1541 ordinance then implements. | — | `moentordning_1541.md` §6 |
| **1541** | Møntordning of Christian III | Establishes the dalerfod as a formal coinage standard. Full dossier. | — | `moentordning_1541.md` (whole file) |
| **1602**, 8 Sept | Forordning | Gold schedule: **Portugaløser 6¾/Mark at 23½ Kt**, **Ungersk Gylden 67/Mark at 23⅓ Kt**. The Rhinsk Gylden is ABSENT — Danish gold is redefined on the ducat grid. | `wilcke1-moentordning-1602-guld` | `dk_dukat_portugaloeser_fod.md` §3.1 |
| **1604**, 20 Nov | Møntordning | Moves the tariff only; the 1602 metrology stands. | `wilcke1-moentordning-1604-nedsaettelse` | `dk_dukat_portugaloeser_fod.md` §3 |

## §2 · Imperial / German

| Date | Instrument | What it sets | refs_pool key | Read it |
|---|---|---|---|---|
| **1490** | Norm of the four Rhenish electors | **71⅓ pieces to the Marck at 18½ Karat** (3,278 g rough / 2,527 g fine) — the Rhenish-gulden form the Empire kept until 1559. | `wilcke6-rhinfyrster-1490-norm` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1495** | Wormser Reichsabschied | Raises the electors' 1490 norm to imperial rank: «*Paa Rigsdagen i Worms 1495 vedtoges denne Møntfod*», reconfirmed at Lindau 1497 and Freiburg 1498. The anchor every pre-1559 Rhenish gulden is measured against. | `wilcke6-worms-1495-reichsabschied` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) · `rhinsk_gylden_fod.md` §1 |
| **1551**, 14 Feb | Augsburg Reichstag decision → **Valvationstag**, Nürnberg | NOT a standard: sends two councillors and a Wardein from each Kreis to «*prøve hver enkelt Mønt … oplyse dens Vægt, Gehalt og det Antal Kreuzer*». Its output is ASSAY data — the source of the karat figures in Wilcke's comparison table. | `wilcke6-valvationstag-1551` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1551**, 28 July | Møntordning of Karl V | Upholds the electors' 1490 form (71⅓ @ 18½). Tariffs: Thaler (Specie) 68 Kreuzer, 24 Skilling lybsk 60 Kreuzer, rhinsk Guldgylden 72 Kreuzer. | `wilcke6-karl-v-moentordning-1551` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1559**, 19 Aug | Møntedikt of Ferdinand I (Augsburger Reichsmünzordnung) | «*fastsattes endelig Møntens Gehalt til **72 Stkr. af den 18½ Karat fine Mark***». Also voids, with six months' notice, «*saavel Christian III.s som Kong Hans' Guldgylden*». Recognises the Dukat as the Reich's gold coin. This is why Danish fineness rises to 18½ from 1563. | `wilcke6-ferdinand-moentedikt-1559` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) · [RMO 1559](https://de.wikipedia.org/wiki/Augsburger_Reichsm%C3%BCnzordnung_von_1559) |

## §3 · Cited in the project, not yet written up here

Generated from a scan of `docs/research/*.md` + `data/shared/*.yml`. Each row is
an instrument our own text already discusses; fill it into §1 or §2 when you next
work on it, rather than researching it afresh.

| Year | Kind | Cited in |
|---|---|---|
| 1495 | Reichsabschied | `fuesse.yml`, `rhinsk_gylden_fod.md`, `source_authority.yml` |
| 1496 | Møntordning | `rhinsk_gylden_fod.md` |
| 1497 | Møntanordning | `rhinsk_gylden_fod.md` |
| 1497 | Møntordning | `danish_royal_gold_1560_1648.md` |
| 1514 | Møntordning | `denmark_fuesse_year_boundaries.md`, `fuesse.yml`, `moentordning_1541.md` … |
| 1518 | Møntordning | `christian_iii_danish_coinage_1534_1572.md` |
| 1523 | Reichsabschied | `rhinsk_gylden_fod.md` |
| 1524 | Møntordning | `fuesse.yml`, `refs_pool.yml`, `rhinsk_gylden_fod.md` |
| 1524 | Reichsmünzordnung | `9_thalerfuss.md`, `dk_dukat_portugaloeser_fod.md` |
| 1532 | Møntordning | `fuesse.yml` |
| 1534 | Møntordning | `pre_1541_silver_seed_inventory.md` |
| 1536 | Reces | `moentordning_1541.md` |
| 1537 | Reces | `moentordning_1541.md` |
| 1539 | Reces | `moentordning_1541.md` |
| 1540 | Reces | `moentordning_1541.md` |
| 1541 | Forordning | `christian_iii_danish_coinage_1534_1572.md`, `moentordning_1541.md` |
| 1541 | Moentordning | `christian_iii_danish_coinage_1534_1572.md`, `denmark_fuesse_year_boundaries.md`, `pre_1541_silver_seed_inventory.md` … |
| 1541 | Møntordning | `christian_iii_danish_coinage_1534_1572.md`, `fuesse.yml`, `moentordning_1541.md` … |
| 1544 | Forordning | `denmark_fuesse_year_boundaries.md`, `wilcke_1514_1541_specs.md` |
| 1544 | Møntordning | `moentordning_1541.md` |
| 1544 | Reces | `moentordning_1541.md` |
| 1547 | Reces | `moentordning_1541.md` |
| 1551 | Moentordning | `fuesse.yml`, `refs_pool.yml` |
| 1551 | Møntordning | `refs_pool.yml`, `rhinsk_gylden_fod.md` |
| 1559 | Møntedikt | `fuesse.yml` |
| 1559 | Reichsmünzordnung | `9_thalerfuss.md`, `de_reichsdukatenfuss.md`, `denmark_fuesse_year_boundaries.md` … |
| 1566 | Konvention | `9_thalerfuss.md`, `fuesse.yml` |
| 1566 | Reichsabschied | `9_thalerfuss.md`, `fuesse.yml`, `german_fuesse-references.yml` … |
| 1566 | Reichsmünzordnung | `fuesse.yml` |
| 1571 | Reichsmünzordnung | `fuesse.yml` |
| 1582 | Møntordning | `moentordning_1541.md` |
| 1602 | Forordning | `daler_klippe_1604.md`, `danish_royal_gold_1560_1648.md`, `refs_pool.yml` |
| 1602 | Moentordning | `fuesse.yml`, `refs_pool.yml` |
| 1602 | Møntordning | `daler_klippe_1604.md`, `danish_royal_gold_1560_1648.md` |
| 1604 | Moentordning | `fuesse.yml`, `refs_pool.yml` |
| 1604 | Møntordning | `danish_royal_gold_1560_1648.md`, `refs_pool.yml` |
| 1615 | Reces | `moentordning_1541.md` |
| 1624 | Forordning | `fuesse.yml` |
| 1658 | Forordning | `fuesse.yml` |
| 1667 | Münzvertrag | `9_thalerfuss.md`, `german_fuesse-references.yml`, `german_fuesse.yml` … |
| 1668 | Münzvertrag | `9_thalerfuss.md`, `fuesse.yml` |
| 1671 | Forordning | `fuesse.yml` |
| 1671 | Plakat | `fuesse.yml` |
| 1690 | Münzvertrag | `german_fuesse.yml` |
| 1700 | Forordning | `rhinsk_gylden_fod.md` |
| 1726 | Forordning | `fuesse.yml` |
| 1726 | Konvention | `fuesse.yml` |
| 1727 | Forordning | `german_fuesse.yml` |
| 1750 | Konvention | `9_thalerfuss.md`, `german_fuesse.yml`, `pistolen_fuss.md` |
| 1753 | Konvention | `9_thalerfuss.md`, `german_fuesse-references.yml`, `refs_pool.yml` |
| 1757 | Forordning | `german_fuesse.yml` |
| 1763 | Konvention | `9_thalerfuss.md`, `german_fuesse-references.yml`, `german_fuesse.yml` … |
| 1782 | Plakat | `courantdukatenfuss.md`, `fuesse.yml`, `german_fuesse-references.yml` … |
| 1788 | Forordning | `german_fuesse.yml` |
| 1794 | Plakat | `fuesse.yml` |
| 1795 | Plakat | `courantdukatenfuss.md`, `fuesse.yml`, `german_fuesse-references.yml` … |
| 1796 | Plakat | `fuesse.yml` |
| 1813 | Forordning | `fuesse.yml`, `refs_pool.yml` |
| 1813 | Møntlov | `dk_kronefod_unity_analysis.md` |
| 1837 | Münzvertrag | `german_fuesse.yml` |
| 1838 | Münzvertrag | `german_fuesse.yml` |
| 1841 | Forordning | `fuesse.yml` |
| 1857 | Konvention | `9_thalerfuss.md` |
| 1857 | Münzvertrag | `fuesse.yml`, `german_fuesse-references.yml`, `german_fuesse.yml` … |
| 1871 | Münzgesetz | `denmark_fuesse_year_boundaries.md`, `dk_kronefod_1873_research.md`, `dk_kronefod_unity_analysis.md` … |
| 1871 | Münzvertrag | `fuesse.yml` |
| 1873 | Konvention | `dk_kronefod_1873_research.md` |
| 1873 | Møntlov | `denmark_fuesse_year_boundaries.md`, `dk_kronefod_1873_research.md`, `fuesse.yml` … |
| 1873 | Münzgesetz | `fuesse.yml`, `pistolen_fuss.md`, `refs_pool.yml` |
| 1875 | Münzvertrag | `pistolen_fuss.md` |
| 1957 | Forordning | `krone_muentzfuesse.md` |

*(A year appearing in both §1/§2 and §3 is not a duplicate: §3 lists every
mention, including the ones the written-up rows above already cover.)*

## §4 · Seen, excluded

Acts examined for this register that set no monetary parameter (general
administrative letters, confirmations without figures, instruments outside
the jurisdictions above). Kept so the next scan does not re-open them.

| Date | Instrument | Where seen | Why excluded |
|---|---|---|---|
| — | *(none yet)* | | |
