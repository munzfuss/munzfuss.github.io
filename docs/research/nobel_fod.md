# `nobel_fod` — the Danish gold Nobel standard (1496–1532): research dossier

> **Status:** internal research dossier (role-1). Rewritten 2026-09-28 after the
> Nobelfod card revision (commits `2fdd18d` … `b88bb76`); supersedes the 2026-06-05
> version, whose retracted claims are kept in §9 with what disproved them.
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
| `galster-unionstidens-nobel` | Georg Galster, **«Danmarks Mønter»**, transcribed on danskmoent.dk `galster/galkult.htm` | Narrative survey; carries its own re-computed tables of the 1513/1514/1524 ordinances | Primary *interpretation*. **Title correction:** the page is «Danmarks Mønter», NOT Galster's catalogue «Unionstidens Udmøntninger» (1972) — the refs_pool key keeps its old name (stable key, §5b), the body names the right work. The transcription is unpaginated → the verbatim quote is the locator. |
| `wilcke-1950-nobel-ordinance` | Julius Wilcke, *Renæssancens Mønt- og Pengeforhold 1481–1588* (1950), ch. 2, danskmoent PDF «Wilcke 7-2» | Transcribes the ordinances (Suhm, Rigsarkivet) + own table | Primary for the **ordinance texts**. Paginated → page hints below. |
| `danskmoent-1nobel` | danskmoent.dk `1nobel.htm` | Type list per ruler (Galster / Schou numbers, rarity) | Derived from Galster's catalogue. |
| `danskmoent-nobel-finhed-f1g45` | danskmoent.dk `fr/f1g45.htm` (+ `fr/f1g69.htm`) | Type pages printing «Bruttovægt 14,375g, Finhed 0,979, Finvægt 14,08g» | **Derived from Galster's conversion table**, not a measurement — see §4.3. |
| — (coin-row source only) | Numista 428544 (1 Noble 1532) | «Gold (.979)», 14.375 g; references_list = `["Fr# 12", "Galster UU# 45"]` | **Derived from Galster** — same triple, cites only Galster. Not independent of danskmoent. |
| `stacksbowers-bruun-1496-nobel` | Stack's Bowers, L. E. Bruun Part I, lot 1001 (14 Sept 2024) | Auction description, Hans 1496 | Secondary; carries the «first dated Scandinavian coin» claim and the survival count. |
| `wikipedia-troy-weight-dutch-mark` | en.wikipedia «Troy weight», Dutch-troy passage | Metrology: «The mark was rated as 3,798 troy grains or 246.084 grams.» | Tertiary; used only for the gram value of the Dutch troy mark. |

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
