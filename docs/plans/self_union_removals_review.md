# Self-union removals — curator review (stage B run 4, 2026-10-23)

Every value below is one the `--no-self-union` rebuild removes from a final at `HEAD` of branch `rebuild-from-members`. Source: `B_classified_nh.json` (classify_self_union_diff.py --no-history). Buckets starting with **S** are proposed for the removal list (stage E); **D** are a promoted final's frozen scalar replaced by the class's; **R** / **H** need a decision.


## S-moved — 1437 values on 531 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 265 |
| catalog | promoted | 207 |
| mint | foundation | 10 |
| mint | promoted | 36 |
| sources | foundation | 95 |
| sources | promoted | 816 |
| year_ranges | foundation | 8 |

Examples:

- `c-07e5aea8` [_unclassified] sources: `('https://ikmk.smb.museum/object?id=18231250', 'IKMK Berlin 18231250')` — home c-dbf87a8e
- `c-07e5aea8` [_unclassified] sources: `('https://ikmk.smb.museum/object?id=18231251', 'IKMK Berlin 18231251')` — home c-dbf87a8e
- `c-07e5aea8` [_unclassified] catalog: `('others', 'Schrötter# 1794')` — home c-dbf87a8e
- `c-07e5aea8` [_unclassified] catalog: `('others', 'Schrötter# 1797')` — home c-dbf87a8e
- `c-383db910` [_unclassified] mint: `"Zellerfeld"` — home c-010f905e
- `c-42750dfb` [_unclassified] mint: `"Zellerfeld"` — home c-010f905e
- `dk-tid-130240` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c9h1.htm', 'danskmoent.dk (Hede c9h1A)')` — home c-3412889a
- `dk-tid-162991` [danish_realm] sources: `('https://numismaster.com/MC_117787', 'NumisMaster')` — home dk-tid-162992
- `dk-tid-163034` [danish_realm] mint: `"Helsingør"` — home c-0055e09d
- `dk-tid-79082` [danish_realm] catalog: `('bruun_page', '86')` — home c-561c542f
- `dk-tid-79082` [danish_realm] catalog: `('bruun_part', 'IV')` — home c-0008432e
- `hede-134b-chr-v-1677` [danish_realm] mint: `"Christiansstad"` — home c-1c5e2813
- `hs-ikmk-18286372` [grafschaft_schaumburg] year_ranges: `1616` — home c-036ff789
- `hs-ikmk-18286372` [grafschaft_schaumburg] year_ranges: `1617` — home c-036ff789

## S-moved-no_merge — 20 values on 11 finals

| field | origin | values |
|---|---|---|
| catalog | promoted | 1 |
| sources | promoted | 19 |

Examples:

- `c-5a55f683` [_unclassified] sources: `('https://ikmk.smb.museum/object?id=18286029', 'IKMK Berlin 18286029')` — home c-642b68f4, decision no_merge
- `c-5a55f683` [_unclassified] sources: `('https://ikmk.smb.museum/object?id=18286030', 'IKMK Berlin 18286030')` — home c-88793357, decision no_merge
- `c-6d39d27d` [schauenburg_pinneberg] catalog: `('others', 'Weinm# 152')` — home km-137419-ernst-1601, decision no_merge

## S-relabel — 128 values on 100 finals

| field | origin | values |
|---|---|---|
| sources | foundation | 83 |
| sources | promoted | 45 |

Examples:

- `c-00c2def8` [danish_norway] sources: `('https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf', 'Bruun Part II, lot 13203, p. 124'` — home c-bd07b231
- `c-0a210ec7` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc5h56.htm', 'danskmoent.dk (Hede nc5h56B)')`
- `dk-tid-55898` [danish_norway] sources: `('https://en.numista.com/55898', 'Numista')`
- `dk-tid-55898` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc7h12.htm', 'danskmoent.dk (Hede nc7h12)')`

## S-recorded — 106 values on 89 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 27 |
| catalog | promoted | 15 |
| mint | foundation | 36 |
| mint | promoted | 23 |
| sources | promoted | 5 |

Examples:

- `c-082b8af9` [_unclassified] mint: `"Harburg"` — home c-685da12e, recorded removal / retraction
- `c-116a22a6` [_unclassified] mint: `"Moisburg"` — home c-00071348, recorded removal / retraction
- `c-191330dc` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/403371', 'KMM 403371 (Inv. FP 3479.10)')` — recorded removal / retraction
- `c-03dc425f` [danish_realm] catalog: `('numista', '42091')` — home c-73caaf55, recorded removal / retraction
- `c-106fed1b` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/402836', 'KMM 402836 (Inv. FP 3594.6)')` — recorded removal / retraction
- `c-164b0c50` [danish_realm] catalog: `('numista', '214327')` — home c-46b4c6d7, recorded removal / retraction
- `dk-tid-101040` [danish_realm] mint: `"Kopenhagen"` — home c-0008432e, recorded removal / retraction
- `dk-tid-70759` [danish_realm] mint: `"Kopenhagen"` — home c-0008432e, recorded removal / retraction
- `dk-tid-79088` [danish_realm] catalog: `('numista', '90550')` — home c-b9bbfab0, recorded removal / retraction
- `dk-tid-99065` [danish_realm] catalog: `('numista', '111346')` — home c-860820e4, recorded removal / retraction

## S-covered — 39 values on 24 finals

| field | origin | values |
|---|---|---|
| catalog | promoted | 21 |
| mint | promoted | 18 |

Examples:

- `c-e5f4c8f1` [danish_norway] mint: `"Christiania?"`
- `c-1352d07f` [danish_realm] mint: `"Roskilde?"`
- `c-158f70a9` [danish_realm] catalog: `('mb', '541-46')`
- `c-f5ef0b21` [danish_realm] catalog: `('mb', '541-46')`

## S-v1-covered — 3 values on 2 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 2 |
| mint | foundation | 1 |

Examples:

- `km-5-fr-iv-1719` [danish_realm] mint: `"Hamborg"`
- `km-696-1-fr-vi-1826` [royal_holstein] catalog: `('km', 'sh:696')`
- `km-696-1-fr-vi-1826` [royal_holstein] catalog: `('km', 'sh:696.1')`

## D-promoted-class-wins — 7709 values on 7063 finals

| field | origin | values |
|---|---|---|
| diameter_mm_verified | promoted | 74 |
| fineness_verified | promoted | 18 |
| fraction | promoted | 48 |
| inscription_obv | promoted | 13 |
| inscription_rev | promoted | 10 |
| metal | promoted | 19 |
| metal_verified | promoted | 46 |
| mint_verified | promoted | 156 |
| mintmaster | promoted | 225 |
| nominal | promoted | 52 |
| ruler | promoted | 1285 |
| verification_note | promoted | 5544 |
| weight_rough_verified | promoted | 40 |
| year_first | promoted | 1 |
| year_label | promoted | 1 |
| year_last | promoted | 1 |
| year_verified | promoted | 176 |

Examples:

- `c-002b7e6e` [_unclassified] verification_note: `{"de": "Datensatz aus dem Interaktiven Katalog des Münzkabinetts Berlin (ikmk.smb.museum, CC BY-SA 4.0); die F`
- `c-002d0d2f` [_unclassified] verification_note: `{"de": "Datensatz aus dem Interaktiven Katalog des Münzkabinetts Berlin (ikmk.smb.museum, CC BY-SA 4.0); die F`
- `c-06cf2b64` [_unclassified] ruler: `"John Frederick (Johann Friedrich)"`
- `c-082b8af9` [_unclassified] diameter_mm_verified: `true`
- `c-082b8af9` [_unclassified] mint_verified: `true`
- `c-0830c299` [_unclassified] ruler: `"John Frederick (Johann Friedrich)"`
- `c-116a22a6` [_unclassified] diameter_mm_verified: `true`
- `c-116a22a6` [_unclassified] mint_verified: `true`
- `c-383db910` [_unclassified] weight_rough_verified: `true`
- `c-4375912f` [_unclassified] weight_rough_verified: `true`
- `c-61738645` [_unclassified] inscription_obv: `"BRAVNSCHWEIG 4 MOND BELEGERT HART MIT ALLEM ERNST GESTVRMET WART / DOCH HAT SIE SICH MANLICH GEWEHRT IR LOB V` — home c-1d410253
- `c-61738645` [_unclassified] inscription_rev: `"BELAGERVNG DER STAD BRAVNSCHWEIG VOM XXII IVL BIS XI NOVEM Ao 1615"` — home c-1d410253
- `c-6d1cfce1` [_unclassified] mintmaster: `"Henning Schlüter"` — home c-420e264a
- `c-6d1cfce1` [_unclassified] inscription_obv: `"V G G GEORG WILHELM HERTZOG ZU BRAUNSCHWEIG U LUNE"` — home c-a967bc11
- `c-6d1cfce1` [_unclassified] inscription_rev: `"PIETATE ET - JUSTITIA"` — home c-a967bc11
- `c-864e23b4` [_unclassified] mintmaster: `"Rudolf Bornemann"` — home c-0def855b
- `c-69d58126` [christian_ii_supporters] metal_verified: `true`
- `c-ddefc984` [christian_ii_supporters] metal_verified: `true`
- `c-039fa112` [danish_india] year_verified: `false`
- `c-04b837f2` [danish_india] year_verified: `false`
- `c-1a0998a0` [danish_norway] fineness_verified: `true`
- `c-2a619cb8` [danish_norway] fineness_verified: `true`
- `c-49ea148b` [danish_norway] metal: `"silver"` — home bruun-14444-ca-1681
- `c-5f490fda` [danish_norway] nominal: `"12 Skilling"` — home c-0752a8bd
- `c-8e850e11` [danish_norway] nominal: `"16 Skilling"` — home c-00f72248
- `c-abc3425a` [danish_norway] metal: `"silver"` — home bruun-14444-ca-1681
- `c-c2e82886` [danish_norway] fraction: `"1"`
- `c-d9906291` [danish_norway] fraction: `"1/96"`
- `c-551b645c` [danish_realm] year_first: `1629`
- `c-551b645c` [danish_realm] year_last: `1629`
- `c-551b645c` [danish_realm] year_label: `"1629"`

## D-foundation — 637 values on 547 finals

| field | origin | values |
|---|---|---|
| diameter_mm_verified | foundation | 5 |
| fineness_verified | foundation | 2 |
| inscription_obv | foundation | 5 |
| inscription_rev | foundation | 5 |
| metal_verified | foundation | 2 |
| mint_verified | foundation | 16 |
| verification_note | foundation | 523 |
| verified | foundation | 18 |
| weight_rough_verified | foundation | 4 |
| year_first | foundation | 20 |
| year_label | foundation | 20 |
| year_last | foundation | 17 |

Examples:

- `dk-tid-55898` [danish_norway] verification_note: `{"da": "Flyttet hertil fra Schleswig-Holstein-artefaktet — KM# 250 / Hede# 12A–12B / Brekke# 31–36 hører til C`
- `dk-tid-101038` [danish_realm] verification_note: `{"da": "Tildeling af møntfod og verifikation af den enkelte mønt mod Hede / Schön / Bruun udestår stadig.", "d`
- `dk-tid-101040` [danish_realm] mint_verified: `true`
- `dk-tid-163059` [danish_realm] verified: `true`
- `dk-tid-163410` [danish_realm] verified: `true`
- `dk-tid-70759` [danish_realm] mint_verified: `true`
- `dk-tid-97364` [danish_realm] diameter_mm_verified: `true`
- `dk-tid-97369` [danish_realm] diameter_mm_verified: `true`
- `hede-134b-chr-v-1677` [danish_realm] year_first: `1677`
- `hede-134b-chr-v-1677` [danish_realm] year_last: `1678`
- `hede-134b-chr-v-1677` [danish_realm] year_label: `"1677-1678"`
- `hede-18-fr-v-1749` [danish_realm] year_first: `1749`
- `hede-18-fr-v-1749` [danish_realm] year_last: `1749`
- `hede-18-fr-v-1749` [danish_realm] year_label: `"1749"`
- `km-16-2-chr-iv-1618` [danish_realm] metal_verified: `true`
- `km-16-2-chr-iv-1618` [danish_realm] weight_rough_verified: `true`
- `km-5-fr-iv-1719` [danish_realm] weight_rough_verified: `true`
- `km-x015-chr-iv-1648` [danish_realm] fineness_verified: `true`
- `km-x016-chr-iv-1622` [danish_realm] fineness_verified: `true`
- `bruun-L12177-unknown-1670` [erzbisthum_bremen_verden] metal_verified: `true`
- `km-46-fr-iii-1617` [gottorp_duchy] inscription_obv: `"E D G C H - S E S D G"` — home c-0aa98956
- `km-46-fr-iii-1617` [gottorp_duchy] inscription_rev: `"MATTHIAS D G R IM S A 19"` — home hs-ikmk-18285708
- `hs-ikmk-18285714` [schauenburg_pinneberg] inscription_rev: `"MATTHIAS D G R IM S A 19"` — home hs-ikmk-18285708
- `hs-ikmk-18285924` [schauenburg_pinneberg] inscription_obv: `"ER PRI - ET C H S S"` — home c-023f3975

## H — 89 values on 31 finals

| field | origin | values |
|---|---|---|
| catalog | promoted | 16 |
| diameter_mm_verified | promoted | 2 |
| fraction | promoted | 1 |
| inscription_rev | promoted | 1 |
| mintmaster | promoted | 1 |
| nominal | promoted | 2 |
| ruler | promoted | 1 |
| sources | promoted | 52 |
| verification_note | promoted | 13 |

Examples:

- `c-05eb9690` [danish_norway] sources: `('https://en.numista.com/99194', 'Numista N#99194 — 8 Skilling - Christian IV - Norway')` — home c-19d952ee
- `c-05eb9690` [danish_norway] sources: `('https://numismaster.com/MC_110623', 'NumisMaster')` — home c-19d952ee
- `c-20390e5a` [danish_norway] catalog: `('bruun_lot_no', '12065')`
- `c-20390e5a` [danish_norway] catalog: `('bruun_page', '191')`
- `c-20390e5a` [danish_norway] nominal: `"1 Speciedaler"`
- `c-20390e5a` [danish_norway] verification_note: `{"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af den enkelte mønt udestår stadig; data er `
- `c-4710f90c` [danish_norway] verification_note: `{"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af den enkelte mønt udestår stadig; data er `
- `c-4dda9342` [danish_norway] mintmaster: `"Henning Christopher Meyer, the elder"` — home c-0d78dbf8
- `c-553363f8` [danish_norway] nominal: `"1 Speciedaler"`
- `c-553363f8` [danish_norway] fraction: `"1"`
- `c-553363f8` [danish_norway] inscription_rev: `"DOMINUS - PROVIDEBIT // 1659"` — home c-6b72a94b
- `c-f4db95a5` [danish_realm] ruler: `"Christian IV"` — home c-08c0fcf7
- `c-f4db95a5` [danish_realm] diameter_mm_verified: `true`
- `c-4ac05937` [royal_holstein] diameter_mm_verified: `true`

## H-stale-v1-twin — 1006 values on 78 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 83 |
| diameter_mm | foundation | 4 |
| diameter_mm_verified | foundation | 3 |
| fineness | foundation | 6 |
| fineness_verified | foundation | 78 |
| inscription_obv | foundation | 75 |
| inscription_rev | foundation | 75 |
| metal | foundation | 78 |
| metal_verified | foundation | 3 |
| mint | foundation | 5 |
| mint_verified | foundation | 78 |
| sources | foundation | 83 |
| verification_note | foundation | 78 |
| verified | foundation | 78 |
| weight_rough_g | foundation | 6 |
| weight_rough_verified | foundation | 3 |
| year_first | foundation | 78 |
| year_label | foundation | 78 |
| year_last | foundation | 78 |
| year_ranges | foundation | 36 |

Examples:

- `dk-tid-70750` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-3-rigsbankskilling-1842/?tid=70750', 'ucoin')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] sources: `('https://numismaster.com/MC_66009', 'NumisMaster')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] weight_rough_g: `(1.519, 'numismaster')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] weight_rough_g: `(1.52, 'ucoin')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] fineness: `(0.229, 'numismaster')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] fineness: `(0.229, 'ucoin')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] diameter_mm: `(15.0, 'ucoin')` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] catalog: `('km', '729')` — home c-e40c23a1, decision merge, twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] mint: `"Altona"` — home c-029d697b, twin of c-e40c23a1, recorded removal / retraction
- `dk-tid-70750` [danish_realm] mint: `"Kopenhagen"` — home c-0008432e, twin of c-e40c23a1, recorded removal / retraction
- `dk-tid-70750` [danish_realm] year_first: `1842` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] year_last: `1842` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] year_label: `"1842"` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] metal: `"silver"` — home bruun-14444-ca-1681, twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] metal_verified: `true` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] fineness_verified: `true` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] weight_rough_verified: `true` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] diameter_mm_verified: `true` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] mint_verified: `true` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] verified: `false` — twin of c-e40c23a1
- `dk-tid-70750` [danish_realm] verification_note: `{"da": "Tildeling af møntfod og verifikation af den enkelte mønt mod Hede / Schön / Bruun udestår stadig.", "d` — twin of c-e40c23a1
- `dk-tid-70751` [danish_realm] diameter_mm: `(15.5, 'ucoin')` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] catalog: `('km', 'A730')` — home c-d3ce70e2, decision merge, twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] year_first: `1842` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] year_last: `1842` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] year_label: `"1842"` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] metal: `"silver"` — home bruun-14444-ca-1681, twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] metal_verified: `true` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] fineness_verified: `true` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] weight_rough_verified: `true` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] diameter_mm_verified: `true` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] mint_verified: `true` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] verified: `false` — twin of c-d3ce70e2
- `dk-tid-70751` [danish_realm] verification_note: `{"da": "Tildeling af møntfod og verifikation af den enkelte mønt mod Hede / Schön / Bruun udestår stadig.", "d` — twin of c-d3ce70e2
- `hs-ikmk-18286306` [grafschaft_schaumburg] year_ranges: `1616` — home c-036ff789, twin of c-b1d7ac00
- `hs-ikmk-18286306` [grafschaft_schaumburg] year_ranges: `1617` — home c-036ff789, twin of c-b1d7ac00
- `hs-ikmk-18286306` [grafschaft_schaumburg] inscription_obv: `"ERN-ES D G - CO HO-L S E S - D G"` — home c-b1d7ac00, twin of c-b1d7ac00
- `hs-ikmk-18286306` [grafschaft_schaumburg] inscription_rev: `"MATTHIAS D G RO IM SEM AV"` — home c-0d7e5fae, twin of c-b1d7ac00
- `hs-ikmk-18286307` [grafschaft_schaumburg] inscription_obv: `"ERN-ES D G - CO HOL - S ET [S] - D G"` — twin of c-b1d7ac00
- `hs-ikmk-18286307` [grafschaft_schaumburg] inscription_rev: `"MATTHIAS D G RO IM SEM A"` — twin of c-b1d7ac00

## R-merge-decision-not-applied — 1 values on 1 finals

| field | origin | values |
|---|---|---|
| sources | foundation | 1 |

Examples:

- `dk-tid-163034` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-8-skilling-1608/?tid=163034', 'ucoin')` — home c-1a0d8b18, decision merge

## R-twin — 96 values on 63 finals

| field | origin | values |
|---|---|---|
| sources | foundation | 29 |
| sources | promoted | 67 |

Examples:

- `c-1f98a0d1` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1665-1666/?tid=97366', 'ucoin')` — home c-975cb79f
- `c-39852c62` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1665-1666/?tid=97366', 'ucoin')` — home c-975cb79f
- `dk-tid-55898` [danish_norway] sources: `('https://numismaster.com/MC_86247', 'NumisMaster')` — home c-0c4843f6
- `km-110-chr-iv-1628` [danish_realm] sources: `('https://numismaster.com/MC_65111', 'NumisMaster')` — home c-6b367cf8

## R-orphan — 1390 values on 7 finals

| field | origin | values |
|---|---|---|
| sources | foundation | 3 |
| sources | promoted | 1387 |

Examples:

- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642896', 'KMM 642896 (Inv. FP 34.774)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642897', 'KMM 642897 (Inv. FP 34.773)')`
- `hede-61-4ducat-fr-iii-1663` [danish_realm] sources: `('https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Mar2026_BruunIV_Coins_Catalog.p`
- `hede-61-4ducat-fr-iii-1663` [danish_realm] sources: `('https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf', 'Bruun Part II, lot 13146, p. 81')`

## R-v1-uncovered — 437 values on 261 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 269 |
| sources | foundation | 168 |

Examples:

- `dk-tid-55898` [danish_norway] sources: `('https://www.coinsbook.net/coins/silver-coin-24-skilling-danske-christian-vii-17440', 'coinsbook.net')`
- `dk-tid-55898` [danish_norway] catalog: `('others', 'Brekke# 31–36')`
- `dk-tid-130240` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-2-d-or-1841-1847/?tid=130240', 'ucoin')`
- `dk-tid-79082` [danish_realm] catalog: `('bruun_lot_no', '17135')`

## R-v1-memberless — 103 values on 30 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 29 |
| diameter_mm | foundation | 12 |
| fineness | foundation | 11 |
| sources | foundation | 35 |
| weight_rough_g | foundation | 16 |

Examples:

- `hede-134b-chr-v-1677` [danish_realm] catalog: `('bruun_collection_id', '6905')`
- `hede-134b-chr-v-1677` [danish_realm] catalog: `('bruun_lot_no', '11260')`
- `hede-18-fr-v-1749` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f5h17.htm', 'Hede 18 / danskmoent.dk')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h56.htm', 'Hede 56B / danskmoent.dk')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] weight_rough_g: `(58.464, 'numista')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] fineness: `(0.881, 'numista')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] diameter_mm: `(44.5, 'numista')`
- `km-577-1-fr-v-1755` [danish_realm] weight_rough_g: `(3.65, 'ucoin')`
- `km-577-1-fr-v-1755` [danish_realm] diameter_mm: `(20.5, 'ucoin')`
- `km-750-1-fr-vii-1850` [danish_realm] fineness: `(0.896, 'numismaster')`

## R — 440 values on 203 finals

| field | origin | values |
|---|---|---|
| catalog | promoted | 46 |
| diameter_mm_verified | foundation | 22 |
| fineness_verified | foundation | 41 |
| inscription_obv | foundation | 15 |
| inscription_rev | foundation | 16 |
| metal | foundation | 33 |
| metal_verified | foundation | 15 |
| mint | promoted | 19 |
| mint_verified | foundation | 29 |
| sources | promoted | 97 |
| verification_note | foundation | 20 |
| verified | foundation | 19 |
| weight_rough_verified | foundation | 14 |
| year_first | foundation | 12 |
| year_label | foundation | 12 |
| year_last | foundation | 12 |
| year_verified | foundation | 18 |

Examples:

- `c-5dbe9824` [danish_norway] catalog: `('others', 'Aagaard# 79.4 (61-2/62-9)')`
- `c-825e8d9f` [danish_norway] catalog: `('bruun_lot_no', '14093')`
- `c-8a0bd288` [danish_norway] sources: `('https://www.danskmoent.dk/fr/f3h54.htm', 'Hede 54A / danskmoent.dk')`
- `c-a21e6343` [danish_norway] sources: `('https://en.numista.com/328513', 'Numista N#328513')`
- `c-013899a0` [danish_realm] mint: `"Ulæselig møntmestermærke"`
- `c-0bd34cbf` [danish_realm] mint: `"Hamborg"`
- `dk-tid-163034` [danish_realm] fineness_verified: `true`
- `dk-tid-163034` [danish_realm] diameter_mm_verified: `true`
- `dk-tid-170107` [danish_realm] year_verified: `false`
- `dk-tid-79088` [danish_realm] diameter_mm_verified: `true`
- `dk-tid-79162` [danish_realm] inscription_obv: `"FRIDERICVS V D G DAN NOR V G REX"` — home c-01e29c44
- `dk-tid-79162` [danish_realm] inscription_rev: `"PRUDENTIA E-T CONSTANTIA // 17-64"` — home c-01e29c44
- `dk-tid-94158` [danish_realm] inscription_obv: `"FRIDERICUS V - DEI GRATIA"` — home c-676e2936, decision no_merge
- `dk-tid-94158` [danish_realm] inscription_rev: `"DAN NOR VAN GOT REX"` — home c-676e2936, decision no_merge
- `dk-tid-97089` [danish_realm] year_verified: `false`
- `hede-134b-chr-v-1677` [danish_realm] metal: `"lead"` — home c-1352d07f
- `hede-134b-chr-v-1677` [danish_realm] metal_verified: `true`
- `hede-134b-chr-v-1677` [danish_realm] mint_verified: `true`
- `hede-18-fr-v-1749` [danish_realm] metal: `"gold"` — home c-002b7e6e
- `hede-18-fr-v-1749` [danish_realm] metal_verified: `true`
- `hede-18-fr-v-1749` [danish_realm] fineness_verified: `true`
- `hede-18-fr-v-1749` [danish_realm] mint_verified: `true`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] weight_rough_verified: `true`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] verified: `false`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] verification_note: `{"da": "Data fra NumisMaster-kataloget (Librios), et kommercielt Krause-Mishler-værk. Endnu ikke efterprøvet m`
- `km-395-1-chr-v-1688` [danish_realm] verification_note: `{"da": "Finheden er ikke direkte belagt; overtaget fra den kanoniske møntfodsstandard (Reichsdukatenfuß, anker`
- `km-577-1-fr-v-1755` [danish_realm] weight_rough_verified: `true`
- `km-577-1-fr-v-1755` [danish_realm] verified: `false`
- `hs-ikmk-18286372` [grafschaft_schaumburg] year_first: `1616`
- `hs-ikmk-18286372` [grafschaft_schaumburg] year_last: `1619`
- `hs-ikmk-18286372` [grafschaft_schaumburg] year_label: `"1616-1619"`
- `km-168-1-1752` [hanseatic_lubeck] year_first: `1752`
- `km-168-1-1752` [hanseatic_lubeck] year_last: `1752`
- `km-168-1-1752` [hanseatic_lubeck] year_label: `"1752"`

## FLAG-own-attested-but-removed — 38 values on 30 finals

| field | origin | values |
|---|---|---|
| catalog | foundation | 5 |
| inscription_obv | foundation | 7 |
| inscription_rev | foundation | 6 |
| mintmaster | promoted | 1 |
| nominal | promoted | 5 |
| ruler | promoted | 6 |
| sources | foundation | 6 |
| sources | promoted | 2 |

Examples:

- `c-023a9d78` [danish_realm] sources: `('https://www.danskmoent.dk/c4hede2.htm', 'danskmoent.dk overview c4hede2 (Hede c4h146 — Tiefenseite fehlt)')`
- `c-81cf98ee` [danish_realm] nominal: `"1 Sechsling"`
- `c-9ee87074` [danish_realm] nominal: `"1 Lejrskilling"`
- `dk-tid-130240` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c8h1.htm', 'danskmoent.dk (Hede c8h1A)')`
- `dk-tid-70760` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f6h27.htm', 'danskmoent.dk (Hede f6h27C)')`
- `km-452-chr-v-1699` [danish_realm] catalog: `('hede_volume', 'c5h')`
- `km-795-1-chr-ix-1874` [danish_realm] catalog: `('bruun_lot_no', '17235')`
- `c-10972209` [grafschaft_oldenburg] ruler: `"Anthony Guenther (Anton Guenther) (1603-1667), Emperor Matthias"`
- `c-129b6467` [grafschaft_oldenburg] ruler: `"Anthony Günther (Anton Günther)"`
- `c-ca430328` [royal_holstein] mintmaster: `"Johan Friedrich Freund (IFF)"`
- `hs-ikmk-18285708` [schauenburg_pinneberg] inscription_obv: `"E D G C H - S E S D G"`
- `hs-ikmk-18285708` [schauenburg_pinneberg] inscription_rev: `"MATTHIA[S D] G R IM S A 19"`
- `hs-ikmk-18286248` [schauenburg_pinneberg] inscription_obv: `"E D G H S - E S C D G"`
- `hs-ikmk-18286248` [schauenburg_pinneberg] inscription_rev: `"MAT I D G R I S A 6-18"`
- `c-4225815c` [sweden] sources: `('https://www.danskmoent.dk/hansgals.htm', 'Galster 231 (hg) — danskmoent.dk hansgals.htm')`

## Per-case lists

### H — head-departed finals (31)

- `c-05eb9690` [danish_norway]
- `c-0d78dbf8` [danish_norway]
- `c-108d9a7e` [danish_norway]
- `c-20390e5a` [danish_norway]
- `c-305bc5e0` [danish_norway]
- `c-39e91dbc` [danish_norway]
- `c-462fe1c6` [danish_norway]
- `c-4710f90c` [danish_norway]
- `c-4a435b6d` [danish_norway]
- `c-4dda9342` [danish_norway]
- `c-4fd0819b` [danish_norway]
- `c-547113c3` [danish_norway]
- `c-553363f8` [danish_norway]
- `c-5817298d` [danish_norway]
- `c-64225e47` [danish_norway]
- `c-6c39ea13` [danish_norway]
- `c-6d2607c9` [danish_norway]
- `c-7db17d5e` [danish_norway]
- `c-8aaf1d86` [danish_norway]
- `c-9a306004` [danish_norway]
- `c-aa197a61` [danish_norway]
- `c-d2897afd` [danish_norway]
- `c-da930af4` [danish_norway]
- `c-00a76180` [danish_realm]
- `c-0fd91ba5` [danish_realm]
- `c-3fc7d1dd` [danish_realm]
- `c-44fc0b29` [danish_realm]
- `c-892e7d26` [danish_realm]
- `c-bd92f9e1` [danish_realm]
- `c-f4db95a5` [danish_realm]
- `c-4ac05937` [royal_holstein]

### H-stale-v1-twin — V1 foundations twinning a harvested seed's final (78)

- `dk-tid-70750` [danish_realm] → c-e40c23a1
- `dk-tid-70751` [danish_realm] → c-d3ce70e2
- `dk-tid-79158` [danish_realm] → c-44a9c52f
- `hs-ikmk-18286306` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286307` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286326` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286334` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286342` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286356` [grafschaft_schaumburg] → c-0d7e5fae
- `hs-ikmk-18286362` [grafschaft_schaumburg] → c-0e4c8f67
- `hs-ikmk-18286369` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286375` [grafschaft_schaumburg] → c-b1d7ac00
- `hs-ikmk-18286698` [grafschaft_schaumburg] → c-1c397f3c
- `hs-ikmk-18286700` [grafschaft_schaumburg] → c-7e981b8f
- `hs-ikmk-18286703` [grafschaft_schaumburg] → c-7e981b8f
- `hs-ikmk-18286704` [grafschaft_schaumburg] → c-7e981b8f
- `hs-ikmk-18286705` [grafschaft_schaumburg] → c-f65d6e1c
- `hs-ikmk-18285689` [schauenburg_pinneberg] → c-0aa98956
- `hs-ikmk-18285701` [schauenburg_pinneberg] → c-0aa98956
- `hs-ikmk-18285715` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285716` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285717` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285718` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285719` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285720` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285721` [schauenburg_pinneberg] → hs-ikmk-18285714
- `hs-ikmk-18285722` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285723` [schauenburg_pinneberg] → hs-ikmk-18285708
- `hs-ikmk-18285724` [schauenburg_pinneberg] → hs-ikmk-18285714
- `hs-ikmk-18285774` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285782` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285789` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285792` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285797` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285803` [schauenburg_pinneberg] → hs-ikmk-18285754
- `hs-ikmk-18285805` [schauenburg_pinneberg] → hs-ikmk-18285754
- `hs-ikmk-18285814` [schauenburg_pinneberg] → hs-ikmk-18285754
- `hs-ikmk-18285818` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285911` [schauenburg_pinneberg] → hs-ikmk-18285754
- `hs-ikmk-18285913` [schauenburg_pinneberg] → hs-ikmk-18285773
- `hs-ikmk-18285916` [schauenburg_pinneberg] → hs-ikmk-18285754
- `hs-ikmk-18285931` [schauenburg_pinneberg] → hs-ikmk-18285924
- `hs-ikmk-18286200` [schauenburg_pinneberg] → hs-ikmk-18285924
- `hs-ikmk-18286201` [schauenburg_pinneberg] → c-023f3975
- `hs-ikmk-18286202` [schauenburg_pinneberg] → hs-ikmk-18285918
- `hs-ikmk-18286203` [schauenburg_pinneberg] → c-023f3975
- `hs-ikmk-18286204` [schauenburg_pinneberg] → hs-ikmk-18285918
- `hs-ikmk-18286205` [schauenburg_pinneberg] → hs-ikmk-18285918
- `hs-ikmk-18286206` [schauenburg_pinneberg] → c-023f3975
- `hs-ikmk-18286207` [schauenburg_pinneberg] → hs-ikmk-18285918
- `hs-ikmk-18286209` [schauenburg_pinneberg] → c-7a27d33e
- `hs-ikmk-18286210` [schauenburg_pinneberg] → hs-ikmk-18285918
- `hs-ikmk-18286211` [schauenburg_pinneberg] → c-26c26d4a
- `hs-ikmk-18286284` [schauenburg_pinneberg] → hs-ikmk-18286251
- `hs-ikmk-18286289` [schauenburg_pinneberg] → hs-ikmk-18286248
- `hs-ikmk-18286294` [schauenburg_pinneberg] → hs-ikmk-18286248
- `hs-ikmk-18286660` [schauenburg_pinneberg] → hs-ikmk-18286654
- `hs-ikmk-18286674` [schauenburg_pinneberg] → hs-ikmk-18285918
- `hs-ikmk-18286687` [schauenburg_pinneberg] → hs-ikmk-18286681
- `hs-ikmk-18286694` [schauenburg_pinneberg] → hs-ikmk-18286681
- `hs-ikmk-18286696` [schauenburg_pinneberg] → hs-ikmk-18286681
- `hs-ikmk-18286720` [schauenburg_pinneberg] → hs-ikmk-18286716
- `hs-ikmk-18286724` [schauenburg_pinneberg] → hs-ikmk-18286716
- `hs-ikmk-18286735` [schauenburg_pinneberg] → hs-ikmk-18286716
- `hs-ikmk-18286738` [schauenburg_pinneberg] → hs-ikmk-18286709
- `hs-ikmk-18286755` [schauenburg_pinneberg] → hs-ikmk-18286709
- `hs-ikmk-18286782` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286784` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286786` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286798` [schauenburg_pinneberg] → hs-ikmk-18286759
- `hs-ikmk-18286821` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286826` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286827` [schauenburg_pinneberg] → hs-ikmk-18286763
- `hs-ikmk-18286829` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286831` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286832` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286834` [schauenburg_pinneberg] → hs-ikmk-18286771
- `hs-ikmk-18286836` [schauenburg_pinneberg] → hs-ikmk-18286763

### Memberless foundations with a catalogue candidate (audit_memberless_foundations.py)

- `hede-18-fr-vi-1814` [danish_realm] 16 Skilling Rigsbanktegn Frederik VI. 1814-1814 → `c-4d7fb9c9` «unified-dk-hede-f6h11» [danish_realm] 12 Skilling 1812-1812 metal≠
- `km-104-hede-56b-chr-iv-1627` [danish_realm] 2 Speciedaler Christian IV. 1624-1634 → `c-5d564c17` «unified-dk-hede-c4h56a» [danish_realm] 2 Speciedaler 1624-1634
- `km-395-1-chr-v-1688` [danish_realm] 2 Ducats Christian V. 1688-1688 → `c-ceda4d19` «unified-dk-hede-c5h23ab» [danish_realm] 2 Dukat 1688-1688
- `km-577-1-fr-v-1755` [danish_realm] ½ Skilling Frederik V. 1751-1762 → `c-ae587d80` «unified-dk-hede-f5h17» [danish_realm] 1 Dukat 1749-1749 metal≠
- `km-750-1-fr-vii-1850` [danish_realm] 2 Frederik d'Or Frederik VII. 1850-1863 → `c-04d8e8cd` «unified-dk-hede-f7h1a» [danish_realm] 2 Frederik D'or 1850-1863
- `km-797-1-chr-ix-1875` [danish_realm] 1 Krone Christian IX. 1875-1875 → `c-dbaa3e31` «unified-dk-hede-c9h14a» [danish_realm] 1 Krone 1875-1898 metal≠
- `km-188-karl-fr-1705-v1` [gottorp_duchy] 1 Dukat Karl Friedrich 1705-1705 → `c-cca16ed3` «unified-dk-bruun-14527» [gottorp_duchy] 1 Ducat 1705-1705
- `km-168-1-1752` [hanseatic_lubeck] 48 Schilling Courant Free Hanseatic City of Lübeck 1752-1752 → `c-2c1c8566` «unified-dk-numista-24631» [_unclassified] 48 Schilling (1 Thaler) 1752-1752
- `km-160-1850` [provisional_govt] 1 Dreiling Prov. Regierung 1850-1850 → `c-fc8ace75` «unified-dk-bruun-14479» [gottorp_duchy] 1 Taler 1697-1697 metal≠
- `km-162-1850` [provisional_govt] 1 Sechsling Prov. Regierung 1850-1851 → `c-d6f88e5f` «unified-dk-numista-19525» [royal_holstein] 1 Sechsling 1850-1851
- `km-733-chr-v-1842` [royal_holstein] 16 Rigsbankskilling = 5 Schilling Courant Christian VIII. 1842-1844 → `c-58969558` «unified-dk-hede-c8h6» [danish_realm] 16 Rigsbankskilling 1842-1844
- `km-90-fr-iii-dk-1658` [royal_holstein] 1 Sechsling Frederik III. 1658-1660 → `c-3774a0e1` «unified-ngc-121095» [royal_holstein] 6 Pfennig 1658-1660 metal≠
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] 1 Rigsbankdaler Frederik VI. 1813-1819 → `c-1368e709` «unified-dk-bruun-8026» [danish_realm] 1 Rigsbankdaler 1813-1813
- `km-695-fr-vi-1820` [royal_holstein] 1 Speciedaler Frederik VI. 1820-1839 → `c-2b3d6fa3` «unified-dk-hede-f6h26a» [danish_realm] 1 Speciedaler 1820-1839
- `km-721-chr-v-1841` [royal_holstein] 4 Rigsbankskilling = 1¼ Schilling Courant Christian VIII. 1841-1842 → `c-baf27f19` «unified-dk-hede-c8h8ba» [royal_holstein] 4 Rigsbankskilling 1841-1842 metal≠
- `km-760-fr-vi-1854` [royal_holstein] 1 Rigsdaler Rigsmønt Frederik VII. 1854-1854 → `c-5cab1a08` «unified-dk-hede-f7h8» [royal_holstein] 1 Rigsdaler 1854-1855

### Memberless foundations with no harvested counterpart (V1-only)

- `hede-134b-chr-v-1677` [danish_realm] 4 Skilling Christian V. 1677-1678 refs={'bruun_collection_id': '6905'}
- `hede-18-fr-v-1749` [danish_realm] 2 Ducat Frederik V. 1749-1749 refs={'bruun_collection_id': '7670'}
- `hede-19-fr-vi-1813` [danish_realm] 12 Skilling Rigsbanktegn Frederik VI. 1813-1813 refs={'bruun_collection_id': '8006'}
- `hede-20-fr-vi-1813` [danish_realm] 6 Skilling Rigsbanktegn Frederik VI. 1813-1813 refs={'bruun_collection_id': '8007'}
- `hede-21-fr-vi-1815` [danish_realm] 4 Skilling Rigsbanktegn Frederik VI. 1815-1815 refs={'bruun_collection_id': '8023'}
- `hede-22-fr-vi-1815` [danish_realm] 3 Skilling Rigsbanktegn Frederik VI. 1815-1815 refs={'bruun_collection_id': '8024'}
- `km-x009-fr-iv-1701` [gottorp_duchy] 4 Schilling Friedrich IV. 1701-1702 refs={}
- `hs-ikmk-18286372` [grafschaft_schaumburg] 1 Arendschilling Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1616-1619 refs={}
- `km-x006-1850` [provisional_govt] 1 Schilling Prov. Regierung 1850-1851 refs={}
- `hs-ikmk-18285902` [schauenburg_pinneberg] 1 Doppelschilling Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1620-1620 refs={}
- `hs-ikmk-18285912` [schauenburg_pinneberg] 1 Doppelschilling Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1620-1620 refs={}
- `hs-ikmk-18286208` [schauenburg_pinneberg] 1 Doppelschilling Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1621-1621 refs={}
- `hs-ikmk-18286752` [schauenburg_pinneberg] 1/24 Taler Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1619-1619 refs={}
- `hs-ikmk-18286788` [schauenburg_pinneberg] 1/24 Taler Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1620-1620 refs={}
- `hs-ikmk-18286838` [schauenburg_pinneberg] 1/24 Taler Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1620-1620 refs={}
- `hs-ikmk-18286841` [schauenburg_pinneberg] 1/24 Taler Ernst III. (1601-1622), Graf von Holstein-Schauenburg und Sternberg, Herr zu Gehmen, Reichsfürst 1620-1620 refs={}

### D-promoted nominal forms (final → class)

- `c-20390e5a` [danish_norway]: "1 Speciedaler" → None
- `c-553363f8` [danish_norway]: "1 Speciedaler" → None
- `c-5f490fda` [danish_norway]: "12 Skilling" → None
- `c-8e850e11` [danish_norway]: "16 Skilling" → None
- `c-a80e70cb` [danish_norway]: "6 Mark Rejsedaler" → None
- `c-03dc425f` [danish_realm]: "Gold Off-Metal. 2 Skilling" → None
- `c-26e0d418` [danish_realm]: "1 Ungersk Gylden" → None
- `c-329482ca` [danish_realm]: "1 Goldgulden" → None
- `c-3344ccca` [danish_realm]: "3 Mark" → None
- `c-3412889a` [danish_realm]: "2 Christian d’Or" → None
- `c-34b22a8e` [danish_realm]: "5 Ducat" → None
- `c-471ecb4b` [danish_realm]: "½ Sølvgylden" → None
- `c-51d19d46` [danish_realm]: "1 Goldgulden" → None
- `c-5a4e1f65` [danish_realm]: "2 Dukat" → None
- `c-61c4742c` [danish_realm]: "1 Landskrone" → None
- `c-621e8b09` [danish_realm]: "1 Goldgulden" → None
- `c-666b9ab2` [danish_realm]: "2½ schilling" → None
- `c-6c343eb0` [danish_realm]: "1 Goldgulden" → None
- `c-6e0d4e36` [danish_realm]: "20 Ducat" → None
- `c-7ba89ef7` [danish_realm]: "1 Hvid" → None
- `c-81cf98ee` [danish_realm]: "1 Sechsling" → None
- `c-83fa9e4d` [danish_realm]: "1 Goldgulden" → None
- `c-897476a3` [danish_realm]: "5 Ducat" → None
- `c-913f9b9d` [danish_realm]: "1 Gros" → None
- `c-9ee87074` [danish_realm]: "1 Lejrskilling" → None
- `c-a8790e31` [danish_realm]: "5 Skilling" → None
- `c-b87e0aec` [danish_realm]: "1½ Gulden" → None
- `c-c5990b01` [danish_realm]: "1 Rigsdaler Courant" → None
- `c-cebf5953` [danish_realm]: "18 Mark" → None
- `c-cebfa214` [danish_realm]: "6 Mark" → None
- `c-ea17009c` [danish_realm]: "1 Sterling" → None
- `c-b9718d53` [erzbisthum_bremen_verden]: "1 Thaler" → None
- `c-f29eba71` [erzbisthum_bremen_verden]: "1 Thaler" → None
- `c-0919a070` [fuerstbisthum_luebeck]: "1 Ducat" → None
- `c-17468351` [fuerstbisthum_luebeck]: "1 Ducat" → None
- `c-64fe16d1` [gottorp_duchy]: "1 Sechsling" → None
- `c-83c7f079` [grafschaft_oldenburg]: "4 Pfennige" → None
- `c-0165c2c1` [herzogtum_braunschweig_lueneburg]: "4 Pfennige" → None
- `c-05b0ad76` [herzogtum_braunschweig_lueneburg]: "2½ Thaler" → None
- `c-404c05f3` [herzogtum_braunschweig_lueneburg]: "2 Thaler = 1/7 Cölln. Mark = 3½ Gulden" → None
- `c-5c9e804a` [herzogtum_braunschweig_lueneburg]: "6 Pfennige" → None
- `c-615a9754` [herzogtum_braunschweig_lueneburg]: "1½ Thaler" → None
- `c-a76cd6a6` [herzogtum_braunschweig_lueneburg]: "1 Ducat" → None
- `c-aef8d172` [herzogtum_braunschweig_lueneburg]: "20 Dukaten" → None
- `c-d1456de9` [herzogtum_braunschweig_lueneburg]: "2 Pfennige" → None
- `c-d1fc0c8d` [herzogtum_braunschweig_lueneburg]: "1 Ducat" → None
- `c-dbac239b` [herzogtum_braunschweig_lueneburg]: "1½ Thaler" → None
- `c-f4cb5b46` [herzogtum_braunschweig_lueneburg]: "1 Krone = 1/50 Pfund fein" → None
- `c-122dbd96` [herzogtum_sachsen_lauenburg]: "4 Schilling" → None
- `c-a7d67c55` [herzogtum_sachsen_lauenburg]: "1⁄24 Reichsthaler" → None
- `c-034963a9` [royal_holstein]: "8 Rigsbankskilling" → None
- `c-66488a70` [royal_slesvig]: "1 Lybsk blaffert" → None
- `c-5a36a5a5` [schauenburg_pinneberg]: "1 Thaler" → None
- `c-7da5d3d8` [schauenburg_pinneberg]: "6 Groschen" → None
- `c-8224a343` [schauenburg_pinneberg]: "1½ Thaler" → None
- `c-a208b610` [schauenburg_pinneberg]: "1 Thaler" → None
- `c-ba72e562` [schauenburg_pinneberg]: "2½ Thalers" → None
- `c-d826865b` [schauenburg_pinneberg]: "12 Groschen" → None
- `c-507f7d36` [sweden]: "halv Ørtug" → None

### Curator decisions touched

- merge decision not applied: `dk-tid-163034` [danish_realm] sources `('https://en.ucoin.net/coin/denmark-8-skilling-1608/?tid=163034', 'ucoin')` — home c-1a0d8b18
- no_merge confirms: `c-5a55f683` [_unclassified] sources `('https://ikmk.smb.museum/object?id=18286029', 'IKMK Berlin 18286029')` — home c-642b68f4
- no_merge confirms: `c-5a55f683` [_unclassified] sources `('https://ikmk.smb.museum/object?id=18286030', 'IKMK Berlin 18286030')` — home c-88793357
- no_merge confirms: `c-0c2ee0b8` [danish_norway] sources `('https://en.ucoin.net/coin/norway-8-skilling-1727-1730/?tid=145800', 'ucoin')` — home c-02b16a70
- no_merge confirms: `c-302a2460` [danish_realm] sources `('https://en.numista.com/142853', 'Numista N#142853 — 1 Skilling Dansk - Christian IV')` — home c-bd92f9e1
- no_merge confirms: `c-302a2460` [danish_realm] sources `('https://en.ucoin.net/coin/denmark-1-skilling-1619/?tid=163000', 'ucoin')` — home c-bd92f9e1
- no_merge confirms: `c-302a2460` [danish_realm] sources `('https://numismaster.com/MC_65012', 'NumisMaster')` — home c-bd92f9e1
- no_merge confirms: `c-302a2460` [danish_realm] sources `('https://numismaster.com/MC_65013', 'NumisMaster')` — home c-bd92f9e1
- no_merge confirms: `c-b9ebec1b` [danish_realm] sources `('', 'KMM 402840 (Inv. FP 3594.2)')` — home c-731a902b
- no_merge confirms: `c-bc13c967` [danish_realm] sources `('https://en.ucoin.net/coin/denmark-8-skilling-1606-1609/?tid=163031', 'ucoin')` — home c-1a0d8b18
- no_merge confirms: `c-bc13c967` [danish_realm] sources `('https://en.ucoin.net/coin/denmark-8-skilling-1608/?tid=163034', 'ucoin')` — home c-1a0d8b18
- no_merge confirms: `c-bc13c967` [danish_realm] sources `('https://numismaster.com/MC_65115', 'NumisMaster')` — home c-1a0d8b18
- no_merge confirms: `c-f120c3c6` [danish_realm] sources `('https://numismaster.com/MC_65882', 'NumisMaster')` — home c-1b1c71b8
- no_merge confirms: `c-f39a0a71` [danish_realm] sources `('https://numismaster.com/MC_65788', 'NumisMaster')` — home c-516d5bd3
- no_merge confirms: `c-f39a0a71` [danish_realm] sources `('https://www.ngccoin.com/price-guide/world/denmark-ducat-km-413-1691-1692-cuid-1050270-du` — home c-516d5bd3
- no_merge confirms: `c-1e3ebd4b` [herzogtum_braunschweig_lueneburg] sources `('https://ikmk.smb.museum/object?id=18296479', 'IKMK Berlin 18296479')` — home c-eb22d0d3
- no_merge confirms: `c-294bed2e` [herzogtum_braunschweig_lueneburg] sources `('https://ikmk.smb.museum/object?id=18296479', 'IKMK Berlin 18296479')` — home c-eb22d0d3
- no_merge confirms: `c-2a9ecadd` [royal_holstein] sources `('https://numismaster.com/MC_145357', 'NumisMaster')` — home c-b20deed6
- no_merge confirms: `c-6d39d27d` [schauenburg_pinneberg] sources `('https://en.numista.com/137419', 'Numista N#137419 — 1 Thaler - Ernest III (Biblischer Ta` — home km-137419-ernst-1601
- no_merge confirms: `c-6d39d27d` [schauenburg_pinneberg] sources `('https://en.numista.com/278300', 'Numista N#278300 — 1 Thaler - Ernest III')` — home km-278300-ernst-1620
- no_merge confirms: `c-6d39d27d` [schauenburg_pinneberg] catalog `('others', 'Weinm# 152')` — home km-137419-ernst-1601
