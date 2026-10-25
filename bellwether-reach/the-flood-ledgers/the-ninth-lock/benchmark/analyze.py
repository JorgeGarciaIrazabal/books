"""Validate recorded blind rankings and aggregate preferences; no model calls."""
import collections, hashlib, itertools, json, re, sys
from pathlib import Path
B=Path(__file__).resolve().parent
manifest=json.loads((B/'run-manifest.json').read_text()); conditions={c['id']:c for c in manifest['conditions']}
keys=json.loads((B/'blind-keys.json').read_text())
original='--original' in sys.argv
review_dir=B/('reviews' if original or len(list((B/'effective-reviews').glob('*.json')))!=8 else 'effective-reviews')
corrected=review_dir.name=='effective-reviews'
prefix='original-' if original else ''
def split(text):
    ms=list(re.finditer(r'^## (P[1-8])[^\n]*$',text,re.M))
    return {m[1]:text[m.end():ms[i+1].start() if i+1<len(ms) else len(text)].strip() for i,m in enumerate(ms)}
outputs={c:split((B/('outputs-corrected' if corrected and c=='kimi-low' else 'outputs')/f'{c}.md').read_text()) for c in conditions}
reviews={}; failures=[]; evidence_flags=[]; hashes={}
for jid,key in keys.items():
    p=review_dir/f'{jid}.json'
    if not p.exists(): failures.append(f'{jid}: missing review');continue
    text=p.read_text().strip()
    if text.startswith('```'):text=re.sub(r'^```(?:json)?\s*|\s*```$','',text)
    try:r=json.loads(text)
    except Exception as e:failures.append(f'{jid}: invalid JSON: {e}');continue
    expected=set(key['labels']); found=[]
    for phase in r.get('phases',[]):
        pid=phase['phase'];found.append(pid)
        flat=[x for tier in phase['tiers'] for x in tier]
        if set(flat)!=expected or len(flat)!=len(expected):failures.append(f'{jid}/{pid}: rank coverage invalid')
        ev=phase.get('evidence',[])
        if {x['candidate'] for x in ev}!=expected or len(ev)!=len(expected):failures.append(f'{jid}/{pid}: evidence coverage invalid')
        for item in ev:
            cid=key['labels'].get(item['candidate'])
            if not cid:continue
            quote=item['quote']
            if not 4 <= len(quote.split()) <= 18:
                evidence_flags.append({'judge':jid,'phase':pid,'candidate':cid,'quote':quote,'kind':'outside requested 4–18-word quotation length'})
            if quote not in outputs[cid][pid]:
                # Whitespace-only normalization is explicit, not a fabricated exact match.
                kind='whitespace-only mismatch' if ' '.join(quote.split()) in ' '.join(outputs[cid][pid].split()) else 'not an exact source quote'
                evidence_flags.append({'judge':jid,'phase':pid,'candidate':cid,'quote':quote,'kind':kind})
    if sorted(found)!=[f'P{i}' for i in range(1,9)]:failures.append(f'{jid}: phase coverage invalid')
    reviews[jid]=r
    hashes[str(p.relative_to(B))]=hashlib.sha256(p.read_bytes()).hexdigest()
if failures:
    (B/(prefix+'validation.json')).write_text(json.dumps({'failures':failures,'evidence_flags':evidence_flags},indent=2)+'\n')
    raise SystemExit('\n'.join(failures))
# Equal weight per reviewer MODEL first, then per opponent. An effort pair is not two model votes.
ranks={}
for jid,r in reviews.items():
    ranks[jid]={p['phase']:{keys[jid]['labels'][label]:i for i,tier in enumerate(p['tiers']) for label in tier} for p in r['phases']}
models=sorted({c['model'] for c in conditions.values()})
def preference(pid,a,b,omit=None):
    by_model=collections.defaultdict(list)
    for jid,pr in ranks.items():
        model=keys[jid]['model']
        if model==omit or a not in pr[pid] or b not in pr[pid]:continue
        ra,rb=pr[pid][a],pr[pid][b]
        by_model[model].append(1 if ra<rb else 0 if ra>rb else .5)
    means={m:sum(xs)/len(xs) for m,xs in by_model.items()}
    return {'preference':sum(means.values())/len(means) if means else None,'reviewer_models':means,'judgments':sum(map(len,by_model.values()))}
def summarize(pid,omit=None):
    out={}
    for a in conditions:
        comparisons={b:preference(pid,a,b,omit) for b in conditions if b!=a}
        values=[v['preference'] for v in comparisons.values() if v['preference'] is not None]
        out[a]={'mean_preference':sum(values)/len(values) if values else None,'compared_opponents':len(values),'pairs':comparisons}
    return out
def best(stats):
    vals=[s['mean_preference'] for s in stats.values() if s['mean_preference'] is not None]
    return [c for c,s in stats.items() if s['mean_preference'] is not None and abs(s['mean_preference']-max(vals))<1e-9] if vals else []
result={'method':'Pairwise ordinal preferences; effort judgments averaged within reviewer model, then reviewer models equally, then opponents equally. Ties=0.5. Not a literary quality score.','phases':{},'source_hashes':hashes,'evidence_flags':evidence_flags,'review_set':review_dir.name,'correction_provenance':'blurb-correction.json' if corrected else None}
for pid in [f'P{i}' for i in range(1,9)]:
    stats=summarize(pid)
    for a,b in itertools.combinations(conditions,2):
        ab=stats[a]['pairs'][b]['preference'];ba=stats[b]['pairs'][a]['preference']
        assert ab is not None and ba is not None and abs(ab+ba-1)<1e-9, (pid,a,b)
    result['phases'][pid]={'candidates':stats,'top':best(stats),'leave_one_reviewer_model_out':{m:best(summarize(pid,m)) for m in models},'raw_ranks':{j:sorted(pr[pid].items(),key=lambda x:x[1]) for j,pr in ranks.items()}}
(B/(prefix+'results.json')).write_text(json.dumps(result,indent=2)+'\n')
(B/(prefix+'validation.json')).write_text(json.dumps({'failures':[],'evidence_flags':evidence_flags,'checks':[f'All {len(reviews)} reviews parse','Eight phases each','Eligible candidates exactly once per phase in rankings and evidence','Exact quote verification','No exact-model self reviews by packet construction']},indent=2)+'\n')
for pid,r in result['phases'].items():
    print(pid, 'top:', ', '.join(r['top']))
    print(' '.join(f'{c}={s["mean_preference"]:.3f}' for c,s in sorted(r['candidates'].items(),key=lambda x:-x[1]['mean_preference'])))
    print('leave-one-model-out:',r['leave_one_reviewer_model_out'])
print('Evidence flags',len(evidence_flags))
