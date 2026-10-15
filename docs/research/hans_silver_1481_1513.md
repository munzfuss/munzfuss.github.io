# Danish-Norwegian silver and billon under King Hans, 1481–1513 — standard, sources, data

> **Question.** The gold of King Hans is covered (`nobel_fod`, `rhinsk_gylden_fod`).
> His silver and billon — Hvid, Søsling, Skilling, the Norwegian and Gotland issues — and
> the coins of the other issuers inside his realm in those years sit in `seed_unsorted`.
> Does that coinage fit an existing Fuß that should be extended back to 1481, or was it a
> different standard that needs a Fuß of its own?
>
> **Excluded here, with their homes:** the gold (`nobel_fod.md`, `rhinsk_gylden_fod.md`);
> Hans' Swedish Ørtug of 1497–1501 (`instruments/1480_moentordning_arboga.md`,
> `instruments/1497_moentanordning_stockholm.md` — a Stockholm-mark standard, not Danish);
> the 1513/1514 complex itself (`instruments/1514_moentordning_malmoe.md`); the pre-1481
> Danish coinage (Erik of Pomerania, Christoffer, Christian I) — touched only in §7.4.
>
> Written 2026-10-15 at the curator's request («проведи глибокий аналіз, збережи
> результати в docs»). **Nothing in data was changed by this dossier.** Every decision in
> §8 is the curator's.

## 1. Bottom line

1. **There is no Danish or Norwegian coinage ordinance of King Hans.** Wilcke 7-1 s. 144,
   Galster (galkult), Holst 1936 all say so in as many words (§3.1). The standard can only
   be reconstructed from (a) the reckoning (Gylden ↔ Mark dansk ↔ Mark lybsk), (b) one
   melt account (Mårten Myntskrivare, Svartsjö 1542), (c) modern assays (Eriksson 2017).
2. **The declared frame is the Lübeck system.** Hans' håndfæstning 1483 makes Norwegian
   coin «jevngod» with Danish; Holst and Gullbekk read that as the Lübeck system; Jesse
   shows Denmark on the Wendish system since Margrete; Hans' Skilling «regnedes god for
   lybsk Valuta» (Wilcke 7-2 s. 149); Eriksson: Skilling and Søsling weights «motsvarade
   mycket bra de lübska» (§3.2).
3. **Recomputation confirms it for the Skilling, refutes it for the Hvid.** Hans' early
   undated Skillinger (9–8 lod, 2,4–2,6 g) carry ≈ 1,2–1,3 g fine — the Lübeck Schilling of
   the 1468/1492 Rezess (103½ to the 9-lot mark = 1,271 g fine). The 1512-dated Skillinger
   are down to 6–7 lod (≈ 0,85–1,0 g fine). The Hvid was never at the Lübeck Witten: ≈ 0,2–
   0,28 g fine against the Witten's 0,355 g (1501) — valued as 3 Lübeck pfennig («densche
   drelinge»). §5.
4. **The Danish money of account sank under him.** 1 rhinsk Gylden = 2 Mark danske at the
   start of the reign, 2½ Mark danske «ved Aarhundredskiftet» (Wilcke 7-1 s. 134); the
   Skilling went for 4, then 5 Hvide instead of 3 (Wilcke 7-2 s. 149; Galster). Christian
   II's håndfæstning of 22 July 1513 restores «to mark … for en rhinsk Gylden» — the act
   that ends the period (§3.3).
5. **It does not fit `8_5_gylden_fod`.** That Fuß is defined by the Sølvgylden at 8½ to the
   mark at 14 lod, created by the 1514 Møntordning. Hans struck no silver Gylden (the cast
   «Sølvgylden» are forgeries — Galster 1947), and the 1514 grid deliberately changed the
   reckoning (Gylden = 24 ß = 72 Hvide instead of Hans' 32 ß / 96–120 Hvide). Extending it
   back would invent a coin and erase the 1513/1514 break (§6.1).
6. **Recommendation (curator's call): a separate Fuß for Hans' silver.** The form that best
   matches the sources is the period-attested **«lübischer Münzfuß»** as a global card
   (§7 of CLAUDE.md: Füße global, phases local), with Denmark-page phases for Hans
   (§7.1–7.2). The alternative is a Danish-specific card, which would need a synthesised
   name under the CLAUDE.md §0 procedure (§7.3).
7. **The data: 286 records** in `danish_realm` / `danish_norway` / `royal_holstein` belong to
   the window (incl. gold 5). 133 are type-attributable to a Galster number (directly or via
   Schou range), 153 are not — mostly single KMM specimens without a type number (§4).

## 2. Sources

| # | Source | Read in | Use here |
|---|---|---|---|
| S1 | Wilcke, *Renæssancens Mønt- og Pengeforhold 1481–1588* (1950), 1. Kap. «Kong Hans' „Møntreformer", Gyldenregning» | cache `scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-1.txt` (PDF page + 30 = printed page) | reckoning, Mårten account, no ordinance |
| S2 | Wilcke 1950, 2. Kap. (Christian II) | cache `…/wilcke_7-2.txt` | 1513/1514 grids, Hans' ß/Hvid fine weights (s. 149–155) |
| S3 | Galster, *Danmarks Mønter* (Nordisk Kultur XXIX, 1936) — danskmoent `galster/galkult.htm` | cache `scripts/cache/danskmoent/galster/galster_galkult.htm` | no ordinance; Skilling good, Hvid bad; 1513 repeats older lost ordinances |
| S4 | Galster, «De saakaldte kong Hans' Sølvgylden», NNUM 1947 s. 49–56 | cache `scripts/cache/danskmoent/hans_1481_1513/galster_1947_hans_soelvgylden.*` | cast Sølvgylden are forgeries |
| S5 | Eriksson, «Haltanalyser av danska mynt 1448–1523», *Metallanalyser av mynt* 2017:1 | cache `…/hans_1481_1513/eriksson_2017_metallanalyser.*` | 118 assays; Hans tables 7–9, summary 16 |
| S6 | Gullbekk, «Norsk mynt i dansketiden. Kong Hans (1483–1513)», NNT 2025-1 s. 4–10 | cache `…/hans_1481_1513/gullbekk_2025_nnt.*` | håndfæstning 1483; Lübeck standard; Norwegian mints |
| S7 | Holst, «Norges mynter til slutten af 16. årh.», Nordisk Kultur XXIX (1936) — danskmoent `artikler/holst.htm` | cache `…/hans_1481_1513/holst_1936.*` | Lübeck system in Norway; no ordinance; weights |
| S8 | Ingvardson, Müter, Foley, «Purse of medieval silver coins from royal shipwreck …», *JAS: Reports* 43 (2022) 103468 | cache `…/hans_1481_1513/ingvardson_2022_gribshunden.extract.txt` (PDF 48 MB not cached) | sealed purse of June 1495: only Hvide |
| S9 | Jesse, *Der wendische Münzverein* | caches `scripts/cache/coingallery/jesse_1927/_jesse_wend_muenzverein.htm` (full text, no print pagination) and `scripts/cache/danskmoent/jesse_1927/` (s. 99–104 PDF) | Lübeck standards 1424 / 1468 / 1492 / 1501 / 1506; Denmark on the Wendish system |
| S10 | danskmoent `hans.htm` + `hansgals.htm` (Galster / Schou / Sømod concordance) | caches `scripts/cache/danskmoent/galster/hans.htm`, `…/hans_1481_1513/hansgals.*` | type list, Schou ranges (§4) |

Provenance chains (C4): Galster's 1513 table (S3) is reworked by Wilcke (S2 s. 150–152)
with a different reading of «værksølv» — two readings of one referat, not two witnesses.
Eriksson (S5) takes the 1513/1514 figures from Galster 1936 (= S3) and the type list from
Galster 1972 *Unionstidens udmøntninger*; her assays are her own. Holst (S7) and Gullbekk
(S6) both rest the «Lübeck system» reading on the håndfæstning 1483 clause — one premise
read twice. Wilcke's Hans fine weights (S2 s. 152) are his own derivation from the Mårten
account (S1 s. 139–140), not a separate source.

## 3. What the sources say

### 3.1 No ordinance

- S1 s. 144: «*For Kong Hans' danske og norske Mønter foreligger der imidlertid indtil
  Dato ikke nogen Møntordning, og der kan saaledes ikke drages nogen Sammenligning mellem de
  Vejninger, der er foretaget paa Museerne, og de lovbestemte Vægte.*»
- S3: «*Der er ikke bevaret nogen dansk Møntordning fra Kong Hans, men af de foreliggende
  Mønter synes Skillingen at være en nogenlunde god Mønt; det kan derimod ikke siges om
  Hvidene, og det var dem, der prægede hele Omsætningen.*» (pool key
  `galster-nobel-hans-ingen-moentordning` already quotes the first clause)
- S7: «*Fra kong Hans har vi ingen myntordning og heller ingen forordning om vekten på edle
  metaller.*»
- S3 adds the one indirect anchor: the 1513 referat «*gentager blot Bestemmelser fra ældre,
  tabte danske Møntordninger*» (key `galster-moentordning-1513-tabte-aeldre`) — Galster's
  point is the remedium «Quintin til Fare», also in «*Kong Hans' Privilegier for
  Guldsmedene i København 1496*». It does not say WHICH figures of 1513 repeat older ones.

### 3.2 The Lübeck frame

- Håndfæstning, Halmstad 1 Feb 1483 (S6 s. 3–4, NGL 2. R. III nr. I art. 14): «*… i alle
  thesse tre steder jeffngod mynt wid Danske penninge*» — mints at Nidaros, Bergen, Oslo,
  Norwegian coin equal to Danish.
- S7: «*De norske myntene vi har fra de første oldenborgere, er ikke utmyntet efter det
  norrøne, men efter det lybske myntsystem … Danmark gikk fra slutten av 14. årh. over til
  det lybske myntsystemet*»; and «*står der i kong Hans' håndfestning at norsk mynt skal være
  jevngod med den danske. Dette innebærer at det lybske system er benyttet*».
- S6 s. 8: «*De nye myntseriene ble utgitt i henhold til lybsk myntstandard*».
- S1 s. 143: the Norwegian mints were to strike «*jevngod Mønt med den danske, o: efter
  lybsk Møntfod, saa den var gænge og gæv i Hansestæderne*»; 1491 repeated.
- S9 (s. 99, 103–104): since Margrete «*mit völliger Anlehnung an das wendische
  Münzsystem*»; after the 1424 treaty broke, «*Nur die Anlehnung des dänischen Münzwesens an
  das der Städte blieb bestehen*» — Christoffer and Christian I strike in Malmø «*Sterlinge
  und Witten (hvid) sowie einen unmittelbar nach hansischem Muster neu geschaffenen Schilling
  zu 12 Pfennigen*».
- S1 s. 142: no evidence that Hans kept his coin up to the Lübeck coin, «*som hans Fader
  Christian I. i sin Tid havde lovet Lybækkerne*».
- S5 s. 5: «*Vikten på de skillingar och söslingar som Hans präglade motsvarade mycket bra
  de lübska. Hviderna var dock mycket lättare än dess motsvarighet lübska witten och
  värdesattes endast till 3 penningar lübsk.*»

The denomination system (S7): Mark lybsk = 16 Skilling = 192 Penning; Hvid = 4 Pf.,
Søsling = 6 Pf., Skilling = 12 Pf. The «norrøne mark» = ½ Mark dansk = 8 ß stays in use as
a money of account in Norway.

### 3.3 The reckoning and its slide

- S1 s. 134: «*1 r. Gylden i Begyndelsen af Kong Hans' Tid regnedes til 2 M d. for ved
  Aarhundredskiftet at stige til 2½ M d., med andre Ord Kong Hans' Sølvmønt var daarlig*»;
  Wilcke ascribes it to «*Kong Hans' middelmaadige Hvide, som udmøntedes i store Mængder*».
  Dated instances in S1 s. 36–37, 61–62: 1503 toll at Ribe and Kolding «*hver Gylden regnet for
  2 M*»; 1508 «*8 r. G. à 2½ M*»; 1497 «*danske Hvide og 4 hvide ß som Kong Hans mønte lod*».
- S2 s. 149 (Wilcke's synthesis): Hans' Skillinger «*kostede baade 4 og 5 Hvide i Stedet for
  de almindelige 3*» and «*regnedes god for lybsk Valuta, 20 eller 24 paa Gyldenen, medens den
  Mønt, hvoraf der gik 2, senere 2½ M d. paa Gyldenen, var Korshviden*» — the «*store
  Udmøntninger af daarlige Krigshvide*» had split the currency into «*M lybsk à 16 ß lybske
  eller danske Skillinger og M dansk à 16 ß à 3 Hvide*».
- S3: «*For at tilveksle sig en Skilling, maatte Godtfolk betale Opgæld og give fire, fem,
  eller endnu flere af de ringholdige Hvide.*»
- Christian II's håndfæstning 22 July 1513: «*thue mark giør fyldest for en … rhinsk Gylden*»
  (key `wilcke-1950-haandfaestning-1513`). S5 s. 6 quotes the nobility's complaint at the
  accession: «*Thi hvor vi for en tid siden havde 100 gylden, der have vi nu ikke mere end
  80, når man regner i danske penge*».

### 3.4 The one quantitative document: Mårten Myntskrivare 1542

S1 s. 139–140 prints, from the Swedish Kammararkiv, the account of old coin remelted at
Svartsjö 1542 into Gustav I's coin:

- «*Danska Hwiter 300 mark ortr woge 74 lodige 7½ lott hulle in fine 4 lott 1 qv 1 dr*»
- «*Konungh Hansses 4 skellinge str 225 mrk woge 42 lodige 7 lott 3 qv hulle in fine 5½
  lott 3 dr*»
- the summary also names «*Konung Hanses skellinger och Marckestycker*».

Wilcke's reading (s. 144): Skilling ≈ 2,7 g «*af Finhed lidt over 5½ Lod*»; Hvid ≈ 0,90 g
(at 3 to the Swedish öre-reckoning), Hans' Hvide «*kun 4¼-lødige*»; the lot = c. 19 200
Korshvide and c. 3 600 Skillinger. In the s. 152 table he sets Hans' Skilling at **0,93 g
fine** (24 = 22,32 g per Gylden) and Hans' Hvid at **0,25 g fine** (96 = 23,04 g per
Gylden). The «Marckestycker» are why Wilcke (s. 141) supposes Hans struck lübsch
Markstücke — no specimen is known (S5 s. 6: «*Det är dock inte känt att det skulle finnas
några marker från Hans*»; Eriksson suggests they mean Sølvgylden — **hypothesis**, hers).

### 3.5 Assays — Eriksson 2017 (S5, tab. 7–9, 16)

| Type | n | Weight g | Lod (assay) | Ag % | Eriksson's dating |
|---|---:|---|---|---|---|
| Hvid Rigsrådet 1481 (G 22) | 3 | 0,68–0,86 | 5 | 26,5–27,7 | 1481(–1483) |
| Hvid Hans Malmø/Kbh/Aalborg (G 31/34/36) | 3 | 0,82–0,90 | 6 | 31,9–34,4 | early reign (assumed) |
| — same | 13 | 0,54–0,92 | 5 | 26,2–29,7 | — |
| — same | 6 | 0,68–0,85 | 4 | 22,9–24,8 | late |
| Søsling Malmø (G 30/33) | 2 | 1,31–1,47 | 5 | 28,9–29,4 | «sannolikt den senare delen» |
| Skilling undated (G 29/32/35) | 22 | 2,13–2,65 | 9→6 | 53,4–32,3 | before 1512 |
| Skilling 1512 (G 29) | 6 | 2,22–3,13 | 7–6 | 41,6–33,3 | 1512 |

Summary (tab. 16): Skilling «9/8» at the start → «6» at the end; Søsling 5 → 5; Hvid 6 → 3.
Eriksson: the Skilling «*sänkts med ca 1/3, vilket måste betecknas som en dramatisk
sänkning*». Caveats she states: only Ag calibrated; surface enrichment possible; Aalborg
over-represented; dating of undated pieces is inferential (her reasoning: dated 1512 =
lowest).

### 3.6 When did the Skilling and Søsling start? — open

- S8: the Gribshunden purse, sealed by the wreck in June 1495, holds 84 identified Hvide (39
  of Hans) and no Skilling or Søsling — «*may indicate that these nominals were not minted
  before June 1495, but the sample size … is too small*».
- S5 s. 10: Bangbostrand hoard (DMS 285, deposited perhaps c. 1490) 210 Hans Hvide, no
  Skilling; Møllegården (DMS 294) only Hans Skillinger. «*Det är emellertid också möjligt att
  skillingmyntningen startade först efter 1497*».
- The only dated pieces are 1512 (Skilling, Søsling unique). So the Skilling's start is
  between ~1495 and ~1512 — no source fixes it.

## 4. Our data — inventory (2026-10-15)

Script: scratch `hans_inv.py` (not committed) — reads `data/v2/final/{danish_realm,
danish_norway,royal_holstein}.yml`, keeps `year_first` 1475–1512 or a Hans / Johan /
Rigsråd / Gaute / Valkendorf ruler, maps to a Galster number either from `catalog.galster`
or from the Schou range in S10 within the same nominal. **286 records.**

### 4.1 Type-attributable (Galster numbers = Galster 1972 / danskmoent `hg`)

| Galster | Type | Mint | records | sources | fuss now |
|---|---|---|---:|---|---|
| 24 / 25 / 26 | Nobel ×1 / ×3 / ×2 | Malmø or Kbh | 1+1+1 | bruun, numista | `nobel_fod` |
| 27 / 28 | Rhinsk gylden / ½ | Malmø or Kbh | 1+1 | bruun, galster | `rhinsk_gylden_fod` |
| 29 | Skilling | Malmø | 21 | 18 KMM, 3 bruun | seed_unsorted |
| 30 | Søsling | Malmø | 1 | galster | seed_unsorted |
| 31 | Hvid | Malmø | 39 | 37 KMM | seed_unsorted |
| 32 / 33 / 34 | Skilling / Søsling / Hvid | København | 5 / 1 / 5 | KMM, galster | seed_unsorted |
| 35 / 36 | Skilling / Hvid | Aalborg | 3 / 14 | KMM, galster | seed_unsorted |
| 141 / 142 | Hvid | Visby | 1 / 1 | galster | seed_unsorted |
| 148–150 | Skilling / Søsling ×2 | Bergen | 1 / 2 / 1 | KMM, bruun | seed_unsorted |
| 151–153 | Hvid | Bergen | 3 / 1 / 4 | KMM, galster | seed_unsorted |
| 155 | Hvid | Oslo | 13 | 11 KMM | seed_unsorted |
| 157–160 | Hvid | Nidaros | 2 / 1 / 3 / 1 | KMM, bruun | seed_unsorted |
| 233–238 | ½ Ørtug | Stockholm, Västerås | 5 | galster, KMM | seed_unsorted (Swedish — out of this card) |

### 4.2 Not type-attributable — 153

- ~120 single KMM specimens of Hans («1 Hvid», «1 Skilling», «1 Korshvid», «1 Firehvid»,
  «(?)») with mint but no Schou number. For Hans each mint has ONE Galster type per
  nominal, so mint + nominal would identify the type — but that is the
  nominal + ruler + mint basis that §9.4 does not accept as a merge key on its own. Curator
  call (§8 D5).
- Rigsrådet 1481–83 Hvid (Galster 22): 8 KMM.
- Archbishops of Nidaros: Gaute Ivarsson (Hvid G 177, Penning G 180; bruun) and Erik
  Valkendorf (Hvid G 184, Skilling ×2 ikmk 1510–22) — Galster numbers outside the Hans list
  because they are separate issuers.
- Duke Frederik of Schleswig-Holstein: two uniface hollow Pfennige «ca 1501–10» (NGC
  cuid 167718 «MB# 5», Lange 10; cuid 167719 «MB# 8», Sch# 1362) in `royal_holstein`.
- «Hans Mule» Dobbelthvid Oslo 1523–24 (G 165) — interregnum 1523–24, NOT Hans' reign
  (S7: «*Under interregnet 1523-1524 blev det slått dobbelthvider i Oslo*»). Out of window.
- Not Hans at all, probably: «Johan» Penning Saxkøbing (KMM, MB 569–570 / 578), «Johannes»
  Penning Odense — no year; **hypothesis**: medieval (14th-c.) issues; would be settled by
  the KMM object records. Also Johan Adolf / Johan Frederik / Hans Adolf / Hans den Yngre
  entries are 16th–17th-c. dukes (matched by name only).
- Undated anonymous KMM «Skillingsmønt», «Søsling?», «Regnepenning» 1500–1700 — no ruler;
  not attributable from the record.

### 4.3 Data points that look wrong (candidates — verified only as far as stated)

| Record | What | Checked |
|---|---|---|
| `kmk-643973` Hans Skilling **1517** | Hans died 1513 | KMM cache `scripts/cache/kmk/643973.json` says authority «Hans», yearFrom 1517 — the SOURCE carries it; `trace_coin why` prints no decision. Source inconsistency, not ours. |
| `unified-dk-bruun-3837` Skilling Malmø, year_label **1512-1515** | Bruun lot 11150 prints 1512; seed year_label 1512 | the range comes from another member of the 3-source class — not traced further |
| KMM Hans Hvide with Norwegian Schou numbers in `danish_realm` (e.g. `kmk-106768` Schou 203, `kmk-130618` Schou 197) | Schou 187–213 = Oslo (G 155) | entity question (danish_norway?) |
| KMM `galster` values 3, 15, 23, 41, 57B, 115 on Hans records | not Hans' Galster numbers (Hans = 24–36, 141–162, 230–238) | **hypothesis**: another numbering or a KMM misprint — open |
| KMM «1 Hvid, forfalskning», «samtidig forfalskning», «piefort» | contemporary counterfeits / piefort | §9 exclusion candidates — curator |

**Already logged elsewhere** (not re-claimed here): the 8½-Gylden-fod card gives the 1513
small-coin figures (Skilling 96/M 5¾ lod, Hvid 222/M 4½ lod) as the 1514 ordinance's — 1514
is 88/M 6 lod and 220/M 5 lod (`instruments/FUSS_REVIEW_FINDINGS.md` line 41,
`instruments/1514_moentordning_malmoe.md` §4.3).

## 5. Recomputation

Cologne mark 233,856 g (project convention; Galster uses ~230 g for Denmark c. 1500 — S3).

**Lübeck standards (S9, Jesse's figures re-derived):**

| Rezess | Coin | per mark | lot | rough g | fine g |
|---|---|---:|---:|---:|---:|
| 1468 = 1492 | Doppelschilling | 69 | 12 | 3,389 | 2,542 |
| 1468 = 1492 | Schilling | 103½ | 9 | 2,259 | **1,271** |
| 1492 | Sechsling | 188–190 | 8 | 1,24–1,23 | 0,62 |
| 1501/02 | Witten | 216 | 5¼ | 1,083 | **0,355** |
| 1506 | Markstück | 13 per fine mark, 15-lot | — | 19,18 (Jesse) | 17,99 |

Jesse checks: «*eine Mark oder 192 Pfennige nach dem Münzfuß von 1492 noch 19,392 g Silber
enthalten müßte*» — our 16 × 1,271 = 20,34 g; Jesse's 19,392 g implies 1,212 g per
Schilling, i.e. a mark of ≈ 223 g. 5 % apart; **open** (Jesse's mark weight is in his
omitted notes).

**Hans (assays, S5; fine = weight × Ag %):**

| Coin | weight | Ag % | fine g | vs Lübeck |
|---|---:|---:|---:|---|
| Skilling, 9 lod (early) | 2,47 | 50–53 | 1,24–1,32 | = Schilling 1492 (1,271) |
| Skilling, 8 lod | 2,16–2,60 | 44,7–48,3 | 1,0–1,2 | −10…−20 % |
| Skilling, 6 lod (1512) | 2,45–2,66 | 33–36 | 0,85–0,93 | −30 % |
| Mårten 1542, Skilling | ≈ 2,7 | 5½ lod + = 34,4–35 % | ≈ 0,93 | −27 % |
| Hvid, 6 lod | 0,82–0,90 | 32–34 | 0,27–0,30 | 0,8 Witten |
| Hvid, 5 lod | 0,54–0,92 | 26–30 | 0,15–0,27 | 0,4–0,75 Witten |
| Mårten 1542, Hvid | ≈ 0,90 | 4¼ lod = 26,6 % | ≈ 0,24 | 0,67 Witten ≈ 3 Pf. lübsch |

**Silver per Gylden of account:**

| Reckoning | composition | fine g |
|---|---|---:|
| Hans, Skilling, 24/G (lübsch) | 24 × 0,93 | 22,3 (Wilcke s. 152: 22,32) |
| Hans, Hvid, 96/G (2 M d) | 96 × 0,25 | 24,0 (Wilcke: 23,04 at 0,24) |
| Hans, Hvid, 120/G (2½ M d) | 120 × 0,21 | ≈ 25 |
| 1513 Blicher, Skilling 32/G | Galster 0,75 / Wilcke 0,875 | 24,0 / 28,0 |
| 1514, Skilling 24/G (88/M, 6 lod) | 24 × 0,996 | 23,9 |
| 1514, Sølvgylden 8½/M, 14 lod | 1 × 24,07 | 24,07 |

Reading (this dossier's, **not stated by a source as such**): from 2 to 2½ Mark danske per
Gylden the Hvid's fine content fell roughly in step, so the Gylden stayed near 23–25 g of
fine silver in Hvide — the Danish mark depreciated, the Gylden did not. Wilcke says the
same in words (s. 134: the Hvide «*kunde ikke opretholde deres Værd overfor 1 god og gæv r.
Gylden*»). ~24 g of fine silver per Gylden is also what 1514 fixed in all three tiers.

## 6. Does it fit an existing Fuß?

### 6.1 `8_5_gylden_fod` (1514–1523) — no

- Defined by the Sølvgylden, 8½ to the mark at 14 lod (fuesse.yml `grid_stops 8.5`,
  `fineness_standard 0.875`), created by the 1514 Møntordning. Hans struck no Sølvgylden:
  S4 — the known «Hans Sølvgylden» are casts, «*ikke hører hjemme i den danske Møntrække*»;
  Galster's list has them as «Falske mønter» G 253.
- The 1514 grid changed the reckoning: «*inddele Gyldenen i 24 ß og 72 Hvide … som i
  Hansestæderne: 24 og 72 i Stedet for 32 og 96*» (S2 s. 155). Hans' Hvid stood at 96 →
  120 to the Gylden; the 1515 Sjælland letter moves the old Korshvid from 4 to 5 to 6 per
  Skilling (S2 s. 156–158, `instruments/1514_moentordning_malmoe.md` §4.4).
- What carries over is only the Gylden-value of ~24 g fine silver (§5) — a continuity of
  the money of account, not of a coinage standard.

### 6.2 `rhinsk_gylden_fod` (gold) as the parent of the small coin — not recommended

There is a sourced argument: reckoning in Gylden (S1 s. 35: «*foretoges Optællingen dog i
Gylden, Mark og Skilling*»), the Hvide «*kun Skillemønt*» (S1 s. 36), and §8a's Scheidemünze
residual places small coin under the period's full-value standard. Against it: CLAUDE.md §8a
step 1 drops a fuss of the other metal; the Skilling was not token coin but the Lübeck
Schilling (§5); a gold card would carry three silver tiers in three mints and two kingdoms.

### 6.3 Any other existing Fuß — no

The silver Füße in `fuesse.yml` start 1514 (`8_5_gylden_fod`), 1524, 1537. None is the
Lübeck system of the 15th century; the Lübeck page itself starts at 1559 (mission scope).

## 7. Proposal — a Fuß for Hans' silver

### 7.1 Form A (recommended): global «lübischer Münzfuß»

- **Name.** «Lübischer Müntzfuß» is in CLAUDE.md's list of Müntzfuß names (i18n policy);
  Jesse uses «lübischer Münzfuß» throughout (title of Grautoff 1836: «über den lübischen
  Münzfuß bis 1463»); Gullbekk «lybsk myntstandard»; Wilcke «lybsk Møntfod». Period-
  and literature-attested — **no synthesised-name procedure needed**, but the exact card
  string (Lübischer Müntzfuß / Lübischer Münzfuß / Lybsk Møntfod) is the curator's per §2
  tier 1.
- **Founding (C1):** the Wendish Münzverein Rezesse — 1424 (with Denmark), 1468, 1492
  (31 articles, Schilling 103½ from the 9-lot mark), 1501/1504/1506 (Witten, Markstück).
  For Denmark: håndfæstning 1483 (Norway «jevngod» with Danish) + Christian I's promise to
  Lübeck (S1 s. 142).
- **Global card, local phases.** On the Denmark page (proposal; boundaries per §7.2):
  - **Phase 0 · Rigsrådet 1481–1483** — Hvid Malmø (G 22), 5 lod (S5 tab. 6). Optional.
  - **Phase I · Hans, Hvid-only coinage, ~1483–1495/97** — Hvid at Malmø, København,
    Aalborg, Visby, Bergen, Oslo, Nidaros; Gylden = 2 M d; Hvid 6 → 5 lod.
    Evidence for «Hvid only»: S8 (1495), S5 (Bangbostrand).
  - **Phase II · Hans, Skilling and Søsling, ~1495/97–1513** — Skilling at the Lübeck
    Schilling (9–8 lod) falling to 6–7 lod by 1512 (the dated pieces); Søsling 5 lod;
    Hvid 5 → 4 lod; Gylden 2½ M d; 4–5 Hvide per Skilling. End: håndfæstning 22 July 1513.
  - **Archbishops of Nidaros** (Gaute Ivarsson 1475–1510, Erik Valkendorf 1510–22, Hvid /
    Penning / Skilling): S7 «*Erkebiskop Gautes hvider og penninger slutter sig ved sin vekt
    til de kongelige mynter av samme slag*» — same tiers; issuer differs. Place in the same
    phases (curator D3).
  - **Duke Frederik of Holstein, Hohlpfennige ca. 1501–10** — Holstein is imperial, the
    pieces are Lübeck-type hollow pfennige by type; **no source in hand states their
    standard** (gap). Belongs here only if the card is global; otherwise out.
- **Cessation:** Denmark leaves it with the 1513 Blicher grid (own Mark dansk, 32 ß/G) and
  returns to Lübeck reckoning with the 1514 grid (24 ß/G) inside `8_5_gylden_fod` — so the
  Denmark-page bar ends 1513; the global card's end (Lübeck's own 1506 Mark standard →
  Talerprägung) is a separate question if the card is ever shown on a German page.

### 7.2 Phase boundary problem

No act separates Phase I and II. Candidates, all indirect: 1495 (purse terminus — earliest
possible), 1497 (war with Sweden, Eriksson's suggestion), «Aarhundredskiftet» (Wilcke's
2 → 2½ M d). A single phase «Hans 1481/83–1513» avoids inventing a boundary; two phases
need an approximate (`~`) boundary marked as indirect, per the curator's rule for indirect
ends (2026-10-11).

### 7.3 Form B: a Danish-specific card

If the curator prefers the card to show the Danish Hvid as the defining coin (it «prægede
hele Omsætningen» — S3), the defining value would be the Gylden-in-Hvide (96 → 120 per
Gylden, ~24 g fine). No period name exists for such a standard («Hvid-», «Mark-dansk-» +
«-fod» are not attested) → CLAUDE.md §0 synthesised-identifier procedure (report absence →
propose → explicit «так» → annotate). It would also cover Christian I and Christoffer
(Hvid since c. 1440, S9) if extended.

### 7.4 Scope extension

CLAUDE.md «Mission temporal scope» puts the Danish lower bound at **1514**. The gold cards
already reach 1496/1497; a silver card for 1481–1513 widens the documented scope for silver
too. If accepted, the CLAUDE.md lower-bound paragraph needs a sentence. Pre-1481 records in
data for reference: Christian I 65, Christoffer 9, Rigsråd 1448 9 (all `danish_realm`,
`seed_unsorted`).

## 8. Decisions for the curator

| # | Decision | Options |
|---|---|---|
| D1 | Separate Fuß for Hans' silver? | A global «lübischer Münzfuß» (§7.1) · B Danish-specific, synthesised name (§7.3) · C leave in seed_unsorted |
| D2 | Phases | one phase 1481/83–1513 · two with an approximate boundary (§7.2) · + Rigsrådet 1481–83 |
| D3 | Archbishops of Nidaros | same card, own rows · out |
| D4 | Duke Frederik's Holstein Hohlpfennige 1501–10 | on the card (global) · out |
| D5 | ~120 KMM Hans specimens without Schou | merge into the Galster type by mint + nominal (Hans has one type per mint) · leave as separate rows · leave unsorted |
| D6 | Counterfeits / piefort in KMM | §9 exclusions · keep |
| D7 | Mission lower bound | add Hans' silver (1481) to CLAUDE.md scope |

**Curator decisions 2026-10-15:** D1 → A (global «lübischer Münzfuß»); D2 → one phase for now;
D3 → other issuers only if their territory belonged to Denmark directly or as a vassal;
D4 → no merge for now; D5 → keep provisionally, verdict per case; D6 → yes, scope from 1481.
The work plan with its checklist: `luebischer_muenzfuss_plan.md`.

## 9. Open questions — and what would settle each

| Question | Would be settled by |
|---|---|
| When did Skilling / Søsling coinage start (1495–1512)? | Märcher, «Et differentieret møntvæsen ca. 1480–1550», *Denar til Daler* (2018) s. 426–495 (paper); dated hoards in *Danmarks middelalderlige skattefund* (Jensen et al. 1992) |
| Which 1513 figures repeat Hans-era ordinances (Galster's «ældre, tabte»)? | the 1496 goldsmiths' Skraa text (Wilcke s. 151 cites it for 14-lødig værksølv) — not seen |
| Hans' «Marckestycker» (1542 account) — real coin or Sølvgylden? | a specimen or a second account; none known (S5, S4) |
| Jesse's 19,392 g per Mark lübsch 1492 vs our 20,34 | Jesse's printed footnote (the coingallery text omits notes) — print edition |
| Duke Frederik's hollow pfennige standard | Lange 1908 (paper) or a Holstein/Lübeck recess naming ducal pfennige |
| KMM «galster» values 3/15/23/41/57B/115 on Hans records | the KMM object pages |
| Gribshunden: further coins from later excavation seasons | future publications of the wreck |
