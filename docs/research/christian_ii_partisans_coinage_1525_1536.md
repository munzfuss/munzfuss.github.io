# Coins in Christian II's name 1525–1536: Søren Norby (Landskrona 1525), Norway 1531–32, the Count's Feud 1534–36

> **Status:** research dossier (role-1), opened 2026-11-05 during the C2+ / C2N review
> (entities `christian_ii_supporters` = C2+, `christian_ii_reconquest` = C2N).
> **Scope:** who struck these coins, under what authority, in which reckoning and on which standard;
> what this means for placing them on a Fuß; the data decisions taken.
> **Excluded:** Christian III's own war coinage in detail (`instruments/1537_reces_moentens_afsaettelse.md`,
> `christian_iii_danish_coinage_1534_1572.md`); Norby's Gotland coins (`gotland_gote.md` §7.2).
> Translations of quotes are in Ukrainian, as in the curator discussion.

## 1. Data decisions taken (2026-11-05, curator «так» / «з усім згоден»)

| Decision | Commit |
|---|---|
| Five KMM records misattributed to «Christian 2» (Galster 61, 63 = Frederik I; 94, 105 = Christian III) moved to `danish_realm`, ruler «(!)» | `da1c80e` |
| Galster 94 classes merged | `4c11dc5` |
| KMM 314762 / 314763 (Øland find, no weight, image or year) excluded as undocumented stubs | `bf0da9a` |
| Merged duplicates: Galster 91 (Galster + Bruun 4149 + five KMM «G. 91»), Galster 85 (Galster + KMM 317776, 570055, 156732 «Sch 18», 156733 «Sch 34»), Galster 174 (Galster + Bruun 9285 + Numista 121905 / 124917 / 448563 + KMM 684215), Galster 172 (Galster + Numista 477387 1531 + 121903 1532) | `ae81d32` |
| Not merged: KMM 156730 / 156731 (Schou 6 with place «Malmø»: Schou points to Galster 91, the place to Galster 86) | — |
| Galster parser: the per-year spec table of nc2g172 (1531: 6,72 g / 0,875; 1532: 6,45 g / 0,970–0,980) was lost; now read | `6a4f2ba` |
| Galster 80 (Norby, Landskrona 1525) stays in C2+ | — |

## 2. Søren Norby, Skilling 1525, Landskrona (Galster 80)

- danskmoent `chr/c2g80`: «*Slået af Søren Norby, som var Christian 2.s hærfører i Skåne (Galster 80,
  Schou 4-5)*» («Карбований Søren Norby, воєначальником Christian 2. у Сконе»).
- danskmoent «nordby»: «*I 1525 ledede han et bondeoprør i Skåne i den landflygtige Christian 2.s navn og
  lader slå skillinge i Landskrone (Galster nr. 80)*».
- Bruun Part II, lot 4116 (s. 26): «*struck … during his siege of the Scanian city of Landskrone*»; 4,08 g.
- Rasmusson, NNUM 1961 s. 87–96 (danskmoent `artikler/nordbynr.htm`): the Landskrona Skilling «*har ett
  identiskt bildschema*» with the Visby Skillinger 1524/25 (Galster 143); marks copied from them, cut much
  more coarsely; weight 3,28 g; Landskrona had a mint opened the year before (n. 21).
- Rasmusson also: by the capitulation terms Norby «*maatte i tre aar lade slaae Mønt på Mønten i Malmø med
  Kongens Stempel og af samme Holdighed som den kongelige Mønt*».
- Nielsen, Festskrift Amagerlands Num. Forening 1987 s. 49–53 (danskmoent `nordbypn.htm`): group 3 =
  Landskrona 1525, «*af samme type som gruppe to, men med Landskrona angivet som møntsted*»; «*må det
  formodes, at udmøntningen har haft et begrænset omfang*».
- **Not the Gotland standard:** struck on the mainland, in Christian II's name; the «Gullandsk mønt»
  of `gotland_gote.md` §7a is the Visby coin. Neither Rasmusson nor Nielsen states a norm for it.

## 3. Christian II in Norway 1531–32 (C2N; Galster 172–174)

- Holst (Norges mynter, danskmoent): «*Disse nødmynter faller naturligvis helt utenfor de systemer man
  søker å følge ved de ordinære utmyntninger*» — no Fuß.
- Galster 172 mark klipping 1531 / 1532 (danskmoent `norge/nc2g172`): 1531 6,72 g / 0,875; 1532
  6,45 g / 0,970–0,980.
- Galster 174 «Søsling(?)» klipping, «Hamar eller København», variants A–C = Schou 1–3. Kunzel n. 2
  after Galster 1972: «*Nr. 174 Sechsling o.J. … Nr 174A Abschlag vom Sechslingsstempel (3,10 g)*».
- Attribution of 174 contested: Wilcke 7-2 s. 227–229 notes no reference to Norway and a crown like Count
  Christoffer's Klippinge, «*udelukker ikke, at de ogsaa hører til Grev Christoffers Klippinge*»; against
  that, three pieces from Storhamar Strand (Mjøsa). Kept in C2N (curator 2026-11-05).

## 4. The Count's Feud 1534–36 (C2+, «group A»): who struck, under what authority

- **No ordinance on either side.** Christian III worked by orders to his mintmaster, e.g. Junge 4 Dec
  1534: «*danske Fireskillingsstykker, lig den Mønt, Kong Frederich lod mønte i Danmark, en lødig Mark til
  fem Lod*» (Wilcke 7-3 s. 237). The first legislative act is the Forordning of 21 Oct 1537 halving the war
  coin (Galster 1936; «*evnede man ikke at gennemføre … før 1540*»).
- **The Count's side minted by contracts with mintmasters, in Christian II's name.** Kunzel 1985–86
  (NNÅ s. 97–112; danskmoent `artikler/gustrow.htm`), from the Schwerin archive:
  - Albrecht VII's contract with Moritz Schacht, Güstrow, 28 March 1535: «*der dänischen Münz halben … inn
    nahmen unsers hern, Khenig Christierns … gelt machen, der da zehen stuck ein gulden gelten*»;
    «*Münzen dänischer Währung, d.h. Vierskillinge*»: 63½ per mark, 4½ lot, 281,25 ‰, 3,683 g, 1,036 g fine;
    117 610 pieces, c. 433 kg rough / 122 kg fine silver. = Galster 85.
  - Rostock 1536: «*für 15 seiner dänischen Doppelschillinge (Vierskillinge) 24 Schilling lübisch*».
  - Joint declaration of Albrecht and Christoph, Copenhagen 10 March 1536: the coin of «*Koppenhagen und
    elbogen*» «*beschwerung getragen*»; both promise to redeem it — the only monetary act of that side.
  - Galster 84 (½ Silbergulden 1536) = Albrecht's «*Beutepfennig*», with gold off-strikes sent to princes,
    «*dienten ausschließlich der Propaganda*».
  - Jørgen Kock: Malmø mintmaster from 4 Apr 1518 (Christian II's Klippinge), leased the mint under
    Frederik I to 1530, after 1533 organised the coinage in Malmø and København for Christian II's party.
- **Reckoning: Danish, on both sides.** Wilcke 7-3 s. 238 (after Grundtvig): «*En Mark Dansk paa 16 ß regnes
  lig 3/5 af en Mark Lybsk … 2½ M Dansk paa 1 Gylden i Mønt, og til samme Værdi beregnes Grev Christoffers
  saakaldte Firskillingsmønt*». Christian III's Klippinge «*skulde gaa for 2 Mark i dansk Mønt*» (Galster
  1936). Gustav Vasa struck «Danish» coin for the troops in Scania, who «*kun vilde have danske Penge*»
  (Wilcke 7-3 s. 245; Galster 1936).
- **Lübeck-equal coin in these years = the duchies' coin, not this one.** Galster 1936: «*Det var kun den
  danske Mønt, der blev gjort til Genstand for Forringelse; hvad Hertugdømmernes Mønt angik, overholdtes
  Privilegiet, at den skulde være jævngod med den lybske*».
- **Content:** Count Christoffer's 2 M 1534–35 «*5 L. 1 Q. · ca. 16*» (Wilcke 7-3 s. 242) ≈ 4,8 g fine [C];
  Schou 17 specimens 14,42 / 14 / 13,7 g «*særdeles vel stemmer med det svenske Regnskab*» (s. 245).
  Güstrow 4 ß ≈ 1 g fine (Denar til daler s. 480; Kunzel 1,036 g). Lübeck 2 ß 1522–30 1,95 g fine
  (Wilcke 7-2 s. 185–186).
- **Denominations:** 2 Mark Klipping, 4 Skilling, Hvid, ½ Silbergulden, gold Gylden — the Mark and 4 ß are
  the denominations of Frederik I's 1524 act («*ii marck danske*», «*iiii ß danske*», RL 1523–1558 nr. 10).
  Galster 88 Hvid copies King Hans' type («*Hans' navnebogstav h*», danskmoent `chr/c2g88`).

## 5. Placement (curator decision pending)

The Count's coins are neither a «Christian II system» (his 1513–23 coins had no Mark or 4 ß pieces) nor
Lübeck coin. They are the Danish Mark / Hvid reckoning, debased, on both sides of the war, so both sides
belong together. Which Fuß depends on the end-point of the Lybsk Møntfod
(`danish_small_coin_lines_1497_1660.md` §6): with (b) 1537–41 they fall inside it; with (a) 1514 they stay
with Christian III's war coin in `8_daler_fod` phase 0 (current home of the latter). Proposed kinds if
placed beside Christian III's war coin: 2 Mark Klipping kurant (as Galster 92 / 97 there), 4 ß and Hvid
scheide.

**Curator 2026-11-06 — PROVISIONAL:** the end-point is taken conditionally as (b) 1537–1541 («поки що приймаємо що умовно „так“»). It is a preliminary estimate, to be decided more precisely later; **later analyses must not rest on it.** Under it the Count's Feud coins fall inside the Lybsk Møntfod; their classification is still to be done.

## 6. Open questions

| Question | Would be settled by |
|---|---|
| Galster 89 / 90: danskmoent «Ungersk gylden» vs Galster 1936 «*2 rh. Gylden*» (Fig. 112–114) | Galster 1972 or the KMM objects KP 2085 |
| Galster 84 (Beutepfennig) — a presentation piece under CLAUDE.md §9? | curator |
| KMM 694936 / 417187 «1 Skilling» (legend IMMERITI CACERIS; «4ß men som B. 33») — Galster 85 by legend, no index | an index or image |
| KMM 331643 2 Skilling 1536 without index or image | an image |
| Galster 174 vs Galster 1972 «Sechsling»; KMM 684215 1,63 g against the 174A off-strike 3,10 g | Galster 1972 |

## Sources

- Kunzel, M.: «Zur Numismatik der dänischen "Grafenfehde" 1534 bis 1536», NNÅ 1985–86 s. 97–112 —
  danskmoent `artikler/gustrow.htm` (archived 14.02.2025); corpus `kunzel-1986-grafenfehde`.
- Rasmusson, N. L.: «Kring en myntmästare i Sören Norbys tjänst», NNUM 1961 s. 87–96 — danskmoent
  `artikler/nordbynr.htm`; corpus `rasmusson-1961`.
- Nielsen, P.: «Søren Norby og hans mønter», Festskrift Amagerlands Num. Forening 1987 s. 49–53 —
  danskmoent `nordbypn.htm`; corpus `nielsen-1987-norby`.
- Wilcke, J. (1950), 7-2 s. 185–186, 227–229; 7-3 s. 231–245 — corpus `wilcke-1950`.
- Galster, G.: *Danmarks Mønter* (Nordisk Kultur XXIX, 1936), Christian II and Christian III chapters —
  corpus `galster-1936-danmarks-moenter`; *Reynold Junges Møntmesterregnskaber 1534–40* (1934) — corpus
  `galster-1934-junge`.
- Horsnæs, Moesgaard, Märcher: *Denar til daler* (2018) s. 478–485 — corpus `denar-til-daler-2018`.
- danskmoent.dk type pages `chr/c2g80`, `c2g82`, `c2g84`–`c2g91`, `norge/nc2g172`–`nc2g174`.
