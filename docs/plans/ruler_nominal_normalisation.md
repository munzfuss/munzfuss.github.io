# Ruler and nominal normalisation — work plan (2026-10-26)

Trigger: on the danskmoent Lübischer Münzfuß page the same ruler and the same
denomination are written several ways side by side («Erik VII» / «Erik VII of
Pomerania»; «1 Sterling (= 3 Pennings)» / «1 Gros (9 Penning)» / «Gros = 9
Pennings»). Survey of the 136 finals in the rebuild scope (lybsk møntfod,
nobelfod, guldgyldenfod) below. Scope of every change: the Fuß list in
`data/v2/_rebuild_scope.yml` (other finals keep their foundation values —
`ruler` and `nominal` are foundation-immutable in absorb).

## 0. Layer (ARCHITECTURE «Layers»)

- The seed keeps the source's spelling (§0b-1, D50). Nothing is rewritten there.
- Ruler display form: the merger, `_canonical_ruler_out` →
  `lib.ruler_reigns.canonical_ruler_display` (exists since 2026-10-23).
- Nominal display form: the merger picks the top-authority member's nominal;
  a per-class curator nominal goes in `classification_decisions` (D50).

## 1. Rulers — findings

| Variant on the page | Source | Why it survives |
|---|---|---|
| Erik VII of Pomerania | Bruun | `_KING_DISPLAY_RE` matches «Name roman» only, not «… of Pomerania» |
| Christopher III of Bavaria | Numista | same |
| Christian I. (c-5be595df, 31 members) | KMM, one of several spellings | canonicaliser maps it to «Christian I»; the final still stores «Christian I.» — to investigate (absorb keeps the stored ruler?) |
| Kristian 1 | KMM | name not in `_KING_DISPLAY_NAME` |
| Chrisytian 1 | KMM | source misprint |
| Ridsrådet | KMM | source misprint of «Rigsrådet» |
| Christoffer III vs Christopher III | Galster / Numista | two spellings of one king |
| None (3 Kobbersterling) | KMM | KMM record has no authority |

Steps:
1. Extend `canonical_ruler_display`: «<Name> <roman> of Pomerania/Bavaria» →
   Erik VII / Christoffer III; «Kristian» → «Christian»; «Christopher» →
   «Christoffer» for the Danish king (curator to confirm the display form).
2. Misprints («Chrisytian 1», «Ridsrådet»): curator decision — normalise as
   spelling, or keep the printed form visible (the «(!)» priority rule is for
   wrong VALUES; a misspelt name may count as spelling). No mechanism exists yet
   for a ruler mark.
3. Find why c-5be595df keeps «Christian I.» after a rebuild; fix in absorb if
   the rebuild path does not re-derive `ruler`.
4. Unit test over the variants; measure on every entity (shared code, §9b).

## 2. Nominals — findings

| Variant | Source | Note |
|---|---|---|
| 1 Sterling (= 3 Pennings), 1 Gros (= 9 Pennings), 1 Hvid (= 4 Pennings) | Numista | the «= N Pennings» part is Numista's equivalent, not on the coin (§1: equivalents go in `note`) |
| Gros = 9 Pennings, 1 Hvid = 4 Pennings | Numista | same, other format |
| 1 Gros (9 Penning), 1 Sterling (3 Penning) | Galster | Galster's own equivalent in brackets |
| (?) — 11 finals, Christian I | KMM | record has no nominal; the template shows «(?)» |
| 1 Kobbersterling? | KMM | the source's doubt |
| 1 Korshvid, falsk | KMM | «falsk» = forgery → §9 exclusion candidate |
| 1 Penny (Gaute Ivarsson), 1 Pfennig (Christian I, NGC) | Bruun / NGC | English / German form; Norwegian archbishop and an NGC Christian I piece — check scope and the period form |

Precedent: D50 put «1 Sterling» on the two Kobbersterling classes where Numista
printed «1 Sterling = 3 Pennings».

Steps:
1. Curator rule for the equivalent suffix: strip «(= N Pennings)» / «= N
   Pennings» / «(N Penning)» from the displayed nominal (merger, after the
   top-authority pick) — or prefer the Danish source's form when the class has
   one. Decide whether the stripped equivalent goes into `note`.
2. «(?)» nominals: read the KMM cache (`nominal`, `typeNumber`, `title`) of the
   11 records; where it names the denomination, the builder takes it; where it
   does not, the gap stays.
3. «1 Kobbersterling?»: the «?» → `nominal_verified: false`-style marker or keep
   as printed — curator.
4. «1 Korshvid, falsk»: present to the curator as an exclusion (PB-12).
5. «1 Penny» / «1 Pfennig»: check each against its catalogue; Danish form or
   out of scope — curator.

## 3. Unmerged duplicates seen in the same table

- Numista 152728 (Gros, Gurre, 1424-1430, Sieg E7-15) stands alone; Galster 16
  is a Gros of Gurre 1430-1439 (with Heljeback G 16). Same mint and
  denomination, different windows → merge-candidate-table.
- Sweep the other Numista singletons of the scope Fuß (Erik VII, Christoffer
  III, Christian I) for the same one-to-one Sieg ↔ Galster pairing used for
  G 4 / G 9 (2026-10-26).

## 4. Order

1. Rulers 1.1 + 1.3 (code, no curator input) → re-flow → verify_reflow → page.
2. Curator questions in one message: ruler misprints, nominal suffix rule,
   «?» nominal, forgery, Penny/Pfennig, Gros 152728.
3. Apply the decisions → re-flow → page in every language → commit.
