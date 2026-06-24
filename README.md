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

The **V2 entity-keyed pipeline** is the production data pipeline (the legacy V1
render path was removed 2026-06-24). Coins are keyed by **political entity** in
`data/v2/final/<entity>.yml`; each display page declares `consumes_entities` and
the build assembles its coin table from the relevant entity files at render time.

**Curated** locations — full prose, per-coin verification, shown on the landing:

| Location | Classified coins | Years | Bibliography |
|---|---|---|---|
| `denmark` | ~1 400 | 1572–1914 | 23 entries |
| `schleswig_holstein` | ~375 | 1567–1863 | 36 entries |
| `lubeck` | ~18 | 1620–1801 | 4 entries |

The other locations — `hamburg`, `holstein_schauenburg`, `bremen_verden`,
`brunswick_lueneburg`, `oldenburg`, `hesse_kassel`, `osnabrueck`, `lauenburg`,
`lubeck_bishopric`, `german_empire` — exist but their coins are still bucketed
under `seed_unsorted` (bulk-imported from the museum / catalogue harvest,
awaiting per-coin Müntzfuß classification). They are **auto-hidden from the
landing index** until triaged; their per-language pages still build and are
reachable by direct URL. (Counts drift as the harvest re-seeds; `docs/TODO.md`
tracks the triage queue.)

**Müntzfüße** are defined globally in `data/shared/fuesse.yml`:

* Silver standards: 9-Thaler / 9¼-Thaler / 11⅓-Thaler / 18½-Thaler / 30-Thaler (Vereinsmüntzfuß) / Kronemont (Christian IV) / Kronemont (Christian V «Grobe») / Kronemont-fine (Frederik IV «Feine»)
* Gold standards: Reichsdukatenfuß / Courantdukatenfuß / Pistolenfuß / Guldkrone / Vereinsgoldmüntze / Reichsgoldmüntzfuß
* Hierarchical-metal standard: Krone-fod (gold anchor + silver Kurant + silver Scheide + bronze, per the [Scandinavian Monetary Union 1873](docs/dk_kronefod_unity_analysis.md))
* `seed_unsorted` — catch-all bucket for bulk-imported coins awaiting per-coin classification

Locations whose coins are still bucketed under `seed_unsorted` are auto-hidden from the landing index. Their per-language pages still build and are reachable by direct URL — the card just disappears from the landing grid until the threshold is crossed (`docs/TODO.md` tracks the triage queue).

## Repository layout

```
data/
├── v2/                         The production pipeline (entity-keyed)
│   ├── seed/<src>/<entity>.yml         Phase 3.1 — per-source seeds, native from cache
│   ├── seed_unified/<entity>.yml       Phase 3.2 — cross-source merge (one entry per coin)
│   ├── final/<entity>.yml              Phase 4 — fuss/phase-classified coins
│   ├── locations/<loc>.yml             Display pages: consumes_entities + phases + timeline
│   ├── merge_decisions/<entity>.yml    Curator confirmations for cross-source merges
│   └── classification_decisions/…      Curator confirmations for fuss / phase
├── shared/
│   ├── fuesse.yml              Mathematical definitions of Müntzfüße (global)
│   ├── german_fuesse.yml       Landing-page Müntzfüße overview cards
│   ├── mints.yml               Mint metadata (nomisma.org refs where available)
│   └── refs_pool.yml           Stable-key inline-refs pool (shared citations)
├── locations/
│   └── <loc>-references.yml    Bibliography sidecars (shared with V2; cited as <sup>[N]</sup>)
└── i18n/
    ├── ui.yml                  UI strings (column headers, badges, etc.)
    └── issuing_entities.yml    Issuing-entity (kingdom / duchy / city-state) metadata

config/theme.yml                Colors, typography
templates/                      Jinja2 HTML templates
assets/                         Runtime static assets (app.js)

scripts/
├── build.py                    Single entry point: data/v2/ → site/
├── lib/                        Schema (Pydantic), V2 assembly/resolver, compute, timeline, …
├── audit_*.py                  Idempotent audits (prose, i18n, year ranges, ucoin, …)
├── fetch_*.py / parse_*.py     Per-source harvest + parse (Hede, IKMK, KMK, Numista, …)
├── maintenance/                Lifecycle utilities: native seed builders (build_<src>_seed.py),
│                               cross-source merger, absorb-into-final, audits (committed)
├── bruun_parser/               4-stage Bruun-PDF → JSON ingest
├── cache/                      ← Git submodule (munzfuss-harvest, private)
└── oneoff/                     Gitignored — single-shot data migrations / scratch

.github/workflows/deploy.yml    Auto-deploy on push to main (V2 build)
docs/                           Project context, V2 pipeline plan + decisions, glossary
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

The curator does **not** hand-type coin rows. Coin data flows through the
4-phase pipeline (HARVEST → SYNTHESIS → SEED → CURATED), driven by scripts;
curator input is restricted to three decision surfaces:

1. **Which entities the project supports** — `data/i18n/issuing_entities.yml`.
2. **Cross-source merge confirmations** — `data/v2/merge_decisions/<entity>.yml`.
3. **Fuß / phase confirmations** — `data/v2/classification_decisions/`.

Editorial prose (location summaries, per-fuss backgrounds, the Müntzfuß cards)
is hand-written in `data/v2/locations/<loc>.yml` and `data/shared/fuesse.yml`.
After any change:

1. **Validate**: `python scripts/build.py --validate-only`.
2. **Preview**: `python scripts/build.py --location <loc> --lang de`.
3. **Commit + push**. GitHub Actions rebuilds and deploys (~1 min).

Do **not** edit anything under `site/` — it's regenerated on every build.

## Adding coins or a location

Coins enter via the pipeline, not by hand:

1. **Harvest + parse** the source (`scripts/fetch_<src>.py` → `scripts/parse_<src>.py`),
   then build its entity-keyed seed (`scripts/maintenance/build_<src>_seed.py` →
   `data/v2/seed/<src>/<entity>.yml`, written natively from the parser cache).
2. **Merge** across sources (`merge_seeds_cross_source.py` → `data/v2/seed_unified/`)
   and **absorb** into the curated layer (`absorb_seeds_into_final_v2.py` →
   `data/v2/final/<entity>.yml`). Disagreements surface as decisions for the
   curator to confirm in `data/v2/{merge_decisions,classification_decisions}/` —
   the preferred fix is always a script rule, so the case becomes auto-handled.

To add a **display location**, create `data/v2/locations/<loc>.yml` declaring the
political entities it `consumes_entities` (with optional year windows), its
`phases` per Müntzfuß, and its prose. A new political entity goes in
`data/i18n/issuing_entities.yml`; a new Müntzfuß goes once in
`data/shared/fuesse.yml`. The page appears on the landing automatically once it
has classified (non-`seed_unsorted`) coins.

Full step-by-step procedures live in `docs/PLAYBOOKS.md`; the pipeline design in
`docs/V2_PIPELINE.md`.

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
| `docs/ARCHITECTURE.md` | Pipeline design, schema, build-script anatomy, the 4-phase data pipeline |
| `docs/V2_PIPELINE.md` | The entity-keyed pipeline — 4-phase plan, phase scripts, promotion gate |
| `docs/V2_DECISIONS.md` | Canonical journal of every V2 architectural decision + code locations |
| `docs/PLAYBOOKS.md` | Step-by-step procedures for recurrent tasks (harvest, merge, classify) |
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
