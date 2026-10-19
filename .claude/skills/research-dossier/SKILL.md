---
name: research-dossier
description: >-
  Write, extend, and SCORE a research dossier under docs/research/<topic>.md against a fixed
  6-criterion completeness rubric, returning X/10 so the work can loop until it clears a
  threshold (default 8+). Use when assembling a depth-first investigation of one subject — a
  Müntzfuß's parameters through time, a coin group, a contested attribution, an ordinance
  lineage — where the evidence and the analysis are themselves the deliverable. The rubric
  checks: scope stated, parameters complete per period, every change tied to a dated named
  instrument, provenance chains named (who reproduced whom), open questions labelled with what
  would settle them, and figures independently recomputed. SCORING is a standalone READ-ONLY
  operation — a bare «оціни / score» request returns the X/10 + gap list and changes nothing.
  Trigger phrases: "створи документ про цю стопу", "напиши дослідницький документ", "онови
  досьє", "оціни повноту документа", "score the dossier", "write a research dossier", "how
  complete is this research note".
---

# research-dossier — author + score a `docs/research/` dossier

Executable form of `docs/research/README.md` (what a dossier is for) + CLAUDE.md **§0**
(no invention) + **§0b / §0b-1** (hypothesis ≠ fact; check the curation layer) +
**§5 / §5a** (source hierarchy, verbatim quote + page hint) + **§0z** (this surface is
role-1 — written for the next analyst, not for the end-reader).

It governs files under `docs/research/*.md` only. It does NOT write rendered prose
(`fuesse.yml`, `data/v2/locations/`) — that is `fuss-description`'s job — and it does
NOT change coin data. A dossier is **substrate**: the assembled evidence a later
decision is made from.

Helper (mechanical signal-scan, candidates not verdicts):
`python .claude/skills/research-dossier/dossier_helper.py <path> [--list]`

## Reader and register

Role-1 (AI / the next analyst), per §0z. That means: dense, no hand-holding, project
vocabulary fine, `data/v2/...` paths fine, internal decision rationale **encouraged** —
all the things forbidden in the rendered artefact belong here. What is NOT allowed is
the thing forbidden everywhere: an unlabelled guess.

Language: match the surrounding dossiers (most are English with Danish/German verbatim
quotes kept in the original). Never translate a verbatim quote.

## The six criteria

1. **Scope stated.** The opening says what question the dossier settles, what it
   deliberately excludes, and where the excluded part lives (a sibling dossier, a TODO,
   «not yet written»). A dossier without a boundary grows into everything and settles
   nothing.
2. **Parameters complete per period.** For a standard, every period carries the full
   parameter set the sources can give — pieces per mark, rough weight, fineness (in the
   source's own unit AND in ‰), fine weight, and the tariff/value if one is decreed.
   A cell the sources do not supply is written as an explicit gap, never left blank and
   never filled by inference-presented-as-fact.
3. **Every change tied to a dated named instrument.** Each parameter change names the
   ordinance / decree / plakat and its date. «The fineness drifted to .972» is not
   admissible; «Forordning 8. September 1602 sets 23⅓ Karat» is. Where a change is
   visible in specimens but no instrument is known, say exactly that.
4. **Provenance chain named.** When a source REPRODUCES another, both links are named —
   «Galster's lightly reworked version of Wilcke's scheme, via danskmoent» is a different
   citation from «Wilcke». Catalogues derived from each other (Sieg→Hede→Schou) are not
   independent witnesses and the dossier must say so where it leans on them. Each source
   carries a verbatim quote and a page hint per §5a.
5. **Open questions labelled — with the thing that would settle them.** Every unresolved
   point is listed explicitly, marked as open, and paired with the specific source or
   measurement that would close it. A hypothesis carries the word; a conclusion carries a
   citation. Nothing sits in between.
6. **Figures independently recomputed.** The source's own numbers are re-derived from the
   stated parameters and the agreement (or disagreement) recorded, and our own data is
   inventoried against the source with divergences named. A dossier that only transcribes
   has not checked anything.

## Scoring rubric — 10 points

| # | Criterion | Max | Award / deduct |
|---|---|---:|---|
| C1 | Scope stated | 1.5 | 0.75 question named · 0.75 exclusions named with their home. |
| C2 | Parameters complete | 2.5 | Full set per period. **−0.25** per period missing a parameter that the cited sources DO supply. A parameter genuinely absent from all sources, written as an explicit gap, costs nothing. Floor 0. |
| C3 | Dated named instruments | 2.0 | 1.0 every change carries an instrument + date · 1.0 no undated drift narrated as if decreed. **−0.5** per change described without its instrument where one exists. |
| C4 | Provenance chains | 2.0 | Start 2.0. **−0.5** per source cited without a verbatim quote or (where the work is paginated) a page hint. **−0.5** per reproduction cited as if original (the Galster-rework class). **−0.5** per derived-catalogue agreement presented as independent corroboration. **−0.5** per source-internal discrepancy (a source's text vs its own table or footnote; our value vs the source's print) that is not listed in a marked «⚠ Source-internal discrepancies» block AND flagged at the figure in the parameters table — a reader of the table alone must see it (curator 2026-10-14). |
| C5 | Open questions labelled | 1.0 | 0.5 all known-open points listed · 0.5 each paired with what would settle it. **Hard cap: any hypothesis stated without a hedge marker → C5 = 0** (§0b). |
| C6 | Recomputation | 1.0 | 0.5 source figures re-derived and the agreement stated · 0.5 our own data inventoried against the source. |

**Threshold: ship at ≥ 8.0.** Below 8 the dossier has a real gap in scope, parameters,
dating, or provenance. A 10 means the subject is documented as completely as the
available sources allow — which is NOT the same as «resolved»; a dossier can score 10
with five open questions, provided each is labelled and paired.

## Workflow

**Two modes — do NOT auto-chain.**
- **SCORE** (default for «оціни повноту», «score the dossier») — READ-ONLY. Emit the
  score + gap list. Change nothing. Stop.
- **WRITE / EXTEND** — runs only when asked to create or update. SCOREs the existing
  file first (skip for a new one), then writes.

**WRITE mode:**
1. Check for an existing dossier on the subject (`ls docs/research/`) — extend rather
   than fork. A second dossier on one subject splits the evidence.
2. Gather sources FIRST, verbatim, before writing a line of analysis — start with the
   local full-text index (section below), then the web. Read the page; don't summarise
   from a search snippet. If a snippet is all you have, the claim is labelled as
   unverified until the page is opened.
3. Write. Recompute every figure you transcribe (C6) — the recomputation is what turns
   a transcription into a check.
4. Any web fact that will ALSO reach the rendered artefact gets its `refs_pool.yml`
   entry in the same change (§5b). A dossier-only fact does not need a pool entry, but
   still needs its quote + page.
5. Re-score. Loop until ≥ threshold or until the only remaining gaps are genuinely
   unsourceable — then cap, name the ceiling, and stop.

## Finding the evidence — `kb search`

The harvested corpus (Secher, Schou, Mordhorst, Wilcke 1919 / 1924 / 1950, Galster,
Jensen, Denar til daler, Munro, Hede pages, Bruun I–V, danskmoent …) is indexed for
full-text search with old spellings and OCR slips folded. Full recipe: `scripts/kb/README.md` §«Researching a Müntzfuß».

```
.venv/bin/python scripts/kb/kb.py build                     # once per session; search warns when stale
.venv/bin/python scripts/kb/kb.py works                     # ids and kinds of what is indexed
.venv/bin/python scripts/kb/kb.py search "kroner 1618 lødig mark" --kind source      # the act (C3)
.venv/bin/python scripts/kb/kb.py search "<subject words>" --kind literature          # the readings (C4)
.venv/bin/python scripts/kb/kb.py search "<nominal> <year>" --kind catalogue         # Hede / Bruun (C6)
.venv/bin/python scripts/kb/kb.py search 'NEAR(krone* lødig*, 10)' --fts --work wilcke-1919
```

- Order for a Fuß: the instrument (`--kind source`) → who read it and with which
  figures (`literature`, per work) → the coins (`catalogue`). That order is C3 → C4 → C6.
- A hit is `work · p. N · path:line`: open the file there, read the page, quote it
  verbatim; check OCR'd figures on the page image. p. N is the printed page.
- **No hit ≠ no source** — not indexed: rigsarkivet scans (handwriting), Bruun 1928,
  paper-only works (Lange, Sieg, printed Hede). Name such a gap in the dossier (C2/C5)
  and go to the web chain (CLAUDE.md «Tool fallback chain»).

## Output format (emit this every SCORE)

```
DOSSIER: docs/research/<file>.md — <subject>
SCORE: 7.0 / 10   (threshold 8.0 → NOT YET / ✓ CLEARS)
  C1 Scope          1.5/1.5  ✓
  C2 Parameters     1.75/2.5 — 1591-93 period has no rough weight (source has it)
  C3 Instruments    1.5/2.0  — «fineness settles at .979» has no instrument named
  C4 Provenance     1.5/2.0  — 1602 table cited as Wilcke; it is Galster's rework
  C5 Open questions 1.0/1.0  ✓
  C6 Recomputation  0.5/1.0  — source figures re-derived; our data not inventoried
GAPS (each → +points, lowest-effort first):
  1. [C4] re-attribute the 1602 table to Galster-via-Wilcke.        (+0.5)
  2. [C6] inventory our final entries against the table.            (+0.5)
CEILING NOTE: <only if a gap is genuinely unsourceable — name it>
```

## Hard rules

- **Never invent to raise the score (§0).** An unavailable parameter stays a labelled
  gap. A dossier scoring 8 honestly beats one scoring 10 with a plausible-sounding
  number nobody printed.
- **Verbatim quotes stay in their language** and are marked as quotes. Translating a
  source quote into the dossier's prose language silently converts evidence into
  paraphrase.
- **Hypothesis carries the word (§0b).** «Probably», «likely», «suggests» without an
  explicit «hypothesis — would be settled by X» is a C5 zero, not a deduction.
- **Check the curation layer before calling our own data wrong (§0b-1).** Run
  `trace_coin.py why <seed-id>` before writing «our value disagrees with the source».
- **A dossier is append-oriented.** Correct an earlier wrong conclusion in place, but
  record what was claimed and what disproved it — the next session needs the trail
  (§0b). Do not silently delete a retracted claim.
