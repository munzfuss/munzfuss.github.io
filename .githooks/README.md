# Git hooks

Project-tracked git hooks (committed to the repo, opt-in per clone).

## Install

```bash
./scripts/install_hooks.sh
```

This is one-time per clone — it runs `git config core.hooksPath
.githooks` which tells git to look here for hooks instead of the
default `.git/hooks/`.

## Bypass for a single commit

```bash
git commit --no-verify
```

Use this only when you know what the hook would flag and you've decided
to accept it (e.g. WIP commit on a feature branch). Don't make it a
habit on `main`.

## Hooks installed

### `pre-commit`

Seven checks before allowing the commit. Each runs only when the commit
actually touches files it cares about, so most commits run two or three.

| # | Check | Severity | Triggers on |
|---|---|---|---|
| 1 | `scripts/build.py --validate-only` | **BLOCK on failure** | any change to `data/`, `templates/`, `scripts/lib/`, `scripts/build.py`, `config/theme.yml`, `assets/` |
| 2 | `scripts/audit_prose.py --staged` | **BLOCK on errors**, advisory on warnings | any change to `data/*.yml` |
| 3 | `scripts/audit_i18n.py` | advisory | any change to `data/*.yml` |
| 4 | `scripts/audit_v2.py --quick` (I1/I2/I3/I5/I8) | **BLOCK on failure** | `data/v2/`, the V2 maintenance scripts, `scripts/build.py`, `scripts/lib/{schema,v2_resolver,v2_entity_classify,seed_merge}.py` — per V2_DECISIONS D26 |
| 5 | `scripts/maintenance/validate_decisions.py` + `--check-members` | **BLOCK on failure** | `data/v2/merge_decisions/*.yml` |
| 6 | `scripts/maintenance/audit_lost_citations.py` | **BLOCK on failure** | `data/v2/final/*.yml` |
| 7 | `scripts/maintenance/verify_reflow.py` | **BLOCK on losses** | `data/v2/final/*.yml` |
| 8 | `scripts/maintenance/rebucket_seeds.py --check` | **BLOCK on drift** | `data/v2/seed/*.yml` |

Seven of the eight block. A commit that breaks schema validation,
violates a V2 invariant, leaves a merge decision whose members do not
resolve, drops a citation a final entry carried, loses a coin or a
value the baseline had, or leaves a seed entry in a file other than its
`_home_entity(issuing_entity)`, refuses to land. Checks 6, 7 and 8 exist
because each caught a specific real defect — see «What this protects
against».

### Prose lint — promoted 2026-09-03

TODO §W took the corpus from 530 prose errors to 0, so check 2 now
blocks on the ERROR tier. What blocks is narrow on purpose: the
error-tier rules mark project-internal text that reached a
reader-facing field (§0z / §0a — a `CLAUDE.md` reference, a
`docs/TODO` section id, a YAML file or schema field name, «in unserem
Datensatz») or a fabricated non-word (§2a). None of those has a
legitimate use, which is what makes them safe to block on.

**WARNINGs will never be promoted**, and that is a rule rather than a
backlog. All of §2 lives in the warning tier, and §2 tier 3 is house
style — the rule's own wording says a modern form in our own prose is
«a style blemish, never a factual error, and … never grounds to block
a commit». A style preference that refuses commits teaches people to
pass `--no-verify`, which costs more than the blemish.

If an error-tier hit is wrong, the fix is to tighten the rule in
`scripts/audit_prose.py` — the linter has no per-line suppression, on
purpose. `tests/test_prose_tier1_source_form.py` pins the boundaries
that were measured rather than guessed (verbatim quotes, URLs, named
instruments, Danish forms, source-attributed hedges).

Check 3 (i18n) stays advisory pending the §X cleanup.

## Docs-only commits

A commit touching only `docs/**`, `README.md`, or `CLAUDE.md` skips
the build check entirely, and every other check skips too — 2 and 3
need a staged `data/*.yml`, 4 a V2 path, 5 a merge decision, 6 and 7 a
staged final. Net effect: docs-only commits run the hook in < 1 s.

## What this protects against

The two failure modes the hook has caught in real sessions:

- The **ruamel.yaml indent-flatten** trap (May 2026). A maintenance
  script re-dumped a location yaml and silently flattened all
  block-style coin entries from 2-space to 0-column indent. Build
  validation catches the structural break immediately; without the
  hook the broken file would have committed cleanly and crashed
  CI on push.

- **Schema regressions** introduced when adding new fields to a
  Pydantic model without updating the data — the data side passes
  validation pre-change, fails post-change, hook surfaces it before
  the commit is recorded.
