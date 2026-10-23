# Finals: `main` vs the rebuild — decision groups (denmark page)

Scope: the entities the `denmark` page consumes — `christian_ii_reconquest`, `christian_ii_supporters`, `danish_norway`, `danish_realm`, `glucksburg_duchy`, `gottorp_duchy`, `norburg_plon_duchy`, `norby_gotland`, `royal_holstein`, `royal_slesvig`, `sonderburg_duchy` (curator 2026-10-23: only the finals a page renders matter; the rest are unprocessed). A page's year window on an entity is not applied here.

Every row is one value that differs between the finals at `main` and the finals rebuilt on this branch (`--no-self-union`, full chain). «removed» = on the base, not on the rebuild; «added» = the reverse. The group letter says what the difference means for the finals' legal form: **A** nothing to decide · **B** garbage on the base · **C** keep, needs a surface · **D** V1 record, deferred · **E** review.

Values: 4954 on 2019 finals; coins gone 1, new 0. Finals that lose `metal` with nothing in its place: 42 (D2-v1-memberless 20, D6-v1-values-on-promoted 18, D1-v1-twin 3, D4-v1-own-record 1).

| class | values | finals |
|---|---|---|
| A | 1336 | 1293 |
| B | 2590 | 560 |
| C | 150 | 109 |
| D | 773 | 398 |
| E | 105 | 60 |

| group | class | values | finals | entities |
|---|---|---|---|---|
| A1-note-da-added | A | 29 | 29 | danish_realm 13, danish_norway 11, royal_holstein 5 |
| A2-ruler-canonical | A | 1194 | 1194 | danish_realm 858, danish_norway 246, royal_holstein 53, royal_slesvig 37 |
| A4-relabel | A | 107 | 81 | danish_realm 38, royal_holstein 32, sonderburg_duchy 17, danish_norway 15 … |
| A5-gain | A | 6 | 6 | danish_realm 4, christian_ii_supporters 1, royal_holstein 1 |
| B1-excluded-stub-citations | B | 1390 | 7 | danish_realm 1229, danish_norway 161 |
| B2-moved-to-another-final | B | 785 | 364 | danish_realm 527, royal_holstein 118, danish_norway 90, gottorp_duchy 26 … |
| B3-recorded-removal | B | 42 | 40 | danish_realm 22, royal_holstein 12, gottorp_duchy 4, norburg_plon_duchy 2 … |
| B4-mintmaster-place | B | 15 | 15 | royal_holstein 9, gottorp_duchy 4, danish_realm 2 |
| B5-covered-other-form | B | 40 | 24 | danish_realm 20, royal_holstein 19, danish_norway 1 |
| B6-flag-class-claim | B | 213 | 166 | danish_realm 176, danish_norway 23, royal_holstein 5, christian_ii_supporters 3 … |
| D6-v1-values-on-promoted | D | 61 | 58 | danish_realm 56, danish_norway 4, gottorp_duchy 1 |
| B8-bruun-anchor | B | 23 | 20 | danish_realm 17, royal_holstein 5, danish_norway 1 |
| B9-note-template-swap | B | 82 | 82 | danish_realm 63, royal_holstein 16, royal_slesvig 3 |
| C0-hand-edit | C | 45 | 25 | danish_realm 29, royal_holstein 14, danish_norway 2 |
| C1-nominal-form | C | 29 | 29 | danish_realm 24, danish_norway 3, gottorp_duchy 1, royal_holstein 1 |
| C2-ruler-regression | C | 7 | 7 | danish_norway 3, danish_realm 3, royal_holstein 1 |
| C3-ruler-lost | C | 14 | 14 | danish_realm 13, danish_norway 1 |
| C4-note-da-lost | C | 5 | 5 | danish_realm 4, danish_norway 1 |
| C5-note-curated-text | C | 5 | 5 | danish_realm 5 |
| C6-mintmaster-name | C | 6 | 6 | danish_realm 3, royal_holstein 3 |
| C7-hand-deletion-returns | C | 39 | 38 | danish_realm 33, danish_norway 3, royal_holstein 3 |
| D1-v1-twin | D | 117 | 51 | danish_realm 84, danish_norway 15, royal_holstein 15, gottorp_duchy 2 … |
| D2-v1-memberless | D | 132 | 20 | danish_realm 64, royal_holstein 59, gottorp_duchy 9 |
| D3-v1-uncovered | D | 341 | 201 | danish_realm 147, gottorp_duchy 111, sonderburg_duchy 33, royal_holstein 32 … |
| D4-v1-own-record | D | 13 | 12 | danish_realm 13 |
| D5-v1-citations-on-promoted | D | 109 | 75 | royal_holstein 60, danish_realm 31, gottorp_duchy 10, danish_norway 5 … |
| E1-ruler-other | E | 14 | 14 | gottorp_duchy 8, danish_realm 4, danish_norway 1, sonderburg_duchy 1 |
| E2-head-departed | E | 71 | 31 | danish_norway 52, danish_realm 12, royal_holstein 7 |
| E3-own-attested-removed | E | 13 | 8 | danish_realm 12, royal_holstein 1 |
| E4-residual | E | 6 | 6 | danish_realm 3, danish_norway 2, royal_holstein 1 |
| E5-stage-N-automerge | E | 1 | 1 | danish_realm 1 |

## A1-note-da-added — verification_note: the class adds the Danish version

**A** · 29 values on 29 finals. **Legal form:** Nothing to decide — the final's stored note lacked `da`, the class note has it; de/en/uk identical.

| field | origin | direction | values |
|---|---|---|---|
| verification_note | promoted | removed | 29 |

Per entity: danish_realm 13, danish_norway 11, royal_holstein 5.

- `c-020598dd` [danish_norway] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-08589f11` [danish_norway] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-19d952ee` [danish_norway] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-1f7cfe30` [danish_norway] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-825e8d9f` [danish_norway] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-abd4044c` [danish_norway] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-bf63f998` [danish_norway] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-c2f598fa` [danish_norway] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-e252167f` [danish_norway] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-ecc6c66d` [danish_norway] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-f04c87b1` [danish_norway] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-0a59bca7` [danish_realm] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-2431dec5` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-4f9c4838` [danish_realm] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-5ed5a379` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-6b367cf8` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-70c207e5` [danish_realm] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-7345dc86` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-8ad58f76` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-a79e2241` [danish_realm] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-ab8a330a` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-b3e4a39a` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-da79b58d` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-e73bb2e5` [danish_realm] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-680c85ac` [royal_holstein] verification_note: `{"de": "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation stehen noch aus; D` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d
- `c-6e56a95f` [royal_holstein] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-758acbdb` [royal_holstein] verification_note: `{"de": "Nur die Übersichtsreihe von c4hede2.htm belegt diesen Eintrag; die Hede-Tiefenseit` — → {"da": "Kun oversigtsrækken hos c4hede2.htm dokumenterer denne post; H
- `c-c50a7d96` [royal_holstein] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e
- `c-f6bef30d` [royal_holstein] verification_note: `{"de": "NGC-Seed: World Coin Price Guide, Krause-Mishler-basiert, Nachfolger des eingestel` — → {"da": "NGC-seed: World Coin Price Guide, baseret på Krause-Mishler, e

## A2-ruler-canonical — ruler: stage N canonical «Name Roman.»

**A** · 1194 values on 1194 finals. **Legal form:** Nothing to decide — the seed-level canonicalisation (stage N) reaching the final.

| field | origin | direction | values |
|---|---|---|---|
| ruler | promoted | removed | 1194 |

Per entity: danish_realm 858, danish_norway 246, royal_holstein 53, royal_slesvig 37.

Examples:

- `c-009b2222` [danish_norway] ruler: `"Frederik 3"` — → "Frederik III."
- `c-013f03dd` [danish_norway] ruler: `"Frederik 4"` — → "Frederik IV."
- `c-0285dbed` [danish_norway] ruler: `"Christian 5"` — → "Christian V."

## A4-relabel — sources: the same url under another ref text

**A** · 107 values on 81 finals. **Legal form:** Nothing to decide — no citation lost; the class's ref text is the canonical one.

| field | origin | direction | values |
|---|---|---|---|
| sources | foundation | removed | 65 |
| sources | promoted | removed | 42 |

Per entity: danish_realm 38, royal_holstein 32, sonderburg_duchy 17, danish_norway 15, gottorp_duchy 5.

Examples:

- `c-00c2def8` [danish_norway] sources: `('https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf', 'Bruun Part II`
- `c-0a210ec7` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc5h56.htm', 'danskmoent.dk (Hede nc5h56B)')` — → ('https://www.danskmoent.dk/norge/nc5h56.htm', 'danskmoent.dk (Hede nc
- `c-2d8327a8` [danish_norway] sources: `('https://www.danskmoent.dk/norge/hansGej.htm', 'danskmoent.dk (norge/hansGej) — Hans Rhin` — → ('https://www.danskmoent.dk/norge/hansGej.htm', 'danskmoent.dk norge_h
- `dk-tid-55898` [danish_norway] sources: `('https://en.numista.com/55898', 'Numista')` — → ('https://en.numista.com/55898', 'Numista N#55898 — 24 Skilling - Chri; edit 214f991,e210ed6
- `dk-tid-55898` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc7h12.htm', 'danskmoent.dk (Hede nc7h12)')` — → ('https://en.numista.com/55898', 'Numista N#55898 — 24 Skilling - Chri; edit 577ea14
- `dk-tid-163044` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h77.htm', 'danskmoent.dk (Hede c4h77C)')` — → ('https://www.danskmoent.dk/chr/c4h77.htm', 'danskmoent.dk (Hede c4h77

## A5-gain — values the rebuild adds with no removed counterpart

**A** · 6 values on 6 finals. **Legal form:** Nothing to decide — class data the self-union never let through.

| field | origin | direction | values |
|---|---|---|---|
| issuing_entity | promoted | added | 1 |
| mint | promoted | added | 1 |
| year_verified | promoted | added | 4 |

Per entity: danish_realm 4, christian_ii_supporters 1, royal_holstein 1.

- `c-ddefc984` [christian_ii_supporters] mint: `"Kopenhagen"`
- `c-8f3b9eaf` [danish_realm] year_verified: `false`
- `c-cc6867e5` [danish_realm] year_verified: `false`
- `c-ea17009c` [danish_realm] year_verified: `false`
- `c-f157b78e` [danish_realm] year_verified: `false`
- `c-6d4898b8` [royal_holstein] issuing_entity: `"danish_realm"`

## B1-excluded-stub-citations — citations of excluded KMM stubs (scope member)

**B** · 1390 values on 7 finals. **Legal form:** Garbage on the base — the curator excluded these undocumented stubs 2026-10-16/20; only the self-union kept their citations on the documented coin's final.

| field | origin | direction | values |
|---|---|---|---|
| sources | foundation | removed | 3 |
| sources | promoted | removed | 1387 |

Per entity: danish_realm 1229, danish_norway 161.

- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642896', 'KMM 642896 (Inv. FP 34.774)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642897', 'KMM 642897 (Inv. FP 34.773)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642898', 'KMM 642898 (Inv. FP 34.772)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642899', 'KMM 642899 (Inv. FP 34.771)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642900', 'KMM 642900 (Inv. FP 34.770)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642901', 'KMM 642901 (Inv. FP 34.769)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642902', 'KMM 642902 (Inv. FP 34.768)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642903', 'KMM 642903 (Inv. FP 34.767)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642904', 'KMM 642904 (Inv. FP 34.766)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642905', 'KMM 642905 (Inv. FP 34.765)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642906', 'KMM 642906 (Inv. FP 34.764)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642907', 'KMM 642907 (Inv. FP 34.763)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642908', 'KMM 642908 (Inv. FP 34.762)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642909', 'KMM 642909 (Inv. FP 34.761)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642910', 'KMM 642910 (Inv. FP 34.760)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642911', 'KMM 642911 (Inv. FP 34.759)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642912', 'KMM 642912 (Inv. FP 34.758)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642913', 'KMM 642913 (Inv. FP 34.757)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642914', 'KMM 642914 (Inv. FP 34.756)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642915', 'KMM 642915 (Inv. FP 34.755)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642916', 'KMM 642916 (Inv. FP 34.754)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642917', 'KMM 642917 (Inv. FP 34.753)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642918', 'KMM 642918 (Inv. FP 34.752)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642919', 'KMM 642919 (Inv. FP 34.751)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642920', 'KMM 642920 (Inv. FP 34.750)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642921', 'KMM 642921 (Inv. FP 34.749)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642922', 'KMM 642922 (Inv. FP 34.748)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642923', 'KMM 642923 (Inv. FP 34.747)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642924', 'KMM 642924 (Inv. FP 34.746)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642925', 'KMM 642925 (Inv. FP 34.745)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642926', 'KMM 642926 (Inv. FP 34.744)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642927', 'KMM 642927 (Inv. FP 34.743)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642928', 'KMM 642928 (Inv. FP 34.742)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642929', 'KMM 642929 (Inv. FP 34.741)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642930', 'KMM 642930 (Inv. FP 34.740)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642931', 'KMM 642931 (Inv. FP 34.739)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642932', 'KMM 642932 (Inv. FP 34.738)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642933', 'KMM 642933 (Inv. FP 34.737)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642934', 'KMM 642934 (Inv. FP 34.736)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642935', 'KMM 642935 (Inv. FP 34.735)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642936', 'KMM 642936 (Inv. FP 34.734)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642937', 'KMM 642937 (Inv. FP 34.733)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642938', 'KMM 642938 (Inv. FP 34.732)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642939', 'KMM 642939 (Inv. FP 34.731)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642940', 'KMM 642940 (Inv. FP 34.730)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642941', 'KMM 642941 (Inv. FP 34.729)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642942', 'KMM 642942 (Inv. FP 34.728)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642943', 'KMM 642943 (Inv. FP 34.727)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642944', 'KMM 642944 (Inv. FP 34.726)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642945', 'KMM 642945 (Inv. FP 34.725)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642946', 'KMM 642946 (Inv. FP 34.724)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642947', 'KMM 642947 (Inv. FP 34.723)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642948', 'KMM 642948 (Inv. FP 34.722)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642949', 'KMM 642949 (Inv. FP 34.721)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642950', 'KMM 642950 (Inv. FP 34.720)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642951', 'KMM 642951 (Inv. FP 34.719)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642952', 'KMM 642952 (Inv. FP 34.718)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642953', 'KMM 642953 (Inv. FP 34.717)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642954', 'KMM 642954 (Inv. FP 34.716)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642955', 'KMM 642955 (Inv. FP 34.715)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642956', 'KMM 642956 (Inv. FP 34.714)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642957', 'KMM 642957 (Inv. FP 34.713)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642958', 'KMM 642958 (Inv. FP 34.712)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642959', 'KMM 642959 (Inv. FP 34.711)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642960', 'KMM 642960 (Inv. FP 34.710)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642961', 'KMM 642961 (Inv. FP 34.709)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642962', 'KMM 642962 (Inv. FP 34.708)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642963', 'KMM 642963 (Inv. FP 34.707)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642964', 'KMM 642964 (Inv. FP 34.706)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642965', 'KMM 642965 (Inv. FP 34.705)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642966', 'KMM 642966 (Inv. FP 34.704)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642967', 'KMM 642967 (Inv. FP 34.703)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642968', 'KMM 642968 (Inv. FP 34.702)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642969', 'KMM 642969 (Inv. FP 34.701)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642970', 'KMM 642970 (Inv. FP 34.700)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642971', 'KMM 642971 (Inv. FP 34.699)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642972', 'KMM 642972 (Inv. FP 34.698)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642973', 'KMM 642973 (Inv. FP 34.697)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642974', 'KMM 642974 (Inv. FP 34.696)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642975', 'KMM 642975 (Inv. FP 34.695)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642976', 'KMM 642976 (Inv. FP 34.694)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642977', 'KMM 642977 (Inv. FP 34.693)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642978', 'KMM 642978 (Inv. FP 34.692)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642979', 'KMM 642979 (Inv. FP 34.691)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642980', 'KMM 642980 (Inv. FP 34.690)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642981', 'KMM 642981 (Inv. FP 34.689)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642982', 'KMM 642982 (Inv. FP 34.688)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642983', 'KMM 642983 (Inv. FP 34.687)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642984', 'KMM 642984 (Inv. FP 34.686)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642985', 'KMM 642985 (Inv. FP 34.685)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642986', 'KMM 642986 (Inv. FP 34.684)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642987', 'KMM 642987 (Inv. FP 34.683)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642988', 'KMM 642988 (Inv. FP 34.682)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642989', 'KMM 642989 (Inv. FP 34.681)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642990', 'KMM 642990 (Inv. FP 34.680)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642991', 'KMM 642991 (Inv. FP 34.679)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642992', 'KMM 642992 (Inv. FP 34.678)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642993', 'KMM 642993 (Inv. FP 34.677)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642994', 'KMM 642994 (Inv. FP 34.676)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642995', 'KMM 642995 (Inv. FP 34.675)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642996', 'KMM 642996 (Inv. FP 34.674)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642997', 'KMM 642997 (Inv. FP 34.673)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642998', 'KMM 642998 (Inv. FP 34.672)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/642999', 'KMM 642999 (Inv. FP 34.671)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643000', 'KMM 643000 (Inv. FP 34.670)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643001', 'KMM 643001 (Inv. FP 34.669)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643002', 'KMM 643002 (Inv. FP 34.668)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643003', 'KMM 643003 (Inv. FP 34.667)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643004', 'KMM 643004 (Inv. FP 34.666)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643005', 'KMM 643005 (Inv. FP 34.665)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643006', 'KMM 643006 (Inv. FP 34.664)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643007', 'KMM 643007 (Inv. FP 34.663)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643008', 'KMM 643008 (Inv. FP 34.662)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643009', 'KMM 643009 (Inv. FP 34.661)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643010', 'KMM 643010 (Inv. FP 34.660)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643011', 'KMM 643011 (Inv. FP 34.659)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643012', 'KMM 643012 (Inv. FP 34.658)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643013', 'KMM 643013 (Inv. FP 34.657)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643014', 'KMM 643014 (Inv. FP 34.656)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643015', 'KMM 643015 (Inv. FP 34.655)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643016', 'KMM 643016 (Inv. FP 34.654)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643017', 'KMM 643017 (Inv. FP 34.653)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643018', 'KMM 643018 (Inv. FP 34.652)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643019', 'KMM 643019 (Inv. FP 34.651)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643020', 'KMM 643020 (Inv. FP 34.650)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643021', 'KMM 643021 (Inv. FP 34.649)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643022', 'KMM 643022 (Inv. FP 34.648)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643023', 'KMM 643023 (Inv. FP 34.647)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643024', 'KMM 643024 (Inv. FP 34.646)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643025', 'KMM 643025 (Inv. FP 34.645)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643026', 'KMM 643026 (Inv. FP 34.644)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643027', 'KMM 643027 (Inv. FP 34.643)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643028', 'KMM 643028 (Inv. FP 34.642)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643029', 'KMM 643029 (Inv. FP 34.641)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643030', 'KMM 643030 (Inv. FP 34.640)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643031', 'KMM 643031 (Inv. FP 34.639)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643032', 'KMM 643032 (Inv. FP 34.638)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643033', 'KMM 643033 (Inv. FP 34.637)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643034', 'KMM 643034 (Inv. FP 34.636)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643035', 'KMM 643035 (Inv. FP 34.635)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643036', 'KMM 643036 (Inv. FP 34.634)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643037', 'KMM 643037 (Inv. FP 34.633)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643038', 'KMM 643038 (Inv. FP 34.632)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643039', 'KMM 643039 (Inv. FP 34.631)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643040', 'KMM 643040 (Inv. FP 34.630)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643041', 'KMM 643041 (Inv. FP 34.629)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643042', 'KMM 643042 (Inv. FP 34.628)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643043', 'KMM 643043 (Inv. FP 34.627)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643044', 'KMM 643044 (Inv. FP 34.626)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643045', 'KMM 643045 (Inv. FP 34.625)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643046', 'KMM 643046 (Inv. FP 34.624)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643047', 'KMM 643047 (Inv. FP 34.623)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643048', 'KMM 643048 (Inv. FP 34.622)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643049', 'KMM 643049 (Inv. FP 34.621)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643050', 'KMM 643050 (Inv. FP 34.620)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643051', 'KMM 643051 (Inv. FP 34.619)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643052', 'KMM 643052 (Inv. FP 34.618)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643053', 'KMM 643053 (Inv. FP 34.617)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643054', 'KMM 643054 (Inv. FP 34.616)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643055', 'KMM 643055 (Inv. FP 34.615)')`
- `c-afd707d6` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/643056', 'KMM 643056 (Inv. FP 34.614)')`
- `c-302a2460` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h118.htm', 'danskmoent.dk (Hede c4h118A)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/371867', 'KMM 371867 (Inv. FP 10474.11)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/533323', 'KMM 533323 (Inv. FP 10743.9)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642896', 'KMM 642896 (Inv. FP 34.774)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642897', 'KMM 642897 (Inv. FP 34.773)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642898', 'KMM 642898 (Inv. FP 34.772)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642899', 'KMM 642899 (Inv. FP 34.771)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642900', 'KMM 642900 (Inv. FP 34.770)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642901', 'KMM 642901 (Inv. FP 34.769)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642902', 'KMM 642902 (Inv. FP 34.768)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642903', 'KMM 642903 (Inv. FP 34.767)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642904', 'KMM 642904 (Inv. FP 34.766)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642905', 'KMM 642905 (Inv. FP 34.765)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642906', 'KMM 642906 (Inv. FP 34.764)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642907', 'KMM 642907 (Inv. FP 34.763)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642908', 'KMM 642908 (Inv. FP 34.762)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642909', 'KMM 642909 (Inv. FP 34.761)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642910', 'KMM 642910 (Inv. FP 34.760)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642911', 'KMM 642911 (Inv. FP 34.759)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642912', 'KMM 642912 (Inv. FP 34.758)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642913', 'KMM 642913 (Inv. FP 34.757)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642914', 'KMM 642914 (Inv. FP 34.756)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642915', 'KMM 642915 (Inv. FP 34.755)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642916', 'KMM 642916 (Inv. FP 34.754)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642917', 'KMM 642917 (Inv. FP 34.753)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642918', 'KMM 642918 (Inv. FP 34.752)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642919', 'KMM 642919 (Inv. FP 34.751)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642920', 'KMM 642920 (Inv. FP 34.750)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642921', 'KMM 642921 (Inv. FP 34.749)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642922', 'KMM 642922 (Inv. FP 34.748)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642923', 'KMM 642923 (Inv. FP 34.747)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642924', 'KMM 642924 (Inv. FP 34.746)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642925', 'KMM 642925 (Inv. FP 34.745)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642926', 'KMM 642926 (Inv. FP 34.744)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642927', 'KMM 642927 (Inv. FP 34.743)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642928', 'KMM 642928 (Inv. FP 34.742)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642929', 'KMM 642929 (Inv. FP 34.741)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642930', 'KMM 642930 (Inv. FP 34.740)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642931', 'KMM 642931 (Inv. FP 34.739)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642932', 'KMM 642932 (Inv. FP 34.738)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642933', 'KMM 642933 (Inv. FP 34.737)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642934', 'KMM 642934 (Inv. FP 34.736)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642935', 'KMM 642935 (Inv. FP 34.735)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642936', 'KMM 642936 (Inv. FP 34.734)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642937', 'KMM 642937 (Inv. FP 34.733)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642938', 'KMM 642938 (Inv. FP 34.732)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642939', 'KMM 642939 (Inv. FP 34.731)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642940', 'KMM 642940 (Inv. FP 34.730)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642941', 'KMM 642941 (Inv. FP 34.729)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642942', 'KMM 642942 (Inv. FP 34.728)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642943', 'KMM 642943 (Inv. FP 34.727)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642944', 'KMM 642944 (Inv. FP 34.726)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642945', 'KMM 642945 (Inv. FP 34.725)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642946', 'KMM 642946 (Inv. FP 34.724)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642947', 'KMM 642947 (Inv. FP 34.723)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642948', 'KMM 642948 (Inv. FP 34.722)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642949', 'KMM 642949 (Inv. FP 34.721)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642950', 'KMM 642950 (Inv. FP 34.720)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642951', 'KMM 642951 (Inv. FP 34.719)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642952', 'KMM 642952 (Inv. FP 34.718)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642953', 'KMM 642953 (Inv. FP 34.717)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642954', 'KMM 642954 (Inv. FP 34.716)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642955', 'KMM 642955 (Inv. FP 34.715)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642956', 'KMM 642956 (Inv. FP 34.714)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642957', 'KMM 642957 (Inv. FP 34.713)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642958', 'KMM 642958 (Inv. FP 34.712)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642959', 'KMM 642959 (Inv. FP 34.711)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642960', 'KMM 642960 (Inv. FP 34.710)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642961', 'KMM 642961 (Inv. FP 34.709)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642962', 'KMM 642962 (Inv. FP 34.708)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642963', 'KMM 642963 (Inv. FP 34.707)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642964', 'KMM 642964 (Inv. FP 34.706)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642965', 'KMM 642965 (Inv. FP 34.705)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642966', 'KMM 642966 (Inv. FP 34.704)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642967', 'KMM 642967 (Inv. FP 34.703)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642968', 'KMM 642968 (Inv. FP 34.702)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642969', 'KMM 642969 (Inv. FP 34.701)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642970', 'KMM 642970 (Inv. FP 34.700)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642971', 'KMM 642971 (Inv. FP 34.699)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642972', 'KMM 642972 (Inv. FP 34.698)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642973', 'KMM 642973 (Inv. FP 34.697)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642974', 'KMM 642974 (Inv. FP 34.696)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642975', 'KMM 642975 (Inv. FP 34.695)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642976', 'KMM 642976 (Inv. FP 34.694)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642977', 'KMM 642977 (Inv. FP 34.693)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642978', 'KMM 642978 (Inv. FP 34.692)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642979', 'KMM 642979 (Inv. FP 34.691)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642980', 'KMM 642980 (Inv. FP 34.690)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642981', 'KMM 642981 (Inv. FP 34.689)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642982', 'KMM 642982 (Inv. FP 34.688)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642983', 'KMM 642983 (Inv. FP 34.687)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642984', 'KMM 642984 (Inv. FP 34.686)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642985', 'KMM 642985 (Inv. FP 34.685)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642986', 'KMM 642986 (Inv. FP 34.684)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642987', 'KMM 642987 (Inv. FP 34.683)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642988', 'KMM 642988 (Inv. FP 34.682)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642989', 'KMM 642989 (Inv. FP 34.681)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642990', 'KMM 642990 (Inv. FP 34.680)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642991', 'KMM 642991 (Inv. FP 34.679)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642992', 'KMM 642992 (Inv. FP 34.678)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642993', 'KMM 642993 (Inv. FP 34.677)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642994', 'KMM 642994 (Inv. FP 34.676)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642995', 'KMM 642995 (Inv. FP 34.675)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642996', 'KMM 642996 (Inv. FP 34.674)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642997', 'KMM 642997 (Inv. FP 34.673)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642998', 'KMM 642998 (Inv. FP 34.672)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/642999', 'KMM 642999 (Inv. FP 34.671)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643000', 'KMM 643000 (Inv. FP 34.670)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643001', 'KMM 643001 (Inv. FP 34.669)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643002', 'KMM 643002 (Inv. FP 34.668)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643003', 'KMM 643003 (Inv. FP 34.667)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643004', 'KMM 643004 (Inv. FP 34.666)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643005', 'KMM 643005 (Inv. FP 34.665)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643006', 'KMM 643006 (Inv. FP 34.664)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643007', 'KMM 643007 (Inv. FP 34.663)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643008', 'KMM 643008 (Inv. FP 34.662)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643009', 'KMM 643009 (Inv. FP 34.661)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643010', 'KMM 643010 (Inv. FP 34.660)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643011', 'KMM 643011 (Inv. FP 34.659)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643012', 'KMM 643012 (Inv. FP 34.658)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643013', 'KMM 643013 (Inv. FP 34.657)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643014', 'KMM 643014 (Inv. FP 34.656)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643015', 'KMM 643015 (Inv. FP 34.655)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643016', 'KMM 643016 (Inv. FP 34.654)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643017', 'KMM 643017 (Inv. FP 34.653)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643018', 'KMM 643018 (Inv. FP 34.652)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643019', 'KMM 643019 (Inv. FP 34.651)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643020', 'KMM 643020 (Inv. FP 34.650)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643021', 'KMM 643021 (Inv. FP 34.649)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643022', 'KMM 643022 (Inv. FP 34.648)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643023', 'KMM 643023 (Inv. FP 34.647)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643024', 'KMM 643024 (Inv. FP 34.646)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643025', 'KMM 643025 (Inv. FP 34.645)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643026', 'KMM 643026 (Inv. FP 34.644)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643027', 'KMM 643027 (Inv. FP 34.643)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643028', 'KMM 643028 (Inv. FP 34.642)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643029', 'KMM 643029 (Inv. FP 34.641)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643030', 'KMM 643030 (Inv. FP 34.640)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643031', 'KMM 643031 (Inv. FP 34.639)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643032', 'KMM 643032 (Inv. FP 34.638)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643033', 'KMM 643033 (Inv. FP 34.637)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643034', 'KMM 643034 (Inv. FP 34.636)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643035', 'KMM 643035 (Inv. FP 34.635)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643036', 'KMM 643036 (Inv. FP 34.634)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643037', 'KMM 643037 (Inv. FP 34.633)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643038', 'KMM 643038 (Inv. FP 34.632)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643039', 'KMM 643039 (Inv. FP 34.631)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643040', 'KMM 643040 (Inv. FP 34.630)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643041', 'KMM 643041 (Inv. FP 34.629)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643042', 'KMM 643042 (Inv. FP 34.628)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643043', 'KMM 643043 (Inv. FP 34.627)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643044', 'KMM 643044 (Inv. FP 34.626)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643045', 'KMM 643045 (Inv. FP 34.625)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643046', 'KMM 643046 (Inv. FP 34.624)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643047', 'KMM 643047 (Inv. FP 34.623)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643048', 'KMM 643048 (Inv. FP 34.622)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643049', 'KMM 643049 (Inv. FP 34.621)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643050', 'KMM 643050 (Inv. FP 34.620)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643051', 'KMM 643051 (Inv. FP 34.619)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643052', 'KMM 643052 (Inv. FP 34.618)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643053', 'KMM 643053 (Inv. FP 34.617)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643054', 'KMM 643054 (Inv. FP 34.616)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643055', 'KMM 643055 (Inv. FP 34.615)')`
- `c-6b8170bb` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/643056', 'KMM 643056 (Inv. FP 34.614)')`
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186404', 'KMM 186404 (Inv. FP 489.19.3)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186405', 'KMM 186405 (Inv. FP 489.19.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186406', 'KMM 186406 (Inv. FP 489.19.8)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186407', 'KMM 186407 (Inv. FP 489.20.5)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186408', 'KMM 186408 (Inv. FP 489.20.4)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186409', 'KMM 186409 (Inv. FP 489.20.7)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186410', 'KMM 186410 (Inv. FP 489.20.6)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186411', 'KMM 186411 (Inv. FP 489.20.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186412', 'KMM 186412 (Inv. FP 489.19.9)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186413', 'KMM 186413 (Inv. FP 489.20.3)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186414', 'KMM 186414 (Inv. FP 489.20.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186415', 'KMM 186415 (Inv. FP 489.18.4)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186425', 'KMM 186425 (Inv. FP 489.18.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186426', 'KMM 186426 (Inv. FP 489.17.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186427', 'KMM 186427 (Inv. FP 489.18.3)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186428', 'KMM 186428 (Inv. FP 489.18.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186429', 'KMM 186429 (Inv. FP 489.16.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186431', 'KMM 186431 (Inv. FP 489.17.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186432', 'KMM 186432 (Inv. FP 489.16.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186433', 'KMM 186433 (Inv. FP 489.20.8)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186434', 'KMM 186434 (Inv. FP 489.20.9)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186435', 'KMM 186435 (Inv. FP 489.22.24)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186436', 'KMM 186436 (Inv. FP 489.22.23)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186437', 'KMM 186437 (Inv. FP 489.22.26)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186438', 'KMM 186438 (Inv. FP 489.22.25)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186439', 'KMM 186439 (Inv. FP 489.22.20)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186440', 'KMM 186440 (Inv. FP 489.22.19)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186441', 'KMM 186441 (Inv. FP 489.22.22)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186442', 'KMM 186442 (Inv. FP 489.22.21)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186443', 'KMM 186443 (Inv. FP 489.22.27)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186444', 'KMM 186444 (Inv. FP 489.26.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186445', 'KMM 186445 (Inv. FP 489.26.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186446', 'KMM 186446 (Inv. FP 489.26.4)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186447', 'KMM 186447 (Inv. FP 489.26.3)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186448', 'KMM 186448 (Inv. FP 489.24)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186449', 'KMM 186449 (Inv. FP 489.23)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186450', 'KMM 186450 (Inv. FP 489.25.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186451', 'KMM 186451 (Inv. FP 489.25.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186452', 'KMM 186452 (Inv. FP 489.22.18)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186453', 'KMM 186453 (Inv. FP 489.22.5)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186454', 'KMM 186454 (Inv. FP 489.22.4)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186455', 'KMM 186455 (Inv. FP 489.22.7)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186456', 'KMM 186456 (Inv. FP 489.22.6)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186457', 'KMM 186457 (Inv. FP 489.22.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186458', 'KMM 186458 (Inv. FP 489.21)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186459', 'KMM 186459 (Inv. FP 489.22.3)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186460', 'KMM 186460 (Inv. FP 489.22.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186461', 'KMM 186461 (Inv. FP 489.22.8)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186462', 'KMM 186462 (Inv. FP 489.22.14)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186463', 'KMM 186463 (Inv. FP 489.22.13)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186464', 'KMM 186464 (Inv. FP 489.22.15)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186465', 'KMM 186465 (Inv. FP 489.22.16)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186466', 'KMM 186466 (Inv. FP 489.22.10)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186467', 'KMM 186467 (Inv. FP 489.22.9)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186468', 'KMM 186468 (Inv. FP 489.22.12)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186469', 'KMM 186469 (Inv. FP 489.22.11)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186470', 'KMM 186470 (Inv. FP 489.22.17)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186471', 'KMM 186471 (Inv. FP 489.26.28)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186472', 'KMM 186472 (Inv. FP 489.26.27)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186473', 'KMM 186473 (Inv. FP 489.26.30)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186474', 'KMM 186474 (Inv. FP 489.26.29)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186475', 'KMM 186475 (Inv. FP 489.26.24)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186476', 'KMM 186476 (Inv. FP 489.26.23)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186477', 'KMM 186477 (Inv. FP 489.26.26)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186478', 'KMM 186478 (Inv. FP 489.26.25)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186479', 'KMM 186479 (Inv. FP 489.26.31)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186480', 'KMM 186480 (Inv. FP 489.27.5)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186481', 'KMM 186481 (Inv. FP 489.27.4)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186482', 'KMM 186482 (Inv. FP 489.28)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186483', 'KMM 186483 (Inv. FP 489.27.6)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186484', 'KMM 186484 (Inv. FP 489.27.1)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186485', 'KMM 186485 (Inv. FP 489.26.32)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186486', 'KMM 186486 (Inv. FP 489.27.3)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186487', 'KMM 186487 (Inv. FP 489.27.2)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- `c-bbb03d20` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/186488', 'KMM 186488 (Inv. FP 489.26.22)')` — → ('https://samlinger.natmus.dk/KMM/object/317652', 'KMM 317652 (Inv. FP
- … 990 more

## B2-moved-to-another-final — values of members that now live in another final

**B** · 785 values on 364 finals. **Legal form:** Garbage on the base — the value is rendered on the member's current final (S-moved; no_merge cases confirmed by decision).

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 236 |
| catalog | promoted | removed | 168 |
| mint | foundation | removed | 10 |
| mint | promoted | removed | 8 |
| sources | foundation | removed | 79 |
| sources | promoted | removed | 284 |

Per entity: danish_realm 527, royal_holstein 118, danish_norway 90, gottorp_duchy 26, sonderburg_duchy 10, royal_slesvig 7, norburg_plon_duchy 5, glucksburg_duchy 2.

Examples:

- `c-00c2def8` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-krone-1699-1702/?tid=94124', 'ucoin')` — edit 4831c21
- `c-0c2ee0b8` [danish_norway] sources: `('https://en.ucoin.net/coin/norway-8-skilling-1727-1730/?tid=145800', 'ucoin')`
- `c-1302593b` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1661-1662/?tid=99107', 'ucoin')` — edit 4831c21
- `c-1f98a0d1` [danish_norway] catalog: `('km', '83')`
- `c-21d2bf35` [danish_norway] catalog: `('km', '39')`
- `c-39852c62` [danish_norway] catalog: `('km', '74')`
- `c-086be393` [danish_realm] mint: `"Kongsberg"`
- `c-3f43575e` [danish_realm] mint: `"Helsingør"`
- `c-3f467d36` [danish_realm] mint: `"Kongsberg"`
- `dk-tid-162991` [danish_realm] sources: `('https://numismaster.com/MC_117787', 'NumisMaster')`
- `dk-tid-163033` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-3-skilling-lybsk-1644/?tid=163672', 'ucoin')` — edit 2098ed8
- `dk-tid-163034` [danish_realm] mint: `"Helsingør"`
- `dk-tid-79082` [danish_realm] catalog: `('bruun_page', '86')` — → ('bruun_lot_no', '11287')
- `dk-tid-79082` [danish_realm] catalog: `('bruun_part', 'IV')` — → ('bruun_lot_no', '11287')
- `dk-tid-79088` [danish_realm] sources: `('https://en.numista.com/90550', 'Numista N#90550 — 24 Skilling Dansk - Christian VII')`
- `dk-tid-79088` [danish_realm] catalog: `('bruun_collection_id', '7735')` — edit 214f991
- `hede-134b-chr-v-1677` [danish_realm] mint: `"Christiansstad"`
- `km-147-chr-a-1689` [gottorp_duchy] mint: `"Tönning"` — edit 214f991

## B3-recorded-removal — values a recorded removal already took off

**B** · 42 values on 40 finals. **Legal form:** Garbage on the base — `_recorded_removals` / retractions reproduce without the ledger entry being re-applied.

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 24 |
| catalog | promoted | removed | 13 |
| sources | promoted | removed | 5 |

Per entity: danish_realm 22, royal_holstein 12, gottorp_duchy 4, norburg_plon_duchy 2, danish_norway 1, royal_slesvig 1.

- `c-191330dc` [danish_norway] sources: `('https://samlinger.natmus.dk/KMM/object/403371', 'KMM 403371 (Inv. FP 3479.10)')`
- `c-03dc425f` [danish_realm] catalog: `('numista', '42091')`
- `c-106fed1b` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/402836', 'KMM 402836 (Inv. FP 3594.6)')` — edit 399c954
- `c-106fed1b` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/402837', 'KMM 402837 (Inv. FP 3594.5)')` — edit 399c954
- `c-106fed1b` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/402838', 'KMM 402838 (Inv. FP 3594.4)')` — edit 399c954
- `c-164b0c50` [danish_realm] catalog: `('numista', '214327')` — edit 4f22f45
- `c-1b1c71b8` [danish_realm] catalog: `('numista', '502760')`
- `c-4717a7d3` [danish_realm] catalog: `('numista', '82871')`
- `c-51d19d46` [danish_realm] catalog: `('numista', '433743')`
- `c-6e868a11` [danish_realm] catalog: `('numista', '22115')` — → ('bruun_lot_no', '17205')
- `c-731a902b` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/402840', 'KMM 402840 (Inv. FP 3594.2)')` — edit 4f87b92
- `c-d512bc09` [danish_realm] catalog: `('numista', '72262')`
- `c-df5ca149` [danish_realm] catalog: `('numista', '107874')`
- `dk-tid-79088` [danish_realm] catalog: `('numista', '90550')`
- `dk-tid-99065` [danish_realm] catalog: `('numista', '111346')`
- `hede-23-fr-vi-1815` [danish_realm] catalog: `('numista', '22803')`
- `hede-36-chr-v-1694` [danish_realm] catalog: `('numista', '502760')` — edit 399c954
- `km-104-hede-56b-chr-iv-1627` [danish_realm] catalog: `('numista', '109970')`
- `km-110-chr-iv-1628` [danish_realm] catalog: `('numista', '107718')` — → ('sieg', '58')
- `km-68-chr-iv-1619` [danish_realm] catalog: `('numista', '142850')` — edit 214f991
- `km-695-4-fr-vi-1835` [danish_realm] catalog: `('numista', '22190')` — edit efbc228
- `km-720-1-hede-3e-chr-viii-1845` [danish_realm] catalog: `('numista', '22116')` — → ('bruun_lot_no', '1162'); edit 399c954
- `km-744-1-fr-vii-1849` [danish_realm] catalog: `('numista', '83074')` — edit 399c954
- `km-118-chr-a-1673` [gottorp_duchy] catalog: `('numista', '313829')` — edit 214f991
- `km-188-karl-fr-1705-v1` [gottorp_duchy] catalog: `('numista', '319169')` — edit 214f991
- `km-313441-fr-iii-1622` [gottorp_duchy] catalog: `('numista', '313441')` — edit 214f991
- `km-73-fr-iv-1698` [gottorp_duchy] catalog: `('numista', '564126')` — edit 214f991
- `km-27-fr-karl-plon-1760` [norburg_plon_duchy] catalog: `('numista', '222051')` — edit 214f991
- `km-28-fr-karl-plon-1761` [norburg_plon_duchy] catalog: `('numista', '41864')` — edit 214f991
- `c-4c356fba` [royal_holstein] catalog: `('numista', '22578')`
- `c-c64920e8` [royal_holstein] catalog: `('numista', '108733')`
- `c-d46a4495` [royal_holstein] catalog: `('numista', '313357')` — → ('km', '63'); edit b9e45f7
- `c-dcda1afa` [royal_holstein] catalog: `('numista', '22577')`
- `km-30-2-chr-iv-1642` [royal_holstein] catalog: `('numista', '109450')`
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] catalog: `('numista', '22803')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] catalog: `('numista', '22190')` — edit e8de501
- `km-733-chr-v-1842` [royal_holstein] catalog: `('numista', '24423')` — edit 214f991
- `km-760-fr-vi-1854` [royal_holstein] catalog: `('numista', '22192')` — edit e8de501
- `km-80-1-chr-v-1693` [royal_holstein] catalog: `('numista', '108725')` — edit 214f991
- `km-90-fr-iii-dk-1658` [royal_holstein] catalog: `('numista', '313339')` — edit 214f991
- `km-x007-chr-iv-1620` [royal_holstein] catalog: `('numista', '108002')`
- `c-b8b19e58` [royal_slesvig] catalog: `('numista', '301237')`

## B4-mintmaster-place — mintmaster: a place or entity name in the mintmaster field

**B** · 15 values on 15 finals. **Legal form:** Garbage on the base — V1 bootstrap residue («Trankebar» ×74, «Lübeck», «Brunswick-Wolfenbüttel»); the class has no mintmaster.

| field | origin | direction | values |
|---|---|---|---|
| mintmaster | promoted | removed | 15 |

Per entity: royal_holstein 9, gottorp_duchy 4, danish_realm 2.

- `c-6eca4456` [danish_realm] mintmaster: `"Fredriksborg"`
- `c-af5e6252` [danish_realm] mintmaster: `"Hafnens"` — edit 88aa100
- `c-2191da1c` [gottorp_duchy] mintmaster: `"Gottorp"`
- `c-2cd9d265` [gottorp_duchy] mintmaster: `"Gottorp"`
- `c-2f6d89c3` [gottorp_duchy] mintmaster: `"Gottorp"`
- `c-71739fe0` [gottorp_duchy] mintmaster: `"Gottorp"`
- `c-00eca585` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-0178f89d` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-196700fe` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-30bb6484` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-3f7a6aeb` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-822d83a2` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-8573537a` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-91163ccf` [royal_holstein] mintmaster: `"Slesvig-Holsten"`
- `c-dee1208e` [royal_holstein] mintmaster: `"Slesvig-Holsten"`

## B5-covered-other-form — values the class carries in another form

**B** · 40 values on 24 finals. **Legal form:** Garbage on the base — same catalogue number in another register / sub-variant, same year inside a range, same reading under another label.

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 2 |
| catalog | promoted | removed | 19 |
| mint | foundation | removed | 1 |
| mint | promoted | removed | 18 |

Per entity: danish_realm 20, royal_holstein 19, danish_norway 1.

- `c-e5f4c8f1` [danish_norway] mint: `"Christiania?"` — → "Christiania"; edit 88aa100
- `c-1352d07f` [danish_realm] mint: `"Roskilde?"` — → "Roskilde"; edit 88aa100
- `c-1545e0f9` [danish_realm] mint: `"Kopenhagen?"` — → "Kopenhagen"
- `c-158f70a9` [danish_realm] catalog: `('mb', '541-46')`
- `c-198f01a0` [danish_realm] mint: `"Ribe?"` — → "Ribe"; edit 88aa100
- `c-2bfed91a` [danish_realm] mint: `"Altona. Mintmasters"`
- `c-302a2460` [danish_realm] mint: `"Møntmester ulæseligt"`
- `c-302a2460` [danish_realm] mint: `"Møntmestermærke"`
- `c-404dadd1` [danish_realm] mint: `"Næstved?"` — → "Næstved"; edit 88aa100
- `c-4b2cb585` [danish_realm] mint: `"Ribe?"` — → "Ribe"; edit 88aa100
- `c-7e8d690a` [danish_realm] mint: `"Kopenhagen?"` — → "Kopenhagen"
- `c-904a5eee` [danish_realm] mint: `"Hamborg"`
- `c-bdb9c2a8` [danish_realm] mint: `"Ronneby?"` — → "Ronneby"
- `c-bdd9372b` [danish_realm] mint: `"Malmø?"` — → "Malmø"; edit 88aa100
- `c-bf60ad9f` [danish_realm] mint: `"Næstved?"` — → "Næstved"; edit 88aa100
- `c-c4babebe` [danish_realm] mint: `"Næstved?"` — → "Næstved"; edit 88aa100
- `c-c74262ca` [danish_realm] mint: `"Ribe?"` — → "Ribe"; edit 88aa100
- `c-cdeb43f6` [danish_realm] mint: `"Kopenhagen?"` — → "Kopenhagen"
- `c-e5f3c0ff` [danish_realm] mint: `"Store-Magleby-skatten"`
- `c-f5ef0b21` [danish_realm] catalog: `('mb', '541-46')`
- `km-5-fr-iv-1719` [danish_realm] mint: `"Hamborg"`
- `c-35178b3c` [royal_holstein] catalog: `('km', 'dk:A43')` — → ('km', '95')
- `c-35178b3c` [royal_holstein] catalog: `('km', 'dk:B43')` — → ('km', '95')
- `c-35178b3c` [royal_holstein] catalog: `('km', 'sh:95')` — → ('km', '95')
- `c-35178b3c` [royal_holstein] catalog: `('km', 'sh:A43')` — → ('km', '95')
- `c-35178b3c` [royal_holstein] catalog: `('km', 'sh:B43')` — → ('km', '95')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'dk:77')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'dk:77.1')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'dk:77.2')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'dk:83')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:108')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:110')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:114')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:77')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:77.1')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:77.2')` — → ('km', '108')
- `c-b735eb06` [royal_holstein] catalog: `('km', 'sh:83')` — → ('km', '108')
- `c-d46a4495` [royal_holstein] catalog: `('km', 'sh:63')` — → ('km', '63'); edit efbc228
- `km-696-1-fr-vi-1826` [royal_holstein] catalog: `('km', 'sh:696')` — → ('km', '696'); edit efbc228
- `km-696-1-fr-vi-1826` [royal_holstein] catalog: `('km', 'sh:696.1')` — → ('km', '696'); edit efbc228

## B6-flag-class-claim — `*_verified` true → the class's false

**B** · 213 values on 166 finals. **Legal form:** Accept the class's claim — the final's `true` had no member attesting it (2026-10-06 `_members_decline` rule); the value renders with (?) instead of as verified. A hold is the exception, per case.

| field | origin | direction | values |
|---|---|---|---|
| diameter_mm_verified | promoted | removed | 61 |
| fineness_verified | promoted | removed | 17 |
| metal_verified | promoted | removed | 40 |
| mint_verified | foundation | removed | 14 |
| mint_verified | promoted | removed | 46 |
| weight_rough_verified | promoted | removed | 33 |
| year_verified | promoted | removed | 2 |

Per entity: danish_realm 176, danish_norway 23, royal_holstein 5, christian_ii_supporters 3, royal_slesvig 3, gottorp_duchy 1, norburg_plon_duchy 1, sonderburg_duchy 1.

Examples:

- `c-69d58126` [christian_ii_supporters] metal_verified: `true`
- `c-ddefc984` [christian_ii_supporters] metal_verified: `true`
- `c-ddefc984` [christian_ii_supporters] mint_verified: `true` — → false
- `c-1a0998a0` [danish_norway] metal_verified: `true` — → false
- `c-1a0998a0` [danish_norway] fineness_verified: `true` — → false
- `c-2a619cb8` [danish_norway] fineness_verified: `true` — → false
- `c-49ea148b` [danish_norway] weight_rough_verified: `true` — → false; edit 88aa100
- `c-abc3425a` [danish_norway] weight_rough_verified: `true` — → false; edit 88aa100
- `c-afd707d6` [danish_norway] diameter_mm_verified: `true`
- `c-bff537a8` [danish_norway] fineness_verified: `true` — → false
- `c-bff537a8` [danish_norway] diameter_mm_verified: `true`
- `c-e5f4c8f1` [danish_norway] mint_verified: `true` — → false; edit 88aa100
- `c-eec754e6` [danish_norway] weight_rough_verified: `true` — → false; edit 88aa100
- `c-013899a0` [danish_realm] mint_verified: `true` — → false; edit 88aa100
- `c-03dc425f` [danish_realm] diameter_mm_verified: `true`
- `c-42f4b301` [danish_realm] year_verified: `true`
- `c-51d19d46` [danish_realm] year_verified: `true`
- `dk-tid-101040` [danish_realm] mint_verified: `true` — → false
- `dk-tid-70759` [danish_realm] mint_verified: `true` — → false
- `dk-tid-96999` [danish_realm] mint_verified: `true` — → false

## D6-v1-values-on-promoted — mint / metal / inscriptions on promoted finals, migrated from purged V1 foundations

**D** · 61 values on 58 finals. **Legal form:** Deferred with D3/D5, but visible — V1 curator values (P3 migration) no class carries: the inscriptions are curated V1 prose, and the finals that lose `metal` / `mint` render an empty column; a hold on the final keeps them until the harvest covers them.

| field | origin | direction | values |
|---|---|---|---|
| inscription_obv | promoted | removed | 2 |
| inscription_rev | promoted | removed | 2 |
| metal | promoted | removed | 19 |
| mint | promoted | removed | 38 |

Per entity: danish_realm 56, danish_norway 4, gottorp_duchy 1.

- `c-49ea148b` [danish_norway] metal: `"silver"` — edit 88aa100
- `c-77d4bd3c` [danish_norway] inscription_obv: `"FRIDERICUS III D G DAN NOR VAN GO REX"`
- `c-77d4bd3c` [danish_norway] inscription_rev: `"DOMINUS - PROVIDEBIT 16-51"`
- `c-abc3425a` [danish_norway] metal: `"silver"` — edit 88aa100
- `c-013899a0` [danish_realm] mint: `"Ulæselig møntmestermærke"` — edit 88aa100
- `c-03dc425f` [danish_realm] mint: `"Kopenhagen"`
- `c-03f7adf9` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-0bd34cbf` [danish_realm] mint: `"Hamborg"`
- `c-11ca983d` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-125ef7c3` [danish_realm] mint: `"Altona"`
- `c-125ef7c3` [danish_realm] mint: `"Kopenhagen"`
- `c-1883f545` [danish_realm] mint: `"Kopenhagen"`
- `c-1c7dd04d` [danish_realm] mint: `"Hamborg"`
- `c-1ca0621c` [danish_realm] mint: `"Nørrejylland"` — edit 88aa100
- `c-1d93662d` [danish_realm] mint: `"Kopenhagen"` — edit 88aa100
- `c-209ba326` [danish_realm] mint: `"Kopenhagen"`
- `c-23613fe6` [danish_realm] mint: `"Ubestemmelig"` — edit 88aa100
- `c-236f8cbd` [danish_realm] mint: `"Kopenhagen"` — edit 88aa100
- `c-28325c08` [danish_realm] mint: `"Hamborg"`
- `c-2ca4f8c8` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-2e65fb18` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-379d673d` [danish_realm] mint: `"Kopenhagen"`
- `c-37ab7655` [danish_realm] mint: `"Kopenhagen"`
- `c-39f9c988` [danish_realm] mint: `"Kopenhagen"` — edit 88aa100
- `c-445fa62c` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-52e13dc4` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-55a52a9a` [danish_realm] mint: `"Kopenhagen"`
- `c-562cfc87` [danish_realm] mint: `"Hamborg"`
- `c-5fd387a8` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-63b82b67` [danish_realm] mint: `"Altona"` — edit 4f22f45
- `c-67cfc1df` [danish_realm] mint: `"Nørrejylland"` — edit 88aa100
- `c-68b46bb6` [danish_realm] mint: `"Hamborg"`
- `c-6fafd92b` [danish_realm] mint: `"Nørrejylland"` — edit 88aa100
- `c-88a0a419` [danish_realm] mint: `"Hamborg"`
- `c-8e2ef963` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-8ffe7308` [danish_realm] mint: `"Kopenhagen"`
- `c-96b85287` [danish_realm] mint: `"Hamborg"`
- `c-9a249ca5` [danish_realm] inscription_obv: `"FRIDERICUS V - DEI GRATIA"` — edit 4f22f45
- `c-9a249ca5` [danish_realm] inscription_rev: `"DAN NOR VAN GOT REX"` — edit 4f22f45
- `c-a0af239d` [danish_realm] metal: `"silver"` — → "copper"
- `c-a7f7c949` [danish_realm] mint: `"Hamborg"`
- `c-b18ae38c` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-b3cd0a66` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-bc13c967` [danish_realm] mint: `"Kopenhagen"`
- `c-bf708807` [danish_realm] mint: `"Hamborg"`
- `c-c40456d0` [danish_realm] mint: `"Kopenhagen"`
- `c-cc8be508` [danish_realm] mint: `"Hamborg"`
- `c-d57c53be` [danish_realm] mint: `"Kopenhagen"`
- `c-d5be1a39` [danish_realm] mint: `"Kopenhagen"`
- `c-d6de4fca` [danish_realm] mint: `"Kopenhagen"`
- `c-d832d320` [danish_realm] mint: `"Sjælland"` — edit 88aa100
- `c-da1ac38a` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-e1bb29c9` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-e288cd02` [danish_realm] mint: `"Kopenhagen"`
- `c-eb9cee38` [danish_realm] mint: `"Hamborg"`
- `c-f10a2baa` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-f177a1a5` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-f3e883f1` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-fdb7c06d` [danish_realm] metal: `"silver"` — edit 88aa100
- `c-ff436f8e` [danish_realm] mint: `"Nørrejylland"` — edit 88aa100
- `c-8613c90d` [gottorp_duchy] mint: `"Samuel Timpf?"` — edit 88aa100

## B8-bruun-anchor — catalog: the Bruun anchor specimen (lot / page / collection id) differs

**B** · 23 values on 20 finals. **Legal form:** Accept the class's anchor — `bruun_*` are scalar fast-lookup anchors (§9a); the rebuilt final still cites Bruun in `sources`, so no specimen is lost. An anchor rule (earliest lot / best grade) can be fixed in absorb if the choice should be deterministic.

| field | origin | direction | values |
|---|---|---|---|
| catalog | promoted | removed | 23 |

Per entity: danish_realm 17, royal_holstein 5, danish_norway 1.

- `c-825e8d9f` [danish_norway] catalog: `('bruun_lot_no', '14093')` — → ('bruun_lot_no', '14092')
- `c-329482ca` [danish_realm] catalog: `('bruun_lot_no', '1037')` — → ('bruun_lot_no', '13103')
- `c-329482ca` [danish_realm] catalog: `('bruun_page', '75')` — → ('bruun_lot_no', '13103')
- `c-3f6bab7b` [danish_realm] catalog: `('bruun_lot_no', '17038')` — → ('bruun_lot_no', '13068')
- `c-40ca576d` [danish_realm] catalog: `('bruun_lot_no', '13150')` — → ('bruun_lot_no', '1071')
- `c-4e85d84e` [danish_realm] catalog: `('bruun_lot_no', '1047')` — → ('bruun_lot_no', '13118')
- `c-630b3d4c` [danish_realm] catalog: `('bruun_lot_no', '1036')` — → ('bruun_lot_no', '13111')
- `c-6e868a11` [danish_realm] catalog: `('bruun_lot_no', '17213')` — → ('bruun_lot_no', '17205')
- `c-7055c3ff` [danish_realm] catalog: `('bruun_lot_no', '13151')` — → ('bruun_lot_no', '1073')
- `c-91272d84` [danish_realm] catalog: `('bruun_lot_no', '13168')` — → ('bruun_lot_no', '1091')
- `c-9c90bcc9` [danish_realm] catalog: `('bruun_lot_no', '11276')` — → ('bruun_lot_no', '1139')
- `c-af6febe0` [danish_realm] catalog: `('bruun_lot_no', '11203')` — → ('bruun_lot_no', '13112')
- `c-b6029d8c` [danish_realm] catalog: `('bruun_lot_no', '17059')` — → ('bruun_lot_no', '1042')
- `c-b6029d8c` [danish_realm] catalog: `('bruun_page', '39')` — → ('bruun_lot_no', '1042')
- `c-e62e35a9` [danish_realm] catalog: `('bruun_lot_no', '13085')` — → ('bruun_lot_no', '11181')
- `c-e89fbbe2` [danish_realm] catalog: `('bruun_lot_no', '13190')` — → ('bruun_lot_no', '17103')
- `c-f3fe9aa0` [danish_realm] catalog: `('bruun_lot_no', '13156')` — → ('bruun_lot_no', '1083')
- `c-f479c0e7` [danish_realm] catalog: `('bruun_lot_no', '1045')` — → ('bruun_lot_no', '1043')
- `c-5cab1a08` [royal_holstein] catalog: `('bruun_lot_no', '17215')` — → ('bruun_lot_no', '17212')
- `c-9c278826` [royal_holstein] catalog: `('bruun_lot_no', '17070')` — → ('bruun_lot_no', '13139'); edit 577ea14
- `c-9f71c4b4` [royal_holstein] catalog: `('bruun_lot_no', '11190')` — → ('bruun_lot_no', '13099')
- `c-c9d7a202` [royal_holstein] catalog: `('bruun_lot_no', '17078')` — → ('bruun_lot_no', '13159')
- `c-c9d7a202` [royal_holstein] catalog: `('bruun_page', '55')` — → ('bruun_lot_no', '13159')

## B9-note-template-swap — verification_note: one generated template replaced by another

**B** · 82 values on 82 finals. **Legal form:** Nothing lost — absorb's promotion boilerplate («Hede seed: … still pending») vs the class's source template (IKMK / KMM / Numista record); both are generated. The hand-backfilled `da` is replaced by the class template's own `da`.

| field | origin | direction | values |
|---|---|---|---|
| verification_note | promoted | removed | 82 |

Per entity: danish_realm 63, royal_holstein 16, royal_slesvig 3.

Examples:

- `c-013e4512` [danish_realm] verification_note: `{"da": "Kun oversigtsrækken i f2hede.htm belægger denne post; Hede-dybdesiden mangler på d` — → {"da": "Kun oversigtsrækken hos f2hede.htm dokumenterer denne post; He; edit a523b0f
- `c-013ec728` [danish_realm] verification_note: `{"da": "Kun oversigtsrækken i c5hede1.htm belægger denne post; Hede-dybdesiden mangler på ` — → {"da": "Kun oversigtsrækken hos c5hede1.htm dokumenterer denne post; H; edit a523b0f
- `c-084f5f0c` [danish_realm] verification_note: `{"da": "Kun oversigtsrækken i f2hede.htm belægger denne post; Hede-dybdesiden mangler på d` — → {"da": "Kun oversigtsrækken hos f2hede.htm dokumenterer denne post; He; edit a523b0f

## C0-hand-edit — a hand edit on the final (per commit)

**C** · 45 values on 25 finals. **Legal form:** Keep — needs the surface named per commit below (hold / writer rule / merge decision / errata).

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 9 |
| catalog | promoted | removed | 11 |
| diameter_mm | foundation | removed | 2 |
| fineness | foundation | removed | 2 |
| mint | foundation | removed | 1 |
| mintmaster | promoted | removed | 2 |
| sources | foundation | removed | 8 |
| sources | promoted | removed | 8 |
| weight_rough_g | foundation | removed | 2 |

Per entity: danish_realm 29, royal_holstein 14, danish_norway 2.

| commit | date | subject | values | finals |
|---|---|---|---|---|
| `214f991` | 2026-05-18 | v2: rename curated → final + bootstrap_v2_final_from_v1 + match strategy doc | 5 | 1 |
| `730d93f` | 2026-05-18 | data: strip *-unlisted refs from catalog + mintmaster initials from mint | 1 | 1 |
| `ace1c6a` | 2026-05-19 | docs+data: source-ref label convention + cleanup of 9 verbose offenders | 1 | 1 |
| `26c903d` | 2026-05-24 | data(final): consolidate per-Hede-sub-variant V1 foundations into single entries | 3 | 2 |
| `51ff425` | 2026-05-26 | data: bump cache pointer — Numista BO.7 batch EF (oldenburg_county, 5 NIDs) | 6 | 2 |
| `10850ab` | 2026-05-27 | restore-v1: broaden V1↔V2 matchers — lange + km+ruler+year fallbacks | 1 | 1 |
| `784179d` | 2026-05-27 | fraction-infer: sub-unit-aware leading-fraction + retroactive correction | 2 | 2 |
| `a2e1952` | 2026-05-31 | fix: tighten over-merge split — require no shared type-level catalog ref (Hede/L | 11 | 3 |
| `4f22f45` | 2026-06-01 | data: §CL-3 absorb → final (7018 entries, builds clean) | 6 | 2 |
| `58f1a4b` | 2026-06-03 | data: §CS fix 7 V1 bruun collection-id typos (adjacent-lot mis-cites) | 1 | 1 |
| `24b8855` | 2026-06-12 | data: consolidate duplicated/truncated Aagaard refs (179 entries) | 4 | 4 |
| `11f2f2a` | 2026-06-14 | data: gap-fill None ruler (67) + mintmaster (258) on final from members | 2 | 2 |
| `efbc228` | 2026-06-16 | data: absorb apply — KM631/FrD'or united in royal_holstein, c7h re-homed, c7h13a | 3 | 1 |
| `1a2e482` | 2026-06-20 | data: Ungersk Gylden → reichsdukatenfuss — fold 5 KMM specimens + promote f2h7e | 2 | 2 |
| `aab9d06` | 2026-06-20 | data: merge KMM 156783 «Guldgylden» → f2h5 Guldkrone (Frederik II 1564) | 1 | 1 |
| `95f4d35` | 2026-06-23 | data: clean Hede-3/Hede-8 over-merge residue from c5h56 (Christian V 2 Dukat) | 2 | 1 |
| `69255e4` | 2026-06-26 | data: fold 4 confirmed Pattern-A duplicate final foundations | 5 | 2 |
| `fc5a619` | 2026-06-28 | data: c7h13 — restore dropped Bruun Part III (KM 651.1) source + drop foreign N# | 3 | 1 |
| `8266c1e` | 2026-07-19 | data: sovereign trial pieces display + km-a47 auction source | 1 | 1 |


`214f991` v2: rename curated → final + bootstrap_v2_final_from_v1 + match strategy doc

- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.numista.com/308517', 'Numista N#308517')` — → ('https://en.numista.com/308517', 'Numista N#308517 — 1 Speciedaler - ; edit 214f991,a2e1952,e210ed6
- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.numista.com/catalogue/pieces301630.html', 'Numista N#301630')` — → ('https://en.numista.com/308517', 'Numista N#308517 — 1 Speciedaler - ; edit 214f991,a2e1952,e210ed6
- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1683/?tid=163663', 'ucoin tid 163663')` — → ('https://en.numista.com/308517', 'Numista N#308517 — 1 Speciedaler - ; edit 214f991,a2e1952,e210ed6
- `km-105-chr-v-1683` [royal_holstein] catalog: `('others', 'KM# 73')` — edit 214f991,a2e1952
- `km-105-chr-v-1683` [royal_holstein] catalog: `('others', 'Numista N#308517')` — edit 214f991,a2e1952

`730d93f` data: strip *-unlisted refs from catalog + mintmaster initials from mint

- `km-733-chr-v-1842` [royal_holstein] mint: `"Altona"` — edit 730d93f

`ace1c6a` docs+data: source-ref label convention + cleanup of 9 verbose offenders

- `km-73-chr-iv-1619` [danish_realm] sources: `('https://en.numista.com/420365', 'Numista 420365')` — → ('https://en.numista.com/420365', 'Numista N#420365 — 1 Gold Krone - C; edit ace1c6a,e210ed6

`26c903d` data(final): consolidate per-Hede-sub-variant V1 foundations into single entries (c4h25 + 

- `km-104-hede-56b-chr-iv-1627` [danish_realm] catalog: `('bruun_collection_id', '5607')` — edit 26c903d
- `km-74-1-hede-25c-chr-iv-1621` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h25.htm', 'danskmoent.dk (Hede c4h25D)')` — → ('https://www.danskmoent.dk/chr/c4h25.htm', 'danskmoent.dk (Hede c4h25; edit 26c903d
- `km-74-1-hede-25c-chr-iv-1621` [danish_realm] catalog: `('others', 'Harck-29.1')` — → ('bruun_lot_no', '1028'); edit 26c903d

`51ff425` data: bump cache pointer — Numista BO.7 batch EF (oldenburg_county, 5 NIDs)

- `dk-tid-70750` [danish_realm] weight_rough_g: `(1.52, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70750` [danish_realm] fineness: `(0.229, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70750` [danish_realm] diameter_mm: `(15.0, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70751` [danish_realm] weight_rough_g: `(1.52, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70751` [danish_realm] fineness: `(0.229, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70751` [danish_realm] diameter_mm: `(15.5, 'ucoin')` — edit 4f22f45,51ff425

`10850ab` restore-v1: broaden V1↔V2 matchers — lange + km+ruler+year fallbacks

- `c-131a7eb9` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-2-dukat-1647/?tid=97394', 'ucoin')` — edit 10850ab,a2e1952

`784179d` fraction-infer: sub-unit-aware leading-fraction + retroactive correction

- `dk-tid-130240` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c9h1.htm', 'danskmoent.dk (Hede c9h1A)')` — → ('https://www.danskmoent.dk/chr/c8h1.htm', 'danskmoent.dk (Hede c8h1C); edit 784179d
- `km-578-1-fr-v-1751` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f5h37b.htm', 'danskmoent.dk (Hede f5h37bA)')` — → ('https://www.danskmoent.dk/fr/f5h37b.htm', 'danskmoent.dk (Hede f5h37; edit 784179d

`a2e1952` fix: tighten over-merge split — require no shared type-level catalog ref (Hede/Lange/Sieg/

- `c-43d7dead` [danish_norway] sources: `('https://numismaster.com/MC_110722', 'NumisMaster')` — edit a2e1952
- `c-131a7eb9` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-2-dukat-1647/?tid=97394', 'ucoin')` — edit 10850ab,a2e1952
- `c-131a7eb9` [danish_realm] catalog: `('bruun_collection_id', '5814')` — → ('bruun_lot_no', '11210'); edit a2e1952
- `c-131a7eb9` [danish_realm] catalog: `('bruun_lot_no', '1046')` — → ('bruun_lot_no', '11210'); edit a2e1952
- `c-131a7eb9` [danish_realm] catalog: `('bruun_page', '84')` — → ('bruun_lot_no', '11210'); edit a2e1952
- `c-131a7eb9` [danish_realm] catalog: `('bruun_part', 'I')` — → ('bruun_lot_no', '11210'); edit a2e1952
- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.numista.com/308517', 'Numista N#308517')` — → ('https://en.numista.com/308517', 'Numista N#308517 — 1 Speciedaler - ; edit 214f991,a2e1952,e210ed6
- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.numista.com/catalogue/pieces301630.html', 'Numista N#301630')` — → ('https://en.numista.com/308517', 'Numista N#308517 — 1 Speciedaler - ; edit 214f991,a2e1952,e210ed6
- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1683/?tid=163663', 'ucoin tid 163663')` — → ('https://en.numista.com/308517', 'Numista N#308517 — 1 Speciedaler - ; edit 214f991,a2e1952,e210ed6
- `km-105-chr-v-1683` [royal_holstein] catalog: `('others', 'KM# 73')` — edit 214f991,a2e1952
- `km-105-chr-v-1683` [royal_holstein] catalog: `('others', 'Numista N#308517')` — edit 214f991,a2e1952

`4f22f45` data: §CL-3 absorb → final (7018 entries, builds clean)

- `dk-tid-70750` [danish_realm] weight_rough_g: `(1.52, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70750` [danish_realm] fineness: `(0.229, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70750` [danish_realm] diameter_mm: `(15.0, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70751` [danish_realm] weight_rough_g: `(1.52, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70751` [danish_realm] fineness: `(0.229, 'ucoin')` — edit 4f22f45,51ff425
- `dk-tid-70751` [danish_realm] diameter_mm: `(15.5, 'ucoin')` — edit 4f22f45,51ff425

`58f1a4b` data: §CS fix 7 V1 bruun collection-id typos (adjacent-lot mis-cites)

- `km-577-1-fr-v-1755` [danish_realm] catalog: `('bruun_collection_id', '7656')` — edit 58f1a4b

`24b8855` data: consolidate duplicated/truncated Aagaard refs (179 entries)

- `hede-17-fr-ii-1572` [danish_realm] catalog: `('others', 'Aagaard# & Märcher-72.10')` — edit 24b8855
- `km-133-1-chr-iv-1645` [danish_realm] catalog: `('others', 'Aagaard# K9')` — edit 24b8855
- `km-15-chr-iv-1603` [danish_realm] catalog: `('others', 'Aagaard# 3 (3/3) / Aagaard-4')` — → ('others', 'Aagaard# 3 (3/3)'); edit 24b8855
- `km-271-fr-iii-1666` [danish_realm] catalog: `('others', 'Aagaard# 94.1')` — edit 24b8855

`11f2f2a` data: gap-fill None ruler (67) + mintmaster (258) on final from members

- `c-4dda9342` [danish_norway] mintmaster: `"Henning Christopher Meyer, the elder"` — → "Henning Christopher Meyer, the Elder"; edit 11f2f2a
- `c-7dcfff98` [royal_holstein] mintmaster: `"Jacob Schwieger"` — → "Jacob Schwieger (IS)"; edit 11f2f2a

`efbc228` data: absorb apply — KM631/FrD'or united in royal_holstein, c7h re-homed, c7h13a year-hold

- `c-2a9ecadd` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1795-1801/?tid=79169', 'ucoin')` — edit efbc228,fc5a619
- `c-2a9ecadd` [royal_holstein] sources: `('https://numismaster.com/MC_145357', 'NumisMaster')` — edit efbc228,fc5a619
- `c-2a9ecadd` [royal_holstein] sources: `('https://numismaster.com/MC_65502', 'NumisMaster')` — edit efbc228,fc5a619

`1a2e482` data: Ungersk Gylden → reichsdukatenfuss — fold 5 KMM specimens + promote f2h7e

- `c-47e5cd8e` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/137163', 'KMM 137163 (Inv. RP 24.1, Schou 3)')` — edit 1a2e482
- `c-e7fbabb3` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/156724', 'KMM 156724 (Inv. KP 1800.3, Schou 5)')` — edit 1a2e482

`aab9d06` data: merge KMM 156783 «Guldgylden» → f2h5 Guldkrone (Frederik II 1564)

- `c-a26aa752` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/156783', 'KMM 156783 (Inv. RP 424.1, «Guldgylden»` — edit aab9d06

`95f4d35` data: clean Hede-3/Hede-8 over-merge residue from c5h56 (Christian V 2 Dukat)

- `c-1fcc3e8e` [danish_realm] catalog: `('bruun_lot_no', '1122')` — edit 95f4d35
- `c-1fcc3e8e` [danish_realm] catalog: `('bruun_page', '173')` — edit 95f4d35

`69255e4` data: fold 4 confirmed Pattern-A duplicate final foundations

- `c-04e71a9f` [danish_realm] catalog: `('sieg_hede1971', '14.1')` — → ('sieg', '14.1'); edit 69255e4
- `c-2a9ecadd` [royal_holstein] catalog: `('bruun_lot_no', '11295')` — → ('bruun_lot_no', '1155'); edit 69255e4
- `c-2a9ecadd` [royal_holstein] catalog: `('bruun_page', '147')` — → ('bruun_lot_no', '1155'); edit 69255e4
- `c-2a9ecadd` [royal_holstein] catalog: `('bruun_part', 'III')` — → ('bruun_lot_no', '1155'); edit 69255e4
- `c-2a9ecadd` [royal_holstein] catalog: `('others', 'FP-42.3')` — → ('bruun_lot_no', '1155'); edit 69255e4

`fc5a619` data: c7h13 — restore dropped Bruun Part III (KM 651.1) source + drop foreign N#131730

- `c-2a9ecadd` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1795-1801/?tid=79169', 'ucoin')` — edit efbc228,fc5a619
- `c-2a9ecadd` [royal_holstein] sources: `('https://numismaster.com/MC_145357', 'NumisMaster')` — edit efbc228,fc5a619
- `c-2a9ecadd` [royal_holstein] sources: `('https://numismaster.com/MC_65502', 'NumisMaster')` — edit efbc228,fc5a619

`8266c1e` data: sovereign trial pieces display + km-a47 auction source

- `km-a47-chr-iv-1608` [danish_realm] sources: `('https://auctions.stacksbowers.com/lots/view/3-1AKR2G/denmark-sovereign-1608-elsinore-min` — edit 8266c1e

## C1-nominal-form — nominal: the final's form vs the class's form

**C** · 29 values on 29 finals. **Legal form:** Decide per pair — the writer's nominal normalisation (stage N) or a hold on the final; several class forms are junk («1 Ducat (3.5)»).

| field | origin | direction | values |
|---|---|---|---|
| nominal | promoted | removed | 29 |

Per entity: danish_realm 24, danish_norway 3, gottorp_duchy 1, royal_holstein 1.

| final form (base) | class form (rebuild) | n |
|---|---|---|
| "1 Goldgulden" | "1 Rhinsk Gylden" | 4 |
| "5 Ducat" | "½ Portugaløser" | 2 |
| "12 Skilling" | "⅛ Speciedaler = 12 Skilling" | 1 |
| "16 Skilling" | "16 Skilling = 1 Mark" | 1 |
| "6 Mark Rejsedaler" | "1 Rigsdaler Courant (6 Mark Rejsedaler)" | 1 |
| "Gold Off-Metal. 2 Skilling" | "1 Gold Off-Metal" | 1 |
| "1 Ungersk Gylden" | "1 Gulden" | 1 |
| "3 Mark" | "¼ Ducat (3 Mark)" | 1 |
| "2 Christian d’Or" | "2 Christian D'or" | 1 |
| "½ Sølvgylden" | "½ Gulden" | 1 |
| "1 Goldgulden" | "1 Gold Gulden" | 1 |
| "2 Dukat" | "3 Dukat" | 1 |
| "1 Landskrone" | "1 Søsling" | 1 |
| "2½ schilling" | "1/24 Specie, 2½ schilling" | 1 |
| "20 Ducat" | "2 Portugaløser" | 1 |
| "1 Hvid" | "1 Hvid = 4 Pennings" | 1 |
| "1 Sechsling" | "1 Søsling lybsk" | 1 |
| "1 Gros" | "Gros = 9 Pennings" | 1 |
| "5 Skilling" | "0,5 Skilling" | 1 |
| "1 Rigsdaler Courant" | "½ Kurant Dukat (1 Rixdaler)" | 1 |
| "18 Mark" | "1 Guldkrone" | 1 |
| "6 Mark" | "1 Reisedaler = 6 Mark" | 1 |
| "1 Sterling" | "1 Sterling = 3 Pennings" | 1 |
| "1 Sechsling" | "6 Pfennig, Sechsling" | 1 |
| "8 Rigsbankskilling" | "8 Skilling" | 1 |

- `c-5f490fda` [danish_norway] nominal: `"12 Skilling"` — → "⅛ Speciedaler = 12 Skilling"
- `c-8e850e11` [danish_norway] nominal: `"16 Skilling"` — → "16 Skilling = 1 Mark"
- `c-a80e70cb` [danish_norway] nominal: `"6 Mark Rejsedaler"` — → "1 Rigsdaler Courant (6 Mark Rejsedaler)"
- `c-03dc425f` [danish_realm] nominal: `"Gold Off-Metal. 2 Skilling"` — → "1 Gold Off-Metal"
- `c-26e0d418` [danish_realm] nominal: `"1 Ungersk Gylden"` — → "1 Gulden"; edit 9a3a0e4
- `c-329482ca` [danish_realm] nominal: `"1 Goldgulden"` — → "1 Rhinsk Gylden"; edit baa587f
- `c-3344ccca` [danish_realm] nominal: `"3 Mark"` — → "¼ Ducat (3 Mark)"
- `c-3412889a` [danish_realm] nominal: `"2 Christian d’Or"` — → "2 Christian D'or"
- `c-34b22a8e` [danish_realm] nominal: `"5 Ducat"` — → "½ Portugaløser"
- `c-471ecb4b` [danish_realm] nominal: `"½ Sølvgylden"` — → "½ Gulden"
- `c-51d19d46` [danish_realm] nominal: `"1 Goldgulden"` — → "1 Gold Gulden"; edit baa587f
- `c-5a4e1f65` [danish_realm] nominal: `"2 Dukat"` — → "3 Dukat"; edit 4093197
- `c-61c4742c` [danish_realm] nominal: `"1 Landskrone"` — → "1 Søsling"; edit 88aa100
- `c-621e8b09` [danish_realm] nominal: `"1 Goldgulden"` — → "1 Rhinsk Gylden"; edit baa587f
- `c-666b9ab2` [danish_realm] nominal: `"2½ schilling"` — → "1/24 Specie, 2½ schilling"; edit 88aa100
- `c-6c343eb0` [danish_realm] nominal: `"1 Goldgulden"` — → "1 Rhinsk Gylden"; edit baa587f
- `c-6e0d4e36` [danish_realm] nominal: `"20 Ducat"` — → "2 Portugaløser"
- `c-7ba89ef7` [danish_realm] nominal: `"1 Hvid"` — → "1 Hvid = 4 Pennings"
- `c-81cf98ee` [danish_realm] nominal: `"1 Sechsling"` — → "1 Søsling lybsk"
- `c-83fa9e4d` [danish_realm] nominal: `"1 Goldgulden"` — → "1 Rhinsk Gylden"; edit baa587f
- `c-897476a3` [danish_realm] nominal: `"5 Ducat"` — → "½ Portugaløser"
- `c-913f9b9d` [danish_realm] nominal: `"1 Gros"` — → "Gros = 9 Pennings"
- `c-a8790e31` [danish_realm] nominal: `"5 Skilling"` — → "0,5 Skilling"; edit 88aa100
- `c-c5990b01` [danish_realm] nominal: `"1 Rigsdaler Courant"` — → "½ Kurant Dukat (1 Rixdaler)"
- `c-cebf5953` [danish_realm] nominal: `"18 Mark"` — → "1 Guldkrone"
- `c-cebfa214` [danish_realm] nominal: `"6 Mark"` — → "1 Reisedaler = 6 Mark"
- `c-ea17009c` [danish_realm] nominal: `"1 Sterling"` — → "1 Sterling = 3 Pennings"
- `c-64fe16d1` [gottorp_duchy] nominal: `"1 Sechsling"` — → "6 Pfennig, Sechsling"
- `c-034963a9` [royal_holstein] nominal: `"8 Rigsbankskilling"` — → "8 Skilling"

## C2-ruler-regression — ruler: an annotated or misspelt source form comes back

**C** · 7 values on 7 finals. **Legal form:** Keep the canonical form — extend `canonical_ruler_display` to the annotated Danish-king forms; the two KMM typos («Frederikg 4», «Frederik VVI») → KMM builder errata.

| field | origin | direction | values |
|---|---|---|---|
| ruler | promoted | removed | 7 |

Per entity: danish_norway 3, danish_realm 3, royal_holstein 1.

- `c-2b895709` [danish_norway] ruler: `"Frederik III."` — → "Frederick III (Frederik III)"; edit 7e95732
- `c-35d24571` [danish_norway] ruler: `"Frederik III."` — → "Frederick III (Frederik III)"; edit 7e95732
- `c-da179a7e` [danish_norway] ruler: `"Frederik I."` — → "Frederick I (Friedrich I)"; edit a777b9a
- `c-0514c3fc` [danish_realm] ruler: `"Frederik IV."` — → "Frederikg 4"; edit 7e95732
- `c-24866025` [danish_realm] ruler: `"Frederik VI."` — → "Frederik VVI"; edit 7e95732
- `c-327a89cb` [danish_realm] ruler: `"Frederik III."` — → "Frederick III (Frederik III)"; edit 7e95732
- `c-d84bda91` [royal_holstein] ruler: `"Frederik VI."` — → "Frederick VI of Denmark (Friedrich VI von Dänemark)"; edit a777b9a

## C3-ruler-lost — ruler: the class has none, the final had one

**C** · 14 values on 14 finals. **Legal form:** Keep — single-source classes (NGC, IKMK, Bruun, KMM) whose builder sets no ruler; a writer rule (ruler from the title / reign) or a hold on the final.

| field | origin | direction | values |
|---|---|---|---|
| ruler | promoted | removed | 14 |

Per entity: danish_realm 13, danish_norway 1.

- `c-60c1ac21` [danish_norway] ruler: `"Frederik VI."`
- `c-0a481b96` [danish_realm] ruler: `"Christian V."`
- `c-36021b82` [danish_realm] ruler: `"Christian V"`
- `c-65eb884f` [danish_realm] ruler: `"Christian V"`
- `c-778f4e8d` [danish_realm] ruler: `"Christian IV."`
- `c-8c166c35` [danish_realm] ruler: `"Christian V"`
- `c-9c35e5bc` [danish_realm] ruler: `"Frederick III"`
- `c-a33b02eb` [danish_realm] ruler: `"Christian V"`
- `c-a5cc4716` [danish_realm] ruler: `"Frederik III."`
- `c-c3acee1b` [danish_realm] ruler: `"Christian V"`
- `c-d866a390` [danish_realm] ruler: `"Frederick III"`
- `c-e4613668` [danish_realm] ruler: `"Christian V"`
- `c-e4814701` [danish_realm] ruler: `"Frederick III"`
- `c-fea181e8` [danish_realm] ruler: `"Frederik III."`

## C4-note-da-lost — verification_note: the final's Danish version is not in the class

**C** · 5 values on 5 finals. **Legal form:** Keep — the hand backfill of `da`; the class's note template for that source needs a `da` version.

| field | origin | direction | values |
|---|---|---|---|
| verification_note | promoted | removed | 5 |

Per entity: danish_realm 4, danish_norway 1.

- `c-69c4301b` [danish_norway] verification_note: `{"da": "Data hentet fra Bruun-auktionskatalogen (Stack's Bowers, L. E. Bruun Collection 20` — → {"de": "Daten aus dem Bruun-Auktionskatalog (Stack's Bowers, L. E. Bru; edit 064bfe9
- `c-048a552f` [danish_realm] verification_note: `{"da": "Post fra Den kgl. Mønt- og Medaillesamling (Nationalmuseet, København, api.natmus.` — → {"de": "Datensatz aus der Kgl. Münz- und Medaillensammlung (Nationalmu; edit 064bfe9
- `c-20676b26` [danish_realm] verification_note: `{"da": "Post fra Den kgl. Mønt- og Medaillesamling (Nationalmuseet, København, api.natmus.` — → {"de": "Datensatz aus der Kgl. Münz- und Medaillensammlung (Nationalmu; edit 064bfe9
- `c-27b95413` [danish_realm] verification_note: `{"da": "Post fra Den kgl. Mønt- og Medaillesamling (Nationalmuseet, København, api.natmus.` — → {"de": "Datensatz aus der Kgl. Münz- und Medaillensammlung (Nationalmu; edit 064bfe9
- `c-88562d8b` [danish_realm] verification_note: `{"da": "Numista-seed: tildeling af møntfod og fase samt verifikation af den enkelte mønt u` — → {"de": "Numista-Seed: spezifikische Müntzfuß- und Phase-Zuordnung sowi; edit 064bfe9

## C5-note-curated-text — verification_note: curated prose replaced by a class template

**C** · 5 values on 5 finals. **Legal form:** Keep — the base note is not a template (fewer than 5 finals share it); a hold on `verification_note`, or the text belongs on the seed.

| field | origin | direction | values |
|---|---|---|---|
| verification_note | promoted | removed | 5 |

- `c-3fc323e5` [danish_realm] verification_note: `{"da": "Finheden er ikke attesteret på stykket; .979 (23½ karat) er sat som kanonisk møntf` — → {"da": "Numista-seed: tildeling af møntfod og fase samt verifikation a; edit 7a831dc
- `c-59881f83` [danish_realm] verification_note: `{"da": "Finheden er ikke attesteret på stykket; finheden af noblerne før 1514 er ikke angi` — → {"da": "Numista-seed: tildeling af møntfod og fase samt verifikation a; edit c3bd650
- `c-621e8b09` [danish_realm] verification_note: `{"da": "Finheden .770 = den kanoniske finhed for Rhinskgyldenfod fase I (≈ 18½ karat, Fred` — → {"da": "Hede-seed: tildeling af møntfod og fase samt verifikation af d; edit 7a831dc
- `c-bc790ea1` [danish_realm] verification_note: `{"da": "Finheden er ikke attesteret på stykket; finheden af noblerne før 1514 er ikke angi` — → {"da": "Data hentet fra Bruun-auktionskatalogen (Stack's Bowers, L. E.; edit c3bd650
- `c-f9c15578` [danish_realm] verification_note: `{"da": "Finheden er ikke attesteret på stykket; finheden af noblerne før 1514 er ikke angi` — → {"da": "Numista-seed: tildeling af møntfod og fase samt verifikation a; edit c3bd650

## C6-mintmaster-name — mintmaster: a real name the class does not carry

**C** · 6 values on 6 finals. **Legal form:** Keep — gap-filled from members (11f2f2a) or V1; a hold, or the member that carried it must be found.

| field | origin | direction | values |
|---|---|---|---|
| mintmaster | promoted | removed | 6 |

Per entity: danish_realm 3, royal_holstein 3.

- `c-1fcc3e8e` [danish_realm] mintmaster: `"Christian Wineke, the Elder"`
- `c-a2786f28` [danish_realm] mintmaster: `"lensmand Søren Norby"`
- `c-f120c3c6` [danish_realm] mintmaster: `"Christian Wineke, the Elder"`
- `c-44a9c52f` [royal_holstein] mintmaster: `"Hans Schierven Knoph (HSK)"` — → "Hans Schievern Knoph"
- `c-4c356fba` [royal_holstein] mintmaster: `"Ole Varberg"`
- `c-ca430328` [royal_holstein] mintmaster: `"Johan Friedrich Freund (IFF)"` — → "Johan Friedrich Freund"

## C7-hand-deletion-returns — a value a hand edit deleted comes back from the class

**C** · 39 values on 38 finals. **Legal form:** Keep the deletion — the class still carries the residue: a merge decision (split) / seed errata, or absorb applies `kind: field` ledger entries at enrichment.

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | added | 19 |
| catalog | promoted | added | 1 |
| nominal | promoted | added | 8 |
| ruler | promoted | added | 10 |
| sources | foundation | added | 1 |

Per entity: danish_realm 33, danish_norway 3, royal_holstein 3.

- `c-2b895709` [danish_norway] ruler: `"Frederick III (Frederik III)"` — ← "Frederik III."; edit 7e95732
- `c-35d24571` [danish_norway] ruler: `"Frederick III (Frederik III)"` — ← "Frederik III."; edit 7e95732
- `c-da179a7e` [danish_norway] ruler: `"Frederick I (Friedrich I)"` — ← "Frederik I."; edit a777b9a
- `c-0514c3fc` [danish_realm] ruler: `"Frederikg 4"` — ← "Frederik IV."; edit 7e95732
- `c-24866025` [danish_realm] ruler: `"Frederik VVI"` — ← "Frederik VI."; edit 7e95732
- `c-26e0d418` [danish_realm] nominal: `"1 Gulden"` — ← "1 Ungersk Gylden"; edit 9a3a0e4
- `c-327a89cb` [danish_realm] ruler: `"Frederick III (Frederik III)"` — ← "Frederik III."; edit 7e95732
- `c-329482ca` [danish_realm] nominal: `"1 Rhinsk Gylden"` — ← "1 Goldgulden"; edit baa587f,edf779c
- `c-3412889a` [danish_realm] nominal: `"2 Christian D'or"` — ← "2 Christian d’Or"; edit 784179d,edf779c
- `c-3412889a` [danish_realm] ruler: `"Christian VIII."` — ← "Christian IX."; edit 784179d,edf779c
- `c-51d19d46` [danish_realm] nominal: `"1 Gold Gulden"` — ← "1 Goldgulden"; edit eefddf5
- `c-5a266897` [danish_realm] ruler: `"Christian IV."` — ← "Christian 4"; edit d410c68
- `c-621e8b09` [danish_realm] nominal: `"1 Rhinsk Gylden"` — ← "1 Goldgulden"; edit baa587f
- `c-6c343eb0` [danish_realm] nominal: `"1 Rhinsk Gylden"` — ← "1 Goldgulden"; edit baa587f
- `c-83fa9e4d` [danish_realm] nominal: `"1 Rhinsk Gylden"` — ← "1 Goldgulden"; edit baa587f
- `c-90ec9b6e` [danish_realm] ruler: `"Christian IV."` — ← "Christian 4"; edit 16491cb
- `c-af6febe0` [danish_realm] catalog: `('sieg', '108')` — ← ('bruun_lot_no', '11203'); edit edf779c
- `hede-112a-fr-iii-1666` [danish_realm] catalog: `('sieg', '58')` — ← ('sieg_hede1971', '58'); edit 0aa8b69
- `hede-47-fr-iv-1713` [danish_realm] catalog: `('schou', '1')` — ← ('schou_hede1971', '1'); edit 0aa8b69
- `hede-72-chr-iv-1596` [danish_realm] catalog: `('sieg', '37')` — ← ('schou_hede1971', '10-12'); edit 0aa8b69
- `km-110-chr-iv-1628` [danish_realm] catalog: `('sieg', '58')` — ← ('km', '110'); edit 0aa8b69
- `km-15-chr-iv-1603` [danish_realm] catalog: `('others', 'Aagaard# 3 (3/3)')` — ← ('others', 'Aagaard# 3 (3/3) / Aagaard-4'); edit 24b8855
- `km-19-chr-iv-1603` [danish_realm] catalog: `('sieg', '116')` — ← ('sieg_hede1971', '116'); edit 0aa8b69
- `km-32-1-chr-iv-1606` [danish_realm] catalog: `('sieg', '60')` — ← ('others', 'Harck-6.28.1'); edit 0aa8b69
- `km-340-1-chr-v-1672` [danish_realm] catalog: `('schou', '3')` — ← ('bruun_lot_no', '1101'); edit 0aa8b69
- `km-46-chr-iv-1608` [danish_realm] catalog: `('sieg', '147')` — ← ('sieg_hede1971', '147'); edit 0aa8b69
- `km-48-chr-iv-1602` [danish_realm] catalog: `('sieg', '107')` — ← ('sieg_hede1971', '107'); edit 0aa8b69
- `km-74-1-hede-25c-chr-iv-1621` [danish_realm] catalog: `('sieg', '140')` — ← ('bruun_lot_no', '17052'); edit 0aa8b69
- `km-772-2-chr-ix-1871` [danish_realm] catalog: `('sieg', '4')` — ← ('schou_hede1971', '1,1'); edit 0aa8b69
- `km-796-1-chr-ix-1874` [danish_realm] catalog: `('sieg', '12.1')` — ← ('bruun_collection_id', '8401'); edit 0aa8b69
- `km-797-2-chr-ix-1898` [danish_realm] catalog: `('sieg', '13.2')` — ← ('bruun_collection_id', '8443'); edit 0aa8b69
- `km-798-2-chr-ix-1897` [danish_realm] catalog: `('sieg', '14.2')` — ← ('bruun_collection_id', '8434'); edit 0aa8b69
- `km-802-chr-ix-1903` [danish_realm] catalog: `('sieg', '17')` — ← ('bruun_collection_id', '8467'); edit 0aa8b69
- `km-803-fr-viii-1906` [danish_realm] catalog: `('sieg', '6')` — ← ('bruun_collection_id', '8472'); edit 0aa8b69
- `km-81-chr-iv-1620` [danish_realm] catalog: `('sieg', '51.1')` — ← ('others', 'Harck-18.2.1'); edit 0aa8b69
- `km-82-chr-iv-1620` [danish_realm] catalog: `('sieg', '64.1')` — ← ('sieg_hede1971', '64.1'); edit 0aa8b69
- `c-034963a9` [royal_holstein] nominal: `"8 Skilling"` — ← "8 Rigsbankskilling"; edit edf779c
- `c-d84bda91` [royal_holstein] ruler: `"Frederick VI of Denmark (Friedrich VI von Dänemark)"` — ← "Frederik VI."; edit a777b9a
- `km-105-chr-v-1683` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1683/?tid=163663', 'ucoin')` — ← ('https://en.numista.com/308517', 'Numista N#308517'); edit a2e1952

## D1-v1-twin — V1 foundation twinning a harvested seed's final

**D** · 117 values on 51 finals. **Legal form:** Deferred — fold the twin into the harvested final (merge decision) and the stale copy goes.

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 8 |
| diameter_mm | foundation | removed | 2 |
| fineness | foundation | removed | 4 |
| metal | foundation | removed | 3 |
| mint | foundation | removed | 5 |
| mint_verified | foundation | removed | 3 |
| sources | foundation | removed | 24 |
| sources | promoted | removed | 64 |
| weight_rough_g | foundation | removed | 4 |

Per entity: danish_realm 84, danish_norway 15, royal_holstein 15, gottorp_duchy 2, norburg_plon_duchy 1.

- `c-1f98a0d1` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1665-1666/?tid=97366', 'ucoin')` — edit 4831c21
- `c-39852c62` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1665-1666/?tid=97366', 'ucoin')` — edit 4831c21
- `c-4710fb49` [danish_norway] sources: `('https://en.ucoin.net/coin/norway-4-mark-1669/?tid=145426', 'ucoin')`
- `c-4ce11a03` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-2-speciedaler-1665/?tid=97356', 'ucoin')` — edit 4831c21
- `c-5ee33d47` [danish_norway] sources: `('https://en.ucoin.net/coin/norway-16-skilling-1670/?tid=144918', 'ucoin')` — edit 577ea14
- `c-5ee33d47` [danish_norway] sources: `('https://en.ucoin.net/coin/norway-16-skilling-1671-1679/?tid=144919', 'ucoin')`
- `c-5fc64998` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1657-1661/?tid=97362', 'ucoin')` — edit 4831c21
- `c-5fc64998` [danish_norway] sources: `('https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Oct2025_LE_`
- `c-75b907a1` [danish_norway] sources: `('https://numismaster.com/MC_86246', 'NumisMaster')`
- `c-d92c4cc6` [danish_norway] sources: `('https://en.numista.com/75266', 'Numista N#75266 — 8 Skilling - Frederik IV (Type I; ligh`
- `c-d92c4cc6` [danish_norway] sources: `('https://en.ucoin.net/coin/norway-8-skilling-1702-1715/?tid=145798', 'ucoin')`
- `c-d92c4cc6` [danish_norway] sources: `('https://numismaster.com/MC_86227', 'NumisMaster')`
- `c-d92c4cc6` [danish_norway] sources: `('https://www.ngccoin.com/price-guide/world/norway-8-skilling-km-209-1702-1715-cuid-109776`
- `c-fa7995a4` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1776-1780/?tid=79167', 'ucoin')` — edit 4831c21
- `dk-tid-55898` [danish_norway] sources: `('https://numismaster.com/MC_86247', 'NumisMaster')` — → ('https://en.numista.com/55898', 'Numista N#55898 — 24 Skilling - Chri
- `c-05385872` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-24-skilling-1778-1783/?tid=79089', 'ucoin')`
- `c-05385872` [danish_realm] sources: `('https://numismaster.com/MC_65146', 'NumisMaster')`
- `c-0a481b96` [danish_realm] sources: `('https://en.numista.com/145642', 'Numista N#145642 — 1 Mark Dansk - Christian V')`
- `c-0a481b96` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-mark-1672-1676/?tid=97122', 'ucoin')`
- `c-0a481b96` [danish_realm] sources: `('https://numismaster.com/MC_65162', 'NumisMaster')`
- `c-0a481b96` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c5h70.htm', 'danskmoent.dk (Hede c5h70)')`
- `c-106fed1b` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-sosling-1651/?tid=96431', 'ucoin')` — edit 4831c21
- `c-164b0c50` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1670/?tid=99111', 'ucoin')`
- `c-1fcc3e8e` [danish_realm] sources: `('https://numismaster.com/MC_65883', 'NumisMaster')`
- `c-1fcc3e8e` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-2-ducat-km-419-1692-cuid-1050329-duid-`
- `c-2814423a` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-skilling-1661/?tid=96452', 'ucoin')` — edit 4831c21
- `c-302a2460` [danish_realm] sources: `('https://en.numista.com/109264', 'Numista N#109264 — 1 Kroneskilling - Christian IV')`
- `c-302a2460` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-skilling-1629/?tid=96445', 'ucoin')`
- `c-302a2460` [danish_realm] sources: `('https://numismaster.com/MC_65011', 'NumisMaster')`
- `c-302a2460` [danish_realm] sources: `('https://numismaster.com/MC_65017', 'NumisMaster')`
- `c-302a2460` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-skilling-km-113.2-1629-cuid-1049982-du`
- `c-302a2460` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-skilling-km-65-1619-cuid-1050281-duid-`
- `c-4717a7d3` [danish_realm] sources: `('https://numismaster.com/MC_65108', 'NumisMaster')`
- `c-4717a7d3` [danish_realm] sources: `('https://numismaster.com/MC_65111', 'NumisMaster')`
- `c-4717a7d3` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-6-skilling-km-110-1628-1629-cuid-10505`
- `c-4cfa0f89` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-gl%C3%BCckstadt-mark-danske-km-a4-1617`
- `c-516d5bd3` [danish_realm] sources: `('https://numismaster.com/MC_65785', 'NumisMaster')` — edit bab0d82
- `c-516d5bd3` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-ducat-km-412.1-1691-cuid-1050269-duid-`
- `c-67f432b0` [danish_realm] sources: `('https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Sept2024_LE`
- `c-8784eaad` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-mark-1666/?tid=97120', 'ucoin')` — edit 4831c21
- `c-904a5eee` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-skilling-1676-1681/?tid=96454', 'ucoin')`
- `c-904a5eee` [danish_realm] sources: `('https://numismaster.com/MC_65027', 'NumisMaster')`
- `c-904a5eee` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-skilling-km-357-1676-1681-cuid-1049931`
- `c-9a249ca5` [danish_realm] sources: `('https://ikmk.smb.museum/object?id=18203664', 'IKMK Berlin 18203664')` — edit 4f22f45
- `c-9e01032d` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1665-1666/?tid=97366', 'ucoin')`
- `c-9e01032d` [danish_realm] sources: `('https://numismaster.com/MC_65451', 'NumisMaster')`
- `c-9e01032d` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-speciedaler-km-262-1665-1666-cuid-1050`
- `c-a5cc4716` [danish_realm] sources: `('https://en.numista.com/201276', 'Numista N#201276 — 2 Mark Dansk - Frederik III')`
- `c-a5cc4716` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-2-mark-1653-1657/?tid=99092', 'ucoin')`
- `c-a5cc4716` [danish_realm] sources: `('https://numismaster.com/MC_65176', 'NumisMaster')`
- `c-a9c78d3a` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-skilling-1644-1648/?tid=96446', 'ucoin')` — edit 4831c21
- `c-caf314e5` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-sosling-1631/?tid=96429', 'ucoin')` — edit 4831c21
- `c-d56c3622` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-mark-1668/?tid=97121', 'ucoin')` — edit 4831c21
- `c-d95f8018` [danish_realm] sources: `('https://numismaster.com/MC_65564', 'NumisMaster')`
- `c-f120c3c6` [danish_realm] sources: `('https://numismaster.com/MC_65883', 'NumisMaster')`
- `dk-tid-70750` [danish_realm] catalog: `('km', '729')` — edit 214f991
- `dk-tid-70750` [danish_realm] fineness: `(0.229, 'numismaster')`
- `dk-tid-70750` [danish_realm] metal: `"silver"`
- `dk-tid-70750` [danish_realm] mint: `"Altona"`
- `dk-tid-70750` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `dk-tid-70750` [danish_realm] mint_verified: `true` — → false
- `dk-tid-70750` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-3-rigsbankskilling-1842/?tid=70750', 'ucoin')` — edit 214f991
- `dk-tid-70750` [danish_realm] sources: `('https://numismaster.com/MC_66009', 'NumisMaster')`
- `dk-tid-70750` [danish_realm] weight_rough_g: `(1.519, 'numismaster')`
- `dk-tid-70751` [danish_realm] catalog: `('km', 'A730')` — edit 214f991
- `dk-tid-70751` [danish_realm] fineness: `(0.229, 'numismaster')`
- `dk-tid-70751` [danish_realm] metal: `"silver"`
- `dk-tid-70751` [danish_realm] mint: `"Altona"`
- `dk-tid-70751` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `dk-tid-70751` [danish_realm] mint_verified: `true` — → false
- `dk-tid-70751` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-3-rigsbankskilling-1842/?tid=70751', 'ucoin')` — edit 214f991
- `dk-tid-70751` [danish_realm] sources: `('https://numismaster.com/MC_66010', 'NumisMaster')`
- `dk-tid-70751` [danish_realm] weight_rough_g: `(1.519, 'numismaster')`
- `dk-tid-79158` [danish_realm] catalog: `('bruun_collection_id', '7752')` — edit 214f991
- `dk-tid-79158` [danish_realm] catalog: `('bruun_lot_no', '13233')` — edit 214f991
- `dk-tid-79158` [danish_realm] catalog: `('bruun_page', '164')` — edit 214f991
- `dk-tid-79158` [danish_realm] catalog: `('bruun_part', 'II')` — edit 214f991
- `dk-tid-79158` [danish_realm] catalog: `('km', '606')` — edit 214f991
- `dk-tid-79158` [danish_realm] catalog: `('numista', '148219')`
- `dk-tid-79158` [danish_realm] diameter_mm: `(31.0, 'numista')`
- `dk-tid-79158` [danish_realm] diameter_mm: `(36.0, 'ucoin')`
- `dk-tid-79158` [danish_realm] fineness: `(0.875, 'numista')`
- `dk-tid-79158` [danish_realm] fineness: `(0.875, 'ucoin')`
- `dk-tid-79158` [danish_realm] metal: `"silver"` — edit 214f991
- `dk-tid-79158` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `dk-tid-79158` [danish_realm] mint_verified: `true` — → false
- `dk-tid-79158` [danish_realm] sources: `('https://en.numista.com/148219', 'Numista N#148219 — ½ Speciedaler - Christian VII (Type `
- `dk-tid-79158` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-2-speciedaler-1769/?tid=79158', 'ucoin')` — edit 214f991
- `dk-tid-79158` [danish_realm] sources: `('https://numismaster.com/MC_65396', 'NumisMaster')`
- `dk-tid-79158` [danish_realm] sources: `('https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf', 'Bruun Part II`
- `dk-tid-79158` [danish_realm] weight_rough_g: `(14.45, 'ucoin')`
- `dk-tid-79158` [danish_realm] weight_rough_g: `(14.477, 'numista')`
- `km-110-chr-iv-1628` [danish_realm] sources: `('https://numismaster.com/MC_65111', 'NumisMaster')` — edit eae75bb
- `km-194-fr-iii-1654` [danish_realm] sources: `('https://en.numista.com/143625', 'Numista N#143625 — 1 Krone - Frederik III Victory over `
- `km-194-fr-iii-1654` [danish_realm] sources: `('https://numismaster.com/MC_65282', 'NumisMaster')`
- `km-194-fr-iii-1654` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-krone-km-222-1659-1660-cuid-1050640-du`
- `km-340-1-chr-v-1672` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-dukat-1671-1674/?tid=97528', 'ucoin')` — → ('https://www.danskmoent.dk/chr/c5h2.htm', 'danskmoent.dk (Hede c5h2)'; edit 10850ab
- `km-340-1-chr-v-1672` [danish_realm] sources: `('https://numismaster.com/MC_165455', 'NumisMaster')` — → ('https://www.danskmoent.dk/chr/c5h2.htm', 'danskmoent.dk (Hede c5h2)'
- `km-340-1-chr-v-1672` [danish_realm] sources: `('https://www.ngccoin.com/price-guide/world/denmark-ducat-km-340.2-1672-cuid-1060728-duid-` — → ('https://www.danskmoent.dk/chr/c5h2.htm', 'danskmoent.dk (Hede c5h2)'
- `bruun-14444-ca-1681` [gottorp_duchy] sources: `('https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Oct2025_LE_`
- `km-46-fr-iii-1617` [gottorp_duchy] sources: `('https://ikmk.smb.museum/object?id=18285059', 'IKMK Berlin 18285059')` — → ('https://ikmk.smb.museum/object?id=18284934', 'IKMK Berlin 18284934')
- `km-17-ja-i-plon-1690` [norburg_plon_duchy] sources: `('https://numismaster.com/MC_73979', 'NumisMaster')`
- `c-233e0ac8` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-2-skilling-1771/?tid=78766', 'ucoin')` — edit efbc228
- `c-320a1040` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1647/?tid=97359', 'ucoin')` — edit 4831c21
- `c-bffd7a14` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-1-dor-1843-1847/?tid=130239', 'ucoin')` — edit 577ea14
- `c-d46a4495` [royal_holstein] sources: `('https://www.ngccoin.com/price-guide/world/german-states-schleswig-holstein-krone-km-103-` — → ('https://en.numista.com/108775', 'Numista N#108775 — 4 Mark Dansk - C
- `c-dcda1afa` [royal_holstein] sources: `('https://en.numista.com/22577', 'Numista N#22577 — 2 Skilling - Frederik VI (straight nec`
- `c-dcda1afa` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-2-skilling-1809-1810/?tid=79554', 'ucoin')`
- `c-dcda1afa` [royal_holstein] sources: `('https://numismaster.com/MC_65084', 'NumisMaster')`
- `c-e058d65a` [royal_holstein] sources: `('https://numismaster.com/MC_92989', 'NumisMaster')`
- `c-ef000d77` [royal_holstein] sources: `('https://numismaster.com/MC_92967', 'NumisMaster')`
- `c-f79a47c2` [royal_holstein] sources: `('https://ikmk.smb.museum/object?id=18204859', 'IKMK Berlin 18204859')`
- `dk-tid-79553` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-2-skilling-1801-1805/?tid=79553', 'ucoin')` — edit efbc228
- `dk-tid-79553` [royal_holstein] sources: `('https://numismaster.com/MC_65082', 'NumisMaster')` — edit efbc228
- `km-721-chr-v-1841` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-4-rigsbankskilling-1841-1842/?tid=70753', 'ucoin')` — edit e8de501
- `km-x007-chr-iv-1620` [royal_holstein] sources: `('https://en.numista.com/108002', 'Numista N#108002 — 4 Skilling Lybsk - Christian IV Wire`
- `km-x007-chr-iv-1620` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-4-skilling-lybsk-1620/?tid=163638', 'ucoin')` — edit 214f991,e210ed6

## D2-v1-memberless — memberless V1 foundation: its own record

**D** · 132 values on 20 finals. **Legal form:** Deferred — 16 V1-only + 16 with a catalogue candidate; carry the own record (`_FOUNDATION_OWN`), merge, or exclude.

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 19 |
| diameter_mm | foundation | removed | 9 |
| fineness | foundation | removed | 11 |
| metal | foundation | removed | 20 |
| mint | foundation | removed | 19 |
| mint_verified | foundation | removed | 19 |
| sources | foundation | removed | 21 |
| weight_rough_g | foundation | removed | 14 |

Per entity: danish_realm 64, royal_holstein 59, gottorp_duchy 9.

- `hede-134b-chr-v-1677` [danish_realm] catalog: `('bruun_collection_id', '6905')` — edit 214f991
- `hede-134b-chr-v-1677` [danish_realm] catalog: `('bruun_lot_no', '11260')` — edit 214f991
- `hede-134b-chr-v-1677` [danish_realm] metal: `"lead"` — edit 214f991
- `hede-134b-chr-v-1677` [danish_realm] mint_verified: `true` — → false; edit 214f991
- `hede-18-fr-v-1749` [danish_realm] catalog: `('bruun_collection_id', '7670')` — edit 214f991
- `hede-18-fr-v-1749` [danish_realm] catalog: `('schou_hede1971', '2')` — edit 214f991
- `hede-18-fr-v-1749` [danish_realm] catalog: `('sieg_hede1971', '38')` — edit 214f991
- `hede-18-fr-v-1749` [danish_realm] metal: `"gold"` — edit 214f991
- `hede-18-fr-v-1749` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `hede-18-fr-v-1749` [danish_realm] mint_verified: `true` — → false
- `hede-18-fr-v-1749` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f5h17.htm', 'Hede 18 / danskmoent.dk')` — edit 214f991,e210ed6
- `hede-18-fr-vi-1814` [danish_realm] metal: `"silver"` — edit 214f991
- `hede-18-fr-vi-1814` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `hede-18-fr-vi-1814` [danish_realm] mint_verified: `true` — → false
- `hede-19-fr-vi-1813` [danish_realm] catalog: `('bruun_collection_id', '8006')` — edit 214f991
- `hede-19-fr-vi-1813` [danish_realm] metal: `"silver"` — edit 214f991
- `hede-19-fr-vi-1813` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `hede-19-fr-vi-1813` [danish_realm] mint_verified: `true` — → false
- `hede-20-fr-vi-1813` [danish_realm] catalog: `('bruun_collection_id', '8007')` — edit 214f991
- `hede-20-fr-vi-1813` [danish_realm] metal: `"silver"` — edit 214f991
- `hede-20-fr-vi-1813` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `hede-20-fr-vi-1813` [danish_realm] mint_verified: `true` — → false
- `hede-21-fr-vi-1815` [danish_realm] catalog: `('bruun_collection_id', '8023')` — edit 214f991
- `hede-21-fr-vi-1815` [danish_realm] metal: `"silver"` — edit 214f991
- `hede-21-fr-vi-1815` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `hede-21-fr-vi-1815` [danish_realm] mint_verified: `true` — → false
- `hede-22-fr-vi-1815` [danish_realm] catalog: `('bruun_collection_id', '8024')` — edit 214f991
- `hede-22-fr-vi-1815` [danish_realm] metal: `"silver"` — edit 214f991
- `hede-22-fr-vi-1815` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `hede-22-fr-vi-1815` [danish_realm] mint_verified: `true` — → false
- `km-104-hede-56b-chr-iv-1627` [danish_realm] catalog: `('others', 'KM-DK# 104')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] catalog: `('schou_hede1971', '8-9')` — edit 214f991
- `km-104-hede-56b-chr-iv-1627` [danish_realm] catalog: `('sieg_hede1971', '124.2')` — edit 214f991
- `km-104-hede-56b-chr-iv-1627` [danish_realm] diameter_mm: `(44.5, 'numista')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] fineness: `(0.881, 'numista')`
- `km-104-hede-56b-chr-iv-1627` [danish_realm] metal: `"silver"` — edit 214f991
- `km-104-hede-56b-chr-iv-1627` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-104-hede-56b-chr-iv-1627` [danish_realm] mint_verified: `true` — → false
- `km-104-hede-56b-chr-iv-1627` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h56.htm', 'Hede 56B / danskmoent.dk')` — edit 214f991,e210ed6
- `km-104-hede-56b-chr-iv-1627` [danish_realm] weight_rough_g: `(58.464, 'numista')`
- `km-395-1-chr-v-1688` [danish_realm] catalog: `('bruun_collection_id', '7081')` — edit 214f991
- `km-395-1-chr-v-1688` [danish_realm] metal: `"gold"` — edit 214f991
- `km-395-1-chr-v-1688` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-395-1-chr-v-1688` [danish_realm] mint_verified: `true` — → false
- `km-577-1-fr-v-1755` [danish_realm] diameter_mm: `(20.5, 'ucoin')`
- `km-577-1-fr-v-1755` [danish_realm] metal: `"copper"`
- `km-577-1-fr-v-1755` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-577-1-fr-v-1755` [danish_realm] mint_verified: `true` — → false
- `km-577-1-fr-v-1755` [danish_realm] weight_rough_g: `(3.65, 'ucoin')`
- `km-750-1-fr-vii-1850` [danish_realm] catalog: `('bruun_collection_id', '8203')` — edit 214f991
- `km-750-1-fr-vii-1850` [danish_realm] diameter_mm: `(27.1, 'ucoin')`
- `km-750-1-fr-vii-1850` [danish_realm] fineness: `(0.896, 'numismaster')` — edit 577ea14
- `km-750-1-fr-vii-1850` [danish_realm] fineness: `(0.896, 'ucoin')`
- `km-750-1-fr-vii-1850` [danish_realm] metal: `"gold"` — edit 214f991
- `km-750-1-fr-vii-1850` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-750-1-fr-vii-1850` [danish_realm] mint_verified: `true` — → false
- `km-750-1-fr-vii-1850` [danish_realm] weight_rough_g: `(13.28, 'ucoin')`
- `km-750-1-fr-vii-1850` [danish_realm] weight_rough_g: `(13.284, 'numismaster')` — edit 577ea14
- `km-750-1-fr-vii-1850` [danish_realm] weight_rough_g: `(13.29, 'bruun')` — edit 577ea14
- `km-797-1-chr-ix-1875` [danish_realm] catalog: `('sieg_hede1971', '13.1')` — edit 214f991
- `km-797-1-chr-ix-1875` [danish_realm] metal: `"gold"`
- `km-797-1-chr-ix-1875` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-797-1-chr-ix-1875` [danish_realm] mint_verified: `true` — → false
- `km-797-1-chr-ix-1875` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c9h14.htm', 'Hede 14A / danskmoent.dk')` — edit 214f991,e210ed6
- `km-188-karl-fr-1705-v1` [gottorp_duchy] catalog: `('bruun_lot', '14528')` — edit 214f991
- `km-188-karl-fr-1705-v1` [gottorp_duchy] fineness: `(0.986, 'numista')`
- `km-188-karl-fr-1705-v1` [gottorp_duchy] metal: `"gold"` — edit 214f991
- `km-188-karl-fr-1705-v1` [gottorp_duchy] mint_verified: `true` — → false
- `km-188-karl-fr-1705-v1` [gottorp_duchy] sources: `('', 'Bruun Part II, lot 14234, p. 283')`
- `km-188-karl-fr-1705-v1` [gottorp_duchy] sources: `('https://en.numista.com/catalogue/pieces319169.html', 'Numista')` — edit 214f991,e210ed6
- `km-188-karl-fr-1705-v1` [gottorp_duchy] weight_rough_g: `(3.5, 'numista')`
- `km-x009-fr-iv-1701` [gottorp_duchy] metal: `"silver"` — edit 214f991
- `km-x009-fr-iv-1701` [gottorp_duchy] sources: `('https://www.numisbids.com/sale/433/lot/1676', 'Emporium 69 · Lot 1676')` — edit 214f991,e210ed6
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] catalog: `('bruun_collection_id', '8025')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] catalog: `('others', 'KM# 683')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] diameter_mm: `(30.0, 'ucoin')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] diameter_mm: `(31.0, 'numista')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] fineness: `(0.875, 'numista')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] fineness: `(0.875, 'ucoin')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] metal: `"silver"` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] mint: `"Altona"` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] mint: `"Kopenhagen"` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] mint_verified: `true` — → false; edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] sources: `('https://auctions.stacksbowers.com/lots/view/3-1AKSQN/denmark-rigsbankdaler-1813-copenhag` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] sources: `('https://coins.ha.com/itm/denmark/frederik-vi-rigsbankdaler-1813-ic-vf25-ngc-/a/231513-64` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] sources: `('https://en.numista.com/22803', 'Numista')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] sources: `('https://www.danskmoent.dk/fr/f6h24.htm', 'Hede / danskmoent.dk')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] weight_rough_g: `(14.447, 'numista')` — edit e8de501
- `km-683-1-fr-vi-1813__v1from_schleswig_holstein` [royal_holstein] weight_rough_g: `(14.45, 'ucoin')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] catalog: `('bruun_lot', '8110')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] diameter_mm: `(37.0, 'ucoin')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] fineness: `(0.875, 'numismaster')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] fineness: `(0.875, 'ucoin')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] metal: `"silver"` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] mint: `"Altona"` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] mint: `"Kopenhagen"` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] mint_verified: `true` — → false; edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] sources: `('https://auctions.stacksbowers.com/lots/view/3-1AKSSL/denmark-speciedaler-1837-copenhagen` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] sources: `('https://coins.ha.com/itm/denmark/denmark-frederik-vi-speciedaler-1839-ic-ws-ms64-ngc-/a/` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] sources: `('https://en.numista.com/22190', 'Numista')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] sources: `('https://www.danskmoent.dk/fr/f6h26.htm', 'Hede / danskmoent.dk')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] weight_rough_g: `(28.89, 'ucoin')` — edit e8de501
- `km-695-fr-vi-1820` [royal_holstein] weight_rough_g: `(28.893, 'numismaster')` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] diameter_mm: `(17.0, 'ucoin')` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] fineness: `(0.25, 'ucoin')` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] metal: `"silver"` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] mint: `"Altona"` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] mint: `"Kopenhagen"` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] mint_verified: `true` — → false; edit e8de501
- `km-721-chr-v-1841` [royal_holstein] sources: `('https://www.infinitycoins.com/Products/1842-denmark-4-rigsbankskilling-1-schilling-coura` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] sources: `('https://www.ngccoin.com/price-guide/world/denmark-4-rigsbankskilling-km-721.2-1842-cuid-` — edit e8de501
- `km-721-chr-v-1841` [royal_holstein] weight_rough_g: `(1.7, 'ucoin')` — edit e8de501
- `km-733-chr-v-1842` [royal_holstein] diameter_mm: `(21.5, 'ucoin')` — edit 4f22f45
- `km-733-chr-v-1842` [royal_holstein] fineness: `(0.5, 'ucoin')` — edit 4f22f45
- `km-733-chr-v-1842` [royal_holstein] metal: `"silver"` — edit 214f991
- `km-733-chr-v-1842` [royal_holstein] mint_verified: `true` — → false
- `km-733-chr-v-1842` [royal_holstein] sources: `('https://en.numista.com/24423', 'Numista')` — edit 214f991,e210ed6
- `km-733-chr-v-1842` [royal_holstein] sources: `('https://www.ngccoin.com/price-guide/world/denmark-16-rigsbankskilling-km-733-1842-1844-c` — edit 214f991,e210ed6
- `km-733-chr-v-1842` [royal_holstein] weight_rough_g: `(4.21, 'ucoin')` — edit 214f991,4f22f45
- `km-760-fr-vi-1854` [royal_holstein] diameter_mm: `(30.5, 'numista')` — edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] fineness: `(0.875, 'numista')` — edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] metal: `"silver"` — edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] mint: `"Altona"` — edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] mint: `"Kopenhagen"` — edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] mint_verified: `true` — → false; edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] sources: `('https://en.numista.com/catalogue/pieces22192.html', 'Numista')` — edit e8de501
- `km-760-fr-vi-1854` [royal_holstein] weight_rough_g: `(14.447, 'numista')` — edit e8de501
- `km-90-fr-iii-dk-1658` [royal_holstein] metal: `"billon"` — edit 214f991
- `km-90-fr-iii-dk-1658` [royal_holstein] mint_verified: `true` — → false
- `km-90-fr-iii-dk-1658` [royal_holstein] sources: `('https://en.numista.com/catalogue/pieces313339.html', 'Numista')` — edit 214f991,e210ed6
- `km-90-fr-iii-dk-1658` [royal_holstein] sources: `('https://www.danskmoent.dk/fr/f3h150.htm', 'Hede / danskmoent.dk')` — edit 214f991,e210ed6
- `km-90-fr-iii-dk-1658` [royal_holstein] weight_rough_g: `(0.6, 'numista')`

## D3-v1-uncovered — V1 foundation sources / catalog the class does not carry

**D** · 341 values on 201 finals. **Legal form:** Deferred — curator 2026-10-23: the harvests are expected to cover these; what they do not is listed here.

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 205 |
| sources | foundation | removed | 136 |

Per entity: danish_realm 147, gottorp_duchy 111, sonderburg_duchy 33, royal_holstein 32, norburg_plon_duchy 11, glucksburg_duchy 5, danish_norway 2.

Examples:

- `dk-tid-55898` [danish_norway] sources: `('https://www.coinsbook.net/coins/silver-coin-24-skilling-danske-christian-vii-17440', 'co` — → ('https://en.numista.com/55898', 'Numista N#55898 — 24 Skilling - Chri; edit 214f991,e210ed6
- `dk-tid-55898` [danish_norway] catalog: `('others', 'Brekke# 31–36')` — edit 214f991
- `dk-tid-130240` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-2-d-or-1841-1847/?tid=130240', 'ucoin')` — → ('https://www.danskmoent.dk/chr/c8h1.htm', 'danskmoent.dk (Hede c8h1C); edit 214f991,e210ed6
- `dk-tid-130482` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-2-d-or-1850-1863/?tid=130482', 'ucoin')` — edit 214f991,e210ed6
- `dk-tid-79082` [danish_realm] catalog: `('bruun_lot_no', '17135')` — → ('bruun_lot_no', '11287')
- `dk-tid-94160` [danish_realm] catalog: `('bruun_lot_no', '11282')` — → ('bruun_lot_no', '13225'); edit 214f991

## D4-v1-own-record — V1 foundation metal / mint / readings not carried (seeded, not twin)

**D** · 13 values on 12 finals. **Legal form:** Decide — together with the twins (D1) and the memberless (D2) the foundations that lose `metal` render an empty metal column (count in the header); carrying `metal`/`mint` for foundations, like their prose and years, is the cheap fix.

| field | origin | direction | values |
|---|---|---|---|
| metal | foundation | removed | 1 |
| mint | foundation | removed | 12 |

- `dk-tid-101040` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `dk-tid-70759` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `dk-tid-96999` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `dk-tid-97091` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-103-chr-iv-1624` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-16-2-chr-iv-1618` [danish_realm] metal: `"billon"` — edit 214f991
- `km-16-2-chr-iv-1618` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-271-fr-iii-1666` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-374-2-chr-v-1685` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-68-chr-iv-1619` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-8-chr-v-1677` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-8-fr-iv-1718` [danish_realm] mint: `"Kopenhagen"` — edit 214f991
- `km-x016-chr-iv-1622` [danish_realm] mint: `"Kopenhagen"` — edit 214f991

## D5-v1-citations-on-promoted — V1 curator citations / catalogue refs restored onto promoted hosts

**D** · 109 values on 75 finals. **Legal form:** Deferred with D3 — the 2026-05 restore-v1 pass put V1 citations (old Numista `catalogue/pieces` urls, bare «Numista» / «ucoin» refs, NGC price guide, «KM-DK#») on promoted finals; no class attests them.

| field | origin | direction | values |
|---|---|---|---|
| catalog | promoted | removed | 16 |
| sources | promoted | removed | 93 |

Per entity: royal_holstein 60, danish_realm 31, gottorp_duchy 10, danish_norway 5, norburg_plon_duchy 2, sonderburg_duchy 1.

Examples:

- `c-8a0bd288` [danish_norway] sources: `('https://www.danskmoent.dk/fr/f3h54.htm', 'Hede 54A / danskmoent.dk')` — edit 4831c21
- `c-a21e6343` [danish_norway] sources: `('https://en.numista.com/328513', 'Numista N#328513')` — edit 4831c21
- `c-a21e6343` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-2-speciedaler-1662-1664/?tid=97379', 'ucoin tid 97379'` — edit 4831c21
- `c-5d564c17` [danish_realm] catalog: `('others', 'KM-DK# 104')`
- `c-81ec19a2` [danish_realm] catalog: `('others', 'KM-DK# 204')`
- `c-ad03fceb` [danish_realm] catalog: `('jesse', '262')`

## E1-ruler-other — ruler: the class names another ruler

**E** · 14 values on 14 finals. **Legal form:** Review per case — either the final's ruler was wrong (V1 / gap-fill) or the class is an over-merge.

| field | origin | direction | values |
|---|---|---|---|
| ruler | promoted | removed | 14 |

Per entity: gottorp_duchy 8, danish_realm 4, danish_norway 1, sonderburg_duchy 1.

- `c-3a144235` [danish_norway] ruler: `"Christian III."` — → "Olav Engelbrektsson"; edit 917b7a6
- `c-087330c2` [danish_realm] ruler: `"Johan"` — → "Hans"; edit 88aa100
- `c-4e44f562` [danish_realm] ruler: `"Hans ?"` — → "Hans"; edit 88aa100
- `c-5c4e33a9` [danish_realm] ruler: `"Johan"` — → "Hans"; edit 88aa100
- `c-a497262e` [danish_realm] ruler: `"Johan"` — → "Hans"; edit 88aa100
- `c-062bba1d` [gottorp_duchy] ruler: `"Hans"` — → "August Friedrich"
- `c-5124f8b1` [gottorp_duchy] ruler: `"Adolf"` — → "Johann Adolf"
- `c-5b823db6` [gottorp_duchy] ruler: `"Friedrich IV"` — → "Christian August"
- `c-7c0f94fe` [gottorp_duchy] ruler: `"Adolf"` — → "Johann Adolf"
- `c-94688f82` [gottorp_duchy] ruler: `"John Adolphus / Rudolph II"` — → "Johann Adolf / Rudolph II"
- `c-a451fc9e` [gottorp_duchy] ruler: `"Adolf"` — → "Johann Adolf"
- `c-b8ee82da` [gottorp_duchy] ruler: `"Adolf"` — → "Johann Adolf"
- `c-cfe50283` [gottorp_duchy] ruler: `"Adolf"` — → "Johann Adolf"
- `c-2b51aebd` [sonderburg_duchy] ruler: `"Hans"` — → "Alexander"

## E2-head-departed — finals whose head seed left the class

**E** · 71 values on 31 finals. **Legal form:** Review — the final's label names a seed no longer in its class; re-home or drop the stale values.

| field | origin | direction | values |
|---|---|---|---|
| catalog | promoted | removed | 16 |
| diameter_mm_verified | promoted | removed | 2 |
| inscription_rev | promoted | removed | 1 |
| sources | promoted | removed | 52 |

Per entity: danish_norway 52, danish_realm 12, royal_holstein 7.

- `c-05eb9690` [danish_norway] sources: `('https://en.numista.com/99194', 'Numista N#99194 — 8 Skilling - Christian IV - Norway')` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://numismaster.com/MC_110623', 'NumisMaster')` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://numismaster.com/MC_110625', 'NumisMaster')` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://numismaster.com/MC_110626', 'NumisMaster')` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc4h14)')` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://www.ngccoin.com/price-guide/world/norway-8-skilling-km-22a-1643-cuid-1094235-dui` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://www.ngccoin.com/price-guide/world/norway-8-skilling-km-26.2-1644-cuid-1099057-du` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-05eb9690` [danish_norway] sources: `('https://www.ngccoin.com/price-guide/world/norway-8-skilling-km-26.3-1644-cuid-1095583-du` — → ('https://www.danskmoent.dk/norge/nc4h14.htm', 'danskmoent.dk (Hede nc
- `c-0d78dbf8` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf4h1.htm', 'danskmoent.dk (Hede nf4h1)')` — → ('https://www.danskmoent.dk/norge/nf4h1.htm', 'danskmoent.dk (Hede nf4
- `c-108d9a7e` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc4h7.htm', 'danskmoent.dk (Hede nc4h7)')` — → ('https://www.danskmoent.dk/norge/nc4h7.htm', 'danskmoent.dk (Hede nc4
- `c-20390e5a` [danish_norway] catalog: `('bruun_lot_no', '12065')` — → ('bruun_lot_no', '14037')
- `c-20390e5a` [danish_norway] catalog: `('bruun_page', '191')` — → ('bruun_lot_no', '14037')
- `c-20390e5a` [danish_norway] catalog: `('bruun_part', 'III')` — → ('bruun_lot_no', '14037')
- `c-20390e5a` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h8.htm', 'danskmoent.dk (Hede nf3h8)')` — → ('https://www.danskmoent.dk/norge/nf3h8.htm', 'danskmoent.dk (Hede nf3
- `c-305bc5e0` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-2-speciedaler-1649-1650/?tid=97375', 'ucoin tid 97375'` — → ('https://www.danskmoent.dk/norge/nf3h9.htm', 'danskmoent.dk (Hede nf3; edit 4831c21
- `c-305bc5e0` [danish_norway] sources: `('https://www.danskmoent.dk/fr/f3h50.htm', 'Hede 51 / danskmoent.dk')` — → ('https://www.danskmoent.dk/norge/nf3h9.htm', 'danskmoent.dk (Hede nf3; edit 4831c21
- `c-305bc5e0` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h9.htm', 'danskmoent.dk (Hede nf3h9)')` — → ('https://www.danskmoent.dk/norge/nf3h9.htm', 'danskmoent.dk (Hede nf3
- `c-39e91dbc` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc4h10.htm', 'danskmoent.dk (Hede nc4h10)')` — → ('https://www.danskmoent.dk/norge/nc4h10.htm', 'danskmoent.dk (Hede nc
- `c-462fe1c6` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h67.htm', 'danskmoent.dk (Hede nf3h67)')` — → ('https://www.danskmoent.dk/norge/nf3h67.htm', 'danskmoent.dk (Hede nf
- `c-4710f90c` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h70.htm', 'danskmoent.dk (Hede nf3h70)')` — → ('https://www.danskmoent.dk/norge/nf3h70.htm', 'danskmoent.dk (Hede nf
- `c-4a435b6d` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc5h58.htm', 'danskmoent.dk (Hede nc5h58)')` — → ('https://www.danskmoent.dk/norge/nc5h58.htm', 'danskmoent.dk (Hede nc
- `c-4dda9342` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-krone-1686-1689/?tid=97316', 'ucoin')` — → ('https://www.danskmoent.dk/norge/nc5h67.htm', 'danskmoent.dk (Hede nc; edit 4831c21
- `c-4dda9342` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc5h67.htm', 'danskmoent.dk (Hede nc5h67)')` — → ('https://www.danskmoent.dk/norge/nc5h67.htm', 'danskmoent.dk (Hede nc
- `c-4fd0819b` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h69.htm', 'danskmoent.dk (Hede nf3h69)')` — → ('https://www.danskmoent.dk/norge/nf3h69.htm', 'danskmoent.dk (Hede nf
- `c-547113c3` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h68.htm', 'danskmoent.dk (Hede nf3h68)')` — → ('https://www.danskmoent.dk/norge/nf3h68.htm', 'danskmoent.dk (Hede nf
- `c-553363f8` [danish_norway] catalog: `('bruun_collection_id', '9802')` — → ('bruun_lot_no', '14055')
- `c-553363f8` [danish_norway] catalog: `('bruun_lot_no', '14057')` — → ('bruun_lot_no', '14055')
- `c-553363f8` [danish_norway] catalog: `('km', '56')` — → ('bruun_lot_no', '14055')
- `c-553363f8` [danish_norway] catalog: `('others', 'Aagaard# 67.1')` — → ('bruun_lot_no', '14055'); edit 4f22f45
- `c-553363f8` [danish_norway] inscription_rev: `"DOMINUS - PROVIDEBIT // 1659"` — → "DOMINUS - PROVIDEBIT // 1660"
- `c-553363f8` [danish_norway] sources: `('https://ikmk.smb.museum/object?id=18219604', 'IKMK Berlin 18219604')` — → ('https://www.danskmoent.dk/norge/nf3h33.htm', 'danskmoent.dk (Hede nf
- `c-553363f8` [danish_norway] sources: `('https://numismaster.com/MC_110726', 'NumisMaster')` — → ('https://www.danskmoent.dk/norge/nf3h33.htm', 'danskmoent.dk (Hede nf
- `c-553363f8` [danish_norway] sources: `('https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Sept2024_LE` — → ('https://www.danskmoent.dk/norge/nf3h33.htm', 'danskmoent.dk (Hede nf
- `c-553363f8` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h33.htm', 'danskmoent.dk (Hede nf3h33)')` — → ('https://www.danskmoent.dk/norge/nf3h33.htm', 'danskmoent.dk (Hede nf
- `c-553363f8` [danish_norway] sources: `('https://www.ngccoin.com/price-guide/world/norway-specie-daler-km-51-1658-1659-cuid-10981` — → ('https://www.danskmoent.dk/norge/nf3h33.htm', 'danskmoent.dk (Hede nf
- `c-5817298d` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc7h7.htm', 'danskmoent.dk (Hede nc7h7)')` — → ('https://www.danskmoent.dk/norge/nc7h7.htm', 'danskmoent.dk (Hede nc7
- `c-64225e47` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc7h8.htm', 'danskmoent.dk (Hede nc7h8)')` — → ('https://www.danskmoent.dk/norge/nc7h8.htm', 'danskmoent.dk (Hede nc7
- `c-6c39ea13` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h38.htm', 'danskmoent.dk (Hede nf3h38)')` — → ('https://www.danskmoent.dk/norge/nf3h38.htm', 'danskmoent.dk (Hede nf
- `c-6d2607c9` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc4h9.htm', 'danskmoent.dk (Hede nc4h9)')` — → ('https://www.danskmoent.dk/norge/nc4h9.htm', 'danskmoent.dk (Hede nc4
- `c-7db17d5e` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc7h11.htm', 'danskmoent.dk (Hede nc7h11)')` — → ('https://www.danskmoent.dk/norge/nc7h11.htm', 'danskmoent.dk (Hede nc
- `c-8aaf1d86` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc7h18.htm', 'danskmoent.dk (Hede nc7h18)')` — → ('https://www.danskmoent.dk/norge/nc7h18.htm', 'danskmoent.dk (Hede nc
- `c-9a306004` [danish_norway] catalog: `('bruun_lot_no', '12046')` — → ('bruun_lot_no', '14012')
- `c-9a306004` [danish_norway] catalog: `('bruun_page', '183')` — → ('bruun_lot_no', '14012')
- `c-9a306004` [danish_norway] catalog: `('bruun_part', 'III')` — → ('bruun_lot_no', '14012')
- `c-9a306004` [danish_norway] catalog: `('others', 'B# 1148')` — → ('bruun_lot_no', '14012')
- `c-9a306004` [danish_norway] catalog: `('others', 'B# 753')` — → ('bruun_lot_no', '14012')
- `c-9a306004` [danish_norway] sources: `('https://en.numista.com/308515', 'Numista')` — → ('https://www.danskmoent.dk/norge/nc4h5.htm', 'danskmoent.dk (Hede nc4; edit 4831c21
- `c-9a306004` [danish_norway] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1629-1630/?tid=163659', 'ucoin')` — → ('https://www.danskmoent.dk/norge/nc4h5.htm', 'danskmoent.dk (Hede nc4; edit 4831c21
- `c-9a306004` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc4h5.htm', 'danskmoent.dk (Hede nc4h5)')` — → ('https://www.danskmoent.dk/norge/nc4h5.htm', 'danskmoent.dk (Hede nc4
- `c-aa197a61` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc4h12.htm', 'danskmoent.dk (Hede nc4h12)')` — → ('https://www.danskmoent.dk/norge/nc4h12.htm', 'danskmoent.dk (Hede nc
- `c-d2897afd` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc5h57.htm', 'danskmoent.dk (Hede nc5h57)')` — → ('https://www.danskmoent.dk/norge/nc5h57.htm', 'danskmoent.dk (Hede nc
- `c-da930af4` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nf3h71.htm', 'danskmoent.dk (Hede nf3h71)')` — → ('https://www.danskmoent.dk/norge/nf3h71.htm', 'danskmoent.dk (Hede nf
- `c-00a76180` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f3h133.htm', 'danskmoent.dk (Hede f3h133)')` — → ('https://www.danskmoent.dk/fr/f3h133.htm', 'danskmoent.dk (Hede f3h13
- `c-0fd91ba5` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h111.htm', 'danskmoent.dk (Hede c4h111)')` — → ('https://www.danskmoent.dk/chr/c4h111.htm', 'danskmoent.dk (Hede c4h1; edit 4093197
- `c-3fc7d1dd` [danish_realm] catalog: `('hede_volume', 'c10h')` — edit 4093197
- `c-3fc7d1dd` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c10h10.htm', 'danskmoent.dk (Hede c10h10B)')` — edit 4093197
- `c-44fc0b29` [danish_realm] sources: `('https://www.danskmoent.dk/f5hede.htm', 'danskmoent.dk overview f5hede (Hede f5h12 — Tief`
- `c-892e7d26` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-speciedaler-1667/?tid=99108', 'ucoin')` — → ('https://www.danskmoent.dk/fr/f3h73.htm', 'danskmoent.dk (Hede f3h73A; edit bab0d82
- `c-892e7d26` [danish_realm] sources: `('https://numismaster.com/MC_65452', 'NumisMaster')` — → ('https://www.danskmoent.dk/fr/f3h73.htm', 'danskmoent.dk (Hede f3h73A; edit bab0d82
- `c-892e7d26` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f3h73.htm', 'danskmoent.dk (Hede f3h73)')` — → ('https://www.danskmoent.dk/fr/f3h73.htm', 'danskmoent.dk (Hede f3h73A; edit bab0d82
- `c-bd92f9e1` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h118.htm', 'danskmoent.dk (Hede c4h118)')` — → ('https://www.danskmoent.dk/chr/c4h118.htm', 'danskmoent.dk (Hede c4h1; edit 4093197
- `c-f4db95a5` [danish_realm] catalog: `('km', '26.1')`
- `c-f4db95a5` [danish_realm] diameter_mm_verified: `true` — → false; edit 2098ed8
- `c-f4db95a5` [danish_realm] sources: `('https://en.ucoin.net/coin/denmark-1-16-speciedaler-1640-1641/?tid=163618', 'ucoin')`
- `c-4ac05937` [royal_holstein] catalog: `('km', '627')` — edit efbc228
- `c-4ac05937` [royal_holstein] catalog: `('numista', '148397')` — edit efbc228
- `c-4ac05937` [royal_holstein] diameter_mm_verified: `true` — edit efbc228
- `c-4ac05937` [royal_holstein] sources: `('https://en.numista.com/148397', 'Numista N#148397 — 32 Skilling Dansk - Christian VII')` — → ('https://www.danskmoent.dk/chr/c7h26.htm', 'danskmoent.dk (Hede c7h26; edit efbc228
- `c-4ac05937` [royal_holstein] sources: `('https://en.ucoin.net/coin/denmark-32-skilling-1775/?tid=79090', 'ucoin')` — → ('https://www.danskmoent.dk/chr/c7h26.htm', 'danskmoent.dk (Hede c7h26; edit efbc228
- `c-4ac05937` [royal_holstein] sources: `('https://numismaster.com/MC_65148', 'NumisMaster')` — → ('https://www.danskmoent.dk/chr/c7h26.htm', 'danskmoent.dk (Hede c7h26; edit efbc228
- `c-4ac05937` [royal_holstein] sources: `('https://www.danskmoent.dk/chr/c7h26.htm', 'danskmoent.dk (Hede c7h26)')` — → ('https://www.danskmoent.dk/chr/c7h26.htm', 'danskmoent.dk (Hede c7h26; edit efbc228

## E3-own-attested-removed — a value the final's own class attests, yet removed

**E** · 13 values on 8 finals. **Legal form:** Review — a switch defect or a class value filtered later (KMM specimen drop, thinning).

| field | origin | direction | values |
|---|---|---|---|
| catalog | foundation | removed | 8 |
| sources | foundation | removed | 4 |
| sources | promoted | removed | 1 |

Per entity: danish_realm 12, royal_holstein 1.

- `c-023a9d78` [danish_realm] sources: `('https://www.danskmoent.dk/c4hede2.htm', 'danskmoent.dk overview c4hede2 (Hede c4h146 — T` — → ('https://www.danskmoent.dk/c4hede2.htm', 'danskmoent.dk overview c4he
- `dk-tid-130240` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c8h1.htm', 'danskmoent.dk (Hede c8h1A)')` — → ('https://www.danskmoent.dk/chr/c8h1.htm', 'danskmoent.dk (Hede c8h1C)
- `dk-tid-173646` [danish_realm] catalog: `('bruun_lot_no', '17093')` — → ('bruun_lot_no', '1110')
- `dk-tid-173646` [danish_realm] catalog: `('bruun_page', '64')` — → ('bruun_lot_no', '1110')
- `dk-tid-173646` [danish_realm] catalog: `('bruun_part', 'IV')` — → ('bruun_lot_no', '1110')
- `dk-tid-70760` [danish_realm] sources: `('https://www.danskmoent.dk/fr/f6h27.htm', 'danskmoent.dk (Hede f6h27C)')` — → ('https://www.danskmoent.dk/fr/f6h27.htm', 'danskmoent.dk (Hede f6h27B
- `km-452-chr-v-1699` [danish_realm] catalog: `('hede_volume', 'c5h')` — → ('hede_volume', 'f4h'); edit 214f991
- `km-795-1-chr-ix-1874` [danish_realm] catalog: `('bruun_lot_no', '17235')` — → ('bruun_lot_no', '17259'); edit 214f991
- `km-795-1-chr-ix-1874` [danish_realm] catalog: `('bruun_page', '116')` — → ('bruun_lot_no', '17259'); edit 214f991
- `km-796-1-chr-ix-1874` [danish_realm] catalog: `('bruun_lot_no', '17252')` — → ('bruun_lot_no', '17256'); edit 214f991
- `km-796-1-chr-ix-1874` [danish_realm] catalog: `('bruun_page', '119')` — → ('bruun_lot_no', '17256'); edit 214f991
- `km-796-1-chr-ix-1874` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c9h15.htm', 'danskmoent.dk (Hede c9h15A)')` — → ('https://www.danskmoent.dk/chr/c9h15.htm', 'danskmoent.dk (Hede c9h15; edit f58b867
- `km-683-4-fr-vi-1818` [royal_holstein] sources: `('https://www.danskmoent.dk/fr/f6h24.htm', 'danskmoent.dk (Hede f6h24C)')` — → ('https://www.danskmoent.dk/fr/f6h24.htm', 'danskmoent.dk (Hede f6h24E

## E4-residual — everything else

**E** · 6 values on 6 finals. **Legal form:** Review per case.

| field | origin | direction | values |
|---|---|---|---|
| catalog | promoted | removed | 3 |
| sources | promoted | removed | 3 |

Per entity: danish_realm 3, danish_norway 2, royal_holstein 1.

- `c-5dbe9824` [danish_norway] catalog: `('others', 'Aagaard# 79.4 (61-2/62-9)')` — → ('others', 'Aagaard# 79.4 (61-2/62-2)'); edit 4f22f45
- `c-c7fc4117` [danish_norway] sources: `('https://www.danskmoent.dk/norge/nc6h4.htm', 'danskmoent.dk (Hede nc6h4C)')`
- `c-963747d8` [danish_realm] sources: `('https://samlinger.natmus.dk/KMM/object/106937', 'KMM 106937 (Inv. GP 2439.170)')` — edit 88aa100
- `c-af6febe0` [danish_realm] catalog: `('sieg_hede1971', '108')` — → ('bruun_lot_no', '13112')
- `c-cd04fcb6` [danish_realm] sources: `('https://www.danskmoent.dk/chr/c4h171.htm', 'Hede 171 — 1 søsling lybsk, Glückstadt (1623`
- `c-d46a4495` [royal_holstein] catalog: `('km', 'dk:103')` — → ('km', '63'); edit efbc228

## E5-stage-N-automerge — a class merged by stage N's canonicalisation

**E** · 1 values on 1 finals. **Legal form:** Review — «Hans?» → «Hans» (unverified) let the matcher unite the KMM record with the documented Hvid class.

| field | origin | direction | values |
|---|---|---|---|
| *coin* | promoted | gone | 1 |

- `c-43ceeeff` [danish_realm] *coin*: `None`

## Hand-edit commits and where their undone values landed

| commit | date | kind | subject | undone +/− | groups |
|---|---|---|---|---|---|
| `730d93f` | 2026-05-18 | edit | data: strip *-unlisted refs from catalog + mintmaster initials from mi | +1 −0 | C0-hand-edit 1 |
| `eae75bb` | 2026-05-18 | pipeline | v2: Phase 4 — absorb_seeds_into_final_v2.py (D9 bidirectional + D17-D2 | +2 −0 | B2-moved-to-another-final 1, D1-v1-twin 1 |
| `214f991` | 2026-05-18 | pipeline | v2: rename curated → final + bootstrap_v2_final_from_v1 + match strate | +782 −0 | D3-v1-uncovered 318, B2-moved-to-another-final 209, A4-relabel 51, D2-v1-memberless 51, D1-v1-twin 15, D4-v1-own-record 13, B3-recorded-removal 10, E3-own-attested-removed 5, C0-hand-edit 5, B6-flag-class-claim 1 |
| `edf779c` | 2026-05-19 | edit | data(v2): consolidate curator+unified duplicates + dedupe sources | +0 −5 | C7-hand-deletion-returns 5 |
| `4093197` | 2026-05-19 | edit | data(v2): D40 first application — 543 D+E entries bulk-promoted | +8 −0 | E2-head-departed 4, B2-moved-to-another-final 2, C1-nominal-form 1, A2-ruler-canonical 1 |
| `05b5b5e` | 2026-05-19 | edit | data(v2): D39 first application — 535 N-cases bulk-promoted across 8 e | +5 −0 | A2-ruler-canonical 3, B2-moved-to-another-final 1, A4-relabel 1 |
| `ace1c6a` | 2026-05-19 | edit | docs+data: source-ref label convention + cleanup of 9 verbose offender | +1 −0 | C0-hand-edit 1 |
| `e157ce2` | 2026-05-19 | edit | data(v2): D37 first application — danish_norway 438 entries bulk-promo | +3 −0 | A4-relabel 2, B2-moved-to-another-final 1 |
| `f58b867` | 2026-05-20 | edit | build(v2): foundation sources list flush — same skip_first_list rule | +5 −0 | B2-moved-to-another-final 3, E3-own-attested-removed 1 |
| `577ea14` | 2026-05-23 | edit | data(v2-final): systematic re-route of 115 orphan unified entries into | +19 −0 | B2-moved-to-another-final 10, D2-v1-memberless 3, D1-v1-twin 2, A4-relabel 2, B8-bruun-anchor 1, D5-v1-citations-on-promoted 1 |
| `e210ed6` | 2026-05-24 | edit | data: restore 838 V1 curator-added sources into V2 final entries | +213 −0 | D3-v1-uncovered 117, A4-relabel 52, D2-v1-memberless 9, C0-hand-edit 4, B2-moved-to-another-final 1, D1-v1-twin 1 |
| `26c903d` | 2026-05-24 | edit | data(final): consolidate per-Hede-sub-variant V1 foundations into sing | +3 −0 | C0-hand-edit 3 |
| `e07029d` | 2026-05-26 | pipeline | fix(absorb): preserve V1 curator note + _curation_holds + backfill KM- | +8 −0 | B2-moved-to-another-final 7, B6-flag-class-claim 1 |
| `51ff425` | 2026-05-26 | edit | data: bump cache pointer — Numista BO.7 batch EF (oldenburg_county, 5  | +6 −0 | C0-hand-edit 6 |
| `9cb33bd` | 2026-05-27 | pipeline | restore-v1: V2-side list-form catalog lookup + final audit | +5 −0 | D5-v1-citations-on-promoted 4, A4-relabel 1 |
| `b9e45f7` | 2026-05-27 | pipeline | restore-v1: cross-register KM + alt-Numista merge for dual-V1 buckets | +3 −0 | A4-relabel 1, D5-v1-citations-on-promoted 1, B3-recorded-removal 1 |
| `4831c21` | 2026-05-27 | pipeline | restore-v1: hede+ruler + unique-only year+nominal+ruler matchers | +56 −0 | B2-moved-to-another-final 32, D1-v1-twin 12, D5-v1-citations-on-promoted 6, E2-head-departed 5, D3-v1-uncovered 1 |
| `10850ab` | 2026-05-27 | pipeline | restore-v1: broaden V1↔V2 matchers — lange + km+ruler+year fallbacks | +24 −0 | D5-v1-citations-on-promoted 7, B2-moved-to-another-final 6, D3-v1-uncovered 6, A4-relabel 3, C0-hand-edit 1, D1-v1-twin 1 |
| `e851d3f` | 2026-05-27 | pipeline | absorb+data: restore V1-curator year_ranges + sources to V2 final entr | +69 −0 | D5-v1-citations-on-promoted 34, A4-relabel 23, B2-moved-to-another-final 10 |
| `784179d` | 2026-05-27 | edit | fraction-infer: sub-unit-aware leading-fraction + retroactive correcti | +2 −2 | C7-hand-deletion-returns 2, C0-hand-edit 2 |
| `971e3c8` | 2026-05-30 | pipeline | build: absorb-level globally-unique-ID fallback — consolidate residual | +1 −0 | B2-moved-to-another-final 1 |
| `a293a31` | 2026-05-30 | pipeline | data: regenerate seed_unified + final after Numista dup consolidation | +3 −0 | B2-moved-to-another-final 3 |
| `a2e1952` | 2026-05-31 | edit | fix: tighten over-merge split — require no shared type-level catalog r | +11 −1 | C0-hand-edit 11, C7-hand-deletion-returns 1 |
| `bab0d82` | 2026-05-31 | pipeline | fix: split 50 over-merged different-KM members in absorb (§9.4) + guar | +14 −0 | B2-moved-to-another-final 10, E2-head-departed 3, D1-v1-twin 1 |
| `4f22f45` | 2026-06-01 | pipeline | data: §CL-3 absorb → final (7018 entries, builds clean) | +424 −0 | C0-hand-edit 6, D6-v1-values-on-promoted 3, D2-v1-memberless 3, E2-head-departed 1, E4-residual 1, B2-moved-to-another-final 1, B3-recorded-removal 1, D1-v1-twin 1 |
| `399c954` | 2026-06-03 | pipeline | data: absorb re-merged seed_unified into final — §CS propagation | +73 −19 | B3-recorded-removal 6, B6-flag-class-claim 5, B2-moved-to-another-final 2, A4-relabel 1, B1-excluded-stub-citations 1, A2-ruler-canonical 1 |
| `58f1a4b` | 2026-06-03 | edit | data: §CS fix 7 V1 bruun collection-id typos (adjacent-lot mis-cites) | +1 −0 | C0-hand-edit 1 |
| `88aa100` | 2026-06-03 | pipeline | data: absorb KMK + recovered Bruun into V2 final (9947 bulk-promoted,  | +189 −0 | A2-ruler-canonical 78, B6-flag-class-claim 62, D6-v1-values-on-promoted 29, B5-covered-other-form 9, E1-ruler-other 4, C1-nominal-form 3, E4-residual 1, B4-mintmaster-place 1 |
| `51a609c` | 2026-06-09 | edit | build: re-validate composed_of membership (evict identity-mismatched m | +1 −0 | A2-ruler-canonical 1 |
| `24b8855` | 2026-06-12 | edit | data: consolidate duplicated/truncated Aagaard refs (179 entries) | +4 −1 | C0-hand-edit 4, C7-hand-deletion-returns 1 |
| `eefddf5` | 2026-06-12 | edit | data: reclassify Frederik I 1527 Goldgulden as Rhinsk Gylden (rhinsk_g | +0 −1 | C7-hand-deletion-returns 1 |
| `0aa8b69` | 2026-06-13 | edit | data: normalise numeric catalogue indices (905 entries) | +0 −18 | C7-hand-deletion-returns 18 |
| `11f2f2a` | 2026-06-14 | edit | data: gap-fill None ruler (67) + mintmaster (258) on final from member | +17 −0 | C0-hand-edit 2 |
| `efbc228` | 2026-06-16 | pipeline | data: absorb apply — KM631/FrD'or united in royal_holstein, c7h re-hom | +25 −3 | E2-head-departed 7, D5-v1-citations-on-promoted 3, D1-v1-twin 3, C0-hand-edit 3, B5-covered-other-form 3, D3-v1-uncovered 2, A2-ruler-canonical 1, B3-recorded-removal 1, E4-residual 1, B2-moved-to-another-final 1 |
| `e8de501` | 2026-06-16 | edit | fix: home-file royal_holstein-priority + migrate 7 misfiled overlap fi | +72 −0 | D2-v1-memberless 47, B2-moved-to-another-final 21, B3-recorded-removal 3, D1-v1-twin 1 |
| `968af94` | 2026-06-17 | pipeline | data: re-absorb all entities — materialise re-flow into finals (+ reti | +12 −0 |  |
| `9a3a0e4` | 2026-06-18 | edit | data: danish_realm — fix 4 gold-coin nominals + reclassify the Soverei | +1 −1 | C1-nominal-form 1, C7-hand-deletion-returns 1 |
| `a777b9a` | 2026-06-19 | edit | data+template: normalize remaining annotated/uncertain Danish-king rul | +2 −2 | C2-ruler-regression 2, C7-hand-deletion-returns 2 |
| `917b7a6` | 2026-06-19 | edit | data: canonicalise Danish-king «Christian» ruler names to «Christian { | +6 −0 | A2-ruler-canonical 5, E1-ruler-other 1 |
| `7e95732` | 2026-06-19 | edit | data: canonicalise Danish-king «Frederik» ruler names to «Frederik {Ro | +5 −5 | C2-ruler-regression 5, C7-hand-deletion-returns 5 |
| `aab9d06` | 2026-06-20 | edit | data: merge KMM 156783 «Guldgylden» → f2h5 Guldkrone (Frederik II 1564 | +1 −0 | C0-hand-edit 1 |
| `1a2e482` | 2026-06-20 | edit | data: Ungersk Gylden → reichsdukatenfuss — fold 5 KMM specimens + prom | +2 −0 | C0-hand-edit 2 |
| `95f4d35` | 2026-06-23 | edit | data: clean Hede-3/Hede-8 over-merge residue from c5h56 (Christian V 2 | +2 −0 | C0-hand-edit 2 |
| `69255e4` | 2026-06-26 | edit | data: fold 4 confirmed Pattern-A duplicate final foundations | +5 −0 | C0-hand-edit 5 |
| `fc5a619` | 2026-06-28 | edit | data: c7h13 — restore dropped Bruun Part III (KM 651.1) source + drop  | +3 −0 | C0-hand-edit 3 |
| `d410c68` | 2026-07-09 | edit | data: foundation-reset kmk-158132 — split the 1643 Schou-58 specimen o | +1 −1 | A2-ruler-canonical 1, C7-hand-deletion-returns 1 |
| `baa587f` | 2026-07-11 | edit | data: Denmark rhinsk_gylden_fod — nominal + timeline label "Rhinsk Gyl | +5 −4 | C1-nominal-form 5, C7-hand-deletion-returns 4 |
| `16491cb` | 2026-07-12 | edit | data: exclude kmk-137189 — anomalous ¼ Portugaløser stub (danish_realm | +0 −1 | C7-hand-deletion-returns 1 |
| `8266c1e` | 2026-07-19 | edit | data: sovereign trial pieces display + km-a47 auction source | +1 −0 | C0-hand-edit 1 |
| `2098ed8` | 2026-07-29 | pipeline | data(v2): absorb — the fifteen duplicated coins render once | +22 −1 | B2-moved-to-another-final 15, B6-flag-class-claim 4, A2-ruler-canonical 1, E2-head-departed 1, D5-v1-citations-on-promoted 1 |
| `43fe1be` | 2026-08-25 | edit | data(v2): drain all 1627 pending into the unsorted pens | +324 −0 | D5-v1-citations-on-promoted 5 |
| `064bfe9` | 2026-09-19 | edit | data: backfill Danish into the existing verification notes | +9 −5 | C4-note-da-lost 5, B9-note-template-swap 4 |
| `7a831dc` | 2026-09-20 | edit | data: the last 32 verification notes on the Denmark page speak Danish | +2 −0 | C5-note-curated-text 2 |
| `a523b0f` | 2026-09-20 | edit | data: Danish for the Denmark page's generated coin notes | +78 −0 | B9-note-template-swap 78 |
| `c3bd650` | 2026-09-27 | edit | data: drop the 1514 fineness anchor from Nobelfod Phase 0 coins | +3 −0 | C5-note-curated-text 3 |
| `33e05e4` | 2026-09-28 | edit | data(v2): promote all 758 pending classes; drop 111 superseded shells | +683 −0 |  |
| `4f87b92` | 2026-10-19 | pipeline | build: absorb drops KMM citations of specimens that belong to another  | +1 −0 | B3-recorded-removal 1 |
| `0e0e287` | 2026-10-19 | edit | data: Sweden exclusions lifted - post-1523 issues join the Swedish cor | +7 −0 |  |
| `91ca8b0` | 2026-10-20 | edit | data: four KMM stub exclusions lifted — their seeds carry photos | +1 −0 | A2-ruler-canonical 1 |
