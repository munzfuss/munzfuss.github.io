"""
Stage 3 — classify every parsed lot into a territory bucket.

Inputs:  scripts/cache/bruun/lots/*.json (all parts auto-discovered)
Outputs: scripts/cache/bruun/scope.json
         — single dict: {bucket: [lots]} with `bucket` and `exclusions` fields
           added to each lot

Buckets:
  - denmark              → data/locations/denmark.yml (existing)
  - schleswig_holstein   → data/locations/schleswig_holstein.yml (existing)
                           covers ALL SH duchies: Gottorp, Sonderburg, Norburg-Plön,
                           Glücksburg, Schaumburg-Pinneberg, Rantzau, Augustenburg
  - lubeck_bishopric     → data/locations/lubeck_bishopric.yml (Eutin prince-bishopric)
  - bremen_verden        → data/locations/bremen_verden.yml (Bremervörde + Stade)
  - hesse_kassel         → data/locations/hesse_kassel.yml
  - osnabrueck           → data/locations/osnabrueck.yml
  - oldenburg            → data/locations/oldenburg.yml
  - brunswick_lueneburg  → data/locations/brunswick_lueneburg.yml (Wolfenbüttel)
  - OUT                  Norway-only / Sweden-only / GB / Russia / Poland / etc.

Exclusions (per §9 inclusion criteria + project window):
  - patterns / probes / essais / Pn-prefix
  - medals / jetons
  - medieval pennies (Hauberg / Galster prefixes)
  - year < 1566 or year > 1914
  - undated lots without a recoverable year

Re-run after stage 02 produces new lots/{partN}.json. Re-bucket-categorise
existing parts is also free (no API calls) — adjust classify_extended() and
re-run.
"""
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

CACHE_DIR = Path(__file__).resolve().parents[2] / "scripts" / "cache" / "bruun"
LOTS_DIR = CACHE_DIR / "lots"
OUT_DIR = CACHE_DIR

PROJECT_YEAR_MIN = 1566
PROJECT_YEAR_MAX = 1914

MEDIEVAL_RE = re.compile(
    r"\b(Penny|Witten|Hvid|Sterling|Bracteate|Semi[- ]Bracteate|Hauberg|Hbg)\b",
    re.IGNORECASE,
)

PATTERN_RE = re.compile(r"\b(Pattern|Probe|Essai|Trial|Probestrike)\b", re.IGNORECASE)
MEDAL_RE = re.compile(r"\b(Medal(?:lion)?\b|Medaille|Jeton|Token)", re.IGNORECASE)


def classify_extended(lot: dict) -> tuple[str, list[str]]:
    """Return (bucket, exclusion_reasons[]).
    Buckets: denmark, schleswig_holstein, lubeck_bishopric, bremen_verden,
             hesse_kassel, osnabrueck, oldenburg, brunswick_lueneburg, OUT."""
    excl = []
    region = (lot.get("region") or "").upper()
    meta = lot.get("meta_line") or ""
    mint = lot.get("mint") or ""
    body = lot.get("body_excerpt") or ""

    # Patterns / medals
    if lot.get("refs", {}).get("Pn"):
        excl.append("pattern (Pn-ref)")
    if PATTERN_RE.search(meta) or PATTERN_RE.search(body[:200]):
        excl.append("pattern keyword")
    if MEDAL_RE.search(meta):
        excl.append("medal/jeton")
    if MEDIEVAL_RE.search(meta[:200]):
        excl.append("medieval")

    # Year window (strict)
    year = lot.get("year")
    if not year:
        excl.append("no year")
    elif year < PROJECT_YEAR_MIN:
        excl.append(f"pre-{PROJECT_YEAR_MIN} ({year})")
    elif year > PROJECT_YEAR_MAX:
        excl.append(f"post-{PROJECT_YEAR_MAX} ({year})")

    # Bucket — order matters
    bucket = "OUT"

    body_head = (lot.get("body_excerpt") or "")[:300]
    full_classify_text = f"{meta}\n{body_head}"

    # -1. Lübeck (Bishopric) — issuer takes precedence over mint location (e.g. Lübeck Bishop
    #     could mint at Bremervörde or Eutin or Kaltenhof — coin still belongs to Lübeck-Bishopric)
    if (
        re.search(r"Lübeck \(Bishop|Luebeck \(Bishop", full_classify_text, re.IGNORECASE)
        or re.search(r"\bKaltenhof\b", full_classify_text, re.IGNORECASE)
    ):
        return ("lubeck_bishopric", excl)

    # 0. Bremen-Verden (Archbishopric / Bishopric — even when nested under SH-Gottorp prince-bishop)
    #    Bremervörde Mint = capital of Bremen-Verden. Stade Mint = same territory under Sweden later.
    #    The "Bremen (Bishopric)" string also indicates Bremen-Verden, NOT city of Bremen.
    if (
        re.search(r"Bremen[ \-]Verden|Bremen and Verden|Bremen & Verden|"
                  r"Bremen \(Bishop|Bremen[\- ]Bishop", full_classify_text, re.IGNORECASE)
        or mint in {"Bremervörde Mint"}
        or re.search(r"\bBremervörde\b|Bremervorde", full_classify_text, re.IGNORECASE)
    ):
        bucket = "bremen_verden"
    # 0b. Stade Mint without explicit "Bremen-Verden" → still Bremen-Verden (Stade was the Swedish capital
    #     of Bremen-Verden after 1648).
    elif mint == "Stade Mint" and not re.search(r"Schleswig-Holstein-Gottorp", meta, re.IGNORECASE):
        # Karl X Gustav / Karl XI Stade-mint coins are Sweden-Bremen-Verden — bremen_verden bucket
        bucket = "bremen_verden"
    # 0c. Brunswick / Wolfenbüttel (Christian IV's mainland Lower-Saxony territory)
    elif (
        re.search(r"Brunswick|Braunschweig|Lower Saxony.*Wolfenb", full_classify_text, re.IGNORECASE)
        or mint == "Wolfenbüttel Mint"
        or re.search(r"\bWolfenbüttel\b|Wolfenbuettel", full_classify_text, re.IGNORECASE)
    ):
        bucket = "brunswick_lueneburg"
    # 0d. Lauenburg (separate duchy under DK king from 1815, own Konventionsfuß-style
    #     Müntzfuß; doesn't fit the Schleswig-Holstein file structure).
    #     Check BEFORE the SH-keyword match because Lauenburg coins typically read
    #     "DENMARK. Lauenburg. <denom>, <year>. Altona Mint. <king>." — Altona-mint
    #     would otherwise route to schleswig_holstein.
    elif re.search(r"\bLauenburg\b", full_classify_text, re.IGNORECASE):
        bucket = "lauenburg"
    # 1. Schleswig-Holstein duchies / counties / branches
    elif re.search(
        r"Schleswig-Holstein|Schleswig\b(?!.*Holstein-Gottorp.*Lübeck)|"
        r"Holstein\b(?!-Gottorp.*Lübeck)|Sonderburg|Sønderborg|Norburg|Nordborg|"
        r"Plön|Ploen|Glücksburg|Gluecksburg|Augustenburg|Augustenborg|"
        r"Schaumburg|Schauenburg|Pinneberg|\bRantzau\b|Lyksborg",
        meta, re.IGNORECASE
    ):
        # Split out Lübeck Bishopric specifically
        if re.search(r"Lübeck \(Bishop|Luebeck \(Bishop", meta, re.IGNORECASE):
            bucket = "lubeck_bishopric"
        else:
            bucket = "schleswig_holstein"
    # 2. SH-mints under Danish king (Glückstadt / Altona / Husum / Rendsburg)
    elif mint in {"Glückstadt Mint", "Altona Mint", "Schleswig Mint", "Husum Mint",
                   "Rendsburg Mint"}:
        bucket = "schleswig_holstein"
    # 3. Lübeck Bishopric (when listed without SH-Gottorp prefix; e.g. August Friedrich at Kaltenhof Mint)
    elif (
        re.search(r"Lübeck \(Bishop|Luebeck \(Bishop", meta, re.IGNORECASE)
        or re.search(r"\bKaltenhof\b|\bEutin\b", full_classify_text, re.IGNORECASE)
    ):
        bucket = "lubeck_bishopric"
    # 5. Hesse-Kassel
    elif re.search(r"Hesse[\- ]Kassel|Hessen[\- ]Kassel", meta, re.IGNORECASE):
        bucket = "hesse_kassel"
    # 6. Osnabrück (prince-bishopric)
    elif re.search(r"Osnabr(?:ü|ue)ck", meta, re.IGNORECASE):
        bucket = "osnabrueck"
    # 7. Oldenburg (incl. Oldenburg-Lübeck-Bishopric "Friedrich August" issues at Altona)
    elif re.search(r"\bOldenburg\b", meta, re.IGNORECASE):
        bucket = "oldenburg"
    # 9. Default: DENMARK or out
    elif region == "DENMARK":
        bucket = "denmark"
    # else OUT (Norway, Sweden, GB, Russia, Poland, ...)

    return bucket, excl


def main():
    all_lots = []
    # Auto-discover every part the lots/ directory has been populated with
    for path in sorted(LOTS_DIR.glob("part*.json")):
        slug = path.stem
        for lot in json.loads(path.read_text()):
            lot["part"] = slug.replace("part", "").upper()
            all_lots.append(lot)

    print(f"Total parsed Bruun lots: {len(all_lots)}")

    # Classify
    by_bucket = defaultdict(list)
    excl_count = Counter()
    for lot in all_lots:
        b, excl = classify_extended(lot)
        lot["bucket"] = b
        lot["exclusions"] = excl
        by_bucket[b].append(lot)
        for r in excl:
            excl_count[r] += 1

    print()
    print("=== Bucket assignment (BEFORE exclusion filter) ===")
    for b in sorted(by_bucket.keys(), key=lambda k: -len(by_bucket[k])):
        print(f"  {b:<25} {len(by_bucket[b])}")

    # In-scope (after exclusion)
    in_scope = {b: [l for l in lots if not l["exclusions"]]
                for b, lots in by_bucket.items()}

    print()
    print("=== In-scope per bucket (year 1566-1914, no patterns/medieval/medals) ===")
    grand_total = 0
    for b in sorted(in_scope.keys(), key=lambda k: -len(in_scope[k])):
        ct = len(in_scope[b])
        if b == "OUT":
            continue
        print(f"  {b:<25} {ct}")
        grand_total += ct
    print(f"  {'(out)':<25} {len(in_scope.get('OUT', []))}")
    print(f"  TOTAL in-scope (excl. OUT): {grand_total}")

    print()
    print("=== Top exclusion reasons ===")
    for r, c in excl_count.most_common(10):
        print(f"  {c:>4}  {r}")

    # Save extended-scope data
    serializable = {b: [l for l in lots] for b, lots in by_bucket.items()}
    (OUT_DIR / "scope.json").write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False)
    )
    print(f"\n→ {OUT_DIR / 'scope.json'}")


if __name__ == "__main__":
    main()
