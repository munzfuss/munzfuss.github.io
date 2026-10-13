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
| **1480**, 12 Sept (Wilcke's resolution of «feria quinta nativitatis Marie») | Møntordning, Arboga (open letter to mintmaster Cornelius Jacobson, Västerås) | Riksråd / Sten Sture | SE | Ørtug 8 lod, 34 kast − 1 = 135 per weighed Stockholm mark; ½ Ørtug 6 lod, 53 kast = 212; hollow penning 5 lod, 3½ mark 2 öre (672); remedia ½–1 quintin; ⅔ Ørtug : ⅓ halves; ≤ 100 weighed marks of penningar a year. Continues 1478/1479; taken over by Hans 1497. Evidentiary, not Danish law. | Wilcke 7-1 s. 118–119 (prints the letter) | `wilcke-1950-arboga-1480-oertug`, `-halvoertug-penning`, `-produktion-cap` | `instruments/1480_moentordning_arboga.md` |
| **1497**, 4 Dec | Møntanordning for Sverige (Hans → mintmaster Michel Johansson, Stockholm) | Hans | SE | Gylden «på Rinske Gylden slagh», 72 to the weighed Cologne mark at **18 karat 1 gren = 18¼ kt** (remedium 3 gren / 1 orth), tariff 1½ Stockholm mark — never struck («*hvilket ej gick i verkställighet*», Styffe); the 1480 silver grid confirmed (Ørtug 8 lod 135/M, ½ Ørtug 6 lod 212/M, penning 5 lod); Slagskat ½ gylden per mark gold, ½ Stockholm mark per mark silver; 20 + 20 mark a year for the king. Wilcke VI's «18½ karat» (after Schive) is corrected by Wilcke VII s. 121 n. 1. | Wilcke 7-1 s. 116–117 (prints the letter); Wilcke 6 ch. 1 (retelling, 18½) | `wilcke-1950-stockholm-1497-gylden`, `-slagskat`, `-18-kvart-karat`; `wilcke6-hans-moentanordning-1497-sverige` (older reading) | `instruments/1497_moentanordning_stockholm.md` |
| **1513**, 22 July | Haandfæstning Christian II, møntparagraf | Christian II / Rigsraad | DK+NO | «*hvad som myntes efter thende dag i Danmark og Norge skal myntes saa at thue mark giør fyldest for en* [rhinsk Gylden]» — the 2 Mark = 1 Gylden rate the 1514 ordinance implements. | Wilcke 7-2 p. 149 (quotes); Galster | `wilcke-1950-haandfaestning-1513` | `instruments/1514_moentordning_malmoe.md` |
| **1513**, 1 Aug | Beskikkelsesbrev (reskript) for Dynes Blicher, Malmø | Christian II | DK | Mintmaster appointment WITH parameters: strike Skilling and Hvid, 1 Skilling = 3 Hvide, 16 Skilling = ½ rhinsk Gylden (Ernst: Gylden = 32 sk.). Wilcke: not carried out. | Wilcke 7-2 p. 149 (quotes); Ernst (artikler_skilltal) | `wilcke-1950-blicher-1513`, `wilcke-1950-ordning-1513-ikke-udfoert` | `instruments/1514_moentordning_malmoe.md` |
| Summer **1514** | Møntordning («Dienis Blicher Brev»), Malmø | Christian II with Rigsraad | DK | Both metals: Nobel 16/Mark 23½ Kt; rhinsk Gylden 72/Mark 18 Kt; Sølvgylden 8½/Mark 14 Lod; Skilling and Hvid subdivisions. The project's Danish anchor. | Wilcke 7-2 pp. 152–153 (prints) | `wilcke-1950-moentordning-1514`, `-soelvgylden`, `-skilling`, `-nobel-1514`, `wilcke-rhinsk-gylden-1514-standard`, `wilcke-1950-lovkompleks-1514-1515` | `instruments/1514_moentordning_malmoe.md` |
| **1514**, 3 Aug | Møntordning for Norge | Christian II | NO | Norwegian coin to be as good as Danish and mutually current; silver and gold weight set; the Danish Møntordning referred to and confirmed for Norway. | Wilcke 7-2 p. 156; Holst (artikler_holst) | `wilcke-1950-norge-1514` | `instruments/1514_moentordning_malmoe.md` |
| **1515**, 24 Aug | Aabent Brev for Sjælland | Christian II | DK | Renews the 1514 «Skikkelse paa en ny Mønt» for Sjælland; the old Korshvid reduced 4 → 5 → 6 to the Skilling across the complex. | Wilcke 7-2 pp. 156–157 (quotes) | `wilcke-1950-sjaelland-1515` | `instruments/1514_moentordning_malmoe.md` |
| **1523**, 26 March / 3 Aug | Haandfæstning Frederik I (foreløbig to the Jutland nobility / endelig, Roskilde) | Frederik I / Rigsraad | DK | Coin to be struck «*ligegoett ved Lybsck, Hamborgh oc Lanteholstenn*». | Wilcke 7-2 p. 174, 7-5 p. 309 (quotes); Galster | — | — |
| **1523**, 10 Aug | Forordning / Valvation (Klipping withdrawal) | Frederik I | DK | Old coin to be delivered within 3 weeks and exchanged at real, not nominal, value; the new coin reckoned 1 Mark = 12 Skilling, Gylden = 2 Mark; Klippinge melted into 14- and 6-Penning pieces. | Wilcke 7-2 p. 193; Galster; Ernst (artikler_kghklipp) | — | — |
| **1524**, 25 Feb | Møntordning (Rigsraadets Brev to Jørgen Kock), København | Rigsraad for Frederik I | DK | Gold: Nobel 23 Kt 16/Mark, rhinsk Gylden 18 Kt 72/Mark; silver: Sølvgylden 8/Mark 14 Lod with Mark-subdivision; Klippinge withdrawn. | Wilcke 7-2 pp. 180–187 (prints) | `wilcke-1950-rigsraadets-brev-1524`, `wilcke-1950-rigsraad-1524-klippinge`, `-soelvmynt`, `-moneta-nova`, `wilcke-1950-tabel-1524-soelvgylden` | `instruments/1524_moentordning_frederik_i.md` |
| **1524** | Kongebrev Frederik I to Jørgen Kock | Frederik I | DK | Executes the Rigsraad ordinance; Nobel at the old fineness (Galster: 23 Kt, «ingen betydning»). | Wilcke 7-2 p. 184 (prints) | `wilcke-1950-kongebrev-1524`, `wilcke-1950-moentordning-1524`, `wilcke-rhinsk-gylden-1524-standard`, `wilcke-1950-kongebrev-1524-markstykker`, `-skilling-hvid`, `galster-nobel-1524-*` | `instruments/1524_moentordning_frederik_i.md` |
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
| **1544**, 1–15 Dec | Brev to the Hansestæder on the Flensborg coin | Christian III | SH-k | The types the king intends to strike at Flensborg (incl. Witten, dropped again in 1547). | Nöbbe (artikler_flenobbe; Sejdelin 865, quotes) | `noebbe-flensborg-1544-brev-hansestaeder` | `instruments/1547_bestalling_flensborg.md` |
| **1547**, 22 Jan | Bestalling mit Müntzordnung, Jørgen Kock d. y., Flensborg (Kolding) | Christian III | SH-k | Four-year appointment; Gyldengroschen and halves, then «*doppelte vnd einfattige schillinge, danach soslinge, vnd dan blaffert vnnd pfennige*»; weights and Guldgylden grid per Wilcke's table. | act (T.K. 160 pp. 28–29) · Wilcke 7-4 pp. 282–283 (prints) | `wilcke-1950-kock-1547-vier-jahr-schleswig-holstein`, `wilcke-1950-flensborg-1547-bestalling`, `-vaegt`, `-guldgylden`, `-smaamoent-hanse`, `-praegeorden`, `-margin-dansk-moent` | `instruments/1547_bestalling_flensborg.md` |
| **1550**, 8 July | Instruks for tolder Sander Leyl, Helsingør | Christian III | DK | Sundtold payable in gold, Rosenobler, or 3 full-weight rhinske Gylden per Nobel (with a rebate for 2–3 Nobler). | Wilcke 7-4 p. 286 | `wilcke-1950-sundtold-1550` | — |
| **1551**, 11 Oct | Aabent Brev to the lensmænd «om Mønten» | Christian III | NO | The Norwegian 4-Hvid piece to be taken at full value = 4 Danish Hvide, 36 pieces = 1 Joachimsdaler; refusal forfeits the money and goods, ½ to the king, ½ to the informer. | Wilcke 7-4 p. 305 (quotes) | — | — |

Not instruments, kept out (block A): Kvitteringer 1491–1557 (receipts), Jørgen Kock's report
of 6 May 1530, the 1518 «Klipping» coinage (accounts only, no act), the «separate act of
26 Feb 1524» (not found in Wilcke 7-2), Hans the Elder's interest Forordning 10 Aug 1557 —
see §4.

### §1b · 1559–1625 (Frederik II · Christian IV to the Krone reform)

«Text seen»: `act (Secher I nr. N, s. P)` = the act read in Secher's Corpus (volume, Secher's
act number, printed page from the running head); `Secher index` = only the Sagregister line
read so far (act text to be read for the dossier); `Wilcke I s. P` = Wilcke 1919 printed page
(= our PDF page + 1); `Wilcke 7-5/7-6 s. P` = Wilcke VII printed page.

| Date | Instrument (source's name) | Issuer | Jur. | What it sets | Text seen | refs_pool key | Dossier |
|---|---|---|---|---|---|---|---|
| **1563** (autumn) → **1564**, 10 Dec | Forordning on the war Klippinge + 7 enforcing acts: Mis. 14 Sept 1563 (nr. 174), Åb. br. 30 Nov 1563 (190), 27 March 1564 (205), 15 Apr (210), Mis. 18 Apr (211), Åb. br. 27 Apr (214), Mis. 28 Apr (215), Åb. br. 10 Dec (240) | Frederik II | DK | Legal tender of the Klippinge struck «udi denne feide»: to be taken «for fulde», on pain of life and the gallows (27–28 Apr 1564); 15 Apr 1564 the peasants to lend their Klippinge to the king against «rund mønt» later. Secher: the Forordning itself is lost, known from nr. 205. | act (Secher I nr. 174–240, s. 243–260) | — | — |
| **1564**, 28 June | Brev (Norske Magasin I p. 434) | Frederik II | NO | The Klipping not to be refused or held «ugæv» in Norway. | Wilcke 7-5 s. 358 (quotes) | — | — |
| **1564**, 11 Dec → **1566**, 1 March | Bestalling Hans Køppelin, Bremerholm (1 year), then letter to the lensmand of Flensborg: Køppelin to strike small coin «som Lybecksk og Hamburgsk Skrot» | Frederik II | DK → SH-k | Flensborg small coin at the Lübeck/Hamburg standard — standard by reference. | Wilcke 7-5 s. 351 | — | — |
| **1567**, 5 Jan · 27 Feb · 11 March | Mis. to the toldere (nr. 346, 357); Åb. br. to the landsdommere (359) | Frederik II | DK | The course at which the «ny dalere» are taken in told; the coin in which law-fines are paid. | act (Secher I nr. 357, s. 331) · Secher index (346, 359) | — | — |
| **1569**, 17 Sept | Mis. to the tolder in Aalborg | Frederik II | DK | Value of a rosenobel paid in told. | act (Secher I nr. 488, s. 418) | — | — |
| **1570**, 26 Oct | Bestalling Baltzer Wegener, Flensborg (1 year) | Frederik II | SH-k | Skilling, Hvid, Blaffert, Søsling and Pfennig at Flensborg; the Lower-Saxon Wardein found the Skilling 3 Penninge too light, the Landdag asked in 1571 to stop the mint. | Wilcke 7-5 s. 353 | — | — |
| **1571**, 26 March | Mis. | Frederik II | DK | Told and lastpenge in the Sound to be taken in old dalers. | Secher index (nr. 569) | — | — |
| **1572**, 16 June | Aabent Brev (Kiøpnehafn) | Frederik II | DK | Every piece re-rated at half its name: Mark = 8 sk. (½ Mark), 8 sk. = 4, 4 = 2, 2 = 1, Skilling = Søsling, 4 Hvid = 2, 2 = 1; the old daler = 32 sk. = 2 Mark of 16 sk.; penalty 500 daler; export of the coin forbidden on forfeiture (§ 3–4). Wilcke: a 25 % reduction (Mark from ⅓ to ¼ daler), not 50 %. | act (Secher I nr. 609, s. 504–505) · Wilcke 7-6 s. 373–374 (prints) | `secher-ccd-1-609-1572-omsaettelse`, `-udfoersel`, `wilcke-1950-1572-nedsaettelse-25-pct` | `instruments/1572_aabent_brev_moentens_omsaettelse.md` |
| **1572**, 9 Sept · 15 Sept · **1573**, 29 Jan · 28 March · **1574**, 10 March | Mis. ×4 + Åb. br. on the dalers in told | Frederik II | DK | 9 Sept 1572: on each new daler take as much as it is lighter than an old daler; 29 Jan 1573: the new Netherlands dalers «fast alle vegne ugangbar» — told only in old dalers; 10 March 1574: course of the new Netherlands daler. | act (Secher I nr. 621 s. 522, nr. 636 s. 532) · Secher index (623, 648, 695) | — | — |
| **1574**, 26 Jan | Stadfæstelse of the Bergen burghers' «Skik og Ordning» | Frederik II | NO | After the coin change: where 3 Mark was paid for 1 Daler before, no more than 1 Daler = 2 Mark «som Mønten nu er omsat». | Wilcke 7-6 s. 386 (quotes) | — | — |
| **1576**, 14 Dec · **1578**, 26 Nov · **1581**, 9 Nov | Åb. br. on the reckoning of jordskyld and husleje (Nyborg), of the sagemark, of taxes, jordskyld and landgilde «efter møntens forandring» | Frederik II | DK | Accounting conversion rules after the 1572 change. | Secher index (II nr. 45, 139, 264) | — | — |
| **1580**, 22 Sept | Mis. to Copenhagen, Helsingør, Slangerup | Frederik II | DK | Rosenobler, dukater «eller andit guld» to be taken from the hofsinder at the value they have been current for in the realm. | act (Secher II nr. 214, s. 172) | — | — |
| **1581**, 4 May | Mis. to the tolder in Helsingør | Frederik II | DK | The coin he may take instead of gold. | Secher index (II nr. 242) | — | — |
| **1582**, 12 Jan | Møntanordning / Befaling for mintmaster Poul Gulden | Frederik II | DK | The daler of 4 Mark = 64 ß restored; Mark and ½ Mark at 9 lod 15 gren (614,58 ‰) at the old weight (24/M), 2 ß 5 lod 100/M, 1 ß 3 lod 132/M, Hvid 2 lod 12 gren 370/M, each with the mark fine «udbragt til» (39 M 2 Hvid / 40 / 44 / 46 M 4 ß) and the king's gain at a silver price of 8 Dlr 2 M 8 ß; only the king's silver, no further lowering without order. Confirmed for Norway 1 Aug 1589; repeated for Metzner 1 Aug 1594 / 1597. Not in Secher (Kancelli order; RA. T.K. 160 no. 8). | Wilcke 7-6 s. 397–399 (renders the decision); Wilcke I s. 55, 59, 61; Galster | `wilcke-1950-befaling-1582-moentgrid`, `wilcke-1950-metzner-1597-samme-indhold`, `wilcke-1919-befaling-1582-daler-4-mark` | `instruments/1582_befaling_poul_gulden.md` |
| **1582**, 12 Feb | Åb. br. | Frederik II | DK | Course of the rosenobel at the Øresund told. | Secher index (II nr. 277) | — | — |
| **1586**, 30 Jan | Mis. to Copenhagen and Helsingør | Frederik II | DK | The imported new dalers «ikke skulle være så gode, som sig burde». | Secher index (II nr. 422) | — | — |
| **1586**, 6 June | Forordning for Norway | Frederik II | NO | How byskat, jordskyld and landgilde are collected in Norway since the coin change (1 Mark = 8 sk. etc., the coin doubled in reckoning). | Wilcke 7-6 s. 386 | — | — |
| **1590**, 20 Nov | Mis. to the toldere | Christian IV (regency) | DK | The rosenobel has fallen from 16 to 13 Mark danske; add ¾ daler per rosenobel taken in told, or take 4 dalers instead. | act (Secher II nr. 549, s. 578) | — | — |
| **1593**, 20 May | Møntanordning | regency | DK | The Mark at 7,3 g of 14-lot silver (Wilcke: 6,3990 g fine). | Wilcke I s. 48 | — | — |
| **1593**, 14 Sept · **1594**, 1 Aug | Bestalling Andreas Metzner (Kolding) · Møntordning for Metzner | regency | DK | Metzner to set up the Münzdruckwerk; the 1594 ordinance «af ganske samme Indhold» as 12 Jan 1582. | Wilcke I s. 57; Wilcke II (w2ref) | — | — |
| **1602**, 12 May | Åb. br. om dalernes værdi | Christian IV with Rigsraad | DK+NO | Every daler = 33 sk. lybsk = 66 sk. danske in all trade and payment; the ortsdaler and the Danish Mark pieces excepted, «ved sin sedvonlige verd». | act (Secher III nr. 173, s. 150–151) · Wilcke I s. 61, 66 | `secher-ccd-3-173-1602-daler-66-sk` | `instruments/1602_forordninger_moentreform.md` |
| **1602**, 25 June | Forordning (German original, signed) — Schwabe's Beskikkelse the same day | Christian IV | DK | Silver grid: Mark 24/M 9 9/18 lod (593,75 ‰); 4 ß 76 or 78/M 7¼ lod; 2 ß 108/M 4¾; 4 Hvid 116/M 3¼; 1 ß 136/M 2¾; Søsling 220/M 2 lod; Hvid 312/M 1½; Blaffert copper 400/M; each line with the mark fine «udbragt til» (reckoned at a Mark of 16 ß). Wilcke: a proposal copied into an ordinance. | Wilcke I s. 64–66 (table s. 65) | `wilcke-1919-forordning-1602-25-juni-forslag` | `instruments/1602_forordninger_moentreform.md` |
| **1602**, 8 Sept | Forordning (the full system) | Christian IV | DK | Gold with statutory values: Portugaløser 6¾/M 23½ kt = 17 Dlr., Ungersk Gylden 67/M 23⅓ kt = 1⅝ Dlr., 8 / 6 / 4 Dlr. Klipping 13¼ / 17¾ / 24 per M at 22½ / 22⅙ / 20 kt; silver in two tiers — grov Mark 25/M 9½ lod = 16½ ß, grov 4 ß 80/M 7¼ lod, 2 ß 112/M, 1 ß 146/M, Søsling 230/M, Hvid 328/M, and «fine» Mark 38/M, 8 ß 80/M, 4 ß 160/M at 14 2/9 lod (daler fineness, light). The rhinsk Gylden absent. | Wilcke I s. 68–69 (table s. 69) · w1d | `wilcke1-moentordning-1602-guld`, `wilcke-1919-forordning-1602-8-sept-fin-moent` | `instruments/1602_forordninger_moentreform.md` · `dk_dukat_portugaloeser_fod.md` §3.1 |
| **1604**, 20 Nov | Møntordning | Christian IV | DK | «Enslydende» with 8 Sept 1602 except: the three fine silver sorts omitted; gold values in dalers unstated; Portugaløser → 16 Dlr., Ungersk Gylden → 1 9/16 Dlr.; 4 Dlr. Klipping 24½/M at 20⅓ kt (8,087 g fine), still 4 Dlr. | Wilcke I s. 74–75 | `wilcke1-moentordning-1604-nedsaettelse` | `instruments/1602_forordninger_moentreform.md` · `dk_dukat_portugaloeser_fod.md` §3 |
| **1605**, 17 March | Frdg. om møntens forandring | Christian IV | DK | — | Secher index (III nr. 208) | — | — |
| **1605**, 8 July · 4 Aug | Frdg. (both realms) on the Slesvig coin; Frdg. on the Sønderborg coin | Christian IV | DK+NO | The Slesvig 4-skilling set at the Lüneburg Kreistag to 4 lybske penninge, the skilling to 2 — current for six months, then withdrawn; the same to apply in the realms. | act (Secher III nr. 214, s. 188–189) · Secher index (216) | — | — |
| **1605**, 31 Aug | Møntordning | Christian IV | DK | «Enslydende» with 20 Nov 1604 plus the three fine sorts (Mark, 8 ß, 4 ß at 14 2/9 lod) restored per 8 Sept 1602; the Renteskriver's endorsements on the draft. | Wilcke I s. 75–76 (quotes the endorsements) | `wilcke-1919-moentordning-1605-31-aug` | `instruments/1602_forordninger_moentreform.md` |
| **1607**, 28 May · **1609**, 28 Sept | Bestalling og Ordning / Müntz-Ordnung for Hans Flemming, Helsingør | Christian IV | DK | Mint ordinance «an schrott, Korn und Gewichte»; assay box (Dutch model); minting on English and Dutch merchants' account. | Wilcke I s. 77 | — | — |
| **1609**, 3 Feb | Mandat om møntens forandring | Christian IV with Rigsraad | DK+NO | Every daler in Denmark and Norway = 34 sk. lybsk = 68 sk. danske; 4 Mark … (continues). | act (Secher III nr. 295, s. 253) · Wilcke I s. 137 | — | — |
| **1609**, 4 Oct | Frdg. | Christian IV | DK | Foreign small coin, withdrawn at its own mints, forbidden in trade. | Secher index (III nr. 309) | — | — |
| **1610**, 1 Feb · 28 Feb · 2 Nov · **1611**, 8 May | Forordninger Johan Adolf (Gottorp) | Duke Johan Adolf | SH-d | The subjects' demand to pay in the duke's own coin; Wilcke cites them for the ducal Mark coinage's difficulties. | Wilcke I s. 144 | — | — |
| **1610**, 3 April | Frdg. om møntens forandring over alt Danmarkes og Norges riger | Christian IV | DK+NO | The rigsdaler rising in Germany to 74 sk. danske and above — raised here likewise, lest dalers leave the land; printed Waldkirch 1610, 7 leaves. | act (Secher III nr. 318, s. 272) · Wilcke I s. 107 | — | — |
| **1613**, 15 May | Mis. to toldere and sisemestre in Denmark and Norway | Christian IV | DK+NO | Told only in rigsdaler, not in gold, Mark pieces or other coin — except rosenobel and goldgylden for ship toll; small coin received to be changed into rigsdaler. | act (Secher III nr. 395, s. 404) | — | — |
| **1616**, 4 July | Frdg. om mønten | Christian IV | DK | — | Secher index (III nr. 433) · Wilcke I s. 122 | — | — |
| **1616**, 21 Oct | Contract Count Ernst of Holstein-Schauenburg ↔ Gabriel de Valentza, Altona | Count Ernst | Schauenburg (HRE) | 150 Mark fine silver weekly to the Altona mint, struck as Schreckenberger 47 to the 9 3/16-lot Mark (c. 5 g, 2,85 g fine); fee ⅓ ß lybsk per Mark. | Wilcke I s. 34 | — | — |
| **1618**, 5 April | Åb. br. om mønten — the Møntordning given as the Bestillinger of Post and Schwabe (Wilcke: unpublished) | Christian IV | DK | Gold: double Krone = 3 Rdl., Krone 1½, ½ Krone 3 rigsort; 22 karat; 39 / 78⅔ / 160 to the lødig mark; Slagskat 2½ rigsort per mark fine. Silver: Krone «al tid» = 1½ rigsdaler, ½, ort, ⅛, 1/16 Kroner at 13¾ lod, 6 257/1400 / 12 323/700 / 25 1/7 / 52 / 104½ to the mark; 4 ß 106/M 7 lod, 2 ß 150/M 4½, 1 ß 196/M 2½, Søsling 300/M 1¾, Hvid 415/M 1½ «af payement»; Slagskat 2¼ rigsort per mark fine + 50 Rdl. per 1 000 supplied; 4 000 specie dalers a year at the Lübeck/Hamburg standard; mintmark; secrecy. | act (Secher III nr. 487, s. 528–531) · Wilcke I s. 151–161 (table s. 152) | `secher-ccd-3-487-1618-soelvkrone`, `-guldkrone`, `-payement`, `wilcke-1919-kronefod-tabel`, `wilcke-1919-1618-hemmelig-moentordning` | `instruments/1618_kronemoent_indfoerelse.md` |
| **1618**, 1 May | Frdg. om forhøjelse af rigsdalernes værdi | Christian IV with Rigsraad | DK+NO | Rigsdaler in specie = 84 ß danske (from 68); whole / half Mark pieces stay at 20 / 10 ß; foreign counterfeiting of Mark pieces to be prosecuted. | act (Secher III nr. 495, s. 541) · Wilcke I s. 157 | `secher-ccd-3-495-1618-rigsdaler-84`, `wilcke-1919-tarifkaede-1618` | `instruments/1618_kronemoent_indfoerelse.md` |
| **1618**, 12 July | Åb. br. om ny mønt (printed patent, read at the things) | Christian IV | DK+NO+duchies | The Danish Kroner «af gout sølf» announced against foreign counterfeits of the Mark: Krone = 1½ rigsdaler in specie = 126 ß danske now; ½ Krone 3 rigsort; ortskrone 1½ rigsort; the Krone follows the rigsdaler's changing course (§ 2); officials to trace counterfeits (§ 3). | act (Secher III nr. 500, s. 546–547) · Wilcke I s. 155–156 | `secher-ccd-3-500-1618-krone-126`, `wilcke-1919-patent-12-juli-1618` | `instruments/1618_kronemoent_indfoerelse.md` |
| **1618**, 12 Dec | Mandat (with Lübeck) § 5; «Ordning om 2 ß og Groschen» | Christian IV | SH-k | Foreign 4 ß (and 2 ß, 1 ß) below the Brunswick Kreis resolution forbidden. | Wilcke I s. 39, 162 | — | — |
| **1619**, 8 Jan | Frdg. | Christian IV | DK | Value at which various fireskillingsstykker are taken. | Secher index (III nr. 512) · Wilcke I s. 179 | — | — |
| **1619**, 4/5 April | Instruks (mint, «alle de nye Udregninger») | Christian IV | DK | 1 ß at 13¾ lot; the new calculations for the small coin. | Wilcke I s. 163 | — | — |
| **1619**, 8 April | Frdg. om guld- og sølvkroner og mindre møntsorter («møntordinantie») | Christian IV | DK+NO | The Krone grid in gold and silver and the smaller sorts, «paa det mønten … al tid kand blifve udi en statu». | act (Secher III nr. 523, s. 573) · Wilcke I s. 167 | — | → Krone dossier |
| **1619**, 7 Sept | Plakat | Christian IV | DK | Course 6½ Mark; the «slagne Daler» first officially called Rigsdaler. | Wilcke I s. 48 | — | — |
| **1619**, 16 Nov · 20 Nov | Frdg. om mønten · Møntmesteranordning (Schwabe's Bestalling) | Christian IV | DK | The Forordning with its mintmaster's ordinance (2 ß weight; 1 ß reduced from 13¾ to 5 lot). | Secher index (III nr. 541) · Wilcke I s. 12, 183 | — | — |
| **1620**, 20 July | Møntedikt for the duchies | Christian IV | SH-k | Dobbeltskillinger (4 ß d.) taken only by weight per the attached Specifikation (old stamped pieces at full value); the Daler at most 33¼ ß l. = 104 ß d. | Wilcke I s. 187 | — | — |
| **1621**, 20 Feb | Frdg. om mønten | Christian IV | DK | — | Secher index (III nr. 581) | — | — |
| **1622**, 10 May | Møntordning | Christian IV | DK | — | Wilcke I s. 199 | — | — |
| **1622**, 16 Aug | Frdg. om de forskellige mønters værdi («nerverende myntordning») | Christian IV with Rigsraad | DK+NO (Paus s. 614) | Tariff: rigsdaler in specie 6 Mark (Mark = 16 ß); stykke van achten 5 Mark 14 ß; rosenobel 4 Rdl.; ungarsk dukat 10½ Mark; goldgylden 7½ Mark; Danish gold or silver Krone 9 Mark (= 144 ß); Danish Mark piece 1 Mark 5 ß; 12 / 8 ß as struck; rytter / nelleblad 4 ß → 3½ ß, 8 ß → 7 ß; 1 ß = 1 ß; pundepenninge 12 sletdaler; fines; foreign merchants' coin watched. | act (Secher IV nr. 20, s. 20–22) · Wilcke I s. 224 | `secher-ccd-4-20-1622-tarif` | `instruments/1624_moentordning_kobenhavn.md` §6 |
| **1622**, 15 Oct · 24 Oct | Frdg. om fremmede fire-, to- og enskillingsstykker · Frdg. om fremmede daleres værdi | Christian IV | DK+NO | 15 Oct: foreign payement 4 ß and new 2 ß / 1 ß not struck in the realm, the duchies, Hamburg or Lübeck demonetised. 24 Oct: foreign dalers tariffed by inscription (Swedish 4 Mark 1612 = 59 ß, Dutch 76½ ß, Albertus 90 ß …). | acts (Secher IV nr. 33 s. 34; nr. 36 s. 35–36) · Wilcke I s. 207 | — | `instruments/1624_moentordning_kobenhavn.md` §6 |
| **1622**, 25 Oct | Mandat wegen der kleinen Münzen (duchies) | Christian IV | SH-k | The neighbours' light sorts forbidden; the king's 2 and 4 ß at a Rigsdaler of 36 ß l. | Wilcke I s. 204–205; Wilcke II (w2ref) | — | — |
| **1623**, 28 Feb | Münz-Edict (duchies) | Christian IV | SH-k | Daler = 3 Mark lybsk. | Wilcke I s. 211 | — | — |
| **1623**, 14 Dec | Patent (duchies) — «Münz-Calada» | Christian IV | SH-k | General reduction of the bad coin against the new good one; a term set. | Wilcke I s. 30 | — | — |
| **1624**, 14 Feb | Møntordning for mønten i København (Sjæll. Reg. 17, 539–40; entered after Schwabe's Bestalling of 21 Aug 1624) | Christian IV | DK (København mint) | Silver grid at 13¾ lod: Krone 6 257/1400, ½ Krone 12 257/700, orts Krone 24 257/300 (Wilcke: /350) per løde mark, «udbragt til» 10 Rdl. 34 ß at a daler of 100 ß; 12 ß 76/M, 8 ß 115/M at 13¾ lod; 2 ß 180/M 4½ lod; 1 ß 254/M 2½ lod; copper Søsling 150/M, Hvid 231/M. Wilcke: the 4-ß Opgæld legalised — daler 100 ß, Krone still 144 ß. | act (Secher IV nr. 107, s. 144–145; fractions verified on the page image) · Wilcke I s. 217–221 (table s. 218) | `secher-ccd-4-107-1624-kroner`, `-12-8-skilling`, `-smaamoent`, `wilcke-1919-moentordning-14-feb-1624` | `instruments/1624_moentordning_kobenhavn.md` |
| **1625**, 22 Jan | Frdg. om nedsættelse i værdi af syv- og halvfjærde-skillinger så og om fremmede efterslagne mønters indførelse | Christian IV | DK+NO | 7 ß and 3½ ß (rytter / nelleblad / nøgle) to 6 and 3 ß from St. Hans dag 1625, redeemable at the Rentekammer at full value until then; import of counterfeit ½ Kroner, 12 and 8 ß forbidden; enforcement §§ 3–4. Superseded by 4 May (6⅔ / 3⅓ ß). | act (Secher IV nr. 138, s. 193–195) · Wilcke I s. 225–226 | `secher-ccd-4-138-1625-afsaettelse` | `instruments/1624_moentordning_kobenhavn.md` |
| **1625**, 24 April | Mis. til tolderne i Helsingør | Christian IV | DK (Sound toll) | 4 rigsdaler in specie to be taken instead of each rosenobel due in told, «indtil videre». | Secher IV nr. 154, s. 216–217 (summary heading only) | — | `instruments/1624_moentordning_kobenhavn.md` |
| **1625**, 4 May | Frdg. om mønten (printed patent; «med voris Danmarkis rigis raads raad oc efter deris begeringe», after the Rigsraad's Betænkning of 15 Feb 1625) | Christian IV with Rigsraad | DK+NO + «underliggende lande» | Rigsdaler = 6 slette Mark (96 ß) «oc icke mere»; Krone = 2 sletdaler = 8 Mark (128 ß); ½ Krone 4 Mark (64 ß); orts Krone ½ sletdaler; ½ orts Krone 1 Mark; 24 ß → 20; new Mark / 16 ß → 13⅓; 12 ß → 10; 6 ß → 5; 8 ß → 6⅔; 4 ß → 3⅓; 3½ ß (rytter / nelleblad / nøgle) → 3⅓, doubles 6⅔; old Mark piece 20 ß; gold per earlier ordinances. Krone coinage ceased summer 1625 (Wilcke). | act (Secher IV nr. 158, s. 229–230) · Wilcke I s. 231–234 | `secher-ccd-4-158-1625-rigsdaler-krone`, `-smaamoent`, `wilcke-1919-forordning-4-maj-1625`, `wilcke-1919-rigsraad-1625-romerske-fod` | `instruments/1624_moentordning_kobenhavn.md` |

Not instruments, kept out (block B): Haandfæstning 1559 (no coinage clause, Wilcke 7-5 s. 308),
Bestalling Køppelin 15 Sept 1563 (1 year, no grid), Isensnider 1565, Kort N. 1576, Delhusen 1577,
Brucker 1581 (staff), Svendborg byskat 1578, counterfeit warning 1584, the coronation letters 1596,
export ban 12 July 1603, the Dutch Plakat 1606, Charisius 1607, the valvations 1613/1620/1623,
the Westphalian Kreis decision 7 May 1618, the Mecklenburg–Hanse union 23 Apr 1620, Rigsraad's
Betænkning 15 Feb 1625 — see §4.

### §1c · 1625–1700 (Christian IV late · Frederik III · Christian V)

«Text seen»: `act (Secher IV nr. N, s. P)` as in §1b; `Wilcke II kap. X, s. P–Q` = the 1924
volume's section whose printed range the danskmoent HTML heading gives (no page breaks inside —
SOURCES §13.17); `Mordhorst` = the Nationalbanken digest with quotations (danskmoent `mord`);
`Schou Bd 1` = Chronologisk Register 1670–99 (Fraktur OCR; the page of each act still to be
located and checked against the image).

| Date | Instrument (source's name) | Issuer | Jur. | What it sets | Text seen | refs_pool key | Dossier |
|---|---|---|---|---|---|---|---|
| **1627**, 22 Dec | Forordning on minting from Bruchsilber | Christian IV | DK | Silver objects offered at the mint bought and struck into 6 ß at c. 1½ Dlr. over the Speciemøntfod per Mark fine. | Wilcke II kap. 1, s. 49–58 | — | — |
| **1628**, 28 April | Bestalling Anders Pedersen, mintmaster in Norway (Christiania) | Christian IV | NO | «daller af Brandtsølv» from the Kongsberg silver: 15 Lod 2 Quintin (15½ lot) fine; 9 to the lødig Mark, halves 18, Ortsdaler 36, ½ Ort 72; remedium 1 Gren to be made good in the next melt. | Wilcke II kap. 2.1, s. 151–156 (quotes) | — | — |
| **1628**, 15 Nov | Müntzordnung (with Schwabe's Erklæring of 13 Nov) | Christian IV | DK | 6 ß from Bruchsilber; gold incl. Rosenobler at 24 to the 20-karat Mark (Wilcke: wrongly — the old ones were 26). | Wilcke II kap. 1, s. 49–58 | — | — |
| **1629**, 8 April | Frdg. | Christian IV | DK | No coin to be used but that which can be paid in tax. | Secher index (IV nr. 341?) · Wilcke II | — | — |
| **1629**, 10 Oct | Frdg. om møntvæsenets bedre indretning | Christian IV | DK | — (text not yet read) | Secher index (IV nr. 341) · Wilcke I s. 12; Wilcke II kap. 1 | — | — |
| **1630**, 21 Jan | Møntordning for mønten i København | Christian IV | DK | 8 ß: 98 to the Mark at 14 lot, 12 = 1 rigsdaler specie; 4 ß: 198 to the Mark at 14 lot, 24 = 1 rigsdaler; 2 ß … (continues). | act (Secher IV nr. ?, s. 504) · Wilcke II kap. 1, s. 58–82 | — | → dossier candidate |
| **1630**, 14 April | Patent for the duchies on the reduced and valued Danish VI-Schilling pieces | Christian IV | SH-k | Tariff of the Copenhagen 6 ß in the duchies. | Wilcke II kap. 1, s. 58–82 (quotes) | — | — |
| **1631**, 26 July | Møntordning | Christian IV | DK | — | Wilcke II kap. 1, s. 58–82 | — | — |
| **1635**, 27 Aug | Åb. br. om udmøntning af ungarske dukater | Christian IV | DK | Hungarian ducats to be struck. | Secher index (IV) · Wilcke II kap. 1 | — | — |
| **1639**, 8 June | Frdg. om guldmønten m. m. | Christian IV | DK | The gold coin raised (the 1640 act calls it «guldmyntens forhøielse»); gold tariff table per SOURCES §3. | Secher index (V nr. 31) · Wilcke II | — | — |
| **1639**, 10 July | Åb. br. om forhøjelse af kursen på goltgylden | Christian IV | DK | Goldgylden course raised. | Secher index (V nr. 41) | — | — |
| **1640**, 18 May | Frdg. om nedsættelse af guldmøntens værdi | Christian IV | DK | Gold coin back to its value before 8 June 1639. | act (Secher V nr. 56, s. 56) · Wilcke II | — | — |
| **1640**, 17 Sept · **1641**, 31 Dec | Bestalling Simon Timpff, Glückstadt, and its renewal | Christian IV | SH-k | Renewal adds 8 ß l. (1 Marck d.) at 48 to the 13-lot Mark; Wilcke prints the whole Glückstadt system (Dukater 67/Mark 23½ Kt …). | Wilcke II kap. 3, s. 218–245 (table) | — | → dossier candidate |
| **1641**, 17 June | Åb. br. (Kroneborg) | Christian IV | DK | Import of foreign «penge af payement» not of the value they pass for forbidden, at Helsingør and in the land. | act (Secher V nr. 97, s. 89) | — | — |
| **1641**, 2 July · 16 Oct · **1642**, 11 March | Befalinger to Statholder Christoffer Urne (Christiania mint) | Christian IV | NO | Small coin to be struck from the Kongsberg silver «udi Rixdalers Verdt»; 16 Oct: 2, 4, 8 ß «efter indlagte Mønt Ordinance paa Skrod og Lod» (the 1630 København grid — 8 ß 98/M, 4 ß 198/M, 2 ß 398/M at 14 lod); 11 March 1642: continue the three sorts. | Wilcke II kap. II.3 (quotes; R. A. Norske Tegnelser VII) | `wilcke-1924-kap2-3-befaling-1641-rixdalers-verdt` | `instruments/1643_muentzordnung_christiania.md` |
| **1643**, 25 Feb | «Der zu Dennemarcken, Norwegen Kønigl. Maytt. Müntzordnung … dess Müntzmeister Peter Gronners bestalling ein verleibet» (the Christiania mint account's title) | Christian IV | NO (Christiania mint) | Small coin on the København 1624 grid: 2 ß 180/M 4½ lod, 1 ß 254/M 2½ lod; 8 ß at the 1629/1641 gross weight (98/M, 2,386 g) with the 1624 Krone-8-ß fine weight (12 lod inferred); 4 ß added (198/M at 12 lod inferred); specie 800 Rdl. per 100 Mark at 14 1/18–14 2/18 lod, remedium 2 Pf.; Forpagtning: silver at 9 Rdl. 36 ß per Mark fine, Overskud 61 / 40½ / 16 Rdl. 18 ß per 100 Mark alloyed (8 / 2 / 1 ß). In force in the Norwegian accounts to 1667. Act not printed; Wilcke's table s. 172 missing from the transcription. | Wilcke II kap. II.3 (s. 165–174) + II.7 | `wilcke-1924-kap2-3-gruener-forslag-1642`, `-moentordning-1643-titel`, `wilcke-1924-kap2-7-moentordning-1643-afgifter` | `instruments/1643_muentzordnung_christiania.md` |
| **1643**, 27 Feb | Christian IV's store Reces, II. bog 17. kap. § 1 «med mynten» | Christian IV | DK | Burgomasters and council to see that foreign merchants trade and pay in current coin, and to prosecute offenders (after Frdg. 10 Oct 1629 § 11). A policing clause, no parameters. | act (Secher V nr. 143, s. 160–161) | `secher-ccd-5-143-1643-reces-mynten` | `instruments/1643_muentzordnung_christiania.md` §3 |
| **1645**, 12 Dec · **1646**, 26 Sept | Skrivelse, confirmed by Forordning (Duke Frederik, Gottorp) | Duke Frederik III of Gottorp | SH-d | No one bound to take more than 10 Marck in the new Markstykker; the duke had the minting stopped. | Wilcke II kap. 3, s. 218–245 | — | — |
| **1647**, 10 Dec | Frdg. om guld- og sølvmøntens kurs | Christian IV | DK | Gold and silver tariff: old Jacobus 5 rdl 1 ort, new Jacobus 4 rdl 1 ort, half rider 5 rdl 1 ort(?), goldgylden 1 rdl 1 ort, French crown 2 rdl, French pistole 3 rdl 3 ort; rixdaler 6 Mark ½ «udi mynt». | act (Secher V nr. 337, s. 546) · Wilcke II kap. 1.3, s. 82–101 | — | — |
| **1648**, 14 Jan | Ulfeldt's reduction of the København 2 ß and 1 ß (Wilcke: «nedsatte Corfits Ulfeldt disse Mønters Vægt») | Rigshofmester Corfits Ulfeldt | DK (København mint) | 2 ß 192/M (= 4 Rdl. the Mark gross), 1 ß 256/M (= 4 sletdaler) — from the 1643 grid's 180 / 254; the København Skilling standard for Frederik III's reign. | Wilcke II kap. II.7 (retelling; instrument not seen) | `wilcke-1924-kap2-7-ulfeldt-1648` | `instruments/1643_muentzordnung_christiania.md` §6 |
| **1648**, 21 March | Frdg. af rigens råd om guld- og sølvmønt | Rigsraad (interregnum) | DK | Amends the Forordning of 10 Dec 1647 after complaints. | act (Secher V nr. 339, s. 546–547) · Wilcke II kap. 1.4 | — | — |
| **1648**, 8 May / 6 July | Haandfæstning Frederik III § 48 | Frederik III / Rigsraad | DK | A change in the coin only with the Rigsraad's consent. | act (Secher V nr. 346, 348, s. 553 ff.) | — | — |
| **1650**, 10 Aug | Åb. br. om nedsættelse af dukaters værdi | Frederik III | DK | Ducat course reduced. | Secher index (V nr. 451) · Wilcke II kap. 1.4 | — | — |
| **1651**, 9 May | Ordre on striking whole and half rigsdaler, slette daler and rigsorter | Frederik III | DK | Minting order (types). | Secher index (VI nr. 16) | — | — |
| **1651**, 14 Jan | Bestalling Frederik Grüner, Christiania | Frederik III | NO | Rigsdaler «efter hollandsk Skrot og Korn»; 2 and 1 ß as ordered in Christian IV's time. | Wilcke II kap. 2.5, s. 179–186 | — | — |
| **1651**, 15 Oct · 24 Oct | Åb. br. ×2 | Frederik III | DK | Import of foreign pajement forbidden (Helsingør, as 1641); import of «styk von achten» forbidden. | act (Secher VI nr. 42, 45, s. 74–75) | — | — |
| **1652**, 19 Feb | Mis. | Frederik III | DK | Søslinger and Hvider forbidden. | Secher index (VI nr. 60) | — | — |
| **1652**, 13 April | Ordre | Frederik III | DK | Slette daler to be struck «paa lige skrot og lod» as the Norwegian 2-Mark pieces, so both realms' coin is of equal value. | act (Secher VI nr. 70, s. 89) | — | — |
| **1652**, 20 May | Ordre | Frederik III | DK | Enskillinger at the value of the last struck in Christian IV's time. | Secher index (VI nr. 77) | — | — |
| **1653**, 29 Aug | Ordre on the fineness for 2- and 1-skillinger, dukater and guldkroner | Frederik III | DK | Fineness fixed (text to read). | Secher index (VI nr. 130) | — | — |
| **1654**, 16 Feb | Wardein-Bestalling Christian Herbach | Frederik III | DK | Buys all Bruchsølv and gold offered; Guldkroner from the gold, Sletdaler from the silver «efter hidtidig Korn og Skrot». | Wilcke II kap. 1.5, s. 113–133 (quotes) | — | — |
| **1657**, 15 July · **1659**, 19 May | Bestalling Jacob Schwieger, Glückstadt + addition | Frederik III | SH-k | Rigsdaler, halves, Orter, Dukater; 1659: Kroner / 2-Marck pieces «efter dansk Korn og Skrot», 10½ to the Mark at 10 Lod 3 Quintin fine, fee 12 ß l. per Mark fine. | Wilcke II kap. 3.3 (w2c3) | — | — |
| **1658**, 2 Jan | Frdg. (with the Rigsraad) | Frederik III | DK | Every ducat to pass for 12 Mark danske until further notice; printed, read at Sorø birketing; Paus s. 926. | act (Secher VI nr. 313, s. 365) · Wilcke II kap. 1.5 | — | — |
| **1658**, 6 Feb | Frdg. om fri udmøntning på kongens mønt | Frederik III | DK | Anyone may have his own gold or silver struck at the royal mint into ducats, slette daler and 2-Mark pieces «efter den skrot og korn, som myntemesteren befalet er». | act (Secher VI nr. 319, s. 368) | — | — |
| **1660**, 18 April | Patent (Flensborg) | Frederik III | SH-k | The 14 and 7 ß l. pieces of 1644–45 (Hebrew legend) to be accepted. | Wilcke II kap. 3.3 (w2c3) | — | — |
| **1660**, 20 Sept | Kgl. Patent «der Müntz halber und Absetzung der Cronen» | Frederik III + Christian Albrecht | SH-k+SH-d | The Krone reduced in the duchies after the war. | Wilcke II kap. 1.6 (w2a6) | — | — |
| **1661**, 20 Feb | Forordning at Toldens Opbørsel skal være udi Rixdal. Mynt in Specie | Frederik III | DK+NO | Told above 1 rdl to be paid in specie, per the Told-Ruller. | Mordhorst (f3) | — | — |
| **1665**, 10/22 Jan | Reskripter (Kammerkollegiet; mintmaster Herbach) | Frederik III | DK | Small coin under 2-Mark pieces not to be struck until further notice; dies to the treasury. | Mordhorst (f3) | — | — |
| **1665**, 6 May | Reskript | Frederik III | NO | A specie coinage at Christiania. | Mordhorst (f3) | — | — |
| **1666**, 10 Jan (+ reskript 12 Jan) | Forordning om Smaa-Mynten | Frederik III | DK | Import of foreign coin under whole Mark pieces forbidden; the mintmasters' small coin limited to whole and half dalers. | Mordhorst (f3) | — | — |
| **1667**, 29 March | Forordning om Fremmede Myntes Affsettelse | Frederik III | DK+NO | All foreign silver coin except specie reduced to its «Valeur paa Skrot og Korn»: kronemønt to ⅞ (2-sletdaler 7 M, sletdaler 3½ M, 2-Mark 28 sk., Mark 14 sk., 12 ß 11 sk., 8 ß 7 sk.), 4 and 2 ß to ¾; foreign coin under 2 ß forbidden. | Mordhorst (f3, quotes) | — | — |
| **1669**, 18 March · **1670**, 12 April | Forbud om Smaa Mynt fra fremmede Stæder; Forordning om Smaa Mynten | Frederik III / Christian V | DK | Import of foreign small coin forbidden; the ban sharpened. | Mordhorst (f3, c5) | — | — |
| **1671**, 22 March | Myndt-Ordning («saasom Kongen anseer en god og velbeskikket Myndt nødvendig til Landets Velstand …»; printed 4to, not in the forordningssamling) | Christian V | DK + NO + Glückstadt («I de Kgl. Lande») | Three mints: København, Christiania, Glückstadt. Small coin: 4 ß 120/M at 7½ lod (10 Rdl. 4 Mk per mark fine), 2 ß 214½/M at 6½ lod (11 Rdl.), 1 ß 288/M at 4 lod (12 Rdl.), Søsling 320/M at 2 lod (13 Rdl. 2 Mk). Grov: Specie 8 3/32/M at 14 lod (9¼ Rdl.; print misprint 7 5/6), ½ and orts à l'advenant; Krone / Slettedaler 10½/M at 10¾ lod (10 Rdl. 2½ Mk), ½ Krone, Mark, ½ Mark alike. Gold: ducat 67/M at 23 kt 6 gren (print 26, misprint). A royal Wardein at each mint, sealed melt samples, dies locked, half-yearly assay by the Commerce-Collegium. | act (Schou I s. 80–82, page images read) · Mordhorst (c5) · Wilcke II kap. I.6, II.7 | `schou-1795-bd1-s81-myndtordning-1671-smaamoent`, `-grov-moent`, `-guld`, `schou-1795-bd1-s82-myndtordning-1671-vardin`, `wilcke-1924-kap1-6-timpfe-1671-kroener`, `-reform-1671-2-skilling`, `danskmoent-c5mord` | `instruments/1671_myndt_ordning.md` |
| **1671**, 22 March | Forbud paa Smaa-Myntis Indførsel | Christian V | DK + NO | Total ban on importing foreign small coin (Skillinger, Toskillinger; Mordhorst adds 4 ß) by land or water, on pain of forfeiting the coin, horses, wagons, ship's hold and cargo; sharpens the Forbud of 18 March 1669. | act digest (Schou I s. 80) · Mordhorst (c5) | `schou-1795-bd1-s80-forbud-1671-smaamoent` | `instruments/1671_myndt_ordning.md` §3 |
| **1673**, 15 July (+ interpretation 28 June) | Verordnung wegen des Müntzwesens in Holstein | Christian V | SH-k | The Schleswig-Holstein coin edict; Danish rigsmønt (grov and skillemønt) not covered. | Mordhorst (c5) | — | — |
| **1674**, 23 Feb · 24 Feb | Forordning om Opgelt paa groft Myndt imod Rixdaler in Specie; Forbud om Rixdalers Omsmeldtning oc des Udførsel; reskript | Christian V | DK | Max. 4 % agio on specie against kroner and grov kurant for interest and instalments; melting and export of specie forbidden; henceforth only specie to be minted, told everywhere in specie. | Mordhorst (c5) | — | — |
| **1675**, 8 March | Forordning om fremmede Myndt | Christian V | DK | Dukaton 7½ M kurant; Albertus- and Kreuzdaler 6 M; Gottorp and Glückstadt dytkener at 6 sk., others forbidden. | Mordhorst (c5) | — | — |
| **1675**, 11 March | Reskript (2-Krone) | Christian V | DK | Named in `denmark.yml`; text to locate (Schou). | — | — | — |
| **1676**, 30 May | Forordning om Mynten | Christian V | DK | Supplements 8 March 1675. | Mordhorst (c5) | — | — |
| **1676**, 5 June · **1689**, 18 May | Forordning om Sølfkiøbet ×2 | Christian V | DK | Taxes may be paid in silver at a fixed rate after the mintmaster's assay: 3 M 4 sk. kurant per lot at Copenhagen fineness (1676); the mint's published purchase price 3 M 3 sk. per lot, 13-lot silver 3 M 1 sk. 2¼ hvid (1689). | Mordhorst (c5) | — | — |
| **1680**, 10 Feb · 18 Sept | Forordning om Fremmede Dytkeners Afsettelse oc Penges Udførsels Forbud (DK; NO) | Christian V | DK / NO | Export of specie, dukatoner, whole and half kroner forbidden (travellers 20 rd); dytkener not struck at Glückstadt, Gottorp or in the realms reduced from 6 to 5 sk. kurant. | Mordhorst (c5) | — | — |
| **1682**, 28 Oct | Forordning om Kaaber-Penges afskaffelse … udi Norge | Christian V | NO | The Norwegian war copper coin withdrawn from the end of 1682. | Mordhorst (c5) | — | — |
| **1684**, 19 Jan · **1686**, 17 April · 7 July · **1690**, 26 Oct | Reskripter (minting orders) | Christian V | NO / DK | Kongsberg silver ¾ kroner ¼ 2 ß at Christiania (1684); Copenhagen 100 000 rd kroner at 10 rd 2½ M per Mark fine + 10 000 rd small coin at 11⅔ rd (1686); Kongsberg silver ½ specie, ⅜ sletdaler, rest 4/2 ß per the Copenhagen ordinances (1686); 100 000 rd sletdaler 60/30/10 whole/half/quarter at 10 rd 2½ M (1690). | Mordhorst (c5) | — | — |
| **1684**, 28 May → **1695**, 19 Feb | Forordninger om Opgelt (1684, 1685, 8 May 1686, 1687, 1688, 14 April 1694, 1695) | Christian V | DK | Annual cap on the agio of specie against kroner for debts «in Specie»: 4 % → 6 % (1684 → 1685). | Mordhorst (c5) | — | — |
| **1687**, 26 Feb | Forordning om Ducatons, Realer, Albertus oc Kryts-Dalers Forhøyelse | Christian V | DK+NO | Dukaton 7 M 10 sk. kurant; Realer, Albertus- and Kreuzdaler 6 M 2 sk. | Mordhorst (c5) | — | — |
| **1687**, 30 April | Forordning om Fremmet Smaa Myntes afskaffelse oc Førstel. Holstenske Grof-Myntes Reduction | Christian V | DK | Foreign small coin forbidden; the ducal (not royal) Holstein 4- and 2-Mark pieces reduced to ⅞ (3½ M, 28 sk. kurant); export of grov silver coin except specie allowed. | Mordhorst (c5) | — | — |
| **1692**, 31 Dec | Reskript til kammerkollegiet om en ny møntanordning (+ the minting order of the same day; Schou 1795: «Regl. 31 Dec. 1692») | Christian V | DK (København mint) | Kurant only in Kroner, Mark pieces, 2 ß and ½ ß. Kroner and Mark «efter den allerbedste Godhed, som de nogen Tid udi Kongens Regjeringstid have været slagne» = 10 Rdl. 38 ß per mark fine (Hede's formula: 13 to the 13⅓-lødig mark, 17,988 / 14,984 g — the «fine kroner» 1693–1771); 2 ß not worse than the Kroner save for cost = 10 Rdl. 64 ß per mark fine; ½ ß in copper. Order: 100 000 Rdl. Kroner / Mark, 5 000 Rdl. copper ½ ß; no 2 ß «foreløbig». Not printed; text not in hand. | Mordhorst (c5, quotes) · Hede 1957 · Schou I s. 80 note | `mordhorst-c5mord-reskript-1692-kroner`, `-2-skilling`, `-udmoentning`, `hede-1957-kronemoenten-fine-kroner-formel`, `-reskript-1692-0-02-g`, `schou-1795-bd1-s80-note-regl-1692` | `instruments/1692_reskript_ny_moentanordning.md` |
| **1693**, 25 Feb | Forordning om Specie Rixdaler som ere myntede ved Sølv-Verket Kongsberg | Christian V | DK+NO | The Kongsberg speciedaler fixed at 6 M 8 sk. (the general course «Otte Skilling paa Daleren»). | Mordhorst (c5) | — | — |
| **1699**, 14 Feb | Forordning om Toldens Oppebørsel udi Specie efter Told-Rullen af Aar 1691 | Christian V | DK | Told in specie; temporarily in kroner with 12 % agio (previously 8 sk. per speciedaler). | Mordhorst (c5) | — | — |

Not instruments, kept out (block C+D): Schwabe's Erklæring 13 Nov 1628, the Hamburg Mandat
6 July 1644 (foreign), Bestallinger without a grid 1641–1664, Krüger's privilege 15 Nov 1664
(parameters unknown — §4 until read), bullion export bans 19 Nov 1663 / 8 March 1664,
Forordning om Falske Mynte 5 June 1665, the 1669 inquiry orders and the Commercekollegium
memorial, the Wexel-Ret acts 1681/1683/1688, the authorised seddeler 1695/96 — see §4.

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
| 1615 | Reces | `moentordning_1541.md` |
| 1667 | Münzvertrag | `9_thalerfuss.md`, `german_fuesse-references.yml`, `german_fuesse.yml` … |
| 1668 | Münzvertrag | `9_thalerfuss.md`, `fuesse.yml` |
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
| 1524, 26 Feb | «separate act» on the 14-Penning piece | `denmark.yml` 8-Gylden-fod bar title; `wilcke_1514_1541_specs.md` §2 | a misreading of Wilcke's table s. 187: the 14-penning line is dated 25/2 1524 there, its fineness comes from the marginal notes of Kongens Brev (s. 181) — no third act (`instruments/1524_moentordning_frederik_i.md` §8.1) |
| 1530, 6 May | Brev Jørgen Kock → Bergenhus | Galster; Holst | a REPORT on the Malmø mint's fineness — evidence for the 1524 dossier |
| 1531, 30 May | Brunswick Møntordning (Wildemannsthaler) | Wilcke 7-6 | territorial German, not Imperial |
| 1557, 10 Aug | Forordning of Duke Hans the Elder on interest | Wilcke 7-4 p. 308 | 6 % cap — not coinage |
| 1559, 12 Aug | Haandfæstning Frederik II | Wilcke 7-5 s. 308 | no coinage clause taken up |
| 1563–1581 | Bestallinger / Åb. breve for mint staff: Køppelin 15 Sept 1563 (1 year), Boessen 1565 (Isensnider), Kort N. 1576, Delhusen 1577, Brucker 1581 (Münzdruckwerk trials) | Wilcke 7-5, 7-6 | appointments without a grid |
| 1578, 4 June | Åb. br. Svendborg byskat after the coin change | Wilcke 7-6 s. 384 | fiscal conversion of one town's tax |
| 1584, 2 Oct | Mis. warning against foreign counterfeit coin | Secher II nr. 380 | police |
| 1596, 8 and 24 July | Kongebreve to Gottorp / Matz Puls | Wilcke II (w2ref) | borrowing minters for the coronation specie |
| 1603, 12 July | Frdg. against export of gold, silver and copper | Secher III nr. 161 | export ban, no parameter |
| 1606, 21 March | Dutch Møntplakat | Wilcke I s. 77 | foreign model of the 1607 Bestalling |
| 1607, 21 Jan | Instruks Jonas Charisius | Wilcke I s. 76 | diplomatic mission |
| 1613, 10 Aug · 1620, 10 June · 1623, 1 March | Valvationer | Wilcke I | assay outcomes |
| 1618, 7 May | Westphalian Kreis probation-day decision (Altona) | Wilcke I s. 37 | Kreis jurisdiction, context for Schauenburg |
| 1620, 23 April | Union Mecklenburg–Bremen–Lübeck–Hamburg | Wilcke I s. 162 | foreign; repeats the 1618 Mandat |
| 1622, 18 Jan | end date of Johan Post's account | Wilcke I s. 163 | not an act |
| 1625, 15 Feb | Rigsraadets Betænkning | refs `wilcke-1919-rigsraad-betaenkning-1625` | advice, evidence for the 1624/25 dossier |
| 1628, 13 Nov | Schwabe's Erklæring om Mønternes Finhed | Wilcke II kap. 1 | mintmaster's statement — evidence for the 15 Nov 1628 ordinance |
| 1644, 6 July | Mandat (Hamburg devaluation) | Wilcke II kap. 3 | foreign city |
| 1641–1664 | Bestallinger without a grid: Pentz's letter 3 Jan 1641, proberer 12 June 1650, wardeins 26 Feb 1655 / 20 Apr 1656, Köhler→Stichmann 12 March 1662, Grüner's confirmation 20 June 1662, Herbach 2 Nov 1663 / 20 Oct 1664 | Wilcke II | appointments, salaries |
| 1664, 15 Nov | Bevilling for Gotfrid Krüger «paa dend liden Mønt» | Wilcke II kap. 1.5 | a mint privilege; parameters not yet read — move to §1c if the text sets any |
| 1663, 19 Nov · 1664, 8 March | Åbent brev / Forbud on buying up and exporting gold and silver | Mordhorst (f3) | bullion export, no parameter |
| 1665, 5 June | Forordning om Falske Mynte | Mordhorst (f3) | penal |
| 1669, Feb–March | Commercekollegium memorial 20 Feb; Kongebrev 1 March; orders 18/23 March | Wilcke II kap. 1.6 | inquiry into the coinage — evidence for the 1671 dossier |
| 1681, 16 Apr · 1683, 15 Apr · 1688, 31 March | Wexel-Ret; Danske Lov; misuse of bills | Mordhorst (c5) | exchange law, not coinage |
| 1695, 22 June · 1696, 21 Aug | authorised seddeler in Norway and their abolition | Mordhorst (c5) | paper money |
