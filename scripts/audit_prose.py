#!/usr/bin/env python3
"""Prose linter — catches forbidden patterns in rendered prose.

Implements the operational test of CLAUDE.md §0a (reader voice vs
analyst voice), §0z (three reader roles), §2a (academic register +
forbidden non-words), and §2 (period-correct German orthography),
as a mechanical pass over the rendered-prose surfaces.

What it checks
--------------

Rendered-prose surfaces — fields whose content lands on the role-3
end-reader's page:

  * `data/locations/*.yml` — coin notes, phase descriptions,
    location description, fuss_refs labels, verification_note.
  * `data/locations/*-references.yml` — bibliography content.
  * `data/shared/fuesse.yml` — Fuß descriptions, phase narratives.
  * `data/shared/german_fuesse.yml` — landing-page Fuß cards.
  * `data/shared/german_fuesse-references.yml` — bibliography.

What it does NOT check
----------------------

  * Code files, docs/, CLAUDE.md itself (analyst voice OK there;
    CLAUDE.md also QUOTES forbidden phrases as worked examples).
  * Catalog identifiers (`catalog.km`, `catalog.hede`, …) and
    proper nouns (`mint`, `ruler`, `nominal` — period inscription,
    NEVER translate).

Severity
--------

  ERROR    high-confidence violation; should block on review.
  WARNING  worth a human look; sometimes a legitimate use.
  INFO     hint / observation, not blocking.

Exit codes
----------

  0   no ERRORs.
  1   at least one ERROR fired.

Usage
-----

    .venv/bin/python scripts/audit_prose.py
    .venv/bin/python scripts/audit_prose.py --location denmark
    .venv/bin/python scripts/audit_prose.py --rule '§2'
    .venv/bin/python scripts/audit_prose.py --language uk
    .venv/bin/python scripts/audit_prose.py --staged   # only git-staged files
    .venv/bin/python scripts/audit_prose.py --json     # machine-readable

Extending
---------

Add new rules to the RULES list at the top. Each rule is a tuple:

    (regex_pattern, severity, rule_section, languages, description)

  regex_pattern   compiled re.Pattern with re.IGNORECASE if desired
                  (use raw strings; the engine doesn't re-flag-it).
  severity        'error' | 'warning' | 'info'.
  rule_section    short marker like '§0a' / '§2'.
  languages       set of 'de' | 'en' | 'uk' the rule applies to,
                  or 'any' for cross-language.
  description     short explanatory phrase printed alongside hits.

When a new pattern produces false positives in the wild, prefer
tightening the regex (lookarounds for context) over adding global
suppressions. Per-line suppression is intentionally not supported —
the rules should be precise enough to avoid that scaffolding.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator

try:
    import yaml
except ImportError:
    print("PyYAML required. Install via .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# ----------------------------------------------------------------------------
# RULES
#
# Each rule: (compiled_pattern, severity, section, langs, description).
# Severity convention:
#   error   — strong false-positive resistance; pattern only fires on
#             unambiguous violations.
#   warning — context may legitimise the match; needs human review.
#   info    — heuristic / soft hint.
#
# All patterns are matched against HTML-stripped text. The stripper
# preserves the inside of <i>, <b>, <em>, <cite> tags but drops
# <a href="…">, <sup>…</sup>, <span data-…> attributes etc.
# ----------------------------------------------------------------------------

# Helper to compile a list of alternations into a word-boundaried regex.
def _kw(*words: str, flags: int = re.IGNORECASE) -> re.Pattern:
    body = "|".join(re.escape(w) for w in words)
    return re.compile(rf"(?<![\w-])({body})(?![\w-])", flags)


RULES: list[tuple[re.Pattern, str, str, set[str], str]] = [
    # ------------------------------------------------------------------
    # §0a + §0z — first-person plural about project, role-3 leak
    # ------------------------------------------------------------------
    # DE — «in unserem Artefakt», «unsere Karte», «wir behandeln» etc.
    (re.compile(r"\b(in unserem|unsere[rms]?\s+(?:Karte|Artefakt|Periodisierung|Taxonomie|Projekt|Datenbank|Tabelle))\b", re.IGNORECASE),
     "error", "§0z", {"de"},
     "project-internal reference in role-3 prose (CLAUDE.md §0z)"),
    (re.compile(r"\bwir\s+(?:behandeln|klassifizieren|betrachten|werten|analysieren|kategorisieren)\b", re.IGNORECASE),
     "error", "§0a", {"de"},
     "first-person plural about project work"),

    # EN — «our card», «this artefact», «we treat», «we classify»
    (re.compile(r"\b(our\s+(?:card|artefact|artifact|taxonomy|periodi[sz]ation|model|classification)|this\s+(?:artefact|artifact))\b", re.IGNORECASE),
     "error", "§0z", {"en"},
     "project-internal reference in role-3 prose"),
    (re.compile(r"\bwe\s+(?:treat|classify|consider|categori[sz]e|analy[sz]e|argue|propose)\b", re.IGNORECASE),
     "error", "§0a", {"en"},
     "first-person plural about project work"),

    # UK — «у нашому артефакті», «наша карта», «ми класифікуємо»
    (re.compile(r"\b(у\s+нашому|у\s+нашій|нашо[їюм]?\s+(?:карті|картці|таксономі[їю]|періодизаці[їю]|базі)|наш\s+артефакт)\b", re.IGNORECASE),
     "error", "§0z", {"uk"},
     "project-internal reference in role-3 prose"),
    (re.compile(r"\bми\s+(?:класифікуємо|вважаємо|пропонуємо|аналізуємо|трактуємо)\b", re.IGNORECASE),
     "error", "§0a", {"uk"},
     "first-person plural about project work"),

    # ------------------------------------------------------------------
    # §0z — file paths / code identifiers in rendered prose
    # ------------------------------------------------------------------
    # backticks containing project paths
    (re.compile(r"`[^`]*?(?:data/|scripts/|\.yml|\.md|\.py|seed_unsorted|fineness_anchor|km_register|catalog\.)[^`]*?`"),
     "error", "§0z", {"de", "en", "uk"},
     "project-internal code/path reference in role-3 prose"),

    # explicit CLAUDE.md / TODO / PLAYBOOKS references in role-3 prose
    (re.compile(r"\b(CLAUDE\.md|docs/TODO|docs/PLAYBOOKS|docs/DECISIONS|docs/SOURCES)\b"),
     "error", "§0z", {"de", "en", "uk"},
     "internal-doc reference in role-3 prose"),

    # ------------------------------------------------------------------
    # §2a — authorial editorialising
    # ------------------------------------------------------------------
    (_kw("interestingly", "importantly", "notably", "crucially", "remarkably"),
     "warning", "§2a", {"en"},
     "authorial editorialising (replace with the fact itself)"),
    (re.compile(r"\b(цікаво\s+що|важливо\s+зазначити|варто\s+зазначити|примітно)\b", re.IGNORECASE),
     "warning", "§2a", {"uk"},
     "authorial editorialising"),
    (re.compile(r"\b(interessanterweise|bemerkenswert|wichtig\s+zu\s+erwähnen)\b", re.IGNORECASE),
     "warning", "§2a", {"de"},
     "authorial editorialising"),

    # ------------------------------------------------------------------
    # §0a — hedging meta-language
    # ------------------------------------------------------------------
    (_kw("arguably", "presumably"),
     "warning", "§0a", {"en"},
     "hedging meta-language without explicit hypothesis marker"),
    (re.compile(r"\b(one could say|the case can be made|it could be argued)\b", re.IGNORECASE),
     "warning", "§0a", {"en"},
     "hedging meta-language"),

    # ------------------------------------------------------------------
    # §2a — forbidden non-words (Cyrillic-transliteration traps)
    # ------------------------------------------------------------------
    (_kw("прягеа"),
     "error", "§2a", {"uk"},
     "fabricated non-word (fake-feminine of «Prägung»); use «карбування» / «наклад»"),
    (re.compile(r"\bРеймсько-", re.IGNORECASE),
     "error", "§2a", {"uk"},
     "wrong rendering of «Reichsweit-»; use «загальноімперсько-» / «імперсько-»"),
    # Forbidden pseudo-Anglo-Slavic word «stope/stopa» — across EN/DE/UK
    # scopes. Catches all common shapes seen in the project:
    #   EN: «stope», «per-stope», «stopa-anchor»
    #   DE: «Stopa-Wert», «-Stope» / «-Stopen» compound suffixes,
    #       «Reduzierungsstope», standalone «Stopa» / «Stope»
    # Ukrainian «стопа» (Cyrillic) is the only legitimate form — the
    # pattern won't match Cyrillic because `\b...\b` + ASCII letters.
    (re.compile(r"\b(?:stope|stopa)(?:-\w+)?\b", re.IGNORECASE),
     "error", "§2a", {"en", "de"},
     "non-word «stope/stopa» — use «standard» / «Müntzfuß» / «-Fuß» / Cyrillic «стопа» (uk)"),
    (re.compile(r"\b\w+-[Ss]top[ae]n?\b"),
     "error", "§2a", {"en", "de"},
     "compound with «-Stope/-Stopa/-Stopen» suffix — use «-Fuß» / «-Müntzfuß»"),
    (re.compile(r"\bReduzierungsstope\b", re.IGNORECASE),
     "error", "§2a", {"de"},
     "non-word compound; use «Reduzierungs-Müntzfuß» or «reduzierter Müntzfuß»"),

    # ------------------------------------------------------------------
    # §2a — sensationalist intensifiers
    # ------------------------------------------------------------------
    (_kw("екстремальний", "екстремальна", "екстремальне", "екстремальні", "величезний", "величезна", "величезне"),
     "warning", "§2a", {"uk"},
     "sensationalist intensifier — quantify instead"),
    (_kw("extreme", "extremely", "massive", "unbelievable", "huge"),
     "warning", "§2a", {"en"},
     "sensationalist intensifier — quantify instead"),
    (_kw("extrem", "gewaltig", "enorm"),
     "warning", "§2a", {"de"},
     "sensationalist intensifier — quantify instead"),

    # editorial exclamation marks in rendered prose: heuristic — any !
    # at end of a non-quoted, non-block-tag position. We only catch
    # the obvious cases here (« ! » mid-sentence or a bracketed
    # exclamation), to avoid flagging legitimate enthusiastic period-
    # source quotes.
    (re.compile(r"(?<!\w)(WOW|wow|achtung!|Achtung!)\b"),
     "error", "§2a", {"de", "en", "uk"},
     "editorial exclamation in rendered prose"),

    # ------------------------------------------------------------------
    # §2 — period-correct German orthography
    # ------------------------------------------------------------------
    # Müntz- prefix forms — «Münzfuß» / «Münzwesen» etc are forbidden
    # in DE prose. Period-correct is Müntz-.
    # Tolerate «Reichsmünz-» / «Kurantmünz-» (modern compounds in
    # banking context) and the orthographic anchor «Münze» (the
    # institution «die Münze», a permitted modern form for the mint
    # entity name where period sources also use «Münze» / «Müntze»
    # interchangeably).
    (re.compile(r"(?<![a-zA-ZäöüÄÖÜßt])(Münz)(?:fuß|fuss|wesen|vertrag|ordnung|reform|politik|recht|hoheit|standard|index|kabinett|sammlung)", re.UNICODE),
     "error", "§2", {"de"},
     "use Müntz- (period-correct) in DE prose"),

    # «Mark» without acceptable-context prefix. Allowed forms:
    # Reichsmark, Kurantmark, Mark Banco, Mark Dansk, Mark Lübisch,
    # Cölln. Marck, Marck Banco. We flag bare «Mark» that's not in
    # a banking-currency compound — but this is noisy enough that
    # we keep it WARNING, not ERROR.
    (re.compile(r"(?<![a-zA-ZäöüÄÖÜß-])Mark\b(?!\s+(?:Banco|Lübisch|Dansk|Courant|Kurant|deutscher))", re.UNICODE),
     "warning", "§2", {"de"},
     "Mark without Banco/Lübisch/etc context — consider Marck for period prose"),

    # «Taler» (modern) → Thaler (period). High-confidence.
    (re.compile(r"(?<![a-zA-ZäöüÄÖÜß-])(Taler|talern)\b", re.UNICODE),
     "error", "§2", {"de"},
     "use Thaler (period-correct) in DE prose"),

    # «Kurant» (modern) → Courant (period). Tolerate «Kurantmark» /
    # «Kurantdaler» / «Kurantmøntfod» (Danish period-form) — only
    # flag the bare adjective.
    (re.compile(r"(?<![a-zA-ZäöüÄÖÜß-])Kurant\b(?!(?:daler|m[øo]ntfod|mark|m[üu]nze|s?dukat))", re.UNICODE),
     "warning", "§2", {"de"},
     "consider Courant (period-correct) in DE prose"),

    # «Cölnisch» (with umlaut Mark «Cöllnisch») — both forms exist
    # in period sources; CLAUDE.md prefers «Cöllnische Marck». No
    # rule fired here (too contextual).

    # «bis» (modern preposition) → biß (period). High volume,
    # warning only.
    (re.compile(r"(?<![a-zA-ZäöüÄÖÜß-])bis\b(?![sz])", re.UNICODE),
     "warning", "§2", {"de"},
     "consider biß (period-correct) for the preposition «until/to»"),

    # ------------------------------------------------------------------
    # §0b — hypothesis-vs-fact: confident hedge words without explicit
    # hypothesis marker. WARNING because some uses are legitimate
    # (period-source uncertainty: «den Quellen zufolge wahrscheinlich»).
    # ------------------------------------------------------------------
    (_kw("likely", "probably", "presumably"),
     "warning", "§0b", {"en"},
     "hedge word — label as hypothesis or remove (CLAUDE.md §0b)"),
    (_kw("wahrscheinlich", "vermutlich"),
     "warning", "§0b", {"de"},
     "hedge word — label as hypothesis or attribute to a source"),
    (re.compile(r"\b(імовірно|ймовірно|припускається|схоже на те)\b", re.IGNORECASE),
     "warning", "§0b", {"uk"},
     "hedge word — label as hypothesis or attribute to a source"),
]


# ----------------------------------------------------------------------------
# Field selection: which (path, lang) pairs to lint inside a YAML doc.
# ----------------------------------------------------------------------------

# Fields whose values are role-3 rendered prose, by location of the file.
# Each entry: a JSONPath-like expression understood by walk_string_fields()
# below. The walker only emits strings at these paths.
LOCATION_PROSE_PATHS = {
    # location level
    "description.{lang}",
    # coins[]
    "coins[].note.{lang}",
    "coins[].verification_note.{lang}",
    "coins[].fuss_refs[].label.{lang}",
    # phases (legacy + current shapes)
    "phases.*.description.{lang}",
    "phases.*.label.{lang}",
}

REFS_PROSE_PATHS = {
    "entries[].content.{lang}",
}

# Shared/fuesse paths (data/shared/fuesse.yml + german_fuesse.yml)
FUSS_PROSE_PATHS = {
    # fuss-level
    "{fuss_id}.description.{lang}",
    "{fuss_id}.short.{lang}",
    "{fuss_id}.preamble.{lang}",
    "{fuss_id}.phases.*.description.{lang}",
    "{fuss_id}.phases.*.label.{lang}",
}

LANGS = ("de", "en", "uk")


# ----------------------------------------------------------------------------
# HTML stripper — keep text inside <i>/<b>/<em>/<cite>; drop <sup>/<a>
# bodies and all tag attributes. Conservative — turns HTML into a plain
# text approximation suitable for word-boundary regex matching.
# ----------------------------------------------------------------------------

_TAG_RE = re.compile(r"<(/?)(?P<tag>[a-zA-Z]+)\b[^>]*>")
_SUP_BODY_RE = re.compile(r"<sup\b[^>]*>.*?</sup>", re.DOTALL)
_A_HREF_BODY_RE = re.compile(r"<a\s[^>]*\bhref=\"#ref\d+\"[^>]*>.*?</a>", re.DOTALL)


def strip_html(text: str) -> str:
    """Return plain-text approximation. Drops <sup>...</sup> and <a href="#refN">...</a>
    BODIES entirely (these are citations, not prose). Other tags are
    stripped but their inner text preserved."""
    if "<" not in text:
        return text
    text = _SUP_BODY_RE.sub(" ", text)
    text = _A_HREF_BODY_RE.sub(" ", text)
    text = _TAG_RE.sub("", text)
    return text


# ----------------------------------------------------------------------------
# YAML walker — emit (key_path, lang, content_string) tuples.
# ----------------------------------------------------------------------------

def _emit_i18n(obj, lang: str, key_path: str) -> Iterator[tuple[str, str, str]]:
    """Emit a string if obj has the given lang key, else nothing."""
    if isinstance(obj, dict) and obj.get(lang) and isinstance(obj.get(lang), str):
        yield key_path, lang, obj[lang]


def walk_location(doc: dict) -> Iterator[tuple[str, str, str]]:
    """Yield (key_path, lang, content) for all role-3 prose fields in a location yaml."""
    # location-level description
    desc = doc.get("description")
    if isinstance(desc, dict):
        for lang in LANGS:
            yield from _emit_i18n(desc, lang, "description")

    # phases — either dict-of-dicts or list, depending on file
    phases = doc.get("phases")
    if isinstance(phases, dict):
        for phase_key, phase in phases.items():
            if not isinstance(phase, dict):
                continue
            for lang in LANGS:
                yield from _emit_i18n(phase.get("description") or {}, lang, f"phases.{phase_key}.description")
                yield from _emit_i18n(phase.get("label") or {}, lang, f"phases.{phase_key}.label")
    elif isinstance(phases, list):
        for i, phase in enumerate(phases):
            if not isinstance(phase, dict):
                continue
            for lang in LANGS:
                yield from _emit_i18n(phase.get("description") or {}, lang, f"phases[{i}].description")
                yield from _emit_i18n(phase.get("label") or {}, lang, f"phases[{i}].label")

    # coins
    for i, coin in enumerate(doc.get("coins") or []):
        if not isinstance(coin, dict):
            continue
        for lang in LANGS:
            yield from _emit_i18n(coin.get("note") or {}, lang, f"coins[{i}].note")
            yield from _emit_i18n(coin.get("verification_note") or {}, lang, f"coins[{i}].verification_note")
        # fuss_refs labels
        for j, fr in enumerate(coin.get("fuss_refs") or []):
            if isinstance(fr, dict) and isinstance(fr.get("label"), dict):
                for lang in LANGS:
                    yield from _emit_i18n(fr["label"], lang, f"coins[{i}].fuss_refs[{j}].label")


def walk_references(doc: dict) -> Iterator[tuple[str, str, str]]:
    """Yield (key_path, lang, content) for references-yaml content fields."""
    for i, entry in enumerate(doc.get("entries") or []):
        if not isinstance(entry, dict):
            continue
        content = entry.get("content")
        if isinstance(content, dict):
            for lang in LANGS:
                yield from _emit_i18n(content, lang, f"entries[{i}({entry.get('id', '?')})].content")


def walk_v2_location(doc: dict) -> Iterator[tuple[str, str, str]]:
    """Yield role-3 prose from a `data/v2/locations/<loc>.yml` file: the
    location summary, the per-fuss period prose, and timeline bar titles.
    Fuß `name` / `historical_name` are identifiers (never translated) and
    are deliberately skipped; `grundwerte` is structured data, not prose."""
    for lang in LANGS:
        yield from _emit_i18n(doc.get("summary") or {}, lang, "summary")
    fuss_periods = doc.get("fuss_periods")
    if isinstance(fuss_periods, dict):
        for fk, period in fuss_periods.items():
            if not isinstance(period, dict):
                continue
            for lang in LANGS:
                yield from _emit_i18n(period.get("hintergrund") or {}, lang, f"fuss_periods.{fk}.hintergrund")
                yield from _emit_i18n(period.get("closing") or {}, lang, f"fuss_periods.{fk}.closing")
                yield from _emit_i18n(period.get("description") or {}, lang, f"fuss_periods.{fk}.description")
                yield from _emit_i18n(period.get("details") or {}, lang, f"fuss_periods.{fk}.details")
    timeline = doc.get("timeline")
    if isinstance(timeline, dict):
        for i, bar in enumerate(timeline.get("bars") or []):
            if isinstance(bar, dict):
                for lang in LANGS:
                    yield from _emit_i18n(bar.get("bar_title") or {}, lang, f"timeline.bars[{i}].bar_title")


def walk_v2_final(doc: dict) -> Iterator[tuple[str, str, str]]:
    """Yield role-3 prose from a `data/v2/final/<entity>.yml` file — the
    per-coin notes (where V2 coin prose actually lives)."""
    for i, coin in enumerate(doc.get("coins") or []):
        if not isinstance(coin, dict):
            continue
        # Skip un-triaged seed coins: their notes are raw catalogue data,
        # not curated reader-facing prose (V1 parity — the V1 audit only saw
        # curated coins, never the data/seed/ raw layer).
        if coin.get("fuss") == "seed_unsorted":
            continue
        for lang in LANGS:
            yield from _emit_i18n(coin.get("note") or {}, lang, f"coins[{i}].note")
            yield from _emit_i18n(coin.get("verification_note") or {}, lang, f"coins[{i}].verification_note")
        for j, fr in enumerate(coin.get("fuss_refs") or []):
            if isinstance(fr, dict) and isinstance(fr.get("label"), dict):
                for lang in LANGS:
                    yield from _emit_i18n(fr["label"], lang, f"coins[{i}].fuss_refs[{j}].label")


def walk_fuesse(doc: dict) -> Iterator[tuple[str, str, str]]:
    """Yield from data/shared/fuesse.yml or german_fuesse.yml — fuss-level prose."""
    for fuss_id, fuss in (doc or {}).items():
        if not isinstance(fuss, dict):
            continue
        for slot in ("description", "short", "preamble", "name", "long"):
            sub = fuss.get(slot)
            if isinstance(sub, dict):
                for lang in LANGS:
                    yield from _emit_i18n(sub, lang, f"{fuss_id}.{slot}")
        # phases inside fuesse.yml
        phases = fuss.get("phases")
        if isinstance(phases, dict):
            for pk, phase in phases.items():
                if not isinstance(phase, dict):
                    continue
                for lang in LANGS:
                    yield from _emit_i18n(phase.get("description") or {}, lang, f"{fuss_id}.phases.{pk}.description")
                    yield from _emit_i18n(phase.get("label") or {}, lang, f"{fuss_id}.phases.{pk}.label")
        elif isinstance(phases, list):
            for i, phase in enumerate(phases):
                if not isinstance(phase, dict):
                    continue
                for lang in LANGS:
                    yield from _emit_i18n(phase.get("description") or {}, lang, f"{fuss_id}.phases[{i}].description")
                    yield from _emit_i18n(phase.get("label") or {}, lang, f"{fuss_id}.phases[{i}].label")


# ----------------------------------------------------------------------------
# Line-number recovery — given the raw YAML text and a content string,
# find the line where that string starts. Cheap heuristic: take the
# first ~50 chars of the content (HTML-stripped enough to be searchable),
# escape them as a fixed string, search the raw text. Returns 0 when
# not found (rare; the field key path is reported anyway).
# ----------------------------------------------------------------------------

def find_line_of(raw_text: str, content: str) -> int:
    if not content:
        return 0
    # Strip leading whitespace/HTML from content for the search probe.
    probe = content.lstrip()[:50]
    if not probe:
        return 0
    # YAML strings appear on the line of their `key:` declaration when
    # inline, or on the next line when block-scalar `|` form. We just
    # find the first occurrence of the probe substring.
    idx = raw_text.find(probe)
    if idx < 0:
        # Try with first 20 chars (block-scalar continuation might
        # have line breaks in between)
        probe = content.lstrip()[:20]
        idx = raw_text.find(probe)
        if idx < 0:
            return 0
    return raw_text[:idx].count("\n") + 1


# ----------------------------------------------------------------------------
# Hit dataclass + linting engine
# ----------------------------------------------------------------------------

@dataclass
class Hit:
    file: str
    line: int
    field: str
    lang: str
    rule: str
    severity: str
    description: str
    match: str
    excerpt: str  # ~80 chars of surrounding context


SEVERITY_RANK = {"error": 3, "warning": 2, "info": 1}


def lint_text(text: str, lang: str, field: str, file_str: str, raw_text: str,
              rule_filter: str | None) -> Iterator[Hit]:
    stripped = strip_html(text)
    line = find_line_of(raw_text, text)
    for pattern, severity, section, langs, description in RULES:
        if langs != "any" and lang not in langs:
            continue
        if rule_filter and rule_filter not in section:
            continue
        for m in pattern.finditer(stripped):
            start = max(0, m.start() - 40)
            end = min(len(stripped), m.end() + 40)
            excerpt = stripped[start:end].replace("\n", " ")
            yield Hit(
                file=file_str,
                line=line,
                field=field,
                lang=lang,
                rule=section,
                severity=severity,
                description=description,
                match=m.group(0),
                excerpt=excerpt,
            )


# ----------------------------------------------------------------------------
# File collection
# ----------------------------------------------------------------------------

def collect_files(args) -> list[Path]:
    if args.staged:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        candidates = [ROOT / p for p in out.stdout.split() if p.endswith(".yml")]
    else:
        candidates = []
        if args.location:
            candidates.extend([
                DATA / "v2" / "locations" / f"{args.location}.yml",
                DATA / "locations" / f"{args.location}-references.yml",
            ])
        else:
            # V2 prose surfaces: per-location display yamls + per-entity
            # coin files. Coin prose lives in data/v2/final/; location +
            # fuss-period prose lives in data/v2/locations/. Reference
            # sidecars stay in data/locations/ (shared with V2).
            candidates.extend(
                p for p in sorted((DATA / "v2" / "locations").glob("*.yml"))
                if not p.stem.endswith("-references"))
            # Skip _-prefixed synthetic buckets (e.g. _unclassified.yml) —
            # they're consumed by no location, so their coin notes are not
            # reader-facing.
            candidates.extend(
                p for p in sorted((DATA / "v2" / "final").glob("*.yml"))
                if not p.stem.startswith("_"))
            candidates.extend(sorted((DATA / "locations").glob("*-references.yml")))
            candidates.append(DATA / "shared" / "fuesse.yml")
            candidates.append(DATA / "shared" / "german_fuesse.yml")
            candidates.append(DATA / "shared" / "german_fuesse-references.yml")
    return [p for p in candidates if p.exists()]


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty()

def _c(text: str, code: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _sev_tag(severity: str) -> str:
    if severity == "error":
        return _c("ERROR  ", "1;31")
    if severity == "warning":
        return _c("WARNING", "1;33")
    return _c("INFO   ", "1;34")


def report_human(hits: list[Hit]) -> int:
    if not hits:
        print(_c("✓ No prose violations detected.", "1;32"))
        return 0
    # group by file
    by_file: dict[str, list[Hit]] = {}
    for h in hits:
        by_file.setdefault(h.file, []).append(h)
    for f in sorted(by_file):
        print(_c(f, "1"))
        for h in sorted(by_file[f], key=lambda x: (x.line, x.field, -SEVERITY_RANK[x.severity])):
            line_str = f"line {h.line}" if h.line else "line ?"
            print(f"  {_sev_tag(h.severity)} [{h.rule}] {line_str} ({h.lang}) {h.field}")
            print(f"           «{h.match}» — {h.description}")
            print(f"           > …{h.excerpt}…")
        print()
    # summary
    errs = sum(1 for h in hits if h.severity == "error")
    warns = sum(1 for h in hits if h.severity == "warning")
    infos = sum(1 for h in hits if h.severity == "info")
    summary = f"{len(hits)} hit(s) across {len(by_file)} file(s): {errs} error, {warns} warning, {infos} info"
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
            "info": sum(1 for h in hits if h.severity == "info"),
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
    ap.add_argument("--location", help="lint only data/locations/<NAME>.yml + its references")
    ap.add_argument("--language", choices=LANGS, help="lint only this language's fields")
    ap.add_argument("--rule", help="lint only rules whose section starts with this prefix (e.g. '§2')")
    ap.add_argument("--staged", action="store_true", help="lint only files staged in git")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = ap.parse_args()

    hits: list[Hit] = []
    files = collect_files(args)
    if not files:
        if args.json:
            print(json.dumps({"hits": [], "summary": {"total": 0, "error": 0, "warning": 0, "info": 0, "files": 0}}))
        else:
            print("no files to lint")
        return 0

    for path in files:
        raw = path.read_text(encoding="utf-8")
        try:
            doc = yaml.safe_load(raw) or {}
        except yaml.YAMLError as e:
            print(f"WARN: {path.relative_to(ROOT)} — yaml parse error, skipping: {e}", file=sys.stderr)
            continue
        rel = str(path.relative_to(ROOT))

        parent = path.parent.name
        grand = path.parent.parent.name
        if grand == "v2" and parent == "locations":
            walker = walk_v2_location
        elif grand == "v2" and parent == "final":
            if path.stem.startswith("_"):
                continue  # synthetic bucket (e.g. _unclassified) — not reader-facing
            walker = walk_v2_final
        elif parent == "locations":
            # data/locations/ now holds only -references sidecars (V1 coin
            # yamls removed); walk_location is kept for transitional / staged
            # V1 files.
            walker = walk_references if path.stem.endswith("-references") else walk_location
        elif parent == "shared":
            if path.stem.endswith("-references"):
                walker = walk_references
            else:
                walker = walk_fuesse
        else:
            continue  # unknown file shape

        for field, lang, content in walker(doc):
            if args.language and lang != args.language:
                continue
            for hit in lint_text(content, lang, field, rel, raw, args.rule):
                hits.append(hit)

    if args.json:
        return report_json(hits)
    return report_human(hits)


if __name__ == "__main__":
    sys.exit(main())
