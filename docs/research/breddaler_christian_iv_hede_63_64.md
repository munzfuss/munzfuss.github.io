# Christian IV Breddaler — Hede 63 and Hede 64: denomination ↔ catalogue concordance

Opened 2026-11-07 (curator request: «таблиці відповідності номіналів, (суб)індексів Hede,
індексів KM, включно з прогнозованими»). Scope: the two Breddaler types of Christian IV,
each struck in several values and catalogued by Hede under one number with letters,
without saying which letter is which value. Out of scope: Hede 63 / 64 of other
reigns (Christian V Hede 63 = Speciedaler 1671, etc.), the 1 Speciedaler Hede 53.

## 1. What the Hede pages give — and what they do not

[danskmoent c4h63](https://www.danskmoent.dk/chr/c4h63.htm) (cache
`scripts/cache/hede/c4h63.htm`):

> «Christian 4., Breddaler u.år, København — Forside: kongen til hest, bagside: våbenskjold
> (Hede 63A-F, Schou 15-17, 20-21, 26-27, 29, Sieg 97-102). Slået af Hans Flemming i
> værdierne 1, 1-1/2, 2, 3, 4 og 6 speciedalere.»

(transl.: «undated Breddaler, Copenhagen — obverse: the king on horseback, reverse: coat of
arms … struck by Hans Flemming in the values 1, 1½, 2, 3, 4 and 6 speciedaler»)

[danskmoent c4h64](https://www.danskmoent.dk/chr/c4h64.htm) (cache
`scripts/cache/hede/c4h64.htm`):

> «Christian 4., Breddaler, København — Forside: brystbillede, bagside: kongen til hest
> (Hede 64A-D, Schou 18-28, Sieg 103-106). Slået af Schwabe i værdierne 1, 1-1/2, 2 og 3
> speciedalere.»

(transl.: «obverse: bust, reverse: the king on horseback … struck by Schwabe in the values
1, 1½, 2 and 3 speciedaler»)

The pages give the letter RANGE, the value LIST and page-wide Schou / Sieg ranges. They do
**not** pair a letter with a value, nor a Schou / Sieg number with a letter. Every
letter ↔ value pair below therefore comes from another source (column «Basis»), and the
seed builder records it as such (`_MULTI_VALUE_PAGES` in
`scripts/maintenance/build_hede_denmark_seed.py`, curator 2026-11-06, `1356741`; rendered
«[ ]», `uncertainty.nominal: other_source`).

## 2. The Krause / Davenport system

NGC (= NumisMaster data) gives one KM number per value and ties each to a Davenport
letter. The Davenport number is the key that joins Krause to Hede: the **3537** series is
the Hede 63 design, the **3538** series the Hede 64 design.

| Dav | KM | Value | Krause date | Krause design note (NGC, verbatim) |
|---|---|---|---|---|
| 3537A | 154 | 1½ Sp | (1607-14) | «Similar to 2 Speciedaler, KM#147. Dav. #3537A. Breddaler.» |
| 3537B | 147 | 2 Sp | (1607-14) | «Dav. #3537B. Breddaler.» |
| 3537C | 77 | 3 Sp | (1607-14) | «Similar to 2 Speciedaler, KM#147. Dav. #3537C. Breddaler.» |
| 3537D | 115 | 4 Sp | (1607-14) | «Similar to 2 Specidaler, KM#147. Dav. #3537D. Breddaler.» |
| 3537E | 116 | 6 Sp | (1607-14) | «Similar to 2 Specidaler, KM#147. Dav. #3537E.» |
| 3538A | 155 | 1½ Sp | (ca.1611) | «Obverse: 1/2-figure of king, Reverse: King on horseback … Dav. #3538A. Breddaler.» |
| 3538B | 148 | 2 Sp | 1611 | (NumisMaster 65537: Dav 3538B; Numista 200434 «EC II 3538B») |
| 3538C | 78 | 3 Sp | (ca.1611) | «Obverse: 1/2-figure of king, Reverse: King on horseback … Dav. #3538C. Breddaler.» |

Cache: `scripts/cache/ngc/denmark/cuid_<id>.txt`. No 1 Speciedaler value appears in either
series in the sources we hold (gap, §5).

## 3. Concordance — Hede 63 (Hans Flemming, king on horseback / arms, ND 1607–1614)

«Prognosis» = derived by us, not printed by any source (§4).

| Value | Hede | Basis for letter ↔ value | Schou (Bruun) | Sieg (Bruun) | Dav | KM | Harck (Bruun) | Records |
|---|---|---|---|---|---|---|---|---|
| 6 Sp | 63A | page photo caption «Det afbildede, unikke eksemplar af 6 speciedaler»; Numista 568548 | — | — | 3537E | 116 | — | [Numista 568548](https://en.numista.com/568548), [NGC 1050083](https://www.ngccoin.com/price-guide/world/denmark-6-speciedaler-km-116-1607-14-cuid-1050083-duid-1237849), NumisMaster 65595 |
| 4 Sp | 63B | Bruun Part IV lot 17061 «4 Speciedaler … Dav-3537D; KM-115; Hede-63B»; Numista 568172 | 16 | 115 | 3537D | 115 | 7.4 | Bruun 5844 ([Part IV](https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Mar2026_BruunIV_Coins_Catalog.pdf), lot 17061, 115.62 g), [Numista 568172](https://en.numista.com/568172), [NGC 1069046](https://www.ngccoin.com/price-guide/world/denmark-4-speciedaler-km-115-1607-14-cuid-1069046-duid-1237843), NumisMaster 65590 |
| 3 Sp | 63C | Bruun Part II lot 13123 «3 Speciedaler … Dav-LS528; KM-77; Hede-63C» | 17 | 114 | 3537C | 77 | — | Bruun 5845 ([Part II](https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf), lot 13123, 86.40 g), [NGC 1050185](https://www.ngccoin.com/price-guide/world/denmark-3-speciedaler-km-77-1607-14-cuid-1050185-duid-1237833), NumisMaster 65569 |
| 2 Sp | 63D | Bruun Part I lot 1052 «2 Speciedaler … KM-147; Dav-LS529; Hede-63D» | 20 | 113.2 | 3537B | 147 | — | Bruun 5846 ([Part I](https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Sept2024_LEBruun_Collection_Part_I_Catalog.pdf), lot 1052, 56.36 g), [NGC 1050079](https://www.ngccoin.com/price-guide/world/denmark-2-speciedaler-km-147-1607-14-cuid-1050079-duid-1237551), NumisMaster 65536, [ucoin 163074](https://en.ucoin.net/coin/denmark-2-speciedaler-1607/?tid=163074) |
| 1½ Sp | 63E | Bruun Part V lot 14127 «1 1/2 Speciedaler … Hede-63E» | 27 | 112.1 | 3537A | **154** | 7.7.2 | Bruun 5851 ([Part V](https://www.danskmoent.dk/pdf/SBG_Oct2026_BruunPartV_WebCat_LR_2.pdf), lot 14127, 48.51 g — prints «KM-115» ⚠ §6), [NGC 1060266](https://www.ngccoin.com/price-guide/world/denmark-1-1-2-speciedaler-km-154-1607-14-cuid-1060266-duid-1237537), NumisMaster 65516 |
| 1 Sp | 63F | **by elimination** (§4.1): six letters, six values, 63A–E paired | — | — | 3537 | 144 | — | [NGC 1050179](https://www.ngccoin.com/price-guide/world/denmark-speciedaler-km-144-1607-14-cuid-1050179-duid-1237430) «Similar to 2 Daler, KM#147. Dav. #3537. Breddaler.», NumisMaster 65422 |

## 4. Concordance — Hede 64 (Schwabe, bust / king on horseback, ca. 1611, København)

| Value | Hede | Basis for letter ↔ value | Schou (Bruun) | Sieg (Bruun) | Dav | KM | Harck (Bruun) | Records |
|---|---|---|---|---|---|---|---|---|
| 3 Sp | 64A | **working decision** (§4.1) | — | — | 3538C | 78 | — | [NGC 1050186](https://www.ngccoin.com/price-guide/world/denmark-3-speciedaler-km-78-ca.1611-cuid-1050186-duid-1237834), NumisMaster 65570, [Numista 522052](https://en.numista.com/522052) (86.98 g) — no source names a Hede letter; joined to 64A 2026-11-07 |
| 2 Sp | 64B | Bruun Part I lot 1053 «2 Speciedaler … KM- 148; Dav-LS533; Hede-64B»; Bruun Part IV lot 17062 «2 Speciedaler … Hede- 64B» | 22, 24 | 119.1, 119.3 | 3538B | 148 | 6.13.1 | Bruun 5849 (Part I, lot 1053, 58.00 g), Bruun 5847 (Part IV, lot 17062, 57.58 g — prints «KM-154» ⚠ §6), [Numista 200434](https://en.numista.com/200434), NumisMaster 65537, [ucoin 163073](https://en.ucoin.net/coin/denmark-2-speciedaler-1611/?tid=163073) |
| 1½ Sp | 64C | Bruun Part II lot 13124 «1 1/2 Speciedaler … Hede-64C» | 28 | 118 | 3538A | **155** | — | Bruun 5850 (Part II, lot 13124, 48.80 g — prints «KM-154» ⚠ §6), [NGC 1050078](https://www.ngccoin.com/price-guide/world/denmark-1-1-2-speciedaler-km-155-ca.1611-cuid-1050078-duid-1237538), NumisMaster 65521 |
| 1 Sp | 64D | **working decision** (§4.1) | — | — | 3538 | 145 | — | [NGC 1050713](https://www.ngccoin.com/price-guide/world/denmark-speciedaler-km-145-ca.1611-cuid-1050713-duid-1237431) «Half figure of King / King on horseback … Dav. #3538. Breddaler.», NumisMaster 65424 |

### 4.1 How the unprinted letters are paired (derived, not attested)

- In Hede 63 the attested letters run in **descending** value: A 6 → B 4 → C 3 → D 2 → E 1½.
  The page lists six letters «Hede 63A-F» and six values; with A–E paired by Bruun and
  Numista, the one value left is 1, hence 63F = 1 Sp — **by elimination**, which needs no
  assumption about the order. The 1 Sp of the Dav 3537 design is KM 144 (NGC 1050179).
- In Hede 64 the attested letters B = 2 and C = 1½ fit the same descending order; with the
  page's list 1, 1½, 2, 3 they leave {1, 3} for {A, D}. Elimination stops there: A = 3 /
  D = 1 rests on the **assumption** that Hede 64 runs in descending value like Hede 63.
  Curator 2026-11-07 («Б»): adopted as a working decision.
- 64A = 3 Sp then pairs with KM 78 / Dav 3538C (the only 3 Sp of the 3538 design), and
  64D = 1 Sp with KM 145 / Dav 3538 (NGC 1050713).
- What would settle it: Hede's printed catalogue (the letters with values), or a source
  that prints «Hede-64A» / «Hede-64D» / «Hede-63F» with a value.
- Data state (2026-11-07): the seeds `dk-hede-c4h63f` / `c4h64a` / `c4h64d` carry 1 / 3 / 1
  Speciedaler, `nominal_verified: false`, with an inferred `page_values` entry quoting the
  page's list (Hede builder `_MULTI_VALUE_PAGES`); each is merged with its KM records
  (merge_decisions/danish_realm.yml) and classified 9_thaler / I. If a source ever prints
  «Hede-64A» or «Hede-64D» with the other value, the 64 merges swap (KM 78 ↔ KM 145).

## 5. Gaps

- A KM / Dav number for the 1 Speciedaler of each design is given only by NGC / NumisMaster
  (KM 144 = Dav 3537, KM 145 = Dav 3538, both «Unique»); their weight 29.232 g and fineness
  .875 are the catalogue's standard figures, not a weighing (§8). (Earlier versions of this
  section said no source gives them — corrected 2026-11-07.)
- Schou / Sieg are given per letter only by Bruun. The Sieg numbers Bruun prints
  (112.1–115, 118–119.3) are outside the page's «Sieg 97-102» / «Sieg 103-106»: a different
  Sieg edition (CLAUDE.md §9.4 caveat (a), editions renumber) — not used as a key.
- The Schou numbers Bruun prints all lie inside the page's own ranges (63: 16, 17, 20, 27 ∈
  «15-17, 20-21, 26-27, 29»; 64: 22, 24, 28 ∈ «18-28»), and Schou 28 is outside the Hede 63
  list — an independent check on Bruun's Hede letters for 63E and 64C.

## 6. ⚠ Source discrepancies

| Source | Prints | Against | Data state |
|---|---|---|---|
| Bruun Part V lot 14127 (Bruun 5851, Hede 63E, 1½ Sp) | «KM-115» | KM 115 = 4 Sp Dav 3537D (Bruun lot 17061 itself, NGC 1069046, Numista 568172); the 1½ Sp of the Dav 3537 design is KM 154 | `catalog_marks` (!) on the seed, curator 2026-11-07 |
| Bruun Part II lot 13124 (Bruun 5850, Hede 64C, 1½ Sp) | «KM-154» | KM 154 is Dav 3537A, «Similar to 2 Speciedaler, KM#147», (1607-14) — the Hede 63 design; the 1½ Sp of the Hede 64 design (bust / horseman, ca. 1611) is KM 155, Dav 3538A | `catalog_marks` (!), curator 2026-11-07 |
| Bruun Part IV lot 17062 (Bruun 5847, Hede 64B, 2 Sp) | «KM-154» | Bruun Part I lot 1053 prints «KM- 148» for the same Hede 64B; KM 154 is a 1½ Sp | `catalog_marks` (!) since 2026-11-06 (`a4f4a03`); reason re-worded 2026-11-07 to cite NGC instead of lot 13124 |
| danskmoent c4h63 (page title) | «København» | Bruun lots 1052, 14127, 17061: «Elsinore Mint»; lot 13123: «Copenhagen Mint (?)» | not resolved; seeds keep each source's mint |

The same KM error recurs in one catalogue (KM-154 on two different coins, KM-115 on two
different values), which is why the KM number — not the Hede letter — is taken as Bruun's
slip in these lots.

## 7. Records and classes (2026-11-07)

- Hede 63E class: `dk-hede-c4h63e`, `dk-bruun-5851`, `ngc-1060266`, `denmark-numismaster-65516`
  (merge_decisions/danish_realm.yml, 2026-11-07).
- Hede 64C class: `dk-hede-c4h64c`, `dk-bruun-5850`, `ngc-1050078`, `denmark-numismaster-65521`
  (merge_decisions/danish_realm.yml, 2026-11-07); final `km-154-hede-64b-chr-iv-1611` (id is
  historical; the coin is KM 155).
- Hede 63F class: `dk-hede-c4h63f`, `ngc-1050179`, `denmark-numismaster-65422` (KM 144).
- Hede 64D class: `dk-hede-c4h64d`, `ngc-1050713`, `denmark-numismaster-65424` (KM 145).
- Hede 64A class: `dk-hede-c4h64a`, `ngc-1050186`, `denmark-numismaster-65570`,
  `dk-numista-522052` (KM 78). 63F and 64D are kept apart by explicit no_merges.
- All Hede 63 / 64 classes are 9_thaler / I since 2026-11-07.
- The KM 144 final still cites KMM 78341 («speciedaler», Christian 4, no type number, no
  weight, no image); its seed left the corpus with the KMM stub rule (`2b96f63`). Nothing
  ties it to KM 144 in particular.
- Before 2026-11-07, KM 154 (NGC 1060266, NumisMaster 65516) sat with Hede 64C because of
  Bruun 5850's «KM-154», and the KM 155 records sat in their own unsorted class.

## 8. Weights and fineness (2026-11-07)

Specimen weights against 1 Speciedaler = 29.232 g (9-Thaler-Fuß: 8 per rough Cöllnische
Marck at 14²⁄₉ Loth) and 28.89341 g (9¼-Thaler-Fuß at 14 Loth), both from `fuesse.yml`;
Δ computed here.

| Sp | Hede | Specimen | g | Δ 9-Fuß | Δ 9¼-Fuß |
|---|---|---|---|---|---|
| 6 | 63A | Numista 568548 | 172.50 | −1.65 % | −0.50 % |
| 4 | 63B | Bruun 5844 = Numista 568172 (same value) | 115.62 | −1.12 % | +0.04 % |
| 3 | 63C | Bruun 5845 | 86.40 | −1.48 % | −0.32 % |
| 3 | 64A | Numista 522052 | 86.98 | −0.82 % | +0.35 % |
| 2 | 63D | Bruun 5846 | 56.36 | −3.60 % | −2.47 % |
| 2 | 63D | ucoin 163074 | 58.56 | +0.16 % | +1.34 % |
| 2 | 64B | Bruun 5847 | 57.58 | −1.51 % | −0.36 % |
| 2 | 64B | Bruun 5849 | 58.00 | −0.79 % | +0.37 % |
| 2 | 64B | Numista 200434 | 58.61 | +0.25 % | +1.42 % |
| 2 | 64B | ucoin 163073 | 58.56 | +0.16 % | +1.34 % |
| 1½ | 63E | Bruun 5851 | 48.51 | **+10.63 %** | +11.93 % |
| 1½ | 64C | Bruun 5850 | 48.80 | **+11.29 %** | +12.60 % |

- NGC / NumisMaster's 58.464 g (2 Sp) and 29.232 g (1 Sp) equal the standard exactly and are
  left out as catalogue figures, not weighings.
- ⚠ Both 1½ Speciedaler weigh 1.66–1.67 Speciedaler (5/3 = 48.72 g: −0.43 % / +0.16 %).
  Bruun prints «1 1/2 Speciedaler» on both lots, Krause (KM 154 / 155) the same; no source
  names a 1⅔ value. danskmoent c4h63 / c4h64: «Vægten er usikker» (the weight is uncertain).
  Open; no mark set.
- Weight alone does not separate the 9- from the 9¼-Thaler-Fuß here (1.2 % apart, inside
  the spread). Wilcke 1919 s. 92–93 gives «Speciedaleren skulde veje 2 Lod, 8 Stkr. af 1 Mark
  brutto» and, after Prætorius, «Schwabes Dalere var 14 4/18 lødige» = 9-Thaler-Fuß; Wilcke
  calls the fineness derivation, from one ledger entry, «ret betænkeligt». Classification
  9_thaler (curator 2026-11-07).
- Fineness: attested only as catalogue figures — .888 on both 2 Sp types (NGC, NumisMaster,
  Numista, ucoin), .875 on KM 144 / 145 (NGC, NumisMaster). No assay of a Breddaler is known
  to us. The other classes carry 0.88889, `fineness_verified: false`, with an inferred
  `standard` entry quoting Wilcke 1919 s. 93 (Hede seeds 63A/B/C/E, 64C; Numista 522052).
