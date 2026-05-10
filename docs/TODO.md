# Pending audits and longer-term TODO

> **Read this at session start** — the entries below are open audit items
> that have not been actioned. CLAUDE.md links here so they don't get
> forgotten across sessions. When an item is done, move it to the
> "Done" section at the bottom (with the commit SHA) so we have a record.

## Open

### L. Schleswig-Holstein + Denmark consolidation campaign  *(opened 2026-05-10)*

A coordinated multi-pass effort to bring the SH and Denmark locations
to «published-quality» state before the next location takes priority.
The nine sub-tasks below are tightly coupled — many depend on
upstream completion (the territorial-attribution sweep before the
data audit, etc.) — and should be worked through roughly in the
listed order.

1. **Process all IKMK candidates for SH and Denmark.** Run
   `scripts/match_ikmk_locations.py` for both locations and walk the
   produced `_match_<loc>.md` cards bucket-by-bucket: strict_match
   (merge per §9a), fuzzy_match (visual confirm + merge), new_lange_variant
   (decide: new entry or extend existing), weak_candidate (manual call),
   no_match (defer). The Sonderburg-Sub-variant work this session
   covered batches 1–4 of SH; the rest of the SH index plus the
   entire DK index remain.

2. **Search for additional sources for the Danish coins; verify
   that Hede / danskmoent.dk has been harvested successfully and
   exhaustively.** danskmoent.dk indexes Hede catalog pages at
   `c{ruler}h{N}.htm` (per-type) and `c{ruler}hede{N}.htm` /
   `c{ruler}hede{N}.htm` overview pages. Confirm we have a cache
   of every Hede page covering coins in our DK catalog (no missing
   ruler-eras), and that the cross-link to YAML coins is wired
   (a `catalog.hede` field where missing). Subsumes part of TODO K.

3. **Triage all remaining `seed_unsorted` coins in denmark.** The
   Bruun bulk import seeded coins under `seed_unsorted` when no
   confident phase / fuss could be assigned. Walk the list (already
   tracked under TODO D for the broader hamburg+lubeck+denmark
   scope, but bring the DK part to completion as part of this
   campaign).

4. **Move all genuinely-Danish coins from SH to denmark.** Royal-
   Danish issues (Christian IV, Frederick III, Christian V, etc.)
   minted in Copenhagen / Helsingør / Christiania currently living
   in `data/locations/schleswig_holstein.yml` should migrate to
   `data/locations/denmark.yml`. Cross-check `mint` and
   `issuing_entity` fields; anything that is `royal_holstein` is a
   deliberate SH-territorial issue (Glückstadt under Christian IV
   stays in SH); anything that is plain Danish royal goes to DK.

5. **Show all Denmark-related SH coins on the Danish page.** SH
   coins issued by the Danish Crown for SH-territory (Glückstadt
   Reichsthalers under ChrIV, Schleswig-Holstein-dänisch Mark/Marck
   etc.) historically circulated as part of Danish coinage and a
   reader on the DK page would expect to find them. Decide the
   mechanism — preferably *not* a YAML copy. Options to consider:
   (a) a Jinja-side cross-include that pulls a filtered view of
   SH's `royal_holstein`-issuing coins into a new section on
   `denmark/<lang>/index.html`; (b) extracting those coins into a
   shared file `data/shared/dk_sh_dual_register.yml` and including
   from both location pages. The end-reader sees one view per
   location; the data lives once.

6. **Move all SH-territorial coins from denmark to SH.** The
   mirror of (4): any coins currently in `denmark.yml` that are
   actually SH-territorial issues (e.g. struck in Altona by the
   Danish Crown but for the duchies, not for the kingdom) belong
   in `schleswig_holstein.yml`.

7. **Verify that all SH and Denmark coins sit in the correct fuss,
   category, and phase.** Walk every coin in both files and confirm
   `fuss` (per §8.1 / §8a), `kind` (kurant / scheide / tarif /
   gedenk per §6), and `phase` (per the location's phase definitions
   and §8.2). The Sonderburg-Kipper rows on §8.1 boundaries are
   particular candidates for review.

8. **Per-coin data audit.** For every coin in both files, walk every
   listed source and confirm that (a) the data published in the
   source matches the data on the coin row, AND (b) every data
   point on the coin row that the source documents is present.
   Catches both transcription errors (Numista digit-swap pattern
   from TODO K) and missed enrichments (source published a
   diameter or fineness we didn't transcribe). Done criterion:
   audit-script `scripts/audit_per_coin_sources.py` that flags
   discrepancies, then per-row remediation pass.

9. **Audit of all rendered prose.** All `note`, `description`,
   `verification_note`, and phase-prose fields across both
   `data/locations/schleswig_holstein.yml`,
   `data/locations/denmark.yml`, and the matching
   `*-references.yml` files. Check: register (CLAUDE.md §2a),
   period orthography (§2), reader-voice vs analyst-voice (§0a /
   §0z), no-invention (§0), inline-citation hygiene (§5), and
   uk Cyrillic-transliteration trap (§2a). The corpus has
   accumulated ~ a year of prose under varying voice discipline;
   a sweep is overdue.

**Estimated effort.** Each sub-task is a multi-hour to multi-day
piece of work. Expected total: 1–2 weeks of focused sessions. Open
sub-items as their own TODO letters once they reach the active
working tier.

---

### K. Systematic Numista vs. Hede cross-check  *(opened 2026-05-09)*

**Surfaced during.** Three independent investigations during the
weight-spread audit (this session) found Numista publishing weights
that disagree substantially with Hede authoritative specs (via
danskmoent.dk):

  | Coin | Numista weight | Hede spec | Δ |
  |---|---:|---:|---:|
  | km-79-chr-v-1693 (4 Skilling Dansk) | 1.224 g | 1.951 g (Hede 128) | +59 % |
  | km-110-chr-v-1693 (1 Krone) | 21.98 g | 22.272 g (Hede 125 B) | +1 % |
  | km-128-chr-v-1787 (10 Schilling Courant) | 8.428 g | 6.129 g (Hede 42) | −27 % |

The km-79 and km-128 cases were egregious: Numista's value lined up
with a *different* coin's weight (km-79: matches the 2-Skilling
KM#78 spec; km-128: matches the 1/3-Speciedaler fein-weight of
KM-130, suggesting denomination conflation). Numista's fineness on
km-79 also showed a digit-swap error (.347 vs Hede's .437).

In every case Hede + ucoin + (where present) Bruun agreed on the
correct value, and Numista was the outlier. This is consistent with
CLAUDE.md §5's «Numista — useful for catalog numbers and rough
data, but user-edited, treat with some skepticism» — but the
specific failure mode (denomination cross-contamination,
digit-swap) suggests a population of similar errors across the
Danish royal billon / Schilling-class corpus.

**Background.** Hede covers Danish royal coinage 1541-1814
exhaustively — every type has a `c{ruler}h{N}.htm` page on
danskmoent.dk with `Bruttovægt`, `Finhed`, `Finvægt` figures and
mintmaster + Schou refs. We have direct verification this URL
pattern works (km-79 / km-110 / km-128). Hede sits at tier 2 of our
source hierarchy (after coin inscription / museum); Numista at
tier 5.

**Done criterion.** Audit script
`scripts/audit_numista_vs_hede.py` (to be written) that:

  1. For every coin in `data/locations/*.yml` where `catalog.numista`
     is set AND a Hede ref is known (either in `catalog.hede` or
     parseable from sources), fetch the Numista cache + fetch the
     Hede page (URL pattern `c{ruler}h{N}.htm` derivable from
     ruler-era + Hede number).
  2. Compare published weight + fineness. Flag spreads ≥ 5 % as
     candidates for the per-coin Hede-correction pass.
  3. Output a triage list (similar in shape to `_match_<loc>.md`):
     coins where Numista is likely wrong, coins where they agree,
     coins where Hede ref is missing and needs lookup.

Then a second pass: for each flagged coin, apply the same
correction shape used on km-79 / km-128 — Hede authoritative,
ucoin/Bruun confirming, Numista retained-but-flagged with
`(likely transcription error — see note)` source suffix.

Note: the population is bounded by «coins with Hede ref». For
locations where Hede applies (denmark, schleswig_holstein,
lauenburg), that's most entries. For the SH-territorial-duchies
(Sonderburg, Gottorf), Hede may not apply (Lange Vol II is the
authority) — the audit must distinguish.

**Estimated effort.** Audit-script + first triage report: ~1 h.
Per-coin Hede-correction pass: ~5-10 min per coin × N flagged.
Total depends on how many coins have the cross-contamination
pattern — probably 20-50 SH/DK entries based on the sample so far.

---

### J. Bruun parser + cross-match: two latent bugs from km-165/KM-166 audit  *(opened 2026-05-09)*

**Surfaced during.** Audit of `km-165-fr-iv-1698` (Schleswig-Holstein-Gottorp
1 Mark 1698 Tönning, Lange-430A) revealed Bruun lot `III/12210` had been
mis-attached as an orphan weight (22.0 g) to km-165 even though the lot is
KM-**166** / Lange-**430AA** (the sister 2 Mark, separate Krause type per §9.3).
The KM-166 type is genuinely missing from our YAML and has to be reconstructed
from Bruun-cache data because the cross-matcher absorbed it into km-165 instead
of spawning a new entry.

Two underlying defects in `scripts/bruun_parser/` + `scripts/cache/bruun/cross_match.py`:

1. **`refs`-extractor truncates double-letter catalog suffixes.**
   Bruun lot 12210 body explicitly says «Lange-430AA», but the parsed
   `refs` shows `{'Lange': '430A'}`. The regex stops after one trailing
   letter (likely `Lange-(\d+\w)` style). All Lange-/Hede-/Sieg- variants
   that use double-letter suffixes (e.g. AA, AB, BA) silently lose the
   second letter. Risk: future bulk-cross-match operations alias different
   types onto the same parsed catalog token.

2. **`cross_match.py` single-match path doesn't gate on KM-token parity.**
   When a Bruun lot finds exactly one candidate coin via the year + denom
   + non-KM-token heuristic, the matcher emits `cat: A` and links the lot
   to that coin without verifying `lot.refs.KM == coin.catalog.km`. The
   §9.3 compatibility filter introduced in commit `a5dd778` fires only on
   multi-match (`cat: B`/`D`) cases, so single-match KM-mismatches like
   12210→km-165 (KM 166 vs 165) bypass the §9.3 cleanup entirely.

**Done criterion:**
  - Parser regex updated to capture full catalog suffix (e.g. `Lange-(\d+[A-Z]+)`),
    re-run `scripts/bruun_parser/02_parse_lots.py`. Verify no other
    Lange-AA/AB collapses exist by diffing the regenerated cache.
  - `cross_match.py` extended so single-match path also calls
    `lot_compatible_with_coin()` (or equivalent KM-token assertion) before
    emitting `cat: A`. Re-run `scripts/bruun_parser/04_cross_match.py`.
  - Audit pass: any newly-flagged D-cases (lots that lose their A-classification
    after the parity check) get triaged like the original §9.3-cleanup
    (commit `ffbf458`/`a5dd778`).
  - Cross-check the four Bruun-PDF cache (parts I–IV) for any other
    parser-truncated-suffix collisions; expected handful, not hundreds.

**Estimated effort.** Parser regex + re-run cache: ~15 min. Match-logic
update + re-run + audit triage: ~1 h depending on how many additional
single-match-mismatches the parity check surfaces.

---

### I. Restructure `\n`-joined source labels in scalar metric fields  *(opened 2026-05-08)*

**Background.** Several `weight_rough_g[].source` (and likely `fineness[].source` /
`diameter_mm[].source`) entries use a YAML literal-block string with embedded
`\n` to join multiple primary sources for the same value, e.g.:

```yaml
weight_rough_g:
  - {value: 28.893, source: "Hede 39A\nNumista"}        # km-138-1
  - {value: 6.642,  source: "Hede 2\nucoin"}            # planned for km-730 lift
  - {value: 3.49,   source: "Hede 118\nNumista"}        # km-72 (just fixed in d77a404)
```

**Why this is the wrong shape for source data.** Source provenance is a
*structured* claim («this value is independently attested by source A AND source B»).
Burying it in a single newline-delimited string forces every consumer
(audit scripts, future query/dedup tooling, schema-migration scripts) to
re-parse the string to recover the constituent sources. We already hit this
the day we wrote it: the orphan-weight audit script (`scripts/oneoff/audit_orphan_weight_sources.py`)
had to special-case `[,;\n]` splitting to avoid false positives — that's
exactly the parser-of-display-string anti-pattern.

Render-side prose can join sources however it likes (`«Hede 2 + ucoin»`,
inline `<sup>` stacks, etc.) — that's display logic. **Source-data fields
should carry sources as arrays.**

**Two-step:**

1. **Analysis step (do first).** Decide the right shape. Options:
   - (a) `source: ["Hede 2", "ucoin"]` — list of strings.
   - (b) `source: [{type: hede, ref: "Hede 2"}, {type: ucoin}]` — structured per-token.
   - (c) split into separate `weight_rough_g[]` entries, one per source —
     same shape as the existing per-specimen Bruun rows already use, but
     would create N rows with the same numeric value (a kind of dup,
     though §9a-defensible if the sources genuinely measured / round
     independently).
   Each has trade-offs: (a) is the smallest schema change but still
   stringly-typed; (b) is properly structured but requires schema +
   render updates; (c) is most-§9a-aligned but inflates the table for
   nominal/standard values that aren't really «multiple specimens».
   Also decide: scope = only `weight_rough_g[].source`, or also any
   other metric field that has a `.source` sub-field.

2. **Decide rule placement.** Should this become a CLAUDE.md rule
   (analogous to §9a multi-specimen merge — extend §9a, or add a new
   sub-rule «source-data is structured, not stringly-joined») so future
   edits don't reintroduce the pattern? Or one-shot fix only? If
   one-shot, the danger is the next bulk-import that touches similar
   data quietly re-emits the pattern.

3. **Migration step (after analysis).** Sweep:
   - `data/locations/*.yml` and `data/shared/*.yml` for `\n` inside
     `.source` strings; convert per the chosen shape.
   - Update `scripts/lib/schema.py` if the shape changes.
   - Update `scripts/lib/render.py` (and templates) if the rendered form
     needs adjustment.
   - Update `scripts/oneoff/audit_orphan_weight_sources.py` to drop the
     `\n`-splitting kludge.
   - Update any bulk-import scripts (`scripts/oneoff/bulk_import_seed_locations.py`,
     `scripts/maintenance/*`) that emit the legacy form.

**Done criterion.** Zero remaining `"…\n…"` patterns inside any
`.source` field. Audit script `audit_orphan_weight_sources.py` works
without the `\n`-split hack. CLAUDE.md updated (or explicitly decided
no rule needed) per the analysis output.

**Estimated effort.** Analysis ~30 min; migration ~1 h depending on
chosen shape.

---

### H. Coverage check for additional museum / catalogue APIs  *(opened 2026-05-07)*

**Background.** IKMK Berlin (`ikmk.smb.museum`) was confirmed in
2026-05 as a usable enrichment source: CC BY-SA 4.0 texts, PDM 1.0
images, free unauthenticated JSON via
`/object?id=<id>&download=json_ext`. Bulk cache job for SH+DK scope
was run (~2.9k records). See `docs/IKMK_HARVEST.md`.

The same shape of work is worth doing for the next two tiers of
museum sources mentioned in CLAUDE.md §5 source hierarchy:

- **Royal Coin Cabinet (Copenhagen)** — Den Kgl. Mønt- og
  Medaillesamling at the National Museum of Denmark. Likely
  candidate URL `samlinger.natmus.dk` or
  `kongernessamling.dk` — confirm.
- **British Museum** — has an unambiguous open API at
  `https://www.britishmuseum.org/api/...` (Collections Online).
  Numismatic department likely indexes Holstein, Hamburg, Lübeck
  coins.

**Done criterion.** For each: licensing posture confirmed, sample
records fetched for known SH/DK coins, coverage estimate produced
(N records in scope), comparison with IKMK overlap. Record findings
in `docs/<MUSEUM>_HARVEST.md` similar to the IKMK one.

**Estimated effort.** ~30 min per source for the probe; bulk cache
~1 h each if API permits.

---

### D. Triage `seed_unsorted` coins in denmark / hamburg / lubeck  *(opened 2026-05-04)*

**Background.** After bulk-importing 581 ucoin entries into proper
location files (commit `1abbef8`), three locations carry coins under
the placeholder `seed_unsorted` Müntzfuß:

- `data/locations/denmark.yml`     — 422 seed entries (years 1582–1875)
- `data/locations/hamburg.yml`     —  80 seed entries (years 1726–1873)
- `data/locations/lubeck.yml`      —  79 seed entries (years 1620–1797)

Each seed entry carries raw ucoin data (km, denom, year, fineness,
weight, diameter, url, tid) plus best-effort heuristic inference for
ruler/mint/metal. Every value flagged `verified: false`.

**Done criterion (per location).** All seed entries reclassified into
their proper Müntzfuß and gain `verified: true` for source-attested
fields. The location automatically reappears on the landing page once
its `seed_unsorted` count reaches zero — the build script
(`scripts/build.py::build_landing`) hides any location with even a
single seed entry, then re-checks on every build. No template/config
edit needed when the threshold is crossed.

**Recommended order.**

1. **Hamburg (80, smallest)** — needs new Hamburg-specific Müntzfüße
   defined in `data/shared/fuesse.yml` first (Bankthaler / Speciesthaler /
   Mark-Courant standards). Triage by ucoin Period + Hede equivalents.
2. **Lübeck (79)** — needs Wendisch-Lübisch Münzfüße defined (the
   existing 11_333_thaler proxy is incorrect for most Lübeck coins).
   The 1 already-curated entry (km-168-1-1752) is the model.
3. **Denmark (422, largest)** — most coins fit existing fuesse:
   - period_2940 (Speciedaler 1582-1624) → 9_25_thaler / 9_thaler
   - period_1147 (Rigsdaler 1625-1699) → 9_25_thaler / kronemont
   - period_1115 (Rigsdaler 1699-1749) → 9_25_thaler / reichsdukatenfuss
   - period_846  (Rigsdaler 1750-1812) → 11_333_thaler / 18_5_thaler
   - period_647  (Rigsbankdaler 1813-1854) → 18_5_thaler
   - period_646  (Rigsdaler rigsmønt 1854-1873) → 30_thaler
   - period_374  (Christian IX 1873-1906) → reichsgoldmuenzfuss
   Some need new Royal Danish standards added (Kurantmøntfod 1726+).

---

### F. Bruun fall-throughs documented for posterity  *(opened 2026-05-06)*

After Phase 4c + Phase 3 completed, the Bruun cross-match shows 11 fall-through
candidates in DK+SH that did NOT enter the data. All are accounted for:

- **3 medieval (pre-1566, out of project window)** — excluded per project scope:
  - P1·1001 Hans 1496 Noble (Bruun-coll. 3831, NGC AU-55, UNIQUE in private)
  - P1·1002 Hans ND 1496-1497 Goldgulden (Bruun-coll. 3840)
  - P3·11148 Christopher III 1440-42 Skilling Lund (Bruun-coll. 3763)

- **1 pattern (per §9.1)** — excluded:
  - P2·13140 Frederik III 1659 5 Ducats Hede-100A KM-PnJ16 (Bruun-coll. 6275, NGC Unc Details—Cleaned)

- **2 SH-Altona Christian VII multi-year merges** — addressed in this commit:
  - KM-640.1 1786 Albertsdaler → enriched km-640-1-chr-vii-1784 (Bruun-coll. 7863, 1786 specimen)
  - KM-641.4 1785 12 Mark (Courant Ducat) → new entry km-641-4-chr-vii-1785 (Hede-4D sub-variant of Hede-4B 1783, Bruun-coll. 7859)

- **5 already-covered (matcher-quirks)** — no action needed:
  - P2·14241 KM-226.1 1753 Karl Peter Ulrich Mannheim Taler — flagged as Krause sub-variant of existing km-226-kpu-1753 in Phase 4a batch 6
  - P2·14261 KM-cf.455 Adolf XIII 1598 3 Taler Altona — already added as bruun-14813-adolf-xiii-1598a (Phase 4a batch SP); matcher missed because no exact KM ref
  - P3·12215 Adolf XIII 1598 1½ Taler Altona — already added as bruun-14815-adolf-xiii-1598b (Phase 4a batch SP); same matcher reason
  - P4·17210 KM-758.1 Frederik VII 1854 4 Skilling Rigsmønt → already enriched km-x003-fr-vi-1854 in Phase 4a batch 7b
  - P4·17218 KM-cf.758.2 Frederik VII 1856 Copper Piefort 4 Skilling — already added as schou-piefort-fr-vii-1856 in Phase 4c batch 6

**Bruun cross-match closing state (2026-05-06 after parser-fix + §9.3 cleanup):**
TOTAL=783, A=763 (97%), B=11, D=9.

- **B=11 residual noise** — multi-match cases where the *correct* candidate is
  enriched but a *spurious* year-overlap candidate (e.g. Lübeck KM-27 1/192 Thaler
  colliding with Danish KM-27 Speciedaler) lacks the Bruun citation, so cross_match's
  `all()` semantic still flags the lot as B. The 11 residuals are documented and
  not actionable without changing cross_match.py to use `any()`-semantic; left as
  closing inventory:
  - P1·1017, P3·11178 (KM-26 Hede-11 6 Daler Klippe 1604) → dk-tid-163410 ✓
  - P1·1018, P4·17046 (KM-25 Hede-12 4 Daler Klippe 1604) → dk-tid-163409 ✓
  - P1·1049, P2·13114, SH P2·13120, SH P4·17058 (KM-27 Speciedaler 1642–1647 Glückstadt) → km-27-chr-iv-1641/1644 ✓
  - P2·13097 (KM-16 2 Speciedaler 1623 Glückstadt) → km-16-chr-iv-1623 ✓
  - P2·13159 (KM-56 Ducat 1666 Glückstadt) → km-56-fr-iii-1666 ✓
  - P4·17194 (KM-742 Speciedaler Frederik VII 1848 Accession) — no host coin in our YAML; KM-742 is a distinct Krause type from km-744 (1849). Genuine D-candidate that was mis-categorised B by ref-token noise.

- **D=9 fall-throughs** — true non-matches (medieval / pattern / cross-bucket
  mis-routings handled in this section, plus 1 oldenburg P3·12226 1/2 Mark
  / 12 Grote 1658 awaiting Müntzfuß-classification of `oldenburg.yml`).

**Done criterion**: this list is the closing inventory; no further fall-throughs from the
4-PDF Bruun cross-match remain. Bruun Part V (when published) will run through the same
pipeline and any new fall-throughs will be triaged similarly.

---

### E. Müntzfuß-classify 7 promoted Bruun stub locations  *(opened 2026-05-06; updated 2026-05 after Phase 4b proper)*

**Background.** Bruun parts I–IV ingest (cache in `scripts/cache/bruun/`) routed
**38 in-scope coins** to 7 territories. They are NOW promoted to real location
files (see commits 2026-05) with `fuss: seed_unsorted` placeholder; per-coin
data (KM/Hede/Sieg/Lange/Fr/Dav refs, year, ruler, mint, weight, NGC grade,
Bruun-page citation) is preserved. The Müntzfuß-system research is what's
still pending — each territory uses its own Reichskreis or local standard that
needs proper study.

**Seed files & their Müntzfuß-systems to research:**

| Seed file | Coins | Müntzfuß systems to research |
|---|---:|---|
| `data/seed/bruun/lubeck_bishopric.yml`     | 14 | Reichsthalerfuß via Holstein-Gottorp prince-bishops (Eutin) |
| `data/seed/bruun/oldenburg.yml`            | 10 | Niedersächsischer Kreis-Fuß; Jever-Mint grote-systems under Anton Günther |
| `data/seed/bruun/bremen_verden.yml`        |  6 | Niedersächsischer Kreis (1635–1648), then Swedish administration 1648–1712 |
| `data/seed/bruun/brunswick_lueneburg.yml`  |  4 | Reichsmünzordnung → Leipziger Fuß → Konventionsfuß (Wolfenbüttel mint, Christian IV's Niedersachsen-Periode 1627) |
| `data/seed/bruun/hesse_kassel.yml`         |  2 | Reichsmünzfuß → Konventionsfuß (Kasseler Münzkonvention 1763), 14-Thalerfuß |
| `data/seed/bruun/lauenburg.yml`            |  1 | Lauenburg-Konventionsfuß (1815–1864 under DK king) — distinct from Schleswig-Holstein, struck at Altona Mint per separate Lauenburg standard |
| `data/seed/bruun/osnabrueck.yml`           |  1 | Niedersächsischer Kreis-Fuß under prince-bishop, alternating Catholic/Lutheran 1648+ |

**Promotion procedure** (per territory) is documented in `data/seed/bruun/README.md`:
research the relevant Müntzfuß, add to `data/shared/fuesse.yml`, add issuing entity
to `data/i18n/issuing_entities.yml`, create `data/locations/<territory>.yml` +
`-references.yml`, transform each seed coin record into a full `Coin` schema entry
with computed fineness/fuss/phase, then move (don't copy) the seed file out of
`data/seed/bruun/`.

**Done criterion.** All 6 seed files emptied (or moved to git history). The 37
coins live in proper `data/locations/` files with correct fuss-classification.

---

### C. Bremen-Archbishopric Frederick (II/III) coinage 1641–1643  *(opened 2026-05-03)*

**Surfaced during.** Cross-check of the 3 Numista issuer-list pages
linked from item B (now closed). The Bremen-archbishopric page
returned 3 Frederick III Bremen issues — historically connected to
our Holstein register because Frederick III held the Bremen
archbishopric (as Frederick II) before becoming Danish king in 1648.

**3 coins to model into a future `data/locations/bremen.yml`:**

| Coin | KM# | Numista | Metal / spec |
|---|---|---|---|
| 1 Thaler Frederick of Dänemark 1641 | KM# 38 | N#129848 | Silver .888, 29.23 g, Dav CCT# 5078/5078A, Jungk# 363… |
| 2 Schilling Frederick II 1641–1643 | KM# 36 | N#429659 | Silver |
| 1/16 Thaler 1641–1643 | KM# 37.1 | N#394107 | Silver, 1.57 g, ⌀19.3 mm, Jungk# 366–371 |

These are **NOT in scope of `schleswig_holstein.yml`** — Bremen archbishopric
is a distinct ecclesiastical territory, not a Schleswig-Holstein
duchy. They would belong in a separate `bremen.yml` location.

The user opened these as part of TODO B research; recording here so
the link from B's closure isn't lost. Whenever Bremen comes up as a
new location target, this is the seed list.

**Done criterion.** Bremen location file created with these 3 coins
(plus whatever else the bremen.yml scoping work surfaces) — OR an
explicit decision that Bremen stays outside the project scope.

---

## Done

### G. §9.3 cleanup of wrong Bruun-specimen attachments  *(closed 2026-05-06)*

**Background.** When Phase 3 ran the original `phase3_enrich.py` without
single-match filtering, multi-matched Bruun lots were broadcast to ALL
candidate ids — attaching the same specimen to multiple coins, including ones
whose KM (and Hede where comparable) demonstrably mismatched the lot's
catalog refs. Per §9.3, different KM = different type, so these were silent
data corruptions sitting in `denmark.yml` and `schleswig_holstein.yml`.

**Outcome.** Audit (`scripts/oneoff/audit_wrong_bruun_attachments.py`)
identified 58 mis-attachments across 42 coins. Strip
(`strip_wrong_bruun_attachments.py`) cleared those attachments from
`catalog.bruun_*`, `weight_rough_g[]`, and `sources[]`, then phase3b/3c
re-enriched with §9.3 compatibility filtering baked in
(`lot_compatible_with_coin()` is now called before any new spec is added
to a host coin). Final audit reports 0 mis-attachments.

**Closure commit:** `ffbf458` (DK+SH strip), `03b1c10` (parser fix
prerequisite), `a5dd778` (Phase 3b/3c clean re-enrichment).

---

### A. Verify continuous year-ranges for gaps  *(closed 2026-05-03)*

**Outcome.** All 15 coins audited against Numista `_issues.json` cache:

- **10 confirmed continuous** — Numista per-year breakdown explicitly
  enumerates every year in the declared range (no gaps):
  km-137117 (1589–1601), km-5-ja (1594–1605), km-103 (1671–1682),
  km-8-ernst (1600–1609), km-25 (1640–1648), km-155 (1695–1702),
  km-185 (1703–1710), km-183 (1703–1709), km-735 (1842–1848),
  km-193 (1706–1712).
- **4 «is_dated: false»** — Numista records the type as a single
  range without per-year split (per-year breakdown unavailable from
  Numista; left as continuous, undocumented gaps possible):
  km-3-ja (1590–1616), km-137419-ernst (1601–1622),
  km-278283-ernst (1601–1622), km-137112-otto (1567–1576).
- **1 special** (km-120-chr-v-1787) — its Numista link N#34037 was
  incorrect (pointed to Mauritius ½ Rupee 1946); removed. No correct
  Numista entry found for Christian VII 2 Sechsling Tower Hill 1787–1800.
  ucoin tid 90571 records as range 1787–1800 without per-year split —
  left as continuous.

All 15 entries gained a `verification_note` documenting the audit so
future re-runs of similar checks won't re-flag them. Per-coin notes
quote the audit date (2026-05-03) and the source consulted, satisfying
the original done-criterion: «range confirmed against an explicit
source».

---

### B. Investigate Frederick III silver «1 Krone» 1659–1660 (N#313341)  *(closed 2026-05-03)*

**Outcome.** N#313341 turned out to be a **duplicate Numista listing
of our existing `km-x001-fr-iii-1659`** (Type II, Hede 153A). Numista
carries two parallel entries for the same Davenport-3675 type:
N#111285 under the «City of Glückstadt» issuer (KM# B43) and N#313341
under the «Schleswig-Holstein duchies» issuer (KM# 95). The km-x001
entry already cites both Numista IDs in `sources` and explicitly
documents the duplication in its body note («same coin, duplicate
Numista listing»).

**Cross-check of the 3 research links** (all Frederick III, ru=437):
- `schleswig_holstein_danish_duchies` (3 hits): all 3 already in base
  — km-90 (1 Sechsling), km-x001 (1 Krone, this item), km-103 (4 Marck
  Danske, listed under Christian V on Numista despite the FRIII filter)
- `gluckstadt_city` (9 hits): all 9 already in base — Guldkrone,
  1/16 Speciedaler, both 4-Mark-Dansk types, Speciedaler 1664-66,
  ⅛ Reichs Daler, both 1/16-Thaler bust types, 1 Ducat 1666-69
- `bremen_archbishopric` (3 hits): not in base, not in Holstein scope
  — moved to Item C as seed for a future `bremen.yml`

**Net result.** No new Holstein coin to add from item B. The «silver
Krone» discovery turned into a Numista-duplicate normalisation that
was already done.

(none yet)
