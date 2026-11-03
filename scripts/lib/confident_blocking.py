"""Candidate blocking for loops that keep only `match_pair(...) == "confident"`.

Absorb compares one coin against every final of the entity and keeps the
finals `match_pair` calls `confident` — 1.3 M calls on a full run, most of
them against finals that share nothing with the coin (2026-11-03: the
self-foundation fold alone was ~1 min of a ~2.5 min absorb). This index
returns, in the original order, only the finals that CAN be confident; the
caller still runs `match_pair` on each, so the verdicts are the same.

SOUNDNESS. `_match_pair_core` returns `confident` on three paths only:
  * the §9a multi-specimen promotion — needs `catalog` and `ruler` True;
  * `primary_true >= 3` of {metal, nominal, catalog, ruler} — so at least one
    of `catalog`, `ruler` is True;
  * catalogue + nominal + ruler agreeing — needs `catalog` True.
The `match_pair` wrapper (the evidence gate) only ever DEMOTES a confident.
So every confident pair has `ruler` True or `catalog` True, and:
  * `ruler` True ⇔ both normalised rulers (D33-inferred when `reign_index`
    is given and the ruler is empty) are equal;
  * `catalog` True ⇔ `_catalog_chain_consistent` is `agree` — which needs at
    least one shared scoped key whose values agree by one of its rules
    (case-folded equality, numeric core, bare-vs-dot parent, Lange / Schou /
    Sieg number sets) — or `_others_agree` finds a register both records give
    with an equal value or overlapping printed range.
Each of those agreements is indexed below as a shared token, so a final that
shares no token with the coin cannot be confident and is skipped. Any coin
the tokeniser cannot read is a wildcard and is always compared.

If `match_pair` gains a new `confident` path that rests on neither `ruler`
nor `catalog`, this proof breaks: extend the tokens, or run with
`CONFIDENT_BLOCKING=0` (full scan) and diff. `CONFIDENT_BLOCKING_VERIFY=1`
runs both and raises on the first coin whose confident set differs.
"""
from __future__ import annotations

import os
import re
from collections import defaultdict

ENABLED = os.environ.get("CONFIDENT_BLOCKING", "1") != "0"
VERIFY = os.environ.get("CONFIDENT_BLOCKING_VERIFY") == "1"

# The two value rules nested in `_catalog_chain_consistent`.
_CORE_RE = re.compile(r"^(\d+(?:\.\d+)?)[A-Za-z]{1,2}$")
_DOTNUM_RE = re.compile(r"^(\d+)\.\d+$")
_OTHERS_SPAN_MAX = 5000      # a wider printed range is a wildcard for its register


def _mg():
    import maintenance.merge_seeds_cross_source as mg
    return mg


def _tokens(coin: dict, entity_id, reign_index) -> tuple[set, set, set]:
    """(tokens to post and query, others registers posted as «any value»,
    others registers whose own range is too wide to enumerate)."""
    mg = _mg()
    toks: set = set()
    ra = mg._normalise_ruler(coin.get("ruler"))
    if reign_index and not ra:
        ra = mg._infer_ruler(coin, reign_index) or ra
    if ra:
        hash(ra)
        toks.add(("r", ra))
    for k, va in mg._catalog_refs(coin, entity_id).items():
        for x in str(va).split("|"):
            toks.add(("c", k, x.lower()))
            s = x.strip()
            m = _CORE_RE.match(s)
            toks.add(("c", k, m.group(1) if m else s))
            p = _DOTNUM_RE.match(s)
            if p:
                toks.add(("c", k, p.group(1)))
        for n in mg._lange_numbers(va):
            toks.add(("L", k, n))
    regs: set = set()
    wide: set = set()
    for reg, vals in mg._others_registers(coin).items():
        regs.add(reg)
        for v in vals:
            toks.add(("o", reg, "=" + v))
            sp = mg._span(v)
            if sp:
                if sp[1] - sp[0] > _OTHERS_SPAN_MAX:
                    wide.add(reg)
                else:
                    toks.update(("o", reg, i) for i in range(sp[0], sp[1] + 1))
    return toks, regs, wide


class ConfidentBlocker:
    """Index over `coins` (the right-hand side of `match_pair(coin, other)`).

    Build it right before the loop, from the coins as they stand then: the
    tokens are read once and the coins must not change while it is used."""

    def __init__(self, coins, entity_id, reign_index=None):
        self.entity_id = entity_id
        self.reign_index = reign_index
        self.n = len(coins)
        self.post: dict = defaultdict(list)
        self.wild: list[int] = []
        for i, c in enumerate(coins):
            try:
                toks, regs, wide = _tokens(c, entity_id, reign_index)
            except Exception:
                self.wild.append(i)
                continue
            for t in toks:
                self.post[t].append(i)
            for reg in regs:
                self.post[("o", reg, "*any")].append(i)
            for reg in wide:
                self.post[("o", reg, "*wide")].append(i)

    def indices(self, coin) -> list[int]:
        """Ascending indices of the coins that can be confident with `coin`."""
        try:
            toks, regs, wide = _tokens(coin, self.entity_id, self.reign_index)
        except Exception:
            return list(range(self.n))
        hit = set(self.wild)
        for t in toks:
            hit.update(self.post.get(t, ()))
        for reg in regs:
            hit.update(self.post.get(("o", reg, "*wide"), ()))
        for reg in wide:
            hit.update(self.post.get(("o", reg, "*any"), ()))
        return sorted(hit)


def select(blocker: ConfidentBlocker | None, coin, seq: list) -> list:
    """`seq` (the list the blocker was built on), reduced to the items that
    can be confident with `coin`, in their original order. With blocking off
    (`CONFIDENT_BLOCKING=0`) or no blocker, `seq` itself."""
    if blocker is None or not ENABLED:
        return seq
    return [seq[i] for i in blocker.indices(coin)]


def verify(blocker: ConfidentBlocker | None, coin, seq: list, is_confident) -> None:
    """With `CONFIDENT_BLOCKING_VERIFY=1`: raise if a confident item of `seq`
    is missing from `select(...)`. `is_confident(item)` is the caller's own
    test, so the check covers exactly the loop it guards."""
    if not VERIFY or blocker is None:
        return
    kept = {id(x) for x in select(blocker, coin, seq)}
    missed = [x for x in seq if id(x) not in kept and is_confident(x)]
    if missed:
        raise AssertionError(
            f"confident_blocking: {coin.get('id')!r} is confident with "
            f"{[m.get('id') for m in missed]} but they share no token")
