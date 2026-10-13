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

Columns as defined above. «Text seen»: `Wilcke prints` = Wilcke VII reproduces the act's
wording (Danish of the period or German); `Wilcke` / `Galster` / `Holst` / `Ernst` = that
author's retelling; `act` = read in a printed Corpus or a scan. Page hints are PRINTED pages
(Wilcke VII chapters: 7-1 … 7-6 = his Første … Sjette Kapitel; our PDF extracts carry the
printed number on each page).

### §1a · 1480–1559 (Hans · Christian II · Frederik I · Christian III)

| Date | Instrument (source's name) | Issuer | Jur. | What it sets | Text seen | refs_pool key | Dossier |
|---|---|---|---|---|---|---|---|
| **1480**, 12 Sept | Møntordning, Arboga | Riksråd / Sten Sture | SE | Swedish standard of the Union years, continuing Sten Sture's Ordning 4 July 1478 and Brev 10 March 1479; Wilcke's starting point for Hans' coinage. Evidentiary, not Danish law. | Wilcke 7-1 p. 119 (prints the Latin dating clause) | — | — |
| **1497**, 4 Dec | Møntanordning for Sverige (Hans → mintmaster Michel Johansson) | Hans | SE | Gylden 72 to the 18½-carat Cologne mark. Sweden only, never executed («*Nogen svensk Guldmønt blev dog aldrig slaaet*»); fixes what Hans meant by «Rhenska gulden slag». | Wilcke 6 ch. 1; Wilcke 7-1 p. 120 | `wilcke6-hans-moentanordning-1497-sverige` | — |
| **1513**, 22 July | Haandfæstning Christian II, møntparagraf | Christian II / Rigsraad | DK+NO | «*hvad som myntes efter thende dag i Danmark og Norge skal myntes saa at thue mark giør fyldest for en* [rhinsk Gylden]» — the 2 Mark = 1 Gylden rate the 1514 ordinance implements. | Wilcke 7-2 p. 149 (quotes); Galster | — | → 1514 dossier |
| **1513**, 1 Aug | Beskikkelsesbrev (reskript) for Dynes Blicher, Malmø | Christian II | DK | Mintmaster appointment WITH parameters: strike Skilling and Hvid, 1 Skilling = 3 Hvide, 16 Skilling = ½ rhinsk Gylden (Ernst: Gylden = 32 sk.). Wilcke: not carried out. | Wilcke 7-2 p. 149 (quotes); Ernst (artikler_skilltal) | `wilcke-1950-blicher-1513`, `wilcke-1950-ordning-1513-ikke-udfoert` | → 1514 dossier |
| Summer **1514** | Møntordning («Dienis Blicher Brev»), Malmø | Christian II with Rigsraad | DK | Both metals: Nobel 16/Mark 23½ Kt; rhinsk Gylden 72/Mark 18 Kt; Sølvgylden 8½/Mark 14 Lod; Skilling and Hvid subdivisions. The project's Danish anchor. | Wilcke 7-2 pp. 152–153 (prints) | `wilcke-1950-moentordning-1514`, `-soelvgylden`, `-nobel-1514`, `wilcke-rhinsk-gylden-1514-standard` | → `1514_moentordning_malmoe.md` (to write) |
| **1514**, 3 Aug | Møntordning for Norge | Christian II | NO | Norwegian coin to be as good as Danish and mutually current; silver and gold weight set; the Danish Møntordning referred to and confirmed for Norway. | Wilcke 7-2 p. 156; Holst (artikler_holst) | — | → 1514 dossier |
| **1515**, 24 Aug | Aabent Brev for Sjælland | Christian II | DK | Renews the 1514 «Skikkelse paa en ny Mønt» for Sjælland; the old Korshvid reduced 4 → 5 → 6 to the Skilling across the complex. | Wilcke 7-2 pp. 156–157 (quotes) | — | → 1514 dossier |
| **1523**, 26 March / 3 Aug | Haandfæstning Frederik I (foreløbig to the Jutland nobility / endelig, Roskilde) | Frederik I / Rigsraad | DK | Coin to be struck «*ligegoett ved Lybsck, Hamborgh oc Lanteholstenn*». | Wilcke 7-2 p. 174, 7-5 p. 309 (quotes); Galster | — | — |
| **1523**, 10 Aug | Forordning / Valvation (Klipping withdrawal) | Frederik I | DK | Old coin to be delivered within 3 weeks and exchanged at real, not nominal, value; the new coin reckoned 1 Mark = 12 Skilling, Gylden = 2 Mark; Klippinge melted into 14- and 6-Penning pieces. | Wilcke 7-2 p. 193; Galster; Ernst (artikler_kghklipp) | — | — |
| **1524**, 25 Feb | Møntordning (Rigsraadets Brev to Jørgen Kock), København | Rigsraad for Frederik I | DK | Gold: Nobel 23 Kt 16/Mark, rhinsk Gylden 18 Kt 72/Mark; silver: Sølvgylden 8/Mark 14 Lod with Mark-subdivision; Klippinge withdrawn. | Wilcke 7-2 pp. 180–187 (prints) | `wilcke-1950-rigsraadets-brev-1524`, `wilcke-1950-moentordning-1524`, `wilcke-rhinsk-gylden-1524-standard`, `wilcke-1950-tabel-1524-soelvgylden` | → `1524_moentordning_frederik_i.md` (to write) |
| **1524** | Kongebrev Frederik I to Jørgen Kock | Frederik I | DK | Executes the Rigsraad ordinance; Nobel at the old fineness (Galster: 23 Kt, «ingen betydning»). | Wilcke 7-2 p. 184 (prints) | `wilcke-1950-kongebrev-1524`, `galster-nobel-1524-*` | → 1524 dossier |
| **1524**, 20 June (Holst: 24 June) | Kongebrev to Bisp Magnus of Hamar | Frederik I | NO | May and shall strike 4-Hvid Skilling and Hvid; 4-Hvid at 5 Lod fine, 96 to the weighed Mark (Holst: 2,40 g; Hvid 300/Mark 4 Lod). | Wilcke 7-2 p. 196 (quotes); Holst table | — | — |
| **1525**, 18 Oct | Tilladelse / Befaling, Oluf Galle (Akershus) to mintmaster Hans Hansen, Oslo | on Frederik I's behalf | NO | Penninge of 4 Hvide, 30 to the rhinsk Gylden (Gylden = 2½ M d.), 4 Lod fine, 112 to the weighed Mark; remedium ½ Quintin / 1–2 pieces; mintmaster's fee 2½ M d. per Mark fine. | Wilcke 7-2 p. 197 (quotes) | — | — |
| **1526**, 8 Nov | Ordning, Oslo (Oluf Galle for the king) | on Frederik I's behalf | NO | «*for bryst og trang … paa penninge*»: Oslo mint continued; Holst: 112/Mark at 3½ Lod. | Wilcke 7-2 p. 199; Holst table | — | — |
| **1527**, Wed. after Midfaste | Regulativ, Vincents Lunge, Bergenhus | on Frederik I's behalf | NO | Bergen: Firehvid 126/Mark (Wilcke: read 106) at 4½ Lod; Hvid 320/Mark at 3½ Lod. | Holst table (artikler_holst) | — | — |
| **1530**, 7 Aug | Befaling to Esge Bille, Bergenhus | Frederik I | NO | Strike coin «*lige goed udi korn oc pagementhe medt then mynth som wy lade slaa her i wort rige Danmark*» — standard by reference to the Danish. | Holst (Dipl. Norv.) | — | — |
| **1532**, 23 Nov | Aabent Brev to Erik Gyldenstierne, Akershus | Frederik I | NO | Strike as many Penninge as he can to pay the garrison, «*paa det samme Pavemint, Korn og Skrot*» as Mogens Gyldenstierne struck when he held Akershus — standard by reference. | Wilcke 7-2 p. 204 (quotes) | — | — |
| **1536**, 30 Oct | Haandfæstning Christian III, møntparagraf | Christian III / Rigsraad | DK | Once peace is made, a coin «*lidelig og gavnlig for Rigens Indbyggere lige ved Fyrstendømmerne*». | Wilcke 7-5 p. 309 | — | — |
| **1537**, 24 Aug | Ordinans (St. Bartholomæi), cap. 10 | Christian III | DK | The king's coin to pass «*til den Værd vi den forsat have … for saadan Værd, som hun er sat for*» — the war coin's nominal value upheld. | Wilcke 7-3 p. 249 (quotes) | — | — |
| **1537**, 21 Oct | Forordning / Reces | Christian III | DK | All coin struck by the king reduced to half: 2-Mark = 1 Mark, Mark = 8 sk., 4 sk. = 2 sk., 2 sk. = 1 sk., Skilling = Søsling; Hvide and small coin to follow; rhinsk Gylden or Joachimsdaler = 3 Mark danske, on pain of 40 Mark. Galster: at first stayed on paper. | Galster (galkult); Wilcke 7-3 p. 254 | — | — |
| **1540** | Reces, cap. 12 «Om myntthen» | Christian III | DK | Exchange ceiling: «*oc schall een rhinsk Gylden eller en Jochimsdaler ikke dyrere wedtzles end for III Mark Danske*». | Wilcke 7-3 (quotes); `moentordning_1541.md` §6 | `wilcke-1950-recess-1540-rhinsk-gylden` | `moentordning_1541.md` §6 |
| **1541**, 20 March | Forordning om Maal og Vægt | Christian III | DK+NO | Weights and measures (Paus prints it). | act (Paus; `sources/paus_…`) | — | `moentordning_1541.md` |
| **1541**, 20 Sept | Møntordning Christian III | Christian III | DK+NO | The dalerfod as a formal standard. | act (T.K. 160 pp. 16–22) · Wilcke 7-4 prints | `wilcke-1950-moentordning-1541` | `moentordning_1541.md` |
| **1544**, 27 Sept | Møntordning (tillæg) for unge Jørgen Koch | Christian III | DK+NO | Full grid (Wilcke prints the table: Gylden, Mark, Skilling … with Finhed, Stk./Mark, weights). | act (T.K. 160 pp. 25–27) · Wilcke 7-4 p. 270 (table) | `wilcke-1950-tillaeg-1544` | `moentordning_1541.md` |
| **1544**, 1–15 Dec | Brev to the Hansestæder on the Flensborg coin | Christian III | SH-k | The types the king intends to strike at Flensborg (incl. Witten, dropped again in 1547). | Ernst (artikler_flenobbe; Sejdelin 865) | — | → 1547 dossier |
| **1547**, 22 Jan | Bestalling mit Müntzordnung, Jørgen Kock d. y., Flensborg (Kolding) | Christian III | SH-k | Four-year appointment; Gyldengroschen and halves, then «*doppelte vnd einfattige schillinge, danach soslinge, vnd dan blaffert vnnd pfennige*»; weights and Guldgylden grid per Wilcke's table. | act (T.K. 160 pp. 28–29) · Wilcke 7-4 pp. 282–283 (prints) | `wilcke-1950-flensborg-1547-bestalling`, `-vaegt`, `-guldgylden`, `wilcke-1950-kock-1547-vier-jahr-schleswig-holstein` | → `1547_bestalling_flensborg.md` (to write) |
| **1550**, 8 July | Instruks for tolder Sander Leyl, Helsingør | Christian III | DK | Sundtold payable in gold, Rosenobler, or 3 full-weight rhinske Gylden per Nobel (with a rebate for 2–3 Nobler). | Wilcke 7-4 p. 286 | `wilcke-1950-sundtold-1550` | — |
| **1551**, 11 Oct | Aabent Brev to the lensmænd «om Mønten» | Christian III | NO | The Norwegian 4-Hvid piece to be taken at full value = 4 Danish Hvide, 36 pieces = 1 Joachimsdaler; refusal forfeits the money and goods, ½ to the king, ½ to the informer. | Wilcke 7-4 p. 305 (quotes) | — | — |

Not instruments, kept out (block A): Kvitteringer 1491–1557 (receipts), Jørgen Kock's report
of 6 May 1530, the 1518 «Klipping» coinage (accounts only, no act), the «separate act of
26 Feb 1524» (not found in Wilcke 7-2), Hans the Elder's interest Forordning 10 Aug 1557 —
see §4.

### §1b · 1559–1625 — next chunk (rows below migrated from the old table)

| Date | Instrument (source's name) | Issuer | Jur. | What it sets | Text seen | refs_pool key | Dossier |
|---|---|---|---|---|---|---|---|
| **1602**, 8 Sept | Forordning | Christian IV | DK | Gold schedule: Portugaløser 6¾/Mark at 23½ Kt, Ungersk Gylden 67/Mark at 23⅓ Kt; the rhinsk Gylden absent — Danish gold redefined on the ducat grid. | Wilcke I (w1d) | `wilcke1-moentordning-1602-guld` | `dk_dukat_portugaloeser_fod.md` §3.1 |
| **1604**, 20 Nov | Møntordning | Christian IV | DK | Moves the tariff only; the 1602 metrology stands. | Wilcke I | `wilcke1-moentordning-1604-nedsaettelse` | `dk_dukat_portugaloeser_fod.md` §3 |

## §2 · Imperial / German

| Date | Instrument | What it sets | refs_pool key | Read it |
|---|---|---|---|---|
| **1490** | Norm of the four Rhenish electors | **71⅓ pieces to the Marck at 18½ Karat** (3,278 g rough / 2,527 g fine) — the Rhenish-gulden form the Empire kept until 1559. | `wilcke6-rhinfyrster-1490-norm` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1495** | Wormser Reichsabschied | Raises the electors' 1490 norm to imperial rank: «*Paa Rigsdagen i Worms 1495 vedtoges denne Møntfod*», reconfirmed at Lindau 1497 and Freiburg 1498. The anchor every pre-1559 Rhenish gulden is measured against. | `wilcke6-worms-1495-reichsabschied` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) · `rhinsk_gylden_fod.md` §1 |
| **1524**, 10 Nov | Reichsmünzordnung, Esslingen (Karl V) | Guldgylden 89 pieces to the 22-carat mark; a silver piece = one Guldgylden at 8 to the 15-lot mark. | `wilcke6-esslingen-1524` | Wilcke I p. 23; [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1535**, 15 April | Kursächsische Münzordnung (sent to Christian III) | Not imperial law but the MODEL Christian III obtained: Gylden 14 Lot 8 Grän 8/Mark; ½ Gylden 16/Mark; Zinsgroschen 7 Lot 9 Gr. 88/Mark; 3-Pf. 4 Lot 117/Mark; Pf. 4 Lot 37/Lot. Antecedent of 1541. | — | Wilcke 7-4 p. 260 (prints the grid) · T.K. 160 pp. 8–15 (scan) |
| **1551**, 14 Feb | Augsburg Reichstag decision → **Valvationstag**, Nürnberg | NOT a standard: sends two councillors and a Wardein from each Kreis to «*prøve hver enkelt Mønt … oplyse dens Vægt, Gehalt og det Antal Kreuzer*». Its output is ASSAY data — the source of the karat figures in Wilcke's comparison table. | `wilcke6-valvationstag-1551` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1551**, 28 July | Møntordning of Karl V | Upholds the electors' 1490 form (71⅓ @ 18½). Tariffs: Thaler (Specie) 68 Kreuzer, 24 Skilling lybsk 60 Kreuzer, rhinsk Guldgylden 72 Kreuzer. | `wilcke6-karl-v-moentordning-1551` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) |
| **1559**, 19 Aug | Møntedikt of Ferdinand I (Augsburger Reichsmünzordnung) | «*fastsattes endelig Møntens Gehalt til **72 Stkr. af den 18½ Karat fine Mark***». Also voids, with six months' notice, «*saavel Christian III.s som Kong Hans' Guldgylden*». Recognises the Dukat as the Reich's gold coin. This is why Danish fineness rises to 18½ from 1563. | `wilcke6-ferdinand-moentedikt-1559` | [Wilcke 6](https://www.danskmoent.dk/wilcke/w6a.htm) · [RMO 1559](https://de.wikipedia.org/wiki/Augsburger_Reichsm%C3%BCnzordnung_von_1559) |

## §3 · Cited in the project, not yet written up here

Generated from a scan of `docs/research/*.md` + `data/shared/*.yml`. Each row is
an instrument our own text already discusses; fill it into §1 or §2 when you next
work on it, rather than researching it afresh.

| Year | Kind | Cited in |
|---|---|---|
| 1496 | Møntordning | `rhinsk_gylden_fod.md` |
| 1497 | Møntordning | `danish_royal_gold_1560_1648.md` |
| 1518 | Møntordning | `christian_iii_danish_coinage_1534_1572.md` |
| 1523 | Reichsabschied | `rhinsk_gylden_fod.md` |
| 1532 | Møntordning | `fuesse.yml` |
| 1534 | Møntordning | `pre_1541_silver_seed_inventory.md` |
| 1539 | Reces | `moentordning_1541.md` |
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
| 1489–1557 | Kvitteringer (Dringelberg 1491, Bryske 1518–20, Lunge 1525, Blech 1529, Fechtel 1536/1557 …) | Wilcke 7-1/7-2/7-4 | receipts and accounts: OUTCOMES, cited inside dossiers |
| 1518 | «Klipping»-udmøntning | Wilcke 7-2 pp. 160–166 | no act — accounts and Blicher's 1518 privilege only |
| 1524, 26 Feb | «separate act» on the 14-Penning piece | `denmark.yml` 8-Gylden-fod bar title | not found in Wilcke 7-2 (p. 191 treats the 14 Penning without a dated act) — the claim needs a source |
| 1530, 6 May | Brev Jørgen Kock → Bergenhus | Galster; Holst | a REPORT on the Malmø mint's fineness — evidence for the 1524 dossier |
| 1531, 30 May | Brunswick Møntordning (Wildemannsthaler) | Wilcke 7-6 | territorial German, not Imperial |
| 1557, 10 Aug | Forordning of Duke Hans the Elder on interest | Wilcke 7-4 p. 308 | 6 % cap — not coinage |
