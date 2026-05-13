# Daily notes archive

Immutable per-day session journal. One file per day, named
`YYYY-MM-DD.md` (ISO date). Once a day's note is committed, it
should not be edited — additions go in the next day's file.

## Purpose

Capture the day's **insights, observations, and analytical
reasoning** that don't fit anywhere else in the doc tree. The
companion files cover their own slices; this is what's left.

| File | Captures | Mutability |
|---|---|---|
| `CLAUDE.md` | immutable rules, project conventions | append-only over time |
| `docs/PLAYBOOKS.md` | executable procedures (PB-N) | append-only |
| `docs/DECISIONS.md` | rationale for non-obvious choices | append-only |
| `docs/SOURCES.md` §13 | dated quirks per source | append-only |
| `docs/TODO.md` | long-term audit items + closure notes | items move Open → Done |
| **`docs/handoff.md`** | **forward-looking session state** | **REWRITTEN each session** |
| **`docs/notes/YYYY-MM-DD.md`** | **the day's reasoning + insights** | **immutable archive** |

The crucial pairing is **handoff ↔ notes**:

- `handoff.md` is forward-looking and gets rewritten — at any moment
  it reflects «what does the NEXT session need to know to pick up
  cold?». Yesterday's open threads get pruned once they're resolved
  or stale.
- `docs/notes/YYYY-MM-DD.md` is backward-looking and immutable. When
  yesterday's pending verification gets resolved today, the
  handoff.md row goes away — but the original reasoning of «why was
  this pending? what did we examine? what's the verdict-watching
  for?» stays in yesterday's note, forever findable.

Without daily notes, that reasoning lives only in chat history
which gets compacted away after a session or two.

## What goes in a daily note

- **Session topic.** A one-line subject (the chapter title would suit).
- **What happened.** High-level prose — not commit-by-commit (the git
  log does that) but «what was the day's actual project-work
  arc?». A paragraph or two.
- **Insights / observations.** Bullet points or prose — things
  worth preserving that aren't strong enough yet for TODO /
  DECISIONS / §13. Hunches, half-formed theories, unexpected
  source behaviours, performance numbers, error rates.
- **Open threads at session end.** Forward-pointers. These get
  cross-posted to `handoff.md` for the next session, but archived
  here so we still have them after handoff is rewritten.
- **References.** Commits, TODO §X added/closed, DECISIONS entries
  logged, SOURCES.md §13.Y additions, PLAYBOOKS PB-N additions.

## What does NOT go in a daily note

- Commit messages (git log is the source of truth).
- Rule additions (CLAUDE.md is the source of truth; cite the §N
  here, don't reproduce the rule).
- Per-source quirks that meet the > 15-min threshold — those go
  in `docs/SOURCES.md` §13 (cite the §13.X entry from here).
- Decisions whose rationale is general-purpose — those go in
  `docs/DECISIONS.md` (cite the YYYY-MM-DD entry from here).

The daily note links INTO those files; it does not duplicate their
content.

## Operational rules

- **One file per day.** If a day has no project-work activity, no
  file. Empty files are forbidden.
- **Immutable after commit.** Edits to a past day's note are
  forbidden except for fixing typos (caught immediately) or adding
  cross-refs to entries that were filed later. Edits that revise
  the analytical narrative go in a NEW day's note that references
  the original.
- **Auto mode + session lifecycle.** Per PLAYBOOKS PB-8 «Session
  end», updating today's note is part of the session-end ritual.
  If the session didn't touch project-work, no note needed.

## Discovery

```bash
ls docs/notes/                  # all dated notes
grep -l "<keyword>" docs/notes/ # find notes mentioning a topic
git log -- docs/notes/          # creation order
```

Notes are searchable by date OR by content. For a quick scan of
«what was happening around date X», open `docs/notes/X.md`.
