# Work plan — «lübischer Münzfuß» card with King Hans' silver (Denmark page)

> **Goal.** A finished Fuß card for the silver and billon of King Hans (1481–1513) — card,
> left block, «details» (instruments, phase description, closing), timeline bar, coin table
> with sourced notes — at the level of `nobel_fod` / `rhinsk_gylden_fod` (curator-approved
> models, 2026-10-12 / 2026-10-13), in de / en / uk / da.
>
> **Evidence base:** `hans_silver_1481_1513.md` (dossier). **This file is the working
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

## 1. Research completion

| ✓ | Step | Output |
|---|---|---|
| ☑ | 1.1 Inventory, sources, recomputation, options | `hans_silver_1481_1513.md` (commit `1a06455`); sources cached `scripts/cache/danskmoent/hans_1481_1513/` (`a803eda37`) |
| ☑ | 1.2 Record D1–D6 in the dossier §8 | dossier |
| ☐ | 1.3 **Territorial status table for D3**, each with a source: Denmark proper + Skåne; Gotland / Visby (Danish crown); Norway (union kingdom, håndfæstning 1483 — consumed by the page via `danish_norway`); archbishopric of Nidaros (Gaute Ivarsson, Erik Valkendorf); Sweden 1497–1501 (union kingdom — **not** dependent on Denmark → proposal: Hans' Ørtug off the page, relocate to `sweden`); Schleswig (Danish fief) vs Holstein (imperial fief) for Duke Frederik's Hohlpfennige — which duchy and mint the pieces belong to | dossier §, then ⏸ curator confirms each row |
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
| ⏸ | 3.1 Key and display string. Proposal: key `luebischer_muenzfuss`; name per §2 tier 1 — the sources write «lübischer Münzfuß» (Jesse), CLAUDE.md lists «Lübischer Müntzfuß», Danish «lybsk Møntfod»; one string in all languages | curator picks the string |
| ☐ | 3.2 Grid: what defines the standard on the card — the Schilling 103½ to the 9-lot Cologne mark (Rezess 1468 = 1492) as `grid_stops` / `fineness_standard 0.5625`, or the Mark lübsch as unit; computed fine weights (§5 of the dossier) | fuesse.yml |
| ☐ | 3.3 `events`: `first_adoption` / `std_start` / `std_end` / `first_mint` / `last_mint` / `demonetisation` per scope (anywhere vs Denmark); the end for Denmark = håndfæstning 22 July 1513 (+ Blicher grid), marked indirect if so | fuesse.yml + schema check |
| ☐ | 3.4 `grundwerte.rows`: decree rows (Rezess 1468/1492; håndfæstning 1483; håndfæstning 1513 as the end) and the period row «Period I (1481–1513) · King Hans» with short parameters | fuesse.yml |
| ☐ | 3.5 Card text `rechnungsfraktionen` (`description_in_card: true`): founding, role (Skilling = Lübeck Schilling; Hvid as small coin «densche drelinge»; Gylden 2 → 2½ M d), cessation (1513/1514), cross-refs `[fuss:rhinsk_gylden_fod]`, `[fuss:nobel_fod]`, `[fuss:8_5_gylden_fod]` | fuesse.yml, 4 languages |
| ☐ | 3.6 `fractions` (Mark = 16 ß = 192 Pf; Hvid 4 Pf; Søsling 6 Pf; Skilling 12 Pf) | fuesse.yml |

## 4. The Denmark page — `data/v2/locations/denmark.yml`

| ✓ | Step | Output |
|---|---|---|
| ☐ | 4.1 `fuss_order` position (before `8_5_gylden_fod`) and timeline bar (year span, layers, bar_title) | denmark.yml |
| ☐ | 4.2 `fuss_periods`: `spec`, `instruments`, `pdate_label`, `closing_label`, `closing` | denmark.yml |
| ☐ | 4.3 `phases[luebischer_muenzfuss]`: one phase I (1481–1513) — title + description (Rigsrådet 1481–83 prelude, Hvid-only start (Gribshunden 1495), Skilling / Søsling later, debasement to 1512, Gylden 2 → 2½ M d, mints in Denmark, Norway, Gotland, archbishops per D3) | denmark.yml |
| ☐ | 4.4 Cross-references from neighbours: Nobelfod / Guldgyldenfod period I (silver coinage of the same king), `8_5_gylden_fod` (successor) | 4 languages |

## 5. Citations — `data/shared/refs_pool.yml` (skill `cite-source`)

| ✓ | Step | Output |
|---|---|---|
| ☐ | 5.1 One key per passage for every claim in 3.4–4.4 (Wilcke 7-1 s. 134, 139–140, 143, 144; 7-2 s. 149, 152, 155; Galster galkult; Galster 1947; Eriksson 2017 tab. 7/9/16; Gullbekk s. 3–4, 8; Holst; Jesse 1424/1492/1501/1506; Ingvardson 2022); reuse existing keys (`galster-nobel-hans-ingen-moentordning`, `wilcke-1950-haandfaestning-1513`, …) | refs_pool |
| ⏸ | 5.2 Archive copies: find Wayback snapshots; Save Page Now only with the curator's yes per batch | refs_pool |
| ☐ | 5.3 Translations after every quote in de/en/uk; da original for Danish | refs_pool + prose |

## 6. Coins

| ✓ | Step | Output |
|---|---|---|
| ☐ | 6.1 Classify the type-attributable records (Galster 29–36, 141–142, 148–162 per D3, Rigsrådet G 22, archbishops) into `luebischer_muenzfuss` / phase I, with `kind` (Skilling, Søsling: kurant? Hvid: scheide? — decide from the sources and note the reason) | `classification_decisions/{danish_realm,danish_norway}.yml` → absorb |
| ⏸ | 6.2 The ~120 KMM specimens without a type key (D4: no merge) — do they render as single rows in the table now, or stay in `seed_unsorted` until a merge decision? | curator |
| ☐ | 6.3 Per-case review of counterfeits / piefort (D5): `kmk-278927`, `kmk-318049`, `kmk-734756`, + any found — table with source text, for the curator's verdict each | this file / dossier |
| ☐ | 6.4 Data anomalies: `kmk-643973` (Hans 1517 in KMM source), `unified-dk-bruun-3837` year range 1512–1515, Norwegian-Schou records in `danish_realm`, KMM «galster» values 3/15/23/41/57B/115 — trace (`trace_coin why`), then report | dossier §4.3 |
| ⏸ | 6.5 Entity moves per D3 (Swedish Ørtug → `sweden`; Norwegian records → `danish_norway`; Duke Frederik's pieces per 1.3) — RELOCATE via `v2-merge-coins` after the curator confirms each | merge_decisions |
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

- 2026-10-15 — plan created after D1–D6.
