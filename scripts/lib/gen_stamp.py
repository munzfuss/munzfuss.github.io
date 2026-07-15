"""Content-stable `generated_at` — reuse the prior timestamp on a no-op re-run.

Pipeline-transition scripts (`merge_seeds_cross_source.py`,
`absorb_seeds_into_final_v2.py`) stamp `generated_at: <today>` into every file
they (re)write. On a re-flow (merger + absorb) that changes nothing in a given
entity, that unconditional stamp is the ONLY diff — a daily cosmetic churn
across the `seed_unified/` + `classification_decisions/` files that buries the
real changes when a curator runs `git diff data/` (the project's core review
tool). (Investigated 2026-07-15: the finals field-order drift was a one-time
migration; the timestamp bump was the sole genuinely-recurring churn.)

`resolve_generated_at` keeps the timestamp meaningful AND churn-free by
redefining it as «when the content last changed», not «when the script last
ran». When the regenerated payload equals the existing file's payload (both
compared with the timestamp field removed), the existing date is reused;
otherwise today's date is returned.

Safe because `generated_at` is purely informational — no pipeline code branches
on it (verified 2026-07-15: the only reads are self-reads inside the same
emit/render site; nothing downstream keys logic off it).
"""
from datetime import date


def resolve_generated_at(new_payload: dict, existing_doc: dict | None,
                         ts_field: str = "generated_at") -> str:
    """Return the ISO date string to stamp into `new_payload[ts_field]`.

    Reuse `existing_doc[ts_field]` when the two payloads are content-equal with
    `ts_field` stripped from BOTH sides; otherwise return today's ISO date.
    Today is also returned when there is no existing doc, it carries no prior
    timestamp, or the content differs.

    `new_payload` may already carry a placeholder `ts_field` value — it is
    stripped before the comparison, so the placeholder is irrelevant.
    """
    today = date.today().isoformat()
    if not existing_doc:
        return today
    old_ts = existing_doc.get(ts_field)
    if not old_ts:
        return today
    strip_new = {k: v for k, v in new_payload.items() if k != ts_field}
    strip_old = {k: v for k, v in existing_doc.items() if k != ts_field}
    return old_ts if strip_new == strip_old else today
