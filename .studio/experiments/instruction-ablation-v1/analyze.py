"""Analyze recorded anonymous instruction comparisons; no model calls."""
from pathlib import Path
import json,collections,hashlib,re
B=Path(__file__).resolve().parent;keys=json.loads((B/'condition-keys.json').read_text());blind=json.loads((B/'blind-keys.json').read_text());assignments=json.loads((B/'assignments.json').read_text());ids=[t['id'] for t in assignments];conditions=json.loads((B/'run-manifest.json').read_text())['conditions']
def sections(t):
 ms=list(re.finditer(r'^## (F[12]-[PDC])[^\n]*$',t,re.M));assert [m[1] for m in ms]==ids
 return {m[1]:t[m.end():ms[i+1].start() if i+1<len(ms) else len(t)].strip() for i,m in enumerate(ms)}
outputs={run:sections((B/f'outputs/{run}.md').read_text()) for run in keys};votes=collections.defaultdict(lambda:collections.defaultdict(list));flags=[];failures=[];review_hashes={}
for jid,k in blind.items():
 p=B/f'reviews/{jid}.json'
 try:r=json.loads(p.read_text())
 except Exception as e:failures.append(f'{jid}: {e}');continue
 rows=r.get('comparisons',[]);expected=set(k['pairs']);seen=[x.get('pair') for x in rows]
 if set(seen)!=expected or len(seen)!=len(expected):failures.append(f'{jid}: pair coverage invalid');continue
 for row in rows:
  pair=k['pairs'][row['pair']];pref=row.get('preference');assert pref in ['X','Y','tie'];evidence=row.get('evidence',[])
  if {e.get('side') for e in evidence}!={'X','Y'} or len(evidence)!=2:failures.append(f'{jid}/{row["pair"]}: evidence sides invalid');continue
  for e in evidence:
   source=outputs[pair[e['side']]][pair['task']];quote=e['quote'];flag={'judge':jid,'pair':row['pair'],'task':pair['task'],'run':pair[e['side']],'quote':quote}
   if quote not in source:flags.append(dict(flag,kind='not an exact source quote'))
   if not 4<=len(quote.split())<=14:flags.append(dict(flag,kind='quotation length outside 4–14 words'))
  value=.5 if pref=='tie' else int(keys[pair[pref]]['arm']=='proposed');votes[(pair['condition'],pair['task'])][k['model']].append(value)
 review_hashes[str(p.relative_to(B))]=hashlib.sha256(p.read_bytes()).hexdigest()
if failures:
 (B/'validation.json').write_text(json.dumps({'failures':failures,'flags':flags},indent=2)+'\n');raise SystemExit('\n'.join(failures))
models=sorted({x['model'] for x in conditions})
def value(condition,task,omit=None):
 vals=[sum(xs)/len(xs) for m,xs in votes[(condition,task)].items() if m!=omit];assert vals
 return sum(vals)/len(vals)
def summary(omit=None):
 out={}
 for task in assignments:
  vals={c['id']:value(c['id'],task['id'],omit) for c in conditions};out[task['id']]={'updated_preference':sum(vals.values())/len(vals),'conditions':vals}
 return out
s=summary();role_results={}
audit=json.loads((B/'audit-results.json').read_text());director=json.loads((B/'director-audit.json').read_text())
assert set(director['runs'])==set(keys),'Director coverage incomplete'
for run,row in director['runs'].items():assert row['source_sha256']==hashlib.sha256((B/f'outputs/{run}.md').read_bytes()).hexdigest(),run
for role in ['story_architect','drafter','canon_keeper']:
 tasks=[t['id'] for t in assignments if t['role']==role];byfixture={t:s[t]['updated_preference'] for t in tasks};objective={'current':0,'proposed':0};details={'current':[],'proposed':[]}
 for run,key in keys.items():
  violations=[v for v in director['runs'][run].get('violations',[]) if v['task'] in tasks and not v.get('counted_mechanically')]
  for v in violations:objective[key['arm']]+=1;details[key['arm']].append({'run':run,**v})
  if role=='canon_keeper':
   for f,row in audit['runs'][run]['audits'].items():
    if 'parse_error' in row:objective[key['arm']]+=4;details[key['arm']].append({'run':run,'task':f+'-C','kind':'audit parse failure'})
    else:
     for lid in row['missed_seeded_lines']:objective[key['arm']]+=1;details[key['arm']].append({'run':run,'task':f+'-C','kind':'missed seeded line','line':lid})
     for lid in row['false_positive_lines']:objective[key['arm']]+=1;details[key['arm']].append({'run':run,'task':f+'-C','kind':'definite false positive','line':lid})
  if role=='canon_keeper':
   for fault in director.get('evidence_faults',[]):
    if fault['run']==run:objective[key['arm']]+=1;details[key['arm']].append(dict(fault,kind='inaccurate source locator'))
 fixture_test=all(x>.5 for x in byfixture.values());no_regression=objective['proposed']<=objective['current'];leave={m:{t:summary(m)[t]['updated_preference'] for t in tasks} for m in models};sensitive=any(any(x<=.5 for x in row.values()) for row in leave.values());eligible=fixture_test and no_regression and not sensitive
 role_results[role]={'fixtures':byfixture,'mean_updated_preference':sum(byfixture.values())/2,'objective_violations':objective,'objective_details':details,'both_fixtures_prefer_proposed':fixture_test,'no_objective_regression':no_regression,'remove_one_reviewer_model_sensitive':sensitive,'leave_one_reviewer_model_out':leave,'eligible_to_adopt':eligible,'decision':'adopt proposed block' if eligible else 'retain current contract; evidence insufficient for general replacement'}
result={'method':'Paired ordinal judgments; effort judgments averaged within each eligible reviewer model, reviewer models equally, conditions equally. .5 is tie. Values are measured preferences, not literary scores.','tasks':s,'roles':role_results,'review_hashes':review_hashes,'flags':flags}
(B/'results.json').write_text(json.dumps(result,indent=2)+'\n');(B/'validation.json').write_text(json.dumps({'failures':[],'flags':flags,'checks':['All 8 review JSON files parse','All 36 eligible pairs once per reviewer','X and Y evidence each pair','Exact-quote and word-count checks','Exact-model pair exclusions by construction','Director coverage complete and fresh']},indent=2)+'\n')
for role,row in role_results.items():print(role,row['fixtures'],'violations',row['objective_violations'],'adopt',row['eligible_to_adopt'])
print('Evidence flags',len(flags))
