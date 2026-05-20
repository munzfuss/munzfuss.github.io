#!/usr/bin/env bash
# V2 pipeline runner — chains Phase 3.2 → 4 absorb → 4 classify → 6 relink.
#
# Run after a harvest cycle (new cache entries) OR after curator edits to
# `data/v2/merge_decisions/` / `data/v2/classification_decisions/` to regenerate
# V2 final entries.
#
# Per `docs/ARCHITECTURE.md` §«V2 entity-keyed pipeline» + `docs/V2_PIPELINE.md`.
#
# Per-source seed builders (`build_<src>_<loc>_seed.py`, V2-native via
# `lib.v2_seed_writer.write_v2_seed`) are NOT chained here — invoke them
# separately per source after harvest brings new cache entries.
#
# Usage:
#   scripts/run_v2_pipeline.sh              # dry-run all phases (no mutations)
#   scripts/run_v2_pipeline.sh --apply      # mutate data/v2/* + build site
#   scripts/run_v2_pipeline.sh --apply --skip-build   # mutate but no render
#
# All phases idempotent — re-running on already-canonical state is a no-op.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PROJECT_ROOT}/.venv/bin/python"
APPLY=""
SKIP_BUILD=""

for arg in "$@"; do
    case "$arg" in
        --apply) APPLY="--apply" ;;
        --skip-build) SKIP_BUILD=1 ;;
        -h|--help)
            sed -n '2,18p' "${BASH_SOURCE[0]}"
            exit 0
            ;;
        *)
            echo "unknown flag: $arg" >&2
            exit 1
            ;;
    esac
done

cd "$PROJECT_ROOT"

if [[ -z "$APPLY" ]]; then
    echo "═══ V2 pipeline — DRY-RUN (no mutations) ═══"
    echo "Use --apply to actually mutate data/v2/* files."
    echo
fi

echo "──[1/5] Phase 3.2: merge_seeds_cross_source ──────────────────────"
"$PY" scripts/maintenance/merge_seeds_cross_source.py ${APPLY:---dry-run}

echo
echo "──[2/5] Phase 4 absorb: absorb_seeds_into_final_v2 ───────────────"
"$PY" scripts/maintenance/absorb_seeds_into_final_v2.py ${APPLY:---dry-run}

echo
echo "──[3/5] Phase 4 classify: auto_classify_seed_unsorted ────────────"
# auto_classify uses --apply (no --dry-run flag); default is dry-run.
"$PY" scripts/maintenance/auto_classify_seed_unsorted.py $APPLY

echo
echo "──[4/5] Phase 6 relink: relink_promoted_v2 ───────────────────────"
"$PY" scripts/maintenance/relink_promoted_v2.py ${APPLY:---dry-run}

echo
if [[ -n "$SKIP_BUILD" ]]; then
    echo "──[5/5] Build SKIPPED per --skip-build ───────────────────────────"
elif [[ -n "$APPLY" ]]; then
    echo "──[5/5] Build: scripts/build.py ──────────────────────────────────"
    "$PY" scripts/build.py 2>&1 | tail -8
else
    echo "──[5/5] Build SKIPPED — dry-run mode (re-run with --apply) ───────"
fi

echo
echo "═══ V2 pipeline ${APPLY:+APPLIED}${APPLY:-DRY-RUN COMPLETE} ═══"
