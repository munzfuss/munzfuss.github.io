"""
Layer A → B: compute derived fields for each coin.

Pure functions over the input data. No template concerns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Coin, Fuss, Location


@dataclass
class ComputedCoin:
    """A coin with its computed numerical fields added."""
    raw: Coin                              # original input
    fuss: Fuss                           # resolved fuss reference
    weight_fein_g: float | None = None     # rough × fineness
    soll_fein_g: float | None = None       # from fuss.fractions[fraction]
    soll_rau_g: float | None = None        # for gold
    delta_g: float | None = None           # actual − target
    delta_pct: float | None = None         # delta / target × 100
    within_remedium: bool | None = None    # |delta_pct| ≤ 1.0
    implied_fuss: float | None = None     # actual Münzfuß back-computed from metal content
    has_manual_implied: bool = False      # true if fuss_refs already documents an "Ist-Wert" note
    # Catalog refs grouped by prefix; each group is (label, [values]).
    # Rendered in template, one group per line: "KM# 77, 77.1, 77.2".
    catalog_groups: list[tuple[str, list[str]]] = field(default_factory=list)
    # True if any input (weight_rough or fineness) is unverified, in which case
    # ALL derived values (weight_fein, delta, implied_fuss) inherit the (?)
    # marker — they sit on a non-primary base.
    derived_unverified: bool = False

    def __getattr__(self, name):
        """Proxy to raw for convenience."""
        return getattr(self.raw, name)


# ---------------------------------------------------------------------
# Catalog grouping — collects named fields + parses cat.others into a
# stable, prefix-grouped, deduplicated list. Used by the renderer to lay
# out the «Каталог» column with one prefix per row.
# ---------------------------------------------------------------------

import re  # noqa: E402

# Display label for each named catalog field
_NAMED_FIELDS: list[tuple[str, str]] = [
    ("km", "KM"),
    ("hede", "Hede"),
    ("sieg", "Sieg"),
    ("schou", "Schou"),
    ("lange", "Lange"),
    ("fr", "Fr"),
    ("dav", "Dav"),
    ("bruun_lot", "Bruun"),
]

# Render priority: lower = earlier. Unknown prefixes get a mid-rank.
_PREFIX_PRIORITY: dict[str, int] = {
    "KM": 10, "Hede": 20, "Sieg": 30, "Schou": 40, "Lange": 50,
    "Fr": 60,
    "Dav": 70,
    "Dav EC II": 71, "Dav EC III": 72, "Dav EC IV": 73, "Dav ECT": 74,
    "Dav Lg": 75, "Dav SG": 76, "Dav GT I": 77, "Dav CCT": 78,
    "Dav.": 75,
    "Bruun": 80,
    "MB": 100, "Weinm": 110, "AKS": 120, "C": 130,
    "Schön": 140, "Schön DM": 141, "Kahnt/Schön": 142,
    "Behr": 150, "Behr.": 150, "Brockmann": 160,
    "Bahrf": 170, "Bobzin": 180, "Hofmann": 190,
    "Jaeg": 200, "Jaeg 6 NWD": 201,
    "Aagaard": 210, "Aagaard-1": 211, "Aagaard-2": 212, "Aagaard-5": 213,
    "Saur": 220, "Diakov": 230, "Uzd": 240, "Bit": 250,
    "Brekke": 260, "Galster": 270, "Hauberg": 280,
    "Fb": 290, "J": 300,
    "N": 9999,  # Numista's own ID — always last
}

_REF_PATTERN = re.compile(r"^([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9./\- ]*?)#\s*(.+)$")


def _parse_ref(s: str) -> tuple[str | None, str]:
    """'KM# 77.1' → ('KM', '77.1'); 'foo bar' → (None, 'foo bar')."""
    m = _REF_PATTERN.match(s.strip())
    if not m:
        return None, s.strip()
    return m.group(1).strip(), m.group(2).strip()


def _compute_catalog_groups(coin: Coin) -> list[tuple[str, list[str]]]:
    """Build a list of (prefix, [values]) groups in render priority order.

    - Named fields (cat.km, cat.lange, ...) become groups by canonical label.
    - cat.others entries: 'PREFIX# value' lands in a group keyed by PREFIX.
    - cat.numista becomes the trailing 'N#' group.
    - Within each group, values are deduped (preserving order).
    - Unparseable entries (no '#') become a trailing anonymous group.
    """
    cat = coin.catalog
    groups: dict[str, list[str]] = {}
    order: list[str] = []  # first-seen order for tie-breaking

    def add(prefix: str, value: str):
        if not value:
            return
        if prefix not in groups:
            groups[prefix] = []
            order.append(prefix)
        if value not in groups[prefix]:
            groups[prefix].append(value)

    # Named fields
    for field_name, label in _NAMED_FIELDS:
        v = getattr(cat, field_name, None)
        if v:
            # Some named fields hold composite "77.1, 77.2" or "77.1 / 77.2"
            for part in re.split(r"\s*[,/]\s*", str(v)):
                if part.strip():
                    add(label, part.strip())

    # Others list — parse each
    plain_lines: list[str] = []
    for raw in cat.others or []:
        prefix, value = _parse_ref(raw)
        if prefix is None:
            plain_lines.append(value)
        else:
            add(prefix, value)

    # Numista — always last
    if cat.numista:
        add("N", str(cat.numista))

    def sort_key(prefix: str) -> tuple[int, int]:
        prio = _PREFIX_PRIORITY.get(prefix, 500)
        return (prio, order.index(prefix))

    # Drop generic "Dav" group if any specific "Dav <subprefix>" carries the
    # same values — the named field is just a less-precise duplicate of the
    # API-derived sub-catalog (e.g. cat.dav="3679 / 3679A" + others has
    # "Dav EC II# 3679" and "Dav EC II# 3679A" → keep only the EC II group).
    if "Dav" in groups:
        dav_vals = set(groups["Dav"])
        for p in list(groups.keys()):
            if p.startswith("Dav ") and dav_vals.issubset(set(groups[p])):
                del groups["Dav"]
                if "Dav" in order:
                    order.remove("Dav")
                break

    # Within each group, sort values naturally so parent types precede their
    # sub-variants (KM# 77 before 77.1, 77.2). Treat each value as a
    # tuple of numeric/string segments split by '.'/'/' so '77' sorts before '77.1'.
    def value_key(v: str):
        out = []
        for tok in re.split(r"[./\-]", v):
            t = tok.strip()
            try:
                out.append((0, int(t)))
            except (ValueError, TypeError):
                out.append((1, t))
        return out

    for p in groups:
        groups[p] = sorted(set(groups[p]), key=value_key)

    sorted_prefixes = sorted(groups.keys(), key=sort_key)
    out: list[tuple[str, list[str]]] = [(p, groups[p]) for p in sorted_prefixes]

    if plain_lines:
        out.append(("", plain_lines))

    return out


def _compute_coin(coin: Coin, fuss: Fuss) -> ComputedCoin:
    cc = ComputedCoin(raw=coin, fuss=fuss)

    # Catalog groups for the «Каталог» column
    cc.catalog_groups = _compute_catalog_groups(coin)

    # Propagate the unverified marker: any derived metric is only as solid as
    # its inputs. If the rough weight or fineness is unverified, mark all
    # downstream computations the same way.
    cc.derived_unverified = (not coin.weight_rough_verified) or (not coin.fineness_verified)

    # weight_fein from rough × fineness
    if coin.weight_rough_g is not None and coin.fineness is not None:
        cc.weight_fein_g = round(coin.weight_rough_g * coin.fineness, 5)

    # soll values from fuss fractions
    if coin.fraction and coin.fraction in fuss.fractions:
        frac = fuss.fractions[coin.fraction]
        cc.soll_fein_g = frac.soll_fein_g
        cc.soll_rau_g = frac.soll_rau_g

    # delta
    if cc.weight_fein_g is not None and cc.soll_fein_g is not None:
        cc.delta_g = round(cc.weight_fein_g - cc.soll_fein_g, 5)
        cc.delta_pct = round(cc.delta_g / cc.soll_fein_g * 100, 3)
        cc.within_remedium = abs(cc.delta_pct) <= 1.0

    # implied fuss: back-compute the standard from the coin's actual silver/gold.
    # Formula for a coin declared as fraction k of 1 Fuß-unit:
    #   full_metal_per_unit = actual_metal_g / k
    #   implied_fuss        = grid_unit_g / full_metal_per_unit
    # For Scheidemünzen this quantifies the seigniorage gap.
    if coin.fraction:
        try:
            num, _, den = coin.fraction.partition("/")
            k = float(num) / float(den) if den else float(num)
        except (ValueError, ZeroDivisionError):
            k = None
        metal_g = None
        if fuss.metal == "silver" and cc.weight_fein_g:
            metal_g = cc.weight_fein_g
        elif fuss.metal == "gold" and coin.weight_rough_g:
            metal_g = coin.weight_rough_g
        if k and metal_g and k > 0 and metal_g > 0:
            full_unit = metal_g / k
            if full_unit > 0:
                cc.implied_fuss = round(fuss.grid_unit_g / full_unit, 2)

    # Detect whether fuss_refs already documents an implied Fuß — if so,
    # templates should skip the auto-computed line to avoid duplication.
    MARKERS = ("Ist-Wert", "Ist ≈", "actual value", "фактичне значення", "Факт ")
    for ref in coin.fuss_refs or []:
        lbl = ref.label
        texts = []
        for lang in ("de", "en", "uk"):
            v = getattr(lbl, lang, None)
            if v: texts.append(str(v))
        joined = " ".join(texts)
        if any(m in joined for m in MARKERS):
            cc.has_manual_implied = True
            break

    return cc


def compute_location(
    location: Location,
    fuesse: dict[str, Fuss],
) -> list[ComputedCoin]:
    """Compute derived fields for all coins in a location."""
    computed = []
    for coin in location.coins:
        if coin.fuss not in fuesse:
            # Should have been caught in validation, but guard anyway
            continue
        computed.append(_compute_coin(coin, fuesse[coin.fuss]))
    return computed
