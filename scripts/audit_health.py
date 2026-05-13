#!/usr/bin/env python3
"""audit_health — one-shot project-health snapshot.

Aggregates metrics across the project into a single dashboard. Run
at session start (per `docs/PLAYBOOKS.md` PB-8) for a «morning
briefing», or before declaring a piece of work done.

What it reports
---------------

  [Build]                schema + cross-ref validation status
  [Data completeness]    null-field counts, verified-flag counts
  [Per-location count]   coins per location yaml
  [Seed state (Hede)]    suppress / guard-survivor / uncurated counts
  [Caches]               sidecar entries + freshness per source
  [Prose lint]           audit_prose.py error/warning rollup
  [TODOs]                Open / Closed / pending-verification counts
  [Git]                  branch state, ahead-count, last commit

Sections delegate to existing scripts where they exist (build.py,
audit_prose.py) and read YAML / cache directly otherwise.

Usage
-----

    .venv/bin/python scripts/audit_health.py
    .venv/bin/python scripts/audit_health.py --fast   # skip slow build run
    .venv/bin/python scripts/audit_health.py --json   # machine-readable
    .venv/bin/python scripts/audit_health.py --section build,git

Exit codes
----------

  0   nothing flagged (no ⚠ in any section).
  1   at least one section flagged a warning or failure.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML required. Install via .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / "scripts" / "cache"

VENV_PY = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").exists() else sys.executable

# ----------------------------------------------------------------------------
# Result dataclass
# ----------------------------------------------------------------------------

@dataclass
class Row:
    label: str
    value: Any
    flag: str = ""        # "" / "ok" / "warn" / "fail"
    note: str = ""        # short trailing note

@dataclass
class Section:
    name: str
    rows: list[Row]
    @property
    def has_warning(self) -> bool:
        return any(r.flag in ("warn", "fail") for r in self.rows)

# ----------------------------------------------------------------------------
# Output formatting
# ----------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty()
LABEL_WIDTH = 26

def _c(text: str, code: str) -> str:
    if not USE_COLOR: return text
    return f"\033[{code}m{text}\033[0m"

def _flag(flag: str) -> str:
    if flag == "ok":   return _c("✓", "32")
    if flag == "warn": return _c("⚠", "33")
    if flag == "fail": return _c("✗", "31")
    return " "

def _fmt_value(v: Any) -> str:
    if isinstance(v, int):
        return f"{v:>6}"
    if isinstance(v, float):
        return f"{v:>6.1f}"
    return str(v)

# ----------------------------------------------------------------------------
# Sections
# ----------------------------------------------------------------------------

def section_build(fast: bool) -> Section:
    """Run scripts/build.py --validate-only (or a fast YAML self-load when
    fast=True)."""
    rows: list[Row] = []
    if fast:
        # Just load all YAMLs, no schema check
        errors = 0
        files = 0
        for p in DATA.rglob("*.yml"):
            files += 1
            try:
                yaml.safe_load(p.read_text())
            except yaml.YAMLError as e:
                errors += 1
        rows.append(Row("YAML load (fast)", f"{files} files", "ok" if errors == 0 else "fail",
                       "" if errors == 0 else f"{errors} parse error(s)"))
        return Section("Build", rows)

    r = subprocess.run([VENV_PY, "scripts/build.py", "--validate-only"],
                       cwd=ROOT, capture_output=True, text=True)
    ok = r.returncode == 0
    out = r.stdout + r.stderr
    coins_total = 0
    locations_total = 0
    suppressed_total = 0
    metal_mm = 0
    weight_mm = 0
    year_mm = 0
    yaml_dup_ok = "✓ No duplicate keys" in out
    xref_ok = "✓ All cross-references OK" in out
    for line in out.split("\n"):
        m = re.search(r"merged (\d+) seed coins", line)
        if m: coins_total += 0   # don't double-count
        m = re.search(r"Locations: (\d+)", line)
        if m: locations_total = int(m.group(1))
        m = re.search(r"suppressed (\d+) hede seed", line)
        if m: suppressed_total += int(m.group(1))
        m = re.search(r"^\s*ℹ\s+\S+:\s+(\d+) hede seed coin\(s\) share a curated Hede ref but differ on metal", line)
        if m: metal_mm += int(m.group(1))
        m = re.search(r"^\s*ℹ\s+\S+:\s+(\d+) hede seed coin\(s\) share a curated Hede ref but weights differ", line)
        if m: weight_mm += int(m.group(1))
        m = re.search(r"^\s*⚠\s+\S+:\s+(\d+) hede seed coin\(s\) match a curated Hede ref but with year_first", line)
        if m: year_mm += int(m.group(1))

    rows.append(Row("Schema validation", "pass" if ok else "FAIL",
                    "ok" if ok else "fail",
                    "" if ok else r.stderr.strip().split("\n")[-1][:80]))
    rows.append(Row("YAML duplicate keys", "none" if yaml_dup_ok else "?",
                    "ok" if yaml_dup_ok else "warn"))
    rows.append(Row("Cross-references", "all valid" if xref_ok else "?",
                    "ok" if xref_ok else "warn"))
    rows.append(Row("Locations", locations_total, "ok" if locations_total > 0 else "fail"))
    return Section("Build", rows)


def section_data_completeness() -> Section:
    """Per-file YAML scan: null-fields + unverified-flag counts."""
    coins_total = 0
    no_metal = 0
    no_fineness = 0
    no_weight = 0
    unv_metal = 0
    unv_fineness = 0
    unv_weight = 0
    unv_mint = 0
    seed_unsorted = 0
    for p in sorted((DATA / "locations").glob("*.yml")):
        if p.stem.endswith("-references"): continue
        doc = yaml.safe_load(p.read_text()) or {}
        for c in doc.get("coins") or []:
            if not isinstance(c, dict): continue
            coins_total += 1
            if c.get("metal") is None: no_metal += 1
            if c.get("fineness") is None: no_fineness += 1
            if c.get("weight_rough_g") is None: no_weight += 1
            if not c.get("metal_verified"): unv_metal += 1
            if not c.get("fineness_verified"): unv_fineness += 1
            if not c.get("weight_rough_verified"): unv_weight += 1
            if not c.get("mint_verified"): unv_mint += 1
            if c.get("fuss") == "seed_unsorted": seed_unsorted += 1
    rows = [
        Row("Total coins", coins_total),
        Row("Coins without metal", no_metal, "ok" if no_metal == 0 else "warn"),
        Row("Coins without fineness", no_fineness, "ok" if no_fineness == 0 else "warn",
            f"§R backfill candidates" if no_fineness else ""),
        Row("Coins without weight", no_weight, "ok" if no_weight == 0 else "warn"),
        Row("metal_verified: false", unv_metal,
            "warn" if unv_metal > 0 else "ok",
            "TODO §M ucoin harvest" if unv_metal > 50 else ""),
        Row("fineness_verified: false", unv_fineness,
            "warn" if unv_fineness > 0 else "ok"),
        Row("weight_rough_verified: false", unv_weight,
            "warn" if unv_weight > 0 else "ok"),
        Row("mint_verified: false", unv_mint, ""),
        Row("fuss=seed_unsorted (untriaged)", seed_unsorted,
            "warn" if seed_unsorted > 0 else "ok"),
    ]
    return Section("Data completeness", rows)


def section_per_location() -> Section:
    rows = []
    for p in sorted((DATA / "locations").glob("*.yml")):
        if p.stem.endswith("-references"): continue
        doc = yaml.safe_load(p.read_text()) or {}
        n = len(doc.get("coins") or [])
        rows.append(Row(p.stem, n, "" if n > 0 else "warn",
                        "" if n > 0 else "empty"))
    return Section("Per-location coin count", rows)


def section_seed_state(build_output: str = "") -> Section:
    """Parse seed-merge stats from build output. Re-runs build with
    --validate-only if build_output not provided."""
    if not build_output:
        r = subprocess.run([VENV_PY, "scripts/build.py", "--validate-only"],
                           cwd=ROOT, capture_output=True, text=True)
        build_output = r.stdout + r.stderr

    # Total seed entries in denmark hede
    seed_total = 0
    seed_path = DATA / "seed" / "hede" / "denmark.yml"
    if seed_path.exists():
        sd = yaml.safe_load(seed_path.read_text()) or {}
        seed_total = len(sd.get("coins") or [])

    suppressed = 0
    metal_mm = 0
    weight_mm = 0
    year_mm = 0
    merged = 0
    for line in build_output.split("\n"):
        if "suppressed" in line and "hede seed coin" in line:
            m = re.search(r"suppressed (\d+)", line); suppressed += int(m.group(1)) if m else 0
        if "differ on metal" in line:
            m = re.search(r"(\d+) hede seed", line); metal_mm += int(m.group(1)) if m else 0
        if "weights differ" in line:
            m = re.search(r"(\d+) hede seed", line); weight_mm += int(m.group(1)) if m else 0
        if "year_first >10y apart" in line:
            m = re.search(r"(\d+) hede seed", line); year_mm += int(m.group(1)) if m else 0
        if "merged" in line and "from hede" in line:
            m = re.search(r"merged (\d+) seed coins", line); merged += int(m.group(1)) if m else 0
    uncurated = max(0, merged - metal_mm - weight_mm - year_mm)
    rows = [
        Row("Total Denmark seed", seed_total),
        Row("Auto-suppressed", suppressed),
        Row("Rendered (uncurated)", merged,
            "warn" if merged > 100 else "",
            "Hede dedup audit ongoing" if merged > 100 else ""),
        Row("Metal-mismatch kept", metal_mm, ""),
        Row("Weight-mismatch kept", weight_mm, ""),
        Row("Year-mismatch kept", year_mm, "warn" if year_mm > 5 else ""),
    ]
    return Section("Seed state (Hede)", rows)


def _file_age(p: Path) -> str:
    if not p.exists(): return "—"
    age = time.time() - p.stat().st_mtime
    if age < 3600: return f"{int(age/60)}m ago"
    if age < 86400: return f"{int(age/3600)}h ago"
    return f"{int(age/86400)}d ago"


def section_caches() -> Section:
    rows = []
    # Numista
    numista_dir = CACHE / "numista"
    if numista_dir.exists():
        files = list(numista_dir.glob("*.json"))
        # _* files are aggregators, count only piece files
        pieces = [f for f in files if not f.name.startswith("_")]
        newest = max(pieces, key=lambda p: p.stat().st_mtime) if pieces else None
        rows.append(Row("Numista entries", len(pieces), "",
                       f"freshest {_file_age(newest)}" if newest else "—"))

    # ucoin
    ucoin_sc = CACHE / "ucoin" / "_composition.json"
    if ucoin_sc.exists():
        d = json.loads(ucoin_sc.read_text())
        ok = sum(1 for v in d.values() if not v.get("status_404"))
        err = sum(1 for v in d.values() if v.get("status_404"))
        rows.append(Row("ucoin composition", ok, "",
                       f"+{err} status_404, sidecar {_file_age(ucoin_sc)}"))

    # Hede
    hede_dir = CACHE / "hede"
    if hede_dir.exists():
        n = len(list(hede_dir.glob("c*h*.json")))
        rows.append(Row("Hede JSON", n))
        # Anyhow check parser run age
        manifest = hede_dir / "_parsed_index.json"
        if manifest.exists():
            rows.append(Row("  parsed-index updated", _file_age(manifest)))

    # IKMK
    ikmk_dir = CACHE / "ikmk"
    if ikmk_dir.exists():
        n = len(list(ikmk_dir.glob("*.json")))
        rows.append(Row("IKMK JSON", n))

    # Bruun
    bruun_lots = CACHE / "bruun" / "lots"
    if bruun_lots.exists():
        n = len(list(bruun_lots.glob("part*.json")))
        rows.append(Row("Bruun parts (parsed)", n))

    return Section("Caches", rows)


def section_i18n() -> Section:
    r = subprocess.run([VENV_PY, "scripts/audit_i18n.py", "--json"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode not in (0, 1):
        return Section("Cross-lang i18n", [Row("audit_i18n.py", "FAIL", "fail", r.stderr[:80])])
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return Section("Cross-lang i18n", [Row("audit_i18n.py", "JSON parse error", "fail")])
    s = d["summary"]
    rows = [
        Row("Errors", s["error"], "ok" if s["error"] == 0 else "warn",
            "TODO §X cleanup" if s["error"] > 10 else ""),
        Row("Warnings", s["warning"], "ok" if s["warning"] == 0 else ""),
    ]
    if s["error"] + s["warning"] > 0:
        by_rule = {}
        for h in d["hits"]:
            by_rule.setdefault(h["rule"], {"e": 0, "w": 0})
            by_rule[h["rule"]]["e" if h["severity"] == "error" else "w"] += 1
        rule_names = {"R1": "missing translation", "R2": "<sup> count mismatch",
                      "R3": "catalog-ref divergence", "R4": "length ratio extreme",
                      "R5": "Müntzfuß name translated"}
        for rule in sorted(by_rule):
            v = by_rule[rule]
            label = f"  {rule} {rule_names.get(rule, '')}"
            value = f"{v['e']}E / {v['w']}W"
            rows.append(Row(label, value))
    return Section("Cross-lang i18n", rows)


def section_prose_lint() -> Section:
    r = subprocess.run([VENV_PY, "scripts/audit_prose.py", "--json"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode not in (0, 1):
        return Section("Prose lint", [Row("audit_prose.py", "FAIL", "fail", r.stderr[:80])])
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return Section("Prose lint", [Row("audit_prose.py", "JSON parse error", "fail")])
    s = d["summary"]
    rows = [
        Row("Errors", s["error"], "ok" if s["error"] == 0 else "warn",
            "TODO §W cleanup" if s["error"] > 10 else ""),
        Row("Warnings", s["warning"], "ok" if s["warning"] == 0 else ""),
        Row("Files touched", s["files"]),
    ]
    # rule-level breakdown
    if s["error"] + s["warning"] > 0:
        by_rule = {}
        for h in d["hits"]:
            by_rule.setdefault(h["rule"], {"e": 0, "w": 0})
            by_rule[h["rule"]]["e" if h["severity"] == "error" else "w"] += 1
        for rule in sorted(by_rule):
            v = by_rule[rule]
            label = f"  {rule}"
            value = f"{v['e']}E / {v['w']}W"
            rows.append(Row(label, value))
    return Section("Prose lint", rows)


def section_todos() -> Section:
    text = (ROOT / "docs" / "TODO.md").read_text()
    # Open entries: under `## Open`, before `## Done`
    open_match = re.search(r"^## Open\s*\n(.*?)^## Done", text, re.MULTILINE | re.DOTALL)
    done_match = re.search(r"^## Done\s*\n(.*)", text, re.MULTILINE | re.DOTALL)
    open_section = open_match.group(1) if open_match else ""
    done_section = done_match.group(1) if done_match else ""
    open_entries = re.findall(r"^### [A-Z][A-Z]?\.", open_section, re.MULTILINE)
    done_entries = re.findall(r"^### [A-Z][A-Z]?\.", done_section, re.MULTILINE)

    # Pending verifications in handoff
    pending = 0
    hp = ROOT / "docs" / "handoff.md"
    if hp.exists():
        ht = hp.read_text()
        sect = re.search(r"## Pending verifications.*?(?=^## |\Z)", ht, re.MULTILINE | re.DOTALL)
        if sect:
            pending = len(re.findall(r"^\d+\.\s", sect.group(0), re.MULTILINE))
    rows = [
        Row("Open TODOs", len(open_entries)),
        Row("Closed TODOs", len(done_entries)),
        Row("Pending verifications (handoff)", pending,
            "warn" if pending > 0 else "ok"),
    ]
    return Section("TODOs", rows)


def section_git() -> Section:
    def g(args):
        return subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True).stdout.strip()

    branch = g(["rev-parse", "--abbrev-ref", "HEAD"])
    status = g(["status", "--porcelain"])
    n_changed = len([l for l in status.split("\n") if l.strip()])
    ahead = g(["rev-list", "--count", "origin/main..HEAD"]) or "?"
    last = g(["log", "-1", "--format=%cr · %h · %s"])
    # Submodule
    submod_status = g(["submodule", "status"])
    submod_dirty = submod_status.startswith(("+", "-"))
    submod_ahead = ""
    if (ROOT / "scripts" / "cache" / ".git").exists() or (ROOT / "scripts" / "cache").is_dir():
        sub_ahead = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            cwd=ROOT / "scripts" / "cache",
            capture_output=True, text=True
        ).stdout.strip() or "0"
        submod_ahead = sub_ahead

    rows = [
        Row("Branch", branch),
        Row("Working tree", "clean" if n_changed == 0 else f"{n_changed} modified",
            "ok" if n_changed == 0 else "warn"),
        Row("Ahead of origin", ahead,
            "warn" if ahead and ahead.isdigit() and int(ahead) > 0 else "ok",
            "git push when ready" if ahead and ahead.isdigit() and int(ahead) > 0 else ""),
        Row("Last commit", last),
        Row("Submodule scripts/cache", "clean" if not submod_dirty else "dirty",
            "ok" if not submod_dirty else "warn"),
    ]
    if submod_ahead and submod_ahead.isdigit() and int(submod_ahead) > 0:
        rows.append(Row("  ahead of origin", submod_ahead, "warn",
                       "push submodule first, then main"))
    return rows_to_section("Git", rows)


def rows_to_section(name: str, rows: list[Row]) -> Section:
    return Section(name, rows)


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def print_human(sections: list[Section], elapsed: float) -> int:
    print()
    title = f"muentzfuesse health — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    print(_c(title, "1"))
    print(_c("─" * len(title), "2"))
    any_warning = False
    for sec in sections:
        if sec.has_warning: any_warning = True
        print()
        header = f"[{sec.name}]"
        print(_c(header, "1;36"))
        for r in sec.rows:
            flag = _flag(r.flag)
            label = r.label.ljust(LABEL_WIDTH)
            value = _fmt_value(r.value)
            tail = f"  {_c(r.note, '2')}" if r.note else ""
            print(f"  {flag} {label} {value}{tail}")
    print()
    summary = f"completed in {elapsed:.1f}s"
    if any_warning:
        print(_c(f"⚠  {summary} — warnings present", "33"))
    else:
        print(_c(f"✓  {summary} — all green", "32"))
    return 1 if any_warning else 0


def print_json(sections: list[Section], elapsed: float) -> int:
    out = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": elapsed,
        "sections": [
            {"name": s.name, "has_warning": s.has_warning,
             "rows": [asdict(r) for r in s.rows]}
            for s in sections
        ],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 1 if any(s.has_warning for s in sections) else 0


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

SECTIONS = {
    "build": ("Build", lambda args: section_build(args.fast)),
    "data": ("Data completeness", lambda args: section_data_completeness()),
    "perloc": ("Per-location coin count", lambda args: section_per_location()),
    "seed": ("Seed state (Hede)", lambda args: section_seed_state()),
    "caches": ("Caches", lambda args: section_caches()),
    "prose": ("Prose lint", lambda args: section_prose_lint()),
    "i18n": ("Cross-lang i18n", lambda args: section_i18n()),
    "todos": ("TODOs", lambda args: section_todos()),
    "git": ("Git", lambda args: section_git()),
}
DEFAULT_SECTIONS = list(SECTIONS.keys())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fast", action="store_true",
                   help="skip slow build run (uses YAML-load only)")
    ap.add_argument("--json", action="store_true",
                   help="machine-readable JSON output")
    ap.add_argument("--section",
                   help="comma-separated list of sections to run "
                        "(default: all). Available: " + ", ".join(DEFAULT_SECTIONS))
    args = ap.parse_args()

    requested = args.section.split(",") if args.section else DEFAULT_SECTIONS
    invalid = [s for s in requested if s not in SECTIONS]
    if invalid:
        print(f"unknown section(s): {invalid}", file=sys.stderr)
        print(f"available: {list(SECTIONS.keys())}", file=sys.stderr)
        return 2

    t0 = time.time()
    sections = []
    for key in requested:
        try:
            sections.append(SECTIONS[key][1](args))
        except Exception as e:
            sections.append(Section(SECTIONS[key][0], [Row("error", str(e)[:80], "fail")]))
    elapsed = time.time() - t0

    if args.json:
        return print_json(sections, elapsed)
    return print_human(sections, elapsed)


if __name__ == "__main__":
    sys.exit(main())
