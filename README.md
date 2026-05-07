# Müntzfüße · Coinage Standards of North German Territories

Mathematically-verified, historically accurate reference pages documenting coinage standards (*Münzfüße*) of North German cities and territories, ca. 1566–1914.

**Live:** https://munzfuss.github.io/  
**Source research language:** German (period-correct orthography)  
**Interface languages:** DE · EN · UK

## What this is

This repo is a **static site generator** specialized for numismatic research. Every coin, phase, and Münzfuß is defined in YAML source files. A Python build pipeline transforms these into a multi-language static site deployed via GitHub Pages.

## Current state

| Location | Coins | Status | Year span | Bibliography |
|---|---|---|---|---|
| `schleswig_holstein.yml` | 253 | curated | 1567 – 1863 | `schleswig_holstein-references.yml` |
| `denmark.yml` | 468 | 46 curated + 422 seed (hidden from landing) | 1582 – 1875 | `denmark-references.yml` (5 entries) |
| `hamburg.yml` | 80 | seed (hidden from landing) | 1726 – 1873 | — |
| `lubeck.yml` | 80 | 1 curated + 79 seed (hidden from landing) | 1620 – 1797 | — |

12 Münzfüße defined globally in `data/shared/fuesse.yml` (11 real + the placeholder `seed_unsorted` used to bucket bulk-imported coins until per-coin classification work moves them into proper standards).

Locations are auto-hidden from the landing index while they still carry coins under `seed_unsorted`. Their per-language pages still build and are reachable by direct URL — the card just disappears from the landing grid until the threshold is crossed (see `docs/TODO.md` item D for the triage queue).

## Structure

```
data/
├── shared/
│   ├── fuesse.yml              Mathematical definitions of Münzfüße (global)
│   └── mints.yml               Mint metadata (nomisma.org refs where available)
├── locations/
│   ├── schleswig_holstein.yml           Curated Holstein register (253 coins, full DE/EN/UK)
│   ├── schleswig_holstein-references.yml  Bibliography sidecar (refs cited inline as [N])
│   ├── denmark.yml                      Royal Danish Copenhagen (curated + seed, with sidecar)
│   ├── denmark-references.yml
│   ├── hamburg.yml                      Hanseatic Hamburg (seed)
│   └── lubeck.yml                       Hanseatic Lübeck (seed + 1 curated)
└── i18n/
    ├── ui.yml                  UI strings (column headers, badges, etc.)
    └── issuing_entities.yml    Issuing-entity (kingdom / duchy / city-state) metadata

config/theme.yml                Colors, typography

templates/                      Jinja2 HTML templates
assets/                         Runtime static assets copied to site/assets/ (app.js)
scripts/
├── build.py                    Single entry point: data → site/
├── lib/                        Schema (Pydantic), compute, categorize, timeline,
│                               render, i18n, styles + static `style.base.css`
├── audit_*.py                  Idempotent audits (year ranges, ucoin-categorise,
│                               numista cross-check, fuss anchors, ucoin links/data)
├── fetch_numista_api.py        Cached Numista API v3 fetcher (200 calls/24h)
├── enrich_from_numista.py      Merge cached Numista responses into coin entries
├── build_ucoin_url_index.py    Rebuild the ucoin URL index from the local cache
├── bruun_parser/               4-stage Bruun-PDF → JSON ingest pipeline
├── cache/                      Cached source-tier responses (bruun, numista, ucoin)
├── maintenance/                Lifecycle-bound utilities (committed, not on build
│                               path) — translation cleanup, one-shot enrichers,
│                               source-dedup, ucoin re-link. See README inside.
└── oneoff/                     Gitignored — single-shot data migrations

.github/workflows/deploy.yml    Auto-deploy on push to main
```

See `docs/` for the full project context:

- **`CLAUDE.md`** — Project principles, research conventions, anti-patterns. Read this first on every session.
- **`docs/ARCHITECTURE.md`** — Pipeline design (A → B → C → HTML), schema, validation
- **`docs/DECISIONS.md`** — Log of analytical decisions with reasoning
- **`docs/CONVENTIONS.md`** — YAML writing rules (i18n strategy, number formatting, verification markers)
- **`docs/GLOSSARY.md`** — DE/EN/UK terminology reference

## Quickstart

Requires Python 3.12+.

```bash
# Install dependencies
pip install -r requirements.txt

# Validate data (schema + cross-refs)
python scripts/build.py --validate-only

# Build full site (all locations, all languages)
python scripts/build.py

# Build one location in one language (fast iteration)
python scripts/build.py --location schleswig_holstein --lang de

# Clean rebuild with debug dumps
python scripts/build.py --clean --debug
```

Site output lands in `site/`. Open `site/de/index.html` in a browser.

## Editing workflow

1. **Edit a YAML file** under `data/` (the only source of truth).
2. **Validate**: `python scripts/build.py --validate-only`.
3. **Preview**: `python scripts/build.py --location <loc> --lang de`.
4. **Commit and push**. GitHub Actions rebuilds and deploys (~1 min).

Do **not** edit anything in `site/` — it is regenerated on every build.

## Adding a new coin

Find the right location file (e.g., `data/locations/schleswig_holstein.yml`), add a new `coin` entry:

```yaml
- id: km-200-chr-viii-1842
  fuss: 18_5_thaler         # must exist in data/shared/fuesse.yml
  phase: B                  # must exist in this location's phases[18_5_thaler]
  kind: kurant              # kurant | scheide | tarif | gedenk
  nominal: "1 Rigsbankdaler"   # literal inscription, not calculated equivalent
  year_label: "1842"
  year_first: 1842
  ruler: "Christian VIII."
  mint: "Altona"
  catalog:
    km: "721"
    hede: "9A"
  metal: silver
  fineness: 0.875
  weight_rough_g: 14.44670
  fraction: "1"             # optional: lookup key in fuss.fractions
  note:
    de: "…"
    en: null                # TODO: translate
    uk: null
  sources:
    - type: numista
      url: "https://en.numista.com/catalogue/pieces…"
  verified: true
```

Build script auto-computes `weight_fein_g`, `soll_fein_g`, `delta_g`, `delta_pct`, `implied_fuss`.

## Adding a new location

1. Create `data/locations/<newloc>.yml`. Use **`schleswig_holstein.yml` as the template** (the richest example with full structure: `id`, `name`, `summary`, `fuss_order`, `timeline`, `fuss_periods`, `phases`, `coins`, `methodology_heading`, `methodology`).
2. Define `phases` per Müntzfuß.
3. Add coins. If the location uses a new political entity (kingdom / duchy / city-state), add it to `data/i18n/issuing_entities.yml` first (see `hanseatic_hamburg` / `hanseatic_lubeck` for examples).
4. If the new location uses a Müntzfuß not yet defined, add it to `data/shared/fuesse.yml` once. Subsequent locations can reference it.
5. Build — `python scripts/build.py` — the new location appears on the landing page automatically (provided no coins are under `fuss: seed_unsorted`).

## GitHub Pages + custom domain

1. Settings → Pages → Source: "GitHub Actions".
2. Create a `CNAME` file in repo root with your domain (e.g., `muentzfuesse.example.com`).
3. Configure DNS A/CNAME records to `185.199.108.153` / `…109.153` / `…110.153` / `…111.153`.
4. Wait for DNS propagation. HTTPS is auto-provisioned.

See: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site

## Development principles

**Non-negotiable** (see `CLAUDE.md` for full treatment):

1. **No invention.** Every claim in the rendered prose traces to a named source — coin inscription, catalogue, auction, MGM, Numista / ucoin, Hede / Wilcke / Schou / Lange / Sieg, danskmoent.dk, etc. No mintage figures, motivations, or historiographical labels without an explicit citation.
2. **Only what's on the coin goes in `nominal`.** Calculated equivalents go in `note`.
3. **Period-correct German orthography** in `de` fields: Müntz, Müntzfuß, biß, Marck, Cöllnische, Thaler, Courant, Groß.
4. **Academic register** in all three languages — no colloquialisms, no editorial intensifiers, no first-person voice.
5. **`(?)` marker** for unverified values. Set `verified: false` with explanatory `verification_note`. Flipping to `true` requires an explicit source — not a heuristic, not a "looks plausible" judgement.
6. **Source hierarchy**: coin inscription → museum → auction → MGM → Numista / ucoin → Wikipedia → secondary. Every web-sourced fact gets a bibliography entry AND an inline `<sup>[N]</sup>` cite.
7. **Kurant vs Scheide vs Tarif distinction** is mandatory — do not conflate.
8. **Münzfüße are global, phases are local.**

## Tech stack

- **Python 3.12** · core language
- **Pydantic 2.x** · schema validation
- **PyYAML** · build-time source loading; **ruamel.yaml** for round-tripping in maintenance scripts
- **Jinja2** · HTML templates
- **GitHub Actions + Pages** · CI/CD and hosting
- No JavaScript framework; minimal client-side JS (language redirect only).

## License

[GNU General Public License v3.0](LICENSE) — code, data, and generated artifacts.

## Contact

Research by Serhii · Contributions via PR.
