#!/usr/bin/env python3
"""audit_i18n — cross-language consistency detector for DE/EN/UK fields.

Manually-written 3-language prose drifts: a translator updates DE,
forgets EN; a citation gets added in DE but not propagated; a section
header is dropped from UK because the translator paused. This linter
catches the structural divergences across the trilingual triples.

What it checks
--------------

For every (de, en, uk) triple in role-3 rendered prose surfaces:

  R1 Missing translation       any of DE/EN/UK empty when another is filled.
  R2 Citation count mismatch   <sup> tag counts differ across the trio.
  R3 Catalog-ref localisation  KM / Hede / Sieg / Lange numbers translated
                               or transliterated (must stay identical).
  R4 Length ratio extreme      max/min > 3× and min < 100 chars
                               (signals heavy truncation / missing block).
  R5 Müntzfuß name translation forbidden Cyrillic-stop / Latin-foot
                               suffixes that suggest -Fuß was translated.

These are STRUCTURAL checks — they don't verify the *quality* of the
translation, only that the cross-language fields stay in shape.

Tier of fields scanned (the role-3 surfaces):

  * `data/locations/*.yml` — coin notes, phase descriptions, location
    description, fuss_refs labels, verification_note.
  * `data/locations/*-references.yml` — bibliography content.
  * `data/shared/fuesse.yml` — Fuß descriptions, phase narratives.
  * `data/shared/german_fuesse.yml` — landing-page Fuß cards.
  * `data/shared/german_fuesse-references.yml` — bibliography.

Usage
-----

    .venv/bin/python scripts/audit_i18n.py
    .venv/bin/python scripts/audit_i18n.py --location denmark
    .venv/bin/python scripts/audit_i18n.py --rule R1     # missing only
    .venv/bin/python scripts/audit_i18n.py --json

Exit codes: 0 all-clean; 1 any ERROR; warnings don't trip exit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator

try:
    import yaml
except ImportError:
    print("PyYAML required.", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

LANGS = ("de", "en", "uk")


# ----------------------------------------------------------------------------
# YAML triple walker
# ----------------------------------------------------------------------------

def _triple(obj, key_path: str) -> Iterator[tuple[str, dict[str, str]]]:
    """If obj is a dict with at least one of de/en/uk keys, emit one triple."""
    if not isinstance(obj, dict):
        return
    triple = {l: obj.get(l) or "" for l in LANGS}
    if any(triple.values()):
        # Force string type — bool / int / None get normalised to empty.
        triple = {l: v if isinstance(v, str) else "" for l, v in triple.items()}
        yield key_path, triple


def walk_location_triples(doc: dict) -> Iterator[tuple[str, dict[str, str]]]:
    """Walk a location yaml; yield (key_path, {de, en, uk}) triples."""
    yield from _triple(doc.get("description") or {}, "description")

    phases = doc.get("phases")
    if isinstance(phases, dict):
        for pk, phase in phases.items():
            if not isinstance(phase, dict):
                continue
            yield from _triple(phase.get("description") or {}, f"phases.{pk}.description")
            yield from _triple(phase.get("label") or {}, f"phases.{pk}.label")
    elif isinstance(phases, list):
        for i, phase in enumerate(phases):
            if not isinstance(phase, dict):
                continue
            yield from _triple(phase.get("description") or {}, f"phases[{i}].description")
            yield from _triple(phase.get("label") or {}, f"phases[{i}].label")

    for i, coin in enumerate(doc.get("coins") or []):
        if not isinstance(coin, dict):
            continue
        yield from _triple(coin.get("note") or {}, f"coins[{i}].note")
        yield from _triple(coin.get("verification_note") or {}, f"coins[{i}].verification_note")
        for j, fr in enumerate(coin.get("fuss_refs") or []):
            if isinstance(fr, dict):
                yield from _triple(fr.get("label") or {}, f"coins[{i}].fuss_refs[{j}].label")


def walk_references_triples(doc: dict) -> Iterator[tuple[str, dict[str, str]]]:
    for i, entry in enumerate(doc.get("entries") or []):
        if not isinstance(entry, dict):
            continue
        eid = entry.get("id", "?")
        content = entry.get("content")
        if isinstance(content, dict):
            yield from _triple(content, f"entries[{i}({eid})].content")


def walk_fuesse_triples(doc: dict) -> Iterator[tuple[str, dict[str, str]]]:
    for fuss_id, fuss in (doc or {}).items():
        if not isinstance(fuss, dict):
            continue
        for slot in ("description", "short", "preamble", "name", "long", "historical_name"):
            sub = fuss.get(slot)
            if isinstance(sub, dict):
                yield from _triple(sub, f"{fuss_id}.{slot}")
        phases = fuss.get("phases")
        if isinstance(phases, dict):
            for pk, phase in phases.items():
                if not isinstance(phase, dict):
                    continue
                yield from _triple(phase.get("description") or {}, f"{fuss_id}.phases.{pk}.description")
                yield from _triple(phase.get("label") or {}, f"{fuss_id}.phases.{pk}.label")
        elif isinstance(phases, list):
            for i, phase in enumerate(phases):
                if not isinstance(phase, dict):
                    continue
                yield from _triple(phase.get("description") or {}, f"{fuss_id}.phases[{i}].description")
                yield from _triple(phase.get("label") or {}, f"{fuss_id}.phases[{i}].label")


def walk_v2_location_triples(doc: dict) -> Iterator[tuple[str, dict[str, str]]]:
    """Walk a data/v2/locations/<loc>.yml; yield (key_path, {de,en,uk}).
    Fuß name / historical_name are identifiers (never translated) and
    grundwerte is structured data — both skipped."""
    yield from _triple(doc.get("summary") or {}, "summary")
    fuss_periods = doc.get("fuss_periods")
    if isinstance(fuss_periods, dict):
        for fk, period in fuss_periods.items():
            if not isinstance(period, dict):
                continue
            yield from _triple(period.get("hintergrund") or {}, f"fuss_periods.{fk}.hintergrund")
            yield from _triple(period.get("closing") or {}, f"fuss_periods.{fk}.closing")
            yield from _triple(period.get("description") or {}, f"fuss_periods.{fk}.description")
            yield from _triple(period.get("details") or {}, f"fuss_periods.{fk}.details")
    timeline = doc.get("timeline")
    if isinstance(timeline, dict):
        for i, bar in enumerate(timeline.get("bars") or []):
            if isinstance(bar, dict):
                yield from _triple(bar.get("bar_title") or {}, f"timeline.bars[{i}].bar_title")


def walk_v2_final_triples(doc: dict) -> Iterator[tuple[str, dict[str, str]]]:
    """Walk a data/v2/final/<entity>.yml; yield curated coin-note triples.
    Un-triaged seed coins (fuss == seed_unsorted) are raw catalogue data,
    not curated reader-facing prose — skipped (V1 parity)."""
    for i, coin in enumerate(doc.get("coins") or []):
        if not isinstance(coin, dict):
            continue
        if coin.get("fuss") == "seed_unsorted":
            continue
        yield from _triple(coin.get("note") or {}, f"coins[{i}].note")
        yield from _triple(coin.get("verification_note") or {}, f"coins[{i}].verification_note")
        for j, fr in enumerate(coin.get("fuss_refs") or []):
            if isinstance(fr, dict):
                yield from _triple(fr.get("label") or {}, f"coins[{i}].fuss_refs[{j}].label")


# ----------------------------------------------------------------------------
# Rule checks
# ----------------------------------------------------------------------------

SUP_RE = re.compile(r"<sup\b", re.IGNORECASE)
SUP_REF_RE = re.compile(r'href="#(ref\d+)"', re.IGNORECASE)

# Catalog refs that must stay identical across languages.
# We extract them from a normalised form and compare sets.
CATREF_RE = re.compile(
    # KM-DK# 25 / KM 16.1 / KM-87
    r"\bKM[-\s]?(?:DK|SH|NO|DE)?#?\s*\d{1,4}(?:\.\d+)?\b"
    # Hede 79A / Hede-178A
    r"|\bHede[-\s]\d+[A-Z]?\b"
    # Sieg 38.1
    r"|\bSieg[-\s]\d+(?:\.\d+)?\b"
    # Lange 426 / Lange-444A
    r"|\bLange[-\s]\d+[A-Z]?\b"
    # Schou 1a
    r"|\bSchou[-\s]\d+[a-z]?\b"
    # Fr. 290
    r"|\bFr\.?\s*\d+\b"
    # Bruun-7872 — hyphenated collection ID, 3-5 digits;
    # the hyphen disambiguates from «Bruun 1604» year references.
    r"|\bBruun-\d{3,5}\b"
    # N#108979 / N# 108979 — Numista
    r"|\bN#\s*\d+\b",
    re.IGNORECASE,
)

# Cyrillic transliteration of Müntzfuß-Fuß suffix or other forbidden non-words.
# Per CLAUDE.md i18n policy «Müntzfuß standard names NEVER translate».
#
# This rule is scoped to **compound Müntzfuß-name + Cyrillic-Fuß-suffix**
# patterns — the kind that translate a proper-name compound like
# «Krone-Müntzfuß» → «Krone-стопа» or «9¼-Thaler-Fuß» → «9¼-талер-стопа».
# It does NOT flag bare-«стопа» / «стопи» / «стопу» as «standard», which
# per §2a is the LEGITIMATE Ukrainian rendering of the generic concept
# («канонічна стопа Speciedaler», «та сама стопа», «вендсько-любецька
# стопа»). Flagging bare-«стопа» produces noise and obscures real
# proper-name compound violations.
#
# Two alternations:
#   1. <digit/fraction-prefix>-<Cyrillic-denom>-стопа — e.g.
#      «9¼-талер-стопа», «12-талер-стопа», «20-гульден-стопа».
#   2. <Latin-Mfuß-name-prefix>-стопа — e.g. «Krone-стопа»,
#      «Speciedaler-стопа», «Konventions-стопа», «Vereinsmünz-стопа».
#      The prefix list mirrors the curated Mfuß name set documented
#      in CLAUDE.md §i18n policy.
_LATIN_MFUSS_PREFIX = (
    r"(?:Krone|Kurantmønt|Speciedaler|Speciemont|Reichsdukaten|"
    r"Reichsgoldmünz|Reichsmünz|Konventions|Convention|Vereinsmünz|"
    r"Vereins|Pistolen|Graumann|Lübisch|Hamburgisch|Burgundisch|"
    r"Schleswig-Holsteinisch|Zinnaisch|Banco|Mark[ -]Banco|Altonaer|"
    r"Bremer|Lauenburger)"
)
FORBIDDEN_UK_MFUESSE = re.compile(
    r"(?:"
    r"\b\d+(?:[.,⅓¼½¾⅔]+)?-\s*(?:талер|тал|гульден|гульд|марк)-стоп(?:а|и|у|і|ою|о|ам|ах|ами|е)\b"
    r"|"
    rf"\b{_LATIN_MFUSS_PREFIX}-стоп(?:а|и|у|і|ою|о|ам|ах|ами|е)\b"
    r")",
    re.IGNORECASE,
)
FORBIDDEN_EN_MFUESSE = re.compile(r"\b(\d+(?:[\d./]+)?-thaler-foot|thaler-foot)\b", re.IGNORECASE)


@dataclass
class Hit:
    file: str
    field: str
    rule: str
    severity: str
    description: str
    detail: str


def normalize_catref(s: str) -> str:
    """Normalize KM-DK# 25 → KM-DK#25, Hede 79A → Hede79A — strip spaces
    around the numeric so cross-language string-equality works."""
    s = re.sub(r"\s+", "", s).upper()
    s = s.replace("#", "")
    return s


def check_missing(triple: dict[str, str]) -> list[Hit]:
    out = []
    nonempty = [l for l in LANGS if triple[l].strip()]
    if not nonempty:
        return out
    for l in LANGS:
        if not triple[l].strip():
            out.append(Hit("", "", "R1", "error",
                          "missing translation",
                          f"have: {','.join(nonempty)}; missing: {l}"))
    return out


def check_citation_count(triple: dict[str, str]) -> list[Hit]:
    counts = {l: len(SUP_RE.findall(triple[l])) for l in LANGS}
    nonempty_counts = {l: c for l, c in counts.items() if triple[l].strip()}
    if len(set(nonempty_counts.values())) > 1:
        return [Hit("", "", "R2", "warning",
                   "<sup> citation count mismatch",
                   f"de={counts['de']} en={counts['en']} uk={counts['uk']}")]
    return []


def check_catref_consistency(triple: dict[str, str]) -> list[Hit]:
    """Catalog refs (KM/Hede/Sieg/etc) should appear identically across
    languages. Different SETS of catalog refs → flag."""
    refs = {l: set(normalize_catref(m.group(0)) for m in CATREF_RE.finditer(triple[l]))
            for l in LANGS}
    nonempty_refs = {l: r for l, r in refs.items() if triple[l].strip()}
    if len(nonempty_refs) < 2:
        return []
    # Reference set: union of non-empty languages
    union = set.union(*nonempty_refs.values())
    if not union:
        return []
    out = []
    for l, r in nonempty_refs.items():
        missing = union - r
        if missing:
            out.append(Hit("", "", "R3", "warning",
                          f"catalog refs missing in {l}",
                          f"missing: {', '.join(sorted(missing))[:80]}"))
    return out


def check_length_ratio(triple: dict[str, str]) -> list[Hit]:
    """Extreme length disparity suggests heavy truncation / missing block."""
    lens = {l: len(triple[l].strip()) for l in LANGS}
    nonzero = [v for v in lens.values() if v > 0]
    if len(nonzero) < 2:
        return []
    if max(nonzero) / min(nonzero) > 3 and min(nonzero) < 200:
        return [Hit("", "", "R4", "warning",
                   "length ratio extreme",
                   f"de={lens['de']} en={lens['en']} uk={lens['uk']} chars")]
    return []


def check_mfuesse_translation(triple: dict[str, str]) -> list[Hit]:
    """Müntzfuß standard names NEVER translate (CLAUDE.md i18n policy).
    Catch Cyrillic «-стопа» and English «-thaler-foot» style attempts."""
    out = []
    if FORBIDDEN_UK_MFUESSE.search(triple["uk"]):
        m = FORBIDDEN_UK_MFUESSE.search(triple["uk"])
        out.append(Hit("", "", "R5", "error",
                      "Müntzfuß name translated to UK Cyrillic form",
                      f"matched: «{m.group(0)}» — Müntzfuß names never translate"))
    if FORBIDDEN_EN_MFUESSE.search(triple["en"].lower()):
        m = FORBIDDEN_EN_MFUESSE.search(triple["en"].lower())
        out.append(Hit("", "", "R5", "error",
                      "Müntzfuß name translated to EN form",
                      f"matched: «{m.group(0)}» — use German period form"))
    return out


ALL_CHECKS = {
    "R1": check_missing,
    "R2": check_citation_count,
    "R3": check_catref_consistency,
    "R4": check_length_ratio,
    "R5": check_mfuesse_translation,
}


def check_triple(triple: dict[str, str], file_str: str, field: str,
                 rule_filter: str | None) -> Iterator[Hit]:
    for rule_id, check_fn in ALL_CHECKS.items():
        if rule_filter and not rule_id.startswith(rule_filter):
            continue
        for hit in check_fn(triple):
            hit.file = file_str
            hit.field = field
            yield hit


# ----------------------------------------------------------------------------
# File collection
# ----------------------------------------------------------------------------

def collect_files(args) -> list[Path]:
    if args.location:
        return [p for p in [
            DATA / "v2" / "locations" / f"{args.location}.yml",
            DATA / "locations" / f"{args.location}-references.yml",
        ] if p.exists()]
    # V2 prose surfaces: per-location display yamls + per-entity coin files
    # (skip _-prefixed synthetic buckets like _unclassified — not reader-
    # facing). Reference sidecars stay in data/locations/ (shared with V2).
    files = [p for p in sorted((DATA / "v2" / "locations").glob("*.yml"))
             if not p.stem.endswith("-references")]
    files += [p for p in sorted((DATA / "v2" / "final").glob("*.yml"))
              if not p.stem.startswith("_")]
    files += sorted((DATA / "locations").glob("*-references.yml"))
    for name in ("fuesse.yml", "german_fuesse.yml", "german_fuesse-references.yml"):
        p = DATA / "shared" / name
        if p.exists():
            files.append(p)
    return [p for p in files if p.exists()]


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty()
def _c(text: str, code: str) -> str:
    if not USE_COLOR: return text
    return f"\033[{code}m{text}\033[0m"

SEV_RANK = {"error": 3, "warning": 2, "info": 1}

def _sev_tag(sev: str) -> str:
    if sev == "error":   return _c("ERROR  ", "1;31")
    if sev == "warning": return _c("WARNING", "1;33")
    return _c("INFO   ", "1;34")


def report_human(hits: list[Hit]) -> int:
    if not hits:
        print(_c("✓ No cross-language inconsistencies detected.", "1;32"))
        return 0
    by_file: dict[str, list[Hit]] = {}
    for h in hits:
        by_file.setdefault(h.file, []).append(h)
    for f in sorted(by_file):
        print(_c(f, "1"))
        for h in sorted(by_file[f], key=lambda x: (x.field, -SEV_RANK[x.severity])):
            print(f"  {_sev_tag(h.severity)} [{h.rule}] {h.field}")
            print(f"           {h.description}")
            print(f"           > {h.detail}")
        print()
    errs = sum(1 for h in hits if h.severity == "error")
    warns = sum(1 for h in hits if h.severity == "warning")
    summary = f"{len(hits)} hit(s) across {len(by_file)} file(s): {errs} error, {warns} warning"
    if errs:
        print(_c(summary, "1;31"))
        return 1
    elif warns:
        print(_c(summary, "1;33"))
        return 0
    else:
        print(summary)
        return 0


def report_json(hits: list[Hit]) -> int:
    out = {
        "hits": [asdict(h) for h in hits],
        "summary": {
            "total": len(hits),
            "error": sum(1 for h in hits if h.severity == "error"),
            "warning": sum(1 for h in hits if h.severity == "warning"),
            "files": len({h.file for h in hits}),
        },
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if out["summary"]["error"] else 0


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--location", help="lint only this location's yamls")
    ap.add_argument("--rule", help="filter rule(s) by prefix, e.g. R1")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    hits: list[Hit] = []
    for path in collect_files(args):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"WARN: {path.relative_to(ROOT)} — parse error: {e}", file=sys.stderr)
            continue
        rel = str(path.relative_to(ROOT))

        parent = path.parent.name
        grand = path.parent.parent.name
        if grand == "v2" and parent == "locations":
            walker = walk_v2_location_triples
        elif grand == "v2" and parent == "final":
            if path.stem.startswith("_"):
                continue  # synthetic bucket (e.g. _unclassified) — not reader-facing
            walker = walk_v2_final_triples
        elif parent == "locations":
            walker = walk_references_triples if path.stem.endswith("-references") else walk_location_triples
        elif parent == "shared":
            walker = walk_references_triples if path.stem.endswith("-references") else walk_fuesse_triples
        else:
            continue

        for field, triple in walker(doc):
            for hit in check_triple(triple, rel, field, args.rule):
                hits.append(hit)

    if args.json:
        return report_json(hits)
    return report_human(hits)


if __name__ == "__main__":
    sys.exit(main())
