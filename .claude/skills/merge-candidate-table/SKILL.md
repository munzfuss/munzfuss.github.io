---
name: merge-candidate-table
description: >-
  Build a field-by-field comparison table between a coin RECORD under
  examination and its merge CANDIDATE(s), for reviewing a proposed merge BEFORE
  executing it. Clearly separates the record (📍) from the candidate(s) (🎯),
  marks every field match / missing / conflict, names the KEY catalogue
  identifier that justifies (or refutes) the merge per §9.4, and lists source
  links for both sides. Use when deciding whether a seed_unsorted /
  under-documented coin is the same as an existing final, or when comparing any
  two coin records before a merge — the read-only evidence step that feeds a
  curator verdict, then hands off to `v2-merge-coins` for execution. Also
  invoke it PROACTIVELY, without being asked, whenever you are about to ask the
  curator to approve or reject a merge — including merges you did not propose:
  pairs a re-flow auto-merged, a `v2-merge-coins graph` «NO shared base»
  warning, a `verify_reflow` fold or COIN GONE that turns out to be a new union,
  a suspected over-merge before a split. Trigger
  phrases: "порівняй ці монети", "побудуй таблицю порівняння", "таблиця
  мердж-кандидатів", "record vs merge-candidate", "compare coin records", "is
  this the same coin as", "дай таблицю по цих записах".
---

# merge-candidate-table — record vs merge-candidate comparison

**READ-ONLY.** This skill produces a comparison table + links for the curator to
review a proposed merge. It never edits data. Execution is `v2-merge-coins`
(same-entity / cross-entity merge_decisions); this is the evidence that precedes
that verdict. Read CLAUDE.md §9.4 (index-graph: same coin iff a catalogue base
unifies), §9a (multi-specimen), §0z (reader roles — this table is role-2, for the
user) first.

## When to use

- **Any question to the curator of the form «merge or not».** The table is the
  required FORM of that question, not a reference produced on request. If you
  are about to write «approve this merge?» / «злити чи розвести?», build the
  table first — a hand-rolled summary skips Step 0 (`no_merges`), the link
  check and the 📍/🎯 split (2026-10-05: two re-flow auto-merges were put to
  the curator as an ad-hoc table and had to be redone through this skill).
- A re-flow produced a union no `merge_decisions` entry covers — `trace_coin`
  shows a seed in another class, or an entity's coin count dropped.
- `merge_helper.py graph` warned «NO shared base» — the curator sees the table
  before any decision is written.
- A suspected over-merge before a split — same table, different verdict.
- A `seed_unsorted` or under-documented coin might be the same as an existing
  classified final → show the evidence before merging.
- The user asks «is X the same coin as Y?» / «порівняй ці записи».
- Any pre-merge review where the curator needs to SEE, field by field, what
  matches and what doesn't — especially when the §9.4 graph-gate warns «no shared
  base» and the call rests on a specific catalogue key.

## When NOT to use

- The merge is already approved and only needs executing → go straight to
  `v2-merge-coins`.
- The catalogue key is unambiguous (the same full KM / Hede / Schou index on
  every member) and the merge is automatic, with no question to the curator —
  there is nothing to show.
- De-duplicating specimens of one already-merged type (§9a thinning, surplus
  weights from one source) — that is not a «same coin or not» question.
- A bulk audit of dozens of pairs → `v2-audit` / `merge_helper.py scan`. The
  table is for the pairs that have reached a verdict, not for the sweep.

## The two roles — NEVER blur them

Every coin in the table is exactly one of:

- **📍 RECORD** — the coin under examination (the one you're deciding the fate
  of). Usually a `seed_unsorted` / sparse source record (a lone KMM object, a
  bare Numista type, an un-classified galster/bruun seed).
- **🎯 CANDIDATE** — an EXISTING classified final you're proposing to merge the
  record INTO. It is the richer, already-placed coin.

Mark them with the 📍 / 🎯 glyphs in the header row AND in the links block. If a
reader can't tell in one second which coin is being judged and which is the
target, the table has failed its job. When there are several candidates, give
each its own 🎯 column (or its own table).

## Step 0 — check `no_merges` BEFORE building the table (MANDATORY)

A standing curator `no_merges` outranks anything this table concludes. Presenting
a merge the curator has ALREADY forbidden, without saying so, invites an approval
given on incomplete information — the approval is then void, and the merger
refuses the decision anyway.

```bash
.venv/bin/python - <<'EOF'
import yaml
ENT, GRP = "<entity>", {...}          # every id you are about to compare
d = yaml.safe_load(open(f"data/v2/merge_decisions/{ENT}.yml")) or {}
for e in d.get("no_merges") or []:
    m = set(e.get("members") or [])
    if m & GRP:
        print("NO_MERGE:", sorted(m), "\n   ", (e.get("reason") or "").strip()[:200])
EOF
```

Also check `_cross_entity.yml` when the ids span buckets. Scope the filter to the
WHOLE candidate set, not just the pair in focus — a pair-only query undercounts
(2026-07-31: reported 9 prohibitions where the cluster held 12).

If a hit comes back, the table MUST carry it: state the prohibition, its date and
commit, and quote its recorded reason. Then judge whether the evidence you found
actually contradicts it, and say which. Two outcomes are legitimate — «the
prohibition stands, no merge», or «the prohibition rests on X and the evidence
says Y, so it is worth revoking» — and both are the curator's call, not yours.
Watch in particular for a prohibition BROADER than the verdict it cites: one
recorded ruling about one pair, generalised by an implementer into a wall of
pairs, is exactly the shape that hides an unexamined case (real: the 1747 1-Dukat
cluster, `de3b86d` — 12 no_merges from a verdict about one of them).

## Step 1 — gather the data (both sides), from the SOURCE, verbatim (§0b)

**Record (📍)** — open the actual source, don't trust the rendered seed:
- KMM (`kmk-NNNNNN`): `scripts/cache/kmk/<id>.json` → `authority`, `nominal`
  (verbatim — «2 Ungarsk gylden» / «Dobbelt …»), `typeNumber` (the Schou/Hede
  tag), `creationEvents[].yearFrom`, `materials`, `measurements`,
  `drawingExists`, `objectIdentification`.
- Numista / NumisMaster / danskmoent: the parsed cache or the page itself.
- The V2 seed carries the normalised nominal + catalog — use it for the
  project-side view, but cite the cache for the verbatim.

**Candidate (🎯)** — the existing final's structured fields:
```
python3 -c "import yaml; d=yaml.safe_load(open('data/v2/final/<entity>.yml'));
[print(c.get('id'), c.get('nominal'), c.get('ruler'), c.get('year_label'),
 c.get('mint'), c.get('catalog'), [s.get('url') for s in (c.get('sources') or [])])
 for c in d['coins'] if c.get('id')=='<candidate-id>']"
```
Pull: `nominal`, `ruler`, `year_label`, `mint`, `catalog` (hede / schou / sieg /
km / fr — list-form), `fineness`, `weight_rough_g`, and every `sources[].url`.

Confirm the record's home entity + the candidate's entity — if they differ, the
merge is **cross-entity** (`_cross_entity.yml`), flag it in the verdict line.

## Step 2 — the table

One row per comparison field; two value columns (📍 record, 🎯 candidate); a
match column. Standard field order (drop rows that are empty on BOTH sides):

| Поле | 📍 ЗАПИС `<record-id>` (<source>) | 🎯 КАНДИДАТ `<cand-id>` (<type>) | збіг |
|---|---|---|---|
| Номінал | verbatim record nominal | candidate nominal | ✅/⬜/❌ |
| Правитель | ruler | ruler | … |
| **Каталог-ключ** (Schou / Hede / KM) | the record's index | the candidate's index | ✅ **← the load-bearing row** |
| Рік | year or «— нема» | year_label | … |
| Мінт | mint or — | mint | … |
| Вага / проба | weight / fineness or — | weight / fineness | … |
| Інші індекси (Hede/Sieg/KM/Fr) | — (record poorer) | full list | … |

**Match markers:**
- **✅ match** — the two values agree. Reserve **bold + a «← ключ» note** for the
  ONE catalogue index that *uniquely identifies the type* (Schou N, KM N, Hede
  N) — that row is why the merge is legitimate (§9.4). A shared Schou/KM/Hede
  base is the merge's backbone; nominal + ruler alone are NOT (that's the
  over-merge trap).
- **⬜ missing** — present on one side, blank on the other. This is NOT a
  disqualifier: it just means the record is poorer (typical for sparse KMM
  stubs). State «запис без року / лише Schou» in the note — it explains WHY the
  merge still holds (the record is a thin attestation of the same type).
- **❌ conflict** — both sides carry the field and they genuinely disagree on a
  *verified* value (different KM base that no catalogue unifies, different metal,
  fineness off > ~2 %). One real ❌ on a load-bearing field KILLS the merge — it
  means distinct types (§9.4) or a different coin. Surface it, don't bury it.

Sub-index nuance (§9.4): a value INSIDE a range/list counts as ✅, not ❌ —
«Schou 3» ∈ «Schou 3-4» (Hede 8B) or ∈ a candidate's `schou: [3, 7, 10-11]` is a
match on the sub-variant, not a conflict. Say so («3 ∈ …; Hede 8B = Schou 3-4»).

Close the table with a one-line verdict: what the load-bearing match is, why the
⬜ rows don't disqualify, whether it's same-entity or cross-entity, and what the
merge ADDS (usually: the KMM/Numista specimen + its citation, §9a).

## Step 3 — the links block (record vs candidate, explicitly separated)

Always two clearly-labelled groups. Give the record its own source; give the
candidate ALL its source URLs (danskmoent Hede page, Bruun PDF, NumisMaster,
Numista) — those let the user open both and eyeball the coins.

```
🔗 Запис (📍): [KMM 137159](https://samlinger.natmus.dk/KMM/object/137159)
🔗 Кандидат 🎯 `km-46` (Hede 18): [danskmoent c4h18](https://www.danskmoent.dk/chr/c4h18.htm) ·
   [Bruun Part I, lot 1020](<pdf-url>) · [NumisMaster MC_65617](https://numismaster.com/MC_65617)
```

URL patterns: KMM `samlinger.natmus.dk/KMM/object/<id>` · danskmoent Hede
`danskmoent.dk/chr/c4hNN.htm` (Chr IV) / `/fr/…` (F.II/III) / `/norge/…` (NO) ·
Numista `en.numista.com/<nid>` · NumisMaster `numismaster.com/MC_<n>`.

**Link the coin's PAGE, and check it first.** The page is the default and the
preferred form: it carries the image AND everything around it — legends, year
list, sub-variants, weight, the catalogue references — which a bare image URL
strips away. The curator is judging a coin, not looking at a picture.

A direct image URL is a **supplement, never a replacement**: add it beside the
page when the page is slow, image-poor, or buries the relevant specimen among
several. Sources for one: danskmoent's Zincksamlingen GIFs (grep the cached page
for `IMG SRC`, e.g. `danskmoent.dk/zinck/zinck7/7z218f5h9.gif`) and Numista's
`obverse.picture` / `reverse.picture` in `scripts/cache/numista/<nid>.json`.

A page that loads but shows no image still fails the visual job, so say so rather
than let the curator discover it. Known state (2026-07-31): **numismaster.com is
dead** — it answers nothing, so its data can only be quoted from our cache and it
must never be offered as something to look at. **KMM** frequently lists `.tif`
assets in the JSON while the object page serves none. **ucoin** pages often carry
no photo. When every page for a side is image-less, that is not a link problem —
it is a blocked verdict, and the honest move is to record the coin as deferred
with the reason, not to hand over links that cannot settle anything.

Verify before sending, and mark the result:

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}b\n" \
     -L --max-time 15 -A "Mozilla/5.0" "<url>"
```

A `403` from Numista/ucoin and a `455` from danskmoent are bot filters, not
breakage — those pages open fine in a browser (danskmoent returns 200 once real
browser headers are sent). A `000` is genuinely dead. Label each link ✅ verified
/ 🟡 blocks curl but works in a browser / ❌ dead, so the curator knows what to
expect instead of discovering it by clicking.

## Worked example (the one the user approved, 2026-07-13)

📍 `kmk-137159` (KMM, «2 Ungarsk gylden», Schou 2, Chr IV, no year/weight) vs
🎯 `km-46` (Hede 18 = 2 Ungersk Gylden 1608, København, Schou 2, Sieg 141, KM 46,
Fr 36, .972, 6.98 g):

| Поле | 📍 kmk-137159 | 🎯 km-46 (Hede 18) | збіг |
|---|---|---|---|
| Номінал | 2 Ungarsk gylden («Dobbelt») | 2 Ungersk Gylden | ✅ |
| Правитель | Christian IV | Christian IV | ✅ |
| **Schou** | **2** | **2** | ✅ **← унікальний ключ** |
| Рік | — нема | 1608 | ⬜ запис без року |
| Мінт | — | København | ⬜ |
| Вага / проба | — / — | 6,94-6,98 g / .972 | ⬜ |
| Hede / Sieg / KM / Fr | — (лише Schou) | 18 / 141 / 46 / 36 | ⬜ |

Verdict: no ❌; the load-bearing **Schou 2** uniquely = the 2-Ungersk 1608 (Hede
18); the ⬜ rows just mean the KMM record is a thin attestation. Same-entity
(danish_realm). Merge adds the KMM specimen (§9a). → hand off to `v2-merge-coins`.

## Hard rules

- **Query `no_merges` (Step 0) before the table is written, never after.** A
  table that omits a standing prohibition invites an approval the curator would
  not have given, and the merger refuses the resulting decision anyway. Scope the
  query to the whole candidate set, not the pair in focus.
- **Link the coin's PAGE — it carries the image plus the surrounding data a bare
  image URL strips.** A direct image URL supplements the page, never replaces it.
  State each link's verified status; numismaster.com is dead, KMM often serves no
  image, ucoin frequently has none. When no page for a side shows the coin, that
  is a blocked verdict — record it as deferred, don't hand over useless links.
- 📍 vs 🎯 must be unambiguous in the header AND the links. Never present a
  candidate as if it were a source of the record (a comparison peer ≠ a source).
- The verdict rests on a **load-bearing catalogue key** (§9.4), never on
  nominal+ruler+year alone — call that key out in bold.
- ⬜ (missing on the sparse side) never disqualifies; only a real ❌ on a verified
  field does. Don't let a poorer record read as a mismatch.
- Cite the SOURCE verbatim for the record (§0b) — open the cache/page, don't
  paraphrase the normalised seed.
- This skill STOPS at the table + verdict. It does not merge. Route execution to
  `v2-merge-coins` (and note same-entity vs cross-entity there).
