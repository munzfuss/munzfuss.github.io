# Session handoff

> **Read at session start, alongside `CLAUDE.md` + `docs/TODO.md` + `docs/SOURCES.md` §13-§14 + `docs/PLAYBOOKS.md`. Glance at `docs/DECISIONS.md` and the latest `docs/notes/YYYY-MM-DD.md` for rationale + recent context.**
>
> Short-term state for the next agent (or future-me) to pick up cold:
> *what was I doing, what's next, what's blocking, what's freshly
> committed but not yet pushed*. This is NOT the place for stable
> conventions (those go in `CLAUDE.md`) or long-term audit items with
> design context (those go in `docs/TODO.md`). Keep it lean — when an
> entry stops being relevant to the immediate next steps, prune it.
>
> **Maintenance discipline**: update at task / chapter boundaries, when
> direction shifts, or when you notice the gap between «what I'd want
> next session to know» and «what's recorded». A typical entry survives
> a few sessions before either being completed (delete) or promoted to
> `docs/TODO.md` (with full context).

## 2026-09-24 — kronemont_chr_iv sourced to Wilcke I page by page; open items for the curator

Local, NOT pushed: `afc182c` (refs + Denmark prose), `2de0835` (card rows,
two-era accounting fractions), `70b2fd8` (1619 kroneskilling `fraction: 1/48`),
plus the Block 9 schema/grid_stops commit and this handoff. Plan:
`~/.claude/plans/iterative-napping-oasis.md`.

**Two corrections to the plan, found at the source:** the «1⅓ still short:
34,4 g vs 32,5 g» passage is Wilcke I **p. 233** (PDF 232; OCR prints «235»),
not 235; and after 1625 the Ortskrone = **½** sletdaler (32 ß), not 1½ —
OCR «1 f2»; only ½ agrees with «halv Ortskrone = 1 Sletmark = 16 ß».

**Not done, deliberately — curator decisions:**

1. **Phase III `soll_fein_by_phase` (plan Block 8.2) skipped.** The 1665
   Pumphosenkrone (.791 → 14,957 g fine) renders Δ −8 % against 16,250.
   Setting phase III's Soll to the Grove Krone 14,964 would contradict the
   rule this very file states for rhinsk_gylden_fod: «Only a dated ordinance
   may set a phase's own target … so their shortfall stays visible». No
   ordinance is known for 1665; Hede calls them «specielle udgaver». The
   real question is placement (kronemont vs kronemont_chr_iv), not Soll.
2. **`kronemont` `details` + Schleswig-Holstein copy still say «Anfangstarif
   … Aufschlag ca. 11 %» citing `danskmoent-w2ref`** — the same wrong figure
   fixed on kronemont_chr_iv (Wilcke I p. 231: 16 %, 20 % with recoining).
   Other `danskmoent-w2ref` citers (Gresham claims, guldkrone phase) were not
   verified against Wilcke II; the ref entry now at least describes the
   volume it links.
3. **`parse_hede.py::_UNIT_CANONICAL` maps `rd.kr` → `rigsdaler_kurant`.**
   Hede writes «rigsdaler kroner»; not kurant, not post-1726, 10,4 ≠ 11⅓.
   Fix map, add `rigsdaler_krone` (already in the schema docstring and on the
   two krone `hede_yield`s), relabel 28 cache JSONs + 3 seed/unified/final.
   The relabel alone moves nothing (`unit` is not rendered).
4. **`hede_yield` is populated but NOT consumed.** `_build_yield_index`
   ignores the field and still indexes `grid_stops`; the new krone values
   (12.367 / 10.5 / 13, unit rigsdaler_kurant) match no coin. Wiring it in = re-classifying ~22 coins at 10,418
   that sit on `9_25_thaler` (plus 5 at 10,4, 5 in seed_unsorted).
5. `fractions.soll_fein_g` 1/1/2/1/4/1/8 realignment to Wilcke Nr. 105–108
   (16,127 / 7,993 / 3,865 / 1,923 g) — moves Δ on ~15 rows.
6. `½ Guldkrone` `unified-dk-hede-c4h27` (gold) on this silver fuss, Δ −83,5 %.
7. `skilling danske` coins (12/8/4/2 Skilling) keyed as krone fractions;
   `km-68` 2 Kroneskilling keyed 1/48 (Corona-Danica scale) in a table on
   Hede's scale — should be 1/24; 4/8 ks likewise.
8. Phase I `year_to: 1624` vs Wilcke «Sommeren 1625» (p. 231); prose now
   says 1618–1625.
9. hintergrund 10½-Fuß resumption «1644» vs kronemont card 1649/1652.
10. Phase I description still carries KM# numbers in prose (§7a C6).

## 2026-09-22 — thinning stopped forgetting what it drops (both layers); YAML residual A + B paid

Eleven commits local, NOT pushed: `474771f` `32e51b0` `292aae7` `2de946c`
`dc944c0` `e2338b1` `71963bb` `fea6534` `c416c7e` `5e4dfce` `3c6a9af`.

Started as the YAML reformat-debt task and turned into the thinning layers.
Two inert `no_merges` pairs in danish_realm led back to §9a thinning dropping
records that nothing downstream could account for.

**Both thinning layers now record what they removed.**
`lib/seed_thin._record_thinned_from` writes `_thinned_from` on the
representative (the same record `_salvage_unique` targets), and
`thin_final_weight_lists._record_thinned_weights` writes `_weights_thinned` —
the removed readings verbatim, NOT a boolean, so `verify_reflow` can excuse
exactly those values and still block a real loss in the same list. Both keys
are in `_PRESERVE_ALWAYS_KEYS` / re-derived per pass.

**The seed-layer bucket key is now the merger's.** `_subvariant_key` compared
`nominal` and `ruler` RAW while claiming to use the merger's signals, so
«Christian 4» and «Christian IV» were two buckets, each with its own
`max_weightless` quota. Aligned it to `lib.nominal_synonyms.normalise_nominal`
+ `lib.ruler_reigns.normalise_ruler_key`; `mint` stays raw (measured: changes
nothing). The re-flow dropped 294 kmk records — 291 weightless, 3 exact
same-weight twins — with no envelope moving and every id recorded.

**Thinning no longer re-sorts the file.** It sorted output by id, which is not
how the corpus is written (only the two thinned sources were id-sorted at all;
`merge_seed` emits parser order + orphan tail). Dropping 5 records from
gottorp_duchy used to rewrite 6 127 lines; now 99, and sonderburg_duchy is not
touched at all.

**Ruler comparison key moved to `lib/ruler_reigns.normalise_ruler_key`**,
beside `normalise_ruler_name` (display form, untouched). Nominals were already
delegated. Verified identical on all 654 distinct live ruler strings.

**Three method notes, each of which cost time here:**
1. `_expand_member_against` has THREE call sites — the per-entity closure, the
   cross-entity pre-scan, and the completeness guard. Wiring the thinned index
   into one left `validate_decisions` reporting every member resolving while
   the merger silently skipped them. Wire all three or none.
2. The `absorb → thin_final_weight_lists` pairing in the 2026-09-13 note below
   is real and I skipped it: absorb re-populates the full §9a envelope, so a
   run without the thinner reads as 3 rendered coins "losing" weights.
3. A guard extracted to the scratchpad resolves `FINAL_DIR` from `__file__` and
   silently reads an EMPTY directory — it reports «0 changed» and looks like a
   clean baseline. Run a HEAD-version script from inside the repo tree.

**YAML residual**: step A (18 hand-edited files, 1 141 lines) and step B
(`_pending_merge_review.yml`, 4 187) are paid; `.git-blame-ignore-revs` now
exists (enable locally with `git config blame.ignoreRevsFile
.git-blame-ignore-revs`). Site hash was byte-identical across step A.

**Open, measured, not started:**
- **Step D — `data/v2/seed/` 10 061 lines**, 93 % of it `seed/numista` (9 203)
  + `galster` (807); kmk/ikmk are at zero through the same writer, so the
  question is why `build_numista_seed` leaves a trace when they do not.
  `v2_seed_writer.py` ~1838 only writes when something changed, so these never
  self-heal.
- **94 dead members in `_cross_entity.yml`**, absent from HEAD and from the
  current seeds — stale since the 2026-09-12 re-seed. Invisible to the gate:
  `check_member_resolution` skips `_`-prefixed files by design.
- **`_pending_merge_review.yml` is decaying.** Live (284 of its 303 candidates
  are still `seed_unsorted`) but keyed on `unified-*` ids, so in
  `confident_duplicate` only 9 of 122 PEER ids still resolve. Re-key on seed
  ids (§9b) when picking up the review.

## 2026-09-20 — NEXT TASK: the `mint` field carries a family of non-places

Found while repairing the fragment notes (`07b6a97`) and settling one
`mint: lybsk` (`1ca194d`). The KMM `place` → `mint` mapping in the kmk seed
builder pulled a whole family of values into `mint` that are not mint towns.
Counts are entries across final + seed (each coin appears in both):

| value | entries | what it actually is |
|---|---:|---|
| `Tysk` | 129 | «German» — a country/region, not a mint |
| `ulæselig` | 10 | «illegible» |
| `ubestemt` | 6 | «undetermined» |
| `ej bevaret` / `ej læselig` / `ej synligt` / `møntsted ulæselig` | 2 each | the same, in other words |
| `skilling`, `søsling` | 2 each | denominations in the mint field |
| `ikke Andreas Khüne)` | 2 | a fragment, stray paren included |
| `Ostindisk` | 2 | a region (Tranquebar / the East India trade) |

**Start with the illegible/undetermined group (~22 entries).** It is the only
unambiguous one: per §4 those belong as `mint: null` + `mint_verified: false`,
not as a mint name — right now the rendered page prints «ulæselig» to the
reader as a place of striking. `Tysk` ×129 needs a decision first: it may be a
deliberate grouping for the brakteats rather than a defect.

**Do NOT sweep this by pattern.** The same scan flagged `mint: Lybæk`, which
is the Danish name of Lübeck and a REAL attribution that KMM records as the
place — the curator's warning («в любеку теж могли карбувати, тому тут
обережно») is what stopped that one being «fixed» into nothing. Every value
needs its source read: for `lybsk` the answer came from Hede 171, which prints
«1 søsling lybsk, Glückstadt» — currency in the name, mint elsewhere.

Procedure: `trace_coin.py why <seed-id> --field mint` first (§0b-1), then the
KMM cache record, then the Hede/Galster page the entry's `typeNumber` names.
Repairs need a `_curation_holds` per entry: `mint` is not a CURATED_FIELD but
a _VERIFIABLE_FIELD, so a re-seed with `mint_verified: true` on both sides
lets fresh win and restores the bad value.

## 2026-09-13 — foreign-crown scope cleanup (Sweden + Tier-2) and the Gottorp/Sonderburg re-route

Applied the curator rule «a polity's coins appear on a location page only for
the years the Danish king held that polity's crown» (personal union counts;
tracked by the issuing CROWN = ruler, not the physical mint city).

Shipped:
- `163ac3a` / `823c123` / `c78ef4a` — excluded post-1523 Swedish issues from
  danish_realm (12: Christian III 1535 ×3 struck by Gustav Vasa, Erik XIV,
  Johan III ×4, Ulrika Eleonora, Fredrik I, Karl XIV Johan, Gustav Vasa
  1524-1527) + Tier-2 foreign crowns (5: Æthelred II England, Stralsund civic,
  Rostock civic, August III/Poland-Gdansk, Johann Albrecht I/Mecklenburg). All
  via `data/v2/exclusions/danish_realm.yml`. Rationale in `docs/SOURCES.md`
  §13.16 (incl. the KMM-`nation`-is-collection-not-issuer finding: the
  discriminator is `authority` + the «imitation» marker — `kmk-312155`
  «Æthelred, imitation» is a Danish coin and STAYS).
- `83883c7` — year-aware Stockholm/Vesterås mint routing (post-1523 → sweden
  OOS entity), so a future re-harvest cannot re-introduce them.
- `288303e` **fix:** `audit_entity_misclassifications._relocate_misclassifications`
  now writes seeds with the canonical ruamel serializer (`_canonical_seed_yaml`,
  width 200) + reads round-trip, not PyYAML `safe_dump(width=120)`. The old
  path re-flowed every long string → a 56-coin move produced a 570 000-line
  diff (real change ~1.5k). Pinned by `tests/test_relocate_serializer_canonical.py`.
  The relocation's CUR-vs-EXP asymmetry (CUR = direct dump, never merge_seed,
  or removed coins resurrect as orphan_curated; EXP = merge_seed) is documented
  in the tool + `scripts/maintenance/README.md`.
- `66f1eb5` **data(v2):** routed 151 KMM Holstein-Gottorp + Sonderburg ducal
  coins out of danish_realm (56) + royal_holstein (95) into gottorp_duchy /
  sonderburg_duchy via two `entity_routing_rules.yml` rules (gottorp_ducal_lineage,
  sonderburg_ducal_lineage) + `audit_entity_misclassifications --apply --source kmk`.
  gottorp/sonderburg set `bulk_promote_pending: all` so the relocated
  seed_unsorted coins promote. verify_reflow: 0 losses (every removal a
  recognised relocation); converged on pass 3 of merge→absorb→thin.

**Method note that cost a full revert the first time:** the pipeline is
TWO-PASS and the thinning phase is SEPARATE. A relocation is
`audit_entity_misclassifications --apply` → `merge_seeds_cross_source --apply`
→ `absorb_seeds_into_final_v2 --apply` → **`thin_final_weight_lists --apply`**,
repeated until `git status` is clean (finals converge on ~pass 3). Skip the
thinner and danish_realm final carries the full un-thinned §9a envelope
(+4733 display:false weights) as churn unrelated to the change; measure a
re-flow ONLY with `verify_reflow.py` (§9b).

**Next (separate passes, NOT started — investigated 2026-09-13, see below):**
Tier-2 residual review (Rostock 1557 «Christian III» Hede 10), the mint-field
data-quality debt (spurious «Hamborg»/«Mecklenburg» on genuine Danish-king
coins), and the exonumia tokens sitting in the `ruler` field of danish_realm.

## 2026-09-12 — §9a thinning moved off the seed layer; five defects found flushing a full re-flow

Full pipeline flush (seeds → merge → absorb → thin → classify → relink); commits
`113be4a` … `0534a1a`, rationale in their bodies.

**The layer split now in force** (`f98808d`):
- **seed layer** — `lib.seed_thin.thin_safe` (kmk + ikmk builders): only removals
  that cannot move a weight — same-weight twins in a bucket collapse to one,
  weightless records capped at three per bucket, curated records never. Exists for
  volume (merger ~20 min instead of hours).
- **merged layer** — `thin_final_weight_lists.py`, pipeline phase `2b/5` after
  absorb: the real §9a envelope (min / middle / max per resource), skips coins with
  disagreeing fineness, never drops `erroneous`/`suspect`, never touches `sources[]`.
- Residual caveat (in `thin_safe`'s docstring): same-weight twins landing in
  DIFFERENT merger classes lose a reading in one of them.

**Other fixes**: `3c48efd` held `issuing_entity` survives a re-seed that moves the
coin; `0863e94` thinning never drops curated records; `adc89d2` wear alone no
longer splits one type (identical non-empty catalogue bypasses the 5 % gate only).
Curator calls: nine weights flagged (`kmk-275886` erroneous, eight suspect);
87 KMM specimens joined c5h74 / f6h15 / f6h14; three «Hede 13 ell. 39» pieces excluded.

**The pipeline needs TWO passes to reach its fixed point.** absorb enriches the
existing final foundation (D3), so pass 1's output is pass 2's input: pass 1→2
changed `final/` in 4 files, pass 2→3 nothing. A diff after one run is not
breakage; **re-run until `git status` is clean before committing `final/`.**

**Open, deliberately untouched:**
- 9 coins disagree silver ↔ billon between `final` and the recomputation
  (`audit_curation_loss`, `metal=9`). Pre-dates this session.
- `kmk-693172` — a `danish_realm` `no_merges` member resolving to no seed; blocks
  pre-commit Check 5 (pre-existing). Re-pointing it is a `v2-merge-coins` call.

## 2026-09-10 (cont.) — reflow-home-drift fixed systemically (§CV + rebucket) + Option Z

Resolves the previous entry's **DEFERRED 2**. Root cause of the ~13-coin
relocation on a full re-flow: a seed entry's physical `data/v2/seed/<src>/<entity>.yml`
bucket had drifted from `_home_entity(issuing_entity)` (issuing_entity edited in
place without a builder re-run, or the `139df3f` royal_slesvig split moved
Husum/Haderslev), and the merger buckets by the seed FILE → wrong seed_unified/final
→ audit_v2 I1 hard-block. HEAD finals had been hand-relocated once; the re-flow
reverted them.

Shipped (3 commits):
- `3b34adf` **fix:** §CV — `_home_entity` (`scripts/lib/v2_seed_writer.py`) now homes a
  joint `issuing_entity` by CONSUMES-MAP SUPERSET (the member whose consuming-page
  set ⊇ every other's), replacing the hardcoded-`royal_holstein` overlap. Fixes the
  cross-entity Christian IV Portugaløser/Ungersk-Gylden joints (c4h5a/c4h8a → royal_slesvig)
  with zero royal_holstein regressions. `audit_v2` imports `_home_entity`, so audit ↔
  seed-writer stay in lockstep. New memoised `_consumes_page_map()`.
- `434b2aa` **build:** `scripts/maintenance/rebucket_seeds.py` (standalone, all-source
  generalisation of `write_v2_seed`'s purge+regroup — moves a drifted entry verbatim to
  its `_home_entity` bucket, aliases resolved, `_curation_holds` preserved, never re-derives
  issuing_entity) + **pre-commit Check 8** (`rebucket_seeds.py --check` HARD-BLOCK on staged
  `data/v2/seed/**`) so the drift can never reach a re-flow again.
- `fd231b5` **data:** re-home 13 drifted seeds + Option Z + full re-flow (27 files).

**Option Z (dk-bruun-14770, Christian III «1 Goldgulden» 1536):** mint resolved to
**Roskilde only** → scalar `issuing_entity: danish_realm` (was the 2026-08-26 joint
`[danish_realm, royal_slesvig]`, which §CV would have homed to royal_slesvig against the
curator's «homes here»). Two specialist sources fix the mint and reject the other readings:
danskmoent (Galster-131) «Roskilde, af Galster fejlagtigt henført til Gottorp» (Gottorp is
Galster's OWN error, carried by KMM kmk-81473); Bruun lot 14258 «despite the reverse legend
MON NOVA AVREA SLESVICENSIS … probably minted in Roskilde» (the Schleswig reading, carried by
Numista N#379084). Demoted kmk-81473 + dk-numista-379084 `mint_verified→false`; final
`issuing_entity` hand-frozen scalar (it's `_FOUNDATION_IMMUTABLE`) and mint cleared to Roskilde
(the absorb `_collect_mints` union-ratchet otherwise re-keeps a stale reading).

Validation: `audit_v2` I1 **14→0**; `verify_reflow` **0 losses** vs HEAD; `audit_lost_citations`
**0**. Full pre-commit hook passed on the data commit.

**OPEN — latent regression spun off (task `task_1ef16042`, analysis).** kmk-81473's
`mint_verified` had been silently flipped false→true by a regen, contradicting its own
2026-08-20 `_curation_holds`. Restored to false in `fd231b5`, but the ROOT (why the hold on a
`*_verified` boolean flag did not survive the kmk re-seed / merge) is unfixed and likely affects
every curated `*_verified` hold. New session to analyse `build_kmk_seed.py::CURATED_FIELDS` +
`seed_merge.py::merge_seed` hold-application; READ-ONLY until curator approves a fix.

## 2026-09-10 — Guldkrone pass; two items deferred for a next-pass ANALYSIS

Shipped this session (5 commits): NGC KM-40 Guldkrone stub
merge (`3e2d805`), NumisMaster/NGC single-krone template weights flagged
`erroneous` (`39e2d62` + `cdb4807`), all 9 Guldkrone coins reclassified
`kind kurant→tarif` (`4c65280`), and `c4h28` (Christian IV «2 Guldkrone» Hede 28)
`fraction 2→1` (`6995600`). Root story: Hede 1957 fn (1) — Christian IV's
«2 Guldkrone» is physically Frederik III's «1 Guldkrone» (~6 g), so the ~6 g
piece is fraction 1; NumisMaster/NGC carry a single-krone «type weight» (2.973 g,
and 3 g ucoin / 5.996 g on the 2-Guldkrone) glued onto every «Krone» KM.

**DEFERRED 1 — stale fuss fraction-«2» comment (needs analysis first).**
`data/shared/fuesse.yml::guldkrone.fractions."2"` carries a comment framing
«2 Guldkrone (Christian IV Hede 25/28 series 1619-1648 … Δ exposes ~50 %
Krone-unit-redefinition-seigniorage)». That model is NOT what the data does:
km-74 (Hede 25) and now c4h28 (Hede 28) are both fraction **1** (the 6 g piece),
and fraction 2 (soll 11.99 g) is used only by the GENUINE ~12 g double-doubles
(f3h45 real 11.18 g, f4h30 1701). Rewrite the comment to describe the real 12 g
Frederik III «2 Guldkrone», dropping the «-50 % Hede 25/28» framing — but
verify the f3h45 / f4h30 metric and the Hede-1957 naming first (§0b) before
touching the prose. Curator wants analysis, not a blind edit.

**DEFERRED 2** — resolved in the entry above (§CV + rebucket + Option Z).

## 2026-09-04 (3) — two markers on a source's reading: «(*)» suspect, «(!)» erroneous

**Shipped.** Curator direction, 2026-09-04, in three corrections that shaped it:

1. «ми не можемо просто видалити дані яке дає джерело, якщо вони некоректні —
   ми лише можемо позначити їх як некоректні, але не видаляти»
2. «"підозріле" це не зовсім коректний відтінок, тут ми точно знаємо що помилка»
   → the strong mark is **erroneous**, not «suspect»
3. «до рендера і до дельти мають доходити і підозрілі, і помилкові» → both are
   **presentational**; neither is withheld from the arithmetic

So there are now four states on a measurement, and the line between the two new
ones is exactly what can be shown:

    verified: false   we could not confirm a value                  → «(?)»
    suspect           the reading does not fit, we can't show why   → «(*)»
    erroneous         the reading has been shown to be wrong        → «(!)»
    display: false    a redundant duplicate                         → nothing

Both reasons are `I18nText` triples — the reader sees them in the tooltip, so
they are reader-facing prose (§0z): no project paths, no §-references. The
internal argument stays in `_curation_holds`.

**Neither marker touches the arithmetic.** `normalise_field` returns marked
readings like any other; they become the primary reading, the Feingewicht, the
Δ. Withholding would change the numbers on our own authority and, where the
marked value is the coin's only reading, erase the Δ over a judgement the
reader never got to see. `compute.marker_reasons` is the parallel channel the
template matches group-by-group to hang the mark beside the figure — both the
plain and the multi-specimen sub-row paths (14 sites).

**The one place a marker DOES act is merge matching, and only `erroneous`**
(`merge_seeds_cross_source._accepted`, applied in `_fineness_repr`,
`_weight_repr` and the metal normalisation). Curator: «якісь правила мерджів
можуть зважати на ці мітки, якщо вони не дають здійснити коректний мердж». It
is §4's «an unverified value cannot DISPROVE a merge», one step stronger — and
it is load-bearing: with the blanket 3,5 g / .986 still counted, a real KMM
specimen of the 1624 Sonderburg type would not merge into its own type
(sonderburg 61 → 60 unified). `suspect` deliberately does NOT filter there: a
reading we have not disproved is still evidence.

`audit_v2` I11 blocks a blank reason and a `<field>_verified: true` on a coin
whose every reading of that field is erroneous. 15 tests in
`tests/test_erroneous_readings.py`.

**Applied to two real cases**, one of each kind:

- **erroneous** — the five ducal Goldgulden. NGC/NumisMaster's 3,5 g / .986 is
  back on all five after having been deleted earlier in the session; that
  deletion was the mistake this mechanism exists to prevent.
- **suspect** — `kmk-156725`, the Nationalmuseet's Nobel of Frederik I at
  17,4 g. Grounds: every other Nobel in the corpus runs 13,58-15,11 g, the
  Møntordning af Sommeren 1514 implies 14,616 g, and the 17,4 g is the outlier
  inside its OWN coin's weight list (`unified-dk-galster-f1g-69`, beside
  14,375 g). A heavy specimen, a mis-keyed digit and a different attribution
  all remain open — hence a doubt, not a demonstration.

### Fixed in passing

Re-flowing `danish_realm` resurrected the phase id `I-1602` on six coins: the
2026-09-04 renumbering renamed it to `II` in the FINALS but not in
`classification_decisions/danish_realm.yml`, which is authoritative, so absorb
put it straight back and the render dropped all six. Renamed at the decision
surface. **The lesson generalises: a phase/fuss rename must be applied to the
decision surface first, or the next absorb undoes it.**

### Next

1. **Sweep for the rest of the erroneous class.** §13.15's diagnostic finds
   them; start with the 43 Ducats at exactly 3,5 g / .986 in the same NGC cache.
2. **`verify_reflow` identifies a measurement entry by its `source` STRING**
   (`IDENTITY_KEYS`), so relabelling a source reads as a loss and hard-blocks
   the commit though every value is present. Bypassed twice with the curator's
   agreement. The fix is to treat a shrink as a relabel when the numeric value
   set has not shrunk — which is what the tool's own docstring says it means.
3. **The fuss move to `rhinsk_gylden_fod` is still open** and still needs the
   periodisation decision: declared only on the Denmark page (I 1496-1547 ·
   II 1563-1584 · III 1625-1632), so 1619 / 1624 / 1664 have no window, and it
   is not declared on the schleswig_holstein page at all.

## 2026-09-04 (2) — the «Goldgulden» five: settled, and a new source worth harvesting

**Nothing committed for the coins yet** — the documentation below is committed;
the data repair is the next step and is described at the end.

### What was settled

Five ducal Schleswig-Holstein coins sat on `reichsdukatenfuss` at 3,5 g / .986:
Gottorp KM 53 (1619), KM 79 (1627), KM 108 (1664); Sonderburg KM 10 (1619),
KM 24 (1624). Their only sources were NGC and NumisMaster — **one lineage**, not
two («powered by NumisMaster»).

**They are Rhenish Goldgulden, not ducats.** Weighed specimens run **3,08-3,22 g
(mean 3,160 → 74,0 per rough Cologne mark)** against the ducat grid's 3,4904.
Full evidence and the general diagnostic are written up as
**`docs/SOURCES.md` §13.15** — read that before touching any catalogue-sourced
metrology, because the failure mode generalises: *a catalogue with no parameter
for a denomination may fill the field from the neighbouring denomination, and
nothing in the record says so.*

The single strongest argument needs no weighing: Numista's own currency header
for the Danish duchies reads «1 Ducat = 2 Thaler · 1 Goldgulden = 1.5 Thaler».
At 3,5 g × .986 the two would be worth the same and that line would be nonsense.

Per-coin state:

| coin | Lange | evidence | verdict |
|---|---|---|---|
| Sonderburg KM 24 · 1624 | **557** | 4 weighed: 3,22 (Künker 176/5749 → Oslo 42/414) · 3,19 (coll. K = Lange's own) · 3,16 (KM, double-struck) · 3,08 (Berlin) | settled |
| Sonderburg KM 10 · 1619 | **527** | 1 weighed: **3,15 g**, KM GP 888 ex Mayntzhusen | settled |
| Gottorp KM 53 · 1619 | — | Jensen 2002 p. 39: «en unik guldgylden fra hertug Frederik 3. 1619», bought Osnabrück (Künker) spring 1998 for Den kgl. Mønt- og Medaillesamling; unique | settled as Goldgulden, **no weight** |
| Gottorp KM 79 · 1627 · KM 108 · 1664 | — | tariff incompatibility only | strong indirect, **no weight, no Lange** |

### A new source worth treating like the Bruun PDFs

**Jørgen Steen Jensen, *Hertug Hans den Yngre*, København 1971** — free, full,
at <https://www.danskmoent.dk/pdf2/JSJ_HdY.pdf> (18,7 MB, 91 pp.). Catalogued as
**`docs/SOURCES.md` §3a**, together with his 2002 *Sønderjyllands mønthistorie*
and the collection sigla needed to read either.

Measured contents, from a local text extraction (150 k chars, extracts cleanly
with `pypdf`):

- **~36 numbered type entries** covering Hans den Yngre **and his five sons** —
  the Sønderborg, Nordborg, Glücksborg and Plön lines.
- **119 weighed specimens**, each with a collection siglum. This is per-specimen
  metrology of exactly the kind §9a wants and that no online catalogue has for
  these houses.
- **A Lange number on essentially every entry** — the cheapest route we have to
  Lange, which is otherwise paper-only at ~1 795 € (§5).
- Legends transcribed for obverse and reverse, variant letters (a/b/…),
  mint, mintmaster, and notes on later debased re-strikes.
- A **Stempelkatalog** of surviving dies at the Royal Coin Cabinet, and
  **fundlister** (9 hoard lists) with deposition dates.

**What it is worth against our corpus, measured 2026-09-04:** we hold **67 coins
of 1560-1700 in `sonderburg_duchy` (47), `norburg_plon_duchy` (18) and
`glucksburg_duchy` (2)`. Of those, **29 have no weight at all**, and only **34 of
67 carry a Lange number**. Jensen 1971 can plausibly close most of both gaps in
one pass — and, unlike a catalogue default, every figure it supplies is a
weighing of a named specimen in a named cabinet.

**Suggested shape if this becomes a harvest** (it is a book, not a website, so
it does not fit the 4-phase pipeline as-is — closest precedent is the Bruun PDF
route, `docs/SOURCES.md` §1.3):

1. Park the PDF next to the Bruun ones under `scripts/cache/` and write a
   parser for the catalogue block: entry number → nominal, year, legends,
   Lange number, then the specimen list (siglum + mass + provenance).
2. Match to our finals on `(issuing_entity, nominal, year)` plus the Lange
   number where we already have one — Lange is the load-bearing key here, in the
   §9.4 sense.
3. Merge per §9a: every specimen contributes its own `weight_rough_g` entry
   with a `source` naming the cabinet, and its own `sources[]` citation. Do NOT
   collapse to one representative weight — the 3,08-3,22 spread on Lange 557 is
   exactly the variance signal §9a exists to preserve.
4. Watch the §9a **intra-sub-variant thinning** rule if a single cabinet
   contributes ≥5 specimens of one sub-variant.

**Access caveat** (also in §3a): danskmoent's host challenges `curl`; `WebFetch`
refuses >10 MB; Chrome's PDF viewer gives no text. Download in a browser, then
`pypdf` locally.

### Also recovered: the KMM search route

`samlinger.natmus.dk/objectbrowse?keyword=A,B` — **comma ANDs, a space returns
zero** even for combinations that exist. Result links are `/kmm/object/<id>`.
This partially reopens what `docs/TODO.md` §DB recorded as lost enumeration;
written up in **`docs/SOURCES.md` §13.14**. Used it to establish that the unique
Gottorp 1619 guldgylden is *not published online at all* (the museum's Gottorp
gold is 12 objects, all already in our cache) rather than merely missing locally.

### Also corrected

`docs/SOURCES.md` §5 named Lange as «Aage Lange, *Sønderjyske og
slesvig-holstenske Mønter 1522-1864*». No such work exists in any search; every
citation traced resolves to **Christian Lange (1845-1914), *Chr. Lange's
Sammlung schleswig-holsteinischer Münzen und Medaillen*, I-II, Berlin
1908-1912**. Row rewritten with the volume split — **Band II** is the one this
project needs — and with the availability findings (no free full text anywhere;
Google Books Band II is searchable snippet-only, and «Sonderburg Goldgulden»
hits pp. 2, 10, **322**).

### One retraction

Mid-investigation I offered «an orb on the reverse marks a Goldgulden, arms mark
a ducat» as a discriminator. **Withdrawn.** danskmoent describes the reverse of
Lange 527 (Sonderburg 1619) as *våbenskjold* — arms — while NGC calls it «Orb in
inner circle». The design is not a reliable discriminator; weight is.

### Next step — the data repair, NOT yet done

1. **Metrology.** Replace the 3,5 g / .986 template on the two Sonderburg coins
   with the weighed specimens (§9a list form, one entry per specimen, each
   citing its cabinet). The NGC/NumisMaster `weight_rough_verified: true` and
   `fineness_verified: true` were set by the seed builder on a default and must
   go to `false` where no real figure exists — **no source gives a fineness for
   any of the five originals**; Jensen gives one only for the debased ~1633
   re-strike (521-569 ‰, and that is a forgery figure, not the standard).
2. **Catalog.** Add `lange: '527'` / `'557'`, plus the Sieg / Sømod / Storgaard
   numbers from danskmoent's concordance tables.
3. **The fuss move** — the part needing a curator decision. Moving them to
   `rhinsk_gylden_fod` is not free: that fuss is declared **only on the Denmark
   page** (phases I 1496-1547 · II 1563-1584 · III 1625-1632), so 1619/1624/1664
   have no window there either, and it is **not declared on the
   schleswig_holstein page at all** — moving them as-is would drop all five from
   that page. Needs: declare the fuss on the SH page with its own phases, decide
   the Danish windows, then move with dict-form phases per the 2026-09-04 (1)
   entry.
4. Gottorp KM 79 and KM 108 stay unresolved for want of a weight; Lange Band II
   or a future auction appearance is what would settle them.

## 2026-09-04 — Dukatfod: phases renumbered, the 1602 Δ target, one deferred question

**Two commits, local, not pushed** — `77af47d` (mechanism) + `fa19df4` (data).
Preceded by `f58576d` yesterday, which gave the Danish Dukatfod card its
per-phase Grundwerte rows and the honest statement of the Hede-vs-Krause split on
the fineness.

**Denmark's reichsdukatenfuss phases are now I · II · III · IV** (1531-1601 /
1602-1611 / 1623-1726 / 1726-1802). `I-1602` is gone. If you have a stale phase
list anywhere, that is why.

**A phase id is per-page, and this fuss is where that bites.** Denmark and
Schleswig-Holstein now BOTH declare I·II·III·IV for it and mean different years
(SH: 1600-1726 / 1726-1771 / 1771-1813 / 1813-1871). Consequences worth knowing
before touching anything here:

  * A scalar `phase` on a coin in an entity both pages consume (royal_holstein,
    royal_slesvig, the four duchies) is right on at most one page. 26 coins now
    carry the dict form; `resolve_phase_for_location` raises a hard ValueError if
    a dict lacks the page's key, and it runs BEFORE the `consumes_entities` year
    cap — so both keys are mandatory even where a cap means one page never shows
    the coin.
  * `soll_fein_by_phase` on the SHARED fuss reaches every page. Denmark's 1602
    target therefore lives in `denmark.yml::fuss_periods.reichsdukatenfuss.
    fractions` (the new `FussPeriod.fractions` override, merged per fraction key
    by `categorize._merge_fractions`). Putting it on the shared table made the
    two Plön ducats of 1760 measure against the Danish 1602 ordinance.

**The rule that governs any further Δ re-targeting** (curator, 2026-09-03):
an ordinance that changes the parameters sets the expected value, and its phase
legitimately gets its own target; where no ordinance exists and the fine content
simply fell, that must SHOW as a deviation and the phase gets no target. Case by
case — no blanket per-phase table. Under it exactly one Danish phase qualifies
(II, the Forordning af 8. september 1602). Phases III and IV run at .979 with no
located instrument and keep the imperial target on purpose.

**`lib.yaml_io.edit_coin_field` is unsafe for any field ABOVE `id:`.** It bounds
a coin block from its `id:` line to the next coin's, but `data/v2/final/*.yml`
order fields `fuss, phase, kind, nominal, ruler, issuing_entity, fraction, id, …`
— so editing `phase` or `fraction` through it targets the FOLLOWING coin. The
`expect_contains` guard caught it here; without that guard it would have written
silently. Not fixed — worth fixing at the helper (bound on the `  - ` dash), and
worth checking whether any past one-off used it on such a field.

### Deferred, needs research before anything is touched

**Five «1 Goldgulden» records sit on `reichsdukatenfuss`**: `unified-ngc-1156100`
(Gottorp 1619), `-1157533` (1627), `-1156101` (1664), `unified-ngc-1161408`
(Sonderburg 1619), `-1206707` (1624). Every OTHER Goldgulden in the corpus sits
on `rhinsk_gylden_fod` — including Christian IV's own of 1625-1632, Hede-attested
at .76, contemporaneous with three of these. All five are NGC/NumisMaster-only
and carry exactly 3,5 g + .986, which is that catalogue's blanket default rather
than a weighing (its `actual_weight_fein` is just 3,5 × .986 ÷ 31,1). Same class
as Numista N#355730, corrected 2026-07-10.

**Hypothesis, not a finding.** It needs Lange, or the Krause German-States entry
text, before anyone moves them. And the move is not free:
`rhinsk_gylden_fod` phases are declared ONLY on the Denmark page (I 1496-1547,
II 1563-1584, III 1625-1632), so 1619 / 1624 / 1664 have no window there either,
and the fuss is not declared on the Schleswig-Holstein page at all — moving them
as they stand would drop them from that page entirely. So the task is: settle the
attribution first, then decide the periodisation on both pages, then move.

### Noticed while measuring, out of scope

The Denmark page silently DROPS 1896 coins whose phase id it does not declare —
overwhelmingly `unified-kmk-*` with no year information. The build prints a
five-line summary and exits 0. Unrelated to the above; worth its own look.

## 2026-09-03 — TODO §W closed: prose linter realigned, 530 errors → 0, hook promoted

**Pushed.** §W is done; `docs/TODO.md` §W carries the full account. What
the next session most needs to know:

**CLAUDE.md §2 was rewritten** (three tiers, curator direction 2026-09-02).
Tier 1 — a quote, title, URL or named instrument carries the SOURCE's
form AND its own LANGUAGE, untouchable. Tier 2 — standard names identical
across DE/EN/UK. Tier 3 — period register in our own DE prose is a
RECOMMENDATION, warning-only, and can never block a commit. If you find
yourself about to «fix» a `Münz-` spelling, check which tier it is first.

**`audit_prose` now HARD-BLOCKS on errors** in the pre-commit hook
(warnings never will — that is a rule, not a backlog). Baseline is 0
errors / 154 warnings. If a new error-tier hit looks wrong, tighten the
rule in `scripts/audit_prose.py`; there is no per-line suppression, on
purpose, and `tests/test_prose_tier1_source_form.py` pins the boundaries.

**Two things that look like defects and are NOT** — both measured, both
recorded in the linter docstring so they are not re-litigated:
  * monolingual curator fields (`_curation_holds`, decision `reason`,
    `scope_note`, `match_uncertainty::why`, `events.<key>.note`) are
    role-1 BY DESIGN. The tell: a {de,en,uk} triple was built to be read
    by someone; a plain string was not. 4984 of 5039 `§`+digit marks
    live there and are correct.
  * `seed_unsorted` appears 118× in the rendered site — all markup
    (`id="fuss-seed_unsorted"` anchors, class attributes, one comment).

**New tool:** `scripts/maintenance/rewrite_verification_notes.py` —
idempotent, dry-run by default, line-based (no YAML round-trip, so it is
immune to the reformat trap `lib/yaml_io` documents). It healed 32 196
strings across seed / seed_unified / final without a re-flow. Extend its
family list rather than writing a new script for the next boilerplate.

**Method note worth keeping.** Every gate this session was
`--validate-only`, which does NOT render. The first full build at the end
found three Danish instruments that step 7 had missed in
`refs_pool.yml` — grepping the RENDER caught what grepping the source
did not, because step 7 was scoped to `locations/*` + `fuesse.yml`.
Build and grep `site/` before declaring a prose sweep finished.

**Open, needing a curator call:** 13 fields carry genuine unsourced
hypotheses in rendered prose («vermutlich Schreibfehler», «probably
struck by Schwabe» from similarity, «wahrscheinlich verwechselt
Bobzin»). Each needs a §0b-1 verification step, or a decision: label as
hypothesis, or move from `note` (rendered) to `verification_note` (not
rendered). Listed in the §W step-5 commit body (`9f5a69d`).

## 2026-08-29 — §DB re-probed and measured; the re-harvest is NOT worth building

**Blocker re-verified.** `api.natmus.dk/search/public/raw` now fails at TLS
(cert `CN=api.natmus.dk` expired 24 Aug 2026); ignoring the cert it answers
HTTP 403 «Web App - Unavailable». Permanently gone, not an outage. The web
route `samlinger.natmus.dk/KMM/object/<id>` is HTTP 200, server-rendered,
carries the rådata JSON. Recorded in `docs/SOURCES.md` §13.14.

**Measurement (the point of the session).** The 14 911 index-less ES objects do
NOT convert: a stratified sample of 404 of the 11 033 uncached ones gains an
index 3.2 % of the time, and only **2 of the 404 are in the kmk seed at all** —
the population is ~99.5 % material the seed builder already filters out. The
real target is the **4 107 catalogue-less seed coins**, of which **84 would gain
a real index from rådata already on disk** (52 hede, 21 bergsoe, 6 schou,
5 lange, 3 galster, 4 others). The remainder are KMM recording no index
(«Hede» with no number ×244, «Ubestemmelig», «FALSK»), not a parser gap.

**Awaiting the curator.** Whether to run the local no-network re-seed for those
84 now — it is a whole-corpus re-flow (§9b snapshot/diff + `verify_reflow.py`
0 losses) for an 84-coin gain — or let it ride along with the next re-flow.
Nothing has been flowed into the seeds.

**Shipped:** `741c5a1` explicit cf-reference guard in
`build_kmk_seed._raadata_catalog` + `tests/test_kmk_raadata_cf_refs.py`
(behaviour unchanged, previously safe only by regex accident); `ad10ff9` docs;
`3f237b4` cache pointer (519 new rådata sidecars). 3 commits local, not pushed.

## 2026-08-25 — V1 atavisms DONE, and two parser defects they uncovered

Five commits: `bf66e64` `45112a5` (bruun parser + its 15 coins), `6893067`
(129 twins), `3a3e253` `dc6500c` `3c3dc79` (ngc parser, ucoin routing, the
last 8 twins), `ea21a9e` (SOURCES §13.13). 100 commits ahead of origin,
nothing pushed.

### The V1-atavism task is closed

All 137 V1-legacy ucoin twins are gone. The premise held: a ucoin `tid=`
identifies one type and should yield one seed, and 137 of them yielded two
— a modern `*-tid-*` and a V1-era `km-…`. The twin carried no scalar field
the modern seed lacked and cited only that same ucoin URL.

Audited across ALL nine sources on four independent signals — id convention,
one-record-many-seeds, one id in several entity files, cross-source citation.
**The residue was confined entirely to ucoin**, and signals A and B named the
same 137 seeds from two directions. bruun / hede / galster / numista / ngc /
ikmk / kmk are 100 % uniform. numismaster's two id prefixes are its per-country
builder output, not a defect. ucoin's `tid-tid-*` shape (1863) is cosmetically
odd but every one is backed by a cache record.

### The thing that was misdiagnosed twice — read this before trusting a twin story

`6893067`'s message says the twin carried a mint from V1 curation. **That is
wrong.** Both twins have `mint: None`. What the twin carried was
`issuing_entity: royal_holstein`, which the V1 curator read from ucoin's own
`period` label. Corrected in `3c3dc79`; noted here because the wrong version
is in the git log and will be read again.

`period` on ucoin is two different fields wearing one name: usually a currency
era («Rigsdaler (1625-1699)»), but for part of the catalogue a TERRITORIAL
series («Glückstadt (1617-1773)», «Holstein-Gottorp-Rendsburg», «Duchy of
Schleswig-Holstein»). The builder routed the German series and had no entry for
the two Danish-filed ones, so 53 coins sat in `danish_realm` while every
mint-aware source put them in `royal_holstein` — 436 kmk, 63 hede, 62 numista,
46 bruun, 15 numismaster, 3 ikmk, and the mint registry itself. `dc6500c` fixes
it. Both consuming pages keep the coins.

### The cascade that was a symptom, not a cost

Removing the last 8 twins first LOOKED expensive: it turned four per-entity
merge groups into cross-entity ones, which imports the completeness invariant
and demanded §9.4 calls on 20-plus further coins — including bare KM numbers
colliding across the Denmark and Schleswig-Holstein volumes, exactly the trap
§9.4 warns about. That whole cascade was an artefact of removing the twin
BEFORE teaching the builder to derive what it held. With `dc6500c` in place the
groups stay inside one entity and the gate never fires. **If a fix starts
cascading into curator decisions far from the task, suspect the direction.**

### Two parser defects found underneath

- **bruun §9.1 over-fired on the next lot's headline.** A lot block runs to the
  next lot-number line, so it swallows the catalogue's section headline for the
  FOLLOWING lot — «Extremely Rare and Historically Interesting Pattern» — which
  precedes the lot it describes and can only land on the previous one. 15
  NGC-graded circulation coins were excluded by a word appearing nowhere in
  their own description. The price estimate closes the description; the §9.1 and
  §9.2 tests now run against that slice. Recovered 7117 (the Hede-39 specimen
  CLAUDE.md §0b-1 is written about) and 7928 (the sole Bruun citation behind
  c7h13).
- **ngc could not read a date written against the mintmaster initials.** NGC
  writes the cell as «1711IW» / «1671GK», so the trailing `\b` never matched: 40
  records lost a legible date, and the same string was read as damage (12 flagged
  partially illegible). NGC marks damage with `z` alone. This surfaced because
  three NGC records had been drawing their years from the ucoin member of their
  class and went yearless when it moved entity.

### NGC Denmark — there is NO harvest gap, and the metric that says otherwise is wrong

Recorded in `docs/SOURCES.md` §13.13(a2)/(a3). Short version: `DENMARK` has
exactly two sub-regions, `GLÜCKSTADT` (97 types) and `HOLSTEIN-GOTTORP-RENDSBORG`
(4); `NORWAY` has none; all 101 cuids are already in the `denmark` tree from the
All Regions walk. The two sub-region directories hold only a `_listing_raw.json`
that was never ingested, which is why `fetch_ngc.py status` shows `0 / 0` for
them — that is an un-ingested listing, not a shortfall.

**Do not audit NGC completeness against duid counts.** «Listing says N duids,
parsed record has M rows, so N−M are missing» reported 756 missing in-scope rows
across 311 types. All fictional. Verified live: cuid 1051684 is listed with 3
duids and its page renders ONE row, identically at duid 1239857 and 1239858 —
the duid in the URL selects nothing. Audit on cuids covered.

### Still open

- **53 new Hede types** await classification; `c5h30` and `f3h25` are off-strikes
  → §9.3 exclusions.
- The rest (pending promotion, Hede 74 vs 123, four detached specimens, `_catalog`
  ranges) is listed once, under 2026-08-25 (later).

## 2026-08-25 (later) — Schleswig gets its own entity, and Denmark's reach follows vassalage

Five commits: `62c036b` (research), `139df3f` (the split), `e7747eb` (vassal
bounds), `826bd25` (ruler houses + a correction), `ef9c1e3` (Gottorp's card).

### What was actually wrong, and it was not what the brief said

The brief «OPEN, BIG — an entity for the Duchy of Schleswig» rests on the
premise that filing pre-1544 coins under `gottorp_duchy` is an unnoticed
contradiction. `trace_coin why` says otherwise: a curator call of 2026-07-16
put a 1531 ducal Goldgulden there deliberately, on the legend «FRIDERICVS D
HOLSACI / MO NOV AVREA SLESVICENSIS», date in plain view. So the routing is
decided and stands; what was inconsistent was the entity's own DESCRIPTION.
The full research is in `docs/research/duchy_of_schleswig_entity.md`.

The second premise had also expired: the Danish-spelling KMM records are no
longer misrouted anywhere. All 52 sit in `danish_realm` with the right entity
and simply lose their region, because `Slesvig` is not an alias in the registry.

And `place: Slesvig` in KMM is not one attribution: **46 of the 54 records sit
on a single register page, protocol III p. 129**, spanning 1523-1563 and three
rulers. Frederik I's twelve are supported (Wilcke 7-2 p. 186-187, the mint moved
Husum → Slesvig at his 1523 accession); Frederik II's twenty-eight are
contradicted — danskmoent puts his mints at Bremerholm and Frederiksborg, Wilcke
puts the duchy mint at Flensborg 1566-1571, and Gottorf had been Adolf's since
19 August 1544. **Do not promote that group into a territorial entity.**

### royal_slesvig

`royal_holstein` stood for the king's share of BOTH duchies. Schleswig was a
crown fief outside the Empire; Holstein an imperial fief from 1474 that joined
the German Confederation in 1815 — the 1806 incorporation patent was «faktisch
wirkungslos». The new entity takes the king's Schleswig mints — Flensburg,
Husum, Haderslev. Rendsburg looks like a border case and is not: a noble
arbitration of twelve knights ruled the town to Holstein in 1250.

**The trap this hid.** `CROWN_MINT_REALM` and `HOLSTEIN_CROWN_MINTS` are both
DERIVED from the registry, and the second was keyed on `royal_holstein` alone.
Splitting would have silently dropped the three Schleswig mints out of the
build-time widening gate and stopped their coins reaching the SH page at all.
Renamed `DUCHY_CROWN_MINTS`, keyed on both duchy realms, old name aliased.

### Denmark's consume list now states a rule

Curator direction: a region belongs on the page for the years it belonged to
the Danish king, directly or through a vassal — and **a vassal at war with his
suzerain does not belong**.

| entity | to | why | coins beyond |
|---|---|---|---|
| `royal_slesvig` | 1864 | crown fief throughout | 0 |
| `royal_holstein` | 1864 | held by the king in person as duke | 0 |
| `gottorp_duchy` | **1656** | Friedrich III took the field with Sweden in 1657; Roskilde 24 Feb 1658 ended the fealty | 141 |
| `sonderburg_duchy` | **1667** | «Nach einem Konkurs 1667 ging der Sonderburger Anteil … an den dänischen König» | 0 |
| `norburg_plon_duchy` | **1761** | Norburg failed 1669, lands to Plön 1679; Plön «erlosch 1761» | 0 |
| `glucksburg_duchy` | **1779** | elder Glücksburg line «erlosch 1779» | 0 |
| `danish_norway` | 1814 | Kiel | 192 |

Denmark went from 14 Gottorp coins to 258, plus Sonderburg 56, Norburg-Plön 45,
royal_slesvig 38, Glücksburg 7.

### A measurement I got wrong — the fourth of this session

I reported four coins wrongly on the Denmark page: undated Gottorp pieces of
Christian Albrecht and Karl Friedrich, whose reigns lie wholly after 1658,
slipping past the consume-window because `build.py` tests it only when
`year_first` is not None. The bypass in the code is real. **The consequence was
not.** An undated coin never reaches ANY page — it is dropped earlier and
structurally for having no year, which this very file already records. Measured
before and after: 0 either way, byte-identical pages. Corrected in `826bd25`;
`e7747eb`'s message still carries the wrong claim.

Same shape as the NGC duid gap and the «11 284 blocked buckets»: a conclusion
drawn from code without checking the end of the chain. **Check the render.**

Kept anyway, because the homonymy under it was genuine: `reign_window("Frederik
3")` answered the Danish king 1648-1670 to anyone, including a Gottorp coin
whose Friedrich III ruled 1616-1659. `HOUSE_REIGNS` is now keyed by issuing
entity, with the Gottorp line from Adolf I 1544 to Paul 1773.

### TWO BACKLOGS, and they are not the same queue

Asked whether the unclassified Hede types are among the `pending`. **They are
not**, and the distinction matters for planning:

- **`pending` — 1627.** Unified classes with NO final entry. They do not render.
- **`fuss: seed_unsorted` — 13 273 of 14 993 finals (88 %).** These ARE in final
  and DO render; they just carry no Münzfuß. By phase: kmk 7842, ikmk 2495,
  numista 995, ucoin 716, ngc 424, hede 193.

Every one of the 1189 Hede seeds with a unified class is in final. The Hede
slice of the unsorted backlog is 212 coins, not the 53 figure I had been
carrying — 53 was the count of stubs the parser fix ADDED, some already
classified.

### Still open

- **`pending` promotion** — 1627. Reasoning for the order at «NEXT UP» above.
- **`fuss: seed_unsorted`** — 13 273. The far larger backlog, and untouched.
- **Hede 74 vs 123** — curator call; the duplicated `numista: 22576` should
  leave one side.
- **Four specimens** from the 3a/3b splits need a German-lands `issuing_entity`.
- **`_catalog` ranges** — only kmk was fixed.
- `c5h30` and `f3h25` are off-strikes → §9.3 exclusions.

## 2026-08-21 — mint source-fidelity pass, and what it left open

Eight parser/registry defects that all had the same shape: no error, no empty
field, just a confident value narrower than what the source said. Fixed in
`aa771d5`, `38369e6`, `f53986f`, `8e875c2` + the `_recorded_removals.yml` work.
Full re-flow done (re-parse NGC + Galster → re-seed 7 sources → merge → absorb),
`verify_reflow` clean, 45 tests in `tests/test_mint_source_fidelity.py`.

### OPEN — audit every `v1-*` / V1-carryover seed for atavistic indices

**The task:** find seeds whose catalogue indices NO current source attests —
values carried over from the V1 bootstrap and since orphaned. They look
authoritative, they key the cross-source merger, and nothing regenerates or
removes them.

**The case that surfaced it.** `km-358-h123-chr-v-1681` is a SEED whose id is a
V1 FINAL id, sitting in `data/v2/seed/ucoin/`, whose source URL is ucoin
`tid=96983` — the very same ucoin record that already produced `dk-tid-96983`.
So one ucoin entry became two seeds. The V1 copy additionally carries
`hede: 123` + `sieg: 129`, which ucoin does not publish at all (its page is
titled «Denmark 2 skilling, 1676-1681», no catalogue numbers): those came from
V1 hand-curation and are attached to the wrong coin — Hede 123 is the
Glückstadt 1681 type, ucoin's entry is the København 1676-1681 one (Hede 74A/B).
The two indices then split the coin into two finals across two entities and made
`Glückstadt` look attested on the København coin.

**Suggested shape of the audit:** for every seed whose id does NOT match its
builder's own id convention (`km-*`, `unified-*`, any V1 final-shaped id) — and
especially those in `data/v2/seed/ucoin/` — compare each catalogue index it
carries against what its cited source actually publishes in the cache. An index
no source gives is an atavism: either re-attach it to the coin it belongs to, or
drop it. Cross-check for duplicate seeds sharing one source URL (the ucoin
`tid=` collision above is unlikely to be the only one).

### OPEN — 108 Hede types with no record at all

`parse_hede._extract_index_stubs` and its caller both gate on
`^n?[cf]\d+hede$`, so every index page with a volume suffix is skipped:
`c4hede2` (15 rows), `c5hede1` (41), `f3hede1` (44), `f3hede2` (8), plus
`c4hede3` / `c5hede2` / `f3hede3` / `c8hede8c` (0 each). Those rows are Hede
types whose danskmoent index line carries no deep-page link, so the stub is the
only record they would ever get — and none exists. `c5h123` (2 Skilling,
Glückstadt, 1681, Sieg 129) is one of them, and KMM 736272 is sitting there
attesting exactly it with nowhere to merge.

Curator direction: fix the regex, then MEASURE how many of the 108 merge into
existing index-less museum records before deciding what to keep (§9 pass needed
— some are off-strikes, e.g. `c5h30` «Kobberafslag af påtænkt dukat», `f3h25`
«Sølvafslag af ukendt 1/2 Dukat»).

### OPEN — curator calls still outstanding

* **Hede 74 vs Hede 123** (2 Skilling Christian V): merge or keep apart. KM 358
  and Numista 22576 unify them; Hede, Sieg AND KMM separate them by mint
  (København vs Glückstadt). My read is «two types, Krause lumped» → `no_merges`
  + strip the duplicated `numista: 22576` from one side.
* **`Slesvig` as a mint alias.** `classify_mint_to_entity('Slesvig')` is None
  while `Schleswig` → gottorp_duchy, so the Danish spelling dies in
  `_split_place`'s nation-guard. KMM has 48 × «Danmark - Slesvig» (reads as a
  town) against 254 compound forms (read as the region). Aliasing it moves those
  48 into gottorp_duchy — measure before doing it.
* **City in `mintmaster`, 164 kmk seeds.** `_enrich_from_raadata` splits the
  rådata locality on `" - "` but not on `", "`, so «Tysk, Hamburg» reaches
  `_split_place` whole and comes back as mint «Tysk» + mintmaster «Hamburg».
  Fix: split on the comma too when the head is a territory (nation-classifier
  test), not a mint.

### OPEN — `_catalog` keeps only the FIRST number of a range

`build_kmk_seed._catalog` reads an index with `re.match(r"\d+[A-Za-z]?", rest)`,
so a printed range loses its tail: KMM's «Sch 20-22» becomes `schou: 20`. Found
while fixing the edition-year bug (2026-08-21) and deliberately NOT widened
there — the generic pattern feeds every catalogue, so broadening it changes many
values at once and needs its own measurement. The edition-year path DOES read
ranges (`Lange 1908, no. 306-312` → `lange: 306-312`), which is why that case is
already correct.

## NEXT UP — decided order, and why (2026-08-21, curator-agreed)

**Do NOT bulk-promote the 1628 pending coins yet.** The order is:

1. **V1-atavism audit** ← start here
2. ~~Duchy-of-Schleswig entity~~ — done 2026-08-25 (`royal_slesvig`)
3. one re-flow
4. THEN re-count what is still pending and promote the remainder

### What `pending` actually is (it was misread all session)

`pending` is not a data state and not a place a coin lives. It is a list of ids
in `data/v2/classification_decisions/<entity>.yml`. The coin itself sits in
`seed_unified` with all its data; it is simply ABSENT from `final`, so it never
reaches a page. That is different from `fuss: seed_unsorted`, which is a coin
that IS in final and DOES render, just without a Fuß.

1628 entries across 16 entities, every one `status: no_match_in_final`. The
Danish entities are clean (`danish_realm` 0 pending / 91 assignments,
`danish_norway` 0 / 45, `royal_holstein` 0 / 19); the backlog is the German
lands — herzogtum_braunschweig_lueneburg 816, `_unclassified` 219,
schauenburg_pinneberg 153, landgrafschaft_hessen_kassel 142, hanseatic_lubeck
104, gottorp_duchy 81. Curator's verdict: this is debt, and it should end as
`seed_unsorted` in final.

### Why the promotion waits

- **1553 of the 1628 carry a catalogue index.** They are mergeable under §9.4,
  not orphans. Merging them into an existing coin costs nothing; promoting them
  first and de-duplicating later costs an exclusion pass against gates that are
  built to refuse exactly that.
- **The three open items each SHRINK the number, and shrink it the right way** —
  by attaching a coin to one that already exists rather than adding a row. The
  V1 atavisms are the clearest case: a bogus index is what SPLITS a coin from
  its type. `km-358-h123` was split from Hede 74 by a `hede: 123` carried over
  from V1 that ucoin never published.
- **`bulk_promote_pending` already defaults to `no_basic_peer_only`**, so
  everything with no peer at all is promoted automatically. The 1628 are the
  residue where the matcher DID see peers and could not decide — promoting them
  wholesale means overriding that doubt by fiat.
- Only **75** of the 1628 have no catalogue index at all. Those are the safe
  slice if a small first batch is ever wanted.

### THE V1-ATAVISM TASK — start here

**Goal (curator's framing):** find catalogue indices that NO current source
attests, and drop them. They are leftovers of over-merges, splits and the V1
bootstrap; they look authoritative, they key the cross-source merger, and
nothing regenerates or removes them.

**What is already measured** (2026-08-21, upper bounds — the harmful share is
NOT yet counted):
- **216 seeds whose id does not match their own builder's convention**, ALL of
  them in `data/v2/seed/ucoin/`, all shaped like a V1 final id
  (`km-1-fr-iv-1702`, `km-x011-fr-iv-1719-half`). Every other source — bruun,
  hede, galster, numista, ngc, ikmk, kmk, numismaster — holds the convention at
  100%.
- **395 source URLs cited by ≥2 DIFFERENT seeds.** The pattern is visible by
  eye: `tid=90498 → ['sh-tid-90498', 'km-116-chr-v-1787']`, i.e. the modern
  ucoin builder AND a V1 twin on the same ucoin `tid=`.

**The worked example that proves the mechanism.**
`km-358-h123-chr-v-1681` is a SEED whose id is a V1 FINAL id, living in
`data/v2/seed/ucoin/`, whose source URL is ucoin `tid=96983` — the very record
that already produced `dk-tid-96983`. It additionally carries `hede: 123` and
`sieg: 129`, which ucoin does not publish at all (its page is «Denmark 2
skilling, 1676-1681», no catalogue numbers). Those two indices came from V1
hand-curation and are attached to the WRONG coin: Hede 123 is the Glückstadt
1681 type, while ucoin's entry is the København 1676-1681 one (Hede 74A/74B).
The result was one coin split across two finals in two entities, with
`Glückstadt` looking attested on the København coin.

**Method.** For every seed, for every catalogue index it carries, check whether
the cached record of its OWN cited source actually prints that index. An index
no source gives is an atavism: re-attach it to the coin it belongs to, or drop
it. Do this across ALL sources, not only ucoin — the ucoin V1 twins are the
visible cluster, not necessarily the whole set. Also list seeds that share one
source URL: one source record should not produce two seeds.

**Caution.** Removing an index changes merge keys, so it will move coins between
classes and possibly between entities. Snapshot with `trace_coin.py snapshot`
first, and expect `verify_reflow` to need `_recorded_removals.yml` entries for
the indices deliberately dropped (`kind: field`).

### Also still open

- **Hede 74 vs 123** — merge or keep apart. My read: two types, Krause lumped
  them under KM 358; Hede (74A/B vs 123), Sieg (7/8 vs 129) and KMM all separate
  them by mint. Needs the curator's call, and the duplicated `numista: 22576`
  should leave one of the two sides.
- **53 new Hede types** await classification; `c5h30` and `f3h25` are
  off-strikes and belong in §9.3 exclusions.
- **Four specimens detached by the 3a/3b splits** need an `issuing_entity` for
  the German states before their citations travel back to them.
- **`_catalog` ranges for the other builders** — only kmk was fixed.

---

## 2026-08-18 (night) — «I» renamed, and it did not mean what I assumed

**Commit** `716d7a9`.

The `seed_unsorted` bucket id `I` is a Roman numeral — the shape every real
Müntzfuß uses for its first phase. Harmless while a coin sits in seed_unsorted;
not harmless the moment someone gives such a coin a real fuss and leaves the
phase, because it then lands in phase I of that fuss looking entirely correct.
I9 cannot catch it (seed_unsorted is exempt, and fuss + phase I is a valid pair),
and it is undetectable after the fact — hence renaming the id rather than adding
a check.

**The correction, and it is the point of this entry.** `I` does NOT mean the same
thing on every page. I established it was the V1-bootstrap catch-all from
Denmark's title plus the id prefixes (`hb-`, `lu-`, `hs-` are LOCATIONS, not
sources, and none of those ids exists in `data/v2/seed/`), renamed all 247 coins,
and only then read `holstein_schauenburg`'s bucket titles: **«Ernst III
(1601–1622)» and «Just Herman und Otto V (1622–1640)» — curated ruler
periodisations**, with the 105 coins correctly placed, `km-135-just-herman-1624`
included. A blanket rename would have collapsed two real periods into one
meaningless bucket. Reverted and re-scoped.

**Renamed:** `denmark`, `hamburg`, `lubeck`, `lubeck_bishopric` (the four pages
whose `I` is demonstrably a bulk catch-all) + the 142 coins they carry — 80
`hb-tid` in hanseatic_hamburg, 62 `lu-tid` in hanseatic_lubeck. Titles now say
V1 bootstrap; Denmark's claimed «ucoin» for a bucket holding nothing.

**Deliberately left alone:** holstein_schauenburg's `I`/`II` (curated), and
erzbisthum_bremen_verden's single `bruun-L12177` coin — its page declares neither
id, so nothing establishes what its `I` meant. One-coin loose end.

`v1_bootstrap` is deliberately NOT in absorb's `_SEED_TAG_PHASES`: `I` was not
either, so these entries count as curated for the stale-final drop and stay
protected. Adding the new id would have silently removed that protection.

Verified: 142 changed, 0 losses, invariants clean, four test suites pass, every
rendered page count unchanged.

**The bucket-declaration decision is still the curator's and is now fully
unblocked.** Measured on current data, dated coins only (the undated guard drops
the rest): Denmark +6092 (kmk 5777, ngc 297, ikmk 18), all ten pages +7688.
Density of the Denmark intake: nominal 100 %, catalogue index 59 %, mint 47 %,
metal 16 %, weight 12 % — most rows would be very sparse. Filter tiers if wanted:
dated+catalogue +3669 Denmark / +4456 all; dated+catalogue+metal +762 / +1180;
dated+catalogue+weight +638 / +960. Note the gap is NOT only kmk/ikmk/ngc —
`schleswig_holstein`, `german_empire`, `bremen_verden` are also missing buckets
their own consumed entities use, and `german_empire` (142) and
`schleswig_holstein` (87) need the holstein_schauenburg-style `I`, which the
derived-bucket approach will NOT generate, since no seed source is named `I`.

## 2026-08-18 (evening) — the kmk seed was never stale; its default flag was wrong

**Commits** `44a2ec8`, `2aa8275`.

**My earlier report was wrong, twice.** I told the curator the committed kmk seed
had drifted from its own builder — 109 vanished, 21 new, 58 re-routed on an
unchanged cache. The seed had not drifted. I was running the builder with the
wrong flags.

**What it actually was.** `build_kmk_seed.py` fills year, mint and catalogue for
part of its corpus from the web-rådata cache, and that enrichment was OPT-IN
(`--raadata`). The committed seed was built WITH it; my re-runs were not. Since
`seed_merge.merge_one` DELIBERATELY drops an un-curated field the fresh entry no
longer carries — «stale keys go away when the parser stops emitting them» — the
default run read as the parser having stopped emitting year/mint/catalogue and
deleted them. Clean specimen: `scripts/cache/kmk/81500.json` (ES) has neither
1690 nor Lange 763; `scripts/cache/kmk/web/81500.json` has both.

**How bad it was at the end of the chain**, which is the only place it shows:
232 losses — 125 finals gone, 25 stripped of `year_first`/`year_last`/
`year_label`, 7 catalogue shrinks. And it composed badly with `4c8bb50`: a final
that loses its year is then correctly dropped by the new undated guard, so the
two changes together would have removed 25 dated coins from the pages, each step
looking harmless alone.

**The fix is the default, not the merge.** The drop-what-fresh-omits rule is what
lets a parser fix retire a stale value — changing it would be wrong. What was
wrong is that the builder's default did not reproduce the artefact that is
committed. Enrichment is now ON; `--no-raadata` opts out; `--raadata` stays as a
no-op. Six tests in `test_seed_reseed_idempotent.py`, three of them pinning
merge_one's behaviour AS DELIBERATE plus the counterweight that curated fields
and `_curation_holds` survive omission.

**The clean re-seed then landed** (`2aa8275`): byte-idempotent apart from 274
`mint_verified` flags correctly flipping true; 9 coins changed, 11 gains, 0
losses, 0 stale finals, 0 missing citations over 15049 finals, render identical
on all thirteen pages.

**The generalisable lesson, and the audit that closes it.** Any builder whose
DEFAULT flags do not reproduce how its committed seed was built will silently
delete the difference on the next re-run, and the damage only becomes visible
after merge+absorb. **All eight remaining builders were audited 2026-08-18 —
none has the kmk shape.** Each was run with defaults from a clean tree, measured
seed-keyed against HEAD, and reverted: `bruun`, `galster`, `hede`,
`numismaster`, `numista`, `ucoin` byte-identical (hede only its `generated_at`);
`ikmk` 0 losses with 35 coins correctly re-routed out of `_unclassified` by
mint-registry gains since its 2026-06-24 seed; `ngc` 0 losses of the kmk kind.
Hypotheses tested and disproven: `hede --year-from/--year-to` defaults (1514 /
1914) DO match the committed window; `ikmk --no-thin` — default thinning matches
the committed artefact (no weight-list churn); `ucoin`'s `_collect_v1_ucoin_entries`
reads `data/locations/` which no longer holds coin yamls post-V1-teardown, yet
the seed is unchanged, so nothing depended on it. `ngc --scope` / `ucoin --entity`
scoping is safe as predicted — an untouched entity file is simply not rewritten,
and 135 ucoin entries the cache no longer covers survive as `orphan_curated`.

**One unrelated finding, for the curator — NOT the flag class.** A default
`build_ngc_seed.py` run deletes one hand-curated line on `ngc-167742`
(`royal_holstein`): `year_verified: false` with the comment «ND: date_line
«(1523-33)» is an attribution window … Held from widening the merge via
`_cross_entity` year_demote». `year_verified` is not in `seed_merge.CURATED_FIELDS`
and the entry carries no `_curation_holds`, so merge_one drops it exactly as
designed. `trace_coin why` records no decision behind it. The fix is a
`_curation_holds: {year_verified: "..."}` on that entry (or adding the field to
the builder's `extra_curated`) — left untouched, curator's call.

**Still open, and now unblocked:** the curator decision on declaring
`kmk`/`ikmk`/`ngc` buckets in the `seed_unsorted` phase lists. It was gated on
this repair. Completing Denmark's three brings **6280** coins onto the page
(1826 → ~7939), almost all un-triaged KMM museum specimens; ten of eleven pages
have the same gap. The derived-bucket implementation was written and reverted —
it is reproducible in about half an hour, and can be filtered (dated only,
catalogued only, per-entity) if the raw number is too blunt.

## 2026-08-18 (later) — pre-1544 Gottorp reaches the Denmark page

**Commits** `4c8bb50`, `48b4e17`, on top of the morning's three.

The two `rhinsk_gylden_fod` coins that I9-info surfaced — Frederik I Goldgulden
1531 and Christian III Ducat 1534, both Gottorp mint — now render on Denmark.

**The history, since it decided the shape of the fix.** The Gottorf ducal line
begins 19 August 1544 (Rendsburg Landtag, Adolf I); before that Gottorf is
Frederik's seat from the 1490 partition, and after his 1523 accession he governs
from it as King of Denmark, with the ducal-zone mint moved Husum → Slesvig/
Gottorp at that same accession (Wilcke 7-2 p. 186-187, via
`sh_ducal_zone_husum_1514.md` §3). So pre-1544 Gottorp coins are older than the
duchy. From 1544 the Gottorp dukes are sovereign co-rulers; Roskilde 1658 and
Copenhagen 1660 release them from Danish feudal bonds and they become Sweden's
ally against Denmark — which is why the Denmark page takes `gottorp_duchy` with
`year_to: 1543` and not wholesale (35 coins in, 314 out).

**What was deliberately NOT done: the entity was left alone.** I started by
re-routing pre-1544 Gottorp to `royal_holstein` in the mint registry, and had to
revert the lot — `trace_coin why` shows a curator cross-entity call of
2026-07-16 that already weighed this and chose `gottorp_duchy` on the ducal
legend «FRIDERICVS D HOLSACI / MO NOV AVREA SLESVICENSIS», which outranks Bruun's
«DENMARK» heading under §5. The consume-cap gets the same visible result without
touching that call. **Run `why` before the registry, not after.**

**Three findings from the reverted attempt. Two are now closed (see the
year-aware entry below); the third is still open.**

- `build_kmk_seed.py --write` today produces 109 vanished, 21 new and 58
  re-routed seeds (Norway→Denmark at 1642-1765) with no input change — the
  committed kmk seed is stale against its own builder. Reverted, untouched.

**The open decision — the seed_unsorted bucket lists are stale on ten of eleven
pages.** `denmark` lacks `kmk`/`ikmk`/`ngc`, `lubeck` lacks four, and so on: a
coin seeded from a source the page never listed is dropped by the pre-filter.
I built a derived-bucket fix (same medicine as the absorb tag set) and reverted
it — completing Denmark's three buckets alone puts **6280** coins on the page
(1826 → ~7939), almost all of them un-triaged KMM museum specimens. That is a
curator call about what the page is for, not a mechanical repair. The undated
guard in `4c8bb50` is the part of that work that stands on its own.

**Also fixed on the way:** ~1536 undated stubs were one bucket away from
rendering as blank-year rows, and `compute_coin_year_runs` had no None guard, so
the build died with a TypeError instead. Guard now at the shared choke point;
brunswick_lueneburg 1521 → 1491, no other page moved.

## 2026-08-18 — the stranded phase, and why the validator could not see it

**Commits — everything from 2026-08-07 onward is still local;
this session adds `20ccfd1`, `012e74a`, `a6a1c3e`.

**Task A is done, and it was 108 coins, not 17.** The handoff's figure was stale.
108 finals across 7 entities and 13 fuesse carried a real Müntzfuß beside
`phase: 'ngc'` and rendered on no page at all. A further 421 sit at
`seed_unsorted/ngc`, which is the normal un-triaged state and untouched.

**The cause was a promotion that moved the fuss and not the phase.** None of the
108 had a classification decision; `trace_coin why` prints nothing for any of
them. The fuss reached them through `curator_migrations` in absorb — when the
merger re-homed a seed onto a new NGC host and the stale V1 foundation was
purged, its curator classification migrates to the host. The applier
(`absorb_seeds_into_final_v2.py` ~2450) overwrote `fuss` from the
`seed_unsorted` placeholder, but the phase-placeholder list it consulted was a
hand-written literal that nobody extended when NGC landed on 2026-08-10. The
same concept already existed as `_SEED_TAG_PHASES` a thousand lines above, also
hand-written, also missing `ngc`. **Two independently maintained literals of one
set** — that is the mechanism, not the omission. Both are now one set derived
from the directory names under `data/v2/seed/`.

**The deeper half: the validator was structurally unable to fire.**
`schema.validate_cross_refs` (~1118) does carry «a coin's phase must be declared
by its fuss». It never sees these coins. `build._assemble_v2_location`'s per-coin
pre-filter DROPS a coin whose phase its fuss does not declare (~991) *before* the
`Location` object is built, so the validator only ever validates survivors. Two
implementations of one rule, filter first — which is exactly why
`--validate-only` exited 0 on data that renders 108 coins nowhere. The rule is
now stated on the DATA as `audit_v2` **I9**, where nothing can filter it away,
with two deliberate exemptions: `seed_unsorted`, and the fusses in
`build._DERIVE_PHASE_FROM_YEAR` (imported, not copied — a duplicated literal is
the very mechanism I9 exists to catch). Ten tests in
`scripts/maintenance/test_phase_declared.py`, including a live assertion over the
repository.

**One curator call inside the repair.** `unified-ngc-1175224` (4 Schilling Johann
1618-1622, KM 13 / Lange 539, sonderburg) sits before every Sonderburg 9¼ window,
which opens 1622. Decided: phase I, `year_first` left at 1618.

**New, and NOT taken on — I9-info has two cases.** `unified-dk-bruun-14741` and
`unified-dk-bruun-14783` carry `fuss: rhinsk_gylden_fod` in `gottorp_duchy`, for
which **no consuming page declares any phase at all**. They are invisible for the
same net reason as the 108, but the repair is a location-yaml periodisation
decision — add the fuss to Gottorp's phase list, or move the coins — not a
coin's phase. Left as a curator-review surface, reported informational so it does
not block commits.

**Overlap with Follow-up E, noted and not touched.** Both defects live in the same
render path and both are «classified data that never reaches the page», but they
are opposite ends of it: I9 is a coin the pre-filter drops, Follow-up E is a coin
the seed-render pass surfaces despite an exclusion. Nothing in this session's
change touches `data/v2/exclusions/`, and the seed-render pass is still
un-consulted by the build.

## 2026-08-17 — the Danish ducat card raised, and two defects deferred

Ducat card 5.9 → raised; phases re-cut to follow the coins (`4a2c834` `ff9d217`
`280674c` `18d27c9`). Off-strike exclusions and the parser-retraction gate
(`2496f8d` `18812cf` `d392810` `7f59831`) closed. Task A (`phase: 'ngc'`) was done
2026-08-18. A deliberate asymmetry to leave alone: the ducat phases end 1802, the
timeline status layer runs to 1813 (phases follow coins, status follows law).

**Still open:**
- **Task B — richer `pdate_label`**: give minting / standard / circulation years
  separately, matching the timeline bar's three layers.
- **Follow-up E — an exclusion does not reach the render if the coin is still in
  the seed layer.** `scripts/build.py` never reads `data/v2/exclusions/`; absorb
  removes the coin from `final`, but the seed-render pass in `_assemble_v2_location`
  surfaces it again. Confirmed: `dk-numista-387448` (KM PnC20) and
  `dk-numista-387243` (KM PnD20), excluded 2026-07-12, still render. Scope NOT
  measured — grepping HTML for seed ids is the wrong instrument; reproduce the
  seed-render pass's selection. Shared render path → own session.
- **Follow-up D** — for the 32 KMM stubs with no index and ~20 with bare `schou`:
  does a Hede/KM number exist in any source we have not read, or is the ceiling a
  new harvest? Check before planning.
- **Follow-up C** — `unified-dk-hede-nf3h62` (1 Speciedaler 1667-1669, mother of the
  excluded 1668 off-strike) is still `seed_unsorted`; sibling `nf3h57` is `9_25_thaler/I`.
- `ngc-1098157` (PnA19, 10 Ducat, no year, only a Pn number) — needs its own call;
  carries a stale `fineness_verified: true` with no fineness.
- **Re-run needed**: a merge-candidate scan must not gate on nominal fraction
  («1 Kurantdukat» = «12 Mark», «1 Speciedaler» = «2 Rigsbankdaler»). The
  «119 of 125 unsorted Danish gold without candidate» count used such a filter and
  is unproven.
- Card ceiling: C1 «why» — no source gives a motive for adopting the standard.

## 2026-08-16 — the ducat gets three dossiers, and its 67 turns out to be Venetian

**Commits — everything from 2026-08-07 onward is still local.

**The question that ran the session:** where does the imperial ducat standard —
67 pieces per rough Cologne mark at 23⅔ Karat — come from? Answered as far as the
sources reach, and the answer is now in `docs/research/ducat_origins.md`.

**What was established.** The family's ancestor is the Florentine fiorino d'oro of
1252, which the Bundesbank catalogue calls «the progenitor» and from which Venice
(1284), Hungary (1325), Bohemia, Portugal (1457), Spain (1497) and the Rhenish
gulden all descend — which is why every one of them computes to ≈66 per rough
Cologne mark. The ducat's **67 is Venetian**: Bobzin has Venice cutting its ducat
from 3,54 to **3,49 g in 1526**, and 233,856 / 3,49 = 67,007. The **fineness is
Rhenish**: Jesse has the electors striking Florene «23⅔karätig» before 1365,
after which their gulden fell to 18½ by 1490. The margin sits in the fineness,
not the count. And as a **legal** figure 67 / 23⅔ begins in 1559 and not before —
Esslingen 1524 sets only the mark, Augsburg 1551 has no ducat, and the pre-1559
German ducats scatter from 65,7 to 68,5.

**Two readings were tried, demoted, and kept for the trail** (§6c Troyes-mark,
§6e mint-margin). §6e's arithmetic still holds and still excludes Rhenish gulden
as source metal; it is simply no longer needed to explain the number.

**Three dossiers now exist and cross-link:** `ducat_origins.md` (shared),
`dk_dukat_portugaloeser_fod.md` (Denmark), `de_reichsdukatenfuss.md` (the
imperial ordinance line). Each carries its own open-questions list with what
would settle each item.

**Data changes that shipped:** Grevens-Fejde re-dating (Galster 88/89/90 →
1534-1536, root-fixed in the seed builder with tests); the 1604 Klippen fraction
release; the Denmark ducat timeline given Denmark-scope events (mint 1531-1802,
status 1531-1813, circulation 1531-1873 faded from 1833); both ducat descriptions
rewritten with the Portugaløser included; six new `refs_pool` keys;
coingallery.de registered in `SOURCES.md` §6.6.

### Open, and each has a named next step

* **`fuesse.yml::reichsdukatenfuss.events` anchors are stale.** Both
  `first_adoption.anywhere` and `first_mint.anywhere` are 1513 and both notes
  cite Galster c2g-89/90 — re-dated this session to 1534-1536. The earliest
  Danish piece is Galster 46 of **1531**; the event's own scope label covers the
  Reich, where the earliest attested strike is **Hamburg 1497**. **Curator
  decision, deliberately not made:** these events drive the rendered timeline on
  every page. Full statement in `de_reichsdukatenfuss.md` §7.1.
* **Hamburg 1497's fineness is unpublished** — the single most valuable missing
  datum on the German side (`de_reichsdukatenfuss.md` §7.2).
* **The 1559 drafting record** would settle whether Ferdinand I set 67 against
  the Hungarian standard he had held since 1526 (`ducat_origins.md` §7.13).
* **Pohl, *Ungarische Goldgulden des Mittelalters (1325-1540)*** would settle the
  Hungarian specimen-level questions; **van Gelder & Hoc** the Low Countries
  census; **Jensen/Skjoldager (2021)** the authorising act for the Danish 1531.
* **Bobzin's «3,49 g» — fine or gross?** Decides whether the Reich's margin is
  1,40 % or the whole 23⅔-against-pure difference (`ducat_origins.md` §7.14).

### Two project-level lessons recorded outside the dossiers

* **`hintergrund` beats `description`** in the location template's fuss title
  block — so editing a location's `description` override changes nothing on that
  page. Now in `docs/CONVENTIONS.md`; found the hard way when a rewritten Danish
  card produced no visible change and the previous text turned out never to have
  rendered either. **Verify prose edits on the built page, not in the YAML.**
* **New skill `research-dossier`** — writes and scores `docs/research/*.md`
  against a 6-criterion rubric. Registered in `CLAUDE.md` §Skills.

---

## 2026-08-15 — the 1604 gold Klippen get their own standard, and Denmark's ducat phase splits at 1602

**Commits — `9f0b338` (dossier) + the fuss / denmark / data /
handoff commits of this session, on top of everything from 2026-08-08.

**What triggered it.** A question about the `tarif-1604` phase turned into a
placement problem: those four Klippen (3 · 4 · 6 · 8 Daler, Hede 10-13) sat under
`reichsdukatenfuss`, which the ordinance that created them rules out.

**The primary source finally arrived.** Wilcke I is online at danskmoent.dk, and
**p. 69** carries the schedule of the ordinance of 8 September 1602 under a
column headed «**Lovbestemt Værdi**». The May dossier
(`docs/research/daler_klippe_1604.md`) had asked for exactly those pages; it is
now extended with the ordinance table, the **20 November 1604 revision** (4 Daler
re-cut to 24½ per mark at 20⅓ karat, «fine Mark til 115½ Dlr», 8,087 g — our
recomputation gives 8,0871), the boundaries (February 1609 left the gold alone;
the next event is the **Guldridder 1611-13**, absent from our data), and a batch
of 552 four-daler pieces found overweight and re-melted into 588.

**What settled the placement.** Against the ordinance's own Ungersk Gylden the
Portugaløser is 9,996 ducats and the Gylden 0,999 — round numbers. The Klippen
give 2,393 / 3,586 / 4,877, no relation at all. They count in the SILVER daler:
at Wilcke's 12,80:1 the 4 Daler is 4,000 silver daler and the 6 Daler 5,995. And
they divide the FINE mark — on the rough mark the denominations give 96 / 106½ /
106 and no common footing.

**New fuss `115_5_daler_fod`** — «115½-Dalerfod», historical_name
«Gulddalerfod», `grid_unit_convention: fein`. The figure is Wilcke's own (curator
choice: name the standard as legislated). Our coins were struck to the 1602
formula and read ~2 % heavy against it — ordinary specimen deviation, visible as
Δ. Two schema notes worth remembering: `fineness_standard` carries the
ordinance's FLOOR (20 karat) because its only consumer splits «reduced» tariff
coins and none of this series is reduced against its own ordinance; the variable
karat lives in `fineness_period` as free text.

**Denmark's ducat phase I split at 1602.** It claimed «Probe bleibt durchweg
.986» while every Christian IV Ungersk Gylden from 1603 is .972 — the ordinance
set it at 23⅓ karat, four grains under imperial, same rough weight. Phase I now
ends 1601; new phase `I-1602` runs 1602-1611 (end evidenced: 1609 left the gold
alone, 1611 brings the Guldridder). The phase is deliberately NOT uniform in
fineness — the Portugaløser sits at 23½ in the same schedule, because the
ordinance sets a karat per denomination.

**Phase II carried the same false claim and needed a different fix.** The data
shows a split, not one value: Copenhagen runs .979/.980 across 227 readings while
.986 survives in 8 — all Glückstadt and Tönning, i.e. the duchies inside the
Empire. Title, description and the Danish card's Grundwerte now say that. The
GLOBAL `fuesse.yml::reichsdukatenfuss` was deliberately left alone: it describes
the imperial standard correctly, and Gottorp / Rantzau / Lübeck still hold it.

**Verification**: re-flow 6662 → 6662, 10 changed, 0 losses; 852 tests; build
clean; all three refs cited from prose (24 / 18 / 12 times).

### Closed same day
* **The three Klippen without a `fraction` were held that way on purpose.**
  `dk-tid-163409` / `dk-tid-163410` / `km-27-chr-iv-1604` each carried
  `_curation_holds: {fraction: "removed — the Daler face is NOT a clean Münzfuß
  multiple (4 Daler != 4 Dukat) … Pending curator decision"}`, added by `0f040f2`
  when the coins still sat under `reichsdukatenfuss`. The inference pass skips
  any entry holding `fraction` (`absorb_seeds_into_final_v2.py:2558`), so it
  behaved exactly as designed — there was never a control-flow defect, and the
  monotonic-guard hypothesis recorded here earlier was wrong. Under
  `115_5_daler_fod` the Daler IS the fuss unit, which is the decision the hold's
  own text was waiting for; the curator released it 2026-08-15 and absorb set
  '4' / '6' / '8'.

  The visible effect is the Δ column, not the row order: the three now compute
  against the ordinance soll at −0,04 % / −0,07 % / −0,06 % (worst alternative
  reading −1,77 %). Order was already 3 · 4 · 6 · 8 via the nominal-quantity
  fallback and did not move.

  Third time in a week that a value disagreeing with expectation turned out to
  be a curator decision rather than a defect — §0b-1 exists for exactly this, and
  `trace_coin.py why` would have answered it in one command.

### Open, deliberately
* **`implied_fuss` ignores `grid_unit_convention`** (noticed 2026-08-15 while
  clearing the holds above; NOT introduced by that change). `compute.py:1054`
  and `:1109` both compute `fuss.grid_unit_g / (metal_g / k)`, and for a gold
  fuss `metal_g` is the ROUGH weight (`:1049`). On a fuss declaring
  `grid_unit_convention: fein` that yields coins-per-ROUGH-mark while the card
  states the fine-mark figure — for `115_5_daler_fod` about 96 against a
  declared 115½. It does not surface today because the line only renders at
  |Δ| > 2 % (`:1184`) and no reading of the four Klippen reaches that. The other
  exposed fuss is `vereinsgoldmuenze`. The fix is to divide by the coin's
  fineness before the ratio when the convention is `fein`; it needs a check of
  every `fein` fuss first, since silver fusses reach the same line through
  `weight_fein_g` and are already correct.
* **3 Daler**: mint accounts say «half a 6 Daler Klippe» (6,588 g at .924), the
  unique specimen weighs 7,42 g. It is in the fuss without a `fineness`.
* **Haderslev 1591-93**: hede .986 vs three sources .972. Ernst, NNUM 1953 s. 198
  would settle it. Wilcke separately calls a later improvement of the Gylden
  toward imperial «muligt» — possibility, not fact.
* **Guldridder 1611-13 / 1627 / 1629** — missing from the data entirely.
* **Bruun's «6 Daler = 3½ Ungersk Gylden»** (1 Gylden = 1,714 Dlr) contradicts
  the ordinance's 1⅝ (1,625) by 5,5 %. Recorded in the dossier, not adjudicated.

## 2026-08-10 — Queen Sophie's 1584 gift set: split apart, and its seventh piece finally harvested

**Commits — `6b9ab63` (the split), `c6bf7c0` (the Engelot),
submodule `692f78054`. `8e0f0ad` + `36aca53` ahead of them belong to ANOTHER
session; leave them alone.

**Hede 7 and Sieg 29 are SET numbers, not type numbers.** The reign index
f2hede.htm prints ONE row — «7A-G | 29» — covering seven different
denominations. Any two of the seven can auto-glue on those false shared bases,
and blocking one pair just moves the fusion onto the next: blocking 7E-7F sent
it straight to 7F-7G. `merge_decisions/danish_realm.yml` now carries the full
21-pair clique. If an eighth record of this set ever appears, extend the clique
before flowing it, not after.

**Engelot 7D was never harvested because of its URL.** danskmoent hosts it at
the site root as `/engelot.htm`; `fetch_hede`'s cNhM / fNhM pattern never
matched, and the galster parser that caught the page by accident filed it as a
reign-overview and skipped it. `fetch_hede` now detects irregular coin links
(pure-anchor-list cell + conforming sibling + denomination-shaped anchor text —
isolates exactly this one page across all 21 overviews) but harvests only what
`IRREGULAR_COIN_PAGES` maps to an explicit Hede-shaped cache name, warning about
anything unmapped. Cached as `f2h7d.htm`, seeded as `dk-hede-f2h7d`.

**OPEN — the Engelot's Müntzfuß.** It sits in `seed_unsorted`, gold, 5.06 g, no
fineness written. Wilcke 1950 tabulates «Angel (Engelot)» under Engelsk Moent at
5.084 g rough / 5.057 g fine, which the specimen sits just under — but those
digits are OCR-degraded in the cached scan, so nothing was written on their
basis. To close it: a clean scan of that table, or Wilcke 1931 «Frederik II.s
Guldmoent 1584», Daler Mark og Kroner s. 85-90, which danskmoent cites directly
for this set. The project has no Angel/Engelot Fuss card; the sibling
English-model cards (`nobel_fod`, `rosenobel_fod`, `sovereign_fod`) are the
shape one would take.

**f2_guldkrone_fod is no longer a two-year Fuss.** The set's Guldkrone (7F, 3.38
g) went in as a new Phase II (1584) on gross weight alone per §8a step 4 — the
source publishes no fineness and none was written. Window is now 1563-1584 and
the documented-window hiatus to Christian IV reads 34 years, not 55, in all
three languages.

**Two traps that cost time here, both worth remembering.**
(a) `cmd 2>&1 | tail -2 && next` does NOT stop on failure — `tail` exits 0. A
`trace_coin snapshot` that correctly REFUSED a half-applied tree was read as
having aborted the chain, and a second merger was launched on top of the first;
two `merge_seeds_cross_source --apply` ran concurrently over the same
`seed_unified/` before being killed. Check the rc, not the pipe.
(b) A re-flow can silently drop curation. `verify_reflow` caught `f2h7g` losing
its curated nominal, its canonical .770 fineness with the §4 note, and its
`_curation_holds` — the entry had briefly been absorbed into a sibling and came
back rebuilt from the unified. Restored verbatim from HEAD. Run verify_reflow
before believing a re-flow was clean.

**Why the seed diffs look enormous for one coin.** Purely positional. The
builder is deterministic (consecutive runs differ only in `generated_at`), key
order is stable, and `royal_holstein` came out semantically identical — 0 added,
0 removed, 0 changed — while showing 568 changed lines. Same class as the
seed_unified churn in `8e0f0ad`: there, 116 of 371 gottorp classes were RENAMED
because a unified class is named after its top-authority member (§9b) and the
list is id-sorted, so each rename moves a ~40-line block. Not a formatting
regression; the line counts just overstate the semantic change by roughly ten
times.

## 2026-08-07 — the Christiania 3-Dukat re-grouping, and three heals for one accumulation defect

**Commits — `153fc9d`, `0ff9a23`, `0bb97f9`, `d157b27`,
`217895f`, `cdd1bcc`, `dacf5fc`, `aec0e73`, `04234cc` (+ submodule `1727099ba`).

### What the session was actually about
Group B of the `8_dukat` triage. It turned into a pipeline session because the
coins kept exposing mechanism.

**The Christiania 3-Dukat family had a systematic off-by-one KM-to-Hede
mapping** (`d157b27`). NumisMaster and ucoin publish a Krause number and nothing
else; the danskmoent Hede pages publish hede+schou and no Krause; every coin in
the family is «3 Dukat, Christian V, Christiania, 1673». Register intersection
empty → the matcher decided on metal+nominal+ruler+year → each KM landed one
class early. Curator read the reverse designs (lion vs elephant, rider vs bust)
and settled it: KM 124=Hede Norge 5, 125=10, 126=12, Hede 14 has no KM.

Two implementation lessons in that commit worth not re-learning:
* blocking only the OBSERVED wrong edge is useless — freed from nc5h10,
  MC_110811 auto-matched nc5h12 instead and force_union merged both classes.
  The matcher has no signal to prefer any particular wrong partner, so the
  constraint must be TOTAL (97 pairwise no_merges).
* a re-grouping that REMOVES a value needs a manual final reset: absorb unions
  catalog+sources and never subtracts.

### The recurring defect: deep-merge accumulates, the gate sees a shrink
Hit **three times in one day** — KM in the finals, the sibling-Schou heal, the
off-strike-aside heal. Each time a correct, verified cleanup was blocked by
`verify_reflow` with no way to tell it from real loss, and the only exit was
`--no-verify`.

Resolved structurally in `04234cc`: `heal_hede_retracted_refs.py` writes
`data/v2/_retracted_refs.yml`; `verify_reflow` reads it exactly as it already
reads `exclusions/`. **If you fix a parser and the seeds do not change, this is
why** — `catalog` is in DEEP_MERGE_FIELDS and list-capable, so a re-seed unions.
A heal is mandatory, and the ledger is what keeps the gate honest afterwards.

### Open, with the evidence already gathered
* **`c5h39` / `c5h40` — CLOSED 2026-08-08. Not a defect. Do not «fix» it.**
  This entry was on the open list twice with two different wrong diagnoses,
  both of mine, both from comparing the seed against danskmoent and the parser
  cache without reading the `_source_errata` sitting ten lines below in the very
  same seed entry.

  What is actually going on: danskmoent prints «1 Dukat = Hede 40 / 2 Dukat =
  Hede 39». Bruun's physical specimens print the opposite — lot 13186 (NGC
  MS-63, 3.45 g) reads «Fr-161; KM-A433; Hede-39; Sieg-106; Schou-4», lot 17098
  (MS-62, 6.94 g) gives Hede 40 / Sieg 107 / Schou 3. The curator called it for
  Bruun on 2026-07-16, and that call is implemented in two places:
  `_KNOWN_HEDE_TYPOS` in `parse_hede.py` swaps the tags, and each seed entry
  carries two `_source_errata` (sieg, schou) quoting the lot.

  So «Schou 4», the value earlier notes called a phantom appearing nowhere on
  the page, is Bruun's own reading of the coin in hand. The Sieg values look
  crossed against the cache precisely because danskmoent's per-block refs follow
  danskmoent's inverted denominations, which the erratum supersedes.

  **A guard now exists so this class of mistake is one command away from being
  caught:** `trace_coin.py why <seed-id> [--field N]` prints every curator layer
  touching a coin — errata, holds, the parser's page-keyed override tables,
  exclusions / merge / classification decisions, the retraction ledger, and the
  page's own verbatim text. CLAUDE.md §0b-1 makes it mandatory before calling
  any value wrong; PB-13 is the procedure. Prose alone was not going to fix
  this — §0b already said «verify from the real data» and the mistake happened
  twice anyway, because the source and the cache were BOTH read and the layer
  between them was the answer.

  Two attempts to «repair» this working construction were made and reverted;
  don't repeat them. Teaching DIRECT_HEDE_HEADER_RE to accept a header whose
  Hede number is followed by refs is INERT — a full re-parse changed no key.
  Emptying `_INVERTED_TAG_PAGES` is strictly WORSE: it lets danskmoent's
  nominal and refs re-attach after the swap, so the 2-Dukat takes the 1-Dukat's
  Schou 3 / Sieg 107. That suppression is part of the fix, not a leftover, and
  its «needs a proper fix» comment is stale.
* **Galster scope, re-measured.** A parallel agent reported «716 of 842 seeds
  never overlap»; that counted seeds LACKING the field and missed the
  ruler-derived fallback. Real figures: 798 scoped, 44 bare, of which 14 Galster
  values sit in both buckets. Causes are source-side ruler spellings
  (natmus.dk's own `authority`: «Cristian 3», «Chrsitian 2», «Chrsitan 2» —
  fixed by an explicit alias table, NOT by editing the stored value, which
  would be a §CN erratum), plus ordinal-less «Christian»/«Frederik» and 36
  non-regnal authorities (Rigsrådet, Interregnum, Søren Nordby, the Norwegian
  archbishops) whose Galster volume is historical knowledge — a curator call
  (§8a), left bare on purpose.
* **§9.4 surface measured** with `MERGE_EVIDENCE_GATE=r1`: 227 confident
  verdicts demoted, 221 merges that would not happen, concentrated in
  danish_realm (182). That is the review queue, NOT the error count — many are
  legitimate (the whole nc5h* family needed 143 forced merges for exactly this
  reason). **Re-measured after the parser work: 227 again, Δ 0**, and a
  before/after of the plain run shows the parser fixes changed NOT ONE merge
  verdict (unified, confident and lowconf all identical). I had predicted the
  number would RISE because false Schou edges were masking real disjointness;
  that was wrong. The borrowed Schou numbers were wrong DATA and a latent
  hazard, but they were never load-bearing for a merge — the classes were held
  apart by the Hede conflict regardless. Worth remembering before framing the
  next «false unifying edge» as active damage: measure whether it fired.
* **Triage** `8_dukat`: A closed, B down to B3 Portugaløser (3 + a separate
  `3_portugaloser` category of 5 — one family, review together) and B5 (1, no
  nominal). Then C (10), D1 (13), D2 (19), E (3).
* **Deferred on dead resources**: `denmark-numismaster-110817` (KM A140, sole
  source, numismaster.com answers 000), A3's `denmark-numismaster-65781` and
  `kmk-439652` (no images). The tracker `output/scratch/dukat_triage_progress.md`
  (gitignored) carries the per-coin analysis.
* **Also noted, not chased**: `kmk-83604` was an authority-only stub excluded in
  July that had since been absorbed into a documented 6-source class on no
  catalogue edge at all — the §9.4 over-merge signature. The dead exclusion was
  removed; whether that absorption is legitimate is untouched.

## 2026-08-01 — three catalogue-index losses in the Bruun chain, and what they hid

**Four commits (10 ahead overall): `138c8ca` code, `bdba13c`
seeds, `dfb6145` the Pn change + the Rigsbanktegn fold, plus two submodule
commits (`7bbe58fc8`, `fe61eee4c`).

Started from a curator question — Bruun lot 1070 prints `KM-PnA16` and our seed
had no km at all. Three independent losses on the path from PDF to seed:

1. The KM ref regex allowed ONE prefix letter, so the two-letter Krause
   registers (`Tn` tokens, `PM` plate money) were dropped — 15 lots.
2. The Pn regex demanded a digit straight after «Pn», so the series-letter forms
   (`PnA16`, `PnH16`, `PnJ16`, `PnG16`, …) matched neither pattern. That marker
   is the §9 item-5 gate for the off-nominal test.
3. **`catalog.others` was existing-wins on merge**, so neither parser fix could
   land. This was the one that mattered: teaching the parser a new catalogue is
   useless if the merge drops the addition on every regen. It was also
   swallowing a Hauberg ref in galster, unrelated to Pn.

**What that uncovered.** Six Rigsbanktegn 1813-1815 had been rendering as TWO
coins each for as long as the data has existed — the Bruun half holding Hede /
Sieg / Schou, the commercial half holding the Krause `Tn` number and every
weight. Complementary registers, and no audit could see it because they were
formally distinct classes. `Tn` was the only shared key, and the regex ate it.
Folded (pairs recorded in `dedup_final_foundations.py`), keeping the
Bruun-anchored entry — right on `nominal` and on `kind` (§6: a copper token is
scheide, the other half said kurant).

Separately, `PATTERN_RE` carried `Pn\d+`, which CLAUDE.md §9 item 1 explicitly
forbids as a skip criterion. Five full-weight gold coins were suppressed by it
and nothing else — four Portugaløser/halves 1653-1655 and a 10 Ducats 1699. They
are now in seed_unsorted. **Consequence for the 8_dukat triage: that set is
built from what reaches the seed, so it was incomplete — group B in particular
should grow when the set is regenerated.**

**OPEN — spawned as `task_28d22baa`.** The re-merge expelled 15 KMM specimens
from those classes into singletons. They differ from the retained KMM records
only in having no `metal` value — missing data, which under §4 must not disprove
a merge. Nothing ships worse (their museum URLs were already on the finals and
stayed; the field-by-field final diff against HEAD shows 7 entries changed, 6
duplicates gone, 0 new, zero URLs lost), but the matcher's membership graph is
wrong and needs the systemic fix.

## 2026-07-31 — A3 dukats: one closed, three blocked on the curator

**Two commits: `a18432d` (main) + `285c481f1` (submodule).

**A3 of the `8_dukat` triage** (`output/scratch/dukat_triage_progress.md`,
gitignored — the full per-record analysis lives there, don't re-derive it).
The plan said "one absorb, mechanical". None of the four was mechanical.

  * **`dk-bruun-7396` — CLOSED**, excluded as a Guldafslag (§9.3). Bruun lot
    1133: "a gold planchet struck to a Double Ducat weight standard with the
    dies customarily used for a 16 Skilling", Fr/KM-Unlisted; danskmoent f4h47
    Zincksamlingen lists it as "1713, Guldafslag, Schou 1a". Silver mother
    `hede-47-fr-iv-1713` kept.
  * **`denmark-numismaster-65781` (KM 387) — DEFERRED**, no image obtainable.
    numismaster.com/MC_65781 does not load and ucoin tid=97535 carries no
    photos. Two over-merges sit in that node, in opposite directions; the
    analysis is complete and one photo of KM 387 settles it.
  * **`kmk-439652` — DEFERRED**, no image obtainable.
    samlinger.natmus.dk/KMM/object/439652 currently serves no images (the
    record lists three .tif assets but the page won't show them). Its
    typeNumber contradicts the object; resolving it needs a `_source_errata`,
    which needs more than a motif string.
  * **`dk-hede-f5h9` — CLOSED** (`6a5aa40`). Curator confirmed visually that
    Hede 9 = KM 564; 3 of the 12 `no_merges` in the 1747 cluster were revoked
    and the four seeds merged. The class now carries both indexing traditions
    (km 564 / fr 266 alongside hede 9 / schou 10 / sieg 30), four weight and
    fineness readings, and a verified Kopenhagen mint the KM sources lacked.
    Left seed_unsorted for reichsdukatenfuss/III. The other nine no_merges
    stand, with a comment marking the revocation so a later pass does not
    restore them for symmetry.

**The mechanism worth remembering — a parser filter does NOT remove a coin.**
I added `(?:gold|silver) planchet` to `02_parse_lots.py::PATTERN_RE` and
re-ran the whole pipeline: **zero changes**. The builder stops emitting the
lot, but `merge_seed` keeps entries the parser no longer produces
(`orphan_curated`) precisely so data is never silently lost — the seed entry
just migrates to the file's orphan tail. What actually drops a coin from the
render is `data/v2/exclusions/<entity>.yml`. Both are wanted: the filter stops
a re-harvest re-introducing it, the exclusion removes it. `dk-bruun-7235`
(the medal excluded 2026-07-27) is the same shape and was already handled this
way.

**Process failure to not repeat: check `no_merges` BEFORE presenting a merge
table.** I ran `merge-candidate-table` on all four records, showed the curator
a clean verdict for `dk-hede-f5h9`, got approval, wrote the `merges` entry —
and the merger refused it against nine standing `no_merges` from `de3b86d`
(2026-05-31). The approval was given without that fact on the table, so it was
void; the entry was reverted. The candidate-scan step must query `no_merges`
for every proposed pair.

**Three of the twelve `no_merges` in that cluster were revoked** — the curator
looked at the images and confirmed. Nine were correct and stay. The evidence
that carried it is a two-system type match, not the elimination argument first
offered. danskmoent (Hede) and NumisMaster (Krause) described these coins
independently, and the three pairs line up on BOTH sides of each coin with no
cross-matching: Hede 9 "portraet" (bust) / "vaabenskjold" vs KM 564 "Bust
right" / "Crowned oval arms"; Hede 11AB "portraet, HEL FIGUR" / "vaabenskjold"
vs KM 565 "robed King STANDING" / "Crowned draped oval arms"; Hede 13 "portraet,
HEL FIGUR" / "Christiansborg fort" vs KM 566 "robed King STANDING" / "Fortress
of Christiansborg". Hede 9 is the only one with a bust; Hede 13 the only one
with the fortress. One node is nailed by a source rather than inferred —
Numista N#147904 (KM 566) cites "Hede 13" in its own references.

The `de3b86d` verdict quoted in the file is only "KM 564 i Hede 11AB tse rizni
monety". Its own comment lists "(4) Hede 9 / Sieg 30" with no KM at all — the
question "which KM does Hede 9 carry" was never asked. The same comment claims
"Hede 11AB … Fr 266", but Fr 266 sits on KM 564 (N#342563) while f5h11ab has
Fr 271 (N#322683) — that half of the comment is wrong.

**Also surfaced, unrelated to A3 but in the same node**: `km-455-chr-v-1699` is
a second final carrying Hede 57 / Schou 27 / Sieg 115 with an empty
`composed_of` — two classes on one Hede type.

## 2026-07-30 — the last two cross-entity tails closed + trace_coin hardened

**Four commits (25 ahead of origin overall): `64aeece` five
cross-entity decisions, `0e0ab79` Rendsburg research note, `3f19069` merge +
absorb, `0b4259b` trace_coin.py adoption/reclassification split + `check-phases`.

**Both tails the previous entry left open are CLOSED.**

  • **⅕ Rigsbankskilling 1842, Altona** — was FOUR classes (KM 723, KM 724, a
    lone ucoin KM 724 stranded in danish_realm, and the Hede record alone) → one
    class of 7 sources carrying both Krause numbers. Key is Hede 13, whose index
    entry describes exactly this pair: 13A (Sieg 1) Rigsbankskilling, 13B (Sieg
    2) R.B.S. The letters differ by REVERSE LEGEND, which Numista confirms
    independently (N#19000 spells it out, N#41421 abbreviates). Copper, 1.462 g
    on both. The earlier reading that took the stub's «FF / K» for a mint split
    does NOT survive checking — both Krause numbers read Altona and FF / K are
    mintmaster marks. Recorded in the decision so it is not re-derived.
  • **Rendsburg 1716-1720, Frederik IV** — four coins (12 Skilling KM 6, 1
    Skilling KM 5, 1 Dukat KM 8, ½ Dukat KM 7), each split because NumisMaster
    files them under the Krause SECTION HEADING «HOLSTEIN-GOTTORP-RENDSBORG» and
    the builder read that country field as an issuer. All four have `ruler: None`
    — it was never a statement about the issuer. `royal_holstein` is correct, and
    `docs/research/mint_year_transitions.md` now says why instead of asking:
    danskmoent files them in the Frederik IV volume (Hede 60-63, mintmaster
    Bastian Hille at Rendsborg); the 12-skilling pieces were cut to 10 skilling
    by the Danish ordinance of 15 July 1726, a royal act over royal money; and
    Rendsburg was the crown's second-largest fortress, while Denmark had stripped
    Gottorp of its Schleswig share in 1713. No year-override for Rendsburg.
    `gottorp_duchy`'s pending list shrinks by exactly these four.

136 forced merges (was 131). Verified seed-keyed with `trace_coin.py diff`: zero
seeds vanished, zero finals lost, zero source drops. Seven phase changes, all
I → II and all corrections — six are the ⅕ Rigsbankskilling records joining the
Hede 13 class (Phase I of 18_5_thaler runs to 31 Dec 1841, Phase II opens with
the ordinance of 18 Dec 1841, so the three classes carrying I had it wrong).

**trace_coin.py — two corrections from real use, both worth knowing.**
  1. A seed has no classification of its own; it reads its final's fuss/phase.
     So «this seed's fuss changed» meant two things in one bucket. Now split by
     whether the final id stayed: RECLASSIFIED IN PLACE (same final, own value
     changed — still a loss, still exits 1) vs ADOPTED THE HOST CLASS (moved to
     a different final and took its value — merge mechanics, reported for review,
     not counted as a loss). Also fixed a real defect found while editing: fuss
     and phase were compared on separate if/elif branches, so a phase-only change
     could be missed entirely.
  2. New `check-phases` mode, in the curator's framing: coins and ordinances
     dictate the years of a phase, not the reverse. It never suggests trimming a
     coin's years (§4) — it reports PERIODISATION MAY NEED WIDENING and PHASE
     ASSIGNMENT IN QUESTION, and always exits 0. Its first cut produced 648
     findings against 22 real ones because it judged every coin against every
     location defining the fuss; scoping to pages whose `consumes_entities`
     actually cover the coin brings it to 20 + 18. Same class of error as keying
     a diff on unstable ids: comparing against the wrong reference and believing
     the number.

**OPEN — next session:**
  • `check-phases` has 20 + 18 unreviewed findings. They are questions for the
    curator, not defects — work through them with the widening/assignment split
    in mind.
  • `km-735-2-chr-viii-1847` (1842-1848) and `km-721-3-chr-viii-1842`
    (1841-1842) now sit in 18_5_thaler **II** in `royal_holstein`. II follows
    the same 18 Dec 1841 reasoning as the ⅕ Rigsbankskilling above, but
    km-721-3's `year_first` is 1841 — inside Phase I by §8.2's first-year rule.
    Still a curator call.
  • Bruun builder defaults `kind: kurant` — it stamps kurant on a .250-fine
    4-Skilling Scheidemünze. Harmless post-merge (foundation wins) but wrong at
    the seed layer.
  • Next triage group is **A3** of `output/scratch/dukat_triage_progress.md`
    (gitignored): late era 1687-1747, four records — `numismaster-65781`,
    `kmk-439652`, `bruun-7396`, `hede-f5h9`.

## 2026-07-27 — A1 Christiania dukats closed + D48 (`merges` names the whole class)

**Four commits: `8f1e1b7` (approved merges + orphan heal),
`2281ba0` (merge applied, zero member losses), `40fc74c` (D48 rule),
`8a1b0d7` (promotion).

**A1 group is DONE** — 8 promoted to `reichsdukatenfuss`/II, 1 dropped
(`7235`, medal). The last two arrived merged, not raw: `unified-dk-hede-nc5h6`
(½ Dukat, Hede Norge 6 + Schou 40) and `unified-dk-hede-nc5h7` (1 Dukat,
Hede Norge 7 + Schou 34).

**D48 — the rule worth remembering.** A `merges` entry must name the WHOLE
intended class, never the minimal pair. `force_union`
(`merge_seeds_cross_source.py` ~line 2369) clears AUTO no_merges only between
the classes it EXPLICITLY joins; a transitively auto-joined member gets no such
clearance. So `[dk-hede-nc5h6, dk-bruun-10509]` EXPELLED `dk-tid-145745` from
the very group it was meant to enrich. Naming all four fixed it in one pass —
no code change, no matcher gate. Encoded in the `v2-merge-coins` skill (Step 2
+ Hard rules) so it is read at authoring time.

**Mirror half**: for the inverse (a zero-overlap record ATTRACTED into the
wrong class) the surface is `no_merges`. Used here to keep the km-118 records
with Hede 3 and to protect the 2026-07-25 KM 119 split from `dk-hede-nc5h8`.
Once both fronts were closed, `nc5h8` auto-joined its real partner
`dk-bruun-10498` unaided on `hede 8` + `schou 15`, and now carries the correct
**km 120** instead of 119 — a neighbouring type fixed as a side effect.

**The seven Hede Norge seeds of `6db6856` are now merged** — the deliberate
`seed/` vs `seed_unified/` divergence noted in `8f1e1b7` is RESOLVED, do not
act on that warning any more. Landing state: nc5h1 → km 111/hede 1;
nc5h2 → km 112/hede 2; nc5h6 → km 103; nc5h7 → hede 7 (no KM published);
nc5h8 → km 120; nc5h64 single; nc5h66 absorbed into
`unified-dk-numista-101800` (4 Mark Kongsberg, which already carried hede 66 +
schou 6). Verified: 0 of 2169 prior classes split or lost a member.

**Attribution caveat to carry forward (nc5h7).** The DANISH Hede 7
(`danskmoent.dk/chr/c5h7.htm`) is also a 1 Dukat u.år of Christian V with
metrics identical to the digit — 3,490 g / 0,979 / 3,418 g. Weight and fineness
CANNOT discriminate; only mint (Christiania vs København) and Schou (34 vs 23)
do, and Numista publishes no Schou. Anyone re-reading that entry must not
mistake the metric agreement for evidence.

**Still open**: `task_0d84767d` (require a shared catalogue register in the
matcher). D48 removes the day-to-day blockage but not the cause —
`00318b8` measured 14116 of 134306 confident verdicts (10.5 %) resting on an
empty register intersection, and its `r1c+r2n` gate still costs 429 collateral
member-losses on `danish_realm`, so it is not shippable yet.

**Pre-existing noise to expect in absorb runs on this entity**: 27
stale-foundation purges + 27 monotonic-guard re-promotions are a backlog from
the parallel re-seed commits, NOT from your change. Control-run against HEAD's
`seed_unified` before attributing them to yourself.

## 2026-07-25 — Hede: Danish vs Norwegian series (matcher gate + «Hede Norge» label)

**Three commits: `cf86573` (matcher series gate + 7 tests),
`9890dd6` (parser cf-guard + 8 tests + cache re-parse), plus the render commit.

**The finding.** Hede numbers the Danish and Norwegian volumes as two
INDEPENDENT series (Hede 39 = 2 Dukat gold; Hede Norge 39 = 1 Speciedaler
silver). `_catalog_refs` scopes the Hede key by RULER, which both share, so
«hede/frederik iii = 39» collides by construction — 76 such pairs across the
seeds. Per-entity processing normally keeps them apart; the cross-entity pull
in `_cross_entity.yml` is the hole (it puts `dk-hede-f3h39` into the Norwegian
run). That pair was saved only by metal + nominal, not by the index.

**Measured before choosing** (sandbox outside the repo, no-op control = 0 diff):
- Adding the country to the KEY — REJECTED. 1614 of 1873 Hede records in
  `danish_norway` cite a BARE number (Bruun / KMK / Numista / IKMK publish no
  volume); 435 currently-merged pairs have the volume on one side only. Any
  rule demanding it on both detaches those from their only Hede attestation.
- VETO when both sides know their series — ADOPTED. Full merger re-run:
  9651 pairs before and after, **0 broken, 0 new**.

**Series is derived from `hede_volume`, never from the entity.** A Norwegian
coin can carry a Danish Hede number: Bruun lot 17085 prints a Christiania
2 Ducat as «Hede-39 (Denmark)», and `dk-hede-f5h36a/b/c` (Kongsberg, Danish
volume `f5h`) live in `danish_norway`. Entity-derived would mislabel both.

**Render.** Denmark's page consumes all three Danish-realm entities, so the
series meet in one catalogue column. Norwegian indices now render «Hede Norge#»
in two tiers: ATTESTED (189 tokens, `hede_volume` present) and INFERRED
(117 tokens, volume-less citation → series read off `issuing_entity`, tooltip
says so). Tooltips are i18n keys resolved in the template — `compute_location`
runs once per location for three languages.

**The inferred tier was then VERIFIED (curator asked, 2026-07-26).** Each of the
411 volume-less records was tested by looking its number up in BOTH the Danish
and the Norwegian volume of the same ruler and comparing nominal + metal + mint:

    114  Norwegian series confirmed (page match)
    122  no page data, but mint is Christiania / Kongsberg
    172  undecidable (no page data, mint not decisive)
      1  ambiguous
      0  DANISH series  ← no counter-example

A first pass WITHOUT mint reported «6 Danish», and every one dissolved: Bruun
prints them under a NORWAY header with a bare «Hede-35 / 56 / 8 / 60» (its
convention: silence = series matches the lot country), the Norwegian pages for
those numbers are absent from the harvest entirely, and the Danish «match» was
a nominal+metal coincidence with a different mint (c5h8 = 2 Dukat Kopenhagen vs
Bruun-10498 = 2 Ducat Christiania). Do not re-chase those six. Note also that
`startswith('dk-hede-nc5h8')` matches `nc5h80/81` — that false-positive cost a
detour; anchor the suffix when probing seed ids.

So the label is right wherever the data can adjudicate. The residual 172 rest on
`issuing_entity` alone — which is exactly what their tooltip says.

**This raises Finding B's priority, and the missing pages DO NOT EXIST.**
Verified twice over, so don't re-harvest hoping for more: of the Norwegian
numbers listed in an overview but absent from our cache, **0 of 53 are linked**
in the overview markup (all plain text), and a live sample returns 404
(`nf3h1`, `nf3h5`, `nc5h3`, `nc5h8`, `nc4h6`, `nf4h12`) against 200 for the
controls `nc5h6` / `nf3h30`. Split: `nf3h` 27, `nc5h` 19, `nc4h` 4, `nf4h` 2,
`nf6h` 1.

The overview ROW is their only carrier — and it is complete: nominal, material,
year and mint are populated on all 53 (notes on 44). Minus three `Afslag` /
`guldafslag` rows excluded per §9 item 3 (`nf3h1`, `nc5h9`, `nc5h22`), that is
**50 coins reachable no other way**. Guards the ingest still needs: the §9.3
exclusion above, and never materialising a «Som N…» note as a value (19 rows
carry one).

**Adjacent-session audit** (asked for explicitly). `b8aab75`'s Norwegian-infix
fix is sound and needs no revert; its tests still pass. Two follow-ups:
- FIXED here: the refs regex harvested cf-class cross-references onto the
  citing page («samme stempler som Hede 104», «Bagsiden minder om Danmark Hede
  82»). 9 pages lose a foreign number; seeds were already immune (the builder
  picks the page-canonical number), so this is defence in depth.
- DIAGNOSED, not fixed — STALE SEED ORPHANS, not a live parser defect. (An
  earlier reading in this file claimed `unknown_324` was unique data needing
  relabelling. That was WRONG — it was inferred from the overview row without
  checking whether the correctly-labelled entry already existed. It does.)

  The current parser is CLEAN: `scripts/cache/hede/nf3h2.json` has
  `specs.by_hede = {2, 3}` and `nf5h3.json` has `{3A, 3B}` — `b8aab75` already
  fixed this, and the pages label every block explicitly in print. A
  FROM-SCRATCH seed build produces **zero** `unknown_` ids and yields
  `dk-hede-nf3h3`, `dk-hede-nf5h3a/3b` properly.

  The seed entries survive only because the curation-preserving merge never
  DELETES an entry the parser stopped producing. They duplicate the correct
  ones field-for-field:
  * `nf3hunknown_324` ≡ `nf3h3` (2 Dukat, gold, 6.981 g, 0.979)
  * `nf5hunknown_387` ≡ `nf5h3b` (2 Skilling, billon, 1.151 g, 0.250)

  **A full orphan audit (live seed ids minus from-scratch ids) found exactly
  three, all `fuss: seed_unsorted`, none curated, so deleting loses nothing:**
  1. `dk-hede-nf3hunknown_324` — already merged into `unified-dk-hede-nf3h3`,
     so it only pollutes the rendered index: «Hede Norge# 3, unknown_324».
  2. `dk-hede-nf5hunknown_387` — did NOT merge; it stands as its own unified
     AND final entry, i.e. a **duplicate coin row** on the rendered page.
  3. `dk-hede-c8h11a` (royal_holstein) — superseded by the `c8h11aa`/`c8h11ab`
     split; merged into `unified-dk-hede-c8h11a` alongside its own children.

  Remedy: drop the three seed entries, re-run merger + absorb. Awaiting curator
  go-ahead (it removes a rendered row). The general lesson is worth keeping:
  **a parser fix leaves orphan seed entries behind**, so the live-vs-scratch id
  diff is worth running after any parser change.
- FIXED here (`a8f5a2a`): the 5 `royal_holstein` `mint_verified` false→true
  flips were NOT an unregenerated change — they were a live bug. The
  sources-imply-mint rule is written TWICE in `v2_seed_writer.py` (in-memory
  write path + on-disk normalisation pass) and `d934e4e` added the list-form
  exclusion to the first copy only. So `mint: [Altona, Kopenhagen]` entries got
  auto-promoted to verified on any regen — value unchanged, only the CLAIM
  (§4), and the regen was non-idempotent, meaning any unrelated builder run
  silently restated five curator flags. Post-fix a full Hede regen is
  byte-identical across all three entity files.

## 2026-07-22 — §DB first recovery pass: KMK web-rådata catalogue harvest (dukat group)

**The web page is server-rendered — bare `curl` works** (earlier
«JS-SPA, needs Apify» assumption was wrong). Catalogue sits in
`<div id="description">` on `samlinger.natmus.dk/KMM/object/<id>`, e.g.
`to mark  |  Bech nr. 876; B 783.a; Sch 3a`.

**Shipped**: `scripts/fetch_kmk_web.py` — Phase-1 fetch
(→ `scripts/cache/kmk/web/<id>.html`, skip-if-cached, polite) + shared
`extract_description()` parser. First reusable step of the §DB migration.

**First recovery pass (68 dukat-group KMK coins)**: 25 gained a catalogue
index, 43 are genuinely nominal-only stubs (web has no catalogue either).
Mapping applied: `Sch N`→`schou`; `Bech#`/`B#`/`LEB#`/`Schubart#`/`Auk.Kat.#`
→ `others[]` verbatim (NOT mapped to named fields — still need a source check
per §0). Written into BOTH kmk seed AND finals (union, ruamel_seed round-trip,
pure +104-line catalog-only diff, no churn). Web pages committed to the
submodule as provenance (`7c649b3`).

**§DB step 2 shipped same day (commits `5fee913` + `0c80d46`)**: the object
page embeds the FULL rådata JSON (`beskrivelser`/`maalinger`/`haendelser`/
`materialer`) — `fetch_kmk_web.parse_raadata()` extracts it, and
`build_kmk_seed.py --raadata` natively fills ES gaps (weight ← maalinger,
year ← haendelser, mint ← lokalitet «Nation - City», catalogue ← beskrivelser
UNIONed with typeNumber). Full re-seed + merger + absorb applied for 5
entities. Side-effects verified clean: (a) 15 coins RELOCATED by the mint
registry (13 × Wolfenbüttel-1627 → braunschweig, Reinfeld → sonderburg,
86269 → danish_norway) — moves, not losses; (b) −14/+2 §9a thinning
rep-swaps, no unique catalogue ref lost (galster 36/42 buckets checked);
(c) sovereign_fod curation intact. **The 3 relocated Wolfenbüttel gold
dukats (unified-kmk-290901 [+47350], 290902, 290909) sit in braunschweig
classification_decisions `pending:` awaiting curator review** (no
bulk_promote there — correct no-promotion-without-curator discipline).
NOTE: they left the Denmark gold-triage table scope (danish entities only).

**§DB Phase 1+2 COMPLETE (2026-07-22 session 2, commits `d3bc950` `6eeaf28`
`e157d43`)**: bulk-fetched rådata JSON sidecars for ALL 13,991 seed objects
(variant «б», 0 errors, 56 MB submodule) + full-corpus re-seed `--raadata` +
merger + absorb for all 11 kmk entities. Gains: seed catalog +386/+234-upgraded
(incl. `klassifikationer` Typenummer → canonical hede/galster/schou — a
bonus discovery), mint +329, year +49, weight +44; finals +214 with catalogue.
Guard-surfaced fixes en route: kmk-160386 (raadata «H. 16B») accreted into the
existing f7h16 cross-entity group; unified-dk-bruun-8034 metal billon→copper
(Bruun «red copper surfaces» + KMM `kobber` — old billon was a wrong verified
inference); 3 stale 2026-06-08 no_merges guards removed (Wolfenbüttel
relocation encodes the split structurally). **Still open in §DB**: only scope
re-discovery (enumerate KMM ids beyond the 43k cache via the SPA search
backend; small marginal gain — deprioritised).
**User question pending**: what are `B` / `Bech` / `LEB` catalogues?
(identify → promote `others[]` labels to schema fields). Also minor: stale
sovereign assignments in danish_realm classification_decisions reference old
merge-head ids (426815/137087/426842/137089 → now unified-dk-hede-c4h20/c4h22)
— harmless («unmatched: 4» in absorb), could be cleaned to old-head-free form.

**43 nominal-only stubs** (no catalogue on web, most no year/weight) remain in
the dukat group's `seed_unsorted`: the `kmk-783xx`/`kmk-277197..200`/etc.
cluster. Those that ALSO lack a year are exclusion (undocumented_stub)
candidates — a separate curator call, not done in this pass.

## 2026-07-14 — galster Gej fix · Norway harvest-gap audit · rhinsk phase renumber · c3h14 Goldgulden split · c3g131 schou 1-7 · c3h14 nominal → Goldgulden

Shipped and closed (details in the commit bodies and `docs/SOURCES.md §13.11`):
absorb year-hold fix on the pure-absorbed fast path (`e5d18a2`), galster re-flow
(`9a9b8c6`), `generated_at` churn fix (`80b671d`) + serialization fixed point
(`b46deed`), Christian III Goldgulden split into two coins (`82e2d5e`, `990f750`),
c3g131 Schou 1-7 (`ee7d177`), galster canonical-index-paren parser fix (`d3cb920`
`8d77786`, 34 pages recovered, 0 regressions), «Gej» guard (`ffa32bf`),
rhinsk_gylden_fod phases renumbered I/II/III (`4afaafd`).

**Still open:**
- **Galster multi-variant Schou UNION** (f1g66 / f1g73 / f1g63) — Schou split
  across per-variant parens; the parser keeps only the summary / first paren, never
  the union. See `docs/SOURCES.md §13.11`.
- Per-source SEED builders (`v2_seed_writer`, `build_ucoin_seed`, …) still stamp a
  UTC timestamp on every re-seed — a smaller churn source, left untouched.
- **🔵 Norway Numista pre-1513 harvest gap.** Every Numista Norway harvest used the
  1514 floor: 105 NIDs `oos_excluded` in NO p2, all uncached, listing page 1 never
  audited for Norway. Denmark got a `p0_pre_lovkompleks` bucket (20 NIDs, closed);
  Norway none. N#444264 (Hans Bergen Goldgulden) was added post-snapshot, so the
  body still grows. **Offered, awaiting curator go-ahead:** a
  `norway/p0_pre_lovkompleks` bucket — listing page 1 (public page, no API budget)
  + the 1481-1513 subset of the 105.

## 2026-07-13 — gold seed_unsorted triage (Portugaløser + tarif-Daler)

**Task shape.** Working through the ~212 gold `fuss: seed_unsorted` coins
(danish_realm / danish_norway / royal_holstein, metal != silver), group by group,
classifying / merging / excluding each. Curator-driven, case-by-case.

**⚠ Scratchpad loss.** The session working file
`…/scratchpad/seed_unsorted_gold.md` (the 212-coin list with per-coin resolution
map) was cleaned mid-session — scratchpad is session-scoped, do NOT rely on it.
Regenerate if continuing: filter seed_unified for `fuss == seed_unsorted` +
`metal != silver` across the three danish entities, group by nominal family.
Resolved work is safely in git; open items are captured below.

**Group progress (11 groups):**
- ✅ `1_rosenobel` (2/2 excluded) · `2_nobel` (2/2 merged) · `3_portugaloser`
  (19/22 done, 3 deferred) · `5_gold_daler_tarif` (5/5: 4 merged + 1 excluded) ·
  `0_offstrike_EXCLUDE` (8 excluded — 5 gold + 3 copper/tin/unspec off-strikes)
- ⬜ PENDING: `4_kurantdukat` (22) · `6_guldkrone` (7)
  · `7_goldgulden_gylden` (12) · `8_dukat` (73) · `9_dor_pistolen` (11) ·
  `Z_other_review` (51)

**OPEN items awaiting the curator (all need a verdict — do NOT auto-resolve):**
- **`kmk-136897`** (3_portugaloser Case 5) — KMM «½ portugaløser» but own tag
  «Sch 2» + 1593. Analysis: it's ¼ **Hede 7B** (Schou 2 + 1593 = ¼; ½ would be
  Schou 1). Merge target if confirmed → `dk-bruun-4601`. **BLOCKED**: source
  images down on samlinger.natmus.dk; leave in seed until they return + curator
  eyeballs ½ (17.5 g) vs ¼ (8.7 g).
- **`kmk-122106`** (3_portugaloser Case 6) — KMM «portugaløser» but own tag
  «H 49»; Hede 49 (c4h) = **Speciedaler 1603** (danskmoent c4h49). Suspected KMM
  label error → it's the Speciedaler. Merge target if confirmed →
  `unified-dk-hede-c4h49`. **BLOCKED**: images down; leave in seed.
- **`kmk-298423`** (3_portugaloser Case 8) — undocumented «4 Portugaløser» Johan
  Adolf (Gottorp), unique nominal, no wt/image/mint/catalogue. Either an
  exceptional specimen or a KMM error. Leave in seed; revisit with more data.

**Mechanics used (reusable for the remaining groups).** Same-entity §9a specimen
merges via `merge_decisions/<entity>.yml`; cross-entity relocations (Haderslev =
royal Schleswig → `royal_holstein`, renders both pages) via
`_cross_entity.yml`; off-strikes via `exclusions/<entity>.yml`; classifications
via `classification_decisions/<entity>.yml`. Flow = merger `--apply` (no
`--entity` when cross-entity active) → absorb affected entities → revert the
date-only seed_unified noise (`git diff --numstat | awk '$1==2&&$2==2' | xargs
git checkout --`) → `audit_lost_citations` → commit by pathspec. The §9.4
graph-gate warns «no shared base» on catalogue-divergence + Schou-range +
physical-uniqueness cases (all false alarms) — document the override in the
merge reason.

## 2026-07-09 (later) — Phase-filter fix SHIPPED + reign-span model + coin cleanup

**Phase-filter fix (Part A deferred #1) — DONE, but NOT via the
`_DERIVE_PHASE_FROM_YEAR` generalisation the Part A note guessed.** Final curator
model: **(Change 1)** NO year-filter of coin membership — deleted build.py #6
«year-range sanity» drop + the schema.py chronology validator; a coin lives in its
STORED phase regardless of year. **(Change 2)** `_expand_outer_phase_span` (build.py)
shifts only the TWO OUTER anchors of a fuss (earliest phase year_from/from_label,
latest phase year_to/to_label) outward to cover coins; interior boundaries untouched;
labels auto-generated from coin years. Three guards: `year_verified:false` excluded ·
1914 hard cap (`_MISSION_YEAR_MAX`) · dated-anchor pin (a from/to_label already naming
an explicit year — «30. Mai 1566» — is never overwritten). Self-surfacing: every shift
LOGS its driver coin (⇄ lines). The 4 Haderslev now render on SH.

**Reign-span model — NEW field `Coin.year_is_reign_span`.** A year that IS a ruler's
reign window (placeholder, exact mint year unknown, «1588-1648» Chr.IV) is DISTINCT
from an imprecise estimate («1496-1497»). BOTH are `year_verified:false` (both show
«(?)», both excluded from expansion); the new flag distinguishes them in DATA only (no
render/expansion change). Set by the absorb reign-span override (`_enrich_final_entry`)
when resolved year_ranges == the ruler's reign (`lib.ruler_reigns`) — 159 coins across
danish_realm/royal_holstein/danish_norway/gottorp_duchy. **LIMITATION:**
`normalise_ruler_name` returns None for all NON-Danish rulers, so German dukes/counts
(Ernst III von Gottorp etc.) never get the auto reign-flag — not yet addressed.

**Coin cleanup (drivers the mechanism surfaced):** `f3h91` die-error 1633 (a
NumisMaster-documented «error date for 1653») dropped via _curation_holds; `bruun-14906`
over-merge split (Ernst III Sterbetaler Weinm-153 vs Biblischer Taler Weinm-152, zero
shared index → no_merges); `kmk-158132` over-merge split (4 outliers off the Hede-144
/1629 core via no_merges) + **foundation-reset** (renamed the curated final's id onto
the core `unified-dk-hede-c4h144a` so the 1643 Schou-58 specimen promotes as its own
seed_unsorted final; the foundation-reset trap — a curated final's stored composed_of
re-grabs a split member on the next absorb).

**Whack-a-mole CONVERGED — remaining drivers are legitimate, not errors.** The mechanism
now surfaces `km-44-fr-iii-1655 → 1616` on SH 9_25 — but that is **Frederik III von
GOTTORP** (Duke, reigned 1616-1659; NOT the Danish king), and NumisMaster MC_167284
attests a real 1616 KM-44 «Reuterpfennig». So the 1616 shift is LEGITIMATE, no fix. Twice
this session I mis-read «Frederik III» as the Danish king (§0b) — on this project a bare
«Frederik III» / «Ernst III» is often a Holstein duke/count, NOT the Danish king. OPEN
nuance (not blocking): is a 1616 Gottorp Scheidemünze correctly in 9¼-Thaler-Fuß (label
1622)? — a classification question.

**Change 3 (timeline) — DONE.** The timeline mint-event auto-sync (`📐` log,
`timeline.derive_mint_overrides`) coin-expanded the mint stripe from ALL coins,
ignoring year_verified — so it showed 9_25 mint from 1588 (a reign-span Chr.IV
Skilling) while the phase header, correctly, starts 1622. Added the SAME year_verified
guard Change 2 uses (skip `year_verified: false`); the 1914 cap was already there. The
timeline mint stripe now matches the phase outer-span (9_25 1588→1622, 9_thaler
1559→1566, reichsdukatenfuss[holstein] →1591 Haderslev, 11_333 1700→1725).

**Coin-cleanup tail (all drivers the mechanism surfaced) — FULLY CONVERGED.** The last
SH 9¼-Thaler drivers: km-44 (Gottorp reign-window 1616 → reign-flag), 96114 (stale
source-less 1618 → 1622), bruun-14906/N#278300 (2nd over-merge — Sterbetaler vs
portrait Thaler — split), 120994 (NumisMaster «ND(1618-22)» parser bug → range-start
read as a mint year; corrected to 1622 per Numista N#151529). Only remaining SH shift
= reichsdukatenfuss→1591 (Haderslev, curator-confirmed OK).

**Systemic FOLLOW-UPS (recorded, not done):**
1. **NumisMaster «ND(YYYY-YY)» parser — CODE FIXED, re-flow DEFERRED.** The parser bug
   (reads the range START as a mint year: «ND(1618-22)» → 1618, because the structured
   Date field collapses it AND parse_year_range drops the 2-digit end) is FIXED:
   `parse_numismaster.extract_nd_range()` reads the ND(…) marker + `_complete_abbrev_year()`
   completes the end (raising on a century-boundary rather than guessing), seed builder
   sets `year_verified: false` for `undated` coins. 13 unit tests
   (`tests/test_numismaster_nd_range.py`). Cache re-parsed → 45 ND records fixed
   (submodule commit `8f9b0adaf`; 23 with corrected years incl. MC_101370's 14-year error).
   **NOT re-flowed into seeds/finals** — the numismaster seeds are stale (2026-06-16), so
   a re-seed bundles the 45-coin fix with ~3 weeks of builder drift (scope_note, nominal,
   catalog). (The main-vs-pre1541 two-builder overlap that made this worse was RESOLVED
   2026-07-10 — the pre1541 builder is retired; only one numismaster builder writes
   royal_holstein now.) A surgical ruamel patch reformats the whole file (serialization ≠
   v2_seed_writer). NEXT: a COORDINATED numismaster re-seed (review the full drift +
   reconcile the two builders) materialises the fix into seeds/finals. The one ND coin that
   drove a fuss span (120994) is already fixed by hand.
2. `normalise_ruler_name` returns None for all NON-Danish rulers → German dukes/counts
   never get the auto reign-flag (km-44 marked by hand + kept via _FOUNDATION_IMMUTABLE_FIELDS).
3. N#278300 (Ernst III portrait Thaler) promoted to seed_unsorted after the split — needs
   classification.

## 2026-07-09 — Part A (Bruun mint meta-priority) COMPLETE + crown-map from registry + 2 deferred design decisions

**Bruun mint meta-priority (Part A) — SHIPPED end-to-end.** Parser now extracts
the mint from the cataloguer's meta-line («… Næstved Mint. …») over the
whole-body MINT_RE search (which grabbed unrelated prose mints). Recovered **203
in-scope mints** (mint=None → correct); dual-mint capture («Altona /
Poppenbüttel», «Malmö or Copenhagen») + `/`-split in `classify_mint_to_entity`.
Registry +5 mints (steinbeck→gottorp, jever→oldenburg, reinfeld→sonderburg,
osnabrueck→osnabrueck, aalborg→danish_realm) + gimsøy alias. Full re-flow
(re-parse → re-seed → merge → absorb): **16 mint-driven re-homings** (14
royal_holstein + 2 bremen_verden) + 1 rescue (Karl XI 1686 Stade Taler). 0
duplicate finals, audit_lost_citations 0.

**Crown-map now sourced from the registry** (`mint_registry._CROWN_OWNED` →
`CROWN_MINT_REALM`/`HOLSTEIN_CROWN_MINTS`, build.py imports them). Added the 6
missing royal-Holstein crown mints (Haderslev/Flensburg/Rendsburg/Rethwisch/
Husum/Poppenbüttel) so danish_realm crown coins there widen onto the SH page.
Fixed the wrong Rethwisch registry comment (Plön until 1761, Copenhagen branch
1769-70, NOT «royal Holstein after 1640»).

**Re-homing PRINCIPLE established: auto-re-home only UNCURATED (seed_unsorted)
lots.** Re-homing a coin already curated in another entity strands its curated
final (absorb keeps it + emits a fresh uncurated one → duplicate + lost
citation). `build_bruun_denmark_seed._ENTITY_PIN` pins the 9 curated Bruun coins
that would have wrongly re-homed (Haderslev Portugaløser 4595/4597/4598/4601;
Rethwisch Speciedaler 7748/7749/7753/7754/10781) back to danish_realm; their
mint still surfaces them on SH via the crown-map render-widening.

**TWO DEFERRED design decisions (both awaiting curator):**
1. **Phase-filter «coins define phase years» — ✅ DONE (see 2026-07-09 (later) entry above; the final model differs from this note's guess).** Curator ruling
   2026-07-09: coins define phase year-boundaries; only the page research-window
   (consumes_window) + location status-changes clip — NOT the phase windows.
   Current `_assemble_v2_location` phase pre-filter DROPS 128 in-scope coins whose
   year falls outside a phase window (condition #6 `year_first outside phase`;
   the 9006 «phase not defined» drops are legit seed_unsorted). Fix = generalise
   `_DERIVE_PHASE_FROM_YEAR` (currently 18_5_thaler only) to all fusses +
   clamp-to-nearest (expand, don't drop). 4 open sub-decisions (in chat
   2026-07-09): clamp-to-nearest confirm · phase DISPLAY-range expand? ·
   status-change exception marker (flag vs consumes-window) · rollout scope.
   This is what still blocks the Haderslev 1591-93 coins from SH (their
   reichsdukatenfuss is phase-blocked by SH Phase-I=1600).
2. **Strict mint→entity for the 9 pinned coins?** They're pinned to danish_realm
   respecting existing curation; to instead honour strict mint→entity, migrate
   each coin's fuss/phase to the mint entity via a classification_decision and
   drop it from `_ENTITY_PIN`.

## 2026-06-29 (night) — two skills + gottorp over-merge fixed + audit-expansion fix

> **TWO project skills created (first `.claude/skills/`; `.gitignore` un-ignores it).**
> They are the executable form of the merge/audit procedures — USE THEM going forward:
> - **`v2-merge-coins`** (`b95cd4d`, corrected `1de7a4c`) — merge/split coins safely.
>   `merge_helper.py {resolve,graph,audit,scan}`. Two guards: §9.4 over-merge gate
>   (`graph` → «NO shared base index → STOP») + seed-id resolution (`resolve`). Both
>   would have prevented this session's two errors. Executable PB-1.
> - **`v2-audit`** (`1de7a4c`) — read-only pipeline health review; orchestrates
>   member-resolution + over-merge `scan` + audit_v2 + lost-citation + audit_health.
> - CLAUDE.md «## Skills» section + pre-commit description updated (this docs commit).
>
> **gottorp John-Adolphus Thaler over-merge — MY error, caught by user, fixed (`03acfd5`).**
> I force-merged 5 seeds into one (`85ac423`) on the «KM 33 + KM 35 one coin» premise;
> the user spotted it was really THREE coins (KM 35/Lange 271/Dav 3690 · KM 33/Dav 3688 ·
> KM 41/Lange 274b/Dav 3692 — separated by Krause AND Davenport). Reverted: `no_merge
> [99444, kmk-348805]`; coin 1 = `km-35-ja-1611` (9_thaler/I, foundation reset to
> coin-1-only — it had been poisoned to km=[35,33] and was re-grabbing coin 2);
> coin 2 + coin 3 land in pending (no regression — were pending pre-merge too). **Lesson
> (now the skill's reason-for-being): an auto/force merge on ruler+nominal+year with NO
> shared catalogue index is the recurring trap.** coin 3 (`kmk-348805`+`99448` = KM41 ≡
> Lange 274b, curator «хай буде 3») is now RECORDED as an explicit force-`merges`
> (`ef2fc0e`); `merge_helper.py scan` skips any entry fully covered by a force-merge
> group, so a curator-vetted no-shared-base identity no longer re-flags (gottorp 4→3).
>
> **The «5 remaining orphans» were a FALSE POSITIVE — averted re-pointing them (`1de7a4c`,
> `22d7ffc`).** My orphan audit checked exact `member in seed_ids`, so it flagged bare
> Hede codes (`dk-hede-c4h112`×4, `dk-hede-f5h12`). But the MERGER deliberately expands
> them (`_expand_member`: dk-hede-c4h112 → c4h112a/c4h112b, grouped so no_merge never
> blocks the within-coin pair). Re-pointing them to a flat sub-variant list would have
> BROKEN c4h112a-c4h112b. Fix: validate_decisions `--check-members`, merge_helper `audit`,
> and audit_v2 I6 now all mirror `_expand_member_against`. **NEVER re-point a bare Hede code.**
>
> **Orphan backlog: 7 → 0 for merge-decisions.** `km-305-2-fr-iii-1669` + `km-596-fr-v-1763`
> (folded V1 final-ids whose Bruun seeds were already members — verified data preserved in
> f3h121a/f5h38a) DROPPED (`f8272ce`, no-op: merger was already skipping them). The other 5
> were the false positive (now resolve). Pre-commit member-resolution guard PROMOTED to
> HARD BLOCK (`22d7ffc`).
>
> **audit_v2 I6: 10 → 0.** Fixed false positives (bare-Hede merge members + km-645 which
> resolves via FINAL-id, now accepted — `22d7ffc`), then HEALED the 2 genuine stale
> classification refs (`80818c3`, NO re-absorb — they resolve on the file edit alone, the
> coins already carry the correct classification, so a re-absorb would only add drift risk):
> - `km-635-1-chr-vii-1778` (royal_holstein) — RE-POINTED coin_id → `unified-dk-hede-c7h28`
>   (the real coin, already 11_333/I/scheide as a foundation; no-op assignment made
>   functional); the 3 sibling «see km-635» reason refs updated to «see unified-dk-hede-c7h28».
> - `unified-dk-bruun-7893` (danish_realm) — DROPPED (coin cross-entity-moved to
>   royal_holstein c7h25 = km-645, already kurant 11_333/I).
> **audit_v2 I4: 51 → 5 (two schema fixes).** (1) `55a04a3` — the 43 naked KMM museum
> specimens (seed_unsorted, no year, no KM) no longer fail: `year_label` / `year_first`
> optional for `fuss == seed_unsorted` (new `_check_year_required` keeps them mandatory for
> every classified/rendered coin). (2) `f720155` — the 3 cross-volume dict-form `km` coins
> (`c5h125a` / `f3h153a` / `km-696-1`) now validate: `catalog.km` dict value is
> `str | list[str]` (was `str`), modelling `{sh:['108','110'], dk:['77','77.1']}`. Both with
> regression tests. The **5 remaining (3 distinct) are SEPARATE pre-existing issues**: 2
> out-of-scope metal-enum values (`unified-dk-numista-422716` / `-342834`) + 1 `phase.str`
> (`galster c3g-131`). audit_v2 --quick (pre-commit) skips I4 regardless.
>
> **Earlier this session (pre-night):**
> - «oldest gold coin of Scandinavia» claim DROPPED for the Hans Rhinsk Gylden (`579aff6`)
>   — Numista N#426966 (Erik of Pomerania gold, ~1396-1439) predates it; Hede didn't know.
> - rhinsk_gylden_fod `pdate_label` collapsed to «~1497 → 1632 · 135 Jahre» (`21dcaa7`).
> - **Full V2 re-flow catch-up (`1132f83`)** — `7680446` (Aagaard) had scrubbed 3 Danish
>   finals via a targeted pass, NOT a full re-absorb, leaving them stale; a merger+absorber
>   re-run synced danish_realm/royal_holstein/_unclassified/gottorp final (0 citation loss,
>   audit_v2 unchanged). **Lesson: a targeted final scrub leaves final stale vs seed_unified —
>   re-absorb after.**
>
> **STILL DEFERRED (older):** f7h7 (Prøvemønt tangle), c9h18 ~29 KMM museum rows.

## 2026-06-28 — B1 over-union cleanup (group D / Pattern B), 8 of 8 COMPLETE

> **Context.** The over-union (Pattern B / group D) audit found 25 danskmoent-page
> collision groups where distinct coins carry each other's Hede sub-letters in
> `catalog.hede`. Sub-categories: B1 distinct-KM (8), B4 same-KM/diff-Sieg (9),
> B2 specimen-fold (4), B3 cross-entity (3), B5 (1). Working through B1 (8) one by
> one on user verdict. Pattern: most are NOT merges — they're genuinely distinct
> types whose catalog.hede over-unioned; a few ARE one Hede type Krause split by KM.
>
> **DONE (committed):**
> - **c4h105** (`dce7296`) — Hede 105 = one «2 Krone» Chr IV; merged KM 60 (105A mit
>   Stern) + KM 61 (105B ohne Stern) into one entity, KM [60,61].
> - **c4h92** (`7a7534a`) — TWO types, not over-union: Hede 92/KM 33 (portrait, Sieg
>   72) vs Hede 77/KM 12 (oval shield, Sieg 71). dk-tid-163044 (KM 12a) was wrongly
>   Hede 92A → re-identified as Hede **77C**, re-homed. merge [dk-bruun-4705,
>   dk-hede-c4h92b, dk-hede-c4h92a] + 5 no_merges (Hede-92A out of KM-12). NB the
>   KM-12 coin now belongs to the **c4h77/Hede-77 family** — a SEPARATE deferred
>   cleanup (Numista 55303 = KM 12/Hede 77,77A 1602-1604 + floating natmus 77A/B/C).
> - **c5h67** (`5dfee7e`) — Hede 67 «1 Krone» Chr V, KM 330(67A)+370(67B) → one row.
> - **c5h31** (`5dfee7e`) — Hede 31 «1 Dukat» Chr V, KM 412+415.1+415.3 → one row.
>
> **Also DONE (committed):**
> - **c5h125** (`7f0bb41`) — «4 Marck Danske» Chr V Glückstadt, six clusters all Hede
>   125 → one entity. Dual-volume KM kept distinct via dict-form km_register
>   `{dk:[77,77.1,77.2,83], sh:[108,110,114]}` (KM-DK# on denmark, KM-SH# on SH; note
>   documents both). Folded km-108/110/114 finals.
>
> **DONE (committed):** c9h1 (`6058712`) — split «2 Christian d'Or» by reign: Chr VIII/KM 722/Hede c8h1 (1841-1847) vs Chr IX/KM 773/Hede c9h1 (1866-1870); ruler fixed (source error danskmoent c9h1.htm desc says Chr 8). NB Chr IX inherits phase I — review.
>
> **REMAINING B1 (2 — complex splits), user-confirmed, plans ready:**
> - **c7h13** «1 Speciedaler» Chr VII 1795-1801 (royal_holstein) — Hede 13 = KM 651 +
>   KM 654 (merge). BUT **Numista 131730 = KM 640 is a DIFFERENT coin (over-merge)**
>   inside the c7h13a cluster — split it OUT to its own row. Split-mixed-cluster shape
>   (no_merge + force-merge, c4h92 pattern).
> - **c9h1** «2 Christian d'Or» (danish_realm) — TWO coins; the Hede-1 clash is because
>   **Hede index restarts per ruler**: Hede 1 = KM 773 (Christian **IX**, 1866-1870)
>   AND Hede 1 = KM 722 (Christian **VIII**, 1841-1847). dk-tid-130240 is over-merged
>   ACROSS both reigns (KM 722 + years 1841-1847 AND 1866-1867). Split into Chr VIII/
>   KM 722 + Chr IX/KM 773 — fix indices AND years AND rulers. **Source error
>   (user-flagged, record in SOURCES §13):** danskmoent c9h1.htm link correctly says
>   Christian 9 but the description text erroneously says Christian 8 — don't let it
>   mis-set the ruler.
> - **c4h119 — DONE** (`38c0275`): split KM 66/Hede 118 (1619) vs KM 67/Hede 119
>   (1619-1623); no_merge+force split the mixed cluster, 6 year_demote stripped the
>   museum reign-span years. [orig plan:] «1 Skilling» Chr IV (danish_realm) — NOT a simple over-union: KM 66 /
>   Hede 118 (1619, oval... portrait) renders as TWO duplicate rows
>   (`unified-dk-hede-c4h118` clean + `unified-dk-hede-c4h119a` messy). Plan
>   (user-confirmed): (1) merge messy c4h119a into clean c4h118 → KM [66,66.1,66.2],
>   Hede [118A,118B], Sieg 31, Schou 142-143, year **1619** (strip the museum
>   reign-span 1588-1648 that came from 5 natmus specimens dated to the whole Chr IV
>   reign); (2) c4h119b (KM 67/Hede 119) keeps 119A-D, fix year_last 1629→**1623**
>   (1629 came from natmus kmk-344187's over-broad date); restore Hede 119A (seed
>   dk-hede-c4h119a) to c4h119b. Same split-mixed-cluster shape as c4h92 (no_merge
>   + force-merge to route the Hede-119 seeds off the KM-66 cluster). The 12 KMM
>   Hede-119 floaters in c4h119a are weightless (no measurement-data loss).
>
> **Reusable pattern for these (proven c4h59/c4h105/c4h92/c5h67/c5h31):** merge_decision
> at seed_unified (durable) → `merge_seeds_cross_source --apply --entity X` → verify
> seed_unified split → `process_entity` convergent check → dedup fold helper on finals
> + set composed_of to convergent (NO pin) → fix notes/years → validate + audit_v2
> (must stay 0) → build location → commit (hook ~3 min). For mixed-cluster splits use
> the COMPLETE block-set no_merge (block the moved seed from ALL catalog-less members
> of the wrong cluster — c4h116 lesson).

## 2026-06-26 — thin-line metal consensus + Pattern-A dedup + 2-Dukat-1747 regroup

> **Thin-line metal consensus (`f41217d` code+tests, `078f66a` 19 data flips).**
> `_collect_metal` now resolves {silver,billon}/{bronze,copper} via per-resource-
> collapsed authority-weighted vote + fineness tiebreak (Hede billon boundary ~0.30,
> NOT textbook 0.50). One-time 19-flip correction applied. Tests: `tests/
> test_thin_line_metal_consensus.py` + updated `test_metal_conflict_guard.py`.
>
> **Pattern-A duplicate final-foundation fold (`69255e4`).** New `scripts/maintenance/
> dedup_final_foundations.py` folds confirmed true-dup foundations (V1/curated entry
> + its unified twin coexisting because absorb does NO final-vs-final dedup). 4 folded
> via §9a (c4h105 km-61-1⊕hede-105a, f5h11 f5h12⊕f5h12ab, c7h13 c7h13a⊕km-651-1,
> c9h13 c9h13a⊕km-798-1) — all identical-KM confirmed. Durable: twin pinned in
> keeper.composed_of, revalidate keeps same-nominal members.
> **SURFACED then ALL RESOLVED 2026-06-26/27 — block closed** (was left mislabelled
> «not actioned»; corrected 2026-07-02 after it kept re-surfacing as a false open item):
> - **c4h115** (km-81 / bruun-5181) — ✅ folded `26d2a45` (curator «one coin»):
>   bruun-5181 → km-81 via merge_decision [dk-bruun-5181, dk-hede-c4h115a]; the divergent
>   1.462g / 0.437 NumisMaster reading kept §9a list-form + deviation note; standalone deleted.
> - **f3h62** (bruun-6403 KM-240 / f3h62ab KM-241) — ✅ §CN errata `62e800a`
>   (curator-approved km 240→241 on bruun-6403; the canonical KM-240 slip = 1 Speciedaler
>   Hede 61, a genuine separate coin still at km-240); bruun-6403 folded into f3h62ab.
> - KM-differ candidates — ✅ all closed 2026-06-27: **c4h116** `adeb443`, **c5h57**
>   `48f49ee`, **c9h16** `21fbdcd` (§CN errata), **f6h27** `1287d4c`, **c4h59** `f2a9291`.
>
> **2-Dukat Frederik V 1747 family regroup (`87ba864` data, `a0a5ea5` graph).**
> Investigated via catalog_graph.py component 10 + danskmoent/Numista. The 3 genuine
> Hede types (10/12/14) each Bruun-anchored to one KM (568.2/569/570); KM 567/568.1
> carried no Hede so the matcher scattered them. Design-match + Friedberg bridge:
> **KM 567 = Hede 10A** (bust/brystbillede), **KM 568.1 = Hede 10B** (head/hoved).
> merge_decisions force them into Hede 10 + merge f5h14↔bruun-7612 (KM570) + keep
> kmk-332101 (Schou 3) in Hede 12. Merger re-applied (seed_unified family-scoped);
> final hand-reconciled to match seed_unified (avoids the entity-wide absorb re-flow
> +18 stale-purge drift) — future absorb idempotent on the 3 entries. **Structural
> fact (worth a SOURCES.md §13 note, NOT yet added):** no single-record KM↔Hede
> cross-ref exists for Danish gold — Danish catalogues (danskmoent/Hede/Schou/Sieg)
> carry no KM, Krause/NumisMaster/Numista carry no Hede; the only bridge is Friedberg
> or design-description match. Don't waste a session hunting a direct cross-ref.

## 2026-06-24 (later) — §9a salvage + galster-key fix + full re-flow shipped

> **§9a thinning now SALVAGES dropped specimens' distinguishing data** (`c199b93`
> code+test). Before: thinning a ≥5 bucket to min/middle/max dropped every other
> specimen wholesale, losing any distinct catalogue index (the `others`
> sub-catalogue: schrötter#/olding#/dorfmann#/galster sub-variants) or fineness/
> diameter the reps lacked. Now `_salvage_unique(reps, dropped)` (`lib/seed_thin.py`)
> unions distinct catalogue indices onto reps[0] + fills fineness/diameter only when
> reps lack it; redundant weight + per-specimen sources still shed. Wired into both
> `thin_coins` + `thin_kmk_seed.thin`. 7 unit tests (`tests/test_seed_thin.py`).
>
> **galster-key fix (`66649db` code, `381f35a` seeds; kmk 13819→14003).** The salvage
> exposed a latent bug: the thinning bucket key (`_subvariant_key` in both thinners)
> OMITTED `galster` (a type-identity register, like km/hede/sieg/schou; thin_kmk_seed
> also lacked `lange`). So distinct Galster types (57 Kbh-Søsling vs 63 Malmö-Søsling
> vs 104 ChrIII-4Sk) shared one bucket → collapsed → salvage unioned their galster
> onto one rep → f1g-57 bloated to [5,57,57A,57B,63,104,567B] → 7 transitive
> over-merges. Added galster (+lange) to both keys → over-merge resolved (f1g-57 →
> [57,57A,57B]), +184 distinct Galster types recovered. Verified vs danskmoent:
> f1g57 = «Søsling 1524 København, Galster split into 57A/57B groups».
> Plus two KMM `typeNumber` data fixes in `build_kmk_seed._catalog` (curator-approved):
> galster sub-variant case-norm (57b→57B; scoped to galster — Hede/Lange/Schou case
> convention NOT uniformly uppercase) + builder-level source errata for 3 malformed
> strings (309770 «Galster 5 + B», 311330/311331 «G. 567B» → 57B; f1g5/f1g567 both
> danskmoent-404). Errata in the BUILDER not data-`_source_errata` because these thin
> into the 57B bucket and an entry-level carrier wouldn't survive the next rebuild.
>
> **TOOLING LESSON (merge carry-forward):** when a builder's catalog OUTPUT changes
> (errata/case-norm/key change), a routine `--write` (merge) deep-merges the stale
> on-disk catalog value with the fresh one → list-form bloat (e.g. galster ['5','57B']).
> For a non-curated source (KMK/IKMK) flush with `--write --no-merge` once; then
> routine `--write` is idempotent again. Verified: post-flush `--write` holds 14003,
> 0 bloat.
>
> **denmark UK preamble** (`9df01d6`): «sjælland-ський åbent Brev» (Cyrillic-suffix
> hybrid, §2 trap) → «зеландський відкритий лист» (descriptive, parallel to «норвезький
> ордонанс»). DE/EN keep the Danish proper name. Only the preamble; the 5 other UK
> occurrences already used clean «Sjælland åbent Brev».
>
> **FULL RE-FLOW DONE (`9e8b6f7`)** — merger+absorb all 22 entities, propagating the
> thinning + galster fix to `final/`. Merger 24266 seeds → 15433 unified (8763
> confident folds, 963 conflicts logged to match_uncertainty, no coin loss). Absorb
> final 15152; **522 stale non-curated `seed_unsorted` stubs dropped** (their backing
> specimens were §9a-thinned — EMPIRICALLY verified 0 curated entries in the drop set
> via `_is_vanished_stale_final`'s `not _final_is_curated` guard; curated finals that
> lost backing are RETAINED). Build clean; audit §9a = 0 remaining ≥5 buckets / 0
> same-weight dups. The big line-diff (−82k) is the thinning finally reaching final/.
>
> **Minor open (out of scope, flagged not fixed):** `unified-dk-galster-hg-238` (Hans)
> carries «Lagerqvist 9a-f» in its `catalog.galster` field — a Lagerqvist ref misfiled
> into the galster register. Not touched.
>
> **Pre-existing backlog (NOT from this session):** audit_health shows 588 prose-lint
> errors (§W cleanup) + 1 i18n error — coin-data re-flow doesn't touch prose surfaces.

## 2026-06-14 — KM render-leak fix + two pipeline fixes staged for the coordinated apply

This session, in order of the user's reports:

1. **KM str-repr corruption — FIXED + applied (commit 38f4f67).** 6 V2 final
   entries carried a `catalog.km` list whose first element was a Python
   str-repr of the real KMRef-list (`"['63', {'value':'103','register':'DK'}]"`),
   a leftover from the 2026-05-31 «44-false-positive» `str(km_list)` bug
   (the write path is long fixed; only the baked data remained). Repaired via
   `scripts/maintenance/fix_corrupted_km_repr.py` (faithful explode+dedup, no
   register re-adjudication). Trigger coin c5h121 now renders «KM-DK# 103 ‖
   KM-SH# 63». seed_unified was already clean; only final changed. Verified:
   0 leaks across schleswig_holstein + denmark, 3 langs.

2. **2 Frederik D'or Hede 1B+1C merge — DECLARED, NOT applied (commit 17b4e69).**
   User: «це одна монета». Diagnosed (empirically via `match_pair`): the
   auto-matcher's §9a `_has_type_strong_agreement` gate uses RAW catalog
   overlap, so sub-variants (Hede 1B vs 1C, KM 750.2 vs 750.3) don't overlap →
   pair drops to low_confidence → never unites. Mint was NOT the blocker
   (both carry Altona). Same cross-letter class as Ungersk Gylden 8A/8B.
   Fix = per-entity `merge_decisions/royal_holstein.yml::merges` (9 source
   seeds). Dry-run preview confirms one unified entry, no catalog conflicts.
   Takes effect on the next merger+absorb apply.

3. **Numista «Royal Danish» mint — registry fix DORMANT, NOT propagated (commit c9d9f8d).**
   «Royal Danish» = «Royal Danish Mint» (Den Kongelige Mønt) = Kopenhagen,
   verified via Numista cache (`mints[].name`, `mint_text`). The seed writer's
   « Mint»-strip reduced the API name to «Royal Danish», absent from the
   registry → surfaced as a bogus mint on 418 V2 entries (all sourced from
   numista). Fixed at the single source of truth: added «royal danish» +
   «royal danish mint» to the kopenhagen alias set in `mint_registry.py`.
   Dormant for render (build reads final mint as-is). User chose to defer
   propagation to the coordinated apply. **At apply:** the 24 numista seeds
   carrying `['Altona','Royal Danish']` become `['Altona','Kopenhagen']` →
   `classify_mint_to_entity` returns `[danish_realm, royal_holstein]` (multi)
   instead of scalar `royal_holstein`. **KEEP this — do NOT drop Copenhagen.**
   §0b CORRECTION (2026-06-15): an earlier caveat here hypothesised the
   Copenhagen was a «spurious Numista guess» to authority-drop. That was a
   hypothesis-as-conclusion and was REFUTED on verification: for 19 of the 24,
   Copenhagen is independently confirmed by Bruun and/or NumisMaster (and Hede
   for KM 631) — they split the KM sub-variants by mint (.1=Kopenhagen,
   .2=Altona, etc.). These are GENUINE multi-mint Altona+Copenhagen types, so
   the `[danish_realm, royal_holstein]` joint classification is CORRECT (they
   render natively on both pages). The other 5 (KM 600/651/767/763/958) have no
   independent corroboration but no refutation either → keep per §0b. NOTE: KM
   631 is therefore a genuine joint coin — the «single royal_holstein, denmark
   consumes it» modeling chosen on 2026-06-14 was under the wrong premise;
   joint `[danish_realm, royal_holstein]` is the accurate model (pending user
   confirmation).

**→ The «coordinated full apply» now bundles 3 things** (all gated on the
curation-loss audit, TODO #6 / parked task #4-#8): (a) Ungersk Gylden
cross-entity merge (commit 431a18b, `_cross_entity.yml`); (b) Frederik D'or
merge (17b4e69); (c) Royal Danish seed-rebuild (re-run `build_numista_seed.py`
from cache — NO live API — then merger+absorb). Sequence: curation audit →
re-run numista seed-builder → full merger `--apply` (no `--entity`, so the
cross-entity source-side excludes apply) → absorb dry-run gate → absorb
`--apply` → build `--include-v1` → verify. The merger/absorb REBUILD fresh
from members, so stale «Royal Danish» is replaced (not appended) once the
seed source is fixed — addresses the «additive-only» concern.

## Denmark gold-gylden Rhinsk/Ungersk reclassification — SHIPPED 2026-06-12

Discriminator between `rhinsk_gylden_fod` (Rhenish gylden, .75 / 18 Karat /
72 per Cölln. mark — **academic source: Wilcke 1950 w7-2 p.184 «Rinske
Gylden (18 Karat, 72 Stkr.)»**, ref `wilcke-rhinsk-gylden-1524-standard`) and
`reichsdukatenfuss` (Ungersk/Dukat, .986) is FINENESS, not weight. Numista's
generic "Goldgulden" label hides this → systematic misrouting. danskmoent/
Galster classify each coin (Galster 27 = Rhinsk; Galster 46 / c2g-89 =
Ungersk). Fixed so far:
- Frederik I 1527 (Galster 59) → rhinsk_gylden_fod (commit eefddf5).
- Hans ~1497 N#355730 (Galster 27, danskmoent hg27 «den ældste i
  Skandinavien») → rhinsk_gylden_fod; now the EARLIEST Danish Rhinsk Gylden
  (commit 682e5e5). reichsdukatenfuss de-facto anchor corrected 1481→1513
  (Christian II Ungersk Galster c2g-89, already on the fuss) — the old prose
  wrongly used the Hans Rhinsk coin as the .986 anchor.

**OPEN follow-up (flagged, not done): ~58 seed_unsorted gold gylden/dukat
coins** on danish_realm carry the same Numista-"Goldgulden" ambiguity (e.g.
f2h7e Ungersk / f2h7g Rhinsk 1584, kmk-137161/2 Ungersk 1592, kmk-575432
Frederik I 1531 Ungersk). A Rhinsk-vs-Ungersk classify sweep by
danskmoent/Galster fineness is the next batch task. Mechanism reminder: a
coin only renders on its bar if `phase` is defined for that fuss AND
year_first is within the phase year-envelope (±1) — extend the phase/bar
year_from when a coin predates it (build.py:1005-1023). Duplicates across
sources merge via `promoted_to` + `composed_of` (Pass 1 skips promoted).

## Fuss cross-reference system — SHIPPED 2026-06-11

Prose references a Müntzfuß by stable id now — `[fuss:KEY]` — not a
hand-written `<code>Name</code>` span. Post-render resolver
`scripts/lib/fuss_refs.py::process_html(html, lang, name_map)` (mirrors
`refs_pool`, called at both build.py post-render sites) substitutes the
EFFECTIVE name (per-location `fuss_periods[KEY].name` override layered
over global `fuesse[KEY].name`) and links to `#fuss-KEY` when that card
is on the page (plain `<code>` otherwise; unknown key → visible §0
placeholder). build_landing gained a `fuesse` param for the global-name
map. Migration `scripts/maintenance/migrate_fuss_xrefs.py` (idempotent)
converted 168 refs across fuesse.yml + V1/V2 location yamls. Tests
`tests/test_fuss_refs.py` 7/7. Payoff proven in render: same
`[fuss:reichsdukatenfuss]` → «Rigsdukatfod» (linked) on Denmark,
«Reichsdukatenfuß» (plain) on Hamburg. Cross-PAGE linking deferred (would
need a key→owning-location map). Full spec + as-built:
`docs/fuss_cross_refs_design.md`. **Next:** if a new fuss is referenced
in prose, just write `[fuss:newkey]` — no name, no `<code>`. Optional
follow-up noted in design doc: an `audit_prose.py` rule flagging NEW
hand-written `<code>fuss-name</code>` spans to stop the convention
eroding.

Also this session (2026-06-11), earlier commits 4a86665 / 8428c9f /
627c4a8: Nobel/Rosenobel prose polish — UK «сучасн-»→«тогочасн-» where
period-relative; rosenobel «contemporary→earlier nobel_fod» factual fix;
«Reichsdukat»→«Dukat» (Danish coin name) in the Nobelfod description.

## composed_of re-validate + full re-merge (2026-06-09) — SHIPPED

The absorb stage is additive + STICKY: once a unified entry lands in a
foundation's `composed_of`, no later run re-checked whether it still
belonged. Earlier mis-groupings (and V1-bootstrap composed_of carried
forward) persisted forever — KM 42 «8 Skilling» (`dk-tid-163034`) had
dragged in «1 Denning» (0.44 g) + «4 Skilling lybsk» (1.822 g) + two
«6 Skilling», polluting the 8-Skilling weight envelope.

**(A) `_revalidate_composed_of` — `51a609c` (absorb code + danish_realm final).**
New absorb-stage pass (default on; `--no-revalidate` to skip). Evicts a
composed_of member iff its normalised nominal GENUINELY differs from the
foundation's AND the two share NO agreeing type-level catalogue — the SAME
nominal discriminator shipped in `match_pair`, applied to existing
membership. **Uses the merge module's synonym-aware `_normalise_nominal`
(imported as `_mg_normalise_nominal`), NOT v2_seed_writer's bare one** —
else synonym pairs («1 Ducat» vs «1 Dukat») false-evict (caught in dry-run:
18→12 once the normaliser was fixed). The weight-tier disambiguator is
DELIBERATELY NOT used (same-nominal weight divergence = specimen variance,
not a different coin; verified 24/38 weight-tier drops were same-nominal).
Evicted members are surgically decontaminated off the host
(`_surgical_decontaminate`: only their EXCLUSIVE weight/source values
removed — orphan + remaining-member data preserved per §9a; twin-
independent, no clean-snapshot needed), dropped from composed_of, and
force-promoted standalone (reuses the over-merge-purge `forced_evict_promote`
path) so they re-home; the discriminator then blocks re-absorption.
danish_realm: 12 evictions / 8 hosts → 10 re-homed standalone + 2 matched
into correct existing finals; **0 coins lost**.

**(B) Nominal folds — `1d08444` (`lib/nominal_synonyms.py`).** Two residual-
edge folds for the discriminator (issuer-PREFIX «Oldenburg. Taler» was
already handled by `_strip_region_prefixes`): worth-equivalence tail strip
(`= …` → "", handles «1 Thaler = 1/14 Cölln. Mark» + the trailing weight-
standard gloss) + `_strip_mint_suffix` (drops trailing «. <Mint>[ og <Mint>]»
when the segment is mint-only — «4 Skilling Rigsmønt. København og Altona»
→ «4 skilling rigsmont»; conservative, leaves «100 Rd. Conr.» / «Cölln. Mark»).

**(C) Full re-merge + re-absorb — `2fcde35` (22 seed_unified + 5 final + 19 cd).**
Materialises the discriminator + both folds across ALL 22 entities (prior
ship covered only 4). 26651 seeds → 17337 unified (9314 merges). **Seed
conservation verified — ZERO seeds lost everywhere**; only `_unclassified`
grew (+322 newly-harvested seeds entering the merge → classification
backlog, NOT a loss). danish_norway/royal_holstein/bremen_verden finals
net −6/−1/−1 from legitimate cross-source de-dup (all underlying seeds
confirmed still reaching a final). KM 42 stays clean (idempotent).

**Deferred / open after this task:**
- **`_unclassified` +322 classification backlog** — newly-harvested seeds
  now in `seed_unified/_unclassified.yml` awaiting entity routing.
- **General re-validate re-homing across transitive over-merges** — the
  current pass evicts identity-mismatches one-level; a transitivity-aware
  variant (re-home dropped members that themselves anchor a sub-cluster)
  was scoped but deferred as regression-prone — own focused session.
- «= X» / «Rd. Conr.» nominals beyond the folds above are curator-territory
  (genuinely ambiguous worth-equivalences) — left as-is.

## Catalog-index normalization + KMM thinning (2026-06-08) — SHIPPED

Shipped (details in commit bodies): catalog-index normalization + restart-scope
registry (`17c7e91` `75734e6`), natmus erratum Hede 141→134 (`18a5fbe`), KMM
citation thinning (`7d37a92` `758cfba`), verified-mint divergence disqualifier
(`775660e` `e8f6215`), nominal discriminator (`fb7bc80` `a6e7f8b`), mixed-number
fraction fix (`6238372`), Numista re-parse, Davenport volume-fold (`bc1f9d7`),
Numista multi-KM accumulation (`29b5de2`), catalog-index range-collapse (`94d6213`),
Rhinsk Gylden metal gate (`896ffef`), weight thinning in absorb (`fb91804`, since
superseded by the 2026-09-12 layer split).

**OPEN / next (all user-directed this session — designs captured, NOT yet built):**
- 🟡 **re-validate-composed_of absorb pass (HIGHEST leverage — now doubly motivated).** The
  absorb NEVER re-validates existing composed_of members (only adds), so historical bad
  merges are STICKY — they survive every re-run + every new discriminator. This is why
  c4h55's foundation mint stayed polluted, and why KM-42 (`dk-tid-163034`, 8 Skilling
  Christian IV) STILL carries 2 wrong-type specimens despite weight-tier-1 already
  rejecting them: **KMM 137199 «Denning» 0.44 g «Sch 83»** (Russian-kopeck imitation) +
  **KMM 591520 «4 Skilling Lybsk Rytterpenning» 1.822 g «Sch 42»** — both merged via a
  bare-Schou collision with the Hede-93 Schou cross-refs. NOW the weight-thinning surfaces
  the 0.44 Denning as the displayed min, so this pass is the clean-up. The fix: an absorb
  pass that re-runs `match_pair(member, foundation)` over every existing composed_of member
  and DROPS those now `no_match`. Self-heals the whole sticky class (KM-42 anomalies via
  weight-tier-1, Wolfenbüttel residue via mint discriminator). Uses only SAFE existing
  discriminators — no synonym risk. MUST dry-run with a printed drop-list for review.
- 🟢 **Residual discriminator edge false-splits (curator-mergeable, low priority).** After
  shipping (below), ~2 edge categories still split as FALSE on danish_realm: a trailing
  «. <mint>» annotation («4 Skilling Rigsmønt. København og Altona» vs «4 Skilling Rigsmønt»)
  and «= X» equivalence nominals («12 Rigsdaler courant = 2 Rigsdaler» vs «2 Rigsdaler»). Too
  niche/risky for a broad fold; if they surface as real duplicates, merge via
  `merge_decisions/`. The forgery splits («1 Skilling samtidig forfalskning» vs «1 Skilling»)
  are arguably LEGIT (distinct items) — leave.
- 🟡 **Classify the 13 new Hesse-Kassel Numista coins** (`data/v2/classification_decisions/
  landgrafschaft_hessen_kassel.yml` pending list). They entered as `seed_unsorted` in the
  full re-parse below — assign fuss/phase (or fix matcher rules) per PB Phase-4. The 322
  new `_unclassified` Numista types are NOT rendered and need no action unless a future
  classification pass routes them.
- 🟢 **Rhinsk Gylden seed_unsorted tail (follow-up to the c3h14/c3h15 fix above).** gold
  Rhinsk Gylden `galster-hg-27` and `galster-hg-gej` sat in `seed_unsorted`
  (`f2h7g` is classified since, `rhinsk_gylden_fod` II). They belong in `rhinsk_gylden_fod` too — classify them (the metal-gate
  fix means a re-run of auto_classify won't mis-route them to silver). «1 Denning» (c4h169)
  = Russian-kopeck-imitation trade coin (1619 Glückstadt) — stays soll-less, NOT Rhinsk.
- 🟢 **Foundation-mint pollution (systemic note).** c4h55's foundation had accumulated a
  wrong mint (Wolfenbüttel) from historical bad merges; the absorb matches against the
  STORED foundation mint (re-derives only in enrich, AFTER matching), so the pollution
  survived re-runs until cleaned by hand. Other foundations may carry similar pollution —
  a «re-validate existing composed_of members against the current matcher» absorb pass
  would self-heal both this and the sticky-member problem.
- 🟢 `mb` index (24 % xEntity, 0 % xRuler) left bare — verify restart axis + scope if
  per-region.

## Soll/Δ-gap sweep (2026-06-07) — 8 coins fixed, 16 surfaced

User flagged on the rendered Denmark page: rows with weight+fineness (so a
Feingewicht is computed) but blank Soll/Δ. Root cause: the build's `_compute_coin`
needs `coin.fraction` to be a key in `fuss.fractions`; many coins had
`fraction: None` (or a fraction the fuss didn't define). **Audit any time with
`scripts/maintenance/audit_hede_seed_loss.py`-style logic OR the inline check
(weight+fineness present, fuss≠seed_unsorted, fraction not in fuss.fractions).**

**FIXED (commits b79ae73, b59267b):** Nobel 2/3 (added nobel_fod fractions «2»/«3»
= 2x/3x the per-Nobel Soll, §0 computation attribution) + 7 coins where the fuss
already defined the key, fraction just None → set deterministic Δ-verified value:
rhinsk_gylden_fod «1»; 8_daler_fod 1 Gulden «1» / 8 Skilling «1/6» (1 Daler=48 Sk);
18_5_thaler 8 Rigsbankskilling «1/12» (8/96) / 16 Rbsk «1/6» (16/96). All Δ within
tolerance.

**SURFACED — 16 coins still soll-gap, need curator decision (NOT auto-set):**
  - `reichsdukatenfuss` «4 Speciedaler» (unified-dk-numista-117501) — LIKELY
    MIS-CLASSIFIED: silver .875 4-Speciedaler (fein 100.71 ≈ 4× 9¼-Speciedaler)
    sitting under a GOLD Dukat fuss. Re-classify to 9_25_thaler «4» (or 9_thaler)?
  - `11_333_thaler` «3 Krone» (numismaster-65368) — gold .993, fein 44.97; ratio
    under this fuss unclear (possible gold-under-silver-fuss mismatch).
  - Scheidemünze / billon sub-denoms where a full-Kurant Soll would be misleading
    (the −% IS the seigniorage per §6 — curator call whether to show it):
    `8_daler_fod` 1 Hvid / 1 Penning / 2 Skilling ×5; `9_thaler` 1 Denning;
    `9_25_thaler` 3 Skilling Lybsk ×5 (Lybsk-skilling ratio needed);
    `8_daler_lybsk_fod` 2 Rhinsk Gylden.
  - Note: fraction auto-derivation (`absorb`/`lib.fraction_infer`) only runs on
    newly-absorbed entries + can't resolve sub-unit ratios (8 Rbsk→1/12) — a
    general «derive fraction over ALL final entries + sub-unit ratio table» pass
    is the proper long-term fix.

## Harvest coverage state — ucoin + Numista (2026-05-20)

> **For the next harvest session**: detailed snapshot of where every
> ucoin period and Numista bucket stands. Full per-NID gap manifests
> live in `scripts/cache/{ucoin,numista}/_BR_audit-2_2026-05-20.json`
> + `_BO6_audit_2026-05-20.json`. Don't re-enumerate — use the gap
> lists directly. Period IDs map to `?country=X&period=N` URLs on
> ucoin.net catalog. **31 local commits ready to push** at session-
> handover snapshot (`af737ee` → `dad58eb`).

### ucoin — 15 of 15 periods verified (BR audit-2 complete)

✅ **Verified clean (10 periods, exact page-by-page match):**

| Period | Era | Cached / Total |
|---|---|---:|
| DK p2940 Speciedaler 1582-1624 | Christian IV pre-Kipper | 83 / 83 |
| DK p2939 Glückstadt 1617-1773 | DK-rule Glückstadt mint | 50 / 50 |
| DK p2995 HG-Rendsburg 1716-1720 | Holstein-Gottorp under F4 | 4 / 4 |
| DK p374 Christian IX 1873-1906 | Krone-era memorials | 9 / 9 |
| DK p373 Frederik VIII 1906-1912 | Krone-era full reign | 7 / 7 |
| DK p646 Rigsdaler rigsmønt 1854-1873 | F7 → C9 | 13 / 13 |
| NO p2399 Speciedaler 1648-1699 | F3 + Christian V | 153 / 153 |
| NO p2400 Speciedaler 1699-1745 | F4 + C6 | 23 / 23 |
| NO p1041 Rigsdaler 1746-1812 | F5 → F6 | 32 / 32 |
| NO p883 Rigsbankdaler 1813-1815 | NO under DK 1813-1814 only | 2 / 2 |
| SH-cluster `?country=schleswig_holstein` | Speciesbank-era SH 1787-1839 | 15 / 15 |

🔵 **In-scope subset clear (1 period):**

| Period | In-scope cached | Out-of-scope uncached |
|---|---:|---:|
| DK p220 Christian X 1912-1947 | 7 (1912-1914 window, all major denoms) | 23 (post-1914 OOS — Margrethe II era; no fetch needed) |

⚠️ **Real gap periods (4) — 150 TIDs total**:

| Period | Era | Cached / Total | Gap | Priority |
|---|---|---:|---:|:---:|
| DK p1147 Rigsdaler 1625-1699 | C4 late + F3 + Christian V | 201 / 211 | **10** | A — near-closure |
| DK p846 Rigsdaler 1750-1812 | F5 → C7 → F6 early | 20 / 54 | **34** | B — ongoing |
| **DK p1115 Rigsdaler 1699-1749** | **F4 → Christian VI** | **0 / 59** | **59** | **C — FULL UNTOUCHED** |
| **DK p647 Rigsbankdaler 1813-1854** | **Helstaten F6 → C8** | **1 / 48** | **47** | **D — NEAR-FULL UNTOUCHED** |

**ucoin gap details**:
- p1147: 4 known on page 1 (`96989`, `96438`, `96455`, `96986` — Skilling/Hvid Scheide); 6 more need page-2-5 re-enum to identify
- p846: 34 TIDs listed in audit-2 manifest (8/24/4/2-Skilling + 1-Mark + 8-Skilling Bornholm Speciesbank + 1/6-Rigsdaler family)
- p1115: 59 TIDs listed in audit-2 manifest (Frederik IV + Christian VI Reichsdukatenfuß-era — Speciedaler + Krone + Dukat + Skilling)
- p647: 47 TIDs listed in audit-2 manifest (Frederik VI Rigsbankdaler post-1813 reform + Christian VIII 1839-1848)
- All four gap manifests in `scripts/cache/ucoin/_BR_audit-2_2026-05-20.json` under `NEW_GAPS_DISCOVERED`

### Numista — 8 of 8 buckets enumerated (BO.6 v3 complete)

✅ **Verified clean (5 buckets, 671 NIDs):**

| Bucket | In-scope / Cached | Status |
|---|---:|---|
| DK p2 (1617-1671) | 200 / 200 | ✅ CLOSED (prior BO.5) |
| DK p3 (1671-1791) | 200 / 200 | ✅ CLOSED (prior BO.5) |
| DK p4 (1791-1914) | 124 / 104 (+20 Margrethe II false-pos OOS) | ✅ effectively CLOSED |
| SH cluster (5 issuers) | 67 / 67 | ✅ CLOSED batches A+B |
| DK p1 (1513-1617) | 139 / 125 | 🔵 14 left (last leg — batch K closes it) |

⏳ **Untouched (3 buckets, 471 NIDs — all NO):**

| Bucket | Era | Gap | Pages | URL filter |
|---|---|---:|---:|---|
| NO p2 (1513-1657) | C2 Oslo → F3 early | 193 | 1 | `?e=norvege&st=1-2-3-47-154-5-54&cat=y&p=2&q=200&s=c&o=y` |
| NO p3 (1657-1697) | F3 mid → C5 Kongsberg | 200 | 1 | `&p=3` |
| NO p4 (1697-1814) | C5 late → F6 1813 | 77 | 1 | `&p=4` (78 in-scope, only N#487340 cached) |

**Numista gap details**:
- DK p1: 14 NIDs listed in `_BO6_gaps_manifest_2026-05-19.json::denmark_gaps_by_page.p1.gap` (filter to uncached — 14 of 93 original)
- NO p2-p4 in-scope NID lists in `_BO6_audit_2026-05-20.json::in_scope_buckets.norway`
- Real Phase 2 Numista gap = **14 (DK p1) + 470 (NO p2-4) = 484 NIDs**

### Headline numbers post-audit-2

| Resource | Cache total | In-scope cached | Real gap | % done |
|---|---:|---:|---:|---:|
| **ucoin** | 660 TIDs (incl. 4 batch 25 + audit verification) | 656 / 807 | **150** | **81%** |
| **Numista** | 1058 NIDs | 697 / 1181 | **484** | **59%** |

### Recommended next-session work order

0. **Numista `year_list` backfill** (HIGH — added 2026-05-22 per user N#420401 audit; **WIRED into the routine 2026-06-05**) — 122 cache entries with multi-year ranges and NO `year_list` field. Each needs a Numista-page recheck to distinguish dash-form continuous range from comma-form discrete years. Queue in `docs/handoff_numista_year_list_reharvest.yml` (sorted by year gap descending). **Why it sat at 0/122 for two weeks despite «HIGH»:** the routine batches off HARVEST_ROUTINE.md + `_harvest_handoff.json::priority_override`, NOT this handoff prose (HARVEST_ROUTINE.md §0 «this file's logic supersedes the handoff for routine batching»); priority_override was never set; and the §2.1 picker only fetches *uncached* NIDs, so a re-read of already-cached NIDs was structurally unreachable. **Fix:** added as **§2.2 Priority 0 (STANDING)** — every cron run drains 5 from the queue (re-read + §2.3-B `year_list` encoding) before any BO.7 enumeration, until empty (~24 runs). After the queue closes, re-build the affected Numista seeds + re-merge so the discrete `year_list` reaches the rendered table. Removes the §4 «source years are immutable» violation that turned N#420401's «1496, 1502» into a continuous 1496-1502 range.
1. **ucoin p1147 closure** — 10 TIDs (4 known + re-enum p2-5 for remaining 6). Closes the DK Rigsdaler 1625-1699 bucket entirely.
2. **ucoin p846 closure** — 34 TIDs of Frederik V → Christian VII Skilling/Mark Convention era. Mostly 8-Skilling + 1/6-Rigsdaler variants.
3. **Numista DK p1 closure** — 14 NIDs to close pre-1617 DK Reichsdukatenfuß gold + post-1572 First Speciedaler.
4. **ucoin p1115 OPEN** — 59 NEW TIDs (FULL bucket; Frederik IV + Christian VI Reichsdukatenfuß-era).
5. **ucoin p647 OPEN** — 47 NEW TIDs (Frederik VI Helstaten + Christian VIII 1839-1848).
6. **Numista NO p2-p4** — 470 NIDs across 3 pages (largest single remaining bucket).

### Audit cache files (canonical references)

- `scripts/cache/ucoin/_BR_audit-2_2026-05-20.json` — full per-period enumeration verification, ALL gap TID lists
- `scripts/cache/numista/_BO6_audit_2026-05-20.json` — full per-bucket enumeration with in-scope NID lists for DK p1-p4 + NO p2-p4 + SH cluster
- `scripts/cache/numista/_BO6_gaps_manifest_2026-05-19.json` — original BO.6 v2 explicit gap lists (still valid for SH-cluster + DK p1)

### Technical lessons captured this session (in SOURCES.md §13)

- §13.2 ucoin: listing-page slug-collapse trap (`?text-content-filter` solution), `\t`-separated DOM table layout, comma decimal separator, `a.href` vs `a.getAttribute('href')` Cloudflare query-string blackout, `window.<global>` doesn't survive navigation
- §13.1 Numista: per-NID DOM = HTML `<table>` rows + `<th>`/`<td>` extraction beats innerText regex; listing-page year-regex false-positives (DK p4 = 20 Margrethe II false-pos caught)
- PB-10 (PLAYBOOKS): detached-HEAD recovery + parallel-session rebase collision recovery

### Source-quirks pinpointed this session

- ucoin systematic ruler-misattribution: 4 instances flagged in `_audit_context` for seed corrections (KM-260 «Christian IV» 1665 → actually F3; KM-308 1669 «C5» → actually F3; KM-324 ND-1670 «F3» → actually C5; KM-631 1778-1785 «C9» → actually C7; KM-598 1764 «C9» → actually F5)
- DK p846 «sidecar 86» was inflated — actual listing total = 54 (SH-Holstein cross-leak in §M-era sidecar)
- DK p4 «20-NID gap» = all Margrethe II post-1972 false-positives (year-regex matched historic refs in modern descriptions) — effectively CLOSED

---

## Pending verifications awaiting user input

1. **ucoin Composition harvest** (3 productive sessions 2026-05-13;
   paused on Cloudflare). Three sessions cumulative: 121 new sidecar
   entries (98 → 219), 178 metal-field updates. Rate-limit threshold
   characterised: ~50 cumulative requests per session-cookie at any
   pacing 2.5-20 s. Session 4 attempt hit **Cloudflare bot-
   protection challenge** (HTTP 403 + «Just a moment…») which cookie-
   clear cannot bypass. Resume conditions: wait ~24h for Cloudflare
   cooldown, or pass the challenge manually via normal browser
   navigation, or switch IP. ~490 uncached ucoin URLs remain. See
   TODO §M for full details.

2. **Seed audit snapshot** (post-case-9 cleanup) — 605 total Denmark
   Hede-seed entries; 195 auto-suppressed, 9 metal-mismatch guard, 6
   weight-mismatch guard, 1 year-mismatch guard, 394 wholly uncurated.
   Of the 16 guard-survivors, 3 appear to be **false-positive weight-
   guards triggered by outlier values in curated `weight_rough_g[]`
   lists** (km-25 [.49], km-128 [8.428], hede-47 [6.93]); 1 metal-
   mismatch (c5h128 → km-79 SH) may be a billon/silver labelling drift
   that should have caught the fineness-similarity escape hatch but
   didn't. Worth a focused turn before continuing per-case dedup.
   Audit script: `scripts/oneoff/audit_seed_survivors.py` (gitignored).

2. **Case 8 retrospective rigor check** (in flight) — user pushed back
   that case 8 (Hede 59 → KM-100 / KM-135) skipped the per-case «за /
   проти» discipline. I provided all KM-100 source links; awaiting
   user's verdict on whether the «Numista 109973 Bust type I =
   Hede 59A + 59B» mapping is acceptable on year-span-match alone,
   or needs direct obverse-design verification. Same question stands
   for KM-135 (Hede 59C 1646 — no Numista entry, sourced only from
   curator's prior «KM-DK# 135» note).

   ⇒ If user accepts: continue to case 9.
   ⇒ If not: revisit case 8, possibly partial rollback + verification.

2. **«Curated (legacy scalar)» legacy cleanup verification** — just
   purged 45 placeholder entries from `fineness` lists in denmark.yml
   per the new verified-wins-over-unverified rule. Build clean, render
   correct (sample-checked hede-44). User asked for verification
   before any push. ⇒ Awaiting «OK to push» or further checks.

## Helper queries (audit reproducibility)

```bash
# Current dedup-audit candidate file (stale after auto-suppress work
# — regenerable on demand from a sweep script if needed):
#   /tmp/dup_pairs_denmark.txt
# Generated against denmark.yml + seed in a previous session;
# entirely-pending NO-KM cases extracted via the same script.

# Quick «what's the next NO-KM case» check:
python3 -c "
import yaml, re, json
from pathlib import Path
loc = yaml.safe_load(Path('data/locations/denmark.yml').read_text())
seed = yaml.safe_load(Path('data/seed/hede/denmark.yml').read_text())
seed_by_id = {c['id']: c for c in seed.get('coins', [])}
# … (see audit script in chat history)
"
```

The full enumeration script is reproduced in the chat from this
session — search for «E1 NO-KM entirely-pending cases» if context
is preserved, or regenerate by walking the `dup_pairs_denmark.txt`
buckets.

## Quirks / known traps

* **ruamel.yaml round-trip on `denmark.yml`**: re-dumping the whole
  file via `yaml.dump(doc, file)` flattens the coin list indent from
  `  - id:` to `- id:` (loses 2-space). Use line-level surgery
  (regex / sed-style) for in-place edits instead. Caught and reverted
  during the 45-entry cleanup this session.
* **`scripts/cache/numista/*.json`**: cached entries reachable via
  pypdf-style local search; live API calls subject to user's
  per-session budget (per CLAUDE.md «Numista API budget» rule,
  May 2026 quota). The «cache → check first, ask before live
  fetch» pattern is enforced.
* **Push permission is per-turn**: «push» as a verb in any earlier
  turn does NOT carry to future turns. Always wait for an explicit
  per-turn push request.
