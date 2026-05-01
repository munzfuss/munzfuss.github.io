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
    """Five canonical historical events per stope.

    These atomic events are the source of truth. The three nested
    period types (visible as ▓ ⊂ ▒ ⊂ ░ in the timeline schematic)
    are derived from them:

      mint         = [first_mint, last_mint]                   (▓)
      status       = [first_adoption, std_end]                 (▒)
      circulation  = [first_adoption, demonetisation]          (░)

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
    grid_stops: float = Field(..., description="E.g., 9.25 for 9¼-Fuß")
    fineness_standard: float = Field(..., ge=0.0, le=1.0)
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
    """Per-location framing of a single Müntzfuß: validity range + background + closing summary."""
    pdate_label: I18nText | None = None      # .pdate — e.g. "Geltungsbereich in Holstein: ca. 1625 → 24. Aug. 1866 · ca. 240 Jahre"
    hintergrund: I18nText | None = None      # .psub — short summary (1–3 sentences) shown in the fuss title block
    details: I18nText | None = None          # .fuss-hintergrund — long-form historical context, rendered inside the «Деталі» toggle
    closing: I18nText | None = None          # .terr summary block rendered after the last phase
    closing_label: I18nTextOptional | None = None  # small uppercase .tlb inside .terr


class CatalogRefs(_StrictBase):
    km: str | None = None
    lange: str | None = None
    hede: str | None = None
    sieg: str | None = None
    schou: str | None = None
    fr: str | None = None
    dav: str | None = None
    bruun_lot: str | None = None
    numista: str | None = None
    others: list[str] = Field(default_factory=list)


class Source(_StrictBase):
    type: Literal["numista", "auction", "museum", "literature", "web", "other"] = "other"
    url: str | None = None
    ref: str | None = None
    note: str | None = None


class FussRef(_StrictBase):
    """One line in the Fuß-column for a coin (primary / secondary / tertiary).
    Used for dual- or triple-denominated coins where the same silver content
    simultaneously expresses a fraction of several Müntzfüße."""
    rank: Literal["primary", "secondary", "tertiary", "plain"] = "plain"
    label: I18nText


class Coin(_StrictBase):
    id: str
    fuss: str = Field(..., description="FK to shared/fuesse.yml")
    phase: str = Field(..., description="FK to location.phases[fuss]")
    kind: Literal["kurant", "scheide", "tarif", "tarif_subunit", "gedenk"]
    nominal: str = Field(..., description="Literal inscription or closest transcription")
    year_label: str
    year_first: int
    year_last: int | None = None
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
    mint: str | None = None
    mint_verified: bool = True
    mintmaster: str | None = None
    catalog: CatalogRefs = Field(default_factory=CatalogRefs)
    metal: Literal["silver", "gold", "billon", "copper"] | None = None
    fineness: float | None = Field(None, ge=0.0, le=1.0)
    fineness_verified: bool = True
    weight_rough_g: float | None = Field(None, gt=0)
    weight_rough_label: I18nTextOptional | None = None
    weight_rough_verified: bool = True
    diameter_mm: float | None = Field(None, gt=0)
    diameter_mm_verified: bool = True
    fraction: str | None = Field(None, description="E.g., '1/12' — lookup key in fuss.fractions")
    issuing_entity: str | None = Field(None, description="FK to data/i18n/issuing_entities.yml — political entity that struck the coin")
    fuss_refs: list[FussRef] = Field(default_factory=list,
        description="Multi-rank Fuß labels (for dual- or triple-denominated coins)")
    inscription_obv: str | None = None
    inscription_rev: str | None = None
    note: I18nText | None = None
    sources: list[Source] = Field(default_factory=list)
    verified: bool = True
    verification_note: I18nText | None = None

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


class TimelineBar(_StrictBase):
    id: str
    label: I18nText
    small: I18nTextOptional | None = None
    year_from: int
    year_to: int
    bar_label: I18nTextOptional | None = None
    bar_title: I18nTextOptional | None = None
    color_class: str = "si"   # CSS modifier: si, sh, rb, kr, krm, vt, rm, g
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


class Timeline(_StrictBase):
    title: I18nText
    year_from: int
    year_to: int
    axis_step: int = 50
    bars: list[TimelineBar] = Field(default_factory=list)


class Location(_StrictBase):
    model_config = {"extra": "allow"}  # permit sidecar fields like _references_data

    id: str
    name: I18nText
    summary: I18nText
    fuss_order: list[str]
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
            
            # Check fraction exists if given
            if coin.fraction:
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
