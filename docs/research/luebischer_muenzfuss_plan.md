# Work plan — «lübischer Münzfuß» card with King Hans' silver (Denmark page)

> **Goal.** A finished Fuß card for the silver and billon of King Hans (1481–1513) — card,
> left block, «details» (instruments, phase description, closing), timeline bar, coin table
> with sourced notes — at the level of `nobel_fod` / `rhinsk_gylden_fod` (curator-approved
> models, 2026-10-12 / 2026-10-13), in de / en / uk / da.
>
> **Fuß dossier:** `luebischer_muenzfuss.md` (the standard, parameters, instruments, inclusion verdicts). **Evidence survey:** `hans_silver_1481_1513.md`. **This file is the working
> checklist**: tick a step in the same commit that completes it; add, split or reorder steps
> as the work shows what is needed; record every curator decision here with its date.
>
> Status: ☑ done · ◐ in progress · ☐ to do · ⏸ waiting for the curator · ✖ dropped (say why).

## 0. Curator decisions (2026-10-15)

| # | Question (dossier §8) | Decision |
|---|---|---|
| D1 | Separate Fuß? | **A — global card «lübischer Münzfuß»**, Denmark-page phases local |
| D2 | Phases | **one phase** for Hans for now; a split may emerge later |
| D3 | Other issuers in Hans' years | **include only if their territory belonged to Denmark directly or as a vassal**; issuers not dependent on Denmark do not go on the Denmark page |
| D4 | ~120 KMM specimens without Schou | **do not merge for now** |
| D5 | Counterfeits / piefort in KMM | **provisionally keep**; review each case for a final verdict |
| D6 | Mission lower bound | **yes** — Hans' silver (from 1481) enters the Danish scope |
| D7 | Name (2026-10-15, 2nd round) | munzfuss site: «Lübischer Müntzfuß» **if** that was the period German spelling; Danish page (all languages): «Lybsk Møntfod» **if** it matches Danish usage of the 15th–16th c.; otherwise the form of that time. Finding (dossier §10.3): no «-Fuß / -fod» compound is attested for the 15th–16th c. — ⏸ curator to choose |
| D8 | KMM specimens without Schou (2026-10-15) | **all go on the page** as their own rows for now; merging later |
| D9 | Sweden (2026-10-15, revised same day) | different base mark and standard → treat Swedish union coinage **separately, on another page**; own entity file; not on the Denmark page unless a per-case verdict says otherwise |
| D10 | Holstein / Duke Frederik (2026-10-15) | coins of a duke who is at the same time king of Denmark go on the page; any hierarchical tie + a common (compatible) standard → include; each case examined |
| D12 | Inclusion rule (2026-10-15) | written into SOURCES §13.16 (amendment) + CLAUDE.md §9 pointer: tie to Denmark AND compatible standard; different base mark argues against; small drift does not; every case curator-approved |
| D13 | NGC pfennige (2026-10-15) | **re-attribute**: MB#5 → Christian I. 1460–1481, MB#8 → Frederik I. 1523–1533 — done (seed errata + final) |
| D15 | Norway (2026-10-15, 3rd round) | **include from 1483**, the small differences (weight base, lighter Hvide) set aside for now; may be revisited |
| D16 | Sweden test (2026-10-15) | compatible = the local count per local mark makes the coin equal (≈) to a Danish one counted on the Cologne mark; incompatible → off the page. Applied: Ørtug of Hans and Christian I incompatible → relocated to `sweden` (dossier §10.5) |
| D17 | Hans' Holstein Blaffert (2026-10-15) | **yes**, on the page (king = duke; Lübeck–Hamburg standard) — once found in the data |
| D18 | MB#8 (2026-10-15) | **yes** — relocate `royal_holstein` → `danish_realm` |
| D14 | Name (2026-10-15) | variant **a**: «Lübischer Müntzfuß» (munzfuss), «Lybsk Møntfod» (Danish page, all languages) as scholarly names, like Nobelfod |
| D19 | Name collision with the 1726 34-Mark-Fuß (2026-10-15) | **D14 stands** — Hans' standard is «Lybsk Møntfod» (Danish page); the collision is set aside until the 1726 card (`11_333_thaler`) is reworked — both are Lübeck standards, at different times, so it may not be critical |
| D20 | Card name (2026-10-15) | **«11½-Markfod»** main name (all languages, global), **«Lybsk Møntfod»** as `historical_name`; supersedes the name strings of D14 (curator's own term, after Bobzin's «N-Mark-Fuß» measure; 11½ = Schilling 103½ / 9-lot mark) |
| D11 | Save Page Now | **yes** (2026-10-15) — standing for this work |

## 1. Research completion

| ✓ | Step | Output |
|---|---|---|
| ☑ | 1.1 Inventory, sources, recomputation, options | `hans_silver_1481_1513.md` (commit `1a06455`); sources cached `scripts/cache/danskmoent/hans_1481_1513/` (`a803eda37`) |
| ☑ | 1.2 Record D1–D6 in the dossier §8 | dossier |
| ☑ | 1.3a Norway: on the Danish standard from 1483 — dossier §10.4; D15 include from 1483 |
| ◐ | 1.3 **Territorial status table for D3** (facts in dossier §10.1; per-land placement still ⏸), each with a source: Denmark proper + Skåne; Gotland / Visby (Danish crown); Norway (union kingdom, håndfæstning 1483 — consumed by the page via `danish_norway`); archbishopric of Nidaros (Gaute Ivarsson, Erik Valkendorf); Sweden 1497–1501 (union kingdom — **not** dependent on Denmark → proposal: Hans' Ørtug off the page, relocate to `sweden`); Schleswig (Danish fief) vs Holstein (imperial fief) for Duke Frederik's Hohlpfennige — which duchy and mint the pieces belong to | dossier §, then ⏸ curator confirms each row |
| ☐ | 1.4 Lübeck standards from Jesse in full: Rezesse 1424 (with Denmark), 1468, 1492 (31 articles), 1501/1504/1506 — exact figures, page / passage locators; the 19,392 g question | dossier §5; `instruments/` dossiers if tier A (see 1.6) |
| ☐ | 1.5 Remaining sources: Galster 1972 *Unionstidens udmøntninger* (paper — gap or library), Märcher 2018 (paper — gap), Ernst 1940 (danskmoent `ernst/hanshvid.htm`, cached), Hauberg 1891 Gotland, Risvaag / Lohne 2010 (Nidaros mint), Wilcke 7-1 s. 32–147 read end to end for anything missed, Eriksen 1949 (`artikler/skilltal.htm`) | dossier; cache + SOURCES for each new one |
| ☐ | 1.6 Instruments: håndfæstning 1483 (register row ☑), Wendish Rezesse 1468 / 1492 / 1506, Danish-Hanseatic treaty 1424 — decide which get an `instruments/` dossier; add them to `instruments/PLAN.md` | `instruments/`, register |
| ☐ | 1.7 Score the dossier (`research-dossier`) → ≥ 8 | score block in this file |

## 2. Scope

| ✓ | Step | Output |
|---|---|---|
| ☐ | 2.1 CLAUDE.md «Mission temporal scope»: Danish lower bound for silver = 1481 (Hans), with the reason (D6) | CLAUDE.md |
| ☐ | 2.2 Check what else keys on the 1514 bound (timeline axis start, `year_from` filters, audits) | note here |

## 3. The Fuß definition — `data/shared/fuesse.yml`

| ✓ | Step | Output |
|---|---|---|
| ☑ | 3.1 (name settled: D14 + D19) Key and display string (D7 → D14: «Lübischer Müntzfuß» / «Lybsk Møntfod»; dossier §10.3). Key `luebischer_muenzfuss`. Two display strings → the name may need to differ by **site profile** (munzfuss vs danskmoent) — check whether the build supports a per-site name; if not, add it | curator picks the strings; build support |
| ☑ | 3.2 Grid: what defines the standard on the card — the Schilling 103½ to the 9-lot Cologne mark (Rezess 1468 = 1492) as `grid_stops` / `fineness_standard 0.5625`, or the Mark lübsch as unit; computed fine weights (§5 of the dossier) | fuesse.yml |
| ☑ | 3.3 `events`: `first_adoption` / `std_start` / `std_end` / `first_mint` / `last_mint` / `demonetisation` per scope (anywhere vs Denmark); the end for Denmark = håndfæstning 22 July 1513 (+ Blicher grid), marked indirect if so | fuesse.yml + schema check |
| ☑ | 3.4 `grundwerte.rows`: decree rows (Rezess 1468/1492; håndfæstning 1483; håndfæstning 1513 as the end) and the period row «Period I (1481–1513) · King Hans» with short parameters | fuesse.yml |
| ☑ | 3.5 Card text `rechnungsfraktionen` (`description_in_card: true`): founding, role (Skilling = Lübeck Schilling; Hvid as small coin «densche drelinge»; Gylden 2 → 2½ M d), cessation (1513/1514), cross-refs `[fuss:rhinsk_gylden_fod]`, `[fuss:nobel_fod]`, `[fuss:8_5_gylden_fod]` | fuesse.yml, 4 languages |
| ◐ | 3.6 `fractions` (Mark = 16 ß = 192 Pf; Hvid 4 Pf; Søsling 6 Pf; Skilling 12 Pf) | fuesse.yml |

## 4. The Denmark page — `data/v2/locations/denmark.yml`

| ✓ | Step | Output |
|---|---|---|
| ☑ | 4.1 `fuss_order` position (before `8_5_gylden_fod`) and timeline bar (year span, layers, bar_title) | denmark.yml |
| ◐ | 4.2 `fuss_periods`: `spec`, `instruments`, `pdate_label`, `closing_label`, `closing` | denmark.yml |
| ☑ | 4.3 `phases[luebischer_muenzfuss]`: one phase I (1481–1513) — title + description (Rigsrådet 1481–83 prelude, Hvid-only start (Gribshunden 1495), Skilling / Søsling later, debasement to 1512, Gylden 2 → 2½ M d, mints in Denmark, Norway, Gotland, archbishops per D3) | denmark.yml |
| ☐ | 4.4 Cross-references from neighbours: Nobelfod / Guldgyldenfod period I (silver coinage of the same king), `8_5_gylden_fod` (successor) | 4 languages |

## 5. Citations — `data/shared/refs_pool.yml` (skill `cite-source`)

| ✓ | Step | Output |
|---|---|---|
| ◐ | 5.1 One key per passage for every claim in 3.4–4.4 (Wilcke 7-1 s. 134, 139–140, 143, 144; 7-2 s. 149, 152, 155; Galster galkult; Galster 1947; Eriksson 2017 tab. 7/9/16; Gullbekk s. 3–4, 8; Holst; Jesse 1424/1492/1501/1506; Ingvardson 2022); reuse existing keys (`galster-nobel-hans-ingen-moentordning`, `wilcke-1950-haandfaestning-1513`, …) | refs_pool |
| ◐ | 5.2 Archive copies (D11 yes). Done 2026-10-15: Eriksson 2017 → `20261015100138`, hansgals → `20261015100433` (SPN); existing: Gullbekk `20251006175259`, Gribshunden `20250907030329`, galshans `20260122081043`, holst `20250916081200`, Sømod c1holst `20250808133935`. Remaining: the rest as keys are written | refs_pool |
| ☐ | 5.3 Translations after every quote in de/en/uk; da original for Danish | refs_pool + prose |

## 6. Coins

| ✓ | Step | Output |
|---|---|---|
| ☐ | 6.1 Classify the type-attributable records (Galster 29–36, 141–142, 148–162 per D3, Rigsrådet G 22, archbishops) into `luebischer_muenzfuss` / phase I, with `kind` (Skilling, Søsling: kurant? Hvid: scheide? — decide from the sources and note the reason) | `classification_decisions/{danish_realm,danish_norway}.yml` → absorb |
| ☐ | 6.2 The ~120 KMM specimens without a type key: classify them all into the card as single rows (D8); no merge (D4) | classification_decisions |
| ☐ | 6.3 Per-case review of counterfeits / piefort (D5): `kmk-278927`, `kmk-318049`, `kmk-734756`, + any found — table with source text, for the curator's verdict each | this file / dossier |
| ☐ | 6.4 Data anomalies: `kmk-643973` (Hans 1517 in KMM source), `unified-dk-bruun-3837` year range 1512–1515, Norwegian-Schou records in `danish_realm`, KMM «galster» values 3/15/23/41/57B/115 — trace (`trace_coin why`), then report | dossier §4.3 |
| ◐ | 6.5a **Sweden (D9, D16):** 8 records relocated to `sweden` (`_cross_entity.yml`), entity description rewritten. Earlier text:  proposal per case — Hans' Ørtug (Galster 230–238), Christian I and Christian II Swedish pieces out of `danish_realm` into a Swedish union entity that the Denmark page does not consume. Old text:  a union-era Swedish entity on the `danish_norway` model (proposal: «Kingdom of Sweden under the union king», Christian I 1457–64, Hans 1497–1501, Christian II 1520–23) in `issuing_entities.yml`; the existing `sweden` entity is post-1523 and `out_of_scope` and its description says union issues stay in `danish_realm` — rewrite it; add the new entity to Denmark's `consumes_entities` with a year window; relocate Hans' Ørtug (Galster 230–238) and any Christian I / II Swedish pieces — via `v2-merge-coins` RELOCATE | entities, denmark.yml, merge_decisions |
| ⏸ | 6.5b Norwegian-Schou records sitting in `danish_realm` → `danish_norway` | merge_decisions |
| ☑ | 6.5c The two NGC pfennige (D13 done; MB#8 relocated to `danish_realm`, D18) in `royal_holstein` (dossier §10.2): MB#5 → Christian I per Sømod (disputed), MB#8 → King Frederik I (Galster 79); neither is Hans-era. Curator: re-attribute ruler / years, or leave | final via curation surface |
| ☐ | 6.5d (D17 yes) Hans' own Holstein Blaffert (Oldenburg bars; Sømod D103, Jesse 299) — search our data and sources; card row only if the curator places Holstein coin of the king on the Denmark page for this period | — |
| ☐ | 6.6 Coin notes: sourced note per type row (as on the Guldgyldenfod rows) — nominal literal per §1, assay / account figures with citation, no specimen trivia | final via notes surface |

## 7. Verification and quality gates

| ✓ | Step | Output |
|---|---|---|
| ☐ | 7.1 `build.py --validate-only`; full build; `--site danskmoent`; read the rendered section in all four languages | — |
| ☐ | 7.2 `fuss-description` SCORE → ≥ 8 (target as Nobelfod / Guldgyldenfod) | score block here |
| ☐ | 7.3 `fuss-cite-audit --fuss luebischer_muenzfuss --location denmark` → no real high findings | report here |
| ☐ | 7.4 `audit_i18n.py`, `audit_prose.py`; city names by ruling power (Malmø, København, Aalborg, Visby, Bergen, Oslo, Nidaros) in the texts written | — |
| ☐ | 7.5 Timeline: the bar shows status / mint layers like the gold bars; tooltips | screenshot for the curator |

## 8. Close-out

| ✓ | Step | Output |
|---|---|---|
| ☐ | 8.1 `instruments/FUSS_REVIEW_FINDINGS.md` — entries opened / closed by this work | — |
| ☐ | 8.2 `docs/handoff.md` | — |
| ☐ | 8.3 Later, not in this plan unless the curator asks: Christian I / Christoffer / Erik of Pomerania silver under the same card (Hvid since c. 1440) | — |

## Log

- 2026-10-15 — Card built (3.1–3.5, 4.1, 4.3): `fuesse.yml::luebischer_muenzfuss` (name «Lübischer Müntzfuß», grid 103½ Schilling / rough Cologne mark @ 9 Lot = Jesse's 15 June 1468 treaty, reaffirmed 1483/1492; rows 1468 · Haandfæstning 1483 · Period I · Haandfæstning 1513; card text; fractions 2 / 1 / ½ Schilling only — Hvid has no Lübeck counterpart in 1468, open; events 1481–1513, std_end approx); denmark.yml: name override «Lybsk Møntfod», spec, pdate_label, phase I, timeline bar (order 7.5, timeline from 1480). Six new pool keys (Jesse ×2, Wilcke 7-1 s. 134/143, Eriksson s. 5 ×2). Not yet: instruments blocks, closing, coins (6.x), neighbour cross-refs (4.4).

- 2026-10-15 — D19: collision deferred, D14 stands; 1726 sense traced to MKL 1888 (dossier); 15th-c. sense = Grautoff 1836 / Jesse / Wilcke 7-1 s. 143.

- 2026-10-15 — Bobzin: «lübischer Münzfuß» also names the 1726 34-Mark-Fuß (our `11_333_thaler`) — D14 name collision put to the curator (step 3.1 ⏸).

- 2026-10-15 — Bobzin (hagen-bobzin.de) cached; Fuß dossier §3.1a: «N-Mark-Fuß» measure, proposal for step 3.2 = 11½ Mark lübisch per fine mark (1468/1492).

- 2026-10-15 — Fuß dossier `luebischer_muenzfuss.md` created.

- 2026-10-15 — relocation applied (`_cross_entity.yml`, `issuing_entity: sweden` override needed: the Stockholm mint maps to `danish_realm` before 1523); single-member RELOCATE enabled in the merger (`5da257c`). Found while re-flowing, NOT ours, left at HEAD: `unified-kmk-692607` (Christian 3 Sechsling) — the committed KMM seed would widen 1546 → 1534–1559 on the next re-flow (seeds committed without merge+absorb); `erzbisthum_bremen_verden` final has a hand-set `display: false` on a source that absorb drops. Both for the curator / the KMM session.

- 2026-10-15 — D15–D18: Norway from 1483; Sweden incompatible → 8 Ørtug relocated to `sweden`; MB#8 → `danish_realm`.

- 2026-10-15 — D9 revised, D12–D14; inclusion rule in SOURCES §13.16 + CLAUDE.md §9; NGC pfennige re-attributed; Norway §10.4.

- 2026-10-15 — D7–D11; dossier §10 (status of the lands, the NGC pfennige, period name); Sømod 2002 cached; two SPN captures.

- 2026-10-15 — plan created after D1–D6.
