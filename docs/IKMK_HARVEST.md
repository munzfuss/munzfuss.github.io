# IKMK Berlin harvest — process notes

> **Audience: AI (future-me).** Reusable playbook for fetching
> data from the *Interaktiver Katalog des Münzkabinetts Berlin*
> (`ikmk.smb.museum`). **Not user-facing prose** — see CLAUDE.md §0z.

## Why this is OK to scrape (unlike Numista)

IKMK Berlin's content is openly licensed and the operator
explicitly invites reuse. Per-record JSON exposes:

- `text_right` → CC BY-SA 4.0 (descriptions, legends, comments).
- `lod_right` → PDM 1.0 (LOD identifiers — GND/VIAF/Wikidata
  links).
- `image_right` → varies per record. Many SH/DK records are
  **PDM 1.0** (full reuse). Some are CC BY-NC-SA. Always read
  `image_right.short` before reusing an image.
- Footer of every page: «Texts and descriptions of this catalogue
  are licensed CC BY-SA 4.0. LOD ids used are licensed Public
  Domain Mark 1.0.»

There is no «no scraping» clause in the Imprint or Datenschutz.
The implicit deal is: open licence → reuse with attribution
(`Berlin, Münzkabinett der Staatlichen Museen`).

That said, **be polite** — 1-2 requests/sec, set a descriptive
User-Agent that names the project, cache locally so you don't
re-fetch on every analysis pass.

## Anatomy of a coin record (`/object?id=<ikmk_mds_id>&download=json_ext`)

Top-level JSON keys, grouped by usefulness for our project:

### Identity & provenance
- `ikmk_mds_id` — the public 8-digit ID used in URLs (this is
  what we cache by).
- `ikmk_id` — internal numeric ID (smaller).
- `inventory_number` — the museum inventory string.
- `permalink` — canonical URL.
- `owner`, `publisher` — institution metadata with ISIL.
- `text_right`, `lod_right`, `image_right`, `image_restriction`.
- `date_last` — last edit timestamp.

### Specifications (the bread-and-butter)
- `title` — usually `<Country>: <Ruler>` or
  `<Issuer>: <Title>`.
- `nominal` — `{nominal_de, nominal_en, nominal_nomisma_id,
  nominal_gnd_id, info_de, info_en}`. Nomisma URI is
  `http://nomisma.org/id/taler` etc.
- `material` — silver/gold/billon with nomisma URI
  (`/id/ar`, `/id/au`, `/id/bil`, `/id/cu`).
- `weight` — string with unit, e.g. `28.80 g`.
- `diameter` — string, e.g. `44 mm`.
- `die_axis` — clock-position, e.g. `12 h` or `null`.
- `mint` — *list*: each entry has `country_*`, `place_*`,
  nomisma + geonames URIs. Country granularity often modern
  (Germany / Denmark), place granularity matches issuing mint
  (Glückstadt, Altona, Kopenhagen).

### Period
- `year_start` / `year_end` / `date_verbal` / `year_islam`.
- `period` — periodisation card (`Barock`, `Modern Period`, …).
- `division` / `sub_division` — `Neuzeit / 17. Jh.` etc.
- `coin_status` — list of categorical statuses
  (`Herzogtum`, `Königreich`, …) with nomisma URIs.

### Inscription / iconography (extremely useful)
- `avers` and `revers`, each with:
  - `leg_text` — the full legend transcription.
  - `leg_trans` — translation if exists (often empty).
  - `image_description` — German description of the design.
  - `path`, `path_thumbnail`, `path_org`, `path_opt`,
    `path_opt_rel` — image URLs.
  - `photographer.photographer_name` — for image credit.
  - `copyright` — per-image license HTML, with `short` like
    `PDM 1.0` / `CC BY-SA 4.0`.

### Cross-references
- `literatur` — free-text catalogue references separated by
  `;`. Real example: `H. Hede, Danmarks og Norges mønter
  1541-1814 - 1970 ²(1971) 57 Nr. 148; J. S. Davenport,
  European Crowns 1600-1700 (1974) Nr. 3673; Chr. Lange's
  Sammlung schleswig-holsteinischer Münzen und Medaillen
  I (1908) Nr. 65; …`.
- `linked_persons_corporations` — *dict* keyed by relationship
  type id (`54` = Sitter, `55` = Mintmaster, `57` = Authority,
  `50` = previous Owner, …). Each value has `items` keyed by
  person id. Each person has `last_name_de`, `first_name_de`,
  `vitalDates`, and a rich `lod` map: `gnd`, `wikipedia`,
  `viaf`, `wikidata`, IKMK NDP.
- `keywords` — list of `{keyword_de, keyword_gnd_uri,
  keyword_concept_uri}`.
- `timeline_themes` — collection's curatorial groupings (e.g.
  «Deutschland. Silbermünzen 17. und 18. Jh.»).
- `manufacturing` — strike technique with nomisma URI.

### Empty/unused (for our purposes)
- `accession`, `access_year`, `access_type`, `provenienz_extern`,
  `acquisition_date` — sparsely filled, only relevant for
  provenance-research mode.
- `eLearning_completed`, `primary_source_id`, `patronage`,
  `comment` — situational.

## Mapping to our YAML schema

| Our field | IKMK source |
|---|---|
| `inscription_obv` | `avers.leg_text` |
| `inscription_rev` | `revers.leg_text` |
| `diameter_mm` | parse `diameter` (strip ` mm`) |
| `weight_rough_g` (alt) | parse `weight` (strip ` g`); add as `{value, source: 'IKMK <inv>'}` to the list |
| `mint` | `mint[].place_name_de` |
| `ruler` | `linked_persons_corporations[57].items.<id>.last_name_de` (Authority) — or `[54]` Sitter as fallback |
| `mintmaster` | `linked_persons_corporations[55].items.<id>` (Mintmaster) |
| `catalog.hede` | parse from `literatur` field with regex `Hede[^,;]*?(\d+\w*)` |
| `catalog.dav` | `Davenport[^,;]*?(\d+\w*)` |
| `catalog.lange` | `Lange[^,;]*?(\d+\w*)` |
| `catalog.aagaard` (others) | `Aagaard[^,;]*?(\d+\w*)` |
| `sources[]` | `permalink` + `owner.owner_name` + image-attribution snippet |

## Search / enumeration protocol

The catalogue front-end uses a session-cookie POST flow. There's
no documented JSON-list endpoint, so we enumerate via the HTML
results page (`/tray`).

```python
import urllib.request, urllib.parse, http.cookiejar, re
UA = 'Mozilla/5.0 (research; muentzfuesse project; serhii)'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', UA)]
op.open('https://ikmk.smb.museum/home?lang=en').read()  # warm cookie

def search_ids(query, range_=4000):
    data = urllib.parse.urlencode({
        'quick_search_value': query, 'search_type': 'quick_search',
    }).encode()
    op.open(urllib.request.Request(
        'https://ikmk.smb.museum/quick_search?lang=en', data=data,
        headers={'Referer': 'https://ikmk.smb.museum/home?lang=en'},
    )).read()
    html = op.open(
        f'https://ikmk.smb.museum/tray?lang=en&view=list&range={range_}'
    ).read().decode('utf-8', 'replace')
    # Result anchor pattern: <a href='?lang=en&id=NNNNNNNN'>
    return list(dict.fromkeys(
        re.findall(r'\?(?:lang=[a-z]+&)?id=(\d{7,9})(?:&|"|\'|>)', html)
    ))
```

### Pagination quirk

`range` is the per-page limit — passing 4000 returns up to 4000
items in a single HTML response. The header `<N> Search results`
is sometimes a *prefix* of the actual count when the count is
4-digit (e.g. «2381» renders, regex matches the trailing «381»).
**Trust the actual length of the deduped ID list, not the header
regex match.**

For the SH+DK scope the largest single bucket («Kopenhagen») was
~2380 records, comfortably under the 4000-per-page cap. If you
ever need >4000, paginate via the form's `pageno` field (POST to
`/tray` with `pageno=N`) — not yet exercised here.

### Query repertoire that worked for SH+DK scope

Queries that returned ≥1 unique record (May 2026 snapshot):

| query | unique records |
|---|---:|
| `Schleswig-Holstein` | 172 |
| `Holstein` | 289 |
| `Schleswig` | 179 |
| `Holstein-Sonderburg` | 41 |
| `Holstein-Sonderburg-Glücksburg` | 3 |
| `Glückstadt` | 3 |
| `Altona` | 19 |
| `Reinfeld` | 36 |
| `Eutin` | 10 |
| `Sonderburg` | 42 |
| `Augustenburg` | 1 |
| `Plön` | 6 |
| `Glücksburg` | 6 |
| `Norburg` | 1 |
| `Flensburg` | 7 |
| `Kiel` | 39 |
| `Lübeck Bistum` | 32 |
| `Dänemark` | 122 |
| `Denmark` | 40 |
| `Norwegen` | 149 |
| `Norge` | 60 |
| `Kongsberg` | 1 |
| `Christiania` | 1 |
| `Kopenhagen` | ~2380 |

Queries that returned 0 (do not waste round trips):
`Holstein-Gottorp`, `Holstein-Plön`, `Holstein-Sonderburg-Plön`,
`Holstein-Sonderburg-Augustenburg`, `Holstein-Sonderburg-Beck`,
`Tönning`, `Lübeck-Bistum` (with hyphen — use space variant),
`Wiesenburg`, `Rendsburg`, `Husum`, `Slesvig`, `Norway`,
`Christiansborg`.

The query language is **substring-on-title**, not faceted. Two
spelling variants of the same thing (`Lübeck-Bistum` vs `Lübeck
Bistum`) can give very different results, so be liberal with
synonyms.

## Cache layout

```
scripts/cache/ikmk/
├── _manifest.json         # { ids: [...], queries: { q: [...] }, fetched_at }
├── 18206321.json          # one file per ikmk_mds_id
├── 18219857.json
└── …
```

**Don't re-cache** when `{nid}.json` exists — IKMK records change
slowly. Use the `date_last` field on existing files to detect
staleness if you ever need a refresh pass.

## Politeness

- 0.4-0.6 s sleep between fetches (tested fine).
- One concurrent request — no `Promise.all`/threads.
- Identifiable User-Agent string, e.g. `Mozilla/5.0 (research;
  muentzfuesse project; serhii)`.
- If the server returns 429 / 503: back off, halt, surface to
  user — AND log the event to §«Observed rate-limit log»
  below so the next routine reads the new known threshold.

### Per-run batch size — bulk is fine until proven otherwise

Empirically **no rate limit has ever been observed** across the
project's IKMK harvest history (May 2026). Unlike Numista / ucoin
(which are Chrome-MCP HTML scrapes through Cloudflare with hard
5-entry-per-batch caps per `docs/HARVEST_ROUTINE.md` §0.3), IKMK
is a museum JSON API with an openly-licensed reuse contract — the
politeness budget is generous. So:

- **Default per-run batch cap = `known_safe_batch_cap` from
  §«Observed rate-limit log» below.** Initial value (empty log)
  = **500 entries / run**, retained as the default until the log
  records an empirical throttle event.
- Maintain 0.4-0.6 s pacing across the whole batch; do not
  parallelise. Bulk = sequential-many, not concurrent-many.
- A 500-entry batch at 0.5 s pacing ≈ 4 min wall-time, well within
  one routine slot.
- When `fetch_ikmk.py fetch` consumes a manifest larger than the
  cap, slice into multiple back-to-back routine runs rather than
  one mega-call.

### Throttle-recovery protocol (when a 429 / 503 fires)

When `fetch_ikmk.py` (or any other IKMK fetcher) actually gets
throttled mid-batch, the responding routine MUST:

1. **STOP the current batch immediately.** Do NOT retry the same
   request in a tight loop — the throttle is a signal, not noise.
2. **Capture the empirical metric**: how many entries were fetched
   cleanly BEFORE the throttle response (`entries_before_throttle`),
   the HTTP code returned, the `Retry-After` header value (if any),
   and the wall-time of the run so far.
3. **Append a row to §«Observed rate-limit log» below** via Edit on
   this file (the table is the source of truth — the routine reads
   it on next start to pick `known_safe_batch_cap`).
4. **Set the next `known_safe_batch_cap`** = `min(existing_cap,
   round(entries_before_throttle * 0.8))`. The 0.8 derate gives a
   safety margin; the `min()` keeps the cap monotonically non-
   increasing across runs (a relaxation requires a deliberate human
   edit, not an automated bump).
5. **Surface in the end-of-run report**: «IKMK throttled at N entries
   on HTTP <code>; logged + capped future runs at <new_cap>».
6. **Wait** at least the `Retry-After` window before any further
   IKMK request. If no `Retry-After`, back off ≥ 600 s.

### Observed rate-limit log

<!-- ROUTINE-WRITABLE: append rows below the placeholder; never reorder;
     never delete historical rows. Initial state is the «—» placeholder. -->

| Date (UTC)         | Batch attempted | Entries before throttle | HTTP code | `Retry-After` (s) | Recovery applied                       | Source (fetcher / context)        |
|--------------------|-----------------|-------------------------|-----------|-------------------|----------------------------------------|-----------------------------------|
| —                  | —               | —                       | —         | —                 | _no limits observed as of 2026-05-27_  | initial state (no events yet)     |

**Reading the log to compute the active cap** — a routine that
needs the current `known_safe_batch_cap` does:

```python
import re, pathlib

doc = pathlib.Path('docs/IKMK_HARVEST.md').read_text()
# Capture every row under «Observed rate-limit log» that has a
# numeric «entries before throttle» value (skip the placeholder row).
rows = re.findall(
    r'^\|\s*\d{4}-\d{2}-\d{2}[^|]*\|\s*\d+[^|]*\|\s*(\d+)\s*\|',
    doc, flags=re.MULTILINE,
)
INITIAL_CAP = 500
known_safe_batch_cap = (
    min(int(r) * 0.8 for r in rows) if rows else INITIAL_CAP
)
print(int(known_safe_batch_cap))
```

If the regex returns zero rows (only the placeholder is present),
fall back to the 500-entry initial cap.

## Operational driver

`scripts/fetch_ikmk.py` is the one-stop driver:

```bash
# Discover IDs (run search queries, write _manifest.json)
python scripts/fetch_ikmk.py discover

# Fetch JSONs for everything in the manifest, skipping cached
python scripts/fetch_ikmk.py fetch

# One-shot: discover + fetch
python scripts/fetch_ikmk.py
```

Idempotent. Re-runs add new records but never delete or
overwrite.
