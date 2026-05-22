# Pre-1541 Danish silver — current seed inventory + classifier gap (2026-05-21)

> **Companion to `wilcke_1514_1541_specs.md`** (ordinance specs from Wilcke 1950)
> and `denmark_pre_1541_source_survey.md` (source-pool reconnaissance).
> This file is a CURRENT-STATE snapshot: how many specimens of each
> pre-1541 silver type are sitting in `seed_unsorted` as of 2026-05-21,
> what the auto-classifier does with them, and how they map to the §BF
> roadmap in `wilcke_1514_1541_specs.md` §8.
>
> Triggered by user question 2026-05-21 «якою була срібна стопа в данії
> до 1541 року?» — the answer is «no project-defined Fuß yet — known
> gap, blocked on §AZ paper-source promotion». This file documents the
> gap concretely so the next §BY cycle can quantify scope before
> starting implementation.

## §1. Current seed inventory

**Pre-1541 Danish-realm silver / billon specimens currently sitting in
`fuss: seed_unsorted` in `data/v2/final/danish_realm.yml`: 91 entries.**

Group counts by ruler + metal:

| Ruler | Silver | Billon | Total |
|---|---:|---:|---:|
| Christian II (1513-1523) | 6 | 15 | **21** |
| Christian II / Christian III (transition) | 0 | 1 | 1 |
| Frederik I (1523-1533) | 7 | 21 | **28** |
| Christian III pre-Møntordning (1534-1540) | 13 | 28 | **41** |
| **Total** | **26** | **65** | **91** |

Top denomination buckets across the 91:

| Count | Denomination | Notes |
|---:|---|---|
| 13 | 1 Skilling | spans C-II, F-I, C-III pre-1541 — same name, different fineness tier per ruler |
| 9 | 4 Skilling | full-Kurant tier (.875 / 14 Lod per Galster) |
| 8 | 1 Søsling | sub-Skilling Scheide tier |
| 6 | 2 Skilling | mid tier |
| 6 | 4 Skilling (1⁄12) | Numista-formatted variant of «4 Skilling» |
| 6 | 14 Penning | Frederik I 1524 specific (per Wilcke 7-2 p. 187 «14 %» small-change subtype) |
| 4 | 2 Skilling (1⁄24) | Numista-formatted |
| 3 | Halv Sølvgylden | Frederik I 1531-1532 + Christian II |
| 3 | 2 Mark | Christian III Grevens Fejde 1535 Aarhus + Roskilde |
| 3 | 1 Skilling (1⁄48) | Numista-formatted |
| 2 | Silver Gulden / 1 Gulden | Christian II 1518 + 1523 Sølvgylden (Bruun + Numista parallel records) |
| 2 | 1 Hvid | C-II 1535 København + similar |
| 2 | 2 Mark (⅔) | Klippe variant |
| 2 | 1 Joachimstaler | C-III 1537 Copenhagen, 3 weight tiers (per Wilcke 7-3 p. 242) |

The Sølvgylden series itself (the Hauptkurant tier of the period) is
represented by the «Silver Gulden» / «1 Gulden» / «Halv Sølvgylden» /
«1½ Sølvgylden» / «¼ Sølvgylden» entries — ≈ 8-10 distinct catalog
types across C-II, F-I, and a few C-III pre-1541 issues.

## §2. Galster-attested metric pattern (from the cache)

Specs harvested from `scripts/cache/danskmoent/galster/*.json` (per
the cache survey 2026-05-21) confirm the consistent Hauptkurant /
Scheidemünze split across all three rulers:

| Specimen | Year | Mint | Fineness | Brutto g | Fein g | Tier |
|---|---|---|---:|---:|---:|---|
| **Christian II — Galster** |
| 1 Hvid (c2g) | 1513 | Malmø | .246 (4 Lod) | 1.04 | 0.26 | billon |
| 1 Skilling (c2g) | 1516-1517 | Malmø | .375 (6 Lod) | 2.61 | 0.98 | Scheide |
| **1 Sølvgylden (c2g-38)** | 1516, 1518, 1523 | Malmø | **.875 (14 Lod)** | **27.06** | **≈ 23.68** | **Hauptkurant** |
| **Frederik I — Galster (royal)** |
| 1 Skilling (f1g) | 1525, 1531 | Malmø + Kbh | .319 (≈5 Lod) | 2.40 | 0.77 | Scheide |
| **4 Skilling u.år** | — | Malmø | **.875** | **5.23** | **≈ 4.58** | **Hauptkurant** |
| **4 Skilling 1532** | 1532 | Kbh | **.875** | n/a | n/a | **Hauptkurant** |
| **½ or 1 Mark 1529** | 1529 | Kbh | **.875** | n/a | n/a | **Hauptkurant** |
| 1 Hvid u.år | — | Kbh | .250 (4 Lod) | 0.77 | 0.19 | billon |
| **Frederik I — Galster (Husum ducal-zone)** |
| 2 Skilling 1514 | 1514 | Husum | .75 | n/a | n/a | dual-zone Hauptkurant |
| 2 Skilling 1523 | 1523 | Gottorp | .469 | 4.17 | 1.96 | Mid-tier |
| 1 Skilling u.år | — | Gottorp | .5 | n/a | n/a | Mid-tier |
| 1 Skilling 1514, 1516 | 1514-1516 | Husum | .563 | n/a | n/a | Mid-tier |
| 4 Skilling 1514 | 1514 | Husum | **.906 (14½ Lod)** | n/a | n/a | **Hauptkurant (Schleswig)** |
| 8 Skilling 1514 | 1514 | Husum | **.906** | n/a | n/a | **Hauptkurant (Schleswig)** |

**Two converging signals:**

- **Royal-mint Hauptkurant (Sølvgylden / Mark / 4 Skilling Kbh + Malmø)
  = .875 / 14 Lod** across all three rulers 1514-1540.
- **Schleswig ducal-zone Hauptkurant (Husum 1514 4/8 Skilling) = .906
  / 14½ Lod** — the same fineness floor Christian III later adopts
  realm-wide in the 1541 Møntordning (per `moentordning_1541.md` §4.1
  + `wilcke_1514_1541_specs.md` §3).

The transition 1540 → 1541 in royal coinage is thus a **.875 → .906
upgrade** (14 Lod → 14½ Lod, a ~1.9 % fineness lift), with the new
.906 figure inherited from the pre-existing Schleswig ducal standard.

## §3. Classifier behaviour 2026-05-21

Running `auto_classify_seed_unsorted.py --entity danish_realm` against
the 91 pre-1541 silver specimens currently produces:

- **0 hits via `denomination_anchor`** — the §BV-cycle rule table
  (`Rhinsk Gylden` / `Rosenobel` / `Nobel` / `Ungersk Gylden`) was
  designed for the gold tier. Sølvgylden / Mark / Skilling / Hvid all
  fall through.
- **0 hits via `delta_math` for the Hauptkurant tier** — there is no
  Fuß in `fuesse.yml` whose grid yields ~23.7 g fein per Sølvgylden
  or ~4.6 g fein per 4 Skilling. The closest existing Fuß
  (`8_daler_fod`) has soll fein 26.494 g / Daler — a 14 %
  delta, well outside the ±2 % envelope.
- **Scattered `delta_scheide` / `delta_no_fit` for sub-Skilling
  specimens** — Hvid + Søsling drop into Scheidemünze classification
  on whichever sibling Fuß is closest by year-filter, but the
  resulting assignment is arbitrary (the actual parent Fuß doesn't
  exist).

Net effect: **all 91 pre-1541 silver specimens stay in `seed_unsorted`
indefinitely** until the §BY cycle (this proposal) lands new Müntzfuß
definitions.

## §4. Mapping to the §BF roadmap

The `wilcke_1514_1541_specs.md` §8 roadmap proposed 4 new Müntzfüße.
Mapping our current seed inventory against each:

### 4.1 `8_5_gylden_fod` (1514-1523)

- **Anchor**: Møntordning af Sommeren 1514 (Dines Blicher Brev Malmö) +
  Norge-Forordning 3. August 1514 + Sjælland åbent Brev 24. August 1515.
- **Metric (Wilcke 7-2 p. 152-153)**: Sølvgylden 8½ stk/M, 14 Lod
  (.875), ~27.5 g brutto / ~24 g fein. Skilling 96/M, 5¾ Lod (.359),
  2.436 g brutto / 0.875 g fein. Hvid 222/M, 4½ Lod (.281).
- **Phases** (per dossier roadmap):
  - A1 — 1514-1517 baseline (ordinance-compliant)
  - A2 — 1518-1522 Klipping debasement
  - A3 — 1523 final Sølvgylden consolidation (mass mintage pre-deposition)
- **Current seed coverage**: 21 specimens (15 billon + 6 silver) —
  including Sølvgylden 1516/1518/1523, Skilling 1514-1525, Hvid 1513,
  Klipping 18-Penning 1518, plus Visby + Landskrona + Ribe outliers.

### 4.2 `8_gylden_fod` (1524-1531/32)

- **Anchor**: 25 February 1524 royal ordinance, København (Wilcke 7-2
  p. 184-187). Verbatim: «*Vi Fr. ... at slaa, i Guld: Nobler (den
  vegne Mark skal holde 23½ Karat og skraade 16 Stkr.), Rinske Gylden
  (18 Karat, 72 Stkr.) ...*»
- **Metric**: Sølvgylden 8/M, 14 Lod (.875), 29.232 g brutto /
  25.578 g fein. Mark Danske 22/M (12 ß), 14 Lod, 10.629 g brutto.
  4 ß 78/M, 14 Lod, 3.0 g brutto. 4-Hvid ß 96/M, 5 Lod 2 grän (.319),
  2.438 g brutto. Hvid 300/M, 4 Lod.
- **Phases** (per dossier roadmap):
  - A1 — 1524-1531 royal Copenhagen ordinance baseline
  - A2 — 1527-1531 Malmö Goldgulden parallel track (separate Rhinsk-Gylden
    line, already covered by `rhinsk_gylden_fod` Phase 0 extension TBD)
- **Current seed coverage**: 28 specimens (21 billon + 7 silver) —
  Sølvgylden series (¼, Halv, 1, 1½) 1531-1532, 4 Skilling 1532, Mark
  1529, 14 Penning 1524 (the «14 %» small-change subtype), Skilling
  1525-1531.

### 4.3 `frederik_i_husum_fod` (Schleswig-Holstein ducal-zone, 1514-1533)

- **Anchor**: Frederik I as Duke of Schleswig pre-king reign
  (1490s-1523) + post-accession continuation (1523-1533). Husum +
  Gottorp mints under mintmaster Jørgen Drewes. Per Wilcke 7-2 p. 186.
- **Metric**: Mark lybsk 13/M, 14½ Lod (.906), 18.0 g brutto /
  16.31 g fein. ½ Mark 26/M, 14½ Lod, 9.0 g brutto. ¼ Mark 52/M,
  14½ Lod. 4 ß lybsk 59/M, 6 Lod 1 Qvent (.391), 3.98 g. Husumdaler
  1522 6½/M, 14½ Lod, 28.9-38.0 g (two weight variants).
- **Phases** (per dossier roadmap):
  - A1 — 1514-1522 Frederik-I-as-Duke royal Husum baseline
  - A2 — 1522 Husumdaler tariff issue (the «sværeste» + «almindelig» variants)
  - A3 — post-1523 continuation into Frederik I's king phase (Husum
    + Gottorp 1523-1533)
- **Current seed coverage**: ~6-10 specimens — Husum 1514 Mark + ½ Mark
  (Bruun-14708 + 14709), Gottorp 2 Skilling 1523, Doppelschilling 1526.
  Some overlap with `8_daler_lybsk_fod` (1547+) but **distinct
  Müntzfuß generation** — Husum-fod 1514 is the SEED of the Schleswig
  lineage that the 1547 Flensborg Bestalling formalises.

### 4.4 `christian_iii_grevens_fejde_fod` (1534-1540)

- **Anchor**: Counts' Feud civil war 1534-1536, mintage continuing to
  1539. Master Mårtens regnskab table (Wilcke 7-3 p. 242).
- **Metric**: NOT a single Fuß but a CASCADE of debased variants:
  Joachimsdaler 1537 8/M 14½ Lod (.906) + 4.19 M dd metalværdi
  (Christian III's first heavy-Daler issue, 4 years before the 1541
  Møntordning); 2 M Klippinge in three sub-variants (10/8/7 Lod);
  4 ß in three sub-variants (5/4/3½ Lod); 2 ß at 3 Lod (.188); 1 ß
  at 2½ Lod (.156); Rhinske Gylden at 17⅓ Karat (.722).
- **Phases** (per dossier roadmap):
  - Option A — single Fuß with multiple weight-tier phases (preferred:
    cleaner structurally)
  - Option B — multiple sub-Fuß for each fineness-variant (rejected:
    over-fragments the data)
- **Current seed coverage**: 41 specimens (28 billon + 13 silver) —
  2 Mark 1535 Aarhus + Roskilde, 8 Skilling 1535, 1 Mark 1535 multi-mint,
  Joachimstaler 1537 (3 weight tiers per Bruun lots 1005/13060/11165),
  ½ Joachimstaler 1537 (Bruun-4279), plus mass Skilling / Søsling /
  Hvid 1534-1540.

## §5. Implementation cost estimate

Based on the §BV cycle as a comparator (8 §BV Müntzfüße defined +
8 §BV closures, executed across ~3 sessions 2026-05-20 to 2026-05-21):

| Sub-task | Effort | Blocked on |
|---|---|---|
| Define 4 Müntzfüße in `fuesse.yml` with full grundwerte + fractions + events + DE/EN/UK descriptions | Medium-large | Source-research is COMPLETE (dossier §1-4 above) |
| Add 4 entries to `denmark.yml` fuss_order + timeline.bars + fuss_periods + phases | Medium | None |
| Add 4 denomination_anchor rules to `auto_classify_seed_unsorted.py` (Sølvgylden, 14 Penning, Joachimsdaler, Husum-Mark) | Small | None — pattern proven in §BV cycle |
| Promote 91 specimens out of seed_unsorted via classifier `--apply` | Small | Classifier rules need to land first |
| Add bibliography refs (Wilcke 1950 §1+§2+§4+§5; Galster 1965; Jensen-Skjoldager 2021 if specimen-cited) | Small | Existing ref29 (Wilcke 1950) reusable; add ref41-ref44 as needed |

**Net estimate: 1-2 sessions** if all 4 Müntzfüße land in a single
batch (similar pattern to the §BV cycle).

## §6. Cross-references

- Existing dossiers (sources):
  - `docs/research/wilcke_1514_1541_specs.md` — full ordinance specs
    + §8 §BF roadmap
  - `docs/research/denmark_pre_1541_source_survey.md` — per-source
    coverage matrix + harvest cost
  - `docs/research/moentordning_1541.md` — the 1541 Møntordning
    dossier (the «what comes after»)
  - `docs/research/christian_iii_danish_coinage_1534_1572.md` —
    historical context for the Christian III pre-1541 phase
- Existing data:
  - `data/seed/bruun/denmark_pre_1541.yml` — 38 Bruun lots in scope
    (per `wilcke_1514_1541_specs.md` §7)
  - `data/v2/final/danish_realm.yml` — 91 seed_unsorted specimens
    surveyed in §1 above
- Existing tickets:
  - **§BV** (closed 2026-05-21) — 8-Fuß cycle that proved the implementation
    pattern; the §BY cycle below reuses the same shape
  - **§AZ** (long-running, paper-source-blocked) — Galster + Jensen-Skjoldager
    promotion that would land the c3h21-c3h22 Flensborg specimens; partial
    overlap with §BY's `frederik_i_husum_fod` Husum 1514 + Gottorp 1522
  - **§BF** (closed 2026-05-20) — Christian III 1541 dalerfod implementation;
    the §BY cycle is the «what comes before» chronologically
