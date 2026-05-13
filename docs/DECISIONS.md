# Research Decisions Log

Chronological log of significant analytical and architectural decisions made during research. Each entry explains what was decided and why, so future sessions (human or AI) can understand the reasoning without re-deriving it.

Entries are ordered newest-first within each month. CLAUDE.md carries the resulting **rules** and `docs/PLAYBOOKS.md` carries the **procedures**; this file carries the **rationale** — why this and not the alternatives.

---

## 2026-05-13 — Doc-infrastructure trio: handoff.md + SOURCES.md §13 + PLAYBOOKS.md

Introduced three companion files alongside CLAUDE.md to break a single growing mega-file into role-separated documents:

- **`docs/handoff.md`** — short-term state (current focus, pending verifications, local-commit state). Distinct from `docs/TODO.md` (long-term audit items with full design context) and CLAUDE.md (stable conventions). Updated at task / chapter boundaries; entries pruned when they stop helping the next session pick up cold. Introduced commit `da3b7e2`.
- **`docs/SOURCES.md` §13** — dated known-issues log per source. Numista weight typos, ucoin Cloudflare gates, Bruun cataloguer KM-copy mistakes, Hede silver-spec-on-gold-strike trap. Each entry already cost a session of detective work the first time; the log's job is to make the second encounter a 30 s recognition rather than another 30 min investigation. Introduced commit `b2d7809`.
- **`docs/PLAYBOOKS.md`** — executable procedures for recurrent tasks (per-case Hede dedup merge, ucoin Composition harvest, web-research citation cycle, Müntzfuß disambiguation, …). Self-contained: relevant CLAUDE.md rules reproduced inline with section pointer, so the playbook executes cold without flipping files. Introduced commit `390a4c1`.

**Reasoning.** CLAUDE.md had grown to ~50 KB and was mixing three concerns: immutable rules (forbidden patterns, required conventions), procedural how-to (the case-by-case dedup methodology, the citation cycle, the seed-import flow), and ephemeral session state (what was I doing last time?). Trying to maintain all three in one file produced two failure modes — (a) session-state polluting the rules section over time, and (b) procedural detail bloating the rules into unreadability. The split: **CLAUDE.md = WHAT to do / not do (immutable)**, **PLAYBOOKS = HOW to do it (executable)**, **handoff = WHERE we are right now (ephemeral)**, **SOURCES §13 = WHAT'S BROKEN in sources (dated errata)**, **DECISIONS = WHY this and not the alternative (this file)**.

**Alternatives considered.** (1) Keep everything in CLAUDE.md — rejected because the file already exceeded the threshold where humans (and the next session's AI) reliably read it through. (2) Use `docs/CONVENTIONS.md` and `docs/ARCHITECTURE.md` only — rejected because those exist but skew architectural / project-wide, not procedural. (3) Embed playbooks as code-block templates inside CLAUDE.md — rejected because templates need versioning + cross-refs that markdown sections handle but inline blocks don't.

**Scope.** CLAUDE.md header lists all five companion files in its «read at session start» reminder, plus an explicit «rules vs procedures vs rationale» pointer paragraph. handoff.md session-start checklist (PB-8) names the read order.

**Validation.** A new session opening cold should be able to: (a) understand the rules from CLAUDE.md, (b) find the procedure for the current task in PLAYBOOKS.md by PB-N, (c) recognise a known source quirk in SOURCES.md §13 in under 30 seconds, (d) understand the WHY of any non-obvious project choice from DECISIONS.md. If a procedural step recurs across three sessions without a PB-N entry, the playbooks file is under-served and the rule is to add one.

---

## 2026-05-13 — Pattern B: «one Krause KM = one entry» for Hede sub-letters

When a Krause volume publishes a single KM# that subsumes multiple Hede sub-letter variants (e.g. KM-DK# 16.1 covers Hede 79A + 79B, both Christian IV 1603-1613 2 Skilling; KM-DK# 16.2 covers Hede 79C + 79D, both 1618), our model is ONE curated coin entry per Krause# with `catalog.hede` as a LIST of the sub-letters, NOT one entry per Hede sub-letter.

The structural test: Hede's web edition publishes a SINGLE specification card (Bruttovægt / Finhed / Finvægt / iconography description) for the entire Hede# — sub-letters share the spec and differ only by mintmaster mintmark (trefoil vs crossed glødehager vs crossed køller, etc.). Krause assigns one KM# per design / mint / mintmaster *cluster*, not per individual mintmark variant. When the cluster boundaries coincide, the merge is canonical.

**Reasoning.** Krause-Mishler's stated cataloguing principle (CLAUDE.md §9 caveat) is «a separate KM# per design / mint / mintmaster / fineness variant by design». In practice Krause groups some mintmark variants under one KM# because the design is identical and the variants are sub-detail. Hede, by contrast, breaks them out by sub-letter to preserve mintmaster-level provenance. Our project's purpose is the **Müntzfuß standard analysis** — at that level, mintmark variants share everything (Bruttovægt, Finhed, Soll-fein, Δ-from-Soll) and should render as one row. The structural alternative — one row per sub-letter — would produce 2-4 visually-identical rows differing only by a one-character sub-letter, with no analytical signal added.

**Alternatives considered.** (1) Pattern A: one curated entry per Hede sub-letter, with each carrying the same Krause# and a different `catalog.hede` scalar. Rejected: produces redundant near-identical rows. (2) Pattern C: drop the sub-letter detail entirely and store only the bare `hede: '79'`. Rejected: loses Sieg sub-numbering (Sieg 38.1, 38.2, 38.3, 38.4 differ per sub-letter) and forfeits the mintmaster-level provenance Hede publishes. (3) Status quo (mixed): the seed builder emits per-sub-letter, the curator decides per-case. Rejected because it pushes the decision to per-case judgment instead of declaring a project-wide convention.

**Scope.** Schema accepts `catalog.hede` as `str | list[str]`. The build's `_merge_seeds_into_raw` auto-suppresses all seed entries whose Hede ref is in the list (plus bare-basename variants). All 46 Hede-dedup audit cases follow this pattern; cases 1-9 closed under it as of 2026-05-13.

**Validation.** Render check: when KM# X folds sub-letters Y/Z, the rendered page shows ONE row with the Hede column as «Hede X · Y, Z» (or a comma-list per locale). Seed-suppress count increases by the number of folded sub-letters after merge. See PB-1 for the executable procedure.

Closed via the case-9 commit `6d7a087` and the preceding case 7+8 merges. The «Pattern B» / «Model A» terminology is internal project shorthand — not period-attested numismatic vocabulary.

---

## 2026-05-13 — `KMRef {value, register}` schema for cross-volume KM disambiguation

Krause-Mishler numbering restarts within each country / region. `KM-25` in the Krause-Denmark volume is an entirely different coin from `KM-25` in the Krause-Schleswig-Holstein volume. The same physical Christian IV 1640-48 Glückstadt 1-Søsling carries BOTH KM-DK# 25 AND KM-SH# 87 — one physical coin, two Krause catalogue numbers from two Krause volumes.

The schema now models `catalog.km` as `str | list[str | KMRef]`, where `KMRef = {value: str, register: 'DK' | 'SH' | 'NO' | 'DE'}`. Each location yaml declares a default `km_register` (e.g. `km_register: 'DK'` for `denmark.yml`). Rendering: bare «KM#» when the value matches the page default; qualified «KM-DK#» / «KM-SH#» + tooltip («Krause-Mishler — Denmark volume» / «Krause-Mishler — Schleswig-Holstein volume») when cross-register or multi-list.

**Reasoning.** The naïve approach — string-prefix the value as `'KM-DK# 25'` — works for display but breaks programmatic comparison. A reader scanning two coins to check «do they share a Krause#?» can't easily detect that `'KM-DK# 25'` and `'25'` (the bare value) refer to the same Denmark-volume entry. Likewise the auto-suppress logic needs to compare `catalog.km` values across coins; string-prefixed values defeat that comparison. Structuring `{value, register}` keeps the comparable scalar (`value`) separate from the render-time qualifier (`register`), and downstream code accesses one or the other deliberately.

**Alternatives considered.** (1) Single-string prefix («KM-DK#») — rejected as above. (2) Separate fields `catalog.km_dk` and `catalog.km_sh` — rejected because it scales poorly with future volumes (KM-NO, KM-DE, …) and forces schema migrations every time a new volume is touched. (3) Implicit register from `issuing_entity` — rejected because cross-volume coins (the very case this solves) have one issuing entity but TWO Krause volumes referencing them, so the entity can't carry the disambiguation.

**Scope.** `scripts/lib/schema.py` Coin/Location models; `scripts/lib/compute.py` `_compute_catalog_groups` for the qualified-render output tuple `(prefix, values, tooltip)`; `templates/location.html.j2` tooltip rendering; `_KM_REGISTER_TOOLTIP` map in compute.py.

**Validation.** Two test cases: `km-25-chr-iv-1640` (Schleswig-Holstein page, list-form catalog.km with both DK and SH registers — should render bare «KM# 87» for the page-default SH + qualified «KM-DK# 25» with tooltip for the cross-register Denmark entry). `km-100-chr-iv-1624` (Denmark page, single DK register — should render bare «KM# 100»). Case 7 (Hede 178 → KM-25 + KM-87) was the canonical motivating example, closed in commit `cea6b5d` (the SH/Denmark register split was the same atomic change).

---

## 2026-05-13 — Verified-wins-over-unverified merge-conflict rule (CLAUDE.md §4)

When two candidates are being merged into one resulting entry — whether automatically (seed regeneration merge, auto-suppress fold, cross-location coverage scan) or manually (Pattern B consolidation of two curated entries) — and they disagree on the value of a measurement field (`fineness`, `weight_rough_g`, `diameter_mm`, `mint`, etc.), the **source-attested value WINS over the `(?)`-marked one**. The unverified candidate's value MUST NOT propagate to the result.

Concrete example: a curated entry carrying `fineness: 0.875` + `fineness_verified: true` (Numista-cited) being merged with a seed entry carrying `fineness: 0.88889` + `fineness_verified: false` (canonical-anchor-inferred) yields a merged entry with `fineness: 0.875` + `fineness_verified: true`. The canonical-anchor inferred reading is dropped because it has weaker provenance than the source-cited one.

**Reasoning.** Before this rule, the implicit merge behavior was «freshest wins» — the most recent merge re-writes whatever was there. That collapsed under a real case: seed regeneration with new canonical-anchor inference was over-writing previously-curated source-attested values, silently degrading provenance. The rule formalises §0 (no invention) at the merge boundary: a value with a recorded source has stronger truth-claim than a value derived from heuristic inference, and at any merge step the stronger claim must prevail.

This rule applies regardless of which side is «existing» vs «fresh» in any specific merge path; **verification status drives the precedence**, not the YAML order. The seed builder's `_merge_one` encodes this directly via `_VERIFIABLE_FIELDS = {"fineness": "fineness_verified", "weight_rough_g": "weight_rough_verified", "diameter_mm": "diameter_mm_verified", "mint": "mint_verified"}`. Per-case manual merges follow the same principle by convention.

**Alternatives considered.** (1) «Freshest wins» (status quo before this rule) — rejected per above. (2) «Existing wins» — would prevent ANY auto-update including legitimate corrections. (3) «User-prompt on conflict» — rejected for being too noisy on the routine cases (most conflicts are between identical values); the prompt should fire only at TRUE conflicts that fail the verification-precedence test, and even then, verification status almost always picks a clear winner.

**Scope.** `scripts/maintenance/build_hede_denmark_seed.py::_merge_one`; CLAUDE.md §4 explicit codification; cleanup commit `3d22c43` purged 45 «curated (legacy scalar)» placeholder fineness entries that violated the rule retroactively.

**Validation.** Audit pass: any coin with `fineness_verified: true` should have a `fineness.source` that names a primary or secondary tier source (Numista N#, Hede c{vol}h{N}, ucoin tid, IKMK id, Bruun lot). A `fineness_verified: true` paired with a generic «curated» / «canonical» / «inferred» source label is a regression — go find the real source or flip to `fineness_verified: false`.

---

## 2026-05-13 — ucoin-wins-over-inferred in metal backfill (Case 2 auto-replace)

When the ucoin backfill (`scripts/maintenance/ucoin_backfill_metal.py`) encounters a coin whose `metal_verified: false` (inferred from Müntzfuß convention — e.g. «sub-Skilling Scheide tier under 9¼-Thaler → billon») AND ucoin's `Composition` field source-attests a different metal (e.g. «Copper» for KM-86 1 Hvid 1624-25), ucoin's reading replaces ours automatically and flips `metal_verified: true`. Previously the script flagged this as `metal_mismatch` and left both unchanged; the new behavior auto-applies per the verified-wins precedence (above).

Concrete cases from the 2026-05-13 backfill:
- 3 × billon → copper for sub-Skilling Pennings (KM-5, KM-6, KM-86): our inference was correct «small denomination, low fineness» but the actual composition is pure copper, not billon.
- 2 × silver → gold for Daler-class issues (4 Daler 1604, 6 Daler 1604): these are gold-strike commemorative issues, our inference defaulted silver.
- 1 × billon → silver for Søsling 1622 (dk-tid-162994): the Søsling is normally billon but this sub-type is silver per ucoin.

**Reasoning.** Pre-rule behavior put 6+ entries into `metal_mismatch: []` for manual review per session, with the review consistently concluding «yes, take ucoin's value». That's the verified-wins rule fighting against itself — a deterministic outcome being routed through manual review. Auto-applying matches the §4 rule and eliminates the friction; the `metal_disagree_with_source` bucket remains for the genuine edge case where ucoin disagrees with a `metal_verified: true` entry (which then requires actual judgment).

**Alternatives considered.** (1) Keep manual-review prompt — rejected per above. (2) Auto-apply also when our `metal_verified: true` — rejected because that would allow ucoin to over-write source-attested values, violating verified-wins. (3) Special-case copper vs billon (since the project taxonomy puts <50 % silver in `billon`) — rejected as overly clever; the rule is simpler and the mapping in `map_composition` handles the «Silver (Billon) 0.XXX» → `billon` case explicitly.

**Scope.** `scripts/maintenance/ucoin_backfill_metal.py` Case 2 branch; new `metal_replaced` stat bucket distinct from `metal_confirmed` and `metal_mismatch`. Default for absent `metal_verified` flipped from `True` → `False` in the same change (project convention is explicit `true` only when a source attests).

**Validation.** Inspect each `metal_replaced` entry in the run report — the change should be sensible (matches Krause-volume / Hede-period expectations) and the ucoin-reading should be a documented Composition string on the live ucoin page (not a parser artefact). Commit `703617e` documented the first batch of 6 replacements with the cases enumerated.

---

## 2026-05-13 — Mandatory page hints for long-form refs (CLAUDE.md §5a)

Bibliography entries pointing to works ≥ 10 pages (PDF book, multi-chapter monograph, auction catalogue, periodical issue, multi-volume Konversationslexikon, scanned ordinance gazette) MUST carry a **concrete** page reference in the scope note. Forms accepted: `(S. 14)`, `Band 11, S. 890–891`, `Kap. 4, S. 123–125`, `§ 5, S. 12`. Approximate ranges («ca. S. 14–25», «im ersten Kapitel», «passim», «throughout») are explicitly forbidden.

A Wikisource exception applies: when a Wikisource page transcribes per-page from a print original, cite the print pagination — «MKL 1888, Band 11, S. 890–891» — even though the URL is a wiki page. Pure wiki-only articles use a section anchor.

**Reasoning.** Three long-form refs in the project pointed to ≥ 32-page documents without page hints — Soetbeer 1869 (91 pp), Meyers Konversationslexikon 1888 Münzfuß article (Band 11, multi-page), and the Bruun Stack's Bowers 4-PDF umbrella ref. The reader following any of those `<sup>[N]</sup>` would have to skim hundreds of pages to verify the cited claim. That's a citation that fails at its primary job. The bare Wikipedia-style citation convention (which our refs explicitly model on) treats page hints as required for book-length sources; CLAUDE.md §5a was previously silent on it.

A separate failure-mode the rule guards against: **citation false positives**. The Bruun umbrella ref was cited inline for the verbatim Plakat-1782 quote on the courantdukatenfuss-Phase-II prose. Full text search across all 4 cached Bruun PDFs returned 0 hits for the quote. The Bruun catalogues don't contain ordinance verbatim quotes; the actual source of the Plakat quote is danskmoent.dk's Christian-7 ordinance article. The umbrella ref had been silently mis-citing — and would not have been caught if the rule had required page hints, because Bruun's intro pages wouldn't have the quote either, and the missing page hint would have flagged that.

**Alternatives considered.** (1) Recommend page hints, don't require — rejected because soft conventions decay over time. (2) Require page hints only for PDFs > 50 pages — rejected as drawing the threshold too high (MKL articles are typically 1-2 pages in a multi-volume work and still need the volume + page locator). (3) Require verbatim quote without page hint — rejected because the quote alone doesn't help the reader locate the source page.

**Scope.** CLAUDE.md §5a new sub-section «Mandatory page hints for long-form sources»; sweep applied to three existing refs (SH ref38 repurposed from Bruun umbrella to danskmoent.dk ordinance source — commit `91be769`; fuss-shared ref7 Meyers added Band-11-S-890 — same commit; fuss-shared ref12 Soetbeer added S. 4). TODO §S closed in the same change.

**Validation.** Audit pass: any ref whose URL points to archive.org / a PDF / Wikisource / a multi-volume monograph SHOULD have a page-hint pattern (`S. NN`, `pp. NN`, `Band NN, S. NN`, `Kap. NN`) in the scope note. The audit script in `scripts/oneoff/audit_seed_survivors.py` style is the right shape for an `audit_refs_page_hints.py` (TODO entry candidate).

---

## 2026-05-12 — Seed auto-suppression: cross-location coverage + bare-basename + mismatch guards

The build's `_merge_seeds_into_raw` filter (introduced earlier) suppresses Hede seed entries whose ref is already covered by a curated entry's `catalog.hede`. Three additions accumulated through 2026-05-12 to make the filter robust against real curation patterns:

**Cross-location coverage scan.** The auto-suppress now walks ALL `data/locations/*.yml` files to build the coverage set, not just the location whose seed is being merged. The motivating case: `dk-hede-c4h178a` / `c4h178b` (Glückstadt 1640-48 Søsling) sit in `data/seed/hede/denmark.yml` (the seed builder is denmark-named because Hede is a Danish catalogue) but the curated entry lives in `schleswig_holstein.yml` (per the «Glückstadt issues move to SH yaml» convention). Without the cross-location scan, both seed entries would render as duplicates on the denmark page even though they're covered elsewhere.

**Bare-basename variant.** Hede pages like `c5h107` describe sub-letters 107A and 107B sharing one spec block; the parser sometimes emits a combined entry under the bare basename `dk-hede-c5h107` (no trailing letter). When ANY sub-letter is curated, the bare basename should also auto-suppress. The fix: in addition to the explicit-letter seed id (e.g. `dk-hede-c5h107b`), also add the bare-basename id (`dk-hede-c5h107`) to the suppression set via `setdefault` (so explicit-letter info wins over bare-basename info on conflict).

**Mismatch guards.** Three safety layers prevent silent merge of unrelated coins:
- *Metal mismatch:* when curated and seed disagree on metal, the Hede ref on the curated entry is almost certainly a «cf. silver companion» citation (e.g. a gold Portugaloser citing the silver Hede sub-type whose die design it shares). Do NOT suppress the silver Hede entry — it's a separate coin.
- *Weight mismatch:* same Hede ref + same metal but weights differ > 25 % indicates different denominations (e.g. ½ Speciedaler 14.4 g vs 24 Skilling 9.17 g — both might claim Hede sub-letter «12A» across Krause-Denmark / Krause-Norway register volumes, but they're physically different coins).
- *Year mismatch:* > 10 years apart with the «u. å.» (uden år) exception bypass — yearless Hede types whose canonical year is undefined on the coin itself inherit the parser's reign-range interpretation; the year discrepancy is then an artefact of u.år interpretation, not evidence of different sub-types.

**Reasoning.** Each layer caught a real failure case in production:
- Cross-location coverage: Glückstadt Søslinge were rendering on the Denmark page as duplicates of the SH page's curated entries.
- Bare-basename: Hede 107 spec card was producing a phantom row for «107» (no letter) alongside the curated 107B entry.
- Metal mismatch: Hede 156 silver coin was auto-suppressed by the curated gold-Portugaloser cf-citation, losing the silver entry entirely.
- Weight mismatch: Hede 12A cross-Krause-volume collision was being silently merged as one coin.

Without the guards, the filter would either over-suppress (hiding real distinct coins) or under-suppress (showing duplicates). The three layers together get the filter to ~99 % accuracy on the 605 Denmark seed entries (16 of 605 still flagged for manual review; all four classes of legitimate keep are documented in `scripts/oneoff/audit_seed_survivors.py` output).

**Alternatives considered.** (1) A single «metal + weight + year» combined check — rejected because each axis has its own escape-hatch logic (fineness-similarity for metal, u.år for year). (2) Configurable thresholds in YAML — rejected as premature; the current thresholds (25 % weight, 10 y year, 2 % fineness similarity) match observed envelopes. (3) Manual curator approval per suppression — rejected as too noisy; the guards already keep the ambiguous cases visible for review.

**Scope.** `scripts/build.py::_merge_seeds_into_raw`. Suppress / guard counters surface in the build log:
```
⚙  denmark: suppressed 195 hede seed coin(s) covered by curated Hede refs
ℹ  denmark: 9 hede seed coin(s) share a curated Hede ref but differ on metal (cf-companion citation pattern; both kept)
ℹ  denmark: 6 hede seed coin(s) share a curated Hede ref but weights differ >25% (cross-register KM clash or different denomination; both kept)
⚠  denmark: 1 hede seed coin(s) match a curated Hede ref but with year_first >10y apart — kept both for manual review
```

**Validation.** `scripts/oneoff/audit_seed_survivors.py` re-runs the suppression logic read-only and bucketise the survivors: auto-suppressed / metal-mismatch / weight-mismatch / year-mismatch / uncurated. The audit script's accuracy mirrors the build's; if they disagree, the build is canonical and the audit script is the regression to fix.

---

## 2026-05-10 — Multi-source attestation list shape (§9a Option C)

Multi-source attestations on a single measurement value now use one list-entry per source — never a `\n`-joined source label string. When Hede and Numista both publish 28.893 g for a Speciedaler, the YAML encodes it as:

```yaml
weight_rough_g:
  - {value: 28.893, source: "Hede 39A"}
  - {value: 28.893, source: "Numista"}
  - {value: 28.89,  source: ucoin}
```

The forbidden alternative — `{value: 28.893, source: "Hede 39A\nNumista"}` — buried two independent citations in a `\n`-joined string that downstream audit / dedup / query tooling had to re-parse with `re.split(r"[,;\n]", …)`.

**Reasoning.** The parser-of-display-string anti-pattern: code reading the structured field had to undo the display-time string-joining to recover the underlying multi-source attestation. That's the structure leaking into the data. Option C (split into N entries with same value) treats each attestation as its own record; downstream code iterates entries directly. The display pipeline groups list-entries by rounded value at render time, so two same-value entries collapse into ONE rendered span with both sources accumulated into the tooltip — visually identical to the joined form, structurally clean.

**Alternatives considered.** (1) Option A — keep `\n`-joined and parse at every read site (status quo). Rejected. (2) Option B — multi-source as `[sources: [...]]` list inside one value-record: `{value: 28.893, sources: ["Hede 39A", "Numista"]}`. Rejected because the natural reverse-grouping (one source → many values when an auction publishes multiple specimens with the same source) couldn't share the schema — Option B and the multi-specimen-per-source shape would be two incompatible structures. Option C is the same shape for both axes.

**Scope.** TODO I closed 2026-05-10. Migration script `scripts/maintenance/split_multisource_weight_entries.py` did the one-pass conversion. Schema accepts both list and scalar for `weight_rough_g` / `fineness` / `diameter_mm` — list when multi-attested, scalar (legacy) when single-source. The migration converted all existing multi-source attestations to list-form; new coins follow list-form per CLAUDE.md §9a.

**Validation.** No `\n` characters in `source:` field values across `data/locations/*.yml`. The display tooltip renders one source per line as before; the underlying structure is now machine-iterable.

---

## 2026-05-09 — §0z three reader roles + §0b hypothesis vs fact

Two new top-level rules added to CLAUDE.md:

**§0z. Three reader roles — always know who you're writing for.** Every line of text has exactly one of three readers: (1) AI / future-self / other agents (docs, commit messages, code comments), (2) the user (chat replies, deliberation questions), (3) the end-reader (rendered HTML — numismatist using the page as reference). Mis-targeting is the most common cause of voice violations. The forbidden pattern: project-internal rationale leaks into role-3 surfaces — phrases like «our card», «this artefact», «classification pending», «Beleg für die drei numerischen Synonyme im `name`-Feld unserer Vereinsmünzfuß-Karte» (real example caught during the session). The end-reader has no concept of «our card» or a «name field»; the sentence breaks the role boundary.

**§0b. Hypothesis vs. fact — never collapse the two.** A confident-sounding explanation for an observation must be backed by data you actually opened, not by what feels plausible. Before writing «X is because Y», verify Y from the actual data (cache file, source page, parser output). Hedge markers («hypothesis», «припускаю», «pending verification») are mandatory for unverified claims. When data is missing, name the gap explicitly; never fill it with a plausible story. The motivating case: a 2-Speciedaler 1663 row carried two KM numbers (Bruun: KM-240, Numista: KM-241). The prose was written claiming «Bruun-parser typo / OCR artefact» — a guess dressed as a conclusion. Opening `scripts/cache/bruun/lots/part4.json` plainly showed `body_excerpt: "Dav-3547; KM-240; Hede-62A; Sieg-80.1"` — Stack's Bowers' own catalogue had printed «KM-240». The «typo» explanation bypassed verification.

**Reasoning.** Both rules formalise patterns that had silently corrupted prose over multiple sessions. The earlier rules (§0 «no invention», §2a «academic register») addressed the *substance* of false claims; §0b addresses the *epistemic move* that produces them (guessing dressed as analysis), and §0z addresses the *audience confusion* that lets project-meta language leak past role boundaries. Together they tighten the discipline: claim → verify → label. If unverified, label as hypothesis. If wrong role, cut or rewrite.

**Alternatives considered.** (1) Strengthen §0 alone — rejected because §0 forbids invention but doesn't catch the hypothesis-as-conclusion failure mode where the claim is *plausibly* sourceable but never actually was. (2) Add a single combined «epistemic rigor» rule — rejected because §0b and §0z address different mechanics (the hypothesis-fact collapse is about reasoning; the three-roles split is about audience). They share spirit but need separate operational tests.

**Scope.** CLAUDE.md §0z and §0b (top of the rules section, after §0). Both rules carry concrete worked examples from the project's own history (the «KM-240 vs KM-241» case for §0b; the «Beleg für die … `name`-Feld unserer … Karte» case for §0z). Future-session test: every analytical claim that lands in prose must pass the §0b «did I open the underlying data?» check; every sentence in rendered artefact prose must pass the §0z «which role am I writing for?» check.

**Validation.** Audit pass candidate (TODO entry): a `scripts/audit_prose.py` linter that catches forbidden phrases — «we», «our», «this artefact», «our card», hedge words without hypothesis markers («likely», «probably», «presumably»). Until that linter exists, the rule is honor-system but reinforced by review.

---

## 2026-05 — Landing-page filter for unsorted-seed locations

`build_landing` now hides any location card whose coins include at least one entry under `fuss: seed_unsorted` (the bulk-import placeholder). Per-language pages still build and remain reachable by direct URL — only the landing card disappears.

The filter is automatic and idempotent: every build re-evaluates `visible_locations = [loc for loc in locations if not any(c.fuss == "seed_unsorted" for c in loc.coins)]`. As soon as a location's last seed entry is moved into a real Müntzfuß, the next build re-includes the card. No template or config edit needed at the threshold.

Build log surfaces the hidden set: «🙈 Landing hides 3 location(s) with unsorted seed entries: denmark, hamburg, lubeck».

## 2026-05 — Strict-cut Royal Danish coins move to denmark.yml

After the project picked up many Royal Danish Copenhagen issues during ucoin imports — some by mistake, some as «cross-mint context» for Holstein equivalents — settled on a **strict cut**: any pure Royal Danish issue (`mint: Kopenhagen`, `issuing_entity: danish_realm`, no Holstein-side Krause KM#) belongs in `data/locations/denmark.yml`, not in `schleswig_holstein.yml`.

This applied even to two coins previously argued to deserve the «cross-mint context» exception:
- **km-137-chr-iv-1644** (Hebræermønt 1644 Copenhagen — sister to km-32 Glückstadt Hebræermønt 1645)
- **km-303-fr-iii-1668** (Guldkrone Copenhagen 1668 — reformed continuation of km-40-2 Glückstadt Guldkrone 1657–1660)

Migrated in two rounds (commits `bd99259`, `47ac788`):
- Round 1 (21 coins): the entire Christian IV Kronemønt 1618–1624 series + 3 Reichsdukatenfuß ducats 1738–1749.
- Round 2 (25 coins): 23 km-x*** entries originally tagged as «mint: Glückstadt» but with ucoin Period = «Rigsdaler 1625-1699» / «Speciedaler 1582-1624» (= Royal Danish Copenhagen) — re-attributed to Kopenhagen + danish_realm. Plus the 2 cross-mint exceptions above.

ucoin's Period field is the canonical mint signal: pages 2940 / 1147 / 1115 / 846 / 647 / 646 / 374 are all Copenhagen; only page 2939 («Glückstadt 1617-1773») and 2995 («Holstein-Gottorp-Rendsburg 1716-1720») mark Holstein-mint coinage. KM-DK# in `catalog.others` alone is NOT evidence of Copenhagen mint — Krause assigned KM-DK# to many Glückstadt-mint coins as cross-references; it is the *absence* of a Holstein-side KM# combined with Copenhagen-period ucoin that disqualifies a coin from `schleswig_holstein.yml`.

## 2026-05 — Location id `schleswig` → `schleswig_holstein`

The location file covers BOTH Schleswig and Holstein duchies (and Royal Holstein, Gottorp, Sonderburg, Schauenburg-Pinneberg, etc.). Just `schleswig` is a misnomer; `holstein` would be just as wrong (Schleswig duchy mints — Schleswig itself, Tönning, Reinfeld — wouldn't fit). Settled on the proper compound `schleswig_holstein` (commit `25544eb`).

Touched 27 files: file rename, all `id: schleswig` → `id: schleswig_holstein`, all path strings in maintenance scripts, all CLI `--location` flags, Python identifiers (HOLSTEIN → SCHLESWIG_HOLSTEIN), and prose mentions in README/CLAUDE.md/docs that referred to the *file* (geographic «Schleswig» / «Schleswig-Holstein» mentions and HOLSTEIN_SOURCES / EASY_HOLSTEIN_MINTS mint constants left intact).

URL impact: live `/schleswig/` paths break and become `/schleswig_holstein/`. Acceptable since the project is in active development and no external linkers depend on stable URLs.

## 2026-05 — Bulk-import seed buckets into denmark/hamburg/lubeck

The ucoin categoriser had been holding 581 entries in three seed buckets (`H_DENMARK_SEED` 422, `X_HAMBURG_SEED` 80, `X_LUBECK_SEED` 79) marked «out of Schleswig scope but worth keeping for future location files». Bulk-imported all 581 into the corresponding location files (commit `1abbef8`):

- `denmark.yml` :  46 → 468 coins (curated 46 + 422 seed)
- `hamburg.yml` :   0 →  80 coins (NEW location file)
- `lubeck.yml`  :   1 →  80 coins (existing stub + 79 seed)

Each seed coin carries its raw ucoin data (km, denom, year, fineness, weight, diameter, url, tid) plus best-effort heuristic inference: ruler from Royal Danish reign chronology (or hanseatic city-state name), mint = location default, metal heuristic from fineness band. All values flagged `verified: false`; verification_note in DE/EN/UK explains the bulk-import status and what's pending.

Required infrastructure:
- A new placeholder fuss `seed_unsorted` in `data/shared/fuesse.yml` — empty `fractions`, so no soll/delta computation runs and the rendered tables show only what ucoin actually attests.
- Two new issuing entities `hanseatic_hamburg` and `hanseatic_lubeck` in `data/i18n/issuing_entities.yml`.
- Categoriser dispatcher reorder: direct ucoin-tid bridge now wins over MANUAL_OVERRIDES, so bulk-imported coins are recognised as «in base» on the next ucoin re-fetch instead of re-bucketing as seed. Net effect: every one of the 705 ucoin entries now resolves to processed_in_base; all active and seed bucket counts are 0.

Detailed per-coin work moves each seed entry into its proper Müntzfuß and flips `verified: true` for source-attested fields. See `docs/TODO.md` item D for the recommended order (Hamburg → Lübeck → Denmark) and the period→fuss mapping table for the Denmark cluster.

## 2026-05 — Christian IV's Kronemønt 1618 series is Royal Danish, not Holstein

`kronemont_chr_iv` — the 1618–1624 Christian IV Kronemønt programme — is **entirely Royal Danish Copenhagen**. All 18 coins (¼/½/1/2 Krone + Kroneskilling sub-units) live in `denmark.yml`. Glückstadt was founded in 1617 but its 1618 production focused on Reichsthaler/Skilling, not Krone-fractions. Wilcke I p. 152 documents the sub-Krone series without attributing it to Glückstadt; the Royal Danish Krause KM-DK# 56 ⅛ Krone was originally added to schleswig.yml as «mint Glückstadt provisionally entered», then audit revealed all 18 share that misattribution.

Three independent signals confirm Copenhagen for every coin in the series: (a) ucoin Period = «Speciedaler 1582-1624» (Royal Danish page, not Glückstadt), (b) Numista issuer_code = `danemark` with empty `numista_mints`, (c) Krause cross-references to KM-DK# numbers without any Holstein-side KM#.

In `schleswig_holstein.yml` the `kronemont_chr_iv` Münzfuß remains in `fuss_order` with the full historical fuss_periods description but zero coins — Vereinsmünzfuß / 30_thaler pattern: «the standard was in circulation, no Holstein issues struck». pdate_label appends «in Holstein keine eigenen Prägungen — siehe denmark.yml».

---

## 2026-03 — Bremen Thaler Gold silver Münzfuß (1840–1872) reconstruction

Bremen's silver Münzfuß from 1840 was reconstructed independently: **13⅓ aus der rauhen Kölner Mark at fineness 71/72 (= 23 Karat 8 Grän = Reichsdukat gold standard applied to silver)**.

- Empirical Feinsilber content of ~0.240216 g/Grote confirms this.
- The Jever 1764 4-Grote coin inscription «240 OBF FEIN MARC» independently documents the identical standard 76 years earlier — confirming it as an established North German coastal regional standard, not a Bremen innovation.
- Must be recorded as an **original reconstruction**, not citable secondary literature.

**When to note this**: in Bremen's YAML, the fuss block needs `verification_note` explaining this is a first-principles reconstruction from coin inscriptions + Jever precedent, not a published historical standard. User expects this transparency.

## 2026-03 — Bremen periodization before 1870

Before 25 July 1870 Verordnung, **Bremen had no formal Kurantwährung** — Pistole and foreign gold circulated de facto; Thaler Gold was *only a Rechnungseinheit*. Only with the 1870 Verordnung did Thaler Gold become gesetzliches Zahlungsmittel.

When working on Bremen data: pre-1870 coins labeled "Thaler Courant" (e.g., Bremer Bank banknotes) need a note explaining this reclassification happened in 1870 — the inscription predates formal currency status.

## 2026-03 — Gold:silver ratio in Bremen

The implied ratio in Bremen's Friedrich d'or = 5 Thaler Gold exchange rate is **~14.34:1** (older standard), consistent with Gresham's Law keeping silver in circulation while the 1840 market rate was ~15.5:1.

## 2026-04 — Kronemønt as a separate Münzfuß (not under 9¼)

Kronemønt (1618–1696) is classified as its **own fiscal Tarifmünze category**, not as "reduced 9¼-Fuß". Empirically ≈15.65 Kronen/Marck; ≈10.43-Thaler-Fuß-equivalent. But the fundamental point is that **the Krone was a Tarifmünze** — traded at a king-set value *above* silver content. The difference = Seigniorage, not market price.

Confusing it with a reduced Speciesthaler would misrepresent the economic mechanism. It gets its own fuss entry (`kronemont`) with `kind: tarif` for all its coins.

## 2026-04 — Lübeck 1776 Speciesthaler is 9-Fuß, not 34-Mark-Fuß

The 1776 Lübeck 1-Thaler (233.856 g ÷ 9) is on the 9-Thalerfuß. Should not be grouped with 34-Mark-Fuß Courant-standard coins — these are separate monetary populations and must be analyzed separately.

## 2026-04 — Hamburg Bancovaluta: pre/post-1769 are distinct phases

Hamburg Bancovaluta has two fundamentally different phases separated by the 1769 reform:
- **1619–1769 · Reichstaler-Fuß**: 1 Reichstaler (9-Fuß) = 3 Marck Banco; bank fund nominally backed by Reichstaler. But de facto circulation degraded (Zinnaischer + Leipziger Fuß coins mixed in), making reform in 1769 mandatory after Seven Years' War.
- **1769 · Hamburgischer Banco-Fuß**: 27⅝ Marck Banco per feine Marck; einlagen valued by Feinsilber, not nominal. 
- **1777 · Altonaer Banco-Fuß**: 27¾ Marck Banco — further refinement for Holstein.

When modeling Hamburg: these must be **three separate phases**, not one "Bancovaluta 1619–1875".

## 2026-04 — 13⅓-Thalerfuß: separate fuss from Konventionsfuß

Despite mathematical equivalence (3/4 × Konventionstaler = Kuranttaler), the **13⅓-Thalerfuß** (Konventionskuranttaler-Fuß) should be treated as a **distinct fuss**:
- As a rechnerische Einheit throughout Norddeutschland wherever Konventionsfuß was used but Groschen-Teilung (24/Taler) kept
- Specific prägungen: Sachsen-Weimar-Eisenach 1760 (explicit «13⅓ ST. EINE FEINE MARCK»), Hessen-Kassel 1776/78/79 Sterntaler, Oldenburg 1761–1765

The 17,53920 g Feingewicht value coincides with Bremen's Thaler Gold Raugewicht (986 1/9‰), which is a pure numerical coincidence — different logic (feine Marck-basis for Konv.kurant; rauhe Marck-basis for Bremen Gold).

## 2026-04 — KM# 176 Speciesthaler 1700 "Unterfuß" — non-standard anomaly

Bruun-14231, 26,14 g rau weighs significantly less than the 9¼-Fuß standard (29 g rau). Calculated at .875 fineness: Ist ≈ 22,87 g → implied 10,225-Fuß — **not 9¼**.

Likely a one-off "reduzierter Tönning-Speciestaler" under Friedrich IV. in his last year before death at Klissow (19 July 1702). No secondary literature explanation available online. Must be flagged as `verified: false` with detailed `verification_note`.

## 2026-04 — KM# 152, 154, 154a (pre-1841 Rigsbankskilling) are NOT dual-denominated

Initially marked with `(?)` pending verification. Confirmed by Numista legend transcripts:
- Pre-1841: «*16* REICHS=BANK SCHILLING. [Jahr]. [MM]» — **single inscription**
- Post-1841 (Forordning 18. Dez. 1841, Christian VIII.): dual-inscribed with Schleswig-Holstein Schilling Courant

KM# 152/154/154a belong to 18½-Fuß Phase A with `nominal: "16 Reichsbank Schilling"` (single). Dual-denom begins with KM# 721/733/734/737 in Phase B.

Serhii explicitly requested that `(?)` markers must be removed once verified — don't leave speculative markers in place after confirmation.

## 2026-04 — Coin Nominal field: only literal inscription

**Principle established, then applied retroactively to 7 rows**:

Only what is engraved on the coin goes in `nominal`. Calculated equivalents → `note`.

Fixes applied:
- KM# 82 «8 Skilling Dansk (= 4 Skilling Lybsk = 1/12 Speciedaler)» → «8 Skilling Danske»
- KM# 42.1 «1/16 Speciedaler (= 3 Skilling Lybsk)» → «1/16 Reichsthaler Holstein-Dänisch» (matching actual legend MONNO GLVCKSTAD...XVI·E·REIC·HS·DA)
- KM# 124/150 «1/24 Thaler Species ↵ 2½ Schilling Courant» → «2½ Schilling Courant» (coin says only "2½ SCHILLING COURANT" without SP-Angabe)
- KM# 250 «24 Skilling Danske (Rigsort = ¼ Rigsdaler Courant)» → «24 Skilling Danske» («Rigsort» is a historiographical nickname, never engraved)

Rule: always verify against actual coin inscription (from museum catalog, auction transcript, high-res photo). If uncertain, mark `verified: false` on the nominal itself.

## 2026-04 — "Schillingfuß" is not a real Münzfuß

Early drafts labeled small Billon coins as being "in Schillingfuß". **This is wrong** — Münzfuß is defined by the head silver coin (Speciestaler). Schilling is a nominal *within* that Münzfuß, not a separate fuss.

All 7 Tönning Scheidemünzen (KM# 155, 158, 183, 185, 212, Lange 438, KM# 164 variant) are now correctly classified as belonging to 9¼-Fuß with `kind: scheide`.

## 2026-04 — Kurant vs Scheide as sub-category of phase

Within each phase of a fuss, coins are further split into:
- ✦ Kurantmünzen (green divider): vollwertig, nominal ≈ silver content
- ∘ Scheidemünzen (amber divider): nominal > silver content, local only

This is economic, not decorative. **Mandatory** for any phase that has both categories. Separation reveals when/how Seigniorage was built into the system.

## 2026-04 — 3 Pfennig Preußen 1861–1873 valid in Holstein only from 1866

Numista shows emission dates 1861–1873 for Prussian 3 Pfennig, but in Holstein it became gültig only after Preußen-Annex 24. Aug. 1866. Year label should reflect Holstein-validity, with a footnote.

General principle: **location-specific validity takes precedence over emission period** when the coin belongs in that location's data. A Prussian 1861 coin is not "in Holstein 1861" unless it actually circulated there before annexation.

## 2026-04 — Separate tables for Kurant/Scheide within phases

After noting the conceptual importance of the Kurant/Scheide distinction, implemented as visual split in rendered HTML:
- Green-left-border divider for Kurant sub-block
- Amber-left-border divider for Scheide sub-block
- Each sub-block is a full `<table>` with its own thead — easier to scan at a glance

Added CSS classes `.mt-subcat.kurant` and `.mt-subcat.scheide`. Template enforces this structure automatically.

## 2026-04 — Architecture migration to YAML + build pipeline

Direct HTML editing hit scaling limits. Moving to:
- YAML source data in `data/`
- Pydantic-validated schema
- Python build pipeline → HTML output
- GitHub Actions for deploy

Target: current 180KB Schleswig HTML reproduced 1:1 by build script, then i18n (DE/EN/UK) and landing page added. Subsequent locations (Bremen, Hamburg, Lübeck) require only new YAML files, no code changes.

---

## 2026-05 — Closing-block invariant for every Müntzfuß on a location page

Every fuss on a per-location page (every `fuss_periods.<id>` entry that
renders) must carry both a `closing_label` and a `closing` text. The
header-grundwerte-(details)-closing four-block structure is the
canonical reading shape; a missing closing leaves the fuss entry
truncated and inconsistent with its neighbours.

**Reasoning:** a closing summary doubles as (a) a pointer to «what
the reader should remember about this Müntzfuß on THIS location»,
(b) a place to land the post-period demonetisation / continuation
arc, and (c) a unit of structural symmetry across all fuss blocks
on the page (reading rhythm). Audited on schleswig_holstein.yml in
session that produced commit `bca7b15`; only `kronemont` (10½-Krone-Fuß)
lacked the block. Filled. Audit script in the commit body.

**Scope:** `data/locations/<loc>.yml` `fuss_periods.<fuss_id>.closing_label`
+ `closing` (DE/EN/UK each). Rendered by
`templates/location.html.j2` lines around 890.

**Validation:** Python one-liner
```python
fp = yaml.safe_load(open('data/locations/<loc>.yml'))['fuss_periods']
missing = [f for f, sp in fp.items() if sp and (not sp.get('closing') or not sp.get('closing_label'))]
```
should return `[]`.

---

## 2026-05 — Hide details-toggle when a Müntzfuß has no coins on this page

The collapsible `<details class="fuss-details">` toggle on each fuss
block was previously emitted whenever the fuss had EITHER nonempty
phases (≥ 1 coin documented) OR a curated `details` text block. This
produced empty toggles on fuesse with rich historical context but no
local coinage (e.g. `kronemont_chr_iv` on the SH page — Copenhagen-
only standard, no Holstein issues).

**Decision:** the toggle now requires `nonempty_phases` only. Fuesse
with no coins on the location render their `header + grundwerte +
closing` unconditionally, but the details toggle is skipped — no
empty expandable section. Standalone history that previously lived
inside the toggle body (`sp.details`) is preserved by promoting the
content into the unconditional `closing` block when it matters as
running history.

**Reasoning:** an empty toggle showing «N Phasen, 0 monet» on click
was misleading — the user clicks expecting coin tables, gets only
prose. Hiding the toggle keeps the expectation contract intact.

**Scope:** `templates/location.html.j2` line ~753, condition
`{% if sg.nonempty_phases %}`. Affected fuss on the SH page at the
time of decision: `kronemont_chr_iv` only.

**Validation:** rendered HTML — `grep 'fuss-details" data-fuss=' site/<loc>/<lang>/index.html`
should list only fuss-ids with ≥ 1 coin.

---

## 2026-05 — Light-theme palette via `from_light` override

The timeline-bar layer rendering uses `mix-blend-mode: plus-lighter`
and a per-palette `--layer-bg` colour. On dark themes the lighter
palette `to` end at 1/6 alpha sums to the full saturated colour. On
light themes that same setup washed out — adding a light colour to
a cream backdrop produces near-white. The fix has three layers:

1. **Light themes use `from` (darker palette end)** instead of `to` —
   plus-lighter additivity now lifts the result toward a medium tone
   that contrasts with cream rather than washes out (commit `cc622c4`).
2. **Uniform 0.7 darkening of `from`** on light themes — without
   it the lightest silvers (rt, si) failed WCAG 3:1 contrast against
   cream (commit `32f2eae`).
3. **Optional `from_light` override field per palette** — used pre-
   calibrated as-is on light themes (skipping the 0.7 darkening).
   Currently used by:
   - the silver palettes (rt/si/kr/vt/rb) to substitute neutral-grey
     values for the cool-blue `from` end, keeping pure silvers visually
     distinct from the Krone-Mønt (krm) Prussian-blue family which
     used to merge with them in the dark-blue band (commit `5f13802`)
   - krm to lift the tariff-silver bars from cold dark navy into a
     clearly sky-blue tone — same brightness band as the silvers but
     in a saturated-blue hue, so hue separation does the work of
     distinguishing «tariff silver» from «pure silver» (commit `f577f9f`)
   - rm (Guldkrone-Fuß) to lift the warm-bronze from near-black olive
     into a readable mid-bronze on cream (commit pulled from another
     chat, see `theme.yml` palette comments)

**Architectural rule:** any palette whose plain `from × 0.7` rendering
fails contrast OR collides hue-with-another palette on the cream
backdrop should declare `from_light` in `config/theme.yml`. The plain-
`from` darkening is the fallback; `from_light` is the explicit override
for palettes that need either a different hue (silvers → neutral) or
a different brightness anchor (krm → sky-blue, rm → mid-bronze).

**Scope:** `config/theme.yml#timeline_bars.<id>.from_light` (optional);
`scripts/lib/styles.py` reads it in `_timeline_bars_css` and skips
the 0.7 darken when present.

**Validation:** WCAG contrast script (see commit `32f2eae` body) —
every palette's effective light-theme colour should clear 3:1 against
the cream page bg, and hue separation between the silvers (achroma)
and krm (saturated blue) should be visible at 1.5× zoom on a cream
canvas.

---

## Decision template for future entries

```markdown
## YYYY-MM — [Short title]

[One-paragraph summary of the question and decision.]

[Reasoning: what evidence drove the decision, what alternatives were considered.]

[Scope: which files/fields are affected.]

[Validation: how to verify the decision is still correct if questioned later.]
```
