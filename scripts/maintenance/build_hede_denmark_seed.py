"""Build a Coin-schema seed YAML for `data/locations/denmark.yml`
from the parsed Hede catalogue cache (`scripts/cache/hede/*.json`).

Each parsed Hede entry whose mint is a Danish royal mint (København /
Frederiksborg / Helsingør) becomes a Coin-shaped entry in the seed.
Multi-Hede pages (specs.by_hede with ≥2 sub-variants) expand into one
entry per sub-Hede when the page's joined nominal can be split on the
comma-list pattern «X, Y, Z og W <Denom>»; otherwise the entry is
skipped for manual review.

Output is NOT auto-loaded by `scripts/build.py` (lives outside
`data/locations/`). The seed is a starting point — the human reviewer
pastes accepted entries into `denmark.yml` after a per-coin sanity
check, ideally reclassifying the placeholder fuss/phase to the actual
Müntzfuß window.

Conventions match the existing ucoin-derived bulk seed:
  * id: `dk-hede-<volume><number>` (e.g. `dk-hede-c5h120`)
  * fuss: `seed_unsorted`, phase: `A` — the catch-all bucket
  * All `*_verified` flags set to `false`
  * sources: type=literature pointing to the danskmoent.dk URL

Run:
    python scripts/maintenance/build_hede_denmark_seed.py
"""
from __future__ import annotations

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

PROJECT = Path(__file__).resolve().parents[2]
HEDE_CACHE = PROJECT / "scripts" / "cache" / "hede"
OUT_DIR = PROJECT / "data" / "seed" / "hede"
OUT_FILE = OUT_DIR / "denmark.yml"

# Mints we accept into the Denmark seed (matches existing denmark.yml
# convention of «Kopenhagen» across the seed_unsorted ucoin block).
# Glückstadt / Altona / Flensborg / Haderslev / Rethwitsch belong to
# the Schleswig-Holstein bucket and are filtered out; Christiansstad
# is region-ambiguous (Skåne vs Christiania) and likewise skipped here.
DK_MINT_DE = {
    "København": "Kopenhagen",
    "K�benhavn": "Kopenhagen",  # mojibake variant seen in some headers
    "Frederiksborg": "Frederiksborg",
    "Helsingør": "Helsingør",
    "København og Altona": "Kopenhagen und Altona",
}

# Roman numerals 1..10 for ruler-name rendering. Hede pages write
# «Christian 5.» / «Frederik 3.»; downstream YAML uses the standard
# numismatic Roman form.
_ARABIC_TO_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
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
_GOLD_NOMINAL_TOKENS = (
    "Dukat", "dukat", "Pistole", "pistole",
    "d'or", "Frederik d'or", "Christian d'or",
    "Guldkrone", "Kurantdukat",
)
_KRONE_GOLD_RULERS = {"Christian IX.", "Christian X.", "Frederik VIII.", "Frederik IX."}


def _infer_metal(nominal: str, ruler: str | None, fineness: float | None) -> str:
    n = (nominal or "").lower()
    if any(tok.lower() in n for tok in _GOLD_NOMINAL_TOKENS):
        return "gold"
    if re.search(r"\bkrone(r)?\b", n) and ruler in _KRONE_GOLD_RULERS:
        return "gold"
    # Speciedaler / daler / rd / rigsdaler / rigsbankdaler / mark /
    # skilling / hvid / øre — all silver or billon. Fineness gates
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


# Splits «1, 2, 3 og 4 Speciedaler» / «1 og 2 Dukat» into per-sub-Hede
# nominals. Returns a list of full denomination strings (e.g.
# ["1 Speciedaler", "2 Speciedaler", "3 Speciedaler", "4 Speciedaler"]).
_NOMINAL_LIST_RE = re.compile(
    r"^\s*(\d+(?:[\s,/]+\d+)*\s+og\s+\d+|\d+)\s+([A-Za-zæøåÆØÅ\.\- ]+?)(?:,.*)?$",
)


def _split_multi_nominal(nominal: str, count_expected: int) -> list[str] | None:
    """Return per-sub-Hede nominals when nominal is a comma-list.
    Returns None when the parse doesn't match `count_expected`."""
    if not nominal:
        return None
    m = _NOMINAL_LIST_RE.match(nominal.strip())
    if not m:
        return None
    numbers_part = m.group(1)
    denom = m.group(2).strip()
    # Strip a trailing «, København» / similar embedded into denom.
    denom = re.split(r",\s*", denom, maxsplit=1)[0].strip()
    nums = re.findall(r"\d+", numbers_part)
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
    mint_normalised: str,
) -> dict | None:
    """Assemble one Coin-schema dict from a parsed-page entry + a
    specific spec block. Returns None when essential fields are
    missing or unrecoverable (e.g. nominal parse failure)."""
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
    cm["phase"] = "A"
    cm["kind"] = kind
    cm["nominal"] = nominal
    year_block = _build_year_fields(parsed.get("years") or [])
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
        # Without years we still emit the row but flag year_label
        # as «(?)» — placeholder; user must supply on review.
        cm["year_label"] = "(?)"
        cm["year_first"] = 0  # sentinel so YAML loads; user fixes
    if ruler:
        cm["ruler"] = ruler
    cm["mint"] = mint_normalised

    catalog = CommentedMap()
    catalog["hede"] = hede_number
    catalog["hede_volume"] = hede_volume
    refs = parsed.get("catalog_refs") or {}
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
        cm["fineness_verified"] = False
    if brutto is not None:
        cm["weight_rough_verified"] = False
    cm["mint_verified"] = False
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
    parsed_files = sorted(p for p in HEDE_CACHE.glob("*.json") if not p.name.startswith("_"))
    if not parsed_files:
        print(f"No parsed JSON found in {HEDE_CACHE}", file=sys.stderr)
        return 1

    coins: list[CommentedMap] = []
    stats = {
        "considered": 0,
        "kept": 0,
        "skipped_no_mint": 0,
        "skipped_non_dk_mint": 0,
        "skipped_no_specs": 0,
        "skipped_no_nominal": 0,
        "skipped_multi_nominal_unparseable": 0,
    }
    skipped_mints: dict[str, int] = {}

    for p in parsed_files:
        d = json.loads(p.read_text(encoding="utf-8"))
        stats["considered"] += 1
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
        # Match against DK mint set
        mint_normalised = None
        for canon, normalised in DK_MINT_DE.items():
            if canon.lower() in mint_clean.lower():
                mint_normalised = normalised
                break
        if mint_normalised is None:
            stats["skipped_non_dk_mint"] += 1
            skipped_mints[mint_clean] = skipped_mints.get(mint_clean, 0) + 1
            continue

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
            coins.append(coin)
            stats["kept"] += 1
        elif "by_hede" in specs:
            by_hede = specs["by_hede"]
            # Sort by brutto weight ascending so we can pair against
            # an ordered nominal list («1, 2, 3 og 4 Speciedaler»).
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
            for (sub_num, sub_spec), nominal in zip(sub_items, nominal_parts):
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
    doc["coins"] = CommentedSeq(coins)

    header = (
        "# Hede seed for data/locations/denmark.yml — generated by\n"
        "# scripts/maintenance/build_hede_denmark_seed.py from the parsed\n"
        "# Hede cache (scripts/cache/hede/*.json).\n"
        "#\n"
        "# NOT auto-loaded by scripts/build.py (lives outside data/locations/).\n"
        "# Promotion path: paste accepted entries into the `coins:` block of\n"
        "# data/locations/denmark.yml (alongside or replacing the existing\n"
        "# seed_unsorted ucoin block), then reclassify each from fuss=seed_unsorted\n"
        "# to the actual Müntzfuß window and flip *_verified flags after a\n"
        "# per-coin sanity check against the source Hede page.\n"
        "#\n"
        "# Conventions per the existing seed_unsorted block:\n"
        "#   * fuss=seed_unsorted, phase=A (catch-all bucket)\n"
        "#   * all *_verified flags false\n"
        "#   * source: type=literature pointing to danskmoent.dk URL\n"
        "#\n"
        f"# Total coins: {len(coins)}\n"
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
