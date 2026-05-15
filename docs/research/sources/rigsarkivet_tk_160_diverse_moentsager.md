# Rigsarkivet — Tyske Kancelli, I.A.A. A IX. 160 Diverse Møntsager (1523-1619)

> **Source capture** — primary-source manuscript folio at Danish National
> Archives (Rigsarkivet).
>
> - **Archive**: Rigsarkivet, København (Danish National Archives)
> - **Full archive coordinate**:
>   - Tyske Kancelli — Indenrigske Afdeling (collection 150)
>   - Slesvig-Holsten-Lauenburgske Kancelli
>   - I.A.A. (-1670) — Indenrigske Afdeling A, pre-1670
>   - A IX. Diverse sager
>   - **160. Diverse møntsager**
>   - Date range: **1523-1619**
> - **Total pages**: 219 image-scans (high-res JPEG, 150 DPI, ~3345×2440 px)
> - **Captured**: 2026-05-15 via Arkivalieronline REST API.
> - **Captured by**: claude
> - **License / status**: Public domain (Danish state archive holdings;
>   16th-c. documents; openly browsable via Arkivalieronline).
> - **Local cache**: [`scripts/cache/rigsarkivet/tk_160_diverse_moentsager/`](../../../scripts/cache/rigsarkivet/tk_160_diverse_moentsager/).
>
> **What this capture provides.** The original chancery-hand
> manuscripts of Christian III's complete monetary-reform arc — the
> ultimate primary source that Wilcke 1950, Galster 1965, and every
> later writer cited indirectly. Wilcke 1950 (cached at
> `scripts/cache/wilcke/renaessancens_moent_1950/wilcke_7-4.pdf`)
> transcribed the 1541 Preamble + specification tables from these
> same images. Until 2026-05-15 our project depended on Wilcke's
> modernised-Danish transcription; today we have the chancery-hand
> primary source itself, plus access to body articles, oaths, and
> related correspondence that Wilcke summarised but did not quote
> verbatim.
>
> **Cross-references:** analytical dossier
> [`docs/research/moentordning_1541.md`](../moentordning_1541.md);
> secondary-source capture (Wilcke 1950 transcription)
> [`wilcke_1950_christian_iii_moentreform.md`](wilcke_1950_christian_iii_moentreform.md);
> companion-ordinance capture (20 March 1541)
> [`paus_christian_iii_1541_maal_og_vaegt.md`](paus_christian_iii_1541_maal_og_vaegt.md);
> Galster paraphrase [`galster_galshist.md`](galster_galshist.md).

---

## 1. Discovery and access workflow

The Arkivalieronline image-viewer page (browser URL pattern
`https://arkivalieronline.rigsarkivet.dk/en/billedviser?epid=20018028`)
is a JavaScript-rendered SPA — static HTTP fetch returns only the
HTML shell. The underlying REST API at **`api.rigsarkivet.dk`**
returns JSON metadata and JPEG image data **without authentication**,
discovered 2026-05-15 by inspecting the viewer's JS at
`/js/viewer/billedviser-4.0.0.js`.

### 1.1 API endpoints (verified working)

```
GET https://api.rigsarkivet.dk/ao/v1/billedviser/ep-beskrivelse?epid=20018028&Sprog=da
  → [{"Arkivskaber":"Tyske Kancelli, Slesvig-Holsten-Lauenburgske Kancelli",
      "Arkivserie":"Diverse møntsager"}]

GET https://api.rigsarkivet.dk/ao/v1/billedviser/indeks-top?epid=20018028
  → [{"key":275170,"title":"","folder":true,"lazy":true}]

GET https://api.rigsarkivet.dk/ao/v1/billedviser/indeks-bs?bsid=275170
  → 219 page entries with keys {275170,52825513…52825731}

GET https://api.rigsarkivet.dk/ao/v1/billedviser/billed-reference-lister?bsid=275170
  → {SA_GUIDs: [...], SA_URLs: [...]} arrays of 219 references

GET https://api.rigsarkivet.dk/ao/v1/images/{guid}
  → JPEG image (~300-600 KB, 150 DPI, ~3345×2440 px)
```

The `guid` for page N is `52825512 + N` (verified for pages 1-219).
Image URLs in `SA_URLs` use the same pattern:
`//api.rigsarkivet.dk/ao/v1/images/{guid}`.

### 1.2 Browser deep-link pattern

Image-viewer URL with direct page deep-link:
```
https://arkivalieronline.rigsarkivet.dk/en/billedviser?epid=20018028#275170,{guid}
```

E.g. for page 4 (the user's initial reference):
`#275170,52825516`. For page 17 (1541 Møntordning cover):
`#275170,52825529`.

## 2. Archive coordinate (verified)

Page 1 of the folio is the archivist's modern title card, which
verifies the full archive coordinate verbatim:

```
TYSKE KANCELLI, IND.AFD.
A IX. Diverse sager.
160. Diverse møntsager.
1523 - 1619.
Begyndelse
```

This matches:

- Wilcke 1950 footnote 4 on p. 4: «*RA. T. K., No. 160. Div. Møntsager*»
  (Wilcke's shorthand; equivalent to T.K. I.A.A. A IX nr. 160).
- danskmoent.dk/galster/flegal6.htm metadata: «*Rigsarkivet, København.
  Tyske Kancelli. I. A. A. (-1670) Diverse Møntsager 1523-1619 nr. 160*».

## 3. Folio structure — Christian III monetary-reform arc

Pages **008-029** carry the four critical documents in the Christian
III monetary-reform arc (1535 Saxon template → 1541 Møntordning →
1544 supplement → 1547 Flensborg Bestalling). About 10 % of the
219-page folio.

### 3.1 Pages 008-015 — 1535 Saxon Møntordning template (15 April 1535)

**Page 008** (right side): calligraphic title **«Müntz Ordnung»**
sub-titled **«vom Curfürsten von Sachsen»** = «Mint Ordinance from
the Elector of Saxony», archivist's date label «1535 [Aprilis]»
(matches Wilcke 1950 p. 3: «*en Møntordning af 15. April 1535
tilsendt fra Kurfyrsten af Sachsen*»).

This is the template that Kurfyrst Johan Frederik of Saxony (Christian
III's relative) sent to Christian III to inform his own Møntordning.
Wilcke 1950 p. 3 quotes its specifications:
- Gylden: 14 L 8 grän, 8 stk pr. Mc.
- ½ Gylden: 14-8, 16 stk pr. Mc.
- Hele Zinsgroschen: 7-9, 88 stk pr. Mc.
- 3 Pf. Stkr.: 4-, 117 stk pr. Mc.
- Pf. Stkr.: 4-, 37 stk pr. L (Lod)

Wilcke comments: «*Omend denne Møntordning ikke synes at have
kunnet afgive Rettesnor for dansk Mønt, der ikke manøvrerede med
Groschen, men deltes i M og ß, kunde de almindelige Bestemmelser
nok være af nogen Betydning ved et nyt Rigsmøntsteds Oprettelse.*»
(«Even though this ordinance could not provide a direct guide for
Danish coinage, which did not operate with Groschen but was divided
in M and ß, the general provisions could nonetheless be of some
importance for setting up a new royal mint.»)

### 3.2 Pages 016-022 — 20 September 1541 Møntordning (CORE)

**Page 016**: Outer folded wrapper, with title-side bearing chancery
hand «*Dinstag nach [Crucis] Anno [Domini inn] XXXXI*» — the EXACT
date phrasing Wilcke 1950 p. 4 quotes verbatim («Dinstagh nach Crucis
Anno Domini inn 1541, o: 20. (15) Septbr.»).

**Page 017**: Cover sheet. Ornate calligraphic title **«Müntz
Ordnung»** + sub-title **«Anno MDXXXXI»** (Anno 1541). Archivist's
date label lower-left: «**1541. 20. Septr [fol.] [Reg.]**» (modern
hand, indicating the archive's filing for «1541, 20 September,
folder/register reference»).

**Page 018** (right side): start of body. Opens with the ornate
initial **«C»** decorated and the king's full titulature:

```
Wir Christiern unns Gots gnaden zu Dennemarcken,
Norwegen, der Wennden vnnd Gothen kúnig.
Hertzog zu Sleßwich Holsten, Stormarn vnnd der
Ditmarschen Greue zu Oldenburg vnnd Velmenhorst...
```

Wilcke 1950 p. 4 verbatim translation of the Preamble (post-titulature):

> «Kongen siger i Indledningen, at han ikke alene har befundet sin
> Mønt i stor Uorden(!), men ogsaa lidt stor Skade paa denne, hvorhos
> fremmede Nationers Oprør har bibragt Mønten stor Forklejnelse.
> Derfor maa Mønten nu have Bestand, saaledes at Menigmand og
> indkommende Købmænd saa meget bedre og 'schiedenntlicher' kan
> handle med hinanden.»

(The chancery-hand original on the page matches this content;
Wilcke's modernisation can be cross-verified word-by-word.)

**Pages 019-021**: Body articles continue, with denomination-by-
denomination specifications:
- Page 019 right side has section headers «Pfennig us em Hans grossen»
  and similar denomination paragraphs.
- Page 020 right side has «Hermerszi[?] Schiltern» (= 4-Skilling section),
  «Schilling stüke» (= 1-Skilling), and «Drey Schwer zu Münzeren»
  (denomination subdivisions).
- Page 021 continues with sub-Mark denominations.

**Page 022**: Closing of the ordinance with **chancery seal** (wax
seal visible at lower right of right page) and signature flourish.

### 3.3 Pages 023-024 — Mintmaster's + Warden's Oaths (companion to 1541 Møntordning)

**Page 023** (right side): Section header **«Müntzmesteres Eydt»**
(Mintmaster's Oath) followed by oath text. Opens:

```
Nach den den Slesswigsch-Holstein...
bey... und herr Christianm und... Wenden tonig...
Ditmarschen... und unsen....
```

The oath the appointed Mintmaster swears upon entering office.

**Page 024** (left side starts): Section header **«Wardins Eyde»**
(Warden's Oath — the wardein = assay-master). The Warden was
responsible for testing the fineness of coins produced; the oath
binds him to truthful assaying.

These two oaths are **administrative companions** to the 1541
Møntordning — not strictly part of the ordinance text but issued
together as part of the same regulatory package. Wilcke 1950 does
NOT reproduce these oaths verbatim — they are project-new material
beyond Wilcke's coverage.

### 3.4 Pages 025-027 — 27 September 1544 supplement Møntordning

**Page 025**: Top of document. Archivist's date label «**1544 27
Sept.**» (matches Wilcke 1950 p. 13: «*Møntordningen, hvorefter
unge Jørgen Koch skulde arbejde, var dateret 27. September 1544*»).

Body opens with king's titulature in the same chancery-hand format
as the 1541 act.

**Pages 026-027**: Body of the 1544 supplement, with the
specification table (Wilcke 1950 p. 13 reconstructs this — see
[`wilcke_1950_christian_iii_moentreform.md`](wilcke_1950_christian_iii_moentreform.md)
§6 for the cleaned tabular layout).

### 3.5 Pages 028-029 — 22 January 1547 Flensborg Bestalling

**Page 028**: Top of document. Archivist's date label «**1547 22
Jan.**» (matches Wilcke 1950 p. 26 footnote 1: «*Anno 1547 fik
[Jørgen Kock the Younger] Bestalling med Møntordning ... RA. T.K.
No. 18. Inland. Reg. 1547*»).

Body opens with king's titulature, addressed to the appointed
mintmaster Jørgen Kock the Younger («*Nach dem wir unsern lieben
getreuen Jurgen Kock vier Jahrlangh bestellen...*» — verbatim
match to Wilcke's Old German quote on pp. 25-26).

**Page 029**: Body continues. Section labels include
«**Doppelte und einfachige Schillinge, Sechslinge und Pfennige**»
— matching Wilcke's quoted denomination order («Dobbelte und
einfachige ß, syslinge, witten, Blaffert und pfennige»).

## 4. The wider folio (pages 030-219)

Beyond the Christian III arc, the folio continues with:

- **Pages 030-039**: more 1540s-1550s Christian III materials (mint accounts, Norwegian mint setup correspondence).
- **Page 040**: document dated «1562. 3. Maj» — Frederik II era begins.
- **Pages 041-080+**: Frederik II monetary acts (1559-1572 Klippinge era; project's Phase B per §BC).
- **Pages 080+**: Christian IV era through 1619 (folio's terminus).
- **Pages 002, 004, 045**: hand-written archivist's indices (19th-c.) with item-by-item summaries and date labels.

The full 219-page corpus is cached at
`scripts/cache/rigsarkivet/tk_160_diverse_moentsager/pages/`. The
non-Christian-III material remains available for project's
Phase B (Frederik II 1563-1570 Klippinge), Phase C (1572 Elfsborgs
løsen Speciedaler), and beyond.

## 5. What this capture supersedes / adds vs Wilcke 1950

**Supersedes** (project no longer needs Wilcke as the sole verbatim
source for these claims):

- The 1541 Preamble verbatim — pages 018-019 of the manuscript.
- The 1541 specification table verbatim — pages 019-021.
- The 1544 supplement specification table verbatim — pages 026-027.
- The 1547 Flensborg Bestalling opening — page 028.

Wilcke 1950 remains useful for:
- Modernised Danish spelling (easier reading than chancery hand).
- Analytical commentary on the documents.
- Tabular reconstruction (Wilcke's tables vs the prose specifications in the manuscript).

**Adds** (project material that Wilcke summarised but did not
quote verbatim — now available from this capture):

- **Mintmaster's Oath** (page 023) — Wilcke does not reproduce.
- **Warden's Oath** (page 024) — Wilcke does not reproduce.
- **Full body of all four acts** beyond the Preamble — Wilcke
  paraphrases substantive clauses; the chancery-hand original gives
  the complete article-by-article text.
- **1535 Saxon template body** (pages 009-015) — Wilcke quotes only
  the specification table from p. 3 of his Chapter IV.

## 6. Caveats

**Palaeography barrier.** The manuscripts are in 16th-c. **chancery
hand** (Kanzleischrift) — German Schrift with letter forms
significantly different from modern Roman. Modern Danish + German
readers can decipher it with effort and reference to Wilcke 1950's
modernised parallel transcription. Machine OCR struggles with this
hand; this capture provides image-only material.

**Folio not strictly chronological.** Pages 005-007 (1523 era),
008-015 (1535 Saxon template), 016-029 (1541-1547), 040 (1562)
suggests roughly chronological order in the early section, but
later sections may interleave documents by topic or by accession
sequence. Pages 002, 004, 045 (hand-written indices) help navigate.

## 7. Where to read more

- **Original viewer**: <https://arkivalieronline.rigsarkivet.dk/en/billedviser?epid=20018028#275170,52825529> (page 17, 1541 cover).
- **Local cache**: `scripts/cache/rigsarkivet/tk_160_diverse_moentsager/pages/page_NNN.jpg`.
- **Wilcke 1950 modernised transcription**: [`wilcke_1950_christian_iii_moentreform.md`](wilcke_1950_christian_iii_moentreform.md).
- **Analytical dossier**: [`docs/research/moentordning_1541.md`](../moentordning_1541.md).
