#!/usr/bin/env python3
"""Catalog cross-reference graph (interactive HTML, no local renderer needed).

WHY THIS EXISTS — a reusable disambiguation tool. Whenever the cross-source
merger leaves a tangle of catalog indices that may or may not be the same coin
(different KM / Hede / Sieg numbers all orbiting one nominal+ruler), this graph
makes the conflict visible so a human curator can decide identity vs. distinct.
It was built for, and carries the worked record of, the 9-component
2026-06-06/07 disambiguation pass (1 Krone Frederik III, 8 Skilling Christian
IV, the Dukat families, …). Keep it for the NEXT batch of «is this one coin or
several?» uncertainties — start from this working ancestor, not a blank file.

Vertices = catalog index VALUES (KM 186.1, Hede 91, Dav 3569, Sieg 46, …),
           namespaced per ruler (Hede/Schou/Sieg/Galster restart numbering per
           ruler, so «Hede 91» Frederik III ≠ «Hede 91» Christian IV).
Edges    = two indices that CO-OCCUR on one source record (i.e. that source
           asserts they label the same coin); edge thickness = N sources,
           colour = source. ✔ bold-black edges = CURATOR verdicts (identity);
           CURATOR_DISTINCT pairs draw NO edge (different coins).

Isolated nodes = an index NO source cross-references to anything (e.g. a
hede-less numismaster KM, or a kmk-museum Hede with no KM). Bridges =
edges that link different catalogue systems (KM↔Hede via bruun, etc.).

HOW TO USE FOR A NEW CASE:
  1. Add the conflicting unified-entry ids as a new "N. <nominal> — <ruler>"
     entry in COMPONENTS (the seed/unified ids that orbit the same coin).
  2. Regenerate, open the HTML, eyeball the clusters.
  3. Record the curator's verdict: identity → CURATOR_LINKS tuple (draws ✔),
     distinct → CURATOR_DISTINCT tuple (no edge); add "N" to PROCESSED so the
     hub turns green. Mirror the verdict into docs/handoff.md (durable journal —
     this file's output/ HTML is gitignored, and historically the script itself
     lived under the gitignored scripts/oneoff/).
  4. Later: promote CURATOR_LINKS→merges / CURATOR_DISTINCT→no_merges into
     data/v2/merge_decisions/<entity>.yml so the merger enforces them.

Self-contained: opens in any browser (vis-network loaded from CDN).
Usage: .venv/bin/python scripts/maintenance/catalog_graph.py  → output/catalog_graph.html
"""
import yaml, glob, json, itertools, os

L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- the 9 conflicting components (nominal+ruler groups) ---
COMPONENTS = {
    "1. 1 Krone — Frederik III (Hede 87/91/95)":
        ["unified-denmark-numismaster-65272","unified-denmark-numismaster-65273",
         "unified-denmark-numismaster-65274","unified-denmark-numismaster-65276",
         "unified-dk-hede-f3h91","unified-dk-numista-143477"],
    "2. 1 Krone — Christian V (Hede 90/94)":
        ["unified-dk-hede-c5h90a","unified-dk-hede-c5h90b","unified-dk-hede-c5h90c",
         "unified-dk-hede-c5h94","unified-dk-bruun-7055","unified-kmk-156921","unified-kmk-156932"],
    "3. 8 Skilling — Christian IV (Hede 91/93/96)":
        ["unified-dk-hede-c4h91","unified-dk-hede-c4h93a","unified-dk-hede-c4h96","unified-dk-numista-15669"],
    "4. 2 Mark — Frederik III (Hede 108/109/110)":
        ["unified-dk-hede-f3h108a","unified-dk-hede-f3h109","unified-dk-hede-f3h110a"],
    "5. 2 Skilling — Christian IV (Hede 116/117)":
        ["unified-dk-hede-c4h116a","unified-dk-hede-c4h117a"],
    "6. 1 Skilling — Christian IV (Hede 118/119)":
        ["unified-dk-hede-c4h118a","unified-dk-hede-c4h119a","unified-dk-hede-c4h119b"],
    "7. 1 Dukat — Christian V (Hede 26/29/31/32)":
        ["unified-dk-hede-c5h26ab","unified-dk-hede-c5h29","unified-dk-hede-c5h31a","unified-dk-hede-c5h31c","unified-dk-hede-c5h32","unified-dk-bruun-7061"],
    "8. 2 Dukat — Christian V (Hede 27/56/58)":
        ["unified-dk-hede-c5h27ab","unified-dk-hede-c5h56","unified-dk-hede-c5h58"],
    "9. 2 Dukat — Frederik V (Hede 10/14)":
        ["unified-dk-hede-f5h10ab","unified-dk-hede-f5h14"],
    # 10 — the whole 2-Dukat-Frederik-V-1747 family (2026-06-26 investigation).
    # Three genuine Hede types (10/12/14), each Bruun-anchored to ONE KM
    # (Hede 10→KM 568.2, Hede 12→KM 569, Hede 14→KM 570). The graph shows
    # KM 567, KM 568, KM 568.1 as ISOLATED islands: NumisMaster/ucoin design-
    # variant Krause numbers with NO Hede cross-ref in any source, scattered
    # by the merger into f5h12 (567), f5h10 (568), f5h14 (568.1) on a bare
    # nominal+year heuristic. Question: split the unsourced KMs out, or keep.
    "10. 2 Dukat — Frederik V 1747 (Hede 10/12/14, KM 567-570)":
        ["unified-dk-hede-f5h10ab", "unified-dk-hede-f5h12ab",
         "unified-dk-hede-f5h14", "unified-dk-bruun-7612"],
}

# Component numbers the curator has already worked through (verdicts recorded in
# CURATOR_LINKS). Their hub renders green with a ✓ instead of the amber «pending».
PROCESSED = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}

# Stable index-TYPE palette (km / hede / dav / sieg / schou / …). Fixed: the
# same catalogue type always the same colour in every graph. Kept distinct from
# the brighter SRC_COLOR edge palette (node fills are deeper, edges brighter).
TYPE_COLOR = {"km":"#2b6cb0", "hede":"#2f855a", "dav":"#c05621", "sieg":"#6b46c1",
              "schou":"#718096", "fr":"#b83280", "galster":"#2c7a7b", "others":"#a0aec0"}
# Stable source -> colour palette: the SAME source always gets the SAME colour
# across every graph this tool emits (so graphs are comparable). Any source not
# listed falls back to a DETERMINISTIC colour (stable hash of the name), never a
# per-run-random one.
SRC_COLOR = {
    "bruun":       "#d62728",  # red
    "hede":        "#2ca02c",  # green
    "numismaster": "#1f77b4",  # blue
    "numista":     "#ff7f0e",  # orange
    "ucoin":       "#8c564b",  # brown
    "kmk":         "#9467bd",  # purple
    "galster":     "#17becf",  # cyan
    "ikmk":        "#e377c2",  # pink
}
_FALLBACK = ["#7f7f7f", "#bcbd22", "#aec7e8", "#ffbb78", "#98df8a", "#c49c94"]

def src_color(src: str) -> str:
    if src in SRC_COLOR:
        return SRC_COLOR[src]
    import hashlib
    h = int(hashlib.md5(src.encode("utf-8")).hexdigest(), 16)
    return _FALLBACK[h % len(_FALLBACK)]


def idx_color(k: str) -> str:
    """Stable index-type colour (km / hede / dav / sieg / schou / …), with the
    same deterministic fallback discipline as src_color — same type always the
    same colour across every graph."""
    if k in TYPE_COLOR:
        return TYPE_COLOR[k]
    import hashlib
    h = int(hashlib.md5(("idx:" + k).encode("utf-8")).hexdigest(), 16)
    return _FALLBACK[h % len(_FALLBACK)]


# Schou is die-variant numbered; one source (Hede) cites it as a RANGE for the
# whole type («Schou 64-111»), while museum specimens cite individual die-
# numbers («Schou 99»). Collapse each individual that falls inside a range to
# the range vertex, so specimens hang off the type instead of forming islands.
import re as _re
_RANGE_RE = _re.compile(r"(\d+)\s*-\s*(\d+)")

def _schou_value(vv):
    # Normalise a Schou citation as-is: a range «4 - 6» → «4-6», an individual
    # die-no stays itself. NO remapping of individual numbers into a containing
    # range — a source's «5» and another source's «4-6» are DIFFERENT citations
    # and must stay distinct vertices (they merely attract, see _schou_attract).
    s = str(vv).strip()
    m = _RANGE_RE.search(s)
    if m:
        return f"{int(m.group(1))}-{int(m.group(2))}"
    return s

def _schou_tokens(raw):
    # «140-141,79» → ['140-141', '79']; «5» → ['5']. Each token normalised.
    out = []
    for part in str(raw).split(","):
        t = _schou_value(part)
        if t and t not in out:
            out.append(t)
    return out

def _schou_sort_key(t):
    m = _RANGE_RE.search(t)
    if m:    return (int(m.group(1)), int(m.group(2)))
    if t.isdigit(): return (int(t), int(t))
    return (10**9, 0)

def _compact_schou_set(toks):
    # Render a Hede's full Schou die-set tidily: drop individuals subsumed by an
    # explicit range token, drop ranges nested in a wider range, sort, join.
    # «{64,65,…,111,64-111}» → «64-111»;  «{79,140-141}» → «79, 140-141».
    ranges, inds = [], []
    for t in toks:
        m = _RANGE_RE.search(t)
        if m:           ranges.append((int(m.group(1)), int(m.group(2)), t))
        elif t.isdigit(): inds.append((int(t), t))
        else:           inds.append((10**9, t))
    keep_ranges = [(lo, hi, t) for lo, hi, t in ranges
                   if not any(olo <= lo and hi <= ohi and (olo, ohi) != (lo, hi)
                              for olo, ohi, _ in ranges)]
    keep_inds = [(n, t) for n, t in inds
                 if not any(lo <= n <= hi for lo, hi, _ in keep_ranges)]
    items = [(lo, t) for lo, hi, t in keep_ranges] + keep_inds
    items.sort(key=lambda x: x[0])
    seen, out = set(), []
    for _, t in items:
        if t not in seen:
            seen.add(t); out.append(t)
    return ", ".join(out)

# Davenport «European Crowns» volume prefixes (EC I…IV, ECT) are just the
# century-book a number lives in; the number itself is unique across the EC
# series (non-overlapping ranges), so «EC II# 3643» and «3643» are ONE index.
# AAO is a SEPARATE Davenport series — left untouched, never merged with bare numbers.
_DAV_EC_RE  = _re.compile(r"^EC\s*[IVX]+\s*#?\s*", _re.I)
_DAV_ECT_RE = _re.compile(r"^ECT\s*#?\s*", _re.I)
def _dav_value(v):
    s = str(v).strip()
    s2 = _DAV_EC_RE.sub("", s)
    if s2 == s:
        s2 = _DAV_ECT_RE.sub("", s)
    m = _re.match(r"^(A?\d+)([a-zA-Z])?$", s2)   # «3516a»→«3516A», keep «A1287»
    return m.group(1) + (m.group(2).upper() if m.group(2) else "") if m else s2
CAT_KEYS = ("km","hede","dav","sieg","schou","fr","galster")

# Hede / Schou / Sieg / Galster are Danish per-ruler catalogues: numbering
# RESTARTS with each ruler, so «Hede 91» under Frederik III is a completely
# different coin from «Hede 91» under Christian IV. Such node-ids are
# namespaced by the case's ruler so the same number under two rulers stays two
# separate, unconnected vertices. KM / Dav / Fr number globally (per country)
# and need no namespacing.
PER_RULER = {"hede", "schou", "sieg", "galster"}
SIB_TYPES = {"km", "hede", "dav", "sieg", "fr", "galster"}

def _ruler_tag(comp):
    # "1. 1 Krone — Frederik III (Hede 87/91/95)" -> "Frederik III"
    m = _re.search(r"—\s*([^(]+?)\s*(?:\(|$)", comp)
    return m.group(1).strip() if m else comp

# Curator-confirmed identities — the researcher VISUALLY verified (comparing the
# source coin-pages) that two catalogue indices are the SAME coin, even though no
# single source co-cites them. Rendered as a bold solid edge with a ✔ label, so
# the human verdict is unmistakable against the source-derived links.
# Tuple: (type_a, ruler_a_or_None, val_a, type_b, ruler_b_or_None, val_b, note)
CURATOR_LINKS = [
    ("hede", "Christian IV", "96", "km", None, "42",
     "візуально підтверджено: Hede 96 = KM 42 (8 Skilling, Christian IV)"),
    # Component 5 — «2 Skilling Christian IV» is TWO different coins (Hede 116 ≠
    # Hede 117, two clean Hede/Sieg clusters). KM 80.1 = the Hede-117 family,
    # KM 80.2 = the Hede-116 family. (Counters the old hede-less transitive
    # bridge that wrongly joined KM 80.1 ↔ 80.2 via shared KM-core 80.)
    ("km", None, "80.1", "hede", "Christian IV", "117",
     "візуально підтверджено: KM 80.1 = Hede 117 (2 Skilling, Christian IV)"),
    ("km", None, "80.1", "hede", "Christian IV", "117A",
     "візуально підтверджено: KM 80.1 = Hede 117A (2 Skilling, Christian IV)"),
    ("km", None, "80.2", "hede", "Christian IV", "116A",
     "візуально підтверджено: KM 80.2 = Hede 116A (2 Skilling, Christian IV)"),
    ("km", None, "80.2", "hede", "Christian IV", "116B",
     "візуально підтверджено: KM 80.2 = Hede 116B (2 Skilling, Christian IV)"),
    ("km", None, "80.1", "sieg", "Christian IV", "41",
     "візуально підтверджено: KM 80.1 = Sieg 41 (2 Skilling, Christian IV)"),
    ("km", None, "80.2", "sieg", "Christian IV", "40",
     "візуально підтверджено: KM 80.2 = Sieg 40 (2 Skilling, Christian IV)"),
    # Component 6 — «1 Skilling Christian IV» (Hede 118/119). Curator crosswalk
    # confirmed: Hede 118-anything = KM 66, Hede 119-anything = KM 67. (The c4h119
    # page lists Sieg 32.1-32.4, all sub-variants of the ONE Hede 119 coin.)
    ("hede", "Christian IV", "118", "km", None, "66",
     "візуально підтверджено: Hede 118 = KM 66 (1 Skilling, Christian IV)"),
    ("hede", "Christian IV", "119", "km", None, "67",
     "візуально підтверджено: Hede 119 = KM 67 (1 Skilling, Christian IV)"),
    # Component 1 — «1 Krone Frederik III» (= 4 Mark Danske): ALL one coin per
    # curator, despite two catalog families. KM-186 family (1652-53): Hede 87/95,
    # KM 186/186.1/186.2/186.3, Dav 3569/3569A, Schou 22/59. KM-192 family (1653):
    # Hede 91, Sieg 46, Schou 37/39, KM 192.1/192.2/192.3, Dav 3570/3570A. Within
    # each unit KM↔Hede are already source-linked; these 4 curator edges bridge the
    # families + pull in the two KM-only units (192.1, 192.3 — no Hede). NOTE:
    # f3h91 nominal printed «4 Mark» vs «1 Krone» elsewhere — 1 Krone = 4 Mark
    # Danske; nominal divergence to surface in match_uncertainty on promotion.
    ("hede", "Frederik III", "87", "hede", "Frederik III", "91",
     "візуально підтверджено: Hede 87 = Hede 91 — одна монета (1 Krone, Frederik III)"),
    ("hede", "Frederik III", "87", "hede", "Frederik III", "95",
     "візуально підтверджено: Hede 87 = Hede 95 — одна монета (1 Krone, Frederik III)"),
    ("hede", "Frederik III", "91", "km", None, "192.1",
     "візуально підтверджено: Hede 91 = KM 192.1 — одна монета попри KM-субномер (1 Krone, Frederik III)"),
    ("hede", "Frederik III", "91", "km", None, "192.3",
     "візуально підтверджено: Hede 91 = KM 192.3 — одна монета попри KM-субномер (1 Krone, Frederik III)"),
    # Component 4 — «2 Mark Frederik III»: Hede 108 + 109 + 110 (+ all sub-letters)
    # + KM 259 are ALL sub-types of ONE coin (curator). Anchor Hede 108 → 109,
    # 110, KM 259 unites the four clusters.
    ("hede", "Frederik III", "108", "hede", "Frederik III", "109",
     "візуально підтверджено: Hede 108 = Hede 109 — одна монета (2 Mark, Frederik III)"),
    ("hede", "Frederik III", "108", "hede", "Frederik III", "110",
     "візуально підтверджено: Hede 108 = Hede 110 — одна монета (2 Mark, Frederik III)"),
    ("hede", "Frederik III", "108", "km", None, "259",
     "візуально підтверджено: Hede 108/109/110 = KM 259 (2 Mark, Frederik III)"),
    # Component 3 — «8 Skilling Christian IV»: THREE distinct coins. Hede 93 = KM 32;
    # Hede 91 = KM 32.1 (separate coin); Hede 96 = KM 42 (above). KM 32 ≠ KM 32.1.
    ("hede", "Christian IV", "93", "km", None, "32",
     "візуально підтверджено: Hede 93 = KM 32 (8 Skilling, Christian IV)"),
    ("hede", "Christian IV", "91", "km", None, "32.1",
     "візуально підтверджено: Hede 91 = KM 32.1 — окрема монета (8 Skilling, Christian IV)"),
    # Component 2 — «1 Krone Christian V»: ALL one coin despite the Hede 90/94 split.
    # Anchor Hede 90 → Hede 94 + KM 401 unites the four clusters (Dav 3642/3643/
    # 3645 hang off the KM 401.x sub-numbers via source edges).
    ("hede", "Christian V", "90", "hede", "Christian V", "94",
     "візуально підтверджено: Hede 90 = Hede 94 — одна монета (1 Krone, Christian V)"),
    ("hede", "Christian V", "90", "km", None, "401",
     "візуально підтверджено: Hede 90/94 = KM 401 (1 Krone, Christian V)"),
    # Component 8 — «2 Dukat Christian V»: Hede 27 carries TWO different KM numbers
    # (KM 419 AND KM 416 — unusual but factual). Hede 56 and Hede 58 are separate
    # coins → three distinct coins total.
    ("hede", "Christian V", "27", "km", None, "419",
     "візуально підтверджено: Hede 27 = KM 419 (2 Dukat, Christian V)"),
    ("hede", "Christian V", "27", "km", None, "416",
     "візуально підтверджено: Hede 27 = KM 416 — Hede 27 несе ДВІ KM (419 + 416), 2 Dukat Christian V"),
    # Component 7 — «1 Dukat Christian V» (Hede 26/29/31/32): Hede 26 = KM 413;
    # Hede 31 = KM 415. KM 412 + KM A433 are separate coins; Hede 29 + Hede 32
    # separate. (4 distinct Hede coins — see CURATOR_DISTINCT.)
    ("hede", "Christian V", "26", "km", None, "413",
     "візуально підтверджено: Hede 26 = KM 413 (1 Dukat, Christian V)"),
    ("hede", "Christian V", "31", "km", None, "415",
     "візуально підтверджено: Hede 31 = KM 415 (1 Dukat, Christian V)"),
]

# Curator-confirmed DISTINCTNESS — the researcher verified two index families are
# DIFFERENT coins (the opposite of CURATOR_LINKS). No ✔-edge is drawn (the graph
# already shows them as separate clusters); recorded for the verdict journal and
# for promotion to `merge_decisions::no_merges`.
# Tuple: (type_a, ruler_a_or_None, val_a, type_b, ruler_b_or_None, val_b, note)
CURATOR_DISTINCT = [
    # Component 9 — «2 Dukat Frederik V»: two clean clusters; Hede 10 (+ Sieg 31/
    # 31.2, Schou 4-6, KM 568.x) and Hede 14 (+ Sieg 35, Schou 2) are DIFFERENT coins.
    ("hede", "Frederik V", "10", "hede", "Frederik V", "14",
     "візуально підтверджено: Hede 10 ≠ Hede 14 — різні монети (2 Dukat, Frederik V)"),
    # Component 3 — «8 Skilling Christian IV»: Hede 91 (KM 32.1), Hede 93 (KM 32),
    # Hede 96 (KM 42) are THREE distinct coins.
    ("hede", "Christian IV", "91", "hede", "Christian IV", "93",
     "візуально підтверджено: Hede 91 ≠ Hede 93 — різні монети (KM 32.1 vs KM 32)"),
    ("hede", "Christian IV", "91", "hede", "Christian IV", "96",
     "візуально підтверджено: Hede 91 ≠ Hede 96 — різні монети (8 Skilling, Christian IV)"),
    ("hede", "Christian IV", "93", "hede", "Christian IV", "96",
     "візуально підтверджено: Hede 93 ≠ Hede 96 — різні монети (8 Skilling, Christian IV)"),
    # Component 8 — «2 Dukat Christian V»: Hede 27, 56, 58 are three distinct coins.
    ("hede", "Christian V", "27", "hede", "Christian V", "56",
     "візуально підтверджено: Hede 27 ≠ Hede 56 — різні монети (2 Dukat, Christian V)"),
    ("hede", "Christian V", "27", "hede", "Christian V", "58",
     "візуально підтверджено: Hede 27 ≠ Hede 58 — різні монети (2 Dukat, Christian V)"),
    ("hede", "Christian V", "56", "hede", "Christian V", "58",
     "візуально підтверджено: Hede 56 ≠ Hede 58 — різні монети (2 Dukat, Christian V)"),
    # Component 7 — «1 Dukat Christian V»: Hede 26 (=KM 413), Hede 29, Hede 31
    # (=KM 415), Hede 32 are FOUR distinct coins. KM 412 + KM A433 are separate
    # coins too. CAVEAT: the shared «Schou 8» vertex bridges Hede 29 ↔ Hede 32, but
    # per curator that Schou 8 is most-likely a DIFFERENT die for each — do NOT
    # treat the shared Schou 8 as evidence of identity (§0b: «скоріш за все», soft).
    ("hede", "Christian V", "26", "hede", "Christian V", "29",
     "візуально підтверджено: Hede 26 ≠ Hede 29 — різні монети (1 Dukat, Christian V)"),
    ("hede", "Christian V", "26", "hede", "Christian V", "31",
     "візуально підтверджено: Hede 26 ≠ Hede 31 — різні монети (1 Dukat, Christian V)"),
    ("hede", "Christian V", "26", "hede", "Christian V", "32",
     "візуально підтверджено: Hede 26 ≠ Hede 32 — різні монети (1 Dukat, Christian V)"),
    ("hede", "Christian V", "29", "hede", "Christian V", "31",
     "візуально підтверджено: Hede 29 ≠ Hede 31 — різні монети (1 Dukat, Christian V)"),
    ("hede", "Christian V", "29", "hede", "Christian V", "32",
     "візуально підтверджено: Hede 29 ≠ Hede 32 — різні монети; спільний Schou 8 на графі вводить в оману (різні штемпелі)"),
    ("hede", "Christian V", "31", "hede", "Christian V", "32",
     "візуально підтверджено: Hede 31 ≠ Hede 32 — різні монети (1 Dukat, Christian V)"),
]

def _hede_base(val):
    # Hede sub-letters (116A, 116B, 31C, 112AB) are mintmark/die sub-types the
    # source page presents as ONE coin → collapse to the bare base number for the
    # graph vertex. «116A»→«116», «31C»→«31», «112AB»→«112», «116»→«116».
    m = _re.match(r"(\d+)", str(val))
    return m.group(1) if m else str(val)

def _sieg_base(val):
    # Sieg dot-sub-numbers (32.1, 32.2, 32.3, 32.4) are mintmark sub-variants of
    # ONE coin (e.g. c4h119 lists Sieg 32.1-32.4, all the 1 Skilling Christian IV)
    # → collapse to the base number. «32.1»→«32», «46.2»→«46», «32»→«32». Unlike
    # KM, whose dot-sub-numbers (80.1/80.2) can be DIFFERENT coins (§9.4), Sieg's
    # .N are sub-classes of one type, so they merge. (Curator-confirmed.)
    m = _re.match(r"(\d+)", str(val))
    return m.group(1) if m else str(val)

def _node_id(typ, ruler, val):
    if typ == "hede":
        val = _hede_base(val)        # sub-letters share one base vertex
    elif typ == "sieg":
        val = _sieg_base(val)        # dot-sub-numbers share one base vertex
    scope = ruler if typ in PER_RULER else None
    return f"{typ}:{scope}:{val}" if scope else f"{typ}:{val}"

_RESOLVE_WARNED = set()
def _resolve_member(m, su):
    """COMPONENTS hard-code unified-ids, but the cross-source merge can SHIFT a
    unified-id when membership changes (e.g. the bare `…c4h117` is superseded by
    its by_letter split, so the canonical id becomes `…c4h117a`). Self-heal: if
    the listed id is gone, find the unified entry whose composed_of holds the
    bare seed (`unified-X` → seed `X` or `Xa`/`Xb`…) and use it, warning once so
    the stale COMPONENTS entry can be refreshed. Returns None if truly absent."""
    if m in su:
        return m
    base = m[len("unified-"):] if m.startswith("unified-") else m
    for uid, u in su.items():
        if any(s == base or (s.startswith(base) and s[len(base):].isalpha())
               for s in (u.get("composed_of") or [])):
            if m not in _RESOLVE_WARNED:
                _RESOLVE_WARNED.add(m)
                print(f"  [COMPONENTS stale: {m} -> {uid} (refresh the hard-coded id)]")
            return uid
    if m not in _RESOLVE_WARNED:
        _RESOLVE_WARNED.add(m)
        print(f"  [COMPONENTS member MISSING (no unified holds it): {m}]")
    return None

def load():
    seed = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "data/v2/seed/*/danish_realm.yml"))):
        src = p.split("/")[-2]
        for c in yaml.load(open(p), Loader=L)["coins"]:
            c["_src"] = src; seed[c["id"]] = c
    su = {c["id"]: c for c in
          yaml.load(open(os.path.join(ROOT,"data/v2/seed_unified/danish_realm.yml")), Loader=L)["coins"]}
    return seed, su

def main():
    seed, su = load()
    nodes, edges, hub_edges, polygons = {}, {}, [], []
    node_links = {}   # nid -> {url: source}  (pages that cite this index)
    node_core = {}    # nid -> (type, ruler_scope, core_digits)  for ruler-aware siblings
    schou_idx = {}    # ruler_scope -> {schou_val: nid}  for range↔index attraction
    hede_subs = {}    # merged hede vertex id -> set of sub-letter values (for label)
    sieg_subs = {}    # merged sieg vertex id -> set of dot-sub-number values (for label)

    # PASS 1 — a Hede type is struck from several dies; Schou catalogues the dies.
    # Collect, per Hede vertex, the SET of Schou tokens co-cited with it across all
    # records, then collapse them into ONE «Schou {set}» vertex per Hede (recovers
    # comma-set tokens the old first-match parse dropped, e.g. «140-141,79»).
    hede_schou = {}   # hede_node_id -> set(schou_token)
    for comp, members in COMPONENTS.items():
        rt = _ruler_tag(comp)
        sids = []
        for m in members:
            rm = _resolve_member(m, su)
            for s in (su.get(rm, {}).get("composed_of") or []):
                if s not in sids: sids.append(s)
        for sid in sids:
            c = seed.get(sid)
            if not c: continue
            cat = c.get("catalog") or {}
            hv, sv = cat.get("hede"), cat.get("schou")
            if hv is None or sv is None: continue
            hede_ids = [_node_id("hede", rt, str(x)) for x in (hv if isinstance(hv, list) else [hv])]
            toks = []
            for raw in (sv if isinstance(sv, list) else [sv]):
                toks += _schou_tokens(raw)
            for h in hede_ids:
                hede_schou.setdefault(h, set()).update(toks)
    hede_to_merged = {}   # hede_node_id -> merged schou node id
    merged_label = {}     # merged schou node id -> compact label
    token_owner = {}      # (ruler, token) -> set(hede_node_id)  for hede-less redirect
    for h, toks in hede_schou.items():
        ruler = h.split(":")[1]                 # «hede:Ruler:val»
        lbl = _compact_schou_set(toks)
        mid = f"schou:{ruler}:{lbl}"
        hede_to_merged[h] = mid
        merged_label[mid] = lbl
        for t in toks:
            token_owner.setdefault((ruler, t), set()).add(h)

    for comp, members in COMPONENTS.items():
        rt = _ruler_tag(comp)           # ruler this case belongs to (namespaces per-ruler types)
        sids = []
        for m in members:
            rm = _resolve_member(m, su)
            for s in (su.get(rm, {}).get("composed_of") or []):
                if s not in sids: sids.append(s)
        comp_members = set()            # index-node ids belonging to this case
        for sid in sids:
            c = seed.get(sid)
            if not c: continue
            src = c["_src"]
            cat = c.get("catalog") or {}
            idxs = []
            # this record's Hede vertices → the merged «Schou {set}» vertex(es)
            _hv = cat.get("hede")
            rec_hede = [_node_id("hede", rt, str(x))
                        for x in (_hv if isinstance(_hv, list) else ([_hv] if _hv is not None else []))]
            rec_merged = [hede_to_merged[h] for h in rec_hede if h in hede_to_merged]

            def _emit_schou(mid, lbl):
                idxs.append((mid, "schou", lbl)); comp_members.add(mid)
                if mid not in nodes:
                    nodes[mid] = {"id": mid, "label": f"Schou {lbl}", "color": idx_color("schou"),
                                  "group": comp, "widthConstraint": {"maximum": 120}}

            for k in CAT_KEYS:
                v = cat.get(k)
                if v is None: continue
                if k == "schou":
                    if rec_merged:                       # Schou belong to this record's Hede → merged vertex
                        for mid in rec_merged:
                            _emit_schou(mid, merged_label[mid])
                        continue
                    # hede-less Schou: redirect each token to its owning Hede's merged
                    # vertex when unambiguous, else keep a standalone token vertex.
                    for raw in (v if isinstance(v, list) else [v]):
                        for tok in _schou_tokens(raw):
                            owners = token_owner.get((rt, tok), set())
                            if len(owners) == 1:
                                mid = hede_to_merged[next(iter(owners))]
                                _emit_schou(mid, merged_label[mid])
                            else:
                                nid = f"schou:{rt}:{tok}"
                                idxs.append((nid, "schou", tok)); comp_members.add(nid)
                                schou_idx.setdefault(rt, {})[tok] = nid
                                if nid not in nodes:
                                    nodes[nid] = {"id": nid, "label": f"Schou {tok}",
                                                  "color": idx_color("schou"), "group": comp}
                    continue
                if k == "hede":
                    # Hede sub-letters → ONE base vertex (source page presents the
                    # sub-types as one coin). Sub-letters collected for the label.
                    for vv in (v if isinstance(v, list) else [v]):
                        base = _hede_base(vv)
                        mid = f"hede:{rt}:{base}"
                        idxs.append((mid, "hede", str(vv))); comp_members.add(mid)
                        hede_subs.setdefault(mid, set()).add(str(vv))
                        if mid not in nodes:
                            nodes[mid] = {"id": mid, "label": f"Hede {base}",
                                          "color": idx_color("hede"), "group": comp}
                            node_core[mid] = ("hede", rt, base)
                    continue
                if k == "sieg":
                    # Sieg dot-sub-numbers (32.1-32.4) → ONE base vertex (sub-classes
                    # of one coin, curator-confirmed). Sub-numbers collected for label.
                    for vv in (v if isinstance(v, list) else [v]):
                        base = _sieg_base(vv)
                        mid = f"sieg:{rt}:{base}"
                        idxs.append((mid, "sieg", str(vv))); comp_members.add(mid)
                        sieg_subs.setdefault(mid, set()).add(str(vv))
                        if mid not in nodes:
                            nodes[mid] = {"id": mid, "label": f"Sieg {base}",
                                          "color": idx_color("sieg"), "group": comp,
                                          "widthConstraint": {"maximum": 120}}
                            node_core[mid] = ("sieg", rt, base)
                    continue
                for vv in (v if isinstance(v, list) else [v]):
                    val = _dav_value(vv) if k == "dav" else str(vv)
                    scope = rt if k in PER_RULER else None
                    nid = f"{k}:{scope}:{val}" if scope else f"{k}:{val}"
                    idxs.append((nid, k, val)); comp_members.add(nid)
                    if nid not in nodes:
                        nodes[nid] = {"id": nid, "label": f"{k.upper() if k in ('km','fr','dav') else k.capitalize()} {val}",
                                      "color": idx_color(k), "group": comp}
                        if k in SIB_TYPES:
                            cm = _re.match(r"\d+", val)
                            if cm:
                                node_core[nid] = (k, scope, cm.group(0))
            # co-occurrence edges (clique) within this source record
            for (a,_,_), (b,_,_) in itertools.combinations(idxs, 2):
                key = tuple(sorted([a, b]))
                e = edges.setdefault(key, {"seeds": set(), "srcs": set()})
                e["seeds"].add(sid); e["srcs"].add(src)
            # source-confidence polygon: one record asserting >=3 indices
            poly = sorted({nid for nid, _, _ in idxs})
            if len(poly) >= 3:
                polygons.append({"nodes": poly, "color": src_color(src), "src": src})
            # per-node source citations (for the click panel). Bruun lots all
            # share ONE PDF url but differ by lot-no, so for Bruun we key by the
            # catalogue ref (part + lot) and show that text instead of the link.
            cites = []
            for s in (c.get("sources") or []):
                u = s.get("url"); ref = s.get("ref")
                if src == "bruun":
                    label = ref or u
                    if label:
                        cites.append(("b|" + label, {"t": src, "u": None, "r": label}))
                elif u:
                    cites.append((u, {"t": src, "u": u, "r": None}))
            for nid, _, _ in idxs:
                lk = node_links.setdefault(nid, {})
                for key, ent in cites:
                    lk.setdefault(key, ent)
        # CASE-GROUP hub: a labelled box every index of this case hangs off
        # (faint dashed membership edges) so the 9 case-clusters are visible.
        hub = f"comp:{comp}"
        done = comp.split(".")[0].strip() in PROCESSED   # curator already worked this case
        hub_label = comp.replace(" (", "\n(", 1)   # row 1: «N. Nominal — Ruler», row 2: «(Hede …)»
        if done:
            hub_label = "✓ " + hub_label
        hub_color = ({"background": "#d7ecd9", "border": "#5aa463"} if done   # green = done
                     else {"background": "#fff7df", "border": "#d4b94a"})     # amber = pending
        hub_font = "#3a7d44" if done else "#b3a55a"
        nodes[hub] = {"id": hub, "label": hub_label, "shape": "box",
                      "color": hub_color,
                      "font": {"size": 16, "color": hub_font, "face": "sans-serif",
                               "multi": False, "align": "center"},
                      "widthConstraint": {"maximum": 130}, "margin": 6}
        for nid in comp_members:
            hub_edges.append({"from": hub, "to": nid, "dashes": True, "width": 1,
                              "color": {"color": "#e2e2e2"}, "smooth": False})
    # label each merged Hede vertex with its actual sub-letters («Hede 116A, 116B»;
    # «Hede 31A, 31B, 31C»). Drop the bare base value when sub-letters are present.
    for mid, subs in hede_subs.items():
        # Hede sub-letters are case-INSENSITIVE: «119A» (hede) and «119a» (kmk)
        # are the same sub-variant. Upper-case + dedup so the label shows each once.
        nodes[mid]["label"] = "Hede " + ", ".join(sorted({s.upper() for s in subs}))
    for mid, subs in sieg_subs.items():
        # Sieg dot-sub-numbers merged onto one base vertex → label lists them all.
        def _sk(s):
            m = _re.match(r"(\d+)(?:\.(\d+))?", s)
            return (int(m.group(1)), int(m.group(2) or 0)) if m else (10**9, 0)
        nodes[mid]["label"] = "Sieg " + ", ".join(sorted({s for s in subs}, key=_sk))
    # SIBLING edges: keep sub-variants of one numeric core next to each other
    # (KM 186.1 / 186.2 / 186.3 → core 186; Hede 116A / 116B → 116). Thin dotted
    # grey, distinct from source cross-refs, so physics pulls a sub-variant
    # family into one cluster. Schou excluded (die-variant ranges, not coin
    # sub-types).
    # group by (type, ruler_scope, core_digits) — ruler-aware, so e.g. Hede 91 /
    # Hede 91B siblings ONLY when they belong to the same ruler. Per-ruler types
    # carry their ruler scope in node_core; global types carry scope=None.
    core_groups = {}
    for nid, key in node_core.items():
        core_groups.setdefault(key, []).append(nid)
    sib_edges = []
    for (typ, scope, core), mem in core_groups.items():
        if len(mem) < 2: continue
        for a, b in itertools.combinations(sorted(mem), 2):
            sib_edges.append({"from": a, "to": b, "dashes": [1, 5], "width": 1,
                              "color": {"color": "#b9c4cc"}, "smooth": False,
                              "length": 22,   # short rest-length → sub-variants attract tightly
                              "title": f"суб-варіанти {typ.upper()} {core}"})
    # SCHOU range↔index attraction: a source's range «4-6» and another source's
    # individual «5» stay SEPARATE vertices (no merge), but a thin dotted edge
    # pulls the index toward the range it falls within — same ruler only.
    schou_edges = []
    for scope, vmap in schou_idx.items():
        ranges = [(int(m.group(1)), int(m.group(2)), nid, val)
                  for val, nid in vmap.items()
                  if (m := _RANGE_RE.search(val))]
        inds = [(int(val), nid, val) for val, nid in vmap.items() if val.isdigit()]
        for lo, hi, rnid, rval in ranges:
            for n, inid, ival in inds:
                if lo <= n <= hi:
                    schou_edges.append({"from": rnid, "to": inid, "dashes": [1, 5], "width": 1,
                                        "color": {"color": "#cdbfa0"}, "smooth": False,
                                        "length": 26,
                                        "title": f"Schou {ival} ∈ діапазон {rval}"})
    edge_list = []
    for (a, b), e in edges.items():
        n = len(e["seeds"])             # N = number of source records asserting this link
        s = sorted(e["srcs"])
        edge_list.append({"from": a, "to": b,
                          "title": f"{n} source record(s): " + ", ".join(s),
                          "color": src_color(s[0]),
                          "width": min(2 * n, 24),
                          # a source's index-bundle attracts: shorter rest-length,
                          # tighter the more sources confirm the link.
                          "length": max(28, 55 - 6 * n)})
    # CURATOR-CONFIRMED identities: bold solid edge, ✔ label, distinct colour.
    # Dedup: Hede sub-letter targets (116A, 116B) now resolve to one base vertex.
    cur_edges = []
    cur_seen = set()
    for ta, ra, va, tb, rb, vb, note in CURATOR_LINKS:
        a, b = _node_id(ta, ra, va), _node_id(tb, rb, vb)
        key = tuple(sorted([a, b]))
        if a in nodes and b in nodes and key not in cur_seen:
            cur_seen.add(key)
            cur_edges.append({"from": a, "to": b, "color": {"color": "#111111"},
                              "width": 4, "dashes": False, "smooth": False,
                              "length": 40, "label": "✔", "font": {"size": 18, "color": "#111111"},
                              "title": "✔ " + note})
        elif a not in nodes or b not in nodes:
            print(f"  [curator-link skipped: {a} / {b} not both present]")
    edge_list += sib_edges + schou_edges + cur_edges + hub_edges
    node_links_out = {nid: list(lk.values()) for nid, lk in node_links.items()}
    html = HTML.replace("__NODES__", json.dumps(list(nodes.values()), ensure_ascii=False)) \
               .replace("__EDGES__", json.dumps(edge_list, ensure_ascii=False)) \
               .replace("__POLYGONS__", json.dumps(polygons, ensure_ascii=False)) \
               .replace("__NODELINKS__", json.dumps(node_links_out, ensure_ascii=False))
    outdir = os.path.join(ROOT, "output"); os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "catalog_graph.html")
    open(out, "w").write(html)
    print(f"nodes={len(nodes)} edges={len(edge_list)}  -> {out}")
    iso = [n['label'] for nid,n in nodes.items()
           if not nid.startswith("comp:") and not any(nid in e for e in edges)]
    print(f"isolated (no cross-ref): {len(iso)}")
    for x in sorted(iso): print('   ', x)

HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Catalog cross-reference graph — danish_realm</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>body{margin:0;font-family:sans-serif}#net{width:100vw;height:94vh;border:0}
#leg{padding:6px 12px;font-size:13px;background:#f4f4f4}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin:0 4px 0 12px;vertical-align:middle}</style></head>
<body>
<div id="leg"><b>Вершини</b> (тип, фіксований колір):
<span class="sw" style="background:#2b6cb0"></span>KM
<span class="sw" style="background:#2f855a"></span>Hede
<span class="sw" style="background:#c05621"></span>Dav
<span class="sw" style="background:#6b46c1"></span>Sieg
<span class="sw" style="background:#718096"></span>Schou
<span class="sw" style="background:#b83280"></span>Fr
<span class="sw" style="background:#2c7a7b"></span>Galster
&nbsp;|&nbsp; <b>Ребра</b> (джерело, фіксований колір):
<span class="sw" style="background:#d62728"></span>bruun
<span class="sw" style="background:#2ca02c"></span>hede
<span class="sw" style="background:#1f77b4"></span>numismaster
<span class="sw" style="background:#ff7f0e"></span>numista
<span class="sw" style="background:#8c564b"></span>ucoin
<span class="sw" style="background:#9467bd"></span>kmk
<span class="sw" style="background:#17becf"></span>galster
<span class="sw" style="background:#e377c2"></span>ikmk
&nbsp; — товщина ребра = к-ть джерел (2×N) · острови = індекси, які жодне джерело не повʼязало
&nbsp;|&nbsp; <span class="sw" style="background:#fff7df;border:1px solid #d4b94a"></span><b>жовтий блок</b> = кейс-група (ще не опрацьована) &nbsp; <span class="sw" style="background:#d7ecd9;border:1px solid #5aa463"></span><b>✓ зелений</b> = опрацьована &nbsp;·&nbsp; сіра крапкова лінія = суб-варіанти одного ядра тримаються поряд · напівпрозорий багатокутник кольору джерела = один сід дає ≥3 індекси (зона впевненості джерела).</div>
<div id="net"></div>
<div id="pop"></div>
<style>#pop{display:none;position:fixed;z-index:20;background:#fff;border:1px solid #ccc;
border-radius:6px;padding:8px 10px;font-size:12px;max-width:340px;max-height:46vh;overflow:auto;
box-shadow:0 3px 12px rgba(0,0,0,.22);line-height:1.5}
#pop a{color:#1f6fb5;text-decoration:none}#pop a:hover{text-decoration:underline}
#pop .x{float:right;cursor:pointer;color:#999;margin-left:8px}</style>
<script>
var nodes=new vis.DataSet(__NODES__), edges=new vis.DataSet(__EDGES__);
var polygons=__POLYGONS__, nodeLinks=__NODELINKS__;
var network=new vis.Network(document.getElementById('net'),{nodes:nodes,edges:edges},{
 nodes:{shape:'dot',size:14,font:{size:14,color:'#9aa0a6'}},
 edges:{smooth:false},
 physics:{barnesHut:{gravitationalConstant:-8000,springLength:90},stabilization:{iterations:300}},
 interaction:{hover:true,tooltipDelay:80}});

function hexToRgba(hex,a){hex=hex.replace('#','');
 if(hex.length===3)hex=hex.split('').map(function(c){return c+c;}).join('');
 var n=parseInt(hex,16);return 'rgba('+((n>>16)&255)+','+((n>>8)&255)+','+(n&255)+','+a+')';}
function convexHull(pts){pts=pts.slice().sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});
 if(pts.length<3)return pts;
 function cr(o,a,b){return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);}
 var lo=[],up=[],i;
 for(i=0;i<pts.length;i++){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],pts[i])<=0)lo.pop();lo.push(pts[i]);}
 for(i=pts.length-1;i>=0;i--){while(up.length>=2&&cr(up[up.length-2],up[up.length-1],pts[i])<=0)up.pop();up.push(pts[i]);}
 lo.pop();up.pop();return lo.concat(up);}

// fill the polygon of every source record that asserts >=3 indices, BEHIND nodes
network.on('beforeDrawing',function(ctx){
 for(var i=0;i<polygons.length;i++){var pg=polygons[i];
  var pos=network.getPositions(pg.nodes),pts=[],j;
  for(j=0;j<pg.nodes.length;j++){var p=pos[pg.nodes[j]];if(p)pts.push([p.x,p.y]);}
  if(pts.length<3)continue;var h=convexHull(pts);if(h.length<3)continue;
  ctx.beginPath();ctx.moveTo(h[0][0],h[0][1]);
  for(j=1;j<h.length;j++)ctx.lineTo(h[j][0],h[j][1]);ctx.closePath();
  ctx.fillStyle=hexToRgba(pg.color,0.13);ctx.fill();
  ctx.strokeStyle=hexToRgba(pg.color,0.45);ctx.lineWidth=1.5;ctx.stroke();}
});

// click a vertex → panel of source pages (each opens in a new tab)
var pop=document.getElementById('pop');
pop.addEventListener('click',function(e){if(e.target.className==='x')pop.style.display='none';});
function esc(s){return (s+'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
network.on('click',function(params){
 if(!params.nodes.length){pop.style.display='none';return;}
 var nid=params.nodes[0];
 if(nid.indexOf('comp:')===0){pop.style.display='none';return;}
 var lab=(nodes.get(nid)||{}).label||nid;
 var links=nodeLinks[nid]||[];
 var html='<span class="x">×</span><b>'+esc(lab)+'</b><br>';
 if(!links.length){html+='<i>немає посилань-джерел</i>';}
 else{for(var i=0;i<links.length;i++){var L=links[i];
   if(L.u){html+='<a href="'+esc(L.u)+'" target="_blank" rel="noopener">'+esc(L.t)+'</a> — <span style="color:#888">'+esc(L.u)+'</span><br>';}
   else{html+='<span style="color:#555">'+esc(L.r)+'</span><br>';}}}
 pop.innerHTML=html;
 var r=document.getElementById('net').getBoundingClientRect();
 var x=r.left+params.pointer.DOM.x+14, y=r.top+params.pointer.DOM.y+8;
 pop.style.left=Math.min(x,window.innerWidth-360)+'px';
 pop.style.top=Math.min(y,window.innerHeight-260)+'px';
 pop.style.display='block';
});
</script></body></html>"""

if __name__ == "__main__":
    main()
