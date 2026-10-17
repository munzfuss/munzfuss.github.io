# Undated coins on the Denmark page — groups and plan

> Working plan, opened 2026-10-17 on the curator's request («приймемо цю таблицю
> як план дій … по кожному рядку по черзі»). One row at a time; each row's
> decision is the curator's. Index entry: `docs/TODO.md` §EB.

## Where the number comes from

The Denmark page assembly (`scripts/build.py::_assemble_v2_location`) drops a
coin for one of three reasons. Counted 2026-10-17 after commit `80d1dd4`:

| Reason | Coins | Nature |
|---|---|---|
| year outside the entity's consume-window (`danish_norway` after 1814, `royal_holstein` after 1864, …) | 341 | page scope by design — not a loss |
| no year information | 185 | this plan |
| out-of-scope metal (paper money etc.) | 16 | page scope by design |

Already done before this plan: KMM `sluttid`-only years read (`aeab3e2`),
reign-window placeholder (?) for an undated coin whose ruler is known, chosen
by issuer (`c6202fa`, `80d1dd4`) — 1776 → 542 drops.

## The 185, by what could date them

| # | Group | Coins | What could date them | Status |
|---|---|---|---|---|
| 1 | Ruler of another house, no reign table | 61 (78 by the wider match) | reign tables for Sønderborg, Plön/Norburg, Schaumburg-Pinneberg, Oldenburg, Gottorp prince-bishops, Rantzau — each with a source; or entity re-routing | **done 2026-10-17** (57 stubs excluded, Sønderborg table) |
| 2 | Medieval rulers (before 1481) | 44 | datable, but outside the page's span — exclude from the page rather than date? | open |
| 3 | No ruler, no catalogue | 29 | hopeless except nominals of one period (Kobbersterling = Erik af Pommern) | open |
| 4 | Catalogue index matching a dated type | ~12 | not years — merge into the type (`merge_decisions`, a comparison table per pair) | open |
| 5 | «Aahuset L. Chr. Larsen» | 8 | probably a private issuer — unchecked | open |
| 6 | Unambiguous misspellings of Danish kings | ~6 | aliases in the normaliser («Chrtistian 4», «Chritian 4», «Chrisytian 1», «Kristian 1», «Ridsrådet») | open |
| 7 | Years printed in the ruler string | 5 | «Hans den Yngre af Slesvig-Holsten-Sønderborg 1564-1622» — KMM's own reign years, as (?) | open |
| 8 | Bare «Christian» / «Frederik» | 6 | ambiguous without other data | open |
| 9 | Modern / foreign («Margrethe 2», «Carl 15.») | 4 | outside the page | open |

Groups overlap at the edges (a record can be both «other house» and «years in
the ruler string»); counts are from one classification pass.

Separate finding, handed to a parallel session 2026-10-17: the NGC parser does
not read dates printed with a letter for a digit («16Z4(a)» = 1624).

## Row 1 — rulers of other houses (analysis 2026-10-17)

78 records match a non-royal ruler name. They are of two kinds:

**A. 58 empty KMM stubs.** Inventory-list objects from the accessions of
1883–84 (`GP 888.x`, 41) and 1888–89 (`GP 982.x`, 17): `nation: Slesvig-Holsten`,
`workDescription: Mønt`, an `authority` — and nothing else: no nominal, no
year, no weight, no catalogue index, no image check done. 50 of them sit in
`royal_holstein` only because the KMM builder's nation fallback routes
«Slesvig-Holsten» there, although the authority names another issuer:
Schaumburg-Pinneberg counts (Adolf XIII, Ernst III, Otto V, Otto VI, Justus
Herman), Ditlev Rantzau, Anton Günther (Oldenburg), Gottorp dukes and the
Gottorp prince-bishops (Christian Albert, Karl Peter Ulrik, Johan Frederik,
August Frederik, Christian August), Alexander (Sønderborg?). 8 sit in
`norburg_plon_duchy` (Hans Adolf of Plön, August of Nordborg).
Even with a reign window they would render as rows «(?) · reign (?)» with
nothing else.

**B. 20 records with a nominal.** 12 Sønderborg (Hans den Yngre, «Johann»:
2 / 4 Schilling), 4 NGC royal_holstein (Friedrich I / II with MB numbers —
row 4 merge candidates), 1 Gottorp (Johan Friedrich, 4 Skilling lybsk,
Jungk 316), 3 danish_realm «Johan / Johannes» pennies (medieval — row 2).

Options for the curator (row 1):
- A: (a) re-route each stub to its issuer's entity by an entity-routing rule
  keyed on the KMM authority (most then leave the Denmark page by the issuer's
  consume-window); (b) exclude them as empty stubs (the 2026-10-15 category-C
  precedent, `docs/research/luebischer_muenzfuss.md` §6b); (c) date them by
  new house tables and keep them.
- B: a Sønderborg reign table (Hans den Yngre 1564–1622; source to be cited),
  then the existing placeholder rule dates the 12; the NGC four go to row 4.

**Decision and outcome (curator 2026-10-17: «Виключи 58 порожніх заглушок …
як порожні (як категорію C 2026-10-15); і додай таблицю Sønderborg з
джерелом»).**
- A: 57 excluded as `undocumented_stub` (49 in `exclusions/royal_holstein.yml`,
  8 in the new `exclusions/norburg_plon_duchy.yml`). The 58th candidate,
  `kmk-83149` «Alexander» (GP 982.173), has a weight and typeNumber «Lange»
  (no number), so it is not empty and stays — open.
- B: `sonderburg_duchy` reign table, Hans (Johann) der Jüngere 1564–1622
  (NDB 10, 1974, S. 534 f.); 12 Sønderborg coins now carry 1564–1622 (?).
  Commit `697bcee` (code + exclusions) and the re-flow after it.
- Left over: the 4 NGC royal_holstein Friedrich I / II records → row 4;
  the 3 danish_realm «Johan / Johannes» pennies → row 2; Sonderburg KM 11
  (NGC 1172866 + numismaster-120993 vs km-11-hans-jr-sonderb-1620) needs a
  merge decision (found by the NGC session).
