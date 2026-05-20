"""V2-native seed writer — shared helper for seed builders.

Replaces the V1→V2 indirection that runs every V1 builder through
`seed_v2_regroup.py` to translate location-keyed output into entity-
keyed V2 seed yamls. Each builder calls `write_v2_seed(coins, source)`
directly and the result lands in `data/v2/seed/<source>/<entity>.yml`
ready for the cross-source merger.

Per V2_PIPELINE.md §3.10: when a coin has list-form `issuing_entity`
(joint mint, e.g. `[danish_realm, royal_holstein]` for Altona+Kopenhagen),
the HOME FILE is the alphabetically-first entity. Build assembly's
inverse-index pass surfaces the coin on every consumer page whose
`consumes_entities` intersects with the list.

Per CLAUDE.md «V2 entity-keyed pipeline»: V1 is FROZEN; new builders
write V2 directly. The previous `data/seed/<source>/<location>.yml`
output path is no longer touched by these builders.

Curation preservation: each per-entity write goes through
`lib.seed_merge.merge_seed`, so existing curator-set `fuss`/`phase`/
`issuing_entity`/`note`/`*_verified` flags survive regeneration.
Orphan curated entries (in V2 seed but no longer in the fresh build)
stay verbatim — no silent data loss.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import PROJECT_ROOT  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

V2_SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed"

# ----------------------------------------------------------------------
# Pre-write hygiene: out-of-scope filter + normalisation
# ----------------------------------------------------------------------
import re  # noqa: E402

# Nominal substrings that mark a coin as OUT-OF-SCOPE for the project.
# Per CLAUDE.md «Mission temporal scope» the artifact documents NORTH
# GERMAN + DANISH-NORWEGIAN coinage. Trade coins minted FOR (not BY)
# the Danish Crown — East India Asiatic Piastre etc. — fall outside
# this register even when minted at Kopenhagen. User-confirmed
# 2026-05-20.
_OUT_OF_SCOPE_NOMINAL_TOKENS = (
    "piastre",       # Christian VII East India trade
    "rupee",         # East India Tranquebar
    "fanam",         # East India sub-denomination
    "cash",          # East India sub-denomination
)

# Canonical mint name table — normalises the dozens of orthographic
# variants encountered across sources (English / Danish / Latin
# spellings, country-prefixed ucoin format, modern vs historical
# spellings) to ONE canonical form per physical mint town.
# Project convention per CLAUDE.md i18n policy: German period spelling
# for project canonical (Kopenhagen, Christiania, Glückstadt, Altona).
_MINT_CANONICAL = {
    # Copenhagen variants → Kopenhagen
    "copenhagen": "Kopenhagen",
    "københavn": "Kopenhagen",
    "kjøbenhavn": "Kopenhagen",      # pre-1948 Danish spelling
    "k�benhavn": "Kopenhagen",        # mojibake from iso-8859 source
    "hafnia": "Kopenhagen",           # Latin (Christian IV legends)
    "kopenhagen": "Kopenhagen",
    # Christiania / Oslo (Norge)
    "christiania": "Christiania",
    "oslo": "Christiania",            # pre-1924 Christiania (post 1925 Oslo)
                                       # — project window ends 1914 → Christiania
    # Glückstadt variants
    "glückstadt": "Glückstadt",
    "gluckstadt": "Glückstadt",       # ASCII fallback
    "gl�ckstadt": "Glückstadt",       # mojibake
    # Rendsburg (German canonical for SH)
    "rendsburg": "Rendsburg",
    "rendsborg": "Rendsburg",         # Danish spelling
    # Helsingør
    "helsingør": "Helsingør",
    "helsingor": "Helsingør",
    "helsing�r": "Helsingør",         # mojibake
    "elsinore": "Helsingør",          # English
    "elseneur": "Helsingør",          # French (old auction catalogues)
    # Aarhus / Århus
    "århus": "Århus",
    "aarhus": "Århus",
    # Malmö / Malmø (Scania historical; Swedish for project)
    "malmö": "Malmö",
    "malmø": "Malmö",                 # Danish for the same town
    "malm�": "Malmö",                 # mojibake
    "malmoe": "Malmö",
    # Kongsberg (Norge silver mint)
    "kongsberg": "Kongsberg",
    "konsberg": "Kongsberg",
}

# Country / region prefix tokens that ucoin sometimes prepends
# («Denmark, Copenhagen»). Strip these before canonicalising.
_MINT_COUNTRY_PREFIXES = frozenset({
    "denmark", "norway", "sweden", "germany", "holstein", "schleswig",
    "schleswig-holstein", "lübeck", "hamburg",
})


def _canonicalise_mint(raw):
    """Map an arbitrary mint string (or list) to canonical project
    spelling. Strips country-prefixes, paren tails, applies alias
    map, restores diacritics. Returns scalar (single mint) or sorted
    de-duped list (joint mint). None when input is None / empty."""
    if raw is None:
        return None
    items = raw if isinstance(raw, list) else [raw]
    out_set: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        # Strip paren tail «Altona (FK VS)» → «Altona»
        base = re.sub(r"\s*\([^)]*\)\s*$", "", item).strip()
        if not base:
            continue
        # Split on comma — drop country prefix tokens, canonicalise the
        # rest. «Denmark, Copenhagen» → Kopenhagen.
        for tok in [t.strip() for t in base.split(",") if t.strip()]:
            key = tok.lower()
            if key in _MINT_COUNTRY_PREFIXES:
                continue
            canonical = _MINT_CANONICAL.get(key, tok)
            if canonical not in out_set:
                out_set.append(canonical)
    if not out_set:
        return None
    return out_set[0] if len(out_set) == 1 else sorted(out_set)


# Nominal normalisation table — fixes mojibake + standardises fraction
# typography («1/2» → «½», «1 1/2» → «1½») without altering the
# semantic content. Per CLAUDE.md §i18n the period denomination form
# stays — we only fix encoding artefacts and typographic consistency.
_NOMINAL_MOJIBAKE_FIXES = (
    ("K�benhavn", "København"),
    ("Malm�", "Malmø"),
    ("Gl�ckstadt", "Glückstadt"),
    ("Helsing�r", "Helsingør"),
    ("Sølv�", "Sølv"),
    ("�", ""),  # last-resort drop remaining replacement-char artefacts
)


def _normalise_nominal(raw):
    """Normalise a nominal string: mojibake fix + fraction typography +
    consistent capitalization of the denomination noun. Preserves the
    period-correct numismatic form (no translation), only typographic
    cleanup. Returns None when input is None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # Mojibake repair first — must happen before any case folding so
    # the diacritic-bearing char survives.
    for bad, good in _NOMINAL_MOJIBAKE_FIXES:
        if bad in s:
            s = s.replace(bad, good)
    # Strip trailing year-status markers — «uden år» metadata that
    # accidentally entered the nominal field via parser greed. The
    # year-status belongs in `year_label` (rendered as «u. å.»);
    # nominal should hold ONLY the denomination noun. Patterns
    # observed (Hede pages, mostly Christian IV / Frederik III
    # undated gold strikes):
    #   «1 Portugaløser U.år»     → «1 Portugaløser»
    #   «1/2 Dukat U.år (ca 1648)» → «1/2 Dukat»
    #   «1 Søsling u.år»          → «1 Søsling»
    #   «..., u. år (-32)?»       → «...»  (strip from comma onward)
    # Anchored at end so we don't accidentally strip a denomination
    # named «UR» or similar (none exist in Danish numismatics).
    s = re.sub(
        r"[,\s]+[Uu]\.?\s*[åÅaA]?\.?\s*[Rr]?\.?(?:\s*\((?:[^)]*\)|[^)]*$))?\s*\??$",
        "",
        s,
        flags=re.IGNORECASE,
    ).strip(" ,")
    # Fraction typography: «1 1/2» / «1-1/2» → «1½»; «1/2» → «½»; etc.
    s = re.sub(r"(\d)\s*[\-\s]\s*1/2\b", r"\1½", s)
    s = re.sub(r"(\d)\s*[\-\s]\s*1/4\b", r"\1¼", s)
    s = re.sub(r"(\d)\s*[\-\s]\s*3/4\b", r"\1¾", s)
    s = re.sub(r"\b1/2\b", "½", s)
    s = re.sub(r"\b1/4\b", "¼", s)
    s = re.sub(r"\b3/4\b", "¾", s)
    s = re.sub(r"\b1/3\b", "⅓", s)
    s = re.sub(r"\b2/3\b", "⅔", s)
    s = re.sub(r"\b1/8\b", "⅛", s)
    s = re.sub(r"\b1/16\b", "1/16", s)  # leave higher fractions as-is
    # Capitalize denomination noun after a number. «1 skilling» →
    # «1 Skilling»; «4 mark» → «4 Mark»; «1 dukat» → «1 Dukat».
    # Only first noun, not deep capitalisation.
    s = re.sub(
        r"(\b(?:\d+|½|¼|¾|⅓|⅔|⅛)\s+)([a-zæøåüß])",
        lambda m: m.group(1) + m.group(2).upper(),
        s,
    )
    return s


def _is_out_of_scope_nominal(nominal) -> bool:
    """Return True when the nominal indicates an out-of-scope trade coin
    (East India Piastre / Rupee / Fanam / Cash). User-confirmed
    2026-05-20: these coins were minted BY the Danish Crown FOR Asian
    markets, not for the European-realm coinage system the artifact
    documents — exclude from every seed regardless of mint."""
    if not nominal:
        return False
    n = str(nominal).lower()
    return any(tok in n for tok in _OUT_OF_SCOPE_NOMINAL_TOKENS)


def _apply_pre_write_hygiene(coins: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Run mint + nominal normalisation in-place and filter out coins
    whose nominal puts them out-of-scope. Returns (kept, stats)."""
    stats = {
        "mint_normalised": 0,
        "nominal_normalised": 0,
        "out_of_scope_filtered": 0,
    }
    kept: list[dict] = []
    for c in coins:
        if not isinstance(c, dict):
            kept.append(c)
            continue
        nominal = c.get("nominal")
        if _is_out_of_scope_nominal(nominal):
            stats["out_of_scope_filtered"] += 1
            continue
        new_nom = _normalise_nominal(nominal)
        if new_nom is not None and new_nom != nominal:
            c["nominal"] = new_nom
            stats["nominal_normalised"] += 1
        mint = c.get("mint")
        new_mint = _canonicalise_mint(mint)
        if new_mint != mint and not (new_mint is None and mint in (None, "")):
            c["mint"] = new_mint
            stats["mint_normalised"] += 1
        kept.append(c)
    return kept, stats


def _home_entity(coin: dict) -> str | None:
    """Return the home-file entity for a coin.

    - Scalar `issuing_entity`: that entity.
    - List-form `issuing_entity` (joint mint): alphabetically-first
      entity, per V2_PIPELINE.md §3.10.
    - Missing / empty: None (caller routes to `_unclassified.yml`).
    """
    ie = coin.get("issuing_entity")
    if isinstance(ie, str) and ie:
        return ie
    if isinstance(ie, list) and ie:
        return sorted(str(e) for e in ie if e)[0]
    return None


def write_v2_seed(
    coins: list[dict],
    source_name: str,
    scope_note: str,
    *,
    source_label: str | None = None,
    dry_run: bool = False,
    no_merge: bool = False,
    extra_top_level: dict | None = None,
) -> dict:
    """Group `coins` by `issuing_entity` → write
    `data/v2/seed/<source_name>/<entity>.yml` per entity.

    Parameters
    ----------
    coins : list of Coin-schema dicts. Each must carry `issuing_entity`
        (scalar or list-form). Coins with missing/empty issuing_entity
        route to `_unclassified.yml` for curator review.
    source_name : subdirectory under `data/v2/seed/` to write into.
        E.g. "hede" → `data/v2/seed/hede/`.
    scope_note : human-readable string describing the source + scope.
        Emitted as the `scope_note` header in every output yaml.
    source_label : optional value for the `source` header (defaults
        to source_name).
    dry_run : if True, only logs stats and skips writes.
    no_merge : if True, wholesale-overwrites existing seed yamls
        without `merge_seed` curation preservation. Destructive — use
        only for verification or fresh-build scenarios.
    extra_top_level : optional dict of extra header keys to merge into
        every output yaml's top level (e.g. {"scope_year_from": 1514}).

    Returns
    -------
    dict with summary stats:
      {
        "entities_written": [...],
        "per_entity": {entity: {merged_existing, added_new, orphan_curated, total}},
        "unclassified_count": N,
      }
    """
    # Pre-write hygiene: normalise mints + nominals, drop out-of-scope
    # trade coins (Piastre / Rupee / Fanam / Cash). Runs in-place so
    # all builders benefit uniformly. Returns the kept list +
    # per-source counts of how many entries were touched.
    coins, hygiene_stats = _apply_pre_write_hygiene(list(coins))
    if any(hygiene_stats.values()):
        print(f"\n[{source_name}] pre-write hygiene: "
              f"out_of_scope_filtered={hygiene_stats['out_of_scope_filtered']}, "
              f"nominal_normalised={hygiene_stats['nominal_normalised']}, "
              f"mint_normalised={hygiene_stats['mint_normalised']}")

    by_entity: dict[str, list[dict]] = defaultdict(list)
    unclassified: list[dict] = []
    for c in coins:
        home = _home_entity(c)
        if home is None:
            unclassified.append(c)
            continue
        by_entity[home].append(c)

    src_dir = V2_SEED_ROOT / source_name
    src_dir.mkdir(parents=True, exist_ok=True)

    # Cross-entity dup-purge: when a fresh build re-classifies a coin
    # from entity A to entity B (e.g. mint reading refined → previously
    # `royal_holstein` now `gottorp_duchy`), the OLD entry in A's seed
    # file must be removed, else the same id appears in two files and
    # the cross-source merger sees a phantom duplicate. Walk every
    # existing seed file under this source, collect ids that this fresh
    # build now places under a DIFFERENT entity, drop them from their
    # stale home.
    fresh_id_to_entity: dict[str, str] = {}
    for entity, ents in by_entity.items():
        for c in ents:
            cid = c.get("id")
            if cid:
                fresh_id_to_entity[cid] = entity
    purged_per_file: dict[str, int] = {}
    if not dry_run and not no_merge:
        import ruamel.yaml as _ruyaml
        purge_yaml = _ruyaml.YAML(typ="rt")
        purge_yaml.preserve_quotes = True
        purge_yaml.width = 200
        purge_yaml.indent(mapping=2, sequence=4, offset=2)
        for existing_path in sorted(src_dir.glob("*.yml")):
            stale_entity_name = existing_path.stem
            if stale_entity_name == "_unclassified":
                # _unclassified entries that fresh build now classifies
                # to a real entity must also be removed from the bucket.
                pass
            with existing_path.open() as f:
                existing_doc = purge_yaml.load(f)
            if not isinstance(existing_doc, dict):
                continue
            existing_coins = existing_doc.get("coins") or []
            kept = []
            purged = 0
            for c in existing_coins:
                if not isinstance(c, dict):
                    kept.append(c)
                    continue
                cid = c.get("id")
                if cid and cid in fresh_id_to_entity:
                    new_entity = fresh_id_to_entity[cid]
                    if new_entity != stale_entity_name:
                        purged += 1
                        continue
                kept.append(c)
            if purged:
                existing_doc["coins"] = kept
                with existing_path.open("w") as f:
                    purge_yaml.dump(existing_doc, f)
                purged_per_file[existing_path.name] = purged

    stats = {
        "entities_written": [],
        "per_entity": {},
        "unclassified_count": len(unclassified),
        "cross_entity_purged": sum(purged_per_file.values()),
    }

    if purged_per_file:
        print(f"\n[{source_name}] cross-entity dup-purge: "
              f"{sum(purged_per_file.values())} stale entries removed "
              f"from {len(purged_per_file)} file(s)")
        for fname, n in sorted(purged_per_file.items()):
            print(f"  - {fname}: {n} entries dropped (re-classified)")
    print(f"\n[{source_name}] grouping → {len(by_entity)} entities, "
          f"{len(unclassified)} unclassified")
    for entity in sorted(by_entity.keys()):
        ents = by_entity[entity]
        # Sort stable for clean diffs
        ents.sort(key=lambda e: (e.get("year_first") or 9999, e.get("id") or ""))
        out_path = src_dir / f"{entity}.yml"
        merge_stats = {"merged_existing": 0, "added_new": len(ents), "orphan_curated": 0}
        if not dry_run and not no_merge:
            ents, merge_stats = merge_seed(ents, out_path)

        print(f"  [{entity}] {len(ents)} entries  "
              f"(merged={merge_stats['merged_existing']}, "
              f"added={merge_stats['added_new']}, "
              f"orphan_curated={merge_stats['orphan_curated']})")

        if dry_run:
            stats["per_entity"][entity] = {**merge_stats, "total": len(ents)}
            continue

        yaml = ruamel.yaml.YAML(typ="rt")
        yaml.preserve_quotes = True
        yaml.width = 200
        yaml.indent(mapping=2, sequence=4, offset=2)
        out = {
            "status": "seed",
            "source": source_label or source_name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entity": entity,
            "scope_note": scope_note,
        }
        if extra_top_level:
            for k, v in extra_top_level.items():
                if k not in out:
                    out[k] = v
        out["coins"] = ents
        with out_path.open("w") as f:
            yaml.dump(out, f)
        stats["entities_written"].append(entity)
        stats["per_entity"][entity] = {**merge_stats, "total": len(ents)}

    # Unclassified bucket — keep coins that the entity classifier failed
    # to resolve so curators can triage them without losing source data.
    if unclassified:
        unclass_path = src_dir / "_unclassified.yml"
        unclassified.sort(key=lambda e: (e.get("year_first") or 9999, e.get("id") or ""))
        merge_stats = {"merged_existing": 0, "added_new": len(unclassified), "orphan_curated": 0}
        if not dry_run and not no_merge:
            unclassified, merge_stats = merge_seed(unclassified, unclass_path)
        print(f"  [_unclassified] {len(unclassified)} entries")
        if not dry_run:
            yaml = ruamel.yaml.YAML(typ="rt")
            yaml.preserve_quotes = True
            yaml.width = 200
            yaml.indent(mapping=2, sequence=4, offset=2)
            out = {
                "status": "seed",
                "source": source_label or source_name,
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "entity": "_unclassified",
                "scope_note": (
                    f"{scope_note} — entries the mint→entity classifier "
                    "could not resolve. Curator triage required: assign "
                    "`issuing_entity` per coin, then re-run the builder."
                ),
                "coins": unclassified,
            }
            with unclass_path.open("w") as f:
                yaml.dump(out, f)
        stats["per_entity"]["_unclassified"] = {**merge_stats, "total": len(unclassified)}

    # Summary
    by_realm = Counter(e for entity, ents in by_entity.items() for e in [entity] for _ in ents)
    print(f"\n[{source_name}] wrote V2 seed: "
          f"{len(stats['entities_written'])} entity file(s)"
          f"{', 1 unclassified file' if unclassified else ''}")
    return stats
