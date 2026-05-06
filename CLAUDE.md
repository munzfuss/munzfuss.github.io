# Numismatic Münzfüße Project — Claude Code Context

> **Read this file first on every session.** It contains non-negotiable principles and conventions developed over many research sessions. Supporting files: `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/CONVENTIONS.md`, `docs/GLOSSARY.md`.
>
> **Also read `docs/TODO.md` at session start.** It tracks open audit items the user has flagged across sessions (continuous-year-range verification, etc.). Surface relevant TODO entries to the user when their current task touches on those topics, so we don't drift past them silently.

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
  - **Narrow exception — synthesised display identifiers with explicit user approval.** When the user explicitly asks for a name/label slot (e.g. `historical_name` for a fuss whose only period-attested form is the bare numeric formula, or a similar identifier-shaped field) and an exhaustive search of period and modern sources turns up no usable term, Claude MAY *propose* a synthesised identifier or a modern analogue — never silently apply it. The procedure is mandatory in this exact order: (a) report the search results showing the absence, (b) flag the proposal as «synthesised» / «modern analogue» and explicitly invoke this exception, (c) wait for the user's explicit «yes» / «погоджую» / equivalent in the chat, (d) only then write the term into the YAML/data. The synthesised term must also carry an annotation in the data — either an inline note or a bibliography ref pointing to the search-was-exhausted record — so the reader can see it was synthesised, not period-attested. Quietly inserting any «-Fuß»-suffixed compound, «-стопа»-form, or other identifier-shaped string without going through (a)→(d) is exactly the prohibited «invention» case and remains forbidden.
- Filling **descriptive prose** to make a section "feel complete". A two-sentence factual phase description is preferable to a paragraph of plausible-sounding narrative. Empty space is honest; padding is not.
- Reasoning by analogy from one location/period to another and presenting the conclusion as established fact. Analogy is at most a hypothesis — and a hypothesis without a source has no place in the artefact.

**Required moves:**
- When you write a sentence, ask: *which source says this*? If you cannot name one, the sentence is fabrication. Either find a source or remove the sentence.
- For interpretive observations that genuinely belong (e.g. "this Δ exceeds the Schleswig 9¼-Fuß remedium"), attribute them to the build's own computation: «errechnet aus … » / «as computed from …». Don't dress computation as historical narrative.
- When a source confirms only part of a claim, write only that part. Hede c5h120 confirms a 9-Fuß Speciedaler from 1683 — write "Speciedaler 1683 (Glückstadt) nach 9-Fuß, Hede 120". Do not extend.
- When in doubt, say so explicitly in the prose: «Auflage und Anlaß sind in den vorliegenden Quellen nicht angegeben» / «mintage and circumstance are not given in the available sources». An explicit gap is more useful than a confident fiction.

This rule **subsumes and reinforces** §4 (unconfirmed-data marker), §5 (source hierarchy), §2a (academic register), and the "Inventing sources" anti-pattern. When those rules and this one say similar things, this one is the canonical statement; the others are specific applications.

**The scholarly tone is not optional decoration.** A hedged guess presented in confident prose is worse than no entry at all — it pollutes the reference and silently corrupts every researcher who later cites it.

### 0a. Reader voice vs. analyst voice — strictly separate

> **The artefact is written for the reader, not for us.** The reader is a numismatist or historian using the page as a finished reference work. The chat where we deliberate, weigh sources, and decide is one register; the YAML/HTML output where the conclusion lives is a different register. Do not bleed one into the other.

**The reader expects to see:**
- Historical facts as a settled, sourced narrative
- Inline `<sup>` citations to bibliography entries for any non-trivial claim
- Period-correct language (per §2a)
- Concise, restrained academic prose (per §2a)

**The reader does NOT want to see (forbidden in rendered prose):**
- First-person plural about the project: «<i>ми проаналізували</i>», «<i>in unserem Artefakt</i>», «<i>this artefact treats</i>», «<i>wir behandeln</i>», «<i>we classify as</i>».
- Modelling decisions exposed: «<i>не подається окремою секцією</i>», «<i>not treated as its own section</i>», «<i>belongs in Phase B of our periodisation</i>», «<i>per our taxonomy</i>», «<i>see Phase C</i>» (cross-references inside the artefact's structure are project-meta).
- Process artifacts: «<i>аналіз показує</i>», «<i>consensus among sources is</i>», «<i>after weighing the evidence</i>», «<i>we conclude</i>».
- Hedging meta-language: «<i>arguably</i>», «<i>one could say</i>», «<i>the case can be made that</i>» — either commit and cite, or remove the sentence.
- Authorial editorialising: «<i>interestingly</i>», «<i>importantly</i>», «<i>cікаво що</i>», «<i>варто зазначити</i>», «<i>notably</i>».

**Allowed self-reference (only):**
- Computation attribution per §0: «<i>errechnet aus … </i>» / «<i>as computed from …</i>». Computation is a deductive step, not a project decision — citing the build's own arithmetic is honest.
- Source-driven hedging when sources themselves are uncertain: «<i>nach den vorliegenden Quellen</i>» / «<i>according to the available sources</i>» — but only when the uncertainty is in the historical record, not in our analysis.

**Operational test for any sentence going into prose:**
1. Could a reader who has never seen the chat understand it? If it requires knowing «we are building a project», cut it.
2. Could a peer-reviewed numismatic journal print this sentence verbatim? If it sounds like a Slack message about the article rather than the article itself, rewrite.
3. Does the sentence describe a historical fact (✓), or our internal handling of that fact (✗)?

The chat is for analysis, deliberation, source-weighing, modelling decisions. The YAML/HTML output is the **finished form** — already decided, sourced, polished. Strip the scaffolding before writing into the artefact.

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

**One source with full data is enough for `verified: true`.** Verification is not a quorum requirement — it asks "does any acceptable source attest this exact value?". A single Numista entry (or single ucoin / Hede / IKMK record) that publishes the field directly is sufficient. The flag means «present in a source», not «present in multiple sources».

**When `verified: false` is the right call for a partially-sourced coin:**
A source may publish *some* fields but not others (e.g. a ucoin entry gives weight + diameter but no fineness). For the unsourced field, you may still record the value our project would expect from the standard — but only when **both** of these hold:
1. The fineness (or other missing field) is the **canonical value of the Münzfuß** the coin clearly belongs to (e.g. .500 for an 18½-Fuß Rigsbankskilling, .875 for a 9¼-Fuß Speciedaler) — i.e. the value is *known to us from the standard*, not invented.
2. The arithmetic check using that canonical value × the sourced weight produces a Feingewicht that **falls within the standard's typical Δ envelope** (≤ ~2 % off the soll) — i.e. nothing in the sourced data contradicts the assumption.
In that case write the canonical value and mark **`<field>_verified: false`** with a `verification_note` such as «assumed canonical .500 fineness for 18½-Fuß; ucoin tid X attests weight only, fineness inferred from standard». The `(?)` marker correctly signals to the reader that *this specific field* is inferred, while preserving the coin's place in the table.

**`verified: true` is wrong** in any of these cases: (a) the value comes purely from a back-computation we performed (no source published it directly), (b) the value comes from analogy with another type, (c) the value matches the standard «too neatly» without an explicit source — neat fits are evidence the value is *plausible*, not *attested*.

**Source years are immutable — never truncate to fit our taxonomy.** A coin's `year_first` / `year_last` / `year_label` / `year_ranges` reflect what the source documents. **Do not silently shorten** the range to align with a Fuß window, a Phase boundary, or any other locally-defined annotation. If the source documents that a type was minted 1617, 1627, 1628, 1629, then `year_first: 1617`, `year_last: 1629`, `year_ranges: [[1617,1617], [1627,1629]]`, `year_label: "1617, 1627–1629"` — even if our Phase A for that Fuß ends in 1625. Phases and Füße are **our** structural annotations; years are **the source's** factual record. When the documented years overshoot a phase boundary, leave the years intact and (a) place the coin in the phase whose Münzfuß it actually represents (year_first determines phase per §8.2) — `year_last` overshooting the phase end is acceptable, or (b) note the cross-phase span explicitly in the prose. Never quietly clip.

### 5. Source hierarchy

In descending order of authority:

1. **Coin inscription itself** (from IKMK, museum catalog, or high-resolution photo)
2. **Museum catalogs** (IKMK Berlin, Royal Coin Cabinet Copenhagen, British Museum)
3. **Auction catalog introductions** (Bruun Part II by Stack's Bowers Zürich 2025 is exceptionally well-researched)
4. **MGM Münzlexikon** (Münzen, Geschichte, Menschen)
5. **Numista** — useful for catalog numbers and rough data, but user-edited, treat with some skepticism
6. **ucoin.net** — same tier as Numista; user-edited catalogue covering many overlapping types. Use as confirmation source: when ucoin's weight/fineness/diameter agrees with our value, that counts as a confirmation suitable for flipping `*_verified: true`. When ucoin disagrees, record the divergence via `measurement_alts` rather than picking one silently.
7. **Wikipedia** (DE/EN) — last resort, always cross-check
8. **Secondary literature** (rounded figures, modern retellings) — lowest priority

When sources conflict, primary sources (inscriptions, archives) override secondary/tertiary sources. Always document the source chain in `coin.source`.

**Web-sourced facts → bibliography entry + inline `<sup>` citation, IMMEDIATELY.** Whenever a fact you write into ANY rendered artefact (per-location prose, landing-page text, glossary entries, docs/* notes, anywhere user-facing) comes from a web lookup — Wikipedia, danskmoent.dk, Numista, Stack's Bowers PDF, Reichsgesetzblatt scan, MGM Münzlexikon, Bobzin, Wikisource, etc. — do BOTH steps in the same change, while the source is still open in your context:

1. **Add a bibliography entry** in the appropriate references file:
   - Per-location pages → `data/locations/<loc>-references.yml` (`ref26`, `ref27`, …)
   - Landing-page Müntzfüße overview → `data/shared/german_fuesse-references.yml`
   - Glossary / docs / cross-cutting → cite inline with the entry, link directly in the doc text
   Each entry carries DE/EN/UK content describing the source and the specific claim it backs.
2. **Inline-cite that entry** in the relevant prose with `<sup><a href="#ref{N}">[N]</a></sup>` immediately after the sentence whose factual content the source backs. The bibliography slot alone is dead weight if no `<sup>` ref points to it from the rendered text.

This rule applies equally to:
- Adding a NEW fact (e.g. «Speciesbank gegründet 29. Februar 1788»).
- Verifying a fact you already wrote, then keeping it (e.g. «67 Dukaten aus der rauen, nicht feinen, Cölln. Marck» — verified against Wikipedia DE «Dukat»).
- Confirming a term IS or IS NOT period-attested (e.g. «Zollpfundfuß» dropped because Meyers Konversationslexikon 1888 + Bobzin + Wikipedia DE «Wiener Münzvertrag» do not attest it).

**Why the urgency.** Web-sourced facts citation must happen *while the source is still in your context*. Don't just cite sources at the end of a chat reply — those evaporate; the bibliography file + inline `<sup>` is what actually ships with the artefact and travels with the data. If you defer the citation step to «later», you almost certainly will not have the URL, the exact quote, or the exact wording in scope by the time you commit, and the next session reading the YAML without the chat transcript sees a fact with no source — a silent §0 regression. The compound effect over many sessions is data drift toward unverifiable assertions.

**Skipping either step silently regresses §0 (no invention)** — a fact without a recorded source, OR a recorded source that nothing in the prose links to, becomes invention the next time someone reads the YAML without the chat history.

**Self-check before declaring a web-research task done**: search the diff for the new `ref{N}` ids — they should appear at least twice (once in the references file defining the entry, once or more in the prose as `<sup>[{N}]</sup>` inline). If the ref appears only in the bibliography file, the inline-cite step was skipped; go back and add it. If the diff has prose changes but no new `ref{N}` and the change came from web research, the bibliography step was skipped; go back and add it.

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

### 9a. Multi-specimen merge — preserve all data, never collapse

> **Deduplication is data merge, not data drop.** When the same coin (per §9.3 — same KM# / Hede# / Lange# / Sieg# index) appears as **multiple specimens** (two Bruun-PDF lots of the same KM in different auction parts; three Bruun lots of the same KM in different years; ucoin + Numista + museum entries for the same type) the records merge into ONE coin entry — but **every per-specimen observation that differs (weight, fineness, year, condition, mintmark) must be preserved**.

**The mistake to avoid.** Picking the "best" specimen for the canonical fields and reducing the others to a one-line mention in `note` text. The other specimens' weight observations, condition grades, mint-master initials and provenance disappear from the structured data — future sessions reading the YAML without the chat history see a single arbitrary observation and have no way to reconstruct the variance the source documented.

**The right pattern (per field):**

- **`weight_rough_g`** — list of `{value, source}` entries, one per specimen. The list grows with each new specimen; old entries are never overwritten or replaced.
  ```yaml
  weight_rough_g:
    - value: 13.26
      source: Bruun III, lot 11304 (Bruun-coll. 8149, 1842 specimen)
    - value: 13.28
      source: Bruun IV, lot 17185 (Bruun-coll. 8168, 1844 specimen)
    - value: 13.29
      source: Bruun IV, lot 17190 (Bruun-coll. 8184, 1847 specimen)
  ```
- **`fineness`** — single field, but if multiple measurements diverge meaningfully, switch to a similar list shape (or note the variance + cite the divergent source).
- **`sources`** — one entry per specimen citation (auction lot / museum record / catalogue listing). Each `ref` field carries the specimen-specific detail (collection-id, lot-no, page, year, condition, weight) so a reader can identify exactly which physical coin contributed which value.
- **Multi-year same-KM** — ONE entry with `year_label: "1842, 1844, 1847"`, `year_first: 1842`, `year_last: 1847`, `year_ranges: [[1842,1842], [1844,1844], [1847,1847]]`. Each year's specimen contributes its own weight to `weight_rough_g` and its own citation to `sources`.
- **Bruun-citation primacy** — `bruun_collection_id` / `bruun_part` / `bruun_lot_no` / `bruun_page` carry the **best-conditioned** (or earliest if grade tied) specimen as a fast-lookup anchor. Alternative specimens travel in `sources` with full Bruun-coll/part/lot/page detail in the `ref` text — losing none of the citation data, just structured slightly differently.

**Why this matters.** Catalog variance — specimen weights spanning ±0.5g for the same KM, different mintmasters' initials across years, NGC grades from VF-30 to MS-65 — is **research signal**. Numismatic scholarship lives off these variations. Collapsing them into one number forces every future researcher to re-extract the data we already had in hand.

**Operational test before committing a "merge"**: inspect the diff. For every specimen of the source you're consuming, the diff must add at least:
- one `weight_rough_g` list entry (if weight is published)
- one `sources` list entry (always, with full per-specimen citation)

If a specimen contributed neither, the merge is data-lossy — go back and add the per-specimen entries.

**This rule applies to ANY data merge across sources** — Bruun is just the current trigger. ucoin + Numista + museum entries for the same KM should similarly merge into one entry with multi-source weight/grade/diameter data preserved as a list, never collapsed to a single representative value.

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
python scripts/build.py --location schleswig_holstein   # single location, all languages
python scripts/build.py --location schleswig_holstein --lang de   # single page
python scripts/build.py --debug            # also writes output/debug/*.json
python scripts/build.py --validate-only    # runs schema validation, no rendering
```

## Git workflow

- **main** = source of truth. Every push triggers GitHub Actions → build → deploy to Pages.
- **Feature branches** for larger changes (new location, template rework).
- **Commit messages**: conventional prefixes — `data:` (YAML changes), `schema:` (model changes), `template:` (render changes), `build:` (script logic), `docs:`, `fix:`.
- **Commit messages MUST be in English only** (subject + body), regardless of the language used in the chat conversation. Project communication may be in Ukrainian, but git history is English-only.
- Commit small, commit often. YAML diffs are readable.

### Commit cadence + push reminder (operational rule)

> **Commit at every atomic task boundary.** When a discrete task finishes — a bug fix lands, a prose passage is rewritten, a new field is added, a research finding is integrated — create a commit immediately. Do not let modified files accumulate across multiple unrelated tasks; that turns the eventual commit into an archaeology problem and destroys reviewable history.
>
> **What counts as «atomic»:**
> - One logical change with one clear motivation (e.g. «fix Mark Sch.-H. Courant fraction», «add Krone formal-standard sourcing», «rewrite kronemont_fine bar_title»).
> - Touches one or a few related files. If a single change spans 6+ files across unrelated subsystems, it's probably 2-3 atomic tasks bundled together — split.
> - Builds cleanly on its own (`python scripts/build.py --validate-only` passes).
>
> **At the end of every chat task that produced changes:**
> 1. Run `git status` to see what's uncommitted.
> 2. Group the changes into atomic commits (one per logical task) and create them with conventional-prefix messages (`data:`, `template:`, etc.).
> 3. Verify the build still passes (`python scripts/build.py`).
> 4. **Remind the user to push.** Never push autonomously — pushes go to public Pages and need explicit user approval. End the response with a one-liner like «N commits ready locally — `git push` when ready.»
>
> **What this prevents:** the «I thought you committed already» surprise — a session ending with 13 files modified, multiple unrelated tasks tangled together, and no git history showing the work in progress.

### One-off / scratch scripts

Anything that runs **once** on a specific dataset and won't be replayed (data migrations, ad-hoc cleanups, one-time imports keyed to a particular ruler / mint / catalog) lives in **`scripts/oneoff/`** — gitignored. Do not commit it.

Truly reusable utilities (build steps, periodic enrichment passes, idempotent quality checks) go directly under `scripts/`. Tests:

- *Could this run again next year on a different dataset?* → `scripts/`.
- *Is the input data hardcoded / already gone / consumed?* → `scripts/oneoff/`.

Past examples of one-off scripts (now removed): `cleanup_sources.py`, `migrate_notes.py`, `relocate_data_notes.py`, `fix_wrong_numista_urls.py`, `manual_translations.py`, `add_new_coins.py` (Gottorp Duchy import), etc. — all served their migration purpose and were dropped from the repo.

## Data editing workflow

1. Edit the relevant YAML file (e.g., add a coin to `data/locations/schleswig_holstein.yml`)
2. Run `python scripts/build.py --validate-only` locally to catch schema errors
3. Optionally `python scripts/build.py --location schleswig_holstein --lang de` to preview
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

**Rule: NEVER translate coin denominations or Müntzfuß names.** They stay in their German / Latin / Danish period form across all three language pages, including inside running prose and Rechnungsfraktionen blocks.

This includes (non-exhaustive):
- **Coin denominations**: Thaler, Reichsthaler, Gulden, Kreutzer, Batzen, Pfennig, Heller, Groschen, Mariengroschen, Schilling, Sechsling, Dreiling, Marck, Mark, Skilling Danske, Kroneskilling, Krone, Dukat, Friedrichsdor, Pistole, Vereinsthaler, Vereinsmünze, Vereinsdoppeltaler, Doppelkrone, Conventionsthaler, Couranttaler, Speciedaler, Rigsdaler, Rigsbankdaler, Rigsbankskilling, Mark Banco / Marck Banco, Pfund Banco, Schilling Banco, Pfennig Banco, Sterntaler, Blutdollar — and any variant compound (e.g. «1 Reichsthaler Sch.-H. Courant», «1 Marck Courant», «½ Reichsthaler»).
- **Müntzfuß / standard names**: 9-Thalerfuß, 9¼-Thalerfuß, 10½-Thalerfuß, 12-Thalerfuß, 14-Thalerfuß, 18½-Thalerfuß, 30-Thalerfuß, 24-Guldenfuß, 24½-Guldenfuß, 52½-Guldenfuß, 45-Guldenfuß, 20-Guldenfuß, 10⅔-Pfund-Banco-Fuß, Reichsmüntzfuß, Reichsdukatenfuß, Konventionsfuß, Vereinsmünzfuß, Reichsgoldmünzfuß, Graumannscher Müntzfuß, Lübischer Müntzfuß, Hamburgischer Banco-Fuß, Altonaer Banco-Fuß, Burgundischer Fuß, Zinnaischer Müntzfuß, Schleswig-Holsteinisch Courant, Schillingfuß, Rigsbankdalerfuß, Bancovaluta, etc. — and any synonym written as a `-Fuß` compound.
- **Institutional / ordinance names**: Hamburger Bank, Altonaer Bank, Schleswig-Holsteinische Speciesbank, Königliche Münze zu Altona, Wiener Münzvertrag, Münchener Münzvertrag, Dresdener Münzvertrag, Reichsmünzordnung, Forordning, Müntzconvention, Bankordnung — proper nouns of period institutions and decrees.

What that means in practice: a UK reader sees «1 Thaler = 24 Gute Groschen», not «1 талер = 24 хороших гроші». An EN reader sees «1 Thaler Specie = 60 Schilling S.-H. Courant», not «1 Specie thaler = 60 Schleswig-Holstein Courant shillings». Quantifiers, common verbs and connective prose ARE translated normally; only the period-correct numismatic noun stays.

The exception remains the small set of explicitly-translated UI labels in `data/i18n/ui.yml` (column headers, button captions, section titles like «Rechnungsfraktionen» / «Accounting fractions» / «Розрахункові фракції»). Those are user-interface chrome, not numismatic content.

UI strings (column headers, navigation, buttons) live in `data/i18n/ui.yml`.

## Anti-patterns to avoid

1. **Mental reframing of user requests.** If the user says "don't change X", don't change X even if a "better" change seems obvious.
2. **Inventing sources.** If unsure, say `verified: false` and `verification_note: "not found in online sources"`.
3. **Rounding silently.** All numbers in YAML must be traceable. If the source says 3.46 g, store 3.46 not 3.5.
4. **Fixing YAML in one place while leaving equivalent issue elsewhere.** E.g., don't rename KM# 82's nominal without checking KM# 42.1 for the same pattern.
5. **Leaving HTML hand-edits in site/.** site/ is regenerable. If the fix belongs there, it belongs in the template or data.
6. **Proposing a coin-merge without checking metal/composition first.** When suggesting that a ucoin/Numista entry is the same coin as an existing base entry (i.e. fold-as-alt), **metal must be a hard filter** before nominal/year/weight overlap. Two coins of the same denom + year + ruler but different metals (gold vs silver, billon vs copper) are NEVER the same type — they're related issues at most. Pre-screen scripts that match by year + denom token overlap will produce false positives if they ignore composition; always include the metal field in the comparison output and flag mismatches as automatic disqualifiers, not «similar candidates worth checking». Same applies to fineness mismatches beyond ~2 % — different fineness usually means different Krause sub-variant.

## Checking your work

Before committing:
```bash
python scripts/build.py --validate-only   # schema OK
python scripts/build.py                    # builds successfully
# open site/schleswig_holstein/de/index.html in browser — spot check
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
- **Never call `mcp__Claude_Preview__preview_stop`** without explicit user permission — even if the preview seems idle, finished, or redundant. The user runs the preview lifecycle; Claude does not stop it unilaterally. If a preview restart is needed (e.g. to pick up new files), ask first; if disk-space or memory pressure becomes an issue, surface it and let the user decide.

Never invent translations for technical German numismatic terms without confirming with the user.

## Prior work (context)

This project began as iterative research in claude.ai chat. Before this build pipeline existed, three main HTML artifacts were hand-built:

1. **Schleswig-Holstein** (180KB, 86 coins across 7 Münzfüße, 1618–1873). This is the fidelity target for the first build — `data/locations/schleswig_holstein.yml` + build pipeline should reproduce it structurally.
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
5. **Ask the user** — if all four tiers fail, ask the user to paste the page HTML / Markdown / a screenshot directly into chat. Do not silently abandon the verification. Phrase it precisely: «Numista N#XXX still won't load through any tool I have. Could you open the page in your browser and paste the relevant section here?»

**For PDF content** (Bruun Part II, Wilcke I/II, NNUM articles, danskmoent.dk PDFs):

Use the **pdf-viewer MCP** (`mcp__pdf-viewer__display_pdf` to open, then `mcp__pdf-viewer__interact` to navigate / search / get_text / get_screenshot). Accepts both local file paths and HTTPS URLs. Most efficient for: searching by lot number across a 356-page Bruun catalogue, extracting Hede tables, getting a specific page screenshot for cross-reference. If the PDF tool is unavailable in this session, fall back to: WebFetch on a direct PDF URL → ask the user to provide the relevant page text.

**Numista-specific:** WebFetch and Apify both routinely return 403 on Numista catalogue pages (mi=…, ru=…, large queries especially). Chrome MCP works reliably (Cloudflare challenge resolves automatically after ~5–10 s — wait once, then re-issue `get_page_text`). If a verification depends on Numista data and Apify is rate-limited, **switch to Chrome MCP immediately** — do not abandon the verification.

**Pattern for browser automation via Chrome MCP:** always batch actions with `browser_batch` (the runtime gives a system-reminder if you don't). Sequence: `list_connected_browsers` → `select_browser` → `tabs_context_mcp(createIfEmpty: true)` → then a single `browser_batch` with `[navigate, get_page_text]` per URL. For multi-page comparisons, one `browser_batch` per URL keeps the round trip count low.

**General principle:** when a tool fails, the next sentence in your response should *not* be «I cannot verify». It should be «trying tier N+1». Only report «cannot verify» after the whole chain — including asking the user — has been exhausted.

## Numista API budget — ASK before bulk-fetching (May 2026 only)

> **Time-scoped rule: applies through May 2026 only.** Re-evaluate at the
> start of June 2026 — the user's monthly Numista quota resets and the
> rule may be relaxed or dropped. If today's date (see `# currentDate`
> in this file's context) is past 2026-05-31, ask the user whether this
> rule still stands before applying it.

The user is on a **rate-limited Numista API plan** (200 calls / 24h on the free tier; in May 2026 the user explicitly noted the remaining monthly budget is scarce). Calling `https://api.numista.com/v3/...` consumes that quota.

**While this rule is active: before issuing more than ~5 Numista API requests in a session, STOP and ask the user.** Phrase it as a budget request, not a fait accompli, and propose alternatives. Example:

> «Для класифікації 70 коінів треба ~140 Numista API викликів (search + type fetch). У тебе ліміт квоти. Альтернативи:
> (a) Скрапити кожний coin-page через Chrome MCP (повільно, але без квоти)
> (b) Обробити лише 10 пріоритетних KM# і пропустити решту
> (c) Витратити квоту і прийняти ~140 запитів
> Як вирішиш?»

**Never silently burn the quota.** Even if the script is technically correct and the data would be useful, the user needs to make the budget call. Cached requests in `scripts/cache/numista/<nid>.json` are free to re-read — only LIVE API calls count. So always check the cache first, and only ask permission for the new fetches.

The same principle applies to any other paid/quota'd resource you might integrate later (e.g. authenticated APIs, paid scraping services) — but those have their own scope and timeline; this specific rule is May-2026-bound.
