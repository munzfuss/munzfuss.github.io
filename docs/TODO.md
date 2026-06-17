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

### BF. ✅ Denmark 1514-1566 gap — Müntzfüße + coin promotion for the new lower-bound window  *(opened 2026-05-15, rescoped 2026-05-16 per §BI, **closed 2026-05-21**)* *(est: large)* *(type: research-applied + data)*

**Closed 2026-05-21** via commits `0102073` (Fuß defs in fuesse.yml) + `9343cd6` (V2 denmark fuss_periods + 6 c3h promotions + 4 refs). User verdict 2026-05-21: (a) separate Flensborg Fuß + Danish `_fod` naming.

**Definition of done — met:**
- ✅ `8_daler_fod` + `8_daler_lybsk_fod` defined in `data/shared/fuesse.yml` with full metric blocks (grundwerte, fractions, events), DE/EN/UK descriptions, sourced metrics (Wilcke 1950 / Paus 1752 / Rigsarkivet T.K. nr. 160 / Galster 1965).
- ✅ V2 `data/v2/locations/denmark.yml`: fuss_order updated (both new Fußen prepended chronologically), timeline.bars added for both, fuss_periods entries with full pdate_label / hintergrund / closing for both.
- ✅ 6 c3h Kopenhagen seed coins promoted in `data/v2/final/danish_realm.yml`: Phase A1 Kurant (c3h3 Mark, c3h4 8 Sk, c3h5 4 Sk); Phase A1 Scheide (c3h6a 1 Sk 1542, c3h7 Hvid); Phase A2 Scheide (c3h8 Penning 1546).
- ✅ 4 new bibliography refs (ref29 Wilcke 1950, ref30 Paus 1752, ref31 Rigsarkivet T.K. nr. 160, ref32 Galster 1965) with verbatim quotes + page hints per §5a.

**Remaining work — sibling tasks, NOT blocking §BF closure:**
- **Flensborg c3h21/c3h22 specimen promotion** — Lybsk Sølvgylden + Søsling lybsk specimens not yet in our cache; pending §AZ Galster + Jensen-Skjoldager paper-source import. The `8_daler_lybsk_fod` Fuß card renders structurally with the metric block but the coin table stays empty until those specimens arrive.
- **c3h1 + c3h2** (1557 Ungersk Gylden gold .986) — these are POST-1559 gold issues, belong under `reichsdukatenfuss`, not the Christian-III silver track. Separate placement task.
- **Pre-1541 sub-window** (Christian II 1513-1523 + Frederik I 1523-1533) — depends on §AZ Galster + Jensen-Skjoldager catalog import. §BF was scoped to 1541-1566 Christian III; pre-1541 stays its own §AZ-blocked workstream.
- **Classifier rule extension** for `8_daler_fod` era-anchor (year+denomination → Fuß) — deferred to when c3h21/22 land; current 6 coins manually promoted, future imports will need rule-based classification.

**Original §BF planning text below preserved for reference:**



**Surfaced.** User direction 2026-05-15 with explicit «найвищий» marker. The dual-anchor scope decision (§BC closed 2026-05-15) initially extended the Denmark page's lower bound from 1559 to 1541; §BI (2026-05-16) re-anchored further back to **1514** (Christian II Lovkompleks per Wilcke 1950 p. 183-186 verbatim). The seed builder's `--year-from` default is now 1514 and ~26 c3h Hede entries (Christian III + early Frederik II) sit in `data/seed/hede/denmark.yml` — but none of them are placed yet. The page renders the new (1514–1914) range in its header/timeline, but the 1514-1566 phase block of the Denmark page is structurally **empty of curated Müntzfüße + coins**. Closing this gap is the Highest-priority blocker for the Denmark-track research front.

**Note on pre-1541 sub-window**: the 1514-1540 portion (Christian II 1513-1523 + Frederik I 1523-1533) needs a NEW-SOURCE catalog import — **Galster 1959-1960 + Jensen-Skjoldager 2021** (sibling TODO §AZ — see below). Hede 1957 itself does NOT catalogue pre-Christian-III rulers, so this is not a Hede extension; it's a new reference-source family. Until §AZ lands, §BF's data-coverage stays at Christian III 1541+ from the existing Hede cache.

**Underlying research is already done.** Two long-form dossiers cover this period in detail:

- `docs/research/moentordning_1541.md` — full primary-source capture of the spring 20 March 1541 «Om Maal og Vægt» Forordning + autumn 20 September 1541 Møntordning + 1544 supplement + 1547 Flensborg Bestalling. Includes Marken-fin / Cølnsk-Vægt arithmetic, denomination tables, dual-zone (Lybsk vs Danish) currency seed of 1547, mintmaster's oaths.
- `docs/research/christian_iii_danish_coinage_1534_1572.md` — context for Christian-III-Daler-fod silver, gold one-offs, and the transition toward Frederik II's 9-Fuß alignment.

Primary-source captures: `docs/research/sources/wilcke_1950_christian_iii_moentreform.md`, `paus_christian_iii_1541_maal_og_vaegt.md`, `rigsarkivet_tk_160_diverse_moentsager.md`.

**Scope.** Four operational sub-tasks (from the §BC closure note, now promoted under §BF):

1. **Define new Müntzfuß `8_daler_fod`** in `data/shared/fuesse.yml`. Canonical metric: mf 8.827, 26.494 g fein per Daler, fineness 0.906 (14½ Lod), sourced to Wilcke 1950 + Rigsarkivet T.K. nr. 160 + Paus 1752. Per §BD this should probably be the Danish-form name from the start (`dalerfod` not `christian_iii_thaler_fuss`).
2. **Add `fuss_periods.8_daler_fod`** block to `data/v2/locations/denmark.yml` with phases (V2-only — V1 frozen at `/v1/` since 2026-05-18 flip):
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

- **(a) Separate Müntzfuß `8_daler_lybsk_fod`** for the Lybsk-aligned sub-Mark + 14¼ Lod Daler. Clean genealogy: A1/A2 are København, A3/A4 are Flensborg. Two parallel Müntzfüße for the same monarch.
- **(b) Same `8_daler_fod` Fuß with mint-tag differentiation** — A3/A4 phases marked as Flensborg-specific within the single Fuß. Simpler structurally but conflates two genuinely distinct standards.

Likely answer is (a) — the dual-zone is the seed of an enduring lineage and deserves its own Fuß slot. User verdict requested before the data edit.

**Cross-references.**

- **§BD** (Danish Müntzfuß names) — the new `dalerfod` / `flensborg_fod` IDs should land in the Danish convention from day one. Sequencing §BD verdict before §BF data edit avoids immediate rename churn.
- **§BB** (Fuß descriptions — historical framing only) — `8_daler_fod` `hintergrund` prose follows the §BB rule (historical framing, no parameter bleed).
- **§AY** (Frederik II 3-Mark one-off) — sits at the boundary of this window (1560/1563); coordinate with §BF if the 1560s F2 seed entries land in the same pass.
- **§AV / §AW** (Guldkrone-fod, Rhinsk Gylden) — earlier Christian I / Hans gold entries; design decisions interact with the broader 1541-window architecture.
- **§BE** (Danish translation for DK/SH) — every new field added under §BF will eventually need a `da:` translation. Either add `da:` upfront (if §BE is also accepted) or accept the rework.

**Action sequence.**

1. User decides on (a) vs (b) for Flensborg.
2. User decides §BD architecture (jurisdiction-aware naming) at least at policy level — affects whether new IDs are `8_daler_fod` (Danish form) or `christian_iii_thaler_fuss` (German form).
3. Define Müntzfuß / Müntzfüße in `fuesse.yml` with sourced metrics + hintergrund prose.
4. Add `fuss_periods` block(s) to `denmark.yml` with phase boundaries + descriptions.
5. Promote seed coins into curated entries with `fuss:` + `phase:` set; preserve all per-specimen multi-source data (§9a).
6. Add the 4 new bibliography entries to `denmark-references.yml` with verbatim quotes + page hints per §5a.
7. Build clean + sample-review three coins per phase against the rendered page.

**Definition of done.** The Denmark page renders a non-empty 1514-1566 section with at least 6 placed coins, a `8_daler_fod` Fuß card with full metric block + sourced hintergrund, and the dual-track Flensborg phase (if (a)) wired up. The 26+ new c3h seed entries auto-suppress against the curated phase blocks per the `_merge_seeds_into_raw` rule. Pre-1541 sub-window coverage (Christian II 1513-1523 + Frederik I 1523-1533) depends on §AZ Galster + Jensen-Skjoldager catalog import landing first.

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

### BQ. 🟢 DK ↔ SH coverage parity audit — every Schleswig-Holstein coin on the Denmark page must also surface on the SH page  *(opened 2026-05-18)* *(est: medium)* *(type: data-audit + curation-move)*

**Surfaced.** User direction 2026-05-18 with explicit «найвищий» marker: «впевнитись що всі Ш-Г монети на сторінці Данії також listed на сторінці Ш-Г, якщо ні то перенеси».

**Context.** Many coins struck for the Danish-Helstaten era (1813–1864) carry SH relevance — minted at Altona, denominated in Schleswig-Holstein Courant, or otherwise tied to the duchy's jurisdiction — yet currently surface only on the Denmark display page. With V2's entity-keyed pipeline (D2/D3) a coin's `issuing_entity` is the home file, and `consumes_entities` on the display location drives the render-time assembly. Two failure modes the audit looks for:

1. **Wrong `issuing_entity`** — a coin tagged `danish_realm` or `gesamtstaat` whose mint + denomination clearly point at the royal_holstein / gesamtstaat duchy jurisdiction. Fix: re-tag and (if needed) move home file.
2. **Right entity but display page misses it** — `schleswig_holstein.yml::consumes_entities` doesn't list the entity that owns the coin. Fix: add the entity to `consumes_entities` on the SH display page.

**Audit steps.**
1. Enumerate every coin currently rendered on the Denmark page (`site/v2/denmark/de/index.html` — or read from `data/v2/final/danish_realm.yml` + any other entities Denmark consumes).
2. For each, check: does the same coin (by canonical id / catalog ref) also surface on the SH page?
3. If NO, decide per coin:
   - **Move home**: coin truly belongs to a SH-specific entity (royal_holstein / gottorp_duchy / etc.). Update `issuing_entity` accordingly; re-run absorb pipeline.
   - **Add to consumes**: coin's home stays where it is, but SH page should consume that entity. Extend `data/v2/locations/schleswig_holstein.yml::consumes_entities`.
   - **Skip**: coin is genuinely Denmark-only (no SH jurisdictional tie). Document the negative finding.

**Special attention to:**
- Christian VIII / Frederik VII Rigsbankdaler / Rigsbankskilling 1842-1855 — dual-denominated «X Rigsbankskilling = Y Schilling Courant» types currently mostly tagged `gesamtstaat`. Where do they render now? Both pages? Just one?
- Altona-mint coins under royal-Danish rulers (Frederik VI / Christian VIII / Frederik VII). Altona was an SH-mint town; these likely belong to royal_holstein not danish_realm.
- The km-735 / km-726-2 / km-733 / km-734 / km-737 / km-743 / km-761 cluster — multi-mint (Altona + Kopenhagen) gesamtstaat / royal_holstein entries that just received the mintmaster cleanup (D32). Verify both pages list them.

**Definition of done.**
- Diff report: per-coin {coin_id, current home, surfaces-on-DK, surfaces-on-SH, decision}.
- All «only-DK, should-also-SH» cases either moved or surfaced via consumes_entities.
- The opposite direction (SH coins missing on DK) is OUT OF SCOPE for this task — only the DK→SH leak is the user's concern.

### BU. 🟡 Source-ref labels: use distinguishing sub-index when ≥2 same-resource links carry different sub-variants  *(opened 2026-05-19)* *(est: small)* *(type: convention refinement)*

**Note on section number** — opened as §BR locally on 2026-05-19, renumbered §BU at merge-time (2026-05-19) because §BR was already taken on main for the ucoin DK-realm coverage audit (opened 2026-05-18, see «In progress» below).

**Surfaced.** User direction 2026-05-19. The default convention (just codified in `docs/CONVENTIONS.md` §«Source-ref label shape») is:
- Single source of a resource: label = bare resource name («Numista»)
- Multiple same-resource sources: label = resource + resource's page-id («Numista 199146», «ucoin tid 162999», «Bruun Part II, lot 14465»)

That rule covers «which of ≥2 same-resource sources is this link». But it ignores a STRONGER semantic distinction available in many ≥2-same-resource cases: **the resources themselves point at different SUB-VARIANTS of the coin** (different Hede sub-letters, different Krause-volume sub-numbers, different mintmaster die variants). When the sub-index IS the actual distinguishing axis, the label should expose it instead of the bare page-id.

**Examples of the pattern this TODO addresses:**

- Cross-Krause-volume single coin (currently labelled `Numista 199146` / `Numista 301740` after the §«link-label shape» cleanup — concrete pair caught 2026-05-19): two Numista entries for the SAME physical coin, one under «KM-25 DK volume» and one under «KM-87 SH volume». Better label: `Numista (KM-DK 25)` / `Numista (KM-SH 87)` — the cross-volume KM is the distinguisher.
- Hede sub-letters folded under one Numista entry: `Numista 568145` covers BOTH Hede 26A and 26B (Frederik III 1667 1 Ducat); when paired with two Bruun lots — one citing Hede 26A and one citing 26B — Bruun's labels should expose the Hede sub-letter (`Bruun (Hede 26A)` / `Bruun (Hede 26B)`).
- Bruun part vs lot when both labels collide.

**Why this matters.** The «Джерела» column on the rendered page is the reader's primary tool for jumping between cited sources. When labels show only `Numista 199146` vs `Numista 301740`, the reader has to OPEN both to learn which is the DK-volume vs SH-volume citation. Showing the sub-index inline turns the «click to learn» step into «read once» — same information surface, lower friction.

**Algorithm sketch** (to be implemented in `_compute_coin` or render layer):

1. Per coin, group `sources[]` by resource (numista / ucoin / bruun / hede / etc.).
2. For each group with ≥2 entries:
   a. Walk each source's `ref` (or compute from URL) and identify the resource's «page id» (Numista N#, ucoin tid, Bruun lot-no, Hede basename).
   b. Walk the COIN's `catalog` field (or related ref fields) and look for sub-indices that vary across the same-resource sources — Krause register (`km` dict-form), Hede sub-letters (`hede` list-form), Dav sub-variant (LS455/LS456), mintmaster initials.
   c. If exactly ONE sub-index axis differs across the group AND each source maps cleanly to one sub-index value → use the sub-index as the label suffix (`Numista (KM-DK 25)`); otherwise fall back to page-id (`Numista 199146`).
3. Single-source groups stay at the bare resource name as today.

**Definition of done.**
- `_compute_coin` (or the renderer that emits the «Джерела» column) detects ≥2-same-resource groups + walks the coin's catalog for distinguishing sub-indices.
- The 4 concrete cases identified during the 2026-05-19 cleanup (`Numista 199146`/`301740` cross-volume KM, `Numista 568145` Hede 26A/26B fold, the two `ucoin tid 97085`/`97086` pairs if applicable, the `Numista 420365` 26A+26B fold) render with sub-index labels instead of bare page-ids.
- Idempotent: re-running the renderer on the same data produces identical labels.
- Single-source groups behaviour unchanged.
- CONVENTIONS.md §«Source-ref label shape» updated to describe the auto-derived sub-index labels (the manually-curated «(KM-25 DK volume)»-style suffixes are no longer needed — render layer computes them).

### BS. 🟡 Coin-table row-height — note's tall content blows up row-height; hover should overlay  *(opened 2026-05-19)* *(est: small-medium)* *(type: layout / CSS)*

**Surfaced.** User direction 2026-05-19: «для рядків в таблиці монет на веб-сторінці, зараз виходить так що висота рядка визначається висотою найвищого значення в будь-який комірці таблиці. треба зробити щоб висота рядка таблиці рахувалась незважаючи на висоту поля note, а коли hover на такий рядок (у якого note менший за висоту рядка) то поле note стає видимим на всю свою висоту перекриваючи рядки знизу.»

**Current behaviour.** Each coin-table row's height = `max(height_of_each_cell)`. Long `note` content (multi-sentence DE/EN/UK paragraphs with Bruun quotes, transition rationale, Krause sub-variant breakdown, etc.) forces the entire row to grow — every other cell pads with whitespace. On the rendered Müntzfuß tables (Reichsdukatenfuß, 9-Thaler-Fuß, etc.) this produces 200-400-pixel rows interspersed with normal 40-60-pixel rows, breaking visual rhythm.

**Desired behaviour.**
- Row height = computed from the OTHER cells (year / nominal / metal / fineness / weight / catalog / mint), ignoring note's full content. The note cell renders to the row's «normal» height with overflow clipped (CSS `max-height` + `overflow: hidden` + a fade-out gradient or «…» indicator).
- On row hover (or possibly on click for mobile), the note cell EXPANDS to its full content height. The expanded note overlays the rows below it (via CSS `position: absolute` from the cell with a high `z-index`, or `position: sticky` within the row). The rest of the table layout doesn't shift — only the note temporarily covers the rows immediately beneath.
- Mobile / no-hover devices: tap to toggle expanded state on a per-row basis.

**Implementation notes (sketch).**
- The note column already lives in a `<td class="note-cell">` or similar; add CSS `max-height: var(--row-normal-h)` + `overflow: hidden` for default state.
- On hover: `max-height: none; position: absolute; left: <col-x>; top: <row-y>; z-index: 10; background: var(--bg)` to overlay.
- The «normal» row height should come from the OTHER cells' natural height; setting `max-height` on the note cell achieves this without explicit row-height pinning.
- Smooth `transition: max-height 0.2s ease-out` for the hover expansion.
- Test on a known-heavy page (Lübeck phases with long bar_title prose, Denmark phases with Hebræermønt 1644 historical context, Schleswig-Holstein km-735 / km-743 etc.).

**Definition of done.**
- Coin tables on every rendered location page have visually-uniform row heights regardless of note content length.
- Hover (or tap on mobile) reveals the full note content as an overlay.
- The `note-cell`'s collapsed state shows a clear «more content» affordance (gradient fade, ellipsis, or small icon).
- No layout-shift on hover — overlapping rows stay in place underneath the expanded note.
- Tested across DE/EN/UK (note lengths vary by language).

### BT. 🟡 D38-style consistency cleanup for remaining seed builders (Hede / Bruun / Galster / Numista pre1541)  *(opened 2026-05-19)* *(est: small)* *(type: builder consistency)*

**Surfaced.** D38 (2026-05-19) refactored `build_numismaster_seed.py` + `build_numismaster_pre1541_seed.py` to emit canonical V2 `issuing_entity` tags directly from cache `country` fields — the linear-pipeline principle says cache-derived entity hints belong at the per-source builder layer (Phase 3.1a), not the regroup classifier (Phase 3.1b). Four sibling builders still use the legacy patterns:

| Builder | Current state | Functional? | What's wrong per D38 principle |
|---|---|---|---|
| `build_hede_denmark_seed.py` | Line 647: hardcoded `cm["issuing_entity"] = "danish_realm"` for ALL ~885 entries | ✓ regroup rescues via D35 mint-override (Christiania→danish_norway, Glückstadt→royal_holstein) | Builder ignores mint info it already has; rebuild produces wrong entity tag that regroup must fix |
| `build_bruun_denmark_seed.py` | Line 280: `"norwegian_realm" if is_norway else "danish_realm"` (binary, ignores region detail) | ✓ regroup remaps `norwegian_realm` → `danish_norway` via `_SEED_ENTITY_REMAP` | Uses defunct alias; SH-region Bruun lots also default to danish_realm |
| `build_galster_denmark_seed.py` | Line 80: `detect_issuing_entity` returns `"norwegian_realm"` for sub_realm=norway | ✓ regroup remaps | Same legacy alias |
| `build_numista_pre1541_seed.py` | Line 70: `"norwegian_realm"` if "norway" in issuer text | ✓ regroup remaps | Same legacy alias |

**Functional impact:** zero — pipeline outputs correct V2 entity files via the regroup-layer compensations (D35 mint-override + `_SEED_ENTITY_REMAP`).

**Architectural impact:** builders not doing their full job. Following D38 principle, each per-source builder should emit the canonical V2 `issuing_entity` tag directly — regroup remains a thin fan-out shim without source-specific knowledge.

**Plan (mechanical, ~30 minutes total):**

1. **Hede builder**: import `classify_mint_to_entity` from `lib.v2_entity_classify`; replace the hardcoded `danish_realm` with `classify_mint_to_entity(coin.get("mint")) or "danish_realm"`. Edge cases: Norge entries (mint=Christiania/Kongsberg/Oslo/Bergen) → `danish_norway`; Glückstadt/Altona → `royal_holstein`; `n*h` volume basenames with no mint default to `danish_norway` (volume code is parser-canonical for Norge).

2. **Bruun builder**: use lot's `region` field directly: `NORWAY` → `danish_norway`; `DENMARK` → call `classify_mint_to_entity(mint)` for Glückstadt/Altona/etc. routing; `SCHLESWIG-HOLSTEIN` → `royal_holstein` (Bruun's regional grouping for SH lots).

3. **Galster builder**: replace `"norwegian_realm"` with `"danish_norway"`; call `classify_mint_to_entity(mint)` for non-Norway entries.

4. **Numista pre1541 builder**: replace `"norwegian_realm"` with `"danish_norway"`; consider extending to use Numista's `issuer.code` / `issuer.name` for richer routing (e.g. county-level rulers).

5. **Rebuild each affected seed with `--no-merge`** to overwrite legacy aliases. Safe for all 4 because V1 seeds are auto-generated (no curator-direct edits documented). Verify via:
   - `grep "issuing_entity:" data/seed/<src>/*.yml | sort | uniq -c` — no `norwegian_realm`, no `schleswig_holstein_duchy`
   - Re-run regroup; `_unclassified` stays 0
   - Re-run merger + absorb; pipeline idempotent

**Definition of done.**
- All 4 builders import `classify_mint_to_entity` (or use cache-derived source-specific signal); no hardcoded entity defaults or legacy aliases remain in builder code.
- V1 seeds carry canonical V2 `issuing_entity` values directly.
- `_SEED_ENTITY_REMAP` can drop the `norwegian_realm` → `danish_norway` entry (or keep it as defensive belt-and-braces — curator's call).
- D38 entry in V2_DECISIONS.md extended with «and applied to Hede / Bruun / Galster / Numista builders 2026-XX-XX».

#### BO.5 — Numista DK 1602-1914 main-window coverage audit + harvest  🔵 **IN PROGRESS — batches 1-5/6 done (200 NIDs, 94.3 %)** *(opened 2026-05-18, est: medium-large)*

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
  | **3** | ✅ DONE 2026-05-18 | 40 (111312…181629) | Christian IV 1591-1648 silver+gold repertoire (4-Daler Klippe KM# 25, 1-Speciedaler bust-I/II KM# 102/135, 3-Speciedaler KM# 75, Rhinsk Gylden KM# 108, 8-Skilling KM# 31, 1-Mark Helsingør KM# 36) + Frederik III commemorative Victory-over-Swedes Krone (KM# 222/225) + 4-Mark KM# 186/187 + 1-Speciedaler KM# 212 + 2-Ducats Ship I/II (KM# 216.1/216.2) + ½-Krone KM# 267 + Christian V East-India 1-Speciedaler KM# 317/319 + 4-Mark KM# 359.1/401.1-4 + Frederik V Coronation/Accession KM# 546/562/563 + Christian VII Christian-d'Or KM# 629 + Albertsdaler KM# 640 + Gianelli 1-Speciedaler KM# 654 + Frederik VI 2-Frederik-d'Or KM# 713 | `4068959` (submodule) |
  | **4** | ✅ DONE 2026-05-18 | 40 (182700…366728) | Christian IV high-denom 10-Ducats Fr# 68 + Rosenobel KM# 51 + 1-Piastre East-India KM# 117 + Speciedaler-Copenhagen-rect-arms KM# 44 (Dav 3514A) + Frederiksborg 12-Skilling KM# 85 + Hvid KM# 63.2 + Frederik III 1-Speciedaler 13-province KM# 169 + 2-Gold-Krone KM# 279 + Cross-monogram 2-Ducats KM# 243/295/326/PnB16/PnD16 + Largesse 1-/2-Ducat Klippe KM# 163/164 + ½-Portugaloser KM# PnG16 + Christian V Plain-monogram 2-Mark KM# 329.2 + Thin-monogram-Type2 4-Mark KM# 386.2 + 1-Ducat KM# 374.2/412.2 + 2-Ducats KM# 439 + Frederik IV Accession 3-Krone KM# 449 + Coronation 2-Ducats KM# 461 + ½-Ducat KM# 452 + 2-Ducats KM# 475/A488 + SH ½-Dukat Rendsburg KM# 7 + Frederik V Accession 1-/2-Ducats KM# 547/553 + 1-Krone KM# A571 + Christian VII 1-Piastre Asiatic KM# 638 + Christian IX 2-Christians-d'Or KM# 773 | `fcffa68` (submodule) |
  | **5** | ✅ DONE 2026-05-19 | 40 (372940…468777) | Christian IV gold high-denom (2-Goldgulden KM# 46 Fr# 36 .972, ¼-/½-Rosenobel KM# 50.1/50.2/Fr# 49, 1-/¼-/½-Ducat KM# 149/150/152/153, ¼-Portugaloser KM# 114, 3-Daler Klippe KM# 24, 8-Daler Klippe KM# 27 Fr# 44 .937, 2-Gold-Kronen KM# 111, 4-Speciedaler bust-I KM# 79 Dav 3521) + Frederik III gold cluster (½-Portugaloser KM# Pn10/Pn13 Fr# 106, 1-/2-/3-/4-/5-/6-/10-Ducat range KM# 217.1/217.2/252/253/265.2/314/Pn10/PnF16, Largesse 3-/4-Ducat Klippe KM# 165/166, 1-Gold-Crown KM# 206.1/206.2 Fr# 120) + Christian V gold (KM# 328/396/458, 4-Mark Pattern KM# Pn30) + Frederik IV Coronation 3-/4-Ducats KM# 461-464 + 2-Ducats KM# 498 1710-1711 + 3-Ducats KM# 472 | `b8e3cab` (submodule) |
  | **6** | ⏳ pending | 12 (468831…577419) | TBD when run | — |

Per-batch NID lists live in `scripts/cache/numista/_BO5_audit_2026-05-18.json` under `harvest_progress.batches.batch_N.nids` — drop-in resume-friendly format.

**Cloudflare risk profile (empirical, 2026-05-17/18 across two harvest sessions):**

- Per-NID `/catalogue/pieces<N>.html` URL: **low risk**, survived 70+ sequential fetches across two days (BO.1 SH-cluster 30 fetches + BO.5 batch 1 40 fetches) with 0 trips at 31-60s pacing.
- Listing pages (`/<code>-1.html`, `?e=...`): **medium risk**, 2-3 trips during enumeration phase, each requiring 3-4 min cooldown.
- `?ru=` ruler filter URL: **high risk** — fires on first call.

The per-NID route is the safe one for incremental harvest. Listing-page enumeration only fires when scoping (BO.5's discovery phase is done).

**Pause rationale (2026-05-18, refreshed after batch 3):** user direction «зробимо тимчасову паузу щоб не було лімітів» after batch 1; reaffirmed after batch 2 with «запиши стан і що лишилось для наступних сесій, бо зараз зробимо паузу на юкоін і переключимось знову на нуміста на 1 батч» (1 Numista batch then pause again); resumed after BR batch 3 with «тепер ще один нуміста батч» (sequenced single-batch alternation between platforms). The cumulative Numista access budget is finite and the user wants to spread the load across more days rather than burn it in one session. Per-NID fetches do not have a hard quota but they do contribute to Cloudflare's daily anti-abuse heuristic for our IP. Across batches 1+2+3 (120 total fetches over three sessions ~50-52 min each) **0 Cloudflare trips fired** at 31-60 s pacing — three-session empirical confirmation that the per-NID HTML route plus pacing is sustainable.

**Resume procedure:**

1. Read `scripts/cache/numista/_BO5_audit_2026-05-18.json` → `harvest_progress.batches.batch_<N>.nids` for the next pending batch.
2. Use the JS extractor pattern from `docs/HARVEST_GUIDE.md §«Per-NID HTML fetcher»` (unchanged template).
3. Save via `/tmp/save_numista.py` (Python helper writes to `scripts/cache/numista/<nid>.json` with `_harvested_via: "chrome_mcp_html"` marker).
4. Per batch end: stage all 40 new cache files in submodule, commit with «numista: §BO.5 batch N/6 — ...», push submodule, update this entry's batch-progress table.
5. After final batch (6/6): write the seed-builder pipeline for chrome_mcp_html-harvested entries OR fold into existing Numista parser depending on how the data shape compares with API entries.

**Definition of done.** All 212 NIDs cached in `scripts/cache/numista/` with `_harvested_via: "chrome_mcp_html"` marker. Phase-1 coverage table updated to reflect 100% DK 1602-1914 coverage. Final BO.5 closure note replaces this in-progress entry.

#### BR — ucoin DK-realm 1514-1914 coverage audit  🔵 **AUDIT DONE + batches 1-7 of N harvested (259 TIDs); p2399 + p2939 + SH-country CLOSED + DK Krone era 1873-1914 CLOSED** *(opened 2026-05-18, est: medium-large)*

**Update 2026-05-18 (p2399 closed):**

Per user direction «пуш в обидві і тоді ще один батч юкоін» following BO.5 batch 3/6, completed final batch of p2399 (Norway Speciedaler 1648-1699). Period now closed cleanly: all 153/153 TIDs harvested across 4 sessions.

**Batches 1-5/N done (submodule commits `4a323ea` + `bb4c6a4` + `44c744f` + `7136528` + `4f6d77a`):**

| Batch | Status | Count | Period coverage | Submodule commit |
|---|---|---:|---|---|
| **1** | ✅ DONE 2026-05-18 session 1 | 40 | p2399 page 1 (first 40 of 48) | `4a323ea` |
| **2** | ✅ DONE 2026-05-18 session 2 | 40 | p2399 page-1 leftovers (8) + page-2 first 32 | `bb4c6a4` |
| **3** | ✅ DONE 2026-05-18 session 3 | 40 | p2399 page-2 tail (16) + page-3 head (24) | `44c744f` |
| **4** | ✅ DONE 2026-05-18 session 4 | 33 | p2399 page-3 tail (24) + page-4 (9) — **PERIOD CLOSED** | `7136528` |
| **5** | ✅ DONE 2026-05-18 session 5 | 40 | p2939 SH-Glückstadt (1617-1694) Christian IV + Frederick III + Christian V; first 40 of 50 sorted by year asc | `4f6d77a` |
| **6** | ✅ DONE 2026-05-19 session 6 | 26 | p2939 tail (10 TIDs Christian V 1693-1696 + Frederik IV 1702-1716 — **p2939 CLOSED 50/50**) + country=schleswig_holstein (16 TIDs Christian VII 1787-1808 + Frederik VI 1809-1839 + Provisional Govt 1850-1851 — **SH-country CLOSED 16/16**); user-requested SH probe COMPLETE | `ab67784` |
| **7** | ✅ DONE 2026-05-19 session 7 | 40 | DK Krone era 1873-1914 **CLOSED** (23 TIDs: p374 Christian IX 9/9 circulation KM# 790-798, p373 Frederik VIII 7/7 KM# 804-810, p220 Christian X 1912-1914 in-window 7/7 KM# 812-818) + NO p2400 head (17 TIDs Frederik IV 1699-1730 era KM# 200.1-224) | `37a228c` |
| 8+ | ⏳ pending | ~200 across other periods | NO p2400 tail (6) + p1041 + p883 (1746-1814) + p374 commemoratives (3) + Holstein-Gottorp-Rendsburg 1716-1720 | — |

- **153/153 p2399 TIDs harvested (100 %)**, all canonical-TID validations PASSED (zero «random euro-cent» mismatches across four sessions)
- Coverage by ruler: Frederick III 1648-1670 (full Speciedaler + ½/1/2/3/4-Speciedaler + ½/1/2-Ducat + ⅛/¼/½/2/4-Mark repertoire) + Christian V 1670-1699 (1/2/3/4-Speciedaler with monogram/draped-bust/portrait variants + ½/1/2/3/4-Ducat gold high-denom + 1-Mark/2-Mark/4-Mark cluster; 1699 silver-upgrade 4-Mark KM# 199 @ .833 fineness)
- Save format: `scripts/cache/ucoin/<tid>.json` per-TID files with `_verified: true` + `_canonical_tid` + `_harvested_via: chrome_mcp_html` markers
- Save script: `/tmp/save_ucoin.py` aborts with exit code 2 on canonical-tid mismatch — prevents overwriting cache with the wrong-coin-served-as-defence-response

**Cumulative ucoin session-cookie budget check.** Per `docs/SOURCES.md §13.2`, the empirical cookie-cycle ceiling at 20 s pacing was ~50 fetches. Across batches 1-4 we did ~163 cumulative ucoin requests (153 harvests + 10 enumeration probes) over four ~50-70-min sessions, with **0 canonical-TID failures**. Four-session evidence confirms: the 31-60 s pacing materially extends the budget (or the cookie counter resets between sessions). Empirical cap is well above the §13.2 historical figure.

**p2399 closure (2026-05-18):** Norway Speciedaler 1648-1699 period now 100 % covered. State recorded in `scripts/cache/ucoin/_BR_audit_2026-05-18.json`. Batch 5 pivots to p2400 (Norway Speciedaler 1699-1745, Frederick IV / Christian VI era) — needs listing-page enumeration first to size before building TID list.

**Platform-floor confirmations (this session's discovery):**

  | Platform | DK floor | NO floor | SH floor |
  |---|---|---|---|
  | **Numista** | 1602 | 1602 | 1567 (SH-Gottorp) — varies by SH-issuer code |
  | **NumisMaster** | 1591 | 1608 | 1538 (Holstein-Schauenburg) |
  | **ucoin** | **1582** ✓ | **1648** ✓ | **1787-1851** ✓ (only 15 entries total) |

→ This **closes §BO.1 step 3 «Norway 1514-1601 sweep»** with a clean negative finding: all three commercial / community catalogues have a platform floor for Norway between 1602 and 1648 — no pre-1602 Norge data is recoverable from any of them. The §BF Denmark 1514-1566 gap remains paper-only (Galster / Jensen-Skjoldager) per the original audit.

**Remaining BR scope (after batch 7 / DK Krone era CLOSED):**

  | Scope | Total on ucoin | Cached | Remaining | Batches needed (40/each) |
  |---|---:|---:|---:|---:|
  | NO period 2399 (1648-1699 Speciedaler) | 153 | **153** | **0** ✅ | 0 (CLOSED) |
  | DK period 2939 (SH-Glückstadt 1617-1773) | 50 | **50** | **0** ✅ | 0 (CLOSED) |
  | DK country=schleswig_holstein (1787-1851) | 16 | **16** | **0** ✅ | 0 (CLOSED) |
  | DK period 374 circulation (Christian IX 1873-1906) | 9 | **9** | **0** ✅ | 0 (CLOSED) |
  | DK period 374 commemoratives | 3 | 0 | 3 | ~⅛ |
  | DK period 373 (Frederik VIII 1906-1912) | 7 | **7** | **0** ✅ | 0 (CLOSED) |
  | DK period 220 (Christian X 1912-1914 in-window) | 7 | **7** | **0** ✅ | 0 (CLOSED) |
  | NO period 2400 (1699-1745 Speciedaler) | 23 | 17 | **6** | ~⅙ |
  | NO period 1041 (1746-1812 Rigsdaler) | unknown | 0 | ? | ? |
  | NO period 883 (1813-1815 Rigsbankdaler) | unknown | 0 | ? (1813-1814 portion only) | ~1 |
  | DK Holstein-Gottorp-Rendsburg (1716-1720, newly discovered) | unknown | 0 | ? | small |

**Negative finding (2026-05-19):** ucoin's SH country listing has no entries past 1851 (Provisional Government era end). 1851-1864 SH-duchy coverage (Frederik VII Helstaten era pre-Prussian annexation) is **ucoin platform-floor**, not a harvest gap. The «1851-1864» portion of the user-requested probe is empirically empty.

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

### BV. 🔵 Pre-1582 Danish Müntzfüße — define missing standards in fuesse.yml + Denmark page  *(opened 2026-05-20, user-marked «найвищий», **8 of 8 closed 2026-05-21**, status: In review)* *(est: medium-large)* *(type: data + research-applied)*

**Progress 2026-05-21 — 8 of 8 candidates closed, ticket in In review:**
- ✅ **8_daler_fod** (commits `0102073` + `9343cd6` + `b88c4a9`, §BF closure)
- ✅ **8_daler_lybsk_fod** (same §BF commits, structural Fuß card)
- ✅ **rhinsk_gylden_fod** (commit `81c91fa`, §AW plan executed — 3 specimens promoted f2h3 + f2h6 + c4h29, originally two phases I + II)
- ✅ **f2_guldkrone_fod** (§AV verdict «окрема» 2026-05-21, separate Fuß — 2 specimens promoted f2h2 + f2h5, Klipping-Notmünz-Emission Northern Seven Years' War, 4 new bibliography refs ref33-ref35 added with Wilcke Rentmeister-Rechnungen verbatim, danskmoent.dk, Historyofwar.org)
- ✅ **goldgulden_fod** (verdict «зроби окремою» 2026-05-21, separate pre-Reichsmünzordnung Fuß for the Hungarian-Venetian Dukat standard; 1527-1559 span; 2 specimens promoted c3h1 + c3h2 1557 Ungersk Gylden; metrically identical to reichsdukatenfuss but legally distinct pre-Augsburger 1559 codification; f1h** Frederik I 1527-1533 specimens pending §AZ; documented as merge-back candidate if maintenance-irrelevant)
- ✅ **nobel_fod** (Sovereign-tier Danish prestige gold coinage 1496-1532, modelled on Henry VII's English Sovereign 1489 via Øresund Toll channel; Hans 1496 reference specimen 14.67g per Stack's Bowers Bruun Lot 1001 €1.2M auction; Hans 1502 + Christian II 1516+1518 + Frederik I 1532 + undated Ribe Galster 68/69 — all RRR or unique; 3 new bibliography refs ref36-ref38 with Stack's Bowers + danskmoent.dk + Wikipedia Sovereign; ZERO specimens in cache, pending §AZ Galster + Jensen-Skjoldager paper-source import)
- ✅ **rosenobel_fod** (§AX — Renaissance adaptation of English Rose Noble; Phase I Frederik II 1584 Frederiksborg unique 7.69g + Phase II Christian IV 1611-1629 Copenhagen 8.994g/.833/7.492g fein; ½-Rosenobel «Guldridder» Hede 24; Kalmar War 1611-1613 + Imperial-Danish War 1625-1629 financing context; 5 specimens promoted/reclassified — f2h7b + c4h23a + c4h24 + numismaster-65609 + km-x026 (km-x026 fraction corrected 2→1 from legacy V1 reichsdukatenfuss misplacement); 2 new refs ref39-ref40 danskmoent.dk + Historyofwar Kalmar War; tariff ≈ 3-4 Specie computed, no period attestation — §AX tariff investigation closed as computed, formal verification still optional)
- ✅ **«Gottorp 0.764» (1534 one-off) — NOT a separate Fuß: Galster misattribution.** Investigation 2026-05-21 against `scripts/cache/danskmoent/galster/chr_c3g131.json` revealed danskmoent.dk verbatim correction: «*Roskilde, af Galster fejlagtigt henført til Gottorp*» — actual mint is **Roskilde**, actual year **1536** (not 1534), denomination **1 Rhinsk gylden** (.764 / 3.19g rough / 2.44g fine). Metrics match `rhinsk_gylden_fod` Phase II (.76) within ~1.1 % Δ. **Verdict (user 2026-05-21):** option (a) — folded into `rhinsk_gylden_fod` as new **Phase 0** (Christian III 1536, Roskilde). Existing Phase I (Frederik II 1563-1564) and Phase II (Christian IV 1625-1632) retained unchanged. Belegfenster extended 1563-1632 → 1536-1632 (96-year window with 27 + 61 year hiatus periods). 2 specimens promoted from seed_unsorted: `unified-dk-galster-c3g-131` + `unified-dk-bruun-14770`. Cross-references on the merged type: Schou 4 / Sieg 23 / Friedberg 18 / Lange 18 / Galster 131. No new bibliography refs needed — ref29 (Wilcke 1950) already covers the Rhenish-Gulden standard genealogy.

Project ticket `190229723` ready to flip In review → Done — all 8 candidates closed; remaining work is harvest-bound (§AZ Galster + Jensen-Skjoldager paper-source import for f1h** + c1h** + c2h** + c3h-Flensborg specimens) and tracked under §AZ separately, not §BV.



**Surfaced.** User direction 2026-05-20 with explicit «найвищий» marker. The §8a auto_classify_seed_unsorted classifier can only target Müntzfüße that EXIST in `data/shared/fuesse.yml` AND have phase blocks in the location yamls. A tranche of pre-1582 Danish gold + silver standards is currently absent from our data, so coins from those eras stay stuck in `seed_unsorted` indefinitely regardless of classifier improvements. Goal: ship Fuß definitions on the Denmark page first (no coins required initially) so classifier rules can be authored against them, then per-Fuß coin promotion follows downstream.

**Scope — candidate missing Müntzfüße from the user's preliminary 1390-1660 Danish-gold timeline (2026-05-20).** User explicitly flagged that the timeline values are **NOT to be treated as authoritative** («не сприймай ці визначення як ‹закон›, ми це ще дослідимо детальніше»). Each Fuß below carries a working name + provisional metric; **every metric written into fuesse.yml must trace to a primary or top-tier secondary source per CLAUDE.md §0**.

| # | Working name | Period (in scope 1514+) | Provisional metric | TODO sub-task | Verification debt |
|---|---|---|---|---|---|
| 1 | **`sovereign_fod`** / **`noble_fod`** | C-II 1516-1518 + F1 1524, 1532 (extends to Hans 1496-1502 pre-scope) | gold ~14-15 g rough, .979-.995 fineness (English Sovereign / Noble tier) | new (no TODO yet) | Hans Realer + C-II Realer + F1 Realer — Wilcke 1924/1950 chapter on pre-Reformation gold; Galster 1959-1960; Hede c1h / c2h / f1h primary entries |
| 2 | **`rhinsk_gylden_fod`** | F2 1563 → C-IV 1632 (extends back to Hans 1497 pre-scope) | gold .76-.77 fineness, ~3.25 g rough; per-piece fein ~2.5 g | **§AW (plan ready)** | Wilcke chapter on Rhinsk Gylden; period tariff (1 Rhinsk Gylden ≈ 0.7-0.75 Reichsdukat) needs source |
| 3 | **`goldgulden_fod`** (transitional pre-Reichsdukatenfuß)? | F1 1527 → C-IV 1593 (overlapping with Rhinsk track and post-1564 Reichsdukatenfuß) | gold .986, ~3.49 g rough | new (no TODO yet) | **Open question:** distinct from `reichsdukatenfuss` (1564→1802) or just an early phase of it? Wilcke + Bobzin verification required |
| 4 | **C-III Gottorp 0.764 Dukat-named** (one-off 1534) | C-III 1534 Gottorp only | gold .764, weight TBD | new (no TODO yet) | One-off classification: own Fuß, fold into `rhinsk_gylden_fod` as a higher-fineness variant, or phase under existing `reichsdukatenfuss`? |
| 5 | **`f2_guldkrone_fod`** (écu d'or tier) | F2 1563-64 only | gold .9305, fein 3.120 g per piece (Hede f2h2, f2h5) | **§AV** (pending (a) vs (b) verdict — separate Fuß vs phase under `guldkrone`) | Wilcke + Hede f2h2/f2h5 |
| 6 | **`8_daler_fod`** (silver) | 1541-1582 (København baseline + 1544 debased) | mf 8.827 anchor; fein 26.494 g per Daler at .906 / 14½ Lod | **§BF** (full plan, pending dual-zone verdict) | Wilcke 1950 + Rigsarkivet T.K. 160 + Paus 1752 — already captured in `docs/research/moentordning_1541.md` |
| 7 | **`8_daler_lybsk_fod`** (silver) | 1547-1571 (Lybsk-aligned dual-zone) | TBD per dossier §7.1 (Lybsk sub-Mark + 14¼ Lod Daler) | **§BF** (full plan, sub-design of dual-zone choice) | Same as #6 + 1547 Flensborg Bestalling |
| 8 | **Rosenobel Fuß placement** (1611-1629) | C-IV 1611, 1612, 1613, 1627, 1629 | gold .833, fein 7.495 g per Rosenobel | **§AX** (pending tariff investigation) | Wilcke I + Bobzin + contemporary Danish ordinance for the period tariff |

**Acceptance criteria (per Fuß).** When ANY of these candidates lands in fuesse.yml, the following must all hold:

1. `data/shared/fuesse.yml` entry with: `id`, `name`, optional `historical_name`, `metal`, `grid_unit_g` + `grid_stops` (anchor formula), `fineness_standard`, `fineness_display`, `grundwerte` block (rows for fractions per CLAUDE.md §2 period orthography), `fractions: {N: {soll_rau_g, soll_fein_g}}`, `events` block (`first_adoption.anywhere`, `first_mint.anywhere`, `std_end.anywhere`, plus `anywhere_label: {de, en, uk}`), `description` prose in DE/EN/UK with period orthography per §2. Every metric carries a verbatim source comment (e.g. `# Wilcke 1950 Kap. 7-4 p. 184`).
2. Phase block in `data/v2/locations/denmark.yml` under `fuss_periods.<fuss_id>` with `year_from` / `year_to` per phase + soll values + mint(s) attested + brief description.
3. Added to `fuss_order` list in `data/v2/locations/denmark.yml`.
4. Added to `data/shared/german_fuesse.yml` (landing-page Müntzfüße overview).
5. At least ONE bibliography reference in `data/locations/denmark-references.yml` with verbatim quote ≤25 words + page hint per CLAUDE.md §5a.
6. `python scripts/build.py --validate-only` clean; the Fuß card renders on the Denmark page (V2, default site root) with structural row OK (empty coin tables acceptable initially).
7. **`scripts/maintenance/auto_classify_seed_unsorted.py`** extended with a rule targeting the new Fuß — typically either an era-anchor (year+denomination → Fuß, like the new kronefod rule landed 2026-05-20) or a fineness/weight-Δ math arm. **Without this step the new Fuß is unreachable from seed.**

**V1 NOT touched.** Per the 2026-05-18 V2 promotion (`5df8370 build: V2 default at /, V1 fallback under /v1/`), V1 yamls (`data/locations/<loc>.yml`) are frozen at their post-flip state. New Müntzfüße land V2-only; the V1 page renders its pre-flip Fuß repertoire indefinitely until V1 is retired.

**Sequencing — independent landings, lowest research-debt first:**

1. **`rhinsk_gylden_fod`** (§AW) — plan already ready, metric verified, just needs ship-execution. **Start here.**
2. **`f2_guldkrone_fod`** (§AV) — pending (a) vs (b) verdict from user. Once resolved, ~30 min implementation.
3. **`8_daler_fod`** + **`8_daler_lybsk_fod`** (§BF) — pending dual-zone verdict from user. ~2-3 sessions total (longer because seed coin promotion is bundled).
4. **`sovereign_fod`** — research from scratch. Primary sources for Hans 1496+ + Christian II + Frederik I Realer needed before metric can be written. Estimated 1-2 sessions of source-hunting (Wilcke 1924 + Galster 1959-1960 + Hede c1h/c2h/f1h).
5. **`goldgulden_fod` decision** — separate Fuß vs phase under `reichsdukatenfuss`. Likely resolution after #4 (Sovereign research clarifies pre-1564 gold landscape).
6. **Rosenobel + C-III Gottorp one-offs** (§AX + new sub-task) — likely resolve as standalone phases under existing Fuß families rather than new Fuß slots.

**Cross-references** (existing TODOs subsumed under this umbrella):

- **§AV** Frederik II Guldkrone-fod 1563-64 → row 5 above
- **§AW** Rhinsk Gylden-fod 1563-1632 → row 2 above
- **§AX** Rosenobel 1611-1629 → row 8 above
- **§BF** Christian III dalerfod + flensborg_fod 1541-1582 → rows 6+7 above
- **§BD** Danish Müntzfuß naming convention — applies to ALL new IDs (use Danish form `_fod` rather than German `_fuss` per §BD policy)
- **§BB** Fuß description framing rule — applies to ALL new `description` prose (historical framing only, no parameter bleed)
- **§AU** Frederik II seed promotion — depends on §AV + §AW landings
- **§AZ** Galster + Jensen-Skjoldager paper-source import — independent track that PROVIDES coins for the new Fuß slots once they exist (especially `sovereign_fod` + `rhinsk_gylden_fod`)
- **`docs/V2_PIPELINE.md`** — entity-keyed pipeline; V1 retired to `/v1/` archive 2026-05-18, all new Fuß work is V2-only
- **`scripts/maintenance/auto_classify_seed_unsorted.py`** — every new Fuß must be coupled with a classifier rule extension

**Definition of done.** All 6-8 missing Müntzfüße defined in fuesse.yml + visible on the Denmark V2 page (default site root) with structural rows (empty coin tables OK initially), classifier extended to target each new Fuß (era-anchor or delta-math), at least 6-10 new bibliography refs added across the new Fuß definitions. Coin promotion into each Fuß is a separate downstream task — typically tracked under the per-Fuß sub-TODO (§BF for 1541-1571 silver, sibling per-Fuß TODOs to be opened as each Fuß lands).

---
## High priority

> **Awaiting your verdict before any action**:
> - **§AB** (Daler-Klippe placement — new Fuß `daler_tarif_gold` vs redefine fractions). Deferred 2026-05-13: «поки що нічого з цим не роби, я вивчу питання і повернусь».
> - **§AM** (DROP 5 gold off-strike entries per CLAUDE.md §9.3) — per-case verdict per candidate (PB-1 style).
> - **§AQ** (Seed-merge data augmentation policy — field selection + conflict resolution naming).

> **Curator-ordered sequence (2026-06-01, user-directed «з високим пріоритетом»):** do **§CJ → §CK → §CL** in that order. §CJ + §CK are seed-/data-level work; §CL is the single coordinated propagation that ships everything (ucoin backlog re-seed + numista index-fix re-seed already done this session, plus whatever §CJ/§CK change) to the rendered pages.

### CS. 🔵 Split-duplicate dedup campaign — same coin in 2+ final entries  *(opened 2026-06-03, user-flagged; ongoing, multi-root)* *(est: medium-large)* *(type: merger policy + normalization + parser + curation)*

**Surfaced.** 2026-06-03, user spotted two rendered «duplicates»: 2 Ducat 1644-48 Christian IV (KM 140 vs KM-DK 139,140, both Hede 32, shared Bruun 5730) + ½ Dukat 1647 (Hede 38 vs 40, shared Bruun 5814). «потенційно є й інші».

**Scan recipe (the strong signal).** A Bruun `bruun_collection_id` = ONE physical specimen → must live in exactly ONE final entry. Scan: build `bruun_collection_id → {(entity, final_id)}` across `data/v2/final/*.yml`; any id in ≥2 different entries = a split. **Found 129 ids → 108 split-clusters** (2026-06-03 baseline). Categorise per cluster by normalised-nominal agreement.

**Four roots (≈100 genuine dups) + ~8 spurious:**
1. **Transitivity block** — a KM-sub-variant `no_match` (e.g. NumisMaster KM 139 vs KM 140, both Hede 32) fractures a Hede-cluster; `union()` refuses the confident hede↔bruun merge because the cross-class KM-139/140 pair is a registered no_merge. Needs: when Hede agrees + Bruun-coll-id overlaps, tolerate a KM sub-variant disagreement (extend the §9a type-strong path, OR per-case `merge_decisions`).
2. **Nominal-synonym gaps — ✅ DONE 2026-06-03 (commit `5bac350`).** Added Taler/Reichsthaler→daler, Marck→mark, Rigsdaler Courant↔Kurantdaler, D'or genitive-s to `scripts/lib/nominal_synonyms.py` (in-pipeline via merge/absorb; verified no false-fold). seed_unified diff-nominal splits 37→13 on re-merge (reverted pending batch propagation).
3. **Cross-entity scope** — same coin promoted into BOTH `danish_realm` and `royal_holstein` finals (e.g. Kurantdaler CVII Hede 25 KM 645) → renders twice on denmark (which consumes both). Needs entity-routing consistency / cross-entity dedup.
4. **Hede sub-variant** — Hede 38 vs 40 (½ Dukat 1647) genuinely `no_match` per Hede-as-type-id, yet share Bruun 5814. Needs source check: genuine sub-variants OR one Hede attribution wrong.
+ **~8 spurious Bruun-id collisions** (parser): different coins share a Bruun id — e.g. «1 Ducat Rantzau 1689» ↔ «1 Taler Gottorp 1622»; «12 Mark CVII 1781» ↔ «8 Skilling FV 1763». **User-ordered NEXT** after nominals.
+ **Catalog-ref VALUE formatting — `dav` ✅ DONE 2026-06-03 (commit `e03e6e9`).** Davenport `3682` (Bruun bare) vs `EC II 3682` (Numista) → catalog-disagree. Added `_normalise_dav_value` (strip series prefix EC/GT/ST/CCT/SG/Lg/BrSL/AAO/ECT + roman + «#») — MATCHING only, stored form kept. The Gottorp pair's catalog now agrees. Likely other ref-value-format gaps exist (check fr/sieg/schou formatting on a future pass).
+ **STACKED ruler-synonym `John Adolphus → Johann Adolf` ✅ DONE 2026-06-03 (commit `f5374d0`).** After nominal + dav the Gottorp KM-21 pair STILL no_match on ruler «Johann Adolf»(de) ≠ «John Adolphus»(en) — same Gottorp duke (r. 1590-1616). Reign-window + entity survey confirmed bare «John Adolphus» = only that duke (gottorp 1590-1611); added `\bjohn adolphus\b(?!\s+[ivx])→johann adolf` with a numeral-lookahead guard so «John Adolphus I» (Norburg-Plön, 1690), bare «Adolf» (grandfather 1544-1586), Schauenburg «Adolf XIII/XIV», «Hans Adolf», «Adolf Friedrich» all stay DISTINCT. **All 3 stacked gaps now closed → Gottorp pair match_pair=confident.** The «stacked normalization gaps» pattern (nominal→dav→ruler) is real — each fix reveals the next blocker.
+ **Johan/Johann Adolf spelling-fold ✅ DONE 2026-06-03 (commit `1e15579`).** The Gottorp duke's `johan adolf`(154)/`johan adolph`(120)/`johann adolf`(120)/`johan adolg`(typo)/`hertug johan adolf` → all `johann adolf` (~413 coins). Added leading ducal-title strip (Hertug/Herzog/Duke) + the numeral-guarded `johann?\s+adol(?:f|ph|g)` fold. Reign-window + entity survey verified one duke (1579-1615); 13 collision forms (Johan/Johann Friedrich, John Frederik, Johann III/Georg/Christian, Johan Albrecht, Karl XIV Johan, Adolf, Adolf XIII, Hans Adolf, Norburg-Plön I-forms) confirmed UNCHANGED.
+ **Arabic↔roman regnal numeral ✅ DONE 2026-06-03 (commit `c29a922`).** Analysis of the «Friedrich/Frederik» request surfaced the REAL massive fragmentation: ucoin/Numista «Christian 4»/«Frederik 3» vs Hede/Bruun «Christian IV»/«Frederik III» — ≈19.3k coins, every Danish king split by numeral format. Added `_regnal_arabic_to_roman` in `_normalise_ruler` (IN-PIPELINE — every future merge/absorb). Trailing-only + name-no-digit + no-joint-separator guards (Karl 3 Johan / «eller»-forms untouched); also catches Schauenburg «Adolf 13»→xiii. Matching-only; display keeps source form. Verified + idempotent.
+ **Friedrich/Frederik NAME fold ✅ DONE 2026-06-03 (commit `8a2e367`).** Per-entity reign-window survey confirmed within each REAL entity the Friedrich/Frederik forms are ONE ruler (Bremen archbishop Johann Friedrich, Gottorp Karl Friedrich / Friedrich IV / Friedrich I, Braunschweig Friedrich Ulrich, royal_holstein Frederik I/II/III). Implemented MATCHING-only global spelling fold (chosen approach — simplest + safe; entity-aware display canonicalisation deferred): `friedrich`/`friederich`/`frederick`→`frederik` + `joh(n|an|ann) frederik`→`johann frederik` compound (numeral-guarded) + extended title-strip to `ærkebisp`/`erkebisp`/`archbishop`. SAFE because: matcher is per-entity (cross-entity Friedrichs never compared) + match_pair year/catalog fallback separates the `_unclassified` grab-bag's same-numeral different rulers («Friedrich III» 1491 vs 1888 → years disagree). Numeral guard keeps «Johann Friedrich I» (Saxony 1535) distinct; bare Johan/John untouched. Verified 8 guard forms unchanged; Bremen «John Frederik» ↔ «Ærkebisp Johann Friedrich» now confident.
+ **Christian Albert ↔ Christian Albrecht ✅ DONE 2026-06-03 (commit `78378ef`).** Gottorp duke (r. 1659-1695); both forms = one duke (1661-1694, gottorp/royal_holstein/danish_realm/hamburg). Folded the «Christian Alb…» compound → christian albrecht (German canonical), numeral-guarded; bare Albrecht (Wallenstein) / Johan Albrecht I / Albrecht II. Alcibiades untouched.
+ **Ruler normalization — REMAINING (lower priority):** (a) entity-aware DISPLAY canonicalisation (render German entities' rulers in German form, Danish in Danish — separate from the matching folds, which keep source display form); (b) any further German↔English name pairs surfaced on the next dup-scan — same per-entity reign-window method; (c) the §CS propagation (re-merge → absorb → build) of ALL the ruler + nominal + dav dedup fixes, batched.

**Propagation.** Each fix is a code/data change; the actual page-collapse needs re-merge → absorb → build (the §CL/§CR cycle, now fast via parallel PASS-1). **Batch ONE propagation after the next round of fixes** (parser-collisions + Davenport-value norm + roots #1/#3/#4) rather than re-propagating per fix.

**Curator-ordered sequence (2026-06-03):** nominals (done) → **parser-collisions next** → then roots #1/#3/#4 + Davenport-value norm → single propagation.

### CJ. 🟢 Generic catalogue-index capture audit for ALL non-numista sources (Bruun / ucoin / NumisMaster / IKMK / Hede / Galster)  *(opened 2026-06-01, user-directed «з високим пріоритетом»)* *(est: medium)* *(type: parser audit + data integrity)* — **DO FIRST**

**Surfaced.** 2026-06-01, after the numista parser was found dropping most catalogue indices (`0c84510`: Dav-volume variants + AKS/Jaeger/NWD/Craig/Behrens silently dropped; fixed by routing any unmodelled code → `others`, a GENERIC open approach, not a closed white-list).

**The task.** Audit every OTHER source parser the same way and make each **generic / open to ANY index** (NOT a hard-coded white-list of the few we happen to know):
- `parse_*` / `build_*_seed` for Bruun, ucoin, NumisMaster, IKMK, Hede (danskmoent), Galster.
- For each: enumerate the catalogue-index universe its raw cache carries; confirm typed indices land in CatalogRefs typed fields; confirm EVERY unmodelled-but-real catalogue code is preserved in `others` (full label), not dropped; confirm `_ALLOWED_CATALOG` (or equivalent) is derived from the schema (`CatalogRefs.model_fields`), not a drifting hand-list.
- Pattern reference: the numista fix — `scripts/lib/numista_canonical.py` (`_DROP_REFS` minimal; everything else → `others`) + `build_numista_seed._ALLOWED_CATALOG = set(CatalogRefs.model_fields)`.

**Why.** Same data-loss class as the numista bug — surviving indices on the rendered table must reflect ALL catalogues each source publishes.

**Closed 2026-06-01 (code-level; seed regen → §CL).** Built a SHARED generic mapper `scripts/lib/catalog_codes.py` — `CATALOG_CODE_MAP` (single source of truth: code → schema field), `DROP_CODES` (minimal: only Numista-internal n/uc), `map_catalog_token` / `add_to_catalog` (free-text tokens), and `catalog_from_ref_dict(refs, key_field_map, drop_keys)` (structured refs-dict → CatalogRefs-shaped dict; schema-field keys → typed, everything else → `others` as «Label# value», `schema_catalog_fields()` derived from `CatalogRefs.model_fields`, NOT a hand-list). Applied to the three structured-refs builders: **Bruun** (`build_bruun_denmark_seed`: replaced the `REF_FIELDS`-only loop — it dropped **Aagaard entirely (253 cache refs)** and mapped 8 Swedish keys lott/delzanno/sm/hagander/appelgren/mb_swedish/hauberg/malmer to NON-schema field names that only survived via the Sweden scope-gate; now all → `others`, **243 in-scope Aagaard refs recovered**, ~10 OOS-gated), **Galster** + **Hede** (hardened: were lossless already — Galster verbatim-copied catalog_refs whose keys are schema-field names, Hede explicit per-key map covered all its keys — but neither was generic-safe against a future non-schema key; now route unknown → `others`; Hede keeps the `Frederik`/`Hede` drop_keys).

**Per-source audit results (structured ref fields only; prose-field scans were dominated by English auction prose / mintmaster initials, not catalogues):**
- **ucoin** — `_parse_km_ref` white-list (km/hede/sieg/lange/fr/schou/dav/mb) drops **nothing real** (only «tn» false-positive = the KM *value* «Tn6»). No change needed.
- **Hede** — `catalog_refs` dict keys {hede,schou,sieg,galster,km,fr} all typed. No drop. Hardened.
- **Galster** — `catalog_refs` dict keys all schema-field names. No drop. Hardened.
- **Bruun** — **Aagaard (253) dropped** — fixed (recovered to `others`).
- **NumisMaster** — `parse_references` named regexes (Schou/Lange/Fr/KM/MB/Sieg/Hede/Bruun/Schive/Dav) cover the catalogues that appear; remaining tokens are prose words + mintmaster initials (LS/PN). No structured catalogue drop. Left as-is (a blanket generic scan of its noisy prose body would inject false positives — not worth it).
- **IKMK** — **NOT a code+number source: `literatur` is full prose bibliographic citations** («G. Schön…, Weltmünzkatalog (2004) Nr. 52; H. Hede, … Nr. 1»). The 6-author white-list (Hede/Davenport/Lange/Sieg/Schou/Friedberg) captures the Danish-core catalogues; OTHER authors (Schön=Weltmünzkatalog, Schrötter=Preuss. Münzwesen, Olding, Duve, Fiala — German-states catalogues relevant to the German entities) ARE dropped. **The generic tokenizer does NOT apply** — extracting catalogue+number from prose needs an author-surname→catalogue map, a separate harder problem. **Deferred as its own follow-up** (see §CJ-IKMK below).

**Seed regen DEFERRED to §CL.** The §CJ change is CODE-ONLY this commit. Re-building bruun/galster/hede seeds NOW would bundle ~5000 lines of pre-existing **§CG note-annotation stale-drift** (the committed seeds are out of date with their current builders — verified: a HEAD-code rebuild produces the same drift independent of §CJ) with the +130-line Aagaard recovery — non-atomic. §CL's full re-merge→absorb→render rebuilds all seeds; the Aagaard recovery + the stale-drift land there together legitimately. Galster/Hede entries will also re-indent (older `v2_seed_writer` → current `coins:`-nested form).

### CJ-IKMK. 🟢 IKMK prose-citation catalogue capture (German-states catalogues)  *(opened 2026-06-01, split from §CJ)* *(est: medium)* *(type: parser enhancement)* — **CLOSED (code-level; seed regen → §CL)**

IKMK `literatur` is prose bibliography, not code+number tokens. The 6-author white-list (Hede/Davenport/Lange/Sieg/Schou/Friedberg → typed) missed German-states catalogues cited by author surname.

**Closed 2026-06-01 (code-only; seed regen → §CL).** Verified each candidate author↔catalogue against the actual literatur titles, then added a CURATED `_EXTRA_CAT_AUTHORS` map in `build_ikmk_seed.py` (→ `catalog.others` as «Label# Nr»): **Behrens** (Lübeck), **Welter/Fiala/Duve/Jesse** (Brunswick-Lüneburg), **Dorfmann** (Lauenburg), **Arnold→AKS** (Großer dt. Münzkatalog 1800+), **Schön** (Weltmünzkatalog), **Jaeger** (dt. Münzen seit 1871), **Divo** (dt. Goldmünzen 1800-1930), **Schrötter/Olding** (Prussian). Deliberately EXCLUDED: Kluge + Bahrfeldt (multi-work authors — surname≠single catalogue, would mis-attribute), Schnee/Keilitz (Saxon, OOS), Dannenberg (medieval), Noss (Jülich, OOS), Steguweit (medals=exonumia §9.2), and positional-noise tokens (Die/Das/Sammlung/RIC). New `_EXTRA_NR_RE` handles plain / letter-suffix («90 a», «552 A») / Olding K-numbers («K 16.2/3746»). In-memory test on the cache: **705/1653 IKMK records gain German-states refs** (Schrötter 316, Olding 164, Welter 124, AKS 107, Schön 89, Divo 85, Fiala 60, Jaeger 60, Duve 50, Jesse 37, Dorfmann 34, Behrens 22), **0 regression on typed fields**.

**Latent bug fixed in passing:** `_catalog` did NOT exclude `Vgl.` (cf) segments — so a «Vgl. Hede Nr. 5» cf was captured as a POSITIVE `hede` ref (anti-pattern 5 violation). Now each segment is truncated at the first `Vgl.` (cf can sit mid-segment, e.g. «… Nr. 471. Vgl. v. Schrötter …» — leading-only skip leaked the cf author/number into the wrong field; truncation drops the whole cf tail). 33+ wrongly-captured cf typed-refs will be cleaned when IKMK seeds regenerate in §CL.

### CN. 🟢 Typed inline source-index-errata mechanism  *(opened 2026-06-01, user-directed during §CK pair-2 review)* *(est: medium)* *(type: pipeline mechanism + data integrity)* — **CLOSED (mechanism + first 2 entries; effect lands §CL)**

**Surfaced.** 2026-06-01 during §CK pair-2 (Norway Frederik III Speciedaler). Curator (by image) found a source mis-printing a catalogue index: Bruun Part III lot 12073 prints «KM-48» on a Hede-14 coin (KM 48 = Hede 17); NumisMaster MC_110722 labels «KM 48» on a KM-40-type image. The merger faithfully accumulated the wrong KM. There was NO typed mechanism to (a) pull the record into the correct host despite the wrong source index, (b) record what/where is wrong — only `merge_decisions` (routing, no error semantics), `_curation_holds` (freeze, no correction), and the ad-hoc prose approach of the KM-240 case (37f5b6d).

**Design (curator-chosen):** inline on the seed entry (NOT a separate file — co-located with the source's own data), applied at seed build, with a visible trail.
- **`_source_errata`** (curator input, on the seed entry): list of `{field, printed, correct, reason, curator}`. `printed` preserves what the source faithfully printed (provenance); `correct` is the curator-verified value; `reason` is self-contained evidence.
- **`apply_source_errata`** (`lib/seed_merge.py`): runs LAST in `merge_seed` (after the merge, so it wins over the parser, which keeps re-emitting the wrong value from the immutable cache) — overwrites the field with `correct` and writes an **`_errata_applied`** audit trail. `_source_errata` is preserved across regen exactly like `_curation_holds` (`_PRESERVE_ALWAYS_KEYS`).
- **Routing follows for free:** fixing the index → the corrected value drives matching, so a mis-labelled record re-routes to the correct host at re-merge (no separate `merge_decisions` needed).
- **Merger propagation** (`merge_seeds_cross_source.py::_synthesise_unified_entry`): aggregates members' errata into `_errata_applied` on the unified entry.
- Both `_`-keys are auto-stripped before Coin validation + not rendered (build.py strips all `_`-keys); the corrected scalar (e.g. `km: 40`) IS rendered. No schema change needed.

**First two entries (committed):** `dk-bruun-9663` (km 48→40) + `denmark-numismaster-110722` (km 48→40). Mechanism unit-tested (correct + preserve-across-regen + idempotent). Build validates.

**Effect lands in §CL.** The seed km is already corrected; the re-merge will (a) drop KM 48 from the Hede-14 unified entry, (b) **re-route `denmark-numismaster-110722` to the KM-40 (Hede 14) host** — VERIFY this lands correctly post-merge (its year 1653-1656 overlaps Hede 17, so confirm the km-40 signal wins; if it orphans, add a `merge_decisions` force-merge). nf3h17 keeps `km: ['48','A46']` (A46 = legit sub-type per curator). A reader-facing footnote on the corrected coin is NOT auto-generated (§0a); add per-coin via the errata `reason`→note path only on explicit request.

### CK. 🟢 Curator image-review of 30 IKMK candidate-duplicate pairs  *(opened 2026-05-31, user-directed «з високим пріоритетом», re-confirmed актуально 2026-06-01)* *(est: medium)* *(type: dedup verification — curator decides by images)* — **DO SECOND**

**Surfaced.** 2026-05-31 during the IKMK→final propagation. 30 IKMK standalone coins share nominal+ruler+year(±1) with an existing coin but were NOT auto-merged (no wrong merge made). Curator must decide same-coin (consolidate) vs distinct (keep both) **by images** per the standing constraint «остаточне рішення це чи є вони однією монетою дивлячись на їхнє зображення». Work-list with IKMK image links + existing-coin identity: `docs/ikmk_candidate_duplicates_review.json` (triaged: 27 distinct-by-§9.4-catalog, 3 genuine same-catalog candidates). Process: present pairs → curator verdict per pair → consolidated-same via `merge_decisions`, distinct kept.

### CL. 🟢 Coordinated re-merge → re-absorb → render to ship all accumulated seed-level changes  *(opened 2026-06-01, user-directed «з високим пріоритетом», **closed 2026-06-01**)* *(est: medium)* *(type: pipeline propagation + verification)*

**Closed 2026-06-01.** Ran the full pipeline in a routine-quiet window (3 atomic commits `29a1dca` / `51288c5` / `4f22f45`):
- **§CL-1 seed regen** (bruun/galster/hede, cache-only): Aagaard 243 recovered, Galster/Hede generic, §CN errata preserved+re-applied through merge_seed (dk-bruun-9663 km 40), + §CG note-drift. **IKMK NOT regenerated** — bare `build_ikmk_seed` wrote 0 entity files (its entity-write path is gated behind open §CH); the §CJ-IKMK German-states `others` materialize when §CH lands.
- **§CL-2 merge** (all entities): 11609 seeds → 7567 unified (4042 merges); curator decisions reapplied (21 forced merges + 30 forced no_merges); **over-merge audit SAFE 0 / COMPLEX 0**; 0 duplicate unified ids; **§CN routing confirmed** — `denmark-numismaster-110722` left the false km-48/Hede-17 host, routed to a km-40 host (`unified-dk-hede-nf3h21`, hede 21 — exact Hede sub-type is a curator image-call, but it's out of the wrong km-48 host).
- **§CL-3 absorb → final**: 7018 final entries, 81 newly absorbed, 13 stale refs purged, 0 duplicate final ids, build.py renders clean. Aagaard 244 + numista index-fix others (1421 others-blocks) surface on the pages.

**Residuals (NOT shipped by §CL, by design):**
- **§CM German-entity ucoin coins** (Brunswick-Lüneburg / Osnabrück / Oldenburg / Lauenburg) reached seed_unified but have **no `final/` foundation** → in the absorb "genuinely new (pending): 286" bucket; new `classification_decisions/` stubs created for them. They await **curator promotion + a display page** (the pipeline does not auto-promote new entities to final). Surfacing them on pages is a separate follow-up.
- **§CJ-IKMK others** deferred to §CH (IKMK builder entity-write).
- 51 enrichment conflicts + 4 multi-match warnings logged during absorb — review when convenient.
- 3 §CL commits local-only — push pending user request.

**Surfaced.** 2026-06-01. Seed-level changes accumulated that are NOT yet on the rendered pages: (a) numista index-fix re-seed — **947 numista seeds gained `others`/`dav`-volume refs** (`0c84510` + `_ALLOWED_CATALOG`-from-schema), (b) §CM German-entity ucoin coins once routed, (c) §CJ Bruun **Aagaard recovery (243 refs → `others`)** + Galster/Hede generic-mapping (lossless but re-serialises), (d) §CN source-index errata — `dk-bruun-9663` + `denmark-numismaster-110722` km 48→40 (re-merge drops KM 48 from the Hede-14 unified + re-routes 110722 to the KM-40 host — VERIFY post-merge). Run the single coordinated propagation: `merge_seeds_cross_source.py --apply` (all entities) → `gen_overmerge_purge_allowlist.py --write` → `absorb_seeds_into_final_v2.py --apply` (all entities) → `build.py`. Verify: over-merge audit SAFE 0, no new dups, all curator `merge_decisions`/`no_merges` reapply, the recovered numista indices + §CM ucoin coins + §CJ Aagaard refs surface, build clean. Cache-only, no API cost; large run touching all entities.

> **§CL MUST regenerate bruun/galster/hede + ikmk seeds first** (`build_{bruun,galster,hede}_denmark_seed.py` + `build_ikmk_seed.py`, cache-only) — §CJ + §CJ-IKMK landed code-only, so those seeds are stale vs their builders. Expect a LARGE but legitimate seed diff combining: §CJ Aagaard recovery (+`others`), §CJ-IKMK German-states-catalogue recovery (705 IKMK records gain `catalog.others`) + 33+ `Vgl.`-cf typed-ref cleanups, pre-existing §CG note-annotation drift (note/nominal/translation churn — confirmed builder-driven, not hand-edits), and a Galster/Hede/IKMK entry re-indent to the current `coins:`-nested writer form. Commit that seed regen as its own atomic step (separate from the merge/absorb/render commits) so the drift + recoveries are reviewable together but isolated from the propagation logic.

**MANDATORY — commit `parsed/` to the submodule whenever the re-process re-parses.** Since 2026-06-01 the numista Phase-2 sidecars (`scripts/cache/numista/parsed/`) are version-controlled (Option A). Any `parse_numista --force` run mutates those NOW-TRACKED files, so the PB-10 two-step dance applies: (A) `git -C scripts/cache add numista/parsed/ && git -C scripts/cache commit numista/parsed/ -m "…"` + push submodule, then (B) bump the main pointer (`git commit scripts/cache -m "…"`). Do this BEFORE the main `build.py` commit so the synthesis provenance ships with the seeds. (Other sources keep parsed sidecars as tracked siblings, no subdir — they commit as normal cache files.)

**NOTE — the «1031 ucoin backlog» was a counting artifact, NOT a real gap.** V1-anchored ucoin tids are seeded under their curator id (e.g. tid 163005 → `km-69-chr-iv-1619`, NOT `dk-tid-163005`); counting only `dk-tid-*` undercounted. The ucoin re-seed (2026-06-01) reported `added_new=0` for the mapped entities — the DK-realm/Norway/SH/Hamburg/Lübeck ucoin seed is complete, not stale. The genuine ucoin gap is §CM (unmapped German entities).

### CM. ✅ ucoin builder — add country→entity mappings for the 6 German mission entities (~734 harvested coins unseeded)  *(opened 2026-06-01, **closed 2026-06-01**)* *(est: small-medium)* *(type: builder coverage + data)*

**Closed 2026-06-01.** Added the German country tokens → entity mappings to `build_ucoin_seed.py::URL_COUNTRY_TO_ENTITY` (brunswick/brunswick_wolfenbuttel/brunswick_luneburg → herzogtum_braunschweig_lueneburg; osnabruck → hochstift_osnabrueck; bremen → erzbisthum_bremen_verden; hesse_kassel → landgrafschaft_hessen_kassel; oldenburg → grafschaft_oldenburg; lauenburg → herzogtum_sachsen_lauenburg) AND the matching `ENTITY_WINDOW` entries (1559-1914, required because `--all` iterates ENTITY_WINDOW.keys() + build_seed gates on membership). Re-ran `build_ucoin_seed --all` → **700 German ucoin coins now seeded** (Brunswick 333, Osnabrück 174, Bremen 84, Hesse-Kassel 62, Oldenburg 35, Lauenburg 12; 11 pre-1559 Bremen correctly skipped-oob). `german_empire` (27) intentionally NOT mapped — unified-Empire common types don't belong to a single mission state; **left as a residual curator decision** (which entity, if any, should own the generic Reichsmark types). These seeds are `seed_unsorted` and reach the page via §CL.

**Surfaced.** 2026-06-01. `build_ucoin_seed.py::URL_COUNTRY_TO_ENTITY` maps only denmark/norway/schleswig_holstein/hamburg/lubeck. ucoin URLs for **Brunswick** (brunswick / brunswick-wolfenbuttel / brunswick-luneburg = 333), **Osnabrück** (174), **Bremen** (91), **Hesse-Kassel** (62), **Oldenburg** (35), **german_empire** (27), **Lauenburg** (12) — ~734 harvested + verified ucoin records — route to `None` → silently skipped → never seeded. All are in the mission scope. Add the country tokens → entity mappings (erzbisthum_bremen_verden, grafschaft_oldenburg, herzogtum_braunschweig_lueneburg, herzogtum_sachsen_lauenburg, hochstift_osnabrueck, landgrafschaft_hessen_kassel, + a german_empire decision) and re-seed those entities. (numista already seeds these German entities; only the ucoin builder lacks the mapping.)

> **Note 2026-06-01:** the §CM residual «German coins not on pages» is now RESOLVED — the 6 German location pages render their seed_unsorted coins (phase-def alignment + paper-metal guard, commit `f2dab89`), seed_unsorted windows are project-focus per jurisdiction (`b10697c`), and the Denmark page is now a Danish-monarch realm-aggregate via per-entity consume-window (`fc81335` + `0122a6c`). Three follow-ups remain — §CO / §CP / §CQ below.

### CO. ✅ `german_empire` — own location for the Reichswährung tier  *(opened 2026-06-01, **closed 2026-06-01**)* *(est: small)* *(type: curator decision + new location)*

**Closed 2026-06-01.** Curator chose option (c): the unified-Empire mark/pfennig coinage (1871-1914, Reichsgoldmünzfuß) gets its OWN mission entity + display location `german_empire`. Done: registered the entity in `data/i18n/issuing_entities.yml` (Deutsches Reich / German Empire / Німецька імперія, abbrev DR); mapped `german_empire → german_empire` in `build_ucoin_seed.py::URL_COUNTRY_TO_ENTITY` + `ENTITY_WINDOW (1871, 1914)`; re-seeded → 27 ucoin coins (1873-1908); created `data/v2/locations/german_empire.yml` (consumes `german_empire`, summary framed on the Reichsgoldmünzfuß / Münzgesetz 4 Dec 1871, seed_unsorted phase 1871-1914); merged → seed_unified. Page renders all 27 coins in DE/EN/UK + appears on the landing; build clean. Coins are seed_unsorted (Bulk-Seed) pending Phase-4 classification — gold (10/20 Mark) → `reichsgoldmuenzfuss`, silver/base → the imperial Scheide tier.

### CP. 🟢 Review 51 enrichment conflicts + 4 multi-match warnings from the §CL/§CH absorb  *(opened 2026-06-01, user-directed «високий пріоритет»)* *(est: small-medium)* *(type: data audit + curation)* — **ready**

`absorb_seeds_into_final_v2.py --apply` logs «Enrichment conflicts (logged): 51» + «Multi-match warnings: 4» across the full-entity run. Enrichment conflicts = a final entry's composed_of members diverge on a scalar field at enrichment time (the discarded variant must not be silently lost — §9a / data-accumulation). Re-run absorb with `--verbose` (or read the absorb log / `data/v2/match_uncertainty/` + `classification_decisions/`) to enumerate the 51, then per-case: confirm the kept value is correct + surface the discarded variant (list-form / match_uncertainty) or record a curator decision. The 4 multi-match warnings = a seed coin matched >1 final foundation — verify the chosen one.

### CQ. 🟡 Monotonic-absorb fix — stop new-source re-merge de-promoting existing finals (14 IKMK in pending)  *(opened 2026-06-01, user-directed «високий пріоритет», design in §CH)* *(est: medium)* *(type: build mechanism — cron-critical, all-final blast radius)* — **needs focused session**

When a new source is merged + re-absorbed (e.g. §CH fresh-IKMK), the absorb's stale-foundation-purge drops a foundation whose grouping changed, and the replacement unified host fails the D40 bulk-promote peer-check → lands in pending instead of final. §CH-2 (2026-06-01) de-promoted **14 in-scope IKMK coins** final→pending this way (verified: 0 NON-IKMK foundations harmed that run, but the bug is general — affects ANY new-source re-merge). **Full diagnosis + fix design already written in §CH (Normal-priority block, «monotonic absorb»):** track prior-final source-ids; force-promote (sticky) any unified host whose composed_of contains an «owed» prior-final source-id. Test gate: re-run absorb across ALL entities with no seed change → assert zero net coin-count change (idempotency) before commit. Until shipped, the 14 IKMK stay seed-only (data intact in seed_unified/pending). Promoted to High here per user; design lives in §CH.

### CI. 🟢 Legend-verify the 82 dual-denomination nominals (harvest-routine priority — Chrome MCP, NOT Numista API)  *(opened 2026-05-30, user-directed «пріоритетний»)* *(est: medium)* *(type: harvest verification + curation)*

**Surfaced.** 2026-05-30, §CG stage C part 2. The dual full-denomination nominals («4 Mark = 1 Krone», «16 Skilling = 1 Mark», «2 Krone (8 Mark)», «12 Mark = 3 Kroner», «1 Portugaløser (10 Ducats)», …) cannot be auto-cleaned because **some coins genuinely carry a DUAL denomination on the coin itself** — e.g. «16 Rigsbankskilling = 5 Schilling Courant» (the dual-inscribed Rigsbankskilling, Phase 2 of `18_5_thaler_fod`, the canonical §1 example) and «16 Skilling (1 Mark = 1/6 Speciedaler)». Per CLAUDE.md §1: **if the dual is inscribed on the coin, KEEP it; if the second value is only an editorial equivalent, the inscribed denomination is the nominal and the equivalent → `note`.** Deciding requires the actual legend.

**Work-list:** `docs/cg_dual_denomination_verify.json` — 82 coins (id + nominal + entity + catalog refs), grouped: danish_norway 24, danish_realm 17, herzogtum_braunschweig_lueneburg 12, hochstift_osnabrueck 9, schauenburg_pinneberg 9, royal_holstein 5, erzbisthum_bremen_verden 3, herzogtum_sachsen_lauenburg 2, grafschaft_oldenburg 1.

**Wired into the harvest routine 2026-05-30** (commits `4a3c886` super + `1c78a3a1` submodule): `_harvest_handoff.json::priority_override` → `task: §CI` so the routine surfaces it at preflight + honours it FIRST; procedure in **HARVEST_ROUTINE.md §5.6**; per-run progress in `ci_verified_ids`. So this is now an ACTIVE routine priority, not just a backlog entry.

**Method (user-directed 2026-05-30).** «варто спробувати механізмом харвест рутини … нуміста по апі не перевіряй, можна через хром мсп». For each coin fetch the legend via **Chrome MCP** (IKMK / danskmoent / Numista-page-via-Chrome — **NOT** the Numista API, budget-bound). Then per coin: (a) legend shows BOTH denominations → keep the dual nominal as-is; (b) legend shows ONE → set `nominal` to the inscribed denomination, move the other to `note`; (c) no legend / undated → leave + flag. This is a harvest-routine priority pass (targeted fetch of 82 known coins, not manifest enumeration). The §CG stage-A/B normaliser already handles everything else; this closes the §1-ambiguous remainder.

### W. 🟢 Clean up §0z violations surfaced by `scripts/audit_prose.py`  *(opened 2026-05-13, promoted Normal → High 2026-05-23, user-directed «з високим пріоритетом»)* *(est: medium-large)* *(type: prose cleanup + linter integration)*

**Surfaced.** The new prose-linter `scripts/audit_prose.py` (commit ahead) catches forbidden patterns per CLAUDE.md §0a/§0z/§2a/§2/§0b across all `data/**/*.yml` rendered-prose surfaces. First run reports **873 hits across 8 files** — most are real violations, not false positives.

**Re-audit 2026-05-23 (after the session-scoped §0z cleanup landed in commits `1a1d77d` + `b5097ee`):** `.venv/bin/python scripts/audit_prose.py --rule §0z` still reports **577 hits across 4 files**. The session-scoped cleanup hit the user-flagged «Наразі НУЛЬ еталонних зразків у кеші — pending §AZ Galster + Jensen-Skjoldager paper-source import» class (Modellierungsnotiz / mission-scope-clipped / Aktuell-NULL / aktuellen-Projekt-Cache wrappers in `fuesse.yml` + `denmark.yml`); the residual 577 are different shapes — listed below.

**By rule (current snapshot 2026-05-23):**

  - **§0z: 573 errors initially → still the dominant residual class.** 552 of these = `verification_note` fields literally citing «CLAUDE.md §4» / «CLAUDE.md §0» in the tooltip text — a project-internal-meta reference that the role-3 numismatist-reader sees in the (?) tooltip but has no context for. Bulk-introduced by the canonical-fineness backfill (§R-style) where the auto-generated verification_note explained the inference with «Per Projekt-Konvention (CLAUDE.md §4) auf den kanonischen Müntzfuß-Wert … gesetzt». The remaining hits are «in unserem» / «у нашій» first-person-plural project-self-references in coin notes + reference-file entries. The fix is mechanical: rewrite to say WHAT (canonical-fineness-from-Müntzfuß-standard) without WHERE-IT'S-CODIFIED (CLAUDE.md §4), and strip first-person-plural project framing from role-3 prose.
  - **§2: 90 errors + 123 warnings.** Period-orthography violations in DE prose — modern «Taler» / «Münzfuß» / «Münzvertrag» / «Münzreform» that should be «Thaler» / «Müntzfuß» / «Müntzvertrag» / «Müntzreform». The 123 warnings include modern «Mark» (where period-correct is «Marck») and modern «bis» (where period-correct is «biß») — those are higher-volume and need manual judgment because some quoted text from Wikipedia legitimately uses modern spelling.
  - **§0b: 61 warnings.** «vermutlich» / «імовірно» / «presumably» / «likely» hedge words without explicit hypothesis marker. Each needs review: either label as hypothesis pending verification, or attribute to a period source's own uncertainty, or replace with a hard claim once verified.
  - **§2a: 17 warnings.** Sensationalist intensifiers («extrem», «величезний») — easy mechanical rewrite to quantified language.
  - **§0a: 9 warnings.** First-person plural («presumably») in EN prose — needs voice rewrite.

**Plan.**

  1. **§0z verification_note cleanup** (biggest single class). One-pass `scripts/maintenance/rewrite_verification_notes.py` that walks all coins, detects the «Per Projekt-Konvention (CLAUDE.md §X)» template, and rewrites to the role-3-clean form. Target rewrite:
     - Before: «Per Projekt-Konvention (CLAUDE.md §4) auf den kanonischen Müntzfuß-Wert (9_thaler, Anker 0.8889) gesetzt; Δ -1.31% gegen den Soll-Wert.»
     - After:  «Probe nicht direkt belegt; aus dem kanonischen Müntzfuß-Standard (9_thaler, Anker 0.8889) übernommen. Δ -1.31% gegen den Soll-Wert liegt in der Spezimen-Toleranz.»
  1a. **«in unserem» / «у нашій» first-person-plural sweep.** Companion pass to (1) — strip project-self-references from coin-note + reference-entry prose. Replace «in unserem Fuß-Register noch nicht definiert» with «im hiesigen Fuß-Register noch nicht definiert» / drop the project framing entirely.
  2. **§2 orthography cleanup** — sweep Taler→Thaler, Münzfuß→Müntzfuß, Münzvertrag→Müntzvertrag, Münzreform→Müntzreform in DE-only fields (`note.de`, `description.de`, `verification_note.de`, `entries[].content.de`). Mostly mechanical; «Münze» (the institution) stays; «Reichsmünz-» / «Kurantmünz-» compounds in banking context stay.
  3. **§0b hedge-word audit** — per-coin manual review. Each «vermutlich» / «likely» is either correctable (attribute to source) or needs an actual verification step (per CLAUDE.md §0b).
  4. **§2a + §0a** — small enough to fix inline as discovered.

**Operational integration (after cleanup).** Once the project starts clean, wire `audit_prose.py` into:
  - **Pre-commit hook** (`.githooks/pre-commit`) — refuse to commit when ERRORs are introduced.
  - **CI on push** — informational warning report for WARNINGs.

The lint rule set itself can keep growing as new anti-patterns are discovered; the rules list at the top of `scripts/audit_prose.py` is intentionally inline + scannable.

### CA. 🟢 Build per-resource harvest skill (`/harvest-numista`, `/harvest-ucoin`, `/harvest-bruun`, `/harvest-hede`, `/harvest-galster`, `/harvest-ikmk`)  *(opened 2026-05-22, user-directed)* *(est: medium-large)* *(type: tooling + automation)*

**Surfaced.** User direction 2026-05-22: «створи туду високого пріоритету – зробити скіл для харвесту для кожного ресурсу». Trigger context: discovered systematic data-loss in Numista harvest (Chrome MCP scraper collapsed «Years: 1496, 1502» discrete → `year_first: 1496, year_last: 1502` continuous range; 122 cache entries affected; HARVEST_ROUTINE.md §2.3 + builder fixed 2026-05-22 + handoff queue created in `docs/handoff_numista_year_list_reharvest.yml`). The fact that a single field-shape gap costs ~122 backfill entries suggests the current «long monolithic HARVEST_ROUTINE.md doc» pattern is fragile — easy to miss field-shape edge cases, no executable validation, no per-resource isolation.

**Goal.** Replace the resource-specific sections of HARVEST_ROUTINE.md with dedicated **skills** invocable as `/harvest-<resource>` slash commands. Each skill encapsulates: the URL pattern, the data shape (with `year_list` / `years_text` / `mintmaster` / etc. all enforced via field schema), the save script, the rate-limit cadence, the canonical-page-vs-redirect validation, and the per-resource quirks doc reference.

**Per-resource skills to build (in expected priority order):**

1. **`/harvest-numista`** — Chrome MCP HTML scrape, slug-free URL, year-shape distinction (single / dash-form continuous / comma-form discrete), Numista API quota guard (per CLAUDE.md «Numista API budget» rule). Drives `scripts/cache/numista/`.
2. **`/harvest-ucoin`** — Chrome MCP, slug-required URL (`/coin/<slug>-tid-<TID>`), canonical-TID re-verification gate (`_verified: false` → abort save per §1a save_ucoin.py), Cloudflare retry path. Drives `scripts/cache/ucoin/`.
3. **`/harvest-bruun`** — Stack's Bowers PDF mining via pdf-viewer MCP, per-lot extraction with KM / Hede / Sieg / Schou citation parsing. Drives `scripts/cache/bruun/`.
4. **`/harvest-hede`** — danskmoent.dk multi-page (deep page + index-stub paths), embedded image-table OCR-or-manual-typed input, Galster cross-reference capture. Drives `scripts/cache/hede/` (currently driven by `scripts/parse_hede.py`).
5. **`/harvest-galster`** — Galster catalogue standard format, sub-variant index handling. Drives `scripts/cache/galster/`.
6. **`/harvest-ikmk`** — IKMK Berlin museum API (`/object/<id>/json/`), bulk-fetch friendly. Drives `scripts/cache/ikmk/`.

**Minimum spec per skill:**

- **Frontmatter** — name, description, expected input pattern (e.g. «list of NIDs» / «list of TIDs» / «lot range»).
- **URL-pattern + extractor JS** — verbatim Chrome MCP `browser_batch` snippet that returns the harvest payload.
- **Field schema** — enumerated list of every cache field with type + nullability + how to encode each Numista-/ucoin-display shape (e.g. the `year_list` distinction documented this session).
- **Save script** — call signature for `/tmp/save_<resource>.py` (preflight from HARVEST_ROUTINE.md §1a still applies but skill checks presence + recreates if missing).
- **Per-resource quirks** — cross-reference to `docs/SOURCES.md` §13 entry for the source. Skill should refuse to harvest if the quirk log lists an active unresolved issue.
- **Rate-limit cadence** — `sleep $((RANDOM % 30 + 31))` between calls (current convention), or resource-specific.
- **Cache validation step** — after save, validate the JSON shape against the schema; abort if missing required fields.

**Migration path.** Each new skill REPLACES the corresponding section of HARVEST_ROUTINE.md. The .md doc shrinks to: (a) preflight (§1, §1a, §1.5), (b) priority order (§2.2, §4.2), (c) commit cadence (§3, §5), (d) coverage tables (§6) — all resource-agnostic. The resource-specific «how to fetch one entry» disappears from the doc and lives in the skill instead. This gives us: (i) per-resource isolation — fixing a Numista shape gap doesn't risk touching ucoin / Hede prose, (ii) executable validation — a skill can enforce the schema at save time, (iii) discoverability — `/harvest-` autocomplete shows the available resources.

**Acceptance criterion.** All 6 skills exist + the corresponding HARVEST_ROUTINE.md sections shrink to a one-line «see /harvest-<resource>». A fresh agent picking up a harvest task discovers the right skill from the slash autocomplete + reads the skill spec instead of the long .md.

**Cross-reference.** `docs/HARVEST_ROUTINE.md` (current resource-by-resource format), `docs/HARVEST_GUIDE.md` (deeper per-source playbooks), `docs/handoff_numista_year_list_reharvest.yml` (immediate backfill queue the first new skill can consume as input).

### BZ. 🟢 Krone-Fuß vernacular names — confirm/add «Груба Крона» / «Тонка Крона» with source citations in descriptions  *(opened 2026-05-21)* *(est: small)* *(type: prose enrichment + sourcing)*

**Surfaced.** User direction 2026-05-21: ensure the **descriptions** of `kronemont` (10½-Krone-Fuß) and `kronemont_fine` (13-Krone-Fuß) explicitly mention the period-attested vernacular names — «Груба Крона» (Grov Krone / Grobe Krone) and «Тонка Крона» (Fin Krone / Feine Krone) respectively — with inline source citations (per CLAUDE.md §5 web-sourced facts → bibliography entry + inline `<sup>` citation, IMMEDIATELY).

**Current state on `data/shared/fuesse.yml`.** The vernacular names DO appear in the Grundwerte headings + one rechnungsfraktionen passage:

- **`kronemont.grundwerte.heading`** (line 2098-2100): «<i>Grobe Krone</i>» / «<i>Груба Крона</i>» — appears as part of the heading subtitle but unsourced.
- **`kronemont.grundwerte.rechnungsfraktionen.uk`** (line 2157): «<i>13-Krone-Fuß («Тонка Крона»)</i>» — passing mention in cross-reference, also unsourced.
- **`kronemont_fine.grundwerte.heading`** (line 2228-2230): «<i>Feine Krone</i>» / «<i>Тонка Крона</i>» — same shape as `kronemont`, also unsourced.

The longform `description:` blocks (line 2158-2173 for `kronemont`, line 2288-2306 for `kronemont_fine`) **DO NOT** mention the vernacular names AT ALL. The reader who skips the Grundwerte heading and reads only the prose description never learns these were the period-current Danish names.

**Required action.**

1. **Find primary sources** for both vernacular names (Hede 1957, Wilcke I/II 1919/1924, Aagaard Glückstadt 1671-1696, danskmoent.dk artikler — likely candidates). Each name needs a period-attested source quote, not just modern numismatic-encyclopaedia paraphrase. Confirm the actual Danish forms — «Grov Krone» / «Grove Krone» (the modifier inflection «Grobe» vs «Grov» depends on grammatical context) and «Fin Krone» / «Feine Krone».
2. **Add to descriptions:** weave the vernacular names into the existing description prose (DE/EN/UK) with inline `<sup><a href="#refNN">[NN]</a></sup>` references. The reader should learn the period-current name AND understand its etymology — «груба» = «coarse» (lower fineness, .672), «тонка» = «fine» (higher fineness, .8333) — from the description, not just the heading.
3. **Bibliography entries:** add to `data/locations/denmark-references.yml` per CLAUDE.md §5a (Wikipedia-style atomic refs with verbatim quote + page hint). Likely candidate sources:
   - Hede 1957 NNUM article «Kronemønten 1618-1771» (already ref4 / ref9 in denmark-references.yml — may already carry the period names; verify).
   - Wilcke II 1924 «Møntvæsenet under Christian IV og Frederik III 1625-1670» (already ref16) — historical naming.
   - danskmoent.dk article «1 Krone / 4 Mark» (already ref1) — verify Hede-school usage.
   - Aagaard 2022 «Christian V Kronemønt Glückstadt 1671-1696» (ref15) — Glückstadt-era naming.
4. **Same fix on the Denmark page (`data/v2/locations/denmark.yml` if separate description-text lives there)** if the location-overlay block carries an independent prose for these Fuß.

**Acceptance criterion.** After the fix, a reader scanning the description prose (the long-form text, not the Grundwerte heading) for `kronemont` should encounter «Grobe Krone / Grov Krone / Груба Крона» with a `<sup>[N]</sup>` citation; same for `kronemont_fine` with «Feine Krone / Fin Krone / Тонка Крона». Verbatim period-source quotation preferred over secondary-source paraphrase.

**Cross-reference.** This pattern (period vernacular name + etymology + source) is the same shape as the «Guldridder» nickname already documented for the ½-Rosenobel Hede 24 (period prose, sourced) — use that as a model.

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

### BW. 🟢 Persist `classification_signal` on coin entries for audit traceability  *(opened 2026-05-20, user-marked «високий»)* *(est: small)* *(type: data + classifier extension)*

**Surfaced.** User direction 2026-05-20 with explicit «з високим пріоритетом» marker. The §8a classifier (`scripts/maintenance/auto_classify_seed_unsorted.py`) runs multiple rule arms in sequence (`_classify_via_yield` → `_classify_via_kronefod_anchor` → `_classify_via_era_anchor` → `_classify_via_delta`) and produces a single best-match decision per coin. At `--apply` time only the resulting (`fuss`, `phase`, `kind`) lands on the coin entry — the **signal that produced that decision is discarded**. A curator looking at `fuss=kronefod` in `data/v2/final/danish_realm.yml` cannot tell whether it came from the `era_kronefod` year+denomination anchor, the `delta_confident` fineness+weight math, or `hede_yield` (Hede-attested Müntzfuß yield), without re-running the classifier in `--show all` mode.

**Why this matters.**

1. **Reviewability** — when a curator suspects a misclassification, knowing which signal produced it tells them where to debug (rule logic vs source data).
2. **Rule-impact metrics** — once we extend the classifier (new era-anchor rules, fineness-class rules for Søsling-scale Scheidemünze, etc.) we want to know which existing classifications were touched by which rule, so a rule change can be audited against the population of coins it affected.
3. **Future re-classification** — if we re-run the classifier with refined rules, we want a way to compare «what signal X produced last time vs this time» per coin.

**Plan.**

1. **Schema extension** in `scripts/lib/schema.py`:
   ```python
   class Coin(BaseModel):
       classification_signal: str | None = Field(
           None,
           description="Which classifier signal produced (fuss, phase). "
           "Set automatically by auto_classify_seed_unsorted.py --apply. "
           "Values: hede_yield, era_kronefod, era_anchor, delta_confident, "
           "delta_low_conf, delta_scheide, curator_decision (manual override), "
           "legacy_v1 (pre-V2 manual placement, signal not re-derivable)."
       )
   ```
2. **Classifier `--apply` writes the field**: when mutating a coin's fuss / phase, additionally set `coin["classification_signal"] = decision["signal"]`.
3. **`CURATED_FIELDS` (in `scripts/lib/seed_merge.py`)** — add `classification_signal` to the allowlist so future merges preserve it. Manual override convention: setting `classification_signal: curator_decision` in a `classification_decisions/<entity>.yml` entry signals «manual override, do not auto-reclassify on next pass».
4. **Backfill for existing classifications**: one-time pass that walks `data/v2/final/*.yml`, runs the classifier rules in detection-only mode (no apply, no mutation), and writes `classification_signal` for every non-`seed_unsorted` coin whose signal can be re-derived. Coins where the rules don't re-fire (e.g. legacy curator-edited) get `classification_signal: legacy_v1` to flag them as carrying pre-V2 manual placement.
5. **Audit hook**: add to `audit_v2.py` a section reporting `classification_signal` distribution per entity — helps spot drift over time («Why did our era_anchor population shrink from 25 to 12 between runs?»).

**Acceptance criteria.**

- Schema field added + validator accepts it.
- `auto_classify_seed_unsorted.py --apply` writes the field.
- Backfill pass runs cleanly across all 20 entity files; ≥95% of non-seed_unsorted coins receive a signal value (the legacy ~5% get `legacy_v1`).
- `scripts/audit_v2.py` adds a «Classification signal distribution» section.
- Build clean.

**Cross-references.**

- §BV — every new Fuß rule added under §BV must use a NAMED signal value (e.g. `era_sovereign_fod`, `era_rhinsk_gylden`) so the field stays useful.
- §BT — D38-style consistency: builders that bypass classifier (write `fuss:` directly) should also write a `classification_signal: builder_<source>` for consistency. Optional extension.
- §BX (auto_classify pipeline integration) — when classifier becomes canonical Phase 4 step in the V2 pipeline chain, this field becomes structural metadata, not optional.

**Definition of done.** Every coin entry in `data/v2/final/*.yml` carries a `classification_signal` value (or explicit `legacy_v1` for pre-V2 placements). Audit script reports the distribution. Future rule extensions automatically write the signal as they fire.

### CC. 🟢 222 Numista cache entries with no year_first — undated / ND issues investigation  *(opened 2026-05-27, user-marked «з високим пріоритетом»)* *(est: small)* *(type: audit + classification)*

**Surfaced.** First run of `scripts/parse_numista.py` (commit `fccb75c`) reports 222 of 1717 top-level Numista cache files as `unparseable_top` — both shape-detectors (api / chrome) recognise them, but the per-shape parse returns None. Investigation in this session showed the cause is **missing `year_first` / `min_year`** — i.e. the underlying coin type has no year on Numista (undated, «ND», pattern strikes, modern restrikes).

**Why this matters.** Per CLAUDE.md §9 exclusion list, project does NOT include patterns / trial strikes (case 1) or off-strike singletons (case 3). The 222 might include legitimate undated circulation coins that DO belong in our scope (Christian IV «ND» Schüsselpfennige in Holstein, etc.) — we should NOT silently drop them all.

**Plan.**
1. Walk all 222 unparseable cache files, tag by source-shape + issuer + denomination + presence/absence of «ND» / «No date» / «undated» marker in title.
2. Triage into 4 buckets:
   - **OUT-OF-SCOPE** — patterns / probe / off-strike (drop).
   - **GENUINELY UNDATED CIRCULATION** — add to seed with `year_first: None` + `year_verified: false`; render with `(?)` per CLAUDE.md §3a year-format escape hatch.
   - **DATE-INFERABLE** — title or ruler implies year range (Christian II 1513-1523, etc.); add inferred range with `year_verified: false`.
   - **NEEDS RE-HARVEST** — Numista may have date in HTML but our cache file lost it; re-harvest single coin via Chrome MCP per HARVEST_ROUTINE §5.5.
3. Extend `parse_numista_api.py` + `parse_numista_chrome.py` to handle the **GENUINELY UNDATED** case explicitly — emit canonical sidecar with year fields null + `_undated: true` marker — instead of returning None.
4. Update `build_numista_seed.py` to accept undated entries with appropriate fuss/phase defaults.

**Acceptance criteria.** Triage report committed under `docs/anomaly_log.yml` (or as a new analysis doc); per-bucket count + ID list; parser extended to handle the GENUINELY UNDATED case; re-run shows ≥80% of the 222 either landing as proper seeds (with year_verified=false) or explicit OOS-drop documented.

### CD. 🟢 Drop legacy `build_numista_pre1541_seed.py` + `parse_numista_pre1541.py` + `denmark_pre_1541/` cache subdir  *(opened 2026-05-27, user-marked «з високим пріоритетом»)* *(est: small)* *(type: refactor cleanup)*

**Surfaced.** Commit `337466d` added a deprecation guard to `build_numista_pre1541_seed.py` (the §AZ Tier 3 single-window builder), making it refuse to run without `--allow-deprecated`. The generic `build_numista_seed.py` (commit `a773c2d`) reads canonical Phase 2 sidecars including the pre_1541 subdir's output, so the legacy scripts are functionally superseded. They remain on disk for reference + git-blame traceability of the §AZ Tier 3 work, but a few more end-to-end re-runs are needed to confirm zero regression before deletion.

**Plan.**
1. Run `scripts/parse_numista.py --force` followed by `scripts/maintenance/build_numista_seed.py` on a clean checkout AND on a checkout where `denmark_pre_1541/n*.json` is moved to a temp location (then back) — confirm both runs produce byte-identical V2 seed output for the 56 pre_1541 entries.
2. Delete the three artefacts:
   - `scripts/maintenance/build_numista_pre1541_seed.py`
   - `scripts/parse_numista_pre1541.py` (Phase 2 HTML-pre1541 parser — the generic driver still reads the parsed JSON sidecars)
   - `scripts/fetch_numista_pre1541.py` (Phase 1 HTML fetcher — keep ONLY if there's evidence it caught entries not reachable via the API)
3. Decide on `scripts/cache/numista/denmark_pre_1541/n*.{html,json}`:
   - The HTML files are Phase 1 raw cache; could be migrated to top-level `scripts/cache/numista/<NID>.html` for uniformity, OR left in place as historical artefact.
   - The JSON files are Phase 2 output; the new driver already copies them through `parsed/<NID>.json` so the subdir is redundant once verified.
4. Update HARVEST_GUIDE.md / SOURCES.md references to point at the new single-pipeline path.

**Acceptance criteria.** No `pre1541` filename left under `scripts/` or `scripts/maintenance/`. The 56 pre_1541-window entries continue to land in `data/v2/seed/numista/<entity>.yml` after deletion. `git grep "pre_1541"` returns only doc-trail mentions in commit messages / DECISIONS.md.

**Cross-references.** Closes the TODO §BO.5 step 5 cleanup tail — see TODO §BO entry body for the original «OR fold into existing Numista parser» note that this scope is now fulfilling.

## Normal priority

### CT. ✅ DONE 2026-06-11 — Fuss cross-reference system — author by id, resolve display name + clickable link at build time  *(opened + closed 2026-06-11)* *(est: medium)* *(type: feature)*

**IMPLEMENTED same day.** Resolver `scripts/lib/fuss_refs.py`, wired into `build.py` at both post-render sites, migration `scripts/maintenance/migrate_fuss_xrefs.py` converted 168 refs, tests `tests/test_fuss_refs.py` (7 green). End-to-end verified: same `[fuss:reichsdukatenfuss]` marker → «Rigsdukatfod» (linked) on Denmark, «Reichsdukatenfuß» (plain) on Hamburg. Full spec + as-built notes in [`docs/fuss_cross_refs_design.md`](fuss_cross_refs_design.md).

Replace hand-written `<code>Fuss-Name</code>` cross-refs in prose with id-markers `[fuss:KEY]`. A post-render pass (new `scripts/lib/fuss_refs.py`, mirroring `refs_pool.process_html`, called at the same two build sites) substitutes the **effective display name** — honouring per-location `fuss_periods[KEY].name` overrides (the live «Reichsdukatenfuß» ↔ «Rigsdukatfod» mechanism) — and wraps it in a clickable `<a href="#fuss-KEY">` when the card is present on the page (anchors already rendered at [location.html.j2:760](../templates/location.html.j2); plain `<code>` fallback when off-page). Payoff: renaming a standard touches one `name` field and every cross-ref updates, with the right name per jurisdiction.

User decisions (2026-06-11): reference by id ✓; clickable link to card ✓. Migration (key-form `<code>KEY</code>` sweep across `fuesse.yml` + `data/v2/locations/*` + `data/locations/*`, ~dozens of occurrences: `11_333_thaler` 21×, `9_25_thaler` 18×, `8_daler_fod` 18×, `18_5_thaler` 18×, etc., plus the 2 already-converted display-name cards `Rosenobel-fod` / `Nobelfod`) is part of the build-out — see design doc §Migration + §Test plan.

### CG. 🟢 §1 nominal hygiene — `nominal` carries ONLY the denomination + its numeric quantity (strip locations / equivalents / fractions / weights / nicknames / editorial words; normalise Halv→½ + Roman→Arabic; remove medals)  *(opened 2026-05-30, scope expanded 2026-05-30)* *(est: medium-large)* *(type: data-audit + curation)*

**Surfaced.** 2026-05-30, during the Nobel-spelling normalisation work (V2_DECISIONS D43); scope expanded same day after the user reviewed the prepend-1 guard's skip-list. Two user clarifications of CLAUDE.md §1:

1. **What the coin actually IS matters.** A coin with NO inscribed nominal vs one WITH an inscribed nominal differ. If the nominal is **inscribed**, THAT inscription is the `nominal` — never an equivalent (not «1 Krone = 4 Mark»). If **not inscribed**, we may use what the source(s) provide.
2. **Master rule — nothing but the nominal itself (incl. its numeric value) may live in the `nominal` field.** No location, no editorial words, no equivalents, no fractions-of-another-standard, no weights, no nicknames, no Latin alt-names, no modern-currency. Everything else moves to `note` / the proper structured field (mint / issuing_entity / weight_rough_g / fraction / kind).

**Finding.** ~85 V2 `nominal` fields carry non-nominal content. Sub-patterns (✎ = mechanizable in the normaliser; 🔍 = needs per-coin legend verification):

- ✎ **Location-prefix leaked into nominal (33):** `Oldenburg. Taler`, `Lübeck (Bishopric). Taler`, `Bremen & Verden. 4 Mark`, `Rantzau. Ducat`, `Osnabrück. Taler`, `Wismar. Ducat`, `Lauenburg. ⅔ Taler (Zweidrittel)`, `Lower Saxony. Gutergroschen`, `Danish West India Company 2 Ducats`, even double `Oldenburg. Lübeck (Bishopric). 5 Taler (Pistole - Friederich Augustd'or)`. → strip the place prefix; the location is the issuing entity (already encoded by the entity file the coin lives in / `issuing_entity` / `mint`). Result is the bare denomination («1 Taler»). Any trailing equivalent/name tail («(Pistole…)») → `note`.
- ✎ **Halv-word instead of ½ (≈8):** `Halv ørtug`, `Halv ørtug, Vesterås (Sverige)`, `Halv Sølvgylden`, `Half Portugaloser (5 Ducats)`. → replace the fractional WORD with its numeric value: `Halv X` / `Half X` → `½ X`.
- ✎ **Roman-numeral count (≈3):** `IIII Schilling` → `4 Schilling`; `XV Skilling` → `15 Skilling`. → normalise roman → arabic.
- ✎ **Editorial prefix (3):** `Commemorative 2 Kroner` → `2 Kroner`, `Largesse 4 Ducats` → `4 Ducats`, `Largesse Ducat` → `1 Ducat`. → strip the editorial word; the «commemorative / largesse» character → `kind: gedenk` + `note`.
- ❌ **Medals — out of project scope entirely (§9 exonumia):** we only record what circulated or could have circulated as money. `grafschaft_oldenburg.yml` «Medal» (mis-tagged `kind: kurant`) → **remove the entry**. `danish_realm.yml` «Gold Medallic 2 Ducats» (`kind: gedenk`) → 🔍 review: a circulating/presentation 2-Ducat *coin* in medallic style stays (as «2 Ducats», medallic note); a true medal is removed.
- ✎ **Weight-in-parens (parser bleed — the number is grams, NOT a count):** `1 Ducat (3.5)`, `1 Goldgulden (1.5)`, `1 Goldgulden (3.25)`, `1 Crown (15.75)`, `1 Ducat (Dukat) (3.5)`. → drop from nominal (weight already in `weight_rough_g`).
- ✎ **Fraction-of-another-standard:** `1 Groschen (1/24 Thaler)`, `1 Pfennig (1/288 Thaler)`, `1 Grote (1/72 Thaler)`, `1 Hvid (1/144 Speciedaler)`, `1 Skilling (1/96 Speciedaler)`, `1 Mariengroschen (1/36 Thaler)`, `1 Schwaren (1/360 Thaler)`, `12 Pfennige (1/21 Thaler)`, `12 Grote (1/6 Thaler)`. → fraction → `note` / `fraction` field.
- ✎ **Nickname / Latin / type:** `1 Skilling (hulpenning)`, `1 Speciedaler (Prinsens Daler)`, `2 Reichsthaler (Doppeltaler)`, `6 Mark (Rejsedaler)`, `3 Skilling Lybsk (Døtgen)`, `½ Skilling (Søsling)`, `½ Penning (Skærv)`, `1 Speciedaler (Reichstaler)`, `1 Joachimsdaler (Taler)`, `1 Silver Gulden (Taler)`. → nickname → `note`.
- ✎ **Modern-currency / metric equivalence:** `1 Øre (0.01 DKK)`, `10 Øre (0.10 DKK)`, `1 Krone = 3/5 Vereinsthaler = 1/50 Metric Pound`. → equivalence → `note`.
- 🔍 **Genuine two-denomination ambiguity (which is inscribed?):** `2 Krone (8 Mark)`, `1 Kronerigsdaler (6 Mark)`, `12 Mark (Courant Ducat)`, `12 Mark = 3 Kroner`, `1 Hvid (= 4 Pennings)`, `1 Mark = 16 Skilling`, `1 Reisedaler = 6 Mark`, `12 Rigsdaler courant = 2 Rigsdaler`, `1/15 Speciedaler = 1/12 Rigsdaler Courant`. → verify the actual legend (IKMK free / danskmoent / Numista — mind the May-2026 API budget); set `nominal` = inscription, equivalent → `note`.
- 🔍 **Unknown-denomination placeholders (keep as coins, resolve nominal):** `(?)`, `Gold coin`, `Gold Issue`, `Gold Bracteate` — real coins, undetermined denomination. NOT medals; stay. Either resolve to a sourced denomination or keep the source placeholder + `verified: false`.

**Portugaløser resolution (analysed 2026-05-30).** Question raised: is «Portugaloser» just a name, or literally a nominal = 10 Ducats? **Answer: a NAMED denomination that is also value-defined = 10 Ducats** — like «Speciedaler», not merely «X Mark». Named after the Portuguese *português* (≈10 cruzados / Manuel I 1499). Our V2 family is internally coherent: 1 Portugaløser ≈ 34,5–35,2 g .979–.986 gold = **10 Dukat**; ½ ≈ 17 g = 5 Dukat; ¼ ≈ 8,66 g = 2½ Dukat; 2× ≈ 69,7 g = 20 Dukat. The fractions are ALREADY expressed *as* Portugaløser, so the coin-name is the operative denomination. Portugaløser are prestige/presentation gold whose legends carry a motto, not a value — our notes record no denomination in any Portugaløser legend, so per clarification #1 (not inscribed → source-primary) the **`nominal` = «Portugaløser»** (with quantity/fraction), and the «(10 Dukat)» / «(5 Dukat)» / «(2½ Dukat)» / «(20 Speciedaler)» value-equivalents → `note`. Two consequences:
  - **Canonicalise spelling** Portugaloser → **Portugaløser** (Danish ø — Hede/danskmoent form), same mechanism as Noble→Nobel (add to `_NOMINAL_DISPLAY_SPELLING`). Currently mixed across V2 (`Portugaloser` vs `Portugaløser`).
  - **Reorder the divergent forms** `10 Ducats (Portugaloser)` / `1 Portugaloser (10 Ducats)` / `1 Portugaløser (20 Speciedaler)` / `1 Portugaløser (= 20)` → all to `N Portugaløser` + equivalent in `note`.
  - Caveat: confirm the legend carries no denomination via IKMK/danskmoent before finalising (inferred from the prestige-gold convention + absence in our notes, not yet verified per coin).

**Already done (2026-05-30, commit `3dbdc85`):** the seed-ingest normaliser (`lib/v2_seed_writer.py::_normalise_nominal`) is head-aware — the translation-hint paren-strip removes ONLY a same-denomination language/plural variant («2 Ducats (Dukaten)» → «2 Ducats»), and KEEPS a cross-denomination equivalent («4 Mark (Krone)» stays) rather than silently deleting it. So the pipeline no longer makes the §1 decision by accident; the existing-data cleanup below is what remains.

**Note — the flagged Krone coins are already clean in V2.** The Christian V / Frederik III «4 Mark» / «1 Krone» coins (Hede 78 / 91B / 95A / 105A / 112A) carry a clean `nominal` («4 Mark», «1 Krone») in V2 final — the «(Krone)» equivalent lives in `note` prose (correct). The original «4 Mark (Krone)» flag was a false alarm for V2 (it lived in V1 `denmark.yml` + seed nominals, where V1 is frozen).

**Approach (user-chosen 2026-05-30: defer to dedicated session).** When picked up: (1) extend the normaliser with the ✎-mechanizable rules (location-prefix strip → with the place routed to `mint`/`issuing_entity`, Halv→½, Roman→arabic, editorial-prefix strip, weight/fraction/nickname/modern-equivalence → `note`, Portugaløser spelling + reorder) so existing-data cleanup AND future seeds are handled in one place; (2) remove medal exonumia entries (§9); (3) for the 🔍 two-denomination + Medallic-review + unknown-placeholder sets, verify the inscription per coin (IKMK first — free) before deciding. Respect V1-frozen (`data/locations/*.yml`) — V2 only. Cross-check against the render-time `normalise_nominal_display` so the cleanup is idempotent with the pipeline.

**Progress 2026-05-30 — stages A + B DONE (the ✎-mechanizable subset), stage C remaining (judgment / legend / note-policy):**
- **Stage A (commit `3509647`)** — lossless string rules added to `normalise_nominal_display` (render + seed-ingest) + retro-applied (83 fields / 11 files): `Halv`/`Half` → `½`, leading roman → arabic (`IIII Schilling` → `4 Schilling`), `Portugaloser` → `Portugaløser` (Danish ø).
- **Stage B (commit `2f8e4ad`)** — coin-context strips, no note prose / no legend needed (203 fields / 40 files) + medal removal: location-prefix → strip via CLOSED `_NOMINAL_LOCATION_PREFIXES` set (`Oldenburg. Taler` → `1 Taler`; the closed set deliberately spares `Gold Off-Metal.` off-strikes + `Danish West India Company.` issuers from being dropped); editorial-prefix strip (`Commemorative`/`Largesse`, character → kind=gedenk); weight-in-grams decimal paren drop (`1 Ducat (3.5)` → `1 Ducat`); modern-currency drop (`1 Øre (0.01 DKK)` → `1 Øre`). **Medal** removed per §9 (1908 Oldenburg «Medal», 3 records).
- **Stage C — REMAINING (220 nominals in V2 final), needs decisions:**
  1. ✅ **DONE (Stage C-1, commit `4eeab5b`)** — fraction-of-standard paren «1 Skilling (1/96 Speciedaler)» + nickname/alt-name paren «1 Speciedaler (Reisedaler)», «6 Pfennigs (Sechsling) (1/48 Thaler)» → `note`. User chose «усе → note, мовно-нейтральний append». New `lib.v2_seed_writer.split_nominal_annotations` + wired into `_apply_pre_write_hygiene` (future seeds) + one-shot on existing data (327 notes created language-neutral + 18 strip-only). Residual fraction/nickname in final = 0.
  2. **dual full-denomination (82)** «4 Mark = 1 Krone», «16 Skilling = 1 Mark», «2 Krone (8 Mark)», «16 Rigsbankskilling = 5 Schilling Courant» — which denomination is INSCRIBED? **Some are genuinely dual-inscribed (keep); the rest are editorial equivalents (clean).** Promoted to its own High-priority harvest task **§CI** (Chrome MCP legend verification, NOT Numista API; work-list `docs/cg_dual_denomination_verify.json`).
  3. ✅ **DONE (commit `84b3397`)** — **«Gold Medallic 2 Ducats»** (KM#460 / Hede c5h59) reviewed: a catalogued 2-Ducat presentation strike, NOT exonumia → cleaned to «2 Ducats» (kept; «Medallic» already in note). **Placeholders (11)** «(?)»/«Gold coin»/«Gold Issue»/«Gold Bracteate» — LEFT as-is: genuinely unknown denomination, per §1 the source's generic descriptor IS the source-value when nothing is inscribed.
  4. ✅ **DONE (commit `84b3397`)** — **Portugaløser «(N Ducats)» tails** reordered: nominal = «<qty> Portugaløser», ducat/speciedaler equivalent → note (both orders incl. inverse «10 Ducats (Portugaløser)»). New `portugaloser_medallic_split` wired into `_apply_pre_write_hygiene` for future seeds.

**Status: §CG closed except §CI** (the 82 dual full-denomination coins needing Chrome-MCP legend verification — its own High-priority harvest task). Stages A + B + C all landed; the seed-ingest normaliser (`_apply_pre_write_hygiene` + `normalise_nominal_display`) now produces clean nominals from every source so future harvests arrive §1-compliant.

### CH. 🟢 IKMK generic seed builder + drain the enumerated-but-unfetched backlog  *(opened 2026-05-30)* *(est: medium-large)* *(type: harvest + builder + classifier)*

**Progress 2026-05-30:** builder `build_ikmk_seed.py` landed (commit e99031f, 7th source) + hardened (commit `130ba9b`): added an **era scope gate** (drop year_first <1481 / >1914 — IKMK full-text queries pulled in medieval Denar/Örtug «MA» Gotland + post-1914 modern) and rebuilt §CG-clean (188 classified, all in-scope, 0 dirty nominals). **Also fixed a CRITICAL latent regression in `130ba9b`:** §CG-D43 removed `_BARE_DENOMINATION_NOUNS` but `_extract_mint_from_nominal` still referenced it → **every** seed builder's `_apply_pre_write_hygiene` raised NameError (surfaced only when the IKMK builder ran). Restored.

**⚠️ Propagation BLOCKED — absorb de-promotes pre-existing coins on a new-source re-merge (found + ROOT-CAUSED 2026-05-30, NOT shipped).** Re-running merger + absorb `--entity` for the 10 IKMK entities propagated 258 IKMK coins to final BUT **de-promoted 9 pre-existing coins** (danish_realm 4, danish_norway 2, royal_holstein 3 — e.g. `unified-denmark-numismaster-65634/65627/65629`). They survive in seed + seed_unified, vanished from final. **Propagation reverted.**

  **Root cause (pinpointed via trace):** absorb is **idempotent on unchanged input** (re-run royal_holstein with no seed change → 306→306, verified). The de-promotion is the **`process_entity` `surviving_finals` stale-foundation purge, Shape A/D (`absorb_seeds_into_final_v2.py` ~894-918)**: adding IKMK + re-merging changes how an existing source-seed (e.g. `denmark-numismaster-65634`) is GROUPED in seed_unified → the old `unified-<source>` foundation entry is judged stale («merged into peers») and dropped, expecting the «replacement unified host» to be re-added by the match-pair / bulk-promote pass below — but that new host **fails its D40 bulk-promote peer-check** (the IKMK coin is a new low-confidence peer) → it lands in pending, not final. Two-stage interaction: stale-purge drop + bulk-promote-skip. Affects ANY new-source re-merge, not just IKMK (general pipeline concern).

  **Fix design (monotonic absorb — for a focused, cross-entity-tested session, NOT a rushed patch — cron-critical, all-final blast radius):** track the set of source-seed-ids represented in the PRIOR final (each foundation's `source_id` + composed_of members); when the stale-purge drops a foundation, mark its source-ids as «owed»; in the bulk-promote loop, **force-promote** (sticky) any unified host whose composed_of contains an owed prior-final source-id — analogous to the existing `force_promote = uid in _assignment_ids` curator-override at line 1214. Genuine new duplicates are still consolidated by the merger (composed_of), so sticky-keeping a still-standalone host is safe. **Test gate before commit:** re-run absorb `--apply` across ALL entities with no seed change → assert zero net coin-count change (idempotency); then the IKMK propagation → assert the 9 stay + zero new duplicates. Until shipped, IKMK stays seed-only (counted in `harvest_coverage.py` §A, not on pages).

**Surfaced.** 2026-05-30, building the full-coverage inventory (`scripts/maintenance/harvest_coverage.py`, HARVEST_ROUTINE §6.5). IKMK is the only coin-specimen source with **NO V2 seed builder** — its cache is entirely uncovered by political entity. Two distinct gaps:

1. **No seed builder → 0 entity coverage.** 1 778 IKMK records are cached but none flow into `data/v2/seed/ikmk/<entity>.yml`; the §6.5 §A matrix (6 368 classified specimens across 20 entities) counts zero IKMK pieces. IKMK records expose mint **country** (`mint[].country_name_en` = Germany 1 403 / Denmark 34 / Norway 24 / …), NOT mint city — so per-entity classification needs the `division` / `sub_division` region labels (e.g. «Holstein-Schauenburg») + `literatur` (Lange/Hede tags) + per-piece mint-city research, the way the ad-hoc `enrich_sh_from_ikmk*.py` / `seed_holstein_schauenburg_from_ikmk.py` scripts did by hand. Build `parse_ikmk.py` (Phase 2 canonical sidecar) + `build_ikmk_seed.py` (Phase 3) routed through `lib/v2_seed_writer.py` like every other builder, classifying via mint-city where present + division-region fallback. Heavy OOS contamination (Poland 95 / Switzerland 54 / Czech 28 / modern post-1900 — full-text queries pull cross-references) → reuse the §6.5 country + era + year-window (1481–1914) filters as the in-scope gate.
2. **4 498 enumerated-but-unfetched.** The IKMK manifest enumerated 6 275 in-scope ids but only 1 777 have a record file — 4 498 discovered and never fetched. The hourly routine's «next 5 from manifest uncached pool» drains this slowly; a dedicated bulk-fetch pass closes it faster. (1 442 of the cached are in temporal scope 1481–1914; the unfetched likely mix in-scope + still-uncaught OOS.)

Until both close, IKMK stays «supplementary museum-catalogue enrichment» (HARVEST_ROUTINE §5.5) — useful for photo + legend cross-reference on coins already seeded from other sources, but not a counted coverage contributor. The §6.5 §C IKMK-detail block now makes the gap visible every run so it is not silently forgotten. **The user's original prompt for §6.5 was exactly this: «що було покрито старим харвестом ІКМК по шлезвіг-гольштейну» — answer: nothing is entity-classified yet; this task is the fix.**

### BY. ✅ Pre-1541 Danish silver Müntzfüße — 2 standards landed + Christian III Dalerfod Phase 0 expansion + 55 specimens promoted  *(opened 2026-05-21, closed 2026-05-21, **refactored 2026-05-21**)* *(est: medium-large)* *(type: data + classifier extension)*

**Refactor 2026-05-21:** following web-research into how numismatic literature (danskmoent.dk Galster-Hede catalogue, Wilcke 1950 7-3 p. 242 «die 1537 Karbung etabliert das 14½-Lod-Daler-Standard», Reynold Junge mintmaster continuity 1534-1540 per `jungebc.htm`), the originally-separate `christian_iii_grevens_fejde_fod` was MERGED into `8_daler_fod` as Phase 0 (de-facto-Etablierung 1534-1540). Rationale: no source treats them as separate Müntzfüße; metric anchor (14½ Lod / 8/M / 26.494 g fein) is identical between 1537 Joachimsdaler and 1541 Møntordning Daler — 1541 codifies de jure what Junge established de facto 1537. The 40 specimens previously under grevens_fejde A1/A2/A3 are now under dalerfod Phase 0. Cycle now ships 2 (not 3) new Müntzfüße + 1 phase-expansion of existing dalerfod.

**Closed 2026-05-21.** 3-Müntzfuß implementation cycle complete in three atomic commits:

- ✅ **`8_5_gylden_fod`** (commit `49f2922`, §BY/1) — Sølvgylden-Skilling-Hvid triad 1514-1523. 3 phases (A1 Haandfæstning + Lovkompleks baseline, A2 Klipping debasement, A3 final consolidation). 3 specimens promoted: galster-c2g-38 + bruun-3931 + bruun-3933. New classifier rule «sølvgylden»/«solvgylden»/«silver gulden» year_max=1523.
- ✅ **`8_gylden_fod`** (commit `0480880`, §BY/2) — Møntordning af 25. Februar 1524, 8 Sølvgylden/M @ 14 Lod (vs Christian II 8.5/M) + Lybsk-aligned 24-ß-Mark subdivision + 14-Penning Klipping-Indfrielse-Mønt (separate act 26 Feb 1524). 2 phases (A1 1524-1531, A2 1532 final consolidation). 12 specimens promoted: 4× galster-f1g Sølvgylden 1531-1532 + bruun-4075 ¼ Silver Gulden 1532 + 7× «14 Penning» 1524 specimens. New classifier rules: «sølvgylden» year_min=1524 year_max=1533, «14 penning» year_min=1523 year_max=1533.
- ✅ **`christian_iii_grevens_fejde_fod`** (commit `017f344`, §BY/3) — civil-war cascade 1534-1540 with 9+ fineness variants per Wilcke 7-3 p. 242 «Master Mårtens regnskabsbøger». 3 phases (A1 Klippe cascade Aarhus+Roskilde+Stockholm+Ribe 1534-1536, A2 Joachimsdaler 1537 Copenhagen, A3 pre-Møntordning transition 1538-1540). Main anchor: Joachimsdaler 1537 at 14½ Lod (metrically identical to 1541 Møntordning — Christian III's first heavy-Daler attempt). 40 specimens promoted: 3× Joachimsdaler 1537 Bruun + 1× ½ Joachimsdaler + multi-mint Klippe + Skilling cascade. New classifier function `_classify_via_grevens_fejde_anchor` (year-range + ruler + entity + metal pattern).

**Deferred to future SH-page cycle:** `frederik_i_husum_fod` (Schleswig-Holstein ducal-zone, 1514-1533) — per user 2026-05-21 «досліди цей стандарт теж, для майбутнього огляду для шлез-гольшт земель». Foundation research already captured at `docs/research/sh_ducal_zone_husum_1514.md` (Husum 1514 Bestalling + Wendischer Münzverein genealogy + 1474 Kaiser Friedrich III imperial privilege). Implementation when SH-page expansion cycle starts.

**Project impact:**
- 3 new Müntzfüße in `data/shared/fuesse.yml`
- 3 new fuss_periods + phases blocks in `data/v2/locations/denmark.yml`
- 3 new timeline.bars (positions 12, 13, 14)
- 4 new classifier rules + 1 new era-anchor function
- **55 specimens promoted out of seed_unsorted** (target was 60-80 — actual landed slightly below because Sølvgylden patterns split across two Fuß via year_max/year_min, and some pre-1534 Galster Skilling/Hvid specimens still need additional period-specific patterns)
- Pre-1541 silver gap closes for Danish-realm-entity scope
- Foundation laid for §AZ paper-source import to deepen specimen coverage incrementally

**Remaining seed_unsorted with pre-1541 silver/billon profile:** ~36 specimens (91 inventory - 55 promoted). Most are pre-1523 Christian II + Frederik I Skilling/Hvid that don't carry "Sølvgylden" denomination text and need additional rules (Skilling year_max=1523 → Lovkompleks, Skilling 1524-1533 → 8-Gylden-Fod, etc.) — straightforward follow-up but deferred to keep §BY commits focused on Sølvgylden/Joachimsdaler/Klippe hauptkurant tiers.

Original §BY planning preserved below for reference:

---

### BY-planning (preserved for historical reference)


**Surfaced.** User question 2026-05-21 «якою була срібна стопа в данії до 1541 року?» exposed a known coverage gap: the §BV cycle (closed same day) added eight pre-1582 Fuß slots but only on the gold side; the silver side 1514-1540 still has NO project-defined Müntzfuß. 91 silver/billon specimens currently sit in `seed_unsorted` because the classifier has no metric target to land them under.

User verdict: «так, роби, знайдену інформацію помісти в docs».

**Research COMPLETE** — captured in three companion dossiers:

- `docs/research/wilcke_1514_1541_specs.md` §1-§4 — full ordinance-level specs from Wilcke 1950 (Christian II 1514 Lovkompleks pp. 150-156, Frederik I 25 Feb 1524 ordinance pp. 184-187, Husum ducal-zone p. 186, Grevens Fejde 1534-39 p. 242)
- `docs/research/denmark_pre_1541_source_survey.md` — per-source coverage matrix (Wilcke + Bruun + Galster + Numista + Jensen-Skjoldager)
- `docs/research/pre_1541_silver_seed_inventory.md` — **new 2026-05-21**, current-state snapshot: 91 seed_unsorted specimens grouped + classifier behaviour + §BF roadmap mapping

**Scope — 4 new Müntzfüße to define (per `wilcke_1514_1541_specs.md` §8 roadmap):**

| ID (proposed) | Period | Anchor | Specimens in scope |
|---|---|---|---:|
| `8_5_gylden_fod` | 1514-1523 | Møntordning Sommer 1514 (Dines Blicher Brev Malmö) + Norge 3 Aug 1514 + Sjælland åbent Brev 24 Aug 1515 | 21 |
| `8_gylden_fod` | 1524-1531 | 25 Februar 1524 royal ordinance (Wilcke 7-2 p. 184-187) | 28 |
| `frederik_i_husum_fod` | 1514-1533 | Husum + Gottorp ducal-zone (mintmaster Jørgen Drewes) | ~6-10 |
| `christian_iii_grevens_fejde_fod` | 1534-1540 | Master Mårtens regnskab (Wilcke 7-3 p. 242) — civil-war cascade | 41 |

Metric anchors fully documented in the existing dossier — no further primary-source research needed before implementation.

**Implementation sub-tasks (§BV-style cycle):**

1. **Define 4 Müntzfüße in `data/shared/fuesse.yml`** with full `grundwerte` + `fractions` + `events` + DE/EN/UK descriptions. Per §BD, all four IDs use the Danish `-fod` convention from day one. Per §0z, descriptions stay reader-voice (historical fact, not project-meta). Per §BB, prose is historical framing only — no parameter bleed.

2. **Add 4 entries to `data/v2/locations/denmark.yml`** under fuss_order + timeline.bars + fuss_periods + phases. Sequencing decisions:
   - `8_5_gylden_fod` ends 1523 → preceeds Frederik I (1523-1533) chronologically; place after `nobel_fod` / `goldgulden_fod` in silver group.
   - `8_gylden_fod` follows `8_5_gylden_fod` (chronological).
   - `frederik_i_husum_fod` is the SEED of the later Flensborg-fod lineage — list adjacent to `8_daler_lybsk_fod`.
   - `christian_iii_grevens_fejde_fod` immediately precedes `8_daler_fod`.
   - Update `timeline.bars[].order` sequence accordingly (currently 0..18; will become 0..22 after insertion of 4 new bars).

3. **Add 4 denomination-anchor rules to `scripts/maintenance/auto_classify_seed_unsorted.py`** (`_DENOMINATION_ANCHOR_RULES` table). Per §BV's proven pattern — denomination + optional year-gate. Suggested rules:
   - «Sølvgylden» (any form: 1, ¼, ½, 1½) + `year_max: 1523` → `8_5_gylden_fod`
   - «Sølvgylden» + `year_min: 1524, year_max: 1533` → `8_gylden_fod`
   - «14 Penning» / «14 Penny» + `year_max: 1533` → `8_gylden_fod` (the Wilcke 7-2 p. 187 «14 %» small-change subtype)
   - «Mark lybsk» / «4 ß lybsk» / «Husumdaler» + mint in {Husum, Gottorp} → `frederik_i_husum_fod`
   - «Joachimstaler» / «Joachimsdaler» + year 1537 → `christian_iii_grevens_fejde_fod` (Christian III's first heavy-Daler issue)
   - «2 Mark Klippe» / «4 Skilling Klippe» + year 1535-1539 + mint in {Aarhus, Roskilde, Ribe, Stockholm} → `christian_iii_grevens_fejde_fod`

4. **Add bibliography refs to `data/locations/denmark-references.yml`** as needed — ref29 (Wilcke 1950) already covers most; expect ref41-ref44 for ordinance-specific citations (1514 Sommer-ordinance text, 25 Feb 1524 royal ordinance text, Husum 1514 spec, Grevens Fejde Mårtens regnskab).

5. **Run `auto_classify_seed_unsorted.py --entity danish_realm --apply`** — expected to promote ≈ 60-80 specimens out of seed_unsorted (the remainder will be FUSS_OK_PHASE_GAP or genuinely off-pattern Klippe/civil-war variants needing manual placement).

6. **Build + validate + commit** in atomic-task batches (per CLAUDE.md commit-cadence rule — one Fuß per commit, classifier rule update its own commit, specimen promotion its own commit).

**Cross-references:**

- **§BV** (closed 2026-05-21) — 8-Fuß gold cycle that proved the implementation pattern. §BY reuses the same shape (denomination_anchor rules + surgical apply path + verbatim source quotes in `verification_note: false` + `_curation_holds` for any manual edits).
- **§BF** (closed 2026-05-20) — Christian III 1541 `8_daler_fod`. §BY is «what comes chronologically before» §BF; the 1540→1541 fineness transition (.875 → .906) is a natural cross-Fuß boundary.
- **§AZ** (long-running, paper-source-blocked) — Galster + Jensen-Skjoldager promotion that would land the c3h21-c3h22 Flensborg specimens + earlier Frederik I royal-mint paper-only specimens. §BY can proceed WITHOUT waiting for §AZ — the existing Galster cache + Bruun lots already cover 91 specimens; §AZ would deepen coverage incrementally.
- **§BD** (Danish-jurisdiction Fuß names) — all 4 new IDs adopt the `-fod` convention from day one (`*_lovkompleks_fod`, `*_dalerfod`, `*_husum_fod`, `*_grevens_fejde_fod`).

**Acceptance criteria (per §BV pattern):**

- 4 `fuesse.yml` entries land with full structural blocks + sourced metric annotations.
- 4 `denmark.yml` timeline.bars + fuss_periods + phases land.
- 4 denomination-anchor rules added to classifier; dry-run shows ≥ 60 new auto-promotions.
- `python scripts/build.py --validate-only` clean; rendered Denmark DE/EN/UK pages show 4 new Fuß cards.
- §BY closure commits push the ahead-of-origin count.

**Definition of done.** Pre-1541 silver gap closes; the 91 seed_unsorted specimens are either promoted to one of the 4 new Müntzfüße or explicitly noted as FUSS_OK_PHASE_GAP / off-pattern (with reason). The §AZ paper-source import becomes a coverage-deepening task, not a blocker.

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

### BX. 🟢 Integrate auto_classify_seed_unsorted.py as canonical Phase 4 step in V2 pipeline  *(opened 2026-05-20, substantially closed 2026-05-21)* *(est: small-medium)* *(type: pipeline + docs)*

**Progress 2026-05-21 — wrapper + canonical docs landed.** Core integration done:
- `scripts/run_v2_pipeline.sh` (new) chains Phase 3.2 → 4 absorb → 4 classify → 6 relink → build in canonical order. Dry-run by default; `--apply` mutates. `--skip-build` for data-only runs.
- `docs/ARCHITECTURE.md` §«Phase 4 — Classification to Müntzfuß (final)» rewritten to describe the actual two-stage process (`absorb_seeds_into_final_v2.py` + `auto_classify_seed_unsorted.py`) and reference the wrapper. «to-be-built» annotation dropped for `merge_seeds_cross_source.py` (already existed) + `classify_to_fuss_v2.py` (was the placeholder name for `auto_classify_seed_unsorted.py`).
- ARCHITECTURE.md pipeline diagram + script-inventory chain (post-harvest re-run section) updated to name the wrapper.

**Remaining (optional polish, not blocking):**
- PB-12 playbook entry «Post-harvest V2 pipeline re-run» — operator-facing procedure for `run_v2_pipeline.sh` usage scenarios (after new harvest cache, after curator decision file edits, before push verification). Low priority — wrapper's `--help` covers basic usage.
- Pre-commit hook advisory check — flag staged `data/v2/final/*.yml` changes that introduce new `fuss: seed_unsorted` entries the classifier would auto-resolve. Decision (a) in original plan; deferred — workflow needs to prove the manual approach is error-prone first.



**Surfaced.** User direction 2026-05-20: «цей процес має бути складовою частиною нашого пайплайну даних на v2 (уже основній версії)». The §8a auto-classifier (`scripts/maintenance/auto_classify_seed_unsorted.py`) currently sits in the `scripts/maintenance/` ad-hoc tier and is invoked manually. Per `docs/ARCHITECTURE.md` §«Phase 4 — Classification to Müntzfuß (final)» (line 541), a script with this exact responsibility is documented as **`classify_to_fuss_v2.py` (to-be-built)** — the existing `auto_classify_seed_unsorted.py` IS that script under a different name, just not yet canonicalised in the pipeline orchestration.

**Why this matters.** After every new harvest cycle (Phase 1 → 2 → 3.1 → 3.2 → 4 absorb → render), the classifier should run as a canonical step so newly-absorbed entries with `fuss: seed_unsorted` get classified BEFORE the build assembles + renders. Without canonical integration, the operator (today: a Claude session) has to remember to run it; «forgot to run classify» causes silent regression to seed_unsorted-bucket bloat.

**Plan.**

1. **Decide naming**: keep `auto_classify_seed_unsorted.py` (clearer name about its actual job) OR rename to `classify_to_fuss_v2.py` (match ARCHITECTURE.md spec). Recommend: **keep current name** + update ARCHITECTURE.md to drop the «to-be-built» annotation and point to the actual script.
2. **Canonicalise in script-inventory chain** in `docs/ARCHITECTURE.md` line 569-577 («Script inventory + when to re-run each»): replace the «classify_to_fuss_v2.py» placeholder with `auto_classify_seed_unsorted.py --apply` as step 4 of the post-harvest chain.
3. **Document the run-order dependency** explicitly in `docs/V2_PIPELINE.md`: classifier runs AFTER absorb (`absorb_seeds_into_final_v2.py`) — operates on `data/v2/final/<entity>.yml`. It mutates fuss + phase in place, idempotent on re-runs (seed_unsorted shrinks monotonically).
4. **Auto-trigger options** (pick one):
   - (a) Add to the pre-commit hook — runs `--dry-run` on staged changes, errors if it detects new seed_unsorted entries that would be auto-classified. Curator must run `--apply` manually before commit lands. Pro: forces awareness. Con: slow pre-commit.
   - (b) Add to a `run_v2_pipeline.sh` wrapper script that chains all phase scripts in correct order (seed_v2_regroup → merge_seeds_cross_source → absorb → auto_classify → relink_promoted). Pro: single command. Con: operator still has to invoke the wrapper.
   - (c) Document in `docs/PLAYBOOKS.md` as a recurrent-procedure entry (PB-N «Post-harvest V2 pipeline re-run») without code automation. Pro: lowest infra cost. Con: relies on operator memory.
   - **Recommend (b) + (c)**: wrapper script for one-command convenience + playbook for documentation.
5. **Coupled with §BW** (classification_signal persistence): once §BW lands, the canonical pipeline write of `classification_signal` is part of the auto-classify step. The integration must include this field, not just fuss/phase.

**Acceptance criteria.**

- ARCHITECTURE.md §«Phase 4 classification» updated: drop «to-be-built» note, name the actual script.
- ARCHITECTURE.md script-inventory chain includes `auto_classify_seed_unsorted.py --apply` as canonical Phase 4 step.
- V2_PIPELINE.md updated with explicit run-order specification.
- `scripts/run_v2_pipeline.sh` (or equivalent wrapper) chains the full Phase 3.1 → 3.2 → absorb → classify → relink sequence.
- `docs/PLAYBOOKS.md` entry «Post-harvest V2 pipeline re-run» documents the wrapper invocation + when to use it (after harvest brings new cache files, after curator edits decision files, before build verification).
- Pre-commit hook MAYBE checks for unclassified seed_unsorted in staged data/v2/final/ changes (advisory) — decision (a) deferred until the workflow proves the manual approach is error-prone.

**Cross-references.**

- §BV (pre-1582 Müntzfüße) — each new Fuß landing requires a corresponding rule in this classifier; the pipeline integration formalises «classifier-extension-then-run».
- §BW (classification_signal persistence) — must be coupled with the canonical pipeline write to remain useful.
- §BT (D38-style builder consistency) — builders that write fuss directly (legacy) bypass the classifier; the pipeline should converge on classifier-as-single-source-of-truth.
- `docs/ARCHITECTURE.md` §«Phase 4 — Classification to Müntzfuß (final)» — the documented spec the current script already implements.
- `docs/V2_PIPELINE.md` §«Detailed execution plan» Phase 4 — needs update to reference the canonical script name.

**Definition of done.** Operator runs `scripts/run_v2_pipeline.sh` (or equivalent) after harvest cycles; classifier runs in canonical order; ARCHITECTURE.md + V2_PIPELINE.md + PLAYBOOKS.md cross-reference the actual script name; no «to-be-built» annotations remain.

### CF. 🔵 No-mint Schauenburg Ernst III. cluster — 184-entry tradition audit pending Lange/Behrens/Weinmeister page-by-page  *(opened 2026-05-27, user-asked «наступною задачею»)* *(est: large — many sessions)* *(type: deep audit + manual research)*

**Surfaced.** Same tradition audit as §CE. After the §CE migration, the largest residual classification ambiguity in the Schauenburg lineage is the **184 Ernst III. (1601-1622) entries that lack mint attribution** in our cache (mostly IKMK Berlin bulk-seed). These currently sit in `holstein_schauenburg_county.yml` as bulk `seed_unsorted` per the original §0b14f71 (2026-05-08) split decision, but the audit revealed that without mint-info we genuinely cannot tell whether each entry belongs in SH-tradition (Schilling Holsteinisch + ½ / ¼ Reichsthaler from Altona) or Niedersachsen-tradition (Doppelschilling + 1/16 / 1/24 Thaler from Oldendorf/Rinteln).

**Breakdown by denomination** (184 entries):

| Denom | n | Tradition signal needed |
|---|---|---|
| Schilling (60) | 60 | Distinguish SH «Schilling Lübisch» vs NS «Doppelschilling Niedersachsen» — needs weight + fineness + iconography (Wendischer Münzverein vs Lower Saxon imagery) |
| Pfennig (18) | 18 | Niedersachsen-leaning by default but Ernst III. also minted Pfennig at Altona |
| Reichsthaler-Multi (17) | 17 | Two-Thaler / Three-Thaler — both systems struck them |
| Reichsthaler (13) | 13 | Mint-disambiguating; weight + fineness Δ analysis |
| ½ Reichsthaler (13) | 13 | Same |
| 1/16 Reichsthaler (7) | 7 | Same |
| Fürstengroschen (5) | 5 | Niedersachsen-specific |
| Ducat (5) | 5 | Trade gold — both systems |
| 1/24 Reichsthaler (3) | 3 | Niedersachsen-only by definition (already part of §CE if any are wrongly in `schauenburg_pinneberg`) |
| Groschen (3) | 3 | Niedersachsen-leaning |
| ¼ Reichsthaler (2) | 2 | Both systems |
| Goldgulden (2) | 2 | Both |
| unmatched (43) | 43 | Mixed — needs prose inspection |

**Plan.**
1. **Phase 1 — automated weight-clustering** (small effort): for each denomination group, cluster the per-entry weights and check whether the distribution is bimodal. Bimodal clusters likely indicate two parallel mints/systems; unimodal suggests one. Reichsthaler weight Δ vs SH Soll (28.07g fein @ 9¼-Fuß) vs NS Soll (29.23g brutto @ 14 Lod) might separate cleanly.
2. **Phase 2 — primary-source verification** (large effort, many sessions): walk through Lange 1908/1912 + Behrens 1905 + Weinmeister 1908 + Bei der Wieden 1961 systematically. Each entry's IKMK photo can be matched against catalogue iconography descriptions. For the 60-Schilling cluster, Wendischer Münzverein vs Niedersachsen iconography is the key discriminator (Madonna vs imperial eagle / regional shield arrangement).
3. **Phase 3 — apply curator verdicts**: for each entry that can be confidently classified, move to the appropriate entity + fuss. For unresolvable cases, document under `data/v2/match_uncertainty/holstein_schauenburg_county.yml` + leave as seed_unsorted with annotated reason.

**Acceptance criteria.** Phase 1 weight-cluster analysis committed as a `docs/research/schauenburg_ernst_iii_clustering.md` document. Phases 2-3 ship per-batch (10-20 entries per session) with per-entry curator verdicts in commit messages. By completion, every Ernst III. entry either lives in its correct entity bucket OR is documented as unresolvable with a specific source-research request open against it.

**Cross-references.** §CE (the immediate-cleanup precursor — clean obvious cases first). §BV / §BY (pre-1622 Müntzfuß scoping — Ernst III. period overlaps Reichsmünzordnung + early Kipper era). `docs/research/schauenburg_pinneberg_economic_zone.md` (new doc to be created).

---

### CG. 🟢 Make `classify_mint_to_entity` issuer-aware (KM-register / denomination / ruler), not bare mint-location  *(opened 2026-06-15)* *(est: medium)* *(type: pipeline + decision)* *(do BEFORE seed-builders become authoritative / Phase 9 promotion)*

**Problem.** `scripts/lib/v2_entity_classify.py::classify_mint_to_entity(mint, year)` maps a coin to a political entity from the **mint location alone**. That is the wrong criterion (curator decision 2026-06-15): a mint indicates the issuing entity / circulation **only when the issuer owned that mint**. Two failure modes proven in the data:
- **Crown mints served multiple realms.** Altona was the royal *Danish* mint in Holstein and struck *Danish-realm* coinage (Rigsbankskilling, Skilling Dansk, Speciedaler, Frederiks D'or, …). Of 29 Altona/Glückstadt-struck `danish_realm` coins, **28 carry only the Danish (KM-DK) register + Danish denominations** — Danish issues, not Holstein. Bare-mint classification would wrongly tag them `royal_holstein`.
- **Commission strikes / changing ownership.** Pre-1640 Altona belonged to Schaumburg-Pinneberg; Ernst-III-von-Schaumburg coins struck there are `schauenburg_pinneberg` (issuer), not `royal_holstein`. The 1848 Provisional Government and the Plön duke also struck at "royal Holstein" mints but are their own issuers.

**Correct criterion** = issuer (ruler / legend) + circulation, with the **issuer-owns-mint guard**. Practical signals: **KM register** (KM-SH = Krause «German States — Schleswig-Holstein» volume → royal_holstein; KM-DK = Denmark volume → danish_realm), **denomination** (Holstein-Courant «Schilling Sch.-H. Courant» → duchies; Danish Rigsdaler/Speciedaler/Skilling Dansk → realm), **ruler**. The crown mint-realm union (`royal_holstein` for a Holstein-only strike; `[danish_realm, royal_holstein]` if struck at Copenhagen too — since royal_holstein ⊂ danish_realm politically) applies ONLY to crown coins.

**Where it bites.** The RENDER layer is already correct — `build.py::_derive_issuing_entity` + `_CROWN_MINT_REALM` (commit bd9126b) recompute issuing_entity per page from the crown mint-realm union, scoped to `issuing_entity==danish_realm` (the guard). But `classify_mint_to_entity` (used by the seed-builders `v2_seed_writer` + `build_*_seed.py` and the merger `merge_seeds_cross_source.py`) still encodes bare-mint logic → when the seed-builders are re-run / promoted to authoritative, it would misclassify Altona-struck Danish *seeds* into `royal_holstein` buckets.

**Fix.** Make `classify_mint_to_entity` issuer-aware — give it access to the coin's catalog (KM register) + nominal + ruler (change signature to take the coin/record, or add a sibling `classify_coin_to_entity`), reusing the `_CROWN_MINT_REALM` + issuer-owns-mint logic. Audit all callers (seed-writer, merger, the `scripts/maintenance/build_*_seed.py` builders). **Dry-run the seed-bucket reclassification** (how many seeds move) before applying.

**Gate / why deferred.** Not blocking anything now (V1 is the verification anchor; seeds are not yet authoritative). Do it **before** the seed-builders are made authoritative (Phase 9 promotion), so the bucket classification is issuer-correct from the start. Reference: the render-layer precedent (bd9126b) + the criterion analysis (handoff 2026-06-15).

---

## Low priority

### CU. 🔵 Year-union should downweight reign-window placeholder members  *(opened 2026-06-15)* *(est: medium)* *(type: pipeline-rule + regression-test)*

**Context.** `_enrich_final_entry` (absorb) derives a final's displayed year via `_union_year_ranges(members)` — a blind union of every composed member's `year_ranges`. When a member carries a loose full-reign span, the union widens the displayed minting year past what the coin was actually struck. Surfaced by the 2026-06-15 curation-loss field-diff gate (`scripts/maintenance/audit_curation_loss.py`): the ONLY 2 absorb-stage losses project-wide were both this pattern —

- `unified-dk-bruun-3839` (1 Rhinsk Gylden, Hans): member `galster-hg-27` = 1481-1513 (`year_verified=false`, the `fbc926c` reign-window anchor) widened the curated 1497.
- `km-795-1-chr-ix-1874` (10 Øre, Christian IX): the widener is the KMM specimen `kmk-279179` = 1863-1906 (`year_verified=None`, full Chr.IX reign), which merged into the `c9h16a` cluster (the Hede seed itself gives discrete 1874-1891). Earlier mis-attributed to `hede-c9h16a`; §0b-corrected 2026-06-17. Would back-date decimal coinage struck only from 1874.

**Stopgap shipped (commit cebf090).** Both protected per-case via `_curation_holds` + the year-hold semantics changed from union-preserve to OVERRIDE (a frozen year is now authoritative; member ranges no longer widen it). This fixes the 2 known cases and is the right behaviour for `_curation_holds`, but it requires a curator to NOTICE and FREEZE each case by hand.

**✅ MECHANISM SHIPPED — curator-mute (`year_demote`), 2026-06-17.** Chosen the SAFE curator-explicit path over risky auto-detection. A new `year_demote: [{member_id, reason}]` list in `merge_decisions/<entity>.yml` names reign-window placeholder members; `process_entity` stamps `_year_demoted` on the matching seeds (via `_expand_member`), and `_union_year_ranges` (refactored to a `_collect()` helper + two-pass) holds them to a **last-resort pass** — their span never widens the union, but their years are NOT deleted (used only if no non-muted member attests any year). `build_unified` propagates `_year_demoted` to a wholly-muted unified entry (e.g. `unified-dk-numista-355730`) so the absorb-level union demotes it too. Precedence: muted = below a normal member, above no-data. 5 unit tests in `tests/test_union_year_ranges.py`; light-integration verified the 3 culprits resolve (bruun-3839 cluster → 1496, c9h16a → 1874-1905, numista-355730 stays 1481-1513 + demoted). The 3 culprits are declared in `merge_decisions/danish_realm.yml`. **Why curator-mute, not auto-detect:** the pollution signatures differ (`galster-hg-27` v=false vs `kmk-279179`/`numista-355730` v=None full-reign span), so `year_verified` is not a clean discriminator and auto-detecting «span == ruler's full reign» (via `lib.ruler_reigns.reign_window`) risks false positives on coins genuinely struck across a reign. Auto-SUGGEST (flag candidates for curator review, never auto-apply) stays an optional future enhancement.

**✅ MATERIALISED via the 2026-06-17 coordinated re-flow** (commits `68fae2f` merge + `968af94` absorb). bruun-3839 → 1496-1497, km-795 → 1874-1905 discrete, c9h16a → 1874-1905; the per-case `_curation_holds` on bruun-3839 + km-795 + c7h13a were retired (the mute + §CW resolve them natively). **Extended to a NEW class — ND-swallow:** the re-flow's curation-loss gate caught 4 coins where an UNDATED Bruun specimen's broad «ND (1670-99)»-type range (year_verified=False) was swallowing the dated discrete years of its merged cluster (dk-bruun-10497/10501/10509 in danish_norway, dk-bruun-14741 in gottorp_duchy). Same `year_demote` mechanism applied → they resolve to the dated peers' years (10497 → 1673,1675,1679; 14741 → 1531). The reign-window AND undated-specimen-broad-range cases are both the same loose-span-vs-discrete pollution; year_demote covers both. **✅ Edge case RESOLVED at the root (2026-06-17, commits `8571258` fix+tests / `58bc460` data).** The c7h13a missing-1798 was NOT a union bug but a Hede-seed-builder one: `_build_year_fields` collapsed a consecutive year run (13C «1798, 1799») into a loose `year_first/year_last` span (it emitted `year_ranges` only when gaps existed, `len(ranges)>1`), which the merger could displace under the cluster's [1795,1801] discrete envelope, dropping the only attestation of 1798 (1799 survived via 13D's independent singleton). Fix: emit ONE singleton `[y,y]` per attested year whenever `len(yrs)>1` so the merger classifies Hede years DISCRETE; `_format_year_label` folds them back to «1795-1799, 1801» for display. Materialised via re-seed hede (3 entities, year-only diff) → re-merge → re-absorb (curation-loss gate REAL-LOSS=0, 4 benign year-add). Bonus: three other unified labels self-corrected (nf3h69 1649-1668 → discrete gaps revealed; c5h126a/c5h107 1693-1696 → 1693-1694,1696; c8h3a 1840-1848 → discrete) — the now-discrete Hede years let the merger displace masking ucoin/Numista loose spans, so the page stops asserting un-struck in-between years (§3a/§4). Tests: `TestHedeDiscreteYearEnumeration` + `TestC7H13ASpeciedalerInteriorYear` in `tests/test_union_year_ranges.py` (58 green). Rendered + verified on denmark + schleswig_holstein de/en/uk.

**Done-when.** After the coordinated re-flow: bruun-3839 renders 1496-1497, km-795 renders 1874-1905, BOTH without `_curation_holds` (the `year_demote` mute is the sole mechanism); `audit_curation_loss.py --losses-only` reports `widen=0`; no other entity's displayed year changes.

### CV. 🔵 Generalise `_home_entity` to a CONFIGURED jurisdiction-overlap set (NOT consumes-map-blind)  *(opened 2026-06-16, design corrected 2026-06-16)* *(est: medium)* *(type: pipeline-rule)*

**Context.** A coin's `issuing_entity` may be a list (joint mint = circulation in several political entities — e.g. Altona+Kopenhagen → `[danish_realm, royal_holstein]`). The VALUE keeps the full set; the HOME FILE (`data/v2/seed|final/<entity>.yml`) must be the entity whose consuming-page set covers the others', so the file-based Pass-1 assembly surfaces the coin on every page that shows any of its entities (invariant, curator 2026-06-16: «кожна фінальна сторінка має містити всі монети, у яких є entities, показані на цій сторінці»). A joint coin homed to a non-overlap member (e.g. `danish_realm.yml`, alphabetical default `d < r`) reaches the SH page only via the fragile Pass-2 issuing_entity intersection, and only while the joint VALUE survives the merger (first-member) + absorb (foundation-immutable) pipeline.

**Stopgap shipped (2026-06-16).** `_home_entity` (v2_seed_writer.py) hardcodes `royal_holstein`-priority: `if "royal_holstein" in ie → royal_holstein`. Covers the immediate Danish-crown Altona+Kopenhagen case. Fires only on list-form `issuing_entity`.

**⚠ DESIGN CORRECTED 2026-06-16 — do NOT use a consumes-map-blind «any 2-page entity = overlap» rule.** «Consumed by 2+ pages» has TWO distinct causes, and only one of them wants overlap-home:
  - **Jurisdiction-overlap** — `royal_holstein` (⊂ `danish_realm` politically; consumed by `schleswig_holstein` + `denmark`). Coins here are genuinely JOINT (`[danish_realm, royal_holstein]`). Overlap-home is correct: home to `royal_holstein` → both pages via Pass 1.
  - **Tradition-split** — `schauenburg_pinneberg` (the Holstein half of the Schauenburg principality; consumed by `holstein_schauenburg` + `schleswig_holstein`). Coins here are SCALAR — assigned to ONE monetary tradition by `entity_routing_rules.yml::schauenburg_niedersaechsisch_denoms` (denomination/monetary-system: Mariengroschen/Fürstengroschen/Arendschilling → `grafschaft_schaumburg`; SH-Courant/imperial-1/24 or Altona-mint → `schauenburg_pinneberg`). Verified 2026-06-16: **0 list-form coins involve schauenburg/grafschaft** — so `_home_entity` (list-only) never touches them. A consumes-map-blind rule would (a) be moot here today, AND (b) WRONGLY home a hypothetical future joint `[grafschaft_schaumburg, schauenburg_pinneberg]` coin to `pinneberg` → push a possibly-Niedersächsisch coin onto the SH page. So this entity must be EXCLUDED from overlap-home.

**The fix.** `_home_entity` reads a small CONFIGURED set of genuine jurisdiction-overlap entities — `{royal_holstein}` now; a new entity is added only when it is a true subset-overlap (the overlap entity politically ⊂ the others, like royal_holstein ⊂ danish_realm). For a list-form `issuing_entity`, if it contains a member of that set, home there; else alphabetical. **Tradition-split entities (`schauenburg_pinneberg`) are deliberately NOT in the set** — their coins are scalar (assigned by the denomination routing-rule, §CE) and already render on both consuming pages via Pass 1; their multi-page consumption is NOT a jurisdiction-overlap. This is strictly safer than the consumes-map-blind approach and CANNOT move the already-split Schauenburg coins (they are scalar; the rule fires only on list-form).

**Done-when.** `_home_entity` keys off a documented jurisdiction-overlap set (extensible, but each entry justified as a subset-overlap); `schauenburg_pinneberg` and other tradition-split entities are excluded with an inline note; a scan finds 0 list-form coins with a jurisdiction-overlap member homed to a non-overlap file (seed + final); 0 Schauenburg coins moved. The Schauenburg tradition-split (entity-assignment by denomination) stays entirely in `entity_routing_rules.yml`, untouched by `_home_entity`.

### CW. 🔵 Merger over-merges a trade-coin (Albertsdaler) into the same-nominal domestic Speciedaler (Hede 13)  *(opened 2026-06-16)* *(est: medium)* *(type: pipeline-rule + data-correction)*

**Context.** `unified-dk-hede-c7h13a` (royal_holstein) is a **2+2 conflation of two distinct types** struck by Christian VII at Altona, both nominal-classed «1 Speciedaler», silver:
  - **Hede 13** — the domestic Speciedaler. danskmoent `c7h13.htm` (verified 2026-06-16): «1 speciedaler», København + Altona, years **1795, 1796, 1797, 1798, 1799, 1801**, sub-vars A-D, **NO KM, NO Davenport** (Schou + Sieg only). Members `dk-hede-c7h13a` + `dk-hede-c7h13b`.
  - **Albertsdaler** (trade coinage) — Numista N#131730 «1 Albertsdaler Trade coinage», **KM 640, Dav EC III 1310**, `years_text` **1781-1796**; NumisMaster MC_145357 carries **KM 640.2, Dav 1310**, 1796. Members `dk-numista-131730` + `denmark-numismaster-145357`. The Albertustaler is a distinct export trade-crown (hence the Davenport «European Crowns» number); a domestic Speciedaler is never in Davenport.

**Root cause.** The cross-source merger matched all four on the **primary signals** nominal + ruler + mint + metal («1 Speciedaler» · Christian VII · Altona · silver). It has **no discriminator for trade-coin-vs-domestic** of the same nominal, so the Albertsdaler folded into the Hede 13 cluster, dragging its `km 640/640.2` + `dav EC III 1310` + the 1781-1796 range onto a domestic-Speciedaler entry.
*§0b correction.* An earlier session hypothesis blamed a «KM-640 cross-register collision». **Wrong** — `dk-hede-c7h13a` has **no KM at all**; the match fired on primary signals, and BOTH Albertsdaler members (not the Hede ones) carry the KM 640 / Dav 1310. The KM only *appears* in the unified output because the merger accumulated it from the Albertsdaler members.

**Current masking (symptom, not root).** The final `unified-dk-hede-c7h13a` was hand-fixed this session to hold `year_label = 1795, 1797, 1799, 1801` (Hede years) — which strips the Albertsdaler range from the *rendered* year column, but the over-merge persists: `composed_of` still lists both Albertsdaler members, and the final still carries `km: {sh: [..., 640, 640.2]}` + `dav: EC III 1310` folded in from them.

**Discrete-years sub-finding (the trigger question) — see §CX.** N#131730's live Numista page shows discrete strike-years 1781, 1784, 1786 (Poppenbüttel), 1796; our cache `scripts/cache/numista/131730.json` (harvested 2026-05-18, `chrome_mcp_html`, pre-dating the `year_list` extractor `d4d1ca8` 2026-05-22) holds only `min_year/max_year/years_text = 1781-1796` — no `year_list` — so we render a range. **This is NOT a one-off miss:** the 2026-06-10 «501-entry» year_list re-harvest covered danish_norway + 5 German entities but NOT the Danish-crown track — royal_holstein (102 range-only-no-list / 154 NIDs), danish_realm (248/516), gottorp_duchy (55/93) were entirely out of scope. 131730 is one of ~400+ ungapped Danish-crown numista entries → tracked as §CX. For c7h13a specifically it's also **moot until the over-merge is split**: re-harvesting discrete Albertsdaler dates would just put more trade-coin dates on the wrong (domestic) entry. Fix the over-merge first; the discrete years then land on the split-out Albertsdaler entry via §CX.

**The fix.** (1) Split the two Albertsdaler members (`dk-numista-131730` + `denmark-numismaster-145357`) out of the Hede 13 cluster into their own unified entry — via a merger non-merge decision (`match_uncertainty/` or an explicit exclusion in `merge_decisions/`), keyed on the type difference (Davenport-presence / «trade coinage» / KM-640-Denmark). (2) Re-flow merger → absorb for royal_holstein so c7h13a sheds `dav EC III 1310` + `km 640/640.2` and the Albertsdaler renders as its own coin (its proper Hede number is a c7 Albertustaler entry, NOT 13). (3) Then the per-case year-hold on c7h13a becomes unnecessary. **Generalise:** consider Davenport-number presence (or KM «trade coinage» tag) as a merge **discriminator** — a Davenport-catalogued trade crown and a non-Davenport domestic coin of the same nominal+ruler+mint are different types. May catch other trade-coin/domestic over-merges (Piastre, Albertustaler, Guinea trade coinage).

**Done-when.** The Albertsdaler is a separate unified entry from Hede 13; `unified-dk-hede-c7h13a` no longer carries `dav EC III 1310` or `km 640/640.2`; the Albertsdaler renders with its own years (1781-1796, ideally discrete after a 131730 re-harvest); the session's manual year-hold on c7h13a is redundant; no other royal_holstein cluster changes. Belongs with the parked coordinated merger/absorb re-flow.

### CX. 🟡 Numista `year_list` re-harvest never reached the Danish-crown track (royal_holstein / danish_realm / gottorp …)  *(opened 2026-06-16)* *(est: medium — Chrome-MCP harvest + re-flow)* *(type: harvest-backfill)*

**Context.** The discrete-strike-year machinery exists and works: extractor `d4d1ca8` (2026-05-22) reads Numista's `table.collection` → `year_list`; the «501-entry» re-harvest (`b4d0552` / `5d812df` / `012fb9e`, 2026-06-10) gained discretes on 417/501 (84 confirmed range-only); a standing Priority-0 backfill queue (`docs/handoff_numista_year_list_reharvest.yml`) drains the tail (now `pending: []`, 67/92 processed). SOURCES §13.1 + §13.2 document the Chrome-MCP same-origin `fetch()` harvest (no API quota — logged-in session).

**The gap.** That re-harvest's scope was **danish_norway + 5 German entities**; the **Danish-crown / Schleswig-Holstein track was never covered.** Measured 2026-06-16 (range-only numista entries with NO `year_list`, i.e. we render a continuous range that may falsely assert un-struck in-between years per §3a/§4):
  - `royal_holstein` — **102** of 154 NIDs · 0 re-harvested
  - `danish_realm` — **248** of 516 NIDs · 1 re-harvested
  - `gottorp_duchy` — **55** of 93 NIDs · 0 re-harvested
  - (control: `danish_norway` — only 4 of 365, 90 already have `year_list` ✅ covered)
  - plus likely tails in sonderburg/glucksburg/norburg_plon/rantzau/schauenburg — to be measured.
~**400+ ungapped Danish-crown entries** total. At the 501-set's ~83 % discrete-gain rate, most would gain real discrete years; the rest confirm range-only.

**The trigger.** N#131730 (Albertsdaler, §CW) is one of the 102 royal_holstein cases — its cache (2026-05-18) predates the extractor and was never re-touched. The user correctly recalled the discrete-year work existed; it simply never ran on this entity track.

**The fix.** Build the candidate NID list (range-only-no-`year_list` numista NIDs across the Danish-crown entities), append to `docs/handoff_numista_year_list_reharvest.yml::pending`, and let the harvest routine drain it as Priority 0 (Chrome-MCP `fetch()` + DOMParser, ≈30 NIDs/JS-call per §13.2) — OR run a focused batch directly. Then re-seed (`build_numista_seed`) → merger (`_union_year_ranges` already prefers discretes) → absorb to materialise. NO API quota cost (Chrome session). Batches naturally with the parked coordinated re-flow.

**✅ HARVEST DONE (2026-06-16).** Collected 456 candidate NIDs (range-only-no-`year_list`), queued, and drained in-session via Chrome MCP same-origin fetch (logged-in, 0.35s pacing, **0 errors**): **218 gained discrete `year_list`** from `table.collection`, 238 confirmed range-only. Caches patched in place (year_list + min/max, other fields preserved) and committed in the submodule (`2758b6d41`); queue drained (`pending: []`). **REMAINING — materialisation only:** re-seed `build_numista_seed` → re-merge → re-absorb so the discrete labels reach the rendered finals. NOT done in-session because the numista seed regen bundles the same intervening builder/cache drift as Bruun (`4465c1b`/`e8de501`/`41efdf0` Aagaard→others, etc.) — belongs in the coordinated re-flow. **The durable km-str-repr (form #2) fix that was the prerequisite is now DONE (commit `441b285`)** — `_merge_km_field` no longer str()s a list-valued register, and `normalise_catalog` heals any residual on every absorb; re-absorb royal_holstein verified 0 str-repr. So the re-flow no longer needs per-entity km hand-patching (it had corrupted c7h13a + km-696 every run during §CW).

**✅ MATERIALISED via the 2026-06-17 coordinated re-flow.** The raw-cache→parsed-sidecar gap was the missing link: build_numista_seed reads `numista/parsed/<NID>.json`, so the 218 discretes (in the raw cache from §CX) had to be backfilled into the parsed sidecars first (220 sidecars, submodule `c18232a7d`). Then re-seed (`3486bf0`) → merge (`68fae2f`) → absorb (`968af94`) carried them through: e.g. Albertsdaler c7h22ab → 1781,1784,1786,1796; 5567 → 14 discrete years. Rendered (year column splits `year_label` by comma). §CX closed.

**Done-when.** The Danish-crown numista entities' range-only-no-`year_list` count drops to the genuine range-only residual (mirroring danish_norway's 4/365); discrete `year_list`s are in cache + seed; after a re-flow the gapped year labels render (e.g. «1781, 1784, 1786, 1796» instead of «1781-1796») on the correctly-split entries (§CW first for 131730). Cross-ref §CW.

## Done

### CE. ✅ Schauenburg NS-tradition migration + «1/24 Thaler» rule correction  *(opened 2026-05-27, closed 2026-05-29)* *(est: small)* *(type: data-audit + curator-fix + rule correction)*

**Closed 2026-05-29.** The original §CE premise («1/24 Thaler is Niedersächsisch-only, 9 entries to migrate») was DISPROVEN during execution. NumisMaster reverse-legend inspection showed the 1/24 Thaler is the **Imperial Gutegroschen** of the 24-Groschen-per-Reichsthaler reckoning — «24» mark on the imperial orb + crowned imperial eagle + reigning-emperor name (Rudolf II on the Schaumburg-Pinneberg pieces). It is a Reichsmünzordnung-standard denomination struck empire-wide on BOTH the Pinneberg (Altona, SH side) and Schaumburg-county (Niedersachsen) sides — NOT a Mariengroschen-system signal. Only Mariengroschen (36/Thaler) + Fürstengroschen + Arendschilling are reliable NS-exclusive denominations.

**Delivered:**
- **Routing-rule correction** (`data/v2/entity_routing_rules.yml`): removed `1/24 thaler` + `1/21 thaler` from the `schauenburg_niedersaechsisch_denoms` rule's `denomination_any`. Documented the Gutegroschen rationale inline. The rule now fires only on genuine NS-exclusive denoms.
- **Net migration outcome:** only the genuine Mariengroschen entries route to `holstein_schauenburg_county` (96072 + 96073 auto-migrated by rule; km-135 hand-moved — see below). The 1/24 Thaler entries place by mint: 6 Altona-mint pieces correctly STAY in `schauenburg_pinneberg` (SH side); 3 no-mint NumisMaster 1/24 Thaler (171189/96084/96088) remain where the NumisMaster builder placed them (HSC) — deferred to §CF as genuine no-mint ambiguity, NOT forced.
- **km-135** (V1-foundation, 4 Mariengroschen Oldendorf 1624): the sole foundation entity-invariant case (mint=Oldendorf→HSC + Mariengroschen=NS, both signals agree). Hand-moved from `final/schauenburg_pinneberg.yml` → `final/holstein_schauenburg_county.yml`; `fuss: 9_25_thaler → seed_unsorted` (Mariengroschen has no SH-Fuß), dropped the spurious `fraction: 1/12` artefact, `issuing_entity → holstein_schauenburg_county`, `phase: II`. Added new HSC `seed_unsorted/II` phase (Just Herman + Otto V, 1622-1640) to host it.
- **Tests:** `test_24_thaler_no_longer_ns_signal` (1/24 Thaler passthrough) + updated 2 OR-coupling tests to use Mariengroschen. All 10 pass.
- **audit_v2 I7** dropped 13 → 0 informational conflicts (the 1/24-Thaler-Altona false flags are gone). Build + validate clean. km-135 renders on HSC page, removed from SH page.

**Key correction recorded** (§0b discipline): a hypothesis-as-fact slipped into the original §CE/§CF TODO bodies («1/24 Thaler does NOT exist in SH 9¼-Fuß subdivisions; Niedersächsisch-only»). The Gutegroschen finding corrects it. The reliable NS-tradition denomination set is Mariengroschen / Fürstengroschen / Arendschilling — NOT 1/24 Thaler.

**Cross-references.** §CF (no-mint Schauenburg cluster) inherits the 3 no-mint 1/24 Thaler + the broader no-mint SP-vs-HSC ambiguity. The §CF body's «1/24 Thaler» row should be re-read with the Gutegroschen correction in mind.

### CB. ✅ «Schleswig and Holstein, Danish duchies of» issuer → royal_holstein (flat) — 6 _unclassified Numista entries resolved  *(opened 2026-05-27, closed 2026-05-29)* *(est: small-medium → actual small)* *(type: classifier extension)*

**Closed 2026-05-29.** Resolution turned out SIMPLER than the original year-axis plan. The TODO draft assumed «Danish duchies» spans multiple entities by year (gottorp pre-1559 / royal mid / gesamtstaat post-1773). Twin-evidence investigation disproved this:

every «Danish duchies» coin with a findable same-type V2 twin lands in **royal_holstein**, regardless of year (1545-1787):
  - km-82-chr-iv-1640 (2 Schilling Reuterpfennig 1640)
  - hede-c7h45 (2 Sechsling 1787)
  - hede-c5h121 + sieg-137 (4 Marck / 1 Krone 1671)
  - numismaster mb-48 (1 Thaler Christian III 1545)
  - numismaster mb-62 (1 Pfennig Schüsselpfennig Friedrich II 1559)

**Why flat (no year-axis).** Numista distinguishes THREE issuer strings — «Schleswig-Holstein-Gottorp, Duchy of» (→ gottorp_duchy, the sovereign Gottorp dukes' own coinage), «Holstein-Schaumburg-Pinneberg, County of» (→ schauenburg), and «Schleswig and Holstein, Danish duchies of» (the Danish KING's ducal portion = royal Holstein). The third is unambiguously the royal/Danish line across the whole period. Control-based classification (per issuing_entities.yml): SH territory under Danish control = royal_holstein, all eras. The deprecated `gesamtstaat` is a term-only retirement — coins classify by territorial control, and post-1773 unified SH (Altona-struck) = royal_holstein. User confirmed 2026-05-29: «це ж лише термін депрекейтед, самі монети визначені за локацією — Ш-Г під контролем данії значить роял гольштейн».

**Delivered.** `_ISSUER_REGISTRY` in `scripts/lib/mint_registry.py`: 3 issuer-string variants None → royal_holstein, with full twin-evidence + 3-era rationale in the comment block. Test `test_danish_duchies_issuer_to_royal_holstein` added. All 6 entries now land in royal_holstein after the standard pipeline cascade — 4 standalone, 2 (468485 1 Thaler 1545 + 31895 2 Sechsling 1787) cross-source MERGED into their existing Hede twins (unified-dk-hede-c3h16 + unified-dk-hede-c7h45), consolidating Numista catalog refs without duplicate rows. `_unclassified.yml` Numista bucket now empty. The 2 «no mint» entries 153125/301237 from the original list got mint-classified separately (Malmo→danish_realm, Husum→royal_holstein) once mints were read.

**Decision recorded:** year-axis NOT added to issuer classification — no current issuer genuinely varies entity by year (verified across all registry entries). Will add the mechanism (paralleling mint_registry's entity_for_canon_year) only when a real year-varying issuer appears, with real bands + test coverage. Avoids speculative generality.

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

  1. **`8_daler_fod` Müntzfuß** in `data/shared/fuesse.yml` — canonical metric mf 8.827 / Cölln. Mark 233.856 g / per-Daler 26.494 g fein / fineness 0.906. **NOT YET DONE** — separate normal-priority TODO.
  2. **`fuss_periods.8_daler_fod`** in `data/locations/denmark.yml` with phases A1 (1541-1543 København baseline) + A2 (1544-1555 København debased). **NOT YET DONE**.
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
