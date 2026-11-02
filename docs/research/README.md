# docs/research/

Topical research notes — depth-first investigations on specific
coins, periods, or analytical questions that span multiple sessions
and don't fit the other doc slots.

## What lives here

Each file is a **standalone research dossier** on one subject. Captures:

- All evidence assembled (verbatim quotes, source URLs, cache
  references, our internal data inventory).
- Computed metrics (Δ-from-Soll, tariff vs metal calculations, etc.).
- Pattern comparisons with adjacent issues.
- Classification analysis with alternative proposals.
- Open decisions / pending verdicts.

### The one file that is NOT a dossier

**[`ordinances_register.md`](ordinances_register.md)** — a register, not an
investigation: every coinage ordinance, edict, recess and treaty the project
cites, Danish-Norwegian in §1 and Imperial in §2, each with what it sets, its
`refs_pool` key where one exists, and where to read it. §3 lists the ~70
instruments our own text already discusses but nobody has written up yet, with
the file that discusses each.

**Look there before searching the web for an ordinance** — and search the
harvested texts with `scripts/kb/kb.py search` (recipe: `scripts/kb/README.md`). It also carries the
two rules that cost this project real rework: an instrument states a TARGET
while an assay states an OUTCOME, and karat is the primary value with the
permille only its conversion.

The per-Fuß findings of the dossiers are collected in **[`instruments/FUSS_REVIEW_FINDINGS.md`](instruments/FUSS_REVIEW_FINDINGS.md)** (read before sorting `seed_unsorted`).
The register's rows point at **[`instruments/`](instruments/README.md)** — one
dossier per act (`<yyyy>_<slug>.md`, fixed nine-section template in that
folder's README). `moentordning_1541.md` predates the folder and stays here.

## Index — every dossier in this folder

**Start here for the silver standard before 1622:** the two chronologies give the formula series year by year and
point to the detailed dossiers. Read them before opening a period dossier or searching the web.
Every new dossier gets a row here in the same commit (`tests/test_research_index.py` fails otherwise).

### Chronologies (entry points)

| File | Covers |
|---|---|
| [`luebeck_standard_chronology_1226_1622.md`](luebeck_standard_chronology_1226_1622.md) | Lübeck / Wendish coin formulas 1226–1622, denomination × act table, levels per fine mark |
| [`danish_standard_chronology_1396_1541.md`](danish_standard_chronology_1396_1541.md) | Danish coin formulas under the Lübeck orientation 1396–1541: acts, assays, rates, the three kinds of tie, end-point candidates (§5, curator decision pending); §2i fineness spread within a type; §2j Erik VII's sterling — Lübeck system, not English (with the 1406 «V̶ = 4½» emendation) |

### Danish and Lübeck silver before 1541

| File | Covers |
|---|---|
| [`wendischer_muenzverein_c1400.md`](wendischer_muenzverein_c1400.md) | the Wendish system c. 1365–1424 that Denmark took up |
| [`mark_lybsk_mark_dansk.md`](mark_lybsk_mark_dansk.md) | Mark lübisch vs Mark dansk c. 1300–1514, the ratio and why two |
| [`gotland_gote.md`](gotland_gote.md) | the gote and Gotlandic reckoning c. 1340–1450; Danish reckoning c. 1450–1490; «gullandsk mønt» again c. 1500/1510–1565 |
| [`luebischer_muenzfuss.md`](luebischer_muenzfuss.md) | the Lübeck standard and King Hans' silver 1481–1513 (accepted periodisation §0.6, assays §3) |
| [`luebischer_muenzfuss_plan.md`](luebischer_muenzfuss_plan.md) | work plan for the lübischer Münzfuß card |
| [`hans_silver_1481_1513.md`](hans_silver_1481_1513.md) | Hans' silver and billon: standard, sources, data |
| [`hans_rates_1481_1513.md`](hans_rates_1481_1513.md) | Gulden / Lübeck money / Hvid / Skilling rates 1481–1513 and the silver they imply |
| [`eriksson_2017_assays.md`](eriksson_2017_assays.md) | XRF assays 1448–1523 (Eriksson; Heljeback 1400–1448 noted) matched to our data |
| [`sh_ducal_zone_husum_1514.md`](sh_ducal_zone_husum_1514.md) | Schleswig-Holstein ducal silver 1474–1547 |
| [`wilcke_1514_1541_specs.md`](wilcke_1514_1541_specs.md) | Wilcke 1950's ordinance specifications 1514–1541 |
| [`moentordning_1541.md`](moentordning_1541.md) | the Møntordning of 20 Sept 1541 |
| [`christian_iii_danish_coinage_1534_1572.md`](christian_iii_danish_coinage_1534_1572.md) | Christian III and early Frederik II coinage 1534–1572 |
| [`denmark_pre_1541_source_survey.md`](denmark_pre_1541_source_survey.md) | sources for pre-1541 Denmark other than Hede |
| [`pre_1541_silver_seed_inventory.md`](pre_1541_silver_seed_inventory.md) | pre-1541 silver in our seeds (2026-05-21 snapshot) |
| [`cologne_mark_weight_16c.md`](cologne_mark_weight_16c.md) | the Cologne mark in 16th-c. Denmark: 230 g vs 233,855 g |

### Gold standards

| File | Covers |
|---|---|
| [`nobel_fod.md`](nobel_fod.md) | Danish gold Nobel 1496–1532 |
| [`burgundian_gold_real_1487.md`](burgundian_gold_real_1487.md) | the Burgundian gold real of 1487, model of the Nobel |
| [`rhinsk_gylden_fod.md`](rhinsk_gylden_fod.md) | the Rhenish gold-gulden standard, German and Danish tracks |
| [`frederik_i_gottorp_goldgulden_dating.md`](frederik_i_gottorp_goldgulden_dating.md) | dating of Frederik I's Gottorp Goldgulden (Galster 122) |
| [`ducat_origins.md`](ducat_origins.md) | where the northern ducat standard comes from |
| [`de_reichsdukatenfuss.md`](de_reichsdukatenfuss.md) | the imperial ducat standard 1340–1876 |
| [`dk_dukat_portugaloeser_fod.md`](dk_dukat_portugaloeser_fod.md) | Ungersk Gylden, Dukat, Portugaløser |
| [`danish_royal_gold_1560_1648.md`](danish_royal_gold_1560_1648.md) | Danish royal gold 1560–1648 |
| [`f2_guldmoent_1584_gavesaet.md`](f2_guldmoent_1584_gavesaet.md) | Frederik II's 1584 gold set |
| [`daler_klippe_1604.md`](daler_klippe_1604.md) | Christian IV's Daler-Klippe gold 1604–1605 |
| [`courantdukatenfuss.md`](courantdukatenfuss.md) | Courantdukatenfuß |
| [`pistolen_fuss.md`](pistolen_fuss.md) | Pistolen-Fuß |
| [`vereinsgoldmuenze.md`](vereinsgoldmuenze.md) | Vereinsgoldmünze (Krone) |

### Later silver and the Krone

| File | Covers |
|---|---|
| [`9_thalerfuss.md`](9_thalerfuss.md) | 9-Thalerfuß / Reichsmüntzfuß |
| [`krone_muentzfuesse.md`](krone_muentzfuesse.md) | Krone-Müntzfüße 1618–1771 |
| [`dk_kronefod_1873_research.md`](dk_kronefod_1873_research.md) | Danish Kronefod 1873–1914 |
| [`dk_kronefod_unity_analysis.md`](dk_kronefod_unity_analysis.md) | Kronefod — one standard or two |
| [`denmark_fuesse_year_boundaries.md`](denmark_fuesse_year_boundaries.md) | year boundaries of the Denmark-track Füße 1497–1873 |

### Locations, entities, method

| File | Covers |
|---|---|
| [`altona.md`](altona.md) | Altona — Münz- und Bankwesen |
| [`hamburg.md`](hamburg.md) | Hamburg — Münz- und Bankwesen |
| [`duchy_of_schleswig_entity.md`](duchy_of_schleswig_entity.md) | the Duchy of Schleswig as a V2 entity |
| [`schleswig_flensborg_status_1350_1460.md`](schleswig_flensborg_status_1350_1460.md) | who held Schleswig and the town of Flensborg 1350-1460, under which title (Flensborg coins on the Denmark page) |
| [`denomination_lineages.md`](denomination_lineages.md) | denomination lineages above the Füße |
| [`hierarchical_metal_tiers.md`](hierarchical_metal_tiers.md) | metal tiers within one Fuß (convention) |
| [`mint_year_transitions.md`](mint_year_transitions.md) | mint year-aware classification dates |
| [`numismaster_dk_sh_1514_1914_harvest_surface.md`](numismaster_dk_sh_1514_1914_harvest_surface.md) | NumisMaster harvest surface DK / SH |
| [`ordinances_register.md`](ordinances_register.md) | register of every coinage act (not a dossier, see above) |

## How it differs from other doc surfaces

| Surface | Purpose | Mutability |
|---|---|---|
| `docs/research/<topic>.md` | **Depth-first dossier on one subject** | Append-only as research advances; closed when the subject is fully resolved into data + TODO Done entries |
| `docs/notes/YYYY-MM-DD.md` | Day-level session journal | Immutable per-day |
| `docs/SOURCES.md` §13 | Short per-source quirks log | Append-only entries |
| `docs/DECISIONS.md` | ADR-style rationale for non-obvious choices | Append-only |
| `docs/TODO.md` | Open work items + Done log | Items move Open → Done |

Research notes are **substrate** — the place where evidence is
collected before it gets distilled into a TODO decision, an ADR, a
SOURCES quirk, or rendered coin-table prose. Once a research subject
is fully resolved (decision made, coins reclassified, references
filed), the dossier stays as the audit trail of what was considered
and why.

## When to create a new dossier

Spawn one when:

- A pending decision (typically a 🟡 TODO entry) accumulates evidence
  that doesn't fit in a single TODO entry body without bloating it.
- Multiple external sources need to be assembled, cross-quoted, and
  weighed before the decision can land.
- The analytical reasoning chain runs more than a few paragraphs and
  is worth preserving as the canonical answer to «why did we decide
  X for this subject?».

If the subject is a one-line decision with one source → ADR in
`DECISIONS.md` is enough. If it's a source quirk → `SOURCES.md §13`.
If it's a single-line audit task → keep in TODO. Research dossiers
are for the cases where the evidence + analysis is itself a
deliverable.

## File naming

`<topic_slug>.md` — descriptive snake_case identifier. Examples:

- `daler_klippe_1604.md` — Christian IV's 1604 gold tariff Klippen
- `kronemont_1618_tariff.md` (hypothetical) — Krone-Mønt tariff history
- `glueckstadt_9_fuss_continuation.md` (hypothetical) — Glückstadt's
  retention of the 9-Fuß standard after 1622

No date in the filename — research notes are subject-keyed, not
date-keyed (unlike `docs/notes/YYYY-MM-DD.md`).

## Closure / lifecycle

When the subject is fully resolved:

- The dossier stays — it remains the audit trail.
- Add a closing section at the end documenting how the question was
  resolved (which Fuß category was chosen, which TODO entry closed
  the work, etc.) with the closing commit SHA.
- Cross-references from the relevant TODO Done entry / ADR back to
  the dossier so future readers can find the full reasoning.

The dossier does NOT get moved to `docs/archive/` — it stays at
`docs/research/` indefinitely as live reference for «what did we
already research on this topic».
