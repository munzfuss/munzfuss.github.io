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
# over every final; both are idempotent. Honours ABSORB_NO_SELF_UNION (rebuild
# every final) and ABSORB_REBUILD_FUSS / data/v2/_rebuild_scope.yml (rebuild
# the finals of those Fuß only).
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
# Hash of every derived file a step can write; on the second pass of --twice
# each step reports which of them it changed, so the step that really needs
# a second run can be told from the ones that only repeat themselves.
snap() {
  $PY - <<'EOF'
import hashlib, pathlib
for d in ("final", "seed_unified", "classification_decisions", "class_registry", "seed"):
    for p in sorted(pathlib.Path("data/v2", d).rglob("*.yml")):
        print(hashlib.md5(p.read_bytes()).hexdigest(), p)
EOF
}
PASS=1
step() {
  local label="$1"; shift
  echo "──$label"
  local before="" t0 t1
  [ "$PASS" = 2 ] && before=$(snap)
  t0=$(date +%s)
  "$@"
  t1=$(date +%s)
  if [ "$PASS" = 2 ]; then
    local changed
    changed=$(diff <(echo "$before") <(snap) | sed -n 's/^> [0-9a-f]* //p' | tr '\n' ' ')
    echo "  ⏱ pass $PASS $label: $((t1 - t0)) s; changed: ${changed:-nothing}"
  else
    echo "  ⏱ pass $PASS $label: $((t1 - t0)) s"
  fi
  TIMES="$TIMES
  pass $PASS $label $((t1 - t0)) s${changed:+ — changed: $changed}"
}
run_pass() {
  step "[1/5] merge"    $PY scripts/maintenance/merge_seeds_cross_source.py --entity "$ENTS" ${APPLY:---dry-run}
  step "[2/5] absorb"   $PY scripts/maintenance/absorb_seeds_into_final_v2.py --entity "$ENTS" ${APPLY:---dry-run}
  step "[3/5] thin"     $PY scripts/maintenance/thin_final_weight_lists.py ${APPLY:---dry-run}
  step "[4/5] classify" $PY scripts/maintenance/auto_classify_seed_unsorted.py --entity "$ENTS" $APPLY
  step "[5/5] relink"   $PY scripts/maintenance/relink_promoted_v2.py ${APPLY:---dry-run}
}
TIMES=""
run_pass
if [ -n "$TWICE" ] && [ -n "$APPLY" ]; then
  TMP=$(mktemp -d)
  cp -R data/v2/final/. "$TMP/"
  PASS=2
  run_pass
  if diff -rq "$TMP" data/v2/final > /dev/null; then
    echo "FIXED POINT"
    rm -rf "$TMP"
  else
    # Keep the first pass and name the coins the second pass changed — a
    # bare «files differ» left nothing to analyse without a third run.
    echo "NOT A FIXED POINT — first pass kept in $TMP; coins the second pass changed:"
    $PY - "$TMP" <<'EOF'
import sys, yaml, pathlib
a_dir = pathlib.Path(sys.argv[1])
for a in sorted(a_dir.glob("*.yml")):
    b = pathlib.Path("data/v2/final") / a.name
    if a.read_bytes() == b.read_bytes():
        continue
    ca = {c["id"]: c for c in (yaml.safe_load(a.read_text()) or {}).get("coins") or []}
    cb = {c["id"]: c for c in (yaml.safe_load(b.read_text()) or {}).get("coins") or []}
    gone = sorted(set(ca) - set(cb)); new = sorted(set(cb) - set(ca))
    changed = sorted(i for i in set(ca) & set(cb) if ca[i] != cb[i])
    fields = {i: sorted(k for k in set(ca[i]) | set(cb[i]) if ca[i].get(k) != cb[i].get(k)) for i in changed}
    print(f"  {a.stem}: gone {gone[:10]} new {new[:10]} changed {len(changed)}")
    for i in changed[:15]:
        print(f"    {i}: {fields[i]}")
EOF
  fi
fi
echo "step times:$TIMES"
