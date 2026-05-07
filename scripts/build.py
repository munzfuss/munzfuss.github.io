#!/usr/bin/env python3
"""
Build the site from YAML data.

Usage:
  python scripts/build.py                        # full build
  python scripts/build.py --location schleswig_holstein   # single location
  python scripts/build.py --lang de              # single language
  python scripts/build.py --validate-only        # schema check, no render
  python scripts/build.py --debug                # dump intermediate JSON
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import ValidationError

# Make local lib importable when run as `python scripts/build.py`
sys.path.insert(0, str(Path(__file__).parent))

from lib import i18n
from lib.categorize import (
    categorize, compute_bar_layers, compute_coin_year_runs,
    compute_hover_zones, derive_holstein_mint_overrides,
)
from lib.compute import compute_location
from lib.render import build_env, generate_css
from lib.schema import Location, Fuss, I18nText


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATE_DIR = REPO_ROOT / "templates"
SITE_DIR = REPO_ROOT / "site"
DEBUG_DIR = REPO_ROOT / "output" / "debug"

DEFAULT_LANGS = ["de", "en", "uk"]


def load_fuesse() -> dict[str, Fuss]:
    path = DATA_DIR / "shared" / "fuesse.yml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    
    fuesse = {}
    for fuss_id, data in raw.items():
        data["id"] = fuss_id
        fuesse[fuss_id] = Fuss(**data)
    return fuesse


def load_theme() -> dict:
    with open(CONFIG_DIR / "theme.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_ui() -> dict:
    return i18n.load_ui(str(DATA_DIR / "i18n" / "ui.yml"))


def load_issuing_entities() -> dict:
    """Load political-entity definitions for the issuing_entity field."""
    path = DATA_DIR / "i18n" / "issuing_entities.yml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_YEAR_PARSE_4DIGIT = re.compile(r"\b(1[5-9]\d{2})\b")
_YEAR_PARSE_CENTURY = re.compile(r"\b(\d{1,2})\.\s*Jh\.?")


def _landing_year_from(entry: dict) -> int:
    """Extract a chronological start year for landing-page sorting.

    Order of precedence:
      1. Explicit `year_from: int` on the entry (escape hatch).
      2. First 4-digit year in the prefix of `years_label.de`
         (the part before the `→` arrow).
      3. Century-form `NN. Jh.` in the same prefix → (NN-1) * 100.
      4. Fallback: 9999 (entry sorts last).
    """
    explicit = entry.get("year_from")
    if isinstance(explicit, int):
        return explicit
    label = ((entry.get("years_label") or {}).get("de") or "")
    prefix = re.split(r"\s*[→—\-]\s*", label, maxsplit=1)[0]
    m = _YEAR_PARSE_4DIGIT.search(prefix)
    if m:
        return int(m.group(1))
    m = _YEAR_PARSE_CENTURY.search(prefix)
    if m:
        return (int(m.group(1)) - 1) * 100
    return 9999


def load_german_fuesse() -> list[dict]:
    """Load the landing-page reference catalogue of German Müntzfüße.

    Returned as a raw list of dicts (NOT validated against Pydantic) — this
    file is purely a presentation catalogue for the landing page and is not
    cross-referenced against the per-coin `coin.fuss` field. Returns empty
    list if the file is absent.

    Sorted by chronological start year (parsed from `years_label.de`
    prefix, or taken from an optional explicit `year_from: int` field).
    Stable secondary sort by YAML position keeps insertion order among
    entries that resolve to the same year. The `order` mechanism that
    drives location-page timeline bars does NOT apply here — the
    landing intentionally surfaces a chronological view.
    """
    path = DATA_DIR / "shared" / "german_fuesse.yml"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    entries = raw.get("entries", [])
    indexed = list(enumerate(entries))
    indexed.sort(key=lambda ie: (_landing_year_from(ie[1]), ie[0]))
    return [e for _, e in indexed]


def load_german_fuesse_references() -> dict | None:
    """Load the bibliography sidecar for the German Müntzfüße catalogue.

    Same convention as `data/locations/<loc>-references.yml`: a YAML
    file with `heading` (multilingual) and `entries` (each with id +
    multilingual content). Inline `<sup>` citations in the catalogue
    prose link by id; the landing template renders the section after
    the catalogue.
    """
    path = DATA_DIR / "shared" / "german_fuesse-references.yml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_locations(filter_id: str | None = None) -> list[Location]:
    locations = []
    for path in sorted((DATA_DIR / "locations").glob("*.yml")):
        # Skip reference sidecar files
        if path.stem.endswith("-references"):
            continue
        if filter_id and path.stem != filter_id:
            continue
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        try:
            loc = Location(**raw)
            # Attach references sidecar if present
            ref_path = path.parent / f"{path.stem}-references.yml"
            if ref_path.exists():
                with open(ref_path, encoding="utf-8") as rf:
                    loc._references_data = yaml.safe_load(rf)
            else:
                loc._references_data = None
            locations.append(loc)
        except ValidationError as e:
            print(f"❌ Schema errors in {path.name}:")
            print(e)
            raise
    return locations


def cross_ref_check(locations: list[Location], fuesse: dict[str, Fuss]) -> bool:
    all_ok = True
    for loc in locations:
        errors = loc.validate_cross_refs(fuesse)
        if errors:
            all_ok = False
            print(f"❌ Cross-reference errors in '{loc.id}':")
            for err in errors:
                print(f"   {err}")
    return all_ok


def dump_debug_computed(loc_id: str, computed) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    path = DEBUG_DIR / f"{loc_id}.computed.json"
    with open(path, "w", encoding="utf-8") as f:
        data = []
        for cc in computed:
            d = cc.raw.model_dump(exclude_none=True)
            d["_computed"] = {
                "weight_fein_g": cc.weight_fein_g,
                "soll_fein_g": cc.soll_fein_g,
                "delta_g": cc.delta_g,
                "delta_pct": cc.delta_pct,
                "within_remedium": cc.within_remedium,
                "implied_fuss": cc.implied_fuss,
            }
            if cc.alts:
                d["_computed"]["alts"] = [
                    {
                        "source": a.source,
                        "weight_rough_g": a.weight_rough_g,
                        "fineness": a.fineness,
                        "diameter_mm": a.diameter_mm,
                        "weight_fein_g": a.weight_fein_g,
                        "delta_g": a.delta_g,
                        "delta_pct": a.delta_pct,
                        "within_remedium": a.within_remedium,
                        "implied_fuss": a.implied_fuss,
                    } for a in cc.alts
                ]
            data.append(d)
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"   ↳ Wrote {path.relative_to(REPO_ROOT)}")


def build_location(
    loc: Location,
    fuesse: dict[str, Fuss],
    theme: dict,
    ui: dict,
    languages: list[str],
    env: Environment,
    debug: bool = False,
    repo_url: str = "",
    issuing_entities: dict | None = None,
    base_url: str = "",
) -> None:
    print(f"🏛️  Building {loc.id} ({len(loc.coins)} coins)")
    
    computed = compute_location(loc, fuesse)
    if debug:
        dump_debug_computed(loc.id, computed)
    
    tree = categorize(loc, computed, fuesse)

    # Per-location set of issuing entities that actually have coins here.
    # The filter strip in the template iterates the global registry but
    # SKIPS entries not in this set, so a chip with no coins to toggle
    # (e.g. `prussian_province` in schleswig_holstein.yml) doesn't render at all.
    active_entity_ids = {
        c.issuing_entity for c in loc.coins if c.issuing_entity is not None
    }

    # Pre-compute the up-to-six period × scope layers for each timeline bar.
    # Empty when this location has no timeline (e.g. lubeck stub).
    bar_layers = {}
    coin_years = {}
    hover_zones = {}
    if loc.timeline:
        # Auto-sync `events.first_mint.holstein` / `last_mint.holstein`
        # to the actual SH coin spans so a freshly-added Bruun-era
        # Speciedaler 1859 instantly shifts the mint layer right, and a
        # curator-set patent year (e.g. 10½-Krone-Fuß first_mint=1644
        # while the first physical strike is 1645) reflects the data,
        # not the decree. Other locations are no-ops.
        mint_overrides = derive_holstein_mint_overrides(loc, fuesse)
        if mint_overrides:
            fuesse_for_bars = {**fuesse, **mint_overrides}
            diffs = []
            for fid, new_f in mint_overrides.items():
                old_lm = fuesse[fid].events.last_mint.holstein
                new_lm = new_f.events.last_mint.holstein
                old_fm = fuesse[fid].events.first_mint.holstein
                new_fm = new_f.events.first_mint.holstein
                if new_fm != old_fm or new_lm != old_lm:
                    diffs.append(
                        f"{fid}: {old_fm}–{old_lm} → {new_fm}–{new_lm}"
                    )
            if diffs:
                print(f"   📐 Mint-event auto-sync ({len(diffs)} fuesse): "
                      + "; ".join(diffs))
        else:
            fuesse_for_bars = fuesse
        bar_layers = compute_bar_layers(
            loc.timeline.bars, fuesse_for_bars,
            loc.timeline.year_from, loc.timeline.year_to,
            scope_mode=loc.timeline.scope_mode,
        )
        # Per-bar list of consecutive-year runs marking every year a coin
        # was actually minted under that stope (per data/locations/<loc>.yml
        # coin entries). Renders as 1-year-wide rectangles overlaid on the
        # layered period × scope bar.
        coin_years = compute_coin_year_runs(
            loc.timeline.bars, computed,
            loc.timeline.year_from, loc.timeline.year_to,
        )
        # Hover zones — segments where the active layer set stays constant.
        # Each zone becomes a transparent overlay div with a static
        # `data-tooltip` aggregating all active layers' texts (template
        # builds the joined text from per-layer tooltip parts).
        hover_zones = compute_hover_zones(
            bar_layers,
            loc.timeline.year_from, loc.timeline.year_to,
        )

    # Resolve references (from sidecar YAML) if present
    references_data = getattr(loc, '_references_data', None)
    
    generated_date = datetime.now().strftime("%Y-%m-%d")
    
    tmpl = env.get_template("location.html.j2")
    
    for lang in languages:
        # Pre-resolve references for this language
        refs_for_lang = None
        if references_data:
            refs_for_lang = {
                'heading': i18n.t(references_data.get('heading'), lang),
                'entries': [
                    {'id': e['id'], 'content': i18n.t(e.get('content'), lang)}
                    for e in references_data.get('entries', [])
                    if i18n.t(e.get('content'), lang)
                ]
            }
        
        html = tmpl.render(
            tree=tree,
            ui=ui,
            theme=theme,
            lang=lang,
            languages=languages,
            references=refs_for_lang,
            generated_date=generated_date,
            repo_url=repo_url,
            base_url=base_url,
            issuing_entities=issuing_entities or {},
            active_entity_ids=active_entity_ids,
            bar_layers=bar_layers,
            coin_years=coin_years,
            hover_zones=hover_zones,
            ui_get=lambda k, l=lang: i18n.ui_get(ui, k, l),
            t=lambda v, l=lang: i18n.t(v, l),
            fmt_num=lambda v, **kw: i18n.fmt_num(v, lang, **kw),
            fmt_delta=lambda g, p: i18n.fmt_delta(g, p, lang),
            fmt_date=lambda d, l=lang: i18n.fmt_date(d, l),
        )

        out_dir = SITE_DIR / loc.id / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "index.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   → {out_file.relative_to(REPO_ROOT)}")


def build_landing(
    locations: list[Location],
    ui: dict,
    theme: dict,
    languages: list[str],
    env: Environment,
    repo_url: str = "",
    base_url: str = "",
    contact_email: str = "",
    german_fuesse: list[dict] | None = None,
    german_fuesse_references: dict | None = None,
    include_seed: bool = False,
) -> None:
    tmpl = env.get_template("landing.html.j2")
    generated_date = datetime.now().strftime("%Y-%m-%d")

    # Locations with any `seed_unsorted` coin haven't been triaged into proper
    # Müntzfuß standards. In production we hide them entirely from the landing
    # (the per-location pages still build, so existing URLs keep working). In
    # local builds (`--include-seed`, on by default when --base-url is empty)
    # they appear on the landing too, with a muted 'seed' card variant so the
    # researcher can navigate to them while iterating.
    seed_ids = {
        loc.id for loc in locations
        if any(c.fuss == "seed_unsorted" for c in loc.coins)
    }
    if include_seed:
        # Stable-sort so non-seed locations land first on the grid; seed
        # locations follow. Within each group the original location load
        # order (alphabetical via glob) is preserved.
        visible_locations = sorted(locations, key=lambda l: l.id in seed_ids)
        if seed_ids:
            print(f"🌱 Landing shows {len(seed_ids)} seed location(s) "
                  f"(local-build mode): {', '.join(sorted(seed_ids))}")
    else:
        visible_locations = [loc for loc in locations if loc.id not in seed_ids]
        if seed_ids:
            print(f"🙈 Landing hides {len(seed_ids)} location(s) with unsorted "
                  f"seed entries: {', '.join(sorted(seed_ids))}")

    # Landing is generated per-language at /<lang>/index.html;
    # root / redirects to /de/ (or user's preferred language via JS — optional)
    for lang in languages:
        # Resolve references for this language (same shape as per-
        # location pages: heading + list of {id, content}).
        gf_refs_for_lang = None
        if german_fuesse_references:
            gf_refs_for_lang = {
                'heading': i18n.t(german_fuesse_references.get('heading'), lang),
                'entries': [
                    {'id': e['id'], 'content': i18n.t(e.get('content'), lang)}
                    for e in german_fuesse_references.get('entries', [])
                    if i18n.t(e.get('content'), lang)
                ]
            }

        html = tmpl.render(
            locations=visible_locations,
            seed_ids=seed_ids,
            ui=ui,
            theme=theme,
            lang=lang,
            languages=languages,
            generated_date=generated_date,
            repo_url=repo_url,
            base_url=base_url,
            contact_email=contact_email,
            german_fuesse=german_fuesse or [],
            german_fuesse_references=gf_refs_for_lang,
            ui_get=lambda k, l=lang: i18n.ui_get(ui, k, l),
            t=lambda v, l=lang: i18n.t(v, l),
            fmt_date=lambda d, l=lang: i18n.fmt_date(d, l),
        )
        out_dir = SITE_DIR / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🏠 Landing: {out_dir.relative_to(REPO_ROOT)}/index.html")

    # Root index.html — language redirect.
    # Priority: 1) lang cookie set by app.js on previous visit
    #           2) browser preference (navigator.language)
    #           3) fallback to 'en'
    root_html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<title>Müntzfüße</title>
<script>
const base = {base_url!r};
const langs = ['de', 'en', 'uk'];
const m = document.cookie.match(/(?:^|;\\s*)lang=([a-z]{{2}})/);
const cookieLang = m ? m[1] : null;
const browserLang = (navigator.language || 'en').slice(0, 2).toLowerCase();
let target = 'en';
if (langs.includes(cookieLang)) target = cookieLang;
else if (langs.includes(browserLang)) target = browserLang;
window.location.replace(base + '/' + target + '/');
</script>
<noscript><meta http-equiv="refresh" content="0; url={base_url}/en/"></noscript>
</head><body><p>Loading… <a href="{base_url}/en/">English</a> · <a href="{base_url}/de/">Deutsch</a> · <a href="{base_url}/uk/">Українська</a></p></body></html>"""
    with open(SITE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(root_html)


def generate_assets(theme: dict) -> None:
    assets_dir = SITE_DIR / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css = generate_css(theme, lang="de")
    with open(assets_dir / "style.css", "w", encoding="utf-8") as f:
        f.write(css)
    print(f"🎨 CSS: site/assets/style.css ({len(css):,} bytes)")

    # Copy static assets (JS, images) from /assets → site/assets
    src_assets = REPO_ROOT / "assets"
    if src_assets.is_dir():
        for src in src_assets.iterdir():
            if src.is_file():
                dst = assets_dir / src.name
                shutil.copyfile(src, dst)
                print(f"📎 Asset: site/assets/{src.name} ({dst.stat().st_size:,} bytes)")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--location", help="Build only this location (default: all)")
    p.add_argument("--lang", help="Build only this language (default: all)")
    p.add_argument("--debug", action="store_true", help="Dump intermediate JSON")
    p.add_argument("--validate-only", action="store_true", help="Check schema + cross-refs, don't render")
    p.add_argument("--clean", action="store_true", help="Remove site/ before building")
    p.add_argument("--repo-url", default="", help="URL for source data link in footer")
    p.add_argument("--base-url", default="", help="URL prefix for assets and inter-page "
                   "links. Empty for user pages or root-served sites; '/repo-name' for "
                   "GitHub Pages project sites. Trailing slash stripped automatically.")
    p.add_argument("--include-seed", dest="include_seed", action="store_true",
                   default=None,
                   help="Include locations that still have seed_unsorted coins on the "
                        "landing page (rendered as cards with a 'seed' tag and muted "
                        "styling). Default: auto-enable when --base-url is empty "
                        "(local builds), suppress in production CI builds.")
    p.add_argument("--no-include-seed", dest="include_seed", action="store_false",
                   help="Force-hide seed locations from the landing page even on local "
                        "builds (matches production behaviour).")
    return p.parse_args()


def main():
    args = parse_args()

    # Normalise base_url: drop trailing slash so templates can use {{ base_url }}/path
    base_url = args.base_url.rstrip("/")

    # YAML integrity guard — runs BEFORE Pydantic validation because
    # Pydantic operates on the parsed dict, after PyYAML has silently
    # collapsed duplicate keys via last-wins. A botched edit that
    # duplicates a key (two `metal:` lines under one record) survives
    # schema validation and ships broken data; this AST walk catches it.
    from lib.yaml_check import check_data_directory
    print("🛡️  YAML integrity check (duplicate keys)...")
    n_dups = check_data_directory(Path("data"))
    if n_dups:
        print(f"\n❌ Found {n_dups} duplicate-key issue(s). Fix and rerun.")
        sys.exit(1)
    print("   ✓ No duplicate keys")
    print()

    # Load shared resources
    print("📦 Loading shared resources...")
    fuesse = load_fuesse()
    print(f"   Müntzfüße: {len(fuesse)} ({', '.join(fuesse)})")

    theme = load_theme()
    ui = load_ui()
    print(f"   UI strings: {len(ui)} keys")
    issuing_entities = load_issuing_entities()
    print(f"   Issuing entities: {len(issuing_entities)} ({', '.join(issuing_entities)})")
    german_fuesse = load_german_fuesse()
    print(f"   German Müntzfüße catalogue: {len(german_fuesse)} entries")
    german_fuesse_refs = load_german_fuesse_references()
    if german_fuesse_refs:
        print(f"   German Müntzfüße references: {len(german_fuesse_refs.get('entries', []))} entries")
    
    # Load locations
    locations = load_locations(filter_id=args.location)
    print(f"   Locations: {len(locations)} ({', '.join(l.id for l in locations)})")
    print()
    
    # Schema + cross-ref validation
    print("🔍 Validating cross-references...")
    if not cross_ref_check(locations, fuesse):
        print("\n❌ Validation failed. Fix errors above and rerun.")
        sys.exit(1)
    print("   ✓ All cross-references OK")
    print()
    
    if args.validate_only:
        print("✅ Validation-only mode. No rendering performed.")
        return
    
    # Clean site/ if requested
    if args.clean and SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
        print("🗑️  Cleaned site/")
    
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Render
    languages = [args.lang] if args.lang else DEFAULT_LANGS
    env = build_env(str(TEMPLATE_DIR))
    
    for loc in locations:
        build_location(loc, fuesse, theme, ui, languages, env,
                       debug=args.debug, repo_url=args.repo_url,
                       issuing_entities=issuing_entities, base_url=base_url)

    if len(locations) > 1 or not args.location:
        # Pull contact email from local.env (or process env). Falls back to
        # empty string → footer just hides the «Contact» link.
        from lib.env import load_local_env
        load_local_env()
        contact_email = os.environ.get("CONTACT_EMAIL", "")

        # Seed-locations on landing: explicit flag wins, otherwise auto-enable
        # for local builds (no --base-url set) and disable for production CI
        # (which always sets --base-url).
        if args.include_seed is None:
            include_seed = (base_url == "")
        else:
            include_seed = args.include_seed

        build_landing(locations, ui, theme, languages, env,
                      repo_url=args.repo_url, base_url=base_url,
                      contact_email=contact_email,
                      german_fuesse=german_fuesse,
                      german_fuesse_references=german_fuesse_refs,
                      include_seed=include_seed)

    generate_assets(theme)
    
    print()
    print(f"✅ Build complete: {SITE_DIR}/")


if __name__ == "__main__":
    main()
