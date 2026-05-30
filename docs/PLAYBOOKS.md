# Playbooks — recurrent procedures

> **Purpose.** Step-by-step procedures for tasks that recur across
> sessions. CLAUDE.md holds **rules** (immutable principles, project
> conventions, anti-patterns). This file holds **procedures** (how
> to actually do X).
>
> The two split is intentional:
>
> - When a session asks «what's forbidden / what's required?», the
>   answer lives in `CLAUDE.md`.
> - When a session asks «how do I add a Bruun lot to an existing
>   coin?» or «how do I run a Hede dedup case?», the answer lives
>   here.
>
> Each playbook is self-contained: rules from `CLAUDE.md` that bear on
> the procedure are reproduced inline with a section pointer, so the
> reader doesn't need to flip back and forth. Quirks already
> diagnosed live in `docs/SOURCES.md` §13; playbooks reference those
> by entry.
>
> **When to add a new playbook.** When the same multi-step sequence
> recurs in a third session and you find yourself re-reconstructing
> it each time. Aim for procedural depth, not exhaustiveness — the
> playbook should be executable cold, but doesn't need to anticipate
> every edge case.
>
> **PB-N numbering is stable.** Insertions append at the end (next
> free number); never renumber.

---

## PB-1. Per-case Hede dedup merge

**When to use.** A Hede seed entry shares a Krause# (or potentially
shares one) with a curated entry; we need to decide whether they're
the same physical coin and, if so, fold them into one record per the
«one Krause KM = one entry» Pattern B.

**Prerequisites.**

- The 46-case dedup list under `scripts/oneoff/audit_seed_survivors.py`
  (regenerable on demand).
- The seed file `data/seed/hede/<location>.yml`.
- The curated location yaml `data/locations/<location>.yml`.
- `scripts/cache/hede/c{ruler}h{N}.json` for the Hede page in question
  (parsed Hede source-of-truth).

**Mandatory user-interaction discipline (CLAUDE.md «Auto mode»
exception).** User directive 2026-05-12: «без автоматичних батчів,
кожен кейс розглянь окремо, задавай питання». Do NOT batch multiple
cases per turn; do NOT auto-execute a merge without explicit per-
case user verdict.

**Steps.**

1. **Identify the candidates.** Find:
   - The seed entries (e.g. `dk-hede-c4h79a`, `dk-hede-c4h79b`,
     `dk-hede-c4h79c`, `dk-hede-c4h79d` for case 9).
   - The curated entries that might collide (search by KM, year, ruler,
     denomination — the seed's `catalog.hede` is your starting point).

2. **Gather all sources up front.** Per user directive 2026-05-12:
   «дай мені посилання на хеде 115A B C D я перевірю». Surface them
   ALL in one chat message before proposing the merge — links to:
   - `https://www.danskmoent.dk/chr/c{vol}{n}.htm` (Hede page; the
     spec card + sub-letter description + Zincksamlingen specimen
     list).
   - `https://en.numista.com/{N}` for each Numista entry on the
     candidate coins.
   - `https://en.ucoin.net/coin/<slug>/?tid={N}` for each ucoin tid.
   - Bruun PDF page references when applicable (per the §1.3 page-map
     in `docs/SOURCES.md`).
   - Cached Hede JSON: `cat scripts/cache/hede/c{vol}{n}.json` reveals
     the parsed `by_letter` structure + `description` + `specs.default`
     + `eksemplarer.Zincksamlingen` lists.

3. **Write the для / проти merge analysis.** Both sides explicit:
   - **Для merge:** shared spec card (one Bruttovægt / Finhed /
     Finvægt for all sub-letters); identical metal + ruler + mint +
     fraction; year ranges overlap or cover the same period;
     iconography description (`Forside: …`, `bagside: …`) matches
     across sub-letters; Krause already lumps them under one KM#.
   - **Проти merge:** different metal (gold off-strike vs silver
     mother coin — see SOURCES.md §13.4 for the Hede c4h47 trap);
     weight differs > 2× (likely different denominations sharing a
     coincidence Hede# across Krause volumes — see SOURCES.md §13.6);
     fineness differs > 2 % (likely different sub-issues at a debasement
     edge); year-span mismatch (different Hede sub-letter covers a
     different reign window than the candidate curated entry).
   - **Open questions.** State explicitly what's NOT verified
     (e.g. «Numista «Bust type I» = Hede 79A + 79B mapping is year-
     span-match only, not direct obverse-design verification»). Per
     CLAUDE.md §0b: hypothesis vs. fact — don't dress assumptions
     as conclusions.

4. **Wait for user verdict.** User says «це одна монета, мердж» or
   «це дві різні», or asks for more sources. Never proceed without
   the verdict.

5. **Execute the merge.** Typical changes to the curated entry:
   - Add `catalog.hede` (list form when folding sub-letters):
     ```yaml
     catalog:
       km: '16.1'
       hede:
         - 79A
         - 79B
       hede_volume: c4h
       sieg:
         - '38.1'
         - '38.2'
     ```
   - Update `year_label`, `year_first`, `year_last`, `year_ranges`
     to the union (use the wider-range sub-letter as the superset).
   - Per CLAUDE.md §9a multi-specimen preservation: convert scalar
     `weight_rough_g` / `fineness` to multi-source list with one
     entry per attestation:
     ```yaml
     weight_rough_g:
       - value: 2.088
         source: Hede c4h79 (danskmoent.dk)
       - value: 1.78
         source: ucoin tid 163008
     fineness:
       - value: 0.296
         source: Hede c4h79 (danskmoent.dk)
       - value: 0.298
         source: ucoin
     ```
   - Rewrite the `note` (DE/EN/UK) to mention the sub-variant folding
     and explain any retained divergences (Soll vs specimen, mintmark
     differences). Per CLAUDE.md §0z: write for the role-3 reader
     (numismatist), not for project-meta.
   - Ensure `mint_verified: true` if Hede page attests the mint
     (which it does for canonical c{vol}h{N} pages).

6. **Add Hede source to `sources[]`** with attribution:
   ```yaml
   sources:
     - type: literature
       url: https://www.danskmoent.dk/chr/c4h79.htm
       ref: Hede c4h79 (danskmoent.dk) — Soll und Mzm.-Untervarianten 79A/B
     - type: ucoin
       url: https://en.ucoin.net/coin/denmark-2-skilling-1603-1613/?tid=163008
       ref: ucoin tid 163008 — Specimen-Werte
   ```

7. **Rename the curated id if needed.** Convention for KM-numbered
   entries: `km-{N}-{ruler-abbrev}-{year}` (e.g. `km-16-1-chr-iv-1603`).
   For sub-numbered (16.1 / 16.2): `km-16-1-…` / `km-16-2-…`. When
   the prior id was a `dk-tid-NNNNN`-style placeholder, switch to
   the canonical KM-form on merge.

8. **Verify auto-suppress fires.** Run the build and read the seed-
   merge summary:
   ```
   ⚙  denmark: suppressed N hede seed coin(s) covered by curated Hede refs
   ```
   The N should jump by the number of seed entries folded (e.g.
   case 9 yielded +4 = 191 → 195). If a seed entry stayed visible
   on the rendered page, the `catalog.hede` list isn't picking it
   up — recheck the spelling (`79A` vs `79a` vs `'79A'`) and the
   `hede_volume` value.

9. **Build smoke check.** `python scripts/build.py --location <loc>`
   should pass; the rendered page should show the merged entry with
   tooltip(s) for cross-register catalog refs (per CLAUDE.md §9
   caveat on KM-register volumes).

10. **Commit per the CLAUDE.md cadence rule.** Atomic commit, message
    follows the case-9 template (`data(<loc>): case N — fold c{vol}h{N}[A-D]
    into KM-{N} + KM-{N+1}`). Include the для/проти summary in the
    commit body and the seed-suppress count delta (`191→195 (+4)`).
    Do NOT push without explicit user permission.

11. **Update `docs/handoff.md`** if the case closed reveals next-case
    pointer, OR if a pending verification opened during the work.

**Success criteria.**

- Build clean.
- Auto-suppress count rises by the expected delta.
- Multi-source attestations preserved (no `(?)` markers introduced
  on previously source-attested fields per CLAUDE.md §4 verified-
  wins-over-unverified).
- The user's per-case verdict is honoured exactly (merge or split
  as instructed — never silently expand scope).

**Common failures + recovery.**

- *Suppress doesn't fire after merge.* Check `catalog.hede` is a list
  (not a `\n`-joined string), `hede_volume` matches the seed entry's
  prefix (`c4h` not `c4`), and that the seed's id matches
  `_hede_seed_id(volume, num)` output. See `_merge_seeds_into_raw` in
  `scripts/build.py`.
- *Build error after rename.* `id` changes might be referenced from
  `verification_note` cross-references; grep for the old id.
- *Year-range overshoot.* Per CLAUDE.md §4 «Source years are
  immutable»: don't clip a sub-letter's documented years to a phase
  window — extend the phase or split the entry. Never silently
  shorten Hede-documented year ranges to make placement neat.

**Related rules.** CLAUDE.md §4 (verified-wins, source years
immutable), §9 (caveat «same KM# across catalogues»), §9a (multi-
specimen merge preservation).

**Related quirks.** SOURCES.md §13.4 (Hede sub-letter convention,
silver-spec-on-gold-strike trap), §13.6 (Krause register volumes
KM# inflation).

---

## PB-2. ucoin Composition harvest session

**When to use.** Resuming the ucoin Composition harvest from `TODO §M`,
or adding ucoin-attested metal / fineness / weight to a batch of
coins whose `metal_verified` is `false`.

**Prerequisites.**

- Chrome MCP available + browser logged into ucoin (any normal
  session — no ucoin-side authentication required, but Cloudflare
  fingerprint matters).
- ucoin NOT currently under Cloudflare bot-protection (check by
  navigating to one ucoin page; if the title shows «Just a moment…»,
  Cloudflare is gating — wait ~24 h or pass the challenge manually).
- `scripts/cache/ucoin/_composition.json` writable; `.venv` python
  with `ruamel.yaml`.

**Operational pacing (measured 2026-05-13 — see SOURCES.md §13.2).**

| Pacing | Safe session size | When to use |
|---|---|---|
| 2.5 s | ~30 fetches | desperate / not recommended |
| 10 s | ~45 fetches | balanced |
| **20 s** | **~40-45 fetches** | **default; recommended** |

The ceiling is ~50 cumulative fetches per session-cookie regardless
of pacing. Slower pacing extends time-in-window marginally. **Never
chain > 45 fetches in a single cookie-cycle.** Once tripped, every
subsequent request returns a wrong-tid redirect page until cookies
are cleared.

**Steps.**

1. **Inventory uncached + unverified candidates.** Python helper:
   ```python
   import yaml, re, json
   from pathlib import Path
   COMP = json.load(open('scripts/cache/ucoin/_composition.json'))
   remaining = []
   for p in sorted(Path('data/locations').glob('*.yml')):
       if p.stem.endswith('-references'): continue
       doc = yaml.safe_load(p.read_text()) or {}
       for c in doc.get('coins') or []:
           if not isinstance(c, dict) or c.get('metal_verified'): continue
           for s in c.get('sources') or []:
               if isinstance(s, dict) and s.get('type') == 'ucoin':
                   m = re.search(r'tid=(\d+)', s.get('url') or '')
                   if m and m.group(1) not in COMP:
                       remaining.append([m.group(1), s['url']])
                   break
   print(json.dumps([remaining[0:2], remaining[2:4], remaining[4:6]]))
   ```
   Pull batches of 6 (3 × 2-coin sub-batches per `browser_batch`).

2. **Reset session counter.** Fresh cookie session = fresh counter:
   ```javascript
   localStorage.uc_req_total = '0';
   localStorage.uc_results = '[]';
   ```

3. **Launch fetcher.** One `browser_batch` with 3 sequential
   `javascript_tool` calls, each running 2 coins × 20 s delay
   (= ~40 s per JS call, safely under the 45 s CDP timeout). The
   template lives in
   `scripts/maintenance/ucoin_fetch_composition.py::MEGA_FETCH_TEMPLATE`
   — or use this minimal inline form:
   ```javascript
   (async () => {
     const todo = [...]; // [[tid, url], ...]
     const D = 20000;
     const L = {Composition:'c','Weight (g)':'w','Diameter (mm)':'d'};
     const isU = v => !v || /Unknown/i.test(v);
     const out = JSON.parse(localStorage.uc_results || '[]');
     let rc = parseInt(localStorage.uc_req_total || '0');
     for (const [tid, url] of todo) {
       await new Promise(r => setTimeout(r, D));
       const r = await fetch(url, {credentials: 'same-origin'});
       const html = await r.text();
       const doc = new DOMParser().parseFromString(html, 'text/html');
       const canon = doc.querySelector('link[rel=canonical]');
       let cT = null;
       if (canon) { const m = canon.href.match(/[?&]tid=(\d+)/); if (m) cT = m[1]; }
       rc++;
       if (!r.ok) { out.push({tid, err: 'HTTP ' + r.status, req: rc}); continue; }
       if (cT && cT !== String(tid)) { out.push({tid, err: 'slug_mismatch_' + cT, req: rc}); continue; }
       const rec = {tid, req: rc};
       for (const tr of doc.querySelectorAll('tr')) {
         const th = tr.querySelector('th'); const td = tr.querySelector('td');
         if (!th || !td) continue;
         const k = th.textContent.trim();
         if (k in L) { const v = td.textContent.trim(); if (!isU(v)) rec[L[k]] = v; }
       }
       out.push(rec);
     }
     localStorage.uc_req_total = String(rc);
     localStorage.uc_results = JSON.stringify(out);
   })()
   ```

4. **Read results.** `localStorage.uc_results` after the batch. Chrome
   MCP truncates output at ~1000 chars; for larger payloads read in
   slices: `localStorage.uc_results.slice(0, 800)`, `.slice(800)`, etc.

5. **Watch for rate-limit signal.** Any `err: 'slug_mismatch_<other_tid>'`
   is the rate-limit redirect (NOT a real URL breakage — see
   SOURCES.md §13.2). 3 consecutive of these = rate-limit tripped.
   STOP, mark them for retry post-cookie-clear, ask user to clear
   cookies before resuming.

6. **Ingest successful fetches.**
   ```bash
   .venv/bin/python scripts/maintenance/ucoin_fetch_composition.py ingest <<'EOF'
   [{"tid":"X","c":"Silver 0.875","w":"...","d":"..."}, ...]
   EOF
   ```

7. **Run the backfill.**
   ```bash
   .venv/bin/python scripts/maintenance/ucoin_backfill_metal.py
   ```
   Watch for the four-bucket summary: `metal_set`, `metal_confirmed`,
   `metal_replaced`, `metal_disagree_with_source`. The first three are
   automatic; the last needs manual review (verified entries that
   disagree with ucoin's source-attested reading — per CLAUDE.md §4
   verified-wins, those flag for inspection, NOT auto-flip).

8. **Build smoke + commit.** Per CLAUDE.md cadence rule. The harvest
   commit goes in `scripts/cache/` submodule first (`harvest(ucoin):
   …`), then the main-repo commit bumps the submodule pointer + adds
   the data/locations changes (`data: ucoin Composition backfill — N
   fields populated`).

9. **At rate-limit (when it happens).** Mark all `err: 'slug_mismatch_…'`
   entries via the ingest command (it auto-flags them `status_404`
   for skip-on-next-run). Ask the user to clear `en.ucoin.net` cookies.
   On next session, those tids re-enter the queue automatically — the
   sidecar has only their error marker, which doesn't count as
   «cached».

**Success criteria.**

- New entries in `_composition.json` with `composition` + measurements.
- Backfill applied N field updates; build clean.
- Zero `metal_disagree_with_source` entries (or each one investigated
  case-by-case).

**Common failures + recovery.**

- *Chrome MCP disconnects mid-batch.* The JS continues running but
  Chrome MCP can't read back. The subsequent reconnect-and-retry
  often double-fetches the same tids (counts twice against the ucoin
  server-side counter). Mitigation: read `localStorage.uc_req_total`
  carefully after each batch — if the counter is higher than expected,
  you've taken double-hits and should pause sooner.
- *Cloudflare challenge.* Hard 403 + «Just a moment…» on every request.
  Cookie clear DOES NOT help (likely makes it worse — wipes the
  `cf_clearance` token). Stop, document in TODO §M, wait 24 h.
- *Composition string the parser can't map.* `map_composition()` in
  `ucoin_backfill_metal.py` handles the standard «Silver 0.X», «Gold
  0.X», «Silver (Billon) 0.X», «Bronze / Copper-nickel / Cupronickel»
  patterns. New compositions show up in `unknown_composition: [...]`
  — add a case to `map_composition()` and re-run.

**Related rules.** CLAUDE.md §4 (verified-wins), §5 «Tool fallback
chain» (Chrome MCP is the right tier for ucoin).

**Related quirks.** SOURCES.md §13.2 (full ucoin rate-limit + Cloudflare
log).

---

## PB-3. Web-research citation cycle

**When to use.** A fact you're about to write into rendered prose
(coin note, fuss description, location preamble, landing-page text,
glossary entry) comes from a web lookup — Wikipedia / danskmoent.dk /
Numista / Wikisource / archive.org / institutional pages / Wilcke
HTML.

**Hard rule (CLAUDE.md §5, repeated for emphasis).** Both steps in
the SAME change while the source is open in your context:

1. **Add a bibliography entry** in the appropriate references file.
2. **Add the inline `<sup>` citation** in the prose.

Skipping either step silently regresses §0 (no invention).

**Steps.**

1. **Identify the destination references file:**
   - Per-location prose → `data/locations/<loc>-references.yml`.
   - Landing-page Müntzfüße overview → `data/shared/german_fuesse-references.yml`.
   - Glossary / docs / cross-cutting → cite inline in the doc.

2. **Pick the next free `ref{N}` id.** Grep the existing ids,
   append at next number — never renumber existing refs (every
   inline `<sup>[N]</sup>` across the project resolves by number).

3. **Build the ref body per CLAUDE.md §5a:**
   ```yaml
   - id: ref{N}
     content:
       de: |
         <b>Author surname, First name</b>: <i>Title</i> (Publisher, Year) —
         <a href="https://example.com/url" target="_blank">example.com/url</a>.
         Optional one-line scope note (≤ 140 chars, no quotes longer than
         ~25 words, no «proves X», no project-meta).
       en: …
       uk: …
   ```

4. **Long-form sources MUST carry a concrete page hint** (CLAUDE.md
   §5a «Mandatory page hints»). For any work ≥ 10 pages — PDF book,
   monograph, auction catalogue, periodical, multi-volume Konversations-
   lexikon, scanned ordinance gazette — the scope note MUST include a
   literal page reference. Accepted forms:
   - `«verbatim quote» (S. 14)` — short quote + page, canonical.
   - `Band 11, S. 890–891` — multi-volume work + volume + pages.
   - `Kap. 4, S. 123–125` — chapter-based work.
   - `§ 5, S. 12` — legal / ordinance texts.

   **Forbidden:** «ca. S. 14–25», «im ersten Kapitel», «passim»,
   «throughout», «зокрема в книзі». Approximate ranges are invalid.

   Wikisource exception: when the page transcribes per-page from a
   print original, cite the print pagination (`MKL 1888, Band 11, S.
   890–891`). Pure wiki-only articles use a section anchor.

5. **Locate the page hint when not already known.** Tools (cheapest
   first):
   - `pypdf` against a locally-downloaded PDF (curl-to-/tmp pattern,
     see SOURCES.md §1.3 for the Bruun-PDF example).
   - `pdftotext` for OCR-quality PDFs.
   - `WebFetch` on archive.org's `*_djvu.txt` URL for archive-hosted
     books (full-text search).
   - `WebSearch` for «<verbatim phrase> + book title» often surfaces
     a Google Books snippet with page number.
   - `mcp__pdf-viewer__display_pdf` + `interact` for short PDFs
     (does NOT work on Bruun PDFs > 29 MB — see SOURCES.md §13.3).
   - As a last resort, ask the user to verify a page in paper.

6. **Add the inline `<sup>` citation** at the END of the sentence the
   ref backs:
   ```html
   <sup><a href="#ref{N}">[{N}]</a></sup>
   ```
   Stack multiple refs when several sources back one sentence:
   `<sup><a href="#ref10">[10]</a><a href="#ref11">[11]</a></sup>`.

7. **Verify the diff before committing.** The new `ref{N}` should
   appear at least TWICE in the diff — once in the references file
   defining the entry, once or more in the prose as
   `<sup><a href="#ref{N}">[{N}]</a></sup>` inline. If it appears only
   in the references file, the inline-cite step was skipped → go back
   and add it. If the diff has prose changes from web research but no
   new `ref{N}`, the bibliography step was skipped → go back.

**Success criteria.**

- New `ref{N}` exists in three languages (DE/EN/UK) — EN+UK can be
  added incrementally if DE is the immediate work, but the slot
  must be present.
- Long-form source has a concrete page hint.
- Inline `<sup>` cite matches the prose claim.

**Common failures + recovery.**

- *Citation refers to source X but quote isn't actually in source X.*
  Run the verbatim-search step (pypdf / WebFetch / archive djvu)
  BEFORE accepting the ref. The Bruun PDFs case (SOURCES.md §13.3:
  Plakat-1782 verbatim NOT in any Bruun PDF) is a real precedent —
  don't repeat it.
- *Multi-source bundle in one ref.* CLAUDE.md §5a forbids bundling
  (e.g. «Stack's Bowers Part I + II + III + IV» under one `ref{N}`).
  Split into atomic refs, append at end of file (next free N+1,
  N+2…), update inline cite to the stack form.
- *Renumbering temptation.* Never renumber existing ids — they're
  load-bearing across the project. Append at end, period.
- *Cross-language drift.* If you only fill DE, leave EN and UK keys
  as empty strings (matching the existing convention for unfilled
  translations) — don't omit the keys, or schema validation
  warnings appear.

**Related rules.** CLAUDE.md §0 (no invention), §5 (web-sourced
facts → bibliography + inline cite), §5a (ref style + page hints).

**Related quirks.** SOURCES.md §13.3 (Bruun-PDF citation traps).

---

## PB-4. Müntzfuß disambiguation for an ambiguous coin

**When to use.** A new coin has documented year(s) in a window where
two or more Müntzfüße were in force, and the sources don't directly
tell us which Fuß it belongs to. CLAUDE.md §8a defines the filtering
pipeline; this playbook walks the execution.

**Prerequisites.**

- The coin's documented `metal` + `nominal` + `year_first` /
  `year_last` + `weight_rough_g` (specimen) + `fineness` if attested.
- The candidate Fuß set: every Fuß whose period covers the coin's
  year-range, by metal class (silver / gold / bimetal).
- `data/shared/fuesse.yml` for Soll-values per fraction.

**Steps (matches CLAUDE.md §8a filtering pipeline 1-6).**

1. **Metal mismatch — drop candidates incompatible with the coin's
   metal.** A gold coin cannot belong to a silver-only Fuß; a silver
   coin cannot belong to `reichsdukatenfuss`. Bimetal pairings
   (Pistolenfuß-paired silver, Vereinsgoldmünze-paired Vereinsmüntzfuß-
   silver-tier) are explicit pairings — check the relevant Fuß
   definition.

2. **Denomination-name mismatch.** «Rigsbankskilling» is character-
   istic of 18½-Thaler-Fuß; «Speciedaler» of 9¼ and not 9; «Vereins-
   thaler» exclusively of Vereinsmüntzfuß. Soft signal — denomination
   drift across Füße does happen — but a clean nominal-name match
   still narrows the set quickly.

3. **Feingewicht Δ-from-Soll comparison (when fineness is specimen-
   attested).** Compute `Δ = (specimen_Feingewicht − Soll_Feingewicht)
   / Soll_Feingewicht` for each candidate. Coins typically run
   slightly under (specimen variance + wear); a small fraction run
   slightly over (rarely beyond +2 %, with rare exceptions for tariff
   coins or high-quality cabinet specimens). Smallest |Δ| within
   roughly ±2 % is the placement.

4. **Bruttogewicht pattern (when fineness is unknown).** Without
   specimen-attested fineness, Feingewicht can't be computed directly.
   Compare the raw weight against existing same-nominal entries
   already placed under each candidate Fuß — does the specimen
   cluster with one Fuß's typical band and not the other's? Use as
   the placement signal when the pattern is clean.

5. **Fineness hint (when known but step 3 wasn't decisive).** Each
   Fuß has a characteristic fineness signature for a given metal
   (e.g. .875 silver = 9¼-Thaler-Fuß; .896 gold = Pistolenfuß; .986
   gold = Reichsdukatenfuß). Supporting signal alongside steps 3-4,
   never alone — debasement and specimen-tolerance can disrupt the
   signature.

6. **Escalate to user if 1-5 don't pick a unique candidate.** Surface
   the data — coin id, year, metal, nominal, Bruttogewicht, fineness
   (if known), surviving candidate Füße with their Soll-values +
   computed Δ — and wait for the placement decision. Do not silently
   assign per CLAUDE.md §0.

**Scheidemünze residual case.** When the specimen's Feingewicht (or
Bruttogewicht-pattern at known typical fineness) is dramatically
below every candidate's Soll for a full-Kurant of that fraction
(typically > 20 % under), the coin is not a full-Kurant of any
candidate — it's a Scheidemünze per CLAUDE.md §6. Place under the
*parent* full-Kurant Fuß of the period (the established standard,
not a contender new Fuß) and mark `kind: scheide`.

**Success criteria.**

- A unique Fuß identified, OR a documented escalation to user.
- The coin's `fuss:` value matches the chosen Fuß.
- The build's computed Δ for the coin falls within ±2 % of Soll
  (or the prose acknowledges the Scheidemünze case).

**Related rules.** CLAUDE.md §6 (Kurant vs Scheide), §7 (Fuß global,
phase local), §8 (placement checklist), §8a (this filtering pipeline).

---

## PB-5. Adding a Bruun specimen to an existing coin

**When to use.** A coin entry already exists with at least one
`weight_rough_g` reading; a Bruun lot of the same KM# is being
imported (per §9a multi-specimen merge).

**Prerequisites.**

- Bruun part PDF locally cached (`/tmp/bruun_part{1,2,3,4}.pdf`
  via curl-to-/tmp), OR the parsed JSON
  `scripts/cache/bruun/lots/part{1,2,3,4}.json`.
- The coin's curated entry id and its `catalog.km` value.
- The Bruun lot's `lot_no`, `page`, and (preferably) `body_excerpt`.

**Steps.**

1. **Verify the specimen actually matches the coin.** Cross-check:
   - KM# (Bruun's printed KM vs ours — see SOURCES.md §13.3 cataloguer
     KM-copy mistakes).
   - Hede# (independent confirmation; Bruun usually prints Hede
     accurately).
   - Year (Bruun's printed year vs coin's `year_label`).
   - Mintmaster initials (Bruun gives full name, ours stores
     initials only).
   - **Composition (gold vs silver).** Pre-check per CLAUDE.md anti-
     pattern #6: «proposing a coin-merge without checking metal/
     composition first». Bruun gives `body_excerpt` with «Gold» /
     «Silver» in the first line.

2. **Extract the specimen data:**
   - `weight_g` from Bruun's lot dict (or parsed from body excerpt).
   - `grade` (NGC grade, if present).
   - `mintmaster` (full name from body excerpt).
   - Lot context (year of auction, lot sequence in the part).

3. **Append to `weight_rough_g[]`** per CLAUDE.md §9a:
   ```yaml
   weight_rough_g:
     - value: 5.197       # existing entry
       source: Hede 47 / danskmoent.dk
     - value: 5.20        # new — append
       source: Bruun Part III, lot 11270, p. 139
   ```
   Do NOT replace existing entries; append. Each `(value, source)`
   tuple represents one independent attestation.

4. **Add the Bruun-citation primacy fields** when this is the best-
   conditioned specimen (or the earliest, if grade-tied):
   ```yaml
   catalog:
     ...
     bruun_collection_id: '7341'
     bruun_part: III
     bruun_lot_no: 11270
     bruun_page: 139
   ```
   When alternative specimens exist, the lesser ones travel in
   `sources[]` only (with full part + lot + page in the `ref` text).

5. **Add the source to `sources[]`:**
   ```yaml
   sources:
     ...
     - type: auction
       url: https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Oct2025_LE_Bruun_Coins_Part_III.pdf
       ref: Bruun Part III, lot 11270, p. 139
   ```

6. **Per-grade thinning (per CLAUDE.md §9a «Intra-sub-variant
   thinning»).** If the entry now has ≥ 5 `weight_rough_g` entries
   from a single resource sharing the same sub-variant, AND fineness
   is uniform, thin to `[min, len//2, max]` — three retained per the
   convention. The maintenance script
   `scripts/maintenance/thin_intra_subvariant_specimens.py` automates
   this.

7. **Same-weight duplicates.** If the new Bruun weight equals an
   existing entry from the same source/sub-variant at display
   precision (2 decimals), keep only one — the entry whose underlying
   record carries the most populated fields stays. See CLAUDE.md §9a
   «Same-weight duplicate» degenerate-thin sub-rule.

8. **Build smoke + commit.** Commit message: `data(<loc>): add Bruun
   specimen for km-{N} ({ruler}-{year})`. Body: cite the lot + page,
   what specimen data was added.

**Success criteria.**

- Coin entry now lists the Bruun specimen; no existing data overwritten.
- `bruun_collection_id` (etc.) reflects the dominant specimen (best
  grade / earliest year on ties).
- Thinning rule respected (≤ 3 entries per single-resource same-
  sub-variant bucket if uniform fineness; or all entries preserved
  if fineness varies).

**Related rules.** CLAUDE.md §9 (inclusion criteria + KM-cross-volume
caveat), §9a (multi-specimen merge + thinning).

**Related quirks.** SOURCES.md §13.3 (Bruun-cataloguer KM-copy
mistakes, Plakat-1782 not in Bruun, pdf-viewer-MCP unusable).

---

## PB-6. Adding a new location

**When to use.** Bringing a new city / territory into the project
(e.g. adding `oldenburg.yml` to the existing 12-location set). Rare
but high-impact.

**Prerequisites.**

- A clear sense of which Müntzfüße applied (and when) — usually
  documented in CLAUDE.md «Prior work» reference HTML artefacts
  or in a `docs/<loc>.md` research note prepared earlier.
- The location's issuing entity (sovereign duchy / Hanseatic city /
  prince-bishopric) registered in `data/i18n/issuing_entities.yml`.
- The mint(s) used by this location registered in
  `data/shared/mints.yml`.

**Steps.**

1. **Create `data/locations/<loc>.yml`** with the location header:
   ```yaml
   id: <loc>
   name:
     de: …
     en: …
     uk: …
   km_register: DK | SH | NO | DE  # which Krause volume's numbering
                                    # is canonical for this page
   description:
     de: |
       <one-paragraph historical preamble, sourced via inline <sup>>
     en: |
       …
     uk: |
       …
   issuing_entities:
     - <entity_id from data/i18n/issuing_entities.yml>
   mints:
     - <mint_id from data/shared/mints.yml>
   phases:
     # see existing locations for shape
   coins: []   # will be populated from seed + manual curation
   ```

2. **Create the references file** `data/locations/<loc>-references.yml`:
   ```yaml
   heading:
     de: "Quellen · References"
     en: "References · Sources"
     uk: "Посилання · Джерела"

   entries:
     - id: ref1
       content:
         de: …
         en: …
         uk: …
   ```

3. **Verify the issuing-entity exists.** Open
   `data/i18n/issuing_entities.yml`; if the entity isn't there yet,
   add it with DE/EN/UK names + period bounds. New entities should
   match the historical entity-name convention (e.g. «Herzogtum
   Holstein-Glückstadt», not invented labels).

4. **Verify mints registry.** Open `data/shared/mints.yml`; add any
   new mint with DE/EN/UK names + active-period.

5. **Define phases.** Each Fuß × phase = one block of coins. Phases
   are LOCAL to the location (CLAUDE.md §7), even when the Fuß is
   global. Phase metadata: `start_year`, `end_year`, `description`
   (DE/EN/UK), `kind: phase`.

6. **Add first coin(s).** Either:
   - Manual: build the curated entries from sources directly
     (Bruun / Numista / ucoin / Hede), following CLAUDE.md §9
     inclusion criteria.
   - Seed-driven: if a Hede-seed for the location exists in
     `data/seed/hede/<loc>.yml`, the build's `_merge_seeds_into_raw`
     auto-populates them; curate the high-value entries to Pattern-B
     consolidated form per PB-1.

7. **Build smoke check.**
   ```bash
   python scripts/build.py --location <loc> --lang de
   python scripts/build.py --location <loc>           # all 3 langs
   python scripts/build.py                            # full site
   ```
   Open `site/<loc>/de/index.html` in browser for visual confirmation.

8. **Add to landing.** The landing page (`templates/landing.html.j2`)
   reads from `data/locations/`; verify the new location card
   renders. If it doesn't appear, check `data/i18n/ui.yml` for the
   location name slot.

9. **Update README + handoff.** A new location is worth a one-line
   handoff entry.

**Success criteria.**

- Full build clean (`python scripts/build.py`).
- New page renders in all 3 languages.
- Landing-page card present.
- At least one coin per Fuß × phase block (no empty phases).

**Common failures + recovery.**

- *Missing issuing-entity in registry.* Schema validation fails
  with «Unknown issuing_entity ID». Add to
  `data/i18n/issuing_entities.yml` first.
- *Schema rejects fields.* `Location` model in `scripts/lib/schema.py`
  is `extra="forbid"` — any unknown top-level key fails. Match the
  shape of an existing location yaml.
- *KM register collisions.* If a coin in this location appears in
  both a Denmark-volume and a SH-volume KM listing, use the
  `KMRef {value, register}` list form (per CLAUDE.md §9 caveat).

**Related rules.** CLAUDE.md §7 (Fuß global, phases local), §8
(placement checklist), §9 (inclusion criteria).

---

## PB-7. Cross-Krause-volume KM-collision handling

**When to use.** The same physical coin appears in two Krause volumes
(typically DK-volume + SH-volume for Glückstadt issues; can also be
DK-volume + NO-volume for double-monarchy issues 1814-).

**Concrete example (canonical).** Christian-IV 1640-48 Glückstadt
1-Søsling Lybsk:
- Krause-Denmark volume: KM-DK# 25
- Krause-Schleswig-Holstein volume: KM-SH# 87
- Hede# 178 (single page, sub-letters A + B for mintmark variants)
- Same physical coin, two Krause catalogue numbers.

**Steps.**

1. **Identify the dual-listing.** Numista usually has two records,
   one per Krause volume (different N# numbers). Both records may
   reference each other in the body («Krause: KM-25 / KM-87»). Hede
   typically lists ONE entry (sub-letters folded under one Hede#).

2. **Choose the page-owner location.** The coin lives ONE place in
   our project. Convention:
   - Glückstadt issues → `schleswig_holstein.yml` (Glückstadt was
     the Holstein-Dänish-administered mint, even though the issuer
     was the Danish crown).
   - Pure-Denmark issues → `denmark.yml`.
   - When ambiguous, the user decides per coin.

3. **Use the `KMRef` list form for `catalog.km`:**
   ```yaml
   catalog:
     km:
       - {value: '25', register: DK}
       - {value: '87', register: SH}
     hede:
       - 178A
       - 178B
     hede_volume: c4h
     numista: '199146'    # one of the two N# is the canonical lookup
   ```

4. **Set the page's `km_register`** in the location yaml header. For
   `schleswig_holstein.yml`, `km_register: SH` — that means a coin
   with `catalog.km: {value: '87', register: SH}` renders as bare
   «KM# 87» (matches page default), while `{value: '25', register: DK}`
   renders as qualified «KM-DK# 25» + tooltip (cross-register).

5. **Multi-source weight per §9a.** Both Numista records often have
   independent weight readings (sometimes inconsistent — see
   SOURCES.md §13.1 Numista 301740 0.49 g case). Preserve all:
   ```yaml
   weight_rough_g:
     - value: 0.704
       source: Hede c4h178 (Soll-Bruttovægt, shared by both sub-letters)
     - value: 0.76
       source: Numista 199146   # KM-DK# 25 record
     - value: 0.49
       source: Numista 301740   # KM-SH# 87 record — anomalous reading
     ...
   ```
   Per CLAUDE.md §0z (reader voice): if a reading is anomalous, the
   prose CAN mention «one specimen reading at 0.49 g is documented»;
   it MUST NOT say «this is a Numista user-edit error» (project-
   internal classification — not for role-3 reader). Document the
   diagnosis in `docs/SOURCES.md` §13 instead.

6. **Note prose acknowledging the dual-listing.** One sentence,
   reader-facing:
   > «Die selbe Münze erscheint in zwei Krause-Bänden: KM-DK# 25
   > (Denmark, Numista 199146) und KM-SH# 87 (Schleswig-Holstein,
   > Numista 301740).»

   Per CLAUDE.md §0a: factual, no project-meta («our card», «our
   model»), no editorial commentary on which Numista record is
   «right».

7. **Test the render.** Open the page in browser. The single coin
   row should show:
   - In the catalog column: the bare KM# for the page-register +
     the qualified KM-{other-register}# with tooltip explaining the
     cross-volume.
   - The Hede# list shows both sub-letters.
   - Tooltip text comes from `_KM_REGISTER_TOOLTIP` in `scripts/lib/
     compute.py` («Krause-Mishler — Denmark volume» / «… —
     Schleswig-Holstein volume»).

**Success criteria.**

- Single curated entry (NOT two).
- Both KM# refs visible on the rendered page with appropriate
  qualification.
- Multi-source weight preserved per §9a.

**Related rules.** CLAUDE.md §9 (caveat «same KM# across catalogues
is NOT automatically the same type»), §9a (multi-specimen merge).

**Related quirks.** SOURCES.md §13.6 (Krause register volumes KM#
inflation).

---

## PB-8. Session lifecycle

**When to use.** Every session — start and end.

**Session start.**

1. **Read CLAUDE.md.** Mandatory; cannot be skipped. It carries
   the immutable rules and project conventions.

2. **Read `docs/TODO.md`.** Open audit items the user has flagged.
   Note any §X TODOs whose topic touches today's planned work —
   surface them if you'll work near that territory.

3. **Read `docs/handoff.md`.** Short-term state: current focus,
   pending verifications awaiting user, local-commit state. The
   handoff tells you what's interrupted and what the user is
   probably about to ask about.

4. **Read `docs/SOURCES.md` §13 + §14.** Known-issues log + cache
   freshness snapshot. If a source-quirk is relevant to the day's
   work, you should recognise it before you stumble into it.

5. **Glance at `docs/DECISIONS.md` newest entries + the latest
   `docs/notes/YYYY-MM-DD.md`.** Recent rationale + recent context.
   The notes file matching yesterday's date (or the most recent
   project-work day) carries the analytical narrative behind any
   handoff threads that look puzzling.

6. **Optional: run `.venv/bin/python scripts/audit_health.py --fast`**
   for a one-shot project-health dashboard (build clean? cache fresh?
   prose / i18n hits? commits ahead origin?). Recommended when
   starting a multi-step task; skip for trivial one-off tweaks.

7. **Run `git status` + `git log --oneline -10`.** What's
   committed, what's pending push, what's modified-but-uncommitted.
   This reveals work-in-progress from the previous session.

8. **First-time-on-this-clone-only: `./scripts/install_hooks.sh`**
   to enable the pre-commit hook (build-validate + advisory
   prose/i18n lint). Idempotent; safe to re-run. Check via
   `git config --get core.hooksPath` — should print `.githooks`.

9. **Note auto-mode state.** If the session started under «Auto
   mode active», execute autonomously per the rule banner. If not,
   confirm with the user before non-trivial changes.

**Session end (final response).**

1. **Run the build.** `.venv/bin/python scripts/build.py` (or
   `--validate-only` for speed when no template/data changed). The
   build should be clean before declaring the session done.

2. **Atomic commits per CLAUDE.md cadence rule.** Group changes by
   logical task; conventional-prefix messages (`data:`, `template:`,
   `docs:`, `schema:`, `build:`, `fix:`). Commit messages in
   English regardless of chat language.

3. **Update `docs/handoff.md`** if any of:
   - Current focus changed.
   - A pending verification opened (waiting on user input).
   - A surface that was rebuilt deserves a one-liner for the next
     session.
   - Local commits got pushed (update «Local commit state» section).

4. **Add to `docs/SOURCES.md` §13** any new source quirk that cost
   > 15 min to figure out.

4a. **Append to `docs/notes/YYYY-MM-DD.md`** (today's daily note).
    Create the file if it doesn't exist for today's date. Capture:
    - the session's topic (one-line heading),
    - what happened (high-level prose, not commit-by-commit),
    - insights / observations that aren't strong enough for TODO /
      DECISIONS / §13 yet,
    - open threads at session end (forward-pointers),
    - references (commit SHAs, TODO §X added/closed, decisions
      logged, §13.Y additions, PB-N additions).

    The daily note is immutable once committed — the forward-
    pointing version of «what's pending?» lives in `handoff.md`;
    the immutable archive of «what was the reasoning?» lives in
    the dated note. See `docs/notes/README.md` for the convention
    + worked examples.

    If the session didn't touch any project-work (only chatted /
    explored / answered questions), no note needed. Empty notes
    are forbidden.

5. **Close completed TODOs.** Move from `## Open` to `## Done` with
   a closure note that summarises the work + cites the commit SHA.
   Match the existing template (see closed TODOs I, J, K, S in
   `docs/TODO.md`).

6. **Remind the user to push.** Never push autonomously. End with
   a one-liner: «N commits ready locally — `git push` when ready.»
   When the user replies «push» / «пуш» / equivalent, that's per-
   turn permission to push to origin/main.

**Success criteria.**

- Build clean.
- Working tree clean (everything committed).
- handoff.md reflects the current state.
- User knows how many commits await push.

**Related rules.** CLAUDE.md «Read this file first on every
session», «Preview lifecycle» (+ PB-11), «Commit cadence + push
permission».

---

## PB-9. Closing a TODO item

**When to use.** A multi-session TODO entry reaches a state where
no further action is needed (the audit is complete, the bug is
fixed, the design decision is made and implemented).

**Steps.**

1. **Locate the entry in `## Open`** in `docs/TODO.md`. Read its
   full body — the closure note will reference the original goals.

2. **Author the closure note.** Convention:
   - Title line stays the same with `*(opened YYYY-MM-DD, closed YYYY-MM-DD)*`.
   - First paragraph «**Surfaced.**» — restates the original
     problem (one sentence).
   - Body — explains the outcome: what was decided, what was
     implemented, the commits that landed it.
   - Final paragraph «**Closed via commit `<SHA>`.**» — for trace-
     ability.
   - Match the shape of existing closed TODOs I, J, K, S in `## Done`.

3. **Move the entry.** Cut from `## Open`, paste at the TOP of
   `## Done`. Reverse-chronological is convention.

4. **Update `docs/handoff.md`** if the closed TODO was listed in
   the «Open TODOs added this session» table — remove the row.

5. **Commit.** Message: `docs(todo): close §X — <one-line topic>`.

**Common failures + recovery.**

- *Partial closure.* If only PART of the TODO is done (the original
  audit covered N items, M are still pending), DON'T move to Done.
  Instead, update the entry's body in-place with progress + remaining
  scope, and add a date marker to the title:
  `*(opened YYYY-MM-DD, partial progress YYYY-MM-DD)*`. The TODO
  stays in `## Open`. (See TODO §M's «paused» history for a worked
  example.)

**Related rules.** CLAUDE.md «Commit messages MUST be in English».

---

## PB-10. Committing harvest cache changes

**When this fires.** A session touched files under `scripts/cache/`
(usual triggers: `parse_hede.py --force` after a parser fix updates
100+ Hede JSONs; `fetch_ikmk.py` adds new museum records; ucoin
composition harvest writes to `_composition.json`; Bruun parser
update rewrites `lots/part*.json`). The main repo's `git status` then
shows `modified: scripts/cache (new commits)` — that's the submodule
pointer waiting to be bumped.

Architectural background: `scripts/cache/` is a private-repo
submodule (see `docs/ARCHITECTURE.md` §«Harvest cache»). It carries
regenerable fetch / parse artefacts; the build pipeline doesn't read
it; only fetchers / parsers / audits / maintenance scripts do.

**The two-step commit dance.** Push the submodule FIRST, then bump
the pointer in main. Otherwise collaborators (or CI, if it ever
starts pulling the submodule) see a dangling pointer.

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

**Conventional-prefix messages.**

- Inside `scripts/cache/`: `harvest(<source>):` (e.g.
  `harvest(hede):`, `harvest(numista):`, `harvest(ikmk):`,
  `harvest(ucoin):`, `harvest(bruun):`).
- Inside main bumping the pointer: `build: bump harvest submodule
  (<one-line reason>)`.

**Symptom diagnosis — when in doubt, this runs.** If a session that
changed cache files forgets the two-step dance, the symptom is
`git status` in main shows `modified: scripts/cache (new commits)`
even after pushing the cache contents. That's just the
submodule-pointer bump waiting to be committed in main; step 2 above
fixes it.

**Detached-HEAD recovery after a submodule commit.** When you `cd
scripts/cache && git commit`, the commit can land on a **detached
HEAD** if the submodule was pointing at an SHA (not a branch tip) at
the time it was checked out — which is the normal state of a Git
submodule. `git log --oneline` shows the new commit; `git branch
--show-current` is empty; `git status` says `HEAD detached from
<sha>`. The new commit is real but it's not attached to `main`, so a
naïve `git push` from the submodule rejects the push («refusing to
update checked out branch» on the remote OR no upstream).

To recover without losing work:

```bash
# Inside scripts/cache, after the commit lands on detached HEAD:
git checkout main                # detaches HEAD warning — that's fine
git reset --hard <new-commit-sha>  # forwards main to the new commit
git log -2 --oneline             # verify the new commit is now on main
# Then back to main repo for the pointer bump (step 2 above).
```

The `git reset --hard` here is safe **only** because the SHA we're
resetting to is the commit we just made on detached HEAD — same
file content as the working tree. If unsure, `git branch tmp
<new-sha>` first as a safety belt before the reset. Triggered by
parallel-session timing where another agent advanced `origin/main`
between our submodule checkout and our commit; the «detached HEAD»
state is the symptom of the divergence.

**Recovery from a parallel-session rebase collision.** When another
agent has pushed pointer bumps on `main` that we haven't seen, our
two-step dance will reject at step 2 («! [rejected] main → main
(fetch first)»). Standard recovery is `git pull --rebase` — but if
the main-repo conflict is on the **submodule pointer line itself**
(both branches advanced the pointer to different SHAs), the rebase
fails on each pointer-bump commit in turn, asserting stale base
SHAs. Recovery pattern:

```bash
# Main repo:
git rebase --abort
git reset --hard origin/main             # accept incoming branch state
git submodule update --init              # pull submodule pointer to main's state
# Now manually advance the submodule to OUR new harvest commit:
cd scripts/cache && git checkout main && git reset --hard <our-cache-sha>
cd ../..
# One consolidated pointer-bump commit — preserves OUR cache work
# while accepting upstream's data/* commits:
git add scripts/cache && git commit -m "cache: bump submodule (post-rebase consolidation)"
```

This loses the per-batch granularity of multiple pointer-bumps that
might have been waiting locally, but the submodule history preserves
the per-batch detail in full. Triggered 2026-05-19 during BO.6 v2
work, see commit `16ccfe1`.

**Recovery from a `git pull` MERGE with submodule divergence.** A
NON-rebase pull (`git pull --no-rebase`, or plain `git pull` when both
sides diverged) that finds the **submodule itself diverged** (local
advanced N harvest commits, origin advanced M different commits, off a
common base) reports:

```
Failed to merge submodule scripts/cache (commits not present)
CONFLICT (submodule): Merge conflict in scripts/cache
```

Git CANNOT auto-resolve this — the two submodule pointers are not
ancestor/descendant (both branched off the merge-base). Resolution:
**merge the submodule by hand, then point the superproject at the
merged result.**

```bash
# 0. Confirm divergence direction (not a trivial fast-forward):
git ls-files -u scripts/cache          # stage 1=base, 2=ours, 3=theirs SHAs
cd scripts/cache
git fetch origin main
git merge-base --is-ancestor <ours> <theirs> && echo "linear" || echo "diverged"

# 1. Merge inside the submodule (both private-repo harvest histories
#    combine — merge commits are fine here; no content conflict when
#    the two sides touched different cache files, which is the norm).
git merge --no-edit origin/main
git rev-parse HEAD^1 HEAD^2            # verify the merge has BOTH parents

# 2. Back in the superproject: record the merged submodule pointer.
cd ../..
git add scripts/cache

# 3. Resolve any OTHER superproject conflicts (e.g. docs/anomaly_log.yml
#    — union both sides' new entries; for a resolved-vs-open anomaly,
#    take the side that RESOLVED it + keep the other side's new entries).
#    Then finalise the superproject merge commit:
git commit --no-edit
```

⚠ **Push-order is CRITICAL after this.** The superproject merge-commit
now references a submodule **merge-commit that exists only locally**
(it was created in step 1, never pushed). If the superproject is pushed
before the submodule, origin/main will reference a submodule SHA the
remote submodule doesn't have — a dangling pointer that breaks
`git submodule update` for every other clone / session. So the standard
PB-10 order is MANDATORY here, not just advisory: **`cd scripts/cache
&& git push` FIRST, then push the superproject.** (Same submodule-first
rule as the two-step dance above — but here it's load-bearing because
the referenced submodule commit is a fresh local merge, not an
already-pushed harvest commit.) Triggered 2026-05-30 reconciling a
63-local-vs-2-origin divergence where the submodule had also diverged
59-vs-1; submodule merge `468fb8ac`, superproject merge `0a85db1`.

**Push-permission rule still applies.** Per CLAUDE.md «Commit cadence
+ push permission»: never push autonomously. Both `git push` calls above
require the user's explicit «пуш» / «push» grant. The grant covers
the turn — for the harvest two-step, that means one grant authorises
both pushes (submodule first, main second), since they together form
the «atomic harvest commit» from the user's perspective.

**Related rules.** CLAUDE.md «Harvest cache» pointer; ARCHITECTURE.md
«Harvest cache (submodule)» section (canonical architectural
description); CLAUDE.md «Commit cadence + push permission» (governs
both pushes); **`docs/HARVEST_GUIDE.md`** is the canonical reference
for building a new harvester end-to-end (fetcher + parser + seed
builder + cache shape + decision tree for picking the right access
strategy). Read HARVEST_GUIDE.md FIRST when adding a new source —
it captures the patterns established during the §AZ four-source
pre-1541 harvest (Bruun + Wilcke + danskmoent.dk Galster + Numista
HTML + NumisMaster MC_NNNNN) so the next session doesn't re-discover
the URL patterns, the parser-quality benchmarks, the Cloudflare
rate-limit constants, or the common pitfalls (Python urllib em-dash
header encoding, Numista API-vs-HTML distinction, harness bash sleep
restrictions, JS-rendered SPA discovery via Chrome MCP).

---

## PB-11. Preview-mode lifecycle — auto-build + stop / restart

The Claude Preview MCP runs a live preview server against the
project's rendered output. Two operational concerns: keep the preview
in sync with this turn's edits (auto-build), and respect that the
user — not Claude — owns the preview lifecycle (stop / restart).

### Auto-build at end-of-turn

**Rule.** When the preview server is running AND this turn modified a
file that affects rendered output, run `python scripts/build.py`
before ending the turn. This keeps the preview window in sync with
the working tree without the user having to ask.

**How to detect preview is active.** The harness emits
`PostToolUse:Write hook additional context: A preview server is
running.` after any Write / Edit. If that reminder appears anywhere
in the turn — or if `mcp__Claude_Preview__*` tools are in scope —
treat preview as on.

**Files that affect rendered output (build-trigger):**
- `data/locations/*.yml` — coin data, phases, references
- `data/shared/*.yml` — fuesse, mints
- `data/i18n/*.yml` — UI strings
- `templates/**.j2` — Jinja
- `config/theme.yml` — CSS theme tokens
- `scripts/build.py`, `scripts/lib/**` — build pipeline + `style.base.css`
- `assets/**` — copied verbatim into `site/assets/`

**Files that do NOT trigger a rebuild:**
- `docs/**`, `CLAUDE.md`, `README.md`
- `scripts/maintenance/**`, `scripts/audit_*.py`, `scripts/oneoff/**`
- `scripts/cache/**` (read by maintenance scripts; not by `build.py`)
- `scripts/fetch_*.py`, `scripts/match_*.py`
- `requirements.txt`, `local.env`, `.gitignore`

**Granularity.** Run the build ONCE at end of turn, not after every
Edit. If the turn has multiple edits across web-affecting files,
one build at the end covers them all.

**When in doubt: build.** ~5-15 s of CPU cost beats the user noticing
a stale preview manually.

**If validation / render fails**: surface the failure in the response,
don't silently retry. Schema-validation breaks usually came from this
turn's edits and need a fix.

### Stop / restart — never unilateral

**Rule.** **Never call `mcp__Claude_Preview__preview_stop`** unless
the user has explicitly asked for it (in this turn or earlier in the
same session) — even if the preview seems idle, finished, or
redundant. The user runs the preview lifecycle; Claude does not stop
it unilaterally.

**Exception (explicit-permission phrasings).** When the user directly
says «stop the preview», «перезапусти превʼю», «restart the preview»,
or any equivalent phrasing that names the preview AND a stop/restart
action, that counts as the explicit permission this rule requires —
proceed with `preview_stop` (followed by `preview_start` for a
restart) without asking again.

**Restart implies stop.** Specifically for «restart» / «перезапусти»:
a restart is by definition stop + start, so a request to restart
inherently authorises the stop step — no separate confirmation
needed. This restart-implies-stop logic is **scoped strictly to the
restart phrasing** — it does not generalise to other words that could
be construed as adjacent (e.g. «refresh the preview», «reset»,
«прибери» without «перезапусти»); for anything that isn't an explicit
stop or restart request, the default no-stop rule still applies.

**Page reload — same shape.** The same applies to `location.reload()`
via `preview_eval` when the user asks to reload / refresh the page.

**Ambiguous mentions.** If the user mentions the preview but not a
stop/restart action, ask first; if disk-space or memory pressure
becomes an issue, surface it and let the user decide.

**Related rules.** CLAUDE.md «Preview lifecycle» pointer; CLAUDE.md
«Build command».

---
