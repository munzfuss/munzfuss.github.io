"""Usage: find_empty_duplicates.py [<base-ref, default main>] [<out.json>]

Memberless finals of the Denmark page: is each an EMPTY DUPLICATE?

A final with no member left after the rebuild keeps only its skeleton; on
`main` it carried its own copies of values. It is an empty duplicate when
EVERY value it had on `main` is present on another final of the rebuild:
  * every source URL (Numista pieces<N>.html folded to /<N>),
  * every catalogue value (KM in any volume; `others` «KM# 73» folded to 73),
  * every measured reading (weight / fineness / diameter, by value),
  * metal.
Hosts = rebuild finals (any entity) that carry at least one of its URLs.
`mint` / `mintmaster` / `nominal` are reported, not used to decide: a V1
record's mint or nominal often disagrees with the source the host follows,
and that disagreement is the point of the comparison, not a lost value.
"""
import json
import re
import sys
import glob
import os
import yaml

import subprocess
BASE = sys.argv[1] if len(sys.argv) > 1 else 'main'
OUT = sys.argv[2] if len(sys.argv) > 2 else None
DENMARK = ['christian_ii_reconquest', 'christian_ii_supporters', 'danish_norway', 'danish_realm',
           'glucksburg_duchy', 'gottorp_duchy', 'norburg_plon_duchy', 'norby_gotland',
           'royal_holstein', 'royal_slesvig', 'sonderburg_duchy']
SKIP_CAT = {'hede_volume'}


def base_coins(ent):
    r = subprocess.run(['git', 'show', f'{BASE}:data/v2/final/{ent}.yml'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return []
    return (yaml.safe_load(r.stdout) or {}).get('coins') or []


def coins(path):
    if not os.path.exists(path):
        return []
    return (yaml.safe_load(open(path)) or {}).get('coins') or []


def norm_url(u):
    u = str(u).strip()
    m = re.match(r'https?://(?:\w+\.)?numista\.com/(?:catalogue/pieces)?(\d+)(?:\.html)?/?$', u)
    if m:
        return f'numista:{m.group(1)}'
    return u.rstrip('/')


def urls(c):
    return {norm_url(s['url']) for s in c.get('sources') or [] if isinstance(s, dict) and s.get('url')}


def cat_vals(c):
    out = set()
    for f, v in (c.get('catalog') or {}).items():
        if f in SKIP_CAT or v is None:
            continue
        vals = []
        if isinstance(v, dict):
            for x in v.values():
                vals += x if isinstance(x, list) else [x]
        else:
            vals = v if isinstance(v, list) else [v]
        for x in vals:
            if isinstance(x, dict):
                x = x.get('value')
            if x is None:
                continue
            x = str(x).strip()
            if f == 'others':
                out.add(('others', x))
            else:
                out.add((f, x))
    return out


def readings(c):
    out = set()
    for f in ('weight_rough_g', 'fineness', 'diameter_mm'):
        v = c.get(f)
        for x in (v if isinstance(v, list) else [v]):
            val = x.get('value') if isinstance(x, dict) else x
            if isinstance(val, (int, float)):
                out.add((f, round(float(val), 3)))
    return out


# rebuild finals, all entities, indexed by URL
now_all = {}
for p in glob.glob('data/v2/final/*.yml'):
    ent = os.path.basename(p)[:-4]
    for c in coins(p):
        now_all[c['id']] = (ent, c)
by_url = {}
for cid, (ent, c) in now_all.items():
    for u in urls(c):
        by_url.setdefault(u, set()).add(cid)

UNIQUE_KEYS = ('bruun_collection_id', 'numista')
by_key = {}
for cid, (ent, c) in now_all.items():
    for f, v in cat_vals(c):
        if f in UNIQUE_KEYS:
            by_key.setdefault((f, v), set()).add(cid)

rows = []
for ent in DENMARK:
    main = {c['id']: c for c in base_coins(ent)}
    for c in coins(f'data/v2/final/{ent}.yml'):
        if c.get('composed_of'):
            continue
        m = main.get(c['id'])
        if m is None:
            rows.append({'entity': ent, 'id': c['id'], 'verdict': 'new-on-branch'})
            continue
        mu = urls(m)
        hosts = set()
        generic = {u for u in mu if len(by_url.get(u, set()) - {c['id']}) > 4}
        for u in mu - generic:
            hosts |= by_url.get(u, set()) - {c['id']}
        for f, v in cat_vals(m):
            if f in UNIQUE_KEYS:
                hosts |= by_key.get((f, v), set()) - {c['id']}
        hcat, hread, hmetal = set(), set(), set()
        for h in hosts:
            hc = now_all[h][1]
            hcat |= cat_vals(hc)
            hread |= readings(hc)
            hmetal.add(hc.get('metal'))
        hcat_plain = {v for _, v in hcat}
        lost = []
        for u in mu:
            if not (by_url.get(u, set()) - {c['id']}):
                lost.append(f'source {u}')
        for f, v in sorted(cat_vals(m)):
            if f == 'others':
                tok = re.split(r'[#\s]+', v)[-1]
                if tok in hcat_plain or v in hcat_plain:
                    continue
                lost.append(f'others {v}')
            elif f.endswith('_hede1971') and (f[:-9], v) in hcat:
                continue
            elif (f, v) not in hcat and not (f == 'km' and v in {x for g, x in hcat if g == 'km'}):
                lost.append(f'{f} {v}')
        for f, v in sorted(readings(m)):
            if (f, v) not in hread:
                lost.append(f'{f} {v}')
        if m.get('metal') and m.get('metal') not in hmetal:
            lost.append(f"metal {m.get('metal')}")
        if not mu:
            verdict = 'no-sources-on-main'
        elif lost:
            verdict = 'loses-data'
        else:
            verdict = 'empty-duplicate'
        hinfo = sorted(f'{now_all[h][0]}:{h}' for h in hosts)
        diffs = []
        for f in ('mint', 'mintmaster', 'nominal'):
            hv = {json.dumps(now_all[h][1].get(f), ensure_ascii=False) for h in hosts}
            mv = json.dumps(m.get(f), ensure_ascii=False)
            if m.get(f) is not None and mv not in hv:
                diffs.append(f'{f}: {m.get(f)} vs {"/".join(sorted(hv)) or "—"}')
        rows.append({'entity': ent, 'id': c['id'], 'verdict': verdict, 'hosts': hinfo,
                     'lost': lost, 'differs': diffs, 'n_urls': len(mu),
                     'nominal': m.get('nominal'), 'years': m.get('year_label'),
                     'generic': sorted(generic)})

if OUT:
    json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(Counter(r['verdict'] for r in rows))
print(Counter((r['entity'], r['verdict']) for r in rows))
