# docs/research/instruments/ — one dossier per coinage instrument
> **Queue:** `PLAN.md` in this folder is the chronological checklist of every instrument to be written up, with ☑/☐ status — take the next item from there and tick it in the same commit; add any instrument a dossier turns up.
> **Findings about our data:** `FUSS_REVIEW_FINDINGS.md` — every dossier's §7 observation about `data/v2/final` (unsorted coins whose act is now known, mis-placed coins, contradicted values) goes there as one row, keyed by Fuß / entity, in the same commit as the dossier. A session sorting `seed_unsorted` or reviewing a Fuß starts from that file, not from twenty dossiers.

Per-instrument dossiers for the rows of
[`../ordinances_register.md`](../ordinances_register.md). The register is the
index (one line per act: date, issuer, jurisdiction, what it sets); a file here
is the full write-up of ONE act — its text, its parameters recomputed, its
place in the chain of instruments, and what in our data rests on it.

Scope of an instrument that gets a file: it fixes a monetary parameter —
pieces to the mark, fineness (karat / lod), weight, tariff or course,
legal-tender status or demonetisation, a mint's location, a mintmaster's
appointment WITH parameters. An administrative act with no parameter is
listed in the register's «seen, excluded» section and gets no file.

## File naming

`<yyyy>_<slug>.md` — year first so the folder sorts chronologically, then a
snake_case slug from the instrument's OWN name in its own language (§2
tier 1: «Møntordning», «Forordning», «Kongebrev», «Bestalling», «Reces»,
«Reichsmünzordnung» — never a translation):

- `1514_moentordning_malmoe.md` — the Lovkompleks of 1514 (four acts, one
  dossier: Dienis Blicher Brev, Norge 3 Aug 1514, Kvittering 1515, Sjælland
  åbent Brev 24 Aug 1515)
- `1524_moentordning_frederik_i.md` — Møntordning 25 Feb 1524 + the Kongebrev
  to Jørgen Kock
- `1547_bestalling_flensborg.md`
- `1602_forordning_8_september.md`

Several acts that belong together (an ordinance and its supplement, a
Møntordning and the Kongebrev that executes it) share one file; the register
still gets one row per act, each pointing at the same file.

`../moentordning_1541.md` predates this folder and stays where it is; the
register links it.

## Section template (fixed order; keep the numbering)

1. **Identification** — date (as printed by the source; old-style where the
   source gives it), the instrument's name exactly as the source prints it,
   issuer (ruler / Rigsraad / Kancelli), addressee, jurisdiction (DK / NO /
   S-H ducal / S-H royal / HRE), archival signature if known (Rigsarkivet
   series + folio).
2. **Source chain** — where the original text is (archive / printed
   collection: Secher CCD vol + page, Kolderup-Rosenvinge, Paus, Schou,
   Hirsch), every reproduction we used (Wilcke vol + page, Galster, danskmoent
   `mord` page), and our cache path for each. Say explicitly which of them is
   the ACT and which is a RETELLING — a Wilcke paraphrase is not the act.
3. **Verbatim text** — the passage(s) in the original language, with page
   hints, followed by a Ukrainian translation marked as such. Spelling as
   printed; never normalised.
4. **Parameters** — one table row per coin the act names: metal · pieces per
   mark (which mark) · fineness in the act's own unit (karat / lod / grän) →
   ‰ · rough weight g · fine weight g · tariff / course. Every value marked
   TARGET (the act) — an assay or a mint account is an OUTCOME and goes in a
   separate, labelled table if cited at all. Our recomputation stands beside
   the source's figure; a parameter the act does not state is written as a
   gap («not stated»), never filled from the coins.
5. **Mints and mintmasters** named by the act.
6. **Antecedent and successor instruments** — which act it restates, amends
   or voids; which act later replaces it. Links to their dossiers / register
   rows.
7. **Our data** — the fuss and phase(s) it anchors in `data/shared/fuesse.yml`
   / `data/v2/locations/*.yml`, the `refs_pool.yml` keys that quote it, and
   the coins in `data/v2/final/` classified under it (seed ids, from
   `trace_coin.py`).
8. **Open questions** — each paired with what would settle it. Hypotheses
   labelled as such (§0b).
   **Source-internal discrepancies get their own marked block** (a «⚠ Source-internal
   discrepancies» sub-section under §4, as `1563_klippinge_syvaarskrigen.md` §4.4): when
   one source gives a figure in two forms (Wilcke's text vs his own table; a date in the
   text vs the footnote), or our data carries a value the source does not print, list
   both readings side by side AND flag the figure with ⚠ where it appears in the
   parameters table. A reader who opens only the table must see that the value is
   contested; burying it in §8 is not enough (curator direction 2026-10-14).
9. **Sources consulted** — full bibliographic lines, with URLs and archive
   copies.

Score with `.claude/skills/research-dossier/dossier_helper.py <file>` and the
`research-dossier` rubric; ship at ≥ 8.0, and record the score with the
commit SHA in a closing line. An unavailable parameter stays a labelled gap —
never invent to raise the score.
