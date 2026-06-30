"""
Schema definitions for YAML data validation.

All types are Pydantic models. Validation errors at build-time catch:
- Missing required fields
- Invalid fuss/phase references
- Chronology mismatches
- Duplicate coin IDs
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Guard: every model below uses `extra='forbid'` (via _StrictBase) so that
# stray YAML keys — typos in field names, orphaned fields after a botched
# text-substitution edit, or fields the schema doesn't actually accept —
# raise a hard ValidationError at build time rather than being silently
# ignored. Combined with the AST-level duplicate-key check in
# `lib.yaml_check`, this makes the whole data layer fail-fast on shape
# mistakes, not just on type mistakes.
class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Shared types
# =============================================================================

class I18nText(_StrictBase):
    """A translatable string. DE is mandatory; EN/UK fall back."""
    de: str
    en: str | None = None
    uk: str | None = None

    def resolve(self, lang: str, fallback: list[str] = None) -> str:
        """Resolve to target language with fallback chain."""
        fallback = fallback or ["en", "de"]
        order = [lang] + [f for f in fallback if f != lang]
        for l in order:
            val = getattr(self, l, None)
            if val:
                return val
        return self.de  # last resort


class I18nTextOptional(_StrictBase):
    """Like I18nText but DE is optional (used for weight_rough_label etc.)."""
    de: str | None = None
    en: str | None = None
    uk: str | None = None

    def resolve(self, lang: str, fallback: list[str] = None) -> str | None:
        fallback = fallback or ["en", "de"]
        order = [lang] + [f for f in fallback if f != lang]
        for l in order:
            val = getattr(self, l, None)
            if val:
                return val
        return None


class FieldValue(_StrictBase):
    """A single measurement reading attributed to one source. Used as
    elements in list-form measurement fields (weight_rough_g,
    fineness, diameter_mm) when one or more sources document the
    field. The source label is short — full URL/citation context
    lives in the coin's `sources` block.

    A coin field can be either a bare number (single value, source
    implicit in the coin's catalog refs) OR a list of FieldValue
    entries (one per source, all values preserved with attribution).
    For derived calculations (Feingewicht = weight × fineness),
    values are paired by matching `source` label — so each source's
    coherent reading produces its own derived value, never mixing
    weight from one source with fineness from another.
    """
    value: float = Field(..., gt=0)
    source: str = Field(..., min_length=1)
    # display:false hides this reading from the rendered weight/fineness
    # column (and its derived Feingewicht) while keeping the data — the
    # §9a weight-specimen thinning (min/middle/max of an over-collected
    # single-resource museum bucket) sets it on the dropped intermediates.
    # Default True so existing entries render unchanged.
    display: bool = True


class HedeMuentzfussYield(_StrictBase):
    """Hede 1971 per-page «Marken fin udbragt til N <UNIT>» quote — the
    explicit Müntzfuß ratio Hede attested for this coin.

    Hede pages publish this quantity in the spec block right after
    Finvægt (e.g. «Bruttovægt 28,893 g · Finhed 0,875 · Finvægt 25,281 g
    · Marken fin udbragt til 9,250 speciedaler»). The (value, unit) pair
    identifies the Müntzfuß directly — 9.25 speciedaler ≡ 9¼-Speciedaler-
    Fuß, 11.333 rigsdaler_kurant ≡ 11⅓-Kurantmøntfod, 18.5 rigsbankdaler
    ≡ 18½-Rigsbankdaler-Fuß. The §8a auto-classifier consumes this field
    as the primary classification signal; absence falls back to fineness/
    weight-Δ math against fuss Soll values.

    Populated by `build_hede_denmark_seed.py` from the parser's
    `marken_fin_udbragt_til` spec key; empty when Hede didn't publish
    the ratio for that page.
    """
    value: float = Field(..., gt=0,
        description="The N in «udbragt til N» (parsed from Danish decimal notation).")
    unit: str = Field(..., min_length=1,
        description=(
            "Canonical denominator unit: 'speciedaler' / 'rigsdaler' / "
            "'rigsdaler_kurant' / 'rigsbankdaler' / 'piastre'."
        ))
    basis: str | None = Field(None,
        description="'fin' (fine Mark) or 'rauh' (gross Mark). Hede uses 'fin' on virtually all pages.")
    unit_raw: str | None = Field(None,
        description=(
            "Verbatim unit token from the page (e.g. 'daler', 'dlr', 'rd.kr', "
            "'speciedalere') when it differs from the canonical form. Kept "
            "for audit / debugging — downstream consumers use `unit`."
        ))


# =============================================================================
# Shared: fuesse.yml
# =============================================================================

class Fraction(_StrictBase):
    """A single denominational fraction of a fuss."""
    soll_fein_g: float
    soll_rau_g: float | None = None  # only for gold fuesse (optional)


class GrundwerteRow(_StrictBase):
    """A key-value row inside the Grundwerte card. Values may contain safe HTML."""
    key: I18nText
    value: I18nText


class Grundwerte(_StrictBase):
    """Base-value card shown under each Müntzfuß header."""
    heading: I18nText | None = None
    subheading: I18nTextOptional | None = None
    badge: I18nTextOptional | None = None            # small tag in header (e.g. "Müntzfuß · Silber")
    rows: list[GrundwerteRow] = Field(default_factory=list)
    rechnungsfraktionen_label: I18nTextOptional | None = None
    rechnungsfraktionen: I18nText | None = None      # rich block, safe HTML
    aside_label: I18nTextOptional | None = None       # optional 2nd right-column block
    aside: I18nText | None = None                     # rich block (right column, below
                                                      # rechnungsfraktionen) — e.g. a
                                                      # «Verhältnis zu anderen Füßen» note


class FussEvent(_StrictBase):
    """One historical event year recorded for two scopes.

    Each event has a single canonical year per scope:
      - `anywhere` : the year *anywhere* the standard was active.
        Always present for an event that happened at all.
      - `holstein` : the year specifically within Schleswig-Holstein.
        `null` (or omitted) means the event did not apply in H —
        e.g. `first_mint.holstein = null` for a Copenhagen-only
        kronemont, or for a standard adopted in H but never minted there.

    `approx_anywhere` / `approx_holstein` flag uncertain dates (rendered
    elsewhere as `~YYYY`; the int is still stored verbatim).

    `note` is a brief plain-text explanation — typically *why* the year
    is approximate, or which forordning / Reichsabschied marks the date.
    """
    anywhere: int | None = None
    holstein: int | None = None
    approx_anywhere: bool = False
    approx_holstein: bool = False
    note: str | None = None


class FussEvents(_StrictBase):
    """Five canonical historical events plus optional «sole» bookmarks.

    These atomic events are the source of truth. The three nested
    period types (visible as ▓ ⊂ ▒ ⊂ ░ in the timeline schematic)
    are derived from them:

      mint         = [first_mint, last_mint]                   (▓)
      status       = [first_adoption, std_end]                 (▒)
      circulation  = [first_adoption, demonetisation]          (░)
      sole         = [sole_start, sole_end]                    (✦)
                     OPTIONAL — only set when the standard had a
                     distinct period of being the SOLE legal tender,
                     different from its broader status period. E.g.
                     Reichsgoldmuenzfuß had legal-tender status
                     1871-1914, but only became sole legal tender 1907
                     (after Vereinsthaler demon) → 1914 (war suspension).

    Storing events (not periods) avoids duplication: when first_mint
    coincides with first_adoption (the standard was minted from year
    one), the year appears once. Containment ▓ ⊂ ▒ ⊂ ░ usually holds
    historically, but rare cases break it (e.g. 9-Thaler-Fuß H:
    std_end 1622 < last_mint 1625 — Friedrich III. switched standards
    while transition strikes continued). Storing atomic events keeps
    such facts faithful; the visualization layer is free to expand
    boundaries for display.
    """
    first_adoption: FussEvent | None = None
    first_mint: FussEvent | None = None
    last_mint: FussEvent | None = None
    std_end: FussEvent | None = None
    demonetisation: FussEvent | None = None
    sole_start: FussEvent | None = None
    sole_end: FussEvent | None = None
    anywhere_label: I18nText | None = None
    """Short translatable label for the `anywhere` scope, used in
    layer tooltips. Concretely identifies *where* "anywhere" means
    for THIS stope — e.g. «Священна Римська імперія», «Данія-Норвегія»,
    «Дансько-холштинський Гезамтштат», «Wiener Münzvertrag-Raum». The
    `holstein` scope uses the global UI string `tl.scope.holstein`."""


class Fuss(_StrictBase):
    """A global Münzfuß mathematical definition."""
    id: str = ""  # filled in by loader
    name: I18nText
    historical_name: str | None = None
    # ↑ Period-correct or near-period name (Reichsmüntzfuß, Speciesfuß,
    # Kurantmøntfod, Rigsbankfod, Vereinsmüntzfuß, Kronemøntfod, …).
    # Single string in original orthography (German with ß/ä; Danish with ø);
    # not localised — these are proper-noun monetary terms shared across all
    # rendered languages. Rendered in `.phistorical` above `.psub` in the
    # phase-header.
    metal: Literal["silver", "gold"]
    grid_unit_g: float = Field(..., description="E.g., 233.856 for Cöllnische Marck")
    grid_unit_name: str | None = Field(
        None,
        description=(
            "Human-readable name of the mass unit measured by "
            "`grid_unit_g`. The canonical period-correct form, e.g. "
            "«Cöllnische Marck» (233.856 g; default for pre-imperial "
            "Danish + Reichsthaler-family stops), «Zollpfund» (500 g; "
            "Vereinsmüntzfuß 1857 + Reichsgoldmüntzfuß 1871), «Pfund "
            "metrisch» (500 g; Wiener Münzvertrag gold), «Kilogramm» "
            "(1000 g; Skandinavisk Møntunion 1873). Together with "
            "`grid_stops` and `grid_unit_convention` this fields gives "
            "the complete period-formula «N Stück per <unit> [rauh|fein] "
            "@ <fineness_period>»."
        ),
    )
    grid_stops: float = Field(..., description="E.g., 9.25 for 9¼-Fuß")
    grid_unit_convention: Literal["rauh", "fein"] | None = Field(
        None,
        description=(
            "Period convention anchor for `grid_unit_g` + `grid_stops`. "
            "`rauh` (alloyed metal mass) — pre-Reichsabschied 1566 stops "
            "express N pieces per ROUGH Cölln. Marck @ Lod-fineness "
            "(e.g. C-III Royal Dalerfod «8 Daler aus der Marck rauh @ "
            "14½ Lod»; same convention applies to 8_5_gylden_fod, "
            "8_gylden_fod, christian_iii_*, rhinsk_gylden_fod, "
            "f2_guldkrone_fod, nobel_fod, rosenobel_fod, kronemont*, "
            "guldkrone, reichsdukatenfuss, pistolenfuss, "
            "courantdukatenfuss). `fein` (pure metal mass) — post-1566 "
            "imperial-aligned stops express N pieces per FINE Cölln. "
            "Marck or Pfund (e.g. 9-Thaler-Fuß «9 Reichsthaler aus der "
            "Marck fein», 9_25_thaler, 11_333_thaler, 18_5_thaler, "
            "30_thaler, vereinsgoldmuenze, reichsgoldmuenzfuss, "
            "kronefod). Optional for backward compatibility; new stops "
            "must declare. The unit itself (Marck / Pfund / kg) is "
            "captured by `grid_unit_name` + `grid_unit_g`."
        ),
    )
    fineness_standard: float = Field(..., ge=0.0, le=1.0)
    fineness_period: str | None = Field(
        None,
        description=(
            "Period-form fineness expression in the source-attested "
            "unit (Karat/Grän for gold, Lod/Loth for silver, ‰ for "
            "post-1857 metric-era stops). Examples: «23 Karat 8 Grän» "
            "(reichsdukatenfuss .986), «14½ Lod» (christian_iii_"
            "dalerfod .906), «14²⁄₉ Loth» (9_thaler .8889), «21¾ Karat» "
            "(pistolenfuss .903), «900‰» (kronefod metric-era). "
            "Complements the decimal `fineness_standard` (machine-"
            "readable) and `fineness_display` (full formatted string "
            "for rendering). This is the bare period locator — the "
            "audit-/query-facing value for «what unit did the source "
            "use» without parsing display prose."
        ),
    )
    fineness_display: str | None = None
    description: I18nText | None = None
    grundwerte: Grundwerte | None = None
    fractions: dict[str, Fraction]
    events: FussEvents | None = None


# =============================================================================
# Location YAML: phases + coins
# =============================================================================

class Phase(_StrictBase):
    id: str
    year_from: int
    year_to: int
    from_label: str
    to_label: str
    title: I18nText
    description: I18nText | None = None     # short .phd tagline under the .ph header
    context: I18nText | None = None         # <details>Kontext und Details</details> rich-HTML block
    mt_caption: I18nText | None = None      # caption rendered above the first coin table

    @model_validator(mode="after")
    def check_year_order(self):
        if self.year_to < self.year_from:
            raise ValueError(f"phase {self.id}: year_to ({self.year_to}) < year_from ({self.year_from})")
        return self


class FussPeriod(_StrictBase):
    """Per-location framing of a single Müntzfuß: validity range + background + closing summary.

    Also acts as the per-location override layer for select shared/fuesse.yml
    fields (per the per-location-override design 2026-05-22). When any of
    `name`, `historical_name`, `description`, or `grundwerte` is set in
    a location's `fuss_periods.<fuss>` block, the build resolver overlays
    it on the shared Fuß definition for THIS page. Sub-keys of `grundwerte`
    (heading/subheading/badge/rechnungsfraktionen_label/rechnungsfraktionen)
    are independently overridable; the `rows` list, when provided, FULLY
    REPLACES the shared list (no list-level deep-merge).

    Use case: the same physical Fuß (e.g. Reichsdukatenfuß = Hungarian-
    Venetian Dukat tradition) gets distinct narratives on the Danish vs
    German page — on denmark.yml it surfaces as «Rigsdukatfod 1481-1876
    Hungarian-Goldgulden tradition»; on lubeck/SH pages it stays the
    canonical imperial «Reichsdukatenfuß 1559+». Same Fuß ID, same
    coins, different framing.
    """
    pdate_label: I18nText | None = None      # .pdate — e.g. "Geltungsbereich in Holstein: ca. 1625 → 24. Aug. 1866 · ca. 240 Jahre"
    hintergrund: I18nText | None = None      # .psub — short summary (1–3 sentences) shown in the fuss title block
    details: I18nText | None = None          # .fuss-hintergrund — long-form historical context, rendered inside the «Деталі» toggle
    closing: I18nText | None = None          # .terr summary block rendered after the last phase
    closing_label: I18nTextOptional | None = None  # small uppercase .tlb inside .terr

    # ---- Per-location override layer (opt-in; absent → fall back to shared/fuesse.yml) ----
    name: I18nText | None = None                   # override Fuss.name on this page
    historical_name: str | None = None             # override Fuss.historical_name
    description: I18nText | None = None            # override Fuss.description (long intro)
    grundwerte: Grundwerte | None = None           # override Fuss.grundwerte (deep-merge on top-level sub-keys; lists replace)


class KMRef(_StrictBase):
    """A Krause-Mishler reference with an optional register tag.

    Krause publishes regional volumes with independent numbering
    (Denmark vs Schleswig-Holstein vs Norway vs German States…) —
    KM-25 in the Denmark volume is unrelated to KM-25 in the SH
    volume. When ONE coin appears in MULTIPLE Krause volumes under
    DIFFERENT numbers (e.g. a Glückstadt issue catalogued both as
    DK-KM-25 and SH-KM-87), every list entry needs its own register
    tag so the renderer can disambiguate.

    The `register` value is short region code: `DK` (Denmark), `SH`
    (Schleswig-Holstein), `NO` (Norway), `DE-*` (German states by
    sub-region). `None` means «inherit the page's default register»
    (see Location.km_register). The compute layer's rendering rule:

      * Single list entry with implicit register (= None or equals
        page's default) → bare «KM#» prefix.
      * Single list entry with non-default register → «KM-<reg>#»
        prefix + tooltip.
      * Multiple list entries → every token «KM-<reg>#» + tooltip
        (so the reader can read off which catalog volume each
        number lives in).
    """
    value: str
    register: str | None = None


class CatalogRefs(_StrictBase):
    # `km` accepts four shapes:
    #   * scalar string (e.g. `'73'`) — single KM in the page's default
    #     register
    #   * dict `{<register>: <km>}` (V2, per V2_PIPELINE.md §4) — explicit
    #     per-register namespacing for a coin catalogued in multiple Krause
    #     volumes. Build assembly's `resolve_km_for_location()` picks the
    #     entry whose register matches the current display location. Keys
    #     match `data/locations/<loc>.yml::km_register` casing (`'dk'`,
    #     `'sh'`, …) — lookup is case-insensitive.
    #   * list of strings — multi-KM (same coin in multiple Krause
    #     volumes), all rendered with page's default register
    #   * list of KMRef objects — multi-KM with per-entry register tags
    # See KMRef docstring for the cross-register rendering rules; see
    # V2_PIPELINE.md §4 for the dict-form rationale.
    km: str | dict[str, str] | list[str | KMRef] | None = None
    lange: str | list[str] | None = None
    # `hede` (and parallel `sieg` / `schou`) accept a list form when the
    # coin is a Krause-KM-canonical entry that spans multiple Hede sub-
    # letters (mint-master / die-cutter variants Krause folds into one
    # type). Example: KM-81 = Hede 115A / 115B / 115C / 115D. The list
    # entries are positionally aligned with `sieg` / `schou` when those
    # are also lists, so a renderer can pair them per-sub-letter when
    # showing the breakdown. Scalar form remains the default for
    # single-sub-letter coins.
    hede: str | list[str] | None = None
    # Ruler-volume code per danskmoent.dk URL convention. Hede 1971
    # publishes a separate catalogue volume per Danish king, so
    # «Hede 28» is ambiguous across rulers (Christian IV's c4h28
    # is a different coin from Christian VII's c7h28). Storing the
    # volume code explicitly lets the matcher and any future
    # cross-source tooling disambiguate without re-deriving from
    # `coin.ruler`. Codes follow the danskmoent.dk URL pattern:
    # c{N}h for Christian {N}, f{N}h for Frederik {N}, etc. Keep
    # `hede` as the bare number+suffix; the full reference is
    # f"{hede_volume}{hede}" when both are set.
    hede_volume: str | None = None
    sieg: str | list[str] | None = None
    # Sieg catalog number as printed in Holger Hede's "Danmarks og Norges
    # Mønter" 1964/1971 (via danskmoent.dk's Hede pages). The Sieg-
    # Møntkatalog is an annual catalogue (43rd ed in 2016 per Numista's
    # SIEG literature record) with renumbering between editions, so the
    # number printed in Hede 1971 (= the Sieg edition contemporaneous
    # with that monograph, c. 1960s-1970s) systematically differs from
    # the number printed in modern auction catalogues like Stack's
    # Bowers Bruun PDF 2024-2026. Typical offset ≈ +16 across the
    # Christian IV silver section (c4h*); other ranges vary. We keep
    # `sieg` as the modern reference for cross-checking against current
    # auction citations, and `sieg_hede1971` records the older number
    # so a researcher cross-checking against Hede 1971 / danskmoent.dk
    # finds the entry. The renderer only surfaces `(Hede-1971: X)` when
    # the two values differ.
    sieg_hede1971: str | None = None
    schou: str | list[str] | None = None
    # Schou catalog number as printed in Hede 1971 / danskmoent.dk
    # when it differs from the modern Schou citation (analogous to
    # `sieg_hede1971`). H. H. Schou's «Beskrivelse af de paa Den
    # Kongelige Mønt- og Medaillesamling forefundne mønter» (1926-1929)
    # is itself stable — but Hede 1971 sometimes prints a Schou range
    # like «3,31» where modern citations give the per-coin Schou number
    # (e.g. «3» for one sub-variant); this field preserves the Hede
    # 1971 reading.
    # Per CLAUDE.md «Data-accumulation principle»: every catalog ref
    # below accepts `str | list[str]`. When the cross-source merger
    # encounters two members with different values for the same ref
    # (e.g. two distinct Numista N#s describing the same physical
    # coin), it emits list-form to preserve both. Render layer picks
    # one for display; data layer keeps everything. Same goes for
    # legacy V1-singleton refs — list-form is opt-in via merger.
    schou_hede1971: str | None = None
    fr: str | list[str] | None = None
    dav: str | list[str] | None = None
    # Galster — primary Danish-medieval catalogue (Georg Galster's series of
    # «Mønter fra ...» publications). `galster_volume` parallels
    # `hede_volume` — the per-ruler / per-series volume code where bare
    # `galster` numbers would otherwise collide across publications.
    galster: str | list[str] | None = None
    galster_volume: str | list[str] | None = None
    # Jensen-Skjoldager catalogue — Norwegian medieval (pre-1481) supplemental
    # to Galster, used in galster + bruun seeds for Norwegian-tier coinage.
    jensen_skjoldager: str | list[str] | None = None
    # Schive — Norwegian C. I. Schive «Norges Mynter til Henrik III».
    schive: str | list[str] | None = None
    # Skaare — Kolbjørn Skaare, «Coins and Coinage in Viking-Age Norway»
    # (1976) / «Norges mynthistorie» (1995).
    skaare: str | list[str] | None = None
    # Friedberg — Robert Friedberg «Gold Coins of the World». Global gold
    # reference; cited for Danish-Norwegian gold issues.
    friedberg: str | list[str] | None = None
    # Davenport (long-form variant emitted by some seed parsers;
    # `dav` short alias used by the V1 main builder).
    davenport: str | list[str] | None = None
    # Madai-Bach pre-Krause numbering for Schleswig-Holstein duchy coins
    # (used by NumisMaster on entries pre-1604 where KM# was never assigned;
    # appears as «MB# 27» on the source page's catalog-number field).
    mb: str | list[str] | None = None
    # NMD — Norwegian medieval-era catalogue cited alongside Sieg/Galster
    # in the Bruun PDFs (esp. pre-1541 Norway lots). Cited as «NMD-1»,
    # «NMD-2», etc.
    nmd: str | list[str] | None = None
    # FP — Friberg-Pedersen catalogue (Bent Friberg & Tom Pedersen),
    # «Skillingen, Specien og Kronen 1761-1813». Christian VII-specific
    # Danish + Norwegian catalogue cited alongside Hede/Sieg/Schou on
    # 1766-1808 lots in the Bruun PDFs. Cited as «FP-9.3», «FP-44.6»,
    # «FP-36», etc. Both base-numbers and sub-variant decimals appear.
    fp: str | list[str] | None = None
    # ── Additional regional catalogues surfaced by KMM / Nationalmuseet
    #    (the museum `typeNumber` field; see docs/KMK_HARVEST.md). All cited
    #    in-scope; abbreviation in parens is the KMM `typeNumber` prefix. ──
    # Thomsen («Th.») — C. J. Thomsen's collection catalogue, Danish.
    thomsen: str | list[str] | None = None
    # Bergsøe («Bgs.») — Danish (Vilhelm Bergsøe), medals + coins.
    bergsoe: str | list[str] | None = None
    # Hauberg («Hbg.») — P. Hauberg, «Danmarks Myntvæsen … 1146-1241»,
    # medieval Danish (borderline; mostly era-gated out at SEED).
    hauberg: str | list[str] | None = None
    # Aagaard («Aagaard 1996 …») — Danish modern typology reference.
    aagaard: str | list[str] | None = None
    # Welter — Gerhard Welter, «Die Münzen der Welfen» (Brunswick-Lüneburg).
    welter: str | list[str] | None = None
    # Fiala — Eduard Fiala, Brunswick-Lüneburg coinage.
    fiala: str | list[str] | None = None
    # Behrens — Hermann Behrens, «Münzen und Medaillen der Stadt Hamburg»
    # / «… der Stadt und des Bisthums Lübeck» (Hanseatic).
    behrens: str | list[str] | None = None
    # Gaedechens — O. C. Gaedechens, Hamburg coins + medals.
    gaedechens: str | list[str] | None = None
    # Jesse — Wilhelm Jesse, «Der wendische Münzverein» (Hamburg / Lübeck /
    # Mecklenburg Hanseatic monetary union).
    jesse: str | list[str] | None = None
    # Kreber — Hamburg medal / coin catalogue.
    kreber: str | list[str] | None = None
    # Bruun citation. collection-id IS list-form: same physical coin
    # type can appear in MULTIPLE Bruun lots (different specimens) with
    # their own collection ids — the merger preserves every distinct id.
    # part / lot_no / page are specimen-level — top-auth wins for the
    # display tuple but the per-member detail lives in `sources[]`.
    bruun_collection_id: str | list[str] | None = None
    bruun_part: Literal["I", "II", "III", "IV", "V", "VI"] | None = None
    bruun_lot_no: int | None = None
    bruun_page: int | None = None
    bruun_lot: str | list[str] | None = None
    # Numista N#: list-form when two N#s describe the same physical
    # coin (rare but happens — sub-variants Numista chose to split that
    # other sources merge).
    numista: str | list[str] | None = None
    others: list[str] = Field(default_factory=list)


class Source(_StrictBase):
    type: Literal["numista", "ucoin", "auction", "museum", "literature", "web", "other"] = "other"
    url: str | None = None
    ref: str | None = None
    note: str | None = None
    display: bool = True
    """When False the citation is SUPPRESSED from the rendered table but kept in
    the data (data-accumulation principle — nothing is lost). Set by the
    specimen-thinning pass for weightless museum over-collections: when a coin
    has no weight and ≥5 KMM specimen citations, only ~3 representatives stay
    visible (imaged-first), the rest are display:false. The renderer skips
    display:false sources; the YAML retains every link + datum under the hood."""


class FussRef(_StrictBase):
    """One line in the Fuß-column for a coin (primary / secondary / tertiary).
    Used for dual- or triple-denominated coins where the same silver content
    simultaneously expresses a fraction of several Müntzfüße."""
    rank: Literal["primary", "secondary", "tertiary", "plain"] = "plain"
    label: I18nText


class Coin(_StrictBase):
    id: str
    fuss: str = Field(..., description="FK to shared/fuesse.yml")
    phase: str | dict[str, str] = Field(
        ...,
        description=(
            "FK to location.phases[fuss]. Scalar string for the 90% case "
            "(coin sits in the same phase on every display page it surfaces "
            "on). Dict `{loc_id: phase_id}` (V2, per V2_PIPELINE.md §5) when "
            "the same coin lives in different local periodisations across "
            "the display pages of multi-consumer entity files. The build "
            "assembly's `resolve_phase_for_location()` picks the matching "
            "key at render time."
        ),
    )
    kind: Literal["kurant", "scheide", "tarif", "tarif_subunit", "gedenk"]
    nominal: str = Field(..., description="Literal inscription or closest transcription")
    # year_label / year_first are REQUIRED for classified coins, but OPTIONAL for
    # `fuss == seed_unsorted` — undated KMM museum specimens (no year, no KM) are
    # legitimately yearless and never render; enforced by `_check_year_required`.
    year_label: str | None = None
    year_first: int | None = None
    year_last: int | None = None
    year_verified: bool = Field(
        True,
        description=(
            "True when the coin's year is attested by the coin's own "
            "inscription (the inscription IS the source per CLAUDE.md §5 "
            "tier 1) OR by a catalogue's exact dating. False when the "
            "year is an attribution-only estimate (typical for undated "
            "Klippen / counterstrikes / no-date issues where Bruun / "
            "Hede gives «ca. NNNN» or «ND»). Render layer surfaces a "
            "(?) marker next to the year column when False — analogous "
            "to the `*_verified` flags for metal / fineness / weight / "
            "diameter / mint. The `year_label` field itself stays plain "
            "decimal per §3a; the uncertainty is expressed via this "
            "flag, NOT by inlining «(?)» / «ca.» / «ND» into the label."
        ),
    )
    year_ranges: list[list[int]] | None = Field(
        None,
        description=(
            "Optional list of explicit `[first, last]` minted-year sub-ranges "
            "for coins NOT struck continuously across [year_first, year_last]. "
            "Use when Numista (or any source) shows actual struck years are "
            "sparse — e.g. KM#75 N#313684 spans 1625-1657 in the summary but "
            "was actually struck only 1625-1626, 1635-1636, 1656-1657. When "
            "set, the per-year mintage marker on the timeline iterates "
            "year_ranges (NOT [year_first, year_last]) so the visualization "
            "and tooltip counts reflect real minting activity."
        ),
    )
    ruler: str | None = None
    ruler_verified: bool = Field(
        True,
        description=(
            "Whether the ruler attribution comes from a source-attested "
            "reading (coin inscription, Hede page header, Numista entry "
            "with explicit ruler field). False when the attribution is "
            "suspect — typical trigger 2026-05-22: ucoin source data "
            "occasionally tags a coin with a king whose reign doesn't "
            "cover the coin's minting year (e.g. ucoin tid=79557 «4 "
            "Skilling 1807 — Frederick VI» but Christian VII reigned "
            "until 13 March 1808). The ucoin builder's reign-window "
            "check flips this False, then the cross-source merger's "
            "verified-wins rule (§4) lets NumisMaster / Bruun / Hede "
            "attestations override the suspect ucoin reading."
        ),
    )
    mint: str | list[str] | None = Field(
        None,
        description=(
            "Mint city/cities where the coin was struck. A bare string for "
            "single-mint coins (the common case); a list of strings when the "
            "same type was struck IN PARALLEL at multiple mints (e.g. "
            "['Altona', 'Kopenhagen', 'Kongsberg'] for Christian VII's 1 Skilling "
            "1771). Mintmaster initials NEVER live in this field — they go in "
            "the dedicated `mintmaster` field (per user policy 2026-05-18 / "
            "V2_DECISIONS D32). The render layer joins list entries with «, » "
            "for the mint column."
        ),
    )
    mint_verified: bool = True
    mintmaster: str | None = None
    catalog: CatalogRefs = Field(default_factory=CatalogRefs)
    metal: Literal["silver", "gold", "billon", "copper", "lead", "bronze"] | None = None
    metal_verified: bool = Field(
        True,
        description=(
            "True when the metal designation comes from a sourced field "
            "(Numista composition, ucoin Composition, Hede / Lange / Sieg "
            "per-coin record). False when inferred from project tier "
            "convention (per CLAUDE.md §6: Krone-fod øre tier, sub-Skilling "
            "Scheide → billon, etc.) without source verification. Render "
            "layer surfaces a (?) marker next to the metal label when False."
        ),
    )
    fineness: float | list[FieldValue] | None = Field(
        None,
        description=(
            "Either a bare number (single source, source implicit in "
            "catalog refs) OR a list of FieldValue entries — one per "
            "source — when multiple sources document the value with "
            "explicit attribution required."
        ),
    )
    fineness_verified: bool = True
    weight_rough_g: float | list[FieldValue] | None = Field(
        None,
        description="Same form as fineness — scalar or list of FieldValue.",
    )
    weight_rough_label: I18nTextOptional | None = None
    weight_rough_verified: bool = True
    diameter_mm: float | list[FieldValue] | None = Field(
        None,
        description="Same form as fineness — scalar or list of FieldValue.",
    )
    diameter_mm_verified: bool = True

    hede_muentzfuss_yield: HedeMuentzfussYield | None = Field(
        None,
        description=(
            "Hede 1971 per-page «Marken fin udbragt til N speciedaler/"
            "rd.kr/...» quote — the explicit Müntzfuß ratio attested by "
            "Hede for this coin. Authoritative classification signal: "
            "the (value, unit) pair maps to a project Müntzfuß "
            "directly (9.25 speciedaler → 9¼-Speciedaler-Fuß, 11.333 "
            "rigsdaler_kurant → 11⅓-Kurantmøntfod, 18.5 rigsbankdaler "
            "→ 18½-Rigsbankdaler-Fuß, etc.). Populated by "
            "build_hede_denmark_seed.py from `marken_fin_udbragt_til` "
            "in the parsed Hede sidecar; absent when the Hede page "
            "didn't quote the ratio."
        ),
    )

    @field_validator("fineness", mode="before")
    @classmethod
    def _validate_fineness_range(cls, v):
        # Bare-number form: must be in [0, 1]
        if isinstance(v, (int, float)):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"fineness must be in [0, 1], got {v}")
        elif isinstance(v, list):
            for entry in v:
                val = entry.get("value") if isinstance(entry, dict) else getattr(entry, "value", None)
                if val is not None and not (0.0 <= val <= 1.0):
                    raise ValueError(f"fineness FieldValue.value must be in [0, 1], got {val}")
        return v
    fraction: str | None = Field(None, description="E.g., '1/12' — lookup key in fuss.fractions")
    issuing_entity: str | list[str] | None = Field(
        None,
        description=(
            "FK to data/i18n/issuing_entities.yml — political entity that "
            "struck the coin. Scalar form is the 90% case. List form (V2, "
            "per V2_PIPELINE.md §3.10) for joint-jurisdiction coins (e.g. "
            "Altona+Kopenhagen mint → `[danish_realm, royal_holstein]`). "
            "Each list element must be a known entity tag; list non-empty, "
            "no duplicates. Per the home-file rule, the coin is stored in "
            "the entity file matching the alphabetically-first element."
        ),
    )
    entity_classified_via: Literal["mint", "nation", "issuer", "ruler", "manual"] | None = Field(
        None,
        description=(
            "Provenance of the `issuing_entity` value — HOW it was derived, "
            "not whether it is correct (entity is ALWAYS inferred; no source "
            "states the political tag). Records the reliability tier of the "
            "inference so curators can prioritise review of coarse routings: "
            "`mint` = classified from a specific mint city (precise); "
            "`nation`/`issuer` = classified from a realm / jurisdiction string "
            "(coarse — e.g. KMM `nation` fallback when no mint, or Numista "
            "issuer text); `ruler` = from authority name; `manual` = curator-"
            "assigned. None = unset (legacy / pre-classifier entries). "
            "Project-internal scaffolding — never rendered (CLAUDE.md §0z)."
        ),
    )
    fuss_refs: list[FussRef] = Field(default_factory=list,
        description="Multi-rank Fuß labels (for dual- or triple-denominated coins)")
    inscription_obv: str | None = None
    inscription_rev: str | None = None
    note: I18nText | None = None
    sources: list[Source] = Field(default_factory=list)
    verified: bool = True
    verification_note: I18nText | None = None
    # ---- V2 fields (per V2_PIPELINE.md §3) -------------------------------
    # composed_of / promoted_to encode the bidirectional seed↔curated link
    # set up in Phase 6. `composed_of` is the authoritative side (curator
    # writes it); `promoted_to` is derived by `relink_promoted_v2.py`.
    composed_of: list[str] | None = Field(
        None,
        description=(
            "V2 bidirectional link (curated side): list of seed ids that "
            "this curated coin rolled up. Build assembly drops seed entries "
            "whose `promoted_to` is set so they don't render duplicate."
        ),
    )
    promoted_to: str | None = Field(
        None,
        description=(
            "V2 bidirectional link (seed side): pointer back to the curated "
            "coin id that subsumes this seed entry. Derived by "
            "`relink_promoted_v2.py` from curated `composed_of` lists."
        ),
    )

    # `_entity_routing_hint` is audit metadata from
    # `scripts/lib/entity_routing.py`, written to the YAML when any rule
    # in `data/v2/entity_routing_rules.yml` matched this coin's
    # patterns. Persists across regen / absorb so curators debugging a
    # non-obvious placement can see the rule's verdict.
    #
    # Shape: {rule_id, matched_on, would_route_to, active,
    # agrees_with_active?, reasoning}. `active=true` → rule changed
    # entity; `active=false` + `agrees_with_active=false` → mint and
    # rule disagree (curator-review case). Not rendered on pages.
    #
    # Not modelled as a Pydantic field because of pydantic v2's
    # leading-underscore prohibition. Stripped from the dict by the
    # build assembly + the seed writer before Coin instantiation, same
    # mechanism as the V1→V2 migration breadcrumbs below.
    # ---- V2 migration bookkeeping (temporary; cleaned at Phase 9 flip) ----
    # The migration script adds three extra keys per V2 coin yaml:
    #   - `v1_home_location` — source `data/locations/<loc>.yml` stem
    #   - `_migration_note` — human-readable «how was this derived» note
    #   - `_migration_dup_origin_id` — id collision back-reference
    # These are NOT modelled on Coin; they're stripped from the dict by
    # the Phase 4 build assembly (`_assemble_v2_location` /
    # `_strip_v2_breadcrumbs`) before instantiating the Coin. Keeping them
    # outside the schema avoids polluting the model with throwaway fields
    # AND avoids pydantic v2's private-attribute trap on underscore names.
    # Cleaned at Phase 9 promotion.
    # ----------------------------------------------------------------------

    @field_validator("issuing_entity")
    @classmethod
    def _validate_issuing_entity_list(cls, v):
        if not isinstance(v, list):
            return v
        if not v:
            raise ValueError("issuing_entity list must be non-empty")
        if len(set(v)) != len(v):
            raise ValueError(f"issuing_entity list has duplicates: {v}")
        return v

    @model_validator(mode="after")
    def _check_year_ranges(self):
        """If `year_ranges` is set: validate well-formed [first, last] pairs
        and confirm that `year_first` / `year_last` envelope the union."""
        if self.year_ranges is None:
            return self
        if not self.year_ranges:
            raise ValueError(f"coin {self.id}: year_ranges must be non-empty if set")
        for r in self.year_ranges:
            if len(r) != 2 or not all(isinstance(x, int) for x in r):
                raise ValueError(f"coin {self.id}: each year_ranges item must be [first:int, last:int]")
            if r[1] < r[0]:
                raise ValueError(f"coin {self.id}: year_ranges item {r}: last < first")
        rmin = min(r[0] for r in self.year_ranges)
        rmax = max(r[1] for r in self.year_ranges)
        if self.year_first != rmin:
            raise ValueError(
                f"coin {self.id}: year_first ({self.year_first}) must equal "
                f"min(year_ranges) ({rmin})"
            )
        if self.year_last is None or self.year_last != rmax:
            raise ValueError(
                f"coin {self.id}: year_last ({self.year_last}) must equal "
                f"max(year_ranges) ({rmax})"
            )
        return self

    @model_validator(mode="after")
    def _check_year_required(self):
        """`year_label` + `year_first` are mandatory for CLASSIFIED coins (every
        coin that renders), but optional for `fuss == seed_unsorted` — an
        unclassified KMM museum specimen may legitimately carry no year and no
        catalogue number (undated, never rendered). This keeps the contract
        strict where it matters and stops naked museum records from failing
        schema validation (audit_v2 I4)."""
        if self.fuss != "seed_unsorted":
            missing = [f for f in ("year_label", "year_first")
                       if getattr(self, f) is None]
            if missing:
                raise ValueError(
                    f"coin {self.id}: {', '.join(missing)} required for a "
                    f"classified coin (fuss={self.fuss!r})"
                )
        return self


class HiddenLayer(_StrictBase):
    """One (scope, kind) pair to suppress on a single TimelineBar.
    Used in `TimelineBar.hide_layers` for granular per-page visibility
    filtering — see the docstring there for context and use cases."""
    scope: Literal["anywhere", "holstein"]
    kind: Literal["mint", "status", "circulation", "sole"]


class TimelineBar(_StrictBase):
    id: str
    label: I18nText
    small: I18nTextOptional | None = None
    year_from: int
    year_to: int
    bar_label: I18nTextOptional | None = None
    bar_title: I18nTextOptional | None = None
    nominal_modern: I18nTextOptional | None = None
    """Modern normalised form of the largest accounting unit (the
    «nominal» part of the label). Period orthography may be used in
    `label` (e.g. «Golt Krone», «Rosen Nowel») while the
    normalised modern form (e.g. «Guldkrone», «Rosenobel») stays
    machine-searchable here. Purely data — the renderer does not
    consume this field today; future audit / search tooling can.
    Add this for ANY bar whose `label` uses period orthography in
    the nominal suffix; optional for bars whose `label` already
    uses the canonical modern form."""
    color_class: str = "si"   # CSS modifier: si, sh, rb, kr, krm, vt, rm, g
    order: float | None = None
    """Optional sort key for the timeline-bar order. When set, bars are
    sorted by `order` ascending (stable sort — bars with equal `order`
    keep their YAML insertion order); when unset, the bar falls back to
    its YAML position. Use to inject a new bar into a specific position
    without physically moving YAML blocks: assign an `order` between two
    existing bars' position-indexes (or fractional, e.g. 1.5 to land
    between positions 1 and 2)."""
    indented: bool = False    # render label with left padding (sub-entry)
    dashed: bool = False      # render bar with dashed border (derived standard)
    compact: bool = False     # render track half-height (non-Fuß, e.g. Theilung)
    overlay: bool = False     # render INTO the previous bar's track (not a new row);
                              # the bar lays over its parent as a thinner stripe and
                              # its label folds in as a sub-line under the parent's label.
    events: FussEvents | None = None    # 5 canonical events × 2 scopes (anywhere / holstein);
                                        # used for stopes that appear on the timeline but
                                        # are NOT defined in shared/fuesse.yml as a Fuß
                                        # (e.g. Reichsgoldmünzfuß is a contextual entry only)
    truncate_anywhere_after: int | None = None
    """Cap the `anywhere` scope's `last` year for this bar at this value;
    drop the layer entirely when its `first` year is already past the cutoff.
    Use case: on the Holstein page, Danish-Helstaten stopes (kronemont,
    9¼-Fuß, 18½-Fuß etc.) continued in Copenhagen after the Prussian
    annexation 24 Aug. 1866, but that continuation is no longer relevant
    to a Holstein-page timeline; setting `truncate_anywhere_after: 1866`
    on those bars sharply cuts every anywhere-scope layer at 1866 (status,
    circulation, mint, sole) without touching the holstein-scope layers
    (which already terminate at 1866 in their `events`)."""
    truncate_anywhere_after_by_kind: dict[str, int] | None = None
    """Per-kind override of `truncate_anywhere_after`. When set, the dict
    maps layer kind (`mint` / `status` / `circulation` / `sole`) to its
    own cutoff year for the anywhere scope; any kind not in the dict
    falls back to `truncate_anywhere_after`. Use case: the 9-Thaler-Fuß
    bar on the Holstein page wants to cut mint+status at 1667 (Saxon-
    Pivot, Reich-wide mass-minting end) but extend circulation to ~1700
    (Hauptumlaufmünze functional end per Wikipedia DE «Speciestaler»);
    a single `truncate_anywhere_after` cannot express that asymmetry."""
    hide_anywhere: bool = False
    """When `true`, suppress all anywhere-scope layers (mint, status,
    circulation, sole) for this bar — render only the holstein-scope
    layers. The underlying events in `data/shared/fuesse.yml` are
    preserved; this is a per-page visibility flag. Use case: on the
    Holstein page the 9-Thaler-Fuß bar's anywhere-extent (1566—1875,
    Hamburg/Lübeck Bank-Mark continuation) is Reich-/Hanseatic-broad
    context that distracts from the Holstein-narrative the bar is meant
    to convey; hiding the anywhere layers keeps only the Holstein-
    territorial story (1566—1625 mint, 1566—~1700 circulation)."""
    hide_layers: list["HiddenLayer"] = Field(default_factory=list)
    """Per-bar visibility filter — suppress specific (scope, kind) layers
    while keeping the rest of the bar visible. Finer-grained than
    `hide_anywhere` (which kills every anywhere-scope layer at once).
    Use case: on the Holstein page the Krone bars (kronemont,
    kronemont_chr_iv, kronemont_fine) carry an anywhere-circulation
    layer (Helstaten-wide circulation until Statsbankerot 1813) that is
    Danish-Norwegian-broad and not relevant to the Holstein narrative;
    setting `hide_layers: [{scope: anywhere, kind: circulation}]` on
    those bars suppresses just that one layer while leaving the
    anywhere-mint and anywhere-status layers intact."""
    mint_alpha_multiplier: float | None = None
    """Override `--layer-alpha-multiplier` for THIS bar's `mint` layer
    only (default: inherit the page value — 2 on a `denmark_only` page,
    1 elsewhere). Emphasises the «карбування» (mint) stripe, e.g. when
    the status / circulation layers are hidden via `hide_layers` and the
    lone mint stripe would otherwise render at the faint stacking alpha.
    `6` = 3× the denmark-only baseline (2 × 0.1667 ≈ 0.33 → ≈ 1.0)."""


class Timeline(_StrictBase):
    title: I18nText
    year_from: int
    year_to: int
    axis_step: int = 50
    bars: list[TimelineBar] = Field(default_factory=list)
    scope_mode: Literal["dual", "denmark_only"] = "dual"
    """`dual` (default): emit both `anywhere` and `holstein` scope layers per
    bar — this is the Holstein-page model where the Reich/Helstaten span
    is the broader context and the Holstein-territorial span is the focused
    sub-track. `denmark_only`: emit only `anywhere` scope layers; suppress
    every holstein-scope layer entirely. Used on the Denmark page where
    Holstein is not a separate track — anywhere = the Royal Danish view."""

    @model_validator(mode="after")
    def _sort_bars_by_order(self):
        """Sort `bars` by their optional `order` field, stable.
        Bars with no explicit `order` fall back to their YAML position;
        bars with the same effective order preserve insertion order."""
        indexed = list(enumerate(self.bars))
        indexed.sort(key=lambda ib: (ib[1].order if ib[1].order is not None else ib[0], ib[0]))
        self.bars = [b for _, b in indexed]
        return self


class Location(_StrictBase):
    model_config = {"extra": "allow"}  # permit sidecar fields like _references_data

    id: str
    name: I18nText
    summary: I18nText
    fuss_order: list[str]
    # Default Krause-Mishler register for this location. Determines
    # which KM references render BARE («KM#») vs PREFIXED («KM-DK#»,
    # «KM-SH#»). When a coin's `catalog.km` is a scalar string OR a
    # single-entry KMRef whose `register` equals this value (or is
    # None), it renders bare. Cross-register or multi-KM entries
    # always render with explicit prefix + tooltip. Typical values:
    # 'DK' for denmark.yml, 'SH' for schleswig_holstein.yml. Leave
    # unset for locations where the distinction doesn't apply yet.
    km_register: str | None = None
    timeline: Timeline | None = None
    fuss_periods: dict[str, FussPeriod] = Field(default_factory=dict)  # fuss_id → per-location framing
    phases: dict[str, list[Phase]] = Field(default_factory=dict)  # fuss_id → [Phase]
    coins: list[Coin] = Field(default_factory=list)
    methodology_heading: I18nTextOptional | None = None
    methodology: I18nText | None = None

    @field_validator("coins")
    @classmethod
    def check_unique_ids(cls, v):
        ids = [c.id for c in v]
        duplicates = {x for x in ids if ids.count(x) > 1}
        if duplicates:
            raise ValueError(f"duplicate coin IDs: {duplicates}")
        return v

    def validate_cross_refs(self, fuesse: dict[str, Fuss]) -> list[str]:
        """Returns list of error messages (empty = OK). Called after schema validation."""
        errors = []
        
        # Check every coin's fuss exists
        for coin in self.coins:
            if coin.fuss not in fuesse:
                errors.append(f"coin {coin.id}: fuss '{coin.fuss}' not in shared/fuesse.yml")
                continue
            
            # Check fraction exists if given. Skip the check on the
            # `seed_unsorted` catch-all bucket — it carries coins
            # awaiting Müntzfuß classification, and a stub merged
            # with a source that DOES know its fraction (Bruun: «2 Dukat»
            # → fraction='2') is legitimate carry-over. The fraction
            # will get validated against the real fuss at Phase-4
            # auto-classifier or curator promotion time.
            if coin.fraction and coin.fuss != "seed_unsorted":
                if coin.fraction not in fuesse[coin.fuss].fractions:
                    errors.append(
                        f"coin {coin.id}: fraction '{coin.fraction}' not in "
                        f"fuss '{coin.fuss}'.fractions (available: "
                        f"{list(fuesse[coin.fuss].fractions)})"
                    )
            
            # Check phase exists
            if coin.fuss not in self.phases:
                errors.append(f"coin {coin.id}: no phases defined for fuss '{coin.fuss}'")
                continue
            
            phase_map = {p.id: p for p in self.phases[coin.fuss]}
            if coin.phase not in phase_map:
                errors.append(
                    f"coin {coin.id}: phase '{coin.phase}' not defined for fuss "
                    f"'{coin.fuss}' (available: {list(phase_map)})"
                )
                continue
            
            # Check chronology — allow slight leeway for coins dated just before the phase starts
            # (e.g., 1787 coin in a 1788 phase — these dates represent "issued for" the reform)
            ph = phase_map[coin.phase]
            if coin.year_first < ph.year_from - 1 or coin.year_first > ph.year_to + 1:
                errors.append(
                    f"coin {coin.id}: year_first={coin.year_first} outside phase "
                    f"{coin.phase} range [{ph.year_from}, {ph.year_to}]"
                )
        
        return errors
