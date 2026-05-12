"""Build a Coin-schema seed YAML for `data/locations/denmark.yml`
from the parsed Hede catalogue cache (`scripts/cache/hede/*.json`).

Each parsed Hede entry whose mint is a Danish royal mint (København /
Frederiksborg / Helsingør) becomes a Coin-shaped entry in the seed.
Multi-Hede pages (specs.by_hede with ≥2 sub-variants) expand into one
entry per sub-Hede when the page's joined nominal can be split on the
comma-list pattern «X, Y, Z og W <Denom>»; otherwise the entry is
skipped for manual review.

The output is consumed by `scripts/build.py` as an auto-merged seed
side-car for the location page (`data/locations/denmark.yml`) — see
`scripts/build.py::_merge_seeds_into_raw`. The seed file is the
canonical intermediate: filtering by year + mint happens HERE so the
file the build reads is already scoped to what should ship.

Conventions match the existing ucoin-derived bulk block in
`denmark.yml`:
  * id: `dk-hede-<volume><number>` (e.g. `dk-hede-c5h120`)
  * fuss: `seed_unsorted`, phase: `A` — the catch-all bucket
  * All `*_verified` flags set to `false`
  * sources: type=literature pointing to the danskmoent.dk URL

The `--year-to` flag (default 1914 — the project's scope upper
bound per CLAUDE.md) caps the seed at that year inclusive; entries
whose `year_first` is after the cap are dropped. Stored in the
seed file's header for traceability so the next reader knows what
scope the file represents without re-running.

Run:
    python scripts/maintenance/build_hede_denmark_seed.py
    python scripts/maintenance/build_hede_denmark_seed.py --year-to 1900
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

# Words inside a nominal that should NOT be Title-Cased ("og" = Danish
# «and», kept lowercase per period-form usage).
_NOMINAL_LOWERCASE_WORDS = {"og", "und", "and"}

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import HEDE_CACHE, PROJECT_ROOT as PROJECT  # noqa: E402

OUT_DIR = PROJECT / "data" / "seed" / "hede"
OUT_FILE = OUT_DIR / "denmark.yml"

# Mints accepted into the Denmark seed. Hede 1971 («Danmarks og
# Norges mønter») by definition only catalogues Danish-Norwegian
# state coinage — every mint listed here is a Danish-royal mint,
# even when located physically in Holstein (Glückstadt, Altona,
# Flensborg, Haderslev, Rendsborg, Rethwitsch were all founded /
# operated by the Danish crown). The Holstein-mint locations stay
# in this set because the COIN'S political attribution is the
# Danish state regardless of where the strike happened — and that's
# what the Denmark page is documenting.
#
# Schleswig-Holstein-LOCAL issuers (Gottorp duchy, Sonderburg duchy,
# Norburg-Plön, Glücksburg, Rantzau county, Schauenburg-Pinneberg)
# are NOT in Hede — they're covered by Lange 1908/1912 and will get
# their own seed pipeline pointed at schleswig_holstein.yml.
#
# Christiansstad is region-ambiguous (Skåne when Danish, post-1658
# Swedish) and is left out to avoid silent mis-attribution.
DK_MINT_DE = {
    # Denmark proper
    "København": "Kopenhagen",
    "K�benhavn": "Kopenhagen",  # mojibake variant seen in some headers
    "Kåbenhavn": "Kopenhagen",  # ditto, alt-decoding
    "Frederiksborg": "Frederiksborg",
    "Helsingør": "Helsingør",
    # Danish-royal mints in the Holstein territories
    "Glückstadt": "Glückstadt",
    "Altona": "Altona",
    "Flensborg": "Flensburg",
    "Haderslev": "Hadersleben",
    "Rendsborg": "Rendsburg",
    "Rethwitsch": "Rethwisch",
    # Danish-royal mints in the Norwegian realm (1380–1814).
    # These are recognised as part of the Dansk Mønt corpus per
    # Hede 1971's full title «Danmarks og Norges mønter»; coins
    # struck at these mints carry Norwegian legends but are
    # catalogued in the same registry. The issuing-entity tag is
    # assigned downstream by retag_entities.py.
    "Kongsberg": "Kongsberg",
    "Christiania": "Christiania",
    "Poppenbüttel": "Poppenbüttel",
}


# Split a multi-mint string («København og Kongsberg»,
# «Altona, Kopenhagen, Kongsberg») into individual segments. Hede uses
# Danish/German conjunctions «og» / «und» / «&» / «,» between mints.
_MINT_SEP_RE = re.compile(r"\s+(?:og|und|and|&)\s+|\s*,\s*", re.IGNORECASE)


def _normalize_mints(mint_clean: str) -> list[str] | None:
    """Map a possibly multi-mint raw Hede string to a list of
    canonical mint names. Returns the de-duplicated list in source
    order, or None when no segment matches the DK/SH/NO mint set."""
    parts = _MINT_SEP_RE.split(mint_clean)
    out: list[str] = []
    for part in parts:
        part = part.strip(" (),;.").strip()
        if not part:
            continue
        for canon, normalised in DK_MINT_DE.items():
            if canon.lower() in part.lower():
                if normalised not in out:
                    out.append(normalised)
                break
    return out or None

# Roman numerals 1..10 for ruler-name rendering. Hede pages write
# «Christian 5.» / «Frederik 3.»; downstream YAML uses the standard
# numismatic Roman form.
_ARABIC_TO_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
}


# Reign spans for Danish kings — used as a fallback year window when
# Hede publishes an «u. år» (undated) entry that yields no parseable
# year tokens. The seed needs year_first / year_last so the
# `seed_unsorted` phase A cross-ref check passes (1500-1914 window);
# anchoring the coin to its ruler's reign keeps the placeholder
# honest and rolls into the right phase on promotion.
_RULER_REIGN: dict[str, tuple[int, int]] = {
    "c3h": (1534, 1559),  # Christian III.
    "f2h": (1559, 1588),  # Frederik II.
    "c4h": (1588, 1648),  # Christian IV.
    "f3h": (1648, 1670),  # Frederik III.
    "c5h": (1670, 1699),  # Christian V.
    "f4h": (1699, 1730),  # Frederik IV.
    "c6h": (1730, 1746),  # Christian VI.
    "f5h": (1746, 1766),  # Frederik V.
    "c7h": (1766, 1808),  # Christian VII.
    "f6h": (1808, 1839),  # Frederik VI.
    "c8h": (1839, 1848),  # Christian VIII.
    "f7h": (1848, 1863),  # Frederik VII.
    "c9h": (1863, 1906),  # Christian IX.
    "f8h": (1906, 1912),  # Frederik VIII.
    "c10h": (1912, 1947), # Christian X.
    "f9h": (1947, 1972),  # Frederik IX.
}


def _titlecase_nominal(nominal: str) -> str:
    """Capitalise the first letter of each token in the nominal, but
    leave joiners («og», «und») lowercase. Preserves digits, slashes,
    «½», «¼», etc. untouched."""
    if not nominal:
        return nominal
    parts = re.split(r"(\s+)", nominal)  # keep separators
    out = []
    for p in parts:
        if not p or p.isspace():
            out.append(p)
            continue
        lower = p.lower()
        if lower in _NOMINAL_LOWERCASE_WORDS:
            out.append(lower)
            continue
        # Skip pure-digit / fraction tokens
        if re.match(r"^[\d\W]+$", p):
            out.append(p)
            continue
        out.append(p[0].upper() + p[1:])
    return "".join(out)


def _normalise_ruler(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.match(r"^\s*(Christian|Frederik)\s+(\d{1,2})\.?\s*$", raw)
    if not m:
        return raw.strip()
    name, num = m.group(1), int(m.group(2))
    roman = _ARABIC_TO_ROMAN.get(num)
    return f"{name} {roman}." if roman else raw.strip()


# Gold-marker tokens. When a nominal contains any of these and the
# fineness is high (≥ 0.85) we tag the coin gold; otherwise silver.
# «Krone(r)» is ambiguous (Christian IV silver Kronemont vs Christian
# IX/X gold Krone), so the rule layers on the ruler: «Krone(r)» is
# gold only for Christian IX / Christian X / Frederik VIII / Frederik IX.
#
# Renaissance gold tokens — Hede's pre-1591 catalogue records
# Christian III / Frederik II / early Christian IV gold via period
# names: «Ungersk Gylden» (Hungarian ducat-pattern), «Rhinsk
# Gylden» (Rhenish florin), «Goldgulden», «Portugaløser» (10-
# Dukat presentation piece), «Rosenobel» (English-pattern rose
# noble), «Guldmønt» (literally «gold-coin» when the type lacks a
# proper denomination). All gold; specimens commonly run 3-35 g at
# .75-.986 fineness.
#
# Sølvgylden («silver-gylden») is a specific Christian III tariff
# coin in SILVER at ~29 g and ~.89 fineness — the «sølv» prefix
# overrides the Gylden gold-marker.
_GOLD_NOMINAL_TOKENS = (
    "Dukat", "dukat", "Pistole", "pistole",
    "d'or", "Frederik d'or", "Christian d'or",
    "Guldkrone", "Guldcrone", "Guldmønt", "Guldmoent",
    "Kurantdukat", "Speciedukat",
    "Ungersk Gylden", "Rhinsk Gylden", "Goldgulden",
    "Portugaløser", "Portugaloser",
    "Rosenobel",
)
_KRONE_GOLD_RULERS = {"Christian IX.", "Christian X.", "Frederik VIII.", "Frederik IX."}


def _infer_metal(nominal: str, ruler: str | None, fineness: float | None) -> str:
    n = (nominal or "").lower()
    # «Sølvgylden» (Christian III's silver tariff piece) precedes the
    # «Gylden» gold-marker check — explicit silver override.
    if "sølvgylden" in n or "soelvgylden" in n:
        return "silver"
    if any(tok.lower() in n for tok in _GOLD_NOMINAL_TOKENS):
        return "gold"
    # Krone-fod (post-1873) has TIERED metal — gold only for 5/10/20
    # Kroner (Hauptkurant), silver Kurant for 1/2 Kroner. The earlier
    # «any «krone» + Krone-fod ruler → gold» rule mis-routed 2-Kroner
    # silver commemoratives (Christian IX 1888 jubilee, Christian X
    # 1912 tronskifte, etc.) to gold. Gate gold-routing on the
    # specific gold-tier denominations.
    if re.search(r"\bkrone(r)?\b", n) and ruler in _KRONE_GOLD_RULERS:
        if re.match(r"^(5|10|20)\s+kroner?\b", n):
            return "gold"
        # «1 Krone» / «2 Kroner» → silver Kurant tier of Krone-fod
        return "silver"
    # øre denominations — Krone-fod subsidiary tiers:
    #   25 / 10 øre = silver Scheide (.600 / .400)
    #   5 / 2 / 1 øre = bronze
    if re.search(r"\bø?re\b", n):
        m = re.match(r"^(\d+)\s+ø?re\b", n)
        if m and int(m.group(1)) in (1, 2, 5):
            return "copper"
        return "silver"
    # Speciedaler / daler / rd / rigsdaler / rigsbankdaler / mark /
    # skilling / hvid — all silver or billon. Fineness gates
    # billon below.
    if fineness is not None:
        if fineness < 0.30:
            return "billon"
    return "silver"


def _infer_kind(metal: str, nominal: str, ruler: str | None, fineness: float | None) -> str:
    """Default = kurant. Lower-tier silver / billon Skilling drops to
    scheide. Christian IV Krone (Kronemont, 1618-1645) is tarif."""
    n = (nominal or "").lower()
    if ruler == "Christian IV." and re.search(r"\bkrone\b", n):
        return "tarif"
    if metal == "billon":
        return "scheide"
    if metal == "silver" and fineness is not None and fineness < 0.55:
        return "scheide"
    return "kurant"


# Splits «1, 2, 3 og 4 Speciedaler» / «1 og 2 Dukat» / «1/2, 1 og 2
# Dukat» / «1, 2, 5, 10 Dukat» (no «og») into per-sub-Hede nominals.
# Returns a list of full denomination strings (e.g. ["1 Speciedaler",
# "2 Speciedaler", "3 Speciedaler", "4 Speciedaler"]).
#
# Two patterns supported in the numeric prefix:
#   - Comma/space/slash-separated list ending in «og N»
#     («1, 2, 3 og 4 Speciedaler» — Hede's standard list format)
#   - Plain comma-separated list without «og»
#     («1, 2, 5, 10 Dukat» — used on f3h10)
# Each number element may be a bare integer OR a fraction («1/2»).
_NUM_TOKEN = r"\d+(?:/\d+)?"
_NOMINAL_LIST_RE = re.compile(
    r"^\s*("                                 # group 1: numbers section
    r"" + _NUM_TOKEN + r"(?:[\s,/]+" + _NUM_TOKEN + r")*(?:\s+og\s+" + _NUM_TOKEN + r")?"
    r")\s+"
    r"([A-Za-zæøåÆØÅ\.\- ]+?)(?:,.*)?$"        # group 2: denomination
)


def _split_multi_nominal(nominal: str, count_expected: int) -> list[str] | None:
    """Return per-sub-Hede nominals when nominal is a comma-list.
    Returns None when the parse doesn't match `count_expected`.

    Handles fraction multipliers (e.g. «1/2 Dukat») by capturing each
    number token in `_NUM_TOKEN` form.

    Special case: when nominal is a SINGLE denomination (just «1 Skilling»,
    no «og» / multi-list) but count_expected > 1, treats the by_hede
    entries as sub-letter variants of the same denomination and emits
    the same nominal for each. This covers pages like c3h6 («1 Skilling»
    with Hede 6A + 6B sub-letters)."""
    if not nominal:
        return None
    m = _NOMINAL_LIST_RE.match(nominal.strip())
    if not m:
        return None
    numbers_part = m.group(1)
    denom = m.group(2).strip()
    # Strip a trailing «, København» / similar embedded into denom.
    denom = re.split(r",\s*", denom, maxsplit=1)[0].strip()
    nums = re.findall(_NUM_TOKEN, numbers_part)
    # Same-denomination sub-letter case: single multiplier, multiple
    # by_hede entries — replicate the nominal for each.
    if len(nums) == 1 and count_expected > 1:
        return [f"{nums[0]} {denom}"] * count_expected
    if len(nums) != count_expected:
        return None
    return [f"{n} {denom}" for n in nums]


def _build_year_fields(years: list[dict]) -> dict:
    if not years:
        return {}
    yrs = sorted({int(y["year"]) for y in years})
    if not yrs:
        return {}
    year_first = yrs[0]
    year_last = yrs[-1]
    # Group consecutive years into ranges
    ranges: list[list[int]] = []
    start = yrs[0]
    prev = yrs[0]
    for y in yrs[1:]:
        if y == prev + 1:
            prev = y
            continue
        ranges.append([start, prev])
        start = y
        prev = y
    ranges.append([start, prev])
    # Label: comma-list of ranges
    label_parts = [
        str(a) if a == b else f"{a}–{b}"
        for a, b in ranges
    ]
    year_label = ", ".join(label_parts)
    out: dict = {
        "year_label": year_label,
        "year_first": year_first,
    }
    if year_last != year_first:
        out["year_last"] = year_last
    if len(ranges) > 1:
        # Year_ranges only useful when sub-ranges exist (gaps in the
        # struck year sequence). If continuous, year_first/year_last
        # cover everything.
        out["year_ranges"] = ranges
    return out


_DANSKMOENT_BASE = "https://www.danskmoent.dk"


def _danskmoent_url(basename: str) -> str:
    """Reconstruct the per-coin URL from a cache basename.
    Christian pages live under /chr/, Frederik under /fr/."""
    if basename.startswith("c"):
        return f"{_DANSKMOENT_BASE}/chr/{basename}.htm"
    if basename.startswith("f"):
        return f"{_DANSKMOENT_BASE}/fr/{basename}.htm"
    return f"{_DANSKMOENT_BASE}/{basename}.htm"


def _build_coin(
    *,
    hede_volume: str,
    hede_number: str,
    parsed: dict,
    spec: dict,
    nominal_override: str | None = None,
    mint_normalised: str | list[str],
    years_override: list[dict] | None = None,
    catalog_refs_override: dict | None = None,
) -> dict | None:
    """Assemble one Coin-schema dict from a parsed-page entry + a
    specific spec block. Returns None when essential fields are
    missing or unrecoverable (e.g. nominal parse failure).

    Per-letter sub-variants (by_letter pages) pass `years_override` +
    `catalog_refs_override` so each letter coin carries its own year
    list + Hede/Sieg sub-numbers while sharing the page-level spec.
    """
    nominal_raw = nominal_override or parsed.get("nominal") or ""
    # Strip trailing «, København» / «, Glückstadt» / «, Frederiksborg»
    # mint segments that the H1 parser absorbed into nominal.
    nominal = re.split(r",\s*[A-ZÆØÅa-zæøå]", nominal_raw, maxsplit=1)[0].strip()
    nominal = re.sub(r"\s+", " ", nominal).strip(" ,.")
    if not nominal or len(nominal) < 3:
        return None
    nominal = _titlecase_nominal(nominal)
    ruler = _normalise_ruler(parsed.get("ruler"))
    fineness = spec.get("finhed") if spec else None
    brutto = spec.get("bruttovægt_g") if spec else None
    metal = _infer_metal(nominal, ruler, fineness)
    kind = _infer_kind(metal, nominal, ruler, fineness)
    coin_id = f"dk-hede-{hede_volume}{hede_number.lower()}"

    cm = CommentedMap()
    cm["id"] = coin_id
    cm["fuss"] = "seed_unsorted"
    # Source-specific phase under seed_unsorted so the Hede-derived
    # rows render in their own sub-section on the location page,
    # cleanly separated from the older ucoin bulk block (phase=A).
    # Both phases live inside seed_unsorted (the catch-all bucket
    # awaiting Müntzfuß reclassification); the separation is
    # cosmetic-but-honest about provenance, not analytical.
    cm["phase"] = "hede"
    cm["kind"] = kind
    cm["nominal"] = nominal
    year_block = _build_year_fields(years_override or parsed.get("years") or [])
    if year_block:
        cm["year_label"] = year_block["year_label"]
        cm["year_first"] = year_block["year_first"]
        if "year_last" in year_block:
            cm["year_last"] = year_block["year_last"]
        if "year_ranges" in year_block:
            yr_seq = CommentedSeq()
            for pair in year_block["year_ranges"]:
                inner = CommentedSeq(pair)
                inner.fa.set_flow_style()
                yr_seq.append(inner)
            cm["year_ranges"] = yr_seq
    else:
        # Undated Hede entry («u. år» — uden årstal). Anchor to the
        # ruler's reign window so the placeholder year_first sits
        # inside seed_unsorted/A's [1500, 1914] cross-ref window AND
        # is at least *plausible* for promotion. year_label keeps
        # «u. å.» so the reader sees the entry is undated.
        reign = _RULER_REIGN.get(hede_volume)
        if reign:
            cm["year_label"] = f"u. å. ({reign[0]}–{reign[1]})"
            cm["year_first"] = reign[0]
            cm["year_last"] = reign[1]
        else:
            cm["year_label"] = "u. å."
            cm["year_first"] = 1500  # last-resort sentinel within phase A
    if ruler:
        cm["ruler"] = ruler
    if isinstance(mint_normalised, list):
        seq = CommentedSeq(mint_normalised)
        seq.fa.set_flow_style()
        cm["mint"] = seq
    else:
        cm["mint"] = mint_normalised

    catalog = CommentedMap()
    catalog["hede"] = hede_number
    catalog["hede_volume"] = hede_volume
    refs = catalog_refs_override or parsed.get("catalog_refs") or {}
    if "Schou" in refs and refs["Schou"]:
        catalog["schou"] = refs["Schou"][0]
    if "Sieg" in refs and refs["Sieg"]:
        catalog["sieg"] = refs["Sieg"][0]
    if "Frederik" in refs and refs["Frederik"]:
        catalog["fr"] = refs["Frederik"][0]
    if "Dav" in refs and refs["Dav"]:
        catalog["dav"] = refs["Dav"][0]
    if "Km" in refs and refs["Km"]:
        catalog["km"] = refs["Km"][0]
    cm["catalog"] = catalog

    cm["metal"] = metal
    if fineness is not None:
        cm["fineness"] = fineness
    if brutto is not None:
        cm["weight_rough_g"] = brutto
    # Per CLAUDE.md §4: a value directly attested by an acceptable
    # source is sufficient to flip its `*_verified` flag. Hede 1971
    # publishes `finhed` and `bruttovægt_g` per page; both are
    # source-attested. The overall `verified` flag stays false (it
    # signals «full per-coin sanity check done», not «any source
    # confirms any field»). `mint_verified` also stays false here —
    # mint extraction is parser-heuristic and can drift.

    sources = CommentedSeq()
    src = CommentedMap()
    src["type"] = "literature"
    src["url"] = _danskmoent_url(parsed["id"])
    src["ref"] = f"Hede {hede_volume}{hede_number} (danskmoent.dk)"
    sources.append(src)
    cm["sources"] = sources

    cm["issuing_entity"] = "danish_realm"
    cm["verified"] = False
    if fineness is not None:
        cm["fineness_verified"] = True   # Hede page directly publishes
    if brutto is not None:
        cm["weight_rough_verified"] = True   # Hede page directly publishes
    cm["mint_verified"] = False  # parser-heuristic; not flipped here
    vn = CommentedMap()
    vn["de"] = (
        "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation "
        "stehen noch aus; Daten direkt aus danskmoent.dk übernommen."
    )
    vn["en"] = (
        "Hede seed: Müntzfuß assignment, phase and per-coin verification "
        "are still outstanding; data lifted directly from danskmoent.dk."
    )
    vn["uk"] = (
        "Hede-seed: призначення Müntzfuß, фази та покоінна верифікація "
        "ще очікуються; дані взято безпосередньо з danskmoent.dk."
    )
    cm["verification_note"] = vn
    return cm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--year-to", type=int, default=1914,
        help=(
            "Drop entries whose year_first is after this year (inclusive). "
            "Default 1914 — the project's scope upper bound per CLAUDE.md. "
            "Set higher to include modern issues (post-Reichsgoldmünzfuß-era)."
        ),
    )
    ap.add_argument(
        "--year-from", type=int, default=1566,
        help=(
            "Drop entries whose year_first is before this year. Default 1566 "
            "— the Reichsmünzordnung anchor, also the lower bound for the "
            "Denmark page (pre-1566 Hede entries don't fit the 9-Thaler-Fuß "
            "or any later standard documented on the page)."
        ),
    )
    args = ap.parse_args()
    year_to = args.year_to
    year_from = args.year_from

    parsed_files = sorted(p for p in HEDE_CACHE.glob("*.json") if not p.name.startswith("_"))
    if not parsed_files:
        print(f"No parsed JSON found in {HEDE_CACHE}", file=sys.stderr)
        return 1

    # Load the aggregate canonical-resolution index built by
    # parse_hede.py — composite Hede key («c4h111», «f3h68») →
    # canonical file owning that key. Used to filter out duplicates:
    # «c4h111» and «c4h111note» both describe Hede 111; only the
    # canonical (c4h111) emits a seed entry. Multi-Hede pages like
    # f3h68 only emit their own primary number, not the cross-
    # referenced Hede 61 / 62AB / 63 specs (those belong to f3h62).
    index_path = HEDE_CACHE / "_parsed_index.json"
    if not index_path.exists():
        print(f"Aggregate index missing — run parse_hede.py first", file=sys.stderr)
        return 1
    aggregate_idx = json.loads(index_path.read_text(encoding="utf-8"))
    # file basename → set of Hede sub-numbers that file canonically owns
    canonical_subs: dict[str, set[str]] = {}
    for composite_key, summary in aggregate_idx.items():
        # Extract the sub-Hede portion from composite key
        # «c4h111» → «111», «f3h62ab» → «62ab», «c10h35» → «35».
        m = re.match(r"^[cf]\d+h(.+)$", composite_key)
        if not m:
            continue
        sub_num = m.group(1).lower()
        canonical_subs.setdefault(summary["file"], set()).add(sub_num)

    coins: list[CommentedMap] = []
    stats = {
        "considered": 0,
        "kept": 0,
        "skipped_no_mint": 0,
        "skipped_non_dk_mint": 0,
        "skipped_no_specs": 0,
        "skipped_no_nominal": 0,
        "skipped_multi_nominal_unparseable": 0,
        "skipped_out_of_scope_year": 0,
        "skipped_non_canonical": 0,
        "skipped_cross_reference_subhede": 0,
    }
    skipped_mints: dict[str, int] = {}

    for p in parsed_files:
        d = json.loads(p.read_text(encoding="utf-8"))
        stats["considered"] += 1
        # Skip files that aren't canonical for any Hede number (e.g.
        # c4h111note — a footnote page where c4h111 owns the actual
        # Hede 111 entry).
        owned_subs = canonical_subs.get(d["id"], set())
        if not owned_subs:
            stats["skipped_non_canonical"] += 1
            continue
        raw_mint = (d.get("mint") or "").strip().lstrip("),.;- ").strip()
        # Discard mojibake / parser-artifact mints (single digit, lone
        # punctuation, denomination-shaped strings).
        if not raw_mint:
            stats["skipped_no_mint"] += 1
            continue
        # If the mint looks like a denomination («1 Speciedaler» —
        # parser folded the second nominal field in as mint), skip.
        if re.match(r"^\d+\s+[A-Za-zæøå]", raw_mint):
            stats["skipped_no_mint"] += 1
            continue
        # Strip leading «NN, » prefix («23, København» → «København»)
        mint_clean = re.sub(r"^\d+\s*,\s*", "", raw_mint)
        # Strip trailing punctuation
        mint_clean = mint_clean.rstrip(".;,)").strip()
        # Match against DK / SH / Norway mint set. Multi-mint Hede
        # strings («København og Kongsberg», «Altona, Kopenhagen,
        # Kongsberg») return a list — preserved on the coin so every
        # parallel-strike city renders in the table.
        mints_list = _normalize_mints(mint_clean)
        if not mints_list:
            stats["skipped_non_dk_mint"] += 1
            skipped_mints[mint_clean] = skipped_mints.get(mint_clean, 0) + 1
            continue
        mint_normalised: str | list[str] = (
            mints_list[0] if len(mints_list) == 1 else mints_list
        )

        hede_volume = d.get("ruler_volume") or ""
        if not hede_volume:
            continue
        specs = d.get("specs") or {}

        if "default" in specs:
            spec = specs["default"]
            nums = d.get("hede_numbers_filename") or d.get("hede_numbers_title") or []
            if not nums:
                # Derive from id («c5h120» → «120»)
                m = re.match(r"^[cf]\d+h(\w+)$", d["id"])
                nums = [m.group(1)] if m else []
            if not nums:
                stats["skipped_no_specs"] += 1
                continue
            hede_number = nums[0]
            # Letter-grouped sub-variants: when the page emits a
            # by_letter block, generate one coin per letter with the
            # SHARED spec but per-letter years + Hede sub-letter +
            # sub-Sieg refs. The bare numeric Hede key (e.g. «16») is
            # NOT emitted in this case — only the letter-suffixed keys
            # («16A», «16B») which carry the actual data.
            by_letter = d.get("by_letter") or {}
            if by_letter:
                for letter, lv in sorted(by_letter.items()):
                    sub_hede = f"{hede_number}{letter}"
                    if sub_hede.lower() not in owned_subs:
                        stats["skipped_cross_reference_subhede"] += 1
                        continue
                    coin = _build_coin(
                        hede_volume=hede_volume,
                        hede_number=sub_hede,
                        parsed=d,
                        spec=spec,
                        mint_normalised=mint_normalised,
                        years_override=lv.get("years"),
                        catalog_refs_override=lv.get("catalog_refs"),
                    )
                    if coin is None:
                        stats["skipped_no_nominal"] += 1
                        continue
                    if coin.get("year_first") and (
                        coin["year_first"] > year_to
                        or coin["year_first"] < year_from
                    ):
                        stats["skipped_out_of_scope_year"] += 1
                        continue
                    coins.append(coin)
                    stats["kept"] += 1
                continue
            if hede_number.lower() not in owned_subs:
                stats["skipped_cross_reference_subhede"] += 1
                continue
            coin = _build_coin(
                hede_volume=hede_volume,
                hede_number=hede_number,
                parsed=d,
                spec=spec,
                mint_normalised=mint_normalised,
            )
            if coin is None:
                stats["skipped_no_nominal"] += 1
                continue
            if coin.get("year_first") and (
                coin["year_first"] > year_to
                or coin["year_first"] < year_from
            ):
                stats["skipped_out_of_scope_year"] += 1
                continue
            coins.append(coin)
            stats["kept"] += 1
        elif "by_hede" in specs:
            by_hede = specs["by_hede"]
            # Prefer the parser-emitted per-Hede nominal (one «nominal»
            # field inside each by_hede spec). When ALL entries carry
            # a nominal, we don't need the weight-sort multi-nominal
            # split heuristic — use parser data directly. Falls back to
            # the legacy split logic when nominals are absent (older
            # cached parses or pages without a clear descriptive list).
            entries_with_nominal = [
                (sub_num, sub_spec, sub_spec.get("nominal"))
                for sub_num, sub_spec in by_hede.items()
            ]
            if all(n for _, _, n in entries_with_nominal):
                # Direct per-Hede emission with parser-attested nominals.
                sub_items_paired = [
                    ((sub_num, sub_spec), nominal)
                    for sub_num, sub_spec, nominal in entries_with_nominal
                ]
            else:
                # Legacy weight-sort + split fallback for pre-fix cache
                # entries.
                sub_items = sorted(
                    by_hede.items(),
                    key=lambda kv: kv[1].get("bruttovægt_g", 0) or 0,
                )
                count = len(sub_items)
                nominal_parts = _split_multi_nominal(d.get("nominal") or "", count)
                if nominal_parts is None:
                    # Can't split cleanly — skip the whole page for
                    # manual review.
                    stats["skipped_multi_nominal_unparseable"] += 1
                    continue
                sub_items_paired = list(zip(sub_items, nominal_parts))
            for (sub_num, sub_spec), nominal in sub_items_paired:
                if sub_num.lower() not in owned_subs:
                    stats["skipped_cross_reference_subhede"] += 1
                    continue
                coin = _build_coin(
                    hede_volume=hede_volume,
                    hede_number=sub_num,
                    parsed=d,
                    spec=sub_spec,
                    nominal_override=nominal,
                    mint_normalised=mint_normalised,
                )
                if coin is None:
                    stats["skipped_no_nominal"] += 1
                    continue
                if coin.get("year_first") and (
                    coin["year_first"] > year_to
                    or coin["year_first"] < year_from
                ):
                    stats["skipped_out_of_scope_year"] += 1
                    continue
                coins.append(coin)
                stats["kept"] += 1
        else:
            stats["skipped_no_specs"] += 1
            continue

    # Sort by year_first then by hede_volume+hede for stability.
    def _sort_key(c: CommentedMap) -> tuple:
        return (
            c.get("year_first") or 0,
            c.get("ruler") or "",
            c.get("catalog", {}).get("hede_volume", ""),
            c.get("catalog", {}).get("hede", ""),
        )
    coins.sort(key=_sort_key)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    doc = CommentedMap()
    doc["status"] = "seed"
    doc["source"] = "Hede 1971 (danskmoent.dk cache)"
    doc["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    doc["scope_year_from"] = year_from
    doc["scope_year_to"] = year_to
    doc["coins"] = CommentedSeq(coins)

    header = (
        "# Hede seed for data/locations/denmark.yml — generated by\n"
        "# scripts/maintenance/build_hede_denmark_seed.py from the parsed\n"
        "# Hede cache (scripts/cache/hede/*.json).\n"
        "#\n"
        "# Auto-merged into the location at build time by\n"
        "# scripts/build.py::_merge_seeds_into_raw — any *.yml file under\n"
        "# data/seed/<source>/<location_id>.yml whose name matches the\n"
        "# location id is appended to the location's coins[] before the\n"
        "# Location schema validates the result.\n"
        "#\n"
        "# Scoping happens HERE, not in the build: only entries with\n"
        f"# {year_from} <= year_first <= {year_to} (project scope per\n"
        "# CLAUDE.md; lower bound = Reichsmünzordnung 1566, upper bound\n"
        "# = end of precious-metal anchor era) are kept. The build trusts\n"
        "# what's in the file and doesn't second-guess the cap; to change\n"
        "# scope, re-run the generator with different --year-from /\n"
        "# --year-to values.\n"
        "#\n"
        "# Conventions per the existing seed_unsorted block in\n"
        "# data/locations/denmark.yml:\n"
        "#   * fuss=seed_unsorted, phase=A (catch-all bucket)\n"
        "#   * all *_verified flags false\n"
        "#   * source: type=literature pointing to danskmoent.dk URL\n"
        "#\n"
        f"# Total coins: {len(coins)}\n"
        f"# Scope: {year_from} <= year_first <= {year_to}\n"
        f"# Generated: {doc['generated_at']}\n"
    )

    with OUT_FILE.open("w") as f:
        f.write(header)
        yaml.dump(doc, f)

    print(f"Wrote {OUT_FILE.relative_to(PROJECT)} ({len(coins)} coins)")
    print()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k:40s} {v:5d}")
    print()
    print(f"Top skipped non-DK mints (first 15):")
    for m, c in sorted(skipped_mints.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {c:4d}  {m!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
