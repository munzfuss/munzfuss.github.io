# Numismatic Münzfüße Project — Claude Code Context

> **Read this file first on every session.** It contains non-negotiable principles and conventions developed over many research sessions. Supporting files: `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/CONVENTIONS.md`, `docs/GLOSSARY.md`, `docs/SOURCES.md` (per-source quirks log), `docs/PLAYBOOKS.md` (step-by-step procedures for recurrent tasks), `docs/notes/YYYY-MM-DD.md` (immutable daily reasoning archive).
>
> **Rules vs procedures split.** `CLAUDE.md` carries IMMUTABLE RULES — what is forbidden, what is required, what conventions apply. `docs/PLAYBOOKS.md` carries EXECUTABLE PROCEDURES — how to actually do recurrent tasks (per-case Hede dedup merge, ucoin Composition harvest session, web-research citation cycle, Müntzfuß disambiguation, adding a Bruun specimen, adding a new location, cross-Krause-volume KM-collision handling, session lifecycle, closing a TODO). When you find yourself asking «what's the procedure for X?», check `docs/PLAYBOOKS.md` PB-N first.
>
> **Also read `docs/TODO.md` at session start.** It tracks open audit items the user has flagged across sessions (continuous-year-range verification, etc.). Surface relevant TODO entries to the user when their current task touches on those topics, so we don't drift past them silently.
>
> **And read `docs/handoff.md` at session start.** Short-term session state — current focus, pending verifications awaiting user input, recently-changed surfaces, local-commit state. Distinct from `docs/TODO.md` (long-term audit items with full design context) and this file (stable conventions). Update at task / chapter boundaries; prune entries that no longer help the next session pick up cold.

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

### 0b. Hypothesis vs. fact — never collapse the two

> **This is a scholarly numismatic study, not detective fiction.** A confident-sounding explanation for an observation must be backed by data you actually opened, not by what feels plausible from context. Hypotheses are legitimate tools — but they must be labelled as hypotheses, and the next move is always to try to prove or disprove them, not to ship them as conclusions.

**The failure mode this rule guards against.** A surprising data point appears (two sources disagree, a number looks off, a value seems to defy the standard). The mind reaches for a satisfying explanation — «must be a typo», «probably an OCR error», «by analogy with X this is surely Y», «the parser likely truncated this». That explanation gets written into the rendered prose as if it were established. It feels like analysis. It is, in fact, a guess that bypassed verification.

Concrete real example from this project (caught 2026-05-10): a 2-Speciedaler 1663 row carried two competing KM numbers — Bruun's auction catalogue printed «KM-240», Numista showed «KM-241» for the same physical type. The note prose was written explaining this as «Bruun-parser typo / OCR artefact». When the underlying `scripts/cache/bruun/lots/part4.json` was opened afterwards, the `body_excerpt` plainly read «Dav-3547; KM-240; Hede-62A; Sieg-80.1; ...»: Stack's Bowers' own auction catalogue had printed «KM-240». The parser captured this faithfully. The «typo» explanation was a hypothesis dressed as a conclusion — the actual story (Bruun cataloguer cited the 1-Speciedaler's KM number on the 2-Speciedaler lot, likely an «adjacent KM» mistake on Bruun's side, or an older Krause edition) only emerged after checking the body_excerpt + cross-referencing four other sources.

**Required moves:**

- **Before writing «X is because Y», verify Y from the actual data.** If Y is in a local cache, open the cache file. If Y is on a web page, fetch the page. If Y is the output of a script, run the script (or read its source). The verification step is the work; skipping it doesn't save time, it pollutes the artefact.
- **Hedge markers are mandatory for unverified claims.** Use «hypothesis», «possibly», «I haven't verified this», «pending check against …», «припускаю», «гіпотеза». Confident phrasing — «this is …», «the cause is …», «the parser misread …» — is reserved for claims that have been verified.
- **When data is missing, name the gap.** Never fill it with a plausible story. «Source X does not document this; status unknown until …» is honest. «X is probably …» without an explicit hypothesis label is not.
- **After framing a hypothesis, attempt to prove or disprove it.** A hypothesis that survives a session without any verification effort isn't yet research output — it's just a thought. Either run the check or leave the question open with the gap labelled.
- **When a hypothesis turns out wrong, fix the prior assertion publicly.** Don't quietly delete it; record what was claimed, what verification showed, and the correction. Future sessions reading the YAML / commit log need to see the trail to avoid repeating the mistake. (See e.g. the «Bruun-parser KM-typo» correction in commit `37f5b6d`.)

**Forbidden:**

- «It must be a typo / OCR artefact / cataloguer's error» — written into prose without checking the source PDF, cache record, or parser output to confirm.
- «By analogy with X, this should be Y» — used as a final claim. Analogy generates hypotheses, not conclusions. The hypothesis still needs verification before it ships.
- «Likely / probably / presumably / it seems that» — written into rendered prose without an explicit «hypothesis pending verification» marker. The rendered artefact carries verified claims only; speculation belongs in chat or in clearly-flagged verification notes.
- «The parser is wrong» / «the source is incorrect» — claimed without diff'ing the parser output against the underlying text, or without cross-checking the suspect source against ≥2 independent peers.

**Operational test before any analytical claim leaves your fingers:**

1. Did I open the underlying data (cache file, source page, computed value, body_excerpt) to verify this *specific* claim?
2. If no — am I labelling this explicitly as a hypothesis to be tested? Did I name what would prove or disprove it?
3. If yes — does the data actually say what I'm about to claim, in those exact words?

This rule complements §0 (no invention). §0 forbids unsourced claims in the rendered output; §0b forbids unverified analytical leaps regardless of where they appear — chat, prose, commit messages, audit notes. Together they enforce a single discipline: every claim is either verified-and-attributed, or labelled as the hypothesis it actually is.

### 0z. Three reader roles — always know who you're writing for

> **Every line of text you produce has exactly one of three readers. Mis-identifying which one is the most common cause of voice violations on this project. Decide before you write, not after.**

**The three roles:**

1. **AI (you, future-you, other agents).** Audience for: code comments, docstrings, commit messages, `docs/*.md`, `scripts/oneoff/*.py` headers, internal scratch notes, the message-summary at the end of a chat turn that captures «what just happened». Treat this as a note from yourself to yourself: assume the reader has full project context but no memory of *this* turn — write what next-session-you needs to know to pick the work up cold. Density and jargon are encouraged; no hand-holding.

2. **The user (Serhii).** Audience for: chat replies in this conversation, questions about ambiguous data, choice-points where direction is needed. The user is an expert numismatist and the project's principal researcher; he decides what is investigated and what gets shipped. He sees this chat only — never the AI-internal scaffolding, never the rendered artefact (those are separate channels). When writing to him: be direct, propose options when there's genuine choice, surface findings concisely, and never narrate effort («let me search…», «I'll now…»). Ukrainian, ти-form, expert register.

3. **The end-reader.** Audience for: every byte that lands inside `data/locations/*.yml`, `data/shared/*.yml`, `data/i18n/*.yml`, the rendered HTML on the per-location pages and landing, the references files. This is a numismatist or historian using the artefact as a finished reference work. **They never see the chat, never see the commits, never see the project's internal classification decisions.** Their experience is exclusively the rendered page. They want a polished encyclopaedic article: facts, sourced; mathematics, verified; period-correct typography; no mention of «we», «our taxonomy», «our card», «this artefact», «classification pending», or any other process artefact.

**The most common mis-targeting failure on this project:** project-internal rationale or analyst-deliberation written into role-3 surfaces (the rendered artefact). Examples that have actually slipped through and had to be cleaned up:

- «Beleg für die drei numerischen Synonyme im `name`-Feld unserer Vereinsmünzfuß-Karte» — explains a project-decision (why we put three numbers in the name field) inside a citation that the end-reader sees as a bibliography entry. The end-reader has no concept of a `name` field or an «our card», and the citation doesn't establish anything historical — it justifies *us*.
- «Beleg, daß ‹Zollpfundfuß› kein period-attestierter Terminus ist (pgl. CLAUDE.md §0 ‹no invention›)» — same shape: explains why we *didn't* coin a particular term. CLAUDE.md is an AI-internal document; cross-referencing it from a reader-facing bibliography entry breaks the role boundary.
- «Period-offizielle Bezeichnung 1871–1914: ‹Mark deutscher Reichswährung› — Grundlage für die Karte Reichsgoldmünzfuß.» — the «Grundlage für die Karte» half is project-internal scaffolding; the historical fact (the period name) is fine on its own without naming the card it backs.
- «`Konventionscouranttaler` — die Bezeichnung der MÜNZE (24-Groschen-Variante zum Konventionstaler bei 32 Groschen), nicht ein eigener Müntzfuß-Name» — explains the project's *classification* of the term (whether it's a Fuß or a coin name). Useful to us; invisible noise to the reader, who just wants to know what «Konventionscouranttaler» is.
- «Drei Datierungs-Anker — bewusst getrennt halten: 1667 / ~1700 / 1738. Die einzelne Standard-Karte zeigt ‹1566 → ca. 1700› als Faustanker; die Timeline-Visualisierung auf den Locations-Seiten gibt jeden Anker einer eigenen Schichtart (mint=1667, circulation=1700, status=1738), um die historische Asymmetrie sichtbar zu machen.» — pure project-decision narration. The reader cares that the three dates are documented; how *we* visualise them is not their concern.

**Operational test before any line of text leaves your fingers, two questions:**

1. *Which role am I writing for right now?*
2. *Would a member of any other role be confused or misled by this sentence?*

If sentence references «our card», «this artefact», «our `name` field», `CLAUDE.md`, `data/...yml` paths, or any project-decision rationale — and it's destined for a role-3 surface — it's mis-targeted. Cut it, or move the historical fact to the prose without the project-meta wrapper.

This rule supersedes and concretises §0a (reader voice vs analyst voice): §0a says *what* the voice should sound like; §0z says *how to decide* which voice applies before opening the YAML or the chat. When the rules say similar things, §0z is the canonical decision-procedure; §0a is the executional style guide.

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

**Cyrillic-transliteration trap (mandatory check on every uk translation
of a German term).** German numismatic vocabulary is dense with -ung,
-ation, -fuß, Reichs-, Münz- compounds. A common failure mode is to
mechanically Cyrillicise the German root and end up with a word that
*sounds Slavic-shaped* but means nothing — or, worse, collides with
an unrelated Ukrainian word. Two real cases that lived in the data
through several sessions before being caught:

- **«прягеа»** — fabricated via «Prägung» → fake-feminine «прягеа».
  Looks like a noun, isn't one. Spread to 37 occurrences across 5
  files before audit (commit `9860a43`). The actual Ukrainian term is
  «карбування» (action) or «наклад» (quantitative figure).
- **«Реймсько-»** — «Reichsweit standardisierte» mis-rendered as
  «Реймсько-стандартизована». Reads as «Reims-» (the French city) — Reims
  has nothing to do with the Wiener Münzvertrag. The actual rendering
  is «загальноімперсько-стандартизована» (Reich-wide standardised) or
  «імперсько-».

Operational rule: before committing any uk translation of a German
compound that looks unfamiliar, mentally test the result against
**(a)** existing Ukrainian dictionaries — does the word actually
exist? — and **(b)** does the resulting Cyrillic string accidentally
look like an unrelated Ukrainian/Russian word (place name, common
noun, etc.)? If either check fails, the translation is wrong even if
the German source is rendered «correctly» phoneme-by-phoneme. Use a
proper Ukrainian numismatic equivalent or — when no equivalent exists
— keep the German period form intact (per the i18n policy below).

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

**Verified-wins-over-unverified — the merge-conflict rule.** When two candidates are being merged into one resulting entry — whether automatically (seed regen merge, auto-suppress fold, cross-location coverage scan) or manually (Pattern B consolidation of two curated entries) — and they disagree on the value of a measurement field (`fineness`, `weight_rough_g`, `diameter_mm`, `mint`, etc.): the source-attested value WINS over the `(?)`-marked one. The unverified candidate's value MUST NOT propagate to the result. Concretely: a curated entry carrying `fineness: 0.875` + `fineness_verified: true` (Numista-cited) being merged with a seed entry carrying `fineness: 0.88889` + `fineness_verified: false` (canonical-anchor-inferred) yields a merged entry with `fineness: 0.875` + `fineness_verified: true` — the canonical-anchor inferred reading is dropped because it has weaker provenance than the source-cited one. This rule applies regardless of which side is «existing» vs «fresh» in any specific merge path; verification status drives the precedence, not which YAML the value happened to sit in first. The seed builder's `_merge_one` encodes this directly (see `_VERIFIABLE_FIELDS` in `scripts/maintenance/build_hede_denmark_seed.py`); per-case manual merges follow the same principle by convention.

**Source years are immutable — never truncate to fit our taxonomy.** A coin's `year_first` / `year_last` / `year_label` / `year_ranges` reflect what the source documents. **Do not silently shorten** the range to align with a Fuß window, a Phase boundary, or any other locally-defined annotation. If the source documents that a type was minted 1617, 1627, 1628, 1629, then `year_first: 1617`, `year_last: 1629`, `year_ranges: [[1617,1617], [1627,1629]]`, `year_label: "1617, 1627–1629"` — even if our Phase A for that Fuß ends in 1625. Phases and Füße are **our** structural annotations; years are **the source's** factual record. When the documented years overshoot a phase boundary, leave the years intact and (a) place the coin in the phase whose Münzfuß it actually represents (year_first determines phase per §8.2) — `year_last` overshooting the phase end is acceptable, or (b) note the cross-phase span explicitly in the prose. Never quietly clip.

### 5. Source hierarchy

> **Source-quirks log.** Before investing time in re-diagnosing a surprising answer from any source listed below, scan `docs/SOURCES.md` §13 «Known-issues log». Every entry there cost a session of detective work the first time round; the next session that hits the same pattern should recognise it from the log in 30 s rather than 30 min. When you encounter a new source quirk that took > 15 min to figure out, ADD it to §13 before closing the session.

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

### 5a. Reference-style — bibliographic only, Wikipedia-style

> **The `*-references.yml` files are bibliographies, not commentary. One source per entry, citation-only — no quotes, no analysis, no «this proves X».**

A reference entry's job is to tell the reader **where to verify the claim**, full stop. Anything that interprets, weighs, or argues about what the source says belongs **in the prose where the source is cited**, not inside the bibliography slot. The shape of one entry:

```yaml
- id: ref{N}
  content:
    de: |
      <b>Author surname, First name</b>: <i>Title</i> (Publisher, Year) —
      <a href="https://example.com/url" target="_blank">example.com/url</a>.
      Optional one-line scope note describing what the source attests
      (≤ 140 chars, no quotes, no «proves X»).
    en: …
    uk: …
```

**Required content:**
- Author / institution name (bold).
- Title (italic).
- Publisher and/or year for printed works; URL for online works.
- Hyperlink with `target="_blank"`.
- At most one sentence (≤ 140 chars) saying *what the source attests* — e.g. «source for the Speciedaler standard 25.28173 g», «attests the 1618 patent date».
- **Concrete page hint** when the source is a long-form work (see «Mandatory page hints» below).

**Mandatory page hints for long-form sources.** When the URL or work points to a document of **≥10 pages** — PDF book, multi-chapter monograph, auction catalogue, periodical issue, multi-volume Konversationslexikon, scanned ordinance gazette — the scope note MUST carry a **concrete** page reference to the cited claim. The ref body without a page hint is invalid for these sources.

Forms accepted (use whichever fits the underlying work's pagination scheme):
- `«verbatim quote» (S. 14)` — short quote + page, the canonical form.
- `Band 11, S. 890–891` — for multi-volume works name the volume + pages.
- `Kap. 4, S. 123–125` — chapter + pages when the work is chapter-based.
- `§ 5, S. 12` — paragraph + page in legal / ordinance texts.

**Approximate ranges, vague descriptors, and «irgendwo im Buch» are forbidden.** Specifically NOT acceptable: «ca. S. 14–25», «im ersten Kapitel», «ungefähr Mitte», «passim», «throughout», «зокрема в книзі». The reader who follows the ref must land on the exact line of the claim, not skim the whole work.

**Wikisource / Wikipedia exception.** If the underlying print source has page numbers, those still go in the scope note (Wikisource transcribes per-page, so «MKL 1888, Band 11, S. 890–891» applies even though the URL is a wiki page). Pure wiki-only articles (no print original) use the section anchor instead, e.g. «Abschnitt ‹Geschichte›» / «section ‹History›».

**Catalogue-of-catalogues / umbrella refs are forbidden.** A single `ref{N}` listing «Stack's Bowers Part I PDF + Part II PDF + Part III PDF + Part IV PDF» is a bundle and violates the «Multi-source bundles» rule below. Each PDF / part is its own work and gets its own atomic ref when cited inline. Catalogue-level «for reference» bibliography entries that no inline `<sup>[N]</sup>` points to are dead weight — the per-claim `sources[].ref` arrays on coin entries already document citations with full part + lot + page detail, that's where the catalogue surfaces.

**Operational test before committing a ref to a long-form source.** Look at the scope-note string. Does a page reference appear as a literal number? If no — do the page-finding step now (pypdf / pdftotext / WebFetch of archive.org's djvu text / pdf-viewer MCP / Wikisource page-marker scan). Skipping it silently regresses §0 — the reader cannot verify the claim without re-skimming hundreds of pages, which means the citation has failed at its primary job.

**Forbidden inside a ref body:**
- Multi-sentence analysis, argumentation, or interpretation («establishes that …», «proves that …», «in other words: …»).
- Long verbatim quotes (more than ~25 words). If a quote is the evidence, it goes in the prose where the ref is cited, with the ref pointer next to it.
- Multi-source bundles. Each source gets its own `ref{N}` entry, even if the same prose paragraph cites three of them. Inline citations stack: `<sup><a href="#ref10">[10]</a><a href="#ref11">[11]</a><a href="#ref12">[12]</a></sup>`.
- Cross-references between refs («see ref30», «contrasted with ref29»). Cross-talk goes in the prose.
- Marketing / institutional fluff («the world's largest collection insured for 500 m DKK»).

**Numbering and migration:**
- Existing `ref{N}` ids are stable. When splitting a bundled ref into atomic sources, keep the lowest existing number with the dominant source and **append the new atomic refs at the end of the file** (next free `ref{N+1}`, `ref{N+2}`, …). Never renumber existing entries — every inline `<sup><a href="#ref{N}">` in `data/locations/*.yml` and `data/shared/fuesse.yml` would silently break.
- When you split a bundle, update the inline citation in the prose to a stack of the new atomic refs at the same position: a single `<sup>[35]</sup>` becomes e.g. `<sup>[35][39][40]</sup>`.
- When you trim analysis out of a ref body, the analysis usually already exists in the prose that cites the ref (the ref body was a duplicate). If it doesn't, move the analysis into the citing prose; never leave it in the ref slot.

**Why this matters.** A reader scanning the references list expects «author + title + URL» — the same thing every academic encyclopaedia and Wikipedia article does. A 600-word analysis paragraph buried in slot 35 between slots 34 and 36 is invisible to that scan and indistinguishable from prose; it should *be* prose, with the citation hanging off it. Bundled refs make footnote stacks ambiguous (which of the five sources backs *this* sentence?). Atomic refs let the reader follow the exact source that backs each claim.

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

### 8a. Müntzfuß disambiguation when sources don't decide

**When this rule applies — both conditions must hold:**

1. The available sources (inscription, catalogue, ordinance per §5) do not directly establish which Müntzfuß the coin belongs to.
2. The coin's year(s) fall within a window where two or more Müntzfüße were in force or could plausibly have been struck.

If sources do decide, follow §8.1 — this rule does not apply, and inventing ambiguity where none exists is a §0 violation.

**Filtering pipeline.** Apply each step in order against the candidate-fuss set; the first step that picks a unique fuss is the answer. Each step narrows the candidate set rather than producing the final decision on its own (except where stated).

1. **Metal mismatch.** Drop any candidate fuss whose metal class doesn't match the coin's metal. A gold coin cannot belong to a silver-only fuss; a silver coin cannot belong to `reichsdukatenfuss`. Bimetal pairings (e.g. Pistolenfuß-paired silver coins, Vereinsmüntzfuß silver-tier paired to Vereinsgoldmünze) are handled per the relevant fuss definition.

2. **Denomination-name mismatch.** Each fuss carries a characteristic denomination repertoire. If the coin's nominal is typical for fuss B but never appeared in fuss A, drop A. Soft signal — denomination drift across fusses does happen — but a clean nominal-name match still narrows the set quickly. Examples: «Rigsbankskilling» is characteristic of 18½-Thaler-Fuß; «Speciedaler» of 9¼-Thaler-Fuß and not 9-Thaler-Fuß; «Vereinsthaler» exclusively of Vereinsmüntzfuß.

3. **Feingewicht (when fineness is specimen-attested) — Δ-from-Soll comparison.** Compute `Δ = (specimen_Feingewicht − Soll_Feingewicht) / Soll_Feingewicht` for each candidate fuss's Soll-value at this fraction. Coins typically run slightly under the standard (specimen variance + wear); a small fraction run slightly over (rarely beyond +2%, with rare exceptions for tariff coins or high-quality cabinet specimens). The candidate with the smallest |Δ| — and an absolute Δ within roughly ±2% — is the placement.

4. **Bruttogewicht (when fineness is unknown) — pattern comparison.** Without specimen-attested fineness, Feingewicht can't be computed directly. Compare the raw weight against existing same-nominal entries already placed under each candidate fuss in this project's YAML — does the specimen's Bruttogewicht cluster with one fuss's typical band and not the other's? Use as the placement signal when the pattern is clean.

5. **Fineness hint (when known but Feingewicht-Δ alone wasn't decisive).** Each fuss has a characteristic fineness signature for a given metal (e.g. .875 silver = 9¼-Thaler-Fuß; .896 gold = Pistolenfuß; .986 gold = Reichsdukatenfuß). Use as a supporting signal alongside steps 3-4 — never alone, since fineness drift, debasement, and specimen-tolerance can disrupt the signature.

6. **Escalate to user** if steps 1-5 don't pick a unique candidate. Surface the data — coin id, year, metal, nominal, Bruttogewicht, fineness (if known), the surviving candidate fusses with their Soll-values + computed Δ — and wait for the placement decision. Do not silently assign per §0.

**Scheidemünze residual.** When the specimen's Feingewicht (or Bruttogewicht-pattern at known typical fineness) is dramatically below every candidate's Soll for a full-Kurant of that fraction (typically > 20% under), the coin is not a full-Kurant of any candidate — it's a Scheidemünze per §6. Place under the *parent* full-Kurant fuss of the period (the established standard, not a contender new fuss) and mark `kind: scheide`. This handles deliberately-debased small-change tiers (Kipper-period Doppelschillinge, post-reform billon Skilling, etc.) where specimen variance can't explain the gap.

### 9. Coin inclusion criteria (source-agnostic)

When deciding whether a coin entry belongs in a location's coin table — regardless of where it was sourced (Numista, Bruun, IKMK Berlin, Lange, MGM, hand-typed from a museum visit) — apply these three exclusions, and only these:

1. **Patterns / trial strikes** — entries marked `Pn*`, `(Silver pattern strike)`, `(Gold pattern)`, "Probe", "Essai" etc. They were not struck for circulation. Skip.
2. **Exonumia** — medals, jetons, commemorative tokens, Tin/White-metal pieces without a denomination. They belong to separate registers, not to coin tables.
3. **Duplicates** — defined strictly by **catalog index**, primarily KM# (Krause-Mishler). Two entries sharing the same KM# (or the same Hede#, Sieg#, Lange# when KM# is absent) are duplicates. **Different catalog index = different type**, even if the denomination, ruler, mint, and year ranges overlap. Krause-Mishler assigns a separate KM# to each design / mint / mintmaster / fineness variant by design.

   **Caveat — same KM# across different issuers / catalogues is NOT automatically the same type.** Krause-Mishler numbering restarts within each country / region: `KM#75` in the «Denmark» Krause volume is an entirely different coin from `KM#75` in the «German States — Schleswig-Holstein» volume. Likewise for Hede (Danish), Sieg (Danish-Norwegian), Lange (Holstein), Behrens (Lübeck) — each catalogue's numbering is internal to that catalogue. Two entries colliding on a bare numeric `km`, `hede`, `lange` etc. are duplicates **only if** they refer to the SAME catalogue scope (same country/region in Krause; same author in the regional catalogues). When doing cross-location dedup or bulk import, always pre-screen by composition + nominal + ruler + year before declaring a KM-collision a duplicate; if those don't line up, the «same» KM is just a numeric coincidence between two unrelated catalogue volumes.

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

**Intra-sub-variant thinning (counter-balance to over-collection).** §9a above guards against under-merging: each specimen carries a unique observation and must be preserved. The opposite failure mode is *over-collection from one resource*: when a single museum / catalogue holds many specimens of the *exact same* sub-variant, the intermediate weights between min and max contribute no additional information about the standard's variance envelope — they are noise from one source's holdings, not independent measurements. Apply the following thinning rule when both conditions hold:

1. **One coin entry has ≥5 `weight_rough_g` entries from a single resource** (IKMK / Bruun / ucoin / Numista — counted per-resource, not in total).
2. **Within that resource, those entries sub-group by published catalog index** (per the source's own classification — IKMK `literatur` field for Lange/Hede tag, Bruun `refs` for KM/Hede/Lange, ucoin `km` field with sub-suffix) **into one bucket of ≥5 specimens** sharing the same sub-variant tag.
3. **Fineness is uniform or absent across that bucket** — same `fineness` value (or no fineness recorded). If the bucket includes multiple fineness readings, do not thin: the variance is informative.

When all three hold, sort the bucket's entries by weight ascending, keep three:

  - **min** — position 0 of the sorted list
  - **middle by list position** — position `len // 2` (NOT the median value; the entry that sits at the middle index of the weight-sorted list, deterministic for tied weights via stable sort)
  - **max** — position `len - 1`

Discard the other entries along with their corresponding `sources[]` URLs. The retained three define the variance envelope; the discarded entries' specimen IDs are by-definition not numismatically distinguishing within that sub-variant (had any been distinguishing — e.g. mule, counterstamp, off-metal strike — IKMK / Bruun would have catalogued it as a separate sub-variant tag, breaking out of this bucket).

Specimens that the source itself flags as singular — mules, off-metal strikes, counterstamped pieces, hand-curated annotations like `(mule)` or `(1620 cf Lange 534)` in our existing source labels — sit in their own one- or two-entry sub-variant buckets and are NOT eligible for thinning. The bucket size threshold (≥5) protects these single-specimen variants automatically.

**Operational reuse.** Apply this thinning rule on **every** new specimen import, not only IKMK / Bruun — any time we add weight readings from a single resource (museum API, auction catalogue, online catalogue, ucoin, Numista, future sources) that crosses the threshold within one sub-variant, do the thin at import time so the YAML never carries the noise in the first place. Better to never accumulate it than to clean it up after. The maintenance script `scripts/maintenance/thin_intra_subvariant_specimens.py` encodes the canonical decisions per audit pass; the same shape — sort by weight, keep `[0, len//2, -1]`, drop the rest plus matched `sources[]` — generalises to any resource. (Codified 2026-05-09 after a 20-specimen sweep across km-46 / km-5 / km-9.)

**Same-weight duplicate (degenerate-thin sub-rule).** Independent of the ≥5-threshold rule above, a separate degeneracy can occur with as few as TWO specimens: when two or more entries from the same resource AND same sub-variant carry the **identical numeric weight** (within display precision — same value at 2 decimals for `weight_rough_g`), those entries don't add measurement signal — they're either two custodial copies of one published reading or two specimens that happen to weigh in identical at our reporting precision; either way, only one preserves all available data, the others are noise. Discard all-but-one of the same-weight duplicates plus their matching `sources[]` URLs. Choose which to keep by maximising data: the entry whose underlying source record (IKMK JSON / Bruun lot dict / ucoin URL-index entry / Numista cache) carries the most populated fields stays; ties — when records carry the same number of populated fields — break either way (no semantic difference between them at that point). Like the threshold-rule, this fires both at import time AND in audit passes; reuse the same `thin_intra_subvariant_specimens.py` shape.

**Source-data is structured, not stringly-joined.** When two or more independent sources attest the SAME numeric value (e.g. Hede and Numista both publish 28,893 g for a Speciedaler), each attestation is its own `FieldValue` entry that shares the value but carries one source label:

```yaml
weight_rough_g:
  - {value: 28.893, source: "Hede 39A"}
  - {value: 28.893, source: "Numista"}
  - {value: 28.89,  source: ucoin}
```

Never collapse multi-source attestation into a single entry with a `\n`-joined source string (`"Hede 39A\nNumista"` is forbidden). The display pipeline already groups list-form entries by rounded value, so two same-value entries collapse into ONE rendered span with both sources accumulated into the tooltip — visually identical to the joined form, structurally clean. Audit / dedup / future query tooling can iterate entries directly without parser-of-display-string kludges.

The same rule applies to `fineness[]` and `diameter_mm[]` source attribution — every list-form measurement field uses one entry per attestation. (Closed via TODO I, 2026-05-10. Migration script: `scripts/maintenance/split_multisource_weight_entries.py`.)

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
  timeline.py                           # bar_layers / coin_year_runs / hover_zones
  render.py                             # C → HTML via Jinja2; CSS dispatch
  styles.py                             # CSS prefix generator (theme tokens + bar palette)
  style.base.css                        # Static CSS body (var(--*) refs)
  i18n.py                               # Translation resolution, number formatting
  yaml_check.py                         # AST-level duplicate-key guard
  env.py                                # local.env loader

scripts/maintenance/                    # Committed lifecycle-bound utilities
                                        # (translation cleanup, one-shot enrichers,
                                        # dedup / relink passes — not on build path)

scripts/cache/                          # ← Git submodule (munzfuss-harvest, private)
                                        # Raw + parsed fetch cache: bruun/, hede/,
                                        # ikmk/, numista/, ucoin/. NOT read by
                                        # scripts/build.py — only by fetchers,
                                        # parsers, audits, and maintenance scripts.
                                        # See «Harvest submodule workflow» below.

site/                                   # .gitignored — build output
  index.html                            # Landing page (language-switchable)
  <lang>/index.html                     # e.g., de/index.html (locations index)
  <loc>/<lang>/index.html               # e.g., schleswig/de/index.html
  assets/{style.css, app.js}            # style.css = prefix + style.base.css concat

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

### Preview-mode auto-build (operational rule)

> **When the preview server is running and this turn modified a file
> that affects rendered output, run `python scripts/build.py` before
> ending the turn.** Keeps the preview window in sync with the working
> tree without the user having to ask.
>
> **How to detect preview is active.** The harness emits
> `PostToolUse:Write hook additional context: A preview server is
> running.` after any Write / Edit. If that reminder appears anywhere
> in the turn — or if `mcp__Claude_Preview__*` tools are in scope —
> treat preview as on.
>
> **Files that affect rendered output (build-trigger):**
> - `data/locations/*.yml` — coin data, phases, references
> - `data/shared/*.yml` — fuesse, mints
> - `data/i18n/*.yml` — UI strings
> - `templates/**.j2` — Jinja
> - `config/theme.yml` — CSS theme tokens
> - `scripts/build.py`, `scripts/lib/**` — build pipeline + `style.base.css`
> - `assets/**` — copied verbatim into `site/assets/`
>
> **Files that do NOT trigger a rebuild:**
> - `docs/**`, `CLAUDE.md`, `README.md`
> - `scripts/maintenance/**`, `scripts/audit_*.py`, `scripts/oneoff/**`
> - `scripts/cache/**` (read by maintenance scripts; not by `build.py`)
> - `scripts/fetch_*.py`, `scripts/match_*.py`
> - `requirements.txt`, `local.env`, `.gitignore`
>
> **Granularity.** Run the build ONCE at end of turn, not after every
> Edit. If the turn has multiple edits across web-affecting files,
> one build at the end covers them all.
>
> **When in doubt: build.** ~5-15 s of CPU cost beats the user
> noticing a stale preview manually.
>
> **If validation / render fails**: surface the failure in the
> response, don't silently retry. Schema-validation breaks usually
> came from this turn's edits and need a fix.

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
> **Push permission grant.** A request from the user to push — phrased as «пуш», «push», «git push», «push it», «запуш», or any equivalent that names the push action — counts as explicit permission to push to `origin/main` for that turn. No follow-up confirmation is required; run `git push` and report the resulting refspec range. The push permission is per-turn and per-request — it does not pre-authorise future pushes elsewhere in the session.
>
> **What this prevents:** the «I thought you committed already» surprise — a session ending with 13 files modified, multiple unrelated tasks tangled together, and no git history showing the work in progress.

### Script directory layout

Three tiers, picked by *recurrence pattern*:

- **`scripts/`** — actively used by the build / research workflow.
  Re-runnable, idempotent, useful right now: `build.py`, the `audit_*.py`
  validators, `fetch_numista_api.py`, `enrich_from_numista.py`,
  `build_ucoin_url_index.py`. Also library code under `scripts/lib/`.
- **`scripts/maintenance/`** — lifecycle-bound utilities that aren't part of
  the build flow but are kept for re-use when the same shape of work
  recurs (next bulk import, next translation drift sweep, next ucoin
  re-link). See `scripts/maintenance/README.md` for the per-script log.
  **Committed** to the repo.
- **`scripts/oneoff/`** — truly throwaway scratch (hardcoded inputs already
  gone, data migrations consumed, one-time fixes). **Gitignored.** Past
  examples (now deleted): `cleanup_sources.py`, `migrate_notes.py`,
  `fix_wrong_numista_urls.py`, `add_new_coins.py` (Gottorp import).

Decision tests for a new script:

- *Will this run regularly as part of build / audit / data refresh?* → `scripts/`.
- *Will this run again on the next phase of similar work, but not on every build?* → `scripts/maintenance/`.
- *Single-shot, hardcoded to data already gone / consumed?* → `scripts/oneoff/` (gitignored).

## Harvest submodule workflow

`scripts/cache/` is a **git submodule** pointing to a separate **private** repo
(`munzfuss/munzfuss-harvest`). The submodule carries the regenerable artefacts
of network fetches and PDF parses (Hede HTML+JSON, IKMK JSON, Numista JSON,
Bruun parsed lots, ucoin URL index). The main repo stays slim; the build
pipeline doesn't read this cache — only fetchers / parsers / audits /
maintenance scripts do.

### First clone on a new machine

```bash
git clone --recursive https://github.com/munzfuss/munzfuss.github.io.git
```

Already cloned without `--recursive`? Initialise the submodule after the fact:

```bash
git submodule update --init
```

The submodule URL is HTTPS to a private repo, so the first clone will prompt
for GitHub credentials (or use SSH if you've set up SSH agent).

### Build doesn't need the submodule

`python scripts/build.py` (validation, render, full build) does NOT read
`scripts/cache/`. The build pipeline works on a clone WITHOUT the submodule
initialised — `scripts/cache/` is just an empty directory. The CI deploy
workflow (`.github/workflows/deploy.yml`) uses `actions/checkout@v4` with
the default `submodules: false`, so Pages deploys are unaffected by the
harvest split.

Only these workflows need the submodule:

- Re-parsing Hede (`scripts/parse_hede.py`)
- Re-fetching from any source (`scripts/fetch_*.py`)
- Running audits (`scripts/audit_*.py`)
- Most `scripts/maintenance/*` lifecycle scripts

### Committing cache changes

When a session changes cache contents (typical trigger: `parse_hede.py
--force` after a parser fix updates 100+ Hede JSON files), the workflow is:

```bash
# 1. Commit cache changes in the submodule first.
cd scripts/cache
git add <changed files>
git commit -m "harvest(<source>): <what changed>"
git push

# 2. Bump the submodule pointer in the main repo.
cd ../..
git add scripts/cache       # records the new commit SHA the submodule points at
git commit -m "build: bump harvest submodule (<reason>)"
git push
```

Both steps are atomic from the main repo's perspective: the bump-pointer
commit in main always references a commit that already exists on the
harvest remote. **Push the submodule first, then push main** — otherwise
collaborators (or CI, if it ever starts pulling the submodule) would see
a dangling pointer.

Conventional-prefix messages:
- Inside `scripts/cache/`: `harvest(<source>):` (e.g. `harvest(hede):`,
  `harvest(numista):`, `harvest(ikmk):`).
- Inside main bumping the pointer: `build: bump harvest submodule ...`.

### When in doubt, build runs

If a session that changed cache files forgets the two-step commit dance,
the symptom is: `git status` in main shows `modified: scripts/cache (new
commits)` even after pushing the cache contents. That's just the
submodule-pointer bump waiting to be committed in main. Step 2 above
fixes it.

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

**Rule: NEVER translate coin denominations or Müntzfuß names in formal denomination references** — the «Rechnungs- und Kursbindungen» / «Розрахункові та курсові звʼязки» / «Accounting and exchange links» block, Grundwerte rows that name a specific denomination as the subject of a metric (e.g. «Feingewicht Vereinskrone»), structured key/value pairs, table column headers, etc. In those formal slots the period German / Latin / Danish form stays intact across DE / EN / UK.

**Müntzfuß (-Fuß / -fod) standard names are stricter still — they NEVER translate, in ANY context** (formal block, flowing prose, headings, alike). «Reichsdukatenfuß» stays «Reichsdukatenfuß» on every page; «Kurantmøntfod» stays Danish; «9¼-Thaler-Fuß» stays the same compound. This is one tier above the denomination rule.

**For coin denominations in flowing historical prose (description, hintergrund, closing, phase narrative), localised forms are acceptable** — «67 дукатів з повної Кельнської марки», «as trade gold, Hungarian and Venetian ducats also circulated», «угорські, венеційські й турецькі дукати того ж стандарту». The strict period-form rule applies to the formal accounting / specification slots, not to every single occurrence of the noun across the artefact. When the same denomination appears both in a Rechnungsfraktionen block (formal) and a description paragraph (prose) on the same page, the formal block uses the German period form and the prose uses whatever reads naturally in the target language.

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
- **Never call `mcp__Claude_Preview__preview_stop`** unless the user has explicitly asked for it (in this turn or earlier in the same session) — even if the preview seems idle, finished, or redundant. The user runs the preview lifecycle; Claude does not stop it unilaterally. **Exception: when the user directly says «stop the preview», «перезапусти превʼю», «restart the preview», or any equivalent phrasing that names the preview AND a stop/restart action, that counts as the explicit permission this rule requires** — proceed with `preview_stop` (followed by `preview_start` for a restart) without asking again. **Specifically for «restart» / «перезапусти»: a restart is by definition stop + start, so a request to restart inherently authorises the stop step — no separate confirmation needed.** This restart-implies-stop logic is **scoped strictly to the restart phrasing** — it does not generalise to other words that could be construed as adjacent (e.g. «refresh the preview», «reset», «прибери» without «перезапусти»); for anything that isn't an explicit stop or restart request, the default no-stop rule still applies. The same applies to `location.reload()` via `preview_eval` when the user asks to reload / refresh the page. If the user mentions the preview but not a stop/restart action, ask first; if disk-space or memory pressure becomes an issue, surface it and let the user decide.

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

- **Numista** (`en.numista.com`): catalog numbers, rough weights. Two access modes, kept strictly separate:
  - **Bulk / programmatic** — exclusively via the official API v3 (`https://api.numista.com/v3/...`) through `scripts/fetch_numista_api.py` and the per-piece cache under `scripts/cache/numista/<nid>.json`. See the «Numista API budget» section below for the per-session call cap.
  - **Ad-hoc verification of a single coin page** — Chrome MCP `navigate` + read what's on screen is fine. That's regular user browsing, NOT the «substantial or repeated extraction» Numista's ToS §9.1 / §12.2 forbid. Useful for: confirming a single fineness / weight / Years field when the API quota is tight, sanity-checking what the page actually shows when our cache disagrees with reality, picking up the rare data point not exposed via the API. The line is: don't loop `fetch()` over IDs, don't dump catalogue lists, don't paginate search results en masse — do open one URL, look at what's there, close it. If you find yourself touching more than ~3-5 Numista pages in a row through Chrome MCP, that's no longer ad-hoc: stop and switch to API (or ask the user about the quota).
- **IKMK Berlin** (`ikmk.smb.museum`): `/object?id={id}&download=json_ext` returns full record. Bulk scraping via browser console on the origin domain bypasses CORS.
- **Bruun PDF** (Stack's Bowers Zürich 14-15 March 2025, Part II): the gold standard reference for Gottorp/Schleswig coinage. 356 pages. `danskmoent.dk` hosts the PDF.
- **CoinVarieties, MGM Münzlexikon, Bobzin, danskmoent.dk**: supplementary academic sources.
- **Offline (paper only)**: Lange 1908/12, Sieg-Møntkatalog 2018, Storgaard 2001 — cited by Bruun/Numista, rarely accessible digitally.

## Project audit tooling

Four scripts cover the project's mechanical-quality checks. Use them at session start (`audit_health.py`), at session end (`audit_prose.py` / `audit_i18n.py`), and continuously via the pre-commit hook.

- **`scripts/audit_health.py`** — one-shot project-health dashboard with 9 sections (build / data completeness / per-location coin count / Hede seed state / cache freshness / prose lint / cross-lang i18n / TODOs / git). Run `.venv/bin/python scripts/audit_health.py --fast` for a ~5 s «morning briefing» before starting multi-step work; drop `--fast` for the full build-validation pass. `--json` for machine-readable; `--section A,B,C` to slice.
- **`scripts/audit_prose.py`** — single-language linter for CLAUDE.md §0a / §0z / §2a / §2 / §0b violations across `data/**/*.yml` rendered-prose surfaces. `--rule '§N'` / `--language X` / `--location <NAME>` / `--staged` filters; `--json` output.
- **`scripts/audit_i18n.py`** — cross-language consistency detector for DE/EN/UK triples. Catches missing translations, citation-count mismatches, catalog-ref divergences, length-ratio extremes, and the Müntzfuß-name-translation trap.
- **`.githooks/pre-commit`** — runs `build.py --validate-only` (hard block on failure) + `audit_prose.py --staged` + `audit_i18n.py` (advisory) on every commit. **Install once per clone via `./scripts/install_hooks.sh`** — sets `git config core.hooksPath .githooks`. Bypass per-commit with `git commit --no-verify`. See `.githooks/README.md` for the «advisory now, block later» promotion path post §W / §X cleanups.

## Tool fallback chain — never stop on first failure

When one tool returns 403/blocked/empty, **escalate to the next tier** rather than giving up. Do not report «source X is blocked, can't verify» until you have tried the entire chain. The user has explicitly asked Claude to remember this and use the next tool when one fails.

**For fetching public web content (preferred order — cheapest first):**

1. **WebSearch** — for finding URLs and broad topical hits. Cheap, fast, no rate limits in practice. Good for «does X exist» / «what's the URL of Y».
2. **WebFetch** (Anthropic-built) — single URL → small-model summary. Good for short pages with a focused question. Often blocked by aggressive bot defences (Numista returns 403, NGC returns 403).
3. **Apify rag-web-browser** (`mcp__Apify__apify--rag-web-browser`) — Google search results + targeted page scrape. Bypasses some 403s by fetching through Apify infra. Numista *sometimes* works here, often returns 403 too. Useful for getting Markdown of a single known URL even when WebFetch fails.
4. **Chrome MCP** (`mcp__Claude_in_Chrome__*`) — real Chrome browser via the user's extension. Bypasses **all** bot defences because it's an actual logged-in browser session on the user's machine. Heaviest tool (real browser, batched actions, screenshots) — use last, but never forget it exists.
5. **Ask the user** — if all four tiers fail, ask the user to paste the page HTML / Markdown / a screenshot directly into chat. Do not silently abandon the verification. Phrase it precisely: «`<source-name>` page `<URL>` still won't load through any tool I have. Could you open the page in your browser and paste the relevant section here?»

**For PDF content** (Bruun Part II, Wilcke I/II, NNUM articles, danskmoent.dk PDFs):

Use the **pdf-viewer MCP** (`mcp__pdf-viewer__display_pdf` to open, then `mcp__pdf-viewer__interact` to navigate / search / get_text / get_screenshot). Accepts both local file paths and HTTPS URLs. Most efficient for: searching by lot number across a 356-page Bruun catalogue, extracting Hede tables, getting a specific page screenshot for cross-reference. If the PDF tool is unavailable in this session, fall back to: WebFetch on a direct PDF URL → ask the user to provide the relevant page text.

**Pattern for browser automation via Chrome MCP:** always batch actions with `browser_batch` (the runtime gives a system-reminder if you don't). Sequence: `list_connected_browsers` → `select_browser` → `tabs_context_mcp(createIfEmpty: true)` → then a single `browser_batch` with `[navigate, get_page_text]` per URL. For multi-page comparisons, one `browser_batch` per URL keeps the round trip count low. Per-source access policies (some sites have site-specific rules — e.g. Numista catalogue pages are OK to open via Chrome MCP for ad-hoc verification but bulk extraction is API-only; ucoin.net catalogue pages are OK with low-volume + attribution but user-pages are not) live in the «Tools and resources» section above and in `docs/SOURCES.md`; defer to those before invoking Chrome MCP for any specific source.

**Project-context note for access decisions:** this is a **non-commercial scholarly numismatic register** — that classification matters when evaluating whether a source's ToS / scraping framework permits our use. Most «is scraping legal» analyses distinguish commercial scraping (resale, ad-monetised replication, competitive intelligence) from non-commercial research scraping (academic / educational, with attribution, low volume); we sit firmly in the second category. When weighing a source's access policy, default-assume our use is on the more-permitted side of that line, and call it out explicitly in source notes (`docs/SOURCES.md`) when the source's framework hinges on the distinction.

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
> (a) Обробити лише 10 пріоритетних KM# і пропустити решту
> (b) Витратити квоту і прийняти ~140 запитів
> (c) Відкласти до наступного reset-у квоти
> Як вирішиш?»

**Never silently burn the quota.** Even if the script is technically correct and the data would be useful, the user needs to make the budget call. Cached requests in `scripts/cache/numista/<nid>.json` are free to re-read — only LIVE API calls count. So always check the cache first, and only ask permission for the new fetches.

The same principle applies to any other paid/quota'd resource you might integrate later (e.g. authenticated APIs, paid scraping services) — but those have their own scope and timeline; this specific rule is May-2026-bound.
