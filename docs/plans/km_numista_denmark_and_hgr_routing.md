# Numista «Denmark» KMs on S-H entities, and Rendsborg routing — plan

Opened 2026-11-24 after dd1986b / cb8c252 (Krause S-H section registers).
Two changes, one at a time, each measured on a trial re-flow before any
commit. Nothing ships without the curator's yes on the measured delta.

## A. Numista issuer «Denmark» on an S-H entity → `dk` (Rendsburg → `hgr`)

**Problem (verified 2026-11-23).** 68 Numista records filed under the issuer
«Denmark» route to royal_holstein (60) or [danish_realm, royal_holstein] (8)
by their mint (Altona 32, Altona+Kopenhagen 28, Rethwisch 5, Rendsburg 2,
Glückstadt+Kopenhagen 1). Their bare KM is read in the entity's section
(`sh`). Checked against NumisMaster / NGC «DENMARK» by KM + years: 66 of 68
are Denmark-volume numbers; the 2 Rendsburg pieces (N#88660 KM 6, N#89702
KM 5) are Krause HOLSTEIN-GOTTORP-RENDSBORG numbers (NumisMaster MC_66626 /
MC_66636; Denmark KM 5 / 6 are the Penning 1602).

**Visible effect today.** 53 of 60 finals are already right: the merger
files a bare number in the volume another member names (`{dk: …}`). Wrong
on the S-H page: c-2a9ecadd «KM-SH# 651, 651.1» (Denmark KM 651);
c-9397f1cf «KM-SH# 701» (Denmark KM 701); four finals with no named volume
show a plain number read as the S-H section (KM 600, 625, 635, 757).

**Is it correct?** Yes in principle: Numista's issuer section follows the
Krause volume (233 / 240 for the S-H issuers, 66 / 68 here, both exceptions
explained). It is the same reading the builder already applies between
Denmark and Norway (a24acea).

**Risk.** Matching scope moves. Numista's number goes from scope `km/sh` to
`km/dk`. It gains agreement with NumisMaster / NGC (`dk`) and LOSES it with
the bare KMs of Bruun (110), ucoin (72) and other Numista records (19) in
the same 62 classes, which stay in `km/sh`. A class held together only by
that bare agreement could split. Must be measured, not assumed.

**Rule.** In `build_numista_seed._apply_km_country_register`: issuer
«Denmark», entity (or every entity of a joint list) in the S-H group, KM
bare → `{dk: …}`; mint Rendsburg → `{hgr: …}`. A list only when all its
numbers share one base (`['640', '640.1']`); a bare list of different bases
stays as printed (the N#119248 case).

## B. Rendsborg records of NGC and NumisMaster → royal_holstein

**Problem.** NGC «Denmark HOLSTEIN-GOTTORP-RENDSBORG» (4 records) route to
danish_realm; NumisMaster country HOLSTEIN-GOTTORP-RENDSBORG (4) routes to
gottorp_duchy. All 8 already sit in the royal_holstein finals Hede 60-63,
held there only by four `_cross_entity.yml` groups. Every new Rendsborg
record would land wrong again and need a hand amendment (the completeness
guard stopped the merger on three of them on 2026-11-23, ngc-1051156 on
2026-11-22). The NumisMaster builder's comment justifies the gottorp route
with «Christian August's brief HGR period 1716-1720» — the attribution the
curator rejected on 2026-07-29 (Rendsburg a Danish royal fortress, Hede
lists the coins in the Frederik IV volume).

**Is it correct?** Yes: the curator's 2026-07-29 ruling in
`_cross_entity.yml` («royal_holstein exactly»). No page change expected —
the finals are royal_holstein already.

**Risk.** Eight seeds change entity file (ids unchanged). The four
cross-entity groups become same-entity; how the merger treats them is to be
seen on the trial. A re-homed seed must not stay behind as orphan-curated in
its old file.

**Rule.** `build_ngc_seed._ENTITY_BY_SUBSECTION` +
HOLSTEIN-GOTTORP-RENDSBORG → royal_holstein; `build_numismaster_seed`
country map → royal_holstein, comment rewritten to the 2026-07-29 ruling.

## Order: B, then A

B first: smaller, no KM semantics touched, expected to leave every final as
it is, so it gives a clean baseline. A second: it changes matching scope and
may move members between classes; with B settled any class change is A's
alone. The two touch different builders (B: NGC + NumisMaster; A: Numista).

## Protocol for each step

1. Code + unit tests (`unittest`).
2. Old vs new builder in memory over the whole cache: list every changed
   record. Expected — B: 8 entity changes, nothing else; A: about 60 KM
   changes (dk) + 2 (hgr), nothing else.
3. Re-seed that source only; keep only the intended field changes (unrelated
   cache-vs-seed drift stays out, as in cb8c252); check no seed id sits in
   two entity files.
4. `trace_coin snapshot` at HEAD; full merge + absorb; `verify_reflow`,
   `audit_lost_citations`, `trace_coin diff`, `validate_decisions
   --check-members`, plus a seed-keyed class-membership diff (every seed
   whose class mates changed).
5. Build danskmoent + the S-H page; list every KM label that changed.
6. **Stop and report** on: any class split or join, any entity change not
   in the expected list, any loss. Otherwise show the delta, commit on yes.

## Out of scope, recorded

- Bruun / ucoin bare KMs on royal_holstein coins are Denmark-volume numbers
  too (110 + 72 in these classes); ucoin's URL country and Bruun's section
  headings could name the volume — a later step, its own measurement.
- c-9397f1cf holds Numista 83067 (Frederik d'Or 1828, KM 699) and 83069
  (1829-1838, KM 701) in one class — merge-candidate table first.
- marker.km_sh still says «volume Schleswig-Holstein».

## B — DONE 2026-11-24

Builder comparison over the whole cache: exactly 8 records change, only
`issuing_entity` (NGC 1050478 / 1051156 / 1051167 / 1051168 danish_realm →
royal_holstein; NumisMaster 66626 / 66629 / 66632 / 66636 gottorp_duchy →
royal_holstein). Re-seed: the same 8 move file, no id in two files; the
re-seed's catalog-mark drift on ngc-1051972 / numismaster-92999 kept out.
Full re-flow: seed_unified, final and class_registry byte-identical to HEAD;
trace_coin diff 0 changes; validate_decisions --check-members clean. The
four _cross_entity groups stay (they record the 2026-07-29 ruling); their
member «home» notes updated.

## A — DONE 2026-11-24

Rule as written above, with the entity test «any entity of the coin (or of a
joint list) in the S-H group». A first cut that looked only at the FIRST entity
caught 39 records and missed the joint-list ones whose seed sits in
royal_holstein (N#132002 / 131337 / 148504 — the 651 / 600 / 635 finals); the
29 joint-list records were checked one by one against NumisMaster / NGC
«DENMARK» by KM base + years + denomination (29 / 29). Builder comparison over
the whole cache: exactly 68 records change, only `catalog.km` (66 → dk, N#88660
/ 89702 → hgr). Re-seed drift (308265 km, 427643 hede, 40843 sieg,
mint_verified, entity_classified_via) kept out.

The trial re-flow stopped twice on the cross-entity completeness guard and once
split a class; each was a fragment of a coin already in a group, verified from
the caches before the curator's yes (2026-11-24):

- KM 701 — NumisMaster MC_66099, NGC 1050449, ucoin 132804 (Denmark KM 701, rows
  1829-1838 FA//FF = danskmoent f6h4 B) were a separate danish_realm final
  c-5219f66c (rendered, pistolenfuss I) → into the Hede 4 group.
- KM 651 — the 2026-06-28 Hede 13 reason read KM 651 as the S-H section; every
  cache says Denmark volume (651.1 / .2 / .3 / 654 = Hede 13A / B / C / D by
  mintmark). Seven danish_realm records of 651.x (three seed_unsorted classes)
  → into the Hede 13 group; correction written into the group's reason.
- KM 661 — ucoin 79557 (4 Skilling 1807 Altona) had only a bare KM 661 shared
  with Numista; recorded as a royal_holstein merge (the curator's 2026-10-22
  shell-review call).

Re-flow: 0 losses (trace_coin, verify_reflow, audit_lost_citations), 7 seeds
promoted out of seed_unsorted, 4 danish_realm finals folded. KM labels fixed:
c-2a9ecadd {dk: 651…, 654}, c-9397f1cf {dk: 699, 701}, c-7116ef28 600,
km-625-chr-v-1771 625, c-05bdb1ab 635, c-9224ec83 757 — all now dk.

Still bare Denmark-volume numbers on royal_holstein finals, from Bruun / ucoin
only (the out-of-scope item below): c-5703ae73 629, c-062a2554 689,
c-5cd784ac 690.1. Related, not done: NGC 1050288 and KMM 78473 (Hede 36, KM 661)
sit in danish_realm seed_unsorted classes, outside the Hede 36 class.

## Follow-up 2026-11-24 — Bruun / ucoin bare KMs, Hede 36 / 29 / 5 fragments

Bare KMs of Bruun (145) and ucoin (86) on royal_holstein are mixed volumes —
against NumisMaster / NGC by KM base + years: Bruun 66 dk, 59 glu, 15 sh, 4 hgr;
ucoin 17 dk, 50 glu, 15 sh, 4 hgr. No single rule.

- ucoin: `period` names the Krause section without exception (Glückstadt →
  glu, Holstein-Gottorp-Rendsburg → hgr, Duchy of Schleswig-Holstein /
  Provisional Government → sh, Rigsdaler / Rigsbankdaler on a `denmark-` URL →
  dk) → `build_ucoin_seed._apply_km_period_register`; 86 seeds, only km. Final
  effect: c-062a2554 KM 689 → dk.
- Bruun: no rule. Altona lots under the same «DENMARK. … Altona Mint.» heading
  carry Denmark numbers (608, 625, 629) and S-H-section ones (138.x, 152,
  154a); Glückstadt / S-H labels would only change display (same match group),
  and Denmark KM 358 is a Copenhagen + Glückstadt type.
- The two Bruun-only Denmark numbers left bare were fragments: Bruun 8045
  (Hede 29A, KM 690.1, CB, 6.13 g) → the Hede 29 group; KM 629 → new Hede 5
  group with NumisMaster 65971 / NGC 1050443 (mintages 207 / 22,721 = Hede 5;
  c-f5aaad22 had rendered beside it). NumisMaster prints mint Copenhagen
  against Hede / Bruun Altona: «suspect» mint_mark on its seed (curator, «(*)»),
  class mint stays Altona.
- Hede 36: NGC 1050288 («1807 MF», KM 661) and KMM 78473 (H 36, Sch 2) joined
  via a cross-entity group, replacing the same-entity merge of 4f90624.

Re-flow: 0 losses; 3 seeds out of seed_unsorted; 3 danish_realm finals folded.
