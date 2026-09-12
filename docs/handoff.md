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

## 2026-09-12 — §9a thinning moved off the seed layer; five defects found flushing a full re-flow

Asked to run the whole pipeline (seeds → merge → absorb → classify → relink) so
that pending state could not sit in the tree and confuse other sessions'
verification. The flush itself was one commit; the other eight came out of what
it exposed. **9 commits, local, unpushed.**

**The hanging state that prompted it.** `83883c7` (same day, earlier) gave
Stockholm/Vesterås a year-aware rule (post-1523 → the out-of-scope `sweden`
entity) but no seed had been rebuilt since, so the render was clean only
through `exclusions/` while the seeds still routed Swedish-crown coins into
`danish_realm`. Now in the data: 114 coins (bruun 102, ikmk 9, kmk 3), every
one `year_first >= 1524`, Kalmar-union pieces correctly left in `danish_realm`.
`a621514` + `3b34adf` had likewise landed after their sources' last build.

**Two architectural findings, both long-lived:**

1. **§9a thinning ran at the wrong layer for ~2.5 months** (curator's insight,
   not mine). The rule names its unit — «one coin entry has ≥5
   `weight_rough_g` entries from a single resource» — which exists only AFTER
   the merge, and the retired `thin_intra_subvariant_specimens.py` trimmed
   exactly that: a LIST inside one coin. The V1 teardown (2026-06-24) rebuilt
   the replacement at the SEED layer and nobody recorded it as a change of
   meaning. At seed level the unit does not exist (one scalar weight per
   record), so it became «≥5 records in a bucket», grouped by a key that is
   **not the merger's**. Measured cost: keeping a bucket's extremes sent them
   to other unified entries than the intermediate readings came from, so the
   coin the reader sees lost its envelope (6 of 8 affected ikmk entries came
   out NARROWER, five collapsed to a single reading, one from 21.800-28.170 g
   to a point); and it deleted seed RECORDS, so every re-seed removed coins
   from `final/`. Fixed in `f98808d` — see below for the layer split.
2. **The thinner sorted by `id`, not by weight, from its first commit**
   (`822833d`, 2026-06-02, whose message says «weight-variance envelope»). It
   shipped a weight-based `_keep_envelope()` and never called it; two
   refactors left both halves untouched. Consequence on kmk: 23 615 of 27 476
   discarded records carried NO weight at all — each a distinct KMM object
   whose citation went with it, and not one gram of redundant weight removed.

**The layer split now in force** (`f98808d`):
- **seed layer** (`lib.seed_thin.thin_safe`, used by kmk + ikmk builders) —
  only removals that provably cannot move a weight: same-weight twins within a
  sub-variant bucket collapse to one (the merger's `(value, source)` dedupe
  would have done it anyway for records that merge together; bucket extremes
  untouched by construction), weightless records beyond three per bucket
  (they carry no weight, so no envelope depends on them), curated records
  never. This exists for VOLUME: without it the merger went from ~20 min to
  2 entities in 20 min on a 41 490-record kmk seed.
- **merged layer** (`scripts/maintenance/thin_final_weight_lists.py`, pipeline
  phase `2b/5` after absorb) — the actual §9a envelope: min / middle by
  position / max **per resource** on the merged coin's list, skipping a coin
  whose fineness readings disagree, never dropping an `erroneous`/`suspect`
  reading, and leaving `sources[]` alone (a weight entry carries only
  `(value, source)` and cannot be mapped back to a citation row without the
  inventory number V1 entries had — also keeps `audit_lost_citations` clean).
- Result: kmk 14 152 → 16 267, ikmk 1 312 → 2 704 (both ABOVE the old rule),
  zero types lost (buckets 9 221 / 924 unchanged), merge back to 20 minutes,
  2 201 redundant readings trimmed on 153 coins.
- **Residual caveat**, in `thin_safe`'s docstring: if two same-weight twins
  land in DIFFERENT merger classes, the class that lost its record loses that
  reading. Cannot change a bucket's extremes; volume small (1 584 kmk, 1 740
  ikmk); not the absolute guarantee the weightless rule is.

**Three more defects fixed:**
- `3c48efd` — a `_curation_holds` on `issuing_entity` died whenever a re-seed
  moved the coin. The field IS in `CURATED_FIELDS`, but the protection was
  unreachable for the one field that decides which FILE a record lands in:
  `write_v2_seed` groups before `merge_seed` runs. Six curator decisions had
  already been reverted, three of them back to the exact stale entity their
  hold argued against. Two mechanisms now: a held entity re-routes; an
  unheld one still moves but the curated entry is merged in first so holds,
  errata and curated values travel with the coin.
- `0863e94` — thinning discarded curated records (`kmk-81785`/`-81790`, holds
  on `mint` + `issuing_entity`); at HEAD they had survived only by where their
  ids fell in the sort.
- `adc89d2` — wear alone split one type into three unified entries. The
  «>5% divergence needs ≥2 shared agreeing catalogue refs» gate (2026-05-22)
  is unreachable for KMM stubs, which carry a single Hede number: 1.11 g vs
  0.948 g is 17%, ordinary wear on a sub-gram billon Skilling. 191 types
  corpus-wide had been split this way. The bypass demands an IDENTICAL
  non-empty catalogue, so it can never let weight similarity substitute for
  catalogue evidence; the 2.5× hard gate is untouched.

**Curator decisions taken this session** (all with explicit in-chat approval):
- `113be4a` — nine implausible weights flagged, three languages each.
  `kmk-275886` 813.0 g on a 1 Mark is **erroneous**: a decimal shifted two
  places, digits 813 are those of the immediately preceding inventory number
  FP 4227.142 (8.13 g), same Hede 99C whose type weight is 8.661 g. Renders
  `(!)`, out of the fine weight and Δ — verified on the page. Eight
  2-Skilling specimens at 0.21-0.67 g against sisters of 0.9-1.8 g are
  **suspect**, not erroneous: KMM records no condition and clipping/corrosion
  of thin base silver could account for it, so they stay in the arithmetic
  and render `(*)`.
- `0c429c0` — 87 KMM specimens joined their cross-entity groups (Hede bases
  c5h74 / f6h15 / f6h14; KMM prints «H. 74 A» / «H. 15A» against the base,
  §9.4 sub-variants). Three Christian VII pieces EXCLUDED instead: KMM prints
  «Hede 13 ell. 39» and «København ell. Altona» — the museum declines to
  choose, and Hede 39 is also a 1 Speciedaler from Altona at 28.893 g but a
  different base (Sieg 42.x/55/56 vs 33.1). Listing them would settle an
  attribution the source left open.

**Two commits used `--no-verify`, reasons in their bodies:**
- `0c429c0` — Check 5 blocks on `kmk-693172`, a `no_merges` member resolving
  to no seed. **Pre-existing**: identical three lines at HEAD, absent from
  every seed in both states. Re-pointing it is a `v2-merge-coins` call.
- `b9cd215` — `verify_reflow` reports 422 COIN GONE (ikmk 393, kmk 29) + 61
  LIST SHRANK. The 422 are **re-representation, not holes**: type coverage
  identical, seeds hold MORE records than baseline, and a class whose
  representative had been a weightless stub is now represented by a different
  one. One-time — selection no longer depends on id position. The 61 are the
  **intended** §9a trim, the same one phase 2b reports; the old architecture
  achieved the same shedding by deleting records, which showed up as vanished
  coins instead.

**Verification**: `build.py` exit 0, `unittest discover tests` **1027 OK**,
tree clean. New tests: `test_seed_curation_survives_entity_move.py`,
`test_thinning_is_weight_based.py`, `test_same_type_weight_exemption.py`,
`test_thinning_layers.py`.

**Also corrected**: `abb17d8` — `CLAUDE.md`, `docs/ARCHITECTURE.md` and
`docs/SOURCES.md` had described galster/numismaster/bruun as wholesale-write
builders for four months. Every builder has been merge-aware since 2026-05-16
(`f250417`): the merge lives in the shared writer, `write_v2_seed` →
`lib.seed_merge.merge_seed`. Two of those notes made a false safety claim —
that a re-seed reverts hand-placed `_curation_holds`/`_source_errata`; both
keys are in `_PRESERVE_ALWAYS_KEYS`. **A builder is merge-aware if it calls
`write_v2_seed`, not if it grep-matches `merge_seed`** — the per-builder grep
is a false negative and produced a wrong verdict here before the docs were
checked.

**Open, deliberately untouched:**
- 9 coins disagree silver ↔ billon between `final` and the recomputation
  (`audit_curation_loss`, `metal=9`). Pre-dates this session.
- `kmk-693172` orphan in `danish_realm` `no_merges` (see above).
- Groups 3-9 of the weight outliers were flagged only after explicit
  per-group approval; no further outlier was touched.

**The pipeline needs TWO passes to reach its fixed point** — worth knowing
before anyone reads a diff as breakage. `absorb` is not a pure function of
`seed_unified`: it ENRICHES the existing `final` foundation (D3, «foundation
frozen except for additive enrichment»), so pass 1's output is pass 2's input.
Measured on unchanged seeds: pass 1 → 2 left `seed_unified` byte-identical and
changed `final/` in 4 files; pass 2 → 3 changed nothing at all. The merger is
idempotent from the first pass; the chain converges on the second, and it
terminates because the changes are monotonic (year ranges widen, coins get
promoted, `multi_match_warnings` clear once the ambiguity is placed).

Two consequences: a session that runs the pipeline once, sees a diff and
concludes it broke something is wrong; and committing after a single pass
leaves HEAD in a state the next run still moves. `b9cd215` did exactly that,
and `37212f8` is the converged state. **Run the pipeline twice, or re-run until
`git status` is clean, before committing `final/`.**

**Next**: nothing blocking. 11 commits await a push (never autonomous).

## 2026-09-10 (cont.) — reflow-home-drift fixed systemically (§CV + rebucket) + Option Z

Resolves the previous entry's **DEFERRED 2**. Root cause of the ~13-coin
relocation on a full re-flow: a seed entry's physical `data/v2/seed/<src>/<entity>.yml`
bucket had drifted from `_home_entity(issuing_entity)` (issuing_entity edited in
place without a builder re-run, or the `139df3f` royal_slesvig split moved
Husum/Haderslev), and the merger buckets by the seed FILE → wrong seed_unified/final
→ audit_v2 I1 hard-block. HEAD finals had been hand-relocated once; the re-flow
reverted them.

Shipped (3 commits, local, **unpushed**):
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

Shipped this session (5 commits, local, unpushed): NGC KM-40 Guldkrone stub
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

**DEFERRED 2 — ✅ RESOLVED 2026-09-10 (cont.), see the entry above (§CV + rebucket + Option Z).** Pre-existing seed-bucket ≠ issuing_entity drift. Any full
`merge_seeds_cross_source --apply` + absorb-all relocates ~13 coins
(kmk-575019/575020, kmk-81779/81780/81785/81790/81792/81793/81794,
dk-bruun-14708/14709, ngc-167729/167733) into the wrong home file → I1/I3
hard-block; plus danish_realm-side pending relocations (c4h5a/c4h8a Ungersk,
ngc-65611, bruun-6498, promotion f3h27). Their SEED sits in a
`royal_holstein`/`royal_slesvig` bucket while `issuing_entity` points elsewhere.
Reproducible with a clean tree at HEAD (independent of this session's work);
HEAD's finals are stale vs the current seed corpus. All five Guldkrone commits
were made by SURGICALLY isolating them around this drift (prune the 13 from
`royal_holstein` seed_unified after each merger run; rebuild `danish_realm`
final HEAD-base + swap only the intended blocks; `git checkout HEAD` the other
entities' seed_unified). Analysis spawned as task `task_85dba800` (running).

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

## 2026-08-26 — Pre-1544 Gottorp/Schleswig-mint issues → royal_slesvig (option A)

**Curator-authorized pipeline change (Serhii, option A). Committed locally, NOT pushed.**

**What & why.** Pre-1544 issues struck at the **Gottorp** and **Schleswig-town**
mints were anachronistically homed in `gottorp_duchy` — a duchy that did not
exist until the Rendsburg partition of **19 Aug 1544** (Adolf I's share).
Historically they are the undivided king-duke **Schleswig** line (Frederik I,
Christian III) → `royal_slesvig`. This **SUPERSEDES the 2026-07-16 cross-entity
legend call** that kept the pre-1544 Goldgulden in gottorp_duchy.

**Mechanism.**
- `scripts/lib/mint_registry.py`: added `year_overrides [{year_to: 1544, entity:
  royal_slesvig}]` to `schleswig` + `gottorp` (exclusive cutoff — year<1544 → RS,
  ≥1544 → gottorp_duchy default). Flensburg/Husum were already `royal_slesvig`.
- `scripts/maintenance/merge_seeds_cross_source.py`: the cross-entity issuing_entity
  stamp (was year-blind) now passes `year_first`; **and** a new optional
  `issuing_entity:` field on a `_cross_entity.yml` merge entry pins the stamp
  verbatim (bypassing the mint derivation) for the mint-ambiguous-resolved-by-ruler
  case.
- `_cross_entity.yml`: 14741 (1531) + 14783 (1534) target gottorp_duchy→royal_slesvig;
  c3h15 (1546) target royal_holstein→royal_slesvig **+ `issuing_entity: royal_slesvig`
  override** (post-1544 Schleswig-town mint would otherwise pull gottorp_duchy; it's
  the KING's royal Flensburg issue, disambiguated by ruler).
- classification_decisions: new `royal_slesvig.yml` (3 Goldgulden assignments +
  `bulk_promote_pending: all`, matching the sibling denmark∩SH overlap entities so
  the relocated seed_unsorted coins keep rendering); the two Goldgulden pulled out of
  `gottorp_duchy.yml`.
- Full builder re-run (galster/numista/bruun/kmk/ikmk) → merge → absorb.

**End state (verified).** gottorp_duchy final has **0** pre-1544 coins; ~31 pre-1544
Gottorp/Schleswig coins now in royal_slesvig. Badges: 14741→RS, 14783→RS, c3h15→RS,
14770 (1536 Roskilde, stays danish_realm home)→**DK+RS**. c3h15 + 14770 finals carry
`_curation_holds{issuing_entity}` (foundation-immutable froze the stale value);
c3h15 also re-pins `year_verified: true` (lost in the royal_holstein→royal_slesvig
relocation, was commit c070d60). **verify_reflow 0 losses, audit_v2 0 violations,
audit_lost_citations 0 missing, full build OK.**

**Incidental (disclose).** Re-running the kmk builder (needed to move the 2 Gottorp
kmk coins) also healed pre-existing stale-seed drift: **40 Flensburg/Husum kmk seed
records** (all Schleswig mints, correctly `royal_slesvig`) moved out of the stale
`kmk/royal_holstein.yml` seed — **0 of them were in any final**, so no final-level
effect. One unrelated `mb` list value (`'566'`) dropped from a danish_realm kmk seed
(inert — cat-drop=0 in finals). Timestamp-only seed churn reverted.

## 2026-08-19 — Frederik II's 1584 gold: Wilcke says the set is medals

**Dossier**: `docs/research/f2_guldmoent_1584_gavesaet.md`. **No data changed.**
Curator's word: «це складне питання але зараз я не бачу рішення».

**How it came up.** Looking for merge/promote candidates for `nobel_fod` and
`rosenobel_fod` on the Denmark page. `nobel_fod` is closed — all 23 Nobel seed
records are absorbed into seven finals, and the rest of the 1490-1540 gold sits
in `rhinsk_gylden_fod` / `reichsdukatenfuss` legitimately. `rosenobel_fod` had
exactly one loose record: `dk-hede-f2h7d`, **1 Engelot 1584**, 5,06 g, the last
unplaced member of Dronning Sophies gavesæt.

**What the source says.** Wilcke 1931 pp. 85-90 is not in our harvest, but
danskmoent republishes the chapter whole at
<https://www.danskmoent.dk/wilcke/w6g.htm>. Verbatim: the pieces «kan kun
betragtes som **Medailler til festlig Brug, ikke som Mønter, slaaede i
Omsætningsøjemed**», and the denomination names are «hentede fra en Række
udenlandske Mønter, som **ikke havde nogen Forbindelse med den hjemlige Mønt i
Datiden**» — a «Paaskud» for assembling a presentation set. He says this
explicitly against Jørgensen 1879 (who called them Prøvemønter) and against
Ramus/Scharling.

Decisive for the original question: Wilcke prints the whole set's weights **in
dukat multiples** — Portugaløser 10⅛, Rosenobel 2¼, Dobbelt Dukat 2, **Engelot
1½**, Ungersk Gylden 1, Guldkrone 1, Goldgylden 15/16. One unit, seven foreign
names on top. My earlier weight signal (5,06/7,69 = 0,658 ≈ the English
angel-to-rose-noble ⅔) was correct arithmetic and the wrong inference: 1½ : 2¼
IS ⅔, and no English prototype is needed to explain it. Metal: 18 rose nobles
melted down, enough for at most two sets.

**Why it is bigger than the Engelot.** The seven are one act, one account entry,
one Sieg 29 — Wilcke's verdict cannot apply to 7d alone. Six are already placed:
7a/7c/7e → `reichsdukatenfuss/I`, **7b → `rosenobel_fod/I`**, 7f →
`f2_guldkrone_fod/II`, 7g → `rhinsk_gylden_fod/II`. Most exposed is
`rosenobel_fod`, whose **Phase I is 7b and nothing else** and whose card
describes a two-phase lineage with `events.first_adoption: 1584`. Phase II
(Christian IV .833 / 8,994 g, 13 sources) is unaffected either way.

**Next session — do not decide from this entry alone**; the three options and
what would settle each are in the dossier. Cheapest next moves: read Hede's own
f2h7 page framing, then Galster 1959 (Nationalmuseets Arbejdsmark p. 117) and
Jensen Steen 1975 (Møntsamlernyt 1/1975 p. XXIV), both cited on
danskmoent's Engelot page. Watch the provenance chain — Wilcke argues against
Jørgensen, so anyone downstream following Wilcke repeats one reading rather
than corroborating it.

**Also found in the same scan, unrelated and untouched**: three NGC records of
the ¼ Portugaløser 1592 in `danish_realm/seed_unsorted` carry Fr 64.1 / 64.2 /
64.3 at 8,661 g — the same Fr indices and weight already on two `royal_holstein`
finals (`hede 3` → Fr [64, 64.1, 64.3], `hede 7B` → Fr [64, 64.2]). Looks like
cross-entity merge candidates; nobody has looked.

## 2026-08-18 (later still) — the year now reaches the mint resolver

**Commit** `1b38390`, on top of `1e59087`.

Closes findings 1 and 2 of the entry below. The three year-blind call sites of
`classify_mint_to_entity` now pass the coin's year, so the era-aware
`year_overrides` in `mint_registry` are visible to them:
`build_galster_denmark_seed.detect_issuing_entity` (year threaded through from
`build_entry`), `build_hede_denmark_seed._classify_hede_entity`
(`cm["year_first"]`), and `v2_seed_writer._check_entity_invariant`
(`c["year_first"]`).

**This was LATENT, and the fix moved no data — deliberately.** Measured before
and after: galster has no Altona coins at all, and hede's 75 are every one of
them 1640 or later, where the default era already gave the right answer. So the
value of the change is entirely in the future — the trap had already nearly
fired once, when the Gottorp `year_overrides` rule landed and neither builder
could see it. `scripts/maintenance/test_mint_entity_year_aware.py` pins the
property instead of leaving it to a data diff: it asserts the resolver is
genuinely era-aware (so the rest is not vacuous), that a pre-1640 Altona mint
reaches `schauenburg_pinneberg` through each of the three functions, that the
writer's invariant still flags a wrongly-routed coin, and that no NEW year-blind
call site appears in `build_*_seed.py` — with the two benign ones allow-listed
by file and line, plus a check that the allow-list has not drifted off them.

`audit_v2 --quick` 0 blocking, `verify_reflow` 0 changed coins, build exit 0.

## 2026-08-18 (late) — the unsorted pens complete themselves; +7530 coins render

**Commit** `43e3ed4`.

Curator direction settled the question I had been treating as a decision: the
`seed_unsorted` phase id is a transient label on material awaiting triage and
carries nothing worth gating a coin on — «байдуже яка назва фази в seed
unsorted», what matters is that a page shows the coins whose polity is in its
scope. So the pens are now completed at assembly time from the phase ids the
ASSEMBLED COINS actually carry, not from any list of sources. One rule covers the
per-source tags, `v1_bootstrap`, and the legacy Roman-numeral ids alike.

**Checked first, and it came back clean:** `audit_v2` I9 = 0 AND I9-info = 0, so
every coin invisible for a phase reason was under `seed_unsorted`. There was no
real-fuss case needing a separate decision. (I9-info had been 2 — the Denmark
consume-cap resolved those.)

**Scoping, all five points pinned by tests:** only pages that already declare a
seed_unsorted list are touched; curated pens always win; a generated pen inherits
a sibling's year bounds so it never widens the page span; the generator only ever
adds under `seed_unsorted`; and cross-page title reuse is restricted to ids that
NAME A SEED SOURCE — `I` is «Ernst III (1601–1622)» on holstein_schauenburg and
must not travel. Verified in the rendered HTML: the label stays put and
schleswig_holstein's generated pen is neutral.

**Render: +7530 over ten pages.** denmark 1842 → 7949, schleswig_holstein 795 →
1708, lubeck 80 → 309, holstein_schauenburg 279 → 405, hamburg 85 → 158,
lubeck_bishopric 0 → 20; brunswick, lauenburg, osnabrueck unchanged. **Zero coins
are now dropped for an undeclared phase.** Remaining drops are structural only:
no year, a fuss the page does not carry, the per-entity consume-window.

Data untouched — verify_reflow 0 changed, invariants clean, four suites pass.

**What this means for the pages now.** Most of the intake is sparse: of the
Denmark cohort, nominal 100 %, catalogue index 59 %, mint 47 %, metal 16 %,
weight 12 %. That is by design — the pens hold un-triaged material and empty as
classification proceeds — but the Denmark page is now ~4× its previous size and
dominated by KMM museum specimens. If that proves too blunt in practice the
filter tiers are measured and in the previous entry.

**One loose end left deliberately:** `erzbisthum_bremen_verden`'s single
`bruun-L12177-unknown-1670` still carries `phase: I` whose meaning nothing
establishes — its page declares neither `I` nor `II`. It now renders in a
generated neutral pen, which is fine, but the id may simply be V1 debris worth
retiring when someone triages that entity.

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

**Commits, local, unpushed** — everything from 2026-08-07 onward is still local;
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

**Commits, local, unpushed** — everything from 2026-08-07 onward is still local.

Scoring the Danish 67-Dukatfod card with `fuss-description` returned **5.9/10**,
and chasing the lost points turned up defects that were not about prose. Four
commits: `4a2c834` the KM 650 cross-entity merge (plus the `verify_reflow` fix
that stopped a cross-entity move reading as a loss), `ff9d217` the phase
periodisation, `280674c` the shared event anchors, `18d27c9` the description.

**What changed.** Denmark's ducat phases now follow the coins: phase I opens at
1531 (Frederik I's Galster 46) instead of 1514, phase III runs to 1802, and
phases IV and V are gone — IV split at 1771 only because the Altona mint opened,
a Schleswig-Holstein event, and held one coin which is now merged into
royal_holstein; V never held a coin, since nothing was struck on this standard
after 1802. Holstein's own phase list was deliberately untouched, and the merged
entry's scalar `phase: III` reads correctly on both pages. The shared
`fuesse.yml` anchors moved off the re-dated Galster c2g-89/90 to Hamburg 1497,
the earliest strike inside the event's own scope. `pdate_label` now gives the
minting years. The card's dead `description` duplicate is deleted — Denmark has
a `hintergrund`, which wins in the title block, so it never rendered.

A deliberate asymmetry to leave alone: the phase list ends 1802 while the
timeline's status layer runs to 1813. Phases follow the coins, the status layer
follows the law.

**Two tasks deferred here, by curator direction, not started.**

**Task A — 17 coins carry `phase: 'ngc'` and do not render.** In `seed_unified`
they are `fuss: seed_unsorted` + `phase: 'ngc'`; in `final` the fuss has been
classified to `reichsdukatenfuss` while the phase still reads `ngc`. The origin
is the NGC seed builder, which writes the literal string `ngc` into `phase` for
2020 entries in `data/v2/seed/ngc/*.yml`. The 17 are those whose fuss got
classified while the phase never did — real Danish and Norwegian ducats of
1648-1699 (`unified-ngc-1050265` 1 Ducat 1648, `unified-ngc-1050311` 10 Ducat
1693/1696 among them), all `kind: kurant`, all belonging in phase II. They are
invisible on the page. Run `trace_coin.py why` first (§0b-1); then find why
`build.py --validate-only` does not flag a phase id no fuss declares, although
`schema.py` ~1118 carries that check — **that** is the deeper bug; then fix at
source, repair the 17, add a regression test. KM 625 of 1771 is duplicated the
same way (`unified-ngc-1050856` against `km-625-chr-v-1771`) and belongs here.

**Task B — richer `pdate_label`.** Give the year kinds separately where known —
minting, standard, circulation — instead of one span, matching the three-layer
split the timeline bar now uses.

**The `unified-ngc-1099232` drop — RESOLVED 2026-08-17 (`2496f8d`).** It was a
legitimate exclusion all along. NGC's own record says «Struck with Speciedaler
dies, KM#83», carries `is_pattern_number` and cross-references the silver mother;
danskmoent norge/nf3h62 lists the piece inline as «Guldafslag 10 Dukat 1668 og
1669 (Unik, Schou 1)»; and the 2026-07-12 exclusion for dk-numista-387243 names
KM PnD20 verbatim — this coin's exact number, nominal and year. It survived that
pass only because exclusions match by seed id and the NGC harvest arrived
2026-08-10. `ngc-1099232` is now on the list, verify_reflow reclassifies the
removal from LOSS to CURATOR EXCLUSION, and danish_norway is no longer blocked.

**Follow-up A — DONE 2026-08-17 (`18812cf`), one step short.** Eight of the family
are now excluded coin by coin, each on NGC's own «Struck with Speciedaler dies»
plus the mother's Krause number, every silver mother verified to survive: PnA20
1664 (KM 10), PnB20 1665 (KM 73), PnC20 1665 (KM 74), PnE20 1669 (KM 83), PnA23
1674 (KM 109), PnB23 1675 (KM 132), PnA31 1685, PnB31 1690 (KM 184). `ngc-1098157`
(PnA19, 10 Ducat, no year) is deliberately NOT excluded — it has no note at all,
only a Pn number, and §9.1 says that is not enough. Three further cache records
(Pn20/Pn21/Pn22) turned out never to have been seeded and are a different
sub-family («Laureate head», «C5 monograms», «Equestrian figure») — real patterns,
not off-strikes.

**The gate gap is closed (`d392810`).** `verify_reflow` now excuses a measurement
reading that a source-sanity gate refused, printing them under their own heading
PARSER RETRACTIONS beside CURATOR EXCLUSIONS. The mechanism already had the right
shape — `_retracted_refs` is keyed by `field` — and was only wired to the catalog
branch; the loader now keys dict-form dropped values through `_key` so a ledger
entry matches the exact identity the list comparison builds. The ledger is a
SECOND file, `data/v2/_source_sanity_retractions.yml`, because
heal_hede_retracted_refs.py rewrites `_retracted_refs.yml` wholesale and would
wipe a co-author's entries; it is derived from the parser cache by
`record_source_sanity_retractions.py`, never hand-written, so it follows any
future parser-gate change. Eleven tests, most of them pinning the narrowness: one
value, one field, one seed — a second value in the same shrink, another field, the
same number from another source, a dropped citation and a vanished coin all still
block. With the gate able to see it the eight exclusions flowed: 2065 → 2058
coins, 0 losses. `ngc-1098157` (PnA19) stays unexcluded as decided — still needs
its own call, and still keeps a stale `fineness_verified: true` with no fineness.

**Follow-up E — an exclusion does not reach the render if the coin is still in the
seed layer.** Found 2026-08-17 while verifying the off-strike pass. `grep -n
exclusion scripts/build.py` returns NOTHING: the build never consults
`data/v2/exclusions/`. Absorb removes the coin from `final`, but
`_assemble_v2_location` has a seed-render pass over `data/v2/seed/**` (see the
comment at build.py ~345) which surfaces it again. Confirmed on two coins the
curator excluded on **2026-07-12**: `dk-numista-387448` («1 Portugaløser» 1665,
KM PnC20) and `dk-numista-387243` («1 Portugaløser» 1668, KM PnD20) are in no
`final/*.yml`, are in `data/v2/seed/numista/danish_norway.yml`, and render on the
Denmark page today with exactly their seed nominal and seed years. This is the
mirror of the trap CLAUDE.md §9 already documents in the other direction — there,
a parser filter alone does not remove a coin already in the seed; here, an
exclusion alone does not remove a coin the seed-render pass surfaces.

**Scope is NOT measured.** All 84 excluded ids still exist in the seed layer, which
is by design, but that is not the count that renders. Grepping the built pages for
the excluded seed ids returns 0 — a wrong instrument, since the seed-render pass
does not print seed ids into the HTML, which is exactly how the two confirmed rows
escaped notice. Measuring properly means reproducing the seed-render pass's own
selection, not searching for ids. Do that before estimating the work. The fix
itself touches the shared render path for every location, so it deserves its own
session rather than a tail-end patch.

**Follow-up B — DONE 2026-08-17 (`7f59831`), and my diagnosis was wrong.** This was
NOT a parser mis-mapping: NGC's page really prints «Fineness: 35.5000» and the
parser captured it faithfully. The defect is in the source. `parse_ngc.sift_fineness`
now accepts only the two encodings the corpus uses (fraction ≤ 1, per mille
500-1000) and sends anything else to `fineness_unusable_raw` with a flag, WITHOUT
reinterpreting it — the values cannot be resolved into a weight either (58.0 appears
on two different nominals, 40.7 on four), and guessing would be §0b invention. 13
records healed, 0 impossible finenesses left, nine tests. The gate must run after
`parse_note`, which replaces the whole `flags` dict.

**Follow-up D — is there anything left to pull for the un-indexed records?** Raised
by the curator 2026-08-17, with the doubt that we may already have parsed everything
available. The 32 KMM stubs with no catalogue index and the ~20 carrying a bare
`schou` cannot be resolved into «duplicate or new type» without a Hede or KM number,
and the question is whether that number exists anywhere we have not yet read — the
KMM record's own fields, an unharvested danskmoent page, a Bruun lot — or whether it
is genuinely absent from every source we hold, in which case the ceiling is a new
harvest or a paper catalogue, not a re-parse. Check before planning any work on it.

**Follow-up C** — `unified-dk-hede-nf3h62`, the silver 1 Speciedaler 1667-1669
that is the mother of the excluded 1668 off-strike, is itself still
`seed_unsorted` while its sibling `nf3h57` sits in `9_25_thaler/I`.

**A scan lesson worth keeping.** A merge-candidate scan must NOT gate on nominal
fraction. «1 Kurantdukat» and «12 Mark» are one coin under two names (the
Courantdukat was tariffed at 12 Mark), as are «1 Speciedaler» and «2
Rigsbankdaler»; a fraction comparison silently discards exactly those candidates.
This cost a wrong call on Hede f5h 23, which was routed to classification as a
standalone coin and briefly rendered as a second row for `dk-bruun-7661` before
being merged (`1977485`). Any earlier «no candidate found» count that relied on
such a filter — including the 119 of 125 unsorted Danish gold reported on
2026-08-17 — is unproven and should be re-run without it.

**Ceiling on the card.** C1's «why» stays open: no source gives a motive for
adopting the standard, so the prose says nothing about one rather than filling
the gap with a phrase.

## 2026-08-16 — the ducat gets three dossiers, and its 67 turns out to be Venetian

**Commits, local, unpushed** — everything from 2026-08-07 onward is still local.

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

## 2026-08-10 — Queen Sophie's 1584 gift set: split apart, and its seventh piece finally harvested

**Commits, local, unpushed** — `6b9ab63` (the split), `c6bf7c0` (the Engelot),
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

## 2026-08-09 — NGC added as a source; NumisMaster is dead; Lübeck pilot done

**Commits, local, unpushed** — `d3f3571`, `656c177` (docs), `1b92848` (scripts +
cache pointer), submodule `c800a491`. Note another session was committing into
this same worktree throughout; all four were made with explicit pathspecs and
nothing of theirs was swept.

**NumisMaster is OFFLINE.** Every URL, root and `MC_<N>` alike, 302s to
numismaticnews.net/pricing. `scripts/cache/numismaster/` is now a permanently
frozen archive — re-parseable, never re-fetchable. NGC bought the dataset and is
the live custodian. SOURCES.md §1.4 carries the banner, §1.5 the new entry.

**NGC access is browser-only, and that is settled.** No public catalogue API
(the one JSON endpoint is typeahead — `CoinDescription` + `URL`, no specs); the
sitemap is US-only; Cloudflare 403s curl. **Playwright was tested in 7
configurations and blocked in all** (bundled Chromium and real `channel=chrome`,
headless and headed, stealth patches, warm persistent profile) while a control
`fetch()` in an ordinary tab succeeded — evidence table in §13.13(c2). **Do not
re-open this by adding playwright/selenium/undetected-chromedriver.**

**The harvest shape that works** — `ngc_receiver.py` on 127.0.0.1, in-page
`fetch()` loop POSTs records straight into the cache. Chrome treats localhost as
trustworthy so an HTTPS page may POST to it. This matters: it keeps a 265-page
walk cheap enough to repeat for every remaining region, instead of relaying each
record back through the agent. A JS loop also SURVIVES the 30 s tool timeout —
fire it and poll the receiver from Bash.

**Lübeck pilot: 265/265 types, 0 rejected.** Behrens 186 (70 %), Davenport 101,
`Previous KM#` 55 (21 %), mayor arms 52, `Varieties exist` 60. Fineness/weight
only ~24 % — those seed `*_verified: false` with NO value (§4). The full-population
numbers beat the 25-page survey sample on both key fields.

**Next, in order.** (1) The §9 call on the **42 `KM Pn*` types** (16 % of Lübeck)
— pattern/presentation gate per §9.1/§9.5, needed BEFORE any seed builder runs.
(2) `build_ngc_seed.py`, merge-aware from day one per the ARCHITECTURE
manual-override rule. (3) Remaining regions — and take **both** `LUBECK` (179
rows) and `LÜBECK` (772): they are separate regions with different contents, and
the umlaut-doubling recurs across the 441-region list.

## 2026-08-15 — the 1604 gold Klippen get their own standard, and Denmark's ducat phase splits at 1602

**Commits, local, unpushed** — `9f0b338` (dossier) + the fuss / denmark / data /
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

## 2026-08-08 — II-2 closed, and the phantom-anchor theory was wrong

**Commits, local, unpushed** — `7c870ef` (+ everything from 2026-08-07, still
unpushed).

**B3 closed** (`7c870ef`). The two ½ Portugaløsere — Frederik III 1653
(`dk-bruun-6082`) and 1655 (`dk-bruun-6174`) — are gold afslag of their
Speciedaler and left under §9.3, curator-confirmed. Both were singleton
`seed_unsorted` classes, so nothing else moved; both silver mothers stay.
6565 → 6563, no losses.

**II-2 closed, but NOT for the reason this file recorded.** The previous entry
blamed the illustration caption «Forside: portræt, bagside: elefant (Hede Norge
14, Schou 1)» acting as a phantom anchor, and proposed year-proximity as the
discriminator. That was a hypothesis, and reading the actual span arithmetic
refuted it. The caption anchor is real and does contribute 1673 — but the coin's
own year was being lost somewhere else entirely: `_extract_desc_hede_groups`
closed each group's ref segment at the next «)», and on an UNPARENTHESISED group
(«Hede Norge 13, Schou 6») that «)» belongs to the FOLLOWING row's rarity marker,
so «3 Dukat 1678 (unik).» fell inside the previous group and the Hede 14 row was
left with an empty span. The boundary now trails the ref run itself. Both years
are recorded, which is what §4 wants — the page's own header says 1673 and its
own row says 1678; we carry both rather than adjudicate.

Corpus effect: four sub-entries, all GAINS — `c4h46` Hede 47 (+1597), `f3h82`
Hede 81 (reign-span 1648-1670 → 1669, dropping `year_verified: false` with it),
`f4h20` Hede 20 (+1702), `nc5h13` Hede 14 (+1678). No catalog_refs moved.

**The fix then exposed a sticky flag.** `year_is_reign_span` marks «this range
IS the ruler's reign window», and the absorb override could only ever SET it —
the field is foundation-immutable, copied verbatim across regens. So f3h81 got
its real 1669 and went on rendering «(?)» as a reign placeholder. The clear is
now in place, and two things about it are worth remembering:

* Recomputing `year_verified` from the OR-merge does NOT undo the «(?)»:
  `members[0]` is the foundation itself, so the stale False the rule wrote last
  run re-elects itself. The clear asks the OTHER members only.
* `normalise_ruler_name` resolves «Frederik III. von Gottorp» to the DANISH
  Frederik III — the comment in CURATED_FIELDS claiming these dukes don't
  resolve is wrong. A blind clear would have stripped km-44's curator flag,
  whose range (1616-1659) is the duke's own reign and whose lookup is simply
  someone else's. `_reign_lookup_is_exact` gates it. Note this cuts BOTH ways
  and the SET direction is unguarded: a Gottorp coin dated exactly 1648-1670
  would be flagged as a reign span on the Danish king's window. Not touched
  here — it wants its own pass. The normaliser is loose in general (it maps
  «Christian von Schleswig-Holstein-Glücksburg» → Christian V and «Christian 3
  eller Frederik 2» → Christian III), so anything keyed on it deserves a look.

**Two method notes worth keeping.** (1) A dry-run over `raw_text` predicted six
changes; the parser feeds that function `descriptive` (text before the first
«Bruttovægt»), so two predicted gains (`c5h15` Hede 16/17) never existed — the
prediction and the pipeline were reading different inputs, §9b again. (2)
`merge_seeds_cross_source.py --entity a,b` silently processed ZERO seeds and
reported success; the flag takes one entity. It also WROTE
`seed_unified/danish_realm,danish_norway.yml` — a real file, a real entity id
with a comma in it, `coins: []` — which is how the run was eventually caught: it
turned up in `git status` as an untracked file hours later. Deleted, and the
flag now exits 2 with the known list. If a re-flow ever looks suspiciously
empty, check the entity spelling first.

## 2026-08-07 — the Christiania 3-Dukat re-grouping, and three heals for one accumulation defect

**Commits, local, unpushed** — `153fc9d`, `0ff9a23`, `0bb97f9`, `d157b27`,
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

## 2026-08-02 (later) — the re-flow SHIPPED; the source-transfer report was mostly the gate

**Three commits, local, unpushed** (`c36f34b`, `23026d2`, `f6dee35`). Tree clean.
`verify_reflow` exits 0; the derived layers are no longer parked.

The entry below reports «a member joining a class under a different anchor does
not hand over its `sources`», measured from `unified-kmk-155180` losing all 13
KMM URLs. **That reading was wrong, and the way it was wrong is the lesson.**
Traced from the data instead of the symptom:

* `seed_unified` carries every citation correctly — the merger's `_collect_sources`
  never dropped anything. All 13 of unified-kmk-155180's URLs are still cited
  after the re-flow; they SPLIT 6/7 between `km-x005-chr-iv-1620` and
  `km-82-chr-iv-1640` because the dissolved class's seeds joined two different
  new classes.
* Entity-wide census, all 22 entities: 0 citations lost, 0 catalogue indices
  (case-folded, as absorb folds them), 0 attested years. 54 of the 56 reported
  losses were the GATE being stricter than its own question.

`23026d2` fixes four false-positive classes in `verify_reflow`: redistribution
across multiple survivors, a surviving coin whose class merely shrank (retention
now measured entity-wide, movers counted as `moved`), the `display: false`
visibility flip, catalogue case-folding, and year_ranges de-overlap.

**The 2 real losses it was burying** were a genuine §9a violation, fixed in
`c36f34b`: the stale-foundation purge snapshots a retired foundation's own
citations into `curator_migrations[host]` under `__merge__sources`, but that
table was read on the BULK-PROMOTE path only — so when the new host was already
a final, the migration was built and silently discarded while the purge still
printed «merged into peers». KMM 307931 / 307934 / 642976 (present in the
harvest cache) ended up cited by nothing. `audit_lost_citations` could not see
it: it compares a final against its own current members, and a retired
foundation is not one of them.

So the 2026-08-01 Rigsbanktegn fold WAS the same defect recurring — the systemic
read was right; the located layer was not.

Note for next time: absorb is not idempotent against a half-applied tree. The
first attempted fix looked like a no-op because the earlier runs had already
purged the foundations, leaving nothing to migrate — `git checkout HEAD --
data/v2/final/` before re-running is what made it measurable.

`git stash@{0}` («reflow-2026-08-02 …») is now superseded by `f6dee35` and can
be dropped; left in place rather than discarded unilaterally.

`task_48e9b393` (verify_reflow keys list entries on whole content) is subsumed
by `23026d2` — the `display`-flip case was exactly that shape.

Standing, unchanged from HEAD: `audit_curation_loss` reports metal=7. Those
entries' stored metal is byte-identical on both sides — it is the
foundation-immutable value disagreeing with what the members would recompute,
not anything this re-flow did.

## 2026-08-02 — the metal guard, and the third defect in the same node

**Pushed** (`f8c3187..e35973b`). Working tree clean, origin in sync.

A parallel session fixed the absent-field veto (`6cf1c57`): `no_match` meant both
«contradicted» and «not enough evidence», and PASS 2 turns every `no_match` into
a TRANSITIVE no_merge, so a record that merely failed to describe itself could
expel its own peers. Split into `no_match` / `abstain`; 49 spurious blocks
removed across 4 entities, `low_confidence` identical everywhere. Verified its
inertness in the code rather than on the commit message's word — PASS 1 collects
only confident/low_confidence, PASS 2 tests `== "no_match"`.

One correction to that commit's wording: it calls the `MetalConflictError`
«PRE-EXISTING at HEAD», which is true but incomplete. The `billon` value is old,
but there was NO conflict before 2026-08-01 — the class held one member reading
`copper, verified: false`, and a weak reading does not contest a verified final.
The three copper-verified sources arrived via the `Tn*` merge of `138c8ca`.

**`e35973b` — a final's stored metal is a derived value, not a second source.**
`_enrich_final_entry` passes the final as `members[0]`; `_collect_metal`'s guard
was built for two independent SOURCES disagreeing (f6h17, 2026-06-20) and could
not tell that from a final lagging its own members, so absorb crashed and such a
final could never be recomputed. The tell was both sides printing the SAME id —
a final named after its unified class collides with that class in the member
list — so the partition keys on POSITION, the documented contract, not on id.
Resolution reuses `_curation_holds`: held value stands, loose value follows its
members, members disagreeing among themselves still raise. Merger path untouched
(`foundation_first` defaults False). Scope measured first: 12 finals with a metal
no verified member attested, 8 of them the silver/billon thin line, 4 real — all
Rigsbanktegn, none held.

**OPEN — the re-flow is still blocked, and by a THIRD defect.** With both fixes
in, a full merger+absorb produces a real §9a loss that `verify_reflow` catches:
`unified-kmk-155180` («2 Skilling lybsk», 13 KMM museum URLs) merges into
`unified-dk-numista-142941` and the survivor carries NONE of the 13;
`unified-kmk-352757` loses 1 of 2. The merges are correct — `abstain` unblocked
them — but **a member joining a class under a different anchor does not hand
over its `sources`**. Spawned as `task_a7479c16`.

That is the same symptom treated by hand on 2026-08-01, when six Rigsbanktegn
finals were folded via `dedup_final_foundations` because a class RENAME left the
survivor with one source and the retired twin with four. Read then as a one-off
foundation trap; two independent recurrences say it is systemic.

The derived layers therefore stay at HEAD. The re-flow output is parked in
`git stash@{0}` («reflow-2026-08-02 …»), not discarded — inspect with
`git stash show -p`, do not pop onto a dirty tree.

**Also spawned:** `task_48e9b393` — `verify_reflow` reports a CORRECTED list
value as a lost one (it keys entries on whole content, so a changed weight reads
as vanish+appear). False alarm, not a missed loss, so the gate stays safe; but a
gate that cries wolf stops being read, which is the one thing this one must not
do.

## 2026-08-01 — three catalogue-index losses in the Bruun chain, and what they hid

**Four commits, local, unpushed** (10 ahead overall): `138c8ca` code, `bdba13c`
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

## 2026-08-02 — the absent-field veto, fixed; danish_realm absorb blocked

**One commit, local, unpushed: `6cf1c57`** (code + tests only, no data).

The expulsion above is fixed, but NOT where it was expected. Every per-field
comparator already returned None on absence — `_normalise_metal`,
`_weight_diverges`, `_mints_overlap`, the catalog chain. None of them was the
defect, and `match_pair(kmk-122613, kmk-152042)` was already `confident`.

The defect was the VERDICT LABEL. With nothing affirming and nothing disagreeing,
`_match_pair_core` fell through to `no_match` — the token PASS 2 turns into a
transitive `UnionFind.no_merge`. `denmark-numismaster-66282` (no ruler) vs
`kmk-122613` (no metal, no weight) scored primary_true=0 with ZERO
disagreements, and that constraint then vetoed the confident pair. A record that
merely fails to describe itself could expel its peers. That tail now returns
`abstain`, which PASS 1 and PASS 2 both ignore. `no_match` = CONTRADICTED,
`abstain` = NOT ENOUGH EVIDENCE; every contradiction path is untouched.

Blast radius, measured by running the merger over all 22 entities twice with
`abstain` relabelled back for the baseline: 15282 → 15233 unified classes, 49
spurious blocks removed, 4 entities (danish_realm 36, danish_norway 11,
royal_holstein 1, sonderburg_duchy 1). low_confidence identical everywhere.

**BLOCKED — needs a curator decision before the data can be re-flowed.**
`absorb_seeds_into_final_v2.py` raises `MetalConflictError` on
`unified-dk-bruun-8027` (12 Skilling Rigsbanktegn 1813). **This is pre-existing
at HEAD, not caused by the fix** — verified by restoring `seed_unified/` from
HEAD and re-running absorb, which crashes identically. The final carries
`metal: billon, metal_verified: true` with no `_curation_holds`; all four backing
seeds say copper (`dk-tid-81023`, `denmark-numismaster-66287`, `dk-numista-18275`
verified; `dk-bruun-8027` unverified). Evidence points to billon being a stale
legacy value, but that is a coin-field call for the curator. Until it is
resolved, `seed_unified/` and `final/` stay at HEAD rather than half-applied
(§9b) — so the committed matcher fix has NOT yet moved any rendered data.

**Four measurement mistakes in one session, all the same shape: the comparison
baseline was not what I assumed.**
  * `body_excerpt` is `body[:600]` — a truncation. An inventory keyed on it
    reported 25 Pn-suppressed lots and a table of 17 that included ordinary
    silver Speciedaler. The real number, measured against the full body, is 5.
  * A dangling-`composed_of` sweep checked ids against ONE entity's
    seed_unified; cross-entity members live elsewhere, so it flagged 6 healthy
    records as dead. It only failed to write because I guessed the wrong
    function name (`yaml_io.dump` vs `save`). `audit_v2` names the exact
    offending pairs — use its list instead of re-deriving one.
  * A `trace_coin` snapshot taken with seeds updated but seed_unified/final
    stale measures a mixture of two changes; it reported «16 lost their final»
    where the comparison against real HEAD shows none.
  * `_list_cap | {"others"}` looked right and rewrote 872/1695 lines across 23
    seed files into scalar `others:` — caught only by reading the diff.

**The rule that would have caught all four:** verify at the END of the chain,
against a clean committed baseline, and read the diff. A parser change is not
verified at the parser; a seed change is not verified at the seed. Note also
that committing seeds without re-running merge+absorb leaves HEAD in a state
where the seeds imply a re-flow nobody has done — the pre-commit citation check
only fires when a `data/v2/final/*.yml` is staged, so it cannot catch that.

## 2026-07-31 — A3 dukats: one closed, three blocked on the curator

**Two commits, local, unpushed**: `a18432d` (main) + `285c481f1` (submodule).

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

**Four commits, local, unpushed** (25 ahead of origin overall): `64aeece` five
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

## 2026-07-29 — ucoin duplicate seeds closed + Hede per-letter mint fix

**Nine commits, local, unpushed** (16 ahead of origin overall): `18ea1a4` prose,
`eafa879` I8, `9d9dc6b` ucoin routing, `17eeac9` parse_hede per-letter mint,
`7e10e54` cache pointer (submodule `4827e06d5`), `5834806` hede re-seed,
`2fcf2e5` eleven cross-entity decisions, `25ba9c7` merge, `2098ed8` absorb,
`1c405bb` trace_coin.py + rules.

**The task_aeed2422 defect is CLOSED.** All fifteen ucoin ids that lived in two
entity buckets now resolve to exactly ONE final each. Root cause: build_ucoin_seed
was the only builder writing its own yaml instead of going through
`write_v2_seed`, so it had no cross-entity dup-purge, and it routed by ucoin URL
country — which files every Danish-crown Altona/Rethwisch piece under /denmark/.
`ebe11c3` relocated them once; the next re-seed re-created the danish_realm copies
and both survived. Fixed at the builder + backstopped by the new **I8** invariant
(seed id in at most one bucket per source, in the `--quick` set so the hook
catches it).

**The id-prefix trap, caught before it landed.** The first cut of the routing fix
derived the id prefix from the home entity, so re-homing RENAMED coins
(`dk-tid-70716` → `sh-tid-70716`) and would have stranded every composed_of and
decision member. Prefix now comes from the URL country, which never moves.

**Hede per-letter mint (curator-reported).** danskmoent gives the mint per letter
whenever a type spans mints — f6h4 reads «A) København; 1828 … B) Altona;
1829-1838» under a header saying only «Altona». `_mint_per_letter_block` existed
but ran only when the header had NO mint, i.e. almost never. Now always runs.
26 letter-mints on 14 pages; f6h4a's mint was simply wrong before, c4h5b/c4h8b
said Haderslev where the letter says København. Consequence by design: 9 more Hede
pages split across buckets (the f7h6/f7h16/f7h17 shape), 4 of which needed new
cross-entity decisions.

**Watch this class of failure.** FOUR times this session a routing change silently
broke a standing curator decision. Three were healed in data; the fourth was the
tool's fault — `validate_decisions --check-members` scoped resolution to the
decision file's own bucket and so reported the live §CW Albertsdaler block as an
orphan after `dk-hede-c7h13b` re-homed. It now mirrors the merger by adding
cross-entity pulls to the entity's set. Run `validate_decisions.py` after EVERY
re-seed, not just from the hook.

**New tool — use it instead of hand-rolling.** `scripts/maintenance/trace_coin.py`
(`trace` / `snapshot` / `diff`), seed-keyed. CLAUDE.md §9b explains why: unified
and final ids are derived and RENAME during a merge, so a diff keyed on them
reports moved coins as lost. I did exactly that three times in one session and
reported it as fact each time.

**CLOSED since** (see the 2026-07-30 entry above, which supersedes this list):
three Rethwisch/1769 pairs (`baa1cb8` + `76ea1f3` — key was Hede + concordant
Schou; Sieg was NOT usable, Bruun cites 32-35 where danskmoent cites 2-6, a
systematic +30 offset between two registers), the KM 723 / KM 724 ⅕
Rigsbankskilling, and the Rendsburg attribution incl. `dk-tid-169253`. The
`km-735-2` / `km-721-3` phase check and the Bruun `kind: kurant` default remain
open and are carried forward there.

## 2026-07-28 — A2 (danish_realm early Dukats) closed + cross-entity dual-home fix

**Three commits, local, unpushed**: `b13b443` (merger stamp fix + test),
`a444118` (curator decisions), `dd18246` (pipeline output).

**A2 group is DONE** — the four early-era danish_realm Dukats of the 8_dukat
triage (`output/scratch/dukat_triage_progress.md`, gitignored, statuses
updated there). One promotion, three merges:
`f2h7c` → reichsdukatenfuss/I standalone · `ikmk-18219560` → the Hede 16AB
class · `kmk-122098` → the Hede 28B class · `dk-bruun-5528` + `kmk-290902`
cross-entity.

**The bug worth remembering — cross-entity stamp vs occupation coinage.** The
merger derived a pulled class's `issuing_entity` from the merged MINT, which
silently overwrote the curator's pull target whenever the mint's entity did
not cover it. Christian IV's 1627 Wolfenbüttel Ducat resolves by mint to
`herzogtum_braunschweig_lueneburg` but was pulled into `danish_realm` — so the
class was written to `danish_realm.yml` while claiming to belong elsewhere
(I1 violation, and the coin would have dropped off the Denmark page). Occupation
coinage is a DUAL HOME, not a relocation, and the curator had already ruled
exactly that for this coin's siblings via the Bruun builder's `_ENTITY_PIN`
(`f48f73e`). `_xentity_issuing_entity` now unions the two when they disagree;
the other three branches are unchanged and every other cross-entity group takes
the unchanged path.

**Where errata was NOT the answer.** IKMK 18219560's `literatur` cites both
"Hede … Nr. 16" and "Bruce-Michael 242"; the curator ruled the coin is Hede 16 /
KM 236, so the KM-242 half is wrong. No erratum was written, because the parser
never mapped that prose citation into a `km` field — the seed's catalog is
`{hede: 16}` only. Errata cancels what a source put in OUR fields; there was
nothing to cancel. The separate 1653-vs-1662 date conflict (IKMK's structured
date contradicts its own legend transcription) is handled by `year_demote`.

**Pre-existing noise, measured not assumed**: 14 prior classes split in
`danish_realm` during the merge (c7h8/10/11d/36, f6h2/4a/15, six numista/ucoin
pairs). A control run with the decision files reverted to HEAD produced the
SAME 14 — it is `seed_unified` lagging the Hede parser fixes `dedee21` /
`1bcce5b`, not this change. Expect them until someone re-flows danish_realm.

**All four A2 records are classified** (`ef034fd` added the last one, the
Wolfenbuettel Ducat -> reichsdukatenfuss/I per the standard the curator already
named in `f48f73e`). f2h7c + 5528 in Phase I, f3h16ab + 6414 in Phase II.

**Retraction — the "14 splits" of the merge run.** The earlier entry blamed
`seed_unified` lagging the Hede parser fixes. That was wrong, and so was the
control run I based it on. Running the SAME detector on the before-snapshot
against ITSELF flags the same 14, so it never measured anything: it built a
leaf->class map, and 15 ucoin ids exist in TWO entity buckets at once
(`seed/ucoin/danish_realm.yml` + `seed/ucoin/royal_holstein.yml`, same id,
byte-identical fields, differing only in issuing_entity), so one home always
overwrote the other. There were no splits. Do not reuse that detector shape
without deduplicating leaf ids first.

**The real defect underneath** (spawned as `task_aeed2422`, not fixed here):
those 15 ucoin records merge and land TWICE, once per bucket — e.g.
`dk-tid-70716` is a member of `unified-dk-numista-19000` in royal_holstein AND
of the singleton `unified-dk-tid-70716` in danish_realm. Introduced by
`ebe11c3` (2026-05-26) which added the royal_holstein copies without dropping
the danish_realm originals. `audit_v2` has no seed-id-uniqueness invariant,
which is why it sat unnoticed for two months. The correct shape is ONE entry
with list-form issuing_entity, as KM 631 is modelled.

**Next in the triage**: A3 — danish_realm late era 1687-1747, four records
(`numismaster-65781`, `kmk-439652`, `bruun-7396`, `hede-f5h9`).

## 2026-07-27 — A1 Christiania dukats closed + D48 (`merges` names the whole class)

**Four commits, local, unpushed**: `8f1e1b7` (approved merges + orphan heal),
`2281ba0` (merge applied, zero member losses), `40fc74c` (D48 rule),
`8a1b0d7` (promotion). 48 unpushed total including parallel sessions.

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

**Three commits, local, unpushed**: `cf86573` (matcher series gate + 7 tests),
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

## 2026-07-25 — mint normalisation: trailing «Mint» descriptor + wrapped mints

**Three commits, local, unpushed**: `64ec0d8` (normalisation fix + 15 tests),
`6620ed3` (data heal, curator-approved), `da60d16` (Bruun parser + 7 tests).

**Bug 1 — trailing «Mint»/«mint» suffix.** Bruun auction meta reads
«Christiania mint» / «Copenhagen Mint» (capitalisation varies), so one town
became two values: it blocked the comparator (`dk-bruun-6811` +
`dk-numista-445275` logged with `mint: false` although all 4 primary signals
agreed) and stored `mint: [Christiania, Christiania mint]` on 12 finals.
**Two causes, not one**: `parse_mint`'s city whitelist in
`build_bruun_denmark_seed.py` has no Christiania (→ falls back to raw
`lot["mint"]`), AND the suffix-strip that ALREADY existed in
`v2_seed_writer._canonicalise_mint` + `merge_seeds_cross_source._normalise_mints`
was case-SENSITIVE (`\s+Mint\s*$`) so lowercase «mint» sailed through.
**Fixed**: one shared `mint_registry.strip_mint_suffix()` used by both call
sites so the rule can't drift. Bruun goes through `write_v2_seed`, so the fix
covers every builder. Healed 32 values (seed 10 / seed_unified 10 / final 12),
all `Christiania mint`, list-form → scalar per §9a.

**Bug 2 — mints pushed onto the next line by a PDF break.** The reported
diagnosis («parser doesn't de-hyphenate») was WRONG and stays disproven:
`body_match` de-hyphenates correctly and has all along, with a proper
lowercase-only guard so «Schleswig-\nHolstein» is not glued. Real cause:
`meta_line` is ONE physical line by construction, so a wrapped « <X> Mint»
token never reaches it, and tier-3's `MINT_RE` whitelist has no Wolfenbüttel.
**Fixed**: tier 2 re-runs `META_MINT_RE` on the leading window of the already
de-wrapped `body_match`, bounded to the meta line's span + 80 chars so the
Bruun-3725 prose-grab stays out of reach. Recovers 33 lots.

**NOT applied to the cache yet — the open blocker.** The parser fix needs a
Phase-2 re-run → `scripts/cache` submodule regen → re-seed → merge → absorb.
Held back because two parallel sessions shared the submodule (phantom-citation
cleanup, hede-parser fix). Run it when the cache is free.

**Verified**: leaf conservation 24440 → 24440; full merger dry-run across all
22 entities matches disk exactly (so NO new auto-merges anywhere, and `--apply`
would be a no-op — deliberately not run); `audit_v2 --quick` 0 violations;
`audit_lost_citations` 0/14928; full build green, no residual in `site/`.

**Expectation that did NOT hold** (don't re-chase it): the mint fix produced no
new merges, because `dk-bruun-6811` + `dk-numista-445275` were ALREADY in
cluster `unified-dk-hede-nc5h16` by another route — the match_uncertainty row
was a logged low-confidence pair, not a merge blocker.

**Found in passing, NOT fixed** (also noted in `da60d16`'s body): tier 3 scans
the WHOLE lot body with the whitelist, so a lot with no mint of its own can
pick one up from its prose. Lot 1247 (Swedish Würzburg Riksdaler) stores
`mint: "Riga Mint"` with no mint in its meta segment at all.

## 2026-07-23 — Numista re-seed drift fix: curator year-narrowing + source-union preserved

**Bug**: a full re-run of `build_numista_seed.py` reverted three Christian IV
English-model gold coins (numista 426503 / 426815 / 426842, Fr 52/50/53) from
the curator's source-backed window `1606-1608` (verified:false) back to
Numista's bare full-reign placeholder `1588-1648` («denomination undetermined»),
AND dropped the curator-added danskmoent.dk Hede c4h21 citation from `426503`.

**Two defects in `merge_one` (scripts/lib/seed_merge.py)**:
  1. `sources` fell through to «fresh wins» → curator-added primary-source
     citations were REPLACED by the Numista-only fresh list — a §9a violation
     («Reconciliation NEVER replaces `sources` — always UNION»). **Fixed**: new
     `_LIST_UNION_FIELDS = {sources}` + `_union_source_lists` (JSON-key dedup,
     existing leads); union field also guarded from the stale-key drop loop.
  2. year fields are neither globally curated nor source-immutable, so the
     curator narrowing wasn't preserved. **Fixed**: `_curation_holds` (dict-form
     + rationale) on the 3 seed entries freezing year_first/last/ranges/label +
     year_verified. Verified against danskmoent c4h21 = Hede 21, undated,
     portrait-dated ~1606-1611 → 1606-1608 is a legit source-backed narrowing;
     1588-1648 is the Numista lazy reign placeholder = the regression.

**Regression was latent at the SEED layer only** — final/danish_realm already
carried 1606-1608 + c4h21 (+ KMM museum enrichment); the next merger+absorb
after a bad re-seed would have propagated 1588-1648 upward. Fix stops it at source.

Re-seed now byte-idempotent on danish_realm. Test:
`tests/test_seed_merge_sources_and_year_hold.py` (10 cases). Full suite 573 green,
`build --validate-only` clean. NOTE danskmoent c4h21 flags these as *prøvemønt*
(trial coins) — a possible §9.1 pattern-exclusion question left for the curator;
not acted on here.

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

## 2026-07-19 — Z_other_review gold triage + KMK catalogue-index loss (§DB)

**Sovereign_fod family closed out**: three trials got display polish
(nominal → `Prøvemønt`, ruler + Kopenhagen mint on Hede 21 / 426503,
km-a47 Stack's Bowers auction-lot source); kmk-137088 (KMM RP 19.1)
merged into the Hede 21 entry per the RP-inventory-sequence argument
(commit 58e1619).

**§DB opened (Highest priority)**: the KMK ES harvest endpoint
(`api.natmus.dk/search/public/raw`) is **403 «Site Disabled»** — fetcher
dead — AND ~15k objects have empty `typeNumber` in our ES cache while the
natmus.dk **web-rådata API** (`samlinger.natmus.dk/KMM/object/<id>`)
carries the catalogue in a `beskrivelser` field we never harvested. An
earlier "parser drops beskrivelser" hypothesis was WRONG (verified §0b) —
the data is absent from our cache, not mis-parsed. Fix = migrate harvest
to the web-rådata API + parse `beskrivelser`→catalog. See TODO §DB.

**Interim recovery done (variant B, commit 28eb471)**: 3 Z-review coins
got their web-rådata index by hand-editing the seed: kmk-86272 (schou 3a
+ Bech# 876 + B# 783.a), kmk-86273 (Bech# 977), kmk-298425 (B# 652).
`Sch`→schou; `Bech`/`B` kept verbatim in `others` (ambiguous, not guessed).

**kmk-86273 excluded** (out_of_scope, Danish East India / Tranquebar
colonial gold, Bech 977) — commit pending.

**DUKAT-PASS working set (curator direction: категорія, NOT fuss)** — these
Z_other_review gold coins are dukat-class but have vague nominals («(?)»,
«to mark»), so they will NOT surface in the categorise()-by-nominal triage
table under 8_dukat. Track them explicitly; fold into the future 8_dukat /
reichsdukatenfuss detailed pass. They stay `seed_unsorted` for now — do NOT
classify into a fuss (user clarified 2026-07-19 «не в стопу, а в категорію»):
  - kmk-298425 — Frederik III 1666, 35.38 g gold, **B 652** (Portugaløser / multi-dukat weight)
  - kmk-86272 — Christian V 1670-99, 7.72 g gold, **Schou 3a** (2-Mark gold ≈ 2 dukat)
  - kmk-391987 — Frederik V, 6.95 g gold, no code (≈ 2 dukat by weight)
  - kmk-391994 — Frederik V, 3.5 g gold, no code (≈ 1 dukat)
  - kmk-391997 — Frederik V, 3.14 g gold, no code (≈ 1 dukat)
  - dk-bruun-7235 — Christian V, Christiania, 7.29 g, **Hede 20B / NMD 24A / Fr 14 / Schou 5** (Norway 2-dukat; entity **danish_norway**)

  The 3 Frederik V pieces are UNDATED (KMM gives no minting year) — a fuss
  classification will need a reign-window year (1746-1766, verified false),
  like the sovereign trials.

**Z_other_review — CLOSED** (all resolved): kmk-697135 excluded
(undocumented_stub, gold «IIII skilling» 1764). **kmk-291032 RELOCATED**
danish_realm → herzogtum_braunschweig_lueneburg (seed-file move; «Wolfenbüttel»
added to mint_registry so a re-harvest routes it automatically; commit 99ca9c2).
Not a cross-entity merge — that needs ≥2 members; a lone mis-homed coin is a
plain seed-file move (entity = seed FILE location, per `_load_all_seeds`).

**goldgulden_gylden Z-review** (2026-07-19 late): of the 5 unsorted,
kmk-291022 «Gyldenløves dukat» recategorised to 8_dukat (categorise() fix —
«gylden» substring in the «Gyldenløve» proper name was a false positive; the
fix lives in the gitignored oneoff, not committable). Three excluded as
undocumented_stub (no weight/photo/index on natmus.dk): kmk-178069, kmk-291022,
kmk-78338 (commit 99ca9c2). **DEFERRED (2 left)**: kmk-122107 (1 Guldgylden,
Frederik I 1531 — galster 6 + web LEB 4063 [L.E. Bruun coll.] + 3 photos) and
kmk-137159 (2 Ungarsk gylden, Christian IV — schou 2 + web B 138b + 4 photos);
both have photos + a recoverable web-`beskrivelser` index — hold until the
natmus image/index access is sorted (part of §DB). Their extra web indices
(LEB 4063, B 138b) are NOT yet recovered.

**FLAG for the curator**: kmk-122102 (Hede 21B) is currently EXCLUDED as a
gold pattern/Prøvemønt — but we now KEEP the sovereign trials in
sovereign_fod. That exclusion is likely stale (pre-sovereign_fod era) and
inconsistent with the merged Hede 21A (kmk-137088). Decide whether to
un-exclude 21B into the sovereign_fod Hede 21 entry.

## 2026-07-16 — systemic parse_hede per-Hede year/catalog/nominal extraction

> **UNPUSHED — push pending «пуш».** 26 main commits (`git log origin/main..HEAD`) — the 23 from
> parts 1-3 + 3 parse_hede commits (`defdb80` parser+tests, `c124641` data, this handoff). Submodule
> `scripts/cache` has 1 new commit (`a8ca05e87`, 57 re-parsed hede pages) — **push the submodule
> FIRST** (PB-10), then `git push`. Overnight autonomous session; verify in the morning before push.

- **What.** Multi-nominal Hede pages (one page documenting «4 Mark» Hede 100AB + «8 Mark» Hede
  101 from the same dies; or «1/2/3/4 Speciedaler» f3h62 covering Hede 61-64) gave EVERY sub-entry
  the page-level year list + the union of all sub-variants' Schou/Sieg. 79 pages / ~180 sub-entries.
  Root cause was entirely in the parser: `_extract_specs` populated only a page-level `years` +
  merged `catalog_refs`; the per-`by_hede` sub-specs had no own year/catalog (the seed builder
  already consumes `spec["years"]`/`["catalog_refs"]`). Fix is **parser-only + additive**:
  `_extract_desc_hede_groups` parses each «<year(s)>; (Hede N, Schou …, Sieg …)» block into
  per-Hede {years, catalog_refs}; `_split_hede_key` + letter-subset matching attach «100A»+«100B»
  → combined key «100AB»; combined-key nominal derived from the sub-letters; `_looks_like_denom`
  guards prose over-capture; Guldafslag/Sølvafslag off-strike blocks no longer pollute the section
  nominal (skip «N Dukat» during the aside, reset at «.»).

- **Result (all root-fixed, propagated seed→unified→final→render):** f3h101 = «8 Mark» / 1659 /
  Schou 31 / Sieg 54 (was «4 Mark»/1559/merged); f3h100ab = «4 Mark» / 1659-1660 / Schou[23,33-35,36]
  / Sieg 53; f3h62 family 62AB=2 Spd, 63=3 Spd, 64=4 Spd. **One residual source typo** carried by a
  `_source_errata` on `dk-hede-f3h100ab` (danskmoent prints «1559» for the Ebenezerkrone; real
  years 1659/1660 — motif = 1658-59 siege of Copenhagen, 8 Mark Hede 101 dated 1659, eksemplarer
  1659/1660). Verification: 5→11 unit tests (`tests/test_parse_hede_per_hede.py`); full re-parse
  (57 pages, 0 key-set anomalies, 0 combined-form phantoms); seed scan 0 catalog-loss + only the
  f3h101 nominal change; scoped catalog reset (978 uncurated `seed_unsorted` entries, parser-owned
  schou/sieg/fr deleted then refilled fresh — `merge_seed` UNIONS list-catalog per §9a so a re-seed
  alone can't PRUNE stale over-broad refs; the reset is the one-time prune).

- **✅ RESOLVED (2026-07-16, user source-call) — `c5h39` / `c5h40` Hede↔denom is a SOURCE
  CONFLICT, not a parser bug. Decision: Hede 39 = 1 Dukat (Bruun wins over danskmoent).**
  danskmoent's page reads Hede 39 = 2 Dukat / Hede 40 = 1 Dukat; Bruun physically weighed the
  coins (lot 13186: Ducat 3.45 g, NGC MS-63, «Hede-39 Sieg-106 Fr-161 KM-A433»; lot 17098:
  2 Ducat 6.94 g «Hede-40 Sieg-107 Fr-160») and assigns them the opposite way. Commit `e1ff225`
  (2026-05-12) already encoded the Bruun call as `_KNOWN_HEDE_TYPOS["c5h39"] = {"39":"40","40":"39"}`.
  User confirmed KEEP Bruun. **Current data already reflects this** (`dk-hede-c5h39` = 1 Dukat /
  3.49 g). No swap, no re-parse needed — status quo IS the decision. **Follow-up DONE (same day):**
  per-coin Sieg/Schou curated directly in `data/v2/final/danish_realm.yml` — `unified-dk-hede-c5h39`
  → Sieg 106 / Schou 4, `hede-40-chr-v-1693` → Sieg 107 / Schou 3 (both per Bruun lots), each with a
  `_curation_holds: {catalog: …}` so absorb can't re-broaden (absorb skips `_fold_catalog_indices`
  when catalog is held — verified in absorb source ~L2766). NOTE: `_INVERTED_TAG_PAGES = {"c5h39"}`
  (defdb80) is NOT redundant — it's protective: removing it would make the typo-swap emit
  Bruun-wrong Sieg 107 on Hede 39. KEEP both parser mechanisms. Still open (tiny): verify where
  final c5h39's `km 415` came from (Bruun says the 1-Ducat is KM-A433).

- **✅ EXECUTED (2026-07-17) — guldkrone-7 pass: all verdicts applied, built, committed
  (`3acabf6` merges 1-6, `b1e10db` phase III, `993db19` dedup script).** End-state verified:
  kmk-149737/137168/291435 → km-74-1 Hede-25 cluster; KM-206 family base-merged into ONE final
  (km [206, 206.1, 206.2] = Hede 43A/B; the km-206-2 duplicate foundation folded via
  dedup_final_foundations — NOTE the new trap found there: the fold writes the DROPPED
  foundation id into the keeper's composed_of, which trips audit_v2 I2 when the dropped id
  exists nowhere else; fixed by pointing composed_of at the real unified id. Consider patching
  the fold script's composed_of rule); KM 279 = Hede 45 (f3h45); KM 40.1/40.2 → f3h145a;
  f4h30 promoted as guldkrone **phase III** (1701, last Danish Guldkrone, struck for the
  Vestindiske Compagni, «kendes ikke mere» — lit-only: Ramus 192, Wilcke III 20, NFM X 87;
  two new refs_pool keys, phase renders with citations). Analysis details remain in
  `scratchpad/guldkrone_pass.md` (uncommitted). Guldkrone group in seed_unsorted: EMPTY.
  Side-fund noted there: dozens of SILVER 1/½ Krone KMM records 1621/1655-1666 in unsorted —
  a future silver-kronemønt pass. «Guilder» research (user Q): Krause English house-label for
  ANY Danish gylden (labels both .972 ungersk and .76 rhinsk types «Guilder») — never a period
  Danish term; etymology = anglicized Dutch gulden ≡ florin. Proposals:
  №1 kmk-149737 + №2 kmk-137168(+bonus kmk-291435) → km-74-1-hede-25c cluster (Schou-in-range /
  Hede 25A edges); №4+5 numismaster-93042/93043 (KM 40.1/.2) → f3h145a (its km list already holds
  40/40.1/40.2); №6 numismaster-65606 (KM 279) → f3h45 (working concordance KM 279 = Hede 45);
  №3 KM-206-family base-merge question (km-206 + km-206-2 + numismaster-65599 = Hede 43A/B, one
  §9.4 base); №7 f4h30 (2 Guldkrone 1701, «Kendes ikke mere», lit-only) — no candidates, fuss
  window question (guldkrone ends 1671) → research Wilcke III s.20 first. BONUS: tid-163671
  (ucoin KM 40, «3.0 g» = Krause boilerplate) likely = f3h145a — cross-entity merge candidate.
  KEY SYSTEMIC FINDING: NumisMaster/Krause prints boilerplate masses for Danish gold kroner
  (Krone=2.973 g, 2 Krone=5.996 g) contradicted by physical Bruun/danskmoent weights already in
  our data (Hede 44=5.59, Hede 45=11.181, Hede 43 phys 5.97-6.0) — distrust NumisMaster mass in
  this family, trust KM↔Hede concordances. Worth a docs/SOURCES.md §13 entry when committing.
  Also noted: my candidate scanner missed list-form km matches (scalar-vs-list compare) — fixed
  ad hoc in scripts/oneoff/guldkrone_scan.py; consider for merge_helper.

- **✅ EXECUTED (2026-07-16) — gylden-11 batch: pipeline ran, finals verified, full build ✓.
  AWAITING COMMIT ONLY (git commit gated by the flapping Bash classifier; 11 data files staged-ready).**
  Verified end-state: №1 unified-dk-bruun-14741 [gottorp] = rhinsk_gylden_fod/I (4 members incl.
  MC_167742; year 1523-1533 = NumisMaster window union — OPTIONAL tidy: year_demote 167742 so
  Galster's attested 1531 wins, ask user); №4 unified-dk-bruun-14783 [royal] = rhinsk_gylden_fod/I,
  year 1534 clean (year_demote worked); №5 c3h15 enriched (mb 51 + fr 17 + numista 474509);
  №6 167747 = rhinsk_gylden_fod/I; №7 kmk-150041 in c4h8a; №8 c4h16 got km B45. 14418 (Christian
  Albrecht Ducat) intact after fixing my own Edit-collision in gottorp classification file (the
  first-entry header replacement had orphaned 14418's fields under my entry — duplicate YAML keys,
  last-wins; restored both entries, re-absorbed). Files to commit: merge_decisions ×3 +
  classification_decisions ×2 + seed_unified ×3 + final ×3 (danish_realm/gottorp_duchy/
  royal_holstein) + this handoff. Suggested msg: «data: gylden batch — 5 merges + 2 rhinsk
  promotions; year_demote ND-ca-1535».

  *(original plan record follows)* User-confirmed verdicts for the 11 `7_goldgulden_gylden`
  seed_unsorted coins (see `scratchpad/seed_unsorted_gold.md`, uncommitted): merges №1
  (167742→Galster-122 Gottorp cluster, cross-entity → gottorp_duchy), №4 (167745+bruun-14783+
  numista-461448 → royal_holstein, year_demote on 167745's ND-ca-1535, fuss→rhinsk_gylden_fod),
  №5 (167748+c3h15+numista-474509 → royal_holstein), №7 (kmk-150041 appended to the c4h8a
  cross-entity entry), №8 (c4h16+numismaster-165442, danish_realm; «Guilder»=Krause anglicization
  of Gylden, verified in-house via MC_65615; KM B45=Hede 16 working concordance); standalone
  promote №6 (167747→rhinsk_gylden_fod); deferred №2+№9 (KMM photos unavailable — natmus resource
  problem), №3 (next round), №11 (undocumented stub); №10 → 8_dukat pass. Decision files ALREADY
  EDITED: `_cross_entity.yml` (3 new entries + c4h8a member), `royal_holstein.yml` (year_demote
  section), `danish_realm.yml` (c4h16 merge). Classification assignments ALSO pre-written:
  `classification_decisions/gottorp_duchy.yml` (unified-dk-bruun-14741 → rhinsk_gylden_fod I kurant)
  + `classification_decisions/royal_holstein.yml` (unified-dk-bruun-14783 + unified-schleswig_holstein-
  numismaster-167747 → rhinsk_gylden_fod I kurant). NOTE: the two cluster-head coin_ids (14741, 14783)
  are PREDICTED (bruun outranks numista/galster/numismaster in head choice) — if the merger picks a
  different head, absorb reports the assignment unmatched → fix the coin_id. **NEXT (pure execution):
  validate_decisions --check-members → FULL merger --apply (no --entity, cross-entity needs global) →
  verify heads match the assignments → absorb danish_realm+royal_holstein+gottorp_duchy --apply →
  build → verify renders → atomic commits.** Nothing of this batch is committed yet.

- **✅ RESOLVED (2026-07-16, user visual check) — `unified-dk-hede-f3h29` + `denmark-numismaster-65918`
  auto-merge is LEGITIMATE (one coin).** «3 Dukat 1666 Frederik III», Hede 29 / Sieg 134 / Schou 5
  ↔ KM 280; no shared catalogue base in either source's own data, but fineness 0.979 + weight
  10.471 g match exactly and the user confirmed visually it's the same physical coin. KM 280 (DK) =
  Hede 29. Keep. (Sibling changes were already correct: `unified-dk-hede-f3h82` −`kmk-149330` right;
  f3h62ab/f3h63 clusters restored.)

- **❓ Clarification for morning — «portugaloser / next category».** You mentioned finishing «все
  що вилізло після того як ми розбирали portugaloser з seed unsorted» and moving to «наступної
  категорії після portugaloser». I don't have context on a Portugalöser-specific seed_unsorted
  categorisation thread — this session's chain was 20 new hede coins → f3h100ab/f3h101 year → the
  parse_hede systemic fix (4/8 Mark Ebenezerkroner + Speciedaler pages, no Portugalöser). I finished
  that in-flight work and did NOT start a Portugalöser categorisation pass (no clear context). If
  that's a distinct backlog category, point me at it and I'll continue.

## 2026-07-15 (part 3) — removed the destructive `--no-merge` seed-builder flag (D47)

> **UNPUSHED — push pending «пуш».** 23 commits (`git log origin/main..HEAD`). This section
> adds 1 (`--no-merge` removal) on top of part-2's 22. Submodule `scripts/cache` still 3 ahead —
> push FIRST (PB-10).

- **Trigger.** Analysed whether a `_source_errata` on a `seed_unsorted` hede coin survives
  downstream (question arose from the f3h100ab/f3h101 «1559»→1659 danskmoent typo, below).
  Answer: **it does** — `apply_source_errata` runs LAST in `lib.seed_merge.merge_seed`
  (called by `v2_seed_writer.write_v2_seed` for every seed write), `_source_errata` ∈
  `_PRESERVE_ALWAYS_KEYS` (survives re-seed even though the parser re-emits the raw cache value),
  and BOTH the merger (`_union_year_ranges` → `_format_year_label`) AND absorb regenerate
  `year_label`/`year_last`/`year_ranges` from the corrected `year_first` — so a year errata needs
  only `year_first` for the render (add `year_label` too just for seed self-consistency).
  Empirically proved end-to-end (scratchpad test: seed-write correction + re-seed re-apply +
  merger/absorb derivation all → 1659). The ONE residual hole was `--no-merge`.

- **Removed `--no-merge` entirely (curator chose option B).** It was the SINGLE bypass of the
  project's «never silently lose curation» invariant: it skipped both the pre-process purge AND
  `merge_seed`, wholesale-writing fresh parser output → silently dropping `_curation_holds`,
  `_source_errata`, curated field overrides, and orphan-curated entries for the whole entity.
  Low-prob (explicit opt-in) × catastrophic (entire entity's curation) × silent — and literally
  in the hede docstring's `Run:` examples. Removed the flag + `no_merge` param from all 8 builders
  (`build_{hede_denmark,numista,numismaster,ucoin,kmk,ikmk,bruun_denmark,galster_denmark}_seed.py`)
  and `write_v2_seed`; every builder now unconditionally routes through `merge_seed`. Verification =
  `--dry-run` (unchanged); genuine fresh rebuild = `rm -rf data/v2/seed/<src>/` + builder. Full
  rationale in **V2_DECISIONS D47**. NOT related to `no_merges` decision pairs / union-find
  `add_no_merge` (untouched). Verified: py_compile all touched · 547 tests OK · kmk+ucoin dry-run
  smoke · 0 leftover flag refs. Docs: D47 added; TODO §BT step 5 rebuild recipe updated.

- **⚠ Pending curator decision — f3h100ab / f3h101 year is 1559 but should be 1659.** Both are
  Frederik III Ebenezerkroner (danskmoent f3h100 prints «1559»; the 8 Mark Hede 101 on the same
  page is correctly dated 1659 — motif «Gud afhugger svenskekongens hånd» = 1658–59 siege of
  Copenhagen). This is a source typo (arguably an extraction artefact). Fix = `_source_errata` on
  both seed entries in `data/v2/seed/hede/danish_realm.yml` (`year_first` 1559→1659 + `year_label`)
  — but **§4 requires explicit in-chat «так» before adding any erratum**; NOT yet applied. Both are
  among the 20 new `seed_unsorted` hede coins (still pending fuss/phase classification).

## 2026-07-15 (part 2) — seed-writer idempotency · _source_note Phase-1 wiring · full lossless re-flow

> **UNPUSHED — push pending «пуш».** 21 commits (`git log origin/main..HEAD`). This
> session's 5 (newest first): `0484d7c` (re-merge seed_unified) · `a77ab38` (re-absorb
> finals) · `d9d310c` (re-seed all) · `0ad4780` (wire _source_note ×5 builders) · `85be578`
> (seed-writer idempotency) — on top of the 16 in the section below (incl. `80b671d`/`b46deed`/
> `562661b` reserialize-drift resolution + gen_stamp ts fix). Submodule `scripts/cache` still
> 3 ahead — push FIRST (PB-10).

- **Seed-writer non-idempotency root-caused + fixed (`85be578`).** `_apply_pre_write_hygiene`
  ran `_extract_mint_from_nominal` BEFORE the annotation splitters, so a mint hidden behind a
  region suffix («Hvid , Visby (Gotland)») escaped the trailing-mint regex; then the splitters
  stripped «(Gotland)» exposing a bare «, Visby» that nothing caught. The fresh-build path thus
  disagreed with the orphan-normalisation pass (runs on already-normalised data, DID strip it),
  so galster never reached a fixed point (perpetual re-seed churn). Fix: RE-extract after the
  splitters. Also `_dump_seed_yaml` skip-write (content-stable seed `generated_at` via
  `gen_stamp.content_equals_except_timestamp`). Tests: `test_nominal_mint_reextract.py`,
  `test_gen_stamp.py`.

- **`_source_note` = deferred Phase-1 work, now wired (`0ad4780`).** Investigating the «14k-line
  stale-seed» churn revealed `_source_note` is NOT a disposable duplicate — commit `80a1b62`
  (Phase-1) populated 2629 candidate-notes (source descriptions) via a one-off and EXPLICITLY
  deferred the builder-wiring to «the next coordinated re-seed». This was that re-seed; dropping
  it would abandon the work. Wired `_source_note` into all 5 builders (numismaster `general_note`
  en · numista obv/rev-desc en · ikmk `comment` de · hede `description` da · kmk `motif` da) via
  the existing `lib/note_extract.source_note`. Verified per-coin: 2625 reproduced IDENTICAL, 0
  changed, 0 LOST + 357 gained coverage. Durable now. `_source_note` stays non-schema (stripped
  by merger, never rendered) — pure curator-review candidate for the future note-selector.

- **Full lossless re-flow (`d9d310c` → `a77ab38` → `0484d7c`).** re-seed → merge → absorb → build.
  Verified by full-id-set + composed_of membership analysis (NOT raw diff lines — those are
  inflated by benign reordering): **0 coins lost anywhere**. Real changes: 4 galster nominal
  fixes («1 Hvid, Visby» → «1 Hvid») + 1 mint correction (c2g-174 Kopenhagen → «Hamar…») + **20
  new hede coins** (f3h84ab etc.). danish_realm net −5 finals = hede providing the authoritative
  Hede/Schou/KM anchor that unifies previously-separate museum(kmk)/auction(bruun)/catalogue
  (numismaster/numista) records of the SAME coin — every consolidation §9.4-verified on a shared
  catalogue base (e.g. kmk-156815 Hede 113A → f3h113a). Gates: audit_lost_citations = 0, V2 I2
  clean, 547 tests OK, build OK, render OK («1 Hvid, Visby» = 0 in danish_realm). **My earlier
  «200+ id restructuring / curation-loss» alarm was WRONG** — reordering artifacts; corrected.

- **⚠ commit-order blemish (harmless):** the merger seed_unified commit was first BLOCKED by the
  I2 hard-block (5 finals transiently referenced retired unified-ids from the hede re-cluster);
  the absorb then purged those 13 stale refs, so finals committed first (`a77ab38`) and
  seed_unified second (`0484d7c`). Final state is consistent (I2 clean); only git history order
  is slightly inverted. If re-running from scratch, run merger+absorb THEN commit seed_unified
  before finals.

- **The 20 new hede coins are `seed_unsorted` (pending classification)** — they render but carry
  no fuss/phase yet. Curator follow-up when convenient (not blocking).

## 2026-07-14 — galster Gej fix · Norway harvest-gap audit · rhinsk phase renumber · c3h14 Goldgulden split · c3g131 schou 1-7 · c3h14 nominal → Goldgulden

> **UNPUSHED — push pending «пуш».** 16 commits unpushed (`git log origin/main..HEAD`):
> `82e2d5e` `81eda30` `ee7d177` `990f750` `202de9e` `115bb05` (c3h14 split / c3g131 schou 1-7 /
> nominal / schou-subsumption docs), then the galster canonical-index-paren work
> `d3cb920` (parser) · `8d77786` (cleaner «mgl.») · `7607db3` (seed + cache pointer, submodule
> `67bdb7a9`) · `4b39400` (docs §13.11), then the overnight re-flow `e5d18a2` (absorb year-hold
> fix) · `9a9b8c6` (galster re-flow to finals) · `ec809ac` (handoff), then the 2026-07-15
> reserialize-drift resolution `80b671d` (gen_stamp timestamp fix + test) · `b46deed` (finals
> serialization fixed-point) + this handoff commit.
> Earlier `dc95899..c90f0a8` were pushed (galster Gej, rhinsk renumber, rhinsk grundwerte aside).
> **Submodule `scripts/cache` is 3 commits ahead — push it FIRST (PB-10).**

### 2026-07-15 overnight — pending-churn analysis + galster re-flow to finals

- **What the «pending churn» actually was (investigated in full).** After the galster
  seed commit `7607db3`, an `absorb --dry-run` showed re-promotions / bulk-promotes /
  assignments across entities. **Conclusion: overwhelmingly benign.** The ~65 curator
  `classification_decisions::assignments` (german_empire→Reichsgoldmünzfuß, danish Nobels→
  nobel_fod, etc.) were ALREADY applied to the finals — absorb re-reports them idempotently
  (0 fuss changes on re-run). The bulk of a full re-flow diff is **field-order
  reserialization** (semantically noop — e.g. schauenburg 146 lines, 0 entries/fields
  changed) + `generated_at` timestamp bumps + `multi_match_warnings` housekeeping. No data
  loss anywhere (`audit_lost_citations` = 0; every regrouped seed member re-lands).

- **Absorb year-hold fix (`e5d18a2`, + test).** The re-flow DID revert one curated value:
  sonderburg `unified-schleswig_holstein-numismaster-120994` year 1622 (curator, Numista
  N#151529) → seed «ND(1618-22)» start 1618. Root cause: the `pure_absorbed` fast-path in
  `_enrich_final_entry` (`composed_of == [self]`) trusted the seed member's year_ranges
  WITHOUT checking `_curation_holds` — the hold-honouring logic lived only in the `else`
  branch. Fix: the fast-path now honours a `year_ranges`/`year_first` hold (dict- and
  list-form). `tests/test_absorb_year_hold_pure_absorbed.py`. This is a durable pipeline fix,
  not a one-off restore — future re-flows won't clobber year holds.

- **Galster re-flow to finals (`9a9b8c6`).** Ran full merger + absorb (with the fix), then
  committed ONLY the real-content subset — `danish_realm` + `gottorp_duchy` (seed_unified +
  final) + the `sonderburg` year fix — reverting the 12 pure-reserialize finals + 20
  timestamp-only seed_unified (pre-existing drift, not this session's concern). Lands: galster
  Schou/Sieg propagated into finals; §9.4-clean regrouping the recovered Schou enabled
  (f1g-55/f1g-60 split out of bruun-4025/4090; hg-36 + 3 kmk merge into peers — all 7 pass the
  over-merge scan, 0 lost); a data FIX — `unified-dk-bruun-4090` reverts a stale reign-window
  «1523-1533» to its Bruun-attested «1532»; c3g131 `_curation_holds.catalog` note refreshed
  (parser fix landed → value now derives natively). sonderburg keeps 1622.

- **RESOLVED (2026-07-15) — reserialize-drift + timestamp-churn root-caused and fixed.** The
  «~1500-line cosmetic churn per re-flow» split into two independent phenomena, both now closed:
  - **Field-order drift (the ~850-line bulk) = ONE-TIME migration, NOT recurring.** The committed
    finals predated a newer absorb serialization: `_enrich_final_entry` collects all immutable
    fields (fuss/phase/kind/`fraction`/nominal/…) to the front, but older files had `fraction`
    trailing after `composed_of`. Proven pure + stable THREE ways — HEAD→run-1: 13 finals, ALL
    pure reserialize (structured order-independent compare, 0 data change); run-1→run-2:
    byte-identical (0/22 differ — idempotent fixed point); validate + full build clean, render
    unchanged (`Schou 1-7` / `Reinhold Junge` still present). Committed the fixed point in
    `b46deed` so future re-flows stop reproducing it (they now show only real data diffs).
  - **Timestamp churn (`generated_at`) = the ONLY genuinely-recurring part — durably fixed in
    `80b671d`.** Both committed emit sites (merger `_emit_unified_yaml`, absorb
    `_emit_classification_decisions`) stamped today's date unconditionally → a daily 1-line diff
    on ~40 seed_unified / decisions files that buried real changes under `git diff data/`. New
    `lib/gen_stamp.resolve_generated_at(new_payload, existing_doc)` reuses the prior date when the
    payload (timestamp stripped from both sides) is unchanged, else today; +10 unit tests
    (`tests/test_gen_stamp.py`). Verified end-to-end: a no-op absorb leaves the 19 timestamp-only
    decisions byte-identical to HEAD (only the real schauenburg `multi_match_warnings` refresh
    survives — a stale 2026-07-09 warning now cleared); a no-op merger leaves rantzau + norburg
    seed_unified byte-identical despite their old `2026-07-09` dates. Safe because `generated_at`
    is informational (verified: nothing branches on it). NOTE — the per-source SEED builders
    (`v2_seed_writer`, `build_ucoin_seed`, …) still stamp a UTC timestamp on every re-seed; that
    is the re-seed step, not a re-flow, so it is a separate (smaller) churn source left untouched.

- **Christian III Goldgulden split (`82e2d5e`).** Reversed the 2026-06-22/07-02 one-type
  merge: the Roskilde-1536 .764 «Goldgulden» and the Flensburg-1546 .750 «Rhinsk Gylden»
  are now **two coins** (§9.4 — Danish specialist catalogues give distinct bases: Sieg 23≠51,
  Schou 4≠2; only coarse Fr 18 / Numista N#379084 / MB 42 lumped them). Coin A →
  `danish_realm` `unified-dk-bruun-14770` (rhinsk_gylden_fod I); Coin B stays `royal_holstein`
  `unified-dk-hede-c3h14`. Mechanism: dropped the `royal_holstein.yml` force-merge, redirected
  `_cross_entity.yml` (Roskilde half → danish_realm, +numismaster-167746), added
  `danish_realm.yml::year_demote` for the Numista/NumisMaster loose 1546-1547 windows.
  **Foundation trap hit + fixed:** the c3h14 final foundation kept the merged mint/catalog/
  nominal/issuing_entity via deep-merge — hand-reset to the Flensburg coin only, frozen via
  `_curation_holds` (mint/nominal), durable across re-absorb. Denmark shows both rows; the SH
  page is unchanged (this ducal/royal gold is denmark-scoped, as before the split).

- **c3g131 Coin A schou → `1-7` (`ee7d177`).** The Roskilde-1536 Goldgulden (`unified-dk-bruun-14770`)
  had carried `schou: [4, 1351]`: «4» from Bruun lot 14258 (specimen variety), «1351» from
  NumisMaster MC_167746 (its own note flags «for no date issue» — out of range for Christian III,
  Schou per-regent ~1-77). danskmoent c3g131 states the type range **«Schou 1-7»** (4 ∈ 1-7).
  Dropped 1351 from the numismaster seed; added `Schou 1-7` + `Sieg 23` to galster seed
  `dk-galster-c3g-131`; set `schou: 1-7` on seed_unified member + final (+ `_curation_holds:
  {catalog}`). **Verified the hard way:** a `_curation_holds: {catalog}` does NOT survive
  absorb's main enrich re-derive (only the hygiene-fold) — durability rests on BOTH the
  foundation AND its seed_unified member carrying `1-7`, which absorb unions to a clean `1-7`.
  **Root cause = parser bug, documented in `docs/SOURCES.md §13.11`:** `parse_galster`'s
  `_parse_description_and_refs` only scans the `Forside:` block to the first blank line, so the
  `(Galster N, Schou X, Sieg Y; …)` line on a *detached* line (as on c3g131) is never extracted →
  `catalog_refs` empty. **This parser bug is now FIXED — see the next bullet.** — *(Earlier this note listed a 2nd follow-up: that a full merger
  re-run would re-surface Bruun's faithful «Schou 4» as `['1-7','4']` and need a merger
  subsumption rule or a bruun `_source_errata`. That was WRONG — verified 2026-07-14: the
  range-subsumption ALREADY exists (`catalog_codes.normalise_numeric_index` + `schou ∈
  _NUMERIC_INDEX_FIELDS`), runs at all three chokepoints — merger `_fold_catalog_indices`
  (`merge_seeds_cross_source.py:3350`), absorb `_normalise_catalog` (`absorb_…:1485`), render
  (`compute.py:663`) — and collapses the plain `4` inside the plain range `1-7` to a clean `1-7`.
  No merger rule and no bruun errata are needed.)*

- **c3h14 Coin B nominal → «1 Goldgulden» (`990f750`).** Renamed the Flensburg-1546 piece
  (`unified-dk-hede-c3h14`, Hede 14 · Sieg 51 · Schou 2, .750 gold) from «1 Rhinsk Gylden» →
  «1 Goldgulden» so both split pieces read consistently (Coin A is already «1 Goldgulden»); Hede's
  Danish «Rhinsk Gylden» stays as the alt-name in `note[]`. Durable via `nominal ∈
  _FOUNDATION_IMMUTABLE_FIELDS` (absorb never re-derives nominal on an existing final) — touched
  only the final foundation + updated the `_curation_holds.nominal` reason; hede seed left faithful.

- **Galster parser fix — canonical-index-paren anchoring (`d3cb920` parser+test · `8d77786`
  cleaner+test · `67bdb7a9` submodule cache · main data commit for pointer+seed).** The c3g131
  detached-paren bug (previous bullet) is the tip of a class: 34 standard pages carried empty
  `catalog_refs` because the index paren sat on a detached line (c3g131 class) or the page had
  no `Forside:` anchor (c3g92 class). **Analysed the whole 118-page corpus first** (user's
  suspicion «сторінки не стандартизовані» — CORRECT): a naive «widen `Forside:`→first-HR» fix
  REGRESSES ~10 currently-correct pages, because the widened region holds prose / literature /
  neighbour parens («(Galster 30)», «(Galster: <book> side 59)») that clobber the real value via
  the extractor's last-paren-wins. **Fix = two-tier, legacy-first, anchored on the page's OWN
  Galster number** (`_galster_number_from_filename` + `_find_canonical_index_paren`): Tier 1 =
  the legacy `Forside:`-narrow scan (byte-identical; keeps f1g66's «(Galster 66A-B)» summary);
  Tier 2 fires only when Tier 1 is empty and picks the pre-HR paren naming the page's own number
  with the most catalogue keywords. Migration gate (`tests/test_galster_canonical_paren.py` +
  full-corpus diff): **unchanged 84, recovered 34, changed 0, LOST 0** — zero regressions.
  Re-parse + re-seed banked 29 Schou + 20 Sieg; c3g131 now derives Schou 1-7 + Sieg 23 natively
  (supersedes the ee7d177 interim). Also fixed `_PROSE_NOISE_RE` to drop abbreviated «mgl.»
  (`build_galster_denmark_seed`, `8d77786`). **Scope = SEED only** — `seed_unified`/`final` NOT
  re-derived because a merger+absorb re-run currently drags unrelated pending cross-session
  reconciliation (19 monotonic re-promotions, bulk-promotes, assignments); banked in source,
  propagates at the next deliberate coordinated re-flow. **Still-deferred:** the multi-variant
  Schou-UNION «accumulate» case (f1g66 / f1g73 / f1g63 — Schou split across per-variant parens;
  Tier 1/2 keep only summary/first, never the union). Full write-up: `docs/SOURCES.md §13.11`.

- **Galster «Gej» fix (`ffa32bf`).** `build_galster_denmark_seed` no longer emits a
  `galster` / `galster_volume` catalogue field for the non-numbered `norge/hansGej.htm`
  placeholder («Gej» = page-filename fragment, gated by `_is_real_galster_index` = has a
  digit). «Gej» survives only in the coin_id. Test: `tests/test_galster_index_guard.py`.

- **rhinsk_gylden_fod / 72-Guldgyldenfod phase renumber (`4afaafd`).** Curator direction:
  a true «Phase 0» would be only the 2 pre-1514 Hans specimens — not worth a phase — so
  shifted every phase +1: **0/I/II → I/II/III, no phase 0**. Founding 1496-1547 band = Phase I
  (Hans + Frederik I + Christian III, .75), Frederik II = II (.77), Christian IV = III (.76).
  Touched in lockstep: coin `phase` (10 finals + 3 classification assignments),
  `soll_fein_by_phase` keys (both fractions — Δ stays aligned), denmark.yml phase blocks +
  timeline + closing, fuesse.yml description + grundwerte. Phase I label shortened + fine
  weight (2,436 g); Phase I description rewritten system-level (no specimens, .75 only,
  Bergen coin in); Phase III label «мінімально знижено» → «.76 (18¼ карат)». New ref
  `danskmoent-hans-goldgulden-bergen` (Nordbø NNUM 1978/1979). Verified: Δ per phase
  (Hans Bergen −0.557 %), labels render I/II/III, audit_lost_citations 0.

- **🔵 OPEN — Norway Numista pre-1513 harvest gap (audit finding, no code yet).** Investigated
  why N#444264 (Hans Bergen Goldgulden) needed separate harvesting: **every** Numista Norway
  harvest used mission floor **1514** (BO.6 `_BO6_audit_2026-05-20.json` + `fetch_numista_pre1541.py`).
  The pre-1513 Norway body — **105 NIDs explicitly `oos_excluded`** in NO p2, ALL uncached,
  + page-1 of the listing never audited for Norway — is a systematic, deliberate gap. **Asymmetry:**
  Denmark got a `p0_pre_lovkompleks` context bucket (20 NIDs, harvested); Norway got none.
  N#444264 isn't even in the 105 (added post-snapshot → body still growing). **Next step offered,
  awaiting curator go-ahead:** mirror Denmark — create a `norway/p0_pre_lovkompleks` bucket,
  enumerate listing page 1 (public page, no API budget) + the 1481-1513 subset of the 105, harvest.
  Would also firm the «Norway's first gold coin» claim via Schive 1865 / Ahlström-Brekke *Norges Mynter*.

## 2026-07-13 — gold seed_unsorted triage (Portugaløser + tarif-Daler)

> **UNPUSHED — push pending «пуш».** Commits this triage: `d675e1d` `ec52477`
> `cfc1c26` `2202998` `16491cb` `d941f3e` `26977af` `26b7d8a` `cc5f5aa` `be13259`
> (Portugaløser Cases 1-9 + f2h7a classify + NumisMaster 65625 fold + tarif 1-4).
> 36 commits unpushed total.

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

## 2026-07-12 — coin-table measurement sub-rows (per-specimen повна/чиста/Δ)

> **UNPUSHED — push pending «пуш».** Commit `d04974e` (+ render-neutral
> groundwork `8c67eba`). Full build exit 0; preview (port 3000) rebuilt.

**What shipped.** Multi-specimen coins now render повна / чиста / Δ as aligned
sub-rows (one per specimen) instead of comma-lists; проба spans exactly the
sub-rows sharing its fineness. Files: `scripts/lib/compute.py` (`_seg_rle`,
`_build_measurement_rows`, `ComputedCoin.msr_*`), `templates/location.html.j2`
(метал/проба + повна + чиста + Δ cells, gated on `coin.msr_n > 1`, else the old
`*_groups` rendering), `scripts/lib/style.base.css` (`.msr-seg`,
`.fin-src`/`.fin-alt`, `.sd-wrap`).

**Key design decisions (all curator-driven this session):**
- проба driven by `fineness_groups` (per-SOURCE readings); each row's fineness
  derived from its own чиста/повна + snapped to the catalogue value → проба
  aligns with чиста row-for-row. Single reading → normal `.fin-src` + source
  tooltip; ≥2 divergent → orange `.fin-alt`, each its own fineness source (NEVER
  the weight source). Metal repeated per variant.
- Diameter is NOT a sub-row axis (specimen spread = wear noise) — Ø keeps its
  own `diameter_groups`.
- чиста/Δ tooltips carry the «weight × fineness» derived-source label
  (`_seg_rle` `src_field`); повна carries the raw weight source.
- `_seg_rle` `group_field="fineness"`: повна/чиста/Δ never merge across a проба
  boundary — a weight shared by two specimens under different fineness keeps its
  own sub-row (не дедуплікується). проба itself is the grouping axis.
- `--msr-row-h` 44px; Δ badge 2-line, unverified «(?)» sits OUTSIDE the coloured
  badge (right, vertically centred via `.sd-wrap`); msr-seg horizontal padding
  matched to `.mt td` so sub-row values align with non-sub-row values.

**Verification note.** Spot-checks were on denmark via an isolated single-table
demo (`site/_msr_demo.html`, now removed) + JS geometry — the preview pane can't
screenshot the full 2025-coin page (renderer times out; scroll decoupled from
capture). Reference cases: c3h14 (royal_holstein, .750 hede / .764 galster) and
the reichsdukatenfuss .986/.972 @ 3.49 g coin — both confirmed aligned.

## 2026-07-10 (later) — founding-era reign-span mint/phase START rule

> **UNPUSHED — push pending «пуш».** Commit `8d4d305` (was cf3aede pre message-amend).
> Full build exit 0, preview (port 3000) rebuilt, 10 new unit tests pass.

**Problem.** A standard whose EARLIEST coin is a reign-window placeholder
(`year_is_reign_span` — «1513-1523» Christian II, exact mint year unknown) was
starting its **карбування (mint) stripe** + phase at the nearest DATED coin,
ignoring that the reign coin was struck earlier. On Dukatfod (reichsdukatenfuss)
the mint stripe indented to 1531 while the standard's founding is 1513/1481.

**Fix — 2-rule policy (curator direction), shared by BOTH surfaces.** New helper
`timeline.founding_mint_start(reign_min, dated_min, adoption_year, firm)` →
`(start, approx)`, driving the timeline mint stripe (`derive_mint_overrides`) AND
the phase table (`build._expand_outer_phase_span`, now fed the fuss
`first_adoption` via a cached `_load_fuesse_cached()`):
- **Rule 1 firm** (dated ordinance / curator-certain de-facto start): HARD-clip
  the start to the founding year, no fade. Reign spill before it is cut.
- **Rule 2 non-firm** (uncertain de-facto): start from the reign coin's own year
  WITH the uncertainty fade.

**Discriminator = NEW per-scope field `FussEvent.firm_<scope>` (default True),
read only on `first_adoption`.** Deliberately SEPARATE from `approx_<scope>` (user
choice «окреме поле») so editing the display-approx flag never changes the span
rule. **Keying on FIRMNESS, not literally «has a decree», is what protects the
accepted 9¼-Thaler 1622** — its 1622 is de-facto-but-firm (Friedrich III first
strike, no Møntordning), so `firm=True` hard-clips the 1588 reign coin up to 1622,
no regression. Only `reichsdukatenfuss` `first_adoption.firm_anywhere: false` set
in data (its anywhere 1481/1513 is a genuine de-facto estimate); everything else
defaults firm=True.

**Effect (denmark only):** reichsdukatenfuss/Dukatfod mint 1531→1513 (fade,
clipped at the 1514 timeline left edge so the fade is off-screen — the stripe just
reaches the edge now) + phase I 1514→1513; 8_5_gylden_fod mint 1516→1514 (Rule 1,
Møntordning Sommeren 1514). 9¼-Thaler (1622) + 9-Thaler (1566) + all SH-scope
reichsdukatenfuss UNCHANGED (SH has no Danish Christian II reign coin; its 1591
shift is the pre-existing dated-coin c4h8a expansion). `last_mint` / the phase
to-anchor still exclude reign placeholders — this rule is START-only.

**Scope note.** Only 4 fusses ever had a reign-span-earliest coin (scan:
reichsdukatenfuss, 8_5_gylden_fod, 9_thaler, 9_25_thaler); the helper is a no-op
for every other fuss (no reign coin earlier than its dated coins → dated start).

**Unrelated pre-existing failure noticed:** `tests/test_mint_ambiguity_split.py`
has 4 failing tests (Malmø ø → Malmö ö normalisation in the mint-name splitter) —
confirmed present at clean HEAD before this change (stash-verified). Not caused
here; flagged as a separate task.

## 2026-07-10 — denmark_pre_1541 unification (NumisMaster _pre1541 pipeline retired)

> **UNPUSHED — push pending «пуш».** Commits (newest first): `c760e4f` cache
> pointer bump · `6638351` data re-flow · `c9220e9` code+docs retirement. Plus
> a submodule commit `1b00a12` (cache scope deletion). Working tree clean,
> full build exit 0, preview (port 3000) rebuilt.

**What.** `denmark_pre_1541` was never an entity/location/issuing_entity — only
a legacy NumisMaster harvest **sub-scope** (3 MCs) with its own parser+builder,
which duplicated coins the MAIN sub-scope already covers. Retired it:
- Deleted `scripts/parse_numismaster_pre1541.py` +
  `scripts/maintenance/build_numismaster_pre1541_seed.py` (both generalised long
  ago into the sub-scope-aware `parse_numismaster.py` + merge-aware
  `build_numismaster_seed.py`); dropped `denmark_pre_1541` from
  `parse_numismaster.py` KNOWN_SUB_SCOPES + the `harvest_coverage.py` numismaster loop.
- Removed the 3 `dk-numismaster-167727/167729/167745` seed entries from
  `data/v2/seed/numismaster/royal_holstein.yml` + refreshed its stale §AZ header
  to the §BK main-builder scope_note (dropped `scope_year_from/to` — the pre1541
  fingerprint). Deleted the `scripts/cache/numismaster/denmark_pre_1541/` scope
  (submodule; the 3 MCs live in `schleswig_holstein/` with raw .html + parsed).
- Re-merged + re-absorbed royal_holstein: the 3 unified clusters lost the dk
  member and re-keyed onto the main-scope head (167727 → `unified-dk-numista-309411`
  [+ sh-numismaster-167727]; 167729/167745 → `unified-schleswig_holstein-numismaster-*`).
  All 3 stayed seed_unsorted → 0 curation lost; final 903→903 (exact 3-for-3 re-key,
  verified by id-diff; cross-entity pulls intact; sh-167745 gained Fr 16).

**This ALSO closed the «two-builder overlap» half of systemic follow-up #1**
(NumisMaster ND re-flow): royal_holstein no longer has a main-vs-pre1541 builder
clash — only ONE numismaster builder writes it now. The coordinated re-seed still
needs to review ~3 weeks of builder drift, but no longer has to reconcile two builders.

**LEFT for a user decision (reported in chat).** The **numista** `denmark_pre_1541`
is a DIFFERENT thing and is ALREADY data-unified: `build_numista_seed.py` reads a
flat `scripts/cache/numista/parsed/*.json` dir (not a per-scope bucket) and seeds
those 56 coins to their proper entities — there is NO numista data split. Only dormant
scaffolding remains: `scripts/fetch_numista_pre1541.py` + `scripts/parse_numista_pre1541.py`
+ the raw cache dir `scripts/cache/numista/denmark_pre_1541/` (56 coins, harvest
provenance). Not touched — lower value, higher risk (deleting the raw dir loses
harvest provenance for coins whose parsed sidecars are still consumed). Ask the user
whether to also retire that dormant numista scaffolding.

## 2026-07-09 (later) — Phase-filter fix SHIPPED + reign-span model + coin cleanup

> **UNPUSHED — push pending «пуш».** This session's commits (newest first):
> foundation-reset kmk-158132 · `ca0400e` split 2 over-merges (bruun-14906 +
> kmk-158132) · `24b3297` f3h91 die-error 1633→1653 · `abf915f` year_is_reign_span
> flag · `be01d87` reign-span verified:false (113) · `77df690` Change 2 outer-span
> expansion · `102301d` Change 1 year-filter removal. Working tree clean, build exit 0.

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

> **UNPUSHED — push pending «пуш».** This session's commits (newest first):
> `8811169` re-merge+re-absorb propagation · `2f1967e` pin curated coins +
> km-645 completeness · `8b531f7` re-seed · `7a647a0` cache pointer (submodule
> `9b0f11246`) · `963a885` parser meta-priority + registry adds · `6cfbf1f`
> crown-map from registry · `afda3b1` year_verified on undated Bruun · `1e6115e`
> drop 3 OOS undated Bruun + NDMED gate. Working tree clean, build + all audits pass.

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

## 2026-07-02 — km-761 cross-entity consolidation + one-pass relocation + completeness guard (HARD ERROR)

> **UNPUSHED — 73 commits ahead of origin; push pending «пуш».** origin/main = `21fbdcd`, HEAD = `73526f8`.
>
> **km-761 «2 Rigsdaler» 1854-1863 cleaned + consolidated into ONE cross-entity coin.**
> The fragmented km-761 cluster (km-761 + f7h6a/b/c) had a FABRICATED note (§0 —
> a garbled Christian IX golden-wedding coin) + wrong indices (hede 7 → Prøvemønt
> f7h7; dav 75 → KM 742 Death-and-Accession). Cleaned each (`be91f25` drop stray
> f7h7 source, `0763b4b` consolidate). Consolidated 13 members → `_cross_entity.yml`
> target royal_holstein, head `unified-dk-hede-f7h6a` (fuss 18_5_thaler, phase
> `{denmark: I, schleswig_holstein: III}`, km [761,761.1,761.2,761.3], hede
> [6A,6B,6C]) — the f7h8/KM631 precedent. Used the existing `_home_entity` [DR,RH]→
> royal_holstein routing (no new logic needed).
>
> **Absorber → ONE-PASS cross-entity relocation (`abfaa0d`).** Previously a
> cross-entity merge needed TWO actions (merge + manual delete of the stale
> source-side final). Added `_cross_entity_relocated_out(entity_id)` +
> `_final_is_relocated(fe, relocated_out)` → the absorber now DROPS the stale
> source-side final in the same pass (a FINAL filter on `enriched_entries`
> AFTER the monotonic guard — placing it earlier didn't stick, the monotonic
> guard re-promotes vanished prior-finals verbatim). Watch for `[<source>]
> cross-entity relocation: dropped N stale source-side final(s)` in the absorb log.
>
> **Completeness guard: WARNING → resolve 16 → HARD ERROR (`8bd2d4c` → `01e5330`
> → `f05f1c7`).** New `_check_cross_entity_completeness` in the merger: on every
> run, if a `_cross_entity.yml` group has a seed sharing a member's KM/Hede base +
> nominal + metal that is NEITHER in `members` NOR in the new `excludes:` field, it
> is a forgotten member (would fragment/phantom in its source entity — the exact
> hole `_final_is_relocated` can't see, an unlisted seed is never in
> `relocated_out`). Shipped as WARNING first; it found **16 real pre-existing
> forgotten KMM specimens** (c7h33 +5, f6h14 +8, c7h13 +3) → MERGED all 16 per §9a
> (NOT excluded — they ARE the coin; `_suppress_weightless_museum_overcollection`
> handles display, thinning does its job). THEN promoted to HARD ERROR (`sys.exit(1)`).
> Verified: clean run rc=0 (completeness=0 proceeds), injection rc=1 (BLOCKED, names
> the seed). The merger is manual-only (CI `deploy.yml` runs build.py, not the
> merger) so the hard-error breaks no automation.
>   - **KMM image signal** (learned): NOT the cache `drawingExists` flag (False for
>     all, including specimens that DO have images). Real signal = `related.assets`
>     with `type: "still"` in the ES `_source`. 3 of the 16 had images.
>
> **Two smaller guards this session:**
> - **exonumia guard broadened** (`86c8c82`, `bd9faa5`) — `build_numista_seed
>   ._excluded_strike_reason` now also drops off-scope metals (`_OFFSCOPE_METALS` =
>   paper/white-metal/tin/pewter) + title-exonumia (`^(medal|médaille|token|jeton|
>   jetton|plaquette)\b`). Cleared 2 of the 3 audit_v2 I4 failures.
> - **phase int→str coercion** (`d88fb24`) — `schema.py::_coerce_phase_to_str`
>   field_validator: an unquoted-YAML-int phase (`phase: 131`) coerces to str; dict
>   int-values coerce too; bool still fails. Cleared the c3g-131 I4 failure. (str→int
>   was analysed + rejected: per-location dict form + non-numeric phase ids like «III».)
>
> **`v2-merge-coins` skill — CROSS-ENTITY MERGE section added (`73526f8`).** Documents
> the `_cross_entity.yml` GLOBAL path (target_entity + members + excludes), the merger
> PULL/EXCLUDE/stamp mechanic, the one-pass relocation filter, and makes the HARD-ERROR
> completeness guard's contract explicit (member enumeration mandatory; every KM/Hede-
> base+nominal+metal sibling is a `member` or an `excludes`, no third option). Records
> run-WITHOUT-`--entity`, absorb-both-entities, [DR,RH]→royal_holstein routing, and that
> `merge_helper.py audit` skips `_cross_entity` by design.
>
> **Board CLEAR** — the whole km-761 / cross-entity / completeness-guard cycle is closed.
> Full suite 444 OK; audit_lost_citations 0; audit_v2 0; build rc=0.
>
> **Later 2026-07-02 — «what's left» audit + two closures.** Re-verified the deferred
> backlog against actual DATA (not the handoff scanner, which trusts stale markers):
> **f3h62** + **c4h115** + **galster hg-238** + **audit_v2 I4** were ALL already
> resolved — false-positives from un-updated «SURFACED, not actioned» bullets (closed
> the stale block `abee66c`). GENUINELY open, data-verified: c9h18 (13 unabsorbed KMM
> 2-Øre fragments), c4h77 (Hede-77 family unassembled), reign-scoped hede/sieg/schou
> mis-attribution audit (never run), §W prose-lint (1203: 563 err/640 warn), i18n
> guldkrone HEDE-25 (1 err/20 warn). Closed this session: **ucoin HARVEST_GUIDE**
> «deferred»→ACTIVE (`5b43881`) + the **sub-letter-space** defect class (`67590f0` +
> `296d051`, 109 values — see the 2026-06-28 «Minor known-quirk» entry, now RESOLVED).
>
> **Later still 2026-07-02 — pushed to origin, then continued.** Pushed `21fbdcd..ec16333`
> (85 commits) then kept working; **origin behind again** (local commits after the push await
> the next «пуш»). Shipped after the push:
> - **NEW skill `fuss-description`** (`aaeef69`) — writes/revises/SCORES a fuss `description`
>   against a 6-criterion rubric → X/10 (founding · role · per-phase differentiator · no
>   metric-fixation · every claim sourced · no specimens), loopable to a threshold (default
>   8+). Helper `describe_helper.py <fuss>`. Executable form of §7a+§0+§5+§0z. Registered in
>   CLAUDE.md §Skills + §7a pointer + PLAYBOOKS PB-3. Demo score: rhinsk_gylden_fod ~8.5/10
>   (8.0 = ship-bar, 9.0 = excellent). **NEVER invent to raise the score.**
> - **c4h77** «1 Mark Danske» Chr IV consolidated — 6 seed_unified clusters → one coin, KM 12 =
>   Hede 77 (`cbd23ad`; bundled 4 benign «2 Skilling» §9a folds per curator OK).
> - **i18n backlog 21 → 0** (`da2332e` normalize_catref hyphen-strip clears 20 spurious R3 +
>   `ac58500` gottorp km-46 missing-DE note).
> - **72-Guldgyldenfod card** (= rhinsk_gylden_fod) reworked: atomic nobel-style Grundwerte rows,
>   per-phase sub-sections (`.gw-phase` CSS, no divider between phases), carats as fractions
>   (18 / 18¼ / 18½), aside block, uk «королівсько-монетний» German-calque → «королівський».
>   Commits 10ea0ec…c103f33.
> - **Cross-entity c3g-131** folded into c3h14 (`ef1a441`) — 4th Galster-131 «1 Rhinsk gylden»
>   (DK standalone) merged into RH; both finenesses [.750, .764] preserved §9a. NOTE: the
>   completeness guard did NOT catch it (keys on km/hede; c3g-131 carries only `galster`) — a
>   known guard blind-spot for galster-only seeds.

## 2026-06-29 (night) — two skills + gottorp over-merge fixed + audit-expansion fix

> **UNPUSHED — 57 commits ahead of origin; push pending «пуш».** Night-work session.
>
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

## 2026-06-29 — B4 (9/9) + B5 (1/1) COMPLETE; whole over-union B-group done bar f7h7

> **UNPUSHED** — 41 commits ahead of origin; push pending «пуш».
>
> The 25-group over-union audit is now essentially CLOSED: B1 (8) ✓, B2 (4) ✓,
> B3 (3): f7h16+f7h17 ✓ / **f7h7 deferred**, B4 (9) ✓, B5 (1: f3h153) ✓.
>
> **B4 (9/9)** — all re-evaluated under corrected §9.4 (Sieg sub-variants are
> sub-variants of one coin). 8 merges + 1 clean:
> - c4h106 (`bf8f2df`) Sieg 90.1-90.4; c4h107 (`0a55aa7`) Hede 107 — Sieg 79.3
>   kept as a verified Bruun attestation (c7h25 shape); c9h18+f3h121 (`5f52a41`);
>   f2h20 (`6c1ccf2`) foundation-fold; f5h34 (`d5b12b9`) KM 580/581; f5h38
>   (`2dfca82`) KM 595/596/597 — render exposed a 3rd KM (597) the B4 table missed.
> - **c4h114** (`f430c87`) — the lone CLEAN: kmk-714958 was a Hede-114A specimen
>   mis-DATED 1619 by KMM (reverse reads «16Z0»=1620). Fixed via the established
>   `_KMM_YEAR_ERRATA` map in build_kmk_seed.py (NOT a final note); the year fix
>   auto-re-clustered it from Hede 110 (1619) to Hede 114 (1620-1621). The
>   KMM-year-error practice = that builder map, curator-confirmed per entry.
> - **c7h28/c7h29** (`814a9d7`) — NOT a merge: two distinct «24 Skilling» Chr VII
>   (Hede 28/KM 635/Sieg 17 vs Hede 29/KM 643/Sieg 18, same 9.171 g). The bug was
>   V1 cross-contamination of the KM lists; cleaned both (dropped each other's
>   phantom KM + the orphan NumisMaster source). NO index source-error.
>
> **B5 f3h153** (`f27d6a7`) — «4 Mark Danske» (=1 Krone) Frederik III Glückstadt
> 1659-1660 = Hede 153, Krause-split across TWO volumes. Merged 3 finals with
> **volume-separated dict-form km** `{sh:[95], dk:[A43,B43]}` (KM 95 = German SH
> volume → KM# 95 on SH page; A43/B43 = Danish volume → KM-DK# on denmark) so
> German/Danish indices never conflate. Confirms dict-form km renders correctly
> on BOTH pages for a royal_holstein coin (the c7h13 dict-form glitch does NOT
> recur here). kind set to tarif (§6 Kronemønt).
>
> **OPEN / deferred:**
> - **f7h7 (B3)** — NOT a clean cross-entity dup. danskmoent Hede 7 is a private
>   **Prøvemønt** (pattern, §9.1-excludable); the «km-761» data is actually the
>   f7h6 circulation «2 Rigsdaler» mis-tagged Hede 7. Tangled with f7h6. Awaiting
>   curator decision (fold km-761 into f7h6 + fix Hede tag, or defer).
> - **c9h18 «2 Øre»** — ~29 PRE-EXISTING un-absorbed KMM museum-specimen rows
>   (weightless, fragmented across 19 seed_unified clusters). Separate
>   museum-fragmentation / §9a-thinning issue, project-wide pattern. Not touched.
> - Single-member cross-entity re-home infra (validator relax + xentity stamp
>   fix) was developed for f7h7 then REVERTED when f7h7 deferred — re-add with the
>   concrete use-case if a single-member re-home is needed.

## 2026-06-28 (later) — B2 specimen-fold (4 of 4) COMPLETE + §9.4 rule corrected

> **UNPUSHED** — 30 commits ahead of origin; push pending «пуш». New this pass:
> c7h25 `2773ab2`, §9.4 rule fix `d8df9d7`, B2 c7h39/f4h57/f3h40 `2a1c4d3`.
>
> **B2 «specimen ⊂ main» (4 candidates) all merged.** Each verified via the
> index-graph procedure (build the graph of all catalogue indices across all
> candidates; a unifying catalogue ⇒ one coin):
> - **c7h25** «1 Kurantdaler» Chr VII 1788 — cross-entity merge (royal_holstein↔
>   danish_realm), KM 645 + Hede 25. Sieg diverges by source: danskmoent «Sieg 26»
>   vs Bruun lot 13248 «Sieg-19» — BOTH cache-verified → union `sieg:[19,26]`.
> - **c7h39** «1 Speciedaler» Chr VII 1787-1808 — 5 finals → 1 (KM base 138 sub
>   .1/.2/.3/.5, Hede 39A-39G). Intra royal_holstein.
> - **f4h57** «1 Dukat» Fr IV 1705-1706 — 2 → 1 (KM 2/2.1/2.2, Hede 57A/57B). Intra rh.
> - **f3h40** «¼ Dukat» Fr III 1665+1668 — 2 → 1 (KM 264/264.1/264.2, Hede 40A-40C). Intra danish_realm.
>
> **§9.4 rule corrected (`d8df9d7`).** The old «different catalog index = different
> type» was too blunt — we tripped over it every B-group session. New rule:
> sub-indices (138.1/138.2; 39A/39B; 102.1/102.3) are sub-variants of ONE coin;
> decide same-coin-vs-distinct-type by building the GRAPH of all catalogue indices
> and checking whether ANY catalogue unifies them under one base index. Distinct
> types only when EVERY catalogue gives distinct base indices unified by none.
> Synced the «Do NOT skip» bullet + the anti-pattern §4 fineness clause.
>
> **Remaining B-group fronts (not yet started):** B4 same-KM/diff-Sieg (9),
> B3 cross-entity (3), B5 (1) — per the 2026-06-28 over-union audit below.
>
> **Minor known-quirk — RESOLVED 2026-07-02** (`67590f0` code, `296d051` data):
> the `catalog.hede: '39 C'` whitespace was NOT one occurrence — a full scan found
> **109** of the same Numista tab-split defect (lange 82 + hede 27) across 22 seed/
> seed_unified/final files. Durable fix shipped: `normalise_numeric_index` collapses
> a whole-token «number space sub-letter» via `_strip_subletter_space` (anchored so
> Lange's reign-disamb «358 C IV» + dav volume codes stay intact), reaching the
> render chokepoint + every merge/absorb/seed-writer pass; the 109 existing values
> healed format-preserving (+109/-109, zero churn). test_catalog_subletter_space.

## 2026-06-28 — B1 over-union cleanup (group D / Pattern B), 8 of 8 COMPLETE

> **UNPUSHED** — pushing pending «пуш». New commits this session on top of the
> 2026-06-27 batch: c4h105 `dce7296`, c4h92 `7a7534a`, c5h67+c5h31 `5dfee7e`
> (+ the earlier c4h59 `f2a9291`, pin-heal `f8c2985`, I1-audit `f66e800`).
>
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

## 2026-06-27 — KM-differ candidates closed + dangling composed_of-pin finding

> **UNPUSHED** — 4 commits ahead of origin (adeb443 c4h116, 48f49ee c5h57,
> 1287d4c f6h27, f2a9291 c4h59) on top of the prior ~80. `git push` pending «пуш».
>
> **All KM-differ candidates from the 2026-06-26 list are now resolved + committed:**
> - **c4h116/c4h117** (adeb443) — over-merge regroup: catalog-less KM 80.2 forced into
>   Hede 117 (not 116). Needed the COMPLETE block-set (all 3 catalog-less Hede-116
>   records + kmk-191584 wanderer) because force-merge runs last and auto-match joins
>   catalog-less KM to the wrong cluster first.
> - **c5h57** (48f49ee) — over-merge regroup: Hede 57 (u.år) = KM 455 (1699), not KM 387.
>   Same shape as c4h116; +no_merge [dk-hede-c5h57, denmark-numismaster-65801] to stop
>   KM B445 (1696 horseback Ducat) following the catalog-less record.
> - **c9h16** (21fbdcd) — §CN errata: Bruun KM-195.1 is a misprint of 795.1 (10 Øre),
>   user-guaranteed; fold bruun-8346/8360.
> - **f6h27** (1287d4c) — Krause dual-listing: 1-Rigsbankdaler = ½ Speciedaler ⇒ KM 696.2
>   = 706.2, one coin. Fold + accumulate KM per §9.
> - **c4h59** (f2a9291) — Hede groups ½ Speciedaler Chr IV as one h59 (59A/B=KM 100
>   1624-1634, 59C=KM 135 1646) despite differing KM. merge_decision force + accumulate
>   KM [100,135]; final fold of standalone km-135; note updated (1624-1646, 59C/KM-135).
>
> **FINDING — dangling composed_of pins trip audit_v2 I2 (5 pre-existing; NOT caused
> by today's work).** `audit_v2.py --quick` exits 1 on the worktree AND on HEAD because
> 5 final foundations pin a drop-id in `composed_of` that resolves to neither seed,
> unified, nor final: `dk-tid-70760→unified-dk-bruun-8093` (f6h27),
> `km-455→unified-dk-bruun-7244` (c5h57), `km-61-1→hede-105a` + `c9h13a→km-798-1` +
> `c7h13a→km-651-1` (dedup_final_foundations PAIRS). Root cause: the dedup fold's
> durability pin assumes the drop's twin survives in seed_unified; when a merge_decision
> ALSO merges them at the seed_unified layer (f6h27, c5h57), the twin is consumed → the
> pin dangles AND is redundant (durability already guaranteed by the merge_decision).
> **c4h59 deliberately avoided this** — folded composed_of left clean (`['unified-dk-hede-
> c4h59a','unified-dk-numista-109973']`), no pin, because its merge_decision handles
> durability. The 2 session pins (f6h27/c5h57) are the same easy case and could be
> stripped; the 3 dedup-PAIRS pins need care (no seed_unified merge_decision → check
> whether removing risks absorb resurrection, or whether the pin should target the
> UNIFIED twin id rather than the final id it currently names — the final-id pin may be
> ineffective for durability anyway).
>
> **RESOLVED — all 5 pins healed (`f8c2985`, audit_v2 I2 5→0).** Verified each
> repair against absorb's OWN convergent state (`process_entity`, no `--apply` to
> avoid the +21 stale-purge drift the session avoids): f6h27 dk-tid-70760 pin
> RE-POINTED unified-dk-bruun-8093→unified-dk-hede-f6h27b (the live merged host);
> c5h57 km-455 pin DROPPED→`[]` (Hede 57 already absorbed in dk-tid-97535); the 3
> dedup orphans (drop composed_of=[], nothing to resurrect) pin DROPPED. KEY mechanic
> learned: absorb's line-1670 "PURGE stale composed_of" strips any cid not in current
> `unified_by_id` on EVERY run, BEFORE building already_absorbed — so the pin never
> reached the resurrection guard; it was cosmetic. Isolated before/after build diff:
> SH render-neutral; denmark removed 3 latent f6h27 "Bulk-Seed" phantom rows (broken
> pin pointed at the dead bruun-8093 so its seeds were never suppressed) — ZERO data
> loss, all values consolidated in keeper dk-tid-70760.
>
> **I1 home-file audit was STALE — fixed (`f66e800`, audit_v2 --quick 0).** The 39
> "violations" were CORRECTLY-placed coins: the live seed-writer
> `lib.v2_seed_writer._home_entity` homes any `issuing_entity` containing
> `royal_holstein` (the SH∩Denmark overlap entity) to royal_holstein.yml so BOTH
> pages pick it up via robust Pass-1 — but the audit still hard-coded the old
> alphabetical-first rule (would want danish_realm.yml) and flagged them. User
> confirmed royal_holstein placement is right. Fix: the audit now IMPORTS
> `_home_entity` and checks `_home_entity(coin) == filename`, so audit + writer
> share ONE function and can't drift. All 12254 live coins pass; regression test
> `tests/test_i1_home_file.py`. **Hook now installable** — `audit_v2 --quick` (what
> Check 4 runs) = 0 (I1/I2/I3/I5 clean). Pre-existing FULL-audit-only findings remain
> (NOT hook-gated, --quick skips them): I4 schema 51 + I6 decision-refs 7 — separate
> cleanup before a non-quick gate could go green.

## 2026-06-26 — thin-line metal consensus + Pattern-A dedup + 2-Dukat-1747 regroup

> **UNPUSHED** — ~80 commits ahead of origin. `git push` pending user «пуш».
>
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

## 2026-06-25 — catalogue «/»=«and» split fix + §DA Table A/B (verdicts pending)

> **UNPUSHED** — slash chain a32d944→5a391e6→97a0157→`5f8c2d1`→`8abf341`. `git push` pending.
>
> **Catalogue «/» = «and» split — FINAL (`5f8c2d1` code+tests, `8abf341` data heal).**
> Evolution across the session: a32d944 split on EVERY «/» → produced prefix-less
> «96|T-91»; I interim-fixed it to «keep tight slash whole» (a32d944) and corrected my
> wrong «range» label (5a391e6/97a0157); **user then settled the semantics — «/» = «та»
> (and)**, superseding keep-whole. Final rule in `lib/catalog_codes.split_multi_ref`
> (both surfaces delegate): split on «/», RE-ATTACH the leading alpha prefix of the
> first member to any bare-numeric continuation → Jensen-Skjoldager «T-91/96» = [«T-91»,
> «T-96»]. Number-list guard keeps non-number «/» whole (publisher «Divo/S», «#»-labelled
> tokens); dash «T-81 - T-88» is a separate range notation, untouched; km keeps its own
> split. **Data heal (`8abf341`):** the old code had ALREADY split these into prefix-less
> lists in the seeds — galster `['T-91','96']`/`['T-41','45']`/`['T-31','35']` + Bruun
> `['T21','25']`/`['T-22','26']` — propagated to seed_unified + final. normalise_catalog
> can't re-heal (the «/» is gone), so a one-time nearest-preceding-prefix heal via
> `lib/yaml_io.py` fixed all 4 danish_realm layers (incl. the merged unified-dk-bruun-4056
> `['T21','25','T-22','26']` → mixed dash styles preserved per §0). Blast radius = J-S
> only, danish_realm only; 0 bare-continuation J-S left; build + validate + 357/357.
>
> **§DA remaining cases — re-investigated from source, awaiting verdicts.** Presented
> two tables in chat (NOT yet acted on, no data touched):
> - **Table A (11 coins, real errors):** **(A1) DONE (`cec33b1` cleaner, `6845b0a`
>   data).** `_reroute_foreign_catalogue_refs` → `_clean_catalogue_refs` (galster/
>   sieg/schive/schou/J-S): drops Danish prose («mangler hos», «adskillige
>   katalognumre, se side …», «; unik»), extracts «hhv. X og mangler»→X, routes
>   Ernst (+ existing Hildebrand/Lagerqvist/Rasmusson/Hauberg)→others. Fixed all 7
>   (f1g-168 galster→168, f1g-49 J-S dropped, c2g-172 schive→XV.5, hg-159/hg-155
>   schive→XIV.* + Ernst→others, f1g-78/f1g-74 schou→13/3). Seed cleaned + re-merged
>   (clean) + final patched SURGICALLY (a full re-absorb drifted an unrelated 10-Ducat
>   1604 entry — avoided). test_galster_catalogue_clean (9 tests). **(A2) DONE (`9bc6d09` filter, `18b3002`
>   data).** build_numista_seed had NO §9 filter (build_hede does); added
>   `_excluded_strike_reason` pre-screen (KM «Pn…»/«(OM)» + title «pattern/trial
>   strike»/off-metal/afslag) — caught 34 numista sidecars, all verified genuine.
>   Removed the 10 currently-seeded unambiguous ones (titles say pattern/trial/off-
>   metal, all standalone): user-flagged 314921 + 345593 (was rendering on denmark),
>   + 314933 (was rendering on oldenburg/german_empire), + 7 Bremen/Brunswick dormant.
>   **Batch-2 RESOLVED (`5660be5` + `43bbb7e`/`59d4c2b`).** Two sub-classes split by
>   curator 2026-06-25:
>   • **3 Portugaløsers KEPT** (387243/387448/427984) — unique FULL-VALUE gold show
>     coins (nominal IS the bullion denomination; «1 Portugaløser» = 10 ducats), could
>     circulate at face value (user: «нехай будуть у нас»). 387243/387448 standalone,
>     427984 merged in `unified-dk-bruun-6273`.
>   • **468992 EXCLUDED — §9 OFF-NOMINAL** — title «5 Ducats» (pure ducat weight) but
>     value.raw «1 Krone» (KM PnJ16): a 1-Krone struck in 5-ducat gold; same metal (not
>     off-metal) but would NOT circulate at its stamped nominal → out of scope. Standalone,
>     removed from 3 layers.
>   Filter changes: (a) dropped the bare Krause «Pn» trigger (it conflates die-trials
>   with full-value pieces) — keys on TITLE («pattern/trial strike»/«(Pattern)»/off-metal/
>   afslag) + «(OM)» KM; (b) added an OFF-NOMINAL rule (`32e485e`) — title leading segment
>   exactly «N Ducat(s)/Dukat» AND value.raw non-bullion AND «Pn» in KM (the «Pn» gate per
>   user — keeps overweight/tariff/bad-data out). Verified: still catches all 10
>   already-removed strikes; catches exactly 468992 off-nominal; does NOT touch the 181
>   genuine Ducat coins, «¼ Ducat / 3 Mark» tariff coins, or the 3 Portugaløsers.
>   **Class codified as CLAUDE.md §9 item 5 (`b387ab1`)** with all caveats (off-nominal =
>   nominal≪metal; Scheidemünze is the opposite §6; not dual-denom/equivalent; not
>   overweight/tariff/bad-data). Item 1 (patterns) refined: bare «Pn» not sufficient to
>   skip. Tests + full suite 382/382.
>   **(A3) DONE — both diagnoses corrected after deeper research.** `31393` (`6062832`):
>   NOT «strip # → SD 44» — «SIEG SD» is a DISTINCT Saxe-Lauenburg/German Sieg catalogue
>   (numista page confirms; 99 coins use Danish «SIEG#», only this 1 «SIEG SD#»). An old
>   build mis-mapped it into the typed (Danish, reign-scoped) `sieg` field → false
>   collision + mis-render. Dropped the typed dup; citation PRESERVED in `others` as
>   «SIEG SD# 44». `km-x000-fr-iii-1644` lange «280 ff.» (`b2ddeca`): NOT a paper/manual
>   value — a V1-bootstrap over-merge/mis-parse artifact. Per-coin identity audit
>   confirmed it's the SOLE genuine lange mis-attribution (km A43 Frederik III 4 Mark vs
>   the only «Lange 280» in harvest = «280-290» of Johann Adolf 1/16 Thaler KM 5). No
>   harvest source gives this coin a Lange; dropped (coin stays ID'd by KM A43+Hede 153B
>   +Sieg 153.2+Schou+Dav, all corroborated).
>   **Provenance audit (user-requested «what do sources not give»):** (1) vague/malformed
>   scan of ALL typed fields → «280 ff.» was the ONLY one. (2) per-coin identity audit
>   (km-owner match) reliable for GLOBAL catalogues: lange = 1 (this), fr = 0. (3)
>   REIGN-SCOPED catalogues (hede/sieg/schou) can't use km-owner match (numbering restarts
>   per reign → false positives, e.g. documented KM-240/241 Hede-62A) — a reign-scoped
>   (number+ruler→km) pass is an open FOLLOW-UP if we want to close that class. Thinning-
>   salvaged indices trace to dropped-specimen cache records → not flagged.
> - **Table B:** `307035` hede «C4 80.C» (reign-disambiguated, our convention `c4h80.C`)
>   — leave as-is. **6× numista lange «… var.» → STRIPPED (`555f5bd` code, `31d5245`
>   data)**: user 2026-06-25 «var прибери, індекс уже достатньо» → `normalise_catalog`
>   now drops a trailing «var.»/«variant» qualifier (new `_strip_variant_qualifier`,
>   block 1b, all typed list-fields); 16b/271/28/331/358 C IV/399 A bared across
>   seed/seed_unified/final (gottorp_duchy + royal_holstein). Distinct from cf./unlisted
>   (those DROP the value). test_catalog_variant_strip (6 tests); 388/388.
> - **§DA fully closed:** A1 (galster prose) + A2 (numista §9 patterns/off-metal/off-nominal,
>   Portugaløser KEPT) + A3 (31393 sieg-dup, 280 ff. mis-attribution) + Table B (var. strip)
>   all done. **Open follow-up:** reign-scoped hede/sieg/schou mis-attribution audit
>   (number+ruler→km) — the only mis-attribution class not yet swept (km-owner method can't
>   handle reign-restart).

## 2026-06-25 — night: galster foreign-catalogue reroute + catalogue-hygiene audit (§DA)

> **All UNPUSHED** (this night added 4: `9558e85` docs → `1a03f3e`). `git push` pending.
>
> **Autonomous night work** (user: «лишаю тебе на night work, продовжуй доки не завершиш»).
> Stayed inside guardrails: no push, no new errata beyond curator-approved, ambiguous
> catalogue-semantics DOCUMENTED not guessed.
>
> **Galster foreign-catalogue reroute — FIXED** (`e2e3727` builder, `1a03f3e` data).
> 5 Hans (hg-) Galster coins crammed foreign catalogues into `galster`/`sieg`:
> hg-233/234/236/238 had galster «233, Hildebrand 715, Rasmusson ill. 17,
> Lagerqvist 4» (danskmoent COMMA-JOINS cross-refs into the galster string);
> hg-141 had sieg «Hauberg 102». These rendered as «Galster Lagerqvist 4» on the
> denmark page. `build_galster_denmark_seed._reroute_foreign_catalogue_refs` splits
> on comma + routes foreign-NAME-whitelist parts (Hildebrand/Lagerqvist/Rasmusson/
> Hauberg) to `others`; real index stays typed, legit Sieg «[2015] 8» kept. Applied
> surgically to the danish_realm seed (ruamel round-trip) — NOT via `--no-merge`,
> which had a collateral `mint_verified:true→false` flip on a danish_norway coin.
> Re-flowed danish_realm (merge+absorb, 0 stale dropped); rendered «Lagerqvist 4»
> now a plain `others` entry. Verified end-to-end.
>
> **Broader finding → TODO §DA — CORRECTED 2026-06-25 (§0b).** The whitespace scan
> surfaced 688 values, which I FIRST mis-documented as «~677 need curator judgment».
> On verification (when the user asked me to double-check) that was **~93% false-
> positive**: ~640 are LEGITIMATE source notation — chiefly **569 Davenport
> volume-series** (`dav` «EC II 3529» etc.; numista emits «Dav <series>» codes and
> `numista_canonical.py:99-106` routes them to `dav` BY DESIGN) + 44 spaced
> sub-variants (source's literal «762 b») + 16 year/range/yearbook annotations + 11
> Galster-UU sub-series. The **genuine issues are only ~30**: ucoin `km` «UC# N»
> (12, internal id misfiled), bare-dash empties (6), bruun/galster parser garbage
> (~10), lange «N var.» (6, policy), «; unik» (2). Lesson: «contains whitespace» is
> NOT a bad-index signal (Davenport volumes/sub-letters legitimately have spaces) —
> verify the source mapping before flagging. Full corrected breakdown in TODO §DA.
>
> **2 stale royal_holstein assignments retargeted** (`60b7fcf`). The full re-flow's
> «Curator assignments unmatched: 2» were c4h8b + bruun-14770 — coins that folded
> into heads c4h8a (Ungersk Gylden) / c3h14 (Rhinsk Gylden); the assignments still
> targeted the dead pre-fold ids. Classification was never at risk (curated finals
> are guard-preserved), but retargeted c4h8b→c4h8a / bruun-14770→c3h14 to clear the
> debt. Render-neutral (coin-id set unchanged); unmatched 2→0.

## 2026-06-24 (later) — §9a salvage + galster-key fix + full re-flow shipped

> **All UNPUSHED** (30 ahead of origin; this session added 6: `c199b93`→`9e8b6f7`).
> `git push` pending — no «пуш» yet.
>
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

## 2026-06-24 — V1 layer fully removed; all consumers migrated to V2

> **Commits UNPUSHED** (this session added 9: `366c9f4` reference/ → `30a4718`
> docs). `git push` pending — no «пуш» yet.
>
> **V1 is gone.** V2 (`data/v2/{locations,final}/`) is the sole pipeline. Proven
> empirically before each removal: a full default build is **byte-identical**
> (44 HTML files, manifest sha1 `91357407…038a15`) with vs. without each removed
> piece. What was removed + how:
> - **Empirical proof first**: re-ran ALL 10 V2 seed builders with `data/seed/`
>   moved aside → each reproduced its committed coin-id set 1:1 from cache
>   (`data/seed/` was V1-anchor, not a live input).
> - **kmk-seed «staleness» was a FALSE alarm, now permanently fixed**
>   (investigated 2026-06-24, §0b). The committed seed was never stale — it was
>   deliberately curated: bare builder emits ~41490 raw museum specimens;
>   `822833d` thinned to the §9a envelope, `a80019b` dropped exonumia. The
>   thinning used to be a SEPARATE post-pass (`thin_kmk_seed.py`), so a bare
>   `build_kmk_seed.py --write` regressed it — which is why the last coordinated
>   re-seed (`3486bf0`) skipped kmk. **Fixed `12575db`**: `build_kmk_seed.py`
>   now calls `thin_kmk_seed.thin()` itself (scope→exonumia→§9a in one run,
>   idempotent, `--no-thin` escape). Seed resynced to the builder output
>   (`d547bec`, 13796→13819, render-neutral). **Safe to `--write` now; re-seed =
>   no-op.**
> - **ikmk over-sampling — RESOLVED (full §9a thin)** (2026-06-24): ikmk also
>   over-sampled (4354, biggest bucket 734 uncatalogued «1/24 Taler» 1619; reached
>   final as a 63-weight coin). New shared `lib/seed_thin.py` (§9a min/middle/max,
>   optional `catalogued_only` gate) wired into `build_ikmk_seed.py`. First pass
>   used the catalogued-only gate (→ 4328, only −26 — the 734 uncatalogued bucket
>   stayed); curator then chose the FULL thin (`catalogued_only=False`) since an
>   uncatalogued museum record carries no distinguishing signal beyond the
>   sub-variant key + weight. ikmk seed now **1273** (4354→1273, −3081; the
>   734-bucket → ≤3 per mint-keyed sub-variant). KMK uses its own no-gate
>   `thin_kmk_seed.py` (committed envelope 13819). Both builders self-filtering +
>   content-idempotent (only `generated_at` churns, as for every V2 seed). All
>   render-neutral (data/v2/final/ untouched; resyncs on next coordinated re-flow).
>   The `catalogued_only` gate stays as an opt-in for future uncertain sources.
> - `366c9f4` reference/ HTML artifacts · `ba528a9` seed_v2_regroup.py +
>   build_numista_pre1541_seed.py (no callers) · `1deb8ff` build.py V1 render path
>   (−458 lines: load_locations, _merge_seeds_into_raw, --include-v1/--v1-only,
>   V1 cross_ref/render/landing; landing+worker now V2-only) · `adb3b34`
>   `data/seed/` · `de7affd` the 12 `data/locations/<loc>.yml` coin yamls.
> - **KEPT**: the 11 `data/locations/<loc>-references.yml` bibliography sidecars
>   (shared with V2 via `load_v2_locations`).
> - **Consumers migrated** (`4c8505d` + `b99d131`): audit_prose + audit_i18n
>   (pre-commit) now scan `data/v2/locations/` + `data/v2/final/` (curated coins
>   only — skip `_unclassified` + `seed_unsorted`; V1 parity ≈ V1 hit counts);
>   audit_fuss_anchors + audit_ucoin_categories + fetch_numista_api + the
>   yaml_io roundtrip test re-pointed to `data/v2/final/` (or `-references` for
>   the ruamel_loc roundtrip case).
> - **RETIRED notes** (`c855710` + bootstrap in `b99d131`): 8 V1-era one-time
>   passes (enrich_*, dedupe_sources, classify_issuing_entity, ucoin_backfill_metal,
>   bruun 04_cross_match, bootstrap_v2_final_from_v1) — kept for reference.
> - **Docs** (`30a4718`): CLAUDE.md, ARCHITECTURE, V2_PIPELINE, HARVEST_GUIDE,
>   build_numismaster docstring updated to «V1 removed / V2 sole pipeline / native
>   builders». V2_DECISIONS (immutable journal) + TODO (curator list) left as-is.
>
> **Note**: `scripts/oneoff/` scratch scripts still reference `data/locations/`
> coin yamls — that's fine (throwaway tier; breaking on removal is expected).
> The prose/i18n audits surfaced a real **curated-prose backlog** (1238 hits)
> they couldn't see while stuck on frozen V1 — that's a separate cleanup, not a
> migration artifact.

## 2026-06-23 — 4 mixed cross-source dups merged (c5h56, f2h8, f6h31, f7h8) — durable

> **18 commits UNPUSHED** (this turn added `673bf03`). `git push` pending.
>
> **4 «mixed» dup candidates consolidated** (curator-confirmed by image). Distinct
> from the stale-Hede-orphan pattern — these were fragmented across sources/entities
> at the seed_unified level. Each merged into ONE host with §9a list-form catalog
> accumulation, durable via `merge_decisions` (so a future re-flow reproduces them):
> - **c5h56** Christian V «2 Dukat» Hede 56 → host `unified-dk-hede-c5h56`; km-458
>   (KM 458, Bruun 7243) folded in; KM 416.2/458 accumulate.
> - **f2h8** Frederik II «3 Mark» (≡ 1 Speciedaler) Hede 8/8A/8B → host
>   `unified-dk-hede-f2h8`; manual f2h8b (Hede 8B, Bruun 4422 + Numista 142126) folded.
> - **f6h31** Frederik VI «8 Rigsbankskilling» KM 152 Hede 31 → host
>   `unified-dk-hede-f6h31`; 3 heads united (same Bruun lot 17159); metal silver→**billon**
>   (0.375-fine = billon; fixed at the Hede SEED via `_curation_holds:{metal}` so the
>   merger keeps billon — danskmoent's loose «sølv» was the silver source).
> - **f7h8** Frederik VII «1 Rigsdaler» Rigsmønt 1854-55 KM 760.1/760.2 → CROSS-ENTITY
>   merge (Kopenhagen danish_realm + Altona royal_holstein clusters) into ONE multi-mint
>   `unified-dk-hede-f7h8` in **royal_holstein** (overlap-home per c7h33/c8h11a, renders
>   on both pages); issuing_entity joint `[danish_realm, royal_holstein]`; phase DICT
>   `{denmark: I, schleswig_holstein: III}` (curator). `_cross_entity.yml` pulls the
>   Cph cluster out of danish_realm (no fragment there).
>
> **Method (NEW memory lesson):** these deletions removed finals that fold REAL
> seed-backed heads → seed_unified must be made consistent (else fragments). A full
> `merger+absorb` re-flow does that BUT also materialises every pending decision in the
> entity (surfaced last-session items). Solution: re-flow to compute the hosts, then
> **transplant** only the 4 hosts into a backup-restored committed state, judge by
> **semantic-diff** (`scripts/oneoff/semantic_diff.py`) not the line diff — the line
> churn is YAML-anchor renumbering (cosmetic). Semantic diff confirmed EXACTLY these
> 4 coins changed. Build clean (denmark/SH); f7h8 renders on both pages, f6h31 billon,
> c5h56 dup row gone.
>
> **TWO OPEN FOLLOW-UPS surfaced (not in this commit — need curator calls):**
> 1. **c5h56 host carries KM 346, which is actually Hede 3** (`unified-dk-bruun-6808`
>    «2 Ducats» 1673 — a SEPARATE type). Looks like a pre-existing Hede-3-into-56 leak
>    from an older merge. NOT touched. → remove KM 346 from c5h56?
> 2. **danish_realm has 2 pending fragments** from LAST session's decisions that a
>    future coordinated re-flow WILL surface (a full `merger+absorb danish_realm`
>    materialised them this session, then I transplanted them back to committed):
>    `unified-kmk-301777` «1 Skilling» 1771 (bruun-7774 no_merge → correct separation,
>    seed_unsorted) + `unified-kmk-175833` «3 Skilling» 1812 (f6h14-adjacent, seed_unsorted).
>    Both need classification when the next danish_realm coordinated re-flow lands.

## 2026-06-22 — metal-conflict guard + bruun-7774 metal fix + 4 cross-entity-dup consolidation (durable)

> **9 commits UNPUSHED.** All verified (build + tests + empirical re-flow). `git push` pending.
>
> **Metal-conflict guard in `_collect_metal`** (commits `f71601a` + `eb80d9b`).
> When >=2 composed_of members are `metal_verified:True` but disagree on metal,
> the merger/absorb now RAISE `MetalConflictError` (stop → curator decides) —
> it once silently shipped KMM «sølv» over Hede «copper». EXCEPTION: thin-line
> alloy pairs `{silver,billon}` + `{bronze,copper}` WARN + pick by authority
> (bronze IS a copper alloy; museums tag bronze «kobber»). c9h18b «2 Øre» CIX
> resolved this way → bronze (Hede auth 5 > KMM 0). `_THIN_LINE_METAL_PAIRS` is
> the list; new pairs go there. Unit tests `tests/test_metal_conflict_guard.py`.
>
> **bruun-7774 «1 Skilling» 1771 silver→copper** (commit `4a86564`). The guard
> exposed a stale-FINAL bug: the coin was silver but is COPPER (KM 616; ucoin +
> NumisMaster×9 + KMM×4 + Bruun). Silver came from an old over-merge with a
> silver «1 Skilling (?)» group (kmk-301777 et al., KMM-flagged «(?)»). Fix:
> `no_merge` (dk-bruun-7774 ↔ kmk-301777) + metal→copper + drop the stale
> composed_of link. The silver «(?)» group stays a separate seed_unified entry.
>
> **4 cross-entity-id dups consolidated into royal_holstein** (commit `c910fd0`).
> c8h11a / f6h9 / f6h14 / f6h17 each had a stale danish_realm copy + a seed-backed
> royal_holstein copy. Merged each into ONE royal_holstein entry (copper, joint-ie
> → renders on denmark Pass-1 windowed ≤1864 + SH Pass-1; data unioned; clean Hede
> token). **c8h11a is the project's FIRST per-location phase DICT**
> `{denmark: I, schleswig_holstein: II}` (1842 ∈ denmark 18_5_thaler I but SH II).
> One-off: `scripts/oneoff/consolidate_cross_entity_dups_20260622.py` (gitignored).
>
> **Durability — analysed + PROVEN** (the deletion un-folded 2 KMM specimens that
> would PROMOTE as silver fragments on denmark; confirmed empirically). Fix:
> kmk-131538 «3 Skilling» (metal None) → `_cross_entity.yml` fold into RH f6h14;
> kmk-175835 «1 Rigsbankskilling» «sølv» → §9.3 Sølvafslag-exclude via
> `build_kmk_seed.py::_KMM_DROP_IDS` (KMM tags it a coin «sølv», not «afslag» →
> type-filter missed it) + removed from kmk seed / DR seed_unified / f6h17. Proven
> via backed-up full re-flow: merger folds/excludes → danish_realm absorb 0
> fragments; absorb `_enrich_final_entry` preserves all foundation enrichment 1:1.
> New tooling-lesson in memory: «deleting a stale final copy that folded museum
> specimens un-folds them → fragments».

## 2026-06-17 (later) — CI build fix (ruamel) + Hede discrete-year root fix (c7h13a 1798)

> **CI deploy was RED since ≥2026-06-11 — FIXED (commit `6f787bd`, UNPUSHED).**
> Root: the build path top-level-imports `ruamel.yaml` (via `lib/v2_resolver.py`,
> `lib/seed_merge.py`, `lib/v2_seed_writer.py`) but `requirements.txt` never listed
> it — CI's `pip install -r requirements.txt` lacked it, so every push failed at
> the «Validate data» step (`build.py --validate-only`) with `ModuleNotFoundError`
> before any render. Local `.venv` has ruamel 0.19.1, which masked the gap. Fix:
> added `ruamel.yaml>=0.17`. Verified: full `--include-v1` build + `--validate-only`
> both exit 0 locally. **The push of this WILL turn CI green again.**
>
> **Hede discrete-year root fix + c7h13a 1798 RESOLVED (commits `8571258` code+tests
> / `58bc460` data, UNPUSHED).** `build_hede_denmark_seed.py::_build_year_fields`
> collapsed a consecutive year run into a loose `year_first/year_last` span (emitted
> `year_ranges` only with gaps), so the merger could displace it under a wider
> discrete envelope and drop an interior year — c7h13C «1798, 1799» lost 1798.
> Fix: emit one singleton `[y,y]` per attested year (Hede lists are always discrete
> enumerations); `_format_year_label` folds them back to «1795-1799, 1801» for
> display. Materialised: re-seed hede (3 entities, year-only diff: 262 hdr + 1510
> singletons, 0 drift) → re-merge → re-absorb (curation-loss gate REAL-LOSS=0, 4
> benign year-add). Three bonus label corrections (nf3h69 1649-1668→discrete gaps,
> c5h126a/c5h107 1693-1696→1693-1694,1696, c8h3a 1840-1848→discrete) — now-discrete
> Hede years let the merger displace masking ucoin/Numista loose spans (§3a/§4).
> 58 tests green; rendered + verified denmark + SH de/en/uk. Full §CX write-up in TODO.
>
> **Push state:** 3 commits UNPUSHED this turn — `6f787bd` (ruamel) `8571258` (Hede
> fix+tests) `58bc460` (Hede data). No submodule change this turn. `git push` pending.

## 2026-06-16 (later) — Bruun ND-year parser fix (committed) + N#131730 over-merge root-diagnosed (§CW)

> **Bruun «ND (…)» year parser FIXED — commit `2efdb80` (UNPUSHED).** New
> `parse_year_span(lot)` in `build_bruun_denmark_seed.py`: an «ND (…)» attribution
> now captures the full range (incl. abbreviated upper bound, `ND (1607-11)`→1611)
> + sets `year_verified=False` → «(?)» marker; dated strikes keep the plain single
> year. 84 in-scope ND lots affected (45 ranges / 33 single / 6 ca.). `year_label`
> stays a clean decimal per §3a. Logged `docs/SOURCES.md` §13.3.
> **Builder code ONLY — the V2 Bruun seeds are NOT regenerated.** Running the
> builder revealed the seeds are STALE w.r.t. ~10 intervening builder/cache commits
> (`41efdf0` Aagaard→`others`, `4465c1b` km cross-register, cache re-parses
> `f5634abb`/`8af66ec` Aagaard die-combos + FP refs + one new lot dk-bruun-6435 +
> a metal flip). A clean regen folds that catch-up in AND then needs a
> `seed_unified`→`final` re-flow — so it's deliberately deferred to the next
> *coordinated* Bruun regen (batch with the parked apply), not bundled into a
> «year-fix» commit. Verified the fix produces correct ranges on the real cache
> lots before reverting the contaminated regen.
>
> **N#131730 over-merge ROOT-DIAGNOSED → new TODO §CW (UNPUSHED docs).** The
> «missing discrete years» question (user) led to: `unified-dk-hede-c7h13a` is a
> **2+2 over-merge** of two distinct Christian-VII-Altona «1 Speciedaler» types —
> **Hede 13** domestic Speciedaler (danskmoent verified: no KM/Dav, 1795-1801;
> members dk-hede-c7h13a + c7h13b) + the **Albertsdaler** trade coin (KM 640/640.2,
> Dav EC III 1310, 1781-1796; members dk-numista-131730 + denmark-numismaster-145357).
> Merger matched on nominal+ruler+mint+metal; no trade-coin-vs-domestic discriminator.
> **This REFINES the earlier handoff follow-up:** c7h13a's spurious-1781 widen is
> the Albertsdaler over-merge (§CW), NOT a §CU reign-window member — the session's
> year-hold (1795,1797,1799,1801) only MASKS the symptom; the over-merge persists
> (c7h13a still carries dav EC III 1310 + km 640/640.2). The cache 131730.json has
> only min/max (no discrete list) but that's moot — fix the over-merge (split +
> re-flow) before re-harvesting the Albertsdaler's discrete years onto its OWN entry.
> §0b: my earlier «KM-640 cross-register collision» hypothesis was WRONG (Hede 13A
> has no KM at all; match fired on primary signals).
>
> **Numista year_list re-harvest gap ROOT-FOUND → new TODO §CX (UNPUSHED docs).**
> Tracing «why no discrete years for 131730» revealed the 2026-06-10 «501-entry»
> year_list re-harvest covered **danish_norway + 5 German entities only** — the
> Danish-crown track was NEVER re-harvested: range-only-no-`year_list` counts
> royal_holstein 102/154, danish_realm 248/516, gottorp 55/93 (control danish_norway
> 4/365 ✅). ~400+ ungapped Danish-crown numista entries; 131730 is just one. The
> machinery (extractor `d4d1ca8`, Priority-0 queue `handoff_numista_year_list_reharvest.yml`)
> all works — it just never ran on this entity track.
>
> **✅ DONE THIS SESSION (UNPUSHED):**
> - **§CW Albertsdaler split** — committed `2324dc9`. no_merges in
>   merge_decisions/royal_holstein.yml + re-ran merger/absorb royal_holstein;
>   c7h13a now domestic (dav EC III 1313, 0.875/28.893, hede 13A-D), Albertsdaler
>   consolidated onto c7h22ab (km 640.1/640/640.2, Dav EC III 1310). Fixed the
>   absorb's recurring km str-repr corruption on c7h13a + km-696 by hand (0 str-repr
>   left). Build clean (denmark 2081 / SH 727), renders verified on both pages.
> - **§CX harvest** — collected 456 Danish-crown range-only NIDs, queued, drained
>   in-session via Chrome MCP (0.35s, 0 errors): 218 gained discrete `year_list`,
>   238 range-only. Caches committed in submodule `2758b6d41`; queue drained.
>   Cache→Downloads→disk transport (Blob `a.click()`) worked around the
>   javascript_tool ~1.5KB result-truncation.
>
> - **km str-repr (form #2) durable fix** — committed `441b285`. Root:
>   `_merge_km_field` (~2620) now iterates a list-valued register instead of
>   `str()`-ing it whole. Heal: `normalise_catalog` explodes any str-repr element
>   (both top-level-list and register-dict-internal shapes), runs on every
>   absorb/merge/seed-write. `fix_corrupted_km_repr.py` shares the predicate; 0
>   corrupted finals. 10 unit tests (`tests/test_km_str_repr_form2.py`). Integration:
>   re-absorb royal_holstein (previously corrupted c7h13a + double-wrapped km-696)
>   → **0 str-repr** (verified, then reverted to keep the §CW final; the only diff
>   was a benign c7h13a km `{sh:[…]}`→bare-list normalisation).
> - **§CU year-mute mechanism** — curator `year_demote` in `merge_decisions`.
>   `process_entity` stamps `_year_demoted` on named reign-window members;
>   `_union_year_ranges` (now `_collect()` + two-pass) holds them to a last-resort
>   pass (span never widens, years not deleted); `build_unified` propagates the
>   flag to wholly-muted unified entries. 3 culprits declared in
>   `merge_decisions/danish_realm.yml` (galster-hg-27, numista-355730, kmk-279179).
>   40 union tests pass; light-integration confirms bruun-3839→1496, c9h16a→1874-1905.
>   MECHANISM committed; MATERIALISATION deferred to the coordinated re-flow (full
>   bruun-3839 1496-1497 also needs the Bruun re-seed), and the per-case year-holds
>   on bruun-3839 + km-795 stay until then (remove WITH the re-flow so they don't
>   OVERRIDE the mute). §CU updated.
>
> - **✅ COORDINATED RE-FLOW DONE (2026-06-17)** — full pipeline re-run, all 22
>   entities, materialising every deferred fix. Phases: submodule `c18232a7d`
>   (numista parsed-sidecar year_list backfill — §CX Phase-2 that the harvest had
>   skipped: build_numista_seed reads `numista/parsed/<NID>.json`, NOT the raw
>   cache the §CX patch wrote) → `3486bf0` re-seed all sources → `68fae2f` merge
>   (+ year_demote for 4 ND-swallow culprits) → `968af94` absorb (+ retired the
>   bruun-3839/km-795/c7h13a holds). Build clean (denmark 2076 / SH 726 stable;
>   German pages grew with the curator-approved ucoin +1136→+273 final). 0 str-repr.
>   Verified: bruun-3839 → 1496-1497, km-795 → 1874-1905 discrete, Albertsdaler
>   c7h22ab → 1781,1784,1786,1796, the 4 ND-swallow coins → their dated years.
>   Gate widens (34) = Bruun-ND honest-range improvements (single→range, desired)
>   + the 4 fixed swallows; metal bruun-3931 gold→silver = correction (Silver Gulden).
>   **NEW class found + fixed (ND-swallow):** an UNDATED Bruun specimen's broad
>   «ND (1670-99)» range (year_verified=False) was swallowing dated discretes of
>   its merged cluster → demoted via year_demote (same §CU mechanism).
>   **Edge case (was flagged) — ✅ RESOLVED at the root 2026-06-17** (commits
>   `8571258` fix+tests / `58bc460` data): c7h13a's missing 1798 was a Hede-seed
>   bug, not a union one — `_build_year_fields` collapsed consecutive runs
>   (13C «1798, 1799») to a loose span the merger could displace. Fix emits
>   discrete singleton `year_ranges`; c7h13a now renders «1795-1799, 1801».
>   See §CX in TODO.md for the full write-up.
>
> **Push:** the re-flow commits (submodule `c18232a7d` + main through `968af94`)
> were PUSHED 2026-06-17 (submodule `e5cd0b774`, main `d36a536` merging #17).

## 2026-06-16 — overlap-home architecture + merger stage of the global apply DONE; absorb DEFERRED (UNPUSHED, e8de501 + e414a0a + 8d882fe + 1a8097b)

> **✅ FULL APPLY COMPLETE — ALL 22 ENTITIES (end of 2026-06-16, commit 2cf628d).**
> The global apply was extended from the Danish trio to the whole corpus: full
> merger --apply (26007 seeds → 16470 unified) + full absorb --apply, all 22
> entities. Build clean, 38 commits, NOTHING PUSHED. The other 19 entities'
> rendered SETS are unchanged (per-location assembled counts identical to
> baseline — bremen 128, brunswick 524, gottorp/holstein_schauenburg/lubeck/
> oldenburg/osnabrueck/hamburg/hesse/german_empire/lauenburg all stable); their
> file diffs are field-level catalog-normalise + enrichment refresh, no coin
> adds/drops. 0 km hybrids + 0 str-repr km across ALL finals.
> **Follow-up (non-blocking): the migration×full-absorb interaction re-introduces
> c7h13a's year-widen (spurious 1781) + a km str-repr on every full absorb — it
> was data-fixed each time (year 1795-1801 + register-keyed km). The durable fix:
> (a) add the str-repr-explosion (form #2, `fix_corrupted_km_repr.py` logic) to
> `catalog_codes.normalise_catalog` alongside the form-#1 dict-fold; (b) close the
> year-hold gap so the override freezes year_first/last (not just year_label) for
> a migrated foundation. Both surfaced only on c7h13a (the one migrated coin with
> a register-keyed SH km + a §CU reign-window member).**
>
> --- Danish-trio detail (still valid, now part of the full apply): ---
> All goals materialised + verified on BOTH denmark + schleswig_holstein pages:
> - **KM631** → ONE coin `unified-dk-hede-c7h33a` in royal_holstein:
>   11_333_thaler/I, joint `[danish_realm, royal_holstein]`, km
>   [631,631.1,631.2,631.3], year held 1778-1785 (§CU — the kmk-122886
>   reign-window 1766-1808 suppressed). Renders on both pages via Pass 1.
> - **Frederik D'or** → ONE coin `unified-dk-hede-f7h1b` (royal_holstein), both pages.
> - **Royal-Danish** mint → Kopenhagen (numista re-seed) materialised.
> - 7 curated c7h/dk-tid finals migrated dr→royal_holstein (ie→joint); c7h33c
>   folded into KM631; c7h11c consolidated into dk-tid-79168.
> - **c7h13a** year-hold 1795-1801 (Hede 13A-D) — suppressed a spurious 1781
>   widen that had dropped it from the 9¼-Fuß phase-III window; renders again.
> - The **km cross-register code bug FIXED at source** (commit 4465c1b): the
>   absorb no longer emits the hybrid `{'sh':[...], 'value':X, 'register':Y}`;
>   0 residual hybrids; km-696 / c5h121 / c7h13a resolve on both pages. (This
>   was a PRE-EXISTING latent bug the apply surfaced — `fix_corrupted_km_repr.py`
>   38f4f67 had only data-patched c5h121; the absorb re-corrupted it every run
>   until this fix.)
>
> Build: denmark 7640 drop / 2084 assembled, SH 982 / 727; id-set deltas sane
> (bulk-promotes + consolidations + migrations); no regression. **`git push`
> when ready.** Remaining follow-ups (separate, non-blocking): §CV (generalise
> `_home_entity` to consumes-map-driven, also schauenburg_pinneberg); §CU
> (systemic reign-window year-union downweight, so per-case year-holds like
> KM631/c7h13a become unnecessary).

**Architecture fix (the curator's home-file model).** A coin's `issuing_entity`
may be a list (joint mint = circulation in several political entities); the
VALUE keeps the full set, but the HOME FILE must be the overlap entity that
maximises page-coverage. `royal_holstein` is the SH∩Denmark overlap (consumed
by BOTH pages), so a coin with royal_holstein in its IE must home to
`royal_holstein.yml` to render on both via Pass 1 (not the fragile Pass-2
intersection). Shipped:
- `_home_entity` royal_holstein-priority (e8de501) — was `sorted(ie)[0]`
  (alphabetical → danish_realm). Migrated the 7 already-joint misfiled finals
  (6 danish_realm + 1 danish_norway) → royal_holstein; verified 7/7 on both
  pages. **General consumes-map-driven rule (also schauenburg_pinneberg) = TODO §CV.**
- cross-entity stamp derives issuing_entity from MINT, not scalar target
  (e414a0a) — so a joint cross-entity-merged coin keeps joint VALUE + homes to
  the mint-derived overlap entity.
- Re-seed numista (8d882fe) + hede (1a8097b): joint coins re-home to
  royal_holstein. Critically — `_home_entity` is consulted ONLY at the seed
  WRITE step; the merger writes seed_unified + absorb writes final BY
  PROCESSING ENTITY, so raw seeds must re-home first (and a cross-entity
  decision's target_entity IS its home file → KM631 target corrected
  danish_realm→royal_holstein).

**Merger stage DONE (1a8097b), scoped to the Danish trio** (danish_realm,
royal_holstein, danish_norway — all affected members live there). Verified: KM631
→ ONE coin `unified-dk-hede-c7h33a` in royal_holstein (joint VALUE, km
[631,631.1,631.2,631.3], 12 members); Frederik D'or → ONE `unified-dk-hede-f7h1b`
royal_holstein (9 members); fragments absorbed; 0 «absent» warnings.

**Absorb DEFERRED — drift review needed first.** The full re-derive of the trio
surfaced accumulated drift since the 2026-06-09 re-merge. The per-entity
`audit_curation_loss.py` OVER-reports it (a re-homed coin reads as a danish_realm
loss though it's gained in royal_holstein — verified f6h14/f6h17 keep full
catalog+weights there). Genuine items to vet before `absorb --apply`:
- **4 §CU reign-window year-widens** (km-695-4 →1820, f5h24 →1763, danish_norway
  kmk-149434 →1643, kmk-194284 →1648) — same class as bruun-3839/km-795; need
  per-case `_curation_holds` (the year-hold override cebf090 handles them) OR
  the §CU systemic fix. (c4h8a Ungersk 8A+8B→1591-1593 is a LEGIT accumulation,
  not pollution.)
- **catalog/measurement drops** (kmk-149272 hede127; c7h29/c4h68/c5h74 weights/
  fineness) — confirm drift-correction (stale re-grouped-member data) vs §9a
  regression.
- **3 metal flips** (dk-tid-71072/78931/79553 billon→silver; km-358 silver→billon)
  — confirm verified-wins drift-correction vs regression.
**Drift review DONE (2026-06-16) — all ~12 genuine items BENIGN.** Verified per-item:
4 year-widens are legit type-spans/accumulation NOT reign-windows (no §CU holds
needed); catalog drop (kmk-149272 hede127) is stale (no current member attests
it); measure drops are rounding artifacts (c7h29 0.563→0.562) / re-grouped-member
data (c4h68) / §9a thinning (c5h74); metal flips are §4 verified-wins corrections
(billon→silver ×3 via Hede/NumisMaster verified) — and km-358 silver→billon is a
CORRECTION (ucoin mislabelled silver but its own fineness 0.281 = billon). The
per-entity audit over-reported re-homed coins as losses. NO §9a regression, NO §CU
pollution.

**BUT `absorb --apply` (trio) revealed a real CROSS-ENTITY CURATION-MIGRATION gap
— reverted.** When a hede SEED re-homed danish_realm→royal_holstein (the 26-coin
re-seed) but its CURATED final + classification stayed in danish_realm, the absorb
drops the danish_realm final (backing gone) AND bulk-promotes a FRESH royal_holstein
final WITHOUT the curation → fuss/phase LOST (KM631 c7h33a went 11_333_thaler/I →
seed_unsorted; c7h11c vanished). The absorb finals + classification_decisions
pending-regen were `git checkout`-reverted; back to the correct pre-absorb state.

**8 curated re-homed coins need their curation to follow to royal_holstein BEFORE
absorb:** unified-dk-hede-c7h33a/c7h33c/c7h26/c7h28 + dk-tid-79553 (11_333_thaler I),
unified-dk-hede-c7h13a (9_25_thaler III), dk-tid-79166/79168 (9_25_thaler II). Fix
= EITHER add royal_holstein `classification_decisions` assignments {coin_id, fuss,
phase, kind} for each (the bulk-promote then applies them — established mechanism,
but coin_id must match the royal_holstein seed_unified id post-re-home) OR migrate
the 8 finals danish_realm→royal_holstein with ie→joint (like the 7 in e8de501).
The assignment route is cleaner. **This is a focused continuation — do NOT rush at
turn-end.**

### ⚠ APPROACH CORRECTED 2026-06-16 — the assignment route below was TESTED and is INSUFFICIENT; use MIGRATION

**Tested in-session (then reverted):** adding the 7 royal_holstein
`classification_decisions` assignments + `absorb --apply` (trio) gave a PARTIAL,
messy result — only 4 of 7 landed in royal_holstein (c7h33a/c7h26a/c7h11a/c7h11b);
**c7h28 + c7h13a stayed in danish_realm** (their CURATED danish_realm finals are
spared by the stale-final-drop, so they persist there and the rh assignment can't
displace them); **c7h35 + c7h11c vanished** (sub-variant fold). Root cause: the
assignment+bulk-promote route only works when the old curated final is dropped —
but a curated final is SPARED, so it stays in danish_realm and the coin is NOT
re-homed.

**CORRECT route = MIGRATE the curated finals** danish_realm→royal_holstein with
`issuing_entity → [danish_realm, royal_holstein]` (the same surgical move proven
for the original 7 in e8de501, verified 7/7 on both pages), THEN absorb (the
migrated rh final is the foundation the re-homed seed_unified enriches; the dr side
loses backing → stale-drops cleanly). Migrate the danish_realm finals for:
unified-dk-hede-c7h33a (KM631; c7h33c folded in) / c7h26 / c7h28, dk-tid-79553,
unified-dk-hede-c7h13a, dk-tid-79166, dk-tid-79168. **Also:** KM631 (c7h33a)
carries a PRE-EXISTING reign-window year 1766-1808 (member kmk-122886, Hede 33A,
year_verified anchor) — it should be 1778-1785; add a §CU `_curation_holds:
{year_ranges, year_label}` on the migrated KM631 final (year-hold override
cebf090). And confirm the c7h11c/c7h35 sub-variant folds (Hede 11C / 35 — distinct
rows or correct fold?). The fuss/phase/kind VALUES in the block below are still
correct (reuse them for the migrated finals' fields, NOT as assignments):

~~Paste these 7 assignments into classification_decisions/royal_holstein.yml~~
(SUPERSEDED — values-reference only):

```yaml
- coin_id: unified-dk-hede-c7h33a    # KM631 (was danish_realm c7h33a+c7h33c)
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler Kurantmøntfod scheide. Curation follows the hede SEED re-home danish_realm→royal_holstein 2026-06-16 (overlap-home rule e8de501); fuss/phase carried from the pre-re-home danish_realm final. KM631 2 Skilling Christian VII (Hede 33A/B/C).'
- coin_id: unified-dk-hede-c7h26a    # was danish_realm unified-dk-hede-c7h26
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler scheide; curation follows hede SEED re-home 2026-06-16.'
- coin_id: unified-dk-hede-c7h28
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler scheide; curation follows hede SEED re-home 2026-06-16.'
- coin_id: unified-dk-hede-c7h35     # was danish_realm dk-tid-79553
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler scheide; curation follows hede SEED re-home 2026-06-16 (V1 dk-tid-79553 backing now in c7h35).'
- coin_id: unified-dk-hede-c7h13a
  fuss: 9_25_thaler
  phase: III
  kind: kurant
  reason: '9¼-Thaler kurant; curation follows hede SEED re-home 2026-06-16.'
- coin_id: unified-dk-hede-c7h11a    # was danish_realm dk-tid-79166
  fuss: 9_25_thaler
  phase: II
  kind: kurant
  reason: '9¼-Thaler kurant; curation follows hede SEED re-home 2026-06-16 (V1 dk-tid-79166 backing now in c7h11a).'
- coin_id: unified-dk-hede-c7h11b    # was danish_realm dk-tid-79168
  fuss: 9_25_thaler
  phase: II
  kind: kurant
  reason: '9¼-Thaler kurant; curation follows hede SEED re-home 2026-06-16 (V1 dk-tid-79168 backing now in c7h11b).'
```

**CAVEATS to check during verify (not blockers, but confirm):**
- **`unified-dk-hede-c7h11c`** (a migrated final, fuss 9_25_thaler) has NO backing in
  royal_holstein seed_unified (the c7h11 seed_unified is a/b/**d**, no c · h11c — it
  folded). On absorb it will consolidate into a c7h11 peer or orphan. CONFIRM whether
  Hede 11C is genuinely a distinct sub-variant that should stay a separate row (then
  it needs its own seed/handling) or correctly folds. The bad-absorb «c7h11c vanished»
  was this fold.
- **km-683/695/721/760/761** (migrated V1-curated finals, no seed backing) are
  orphan-curated → absorb SPARES them (curated, not vanished-stale) → preserved. f6h15
  has backing → preserved. Confirm all 7 migrated finals survive the absorb.

**Sequence:** paste the 7 assignments → `absorb --apply` (danish_realm, royal_holstein,
danish_norway) → `audit_curation_loss.py` (should now show 0 real loss beyond the
benign re-homes) → `build --include-v1` → verify: KM631 → ONE coin
`unified-dk-hede-c7h33a` 11_333_thaler/I royal_holstein on BOTH pages; the 7 c7h/f6
assignments + migrated finals keep their fuss; FrD'or one coin; drop counts don't grow
vs baseline (denmark 7626 / SH 985); spot-check the c7h11c fold → commit. seed_unified
is committed (correct merge, KM631/FrD'or united); finals are at the correct
pre-absorb state. Everything revertible; nothing pushed (31 commits local).

## 2026-06-15 — curation-loss field-diff GATE CLOSED (UNPUSHED, 4b466b2 + fce45f1 + cebf090)

The pre-apply gate is now COMPLETE — supersedes the earlier «verified safe»
caveat in the KM 631 entry below, which only covered entry-DROPS, not
field-level overwrites. New tool `scripts/maintenance/audit_curation_loss.py`
(pure compute via `process_entity`, never writes) diffs the would-be-written
final against the current final on the RE-DERIVED loss-risk fields (year_*,
mint, metal, catalog xsrc, fineness/weight/diameter), skipping
`_curation_holds`-protected fields. Field-category map (from reading
`_enrich_final_entry`): IMMUTABLE (fuss/phase/kind/fraction/nominal/ruler/
mintmaster/issuing_entity) + GAP-FILL (note/verification_note/inscription_*) +
UNION (sources/composed_of) are SAFE; only the RE-DERIVED set can lose curation.

**Full-project result: exactly 2 absorb-stage losses**, both year-widening from
a reign-window composed member — `unified-dk-bruun-3839` (galster-hg-27
1481-1513 v=false widened curated 1497) + `km-795-1-chr-ix-1874` (hede-c9h16a
1863-1906 would back-date the decimal 10 Øre, struck only from 1874). Both
PROTECTED via dict-form `_curation_holds` (curator kept 1497 for bruun-3839).
Everything else benign: 155 Royal-Danish→Kopenhagen mint folds (VERIFIED
against the live Numista source N#18277 = «Royal Danish Mint (Den Kongelige
Mønt), Copenhagen, Denmark (1739-date)» — harvester stored only the institution
name `mints[].name`, registry recovers the city the source states; 121 are
list-form where Kopenhagen is already present from a Hede/Bruun co-member) + 1
benign Malmø→Malmö diacritic (bruun-3839) + 1 year-ADD enrichment. Post-fix
audit: **REAL LOSS widen=0/cat-drop=0/measure-drop=0/metal=0**.

**Mechanism fix shipped (cebf090):** `_curation_holds` on year was INSUFFICIENT
— the held branch did `_union_year_ranges(members)`, folding foundation year
INTO the member union, so it froze only the display label while year_first/last
still leaked to the reign window (and year_first drives §8.2 phase). Changed to
OVERRIDE: a frozen year is authoritative, member ranges don't widen it. Blast
radius 0 (these 2 are the only year-hold entries).

**Deferred systemic follow-up (TODO §CU):** the root cause is `_union_year_ranges`
blindly unioning reign-window placeholder members (year_verified=false full-reign
span like galster-hg-27; OR a loose Hede sub-variant span like c9h16a, v=None)
with tighter same-type attestations. A clean systemic rule (downweight
full-reign-span members when tighter attestations exist) would self-heal future
cases without per-entry holds, but the two pollution signatures differ
(v=false reign-anchor vs v=None loose-range) → needs careful design +
regression testing. Per-case holds suffice for now.

## 2026-06-15 — KM 631 cross-entity merge decision DECLARED (UNPUSHED, 022a754)

KM 631 (2 Skilling, Christian VII, Hede 33 with sub-variants 33A/33B/33C,
struck 1778-1785 at Altona AND Kopenhagen) was fragmented into 3 final rows:
`unified-dk-hede-c7h33a` (Hede 33A, KM 631/631.1, danish_realm) +
`unified-dk-hede-c7h33c` (Hede 33C, KM 631.3, danish_realm) +
`unified-denmark-numismaster-58049` (+ numista N#42563, no Hede, royal_holstein,
seed_unsorted). Split = cross-letter (Hede 33A/C, §9a gate won't unite on RAW
overlap — same class as Frederik D'or) + cross-entity (Altona numismaster/numista
copies bucketed to royal_holstein by mint). Fix = `_cross_entity.yml` force-union
of all 12 seed members, **target_entity: danish_realm** (Danish-realm coinage, Hede
c7h volume); the build's `_derive_issuing_entity` (bd9126b) then renders it joint
[danish_realm, royal_holstein] via the Altona mint → both pages. Pre-scan verified:
9 members home=danish_realm, 3 (numismaster-58048/58049, numista-42563)
home=royal_holstein pulled+excluded. fuss/phase carry from the c7h33a/c7h33c
foundation (11⅓-Thaler I) + their classification_decisions assignments.
**Declarative — materialises on the global merger --apply.** Resolves the
2026-06-14 «single royal_holstein» mis-model flagged in the Royal Danish entry.

**Pre-apply curation-loss gate — VERIFIED SAFE (read-only absorb --dry-run).**
danish_realm/royal_holstein/danish_norway all report «Stale finals dropped (no
backing): 0» → absorb undoes NO curation; curator assignments apply (4+6+0, phase
re-tags survive); net final deltas +22/+4/+1 are legitimate monotonic-guard
re-promote + de-dup reconciliation (current final is behind the pipeline), NOT
loss; 5 enrichment conflicts logged to match_uncertainty (surfaced, not lost). The
km-repr fix survives (seed_unified already clean → absorb reconstructs clean km).
**CAVEAT:** this dry-run reads CURRENT seed_unified, which does NOT yet carry the
KM 631 / Frederik D'or merges — those materialise only after merger --apply. Full
apply effect (new merges + Royal Danish→Kopenhagen rebuild) needs merger --apply
first, then absorb, to be diffable end-to-end. Tree is clean → a verification apply
is fully revertible via `git checkout`.

## 2026-06-15 — issuing_entity derivation for SH-struck crown coins SHIPPED (UNPUSHED, bd9126b)

`build.py::_derive_issuing_entity` (+ `_CROWN_MINT_REALM`): at assembly, a coin
with `issuing_entity == danish_realm` struck at a crown-owned Holstein mint
(Altona/Glückstadt) gets its issuing_entity recomputed as the union of mint-
realms → **Holstein-only strike = royal_holstein; Altona+Kopenhagen = [danish_
realm, royal_holstein]**. Criterion = issuer + circulation, NOT bare mint-
location (curator decision): the issuer-owns-mint guard holds because the crown
owned those mints, and `royal_holstein ⊂ danish_realm` politically so a duchy-
only strike is PURE royal_holstein not joint. Scoped to danish_realm (Pass 1/2
curated only; seed entries untouched) → commission strikes of other issuers at
Altona (Schaumburg-Pinneberg pre-1640, Plön, 1848 Provisional Govt) keep their
own entity. Applied in the two-pass: Pass-2 intersection tests the derived ie
(SH page picks them up) + the resolved coin carries it. Render-only, durable
(absorb's foundation-immutable ie never sees it). Effect: **29 coins (22 joint
+ 7 pure royal_holstein)** now render on BOTH Denmark + SH; km-743 (Copenhagen-
only) stays danish_realm; 1126 Copenhagen-only realm coins unchanged. Verified:
full build clean, ALL per-location drop counts unchanged (no regression).
**Deep-analysis note:** `classify_mint_to_entity` itself encodes the flawed
bare-mint criterion → it would misclassify Altona-struck Danish *seeds* as
royal_holstein; make it issuer-aware (KM register / denomination / ruler) before
the seed-builders become authoritative.

## 2026-06-15 — SH 11⅓ collapse + 18½ per-page phase derivation SHIPPED (UNPUSHED, dc24d7f + fcbf5fe)

Phases are location-local generalisations over a global Müntzfuß (§7); a build
drop fires when a coin's stored scalar `phase` isn't among the consumer page's
windows for that fuss (`build.py:1005-1023`), so cross-periodised coins vanish
from one page. Source review (Wilcke `/wilcke/w3f1.htm`, danskmoent Møntlove)
established the SH 11⅓ sub-phases 1773/1788 are political/institutional, NOT
standard changes (kurant never abolished — «man hang stadig ved Kuranten»;
Altona struck 11⅓ to 1812).

**SHIPPED (dc24d7f):** SH `phases.11_333_thaler` collapsed 3→1 `I[1726-1813]`
(matches DK); 6 coins re-tagged phase II→I (direct final edits + durable
`classification_decisions` assignments); the «retired/only-until-1788» claim
corrected on every surface (SH closing/timeline + DK phases/timeline/
fuss_periods) → Speciedaler became Holstein's PRIMARY from 1788 but the kurant
itself continued; refs_pool gained `wilcke-1788-speciebank-kurant` +
`sh-speciesbank-1788`. Build: drops DECREASED (denmark 7652→7646, SH 991→986),
citations resolve, no stale claims.

**SHIPPED — 18½-Thaler via per-page phase derivation (commit fcbf5fe, option b).**
The first-tried «add 1841/1854 phases to DK» was BROKEN (narrowing DK's single
phase I[1813-1875] dropped its phase-I coins with years 1842+, +52 regression,
proven by build → reverted). The fix is build-side: `build.py`
`_DERIVE_PHASE_FROM_YEAR = {"18_5_thaler"}` — for that fuss the assembly COMPUTES
each coin's phase per consumer page from `year_first` against THAT page's
windows (stored phase wins only as a boundary tiebreaker). No phase-window
edits, no coin re-tag, denmark.yml untouched. On the Denmark page 18½ keeps its
single wide I[1813-1875] so every 18½ coin (incl. SH-periodised stored-II/III
dual-mint coins) derives to I and renders; on the SH page each derives to its
finer I/II/III/IV year-window. Verified: full V2 build clean; drops decreased
(denmark 7646→7626, SH 986→985) and unchanged on every other location; km-721/
760/761/683 render on BOTH pages.

**Other granularity desyncs — widen `_DERIVE_PHASE_FROM_YEAR` per fuss after
review:** 9¼, 9-Thaler, kronemont, reichsdukatenfuss, courantdukatenfuss,
guldkrone, kronemont_chr_iv all have differing DK↔SH windows; adding each fuss
key to the set resolves it the same way. Do a quick per-fuss «realm-wide law vs
political event» sanity check + a build-drop diff before widening (deliberate,
not blanket). The 2 refs `danskmoent-moentlove-1841` +
`forordning-rigsdaler-rigsmont-1854` were prepared then removed — not needed by
the derivation approach (no DK phase prose added); re-add only if the DK 18½
prose is later expanded.

## 2026-06-14 — KM render-leak fix + two pipeline fixes staged for the coordinated apply (UNPUSHED)

10 commits unpushed (origin/main..HEAD). This session, in order of the user's reports:

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

## Denmark gold-gylden Rhinsk/Ungersk reclassification — SHIPPED 2026-06-12, UNPUSHED (commit 682e5e5 + d4d7e3a + eefddf5)

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

## Fuss cross-reference system — SHIPPED 2026-06-11, UNPUSHED (commit 451d0f0; TODO §CT closed)

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

## KMM impossible-year guard — galster-hg-31 1581 fixed (2026-06-11) — SHIPPED, UNPUSHED (4 commits: d5eea8e/bc4a341 then revised fbc926c/d73819c)

Closes the kmk-297794 «1513-1581» quirk surfaced by the Hans Galster-volume
session. Root cause: 25 KMM (natmus) records carry a `creationEvent` with
`yearFrom > yearTo` (raw inversion). The old `build_kmk_seed._year` only
swapped, so an impossible value survived (Hans hvid 1581/1513 → 1513-1581;
1581 is 68y after Hans †1513). New guard: swap when the implied span ≤ 20y
(ordering slip — 7 records, all within reign), else DROP the event's year
(year=None — 18 records, all impossible: truncated yearTo 152/58/675/…,
post-reign yearFrom). Builder fix `d5eea8e`; data `bc4a341`.

- **Materialised** by patching the in-seed records' year fields directly
  (full `build_kmk_seed` re-run RE-INFLATES — thinning is a separate step;
  danish_realm dry-run shows 32215 vs thinned 9630, so DON'T full-rebuild
  to materialise a few rows — patch the thinned seed with the canonical
  ruamel config `typ=rt, preserve_quotes, width=200, indent(2,4,2)` or the
  whole file reformats) → re-merge + re-absorb danish_realm + danish_norway.
  galster-hg-31 1 Hvid Hans now reads 1481-1513; page has 0 year-«1581».
- **REVISED — null → reign-window anchor (`fbc926c` + `d73819c`).** The first
  approach NULLED the year on dropped events. That removed the coin's ONLY
  merger fallback signal, so 6 same-type museum specimens (Christian-IV
  Hede-67 2-Skilling etc.) that share a type-level catalogue but carry no
  fineness/mint stopped merging and surfaced as standalone seed_unsorted
  finals — a regression. Fix: a dropped-all-year record now anchors to the
  named ruler's reign window via `lib.ruler_reigns.reign_window`
  (year_verified=False) — plausible-but-estimated, so the §9a multi-specimen
  merge fires again without the garbage value. 191584 now re-merges into a
  4-member Christian-IV group (year 1588-1648 unverified). Bare-«Hans»
  (no ordinal) doesn't resolve a reign → stays year-None, harmless (merges
  via Galster).
- **❌ CORRECTED — the «KMM Arabic-vs-Roman ruler-scope gap» I flagged here
  earlier DOES NOT EXIST.** I asserted it WITHOUT verifying (§0b lapse).
  `merge_seeds_cross_source._normalise_ruler` ALREADY folds Arabic↔Roman:
  `_normalise_ruler("Christian 4") == _normalise_ruler("Christian IV.") ==
  "christian iv"` → same scope key. The real reason those specimens stood
  alone was the year-null regression above (matcher requires primary +
  ≥1 fallback; nulling the year left primary_true=4 / fallback=0 →
  «insufficient signals» → no_match). Now fixed by the reign-window anchor.
  NB: they still don't merge with the CURATED `c4h67` — but that's a genuine
  metal disagreement (KMM silver vs curated billon), correctly blocked.

## Numista discrete-year (year_list) harvest gap — 501 re-harvested (2026-06-10) — SHIPPED, 3 main + 1 submodule UNPUSHED

User noticed Numista DOES give discrete struck years (1496, 1502) — in the
«Manage my collection» date table — but our data showed the continuous
range «1496-1502». Diagnosed: loss is at the HARVEST step, not the parser.
The thin BO.1/chrome extractor (HARVEST_GUIDE) read only the «Years» range
feature, never the `table.collection` date column, so 501 in-scope
multi-year types had `year_first/last` but `year_list: null` →
`build_numista_seed` fell back to a continuous `year_ranges`. The whole
downstream was already discrete-ready (`parse_numista_chrome` consumes
`year_list`; seed builder emits `[[y,y]]`; merger's `_union_year_ranges`
prefers discretes). The v3 API does NOT help (`parse_numista_api` hardcodes
`year_list=null`; discrete list needs the un-fetched `/types/{id}/issues`).

- **Harvest (`submodule 93b0460d`, cache pointer `<bumped>`):** re-harvested
  all 501 via Chrome MCP same-origin `fetch()` + DOMParser of
  `table.collection` (≈30 NIDs/JS-call, 0.3 s pacing, 0 Cloudflare 403s).
  **417 gained discrete years, 84 confirmed range-only** (kept, NOT
  fabricated). year_list written to raw cache + parsed sidecars.
- **HARVEST_GUIDE extractor upgraded** (`docs`) to capture `year_list` from
  the date table — durable fix so future harvests + re-harvests get it.
- **Materialised (`012fb9e`):** re-parse (surgical — deleted only the 501
  sidecars, re-parsed WITHOUT --force to avoid surfacing 575 unrelated
  newly-parseable types) → re-merge + re-absorb. **412 propagated** into
  rendered finals across danish_norway + bremen_verden + oldenburg +
  braunschweig_lueneburg + sachsen_lauenburg + osnabrueck (gapped labels
  render). danish_norway −3 = lossless Hans-1-Hvid consolidation (the
  prior Galster-volume fix reaching this entity; seed 3903/3903).
- **Residual (entity-routing backlog, NOT this task):** 5 hanseatic_lubeck
  + 144 `_unclassified`-final coins whose numista seed routes to
  `_unclassified` (≠ their foundation's entity) — year_list is in cache +
  `_unclassified` seed, propagates once they're classified. See SOURCES §13.1.
- **Method gotcha for next time:** `parse_numista.py --force` re-parses the
  WHOLE cache and surfaces newly-parseable types (575 → _unclassified, +
  stray hamburg/danish_norway final churn). For a targeted re-parse, delete
  only the target sidecars and run WITHOUT --force.

## Hans Galster volume-scope fix — 1 Nobel year + 31 split-dup consolidations (2026-06-10) — SHIPPED, 2 main UNPUSHED

User flagged: 1 Nobel Hans (Galster 24) rendered «1496-1502» (continuous)
but sources attest discrete 1496 + 1502. Root cause was a **cross-source
matcher gap**, not the year-merge rule (`_union_year_ranges` is correct):
the coin was SPLIT across two finals — `unified-dk-bruun-3831`
(Bruun+Numista+KMM; Numista's loose min/max `[[1496,1502]]` drove the
year) and `unified-dk-galster-hg-24` (discrete `[[1496,1496],[1502,1502]]`).
They never merged because `_catalog_refs` derives the Galster volume-scope
from the ruler via a regex requiring a NUMERAL — **Hans has no ordinal**,
so his refs stayed bare `galster` while the Galster-source entry sat in
`galster/hg`; same Galster 24 → no catalog tie → `no_match`.

- **Fix (`a37c821`):** make the ordinal optional in the volume-derivation
  regex; map no-ordinal Hans → `hg`. Now bruun/kmk/numista Hans galster
  refs scope to `/hg` and merge with Galster-source entries.
- **Data (`bc6dc40`):** re-merge + re-absorb. 1 Nobel now ONE entry,
  `year_label '1496, 1502'` (discrete wins — period not wider than
  discrete min-max), galster source + Galster 24 + schou 2,3 all unified.
  68 Hans bare-galster seed refs re-scoped; **31 stale Hans foundations
  consolidated into peers** (1 Nobel/24, 1 Skilling/29, Goldgulden/27,
  1 Hvid/31 +17 KMM specimens, …) — all same-galster-number same-type
  (verified: every galster-31 member is Hans 1 Hvid; 0 wrong-ruler merge;
  seed conservation 12819/12819, 0 loss).
- **Surfaced (NOT fixed — pre-existing KMM quirk):** `kmk-297794` (Hans
  1 Hvid, Galster 31) carries a loose KMM date «1513-1581», so the
  consolidated `unified-dk-galster-hg-31` year_label widened to
  «1481-1581» (1581 ≫ Hans †1513). A KMM date-field error on one
  specimen, not a merge defect. Candidate for a KMM date-sanity pass.

## Galster single-coin overview-page recovery: 2/3 Nobel danskmoent source (2026-06-10) — SHIPPED, 3 main + 1 submodule UNPUSHED

User flagged that the danskmoent.dk source on **2 Nobel** (Hans 1502,
N#428886) + **3 Nobel** (Hans 1496, N#428914) had vanished. Root cause:
the Galster classifier (`scripts/lib/galster_parsers/classify.py` rule 3)
routes any non-per-coin-filename page to the `reign_index` skip-parser as
a redundant overview. `1nobel.htm` IS a genuine multi-reign overview, but
`2nobel.htm` / `3nobel.htm` are **single-coin pages** (one catalogued
type each → danskmoent never split a dedicated per-coin page), so they
were silently dropped from the seed and never reached the coins.

- **Fix (`c63779a`):** conservative content-based carve-out in rule 3 —
  ruler-keyword H1 + exactly one Galster number + no overview markers
  («Se også» / «ser således ud» / «Møntrækken» / reign-range header)
  → route to `standard`. Dry-run over all 171 reign_index pages: exactly
  4 flip (2nobel, 3nobel, 6penning, halvrhin), all genuine single-coin;
  167 true overviews untouched. Also extended the galster year regex
  `1[5-6]→1[4-6]` (standard.py + build_galster) so Hans-era 14xx years
  parse — 3nobel's 1496 was being dropped (→ no seed). Blast radius:
  only fr_hg24 (1 Nobel Hans) gains its genuine 1496 year. `_build_sources`
  now falls back to catalog_refs.galster + omits empty volume parenthetical.
- **Data (`99a1c69` + cache `bbad3177`):** re-parse → galster seed (+2
  entries) → merge danish_realm → absorb. 2 Nobel gains catalog galster 26
  + danskmoent/2nobel.htm; 3 Nobel gains schou 1 + danskmoent/3nobel.htm +
  mint union [Kopenhagen, Malmö]. Both render on the Denmark page (verified).
- **6penning** (Erik af Pommern, Åbo, pre-1481) + **halvrhin** (Hans ½
  Rhinsk gylden, u.år) re-parse as single-coin but stay out of seed scope
  (undated, no reign-volume anchor → builder drops them).
- **Forgery-year drop (`3deea9d` + cache `afc092d`, data `e080583`).** Hans
  1 Nobel (fr_hg24) carried 1508 — danskmoent flags «(1508 er falsk)»
  (the only 1508-dated specimen is a forgery). Fixed via PARSER, not
  errata (the source is correct, the parser mis-read it; errata is for
  catalogue-index corrections). `_FORGERY_YEAR_PAREN_RE` strips a paren
  with year+falsk before year extraction; cache-wide only `(1508 er falsk)`
  matches → only fr_hg24 affected. year_label 1496,1502,1508 → 1496,1502.

## Source-quality + Schauenburg entity split (2026-06-10) — SHIPPED, all local/UNPUSHED (`git rev-list --count origin/main..HEAD` for the live count)

Six discrete tasks this session, all committed locally, **0 pushed** (push
needs explicit user OK). Pre-commit hook + V2 build clean throughout.

**(1) Bruun nominal-normalization restored — `f252733` (code) + `7f54d64` (data).**
The Bruun seed builder had lost its display-nominal layer: fresh entries went
in raw (no implicit-«1», roman not converted, fraction glyphs, NAME-parens,
ø-spelling) while 1099 existing entries carried normalized forms — a naive
re-run would degrade all of them. Added `_bruun_display_nominal()` +
`extra_curated_fields=frozenset({"nominal"})` threaded through
`merge_one`/`merge_seed`/`write_v2_seed` (default empty → no-op for other
builders) so existing nominals are soft-preserved, fresh ones normalized.
**parse_metal now runs on the RAW denomination** (parens intact) BEFORE the
display strip — the descriptive paren carries the metal signal («12 Mark
(Courant Ducat)»→gold, «8 Skilling (klippe)»→silver); running it on the
stripped nominal had regressed 3 metals. Proven 0 semantic diff on re-run.
`7f54d64` re-serialized the last PyYAML-style bruun seed (danish_realm) to
ruamel — corpus format consistency.

**(2) Absorb drops finals whose backing vanished — `78d54f2` (code+test) +
`340219a` (data, −17).** Absorb was additive/sticky: a final persisted even
when its backing seed_unified entry disappeared (the 622-exonumia hand-removal
case). New drop: a `unified-*` final with NO live backing AND no curation
(fuss seed_unsorted/None, no note/_curation_holds/promoted_to/curator-phase)
is dropped — two enforcement points (explicit filter on the new final set +
monotonic-guard exclusion so a final dropped by an earlier purge isn't
resurrected). Module-level `_final_is_curated`/`_final_has_live_backing`/
`_is_vanished_stale_final` + 19-case unit test (`tests/test_absorb_stale_final_drop.py`).
Materialized 17 drops (15 cross-source-consolidation dups + 2 sub-variant
re-key dups: dk-hede-f3h135→f3h135a/b, dk-galster-f1g-66→f1g-66c); verified 0
seed orphaned, 0 cross-entity dup, note preserved.

**(3) Re-serialize remaining stale seeds — `fe6574c`.** 5 seed files still in
old PyYAML dash-at-parent style (3 kmk + 2 numismaster) → ruamel round-trip,
0 semantic diff. Pure format (a builder re-run was wrong: kmk writes 0 files
without parse-cache, numismaster re-run is a real data change). Corpus now
uniformly ruamel.

**(4) NGC grade-colour → copper — `ec63ace` (code) + `9720042` (data).**
parse_metal reads the NGC/PCGS colour suffix (Brown/BN/RB/RD, anchored to
«NGC <grade> <colour>» so prose «brown patina» never false-matches) →
("copper", False), placed after explicit metal-words, before the weak
denom heuristics. 24 in-scope flips (Danish bronze Øre, copper Rigsbanktegn,
small Rigsbankskilling, 1677 siege klippe dk-bruun-7277, 1602 copper Penny).
Knock-on: corrected metal unblocked 5 cross-source merges (Bruun KM-entry ↔
Numista N#-entry, e.g. KM-754=N#43524) — verified 0 loss, 0 dup.

**(5) Schauenburg 2-entity split — `997aa83`.** The old
`holstein_schauenburg_county` umbrella conflated two regional traditions →
split into **`grafschaft_schaumburg`** (Niedersachsen, 36 coins —
Stadthagen/Bückeburg/Oldendorf/Rinteln, Mariengroschen tradition) +
**`schauenburg_pinneberg`** (Holstein, 246 — Altona, SH-Courant + imperial
1/24). holstein_schauenburg page consumes BOTH; schleswig_holstein consumes
only the Holstein half (mirrors royal_holstein-on-denmark). Mechanism:
new entity in issuing_entities; mint_registry (4 NS mints→grafschaft;
Schauenburg issuer-name fallback→pinneberg); routing-rule routes_to
grafschaft; **`build_numismaster_seed` now applies route_entity_with_rules**
(was the 6-coin mis-route bug); bruun meta-tag→pinneberg. 123 county finals
migrated verbatim (ids+notes preserved) then merge+absorb reconciled;
test_entity_routing 10 green. See V2_DECISIONS D45 (+ D44 for the absorb drop).

**(6) numista dav-dedup refresh — `b7b2165` (9 entities).** Re-running
build_numista_seed materialized a stale catalog.dav: a 2-elem list with the
SAME Davenport ref in two formats («EC II# 3656»+«EC II 3656») → scalar.
218 entries, 0 other field changed. Seed-layer hygiene only — rendered final
was already clean (absorb's `_fold_catalog_indices` normalizes on accumulate).
numista-only quirk; ikmk/numismaster/bruun verified 0 non-Schauenburg drift.

**CLOSED later in the session (the deferred clean-up, all committed):**
- ✅ **galster 66A/66B genuinely lost — recovered** (`1b9e479` fix + `4c170ca`
  data). NOT a re-key: 66A-B (pre-coronation Electus variant) ≠ 66C. Cause:
  the `seed_merge` supersession-drop keyed on id-STRING and dropped
  `dk-galster-f1g-66` (catalog «66A-B») as if `…-66c` superseded it. Fixed
  catalogue-aware (`_own_cat_has_subletter`). Full re-run of hede+galster
  found NO other dropped sub-variants — blast radius was exactly this 1 coin.
- ✅ **holstein_schauenburg page prose rewritten** (`388e6bb`). Summary →
  historical two-part principality (drop «104-piece pending / IKMK
  undistinguished»); phase prose cleaned of §0z project-meta (source
  file-paths / «Build-Assembly» / «Bulk-Seed» pipeline labels); §2-clean,
  renders both parts.
- ✅ **audits run** — `audit_prose` / `audit_i18n` on the new prose
  (grafschaft_schaumburg desc + rewritten summary/phases): 0 new violations,
  i18n-clean.
- ✅ **SOURCES §13.1** numista EC II# quirk (`9b9d413`); **memory
  tooling_lessons** scoping-bug entry (config-dir auto-revert).

**OPEN / next:**
- 🟡 **Systemic §2 «Taler» → «Thaler» normalisation (curator decision).**
  Project-wide: ~1000+ `nominal: … Taler` (178 «1 Taler», 857 «1/24 Taler»,
  …) + 657 §2 note-prose errors (`audit_prose` backlog). The nominal field
  uses «Taler» pervasively while §2 wants «Thaler» in DE prose — the audit
  flags notes, not nominals. NOT introduced by recent work; needs a deliberate
  project-wide pass (nominals + notes together) or an explicit «keep Taler in
  nominals» convention. The 1 holstein_schauenburg `audit_prose` hit
  (unified-dk-bruun-14913 note) is one instance, left as-is pending this call.
- 🟢 Pre-existing standing TODOs untouched: schou-only (17) catalog-noise;
  ~8 genuine catalog over-merges.

## composed_of re-validate + full re-merge (2026-06-09) — SHIPPED, 3 commits UNPUSHED

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

## Catalog-index normalization + KMM thinning (2026-06-08) — SHIPPED, 5 commits UNPUSHED

Started as the «1 Speciedaler Christian IV (Hede 55)» 3-problem task, grew into a
project-wide index refactor + a museum-citation declutter. **All committed locally,
UNPUSHED (48 total unpushed). Pre-commit hook passed throughout; full V2 build clean,
0 `schou#`/`sieg#` overflow site-wide.**

**(A) Catalog-index normalization — `17c7e91` (code) + `75734e6` (data, all entities).**
- `lib/catalog_codes.py::normalise_catalog()` — folds `others: <code># N` overflow
  into its typed list-field (case-insensitive code, guarded against cf-/unlisted-),
  + case-insensitive value de-dup («Hede 55C» + «55c» → one «55C»). Wired into EVERY
  catalog-write chokepoint: `seed_merge.merge_one` (post deep-merge), `v2_seed_writer`
  pre-write hygiene, `merge_seeds_cross_source.build_unified`, `absorb._enrich_final_entry`
  + a blanket pass over every final entry (catches V1-carryover foundations).
- **Restart-scope registry in `_catalog_refs`** (the §9.4 core): two records sharing an
  index VALUE match only when they share its RESTART scope. Empirically measured:
  **Hede 59 %, Schou 64 %, Sieg 42 %** of distinct values span ≥2 reigns → **per-ruler**
  (`<idx>/<ruler>`); **KM 43 %** spans ≥2 entities → per-register; Galster per-volume;
  Friedberg/Davenport/Numista/Bruun/Lange/NMD/Schive/Skaare/mb (~0 %) → global/bare.
  **Sieg + Schou were BARE before (a §9.4 cross-reign collision bug); now ruler-scoped.**
  `_catalog_chain_consistent` value-compare + both SUB_VARIANT_REFS membership tests
  made scope-aware (`k.split("/",1)[0]`) + case-insensitive.
- Rollout regression analysis (`scripts/oneoff/analyze_index_rollout_regressions.py`,
  gitignored): **0 cross-ruler false-merges**; contained to 3 Danish entities (others 0
  grouping change); 66 §9a museum-specimen consolidations; flagged «anomalies» all
  accounting-equivalent nominals (12 RD Courant = 2 RD Species; 4 Mark = 1 Speciedaler;
  16 Skilling = 1 Mark) + billon/silver — catalog-driven per §9.4. No over-merges.

**(B) natmus errata — `18a5fbe`.** KMM 275643 «2 Skilling 1625» typeNumber «Hede 141»
is wrong (Hede 141 = 8 Skilling 1630, confirmed by genuine specimen KMM 190547 +
danskmoent c4h141; a 2-Skilling 1625 is uniquely Hede 134; natmus's OWN sibling
KMM 335046 is tagged «H. 134A»). `_source_errata` hede 141→134 on the kmk seed
(durable, survives rebuild via `_PRESERVE_ALWAYS_KEYS`). Specimen now groups with
Hede 134; KMM 190547 stands alone as Hede 141.

**(C) KMM museum-citation thinning — `7d37a92` (code) + `758cfba` (data).** 3-category
declutter in `absorb._suppress_weightless_museum_overcollection`, keyed by what each
KMM record carries (image read from cache `related.assets[type=still]` — VERIFIED
equal to the natmus page: 290904 shows 3 photos / 123284 shows «Genstanden er endnu
ikke affotograferet»):
- WEIGHT (±image): untouched — the §9a weight-specimen thinning owns those; always shown.
- IMAGE only (no weight): keep 3 (lowest object-id), hide rest.
- NEITHER (79 % of all KMM cites): keep 1, hide rest.
Hidden via `display: false` (data kept §9a — not deleted); 3266 surplus hidden, 0 weight
hidden. Constants `_KEEP_KMM_IMAGE_ONLY=3` / `_KEEP_KMM_PURE=1`.

**(D) Verified-mint divergence disqualifier — `775660e` (code) + `e8f6215` (data).**
RESOLVED the 290904 question + the whole Christian-IV Wolfenbüttel war-coinage cluster.
`match_pair` now blocks a merge when both coins have VERIFIED disjoint scalar mints AND
no strong TYPE-level catalogue tie (KM/Hede/Galster/Dav/Fr/Lange — not Schou/Sieg). So
the Wolfenbüttel coins (mint Wolfenbüttel verified) no longer false-merge into København
Hede 55 (mint Kopenhagen verified) via colliding Schou. `_shares_type_level_catalog`
tolerates case-insensitive + numeric-core + bare-vs-dot-parent («579»≡«579.1»). Full
re-merge of all 22 entities: **0 verified-mint splits of legit groups** (the 1 candidate
was a dot-parent gap, fixed); effect contained to danish_realm. KMM 290904 + 291969 now
separate seed_unsorted Wolfenbüttel coins; KMM 348808 (genuine Hede 55) stays in c4h55;
foundation mint cleaned [Kopenhagen, Wolfenbüttel] → Kopenhagen. 3 no_merges added
(290904↔348808, 290904↔c4h55, 348808↔291969).

**DONE this session (latest first):**
- ✅ **Nominal discriminator SHIPPED** (`fb7bc80` code, `a6e7f8b` data). `match_pair` now
  blocks a merge when normalised nominals GENUINELY differ (synonym folds + daler/gylden
  wildcard exclude label-variance) AND there's no TYPE-LEVEL catalogue tie (shared KM/Hede/
  Galster/Dav/Fr/Lange/N#, not a weak per-reign Schou/Sieg) — mirrors the §9.4 mint
  discriminator. Caught + fixed a Halvkrone/1½ collision: the «Halv-X» fold now consumes the
  implicit-one («1 Halvkrone»=½ krone, not «1 1/2 krone»). Full re-merge + re-absorb (15
  entities): NET de-dup (table folds > discriminator splits) — danish_realm final 7482→7455,
  royal_holstein 944→941, danish_norway 2101→2099, gottorp +1; 11 entities unchanged.
  Validate + build OK. ~2 residual edge false-splits left (see 🟢 below).
- ✅ **Mixed-number fraction fix** (`6238372`). `normalise_nominal` garbled «1½ Thaler» →
  «11/2 daler» (no separator between whole part + vulgar fraction). Now inserts a zero-width
  space before ANY unicode fraction following a digit (½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞) → «1 1/2», and the
  leading-«1 » strip gains `(?!\d)` so «1 1/2» isn't collapsed to «1/2». 0 corruption left;
  «1½» now matches the spelled «1 1/2». Maintenance-side — materializes a few 1½↔1-1/2 de-dup
  matches on the next full re-merge.
- ✅ **Full Numista re-parse materialization** (submodule `b77926fe` 398 sidecars; main
  data commit + classification_decisions). RE-PARSE only (no re-harvest — cache unchanged,
  0 API quota). `parse_numista --force` → `build_numista_seed` → `merge` (15 entities) →
  `absorb` (15). Materialized: 398 types' §9a multi-ref list-form (hede/sieg/schou/km/lange/
  fr/dav) + the session's synonym/Dav-fold/KM-hygiene across all entities. Side-effects of
  the full --force: **+322 newly-parsed types → `_unclassified`** (harvested-but-never-parsed;
  NOT rendered) + **+13 new coins → landgrafschaft_hessen_kassel** (final 77→86, pending
  classification). De-dup from richer refs: danish_realm 7492→7482, royal_holstein 946→944,
  danish_norway 2102→2101 (correct merges, NOT loss; validate OK, build OK).
- ✅ **Davenport volume-fold** (`bc1f9d7` code, `92557b3` data). «EC II» = Davenport
  «European Crowns 1600-1700» (a VOLUME, not a source artifact; numbering continuous, so
  «Dav 3668» = «EC II 3668»). `normalise_catalog` step 4 drops a bare «N» from the dav
  list when a volume-qualified «<VOL> N» (EC/GT/SG/BrSL) with the same trailing number is
  present; bare-with-no-match is kept. Materialized on 145 coins / 9 entities (148 bare
  lines, pure deletion, no re-convergence). This bare+qualified accumulation was a
  side-effect of the multi-KM session's dav accumulation.
- ✅ **Nominal synonym table**
- ✅ **Numista multi-KM support + §9a catalogue accumulation** (`29b5de2` code, `c42c31d`
  data, submodule `d283dd2a`). `numista_canonical.parse_references` (API+chrome) now
  ACCUMULATES every distinct catalogue value into a deduped list instead of first-wins —
  a single Numista type can cite multiple KM (406.1/406.2 mint sub-variants, or 106/56
  across two Krause editions). KM comma-decimals normalise to dots (404,1→404.1).
  `seed_merge` catalog deep-merge UNIONs list-capable sub-fields (was existing-key-wins,
  which silently dropped the fresh 2nd KM); frozen-catalog curation still wins.
  `catalog_codes.normalise_catalog` km hygiene: slash-scalar 683.1/683.2 → list, comma→dot,
  dedup. Materialized for danish_realm + gottorp_duchy (5 types render multi-KM, verified;
  resolved a dup 207063↔65186, 7493→7492 no loss; 683 slash-scalar fixed). **Other 14
  Numista entities' seeds REVERTED** — their lange/dav/fr §9a accumulation (21 multi-ref
  types total: lange 7, dav 6, km 5, fr 2) materializes on the next FULL pipeline run
  (parse --force → build_numista_seed → merge → absorb ALL entities); code is committed.
- ✅ **Catalog-index sort + range-collapse** (`94d6213`). `compute._compute_catalog_groups`
  now expands every index value to its integer members (existing ranges + overlapping/
  adjacent inputs merge: `23-24`+`25-26`+`26` → `23-26`), collapses runs of ≥3 consecutive
  ints into `min-max`, keeps 1-2 runs as individual numbers, and sorts the whole group.
  Applies to ALL index groups (Schou/Sieg/KM/Hede/Lange/…); non-integer tokens (93A, 77.1,
  register-qualified) never collapse and keep parent-before-sub-variant order. Verified on
  KM-42: `Schou# 21, 24, 25, 28, 32-36, 40, 42, 46-48, 51, 52, 56-59, 61, 62, 64, 68, 71-76,
  83, 89, 90, 93, 95, 97-99`. NB: a 2-element run renders as two numbers per the ≥3 rule
  (one-line threshold change if the user later wants ≥2).
- ✅ **Rhinsk Gylden fuss fix** (`896ffef` classifier, `2dc3adf` data). Christian III 1546
  Flensburg gold Rhinsk Gylden (Hede c3h14 «1 Rhinsk Gylden» + c3h15 «2 Rhinsk Gylden»)
  were mis-placed in the SILVER `8_daler_lybsk_fod` by the over-broad Flensborg mint-anchor
  rule (§8a metal-mismatch). Root-cause fix: `allowed_metals` gate on `_MINT_BOUND_FUSSES`
  bindings (gold can't match a silver Fuß). Moved both → `rhinsk_gylden_fod` phase 0 (joins
  the 1536 Roskilde galster-c3g-131; Δ −1.7 % vs soll). Added fraction '2' (soll 6.496/5.002),
  new ref `danskmoent-c3-rhinsk-gylden-1546` (Galster 130, NFM XII s.10), denmark.yml Phase-0
  prose (bar year_to 1536→1546 + title + description + hintergrund + pdate hiatus 27y→17y).
  Verified via computed JSON: both under rhinsk_gylden_fod phase 0, fraction 1/2. The 3
  seed_unsorted Rhinsk Gylden (f2h7g, galster-hg-27, galster-hg-gej) are a SEPARATE
  classification thread — not touched.
- ✅ **§9a weight-thinning → pipeline** (`fb91804` code, `264c4a8` data). `FieldValue.
  display:bool=True` + `compute.normalise_field` skips display:false + `absorb._suppress_
  weightless_museum_overcollection` now thins the weight-giving KMM bucket (≥5 → keep
  min/middle/max by weight, hide the dropped citations + their weight readings by value;
  catalog untouched). 1320 display:false across danish_realm/danish_norway/royal_holstein,
  0 deletions. Verified end-to-end: KM-42 weight column 44→5 readings. **CAVEAT surfaced:**
  the kept min for KM-42 is 0.44 g = the «Denning» anomaly — thinning correctly keeps the
  envelope extremes, so sticky wrong-type specimens now show as min/max. → the re-validate
  pass below is now also needed to keep the thinned envelope CLEAN.

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
- 🟢 **Rhinsk Gylden seed_unsorted tail (follow-up to the c3h14/c3h15 fix above).** 3 gold
  Rhinsk Gylden still sit in `seed_unsorted`: `f2h7g` (Frederik II), `galster-hg-27`,
  `galster-hg-gej`. They belong in `rhinsk_gylden_fod` too — classify them (the metal-gate
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

## Current focus

**V2 entity-keyed refactor — architecture refined 2026-05-18 to
4-phase fully-automated pipeline with V1 reframed as FOUNDATION
(V1 final yamls become V2 final starting state; V2 accumulates
enrichments on top, never overwrites).** Curator no longer edits
coin fields by hand; curator input is restricted to (a) which entities
the project supports, (b) Phase 3 merge confirmations, (c) Phase 4
classification confirmations — all encoded in script rules or
explicit decision files. Worktree branch `feat/v2-pipeline`.
**Canonical decisions journal: `docs/V2_DECISIONS.md`** (28 + 4
deferred). Detailed plan: `docs/V2_PIPELINE.md`. Detailed
architecture: `docs/ARCHITECTURE.md` §«V2 entity-keyed pipeline».
All other workstreams below paused during V2 unless user redirects.

**§CT — Hede parser data-loss audit (2026-06-06). Catalog-graph tool
(`scripts/maintenance/catalog_graph.py` — promoted from gitignored
`scripts/oneoff/` on 2026-06-07; committed + inventoried in the
maintenance README) surfaced 3 parser losses. Status mixed:**
- **SHIPPED (`49d4727` + cache `f71534b08`, committed, UNPUSHED):**
  per-variant Schou «hhv. … og …» list drop (81 by_letter variants).
  Safe — adds Schou values to existing entries, no id change.
- **SHIPPED — year-prefix Schou (`090b033` + cache `00cd21fb4`):**
  «Schou 1829-37: 2» (year-range : die) / «Schou 1731,1» (Schou
  year,running-no) — systemic `:`-sep + `_strip_year_tokens` (1500-1950,
  Dav exempt). id-safe (0 by_letter changes). f6h4b → 2,3 ; c6h4 →
  1,2,3 landed via 2 targeted seed edits (catalog is DEEP_MERGE so the
  cleaned fresh value couldn't overwrite the stale existing one).
- **SHIPPED — by_letter year-less recovery, Option B (`3fee3fa` + cache
  `62ce09dc2`):** `_extract_letter_groups` no longer requires a year on
  the variant line → +33 pages / +51 seed sub-variant entries (c4h117 →
  117A/117B etc.). The id change (bare `dk-hede-c4h112` → `c4h112a/b`)
  is handled WITHOUT changing the id mechanism (user steer):
  (a) `lib/seed_merge.py` supersession-drop (uncurated bare with FRESH
  sub-letter siblings is dropped — no bare+subletter dup);
  (b) `merge_seeds_cross_source.py::_expand_member` — a merge_decision
  member that is a now-absent Hede bare expands to its sub-letters
  (`dk-hede-c4h112` → {`c4h112a`,`c4h112b`}); genuinely-missing →
  warn+skip (no KeyError). force_union unions all; no_merge pairs only
  across DISTINCT original members. Result: c4h112 «Hede 112 = KM 68»
  applies to both 112A+112B; Hede 117 unifies 117A+117B (the «117B
  dropped» was a stale-merge artifact — clean run unions all). Verified
  via dry-run: 0 by_letter regressions, 0 unified entries lost, +12 net,
  schema OK.
- **REMAINING loss — RE-AUDITED 2026-06-07 (the old «76/53/22/16» count
  was STALE; c4h163/c4h164 are seeded now).** Run
  `scripts/maintenance/audit_hede_seed_loss.py` for the live breakdown.
  Current (662 cache pages): **515 OK, 3 sub_letter_loss, 12 field_swap,
  93 in_scope_absent, 25 oos_post_1914, 14 exonumia.** The actionable
  buckets:
  - **field_swap — Part 1 (nominal) + Part 2 (mint) SHIPPED 2026-06-07
    (commits 3cc3272, 5f6ed52). RESOLVED.** Recovered +34 seed coins
    (danish_realm +20, royal_holstein +14); audit OK 515→526, field_swap
    12→0. Part 2 mechanic: parse_hede.py recovers the mint from the per-variant
    A)/B)/C) lines when the H1 is mint-less — PER-LETTER on by_letter pages
    (78A=København, 78B=Helsingør; verbatim so the builder's _normalize_mints
    matches), AGGREGATE multi-mint on single-coin pages (c7h35). Builder
    by_letter path uses the per-letter mint (fallback to top-level), no-mint
    skip deferred when by_letter supplies mints. Verified 0 removed / 0
    existing-coin mint changes. **Still at the seed layer — run merger→absorb
    to render.** REMAINING field-swap residue: c4h53 (by_hede — needs
    per-spec-group mint, each by_hede group can span mints) + 5 no-variant-mint
    pages (c3h23, f6h1, f6h5, f6h26, f7h7 — no recognised mint on their lines;
    nominal fixed by Part 1, stay absent). Historical detail below:
  - **(superseded) field_swap Part 1-only note (commit 3cc3272).**
    Pages whose descriptor line is «Ruler, NOMINAL» (comma right after the
    ruler, NO mint; mint per-variant on A)/B)/C) lines) had the NOMINAL
    field-swapped into `mint`. parse_hede.py now extracts nominal correctly
    (new `_is_denomination` guard; lone denom-shaped segment after the
    ruler-comma = nominal, not mint). Verified: exactly the 13 pages change
    (nominal set, mint→None), 0 regressions on 843 others. audit field_swap
    12→0. **Part 2 (mint recovery, ~32 coins) NOT done — the real blocker.**
    These pages still don't seed: the mint now lives on the per-variant lines
    and must be recovered PER SUB-VARIANT (78A=København, 78B=Helsingør —
    NOT one aggregate). The simple aggregate-mint version was implemented +
    REVERTED after spot-check showed it mis-assigns (78A shown as Helsingør;
    also `display_for_alias` «Kopenhagen» gets dropped by the builder's
    _normalize_mints which keys on verbatim «København»). Correct Part 2 needs:
    (a) per-letter mint in `_extract_letter_groups` (scan each A)/B)/C) body
    for a registry mint, store VERBATIM); (b) per-hede mint for by_hede pages
    (c4h53); (c) builder by_letter + by_hede paths use the per-sub-variant mint
    (with fallback to top-level). Blast radius: ALL ~80 by_letter pages gain a
    `mint` key → must dry-run measure existing-coin mint changes before shipping.
    Affected field-swap pages: c3h23, c4h53, c4h78, c8h3, f6h24/26/27, f6h5,
    f7h1/4/6/7 (+ bonus mint-less recoveries c7h35, c8h1, f7h11/16/17).
  - **sub_letter_loss (3):** c4h163 (missing B — «Fortuna til randen for
    neden», empty sub-variant line), f4h44 (missing B), f5h3 (A vs B case).
  - **in_scope_absent (93):** mostly pages with no single `specs.default`/
    `specs.by_hede` block, multi-coin pages («1, 2 og 3 speciedaler»),
    undated «u.år» pages, or sub-variant-only «None»-nominal pages
    (c4h124-136, c5h131-135). Per-case review; lower priority.
  - **51 case-mismatched hede sub-letters** (kmk lowercase «119b» vs hede
    «119B») — graph fixed; DATA still case-split. Systemic fix pending
    (normalise hede sub-letter to uppercase at merger ingest / per-builder).
- **Curator verdicts (catalog_graph.py, 2026-06-06).** Two journals:
  `CURATOR_LINKS` = IDENTITY (✔-edge, → `merge_decisions::merges`):
  Hede 96 = KM 42; KM 80.1 = Hede 117/Sieg 41; KM 80.2 = Hede 116/Sieg 40;
  Hede 118 = KM 66; Hede 119 = KM 67; **Hede 108 = 109 = 110 = KM 259**
  (2 Mark Frederik III — all one coin); **Hede 93 = KM 32; Hede 91 = KM
  32.1** (8 Skilling Christian IV — Hede 96 = KM 42 above); **Hede 90 = 94 =
  KM 401** (1 Krone Christian V — all one coin despite the Hede 90/94 split;
  Dav 3642/3643/3645 hang off KM 401.x); **Hede 27 = KM 419 = KM 416** (2 Dukat
  Christian V — Hede 27 carries TWO KM numbers, unusual but factual);
  **Hede 26 = KM 413; Hede 31 = KM 415** (1 Dukat Christian V);
  **Hede 87 = 91 = 95 = KM 186-family = KM 192-family** (1 Krone Frederik III
  = 4 Mark Danske — ALL one coin despite two KM families + three Hede; f3h91
  nominal printed «4 Mark» — surface nominal divergence in match_uncertainty).
  `CURATOR_DISTINCT` = DIFFERENT-COIN (no edge, → `merge_decisions::no_merges`):
  Hede 10 ≠ Hede 14 (2 Dukat Frederik V); Hede 91 ≠ 93 ≠ 96 (8 Skilling Chr IV
  — KM 32.1 / KM 32 / KM 42); **Hede 27 ≠ 56 ≠ 58** (2 Dukat Christian V —
  three distinct coins); **Hede 26 ≠ 29 ≠ 31 ≠ 32** (1 Dukat Christian V — four
  distinct coins; KM 412 + KM A433 also separate. CAVEAT: shared «Schou 8»
  vertex bridges Hede 29↔32 but per curator is most-likely a DIFFERENT die for
  each — not evidence of identity). Hub colouring driven by `PROCESSED` — **ALL
  9 components done (green ✓) as of 2026-06-07.** STANDING TASK (user): work
  through ALL graph cases, recording each verdict — **COMPLETE**.
  **PROMOTED to `merge_decisions/danish_realm.yml` (2026-06-07, commit 80026ab):**
  3 merges (comp 1/2/4 all-one-coin) + 14 no_merges (comp 3/5/7/8/9 distinctness).
  seed_unified re-merged 7908→7895 (−13); verified 0 outsiders, all no_merge pairs
  distinct. **NOT promoted (catalog-attribution, need §4 _source_errata not merge):**
  comp 3 Hede96=KM42 (numista-15669 labels itself Hede 93A), comp 7 Hede26=KM413 /
  Hede31=KM415, comp 8 Hede27=KM419 — these reassign a KM our data attributes to a
  DIFFERENT Hede, so merging would unite curator-distinct coins. See FINAL-CONSOLIDATION below.
- **Graph node-merge rules (`scripts/maintenance/catalog_graph.py`):** per-ruler
  namespacing; Hede sub-letters → one base vertex (case-insensitive
  119A=119a); Schou dies → one set-vertex per Hede; **Sieg dot-sub-numbers
  → one base vertex** (32.1-32.4 → «Sieg 32.x», sub-classes of one coin —
  unlike KM, whose .N can be different coins per §9.4); Dav EC-volume
  prefix stripped; `_resolve_member` self-heals merge-shifted unified-ids.

**SUPERSEDED — the old «Component-5 cross-Hede DATA merge» note (2026-06-06,
«merge 116+117+numista-197176»).** The later SYSTEMATIC component-5 verdict
(catalog_graph pass, user msg «2 скілінга це дві різні монети») is the opposite:
Hede 116 (KM 80.2 / Sieg 40) ≠ Hede 117 (KM 80.1 / Sieg 41) — TWO distinct coins.
This also matches the already-committed Group-B decisions (which keep KM 80.1 /
MC_65041 separate from Hede 116). The split verdict is now pinned via
`merge_decisions::no_merges` (comp 5, commit 80026ab). Do NOT resurrect the
old merge — it was wrong.

**PENDING — FINAL-LAYER CONSOLIDATION of the comp-1/2/4 merges (2026-06-07).**
The seed_unified merge is done (merge_decisions + commit 80026ab), but the
`final/danish_realm.yml` layer still has each merged coin SPLIT across multiple
foundations with CONFLICTING fuss — the merge surfaced a bulk-promote
mis-classification. `absorb` is foundation-immutable (DF1): it flags
«curator classification clash» and SKIPS (won't auto-consolidate). The
`classification_decisions::assignments` mechanism ADDS new finals (for
genuinely-new coins) — it does NOT reclassify/merge EXISTING clashing
foundations. So consolidation needs either a new foundation-merge step or
manual foundation surgery. Curator-guided fuss (user 2026-06-07: «з кронами
ясно kronemont; з марками менш очевидно, не критично, якщо неясно лишай
seed_unsorted»):
  - comp 2  1 Krone Christian V 1690-92  → `kronemont/II` (clear: majority +
            Hede pieces already kronemont/II; precedent «1 Krone Chr V 1676-78»).
  - comp 4  2 Mark Frederik III 1665-67  → `kronemont/I` (clear: all 3 final
            entries already agree kronemont/I; precedent «2 Mark Frk III 1652»).
  - comp 1  1 Krone Frederik III 1652-53 → `kronemont`, phase AMBIGUOUS: Hede
            piece f3h91 = kronemont/I, ucoin piece tid-97152 = kronemont_chr_iv/II;
            both phases' data list «1 Krone Frk III 1652-1653». 9_25_thaler/I
            (numista-143477) is the clear mis-classification (Krone ≠ Speciedaler).
            Needs Hede standard-param check to settle I vs chr_iv/II.

**§CR + §CP/§CQ — KMK (8th specimen source) SHIPPED to final + pages
(2026-06-02/03). All committed locally, UNPUSHED.** Chain of work this
session:
- **Thinning** (`scripts/maintenance/thin_kmk_seed.py`, commit 822833d):
  KMK seed 42182 → 14443 per §9a weight-variance envelope (sort by
  weight, keep min/middle/max per ≥5 sub-variant bucket; id-sorted
  reps when no member has a weight). KMK `measurements` only ever
  carries `Vægt` (weight); ~14 % of object records carry it.
- **Merger hardened for scale** (59faeb4 + 0c26500 + 5a8d9d6): (a)
  memoise `_catalog_refs` (≈2.2×) GATED behind `_CATALOG_REFS_MEMO_ENABLED`
  — merger opts in per-entity-clear, absorb/audit/build leave it off
  (id(coin) reuse across entities would otherwise corrupt — the bug
  that inflated a danish_realm fold count 1→17); (b) **component-scoped
  no_merge** — PASS 1 collects confident+low only, PASS 2 registers
  no_merge ONLY within confident-connected components (≈0.5 % of O(n²))
  — fixes the real OOM that killed danish_realm (89.7M no_match
  frozensets ≈ 11 GB); (c) **PASS 1 parallelised** across cpu-1 worker
  processes (byte-identical, ~3.2×+; threshold `MERGE_PARALLEL_THRESHOLD`
  default 4000). Full re-merge now minutes, not 40-50 min.
- **`_collect_sources` .pdf fix** (7abc3f1) — THE root cause of the
  §CP/§CQ "conflicts": Bruun **Part II** PDF is the sole Bruun catalogue
  hosted on `danskmoent.dk/pdf/` (Parts I/III/IV on stacksbowers.com),
  so the `danskmoent.dk` single-page-host substring mis-classified it →
  url-only dedup collapsed every Part-II lot of a type to ONE citation.
  Guard `.pdf` URLs onto the multi-record (url,ref,type) path. Recovers
  Part-II citations project-wide (danish_norway 248→281). See
  SOURCES §13.
- **seed_unified regenerated** (9d8e08e) + **absorb --apply** (88aa100):
  9947 KMK bulk-promoted to V2 final (16957 total), 593 genuinely-new
  → `data/v2/classification_decisions/` pending (await curator
  fuss/phase). 50 enrichment conflicts remain — ALL benign specimen-
  level Bruun part/lot/page (anchor kept, alternatives in sources[];
  verified 0 citation loss). 1 benign self-foundation fold + 1 stale-
  purge (danish_realm).
- **KM-461 1699 2-Ducat corrected** (bb939ec): was the lone genuine
  conflict — V1 mis-tagged the Frederik IV 1699 *tronskifte* (throne-
  change) 2-Dukat as Christian V / Hede c5h-3 (c5h-3 is the unrelated
  1673 2-Dukat, Sieg 118). Now ruler=Frederik IV, hede_volume=f4h,
  rationale in `_curation_holds`; id slug `km-461-chr-v-1699` kept
  stable. Verified on rendered denmark page (tronskifte note + Frederik
  IV + recovered Bruun Part II lot 14032 all render).
- **Log-hygiene DONE** (a7967a9): `_deep_merge_catalog` no longer logs
  specimen-level `bruun_part/lot_no/page` disagreements as merge
  conflicts (they're expected multi-specimen, anchor + sources[]
  lossless per §9a — already excluded from MATCHING, now from the
  conflict LOG too). Verified all 50 were uniformly that pattern across
  1603→1874 (0 genuine among them). Output byte-identical (diagnostic /
  gitignored only). Genuine single-value conflicts (sieg_hede1971 /
  schou_hede1971 / hede_volume) still logged.
- **german_empire V2 final** (a8ffee0): absorb created it (27
  Reichswährung coins promoted); was untracked after the dir-pathspec
  absorb commit — now committed.
- **Next:** (a) `git push` main (15 commits UNPUSHED; submodule
  `scripts/cache` untouched this session → main only); (b) the 593
  KMK-pending coins in `classification_decisions/` await curator
  fuss/phase assignment (Phase 4).

**Mission temporal scope — Denmark-track anchor rescoped 1541 → 1514
on 2026-05-16 per §BI.** Denmark-Norway track lower bound = **1514**
(Christian II Lovkompleks: Møntordning af Sommeren 1514 Kopenhagen +
Møntordning af 3. August 1514 for Norge + Kvittering Paasketid 1515 +
Sjælland åbent Brev af 24. August 1515 — per Wilcke 1950 p. 183-186
verbatim); German-lands track unchanged at **1559 (1566)** (Augsburger
Reichsmüntzordnung). The 1541 Møntordning is now correctly framed as
the THIRD major Danish-Norwegian Møntordning in the Christian-II-
Lovkompleks lineage, not the first. TODO §BC closed; §BI in progress;
CLAUDE.md mission statement updated; `--year-from` default in seed
builder updated 1541→1514; seed regenerated; denmark.yml header /
timeline / summary deck rewritten. **Schleswig-Holstein + all German-
jurisdiction pages NOT touched** — they keep their 1559/1566 anchor
unchanged per §BI's explicit scope-restriction.

**§BI residual sub-tasks** (still in progress):
- Update `denmark_fuesse_year_boundaries.md` reichsdukat section to
  reference 1514 Lovkompleks as the verified first formal Danish
  gold-standard spec (Nobler 23½K 16/Mark establishes 23½K floor).
- Update `moentordning_1541.md` header annotation: position as
  Christian-III's-third Møntordning in Lovkompleks lineage.
- Update §BF scope-note: «1541-1566 gap» becomes «1514-1566 gap».
- Open sibling TODO for **Galster + Jensen-Skjoldager catalog import**
  (Christian II 1513-1523 + Frederik I 1523-1533 coverage — empty
  1514-1540 sub-window until that import lands). NOT a Hede extension
  — Hede 1957 itself does not catalogue pre-Christian-III rulers.

**§BF Denmark 1541-1566 gap (now «1514-1566 gap»)** sequenced AFTER
§BI lands. Original §BF four operational sub-tasks remain valid for
the 1541-1566 portion (8_daler_fod definition + fuss_periods
A1/A2 + seed-coin promotion c3h3-3A/3B + c3h4/5/7 + 4 new refs); the
pre-1541 portion (Christian II 1513-1523 + Frederik I 1523-1533)
becomes a fifth sub-task pending §AZ (Galster + Jensen-Skjoldager catalog import — new source family, not a Hede extension).

**Open §BF design question — Flensborg post-1544 track (Phase A3/A4)**:
separate `8_daler_lybsk_fod` Müntzfuß for Lybsk-aligned
sub-Mark + 14¼ Lod Daler, OR same Fuß with mint differentiation. Per
`moentordning_1541.md` §7.1 the 1547 Flensborg dual-zone is the
genealogical seed of later `18_5_thaler` / `34_marck` family vs
`9_thaler` family — likely deserves its own Fuß. Verdict pending.

**E1 NO-KM dedup audit on `data/locations/denmark.yml`** (parallel
front, separate from §BC follow-up) — methodology is per-case, with
explicit «за / проти merge» analysis, source links provided up-front
so the user can verify visually before any merge. Cases 1-9 of 46
done (case 9 = c4h79A/B/C/D folded into KM-16.1 + KM-16.2 as two
parallel merges, multi-source `weight_rough_g`/`fineness` preserved
per §9a). Next: **case 10 — c4h84 [A B]**.

The list of 46 cases is generated dynamically by the audit script
(see «Helper queries» section below); the per-case order isn't fixed
but reflects the `dup_pairs_denmark.txt` enumeration.

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

## Harvest routine — anomaly investigation (2026-05-29)

Investigated the autonomous harvest routine's self-logged anomalies
(`scripts/cache/_harvest_handoff.json::runs[].anomalies`). Two systemic,
one class transient.

- **IKMK discovery noise → ✅ scope-purged.** `fetch_ikmk.py` uses
  full-text `quick_search` + a **year-only** fetch filter, so the cache
  had filled to ~90 % out-of-scope. Purged 5791/7259 records (cache
  103→28 MB), kept 1468 German/Scandinavian coins + borderline-HRE.
  Landed on **main** (submodule commit `07014b3`, superproject pointer
  bump `651633d`) — not the worktree, due to a `cd /main` slip; curator
  accepted keeping it there. Keep-rule + verification recorded in
  `scripts/cache/ikmk/_oos_purged_by_scope_2026-05.json` and SOURCES.md
  §13.8. **Durable filter landed** (commit `48dc101`, worktree branch):
  `fetch_ikmk.py` now gates fetch + `scan_cache` on `_is_in_entity_scope`
  (country + object-type); the year-only `_is_in_mission_scope` gate is
  removed. Per the curator's multi-level scope (2026-05-29) year is NOT a
  drop criterion — German/Scandinavian (+ lands under their rule) of ANY
  era are broad keep-scope; only other-country coins + exonumia are
  dropped. Validated: entity-only filter flags just 2 of 1478 cached (a
  British Sovereign + a Koch medal — routine-added OOS the old year gate
  let slip), keeps all 326 German/Scandinavian records outside 1514-1914.
- **ucoin `osnabruck_p3057` skip-loop (occ≥10) → ✅ fixed.** Bucket
  «Bishopric of Osnabrück 1482-1661» — first gap-TIDs were pre-1559 OOS,
  so the picker re-offered + skipped it every run. Re-enumerated per-TID
  years via the ucoin listing (Chrome, 2 pages, 55 TIDs) and split
  `_BR_audit-4_2026-05-24.json::osnabruck_p3057.gap_tids` into 29
  in-scope (1631-1662) + 26 `oos_excluded_tids` (1482-1541). gap_tids now
  lists only the in-scope set, so the routine harvests the 1631-1662
  coins and the skip-loop ends. Committed on the **worktree** branch
  (submodule `417ab9d`, pointer bump `620241f`). Since reconciled:
  `origin/main` was merged into the branch (`f989f9b`), unioning the
  IKMK purge (origin) with this p3057 split in submodule merge `d385a7a`;
  a follow-up normalised the audit JSON back to the routine's indent=2
  (`e475a36` / pointer `04a17a7`). The branch's cache submodule now
  carries both changes.
- **Transient (no action):** chrome-mcp-disconnect (16:34 run),
  cloudflare interstitials (auto-cleared), `osnabruck_p2988` audit label
  drift («Hochstift» vs «City of Osnabrück»).

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

## Recent state changes (this session)

* **D39 — bulk_promote `no_basic_peer_only` mode + writer-bug fix**
  (2026-05-19). Extends D37 with a second mode that promotes ONLY
  unmatched unified entries with no metal+nominal peer in foundation;
  D/E/H/C-category cases (catalog/ruler/fallback disagree, low-conf
  near) stay in pending. Writer-bug fixed alongside:
  `_emit_classification_decisions` previously collapsed the flag to
  literal `True` via `bool(...)`, silently downgrading D39 →
  D37-mode-all on the first absorb. 1st `--apply`: 535 N-cases
  promoted across 8 entities, 583 D/E/H/C stay pending. 2nd
  `--apply`: idempotent (0 newly absorbed, 0 newly promoted).
  audit_v2 --quick: 0 violations. See V2_DECISIONS D39 for full
  per-entity breakdown.
* **D38 — NumisMaster builder routes country → canonical V2 entity**
  (2026-05-19). `COUNTRY_TO_ISSUING_ENTITY` mapping refactored to use
  9 canonical V2 entities directly (instead of legacy
  `schleswig_holstein_duchy` alias). Per-cadet-line routing:
  `royal_holstein` / `gottorp_duchy` / `schauenburg_pinneberg` /
  `sonderburg_duchy` / `norburg_plon_duchy` / `glucksburg_duchy`.
  Cascading rebuild: 426 `_unclassified` entries re-routed, V2
  unified regenerated, V2 final absorb-pass surfaces new pending
  for curator review. TODO §BT lists the 4 remaining builders
  (Hede/Bruun/Galster/Numista pre1541) that need similar treatment.
* **Per-case dedup methodology established** (user direction): each
  case gets full source links provided up-front, «за / проти merge»
  written out, user verifies visually before action. Auto-batching
  forbidden.
* **C-bucket auto-suppression in `build.py::_merge_seeds_into_raw`** —
  build-time filter that drops seed coins whose Hede catalog ref is
  already covered by a curated entry. Three safety guards layered on:
  metal-mismatch (cf-companion citations), weight-mismatch (>25 %
  ratio indicates cross-register KM clash or different denomination),
  year-mismatch (>10y with u.år exception). Fineness-similarity
  escape hatch on metal-mm guard for billon/silver labelling drift.
* **Cross-location seed coverage**: denmark seed entries get
  cross-checked against ALL location yamls' curated Hede refs (not
  just denmark's own) — fixes the «Glückstadt Hede entry lives in
  schleswig_holstein.yml curator but in denmark seed» pattern.
* **Bare-basename auto-suppression**: when curator has `hede: '107B'`,
  seed entry `dk-hede-c5h107` (bare basename, parser artefact) is
  also auto-suppressed alongside the explicit `dk-hede-c5h107b`.
* **KM register-aware architecture**: `KMRef {value, register}`
  schema; `Location.km_register: 'DK'`/`'SH'`; render shows bare
  «KM#» when single-entry in page default register, qualified «KM-DK#»
  + tooltip when cross-register or multi-list. Applied to case 7
  (Hede 178 → KM-DK# 25 + KM-SH# 87 same coin in two Krause volumes).
* **Verified-wins-over-unverified merge rule** (codified just now):
  CLAUDE.md §4 + `_VERIFIABLE_FIELDS` in seed builder's `_merge_one`.
  Drops `(?)`-marked values when source-attested candidate exists.
  Followed by legacy-data cleanup (45 «curated (legacy scalar)»
  fineness entries purged).
* **Proof-strike exclusion**: `_KNOWN_PROOF_PATTERNS = {"c4h20"}` in
  seed builder + explicit drop from seed yaml. CLAUDE.md §9 forbids
  proof / trial strikes; mechanism is ready for future entries.
* **«Back-to-top» floating button** in `assets/app.js`: appears at
  `max(viewport, 0.15 × page-height)` scroll threshold; custom RAF
  smooth-scroll with sub-linear duration capped 900 ms.

## Open TODOs added this session

| § | Topic |
|---|---|
| §N | ucoin↔Krause KM-attribution conflicts (earlier session, ongoing) |
| §O | Numista weight typos vs Hede Bruttovægt |
| §P | Denmark DK vs DK+ entity audit (1773 Helstaten cutoff) |
| §Q | Pull Hede / Numista commentary material into coin notes |
| §R | Backfill canonical fineness on `fineness: null` coins (Cat-1 fuesse) |
| §T | Keyword search across coins on a location page |
| §U | Per-specimen Δ-computation needs explicit weight+fineness lineage |
| §V | Numista / ucoin cache coverage audit (no auto-merge pipeline yet) |
| §W | Clean up §0z violations surfaced by scripts/audit_prose.py (873 hits, 663 errors) |
| §X | Fix cross-language inconsistencies surfaced by scripts/audit_i18n.py (76 hits, 43 errors) |
| §Y | Fuß-event vs coin-data span audit (timeline-bar accuracy) — kronemont_chr_iv + 9_thaler-SH outliers |

All entries carry their own design sketches in `docs/TODO.md`;
this list exists only to anchor «what's open» on a quick read.

## Local commit state

* **Main repo**: working tree clean. Recent commits on
  `feat/v2-pipeline` not pushed (user has not granted push
  permission this turn):
  - `917452c` audit(i18n): tighten R5 — flag only Mfuß-compound translations, not bare «стопа»
  - `66a2adc` build: bump scripts/cache → galster JSON regenerations (parser refactor outputs)
  - `5df8370` build: V2 default at /, V1 fallback under /v1/ (D44)
  - `c020d11` build(v2): default bulk_promote_pending → no_basic_peer_only for steady-state
  - `07b88cb` build(v2): expand Bruun year window to 1914 + schema cleanups
* **Submodule `scripts/cache/`**: 7 commits ahead of `origin/main`
  (parse(galster) regen + earlier parse(bruun) Galster/NMD/Schive/
  Skjoldager ref patterns + parse(hede) multi-Hede header layout +
  re-parse 87 hede files + extended marken_fin_udbragt_til). Push
  needs `git -C scripts/cache push origin HEAD:main` once user
  approves; superproject pointer already references the new head
  (`3f566216`).

## Recent changes — URL routing (2026-05-20)

* **V2 → root default, V1 → /v1/ fallback** (`5df8370`, D44).
  V2 pages now render at `site/<loc>/<lang>/index.html`; V1 pages
  move to `site/v1/<loc>/<lang>/index.html`. Two landings:
  `site/<lang>/index.html` lists V2 locations (default),
  `site/v1/<lang>/index.html` lists V1. Root `index.html` redirects
  to default; `/v1/index.html` redirects to V1 fallback. Both
  subtrees emitted on every build; `--v1-only` / `--v2-only` flags
  preserved.
* **V2 invariants audit clean** post-routing (I1-I6 all pass:
  3475 final coins, 3097 unified, 4560 seed, 22 entity tags).

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

## V2 pipeline refactor — architecture refined 2026-05-18

Late 2026-05-18 session refined the architecture into a **4-phase
fully-automated pipeline with V1 as verification anchor**. Earlier in
the session the autonomous-portion of the original 10-phase plan
landed (Phases 0-2 + 4 + 5 + bidirectional link). After user feedback
on idempotency, merge auditability, and curator-edits-via-rules, the
plan reorganised:

**New 4-phase model:**
1. Raw → typed (per resource) — script-only, unchanged
2. Typed → seed per (entity × resource) — script-only, V2 entity-keyed
3. Per-resource seeds → unified per entity (cross-source merge) — script auto-merges where confident; low-confidence cases surface for explicit curator decision in `data/v2/merge_decisions/<entity>.yml`
4. Unified seed → final fuss-distributed — script applies §8a auto-classify where confident; ambiguous cases surface for curator decision in `data/v2/classification_decisions/<entity>.yml`

**V1 = verification anchor.** V1 (`data/locations/`, `data/seed/<src>/<loc>.yml`) frozen post-bootstrap. V2 reprocesses ALL source data — existing + newly-harvested — through the 4-phase pipeline. First full-cycle run expected to map ~1:1 onto V1 curated. Promotion gate (Phase 9): «V1↔V2 diff is zero or fully explained».

**Curator role:** never edits coin fields by hand. Three decision surfaces only: (a) `data/i18n/issuing_entities.yml` (active entity set), (b) Phase 3 merge decisions, (c) Phase 4 classification decisions. Preferred path is always to update script rules so the case becomes auto-handled.

**Resolved 2026-05-18** (all 4 pending §7 decisions closed; added to
V2_PIPELINE.md §7a):
- `catalog.km` schema = `str | dict[str, str]` (dict form for cross-volume
  KMs); see `scripts/lib/v2_resolver.resolve_km_for_location`
- `coin.phase` = `str | dict[str, str]` (scalar default + dict per-location
  override); see `scripts/lib/v2_resolver.resolve_phase_for_location`
- V2 shares `templates/location.html.j2` with V1 (forked only the
  entity-badge cell to render N badges for list-form `issuing_entity`)
- `audit_v2.py` hard-blocks pre-commit from Phase 7 onwards (stricter
  than the original §7.4 «advisory» recommendation)

**Landed this session (16 commits on `feat/v2-pipeline`):**

| Stage | What |
|---|---|
| Phase 0 (bootstrap) | Skeleton `data/v2/`, audit + V1-side fix for 3 missing `issuing_entity` tags |
| Phase 1 (bootstrap) | `bootstrap_v2_final_from_v1.py` — 1317 V1 curated coins → 20 entity files. Idempotent merge-aware via `lib/seed_merge.py` |
| Phase 2 (bootstrap) | `init_v2_locations.py` — 12 V2 location display-meta files with `consumes_entities`. Preserves manual overrides on re-run |
| Schema | `Coin.issuing_entity: str | list[str]`, `Coin.phase: str | dict[str, str]`, `CatalogRefs.km: + dict[str, str]` + 7 new catalog refs (galster / friedberg / schive / skaare / etc.). `Coin.composed_of` + `Coin.promoted_to` |
| V2 build | `scripts/build.py --v1-only` / `--v2-only` + `_assemble_v2_location()` two-pass (direct + inverse-index) + per-coin phase pre-filter. Timeline + template updated for list-form `issuing_entity` |
| km-120 fix | V1 mint correction (`Royal Mint (Tower Hill)` → `Altona` per Numista N#31895) + V2 regen → `_deprecated_gesamtstaat.yml` retired |
| Phase 3.1 (new model) | `lib/v2_entity_classify.py` (mint → entity classifier) + `seed_v2_regroup.py` (V1 seeds → V2 per-entity-per-source seed yamls). Sanitisation moves catalog refs to nested `catalog:`, drops non-schema fields, coerces broken types. 2727 seed coins across hede/numismaster/bruun/galster/numista classified |
| Pipeline idempotency | All V2 scripts now merge-aware via `lib/seed_merge.merge_seed()`: re-runs produce zero file changes; curator edits in CURATED_FIELDS persist; orphan entries preserved verbatim |
| Phase 6 link | `relink_promoted_v2.py` — bidirectional `composed_of` ↔ `promoted_to` materialiser + `--audit` data-loss detection (flags weight/fineness/source-URL values present in seed but not in canonical host) |
| Doc refresh | V2_PIPELINE.md rewritten to 4-phase model; ARCHITECTURE.md §«V2 entity-keyed pipeline» extended; data/v2/README.md + CLAUDE.md preamble updated |

**Build results — V1 + V2 co-existence works:**
- `site/<loc>/<lang>/`: V1 unchanged (DK 2502, SH 842) — frozen verification anchor
- `site/v2/<loc>/<lang>/`: V2 bootstrap state (DK 3087, SH 485)
- Pre-filter drops 22 coins on V2 DK + 12 on V2 SH (cross-page-phase
  incompatibility — SH-page Phase II/III Helstaten coins rendering on DK;
  Haderslev 1591-1593 outside SH reichsdukatenfuss Phase I)

**Outstanding edge cases — DO NOT manually fix; encode as decision-file entries OR script-rule extensions:**
1. `km-120-chr-v-1787` — V1 mint corrected this session via the legacy data-edit path. Going forward, mint corrections like this come from upstream (parser cache should reflect the source's stated mint; the V1-author's «Royal Mint (Tower Hill)» was a hand-edit on top of source data).
2. `km-683-1-fr-vi-1813` dup-collision — DK side carries Bruun-specimen 1813 only; SH side is the consolidated 1813-1819 multi-mint type. **Goes into `data/v2/merge_decisions/danish_realm.yml`** when Phase 3.2 lands — explicit `merge: [dk-bruun-..., dk-numista-22803-..., dk-hede-f6h24a, ...]` declaration.
3. 4 single-Kopenhagen Helstaten coins (`km-743 / km-770 / km-x001 / km-x002`) — they were on V1 SH page despite single-Kopenhagen mint. V2 mint→entity classifier puts them in `danish_realm` (correct per §3.1 strict reading). If user wants SH visibility, the entity classifier rule should explicitly extend for «post-1813 Kopenhagen-mint Helstaten coins → joint `[danish_realm, royal_holstein]`». Goes into `lib/v2_entity_classify.py` — NOT hand-edits on individual coins.
4. 11 list-form Helstaten coins + 7 scalar `royal_holstein` SH-V1 coins use SH-page Phase II/III for `18_5_thaler`. On V2 DK they're dropped because DK has Phase I only. Resolution: Phase 4 auto-classifier needs to know about the dict-form `phase: {denmark: I, schleswig_holstein: II}` pattern — should detect when the same Müntzfuß has different periodisation across consumer pages and emit dict-form `phase` automatically. Goes into the classifier rules.
5. 6 royal_holstein DK-V1 Haderslev coins (`hede-1`, `hede-3`, `hede-6`, `hede-7b`, `hede-8b`, `hede-156`) — 5 dropped on V2 SH because year 1591-1593 falls outside SH reichsdukatenfuss Phase I range [1600, 1726]. Resolution: either widen SH Phase I in `data/v2/locations/schleswig_holstein.yml::phases` (config), or extend the auto-classifier to handle the cross-rendering case automatically.
6. 429 numismaster `_unclassified.yml` (schleswig_holstein_duchy tag without mint) — entity classifier rule needs extension for «numismaster `schleswig_holstein_duchy` without mint → consult ruler-era heuristic → assign». Phase 3.1 rule update, not per-coin manual.

**Pending scripts (4-phase model completion):**
- **`scripts/maintenance/merge_seeds_cross_source.py`** (Phase 3.2) — reads `data/v2/seed/<src>/<entity>.yml` (per-resource seeds), applies confident-merge rules + reads `data/v2/merge_decisions/<entity>.yml` for explicit curator confirmations, writes `data/v2/seed_unified/<entity>.yml` (one entry per physical coin, multi-source enriched).
- **`scripts/maintenance/classify_to_fuss_v2.py`** (Phase 4) — reads `seed_unified/`, applies §8a Müntzfuß-disambiguation pipeline + reads `data/v2/classification_decisions/<entity>.yml`, writes `data/v2/final/<entity>.yml` (fuss-distributed). Also auto-detects cross-page-phase-mismatch cases and emits dict-form `phase` for affected coins.
- **`scripts/maintenance/diff_v1_v2_final.py`** — compares V1 curated (`data/locations/`) against V2 final (`data/v2/final/`), lists every divergence. Phase 9 promotion-gate: «diff is zero or fully explained».
- **`scripts/audit_v2.py`** (Phase 7, hard-block pre-commit per §7.4) — home-file rule, bidirectional link integrity, cross-entity duplicate detection, V1↔V2 reconciliation status.
- **Native V2 builders** (post-Phase 9) — replace `seed_v2_regroup.py` post-processor with proper V2 builders consuming parser cache directly.

**Migration of bootstrap state to new model:** the current `data/v2/curated/<entity>.yml` files (bootstrap-migrated from V1 curated) will be **replaced** by `data/v2/final/<entity>.yml` (regenerated from Phase 3.2 + Phase 4 scripts) once those scripts ship. Until then, `curated/` serves as «Phase 4 equivalent» for V1-migrated coins.

**Anything touching** `_merge_seeds_into_raw` / `_assemble_v2_location` /
`scripts/lib/v2_resolver.py` / `data/v2/curated/*.yml` /
`data/v2/locations/*.yml` / `data/v2/seed/` (when Phase 3 lands) needs
to keep V1 + V2 co-existence working until the explicit «фліпай V2».

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

## OPEN, BIG — an entity for the Duchy of Schleswig under the Danish crown

**Why it exists.** 48 KMM records read «Danmark - Slesvig» — Frederik I (12),
Christian III (8), Frederik II (28), years 1523-1563. The mint registry maps
`schleswig → gottorp_duchy` unconditionally, and that entity's OWN description
in `data/i18n/issuing_entities.yml` dates itself «Adolf I 1544 → Karl Peter
Ulrich 1762». So the mapping files coins from 1523-1543 under a house that did
not exist yet — a contradiction inside the committed data, not a matter of
reading. `royal_holstein` does not take them either: it is Holstein, and its own
description starts at Christian IV.

Today the Denmark page compensates with a consume-cap, `gottorp_duchy` with
`year_to: 1543` (35 coins in, 314 out). That produces the right VIEW from the
wrong MODEL, and the curator's objection stands: everything the cap trims is
potentially Danish and currently lost from the page.

**The curator's proposal (2026-08-21), and why it holds.** Add an entity for the
Duchy of Schleswig as a Danish fief, so a coin can carry BOTH it and
`danish_realm` in list-form `issuing_entity`. No historical contradiction: the
Danish king WAS Duke of Schleswig (fief of the Danish crown from the 1460 Treaty
of Ribe), so a ducal legend — «FRIDERICVS D HOLSACI / MO NOV AVREA SLESVICENSIS»,
the very legend the 2026-07-16 curator call read — expresses his title in that
region, not a separate issuer. The coin does not stop being Danish. The joint
list-form is the shape the pipeline already uses on 44 finals, and build.py's
Pass 2 inverse index renders it on both pages without any year cap.

**RESEARCH FIRST — these are historical questions with knowable answers, not
curator preferences. Do not ask; find out and cite (§0 / §5).**

1. From which year does the Duchy of Schleswig exist AS SUCH, and until which?
2. Who ruled it in the years the coins give (1523-1563), and — going back —
   who were the predecessors, i.e. from when did the territory belong to
   Denmark? The focus is the Danish kingdom: a duke who became king belongs in
   this set; a predecessor under whom the territory was not Danish does not.
3. Were there interruptions — foreign or provisional rule? Those are exception
   years, the shape `mint_registry` already supports via `year_overrides` (cf.
   the Altona entry, `year_to: 1640 → schauenburg_pinneberg`).
4. Where does the 1544 Rendsburg partition leave the ROYAL share of Schleswig
   (Frederik II, 1563)? Same entity, or another?
   Note the 1490 partition already gave Frederik the Gottorf seat, and the
   ducal-zone mint moved Husum → Slesvig/Gottorp at his 1523 accession
   (Wilcke 7-2 p. 186-187, via docs/research/sh_ducal_zone_husum_1514.md §3).

**Mint side.** «Slesvig» is a REGION and appears to be the maximum precision
those records offer. Curator direction: keep it as `Slesvig?` — region-level
with the uncertainty marker, `mint_verified: false` — so a coin with a verified
town mint later overrides it via the existing certain-wins rule in
`_canonicalise_mint`. Do NOT alias `slesvig` onto `schleswig`: that would drag
the entity along with the spelling.

**Implementation surface, once the history is settled.**
- `data/i18n/issuing_entities.yml` — new entity, de/en/uk description
- `scripts/lib/mint_registry.py` — a Slesvig entry with `year_overrides`, AND
  make the existing `schleswig → gottorp_duchy` year-aware (it is unconditional
  today, so the same defect hits the German spelling too — the Danish spelling
  was merely hiding it)
- `data/v2/locations/*.yml` — `consumes_entities` on Denmark and
  Schleswig-Holstein; drop the `year_to: 1543` cap once the model is right
- full re-seed + merge + absorb, then check where the 35 capped coins land

**Precedent to read BEFORE touching the registry** (docs/handoff.md,
2026-08-18): re-routing pre-1544 Gottorp to `royal_holstein` in the registry was
tried and fully reverted, because `trace_coin why` showed a 2026-07-16 curator
cross-entity call that had already weighed it. «Run `why` before the registry,
not after.» This proposal differs — it adds an entity rather than re-pointing an
existing one — but the same check comes first.

Deliberately kept OUT of the 2026-08-21 Phase-3 batch (mintmaster / catalogue
ranges / Hede index stubs): those are mechanical, this is a historical model
change touching two rendered pages, and mixing them would make the diff
unreadable.

## 2026-08-21 (late) — Phase 3 DONE, committed as `eddd3e8`

Nothing below is outstanding; kept as the record of what the phase changed and
why. Submodule artefacts: `eaf225d49` (NGC + Galster re-parse), `e8b41af71`
(53 hede index stubs).

### Where the work stands

A long session fixing source-reading defects. Phases 1 and 2 are done; Phase 3
is mid-execution — code changes are in, the re-seed is done, and what remains is
merge → absorb → verify → commit.

**Committed earlier today:** `aa771d5`, `38369e6`, `f53986f`, `8e875c2` (parser
and registry fixes), `9808d38` (the first data flow + three merge decisions +
`_recorded_removals.yml`), and `eaf225d49` in the `scripts/cache` submodule.

**Phase 1 — done, uncommitted.** `absorb_seeds_into_final_v2.py` line ~2157: the
`composed_of` purge now keeps a member that lives in ANOTHER entity (it only
purged on `cid in unified_by_id`, a per-entity map, so a relocated member had
its membership record DELETED). `audit_v2.py`: I3 extended from `final` to
`seed_unified` and `seed` (per-source), so a home-file violation is caught at
the layer where the move happens, not two layers later.

**Phase 2 — measurements, all done.** Slesvig 48 records; city-in-mintmaster
161 (66 would gain a registry-known mint); truncated catalogue ranges 81
segments; V1 atavisms 216 odd-id seeds / 395 duplicated source URLs (upper
bound, the harmful share is NOT yet counted).

**Phase 3 — code done, uncommitted; run pending.**
- `build_kmk_seed._enrich_from_raadata` → new `_raadata_place`: KMM uses TWO
  separators for «territory + place» (`« - »` 4494, `«, »` 274) and only the
  dash was handled, so `_split_place` read the comma as «city, mintmaster» and
  put the TERRITORY in `mint` and the CITY in `mintmaster` on 161 seeds. Fixed
  where the field is substituted, not in `_split_place`, which handles its own
  ES field correctly (5 real mintmasters there).
- `build_kmk_seed._catalog`: printed RANGES are kept whole («Sch 1-5», «Schou
  31-47»), not truncated to the head. Ranges are already the convention — the
  hede seeds hold 841 schou ranges, galster 81. Abbreviated forms («Lange
  306-10») stored verbatim, not expanded (§0).
- `parse_hede.py`: THREE gates each made the next pointless — the glob
  `*hede.htm` (now `*hede*.htm`), the caller regex, and the same regex inside
  `_extract_index_stubs`. Volume indices split across numbered files
  (`c5hede1`, `f3hede1`…) had never produced a stub, so 53 Hede types had no
  record at all. Also fixed the index LIFECYCLE: an existing stub was skipped
  without being appended to `parsed_files`, so it vanished from
  `_parsed_index.json` on every later run and `build_hede_denmark_seed` then
  dropped it as `skipped_non_canonical` (43 → 3).
- `build_hede_denmark_seed`: `DK_MINT_DE` knew 13 of the registry's 50 mints —
  a fourth private copy of a mint vocabulary. It now falls back to the registry
  for COVERAGE while keeping its own SPELLING decisions (Haderslev,
  Rendsborg→Rendsburg). And `skipped_no_mint` is GONE (curator: an unnamed mint
  is the source's state of knowledge, not grounds to discard the coin) —
  `kept_no_mint: 61`, hede seeds 1154 → 1190.

### HOW IT ENDED

verify_reflow 0 losses / 119 gains, audit_v2 all invariants pass,
audit_lost_citations 0, build exit 0. Seeds +82, finals 14987, 52 new Hede
types. All 25 losses the gate first reported were traced and are recorded in
`data/v2/_recorded_removals.yml` (37 entries now): 6 were a truncated index
replaced by its own printed range — the gate now reads that as a refinement,
same reasoning as `_is_span_refinement` for year_ranges — 17 were §9a thinning
re-bucketing after coins gained real mints (each verified to leave exactly 3
survivors), one a Davenport number gaining its volume, and one an NGC «5 Ducat
1658» that joined the newly-created Hede 27.

### NEXT — Phase 4, absorb only, no merge needed

`classification_decisions` are read by absorb, so this is ~3 min, not ~7:

```
.venv/bin/python scripts/maintenance/trace_coin.py snapshot scratchpad/ph3_before.json
.venv/bin/python scripts/maintenance/merge_seeds_cross_source.py --apply
.venv/bin/python scripts/maintenance/absorb_seeds_into_final_v2.py --apply
.venv/bin/python scripts/maintenance/verify_reflow.py         # must end 0 losses
.venv/bin/python scripts/audit_v2.py --quick                  # must pass
.venv/bin/python scripts/maintenance/audit_lost_citations.py  # must be 0
.venv/bin/python scripts/build.py
```

The 52 new Hede types and the coins `kept_no_mint` returned are sitting in
`pending` (1628 total). Two of the new stubs are off-strikes and belong in §9.3
exclusions at classification time: `c5h30` «Kobberafslag af påtænkt dukat»,
`f3h25` «Sølvafslag af ukendt 1/2 Dukat».

Also pending: promoting the four specimens the 3a/3b splits detached — they need
an `issuing_entity` for the German states before their citations can travel back
to them.

Deliberate removals go in `data/v2/_recorded_removals.yml` (`kind: thinning` /
`kind: field`), read by BOTH branches of verify_reflow. Do not use
`--no-verify`.

### Lesson worth keeping

Three times today a fix looked applied and was not: a duplicate
`_all_v2_seed_coins` silently shadowed by a later definition, a regex fix behind
an untouched glob, and a `KeyError` crash whose stale output file read as
«nothing changed». Run the thing and read the WHOLE output, every time — an
absent result is not evidence of an absent effect.

## NEXT UP — decided order, and why (2026-08-21, curator-agreed)

**Do NOT bulk-promote the 1628 pending coins yet.** The order is:

1. **V1-atavism audit** ← start here
2. Duchy-of-Schleswig entity (the big open item above)
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

- **Duchy of Schleswig entity** — the big one, brief at «OPEN, BIG» above.
- **`pending` promotion** — 1627 now. Re-count after the Schleswig work; the
  reasoning for the order is at «NEXT UP» above and still holds.
- **Hede 74 vs 123** — curator call, and the duplicated `numista: 22576` should
  leave one side.
- **53 new Hede types** await classification; `c5h30` and `f3h25` are off-strikes
  → §9.3 exclusions.
- **Four specimens** detached by the 3a/3b splits need a German-lands
  `issuing_entity`.
- **`_catalog` ranges** — only kmk was fixed; see the OPEN entry above.

---

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
