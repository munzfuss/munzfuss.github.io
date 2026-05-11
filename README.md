# Müntzfüße · Coinage Standards of North German Territories

Mathematically-verified, historically accurate reference pages documenting coinage standards (*Müntzfüße*) of North German cities and territories — and the wider Danish-Norwegian Reich whose courant standards governed Holstein — ca. 1559–1914.

**Live:** https://munzfuss.github.io/
**Source research language:** German (period-correct orthography)
**Interface languages:** DE · EN · UK

## What this is

A **static reference site** specialized for numismatic research. Every coin, phase, and Müntzfuß is defined in YAML; a Python build pipeline (`scripts/build.py`) transforms those sources into a multi-language site deployed via GitHub Actions to GitHub Pages.

The artefact has three concentric audiences:

* **A researcher** auditing a specific coin against its Müntzfuß-standard mass / fineness / tariff
* **A historian** tracing how one standard (e.g. 9¼-Thaler-Fuß) propagates across a composite state (Schleswig-Holstein under Danish crown)
* **A numismatist** comparing parallel standards (Reichsdukat / Pistole / Krone-Mønt / etc.) across two-and-a-half centuries

It is **not** a coin catalogue. We register only types that document the working of one of the listed standards; full corpora (every variant, every die, every specimen) live in Hede / Sieg / Lange / Krause and on the museum / auction-house websites we cite.

## Current state

| Location | Coins | Status | Years | Bibliography |
|---|---|---|---|---|
| `schleswig_holstein` | 324 | **curated** (full prose + per-coin verification + page-level audit) | 1567–1863 | 36 entries |
| `denmark` | 706 | **curated** + ~550 Hede-seed entries auto-classified into existing Fusses | 1572–1914 | 23 entries |
| `lubeck` | 80 | 1 curated + 79 seed | 1620–1801 | 4 entries |
| `hamburg` | 80 | seed | 1713–1868 | — |
| `holstein_schauenburg` | 105 | seed (IKMK ingest) | 1606–1622 | — |
| `lubeck_bishopric` | 15 | seed | 1606–1776 | — |
| `oldenburg` | 10 | seed | 1614–1667 | — |
| `bremen_verden` | 6 | seed | 1622–1674 | — |
| `brunswick_lueneburg` | 6 | seed | 1627 | — |
| `hesse_kassel` | 2 | seed | 1737–1744 | — |
| `osnabrueck` | 1 | seed | 1633 | — |
| `lauenburg` | 1 | seed | 1830 | — |

**16 Müntzfüße** defined globally in `data/shared/fuesse.yml`:

* Silver standards: 9-Thaler / 9¼-Thaler / 11⅓-Thaler / 18½-Thaler / 30-Thaler (Vereinsmüntzfuß) / Kronemont (Christian IV) / Kronemont (Christian V «Grobe») / Kronemont-fine (Frederik IV «Feine»)
* Gold standards: Reichsdukatenfuß / Courantdukatenfuß / Pistolenfuß / Guldkrone / Vereinsgoldmüntze / Reichsgoldmüntzfuß
* Hierarchical-metal standard: Krone-fod (gold anchor + silver Kurant + silver Scheide + bronze, per the [Scandinavian Monetary Union 1873](docs/dk_kronefod_unity_analysis.md))
* `seed_unsorted` — catch-all bucket for bulk-imported coins awaiting per-coin classification

Locations whose coins are still bucketed under `seed_unsorted` are auto-hidden from the landing index. Their per-language pages still build and are reachable by direct URL — the card just disappears from the landing grid until the threshold is crossed (`docs/TODO.md` tracks the triage queue).

## Repository layout

```
data/
├── shared/
│   ├── fuesse.yml              Mathematical definitions of Müntzfüße (global)
│   └── mints.yml               Mint metadata (nomisma.org refs where available)
├── locations/
│   ├── <loc>.yml               Per-location: phases, coins, prose
│   └── <loc>-references.yml    Bibliography sidecar (cited inline as <sup>[N]</sup>)
├── i18n/
│   ├── ui.yml                  UI strings (column headers, badges, etc.)
│   └── issuing_entities.yml    Issuing-entity (kingdom / duchy / city-state) metadata
└── seed/
    └── hede/<loc>.yml          Generated Hede-seed entries auto-merged at build

config/theme.yml                Colors, typography
templates/                      Jinja2 HTML templates
assets/                         Runtime static assets (app.js)

scripts/
├── build.py                    Single entry point: data → site/
├── lib/                        Schema (Pydantic), compute, categorize, timeline,
│   ├── paths.py                Centralised filesystem paths (see HARVEST_ROOT)
│   ├── env.py                  local.env loader
│   └── …
├── audit_*.py                  Idempotent audits (year ranges, ucoin, numista, …)
├── fetch_numista_api.py        Cached Numista API v3 fetcher (200 calls/24h)
├── fetch_hede.py / parse_hede.py    danskmoent.dk Hede catalogue ingest
├── fetch_ikmk.py               IKMK Berlin object harvest
├── build_ucoin_url_index.py    Rebuild the ucoin URL index from the local cache
├── bruun_parser/               4-stage Bruun-PDF → JSON ingest
├── maintenance/                Lifecycle-bound utilities (committed)
├── cache/                      ← Git submodule (munzfuss-harvest, private)
└── oneoff/                     Gitignored — single-shot data migrations

.github/workflows/deploy.yml    Auto-deploy on push to main
docs/                           Project context, decisions log, glossary
```

`scripts/cache/` is mounted as a **git submodule** pointing at a separate private repo, `munzfuss/munzfuss-harvest`. The submodule carries the regenerable artefacts of network fetches and PDF parses (Hede HTML+JSON, IKMK JSON, Numista JSON, Bruun parsed lots, ucoin URL index) — ~124 MB across ~9 200 files. The build pipeline doesn't read this cache; only fetchers, parsers, audits and maintenance scripts do. Keeping it out of the main repo keeps clones slim and prevents bulk re-parses from flooding review history.

## Quickstart

Requires Python 3.12+.

### Fresh clone

```bash
# Clone the main repo + the harvest submodule in one shot.
git clone --recursive https://github.com/munzfuss/munzfuss.github.io.git
cd munzfuss.github.io

# Install Python dependencies.
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Validate data (schema + cross-refs).
python scripts/build.py --validate-only

# Build the full site (all locations, all languages).
python scripts/build.py

# Build one location in one language (fast iteration).
python scripts/build.py --location schleswig_holstein --lang de
```

Site output lands in `site/`. Open `site/de/index.html` in a browser.

### If you cloned without `--recursive`

```bash
git submodule update --init
```

You'll be prompted for GitHub credentials (the harvest submodule is **private**). If you have SSH-agent set up, the prompt resolves transparently.

### Skipping the submodule (cache-free workflow)

The build pipeline (`scripts/build.py`) does NOT read `scripts/cache/`; it works only from `data/`, `templates/`, `config/`. So a clone without the submodule initialised is enough for:

* Validating / building / previewing the site
* Editing YAML in `data/locations/*.yml`
* Running CI deploys (GitHub Actions `actions/checkout@v4` uses `submodules: false` by default — Pages deploys never need the harvest)

The submodule is only needed for:

* Re-fetching from sources (`scripts/fetch_*.py`)
* Re-parsing cached pages (`scripts/parse_hede.py`)
* Running audits (`scripts/audit_*.py`)
* Most `scripts/maintenance/*` scripts (Hede seed builder, etc.)

### Optional: relocate the harvest cache

The cache (~124 MB across 9 200+ files) lives at `scripts/cache/` by default. To place it on an external volume instead — e.g. an SSD or NAS — set `MUNZFUSS_HARVEST_DIR` in `local.env`:

```bash
# local.env (gitignored)
MUNZFUSS_HARVEST_DIR=/Volumes/SSD/munzfuss-harvest
```

The `scripts/lib/paths.py` resolver honours the override, and every fetcher / parser / audit / maintenance script picks up the new location transparently. The default behaviour (`scripts/cache/`, the submodule mount point) is unchanged when the variable is unset.

## Editing workflow

1. **Edit** a YAML file under `data/` (the only source of truth).
2. **Validate**: `python scripts/build.py --validate-only`.
3. **Preview**: `python scripts/build.py --location <loc> --lang de`.
4. **Commit + push**. GitHub Actions rebuilds and deploys (~1 min).

Do **not** edit anything under `site/` — it's regenerated on every build.

## Adding a new coin

Find the relevant location file (e.g., `data/locations/schleswig_holstein.yml`), add a coin entry:

```yaml
- id: km-200-chr-viii-1842
  fuss: 18_5_thaler         # must exist in data/shared/fuesse.yml
  phase: B                  # must exist in this location's phases[18_5_thaler]
  kind: kurant              # kurant | scheide | tarif | gedenk
  nominal: "1 Rigsbankdaler"   # literal inscription, not calculated equivalent
  year_label: "1842"
  year_first: 1842
  ruler: "Christian VIII."
  mint: "Altona"            # string for single-mint; list [..] for parallel-strike
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

The build auto-computes `weight_fein_g`, `soll_fein_g`, `delta_g`, `delta_pct`, `implied_fuss`. For parallel-strike coins, set `mint` to a list — e.g. `["Altona", "Kopenhagen", "Kongsberg"]` for Christian VII's 1771 1 Skilling.

## Adding a new location

1. Create `data/locations/<newloc>.yml`. Use **`schleswig_holstein.yml` as the template** (richest example with full structure).
2. Define `phases` per Müntzfuß used at this location.
3. Add coins. If the location uses a new political entity (kingdom / duchy / city-state), add it to `data/i18n/issuing_entities.yml` first.
4. If the location uses a Müntzfuß not yet defined, add it to `data/shared/fuesse.yml` once. Subsequent locations can reference it.
5. Build — `python scripts/build.py` — the new location appears on the landing page automatically (provided no coins are under `fuss: seed_unsorted`).

## Harvest submodule workflow (advanced)

When a session changes cache contents — typical trigger: `python scripts/parse_hede.py --force` after a parser fix updates 100+ Hede JSON files — the workflow is **two-step**:

```bash
# 1. Commit cache changes inside the submodule.
cd scripts/cache
git add <changed files>
git commit -m "harvest(<source>): <what changed>"
git push

# 2. Bump the submodule pointer in the main repo.
cd ../..
git add scripts/cache       # records the new commit SHA
git commit -m "build: bump harvest submodule (<reason>)"
git push
```

**Always push the submodule first**, then push main. Otherwise the main-repo bump would dangle pointing at a commit not yet on the harvest remote.

Conventional-prefix messages:
* Inside `scripts/cache/`: `harvest(<source>):` (e.g. `harvest(hede):`, `harvest(numista):`).
* Inside main bumping the pointer: `build: bump harvest submodule …`.

See `CLAUDE.md` § «Harvest submodule workflow» for the full operational rules.

## GitHub Pages + custom domain

1. Settings → Pages → Source: «GitHub Actions».
2. Create a `CNAME` file in repo root with your domain.
3. Configure DNS A/CNAME records to `185.199.108.153` / `…109.153` / `…110.153` / `…111.153`.
4. Wait for DNS propagation. HTTPS is auto-provisioned.

The deploy workflow uses `actions/checkout@v4` with `submodules: false` (default). The harvest submodule is **not** fetched during CI — the build doesn't need it — so the private submodule doesn't require deploy-keys or PATs in the workflow.

## Development principles

Non-negotiable (see `CLAUDE.md` for full treatment):

1. **No invention.** Every claim in the rendered prose traces to a named source — coin inscription, catalogue, auction, MGM, Numista / ucoin, Hede / Wilcke / Schou / Lange / Sieg, danskmoent.dk, etc. No mintage figures, motivations, or historiographical labels without an explicit citation.
2. **Only what's on the coin** goes in `nominal`. Calculated equivalents go in `note`.
3. **Period-correct German orthography** in `de` fields: Müntz, Müntzfuß, biß, Marck, Cöllnische, Thaler, Courant, Groß.
4. **Academic register** in all three languages — no colloquialisms, no editorial intensifiers, no first-person voice.
5. **`(?)` marker** for unverified values. Set `verified: false` with explanatory `verification_note`. Flipping to `true` requires an explicit source — not a heuristic, not a «looks plausible» judgement.
6. **Source hierarchy**: coin inscription → museum → auction → MGM → Numista / ucoin → Wikipedia → secondary. Every web-sourced fact gets a bibliography entry AND an inline `<sup>[N]</sup>` cite.
7. **Kurant vs Scheide vs Tarif distinction** is mandatory — do not conflate.
8. **Müntzfüße are global, phases are local.**

## Tech stack

* **Python 3.12** · core language
* **Pydantic 2.x** · schema validation
* **PyYAML** · build-time source loading
* **ruamel.yaml** · round-trip preservation for maintenance scripts
* **Jinja2** · HTML templates
* **pypdf** · Bruun auction PDF ingest
* **GitHub Actions + Pages** · CI/CD and hosting
* No JavaScript framework. Minimal client-side JS (language redirect + table-of-contents anchor).

## Further reading

| Document | What's in it |
|---|---|
| `CLAUDE.md` | Project principles, research conventions, anti-patterns. Read first on every session. |
| `docs/ARCHITECTURE.md` | Pipeline design (A → B → C → HTML), schema, validation |
| `docs/DECISIONS.md` | Log of analytical decisions with reasoning |
| `docs/CONVENTIONS.md` | YAML writing rules (i18n strategy, number formatting, verification markers) |
| `docs/GLOSSARY.md` | DE/EN/UK terminology reference |
| `docs/SOURCES.md` | Per-source notes (access policy, ToS, quirks) for Numista / ucoin / Hede / IKMK / Bruun |
| `docs/IKMK_HARVEST.md` | Background on the IKMK Berlin harvest |
| `docs/hierarchical_metal_tiers.md` | Multi-metal-tier Müntzfuß convention (Krone-fod) |
| `docs/dk_kronefod_*` | Scandinavian Monetary Union research notes |

## License

[GNU General Public License v3.0](LICENSE) — code, data, and generated artifacts.

## Contact

Research by Serhii · Contributions via PR.
