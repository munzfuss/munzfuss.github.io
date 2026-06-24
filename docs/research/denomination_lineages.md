# Denomination lineages — meta-level above Müntzfüße

> Observation captured 2026-05-25. Triggered by a danskmoent.dk passage
> on the Nobel/Rosenobel relationship; expanded into a project-wide
> structural insight that the existing data model does not yet
> formally represent. This document records the concept; concrete
> implementation (per-lineage YAML, render surface, enumeration of
> all such lineages) is deferred to a future pass.

## The observation

`https://www.danskmoent.dk/1nobel.htm` (the Hede overview page for
the Danish Nobel coinage 1496-1532) carries the passage:

> «Senere ændredes betegnelsen til Rosenobel.»  
> («Later the designation was changed to Rosenobel.»)

The page is describing the **continuity of the Noble denomination
family** across two Müntzfüße: the Hans-era Nobel (1496-1532, our
`nobel_fod`) and the Frederik II / Christian IV Rosenobel
(1584 + 1611-1629, our `rosenobel_fod`).

Reading at face value this sentence suggests a single coin family.
But the actual data tells a different metric story:

|  | `nobel_fod` (Hans-era) | `rosenobel_fod` (Frederik II + Christian IV) |
|---|---|---|
| Brutto | 14,61 g rauh | 8,994 g rauh (Christian IV); 7,69 g (Frederik II 1584 unikat) |
| Probe | 23 K 8 Grän ≈ .986 | 20 K = .833 (Christian IV); fineness unknown (Frederik II) |
| Feingewicht | 14,41 g | 7,492 g (Christian IV) |
| Englisches Vorbild (per danskmoent.dk) | Edward III/IV Noble lineage (8.97 → 7.78 g) | Edward IV Rose Noble (7,78 g) |
| Span | 36 Jahre (Hans → Frederik I.) | 1 piece (Frederik II.) + 18 Jahre Massenkarbung (Christian IV.) |
| Stoper Christian III. | nicht weitergeführt | n/a (Christian III. erst nach pause) |
| Funktion | RRR-Prestige | Christian IV. Hauptkarbung 1611-1613 = Kalmar-Krieg-Söldnerbezahlung |

Two **different Müntzfüße**, separated by ~80 years of non-carbung,
sharing only:

1. A **name family** (Nobel → Rosenobel — the «Rose» being the
   distinguishing element added in the Frederik II / Christian IV
   revival, paralleling the English Rose Noble vs Noble distinction).
2. A **denomination ancestor** in English coinage (Edward III Noble
   1344 → Edward IV Rose Noble 1465 → the Danish Frederik II /
   Christian IV Rosenobel resumption).
3. A **functional tier** — both are heavy prestige gold, well above
   contemporary daily-circulation gold (Goldgulden / Kurantdukat etc.).

The danskmoent.dk wording **collapses these into one «designation
change»**. From a Müntzfuß-research perspective (our project mission),
they are distinct standards. From a denomination-family perspective,
they are one continuous «line».

## Why this matters for project architecture

Our V2 data model currently has three structural layers:

1. **Coin** — individual specimen / catalogue type (`data/v2/final/<entity>.yml::coins[]`)
2. **Phase** — period instantiation of a Müntzfuß at a location
   (`data/v2/locations/<loc>.yml::fuss_periods.<fuss>.phases[]`)
3. **Müntzfuß** — the standard itself (`data/shared/fuesse.yml::<fuss_id>`)

What we DO NOT have, but what the Nobel↔Rosenobel relationship —
and other similar relationships in our data — implies should exist:

4. **Denomination lineage / coin family** — a sequence of issues
   that PERSISTS across Müntzfuß boundaries, documenting the
   historical continuity of a coin family.

A lineage's identity is not «one Müntzfuß» but «one coin-family
narrative». It explicitly accommodates the fact that the metric
specification (and potentially even the coin's NAME) changed inside
the same conceptual family.

### What can change inside a lineage

The continuity that defines a lineage is NOT strictly «same name».
Two distinct continuity patterns both qualify:

**Pattern A — same name, metric discontinuity.** The denomination's
name persists but the Müntzfuß underneath it changes. Example:
Nobel (Hans 1496-1532, .986 ~14,6 g) → Rosenobel (Christian IV.
1611-1629, .833 ~9 g). danskmoent.dk frames this as «Senere
ændredes betegnelsen til Rosenobel» — a designation change
rather than a metric change.

**Pattern B — different name, same metric tradition.** The
denomination is renamed while the underlying Müntzfuß and weight
class persist. Example: **Hungarian Goldgulden → Reichsdukat** —
Hans's 1481-1513 Ungersk Gylden (~3,49 g fein, .986) and the
post-1559 Reichsdukat carbung (same ~3,44 g fein, same .986) are
metrically essentially identical; the 1559 Augsburger
Reichsmünzordnung formalised the Goldgulden tradition under a new
imperial label. Our V2 model handles this informally via the
Phase-pre-I extension on `rigsdukatfod` (and `reichsdukatenfuss`
for the Reich side), but it does NOT explicitly carry the
«Goldgulden continuation» information as a structural element.

Hybrid case (rename PLUS metric change) is also possible — Krone
evolutions across Christian IV / Christian V / 1693 reform combine
both axes.

**Implication for translation.** A common temptation is to call
the layer «номінальна лінія» / «denomination line» — but that
framing implies the *denomination name* is the anchor (Pattern A
only). Goldgulden → Reichsdukat (Pattern B) shows the anchor is
something more abstract: the **coin family tradition** itself,
which can survive both metric and name changes.

## Candidate lineages in current project scope

Working through our data, the lineages that span multiple Müntzfüße:

### Nobel-Rosenobel
- `nobel_fod` (Hans 1496 → Frederik I. 1532) — 23 K, ~14,6 g
- → 80-year gap
- `rosenobel_fod` (Frederik II. 1584 unikat → Christian IV. 1611-1629) — 20 K, ~9 g
- Name connection per danskmoent.dk; metric break

### Krone (silver Tarif)
- `kronemont_chr_iv` (Christian IV. Corona Danica 1618) — 13¾ Loth, 12 ²⁵⁷⁄₇₀₀ Krone / Marck
- `kronemont` (Christian V. 1671 onwards) — different Müntzfuß
- `kronemont_fine` (post-1693 reform) — different again
- Same denomination name «Krone» across three metric standards
- Already loosely connected in our docs but no formal lineage object

### Guldkrone
- `guldkrone` (Christian IV. 1618 + Frederik III. 1655-1668) — 20 K
- Different from Rosenobel-fod (different weight / function), but both
  Christian-IV-era gold coins with names containing «Krone»
- ½-Rosenobel period nickname «Guldridder» — but actual «Guldkrone»
  is a separate denomination at separate Müntzfuß

### Kurantdukat
- `courantdukatenfuss` Phase I (Frederik IV. 1714-1717) — 81½ pieces /
  Marck, .875, 2,511 g fein
- `courantdukatenfuss` Phase II (Frederik V. 1757 onwards) — 75 pieces
  / Marck, .875, 2,728 g fein
- Same Müntzfuß ID but two phases with different metric. Borderline —
  in our model we treat this as «one Müntzfuß, two phases», which is
  defensible; the «one denomination, two standards» framing applies
  marginally because the Müntzfuß was administratively continuous.

### Goldgulden → Reichsdukat (Hungarian-Goldgulden tradition) — Pattern B exemplar
- **Pre-1559**: Hungarian-style «Goldgulden» / «Ungersk Gylden»
  (~3,49 g fein @ .986) — minted by Hans 1481-1513, Christian II.
  1513-1523, Frederik I. 1523-1533, Christian III. 1534-1559
- **1559 Augsburger Reichsmünzordnung** formalises the existing
  Hungarian-Goldgulden tradition under the new imperial label
  **«Reichsdukat»** (~3,44 g fein @ .986). Same metric tradition,
  RENAMED. Continues as the European standard gold-trade-coin into
  the 18th-19th c. (Dutch Handelsdukat, Hamburg Dukat, etc.).
- In our V2 model this is handled informally via the Phase-pre-I
  extension on `rigsdukatfod` (Danish side) / `reichsdukatenfuss`
  (Reich side) — the pre-I phase explicitly extends back to
  Hans's 1481-onwards Goldgulden carbung. The «Goldgulden» name
  itself is not modelled as a separate Müntzfuß since the metric
  is essentially continuous through 1559 (this is exactly the
  Pattern B case — name changed, metric tradition preserved).
- **Pattern B exemplar.** This lineage is the cleanest example
  of why «лінія номіналу» (denomination line) fails as a
  translation: the lineage spans a denomination RENAME and would
  be unnamed in that framing.

### Speciedaler / Speciestaler
- `9_thaler` (1566-1623) → `9_25_thaler` (1623+, Schleswig-Holstein
  Phase III etc.)
- Same denomination, distinct metric standards in different periods.
- Our timeline visualisation already shows the cross-fuss continuity
  for Speciedaler implicitly via the location yamls; no explicit
  lineage object.

### Skilling Danske
- Pre-1813 Skilling Danske: divisor of Rigsdaler Courant (`courant`
  context — `data/locations/denmark.yml::Kurantmøntfod`)
- 1813 reform: Rigsbankskilling — completely new Müntzfuß and tariff
  structure
- Same noun «Skilling Danske» before reform, then renamed
- Pure-name continuity broken at reform; functionally separate

### Krone (1873+)
- `kronefod` 1873 — Skandinavisches Münzunion gold-anchored Krone
- Conceptually unrelated to Christian IV.'s 1618 Corona Danica Krone
  (different metal era — silver-tarif then vs gold-Goldstandard now).
- Name reuse without metric continuity. This is more «name family
  reused after lineage extinction» than «one lineage».

## Why we should NOT force a lineage into the Müntzfuß identity

A natural temptation: «unify Nobel + Rosenobel into one `nobel_lineage`
with sub-Fuß phases». We should resist this for several reasons:

1. **The Müntzfuß is the metric anchor.** Phase I (Hans Nobel @ .986
   ~14 g) and Phase II (Christian IV. Rosenobel @ .833 ~9 g) are
   metrically incompatible — one CANNOT use the same fineness / per-
   Marck divisor for both. Lumping them under one Müntzfuß would force
   us to either ignore the metric difference (silent invention per
   §0) or split the Müntzfuß data model in ways the schema doesn't
   support cleanly.

2. **The pause matters.** 80 years without coinage between Frederik I.
   1532 (last Nobel) and Frederik II. 1584 (unikat Rosenobel) is a
   structural discontinuity. The Müntzfuß is dormant, then
   re-established. Treating them as one continuous standard erases
   that gap.

3. **The English model differs.** Hans's Nobel relates loosely (and
   per §0 the causal modelling claim was deliberately removed) to
   the Henry VII Sovereign 1489 / late Edward IV Rose Noble tradition.
   Christian IV.'s Rosenobel relates to the same Rose Noble lineage
   but reaches back to Edward IV 1465 explicitly per danskmoent.dk's
   «Rose noble fra 13-1400-tallet». Different points in the English
   evolution; different functional roles in the Danish economy at
   each point.

4. **Function changed.** Hans's Nobel = Hans/Christian II/Frederik I
   prestige issue, no documented circulation. Christian IV.'s
   Rosenobel = Kalmar-War mercenary pay, documented massive coinage
   1611-1613. Same name, different economic function.

## Proposed future model

A **lineage** is a higher-order object with:

- `lineage_id`: stable string key (e.g. `nobel_rosenobel`)
- `display_name`: i18n family name (DE: «Münzfamilie» / EN: «coin
  family» / UK: **TODO — see terminology note below**)
- `member_fusses`: ordered list of Müntzfuß IDs that constitute the
  lineage chronologically (`[nobel_fod, rosenobel_fod]`)
- `description`: i18n prose narrating the connection (what's shared:
  name OR metric tradition OR functional tier; what's different:
  metric / name / period / iconography — see «What can change»
  section above)
- `references_inline`: per-lineage refs

### Terminology note — UK translation pending

**The Ukrainian rendering is unsettled and needs a final decision
before any rendered artefact emits one of these terms.**

«Лінія номіналу» / «номінальна лінія» seemed reasonable for the
Nobel↔Rosenobel case (same name, metric change), but **fails for
Pattern B** (Goldgulden → Reichsdukat / Dukat) where the
denomination NAME itself changes inside the same tradition. The
anchor isn't the nominal — it's the coin-family tradition.

Candidates considered (per user direction):

- **«родина (монет)»** — biology-style «family». Captures both
  Pattern A and B. Paralles German «Münzfamilie». Currently the
  strongest candidate, used informally in the prose above.
- **«вид»** — biology-style «species». Narrower than «родина» in
  taxonomy. Possibly too specific for the lineage layer.
- **«тип»** — «type». Heavily overloaded in numismatic Ukrainian
  («тип монети» = catalogue type / variant). Reusing it for the
  higher-order lineage would create terminology collision with
  existing Hede/KM/Sieg type-level usage.

Other rejected candidates:

- «лінія» — risks confusion with «династична лінія» / «лінія
  наслідування» (royal line).
- «лінійка» — colloquial / marketing register, violates §2a
  academic tone.
- «лінія номіналу» / «номінальна лінія» — fails for Goldgulden →
  Dukat (name change inside the same tradition).
- «рід» — slightly archaic, less common in modern numismatic
  Ukrainian.

**Decision deferred to the lineage-schema implementation pass.**
At that point we'll have a fuller enumeration of candidate
lineages across the project (including the German side —
Reichsthaler family, Konventionsthaler family, etc.) and can
evaluate which UK term reads cleanly across all of them.

Render surface options:
- Landing page: a «lineages» section showing the family tree
- Per-location page: a sidebar widget on each member-Fuß card
  pointing to the lineage parent
- Per-lineage page (own URL): full history of the family
- Or simply: a `lineage_id` field on each Müntzfuß card that
  surfaces as a hyperlink to lineage documentation

Implementation cost: schema extension + lineage YAML files +
render-surface choice + i18n + cite migration. Several sessions of
work. Worthwhile if the lineage concept proves useful across many
families, not just Nobel-Rosenobel.

## Action items deferred

1. **Enumerate all candidate lineages** systematically across the
   project's coin data. The list above is partial — there are likely
   more «name-continuity, metric-discontinuity» cases in the German
   side too (Reichsthaler vs Konventionsthaler vs Speciesthaler etc.).
2. **Decide on render surface**. Many small cards on landing? One
   per-lineage page? Sidebar on Müntzfuß cards? Need a mockup pass.
3. **Schema design**. Add `Lineage` model in `scripts/lib/schema.py`
   with the fields above.
4. **Cite-migration**. Same inline-refs system applies — lineages
   carry their own `[ref:KEY]` cites against `refs_pool.yml`.
5. **Build integration**. Render-time resolution of lineage links
   on Müntzfuß cards.

For now, this document captures the conceptual layer. Future work
can reference back to it when the «name continuity vs metric
discontinuity» distinction becomes relevant elsewhere in the data.

## Related project surfaces

- `data/shared/fuesse.yml::nobel_fod` — `<code>rosenobel_fod</code>`
  cross-ref in the description (project-internal scaffolding)
- `data/shared/fuesse.yml::rosenobel_fod` — `<em>Nicht zu
  verwechseln</em> mit <code>nobel_fod</code>` disambiguation
  language already present
- `docs/research/sources/coins_of_denmark_academia.md` — Ruckser's
  compilation lists Nobel + Rosenobel as separate coins under
  separate kings, NOT as one lineage. Confirms our metric-anchored
  separation is consistent with at least one secondary source.
- `docs/research/sources/jensen_1972_danish_money_14th_century.md` —
  the 14th-century gap context (1332-1377 no Danish coinage) is
  itself an extreme version of the same «discontinuity inside a
  conceptual family» phenomenon at the country level.

## Source for the trigger

The single danskmoent.dk passage that prompted this observation:

> «Senere ændredes betegnelsen til Rosenobel.»

URL: <https://www.danskmoent.dk/1nobel.htm>

This is a one-line gloss on the page that links the two coin
families. The phrase is intentionally compact and does not claim
metric continuity — it says only «the designation was later
changed», which is consistent with our model (different Müntzfuß,
same denomination-family name).

Pool-key suggestion for citing this insight in project prose:
`danskmoent-1nobel` (already in pool — same page that backs the
`nobel_fod` Galster catalogue claims).
