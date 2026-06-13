# Fuss cross-reference system — design + implementation

> **Status: IMPLEMENTED 2026-06-11** (commit lands same day). Tracked
> as `docs/TODO.md` §CT (closed). Decisions taken with the user:
> reference fusses by **stable id**, resolve the display name at build
> time (honouring per-location name overrides), and render the result
> as a **clickable link** to the fuss card.
>
> **As built** (matches this spec):
> - Resolver: [`scripts/lib/fuss_refs.py`](../scripts/lib/fuss_refs.py)
>   (`process_html(html, lang, name_map)`).
> - Wired into [`scripts/build.py`](../scripts/build.py) at both
>   post-render sites (per-location after the refs_pool pass; landing
>   with global names + new `fuesse` param).
> - Migration: [`scripts/maintenance/migrate_fuss_xrefs.py`](../scripts/maintenance/migrate_fuss_xrefs.py)
>   — converted 168 hand-written cross-refs (all `<code>KEY</code>`
>   key-forms + the two display-name cards) to `[fuss:KEY]` across
>   `fuesse.yml` + V1/V2 location yamls.
> - Tests: [`tests/test_fuss_refs.py`](../tests/test_fuss_refs.py) (7,
>   all green). Verified end-to-end in the render: Denmark shows
>   «Rigsdukatfod» (override, linked), Hamburg «Reichsdukatenfuß»
>   (global, plain) — same `[fuss:reichsdukatenfuss]` marker.
>
> The text below is the original spec, retained as the reference.

## Problem

Reader-facing prose currently hard-codes the display name of a
cross-referenced Müntzfuß inside a `<code>…</code>` span:

```yaml
# data/shared/fuesse.yml  (nobel_fod description)
… <b>Nicht</b> verwandt mit der <code>Rosenobel-fod</code>-Linie …
```

Three problems with the hand-written name:

1. **Renames don't propagate.** We will keep renaming standards
   (user, 2026-06-11: «ми ще точно будемо змінювати назви стоп»). Each
   rename means hunting every prose occurrence by hand — and missing
   one silently desyncs the artefact.
2. **The name is location-dependent, but the prose is shared.** The
   *same* standard renders under different names per location — e.g.
   the global `reichsdukatenfuss` card is «Reichsdukatenfuß», but on
   the Denmark page a `fuss_periods` override displays it as
   «Rigsdukatfod» (the Danish Rigs-/Riks- syntactic form). A shared
   `fuesse.yml` description that hard-codes one name is wrong on the
   other jurisdiction's page.
3. **Snake_case keys leak to the reader.** The earlier convention put
   the raw id in the span (`<code>rosenobel_fod</code>`). The
   underscore reads as a code identifier — a §0z role-3 violation (the
   end-reader should never see internal keys).

## Goal

Author writes **only the id**; the build substitutes the
contextually-correct display name and wraps it in a link to the card:

```yaml
… <b>Nicht</b> verwandt mit der [fuss:rosenobel_fod]-Linie …
```

renders (on the page where that card is present) as:

```html
… <b>Nicht</b> verwandt mit der
  <a class="fuss-xref" href="#fuss-rosenobel_fod">Rosenobel-fod</a>-Linie …
```

(Render note, 2026-06-12: the fuss name is an ordinary text link — NOT
`<code>`-styled. The name is a proper noun, not an identifier; monospace
read as out-of-place. Off-page refs render as the bare name; only the raw
key in the UNKNOWN-FUSS placeholder keeps `<code>`.)

Renaming the standard = edit one `name` field (global card or location
override); every cross-ref updates automatically, with the right name
per page.

## Existing infrastructure to reuse

Three pieces already exist — the feature is mostly wiring them together.

1. **Per-location name override — already live.**
   `FussPeriod.name: I18nText | None` ([schema.py:337](../scripts/lib/schema.py))
   overrides `Fuss.name` on a given location page. In use today, e.g.
   `data/v2/locations/denmark.yml::fuss_periods.reichsdukatenfuss.name
   = {de/en/uk: Rigsdukatfod}`. The resolver must consult this override
   layered over the global `fuesse[key].name`.

2. **Post-render resolver precedent — `refs_pool` (§5b).** Prose markers
   `<sup>[ref:KEY]</sup>` are resolved *after* Jinja render by
   `scripts/lib/refs_pool.py::process_html(html, lang, pool)`, called at
   exactly two sites: per-location page ([build.py:1351](../scripts/build.py))
   and landing ([build.py:1450](../scripts/build.py)). The fuss resolver
   mirrors this shape exactly. (Post-render, not a Jinja filter, because
   prose is injected into the template as a `| safe` *value*, not as a
   sub-template — so `{{…}}` inside prose is not interpreted. A literal
   `[fuss:KEY]` passes untouched through Jinja to the post-render pass.)

3. **Fuss card anchors — already rendered.**
   [location.html.j2:760](../templates/location.html.j2) emits
   `<section class="fuss-block fuss-{{ sg.fuss.id }}" id="fuss-{{ sg.fuss.id }}">`.
   So the link target `#fuss-<KEY>` already exists on the page — **but
   only when that fuss is present on the current location.** This is the
   defining constraint of the clickable variant (see §«Link vs plain»).

## Marker syntax

```
[fuss:KEY]
```

- `KEY` = the fuss id exactly as in `fuesse.yml` top-level keys
  (`rosenobel_fod`, `nobel_fod`, `9_25_thaler`, `11_333_thaler`,
  `8_daler_fod`, `18_5_thaler`, `royal_holstein`, …).
- Regex: `\[fuss:([0-9A-Za-z_]+)\]`. Underscores and digits are part of
  keys; the class must include both. No hyphen in keys today, but
  including `-` is harmless future-proofing.
- Chosen for consistency with the proven `[ref:KEY]` inline-refs marker.
- The author never writes `<code>`, never writes the name — the
  resolver emits both.

## Resolver — new `scripts/lib/fuss_refs.py`

Self-contained, pure, testable — same discipline as `refs_pool.py`.

### Signature

```python
def process_html(html: str, lang: str, name_map: dict[str, str]) -> str:
    """Resolve [fuss:KEY] markers in rendered HTML.

    name_map: {fuss_key: effective_display_name_for_THIS_page_and_lang}
              — already language-resolved and override-resolved by the
              caller (build.py). Keys absent from the map fall through
              to a visible placeholder.

    Links to #fuss-KEY when that anchor is present in `html` (i.e. the
    card is rendered on this page); otherwise renders plain <code>name</code>.
    """
```

### Algorithm

1. **Collect present anchors** from the page (self-contained, no extra
   plumbing): `present = set(re.findall(r'id="fuss-([0-9A-Za-z_-]+)"', html))`.
2. **Substitute** each `[fuss:KEY]`:
   - `name = name_map.get(KEY)`.
   - If `name is None` → **visible red placeholder** (per §0, never
     silent): `<b style="color:#c00">[UNKNOWN FUSS: <code>KEY</code>]</b>`.
   - Else `inner = f'<code>{name}</code>'`.
   - If `KEY in present` → `f'<a class="fuss-xref" href="#fuss-{KEY}">{inner}</a>'`.
   - Else → `inner` (plain `<code>`, no dead link — see §«Link vs plain»).
3. Return rewritten html. (No biblio injection — unlike refs_pool, there
   is nothing to append.)

### `name_map` construction — in `build.py` (the one piece of plumbing)

The resolver needs the *effective* name per page; that data is not in
the HTML, so build.py computes it and passes it in.

**Per-location page** (near the existing refs_pool call at ~1351):

```python
# fuss_periods overrides for THIS location, layered over global names.
overrides = { … }   # location.fuss_periods: {key: FussPeriod}
name_map = {}
for key, fuss in fuesse.items():
    fp = overrides.get(key)
    nm = (fp.name if fp and fp.name else fuss.name)   # I18nText
    name_map[key] = i18n.t(nm, lang)                  # → str for lang
html = fuss_refs.process_html(html, lang, name_map)
```

**Landing page** (near ~1450): no location context → global names only:

```python
name_map = {key: i18n.t(fuss.name, lang) for key, fuss in fuesse.items()}
html = fuss_refs.process_html(html, lang, name_map)
```

Order vs refs_pool is irrelevant — the two regexes (`[fuss:…]` vs
`<sup>[ref:…]`) never overlap. Place the fuss pass right after the
refs_pool pass at both sites.

## Link vs plain — the same-page-anchor constraint

`#fuss-KEY` exists **only when the location renders that fuss card**.
Cases:

- **Target on the same page** (common — a card cross-referencing a
  sibling standard the same location also documents): emit the link.
- **Target NOT on the page** (a page references a standard documented
  only elsewhere — e.g. a German page mentioning a Denmark-only fod):
  no `#fuss-KEY` anchor exists. **v1 decision: render plain
  `<code>name</code>`, no link** — never emit a dead in-page anchor.

  *Future enhancement (out of scope for v1):* cross-page linking would
  require a `{key → canonical_location_page}` map (which location "owns"
  each standard) so the href can point at `…/<loc>/<lang>/#fuss-KEY`.
  Defer until there's a real need; note it here so the constraint is
  understood, not rediscovered.

The `name` is still substituted in both cases — only the `<a>` wrapper
is conditional. So a rename always propagates everywhere; only the
*linkability* depends on co-location.

## Migration (part of "code later")

A one-shot maintenance script (`scripts/maintenance/migrate_fuss_xrefs.py`),
operating on `data/shared/fuesse.yml`, `data/v2/locations/*.yml`,
`data/locations/*.yml`:

1. **Key-form refs (the bulk, dozens):** `<code>KEY</code>` where
   `KEY ∈ set(fuesse keys)` → `[fuss:KEY]`. Safe and unambiguous —
   the snake_case key is the literal id. Known instances from the
   2026-06-11 survey: `11_333_thaler` (21×), `9_25_thaler` (18×),
   `8_daler_fod` (18×), `18_5_thaler` (18×), `8_gylden_fod` (12×),
   `30_thaler` (12×), `8_daler_lybsk_fod` (9×), `royal_holstein` (6×),
   and the long tail below the survey cutoff. Enumerate the full set
   from `fuesse.yml` keys at migration time, don't trust this list.
2. **Display-name-form refs (only the two cards already converted on
   2026-06-11):** `<code>Rosenobel-fod</code>` → `[fuss:rosenobel_fod]`,
   `<code>Nobelfod</code>` → `[fuss:nobel_fod]`. These need an explicit
   `{display_name → key}` map (2 entries) because the span no longer
   holds the key. Build that map from `fuesse[key].name` across all
   langs + known per-location overrides, OR just hard-code the two.
3. **Do NOT touch** `<code>…</code>` spans whose content is not a fuss
   key/name (catalog refs, coin nominals, weights, etc.). Restrict the
   match to the enumerated key set + the 2 display names.
4. After migration: `build.py --validate-only`, then full `build.py
   --include-v1`, then grep the rendered `site/**` for any residual
   literal `[fuss:` (= a key the resolver didn't recognise) and any
   `[UNKNOWN FUSS:` placeholder (= a key absent from `fuesse`).

## Test plan

- **Unit (`fuss_refs.process_html`):** same-page key → linked `<code>`;
  off-page key → plain `<code>`; unknown key → red placeholder;
  multiple markers in one string; marker adjacent to punctuation
  (`[fuss:nobel_fod]-Linie`, `[fuss:nobel_fod].`).
- **Per-location override:** render the Denmark page, assert a
  `[fuss:reichsdukatenfuss]` resolves to «Rigsdukatfod» (override), and
  the same marker on a German page resolves to «Reichsdukatenfuß»
  (global). This is the headline behaviour — lock it with a test.
- **Anchor presence:** assert the link href matches the rendered
  `id="fuss-KEY"` for an on-page target, and that an off-page target
  produces no `<a>`.
- **No regression:** rendered byte-diff before/after migration should
  change only the affected spans (name text identical where no override
  applies; `<code>X</code>` → `<a …><code>X</code></a>` where linked).

## Open considerations

- **Cross-page linking** — deferred (see §«Link vs plain»). Needs a
  canonical-owner map per standard.
- **Display-mode variants** — if we ever want the *historical_name* or a
  short form in a cross-ref, extend the marker (`[fuss:KEY:hist]`) and
  the name_map to carry multiple name variants. Not needed now; the
  marker grammar leaves room.
- **`audit_prose.py` rule** — after migration, a lint that flags any
  NEW hand-written `<code>fuss-name</code>` (catch authors who bypass
  the marker) would keep the convention from eroding. Optional follow-up.
