#!/usr/bin/env bash
# scripts/install_hooks.sh — point git at the project's hooks directory.
#
# Run once per clone. Idempotent; safe to run again.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit 2>/dev/null || true

# The harvest submodule carries its own guard (research originals — PDF,
# ALTO, scans — never enter munzfuss-harvest; they live in the research
# library, see scripts/library/library.py).
if [ -f scripts/cache/.githooks/pre-commit ]; then
  git -C scripts/cache config core.hooksPath .githooks
  chmod +x scripts/cache/.githooks/pre-commit 2>/dev/null || true
  echo "✓ harvest submodule hooks enabled (blocks PDF / ALTO / scans / files > 20 MB)"
fi

echo "✓ git hooks enabled (core.hooksPath = .githooks)"
echo "  - pre-commit: build validate (block) + prose/i18n lint (advisory)"
echo
echo "Bypass for a single commit: git commit --no-verify"
echo "See .githooks/README.md for details."
