#!/usr/bin/env python3
"""V2 Phase 3.2 — cross-source merge of per-resource seeds into one
unified seed entry per physical coin.

Input  : data/v2/seed/<source>/<entity>.yml         (per-resource seeds)
Output : data/v2/seed_unified/<entity>.yml          (cross-source merged)
         data/v2/match_uncertainty/<entity>.yml     (gitignored — low-confidence)

Per docs/V2_PIPELINE.md §5.2, the matcher applies a strict-primary +
loose-fallback signal hierarchy:

  PRIMARY (all must match for confident auto-merge):
    1. Metal — with billon/silver normalisation when fineness < 0.5
    2. Nominal — verbatim string equality after period-spelling normalise
    3. Catalog index chain — refs cross-checked respecting scopes:
         KM restarts per Krause volume (use entity context)
         Hede restarts per ruler (use catalog.hede_volume)
         Sieg, Schou, Lange, Galster, MB also per-author/per-volume
    4. Ruler — canonical-form equality

  FALLBACK (loose — break ties, never sole signal):
    5. Year-range overlap (≥1 year)
    6. Fineness within ±5 %
    7. Mint overlap

Decisions:
  - All 4 primary match + ≥1 fallback consistent + 0 fallback inconsistent
      → confident auto-merge
  - All primary match + fallback disagrees (e.g. weights inconsistent)
      → low-confidence (surface for curator)
  - ≥3 primary match + remaining primary missing-not-disagreeing
      → low-confidence candidate
  - Primary mismatch → no_match

Curator decision surfaces:
  - data/v2/merge_decisions/<entity>.yml   (committed; authoritative)
      merges: list of {members: [seed_ids], reason: "..."}
      no_merges: list of {members: [seed_a, seed_b], reason: "..."}
  - data/v2/match_uncertainty/<entity>.yml (gitignored; diagnostic only)

Idempotent — fresh re-runs on unchanged input produce zero file changes
(deterministic id ordering + sorted output).

Unified entry id rule (V2_PIPELINE.md §5.2 authority-based):
  Priority order for source-id prefixes: dk-hede- > dk-bruun- >
  dk-numismaster- > dk-numista- > dk-galster-. The unified entry's id
  is `unified-<top-authority-member-id>`. Prefix prevents collision
  with the seed-side id; remains readable for debugging.

Usage:
  scripts/maintenance/merge_seeds_cross_source.py --dry-run    # report only
  scripts/maintenance/merge_seeds_cross_source.py --apply      # write outputs
  scripts/maintenance/merge_seeds_cross_source.py --entity X   # one entity
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

# Ensure `scripts/` is on sys.path so `from lib.nominal_synonyms ...`
# below resolves regardless of how the script is invoked (direct
# `python scripts/maintenance/merge_seeds_cross_source.py` puts only
# `scripts/maintenance/` on the default path).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

ROOT = Path(__file__).resolve().parents[2]
V2_SEED = ROOT / "data" / "v2" / "seed"
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_MERGE_DECISIONS = ROOT / "data" / "v2" / "merge_decisions"
V2_MATCH_UNCERTAINTY = ROOT / "data" / "v2" / "match_uncertainty"


# ---------------------------------------------------------------------------
# cf-form + unlisted detection — user policy 2026-05-18
# ---------------------------------------------------------------------------
# «cf. X» refs point at a similar OTHER coin, not at this entry's own
# catalogue index. «X-unlisted» is a negative claim («this coin is NOT
# in catalogue X»). Neither belongs in catalog columns. Filter at
# ingest in _deep_merge_catalog so future seeds carrying either shape
# (e.g. Bruun harvester reading Stack's-Bowers «Fr-cf. 3089» / Lange's
# «KM-unlisted») don't re-introduce them.
_SCALAR_CF_RE = re.compile(r"^\s*(?:cf\.?\s*\S|unlisted\s*$)", re.IGNORECASE)
_OTHERS_CF_RE = re.compile(
    r"^\s*[A-Za-zÄÖÜäöüß][\w./\- ]*?(?:[-\s]+cf\.?(?:\s|\d)|[-\s]+unlisted\b)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Authority order — V2_PIPELINE.md §5.2 choice (a) confirmed by user
# ---------------------------------------------------------------------------

_ID_AUTHORITY_ORDER = [
    "dk-hede-",          # Hede 1971 (primary scholarly DK)
    "dk-bruun-",         # Stack's Bowers Bruun auction
    "dk-numismaster-",   # Krause-Mishler canonical
    "dk-numista-",       # community Numista
    "dk-galster-",       # Galster pre-1541
]


def _authority_score(coin_id: str) -> int:
    """Higher = more authority. Used to choose unified id."""
    if not coin_id:
        return -1
    for i, prefix in enumerate(_ID_AUTHORITY_ORDER):
        if coin_id.startswith(prefix):
            return len(_ID_AUTHORITY_ORDER) - i
    return 0


# ---------------------------------------------------------------------------
# Catalog-ref scoping
# ---------------------------------------------------------------------------
#
# User-confirmed (chat 2026-05-18):
#   «KM різних локацій стартують з 1 (Ш-Г vs данія, наприклад) і тому може
#    бути клеш, внутрішньо треба розрізняти це КМ данії чи КМ Ш-Г.
#    Хеде теж клешить але per ruler — Хеде#1 рулера_1 і Хеде#1 рулера_2
#    це різні монети, як і KM-DK# 1 ≠ KM-SH# 1.»
#
# Within-entity matching: per-entity loop isolates KM volumes naturally
# (danish_realm coins compare only among themselves; royal_holstein
# coins likewise). But two failure modes survive within ONE entity:
#
#   1. Mixing bare-form `catalog.km: '75'` with dict-form
#      `catalog.km: {dk: '75'}` inside one entity. Same physical KM but
#      different dict-keys (`km` vs `km/dk`) → false no_overlap.
#      FIX: entity-aware register inference — translate bare KM to
#      `km/<inferred_register>` based on entity's natural Krause volume.
#
#   2. Bare-form `catalog.hede: '156'` (no `hede_volume`) within one
#      entity that spans multiple rulers. Christian IV's Hede-156 and
#      Frederik III's Hede-156 would false-match on bare key.
#      FIX: ruler-aware scoping — when `hede_volume` is absent, derive
#      scope from the coin's `ruler` field (normalised). Always present
#      from any non-trivial source; if both sides lack ruler too, fall
#      back to bare `hede` key (still risky but rare in practice).

_ENTITY_TO_KM_REGISTER: dict[str, str] = {
    # Danish-realm tracks Krause's «Denmark» volume
    "danish_realm": "dk",
    "danish_norway": "no",       # Krause has separate Norway volume
    # SH territory — Krause «German States — Schleswig-Holstein»
    "royal_holstein": "sh",
    "gottorp_duchy": "sh",
    "schauenburg_pinneberg": "sh",
    "sonderburg_duchy": "sh",
    "norburg_plon_duchy": "sh",
    "glucksburg_duchy": "sh",
    "rantzau_county": "sh",
    "provisional_govt": "sh",
    "holstein_schauenburg_county": "sh",
    # Other German entities — each has its own Krause volume, keep
    # registers explicit so cross-entity bleed (rare) doesn't false-match
    "fuerstbisthum_luebeck": "de-fbl",
    "hanseatic_hamburg": "de-hh",
    "hanseatic_lubeck": "de-hl",
    "erzbisthum_bremen_verden": "de-bv",
    "herzogtum_braunschweig_lueneburg": "de-bl",
    "herzogtum_sachsen_lauenburg": "de-sl",
    "grafschaft_oldenburg": "de-old",
    "hochstift_osnabrueck": "de-osnabr",
    "landgrafschaft_hessen_kassel": "de-hk",
    # No register — bare KM remains ambiguous within these synthetic buckets
    # "_unclassified": None,
    # "_deprecated_gesamtstaat": None,
}


# ---------------------------------------------------------------------------
# Field normalisation
# ---------------------------------------------------------------------------


def _normalise_metal(metal, fineness):
    """billon/silver collapse when fineness < 0.5 (per §5.2 primary rule 1)."""
    if metal is None:
        return None
    m = str(metal).lower()
    # Pull a representative fineness value
    f_val = None
    if isinstance(fineness, (int, float)):
        f_val = float(fineness)
    elif isinstance(fineness, list):
        vals = [
            e.get("value") for e in fineness
            if isinstance(e, dict) and isinstance(e.get("value"), (int, float))
        ]
        if vals:
            f_val = min(vals)
    if m == "silver" and f_val is not None and f_val < 0.5:
        return "billon"
    # bronze / brass collapse to the copper base-metal tier FOR COMPARISON
    # (mirrors lib/categorize.py grouping copper/bronze/brass together).
    # A source's precise «bronze» (danskmoent.dk Rigsmønt 1856+) and a
    # museum's coarser «copper» (KMM) name the SAME base-metal coin — the
    # granularity difference must not block a merge or read as a real metal
    # disagreement. The precise stored value survives via `_collect_metal`
    # (authority-ranked), which reads the raw metal, not this normalised one.
    if m in ("bronze", "brass"):
        return "copper"
    return m


# Nominal normalisation delegates to the shared synonym table in
# `lib.nominal_synonyms` so the cross-source matcher AND the
# auto-classifier's denomination-anchor rules apply the same
# Danish↔English/German fold. Keep this thin wrapper for backwards
# compatibility — `_normalise_nominal` is called from many places
# in this module.
from lib.nominal_synonyms import normalise_nominal as _normalise_nominal_shared
from lib.catalog_codes import normalise_catalog as _fold_catalog_indices
from lib.v2_seed_writer import _canonicalise_mint
from lib.v2_entity_classify import classify_mint_to_entity


def _normalise_nominal(nominal):
    return _normalise_nominal_shared(nominal)


def _nominal_wildcard_match(na: str, nb: str) -> bool:
    """True when two NORMALISED nominals cannot be a GENUINE denomination
    difference because one side is a bare ambiguous accounting unit and the
    other a specific compound of the SAME unit at the SAME quantity:
    «daler» (could be Specie-/Rigs-/Kurant-daler) vs «speciedaler»,
    «gylden» (Sølv-/Rhinsk-) vs «rhinsk gylden». The bare unit is a
    wildcard so the nominal discriminator never SPLITS on it. Same quantity
    required; the shared unit must be ≥4 chars to avoid trivial coincidence."""
    def _split_qty(n: str):
        m = re.match(r"^(\d+(?:/\d+)?)\s+(.+)$", n)
        return (m.group(1), m.group(2)) if m else ("1", n)
    qa, ba = _split_qty(na)
    qb, bb = _split_qty(nb)
    if qa != qb or ba == bb:
        return False
    short, lng = (ba, bb) if len(ba) <= len(bb) else (bb, ba)
    return len(short) >= 4 and lng.endswith(short)


# A contemporary forgery / imitation is a DIFFERENT physical object from the
# genuine coin it copies — yet it is catalogued BY what it imitates (Hede
# tags «KMM 521» as a forfalskning of Hede 119B), so it shares the genuine
# coin's catalogue ref. Without a guard, that shared ref demotes the nominal
# discriminator and the forgery merges into the genuine type (caught 2026-06-09:
# the «1 Skilling samtidig forfalskning» bouncing onto genuine Hede 119B).
_FORGERY_RE = re.compile(
    r"forfalskning|forfalsk|\bfalsk\b|efterligning|forgery|imitation|"
    r"f[äa]lschung|nachahmung",
    re.IGNORECASE,
)


def _is_forgery_nominal(nominal) -> bool:
    """True when a nominal string carries a forgery / imitation marker
    («samtidig forfalskning», «falsk 8 Skilling», «efterligning», …)."""
    return bool(nominal and _FORGERY_RE.search(str(nominal)))


_ARABIC_ROMAN = {
    1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v", 6: "vi", 7: "vii", 8: "viii",
    9: "ix", 10: "x", 11: "xi", 12: "xii", 13: "xiii", 14: "xiv", 15: "xv",
    16: "xvi", 17: "xvii", 18: "xviii", 19: "xix", 20: "xx",
}


def _regnal_arabic_to_roman(s: str) -> str:
    """Convert a TRAILING 1-2-digit regnal number to roman for MATCHING.
    ucoin / Numista write «Christian 4» / «Frederik 3»; Hede / Bruun write
    «Christian IV» / «Frederik III» — same monarch, but the arabic-vs-roman
    numeral fragments every Danish king (≈19k coins). Canonicalise to roman.

    GUARDS (so two different rulers are never folded):
      • only a TRAILING number is converted (with optional «?»), so
        «Karl 3 Johan» (embedded → Karl XIV Johan) is left alone;
      • the name-part must carry NO other digit and NO joint/uncertain
        separator («eller» / «or» / «/»), so «Frederik 7 eller Christian 9»
        is left alone;
      • numbers outside 1-20 are left as-is.
    Matching only — the stored ruler keeps its source form.
    """
    m = re.match(r"^(.+?)\s*(\d{1,2})\??$", s)
    if not m:
        return s
    name = m.group(1).strip()
    if not name or re.search(r"\d", name):
        return s
    if any(tok in name for tok in (" eller ", " or ", "/")):
        return s
    roman = _ARABIC_ROMAN.get(int(m.group(2)))
    return f"{name} {roman}" if roman else s


@lru_cache(maxsize=None)
def _normalise_ruler(ruler):
    """Canonicalise a ruler string for cross-source comparison.

    @lru_cache: pure str→str (ruler is a scalar string or None). Profiling
    the royal_holstein merge showed this called 1.55 M times costing 21 s
    uncached — the same shape as `_normalise_nominal`, which costs 0.28 s
    BECAUSE it is cached. match_pair re-normalises the same handful of ruler
    strings across every O(n²) pair; memoising collapses that to one compute
    per distinct ruler. (2026-06-04 perf pass.)

    Variants normalised to the same form (so reign-index queries +
    cross-source matcher hits don't fragment over spelling artefacts):

      «Christian IV.»     →  «christian iv»
      «Christian IV»      →  «christian iv»
      «Christian IV. (1588-1648)»  →  «christian iv»
      «Christian VII, der …»  →  «christian vii»
      «Frederik IV 1699 - 1730»  →  «frederik iv»  (NumisMaster reign-bleed)
      «Christian VII 1766 - 1808 Issuer: Danish …»  →  «christian vii»  (NumisMaster Issuer-bleed)
      «Friedrich III. von Schleswig-Holstein-Gottorp»  →  «friedrich iii»

    Returns lowercased, trailing-period-stripped, single-spaced.
    """
    if not ruler:
        return ""
    s = str(ruler)
    # Drop parenthetical reign annotations, e.g. «(1588-1648)»
    s = s.split("(")[0]
    # Drop comma-tail descriptive epithets, e.g. «Christian VII, der …»
    s = s.split(",")[0]
    # Drop «Issuer:» bleed-through from NumisMaster pages
    s = re.split(r"\s+Issuer\s*:", s, maxsplit=1)[0]
    # Drop trailing «1699 - 1730» reign-year tail (NumisMaster mass-pollution
    # already handled by parse_numismaster._clean_ruler, but defensive here
    # so older seeds + future sources stay normalised)
    s = re.sub(r"\s+\d{4}\s*-\s*\d{0,4}\s*$", "", s)
    # Drop «von <house>» / «af <kingdom>» trailing peerage
    s = re.split(r"\s+(?:von|af|of|zu)\s+", s, maxsplit=1)[0]
    # Strip trailing dots + whitespace, normalise internal whitespace.
    # Combined `[\s.]+$` handles the «Christian IV. (1588-1648)» path
    # where split("(")[0] leaves «Christian IV. » — trailing space had
    # to be stripped BEFORE the dot-strip could catch the dot, otherwise
    # «christian iv.» leaked through with dot intact.
    s = re.sub(r"[\s.]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    # English / parser-artefact spelling normalisations. The Danish
    # form is «Frederik» (no `c` before `k`); some sources / parsers
    # render it «Frederick» which fragments index attestation. Same
    # for «Christian» (no variant) — kept for symmetry future-proof.
    # «Frederick»(en) / «Friedrich»(de) / «Friederich»(typo) → «frederik»
    # (Danish canonical). MATCHING-only spelling fold. Safe despite German
    # «Friedrich» rulers being distinct people from Danish «Frederik»: the
    # matcher is per-entity (cross-entity Friedrichs never compared) and
    # match_pair's year/catalog fallback separates same-name-same-numeral
    # rulers within an entity (e.g. _unclassified «Friedrich III» 1491 vs
    # 1888 → years disagree → no_match). Verified per-entity 2026-06-03.
    s = re.sub(r"\b(?:frederick|friedrich|friederich)\b", "frederik", s)
    # Cross-language ruler-name synonyms — different sources use the
    # English vs Danish/Norwegian form for the same monarch.
    #
    #   «John I» / «John I (Hans I)» (Numista English) ↔ «Hans» (Bruun,
    #       Hede, danskmoent.dk Danish form). Hans of Denmark (1455-1513)
    #       reigned 1481-1513 as Hans / Johann / John I.
    #   «John II» (Sweden side via Kalmar Union) — same Hans, period
    #       Swedish attestation. Same canonical.
    #   «Eric» ↔ «Erik» (Erik VII of Pomerania, Erik XIV, etc.)
    #   «Margaret» ↔ «Margrethe» (Margrethe I, Margrethe II).
    #
    # Canonical form is the Danish (matches Hede/Galster/our project YAML).
    # The parenthetical clipping above («John I (Hans I)» → «John I») runs
    # before lowercase, so by the time we get here the input is the bare
    # English form.
    if s in ("john i", "john ii"):
        s = "hans"
    s = re.sub(r"\beric\b", "erik", s)
    s = re.sub(r"\bmargaret\b", "margrethe", s)
    # Leading ruler-TITLE strip — «Hertug …»/«Herzog …»/«Duke …»/«Ærkebisp …»
    # /«Erkebisp …»/«Archbishop …» are not part of the identity (the name
    # discriminates). Folds «Hertug Johan Adolf» → «johan adolf» and
    # «Ærkebisp Johann Friedrich» → «johann friedrich» (Bremen-Verden
    # archbishop — now safe to fold with the Frederik spelling work below).
    s = re.sub(r"^(?:hertug(?:en)?|herzog|duke|ærkebisp(?:pen)?|erkebisp|archbishop)\s+", "", s)
    #   «Johan Adolf» / «Johan Adolph» / «Johan Adolg»(typo) / «Johann Adolf»
    #   / Adolph — Danish «Johan»(1n) vs German «Johann»(2n) + adolf/adolph
    #   spelling of the SAME Holstein-Gottorp duke (r. 1590-1616). Reign-
    #   window + entity survey (2026-06-03) confirms every NO-NUMERAL form
    #   is this one duke (gottorp/royal_holstein/danish_realm, 1579-1615).
    #   The numeral-lookahead guard keeps «Johann Adolph I» (Holstein-
    #   Norburg-Plön, 1690) DISTINCT; the per-entity matcher prevents the
    #   pre-existing gottorp↔norburg_plön «johann adolf» label overlap from
    #   cross-merging. «John Adolphus» (English) is handled by the next sub.
    s = re.sub(r"\bjohann?\s+adol(?:f|ph|g)\b(?!\s+[ivx]\b)", "johann adolf", s)
    #   «John Adolphus» (Numista English) ↔ «Johann Adolf» (German) —
    #   Johann Adolf von Holstein-Gottorp, Duke 1590-1616. Verified safe by
    #   reign-window + entity survey (2026-06-03): the bare «John Adolphus»
    #   form appears only in gottorp_duchy 1590-1611 = this one duke.
    #   GUARDS (negative lookahead on a trailing roman numeral):
    #     - «John Adolphus I» (Holstein-Norburg-Plön, 1690) — a DIFFERENT
    #       duke — stays untouched (the «I» blocks the match).
    #     - Bare «Adolf» (grandfather Adolf I, 1544-1586), Schauenburg counts
    #       «Adolf XIII/XIV», «Hans Adolf», «Adolf Friedrich» are different
    #       strings → never touched.
    #   The matcher is per-entity, so even the pre-existing «johann adolf»
    #   gottorp↔norburg_plön label overlap can't cross-merge.
    s = re.sub(r"\bjohn adolphus\b(?!\s+[ivx]\b)", "johann adolf", s)
    #   «John/Johan/Johann Frederik» — Danish «Johan»(1n)/English «John» vs
    #   German «Johann»(2n) of the SAME compound-name ruler (Friedrich→
    #   frederik already applied above). Per-entity matcher + reign window
    #   verified one ruler per entity (e.g. Bremen-Verden archbishop Johann
    #   Friedrich 1596-1622). Numeral guard keeps «Johann Frederik I»
    #   (Saxony elector, 1535) DISTINCT; bare «Johan»/«John» (Hans the
    #   Younger / John I of Denmark) is untouched (only the +Frederik
    #   compound folds).
    s = re.sub(r"\bjoh(?:n|an|ann)\s+frederik\b(?!\s+[ivx]\b)", "johann frederik", s)
    #   «Christian Albert»(en) ↔ «Christian Albrecht»(de) — Christian Albrecht
    #   von Holstein-Gottorp, Duke 1659-1695. Reign-window + entity survey
    #   (2026-06-03): both forms = this one duke (gottorp/royal_holstein/
    #   danish_realm/hamburg, 1661-1694). Fold to the German canonical.
    #   Targets only the «Christian Alb…» compound, so bare «Albrecht»
    #   (Wallenstein etc.), «Johan Albrecht I», «Albrecht II. Alcibiades»
    #   are untouched; numeral guard reserves any future «Christian Albrecht I».
    s = re.sub(r"\bchristian\s+alb(?:recht|ert)\b(?!\s+[ivx]\b)", "christian albrecht", s)
    # Cross-language ruler-NAME translations — NAME component only, the
    # regnal NUMERAL is preserved (user direction 2026-06-09: «імʼя не може
    # йти окремо від порядкового номера»). Numista publishes English ruler
    # names; NumisMaster / Bruun / Hede the German/Danish form. Folding the
    # NAME (not the numeral) lets «Charles Frederick» ≡ «Karl Friedrich»
    # and «Francis William» ≡ «Franz Wilhelm» merge, while «George IV»
    # stays ≠ «Charles II» (different name → «georg iv» ≠ «karl ii») and
    # «Frederik VI» stays ≠ «Frederik IX» (different numeral). The POLITY is
    # handled by the per-entity matcher — same name+numeral in two
    # different issuing entities is never compared (so a same-named ruler
    # of two different lands cannot cross-merge). Whole-word, German-states
    # canonical (every Charles/Karl, George/Georg, etc. in scope is a
    # German/Norwegian/Swedish ruler — there is no Danish «Karl»).
    s = re.sub(r"\bcharles\b", "karl", s)
    s = re.sub(r"\bgeorge\b", "georg", s)
    s = re.sub(r"\bwilliam\b", "wilhelm", s)
    s = re.sub(r"\bfrancis\b", "franz", s)
    s = re.sub(r"\bernest\b", "ernst", s)
    s = re.sub(r"\baugustus\b", "august", s)
    s = re.sub(r"\bhenry\b", "heinrich", s)
    s = re.sub(r"\berich\b", "erik", s)
    s = re.sub(r"\badolphus\b", "adolf", s)
    # Arabic→roman regnal numeral (Christian 4 → christian iv, etc.) — LAST,
    # after spelling/synonym folds, so the name-part is already canonical.
    s = _regnal_arabic_to_roman(s)
    return s


def _coin_years(coin: dict) -> set[int]:
    """All years this coin's type was attested for, expanded from either
    `year_ranges: [[lo, hi], ...]` or `year_first`..`year_last`.

    Used by `_build_reign_index` (which years does this coin's ruler
    cover?) and by `_infer_ruler` (which years does this coin claim,
    so we can look up the unambiguous ruler?).
    """
    years: set[int] = set()
    yr = coin.get("year_ranges")
    if isinstance(yr, list) and yr:
        for r in yr:
            if isinstance(r, (list, tuple)) and len(r) == 2:
                try:
                    lo, hi = int(r[0]), int(r[1])
                    if hi < lo:
                        lo, hi = hi, lo
                    years.update(range(lo, hi + 1))
                except (TypeError, ValueError):
                    continue
    else:
        yf, yl = coin.get("year_first"), coin.get("year_last")
        if isinstance(yf, int):
            yl_int = yl if isinstance(yl, int) else yf
            if yl_int < yf:
                yf, yl_int = yl_int, yf
            years.update(range(yf, yl_int + 1))
    return years


# ---------------------------------------------------------------------------
# Hede-volume reign windows — per-volume parser-anomaly filter for D33
# ---------------------------------------------------------------------------
# danskmoent.dk Hede catalog is organised by ruler-volumes: `c4h*` is the
# Christian IV volume, `f3h*` is Frederik III, etc. The volume code is
# the parser's canonical attribution of WHICH ruler a Hede entry
# documents — it's encoded in the URL path and never ambiguous. The
# `year_first` / `year_last` fields, by contrast, occasionally suffer
# parser-anomalies (an OCR-or-regex glitch reads 1746 as 1646, or a
# type-continuity range overshoots the issuing ruler's death-year by
# decades — captured 2026-05-18 audit found 11 such cases).
#
# When building the D33 reign index, we use this table to drop
# (year, ruler) attestations whose year falls OUTSIDE the volume's
# documented reign window — the bad year never poisons the index,
# while genuinely-attested in-window years contribute as normal. The
# seed itself stays untouched (parser-fix is a separate task; this is
# a defensive filter at the merger layer).
#
# Window endpoints are inclusive on both sides. Transition years (king
# A dies + king B crowned same calendar year) appear in BOTH adjacent
# windows by design — both rulers can legitimately have struck coins
# in that year, so multi-ruler attestation is the correct outcome.
#
# Source: Wilcke 1950 / Hede 1957 (Danish royal reign chronology) — a
# well-established historical record, not invented; per CLAUDE.md §0
# this category of attested historical knowledge is a valid source.
# Hede volume codes (`c4h`, `f3h`, …) carry both the ruler attribution
# (encoded in the volume letter + roman-numeral integer) AND the reign
# window. Together they let the D33 reign-index construction:
#   (a) OVERRIDE the seed's `ruler` field with the volume-canonical
#       label when they disagree (real cases captured 2026-05-18:
#       `dk-hede-c9h1a` has ruler="Christian VIII." but volume=`c9h`
#       means Christian IX — the page's catalog scope is authoritative);
#   (b) FILTER per-year attestations to the ruler's actual reign window
#       (real cases captured 2026-05-18: `dk-hede-f5h3ab` parsed year
#       1646 for a Frederik V coin — FR V reigned 1746-1766; the
#       attestation is dropped so it doesn't poison the index).
#
# The reign window is also exposed by ruler-name (`_DK_RULER_REIGNS`)
# so non-Hede sources (NumisMaster, Numista, Bruun, Galster) can use
# the SAME filter when their seed's `ruler` field attests a king for
# a year outside that king's reign (captured 2026-05-18:
# `denmark-numismaster-165534` attests Frederik III for year 1633 —
# FR III reigned 1648-1670, that 1633 attestation is wrong).
#
# Source: Wilcke 1950 / Hede 1957 (Danish royal reign chronology) — a
# well-established historical record, not invented; per CLAUDE.md §0
# this category of attested historical knowledge is a valid source.
# (Reign windows scoped to the Danish realm. Other entities like
# `gottorp_duchy`, `schauenburg_pinneberg` use entirely different
# ruler timelines and would need their own tables when D33 fires for
# those — currently they have ≤3 cross-source low-confidence pairs,
# so the Danish table covers the 99 %+ case.)
_HEDE_VOLUME_TO_RULER: dict[str, str] = {
    "c2h": "christian ii",
    "f1h": "frederik i",
    "c3h": "christian iii",
    "f2h": "frederik ii",
    "c4h": "christian iv",
    "f3h": "frederik iii",
    "c5h": "christian v",
    "f4h": "frederik iv",
    "c6h": "christian vi",
    "f5h": "frederik v",
    "c7h": "christian vii",
    "f6h": "frederik vi",
    "c8h": "christian viii",
    "f7h": "frederik vii",
    "c9h": "christian ix",
    "f8h": "frederik viii",
    "c10h": "christian x",
}

_DK_RULER_REIGNS: dict[str, tuple[int, int]] = {
    "christian ii": (1513, 1523),
    "frederik i": (1523, 1533),
    "christian iii": (1534, 1559),
    "frederik ii": (1559, 1588),
    "christian iv": (1588, 1648),
    "frederik iii": (1648, 1670),
    "christian v": (1670, 1699),
    "frederik iv": (1699, 1730),
    "christian vi": (1730, 1746),
    "frederik v": (1746, 1766),
    "christian vii": (1766, 1808),
    "frederik vi": (1808, 1839),
    "christian viii": (1839, 1848),
    "frederik vii": (1848, 1863),
    "christian ix": (1863, 1906),
    "frederik viii": (1906, 1912),
    "christian x": (1912, 1947),
}


def _hede_volume_to_ruler(coin: dict) -> str | None:
    """Map the coin's Hede volume code to its canonical normalised
    ruler label. The `n` prefix (Norge sub-catalogue) is stripped first
    since the same monarch ruled both kingdoms in personal union.
    Returns None for non-Hede entries or Hede entries lacking a parsed
    volume code.
    """
    vol = ((coin.get("catalog") or {}).get("hede_volume") or "").strip().lstrip("n")
    if not vol:
        return None
    return _HEDE_VOLUME_TO_RULER.get(vol)


def _attestation_ruler(coin: dict) -> str | None:
    """Pick the authoritative normalised-ruler attestation for an
    index-building pass:
      • Hede sources → derive from `hede_volume` code (parser-canonical,
        immune to ruler-field mislabels);
      • Non-Hede sources → fall back to `_normalise_ruler(coin.ruler)`.
    Returns None when neither path yields a ruler.
    """
    rn = _hede_volume_to_ruler(coin)
    if rn:
        return rn
    return _normalise_ruler(coin.get("ruler")) or None


# Entities where the ruler is unambiguously a Danish-monarchy king
# (Danish-Norwegian personal union 1380-1814, plus Holstein-Glückstadt
# under Danish sovereignty 1544+). For these we apply STRICT reign
# filtering: an attestation whose normalised ruler isn't in
# `_DK_RULER_REIGNS` is dropped entirely (treated as parser-anomaly
# bad data). Real example caught 2026-05-18: NumisMaster MC pages
# for Danish 1809-1810 coins of Frederik VI rendered as «Frederick IX»
# (FR IX reigned 1947-1972, never could have signed 1809 coins) —
# visual VI / IX confusion in their data entry.
_DK_REALM_ENTITIES = frozenset({"danish_realm", "danish_norway", "royal_holstein"})


def _build_reign_index(coins: list[dict], entity_id: str | None = None) -> dict[int, set[str]]:
    """Build `{year → set(normalised_rulers)}` index from coins of ONE
    entity that DO carry an attested ruler. Per CLAUDE.md §0 / D33 the
    inference downstream is conservative: it ONLY fires when a year
    maps to a singleton ruler set in this index.

    The index is built in two passes:

    1. **Raw attestation pass** — each coin's `(year, ruler)` pair
       contributes to the raw index. Years where multiple distinct
       rulers are attested across the corpus (real transition years
       like 1648 / 1670 / 1808 + data anomalies where some source
       mislabelled a ruler) end up with a multi-element set.

    2. **Contiguous-reign gap-fill pass** — for any year `y` between
       the min and max attested years that is NOT covered by step 1,
       look at the closest preceding attested year `p` and closest
       following attested year `n`. When BOTH `index[p]` and
       `index[n]` are the SAME singleton set `{R}`, fill `y` with
       `{R}`. Rationale: if the reign-corpus says CHR IV alone in
       1605 and CHR IV alone in 1612, the gap years 1606-1611 are
       unambiguously also CHR IV — no seed coin happens to be dated
       to those in-between years, but the bracket guarantees no king
       changed in the interval. The two-sided bracket ensures the
       fill never extends past either end of a reign.

    Transition years (king-A dies + king-B crowned in same calendar
    year), separatist / co-regent windows, and any year where two
    different ruler labels were attested across the corpus end up with
    a multi-element set — `_infer_ruler` returns None for those and
    leaves the ruler null. Better null than a false attribution per
    user direction 2026-05-18.
    """
    raw: dict[int, set[str]] = {}
    strict_dk = entity_id in _DK_REALM_ENTITIES
    for c in coins:
        # Pick the authoritative ruler for this attestation: Hede →
        # volume-canonical (immune to seed-field mislabels); other
        # sources → seed's `ruler` field. See `_attestation_ruler`.
        rn = _attestation_ruler(c)
        if not rn:
            continue
        reign_window = _DK_RULER_REIGNS.get(rn)
        if strict_dk and reign_window is None:
            # Strict DK-realm filter: a ruler-name not in the Danish
            # royal chronology (e.g. NumisMaster's «Frederick IX» on
            # an 1809 coin) is parser-anomaly bad data. Drop the
            # entire attestation rather than letting it poison the
            # year's ruler-set.
            continue
        for y in _coin_years(c):
            if reign_window is not None:
                lo, hi = reign_window
                if y < lo or y > hi:
                    continue
            raw.setdefault(y, set()).add(rn)

    if not raw:
        return raw

    extended = dict(raw)
    known = sorted(raw)
    min_y, max_y = known[0], known[-1]
    # Build a sparse lookup for prev/next attested year per gap year.
    # Walk forward through the year range once, tracking the most-recent
    # singleton-attested year on the left; for each gap year, look ahead
    # to the next singleton-attested year on the right.
    last_singleton: tuple[int, str] | None = None
    next_singleton_after: dict[int, tuple[int, str]] = {}
    next_known: tuple[int, str] | None = None
    for y in range(max_y, min_y - 1, -1):
        if y in raw and len(raw[y]) == 1:
            next_known = (y, next(iter(raw[y])))
        if next_known is not None:
            next_singleton_after[y] = next_known
    for y in range(min_y, max_y + 1):
        if y in raw and len(raw[y]) == 1:
            last_singleton = (y, next(iter(raw[y])))
            continue
        if y in raw:
            # multi-attest year — never gap-fill, never advance singleton
            continue
        next_pair = next_singleton_after.get(y + 1)
        if last_singleton is None or next_pair is None:
            continue
        # Both bracket years attest the same single ruler with no
        # multi-attest year in between (we'd have hit `continue` above
        # before reaching this y).
        if last_singleton[1] == next_pair[1]:
            extended[y] = {last_singleton[1]}
    return extended


def _infer_ruler(coin: dict, reign_index: dict[int, set[str]]) -> str | None:
    """Look up the coin's year(s) in the entity-scoped reign index.

    Resolves to a single inferred ruler under the «singleton-anchored
    + transition-tolerant» rule:

    1. Walk every year in the coin's covered span. Each year contributes
       its ruler-set from the index (singleton, multi-element, or
       missing).
    2. Years where the index is missing the year entirely → return None
       (genuine ignorance — better null than guess).
    3. Collect the set of SINGLETON rulers across the coin's years
       (`singletons`) and the list of MULTI-ELEMENT ruler-sets
       (`multi_sets`).
    4. Require ≥1 singleton anchor — if every year touches a transition
       year only, the coin is genuinely ambiguous and the inference
       returns None. This handles real single-year-on-transition coins
       (e.g. a 1648 1/4 Speciedaler can be CHR IV's or FR III's; we
       refuse to pick).
    5. All singletons must agree on one ruler R. If two years attest
       different singletons, the coin crosses reigns → None.
    6. Every multi-ruler year's set must CONTAIN R. This allows a
       coin whose span includes a transition year (e.g. 1667-1670
       with all of 1667-1669 attesting FR III alone and 1670
       attesting both CHR V + FR III) to confidently infer FR III —
       the transition year's set is a superset of the singleton.
       But disallows inferring R when a multi-set excludes R
       (meaning we're conflating two reigns).
    7. With all checks passed, return R.

    Per user direction 2026-05-18 «краще мати null і продовжити
    шукати правду ніж поставити неправдивий nonull value».
    """
    years = _coin_years(coin)
    if not years:
        return None

    singletons: set[str] = set()
    multi_sets: list[set[str]] = []
    for y in years:
        rulers = reign_index.get(y)
        if not rulers:
            return None
        if len(rulers) == 1:
            singletons.add(next(iter(rulers)))
        else:
            multi_sets.append(set(rulers))

    if not singletons:
        # All covered years are multi-ruler (transition-only span) —
        # genuinely ambiguous, stay null.
        return None
    if len(singletons) > 1:
        # Span crosses two distinct reigns — can't pick one.
        return None

    R = next(iter(singletons))
    for s in multi_sets:
        if R not in s:
            # A multi-set in the span excludes our singleton ruler —
            # the coin's coverage doesn't cohere around a single
            # reign; stay null.
            return None
    return R


# Davenport `dav` VALUE normaliser — for MATCHING comparison only (stored
# values keep their source form per §data-accumulation). Davenport's regional
# sub-catalogues label the number with a series + roman volume: «European
# Crowns» EC I-IV, «German Talers» GT I-III, plus ST / CCT / SG / Lg / BrSL /
# AAO / ECT. Sources differ on including it — Numista «EC II 3682» vs Bruun
# bare «3682» for the SAME coin — so a bare number never matched a prefixed
# one and the catalog chain falsely disagreed (caught 2026-06-03 on Gottorp
# KM-21 Taler/Thaler). Strip the series prefix + «#» so the numeric core
# matches. Cross-series same-number collision (EC 8982 vs GT 8982) is
# tolerated: dav is one of several catalog signals; the holistic chain +
# primary signals (km / hede / ruler / metal) still separate distinct coins.
_DAV_SERIES_PREFIX_RE = re.compile(
    r"^(?:ECT|EC|GT|ST|CCT|SG|Lg|BrSL|AAO)\b\s*[IVX]*\s*#?\s*", re.IGNORECASE)


def _normalise_dav_value(v: str) -> str:
    s = str(v).strip()
    stripped = _DAV_SERIES_PREFIX_RE.sub("", s).strip()
    return stripped or s


def _split_multi(val) -> list[str]:
    """Flatten a catalog value (scalar or list) into individual ref values,
    splitting an «A / B» slash-multi scalar into its members. ucoin / Numista
    pack sub-variants as «125A / 125B» / «3679 / 3679A» in ONE string; left
    whole that value equals NEITHER «125A» nor «125B», so the matcher misses
    the overlap and a same-coin cross-source merge is silently blocked. (Same
    normalisation catalog_codes.normalise_catalog applies at write/display
    time — done here so matching is correct even on not-yet-renormalised
    seeds.)"""
    out: list[str] = []
    for v in (val if isinstance(val, list) else [val]):
        s = str(v).strip()
        if "/" in s:
            out.extend(p.strip() for p in s.split("/") if p.strip())
        elif s:
            out.append(s)
    return out


# Per-coin memo for _catalog_refs. _catalog_refs is a pure function of
# (coin, entity_id), but within ONE process_entity run the entity_id is
# constant and the coin dicts are stable objects (held in seeds_by_id), so
# we key by id(coin) alone. The O(n²) pre-pass calls _catalog_refs 4× per
# pair (≈179M times on danish_realm) though there are only n distinct coins
# — memoising collapses that to n computations.
#
# DANGER — id(coin) is reused after GC. The memo is therefore ONLY safe when
# (a) it is cleared between entities, and (b) the cached coin objects are not
# mutated. The cross-source merger satisfies both, so it OPTS IN by setting
# `_CATALOG_REFS_MEMO_ENABLED = True` inside process_entity (after the clear).
# Every OTHER caller — notably absorb_seeds_into_final_v2.py, which imports
# match_pair / _catalog_refs and runs many entities in ONE process WITHOUT
# clearing AND mutates catalog during enrichment — leaves the flag at its
# default False and so always computes fresh. (Caught 2026-06-02: with the
# memo unconditionally on, a full absorb run cross-contaminated entities via
# id() reuse, e.g. danish_realm reported 17 self-foundation folds instead of
# the correct 1.)
_CATALOG_REFS_MEMO: dict[int, dict[str, str]] = {}
_CATALOG_REFS_MEMO_ENABLED: bool = False


def _catalog_refs(coin: dict, entity_id: str | None = None) -> dict[str, str]:
    """Return dict of {scope_key: ref_value} for every catalog ref.
    Keys encode scope so cross-volume / cross-ruler collisions don't
    false-match (per user reminder: KM-DK#1 ≠ KM-SH#1; Hede#1 of
    Christian IV ≠ Hede#1 of Christian VII).

    Scope-key shape:
      'km/{register}' — for KM. Dict-form contributes one key per
                        register. Bare-form maps to the entity's
                        default register (`_ENTITY_TO_KM_REGISTER`)
                        OR drops to bare `'km'` when entity has no
                        mapping.
      'hede/{ruler}'  — for Hede. Derived from coin's `ruler` field
                        (normalised) when present, else from
                        `catalog.hede_volume` lookup. Falls back to
                        bare `'hede'` only when both unavailable.
      Single-source refs (sieg/schou/lange/galster_volume/fr/dav/mb/
        jensen_skjoldager/schive/skaare/friedberg/davenport) — verbatim
        field name (publication-stable scope, no ruler clash).
    """
    if _CATALOG_REFS_MEMO_ENABLED:
        _cached = _CATALOG_REFS_MEMO.get(id(coin))
        if _cached is not None:
            return _cached
    cat = coin.get("catalog") or {}
    refs: dict[str, str] = {}

    km = cat.get("km")
    if km is not None:
        def _km_join(vals):
            # "|"-join distinct values so _catalog_chain_consistent's
            # set-intersection sees every KM of a multi-KM (curator-merged)
            # coin — same convention as hede/sieg list-form refs.
            seen: list[str] = []
            for v in vals:
                s = str(v).strip()
                if s and s not in seen:
                    seen.append(s)
            return "|".join(seen)
        if isinstance(km, dict):
            for reg, v in km.items():
                vv = v if isinstance(v, list) else [v]
                refs[f"km/{reg.lower()}"] = _km_join(vv)
        else:
            vals = km if isinstance(km, list) else [km]
            # Bare KM — infer register from entity context.
            register = _ENTITY_TO_KM_REGISTER.get(entity_id or "")
            refs[f"km/{register}" if register else "km"] = _km_join(vals)

    hede = cat.get("hede")
    if hede is not None:
        # Scope = ruler-canonical first (preferred since ruler field is
        # the authoritative «which king's Hede catalog» signal); fall
        # back to hede_volume code from URL; finally bare-key.
        ruler_norm = _normalise_ruler(coin.get("ruler"))
        vol = (cat.get("hede_volume") or "").strip()
        if ruler_norm:
            scope = ruler_norm
        elif vol:
            scope = vol
        else:
            scope = ""
        key = f"hede/{scope}" if scope else "hede"
        hede_vals = _split_multi(hede)
        refs[key] = "|".join(sorted(hede_vals)) if hede_vals else str(hede).strip()

    # Per-publication catalog identifiers — each is unique within its own
    # scope. Disagreement on any of these = different physical coins.
    # `numista` + `bruun_collection_id` included: same physical coin
    # generally has one Numista N# and one Bruun collection-id; two
    # records with different IDs = different specimens (Bruun) or sub-
    # variants (Numista) and should NOT auto-merge without curator
    # decision via merge_decisions/<entity>.yml.
    #
    # Bruun_part / bruun_lot_no / bruun_page are SPECIMEN-level — two
    # lots can be the same type; excluded from match comparison.
    # Catalog-key synonym table. Different parsers / catalogues use different
    # short tokens for the same publication; map them all to one canonical
    # ref-key so the cross-source matcher sees overlap. Without this:
    #   - Numista publishes `cat.fr: "3"` (Friedberg «Gold Coins of the World»)
    #   - Bruun parser emits `cat.friedberg: "3"` (same Friedberg)
    #   - `_catalog_chain_consistent` saw refs[{fr:3}] vs refs[{friedberg:3}]
    #     → zero overlap → primary["catalog"] = None → match_pair couldn't
    #     promote the merge.
    # Likewise `dav` (Numista) ↔ `davenport` (Bruun) reference the same
    # Davenport «European Crowns» catalogue; canonical is `dav`.
    CATALOG_KEY_SYNONYMS = {
        "friedberg": "fr",
        "davenport": "dav",
    }
    for field in ("lange", "fr", "dav", "mb",
                  "jensen_skjoldager", "schive", "skaare", "friedberg",
                  "davenport", "numista", "bruun_collection_id"):
        val = cat.get(field)
        if val is None:
            continue
        canonical = CATALOG_KEY_SYNONYMS.get(field, field)
        _items = _split_multi(val)
        if canonical == "dav":
            _items = [_normalise_dav_value(x) for x in _items]
        new_val = "|".join(sorted(_items)) if _items else str(val).strip()
        # When both synonyms attest the same key (e.g. coin has both `fr` and
        # `friedberg` set), merge values rather than letting the later one
        # overwrite. Preserves §«Data-accumulation principle».
        if canonical in refs and refs[canonical] != new_val:
            joined = sorted(set(refs[canonical].split("|")) | set(new_val.split("|")))
            refs[canonical] = "|".join(joined)
        else:
            refs[canonical] = new_val

    # ── Catalogue-index RESTART-SCOPE registry (§9.4, user direction
    # 2026-06-08: «всі індекси … зважати на те коли вони рестартують») ──
    # Two records that share an index VALUE identify the same coin ONLY
    # when they also share that index's RESTART-SCOPE. Each catalogue
    # restarts its numbering along a different dimension:
    #
    #   per RULER    Hede, Schou, Sieg — Danish royal reign-numbered
    #                catalogues; sequence restarts at 1 each reign.
    #                (empirical xRuler-collision: Hede 59 %, Schou 64 %,
    #                Sieg 42 % of distinct values span ≥2 reigns).
    #                → key «<idx>/<ruler>».  hede + schou handled in their
    #                own blocks (hede above, schou+sieg here).
    #   per VOLUME   Galster — keyed «galster/<vol>» (vol ≈ reign).
    #   per REGISTER KM — Krause restarts per country/region; keyed
    #                «km/<register>» (xEntity-collision 43 %).
    #   GLOBAL       Friedberg, Davenport(Dav), Numista N#,
    #                bruun_collection_id, Lange, mb, NMD, Schive, Skaare,
    #                Jensen-Skjoldager, FP, Behrens, … — continuous /
    #                world catalogues (all <5 % xRuler, ~0–6 % xEntity):
    #                bare key, handled by the global loop above.
    #
    # Schou + Sieg share the reign-scope derivation (ruler field first,
    # else the hede_volume code which encodes the reign). Within the
    # per-entity matcher the ruler is the right granularity (Danish vs
    # Norwegian numbering is already separated by entity).
    _reign = _normalise_ruler(coin.get("ruler")) or (
        cat.get("hede_volume") or "").strip()
    for _ridx in ("schou", "sieg"):
        _v = cat.get(_ridx)
        if _v is None:
            continue
        _key = f"{_ridx}/{_reign}" if _reign else _ridx
        _vals = _split_multi(_v)
        refs[_key] = "|".join(sorted(_vals)) if _vals else str(_v).strip()

    galster = cat.get("galster")
    if galster is not None:
        # Galster catalogue is per-ruler (Christian II = c2g, Frederik I = f1g,
        # Christian III = c3g, ...). When the entry carries galster_volume
        # explicitly, scope by that. Otherwise fall back to ruler-derived
        # scope so two records pointing at the same ruler's Galster volume
        # compare as same-scope. Without this, Numista entries (which
        # publish galster ref but no galster_volume) end up in the bare
        # `galster` scope while Galster-source entries land in
        # `galster/<vol>` → no_overlap → false-positive merges with
        # disagreeing galster numbers (caught 2026-05-20 audit on Numista
        # 474583 — Galster 101 vs Galster 103 silently merged).
        vol = (cat.get("galster_volume") or "").strip()
        if not vol:
            # Derive volume code from ruler. Pattern: lowercase initial
            # of forename + numeral + 'g'. «Christian III» → «c3g»,
            # «Frederik I» → «f1g», «Christian II» → «c2g». For Erik VII
            # and other less-common rulers no mapping yet — fall through
            # to bare scope.
            ruler_norm = _normalise_ruler(coin.get("ruler"))
            if ruler_norm:
                # _normalise_ruler returns lowercase, so match case-insens.
                # The ordinal is OPTIONAL: Hans (1481-1513) carries no
                # ordinal («Hans», not «Hans I» — he's the only
                # Danish-Norwegian Hans), and his Galster volume code is
                # the bare-initial «hg». Without the optional-numeral
                # branch, a no-ordinal Hans ref stayed bare `galster`
                # while the Galster-source entry sat in `galster/hg`, so
                # the same Galster 24 (1 Nobel) never merged across
                # sources (caught 2026-06-10 on Bruun-3831 ↔ galster-hg-24).
                m = re.match(r"(christian|frederik|hans|erik|knud)"
                             r"(?:\s+([ivx]+|\d+))?\.?", ruler_norm,
                             flags=re.IGNORECASE)
                if m:
                    name_initial = m.group(1)[0].lower()
                    num = m.group(2)
                    roman_map = {"I": "1", "II": "2", "III": "3",
                                 "IV": "4", "V": "5", "VI": "6",
                                 "VII": "7", "VIII": "8", "IX": "9", "X": "10"}
                    if num:
                        arabic = roman_map.get(num.upper(), num)
                        if arabic.isdigit():
                            vol = f"{name_initial}{arabic}g"
                    elif m.group(1).lower() == "hans":
                        # Hans — no ordinal; Galster volume code is «hg».
                        vol = "hg"
        key = f"galster/{vol}" if vol else "galster"
        if isinstance(galster, list):
            refs[key] = "|".join(sorted(str(g).strip() for g in galster))
        else:
            refs[key] = str(galster).strip()

    if _CATALOG_REFS_MEMO_ENABLED:
        _CATALOG_REFS_MEMO[id(coin)] = refs
    return refs


# Lange (Holstein) citations are list- and range-rich: a single value can be a
# comma list («404A, 405»), an inclusive range («124-131»), an abbreviated range
# («462-63» = 462-463, «280-90» = 280-290), a letter-bounded range («357A-357B»),
# or any mix («431-32, 434, 436-38»). The generic «|»-split + numeric-core path
# treats such a string as ONE opaque token, so «405» falsely disagrees with
# «404A, 405». `_lange_numbers` expands a Lange value to the SET of base catalogue
# numbers it covers; two Lange values then agree iff those sets intersect.
#
# Scoped to the `lange` register ONLY — range-expansion would corrupt registers
# where «-» is a code separator, not a range (Sieg «C3-16» is one code; Dav
# «ST 6515-6517»; etc.). It changes nothing about how the OTHER fields drive the
# consolidated match decision — it only makes Lange's own agree/disagree correct.
_LANGE_RANGE_RE = re.compile(r"^(\d+)[a-z]*-(\d+)[a-z]*$", re.IGNORECASE)
_LANGE_SINGLE_RE = re.compile(r"^(\d+)[a-z]*$", re.IGNORECASE)


def _lange_numbers(value: str) -> set[str]:
    """Expand a Lange catalogue value to the set of base numbers it covers.

    «405» → {405}; «404A, 405» → {404, 405}; «462-63» → {462, 463};
    «280-90» → {280..290}; «357A-357B» → {357}; «431-32, 434, 436-38» →
    {431, 432, 434, 436, 437, 438}. Letter suffixes collapse to the base
    number (die-variant, per §9.4). Non-numeric tokens are kept verbatim so an
    unparseable citation still self-matches."""
    out: set[str] = set()
    for tok in re.split(r"[|,]", str(value)):
        tok = tok.strip()
        if not tok:
            continue
        mr = _LANGE_RANGE_RE.match(tok)
        if mr:
            lo_s, hi_s = mr.group(1), mr.group(2)
            lo = int(lo_s)
            # Complete an abbreviated upper bound: «462-63» → hi «463»
            # (replace the lo's trailing digits with the shorter hi suffix).
            hi = int(lo_s[: len(lo_s) - len(hi_s)] + hi_s) if len(hi_s) < len(lo_s) else int(hi_s)
            if hi < lo:
                lo, hi = hi, lo
            if 0 <= hi - lo <= 60:      # sane series; avoid pathological blow-up
                out.update(str(n) for n in range(lo, hi + 1))
            else:                        # too wide → keep endpoints only
                out.update({str(lo), str(hi)})
            continue
        ms = _LANGE_SINGLE_RE.match(tok)
        if ms:
            out.add(ms.group(1))         # numeric core (drops the letter suffix)
        else:
            out.add(tok.lower())         # unparseable → verbatim self-match
    return out


def _catalog_chain_consistent(refs_a: dict, refs_b: dict):
    """Returns (state, has_overlap):
      state ∈ {'agree', 'disagree', 'no_overlap'}
      has_overlap: True if any shared key

    Multi-catalog tolerance: when ≥2 shared refs AGREE and only ONE
    disagrees, treat the chain as 'agree'. Rationale: catalogue families
    cross-classify the same physical type with different granularities.
    Galster covers parent types; Schou enumerates die / sub-variant
    refinements within a Galster type; Davenport runs at a parallel
    level. So three Bruun lots with Galster=102, Sieg=19, Dav=8226 but
    Schou=8/12/13 are by Galster's reckoning ONE coin with three Schou
    sub-variants — per CLAUDE.md §9a these merge into one entry with
    list-form Schou. Without this tolerance the merger leaves them as
    three phantom unified entries (caught 2026-05-20 audit on Bruun
    4276/4277/4278 Joachimsdaler 1537).

    Schou is the canonical «sub-variant» field on Danish coins (Schou
    catalogue numbers die-variants explicitly). Other sub-variant-style
    fields (`nmd`, `aagaard`, `schive`) follow the same pattern and
    join the sub-variant tolerance list.
    """
    shared = set(refs_a) & set(refs_b)
    if not shared:
        return ("no_overlap", False)
    # Identify «sub-variant» refs — disagreements here are weaker signal
    # because they identify die-variants, sub-types, or specimens rather
    # than coin types themselves. Bruun-collection-id is specimen-level
    # by Bruun's own cataloguing convention (every physical specimen has
    # its own collection id even when of the same coin type) — see §9a.
    # `sieg` is also added: between Hede 1971's printing and modern Sieg-
    # Møntkatalog editions, numbering has shifted (e.g. Hede prints
    # Sieg-112 while modern catalogues use Sieg-96 for the same coin
    # type — see schema.CatalogRefs.sieg_hede1971 docstring). The
    # disagreement is a printing-edition artefact, not a coin-type
    # identity signal — the «what coin is this» question is answered
    # by Hede / Galster / KM / Dav (parent type-level refs), and Sieg
    # follows whichever edition each source happened to cite.
    SUB_VARIANT_REFS = {
        "schou", "nmd", "aagaard", "schive", "skjoldager",
        "bruun_collection_id", "sieg",
    }

    def _numeric_core(v: str) -> str:
        """Strip trailing alphabetic sub-variant suffix («8226A» →
        «8226»). Catalogue convention: a single letter (occasionally
        two) appended to a base catalogue number marks a die-variant
        or sub-type of the same parent. Tolerated as same when the
        broader catalogue chain confirms identity."""
        m = re.match(r"^(\d+(?:\.\d+)?)[A-Za-z]{1,2}$", v.strip())
        return m.group(1) if m else v.strip()

    def _parent_of_dotnum(v: str) -> str | None:
        """Return parent of a dot-numeric sub-variant («70.1» → «70»),
        or None if the value isn't dot-numeric. Used for bare-vs-sub
        catalog-ref tolerance: when ucoin/Numista publish bare «KM-70»
        and Hede/NumisMaster publish specific «KM-70.1», they refer to
        the same Krause-Mishler parent type and should merge.

        Asymmetric: ONLY when one side is bare and the other is
        dot-form is this loosening applied — two distinct dot-form
        sub-variants («70.1» and «70.2») remain different so curator
        sub-variant distinctions stay intact. Same applies to KM «1.1»
        ↔ «1» (parent type) but NOT KM «1.1» ↔ «1.2»."""
        m = re.match(r"^(\d+)\.\d+$", v.strip())
        return m.group(1) if m else None

    agreeing: list[str] = []
    disagreeing: list[str] = []
    for k in shared:
        va, vb = refs_a[k], refs_b[k]
        # Lange-specific value comparison (comma lists + numeric ranges) —
        # see `_lange_numbers`. Bypasses the generic «|»-split path for this
        # register only; other registers fall through unchanged.
        if k.split("/", 1)[0] == "lange":
            if _lange_numbers(va) & _lange_numbers(vb):
                agreeing.append(k)
            else:
                disagreeing.append(k)
            continue
        sa = set(va.split("|"))
        sb = set(vb.split("|"))
        # Case-insensitive value match (§9.4 index normalisation, user
        # direction 2026-06-08): «55C» ≡ «55c». Compare lower-cased sets
        # so a pure case-variant counts as agreement, not disagreement.
        if {x.lower() for x in sa} & {x.lower() for x in sb}:
            agreeing.append(k)
            continue
        # Loosened match: compare numeric cores (8226A ≡ 8226). Applied
        # only when both sides have non-empty numeric cores; cross-
        # variant identity is the catalogue-convention reading.
        cores_a = {_numeric_core(v) for v in sa}
        cores_b = {_numeric_core(v) for v in sb}
        if cores_a & cores_b:
            agreeing.append(k)
            continue
        # Bare-vs-dot-numeric tolerance («70» ≡ «70.1»). Asymmetric: one
        # side must be bare (no dot-form), the other side's dot-num
        # parent must equal the bare side. Two distinct dot-forms
        # («70.1» ≢ «70.2») stay disagreeing so curator sub-variant
        # splits stay intact.
        parents_a = {p for p in (_parent_of_dotnum(v) for v in sa) if p}
        parents_b = {p for p in (_parent_of_dotnum(v) for v in sb) if p}
        # bare-a meets dot-b: cores_a (which equals sa for bare values)
        # intersects with parents_b
        if (cores_a & parents_b) or (cores_b & parents_a):
            agreeing.append(k)
        else:
            disagreeing.append(k)
    if not disagreeing:
        return ("agree", True)
    # Tolerance: at least ONE type-level (non-sub-variant) ref agrees
    # AND every disagreement is a sub-variant field → still agree.
    # Type-level agreement (Hede, Galster, KM, Dav, Davenport, Fr,
    # Lange) establishes coin-type identity; sub-variant disagreements
    # (Schou, Sieg, NMD, Aagaard, Schive, Skjoldager, bruun_collection_
    # id) are die-variants / specimens / catalogue-edition splits.
    # Concrete cases:
    #   - Hede agrees + Schou differs → same coin (Schou = die-variants)
    #   - Hede agrees + Sieg differs → same coin (Sieg-1971 vs modern)
    #   - Galster agrees + Schou + bruun_coll_id differ → same coin
    #     (multi-specimen merge per §9a)
    # Scope-aware sub-variant test: scoped keys («schou/christian iv»,
    # «hede/frederik iii», «galster/c4g») carry a «base/scope» shape.
    # Strip the scope so the membership test matches the bare catalogue
    # name in SUB_VARIANT_REFS. Without this, ruler-scoped `schou` keys
    # would be mis-classified as type-level (they contain «/») and the
    # «Hede agrees + Schou differs → same coin» tolerance would break.
    def _base(k):
        return k.split("/", 1)[0]
    # Numista N# is a SOFT type-level ref: Numista routinely mints a SEPARATE
    # N# for each sub-letter variant of ONE strong-catalogue type (Hede 32A →
    # N#444851, 32B → N#444852; Hede 11A/11C → two N#). When a STRONG parent
    # catalogue (Hede / KM / Galster / Dav / Fr / Lange — one number per coin
    # TYPE within scope) AGREES, a Numista N# disagreement is a sub-variant
    # split, not different-type evidence → tolerate it (the two N# accumulate
    # into the merged entry's list-form `numista` per §9a). When numista is the
    # ONLY shared type-level ref (no strong parent agrees), it stays a HARD
    # discriminator: two distinct N# with nothing else shared are different
    # types. (2026-06-09 — verified the 7 flagged pairs are Numista typology in
    # the harvested data, not a project split.)
    _STRONG_PARENT_CATALOGUES = {
        "hede", "km", "galster", "dav", "davenport", "fr", "friedberg", "lange",
    }
    strong_parent_agrees = any(
        _base(k) in _STRONG_PARENT_CATALOGUES for k in agreeing
    )
    tolerable_disagree = set(SUB_VARIANT_REFS)
    if strong_parent_agrees:
        tolerable_disagree.add("numista")
    non_subvariant_agree = [
        k for k in agreeing if _base(k) not in SUB_VARIANT_REFS
    ]
    blocking_disagree = [
        k for k in disagreeing if _base(k) not in tolerable_disagree
    ]
    if (len(non_subvariant_agree) >= 1
            and not blocking_disagree):
        return ("agree", True)
    return ("disagree", True)


def _year_first(coin):
    return coin.get("year_first")


def _year_last(coin):
    return coin.get("year_last") or coin.get("year_first")


def _years_overlap(a, b):
    af, al = _year_first(a), _year_last(a)
    bf, bl = _year_first(b), _year_last(b)
    if af is None or bf is None:
        return None
    return max(af, bf) <= min(al, bl)


def _fineness_repr(coin) -> float | None:
    f = coin.get("fineness")
    if isinstance(f, (int, float)):
        return float(f)
    if isinstance(f, list):
        vals = [
            e.get("value") for e in f
            if isinstance(e, dict) and isinstance(e.get("value"), (int, float))
        ]
        if vals:
            return sum(vals) / len(vals)
    return None


def _fineness_within(a, b, tol=0.05):
    fa = _fineness_repr(a)
    fb = _fineness_repr(b)
    if fa is None or fb is None:
        return None
    return abs(fa - fb) <= tol


# ---------------------------------------------------------------------------
# Weight tier-1 disambiguator (user-confirmed 2026-05-22)
# ---------------------------------------------------------------------------
#
# Per user direction, weight + fineness form the primary identity vector
# for sub-variant disambiguation. When BOTH coins carry weight_rough_g
# AND the relative gap exceeds the tolerance (default 5%), the matcher
# returns no_match REGARDLESS of catalog-letter agreement.
#
# Rationale — encoded numismatic intuition.
# -----------------------------------------
# Cataloguers regularly cite the same Galster sub-letter (e.g. «92B»)
# for specimens whose physical weight clearly differs beyond expected
# variance. Example: chr_c3g92.htm publishes Galster 92B at 12.12g; the
# Bruun catalogue lot 13057 attests a specimen at 11.05g — both labelled
# «Galster 92B», but with auxiliary catalog refs that diverge (Sieg 4
# vs 16, Schou 48,50 vs 48 alone) and weights ~8.8% apart.
#
# In this regime the physical-specimen identity is the relevant atomic
# unit; cataloguer's sub-letter is an approximation across multiple
# physical specimens. We surface this by keeping the two records as
# distinct unified entries; a curator can later decide whether to fold
# them via §9a multi-specimen merge AFTER additional verification.
#
# Specimen-variance considerations.
# ---------------------------------
# Standard Reichsthaler / well-defined types: ±1-2% specimen variance is
# typical (≤5% covers extremes). Emergency Klippinge / Notmünze:
# variance can reach ±10-15%, but the >5% gap then ALSO usually has
# divergent sub-cataloguing (Sieg numbers, mintmark variants) — which is
# exactly what we want to surface as separate entries. The 5% threshold
# is conservative for cross-source merge; within-source §9a multi-
# specimen merge (where catalog identity is established by the source
# cataloguer themselves) is unaffected.


def _weight_repr(coin) -> float | None:
    """Single representative weight from `weight_rough_g`. Mirrors
    `_fineness_repr` shape: scalar OR list-of-FieldValue."""
    w = coin.get("weight_rough_g")
    if isinstance(w, (int, float)):
        return float(w)
    if isinstance(w, list):
        vals = [
            e.get("value") for e in w
            if isinstance(e, dict) and isinstance(e.get("value"), (int, float))
        ]
        if vals:
            return sum(vals) / len(vals)
    return None


def _weight_diverges(a, b, tol_rel: float = 0.05) -> bool | None:
    """Tier-1 weight disambiguator.

    Returns:
      True  — both sides have weight AND relative Δ > tol_rel → BLOCK merge.
      False — both sides have weight AND relative Δ ≤ tol_rel → ok.
      None  — at least one side lacks weight → not evaluable, no decision.

    Relative tolerance is computed against the average of the two
    readings to avoid asymmetry. Default 5% covers normal specimen
    variance; gaps beyond it signal a likely different physical type.
    """
    wa = _weight_repr(a)
    wb = _weight_repr(b)
    if wa is None or wb is None:
        return None
    if wa <= 0 or wb <= 0:
        return None
    avg = (wa + wb) / 2
    rel = abs(wa - wb) / avg
    return rel > tol_rel


def _shares_unique_id_ref(refs_a: dict, refs_b: dict) -> bool:
    """True iff the two ref dicts share an AGREEING globally-unique
    identity ref — a Numista N# or a Bruun collection-id.

    These two refs are identity-proof: a Numista N# names exactly one
    catalogue type empire-wide; a Bruun collection-id names exactly one
    physical specimen. A shared+agreeing value on either is conclusive
    same-coin evidence that does NOT collide cross-reign / cross-register
    (unlike a bare km, which can be reused across reigns — e.g. KM#461 on
    both a Christian V and a Frederik IV «2 Ducats» around 1699).

    Used to NARROWLY gate the ruler-string-divergence override in
    `match_pair`: ruler is demoted to advisory only on a shared unique-ID
    ref, never on a bare km/hede-volume collision. See the §dup-audit T1
    note (2026-05-30) at the ruler block.
    """
    GLOBALLY_UNIQUE = {"numista", "bruun_collection_id"}
    for k in (GLOBALLY_UNIQUE & set(refs_a) & set(refs_b)):
        va, vb = refs_a[k], refs_b[k]
        sa = set(va.split("|")) if isinstance(va, str) else {str(va)}
        sb = set(vb.split("|")) if isinstance(vb, str) else {str(vb)}
        if sa & sb:
            return True
    return False


def _catalog_strongly_agrees(refs_a: dict, refs_b: dict,
                              min_shared_agreeing: int = 2) -> bool:
    """Strong catalog-agreement test for the weight tier-1 disambiguator.

    Returns True iff:
      (a) refs share ≥ `min_shared_agreeing` keys AND
      (b) every shared key's values overlap (no disagreement on any
          shared key) — strict equality WITHOUT numeric-core normalisation.

    Used to gate weight tier-1 disambiguation:
      - SAME physical type, different preservation (e.g. two specimens
        of KM 19 / Hede 56A with weights 28.8g vs 24.5g due to wear):
        ≥2 type+sub-variant refs agree → True → weight guard does NOT
        fire → merge allowed (per §9a multi-specimen merge).
      - DIFFERENT physical types loosely cataloguing as same parent
        (e.g. Bruun's 8 Skilling 2.72g cited «Galster 93» vs Galster's
        own reference at 3.32g — only galster=93 in common): only 1
        shared ref → False → weight guard fires → no_match.
      - Same parent letter but auxiliary refs disagree (e.g. 92B Galster
        sieg=4 vs 92B Bruun sieg=16): galster agrees + sieg disagrees
        → False (disagreement detected) → weight guard fires.

    Why a strict-equality + min-shared count:
      Per user direction 2026-05-22, when weight diverges > 5% the
      identity of the physical type must be more strongly evidenced
      than a single catalog letter agreement. Wear-only divergence
      typically appears in catalogues that cite ALL the standard refs
      (KM + Hede + Sieg + Schou); cross-source same-letter coincidence
      typically lacks that depth. The min-2 threshold separates these
      two cases cleanly.

    Numeric-core normalisation («92B» ≡ «92») from
    `_catalog_chain_consistent` is INTENTIONALLY NOT applied here —
    Galster letter-suffix is meaningful at the sub-variant level
    («Galster 92» base ≠ «Galster 92B» sub-variant).
    """
    shared = set(refs_a) & set(refs_b)
    # Type-defining authoritative catalogs — one number per coin type
    # within their scope. A single shared+agreeing ref from this set is
    # strong-enough evidence by itself (used to relax min_shared_agreeing
    # for sources that publish only one catalog ref). The check still
    # requires zero disagreements across ALL shared keys.
    #
    # SCOPE-CRITICAL: only keys that are GLOBALLY UNIQUE or already scoped
    # qualify. Per CLAUDE.md §9.4 «catalogue numbers restart within each
    # country / register»:
    #   - bare `km` is AMBIGUOUS (Denmark KM 75 ≠ SH KM 75) — must NOT
    #     count as authoritative on its own. Only the SCOPED form
    #     `km/<register>` (km/dk, km/sh, km/no, etc.) qualifies.
    #   - bare `numista` IS safe — Numista N#s are globally unique.
    #   - bare `bruun_collection_id` IS safe — Bruun catalogue's own
    #     single-source numbering.
    #   - galster/<vol> and hede/<vol> already scoped per ruler-volume.
    #
    # If a coin's catalog has bare `km` (entity without register mapping
    # in `_ENTITY_TO_KM_REGISTER`), it stays bare — and intentionally
    # falls back to the classic ≥2-shared-refs requirement.
    AUTHORITATIVE_TYPE_DEFINING = {
        "numista", "bruun_collection_id",
    }
    has_authoritative_agreement = False
    n_agreeing = 0
    for k in shared:
        va, vb = refs_a[k], refs_b[k]
        sa = set(va.split("|")) if isinstance(va, str) else {str(va)}
        sb = set(vb.split("|")) if isinstance(vb, str) else {str(vb)}
        if sa & sb:
            n_agreeing += 1
            if (k in AUTHORITATIVE_TYPE_DEFINING
                    or k.startswith("km/")
                    or k.startswith("galster/")
                    or k.startswith("hede/")):
                has_authoritative_agreement = True
        else:
            # Any disagreement on a shared key disqualifies — strong
            # agreement requires zero disagreements across shared keys.
            return False
    # Two paths to «strongly agrees»:
    #   (a) classic: ≥ min_shared_agreeing refs in agreement, OR
    #   (b) single-source carry: ≥1 authoritative type-defining ref
    #       (KM / Numista / Bruun-coll-id / galster/vol / hede/vol).
    #       Use this when a source publishes only one catalog ref
    #       (Galster-derived seeds typically have just galster/vol;
    #        Numista pages often carry just N# + a Friedberg cross-ref).
    return n_agreeing >= min_shared_agreeing or has_authoritative_agreement


# Mint spelling aliases — map source-specific variants to a single
# project-canonical lowercased form so cross-source mint comparison
# doesn't false-fail on language / orthography. Each entry: source
# spelling (lowercase) → canonical spelling (lowercase).
#
# Discovered 2026-05-19 during D40 H-case categorisation: 27 of 33
# residual pending entries were «Copenhagen» (NumisMaster English) vs
# «Kopenhagen» (project-canonical Danish/German). 1 case was
# «Rendsborg» (Danish) vs «Rendsburg» (project-canonical German for SH
# towns). Pure normaliser gap, not actual mint divergence.
#
# When extending: keep map-keys lowercase. Match is applied after
# `lower()` + paren-suffix stripping in `_normalise_mints`. Add
# variants ONLY when they refer to the SAME historical mint town —
# never collapse functionally-distinct mints into one canonical form.
_MINT_SPELLING_ALIASES = {
    # Copenhagen — English / historical Danish / Latin → project canonical
    # (German-Danish «Kopenhagen» is the convention per CLAUDE.md §2 / §i18n
    # «mint names use standard academic spellings, identical across languages»;
    # the «Kopenhagen» form is what V1 foundation entries carry).
    "copenhagen": "kopenhagen",
    "københavn": "kopenhagen",
    "kjøbenhavn": "kopenhagen",       # historical Danish (pre-1948 spelling)
    "hafnia": "kopenhagen",            # Latin (Christian IV / Frederik III legends)
    # Rendsburg — Danish vs German for the Schleswig-Holstein town.
    # Project convention: German spelling for SH mints (consistent with
    # other SH towns like Flensburg, Eckernförde, Husum).
    "rendsborg": "rendsburg",
    # Haderslev (DK) ↔ Hadersleben (DE) — same town in Sønderjylland.
    # Carve-out from the «German for SH mints» convention per user
    # direction 2026-05-22 — collapse to the Danish form (matching
    # Hede 1971 + the town's post-1920 official name + majority of
    # our existing data). German-source variants like Numista's
    # «Hadersleben» fold to «Haderslev» at merge time.
    "hadersleben": "haderslev",
    # Helsingør — English «Elsinore» variant
    "elsinore": "helsingør",
    "elseneur": "helsingør",           # French (rare, appears in old auction catalogues)
}


# Country / region prefix tokens that ucoin and similar sources
# sometimes prepend to mint strings — e.g. ucoin's «Denmark, Copenhagen»,
# «Norway, Christiania», «Sweden, Stockholm». These prefixes carry no
# information beyond what the issuing_entity already encodes; stripping
# them lets the city token reach the alias map.
_MINT_COUNTRY_PREFIXES = frozenset({
    "denmark", "norway", "sweden", "germany", "holstein", "schleswig",
    "schleswig-holstein", "lübeck", "hamburg",
})


def _normalise_mints(mint) -> set[str]:
    if mint is None:
        return set()
    mints = mint if isinstance(mint, list) else [mint]
    out = set()
    for m in mints:
        if not isinstance(m, str):
            continue
        # Strip trailing paren tail «Altona (FK VS)» → «Altona», then
        # split on comma so multi-token shapes like «Denmark, Copenhagen»
        # or «Altona, Kopenhagen» (V1 list-style joined into a string)
        # decompose into individual mint tokens.
        # Also strip trailing « Mint» suffix common in Bruun catalogue
        # output («Copenhagen Mint», «Glückstadt Mint», «Altona Mint»)
        # so Bruun mint tokens align with project-canonical bare-mint form.
        base = re.sub(r"\s*\([^)]*\)\s*$", "", m).strip()
        base = re.sub(r"\s+Mint\s*$", "", base).strip()
        if not base:
            continue
        tokens = [t.strip().lower() for t in base.split(",") if t.strip()]
        for t in tokens:
            # Skip pure country-prefix tokens (they're scope qualifiers,
            # not mint towns). Keeps the city token for comparison.
            if t in _MINT_COUNTRY_PREFIXES:
                continue
            # Apply spelling-alias canonicalisation so cross-source
            # comparison doesn't false-fail on English/Danish/German
            # variants of the same mint town.
            canonical = _MINT_SPELLING_ALIASES.get(t, t)
            out.add(canonical)
    return out


def _mints_overlap(a, b):
    ma = _normalise_mints(a.get("mint"))
    mb = _normalise_mints(b.get("mint"))
    if not (ma and mb):
        return None
    if ma & mb:
        return True
    # No overlap — check whether either side's mint is curator-attested
    # (`mint_verified: True`). An UNVERIFIED mint is a V1-bootstrap
    # fallback (typically «Kopenhagen» as default for Danish coins) or
    # a parser guess — it cannot DISPROVE a merge against a verified
    # authority like Hede 1971's page header. When one side is verified
    # and the other isn't, return None (unknown) instead of False.
    #
    # When BOTH sides are unverified, the mint signal is fully advisory;
    # also return None to let other signals drive the decision.
    av = bool(a.get("mint_verified"))
    bv = bool(b.get("mint_verified"))
    if av != bv or (not av and not bv):
        return None
    # Both verified, no overlap — real divergence
    return False


# Type-level catalogues: one number == one numismatic TYPE within scope
# (KM register, Hede reign, Galster volume, the global Dav/Fr/Lange/mb/Numista/
# Bruun-collection ids). A shared+agreeing ref here ties two records as the
# SAME type (so a verified mint disagreement between them is a mint-VARIANT,
# not a different coin). The collision-prone sub-variant refs Schou/Sieg/NMD/
# Aagaard/Schive/Skaare are EXCLUDED — a shared Schou number alone does not
# establish type identity (§9.4: Schou restarts per reign and collides across
# minting contexts, e.g. Wolfenbüttel war coinage «Sch 5» vs København
# Speciedaler Schou 5).
_TYPE_LEVEL_CATALOGUES = frozenset({
    "km", "hede", "galster", "dav", "fr", "lange", "davenport",
    "friedberg", "mb", "numista", "bruun_collection_id",
})


def _type_level_numeric_core(v: str) -> str:
    """«8226A» → «8226»: strip a trailing 1-2 letter sub-variant suffix.
    Module-level twin of the nested helper in `_catalog_chain_consistent`."""
    m = re.match(r"^(\d+(?:\.\d+)?)[a-z]{1,2}$", v.strip())
    return m.group(1) if m else v.strip()


def _shares_type_level_catalog(refs_a: dict, refs_b: dict) -> bool:
    """True iff refs_a and refs_b share an AGREEING type-level catalogue ref
    (scope-aware: «km/dk», «hede/christian iv» strip to «km», «hede»). Uses
    case-insensitive + numeric-core («55A»≡«55») value tolerance, matching
    `_catalog_chain_consistent`."""
    for k in (set(refs_a) & set(refs_b)):
        if k.split("/", 1)[0] not in _TYPE_LEVEL_CATALOGUES:
            continue
        va = {x.strip().lower() for x in str(refs_a[k]).split("|")}
        vb = {x.strip().lower() for x in str(refs_b[k]).split("|")}
        if va & vb:
            return True
        ca = {_type_level_numeric_core(x) for x in va}
        cb = {_type_level_numeric_core(x) for x in vb}
        if ca & cb:
            return True
        # Bare-vs-dot-parent tolerance («579» ≡ «579.1»), matching
        # `_catalog_chain_consistent` — KM sub-variants of one parent type
        # are the SAME type for the mint-discriminator's purposes.
        pa = {m.group(1) for x in va if (m := re.match(r"^(\d+)\.\d+$", x))}
        pb = {m.group(1) for x in vb if (m := re.match(r"^(\d+)\.\d+$", x))}
        if (ca & pb) or (cb & pa):
            return True
    return False


# ---------------------------------------------------------------------------
# Match algorithm
# ---------------------------------------------------------------------------


def match_pair(coin_a: dict, coin_b: dict, entity_id: str | None = None,
               reign_index: dict[int, set[str]] | None = None) -> dict:
    """Apply §5.2 hierarchy. Returns:
        {'decision': 'confident' | 'low_confidence' | 'no_match',
         'primary': {metal, nominal, catalog, ruler},
         'fallback': {years, fineness, mint},
         'why': [str, ...]}
    Primary booleans: True (match), False (mismatch), None (cannot evaluate).

    `entity_id` is used to scope bare-form catalog refs (KM register
    inference per `_ENTITY_TO_KM_REGISTER`) — both coins are assumed
    to belong to the same entity (matcher is per-entity).

    `reign_index` (D33) is an optional `{year → set(rulers)}` map for
    THIS entity, built from members that DO have an attested ruler.
    When either coin's `ruler` is null, the matcher falls back to
    looking up its year(s) in the index — but ONLY adopts the inferred
    value when the union of rulers across every covered year is
    exactly one (transition / co-regent years leave the ruler null per
    user direction). The inference is reported in `why` as
    «ruler inferred: <name> (year(s) X)» so a curator audit can trace
    the chain.
    """
    primary = {}
    fallback = {}
    why = []

    # Weight tier-1 disambiguator (user-confirmed 2026-05-22, refined
    # same day to be catalog-strength-aware).
    #
    # The naïve rule «block merge when weight Δ > 5%» is too aggressive:
    # same-type specimens with different preservation states (wear,
    # corrosion, slight planchet variance) legitimately differ by 5-10%
    # in weight even when cataloguers unanimously assign the same
    # KM/Hede/Sieg/Schou/Galster. Per §9a these merge into ONE entry
    # with a multi-source `weight_rough_g` list.
    #
    # The refined rule combines TWO signals:
    #   1. weight Δ > 5% relative AND
    #   2. catalog does NOT strongly agree (i.e. fewer than 2 shared
    #      catalog refs ALL in agreement, strict equality without
    #      numeric-core / sub-variant tolerance)
    #
    # Both must hold to block merge. Otherwise the merge proceeds
    # through the standard primary-signal path.
    #
    # Worked examples (1535 Galster cluster):
    #   - 92B Galster (12.12g) vs 92B Bruun (11.05g): Δ ≈ 9%; shared
    #     {galster, schou, sieg} but sieg=4 vs sieg=16 disagree → not
    #     strongly-agreeing → no_match ✓
    #   - 93 Galster (3.32g) vs 93 Bruun (2.72g): Δ ≈ 20%; only
    #     {galster=93} shared → 1 ref < 2 threshold → no_match ✓
    #   - Wear-only KM 19 specimens 28.8 vs 24.5g: Δ ≈ 16%; shared
    #     {km=19, hede=56A} both agree → strongly-agreeing → merge ✓
    refs_a_pre = _catalog_refs(coin_a, entity_id)
    refs_b_pre = _catalog_refs(coin_b, entity_id)
    if (_weight_diverges(coin_a, coin_b, tol_rel=0.05) is True
            and not _catalog_strongly_agrees(refs_a_pre, refs_b_pre,
                                              min_shared_agreeing=2)):
        wa = _weight_repr(coin_a)
        wb = _weight_repr(coin_b)
        why.append(
            f"weight: {wa:.3f}g vs {wb:.3f}g — Δ > 5% "
            f"AND catalog not strongly-agreeing (<2 shared refs match) — "
            f"tier-1 disambiguator"
        )
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why}

    # Metal — verified-wins rule (CLAUDE.md §4, extended 2026-05-19
    # operational consequence #1: a `metal_verified: false` value
    # cannot DISPROVE a merge). Without this rule, a builder-inferred
    # billon guess on a Tn-token blocks the merge with a source-attested
    # copper reading from NumisMaster.
    ma = _normalise_metal(coin_a.get("metal"), coin_a.get("fineness"))
    mb = _normalise_metal(coin_b.get("metal"), coin_b.get("fineness"))
    a_metal_verified = bool(coin_a.get("metal_verified"))
    b_metal_verified = bool(coin_b.get("metal_verified"))
    if ma and mb:
        if ma == mb:
            primary["metal"] = True
        elif a_metal_verified and b_metal_verified:
            # Both sides attest a metal — genuine disagreement, no merge
            primary["metal"] = False
            why.append(f"metal: {ma} ≠ {mb} (both attested)")
            return {"decision": "no_match", "primary": primary,
                    "fallback": fallback, "why": why}
        else:
            # At least one side is unverified (builder-inferred guess).
            # Don't let an unverified value disprove a verified one.
            primary["metal"] = None
            why.append(
                f"metal: {ma}({'✓' if a_metal_verified else '?'}) vs "
                f"{mb}({'✓' if b_metal_verified else '?'}) — unverified "
                "side ignored per §4"
            )
    else:
        primary["metal"] = None

    # Nominal — bookkeeping only. Per CLAUDE.md §9.4 «catalog index is
    # THE discriminating signal»; nominal is a descriptive label that
    # varies between sources (e.g. NumisMaster's «4 Speciedaler» vs
    # Hede's «4 Daler» for the same Christian IV 1604 KM-25 Klippe).
    # We compute the agreement state here but DON'T hard-fail when it
    # disagrees — instead let the catalog check below override.
    # Verdict made later: if catalog strongly agrees, accept the merge;
    # if catalog has no overlap, fall through to fallback-driven low-
    # confidence path.
    na = _normalise_nominal(coin_a.get("nominal"))
    nb = _normalise_nominal(coin_b.get("nominal"))
    if not na or not nb:
        primary["nominal"] = None
    elif na == nb:
        primary["nominal"] = True
    elif _nominal_wildcard_match(na, nb):
        # Bare ambiguous unit («daler»/«gylden») vs a specific compound of
        # the same unit + quantity — can't be a genuine difference.
        primary["nominal"] = None
    else:
        primary["nominal"] = False

    # Catalog chain (entity-aware scoping for bare KM + ruler-aware for Hede)
    refs_a = _catalog_refs(coin_a, entity_id)
    refs_b = _catalog_refs(coin_b, entity_id)
    chain_state, has_overlap = _catalog_chain_consistent(refs_a, refs_b)
    if chain_state == "disagree":
        why.append(f"catalog disagree: {refs_a} vs {refs_b}")
        primary["catalog"] = False
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why}
    if chain_state == "agree":
        primary["catalog"] = True
    else:
        # no_overlap: one or both sides lack catalog refs that intersect.
        # NOT a mismatch — can't be evaluated. Tri-state primary signal.
        primary["catalog"] = None

    # Nominal-mismatch handling (refined 2026-05-22 per user direction):
    # only HARD-fail nominal disagreement when catalog ALSO can't carry
    # the merge. When catalog STRONGLY agrees (shared KM / Hede ref),
    # nominal disagreement reflects cross-source cataloguing convention
    # — e.g. NumisMaster's «4 Speciedaler» vs Hede's «4 Daler» for the
    # 1604 Christian IV Gold-Klippinge KM-25 series. The catalog match
    # is the identity-evidence; nominal label difference is noise.
    #
    # When the override fires we DEMOTE primary["nominal"] from False
    # to None (advisory) so the confidence-calc below doesn't count it
    # as a primary-disagreement (which would re-trigger no_match via
    # the `if primary_false` short-circuit on line ~1275).
    if primary["nominal"] is False:
        # FORGERY GUARD (2026-06-09) — runs BEFORE the catalogue-tie demotion.
        # A contemporary forgery / imitation is a different physical object
        # from the genuine coin it copies, yet it is catalogued BY what it
        # imitates (so it shares the genuine coin's Hede/KM). When exactly one
        # side is forgery-marked, that shared catalogue must NOT demote the
        # nominal mismatch — block the merge HARD so the forgery stays its own
        # record (e.g. «1 Skilling samtidig forfalskning» (billon) vs the
        # genuine Hede 119B 1 Skilling).
        if (_is_forgery_nominal(coin_a.get("nominal"))
                != _is_forgery_nominal(coin_b.get("nominal"))):
            why.append(
                f"forgery≠genuine: {coin_a.get('nominal')!r} vs "
                f"{coin_b.get('nominal')!r} — shared catalogue does NOT merge "
                f"a forgery into the type it imitates"
            )
            return {"decision": "no_match", "primary": primary,
                    "fallback": fallback, "why": why}
        # Nominal discriminator (shipped 2026-06-08 after the synonym table
        # was expanded to fold the false-split label-variance categories).
        # The normalised nominals GENUINELY differ (synonym folds + the
        # daler/gylden wildcard above already excluded label-only variance).
        # The catalogue decides whether that's two distinct coins or one
        # type catalogued differently across sources:
        #   • A TYPE-LEVEL catalogue tie (shared KM / Hede / Galster / Dav /
        #     Fr / Lange / N#, NOT a weak per-reign Schou/Sieg) carries the
        #     type identity → DEMOTE the nominal-mismatch to advisory (§9.4),
        #     e.g. NumisMaster's «4 Speciedaler» vs Hede's «4 Daler» (KM-25).
        #   • Only a weak Schou/Sieg tie, or no catalogue overlap → the
        #     nominals are real different-denomination evidence and nothing
        #     ties them → BLOCK the merge.
        if _shares_type_level_catalog(refs_a, refs_b):
            why.append(
                f"nominal: {coin_a.get('nominal')!r} ≠ {coin_b.get('nominal')!r} "
                f"— demoted to advisory via type-level catalogue agreement (§9.4)"
            )
            primary["nominal"] = None  # don't count as primary_false
        else:
            why.append(
                f"nominal: {coin_a.get('nominal')!r} ≠ {coin_b.get('nominal')!r} "
                f"(genuinely different) AND no type-level catalogue tie "
                f"(only Schou/Sieg or none) — different coin (§9.4 nominal discriminator)"
            )
            return {"decision": "no_match", "primary": primary,
                    "fallback": fallback, "why": why}

    # Ruler — direct values first; reign-index inference (D33) when null.
    ra = _normalise_ruler(coin_a.get("ruler"))
    rb = _normalise_ruler(coin_b.get("ruler"))
    if reign_index:
        if not ra:
            inferred_a = _infer_ruler(coin_a, reign_index)
            if inferred_a:
                ra = inferred_a
                why.append(f"ruler_a inferred: {inferred_a!r} from year(s) {sorted(_coin_years(coin_a))}")
        if not rb:
            inferred_b = _infer_ruler(coin_b, reign_index)
            if inferred_b:
                rb = inferred_b
                why.append(f"ruler_b inferred: {inferred_b!r} from year(s) {sorted(_coin_years(coin_b))}")
    if ra and rb:
        if ra == rb:
            primary["ruler"] = True
        else:
            # Honour `ruler_verified` like mint_verified does (CLAUDE.md
            # §4 + V2_DECISIONS §«Ruler verified-wins extension»): a
            # source whose ruler attribution failed the reign-window
            # check (e.g. ucoin tagging 1807 with Frederik VI) carries
            # `ruler_verified: False` and MUST NOT disprove a merge
            # against a verified attestation. When one side is
            # ruler_verified=True and the other is False, return None
            # so other signals drive the decision. When BOTH sides are
            # unverified, also defer (the conflict is between two
            # guesses). Only when BOTH are verified AND values differ
            # do we treat ruler as a genuine primary disagreement.
            a_rv = bool(coin_a.get("ruler_verified", True))
            b_rv = bool(coin_b.get("ruler_verified", True))
            if a_rv and b_rv:
                # Globally-unique-ID override (NARROW — §dup-audit T1
                # 2026-05-30). A ruler-string divergence is demoted to
                # advisory ONLY when the two coins share an agreeing
                # GLOBALLY-UNIQUE identity ref — a Numista N# or a Bruun
                # collection-id. Those are identity-proof: a Numista N# is
                # one catalogue type empire-wide, a Bruun coll-id is one
                # physical specimen. When they agree, a ruler-string
                # difference is cross-source naming / language convention
                # (Numista's English «Christian Albert» vs German
                # «Christian Albrecht von Gottorp» on the coin both cite
                # as N#301216) — not different-ruler evidence.
                #
                # The gate is deliberately NARROWER than
                # `_catalog_strongly_agrees`: it does NOT accept a shared
                # bare km / hede-volume ref, which can collide cross-reign
                # (KM#461 cited on both a Christian V and a Frederik IV
                # «2 Ducats» around 1699). A shared Numista N# / Bruun
                # coll-id never collides cross-reign, so it is safe.
                # (Cross-reign coins that legitimately share a Bruun
                # specimen / N# — same physical coin catalogued under two
                # reign-volumes — DO merge; the hede_volume scalar-handling
                # in _deep_merge_catalog keeps the output well-formed.)
                if _shares_unique_id_ref(refs_a, refs_b):
                    primary["ruler"] = None
                    why.append(
                        f"ruler: {ra!r} ≠ {rb!r} — demoted to advisory via "
                        f"shared globally-unique ID ref (numista N# / "
                        f"bruun coll-id) — identity-proof"
                    )
                else:
                    primary["ruler"] = False
                    why.append(f"ruler: {ra!r} ≠ {rb!r}")
            else:
                primary["ruler"] = None
                why.append(
                    f"ruler-disagreement-suppressed: {ra!r}(verified={a_rv}) "
                    f"vs {rb!r}(verified={b_rv})"
                )
    else:
        primary["ruler"] = None

    # Fallback signals
    fallback["years"] = _years_overlap(coin_a, coin_b)
    fallback["fineness"] = _fineness_within(coin_a, coin_b)
    fallback["mint"] = _mints_overlap(coin_a, coin_b)

    # Verified-mint divergence disqualifier (§9.4, user direction 2026-06-08).
    # `_mints_overlap` returns False ONLY when both sides have a VERIFIED,
    # disjoint mint (per §4 an unverified guess can't disprove). That is a
    # different-coin signal UNLESS a strong TYPE-level catalogue ref ties the
    # two as a mint-VARIANT of one type. Without that tie, block — otherwise
    # the §9a multi-specimen tolerance below would let a bare-Schou collision
    # carry the merge. Catches Christian-IV's 1627 Wolfenbüttel war coinage
    # (mint Wolfenbüttel verified) false-merging into the København Hede 55
    # (mint Kopenhagen verified) via a colliding Schou number.
    if fallback["mint"] is False and not _shares_type_level_catalog(
            refs_a, refs_b):
        why.append(
            f"mint: {coin_a.get('mint')!r} ≠ {coin_b.get('mint')!r} (both "
            "verified, disjoint) AND no strong type-level catalogue tie "
            "(only Schou/Sieg or none) — different coin (§9.4 mint discriminator)"
        )
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why}

    # Confidence calc
    primary_true = sum(1 for v in primary.values() if v is True)
    primary_unknown = sum(1 for v in primary.values() if v is None)
    primary_false = sum(1 for v in primary.values() if v is False)

    fallback_true = sum(1 for v in fallback.values() if v is True)
    fallback_false = sum(1 for v in fallback.values() if v is False)

    if primary_false:
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why or ["primary signal disagreed"]}

    # §9a multi-specimen rule (catalog-driven multi-year/multi-mint tolerance).
    #
    # Two seeds attesting the SAME physical type minted across multiple years
    # (each Bruun specimen has its OWN year_first=year_last for the year it
    # was struck) inevitably disagree on `years` fallback even when catalog
    # evidence is overwhelming (KM + Hede + Sieg + Schou agree). Mint
    # orthographic variation registers as `mint` fallback False before
    # normalisation. Bruun specimens of the same type also disagree on
    # bruun_collection_id (per-specimen) and Schou (per-die-variant).
    #
    # Gate: catalog has TYPE-LEVEL strong agreement — ≥2 non-sub-variant refs
    # agree OR ≥1 shared authoritative type-defining ref (km/<reg>, hede/<vol>,
    # galster/<vol>, numista) agrees — AND no non-sub-variant disagreements.
    # Sub-variant disagreements (Schou, Sieg, bruun_collection_id, NMD,
    # Aagaard, Schive, Skjoldager) are tolerated as expected for §9a.
    #
    # Additional safety: ruler + metal primaries also True. Cross-edition KM
    # drift on different physical coins under the same ruler + metal would
    # be the main false-merge risk, but it's vanishingly rare within a
    # single per-entity bucket.
    AUTHORITATIVE_TYPE_DEFINING_REFS = {"numista", "bruun_collection_id"}
    SUB_VARIANT_REFS_FOR_MULTISPECIMEN = {
        "schou", "nmd", "aagaard", "schive", "skjoldager",
        "bruun_collection_id", "sieg",
    }

    def _has_type_strong_agreement(ra: dict, rb: dict) -> bool:
        shared = set(ra) & set(rb)
        if not shared:
            return False
        non_subvariant_agree = 0
        has_authoritative = False
        for k in shared:
            va, vb = ra[k], rb[k]
            sa = set(va.split("|")) if isinstance(va, str) else {str(va)}
            sb = set(vb.split("|")) if isinstance(vb, str) else {str(vb)}
            overlap = bool(sa & sb)
            # Scope-aware: «schou/christian iv» → base «schou» so the
            # ruler-scoped Schou key still reads as a sub-variant ref.
            is_subvar = k.split("/", 1)[0] in SUB_VARIANT_REFS_FOR_MULTISPECIMEN
            if not overlap and not is_subvar:
                # Non-sub-variant disagreement disqualifies
                return False
            if overlap and not is_subvar:
                non_subvariant_agree += 1
                if (k.startswith("km/")
                        or k.startswith("hede/")
                        or k.startswith("galster/")
                        or k == "galster"
                        or k in AUTHORITATIVE_TYPE_DEFINING_REFS):
                    # `galster` is a TYPE-level catalogue (Galster N = one
                    # numismatic type, like KM/Hede) — but `_catalog_refs`
                    # scopes it as the bare key «galster» (no «/vol» suffix),
                    # so the `galster/` prefix check never matched it. That
                    # left same-Galster specimens from different mints (e.g.
                    # Galster 24 Hans Nobel struck at Malmø AND København)
                    # blocked by the mint-fallback disagreement. Ruler must
                    # still agree (§9a gate), which prevents cross-volume
                    # Galster-number collisions.
                    has_authoritative = True
        return non_subvariant_agree >= 2 or has_authoritative

    if (fallback_false > 0
            and primary.get("catalog") is True
            and primary.get("ruler") is True
            and primary.get("metal") is True
            and _has_type_strong_agreement(refs_a, refs_b)):
        why.append(
            f"§9a multi-specimen promotion: catalog type-strong + ruler + "
            f"metal True; fallback disagreement tolerated ({fallback})"
        )
        return {"decision": "confident", "primary": primary,
                "fallback": fallback, "why": why}

    # All available primary signals agree (no False); some may be None
    # (not evaluable — e.g. catalog no_overlap when refs come from
    # different cataloguing systems, or metal not stated). Decision:
    #
    #   CONFIDENT  — primary_true ≥ 3 AND fallback_true ≥ 1 AND no fallback_false
    #   LOW_CONF   — primary_true == 4 AND fallback_false > 0
    #                (catalog/ruler/nominal/metal all match but specimen
    #                 weight or year disagrees — curator inspect)
    #   LOW_CONF   — primary_true ≥ 2 AND fallback_true ≥ 1 AND no fallback_false
    #   NO_MATCH   — everything else
    if primary_true == 4 and fallback_false > 0:
        why.append(f"all 4 primary match but fallback disagrees: {fallback}")
        return {"decision": "low_confidence", "primary": primary,
                "fallback": fallback, "why": why}

    if fallback_false > 0:
        why.append(f"fallback disagrees ({fallback}), primary_true={primary_true}")
        return {"decision": "no_match", "primary": primary,
                "fallback": fallback, "why": why}

    if primary_true >= 3 and fallback_true >= 1:
        return {"decision": "confident", "primary": primary,
                "fallback": fallback, "why": [f"primary_true={primary_true}/4, fallback_true={fallback_true}"]}

    if primary_true >= 2 and fallback_true >= 1:
        why.append(f"primary_true={primary_true} (<3) — review")
        return {"decision": "low_confidence", "primary": primary,
                "fallback": fallback, "why": why}

    return {"decision": "no_match", "primary": primary,
            "fallback": fallback, "why": why or [f"insufficient signals (primary_true={primary_true}, fallback_true={fallback_true})"]}


# ---------------------------------------------------------------------------
# Union-Find with explicit no-merge support
# ---------------------------------------------------------------------------


class UnionFind:
    """Union-Find with explicit no-merge that respects TRANSITIVITY:
    when A↔B and A↔C are confident merges but B↔C is no_match, the
    transitive union {A, B, C} would silently override B↔C's no_match.
    To prevent this, union(x, y) checks every cross-class member pair
    for a registered no_merge constraint; if any pair conflicts, the
    union is refused.

    This means processing order matters: register all no_merges FIRST
    (matcher pass for no_match decisions), then process confident
    unions. A confident union that violates a no_merge stays separate
    + surfaces in match_uncertainty via the unmerged pair.
    """

    def __init__(self):
        self.parent: dict[str, str] = {}
        self.no_merge: set[frozenset] = set()
        # Curator-declared no_merges (merge_decisions::no_merges). These are
        # NEVER auto-cleared — a curator-forced merge that conflicts with one
        # is refused (genuine curator contradiction → caller warns). Auto
        # no_merges (matcher no_match opinions) live only in `no_merge` and
        # ARE cleared by `force_union` since a curator merge outranks a
        # heuristic no_match.
        self.explicit_no_merge: set[frozenset] = set()

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def can_union(self, x, y) -> bool:
        return frozenset({x, y}) not in self.no_merge

    def _class_members(self, root: str) -> list[str]:
        return [k for k in self.parent if self.find(k) == root]

    def union(self, x, y) -> tuple[bool, frozenset | None]:
        """Returns (succeeded, conflicting_pair_or_None).
        On no_merge violation, returns (False, frozenset({a, b}))
        so caller can log which pair blocked the transitive union."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return (False, None)
        # Direct pair check
        if not self.can_union(x, y):
            return (False, frozenset({x, y}))
        # Cross-class check: any member of rx's class has a no_merge
        # with any member of ry's class?
        if self.no_merge:
            members_x = self._class_members(rx)
            members_y = self._class_members(ry)
            for mx in members_x:
                for my in members_y:
                    if frozenset({mx, my}) in self.no_merge:
                        return (False, frozenset({mx, my}))
        # Stable root choice: lexicographically smaller wins
        if rx < ry:
            self.parent[ry] = rx
        else:
            self.parent[rx] = ry
        return (True, None)

    def add_no_merge(self, x, y, explicit: bool = False):
        fs = frozenset({x, y})
        self.no_merge.add(fs)
        if explicit:
            self.explicit_no_merge.add(fs)
        # Touch both ids so they appear as singleton classes if not
        # subsequently merged with anything else.
        self.find(x)
        self.find(y)

    def force_union(self, x, y) -> tuple[bool, frozenset | None]:
        """Curator-forced union (merge_decisions::merges). Clears AUTO
        no_merges between the two classes — a curator merge outranks any
        heuristic matcher no_match — but REFUSES if an EXPLICIT curator
        no_merge conflicts (a genuine curator contradiction). Returns
        (succeeded, conflicting_explicit_pair_or_None). Apply AFTER the
        confident-merge pass so both classes are fully formed and every
        cross-class auto no_merge gets cleared."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return (True, None)
        members_x = self._class_members(rx)
        members_y = self._class_members(ry)
        # Refuse on explicit curator no_merge conflict.
        for mx in members_x:
            for my in members_y:
                if frozenset({mx, my}) in self.explicit_no_merge:
                    return (False, frozenset({mx, my}))
        # Clear AUTO no_merges between the two classes (heuristic opinions
        # overridden by the curator merge).
        for mx in members_x:
            for my in members_y:
                self.no_merge.discard(frozenset({mx, my}))
        if rx < ry:
            self.parent[ry] = rx
        else:
            self.parent[rx] = ry
        return (True, None)

    def classes(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for k in self.parent:
            groups[self.find(k)].append(k)
        return dict(groups)


# ---------------------------------------------------------------------------
# Unified entry construction
# ---------------------------------------------------------------------------


def _collect_field_list(members: list[dict], field: str,
                          skip_first_list: bool = False) -> list[dict]:
    """For weight_rough_g / fineness / diameter_mm — collect ALL readings
    from every member as multi-source list entries. Dedupe by (value, source)
    so re-runs are deterministic.

    `skip_first_list`: when True, the FIRST member's list-form values
    are IGNORED (its scalar value still counts). Used by absorb when
    the first member is the foundation (final entry) and its list-form
    is absorb-cached output from a prior run. The fresh re-derivation
    should rebuild from composed_of members' attestations rather than
    propagating cached values. Concrete case: `unified-dk-numista-474583`
    foundation had cached list [14.38 galster, 36.31 numista] from a
    previous merger output that merged Numista + Galster c3g-103.
    After the Galster ruler-scope fix split them, seed_unified now
    has only 36.31 from Numista. Without `skip_first_list`, the
    foundation's cached 14.38 (Galster) survives re-enrichment as a
    phantom reading.
    """
    seen: set[tuple] = set()
    out: list[dict] = []
    for idx, m in enumerate(members):
        val = m.get(field)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            # A non-positive measurement (0.0 / negative) is a source
            # placeholder for «not recorded», not a real reading — drop it
            # (schema requires value > 0; common in IKMK/KMM specimens whose
            # weight field is blank → harvested as 0.0).
            if val <= 0:
                continue
            # bare-number form — synthesise source from member id
            entry = {"value": float(val), "source": _source_label_from_id(m.get("id"))}
            key = (entry["value"], entry["source"])
            if key not in seen:
                seen.add(key)
                out.append(entry)
        elif isinstance(val, list):
            # When the caller marks the first member as foundation
            # (absorb's existing final entry), skip its cached list-
            # form values. Its scalar reading (if any) still counts;
            # the list is purely the previous-absorb output and may
            # contain stale entries (now-removed composed_of sources).
            if idx == 0 and skip_first_list:
                continue
            for item in val:
                if not isinstance(item, dict):
                    continue
                v = item.get("value")
                if not isinstance(v, (int, float)):
                    continue
                if v <= 0:  # non-positive = source «not recorded» placeholder
                    continue
                raw_src = item.get("source", "?")
                # Detect & fix stale synthesised labels from a prior buggy
                # split — when the source string matches a dash-segment
                # of ANY member's id (e.g. `'26'` from `km-26-fr-karl-
                # plon-1760` via the old `split('-')[1]` fallback), re-
                # synthesise from the matching member's id so the
                # user-facing tooltip shows the correct source name.
                if (isinstance(raw_src, str)
                        and raw_src
                        and " " not in raw_src
                        and len(raw_src) <= 8):
                    # Look across all members for an id whose segments
                    # contain this stale label. Prefer the first match.
                    for cand in members:
                        cid = cand.get("id")
                        if cid and raw_src in str(cid).split("-"):
                            correct = _source_label_from_id(cid)
                            if correct and correct != "?":
                                raw_src = correct
                                break
                entry = {"value": float(v), "source": raw_src}
                key = (entry["value"], entry["source"])
                if key not in seen:
                    seen.add(key)
                    out.append(entry)
    # Drop stale numeric / dash-segment source labels (e.g. '15', '156',
    # 'dk') unconditionally — these are residue from historical absorb
    # runs where the now-fixed `_source_label_from_id` returned the
    # wrong split segment of curator V1 ids (`km-N-ruler-year`,
    # `dk-tid-N`, etc.). The actual measurement readings carry their
    # correct source (`hede`, `numismaster`, `ucoin`, `bruun`, etc.)
    # via the fresh re-derivation pass above. A stale numeric-only
    # source label refers to no real source — it is a leftover that
    # would otherwise show as a meaningless number in the rendered
    # tooltip.
    import re as _re
    _stale_src = _re.compile(r"^[a-z]?\d+[a-z]?$|^dk$|^sh$|^lu$|^hb$|^en$|^de$|^uk$")
    cleaned: list[dict] = []
    for e in out:
        s = e.get("source", "")
        if isinstance(s, str) and _stale_src.match(s):
            continue  # unconditional drop of synthesised-from-bad-split labels
        cleaned.append(e)
    # Collapse same-value entries whose source labels are nested
    # variants of one another. Pattern: same `value`, sources
    # `[X, X tid N]` or `[X, X N# N]` — both refer to the same external
    # citation (the more-specific form annotates which entry on X). Keep
    # only the MORE SPECIFIC label (drop the bare prefix). Real
    # multi-source attestations (Hede + Bruun + ucoin) keep all
    # distinct labels.
    by_value: dict[float, list[dict]] = {}
    for e in cleaned:
        by_value.setdefault(e["value"], []).append(e)
    nested_pruned: list[dict] = []
    for val, entries in by_value.items():
        if len(entries) > 1:
            srcs = [e.get("source", "") for e in entries
                    if isinstance(e.get("source"), str)]
            # If any source is a prefix of another (e.g. «ucoin» of
            # «ucoin tid 97375»), the prefix is redundant — drop it.
            to_drop_idx: set[int] = set()
            for i, src_i in enumerate(srcs):
                for j, src_j in enumerate(srcs):
                    if i == j or not src_i or not src_j:
                        continue
                    # src_i is a prefix of src_j with a space boundary
                    if (len(src_i) < len(src_j)
                            and src_j.startswith(src_i + " ")):
                        to_drop_idx.add(i)
            for k, e in enumerate(entries):
                if k not in to_drop_idx:
                    nested_pruned.append(e)
        else:
            nested_pruned.extend(entries)
    # Deterministic order: by value, then source
    nested_pruned.sort(key=lambda e: (e["value"], e["source"]))
    return nested_pruned


def _source_label_from_id(coin_id: str | None) -> str:
    if not coin_id:
        return "?"
    # Strip the `unified-` wrapper that the cross-source merger prefixes
    # to its output ids — the underlying source signature lives in the
    # post-prefix part.
    if coin_id.startswith("unified-"):
        coin_id = coin_id[len("unified-"):]
    if coin_id.startswith("dk-hede-") or coin_id.startswith("hede-"):
        return "hede"
    if coin_id.startswith("dk-bruun-") or coin_id.startswith("bruun-"):
        return "bruun"
    if coin_id.startswith("dk-numismaster-"):
        return "numismaster"
    if coin_id.startswith("dk-numista-"):
        return "numista"
    if coin_id.startswith("dk-galster-") or coin_id.startswith("galster-"):
        return "galster"
    # KMM (Den kgl. Mønt- og Medaillesamling / Nationalmuseet) specimen ids
    # `kmk-NNNNN`. Without this branch the generic split returned the numeric
    # object-id segment («156725»), which the stale-source regex
    # (`^[a-z]?\d+[a-z]?$`) then PURGED — silently dropping every KMM-sourced
    # weight/diameter reading from the multi-source list (e.g. the 17.4 g of
    # the Frederik I Ribe Nobel kmk-156725). Label as «kmk» so the reading
    # survives + the tooltip shows a real source.
    if coin_id.startswith("kmk-"):
        return "kmk"
    # IKMK Berlin specimen ids `ikmk-NNNNN`. Same trap as kmk: the generic
    # split returned the numeric object-id («18203389»), purged by the
    # stale-source regex → every IKMK weight/diameter reading silently dropped
    # from multi-source lists (4000+ entries). Label as «ikmk».
    if coin_id.startswith("ikmk-"):
        return "ikmk"
    # ucoin V1 ids also appear as `tid-tid-NNNN` (the bare `tid` query-param
    # prefix doubled). Same source as dk-/sh-/hb-/lu-tid → label «ucoin», not
    # the literal «tid» the generic split would yield.
    if coin_id.startswith("tid-tid-") or coin_id.startswith("tid-"):
        return "ucoin"
    # ucoin V1 carryover ids — `dk-tid-`, `sh-tid-`, `hb-tid-`,
    # `lu-tid-`. The «tid» token is the URL query-param name from
    # ucoin (`?tid=NNNN`); the actual SOURCE is ucoin.net, so label
    # as such for human-readable provenance tooltips.
    if (coin_id.startswith("dk-tid-")
            or coin_id.startswith("sh-tid-")
            or coin_id.startswith("hb-tid-")
            or coin_id.startswith("lu-tid-")):
        return "ucoin"
    # ucoin V1 curator-named ids — `km-N-ruler-YYYY` / `km-xNNN-ruler-YYYY`
    # / `km-NNN-YYYY` / `bruun-NNNNN-ruler-mint-YYYY` / `lange-NNN-ruler-
    # mint-YYYY` and similar V1 curator hand-shaped ids that end with a
    # 4-digit year. Per `build_ucoin_seed.py` §«Preserve V1's custom id»,
    # curator-named entries (no `tid` query-param assigned) carry this
    # shape. The V1-foundation entries came through V1 curator imports
    # where ucoin was the primary source — label them so the
    # weight/fineness multi-source list shows «ucoin» rather than the
    # numeric KM/Bruun/Lange catalog index segment.
    if (coin_id.startswith("km-")
            or coin_id.startswith("bruun-")
            or coin_id.startswith("lange-")) and coin_id.count("-") >= 2:
        # End-of-id year check — pattern `…-YYYY` with 4-digit year
        last = coin_id.rsplit("-", 1)[-1]
        if last.isdigit() and len(last) == 4:
            return "ucoin"
        # km-N-ruler-… without trailing year — still ucoin V1 carryover
        if coin_id.startswith("km-") and coin_id.count("-") >= 3:
            return "ucoin"
    # NumisMaster-prefixed entity IDs from the location-aware builder
    # (e.g. `schleswig_holstein-numismaster-X`).
    if "-numismaster-" in coin_id:
        return "numismaster"
    if "-numista-" in coin_id:
        return "numista"
    # Generic fallback. SAFETY NET (the ikmk/kmk-class trap): when the second
    # segment is a bare numeric object-id (`<source>-<NNNNN>`), the SOURCE is
    # the FIRST segment, not the number — returning the number would be purged
    # by the stale-source regex, silently dropping that source's measurement
    # readings. So fall back to the source prefix for any future `src-NNNNN`
    # shape rather than the numeric id.
    parts = coin_id.split("-")
    if len(parts) >= 2:
        return parts[0] if parts[1].isdigit() else parts[1]
    return "?"


def _collect_sources(members: list[dict],
                       skip_first_list: bool = False) -> list[dict]:
    """Union members' source lists with smart de-duplication.

    Two regimes by URL shape:

    * **Single-page sources** (each URL == one cited record): URL is
      the primary identity; multiple entries with the same URL but
      different `ref` / `type` labels are RE-LABELS of the same
      citation, NOT distinct references. Dedupe by URL alone, keep
      the first occurrence. Covers `danskmoent.dk/*.htm`,
      `en.numista.com/<id>`, `en.ucoin.net/coin/.../?tid=<n>`,
      `numismaster.com/MC_<n>`, `numista.com/`, IKMK `ikmk.smb.museum/`.
    * **Multi-record sources** (one URL hosts many citations, with
      `ref` carrying the per-citation discriminator — page / lot / etc.):
      dedupe by (URL, ref, type) — keep distinct refs even when URL
      collides. Covers Bruun PDFs (Stack's Bowers catalogues — one
      PDF, hundreds of lots), institutional library PDFs.

    `skip_first_list`: when True, the FIRST member's sources list is
    ignored. Used by absorb when the first member is the foundation
    (final entry) and its sources list is absorb-cached output from a
    prior run — may contain phantom citations from composed_of sources
    that have since been split off (e.g. Galster c3g-103 ref left in
    Numista 474583's sources after the Galster ruler-scope split). Re-
    derive from composed_of unified members only.

    Triggers for the «single-page» regime: known host substrings.
    Anything else falls through to the strict (url, ref, type) key.
    """
    _SINGLE_PAGE_HOSTS = (
        "danskmoent.dk",
        "en.numista.com",
        "en.ucoin.net",
        "numismaster.com",
        "ikmk.smb.museum",
    )
    seen_keys: set[tuple] = set()
    out: list[dict] = []
    for idx, m in enumerate(members):
        if idx == 0 and skip_first_list:
            continue
        for s in m.get("sources") or []:
            if not isinstance(s, dict):
                continue
            url = s.get("url") or ""
            ref = s.get("ref") or ""
            stype = s.get("type") or ""
            # A .pdf URL is ALWAYS a multi-record source (one catalogue PDF
            # hosts hundreds of lots, the per-lot discriminator living in
            # `ref`), regardless of host. This guard must precede the
            # single-page-host check. The Bruun catalogue PDFs are hosted
            # per-part on DIFFERENT origins: Parts I/III/IV on stacksbowers.com
            # (never a _SINGLE_PAGE_HOST, so already triple-keyed and correct),
            # but Part II on danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII…pdf —
            # whose "danskmoent.dk" host substring mis-classified it as
            # single-page, collapsing every Part-II lot to ONE citation under
            # url-only dedup. (Caught 2026-06-02: a 2-Speciedaler type lost
            # "Bruun Part II, lot 14032" because "lot 14013" of the same PtII
            # PDF was seen first.) The .pdf guard fixes Part II and is
            # host-agnostic, so a future danskmoent mirror of any other part
            # is covered too.
            if url.lower().endswith(".pdf"):
                key = ("trip", url, ref, stype)
            elif any(host in url for host in _SINGLE_PAGE_HOSTS):
                key = ("url", url)
            else:
                key = ("trip", url, ref, stype)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            out.append(s)
    return out


def _collect_mints(members: list[dict]) -> str | list[str] | None:
    """Collect mint(s) from unified members per verified-wins precedence.

    Per CLAUDE.md §4 «verified-wins-over-unverified» principle applied
    to mint specifically (user-confirmed 2026-05-19): a `mint_verified:
    False` value is a curator GUESS (typically V1 bootstrap default
    «Kopenhagen» for Danish coins, or a parser heuristic). It cannot
    OVERRIDE a `mint_verified: True` authoritative attestation, and
    when no verified attestation exists, the lower-authority guess
    must yield to the higher-authority source's mint.

    Precedence:
      Tier 1: ANY member has `mint_verified: True`
              → use ONLY those members' mints (drop unverified guesses)
      Tier 2: All members unverified
              → use only the HIGHEST-_authority_score source's mints
              (e.g. Hede outranks ucoin even when neither flips the
              verified flag; the ucoin curator's «Kopenhagen» default
              is dropped in favour of Hede's parser-extracted mint)
      Tier 3: All members at authority score 0
              → fall back to UNION of all mints (legitimate joint-mint
              coins like Altona+Kopenhagen where both attest the same
              physical issue)
    """
    # Tier 1: verified mints, when any exist (with non-empty mint)
    source_members = [m for m in members
                      if bool(m.get("mint_verified")) and m.get("mint") is not None]
    if not source_members:
        # Tier 2: keep only the highest-authority members WITH a mint.
        # Members lacking a mint contribute no information at this tier —
        # filtering them out lets lower-authority members with attested
        # mints (e.g. Galster authority=1 with mint=['Kopenhagen','Malmö'])
        # carry the result when higher-authority members lack mint
        # (e.g. Numista authority=2 with mint=None).
        with_mint = [(m, _authority_score(m.get("id", ""))) for m in members
                     if m.get("mint") is not None]
        max_score = max((s for _, s in with_mint), default=0)
        if max_score > 0:
            source_members = [m for m, s in with_mint if s == max_score]
        elif with_mint:
            # Tier 3: all with-mint members at score 0 — keep them all
            source_members = [m for m, _ in with_mint]
        else:
            # Nothing has a mint
            source_members = []
    raw_mints: list[str] = []
    for m in source_members:
        mint = m.get("mint")
        if mint is None:
            continue
        for mt in (mint if isinstance(mint, list) else [mint]):
            if isinstance(mt, str):
                raw_mints.append(mt)
    # Canonicalise spelling + de-dup + certain-wins across the WHOLE union
    # (Kopenhagen ≡ København ≡ K�benhavn ≡ Kbh. → «Kopenhagen»; «Altona;
    # Copenhagen» split; «X?» dropped when certain «X» also attested). One
    # call so the certain-wins pass sees every member's mints together,
    # instead of «[Kopenhagen, K�benhavn]» / «[Kopenhagen, Kopenhagen?]».
    return _canonicalise_mint(raw_mints)


class MetalConflictError(Exception):
    """Raised when merged members carry >=2 distinct `metal_verified: True`
    metals that are NOT one of the thin-line alloy pairs — a real divergence
    the curator must resolve, not have the merger silently pick one. Shipped
    2026-06-20 after a KMM museum «soelv» (metal_verified:True) silently beat
    Hede «copper» (metal_verified:True) on unified-dk-hede-f6h17."""


# Thin-line alloy pairs: a verified-vs-verified disagreement WITHIN one of
# these is NOT a real conflict — it's the same metal under a looser-vs-tighter
# label, so warn (pick by authority) instead of aborting. Each pair is checked
# as a self-contained set: a conflict spanning two pairs (e.g. silver/copper)
# is NOT in any single pair → still raises.
#   {silver, billon}  — low-grade billon vs silver (user-set 2026-06-20)
#   {bronze, copper}  — bronze IS a copper alloy (~95% Cu); museums tag a
#                       bronze coin «kobber»/copper. The numismatic catalogue
#                       (Hede/Numista/NumisMaster) carries the precise «bronze»;
#                       authority resolves it (user-set 2026-06-22, c9h18b).
_THIN_LINE_METAL_PAIRS = ({"silver", "billon"}, {"bronze", "copper"})


def _collect_metal(members: list[dict]) -> str | None:
    """Pick metal across unified members per verified-wins precedence.

    Per CLAUDE.md §4 «verified-wins-over-unverified» applied to metal:
    a `metal_verified: False` value is typically a builder inference
    (ucoin builder maps Müntzfuß → metal, NumisMaster builder maps
    composition → metal). When two builders disagree on metal AND only
    one side is `metal_verified: True`, the verified side wins.

    Precedence (mirrors `_collect_mints`):
      Tier 1: ANY member has `metal_verified: True`
              → use the highest-_authority_score member among those.
              Ties broken in REVERSE insertion order — i.e. members
              appended LAST win when authority tied, because absorb's
              members list is [fc, *composed_of_unified]: the
              composed_of unified entries are FRESHER cross-source
              merge results, while fc is the (potentially stale)
              foundation. When fc and a composed_of member tie on
              authority but disagree on metal, the fresh unified
              attestation should win.
      Tier 2: All members unverified
              → fall back to first non-None metal among the highest-
              authority-scored members
      Tier 3: No metal anywhere → None
    """
    # Tier 1: verified attestations. Sort key: (-authority, -insertion_index)
    # so high-authority wins; ties broken by later insertion (fresher).
    indexed = list(enumerate(members))
    verified = [(idx, m) for idx, m in indexed
                if bool(m.get("metal_verified")) and m.get("metal")]
    if verified:
        # Verified-vs-verified metal-conflict guard (2026-06-20). Two sources
        # both `metal_verified: True` but disagreeing on metal is a genuine
        # divergence the curator must resolve — silently picking by authority
        # once shipped a wrong metal (KMM museum «soelv» beat Hede «copper» on
        # unified-dk-hede-f6h17). EXCEPTION: the thin-line alloy pairs
        # (silver<->billon, bronze<->copper) are NOT real conflicts — same metal
        # under looser-vs-tighter labels — so warn and let authority pick. Any
        # other disagreement (copper/silver, gold/silver, …) raises so the run
        # stops and the curator reviews + decides the metal.
        verified_metals = {m.get("metal") for _, m in verified}
        if len(verified_metals) >= 2:
            host = members[0].get("id") if members else "?"
            detail = ", ".join(f"{m.get('metal')}={m.get('id')}"
                               for _, m in verified)
            thin = next((p for p in _THIN_LINE_METAL_PAIRS
                         if verified_metals <= p), None)
            if thin is not None:
                label = "<->".join(sorted(thin))
                print(f"  ⚠ metal-conflict {label} (thin line — picking "
                      f"by authority) on {host}: {detail}", file=sys.stderr)
            else:
                raise MetalConflictError(
                    f"verified-vs-verified metal conflict on {host}: {detail}. "
                    f"Two sources both metal_verified:True disagree on metal "
                    f"(not a thin-line alloy pair). The merger must NOT silently "
                    f"pick one — resolve the wrong source's metal (curator value "
                    f"/ _source_errata) and re-run.")
        verified_sorted = sorted(
            verified,
            key=lambda im: (-_authority_score(im[1].get("id", "")), -im[0]))
        return verified_sorted[0][1].get("metal")
    # Tier 2: highest-authority unverified, fresher when tied
    sorted_members = sorted(
        indexed,
        key=lambda im: (-_authority_score(im[1].get("id", "")), -im[0]))
    for _, m in sorted_members:
        v = m.get("metal")
        if v:
            return v
    return None


def _merge_km_field(members: list[dict], entity_id: str | None) -> tuple[
    str | dict | None, list[tuple[str, str, str]]
]:
    """Merge `catalog.km` across members into MAXIMAL representation:
    every distinct register-value pair is preserved. Handles bare-form
    + dict-form mixture across sources without losing cross-volume info.

    Example: hede.km = "75" (bare, danish_realm entity → infer dk),
             numismaster.km = {dk: "75", sh: "29"}
    Output:  km = {dk: "75", sh: "29"}   ← cross-volume sh="29" preserved
    (was being silently lost before this fix — see commit message).

    Returns (merged_km, conflicts). conflicts is a list of
    (scope_key, top_auth_value, conflicting_value) — items where two
    members disagreed on the same register's KM. Top-auth wins for the
    merged output; conflicts are surfaced for diagnostic logging.
    """
    # Accumulate DISTINCT values per register (authority order, top-auth
    # first) into a list — data-accumulation principle. Post the §9.4
    # over-merge fix the matcher never auto-merges different-base-KM coins,
    # so divergent same-register KM only reaches here via a curator
    # merge_decision (one Hede type Krause split across e.g. KM 14/15/20) or
    # a genuine multi-citation (two sources cite different KM for the SAME
    # coin). Either way ALL the numbers belong on the one coin → list-form,
    # never drop. (Pre-fix this kept one value/register + dropped the rest to
    # `conflicts`, losing KM 14/20 on a curator-merged Hede-156 type.)
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    by_register: dict[str, list[str]] = {}
    bare_values: list[str] = []
    conflicts: list[tuple[str, str, str]] = []

    def _add(bucket: list[str], val: str):
        if val and val not in bucket:
            bucket.append(val)

    for m in sorted_members:
        km = (m.get("catalog") or {}).get("km")
        if km is None:
            continue
        if isinstance(km, list):
            km_vals = km
        else:
            km_vals = [km]
        for kv in km_vals:
            if isinstance(kv, dict):
                for reg, val in kv.items():
                    # A register value may itself be a list (multi-KM in one
                    # register, e.g. {sh: ['651', '651.1']}). Iterate it —
                    # `str(val)` on the whole list would emit the str-repr
                    # «['651', '651.1']» (the form-#2 corruption). See
                    # docs/SOURCES.md §13.x / catalog_codes._flatten_str_repr_list.
                    for vv in (val if isinstance(val, list) else [val]):
                        _add(by_register.setdefault(reg.lower(), []), str(vv).strip())
                continue
            val_str = str(kv).strip()
            register = _ENTITY_TO_KM_REGISTER.get(entity_id or "")
            if register:
                _add(by_register.setdefault(register, []), val_str)
            else:
                _add(bare_values, val_str)

    def _shape(vals: list[str]):
        """1 value → scalar (V1-compat); ≥2 → list-form (multi-KM)."""
        return vals[0] if len(vals) == 1 else list(vals)

    # Output shape — preserve maximal info:
    #   - cross-volume (≥2 registers) → dict-form, each value scalar-or-list
    #   - single register → bare scalar (1) or bare list (≥2)
    #   - only bare-without-register input → scalar (1) or list (≥2)
    if by_register:
        if len(by_register) == 1:
            return _shape(next(iter(by_register.values()))), conflicts
        return {reg: _shape(vals) for reg, vals in by_register.items()}, conflicts
    if bare_values:
        return _shape(bare_values), conflicts
    return None, conflicts


def _deep_merge_catalog(members: list[dict], entity_id: str | None = None
                        ) -> tuple[dict, list]:
    """Catalog refs accumulated across members per CLAUDE.md
    «Data-accumulation principle». Special-cases KM via `_merge_km_field`
    (cross-volume preservation). For other refs that schema declares as
    `str | list[str]`, accumulates distinct values into list-form when
    members disagree — no silent data loss.

    Top-authority value comes FIRST in the list (preserves display
    preference); distinct lower-auth values append in authority order.

    Returns (merged_catalog, conflicts). `conflicts` only logs cases
    where two members disagreed on a STRICTLY single-value field (e.g.
    bruun_part Literal — can't list-form).
    """
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    out: dict = {}
    all_conflicts: list[tuple[str, str, str]] = []

    # KM — special-case cross-volume merge
    km, km_conflicts = _merge_km_field(members, entity_id)
    if km is not None:
        out["km"] = km
    all_conflicts.extend(km_conflicts)

    # Fields that schema lets us accumulate to list-form
    # (per CatalogRefs `str | list[str]` declaration). Distinct values
    # across members are PRESERVED.
    _LIST_FORM_FIELDS = {
        "hede", "sieg", "schou", "fr", "dav",
        "galster", "galster_volume", "jensen_skjoldager",
        "schive", "skaare", "friedberg", "davenport",
        "mb", "bruun_collection_id", "bruun_lot", "numista", "lange",
        "nmd", "fp",
    }
    # Fields that stay single-value (specimen-level or strict literal).
    # Conflict = log; top-auth wins for output.
    #
    # `hede_volume` is scalar-only in the schema (`str | None`) — it is
    # the per-ruler Hede volume code (c5h, f4h, …). A coin is catalogued
    # in ONE Hede volume; when two cross-source members disagree (e.g. a
    # 1699-transition coin that one source files under Christian V «c5h»
    # and another under Frederik IV «f4h» — same physical coin, divergent
    # reign-attribution), top-authority (foundation / curated) wins and
    # the divergence is logged as a conflict. It must NOT list-form —
    # that produced `hede_volume: ['c5h','f4h']` which violates the
    # schema (§dup-audit T-fix 2026-05-30). Unlike `galster_volume`
    # (`str | list[str]`, list-allowed), `hede_volume` is strictly scalar.
    _SINGLE_VALUE_FIELDS = {
        "bruun_part", "bruun_lot_no", "bruun_page",
        "sieg_hede1971", "schou_hede1971", "hede_volume",
    }
    # SPECIMEN-level single-value fields: a coin TYPE legitimately has many
    # Bruun specimens (different part/lot/page), so a disagreement here is
    # EXPECTED, not a real conflict — the anchor scalar keeps the top-
    # authority specimen and every other specimen's full citation lives in
    # `sources[]` + `bruun_collection_id` (§9a, verified 0 loss 2026-06-03).
    # §9a already excludes these from MATCHING; we likewise keep them OUT of
    # the conflict log so the audit surfaces only GENUINE single-value
    # disagreements (sieg_hede1971 / schou_hede1971 / hede_volume — e.g. the
    # KM-461 c5h-vs-f4h reign mix-up). Output (chosen anchor) is unchanged.
    _SPECIMEN_LEVEL_SINGLE_FIELDS = {
        "bruun_part", "bruun_lot_no", "bruun_page",
    }
    # `others` is already list-form; just union.

    # Defensive filter — drop cf-form values (user policy 2026-05-18):
    # «cf. X» references point at a similar OTHER coin, not at this entry's
    # own catalogue index, so they don't belong in catalog columns. Skip at
    # ingest time so future seeds carrying cf don't leak through.
    def _is_cf(value: str) -> bool:
        v = value.strip()
        if _SCALAR_CF_RE.match(v):
            return True
        if _OTHERS_CF_RE.match(v):
            return True
        return False

    # Collect distinct values per field across members
    per_field_values: dict[str, list[str]] = defaultdict(list)
    for m in sorted_members:
        cat = m.get("catalog") or {}
        for k, v in cat.items():
            if k == "km" or v is None:
                continue
            # Normalise to list of string values for comparison + accumulation
            if isinstance(v, list):
                value_list = [str(x).strip() for x in v if x is not None and str(x).strip()]
            else:
                value_list = [str(v).strip()] if str(v).strip() else []
            for val in value_list:
                if _is_cf(val):
                    continue
                if val not in per_field_values[k]:
                    per_field_values[k].append(val)

    # Emit per-field output
    for k, values in per_field_values.items():
        if not values:
            continue
        if k in _LIST_FORM_FIELDS:
            # str when single value (V1-compatible compact form);
            # list[str] when ≥2 distinct (data accumulation).
            out[k] = values[0] if len(values) == 1 else values
        elif k == "others":
            # `others: list[str]` — always list, union deduped
            out[k] = values
        elif k in _SINGLE_VALUE_FIELDS:
            # Single-value forced (schema constraint). Top-auth wins.
            out[k] = values[0]
            # Specimen-level bruun part/lot/page disagreements are expected
            # (multi-specimen) and lossless — don't log them as conflicts.
            if len(values) > 1 and k not in _SPECIMEN_LEVEL_SINGLE_FIELDS:
                for extra in values[1:]:
                    all_conflicts.append((f"catalog.{k}", values[0], extra))
        else:
            # Unknown field — defensive: keep first non-None
            out[k] = values[0]
            if len(values) > 1:
                for extra in values[1:]:
                    all_conflicts.append((f"catalog.{k}", values[0], extra))

    # `bruun_lot_no` is int in schema, `bruun_page` is int — re-cast when
    # values are numeric strings (pydantic would accept str→int coercion
    # but writing the YAML cleanly is nicer)
    for k in ("bruun_lot_no", "bruun_page"):
        if k in out and isinstance(out[k], str) and out[k].isdigit():
            out[k] = int(out[k])

    # Catalog-key synonym canonicalisation on OUTPUT (the same canonical
    # map used for matcher input in `_catalog_refs`). When per-source data
    # populates both forms (Bruun emits `friedberg`, Numista emits `fr`),
    # the merged output catalog ends up with both keys redundantly — the
    # rendered table shows «Fr#» from `fr` and «Friedberg#» from
    # `friedberg` as two separate columns even though they cite the same
    # catalogue. Fold synonyms to canonical at write time so the YAML
    # carries a single canonical key per catalogue.
    OUTPUT_CATALOG_KEY_SYNONYMS = {"friedberg": "fr", "davenport": "dav"}
    for syn, canonical in OUTPUT_CATALOG_KEY_SYNONYMS.items():
        if syn not in out:
            continue
        syn_val = out.pop(syn)
        canon_val = out.get(canonical)
        if canon_val is None:
            out[canonical] = syn_val
            continue
        # Both populated — union deduped, preserve list-form when ≥2 distinct
        merged_set = set()
        for v in (canon_val if isinstance(canon_val, list) else [canon_val]):
            if v is not None:
                merged_set.add(str(v).strip())
        for v in (syn_val if isinstance(syn_val, list) else [syn_val]):
            if v is not None:
                merged_set.add(str(v).strip())
        merged_list = sorted(merged_set)
        out[canonical] = merged_list[0] if len(merged_list) == 1 else merged_list

    return out, all_conflicts


def _take_first_non_none(members: list[dict], field: str):
    """Return the first non-None / non-empty value across members
    (already sorted top-authority first). Gap-fills from lower-authority
    sources when top-authority lacks the field — no data loss when
    upper has None and lower has a real value."""
    for m in members:
        v = m.get(field)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def _union_year_ranges(members: list[dict]) -> list[list[int]] | None:
    """Cross-source year-range merge with span-comparison displacement.

    Each member contributes `year_ranges` (list of `[lo, hi]` pairs) or
    falls back to `year_first` / `year_last`. A member's year_ranges
    is CLASSIFIED in one of two flavours:

      LOOSE     single non-singleton range `[[lo, hi]]` with lo < hi.
                Typical: Numista / ucoin's «1640-1646» date-range field
                published without per-year breakdown.
      DISCRETE  anything else — multiple entries, single singleton, or
                multiple singletons. A multi-year range INSIDE a
                multi-entry list (e.g. `[1618, 1619]` alongside other
                entries) is exploded into its full year set and counts
                as discrete attestation.

    Cross-source merge (user direction, 2026-05-23 + 2026-05-26 refinement):

      1. discrete_years = union of attested years from every DISCRETE
         member (each range `[lo, hi]` in such a member is exploded
         into years lo..hi inclusive).
      2. loose_ranges = (lo, hi) tuples from every LOOSE member.
      3. Span comparison: when discrete_years is non-empty, compute
         discrete_min = min(discrete_years), discrete_max = max(...).
         For each loose range (lo, hi):
            • If discrete_min ≤ lo AND discrete_max ≥ hi → discrete
              attestations span same-or-wider than the loose window
              → DROP the loose range. Discrete wins.
            • Otherwise (discrete narrower than loose) → KEEP loose.
              Final compression will absorb the discrete singletons
              into the loose envelope.
      4. Result = (discrete years as `[y, y]`) + surviving loose ranges,
         sorted and compressed (adjacent / overlapping ranges merge).

    Returns None when no member contributes any year info.

    Rationale: when discrete sources collectively span the SAME window
    a loose source describes, the loose source is by definition a
    less-precise version of the same claim and is supplanted by the
    granular form. When discrete sources span a NARROWER window than
    the loose source, the loose source carries information about years
    the discrete attestations don't reach (often a reign-window or a
    date-range field), so the loose envelope is retained.
    """
    def _collect(subset: list[dict]) -> tuple[set[int], list[tuple[int, int]]]:
        """Classify a member subset into discrete years + loose ranges."""
        discrete: set[int] = set()
        loose: list[tuple[int, int]] = []
        for m in subset:
            yr = m.get("year_ranges")
            source_pairs: list[tuple[int, int]] = []
            if isinstance(yr, list) and yr:
                for r in yr:
                    if isinstance(r, (list, tuple)) and len(r) == 2:
                        try:
                            a, b = int(r[0]), int(r[1])
                        except (TypeError, ValueError):
                            continue
                        if a > b:
                            a, b = b, a
                        source_pairs.append((a, b))
            else:
                yf, yl = m.get("year_first"), m.get("year_last")
                if isinstance(yf, int):
                    a = yf
                    b = int(yl) if isinstance(yl, int) else yf
                    if a > b:
                        a, b = b, a
                    source_pairs = [(a, b)]

            if not source_pairs:
                continue

            # Classify: LOOSE if a single non-singleton range AND nothing else;
            # DISCRETE otherwise (multi-entry list, single singleton, or multiple
            # singletons).
            is_loose = (
                len(source_pairs) == 1
                and source_pairs[0][0] < source_pairs[0][1]
            )
            if is_loose:
                loose.append(source_pairs[0])
            else:
                # Explode every range into its year set (singleton ranges
                # contribute just one year; multi-year ranges inside a
                # multi-entry list contribute every year between lo and hi).
                for lo, hi in source_pairs:
                    for y in range(lo, hi + 1):
                        discrete.add(y)
        return discrete, loose

    # Primary pass: NON-muted members only. A curator `year_demote`
    # (merge_decisions::year_demote) stamps `_year_demoted` on reign-window
    # placeholder members (a catalogue/museum record carrying the ruler's whole
    # reign rather than the coin's strike years) so their loose span never
    # widens the union. Last-resort fallback: muted members are consulted ONLY
    # when no non-muted member contributes any year — their years are demoted,
    # never deleted (§CU curator-mute; see docs/TODO.md).
    discrete_years, loose_ranges = _collect(
        [m for m in members if not m.get("_year_demoted")])
    if not discrete_years and not loose_ranges:
        discrete_years, loose_ranges = _collect(
            [m for m in members if m.get("_year_demoted")])

    if not discrete_years and not loose_ranges:
        return None

    # Step 3: drop loose ranges fully covered by the discrete span.
    surviving_loose: list[tuple[int, int]] = []
    if discrete_years:
        d_min = min(discrete_years)
        d_max = max(discrete_years)
        for lo, hi in loose_ranges:
            if d_min <= lo and d_max >= hi:
                continue  # discrete spans wider-or-equal → drop loose
            surviving_loose.append((lo, hi))
    else:
        surviving_loose = list(loose_ranges)

    # Step 4: assemble discrete singletons + surviving loose ranges,
    # then compress (sort + merge adjacent or overlapping).
    all_ranges: list[tuple[int, int]] = sorted(
        [(y, y) for y in discrete_years] + surviving_loose
    )
    merged: list[list[int]] = []
    for lo, hi in all_ranges:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return merged


def _format_year_label(year_ranges) -> str | None:
    """Render year_ranges as a compact `year_label` display string.

    Singletons render as bare year strings; multi-year ranges render
    with a hyphen; entries are joined with «, ». Returns None when
    the input is None or empty.

    Examples:
      [[1640, 1640]]                              → "1640"
      [[1640, 1646]]                              → "1640-1646"
      [[1640, 1640], [1642, 1642], [1646, 1646]]  → "1640, 1642, 1646"
      [[1611, 1611], [1613, 1614], [1618, 1620]]  → "1611, 1613-1614, 1618-1620"

    Always render from the cross-source MERGED year_ranges (after
    `_union_year_ranges` applied) rather than from any single source's
    published year_label — discrete attestations win over loose ranges
    when they span same-or-wider per the merge rule, and the label
    must reflect the merged truth, not the loose source's original
    «1640-1646» form.
    """
    if not year_ranges:
        return None
    parts: list[str] = []
    for pair in year_ranges:
        if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
            continue
        lo, hi = pair[0], pair[1]
        if lo == hi:
            parts.append(str(lo))
        else:
            parts.append(f"{lo}-{hi}")
    if not parts:
        return None
    return ", ".join(parts)


def _or_merge_verified(members: list[dict], field: str) -> bool | None:
    """OR-merge for verification flags: if ANY source attests (True),
    the unified entry is `True`. False otherwise (no source confirmed)."""
    seen_any_attestation = False
    seen_any_value = False
    for m in members:
        if field in m:
            seen_any_value = True
            if bool(m[field]):
                seen_any_attestation = True
                break
    if not seen_any_value:
        return None
    return seen_any_attestation


def build_unified(members: list[dict], unified_id: str,
                  entity_id: str | None = None
                  ) -> tuple[dict, list]:
    """Construct one unified entry from N member seed entries.

    Returns (unified_coin_dict, conflicts).
    `conflicts` lists scalar / catalog conflicts where members disagreed
    on a non-list field's value (top-auth wins for the output value but
    caller can log for visibility).

    Data-preservation rules per user direction («жодні дані не повинні
    бути перетерті, лише змерджені»):

      - Multi-source measurements (weight_rough_g, fineness, diameter_mm)
        → multi-source list with every reading preserved (`_collect_field_list`).
      - Sources → union, deduped by (url, ref, type).
      - Mint → union (list-form if multi-mint across members).
      - Catalog refs → max representation via `_deep_merge_catalog` —
        cross-volume KM preserved as dict-form, other refs gap-filled
        top-authority first.
      - Scalar text fields (nominal, ruler, year_label, year_first,
        year_last, year_ranges, mintmaster, fraction, kind, note,
        verification_note, inscription_obv, inscription_rev, metal):
        → `_take_first_non_none` walks members top-authority first;
        lower-authority's value fills gap when top-authority has None.
        On real conflict (both have non-None DIFFERENT values), top-auth
        wins; conflict logged.
      - Verification flags (metal_verified, fineness_verified,
        weight_rough_verified, diameter_mm_verified, mint_verified):
        → `_or_merge_verified` — any source attests → True. (A source's
        confirmation is never lost when its peer says False.)
    """
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    composed_of = sorted(set(m["id"] for m in members if m.get("id")))
    conflicts: list[tuple[str, str, str]] = []

    out: dict = {"id": unified_id}

    # Required schema fields (must have a value)
    out["fuss"] = _take_first_non_none(sorted_members, "fuss") or "seed_unsorted"
    out["phase"] = _take_first_non_none(sorted_members, "phase") or "unified"
    out["kind"] = _take_first_non_none(sorted_members, "kind") or "kurant"
    # `nominal` is schema-required. Some Galster pre-1541 seed entries
    # come with empty-string nominal (parser couldn't extract) — gap-fill
    # to '(?)' placeholder so schema validates; curator inspects pending
    # list and fills in real nominal via classification_decisions or by
    # fixing the parser.
    out["nominal"] = _take_first_non_none(sorted_members, "nominal") or "(?)"
    # `year_label` similar — synthesise from year_first/_last below if absent.

    # year_ranges + year_first/_last — UNION across members per
    # data-accumulation principle. The widest combined range envelope
    # drives year_first/_last; year_ranges keeps the de-overlapped
    # detail so per-year specimen markers in the timeline reflect every
    # source's recorded minting year.
    union_yr = _union_year_ranges(members)
    if union_yr is not None:
        if len(union_yr) == 1 and union_yr[0][0] == union_yr[0][1]:
            # Single-year — drop year_ranges (V1-compat: omit when trivial)
            out["year_first"] = union_yr[0][0]
            out["year_last"] = union_yr[0][1]
        else:
            out["year_first"] = min(r[0] for r in union_yr)
            out["year_last"] = max(r[1] for r in union_yr)
            out["year_ranges"] = union_yr
    # year_label — ALWAYS synthesise from the merged year_ranges, never
    # take from a source verbatim. When discrete attestations from one
    # source supersede a loose date-range from another (per
    # `_union_year_ranges` rules), the display label has to reflect the
    # merged truth «1611, 1613-1614, 1618-1620», not the loose
    # source's original «1611-1619» label.
    if union_yr is not None:
        out["year_label"] = _format_year_label(union_yr)

    # Propagate the year-demote flag when the WHOLE cluster is muted (a
    # reign-window source that is the sole member of its own unified entry,
    # e.g. dk-numista-355730 → unified-dk-numista-355730). The absorb-level
    # union then demotes this seed_unified entry too, so it can't widen the
    # final's year. `_`-prefixed → stripped before Coin validation, not
    # rendered. Mixed clusters are NOT flagged: their non-muted members already
    # carry the true years (§CU curator-mute).
    if members and all(m.get("_year_demoted") for m in members):
        out["_year_demoted"] = True

    # Other scalar text fields — gap-fill across members (log conflicts).
    # `ruler` uses _normalise_ruler equivalence to suppress pure-punctuation
    # variants («Frederik IV.» vs «Frederik IV») from the conflict log:
    # those are NOT real disagreements about who the ruler was, just
    # different spelling conventions across sources. The merger preserves
    # the top-authority spelling verbatim in `out[field]` — only the
    # conflict log is normalised.
    for field in ("fraction", "nominal", "ruler", "mintmaster",
                  "inscription_obv", "inscription_rev"):
        v = _take_first_non_none(sorted_members, field)
        if v is not None:
            out[field] = v
            # Log conflicts when ≥2 distinct values exist across members
            def _conflict_key(val):
                s = val if isinstance(val, str) else str(val)
                if field == "ruler":
                    return _normalise_ruler(s)
                return s
            seen: list[str] = [v if isinstance(v, str) else str(v)]
            seen_keys: set[str] = {_conflict_key(seen[0])}
            for m in sorted_members[1:]:
                mv = m.get(field)
                if mv is None:
                    continue
                mv_repr = mv if isinstance(mv, str) else str(mv)
                mv_key = _conflict_key(mv_repr)
                if mv_key not in seen_keys:
                    seen.append(mv_repr)
                    seen_keys.add(mv_key)
                    conflicts.append((field, seen[0], mv_repr))

    # Multi-mint union
    mint = _collect_mints(members)
    if mint is not None:
        out["mint"] = mint

    # Catalog deep-merge (entity-aware KM)
    cat, cat_conflicts = _deep_merge_catalog(members, entity_id)
    if cat:
        # §9.4 index hygiene on the assembled unified catalog: fold any
        # `others: <code># N` overflow into its typed list-field (case-
        # insensitive code) + case-insensitive value de-dup. Keeps the
        # seed_unified layer clean so the matcher AND the absorb both see
        # normalised indices (a residual «schou# 185» in `others` would
        # otherwise be invisible to the matcher and survive to the final).
        _fold_catalog_indices(cat)
        out["catalog"] = cat
    conflicts.extend(cat_conflicts)

    # Metal — verified-wins (CLAUDE.md §4 / consequence #2).
    metal = _collect_metal(members)
    if metal:
        out["metal"] = metal

    # Verification flags — OR-merge (any source attests counts)
    for field in ("metal_verified", "fineness_verified", "weight_rough_verified",
                  "diameter_mm_verified", "mint_verified", "verified",
                  "year_verified"):
        v = _or_merge_verified(sorted_members, field)
        if v is not None:
            out[field] = v

    # Multi-source measurement lists (every reading preserved)
    fine = _collect_field_list(members, "fineness")
    if fine:
        out["fineness"] = fine
    weights = _collect_field_list(members, "weight_rough_g")
    if weights:
        out["weight_rough_g"] = weights
    diameters = _collect_field_list(members, "diameter_mm")
    if diameters:
        out["diameter_mm"] = diameters

    # Sources union
    sources = _collect_sources(members)
    if sources:
        out["sources"] = sources

    # Notes — gap-fill (next non-None from lower authority if primary lacks)
    note = _take_first_non_none(sorted_members, "note")
    if note is not None:
        out["note"] = note
    vnote = _take_first_non_none(sorted_members, "verification_note")
    if vnote is not None:
        out["verification_note"] = vnote

    # issuing_entity — gap-fill (regroup classifier already set on every member)
    ie = _take_first_non_none(sorted_members, "issuing_entity")
    if ie is not None:
        out["issuing_entity"] = ie

    # Hede-attested Müntzfuß ratio (per-page «Marken fin udbragt til N
    # speciedaler/rd.kr/...» quote). Only ONE source publishes this —
    # the Hede 1971 catalogue via danskmoent.dk pages — so authority-
    # ordering doesn't apply; take whichever member carries it. Pass-
    # through the dict verbatim.
    yld = _take_first_non_none(sorted_members, "hede_muentzfuss_yield")
    if yld is not None:
        out["hede_muentzfuss_yield"] = yld

    # Audit trail
    out["composed_of"] = composed_of

    # Propagate `_entity_routing_hint` from members — last-writer-wins
    # is acceptable since hints are metadata-class. Primary member's
    # hint preferred when present, falling back to others.
    for m in sorted_members:
        if isinstance(m, dict) and m.get("_entity_routing_hint"):
            out["_entity_routing_hint"] = m["_entity_routing_hint"]
            break

    # §CN: aggregate per-member source-index errata into an `_errata_applied`
    # audit trail on the unified entry, so the composed record shows which
    # member-source had which index corrected (and to what). Underscore-keyed
    # → stripped before render, kept in the YAML for audit.
    errata_trail = []
    for m in sorted_members:
        if not isinstance(m, dict):
            continue
        for rec in (m.get("_errata_applied") or m.get("_source_errata") or []):
            if isinstance(rec, dict) and rec.get("field"):
                entry = {"source": m.get("id"), "field": rec["field"],
                         "printed": rec.get("printed"), "correct": rec.get("correct")}
                if entry not in errata_trail:
                    errata_trail.append(entry)
    if errata_trail:
        out["_errata_applied"] = errata_trail

    return out, conflicts


def _unified_id_for_class(members: list[dict]) -> str:
    """Pick the unified id per §5.2 authority rule: top-authority member's id
    with `unified-` prefix."""
    sorted_members = sorted(members, key=lambda c: -_authority_score(c.get("id", "")))
    primary = sorted_members[0]
    return f"unified-{primary['id']}"


# ---------------------------------------------------------------------------
# Decision file I/O
# ---------------------------------------------------------------------------


def _load_decisions(entity_id: str) -> dict:
    """Load explicit merge_decisions/<entity>.yml if present.
    Returns {merges: [{members, reason}], no_merges: [...],
    year_demote: [{member_id|members, reason}]} — year_demote names
    reign-window placeholder members whose year span must not widen the union
    (§CU curator-mute; applied in process_entity, honoured by
    _union_year_ranges via the `_year_demoted` flag)."""
    path = V2_MERGE_DECISIONS / f"{entity_id}.yml"
    if not path.exists():
        return {"merges": [], "no_merges": [], "year_demote": []}
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "merges": doc.get("merges", []) or [],
        "no_merges": doc.get("no_merges", []) or [],
        "year_demote": doc.get("year_demote", []) or [],
    }


# ---------------------------------------------------------------------------
# Per-entity processing
# ---------------------------------------------------------------------------


def _load_seeds_for_entity(entity_id: str) -> list[dict]:
    """Walk data/v2/seed/<source>/<entity>.yml across all sources.
    Returns flat list of coin dicts; each dict has its `id` for identification."""
    coins: list[dict] = []
    if not V2_SEED.exists():
        return coins
    for src_dir in sorted(V2_SEED.iterdir()):
        if not src_dir.is_dir():
            continue
        path = src_dir / f"{entity_id}.yml"
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for c in doc.get("coins") or []:
            if isinstance(c, dict) and c.get("id"):
                coins.append(c)
    return coins


def _expand_member_against(mid: str, id_set) -> list[str]:
    """Resolve a merge-decision member id against an arbitrary id set,
    expanding a Hede bare-id («dk-hede-c4h112») to its sub-letter seeds
    («…112a», «…112b»). Mirrors the per-entity `_expand_member` closure but
    takes the id set explicitly so the global cross-entity pre-scan can resolve
    members that live in OTHER buckets. Returns [] when nothing matches."""
    if mid in id_set:
        return [mid]
    if re.search(r"\d$", mid):
        subs = sorted(k for k in id_set
                      if k.startswith(mid) and k[len(mid):].isalpha())
        if subs:
            return subs
    return []


def _load_all_seeds() -> tuple[dict[str, dict], dict[str, str]]:
    """Global seed index across ALL buckets. Returns
    ({id: coin}, {id: home_entity}). Used by the cross-entity pre-scan to
    resolve + pull member ids that live in a different entity's seed files."""
    by_id: dict[str, dict] = {}
    home: dict[str, str] = {}
    if not V2_SEED.exists():
        return by_id, home
    for src_dir in sorted(V2_SEED.iterdir()):
        if not src_dir.is_dir():
            continue
        for path in sorted(src_dir.glob("*.yml")):
            entity = path.stem
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for c in doc.get("coins") or []:
                if isinstance(c, dict) and c.get("id"):
                    by_id[c["id"]] = c
                    home[c["id"]] = entity
    return by_id, home


# Cross-entity curator merges live in ONE global file (target_entity explicit),
# distinct from the per-entity merge_decisions/<entity>.yml. The «_» prefix
# keeps it out of the entity namespace (`_all_entities` walks seed dirs only;
# `_load_decisions` reads `<entity>.yml`, never this file).
V2_CROSS_ENTITY_DECISIONS = V2_MERGE_DECISIONS / "_cross_entity.yml"


def _load_cross_entity_decisions(
    all_ids: set[str],
) -> tuple[dict[str, list[list[str]]], dict[str, str]]:
    """Pre-scan `data/v2/merge_decisions/_cross_entity.yml`. Each `merges` entry
    carries an explicit `target_entity` + `members` (ids from ANY bucket).

    Returns:
      pull_groups:   {target_entity: [[member_id, ...], ...]}  — force-union groups
      member_target: {member_id: target_entity}                — drives pull + exclude

    Members are resolved (+ Hede sub-letter expansion) against the global id
    set. A member absent from every bucket warns + is skipped; a member mapped
    to two different targets is a curator error → hard assert."""
    pull_groups: dict[str, list[list[str]]] = {}
    member_target: dict[str, str] = {}
    if not V2_CROSS_ENTITY_DECISIONS.exists():
        return pull_groups, member_target
    doc = yaml.safe_load(V2_CROSS_ENTITY_DECISIONS.read_text(encoding="utf-8")) or {}
    for entry in doc.get("merges") or []:
        target = entry.get("target_entity")
        if not target:
            print("  ⚠ cross-entity merge with no target_entity — skipped")
            continue
        expanded: list[str] = []
        for m in (entry.get("members") or []):
            exp = _expand_member_against(m, all_ids)
            if not exp:
                print(f"  ⚠ cross-entity member {m!r} absent from all seeds — skipped")
                continue
            expanded.extend(exp)
        for mid in expanded:
            prior = member_target.get(mid)
            assert prior in (None, target), (
                f"cross-entity member {mid!r} mapped to two targets: "
                f"{prior!r} and {target!r}")
            member_target[mid] = target
        if len(expanded) >= 2:
            pull_groups.setdefault(target, []).append(expanded)
    return pull_groups, member_target


# ---------------------------------------------------------------------------
# Parallel PASS-1 workers
# ---------------------------------------------------------------------------
# The O(n²) PASS-1 matcher (every pair → confident / low_confidence; no_match
# discarded, re-derived within components in PASS 2) is embarrassingly
# parallel: each pair's verdict depends ONLY on the two coins, the entity's
# reign_index, and the explicit-curator no_merge set — never on other pairs or
# on accumulated state. We split the i-rows across worker PROCESSES (macOS
# spawn → these must be module-level functions + module globals, not
# closures). Results are re-sorted by (a_id, b_id) in the parent, which
# reproduces the serial (i<j) ordering EXACTLY, so PASS 2 / 2b / union see
# byte-identical input → byte-identical output. Each worker memoises
# _catalog_refs in its own address space (one entity per pool, coins stable).
_MP_IDS: list = []
_MP_SEEDS: dict = {}
_MP_ENTITY = None
_MP_REIGN = None
_MP_EXPLICIT: frozenset = frozenset()
# Blocking candidate adjacency {i: sorted [j>i, ...]}; None = no blocking
# (full O(n²) — the baseline path, kept for the MERGE_BLOCKING=0 regression
# gate). See _build_candidate_adjacency for the soundness proof.
_MP_CANDIDATES: dict | None = None

# Candidate-blocking toggle. Default ON. MERGE_BLOCKING=0 forces the full
# O(n²) baseline (used to prove byte-identical output vs the blocked path).
_MERGE_BLOCKING = os.environ.get("MERGE_BLOCKING", "1") != "0"


def _build_candidate_adjacency(ids, seeds_by_id, entity_id, reign_index):
    """Blocking index → {i: sorted [j>i, ...]} of candidate pairs to compare.

    SOUNDNESS (zero regression by construction). match_pair NEVER returns a
    non-no_match verdict unless `primary_true >= 2` (confidence calc lines
    ~1713/1723/1727) OR the §9a path (line ~1700, which requires
    `primary["catalog"] is True`). The four primary signals are {metal,
    nominal, catalog, ruler}. Since `metal` is a SINGLE signal, `>=2 primary
    TRUE` is impossible without at least one TRUE among {nominal, catalog,
    ruler}. A primary signal is TRUE only when the two coins AGREE on that
    value. Therefore EVERY non-no_match pair shares at least one of:
      • the normalised nominal,
      • a catalog ref (entity-scoped, same scope+value — or same numeric
        core, to cover sub-variant tolerance like «15a» ≈ «15»),
      • the normalised-or-D33-inferred ruler.
    Indexing on exactly those tokens and emitting every co-posting pair yields
    a strict SUPERSET of all confident + low_confidence pairs. The skipped
    pairs are all guaranteed no_match — which neither union nor surface (PASS 2
    registers no_merge only within confident components; no_match pairs aren't
    written to match_uncertainty). So the merged output is unchanged. A
    MERGE_BLOCKING=0 byte-identical diff gate confirms this empirically on top
    of the proof. (2026-06-04 perf pass — turns danish_realm's 89.7 M O(n²)
    match_pair calls into the ~shared-token candidate set.)
    """
    n = len(ids)
    postings: dict = defaultdict(list)
    for idx in range(n):
        coin = seeds_by_id[ids[idx]]
        toks = set()
        nom = _normalise_nominal(coin.get("nominal"))
        if nom:
            toks.add(("n", nom))
        ra = _normalise_ruler(coin.get("ruler"))
        if not ra and reign_index:
            ra = _infer_ruler(coin, reign_index)
        if ra:
            toks.add(("r", ra))
        for scope, val in _catalog_refs(coin, entity_id).items():
            for v in str(val).split("|"):
                v = v.strip()
                if not v:
                    continue
                toks.add(("c", scope, v))
                m = re.match(r"\d+", v)        # numeric core → sub-variant tolerance
                if m and m.group(0) != v:
                    toks.add(("c", scope, m.group(0)))
        for t in toks:
            postings[t].append(idx)            # appended in ascending idx order
    adj: dict = defaultdict(set)
    for plist in postings.values():
        L = len(plist)
        for a in range(L):
            ia = plist[a]
            for b in range(a + 1, L):
                adj[ia].add(plist[b])          # plist ascending → only j>ia
    return {i: sorted(js) for i, js in adj.items()}


def _pass1_set_globals(ids, seeds_by_id, entity_id, reign_index, explicit_no_merge,
                       candidates=None):
    """Populate the PASS-1 worker globals. Called directly in the parent for
    the serial path, and as the Pool initializer for the parallel path."""
    global _MP_IDS, _MP_SEEDS, _MP_ENTITY, _MP_REIGN, _MP_EXPLICIT, _MP_CANDIDATES
    global _CATALOG_REFS_MEMO_ENABLED
    _MP_IDS = ids
    _MP_SEEDS = seeds_by_id
    _MP_ENTITY = entity_id
    _MP_REIGN = reign_index
    _MP_EXPLICIT = explicit_no_merge
    _MP_CANDIDATES = candidates
    _CATALOG_REFS_MEMO.clear()
    _CATALOG_REFS_MEMO_ENABLED = True


def _pass1_eval_i(i: int):
    """Evaluate every pair (i, j>i) for row i; return (confident, low) sublists.
    no_match verdicts are intentionally discarded (PASS 2 re-derives them
    within confident components). Reads only module globals + i → safe to run
    in a worker process."""
    ids = _MP_IDS
    seeds = _MP_SEEDS
    entity_id = _MP_ENTITY
    reign_index = _MP_REIGN
    explicit = _MP_EXPLICIT
    a_id = ids[i]
    coin_a = seeds[a_id]
    n = len(ids)
    conf: list[dict] = []
    low: list[dict] = []
    # Candidate blocking: when an adjacency is supplied, only the j>i that
    # SHARE >=1 of {nominal, catalog-ref, ruler} with i are compared — a
    # provable superset of all non-no_match pairs (match_pair needs >=2
    # primary TRUE, so >=1 of those three must agree). None → full O(n²).
    js = _MP_CANDIDATES.get(i, ()) if _MP_CANDIDATES is not None else range(i + 1, n)
    for j in js:
        b_id = ids[j]
        if frozenset({a_id, b_id}) in explicit:
            continue
        result = match_pair(coin_a, seeds[b_id], entity_id, reign_index=reign_index)
        d = result["decision"]
        if d == "confident":
            conf.append({"a": a_id, "b": b_id,
                         "primary": result["primary"],
                         "fallback": result["fallback"]})
        elif d == "low_confidence":
            low.append({"members": [a_id, b_id],
                        "primary": result["primary"],
                        "fallback": result["fallback"],
                        "why": result["why"]})
    return conf, low


# Entities at/above this seed count run PASS 1 across worker processes; below
# it the pool spawn/pickle overhead outweighs the gain, so we stay serial.
# Override via MERGE_PARALLEL_THRESHOLD (e.g. =0 forces parallel for tests).
_PASS1_PARALLEL_THRESHOLD = int(os.environ.get("MERGE_PARALLEL_THRESHOLD", "4000"))


def process_entity(entity_id: str,
                   member_target: dict[str, str] | None = None,
                   pull_groups: dict[str, list[list[str]]] | None = None,
                   all_seeds_by_id: dict[str, dict] | None = None) -> dict:
    """Returns:
      {
        'entity_id': str,
        'seeds_count': int,
        'unified_entries': [unified_coin_dict, ...],
        'unified_count': int,
        'confident_merges': [{members, score}, ...],
        'low_confidence_pairs': [{members, why, signals}, ...],
        'forced_merges': [{members, reason}, ...],
        'forced_no_merges': [{members, reason}, ...],
      }
    """
    # Reset the per-coin _catalog_refs memo and OPT IN to memoisation for
    # this entity. id(coin) keys from a prior entity's (now-GC'd) coin dicts
    # could otherwise collide; the merger never mutates member catalogs, so
    # within one entity the memo stays valid. The flag stays True for the
    # rest of the process (each entity re-clears at its own start); it is
    # never set by absorb / audit / build callers, which therefore always
    # compute fresh — see the _CATALOG_REFS_MEMO_ENABLED note.
    global _CATALOG_REFS_MEMO_ENABLED
    _CATALOG_REFS_MEMO.clear()
    _CATALOG_REFS_MEMO_ENABLED = True
    seeds = _load_seeds_for_entity(entity_id)
    # Drop synthetic «catalog-overview» entries the parser sometimes
    # emits when a catalog index page (rather than a coin page) gets
    # processed as if it were a real entry. Their `nominal` field
    # carries page-title fragments like «- oversigt efter Galster» /
    # «overview of Y» — clearly not a numismatic denomination. The
    # seed file itself is left untouched (fix belongs in the parser,
    # tracked separately); we just skip them here so they don't
    # generate spurious low-confidence pairs against real coins.
    def _is_overview_page(c: dict) -> bool:
        nom = (c.get("nominal") or "").strip()
        if not nom:
            return False
        nom_lower = nom.lower()
        return (
            nom_lower.startswith("-")  # catalog-overview title prefix
            or "oversigt" in nom_lower
            or "overview" in nom_lower
        )
    pre_filter_count = len(seeds)
    seeds = [c for c in seeds if not _is_overview_page(c)]
    overview_dropped = pre_filter_count - len(seeds)

    # Cross-entity curator merges (pull-at-processing-time). `member_target`
    # maps a member id → the entity it was curator-declared to belong to.
    #   EXCLUDE: drop own-bucket seeds curator-routed to ANOTHER entity, so this
    #            entity doesn't also emit them as standalone unified entries.
    #   PULL IN: add foreign seeds curator-routed to THIS entity, so the
    #            force-union below + build_unified see them in one bucket.
    member_target = member_target or {}
    pull_groups = pull_groups or {}
    all_seeds_by_id = all_seeds_by_id or {}
    if member_target:
        seeds = [c for c in seeds
                 if member_target.get(c["id"], entity_id) == entity_id]
        present = {c["id"] for c in seeds}
        for mid, tgt in member_target.items():
            if tgt == entity_id and mid not in present and mid in all_seeds_by_id:
                seeds.append(all_seeds_by_id[mid])
                present.add(mid)
    # ids force-merged into THIS entity by a cross-entity decision (drives the
    # issuing_entity stamp on the resulting unified class).
    xentity_members_here: set[str] = {
        mid for grp in pull_groups.get(entity_id, []) for mid in grp}

    decisions = _load_decisions(entity_id)

    # D33 reign index — built ONCE per entity from members that DO
    # carry an attested ruler. Used by `match_pair` to fill ruler=null
    # gaps when (and ONLY when) a coin's covered year(s) attest a
    # single ruler. Transition / co-regent years carry multi-element
    # sets and stay null per user direction («краще null ніж
    # неправдивий nonull»).
    reign_index = _build_reign_index(seeds, entity_id)

    seeds_by_id: dict[str, dict] = {c["id"]: c for c in seeds}
    uf = UnionFind()
    # Ensure all ids are in uf so singleton classes show up.
    for cid in seeds_by_id:
        uf.find(cid)

    def _expand_member(mid: str) -> list[str]:
        """Resolve a merge_decision member id to the real seed id(s) present.

        A Hede BARE id (e.g. `dk-hede-c4h112`) whose page the parser now splits
        into sub-letter entries (`c4h112a`, `c4h112b`) expands to those — the
        curator decision was made at the «whole Hede 112» level, so it applies
        to every sub-variant (force_union: they ARE one coin; no_merge: each
        sub-variant differs from the other-coin members). A genuinely-missing id
        resolves to `[]` so the caller warns + skips (never KeyError-crashes).
        Non-Hede ids (numista/ucoin/numismaster) have no alpha-suffix siblings,
        so this is a no-op identity for them."""
        if mid in seeds_by_id:
            return [mid]
        if re.search(r"\d$", mid):
            subs = sorted(k for k in seeds_by_id
                          if k.startswith(mid) and k[len(mid):].isalpha())
            if subs:
                return subs
        return []

    # 1. Apply explicit no_merges first (curator decisions take precedence
    #    over any auto-rule). Expand each member; pair ONLY across distinct
    #    original members (never within one member's sub-letter expansion —
    #    112a/112b are sub-variants of one coin, not a curator no_merge pair).
    forced_no_merges: list[dict] = []
    for entry in decisions["no_merges"]:
        groups = []
        for m in (entry.get("members") or []):
            exp = _expand_member(m)
            if exp:
                groups.append(exp)
            else:
                print(f"  ⚠ no_merge member {m!r} absent from seed — skipped")
        for gi in range(len(groups)):
            for gj in range(gi + 1, len(groups)):
                for a in groups[gi]:
                    for b in groups[gj]:
                        uf.add_no_merge(a, b, explicit=True)
        forced_no_merges.append(entry)

    # 1b. Stamp `_year_demoted` on reign-window placeholder members named in
    #     `year_demote` (§CU curator-mute). `_union_year_ranges` holds these
    #     back to a last-resort pass so a member carrying the ruler's whole
    #     reign (rather than the coin's strike years) never widens the merged
    #     year. In-memory on the seed dicts (which ARE build_unified's
    #     `members`); the decision file re-applies it every run, so nothing is
    #     written to the seed YAML. `_expand_member` covers bare-Hede→sub-letter.
    for entry in decisions.get("year_demote", []):
        ids = entry.get("members") or (
            [entry["member_id"]] if entry.get("member_id") else [])
        for mid in ids:
            exp = _expand_member(mid)
            if not exp:
                print(f"  ⚠ year_demote member {mid!r} absent from seed — skipped")
                continue
            for sid in exp:
                seeds_by_id[sid]["_year_demoted"] = True

    # 2. PRE-PASS: run matcher on every pair, register no_match pairs in
    #    union-find BEFORE attempting any union. This guarantees that
    #    transitive merges (A↔B, A↔C both confident, B↔C no_match) DO
    #    NOT silently override the B↔C no_match — union() refuses any
    #    cross-class merge that would put a no_merge pair in the same
    #    class.
    confident_pairs: list[dict] = []
    low_confidence: list[dict] = []
    ids = sorted(seeds_by_id)
    # PASS 1 (hot O(n²)): collect confident + low_confidence ONLY. The
    # no_match → no_merge registration is DEFERRED to PASS 2 below. Storing
    # every no_match pair (≈ all O(n²) pairs for a large entity — 89.7M for
    # danish_realm) would balloon UnionFind.no_merge to >10 GB and OOM-kill
    # the process (observed 2026-06-02). PASS 2 registers no_merge only WITHIN
    # confident-connected components, which is the complete set union() ever
    # consults (proof in the PASS 2 note), so the deferral is behaviour-
    # identical. Skipping explicit-curator no_merge pairs here mirrors the
    # original `can_union` guard: during the original loop `can_union` only
    # ever filtered EXPLICIT no_merges, because auto no_merges are added for
    # the SAME pair being processed and so never pre-block a not-yet-visited
    # pair (each pair is visited exactly once, i<j).
    _explicit = frozenset(uf.explicit_no_merge)
    # Candidate blocking (sound superset of all non-no_match pairs) — collapses
    # the O(n²) PASS-1 fan-out to shared-token pairs. MERGE_BLOCKING=0 disables
    # it (full O(n²) baseline) for the regression gate.
    _candidates = (_build_candidate_adjacency(ids, seeds_by_id, entity_id, reign_index)
                   if _MERGE_BLOCKING else None)
    _pass1_set_globals(ids, seeds_by_id, entity_id, reign_index, _explicit, _candidates)
    if len(ids) >= _PASS1_PARALLEL_THRESHOLD:
        # Parallel across worker processes. imap_unordered scrambles row
        # order, so we re-sort by (a_id, b_id) afterwards — which is exactly
        # the serial i<j iteration order (ids is sorted) → PASS 2 / 2b / union
        # receive byte-identical input.
        n_workers = max(1, (os.cpu_count() or 2) - 1)
        # FORK context (not the macOS-default spawn): the parent already set
        # the PASS-1 globals via _pass1_set_globals(...) above, and forked
        # workers inherit them through copy-on-write memory — so we pass NO
        # initializer/initargs. Spawn instead pickles `seeds_by_id` (13398
        # entries for danish_realm) to EVERY worker as initargs, which
        # deadlocked / was pathologically slow (workers idle at 0% CPU while
        # the pool stalled in setup — observed 2026-06-03). Fork inherits the
        # dict for free → no large-object pickling, no hang. macOS allows fork
        # for this pure-compute script (verified: fork-Pool smoke test passes).
        ctx = mp.get_context("fork")
        with ctx.Pool(n_workers) as pool:
            for conf, low in pool.imap_unordered(
                    _pass1_eval_i, range(len(ids)), chunksize=8):
                confident_pairs.extend(conf)
                low_confidence.extend(low)
        confident_pairs.sort(key=lambda p: (p["a"], p["b"]))
        low_confidence.sort(key=lambda p: (p["members"][0], p["members"][1]))
    else:
        for i in range(len(ids)):
            conf, low = _pass1_eval_i(i)
            confident_pairs.extend(conf)
            low_confidence.extend(low)
        # no_match → deferred to PASS 2 (within-component only)

    # 2b. POST-PRE-PASS: Single-candidate promotion for null primary
    # signals (`ruler`, `nominal`).
    #
    # When a coin's `ruler` is null AND its D33 reign-index inference
    # also returns None (single-year-on-transition like 1648 or 1670),
    # OR its `nominal` is null (parser-gap on Galster / Bruun / etc.),
    # `match_pair` leaves the pair as low_confidence even though the
    # other side carries an attested value — primary_true stalls at 2.
    # To recover safely without inviting cross-reign / cross-type
    # mismerges, scan the low_confidence pairs FOR EACH null-attribute
    # coin and check whether every cross-source candidate attests THE
    # SAME value for that field. When the candidate set's union is
    # exactly one, promote ALL of that coin's low_confidence pairs to
    # confident — the other side has uniquely identified the missing
    # attribute. When the union has >1 distinct values (e.g. a 1648
    # 1/4 Speciedaler with both CHR IV and FR III Hede candidates),
    # it's genuinely ambiguous and stays low_confidence for curator
    # review.
    def _attested_value(coin: dict, field: str) -> str | None:
        if field == "ruler":
            return _attestation_ruler(coin)
        if field == "nominal":
            return _normalise_nominal(coin.get("nominal")) or None
        return None

    def _coin_self_value(coin: dict, field: str) -> str | None:
        if field == "ruler":
            return _normalise_ruler(coin.get("ruler")) or None
        if field == "nominal":
            return _normalise_nominal(coin.get("nominal")) or None
        return None

    pairs_to_promote: dict[tuple[str, str], dict] = {}
    null_attribute_coins: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for lcp in low_confidence:
        a_id, b_id = lcp["members"]
        for field in ("ruler", "nominal"):
            # The pair must be at the «one null one attested» pattern
            # for this specific field — primary[field] is None in the
            # matcher's output.
            if lcp["primary"].get(field) is not False and lcp["primary"].get(field) is not True:
                # field is None (or absent) on the pair
                for null_side, attested_side in [(a_id, b_id), (b_id, a_id)]:
                    if _coin_self_value(seeds_by_id[null_side], field):
                        continue
                    # For ruler: skip if the index would have inferred it
                    # (those would already be confident). For nominal:
                    # no inference path, all genuine nulls qualify.
                    if field == "ruler" and _infer_ruler(seeds_by_id[null_side], reign_index):
                        continue
                    attested = _attested_value(seeds_by_id[attested_side], field)
                    if not attested:
                        continue
                    null_attribute_coins[(null_side, field)].append({
                        "pair": lcp,
                        "attested_value": attested,
                    })
                    break

    def _coin_weight(coin: dict) -> float | None:
        w = coin.get("weight_rough_g")
        if isinstance(w, (int, float)):
            return float(w)
        if isinstance(w, list):
            for item in w:
                if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
                    return float(item["value"])
        return None

    for (null_id, field), candidates in null_attribute_coins.items():
        values_attested = {c["attested_value"] for c in candidates}
        winning_candidates = candidates
        winning_value = None

        if len(values_attested) == 1:
            # Unique attested value across all candidates — promote all.
            winning_value = next(iter(values_attested))
        else:
            # Multiple distinct attested values for this null field.
            # Weight tie-breaker: if the null-coin has a recorded weight
            # AND exactly ONE candidate's weight matches within ±2%, the
            # weight uniquely identifies the matching type — promote ONLY
            # that pair, leave the others as low_confidence. Same-weight
            # across different nominals is essentially impossible in
            # numismatic practice (1 Gulden ≈ 30g, ½ Gulden ≈ 15g — the
            # weight IS the denomination signature).
            null_coin = seeds_by_id.get(null_id)
            if null_coin is None:
                continue
            null_weight = _coin_weight(null_coin)
            if null_weight is None or null_weight <= 0:
                continue
            weight_matched = []
            for c in candidates:
                other_id = next(
                    iid for iid in c["pair"]["members"] if iid != null_id
                )
                other_coin = seeds_by_id.get(other_id)
                if other_coin is None:
                    continue
                ow = _coin_weight(other_coin)
                if ow is None or ow <= 0:
                    continue
                if abs(ow - null_weight) / null_weight < 0.02:
                    weight_matched.append(c)
            if len(weight_matched) != 1:
                continue
            winning_candidates = weight_matched
            winning_value = weight_matched[0]["attested_value"]

        for c in winning_candidates:
            a_id, b_id = c["pair"]["members"]
            key = (a_id, b_id)
            if key not in pairs_to_promote:
                primary = dict(c["pair"]["primary"])
                primary[field] = True
                why_lines = list(c["pair"]["why"])
                if len(values_attested) == 1:
                    why_lines.append(
                        f"promoted: single cross-source candidate's {field} attestation is consistent ({winning_value!r})"
                    )
                else:
                    why_lines.append(
                        f"promoted: weight tie-breaker uniquely selects {field}={winning_value!r} (weight {null_weight} ± 2 %)"
                    )
                pairs_to_promote[key] = {
                    "a": a_id, "b": b_id,
                    "primary": primary,
                    "fallback": c["pair"]["fallback"],
                    "why": why_lines,
                }
            else:
                pairs_to_promote[key]["primary"][field] = True
                if len(values_attested) == 1:
                    pairs_to_promote[key]["why"].append(
                        f"promoted: single cross-source candidate's {field} attestation is consistent ({winning_value!r})"
                    )
                else:
                    pairs_to_promote[key]["why"].append(
                        f"promoted: weight tie-breaker uniquely selects {field}={winning_value!r} (weight {null_weight} ± 2 %)"
                    )

    if pairs_to_promote:
        promoted_keys = set(pairs_to_promote.keys())
        confident_pairs.extend(pairs_to_promote.values())
        low_confidence = [
            lcp for lcp in low_confidence
            if tuple(lcp["members"]) not in promoted_keys
        ]

    # PASS 2: register auto no_merge ONLY within confident-connected
    # components. union() (step 3) consults UnionFind.no_merge solely in its
    # cross-class check (members of class rx × members of class ry) — and
    # classes are built EXCLUSIVELY by unioning confident_pairs. Hence every
    # pair union() ever tests lies within ONE confident-connected component;
    # no_match pairs spanning two different components are never consulted, so
    # omitting them changes no merge outcome while bounding the no_merge set
    # to Σ(component²) (≈0.5 % of O(n²) — 42 k vs 7.6 M on danish_norway).
    # Tentative components are built from confident_pairs INCLUDING the §2b
    # promotions appended just above; the component UF here is a throwaway for
    # grouping only — the real unions run in step 3. (The `can_union` guard
    # skips pairs already carrying an EXPLICIT curator no_merge.)
    _comp_parent: dict[str, str] = {}

    def _cfind(x: str) -> str:
        _comp_parent.setdefault(x, x)
        while _comp_parent[x] != x:
            _comp_parent[x] = _comp_parent[_comp_parent[x]]
            x = _comp_parent[x]
        return x

    def _cunion(a: str, b: str) -> None:
        ra, rb = _cfind(a), _cfind(b)
        if ra != rb:
            lo, hi = (ra, rb) if ra < rb else (rb, ra)
            _comp_parent[hi] = lo

    for cp in confident_pairs:
        _cunion(cp["a"], cp["b"])
    _components: dict[str, list[str]] = defaultdict(list)
    for cid in _comp_parent:
        _components[_cfind(cid)].append(cid)
    for _members in _components.values():
        if len(_members) < 2:
            continue
        _ms = sorted(_members)
        for _ii in range(len(_ms)):
            _ma = seeds_by_id[_ms[_ii]]
            for _jj in range(_ii + 1, len(_ms)):
                _mb_id = _ms[_jj]
                if not uf.can_union(_ms[_ii], _mb_id):
                    continue
                if match_pair(_ma, seeds_by_id[_mb_id], entity_id,
                              reign_index=reign_index)["decision"] == "no_match":
                    uf.add_no_merge(_ms[_ii], _mb_id)

    # 3. Apply confident auto-merges. union() refuses any merge that would
    #    create a class containing a no_match pair. Run this BEFORE curator
    #    forced-merges so every equivalence class is fully formed first —
    #    force_union (step 4) then clears auto no_merges between the two
    #    COMPLETE classes, so a curator merge of e.g. a Hede-156 type pulls
    #    in all its KM-15 siblings even though they each carry an auto
    #    no_merge against the KM-20 variant being merged in.
    confident_merges: list[dict] = []
    transitivity_blocks: list[dict] = []
    for cp in confident_pairs:
        ok, blocking = uf.union(cp["a"], cp["b"])
        if ok:
            confident_merges.append({
                "members": [cp["a"], cp["b"]],
                "primary": cp["primary"],
                "fallback": cp["fallback"],
            })
        elif blocking:
            transitivity_blocks.append({
                "would_merge": [cp["a"], cp["b"]],
                "blocked_by_no_match": sorted(blocking),
            })

    # 4. Apply explicit curator merges LAST via force_union: a curator merge
    #    outranks the heuristic matcher, so auto no_merges between the member
    #    classes are CLEARED; only an EXPLICIT curator no_merge can block it
    #    (genuine curator contradiction → warn, leave separate).
    forced_merges: list[dict] = []
    for entry in decisions["merges"]:
        expanded: list[str] = []
        for m in (entry.get("members") or []):
            exp = _expand_member(m)
            if exp:
                expanded.extend(exp)
            else:
                print(f"  ⚠ merge member {m!r} absent from seed — skipped")
        # union every expanded id into one class (a curator bare-Hede merge
        # implies its sub-letters are the same coin → they join the class too).
        for i in range(1, len(expanded)):
            ok, conflict = uf.force_union(expanded[0], expanded[i])
            if not ok:
                print(f"  ⚠ forced merge {expanded[0]} + {expanded[i]} "
                      f"conflicts with explicit no_merge {sorted(conflict)} "
                      f"— left separate")
        forced_merges.append(entry)

    # 4b. Cross-entity curator merges. The members were pulled into this
    #     entity's `seeds_by_id` above, so the union is the same force_union
    #     path as a regular merge — it just spans coins whose home buckets
    #     differ. The resulting unified class is stamped issuing_entity=this
    #     entity in the build loop below.
    for grp in pull_groups.get(entity_id, []):
        present = [m for m in grp if m in seeds_by_id]
        for i in range(1, len(present)):
            ok, conflict = uf.force_union(present[0], present[i])
            if not ok:
                print(f"  ⚠ cross-entity merge {present[0]} + {present[i]} "
                      f"conflicts with explicit no_merge {sorted(conflict)} "
                      f"— left separate")
        if len(present) >= 2:
            forced_merges.append({"members": present, "cross_entity": True})

    # 4. Build unified entries from equivalence classes
    classes = uf.classes()
    unified_entries: list[dict] = []
    merge_conflicts: list[dict] = []  # data-loss visibility: per-unified conflicts
    for class_root, member_ids in sorted(classes.items()):
        member_coins = [seeds_by_id[mid] for mid in sorted(member_ids)]
        unified_id = _unified_id_for_class(member_coins)
        unified, conflicts = build_unified(member_coins, unified_id, entity_id)
        # Cross-entity stamp: a class containing a member curator-pulled into
        # this entity is a real coin of this jurisdiction. Derive its
        # issuing_entity from the merged MINT (the circulation signal) rather
        # than scalar-stamping `entity_id` — so a joint-mint coin (e.g. KM 631
        # struck Altona+Kopenhagen) keeps its full VALUE
        # `[danish_realm, royal_holstein]` and homes to the overlap file
        # `royal_holstein.yml` (visible on both pages via Pass 1), instead of
        # collapsing to scalar `danish_realm` and hiding from SH except via
        # the fragile Pass-2 intersection. `entity_id` is the fallback when the
        # merged coin has no resolvable mint (preserves the curator's pull
        # target so we never drop the class to `_unclassified`).
        if xentity_members_here & set(member_ids):
            unified["issuing_entity"] = (
                classify_mint_to_entity(unified.get("mint")) or entity_id)
        unified_entries.append(unified)
        if conflicts and len(member_coins) > 1:
            merge_conflicts.append({
                "unified_id": unified_id,
                "members": sorted(member_ids),
                # Convert tuples → dicts so yaml.safe_load can read them back
                "field_conflicts": [
                    {"field": f, "top_authority_value": t, "other_value": o}
                    for (f, t, o) in conflicts
                ],
            })

    # Deterministic order
    unified_entries.sort(key=lambda u: u["id"])

    return {
        "entity_id": entity_id,
        "seeds_count": len(seeds),
        "unified_entries": unified_entries,
        "unified_count": len(unified_entries),
        "confident_merges": confident_merges,
        "low_confidence_pairs": low_confidence,
        "forced_merges": forced_merges,
        "forced_no_merges": forced_no_merges,
        "merge_conflicts": merge_conflicts,
        "transitivity_blocks": transitivity_blocks,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _emit_unified_yaml(entity_id: str, unified_entries: list[dict],
                       seeds_count: int) -> str:
    today = date.today().isoformat()
    header = (
        f"# V2 seed_unified for political entity `{entity_id}`.\n"
        f"# Generated {today} by scripts/maintenance/merge_seeds_cross_source.py\n"
        f"# from data/v2/seed/<source>/{entity_id}.yml across all sources.\n"
        f"#\n"
        f"# Input: {seeds_count} per-source seed entries.\n"
        f"# Output: {len(unified_entries)} unified entries (one per physical coin).\n"
        f"#\n"
        f"# Each unified entry's `composed_of` lists the per-source seeds\n"
        f"# it absorbed via the §5.2 match hierarchy. `weight_rough_g[]`,\n"
        f"# `fineness[]`, `diameter_mm[]` are multi-source lists preserving\n"
        f"# every reading per CLAUDE.md §9a. `sources[]` is the union.\n\n"
    )
    payload = {
        "id": entity_id,
        "generated_at": today,
        "coins": unified_entries,
    }
    return header + yaml.dump(payload, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=120)


def _emit_match_uncertainty(entity_id: str, low_conf: list[dict],
                             merge_conflicts: list[dict] | None = None,
                             transitivity_blocks: list[dict] | None = None) -> str:
    today = date.today().isoformat()
    header = (
        f"# Match uncertainty for entity `{entity_id}` — gitignored diagnostic.\n"
        f"# Regenerated {today} by merge_seeds_cross_source.py.\n"
        f"#\n"
        f"# Two sections (both surface data the auto-merger couldn't handle\n"
        f"# without losing information):\n"
        f"#\n"
        f"# 1. low_confidence_pairs — seed-pairs that look LIKE same coin\n"
        f"#    but matcher's primary signals were insufficient to confirm.\n"
        f"#    Resolution: add to merge_decisions/{entity_id}.yml::merges\n"
        f"#    OR extend matcher rules.\n"
        f"#\n"
        f"# 2. merge_conflicts — successful merges where scalar fields\n"
        f"#    DISAGREED across members (top-authority value kept in\n"
        f"#    unified entry; lower-authority value would be lost without\n"
        f"#    this log). Resolution: either accept top-auth, OR widen\n"
        f"#    the unified schema to preserve both, OR fix the parser\n"
        f"#    that emitted the wrong value.\n"
        f"#\n"
        f"# DO NOT edit this file — it's overwritten on every run.\n"
        f"# Curator decisions go into data/v2/merge_decisions/{entity_id}.yml.\n\n"
    )
    payload = {
        "entity_id": entity_id,
        "generated_at": today,
        "low_confidence_pairs": low_conf,
        "merge_conflicts": merge_conflicts or [],
        "transitivity_blocks": transitivity_blocks or [],
    }
    return header + yaml.dump(payload, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=120)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _all_entities() -> list[str]:
    """All entity ids that have at least one seed yaml."""
    seen: set[str] = set()
    if not V2_SEED.exists():
        return []
    for src_dir in V2_SEED.iterdir():
        if not src_dir.is_dir():
            continue
        for p in src_dir.glob("*.yml"):
            seen.add(p.stem)
    return sorted(seen)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write outputs (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Write data/v2/seed_unified/ + data/v2/match_uncertainty/")
    parser.add_argument("--entity", help="Process only this entity")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all low-confidence pairs (default: top 10 per entity)")
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False

    entities = [args.entity] if args.entity else _all_entities()
    if not entities:
        print("No V2 seed files found under data/v2/seed/.")
        return 0

    # Cross-entity curator merges: scan ONCE, globally, before the per-entity
    # loop (a member's exclude from its source entity must agree with its pull
    # into the target — both sides need the same map).
    all_by_id, _home = _load_all_seeds()
    pull_groups, member_target = _load_cross_entity_decisions(set(all_by_id))
    if member_target and args.entity:
        affected = {args.entity} | {member_target[m] for m in member_target}
        if affected - {args.entity}:
            print("  ⚠ --entity with active cross-entity merges: run WITHOUT "
                  "--entity (or process every affected entity) so source-side "
                  "excludes also apply — single-entity --apply can leave a "
                  "duplicate in the un-processed bucket.\n")

    print(f"Processing {len(entities)} entit(y/ies)...\n")

    totals = Counter()
    for ent in entities:
        result = process_entity(ent, member_target=member_target,
                                pull_groups=pull_groups,
                                all_seeds_by_id=all_by_id)
        totals["seeds"] += result["seeds_count"]
        totals["unified"] += result["unified_count"]
        totals["confident_merges"] += len(result["confident_merges"])
        totals["low_confidence"] += len(result["low_confidence_pairs"])
        totals["forced_merges"] += len(result["forced_merges"])
        totals["forced_no_merges"] += len(result["forced_no_merges"])
        totals["merge_conflicts"] += len(result.get("merge_conflicts", []))

        reduction = result["seeds_count"] - result["unified_count"]
        line = (f"{ent:36s}  "
                f"seeds:{result['seeds_count']:4d}  → "
                f"unified:{result['unified_count']:4d}  "
                f"(−{reduction:3d})  "
                f"conf:{len(result['confident_merges']):3d}  "
                f"lowconf:{len(result['low_confidence_pairs']):3d}  "
                f"conflicts:{len(result.get('merge_conflicts', [])):3d}")
        if result["forced_merges"] or result["forced_no_merges"]:
            line += (f"  forced:{len(result['forced_merges'])}/"
                     f"{len(result['forced_no_merges'])}")
        print(line)

        if args.verbose and result["low_confidence_pairs"]:
            for pair in result["low_confidence_pairs"][:5]:
                print(f"    ? {pair['members']}: {pair['why']}")
            if len(result["low_confidence_pairs"]) > 5:
                print(f"    ? ... and {len(result['low_confidence_pairs']) - 5} more")

        if args.apply:
            V2_SEED_UNIFIED.mkdir(parents=True, exist_ok=True)
            (V2_SEED_UNIFIED / f"{ent}.yml").write_text(
                _emit_unified_yaml(ent, result["unified_entries"],
                                   result["seeds_count"]),
                encoding="utf-8",
            )
            if (result["low_confidence_pairs"] or result.get("merge_conflicts")
                    or result.get("transitivity_blocks")):
                V2_MATCH_UNCERTAINTY.mkdir(parents=True, exist_ok=True)
                (V2_MATCH_UNCERTAINTY / f"{ent}.yml").write_text(
                    _emit_match_uncertainty(
                        ent,
                        result["low_confidence_pairs"],
                        result.get("merge_conflicts"),
                        result.get("transitivity_blocks"),
                    ),
                    encoding="utf-8",
                )
            else:
                stale = V2_MATCH_UNCERTAINTY / f"{ent}.yml"
                if stale.exists():
                    stale.unlink()

    print()
    print(f"=== Totals ===")
    print(f"  Per-source seeds total:     {totals['seeds']:>5d}")
    print(f"  Unified entries total:      {totals['unified']:>5d}")
    print(f"  Reduction (merges):         {totals['seeds'] - totals['unified']:>5d}")
    print(f"  Confident auto-merges:      {totals['confident_merges']:>5d}")
    print(f"  Low-confidence pairs:       {totals['low_confidence']:>5d}")
    print(f"  Merge conflicts (logged):   {totals['merge_conflicts']:>5d}")
    print(f"  Forced merges (decisions):  {totals['forced_merges']:>5d}")
    print(f"  Forced no_merges (decisions): {totals['forced_no_merges']:>3d}")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
    else:
        print(f"\n✓ Wrote unified yamls to {V2_SEED_UNIFIED}/")
        print(f"  Match uncertainty diagnostics to {V2_MATCH_UNCERTAINTY}/ "
              f"(gitignored)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
