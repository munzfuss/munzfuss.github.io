# Bruun catalogue cache

Cached intermediate artifacts from the Bruun-catalogue parser pipeline
(`scripts/bruun_parser/`). These files are committed so future sessions don't
need to re-parse the 125 MB of Bruun PDFs (which are not committed).

## Contents

| Path | Size | Stage | What |
|---|---:|---|---|
| `pages/part{1,2,3}.txt` | ~500 KB each | 01 | Page-delimited plain text from each PDF — `========== PAGE N ==========` separators preserve page numbers for `bruun_page` citations |
| `lots/part{1,2,3}.json` | ~330–570 KB | 02 | Parsed lot blocks: `{lot_no, page, region, year, mint, ruler, refs, weight_g, grade, rarity, body_excerpt, ...}` |
| `scope.json` | 1.6 MB | 03 | All lots routed to territory bucket: denmark / schleswig_holstein / lubeck_bishopric / bremen_verden / hesse_kassel / osnabrueck / oldenburg / brunswick_lueneburg / OUT |
| `cross_match.json` | 720 KB | 04 | Same as scope.json but each lot also carries `cat` (A/B/D) and `matched_ids` (which YAML coin(s) it matches, if any) |

## Regenerating

If the cache feels stale or you've improved the parser:

```bash
.venv/bin/python scripts/bruun_parser/01_extract_text.py    # only if PDFs changed
.venv/bin/python scripts/bruun_parser/02_parse_lots.py      # if lot regex changed
.venv/bin/python scripts/bruun_parser/03_classify_scope.py  # if classifier changed
.venv/bin/python scripts/bruun_parser/04_cross_match.py     # if YAML files changed
```

See `scripts/bruun_parser/README.md` for the full pipeline.

## Why these are committed

Stack's Bowers PDFs sometimes get reorganised or moved (Part I lived at a
different URL pattern in early 2025). Having the extracted text checked in
means the project's analytical work isn't held hostage to URL stability.
The text dumps are ~1.5 MB total, the JSONs are ~4 MB — small enough to be
worth the cache hit.
