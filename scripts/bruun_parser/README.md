# Bruun catalogue parser

Reusable pipeline for ingesting Stack's Bowers' L. E. Bruun Collection auction
catalogues (3 catalogues so far, more expected). Outputs feed Phase 3 enrichment
and Phase 4 new-coin additions for `data/locations/*.yml`.

## Pipeline

```
PDFs in /tmp/bruun_pdfs/                     (not committed; ~125 MB)
  ↓ scripts/bruun_parser/01_extract_text.py
scripts/cache/bruun/pages/{partN}.txt        (~1.5 MB total — committed)
  ↓ scripts/bruun_parser/02_parse_lots.py
scripts/cache/bruun/lots/{partN}.json        (~1.4 MB total — committed)
  ↓ scripts/bruun_parser/03_classify_scope.py
scripts/cache/bruun/scope.json               (~1.6 MB — committed)
  ↓ scripts/bruun_parser/04_cross_match.py
scripts/cache/bruun/cross_match.json         (~720 KB — committed)
```

The text dumps + parsed lots are committed so future sessions don't re-parse
the 125 MB of PDF on every refresh. Re-run any stage to regenerate the
downstream artifacts.

## Adding a new Bruun part (Part IV when published)

1. Download the PDF to `/tmp/bruun_pdfs/part4.pdf`. URL pattern:
   `https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_*_Part_IV*.pdf`
   (also mirrored on `https://www.danskmoent.dk/pdf/...`)
2. Add `("part4", "Bruun Part IV (...) ")` to the `PARTS` list at the top of
   `01_extract_text.py`.
3. Add `"part4"` to the loop in `02_parse_lots.py` and `03_classify_scope.py`.
4. Run the four stages:
   ```bash
   .venv/bin/python scripts/bruun_parser/01_extract_text.py
   .venv/bin/python scripts/bruun_parser/02_parse_lots.py
   .venv/bin/python scripts/bruun_parser/03_classify_scope.py
   .venv/bin/python scripts/bruun_parser/04_cross_match.py
   ```
5. Inspect the new B-matches and D-candidates in `scripts/cache/bruun/cross_match.json`.

## Re-parsing after improvements (no new PDF)

If you change the regex / classifier, you can re-run from any stage:

- Improved lot regex → re-run from `02_parse_lots.py`
- Improved territory classifier → re-run from `03_classify_scope.py`
- New location `.yml` files added → re-run only `04_cross_match.py`

## PDF download URLs (current as of Oct 2025)

```bash
mkdir -p /tmp/bruun_pdfs && cd /tmp/bruun_pdfs
curl -sSL --user-agent "Mozilla/5.0" \
  -o part1.pdf \
  "https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Sept2024_LEBruun_Collection_Part_I_Catalog.pdf"
curl -sSL \
  -o part2.pdf \
  "https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf"
curl -sSL --user-agent "Mozilla/5.0" \
  -o part3.pdf \
  "https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Oct2025_LE_Bruun_Coins_Part_III.pdf"
```

(Bruun Part I via Stack's Bowers requires the User-Agent header; Part II is
mirrored on danskmoent.dk; Part III is on Stack's Bowers' direct URL.)

## Known parser limitations

- **Ruler detection** is name-list driven. New rulers (rare for our period
  window 1566–1914 since we already cover Christian III/IV/V/VI/VII/VIII/IX/X
  and Frederik II–IX, plus the Holstein-Gottorp and Sonderburg branches) need
  to be added to the `rulers` list in `02_parse_lots.py`.
- **PDF whitespace artifacts**: `Glück - stadt`, `Co penhagen` etc. are
  common — the mint-detection regex tolerates internal spaces but new edge
  cases may need a regex tweak.
- **Year extraction** prefers `, 1623.` patterns and falls back to the first
  4-digit year in `[1500, 1980]` — medieval lots with `ND (1018-1035)` are
  filtered later by stage 03 via the medieval-prefix check (`Hauberg`, `Hbg`,
  `Penny ND`).
- The classifier is **issuer-priority over mint-priority**: a Lübeck Bishopric
  coin minted at Bremervörde stays in `lubeck_bishopric`, not `bremen_verden`.

## Cross-references

- `docs/SOURCES.md` §1.3 — Bruun catalogue source notes
- `data/locations/schleswig_holstein-references.yml` ref38 — bibliography entry
- `CLAUDE.md` §9 — coin inclusion criteria (patterns / medals / duplicates excluded)
