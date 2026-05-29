"""Entity routing — pre-classification rules applied across all V2
seed builders.

Reads `data/v2/entity_routing_rules.yml` (declarative pattern → entity
routing decisions) and applies them in safe-mode: actively re-routes a
coin's `issuing_entity` ONLY when the coin's mint is absent OR carries
`mint_verified: false`. When a rule matches but mint took precedence,
the rule's verdict is still recorded as `_entity_routing_hint` on the
coin — so a curator debugging a non-obvious placement can read the
rule's analysis even on entries the rule didn't actively change.

Public API:
  load_rules() -> list[dict]
      Loads + caches the rules yaml. Idempotent across calls.

  route_entity_with_rules(coin: dict, *, default_entity: str | None) -> tuple[str | None, dict | None]
      Applies all matching rules to a coin. Returns
      (resolved_entity, hint_dict). The hint is None when no rule
      matched; otherwise a structured dict shaped as documented in
      `data/v2/entity_routing_rules.yml` (active / agrees_with_active /
      would_route_to / matched_on / rule_id / reasoning).

Integration pattern (for seed builders):
  ```
  default_ent = classify_mint_to_entity(coin.get('mint'), year=...)
  if default_ent is None:
      default_ent = classify_issuer_to_entity(coin.get('issuer'))
  routed_ent, hint = route_entity_with_rules(coin, default_entity=default_ent)
  coin['issuing_entity'] = routed_ent
  if hint:
      coin['_entity_routing_hint'] = hint
  ```

Test fixtures: see `scripts/lib/test_entity_routing.py`.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RULES_PATH = PROJECT_ROOT / "data" / "v2" / "entity_routing_rules.yml"

# Module-level cache. Loaded lazily on first call to avoid import-time
# YAML parsing for callers that don't actually need the rules.
_CACHED_RULES: list[dict[str, Any]] | None = None


def load_rules(*, force_reload: bool = False) -> list[dict[str, Any]]:
    """Load + cache rules. Pass `force_reload=True` to bypass cache
    (useful for tests that mutate the file)."""
    global _CACHED_RULES
    if _CACHED_RULES is not None and not force_reload:
        return _CACHED_RULES
    if not _RULES_PATH.exists():
        _CACHED_RULES = []
        return _CACHED_RULES
    with _RULES_PATH.open() as f:
        data = yaml.safe_load(f) or {}
    rules = data.get("rules") or []
    if not isinstance(rules, list):
        raise ValueError(
            f"{_RULES_PATH}: top-level 'rules' must be a list, got {type(rules).__name__}"
        )
    # Light schema validation — each rule must have id, match, routes_to.
    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            raise ValueError(f"{_RULES_PATH}: rule {i} is not a dict")
        for required in ("id", "match", "routes_to"):
            if required not in r:
                raise ValueError(
                    f"{_RULES_PATH}: rule {i} ({r.get('id', '?')}) missing required key '{required}'"
                )
    _CACHED_RULES = rules
    return _CACHED_RULES


# ---------------------------------------------------------------------
# Match predicates
# ---------------------------------------------------------------------

def _ci_substring_any(value: Any, patterns: list[str]) -> str | None:
    """Returns the first pattern that case-insensitively matches as a
    substring of `value`. None if no match (or value not a string)."""
    if not isinstance(value, str) or not patterns:
        return None
    haystack = value.lower()
    for p in patterns:
        if not isinstance(p, str):
            continue
        if p.lower() in haystack:
            return p
    return None


def _evaluate_match(rule: dict[str, Any], coin: dict[str, Any]) -> dict[str, Any] | None:
    """Return a dict of matched-field-name → matched-pattern when all
    of the rule's conditions are satisfied; None otherwise.

    Empty conditions inside the rule's `match` block are skipped (so an
    omitted `mint_any` doesn't block a rule that only cares about
    ruler+denom).

    Special OR-semantic: when BOTH `ruler_lineage_any` AND `issuer_any`
    are specified on a rule, the rule fires when EITHER matches. This
    handles real-world data shapes where a coin's ruler field is empty
    but the issuer chip identifies the lineage (or vice versa). When
    only one of the two is specified, that one must match per the
    usual AND semantic.
    """
    match = rule.get("match") or {}
    matched_on: dict[str, Any] = {}

    # ── ruler_lineage_any / issuer_any — OR-coupled lineage match ──
    rl_patterns = match.get("ruler_lineage_any")
    issuer_patterns = match.get("issuer_any")

    ruler_match = None
    if rl_patterns:
        ruler = coin.get("ruler")
        if isinstance(ruler, list):
            ruler = " / ".join(str(r) for r in ruler if r)
        ruler_match = _ci_substring_any(ruler, rl_patterns)

    issuer_match = None
    if issuer_patterns:
        # Various source builders stash issuer differently; try common slots.
        for slot in ("_numista_issuer", "_issuer", "issuer"):
            candidate = coin.get(slot)
            m = _ci_substring_any(candidate, issuer_patterns)
            if m is not None:
                issuer_match = m
                break

    if rl_patterns and issuer_patterns:
        # Both specified → OR-couple: at least one must match.
        if ruler_match is None and issuer_match is None:
            return None
    elif rl_patterns:
        if ruler_match is None:
            return None
    elif issuer_patterns:
        if issuer_match is None:
            return None
    # (neither specified → no lineage constraint, skip)

    if ruler_match is not None:
        matched_on["ruler_lineage"] = ruler_match
    if issuer_match is not None:
        matched_on["issuer"] = issuer_match

    # ── denomination_any ──────────────────────────────────────────
    denom_patterns = match.get("denomination_any")
    if denom_patterns:
        m = _ci_substring_any(coin.get("nominal"), denom_patterns)
        if m is None:
            return None
        matched_on["denomination"] = m

    # ── mint_any — optional ───────────────────────────────────────
    mint_patterns = match.get("mint_any")
    if mint_patterns:
        mint = coin.get("mint")
        if isinstance(mint, list):
            mint = ", ".join(str(m) for m in mint if m)
        m = _ci_substring_any(mint, mint_patterns)
        if m is None:
            return None
        matched_on["mint"] = m

    # ── year_from / year_to — optional ─────────────────────────────
    yf = match.get("year_from")
    yt = match.get("year_to")
    if yf is not None or yt is not None:
        coin_yr = coin.get("year_first")
        if coin_yr is None:
            return None  # year-bounded rule but coin has no year
        coin_yr = int(coin_yr)
        if yf is not None and coin_yr < yf:
            return None
        if yt is not None and coin_yr >= yt:
            return None
        matched_on["year_first"] = coin_yr

    return matched_on


# ---------------------------------------------------------------------
# Routing entry point
# ---------------------------------------------------------------------

def _mint_is_authoritative(coin: dict[str, Any]) -> bool:
    """True when the coin has a mint AND mint_verified is True. This
    is the «safe-mode» pivot — when the mint is authoritative, the
    rule writes a hint but does NOT override the active entity. When
    the mint is absent or unverified, the rule actively re-routes."""
    mint = coin.get("mint")
    if mint is None:
        return False
    if isinstance(mint, list) and not mint:
        return False
    return bool(coin.get("mint_verified"))


def route_entity_with_rules(
    coin: dict[str, Any],
    *,
    default_entity: str | list[str] | None,
) -> tuple[str | list[str] | None, dict[str, Any] | None]:
    """Apply all matching rules to a coin.

    Parameters
    ----------
    coin : dict
        Coin-schema dict. Must carry at minimum the fields the rules
        match on (typically `ruler`, `nominal`, sometimes `mint` /
        `year_first` / issuer slot).
    default_entity : str | list[str] | None
        The entity the caller would assign in absence of any rule —
        typically the result of `classify_mint_to_entity` (or issuer
        fallback when mint was absent). Used as the «active» value
        when no rule actively re-routes.

    Returns
    -------
    (resolved_entity, hint)
        resolved_entity — the entity to put on `coin.issuing_entity`.
            Equal to default_entity when no rule fires actively;
            equal to rule.routes_to when a rule fires in active mode.
        hint — None when no rule matched at all. Otherwise a dict
            with keys:
              rule_id              str
              matched_on           {field: matched-pattern, ...}
              would_route_to       str
              active               bool — true if rule changed entity
              agrees_with_active   bool — only present when active=false;
                                         true if rule.routes_to ==
                                         the active entity
              reasoning            str — short human note
    """
    rules = load_rules()
    if not rules:
        return default_entity, None

    mint_auth = _mint_is_authoritative(coin)
    active_entity = default_entity
    hint: dict[str, Any] | None = None

    for rule in rules:
        matched_on = _evaluate_match(rule, coin)
        if matched_on is None:
            continue
        rule_routes_to = rule["routes_to"]
        rule_id = rule["id"]

        if not mint_auth:
            # Active re-route: rule wins, mint isn't authoritative
            reasoning_parts = []
            for k, v in matched_on.items():
                reasoning_parts.append(f"{k}={v!r}")
            new_hint = {
                "rule_id": rule_id,
                "matched_on": matched_on,
                "would_route_to": rule_routes_to,
                "active": True,
                "reasoning": (
                    f"Rule matched on " + ", ".join(reasoning_parts)
                    + "; mint absent / unverified → rule re-routed."
                ),
            }
            return rule_routes_to, new_hint
        else:
            # Mint is authoritative; record the rule's verdict but don't
            # override. First matching rule's hint wins (deterministic).
            if hint is not None:
                # Already have a hint from an earlier rule; skip.
                continue
            agrees = (rule_routes_to == active_entity) or (
                isinstance(active_entity, list) and rule_routes_to in active_entity
            )
            hint = {
                "rule_id": rule_id,
                "matched_on": matched_on,
                "would_route_to": rule_routes_to,
                "active": False,
                "agrees_with_active": agrees,
                "reasoning": (
                    f"Rule matched but mint is verified — mint took precedence. "
                    f"Rule would route to {rule_routes_to!r}; "
                    f"active entity is {active_entity!r}."
                ),
            }

    return active_entity, hint
