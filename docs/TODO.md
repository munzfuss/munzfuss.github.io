# Pending audits and longer-term TODO

> **Read this at session start** — the entries below are open audit items
> that have not been actioned. CLAUDE.md links here so they don't get
> forgotten across sessions. When an item is done, move it to the
> "Done" section at the bottom (with the commit SHA) so we have a record.

## How to use this file

Open entries split into four priority tiers:

- **Highest priority** — exceptional, drop-other-work items. Only on
  direct user direction with the explicit **«найвищий»** marker
  («з найвищим пріоритетом», «highest priority», equivalents). These
  block everything else: when a Highest entry is open, no other tier's
  work should ship until it is resolved or explicitly demoted. Keep
  this section to ≤2 entries — if it grows past that, the «blocks
  everything» semantic dilutes. Default state: empty.
- **High priority** — important and emphasised by the user, but NOT
  «найвищий». Triggers: «високий пріоритет», «важливо», «зроби це
  скоріше», equivalents. These are scheduled-next in normal session
  rotation — they do not block other work, but get picked up before
  Normal-tier items. Keep ≤10 entries.
- **Normal priority** (default) — **every new TODO entry lands here
  unless the user explicitly says otherwise.** No priority annotation
  from the user = Normal. Other tiers (Highest / High / Low) only when
  the user emphasises the priority directly in chat.
- **Low priority** — deferred items. Things we're not abandoning
  but consciously postponing (external blockers, big-bang refactors
  pending decisions, ideas worth recording but not now). Move
  entries here when they survive several sessions without progress
  AND have no near-term trigger to act on them, OR when the user
  explicitly says «низький / low / не зараз».

**Trigger-phrase mapping (Ukrainian → tier):**

| User says | Tier |
|---|---|
| «найвищий», «з найвищим пріоритетом», «critical», «blocker», «p0» | **Highest** |
| «високий», «важливо», «зроби скоріше», «high», «soon» | **High** |
| (no priority mention) | **Normal** |
| «низький», «low», «не зараз», «deferred» | **Low** |

When ambiguous (e.g. user says «важливе питання» without explicit tier), default to Normal and surface the question — don't auto-escalate.

### Ordering within a category

**New entries are appended to the END of their category** — chronological
order (oldest at top of section, newest at bottom). Do NOT insert at
the top of the section. Rationale: append-only writes preserve
session-trail / git-blame archaeology and match how a backlog is
naturally consumed (oldest pending first). Existing entries that
predate this convention may sit in reverse-chronological order; that
quirk is grandfathered, but every NEW entry follows the append rule.

### Mandatory annotations on every new entry

The seven currently-flagged High-priority entries (§AA-§AG) carry a
trial set of inline markers. Going forward, **every new entry — in
any tier — must include both**:

- **A status emoji at the start of the title**, picked from:
  - 🟢 **ready** — no decision needed, can start immediately.
  - 🟡 **needs decision** — blocked on user verdict before any action.
  - 🔵 **per-case ongoing** — long-running grind, advances one case
    at a time.
  - 🔴 **paused** — external blocker (rate-limit, source unavailable,
    paid quota exhausted, etc.).
- **An effort estimate in the title**: `*(est: small | medium |
  large | many sessions)*`. Small ≈ <30 min, medium ≈ ~1 h,
  large ≈ multi-hour, many sessions ≈ stretches across days/weeks.

### Optional annotations (use when applicable)

- **Type tag** in the title: `*(type: audit | sweep | script |
  research | feature | tooling | decision)*`. Helps cross-cutting
  filtering — e.g. «all script-tasks I could pick up» — orthogonal
  to priority.
- **Dependency markers** in the body: `*(blocks: §X)*` /
  `*(blocked-by: §Y)*`. Surfaces coupling between entries when one
  must complete before another can start.
- **Last-touched marker** in the title: when an entry survives multiple
  sessions without progress, append `*(last touched YYYY-MM-DD)*`. An
  entry whose last-touched date is >14 days old AND has no recent
  partial-progress note is a candidate for either advancement, low-
  priority demotion, or closure as stale.

### Progress logging

When work begins on an entry, log progress in `docs/handoff.md`
(short-term state) and commit-by-commit in git history. When the
entry is fully closed, move it to `## Done` with the closing commit
SHA. When work happens but the entry isn't closed, update its body
in-place with the progress + remaining scope, and add a date marker
to the title (`*(opened YYYY-MM-DD, partial progress YYYY-MM-DD)*`).

### «Pending decision» summary

When the Highest- or High-priority section accumulates ≥2 entries marked
🟡 (needs decision), surface them as a short bulleted list right under
the section heading so the user sees on first glance what verdicts are
awaited. Inline format:

> **Awaiting your verdict before any action**: §AB (Daler-Klippe
> placement: new Fuß vs redefine fractions), §AC (9-Fuß-Familie
> scope: per-case vs family-wide).

Drop the summary block when only 0–1 🟡 entries remain in that tier.
The summary is per-tier — a Highest-tier summary stays under
`## Highest priority`, a High-tier one under `## High priority`.

## Highest priority

> **Empty most of the time.** Items here block all other work. Add
> only on explicit user direction with the «найвищий» marker (see «How
> to use this file»). Demote to High once the blocker semantic is no
> longer warranted.

### BF. 🟢 Denmark 1514-1566 gap — Müntzfüße + coin promotion for the new lower-bound window  *(opened 2026-05-15, rescoped 2026-05-16 per §BI)* *(est: large)* *(type: research-applied + data)*

**Surfaced.** User direction 2026-05-15 with explicit «найвищий» marker. The dual-anchor scope decision (§BC closed 2026-05-15) initially extended the Denmark page's lower bound from 1559 to 1541; §BI (2026-05-16) re-anchored further back to **1514** (Christian II Lovkompleks per Wilcke 1950 p. 183-186 verbatim). The seed builder's `--year-from` default is now 1514 and ~26 c3h Hede entries (Christian III + early Frederik II) sit in `data/seed/hede/denmark.yml` — but none of them are placed yet. The page renders the new (1514–1914) range in its header/timeline, but the 1514-1566 phase block of the Denmark page is structurally **empty of curated Müntzfüße + coins**. Closing this gap is the Highest-priority blocker for the Denmark-track research front.

**Note on pre-1541 sub-window**: the 1514-1540 portion (Christian II 1513-1523 + Frederik I 1523-1533) needs a NEW-SOURCE catalog import — **Galster 1959-1960 + Jensen-Skjoldager 2021** (sibling TODO §AZ — see below). Hede 1957 itself does NOT catalogue pre-Christian-III rulers, so this is not a Hede extension; it's a new reference-source family. Until §AZ lands, §BF's data-coverage stays at Christian III 1541+ from the existing Hede cache.

**Underlying research is already done.** Two long-form dossiers cover this period in detail:

- `docs/research/moentordning_1541.md` — full primary-source capture of the spring 20 March 1541 «Om Maal og Vægt» Forordning + autumn 20 September 1541 Møntordning + 1544 supplement + 1547 Flensborg Bestalling. Includes Marken-fin / Cølnsk-Vægt arithmetic, denomination tables, dual-zone (Lybsk vs Danish) currency seed of 1547, mintmaster's oaths.
- `docs/research/christian_iii_danish_coinage_1534_1572.md` — context for Christian-III-Daler-fod silver, gold one-offs, and the transition toward Frederik II's 9-Fuß alignment.

Primary-source captures: `docs/research/sources/wilcke_1950_christian_iii_moentreform.md`, `paus_christian_iii_1541_maal_og_vaegt.md`, `rigsarkivet_tk_160_diverse_moentsager.md`.

**Scope.** Four operational sub-tasks (from the §BC closure note, now promoted under §BF):

1. **Define new Müntzfuß `christian_iii_dalerfod`** in `data/shared/fuesse.yml`. Canonical metric: mf 8.827, 26.494 g fein per Daler, fineness 0.906 (14½ Lod), sourced to Wilcke 1950 + Rigsarkivet T.K. nr. 160 + Paus 1752. Per §BD this should probably be the Danish-form name from the start (`dalerfod` not `christian_iii_thaler_fuss`).
2. **Add `fuss_periods.christian_iii_dalerfod`** block to `data/locations/denmark.yml` with phases:
   - **A1 (1541–1543)** — København baseline, mf 8.827 unchanged.
   - **A2 (1544–1555)** — København debased per the 27 September 1544 supplement (mf 9.481 per dossier §4.5).
   - **A3 / A4 (1547+)** — Flensborg dual-zone (see decision below).
3. **Promote seed coins**:
   - **Phase A1**: c3h3-3A, c3h4, c3h5, c3h7 (København 1541-1543 baseline issues).
   - **Phase A2**: c3h3-3B (København 1544+ debased).
   - **Phase A3/A4**: c3h21, c3h22 (Flensborg 1545–1554 lybsk-aligned søsling), plus any 1547+ Bestalling-anchored Flensborg Daler.
   - Any other c3h / f2h entries currently in seed_unsorted that fall in this window.
4. **References** — new entries in `denmark-references.yml`:
   - Wilcke 1950 «Renæssancens Mønt» (Kap. 7-4 verbatim).
   - Galster 1965 (Danish numismatic synthesis).
   - Paus 1752 «Samling af Gamle Norske Love» Vol. II (verbatim transcript of «Om Maal og Vægt»).
   - Rigsarkivet T.K. nr. 160 «Diverse møntsager 1523-1619» (folio reference per the captured archive coordinate).

**Open design question — Flensborg post-1544 track (Phase A3 / A4).** Per `moentordning_1541.md` §7.1 the 1547 Flensborg dual-zone is the *genealogical seed* of the later `18_5_thaler` / `34_marck` family (Lybsk-aligned debased sub-Mark) vs `9_thaler` / Speciedaler family (heavier daler track). Two architectures:

- **(a) Separate Müntzfuß `christian_iii_flensborg_fod`** for the Lybsk-aligned sub-Mark + 14¼ Lod Daler. Clean genealogy: A1/A2 are København, A3/A4 are Flensborg. Two parallel Müntzfüße for the same monarch.
- **(b) Same `christian_iii_dalerfod` Fuß with mint-tag differentiation** — A3/A4 phases marked as Flensborg-specific within the single Fuß. Simpler structurally but conflates two genuinely distinct standards.

Likely answer is (a) — the dual-zone is the seed of an enduring lineage and deserves its own Fuß slot. User verdict requested before the data edit.

**Cross-references.**

- **§BD** (Danish Müntzfuß names) — the new `dalerfod` / `flensborg_fod` IDs should land in the Danish convention from day one. Sequencing §BD verdict before §BF data edit avoids immediate rename churn.
- **§BB** (Fuß descriptions — historical framing only) — `christian_iii_dalerfod` `hintergrund` prose follows the §BB rule (historical framing, no parameter bleed).
- **§AY** (Frederik II 3-Mark one-off) — sits at the boundary of this window (1560/1563); coordinate with §BF if the 1560s F2 seed entries land in the same pass.
- **§AV / §AW** (Guldkrone-fod, Rhinsk Gylden) — earlier Christian I / Hans gold entries; design decisions interact with the broader 1541-window architecture.
- **§BE** (Danish translation for DK/SH) — every new field added under §BF will eventually need a `da:` translation. Either add `da:` upfront (if §BE is also accepted) or accept the rework.

**Action sequence.**

1. User decides on (a) vs (b) for Flensborg.
2. User decides §BD architecture (jurisdiction-aware naming) at least at policy level — affects whether new IDs are `christian_iii_dalerfod` (Danish form) or `christian_iii_thaler_fuss` (German form).
3. Define Müntzfuß / Müntzfüße in `fuesse.yml` with sourced metrics + hintergrund prose.
4. Add `fuss_periods` block(s) to `denmark.yml` with phase boundaries + descriptions.
5. Promote seed coins into curated entries with `fuss:` + `phase:` set; preserve all per-specimen multi-source data (§9a).
6. Add the 4 new bibliography entries to `denmark-references.yml` with verbatim quotes + page hints per §5a.
7. Build clean + sample-review three coins per phase against the rendered page.

**Definition of done.** The Denmark page renders a non-empty 1514-1566 section with at least 6 placed coins, a `christian_iii_dalerfod` Fuß card with full metric block + sourced hintergrund, and the dual-track Flensborg phase (if (a)) wired up. The 26+ new c3h seed entries auto-suppress against the curated phase blocks per the `_merge_seeds_into_raw` rule. Pre-1541 sub-window coverage (Christian II 1513-1523 + Frederik I 1523-1533) depends on §AZ Galster + Jensen-Skjoldager catalog import landing first.

### BO. 🟢 Verify early-period absence on Numista, NumisMaster, ucoin (3 sub-tasks)  *(opened 2026-05-17, user-marked «найвищий»)* *(est: medium)* *(type: audit + harvest)*

**Surfaced.** Phase-1 raw-cache coverage table (2026-05-17) showed all three commercial / community catalogues with **zero entries before their respective earliest-cached year** for Denmark + Norge. Each source has a different floor; the audit window per source is from the mission lower bound **1514** up to (but excluding) the source's earliest-cached year:

  | Source | DK+NO cached | Earliest cached | Audit window (DK) | Audit window (Norge) | Pre-floor entries | Status |
  |---|---:|---:|---|---|---:|---|
  | **Numista** | 372 (range 1514-2008, was 1602-2008) | 1514 (was 1602) | **1514-1602** | 1514-1602 (same as DK) | **≥ 52 (2 DK + 16 SH-Danish-Duchies + 10 Schauenburg + 6 SH-Gottorp + 4 Lübeck-Bishopric + 14 misc cached previously)** | 🟡 substantial 2026-05-18 (BO.1 — DK harvest +2 + SH-cluster harvest +30; NO + Hanseatic free cities + DK ruler-walk deferred) |
  | **NumisMaster** | 1331 (range 1591-1914) | DK 1591 / Norge 1608 | **1514-1591** | **1514-1608** | **0** | ✅ closed 2026-05-17 (BO.2 negative finding) |
  | **ucoin** | 530 (range 1582-1875) | 1582 | **1514-1582** | 1514-1582 (same as DK) | **0** | ⏳ pending (BO.3) |

Two possibilities for each source:

  (a) **Platform genuinely doesn't catalogue pre-floor era** — Krause-Mishler-based platforms (NumisMaster, Numista catalog-num system) have known sparse pre-1604 KM coverage; this is consistent with what we'd expect.
  (b) **Our harvest missed them** — e.g. we used a date filter that auto-cut pre-floor; or a country tag we didn't probe (e.g. «HANSE TOWNS» wrapping joint-issue Christian II coins; or «SCHLESWIG-HOLSTEIN» pre-cadet entries that NumisMaster files under that tag rather than DENMARK).

Until we **prove (a) per source**, we have an unaudited dark zone in the Phase-1 coverage table. For the §BF Denmark 1514-1566 gap (currently dependent on §AZ Galster + Jensen-Skjoldager paper-track only), even a single (b)-case recovery would tighten the source pool.

**Why «найвищий».** The pre-1591 sub-window is the project's least-covered era. §BF (Denmark 1514-1566) is already Highest-priority blocked on this very gap. Closing the audit question — even with a negative «(a) confirmed» finding per source — is a precondition for declaring the 1514-1591 cache «mirrored». User direction 2026-05-17 with explicit «найвищий» marker.

#### BO.1 — Numista 1514-1602 audit (DK + SH-cluster + Lübeck-Bishopric + Norge)  🟡 **SUBSTANTIAL closure 2026-05-18** *(est: small → escalated to medium-large by Cloudflare blocker + SH-cluster scope expansion)*

**Audit window**: 1514-1602 for both Denmark and Norway (Numista floor is identical for both — 1602).

**Executed via Chrome MCP** (user direction 2026-05-17 — «не через апі, а через chrome mcp, роби довгі паузи між викликами рандом 31..60с»). 24 catalogue-search calls + 3 per-type page fetches over 25 minutes with 31-75 s pauses between each.

**Findings (Denmark) — partial closure, harvest gap confirmed:**

  1. **2 dated pre-1602 DK types confirmed AND harvested into cache** (both previously absent — cache earliest was 1602):
       - **N# 153125** — 1 Skilling - Christian II (Malmö; type 1) 1514-1515 — Billon .375, 2.37 g, ⌀ 26.8 mm — SIEG# C2-3, C2-4 — written to `scripts/cache/numista/153125.json` with `_harvested_via: chrome_mcp_html`.
       - **N# 301237** — 2 Schillings - Frederik I (Husum; portrait first type) 1514-1522 — Silver .750, 3.27 g, ⌀ 28.6 mm — SIEG# F1-43,1, F1-43,2 + MB# 10 — written to `scripts/cache/numista/301237.json`. Lettering identifies as DUCAL coin («FREDERICVS D HOLSACIE» = Frederik Duke of Holstein) struck pre-1523 before he became Danish king. Numista files under «Denmark» issuer tag retroactively per his later kingship. Cross-references §BP (DK+ vs RH separation on SH page) — exactly the kind of cross-tagged DK / SH duchy entry that motivates that debate.

  2. **Year-filter sweep 1514, 1515, 1517, 1519, 1524, 1529, 1534, 1539, 1544, 1549, 1554, 1559, 1564, 1569, 1574, 1579, 1584, 1589, 1591, 1594, 1599, 1601, 1602** (single-year filter `a=YYYY` per Numista form): year 1514 returned the 2 types above; all other 22 years returned 0 results.

  3. **Critical caveat — Numista's `a=year` filter is unreliable for «No Date» specimens.** Verified via NID 54915 (cached: «1 Søsling - Christian IV first type», cache says `min_year=max_year=1602`): the live Numista page shows «Date: ND (1602)» — i.e. the coin is undated, the 1602 is an attribution year. The `a=1602` filter returned **0 results** despite NID 54915 clearly belonging to the danemark issuer with year 1602. The filter appears to match on dated-specimen records only, NOT on `min_year`/`max_year` type metadata. **Implication:** my year-sweep almost certainly under-counts; any pre-1602 DK type whose specimens are all undated (the common case for pre-1650 small change) is invisible to this filter. The true count of Numista pre-1602 DK types is `≥ 2`, ceiling unknown.

  4. **Ruler-filter walk blocked by Cloudflare.** Attempted `?mode=avance&e=danemark&ru=2385` (Christian II) to enumerate by reign instead — Cloudflare 5-second challenge fired and did not auto-resolve in 75 s; URL became «BLOCKED: Cookie/query string data». 3-min cooldown + soft-reentry via plain `denmark-1.html` did clear the block, but subsequent attempts to access the linked «See N coins and medals» pages (which use the same `ru=` form internally) would re-trigger the block per the user's «жорсткі фільтри» warning. The ruler-detail page (`/catalogue/ruler.php?id=436`) itself loads fine but only shows 5-6 coin previews per category — full 131-entry DK Christian IV list is only reachable through the Cloudflare-protected listing URL.

  5. **Cache provenance.** Both newly-cached files (153125, 301237) carry explicit `_harvested_via: "chrome_mcp_html"` + `_audit_context` markers distinguishing them from API-shaped entries. The full cache shape is partial vs API-shaped entries — sufficient for `category: coin`, `issuer: danemark`, `min_year` / `max_year` indexing in the existing seed-builder pipeline; not sufficient for fields the seed builder doesn't currently consume from the API path (acceptable trade-off given the chrome_mcp source).

**Findings (Norway) — NOT yet attempted** because the DK sweep alone consumed the session's safe Cloudflare budget. NO sweep deferred to a future session under a different IP or a longer warm-up window. Expected pattern given DK results: ≥ 0 dated pre-1602 NO types via `a=` filter (Norway's coinage 1514-1608 was minimal — primarily Olav Engelbrektsson's late-medieval Trondheim issues; few dated specimens survive).

**Alternative-issuer probe (Hanseatic / Kalmar / Holy Roman) — NOT yet attempted** for the same Cloudflare-budget reason.

**Findings (SH-cluster + Lübeck-Bishopric) — 2026-05-18 expansion per user direction «впевнись що харвест 1514-1602 рр включає також і шлезвіг-гольштейнські royal/ducal князівства теж»:**

Audited 7 SH-cluster + Lübeck-Bishopric issuer landing pages directly (more reliable than year-filter for ND/undated specimens — issuer pages list ALL types with date display, parsing handles range vs single-year). Method: navigate to `/catalogue/<issuer_code>-1.html`, JS-extract NID + display-year for all entries, filter to pre-1602 locally, diff against cache.

  | Issuer | Total on Numista | Pre-1602 found | Cached before | Harvested 2026-05-18 |
  |---|---:|---:|---:|---:|
  | Denmark | 2212 | ≥ 2 (via `a=1514`) | 339 (range 1602+) | 2 (NIDs 153125, 301237) |
  | **Schleswig-Holstein-Gottorp, Duchy** | 91 | **6** | 6 | 0 (fully covered) |
  | **Schleswig and Holstein, Danish duchies of** | 66 | **18** (1 false-pos 158259 = 1848 medal) | 1 | **16** |
  | **Holstein-Schaumburg-Pinneberg, County** | 86 | **21** | 11 | **10** |
  | **Schleswig-Holstein-Sonderburg, Duchy** | 11 | 0 | 0 | 0 (duchy partition 1564, first coinage post-1602) |
  | **Schleswig-Holstein-Norburg-Plön, Duchy** | 4 | 0 | 0 | 0 (sub-duchy partition 1622, all post-1602) |
  | **Lübeck Bishopric** | 16 | **4** | 0 | **4** (Eutin mint; John Adolphus 1593-1599 Portugalöser; bishop-duke under SH-Gottorp regency 1586-) |
  | **TOTAL (DK + SH-cluster + Lübeck-Bishopric)** | — | **51** | 18 (+339 DK) | **32 newly cached** |

**Notable discoveries:**

1. **Numista SH-cluster floor pushed 1567 → 1538.** NID 137111 «Denier Bracteate - Otto V» (1538-1562, Holstein-Schauenburg-Pinneberg County) was missing from cache; its 1538 first-year is now the earliest Numista SH-cluster entry — 29 years before the previous cache floor (1567 SH-Gottorp).

2. **Frederik I as Duke of Holstein 1514 — multi-route cataloguing on Numista.** NIDs 468619 «½ Mark Frederick I» (1514, Husum, MB#18), 468620 «1 Mark Frederick I» (1514, Husum, MB#20), 301214 «2 Schillings Frederick I» (1514-1533, Schleswig), 301215 «1 Sechsling Frederick I» (1516-1532, Schleswig), 309409 «1 Thaler Frederick I» (1522, Husum, Lange#12 / SIEG F1-47 / MB#27 / Dav EC I 8235 / Galster 114), 417865 «1 Goldgulden Frederick I» (1531, Schleswig). All filed under «Schleswig and Holstein, Danish duchies of» — NOT under Denmark issuer (we already had Frederik I 1514-1522 Husum 2 Schilling NID 301237 under Denmark code from step 2). This is the same Frederik I, ducal authority pre-1523 → king post-1523; Numista cross-tags depending on which administrative period the type was minted in.

3. **Christian III ducal coins 1534-1559 fully present on Numista** — 16 ducal types now cached (Schleswig, Flensburg, Husum mints). Includes 1 Goldgulden 1536-1546 (NID 379084), 1 Thaler 1545 (NID 468485 = Hede#16 = Dav 8236), 1 Thaler 1547 (NID 309416 = Lange 20a = Hede#19 = MB#54 = Dav 8237), 2 Goldgulden 1546 (NID 474509 = Hede#15 = SIEG C3-52), and several Schilling / Sechsling / Pfennig minor coins.

4. **`Numista's year-filter `a=YYYY` filters dated-specimen records only, NOT min_year/max_year metadata** — verified caveat persists. Issuer-page approach (`<code>-1.html`) bypasses this by listing all types per issuer regardless of date-attribution status. Recommended for similar future audits.

5. **False-positive year-extraction risk in listing-page JS regex.** Pattern `\b(1[5-6]\d{2})` can match year-like substrings inside NID digit strings (e.g. «158259» → matches «1582»). 1 false positive caught (NID 158259, actual year 1848); 1 cached entry with similar risk noted (NID 152374 — already cached as «Frederik VI 1523» but Frederik VI ruled 1808-1839, so 1523 is likely a false-positive year, not the actual coin year). Pre-1602 year audits should always cross-verify via per-NID page fetch when the NID digits self-overlap with the audit window.

**Definition of done remaining**:
  - Norway 1514-1601 sweep (deferred).
  - Alternative-issuer probe — Hanseatic free cities (Hamburg, Lübeck-City — both in mission scope per CLAUDE.md), Holy Roman / Kalmar Union joint-issue tags. Deferred.
  - Decision on whether to fully enumerate pre-1602 DK ruler-walk via:
       (a) **API approach** (≤5-10 calls; rejected in current session per user direction «не через апі»; revisit when May-2026 budget guard relaxes in June 2026), OR
       (b) **Chrome MCP from a different IP** (e.g. user-machine VPN OFF if currently ON), OR
       (c) **Manual NID-fetch per cache gap** — only when a specific NID is suspected (e.g. via Hede / Bruun cross-reference yielding a Numista N# we haven't cached).

**Phase-1 coverage-table impact**: Numista DK + SH-cluster + Lübeck-Bishopric pre-1602 reclassified from «0 pre-floor» (initial 2026-05-17 surfacing) → «53 pre-floor entries identified on Numista; 32 newly harvested 2026-05-18, +20 already in cache = 52 covered; ≥1 from Denmark issuer still unaudited due to ND-filter caveat». Numista NO row remains «0 pre-floor (not yet audited)».

#### BO.2 — NumisMaster 1514-1591 (DK) + 1514-1608 (Norge) audit  ✅ **CLOSED 2026-05-17** *(est: small-medium)*

**Audit window**: **DK 1514-1591** + **Norge 1514-1608**. DK floor confirmed at 1591 via Phase-1b Sort=Date ASC walk (page-1 row-1); Norge floor confirmed at 1608 (KM_4 Lion Dalar). Both bear separate audit because the country filters are independent on NumisMaster.

**Closure (2026-05-17) — Option (a) confirmed: NumisMaster genuinely does not catalogue DK pre-1591 / Norge pre-1608 entries under any alternative country tag.**

Procedure:
  1. **Full country-filter enumeration** via Chrome MCP — opened numismaster.com `/coins` search facet, cleared cookies (canonical JS-console recipe), expanded the country filter dropdown. The full alphabetical list of 2100 unique country labels was enumerated. Filtered candidates by regex `DENMARK|NORWAY|NORGE|HANSE|HOLSTEIN|SCHLESWIG|HOLY|GERMAN|KALMAR|SCANDIN|NORTH|HAMBURG|LUBECK|EUROPE|UNITED|REICH|EMPIRE`. **Already walked** in Phase 1b: DENMARK, NORWAY, SCHLESWIG-HOLSTEIN + 5 cadets (GLUCKSBURG / GOTTORP / NORBURG / PLOEN / SONDERBURG) + HOLSTEIN-GOTTORP-RENDSBORG + SCHAUMBURG-PINNEBERG. **Notable absences**: NO «HANSE TOWNS», NO «HANSEATIC», NO «DENMARK-NORWAY», NO «DENMARK-NORWAY-SCHLESWIG-HOLSTEIN», NO «KALMAR UNION», NO «HOLY ROMAN EMPIRE» (only «GERMANY - EMPIRE» = 1871+ Reichsgoldmünzen era, well outside our pre-1608 audit window).
  2. **Local cache cross-check (SH-cluster pre-1591 reality)** — scanned `scripts/cache/numismaster/schleswig_holstein/MC_*.json`: 42 entries with first-year token 1514-1590. Country-tag distribution: SCHLESWIG-HOLSTEIN: 23, SCHAUMBURG-PINNEBERG: 15, SCHLESWIG-HOLSTEIN-GOTTORP: 4. Rulers: Adolf I (Gottorp), Christian III, Johann Adolf, etc. — all SH-cluster dukes. Christian III's SH-territorial coins are correctly under SH-tagged catalog records, not under DENMARK; his Danish-realm issues simply do not exist in NumisMaster's catalogue before 1591 (Krause-Mishler-based system, sparse pre-1604 KM coverage as predicted in §BO surfacing note option (a)).
  3. **Hanseatic candidate tags inspected**: HAMBURG (416 entries) — Sort=Date ASC dropped filter (known §BI bug), but default-sort row 1 of page 1 returned 1908-1923 Hamburg KM# entries. No DK-issue content. LÜBECK — same pattern (individual Hanseatic city, no DK-tagged content). Neither is a container for joint-issue Christian II / Frederik I era coins.

**Result.** The 9 SH-cluster country filters already walked in §BI (562 entries) **exhaust NumisMaster's Danish-jurisdiction pre-floor surface area**. No alternative country tag exists; no pre-1591 DK or pre-1608 Norge entries are recoverable from NumisMaster. Pre-floor count for Danish-realm and Norwegian-realm on NumisMaster: **N = 0, confirmed**.

Phase-1 coverage table updated accordingly — NumisMaster row's «Pre-floor entries» column is the documented negative finding, not an unaudited dark zone.

#### BO.3 — ucoin 1514-1582 audit (DK + Norge)  *(est: medium)*

**Audit window**: 1514-1582 for both Denmark and Norway (ucoin's earliest DK entry is 1582; Norge similarly low or absent).

**Approach.** ucoin is Cloudflare-blocked since the §M batch — Chrome MCP required. Existing cache has 530 DK entries 1582-1875. Verify whether ucoin's `tid` enumeration skips pre-1582 or whether we just didn't fetch them.

**Steps.**

  1. Via Chrome MCP, navigate to `https://en.ucoin.net/coins/denmark/`. Look at the «Earliest» year filter on the catalogue page (ucoin typically has a year-range slider).
  2. If pre-1582 entries exist: enumerate `tid` ids via the catalogue listing (Chrome MCP page text + paginate). Compare against our `_url_index.json` keys — anything new?
  3. Same for `/coins/norway/`.
  4. If gaps found: per-tid fetch via Chrome MCP (since urllib is Cloudflare-blocked). Cap at 50 per session per the existing ucoin rate-limit budget.
  5. Document closure: «ucoin DK earliest = YYYY (per catalogue UI); our cache = 1582; gap = N entries; status = (fetched / blocked / not-yet-fetched)» (same for Norge).

**Definition of done.** Each of BO.1, BO.2, BO.3 has either:
  - Pre-floor entries found + harvested into cache + reflected in Phase-1 coverage table, OR
  - A documented negative finding («(a) platform-side limitation: confirmed N=0 via X verification step over the audit window 1514-FLOOR») recorded in this entry's body.

Bundle takes the audit-completeness cluster (§BH Hede + §BM IKMK + §BN Bruun + §BO this) to «100% verified» across all 7 raw sources.

#### BO.5 — Numista DK 1602-1914 main-window coverage audit + harvest  🔵 **IN PROGRESS — batches 1+2/6 done (80 NIDs); paused after batch 2** *(opened 2026-05-18, est: medium-large)*

**Surfaced** by user direction 2026-05-18 «впевнись що в нашому нуміста кеші вже є всі монети по данії в 1602-1914 рр які є на нуміста». BO.1 / .2 / .3 addressed the pre-floor era; BO.5 addresses the main mission window (1602-1914 = Numista DK floor through pre-WWI end of precious-metal era).

**Audit result (2026-05-18, refined with user's URL filter):**

URL pattern: `https://en.numista.com/catalogue/index.php?e=danemark&st=1-2-3-47-154-5-54&cat=y&o=y` (coin subcategories only, excludes patterns/trial strikes/banknotes/medals/tokens, sort by year asc). Walked 5 pages (200/page; pages 1-4 in-window for 1602-1914, page 5 = 2006-2025 out of scope).

  | Metric | Value |
  |---|---:|
  | Total Numista DK coin types (e=danemark + st-filter, all eras) | 868 |
  | In-window [1602, 1914] | **547** |
  | Cache intersection (already harvested) | 335 |
  | **MISSING — needs harvest** | **212** |
  | Coverage % | 61.2 % |

The 212-NID gap is documented in `scripts/cache/numista/_BO5_audit_2026-05-18.json` (full per-NID list, decade distribution, per-batch breakdown).

**Decade distribution of the 212 missing** (gives a sense of which eras still need work):

  | Decade | Missing | Note |
  |---|---:|---|
  | 1600s | 35 | Christian IV early reign |
  | 1610s | 9 | |
  | 1790s-1810s | ~30 | Frederik VI / Speciedaler→Rigsbankdaler reforms |
  | 1820s-1860s | ~60 | Christian VIII / Frederik VII era |
  | 1870s-1914 | ~25 | Christian IX / Frederik VIII / Christian X Krone era pre-WWI |
  | Other 17th-18th | ~50 | Christian V / Frederik IV / V / VI minor coinage |

**Harvest strategy (decided 2026-05-18 with user):** option (b) — split into sessions of 40 NIDs each via Chrome MCP per-NID page fetches with 31-60s random pauses. Five batches of 40 + one tail batch of 12 = 6 sessions, ~50-55 min real time per session.

  | Batch | Status | NIDs | Year-range covered | Commit |
  |---|---|---:|---|---|
  | **1** | ✅ DONE 2026-05-18 | 40 (4139…54912) | 1602-1923 (mostly Christian IX / Frederik VIII / Christian X Krone era + 1602 Christian IV Penning/Hvid family + Frederik IV/V silver Skilling) | `a3d03a6` (submodule) |
  | **2** | ✅ DONE 2026-05-18 | 40 (55301…111300) | Christian V 8/12-Skilling 1683-1684 + SH-Glückstadt 24-Skilling 1762 + Norge Speciedaler + Frederik VI/VII Rigsbankdaler 1820s-1850s + Frederik III 4-Mark-Dansk Type IIA-V (KM# 194.2-194.5, Dav 3572-3574A) | `a33390b` (submodule) |
  | **3** | ⏳ pending | 40 (111312…181629) | TBD when run |
  | **4** | ⏳ pending | 40 (182700…366728) | TBD when run |
  | **5** | ⏳ pending | 40 (372940…468777) | TBD when run |
  | **6** | ⏳ pending | 12 (468831…577419) | TBD when run |

Per-batch NID lists live in `scripts/cache/numista/_BO5_audit_2026-05-18.json` under `harvest_progress.batches.batch_N.nids` — drop-in resume-friendly format.

**Cloudflare risk profile (empirical, 2026-05-17/18 across two harvest sessions):**

- Per-NID `/catalogue/pieces<N>.html` URL: **low risk**, survived 70+ sequential fetches across two days (BO.1 SH-cluster 30 fetches + BO.5 batch 1 40 fetches) with 0 trips at 31-60s pacing.
- Listing pages (`/<code>-1.html`, `?e=...`): **medium risk**, 2-3 trips during enumeration phase, each requiring 3-4 min cooldown.
- `?ru=` ruler filter URL: **high risk** — fires on first call.

The per-NID route is the safe one for incremental harvest. Listing-page enumeration only fires when scoping (BO.5's discovery phase is done).

**Pause rationale (2026-05-18, refreshed after batch 2):** user direction «зробимо тимчасову паузу щоб не було лімітів» after batch 1; reaffirmed after batch 2 with «запиши стан і що лишилось для наступних сесій, бо зараз зробимо паузу на юкоін і переключимось знову на нуміста на 1 батч» (1 Numista batch then pause again). The cumulative Numista access budget is finite and the user wants to spread the load across more days rather than burn it in one session. Per-NID fetches do not have a hard quota but they do contribute to Cloudflare's daily anti-abuse heuristic for our IP. Across batches 1+2 (80 total fetches over two sessions ~52 min each) **0 Cloudflare trips fired** at 31-60 s pacing.

**Resume procedure:**

1. Read `scripts/cache/numista/_BO5_audit_2026-05-18.json` → `harvest_progress.batches.batch_<N>.nids` for the next pending batch.
2. Use the JS extractor pattern from `docs/HARVEST_GUIDE.md §«Per-NID HTML fetcher»` (unchanged template).
3. Save via `/tmp/save_numista.py` (Python helper writes to `scripts/cache/numista/<nid>.json` with `_harvested_via: "chrome_mcp_html"` marker).
4. Per batch end: stage all 40 new cache files in submodule, commit with «numista: §BO.5 batch N/6 — ...», push submodule, update this entry's batch-progress table.
5. After final batch (6/6): write the seed-builder pipeline for chrome_mcp_html-harvested entries OR fold into existing Numista parser depending on how the data shape compares with API entries.

**Definition of done.** All 212 NIDs cached in `scripts/cache/numista/` with `_harvested_via: "chrome_mcp_html"` marker. Phase-1 coverage table updated to reflect 100% DK 1602-1914 coverage. Final BO.5 closure note replaces this in-progress entry.

#### BR — ucoin DK-realm 1514-1914 coverage audit  🔵 **AUDIT DONE + batches 1+2 of N harvested (80 NIDs; ucoin paused)** *(opened 2026-05-18, est: medium-large)*

**Update 2026-05-18 (post-pause resume):**

Per user direction «починай, бажано відсортовано по даті», resumed live ucoin harvest after the offline audit. Earliest gap = Norway under DK rule (ucoin period_id=2399 «Speciedaler 1648-1699», 153 total entries) — started chronologically there.

**Batches 1+2/N done (commits `4a323ea` + `bb4c6a4` in submodule):**

| Batch | Status | Count | Period coverage | Submodule commit |
|---|---|---:|---|---|
| **1** | ✅ DONE 2026-05-18 session 1 | 40 | p2399 page 1 (first 40 of 48) | `4a323ea` |
| **2** | ✅ DONE 2026-05-18 session 2 | 40 | p2399 page-1 leftovers (8) + page-2 first 32 | `bb4c6a4` |
| 3+ | ⏳ pending | 73 in p2399 + ~250 across other periods | p2399 page-2 tail (16) + p2399 pages 3-4 + other periods | — |

- **80/40+40 TIDs harvested**, all canonical-TID validations PASSED (zero «random euro-cent» mismatches across both sessions)
- Coverage by ruler: Frederick III 1648-1670 (Speciedaler/⅛/¼/½/2/4-Mark family) + Christian V 1670-1699 (1-Mark and 2-Mark families with multiple monogram variants per year)
- Save format: `scripts/cache/ucoin/<tid>.json` per-TID files with `_verified: true` + `_canonical_tid` + `_harvested_via: chrome_mcp_html` markers
- Save script: `/tmp/save_ucoin.py` aborts with exit code 2 on canonical-tid mismatch — prevents overwriting cache with the wrong-coin-served-as-defence-response

**Cumulative ucoin session-cookie budget check.** Per `docs/SOURCES.md §13.2`, the empirical cookie-cycle ceiling at 20 s pacing was ~50 fetches. Across batches 1+2 we did ~86 cumulative ucoin requests (80 harvests + 6 enumeration probes) over two ~70-min sessions, with **0 canonical-TID failures**. Either (a) the 31-60 s pacing extends the budget materially, or (b) the cookie-cycle reset between «sessions» (different conversation context) effectively gives a fresh counter, or (c) ucoin raised the threshold since §M (2026-05-13). Whichever explanation, the empirical cap is much higher in current conditions than §13.2 documented.

**Pause notice 2026-05-18 (after batch 2):** user direction «зробимо паузу на юкоін і переключимось знову на нуміста на 1 батч» — switching back to BO.5 Numista DK batch 2 for one session before resuming ucoin. ucoin state recorded in `scripts/cache/ucoin/_BR_audit_2026-05-18.json` under `harvest_progress.batches.batch_<N>.tids` for resume.

**Platform-floor confirmations (this session's discovery):**

  | Platform | DK floor | NO floor | SH floor |
  |---|---|---|---|
  | **Numista** | 1602 | 1602 | 1567 (SH-Gottorp) — varies by SH-issuer code |
  | **NumisMaster** | 1591 | 1608 | 1538 (Holstein-Schauenburg) |
  | **ucoin** | **1582** ✓ | **1648** ✓ | **1787-1851** ✓ (only 15 entries total) |

→ This **closes §BO.1 step 3 «Norway 1514-1601 sweep»** with a clean negative finding: all three commercial / community catalogues have a platform floor for Norway between 1602 and 1648 — no pre-1602 Norge data is recoverable from any of them. The §BF Denmark 1514-1566 gap remains paper-only (Galster / Jensen-Skjoldager) per the original audit.

**Remaining BR scope (revised after floor discovery):**

  | Scope | Total on ucoin | Cached | Remaining | Batches needed (40/each) |
  |---|---:|---:|---:|---:|
  | NO period 2399 (1648-1699 Speciedaler) | 153 | 40 | **113** | ~3 |
  | NO period 2400 (1699-1745 Speciedaler) | unknown | 0 | ? | ? |
  | NO period 1041 (1746-1812 Rigsdaler) | unknown | 0 | ? | ? |
  | NO period 883 (1813-1815 Rigsbankdaler) | unknown | 0 | ? (1813-1814 portion only) | ~1 |
  | DK period 374 (Christian IX 1873-1906) | unknown | 9 | known partial harvest | ~1-2 |
  | DK period 373 (Frederik VIII 1906-1912) | unknown | 0 | ? | ~1 |
  | DK period 220 (Christian X 1912-1947, in-window 1912-1914) | unknown | 0 | ? | small |

Estimated total remaining harvest: **~250-400 TIDs** across **6-10 batches**.

**Rate-limit budget tracking:** session 1 (2026-05-18 12:08-13:18, ~70 min) consumed ~45 cumulative ucoin fetches with zero canonical-TID failures. Per `docs/SOURCES.md §13.2`, the cookie-cycle cap is ~50 fetches at 20s pacing; at our 31-60s pacing we made 45 without trip — comfortable margin. **Each future session should cap at ≤45 ucoin fetches to stay below the ceiling.**

**Resume procedure for future sessions:**

1. **Enumerate next batch** if not already known: visit listing page (`/catalog/?country=norway&period=<P>&page=<N>`) via Chrome MCP, extract TID-to-slug mapping (one navigation, low Cloudflare risk).
2. **Per-TID fetch loop** — for each TID in batch:
   - Sleep 31-60 s random
   - Navigate `/coin/<slug>/?tid=<TID>`
   - Run the JS extractor (template in `HARVEST_GUIDE.md §«Numista catalogue enumeration»` is similar; ucoin uses inline-space label-value format vs Numista's tab-separated — adapt the `get(label)` regex from `/(?:^|\n)<label>\s+([^\n]+)/`)
   - **Mandatory canonical-tid check**: extract `link[rel=canonical]` href, parse `tid=NN`, compare against requested TID
   - On mismatch: ABORT batch immediately, alert user — rate-limit defence has fired. Do NOT save the file.
   - On match: pipe JSON to `/tmp/save_ucoin.py` (exit 2 on mismatch)
3. **Per batch end**: stage all new `scripts/cache/ucoin/<tid>.json` files in submodule, commit + push, bump pointer in main.
4. **Hard cap**: ≤45 ucoin fetches per session to stay under the rate-limit cookie cap. 40-batch sessions plus a few enumeration calls fits comfortably.

**Definition of done** (revised post-audit): all Norway 1648-1814 TIDs cached + DK 1873-1914 Krone era completed. SH 1787-1851 already complete (15/15). Pre-1648 NO + pre-1582 DK + pre-1787 SH + post-1851 SH confirmed as platform-floor (not data gaps).

**Surfaced** by user direction 2026-05-18 «проаналізуй так само що ще лишилось по ucoin для данії і її підконтрольних територій в рамках 1514-1914». Counterpart to BO.5's Numista audit, scoped to the DK realm (Denmark + Norway under DK 1514-1814 + Schleswig-Holstein duchies). Hamburg + Lübeck are separately in mission scope but are NOT «DK-controlled» — noted in passing for completeness.

**Method** — pure offline audit. Inspected `scripts/cache/ucoin/_url_index.json` (705 cached TIDs) + 15 per-period-or-country TSV harvest manifests (`period_*.tsv`, `country_*.tsv`). No live Chrome MCP calls to ucoin per user pause directive («зробимо тимчасову паузу щоб не було лімітів») + the pre-existing §M Cloudflare block since 2026-05-13.

**Cache coverage state (DK-realm + asides), per era × country:**

  | Era | Denmark | Norway | SH-duchies | (Hamburg) | (Lübeck) |
  |---|---:|---:|---:|---:|---:|
  | 1514-1581 | **0** 🔴 | 0 | 0 | 0 | 0 |
  | 1582-1601 | 12 ✓ | **0** 🔴 | 0 | 0 | 0 |
  | 1602-1648 | 123 ✓ | **0** 🔴 | 0 | 0 | 23 ✓ |
  | 1649-1699 | 206 ✓ | **0** 🔴 | 0 | 0 | 19 ✓ |
  | 1700-1749 | 66 ✓ | **0** 🔴 | 0 | 20 ✓ | 22 ✓ |
  | 1750-1812 | 54 ✓ | **0** 🔴 | 10 ✓ | 39 ✓ | 15 ✓ |
  | 1813-1854 | 52 ✓ | **0** 🔴 (DK rule ended 1814; rest is Sweden) | 6 ✓ | 17 ✓ | 0 |
  | 1855-1872 | 8 ✓ | n/a | **0** 🔴 | 4 ✓ | 0 |
  | 1873-1914 | **9** 🔴 (paused mid-harvest §M) | n/a | **0** 🔴 | 0 🔴 | 0 🔴 |
  | **Total** | **530** | **0** | **16** | **80** | **79** |

**Cached for the DK-realm + SH-duchies subset (this audit's primary scope)**: **546 entries**.

**Critical gaps (priority order):**

1. 🔴 **Norway 1514-1814 — 0 entries, never enumerated.** Mission scope explicitly includes Norway under Danish rule. Likely 30-80 types on ucoin (Kongsberg/Christiania mints, Christian IV Speciedaler family, Frederik III-Christian VII Skilling, Frederik VI Rigsbankdaler). **No TSV harvest file ever attempted for Norway.**

2. 🔴 **Denmark 1514-1581 — 0 entries.** Earliest cached DK is 1582 (from `period_2940` «Speciedaler 1582-1624»). Whether ucoin catalogues pre-1582 is unverified — may be a platform-floor (similar to Numista's 1602 floor, NumisMaster's 1591 floor) OR a harvest gap. **Probe needed to disambiguate.**

3. 🔴 **Denmark 1873-1914 Krone era — only 9 entries.** `period_374` TSV header explicitly says «only 1873-1875 overlap» — meaning the §M-era harvest (2026-05-13) deliberately paused after 1875 due to ucoin rate-limits. **This is a KNOWN deferred harvest**, complementary to BO.5 batch 1 Numista work just completed (which fetched 30+ Christian IX/Frederik VIII/Christian X NIDs from Numista).

4. 🟡 **Schleswig-Holstein duchies 1514-1788 — 0 entries.** Only 16 SH cached, all post-1787 Speciesbank-reform era. SH-Gottorp ducal coinage 1564-1773 + Christian III/Frederik II ducal coinage entirely missing.

5. 🟡 **SH 1855-1914 — 0 entries.** Both pre-1864 Helstaten era + post-1864 Reichsmark era missing.

**Asides (not «DK-controlled» but in mission scope per CLAUDE.md):**
- Hamburg pre-1700: 0 cached (earliest 1713). Hamburg post-1872: 0 (Reichsgoldmünzfuß era missing).
- Lübeck pre-1620: 0. Lübeck post-1854: 0.

**Rough scale estimate (offline-only — needs live verification):** total ucoin types for DK-realm 1514-1914 likely **700-1000**, of which **546 cached** = roughly **25-40 % real gap**. Norway is the dominant unknown.

**No batches yet defined** — harvest plan deferred. Once user lifts the «pause to avoid rate limits» directive, the resume procedure is:

1. Visit `en.ucoin.net/coins/norway/` via Chrome MCP to confirm catalogue exists + estimate type count
2. Probe ucoin SH country page for period_ids covering pre-1788 era
3. Identify ucoin period_id for Christian IX 1873-1906 post-1875 + Frederik VIII + Christian X
4. Once scopes are sized, build per-batch harvest plan similar to BO.5 (40 TIDs/session via Chrome MCP, ucoin-specific pacing: ≤45 TIDs per cookie-cycle at 20s pacing per `docs/SOURCES.md §13.2`)
5. Save through `scripts/maintenance/ucoin_fetch_composition.py`-equivalent flow with canonical-tid guard against the slug-redirect rate-limit symptom

**Constraints** per `docs/SOURCES.md §13.2`:
- Cloudflare blocked since §M 2026-05-13 (need user-side browser challenge-pass for `cf_clearance` cookie, OR ≥24 h IP cooldown, OR VPN egress switch)
- ~50-request session-cookie cap before bad-tid canonical-redirect symptoms

**Full audit summary** with per-bucket counts, harvest strategy per scope, and next-action checklist saved at `scripts/cache/ucoin/_BR_audit_2026-05-18.json`.

**Definition of done.** Norway 1514-1814 harvested (or verified-empty), DK 1514-1581 + 1873-1914 closed, SH pre-1788 + post-1855 closed. Phase-1 coverage table updated. BR closure note replaces this in-progress entry.

---
## High priority

> **Awaiting your verdict before any action**:
> - **§AB** (Daler-Klippe placement — new Fuß `daler_tarif_gold` vs redefine fractions). Deferred 2026-05-13: «поки що нічого з цим не роби, я вивчу питання і повернусь».
> - **§AM** (DROP 5 gold off-strike entries per CLAUDE.md §9.3) — per-case verdict per candidate (PB-1 style).
> - **§AQ** (Seed-merge data augmentation policy — field selection + conflict resolution naming).

### BP. 🟢 Schleswig-Holstein page — review correctness of DK+ vs RH separation  *(opened 2026-05-17)* *(est: small-medium)* *(type: curation policy + data)*

**Surfaced.** User direction 2026-05-17 — review whether the SH page's issuing-entity taxonomy correctly separates `gesamtstaat` (DK+) from `royal_holstein` (RH), and whether keeping them as distinct entities on the SH page is logical.

**Current state on `data/locations/schleswig_holstein.yml`** (323 curated coins, distribution):

  | Entity | Abbrev | Count | Coverage |
  |---|---|---:|---|
  | `gottorp_duchy` | HG | 103 | Holstein-Gottorp side (Schleswig, Husum, Tönning mints) |
  | `royal_holstein` | RH | 83 | Königlich-Holsteinische Anteil (Glückstadt, Altona-pre-Helstaten) |
  | `gesamtstaat` | DK+ | 59 | Helstaten-unified-state era (1773-1864 / Rigsbankdaler reform) |
  | `schauenburg_pinneberg` | SP | 43 | Pre-1640 Schauenburg county |
  | `sonderburg_duchy` | SD | 16 | Sonderburg cadet line |
  | `norburg_plon_duchy` | NP | 7 | Norburg / Plön cadet |
  | `rantzau_county` | RZ | 6 | Rantzau county 1650-1726 |
  | `glucksburg_duchy` | GB | 3 | Glücksburg cadet |
  | `provisional_govt` | PG | 2 | 1848-1850 Provisional Government |
  | (no entity) | — | 1 | needs audit |

**The audit question.** RH and DK+ both cover «Danish-crown-side» SH coinage, but at different historical phases:

  - **RH (royal_holstein)**: pre-1773 Danish-king-as-Duke-of-Holstein issues. Mints: primarily Glückstadt (1619-1750), pre-Helstaten Altona. Inscription typically names Holstein (HOLSTEINS, HOLST.) or the duchy explicitly.
  - **DK+ (gesamtstaat)**: 1773-1864 Helstaten-unified-state era. Mints: Altona + København + Glückstadt strike for the whole realm under unified Müntzfuß. Inscription typically «DANSKE» realm-wide.

**Open questions for this audit:**

  1. **Is DK+ presence on the SH page conceptually correct?** Helstaten DK+ coins are realm-wide legal tender; they circulate in SH but they're a *Danish realm* issue, not a *Holstein-territorial* issue. Should they appear on the SH page at all, or only on denmark.yml? Currently each DK+ coin may live on BOTH pages (if dual-cited), which risks double-counting.
  2. **Where does the RH→DK+ boundary actually fall?** Currently per §P the boundary is the 1773 Helstaten administrative milestone. But the 1813 Rigsbankdaler reform is arguably the stronger watershed for SH-coinage (because that's when Holstein-Glückstadt mint effectively transitions to all-realm Rigsbankdaler issues). Audit existing 59 DK+ assignments on SH page for consistency.
  3. **What about Altona-mint coins 1771?** Pre-1773 Altona issues — currently HG-tagged (Holstein-Gottorp), RH-tagged, or DK+? Probably should be RH (still pre-Helstaten royal-Holstein-side), but spot-check the 1771 KM# 616-series assignments to confirm.
  4. **Schleswig-1814-1864 Helstaten era**: Schleswig was Danish (not German imperial) jurisdiction throughout. Coins minted at Altona for the realm: DK+ or specifically Schleswig-marked variants tagged differently? Currently all Helstaten-era SH-mint coins are DK+ — verify against inscription content.

**Recommendation direction** (preliminary, subject to user review):
  - **Option A — Keep DK+ as SH-page entity**: argument is that Altona-mint Helstaten-era coins are SH-territory production, distinct from København-mint Helstaten coins which would only land on denmark.yml. The mint location is the territorial anchor.
  - **Option B — Drop DK+ from SH page**: argument is that DK+ is a *realm-level* entity (per its description: «for the whole realm»), so it conceptually belongs only on denmark.yml. SH-mint Helstaten coins would re-tag as RH-late or a new `royal_holstein_helstaten` sub-entity.
  - **Option C — Status quo, document explicitly**: keep current 59 DK+ + 83 RH split, but add a clarifying note to the SH location header explaining the dual-coverage rule (a coin can appear on both DK and SH pages when it's Helstaten-era + SH-mint).

**Done criterion.**

  1. Enumerate the 59 DK+ coins on SH page → tabulate by mint, year, KM# / Hede ref. Identify any that should be RH instead (pre-1773 misfiles).
  2. Enumerate the 83 RH coins → tabulate by mint, year. Identify any Helstaten-era (post-1773) that should be DK+ instead.
  3. Cross-check overlap with denmark.yml: how many DK+ coin ids appear on BOTH pages? Document the dual-coverage policy.
  4. Decide Option A / B / C with user (or hybrid). If A or C: write the rule into `schleswig_holstein.yml` location summary so future curators apply it consistently. If B: migrate 59 entries to RH (or a new `royal_holstein_helstaten` sub-entity) and remove DK+ from the SH page entirely.
  5. Document closure with count delta + policy rule.

**Cross-references.**

  - **§P** (Denmark issuing-entity audit, DK vs DK+ separation on denmark.yml) — same gesamtstaat boundary question but from the DK-page angle. §BP focuses on the SH-page side. Resolve §P first (it sets the 1773 boundary) → then §BP applies that boundary on SH page.

### AF. 🟢 Hede off-strike audit — bidirectional sweep done, 3 victims surface into §AM  *(opened 2026-05-13, updated 2026-05-15)* *(est: small — followups under §AM)*

**Surfaced.** During the c4h47 fix (silver Hede 47 spec card with Guldafslag Schou 1a sub-variant in Zincksamlingen list — caught 2026-05-13, commit `b0aa746`). The pattern: a Hede page primarily catalogues the silver mother coin, but the description / Zincksamlingen list mentions a Guldafslag (gold off-strike) sub-variant with a different Schou number (e.g. Schou «1» for silver, «1a» for gold). A curator who reads only the spec card and ingests Bruttovægt/Finhed onto a `metal: gold` entry produces a silver-fineness gold coin — exactly the c4h47 trap. Symmetric case (gold mother coin + Sølvafslag silver off-strike → curated `metal: silver` ingesting gold fineness) is the bidirectional sister; both directions exist in real Hede data (e.g. f3h36 «10 Dukat» 0.979 with Sølvafslag, f4h27-29 «Guldjeton» with Sølvafslag).

Documented in `docs/SOURCES.md` §13.4.

**Implementation — `scripts/audit_hede_offstrike.py`** (initial 2026-05-13 commit `f61e312`; enhanced 2026-05-15):

  1. Walk all Hede cache pages (`scripts/cache/hede/*.json`).
  2. Off-strike markers: «Guldafslag», «Sølvafslag», «medaljonprægning», «cf. Hede N».
  3. **Spec-card metal extraction — schema-aware** (2026-05-15 fix): walks both `specs.default.finhed` AND `specs.by_hede.<num>.finhed`. The initial version only checked `specs.default`, missing 18 pages (~45 % of flag-worthy ones) where Hede combines several catalogue numbers on one page and stores per-sub specs under `by_hede` — including f3h62 + f3h68 referenced by §AM candidates.
  4. **Nominal-text fallback** for pages with no finhed published anywhere (`f4h27-29` Guldjeton, `f6h10` Prøvemønt-in-copper): gold tokens (Dukat / Pistole / Goldgulden / Portugaløser / Guldjeton / Guldkrone / Rosenobel / Sovereign / Ungersk gylden), silver tokens (Speciedaler / Rigsdaler / Mark / Skilling / Daler / Krone). Ambiguous nominals → `spec_card_metal: "unknown"` (not cross-referenced).
  5. **Cross-ref**: for each flagged page, look up curated `coins[]` whose `(catalog.hede_volume, catalog.hede)` matches any of the page's legitimate-reference numbers (filename num + by_hede sub-numbers) AND whose `metal` is opposite the spec-card metal.
  6. **Self-test mode** (`--self-test`): synthesises one silver-spec-card + Guldafslag victim, one gold-spec-card + Sølvafslag victim, and one nominal-text-fallback victim, asserts each is flagged. Proves bidirectional logic without depending on live data.

**Scan result 2026-05-15:** 40 flagged pages (silver-mother 22 with Guldafslag, gold-mother 18 with Sølvafslag). 3 curated victims surfaced in `denmark.yml`:

  - `denmark::hede-61-fr-iii-1662` — gold Portugaloser referencing f3h62 (silver Speciedaler page) [also tracked as §AM candidate 2]
  - `denmark::hede-61-4ducat-fr-iii-1663` — gold 4 Ducats referencing f3h62 [§AM candidate 3]
  - `denmark::hede-68a-fr-iii-1665` — gold 5 Ducats referencing f3h68 (silver Speciedaler page) [§AM candidate 4]

All 3 are subsumed by §AM (DROP gold off-strike entries per §9.3). The remaining 2 §AM candidates (hede-156-chr-iv-1623, hede-80b-fr-iii-1668) reference Hede pages whose cache text contains NO off-strike markers — §AM needs re-investigation for those two (the §AM body was written before the §AF cache-driven cross-check).

**Resolution per CLAUDE.md §9 exclusion #3.** Single-specimen off-metal strikes are EXCLUDED from the location coin table. Each victim → «delete entry» (not «convert metal/fineness»). Per-case verdict tracked under §AM (PB-1 style).

**Closure (2026-05-15).** §AF can close once §AM resolves the 3 confirmed candidates. Script lives as ongoing guard — re-run anytime via `.venv/bin/python scripts/audit_hede_offstrike.py` (curated sweep) or `--hede-only` (Hede-page-only inventory) or `--self-test` (logic sanity check). Future Hede cache updates / curated additions should re-trigger the audit to catch regressions before commit. Wiring into pre-commit / `audit_health.py` not yet done — possible follow-up if regressions show up.

### AE. 🟢 Build-guard survivors audit — metal/weight/year mismatch guards on seed-merge  *(opened 2026-05-13, closure-pending 2026-05-13)* *(est: small)*

**Surfaced.** Latest build reports persistent guard-survivors. Investigated 2026-05-13:

  - **9 metal-mismatch kept** — 8 are legitimate cf-companion citations (gold Portugaloser citing the silver Hede sub-type whose dies it shares). ONE outlier — `dk-hede-c5h128` (silver) → `km-79-chr-v-1693` SH (billon, same fineness 0.437) — has identical fineness but escape hatch in `scripts/build.py:408-416` doesn't fire. **Root cause identified**: SH curated `fineness[]` includes outlier value 0.347 (Numista, tagged «likely transcription error») which pulls midpoint to 0.392 vs seed 0.437 → 10.3% delta, exceeds 2% threshold. The fix needs a structured way to exclude tagged-anomalous values from the min/max computation — moved to §AL.
  - **5 weight-mismatch kept** — analogous root cause. Curated `weight_rough_g[]` lists include outlier values (km-25 .49g Numista anomaly, km-128 8.428g Numista transcription error, hede-47 6.93g Bruun gold-strike — now resolved) that pull the 25%-ratio guard. Same anomaly-field redesign needed — moved to §AL.
  - **2 year-mismatch kept** — confirmed legitimate via guard-replication scan 2026-05-13: `dk-hede-c4h55` (1624) vs `dk-tid-97358` (1646) Δ=22y; `dk-hede-c4h167` (1588) vs `km-85-chr-iv-1640` (SH, 1640) Δ=52y. Earlier suspicion of off-by-one on c4h99B/C/D vs km-52 — FALSE ALARM (Δ=2y within ±10y window, guard correctly suppresses them).

**Closure.** No standalone fix in §AE; all three sub-investigations point at the same root cause (anomaly-outlier handling) which §AL will address structurally. Year-mm sub-investigation surfaced no action — guard is working correctly on the legitimate pairs. §AE is now a documentation entry recording the diagnosis; **mark Done after §AL lands** (since §AL closure subsumes the practical fixes).

### AD. 🔵 Hede sub-letter Pattern B fold buckets — 38 remaining  *(opened 2026-05-13)* *(est: many sessions)*

**Surfaced.** The 46-case NO-KM dedup audit (Pattern B per CLAUDE.md §9 caveat + PB-1) closed cases 1-9 manually; ~38 Hede-page sub-letter sibling buckets remain in the seed yaml as separate per-sub-letter entries waiting to be folded under a single Krause# parent.

**Remaining buckets** (per `scripts/oneoff/audit_seed_survivors.py` output, ordered by Hede volume):

  c4h: 84[A,B], 93[A,B], 100[A,B], 107[A,B,C]
  c5h: 67[A,B], 69[A,B], 90[A,B,C], 93[A,B], 95[A,B,C], 125[A,B], 126[A,B], 127[A,B]
  c6h: 6[A,B], 7[A,B]
  c7h: 11[A-D], 33[A-C], 39[B-G] (six sub-letters!), 40[A,B], 41[A-D]
  c8h: 8[ba,bb]    ← parser-quirk «sub-sub-letter»
  f2h: 30[A,B]
  f3h: 15[A,B], 79[A,B], 97[A,B], 108[A,B], 110[A,B], 122[A-C], 126[A,B], 130[A,B], 134[A-C], 138[A-D], 141[A,B]
  f4h: 43[A,B]
  f5h: 34[A,B], 36[A-C], 37[ba,bb]   ← parser-quirk
  f6h: 4[A,B]

**Procedure.** PB-1 per case (gather sources up-front → за/проти merge → user verdict → execute). User direction 2026-05-12: «без автоматичних батчів».

**Closed so far (commits):** case 9 = c4h79 (`6d7a087`), case 8 = c4h59/Hede-59 (`4d59131`), case 7 = c4h178/Krause cross-volume (`cea6b5d` family). 4 done, 38 remaining.

### AB. 🟡 Daler-Klippe 1604 placement — par-metal presentation gold, NOT Reichsdukatenfuß  *(opened 2026-05-13, deep-researched 2026-05-14)* *(est: medium)*

**Surfaced.** While fixing dk-hede-c4h12 silver→gold (commit `b971756`) and the family-wide 1604 Daler-Klippe seed entries (commit `b041b44`). Currently the 1604 Christian IV Daler-Klippe series (8 / 6 / 4 / 3 Daler) sits under `reichsdukatenfuss` with bare-denomination fractions; Δ-from-Reichsdukatenfuß-Soll is systematically −40 to −41 % — the coins are **not** Reichsdukatenfuß.

**Full evidence dossier**: `docs/research/daler_klippe_1604.md` (compiled 2026-05-14, includes ordinance text references, Bruun verbatim tariff statement, Hede specs, Galster context, computed economics, Wilcke II pattern analysis). Read that first before resuming the TODO.

**Key findings (TL;DR from the dossier):**

  - **Tariff** (face value, from Bruun lot 1017 verbatim): «At the time the value of 6 Daler corresponded to 3.5 Ducats (Hungarian Guldens)». Sets 1 Daler 1604 = 0.583 Dukat = 2.005 g fein gold; consistent with 1602 silver-Daler tariff at 66 Skilling Danske.
  - **Actual gold content** vs tariff: 8 Daler +3.0 %, 6 Daler +1.1 %, 4 Daler +1.2 %. **Par-metal with small prestige premium**, NOT seigniorage-spread tariff coins. State pays slight excess for prestige; this is opposite to commercial tariff coins (Krone-Mønt) where face value > metal value.
  - **Function**: explicit non-commercial — Galster verbatim «kom ikke til at få større betydning i handel og vandel». Hofgeschenk, royal gifts, presentation pieces. Mintages 61-588 stk per type.
  - **Variable fineness per denomination** (0.833 / 0.923 / 0.937 across 4/6/8 Daler) breaks any single-Fuß contract.
  - **Pattern context**: part of Christian IV's continuous 1590-1648 tradition of state-gold-tariff Klippen by ordinance (Prinsens Daler 1590, Schwabe coronation 1596, 1604 Daler-Klippe, 1608-11 Kalmar-War Sovereigns, 1618+ Guldkrone). Direct sibling to Guldkrone, not precursor.

**Terminology correction** (user direction 2026-05-14): my earlier name `tariff_gold_klippen` is WRONG. These coins are tariff-DEFINED (fiat value set by ordinance) but NOT «tariff coins» in the seigniorage-spread sense (no spread between face and metal). The word «tariff» collides with established `kind: tarif` for Krone-Mønt. Better naming candidates emphasising the par-metal character:

  - **`daler_klippen_1604`** — narrowest, scope-limited to documented set (recommended for starter)
  - `chr4_gold_klippen` — broader, requires Wilcke I research to confirm 1608-11 / 1618+ compatibility
  - `forordning_1602_guld` — references the specific ordinance

**3 Daler retention** (confirmed 2026-05-14): keep Hede 13 in the series with the «not in 1602 ordinance, only single specimen known» status flagged in the coin's `note` (per dossier §2.4). Don't exclude.

**Open question** — Fuß schema fit: variable fineness across denominations + one-shot 1604 issue + no obvious Cölln. Mark fein integer division break the «sustained Münzfuß» abstraction. Two paths:

  (a) Shoehorn into a Fuß slot for now (cosmetic correct in coin table; `historical_name` documents it's not a real Fuß). Lower effort, unblocks coin placement.
  (b) Schema-level refactor for non-Fuß coin entries (model these as ordinance-defined gold-tariff pieces without a Fuß-fraction relationship). Higher effort, more honest.

**Pending decisions:** (1) starter Fuß name (lean `daler_klippen_1604`); (2) shoehorn (a) vs schema refactor (b); (3) verbatim-quote refs sweep — promote Bruun lot 1017 «6 Daler = 3.5 Ducats» quote + Galster «kom ikke til at få større betydning» quote into `denmark-references.yml` as §AS-style entries.

### AA. 🔵 Seed `fraction` field audit — systematic sweep  *(opened 2026-05-13)* *(est: large)*

**Surfaced.** Two recent fixes (`93b2f6e` for dk-hede-f3h48 wrong `fraction: '1'` on a 1/6 Speciedaler coin; `2e3e1a9` for dk-hede-f2h30 wrong `fraction: '1/96'` on a Skilling Lybsk coin) revealed broader seed-yaml `fraction` field issues. The auto-render math (Soll-fein × fraction) silently produces wrong Δ values when the field is missing or wrong, since the renderer just multiplies whatever's in the field.

**Cluster 1 — Skilling-Lybsk seed entries** (9 entries spanning different Müntzfuß eras):

| Seed | Year | Era | Current fraction |
|---|---|---|---|
| `dk-hede-c4h167` 4 Sk Lybsk u.år | 1588 | pre-Kipper | `'1/24'` (1 Sk = 1/96 Sp?) |
| `dk-hede-c4h170` 3 Sk Lybsk | 1623 | transition | `None` |
| `dk-hede-c4h172` 6 Sk Lybsk | 1625 | post-Kipper | `'1/16'` |
| `dk-hede-c4h176` 3 Sk Lybsk | 1640 | post-Kipper | `None` |
| `dk-hede-c4h177` 3 Sk Lybsk | 1644 | post-Kipper | `None` |
| `dk-hede-f3h149` 3 Sk Lybsk Døtgen | 1658 | Frederik III | `None` |
| `dk-hede-f3h151` 6 Sk Lybsk | 1665 | Frederik III | `'1/16'` |
| `dk-hede-f3h152` 3 Sk Lybsk Døtgen | 1665 | Frederik III | `None` |
| `dk-hede-c5h124` 3 Sk Lybsk | 1680 | Christian V | `None` |
| `dk-hede-c7h45` 2 Sechsling | 1787 | Schimmelmann | `None` |

Each era has its own Lybsk-to-Speciedaler ratio (pre-Kipper 1 Sk Lybsk = 1/32 Sp, post-Kipper 1/48, Schimmelmann 1/60 Schilling-Schl-Hol-Courant). Per-entry case work needed.

**Cluster 2 — f3h48 1648 sisters with missing/wrong fraction** (same 9-Fuß-Speciedaler-Familie as f3h48):

  - `dk-hede-f3h47` (¼ Sp 1648) — `fuss: seed_unsorted`, `fraction: None`.
  - `dk-hede-f3h49` (1/12 Sp 1648) — `fuss: seed_unsorted`, `fraction: None`.
  - `dk-hede-f3h51` (2 Sp 1649) — `fuss: seed_unsorted`, `fraction: None`.

All three should be `fuss: 9_thaler` + appropriate fraction (1/4, 1/12, 2 respectively). Pattern matches the f3h48 fix.

**Cluster 3 — General seed-yaml `fraction` field audit:**

  Run a one-off sweep: walk `data/seed/hede/denmark.yml`, for every entry where `fraction` is `None` OR where `fraction` is inconsistent with the nominal text (e.g. nominal «1/6 Speciedaler» but fraction `'1'`, or nominal «3 Skilling» but fraction `'1/4'`), flag for review. The «nominal X/N but fraction=1» pattern was already swept (commit `93b2f6e` found ONE bug, f3h48); the broader «nominal X/N but fraction != 1/N» and «fraction: None» patterns are still open.

**Plan.** `scripts/audit_seed_fractions.py` — script walks seed yaml, cross-references nominal-text against fraction value, flags discrepancies. Run, review output, fix per-case.

### AM. 🟡 DROP 5 gold off-strike entries per CLAUDE.md §9 exclusion #3  *(opened 2026-05-14)* *(est: small)*

**Surfaced.** Metal-mm guard-survivor investigation 2026-05-14. Five curated gold entries in `denmark.yml` reference a silver Hede page where the Hede description explicitly lists «Guldafslag» (gold off-strike) variants. Per the new §9 exclusion #3 (added 2026-05-13), single-specimen off-metal strikes are NOT minted for circulation and don't belong in the location's coin table.

**Candidates (5):**

  1. `denmark::hede-156-chr-iv-1623` — Portugaloser (10 Ducats), references Hede 156 silver Speciedaler page. Hede text «cf. Schou 16/35». **§AF cross-check 2026-05-15 — UNCONFIRMED**: c4h156.json cache contains no Guldafslag/Sølvafslag/«cf.\\s*Hede» markers. The Schou cross-ref in §AM body alone doesn't match the off-strike pattern. Re-investigate before DROP.
  2. `denmark::hede-61-fr-iii-1662` — Portugaloser (10 Ducats), references Hede 61. Hede page **f3h62** explicit «Guldafslag: 10 Dukat, 5 Dukat og 4 Dukat». **§AF cross-check 2026-05-15 — CONFIRMED**.
  3. `denmark::hede-61-4ducat-fr-iii-1663` — 4 Ducats, same f3h62 Guldafslag list. **§AF cross-check 2026-05-15 — CONFIRMED**.
  4. `denmark::hede-68a-fr-iii-1665` — 5 Ducats, references Hede 68. Hede page **f3h68** explicit «Guldafslag 20 Dukat 1665, 12 Dukat 1665 og 5 Dukat 1665». **§AF cross-check 2026-05-15 — CONFIRMED**.
  5. `denmark::hede-80b-fr-iii-1668` — 10 Ducats (Portugaloser), references Hede 80 silver Speciedaler page. **§AF cross-check 2026-05-15 — UNCONFIRMED**: f3h80.json cache contains no off-strike markers. Re-investigate before DROP.

**§AF audit confirms 3 of 5** (cases 2/3/4). Cases 1 and 5 lack cache evidence for the Guldafslag claim — either the §AM body cited the wrong Hede page, or the cache is incomplete for those pages. Verify against the actual `danskmoent.dk` HTML before DROP. Cases 2/3/4 are ready for user verdict.

**Verdict needed per case** (PB-1 style):
  - «DROP entry» — confirmed off-strike, delete from yaml. Silver seed entry then promotes via Hede coverage.
  - «KEEP — actually own coin with own Hede number» — rare; not single-specimen off-strike.
  - «SPECIAL — record as separate presentation register» — out of current project scope; defer.

### AN. 🟢 Investigate Bruun cross-citation noise (3 cases)  *(opened 2026-05-14)* *(est: small)*

**Surfaced.** Metal-mm guard-survivor investigation 2026-05-14. Three Bruun-curated silver Reichstaler entries in non-Danish locations carry `catalog.hede` references pointing at Danish Hede gold-tier catalogue pages. Strongly suggests Bruun-parser mis-attribution of the `hede` field for these specific records.

**Cases:**

  1. `brunswick_lueneburg::bruun-5536-christian-1627` (silver Reichstaler/Speciedaler) → `catalog.hede: c4h5` (Danish 1 Portugaløser GOLD)
  2. `bremen_verden::bruun-5942-frederik-1641` (silver Reichstaler/Speciedaler) → `catalog.hede: f3h1` (Danish 2 Dukat GOLD)
  3. `bremen_verden::bruun-5941-frederik-1641` (silver 2 Speciedaler) → `catalog.hede: f3h2` (Danish 3 Dukat GOLD)

**Investigation steps:**

  1. Open each `bruun-<id>` cache lot record in `scripts/cache/bruun/lots/part*.json`. Check `body_excerpt` — does the auction lot text actually cite Hede c4h5 / f3h1 / f3h2, or was the Hede ref auto-injected by the parser from an adjacent unrelated lot?
  2. If the auction text DOES cite Hede c4h5 (etc.), it's probably a Bruun cataloguer's «cf.» mention, not a categorical attribution. Strip `catalog.hede` from the curated coin and record as a comment in `note` («Bruun cataloguer noted cf. Hede c4h5 — different metal, different lineage, not the same type»).
  3. If the auction text does NOT cite it — Bruun parser bug. Fix in `scripts/parse_bruun.py` (or wherever the catalog-ref extraction lives) and re-run; remove erroneous refs.

### AO. 🟢 c5h128 silver/billon labelling — same fineness, different label  *(opened 2026-05-14)* *(est: small)*

**Surfaced.** Metal-mm guard-survivor investigation 2026-05-14. Seed `dk-hede-c5h128` labels `metal: silver`, curated `sh::km-79-chr-v-1693` labels `metal: billon`. Both publish fineness 0.437 — same physical material (silver alloy at fineness <0.5 = «billon» in numismatic convention; «silver» on the Hede page is just the parent-language label).

**Two paths:**

  (a) **Forward fix in seed builder.** Update `scripts/maintenance/build_hede_denmark_seed.py:633` to map silver-fineness<0.5 → billon at seed-generation time. Re-run builder to regenerate seed yaml. ~5 LoC.
  (b) **Guard amendment.** Update `scripts/build.py` `_merge_seeds_into_raw` metal-mm guard to treat silver/billon as equivalent when both fineness values are <0.5. Backward-compatible; no seed re-gen needed. ~3 LoC.

Either eliminates the metal-mm guard fire on c5h128 (and any future similar cases). Recommendation: (a) cleaner long-term, but (b) less invasive. Pick one, implement.

### AP. 🟢 Fix `audit_hede_offstrike.py` specs walk bug  *(opened 2026-05-14)* *(est: small)*

**Surfaced.** §AF script bug found 2026-05-14 during metal-mm investigation. Script hardcodes:

```python
default_spec = specs.get("default") or {}
finhed = default_spec.get("finhed")
```

But multi-sub-letter Hede pages store specs under `specs.by_hede` (or `specs.A` / `specs.B` etc.) — the lookup returns None and the page is skipped from flagging entirely.

**Verified missed cases**: `f3h62` (has «Guldafslag: 10 Dukat, 5 Dukat og 4 Dukat»), `f3h68` (has «Guldafslag 20 Dukat 1665, 12 Dukat 1665 og 5 Dukat 1665») — both have `specs.keys() = ['by_hede']`, `finhed = None`. Both skipped by current script. The 5 §AM candidates would have been caught if the script worked correctly.

**Fix:** walk all sub-keys of `specs.*`, take the first numeric `finhed` found. ~10 LoC. Re-run to catch missed cases (should now flag the 5 §AM candidates + verify no other similar mis-flagged Hede pages exist).

### AQ. 🟡 Seed-merge data augmentation — replace suppression with field-wise merge  *(opened 2026-05-14)* *(est: medium)*

**Surfaced.** During metal-mm investigation 2026-05-14, user identified a systemic policy gap in `build.py` `_merge_seeds_into_raw`:

> «Тут загалом теж не ясно, адже жоден не повинен бути suppressed, має бути мердж з доповненням або набору даних, або лише посилання на джерело якщо дані однакові.»

Current behavior: when curated coin matches seed by Hede ref AND no guard fires → seed entry is **fully suppressed** (not rendered, not merged into curated). Seed's `sources[]` URLs, alternative weight readings, fineness alts are silently lost.

**Correct semantic — field-wise merge:**

  1. When curated has data parity with seed → merge `seed.sources[]` into `curated.sources[]` as additional confirmation citations (deduplicate by URL).
  2. When curated lacks a field that seed publishes → append to list per §9a multi-specimen merge rule (the field value becomes a new entry in `curated.<field>[]`).
  3. When values disagree but guards don't fire → just URL augmentation (curated value wins; seed source URL added).
  4. When guards fire → existing keep-both behavior preserved (signal that human review needed).

**Implementation steps:**

  1. Modify `_merge_seeds_into_raw` in `scripts/build.py` to perform field-wise merge before deciding to suppress. Add helper `_merge_seed_into_curated(seed, curated)` that performs the merge in-place on the curated dict.
  2. **No per-coin data file changes** — merging happens at build time; data files keep current shapes.
  3. Add `--debug` output showing per-coin merge stats (N seed sources added, N field values appended).
  4. Update §0a / §9a documentation references where they describe suppression.

**Design questions:**
  - Which fields auto-merge? Proposed: `sources[]`, `weight_rough_g[]`, `fineness[]`, `diameter_mm[]`. NOT auto-merge: `nominal`, `fuss`, `phase`, `kind`, `metal`, `mint` (curator-level fields, conflicts indicate real issues).
  - Conflict resolution: curated always wins on scalar / curator-level fields. Seed contributes only as augmentation.
  - Per-source dedup: when seed and curated share an existing `sources[]` URL, skip adding duplicate.

### AR. 🔴 c7h42 8.428g Numista typo cleanup — pending §AL  *(opened 2026-05-14)* *(est: small once §AL lands)*

**Surfaced.** §AE weight-mm guard-survivor investigation 2026-05-13 / 2026-05-14. Single confirmed weight-mm pair: `dk-hede-c7h42` seed vs `sh::km-128-chr-v-1787` curated. Curated `weight_rough_g[]` carries outlier `8.428` g (Numista N#108979 transcription error, already noted as such in coin's `note` text); cluster around 6.129 g. Min/max ratio 0.724 < 0.75 → weight-mm guard fires → keep both.

**Resolution path:** when §AL anomaly-field design lands, tag the `8.428` entry with `anomaly: source_error`. Guard logic in `build.py` will exclude it from min/max computation; ratio normalises; seed properly suppresses.

**Paused** until §AL has user verdict on field name + enum values (3 candidates per state listed in §AL body). No standalone action — this entry exists solely to track that c7h42 is a known case that the §AL implementation must cover when it lands.

### AS. 🔵 Verbatim-quote-as-locator sweep across all refs  *(opened 2026-05-14)* *(est: large)*

**Surfaced.** User direction 2026-05-14: «треба вказати точну цитату з ресурсу який власне і означає посилання, адже посилання завжди на якийсь конкретний уривок з тексту. проаналізуй чи це стандартна практика для посилань». Verified — standard academic practice (Chicago Manual, MLA, Wikipedia citations) supports / encourages short verbatim quotes as identifying locators in footnotes/endnotes; especially essential for unpaginated web sources where the quote IS the only locator.

**Rule updated in CLAUDE.md §5a** (same commit that spawns this entry):

  - Every ref body must carry a verbatim quote (≤ 25 words, in quotation marks) of the exact passage the citation backs. Locator function — the reader sees what claim the ref backs without re-reading the source.
  - Page-hint requirement scoped to paginated sources only; unpaginated single-page web articles use the quote as locator instead.

**Sweep workload (128 existing refs across 12 files):** every ref needs verification that it carries a verbatim quote, and the quote needs to come from the actual cited passage (not invented). Per-file inventory:

  | File | Refs |
  |---|---:|
  | `german_fuesse-references.yml` | 47 |
  | `schleswig_holstein-references.yml` | 38 |
  | `denmark-references.yml` | 28 |
  | `holstein_schauenburg-references.yml` | 4 |
  | `lubeck-references.yml` | 4 |
  | others (single-entry files) | 7 |

**Plan.**

  1. **Audit script first** — `scripts/audit_refs_quotes.py`: walk every ref body, look for `«…»` / `"…"` / `‹…›` quote markers, flag refs without one. Output baseline missing-quote count + per-file breakdown. Expected: most or all 128 refs currently lack the quote (the old rule didn't require it — quotes lived in the citing prose, not the ref body).
  2. **Per-ref sweep** — for each flagged ref:
     a. Open the source URL (or paper-via-secondary).
     b. Identify the passage that backs the inline citation (find where the prose cites the ref via `<sup>[N]</sup>`; the cited claim points to a specific source passage).
     c. Extract a ≤ 25-word verbatim quote of that passage.
     d. Insert into ref body in all three languages — quote stays in source language; surrounding scaffolding (publisher, year, scope) translates.
  3. **Wire into pre-commit / audit_health** — after baseline sweep complete, `audit_refs_quotes.py` runs as advisory (eventually hard-block once 0 missing).
  4. **Update CLAUDE.md examples** in §5a with the new shape (quote inline, page-hint conditional).
  5. **Existing «forbidden long quotes (>25 words)» clause** stays — the 25-word cap remains binding; the rule shift is only «quote is now REQUIRED, not OPTIONAL».

**Per-ref effort:** ≈ 2-5 min each (open source, locate passage, extract quote, translate scaffolding). 128 refs ≈ 4-10 hours total. Per-session bite: 10-20 refs at a time.

**Cross-references:** §AG (page-hint sweep) overlaps for paginated sources — there the quote AND page-hint are both required; for unpaginated sources only quote applies. §AS may consume / supersede §AG once both rules are universally enforced.

### AL. 🟡 Structured `anomaly` field on list-form weight / fineness / diameter entries  *(opened 2026-05-13, promoted to High 2026-05-15)* *(est: medium)*

**Promoted to High 2026-05-15.** Originally filed under Normal, but blocks two High-priority entries: §AR (🔴 paused «pending §AL») and §AE (closure-pending — practical fixes for the 9 metal-mm + 5 weight-mm guard survivors all subsumed under §AL implementation). Until §AL lands, both stay frozen — so its effective priority is the maximum of its dependents.

**Surfaced.** User direction 2026-05-13 while answering §AE design question: the existing weight-mm guard tightening would benefit from a structured field instead of free-text source-string parsing («likely transcription error»). User identified three real cases that need distinct handling:

  - **Numista recorded Feingewicht as Bruttogewicht** — confirmed cataloguer error in source. Should be excluded from min/max guard computation.
  - **Wide-but-legitimate specimen variance** — large weight spread across surviving specimens, all real. Should remain in min/max.
  - **Unusual specimen of unknown status** — value is non-standard but we don't yet know if it's an error or genuine outlier. Conservative inclusion in min/max with future review.

**Proposed shape — naming open for discussion.** Add an `anomaly` field (optional) to each list-form entry under `weight_rough_g[]` / `fineness[]` / `diameter_mm[]`:

```yaml
weight_rough_g:
  - value: 6.93
    source: Bruun Part I, lot 1133
    anomaly: source_error    # explicit: known mis-recording in catalogue
  - value: 5.20
    source: Hede c4h47
    # no anomaly = normal entry, included in min/max
  - value: 5.19
    source: Numista
    anomaly: source_error    # Numista mis-transcribed Feingewicht as Bruttogewicht
```

**Enum options (3 candidates per slot — pick one set):**

| User's draft | Option A (concise) | Option B (descriptive) |
|---|---|---|
| `probably_source_error` | `source_error` | `confirmed_source_error` |
| `acceptable_anomaly` | `wide_variance` | `legitimate_specimen_variance` |
| `unknown` | `unverified` | `unconfirmed_outlier` |

**My (claude's) recommendation.** Option A — concise enough for YAML readability, semantically distinct. Field name `anomaly` is short and self-explanatory. Drop «probably» from `source_error` because by the time we tag it, we're confident enough to act on it (the «probably» implicitness lives in the broader research practice, not in the structured tag).

**Guard logic update (`scripts/build.py` weight-mm and metal-mm guards).** When computing min/max for the weight-ratio < 0.75 check, **exclude entries with `anomaly: source_error`**. `wide_variance` and `unverified` entries stay in min/max — the first because they reflect real specimen spread, the second because we don't yet have grounds to drop them.

**Schema update (`scripts/lib/schema.py`).** Add `anomaly: Literal["source_error", "wide_variance", "unverified"] | None = None` to the list-form measurement entry models.

**Migration step.** Existing `weight_rough_g[]` entries with source-strings containing «likely transcription error» / «anomalous» / «mis-transcribed» — convert to `anomaly: source_error` on the offending entry; keep the human-readable note in `source` text. Sweep `data/locations/*.yml` for the 5 known weight-mm survivors (TODO §AE inventory) + any matching free-text markers.

**Action.**

  1. Confirm field name + enum values (3 strings) with user.
  2. Add to `scripts/lib/schema.py`.
  3. Update guard logic in `scripts/build.py` `_merge_seeds_into_raw`.
  4. Migrate ~5 known entries from free-text marker to structured field.
  5. Add an audit-section in `audit_health.py` that flags entries with free-text anomaly markers in source-strings (so the next surface case gets caught early).

(§BG closed — see `## Done` section below.)

### BN. 🟢 Bruun extraction completeness — verify all DK + possessions Bruun lots harvested into seed / curated  *(opened 2026-05-17)* *(est: medium-large)* *(type: audit + seed-build + data)*

**Surfaced.** Phase-1 raw-cache coverage table (2026-05-17) showed Bruun as the project's single deepest source for the Denmark-Norway realm (1238 unique DK+NO coll-ids cached across Parts I-IV). But on-disk extraction shape:

  - **38 entries** in `data/seed/bruun/denmark_pre_1541.yml` (Bruun seed limited to 1514-1541 sub-window per §AZ Tier-1 design).
  - **367 DK+NO coll-ids cited** in `data/locations/*.yml` (manual curation work, e.g. `bruun-8082-frederik-1830` on lauenburg.yml).
  - **871 DK+NO coll-ids NOT cited anywhere** in our YAMLs — that's **70% of the Bruun DK+NO corpus uncited**.

For Schleswig-Holstein-mint lots specifically (Glückstadt / Altona / Sonderburg / Schleswig / Husum / Rendsburg / Plön / etc. mentioned in lot `mint` field or `body_excerpt`):

  - **225 lots** mention an SH-mint
  - **129 cited (57%)** + **96 uncited (43%)**

Per-period DK+NO Bruun coverage (1238 lots with year):

  | Period | Bruun cached | Bruun cited (rough) |
  |---|---:|---:|
  | 1514-1541 | 53 | 38 in seed + ~10 curated ≈ 48 |
  | 1541-1582 | 35 | ~12 cited |
  | 1582-1591 | 3 | ~2 cited |
  | 1591-1608 | 52 | ~25 cited |
  | 1608-1814 | 795 | ~245 cited |
  | 1814-1914 | 185 | ~85 cited |

Each Bruun lot carries weight + grade (NGC/PCGS) + auction provenance — strong primary-source citations per CLAUDE.md §5. Leaving 871 lots uncited is the equivalent of having a museum catalogue open on the desk and never looking at it.

**Why now.** Two complementary pipeline paths exist already:

  - `scripts/maintenance/build_bruun_denmark_seed.py` — produces `data/seed/bruun/denmark_pre_1541.yml`. The script is scoped to pre-1541 only. Generalising to a full `data/seed/bruun/denmark.yml` (or split DK / Norge / SH per-location) would auto-fold the 1200+ uncited lots into our seed-merge pipeline at next build.
  - `scripts/lib/seed_merge.py` (§BL) makes the merge-aware regen safe — curated `fuss`/`note` flips survive.

So the mechanical pipeline is ready; the gap is purely «no seed file exists for post-1541 Bruun».

**Done criterion.**

1. **Audit lay-out.** Enumerate the 1238 DK+NO Bruun lots → per-period bucket × per-location (DK vs Norge vs SH-by-mint) breakdown. Output: `docs/research/bruun_extraction_audit.md` so the next session sees the gap structure at a glance.
2. **Generalise the seed builder.** Rename `build_bruun_denmark_seed.py` → `build_bruun_seed.py` with `--location` flag (matching the §BK pattern for NumisMaster). Emit:
     - `data/seed/bruun/denmark.yml` (post-1541 DK + Norge-under-Danish-rule, since both fold into the Denmark-Norway realm per existing convention).
     - `data/seed/bruun/schleswig_holstein.yml` (lots where mint OR body_excerpt mentions an SH mint — region tag in Bruun is sometimes wrong, body_excerpt is ground truth).
     - Keep the legacy `denmark_pre_1541.yml` until curation is fully migrated.
3. **Location-side prep** (per §BK pattern):
     - `data/locations/denmark.yml` already has `seed_unsorted.numismaster` + `seed_unsorted.hede`; add `seed_unsorted.bruun` phase with appropriate `hintergrund` text.
     - `data/locations/schleswig_holstein.yml` already has `seed_unsorted.numismaster` from §BK; add `seed_unsorted.bruun` phase.
4. **Build verification.** Run `build.py --validate-only` → 0 errors. Spot-check 3-5 seed entries against the original Bruun lot data (verify weight, year, mint match).
5. **Spot-check SH overlap.** Of the 225 SH-mint Bruun lots, 129 are cited — verify the 129 citations point at the same coll-id (no parser-bug shifting Bruun-id to wrong location). Surface mis-attributions as separate sub-TODOs.
6. **Document closure** with count delta (new seed entries added, manual curations preserved, any conflicts surfaced).

**Sequence note.** §BN is independent of §BM (IKMK) and §BH (Hede audit) — can run in any order. But it does benefit from §BL (merge-aware seed builders, closed 2026-05-16) — without §BL this would risk wiping the 367 already-curated Bruun citations on first regen.

---

### BM. 🟢 IKMK Berlin completeness audit — DK extraction + SH coverage verification  *(opened 2026-05-17)* *(est: small)* *(type: audit + data)*

**Surfaced.** Phase-1 raw-cache coverage table (2026-05-17) showed IKMK as a small-but-non-zero source for Denmark (41 records via `_match_denmark.json`) but with **0 actually cited in `data/locations/denmark.yml`** — an extraction gap. For Schleswig-Holstein the situation is the opposite: `_match_schleswig_holstein.json` shows 42 strict matches + 23 new-Lange-variants (65 IKMK records total), of which 32 are already cited in `schleswig_holstein.yml` — so 10 strict-matched IKMK records + 23 new-Lange-variants remain potentially unintegrated.

IKMK (Münzkabinett Berlin) is primarily a non-DK collection (~7088 records, mostly ancient Greek + Roman + Ottoman), so the absolute counts are small. But each IKMK record is **museum-grade primary attestation** with weight, fineness, photograph, and inscription transcription — exactly the data we'd otherwise cite via auction catalogues. Letting 41 DK records sit uncited is a §5 «source hierarchy» violation (museum catalogue > auction catalogue per the CLAUDE.md hierarchy).

**Why now.** Cheap to verify (the `_match_*.json` index already lists candidates with `ikmk_id` + `ikmk_year` + `ikmk_nominal`); no new fetch required. If we don't capture these citations now, future curators may unknowingly re-cite the same coin from a weaker source (auction lot) and miss the museum primary attestation.

**Done criterion.**

1. **DK extraction.** For each of the 41 IKMK records in `_match_denmark.json`:
     - Strict matches (5): add IKMK as `sources[type=museum]` ref on the matching curated coin entry.
     - Fuzzy matches (13): manual review — likely same coin, confirm + cite as strict.
     - Weak candidates (23): more careful manual review — may be sibling KM-variant or different sub-type. If it's a NEW coin not in denmark.yml, add as a new curated entry sourced from IKMK; otherwise skip / annotate.
     - Aim: ≥18 strict+fuzzy citations added; the 23 weak-candidates resolved (cited or annotated as «not a match» in a follow-up note).
2. **SH coverage verification.** Of the 65 IKMK SH records:
     - The 10 strict-matches NOT yet cited in `schleswig_holstein.yml` — add IKMK as `sources[type=museum]` ref. Quick check: maybe they're already cited under a different IKMK id format (e.g. `permalink` URL not raw id).
     - The 23 new-Lange-variants collapse to «1 unique new Lange number» per the index totals — investigate that one outlier: is it a genuinely new SH coin worth adding, or is it noise from the matching heuristic?
3. **Non-DK / non-SH IKMK with mission-scope relevance.** Spot-check the IKMK cache for entries that match other in-mission locations we haven't indexed (`_match_bremen_verden.json` / `_match_holstein_schauenburg.json` / `_match_lauenburg.json` / `_match_lubeck.json` / `_match_osnabrueck.json` already exist) — confirm each is processed similarly. Surface any gap as separate sub-TODOs.
4. **Document closure** in this entry's body: count delta per location, list of IKMK ids cited / annotated / skipped.

---

### BH. 🟢 Hede cache completeness audit — verify danskmoent.dk fully harvested, including non-DK content  *(opened 2026-05-15, expanded 2026-05-17 per user)* *(est: small-medium)* *(type: audit)*

**Surfaced.** Hede 1971 (DK realm) + §BG (Norge sub-catalogue, closed 2026-05-17) gave us 836 cached pages covering Denmark + Norway-under-Danish-rule. Coverage is now visually excellent (566 Hede entries in 1608-1814 alone, see Phase-1 coverage table 2026-05-17). But two open questions remain before declaring Hede source «100% mirrored»:

  1. **Did we miss any Danish-royal overview / per-coin pages?** The §BG closure proved that `norge/` subtree had been invisible to the discover regex; what other URL-subspace might still be invisible? E.g. uncovered Hede sub-suffix patterns (overview part-numbers 11+, undated «u. år» dedicated pages, joint-issue cross-reference sub-pages), older rulers we haven't probed (Hans pre-1513, Erik VII, Christoffer of Bayern — danskmoent.dk has scattered Hede mentions outside the c1..c10 / f1..f9 backbone).

  2. **Does danskmoent.dk cover OTHER countries/regions beyond Denmark + its possessions?** And if yes — are any of those relevant to our mission scope (Schleswig-Holstein-as-Danish-duchy, Hamburg-as-Danish-tariff-counter, Sweden under Christian II)? Quick visual scan of the site root (`https://www.danskmoent.dk/index.htm`) is the cheapest answer — if there's a Swedish / Norwegian-independent / Holstein-Lange page subtree, we should at least know it exists.

**Why now.** Phase-1 coverage table (2026-05-17) shows Hede as the project's densest single source for 1541-1914 (768 DK+NO entries). A 5-10% gap in Hede coverage would translate to dozens of missing reference coins on per-location pages. Cheap to verify; expensive to discover later via a one-off curator query.

**Done criterion.**

1. **Danish-royal subtree completeness.** Re-run `scripts/fetch_hede.py discover` against the live site. Diff the fresh manifest against the committed `_manifest.json`: any new overview URLs OR new per-coin links not previously captured → fetch them. Special probes:
     - `c{N}hede{P}.htm` for `P` in `12..15` (current cap is 11; cheap to bump).
     - `chr/c{N}h{M}.htm` / `fr/f{N}h{M}.htm` for `M` going past each ruler's known highest cached number + 50 (catch unreferenced sub-pages).
     - `hans/`, `erik/`, `christofer/`, `c2/` (Christian II) — pre-Christian-III rulers' subtrees probed in §AZ context already; verify the `_manifest.json` mentions them.
2. **Non-DK subtree probe.** Spider `https://www.danskmoent.dk/index.htm` and `/oversigt.htm` (whatever the live nav-root is). Inventory every distinct path-subfolder (`sverige/`, `kongeriket/`, `tyskland/`, etc.) — fetch each subfolder's index page → identify which (if any) cover a region in our mission scope. Surface findings here; if a non-DK subtree is in-scope (e.g. Schleswig-Holstein dedicated pages we missed because the SH coverage came from Lange, not Hede), open a separate harvest TODO.
3. **Cross-reference Hede 1971 + 1977 extension printed indices** (paper or scan, if accessible) against the cache. Count delta per ruler — Hede's printed Hede-numbers per king are well-defined; missing any printed-index entry from our cache = a gap. Surface gaps as separate sub-TODOs.
4. **Document closure** in this entry's body: count delta, any new pages, list of non-DK subtrees found + scope-relevance assessment.

## Normal priority

### AK. Flip `mint_verified` to true for seed entries whose Hede source explicitly states the mint  *(opened 2026-05-13)*

**Surfaced.** User flagged `dk-hede-f2h31` (Hede# 31 / Sieg# 32.1 / Schou# 27 / Fr# 2 — 1 Søsling Lybsk 1566, Frederik II): currently `mint: Flensburg` + `mint_verified: false` → renders as «Flensburg (?)» in the table. But the Hede source page (https://www.danskmoent.dk/fr/f2h31.htm) explicitly names «Flensborg» (Danish spelling of the same German «Flensburg»). The mint IS source-attested; the `(?)` marker is wrong.

**Root cause.** `scripts/maintenance/build_hede_denmark_seed.py:633` sets `cm["mint_verified"] = False` as a parser-heuristic default («not flipped here»). The post-build sweep that flips the flag against the actual Hede page text never happened systematically — so today, **604 seed entries in `data/seed/hede/denmark.yml` carry `mint_verified: false`** (count via `audit_health.py` data-completeness section), even though the majority of them have an explicitly-stated mint in the Hede source.

**Distribution of those 604 (top 12 by mint label):**

| mint | count |
|---|---:|
| Kopenhagen | 479 |
| Glückstadt | 47 |
| Altona | 33 |
| (Kopenhagen, Altona) — joint | 18 |
| Frederiksborg | 5 |
| Rethwisch | 5 |
| Hadersleben | 4 |
| Flensburg | 3 |
| Rendsburg | 3 |
| (Kopenhagen, Kongsberg) — joint | 3 |
| Helsingør | 2 |
| (Altona, Poppenbüttel) — joint | 2 |

Most of these are post-1660 Kopenhagen issues where the Hede page lists «Kjøbenhavn» as the mint by name + cites the mintmaster initials. Pre-1660 issues from Glückstadt, Flensburg, Hadersleben likewise carry explicit mint statements on Hede pages.

**Plan.**

  1. **Starting case `dk-hede-f2h31`**: open the cited danskmoent.dk page, confirm «Flensborg» appears as mint, flip `mint_verified: false → true` in seed. The German form «Flensburg» stays in the YAML (per `data/i18n` policy: mint names use standard academic spellings identical across languages; «Flensborg» on the Danish page is the same place).
  2. **Sweep the other Flensburg / Hadersleben / Rethwisch / Frederiksborg / Rendsburg / Helsingør entries** (~22 entries) — each carries an explicit mint in the source page. Flip the flag.
  3. **Joint-mint entries** ((Kopenhagen, Altona), (Kopenhagen, Kongsberg), (Altona, Poppenbüttel)): the seed records a tuple because the source attests two mint locations. Confirm against Hede page, then flip if the joint statement matches.
  4. **Kopenhagen / Glückstadt / Altona buckets** (~559 entries combined): sample 10 entries per bucket, confirm each Hede page explicitly states the mint, then batch-flip the bucket. The fast path: write a one-off `scripts/oneoff/flip_mint_verified_from_hede.py` that parses each seed entry's Hede cache JSON (`scripts/cache/hede/<hede_volume><hede_num>.json`) for the canonical mint string and flips the flag when source attests.
  5. **Reserved cases**: any seed entry where the Hede page does NOT state the mint (or the parser-heuristic guessed wrong) stays `mint_verified: false`. These are the legitimate `(?)` rendering — not all 604 are bogus.
  6. **Audit follow-up**: add a section to `audit_health.py` (or extend the seed-state section) that flags «mint_verified=false entries where the Hede cache contains the mint string verbatim» — surfaces remaining sweep candidates without re-running the full builder.

**Quick win.** The 22 non-Kopenhagen/Glückstadt/Altona entries (Flensburg, Hadersleben, Rendsburg, etc.) are the most visible `(?)`-rendered cases on smaller-mint coin pages — fixing those first cleans the most obvious incorrect markers; the large Kopenhagen bulk can follow when the scripted sweep is in place.

---

### AJ. Year-aware coin sort comparator (single year vs range, range vs range)  *(opened 2026-05-13)*

**Surfaced.** User direction 2026-05-13. The web-rendered per-phase tables currently sort coins by `(year_first, id)` lexicographically (`scripts/lib/categorize.py:158`). When the table mixes single-year coins with multi-year-range coins (`year_label: "1646, 1648"`, `"1603-1613"`, `"1646, 1648-1651"`, etc.), the naive sort produces awkward orderings. The user's three-case rule virtually merges N range segments into one big interval `[min, max]` across all segments, then compares cases as follows.

**Comparator rule (canonical statement — destination CLAUDE.md or scripts/lib docstring per final implementation choice).**

Pre-step: each coin's effective year-span is `[span_min, span_max]` where
  - single year `Y` → `[Y, Y]`,
  - any range or comma-list (`year_ranges: [[a,b], [c,d], …]`) → `[min(a, c, …), max(b, d, …)]`.

A coin is **single-year** when `span_min == span_max` AND the source `year_label` carries one numeric year only (not a range that happens to be length-1).

A coin is **range-coin** otherwise.

Comparator for two coins X, Y:

  1. **Both single-year** — compare `span_min` (= the year). If equal, fall back to a stable tiebreaker (`id`).
  2. **One single-year, one range** — compare the single coin's year against the range coin's `span_min`. If equal, **single-year wins (sorts before range)**. (User's wording: «екземпляр1 йде раніше в списку за екземпляр2».)
  3. **Both range-coins** — compare `span_min` first; if equal, compare `span_max`. If both equal, stable tiebreaker (`id`).

**Implementation site.** `scripts/lib/categorize.py:158` — replace the `key=lambda c: (c.raw.year_first, c.raw.id)` lambda with a `functools.cmp_to_key`-wrapped comparator implementing the three cases above. The `Coin` schema already carries `year_first` + `year_last` + `year_ranges` + the structural distinction between single-year (`year_ranges` length 1 with `a==b`) and range-coins (everything else), so no schema change.

**Plan.**

  1. Add the `cmp_year_aware(c1, c2)` function in `scripts/lib/categorize.py` (or extract to a helper in `compute.py` if cleaner). Cover the three cases + the «single wins ties with range at the same min» exception.
  2. Replace the existing `coins_in_phase.sort(...)` call.
  3. Verify the rendered table for a Denmark phase that has a mix (e.g. Christian IV phases with several range-coins like KM-44 1608-1621 + single-year specimens) before / after the change.
  4. Codify the rule in CLAUDE.md or a scripts/lib/categorize.py docstring so future schema-additions (e.g. multi-disjoint-range coins) don't silently regress.
  5. Add an audit-section in `audit_health.py` to spot inversion cases (current sort puts a range-coin with `min=1646` before a single-year `1646` — should be the other way after fix).

---

### AI. Apply Intra-sub-variant thinning to coins with > 4 Bruun specimens  *(opened 2026-05-13)*

**Surfaced.** User direction 2026-05-13, surfaced by `dk-tid-163070` (1 Speciedaler 1608-1621 Christian IV, KM-44, Denmark): 7 `weight_rough_g` entries total, of which **6 from Bruun PDF lots** (Parts I-IV). The `audit_health.py` §«Specimen thinning (§9a)» «Bucket candidates ≥5» signal classifies entries by source token and flags any (coin × resource) bucket of ≥5; currently it lists 5 SH IKMK buckets, but doesn't yet flag Bruun-source clusters because the existing CLAUDE.md §9a thinning rule was codified for IKMK over-collection from one Stempelvariante (Berlin holds N specimens of the same Lange-sub-type → only min / middle / max are informative).

**The issue for Bruun.** When a single coin has > 4 Bruun specimens from across Parts I-IV, the intermediate weights between min and max similarly contribute no additional information about the standard's variance envelope — they are noise from over-sampling Bruun's auction-catalogue holdings. Same shape as IKMK over-collection, different resource.

**Rule update.** Extend CLAUDE.md §9a «Intra-sub-variant thinning» to explicitly cover Bruun in the bucket-threshold rule. Current §9a wording — «when one coin entry has ≥5 `weight_rough_g` entries from a *single resource* (most often IKMK Berlin) within a single Stempelvariante sub-group» — already nominally covers Bruun, but the canonical decisions in `scripts/maintenance/thin_intra_subvariant_specimens.py` are all IKMK. The two adjustments needed:

  1. **Lower threshold for Bruun specifically: > 4 Bruun specimens.** The user's framing «де bruun джерел > 4» suggests the threshold for Bruun should be > 4 (i.e. ≥ 5 — consistent with the general rule), not stricter. Treat as same threshold; the canonical text just needs to name Bruun explicitly alongside IKMK so the rule isn't read as IKMK-only.
  2. **Sub-variant grouping for Bruun.** IKMK's `literatur` field carries the Lange sub-variant tag; Bruun lot records carry an analog signal in the `refs` field (Hede sub-letter, Lange sub-letter, sometimes Schou). Define the sub-variant bucket for Bruun-source thinning as «entries sharing the same Hede-sub-letter OR same Lange-sub-letter». Without this grouping rule, the bucket would over-aggregate (e.g. 6 Bruun lots split across 3 Hede sub-letters of 2 each — none of the buckets crosses the threshold, no thinning).

**Action.**

  1. Extend CLAUDE.md §9a's text to name Bruun explicitly alongside IKMK + describe the Bruun sub-variant tag source (Hede/Lange sub-letter from the `refs` field).
  2. Sweep all coins in `data/locations/*.yml` where Bruun-source `weight_rough_g` entries ≥ 5 within one sub-variant. For each, apply min / middle-by-index / max preserving the `bruun_collection_id` / `bruun_part` / `bruun_lot_no` / `bruun_page` citation for retained entries; discard intermediate entries plus their matching `sources[]` URLs (per the existing §9a operational shape).
  3. Encode the decisions in `scripts/maintenance/thin_intra_subvariant_specimens.py` (extend `DROPS` dict; the function `_filter_coin` already handles Bruun source-strings since they share the «Bruun II, lot 11304» shape with IKMK's «IKMK Berlin, Inv. NNNN»).
  4. Re-run `audit_health.py --section thin` to confirm zero Bruun bucket-flags remain (or document why a given bucket legitimately stays — different sub-variants in same Hede page).

**Starting case: `dk-tid-163070`.** Inspect the 6 Bruun entries' Hede sub-letter + Lange sub-letter from their `bruun_part` + `bruun_lot_no`; group by sub-variant; apply min/middle/max per sub-variant bucket of ≥ 5.

---

### AH. Re-evaluate «Numista API budget» rule on 2026-06-01  *(opened 2026-05-13)*

**Surfaced.** CLAUDE.md «Numista API budget — ASK before bulk-fetching (May 2026 only)» is explicitly time-scoped: «applies through May 2026 only». The user's monthly quota resets June 1 and the rule may be relaxed or dropped.

**Plan.** On the first session in June 2026 (or whenever the current date crosses 2026-05-31, whichever comes first):

  1. Open CLAUDE.md and locate the «Numista API budget» section.
  2. Ask the user the simple binary: «June reset has landed — keep the ≤5-calls-then-ASK rule, or relax it / drop entirely?»
  3. Either remove the section, soften it («ASK if planning > ~50 calls»), or re-scope it to «June 2026 only» with the same self-deletion mechanism.

**Why this is here.** The rule's own preamble already instructs «ask the user whether this rule still stands before applying it» when today's date is past 2026-05-31, but a TODO entry surfaces the reminder regardless of whether the rule is about to be applied — useful if the next session doesn't immediately reach for the Numista API.

### Z. Evaluate numismaster.com as a project resource  *(opened 2026-05-13)*

User flagged <https://numismaster.com/> for review. Check whether the site offers material we don't already cover via Bruun PDFs / Numista / ucoin / IKMK / danskmoent.dk — typical questions to answer before deciding inclusion:

  - **Coverage scope.** Does it have Danish / Schleswig-Holstein / Hamburg / Lübeck / German-states content from 1559-1914? Sample 5-10 lookups against our existing curated KMs (e.g. KM-25 SH 1640 Søsling, KM-86 DK 1624-25 1 Hvid, KM-130 SH 1787 ⅓ Specie) — does numismaster surface them with usable data?
  - **Data quality vs Numista.** Is it primary-source-curated (museum-grade) or user-edited (Numista-tier)? Sister-site of Numismatic News (Krause Publications heritage) — likely Krause-derived which OVERLAPS our existing Krause-via-Numista coverage rather than adding new signal.
  - **Access policy.** Robots.txt, ToS, scraping framework. Most Krause-heritage sites are commercial; check whether catalogue lookups are gated behind subscription or open.
  - **Cross-source corroboration value.** Even if data overlaps Numista, an independent Krause-rooted source can break Numista-user-edit ties on contested weights / KM-numbers (the kind of cases logged in `docs/SOURCES.md` §13.1).
  - **Existing precedent.** We already have CoinFactsWiki (referenced from SH ref `coinfactswiki.com`), CoinVarieties, Greysheet — comparable tier. Numismaster fits the same neighbourhood; the question is whether it's strictly additive.

Outcome buckets:
  - (a) STRONG ADD — surfaces data we lack → integrate into source hierarchy (CLAUDE.md §5) at appropriate tier + `docs/SOURCES.md` entry.
  - (b) WEAK ADD — corroboration value only → mention in SOURCES.md «aggregators» section without elevating in the §5 tier list.
  - (c) SKIP — pure Krause-restatement → note in SOURCES.md as «evaluated, redundant» so future sessions don't re-evaluate.

Defer the evaluation until a session that touches a piece of contested data (a weight outlier, a KM-attribution conflict) — that's when independent corroboration is most useful and the evaluation pays off immediately. Until then, NOT used.

### Y. Fuß-event vs coin-data span audit (timeline-bar accuracy)  *(opened 2026-05-13)*

**Surfaced during.** Verifying that timeline bars («Standard / Karbung / im Umlauf» — status / mint / circulation layers) on the Denmark + SH pages reflect the post-2026-05-13 data state. The `guldkrone` Fuß was the clear case from this session's «latest findings» — its anywhere-axis events were extended from 1655 → 1618 to match the Christian-IV Guldkrone unification (commits `6f8fe18` + `4b28b8e` + `e050128`). While doing that walk, two PRE-EXISTING mismatches surfaced — not from this session's work, worth their own audit pass:

**Mismatch 1: `kronemont_chr_iv` last_mint vs DK data — RESOLVED 2026-05-13**

  - `events.last_mint.anywhere = 1652`
  - DK coin span had been 1618-1675 (11 post-1652 entries, ruler Frederik III + Christian V).

Per PB-4 Δ-from-Soll comparison: all 11 entries computed to specimen-fein within ±0.5% of `kronemont` (10½-Krone-Fuß) Soll, vs ~-8% from `kronemont_chr_iv` Soll. Re-classified `kronemont_chr_iv → kronemont` with phase I (Frederik III 1665-1669, 8 entries) or phase II (Christian V 1671-1675, 3 entries). Closed via commit ahead. Verified: kronemont_chr_iv data span now 1618-1652 exactly matching events; kronemont coin count 54 → 65.

**Mismatch 2: `9_thaler` SH last_mint vs SH data**

  - `events.last_mint.anywhere = 1667`
  - SH coin span: 1567-1683 (single 1683 entry).

`km-105-chr-v-1683` (Christian V Glückstadt Krone). Two readings:
  - (a) The 1683 strike is mis-classified — it's actually `kronemont` not `9_thaler`. Likely; Glückstadt was minting under the post-Kipper Kronemønt by then.
  - (b) Glückstadt continued 9-Fuß longer than Royal Danish mainland, and the 1683 strike is the actual Holstein-axis last_mint. Less likely but possible; the SH events block already has its own `last_mint.holstein = 1629` which the SH page auto-syncs (via `derive_holstein_mint_overrides`) to match real data.

Fix: open `km-105-chr-v-1683`, verify against Hede / Bruun / Numista which Fuß it actually belongs to.

**Scope.** Walking the per-Fuß event boundaries against actual coin-data spans across all locations is a one-time audit; the regression should be wired into `scripts/audit_health.py` afterwards as a section so future Fuß-event drift surfaces in the dashboard. Today's check covers only Denmark + Schleswig-Holstein.

### X. Fix cross-language inconsistencies surfaced by `scripts/audit_i18n.py`  *(opened 2026-05-13)*

**Surfaced.** New cross-language detector `scripts/audit_i18n.py` (commit ahead) checks DE/EN/UK triples for 5 structural divergences:

  - **R1 missing translation** (35 errors) — entries where DE is filled but EN or UK is empty. All 35 sit in `data/locations/schleswig_holstein-references.yml` where many `entries[N].content.en` / `.uk` are stubs awaiting incremental translation (the file header notes this convention). Either complete the translations or convert the empty placeholders to a deliberate «(translation pending)» canonical marker that the linter recognises as accepted.
  - **R3 catalog-ref divergence** (33 warnings) — KM / Hede / Sieg / Lange numbers that appear in one language's text but not another's. Most cases are legitimate (one language renders «Hede-59» as a compound while another mentions only «59A»), but each warrants a glance — sometimes a real divergence (e.g. DE forgot to mention a Hede sub-number that the EN version cites).
  - **R5 Müntzfuß name translation** (8 errors) — UK notes use «-стопа» suffix translating «-Fuß» (forbidden per CLAUDE.md i18n policy: «Müntzfuß standard names NEVER translate, in ANY context»). Fix: replace «Krone-стопа» / «9¼-стопа» → keep period German form intact («Krone-Fuß» / «9¼-Thaler-Fuß»).

**Plan.**

  1. **R5 Müntzfuß-name fixes** (8 errors, mechanical): grep for «-стопа» / «-стопи» / «-стопу» in `coins[].note.uk` across all locations; replace each with the period German form intact.
  2. **R1 missing-translation strategy**: decide between (a) actually completing the 35 incremental translations, or (b) introducing an `incremental_translation: true` flag at the entry level that the linter recognises as deliberate-pending. Option (a) is more work but aligns with the «all three languages should be filled in role-3 prose» convention; option (b) preserves the existing file's «add incrementally» comment.
  3. **R3 catalog-ref glance**: per-case review of the 33 warnings; most resolve to legitimate phrasing differences but real divergences (DE-side gap) should be fixed.

Once the project starts clean (or with documented residual warnings), wire `audit_i18n.py` into the same pre-commit hook as `audit_prose.py`.

### W. Clean up §0z violations surfaced by `scripts/audit_prose.py`  *(opened 2026-05-13)*

**Surfaced.** The new prose-linter `scripts/audit_prose.py` (commit ahead) catches forbidden patterns per CLAUDE.md §0a/§0z/§2a/§2/§0b across all `data/**/*.yml` rendered-prose surfaces. First run reports **873 hits across 8 files** — most are real violations, not false positives.

**By rule:**

  - **§0z: 573 errors.** 552 of these = `verification_note` fields literally citing «CLAUDE.md §4» / «CLAUDE.md §0» in the tooltip text — a project-internal-meta reference that the role-3 numismatist-reader sees in the (?) tooltip but has no context for. Bulk-introduced by the canonical-fineness backfill (§R-style) where the auto-generated verification_note explained the inference with «Per Projekt-Konvention (CLAUDE.md §4) auf den kanonischen Müntzfuß-Wert … gesetzt». The fix is mechanical: rewrite to say WHAT (canonical-fineness-from-Müntzfuß-standard) without WHERE-IT'S-CODIFIED (CLAUDE.md §4).
  - **§2: 90 errors + 123 warnings.** Period-orthography violations in DE prose — modern «Taler» / «Münzfuß» / «Münzvertrag» / «Münzreform» that should be «Thaler» / «Müntzfuß» / «Müntzvertrag» / «Müntzreform». The 123 warnings include modern «Mark» (where period-correct is «Marck») and modern «bis» (where period-correct is «biß») — those are higher-volume and need manual judgment because some quoted text from Wikipedia legitimately uses modern spelling.
  - **§0b: 61 warnings.** «vermutlich» / «імовірно» / «presumably» / «likely» hedge words without explicit hypothesis marker. Each needs review: either label as hypothesis pending verification, or attribute to a period source's own uncertainty, or replace with a hard claim once verified.
  - **§2a: 17 warnings.** Sensationalist intensifiers («extrem», «величезний») — easy mechanical rewrite to quantified language.
  - **§0a: 9 warnings.** First-person plural («presumably») in EN prose — needs voice rewrite.

**Plan.**

  1. **§0z verification_note cleanup** (biggest single class). One-pass `scripts/maintenance/rewrite_verification_notes.py` that walks all coins, detects the «Per Projekt-Konvention (CLAUDE.md §X)» template, and rewrites to the role-3-clean form. Target rewrite:
     - Before: «Per Projekt-Konvention (CLAUDE.md §4) auf den kanonischen Müntzfuß-Wert (9_thaler, Anker 0.8889) gesetzt; Δ -1.31% gegen den Soll-Wert.»
     - After:  «Probe nicht direkt belegt; aus dem kanonischen Müntzfuß-Standard (9_thaler, Anker 0.8889) übernommen. Δ -1.31% gegen den Soll-Wert liegt in der Spezimen-Toleranz.»
  2. **§2 orthography cleanup** — sweep Taler→Thaler, Münzfuß→Müntzfuß, Münzvertrag→Müntzvertrag, Münzreform→Müntzreform in DE-only fields (`note.de`, `description.de`, `verification_note.de`, `entries[].content.de`). Mostly mechanical; «Münze» (the institution) stays; «Reichsmünz-» / «Kurantmünz-» compounds in banking context stay.
  3. **§0b hedge-word audit** — per-coin manual review. Each «vermutlich» / «likely» is either correctable (attribute to source) or needs an actual verification step (per CLAUDE.md §0b).
  4. **§2a + §0a** — small enough to fix inline as discovered.

**Operational integration (after cleanup).** Once the project starts clean, wire `audit_prose.py` into:
  - **Pre-commit hook** (`.githooks/pre-commit`) — refuse to commit when ERRORs are introduced.
  - **CI on push** — informational warning report for WARNINGs.

The lint rule set itself can keep growing as new anti-patterns are discovered; the rules list at the top of `scripts/audit_prose.py` is intentionally inline + scannable.

### V. Numista / ucoin cache coverage audit (no auto-merge pipeline yet)  *(opened 2026-05-13)*

Of our four research caches, only **Hede** has an end-to-end seed-
generation + auto-suppression pipeline (`scripts/maintenance/build_*_seed.py`
emits `data/seed/hede/<loc>.yml`; `_merge_seeds_into_raw` in
`scripts/build.py` folds it against curated `catalog.hede` refs). The
other three caches are accumulated but consumed ad-hoc:

  - **Numista** (`scripts/cache/numista/*.json`, ≈ 683 entries; ≈ 385
    mention Denmark): fetched via `scripts/fetch_numista_api.py`, used
    via `scripts/enrich_from_numista.py` to enrich existing curated
    entries that already carry a `catalog.numista` ref. **No
    discovery path**: Numista records not yet linked to a curated
    entry sit cold in the cache.
  - **ucoin** (`scripts/cache/ucoin/_url_index.json`, ≈ 6 300 entries
    across all covered countries; `period_*.tsv` for 11 period
    buckets): the only ucoin → curated linkage is hand-attaching a
    `dk-tid-NNNNN` id (or `sources[].url` ucoin URL) on a curated
    entry. **No discovery path** either.
  - **IKMK Berlin** (`scripts/cache/ikmk/*.json`, 7 000+ entries):
    fetched via `scripts/fetch_ikmk.py`, used as source attestation
    when the user manually attaches the IKMK ID. **No discovery
    path**.

Live numbers (counted over `data/locations/*.yml` 2026-05-13):

  - Curated entries citing a ucoin tid: **704 unique tids**.
  - Curated entries citing a Numista nid (`en.numista.com/N` or
    `N#NNN` form): **130 unique nids**.

So at most ~ 11 % (704 / 6300) of cached ucoin entries are linked to
curated coins, and ~ 19 % (130 / 683) of cached Numista entries.
The remainder — most of the cache — is invisible to the build and
to the researcher unless they happen to query the cache directly.

**Failure modes the gap is producing:**

  1. **Duplicate work**: a session sees a coin missing from the page,
     fetches it fresh from Numista (burns API quota — see CLAUDE.md
     «Numista API budget» rule), unaware the JSON is already on disk.
  2. **Silent under-coverage of locations**: cached ucoin/Numista
     entries for known KM types are ready to be promoted to curated
     entries but no audit surfaces «which Krause coins for Denmark
     have a cached ucoin record but no curated entry yet?».
  3. **Stale data drift**: when Numista updates a published value
     (weight, fineness, year range), our cache may have a newer copy
     than our curated entries — but we only notice when a session
     manually re-checks. No automatic divergence flag.

**Design sketch — two-step, audit-first then optional pipeline:**

Step 1: **Coverage audit script** (`scripts/audit_cache_coverage.py`).
  - For each cache (Numista, ucoin, IKMK), build a set of
    cache-record-ids.
  - For each `data/locations/*.yml`, extract the set of cited ids
    per cache.
  - Print three lists per cache:
      (a) **Linked** — in cache AND in curated.
      (b) **Cache-only** — in cache, NOT in curated. Candidates
          for promotion-to-curated, scoped to the cache-record's
          country / period.
      (c) **Curated-only** — in curated, NOT in cache. Indicates
          a stale cache or a fetch that failed; flag for re-fetch.
  - Country / mint filter: limit to Denmark, Schleswig-Holstein, etc.
  - Output formats: human-readable summary (counts + sample lines)
    + JSON sidecar for downstream tooling.

Step 2: **Seed generator** (mirror Hede's pattern; defer until
audit shows the gap is worth automating).
  - `scripts/maintenance/build_ucoin_seed.py` reads cache + emits
    `data/seed/ucoin/<loc>.yml` for cache-only records that map to
    the location's country.
  - `_merge_seeds_into_raw` extended with a parallel auto-suppress
    path that compares `sources[].url` ucoin URLs (or a dedicated
    `catalog.ucoin: 'NNNNNN'` field, easier to compare).
  - Same metal / weight / year guards as the Hede path.
  - Numista seed analogous: `scripts/maintenance/build_numista_seed.py`
    + `_merge_seeds_into_raw` extension for `catalog.numista` refs.

**Open design questions:**

  * **Where does `catalog.ucoin` live in the schema?** Currently
    ucoin linkage is implicit via `sources[].url`. A first-class
    `catalog.ucoin: 'NNNNNN'` field would make suppress / dedup
    queries trivial. Migration cost: walk every curated entry whose
    `sources[].url` matches `ucoin.net/.*tid=NNNNNN`, lift the
    id into the new catalog field.
  * **Numista discovery scope** — the cache covers ALL countries we've
    ever queried, including non-Northern-German states. Seed
    generation must scope by country/region so a Russian or French
    coin doesn't leak into a Danish seed yml.
  * **IKMK is harder** — IKMK records are individual specimens, not
    coin types. A single coin type can have N IKMK specimens. Coverage
    audit is meaningful; seed-style promotion isn't (we'd never want
    one curated row per IKMK specimen). The IKMK case is multi-source
    weight enrichment, not discovery — already handled per §9a.
  * **Promotion priority signal** — when a cache-only Numista record
    matches a known KM number not yet curated, promotion is easy
    (assign KM + fold). When the cache record has no KM reference,
    promotion needs the per-case methodology (case 9 style). The
    audit should rank cache-only records by how well they map to
    known curated infrastructure.

**Why this matters now.** The Hede dedup audit is closing
(case 9 of 46 done; bare-basename siblings being processed per-case).
When that's done, the next obvious quality lift is the cache-only
gap — there are hundreds of cached Numista / ucoin entries for KMs
that already exist on our pages but have no source citation, and
some that point at types we haven't yet documented at all. Adding
those is the highest-yield work after dedup.

**Out-of-scope (for first cut):**

  - Live cache re-fetch / sync (separate concern; respects API budget).
  - Bruun coverage — Bruun is already cross-matched via
    `scripts/cache/bruun/cross_match.json` and surfaced via TODO §F
    «Bruun fall-throughs». Don't duplicate.

Defer concrete implementation until current dedup audit closes — the
cache-only set won't shrink fast in the meantime, and the dedup work
is informing what the audit output should rank by.

### U. Per-specimen Δ-computation needs explicit weight+fineness lineage  *(opened 2026-05-13)*

When a coin entry carries **multi-source measurement fields** (weight
from one source, fineness from another, often more than one value per
field), the rendered Δ-from-Soll cell shows a single number — but the
HTML doesn't disclose **which `(weight, fineness)` tuple** went into
that number, nor which source backs each input.

**The failure mode.** A Bruun lot publishes a specimen weight but no
fineness. Numista publishes a fineness but no weight. Hede publishes
both as Soll values. The build picks weight from Bruun and fineness
from Hede (or Numista, or the canonical fuss anchor) and computes
Δ = (w · f − Soll) / Soll. The reader sees the single Δ number and
the tooltip showing the individual weight/fineness spans — but cannot
trace which combination produced the Δ. If a future audit notices
the Δ is off, there's no way to know without re-running the build
whether the issue is the weight choice, the fineness choice, or the
pairing logic.

**Example (case 9 c4h Hede 79 → KM-DK# 16.1):**
  - weight: 2.088 g (Hede Soll) + 1.78 g (ucoin observed) — Δ = −15%
  - fineness: 0.296 (Hede) + 0.298 (ucoin) — Δ < 1%
  - Soll for KM-16.1 in 9-Thaler-Fuß: 0.487 g fein → Soll weight at
    canonical fineness ≈ 1.645 g (if .296) or matches Hede's
    11.432 dlr / mark.

Which pair did the build use? Hede×Hede gives Soll-match (effectively
Δ ≈ 0). Bruun×Hede gives the −15% reading. ucoin×ucoin gives the
−15% reading. The rendered cell shows one of those; the reader has
no way to know.

**Design sketch for the fix:**

  1. **Build-time tagging of the chosen pair**. When `compute.py`
     picks the «active» measurement for Δ-computation (whatever the
     selection rule — first-source, source-priority, verified-wins,
     etc.), record both inputs *and* their source labels into the
     computed entry: `{w_value, w_source, f_value, f_source}`.
  2. **Render the pair in the Δ tooltip.** Replace the single Δ
     number's hover-tooltip («Soll-Feingewicht = X g; specimen = Y g»)
     with an explicit triple-line block:
     ```
     Δ basis:
       Gewicht  W g  ← <source1>
       Probe    F   ← <source2>
       gegen Soll-Feingewicht  S g (Fuß-Anker)
     ```
  3. **Audit-script support.** Add a new audit (either a new section
     in `scripts/audit_health.py` or a dedicated `scripts/audit_*.py`)
     to flag entries where the active `(w, f)` pair sits at the
     worst-Δ extreme of all possible pairings; that surfaces «we
     picked the pessimistic combination» as a quality signal.

**Open design questions:**

  - **Selection rule for «active» (w, f)** — currently appears to be
    «first in list» / source-order-of-write. Is that what we want?
    Alternatives: (a) verified-wins (mirrors §4 merge precedence:
    pick the entry with the strongest provenance for each field),
    (b) Soll-match-wins (pick the pair closest to canonical Soll —
    optimistic), (c) reader-toggleable (a dropdown «show Δ vs
    Hede / Bruun / ucoin» that re-computes on the fly).
  - **What to do when only one input has a single source.** No
    ambiguity — render normally with the one source.
  - **Cross-coin consistency.** Within one fuss/phase table, the
    same selection rule should apply to all rows so the Δ column is
    comparable. A reader-toggleable mode would need to apply
    site-wide, not per row.

**Why this matters.** Δ is the column that links data to standard —
it's the numismatic claim the artefact makes. A Δ without provenance
is a number the reader can't independently verify. The opaque-pairing
problem silently degrades the artefact's scholarly weight (§0a
«reader voice»: the rendered page makes a claim it can't show the
sources for).

**Out-of-scope (for first cut):**

  - Per-specimen Δ (one row, multiple Δ values for each pair) —
    visually overwhelming, defer.
  - Re-pairing across multiple specimens with different mintmark
    sub-variants (Hede 79A vs 79B might in theory have different
    Soll if their target marks differ) — for c4h79 they share a
    spec so this is moot, but the general case is a §8a problem.

Defer concrete implementation until current dedup-audit pass closes —
the audit will likely surface several more cases where this lineage
gap matters, and we'll have a better sample to inform the selection
rule.

### T. Keyword search across coins on a location page  *(opened 2026-05-13)*

Long location pages (denmark.yml renders ~1100 coins; schleswig_holstein
~320; growing) lack a primary discovery affordance for the coin table —
the reader has to scroll through fuesse / phases or use the browser's
native Ctrl-F (which matches blindly without coin-row awareness). A
purpose-built keyword search would let the reader jump directly to
any coin matching a query like «1 Speciedaler 1727», «KM 81», «Hede 115»,
«Schwabe», «Glückstadt», «Kroneskilling», etc.

Design sketch (to be refined):

**Search fields per coin** — pre-indexed at build time, fields concatenated
into one searchable haystack per row:

  - `nominal` (period-form, current rendering form)
  - `year_label`, `year_first`, `year_last`, all years in `year_ranges`
  - `ruler` (full canonical form + abbreviated variants — «Christian IV.»
    matches «c4», «Chr.IV», «Chr. IV», etc.)
  - `mint` (city name + alternative spellings — «Kopenhagen» / «København»
    / «Copenhagen»)
  - `catalog.km` (all KMs in the list; both DK and SH register tokens
    if cross-register), `catalog.hede` (all sub-letters), `catalog.sieg`,
    `catalog.schou`, `catalog.fr`, `catalog.dav`, `catalog.numista`,
    `catalog.others`, `catalog.bruun_*`
  - `fuss` + `phase` ids (lets queries like «kronemont_chr_iv» find all
    entries in that phase)
  - `note` text (per-language — search index respects the page's
    rendered language)
  - mint-master names / Mzz privy marks if mentioned in the note
    («Schwabe», «trekløver», «korslagte køller»)

**Index format** — JSON blob embedded near `</body>` (lean: one entry
per coin with id + concatenated lowercased haystack + 3-letter prefixes
for fuzzy first-letter matching). Or a JSON sidecar loaded lazily on
search-button click for slimmer initial page bytes. ~1100 coins × ~200
chars each ≈ 220 KB raw, ~50 KB gzipped — acceptable inline.

**UI options:**

  (a) **In-page filter**: top-of-table search input that hides non-
      matching rows + highlights matches; closing the search restores
      full table. Mobile-friendly. The natural surface for the
      «I have a specific coin in mind» case.
  (b) **Anchored search panel**: floating button (bottom-right, near
      the back-to-top button) that opens a modal with the input +
      result list (id, nominal, year). Click jumps to the row +
      highlights. Better for navigation-style queries («show me all
      coins matching X»).
  (c) **Both** — keyboard shortcut `/` (or `Ctrl-K`) opens the modal,
      while the table itself can also be filtered inline.

**Accessibility:**
  - Search input keyboard-focusable + visible label
  - Empty-state handling («no matches found»)
  - Reset / clear button
  - Result count shown («3 of 1107 coins match»)
  - Live-region announce for screen readers

**Edge cases to think through:**

  - Period-form vs modern-form denominations: a user typing «Speciedaler»
    should match entries showing «Speciedaler» / «Specie-Daler» /
    «Speciesthaler» / Danish «Speciemønt» variants. The index should
    fold these to a canonical lowercase form.
  - Numeric matching: «KM 81» / «KM-81» / «KM#81» / «km81» / «KM 081»
    should all hit the same row. Normalise both query and index.
  - Cyrillic / German ruler-name variants («Christian IV», «Кристіан IV»,
    «Chrystian IV»). Page language probably dictates which form to
    index, but accent-folding helps.
  - Should `verification_note` text be searchable? Probably no — it's
    methodological scaffolding, not coin content.

**Out-of-scope (for first cut):**

  - Fuzzy / typo-tolerant matching (Levenshtein etc.) — initial release
    is substring-match on normalised tokens.
  - Search across multiple locations from one page — single-page-scope
    only. The landing page may eventually want global search, but that's
    a separate concern.
  - Saved searches / shareable URLs (`?q=…`) — nice-to-have, defer.

**Implementation rough plan:**

  1. Build-time: extend `scripts/lib/render.py` to compute the per-coin
     search haystack and emit a `<script id="coin-search-index"
     type="application/json">…</script>` block in the rendered HTML.
  2. Client-side: extend `assets/app.js` with a search module that
     hydrates the index on first focus, applies a filter on
     keypress (debounced), toggles row visibility via a CSS class.
  3. Template: a new `<input>` in the location header (or just before
     the first fuss block); plus a `[no-match]` placeholder row.
  4. CSS: `.coin-row[hidden-by-search]` rule (display:none) +
     highlight-match span styling.

Defer concrete prototyping until a user pain-point trigger surfaces;
the implementation isn't large but the design space (UI form factor,
multilingual normalisation) deserves a focused turn.

### R. Backfill canonical fineness on fineness-missing coins  *(opened 2026-05-13)*

Many seed / partially-curated entries carry `fineness: null` (or
omit the field entirely) because the source — Bruun lot, ucoin
bulk, Hede page in the small minority of cases — published weight
but no fineness reading. For these we can frequently INFER a
canonical fineness from the Müntzfuß the coin belongs to and verify
the assumption via Δ-from-Soll arithmetic, IF the coin's other
fields (weight, year, nominal, ruler) pin it unambiguously to a
single fuss.

The procedure (already applied case-by-case to a handful of strict-
single-fineness Category-1 fuesse — reichsdukatenfuss .9861,
courantdukatenfuss .875, pistolenfuss .903 — see existing
verification_note prose on those entries) per CLAUDE.md §4:

  1. Identify the coin's intended Müntzfuß (sometimes obvious from
     ruler + nominal + year; sometimes ambiguous → skip).
  2. Pick the Müntzfuß's canonical anchor fineness if it has a
     single dominant value (Category-1 fuesse). Skip multi-anchor
     fuesse (Category-2/-3) — guessing wrong is worse than leaving
     `fineness: null`.
  3. Compute the implied Feingewicht = weight × anchor-fineness.
  4. Compute Δ = (implied_fein − soll_fein) / soll_fein.
     If |Δ| ≤ ±2 % (the project's specimen-tolerance envelope per
     CLAUDE.md §4), set:
       - `fineness: <canonical>`
       - `fineness_verified: false`   (forces the `(?)` marker)
       - `verification_note` explaining the inference + Δ value.
     If |Δ| > ±2 %, the assumption is incompatible with the
     sourced weight — leave `fineness: null`.

Automation candidate (build it once, run sweepwise):

`scripts/maintenance/backfill_canonical_fineness.py`
  - Walks `data/locations/*.yml`.
  - For every coin with `fineness: null` (or missing field), gathers
    `fuss`, weight, nominal, year, ruler.
  - Looks up canonical anchor fineness from `data/shared/fuesse.yml`
    via a new explicit-anchor field per fuss (e.g. `fineness_anchor:
    0.9861` for reichsdukatenfuss). For multi-anchor fuesse the
    field is omitted → script skips.
  - Computes Δ against the fraction's soll_fein in fuesse.yml.
  - For coins passing the ±2 % gate, proposes the patch (dry-run by
    default), printing the would-be note text. With `--apply`,
    writes the change through ruamel.yaml preserving comments.

Open design questions:

  * **Where does `fineness_anchor` live?** Option A: a dedicated
    field on `Fuss` in fuesse.yml (cleanest, schema-explicit).
    Option B: inferred from `fineness_display` text (fragile —
    «.875» vs «0.875» variants). Option A wins.
  * **What categories qualify?** Category-1 (strict single fineness)
    only: reichsdukatenfuss, courantdukatenfuss, pistolenfuss,
    reichsgoldmuenzfuss, vereinsmuenzfuss-gold-side, possibly
    18.5_thaler (.875 silver) etc. Need a per-fuss eligibility flag
    or just rely on whether `fineness_anchor` is set.
  * **What about coins where curated already has fineness but
    fineness_verified=false?** Skip — they've already gone through
    the procedure. The sweep targets `fineness: null` only.
  * **Cross-check via Numista cache:** when a Numista entry exists
    for the coin (`catalog.numista`) and publishes its own fineness,
    that's a stronger signal than the canonical anchor. Prefer
    Numista's value when present (with `fineness_verified: true`
    and source-citation). Skip the canonical-anchor path for those.

Scope: hundreds of coins potentially. The auto-suppress and merge
work has already cleaned up most low-quality dupes; what remains is
mostly seed-curated bulk that lacks fineness because the original
source did. A single sweep pass + manual review of the proposed
patches should close most of them.

Defer to the same audit window as §N / §O / §P / §Q.

### Q. Pull Hede / Numista commentary material for coin notes  *(opened 2026-05-13)*

The cached sources (`scripts/cache/hede/*.json` `description` + `raw_text`
fields; `scripts/cache/numista/*.json` `comments` + `obverse` /
`reverse` `description`) carry **substantial narrative context** about
the coins — mint-master identities, design motifs, historical
circumstances (Borgerskabets Mønt 1629, Hebræermønt 1644-48,
Pumphosenkrone 1665, etc.), reform-date attestations, literature
pointers (NNUM articles, Wilcke, Aagaard, Harck) — that is currently
under-used in our `coin.note` prose.

Sweep tasks:

* For every curated coin in `denmark.yml` + `schleswig_holstein.yml`
  whose `catalog.hede` is set, open the corresponding
  `scripts/cache/hede/<volume><number>.json`'s `raw_text` and look
  for narrative content beyond bare specs: pages frequently embed
  one-paragraph historical notes between the sub-letter list and
  the Bruttovægt block.
* Same pass for Numista: `comments` field on cached entries (where
  populated) often holds mint-master + design-variant detail and
  cross-pointers to danskmoent. Worth a per-entry «is there more in
  here?» check.
* Hede references commonly cite specific articles — `Aagaard og
  Märcher 2016 NNUM 4`, `Wilcke 1923 NFM VI`, `Harck 2008 Numismatisk
  Rapport 97` — those references should also flow into our
  per-location `-references.yml` bibliography files with inline
  `<sup>` citations from the coin notes, per CLAUDE.md §5.
* Numista entries occasionally carry **mintage figures** in the
  comments (curators noted «63,564 daler» for Schwabe 1628 etc.).
  These are valuable economic-context data; should land in note as
  a citation per §0 (no invention) — never inferred.

Scope is large (1000+ coins across DK + SH). Probably best done in
ruler-by-ruler passes (Christian IV first, then Frederik III, etc.)
when there's no higher-priority work blocking.

### P. Denmark issuing-entity audit — DK vs DK+ separation  *(opened 2026-05-13)*

Two crown-level issuing entities currently live side-by-side in the
denmark.yml taxonomy:

* **`danish_realm` (DK)** — «Royal Danish Mint at Copenhagen
  (Christiansborg, then Den Kongelige Mønt from 1739). Realm-wide
  issues for the whole Danish monarchy including the duchies.»
  (348 coins use this entity.)
* **`gesamtstaat` (DK+)** — «Unified Danish Crown + duchies
  (1773-1864). Mints at Altona, Copenhagen, Glückstadt strike for
  the whole realm. Covers the 1813 Rigsbankdaler reform and the
  1854 Rigsmønt reform.» (34 coins.)

Both descriptions explicitly cover «realm-wide issues including the
duchies». The semantic distinction is **temporal**: pre-1773 (DK,
pre-Helstaten administrative split) vs post-1773 (DK+, Helstaten
unified-state phase with multi-mint reform-era coinage).

Separate territorial entities already cover the geographical
dimension: `royal_holstein` (Kgl. Holstein-side, Glückstadt /
Altona), `gottorp_duchy`, `sonderburg_duchy`, `norburg_plon_duchy`,
`glucksburg_duchy`, `rantzau_county`, `schauenburg_pinneberg` for
the Schleswig-Holstein side; `danish_norway` (NO) for the Norwegian
realm. So DK / DK+ are crown-level only.

**Audit questions:**

1. Is the 1773 Helstaten administrative milestone strong enough to
   warrant its own entity, or could it be a `helstaten: true` flag
   on coins under a single `danish_realm` entity? The 1813
   Rigsbankdaler reform is arguably the bigger watershed — Helstaten
   only became fully unified-coinage state then.
2. Are the **current 34 DK+ assignments** consistent with a strict
   1773 cutoff? Edge cases: Altona-mint coins 1771 (KM-616 series)
   — those are pre-Helstaten but Altona-side. Currently DK or DK+?
3. Some Helstaten-era coins might be **under-assigned** to DK
   instead of DK+ (curator drift). A consistency pass would help.
4. **Recommendation** (my read): keep the split — 1773 is a
   defensible historical milestone, and tilting one entity per
   administrative phase IS the project's pattern (e.g.
   `provisional_govt` for 1848-1849 transition). But document the
   cutoff rule explicitly (entity description currently says
   «1773-1864»; that's already the boundary). Then run a consistency
   sweep to make sure existing assignments follow it.

Defer to the same audit window as §N / §O when bandwidth opens.

### O. Numista weight typos vs Hede Bruttovægt  *(opened 2026-05-12)*

Adjacent pattern to §N: Numista entries occasionally publish a
«weight» field that's closer to Hede's Finvægt (fine-silver content)
than to Hede's Bruttovægt (gross-coin standard). Numista's own
convention is Brutto (confirmed via control-case KM-81 / Hede 115:
Numista 1.051g matches Hede Bruttovægt exactly). Where Numista
deviates by ~10-15% from Hede's Brutto, the most parsimonious
explanation is a user-edit error — the editor entered Finvægt by
mistake.

One case resolved so far:

* **KM-82 / Hede 114** (8 Kroneskilling Christian IV 1620-1621) —
  *resolved 2026-05-12.* Hede Bruttovægt 2.101g (passes three
  independent checks: internal arithmetic 2.101 × 0.859 = 1.806
  matches published Finvægt; silver-proportional 2× sister-denom
  KM-81 = 2 × 1.051 = 2.102; marken-fin formula gives the correct
  1/12 daler face value matching curator's `fraction: 1/12`).
  Numista/ucoin 1.85g is 12% low — likely Finvægt-mistake. Hede
  value now primary on km-82-chr-iv-1620; Numista 1.85g kept as
  second reading with annotated explanation.

Pattern hypothesis: small-denomination scheidemünze entries on
Numista are more prone to this confusion because Brutto and Finvægt
are visually close and the source pages (often danskmoent Hede)
publish both side-by-side. Larger denominations (where Brutto and
Finvægt differ by a clear factor) are less affected — see KM-81
control case.

Open question: how many other Numista DK entries have this
inversion? A sweep over `scripts/cache/numista/*.json` comparing
`weight` vs Hede's published Brutto for each entry (filtered to
those that also cite Hede in catalog refs) would surface the full
list. Hold for now — defer to the same audit window as §N.

### N. ucoin↔Krause KM-attribution conflicts (Denmark)  *(opened 2026-05-12)*

Recurring pattern surfaced during the dedup-merge audit of denmark.yml:
ucoin's bulk catalog (built from ucoin's user-edited TSV under
`scripts/cache/ucoin/period_*.tsv`) assigns a KM number that
disagrees with Krause-Denmark as verified by Bruun PDF + Hede.
Per CLAUDE.md §5, Bruun is the higher-authority source (auction-
catalog tier 3), so when ucoin's KM and Bruun's KM disagree on the
same numeric value, Bruun wins and ucoin's KM-attribution is dropped.
ucoin entry retains its non-KM data (weight, fineness, year,
nominal, source URL) as a bulk-pending coin awaiting classification.

Two cases resolved so far; pattern likely recurs across the ucoin
period TSVs and warrants a broader sweep:

* **KM 48** — *resolved 2026-05-12.* `dk-tid-162993` («1 Søsling
  1614») had ucoin-assigned km=48. Bruun lot 13080 + Hede c4h48
  attest KM-48 = ¼ Speciedaler 1602 Christian IV (= our
  `km-48-chr-iv-1602`). km tag cleared on dk-tid-162993,
  verification_note records the finding. Per-coin classification of
  the 1614 Søsling type itself remains pending (Hede c4h skips
  this year between c4h84 (1611) and c4h145 (1631), so the type
  needs an independent source if it's to gain a Krause-edition KM
  citation).
* **KM 577** — *resolved 2026-05-12 alongside.* `dk-tid-78763`
  («½ Skilling 1751-1762» 3.654 g) had ucoin-assigned km=577.
  Bruun lot 17127 attests KM-577 = 1 Dukat 1749 Frederik V (= our
  `km-577-1749`). Beyond the KM clash, ucoin's nominal+weight pair
  (½ Skilling at 3.654 g) is itself numismatically implausible —
  expected ½ Skilling weight under Frederik V is ~0.4 g. Both flagged
  for follow-up: KM dropped, full re-classification of the underlying
  coin remains pending.

Open question: are these isolated ucoin-cataloger errors, or do they
trace to an older Krause edition with different KM numbering? A
sweep over `scripts/cache/ucoin/period_*.tsv` against Bruun-verified
KMs in denmark.yml would surface the full set. Hold for now —
follow-up audit pass when the higher-priority L-campaign items free
up.

### M. ucoin Composition harvest — partial progress, paused on Cloudflare bot-protection  *(opened 2026-05-11, partial progress 2026-05-13, paused 2026-05-13)*

**Paused 2026-05-13 end of day.** After three productive sessions
(121 new sidecar entries + 178 metal-field updates across denmark /
lubeck / schleswig_holstein), a fourth session attempt was met with
**HTTP 403 + Cloudflare «Just a moment…» bot-protection challenge**
on every same-origin fetch, even after the user cleared cookies.
Cloudflare's challenge appears to be IP + browser-fingerprint based,
not pure cookie-state — once tripped, cookie-clear forces a re-
challenge instead of resetting it, and our automated fetcher cannot
solve the JS challenge.

**Resume conditions (any one suffices):**

  1. **Wait for Cloudflare cooldown** — typically 24h of quiet
     traffic from our IP. Re-attempt next session with 20-30 s
     pacing and ≤ 30 fetches per cookie-cycle to stay well under
     the underlying request ceiling.
  2. **Pass the Cloudflare challenge manually in the browser** —
     user navigates to ucoin in their normal browser window, waits
     for the «Performing security verification» page to clear,
     accepts any «I'm human» prompt; the resulting `cf_clearance`
     cookie may pass through to subsequent automated requests.
  3. **Different network egress** — VPN or alternative IP, but
     introduces its own complications.

**Resume tomorrow (2026-05-14 or later)** with option 1 / 2; see
the existing rate-limit analysis above for pacing guidance.



**Original surface (2026-05-11).** The investigation of `dk-tid-163075`
(KM# UC# 10, Frederik II 10 Ducat 1588) where user-side verification
on the live ucoin page showed «Composition · Gold» that our local
cache never carried. The `scripts/cache/ucoin/_url_index.json` schema
only stored `denom / diameter_mm / fineness / km / source / url /
weight_g / year` — no metal / composition.

**Progress 2026-05-13 (this session).** Wrote a careful sequential
Chrome-MCP fetcher (2.5 s pacing, CONCURRENCY=1, canonical-tid
validation rejects bad-slug pages serving unrelated coins). Probed
~80 ucoin URLs cited by unverified Denmark coins:

  * **36 successful fetches** — sidecar now has 134 entries with
    real Composition / weight / diameter data (was 98).
  * **45 slug_mismatch failures** — marked `status_404` in sidecar
    so future runs skip them.

Ran `scripts/maintenance/ucoin_backfill_metal.py` (with three logic
fixes — see commit `703617e`): 93 metal fields touched across
denmark / lubeck / schleswig_holstein.

  * `metal_confirmed: 87` — inference agreed with ucoin → flipped
    `metal_verified: true`.
  * `metal_replaced: 6` — ours wrong, ucoin source-attests:
      - 3 billon → copper for sub-Skilling Pennings (KM-5, KM-6, KM-86)
      - 2 silver → gold for Daler-class issues (4 Daler 1604,
        6 Daler 1604)
      - 1 billon → copper for KM-86 (the user's surfacing case)
  * `metal_disagree_with_source: 0` — no verified entries collided.

Backfill script fixes carried by the same commit:
  * `Silver (Billon) X.XXX` parser bug (was returning `silver`+None
    instead of `billon`+X.XXX) — fixed via dedicated bracketed-form
    regex.
  * Default for absent `metal_verified` flipped from `True` → `False`
    (project convention is explicit `true` on source-attested).
  * Case-2 disagreement now replaces with ucoin's reading (verified-
    wins-over-unverified per CLAUDE.md §4) rather than just flagging.

**Root cause clarified 2026-05-13 (post-cookie-clear retry).** The
«slug_mismatch» symptom is ucoin's RATE-LIMIT mechanism, NOT slug-
routing breakage. After a session crosses the limit ucoin starts
serving the canonical page for whichever slug the requester arrives
at NEXT but with a different tid in the canonical link — the page
appears valid but isn't for the requested tid. The canonical-tid
validation guard catches it correctly.

User cleared cookies → ucoin became responsive again. All 45 tids
previously marked status_404 from session 1 (the 2.5 s pacing burst)
were re-fetched successfully on session 2.

**Threshold measured 2026-05-13:**

| pacing | first failure | sustained | per-min rate |
|---|---|---|---|
| 2.5 s | req 37 | ~36 ok in 1.8 min | ~20 req/min |
| 10 s | req 52 | 51 ok in 9.4 min | ~5.4 req/min |

The slower-pacing run got further before the wall, but the absolute
ceiling appears to be ~50 cumulative requests per session-cookie.
Once tripped, every request returns the wrong-tid page until cookies
are cleared (or, presumably, time passes — duration not measured).

**Practical pipeline (still semi-manual, requires the user):**

  1. Run a session of ≤ 45 fetches at 10 s pacing.
  2. Watch for `slug_mismatch_*` cluster (≥ 3 consecutive on the same
     batch) — that's the rate-limit signal.
  3. Pause harvest; ask the user to clear `en.ucoin.net` cookies.
  4. Resume from where we stopped.

**Status after 2026-05-13 sessions (combined):**

  * Sidecar: 185 entries with data (was 98 → 134 → 185).
  * Backfill applied 51 more fields this session (134 of these were
    in the earlier 93). Cumulative: 144 metal/verified fields touched
    across denmark + lubeck + schleswig_holstein.
  * 5 tids still rate-limited at end of session 2 (97085 / 97086 /
    96444 / 96445 / 96458) — left as uncached for next cookie-cycle.
  * Remaining uncached (next sessions): ~520, all expected to fetch
    cleanly given a fresh cookie state per ~45-request batch.

**Remaining work.** ~520 ucoin URLs to harvest via repeated cookie-
cycle sessions (~12 sessions × 45 fetches × 10 s = ~90 minutes of
fetcher time, plus cookie-clear inter-session). The harvest is
mechanical; pacing rule + canonical-tid guard ensures correctness.
A semi-automated cookie-rotation would eliminate the user's manual
cookie-clear step (deferred — needs investigation of whether ucoin
session lifetime is just the JSESSIONID cookie or something else).

**Not blocking page renders.** Denmark / lubeck / schleswig_holstein
pages render correctly; ~93 metal fields are now `verified: true`
(major improvement on legacy inference). The remaining gap affects
~530 mostly-Danish entries whose metal is still inferred from
Müntzfuß convention.

---

### L. Schleswig-Holstein + Denmark consolidation campaign  *(opened 2026-05-10)*

A coordinated multi-pass effort to bring the SH and Denmark locations
to «published-quality» state before the next location takes priority.
The nine sub-tasks below are tightly coupled — many depend on
upstream completion (the territorial-attribution sweep before the
data audit, etc.) — and should be worked through roughly in the
listed order.

1. **Process all IKMK candidates per location.**
   - **1a. Schleswig-Holstein — DONE 2026-05-10.** All 65 IKMK records
     in scope (prefixes Schleswig-Holstein-Sonderburg / -Gottorf /
     -Glücksburg / plain SH) processed: 47 already cited in
     `data/locations/schleswig_holstein.yml`, 2 added (commit
     `eca82c0`: km-9 Lange 533A/a + 533A/b mule specimens after
     §9a thinning), 16 deliberately skipped per §9a sub-variant
     bucket overflow (intra-bucket noise — not a coverage gap).
     Matcher hardening shipped along the way (commit `24a82e7`:
     weight-sanity gate at 1.5× ratio, multi-letter+slash Lange-tag
     regex, parent-fallback strict-ref lookup).
   - **1b. Denmark — PENDING. Blocked by harvest expansion in (2a).**
     Current IKMK scope for `denmark.yml` is only 41 records (26
     under prefix «Dänemark» + 15 under «Norwegen») versus 468 coins
     in the YAML. The IKMK Berlin cache holds 6,531 JSON files in
     total, of which only this restrictive subset routes to the
     denmark mapping in `_index_by_issuer.json`. The harvest filter
     used for the original SH+DK pass was clearly Holstein-context-
     scoped; for proper denmark coverage it has to be re-run with
     a Kopenhagen / Christiania / Norwegen mint sweep across the
     full 1566-1914 window. Matcher run + bucket triage is identical
     in shape to (1a) but blocks on (2a).

2. **Multi-source enrichment pipeline for `denmark.yml`** (DK-only
   scope; SH covered separately under (1a) and the older audit work).
   The four stages below run roughly in order — earlier stages enrich
   the per-coin data that later stages cross-check against:
   - **2a. IKMK harvest expansion. PARTIAL — IKMK ceiling reached
     2026-05-10.** Ran a broader query set covering Denmark proper +
     Danish-Norwegian-union mints + Danish-controlled territories
     (Iceland, Faroe, Greenland, Tranquebar, Danish West Indies,
     Danish Gold Coast) and Danish-king-ordinal queries (Christian
     IV–X, Friedrich III/IV/VI/VII). The fetch added **548 new cache
     records** (722 fetched − 174 ancient/Roman noise removed), but
     only **6 routed to denmark** via the issuer-prefix mapping
     (Trondheim — medieval, out of 1566–1914 scope window).
     Final IKMK Denmark coverage: **68 records / 41 in-scope**
     (vs 62 / 41 pre-expansion). The «several hundred» target is
     not achievable through IKMK alone — IKMK Berlin is a German
     museum and has limited Danish coverage (62 «Dänemark» + 19
     «Norwegen» records exhausted; Tranquebar / Iceland / Faroe /
     Greenland / Danish-Gold-Coast queries returned zero hits).
     Remaining 542 cache records are non-Danish coins (Schleswig-
     Holstein-related, Hessian Friedrich's, Brandenburg-Lüneburg,
     etc.) that the broader ruler-axis queries pulled along with
     Danish ones. Reaching «several hundred» requires alternative
     catalogues — see TODO H for Royal Coin Cabinet Copenhagen +
     British Museum API coverage check.
   - **2b. IKMK candidates processing + DK seed_unsorted triage
     (combined).** After (2a), run `match_ikmk_locations.py denmark`
     and walk the buckets per the same procedure as (1a). At the
     same time, walk the 422 `seed_unsorted` entries currently in
     `denmark.yml` (per TODO D's DK part) and resolve their
     Müntzfuß / phase / verification status. Combining both passes
     maximises per-coin data density: an IKMK record that strict-
     matches a seed entry can lift it out of `seed_unsorted` into
     a real fuss with full provenance in one merge instead of two.
   - **2c. Hede / danskmoent.dk exhaustive coverage check.** Verify
     that `danskmoent.dk` Hede catalogue pages (URL pattern
     `c{ruler}h{N}.htm` per-type, `c{ruler}hede{N}.htm` overview)
     are cached for every ruler-era covering coins in `denmark.yml`,
     and that every coin with a Hede equivalent carries a
     `catalog.hede` field. Subsumes the original TODO K (systematic
     Numista-vs-Hede divergence audit) — once Hede coverage is
     wired, run the Numista-cross-check pass and apply per-coin
     corrections per the established km-79 / km-128 / km-110 shape.
   - **2d. Other-source enrichment (lower priority, post-Hede).**
     Walk denmark.yml coins and pull additional readings from ucoin
     (where SH-style URL index extends to DK), Numista (already
     largely cached but un-merged on many coins), NumisBids, ma-
     shops auction data, and any other accessible catalogue. Each
     source becomes its own atomic step here once the Hede-pass
     surfaces what's still under-documented. Order TBD when the
     sub-items materialise.

3. **Triage all remaining `seed_unsorted` coins in denmark.** The
   Bruun bulk import seeded coins under `seed_unsorted` when no
   confident phase / fuss could be assigned. Walk the list (already
   tracked under TODO D for the broader hamburg+lubeck+denmark
   scope, but bring the DK part to completion as part of this
   campaign).

4. **Move all genuinely-Danish coins from SH to denmark.** Royal-
   Danish issues (Christian IV, Frederick III, Christian V, etc.)
   minted in Copenhagen / Helsingør / Christiania currently living
   in `data/locations/schleswig_holstein.yml` should migrate to
   `data/locations/denmark.yml`. Cross-check `mint` and
   `issuing_entity` fields; anything that is `royal_holstein` is a
   deliberate SH-territorial issue (Glückstadt under Christian IV
   stays in SH); anything that is plain Danish royal goes to DK.

5. **Show all Denmark-related SH coins on the Danish page.** SH
   coins issued by the Danish Crown for SH-territory (Glückstadt
   Reichsthalers under ChrIV, Schleswig-Holstein-dänisch Mark/Marck
   etc.) historically circulated as part of Danish coinage and a
   reader on the DK page would expect to find them. Decide the
   mechanism — preferably *not* a YAML copy. Options to consider:
   (a) a Jinja-side cross-include that pulls a filtered view of
   SH's `royal_holstein`-issuing coins into a new section on
   `denmark/<lang>/index.html`; (b) extracting those coins into a
   shared file `data/shared/dk_sh_dual_register.yml` and including
   from both location pages. The end-reader sees one view per
   location; the data lives once.

6. **Move all SH-territorial coins from denmark to SH.** The
   mirror of (4): any coins currently in `denmark.yml` that are
   actually SH-territorial issues (e.g. struck in Altona by the
   Danish Crown but for the duchies, not for the kingdom) belong
   in `schleswig_holstein.yml`.

7. **Verify that all SH and Denmark coins sit in the correct fuss,
   category, and phase.** Walk every coin in both files and confirm
   `fuss` (per §8.1 / §8a), `kind` (kurant / scheide / tarif /
   gedenk per §6), and `phase` (per the location's phase definitions
   and §8.2). The Sonderburg-Kipper rows on §8.1 boundaries are
   particular candidates for review.

8. **Per-coin data audit.** For every coin in both files, walk every
   listed source and confirm that (a) the data published in the
   source matches the data on the coin row, AND (b) every data
   point on the coin row that the source documents is present.
   Catches both transcription errors (Numista digit-swap pattern
   from TODO K) and missed enrichments (source published a
   diameter or fineness we didn't transcribe). Done criterion:
   audit-script `scripts/audit_per_coin_sources.py` that flags
   discrepancies, then per-row remediation pass.

9. **Audit of all rendered prose.** All `note`, `description`,
   `verification_note`, and phase-prose fields across both
   `data/locations/schleswig_holstein.yml`,
   `data/locations/denmark.yml`, and the matching
   `*-references.yml` files. Check: register (CLAUDE.md §2a),
   period orthography (§2), reader-voice vs analyst-voice (§0a /
   §0z), no-invention (§0), inline-citation hygiene (§5), and
   uk Cyrillic-transliteration trap (§2a). The corpus has
   accumulated ~ a year of prose under varying voice discipline;
   a sweep is overdue.

**Estimated effort.** Each sub-task is a multi-hour to multi-day
piece of work. Expected total: 1–2 weeks of focused sessions. Open
sub-items as their own TODO letters once they reach the active
working tier.

---

### K. Systematic Numista vs. Hede cross-check  *(opened 2026-05-09)*

**Surfaced during.** Three independent investigations during the
weight-spread audit (this session) found Numista publishing weights
that disagree substantially with Hede authoritative specs (via
danskmoent.dk):

  | Coin | Numista weight | Hede spec | Δ |
  |---|---:|---:|---:|
  | km-79-chr-v-1693 (4 Skilling Dansk) | 1.224 g | 1.951 g (Hede 128) | +59 % |
  | km-110-chr-v-1693 (1 Krone) | 21.98 g | 22.272 g (Hede 125 B) | +1 % |
  | km-128-chr-v-1787 (10 Schilling Courant) | 8.428 g | 6.129 g (Hede 42) | −27 % |

The km-79 and km-128 cases were egregious: Numista's value lined up
with a *different* coin's weight (km-79: matches the 2-Skilling
KM#78 spec; km-128: matches the 1/3-Speciedaler fein-weight of
KM-130, suggesting denomination conflation). Numista's fineness on
km-79 also showed a digit-swap error (.347 vs Hede's .437).

In every case Hede + ucoin + (where present) Bruun agreed on the
correct value, and Numista was the outlier. This is consistent with
CLAUDE.md §5's «Numista — useful for catalog numbers and rough
data, but user-edited, treat with some skepticism» — but the
specific failure mode (denomination cross-contamination,
digit-swap) suggests a population of similar errors across the
Danish royal billon / Schilling-class corpus.

**Background.** Hede covers Danish royal coinage 1541-1814
exhaustively — every type has a `c{ruler}h{N}.htm` page on
danskmoent.dk with `Bruttovægt`, `Finhed`, `Finvægt` figures and
mintmaster + Schou refs. We have direct verification this URL
pattern works (km-79 / km-110 / km-128). Hede sits at tier 2 of our
source hierarchy (after coin inscription / museum); Numista at
tier 5.

**Done criterion.** Audit script
`scripts/audit_numista_vs_hede.py` (to be written) that:

  1. For every coin in `data/locations/*.yml` where `catalog.numista`
     is set AND a Hede ref is known (either in `catalog.hede` or
     parseable from sources), fetch the Numista cache + fetch the
     Hede page (URL pattern `c{ruler}h{N}.htm` derivable from
     ruler-era + Hede number).
  2. Compare published weight + fineness. Flag spreads ≥ 5 % as
     candidates for the per-coin Hede-correction pass.
  3. Output a triage list (similar in shape to `_match_<loc>.md`):
     coins where Numista is likely wrong, coins where they agree,
     coins where Hede ref is missing and needs lookup.

Then a second pass: for each flagged coin, apply the same
correction shape used on km-79 / km-128 — Hede authoritative,
ucoin/Bruun confirming, Numista retained-but-flagged with
`(likely transcription error — see note)` source suffix.

Note: the population is bounded by «coins with Hede ref». For
locations where Hede applies (denmark, schleswig_holstein,
lauenburg), that's most entries. For the SH-territorial-duchies
(Sonderburg, Gottorf), Hede may not apply (Lange Vol II is the
authority) — the audit must distinguish.

**Estimated effort.** Audit-script + first triage report: ~1 h.
Per-coin Hede-correction pass: ~5-10 min per coin × N flagged.
Total depends on how many coins have the cross-contamination
pattern — probably 20-50 SH/DK entries based on the sample so far.

---

### H. Coverage check for additional museum / catalogue APIs  *(opened 2026-05-07)*

**Background.** IKMK Berlin (`ikmk.smb.museum`) was confirmed in
2026-05 as a usable enrichment source: CC BY-SA 4.0 texts, PDM 1.0
images, free unauthenticated JSON via
`/object?id=<id>&download=json_ext`. Bulk cache job for SH+DK scope
was run (~2.9k records). See `docs/IKMK_HARVEST.md`.

The same shape of work is worth doing for the next two tiers of
museum sources mentioned in CLAUDE.md §5 source hierarchy:

- **Royal Coin Cabinet (Copenhagen)** — Den Kgl. Mønt- og
  Medaillesamling at the National Museum of Denmark. Likely
  candidate URL `samlinger.natmus.dk` or
  `kongernessamling.dk` — confirm.
- **British Museum** — has an unambiguous open API at
  `https://www.britishmuseum.org/api/...` (Collections Online).
  Numismatic department likely indexes Holstein, Hamburg, Lübeck
  coins.

**Done criterion.** For each: licensing posture confirmed, sample
records fetched for known SH/DK coins, coverage estimate produced
(N records in scope), comparison with IKMK overlap. Record findings
in `docs/<MUSEUM>_HARVEST.md` similar to the IKMK one.

**Estimated effort.** ~30 min per source for the probe; bulk cache
~1 h each if API permits.

---

### F. Bruun fall-throughs documented for posterity  *(opened 2026-05-06)*

After Phase 4c + Phase 3 completed, the Bruun cross-match shows 11 fall-through
candidates in DK+SH that did NOT enter the data. All are accounted for:

- **3 medieval (pre-1566, out of project window)** — excluded per project scope:
  - P1·1001 Hans 1496 Noble (Bruun-coll. 3831, NGC AU-55, UNIQUE in private)
  - P1·1002 Hans ND 1496-1497 Goldgulden (Bruun-coll. 3840)
  - P3·11148 Christopher III 1440-42 Skilling Lund (Bruun-coll. 3763)

- **1 pattern (per §9.1)** — excluded:
  - P2·13140 Frederik III 1659 5 Ducats Hede-100A KM-PnJ16 (Bruun-coll. 6275, NGC Unc Details—Cleaned)

- **2 SH-Altona Christian VII multi-year merges** — addressed in this commit:
  - KM-640.1 1786 Albertsdaler → enriched km-640-1-chr-vii-1784 (Bruun-coll. 7863, 1786 specimen)
  - KM-641.4 1785 12 Mark (Courant Ducat) → new entry km-641-4-chr-vii-1785 (Hede-4D sub-variant of Hede-4B 1783, Bruun-coll. 7859)

- **5 already-covered (matcher-quirks)** — no action needed:
  - P2·14241 KM-226.1 1753 Karl Peter Ulrich Mannheim Taler — flagged as Krause sub-variant of existing km-226-kpu-1753 in Phase 4a batch 6
  - P2·14261 KM-cf.455 Adolf XIII 1598 3 Taler Altona — already added as bruun-14813-adolf-xiii-1598a (Phase 4a batch SP); matcher missed because no exact KM ref
  - P3·12215 Adolf XIII 1598 1½ Taler Altona — already added as bruun-14815-adolf-xiii-1598b (Phase 4a batch SP); same matcher reason
  - P4·17210 KM-758.1 Frederik VII 1854 4 Skilling Rigsmønt → already enriched km-x003-fr-vi-1854 in Phase 4a batch 7b
  - P4·17218 KM-cf.758.2 Frederik VII 1856 Copper Piefort 4 Skilling — already added as schou-piefort-fr-vii-1856 in Phase 4c batch 6

**Bruun cross-match closing state (2026-05-06 after parser-fix + §9.3 cleanup):**
TOTAL=783, A=763 (97%), B=11, D=9.

- **B=11 residual noise** — multi-match cases where the *correct* candidate is
  enriched but a *spurious* year-overlap candidate (e.g. Lübeck KM-27 1/192 Thaler
  colliding with Danish KM-27 Speciedaler) lacks the Bruun citation, so cross_match's
  `all()` semantic still flags the lot as B. The 11 residuals are documented and
  not actionable without changing cross_match.py to use `any()`-semantic; left as
  closing inventory:
  - P1·1017, P3·11178 (KM-26 Hede-11 6 Daler Klippe 1604) → dk-tid-163410 ✓
  - P1·1018, P4·17046 (KM-25 Hede-12 4 Daler Klippe 1604) → dk-tid-163409 ✓
  - P1·1049, P2·13114, SH P2·13120, SH P4·17058 (KM-27 Speciedaler 1642–1647 Glückstadt) → km-27-chr-iv-1641/1644 ✓
  - P2·13097 (KM-16 2 Speciedaler 1623 Glückstadt) → km-16-chr-iv-1623 ✓
  - P2·13159 (KM-56 Ducat 1666 Glückstadt) → km-56-fr-iii-1666 ✓
  - P4·17194 (KM-742 Speciedaler Frederik VII 1848 Accession) — no host coin in our YAML; KM-742 is a distinct Krause type from km-744 (1849). Genuine D-candidate that was mis-categorised B by ref-token noise.

- **D=9 fall-throughs** — true non-matches (medieval / pattern / cross-bucket
  mis-routings handled in this section, plus 1 oldenburg P3·12226 1/2 Mark
  / 12 Grote 1658 awaiting Müntzfuß-classification of `oldenburg.yml`).

**Done criterion**: this list is the closing inventory; no further fall-throughs from the
4-PDF Bruun cross-match remain. Bruun Part V (when published) will run through the same
pipeline and any new fall-throughs will be triaged similarly.

---

### E. Müntzfuß-classify 7 promoted Bruun stub locations  *(opened 2026-05-06; updated 2026-05 after Phase 4b proper)*

**Background.** Bruun parts I–IV ingest (cache in `scripts/cache/bruun/`) routed
**38 in-scope coins** to 7 territories. They are NOW promoted to real location
files (see commits 2026-05) with `fuss: seed_unsorted` placeholder; per-coin
data (KM/Hede/Sieg/Lange/Fr/Dav refs, year, ruler, mint, weight, NGC grade,
Bruun-page citation) is preserved. The Müntzfuß-system research is what's
still pending — each territory uses its own Reichskreis or local standard that
needs proper study.

**Seed files & their Müntzfuß-systems to research:**

| Seed file | Coins | Müntzfuß systems to research |
|---|---:|---|
| `data/seed/bruun/lubeck_bishopric.yml`     | 14 | Reichsthalerfuß via Holstein-Gottorp prince-bishops (Eutin) |
| `data/seed/bruun/oldenburg.yml`            | 10 | Niedersächsischer Kreis-Fuß; Jever-Mint grote-systems under Anton Günther |
| `data/seed/bruun/bremen_verden.yml`        |  6 | Niedersächsischer Kreis (1635–1648), then Swedish administration 1648–1712 |
| `data/seed/bruun/brunswick_lueneburg.yml`  |  4 | Reichsmünzordnung → Leipziger Fuß → Konventionsfuß (Wolfenbüttel mint, Christian IV's Niedersachsen-Periode 1627) |
| `data/seed/bruun/hesse_kassel.yml`         |  2 | Reichsmünzfuß → Konventionsfuß (Kasseler Münzkonvention 1763), 14-Thalerfuß |
| `data/seed/bruun/lauenburg.yml`            |  1 | Lauenburg-Konventionsfuß (1815–1864 under DK king) — distinct from Schleswig-Holstein, struck at Altona Mint per separate Lauenburg standard |
| `data/seed/bruun/osnabrueck.yml`           |  1 | Niedersächsischer Kreis-Fuß under prince-bishop, alternating Catholic/Lutheran 1648+ |

**Promotion procedure** (per territory) is documented in `data/seed/bruun/README.md`:
research the relevant Müntzfuß, add to `data/shared/fuesse.yml`, add issuing entity
to `data/i18n/issuing_entities.yml`, create `data/locations/<territory>.yml` +
`-references.yml`, transform each seed coin record into a full `Coin` schema entry
with computed fineness/fuss/phase, then move (don't copy) the seed file out of
`data/seed/bruun/`.

**Done criterion.** All 6 seed files emptied (or moved to git history). The 37
coins live in proper `data/locations/` files with correct fuss-classification.

---

### D. Triage `seed_unsorted` coins in denmark / hamburg / lubeck  *(opened 2026-05-04)*

**Background.** After bulk-importing 581 ucoin entries into proper
location files (commit `1abbef8`), three locations carry coins under
the placeholder `seed_unsorted` Müntzfuß:

- `data/locations/denmark.yml`     — 422 seed entries (years 1582–1875)
- `data/locations/hamburg.yml`     —  80 seed entries (years 1726–1873)
- `data/locations/lubeck.yml`      —  79 seed entries (years 1620–1797)

Each seed entry carries raw ucoin data (km, denom, year, fineness,
weight, diameter, url, tid) plus best-effort heuristic inference for
ruler/mint/metal. Every value flagged `verified: false`.

**Done criterion (per location).** All seed entries reclassified into
their proper Müntzfuß and gain `verified: true` for source-attested
fields. The location automatically reappears on the landing page once
its `seed_unsorted` count reaches zero — the build script
(`scripts/build.py::build_landing`) hides any location with even a
single seed entry, then re-checks on every build. No template/config
edit needed when the threshold is crossed.

**Recommended order.**

1. **Hamburg (80, smallest)** — needs new Hamburg-specific Müntzfüße
   defined in `data/shared/fuesse.yml` first (Bankthaler / Speciesthaler /
   Mark-Courant standards). Triage by ucoin Period + Hede equivalents.
2. **Lübeck (79)** — needs Wendisch-Lübisch Münzfüße defined (the
   existing 11_333_thaler proxy is incorrect for most Lübeck coins).
   The 1 already-curated entry (km-168-1-1752) is the model.
3. **Denmark (422, largest)** — most coins fit existing fuesse:
   - period_2940 (Speciedaler 1582-1624) → 9_25_thaler / 9_thaler
   - period_1147 (Rigsdaler 1625-1699) → 9_25_thaler / kronemont
   - period_1115 (Rigsdaler 1699-1749) → 9_25_thaler / reichsdukatenfuss
   - period_846  (Rigsdaler 1750-1812) → 11_333_thaler / 18_5_thaler
   - period_647  (Rigsbankdaler 1813-1854) → 18_5_thaler
   - period_646  (Rigsdaler rigsmønt 1854-1873) → 30_thaler
   - period_374  (Christian IX 1873-1906) → reichsgoldmuenzfuss
   Some need new Royal Danish standards added (Kurantmøntfod 1726+).

---

### C. Bremen-Archbishopric Frederick (II/III) coinage 1641–1643  *(opened 2026-05-03)*

**Surfaced during.** Cross-check of the 3 Numista issuer-list pages
linked from item B (now closed). The Bremen-archbishopric page
returned 3 Frederick III Bremen issues — historically connected to
our Holstein register because Frederick III held the Bremen
archbishopric (as Frederick II) before becoming Danish king in 1648.

**3 coins to model into a future `data/locations/bremen.yml`:**

| Coin | KM# | Numista | Metal / spec |
|---|---|---|---|
| 1 Thaler Frederick of Dänemark 1641 | KM# 38 | N#129848 | Silver .888, 29.23 g, Dav CCT# 5078/5078A, Jungk# 363… |
| 2 Schilling Frederick II 1641–1643 | KM# 36 | N#429659 | Silver |
| 1/16 Thaler 1641–1643 | KM# 37.1 | N#394107 | Silver, 1.57 g, ⌀19.3 mm, Jungk# 366–371 |

These are **NOT in scope of `schleswig_holstein.yml`** — Bremen archbishopric
is a distinct ecclesiastical territory, not a Schleswig-Holstein
duchy. They would belong in a separate `bremen.yml` location.

The user opened these as part of TODO B research; recording here so
the link from B's closure isn't lost. Whenever Bremen comes up as a
new location target, this is the seed list.

**Done criterion.** Bremen location file created with these 3 coins
(plus whatever else the bremen.yml scoping work surfaces) — OR an
explicit decision that Bremen stays outside the project scope.

---

### AT. 🟢 Surface `bruun_collection_id` as a rendered catalog ref («Bruun-NNNN»)  *(opened 2026-05-14)* *(est: small)*

**Surfaced.** User direction 2026-05-14, while compiling the §AB Daler-Klippe dossier (which extensively cited Bruun-4666 / 4667 / 4670 as the canonical specimen catalog references). The Bruun catalogues («L. E. Bruun Collection · A Corpus of Scandinavian Coins», Stack's Bowers Zürich Part I-IV 2025) print every coin under a stable `Bruun-NNNN` collection index alongside KM-/Hede-/Sieg-/Schou- catalog refs. Our coin data captures this in `catalog.bruun_collection_id`, but the renderer does not currently surface it in the rendered catalog-ref column — only `bruun_lot` (legacy single-field auction reference) is listed in `scripts/lib/compute.py:203-212` `_NAMED_FIELDS`.

**Concrete gap.** `_NAMED_FIELDS` (compute.py:203):

```python
_NAMED_FIELDS: list[tuple[str, str]] = [
    ("km", "KM"), ("hede", "Hede"), ("sieg", "Sieg"), ("schou", "Schou"),
    ("lange", "Lange"), ("fr", "Fr"), ("dav", "Dav"),
    ("bruun_lot", "Bruun"),  # ← legacy, often empty/missing
]
```

Missing: `("bruun_collection_id", "Bruun-coll")` (or similar label). Example coins where the data IS present but unrendered:

  - `denmark::km-27-chr-iv-1604` (8 Daler Klippe) — `bruun_collection_id: '4666'`
  - `denmark::dk-tid-163410` (6 Daler) — `bruun_collection_id: '4667'`
  - `denmark::dk-tid-163409` (4 Daler) — `bruun_collection_id: '4670'`

These have «Bruun-4666 / 4667 / 4670» in the source Bruun catalogue text but not in our rendered table.

**User direction**: surface as a rendered catalog ref **«нарівні або в others»** — either inline as a first-class catalog ref alongside KM / Hede / Sieg, OR in the `others` list. Both are acceptable; the inline route mirrors how Stack's Bowers prints these.

**Plan.**

  1. **Decide placement** (inline vs others). The inline route is recommended: Bruun-NNNN is a stable cross-referenceable specimen-collection index (every Bruun-published coin has one), not a one-off auction marker (which is what `bruun_lot` would be). Treat it like KM / Hede / Sieg in render priority.
  2. **Add to `_NAMED_FIELDS`** in `scripts/lib/compute.py:203`. Suggested entry:
     ```python
     ("bruun_collection_id", "Bruun-coll"),
     ```
     Or shorter label «Bruun» (collides with current `bruun_lot` slot — resolve by either dropping the legacy entry or renaming).
  3. **Resolve overlap with legacy `bruun_lot`**. Check whether any curated coin currently uses `bruun_lot` without `bruun_collection_id` — if so, decide migration strategy (back-fill bruun_collection_id, or keep both). The schema docstring (schema.py:317-323) already notes `bruun_lot` is legacy single-field, mirrors `bruun_collection_id` when both populated.
  4. **Verify rendered output**: rebuild denmark.html + schleswig_holstein.html, spot-check Daler-Klippe rows (km-27, dk-tid-163409, dk-tid-163410) for «Bruun-4666» etc. appearing in the catalog-ref column with correct tooltip.
  5. **Update CLAUDE.md i18n policy section** if needed: «Bruun-NNNN» format should be consistent across DE / EN / UK (catalog refs are non-translated identifiers per the policy).
  6. **Optional**: audit script in `audit_health.py` that lists Bruun-curated entries lacking a `bruun_collection_id` — surfaces missing data that the new rendering would expose.

**Cross-references.** §AN (Bruun cross-citation noise) flags three coins where `bruun_collection_id` might be mis-attributed by the Bruun parser — fix §AT renderer first so the data state becomes visible, then resolve §AN as actual data correctness work.

---

### AV. 🟡 Frederik-II-Guldkrone-fod 1563-64 — separate Fuß or phase under `guldkrone`?  *(opened 2026-05-14)* *(est: small)*

**Surfaced.** Umbrella research dossier §3.5 / §5.1: Frederik II's 1563-64 Guldkrone (Hede f2h2, f2h5) at fineness 0.934 / fein 3.120 g per piece is **distinct** from Christian IV's 1619-1648 Guldkrone (0.917 / fein 2.725 g) and Frederik III's 1657-1668 Guldkrone (per project's existing `guldkrone` Fuß). 55-year gap with NO Guldkrone strikes between 1564 and 1619. NOT a continuous standard.

**Two design options:**

  (a) Create separate Fuß **`f2_guldkrone_fod`** (1563-64 only), retain existing `guldkrone` for Christian IV 1619+ / Frederik III 1657+ phases.
  (b) Add a third phase to the existing `guldkrone` Fuß for the 1563-64 case, named «Frederik II Guldkrone-fod» — but the 0.934 → 0.917 metric break makes phase modelling awkward (different soll-fein per fraction).

**Recommend (a)** for cleaner classification. Implementation: add new Fuß entry to `data/shared/fuesse.yml` with anchor based on 233.856 / 3.120 ≈ 75 Guldkrone per Cölln. Marck fein (round-number convention candidate).

**Pending user verdict** on (a) vs (b) before §AU Frederik II seed promotion can use it.

### AW. 🟢 Spawn new Fuß `rhinsk_gylden_fod` for 1563-1632 Rhinsk Gylden track  *(opened 2026-05-14)* *(est: medium)*

**Surfaced.** Umbrella research dossier §3.6 / §5.1: a separate **Rhinsk Gylden / Rhenish-Gulden** standard runs through Danish royal coinage at fineness 0.76-0.77 (fein 2.47-2.50 g per piece). Appearances:

  - **f2h3** 1 Rhinsk Gylden 1563 (Frederik II)
  - **f2h6** 1 Rhinsk Gylden 1564 (Frederik II)
  - **c4h29** 1 Rhinsk Gylden 1625, 1627, 1628, 1632 (Christian IV)

69-year span; continuous standard within ~0.01 fineness variance. NOT Reichsdukatenfuß (0.986); NOT Guldkrone (0.917-0.934). German Rhenish Gulden tradition adopted by Danish royal mint for German-trade contexts.

**Historical tariff**: traditionally 1 Rhinsk Gylden ≈ 0.7-0.75 Reichsdukat (worth less fein than Dukat). Needs confirmation from period source.

**Plan**:

  1. Define `rhinsk_gylden_fod` in `data/shared/fuesse.yml` with anchor based on 2.5 g fein per piece and 0.77 standard fineness.
  2. Spawn phases for Frederik II (1563-64) and Christian IV (1625-1632) periods.
  3. Promote f2h3 / f2h6 / c4h29 from seed (currently c4h29 sits in `seed_unsorted`, f2h3/f2h6 not yet in seed — depends on §AU).
  4. Add to landing-page Müntzfüße overview.

### AX. 🟢 Investigate Rosenobel 1611-1629 tariff value + Fuß placement  *(opened 2026-05-14)* *(est: medium)*

**Surfaced.** Umbrella research dossier §3.4 / §5.1: Christian IV's Rosenobel series (Hede c4h23, c4h24) at fineness **0.833** — same as 4 Daler 1604 (c4h12) — has unclear tariff value:

  - **c4h23** 1 Rosenobel 1611, 1612, 1613, 1627, 1629 — brutto 8.994 g, fein 7.495 g
  - **c4h24** 1/2 Rosenobel 1611 — brutto 4.497 g, fein 3.748 g (clean half)

Historical context: **Kalmar War 1611-1613** — Rosenobel issued for war finance (Soldzahlung). Continental imitation of English Noble (originally 6s 8d face value).

Per-coin fein 7.495 g = 2.18 Reichsdukaten ≈ ~2 silver Daler at 12:1 gold-silver ratio. Suggests tariff ~2 Speciedaler / Daler, but needs external source confirmation.

**Two open questions**:

  1. **What was the contemporary tariff?** Need WebFetch / Wilcke I / Bobzin / contemporary Danish ordinance. Likely 2 or 3 Speciedaler face value.
  2. **Fuß placement** depends on tariff:
     - If tariff = par-metal commercial coin → fits some Fuß family (probably not Reichsdukatenfuß given 0.833 fineness)
     - If tariff = ordinance presentation gold (Klippen format) → own Fuß or grouping with the 0.833 «par-metal Klippen sub-cluster» (4 Daler 1604 also at 0.833)

**Plan**: research tariff via danskmoent.dk + Bobzin; document in umbrella dossier; decide Fuß placement; move c4h23 / c4h24 / c4h23b from `seed_unsorted` to the resolved Fuß.

---

### AZ. 🟢 Harvest pre-Christian-III catalog pages — Christian II 1513-1523 + Frederik I 1523-1533  *(opened 2026-05-14, rescoped 2026-05-16 per §BI)* *(est: medium)*

**Surfaced.** Research thread 2026-05-14 (`docs/research/danish_royal_gold_1560_1648.md` §1.4 + `docs/research/christian_iii_danish_coinage_1534_1572.md` §2.3 + 2026-05-16 Numista catalog browse via Chrome MCP) established that pre-Christian-III Danish coinage is documented by reference works **outside Hede 1957's own scope** (Hede starts at Christian III, 1534+). The danskmoent.dk site hosts a parallel Galster-derived series at `/fr/f1g*.htm` for Frederik I (and analogous Christian II series likely) — but this is a **NEW source family**, not a Hede extension.

**Rescoped 2026-05-16 per §BI**: The §BI Denmark-track anchor decision (1541 → 1514, Christian II Lovkompleks) excludes Hans-era (1481-1513) and Erik VII (1397-1439) gold as pre-anchor outliers. This entry now covers ONLY the **1514-1540 sub-window** (Christian II 1513-1523 + Frederik I 1523-1533). Hans Goldgulden / Nobles / Rhinsk Gylden + Erik VII Lund stay as research-doc context per `denmark_fuesse_year_boundaries.md`.

**URL pattern observed on danskmoent.dk** (per 2026-05-14 WebFetch of `1rhingyl.htm`):

  - Reign-overview pages: `hans.htm`, `f1.htm`, `c2.htm`, `c3.htm`, `f2.htm`, `c4.htm`
  - Per-coin Hede pages: `<dir>/<reign>h<N>.htm` where `<dir>` is `chr` for Christians, `fr` for Frederiks (and presumably some path for Hans — needs verification).
  - Per-coin Galster pages: `<dir>/<reign>g<N>.htm` (Galster numbering parallel to Hede).
  - **Frederik I confirmed**: 2 Rhinsk Gylden variants under pattern `fr/f1g59.htm` etc.
  - **Christian II**: NOT in the Rhinsk Gylden link list (no Rhinsk Gylden under his reign — confirms the 1500-1533 gap hypothesis).

**Concrete known entries** (verified 2026-05-14 + 2026-05-16 Numista catalog browse):

In project scope (1514+, per §BI):
  - **Christian II Db. Guldreal ~1514** (per Wilcke p. 184 ordinance — Sovereign metric).
  - **Christian II 1 Noble 1516-1518** (Numista catalog page 1 entries, Sovereign metric).
  - **Frederik I 1 Db. Nobler 1524** (Wilcke p. 187, dukat-fineness double-noble).
  - **Frederik I 1 Goldgulden Malmö 1527** (Numista N#433743, Fr# 10, brutto 3.28 g, finhed UNVERIFIED).
  - **Frederik I 1 Rhinsk Gylden Malmö 1527** (Wilcke p. 216, Rhenish metric).
  - **Frederik I 1 Goldgulden 1531 København or Malmö** (Numista N#428864, Fr# 11, Galster 46, brutto 3.49 g, finhed .986 VERIFIED).
  - **Frederik I 1 Rhinsk Gylden Gottorp 1531** (Wilcke p. 216-217, Rhenish metric).
  - **Frederik I 1 Nobel 1532** (Galster 45, dukat-fineness half-noble).
  - Silver coinage (Skilling subdivisions 1527-1532) — secondary priority.

Out of project scope (pre-1514, per §BI) — research-doc context only, NOT cache-target:
  - **Hans 1496 Dobbeltnobel / Guldreal** (~15 g brutto, Sovereign metric).
  - **Hans 1497 Rhinsk Gylden** (per Møntordningen 4 Dec 1497).
  - **Hans ~1500 Rhinsk Gylden** (Ditmarsken batch).
  - **Hans Goldgulden ND 1481-1513** (Numista N#355730, Fr# 4, brutto 3.3 g, finhed UNVERIFIED).
  - **Hans 3 Noble / 2 Noble / 1 Noble 1496-1502** (Numista N#428914 etc., Sovereign metric).
  - **Erik VII Lund gold 1397-1439** (Numista N#426966, brutto 9.85 g, finhed UNVERIFIED, no Fr#).

**Plan.**

  1. **Map URL space** — fetch danskmoent.dk reign-overview pages (`hans.htm`, `c2.htm`, `f1.htm`) to enumerate all per-coin Hede / Galster pages under each reign. Document URL patterns.
  2. **Extend parse_hede.py** (or current fetcher) to handle Hans / Christian II / Frederik I volume URLs. Likely needs new prefix mappings if Hans pages don't fit `chr/c<N>h*.htm` or `fr/f<N>h*.htm` patterns.
  3. **Harvest cache** — fetch + parse pages into `scripts/cache/hede/h*h*.json`, `c2h*.json`, `f1h*.json` (or whatever filename convention emerges).
  4. **Update seed builder** — `scripts/maintenance/build_hede_denmark_seed.py` line 272 `_RULER_REIGN` table currently has `f2h: (1559, 1588)` etc. Add new entries for Hans (1483-1513), Christian II (1513-1523), Frederik I (1523-1533). Verify scope-filter (currently `scope_year_from: 1559` per commit `7bfd80c`) covers all — Hans pages start 1496 which is within 1559-bound (per CLAUDE.md scope 1559+ per commit `7bfd80c`); need to extend if we want pre-1559 in seed.
  5. **Re-run seed builder** to regenerate `data/seed/hede/denmark.yml` with Hans/F1 entries. Hans entries will land at top by year_first sort.
  6. **Cross-reference back to dossiers** — update `christian_iii_danish_coinage_1534_1572.md` §2.3 + `danish_royal_gold_1560_1648.md` §1.4 with the now-cached Hans entry IDs; close the «Open research item» notes about the 1500-1533 gap (we'll have data to confirm or refute).
  7. **Spawn follow-up TODOs** for Fuß-placement of Hans Rhinsk Gylden (within §AW `rhinsk_gylden_fod` Fuß), Hans Nobles (own gold type?), Frederik I gold (might fit Reichsdukatenfuß or Imperial Reichsgulden).

**Dependencies.**

  - **Scope-anchor RESOLVED 2026-05-16**: §BI sets project lower bound at **1514** (Christian II Lovkompleks). Frederik I + Christian II issues 1514+ are in scope; Hans + Erik VII pre-1514 are excluded.
  - **§AV / §AW / §AY-style Fuß-design decisions** still pending for the in-scope entries — Frederik I 1527/1531 Rhinsk Gylden waits on §AW (`rhinsk_gylden_fod` design); Frederik I 1531 Goldgulden + Christian II Nobler wait on Fuß-classification. For now, fresh-imported entries land in `seed_unsorted` as default.
  - **Cache architecture verdict needed** before harvest: (a) new `scripts/cache/galster/` directory with parallel fetch/parse scripts (cleanest source-separation), or (b) reuse `scripts/cache/hede/` with new `c2g*`/`f1g*` prefix conventions + source-detection branching in parser.

**Cross-references.**

  - Research dossiers: `docs/research/danish_royal_gold_1560_1648.md` §1.4, `docs/research/christian_iii_danish_coinage_1534_1572.md` §2.3, `docs/research/denmark_fuesse_year_boundaries.md` (reichsdukat section + Erik VII / Hans research-doc context).
  - Web sources: danskmoent.dk Galster-page series (`/f1galst.htm` index + `/fr/f1g*.htm` per-coin), Wilcke 1950 p. 183-220 (Christian II + Frederik I body coverage), Wilcke 6 (`/wilcke/w6a.htm`) + Wilcke 7 (`/wilcke/w7hans.htm`) — these last two cover Hans which is now out of scope.
  - **§BI** (1541→1514 anchor rescope) — this entry's rescope-trigger. §BF (1514-1566 gap) unblocks once §AZ harvest lands.

---

### BA. 🟢 Refine Fuß / phase descriptions + boundary years from Galster galshist  *(opened 2026-05-15)* *(est: large)*

**Surfaced.** User direction 2026-05-15 after capturing the full Galster *Danske mønter* historical overview into `docs/research/sources/galster_galshist.md` (commit `1a8ac6b`). The Galster 1965 article (excerpt pp. 23-43) is dense with dated events, mintmaster attributions, ordnance specifics, and metric details that can refine our existing Fuß / phase prose in both `data/shared/fuesse.yml` and per-location `data/locations/*.yml`. Sweep the captured source against existing rendered-prose and tighten where Galster's account adds detail, corrects a date, or clarifies a tariff relationship.

**Specific Galster passages worth mining** (non-exhaustive):

  - **1541 Møntordning + 1544 daler-at-head reform**: «Ved møntordningen af 20. sept. 1541 reorganiseredes møntvæsenet… 1544 blev daleren stillet i spidsen for det danske møntsystem, således at der herefter gik 3 mark på en daler. Denne sloges 8 stk. på den 14 1/2 lødige kølnske mark.» — explicit 1541 Marken-fin 8 stk @ 14½-lødig.
  - **Flensborg royal mint 1545-54**: «Kongen anlagde derfor en ny kongelig mønt i Flensborg, hvorfra der i årene 1545-54 udgik rhinske gylden, dalere og mindre sølvmønt.» — dates Christian III Flensborg operation precisely.
  - **Syvårskrigen 1563-1570 Klipping debasement**: «1563-4 måtte Poul Fechtel levere over 3 millioner mark i klippinge til tomark, mark, fire- og toskilling» + «den nye, runde mønt… bar stadig årstallet 1563, men var endnu ringere end før» + «daleren, der ved krigens afslutning gjaldt 4 mark (mod 3 mark 1563)» — explicit Daler-tariff drift 3 mark→4 mark across the war.
  - **1572 Elfsborgs løsen Speciedaler**: «150000 daler, som Sverige måtte udrede i Elfsborgs løsen, blev slået til dalere 1572… Lødigheden var lidt ringere (14 lødig i stedet for 14 4/18)» — precise lødighed for 1572 issue.
  - **1582 Møntordning**: «efter mange års håbløs forvirring måtte man i møntordningen af 1582 vende tilbage til 'mønten, som før gik' og dele daleren i 4 mark» — establishes 1582 cutover 3 mark→4 mark = 1 daler.
  - **Frederiksborg coin press 1582-85**: Paul Gulden imported from Danzig with new coin press; «portugaløser, rosenobel, dobbeldukat, engelot, guldkrone, guldgylden og ungersk gylden» as wedding-gift set for Sophie, FS monogram, single surviving set.
  - **1602 Møntordning**: «1602 sætte daleren til 66 skilling, men i den nye møntordning benyttede kongen lejligheden til at udnytte møntregalet og nedsætte lødigheden» — clarifies 1602 reform context (sequel to 1580 Hamborg 33 skill. lybsk = 66 skill. dansk lead).
  - **1607 Helsingør forpagtning**: Hans Fleming (Dutch) took mint in lease; first instance of mint farming. Affects mint attribution for any Helsingør entries.
  - **1608 efterligninger of West European trade coins**: «nederlandske 'løvedaler', der kun skulle være 50 2/3 skilling værd», sovereigns, breddalere — context for our gold-track imitations.
  - **Christian IV Daler-tariff escalation**: «1609 sattes daleren til 68 skilling, 1610 til 74 skilling, 1616 til 80 skilling» — explicit yearly tariff figures.
  - **1618 Krone-mønt introduction**: «Fra 1. maj 1618 indførtes kronen, der skulle gå for 1 1/2 daler… der sloges i regnskabsåret 1618-9 for ca. 154.000 daler i den nye kronemønt, hvorved kongen kunne beregne sig en indtægt på ca. 11 %» — precise 11 % seigniorage figure for 1618 Krone-mønt.
  - **1619 Kroneskilling 1/64 daler = 1/96 krone**: explicit subdivision.
  - **Glückstadt mint anlagt 1616** + Frederiksborg 1620-23 ringholdige 8-/12-skillinger.
  - **1625 final daler fixation at 6 mark = 16 skilling, held to 1813 statsbankerot**: «Daleren blev endelig fastsat til 6 mark – 16 skilling, en værdi som blev fastholdt lige til statsbankerotten 1813.»
  - **1626-29 Kejserkrigen** gold issues: «rhinsk gylden, guldkroner og rosenobler» + Norway silver.
  - **1644-48 Torstenssonkrigen Ulfeldter/Hebræer mønt** + Caspar Herbach brilledukater (Norwegian gold).
  - **1648 kongens kroning 23 november**: firkantet udkastningsmønt in gold and silver.
  - **1671 Christian V Møntordning 22. marts**: «det faste værdimål gennem århundreder var speciedaleren, hvis indhold af fint sølv var sunket lidt fra Christian IIIs tid fra 27.405 g til 25.128 g. Den blev nu fastlagt på 8 3/32 stk. på den 14-lødige mark, d.v.s. 25.281 g, og dette blev varigt til 1873.» — **canonical 1671 Speciedaler standard codification**, 25.281 g fein, held 202 years.
  - **1692 Møntordning 31. december**: 100 000 rigsdaler in kroner + markstykker, plus 5000 rigsdaler in halvskillinger (kobber). Anton Meibusch introduces improved technique.
  - **1694-5 8-skillinger in Lykstad + København**: 9-lødige, 76½ stk per Cölln. Mark — became main coin for Kurantmøntfod, joined by Lybæk + Hamborg (4 schilling lybsk).
  - **1709-1713 Store nordiske krig**: over 6⅓ million daler in ringholdige war-mønt; Kurantdukater introduced (face 2 rd. kurant = 12 mark but less worth).
  - **1726 nedsættelser**: 16 skill. → 15 skill., 12 skill. → 10 skill., 2 skill. proportional. 1727 Kurantdukater 12 mark → 11 mark.
  - **1731 24-skilling (rigsort)** introduced as main Kurant coin under Christian VI; remained until 1855.
  - **1736 Kurantbanken** established.
  - **1757 Kurantdukater indkaldt**.
  - **1764-5 170 000 specier slået svarende til Hamborg banco**.
  - **1771 (1775) Christiand'or** after French Louisd'or, for foreign payments.
  - **1776 specie-vs-kurant 4:5 ratio fixed**: 1 specie = 1 rd. 22 sk. kurant.
  - **1788 Schleswig-Holstein Speciebank in Altona** + 9¼-Fuß codification («9 1/4 speciedlr. på marken fin»).
  - **1791 Dansk-norske speciebank** + 11 July 1794 forordning equalising kongerigerne with hertugdømmerne.
  - **1813 Statsbankerot + Rigsbankdaler 18½ stk = 6 mark = 16 skilling per Cölln. Marck fein**: «18 1/2 stk. – 6 mark – 16 skilling af en kølnsk mark fint sølv». 1818 Nationalbanken replaces Rigsbanken.
  - **1826-70 Frederikd'or / Christiand'or in Altona**: 21½ karat, 35 5/24 stk på marken brutto.
  - **1854 rigsbankmønten → rigsmønt rename**.
  - **1865 latinske møntunion** + **1871 Tyskland guldmøntfod** → **1873 Skandinavian møntunion 27. maj** (Danmark + Sverige; Norge tiltrådt 16 oct 1875). 10-krone weight 4.4803 g, 20-krone 8.9606 g; krone subdivision 100 øre.
  - **Skillemønt 1873**: 2 + 1 kr at 15 + 7½ g (fein 12 + 6 g); 25 + 10 øre at 2.42 + 1.45 g (fein 1.45 + 0.58 g); 5/2/1 øre bronze.
  - **1917 25/10 øre → kobbernikkel** (WWI metal-prices); bronze → jern.
  - **1924 särskillemønt**: kobberaluminiumnikkel for 2+1 kr, kobbernikkel for 25/10 øre.
  - **1941 øremønt → zink** (WWII).

**Plan.**

  1. Walk `data/shared/fuesse.yml` Fuß entries (especially 9_thaler, 9_25_thaler, 18_5_thaler, guldkrone, kronemont*, reichsdukatenfuss, kronefod). For each, cross-check description / hintergrund prose against Galster facts. Where Galster gives a date or parameter we don't yet have, add. Where we differ, verify and reconcile.
  2. Walk `data/locations/denmark.yml`, `schleswig_holstein.yml`, `hamburg.yml`, `lubeck.yml` phase descriptions. Update boundary years (e.g. 1582 daler→4 mark cutover, 1671 Speciedaler codification, 1813 Statsbankerot). Add mintmaster attributions where missing (Povl Fechtel 1541-, Hans Delhusen, Paul Gulden 1582-85 Frederiksborg, Nicolaus Schwabe 1602, Hans Fleming 1607 Helsingør, Anton Meibusch 1692+, Caspar Herbach Norwegian brilledukater, Schimmelmann 1764-5, Freund Altona 1826-70).
  3. Verbatim-quote anchors per CLAUDE.md §5a — when adding/refining facts from Galster, cite the local capture via `docs/research/sources/galster_galshist.md` with the relevant Danish-language verbatim passage. New `*-references.yml` entries (or extend existing Galster-citing refs) where the prose now backs additional claims.
  4. **Cross-reference §AS** (verbatim-quote sweep) — many Galster-derived refs will need quote-as-locator per the new §5a rule.

**Scope assessment**: large. The Galster article spans 800 → 1914+ with dozens of dated events; not all are project-relevant (medieval pre-Reformation, post-1914 papermøntfod). Project-relevant window 1541-1914 has ~25-30 dated events worth integrating. Per-Fuß / per-location prose updates likely 50-100 small edits across many files. Suggest splitting into per-Fuß sub-passes or per-location sub-passes to avoid one monster commit.

**Cross-references.**

  - Source capture: `docs/research/sources/galster_galshist.md` (full Galster text, 489 lines).
  - Research dossiers using Galster: `daler_klippe_1604.md`, `danish_royal_gold_1560_1648.md`, `christian_iii_danish_coinage_1534_1572.md`.
  - §AS (verbatim-quote sweep) — interacts with this entry; new refs added under §BA should comply with §AS quote-as-locator convention.

---

### BB. 🟢 Fuß descriptions — historical framing only, no parameters / specific issuances  *(opened 2026-05-15)* *(est: large)*

**Surfaced.** User direction 2026-05-15 during §AG resolution. The current convention for Fuß descriptions across location files is heterogeneous: most phase `description` blocks and `fuss_periods.<fuss>.hintergrund` blocks bleed concrete parameters (fineness ‰, weight g, formula `Marck ÷ N`) and specific catalogue-issuance references (Behrens 641a–647, KM-XXX die groups, specific year groups) into prose. Per the user's articulation:

> «В описі стопи має бути історичний рамковий огляд, без параметрів стопи/монет і без конкретних карбувань, лише загально про стопу.»

**Principle (the rule going forward).**

Phase `description` and Fuß-level `hintergrund` prose convey **historical framing of the standard at this location**:

- *What* the Fuß is — its place in the imperial / Danish / regional mint tradition.
- *When* and under *what authority* it was codified (ordinance, treaty, royal decree).
- *Why* this location adopted / left it (Hanseatic affiliation, Danish-realm membership, currency-union accession, etc.).
- Broader trade / accounting context.

What MUST NOT appear in these surfaces:

- **Concrete metric parameters** — `986 1/9 ‰ Feingold`, `233.856 g ÷ 67 = 3.4419 g`, `888 8/9 ‰`, raw-vs-fine arithmetic. These belong in the Grundwerte / bar-title metric blocks and per-coin notes.
- **Specific catalogue-issuance references** — `Behrens 641a–647`, `KM-191, 195, 198, 205`, «vier dokumentierte Stempelgruppen». These belong in `coins[].note` and `coins[].catalog`.
- **Specific year groups bound to specific issuances** — «Jahrgänge 1789–1801, alle nach demselben Standard». Period years for the phase live in `pdate_label` and `year_from` / `year_to`; the prose stays general.

**Pilot — Lübeck Reichsdukatenfuß done as exemplar (this session, commit pending).** Phase description (`phases.reichsdukatenfuss[0].description`) + Fuß-level `hintergrund` (`fuss_periods.reichsdukatenfuss.hintergrund`) rewritten as historical framing — codification by Augsburger Reichsmünzordnung 1559, role through Reichszeitalter to 1871, North/Baltic trade-coin context, Lübeck's adoption as Hanseatic city. Behrens-641a–647 detail removed; ref3 (Behrens) inline `<sup>` citation dropped. Use this as the reference shape for the sweep.

**Side effect on §AG**: with Lübeck's only two inline cites of ref3 (Behrens) now removed, the §AG «Behrens page-hint missing» concern is moot for Lübeck. §AG can close as obsoleted IF the orphaned `ref3` entry in `lubeck-references.yml` is also dropped (separate small cleanup). Pre-existing Behrens-author-name error («Hans» → «Heinrich») becomes moot if the entry is deleted.

**Scope.** Every Fuß across every location file:

  | File | Fuß surfaces (phase × hintergrund) |
  |---|---|
  | `lubeck.yml` | 4 Füße (11_333_thaler, 9_thaler, reichsdukatenfuss ✓, seed_unsorted) |
  | `hamburg.yml` | ~5 Füße |
  | `denmark.yml` | ~10 Füße (incl. guldkrone, kronemont*, kurantmøntfod, rigsbankdaler etc.) |
  | `schleswig_holstein.yml` | ~12 Füße (multi-phase 9¼ and others) |
  | `holstein_schauenburg.yml`, `lubeck_bishopric.yml`, `oldenburg.yml`, `hesse_kassel.yml`, `bremen_verden.yml`, `osnabrueck.yml`, `lauenburg.yml`, `brunswick_lueneburg.yml` | per-location sweep |

≈ 60–80 total surfaces (description + hintergrund × Füße × locations). Per-surface effort: ~5-15 min — read current prose, identify parameters + specific issuances, rewrite as historical framing, drop orphaned inline refs, move concrete data into a coin note if not already present.

**Action.**

  1. Audit script `scripts/audit_fuss_description_framing.py` — heuristic detection of «parameter bleed» in phase `description` + `hintergrund`: regex-match for `‰`, decimal-gram patterns (`\d+,\d+ g`), formula patterns (`÷ \d+`), catalog-ref tokens (`Behrens \d+`, `KM-\d+`, `Hede \d+`, `Sieg \d+`, etc.). Output baseline count per location.
  2. Per-location sweep — one location per session, ~10-20 surfaces per sitting.
  3. For each surface: rewrite as historical framing per principle above. Move concrete data to coin notes where it's not already there; drop orphaned inline refs from the prose.
  4. Refs becoming orphaned after the sweep: handle case-by-case — either delete (if their only use was this surface), or keep (if they back content elsewhere).
  5. Wire the audit into pre-commit (advisory) so future Fuß-description additions don't re-introduce parameter bleed.

**Cross-references.**

  - **§BA** (Galster-based refinement) is the *content accuracy* pass — boundary years, mintmasters, parameter corrections. §BB is the *structural role* pass — what kind of statement belongs in this prose slot. Independent but synergistic; one location can run §BA + §BB together for a single coherent rewrite.
  - **§AG** (Behrens page-hint compliance) — Lübeck portion obsoleted by the §BB pilot rewrite. If §BB lands across all locations and removes all Behrens inline cites, §AG closes entirely.
  - **§AS** (verbatim-quote-as-locator) — refs that survive the §BB sweep still need the §AS quote requirement. Coordinate so refs aren't quote-cited under §AS then dropped under §BB on the next session.
  - **CLAUDE.md §0z** (three reader roles) — supports the principle: Fuß descriptions are role-3 (end-reader) surfaces; the parameter / catalog-issuance detail belongs in role-3 coin-note surfaces, not in role-3 framing surfaces. Same role, different sub-purpose.

---

### BD. 🟡 Danish-jurisdiction Müntzfuß names — switch German -Fuß to Danish -fod where authoritative sources do  *(opened 2026-05-15)* *(est: large)* *(type: research + refactor)*

**Surfaced.** User direction 2026-05-15 after Denmark-page summary cleanup. While arguing that «-Fuß is pan-German and accepted in Danish numismatics», the assertion was challenged and verified against the two main Danish-language authorities. The result inverted the assumption:

| Source | `-fod` (Danish) compounds | `-Fuß` / `-fuss` |
|---|---|---|
| **Wilcke 1950** «Renæssancens Mønt» | 27 (Møntfod, Sølvmøntfod, Guldmøntfod, Markmøntfod, Rigsmøntfod, Dobbeltmøntfod, **Dalerfod**, …) | **0** |
| **Galster on danskmoent.dk** | 7 (kronefoden, kurantmøntfoden, **9¼ speciemøntfod**, guldmøntfod, dobbeltmøntfod, papirmøntfod, …) | **0** |

The form «Dalerfod» in Wilcke is decisive — he uses it for the imperial 1559/1566 Reichsthaler standard («en Dalerfod 8 Stkr. paa 1 M 14 Lod 4 Gren fint Sølv af Vægt 29,232 gr.»), so the eponymous «9-Thaler-Fuß» in our schema has a direct period-Danish form *Dalerfod* (or *9-Dalersmøntfod* / *9-speciemøntfod* per Galster).

**Inventory of mismatched names on Denmark page** (and partially Schleswig-Holstein):

| Current schema ID + name | Danish authoritative form |
|---|---|
| `reichsdukatenfuss` / Reichsdukatenfuß | Rigsdukatfod (proposed) — Wilcke uses bare «Dukat»; no compound coined in Galster |
| `pistolenfuss` / Pistolenfuß | Pistolfod (proposed; not directly attested in Wilcke/Galster either) |
| `9_thaler` / 9-Thaler-Fuß | Dalerfod (Wilcke verbatim) / 9-Dalersmøntfod / 9-speciemøntfod (Galster idiom) |
| `9_25_thaler` / 9¼-Thaler-Fuß | **9¼-speciemøntfod** (Galster verbatim) |
| `11_333_thaler` / 11⅓-Thaler-Fuß | 11⅓-Dalersmøntfod (extrapolated from Galster pattern) |
| `18_5_thaler` / 18½-Thaler-Fuß | **Rigsbankdalerfod** (Wilcke + Galster both attest the formal name) |
| `kurantmoentfod` / Kurantmøntfod | ✓ already Danish |
| `kronefod` / Kronefod | ✓ already Danish |
| `guldkrone` / Guldkrone | ✓ already Danish |
| `kronemont*` / Kronemønt | ✓ already Danish (-mønt suffix) |
| `courantdukatenfuss` / Courantdukatenfuß | Kurantdukatfod (proposed; not directly attested) |

**Design decision needed before action.** The Müntzfuß is a *global mathematical construct* per CLAUDE.md §7 — `reichsdukatenfuss` is the same standard whether it appears on Lübeck (German jurisdiction, name `Reichsdukatenfuß` is canonical) or on Denmark (Danish jurisdiction, name `Rigsdukatfod` is the period form). Two architectures:

- **(a) Per-jurisdiction display name override.** Keep `reichsdukatenfuss` as the global ID + German canonical name; add an optional `display_name_da` (or per-jurisdiction `display_names: {danish_realm: "Rigsdukatfod"}`) on the Fuß definition; render the Danish form on Denmark + the Danish portions of Schleswig-Holstein. German pages keep «Reichsdukatenfuß».
- **(b) Global rename + per-location inline alternative.** Pick one canonical name globally (likely keep German for Reichsdukatenfuß since the standard is named after the Reichsmünzordnung) and just sprinkle the Danish synonym into the deck / hintergrund prose on Denmark («…umfaßt das Korpus der Møntfødder — Rigsdukatfod (= Reichsdukatenfuß), …»). Lower-cost, lower-rigour.

User verdict requested on (a) vs (b) before any data edit. Once chosen:

1. Confirm proposed Danish names against a third source (Sieg-Møntkatalog if accessible; Lange volumes are German so not helpful here).
2. For (a): extend `data/shared/fuesse.yml` schema with `display_names` map; update `scripts/build.py` renderer to consult the location's `km_register` / realm to pick the right form; sweep all Danish-jurisdiction surfaces (page deck, fuss section titles, bar titles, hintergrund prose).
3. For (b): inline-prose-only sweep across `data/locations/denmark.yml` + Danish phases of `data/locations/schleswig_holstein.yml`.
4. Cross-check against §BB: Fuß descriptions are role-3 framing prose, so the rename interacts with that rewrite. Coordinate so one Fuß isn't framed-rewritten under §BB and then name-rewritten under §BD on the next session.

**Out of scope.** Don't touch schema IDs (`reichsdukatenfuss` etc.) — those are internal identifiers, not user-facing. Renaming IDs would cascade across every coin entry's `fuss:` reference field and is not worth the churn.

**Cross-references.**

- **§BB** (Fuß descriptions framing) — both touch the same prose surfaces; coordinate or sequence.
- **§BE** (Danish translation for DK + SH pages) — natural co-traveller; if we add a `da:` language, the Danish Fuß names are the obvious lexical anchor for the rest of the translation pass.
- **CLAUDE.md §i18n** «Müntzfuß standard names NEVER translate» — current rule has an implicit assumption that the period-correct name is always German. §BD challenges that assumption for Danish-jurisdiction surfaces; the policy may need a paragraph carving out the jurisdiction-aware reading.

---

### BE. 🟡 Add Danish (da) translation to Denmark + Schleswig-Holstein pages  *(opened 2026-05-15)* *(est: many sessions)* *(type: feature + translation)*

**Surfaced.** User direction 2026-05-15. The Denmark page covers the dansk-norske realm; the Schleswig-Holstein page covers a duchy that sat under the Danish crown 1460–1864 and is heavily Danish in primary sources (Wilcke, Galster, Hede, Sieg, danskmoent.dk). Yet the rendered artefact only ships DE / EN / UK. Adding **Danish (`da`)** for these two pages aligns the language coverage with the source language of the historical record and serves the natural reader audience for Danish-Norwegian numismatic content.

**Scope.** Two location files: `data/locations/denmark.yml` + `data/locations/schleswig_holstein.yml`. Plus all sidecar / shared surfaces that surface on those pages:

- Per-location prose: `summary.da`, every phase's `description.da`, every `fuss_periods.<f>.hintergrund.da`, every coin's `note.da` + `verification_note.da`.
- References: `denmark-references.yml` + `schleswig_holstein-references.yml` — add `da:` content for every `ref{N}`.
- Shared issuing entities used by these pages (`data/i18n/issuing_entities.yml`): add `da:` for any entity surfacing on DK / SH.
- UI strings: `data/i18n/ui.yml` — extend with a `da:` column for column headers, button captions, section titles. (Possibly scope the UI-language only to DK + SH pages — landing + German-jurisdiction pages stay 3-lang.)
- Templates: `templates/location.html.j2` (+ landing if a Danish chip surfaces there) — add `da` to the language-switcher chip set, conditional on page.
- Build script: `scripts/build.py` — extend the per-location language loop to include `da` when the location opts in via a new `languages: [de, en, uk, da]` field (default `[de, en, uk]`).

**Estimated volume.** Denmark page = ~1125 coins (each with note + many with verification_note) + ~12 Füße × phase descriptions + summary + references (~45 refs). Schleswig-Holstein page = ~similar order of magnitude. Roughly **2000–3000 translatable text blocks** total. At ~5-10 surfaces per session for careful translation, this is many sessions of work.

**Design decisions needed.**

1. **Translator's hand.** Claude does the bulk; user reviews. Per CLAUDE.md «Never invent translations for technical German numismatic terms without confirming with the user» — Danish numismatic vocabulary is closer to source for the Danish-jurisdiction content (most of these terms came *from* Danish), so the risk is lower than for UK. Still, sample-review the first phase / first 10 coins before committing the pass.
2. **Compositionality with §BD.** Danish-form Müntzfuß names (`Rigsdukatfod`, `9¼-speciemøntfod`, etc. — see §BD) are the natural anchor lexicon for the Danish translation. Sequence §BD before §BE so the translation lands with consistent terminology, or accept some churn if they run in parallel.
3. **Schleswig-Holstein dual-jurisdiction nuance.** SH was under Danish crown 1460–1864 + Prussian province 1864–1914. The Danish translation is unambiguous for the Danish-track Füße (Speciedaler, Kurantmøntfod, Rigsbankdalerfod), but for the Prussian period (Vereinsmünzfuß, Reichsgoldmünzfuß) the Danish language is no longer the source register — period sources for 1864–1914 SH coinage are German. Decide: do we translate the Prussian-era SH content into Danish too (artificial but consistent), or scope `da:` translation only to the Danish-track phases? Probable answer — translate everything, since the reader switches the whole page at once.
4. **Per-language UI-string subset.** If `da` is added only to DK + SH, the landing-page chip set needs conditional rendering (3 chips on most pages, 4 on DK + SH). User-facing language switcher UX needs a verdict before implementation.

**Action plan (post-decision).**

1. **Foundation pass** — extend `Location` schema to support per-page `languages: [...]`; extend `data/i18n/ui.yml` with `da:` column (UI chrome); extend `templates/location.html.j2` to render the `da` chip when present.
2. **Reference sidecar pass** — add `da:` to `denmark-references.yml` + `schleswig_holstein-references.yml` (smaller volume, ~45 + ~40 entries).
3. **Page-level prose pass** — `summary.da`, fuss `hintergrund.da`, phase `description.da` (medium volume, ~50 surfaces per page).
4. **Coin-level prose pass** — every coin's `note.da` + `verification_note.da` (largest volume, ~2000 surfaces). Done per-phase / per-fuss in batches; sample-reviewed.
5. **Shared issuing-entities pass** — extend `data/i18n/issuing_entities.yml` Danish realm + Holstein duchies entities with `da:` labels + tooltips.

**Cross-references.**

- **§BD** (Danish Müntzfuß names) — sequence so the lexicon is settled before the translation pass starts. Otherwise the Danish prose has to be revised mid-stream when the Fuß names change.
- **CLAUDE.md §i18n** — current policy is DE / EN / UK only. Adding `da` to selected pages needs the policy to acknowledge per-location language sets.
- **`data/i18n/ui.yml`** — the existing 3-lang UI-string convention may need a structural revision (e.g. nullable `da:` field, or a separate `ui_da.yml` overlay).
- **Templates** — language-switcher chip implementation determines whether the `da` chip appears on landing / German-jurisdiction pages (probably hidden when the page itself has no Danish content).

---

## Low priority

_None at the moment. This section is reserved for entries we consciously postpone — when something doesn't belong in High or Normal but is also not closed, it lands here._

## Done

### BG. Harvest Norway-specific Hede pages (norge/ subfolder pattern)  *(opened 2026-05-15, closed 2026-05-17)*

**Closed.** Hede 1971 Norway sub-catalogue now mirrored in our cache. The `norge/n<ruler>h<N>.htm` filename pattern was already linked from the existing Danish-royal overviews (c{N}hede{P}.htm / f{N}hede{P}.htm) — `fetch_hede.py`'s `_extract_links` regex was the only blocker.

**Delivered (commit `4c69ce5` in submodule):**

  - `scripts/fetch_hede.py` — `_extract_links` regex extended to accept `norge/n<ruler>{N}h{M}.htm`. The `n` filename prefix marks Norge entries; basenames stay collision-free with Danish counterparts when flattened to cache.
  - `scripts/parse_hede.py` — 4 basename regexes patched to accept the optional `n?` prefix. Norge entries derive `ruler_volume: nc5h` (Christian V Norge), distinct from Danish `c5h`. Aggregate `_parsed_index.json` rebuilt with 1105 composite keys (was 952).
  - `scripts/maintenance/build_hede_denmark_seed.py` — 2 composite-key regexes patched. Norge entries land in `data/seed/hede/denmark.yml` under id `dk-hede-nc{N}h{M}`. 114 Norge entries materialised, growing total Hede seed from 639 → 753 coins.
  - `scripts/cache/hede/` (submodule): 167 new `nc<ruler>h<N>.htm` + parsed `.json` files. Discover/fetch: 167/167 success, 0 errors.

**Spot-check passed:** `nc7h12.json` (Christian VII Norge Hede 12 = 24 Skilling Kongsberg, fineness 0.562, marken-fin **11.333 rd**) exactly matches the curator's annotation on `dk-tid-55898` in denmark.yml (KM# 250, Hede 12A–12B, Brekke 31–36, 1772-1788, Kongsberg, 11⅓-Thaler-Fuß).

**Known follow-up gaps** (not blockers for §BG closure):

  - 53 Norge pages skip seed emission (no parseable spec block, non-DK mints like «Gimsø» / «Bergen» missing from `DK_MINT_DE` whitelist, or no canonical-Hede match). Cache + per-page JSON cover all 167 entries; refinement is a separate small TODO.
  - `dk-tid-55898` curated entry uses `hede_volume: c7h` rather than the Norge-aware `nc7h` — a curator-side data-consistency follow-up to decide on Norge vs Danish ambiguity in the `hede_volume` field.

---

### BJ. NumisMaster harvest Phase 3+4 — scope filter + bulk raw-HTML cache fetch  *(opened 2026-05-16, closed 2026-05-17)*

**Closed.** All 3 in-mission sub-scopes fetched to `scripts/cache/numismaster/<sub_scope>/MC_<N>.html` byte-for-byte, with companion `MC_<N>.meta.json` (HTTP status + headers + html_bytes + fetched_at) and incremental `_manifest.json` (crash-safe resume).

**Final tallies (0 errors across all 1892 MC pages):**

  | sub-scope            | fetched   | size    |
  |----------------------|-----------|---------|
  | schleswig_holstein   | 561/561 ✅ | 114 MB  |
  | denmark              | 987/987 ✅ | 201 MB  |
  | norway               | 344/344 ✅ |  71 MB  |
  | sweden_christian_ii  | 0/0       | —       |
  | **TOTAL**            | **1892**  | **386 MB** |

**Sweden-Christian-II** closed earlier (§BI) as 0-entry negative finding — NumisMaster's Sweden floor is 1573, no Danish-Swedish-union (1514-1523) entries exist in their catalog.

**Wall-clock**: ~22h end-to-end at 30s pacing. URL pattern corrected during smoke-test: `https://numismaster.com/MC_<N>` (NOT `.html` — 404). Chained sub-scopes auto-launched via Monitor poll-loop detecting `pgrep` of prior fetcher exiting.

**Submodule commits** (`munzfuss-harvest`): `f052e66` (Phase 3 + 5-MC smoke) + `bdb6b0d` (SH) + `22c7901` (DK) + `506635d` (NO). **Superrepo pointer bumps**: `6a8af64` + `a4ebfae` + `193d69d` + `3b78876`.

**Operational artifacts** for next session:

  - `scripts/fetch_numismaster.py` — `--filter-scope` (Phase 3) + `--fetch <sub_scope>` (Phase 4). Crash-safe resume via manifest.
  - `docs/HARVEST_GUIDE.md` §«Phase 4 — urllib bulk fetch (§BJ)» — concrete recipes including the chaining Monitor poll-loop.

---

### BK. NumisMaster Phase 5 — parse + seed (from local cache only, no NumisMaster traffic)  *(opened 2026-05-16, closed-partial 2026-05-17)*

**Closed-partial.** Mechanical pipeline complete; seed YAML activation deferred to §BF promotion-prep.

**Delivered:**

  - `scripts/parse_numismaster.py` — sub-scope-aware parser (renamed from `parse_numismaster_pre1541.py`, kept legacy for backwards compat). Walks every `MC_*.html` in `scripts/cache/numismaster/<sub_scope>/` → sibling `MC_<N>.parsed.json` with structured field extraction + cross-refs (Sch / L / Fr / KM / MB / Sieg / Hede / Bruun / Schive). Idempotent. Ran against all 3 sub-scopes: **561 + 987 + 344 = 1892 parsed.json files, 0 fails**.
  - `scripts/maintenance/build_numismaster_seed.py` — sub-scope seed builder reading parsed.json files → emitting `data/seed/numismaster/<sub_scope>.yml`. Merge-aware via `scripts/lib/seed_merge.py` (§BL). Validated for idempotency + no-regression + curation-preservation. **Schema-clean filtering**: extra-vocabulary refs (mb / schive / numismaster_mc) preserved on parsed.json but dropped from seed YAML; enrichment fields use `_`-prefixed keys that `build.py`'s seed-merger strips before validation.

**Deferred (§BF prep work, NOT §BK):**

  - **Seed YAML activation** — emitting `data/seed/numismaster/{schleswig_holstein,denmark,norway}.yml` triggers build validation errors («no phases defined for fuss 'seed_unsorted'») until the target locations declare `seed_unsorted.numismaster` phase config. That's a location-curation step the curator owns. The builder runs correctly; seeds activate once the locations are prepped.
  - **Dedup report** — `numismaster_dedup_report.json` listing each MC_ID's potential overlap with existing curated KM#/MB#/Schou#/Lange#/Hede#/Sieg# refs. Defer to a separate small TODO when curator is ready to start §BF promotion of NumisMaster entries.

**Commits**: `b4c1b3b` (parser + builder) + `aa16c6e` (§BL TODO closure) + `260e9ad` (HARVEST_GUIDE recipes) + chain of submodule cache commits as fetches completed.

---

### BL. Upgrade 4 wholesale-write seed builders to merge-aware (preserve manual overrides)  *(opened 2026-05-16, closed 2026-05-16)*

**Closed (commit `f250417`).** All 4 sibling builders (`build_bruun_denmark_seed.py` / `build_galster_denmark_seed.py` / `build_numismaster_pre1541_seed.py` / `build_numista_pre1541_seed.py`) now apply the same 4-mechanism merge that `build_hede_denmark_seed.py` already implements. Logic extracted to **`scripts/lib/seed_merge.py`** as a shared module so future updates to merge semantics propagate to all 5 builders without 4× copy-paste.

**Mechanisms (per CLAUDE.md §«Manual-override preservation»):**

  1. **`CURATED_FIELDS`** (fuss / phase / fraction / issuing_entity / kind / note / mint_verified / verified) — existing wins when present; absence inherits fresh default.
  2. **`DEEP_MERGE_FIELDS`** (`catalog`) — dict deep-merge; existing keys win, fresh keys fill gaps.
  3. **`_VERIFIABLE_FIELDS`** (fineness / weight_rough_g / diameter_mm / mint) — verified-wins-over-unverified per CLAUDE.md §4: source-attested existing value beats fresh's `(?)`-marked reading.
  4. **`_curation_holds: [field, ...]`** — per-entry escape hatch for fields outside `CURATED_FIELDS`; freezes EXISTING state (present-or-absent) across regen.

**`--no-merge` flag** added to each builder for legacy wholesale rewrite (verification / dry-run paths only).

**Validation (all 4 builders):**

  - **Idempotency**: running a builder twice in succession produces 0-line diff.
  - **No regression on un-curated seed**: `--no-merge` (wholesale) vs default (merge) produces 0-line diff when no curation has been applied.
  - **Curation preservation**: simulated curator edit on `dk-bruun-14708` (set `fuss: testpistolen_curator_edit` + `note`) survived a regen cycle.

**Counts after re-run** (entries in each seed file): bruun 38, galster 79, numismaster 3, numista 56 — unchanged from pre-§BL baseline (no data regression).

**Hede builder unchanged** — retains its inline implementation (parity with the new shared module; optional future refactor to import `seed_merge` instead of carrying its own copy).

§BK (NumisMaster Phase 5 parse + seed) now safe to land — the first curation cycle on the new numismaster seeds won't wipe the curator's work.

---

### BI. NumisMaster harvest Phase 1+2 — catalog walk + MC_ID enumeration  *(opened 2026-05-16, closed 2026-05-16)*

**Closed.** Chrome MCP catalog walk + per-filter MC_ID enumeration COMPLETE. `scripts/cache/numismaster/mc_index.json` now anchors **1981 MC_IDs across 12 filters** (commit `1d41e0d` in `munzfuss-harvest` submodule):

  - **A. Schleswig-Holstein cluster** (9 cadet-line filters, all in scope per user 2026-05-16): HOLSTEIN-GOTTORP-RENDSBORG (4) + GLÜCKSTADT (96, carried over from Phase 1a) + SH-GLUCKSBURG (4) + SH-NORBURG (4) + SH-PLOEN (20) + SH-SONDERBURG (25) + SCHLESWIG-HOLSTEIN main (65) + SCHAUMBURG-PINNEBERG (167, includes HOLSTEIN-SCHAUENBURG roll-up) + SH-GOTTORP (176) = **561 MCs total**.
  - **B. DENMARK** with Sort=Date ASC: walked pages 1-40 (1000 cards spanning 1591-1919); 987 retained after `year_first <= 1914` filter. NumisMaster reports 1308 total Denmark entries; pages 41-53 (1915-2024) skipped as out-of-mission. NumisMaster Denmark floor confirmed at 1591.
  - **C. NORWAY** with Sort=Date ASC: walked all 23 pages (560 cards spanning 1608-2024); 433 retained after `year_first <= 1914` filter. NumisMaster Norway floor confirmed at 1608 (KM_4 Lion Dalar). Post-1814 entries kept for cross-boundary completeness; §BK applies stricter `<=1814` filter to Norway-track entries.
  - **D. SWEDEN under Christian II 1514-1523**: NumisMaster Sweden floor = 1573 → ZERO entries for the Danish-Swedish union era. Sub-scope D closed as negative finding.

**Process artifacts** captured in `scripts/cache/numismaster/_walks/` (28+ files): per-filter `leaf_*_p<N>.txt` raw page-text dumps + `_phase_1b_findings.md`, `_phase_1b_*` process docs.

**Canonical NumisMaster walk recipe** (codified at `docs/HARVEST_GUIDE.md` NumisMaster section, commit `be9ccf8`):
  1. JS-console clear cookies + sessionStorage + localStorage between walks.
  2. Navigate `/coins`, click «Show more» to expand the 742-country sidebar.
  3. JS-direct `input.click()` on the target filter checkbox (matching label text exactly).
  4. JS-direct `sel.value = 'mc_basedate//'; sel.dispatchEvent(new Event('change', {bubbles:true}))` for Sort=Date.
  5. Paginate via `?id=-10012282&advancedsearch=true&pageno=N`; iterate `.iossearchresult` wrapper elements (DOM order = visual rank order via `id="iossearchresultN"`).
  6. Compact extraction (`mc,year_first,year_last` per line) keeps each page's JS return under the tool output cap.

**Next**: §BJ (urllib /MC_<N>.html bulk fetch) now unblocked. ~1981 MC HTML pages to fetch (after Norway-track post-1814 filter narrows further). ~15-17 hours background fetch budget at 30s pacing.

---

### BJ. Survey alternative-to-Hede sources for the 1514-1541 sub-window  *(opened 2026-05-16, closed 2026-05-16)*

**Output**: `docs/research/denmark_pre_1541_source_survey.md` (commit `ce17488`). Comprehensive survey of 14 sources covering Denmark + Norway + Schleswig-Holstein 1514-1541 coinage. All six §BJ Definition-of-done criteria satisfied.

**Three-tier harvest plan for §AZ (the implementation TODO)**:

  - **Tier 1 — local-cache enrichment (zero web cost)**: Bruun parsed lots (38 pre-1541 specimens already in `scripts/cache/bruun/lots/part{1-4}.json` with full Sieg/Schou/Galster/Fr/Lange/Dav cross-refs); Wilcke 1950 ordinance-level master tables (chapters 7-2 + 7-3 + 7-4 already in local TXT cache).
  - **Tier 2 — danskmoent.dk Galster harvest**: confirmed URL patterns `c2galst.htm` (Christian II index, HTTP 200) + `f1galst.htm` (Frederik I index, HTTP 200) + per-coin pages `chr/c2g<N>.htm`, `fr/f1g<N>.htm`, `norge/n<r>g<N>.htm`. Per-coin data shape uniform (Bruttovægt + Finhed + Finvægt + cross-refs + Litteratur). `c3galst.htm` does NOT exist (HTTP 404) — Christian III pre-1541 needs per-coin enumeration via `chr/c3g<N>.htm`. New cache directory `scripts/cache/danskmoent/galster/` recommended. ~50-80 pages estimated.
  - **Tier 3 — Numista Chrome MCP enrichment (LAST per user direction)**: ~50 pre-1541 entries; cross-validates Tier 1+2; no API calls.

**Cross-reference key resolved**:

  - **MB#** = Swedish-specific (Tingström / Stiernstedt), **NOT Münzkabinett Berlin** — appears only on Swedish Riksdaler 1534 lot in entire Bruun corpus.
  - **Sieg#** = densest single cross-ref (37/38 pre-1541 Bruun lots).
  - **Schou 1926** = Schou's «Beskrivelse af danske og norske mønter 1448-1814 og danske mønter 1815-1923» — predecessor to Hede, comprehensive Danish + Norwegian coverage. Bio at `https://www.danskmoent.dk/schou.htm`.
  - **Sømod** = third Danish cross-ref spine (column on `c2galst.htm`).
  - **Schive 1865** = primary Norwegian reference (Schive XV.7-9, XVI.1, etc.).
  - **Lange 1908-12** = primary Schleswig-Holstein reference.
  - **Jensen-Skjoldager «Tronraneren» 2021** = primary Frederik I die-variant authority.
  - **Hede#** at pre-1541: only `c3h3-3A` (Mark 1541, Bruun-4282) onwards — Hede starts at 1541 Møntordning.

**Two background agents stalled (600s watchdog) but contributed key clues before stalling**: `c2njj.htm` (Christian II historical article on danskmoent.dk) discovered; Schou 1926 Internet Archive availability confirmed by one agent (specific Archive.org URL needs follow-up).

**Sibling TODO ready**: §AZ now has concrete architecture (Tier 1-3) and is unblocked for implementation. §BF pre-1541 sub-window depends on §AZ.

---

### BI. Denmark-track anchor rescope 1541 → 1514 — Christian II Lovkompleks  *(opened 2026-05-15, closed 2026-05-16)*

**Decision (user direction 2026-05-16):** Denmark-Norway track lower bound moves from Christian III's 1541 Møntordning to the **Christian II Lovkompleks of 1514-1515** — the four-act legal package per Wilcke 1950 p. 183-186 verbatim:

  - **Sommeren 1514** — Møntordning DK (Dienis Malmö Brev, both metals: Nobler 23½ Karat 16/Mark + Rhinsk Gylden 18 Karat 72/Mark + Skilling fractions, with Rigsrådets Raad og Samtykke)
  - **3 August 1514** — Møntordning Norge (extension under Kalmar Union)
  - **Paasketid 1515** — Kvittering (compliance receipt)
  - **24 August 1515** — Sjælland åbent Brev (Sjælland renewal)

First comprehensive Danish-Norwegian legal act covering both metals + both kingdoms. Independently corroborated by Numista's currency-taxonomy boundary («Penning 825-1513 → Gulden 1513-1572»). Christian III's 1541 Møntordning is now correctly positioned as the THIRD major Danish-Norwegian Møntordning in this Lovkompleks lineage.

**Scope STRICTLY Denmark-track only** — Schleswig-Holstein and all German-jurisdiction pages remain at their existing 1559/1566 anchor per §BI's explicit scope-restriction.

**Closure deliverables** (commit `ab9e552` + `c0687a7`):

  - CLAUDE.md mission statement: Denmark-Norway lower bound line rewritten 1541→1514 with full Lovkompleks citation. German lands 1559/1566 line unchanged.
  - `data/locations/denmark.yml`: top-level + timeline `year_from: 1541→1514`; summary deck rewritten (DE/EN/UK) — Christian II 1514 Lovkompleks as opening anchor, 1541 Møntordning as mid-period silver reform.
  - `scripts/maintenance/build_hede_denmark_seed.py`: `--year-from` default 1541→1514 + extended help text (notes Hede 1957 has no pre-Christian-III coverage; 1514-1540 sub-window empty until §AZ Galster import lands).
  - `data/seed/hede/denmark.yml`: regenerated — `scope_year_from: 1514`.
  - `docs/handoff.md`: Current focus rewritten; §AZ scope confirmed.
  - `docs/research/moentordning_1541.md`: header status-update banner — dossier remains accurate for the 1541 Møntordning specifically but is no longer the project-anchor dossier; positioned as the THIRD Møntordning in the Lovkompleks lineage.
  - `docs/research/denmark_fuesse_year_boundaries.md`: reichsdukat section reworked — 1514 = project anchor (legal); 1531 = first verified .986 strike; summary table extended.
  - `docs/TODO.md`: §BF rescoped «1541-1566 gap» → «1514-1566 gap»; §AZ rescoped (Hans + Erik VII excluded as pre-1514 outliers; Christian II + Frederik I 1514+ in scope).

**Render verified**: Denmark page DE/EN/UK shows `1514–1914` in H1, deck, timeline, hero-stats — all consistent. NO changes to any German or Schleswig-Holstein file.

**Cleanup note (commit `c0687a7`)**: §BJ (created during §BI closure as «Hede catalog extension») was discovered to be a duplicate of existing §AZ + structurally wrong (Hede 1957 doesn't catalogue pre-Christian-III rulers). §BJ deleted; §AZ rescoped per §BI anchor decision; «Hede catalog extension» language replaced with «Galster + Jensen-Skjoldager catalog import (new source family)» across all affected files.

**Follow-ups still open** (separate TODOs):

  - **§BF** (Denmark 1514-1566 gap data population) — remains in Highest priority. Sequenced after §BI; ready to start.
  - **§AZ** (Galster + Jensen-Skjoldager catalog import for Christian II + Frederik I) — in Normal priority. Unblocks §BF pre-1541 sub-window when it lands.

---

### BC. Denmark timeline start year — DECIDED: dual-anchor 1541 (Denmark) / 1559 (German lands)  *(opened 2026-05-15, closed 2026-05-15)*

**Note 2026-05-16**: superseded by §BI — the Denmark anchor moved further back from 1541 to 1514 (Christian II Lovkompleks). §BC's original decision stands as the first step of the eventual two-step anchor move; §BI is the final state.

**Decision (user direction 2026-05-15):**

> «наше дослідження для німецьких земель стартує з 1559 (1566) років
> (авгсбурзький ордонанс), а для данії — з 1541 (Møntordning, той що
> весняний і той що осінній)»

The Denmark timeline start year is **1541**, anchored by Christian
III's *complete* monetary-reform pair (both ordinances together):

  - **Spring 1541** — «Om Maal og Vægt» Forordning of Søndagen Oculi 1541 = **20 March 1541**. Establishes Cølnsk Vægt (Cölln. Mark = 233.856 g) as Denmark-Norway realm-wide silver-trade weight unit. Verbatim text: [`docs/research/sources/paus_christian_iii_1541_maal_og_vaegt.md`](sources/paus_christian_iii_1541_maal_og_vaegt.md).
  - **Autumn 1541** — Møntordning of Dinstag nach Crucis 1541 = **20 September 1541**. Establishes centralised mint (Klarekloster, København), Povel Fechtel as mintmaster, 6-denomination structure (Mark, ½M, 4ß, 1ß, Hvid, Penning) with explicit fineness + brutto-weight per denomination, mønterløn schedule, mintmaster + warden oaths. Verbatim primary source: [`docs/research/sources/wilcke_1950_christian_iii_moentreform.md`](sources/wilcke_1950_christian_iii_moentreform.md); manuscript scans: [`docs/research/sources/rigsarkivet_tk_160_diverse_moentsager.md`](sources/rigsarkivet_tk_160_diverse_moentsager.md).

The German-lands timeline retains its existing anchor: **1559** (Augsburger Reichsmüntzordnung) / **1566** (Reichsabschied formal adoption) — start of standardised imperial coinage. CLAUDE.md mission statement updated to reflect the dual-jurisdiction anchor (same commit as this closure).

**Why dual anchors and not single «whichever is earlier»**: the two jurisdictions had structurally independent monetary frameworks until Helstaten 1813. German cities (Lübeck, Hamburg, Schleswig-Holstein as duchy, Bremen-Verden, etc.) followed imperial Reichsthaler / Reichsdukat hierarchy seeded 1559. Denmark followed Daler / Mark Danske hierarchy seeded by Christian III 1541. Schleswig-Holstein has dual jurisdictional status post-1864 (Danish 1813-1864, Prussian 1864-1914) — the location's phase periodisation reflects this lineage.

**Closure deliverables** (all in this commit batch):

  - CLAUDE.md mission statement: «ca. 1559–1914» → dual-anchor explicit.
  - `scripts/maintenance/build_hede_denmark_seed.py` `--year-from` default: 1559 → 1541.
  - `data/seed/hede/denmark.yml` `scope_year_from`: 1559 → 1541.
  - `docs/research/moentordning_1541.md` header marks the dossier as the project's Denmark anchor reference.
  - `docs/research/christian_iii_danish_coinage_1534_1572.md` header marks the wider dossier as the Denmark anchor period documentation.
  - `docs/handoff.md` records the decision.

**§BC sub-tasks remain open** (now demoted from §BC to follow-up TODOs in this Done note):

  1. **`christian_iii_dalerfod` Müntzfuß** in `data/shared/fuesse.yml` — canonical metric mf 8.827 / Cölln. Mark 233.856 g / per-Daler 26.494 g fein / fineness 0.906. **NOT YET DONE** — separate normal-priority TODO.
  2. **`fuss_periods.christian_iii_dalerfod`** in `data/locations/denmark.yml` with phases A1 (1541-1543 København baseline) + A2 (1544-1555 København debased). **NOT YET DONE**.
  3. **Seed-coin promotion**: c3h3-3A, c3h4, c3h5, c3h7 (Mark, 8 Sk, 4 Sk, Hvid u.år) → phase A1; c3h3-3B → phase A2. **NOT YET DONE**.
  4. **Flensborg Phase A3/A4**: sub-phase decision (separate Müntzfuß for Lybsk-aligned Flensborg track vs same Fuß with mint differentiation). Per §7.1 of moentordning_1541.md the 1547 Flensborg dual-zone is the genealogical seed of later `18_5_thaler` / `34_marck` family vs `9_thaler` family — likely deserves its own Müntzfuß. **NOT YET DONE — open design question for next session**.
  5. **References** in `denmark-references.yml` for Wilcke 1950, Galster 1965, Paus 1752, Rigsarkivet folio — **NOT YET DONE**.

These five operational tasks should be tracked as new normal-priority TODOs going forward.

---

### AG. Long-form refs page-hint compliance — last paginated survivor dropped  *(opened 2026-05-13, closed 2026-05-15)*

**Original scope.** After §S closure (2026-05-13) the page-hint rule (CLAUDE.md §5a) was enforced on all known paginated refs except one residual: `lubeck-references.yml:ref3` — Behrens 1905 «Münzen und Medaillen der Stadt und des Bistums Lübeck» (Berlin 1905, paper-only book, 290 pp, paginated). Per §5a strict «paper-only refs need page hint OR DROP, no exempt tier».

**Investigation 2026-05-14 / 15.** Behrens 1905 not digitally accessible at acceptable granularity — HathiTrust gated, Google Books snippet-only, archive.org search yielded no matching scan. Without a page hint and without a digital secondary citing the paper with a page number, the ref violates §5a by construction.

**Resolution — superseded by §BB rewrite.** During the Reichsdukatenfuß historical-framing rewrite (commits `4715097` 2026-05-15 + `a96911e` 2026-05-15), both inline `<sup>[3]</sup>` citations of Behrens were removed: the new framing prose cites general imperial-gold-standard sources (MGM Reichsdukat ref5, Wikipedia DE «Lübeck» ref6, Wikipedia DE «Münzgesetz» ref7, Museum Rantzau ref8, MGM Handelsdukat ref9) — none requiring Behrens. ref3 became an orphan; per §5a «no orphaned refs» the entry was dropped from `lubeck-references.yml` (commit pending).

**Side benefits of the drop.** Two pre-existing errors in the ref3 body are eliminated automatically:
  - Author name «Hans Behrens» → should be «Heinrich Behrens».
  - Title «Münzen und Medaillen der Stadt Lübeck» → missing «und des Bistums».

**Audit-script status.** The pre-flagged 8 other refs (denmark:ref6/ref10/ref18/ref20; sh:ref29/ref30/ref38; german_fuesse:ref38) are single-page web articles per the 2026-05-14 rule-narrowing — not paginated, page-hint not applicable. They're covered by §AS (verbatim-quote-as-locator) instead. The `scripts/audit_refs_page_hints.py` step originally in the §AG plan was never built — current §AG-scope work was resolved without it, and §AS implementation will cover the broader ref-compliance audit.

**Closure (2026-05-15).** Zero paginated refs in the project now missing page hint. Future paginated-source additions are governed by §5a (honor-system until the pre-commit lint lands).

---

### AY. f2h8 «3 Mark» classification — silver Speciedaler, not gold one-off  *(opened 2026-05-14, closed 2026-05-14)*

**Surfaced.** Initial framing in `docs/research/danish_royal_gold_1560_1648.md` and §AU promotion treated Hede f2h8 («3 Mark» 1560, 1563, brutto 29.232 g, finhed 0.906/0.937, fein 26.491/27.405 g) as a **«heavy gold one-off»** requiring classification investigation — possibly Schaumünze or proto-Daler-gold.

**Investigation result** (2026-05-14, via Hede f2h8 raw text extraction):

> «I katalogerne rubriceres denne mønt normalt som **1 speciedaler**.»
> «1560 (Hede 8A): finhed 0.906, fein 26.491 g, Marken-fin 8.827 speciedaler»
> «1563 (Hede 8B): finhed 0.937, fein 27.405 g, Marken-fin 8.533 speciedaler»
> «Mønten synes slået for **privat regning**.»
> «**Guldafslag** (RRR; Schou 6) 10 Dukat.»

So f2h8 is **a SILVER 1 Speciedaler**, not gold:

  - Catalogues classify as «1 speciedaler» (silver).
  - «III MARCK DANSKE» reverse legend is the nominal-account label (1 Speciedaler = 3 Mark Danske under Christian-III pre-1602 convention).
  - **Privately minted** (private account, not state ordonnance) — only 16 specimens of 1560 sub-letter.
  - Hede sub-letter split: 8A (1560) Marken-fin 8.827 = identical to Christian-III-1541 base standard (c3h3 Hede 3A); 8B (1563) Marken-fin 8.533 = slightly heavier private mintmaster's choice.
  - **Guldafslag** (gold off-strike, 10 Dukat face) is RRR single specimen — per CLAUDE.md §9 exclusion #3 (off-strike single specimens), out of circulation register.

Per **Aagaard, Sven**: *Privat udmøntede speciedalere 1560 og 1563 under Frederik II samt 1590 og 1596(?) under Christian IV* (NNUM 2/2009, pp. 47-54), f2h8 belongs to a small set of privately-minted speciedalere from Frederik II and Christian IV reigns, also covering Christian IV's c4h43 «1 Speciedaler 1590».

**Closed** (commit `<this commit SHA>`):

  - Seed entry split from single `dk-hede-f2h8` (incorrectly `metal: gold, nominal: 3 Mark`) into **`dk-hede-f2h8a` (1560)** + **`dk-hede-f2h8b` (1563)** — both `metal: silver, nominal: 1 Speciedaler`, fineness 0.906 / 0.937 respectively. `verification_note` explains the privately-minted context, the Marken-fin distinction, and the Guldafslag off-strike exclusion per §9.3.
  - Both stay in `seed_unsorted` for Fuß placement — they belong to the **Christian-III-Daler-fod silver tradition** documented in `docs/research/christian_iii_danish_coinage_1534_1572.md` §8 Phase A, classification deferred until that broader silver-Fuß design lands.
  - Build merged 411 seed coins (was 410, +1 from f2h split).
  - Research dossiers `danish_royal_gold_1560_1648.md` and `christian_iii_danish_coinage_1534_1572.md` both updated (commit `7d99174`) with the correct f2h8 framing.

---

### AU. Promote Frederik II gold 1563-64 from Hede cache to seed  *(opened 2026-05-14, closed 2026-05-14)*

**Surfaced.** Umbrella research dossier `docs/research/danish_royal_gold_1560_1648.md` §1 documents Frederik II's full 1563-64 gold issuance from the Bremerholm goldsmith workshop (f2h1–f2h8, none of which were in our seed yaml at time of opening).

**Dependency resolved**: project scope extended 1566→1559 (Augsburger Reichsmünzordnung anchor) in commit `7bfd80c` — opens room for pre-1566 entries. Per dossier's «classify later» fallback path, all 7 entries land in `seed_unsorted` for now; Fuß classification deferred to §AV (Guldkrone-fod), §AW (Rhinsk Gylden), §AY (3 Mark one-off).

**Closed**: 7 seed entries added in commit `<this commit SHA>` to `data/seed/hede/denmark.yml` as `dk-hede-f2h1` through `dk-hede-f2h8` (skipping f2h7 which isn't a gold issue in our cache):

  - `dk-hede-f2h1`: 1 Ungersk Gylden 1563, fineness 0.986, fein 3.442 g
  - `dk-hede-f2h2`: 1 Guldkrone 1563, fineness 0.934, fein 3.120 g (4860 stk by Hans Willers)
  - `dk-hede-f2h3`: 1 Rhinsk Gylden 1563, fineness 0.77, fein 2.500 g
  - `dk-hede-f2h4`: 1 Dukat 1564, fineness 0.986, fein 3.442 g
  - `dk-hede-f2h5`: 1 Guldkrone 1564, fineness 0.934, fein 3.120 g (Bremerholm)
  - `dk-hede-f2h6`: 1 Rhinsk Gylden 1564, fineness 0.77, fein 2.500 g
  - `dk-hede-f2h8`: 3 Mark gold 1560/1563, fineness 0.906, fein 26.491 g (one-off, see §AY)

All entries: `fuss: seed_unsorted`, `phase: hede`, `metal: gold`, `mint: Kopenhagen`, `ruler: Frederik II.`, `verified: false`, fineness + weight verified (Hede direct). Catalog refs include hede/hede_volume/schou/sieg/fr per cache. Build merged 410 seed coins (was 403, +7) — clean.

Total seed coins increased 605 → 612; scope 1559-1914.

Next steps tracked separately: §AV (Guldkrone-fod design), §AW (Rhinsk Gylden Fuß), §AY (3 Mark classification) — all use these seed entries as input.

---

### AC. 9-Fuß Speciedaler family sister entries — family-wide consolidation  *(opened 2026-05-13, closed 2026-05-14)*

**Surfaced.** While processing the user's 2026-05-13 «Hede 56D / 48 / 50AB / 55 → 9-Fuß» direction (commit `950c6ec` moved 5 entries), audit identified additional curated entries with the SAME Marken-fin 9.0/9.071 Hede attestation that suggested they too belonged in 9_thaler, but were outside the user's strict 1646-1651 scope.

**Decision (user direction 2026-05-14).** «якщо Хеде вказує що "marken_fin: 9.071 speciedalere" то це не може бути 9.25-талер, це 9-талер але трішки погіршена версія». Per-candidate Δ-verification confirmed uniform pattern across all 7 candidates: Δ to 9_thaler ≈ −0.9 % (cluster-typical specimen variance) vs Δ to 9_25_thaler ≈ +1.9 to +2.7 % (worse fit, over Soll). Family-wide consolidation justified by Hede source attestation, not derived hypothesis.

**Moved 7 entries** (commit `6dd15a1`):

  - denmark: km-100-chr-iv-1624 (½ Sp 1624-1634, Hede 59A+B); km-104-hede-56b-chr-iv-1627 (2 Sp 1627, Hede 56A+B+C); km-104-hede-56c-chr-iv-1631 (2 Sp 1631, Hede 56C); km-135-chr-iv-1646 (½ Sp 1646, Hede 59C); km-161-fr-iii-1648 (¼ Sp Klippe 1648, Hede f3h47); km-159-fr-iii-1648 (1/12 Sp 1648, Hede f3h49).
  - schleswig_holstein: km-34-chr-iv-1646 (½ Sp 1646, Hede 165).

**Phase boundary updates** to accommodate migration:

  - denmark 9_thaler/II: year_from 1646→1624. Title trimmed from «Späte 9-Fuß-Speciedaler-Familie» to «9-Fuß-Speciedaler-Familie» (phase now covers full 1624-1683 span). Description rewritten to introduce the Christian IV 1624-1648 cluster at the top + retain Frederik III / Glückstadt narrative.
  - SH 9_thaler/II: year_from 1683→1646. Title appended «(1645/46 + 1683)».

---

### S. Add page numbers to long-PDF / book refs  *(opened 2026-05-13, closed 2026-05-13)*

**Surfaced.** Bibliography entries pointing to long PDFs / books were sometimes citing a single claim without naming the page — forcing the reader to skim hundreds of pages to verify. CLAUDE.md §5a recommended a scope note (≤ 140 chars) but the page-hint requirement was implicit, and an audit-sweep across the project's references files turned up three entries lacking concrete pages plus one umbrella ref that bundled four Bruun PDFs under one slot (violating the «atomic refs» rule).

**Sweep done in one pass (audit + fixes):**

* `schleswig_holstein-references.yml::ref38` — was a Stack's Bowers Bruun-collection umbrella (4 PDFs, 350+ pp each, no page hints). The only inline `<sup>[38]</sup>` citation in SH yaml backs the verbatim Plakat 1782 quote; full text-search across all four cached Bruun PDFs (`scripts/cache/bruun/pages/part*.txt`) confirms that phrase is NOT in Bruun. Repurposed ref38 to mirror `german_fuesse-references.yml::ref38` (danskmoent.dk Christian 7 ordinances) — the actual source. Bruun stays cited inline in per-coin `sources[]` arrays with full part + lot + page detail; bibliography-level Bruun umbrella was dead weight.
* `german_fuesse-references.yml::ref7` — Meyers Konversationslexikon 1888 Müntzfuß (Wikisource). Located the article in the underlying print original: Band 11, S. 890–891. Page hint added to scope note in all three languages.
* `german_fuesse-references.yml::ref12` — Adolf Soetbeer's *Denkschrift betreffend deutsche Münzeinigung* (1869, 91 pp). Located the verbatim Bankvaluta quote via archive.org's djvu text search: page 4. Page hint added.
* `denmark-references.yml::ref21` — Abildgren 2004 (32 pp) was already fixed in an earlier session (commit `8cb9a7a`): p. 14 (1914 gold-suspension) + p. 17 (1927 parity return). Listed here for completeness.

**Rule strengthened (CLAUDE.md §5a):** added a «Mandatory page hints for long-form sources» sub-section that makes concrete page references **required** for any ref whose underlying work is ≥10 pages — PDF book, multi-chapter monograph, auction catalogue, periodical issue, multi-volume Konversationslexikon, scanned ordinance gazette. Approximate ranges, vague descriptors («passim», «ungefähr Mitte», «im ersten Kapitel»), and umbrella-of-PDFs refs are now explicitly forbidden. The rule lists acceptable forms (`(S. 14)` / `Band 11, S. 890–891` / `Kap. 4, S. 123–125` / `§ 5, S. 12`) plus the Wikisource exception (use the underlying print source's pagination when transcribed; section anchor for pure wiki-only articles).

Future refs are caught by the rule at write-time; the sweep is no longer needed as a recurring TODO.

### I. Restructure `\n`-joined source labels in scalar metric fields  *(closed 2026-05-10)*

**Surfaced.** Multi-source attestations on a single value (e.g. `weight_rough_g: [{value: 28.893, source: "Hede 39A\nNumista"}]`) buried two independent citations in a `\n`-joined string. Audit / dedup / query code had to re-parse the display string with `re.split(r"[,;\n]", …)` — the parser-of-display-string anti-pattern.

**Outcome — Option C (split into N entries with same value).** Each multi-source attestation now renders as one entry per source:

```yaml
weight_rough_g:
  - {value: 28.893, source: "Hede 39A"}
  - {value: 28.893, source: "Numista"}
  - {value: 28.89,  source: ucoin}
```

The display pipeline (`compute.make_display_groups`) already groups list-form entries by rounded value, so two same-value entries collapse into ONE rendered span with both sources accumulated into the tooltip — visually identical to the joined form, structurally clean.

**Implementation:**

  - **Migration.** `scripts/maintenance/split_multisource_weight_entries.py` walks every coin's `weight_rough_g`, `fineness`, `diameter_mm` lists and splits any `\n`-joined source into separate entries. Idempotent — re-running on already-split data is a no-op. Applied: 40 new entries across 31 coins (4 in denmark, 36 in schleswig_holstein).
  - **Compute fix (latent bug).** `compute.alts` previously hardcoded the alt-source tooltip prefix as «Обчислено з вагою × пробою з:» regardless of which input the alt actually overrode. After the migration this caused split alts that supply only a different weight reading (with fineness inherited from the scalar primary) to render under the «× пробою» prefix and visually duplicate the primary's «з вагою з:» prefix in the same tooltip. Fixed to mirror the primary-derived-source prefix logic — pick the prefix that reflects the actual override (weight only / fineness only / both).
  - **Audit script.** `scripts/oneoff/audit_orphan_weight_sources.py` dropped its `[,;\n]`-split kludge in favour of a clean `[,;]`-only split (the comma/semicolon inline-join still appears in older entries; the `\n` form is gone for good).
  - **CLAUDE.md.** Extended §9a with a «Source-data is structured, not stringly-joined» sub-rule so future edits don't reintroduce the pattern.

**Verification.** Build still passes; rendered output visually identical except for the corrected alt-prefix labels (the latent bug fix). Re-running the migration finds zero remaining `\n`-joined source labels across the corpus.

---

### J. Bruun parser + cross-match: two latent bugs from km-165/KM-166 audit  *(closed 2026-05-10)*

**Surfaced during.** Audit of `km-165-fr-iv-1698` (Schleswig-Holstein-Gottorp
1 Mark 1698 Tönning, Lange-430A) revealed Bruun lot `III/12210` had been
mis-attached as an orphan weight (22.0 g) to km-165 even though the lot is
KM-**166** / Lange-**430AA** (the sister 2 Mark, separate Krause type per §9.3).

**Outcome.**

  - **Parser regex (02_parse_lots.py)** — `[A-Za-z]?` → `[A-Za-z]*` for all
    REF_PATTERNS so multi-letter Krause / Lange / Hede sub-variant suffixes
    capture in full. Re-running the parser surfaced 5 truncated suffixes:
    Lange-430AA (was 430A — the original trigger), Lange-510AAb, Lange-99Aa,
    Lange-99Ab, Dav-3746var. All five are now whole tokens in the cache.

  - **Parity gate (04_cross_match.py)** — added `lot_compatible_with_coin()`
    that gates EVERY candidate path (single-match included, plus the Bruun-id
    fast-lookup) on parent-KM match, falling back to parent-Hede when KM is
    absent on either side. The function also accepts KMs listed in
    `catalog.others` to support intentional Numista-duplicate consolidations
    (e.g. km-105 carrying KM# 73 as a synonym).

  - **Audit pass.** Re-running cross_match flipped 9 lots from cat A to cat
    D (parity-rejected). Verification confirmed all 9 previously-matched
    coin-IDs either no longer exist in YAML (stale cache from prior coin
    renames) or never had the lot attached in the data layer — no §9.3
    cleanup needed in `*.yml`. The 9 D-cases are off-metal-strike Pn-tier
    issues + genuinely-missing Krause types that may warrant new YAML
    entries (deferred — independent of this fix).

**Bruun cross-match state (after fix):** TOTAL=783, A=755 (96%), B=10, D=18.

Implemented in commit (this session). Closes both defects in TODO J.

---

### G. §9.3 cleanup of wrong Bruun-specimen attachments  *(closed 2026-05-06)*

**Background.** When Phase 3 ran the original `phase3_enrich.py` without
single-match filtering, multi-matched Bruun lots were broadcast to ALL
candidate ids — attaching the same specimen to multiple coins, including ones
whose KM (and Hede where comparable) demonstrably mismatched the lot's
catalog refs. Per §9.3, different KM = different type, so these were silent
data corruptions sitting in `denmark.yml` and `schleswig_holstein.yml`.

**Outcome.** Audit (`scripts/oneoff/audit_wrong_bruun_attachments.py`)
identified 58 mis-attachments across 42 coins. Strip
(`strip_wrong_bruun_attachments.py`) cleared those attachments from
`catalog.bruun_*`, `weight_rough_g[]`, and `sources[]`, then phase3b/3c
re-enriched with §9.3 compatibility filtering baked in
(`lot_compatible_with_coin()` is now called before any new spec is added
to a host coin). Final audit reports 0 mis-attachments.

**Closure commit:** `ffbf458` (DK+SH strip), `03b1c10` (parser fix
prerequisite), `a5dd778` (Phase 3b/3c clean re-enrichment).

---

### A. Verify continuous year-ranges for gaps  *(closed 2026-05-03)*

**Outcome.** All 15 coins audited against Numista `_issues.json` cache:

- **10 confirmed continuous** — Numista per-year breakdown explicitly
  enumerates every year in the declared range (no gaps):
  km-137117 (1589–1601), km-5-ja (1594–1605), km-103 (1671–1682),
  km-8-ernst (1600–1609), km-25 (1640–1648), km-155 (1695–1702),
  km-185 (1703–1710), km-183 (1703–1709), km-735 (1842–1848),
  km-193 (1706–1712).
- **4 «is_dated: false»** — Numista records the type as a single
  range without per-year split (per-year breakdown unavailable from
  Numista; left as continuous, undocumented gaps possible):
  km-3-ja (1590–1616), km-137419-ernst (1601–1622),
  km-278283-ernst (1601–1622), km-137112-otto (1567–1576).
- **1 special** (km-120-chr-v-1787) — its Numista link N#34037 was
  incorrect (pointed to Mauritius ½ Rupee 1946); removed. No correct
  Numista entry found for Christian VII 2 Sechsling Tower Hill 1787–1800.
  ucoin tid 90571 records as range 1787–1800 without per-year split —
  left as continuous.

All 15 entries gained a `verification_note` documenting the audit so
future re-runs of similar checks won't re-flag them. Per-coin notes
quote the audit date (2026-05-03) and the source consulted, satisfying
the original done-criterion: «range confirmed against an explicit
source».

---

### B. Investigate Frederick III silver «1 Krone» 1659–1660 (N#313341)  *(closed 2026-05-03)*

**Outcome.** N#313341 turned out to be a **duplicate Numista listing
of our existing `km-x001-fr-iii-1659`** (Type II, Hede 153A). Numista
carries two parallel entries for the same Davenport-3675 type:
N#111285 under the «City of Glückstadt» issuer (KM# B43) and N#313341
under the «Schleswig-Holstein duchies» issuer (KM# 95). The km-x001
entry already cites both Numista IDs in `sources` and explicitly
documents the duplication in its body note («same coin, duplicate
Numista listing»).

**Cross-check of the 3 research links** (all Frederick III, ru=437):
- `schleswig_holstein_danish_duchies` (3 hits): all 3 already in base
  — km-90 (1 Sechsling), km-x001 (1 Krone, this item), km-103 (4 Marck
  Danske, listed under Christian V on Numista despite the FRIII filter)
- `gluckstadt_city` (9 hits): all 9 already in base — Guldkrone,
  1/16 Speciedaler, both 4-Mark-Dansk types, Speciedaler 1664-66,
  ⅛ Reichs Daler, both 1/16-Thaler bust types, 1 Ducat 1666-69
- `bremen_archbishopric` (3 hits): not in base, not in Holstein scope
  — moved to Item C as seed for a future `bremen.yml`

**Net result.** No new Holstein coin to add from item B. The «silver
Krone» discovery turned into a Numista-duplicate normalisation that
was already done.

(none yet)
