# Bruun seed data — territories awaiting full Müntzfuß classification

Per-coin Bruun-catalogue records for territories that fall in the project's
historical scope but for which we have not yet researched the Müntzfuß
system. **Not picked up by the build script** (lives outside `data/locations/`),
so creating these files does not produce broken pages on the live site.

## Promotion path (seed → location)

When a territory is ready to be developed:

1. Research the Müntzfuß system(s) used during the relevant period.
   See <https://stacksbowers.com/the-l-e-bruun-collection/> for the Bruun
   PDF catalogues; this project's `docs/SOURCES.md` §6 lists encyclopedic
   sources for each territory's monetary history.
2. Add fuesse to `data/shared/fuesse.yml` if any are not yet defined
   (Niedersächsischer Kreis-Fuß, Kasseler 14-Thalerfuß, Hamburger
   Konventionsfuß, etc.).
3. Add the issuing entity to `data/i18n/issuing_entities.yml`.
4. Create `data/locations/<territory>.yml` with `name`, `summary`,
   `fuss_order`, `timeline`, `phases`, `methodology`, `coins[]`. Use the
   seed file's `coins[]` as the per-specimen anchor — fold each entry into
   a proper `Coin` schema record (assigning fuss + phase, computing
   fineness from the standard, etc.).
5. Create `data/locations/<territory>-references.yml` with the bibliography.
6. Move (don't copy) the seed file to a deletion in the same commit so
   we don't end up with two sources of truth.

## Seed format

Single dict per file. All fields optional except `id`, `coins`, `status`.

```yaml
id: <territory_id>           # short slug; matches future location id
status: seed                 # always 'seed' for files in this directory

name:                        # tri-lingual human name (optional but recommended)
  de: ...
  en: ...
  uk: ...

scope_note:                  # tri-lingual one-paragraph description of what
  de: |                      # this territory is + period of issuance
    ...                      # (optional, but useful for promotion)

coins:
  - id: bruun-<collection_id>-<short-token>
    # Bruun citation (always present from extraction)
    bruun_part: I            # I / II / III / IV / V / VI
    bruun_collection_id: 14114
    bruun_lot_no: 14200      # auction-sequence lot number
    bruun_page: 290          # PDF page where lot starts

    # From Bruun catalogue body
    year: 1606               # int or null if undated
    ruler: Adolf             # str or null
    mint: Steinbeck          # str or null (Bruun-extracted)
    nominal: Taler           # short denom token from Bruun body
    grade: NGC AU-55         # str or null
    rarity: VERY RARE        # str or null (when Bruun catalogue says so)
    weight_g: 28.96          # float or null

    # Catalogue refs
    catalog:
      km: "29"
      sieg: "9.13"
      lange: "268b"
      hede: ...
      fr: ...
      schou: ...
      dav: "5439"

    # Verbatim Bruun body text (first ~600 chars) — keep so the eventual
    # promotion to a real Coin record has the source paragraph in hand
    body_excerpt: |
      GERMANY . Schleswig-Holstein-Gottorp. Lübeck (Bishopric).
      Taler, 1606-IG. Steinbeck Mint. ...

    # Source citation (always Bruun PDF)
    sources:
      - type: auction
        url: https://stacksbowers.com/.../<part>.pdf
        ref: Bruun Part II, lot 14200, p.290
```

## Current contents (May 2026)

**All 7 seed files have been promoted to real location files** (see commit history
around 2026-05). The directory is now empty by design — left in place as a
landing zone for any future seed-imports from new Bruun parts.

Promoted (and removed from this directory):

| Now lives at | Coins | Status |
|---|---:|---|
| `data/locations/lubeck_bishopric.yml`     | 15 | promoted with seed_unsorted Müntzfuß; proper classification deferred per docs/TODO.md item E |
| `data/locations/oldenburg.yml`            | 10 | promoted with seed_unsorted; classification pending |
| `data/locations/brunswick_lueneburg.yml`  |  6 | promoted with seed_unsorted; classification pending |
| `data/locations/bremen_verden.yml`        |  6 | promoted with seed_unsorted; classification pending |
| `data/locations/hesse_kassel.yml`         |  2 | promoted with seed_unsorted; classification pending |
| `data/locations/lauenburg.yml`            |  1 | promoted with seed_unsorted; classification pending |
| `data/locations/osnabrueck.yml`           |  1 | promoted with seed_unsorted; classification pending |

Each promotion also created a sidecar `<location>-references.yml` and added a new
`issuing_entity` to `data/i18n/issuing_entities.yml`. The build script's
landing-page logic correctly hides locations with seed_unsorted coins, so the
new stub locations don't appear on the landing page until proper Müntzfuß-
classification is done (per docs/TODO.md item E).

Full upstream data still cached: `scripts/cache/bruun/cross_match.json`
(per-territory bucketed + category A/B/D classification).

Generation scripts (one-off, gitignored):
- `scripts/oneoff/seed_bruun_territories.py` — produced the original seed YAMLs
  by reading from the bruun cache (Phase 4b deferred form, May 2026)
- `scripts/oneoff/promote_seed_to_location.py` — promoted those seed YAMLs
  into real `data/locations/*.yml` files (Phase 4b proper, May 2026)
