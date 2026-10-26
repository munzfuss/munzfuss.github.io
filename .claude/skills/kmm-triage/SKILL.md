---
name: kmm-triage
description: >-
  READ-ONLY usefulness triage of the KMM / Nationalmuseet (kmk-* seed) records
  inside one Müntzfuß, before a clean-up: sorts every KMM record that sits in a
  final of the Fuß into the curator's categories by three signals — catalogue
  index, weight, image — 1 useless (none), 2 one of the three (2.1 index only
  but another source in the class gives it too; 2.2 index only and unique,
  ranges like «Schou 10-50» counted as covering), 3 two of three, 4 all three.
  Category 1 is the list of undocumented-stub exclusion candidates. Use for
  «почисти kmk / KMM записи в стопі», «чистка некорисних kmk записів»,
  «категоризуй записи KMM», «які kmk записи некорисні / undocumented stub»,
  «оціни корисність записів KMM у стопі X», «KMM triage». Helper
  `kmm_triage.py --fuss <id>` writes the categorised table; the curator decides,
  exclusions and merges go through PB-12 / `v2-merge-coins`.
---

# kmm-triage — which KMM records of a Fuß are worth keeping

The KMM (Den Kongelige Mønt- og Medaillesamling, Nationalmuseet) seeds are
the largest and thinnest source in the project: many objects carry no
nominal, no weight, no photo and no catalogue number, and each still becomes
a row or a class member. Before a Fuß is cleaned, every KMM record in it is
sorted by what it contributes. This skill only REPORTS; nothing is excluded
or merged without the curator's «так».

## Categories (curator 2026-10-26)

| cat | meaning | contributes |
|---|---|---|
| **1** | useless | no index, no weight, no image |
| **2** | a little use | exactly one of the three |
| 2.1 | — index only, **not unique** | another source in the same class gives the same index (equal, or inside a printed range: «Schou 10-50» covers 23) |
| 2.2 | — index only, **unique** | no other source in the class gives it |
| 2-w / 2-img | — weight only / image only | |
| **3** | useful | two of the three |
| **4** | very useful | image + index + weight |

## Signals — what the helper reads

- **index** — the seed's normalised `catalog` (Galster, Schou, Hede, Sieg,
  Hauberg, … including `others`; `numista`, `bruun_collection_id`,
  `galster_volume` ignored). A KMM `typeNumber` the builder did not parse
  («sch mgl», «G», «schou cf. 90») is listed separately: look at it — a «cf.»
  is not an index (anti-pattern 5), a bare «G» is nothing.
- **weight** — the seed's `weight_rough_g`.
- **image** — `scripts/cache/kmk/web/<id>.json` `billeder` non-empty, else the
  `<id>.html` page carrying an `ImageObject` / `/asset/`. If neither is cached
  the image is «?»: fetch with `scripts/fetch_kmk_web.py <ids>` (the helper
  prints the command) and re-run. Never report «no image» from a missing
  cache.
- **uniqueness** — compared per register against the members of the same
  final from OTHER sources (another KMM record does not count: the question is
  what this source adds).

## Procedure

1. `.venv/bin/python .claude/skills/kmm-triage/kmm_triage.py --fuss <fuss>
   --md <scratchpad>/kmm_<fuss>.md` — counts per category, the unknown-image
   fetch line, unparsed typeNumbers, and the full table (seed, inventory no.,
   class, nominal · ruler, index, unique part, weight, image, KMM-only class).
2. Fetch any «?» images and re-run until none is unknown.
3. Present to the curator: the counts, then category 1 in full (exclusion
   candidates), then 2.1 (the next candidates), with the KMM-only flag — a
   KMM-only class disappears from the page when its records go.
4. Act only on the curator's verdict, per group:
   - exclusion → `data/v2/exclusions/<entity>.yml`, `category:
     undocumented_stub`, one entry per seed with the reason (PB-12; a filter
     alone does not remove a seed already there);
   - a record with an index that stands alone although a class with that index
     exists (missing nominal kept it out) → `merge-candidate-table`, then
     `v2-merge-coins`.
5. Re-flow (merge + absorb), `verify_reflow.py`, rebuild, commit.

## Hard rules

- Read-only until the curator answers. No exclusion, merge or erratum on the
  triage alone.
- An unknown image is «?», never «—».
- Uniqueness counts other SOURCES only, and a range covers its members.
- Category 1 in a KMM-only class removes a row from the page: say so.
