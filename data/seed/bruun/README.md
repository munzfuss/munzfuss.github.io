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

| File | Coins | Notes |
|---|---:|---|
| `lubeck_bishopric.yml` | 14 | Lübeck Bishopric (Eutin) — Holstein-Gottorp ruled prince-bishopric, NOT the city of Lübeck (which has its own `data/locations/lubeck.yml`). Coverage: Johann Adolf 1606-1608 (Steinbeck/Lübeck mints), August Friedrich 1683-1687 (Eutin/Kaltenhof), Christian August 1723-1724 (Eutin). |
| `oldenburg.yml` | 10 | County / later Duchy of Oldenburg. Coverage: Anton Günther 1614-1667 (Jever Mint, mostly Talers + 1 Ducat). |
| `bremen_verden.yml` | 6 | Archbishopric of Bremen-Verden — Bremervörde + Stade mints. NOT the city-state of Bremen. Coverage: Frederik III 1641 (as Archbishop), Karl X Gustav / Karl XI 1660-1674 (under Sweden after 1648), Johann Friedrich (Holstein-Gottorp) 1622 as prince-bishop. |
| `brunswick_lueneburg.yml` | 4 | Brunswick-Wolfenbüttel — Christian IV's mainland Lower-Saxony territory. Coverage: 1627 Wolfenbüttel mint Ducat + Speciedaler + Reichstaler + Gutergroschen. |
| `hesse_kassel.yml` | 2 | Landgraviate of Hesse-Kassel. Coverage: Frederik I 1737-1744 Ducat + 1/4 Ducat (Kassel Mint; same Frederik who was simultaneously King of Sweden 1720-1751). |
| `lauenburg.yml` | 1 | Duchy of Saxe-Lauenburg under DK king (1815-1864) — own Konventionsfuß-style standard, separate from Schleswig-Holstein. Coverage: Frederik VI 1830 2/3 Taler from Altona Mint (4 051 pieces minted, Bruun catalogue). |
| `osnabrueck.yml` | 1 | Prince-Bishopric of Osnabrück. Coverage: Franz Wilhelm von Wartenberg 1633 Taler Klippe (Osnabrück Mint, Thirty Years War period). |

Full upstream data: `scripts/cache/bruun/cross_match.json` (per-territory bucketed
+ category A/B/D classification).

Generation script: `scripts/oneoff/seed_bruun_territories.py` (one-off — produced
the YAML files in this directory by reading from the bruun cache).
