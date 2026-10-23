#!/bin/bash
# The final-forming chain for ONE location page's entities, one process per
# step (indices built once). Faster than the full runner when a change only
# matters to one page; the full `run_v2_pipeline.sh` stays the canonical run
# before a commit of every final.
#
#   scripts/run_v2_page.sh denmark            # dry-run
#   scripts/run_v2_page.sh denmark --apply    # one pass
#   scripts/run_v2_page.sh denmark --apply --twice   # + fixed-point check
#
# thin_final_weight_lists and relink_promoted_v2 have no entity scope and run
# over every final; both are idempotent. Honours ABSORB_NO_SELF_UNION.
set -e
LOC="$1"; shift || true
APPLY=""; TWICE=""
for a in "$@"; do
  case "$a" in
    --apply) APPLY="--apply" ;;
    --twice) TWICE=1 ;;
    *) echo "unknown option $a"; exit 2 ;;
  esac
done
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=.venv/bin/python
ENTS=$($PY -c "
import yaml
ce = yaml.safe_load(open('data/v2/locations/$LOC.yml'))['consumes_entities']
print(','.join(e['entity'] if isinstance(e, dict) else e for e in ce))")
[ -n "$ENTS" ] || { echo "no consumes_entities for $LOC"; exit 2; }
echo "entities: $ENTS"
run_pass() {
  echo "──[1/5] merge";    $PY scripts/maintenance/merge_seeds_cross_source.py --entity "$ENTS" ${APPLY:---dry-run}
  echo "──[2/5] absorb";   $PY scripts/maintenance/absorb_seeds_into_final_v2.py --entity "$ENTS" ${APPLY:---dry-run}
  echo "──[3/5] thin";     $PY scripts/maintenance/thin_final_weight_lists.py ${APPLY:---dry-run}
  echo "──[4/5] classify"; $PY scripts/maintenance/auto_classify_seed_unsorted.py --entity "$ENTS" $APPLY
  echo "──[5/5] relink";   $PY scripts/maintenance/relink_promoted_v2.py ${APPLY:---dry-run}
}
run_pass
if [ -n "$TWICE" ] && [ -n "$APPLY" ]; then
  TMP=$(mktemp -d)
  cp -R data/v2/final/. "$TMP/"
  run_pass
  if diff -rq "$TMP" data/v2/final > /dev/null; then echo "FIXED POINT"; else echo "NOT A FIXED POINT:"; diff -rq "$TMP" data/v2/final | head; fi
  rm -rf "$TMP"
fi
