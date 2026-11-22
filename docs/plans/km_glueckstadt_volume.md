# KM volumes after 677401d — stale volumes, the Glückstadt section, NGC Glückstadt over-merges

Opened 2026-11-22. Stages run one at a time; each is measured on a trial
re-flow (data reverted to HEAD afterwards) and goes ahead only on the
curator's yes.

## Findings (verified 2026-11-22)

1. **Stale volume on a final.** The final self-unions its stored catalogue
   (9¼ / 18½ / Kronemønt are not in `_rebuild_scope.yml`), so a volume that
   no member gives any more stays: km-696-1 keeps `sh: [696…706]` while all
   21 members give `dk` (NumisMaster / NGC explicitly «Denmark»). Same on
   c-b735eb06 (`dk: 77/83`, members give them only in `sh`) and
   c-35178b3c (`sh: A43/B43` beside NGC's `dk`).
2. **Values no member gives.** c-e9e00fad (Hede 7) `sh: 608` — KM 608 is
   Hede 8, its own class c-31f9e790; left from before the 607/608 split.
   c-d46a4495 (Hede 121) `dk: 103` — KM 103 is NGC 101324 «German States
   SCHLESWIG-HOLSTEIN Krone 1671-1682, crowned C5 monogram / crowned Danish
   arms», now a lone class c-c50a7d96 in seed_unsorted: probably the same
   type as Hede 121 (1 Krone = 4 Mark) numbered in the S-H section, like Hede
   120 = Glückstadt KM 73 = S-H KM 105. Not stale — a merge candidate.
3. **Krause «Glückstadt» is its own section.** Same numbering in NGC
   («Denmark GLÜCKSTADT …», 97 records), NumisMaster (country GLÜCKSTADT, 88;
   86 numbers shared with NGC, same denominations) and Numista (issuer
   «Glückstadt, City of», 48 seeds). It collides with Denmark main (KM 26 =
   6 Speciedaler 1604 vs Glückstadt 1/16 Speciedaler 1640; KM 80 = 2 Skilling
   1620 vs 2 Mark Danske 1694; KM 82, 12, 13, 15 likewise) AND with the S-H
   section (Numista issuer «Schleswig and Holstein, Danish duchies of»: KM 79,
   82 are other coins; Hede 120 is S-H KM 105 and Glückstadt KM 73). Neither
   `dk` nor `sh` is right for it. 677401d gave NGC's Glückstadt records `dk`
   (wrong); the royal_holstein bare-KM reading has always filed Glückstadt
   numbers under `sh` (also mixed).
4. **NGC Glückstadt records sit in danish_realm** (94 seeds, no mint, scope
   `denmark`), while NumisMaster routes country GLÜCKSTADT to
   royal_holstein. Since 8e0f0ad (NGC first flowed) nine of them sit in
   Copenhagen classes whose Hede page names København and lists none of the
   added years: km-15-chr-iv-1603 (Hede 74), km-48-chr-iv-1602 (Hede 48),
   km-33-1-chr-iv-1606 (Hede 92), dk-tid-163044 (Hede 77), dk-tid-163033
   (Hede 93), c-8f75b235 (Hede 45, via Holstein-Gottorp-Rendsborg KM 5),
   c-2384d941 (Hede 89), c-3024c6e3 (Hede 93 Chr V), c-1d2dbfd8 (Hede 113).
5. **Holstein-Gottorp-Rendsborg** (NGC sub-section, 4 records, KM 5–8,
   1716–1720) is a further section; its numbers collide with Glückstadt 5–8.

## Stage 1 — stale volumes (code ready, measured)

- `lib/seed_merge._km_bare_superseded`: a fresh volume-keyed KM replaces an
  existing KM in any shape whose numbers it covers (before: bare only — a
  `{dk: 26}` → `{sh: 26}` re-reading became `[{dk}, {sh}]`).
- `absorb._drop_relabelled_km`: before the catalogue merge, the final's own
  KM loses a number filed under a volume in which no member gives it, when a
  member gives the same number under another volume. Untouched: numbers no
  member gives, numbers a member gives with no resolvable volume, finals with
  a catalog / catalog.km hold.
- Trial (absorb all, from HEAD): 3 finals change — km-696-1 (sh dropped),
  c-b735eb06 (dk dropped), c-35178b3c (sh A43/B43 dropped; dk stays until
  stage 2). trace_coin: 0 real losses; verify_reflow: 0 losses. NGC and
  NumisMaster builders re-run on the new merge_seed: seeds unchanged.
  Unit tests seed_merge (31) and km (118) pass.
- Data, on the curator's yes: `_recorded_removals.yml` for c-e9e00fad
  `km 608` (the number lives on in c-31f9e790).
- To add: unit tests for both functions.

## Stage 2 — a register for Krause «Glückstadt» (needs a decision)

Curator decides the register code and the label (e.g. internal `glu`,
displayed «KM-Glückstadt#» or similar) and its tooltip. Then:
NGC sub-section GLÜCKSTADT, NumisMaster country GLÜCKSTADT and Numista
issuer «Glückstadt, City of» write `{glu: …}`; Numista issuer «Schleswig and
Holstein, Danish duchies of» writes `{sh: …}`. Bare numbers (Bruun, ucoin)
follow the merger's one-base rule. Holstein-Gottorp-Rendsborg stays bare
unless the curator wants a register for it too. Measure: re-flow from HEAD,
list every final whose KM changes and every class that splits or joins.

## Stage 3 — NGC Glückstadt records to royal_holstein (needs a decision)

Route the NGC sub-section GLÜCKSTADT like NumisMaster's country GLÜCKSTADT.
The Emitent badge changes on those coins. Decisions naming the 94 ids:
_cross_entity 18, merge_decisions royal_holstein 8 / danish_realm 4,
classification_decisions royal_holstein 4 / danish_realm 4 — each checked
and moved. Measure as above. Most of the nine over-merges should dissolve
here, since their Glückstadt members leave danish_realm.

## Stage 4 — what remains of the nine over-merges

A merge-candidate table per case, no_merges / moves only on the curator's
verdict.

## Stage 5 — side findings

- ngc-101324 (KM 103 Krone) vs Hede 121: merge-candidate table.
- c-e9e00fad carries mint «Kopenhagen» that no member gives (all say
  Rethwisch) — same stale self-union pattern, check separately.
