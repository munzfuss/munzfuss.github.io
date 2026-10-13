# `nobel_fod` — the Danish gold Nobel standard (1496–1532): research dossier

> **Status:** internal research dossier (role-1). Rewritten 2026-09-28 after the
> Nobelfod card revision (commits `2fdd18d` … `b88bb76`); supersedes the 2026-06-05
> version, whose retracted claims are kept in §9 with what disproved them.
>
> **Extended 2026-10-11** (descriptions of phases 0 and I, card heading, Ribe dating,
> 1602 gold table): new §1 rows, §5a, §6a, §7b; §8 and §9 amended. Sections written
> earlier keep their date; where a later section supersedes one, it says so.
>
> **Card status 2026-10-12 — REFERENCE MODEL.** The Nobelfod section of the Denmark page
> is, by the curator's call, practically finished and the model for the other Füße:
> description, Grundwerte, phases 0/I with period texts, timeline bar and a bibliography
> of 42 per-passage keys (every foreign quote translated, archive copy beside every web
> link, `cite-source` lint clean at high/medium). When reworking another Fuß card, take
> this one as the template for structure, register and citation shape. Residual low-level
> items: four quotes over ~25 words; «за Galster» author naming in the prose (handoff
> 2026-10-07) — both left as they are.
>
> **Question this dossier settles:** what the sources document about the Danish
> Nobel as a *standard* — its model, its two parameter regimes (pre-1514 and the
> 1514/1524 ordinances), the dated instruments, who reproduces whom, and how our own
> coin data sits against those figures.
>
> **Excluded, and where it lives:**
> - The later **Rosenobel** (Frederik II 1584, Christian IV 1611–1629, .833) — a
>   separate standard, `rosenobel_fod`; `docs/research/danish_royal_gold_1560_1648.md` §3.4.
> - The **Rhinsk Gylden** / Guldgyldenfod of the same ordinances — `docs/research/rhinsk_gylden_fod.md`.
> - The silver side of the 1513–1524 ordinances (Sølvgylden, Skilling, Klippinge) —
>   `docs/research/wilcke_1514_1541_specs.md`.
> - Market prices and single-specimen provenance — out of scope (§7a); only noted in
>   §6 as a survival signal.
>
> **Sources read in full for this rewrite:** Galster *Danmarks Mønter* (danskmoent
> transcription, complete); Wilcke 1950 ch. 2 (every Nobel passage, local PDF text
> `scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-2.txt`);
> danskmoent `1nobel.htm`, `fr/f1g45.htm`; Stack's Bowers Bruun lot 1001; en.wikipedia
> «Troy weight»; Numista 428544 (cache).

---

## §1. Sources and their provenance chains

| Key (refs_pool) | Work | What it is | Independence |
|---|---|---|---|
| `galster-nobel-*` (11 per-passage keys; the former single key `galster-unionstidens-nobel` was retired 2026-10-07) | Georg Galster, **«Danmarks Mønter»**, transcribed on danskmoent.dk `galster/galkult.htm` | Narrative survey; carries its own re-computed tables of the 1513/1514/1524 ordinances | Primary *interpretation*. **Title correction:** the page is «Danmarks Mønter», NOT Galster's catalogue «Unionstidens Udmøntninger» (1972) — the refs_pool key keeps its old name (stable key, §5b), the body names the right work. The transcription is unpaginated → the verbatim quote is the locator. |
| `wilcke-1950-nobel-1514`, `-nobel-finhed`, `-rigsraadets-brev-1524`, `-kongebrev-1524` (replaced `wilcke-1950-nobel-ordinance`, 2026-10-07) | Julius Wilcke, *Renæssancens Mønt- og Pengeforhold 1481–1588* (1950), ch. 2, danskmoent PDF «Wilcke 7-2» | Transcribes the ordinances (Suhm, Rigsarkivet) + own table | Primary for the **ordinance texts**. Paginated → page hints below. |
| `danskmoent-1nobel` | danskmoent.dk `1nobel.htm` | Type list per ruler (Galster / Schou numbers, rarity) | Derived from Galster's catalogue. |
| `danskmoent-nobel-finhed-f1g45` | danskmoent.dk `fr/f1g45.htm` (+ `fr/f1g69.htm`) | Type pages printing «Bruttovægt 14,375g, Finhed 0,979, Finvægt 14,08g» | **Derived from Galster's conversion table**, not a measurement — see §4.3. |
| — (coin-row source only) | Numista 428544 (1 Noble 1532) | «Gold (.979)», 14.375 g; references_list = `["Fr# 12", "Galster UU# 45"]` | **Derived from Galster** — same triple, cites only Galster. Not independent of danskmoent. |
| `stacksbowers-bruun-1496-nobel` | Stack's Bowers, L. E. Bruun Part I, lot 1001 (14 Sept 2024) | Auction description, Hans 1496 | Secondary; carries the «first dated Scandinavian coin» claim and the survival count. |
| `wikipedia-troy-weight-dutch-mark` | en.wikipedia «Troy weight», Dutch-troy passage | Metrology: «The mark was rated as 3,798 troy grains or 246.084 grams.» | Tertiary; used only for the gram value of the Dutch troy mark. |
| `ernst-1948-ribe-pragtmoenter-1524-1525`, `-ribe-nobel-haandfaestning-1524`, `-ribe-frederik-1-1524-1526` | Axel Ernst, **«Bidrag til Ribe Mønts Historie»**, NNÅ 1948 — danskmoent `ernst/ribeaxe1.htm` (full text; local copy `scripts/cache/danskmoent/galster/ernst_ribeaxe1.htm`) | Dates Frederik I's Ribe coinage 1524–1526 and the undated Ribe Pragtmønter 1524/1525; reviews Galster's «Ribe Mønt» (Fra Ribe Amt XI, 1947) | Secondary; builds on Galster 1947 but argues the dating itself. The transcription does not expose the print pages (danskmoent's literature list gives NNÅ 1948 pp. 15-18). |
| `wilcke-1950-hans-krige-pengetrang` (p. 147), `-guldmoent-krigsaar` (p. 215), `-christian-ii-flugt-1523` (p. 169), `-christian-ii-landgang-norge-1531` (p. 223), `-nobler-1532-vaegtige` (pp. 215–216), `-ribe-nobler-proever` (p. 194) | Wilcke 1950 ch. 2 (local text `scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-2.txt`; printed page = PDF page + 145) | Context of the three coinage episodes and of Ribe | Account-based; his own inferences are hedged («sikkert», «formentlig») and the cards keep the hedge |
| `galster-nobel-christian-ii-pragtmoenter`, `-1532-rustning-christian-ii`, `-hans-ingen-moentordning`, `-gelderske-kors-dordrecht`, `-tre-eksemplarer-vaegt` | Galster «Danmarks Mønter» (same transcription) | Pragtmønter, the 1532 armament «imod den hjemvendende Christiern II», no Møntordning of Hans, Dordrecht details copied, KMM specimens vs the model's weight | Same author, five more passages (one passage = one key) |
| `ernst-1938-nobler-1532-regnskab-fejlskrift` | Axel Ernst, **«Dansk Halv-Sølvgylden 1531»**, NNÅ 1938 pp. 41–52 — danskmoent `ernst/f1g50ern.htm` (local `scripts/cache/danskmoent/galster/ernst_f1g50ern.htm`) | A second reading of the 1532–33 account's Nobler (§5b); the print page of the passage is not shown by the transcription | Independent of Wilcke's reading of the same account; Ernst treats the account as Wilcke's source (Rørdam's printing) and proposes a scribal error |
| `vangelder-1995-reaal-toog-parament` (p. 32) | Van Gelder 1995 | the real as «munt van pronk en opschik» | Quote and page taken from `burgundian_gold_real_1487.md` §2; the PDF was not re-opened for this key |
| `stacksbowers-bruun-1496-nobel-gave` | Bruun Part I lot 1001 text | the «gift for foreign dignitaries» sentence | Verified verbatim in `scripts/cache/bruun/pages/part1.txt` (hedged in the source) |
| **not read** | Galster «Ribe Mønt» (Fra Ribe Amt XI, 1947, pp. 587–619 — tidsskrift.dk/fraribeamt holds image-only scans); Jensen–Skjoldager «The missing link — søslingeudmøntningen i Ribe og Ålborg 1524» (NNUM 2012/1 pp. 14–17), «Frederik 1.s søslinge» (2010), «Tronraneren» (2021) | Would settle the Ribe dating (§8 Q8) | Listed on danskmoent `fr/f1g73.htm` |

**Chain to keep in mind:** Galster ⟶ danskmoent type pages ⟶ Numista. Agreement of
danskmoent and Numista on 14,375 / .979 is ONE reading propagated twice (CLAUDE.md §9.4
caveat b), not corroboration.

---

## §2. Model and name

- **Model = the Dutch great gold real (groote gouden reaal) 1487, not the English Noble.**
  Galster: «*De har intet tilfælles med de engelske Noble (Rosenoble) ; men de svarer i
  Præg, Vægt og maaske ogsaa i Finhed nøje til den store Guldreal (groote gouden reaal),
  som 1487 prægedes i Holland for den romerske Konge (den senere Kejser) Maximilian.*»
  Details copied: «*det saakaldte gelderske Kors … og Rosen i Afsnittet, Dordrechts
  Møntmærke*».
- Bruun lot 1001 independently names the model: «*The model for the design was clearly
  the 'Real d'Or', struck in Dordrecht, for the Holy Roman Emperor, Maximilian I*».
  (Independent of Galster in wording; whether the cataloguer drew on Galster is
  unknown.)
- **Name:** Galster: «*fik deres Navn efter det ædle Metal*». danskmoent 1nobel.htm
  gives the English Noble's route into Denmark: «*Nobelen er en engelsk guldmønt, der fra
  1429 kom til Danmark via Øresundstolden, der netop var fastsat til en nobel per skib*».
  Bruun: the Sound Due was «*a toll of one English Noble*». Wilcke p. 167 keeps the two
  apart in a 1513–14 account: «*300 Nobel, 331 Nobel 17 engelske Nobel, 130 Nobel, 150
  Nobel, 200 engelske Nobel*» — hypothesis: «Nobel» vs «engelske Nobel» there already
  distinguishes the Danish piece; not verified, would need the account itself.
- The tertiary «imitates the English Noble» line (da.wikipedia «Nobel (mønt)») is
  rejected by Galster explicitly; the card follows Galster.

---

## §3. Parameters per period

### §3.1 Period 0 — Hans, 1496–1513 (no Danish ordinance known)

| Parameter | Value | Source |
|---|---|---|
| Instrument | **none known** for the Nobel | — (Galster ties the coinage to the Swedish campaign, not to an ordinance) |
| Pieces per mark | 16½ per **troy** mark — *of the Dutch model* | Galster: «*Den nederlandske Guldreal var ifølge Regnskaberne udmøntet af 24 Karat fint Guld, 16 1/2 paa en troysk Mark, d. v. s. den skulde veje 14,9g*» |
| Mark weight | Dutch troy mark 246.084 g | Wikipedia «Troy weight» |
| Rough weight | 14.914 g (recomputed 246.084 / 16.5) · Galster rounds 14,9 g | recomputed |
| Fineness | **unknown** for the Danish pieces. The model: 24 Karat. Galster: the Nobles match the model «*maaske ogsaa i Finhed*» | Galster |
| Fine weight | — (no fineness) | gap |
| Evidence the Danish pieces follow the model's weight | «*Hertil svarer de tre i den kgl. Mønt- og Medaille samling bevarede Exemplarer saa godt, som man kan forlange*» | Galster |

**Update 2026-10-11:** the model's own standard is documented in
`docs/research/burgundian_gold_real_1487.md`. De Witte II p. 74 has the instruction
of July 1487: 16½ to the mark, XXIV carats. The mark is the Trooise mark ≈ 244.75 g
(Vanhoudt), not the 246.084 g Hollandse mark, which gives 14.833 g. That equals Van
Gelder's legal mass of 14.83 g. The card was switched to 244.75 g / 14.833 g on 2026-10-11
(curator «так»); the 246.084 / 14.914 rows above are the pre-revision state.

The period-0 parameter set is therefore **the model's**, applied to Hans's pieces on
Galster's weight comparison. The card says so in those terms (Grundwerte Phase 0 row).

### §3.2 Period I — ordinances 1514 and 1524

| Instrument (date) | Pieces / Cölln. Mark | Fineness | Source (verbatim, page) |
|---|---|---|---|
| **Møntordning, Sommeren 1514**, letter to «Myntemester Dienis udi Malmø», «efter Rigsraadets Raad og Samtykke» (undated; Galster: «*synes at være samtidig med den norske Møntordning af 3. August 1514*») | 16 | 23½ Karat = .97917 | Wilcke p. 153: «*Nobel 23 1/2 Karat fint nobel Guld … 16 Stkr.*» |
| **Rigsraadets Brev, 25 February 1524** (Frederik I; with the Klipping re-coinage, to Jørgen Kock, Malmø) | 16 | 23 Karat = .95833 | Wilcke p. 182: «*vegne marck vdi fiine kornn hollde xxiij kaarat och skraade paa huer vegne marck xvj stycker*» |
| **Kongebrev, after 25 February 1524** (undated), to Jørgen Kock at Malmø; «*et lignende fik Møntmesteren i Riibe*» | 16 | 23½ Karat = .97917 | Wilcke p. 183: «*Nobler (den vegne Mark skal holde 231/2 Karat og skraade 16 Stkr.)*» |

- Galster on the 25 February act: «*Denne Møntordning fik dog ingen praktisk Betydning,
  da den allerede samme Aar afløstes af en ny … Noblen blev her forbedret til sin gamle
  Finhed 23 1/2 Karat*». So the 23-Karat step existed on paper only (Galster's reading).
- **What «fint nobel Guld» means** — Wilcke p. 153: «*Nobelens Finhed er 231/2 Karat*»,
  and he rejects the reading «23½ Karat of 23 Karat 3½ grains English Nobelguld» as
  «*for subtilt*»: «*nobel*» only means «*fint eller ædelt Guld*». Galster, by contrast,
  applies the «Nobelguld» reading to the *Gylden* (18 × 23½ : 24 = 17⅝ Karat). The two
  authors differ on the Gylden, not on the Nobel.
- No instrument after 1524 touches the Nobel. No Danish instrument ends it.

**Parameter table, period I (recomputed on Wilcke's mark 233.856 g):**

| | 1514 | 25.2.1524 | Kongebrev 1524 |
|---|---|---|---|
| rough | 14.616 g | 14.616 g | 14.616 g |
| fineness | 23½ K / .97917 | 23 K / .95833 | 23½ K / .97917 |
| fine | 14.3115 g | 14.0070 g | 14.3115 g |
| Wilcke's table (p. 187) | «14,616 14,311» | «14,616 14,007» | — |

Recomputation agrees with Wilcke to the printed digit.

---

## §4. The mark-weight question (Galster 230 g vs Wilcke 233.856 g)

### §4.1 What Galster says
In the section on the 1513 Møntordning: «*I det nittende Aarhundrede er den kølnske
Mark fixeret til 233,855g.; men i Begyndelsen af det 16. Aarhundrede var den noget
lettere; man har beregnet den til i Tyskland at have været 23,156g., og Vægten af den i
Danmark samtidigt benyttede saakaldte kølnske Mark kan man ikke bestemme nærmere end med
et rundt Tal til 230g.*»

And on Wilcke, before the 1602 table: «*Dr. W. har regnet med kølnsk Mark af samme Vægt
som nu til Dags (233,855 g.)*».

→ Two deliberate methodologies, not an error on either side. Galster: Danish
«Cologne» mark of the early 16th c. ≈ 230 g, by his own words only a round figure.
Wilcke: the 19th-century fixed value.

**Transcription defect:** «23,156g.» cannot be a mark weight. Hypothesis: 231,56 g in
print — would be settled by the printed Galster page (not available online).

### §4.2 Recomputation of Galster's tables on 230 g
- Nobel 230 / 16 = 14.375 → «14,375» ✓; × 23½/24 = 14.0755 → «14,08» ✓
- Rhinsk Gylden 230 / 72 = 3.1944 → «3,194» ✓
- Sølvgylden 230 / 8½ = 27.059 → «27,06» ✓
All rows of both his 1514 and 1524 tables are on 230 g.

### §4.3 Consequence — «14,375 / 0,979 / 14,08» is a computed type figure, not a specimen
- danskmoent `fr/f1g45.htm` (Galster 45, 1532) and `fr/f1g69.htm` (Galster 69, Ribe,
  undated) both print exactly «*Bruttovægt: 14,375g Finhed: 0,979 Finvægt: 14,08g*» =
  Galster's ordinance row. Identical figures on two different types is the signature of
  a type standard, not a weighed coin.
- Numista 428544 repeats them and cites only «Galster UU# 45».
- The measured specimens of Galster 45 (KMM 680125: 15.108 g; KMM 680126: 13.576 g)
  equal neither 14,375 nor each other.
- **No assay of any Danish Nobel is known in the sources read.** The card's prose and the
  f1g45 ref body were corrected accordingly in `b88bb76` (Phase I no longer says «the
  dated 1532 Nobler carry 23½ carats»; it gives Galster's caveat instead).

### §4.3a Other authors on the mark weight
Moved to the cross-cutting dossier **`docs/research/cologne_mark_weight_16c.md`**
(Hede and Jensen on 233.855 g, Galster's specimen-derived 230 g, Jensen's critique).
Short form: 233.855 g = Wilcke, Hede, Jensen; 230 g = Galster alone; no source
documents the mark actually used at a Danish mint 1513–1541.

### §4.4 Open curator decision
Which mark the Danish 1513–1524 standards use in the card (currently 233.856 g, Wilcke,
uniform with every other Danish fuss). Options put to the curator 2026-09-28:
(1) keep 233.856 g and document Galster's 230 g here + in comments — **current state,
recommended**; (2) switch the 1513–1524 ordinance standards (Nobelfod, Guldgyldenfod,
8½-/8-Gyldenfod) to 230 g — Galster himself calls the figure approximate. Undecided.

---

## §5. Compliance and coinage record (standard-level)

- **Hans:** Galster — gold coinage «*staar rimeligvis i Forbindelse med Udrustningerne
  til Sverigestoget*» (hedged in the source; the card keeps «nach Galster …
  wahrscheinlich»).
- **Christian II (1516, 1518):** Galster — «*Noblerne foreligger med Aarstal 1516 og
  1518; men det er uvist, om de opfylder Møntordningens Krav om Finhed. De er ligesom
  Kong Hans' Noble i første Række Pragtmønter, der skylder Rustningerne mod Sverige deres
  Tilblivelse.*» Wilcke p. 170: «*Mønterne fra 1516 og 1518 særdeles sjældne*». Galster:
  silver off-strikes from the Nobel dies = the Sølvgylden («*Med Nobelstemplerne blev
  taget Afslag i Sølv*»).
- **Frederik I, Ribe (undated):** Wilcke p. 194: «*baade Nobler og Sølvgylden, formentlig
  Prøver*»; Galster fig. 106 «*Nobel fra Ribe (Afslag i Sølv)*».
- **Frederik I, 1532:** Galster — struck from church gold/silver requisitioned 1531 «*i
  Anledning af den forestaaende Fejde*»; «*derimod prægedes af Guldmønt kun 21 Noble*».
  Wilcke pp. 208, 215–216 (account 1532–33): «*Anders Bille lod mønte: 21 Nobler (paa
  tilsammen ca. 60 Lod) … 1 Nobel paa 21/2 Lod 1 Quintin Guld*»; «*Det har været
  særdeles vægtige Nobler, gennemsnitlig 3-dobbelte, thi en Nobel efter Kong Frederiks
  Møntordning vejede 1 Lod*»; «*De skulde sikkert gives de højere Befalingsmænd*»
  (Wilcke's own inference, hedged by «sikkert»).
  Recompute: 1 Lod = 233.856/16 = 14.616 g = 1 Nobel ✓; 60 Lod − 1 Quintin ≈ 873 g / 21
  ≈ 41.6 g ≈ 2.8 Nobler ✓ «3-dobbelte»; the thick piece 2¾ Lod ≈ 40.2 g.
- **Sound Due income under Frederik I:** Wilcke p. 205: «*Af Øresundstolden indgik i
  hvert Fald 11 428 r. G. og 556 Nobler*».
- **Christian III:** no Nobel (danskmoent 1nobel.htm type list ends with Frederik I).
  The card's «Christian III (1534–1559) does not continue it» rests on that absence.
- **Rarity:** Galster «*Bortset fra de sjældnere Mønter, Nobler og Sølvgylden …*»;
  Bruun: «*Of all the Danish Nobles struck between 1496 and 1532 … only 20 remain, most
  of them in the National Museum of Denmark*».
- **Function:** Bruun — «*Although the exact reason for minting this Noble is unknown,
  it seems likely that it was struck for the king's personal use as a gift for foreign
  dignitaries*» (hedged in the source). The card does NOT state a function beyond
  Galster's «Pragtmønter»/armament wording; the earlier «not for circulation / display
  gold» claim was removed (`36ed09d`) as unsourced.

---

## §5a. Context and dating added 2026-10-11 (feeds the phase 0 / phase I descriptions)

**Hans, 1496–1513 (phase 0).**
- Galster: «*Under Kong Hans skete noget nyt … Udmøntning af Guld: Noble og Gylden. Dette
  staar rimeligvis i Forbindelse med Udrustningerne til Sverigestoget*» and «*Der er ikke
  bevaret nogen dansk Møntordning fra Kong Hans*». Wilcke p. 147: Hans «*udnyttede …
  Møntsystemet til at skaffe sig Midler til sine Krige mod Sverige og Ditmarsken m. fl.
  … var han stedse i Pengetrang*». (Wilcke 7-1 pp. 32–37 gives the monetary milieu:
  Sigismund's silver gylden 1484, the American silver after 1492, Danish coin before
  Hans mostly small silver, foreign gulden in the accounts. Not used in the card text.)
- **The model's own character.** Van Gelder 1995 p. 32 calls the great reals «*munt van
  pronk en opschik*»; Van Gelder 1951 p. 46: gold was «*practisch niet geslagen*» in the
  Netherlands apart from a modest Dordrecht coinage. Galster: «*gelderske Kors … Rosen i
  Afsnittet, Dordrechts Møntmærke*» came over to the Danish copy. So Hans copied a show
  coin that was itself struck in small numbers.
- Galster on the KMM specimens: «*Hertil svarer de tre … Exemplarer saa godt, som man
  kan forlange*» (weight against the model's 14.9 g, §3.1).
- **Fineness of the model's «24 karat».** De Witte p. 73 prints XXIV carats; Vanhoudt
  p. xxiv says some Netherlandish ordinances equated pure gold with the English gold
  noble (23 kt 10½ gn, ≈ 995 ‰). Whether that reading applies to the 1487 real is NOT
  stated by either (`burgundian_gold_real_1487.md` Q1); the card says so in those words.
- Function: Bruun lot 1001 (hedged): «*it seems likely that it was struck for the king's
  personal use as a gift for foreign dignitaries*». Used in the phase 0 text with the
  hedge.

**Christian II, 1516 and 1518 (phase I).** Galster: the Nobler are, like Hans's,
«*i første Række Pragtmønter, der skylder Rustningerne mod Sverige deres Tilblivelse*».
The source says «armaments against Sweden» only; it does not say campaign, and the
card says «military preparations». Wilcke p. 161 only places the 1518 war with Sweden
in the narrative («Vi nærmer os nu Krigen med Sverige 1518»); no instrument ties the
Nobler to it.

**Frederik I, 1523–1533 — events relevant to any gold issue** (Galster / Wilcke):

| Date | Event | Source |
|---|---|---|
| 13 Apr 1523 | Christian II flees | Wilcke p. 169 |
| 13 Jul – 10 Aug 1523 | New tax in Jutland for the Klipping withdrawal; forordning of 10 Aug; «Lejrskillinger» struck in the camp at Serritslev Mark during the siege of Copenhagen; the danger from Christian II «foreløbigt drevet over i Slutningen af 1523» | Galster |
| 25 Feb 1524 | Rigsraadets Brev + Kongebrev to Jørgen Kock (Nobel 16/mark) | Wilcke pp. 182–183 |
| 1524 | Mints at Malmø, the «nyindrettede Mønt i Ribe», Aalborg, København, Landskrone «væsentlig af Hensyn til Klippingenes Ommøntning» | Galster |
| 7 Aug 1524 | Coronation as Danish king | Ernst |
| Nov 1524 | Frederik signs at Ribe the Norwegian Haandfæstning (Vincens Lunge): Norway a hereditary kingdom | Ernst (citing Kinch I pp. 467–468) |
| 1523–25 | Søren Norby on Gotland, then Blekinge; at Sølvitsborg Nov 1525 – Aug 1526 | Galster |
| 1526 | Malmø mint pledged to Jørgen Kock; the King lacks silver | Galster (Herredag Odense 1526) |
| to 1530 | Malmø mint idle «halvtredje Aar» («silver has become so dear») | Galster (Kock's letter 6 May 1530) |
| 5 Nov 1531 | Christian II lands in Norway | Wilcke p. 223 |
| 18 Dec 1531 | Rigsraad decides the church-silver requisition | Wilcke p. 206 |
| 1 Jul 1532 | Christian II surrenders | Wilcke p. 223 |
| 10 Apr 1533 | Frederik I dies | Galster |

**Ribe — what dates the undated Nobler (Galster 68, 69).**
- Ernst: Ribe had no mint from the 14th century until summer 1524; «*Ribe-Udmøntninger
  under Fred. I kun strakte sig over Aarene 1524-1526*». Dated Ribe types (danskmoent
  `fr/f1g73.htm`): Søsling 1524 (Schou 126–131), 1525 (Schou 39–43), 1526 (Schou 5–7,
  «*sikkert kun i ret ringe Omfang*»); four-Hvide and 14-Penning of 1524 (before / after
  the coronation).
- Ernst: «*Til Aarene 1524 eller 1525 maa endelig henføres de uden Aarstal i Ribe
  prægede Pragtmønter*»; the Nobel (Schou 1) and the Halvsølvgylden (Schou 5) are Unica
  of the Royal Collection and «*kan muligvis sættes i Forbindelse med*» the November 1524
  signing at Ribe. His reasoning for the silver off-strike (Schou 3): between the
  coronation (7 Aug 1524) and the Norwegian Haandfæstning (Nov 1524). **His hedge
  («muligvis», «bør vel») is carried into the card text.**
- The title «Heres Norvegiæ»: Ernst's earlier note «To hidtil ubeskrevne 14-Penninge fra
  1524» (danskmoent `ernst/14p1524.htm`, local `scripts/cache/danskmoent/galster/ernst_14p1524.htm`)
  finds it, besides on a Ribe 14-Penning of 1524, only on «Fred. I.s kendte Mønt fra
  Ribe med Reversomskriften: «Moneta nova aurea Ripensis» (Jørgensen Nr. 25)». The Galster 68 plate legend (curator's scan 2026-10-11) reads
  «…AVREA RIPENSIS MONETA NOVA» — **hypothesis, not verified:** the same piece.
- Wilcke p. 194 (different view): «*Nobler og Sølvgylden, formentlig Prøver, thi
  Midlerne hertil skulde ikke synes at foreligge*». Both views are in the phase I text,
  each attributed.
- **Galster 68 stays in the table (curator 2026-10-11).** danskmoent says genuine
  specimens «ikke længere kendes ægte» and cast copies exist; Ernst calls Schou 3 a
  silver off-strike of an unknown Nobel. The Galster plate states «Au, 38 mm»; cast
  silver copies do not refute a gold original, so the §9.3 off-metal exclusion is NOT
  applied.
- What was NOT found: any source that ties a Ribe Nobel to a campaign. Wartime
  coincidences (Norby 1523–26; Christian II 1531–32) are outside Ernst's 1524–1525 window
  except by inference; none is made.

---

## §6. Our data against the sources (inventory 2026-09-28, `data/v2/final/danish_realm.yml`)

| Final | Type | Phase | Fineness in data | Weights in data | Note |
|---|---|---|---|---|---|
| `unified-dk-bruun-3831` | 1 Nobel 1496, 1502 (Galster 24) | 0 | — | 14.67 (Bruun), 14.75 (KMM, Numista) | vs model 14.914: −1.6 %, −1.1 % |
| `unified-dk-numista-428886` | 2 Nobel 1502 | 0 | — | 27.9 | 13.95 per Nobel |
| `unified-dk-numista-428914` | 3 Nobel 1496 | 0 | — | 44.72 | 14.91 per Nobel = model |
| `unified-dk-numista-428876` | 1 Nobel 1516, 1518 (Galster 37) | I | .979 «Møntordning 1514», `verified: false` | 14.24, 14.53 | canonical-anchor per §4; consistent with Galster's «uvist» |
| `unified-dk-numista-428544` | 1 Nobel 1532 (Galster 45) | I | .979 galster + .979 numista, `verified: true` | 13.576, 15.108 (KMM); 14.375 ×2 (galster, numista) | the 14.375 entries are Galster's computed type value (§4.3), not specimens |
| `unified-dk-galster-f1g-69` | 1 Nobel Ribe (Galster 69) | I | .979 galster, `verified: true` | 14.375 (galster); 17.4 KMM flagged `suspect` | same computed triple |
| `unified-dk-galster-f1g-68` | 1 Nobel Ribe (Galster 68, «Nu ukendt») | I | — | — | |

Observations (not acted on): the «14.375 g» `weight_rough_g` entries are type values
sitting in a specimen-weight list. Whether to keep them there (they are what the source
prints) or tag them is a curator question — see §8. `fineness_verified: true` is correct
under §4 («present in a source»).

---

## §5b. The 1532–33 account of the Nobler: Lod, Quintin, two readings (added 2026-10-11)

**Units.**
- **Lod** (Lot) = 1/16 of the Cologne mark = 233.856 / 16 = **14.616 g** (`docs/GLOSSARY.md`). In
  these accounts it is a weight; the same word also counts silver fineness in sixteenths
  («14 Lod»).
- **1 Nobel = 1 Lod** is not a further rule: it is the standard «16 Nobel per mark» written in
  the unit the accounts use (Wilcke p. 216: «en Nobel efter Kong Frederiks Møntordning vejede 1
  Lod»; English nobles «1/2 Lod»).
- **Quintin** = ¼ Lod (3.654 g) in the Cologne weight system. NOT checked in the cached
  Wilcke text (it uses the unit without defining it); hypothesis from general metrology. The
  conclusions below move by < 0.5 % if it is wrong.

**The account** (Wilcke 7-2 p. 208; he reprints it from Rørdam 1867 and notes «Enkelte Fejl
i Rørdams Gengivelse»; original: RA, Universitetsarkivet, Konsistorium 52, Aktstykker før
Reformationen): «*Anders Bille lod mønte: 21 Nobler (paa tilsammen ca. 60 Lod) å ca. 18 gylden
å 2½ M … ca. 945 M; 1 Nobel paa 2½ Lod 1 Quintin Guld = ca. 15 gylden … ca. 37 M*».

**Wilcke's reading** (p. 215–216): «*Anders Bilde lod slaa 21 Nobler til samlet Vægt 60 Lod ÷ 1
Quintin og en tyk Nobel paa 2½ Lod 1 Quintin. Det har været særdeles vægtige Nobler,
gennemsnitlig 3-dobbelte … De skulde sikkert gives de højere Befalingsmænd*» (« ÷ » = minus).
- Recomputed: 59¾ Lod = 873 g / 21 = 41.6 g ≈ 2.85 Lod per piece = 2.85 × the standard;
  the thick piece 2¾ Lod ≈ 40.2 g.
- Check from the account's own valuation: 18 gylden per piece against a standard Nobel of
  14.3115 g / 2.436 g (18-karat gylden) ≈ 5.9 gylden → 18 / 5.9 ≈ 3.1; the thick piece
  15 gylden for 2¾ Lod ≈ 2.55 × 5.9.

**Ernst's reading of the same account** (NNÅ 1938, danskmoent `ernst/f1g50ern.htm`): the
account gives «*21 Nobler til en samlet Vægt af 878,7 g og 1 «tyk» Nobel til en Vægt af 40,44
g*» (his figures, not Wilcke's lots); this does not fit the 1524 ordinances (16 per mark =
14.375 g). «*Jeg er derfor tilbøjelig til at antage, at «21» (xxi) i Regnskabet skyldes en
Fejlskrift, vistnok for «61» (lxi), og i saa Fald vilde Udtrykket «1 tyk Nobel» ogsaa blive
mere forstaaeligt som sigtende til en 3 (?) dobbelt Nobel*». 878.7 / 61 = 14.4 g — the
standard Nobel; he places the coinage in the Galster 45 / Schou 1532 Nr. 1 type (13.55 and
15.08 g).
- **The two readings conflict:** Wilcke — 21 pieces averaging triple weight; Ernst — 61
  ordinary Nobler plus one thick (probably triple) Nobel. The account's original numeral
  would decide it (§8 Q13).

**Search for anything else on triple Nobler of 1532 (2026-10-11):**
- danskmoent type pages `1nobel`/`2nobel`/`3nobel`: multiples are Hans only — 3 Nobel 1496
  (Galster 25, Unik), 2 Nobel 1502 (Galster 26, Unik); none for Frederik I.
- Our seeds (galster, numista, kmk, bruun, ikmk): Frederik I Nobler are 1 Nobel only
  (Galster 45 / KMM 680125, 680126 / Numista 428544; Ribe types 68, 69). Bruun lot text:
  «only 20 remain» of all Danish Nobles.
- Cached Wilcke 7-1…7-8, Galster «Danmarks Mønter», Bruun Part I, Hede: no other mention of
  such pieces; the 1533 inventory (Ernst, quoting Nye danske Magazin VI) lists «VI gulden
  stucke van kon. Maits eygen munte» between Portugaløsere and double ducats — Ernst: possibly
  the 1532 Nobel; no weight.
- Result: the account is the only source for such pieces; no coin of triple weight is
  known, and the denomination-by-weight precedent is Hans's 3 Nobel 1496 (44.72 g ≈ 3.06 Lod)
  and 2 Nobel 1502 (27.9 g ≈ 1.9 Lod). **Hypothesis (curator, 2026-10-11): denomination was
  determined by weight, no number being on the coin** — consistent with Hans's multiples;
  not stated by any source and not in the card text.
- The Phase I text states both readings and that nothing else is attested.

---

## §6a. Update to §6 (2026-10-11)

- `unified-dk-galster-f1g-68` and `-69` (Ribe): `year_label` **1524-1525** with the
  unverified marker, `year_verified: false`. The earlier 1523-1533 was Frederik I's reign
  window (`year_is_reign_span`), not a source date; the flag is removed and the values
  frozen in `_curation_holds` (basis: Ernst, §5a).
- Fineness, mark and weight rows of the card now read: **.97917** (23½/24, five decimals),
  14.616 g rough / **14.3115 g** fine per Nobel; 2 Nobel 28.623 g, 3 Nobel 42.9345 g
  (`soll_fein_g`). Source readings (Galster .979 / 14.375 / 14.08) are left as the sources
  print them.
- The seed record Galster 69 has no recorded `why` decision about its year: the seed
  default was the reign window.

---

## §7. Card state after the 2026-09 revision (for orientation)

- Name `Nobelfod` (was `16-Nobelfod`, `2fdd18d`). Period 1496–1532, phases 0 (1496–1513)
  and I (1514–1532). `fineness_standard: 0.979` (the earlier `.986` Reichsdukat
  mis-anchor is gone).
- Grundwerte: Phase 0 = model's 16½ / troy mark, fineness unknown; Phase I = 16 /
  Cölln. Marck, fineness lines 1514 / 25.2.1524 / Kongebrev 1524.
- Timeline bar: mint layer only (status and circulation hidden).
- Events: `demonetisation 1600` (approx) has **no source**; `std_end` / `demonetisation`
  notes still cite legacy «ref37». Flagged, not fixed.

---

## §7a. In force 1514 → ~1602 (curator 2026-10-11, Denmark)

**Curator rule for the end of force (2026-10-11).** When no act expressly
ends a standard, its end is the nearest act that sets a different standard and
ignores the old one; being indirect, that end is marked approximate («~»).
- `std_start` 1514: Møntordning af Sommeren 1514, «Nobel 23 1/2 Karat fint
  nobel Guld … 16 Stkr.» (Wilcke 1950 7-2 p. 153) — the first Danish act on the
  Nobel; Hans' Nobler 1496-1513 precede any act.
- `std_end` ~1602 (was 1533 approx, from Frederik I's death — an inference):
  Forordning 8 Sep 1602 lists Danish gold as Portugaløser, Ungersk Gylden and
  the three gold Daler-Klippinge, with no Nobel; no earlier repeal (1541 silver-only). Last Nobler 1532.
- `first_adoption` stays 1496 (curator: Danish Nobler share only the name with
  English nobles — a different standard, so English nobles' earlier circulation
  in Denmark does not date this one).
- Denmark timeline: status stripe shown (1514 → ~1602, end fade), mint ×6 alpha
  removed so the bar renders like Guldgyldenfod; bar to 1602.
- `demonetisation` ~1600 still unsourced — left as is (curator 2026-10-11).

## §7b. Card state 2026-10-11 (supersedes the stale bullets of §7)

- Phases (Denmark page): **0 · Hans · Ohne dänische Møntordning** (1496–1513) and
  **I · Christian II · Frederik I** (**1516**–1532; coin-based start — the legal basis
  stays 1514). Card keys: «Phase 0 (1496-1513) · König Hans …» and «Phase I (1516-1532) ·
  Könige Christian II., Frederik I.».
- A decree section «Møntordning Christian II 1514 / Kongebrev Frederik I 1524» between
  phases 0 and I (16 / mark, 14.616 g, 23½ kt = .97917, 14.3115 g fine; the 1524 changes
  of fineness are not in it). Phase I keeps «Parameter gemäß …», the three fineness lines
  and the denomination. The Dutch ordinance 1487 has its own decree row above phase 0
  (`burgundian_gold_real_1487.md` §6).
- Phase 0 description: first Danish gold, wartime finance (Wilcke p. 147), no Danish
  Møntordning, model and its «24 karat» convention (stated as open), Pragtmønter, KMM
  specimens vs model weight, the gift hypothesis.
- Phase I description (chronological): Wilcke's wartime-gold remark → 1516/1518 (Galster)
  → Ribe 1524–1526 (Ernst, Wilcke) → 1532 (Galster, Wilcke). The ordinance text is only
  in the instrument block.
- Card description (`grundwerte.rechnungsfraktionen`): heading «coinage 1496–1532, legal
  basis from 1514»; role (Pragtmønter, wartime); Rhinsk Gylden cross-reference; «no
  determination of the fineness of a Danish Nobel is attested»; end of the standard from
  the 1602 table. **Kept as is by the curator:** «the first dated gold coin of Denmark»,
  although Bruun says «first dated Scandinavian coin» (§8 Q10).
- 1602: the Forordning's gold table lists the Portugaløser, the Ungersk Gylden and the
  three gold Daler-Klippinge — not «only» the first two (corrected in `std_end` notes,
  the Guldgyldenfod description and the other dossiers).

---

## §8. Open questions — each with what would settle it

1. **Fineness of any actual Danish Nobel.** No assay known. → an assay/XRF record
   (Nationalmuseet KMM) or Galster's printed 1972 catalogue if it gives measured values.
2. **Period-0 fineness (Hans).** Only Galster's «maaske ogsaa i Finhed» (= 24 Karat
   like the model). → same as 1.
3. **Galster's German Cologne-mark figure** «23,156g.» (transcription defect; hypothesis
   231,56). → printed «Danmarks Mønter», the page of the 1513 Møntordning section.
4. **Mark weight for the card** (§4.4). → curator decision.
5. **«Nobel» vs «engelske Nobel»** in the 1513–14 Helsingør account (Wilcke p. 167) —
   hypothesis that the first denotes the Danish piece. → the account text (C. F. Allen,
   Chr. II.s Breve 1854, cited by Wilcke).
6. **The 14.375 g type values in `weight_rough_g`** lists (§6). → curator: keep / tag /
   move to a type-standard field.
7. **`demonetisation 1600` event** — unsourced approximation. → a source for when
   Nobler ceased to be accepted, or drop the event.

8. **Dating of the Ribe Nobler (Galster 68, 69).** Ernst gives 1524 or 1525 (hedged).
   → Galster «Ribe Mønt» (1947), Jensen–Skjoldager «The missing link» (NNUM 2012/1) and
   «Tronraneren» (2021); the Royal Collection record of the Unica.
9. **The «24 karat» of the 1487 real** (Vanhoudt's noble-gold convention). **Narrowed
   2026-10-12:** the Netherlands instructions themselves use «24 carats» as a
   conventional label — De Witte II p. 79 (instruction after the ordinance of 14 Dec
   1489): «*à XXIV carats — le noble Henricus compté pour fin*»; pp. 39–40 (Bruges 1469),
   44, 53; numeric «fine gold» = 23 ct 9½ gr in 1500 (p. 116) and 1521 (p. 160); full
   table in `burgundian_gold_real_1487.md` §3.1a. Still open: whether the 1487 text
   says the same (Q1). **Card/description state:** «24 карати» is NOT given as the
   prototype's fineness in the phase 0 text; it stays in the details section
   «Instructie Maximilian juli 1487» as what the instruction names, with the
   convention note (ref `dewitte-1896-or-fin-noble-compte-pour-fin-1489`).
10. **«First dated gold coin of Denmark» (card) vs Bruun «first dated Scandinavian
    coin».** Curator kept the card wording 2026-10-11. → a source on dated Danish coins
    before 1496 would settle it either way.
12. **Earlier gold under Erik of Pomerania (1397–1439).** Curator 2026-10-11: the first known
    Danish gold coin is Erik's, not Hans's; Galster's «noget nyt … Udmøntning af Guld» is
    therefore not repeated in the card (phase 0 now says only that gold Nobel and Gylden are
    struck under Hans, with Galster's armament link). Web search found a Numista record of a
    gold coin of Erik (Lund, 9.85 g) but no source stating it is the first; nothing in the
    cached Galster/Wilcke/Bruun texts. → a Galster «Unionstidens Udmøntninger» (1972) entry
    for Erik's gold, or the Royal Collection record. Until then the card carries no «first
    gold» claim; the «first dated gold coin of Denmark» line stays (curator, see Q10).
13. **The Nobler of the 1532–33 account: 21 pieces of average triple weight (Wilcke) or 61
    ordinary + one thick (Ernst)?** → the account's original (RA, Universitetsarkivet,
    Konsistorium 52) or Rørdam 1867's printing; any weight record of a 1532 Nobel above ≈ 15 g.
11. **Is Galster 68 the «Moneta nova aurea Ripensis» gold of Ernst (Jørgensen 25)?** The
    plate legend suggests it; unverified. → Jørgensen's catalogue or the plate itself.

---

## §9. Retracted claims from the 2026-06-05 version

| Claimed | What disproved it |
|---|---|
| Galster's text is «Unionstidens Udmøntninger» | The danskmoent page is «Danmarks Mønter» (page title + header «af Georg Galster»). |
| «Frederik I 1524 Møntordning = 23 Karat» as the 1524 value | Two 1524 acts: Rigsraadets Brev 25.2. (23 K) and the Kongebrev after it (23½ K); Galster: the first «fik ingen praktisk Betydning» (Wilcke pp. 182–183). |
| 1532 specimens attest .979 / 14.375 g (danskmoent «specimen») | Galster's ordinance row on a 230 g mark, repeated on two types; Numista derived from Galster (§4.3). |
| «Resolved» 2026-06-11: the Nobel is definitely ½ Karat below the Dutch model | Compared the 1514 ordinance (Christian II) with the model Hans copied — cross-period; Hans-era fineness is unknown. The card reverted to Galster's hedge. |
| The Nobel is a «Pragtmünze, NOT circulation money» (as fact) | Galster says only «i første Række Pragtmønter» of Hans's and Christian II's pieces; the absolute claim was removed from the card (`36ed09d`). |
| «Hans struck gold … to pay his German mercenaries» (danskmoent c2njj.htm) | Not re-verified in this rewrite; not used in the card. Status: unverified. |
| `.986` in the card is a mis-anchor pending decision | Applied — card is on .979. |
| «The range 1523–1533 for the Ribe Nobler is in Galster» (chat 2026-10-11) | danskmoent f1g68/69 print «u.år»; 1523–1533 was the reign window set by the seed (`year_is_reign_span`). Replaced by 1524–1525 (?) after Ernst (§5a, §6a). |
| «Forordning 1602 defines Danish gold only as Portugaløser + Ungersk Gylden» (`std_end` note, card text, other dossiers) | The same table has three gold Daler-Klippinge rows (8, 6, 4 Daler); reworded everywhere to «lists …, with no Nobel». |
| «14,31 g fine / .979» in the card | 23½/24 = .979167 and 14.616 × 23½/24 = 14.3115 exactly; the card now carries five decimals (`070999f`, `7720ca1`). |
| «The Nobel has nothing in common with the English Noble» (card sentence cited to `galster-nobel-navn`) | That key only supports the name. Galster's statement concerns the Rosenobel, and the curator noted a possible indirect link via the Dutch real's relation to the English noble; the sentence was removed (`174dc2f`), not replaced by a counter-claim. |
| «The first Danish gold appears under King Hans» (phase 0 opening, written 2026-10-11 from Galster's «noget nyt») | Curator: the first known Danish gold coin is Erik of Pomerania's. Sentence replaced by a neutral one (§8 Q12). The Galster sentence is the author's and is not independently confirmed. |

## §10. Tariff acts and accounts as a circulation trace — the search (2026-10-13)

Question (curator): the Guldgyldenfod circulation layer (~1400–~1650) was
built from the series of valuation acts that name and rate the Rhinsk Gylden
(`rhinsk_gylden_fod.md` §17). Is there anything comparable for the Danish
Nobler of 1496–1532 (not the Rosenobel)?

**Answer: no.** Every Danish valuation, tariff list and account read for the
gulden series was re-read for «Nobel». The Danish Nobel is never named as a
rated or received coin in any of them. What the sources carry:

| Date | Record | What it names | Danish Nobel? |
|---|---|---|---|
| 1497, 1503 | Øresund toll accounts (Wilcke 7-1 pp. 80, 143; Astrid Friis) | toll of one «Nobel» per ship, paid in Nobler or 2½ rhinske Gylden; «Noblerne var jo ogsaa af forskellig Art» | «Nobel» = the English toll unit; the Danish piece not distinguishable |
| 1513–14 | Helsingør toll receipts (Wilcke 7-2 p. 167) | «300 Nobel, 331 Nobel 17 engelske Nobel, 130 Nobel, 150 Nobel, 200 engelske Nobel» | the only place where plain «Nobel» stands beside «engelske Nobel» — §8 Q5 hypothesis, unverified |
| 1529, 1530 | accounts (Wilcke 7-2 p. 69) | 1 Rosenobel = 10 Mark d., 1 Engelot = 6 Mark, 1 Goltgylden = 28 ß | no |
| 1532–33 | Anders Bille's account (Wilcke 7-2 pp. 215–216; §5b) | 21 Nobler «å ca. 18 gylden å 2½ M», one thick Nobel «ca. 15 gylden»; Wilcke: «De skulde sikkert gives de højere Befalingsmænd» | **yes — the only valuation of a Danish Nobel in a record**, at the mint, as pay or gift to senior officers |
| 1540 | Recess (Wilcke I p. 50) | rhinsk Gylden / Jochimsdaler ceiling | no |
| 1542–48, 1558–62 | Sound toll tables by coin kind (Wilcke 7-4 p. 294 tbl.; 7-5 p. 346 tbl.) | columns Rosenobel, Henriksnobel, Portugaløser, Engelot, Dobb. Dukat, Guldgylden, Kejsergylden … | no column, no entry |
| 1547, 1581 | Rentekammer rates (Wilcke 7-6 p. 538) | Rosenobel 3 Dlr 10 ß, Henriksnobel 3 Dlr, Dobb. Dukat, Engelot, Portugaløser, Goldgylden … | no |
| 8 Jul 1550 | toll instruction (Wilcke 7-4 p. 292) | Rosenobler, or 3 rhinske Gylden per Nobel | «Nobel» = toll unit |
| 1602, 1604 | Forordning / Møntordning gold tables (Wilcke I pp. 69, 74–75) | Portugaløser, Ungersk Gylden, Guldklippinge | no (the `std_end` ~1602 anchor) |
| c. 1609–12 | Lower-Saxon Kreis valuation (Wilcke I p. 104) | Rosenobel, Skibsnobel, Engellot, Rhinsk Gylden … | no |
| 1622, 1629, 1639, 1640, 1647, 1648 | Danish valuations (Wilcke I pp. 223–224; Wilcke II w2a2–w2a4) | Rosenobel («Dansk og gammel engelsk Rosenobel», 1639), «Flamsk eller Henricus Nobel», Engelot, Goltgylden … | no |

**Reading.** The record is consistent with Galster's «i første Række
Pragtmønter» and Wilcke's «De skulde sikkert gives de højere Befalingsmænd»
(both already in §5–§5b): the Danish Nobler enter the sources once, at the
mint, valued per piece for distribution to officers, and never reappear in a
tariff, a toll or a rate list. That is not evidence that none circulated — a
rate list names the coins its drafter expects to meet, and ~20 surviving
pieces (Stack's Bowers on Bruun 3831) could not register in any list — but it
means **no circulation window can be reconstructed from acts**, unlike the
gulden. The two things that could still move this: (a) the 1513–14 account
text itself (§8 Q5: is plain «Nobel» there the Danish piece?); (b) hoard
evidence — none found (danskmoent «Møntfund fra Møn» has no Hans gold; no
find with a Danish Nobel surfaced in a web search 2026-10-13).

**Consequence for the data.** `nobel_fod.events.demonetisation` ~1600 stays
unsourced (§8 Q7). The honest options are to drop the event (the Denmark page
already hides the circulation layer for this bar) or to leave it hidden as
now; a dated circulation layer like the gulden's cannot be sourced. Not
applied — curator's call.

Sources read for this section beyond those of §1: Wilcke 7-1 pp. 80–81, 143;
7-2 pp. 69, 167, 215–216; 7-4 pp. 292–294; 7-5 p. 346; 7-6 p. 538; Wilcke I
pp. 50, 69, 74–75, 104, 223–224; Wilcke II w2a2–w2a4; Flensborg, «Nobler og
sølvgylden», Frederiksborg Amts Avis 29 Aug 1987
(<https://www.danskmoent.dk/artikler/pfnobler.htm>, Hans's Nobel only, no
circulation data).
