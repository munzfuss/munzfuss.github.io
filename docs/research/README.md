# docs/research/

Topical research notes — depth-first investigations on specific
coins, periods, or analytical questions that span multiple sessions
and don't fit the other doc slots.

## What lives here

Each file is a **standalone research dossier** on one subject. Captures:

- All evidence assembled (verbatim quotes, source URLs, cache
  references, our internal data inventory).
- Computed metrics (Δ-from-Soll, tariff vs metal calculations, etc.).
- Pattern comparisons with adjacent issues.
- Classification analysis with alternative proposals.
- Open decisions / pending verdicts.

## How it differs from other doc surfaces

| Surface | Purpose | Mutability |
|---|---|---|
| `docs/research/<topic>.md` | **Depth-first dossier on one subject** | Append-only as research advances; closed when the subject is fully resolved into data + TODO Done entries |
| `docs/notes/YYYY-MM-DD.md` | Day-level session journal | Immutable per-day |
| `docs/SOURCES.md` §13 | Short per-source quirks log | Append-only entries |
| `docs/DECISIONS.md` | ADR-style rationale for non-obvious choices | Append-only |
| `docs/TODO.md` | Open work items + Done log | Items move Open → Done |

Research notes are **substrate** — the place where evidence is
collected before it gets distilled into a TODO decision, an ADR, a
SOURCES quirk, or rendered coin-table prose. Once a research subject
is fully resolved (decision made, coins reclassified, references
filed), the dossier stays as the audit trail of what was considered
and why.

## When to create a new dossier

Spawn one when:

- A pending decision (typically a 🟡 TODO entry) accumulates evidence
  that doesn't fit in a single TODO entry body without bloating it.
- Multiple external sources need to be assembled, cross-quoted, and
  weighed before the decision can land.
- The analytical reasoning chain runs more than a few paragraphs and
  is worth preserving as the canonical answer to «why did we decide
  X for this subject?».

If the subject is a one-line decision with one source → ADR in
`DECISIONS.md` is enough. If it's a source quirk → `SOURCES.md §13`.
If it's a single-line audit task → keep in TODO. Research dossiers
are for the cases where the evidence + analysis is itself a
deliverable.

## File naming

`<topic_slug>.md` — descriptive snake_case identifier. Examples:

- `daler_klippe_1604.md` — Christian IV's 1604 gold tariff Klippen
- `kronemont_1618_tariff.md` (hypothetical) — Krone-Mønt tariff history
- `glueckstadt_9_fuss_continuation.md` (hypothetical) — Glückstadt's
  retention of the 9-Fuß standard after 1622

No date in the filename — research notes are subject-keyed, not
date-keyed (unlike `docs/notes/YYYY-MM-DD.md`).

## Closure / lifecycle

When the subject is fully resolved:

- The dossier stays — it remains the audit trail.
- Add a closing section at the end documenting how the question was
  resolved (which Fuß category was chosen, which TODO entry closed
  the work, etc.) with the closing commit SHA.
- Cross-references from the relevant TODO Done entry / ADR back to
  the dossier so future readers can find the full reasoning.

The dossier does NOT get moved to `docs/archive/` — it stays at
`docs/research/` indefinitely as live reference for «what did we
already research on this topic».
