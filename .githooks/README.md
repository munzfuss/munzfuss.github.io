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

Three checks before allowing the commit:

| # | Check | Severity | Triggers on |
|---|---|---|---|
| 1 | `scripts/build.py --validate-only` | **BLOCK on failure** | any change to `data/`, `templates/`, `scripts/lib/`, `scripts/build.py`, `config/theme.yml`, `assets/` |
| 2 | `scripts/audit_prose.py --staged` | advisory | any change to `data/*.yml` |
| 3 | `scripts/audit_i18n.py` | advisory | any change to `data/*.yml` |

The build check is the hard block — a commit that breaks schema
validation, cross-reference resolution, or YAML duplicate-key
detection refuses to land.

The two lint checks are **advisory** while the project carries its
baseline of pre-existing prose / i18n violations (cleanup scoped
under TODO §W + §X). Once those clear, the lint checks can be
promoted to hard-block — change `set -uo pipefail` to `set -euo
pipefail` and remove the `|| true` fallbacks in the hook.

## Docs-only commits

A commit touching only `docs/**`, `README.md`, or `CLAUDE.md` skips
the build check entirely. The two lint checks also skip unless any
`data/*.yml` is staged. Net effect: docs-only commits run the
hook in < 1 s.

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
