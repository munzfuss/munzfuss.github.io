# Pending audits and longer-term TODO

> **Read this at session start** — the entries below are open audit items
> that have not been actioned. CLAUDE.md links here so they don't get
> forgotten across sessions. When an item is done, move it to the
> "Done" section at the bottom (with the commit SHA) so we have a record.

## Open

### N. ucoin↔Krause KM-attribution conflicts (Denmark)  *(opened 2026-05-12)*

Recurring pattern surfaced during the dedup-merge audit of denmark.yml:
ucoin's bulk catalog (built from ucoin's user-edited TSV under
`scripts/cache/ucoin/period_*.tsv`) assigns a KM number that
disagrees with Krause-Denmark as verified by Bruun PDF + Hede.
Per CLAUDE.md §5, Bruun is the higher-authority source (auction-
catalog tier 3), so when ucoin's KM and Bruun's KM disagree on the
same numeric value, Bruun wins and ucoin's KM-attribution is dropped.
ucoin entry retains its non-KM data (weight, fineness, year,
nominal, source URL) as a bulk-pending coin awaiting classification.

Two cases resolved so far; pattern likely recurs across the ucoin
period TSVs and warrants a broader sweep:

* **KM 48** — *resolved 2026-05-12.* `dk-tid-162993` («1 Søsling
  1614») had ucoin-assigned km=48. Bruun lot 13080 + Hede c4h48
  attest KM-48 = ¼ Speciedaler 1602 Christian IV (= our
  `km-48-chr-iv-1602`). km tag cleared on dk-tid-162993,
  verification_note records the finding. Per-coin classification of
  the 1614 Søsling type itself remains pending (Hede c4h skips
  this year between c4h84 (1611) and c4h145 (1631), so the type
  needs an independent source if it's to gain a Krause-edition KM
  citation).
* **KM 577** — *resolved 2026-05-12 alongside.* `dk-tid-78763`
  («½ Skilling 1751-1762» 3.654 g) had ucoin-assigned km=577.
  Bruun lot 17127 attests KM-577 = 1 Dukat 1749 Frederik V (= our
  `km-577-1749`). Beyond the KM clash, ucoin's nominal+weight pair
  (½ Skilling at 3.654 g) is itself numismatically implausible —
  expected ½ Skilling weight under Frederik V is ~0.4 g. Both flagged
  for follow-up: KM dropped, full re-classification of the underlying
  coin remains pending.

Open question: are these isolated ucoin-cataloger errors, or do they
trace to an older Krause edition with different KM numbering? A
sweep over `scripts/cache/ucoin/period_*.tsv` against Bruun-verified
KMs in denmark.yml would surface the full set. Hold for now —
follow-up audit pass when the higher-priority L-campaign items free
up.

### O. Numista weight typos vs Hede Bruttovægt  *(opened 2026-05-12)*

Adjacent pattern to §N: Numista entries occasionally publish a
«weight» field that's closer to Hede's Finvægt (fine-silver content)
than to Hede's Bruttovægt (gross-coin standard). Numista's own
convention is Brutto (confirmed via control-case KM-81 / Hede 115:
Numista 1.051g matches Hede Bruttovægt exactly). Where Numista
deviates by ~10-15% from Hede's Brutto, the most parsimonious
explanation is a user-edit error — the editor entered Finvægt by
mistake.

One case resolved so far:

* **KM-82 / Hede 114** (8 Kroneskilling Christian IV 1620-1621) —
  *resolved 2026-05-12.* Hede Bruttovægt 2.101g (passes three
  independent checks: internal arithmetic 2.101 × 0.859 = 1.806
  matches published Finvægt; silver-proportional 2× sister-denom
  KM-81 = 2 × 1.051 = 2.102; marken-fin formula gives the correct
  1/12 daler face value matching curator's `fraction: 1/12`).
  Numista/ucoin 1.85g is 12% low — likely Finvægt-mistake. Hede
  value now primary on km-82-chr-iv-1620; Numista 1.85g kept as
  second reading with annotated explanation.

Pattern hypothesis: small-denomination scheidemünze entries on
Numista are more prone to this confusion because Brutto and Finvægt
are visually close and the source pages (often danskmoent Hede)
publish both side-by-side. Larger denominations (where Brutto and
Finvægt differ by a clear factor) are less affected — see KM-81
control case.

Open question: how many other Numista DK entries have this
inversion? A sweep over `scripts/cache/numista/*.json` comparing
`weight` vs Hede's published Brutto for each entry (filtered to
those that also cite Hede in catalog refs) would surface the full
list. Hold for now — defer to the same audit window as §N.

### L. Schleswig-Holstein + Denmark consolidation campaign  *(opened 2026-05-10)*

A coordinated multi-pass effort to bring the SH and Denmark locations
to «published-quality» state before the next location takes priority.
The nine sub-tasks below are tightly coupled — many depend on
upstream completion (the territorial-attribution sweep before the
data audit, etc.) — and should be worked through roughly in the
listed order.

1. **Process all IKMK candidates per location.**
   - **1a. Schleswig-Holstein — DONE 2026-05-10.** All 65 IKMK records
     in scope (prefixes Schleswig-Holstein-Sonderburg / -Gottorf /
     -Glücksburg / plain SH) processed: 47 already cited in
     `data/locations/schleswig_holstein.yml`, 2 added (commit
     `eca82c0`: km-9 Lange 533A/a + 533A/b mule specimens after
     §9a thinning), 16 deliberately skipped per §9a sub-variant
     bucket overflow (intra-bucket noise — not a coverage gap).
     Matcher hardening shipped along the way (commit `24a82e7`:
     weight-sanity gate at 1.5× ratio, multi-letter+slash Lange-tag
     regex, parent-fallback strict-ref lookup).
   - **1b. Denmark — PENDING. Blocked by harvest expansion in (2a).**
     Current IKMK scope for `denmark.yml` is only 41 records (26
     under prefix «Dänemark» + 15 under «Norwegen») versus 468 coins
     in the YAML. The IKMK Berlin cache holds 6,531 JSON files in
     total, of which only this restrictive subset routes to the
     denmark mapping in `_index_by_issuer.json`. The harvest filter
     used for the original SH+DK pass was clearly Holstein-context-
     scoped; for proper denmark coverage it has to be re-run with
     a Kopenhagen / Christiania / Norwegen mint sweep across the
     full 1566-1914 window. Matcher run + bucket triage is identical
     in shape to (1a) but blocks on (2a).

2. **Multi-source enrichment pipeline for `denmark.yml`** (DK-only
   scope; SH covered separately under (1a) and the older audit work).
   The four stages below run roughly in order — earlier stages enrich
   the per-coin data that later stages cross-check against:
   - **2a. IKMK harvest expansion. PARTIAL — IKMK ceiling reached
     2026-05-10.** Ran a broader query set covering Denmark proper +
     Danish-Norwegian-union mints + Danish-controlled territories
     (Iceland, Faroe, Greenland, Tranquebar, Danish West Indies,
     Danish Gold Coast) and Danish-king-ordinal queries (Christian
     IV–X, Friedrich III/IV/VI/VII). The fetch added **548 new cache
     records** (722 fetched − 174 ancient/Roman noise removed), but
     only **6 routed to denmark** via the issuer-prefix mapping
     (Trondheim — medieval, out of 1566–1914 scope window).
     Final IKMK Denmark coverage: **68 records / 41 in-scope**
     (vs 62 / 41 pre-expansion). The «several hundred» target is
     not achievable through IKMK alone — IKMK Berlin is a German
     museum and has limited Danish coverage (62 «Dänemark» + 19
     «Norwegen» records exhausted; Tranquebar / Iceland / Faroe /
     Greenland / Danish-Gold-Coast queries returned zero hits).
     Remaining 542 cache records are non-Danish coins (Schleswig-
     Holstein-related, Hessian Friedrich's, Brandenburg-Lüneburg,
     etc.) that the broader ruler-axis queries pulled along with
     Danish ones. Reaching «several hundred» requires alternative
     catalogues — see TODO H for Royal Coin Cabinet Copenhagen +
     British Museum API coverage check.
   - **2b. IKMK candidates processing + DK seed_unsorted triage
     (combined).** After (2a), run `match_ikmk_locations.py denmark`
     and walk the buckets per the same procedure as (1a). At the
     same time, walk the 422 `seed_unsorted` entries currently in
     `denmark.yml` (per TODO D's DK part) and resolve their
     Müntzfuß / phase / verification status. Combining both passes
     maximises per-coin data density: an IKMK record that strict-
     matches a seed entry can lift it out of `seed_unsorted` into
     a real fuss with full provenance in one merge instead of two.
   - **2c. Hede / danskmoent.dk exhaustive coverage check.** Verify
     that `danskmoent.dk` Hede catalogue pages (URL pattern
     `c{ruler}h{N}.htm` per-type, `c{ruler}hede{N}.htm` overview)
     are cached for every ruler-era covering coins in `denmark.yml`,
     and that every coin with a Hede equivalent carries a
     `catalog.hede` field. Subsumes the original TODO K (systematic
     Numista-vs-Hede divergence audit) — once Hede coverage is
     wired, run the Numista-cross-check pass and apply per-coin
     corrections per the established km-79 / km-128 / km-110 shape.
   - **2d. Other-source enrichment (lower priority, post-Hede).**
     Walk denmark.yml coins and pull additional readings from ucoin
     (where SH-style URL index extends to DK), Numista (already
     largely cached but un-merged on many coins), NumisBids, ma-
     shops auction data, and any other accessible catalogue. Each
     source becomes its own atomic step here once the Hede-pass
     surfaces what's still under-documented. Order TBD when the
     sub-items materialise.

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

### M. ucoin harvest is missing the `Composition` field  *(opened 2026-05-11)*

**Surfaced during.** The investigation of `dk-tid-163075` (KM# UC# 10,
Frederik II 10 Ducat 1588) where user-side verification on the live
ucoin page showed «Composition · Gold» that our local cache never
carried. Our `scripts/cache/ucoin/_url_index.json` schema only stores
`denom / diameter_mm / fineness / km / source / url / weight_g / year`
— no metal / composition.

**Impact.** Likely affects every ucoin-sourced coin that landed in
`denmark.yml` (and other locations) with `metal: null` or with metal
inferred from the nominal token. The Hede-classifier session
yesterday left 2 denmark entries unclassified specifically because of
the missing-metal gap (`10 Ducat 1588`, `3 Kroner 1726` — the latter
turned out to be silver despite our gold inference; that's a separate
ucoin-erratum case, not this gap).

**Action.**

1. Locate the original ucoin harvest script (`scripts/build_ucoin_url_index.py`
   or similar) and add a `composition` field extraction from the
   ucoin page HTML (the «Composition» label is one of ucoin's
   standard table rows).
2. Re-harvest the existing 4,000+ ucoin URL entries that lack
   `composition`. Numista API-style quota does not apply here —
   ucoin is HTML scraping; respect a polite rate limit (~1 req/sec)
   per the ad-hoc policy in CLAUDE.md.
3. Re-run `scripts/maintenance/classify_dk_seeds.py` after the
   harvest — the metal-aware path will now classify several
   previously-stuck entries.

**Not blocking.** The current Denmark page renders correctly; this
just leaves a handful of metal-tagged-by-inference entries that
should be metal-tagged-by-source.

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

### I. Restructure `\n`-joined source labels in scalar metric fields  *(closed 2026-05-10)*

**Surfaced.** Multi-source attestations on a single value (e.g. `weight_rough_g: [{value: 28.893, source: "Hede 39A\nNumista"}]`) buried two independent citations in a `\n`-joined string. Audit / dedup / query code had to re-parse the display string with `re.split(r"[,;\n]", …)` — the parser-of-display-string anti-pattern.

**Outcome — Option C (split into N entries with same value).** Each multi-source attestation now renders as one entry per source:

```yaml
weight_rough_g:
  - {value: 28.893, source: "Hede 39A"}
  - {value: 28.893, source: "Numista"}
  - {value: 28.89,  source: ucoin}
```

The display pipeline (`compute.make_display_groups`) already groups list-form entries by rounded value, so two same-value entries collapse into ONE rendered span with both sources accumulated into the tooltip — visually identical to the joined form, structurally clean.

**Implementation:**

  - **Migration.** `scripts/maintenance/split_multisource_weight_entries.py` walks every coin's `weight_rough_g`, `fineness`, `diameter_mm` lists and splits any `\n`-joined source into separate entries. Idempotent — re-running on already-split data is a no-op. Applied: 40 new entries across 31 coins (4 in denmark, 36 in schleswig_holstein).
  - **Compute fix (latent bug).** `compute.alts` previously hardcoded the alt-source tooltip prefix as «Обчислено з вагою × пробою з:» regardless of which input the alt actually overrode. After the migration this caused split alts that supply only a different weight reading (with fineness inherited from the scalar primary) to render under the «× пробою» prefix and visually duplicate the primary's «з вагою з:» prefix in the same tooltip. Fixed to mirror the primary-derived-source prefix logic — pick the prefix that reflects the actual override (weight only / fineness only / both).
  - **Audit script.** `scripts/oneoff/audit_orphan_weight_sources.py` dropped its `[,;\n]`-split kludge in favour of a clean `[,;]`-only split (the comma/semicolon inline-join still appears in older entries; the `\n` form is gone for good).
  - **CLAUDE.md.** Extended §9a with a «Source-data is structured, not stringly-joined» sub-rule so future edits don't reintroduce the pattern.

**Verification.** Build still passes; rendered output visually identical except for the corrected alt-prefix labels (the latent bug fix). Re-running the migration finds zero remaining `\n`-joined source labels across the corpus.

---

### J. Bruun parser + cross-match: two latent bugs from km-165/KM-166 audit  *(closed 2026-05-10)*

**Surfaced during.** Audit of `km-165-fr-iv-1698` (Schleswig-Holstein-Gottorp
1 Mark 1698 Tönning, Lange-430A) revealed Bruun lot `III/12210` had been
mis-attached as an orphan weight (22.0 g) to km-165 even though the lot is
KM-**166** / Lange-**430AA** (the sister 2 Mark, separate Krause type per §9.3).

**Outcome.**

  - **Parser regex (02_parse_lots.py)** — `[A-Za-z]?` → `[A-Za-z]*` for all
    REF_PATTERNS so multi-letter Krause / Lange / Hede sub-variant suffixes
    capture in full. Re-running the parser surfaced 5 truncated suffixes:
    Lange-430AA (was 430A — the original trigger), Lange-510AAb, Lange-99Aa,
    Lange-99Ab, Dav-3746var. All five are now whole tokens in the cache.

  - **Parity gate (04_cross_match.py)** — added `lot_compatible_with_coin()`
    that gates EVERY candidate path (single-match included, plus the Bruun-id
    fast-lookup) on parent-KM match, falling back to parent-Hede when KM is
    absent on either side. The function also accepts KMs listed in
    `catalog.others` to support intentional Numista-duplicate consolidations
    (e.g. km-105 carrying KM# 73 as a synonym).

  - **Audit pass.** Re-running cross_match flipped 9 lots from cat A to cat
    D (parity-rejected). Verification confirmed all 9 previously-matched
    coin-IDs either no longer exist in YAML (stale cache from prior coin
    renames) or never had the lot attached in the data layer — no §9.3
    cleanup needed in `*.yml`. The 9 D-cases are off-metal-strike Pn-tier
    issues + genuinely-missing Krause types that may warrant new YAML
    entries (deferred — independent of this fix).

**Bruun cross-match state (after fix):** TOTAL=783, A=755 (96%), B=10, D=18.

Implemented in commit (this session). Closes both defects in TODO J.

---

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
