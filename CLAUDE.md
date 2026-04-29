# Numismatic Münzfüße Project — Claude Code Context

> **Read this file first on every session.** It contains non-negotiable principles and conventions developed over many research sessions. Supporting files: `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/CONVENTIONS.md`, `docs/GLOSSARY.md`.

## Mission

Build mathematically-verified, historically accurate reference artifacts documenting coinage standards (*Münzfüße*) of North German cities and territories, ca. 1566–1914. Output: static HTML pages hosted on GitHub Pages, one per location, in three languages (DE/EN/UK), with a landing page linking them.

**Primary researcher:** Serhii (Ukrainian, expert-level numismatist). Communication in Ukrainian (ти-form). Expects direct, precise answers — no hedging, no self-abasement. Catches analytical errors; challenges conceptual weaknesses; trust is earned through accuracy.

## Non-negotiable research principles

### 0. No invention. State only what the sources document.

> **This is a scholarly historical-numismatic study, not creative writing.** Every factual claim that lands in the rendered artefact (phase descriptions, coin notes, fuss summaries, location preambles, references) must be traceable to a named source — coin inscription, museum catalogue, auction catalogue, MGM, Numista entry, Hede / Wilcke / Schou / Lange / Sieg, danskmoent.dk page, Wikipedia article with citation, or the user's directly-stated knowledge.

**Forbidden moves:**
- Asserting **mintage figures, rarity, "sole issue", "only known specimen"** without an explicit source. Existence of a coin in a catalogue does not establish singularity. Hede c5h120 documenting a 1683 Speciedaler at 9-Fuß confirms the type and the standard — it does NOT confirm that the issue was unique, special, or one-off.
- Asserting **rulers' motivations, decrees, intent** ("Christian V ordered…", "the duchy decided…", "in response to the crisis…") unless that motivation is recorded in a primary or recognised secondary source. Otherwise: state the dated fact, not the reason.
- Adding **temporal embellishments** ("long after the standard had been superseded", "shortly before the reform", "in the twilight of the system") that go beyond bare chronology. State the year, leave interpretation to the reader.
- Inventing **historiographical labels** ("Sonderprägung", "transitional issue", "experimental coinage", "ґлюкштатське відновлення") that do not appear in literature. If a term is novel, it is the user's call to coin it — never Claude's.
- Filling **descriptive prose** to make a section "feel complete". A two-sentence factual phase description is preferable to a paragraph of plausible-sounding narrative. Empty space is honest; padding is not.
- Reasoning by analogy from one location/period to another and presenting the conclusion as established fact. Analogy is at most a hypothesis — and a hypothesis without a source has no place in the artefact.

**Required moves:**
- When you write a sentence, ask: *which source says this*? If you cannot name one, the sentence is fabrication. Either find a source or remove the sentence.
- For interpretive observations that genuinely belong (e.g. "this Δ exceeds the Schleswig 9¼-Fuß remedium"), attribute them to the build's own computation: «errechnet aus … » / «as computed from …». Don't dress computation as historical narrative.
- When a source confirms only part of a claim, write only that part. Hede c5h120 confirms a 9-Fuß Speciedaler from 1683 — write "Speciedaler 1683 (Glückstadt) nach 9-Fuß, Hede 120". Do not extend.
- When in doubt, say so explicitly in the prose: «Auflage und Anlaß sind in den vorliegenden Quellen nicht angegeben» / «mintage and circumstance are not given in the available sources». An explicit gap is more useful than a confident fiction.

This rule **subsumes and reinforces** §4 (unconfirmed-data marker), §5 (source hierarchy), §2a (academic register), and the "Inventing sources" anti-pattern. When those rules and this one say similar things, this one is the canonical statement; the others are specific applications.

**The scholarly tone is not optional decoration.** A hedged guess presented in confident prose is worse than no entry at all — it pollutes the reference and silently corrupts every researcher who later cites it.

### 1. What's on the coin vs. what's calculated

> **Only what is literally inscribed on the coin goes in the `nominal` field. Calculated equivalents, historiographical nicknames, and secondary rechnerische Äquivalenten go in `note` (Bemerkung).**

Examples:
- Coin inscription `*VIII* SKILLING DANSKE` → `nominal: "8 Skilling Danske"`. NOT `"8 Skilling Dansk (= 4 Skilling Lybsk = 1/12 Speciedaler)"`. The equivalents go in `note`.
- Coin inscription `MONNO GLVCKSTAD · XVI · E·REIC· HS·DA` → `nominal: "1/16 Reichsthaler Holstein-Dänisch"` (matching the legend). NOT `"1/16 Speciedaler"` (modern classification).
- `Rigsort` is a historiographical nickname — does NOT appear on the coin — goes in `note`.
- Pre-1841 Rigsbankskilling: legend is `*16* REICHS=BANK SCHILLING`, single-inscribed. Post-1841 (after Forordning 18. Dez. 1841): dual-inscribed. Do not conflate.

### 2. Period-correct German orthography (mandatory in `de` fields)

| Use | NOT |
|---|---|
| Müntz, Müntzfuß, Müntzwesen | Münz, Münzfuß |
| biß | bis |
| Marck | Mark (except Kurantmark/Reichsmark contexts) |
| Cöllnische Marck | Kölnische Mark |
| Thaler | Taler |
| Courant | Kurant |
| Groß, groß | Gross (never ß→ss) |
| Müntzvertrag, Müntzordnung | Münzvertrag |

Danish forms preserved intact: Kurantmøntfod, Plakat, Forordning, Danske Kancelli, Rigsdaler, Rigsort.

English/Ukrainian fields use modern orthography (Münzfuß, Mark etc.) — period orthography is a DE-only convention reflecting historical sources.

### 2a. Academic register (mandatory in all three languages)

This is a **scholarly historical-numismatic study**, not a popular-history blog. All running text — descriptions, phase backgrounds, coin notes, methodological remarks — uses an **academic register**: precise, restrained, source-driven. Avoid:

- **Colloquialisms** (uk: «наварок», «крутий», «класний»; de: «echt mega», «krass»; en: "huge gain", "crazy")
- **Sensationalist intensifiers** ("екстремальний", "величезний", "extreme", "massive", "unbelievable") — quantify instead ("≈ +154 % über Silberwert", "23,48 vs. 10,43")
- **Editorial exclamations** ("nicht Kopenhagen!", "achtung!", "WOW") — state the fact plainly
- **Ad-hoc abbreviations and informal punctuation** in section titles (`+`, `&`, `/`); use full conjunctions ("und"/"and"/"та")
- **First-person voice** ("we think", "our analysis suggests") — use impersonal constructions or attribute to a source
- **Vague hedging** ("probably", "kind of", "досить") — either commit and cite, or mark `verified: false` with a verification note

Preferred terms (uk → register-correct German/English equivalents in parentheses):
- «надбавка» / «премія» / «маржа» (de: «Aufschlag», en: "premium")  — NOT «наварок»
- «значне відхилення» / «суттєве перевищення» (de: «erhebliche Abweichung», en: "substantial deviation") — NOT «екстремальне»
- «спричинило» / «зумовило» / «послужило приводом для» (de: «löste aus», en: "prompted") — NOT «спровокувало» (acceptable but slightly populist)

**Forbidden non-words (in any language):**
- **«stope»** — does not exist in English, German, or Ukrainian. Use the actual term: «standard», «Müntzfuß», «стопа» (uk), or the language-appropriate noun. Never coin pseudo-Anglo hybrids from Slavic roots.
- «емпіричні дані свідчать» / «джерела підтверджують» (de: «empirisch belegt», en: "the evidence shows") — NOT «факти кажуть»

When in doubt, ask: *would this phrase appear in a peer-reviewed numismatic article*? If no, rephrase.

### 3. Precision conventions

- **Decimal separator**: comma in DE (`25,28173 g`), period in EN (`25.28173 g`), comma in UK (`25,28173 г`). The build script handles this via i18n formatter; YAML stores numbers as JSON numbers (`25.28173`).
- **5-decimal precision** for all Feingewicht calculations that appear in text. Internal computation uses full float precision.
- **`=` vs `≈` vs `Kurs`**: strict distinction. `=` for exact mathematical identity; `≈` for approximations ≤0.1%; `Kurs` for historically-set exchange rates that need not reflect metal content.

### 4. Unconfirmed data marker `(?)`

When a value is estimated, unverified, or based on analogy rather than a primary source, mark the field as unverified. In YAML: `verified: false` with a `verification_note`. The build script renders this as `(?)` with a tooltip.

**Never fake certainty.** Better to have 10 rows with `(?)` markers than 10 rows of plausible-looking fabrication.

**Strict rule for flipping `*_verified` to `true`**: the flip is only allowed when an **identifiable source confirms the value**. Acceptable sources are listed in §5 (coin inscription, museum catalogue, auction catalogue, MGM, Numista with explicit data, Wikipedia with citation, Hede / Wilcke / Schou / Bobzin etc.). Heuristic reasoning — «the Δ falls within typical specimen tolerance», «the value matches the standard», «this looks plausible» — is **not** a valid confirmation. If no source is at hand, leave `verified: false`. The `(?)` marker is honest; a wrong `true` is a silent corruption.

The same applies to *modifying* a value: do not edit a field marked `verified: true` unless a source contradicts it. Do not edit a `verified: false` field to a different value unless a source supports the new value.

### 5. Source hierarchy

In descending order of authority:

1. **Coin inscription itself** (from IKMK, museum catalog, or high-resolution photo)
2. **Museum catalogs** (IKMK Berlin, Royal Coin Cabinet Copenhagen, British Museum)
3. **Auction catalog introductions** (Bruun Part II by Stack's Bowers Zürich 2025 is exceptionally well-researched)
4. **MGM Münzlexikon** (Münzen, Geschichte, Menschen)
5. **Numista** — useful for catalog numbers and rough data, but user-edited, treat with some skepticism
6. **Wikipedia** (DE/EN) — last resort, always cross-check
7. **Secondary literature** (rounded figures, modern retellings) — lowest priority

When sources conflict, primary sources (inscriptions, archives) override secondary/tertiary sources. Always document the source chain in `coin.source`.

### 6. Kurantmünze vs. Scheidemünze distinction

- **Kurantmünze** (vollwertig): nominal ≈ silver content. Issued by state without (or with minor) seigniorage. Full-value money.
- **Scheidemünze** (Billon/copper): nominal > silver content. Difference = seigniorage (state profit). Circulates locally only.
- **Tarifmünze** (special case — Kronemønt 1618–1696): set by fiat to a tariff above silver value; distinct category.

In `coin.kind`: one of `kurant | scheide | tarif | gedenk`. Build script renders these into separate sub-tables within each phase (green divider for Kurant, amber for Scheide). This distinction is **mandatory**: conflating them obscures the economic logic.

### 7. Münzfüße are global; phases are local

- **Fuesse** (`data/shared/fuesse.yml`) are universal mathematical constructs: Cöllnische Marck ÷ N. The 9¼-Fuß is the same everywhere. Defined once.
- **Phases** are location-specific: how *this location* applied *this fuss* during *this period*. Bremen's 9¼-Fuß phases differ from Schleswig's.
- Coins reference both: `fuss: reichsdukatenfuss` (global), `phase: A` (local to the location file).

### 8. Coin placement rules (audit checklist)

Every coin must be in:
1. **The correct fuss** by its actual Münzfuß (not where it might seem to fit rhetorically). E.g., dual-denom Rigsbankskilling belong in 18½-Fuß (their Primär-Fuß), not in 9¼-Fuß even though 5 Schilling Courant = 1/12 Speciestaler.
2. **The correct chronological phase** within that fuss. First year of issue determines phase.
3. **The correct Kurant/Scheide category** within that phase.

Never shortcut this. Mis-placement has happened repeatedly and always produces confused conclusions.

### 9. Coin inclusion criteria (source-agnostic)

When deciding whether a coin entry belongs in a location's coin table — regardless of where it was sourced (Numista, Bruun, IKMK Berlin, Lange, MGM, hand-typed from a museum visit) — apply these three exclusions, and only these:

1. **Patterns / trial strikes** — entries marked `Pn*`, `(Silver pattern strike)`, `(Gold pattern)`, "Probe", "Essai" etc. They were not struck for circulation. Skip.
2. **Exonumia** — medals, jetons, commemorative tokens, Tin/White-metal pieces without a denomination. They belong to separate registers, not to coin tables.
3. **Duplicates** — defined strictly by **catalog index**, primarily KM# (Krause-Mishler). Two entries sharing the same KM# (or the same Hede#, Sieg#, Lange# when KM# is absent) are duplicates. **Different catalog index = different type**, even if the denomination, ruler, mint, and year ranges overlap. Krause-Mishler assigns a separate KM# to each design / mint / mintmaster / fineness variant by design.

**Do NOT skip:**
- Multiple coins of the same denomination per ruler if their catalog indices differ (each KM# = a distinct documented type with its own row).
- Coins outside the currently-added time window if they fall within the location's overall historical scope. Extend the relevant phase to cover them rather than dropping the coin.
- Coins where the source lacks fineness or weight — add them with `verified: false` and let `(?)` markers render. Under-documentation is preferable to omission.

This rule was introduced after a manual import accidentally collapsed multiple KM# variants into single representatives ("one 1 Thaler John Adolphus per period"), losing typological coverage. A complete catalog ingest from any source should match that source 1:1 except for the three exclusions above.

## Architecture overview

```
data/shared/fuesse.yml                  # Mathematical definitions of Münzfüße (global)
data/locations/<loc>.yml                # Per-location: phases + coins (inline i18n)
data/locations/<loc>-references.yml     # Bibliography sidecar (refs cited inline as [N])
data/i18n/ui.yml                        # UI strings (column headers, badges, buttons)
data/i18n/issuing_entities.yml          # Issuing-entity (kingdom / duchy) metadata

config/theme.yml                        # Colors, typography, dimensions

templates/landing.html.j2               # Homepage — location cards
templates/location.html.j2              # Per-location/per-language page

scripts/build.py                        # Single entry point: data → site/
scripts/lib/
  schema.py                             # Pydantic models for validation
  compute.py                            # A → B: fein, delta, implied fuss
  categorize.py                         # B → C: group by phase, kind
  render.py                             # C → HTML via Jinja2 + theme-driven CSS
  i18n.py                               # Translation resolution, number formatting

site/                                   # .gitignored — build output
  index.html                            # Landing page (language-switchable)
  <lang>/index.html                     # e.g., de/index.html (locations index)
  <loc>/<lang>/index.html               # e.g., schleswig/de/index.html
  assets/{style.css, app.js}

.github/workflows/deploy.yml            # Auto-build + deploy on push to main
```

## Build pipeline (A → B → C → HTML)

- **A (source)** = raw YAML in `data/`. Hand-edited. Minimal fields: what's on the coin, weight_rough, fineness, fuss, phase, source.
- **B (computed, in-memory)** = A + derived fields: weight_fein, soll_fein, delta_g, delta_pct, implied_fuss. Computed by `compute.py`. Debug output optional → `output/debug/<loc>.computed.json`.
- **C (categorized, in-memory)** = B grouped by fuss → phase → kind (kurant/scheide). Sorted by year_first. Build script walks this tree.
- **HTML** = Jinja2 templates render C. One HTML per (location, language).

Never edit B or C manually. Never edit site/ HTML manually. Always edit `data/` and rebuild.

## Build command

```bash
python scripts/build.py                    # builds everything
python scripts/build.py --location schleswig   # single location, all languages
python scripts/build.py --location schleswig --lang de   # single page
python scripts/build.py --debug            # also writes output/debug/*.json
python scripts/build.py --validate-only    # runs schema validation, no rendering
```

## Git workflow

- **main** = source of truth. Every push triggers GitHub Actions → build → deploy to Pages.
- **Feature branches** for larger changes (new location, template rework).
- **Commit messages**: conventional prefixes — `data:` (YAML changes), `schema:` (model changes), `template:` (render changes), `build:` (script logic), `docs:`, `fix:`.
- **Commit messages MUST be in English only** (subject + body), regardless of the language used in the chat conversation. Project communication may be in Ukrainian, but git history is English-only.
- Commit small, commit often. YAML diffs are readable.

### One-off / scratch scripts

Anything that runs **once** on a specific dataset and won't be replayed (data migrations, ad-hoc cleanups, one-time imports keyed to a particular ruler / mint / catalog) lives in **`scripts/oneoff/`** — gitignored. Do not commit it.

Truly reusable utilities (build steps, periodic enrichment passes, idempotent quality checks) go directly under `scripts/`. Tests:

- *Could this run again next year on a different dataset?* → `scripts/`.
- *Is the input data hardcoded / already gone / consumed?* → `scripts/oneoff/`.

Past examples of one-off scripts (now removed): `cleanup_sources.py`, `migrate_notes.py`, `relocate_data_notes.py`, `fix_wrong_numista_urls.py`, `manual_translations.py`, `add_new_coins.py` (Gottorp Duchy import), etc. — all served their migration purpose and were dropped from the repo.

## Data editing workflow

1. Edit the relevant YAML file (e.g., add a coin to `data/locations/schleswig.yml`)
2. Run `python scripts/build.py --validate-only` locally to catch schema errors
3. Optionally `python scripts/build.py --location schleswig --lang de` to preview
4. Commit + push
5. GitHub Actions rebuilds and deploys (~1 min)

## i18n policy

Strategy A (inline): each translatable field is a `{de: ..., en: ..., uk: ...}` object in YAML. Supported fields: `title`, `description`, `note`, `verification_note`, boilerplate texts.

Non-translated fields (global identifiers):
- Catalog references (KM#, Hede, Sieg, Bruun-lot) — never translated
- `nominal` — kept as literal inscription (Danish/German/Latin); translation is in `note` if needed
- Mint names, ruler names — use standard academic spellings, identical across languages
- Münzfuß names in technical form (`9¼-Fuß`) — displayed identically across languages
- Numbers — localized by formatter, not translated per-row

UI strings (column headers, navigation, buttons) live in `data/i18n/ui.yml`.

## Anti-patterns to avoid

1. **Mental reframing of user requests.** If the user says "don't change X", don't change X even if a "better" change seems obvious.
2. **Inventing sources.** If unsure, say `verified: false` and `verification_note: "not found in online sources"`.
3. **Rounding silently.** All numbers in YAML must be traceable. If the source says 3.46 g, store 3.46 not 3.5.
4. **Fixing YAML in one place while leaving equivalent issue elsewhere.** E.g., don't rename KM# 82's nominal without checking KM# 42.1 for the same pattern.
5. **Leaving HTML hand-edits in site/.** site/ is regenerable. If the fix belongs there, it belongs in the template or data.

## Checking your work

Before committing:
```bash
python scripts/build.py --validate-only   # schema OK
python scripts/build.py                    # builds successfully
# open site/schleswig/de/index.html in browser — spot check
git diff data/                             # sanity check on changes
```

After non-trivial changes, run the structural audit script:
```bash
python scripts/audit.py schleswig
```
Reports chronology mismatches, orphan coins (phase doesn't exist), duplicate KM# entries, and Kurant/Scheide imbalances.

## When to ask the user

- Ambiguous coin provenance, multiple plausible catalog entries
- Conflicting sources on fineness
- Whether a new variant deserves its own row or a note on existing row
- Translation calls for specialized numismatic terms in UK (Ukrainian numismatic vocabulary is sparse)

Never invent translations for technical German numismatic terms without confirming with the user.

## Prior work (context)

This project began as iterative research in claude.ai chat. Before this build pipeline existed, three main HTML artifacts were hand-built:

1. **Schleswig-Holstein** (180KB, 86 coins across 7 Münzfüße, 1618–1873). This is the fidelity target for the first build — `data/locations/schleswig.yml` + build pipeline should reproduce it structurally.
2. **Pan-German Münzfüße overview** (`reference/muenzfuesse_v5.html`, 57KB, 18 Münzfuß cards ca. 1566–1875). The source material for expanding `data/shared/fuesse.yml` and for future locations (Bremen, Hamburg, Lübeck, etc.).
3. **Lübeck coin catalog 1749–1810** (`reference/lubeck_1750_1850_verified_complete.html`, 18KB). Numista + IKMK Berlin data for Lübeck coins. Source material for future `data/locations/lubeck.yml`.

See `reference/README.md` for details on these legacy HTML files and how to use them.

See `docs/DECISIONS.md` for the specific analytical decisions (e.g., why KM# 73 Stapelholmer Schanze is classified as 1698-reduced, why Bremen's 1840 silver Münzfuß reconstruction uses 71/72 fineness, etc.)

See `docs/GLOSSARY.md` for German/Danish/Ukrainian numismatic term mappings.

## Tools and resources

- **Numista** (`en.numista.com`): catalog numbers, rough weights. Rate-limited via HTTP 403; use browser console Promise.all for bulk queries.
- **IKMK Berlin** (`ikmk.smb.museum`): `/object?id={id}&download=json_ext` returns full record. Bulk scraping via browser console on the origin domain bypasses CORS.
- **Bruun PDF** (Stack's Bowers Zürich 14-15 March 2025, Part II): the gold standard reference for Gottorp/Schleswig coinage. 356 pages. `danskmoent.dk` hosts the PDF.
- **CoinVarieties, MGM Münzlexikon, Bobzin, danskmoent.dk**: supplementary academic sources.
- **Offline (paper only)**: Lange 1908/12, Sieg-Møntkatalog 2018, Storgaard 2001 — cited by Bruun/Numista, rarely accessible digitally.

## Tool fallback chain — never stop on first failure

When one tool returns 403/blocked/empty, **escalate to the next tier** rather than giving up. Do not report «source X is blocked, can't verify» until you have tried the entire chain. The user has explicitly asked Claude to remember this and use the next tool when one fails.

**For fetching public web content (preferred order — cheapest first):**

1. **WebSearch** — for finding URLs and broad topical hits. Cheap, fast, no rate limits in practice. Good for «does X exist» / «what's the URL of Y».
2. **WebFetch** (Anthropic-built) — single URL → small-model summary. Good for short pages with a focused question. Often blocked by aggressive bot defences (Numista returns 403, NGC returns 403).
3. **Apify rag-web-browser** (`mcp__Apify__apify--rag-web-browser`) — Google search results + targeted page scrape. Bypasses some 403s by fetching through Apify infra. Numista *sometimes* works here, often returns 403 too. Useful for getting Markdown of a single known URL even when WebFetch fails.
4. **Chrome MCP** (`mcp__Claude_in_Chrome__*`) — real Chrome browser via the user's extension. Bypasses **all** bot defences because it's an actual logged-in browser session on the user's machine. Heaviest tool (real browser, batched actions, screenshots) — use last, but never forget it exists.

**Numista-specific:** WebFetch and Apify both routinely return 403 on Numista catalogue pages (mi=…, ru=…, large queries especially). Chrome MCP works reliably. If a verification depends on Numista data and Apify is rate-limited, **switch to Chrome MCP immediately** — do not abandon the verification.

**Pattern for browser automation via Chrome MCP:** always batch actions with `browser_batch` (the runtime gives a system-reminder if you don't). Sequence: `list_connected_browsers` → `select_browser` → `tabs_context_mcp(createIfEmpty: true)` → then a single `browser_batch` with `[navigate, get_page_text]` per URL. For multi-page comparisons, one `browser_batch` per URL keeps the round trip count low.

**General principle:** when a tool fails, the next sentence in your response should *not* be «I cannot verify». It should be «trying tier N+1». Only report «cannot verify» after the whole chain fails.
