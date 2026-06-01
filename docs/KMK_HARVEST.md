# KMK / KMM Copenhagen harvest — strategy & process notes

> **Audience: AI (future-me).** Reusable playbook for harvesting the
> *Royal Coin Cabinet* (Den Kgl. Mønt- og Medaillesamling, KMM) held by
> the Danish Nationalmuseet, via the open Nationalmuseet API. **Not
> user-facing prose** — see CLAUDE.md §0z. Companion to `IKMK_HARVEST.md`
> (Berlin). Source-policy summary lives in `docs/SOURCES.md §8.3`.

## Status

**Strategy designed 2026-06-01; harvester NOT yet built.** This doc is the
plan. The 8th harvested source (after Numista, ucoin, Bruun, Wilcke,
danskmoent/Galster, NumisMaster, IKMK). Live API sampling confirmed every
technical assumption below.

## Why this is OK to harvest

Nationalmuseet's collection API (`api.natmus.dk`) is a **public, no-auth**
open-data endpoint published by a state museum. No API key, no documented
rate limit, no «no scraping» clause. This project is a non-commercial
scholarly register (CLAUDE.md «Project-context note») → squarely on the
permitted side. **Be polite anyway**: search_after paging at 500–1000/page
with a short delay between pages; cache locally; name the project in the
User-Agent. Attribution string: «København, Den Kgl. Mønt- og
Medaillesamling, Nationalmuseet».

## API mechanics (all live-verified 2026-06-01)

- **Endpoint**: `POST https://api.natmus.dk/search/public/raw` — body is a
  raw Elasticsearch query DSL. (`GET /search/public/simple` is broken,
  HTTP 500 — do NOT use.)
- **Index scope**: `collection.keyword = "KMM"` + `type.keyword = "object"`
  = **639 600** coin/medal objects (the rest of the 707 969 KMM docs are
  `still`/asset image records, not objects).
- **No-auth, no observed rate limit.** API is flagged work-in-progress, so
  expect occasional shape drift; pin nothing, introspect at build time.
- **Deep pagination = `search_after`** (the make-or-break detail):

  ```jsonc
  POST /search/public/raw
  {
    "size": 1000,
    "sort": [{"_id": "asc"}],          // stable total order; _id = "KMM-<n>"
    "search_after": ["KMM-100"],        // omit on first page; else last hit's .sort
    "query": {"bool": {"filter": [
      {"term": {"collection.keyword": "KMM"}},
      {"term": {"type.keyword": "object"}},
      <SCOPE FILTER, see below>
    ]}}
  }
  ```

  Verified: page 1 (`KMM-1, KMM-10, KMM-100`) and page 2 via
  `search_after:["KMM-100"]` (`KMM-100000…`) have **zero overlap** —
  `search_after` bypasses the 10 000-doc `from+size` ceiling cleanly. No
  scroll/PIT needed. Carry each page's last hit `.sort` array forward.

## Anatomy of a record (`_source`)

Every populated field is a **top-level key** (ES omits absent fields, so
sparse records are tiny — 792 bytes). **Store the entire `_source` per
record** (user directive: «якщо там json то зберігай його цілим»). Keys
seen, grouped by usefulness:

### Identity & inventory
- `id` — internal int (the `_id` is `"KMM-<id>"`).
- `objectIdentification` — inventory string, e.g. `"FP 5756.2"`.
- `numberPrefix` / `numberData` / `numberSuffix` — the same inventory
  number, decomposed (`FP` / `5756` / `2`).
- `protocol` / `protocolPage` — accession-protocol locator (provenance).
- `collection` (`"KMM"`), `type` (`"object"`), `workDescription`
  (`"Mønt"` = coin / `"Medalje"` / `"Regnepenning"` = jeton).

### Classification-relevant (the bread-and-butter)
- `nominal` — denomination string, e.g. `"penning"`, `"1/16 thaler"`,
  `"daler"`, `"4 skilling"`. **Scalar string** (NOT the nested object IKMK
  uses).
- `authority` — **ruler**, e.g. `"Svend 2 Estridsen"`, `"Johan Adolf"`,
  `"Frederik 3"`. ~89 % populated in-scope.
- `nation` — **realm / issuing region**, e.g. `"Danmark"`,
  `"Slesvig-Holsten"`, `"Tysk, Hamburg"`. ~95 % populated. **Messy** — see
  scope section. Primary entity-routing signal when `place` is absent.
- `place` — **mint**, e.g. `"Lund, Bosi"` (note: can be `City, mintmaster`
  combined → split on parse). ~27 % populated.
- `typeNumber` — **catalogue ref**, e.g. `"Hbg 32"` (Hauberg), `"Hede …"`,
  `"Dav …"`, `"Sieg …"`, `"Schou …"`. ~65 % populated; build_kmk_seed captures
  ~64 % (16 supported catalogues, abbreviation-aware + multi-field colon/comma
  parse). Heavily abbreviated (`H.`=Hede, `Sch`=Schou, `G.`=Galster, `Th.`=
  Thomsen, `Bgs.`=Bergsøe, `Hbg`=Hauberg) + colon multi-field («H: 134B; Sch: -»,
  `-` = not listed).
  - **Ambiguous bare prefixes `S` / `B` — left UNMAPPED (investigated 2026-06-01,
    inconclusive).** `S N` (34 recs, ~all Christian IV, range 14-195) and `B N`
    (54 recs, ~6 of them medals) could be Schou/Sieg resp. Behrens/Bergsøe.
    Cross-checked against our corpus three ways: (a) structural — `S` never
    co-occurs with `Sch`/`Schou`/`Sieg` in a record (so it's a lone abbrev,
    doesn't say which); (b) coarse (ruler,nominal) join hinted Schou (4) over
    Sieg (0) but those are likely coincidental; (c) **precise Hede-join (3 S+H
    records) did NOT confirm** — our schou/sieg for the exact Hede# disagrees
    with the S-value, and one S-value is decimal (`43.1`, Sieg-style format).
    Net: contradictory, zero clean confirmations → mapping would risk
    systematic mis-attribution (§9.4/§0). `B` likewise — corpus carries ~0
    Behrens/Bergsøe to match against. Revisit only if a Hede↔Schou↔Sieg ground-
    truth table (e.g. fuller danskmoent Hede harvest) makes the join decisive.
- `creationEvents[]` — dating; each `{yearFrom, yearTo, …}`. **Years are
  STRINGS** → numeric-coerce at parse (a lexicographic range leaks short
  Roman years like `"181"`).
- `materials[]` — **array of `{material:"<string>"}` objects** (NOT bare
  strings). Values are DIRTY and need a normaliser: `sølv` / `guld` /
  `kobber`/`Kobber` / `bronze`/`Bronze` / `bly`, compound `sølv-kobber` +
  `Kobberholdigt sølv` (→ billon), numismatic abbrevs `AR`(silver) /
  `Æ`(bronze), uncertainty suffixes `sølv?` / `sølv(?)` / `sølv? forgyldt?`,
  plating notes `Bly, forkobret` / `bly, forgyldt`, plus non-coin noise
  (`ler`=clay, `jern`=iron, `messing`=brass, `Dårligt metal`). Map:
  casefold → strip `?`/`(?)` → take primary token → `sølv→silver, guld→gold,
  kobber→copper, bronze→bronze, bly→lead, sølv-kobber/kobberholdigt
  sølv→billon, ar→silver, æ→bronze`; unmapped → metal absent. ~47 % populated.
- `measurements[]` — **WEIGHT ONLY**: every entry is
  `{unit:"Gram", dimension:"Vægt", data:0.85}`. Verified across the whole
  collection: the ONLY dimension is `Vægt` / unit `Gram` (25 105 records).
  **KMM records NO diameter, ever** — drop `diameter_mm` from the mapping.
  No fineness either. ~19 % carry the weight.

### Extras (collect, low project-priority)
- `related.assets[]` — **coin images**: `{id:"KMM-117497",
  filename:"KMM_294_a.tif", type:"still", subtype:"Standard"}`. Avers/revers
  scans, **licensed CC-BY-SA** (named photographer on the object page). Image
  URL = `https://samlinger.natmus.dk/kmm/asset/<n>.<fmt>` where `<n>` is the
  numeric part of the asset `id` (`KMM-117497` → `117497`):
  `…/117497.jpg?maxsize=300` (thumb), `…/117497.jpg?maxsize=org&download=true`
  (full JPEG), `…/117497.org` (original 30 MB .tif). Attribution string:
  «Foto: <photographer>, Nationalmuseet (CC BY-SA)».
- `foundEvents[]` — find-spot / provenance (KMM's real differentiator).
- `descriptions[]` — free text; **~0 % populated** for coins (no legends,
  unlike IKMK). Don't expect inscriptions here.
- `classifications[]`, `usageEvents[]`, `accessionEvents[]`,
  `nationalImportanceCategory*`, `drawingExists`.

## Scope filter (the hard part — `nation` is dirty)

KMM nation strings vary by case, whitespace, punctuation and a `"Tysk, "`
prefix. Filter by **normalised substring match**, NOT exact terms. In-scope
buckets observed (doc_count):

| project entity | nation strings (variants) | ~count |
|---|---|---:|
| Danish realm | `Danmark`, ` Danmark`, `danmark`, `Danmark?`, `Danmark(?)`, `Danmark-Norge`, `Danmark; Norge`, `Danmark, Trankebar` | ~148 700 |
| Norway | `Norge`, `Norge ` | ~4 250 |
| Schleswig-Holstein | `Slesvig-Holsten`, `Slesvig og Holsten`, `Slesvig`, `Holsten`, `Holsten-Gottorp`, `Holstein-Gottorp`, `Slesvig-Holsten-Gottorp`, `Danmark, Slesvig-Holsten` | ~1 750 |
| Hamburg | `Tysk, Hamburg`, `Hamburg` | ~39 900 |
| Lübeck | `Tysk, Lübeck`, `Lübeck` | ~12 240 |
| Brunswick-Lüneburg | `Tysk, Lüneburg`, `Lüneburg`, `Tysk, Brunswick-Lüneburg` | ~14 000 |
| Bremen / Verden | `Bremen`, `Ærkebispedømmet Bremen` | ~160 |
| Oldenburg | `Tysk, Oldenburg` | ~56 |
| (Lauenburg, Schauenburg, Hessen, Osnabrück) | check buckets at harvest | small |

**OUT of scope** (do NOT harvest): `Tyskland` / `Tysk` generic (16 600 +
10 800), `Tysk, Mecklenburg/Salzwedel/Wismar/Rostock/Stralsund` (Pomerania
/ Brandenburg), and all world/ancient (`Kina`, `Rom`, `græsk`, `England`,
`Indien`, `Kalifatet`, `Sverige`, `Frankrig`, …).

Implementation: pull the full `nation.keyword` terms aggregation (size 300)
ONCE, run each bucket through a normaliser (`strip → casefold → drop "tysk,"
prefix`) + an in-scope regex, and emit the **exact** matching nation strings
as a `terms` filter list. Re-aggregate periodically (WIP API → new variants
appear). Keep the curated drop/keep decision in a sidecar JSON, mirroring
`fetch_ikmk_oos_title_prefixes.json`.

**Nation-scope ≈ 221 934 records** (Hamburg + Danmark dominate) — but **62 %
are undated medieval bracteates/pennings** and most dated records are pre-1480.
That's too much (curator 2026-06-01). **Task scope = «Denmark 1480-1914
(wide)», gated at HARVEST** (not just SEED):

> KEEP iff **(a)** DATED with `creationEvents.yearFrom` ∈ [1480, 1914], **OR**
> **(b)** UNDATED but attributed to an **in-scope ruler** (`authority` present,
> NOT a medieval pre-Hans Danish monarch — `_MEDIEVAL_AUTHORITY` exclude-list).

Branch (b) is essential: ~7.3k undated records carry a ruler + a Hede number
(`H. 71` Frederik III; Christian IV/V skillings) — the project's core coins,
just lacking a precise `creationEvents` date. A pure year gate would lose them.
The medieval EXCLUDE-list (closed, distinctive Danish pre-1481 royal names:
Erik / Svend / Valdemar / Knud / Niels / Abel / Christoffer / Margrete / Oluf /
Harald / Gorm / …) is safer than an in-scope INCLUDE-list and never collides
with in-scope German/SH ruler names (Friedrich, Johan Adolf, …).

Net (live-verified): **221 934 → ~43 033** (≈35.3k dated-in-range + ~7.3k
undated-in-scope-ruler). Drops: 88k anonymous medieval + ~38k medieval-
attributed + dated-out-of-range. The year field is a STRING; a `[1-9][0-9]{3}`
regexp guard on the dated branch removes the tiny 3-digit («181») lexicographic-
range leak. Per-track era refinement (DK 1514 / German 1559) stays a SEED/
Phase-4 concern. NB volume: ~43k whole-JSON records ≈ 40–45 MB in the submodule.

The gate is server-side in the ES query (`fetch_kmk.py::_harvest_query`), so
OOS records are never even downloaded.

## Pipeline plan (4-phase, per `docs/ARCHITECTURE.md`)

1. **HARVEST — `scripts/fetch_kmk.py`** → `scripts/cache/kmk/<id>.json`
   (one whole `_source` per file, like IKMK) + `_manifest.json` (kept nations,
   `in_scope_total`, last `search_after` cursor, counts, timestamp for resume).
   Server-side nation scope + the 1480-1914 task gate (above); whole record, no
   field pruning / exonumia drop.
2. **SYNTHESIS — none.** `_source` is already typed JSON (mirror IKMK: the
   builder reads cache directly; no `parse_kmk.py`).
3. **SEED — `scripts/maintenance/build_kmk_seed.py`** → `data/v2/seed/kmk/
   <entity>.yml`. Field mapping below; era-gate + exonumia exclusion +
   entity routing here; `write_v2_seed` (merge-aware, idempotent).
4. **MERGE/ABSORB** — existing `merge_seeds_cross_source.py` + Phase-4
   classifier dedup KMM against Hede/Bruun/Numista/IKMK. No new code.

### Field mapping (KMM `_source` → Coin schema)

| Coin field | source | notes |
|---|---|---|
| `id` | `f"kmk-{id}"` | |
| `nominal` | `nominal` | scalar |
| `metal` (+`_verified`) | `materials[].material` via dirty-string normaliser (see field anatomy) | verified=present |
| `ruler` | `authority` | trim trailing `(years)…` |
| `mint` (+`_verified`) | `place` split `City[, mintmaster]` → city | verified=present |
| `mintmaster` | `place` tail after comma (if name-shaped) | careful: `"Lund, Bosi"` → mint `Lund`, mm `Bosi` |
| `year_first/last`, `year_label`, `year_ranges` | `creationEvents[].yearFrom/yearTo` | **int-coerce strings**; undated→None |
| `weight_rough_g` (+`_verified`) | `measurements[]` where `dimension=="Vægt"` (always Gram) | only measurement KMM has |
| ~~`diameter_mm`~~ | — | **KMM records no diameter; never populated** |
| `catalog` | `typeNumber` → `{hede/dav/sieg/schou/hauberg/…}` | parse author prefix; `Hbg`→hauberg |
| `issuing_entity` (+`entity_classified_via`) | `classify_mint_to_entity(place, year)`; **fallback `classify_nation_to_entity(nation, year)`** when place absent | None→`_unclassified.yml`; record provenance (see note) |
| `kind` | default `kurant` (seed_unsorted; Phase-4 refines) | |
| `fuss`/`phase` | `seed_unsorted` / `kmk` | |
| `inscription_obv/rev` | — | KMM has none (~0 %) |
| `sources[]` | `{type:"museum", url:f"https://samlinger.natmus.dk/KMM/object/{id}", ref:f"KMM {id} (Inv. {objectIdentification})"}` | url verified live |
| `images` (optional tier) | `related.assets[]` → `https://samlinger.natmus.dk/kmm/asset/<n>.jpg?maxsize=org&download=true` | CC BY-SA; `<n>`=asset id numeric |
| `verification_note` | KMM-seed boilerplate (de/en/uk) | |

### §9 exclusions at seed
- `workDescription == "Regnepenning"` → reckoning jeton = exonumia §9.2 → skip.
- `workDescription == "Medalje"` / division Medals → skip.
- Patterns / off-strikes: KMM rarely flags these; rely on cross-source
  merger + curator.

### Entity routing — nation fallback + provenance marker (NEW helper needed)
`place`/mint is only ~27 % populated, so for the 73 % without a mint, route
by `nation`. Add a `classify_nation_to_entity(nation, year)` companion to
the existing mint-based classifier (normalise nation, map the table above:
`*Hamburg*`→hamburg, `*Lübeck*`→lubeck, `*Lüneburg*`→brunswick_lueneburg,
`*Slesvig*/*Holsten*/*Gottorp*`→royal_holstein|gottorp_duchy (year-aware),
`Danmark`/`Norge`/`Danmark-Norge`→danish_realm|danish_norway,
`*Bremen*`→bremen_verden, `*Oldenburg*`→oldenburg). Mint-based result wins
when present; nation is the fallback.

**Record HOW the entity was derived — `entity_classified_via` (recommended,
not a blocker).** Entity is ALWAYS an inferred field (no source says
«belongs to gottorp_duchy»), but the *reliability* of the inference differs:
mint-based (`place` = a specific city like Altona/Glückstadt) is precise;
nation-based fallback is coarse (nation «Slesvig-Holsten» could be royal OR
Gottorp depending on era/mint — a real misroute risk). So a value filled by
fallback deserves a flag, exactly the spirit of the user's request.

Design analysis (decision deferred to build time):
- **Recommended shape: an enum `entity_classified_via: "mint" | "nation" |
  "ruler" | "manual" | None`**, set by the builder to whichever classifier
  fired. More informative than a bare boolean `entity_fallback: true` — it
  names the method, is queryable («show all nation-classified entries for
  curator review»), and extends cleanly if a ruler-based classifier is added
  later. Never shown to the end-reader (role-3 scaffolding per §0z).
- **A GENERIC per-field `field_falled_back` boolean is NOT recommended** —
  it's YAGNI. The existing `*_verified: false` flag already distinguishes
  source-attested from inferred for the measurement fields (metal, weight),
  and `issuing_entity` is the ONE field on the KMM path that is fallback-
  derived in a way `*_verified` doesn't already capture. Adding a blanket
  mechanism now buys nothing; add the single `entity_classified_via` field
  and revisit if a second fallback-filled field ever appears.
- Cost: one optional schema field + builder sets it + (optionally) the
  cross-source merger surfaces nation-vs-mint entity disagreements in
  `match_uncertainty/`. Does not block harvest — it's a Phase-3 concern.

## Resolved (live-verified 2026-06-01)
1. **Object-page URL**: `https://samlinger.natmus.dk/KMM/object/<id>` where
   `<id>` is the numeric `id` field (e.g. 294). Navigated successfully.
2. **Image URL**: `https://samlinger.natmus.dk/kmm/asset/<n>.jpg?maxsize=org&download=true`
   (full JPEG) / `.org` (original .tif) / `.jpg?maxsize=300` (thumb); `<n>` =
   numeric part of `related.assets[].id`. License CC-BY-SA + named
   photographer on the page.
3. **Measurements**: weight-only — sole dimension `Vægt`, unit `Gram` (25 105
   records collection-wide). **No diameter exists in KMM.** `materials[]` is
   `[{material:"<dirty string>"}]` (normaliser spec in field anatomy).
4. **Year**: `creationEvents[].yearFrom/yearTo` are STRINGS (lexicographic
   range leaks short Roman years) → int-coerce at parse; no numeric date
   field exists.

## Open at implementation (minor)
- Re-pull `nation.keyword` aggregation (size 300) for in-scope variants below
  the sampling cutoff (Lauenburg/Schauenburg/Hessen/Osnabrück/Verden) and
  freeze the keep/drop nation list in a sidecar JSON.
