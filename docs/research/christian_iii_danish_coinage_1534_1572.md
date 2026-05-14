# Christian III and early Frederik II Danish coinage 1534–1572

> **Research note — data dump for future sessions.** Captures the
> numismatic / monetary-history evidence gathered 2026-05-14 on
> Christian III's reign (1534–1559), the 1541 Møntordning that
> founded the modern Danish coinage system, and early Frederik II's
> reign (1559–1572) up to the symbolic 1572 «Elfsborgs løsen»
> Speciedaler cutover.
>
> **No project-classification recommendations** — this document is
> purely the historical-numismatic substrate. Conclusions about Fuß
> categories, scope anchors, seed promotion, or naming conventions
> are deliberately omitted; they belong to future TODO entries when
> the question is reopened.
>
> **Companion**: `docs/research/danish_royal_gold_1560_1648.md`
> covers Danish royal gold 1560–1648 (overlaps for 1560–1572 gold
> data; this doc adds silver + Christian III pre-1559 context).

---

## 1. The 1541 Møntordning (Christian III)

Christian III's Møntordning of **20 September 1541** is the
foundational Danish monetary law of the post-Reformation period.
Per Galster (danskmoent.dk/galster/galshist.htm):

> «1541 — Christian III's coin ordonnance of 20 September 1541
> rightly begins the modern period in Denmark. Christian III
> brought order to the monetary system, and the daler was now
> placed at the head of the coin system. Although he had already
> minted Joachimstaler in 1537, it was through the coin ordonnances
> of 1541 and 1544 that the new coinage system was implemented.
> This achieved unity both with the duchies, where efforts had
> continuously been made to maintain parity with the Lübeck coin,
> and with all of Germany, where the daler had completely
> triumphed.»

Source URL: <https://www.danskmoent.dk/galster/galshist.htm>

**Key features of the 1541 framework:**

- **Daler placed at head of system** (replacing the older gulde-based
  accounting).
- **Sub-coin structure**: 1 Daler = 3 Mark Danske = 48 Skilling.
  (NOT the later 1602 «1 Daler = 4 Mark = 66 Skilling» convention.)
- Parity with Schleswig-Holstein duchies (Lübeck coin) maintained.
- Alignment with broader German daler tradition («daler had
  completely triumphed»).

**1544 supplement**: Hede explicitly recognises a metric break
between 1541 and 1544+ issues, via sub-letter split Hede 3A (1541)
vs Hede 3B (1544–1555) — see §4 below for per-coin Marken-fin
parameters. The 1544 supplement debased the silver Daler by about
7 % relative to the 1541 base.

**Pre-Møntordning context**: Christian III had already minted
Joachimstaler in 1537 (per Galster). The 1541 ordonnance codified
the daler-system that the 1537 Joachimstaler had introduced as a
single-issue precedent.

---

## 2. Pre-1541 Danish coinage tradition

The 1541 Møntordning ended a period of monetary instability that
ran through the Reformation (1536) and the Count's Feud (Grevens
fejde, 1534–1536). Pre-1541 Danish coinage falls into two main
strands, both visible in our Hede cache via the `c3hede` oversigt
page:

### 2.1 First Danish Daler 1518 (Christian II)

Per Galster:

> «De første dalere blev udmøntet i 1518 af bjergsølv til erstatning
> for guldgylden.»

The first daler was minted in 1518 under Christian II from mine
silver («bjergsølv»), as a replacement for the older gold gulde
(«guldgylden»). Pre-Reformation, pre-Joachimstaler. NOT in our
Hede cache (no c2h pages indexed).

### 2.2 Count's Feud Klippinger 1534–1536 (Christian III, pre-Møntordning)

The Hede `c3hede` overview lists war-finance Klipping coins from
the Grevens fejde civil war, minted at Århus and Roskilde. Examples:

| Galster ref | Hede equivalent | Sieg | Nominal | Material | Year | Mint |
|---|---|---|---|---|---|---|
| 92A/92B | — (Klipping) | 3-4 | 2 Mark | Sølv | 1535 | Århus |
| 93 | — | 2 | 8 Skilling | Sølv | 1535 | Århus |
| 94 | — | 1 | 4 Skilling | Sølv | 1535 | Århus |
| 95 | — | 16.1-2 | 4 Skilling | Sølv | 1535 | Århus |
| 96 | — | 15 | 2 Skilling | Sølv | 1536 | Århus |
| 97 | — | 14 | 2 Mark | Sølv | 1535 | Roskilde |
| 98 | — | 13 | 1 Mark | Sølv | 1535 | Roskilde |
| 99 | — | 12 | 4 Skilling | Sølv | 1535 | Roskilde |
| 100 | — | 11 | 2 Skilling | Sølv | 1536 | Roskilde |

All Klipping format (firkantet blanket), all war-finance issues
during the Grevens fejde. These predate the 1541 Møntordning and
operate outside its framework.

Source: danskmoent.dk Hede page `c3hede`
(<https://www.danskmoent.dk/chr/c3hede.htm>).

---

## 3. Christian III gold inventory 1545–1559

The Hede cache (`scripts/cache/hede/c3h*.json`) contains the
following Christian III gold issues. Mintmaster varies by location.

| Hede | Nominal | Year | Mint | Brutto | Finhed | Finvægt |
|---|---|---|---|---:|---:|---:|
| c3h1 | 1 Ungersk gylden | 1557 | København | 3.490 g | **0.986** | **3.442 g** |
| c3h2 | 2 Ungersk gylden | 1557 | København | 6.981 g | 0.986 | 6.884 g |
| c3h15 | 1 og 2 Rhinsk gylden | 1546 | Flensborg | 3.278 g (1×) / 6.556 g (2×) | **0.750** | **2.458 g (1×) / 4.916 g (2×)** |

**Per-coin standard analysis** (computed):

- **Ungersk Gylden** (c3h1, c3h2): canonical Reichsdukat / Hungarian
  Gulden standard. 1 piece = 3.442 g fein at 0.986 fineness =
  imperial Reichsdukat metric. 233.856 / 3.442 ≈ **67.94 Dukaten per
  Cölln. Marck fein** — close to the canonical 67 Dukaten convention
  for Reichsdukatenfuß.
- **Rhinsk Gylden** (c3h15): 1 piece = 2.458 g fein at 0.750
  fineness. 233.856 / 2.458 ≈ **95.14 Rhinsk Gylden per Cölln. Marck
  fein** — matches the standard 95-pieces-per-Marck Rhenish Gulden
  convention.

**Rarity** per Hede pages:
- c3h1 Ungersk Gylden 1557: RR
- c3h2 2 Ungersk Gylden 1557: RRR; the page notes «Sølvafslag Unik»
  (silver off-strike, unique specimen).
- c3h15: «det viste eksemplar er det unikke stykke med værdien 2
  Rhinsk gylden» — 2 Rhinsk Gylden survives as a unique specimen.

**Bibliographic citations** (paper, via Hede pages):
- Ramus side 147 (c3h1)
- NFM XIII side 284 (c3h1), NFM XIV side 145 (c3h2), NFM XII side 10
  (c3h15)
- Wilcke VII side 306 (c3h2)
- Galster: Flensborg Mønt, Sønderborg 1967, side 14-26 (c3h16)
- Grandjean side 184 (c3h1)

Mintmaster for c3h15 attribution: **Reynold Junge** (mark:
glødehagen — «glowing hook»), assigned to Flensborg. The «det viste
eksemplar» (the example shown) is the unique 2 Rhinsk Gylden in
Den Kgl. Mønt- og Medaillesamling, København.

---

## 4. Christian III silver inventory 1541–1559

Full silver inventory from Hede cache, organised by mint. Marken-fin
(«mf») column shows the *daler-per-Cölln.-Marck-fein* tariff
explicitly stated on Hede pages. Computed «g fein per Daler» column
= 233.856 / mf — the per-Daler silver content implied by the
Marken-fin tariff. **Note**: under the 1541 framework, 1 Daler = 3
Mark Danske, so 1 Mark Danske fein = (g fein per Daler) ÷ 3.

### 4.1 København mint (Christian III)

| Hede | Nominal | Year | Brutto | Finhed | Finvægt | mf (daler/Marck) | g fein per Daler |
|---|---|---|---:|---:|---:|---:|---:|
| c3h3 (3A) | 1 Mark | 1541 | 9.744 g | **0.906** | **8.830 g** | **8.827** | **26.494** |
| c3h3 (3B) | 1 Mark | 1544-1555 | 9.744 g | **0.843** | **8.221 g** | **9.481** | **24.665** |
| c3h4 | 8 Skilling | 1541-1544 | 4.872 g | 0.906 | 4.415 g | (matches 8.827) | 26.494 |
| c3h5 | 4 Skilling | 1541-1554 | 2.436 g | 0.906 | 2.208 g | (matches 8.827) | 26.494 |
| c3h7 | Hvid u.år | 1541-1544 | 0.735 g | 0.250 | (≈ 0.184 g) | **8.833** | 26.484 |
| c3h8 | Penning | 1546 | 0.305 g | 0.125 | 0.038 g | **10.666** | 21.93 |

**Hede 3A/3B sub-letter split** is the key — Hede explicitly recognises
1541 as a distinct monetary regime from 1544+. The 1541 standard
(mf 8.827) is HEAVIER than later 9-Fuß (mf 9.0 → 25.984 g per
Daler); the 1544 standard (mf 9.481) is LIGHTER (24.665 g per Daler,
~5 % debasement vs 9-Fuß).

**c3h7 Hvid** (1541-1544) at mf 8.833 confirms the 1541 standard
extended down to the smallest billon (penny-tier) denomination.
**c3h8 Penning 1546** (mf 10.666) is lighter still — smallest
denomination always debased proportionally more.

### 4.2 Flensborg mint (Christian III)

| Hede | Nominal | Year | Brutto | Finhed | Finvægt | mf (daler/Marck) | g fein per Daler |
|---|---|---|---:|---:|---:|---:|---:|
| c3h16 | 1 sølvgylden | 1545 | 29.232 g | **0.890** | **26.035 g** | **8.982** | **26.038** |
| c3h19 | 1 sølvgylden | 1547 | 29.232 g | 0.890 | 26.035 g | 8.982 | 26.038 |
| c3h20 | 1/2 sølvgylden | 1547 | 14.616 g | 0.890 | 13.017 g | 8.982 | 26.038 |
| c3h21 | 1 søsling lybsk | 1545 | 1.292 g | **0.406** | 0.524 g | **9.287** | **25.180** |
| c3h22 | 1 søsling lybsk | 1546-1554 | 1.292 g | 0.406 | 0.524 g | 9.287 | 25.180 |

**Flensborg sølvgylden** (1545-1547): own variant at mf 8.982 = 26.038
g per Daler. Slightly lighter than København 1541 (26.494) but
heavier than København 1544+ (24.665). Distinct Flensborg-mint
parameter.

**Flensborg søsling lybsk** (1545-1554): mf 9.287 = 25.180 g per
Daler. Closer to standard 9-Fuß (25.984) but still distinct.

Mintmasters for Flensborg sølvgylden series: **Jørgen Kock den
Yngre** (per Hede c3h16). Galster's Flensborg Mønt monograph
(Sønderborg 1967, pp. 14-26) is the primary literature.

### 4.3 Other Christian III silver / billon entries

These Hede pages exist in cache but lack metric specs (specs.default
empty or missing in cache JSON):

| Hede | Nominal | Year | Mint |
|---|---|---|---|
| c3h6 | 1 Skilling | 1542 | København |
| c3h9 | 2 Skilling | 1545 | København |
| c3h10 | 2 Skilling | 1541, 1544, 1546, 1554, 1555, 1557, 1558, 1559 | København |
| c3h11 | 1 Skilling | 1554 | København |
| c3h12 | 1 Søsling | 1554 | København |
| c3h13 | 1 Hvid u.år | (1554) | København |
| c3h23 | (Blaffert u. år) | 1514, 1791 | (unclear) |
| c3h24 | u.år | — | Flensborg |
| c3h25 | 1 Penning lybsk u.år | — | Flensborg |

For these the cache lacks Marken-fin; specs would require direct
re-extraction from danskmoent.dk pages or Hede paper original.

---

## 5. Frederik II early reign 1559–1572

Frederik II succeeded Christian III in 1559 and inherited the
Møntordning framework. His own monetary actions during 1559-1572
include: continued Christian III sub-coin pattern, gold issuance
1563-1564 (Bremerholm), Syvårskrigen Klipping series 1563-1570, and
the symbolic 1572 Speciedaler (Elfsborgs løsen).

### 5.1 Gold 1559–1572

Covered in `docs/research/danish_royal_gold_1560_1648.md` §1; brief
recap:

| Hede | Nominal | Year | Brutto | Finhed | Finvægt |
|---|---|---|---:|---:|---:|
| f2h1 | 1 Ungersk Gylden | 1563 | 3.490 g | 0.986 | 3.442 g |
| f2h2 | 1 Guldkrone | 1563 | 3.341 g | 0.934 | 3.120 g |
| f2h3 | 1 Rhinsk Gylden | 1563 | 3.248 g | 0.770 | 2.500 g |
| f2h4 | 1 Dukat | 1564 | 3.490 g | 0.986 | 3.442 g |
| f2h5 | 1 Guldkrone | 1564 | 3.341 g | 0.934 | 3.120 g |
| f2h6 | 1 Rhinsk Gylden | 1564 | 3.248 g | 0.770 | 2.500 g |
| f2h8 | 3 Mark (gold) | 1560, 1563 | 29.232 g | 0.906 | 26.491 g |

Mintmasters: **Hans Willers** (c. 4860 stk Guldkrone, per Hede
f2h2), Hans Köpelin, Laudris Hammer (per f2flens). Mint:
Bremerholm goldsmith workshop, København.

Continuity with Christian III gold:
- Ungersk Gylden 1563-1564: continues Christian III 1557 standard
  (same brutto, finhed, fein).
- Rhinsk Gylden 1563-1564: continues Christian III 1546 standard
  (fineness 0.770 vs 0.750 — slight upward adjustment).
- Guldkrone: appears as a new type in Frederik II's reign (no
  Christian III Guldkrone in our cache).
- 3 Mark gold f2h8: one-off, no Christian III predecessor.

### 5.2 Silver 1559–1563 (pre-Syvårskrigen)

Inherits Christian III sub-coin pattern; Hede entries:

| Hede | Nominal | Year | Mint | Brutto | Finhed | Finvægt | mf | g fein per Daler |
|---|---|---|---|---:|---:|---:|---:|---:|
| f2h9 | 1 Mark | 1544-1559 | København | (no specs) | — | — | — | — |
| f2h10 | 8 Skilling | 1544-1563 | København | 4.872 g | **0.649** | **3.163 g** | **12.321** | **18.98** |
| f2h11 | 2 Skilling | 1559-1563 | København | 2.338 g | **0.312** | **0.731 g** | **13.333** | **17.54** |
| f2h12 | 1 Skilling | 1562-1563 | København | 1.772 g | **0.187** | **0.332 g** | **14.667** | **15.94** |

**Progressive debasement** of København sub-coin denominations
through Frederik II's early reign: 8 Skilling at 18.98 g per Daler
→ 2 Skilling at 17.54 g → 1 Skilling at 15.94 g. Smaller
denominations debased proportionally more. All significantly below
the 1541-era 26.494 g standard — the Christian III 1541 base had
already been abandoned for small change.

### 5.3 Syvårskrigen Klipping 1563–1570

Per Nationalmuseet
(<https://natmus.dk/historisk-viden/temaer/militaerhistorie/danmarks-krige/syvaarskrigen/>):

> «During the Northern Seven Years' War (1563-70), Frederik II had
> clipper coins minted with denominations of 2 and 4 skilling as
> well as 1 and 2 mark. These clippings were deficient and/or
> underweight, meaning they contained too little silver in relation
> to their nominal value.»

> «The production and distribution of such deficient and/or
> underweight coins provided quick profit to the king's treasury,
> and the profits went especially to war financing in 1563, not
> least for payment of mercenary troops.»

Hede entries for war Klipping series:

| Hede | Nominal | Year | Mint | Brutto | Finhed | Finvægt | mf | g fein per Daler |
|---|---|---|---|---:|---:|---:|---:|---:|
| f2h13 | 2 Mark | 1563-1564 | København | (no specs) | — | — | — | — |
| f2h14 | 1 Mark | 1563-1570 | København | 6.878 g | **0.437** | **3.000 g** | **25.904** | **9.03** |
| f2h15 | 4 Skilling | 1563 | København | 6.878 g | 0.437 | 3.000 g | 25.904 | 9.03 |
| f2h16 | (unspecified) | 1563-1570 | (unclear) | — | — | — | — | — |
| f2h16x | 2 Skilling | 1563-1570 | København | (no specs) | — | — | — | — |

**Klipping war finance** is the most dramatic monetary intervention
of the period. At Marken-fin 25.904 daler per Cölln. Marck fein,
1 Daler face contains only ~9 g fein silver — **~35 % of the 9-Fuß
standard** (25.984 g per Daler). The face-value-vs-metal-value
spread is the seigniorage that financed the war («quick profit to
the king's treasury»; «payment of mercenary troops»).

Mintage volumes for war Klipping likely large but not consistently
quantified in Hede pages.

### 5.4 Schleswig-Holstein-Lübeck small change 1566–1571

In parallel with København output, Flensborg minted lübisch-reckoning
small change after the Reichsmüntzordnung 1566:

| Hede | Nominal | Year | Mint | Brutto | Finhed | Finvægt | mf | g fein per Daler |
|---|---|---|---|---:|---:|---:|---:|---:|
| f2h30 | 1 Skilling lybsk | 1566-1571 | Flensborg | 1.856 g | 0.391 | 0.725 g | 10.419 | 22.44 |
| f2h31 | 1 Søsling lybsk | 1566 | Flensborg | 1.124 g | 0.328 | 0.369 g | 10.237 | 22.84 |
| f2h32 | 1 Blaffert lybsk | 1566-1571 | Flensborg | (no specs) | — | — | — | — |
| f2h33 | 1 Penning lybsk | 1566-1571 | Flensborg | (no specs) | — | — | — | — |

Flensborg silver runs at mf ~10.3–10.4 daler / Cölln. Marck fein,
implying ~22.4–22.8 g per Daler — somewhat below 9-Fuß (25.984) but
considerably above the contemporaneous København Klipping war
output. Schleswig-Holstein-Lübeck reckoning sub-coin maintained a
closer-to-imperial standard than the København war finance.

### 5.5 1572 Speciedaler — «Elfsborgs løsen»

Hede entry **f2h17** «1 Speciedaler 1572 København (Elfsborgs løsen)»
exists in cache but specs are not extracted to JSON (specs.default
empty). Per monthuset.dk and Galster sources:

> «Sølvet fra Elfsborgs løsesum blev smeltet om og brugt til at præge
> denne smukke Speciedaler fra 1572, som blev udgivet i forbindelse
> med Frederik II's bryllup med Sophie af Mecklenburg.»

Translation: «The silver from the Älvsborg ransom was melted down
and used to strike this beautiful Speciedaler of 1572, issued in
connection with Frederik II's marriage to Sophie of Mecklenburg.»

**Historical context**:
- Treaty of Stettin (December 1570) ended the Seven Years' War.
- Sweden returned Älvsborg fortress to Denmark in exchange for
  silver ransom paid by Sweden.
- The ransom silver («Elfsborgs løsen») was melted into commemorative
  Specieds aler.
- The 1572 issue coincided with Frederik II's wedding to Sophie of
  Mecklenburg (also 1572).

The Hede f2h17 page suggests this is a single issue tied to the
specific historical event. NOT a Møntordning — a ceremonial /
prestige strike using a specific silver source. Per Galster:

> «Daleren gik under navnet 'speciedaler', eller daler in specie,
> dvs. en daler, som man kan se eller en daler i ét stykke, modsat
> en daler optalt i mark, skilling eller anden mønt.»

Translation: «The daler went under the name 'speciedaler', or daler
in specie, i.e. a daler one can see or a daler in one piece, as
opposed to a daler counted in mark, skilling, or other coin.»

The «Speciedaler» term as a numismatic concept (physical full-weight
specie coin, distinguished from accounting-daler) emerges
semantically through the late 16th-century / early 17th-century
period. The 1572 Frederik II issue is one notable specific example
but does NOT mark a formal codification. Per Wikipedia
(<https://en.wikipedia.org/wiki/Danish_rigsdaler>): the term
«Rigsdaler Species» first appeared on actual coins under Christian
VII (1766–1808). Christian V's 1671 Forordning is often cited as
the formal Speciedaler-standard codification.

---

## 6. 1572 Speciedaler — Frederik II coin types continuing 1584+

Per danskmoent.dk's general Frederik II coinage description
(<https://www.danskmoent.dk/f2flens.htm> + search results):

> «Frederik II had a series of common gold coins struck in 1584 on
> his new coin press in the deer park by Frederiksborg, including
> Portuguese gold coins of 10 1/8 ducats (35.20 g), Rose nobles of
> 2 1/4 ducats (7.69 g), Double ducats of 2 ducats (6.91 g),
> Angelots of 1 1/2 ducats (5.06 g), Hungarian gold coins of 1 ducat
> (3.50 g), Gold crowns of 1 ducat (3.38 g), and Gold guilders of
> 15/16 ducat (3.27 g).»

This 1584 set formalises the Frederik II gold-types pattern that
was already visible in our 1563-1564 cached Hede entries (f2h1
Ungersk Gylden, f2h2/f2h5 Guldkrone, f2h3/f2h6 Rhinsk Gylden, f2h4
Dukat). The 1584 list adds:

- **Portugaløser of 10 1/8 ducats** (35.20 g) — i.e. Reichsdukat-
  multiple at 10⅛ Dukaten face value. Matches the Bremerholm
  Portugaløser tradition (Christian IV 1591-1593 Haderslev series
  at similar 35 g brutto, per `daler_klippe_1604.md` §4.1).
- **Rosenobel of 2 1/4 ducats** (7.69 g) — appears later in Christian
  IV's reign at fineness 0.833 per Hede c4h23/c4h24 (Kalmar War
  1611-1629 series).
- **Angelots of 1 1/2 ducats** (5.06 g) — Anglo-French gold type
  imitated by Danish royal mint.

The Hede cache includes Frederik II Frederiksborg-press entries
**f2h7a–f2h7g** (Portugaløser, Rosenobel, 2 Dukat, Ungersk Gylden,
Guldkrone, Rhinsk Gylden) all dated 1584 — but the cache JSON has
no metric specs for these (specs.default empty). Direct re-extraction
from danskmoent.dk pages would be needed to obtain fineness / brutto
/ fein per piece for the 1584 set.

---

## 7. Per-coin standards — summary table

Aggregating computed standards from §§3–5 above:

### 7.1 Gold standards 1545–1572

| Hede | Year | Type | Fineness | Per-coin fein (g) | Standard family |
|---|---|---|---:|---:|---|
| c3h15 | 1546 | 1 Rhinsk Gylden | 0.750 | 2.458 | Rhenish Gulden (~95/Marck) |
| c3h1 | 1557 | 1 Ungersk Gylden | 0.986 | 3.442 | Reichsdukat (~67.94/Marck) |
| c3h2 | 1557 | 2 Ungersk Gylden | 0.986 | 6.884 | Reichsdukat (2×) |
| f2h1 | 1563 | 1 Ungersk Gylden | 0.986 | 3.442 | continues Reichsdukat |
| f2h2 | 1563 | 1 Guldkrone | 0.934 | 3.120 | own Guldkrone (~74.95/Marck) |
| f2h3 | 1563 | 1 Rhinsk Gylden | 0.770 | 2.500 | continues Rhenish (~93.5/Marck) |
| f2h4 | 1564 | 1 Dukat | 0.986 | 3.442 | continues Reichsdukat |
| f2h5 | 1564 | 1 Guldkrone | 0.934 | 3.120 | continues own Guldkrone |
| f2h6 | 1564 | 1 Rhinsk Gylden | 0.770 | 2.500 | continues Rhenish |
| f2h8 | 1560/63 | 3 Mark (gold) | 0.906 | 26.491 | one-off (heavy gold; same fein as silver Daler at mf 8.827) |

### 7.2 Silver standards 1541–1572

| Hede | Year | Type | mf (daler/Marck) | g fein per Daler | Standard family |
|---|---|---|---:|---:|---|
| c3h3 (3A) | 1541 | 1 Mark | 8.827 | 26.494 | **Christian-III 1541 København (heavier)** |
| c3h4 | 1541-1544 | 8 Skilling | 8.827 (implied) | 26.494 | same |
| c3h5 | 1541-1554 | 4 Skilling | 8.827 (implied) | 26.494 | same |
| c3h7 | 1541-1544 | Hvid | 8.833 | 26.484 | same |
| c3h3 (3B) | 1544-1555 | 1 Mark | 9.481 | 24.665 | **Christian-III 1544 København (debasement)** |
| c3h8 | 1546 | Penning | 10.666 | 21.93 | smaller-denom proportional debasement |
| c3h16 | 1545 | 1 sølvgylden | 8.982 | 26.038 | Flensborg variant |
| c3h19, c3h20 | 1547 | sølvgylden | 8.982 | 26.038 | Flensborg variant |
| c3h21, c3h22 | 1545-1554 | søsling lybsk | 9.287 | 25.180 | Flensborg lübisch, near-9-Fuß |
| f2h10 | 1544-1563 | 8 Skilling | 12.321 | 18.98 | F2 early-reign debasement |
| f2h11 | 1559-1563 | 2 Skilling | 13.333 | 17.54 | F2 small-change debasement |
| f2h12 | 1562-1563 | 1 Skilling | 14.667 | 15.94 | F2 deeper small-change debasement |
| **f2h14** | **1563-1570** | **1 Mark Klipping** | **25.904** | **9.03** | **Syvårskrigen war Klipping** |
| **f2h15** | **1563** | **4 Skilling Klipping** | **25.904** | **9.03** | **Syvårskrigen war Klipping** |
| f2h30 | 1566-1571 | 1 Skilling lybsk | 10.419 | 22.44 | Flensborg lübisch (post-1566 RMO) |
| f2h31 | 1566 | 1 Søsling lybsk | 10.237 | 22.84 | Flensborg lübisch (post-1566 RMO) |
| f2h17 | 1572 | 1 Speciedaler | (specs not in cache) | (presumed ~25.984 per 9-Fuß) | Elfsborgs løsen ceremonial |
| f2h20 | 1578-1579 | 8 Skilling | 9.762 | 23.96 | post-war F2 recovery |
| f2h21 | 1579 | 1 Skilling | 11.000 | 21.26 | recovery — small change still debased |
| f2h24, f2h26 | 1582-1585 | 8 Skilling | 9.762 | 23.96 | continues 1578 standard |

### 7.3 9-Fuß standard (Reichsmüntzordnung 1566 imperial) — reference

For comparison: the Reichsmüntzordnung 1566 standard for the
Reichsthaler was 9 Thaler per Cölln. Marck fein → **mf = 9.000,
g fein per Daler = 25.984**, fineness 0.889. The Danish Speciedaler
that emerges from Christian IV's reign onward conforms to this
standard (Hede c4h44 1596 Speciedaler København: brutto 29.232 g,
finhed 0.888, fein 25.984 g — canonical 9-Fuß).

Comparison:
- **Christian-III 1541 standard** (mf 8.827, 26.494 g per Daler) is
  **~2 % heavier** than imperial 9-Fuß.
- **Christian-III 1544 standard** (mf 9.481, 24.665 g) is **~5 %
  lighter** than imperial 9-Fuß.
- **Flensborg variants** sit in between.
- **Syvårskrigen Klipping** (9.03 g per Daler) is **65 % below** the
  9-Fuß standard — extreme war debasement.
- **Post-1572 F2 large-denomination silver** approaches 9-Fuß; small
  change remains modestly debased.

---

## 8. Three observable monetary phases

Aggregating the per-coin evidence, three distinct silver-standard
phases are visible in the 1541-1572 window:

### Phase A: Christian-III standard era 1541–1559

- 1 Daler = 3 Mark Danske convention.
- København 1541-1543: 1 Daler ≈ 26.5 g fein (mf 8.827).
- København 1544-1555: 1 Daler ≈ 24.7 g fein (mf 9.481, 7 % debasement).
- Flensborg sølvgylden 1545-1547: 1 Daler ≈ 26.0 g fein (mf 8.982).
- Flensborg søsling lybsk 1545-1554: 1 Daler ≈ 25.2 g (mf 9.287, near
  imperial standard).
- Continues into Frederik II's early reign 1559-1563 with progressive
  small-change debasement.

### Phase B: Syvårskrigen Klipping debasement 1563–1570

- Frederik II war Klipping series (1 Mark, 4 Skilling) at mf 25.904
  → 1 Daler ≈ 9 g fein.
- Face-value-vs-metal-value spread = state seigniorage for war
  finance.
- Klipping format (firkantet blanket) — production at København.
- Concluded December 1570 with Treaty of Stettin (end of Seven
  Years' War).

### Phase C: 1572 Reichsthaler 9-Fuß alignment (assumed start)

- 1572 «Elfsborgs løsen» Speciedaler (f2h17) — first symbolic
  full-weight specie issue, using Älvsborg ransom silver.
- Post-Reichsmüntzordnung-1566 imperial framework adoption.
- Frederik II 1578+ silver moves toward 9-Fuß-compliant standard
  (mf 9.762, 23.96 g per Daler for 8 Skilling — slightly below
  imperial but recovery from war Klipping is clear).
- Christian IV 1596+ Speciedaler reaches canonical 9-Fuß (mf 9.000,
  25.984 g per Daler at 0.888 fineness — Hede c4h44).

Note: the cache lacks metric specs for f2h17 specifically; the
classification of 1572 as a 9-Fuß-aligned issue is inferred from
contextual evidence (Elfsborgs ransom silver, post-1566 RMO,
historical narrative of «specie» distinction emerging) rather than
direct measurement. Direct verification would require checking
specimen weights and fineness assays for surviving 1572 Speciedaler
pieces.

---

## 9. Mints and mintmasters 1534–1572

For reference, the Danish-Norwegian mints active in this window:

| Mint | Period active (this window) | Notable mintmasters | Notable output |
|---|---|---|---|
| København (Bremerholm) | 1534-1572 (and beyond) | Hans Willers, Hans Köpelin, Laudris Hammer (gold, 1560s) | Ungersk Gylden, Guldkrone, Rhinsk Gylden, Dukat, 1 Mark Christian III, Syvårskrigen Klipping, 1572 Speciedaler |
| Flensborg | 1545-1571 | Jørgen Kock den Yngre, Reynold Junge (mark: glødehagen) | Rhinsk Gylden 1546, sølvgylden 1545-1547, søsling lybsk 1545-1554, post-1566 lübisch small change |
| Århus | 1534-1536 | (unknown, war finance) | Count's Feud Klippinger (2 Mark, 8/4/2 Skilling) |
| Roskilde | 1535-1536 | (unknown, war finance) | Count's Feud Klippinger (2 Mark, 1 Mark, 4/2 Skilling) |
| Frederiksborg | 1582+ | (Frederik II's deer-park press) | 8 Skilling 1582-1585, 1 Mark 1583, 1584 gold series (f2h7a-g) |

Notes:
- Bremerholm (København) is consistently the royal mint for both
  silver and gold throughout the period.
- Flensborg's role for Schleswig-Holstein duchy issuance ends after
  1571 (per Hede coverage); later Schleswig-Holstein output shifts to
  Glückstadt (Christian IV 1620+).
- Århus and Roskilde Klippinger 1534-1536 are pre-Møntordning war
  finance issues from Grevens fejde (the civil war).
- Frederiksborg becomes Frederik II's secondary mint from 1582
  onwards, using his new deer-park coin press.

---

## 10. Sources consulted

### Direct primary references (verbatim quoted above)

- **Galster, Georg** — *Danske mønter* (danskmoent.dk transcript).
  Quotes on Christian III's 1541 Møntordning, daler-at-head-of-system,
  first daler 1518.
  <https://www.danskmoent.dk/galster/galshist.htm>

- **danskmoent.dk f2flens** — Frederik II coinage overview.
  Bremerholm tri-standard, three mintmasters, 1584 Frederiksborg
  gold press.
  <https://www.danskmoent.dk/f2flens.htm>

- **Nationalmuseet — Den Nordiske Syvårskrig 1563-1570**.
  Klipping war finance, mercenary payment role.
  <https://natmus.dk/historisk-viden/temaer/militaerhistorie/danmarks-krige/syvaarskrigen/>

- **monthuset.dk — Frederik II Speciedaler 1572**.
  Elfsborgs løsen ransom silver, Sophie of Mecklenburg wedding.
  <https://www.monthuset.dk/sjaeldne-monter/frederik-ii-speciedaler-1572-2500970926>

- **Wikipedia — Danish rigsdaler**.
  «Rigsdaler Species» term first appearing under Christian VII;
  Speciedaler standard formalisation history.
  <https://en.wikipedia.org/wiki/Danish_rigsdaler>

### Hede catalogue pages (local cache `scripts/cache/hede/c3h*.json`,
`f2h*.json`)

Christian III: c3h1, c3h2, c3h3 (3A + 3B), c3h4, c3h5, c3h6, c3h7,
c3h8, c3h9, c3h10, c3h11, c3h12, c3h13, c3h15, c3h16, c3h19, c3h20,
c3h21, c3h22, c3h23, c3h24, c3h25, c3hede (oversigt).

Frederik II (up to 1572): f2h1, f2h2, f2h3, f2h4, f2h5, f2h6, f2h8,
f2h9, f2h10, f2h11, f2h12, f2h13, f2h14, f2h15, f2h16, f2h16x, f2h17
(Elfsborgs løsen), f2h30, f2h31, f2h32, f2h33, f2h34.

Frederik II (1572+): f2h7a-g (1584 Frederiksborg gold set, specs
missing), f2h20, f2h21, f2h24, f2h25, f2h26, f2h27, f2h28, f2h29.

URL pattern: `https://www.danskmoent.dk/chr/c3h<N>.htm` (Christian
III) and `https://www.danskmoent.dk/fr/f2h<N>.htm` (Frederik II).

### Secondary literature cited via Hede

- **Ramus** — referenced page 147 (c3h1), 165 (c4h10/13). Paper-only.
- **NFM (Numismatiske Foreningsmøntreferencer?)** — XIII p. 284
  (c3h1), XIV p. 145 (c3h2), XII p. 10 (c3h15). Paper-only.
- **Wilcke** — vol. VII p. 306 (c3h2 silver off-strike note).
- **Grandjean** — page 184 (c3h1). Paper-only.
- **Galster, Georg** — *Flensborg Mønt*, Sønderborg 1967, pp. 14-26
  (c3h16). Paper-only.

### Online news / blog references

Search returned several Danish numismatic blog posts and forum
threads with partial info; not quoted directly. The four primary
sources above (Galster danskmoent transcripts, Nationalmuseet,
monthuset, Wikipedia) are the substantive references for facts
quoted in this document.

---

*Document compiled 2026-05-14 by claude during research-pass on
Christian III's 1541 Møntordning and the Danish silver standard
prior to 1572. Pure data dump for future-session use — no project
classification recommendations included by design.*
