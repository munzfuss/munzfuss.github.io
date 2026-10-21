# Eriksson 2017 — XRF assays of Danish coins 1448–1523: inventory, match to our data, pipeline question

> Role-1 note (AI / curator). Opened 2026-10-21 on the curator's question «what can this source give our coin
> rows, and is it worth connecting as a pipeline source?». **Analysis only — nothing in `data/v2/**` changed, no
> seed written.** Companion sections: `luebischer_muenzfuss.md` §0.5–§0.6 (dating scheme that uses these assays),
> `hans_silver_1481_1513.md` §3.5 (Hans rows summarised), `hans_rates_1481_1513.md` §5–§6.

**Source.** Sarah Eriksson, «Haltanalyser av danska mynt 1448-1523», *Metallanalyser av mynt* 2017:1
(Numismatiska forskningsgruppen, Stockholm University), 20 pdf pages (text s. 1–16, editorial s. 17–19).
Cache: `scripts/cache/danskmoent/hans_1481_1513/eriksson_2017_metallanalyser.{pdf,extract.txt}`;
URL `https://www.danskmoent.dk/pdf/Metallanalyser%20av%20mynt_2017_1.pdf` (SOURCES.md line ~705 has the Wayback
copy). Page numbers below are the printed ones.

**Method (s. 17–18, editorial by K. Jonsson; s. 16–17 S. Isaksson).** Portable XRF (Olympus Delta), obverse
surface, not cleaned; only **Ag is calibrated** (three standards; error «+/- 0,8%»); Cu and Sn are not calibrated
(Sn ≈ 10 % of Ag, «*should be ignored*»), values re-normalised to 100 %. Lod groups are the editor's bins
(«*8 lod = 50,00-43,26%*», i.e. each lod from its exact value down to just above the next lower one). Material:
**Kungl. Myntkabinettet, Stockholm** (systematic collection + finds). ⚠ Name clash: our `kmk-*` seeds are KMM
**Copenhagen** (natmus) — Eriksson's specimens are NOT our KMM objects; no specimen-level link exists.

---

## 1. Inventory (every table row)

Columns: G = Galster 1972 number as printed; n; weight g; lod (Eriksson's bin); Ag %. A row with n = 1 is a
**specimen**; a row with n ≥ 2 is a **group**: min–max of weight and min–max of Ag over n pieces, **unpaired**
(the lightest piece is not necessarily the poorest). 37 rows, 115 coins: **45 specimen rows (45 coins) + 24
group rows (70 coins)**.

### Tab. 4/5 — Christian I, Hvid, Malmö, «1448-1481», G 23 (title → letter via tab. 4: 23a R'D', 23b REX·D',
23c D'G'R'D', 23d DEI G'R'D')

| # | G | n | Weight | Lod | Ag % |
|---|---|---:|---|---:|---|
| 5.1 | 23d | 2 | 0,82–0,75 (printed «0,82-075») | 8 | 45,78–45,19 |
| 5.2 | 23c | 2 | 0,72–0,60 | 8 | 49,17–43,91 |
| 5.3 | 23d | 3 | 0,93–0,64 | 7 | 38,74–37,44 |
| 5.4 | 23b | 2 | 0,93–0,82 | 7 | 42,11–37,96 |
| 5.5 | 23d | 2 | 1,48–0,79 | 6 | 34,60–33,32 |
| 5.6 | 23b | 2 | 1,00–0,90 | 6 | 32,53–31,60 |
| 5.7 | 23c | 2 | 0,87–0,70 | 5 | 29,88–29,05 |
| 5.8 | 23a | 5 | 1,08–0,58 | 5 | 28,55–25,14 |
| 5.9 | 23c | 1 | 0,71 | 4 | 22,40 |
| 5.10 | 23a | 1 | 0,94 | 3 | 13,25 (Eriksson s. 7: possibly contemporary forgery) |

Text s. 7 also names a near-pure-copper forgery (3 % Ag) — **not** in tab. 5. Tab. 4 counts per title
(6/4/5/7 = 22) agree with tab. 5 (a 6, b 4, c 5, d 7).

### Tab. 6 — Rigsrådet 1481, Hvid, Malmö, «1481», G 22 — all specimens
0,84 g 27,65 % · 0,68 g 27,24 % · 0,86 g 26,54 % (all 5 lod).

### Tab. 7 — Hans, Skilling

| # | Mint | Dating | G | n | Weight | Lod | Ag % |
|---|---|---|---|---:|---|---:|---|
| 7.1 | Malmö | 1481-1511 | 29 | 2 | **2,47** (one figure for two pieces) | 9 | 51,54–50,23 |
| 7.2 | Köpenhamn | 1481-1511 | 32 | 1 | 2,37 | 9 | 53,42 |
| 7.3 | Malmö | 1481-1511 | 29 | 3 | 2,56–2,16 | 8 | 48,29–45,68 |
| 7.4 | Köpenhamn | 1481-1511 | 32 | 2 | 2,60–2,46 | 8 | 45,49–44,70 |
| 7.5 | Malmö | 1481-1511 | 29 | 4 | 2,65–2,19 | 7 | 41,52–**36,65** ⚠ |
| 7.6 | Köpenhamn | 1481-1511 | 32 | 2 | 2,43–2,26 | 7 | 41,43–39,02 |
| 7.7 | Ålborg | 1481-1511 | 35 | 2 | 2,19–2,13 | 7 | 41,52–40,29 |
| 7.8 | Malmö | 1481-1511 | 29 | 3 | 2,52–2,34 | 6 | 37,06–36,65 |
| 7.9 | Köpenhamn | 1481-1511 | 32 | 2 | 2,65–2,19 | 6 | 37,32–32,25 |
| 7.10 | Ålborg | 1481-1511 | 35 | 1 | 2,56 | 6 | 37,17 |
| 7.11 | Malmö | **1512** | 29 | 3 | 3,13–2,22 | 7 | 41,63–37,72 |
| 7.12 | Malmö | **1512** | 29 | 3 | 2,66–2,45 | 6 | 35,90–33,28 |

Text s. 9: 28 pieces, 6 dated 1512, 22 undated — the table agrees (22 + 6). The 3,13 g piece is dated 1512 and
carries 41,63 % (text s. 9).

### Tab. 8 — Hans, Søsling («½ skilling»), «1481-1513» — specimens
Malmö «G 33» 1,31 g 29,40 % · Malmö «G 33» 1,47 g 28,87 % (5 lod). See §3 (G 33 → G 30).

### Tab. 9 — Hans, Hvid, «1481-1513»

| # | Mint | G | n | Weight | Lod | Ag % |
|---|---|---|---:|---|---:|---|
| 9.1 | Malmö | 31 | 1 | 0,84 | 6 | 31,90 |
| 9.2 | Köpenhamn | 34 | 1 | 0,82 | 6 | 34,40 |
| 9.3 | Ålborg | 36 | 1 | 0,90 | 6 | 33,82 |
| 9.4 | Malmö | 31 | 5 | 0,87–0,54 | 5 | 28,04–26,21 |
| 9.5 | Köpenhamn | 34 | 1 | 0,74 | 5 | 27,87 |
| 9.6 | Ålborg | 36 | 7 | 0,92–0,68 | 5 | 29,74–26,41 |
| 9.7 | Malmö | 31 | 3 | 0,85–0,75 | 4 | 24,79–23,90 |
| 9.8 | Köpenhamn | 34 | 1 | 0,74 | 4 | 22,94 |
| 9.9 | Ålborg | 36 | 2 | 0,77–0,68 | 4 | 24,68–23,25 |
| 9.10 | Ålborg | 36 | 1 | 1,07 | 1 | 3,10 (s. 4: low-silver pieces «*kan vara eller är samtida förfalskningar*») |

### Tab. 10, 11 — Christian II, Sølvgylden, Malmö, G 38 — specimens
1518: 29,26 g 93,30 % (15 lod) · 1523: 28,27 g 80,17 % (13 lod). Tab. 11 «Kvartsgyllen» 1516, «G 38»:
7,87 g 84,40 % (14 lod).

### Tab. 12 — Christian II, Skilling, Malmö — all specimens (caption: «*redovisas resultaten för varje enskilt
mynt*»)
G 39 1514: 2,05/55,76 · 2,25/49,72 · 2,15/39,71.
G 39 1515: 1,11/84,29 · 1,94/78,54 · 1,67/73,73 · 1,46/64,81 · 1,47/61,66 · 2,16/58,19 · 2,10/51,96 · 2,08/47,75.
G 41 1517: 2,21/39,94 · 2,35/36,88 · 2,40/35,59 · 2,45/35,30 · 2,33/34,12 · 2,34/31,94.
G 39 «1518-1523» (undated): 2,00/32,94 · 2,00/32,58 · 2,12/26,37.
Text s. 11: 20 pieces, 3 undated, 3 of 1514, 8 of 1515, 6 of 1517 — agrees.

### Tab. 14 — Christian II, Skilling with Klipping dies, Malmö, «1518-1522»
Specimens: 42a 1,86/34,17 · 42a 1,98/28,13 · 42b 2,23/18,15 · 42a 1,29/13,53 · 42a 1,83/11,04.
Groups: 42b n=2 2,07–1,88 / 12,05–10,97 (2 lod) · 42b n=5 2,58–1,96 / 6,23–3,95 (1 lod).
Tab. 13 counts 42a 4, 42b 8 — agrees. ⚠ s. 14: «*alla klippingar med lejon utan tunga [har] förts till typ 42b.
Dock har även mynt av typ 42d lejon utan tunga*» — the 42b attribution is Eriksson's simplification.

### Tab. 15 — Christian II, Hvid, Malmö, 1513, G 43 — specimens
0,87 g 30,37 % · 0,61 g 23,03 %.

---

## 2. Match to our finals (scan of `data/v2/final/*.yml` by `catalog.galster`; members via `lib/v2_index`)

| Eriksson | Our final | Fuss / phase | What our final has now |
|---|---|---|---|
| G 22 Rigsråd Hvid (tab. 6) | `unified-dk-galster-rigsraad-22` | `luebischer_muenzfuss` I | no weight, no fineness |
| G 23 Christian I Hvid (tab. 5) | `unified-dk-numista-143575` (30 members) + six separate KMM finals (`kmk-136087`, `-303911`, `-303912`, `-303913`, `-326668` 23C, `-643059` «falsk») | `seed_unsorted` | 1 weight, no fineness; no 23a–d split in the main class |
| G 29 Hans Skilling Malmø (tab. 7) | `unified-dk-bruun-3837` | `luebischer_muenzfuss` I | 3 weights, no fineness |
| G 32 Kbh Skilling | `unified-dk-galster-hg-32` | idem | nothing measured |
| G 35 Aalborg Skilling | `unified-dk-galster-hg-35` | idem | nothing measured |
| «G 33» Malmö Søsling (tab. 8) → **G 30** | `unified-dk-galster-hg-30` | idem | Galster caption 1,43 g |
| G 31 Malmø Hvid (tab. 9) | `unified-dk-numista-108399` | idem | 4 weights |
| G 34 Kbh Hvid | `unified-dk-galster-hg-34` | idem | nothing measured |
| G 36 Aalborg Hvid | `unified-dk-numista-152921` | idem | 5 weights |
| G 38 Sølvgylden (tab. 10) | **two** finals: `unified-dk-galster-c2g-38` and `unified-dk-bruun-3931` | `8_5_gylden_fod` A1 | Galster 27,06 g / 0,875; Bruun 28,74–29,49 g |
| «G 38» ¼ Sølvgylden 1516 (tab. 11) | **none** | — | — |
| G 39 Chr II Skilling 1514–15 (tab. 12) | `unified-dk-bruun-3917` (+ KMM `kmk-354175`, `-684506`, `-700881` «Christiania», all `seed_unsorted`) | `seed_unsorted` | weights; fineness 0,375 (Galster, Numista) |
| G 41 Chr II Skilling 1517 | `unified-dk-bruun-3929` | `seed_unsorted` | 2,36 g; 0,375 (Galster) |
| G 42a/b Klipping (tab. 14) | `unified-kmk-132460` (G 42, 42A), `unified-dk-numista-297656` (G 42), ~12 KMM fragments | `seed_unsorted` | no 42b anywhere |
| G 43 Chr II Hvid 1513 (tab. 15) | `unified-dk-galster-c2g-43` | `seed_unsorted` | 1,04 g / 0,246 (Galster) |

**Matched:** every Galster type Eriksson assays has a final, except the ¼ Sølvgylden. **Unmatched:** tab. 11.
**Conflicting:** §3 and §4.

No final for these types carries a measured fineness today except the Galster/Numista figures on G 38, 39, 41,
43 (those are standard values: 0,875 / 0,375 — Galster's page specs, not assays). The Rigsråd and Hans rows
(`luebischer_muenzfuss`) carry **no fineness at all**: Eriksson would be the first assay source for the card.

---

## 3. Mint column vs Galster number vs tab. 1 / tab. 2 (the §0.5 check, all rows)

Eriksson's tab. 1 («*Myntorter och valörer … (Galster 1972, 51ff)*») is the reference list: 22 Rigsråd Hvid
Malmö; 23a–d Christian I Hvid Malmö; Hans 29 Skilling / 30 Søsling / 31 Hvid Malmö, 32 / 33 / 34 København,
35 Skilling / 36 Hvid Ålborg; Christian II 37 Nobel, 38 Sølvgylden, 39–41 Skilling, 42a–d Klipping, 43 Hvid,
all Malmö. It agrees with danskmoent's Galster pages (`scripts/cache/danskmoent/galster/fr_hg29…36`,
`chr_c2g38/41/43`, `c2g39`). Tab. 2 (Hans, «o = in the material»): Skilling Malmö o, Kbh o, Ålborg X;
Søsling Malmö o, Kbh X; Hvid o / o / o. Tab. 3 (Christian II): Sølvgylden, Kvartsgyllen, Skilling, Klipping,
Hvid o; Nobel X.

| Row | Mint × G vs tab. 1 | vs tab. 2/3 | Verdict |
|---|---|---|---|
| tab. 5, 6 | Malmö × 23 / 22 ✓ | — | consistent |
| tab. 7 | 29 Malmö, 32 Kbh ✓; **35 Ålborg ✓ but tab. 2 marks Ålborg Skilling «X» (not in material)** | ✗ | ⚠ new: tab. 7 has 3 Ålborg G 35 pieces (7.7, 7.10). Either tab. 2's «X» for Ålborg Skilling is the slip, or the mint column. Two internal witnesses (mint column + G 35, which agree with each other and with tab. 1) against one cell of tab. 2 → reading (H): tab. 2's Ålborg Skilling cell is the error. Not settled. **Consequence for §0.5:** tab. 2 has at least one wrong cell, so it is a weaker witness than §0.5 assumed when it resolved tab. 8 «G 33» as G 30 by tab. 2. That resolution still has the mint column «Malmö» for it, but it is now one internal witness of the same table set against another, not two against one. |
| tab. 8 | Malmö × **33** ✗ (33 = Kbh) | Søsling Malmö o, Kbh X | known (§0.5): G 33 is the slip, read **G 30** |
| tab. 9 | 31/34/36 × Malmö/Kbh/Ålborg ✓ | o/o/o ✓ | consistent |
| tab. 10 | 38 Malmö ✓ | o ✓ | consistent |
| tab. 11 | **38** for a ¼ Sølvgylden — tab. 1 has no separate number for fractions; danskmoent's G 38 page is «*1 Sølvgylden … 1516 (RRR), 1518 (RR), 1523*» only | Kvartsgyllen o | ⚠ open: either Galster 1972 subsumes the ¼ under 38 (danskmoent's page does not show it) or Eriksson borrowed the whole-piece number. Galster 1972 itself (paper) would settle it. |
| tab. 12 | 39 / 41 Malmö ✓ | o ✓ | years: 39 = 1514–15 ✓, 41 = 1517 ✓ (danskmoent G 41: 1516, 1517). ⚠ dating column of the 3 undated G 39 says «1518-1523», while the text says «*utan år (1517/1518?)*» and «*en datering 1515/1516*» (s. 12–13) — internal inconsistency; do not import the column as a year. |
| tab. 14 | 42a/42b Malmö ✓ | o ✓ | type split is Eriksson's simplification (42b includes possible 42d) |
| tab. 15 | 43 Malmö 1513 ✓ | o ✓ | consistent |

**Other internal inconsistencies of the source (for the reader of these numbers):**
- Coin count: s. 1 «*118 mynt*», English summary s. 16 «*156 coins*», the tables sum to **115**.
- Tab. 9 text s. 10: «*3 ex. håller 6 lod, 18 ex. håller 5 lod och 3 ex. håller 4 lod*» (24); the table gives
  6 lod 3, 5 lod 13, 4 lod 6, 1 lod 1 (23).
- Editorial rule s. 18: «*Om antalet mynt är färre än fem så redovisas resultaten för varje enskilt mynt*» —
  tabs. 5, 7, 9, 14 nevertheless group 2–4 pieces. The appendix (s. 18: «*I appendixet redovisas
  analysresultatet för varje enskilt … liksom foton*») is **not in this 20-page PDF**.
- 7.5 (H): its lower Ag 36,65 and upper Cu 59,31 are identical to row 7.8's; 36,65 % falls in the 6-lod bin by
  the editor's own definition, not 7 lod. Possibly a copy slip in 7.5 (and 7.7 shares 41,52 / 53,74 with 7.5).
  Not verifiable without the appendix.
- 7.1: one weight «2,47» for n = 2 — either both weigh 2,47 g or one figure stands for the pair; cannot tell.
- 12 (1515, 1,11 g) Cu 7,83 = tab. 11 Cu 7,83 — noted only; Cu is uncalibrated anyway.

---

## 4. Problems in OUR data surfaced by the match (rows added to `FUSS_REVIEW_FINDINGS.md`)

`trace_coin why` run on each; none shows a curator decision on the values below.

1. **G 23 Christian I Hvid class (`unified-dk-numista-143575`) renders 1481–1483 and Schou 13** — the Rigsråd
   Hvid's dating and the Schou number our G 22 final carries. Numista 143575 (cache) says 1448–1481, no Schou;
   Eriksson dates 1448–1481. The year comes from ONE KMM member (authority «Christian 1», «G 23», creation
   1481–1483); Schou 13 from one KMM member («Schou 13; G. 23a»). Members otherwise all G 23 / 23a–d.
   (The class is `seed_unsorted`, pre-1514; no render impact on a Fuß card today.)
2. **Two finals for G 38 Sølvgylden** — `unified-dk-galster-c2g-38` (Galster) and `unified-dk-bruun-3931`
   (Bruun 3931/3933/3934 + Numista 108782), same fuss/phase, same Galster number; no merge or no-merge decision
   found. Merge candidate (needs `merge-candidate-table`). Side note, not checked: the Numista reading 23,68 g on
   3931 equals danskmoent's printed «*Finvægt: 23,68g*».
3. **G 41 Skilling final shows 1514–1517**; Galster (danskmoent) and Eriksson give 1516–1517 / 1517. Bruun 3929
   seed says 1517; the 1514 comes from the other member (`kmk-354202`) — not opened.
4. **`kmk-155167` Christian I Hvid with KMM typeNumber «G. 33»** (Galster 33 = Hans, København Søsling) —
   source-faithful KMM value, `seed_unsorted`; flagged only.

---

## 5. What each row could add

- **Fineness readings** — the main gain. Specimen rows give a paired (weight, Ag) per piece: 45 pieces on 14
  Galster numbers (G 42a/b and the ¼ Sølvgylden counted separately). Group rows give a band (lod) and an Ag range for n pieces, not n readings.
- **Weights** — specimen rows: real readings. Group rows: an envelope over n weighed pieces.
- **Dating** — only tab. 7 (6 Skillinger dated 1512 → G 29 already 1512), tab. 10/12/15 (per-year: G 38 1518,
  1523; G 39 1514, 1515; G 41 1517; G 43 1513) — all already in our year ranges. Tab. 11 adds a 1516 ¼ piece
  that has no row. No year change follows from Eriksson. The lod groups are the dating *evidence* used in
  `luebischer_muenzfuss.md` §0.5–§0.6, which is dossier/card prose, not coin-row data.

**How it would sit under the rules.**
- §4: Eriksson publishes the values directly → `fineness_verified: true` is permitted. The source label must say
  the method: «Eriksson 2017, tab. N (XRF, surface)» — Eriksson's own caveats (surface enrichment, ±0,8 %, Ag only
  calibrated) belong in that label/tooltip, not in a downgrade to `false`.
- §9a: each specimen = one `weight_rough_g` + one `fineness` entry, one `sources` entry. **Thinning does not
  apply**: the only ≥5 buckets (G 39 14 pieces, G 41 6, G 36 Hvid 11) have non-uniform fineness (condition 3
  fails) — keep all.
- **Group rows are the problem.** A min–max over n pieces is not n specimens, and weight-min and Ag-min are not
  the same coin. Options:
  - (a) `weight_range_g` {min, max, source} — the field the Galster-caption session added. ✗ Semantics: it is «a
    catalogue's figure for a TYPE» and the build expands it into lower/upper readings that go through
    Feingewicht and Δ. Paired with a fineness from the same row, the build would compute the Feingewicht of two
    coins that do not exist (lightest × poorest, heaviest × richest). There is no `fineness_range` field.
  - (b) a new structured field, e.g. `assay_groups: [{source, table, n, lod, weight_min, weight_max, ag_min,
    ag_max}]`, carried through merge/absorb by union, rendered as a tooltip/sub-row and **not** fed into
    Feingewicht. Clean, but a schema change (merger `_collect_*`, absorb, render, tests).
  - (c) seed specimen rows only; leave group rows in the dossiers (as now). Loses 70 of 115 pieces from the coin
    rows, loses nothing from the research.
  - (d) first look for the appendix (per-coin values + photos, s. 18): if it exists (the series' site,
    `www.archaeology.su.se/numismatiska`), every group row becomes specimens and the problem disappears.
- **Specimen-only does NOT cover what the groups give (curator question 2026-10-21).** Eriksson bins per mint
  per lod, so an n = 1 row is a rare bin: the extremes and the suspected forgeries. Per type (spec / in groups):
  G 22 3/0 · G 23 2/20 (the two are 22,40 % and the 13,25 % suspected forgery) · **G 29 0/18** · G 32 1/6 (the
  9-lod piece) · G 35 1/2 · G 30 2/0 · G 31 1/8 (the 6-lod piece) · G 34 3/0 · G 36 2/9 (one 6-lod, one 3,10 %
  forgery) · G 38 2+1/0 · G 39 14/0 · G 41 6/0 · G 42 5/7 (all 1–2-lod pieces are in groups) · G 43 2/0.
  Hans alone: 10 of 53 pieces, none for the main Malmø Skilling G 29 (incl. all six dated 1512). Specimen-only
  would be a sample skewed to high fineness and forgeries — not a more precise subset.
- **What a group row really contains.** Its min and max are each a real reading of a real coin; only the pairing
  and the interior n − 2 values are lost. n = 2 rows (13 rows, 26 coins) therefore give EVERY value, unpaired;
  n ≥ 3 rows (11 rows, 44 coins) give the two extremes. So the bounds can enter as ordinary readings — two
  weights and two finenesses per row — with no new field, provided the labels never pair a weight bound with a
  fineness bound: `compute._compute_coin` pairs a weight with the fineness whose source label shares a token
  (`_fineness_for`), else with the highest-authority fineness. Weight labels and fineness labels of a group row
  must share no token; n and the lod bin go into the label («Eriksson 2017, tab. 7, 8 lod, 3 St., leichtestes»).
  Not yet checked: how such a weight reading renders its Feingewicht/Δ (it borrows another source's fineness).
  What a new `assay_groups` field would add beyond that: n and the bin as structured data, nothing else.
- **Only the appendix gives everything exactly** (interior values + pairing); with it the group question
  disappears.
- A type row spans several lod groups (G 29: 9 → 6 lod). Readings 32–53 % on one Hans Skilling row against one
  card Soll will show large Δ — the real state of the coinage, but readable only after the period split of the
  card (TODO ED).

---

## 6. Path and effort

Curator-entered readings are not an option: coin fields are never hand-typed (CLAUDE.md, V2 pipeline). So it is
a small source:

1. **HARVEST** — done (PDF + extract in cache). Optional: the appendix (§5 (d)).
2. **SYNTHESIS** — `scripts/parse_eriksson_2017.py`: the table lines are clean single lines in the `-layout`
   extract; parse with explicit per-table line windows into `…/eriksson_2017_assays.json` (one record per row:
   table, row, mint, denomination, dating, galster, n, w_min, w_max, lod, ag_min, ag_max). Self-check: 37 rows,
   115 coins, per-table counts as in §1. ~1 h.
3. **SEED** — `scripts/maintenance/build_eriksson_seed.py` via `lib/v2_seed_writer.write_v2_seed` →
   `data/v2/seed/eriksson/danish_realm.yml`, one entry per Galster type (readings as lists). Merge key: the
   merger's existing Galster scope — `catalog.galster` + `galster_volume` (`hg` for Hans; `c2g` Christian II;
   ruler-derived otherwise — the Rigsråd (G 22, no volume on our final) and Christian I (G 23) scopes must be
   checked against `merge_seeds_cross_source.py` ~l. 941–990 before seeding) + ruler + mint + metal + nominal.
   ~2 h incl. a `_authority_score` entry for the new source.
4. **Curator decisions needed before the seed:** (i) G 33 → G 30 on tab. 8 is an index override = `_source_errata`
   (CLAUDE.md §4: in-chat «так» required); (ii) tab. 11 ¼ Sølvgylden «G 38» must not merge into the whole
   Sølvgylden (exclusion, `no_merges`, or wait for Galster 1972); (iii) group-row representation (§5 a–d);
   (iv) seed Christian I rows (pre-1514, `seed_unsorted`) or not; (v) tab. 7 Ålborg vs tab. 2 «X» (§3) — keep
   as printed.
5. **Re-flow + verify** — merge + absorb from HEAD, `verify_reflow.py`, `trace_coin snapshot/diff`. ~1 h.

**Estimate:** specimen-only seed (c) ≈ half a day; with a new `assay_groups` field (b) ≈ one day.
**Assessment:** worth connecting, modestly — it is the only assay source for the Rigsråd / Hans types (the
`luebischer_muenzfuss` card has no measured fineness at all), and 45 genuine paired specimens. Best order:
look for the appendix first (d); seed after the card's period split, so the Δ against the per-period Soll is
meaningful.

---

## 7. The appendix — found 2026-10-21; it supersedes §5's group problem

**Source.** «Metallanalyser av mynt 2017:1_APPENDIX», listed on
`https://www.su.se/enheter/numismatiska-forskningsgruppen/om-forskningsgruppen/metallanalyser-av-mynt`
(the old `archaeology.su.se` / `polopoly_fs` links are dead, 404). Cache:
`scripts/cache/danskmoent/hans_1481_1513/eriksson_2017_metallanalyser_appendix.{pdf,extract.txt}`. 14 pp.:
pp. 1–11 photos (obverse + reverse of every coin, numbered, with a scale), pp. 11–14 one table, nos **1–118**:
Nr, MH (ruler), Myntort, Valör, År, Galster, Vikt, Lod, Silver, Koppar, Zink, Tenn, Antimon, Guld, Bly.
Abbreviations: «ks kantskada»; «f» after a weight (nos 4, 60) is not explained in the list (the article's
rule s. 18 puts fragment weights in parentheses — «f» is probably that, not verified).

**What it settles.**
- **Every coin is paired** (weight + Ag + lod per piece): the group-row question of §5 disappears. A seed can
  take 118 specimen readings, no new field.
- **Count:** 118 = the article's s. 1 figure; the article's tables hold 115. Missing from the tables:
  no. 23 (Christian I Hvid, 3,09 % — the near-copper forgery of the text, s. 7), one Malmö 5-lod Hans Hvid
  (appendix 6 pieces: nos 65, 66, 69–71, 73; tab. 9 n = 5) and one Ålborg 4-lod Hans Hvid (nos 74, 76, 79;
  tab. 9 n = 2). The tab. 9 text (3/18/3) matches neither the table nor the appendix (3/14/7 + one 1-lod).
- **Lod is consistent in the appendix** with the rule of s. 18 (checked for all 118: 0 mismatches). The four
  mismatches in the article's tables (tab. 5 37,44 under 7 lod; tab. 7 row 7.5 down to 36,65; tab. 12 78,54
  under 12 and 64,81 under 10) are slips of the article tables: the appendix has 37,44 → 6 (no. 9),
  78,54 → 13 (no. 89), 64,81 → 11 (no. 91).
- **Tab. 7 row 7.5 was a copy slip (H of §3 confirmed):** the four Malmö 7-lod Skillinger are nos 35, 36, 39,
  41 with Ag 43,75 / 43,25 / 40,48 / 40,25, not «41,52–36,65».
- **Tab. 7 row 7.1 «2,47» for n = 2:** nos 28 and 29 both weigh 2,47 g.
- **Tab. 11 ¼ gyllen:** no. 84 «1/4 gyllen», Galster 38, 1516 — the appendix repeats G 38; still open.

**What it does NOT settle — a larger mint ↔ Galster conflict.** In the appendix the Myntort and Galster
columns disagree for **12 coins** (against tab. 1 / danskmoent: 29–31 Malmø, 32–34 København, 35–36 Ålborg):
- Skilling «Malmö» + **G 32** (= København): nos 28, 30, 32, 35, 36, 41, 45, 46, 47 (9 coins);
- Skilling 1512 «Malmö» + **G 35** (= Ålborg): no. 49 (the 3,13 g piece);
- ½ skilling «Malmö» + **G 33** (= København): nos 55, 56 (the §0.5 case — the appendix repeats it).
The article's tab. 7 counted all ten Skillinger under «Malmö 29», i.e. it followed the mint column. So the
mint column is not a reliable witness either, and the G 30 reading of §0.5 is now **unsettled**: the
appendix carries the same pair «Malmö / 33». **The photos decide** (mint name in the reverse legend:
MALMOGIENSIS / HAFNENSIS / ALBORGENSIS); at the PDF's resolution (embedded JPEGs 337 px wide) I could not read
them reliably — a curator reading of nos 28–56 is needed. Also: the Christian I sub-letters per coin (23a–d)
do not match the article's tab. 5 title grouping (e.g. no. 6, 38,74 %, is «23a» in the appendix, «DEI G'R'D'»
= 23d in tab. 5).

**Lod as a value (curator question 2026-10-21: why not take the Lod instead of the Ag range?).** Lod N is the
**upper bound** of a bin «(N−1)·6,25 % < Ag ≤ N·6,25 %» (s. 18: «*8 lod = 50,00-43,26%*» — the printed lower
bound 43,26 does not match the rule's 43,76; a slip in the example). Storing «8 lod» = 0,500 would overstate
every coin in the bin by up to 6,25 points (the three Malmö 8-lod Skillinger are 48,29 / 46,25 / 45,68 %).
The lod is Eriksson's reading of which whole-lod standard a coin was struck to («*antas att myntordningarna
angett vikten i steg om ett lod … även om det i realiteten ofta inte var fallet*»); it belongs in dossier
prose as an interpretation, not in `fineness` as a reading. With the appendix the measured Ag is available
for every coin, so the question is moot.

---

## 8. The rest of the series — what is useful to us (checked 2026-10-21)

Series page: `https://www.su.se/enheter/numismatiska-forskningsgruppen/om-forskningsgruppen/metallanalyser-av-mynt`
(«Filer för utskrift»). Every issue has a per-coin appendix with photos in the same layout as 2017:1.

| Issue | Author, subject | Our rows | Verdict |
|---|---|---|---|
| 2016:1 (+ appendix, 145 coins) | Mikael Heljeback, Danish coins c. 1400–1448: Erik of Pomerania (65), Christopher of Bavaria (77), Rigsrådet 1448 (1 Skilling, G 21, 2,08 g, 45,99 %) | **none** — no final carries Erik / Christopher / Rigsråd 1448 | context only: the pre-1481 silver of the Danish Hvid / Skilling (the `luebischer_muenzfuss` prehistory). Cached. |
| 2017:2 | Sarah Eriksson, Swedish örtugar of Erik of Pomerania 1396–1439 | none (Sweden, pre-scope) | no rows of ours; cached with its appendix on the curator's request (2026-10-21) |
| **2017:3 (+ appendix, 169 coins)** | **Robin Lindblad, Gotland coins c. 1150–1554** | **yes — Visby** | **useful.** Cached. |
| 2018:1 | Eeva Jonsson, Viking-Age coins | none | not useful; not cached |

**2017:3 in detail.** Nos 88–169 (82 coins, all paired weight + Ag + lod) are the Danish-period Visby coins
1450–1554; nos 1–87 are earlier Gotland Penninger / Gotar (out of scope). Catalogue key «LL» = Lagerqvist 1970,
numbered per section (Norby's LL 2 ≠ the Visby Hvid LL 2). Our Visby rows (all in `danish_realm` except Norby):

| Lindblad (LL, dating, n) | Our final | Link |
|---|---|---|
| Hvid 1450, LL 1, 3 | `unified-kmk-352426` (KMM «Gal. 139», Christian I, `seed_unsorted`); no Galster-source final for G 139 | danskmoent G 139 cites «Lagerqvist 1» — explicit, but danskmoent calls the type «Gote», Lindblad «Hvid» (to check) |
| Hvid 1455–1480, LL 2 / 3b / 4a–d, 27 | ? | no concordance |
| Hvid 1480–1500, LL 5, 6 | `kmk-139328` («G. 140») — danskmoent G 140 cites «Lagerqvist 5» | danskmoent, explicit; G 140 is Christian I per Galster, Schou → Christian II, Lindblad 1480–1500 — three datings |
| Hvid 1500–1520, LL 7 / 7a / 7b, 12 | `unified-dk-galster-hg-142` (Hans, `luebischer_muenzfuss`) — danskmoent G 142 cites «Lagerqvist 7b» | explicit for 7b only |
| Skilling Norby 1524 LL 2 (4), 1525 LL 3 (2) | `unified-dk-bruun-4112` (G 143, 1524–1525, `norby_gotland`) | by type + year (H) |
| Skilling Norby u.å. LL 1 / 1a / 1b, 5 | `unified-dk-bruun-4125` (G 144) | by type (H) |
| Hvid Norby u.å. LL 4a / 4b, 9 | `unified-dk-galster-hg-145` (G 145) | by type (H) |
| Hvid ca 1530, LL 5a, 2 | `unified-dk-galster-hg-146` / `kmk-575499` (G 146, Frederik I) | by type + date (H) |
| Skilling 1535 LL 6a (2), 1536 LL 7 (2), 1537 LL 8 (1) | `unified-dk-galster-hg-147` (G 147, 1535–1537) | by type + years (H) |
| Skilling 1554 LL 9 (3), ½ Skilling 1554 LL 10 (3), Hvid (1554) LL 11 (4) | KMM finals `kmk-150112` (1 Skilling 1554), `kmk-150110` / `-150111` (½ Skilling 1554); Hvid: ? | by type + year (H) |
| — | `unified-dk-galster-hg-141` (Hans Visby Hvid G 141, no LL on danskmoent) | unmapped |

So 2017:3 is the **only assay source for the Visby series** (Hans G 141/142 sit under `luebischer_muenzfuss`;
Norby, Frederik I and Christian III Visby coins are all `seed_unsorted`). Before a seed it needs an LL ↔ Galster
concordance: three links are explicit on danskmoent (LL 1 = G 139, LL 5 = G 140, LL 7b = G 142), the rest are by
type and year (H); Lagerqvist 1970 itself (paper) would settle them. A seed for 2017:1 and 2017:3 could share one
builder (same table layout, different catalogue key).

### 7a. Photo check of the 12 conflicting coins (2026-10-21)

The appendix photos of nos 28, 30, 32, 35, 36, 41, 45, 46, 47, 49, 55, 56 were set beside danskmoent reference
specimens (Bonde and Zinck collections on `fr/hg29.htm`, `hg30`, `hg32`, `hg33`, `hg35`). Where the mint stands:
Märcher 2018 s. 404 gives «*MONETA MALMOI, MONETA MALMOIENS*» on the reverse of Christopher's Malmø coins, and
s. 488 «*MONETA HAFNIENS for København*» as the late-medieval practice; on the G 32 reference the reverse legend
reads «MONETA NOVA …NENSIS» (my reading, H). No source specific to Hans' legends is in the cache.

- **Curator's reading (Serhii, 2026-10-21), tentative:** the legends of the conflicting pieces «*наче й схоже на
  malmoensis*» — they look like MALMOENSIS, but the curator says this is hard to tell and may only seem so.
  This is the only reading of the photos; at the appendix's resolution it cannot be made firm.
- **Søslinger nos 55, 56 — a second, independent sign (my visual comparison, H):** the danskmoent references show
  a **quartered** shield on the lion side for G 30 (Malmø) and a **plain** three-lion shield for G 33
  (København); nos 55b and 56b show the quartered shield → type G 30.
- **Working reading:** the Myntort column («Malmö») is right and the Galster column is the slip for these
  12 coins (G 32 / G 35 / G 33 written for Malmø pieces) — two weak witnesses (a tentative legend reading and,
  for the Søslinger, the shield type) for the mint column, none for the Galster numbers. Not settled: better
  photos (KMK Stockholm) or the objects would settle it. For a seed this means: attach these 12 by mint (Malmø
  → G 29 Skilling / G 30 Søsling), and record the printed Galster numbers as the source's values with the
  curator's reading as the reason — an index override, so a `_source_errata` per coin needs the curator's
  explicit «так» (CLAUDE.md §4).
