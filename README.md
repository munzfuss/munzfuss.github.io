# Müntzfüße · Coinage Standards of North German Territories

Mathematically-verified, historically accurate reference pages documenting coinage standards (*Münzfüße*) of North German cities and territories, ca. 1566–1914.

**Live:** https://your-domain.example (set up via GitHub Pages)  
**Source research language:** German (period-correct orthography)  
**Interface languages:** DE · EN · UK

## What this is

This repo is a **static site generator** specialized for numismatic research. Every coin, phase, and Münzfuß is defined in YAML source files. A Python build pipeline transforms these into a multi-language static site deployed via GitHub Pages.

## Structure

```
data/
├── shared/
│   └── stopes.yml              Mathematical definitions of Münzfüße (global)
├── locations/
│   └── schleswig.yml           Per-location: phases + coins + inline DE/EN/UK
└── i18n/
    └── ui.yml                  UI strings (column headers, etc.)

config/theme.yml                Colors, typography

templates/                      Jinja2 HTML templates
scripts/
├── build.py                    Single entry point: data → site/
└── lib/                        Schema (Pydantic), compute, categorize, render

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
python scripts/build.py --location schleswig --lang de

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

Find the right location file (e.g., `data/locations/schleswig.yml`), add a new `coin` entry:

```yaml
- id: km-200-chr-viii-1842
  stope: 18_5_thaler        # must exist in data/shared/stopes.yml
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
  fraction: "1"             # optional: lookup key in stope.fractions
  note:
    de: "…"
    en: null                # TODO: translate
    uk: null
  sources:
    - type: numista
      url: "https://en.numista.com/catalogue/pieces…"
  verified: true
```

Build script auto-computes `weight_fein_g`, `soll_fein_g`, `delta_g`, `delta_pct`, `implied_stope`.

## Adding a new location

1. Create `data/locations/<newloc>.yml` (copy Schleswig as template).
2. Define `phases` (per-stope, per-location).
3. Add coins.
4. Build — `python scripts/build.py` — the new location appears on the landing page automatically.

If the new location uses a stope not yet defined, add it to `data/shared/stopes.yml` once. Subsequent locations can reference it.

## GitHub Pages + custom domain

1. Settings → Pages → Source: "GitHub Actions".
2. Create a `CNAME` file in repo root with your domain (e.g., `muentzfuesse.example.com`).
3. Configure DNS A/CNAME records to `185.199.108.153` / `…109.153` / `…110.153` / `…111.153`.
4. Wait for DNS propagation. HTTPS is auto-provisioned.

See: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site

## Development principles

**Non-negotiable** (see `CLAUDE.md` for full treatment):

1. **Only what's on the coin goes in `nominal`.** Calculated equivalents go in `note`.
2. **Period-correct German orthography** in `de` fields: Müntz, biß, Marck, Cöllnische, Thaler, Courant.
3. **`(?)` marker** for unverified values. Set `verified: false` with explanatory `verification_note`.
4. **Source hierarchy**: coin inscription → museum → auction → MGM → Numista → Wikipedia → secondary.
5. **Kurant vs Scheide vs Tarif distinction** is mandatory — do not conflate.
6. **Münzfüße are global, phases are local.**

## Tech stack

- **Python 3.12** · core language
- **Pydantic 2.x** · schema validation
- **PyYAML** · source data
- **Jinja2** · HTML templates
- **GitHub Actions + Pages** · CI/CD and hosting
- No JavaScript framework; minimal client-side JS (language redirect only).

## License

To be determined. Data: research-commons attribution. Code: MIT or similar.

## Contact

Research by Serhii · Contributions via PR.
